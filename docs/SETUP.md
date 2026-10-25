# Setup
## Local
Python 3.12 と Git を用意する。
```powershell
git clone https://github.com/hagmit/dderby.git
cd dderby
python -m venv .venv
.venv/Scripts/python -m pip install -e '.[dev]'
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m mypy src
.venv/Scripts/python -m pytest
.venv/Scripts/python -m dderby
```
Linux では `.venv/bin/python` を使う。CLI は readiness のみ。
Docker がある環境では `docker build -t dderby-bootstrap .` と `docker run --rm dderby-bootstrap`。

## GCP BLOCKED 解除（ユーザー操作）
1. dev project を選択し Billing を確認。prod project は別にする。
2. gcloud CLI を公式から導入し `gcloud auth login`、`gcloud auth application-default login`。
3. `gcloud config set project YOUR_DEV_PROJECT`。
4. 下記 read-only コマンドで project/Billing/IAM/APIs を確認。
```powershell
gcloud projects describe YOUR_DEV_PROJECT
gcloud billing projects describe YOUR_DEV_PROJECT
gcloud projects get-iam-policy YOUR_DEV_PROJECT
gcloud services list --enabled --project YOUR_DEV_PROJECT
```
IAM の付与は管理者と確認する。worker に Owner を与えない。

## Terraform（適用はまだ行わない）
Terraform 1.13.5 を公式配布から導入。
```powershell
cd infra/terraform
terraform init -backend=false
terraform fmt -check -recursive
terraform validate
terraform test
terraform plan -var='project_id=YOUR_DEV_PROJECT' -var='environment=dev' -out=dev.tfplan
```
mock test は認証不要だが provider download が必要。mock plan は実環境 plan の代用ではない。
plan は作成対象、IAM、API有効化、費用をレビューする。apply は初回スコープ外。
初回は API を有効化する想定。YouTube Data API の quota/credential 設定は Phase 3 で確認。
API key は Secret Manager に直接登録し、tfvars/state/Git に入れない。
worker 実装・image build/push・Secret登録後に image digest を指定し Jobs を有効化する。
Scheduler は paused で作り、検証済み worker のみ明示的に再開する。
GCS remote backend と state access policy を確定してから共有運用へ移る。

## Replay / Recovery / Retention
Raw は追記・版管理、処理版を変えて replay。失敗 observation は削除せず隔離。
無限 retry を禁止し DLQ に保存する。worker/replay 実装は Phase 4/16。
GCS 自動削除は無効。保存量・BigQuery scan・Run timeout を監視し保持期間を合意する。
Terraform state の復旧や resource import は事前 plan を確認し、prod destroy は実行しない。
