# ローカルChromiumでの画面取得（Browserbase不使用）

2026-10-28 ユーザー指定: Browserbaseを使わず、実行環境内のChromium + Playwrightで撮影する。
外部ブラウザサービス・有料API・動画stream直接取得は使わない。

## 使い方
```sh
python -m pip install -e '.[capture]'   # playwright==1.63.0（ブラウザ本体は別途）
DDERBY_CHROMIUM=/opt/pw-browsers/chromium \
python -m frame_extractor.youtube_capture --video-id <ID> --seconds 335 350 \
  --out-dir <evidence-dir> --batch-id <一意のbatch> --budget-seconds 120
```
`HTTPS_PROXY` があればChromiumのproxyに渡す。TLS検証は無効化しない。

## 守ること（コードで強制）
- 通常のwatchページのplayerだけを操作し、`#movie_player` の領域だけを撮る（ブラウザUIは含めない）。
- 開いた後のURLのvideo ID、playerの `getVideoData().video_id`、投稿者handleを照合。
  許諾リスト外（`APPROVED_SCOPES`）は撮影前に `PERMISSION_NOT_CONFIRMED` で拒否。
  たかたかchannelはNFKCタイトルに「みんなでダービー2」が必要。ステバイは目視のシリーズ確認が必要。
- 1回の実行は時間上限（既定120秒、最大600秒）。超過分は `not_attempted_seconds` に残す。
  撮影は子プロセスで動かし、上限+60秒で子とChromiumを強制終了する（固まったページ対策）。
  その場合は残った画像を `WATCHDOG_TIMEOUT` の監査用としてmanifestに索引する。
- 地点ごとに、撮影の前と後の両方で、広告なし・一時停止・seek/buffer終了・player/`<video>`の時刻が指定秒±1秒、
  さらにseekごとに仕掛けた `requestVideoFrameCallback` で実際に表示されたframeのmedia timeが指定秒±1秒を確認。
  加えて連続2枚の同一SHA・時刻不変・DOM時計表示一致を見る。1つでも外れた画像は `CAPTURE_AUDIT_ONLY`。
- これらはブラウザ内部の値による検査で、画像そのものの時刻の保証ではない。合成画面が古いまま残る可能性は残る。
- 全frameは `clock_verified=false`。画像内のplayer時計を人/visionが読むまで、観測やverified raceに登録しない。
- 出力 `{video_id}-{batch_id}/raw/{連番}-{秒}s.png` と `manifest.json` は排他的作成で上書きしない。
- 同意画面・bot確認・接続失敗は `CAPTURE_UNAVAILABLE`（`URL_MISMATCH` / `CAPTURE_ERROR`）。迂回しない。

## 現状
- 偽のwatchページを使う結合テストで、Playwright adapterの撮影・時計照合・SHAを確認済み。
- 2026-10-28のクラウド環境では www.youtube.com への接続がegress policyで拒否（ERR_TUNNEL_CONNECTION_FAILED）。
  実YouTubeでの再生・撮影は未検証。環境のNetwork accessで youtube.com 系の許可が必要。
- 許可後も最初は1動画1地点・120秒以内で試し、画像と時計を確認してから範囲を広げる。
- 2026-10-28 ユーザーが www.youtube.com / i.ytimg.com / *.googlevideo.com を許可。atvVcIDscuc 335秒で2回試行し撮影0枚。
  - watchページへの要求の約半数が `https://www.google.com/sorry/...`（Googleの自動アクセス確認）へ302転送された。
    クラウドのIPからの自動アクセスと判定されたとみられる。確認画面は突破・迂回しない。
  - ページが開けた回もplayerが動画情報を返さず `VIDEO_MISMATCH` で停止（安全側）。
  - 映像配信の `rr*.c.youtube.com` はnetwork policyで拒否（www.youtube.com のみ許可のため）。
  - 結論: この環境のIPではYouTubeの自動確認が出るため、クラウドだけでの安定取得は未達。
