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
