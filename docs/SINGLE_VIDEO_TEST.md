# 1本集中テスト（2026-10-26 JST）

ユーザー依頼により FQ6S0vUh_NM（13:25）へ対象を絞り、ブラウザで62地点を実取得。
粗い走査後に馬情報・odds・結果・着順一覧を重点的に再取得した。
新規9区間候補をSQLiteへ追記。旧2:20〜3:19区間のデータも保持している。
新しい馬名候補12頭、表示ゲージ18件、鮮明な確定表4区間、着順一覧1区間などを取得した。
新規715項目 = 非NULL279 + NULL436。非NULLには測定metadata・selection・再観測を含み、独立事実数ではない。
全区間はrace identityや必須項目が不足するためANALYSIS_EXCLUDEDの部分観測として保存。

## 追加した取込対象
horseの他に、race_observations / bet_observations / unassigned_horse_panelsを保存する。
馬番/馬名の見えないstatus panelも、そのまま根拠付きの局所観測として保存可能。
未割当panelやpre-race oddsを、馬属性や確定結果へ誤って結合しない。
従来のpre-raceデータをconfirmed_result_observation配下へ格納する互換策は、新規packetでは不要。
以前の元観測は変更・削除しない。

## ゲージ測定
画面上で見えるbarのROIを指定し、白いprefixの長さ/可視bar幅を測定。
3走査行×RGB最小値閾値130/145/160の中央値を保存。閾値間差0.08超ならNULL。
座標、各行のprefix画素数と分母、閾値、source frameを保持する。
単一frameの未校正画素推定であり、離散能力値へ丸めたりRankから補完したりしない。
視点/圧縮/反射/ROI指定による誤差があり、固定能力やGolden正解としては扱わない。
複数frameでの校正・視点補正・許容誤差評価は未完了。

## 検証と証跡
画像62枚のhash・source参照・重複frame IDを確認。
各packetを再登録し追加0件、SQLite integrity_check=ok。
ruff / mypy strict / unit 10件成功。新テストで未割当statusとpre-race oddsの保持・非結合を確認。
完全な連続動画処理や全レース完成、OCR精度達成とは扱わない。
キューには実取得秒と区間候補IDを保存し、未サンプル時刻を完了区間へ加えない。

成果物は sibling outputs/single-video-test-FQ6S0vUh_NM-001/REPORT.md とCSV。
元証跡・packet・測定履歴は sibling outputs/observation-ledger/evidence/FQ6S0vUh_NM-deep-test001/。
GCPや有料API、動画ストリームの直接取得は利用していない。
