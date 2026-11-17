"""Local evidence-backed race registry, separate from partial observations."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Callable

from horse_master.observation_store import canonical, digest


@dataclass(frozen=True)
class Checked:
    """Facts shared by every race registry once the common evidence checks passed."""

    video: str
    frames: dict[str, dict[str, Any]]
    numbers: list[int]
    field: Callable[[dict[str, Any]], Any]
    pre_times: list[float]
    result_times: list[float]


def check_common(record: dict[str, Any], manifest: dict[str, Any], root: Path) -> Checked:
    """Lineage, six pre-race win odds, reviewed BET→RESULT link, phases and duplicate review.

    Visual linkage is a review decision with written anchors, not an automatic
    inference from nearby timestamps. Unknown horse names/abilities stay optional.
    """
    if record.get("series") != "minna_de_derby_2":
        raise ValueError("Wrong series")
    if record.get("permission_status") != "approved":
        raise ValueError("Source permission not approved")
    video = record["video_id"]
    frames = {f["frame_id"]: f for f in manifest["frames"]}
    if len(frames) != len(manifest["frames"]):
        raise ValueError("Duplicate frame IDs")
    for frame in frames.values():
        if frame["video_id"] != video or not frame.get("clock_verified"):
            raise ValueError("Frame source/clock unverified")
        if frame.get("quality_status") != "ACCEPTED_FOR_RACE_REVIEW":
            raise ValueError("Frame quality not accepted")
        actual = hashlib.sha256((root / frame["image_path"]).read_bytes()).hexdigest()
        if actual != frame["image_sha256"]:
            raise ValueError("Image hash mismatch")

    def refs(ids: list[str]) -> None:
        if not ids or any(i not in frames for i in ids):
            raise ValueError("Missing frame evidence")

    def field(obj: dict[str, Any]) -> Any:
        refs(obj["source_frame_ids"])
        if obj["value"] is None or not 0.85 <= obj["confidence"] <= 1:
            raise ValueError("Required field unknown or low confidence")
        return obj["value"]

    runners = record["runners"]
    numbers = [r["horse_number"] for r in runners]
    if sorted(numbers) != [1, 2, 3, 4, 5, 6]:
        raise ValueError("Six unique runner numbers required")
    for runner in runners:
        odds = field(runner["pre_race_win_odds"])
        if not set(runner["pre_race_win_odds"]["source_frame_ids"]) <= set(
            record["pre_race_frame_ids"]
        ):
            raise ValueError("Pre-race odds reference a non-BET frame")
        if isinstance(odds, bool) or not isinstance(odds, (int, float)) or odds < 1:
            raise ValueError("Invalid win odds")
    linkage = record["linkage"]
    if linkage.get("status") != "VERIFIED" or not linkage.get("reviewer"):
        raise ValueError("BET to RESULT link not reviewed")
    anchors = linkage["anchors"]
    if len({a["kind"] for a in anchors}) < 3:
        raise ValueError("At least three distinct visual anchors required")
    for anchor in anchors:
        refs(anchor["source_frame_ids"])
        if not anchor.get("description"):
            raise ValueError("Link evidence description missing")
    refs(record["pre_race_frame_ids"])
    refs(record["confirmed_result_frame_ids"])
    if any(frames[i].get("screen_state") not in
           {"BET_OPEN", "HORSE_INFO_VISIBLE", "ODDS_VISIBLE"}
           for i in record["pre_race_frame_ids"]):
        raise ValueError("Required BET screen missing")
    if any(frames[i].get("screen_state") != "RESULT_VISIBLE"
           for i in record["confirmed_result_frame_ids"]):
        raise ValueError("Explicit result screen missing")
    pre_times = [frames[i]["player_display_seconds"] for i in record["pre_race_frame_ids"]]
    result_times = [frames[i]["player_display_seconds"]
                    for i in record["confirmed_result_frame_ids"]]
    if max(pre_times) >= min(result_times):
        raise ValueError("Pre-race evidence must precede confirmed result")
    if not record.get("duplicate_review", {}).get("reviewed"):
        raise ValueError("Duplicate review missing")
    return Checked(video, frames, numbers, field, pre_times, result_times)


def check_paid_ticket(record: dict[str, Any], checked: Checked, kind: str) -> set[str]:
    """A WINNING TICKET row with a positive actual payout; returns its common frames."""
    ticket = record["result"]["paid_tickets"][kind]
    field = checked.field
    if field(ticket["display_kind"]) != "WINNING TICKET":
        raise ValueError("Potential WIN CHANCE is not a paid result")
    if field(ticket["bet_type"]) != kind:
        raise ValueError("Paid ticket type mismatch")
    paid = field(ticket["paid_medals"])
    if isinstance(paid, bool) or not isinstance(paid, (int, float)) or paid <= 0:
        raise ValueError("Ticket must have positive actual payout")
    common = set(record["confirmed_result_frame_ids"])
    for key in ["display_kind", "bet_type", "selection", "paid_medals"]:
        common &= set(ticket[key]["source_frame_ids"])
    return common


def append_race(db: sqlite3.Connection, table: str, record: dict[str, Any],
                manifest: dict[str, Any], checked: Checked) -> bool:
    """Append-only, idempotent insert into ``table`` and its ``{table[:-1]}_images`` index."""
    images = f"{table[:-1]}_images"
    candidate = record["candidate_race_id"]
    key = digest([record["series"], checked.video, candidate])
    content = canonical([record, manifest])
    start, end = min(checked.pre_times), max(checked.result_times)
    db.executescript(f"""
        CREATE TABLE IF NOT EXISTS {table} (
          race_key TEXT PRIMARY KEY, video_id TEXT NOT NULL, candidate_race_id TEXT NOT NULL,
          start_seconds REAL NOT NULL, end_seconds REAL NOT NULL,
          record_json TEXT NOT NULL, manifest_json TEXT NOT NULL, content_hash TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
        CREATE TABLE IF NOT EXISTS {images} (
          image_sha256 TEXT NOT NULL, race_key TEXT NOT NULL REFERENCES {table}(race_key),
          PRIMARY KEY(image_sha256, race_key));
    """)
    label = "Verified" if table == "verified_races" else "Race"
    for name in [table, images]:
        for action in ["UPDATE", "DELETE"]:
            db.execute(f"CREATE TRIGGER IF NOT EXISTS {name}_no_{action.lower()} "
                       f"BEFORE {action} ON {name} BEGIN "
                       f"SELECT RAISE(ABORT,'{label} registry is append-only'); END")
    old = db.execute(f"SELECT content_hash FROM {table} WHERE race_key=?", (key,)).fetchone()
    content_hash = digest(content)
    if old:
        if old[0] != content_hash:
            raise ValueError("Race key already registered with different content")
        return False
    if db.execute(f"SELECT 1 FROM {table} WHERE video_id=? AND start_seconds<=? "
                  "AND end_seconds>=?", (checked.video, end, start)).fetchone():
        raise ValueError("Overlapping video race interval requires identity review")
    hashes = {checked.frames[i]["image_sha256"] for i in
              record["pre_race_frame_ids"] + record["confirmed_result_frame_ids"]}
    for value in hashes:
        if db.execute(f"SELECT 1 FROM {images} WHERE image_sha256=?", (value,)).fetchone():
            raise ValueError("Evidence image already belongs to a registered race")
    with db:
        db.execute(f"INSERT INTO {table} (race_key,video_id,candidate_race_id,start_seconds,"
                   "end_seconds,record_json,manifest_json,content_hash) VALUES (?,?,?,?,?,?,?,?)",
                   (key, checked.video, candidate, start, end, canonical(record),
                    canonical(manifest), content_hash))
        db.executemany(f"INSERT INTO {images} VALUES (?,?)",
                       [(h, key) for h in sorted(hashes)])
    return True


def register(
    db: sqlite3.Connection, record: dict[str, Any], manifest: dict[str, Any], root: Path,
) -> bool:
    """Check lineage and minimum race evidence before an append-only registration."""
    checked = check_common(record, manifest, root)
    numbers, field = checked.numbers, checked.field
    first = field(record["result"]["first_place"])
    second = field(record["result"]["second_place"])
    if type(first) is not int or type(second) is not int or (
        first not in numbers or second not in numbers or first == second
    ):
        raise ValueError("Invalid ordered result")
    for place in ["first_place", "second_place"]:
        if not set(record["result"][place]["source_frame_ids"]) <= set(
            record["confirmed_result_frame_ids"]
        ):
            raise ValueError("Result references a non-result frame")
    # Two paid tickets on the same result panel can prove an ordered pair exactly:
    # a winning single identifies first place; a winning quinella identifies both.
    # This path must preserve the raw ticket facts and the explicit derivation.
    if record["result"].get("evidence_kind") == "PAID_WIN_PLUS_QUINELLA":
        tickets = record["result"]["paid_tickets"]
        common = check_paid_ticket(record, checked, "win") & check_paid_ticket(
            record, checked, "quinella")
        win_selection = field(tickets["win"]["selection"])
        pair = field(tickets["quinella"]["selection"])
        if win_selection != [first] or sorted(pair) != sorted([first, second]):
            raise ValueError("Paid tickets do not prove recorded order")
        if not common or not record["result"].get("derivation"):
            raise ValueError("Paid facts need common result panel and derivation")
    return append_race(db, "verified_races", record, manifest, checked)


def progress(db: sqlite3.Connection, target: int = 500) -> dict[str, Any]:
    """Count only the verified registry, never partial import rows."""
    exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='verified_races'").fetchone()
    count = db.execute("SELECT COUNT(*) FROM verified_races").fetchone()[0] if exists else 0
    return {"target": target, "validated_unique_race_count": count,
            "remaining": max(0, target - count),
            "scope": "Evidence-reviewed races within collected permitted sources"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    with sqlite3.connect(args.database) as db:
        inserted = register(db, record, manifest, args.manifest.parent)
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Database integrity check failed")
        print(json.dumps({"inserted": inserted, **progress(db)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
