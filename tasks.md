# タスク一覧 (Tasks)

本ドキュメントは、現在の未完了タスクのみを管理する。
完了タスクは `archive_tasks.md` を参照すること。

## 運用ルール
- 新規提案・論点整理は、まず優先度 `C*` の議論タスクとして起票すること。
- `C*` 議論タスクで受け入れ条件が合意されるまで、実装タスク (`S*` / `A*` / `B*`) に着手しないこと。
- 完了したタスクは本書から削除し、`archive_tasks.md` へ移動すること。
- 新規タスク起票時は「次回採番メモ」の値で採番し、起票と同時に当該優先度の値を `+1` 更新すること。
- タスク ID の再利用は禁止し、欠番は許容すること。
- すべてのタスクに `Refs:` を付け、`REQ-*` または `DES-*` と紐付けること。

## 次回採番メモ
- `S`: 1
- `A`: 6
- `B`: 3
- `C`: 3

## 推奨実装順序
- A4 -> C2 -> A5 -> B2

## 優先度S: クリティカルなバグ修正や機能追加

## 優先度A: アーキテクチャ刷新や重要な機能改善

- [ ] **A4. 保守運用文書を正本へ統合**
  - Refs: REQ-INSTALL-01, REQ-SYNC-01, DES-INSTALL-01, DES-SYNC-01
  - [ ] `docs/operations.md` にfork運用、本家同期、release固定、障害時確認を統合する
  - [ ] `docs/UPSTREAM_SYNC.md` との重複を解消し、参照元を正本へ向ける
  - [ ] `install-manual.md` のfork URL placeholderを実際のrepositoryと `custom/main` 利用方法へ置換する
  - [ ] 文書内の導入・同期commandが現在のremoteとbranch protectionに一致することを確認する

- [ ] **A5. 実データGPU環境でmask学習を検証**
  - Refs: REQ-MASK-01, REQ-MASK-02, REQ-MASK-04, REQ-NFR-02, DES-REL-01
  - [ ] C2で合意した環境と静的シーンdatasetを用意する
  - [ ] maskなし・maskありで初期点数、loss、評価指標、出力sceneを比較する
  - [ ] 動的領域に由来するGaussianの抑制を定性的・定量的に確認する
  - [ ] commit SHA、upstream SHA、依存環境、mask設定、検証結果をrelease候補へ記録する

## 優先度B: パフォーマンス・品質・拡張性の強化

- [ ] **B2. Downstream固有分岐のcoverageを計測**
  - Refs: REQ-NFR-01, REQ-NFR-02, DES-CI-01
  - [ ] mask provider、COLMAP filtering、masked training・evaluationのcoverage対象を定義する
  - [ ] CPUで再現可能なcoverage計測commandを整備する
  - [ ] downstream固有分岐90%以上を満たさない場合にCIで検知する

## 優先度C: 議論・設計タスク

- [ ] **C2. 検証済みreleaseの対応環境と判定基準を合意**
  - Refs: REQ-INSTALL-01, REQ-SYNC-01, REQ-NFR-02, DES-REL-01
  - [ ] 対応対象とするOS、GPU、driver、CUDA、Python、PyTorch、pycolmapの組み合わせを定義する
  - [ ] maskの効果を合格とする定量指標と目視確認項目を定義する
  - [ ] `mask-vMAJOR.MINOR.PATCH` のversion更新基準を定義する
  - [ ] A5へ昇格可能な受け入れ条件を確定する
