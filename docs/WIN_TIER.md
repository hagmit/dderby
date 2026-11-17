# 単勝区分（win_races）と撮影リスト

2026-11-10 ユーザー指示。単勝オッズの較正（段階1）を早く始めるため、2着を必須にしない区分を足す。

## 何が違うか
- `verified_races`（500件目標の分子）とは別の追記専用テーブル `win_races` / `win_race_images`。500件には数えない。
- 必須条件は検証済みと同じ（`verified_races.check_common`）。違いは2着が任意なことだけ。
  - 6頭の馬番と事前単勝odds（confidence 0.85以上、BET画面frame）
  - BET→RESULTの対応をreviewerが確認し、3種類以上の視覚根拠を記録
  - 時計を確認した採用frame、BETが結果より前、重複レビュー
- 1着の根拠: 結果画面の直接読取、または同じ結果パネルで実際に払い戻された単勝票（`evidence_kind=PAID_WIN`）。
  払戻済みの単勝が1頭を指せば1着は一意。未払戻・WIN CHANCE・別パネルの組合せは不可。
- 2着を記録するなら、1着と違う出走馬番であること。
- 1着の根拠の種類（`evidence_kind`）は、なし・`VISIBLE_CONFIRMED_PAYOUT_TABLE`・`PAID_WIN` のどれか。2着を記録するなら根拠は結果画面のframe。
- 検証済みレースと区間が重なるもの、検証済みの画像SHAを使うものは登録を拒否する。
  単勝区分に入れた後で同じレースを検証済みに登録した場合は、書出しで単勝区分の行を除く（二重計上しない）。

```powershell
python -m horse_master.win_races --database ../observation-ledger/observations.sqlite3 --record <record.json> --manifest <manifest.json>
python -m horse_master.win_races --database ../observation-ledger/observations.sqlite3 --export win-dataset.json
```
`--export` は検証済み＋単勝区分を1レース1行（tier、6頭odds、1着）で書き出す。DBは変更しない。

## 撮影リスト
```powershell
python scripts/build_capture_plan.py --database ../observation-ledger/observations.sqlite3 --videos ../video-inventory/videos.json --out capture-plan.json
```
DBを読取専用で開き、部分観測から次の2種類と、未撮影区間を出す。登録はしない。
- `RESULT_AFTER_ODDS`: 6頭odds済みで1着なし。根拠frameの最後から120秒先までで結果画面を探す。
- `ODDS_BEFORE_RESULT`: 1着済みで6頭oddsなし。最初の根拠frameの120秒前からオッズ画面を探す。
- `sweeps`: タイトルで本シリーズ確認済みの動画ごとに、30秒を超える未撮影区間。
候補の時刻は値の根拠frameの時刻で決める（1つのimportが動画全体の束を含むことがあるため）。
ウィンドウが重なる候補は、同じ区間を一度撮れば足りる。対応（同じレースか）は撮影後に登録時のreviewで判断し、近さだけで結合しない。

## 撮影の進め方（Claude in Chrome、docs/LOCAL_CHROMIUM_CAPTURE.md の手順）
1. 撮影リストの順に、ウィンドウ内を10秒刻みで止めて撮り、オッズ画面と結果画面を探す。
2. 見つかったら前後を数秒刻みで撮り、対応の根拠（station、馬番・馬名、購入票、odds、コース環境など）を3種類以上そろえる。
3. 1本の動画は最初から最後まで、レースごとに「6頭のオッズ画面」と「結果画面（または払戻票）」の両方をそろえる。
4. 画像は追記専用のevidenceに保存し、`clock_verified` は画像内の時計を読んでから付ける。DB登録は親が直列で行う。
