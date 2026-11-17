import copy
from pathlib import Path
import sqlite3

import pytest

from horse_master.verified_races import progress, register
from horse_master.win_races import register_win, win_dataset
from test_verified_races import fixture


def win_only(tmp_path: Path):
    db, record, manifest = fixture(tmp_path)
    del record["result"]["second_place"]
    return db, record, manifest


def test_win_tier_is_separate_idempotent_and_append_only(tmp_path):
    db, record, manifest = win_only(tmp_path)
    assert register_win(db, record, manifest, tmp_path)
    assert not register_win(db, record, manifest, tmp_path)
    assert progress(db)["validated_unique_race_count"] == 0
    assert win_dataset(db) == [{"tier": "WIN_ONLY", "video_id": "v", "candidate_race_id": "r",
                                "win_odds": {n: float(n) for n in range(1, 7)}, "winner": 1}]
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("UPDATE win_races SET video_id='x'")


def test_verified_race_is_not_duplicated_into_win_tier(tmp_path):
    db, record, manifest = fixture(tmp_path)
    assert register(db, record, manifest, tmp_path)
    with pytest.raises(ValueError, match="verified race"):
        register_win(db, record, manifest, tmp_path)
    moved = copy.deepcopy(record)
    moved["video_id"] = "reupload"
    moved_manifest = copy.deepcopy(manifest)
    for frame in moved_manifest["frames"]:
        frame["video_id"] = "reupload"
    with pytest.raises(ValueError, match="verified race"):
        register_win(db, moved, moved_manifest, tmp_path)
    assert [r["tier"] for r in win_dataset(db)] == ["VERIFIED"]


@pytest.mark.parametrize("problem", ["linkage", "clock", "odds", "winner", "second_same",
                                     "result_frame"])
def test_win_tier_keeps_every_other_requirement(tmp_path, problem):
    db, record, manifest = win_only(tmp_path)
    if problem == "linkage":
        record["linkage"]["anchors"] = record["linkage"]["anchors"][:2]
    elif problem == "clock":
        manifest["frames"][1]["clock_verified"] = False
    elif problem == "odds":
        record["runners"][5]["pre_race_win_odds"]["value"] = None
    elif problem == "winner":
        record["result"]["first_place"]["value"] = 7
    elif problem == "second_same":
        record["result"]["second_place"] = copy.deepcopy(record["result"]["first_place"])
    elif problem == "result_frame":
        record["result"]["first_place"]["source_frame_ids"] = ["bet"]
    with pytest.raises(ValueError):
        register_win(db, record, manifest, tmp_path)
    assert win_dataset(db) == []


@pytest.mark.parametrize("problem", [None, "potential", "unpaid", "other_horse", "no_derivation"])
def test_paid_single_win_ticket_proves_winner(tmp_path, problem):
    db, record, manifest = win_only(tmp_path)
    def field(value):
        return {"value": value, "confidence": .95, "source_frame_ids": ["result"]}
    record["result"].update({
        "evidence_kind": "PAID_WIN", "derivation": "Paid single win 1 proves first 1.",
        "paid_tickets": {"win": {"display_kind": field("WINNING TICKET"),
                                 "bet_type": field("win"), "selection": field([1]),
                                 "paid_medals": field(100)}}})
    ticket = record["result"]["paid_tickets"]["win"]
    if problem == "potential":
        ticket["display_kind"]["value"] = "WIN CHANCE"
    elif problem == "unpaid":
        ticket["paid_medals"]["value"] = 0
    elif problem == "other_horse":
        ticket["selection"]["value"] = [2]
    elif problem == "no_derivation":
        record["result"]["derivation"] = ""
    if problem is None:
        assert register_win(db, record, manifest, tmp_path)
    else:
        with pytest.raises(ValueError):
            register_win(db, record, manifest, tmp_path)


def test_win_race_later_verified_is_counted_once(tmp_path):
    db, record, manifest = fixture(tmp_path)
    win = copy.deepcopy(record)
    del win["result"]["second_place"]
    assert register_win(db, win, manifest, tmp_path)
    assert register(db, record, manifest, tmp_path)
    assert [r["tier"] for r in win_dataset(db)] == ["VERIFIED"]


@pytest.mark.parametrize("problem", ["second_frame", "evidence_kind"])
def test_optional_second_and_evidence_kind_are_still_checked(tmp_path, problem):
    db, record, manifest = fixture(tmp_path)
    if problem == "second_frame":
        record["result"]["second_place"]["source_frame_ids"] = ["bet"]
    else:
        record["result"]["evidence_kind"] = "PAID_WIN_PLUS_QUINELLA"
    with pytest.raises(ValueError):
        register_win(db, record, manifest, tmp_path)
