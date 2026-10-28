# 実行計画

2026-10-26 JST。リポジトリ: hagmit/dderby。初回スコープ: Phase 0、1、2 の設計/scaffold。

本番ロードマップは Phase 2 の実環境 plan が通るまで Phase 3 に進まない。
2026-10-26 のユーザー追加承認により、課金なしのブラウザ検証を独立して先行する。
scaffold/単発検証の完成と本番 Phase 完了を区別する。

| Phase | 名称 | 状態 | Done 条件 |
|---|---|---|---|
| 0 | Environment Assessment | COMPLETED | 利用環境・権限・ツール・BLOCKED が明確 |
| 1 | Repository Bootstrap | COMPLETED | 新規環境で依存導入、lint/type/unit が成功 |
| 2 | GCP Infrastructure | BLOCKED | terraform validate 成功、認証済み plan で想定 Resource 確認、Secret 不在 |
| 3 | YouTube Discovery | NOT_STARTED | Discovery 再実行で重複せず新着だけ検出 |
| 4 | Video Source / Ingestion | NOT_STARTED | 許諾済み動画1本を Pipeline へ投入 |
| 5 | Frame Extraction | NOT_STARTED | 動画1本から BET/HORSE INFO/RESULT 候補を自動抽出 |
| 6 | Vision Foundation | NOT_STARTED | 代表画像から horse_name/win_odds/result 構造化 |
| 7 | Odds Recognition | NOT_STARTED | Golden Dataset の Odds Exact Match を計測 |
| 8 | Horse Attribute Recognition | NOT_STARTED | 1頭の rank/condition/speed/power/stamina 自動取得 |
| 9 | Race Builder | NOT_STARTED | 1レースを検証付き構造化 Record として保存 |
| 10 | Horse Master Resolver | NOT_STARTED | 新観測で Horse Master 自動更新 |
| 11 | Data Warehouse | NOT_STARTED | 分析から video/timestamp/frame へ lineage 追跡 |
| 12 | Google Sheets Output | NOT_STARTED | 主要結果をスマートフォンで確認 |
| 13 | Golden Dataset / Evals | NOT_STARTED | 固定 Golden Dataset で regression/improvement 自動判定 |
| 14 | Aggregation | NOT_STARTED | Odds 以上の情報を持つ特徴量候補を探索 |
| 15 | Prediction Model | NOT_STARTED | 未来データで M0 を上回るモデルのみ採用 |
| 16 | Continuous Operation | NOT_STARTED | Discovery から Aggregation まで無人継続処理 |
| 17 | Operations Documentation | NOT_STARTED | Setup/IAM/Secret/deploy/test/retry/recovery/retention/cost/model/troubleshooting 文書化 |

## TODO 状態（全 TODO）
詳細な作業内容は docs/PROJECT_BRIEF.md の同じ ID を参照。

