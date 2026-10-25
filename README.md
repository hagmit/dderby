# dderby
許諾済みの公開「みんなでダービー2」動画を構造化する研究基盤。

現状: Phase 0/1 完了。Phase 2 の設計と Terraform scaffold を作成。
GCP 実環境 plan は認証待ち。本番デプロイ・動画解析・予測モデルはまだ実装していません。

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
