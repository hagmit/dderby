"""The capture plan locates candidates by their evidence frames, not whole imports."""
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from build_capture_plan import build, duration_seconds  # noqa: E402


def ledger() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE imports (import_id, series, video_id, payload_json, manifest_json, "
               "created_at)")
    db.execute("CREATE TABLE observations (observation_id, import_id, field_path, field_name, "
               "appearance_id, candidate_name, value_json, confidence, error_reason, "
               "source_refs_json)")
    frames = [{"frame_id": f"f{s}", "player_display_seconds": s} for s in (100, 400, 600)]
    for import_id, candidate in [("i1", "odds-only"), ("i2", "winner-only")]:
        db.execute("INSERT INTO imports VALUES (?,?,?,?,?,?)", (
            import_id, "game2", "v", json.dumps({"candidate_race_id": candidate}),
            json.dumps({"frames": frames}), ""))
    ref = json.dumps([{"frame_id": "f100", "player_display_seconds": 100}])
    for n in range(1, 7):
        db.execute("INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)", (
            f"o{n}", "i1", f"horses[{n}].win_odds", "win_odds", None, None, "3.5", .95, None,
            ref))
    db.execute("INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)", (
        "w", "i2", "result.first_place", "first_place", None, None, "4", .95, None,
        json.dumps([{"frame_id": "f400", "player_display_seconds": 400}])))
    return db


def test_targets_use_evidence_seconds_and_sweeps_find_gaps() -> None:
    videos = [{"video_id": "v", "series_status": "GAME2_TITLE_CONFIRMED",
               "duration_display": "12:00"},
              {"video_id": "other", "series_status": "NEEDS_GAME_SCREEN_VERIFICATION",
               "duration_display": "5 分"}]
    plan = build(ledger(), videos)
    assert [(t["need"], t["from"], t["to"]) for t in plan["targets"]] == [
        ("RESULT_AFTER_ODDS", 100.0, 220.0), ("ODDS_BEFORE_RESULT", 280.0, 400.0)]
    assert plan["targets"][1]["known_winner"] == [4]
    assert [s["video_id"] for s in plan["sweeps"]] == ["v"]
    assert plan["sweeps"][0]["gaps"] == [[0.0, 100.0], [100.0, 400.0], [400.0, 600.0],
                                         [600.0, 720.0]]


def test_duration_labels() -> None:
    assert duration_seconds("14 分 38 秒") == 878
    assert duration_seconds("1:31") == 91
    assert duration_seconds("1:02:03") == 3723
    assert duration_seconds(None) is None