### Phase 0
- 0-1: COMPLETED
- 0-2: COMPLETED
- 0-3: BLOCKED
- 0-4: COMPLETED
### Phase 1
- 1-1: COMPLETED
- 1-2: COMPLETED
- 1-3: COMPLETED
- 1-4: COMPLETED
- 1-5: COMPLETED
- 1-6: COMPLETED
### Phase 2
- 2-1: IN_PROGRESS
- 2-2: IN_PROGRESS
- 2-3: IN_PROGRESS
- 2-4: IN_PROGRESS
- 2-5: IN_PROGRESS
- 2-6: IN_PROGRESS
- 2-7: IN_PROGRESS
- 2-8: IN_PROGRESS
- 2-9: IN_PROGRESS
- 2-10: IN_PROGRESS
### Phase 3
- 3-1: NOT_STARTED
- 3-2: NOT_STARTED
- 3-3: NOT_STARTED
- 3-4: NOT_STARTED
- 3-5: NOT_STARTED
- 3-6: NOT_STARTED
- 3-7: NOT_STARTED
### Phase 4
- 4-1: NOT_STARTED
- 4-2: NOT_STARTED
- 4-3: NOT_STARTED
- 4-4: NOT_STARTED
### Phase 5
- 5-1: NOT_STARTED
- 5-2: NOT_STARTED
- 5-3: NOT_STARTED
- 5-4: NOT_STARTED
- 5-5: NOT_STARTED
### Phase 6
- 6-1: NOT_STARTED
- 6-2: NOT_STARTED
- 6-3: NOT_STARTED
- 6-4: NOT_STARTED
- 6-5: NOT_STARTED
### Phase 7
- 7-1: NOT_STARTED
- 7-2: NOT_STARTED
- 7-3: NOT_STARTED
- 7-4: NOT_STARTED
- 7-5: NOT_STARTED
- 7-6: NOT_STARTED
- 7-7: NOT_STARTED
### Phase 8
- 8-1: NOT_STARTED
- 8-2: NOT_STARTED
- 8-3: NOT_STARTED
- 8-4: NOT_STARTED
- 8-5: NOT_STARTED
### Phase 9
- 9-1: NOT_STARTED
- 9-2: NOT_STARTED
- 9-3: NOT_STARTED
- 9-4: NOT_STARTED
- 9-5: NOT_STARTED
### Phase 10
- 10-1: NOT_STARTED
- 10-2: NOT_STARTED
- 10-3: NOT_STARTED
- 10-4: NOT_STARTED
### Phase 11
- 11-1: NOT_STARTED
- 11-2: NOT_STARTED
- 11-3: NOT_STARTED
- 11-4: NOT_STARTED
### Phase 12
- 12-1: NOT_STARTED
- 12-2: NOT_STARTED
- 12-3: NOT_STARTED
### Phase 13
- 13-1: NOT_STARTED
- 13-2: NOT_STARTED
- 13-3: NOT_STARTED
- 13-4: NOT_STARTED
- 13-5: NOT_STARTED
### Phase 14
- P14-scope: NOT_STARTED — 原文の集計/運用文書化要件を実装・検証する。
### Phase 15
- 15-1: NOT_STARTED
- 15-2: NOT_STARTED
- 15-3: NOT_STARTED
- 15-4: NOT_STARTED
- 15-5: NOT_STARTED
### Phase 16
- 16-1: NOT_STARTED
- 16-2: NOT_STARTED
- 16-3: NOT_STARTED
- 16-4: NOT_STARTED
- 16-5: NOT_STARTED
- 16-6: NOT_STARTED
- 16-7: NOT_STARTED
### Phase 17
- P17-scope: NOT_STARTED — 原文の集計/運用文書化要件を実装・検証する。

## Phase 2 の到達点
設計と Terraform scaffold は実装済み。fmt/validate と mock provider plan test でローカル検証する。
2-1〜2-10 は実環境 plan 未確認のため IN_PROGRESS。実環境への apply は未実行。
Pub/Sub は pull 型。定期起動する各 Cloud Run Job が queue を pull する設計。Pub/Sub が Job を直接起動するとは仮定しない。

## BLOCKED と解除手順
- GCP: project ID、Billing、IAM、Cloud APIs は認証がないため未確認。Secret の有無も未確認。
- ユーザー操作: dev 用 GCP project を選択し Billing を確認。gcloud を導入し `gcloud auth login` と `gcloud auth application-default login` を実行。
- 確認方法: docs/SETUP.md の read-only チェックと terraform plan。ADC やキーをチャット/Git に貼らない。
- GitHub Actions 実行結果は push 後に確認。GitHub リポジトリ接続自体は確認済み。
- Docker/ffmpeg/gcloud/OpenCV は初期環境にない。Phase 4〜5 前に導入/コンテナ検証する。

## 次の作業
部分観測の先行蓄積を通常手順に追加済み。新しい画像読取は観測DBへ先に登録し、
同名候補と項目ごとに比較する。読めない箇所はNULL、分析除外でも元観測は保持する。
ブラウザ検証の次: player 領域・時刻・読み込み完了を安定確認する capture adapter と画面検出を実装し、
未編集または情報がそろう映像で複数フレームの抽出精度を評価する。課金登録はこの検証の前提ではない。
クラウド運用を選択した時点で Phase 2 の dev plan を確認し、その後 Phase 3 へ進む。

