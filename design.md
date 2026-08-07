# 設計 (Design)

本書は、`requirements.md` で定義された要件を実現するための技術的な解決策を定義する。
各 `DES-*` は `Refs:` / `責務` / `入力` / `出力` / `失敗時` / `不変条件` で記述する。

## 技術基盤

- 言語: Python 3.11、C++、CUDA
- パッケージ管理: `uv` による仮想環境・pip互換導入、setuptoolsによるpackage build
- 数値計算・学習: PyTorch、NumPy
- データ読込: pycolmap、imageio、OpenCV、Pillow
- CLI: tyro
- テスト: pytest、GitHub Actions
- 文書: Sphinx
- 実行環境: Linux、NVIDIA GPUと互換CUDA toolkitを備えたローカル環境、CPUベースのGitHub Actions

## 1. マスク入力 (Mask Input)

### DES-MASK-01: 画像マスクプロバイダー
- **Refs**: REQ-MASK-03, REQ-NFR-01
- **責務**:
  - `examples/datasets/masks.py` が、COLMAP画像と外部マスクの対応付け、遅延読込、二値化、意味の正規化を担う。
  - `ImageMaskProvider` はすべての入力を内部規約 `True = keep` の2次元boolean配列へ変換する。
- **入力**:
  - データルート、画像の相対パス、mask directory、`exclude | valid` のmode、整数threshold、`error | warn | valid` のmissing policy。
  - PNGなどimageioが読込可能な2次元または複数channel画像。
- **出力**:
  - 画像indexに対応する `numpy.ndarray` のvalid mask、またはマスク機能無効時・許可された欠損時の `None`。
- **失敗時**:
  - 明示directoryが存在しない場合、auto探索で候補がない場合、不正なmask次元、既定policyでのmask不足は `ValueError` とする。
  - `warn` policyは警告を発行し、欠損画像を全域validとして扱う。
- **不変条件**:
  - mask pathは画像の相対path stemを優先して一意に対応付ける。
  - multi-channel maskは先頭3channelの最大値から前景を判定する。
  - modeに関係なく、コンポーネント外へ返す値は `True = keep` である。

### DES-MASK-02: マスク座標変換
- **Refs**: REQ-MASK-03, REQ-NFR-01
- **責務**:
  - valid maskを学習画像の高さと幅へ変換し、元画像座標のCOLMAP観測点をmask座標へ対応付ける。
- **入力**:
  - boolean mask、変換先の画像shape、元画像のwidthとheight、2次元観測座標。
- **出力**:
  - 変換先shapeのboolean mask、または観測座標に対応するkeep判定。
- **失敗時**:
  - 元画像の範囲外にある観測座標はinvalidとして扱う。
- **不変条件**:
  - mask resizeは最近傍補間を使用し、新しい中間ラベルを生成しない。
  - imageのundistortion、crop、resizeと同じ順序・範囲の変換をmaskへ適用する。

## 2. COLMAPデータ統合 (COLMAP Integration)

### DES-COLMAP-01: COLMAP Parserでの初期点選別
- **Refs**: REQ-MASK-02, REQ-MASK-03, REQ-NFR-01
- **責務**:
  - `examples/datasets/colmap.py` の `Parser` が、各3D pointに紐づく2D observationをvalid maskへ投影し、初期点群への採否を決定する。
- **入力**:
  - pycolmap reconstructionのpoint track、画像・camera情報、画像ごとのvalid mask、最小valid observation数、filter有効flag。
- **出力**:
  - 採用されたpointの座標、色、reprojection error、および元point IDとの対応。
- **失敗時**:
  - mask filteringによって全COLMAP pointが除去された場合は `ValueError` とする。
- **不変条件**:
  - maskが存在しない画像のobservationは、missing policyで許可された場合にvalidとして数える。
  - maskによる選別を無効化した場合は、maskを理由にpointを除外しない。
  - point track内でmaskが適用されたobservationが存在しないpointは従来どおり保持する。

### DES-COLMAP-02: Dataset sampleへのmask付与
- **Refs**: REQ-MASK-01, REQ-MASK-03, REQ-MASK-04
- **責務**:
  - `examples/datasets/colmap.py` の `Dataset` が、画像と同じ幾何変換を適用したvalid maskを学習sampleへ付与する。
- **入力**:
  - Parserが解決した外部mask、既存ROI mask、画像のundistortion・crop・patch設定。
- **出力**:
  - `bool` Tensorの `mask` を任意に含むdataset sample。
- **失敗時**:
  - mask未使用時は `mask` keyを生成せず、既存のmaskなし経路を維持する。
- **不変条件**:
  - 外部maskと既存ROI maskが両方存在する場合は論理積を採用する。
  - sample内のimage、camera intrinsics、maskは同一の画素座標系を共有する。

## 3. 学習と評価 (Training and Evaluation)

### DES-TRAIN-01: Masked photometric objective
- **Refs**: REQ-MASK-01, REQ-MASK-04
- **責務**:
  - `examples/simple_trainer.py` がdataset sampleのmask有無を判定し、mask対応のL1とSSIMを画像再構成lossへ使用する。
  - maskなしsampleはupstreamの通常loss経路を使用する。
- **入力**:
  - render結果、ground-truth pixels、任意のboolean valid mask、SSIM混合係数。
- **出力**:
  - valid pixelだけから算出したscalar photometric loss。
- **失敗時**:
  - loss関数の入力shape契約に反するmaskは、呼び出し元へ例外を伝播する。
