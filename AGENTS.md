# 作業規則
変更前に GOALS.md、PLANS.md、docs/SPEC.md、docs/DATA_DICTIONARY.md、docs/ARCHITECTURE.md を読む。
- 推測値を確定データとして保存しない。認識値には confidence と根拠フレームを保存する。
- 生データを破壊的に更新しない。permission_status=approved の公開映像のみ解析する。
- 別シリーズの情報を混在させない。本番書込は冪等にする。
- Secret、APIキー、サービスアカウント秘密鍵を Git に保存しない。
- 変更後は必ずテストする。テスト失敗状態で Phase を完了しない。
- Golden Dataset の正解をモデル改善目的で変更しない。
- Rank/Ability の固定性、Condition の序列を事前に仮定しない。
- 各 Phase は調査→設計→実装→テスト→Done 確認→コミット可能な状態の順。
- PLANS.md が進捗の Source of Truth。状態は NOT_STARTED / IN_PROGRESS / COMPLETED / BLOCKED。
- 課金・認証・本番適用・削除・大幅な IAM 変更を自動実行しない。
- 初回スコープは Phase 0、1、2 の設計と Terraform scaffold。後続を先取りしない。
