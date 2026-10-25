# Data Dictionary（設計、テーブル未作成）
BigQuery が System of Record。Sheets は派生表示のみ。

| Table | Logical key | 内容 |
|---|---|---|
| videos | video_id | channel_id/name, title, url, published_at, duration, description, permission_status, processing_status, discovered_at |
| races | race_id | video_id, timestamp, course, distance, direction, track_condition, weather, first/second_place, quality_status |
| race_horses | race_id + horse_number | name raw/normalized, rank/star/sex/style, condition raw/color/icon, odds, gauge ratios, past results |
| race_bets | race_id + bet_type + selection + observation_id | win/quinella 等の odds と根拠 |
| prediction_comments | observation_id | predictor, prediction_mark, comment |
| horse_observations | observation_id | 名前・属性の全出現、動画・レース根拠 |
| horse_master | horse_id | canonical_name, rank/star/sex/style, base_speed/power/stamina, fixed_status, observation/video/conflict_count, first/last_seen, master_confidence |
| extraction_logs | extraction_id | stage, attempts, error_reason, quality metrics |
| model_predictions | model_version + race_id + horse_number | as_of, probability, expected_return |
| model_results | model_version + evaluation_window | logloss, Brier, calibration, hit/ROI/drawdown/streak/bets/skip |

## 共通規約
全レコードに created_at/updated_at（UTC）。派生レコードは video_id/timestamp/frame_id または複数の source_refs、
detector_version/ocr_version/normalization_version/model_version を保持。Raw と Derived を分離する。
認識 field は value（nullable）、confidence [0,1]、error_reason、source_refs を持つ。
odds_raw/numeric/color/color_class、ocr_confidence/color_confidence/final_confidence、corrected を保存。
speed/power/stamina_fill_ratio は [0,1]、不明は NULL。欠測を 0 に置換しない。
permission_status: approved/pending/rejected/revoked。approved 以外は enqueue と処理時点の両方で拒否。
horse fixed_status: UNVERIFIED / PROVISIONALLY_FIXED / FIXED / CONFLICT。
最低3観測2動画で暫定、5観測3動画かつ高confidence一致で固定候補。不一致は CONFLICT。
BigQuery は一意制約を強制しないため staging + MERGE と job key/version で冪等化する。
Raw observation ID は video/frame/ROI/processing_version の決定的ハッシュとする。
初回は warehouse schema の設計のみ。物理 schema と MERGE は Phase 11 で実装・検証。