## Browser Pilot（追加スコープ）
- BP-1: COMPLETED — FQ6S0vUh_NM を Chrome で再生・停止・時刻移動し screenshot を取得。
- BP-2: COMPLETED — 馬名/odds/確定結果の一部を screenshot から読み取り、confidence と provenance を保存。
- BP-3: COMPLETED — 不完全な出走表・race identity の不足により ANALYSIS_EXCLUDED と判定。
- BP-4: NOT_STARTED — 再利用可能な自動 capture adapter、画面状態検出、OCR eval を実装。
- 今回はエージェントによる単発ブラウザ操作/画像読取。継続収集 worker や精度評価の完成ではない。
- 元 screenshot はローカル work/browser-pilot、動画領域のみの画像/JSON/レポートは sibling outputs/browser-pilot-FQ6S0vUh_NM-001。
- 実測内容と制約は docs/BROWSER_PILOT.md。GCP/Billing 設定・動画ファイル取得・クラウドAPI呼出は未実施。

## Partial Observation Ledger（追加スコープ）
- PO-1: COMPLETED — 設計と既存実装を確認。旧実装はJSON保存まででDB未実装と判明。
- PO-2: COMPLETED — SQLite追記専用DB、内容hashによる冪等登録、欠測/根拠/品質除外の保存。
- PO-3: COMPLETED — 完全一致名候補の項目別比較。同一出現の複数frame・再処理を重複計数しない。
- PO-4: COMPLETED — 既存pilotを登録、画像/JSONを証跡として保管し、4番の見える属性を別観測で追加。
- PO-5: COMPLETED — 部分保存・再実行・再出現一致/矛盾・許諾/series/根拠拒否を単体検証。
- PO-6: NOT_STARTED — capture workerとの自動接続、race identity/名寄せ解決、本番BigQuery移行。
- Phase 10/11本番ロードマップ全体は未完了。今回の局所実装とは区別する。
- ローカル保存先: sibling outputs/observation-ledger。手順: docs/PARTIAL_OBSERVATIONS.md。

## Multi Video Operation（追加スコープ）
- MV-1: COMPLETED — 解析再開用hourly heartbeatと日本時間9時の日次保存状況報告を設定。
- MV-2: IN_PROGRESS — 動画別担当による並行解析。初回は新動画fwAHVINOS0Aと既存FQ6S0vUh_NM証跡の未読項目検証。
- MV-3: IN_PROGRESS — 部分観測packetを動画別保存し、親がSQLiteへ直列に冪等登録。
- MV-4: NOT_STARTED — 独立常駐capture worker。本番cloudへは適用しない。
- 永続キュー・再開位置・失敗理由はsibling outputs/observation-ledger/processing-queue.json。
- 初回並行バッチは登録完了。以後はhourly heartbeatからキューの再開位置へ進む（継続運用としてIN_PROGRESS）。

## Single Video Deep Test（追加スコープ）
- SV-1: COMPLETED — FQ6S0vUh_NMを62地点サンプリング、馬情報/odds/結果を重点取得。
- SV-2: COMPLETED — 新規9区間候補の部分観測を追記、名前不明panelと事前betを独立保存。
- SV-3: COMPLETED — 18ゲージの画素推定と座標/閾値/測定履歴を保存（単一frame、未校正）。
- SV-4: COMPLETED — 画像hash、冪等再登録追加0、SQLite整合性、lint/type/unit 10件を確認。
- SV-5: NOT_STARTED — 視点補正・複数frame校正・完全なレースidentity・画面検出精度の評価。
- 成果と制約: docs/SINGLE_VIDEO_TEST.md。本番Phase完了や連続全フレーム解析とは区別する。

