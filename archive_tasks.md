# タスクアーカイブ (Archive Tasks)

本ドキュメントは、完了済みタスクのみを保持する。
現在の未完了タスクは `tasks.md` を参照すること。

## 運用ルール
- 完了したタスクは `tasks.md` から削除し、本書へ移動する。
- 本書へ移動したタスクは完了時点の `Refs:`、チェック項目、補足を保持する。
- 未完了タスクを本書へ置かない。
- タスク ID の再利用は禁止し、欠番は許容する。

## 優先度S: 完了済みのクリティカルなバグ修正や機能追加

## 優先度A: 完了済みのアーキテクチャ刷新や重要な機能改善

- [x] **A1. COLMAP静的シーンmaskを学習経路へ統合**
  - Refs: REQ-MASK-01, REQ-MASK-02, REQ-MASK-03, REQ-MASK-04, DES-MASK-01, DES-COLMAP-01, DES-COLMAP-02, DES-TRAIN-01, DES-EVAL-01
  - [x] 画像単位maskの探索、二値化、mode、missing policyを実装する
  - [x] maskに基づくCOLMAP初期点の選別を実装する
  - [x] mask対応L1、SSIM、PSNRとvalidation可視化を学習例へ統合する
  - [x] maskなしの標準経路を維持する

- [x] **A2. `uv` ベースのソースインストール手順を整備**
  - Refs: REQ-INSTALL-01, DES-INSTALL-01
  - [x] 専用 `.venv` とproject単位のCUDA設定を説明する
  - [x] PyTorch先行導入とbuild isolationを無効にしたeditable installを説明する
  - [x] examples依存とpycolmap APIの確認方法を説明する
  - [x] commit SHAと実行環境による再現条件を説明する

- [x] **A3. Forkと本家追従branchを分離**
  - Refs: REQ-SYNC-01, REQ-NFR-01, DES-SYNC-01
  - [x] `origin` を `uohige/gsplat`、`upstream` を本家repositoryへ設定する
  - [x] `main` を本家mirror、`custom/main` をdownstream利用版として分離する
  - [x] `custom/main` をdefault branchとして保護する
  - [x] 本家同期と通常機能開発のPull Request経路を定義する

- [x] **A4. 保守運用文書を正本へ統合**
  - Refs: REQ-INSTALL-01, REQ-SYNC-01, DES-INSTALL-01, DES-SYNC-01
  - [x] `docs/operations.md` にfork運用、本家同期、release固定、障害時確認を統合する
  - [x] `docs/UPSTREAM_SYNC.md` との重複を解消し、参照元を正本へ向ける
  - [x] `install-manual.md` のfork URL placeholderを実際のrepositoryと `custom/main` 利用方法へ置換する
  - [x] 文書内の導入・同期commandが現在のremoteとbranch protectionに一致することを確認する

## 優先度B: 完了済みのパフォーマンス・品質・拡張性の強化

- [x] **B1. Downstream必須CIを構成**
  - Refs: REQ-SYNC-01, REQ-NFR-02, DES-CI-01
  - [x] mask・loss回帰をCPU runnerで実行する
  - [x] Sphinx文書をwarning errorとしてbuildする
  - [x] 2つのjobを `custom/main` の必須checkとして設定する

## 優先度C: 完了済みの議論・設計タスク

- [x] **C1. Downstream forkの目的と追従方針を整理**
  - Refs: REQ-MASK-01, REQ-INSTALL-01, REQ-SYNC-01, DES-SYNC-01
  - [x] mask機能と導入How-Toをrepositoryの提供範囲として定義する
  - [x] 本家codeへの変更を抑え、example境界で統合する方針を定義する
  - [x] fork内の本家mirrorとdownstream利用版を分離する方針を定義する

- [x] **C2. 検証済みreleaseの対応環境と判定基準を合意**
  - Refs: REQ-INSTALL-01, REQ-SYNC-01, REQ-NFR-02, DES-REL-01
  - [x] Ubuntu 24.04 LTS、RTX 4070、CUDA 12.8、Python 3.11、PyTorch 2.9.1+cu128を初回参照環境として定義する
  - [x] 初期SfM点の除外、同一valid領域のPSNR、事前選定viewのghost低減と静的背景の健全性を合格条件として定義する
  - [x] `mask-vMAJOR.MINOR.PATCH` のversion更新基準を定義する
  - [x] 小規模な自前COLMAP captureの準備を含むA5の受け入れ条件を確定する
