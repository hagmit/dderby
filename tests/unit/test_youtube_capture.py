"""Capture gating with a scripted player; no network or browser."""
import json
from pathlib import Path
from typing import Any

import pytest

from frame_extractor.youtube_capture import (
    CaptureRefused, Limits, capture, check_scope, clock_seconds, owner_handle, watch_video_id,
    write_watchdog_manifest,
)

VIDEO = "r7Bl-CnZ9gs"
STEBY = {"video_id": VIDEO, "title": "t", "owner_url": "http://www.youtube.com/@steby0419"}


class FakePlayer:
    def __init__(self, meta: dict[str, Any] = STEBY, url: str = f"https://www.youtube.com/watch?v={VIDEO}",
                 ad_reads: int = 0, offset: float = 0.0, unstable: bool = False,
                 stale_frame: bool = False, late_ad: bool = False) -> None:
        self.meta, self._url, self.ad_reads = meta, url, ad_reads
        self.offset, self.unstable, self.time, self.shots = offset, unstable, 0.0, 0
        self.stale_frame, self.late_ad, self.previous = stale_frame, late_ad, 0.0

    def open(self, video_id: str) -> None:
        pass

    def url(self) -> str:
        return self._url

    def metadata(self) -> dict[str, Any]:
        return self.meta

    def state(self) -> dict[str, Any]:
        ad = self.ad_reads > 0
        self.ad_reads -= 1
        whole = int(self.time)
        ad = ad or (self.late_ad and self.shots > 0)
        return {"player_state": 2, "current_time": self.time, "ad_showing": ad, "error": None,
                "video_time": self.time, "seeking": False, "ready_state": 4,
                "frame_media_time": self.previous if self.stale_frame else self.time,
                "clock_text": f"{whole // 60}:{whole % 60:02d}"}

    def seek_pause(self, seconds: float) -> None:
        self.previous, self.time = self.time, seconds + self.offset

    def screenshot(self) -> bytes:
        self.shots += 1
        return f"png-{self.time}-{self.shots if self.unstable else 0}".encode()


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def run(player: FakePlayer, tmp: Path, seconds: list[float] | None = None,
        limits: Limits = Limits()) -> dict[str, Any]:
    clock = Clock()
    return capture(player, VIDEO, seconds or [140.0, 153.0], tmp, "b001", limits, clock, clock.sleep)


def test_accepted_frames_are_pending_review_and_append_only(tmp_path: Path) -> None:
    manifest = run(FakePlayer(), tmp_path)
    assert manifest["status"] == "CAPTURED_PENDING_REVIEW" and not manifest["stream_downloaded"]
    assert [f["frame_id"] for f in manifest["frames"]] == [f"{VIDEO}-b001-0001", f"{VIDEO}-b001-0002"]
    frame = manifest["frames"][0]
    assert frame["clock_verified"] is False and frame["issues"] == []
    assert (tmp_path / f"{VIDEO}-b001" / frame["image_path"]).read_bytes() == b"png-140.0-0"
    saved = json.loads((tmp_path / f"{VIDEO}-b001/manifest.json").read_text(encoding="utf-8"))
    assert saved["source"]["series_check"] == "VISUAL_REVIEW_REQUIRED"
    with pytest.raises(FileExistsError):
        run(FakePlayer(), tmp_path)


def test_unapproved_channel_is_refused_before_any_seek(tmp_path: Path) -> None:
    meta = {**STEBY, "owner_url": "http://www.youtube.com/@someone"}
    manifest = run(FakePlayer(meta=meta), tmp_path)
    assert manifest["refused"] == "PERMISSION_NOT_CONFIRMED" and manifest["frames"] == []
    assert manifest["status"] == "CAPTURE_UNAVAILABLE"


def test_redirected_page_is_refused(tmp_path: Path) -> None:
    manifest = run(FakePlayer(url="https://consent.youtube.com/m?continue=x"), tmp_path)
    assert manifest["refused"] == "URL_MISMATCH"


