"""Bounded local-Chromium screenshots of approved YouTube videos.

The player is driven only through the normal watch page. Video streams are never
downloaded. A capture is evidence awaiting review, never a registered observation:
``clock_verified`` stays false until a reviewer reads the clock inside the image.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from typing import Any, Callable, Protocol
import unicodedata
from urllib.parse import parse_qs, unquote, urlparse

SERIES_TERM = "みんなでダービー2"
# handle (without @, NFKC) -> NFKC title term required, or None when the series is
# confirmed by visual review. Unlisted channels are refused before any capture.
APPROVED_SCOPES: dict[str, str | None] = {"steby0419": None, "たかたかchannel": SERIES_TERM}
WATCH_HOSTS = {"www.youtube.com", "youtube.com", "m.youtube.com"}
PAUSED = 2
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
BATCH_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
WATCHDOG_GRACE = 60.0


class Player(Protocol):
    def open(self, video_id: str) -> None: ...
    def url(self) -> str: ...
    def metadata(self) -> dict[str, Any]: ...
    def state(self) -> dict[str, Any]: ...
    def seek_pause(self, seconds: float) -> None:
        """Pause, seek, and arm a check that a new frame is presented for this seek."""
    def screenshot(self) -> bytes: ...


@dataclass(frozen=True)
class Limits:
    budget_seconds: float = 120.0
    point_timeout: float = 15.0
    tolerance: float = 1.0
    settle_seconds: float = 0.3


class CaptureRefused(RuntimeError):
    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason


def nfkc(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def watch_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in WATCH_HOSTS:
        return None
    if parsed.path == "/watch":
        return parse_qs(parsed.query).get("v", [None])[0]
    if parsed.path.startswith("/shorts/"):
        return parsed.path.split("/")[2] or None
    return None


def owner_handle(owner_url: str) -> str | None:
    path = unquote(urlparse(owner_url).path)
    return nfkc(path[2:].split("/")[0]) if path.startswith("/@") else None


def check_scope(meta: dict[str, Any], video_id: str) -> dict[str, Any]:
    """Fail closed unless the page itself shows the expected video and approved channel."""
    if meta.get("video_id") != video_id:
        raise CaptureRefused("VIDEO_MISMATCH", str(meta.get("video_id")))
    handle = owner_handle(str(meta.get("owner_url") or ""))
    scopes = {nfkc(k): v for k, v in APPROVED_SCOPES.items()}
    if handle is None or handle not in scopes:
        raise CaptureRefused("PERMISSION_NOT_CONFIRMED", f"channel={handle}")
    term = scopes[handle]
    if term is not None and nfkc(term) not in nfkc(str(meta.get("title") or "")):
        raise CaptureRefused("SERIES_NOT_CONFIRMED", "title lacks series term")
    return {**meta, "channel_handle": handle,
            "series_check": "TITLE_MATCH" if term else "VISUAL_REVIEW_REQUIRED"}


def clock_seconds(text: str) -> int | None:
    parts = text.strip().split(":")
    if not 2 <= len(parts) <= 3 or not all(p.isdigit() for p in parts):
        return None
    value = 0
    for part in parts:
        value = value * 60 + int(part)
    return value


def _problem(state: dict[str, Any], target: float, tolerance: float) -> str | None:
    """Why this state cannot back a frame at ``target``; None when it can.

    ``getCurrentTime`` alone is not freshness: the presented frame's media time
    (requestVideoFrameCallback, armed per seek) must also be near the target.
    """
    if state.get("error"):
        return "PLAYER_ERROR"
    if state.get("ad_showing"):
        return "AD_SHOWING"
    if state.get("player_state") != PAUSED:
        return "NOT_PAUSED"
    if state.get("seeking") or int(state.get("ready_state") or 0) < 2:
        return "BUFFERING"
    times = [state.get("current_time"), state.get("video_time")]
    if any(t is None or abs(float(t) - target) > tolerance for t in times):
        return "SEEK_OFFSET"
    if state.get("frame_media_time") is None:
        return "FRAME_NOT_PRESENTED"
    if abs(float(state["frame_media_time"]) - target) > tolerance:
        return "STALE_FRAME"
    return None


def _settle(player: Player, target: float, limits: Limits, deadline: float,
            clock: Callable[[], float], sleep: Callable[[float], None]
            ) -> tuple[dict[str, Any], str | None]:
    stop = min(deadline, clock() + limits.point_timeout)
    while True:
        state = player.state()
        reason = _problem(state, target, limits.tolerance)
        if reason is None or reason == "PLAYER_ERROR" or clock() >= stop:
            return state, reason
        sleep(0.25)


def _check_ids(video_id: str, batch_id: str) -> None:
    if not VIDEO_ID.fullmatch(video_id) or not BATCH_ID.fullmatch(batch_id):
        raise ValueError("video_id must be 11 URL-safe characters; batch_id [A-Za-z0-9._-]")


def capture(player: Player, video_id: str, seconds: list[float], out_dir: Path, batch_id: str,
            limits: Limits = Limits(), clock: Callable[[], float] = time.monotonic,
            sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Capture requested points within one time budget and write an append-only batch.

    The manifest is written on every exit path that Python can observe; a hard kill
    is covered by :func:`write_watchdog_manifest` in the supervising process.
    """
    _check_ids(video_id, batch_id)
    batch = out_dir / f"{video_id}-{batch_id}"
    (batch / "raw").mkdir(parents=True, exist_ok=False)
    deadline = clock() + limits.budget_seconds
    manifest: dict[str, Any] = {
        "schema_version": 1, "video_id": video_id, "batch_id": batch_id,
        "method": "local_chromium_watch_page_screenshot", "stream_downloaded": False,
        "requested_seconds": seconds, "frames": [], "not_attempted_seconds": [],
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        player.open(video_id)
        if watch_video_id(player.url()) != video_id:
            raise CaptureRefused("URL_MISMATCH", urlparse(player.url()).hostname or "")
        manifest["source"] = check_scope(player.metadata(), video_id)
        for seq, target in enumerate(seconds, start=1):
            if clock() >= deadline:
                manifest["not_attempted_seconds"] = seconds[seq - 1:]
                break
            manifest["frames"].append(_capture_point(
                player, video_id, batch, batch_id, seq, target, limits, deadline, clock, sleep))
    except CaptureRefused as refused:
        manifest["refused"] = refused.reason
        manifest["refused_detail"] = str(refused)
    except BaseException as error:  # keep partial evidence and fail closed
        manifest["refused"] = "CAPTURE_ERROR"
        manifest["refused_detail"] = f"{type(error).__name__}: {str(error)[:200]}"
        if not isinstance(error, Exception):
            _write_manifest(batch, manifest)
            raise
    _write_manifest(batch, manifest)
    return manifest


def _write_manifest(batch: Path, manifest: dict[str, Any]) -> None:
    accepted = [f for f in manifest["frames"] if f["quality_status"] == "CAPTURED_PENDING_REVIEW"]
    manifest["status"] = "CAPTURED_PENDING_REVIEW" if accepted else "CAPTURE_UNAVAILABLE"
    with (batch / "manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)


def _capture_point(player: Player, video_id: str, batch: Path, batch_id: str, seq: int,
                   target: float, limits: Limits, deadline: float,
                   clock: Callable[[], float], sleep: Callable[[float], None]) -> dict[str, Any]:
    frame: dict[str, Any] = {"frame_id": f"{video_id}-{batch_id}-{seq:04d}",
                             "video_id": video_id, "requested_seconds": target,
                             "clock_verified": False, "issues": []}
    player.seek_pause(target)
    before, reason = _settle(player, target, limits, deadline, clock, sleep)
    if reason:
        frame["issues"].append(reason)
    first = player.screenshot()
    sleep(limits.settle_seconds)
    second = player.screenshot()
    after = player.state()
    if watch_video_id(player.url()) != video_id:
        raise CaptureRefused("URL_MISMATCH", "page changed during capture")
    if player.metadata().get("video_id") != video_id:
        raise CaptureRefused("VIDEO_MISMATCH", "player changed during capture")
    late = _problem(after, target, limits.tolerance)
    if late and late not in frame["issues"]:
        frame["issues"].append(f"AFTER_{late}")
    if hashlib.sha256(first).digest() != hashlib.sha256(second).digest():
        frame["issues"].append("FRAME_UNSTABLE")
    if before.get("current_time") != after.get("current_time") \
            or before.get("frame_media_time") != after.get("frame_media_time"):
        frame["issues"].append("TIME_MOVED")
    shown = clock_seconds(str(before.get("clock_text") or ""))
    current = float(before.get("current_time") or 0.0)
    if shown is None or abs(shown - math.floor(current)) > 1:
        frame["issues"].append("DOM_CLOCK_MISMATCH")
    name = f"{seq:04d}-{int(target)}s.png"
    with (batch / "raw" / name).open("xb") as handle:
        handle.write(first)
    frame.update({
        "image_path": f"raw/{name}", "image_sha256": hashlib.sha256(first).hexdigest(),
        "image_bytes": len(first), "player_current_time": current,
        "frame_media_time": before.get("frame_media_time"),
        "player_clock_text": before.get("clock_text"),
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "quality_status": "CAPTURE_AUDIT_ONLY" if frame["issues"] else "CAPTURED_PENDING_REVIEW",
    })
    return frame


def write_watchdog_manifest(out_dir: Path, video_id: str, batch_id: str,
                            seconds: list[float]) -> dict[str, Any] | None:
    """After a hard kill, index surviving images as audit-only; never overwrite a manifest."""
    batch = out_dir / f"{video_id}-{batch_id}"
    if not batch.is_dir() or (batch / "manifest.json").exists():
        return None
    frames = [{"frame_id": f"{video_id}-{batch_id}-{p.name.split('-')[0]}", "video_id": video_id,
               "clock_verified": False, "issues": ["WATCHDOG_TIMEOUT"],
               "image_path": f"raw/{p.name}", "image_sha256": hashlib.sha256(
                   p.read_bytes()).hexdigest(), "quality_status": "CAPTURE_AUDIT_ONLY"}
              for p in sorted((batch / "raw").glob("*.png"))]
    manifest = {"schema_version": 1, "video_id": video_id, "batch_id": batch_id,
                "method": "local_chromium_watch_page_screenshot", "stream_downloaded": False,
                "requested_seconds": seconds, "frames": frames, "not_attempted_seconds": [],
                "refused": "WATCHDOG_TIMEOUT", "refused_detail": "capture process killed"}
    _write_manifest(batch, manifest)
    return manifest


_STATE_JS = """() => {
  const p = document.querySelector('#movie_player');
  if (!p || typeof p.getCurrentTime !== 'function') return {error: 'NO_PLAYER'};
  const v = p.querySelector('video');
  const err = document.querySelector('.ytp-error, yt-playability-error-supported-renderers');
  const f = window.__ddFrame;
  return {player_state: p.getPlayerState(), current_time: p.getCurrentTime(),
          ad_showing: p.classList.contains('ad-showing'),
          video_time: v ? v.currentTime : null, seeking: v ? v.seeking : null,
          ready_state: v ? v.readyState : 0,
          frame_media_time: f && f.token === window.__ddSeek ? f.mediaTime : null,
          clock_text: (document.querySelector('.ytp-time-current') || {}).textContent || null,
          error: err && err.offsetParent !== null ? 'PLAYABILITY_ERROR' : null};
}"""
_SEEK_JS = """(s) => {
  const p = document.querySelector('#movie_player'), v = p.querySelector('video');
  p.pauseVideo();
  const token = window.__ddSeek = (window.__ddSeek || 0) + 1;
  window.__ddFrame = null;
  if (v && v.requestVideoFrameCallback) v.requestVideoFrameCallback((now, md) => {
    if (window.__ddSeek === token) window.__ddFrame = {token, mediaTime: md.mediaTime};
  });
  p.seekTo(s, true);
  p.pauseVideo();
}"""
_META_JS = """() => {
  const p = document.querySelector('#movie_player');
  const r = window.ytInitialPlayerResponse || {};
  const m = (r.microformat || {}).playerMicroformatRenderer || {};
  const d = p && p.getVideoData ? p.getVideoData() : {};
  return {video_id: d.video_id || null, title: d.title || (r.videoDetails || {}).title || null,
          author: d.author || (r.videoDetails || {}).author || null,
          owner_url: m.ownerProfileUrl || null};
}"""


class PlaywrightPlayer:
    """Watch-page driver; screenshots are cropped to the player element.

    A hung renderer can block ``evaluate`` indefinitely, so callers must run this
    under the process watchdog in :func:`main`.
    """

    def __init__(self, page: Any) -> None:
        self.page = page

    def open(self, video_id: str) -> None:
        self.page.goto(f"https://www.youtube.com/watch?v={video_id}", wait_until="domcontentloaded")
        self.page.wait_for_function(
            "() => { const p = document.querySelector('#movie_player');"
            " return p && typeof p.getCurrentTime === 'function'; }", timeout=20000)
        self.page.evaluate("() => { const p = document.querySelector('#movie_player');"
                           " p.mute(); p.pauseVideo(); }")

    def url(self) -> str:
        return str(self.page.url)

    def metadata(self) -> dict[str, Any]:
        return dict(self.page.evaluate(_META_JS))

    def state(self) -> dict[str, Any]:
        return dict(self.page.evaluate(_STATE_JS))

    def seek_pause(self, seconds: float) -> None:
        self.page.evaluate(_SEEK_JS, seconds)
        self.page.hover("#movie_player")

    def screenshot(self) -> bytes:
        return bytes(self.page.locator("#movie_player").screenshot(animations="disabled"))


def launch_options() -> dict[str, Any]:
    options: dict[str, Any] = {"headless": True, "args": ["--no-sandbox"]}
    if os.environ.get("DDERBY_CHROMIUM"):
        options["executable_path"] = os.environ["DDERBY_CHROMIUM"]
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        parsed = urlparse(proxy)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        options["proxy"] = {"server": f"{parsed.scheme}://{parsed.hostname}:{port}"}
        if parsed.username:
            options["proxy"].update(username=unquote(parsed.username),
                                    password=unquote(parsed.password or ""))
    return options


def _run_child(args: argparse.Namespace) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch_options())
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 800}, locale="ja-JP")
            page.set_default_timeout(20000)
            return capture(PlaywrightPlayer(page), args.video_id, args.seconds, args.out_dir,
                           args.batch_id, Limits(budget_seconds=args.budget_seconds))
        finally:
            browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--seconds", type=float, nargs="+", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--budget-seconds", type=float, default=120.0)
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 0 < args.budget_seconds <= 600:
        parser.error("--budget-seconds must be in (0, 600]")
    try:
        _check_ids(args.video_id, args.batch_id)
    except ValueError as error:
        parser.error(str(error))
    if args.child:
        result = _run_child(args)
        print(json.dumps({k: result.get(k) for k in (
            "status", "refused", "refused_detail", "not_attempted_seconds")}
            | {"frames": [(f["frame_id"], f["quality_status"], f["issues"])
                          for f in result["frames"]]}, ensure_ascii=False))
        return
    # Supervisor: the child (and its Chromium) is killed at budget + grace, whatever it is doing.
    child = subprocess.Popen([sys.executable, "-m", "frame_extractor.youtube_capture",
                              *sys.argv[1:], "--child"], start_new_session=True)
    try:
        sys.exit(child.wait(timeout=args.budget_seconds + WATCHDOG_GRACE))
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()
        written = write_watchdog_manifest(args.out_dir, args.video_id, args.batch_id, args.seconds)
        print(json.dumps({"status": "CAPTURE_UNAVAILABLE", "refused": "WATCHDOG_TIMEOUT",
                          "manifest_written": written is not None}))
        sys.exit(2)


if __name__ == "__main__":
    main()
