"""Read-only capture plan for the win-only tier: which seconds to shoot next, per video.

From the partial-observation ledger it finds race candidates that hold six pre-race
win odds but no winner (look forward for the result) and winners without odds (look
back for the odds board), plus the stretches of each approved video never captured.
It opens the database read-only and never registers anything.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sqlite3
from typing import Any

SEARCH = 120  # seconds around a half-race to look for its other half
SWEEP_STEP = 10


def duration_seconds(label: str | None) -> int | None:
    if not label:
        return None
    if re.fullmatch(r"\d+(:\d{2}){1,2}", label.strip()):
        total = 0
        for part in label.strip().split(":"):
            total = total * 60 + int(part)
        return total
    parts = [int(n) for n in re.findall(r"(\d+)\s*(?:時間|分|秒)", label)]
    units = re.findall(r"(時間|分|秒)", label)
    scale = {"時間": 3600, "分": 60, "秒": 1}
    return sum(n * scale[u] for n, u in zip(parts, units)) or None


def captured_seconds(db: sqlite3.Connection) -> dict[str, set[float]]:
    """Every player second already captured per video, whatever it showed."""
    seen: dict[str, set[float]] = defaultdict(set)
    for video, manifest in db.execute("SELECT video_id, manifest_json FROM imports"):
        for frame in json.loads(manifest).get("frames", []):
            if frame.get("player_display_seconds") is not None:
                seen[video].add(float(frame["player_display_seconds"]))
    return seen


def groups(db: sqlite3.Connection) -> dict[tuple[str, str], dict[str, Any]]:
    """Race candidates with the seconds of the frames their odds/winner were read from.

    An import can cover a whole batch of a video, so only the evidence frames of
    the values themselves locate a candidate in time.
    """
    found: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"odds": set(), "winner": set(), "seconds": set()})
    for video, candidate, path, name, value, refs in db.execute(
            "SELECT i.video_id, json_extract(i.payload_json,'$.candidate_race_id'), "
            "o.field_path, o.field_name, o.value_json, o.source_refs_json FROM observations o "
            "JOIN imports i USING(import_id) WHERE o.field_name IN ('win_odds','first_place')"):
        if value is None or json.loads(value) is None:
            continue
        group = found[(video, candidate or "UNKNOWN")]
        for ref in json.loads(refs or "[]"):
            if isinstance(ref, dict) and ref.get("player_display_seconds") is not None:
                group["seconds"].add(float(ref["player_display_seconds"]))
        if name == "first_place":
            group["winner"].add(json.loads(value))
        elif match := re.match(r"horses\[(\d+)\]", path):
            group["odds"].add(match.group(1))
    return found


def build(db: sqlite3.Connection, videos: list[dict[str, Any]]) -> dict[str, Any]:
    # Only videos whose title confirms the series; others need a game-screen check first.
    approved = {v["video_id"]: v for v in videos
                if v.get("series_status") == "GAME2_TITLE_CONFIRMED"}
    verified: dict[str, list[tuple[float, float]]] = defaultdict(list)
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='verified_races'").fetchone():
        for video, start, end in db.execute(
                "SELECT video_id, start_seconds, end_seconds FROM verified_races"):
            verified[video].append((start, end))
    targets: list[dict[str, Any]] = []
    seen = captured_seconds(db)
    untimed: list[dict[str, Any]] = []
    for (video, candidate), g in groups(db).items():
        if not g["seconds"]:
            if g["winner"] or len(g["odds"]) >= 6:
                untimed.append({"video_id": video, "candidate_race_id": candidate})
            continue
        if any(s <= min(g["seconds"]) <= e for s, e in verified[video]):
            continue
        first, last = min(g["seconds"]), max(g["seconds"])
        if len(g["odds"]) >= 6 and not g["winner"]:
            targets.append({"video_id": video, "candidate_race_id": candidate,
                            "need": "RESULT_AFTER_ODDS", "from": last, "to": last + SEARCH})
        elif g["winner"] and len(g["odds"]) < 6:
            targets.append({"video_id": video, "candidate_race_id": candidate,
                            "need": "ODDS_BEFORE_RESULT", "known_winner": sorted(g["winner"]),
                            "from": max(0.0, first - SEARCH), "to": first})
        elif g["winner"] and len(g["odds"]) >= 6:
            targets.append({"video_id": video, "candidate_race_id": candidate,
                            "need": "LINK_REVIEW_ONLY", "from": first, "to": last})
    sweeps = []
    for video, info in approved.items():
        total = duration_seconds(info.get("duration_display"))
        if total is None:
            continue
        covered = sorted(seen[video])
        gaps, cursor = [], 0.0
        for second in covered + [float(total)]:
            if second - cursor > 3 * SWEEP_STEP:
                gaps.append([cursor, second])
            cursor = max(cursor, second)
        sweeps.append({"video_id": video, "duration_seconds": total,
                       "captured_points": len(covered),
                       "uncovered_seconds": round(sum(b - a for a, b in gaps)),
                       "gaps": gaps})
    order = {"LINK_REVIEW_ONLY": 0, "RESULT_AFTER_ODDS": 1, "ODDS_BEFORE_RESULT": 2}
    targets.sort(key=lambda t: (order[t["need"]], t["video_id"], t["from"]))
    sweeps.sort(key=lambda s: -s["uncovered_seconds"])
    return {"targets": targets, "untimed_candidates": untimed, "sweeps": sweeps,
            "counts": {k: sum(t["need"] == k for t in targets) for k in order},
            "note": "Plan only. Linkage, clocks and duplicates are reviewed at registration."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--videos", type=Path, required=True, help="video-inventory/videos.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    db = sqlite3.connect(f"file:{args.database}?mode=ro", uri=True)
    videos = json.loads(args.videos.read_text(encoding="utf-8"))["videos"]
    plan = build(db, videos)
    args.out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(plan["counts"] | {"sweep_videos": len(plan["sweeps"])}))


if __name__ == "__main__":
    main()
