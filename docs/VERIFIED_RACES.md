# 検証済み500レースのローカル管理

部分観測のimports/observationsと、検証済みレースのverified_racesを分ける。
前者を削除・上書きせず、後者だけを500件目標の分子に数える。
全馬名・全能力は任意の充足項目。6頭の馬番と事前単勝odds、明示された1/2着は必須。
着順の根拠は結果表・順位表の直接読取、または下記の厳密な払戻票導出とし、両者を区別する。

## 実払戻票から一意に確定する着順

同じWINNING TICKETパネルで単勝aと馬連{a,b}がともに実際に払戻されていれば、
1着a・2着bを論理的に一意に導出できる。これは近い時刻からの推測やWIN CHANCEの当たり予想ではない。
`result.evidence_kind=PAID_WIN_PLUS_QUINELLA`としてrawの券種・選択・正の実払戻額・
共通結果frame・明示的な導出規則を必須保存し、結果表の直接読取として扱わない。
未払戻、馬連だけ、単勝だけ、WIN CHANCE、異なる結果パネル間の組合せは採用しない。
これらは既存の6頭事前odds、同一レース対応、画質・時計・重複検証を省略する理由にならない。

## 登録時の検査

`horse_master.verified_races.register`は公開・許諾済みgame2、画像SHA、画像内時刻の確認、
採用画質、6頭番号の一意性、odds形式/confidence、BETとRESULTの位相、着順整合性を検査する。
事前画面が結果より前にあることだけでは同一レースの証明にならない。
対応関係は実画像を確認したreviewerが、station、馬番/馬名、購入票、odds、コース環境など
少なくとも3種類の具体的な視覚根拠と根拠frameを記述する。
これはエージェントによる視覚レビューであり、confidenceは未校正。無編集の動画とは主張しない。
判断できない場合は候補のままにし、追加証拠を取得する。

同じseries/video/candidate_race_idの再登録は追加0。同じキーの異なる内容は拒否。
同一動画内で重なる区間を別raceとして追加しようとした場合、および既登録の事前/結果画像SHAを
別raceで再利用した場合は拒否する。再投稿・別画角による同一場面の疑いはreviewerが別途確認する。
画像SHAが異なることだけで物理的に別のレースとは判断しない。
verified_racesとverified_race_imagesはUPDATE/DELETEを拒否する。
訂正・撤回が必要な場合は将来の明示的な訂正手順を実装してから反映し、黙って書き換えない。

進捗は`race-progress.json`、各判定根拠は動画別evidenceに保存する。
`progress(db)`はverified_racesの実件数だけを返し、部分データや候補数を足さない。
SQLite整合性、同一入力再登録追加0、未知/誤参照/未許諾/時刻不明/着順不整合/重複拒否を確認する。
これはローカル研究用で、本番Phase9全体の完成や500件達成を意味しない。

レビュー記録をregistry形式へ構造化した後、CLIでも登録できる。
```powershell
python -m horse_master.verified_races --database ../observation-ledger/observations.sqlite3 --record <registry.json> --manifest <registry-manifest.json>
```
manifestのimage_pathはmanifestファイルから相対。再実行はinserted=falseとなる。
