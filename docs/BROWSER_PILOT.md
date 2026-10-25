# Browser screenshot pilot — 2026-10-26 JST

## Scope and permission
ユーザーの追加承認により、課金登録・GCP deploy に先立つ単発検証を実施。
対象は明示指定され、分析・フレーム抽出用途の許諾済みと申告された公開動画1本のみ。
動画 ID: FQ6S0vUh_NM。投稿者表示: ステバイ、handle: @steby0419。
channel_id は未取得。他動画への包括承認は登録していない。

## Method
Chrome の通常 YouTube player で再生・停止、時刻付き URL と5秒 seekを使用。
ブラウザ screenshot を保存し、動画表示領域を crop。動画ファイル・ストリームの直接取得は行わない。
元 viewport screenshot はローカル作業領域に保持し、配布画像は動画領域に限定する。
画像解析はこの実行の vision 読取。独立 OCR engine や校正済み confidence は未実装。
confidence はエージェントの自己評価であり、測定された正答確率ではない。
保存時刻は player の秒表示。decoded frame の厳密な PTS は得られていない。
元 screenshot と crop の SHA256、crop座標、source timestamp を manifest に保持。

## Observed
- 2:20: 2〜6番の単勝 odds 3.4 / 8.2 / 5.8 / 5.1 / 2.9。
- 2:33: 4〜6番の単勝 odds 5.8 / 5.1 / 2.9 を再確認。
- 3番の馬名表示「イッポンゼオイ」、4番「ブラッディバロン」。全6頭の馬名は取得できていない。
- 3:14 と3:19の「確定」表: 単勝5番5.1、馬連5-6 9.9、馬単5→6 21.6。
- 上記馬単表から1着5番、2着6番を読み取れる。
- 画面間の対応は時系列と一致 odds による候補関連付け。明示 race ID/course の根拠不足。

## Quality decision
`ANALYSIS_EXCLUDED`。未知項目を推測補完しない。
全出走馬名、1番の単勝 odds、course/distance、完全な能力表示、race identity が不足。
確定結果の部分観測は保持するが、分析済みレースや学習データとして登録しない。
再試行では前後区間を対象に全馬/レース見出しが映るか確認し、存在しなければ除外を維持する。

## Findings and next implementation
ブラウザだけで screenshot と部分情報を取得できることを確認。GCP 利用・課金設定は実施していない。
斜め撮影、反射、筐体の継ぎ目、手、編集テロップが認識を妨げる。
seek 直後に viewport screenshot が前状態を示す場面があった。指定時刻と実際の停止時刻も数秒異なる。
従って本番 capture adapter には広告/画面状態/停止状態/時刻の安定判定と重複検出が必要。
スクショ取得の成功を、人間確認なしの継続収集や OCR 精度達成とは扱わない。
各画像と JSON/manifest はローカル deliverable に保存し、GitHub に映像や個人の browser UI は公開しない。
