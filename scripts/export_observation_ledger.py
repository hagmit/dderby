"""Refresh read-only ledger status and CSV; never modify observation records."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from horse_master.observation_store import summarize
from horse_master.verified_races import progress


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    root = args.directory
    uri = f"file:{(root / 'observations.sqlite3').resolve().as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        db.row_factory = sqlite3.Row
        summary = summarize(db)
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        race_progress = progress(db)
        video_count = db.execute("SELECT COUNT(DISTINCT video_id) FROM imports").fetchone()[0]
        known = db.execute("SELECT COUNT(*) FROM observations WHERE value_json!='null'").fetchone()[0]
        hashes = set()
        for row in db.execute("SELECT manifest_json FROM imports"):
            for frame in json.loads(row[0])["frames"]:
                if frame.get("image_sha256"):
                    hashes.add(frame["image_sha256"])
        rows = db.execute(
            "SELECT observation_id,video_id,appearance_id,candidate_name,field_name,value_json,"
            "confidence,error_reason,source_refs_json FROM observations JOIN imports USING(import_id) "
            "ORDER BY video_id,candidate_name,field_name,observation_id"
        ).fetchall()
        with (root / "observations.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["observation_id", "video_id", "appearance_id", "candidate_name",
                             "field", "value_json", "confidence_uncalibrated", "error_reason",
                             "source_frames"])
            writer.writerows(rows)
    preserved_hashes = {
        hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (root / "evidence").rglob("*")
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
    }
    (root / "verification-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8"
    )
    status = {
        "at": datetime.now(timezone.utc).isoformat(), "video_count": video_count,
        "import_count": summary["import_count"],
        "field_observation_count": summary["field_observation_count"],
        "known_field_observation_count": known,
        "missing_field_observation_count": len(rows)-known,
        "candidate_horse_count": len(summary["candidate_horses"]),
        "unique_image_count": len(hashes), "integrity_check": integrity,
        "preserved_evidence_image_count": len(preserved_hashes),
        "validated_unique_race_count": race_progress["validated_unique_race_count"],
        "race_target": race_progress["target"],
        "note": "Field counts include NULL and rereads. unique_image_count is observation-import "
                "images; preserved_evidence_image_count includes audit/human/verified evidence. "
                "Both image counts deduplicate SHA256. Races count only verified_races.",
    }
    (root / "storage-status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2)+"\n", encoding="utf-8"
    )
    text = f"""# 部分観測・蓄積用データ

最新状態: {status['at']}（UTC）。対象動画 {video_count} 本、入力 {summary['import_count']} 件、
項目観測 {len(rows)} 件（NULL・再読取を含む）。馬名候補 {len(summary['candidate_horses'])} 頭。
SHA256で重複除外した保存証跡画像 {len(preserved_hashes)} 枚
（うち部分観測importsから参照 {len(hashes)} 枚）。DB整合性: {integrity}。
検証済みレース {race_progress['validated_unique_race_count']} / {race_progress['target']}。
候補区間や項目数はレース数に含めません。

- observations.sqlite3: 追記専用のローカル観測DB。
- observations.csv: 閲覧用。独立出現数・確定事実数とは異なります。
- verification-summary.json: 名前完全一致候補の項目ごとの一致・矛盾比較。
- storage-status.json: 件数スナップショット。
- race-progress.json: 検証済みレースの進捗。DBのverified_racesが実件数の根拠。
- evidence/: 元画像・JSON・manifestを不変で保管。新しい読取は別packetとして追加。
- processing-queue.json: 動画ごとの実取得時刻・再開位置・失敗/待機状態。

不完全なレース・馬名不明も保存し、欠測を推測補完しません。
同じ画像の再読取は独立再出現に数えず、未校正confidenceから固定属性と断定しません。
Golden正解や学習用確定データではありません。GCP利用・課金設定なし。
通常報告は日本時間9時の1日1回。ローカルPC/アプリ/ブラウザ接続が必要です。
"""
    (root / "README.md").write_text(text, encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
