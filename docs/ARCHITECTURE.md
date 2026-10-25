# Architecture
YouTube Data API → permission registry → Pub/Sub processing → VideoSourceAdapter → GCS raw
→ ffmpeg → screen/perspective detection → ROI/OCR/color/gauge → Race Builder/Validation
→ Horse Master → BigQuery → Aggregation/Model → Sheets（出力失敗は非致命）。

## 採用サービス
Cloud Run Jobs（バッチ）、GCS（5用途別bucket）、BigQuery（raw/derived dataset）、Artifact Registry、
Pub/Sub（processing/retry + dead letter）、Cloud Scheduler、Secret Manager、Logging/Monitoring、YouTube Data API v3。
常駐サーバー/Cloud SQL/GKE/Composer は初期構成では不要。
Cloud Run Jobs に push endpoint はないため pull subscription を定期実行 worker が取得する。
Discovery、video、vision、analytics を Scheduler から起動可能。起動はデフォルト無効。
将来 worker は処理終了後 ack、lease extension、bounded retry、DLQ、冪等キーを実装する。

## 分離と保護
project ごと dev/prod 分離を推奨。同一projectでも prefix dderby-{environment} で命名。
Bucket は {project}-{prefix}-{purpose}。dataset は dderby_{environment}_{raw|derived}。
5 bucket は uniform access/public prevention/versioning、force_destroy=false。
保持期間は未合意のため自動削除なし。BQ dataset も内容の一括削除は無効。
Terraform state は機密扱い。backend は dev project 確定後に別管理 GCS へ移行し lock を使う。
初回 scaffold の local state は Git 除外。本番運用には使わない。

## IAM
discovery-worker: Youtube Secret 読取、processing publisher。
video-worker: processing subscriber、retry publisher、raw create/read、frames create/read。
vision-worker: retry subscriber、frames read、cropped/failed create/read、raw dataset editor。
analytics-worker: raw viewer、derived editor、model-artifacts create/read、BQ jobUser。
Scheduler専用 SA: 各 Job の run.invoker のみ。Worker に Owner/Editor/Admin は与えない。
ObjectCreator は上書き不可。既存成果物は hash/version key で参照する。
権限は scaffold 段階。worker 実装時に用途と routing を実測して見直す。

## 運用
Structured log の event=worker_failure を log-based metric と alert policy で監視。
通知先は変数指定。未指定の場合は通知しない。OCR/excluded/conflict/cost は Phase 16 で実装。
YouTube API credentials は Secret container のみ作成し値は Terraform に渡さない。
Cloud Run Job は実装済み container image digest が指定された場合だけ作成。
enable_jobs=false / scheduler_paused=true が既定。bootstrap CLI を解析 Job として公開しない。

## 参考資料（2026-10-26 確認）
- https://docs.cloud.google.com/run/docs/execute/jobs-on-schedule
- https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_scheduler_job
- https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_job
Scheduler の Run API 呼び出しには OAuth token を使用する。
