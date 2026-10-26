"""Local evidence-backed race registry, separate from partial observations."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
from typing import Any

from horse_master.observation_store import canonical, digest


def register(
    db: sqlite3.Connection, record: dict[str, Any], manifest: dict[str, Any], root: Path,
) -> bool:
    """Check lineage and minimum race evidence before an append-only registration.

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
    candidate = record["candidate_race_id"]
    key = digest([record["series"], video, candidate])
    content = canonical([record, manifest])
    start, end = min(pre_times), max(result_times)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS verified_races (
          race_key TEXT PRIMARY KEY, video_id TEXT NOT NULL, candidate_race_id TEXT NOT NULL,
          start_seconds REAL NOT NULL, end_seconds REAL NOT NULL,
          record_json TEXT NOT NULL, manifest_json TEXT NOT NULL, content_hash TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
        CREATE TABLE IF NOT EXISTS verified_race_images (
          image_sha256 TEXT NOT NULL, race_key TEXT NOT NULL REFERENCES verified_races(race_key),
          PRIMARY KEY(image_sha256, race_key));
    """)
    for table in ["verified_races", "verified_race_images"]:
        for action in ["UPDATE", "DELETE"]:
            db.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_no_{action.lower()} "
                       f"BEFORE {action} ON {table} BEGIN "
                       "SELECT RAISE(ABORT,'Verified registry is append-only'); END")
    old = db.execute("SELECT content_hash FROM verified_races WHERE race_key=?", (key,)).fetchone()
    content_hash = digest(content)
    if old:
        if old[0] != content_hash:
            raise ValueError("Race key already registered with different content")
        return False
    if db.execute("SELECT 1 FROM verified_races WHERE video_id=? AND start_seconds<=? "
                  "AND end_seconds>=?", (video, end, start)).fetchone():
        raise ValueError("Overlapping video race interval requires identity review")
    hashes = {frames[i]["image_sha256"] for i in
              record["pre_race_frame_ids"] + record["confirmed_result_frame_ids"]}
    for value in hashes:
        if db.execute("SELECT 1 FROM verified_race_images WHERE image_sha256=?", (value,)).fetchone():
            raise ValueError("Evidence image already belongs to a registered race")
    with db:
        db.execute("INSERT INTO verified_races (race_key,video_id,candidate_race_id,start_seconds,"
                   "end_seconds,record_json,manifest_json,content_hash) VALUES (?,?,?,?,?,?,?,?)",
                   (key, video, candidate, start, end, canonical(record), canonical(manifest),
                    content_hash))
        db.executemany("INSERT INTO verified_race_images VALUES (?,?)",
                       [(h, key) for h in sorted(hashes)])
    return True


def progress(db: sqlite3.Connection, target: int = 500) -> dict[str, Any]:
    """Count only the verified registry, never partial import rows."""
    exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='verified_races'").fetchone()
    count = db.execute("SELECT COUNT(*) FROM verified_races").fetchone()[0] if exists else 0
    return {"target": target, "validated_unique_race_count": count,
            "remaining": max(0, target - count),
            "scope": "Evidence-reviewed races within collected permitted sources"}
