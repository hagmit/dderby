# 部分観測の蓄積と再出現検証

原設計には全出現保存・Horse Master比較があったが、前回まではJSON保存のみだった。
今回、SQLite観測DBと比較summaryを実装し、既存pilotを登録した。GCP/Billingは不要。
クラウド版Phase 10/11全体の完成とは区別する。

## 手順
1. 読めた値とNULLを、confidence・欠測理由・video・時刻・frameと保存する。
2. 元JSON/manifest/画像をevidenceに追記保管し、元ファイルを上書きしない。
3. 完全なレースになる前でも観測DBへ冪等登録する。ANALYSIS_EXCLUDEDも保存する。
4. 馬名完全一致の候補ごとに、再出現時に読めた属性だけを比較する。
5. 新しい属性は別観測として追加し、過去のNULLは変更しない。
6. 一致・不一致の両方を残す。不一致はCONFLICTとして再検証する。
7. 全馬・レース対応などが整った観測だけを、用途に応じた分析へ進める。

## 重複と同一性
同一出現の隣接画像・再処理・追加読取は独立した再出現ではない。
今回の2:20と2:33は同じ出現候補。3番/4番とも各1出現でUNVERIFIED。
series/video/candidate_race/horse_numberを局所出現キーとする。
candidate_raceの決め方が変わる場合は対応表が必要。自動race segmentationは未実装。
馬名不明は局所出現のまま残し、他レースの同じ馬番と結合しない。
馬名完全一致も個体同一性の証明ではない。後日の名寄せは元観測を保持した別記録で行う。
odds/condition/結果は動的な値。レース間の違いを固定属性の矛盾として扱わない。
gaugeの段階数・許容誤差は推測しない。今回は観測値の完全一致のみを比較する。
一致が繰り返されても、未校正confidenceからFIXEDへ昇格しない。
不一致は低confidenceを含め検証候補として残し、多数決で上書きしない。

## インポート
Python標準のsqlite3を使用。editable install後、以下を実行する。
```powershell
python -m horse_master.observation_store --database ../observation-ledger/observations.sqlite3 --observations ../browser-pilot-FQ6S0vUh_NM-001/observations.json --manifest ../browser-pilot-FQ6S0vUh_NM-001/manifest.json --summary ../observation-ledger/verification-summary.json
```
CLIは画像SHA256と参照を検証する。再実行のinserted_rows=0で冪等性を確認できる。
新規データは別ファイルとして同じCLIで追加する。自動ブラウザ収集との接続は今後の作業。
DBは追記専用。importsに元payload/manifest、observationsに項目値/NULL/根拠を保存する。
DBと画像evidenceを一緒にバックアップし、Gitには含めない。本番BigQueryへの移行は将来の作業。

## 今回のデータ
元JSONと画像5枚をそのままevidenceへ複製・保持した。
2:33画像を再読取し、4番ブラッディバロンのrank=F、sex=♂、running_style=逃げ、
condition=普通を別の追加観測として保存。gaugeや未表示属性はNULLのまま。
同じ画像の再読取であり、新しい出現とは数えない。
レースはANALYSIS_EXCLUDEDのまま、蓄積状態は保存済み。Golden正解や学習用確定値にはしない。

## 性別の比較表記
ユーザー指定の♂=オス、♀=メスをsummaryの比較時だけ正規化する。
元DBのvalue_json・payload・証跡記号は変更しない。比較summaryのsexには
comparison_normalization=sex_labels_v1とobserved_raw_valuesを残す。
表記だけが異なる同義値をCONFLICTへ昇格させず、オスとメスの実際の不一致はCONFLICTとして残す。
同一出現の記号／表示名の再読取は引き続き1出現で、固定性の確定根拠にはしない。
