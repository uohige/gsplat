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
- A5 -> B2

## 優先度S: クリティカルなバグ修正や機能追加

## 優先度A: アーキテクチャ刷新や重要な機能改善

- [ ] **A5. 実データGPU環境でmask学習を検証**
  - Refs: REQ-MASK-01, REQ-MASK-02, REQ-MASK-04, REQ-NFR-02, DES-REL-01
  - [ ] RTX 4070参照環境をクリーンな `.venv` に構築し、OS、GPU区分、VRAM、driver、CUDA、Python、PyTorch、torchvision、pycolmapの完全なversionを記録する
  - [ ] 40〜60枚を目安に、動的対象を3か所以上へ移動して各位置を5視点以上から撮影したCOLMAP datasetと全画像分のexclude maskを用意し、dataset manifest hashを記録する
  - [ ] 同一dataset、split、seed、30,000 steps、`data_factor=4`、default strategyの条件でmaskなし・maskありを学習する
  - [ ] mask filtering後にも初期点が残り、100点以上または元点群の1%以上が除外されることを確認する
  - [ ] 両checkpointを同一valid領域で評価し、maskありPSNRの低下がmaskなし比0.5 dB以内であることを確認する
  - [ ] 事前選定した3 view以上を比較し、1 view以上でghostが低減し、静的背景に新しい大規模な欠損、ぼけ、境界破綻がないことを確認する
  - [ ] SSIM、LPIPS、最終Gaussian数、所要時間、最大GPU memoryを参考値として記録する
  - [ ] downstream SHA、upstream SHA、環境、dataset識別情報、mask設定、定量結果、目視結果をrelease候補へ記録する

## 優先度B: パフォーマンス・品質・拡張性の強化

- [ ] **B2. Downstream固有分岐のcoverageを計測**
  - Refs: REQ-NFR-01, REQ-NFR-02, DES-CI-01
  - [ ] mask provider、COLMAP filtering、masked training・evaluationのcoverage対象を定義する
  - [ ] CPUで再現可能なcoverage計測commandを整備する
  - [ ] downstream固有分岐90%以上を満たさない場合にCIで検知する

## 優先度C: 議論・設計タスク
