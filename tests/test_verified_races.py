import copy
import hashlib
from pathlib import Path
import sqlite3

import pytest

from horse_master.verified_races import progress, register


def fixture(tmp_path: Path):
    frames = []
    for fid, sec, state in [("bet", 10, "ODDS_VISIBLE"), ("result", 60, "RESULT_VISIBLE")]:
        data = fid.encode()
        (tmp_path / fid).write_bytes(data)
        frames.append({"frame_id": fid, "video_id": "v", "image_path": fid,
                       "image_sha256": hashlib.sha256(data).hexdigest(),
                       "clock_verified": True, "quality_status": "ACCEPTED_FOR_RACE_REVIEW",
                       "player_display_seconds": sec, "screen_state": state})
    def field(value, ref):
        return {"value": value, "confidence": .9, "source_frame_ids": [ref]}
    record = {"series": "minna_de_derby_2", "permission_status": "approved", "video_id": "v",
              "candidate_race_id": "r", "runners": [
                  {"horse_number": n, "pre_race_win_odds": field(float(n), "bet")}
                  for n in range(1, 7)],
              "result": {"first_place": field(1, "result"),
                         "second_place": field(2, "result")},
              "pre_race_frame_ids": ["bet"], "confirmed_result_frame_ids": ["result"],
              "linkage": {"status": "VERIFIED", "reviewer": "test",
                          "anchors": [{"kind": str(i), "description": "reviewed visual anchor",
                                       "source_frame_ids": ["bet", "result"]} for i in range(3)]},
              "duplicate_review": {"reviewed": True}}
    return sqlite3.connect(":memory:"), record, {"frames": frames}


def test_registry_idempotent_and_protects_raw(tmp_path):
    db, record, manifest = fixture(tmp_path)
    assert progress(db)["validated_unique_race_count"] == 0
    assert register(db, record, manifest, tmp_path)
    assert not register(db, record, manifest, tmp_path)
    assert progress(db)["validated_unique_race_count"] == 1
    duplicate = copy.deepcopy(record)
    duplicate["candidate_race_id"] = "alias"
    with pytest.raises(ValueError, match="Overlapping"):
        register(db, duplicate, manifest, tmp_path)
    duplicate["video_id"] = "reupload"
    duplicate_manifest = copy.deepcopy(manifest)
    for frame in duplicate_manifest["frames"]:
        frame["video_id"] = "reupload"
    with pytest.raises(ValueError, match="Evidence image"):
        register(db, duplicate, duplicate_manifest, tmp_path)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("DELETE FROM verified_races")


@pytest.mark.parametrize("problem", ["permission", "clock", "duplicate_runner", "result",
                                     "lineage", "linkage", "wrong_phase", "tamper"])
def test_registry_rejects_unproven_races(tmp_path, problem):
    db, record, manifest = fixture(tmp_path)
    if problem == "permission":
        record["permission_status"] = "pending"
    elif problem == "clock":
        manifest["frames"][0]["clock_verified"] = False
    elif problem == "duplicate_runner":
        record["runners"][0]["horse_number"] = 2
    elif problem == "result":
        record["result"]["second_place"]["value"] = 1
    elif problem == "lineage":
        record["runners"][0]["pre_race_win_odds"]["source_frame_ids"] = ["missing"]
    elif problem == "linkage":
        record["linkage"]["status"] = "CANDIDATE_ONLY"
    elif problem == "wrong_phase":
        record["runners"][0]["pre_race_win_odds"]["source_frame_ids"] = ["result"]
    elif problem == "tamper":
        (tmp_path / "bet").write_bytes(b"changed")
    with pytest.raises(ValueError):
        register(db, record, manifest, tmp_path)
    assert progress(db)["validated_unique_race_count"] == 0
