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
