# dderby
許諾済みの公開「みんなでダービー2」動画を構造化する研究基盤。

現状: Phase 0/1 完了。Phase 2 の設計と Terraform scaffold を作成。
GCP 実環境 plan は認証待ち。本番デプロイ・動画解析・予測モデルはまだ実装していません。

追加実装: [部分観測のローカル蓄積](docs/PARTIAL_OBSERVATIONS.md)。
SQLiteへ先に観測を保存し、同名候補の再出現を項目単位で比較できます。
ブラウザでの単発取得は検証済み。継続自動収集・本番BigQuery連携は未実装です。
現在は [複数動画の定期ブラウザ解析](docs/MULTI_VIDEO_OPERATIONS.md) をチャットのheartbeatで継続し、保存状況を日次報告します。

開始方法は [Setup](docs/SETUP.md)、進捗と解除手順は [PLANS.md](PLANS.md)。
原要件は [PROJECT_BRIEF](docs/PROJECT_BRIEF.md)、設計は [Architecture](docs/ARCHITECTURE.md)。

```sh
python -m pip install -e '.[dev]'
python -m ruff check .
python -m mypy src
python -m pytest
python -m dderby
```
Secret は Git に保存しない。不確実な認識値を推測で確定しない。