@pytest.mark.parametrize(("player", "issue"), [
    (FakePlayer(ad_reads=10**6), "AD_SHOWING"),
    (FakePlayer(offset=3.0), "SEEK_OFFSET"),
    (FakePlayer(unstable=True), "FRAME_UNSTABLE"),
    (FakePlayer(stale_frame=True), "STALE_FRAME"),
    (FakePlayer(late_ad=True), "AFTER_AD_SHOWING"),
])
def test_unsettled_frames_are_kept_only_for_audit(tmp_path: Path, player: FakePlayer,
                                                  issue: str) -> None:
    manifest = run(player, tmp_path, [140.0])
    assert manifest["frames"][0]["quality_status"] == "CAPTURE_AUDIT_ONLY"
    assert issue in manifest["frames"][0]["issues"]
    assert manifest["status"] == "CAPTURE_UNAVAILABLE"


def test_ad_that_ends_within_timeout_is_accepted(tmp_path: Path) -> None:
    manifest = run(FakePlayer(ad_reads=3), tmp_path, [140.0])
    assert manifest["frames"][0]["issues"] == []


def test_budget_stops_remaining_points(tmp_path: Path) -> None:
    manifest = run(FakePlayer(ad_reads=10**6), tmp_path, [1.0, 2.0, 3.0],
                   Limits(budget_seconds=20, point_timeout=15))
    assert len(manifest["frames"]) == 2 and manifest["not_attempted_seconds"] == [3.0]


def test_scope_helpers() -> None:
    assert watch_video_id(f"https://www.youtube.com/watch?v={VIDEO}&t=5") == VIDEO
    assert watch_video_id("https://www.youtube.com/shorts/g6qE9m57kPI") == "g6qE9m57kPI"
    assert watch_video_id(f"http://www.youtube.com/watch?v={VIDEO}") is None
    assert owner_handle("http://www.youtube.com/@%E3%81%9F%E3%81%8B%E3%81%9F%E3%81%8Bchannel") \
        == "たかたかchannel"
    taka = {"video_id": VIDEO, "owner_url": "https://www.youtube.com/@たかたかchannel"}
    assert check_scope({**taka, "title": "みんなでダービー２ part1"}, VIDEO)["series_check"] \
        == "TITLE_MATCH"
    with pytest.raises(CaptureRefused, match="SERIES_NOT_CONFIRMED"):
        check_scope({**taka, "title": "別のゲーム"}, VIDEO)
    with pytest.raises(CaptureRefused, match="VIDEO_MISMATCH"):
        check_scope({**STEBY, "video_id": "other"}, VIDEO)
    assert clock_seconds("1:02:03") == 3723 and clock_seconds("2:20") == 140
    assert clock_seconds("LIVE") is None


def test_unsafe_ids_are_rejected_before_writing(tmp_path: Path) -> None:
    clock = Clock()
    with pytest.raises(ValueError):
        capture(FakePlayer(), VIDEO, [1.0], tmp_path, "../x", Limits(), clock, clock.sleep)
    with pytest.raises(ValueError):
        capture(FakePlayer(), "../../etc/xx", [1.0], tmp_path, "b", Limits(), clock, clock.sleep)
    assert list(tmp_path.iterdir()) == []


def test_watchdog_indexes_orphan_images_as_audit_only(tmp_path: Path) -> None:
    raw = tmp_path / f"{VIDEO}-b9" / "raw"
    raw.mkdir(parents=True)
    (raw / "0001-140s.png").write_bytes(b"x")
    manifest = write_watchdog_manifest(tmp_path, VIDEO, "b9", [140.0])
    assert manifest is not None and manifest["status"] == "CAPTURE_UNAVAILABLE"
    assert manifest["frames"][0]["quality_status"] == "CAPTURE_AUDIT_ONLY"
    assert write_watchdog_manifest(tmp_path, VIDEO, "b9", [140.0]) is None


def test_manifest_is_never_overwritten_or_left_partial(tmp_path: Path) -> None:
    run(FakePlayer(), tmp_path, [140.0])
    batch = tmp_path / f"{VIDEO}-b001"
    assert sorted(p.name for p in batch.iterdir()) == ["manifest.json", "raw"]
    assert write_watchdog_manifest(tmp_path, VIDEO, "b001", [140.0]) is None