## Additional Video Deep Sampling（追加スコープ）
- AV-1: COMPLETED — 同投稿者の公開r7Bl-CnZ9gs / oo5qvMZKkXwをブラウザで確認。
- AV-2: IN_PROGRESS — r7は64地点を保管、8区間候補の馬属性・馬連odds・部分結果・27ゲージ測定履歴を追記。未読画像と出走枠欠測が残る。
- AV-3: BLOCKED — ooは135秒の1枚と部分払戻を保存。ブラウザ取得タイムアウトと担当agent使用上限により高密度取得未達。次回45秒からbounded retry。
- AV-4: COMPLETED — 今回9packetの再登録追加0、画像SHA確認、DB整合性ok、unit10件/lint/type成功。
- 保存状況: 4動画、22imports、1580項目（既知591/NULL989）、馬名候補24、SHA重複排除画像134。項目数は独立事実数ではない。
- 詳細と実再開点はsibling observation-ledger/evidence/*-deep001 とprocessing-queue.json。連続区間の完了は宣言しない。

## 500 Race Collection（追加スコープ）
- R500-1: IN_PROGRESS — 独立画像レビューでFQの3件、実払戻票の厳密導出でr7の1件を登録し現在4/500。部分観測は別途保持し、項目数を完成レース数に加算しない。
- R500-2: IN_PROGRESS — FQ6S0vUh_NMの420–470秒も登録済み。次はIY1rJk8HJtEの362秒払戻に対応する事前6頭oddsの欠測を重点確認。最初の2件は馬番/馬名、複数odds、購入票→払戻票、station/credit/背景を照合。元動画が無編集という保証はしない。
- R500-3: IN_PROGRESS — 他投稿者2チャンネルを許諾確認候補として提示済み。許諾はユーザー取得待ち。許諾済みソースは継続する。
- R500-4: BLOCKED — IY1rJk8HJtEの投稿者/シリーズは確認したが、停止72秒でスクショ取得2回タイムアウト。画像・項目の追加0。先行動画の完成度監査へ切替。
- 監査詳細はsibling observation-ledger/race-readiness-audit.json/.md、進捗はrace-progress.json。部分観測DBは保持し、本番Phase9の完成とは区別する。
- 旧AV-3の使用上限停止は解消済み。oo5qvMZKkXwの再開証跡は保存・登録済み。旧記載は当時の履歴で、現在の再開状態はprocessing-queue.jsonを正とする。
- R500-5: COMPLETED — 局所verified registry、SHA/時計/6頭/odds/位相/結果/複数根拠/重複拒否/追記専用を実装。19unit、lint/type、実画像2件登録/再登録0/DB整合性okを確認。仕様はdocs/VERIFIED_RACES.md。500件の収集と本番Phase9全体は未完了。
- R500-6: COMPLETED — 同一実払戻パネルの単勝+馬連から着順を一意に導出する型を追加。WIN CHANCE/未払戻/選択不整合/根拠不足を拒否。24unit/lint/type成功。r7の295–335秒を2→4として追加し、現在3/500、再登録追加0、DB整合性ok。
- R500-7: BLOCKED — 残り497件は追加画面取得が必要。ブラウザURLを安全に確認できずComputer Useが停止し、複数のgoal継続でも復旧なし。保存済みqnf/r7/OOの完成度監査と取り込み可能な候補の処理を実施済み。ユーザーによるブラウザ接続復旧が必要。他投稿者は許諾確認待ち。未完了を達成扱いにしない。

- R500-8: IN_PROGRESS — ユーザーの「続き」でChrome接続を再確認し、URL/画像の照合が成功して取得停止を解消。FQ追加11地点で420–470秒を登録し再登録追加0。IYは全体の疎な走査と重点取得を行い、部分情報を先に保存。562–595秒はWIN CHANCEと実払戻を区別し、4/6の着順が未確定のためHOLD。旧R500-4/7は停止当時の履歴で、現在はprocessing-queue.jsonを正とする。DB整合性ok、500件目標は未完了。

- R500-9: IN_PROGRESS — 未解析atvVcIDscuc/Eyp7yBAtA8oを2担当で並列検証。画面取得は直列化し62/67枚を証跡保存、25packet/1440項目（NULL・再読取を含む）を追加。atv170–230秒は親の画像照合後に実払戻票から1→3を登録し計5/500、再登録追加0。Eyp439–490秒は着順導出と事前対応を区別しリンク不足でHOLD。全編解析完了は0本のまま。
- MV-5: IN_PROGRESS — ユーザーの追加許諾でたかたかchannelを承認スコープへ追加。タイトルに「みんなでダービー2」を含む公開6本をブラウザDOMで確認し分析キューへ登録。みんダビ王等の未許諾ソースは処理しない。

- MV-6: IN_PROGRESS — 追加承認のたかたかchannel6本はすべて画像保存に着手。part1〜4の部分観測と短いmontageの市場を別枠保存。yrYの初期15枚＋後半42枚を時計/SHA照合し、実払戻馬単6→2もrawで保存したが事前対応の第3根拠不足でHOLD。今回3batch/15packet/930項目を追加、再登録0・DB整合性ok。500件目標は5件のまま。追加取得320秒は同一タブで2回画像timeoutのためbounded retry停止。未許諾チャンネル探索は新規一次確認0、二次索引leadのみ保留保存。

- MV-7: IN_PROGRESS — fwAHVINOS0Aを全長の56地点＋重点12地点で取得し、前後半を2担当で並列レビュー。18packet/603項目を先行保存、同入力再登録0・DB整合性ok。440–480秒は明示結果と馬単odds一致を確認したが、6頭事前単勝盤が画角外で437–441秒の精査でも不足、HOLD。結果のみの720/800/820等は別候補に保持し、完成5/500を増やさない。Tab.screenshotのtimeout時、URL照合可能な同一タブの文書化されたTab.getScreenshotで画面・時計を確認し取得成功。別投稿者kodomoyoのExpo2025版1本を一次metadata確認し許諾pending登録、再生解析は未着手。クラウド引継ぎ一式はローカル準備済み、宛先確認/転送/切替は未完了。

- PO-7: COMPLETED — 性別の比較summaryで♂/オス・♀/メスだけを同義として正規化。原DB/payload/SHA・出現キーは保持し、summaryに元表記と正規化版を明記。従来の性別表記差7件を矛盾から除外し、実際のオス/メス差はCONFLICTを保持。同一出現の表記再読取・元値保持を含む28unit、lint/type成功。summary再作成前後の元DB SHA一致を確認。500件収集の完了とは区別。

## Cloud Data Handoff（追加スコープ、2026-10-27）
- CH-1: COMPLETED — ユーザー指定の既存クラウドchatへ画像なし構造化snapshotを引継ぎ。非公開hagmit/dderby-dataの固定commit 79ab83298aacdbe40f70f0713ec98043c8146505を使用。41分割のSHA/サイズ、2,634,143 bytes ZIPのSHA/CRC、同梱ファイル、SQLite整合性・件数を移行先でread-only検証済み。14動画/133imports/6590項目（NULL・再読取を含む）/検証済み5レースを継承し、全編完了動画は0。画像本体の再検証とは区別する。
- CH-2: COMPLETED — 画像790ファイル/733unique SHAは元PCに不変保管。画像索引・読取JSON・キュー・運用条件を移行先に保存し、画像が必要な作業はSOURCE_IMAGE_REQUIREDとして必要分のみ後送。元PCとsnapshotのDB内容はschema/全行一致を確認。SQLite backupのファイルheader差をデータ差と扱わない。
- CH-3: BLOCKED — クラウドchatにYouTubeブラウザ/CUA機能がなく、新規画面取得は未再開。構造化データの受渡し完了と継続収集の稼働を区別する。ローカル収集と旧scheduleは停止し、二重書込を避ける。500件の目標は5/500のまま未完了。
- CH-4: COMPLETED — 日次報告を移行先の既存chatに1件登録し有効状態を確認。設定上の初回は2026-10-28 09:00 Asia/Tokyo、以後毎日9時。workspace永続性を仮定せず、private GitHubのcurrent-snapshot.jsonとreporting/daily-report-state.jsonを再開元とし、必要時にsnapshotを復元してread-only確認する。10/27の報告済み状態を継承。次回実行時刻APIはnullのため、初回時刻は保存済みscheduleによる確認であり実行成功を先取りしない。
- CH-5: IN_PROGRESS — ユーザー指定でBrowserbaseを使わず、環境内Chromium+Playwrightの撮影adapterを実装（docs/LOCAL_CHROMIUM_CAPTURE.md）。許諾handle/タイトル照合、URL/video ID照合、120秒上限、広告/停止/seek/画面安定/DOM時計の検査、追記専用出力、clock_verified=false。unit+偽watchページの結合テスト、lint/type成功。実YouTubeはegress policyで接続拒否のため未検証、DB登録0、完成5/500のまま。通信許可後の試行2回はGoogleの自動アクセス確認（google.com/sorry）への転送とplayer情報なしで撮影0枚、確認画面は迂回しない。
