# 実行計画

2026-10-26 JST。リポジトリ: hagmit/dderby。初回スコープ: Phase 0、1、2 の設計/scaffold。

Phase 2 の実環境 plan が通るまで Phase 3 に進まない。scaffold の完成と Phase 完了を区別する。

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
Phase 2: dev の実環境 plan をレビューし Done 条件を満たす。その後 Phase 3。
