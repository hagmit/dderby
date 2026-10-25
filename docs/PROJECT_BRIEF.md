```text
あなたはこのRepositoryのLead Engineer、Infrastructure Engineer、Data Engineerです。

このタスクでは、メダルゲーム「みんなでダービー2」の許諾済み公開YouTubeプレイ動画を継続的に収集・解析し、レース情報を画像認識によって自動構造化し、将来的な統計分析・攻略モデル構築に利用できるクラウド基盤を構築してください。

対象チャンネルについては、投稿者から分析・フレーム抽出用途について確認済みです。

対象は公開動画のみです。

本番運用では人間による画面検知・OCR修正を必要としない設計にしてください。

画像認識に失敗した場合は推測による補完を行わず、再処理またはANALYSIS_EXCLUDEDとして扱ってください。


# 最終目的

以下のパイプラインを構築する。

YouTube Discovery
↓
Permission Check
↓
Video Ingestion
↓
Cloud Storage
↓
Frame Extraction
↓
Screen State Detection
↓
Vision / OCR / Color Detection
↓
Race Builder
↓
Automatic Validation
↓
Horse Master Resolver
↓
BigQuery
↓
Aggregation
↓
Statistical Analysis
↓
Prediction Model
↓
Google Sheets / Dashboard


# Codexの作業原則

このRepositoryで作業を開始したら、最初に以下を読むこと。

AGENTS.md
GOALS.md
PLANS.md
docs/SPEC.md
docs/DATA_DICTIONARY.md
docs/ARCHITECTURE.md

存在しない場合は、内容を設計したうえで作成すること。

大規模な変更を一度に実装しないこと。

各Phaseについて、

現状確認
↓
設計
↓
実装
↓
テスト
↓
Done条件確認
↓
コミット可能な状態に整理

の順で進めること。

各PhaseのDone条件を満たしてから次のPhaseへ進むこと。

認証、課金、OAuth同意、GitHub接続、GCPアカウント操作など、ユーザーによる操作が必須の場合は以下を明示すること。

BLOCKED理由
ユーザーが実行する操作
操作完了後の確認方法

ただし、ユーザー操作が必要な項目があっても、そこでプロジェクト全体を停止しないこと。

認証なしで実行可能な、

Repository Bootstrap
コード生成
Terraform作成
Schema作成
Unit Test作成
Dockerfile作成
CI作成
ドキュメント作成

などは先に進めること。

既存ライブラリ、GCPマネージドサービス、標準ツールを優先する。

独自実装は最後の手段とする。

Secret、APIキー、サービスアカウント秘密鍵をGitへ保存しない。

本番データを破壊的に変更しない。

GCP Resource削除、IAMの大幅変更、本番Secret上書きなど不可逆性の高い変更は勝手に実行しない。

本番書込処理は冪等にする。


# TODO STATUS

全TODOを以下のいずれかで管理する。

NOT_STARTED
IN_PROGRESS
COMPLETED
BLOCKED

PLANS.mdをプロジェクト全体のSource of Truthとする。

必要に応じて、

harness/build/

配下へPhaseごとの実行計画を作成する。


# =========================================================
# PHASE 0
# Environment Assessment
# =========================================================

TODO 0-1

現在のCodex実行環境を調査する。

確認するもの:

git
Python
Docker
gcloud CLI
Terraform
ffmpeg
OpenCV
GitHub接続
インターネットアクセス
利用可能な環境変数
利用可能なSecret

不足しているものを整理する。


TODO 0-2

GitHub Repositoryへのアクセス状況を確認する。

Repositoryが存在しない場合は、

mindabi2-research

というRepositoryを前提にBootstrapファイルを作成する。


TODO 0-3

GCPへのアクセス状態を確認する。

確認:

GCP Project
Billing
IAM
Cloud APIs

認証情報が存在しない場合はBLOCKEDにし、必要なユーザー操作を記録する。


TODO 0-4

本システムで使用するGCPサービスを確定する。

候補:

YouTube Data API v3
Cloud Run Jobs
Cloud Storage
BigQuery
Artifact Registry
Pub/Sub
Cloud Scheduler
Secret Manager
Cloud Logging
Cloud Monitoring

不要なサービスは採用しない。


DONE CONDITION

現在使用可能な環境、権限、ツール、BLOCKED項目が明確になっている。


# =========================================================
# PHASE 1
# Repository Bootstrap
# =========================================================

TODO 1-1

以下を作成する。

AGENTS.md
GOALS.md
PLANS.md
README.md
pyproject.toml
.gitignore
.env.example


TODO 1-2

以下のRepository構成を作成する。

src/
  discovery/
  ingestion/
  frame_extractor/
  screen_detector/
  vision/
  race_builder/
  horse_master/
  aggregation/
  modeling/

schemas/

sql/

tests/
  unit/
  integration/
  fixtures/

evals/
  golden/

infra/
  terraform/

scripts/

harness/
  build/
  context/
  build-log.md

docs/
  SPEC.md
  DATA_DICTIONARY.md
  ARCHITECTURE.md
  RESEARCH_LOG.md


TODO 1-3

AGENTS.mdへ以下を記載する。

変更前にGOALS.md、PLANS.md、SPEC.md、DATA_DICTIONARY.mdを読む。

推測値を確定データとして保存しない。

認識値にはconfidenceを保存する。

生データを破壊的に更新しない。

別シリーズの情報を混在させない。

permission_status=approvedの映像のみ解析する。

本番書込処理は冪等にする。

SecretをRepositoryへ保存しない。

変更後は必ずテストする。

Golden Datasetの正解データをモデル改善のために変更しない。


TODO 1-4

GOALS.mdへ以下の最終目標を記録する。

許諾済みのみんなでダービー2動画から、人間による画面確認なしでレース情報を継続収集する。

オッズ、馬情報、能力、状態、予想情報、結果を構造化する。

Horse Masterを構築する。

最終的に表示オッズ以上の予測力を持つ特徴量を発見する。

アウト・オブ・サンプルデータで回収率改善を検証する。


TODO 1-5

PLANS.mdへPhase 0からPhase 17までのロードマップと各Done条件を記録する。


TODO 1-6

CIを作成する。

最低限:

lint
type check
unit test


DONE CONDITION

Repositoryをcloneした新しい環境で依存関係を導入し、テストを実行できる。


# =========================================================
# PHASE 2
# GCP Infrastructure
# =========================================================

Infrastructure as CodeにはTerraformを優先する。


TODO 2-1

dev / prodを分離可能なResource命名規則を設計する。


TODO 2-2

Cloud Storage Bucket構造を設計する。

用途:

raw-video
frames
cropped-images
failed-extractions
model-artifacts


TODO 2-3

BigQuery Datasetを設計する。


TODO 2-4

Artifact Registryを設計する。


TODO 2-5

Cloud Run Jobsを実行できる基盤を設計する。


TODO 2-6

Pub/Sub Topic / Subscriptionを設計する。


TODO 2-7

Cloud SchedulerからDiscoveryを起動可能にする。


TODO 2-8

Secret Managerを利用する。

Secret候補:

YouTube Data API credentials
その他必要なAPI credentials


TODO 2-9

Service Accountを役割別にする。

discovery-worker
video-worker
vision-worker
analytics-worker

Least Privilegeを適用する。

WorkerへOwner Roleを与えない。


TODO 2-10

Cloud Logging / Monitoringを設定可能にする。


DONE CONDITION

terraform validateが成功する。

terraform planで想定Resourceが確認できる。

SecretがRepositoryに含まれていない。


# =========================================================
# PHASE 3
# YouTube Discovery
# =========================================================

初期検証対象動画:

https://youtu.be/FQ6S0vUh_NM

この動画を起点に対象channel_idを特定する。

対象チャンネルについては分析・フレーム抽出用途の許諾確認済み。


TODO 3-1

video_idからchannel_idを取得する。


TODO 3-2

対象チャンネルのuploads一覧を取得する。


TODO 3-3

新着動画を継続検出する。


TODO 3-4

タイトル・説明等から対象ゲーム候補を分類する。

候補キーワード:

みんなでダービー2
みんダビ2


TODO 3-5

videosテーブルへ以下を保存する。

video_id
channel_id
channel_name
title
url
published_at
duration
description
permission_status
processing_status
discovered_at


TODO 3-6

video_idをunique keyとして冪等化する。


TODO 3-7

permission_status != approved

の場合、Video Processing Queueへ送らない。


DONE CONDITION

Discovery Workerを繰り返し実行しても重複登録されない。

新しい対象動画だけを検出できる。


# =========================================================
# PHASE 4
# Video Source / Ingestion
# =========================================================

TODO 4-1

動画取得部分をVideoSourceAdapterとして抽象化する。


TODO 4-2

許諾済みソースだけを解析対象とする。


TODO 4-3

以下を記録する。

video_id
resolution
fps
duration
codec
ingested_at
processing_version


TODO 4-4

途中失敗時に処理状態を保存する。

全処理を最初からやり直さない。


DONE CONDITION

許諾済み動画1本を解析Pipelineへ投入できる。


# =========================================================
# PHASE 5
# Frame Extraction
# =========================================================

全動画フレームへOCRを実行してはいけない。


TODO 5-1

ffmpegを優先して使用する。


TODO 5-2

低頻度サンプリングを実装する。

初期候補:

1fps

設定変更可能にする。


TODO 5-3

画面状態を分類する。

UNKNOWN
BET_OPEN
HORSE_INFO_VISIBLE
ODDS_VISIBLE
PREDICTION_VISIBLE
RACE_RUNNING
RESULT_VISIBLE
NEXT_RACE


TODO 5-4

必要な画面区間だけを高密度再抽出する。


TODO 5-5

スマートフォン等による斜め撮影へ対応できるよう、

Game Screen Detection
Perspective Correction

を独立Componentとして設計する。


DONE CONDITION

動画1本からBET、HORSE INFO、RESULT候補フレームを自動抽出できる。


# =========================================================
# PHASE 6
# Vision Foundation
# =========================================================

実装優先順位:

horse_number
horse_name
win_odds
race_result
rank
condition
running_style
sex
speed
power
stamina
prediction_mark
predictor
predictor_comment
past_results


TODO 6-1

固定UI領域をROI Templateとして管理する。

座標を処理コードへ直接埋め込まない。


TODO 6-2

OCREngineAdapterを作成する。

複数の既存OCR Engineを比較可能にする。


TODO 6-3

同じ表示画面について複数フレームを解析する。


TODO 6-4

多数決、中央値、confidenceを使って最終値を決定する。


TODO 6-5

判断不能な値はNULLとする。

error_reasonを保存する。


DONE CONDITION

代表画像からhorse_name、win_odds、resultを構造化できる。


# =========================================================
# PHASE 7
# Odds Recognition
# =========================================================

重要仕様:

オッズは10未満と10以上で表示色が変わる。

OCRだけではなく表示色も利用する。


TODO 7-1

各Odds Cellを検出する。


TODO 7-2

HSVまたはLab Color Spaceで文字色を分類する。


TODO 7-3

以下を保存する。

odds_raw
odds_numeric
odds_color
odds_color_class
ocr_confidence
color_confidence
final_confidence


TODO 7-4

OCR数値と色カテゴリの整合性を確認する。


TODO 7-5

例:

OCR = 38

color = under_10

であれば3.8誤認識の可能性を再検証する。


TODO 7-6

自動補正した場合:

corrected = true

を保存する。


TODO 7-7

隣接フレームでも確定不能ならNULLとする。


DONE CONDITION

Golden Datasetに対するOdds Exact Matchを測定できる。


# =========================================================
# PHASE 8
# Horse Attribute Recognition
# =========================================================

各馬について以下の表示が存在する。

horse_name
rank
rank_star_count
sex
running_style
condition
speed
power
stamina


TODO 8-1

以下を取得する。

horse_name_raw
horse_name_normalized

rank_raw
rank_normalized

rank_star_count

sex

running_style_raw
running_style_normalized

condition_raw
condition_color
condition_icon


TODO 8-2

Speed / Power / StaminaはOCRではなくGauge Recognitionを使用する。


TODO 8-3

各Gaugeを0.0〜1.0のfill_ratioとして保存する。

speed_fill_ratio
power_fill_ratio
stamina_fill_ratio


TODO 8-4

複数フレームから中央値を採用する。


TODO 8-5

能力が何段階かを事前に仮定しない。

十分な観測数が集まった後、値分布をCluster Analysisして離散値か連続値か検証する。


DONE CONDITION

1頭についてrank、condition、speed、power、staminaを自動取得できる。


# =========================================================
# PHASE 9
# Race Builder
# =========================================================

TODO 9-1

複数のFrame Observationをrace_id単位へ統合する。


TODO 9-2

可能な限り以下を保存する。

race_id
video_id
timestamp

course
distance
direction
track_condition
weather

horses
odds
abilities
condition
past_results
prediction_marks

predictor
predictor_comment

first_place
second_place


TODO 9-3

Validationを実装する。

出走頭数
馬番重複
結果整合性
Odds Format
必須画面の存在
confidence


TODO 9-4

品質基準未達の場合:

ANALYSIS_EXCLUDED

とする。


TODO 9-5

除外データを削除しない。

retry_queueへ送る。


DONE CONDITION

動画内の1レースを構造化Recordとして保存できる。


# =========================================================
# PHASE 10
# Horse Master Resolver
# =========================================================

以下が同名馬について固定か検証する。

rank
rank_star_count
sex
running_style
speed
power
stamina

最初から固定値とは仮定しない。


TODO 10-1

全出現をhorse_observationsへ保存する。


TODO 10-2

同名馬の過去観測と比較する。


TODO 10-3

以下の状態を実装する。

UNVERIFIED
PROVISIONALLY_FIXED
FIXED
CONFLICT


初期ルール候補:

観測1〜2回:
UNVERIFIED

3回以上かつ2動画以上で一致:
PROVISIONALLY_FIXED

5回以上かつ3動画以上、
高confidence観測が一致:
FIXED

高confidence観測同士で不一致:
CONFLICT


TODO 10-4

Horse Masterに以下を保存する。

horse_id
canonical_name
rank
rank_star_count
sex
running_style
base_speed
base_power
base_stamina
fixed_status
observation_count
video_count
first_seen
last_seen
conflict_count
master_confidence


DONE CONDITION

同名馬の新観測によってHorse Masterが自動更新される。


# =========================================================
# PHASE 11
# Data Warehouse
# =========================================================

BigQueryをSystem of Recordとする。

Google Sheetsを本体DBにしない。


最低限以下を用意する。

videos
races
race_horses
race_bets
prediction_comments
horse_observations
horse_master
extraction_logs
model_predictions
model_results


TODO 11-1

created_at
updated_at

を保持する。


TODO 11-2

すべてのDerived Dataから元video_id / timestamp / frame_idへ追跡できるようにする。


TODO 11-3

以下を保存する。

detector_version
ocr_version
normalization_version
model_version


TODO 11-4

Raw ObservationとDerived Dataを分離する。


DONE CONDITION

分析結果から元動画・元フレームまでLineageを追跡できる。


# =========================================================
# PHASE 12
# Google Sheets Output
# =========================================================

TODO 12-1

BigQueryから分析Viewを作る。


TODO 12-2

以下をスマートフォンから閲覧しやすい形で出力する。

Recent Races
Horse Master
Extraction Errors
Horse Master Conflicts
Odds Performance
Condition Performance


TODO 12-3

Google Sheets出力失敗を本体Pipeline失敗扱いにしない。


DONE CONDITION

主要結果をスマートフォンから確認できる。


# =========================================================
# PHASE 13
# Golden Dataset / Evals
# =========================================================

Vision精度を感覚で評価しない。


TODO 13-1

evals/goldenへGolden Datasetを保存可能にする。


TODO 13-2

正解Schemaを作る。


測定項目:

horse_name_accuracy
rank_accuracy
condition_accuracy
odds_exact_match
odds_numeric_mae
speed_gauge_mae
power_gauge_mae
stamina_gauge_mae
result_accuracy


TODO 13-3

Visionコード変更後に同じGolden Datasetを自動評価する。


TODO 13-4

Before / AfterのMetricsを保存する。


TODO 13-5

Golden Datasetの正解値をモデル改善のために変更してはいけない。


DONE CONDITION

Vision変更がRegressionかImprovementか自動判定できる。


# =========================================================
# PHASE 14
# Aggregation
# =========================================================

最低限以下を集計する。

win odds bucket
quinella odds bucket
rank
condition
speed
power
stamina
running_style
distance
course
prediction_mark
predictor
predictor_comment


勝率だけでなく、

observed_probability × displayed_odds

を計算する。


DONE CONDITION

表示Odds以上の追加情報を持つ特徴量候補を探索できる。


# =========================================================
# PHASE 15
# Prediction Model
# =========================================================

モデルを段階的に比較する。


M0:
odds only

M1:
odds + past results

M2:
M1 + prediction marks

M3:
M2 + rank + abilities

M4:
M3 + condition

M5:
M4 + course / distance interactions

M6:
M5 + predictor / comments

M7:
M6 + Horse Master history

M8:
M7 + recent race state


TODO 15-1

Walk Forward Validationを使用する。

Random Splitだけで評価しない。


TODO 15-2

Metrics:

Log Loss
Brier Score
Calibration
Hit Rate
ROI
Max Drawdown
Max Losing Streak
BET Count
SKIP Rate


TODO 15-3

Value Betting判定を実装する。

odds = O
predicted probability = p

expected_return = p * O


TODO 15-4

Prediction Uncertaintyを考慮したConservative Expected Returnを計算する。


TODO 15-5

十分な期待値がない場合:

SKIP

とする。


DONE CONDITION

未来データでM0を上回ったModelのみ採用できる。


# =========================================================
# PHASE 16
# Continuous Operation
# =========================================================

TODO 16-1

Cloud SchedulerでDiscoveryを定期実行する。


TODO 16-2

新着video_idをQueueへ送る。


TODO 16-3

Cloud Run Jobsで解析する。


TODO 16-4

失敗処理をretry_queueへ送る。


TODO 16-5

Retry時も二重登録しない。


TODO 16-6

Cloud LoggingへStructured Logを出す。


TODO 16-7

監視対象:

Discovery failure
Video processing failure
OCR failure rate
ANALYSIS_EXCLUDED rate
Horse Master CONFLICT rate
BigQuery write failure
Processing cost


DONE CONDITION

新しい許諾済み動画について、

Discovery
→ Ingestion
→ Frame Extraction
→ Vision
→ Race Builder
→ BigQuery
→ Horse Master
→ Aggregation

まで人間による画像確認なしで処理される。


# =========================================================
# PHASE 17
# Operations Documentation
# =========================================================

以下をDocumentationする。

Architecture
Setup
GCP Resource
IAM
Secret
Deployment
Testing
Replay / Retry
Recovery
Data Retention
Cost Monitoring
Model Evaluation
Troubleshooting


# =========================================================
# 研究上の重要検証テーマ
# =========================================================

以下を最優先のResearch Questionsとして保持する。

同名馬のRankは固定か。

同名馬のSpeed、Power、Staminaは固定か。

同名馬のSex、Running Styleは固定か。

Conditionだけがレースごとに変化するのか。

ConditionにはOdds以上の追加情報があるか。

RankにはOdds以上の追加予測力があるか。

Speed、Power、Staminaは結果を説明するか。

AbilityとCourse / DistanceにInteractionが存在するか。

Prediction MarkにはOdds以上の情報があるか。

Predictor CommentにはOdds以上の情報があるか。

Horse Masterの過去実績は未来結果を説明できるか。

直近レース履歴から内部状態らしきものを推定できるか。


# =========================================================
# 禁止事項
# =========================================================

根拠のない値をDBへ保存しない。

OCR失敗を推測で確定しない。

別シリーズの仕様を混在させない。

SecretをGitへ保存しない。

Raw Dataを破壊的に上書きしない。

RankやAbilityが固定であると事前に仮定しない。

Conditionの序列を名称だけで確定しない。

予想屋に関するオカルトを事実扱いしない。

放出期・回収期を事実として扱わない。

短期的な的中率だけで攻略成功と判断しない。

Golden Datasetを結果改善目的で変更しない。

テスト失敗状態でPhase完了としない。


# =========================================================
# 最初の実行
# =========================================================

まずRepository全体を調査する。

次にPhase 0を実行する。

PLANS.mdへ全Phaseの現在状態を、

COMPLETED
IN_PROGRESS
BLOCKED
NOT_STARTED

で記録する。

次にPhase 1のRepository Bootstrapを進める。

GCP認証などユーザー操作が必要なものについてはBLOCKEDとして記録する。

BLOCKEDが存在しても、ユーザー操作なしで実装可能な作業は継続する。

一度にPhase 17まで実装してはいけない。

最初のタスクでは、

Phase 0
Phase 1
Phase 2の設計およびTerraform scaffold

までを対象とする。

コード変更後は利用可能なテストを実行する。

最後に以下だけを簡潔に報告する。

COMPLETED
BLOCKED
変更ファイル
テスト結果
次に実行すべきPhase
ユーザー操作が必要な項目
```
