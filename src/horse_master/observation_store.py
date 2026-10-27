"""Append-only local observation ledger; incomplete races remain useful evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

SERIES = "minna_de_derby_2"
STABLE_FIELDS = {
    "horse_name", "rank", "rank_star_count", "sex", "running_style",
    "speed_fill_ratio", "power_fill_ratio", "stamina_fill_ratio",
}
SEX_LABELS = {"♂": "オス", "♀": "メス"}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS imports (
          import_id TEXT PRIMARY KEY, series TEXT NOT NULL, video_id TEXT NOT NULL,
          payload_json TEXT NOT NULL, manifest_json TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
        CREATE TABLE IF NOT EXISTS observations (
          observation_id TEXT PRIMARY KEY, import_id TEXT NOT NULL REFERENCES imports(import_id),
          field_path TEXT NOT NULL, field_name TEXT NOT NULL, appearance_id TEXT,
          candidate_name TEXT, value_json TEXT NOT NULL, confidence REAL NOT NULL,
          error_reason TEXT, source_refs_json TEXT NOT NULL,
          CHECK(confidence >= 0 AND confidence <= 1));
        CREATE INDEX IF NOT EXISTS candidate_fields
          ON observations(candidate_name, field_name, appearance_id);
    """)
    for table in ("imports", "observations"):
        for action in ("UPDATE", "DELETE"):
            db.execute(
                f"CREATE TRIGGER IF NOT EXISTS {table}_no_{action.lower()} "
                f"BEFORE {action} ON {table} BEGIN "
                "SELECT RAISE(ABORT, 'Observation ledger is append-only'); END"
            )
    return db


