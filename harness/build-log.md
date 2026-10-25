# Build Log

2026-10-26 JST: 新規 hagmit/dderby（空の GitHub repository）を使用。

- Phase 0: Git/GitHub/ネットワーク/bundled Python/環境変数名/既定 ADC パスを確認。
- Phase 1: bootstrap/docs/CI/Dockerfile を作成。新規 venv に editable install 成功。
- Python: ruff 成功、mypy strict は 11 source files 成功、pytest は 2 passed。
- Phase 2: Terraform 1.13.5 の公式 zip と SHA256SUMS を照合。
  SHA256: `73f97943c93f268ae2c645b2a737d552175aa64d00a5c8b8f5ccc5831c033c8a`。
- Terraform: google/google-beta 7.46.2（署名検証された provider、lock file 保存）。
  Pub/Sub service identity のため google-beta を使用。
- Terraform fmt check / validate 成功。mock plan test は 5 passed、0 failed。
  5 buckets/2 datasets、既定 Jobs 無効、bucket 保護、Scheduler 停止、
  不正 environment/可変 tag/画像未指定の拒否を確認。
- 実環境の terraform plan/apply は未実行。GCP 認証・project/Billing/IAM/API は BLOCKED。
- Docker build、ffmpeg、OpenCV、実動画解析は未実行。初回スコープ外の worker は未実装。

2026-10-26 JST（追加依頼）: 公開 YouTube 動画を Chrome 上で操作し screenshot pilot を実施。
2:20/2:33 の odds/馬名部分、3:14/3:19 の確定表を取得。
部分観測を JSON と画像 manifest に記録。必須項目と race identity が不足するため ANALYSIS_EXCLUDED。
本番ロードマップは完了扱いにせず、PLANS.md に独立した Browser Pilot として記録。
検証: crop画像5枚の SHA256、source reference、confidence 範囲、NULL理由、除外判定、着順整合性を確認。
既存 ruff/mypy（11 source files）/pytest（2 passed）と git diff --check は成功。

2026-10-26 JST: 部分観測ledgerを追加。既存pilotと4番の追加属性読取をSQLiteに追記保存。
元pilot JSON/画像は不変。読み直しを独立出現として数えない。
ruff成功、mypy strictは12 source files成功、pytestは9 passed（後日読取でも元NULLを保持する検証を含む）。
実データ同一入力の再実行でinserted_rows=0を確認。本番BigQueryは未稼働。
