"""Drive the real Playwright adapter against a routed offline stand-in for the watch page."""
import os
from pathlib import Path

import pytest

from frame_extractor.youtube_capture import PlaywrightPlayer, capture, launch_options

sync_api = pytest.importorskip("playwright.sync_api")

VIDEO = "r7Bl-CnZ9gs"
PAGE = """<!doctype html><html><body style="margin:0">
<div id="movie_player" style="width:640px;height:360px;background:#123">
  <canvas id="c" width="640" height="300"></canvas><span class="ytp-time-current">0:00</span>
</div><script>
const p = document.getElementById('movie_player'); let t = 0, s = -1;
const draw = () => { const g = document.getElementById('c').getContext('2d');
  g.fillStyle = '#' + (Math.floor(t) * 4567 % 0xffffff).toString(16).padStart(6, '0');
  g.fillRect(0, 0, 640, 300);
  document.querySelector('.ytp-time-current').textContent =
    Math.floor(t / 60) + ':' + String(Math.floor(t) % 60).padStart(2, '0'); };
const video = {get currentTime() { return t; }, seeking: false, readyState: 4,
  requestVideoFrameCallback(cb) { setTimeout(() => cb(0, {mediaTime: t}), 20); }};
p.querySelector = (sel) => sel === 'video' ? video : null;
Object.assign(p, {getCurrentTime: () => t, getPlayerState: () => s, mute() {},
  pauseVideo() { s = 2; }, playVideo() { s = 1; }, seekTo(v) { t = v; draw(); },
  getVideoData: () => ({video_id: 'VIDEO_ID', title: 'test', author: 'a'})});
window.ytInitialPlayerResponse = {microformat: {playerMicroformatRenderer:
  {ownerProfileUrl: 'http://www.youtube.com/@steby0419'}}};
</script></body></html>""".replace("VIDEO_ID", VIDEO)


def test_adapter_captures_player_crop(tmp_path: Path) -> None:
    options = launch_options()
    options.pop("proxy", None)  # every request is fulfilled locally
    if "executable_path" not in options and Path("/opt/pw-browsers/chromium").exists():
        options["executable_path"] = os.environ.get("DDERBY_CHROMIUM", "/opt/pw-browsers/chromium")
    with sync_api.sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(**options)
        except sync_api.Error as error:
            pytest.skip(f"Chromium unavailable: {error}")
        try:
            page = browser.new_page()
            page.route("**/*", lambda route: route.fulfill(content_type="text/html", body=PAGE)
                       if route.request.url.startswith("https://www.youtube.com/watch")
                       else route.abort())
            manifest = capture(PlaywrightPlayer(page), VIDEO, [140.0, 153.0], tmp_path, "it")
        finally:
            browser.close()
    assert manifest["status"] == "CAPTURED_PENDING_REVIEW", manifest
    first, second = manifest["frames"]
    assert first["issues"] == [] and first["player_clock_text"] == "2:20"
    assert first["image_sha256"] != second["image_sha256"]
    assert (tmp_path / f"{VIDEO}-it" / first["image_path"]).read_bytes()[:4] == b"\x89PNG"
