"""Win-only race tier: six pre-race win odds and a proven winner, second place optional.

Kept apart from ``verified_races`` and never counted toward the 500-race target.
Every check except the second place is the verified registry's own
(``check_common``): reviewed BET→RESULT link with three anchors, clock-verified
accepted frames, BET before RESULT, duplicate review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
from typing import Any

from horse_master.verified_races import append_race, check_common, check_paid_ticket

# None or a direct read of a result/payout table, or a paid single-win ticket.
WINNER_EVIDENCE = {None, "VISIBLE_CONFIRMED_PAYOUT_TABLE", "PAID_WIN"}


def register_win(
    db: sqlite3.Connection, record: dict[str, Any], manifest: dict[str, Any], root: Path,
) -> bool:
    """Append a win-only race; a race already in ``verified_races`` is refused, not duplicated.

    The winner is either read directly from a RESULT screen, or derived from a paid
    single-win WINNING TICKET (``evidence_kind=PAID_WIN``): a single that actually
    paid out names exactly one winner. Unpaid tickets and WIN CHANCE never qualify.
    """
    checked = check_common(record, manifest, root)
    result = record["result"]
    first = checked.field(result["first_place"])
    if type(first) is not int or first not in checked.numbers:
        raise ValueError("Invalid winner")
    if not set(result["first_place"]["source_frame_ids"]) <= set(
        record["confirmed_result_frame_ids"]
    ):
        raise ValueError("Result references a non-result frame")
    second = result.get("second_place")
    if second is not None and second.get("value") is not None:
        value = checked.field(second)
        if type(value) is not int or value not in checked.numbers or value == first:
            raise ValueError("Invalid second place")
        if not set(second["source_frame_ids"]) <= set(record["confirmed_result_frame_ids"]):
            raise ValueError("Result references a non-result frame")
    if result.get("evidence_kind") not in WINNER_EVIDENCE:
        raise ValueError("Unknown winner evidence kind")
    if result.get("evidence_kind") == "PAID_WIN":
        common = check_paid_ticket(record, checked, "win")
        if checked.field(result["paid_tickets"]["win"]["selection"]) != [first]:
            raise ValueError("Paid ticket does not prove recorded winner")
        if not common or not result.get("derivation"):
            raise ValueError("Paid facts need common result panel and derivation")
    start, end = min(checked.pre_times), max(checked.result_times)
    exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='verified_races'").fetchone()
    if exists and db.execute("SELECT 1 FROM verified_races WHERE video_id=? AND "
                             "start_seconds<=? AND end_seconds>=?",
                             (checked.video, end, start)).fetchone():
        raise ValueError("Race overlaps a verified race; use that record")
    if exists:
        for frame_id in record["pre_race_frame_ids"] + record["confirmed_result_frame_ids"]:
            if db.execute("SELECT 1 FROM verified_race_images WHERE image_sha256=?",
                          (checked.frames[frame_id]["image_sha256"],)).fetchone():
                raise ValueError("Evidence image already belongs to a verified race")
    return append_race(db, "win_races", record, manifest, checked)


def _tables(db: sqlite3.Connection) -> set[str]:
    return {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def win_dataset(db: sqlite3.Connection) -> list[dict[str, Any]]:
    """One row per race for win-market analysis: verified races plus the win-only tier.

    A win-only race later registered as verified (same video interval or a shared
    evidence image) appears once, as VERIFIED.
    """
    tables = _tables(db)
    rows: list[dict[str, Any]] = []
    verified: list[tuple[str, float, float]] = []
    verified_images: set[str] = set()
    if "verified_races" in tables:
        verified = list(db.execute(
            "SELECT video_id, start_seconds, end_seconds FROM verified_races"))
        verified_images = {r[0] for r in db.execute(
            "SELECT image_sha256 FROM verified_race_images")}
    for table, tier in [("verified_races", "VERIFIED"), ("win_races", "WIN_ONLY")]:
        if table not in tables:
            continue
        for key, video, candidate, start, end, record_json in db.execute(
            f"SELECT race_key, video_id, candidate_race_id, start_seconds, end_seconds, "
            f"record_json FROM {table} ORDER BY video_id, start_seconds"
        ):
            if tier == "WIN_ONLY":
                images = {r[0] for r in db.execute(
                    "SELECT image_sha256 FROM win_race_images WHERE race_key=?", (key,))}
                if images & verified_images or any(
                        v == video and s <= end and e >= start for v, s, e in verified):
                    continue
            record = json.loads(record_json)
            rows.append({
                "tier": tier, "video_id": video, "candidate_race_id": candidate,
                "win_odds": {r["horse_number"]: r["pre_race_win_odds"]["value"]
                             for r in record["runners"]},
                "winner": record["result"]["first_place"]["value"],
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--export", type=Path, help="write the combined win dataset as JSON")
    args = parser.parse_args()
    with sqlite3.connect(args.database) as db:
        inserted = None
        if args.record or args.manifest:
            if not (args.record and args.manifest):
                parser.error("--record and --manifest go together")
            record = json.loads(args.record.read_text(encoding="utf-8"))
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            inserted = register_win(db, record, manifest, args.manifest.parent)
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Database integrity check failed")
        rows = win_dataset(db)
    if args.export:
        args.export.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    tiers = {t: sum(r["tier"] == t for r in rows) for t in ("VERIFIED", "WIN_ONLY")}
    print(json.dumps({"inserted": inserted, **tiers, "total": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
