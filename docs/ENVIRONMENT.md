# Phase 0 Environment Assessment
2026-10-26 JST。調査は Secret 値を表示せず実行。

| 項目 | 確認結果 |
|---|---|
| 作業場所 | 新規 outputs/dderby、空のリポジトリから開始 |
| git | 2.55.0.windows.3 |
| Python | PATH は WindowsApps alias。bundled Python 3.12.14 が実行可能 |
| Docker / gcloud / ffmpeg / gh / uv | PATH に見つからない |
| Terraform | 初期 PATH なし。公式配布 1.13.5 を work/ に検証用配置 |
| OpenCV | bundled Python に未導入 |
| GitHub | connector 認証 hagmit、hagmit/dderby admin/push 可、公開/空リポジトリ |
| Internet | registry.terraform.io:443 疎通、HashiCorp 公式配布取得成功 |
| GCP project/Billing/IAM/APIs | BLOCKED: 認証・project 指定なし、実環境照会不可 |
| ADC | 標準 APPDATA/gcloud の ADC と credentials.db が存在しない |
| 環境変数/Secret | 名前のみ点検。GOOGLE_APPLICATION_CREDENTIALS/GOOGLE_CLOUD_PROJECT/GCP_PROJECT/GH_TOKEN/GITHUB_TOKEN は未設定 |

上記は既定パスとプロセス環境の調査結果であり、他の credential store の不存在を保証しない。
Git credential helper=manager。認証値を取得・保存・表示しない。
Secret Manager の登録有無は GCP 認証後に metadata のみ確認する。
ブロッカーの操作/確認方法は PLANS.md と SETUP.md に記録。
