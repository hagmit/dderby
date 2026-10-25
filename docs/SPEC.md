# Specification
対象は公開・許諾済みのみんなでダービー2動画のみ。初期 video_id は FQ6S0vUh_NM。
channel_id は Phase 3 の Data API 取得まで未確定。許諾確認済みというユーザー申告は記録するが、
未特定チャンネルを包括承認しない。許諾 registry は空で開始し channel_id と evidence を登録する。

## 品質と再現性
UNKNOWN/BET_OPEN/HORSE_INFO_VISIBLE/ODDS_VISIBLE/PREDICTION_VISIBLE/RACE_RUNNING/RESULT_VISIBLE/NEXT_RACE。
1fps 候補抽出後、必要区間だけ高密度化。全フレーム OCR は禁止。
Game Screen Detection と Perspective Correction、ROI Template、OCR Adapter を独立させる。
複数フレームの合意/中央値/confidence を用いる。不明は NULL + error_reason。
色だけから小数点を挿入して確定しない。隣接フレームの裏付けが得られなければ NULL。
Gauge は fill_ratio 0..1。能力段階数・同名馬の固定性は観測後に検証する。
出走数/重複馬番/結果/odds/必須画面/confidence を検証し不合格は ANALYSIS_EXCLUDED + bounded retry。
Golden 正解を改善目的で変更しない。原文の全項目・研究課題は PROJECT_BRIEF.md を正とする。

## 初回の境界
本コミットは bootstrap と infrastructure scaffold。動画取得、OCR、モデル、Sheets 出力は未実装。
CLI は readiness 診断のみで、本番 worker として動作しない。
