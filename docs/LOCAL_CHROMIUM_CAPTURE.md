# ローカルChromiumでの画面取得（Browserbase不使用）

> **2026-11-10 ユーザー決定: この方式は今後使わない（破棄可）。撮影はClaude in Chrome（ユーザーの通常Chrome）で行う。**
> 手順は末尾の「Claude in Chromeでの撮影」。以下は経緯の記録。
> `frame_extractor.youtube_capture`、そのテスト、`capture` extra（playwright）は削除済み。以下の「使い方」のコマンドは動かない。

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

Windows PC（PowerShell）では、インストール済みのGoogle Chromeを使える:
```powershell
py -3.12 -m venv .venv; .\.venv\Scripts\pip install -e '.[capture]'
$env:DDERBY_BROWSER_CHANNEL = "chrome"
.\.venv\Scripts\python -m frame_extractor.youtube_capture --video-id <ID> --seconds 335 `
  --out-dir ..\capture-evidence --batch-id <一意のbatch> --budget-seconds 120
```
`$env:DDERBY_HEADED = "1"` でブラウザの窓を表示したまま撮影する（既定は非表示）。
強制終了はWindowsでは `taskkill /T` で子とブラウザをまとめて止める。

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
- 2026-11-05/10 ユーザーのWindows PC（`DDERBY_BROWSER_CHANNEL=chrome`）でatvVcIDscuc 335秒を試行。Google確認画面は出なかった。
  - pc001: 一度も再生していないplayerをseekしたため、サムネイル上で時計だけ5:35になり、frameは表示されない（`NOT_PAUSED`）。
  - 対策: 開くときにミュート再生し、frame表示（広告なし・再生中）を待ってから停止する。偽watchページも未再生ならframeを出さないようにして回帰を検出。
  - pc002: 再生・停止は成功（player_state=2）。335秒の映像が15秒の地点上限内に読み込まれず `BUFFERING`。画像は旧frameに読込表示で時計なし。合格0枚。
  - 対策2: 地点ごとに再生中のままseekし、目標±1秒のframe表示を最大15秒待ってから停止・再seekする。
  - pc003: playerがエラー画面（「エラーが発生しました。更新するか、しばらくしてからもう一度お試しください。」）を表示し
    `PLAYER_ERROR`（player_state=-1）。原因は未特定。迂回せず、ここで撮影を停止した。合格0枚。
  - pc004: ユーザー指示で窓を表示（`DDERBY_HEADED=1`）して同じコードで1回再試行。同じエラー画面で `PLAYER_ERROR`。
    再生中seekの導入後は2回とも同じエラー、導入前のpc002では出ていない（因果は未確認）。撮影を停止。
  - pc005と並行検証: 同時刻に、Playwright側pc005は同じエラー画面（3回目）。ユーザーの通常Chrome（Claude in Chrome拡張、
    ログイン済みプロファイル）では同じ動画・335秒が停止状態で正常表示され、画像内の時計は5:35 / 14:11（cic001、手動方式）。
    同じPC・同じ回線・同じ時刻で差が出たので、IPや動画側ではなくPlaywright起動のブラウザ側の条件が疑わしい（原因は未特定）。
    pc005の画像にはページ上部のYouTubeヘッダーが重なって写った（窓表示時のplayer切り出しの不具合、未修正）。

## Claude in Chromeでの撮影（2026-11-10〜の方式）
- 新しいタブで通常のwatchページを開き、URLのvideo ID、playerの `getVideoData().video_id`、投稿者handleを照合する。
  許諾リスト外は撮らない: `@steby0419`（ステバイ、シリーズは目視確認）、`@たかたかchannel`（NFKCタイトルに「みんなでダービー2」が必要）。動画streamは取得しない。エラー・確認画面が出たら止めて報告する。
- 地点ごとに、停止→`seekTo`→停止。撮影の前後でplayerの状態（停止・時刻一致・seek終了・広告なし・エラーなし・
  `requestVideoFrameCallback` の表示frame時刻）を読む。
- マウスをplayerの外に置き、`window.scrollTo(0,0)` と `wakeUpControls()` で操作バー（時計）を出してから、player領域だけを撮る。
  マウスをplayer上に置くとページがscrollしたり、シークバーのプレビューが映像に重なったりする。
- 保存先は `{video_id}-cic{連番}/raw/{連番}-{秒}s.png` と `manifest.json`（method=`claude_in_chrome_manual_screenshot`）。上書きしない。
- 自動の連続2枚SHA照合はない。画像は拡大・再標本化された切り出し。`clock_verified=false` のまま保存し、
  画像内の時計の読取は `image_clock_read` に別記する。観測DBへの登録は別工程。
- 実績: cic001（335秒）、cic002（345/355/365/380/395秒）。全6枚で画像内の時計が指定秒と一致。