- **不変条件**:
  - invalid pixelはL1とSSIMの集約へ寄与しない。
  - mask対応loss以外のoptimizer、strategy、rasterizerの契約を変更しない。

### DES-EVAL-01: Masked evaluation
- **Refs**: REQ-MASK-04
- **責務**:
  - `examples/mask_utils.py` とvalidation経路が、valid pixelだけのPSNRと可視化用masked imageを生成する。
- **入力**:
  - render結果、ground-truth pixels、boolean valid mask。
- **出力**:
  - valid pixelに限定したPSNRと、invalid pixelを0にした派生画像。
- **失敗時**:
  - validation setの全画像でvalid pixelが存在しない場合は `RuntimeError` とする。
- **不変条件**:
  - metric算出に用いるrender結果とground truthは同じmaskを共有する。
  - 評価用のmasked image生成は元Tensorを正本として変更しない。

## 4. ソースインストール (Source Installation)

### DES-INSTALL-01: `uv` ベースの導入境界
- **Refs**: REQ-INSTALL-01
- **責務**:
  - `install-manual.md` が、専用 `.venv`、project単位のCUDA設定、PyTorch先行導入、editable source install、examples依存導入、import確認を一つの導入経路として定義する。
- **入力**:
  - Python 3.11、NVIDIA driver、CUDA toolkit、PyTorch wheel index、repository commit SHA。
- **出力**:
  - repository直下の `.venv` に隔離されたgsplat本体とexamples実行環境。
- **失敗時**:
  - GPU driver、CUDA compiler、PyTorch CUDA系列、pycolmap APIの確認点を分離し、どの境界が不整合かを利用者が判別できる手順とする。
- **不変条件**:
  - PyTorchをsource buildより先に導入する。
  - build isolationを無効にした導入では、現在の `.venv` のPyTorchをbuildに使用する。
  - 再現性の識別子はcommit SHA、依存定義、PyTorch wheel index、CUDA環境であり、空の `uv.lock` ではない。

## 5. Fork運用と継続検証 (Fork Maintenance)

### DES-SYNC-01: Remoteとbranchの分離
- **Refs**: REQ-SYNC-01, REQ-NFR-01
- **責務**:
  - Git remoteとbranchが、本家の正本、本家mirror、downstream利用版、機能開発、本家同期候補を分離する。
- **入力**:
  - `upstream/main` の新しいcommit、`custom/main` のdownstream commit、作業branch上の変更。
- **出力**:
  - `origin/main` のfast-forward mirror、保護された `origin/custom/main`、単一目的のPull Request。
- **失敗時**:
  - `main` がfast-forwardできない場合は自前commit混入として同期を停止する。
  - 必須CIが失敗するPull Requestは `custom/main` へ統合しない。
- **不変条件**:
  - `main` にdownstream固有commitを置かない。
  - 公開済み `custom/main` をrebaseまたはforce-pushしない。
  - 通常変更はsquash、本家同期はupstreamとの祖先関係を保持するmerge commitで統合する。

### DES-CI-01: Downstream必須check
- **Refs**: REQ-SYNC-01, REQ-NFR-02
- **責務**:
  - `.github/workflows/downstream_checks.yml` が、`custom/main` 向け変更のmask・loss回帰とSphinx文書をCPU runnerで検証する。
- **入力**:
  - `custom/main` へのPull Request、branch上のPython・文書・依存定義。
- **出力**:
  - `Mask and loss tests` と `Documentation` の独立したcheck結果。
- **失敗時**:
  - 依存導入、pytest、Sphinxのいずれかが失敗したjobを成功として扱わない。
- **不変条件**:
  - 2つのcheckはbranch protectionの必須contextと名前が一致する。
  - CUDAの不在を理由にdownstreamのCPU回帰と文書検証を省略しない。

### DES-REL-01: 検証済み版の識別
- **Refs**: REQ-SYNC-01, REQ-NFR-02
- **責務**:
  - annotated tagとGitHub Releaseが、downstream利用版と対応upstream・GPU検証環境の組を識別する。
- **入力**:
  - `custom/main` の検証対象commit、upstream commit SHA、Python・PyTorch・CUDA・driver・pycolmap、mask設定、検証結果。
- **出力**:
  - `mask-vMAJOR.MINOR.PATCH` tagと環境情報を含むrelease metadata。
- **失敗時**:
  - 必須情報または実データ検証が不足する状態を、検証済みreleaseとして扱わない。
- **不変条件**:
  - tagは書き換えず、異なる検証内容には新しいversionを割り当てる。
  - 大容量のdata、checkpoint、PLY、render結果をGit objectへ含めない。

## 6. エラーハンドリングとリソース管理

### DES-ERR-01: 明示的な失敗
- **Refs**: REQ-MASK-02, REQ-MASK-03, REQ-MASK-04, REQ-INSTALL-01, REQ-NFR-01
- **責務**:
  - 利用者入力、外部依存、mask整合性、空の有効領域を区別し、呼び出し側が対処できる情報を伝播する。
- **入力**:
  - mask pathとshapeの検証結果、COLMAP point選別結果、validation集約結果、導入時の環境確認結果。
- **出力**:
  - 原因を識別可能な例外、警告、または診断手順。
- **失敗時**:
  - 原因を握りつぶさず、部分的なmask適用を完全な成功として扱わない。
- **不変条件**:
  - 安全側の既定ではmask不足と全点・全画素除外を明示的な失敗とする。
  - 緩和動作は利用者が明示的に選択した場合だけ有効になる。
