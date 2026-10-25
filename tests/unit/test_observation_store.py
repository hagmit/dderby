"""Synthetic observations test preservation and independent-occurrence comparisons."""
from copy import deepcopy
from pathlib import Path
import sqlite3
from typing import Any

import pytest

from horse_master.observation_store import connect, ingest, summarize


def sample(video: str = "video1", race: str = "race1", rank: str = "F"
           ) -> tuple[dict[str, Any], dict[str, Any]]:
    frame = f"{video}-frame"
    def field(value: Any) -> dict[str, Any]:
        return {"value": value, "confidence": 0.95 if value is not None else 0,
                "source_frame_ids": [frame] if value is not None else [],
                "error_reason": None if value is not None else "NOT_VISIBLE"}
    return ({"video_id": video, "candidate_race_id": race, "permission_status": "approved",
             "quality_status": "ANALYSIS_EXCLUDED", "horses": [
                 {"horse_number": 3, "horse_name": field("synthetic horse"),
                  "rank": field(rank), "speed_fill_ratio": field(None),
                  "win_odds": field(8.2)},
                 {"horse_number": 4, "horse_name": field(None), "rank": field("A")}]},
            {"frames": [{"frame_id": frame, "video_id": video}]})


def test_partial_excluded_data_is_append_only_and_idempotent(tmp_path: Path) -> None:
    db = connect(tmp_path / "observations.sqlite3")
    payload, manifest = sample()
    assert ingest(db, payload, manifest) > 0
    assert ingest(db, payload, manifest) == 0
    summary = summarize(db)
    assert summary["import_count"] == 1
    assert summary["unnamed_field_observation_count"] == 2
    horse = summary["candidate_horses"]["synthetic horse"]
    assert horse["fixed_status"] == "UNVERIFIED"
    assert horse["fields"]["speed_fill_ratio"]["status"] == "NOT_OBSERVED"
    for sql in ("DELETE FROM observations", "UPDATE imports SET series='other'"):
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute(sql)


def test_reprocessing_is_not_an_independent_appearance(tmp_path: Path) -> None:
    db = connect(tmp_path / "observations.sqlite3")
    payload, manifest = sample()
    ingest(db, payload, manifest)
    new = deepcopy(payload)
    new["processing_version"] = "new"
    ingest(db, new, manifest)
    rank = summarize(db)["candidate_horses"]["synthetic horse"]["fields"]["rank"]
    assert rank["status"] == "SINGLE_APPEARANCE"
    assert rank["independent_appearance_count"] == 1


def test_later_visible_attribute_preserves_original_missing_value(tmp_path: Path) -> None:
    db = connect(tmp_path / "observations.sqlite3")
    payload, manifest = sample()
    ingest(db, payload, manifest)
    new = deepcopy(payload)
    new["processing_version"] = "additional_reading"
    new["horses"][0]["speed_fill_ratio"] = {
        "value": 0.7, "confidence": 0.95, "source_frame_ids": ["video1-frame"],
        "error_reason": None,
    }
    ingest(db, new, manifest)
    stored = db.execute("SELECT value_json FROM observations "
                        "WHERE field_name='speed_fill_ratio'").fetchall()
    assert {row[0] for row in stored} == {"null", "0.7"}
    speed = summarize(db)["candidate_horses"]["synthetic horse"]["fields"]["speed_fill_ratio"]
    assert speed["status"] == "SINGLE_APPEARANCE"
    assert speed["values"] == [{"value": 0.7, "appearance_count": 1}]


def test_new_appearances_compare_without_overwriting_and_dynamic_odds_are_not_fixed(
    tmp_path: Path,
) -> None:
    db = connect(tmp_path / "observations.sqlite3")
    ingest(db, *sample())
    payload, manifest = sample("video2", "race2")
    payload["horses"][0]["win_odds"]["value"] = 2.1
    ingest(db, payload, manifest)
    horse = summarize(db)["candidate_horses"]["synthetic horse"]
    assert horse["fields"]["rank"]["status"] == "REPEATED_CONSISTENT"
    assert horse["fixed_status"] == "UNVERIFIED"
    assert "win_odds" not in horse["fields"]
    ingest(db, *sample("video3", "race3", "A"))
    horse = summarize(db)["candidate_horses"]["synthetic horse"]
    assert horse["fixed_status"] == "CONFLICT"
    assert {v["value"] for v in horse["fields"]["rank"]["values"]} == {"A", "F"}


@pytest.mark.parametrize("bad", ["permission", "series", "lineage"])
def test_invalid_import_is_rejected_atomically(tmp_path: Path, bad: str) -> None:
    db = connect(tmp_path / "observations.sqlite3")
    payload, manifest = sample()
    if bad == "permission":
        payload["permission_status"] = "pending"
    elif bad == "series":
        payload["series"] = "different_game"
    else:
        manifest["frames"] = []
    with pytest.raises(ValueError):
        ingest(db, payload, manifest)
    assert summarize(db)["import_count"] == 0