def ingest(db: sqlite3.Connection, payload: dict[str, Any], manifest: dict[str, Any]) -> int:
    """Preserve exact imported evidence; reject permission/lineage errors atomically."""
    if payload.get("permission_status") != "approved":
        raise ValueError("Only explicitly approved sources can be imported")
    if payload.get("series", SERIES) != SERIES:
        raise ValueError("Different game series")
    video_id = payload["video_id"]
    frames = {f["frame_id"]: f for f in manifest["frames"]}
    if any(f["video_id"] != video_id for f in frames.values()):
        raise ValueError("Frame belongs to another video")
    import_id = digest([SERIES, payload, manifest])
    rows: list[tuple[Any, ...]] = []

    def visit(obj: Any, path: str, appearance: str | None, name: str | None) -> None:
        if isinstance(obj, dict) and {"value", "confidence", "source_frame_ids"} <= obj.keys():
            confidence = obj["confidence"]
            refs = obj["source_frame_ids"]
            if not 0 <= confidence <= 1 or any(ref not in frames for ref in refs):
                raise ValueError("Invalid confidence or missing source frame")
            if obj["value"] is not None and not refs:
                raise ValueError("Known values require source evidence")
            if obj["value"] is None and not obj.get("error_reason"):
                raise ValueError("Missing values require an error reason")
            rows.append((digest([import_id, path]), import_id, path, path.rsplit(".", 1)[-1],
                         appearance, name, canonical(obj["value"]), confidence,
                         obj.get("error_reason"), canonical([frames[ref] for ref in refs])))
        elif isinstance(obj, dict):
            for key, value in obj.items():
                visit(value, f"{path}.{key}" if path else key, appearance, name)
        elif isinstance(obj, list):
            for index, value in enumerate(obj):
                visit(value, f"{path}[{index}]", appearance, name)

    for horse in payload["horses"]:
        number = horse["horse_number"]
        # Candidate race identity is video-local. A horse number is never a global horse ID.
        appearance = digest([SERIES, video_id, payload["candidate_race_id"], number])
        name = horse["horse_name"]["value"]
        visit(horse, f"horses[{number}]", appearance, name)
    for key in ("course", "distance", "confirmed_result_observation", "race_observations",
                "bet_observations", "unassigned_horse_panels"):
        if key in payload:
            visit(payload[key], key, None, None)
    with db:
        before = db.total_changes
        db.execute("INSERT OR IGNORE INTO imports VALUES (?, ?, ?, ?, ?, "
                   "strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
                   (import_id, SERIES, video_id, canonical(payload), canonical(manifest)))
        db.executemany("INSERT OR IGNORE INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        return db.total_changes - before


def summarize(db: sqlite3.Connection) -> dict[str, Any]:
    """Compare observed values only; never infer missing attributes or promote a master."""
    candidates: dict[str, Any] = {}
    names = db.execute("SELECT DISTINCT candidate_name FROM observations "
                       "WHERE candidate_name IS NOT NULL ORDER BY candidate_name").fetchall()
    for record in names:
        name = record[0]
        fields: dict[str, Any] = {}
        for field in sorted(STABLE_FIELDS):
            rows = db.execute(
                "SELECT o.*, i.video_id FROM observations o JOIN imports i USING(import_id) "
                "WHERE candidate_name=? AND field_name=? AND value_json != 'null'",
                (name, field),
            ).fetchall()
            if not rows:
                fields[field] = {"status": "NOT_OBSERVED", "values": []}
                continue
            values: dict[str, set[str]] = {}
            observed_raw_values = {row["value_json"] for row in rows}
            for row in rows:
                value = json.loads(row["value_json"])
                if field == "sex" and isinstance(value, str):
                    value = SEX_LABELS.get(value, value)
                values.setdefault(canonical(value), set()).add(row["appearance_id"])
            appearances = {r["appearance_id"] for r in rows}
            status = "CONFLICT" if len(values) > 1 else (
                "REPEATED_CONSISTENT" if len(appearances) > 1 else "SINGLE_APPEARANCE"
            )
            fields[field] = {
                "status": status, "independent_appearance_count": len(appearances),
                "video_count": len({r["video_id"] for r in rows}),
                "values": [{"value": json.loads(value), "appearance_count": len(ids)}
                           for value, ids in sorted(values.items())],
                "observation_ids": [r["observation_id"] for r in rows],
            }
            if field == "sex":
                fields[field]["comparison_normalization"] = "sex_labels_v1"
                fields[field]["observed_raw_values"] = [
                    json.loads(value) for value in sorted(observed_raw_values)
                ]
        candidates[name] = {
            "identity_status": "EXACT_NAME_CANDIDATE_ONLY",
            "fixed_status": "CONFLICT" if any(f["status"] == "CONFLICT"
                                                for f in fields.values()) else "UNVERIFIED",
            "fields": fields,
        }
    return {
        "series": SERIES, "import_count": db.execute("SELECT COUNT(*) FROM imports").fetchone()[0],
        "field_observation_count": db.execute("SELECT COUNT(*) FROM observations").fetchone()[0],
        "unnamed_field_observation_count": db.execute(
            "SELECT COUNT(*) FROM observations WHERE appearance_id IS NOT NULL "
            "AND candidate_name IS NULL"
        ).fetchone()[0],
        "candidate_horses": candidates,
        "notes": ["Repeated frames and reprocessing are not independent appearances.",
                  "Condition, odds and results are dynamic; never promoted to fixed attributes.",
                  "Exact names are candidate matches, not verified horse identities.",
                  "Gauge equality is exact observed equality; no tolerance is invented.",
                  "Confidence may be uncalibrated; no FIXED master is generated."],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.observations.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    # Check actual images before preserving a source reference.
    for frame in manifest["frames"]:
        path = args.manifest.parent / frame["image_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != frame["image_sha256"]:
            raise ValueError(f"Evidence hash mismatch: {frame['frame_id']}")
    with connect(args.database) as db:
        inserted = ingest(db, payload, manifest)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summarize(db), ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    print(json.dumps({"inserted_rows": inserted, "database": str(args.database)}))


if __name__ == "__main__":
    main()
