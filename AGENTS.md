# リポジトリ ガイドライン

## プロジェクト構成とモジュール配置
- 本リポジトリは `nerfstudio-project/gsplat` の downstream fork であり、本家を継続的に取り込みながら、静的シーン向けCOLMAPマスク機能と再現可能なソースインストール手順を提供する。
- Python環境とパッケージ導入には `uv` を使う。ただし、upstreamの `pyproject.toml` はbuild-systemのみを定義し、依存関係の正本は `setup.py` と `examples/requirements.txt` である。空または不完全な `uv.lock` を再現性の根拠にしない。
- Pythonパッケージ本体は `gsplat/`、CUDA/C++実装は主に `gsplat/cuda/` と各コンポーネントの `kernels/cuda/`、実行例とdownstream固有のマスク統合は `examples/` 以下に配置する。
- テストは `tests/` に対象モジュールを反映したファイル名で追加する。テストの自動検出が働くようにすること。
- Sphinx文書は `docs/source/`、保守運用手順は `docs/operations.md`、設計判断は `docs/adr/`、補助スクリプトとCI設定は用途に応じて `lint/` と `.github/workflows/` に配置する。
- dataset、checkpoint、PLY、レンダリング結果、ローカルCUDA設定をGitへcommitしない。

## 仕様書駆動開発 (Spec-driven Development) とドキュメント管理ルール

本プロジェクトでは、要件・設計・タスクを明確に分離し、ドキュメントが常に「システムの最新の正しい状態 (Single Source of Truth)」を表すように管理する。
過去の変更履歴を追記していく「ログ型」の運用は厳禁とする。

### 1. ドキュメントの役割と記述レベルの厳格な分離

#### `requirements.md` — 要件定義書 (What / Why)
- **役割**: システムが「何を」実現しなければならないか、「なぜ」その機能が必要なのかを定義する。
- **記述レベル**: 自然言語中心。
- **制約**: 技術スタック、ライブラリ名、クラス名、API の詳細などの「実装方法 (How)」は記述しない。
- **最小テンプレート**: 各要件は `What` / `Why` / `Fit Criteria` を基本単位とする。
- **Fit Criteria の制約**: 外部から観測可能な合否判定条件のみを記述する。
- **ID体系**: `REQ-<コンポーネント名>-<連番>`（例: `REQ-MASK-01`, `REQ-INSTALL-02`）の形式で固定 ID を付与する。

#### `design.md` — 設計書 (How)
- **役割**: `requirements.md` で定義された要件を「どのように」実現するか、技術的な解決策を定義する。
- **記述レベル**: アーキテクチャ、技術スタック、データモデル、主要コンポーネントのインターフェース設計など、実装時に迷わない具体設計を記述する。
- **最小テンプレート**: 各 `DES-*` に `Refs: REQ-*` / `責務` / `入力` / `出力` / `失敗時` / `不変条件` を明記する。
- **制約**: 提供価値、スコープ定義、将来構想、比較検討の経緯、採用理由、移行手順、運用手順、CLI 利用例は記述しない。
- **ID体系**: `DES-<コンポーネント名>-<連番>`（例: `DES-MASK-01`, `DES-SYNC-02`）の形式で固定 ID を付与し、必ず対応する `REQ-*` を `Refs:` として明記する。

#### `tasks.md` — タスク管理表 (Who / When / Action)
- **役割**: 設計を具体的な作業単位へ分解し、進捗を管理する。
- **記述レベル**: 開発者が「今日何をするか」が分かる粒度。
- **ID体系**: `S*` / `A*` / `B*` / `C*` のような優先度に基づく形式とし、該当する `REQ-*` / `DES-*` を `Refs:` として明記する。
- **運用**: `tasks.md` は未完了のみ、`archive_tasks.md` は完了のみを保持する。
- **採番運用**: `tasks.md` は優先度ごとの「次回採番メモ」を保持する。タスク ID の再利用は禁止し、欠番は許容する。

### 2. ドキュメントの更新ルール（上書き更新の原則）

- **追記の禁止**: 仕様変更時に新しい ID を発行して古い仕様を打ち消すような追記型更新を行わない。
- **直接上書き**: 既存機能に変更が入る場合は、該当する固定 ID の記述内容を最新の正しい状態へ書き換える。
- **廃止の扱い**: 機能自体が完全に廃止された場合は、その ID ごと「廃止済み機能」セクションへ移動する。
- **表現の統一**: 「〜することにした」「〜を追加する」といった過去の変更や動的なアクションを表す表現は避け、文体を静的・現在形（「〜である」「〜の責務を持つ」「〜を担う」）に統一すること。
- **記法の統一**: 見出し階層、章番号、箇条書きインデント、ラベル表記のルールを固定し、重複・逆転・表記ゆれを作らないこと。

#### 変更時チェックリスト
- 変更内容の帰属先（`requirements.md` / `design.md` / `tasks.md`）を先に判定する。
- 文の置き場を次の5択で判定する。
    - 外から観測できる振る舞い: `requirements.md`
    - 名前、型、境界、既定値、列挙語彙: `design.md`
    - なぜその案か、何を捨てたか: `docs/adr/`
    - どう運用するか: `docs/operations.md`
    - 今回やる差分作業: `tasks.md`
- 既存IDの上書きで更新し、不要な新規ID増殖を避ける。
- 更新後に以下を確認する。
    - 見出し階層・章番号の整合
    - 表記ゆれ（ラベル、インデント、用語）の有無
    - `Refs:` の参照先IDの実在
    - `tasks.md` と `archive_tasks.md` の未完了/完了の分離
    - `tasks.md` の「次回採番メモ」が最新状態であること

### 3. 議論と実装のフロー

- 将来の実装に向けたすり合わせやアイデアの議論などは、まず優先度 `C*` の議論タスクとして起票し、背景・論点・合意事項・受け入れ条件・テスト観点・移行方針などを記録すること。
- `C*` 議論タスクの完了後、その合意内容に基づいて `requirements.md` と `design.md` を最新状態に更新（上書き）してから、適切な実装タスク（`S*` / `A*` / `B*`）へ昇格し、実装に着手すること。昇格・ドキュメント更新前に実装を開始しないこと。

#### フロー運用上の禁止事項
- 本文への時系列追記によるログ化を禁止する。
- 完了タスクを `tasks.md` に残し続けることを禁止する。
- 方針未確定のまま実装へ先行着手し、後追いで仕様を合わせる運用を禁止する。

### 4. 補助ドキュメントの役割

- `docs/adr/` は設計判断の理由、不採用案、比較結果、トレードオフを記録する。
- `docs/operations.md` はfork運用、本家同期、検証済み版の固定など、開発者・運用者向けの運用手順書とする。
- `docs/` 配下にはインストール、COLMAPマスク利用法などのユーザー向け利用ガイドを配置する。

## ビルド、テスト、開発用コマンド
- `uv venv --python 3.11 .venv` — リポジトリ専用の仮想環境を作成する。
- `uv pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu128` — 現在のexamplesと整合するPyTorchを先に導入する。利用環境のCUDA系列が異なる場合は `install-manual.md` と実環境の整合を確認する。
- `uv pip install setuptools wheel ninja numpy rich` — freshなuv環境で `--no-build-isolation` を使う前に、`pyproject.toml` のbuild-system依存を同じ `.venv` へ導入する。
- `uv pip install --no-build-isolation -e .` と `uv pip install -r examples/requirements.txt --no-build-isolation` — 本体とexample依存を同じ `.venv` に導入する。
- `.venv/bin/python -m pytest -q tests/test_colmap_masks.py tests/test_losses.py` — downstreamマスク機能と関連するupstream lossを検証する。
- `.venv/bin/python -m pytest tests/` — 実行環境で利用可能なテストスイートを実行する。CUDA必須テストは対応GPU環境で確認する。
- `lint/format-code.sh` — PythonをBlack、C/C++/CUDAをリポジトリ指定版clang-formatで整形する。確認のみの場合は `lint/format-code.sh --check` を使う。
- `make -C docs html SPHINXOPTS="-W --keep-going"` — 警告をエラーとしてSphinx文書をビルドする。
- 依存関係を変更した場合は `setup.py`、`examples/requirements.txt`、導入文書、CIの依存セットを相互に確認する。`uv.lock` は直接編集せず、本リポジトリの依存関係の正本としてcommitしない。

## 設計方針
- 良い設計とは、現在の要件を満たし、入口から中核処理までを少ないジャンプで追える設計である。
- KISS 原則を優先する。将来の拡張可能性だけを理由に、レイヤ、型、設定、ファイルを増やさない。
- API、UI、コアロジック、外部依存、永続化の境界は明確に保つ。ただし、責務分離を機械的な多層化とみなさない。
- 抽象化は、現在存在する重複、複数実装、外部依存の差し替え、リソース管理、または明確な複雑性を解消する場合に導入する。
- 単一実装だけの interface、処理を委譲するだけの service、将来用の factory、責務が曖昧な Manager、薄い中間層は原則として作らない。
- 関数で十分な処理は関数として実装する。既存の処理フローを理由なく多数の小ファイルへ分断しない。
- 入力検証、例外処理、ログ、設定管理、テストなど、現在必要な堅牢性は省略しない。
- downstream固有実装は可能な限り `examples/`、`tests/`、`docs/`、downstream CIに閉じ、本家の `gsplat/` コア変更を最小化する。ただし、責務上コアに置くべき機能を不自然な外部モジュールへ迂回させない。
- マスクは内部で `True = keep` のvalid maskへ正規化し、画像変換後も画像・マスクの座標対応を維持する。COLMAP初期点、学習loss、評価指標の対象領域が同じ規約に従うことを不変条件とする。

### 構造変更時の確認
次の変更は、実装前に方針と必要理由を示してユーザー確認を得る。
- 新しい主要ディレクトリまたはレイヤの追加。
- 抽象基底クラス、Protocol、interface、factory、adapter の追加。
- 中核処理の大規模なファイル分割。
- 公開 API、データセット形式、mask規約、設定形式の変更。
- downstream固有変更を `gsplat/` コアまたはupstream由来のCUDA実装へ加える変更。

## コーディングスタイル
- Pythonフォーマッターはリポジトリ固定のBlack 22.3.0、C/C++/CUDAフォーマッターは `config.yaml` 指定版clang-formatを使い、`lint/format-code.sh` 経由で実行する。
- モジュール名は snake_case、クラス名は PascalCase、関数名は snake_case、定数は UPPER_SNAKE_CASE を使う。
- 型は既存のupstreamコードと整合する標準Python型、`typing`、`typing_extensions`、PyTorch Tensor型を優先する。設定表現は既存の `tyro` とdataclassベースの構造に合わせ、新しいデータモデル基盤を持ち込まない。
- 型ヒントは対象ファイルのupstream互換性を優先する。新規の独立モジュールではPython 3.10以降の組み込みジェネリック表記（例: `list[str]`, `tuple[int, int]`）や `collections.abc` の抽象基底クラスを使用する。
- 公開関数と判断の難しい処理には、既存モジュールの文体に合わせた英語docstringを記述する。ユーザー向け説明は日本語のプロジェクト文書またはupstream Sphinx文書の文脈に合わせる。

## テスト方針
- テストは `pytest` を利用し、テストコードも実行方法もpytestに準拠させる。
- マスク機能の変更では、mask探索とmissing policy、閾値とmode、最近傍リサイズと座標サンプリング、COLMAP SfM初期点の除外、masked lossと評価指標を回帰テストする。
- downstream CIはCPUで実行可能なマスク・lossテストとSphinxビルドを必須とする。CUDAカーネル、学習全体、実データ品質に関わる変更は、対応GPU環境でも検証し、Python、PyTorch、CUDA、driver、pycolmap、対象commit SHAを記録する。
- カバレッジは `tasks.md` で追跡し、downstream固有の分岐は90%以上を目標とする。カバレッジが下がったら早期失敗させる仕組みを作ること。
- 遅い、GPU必須、または任意のワークロードは既存のpytest markerを利用し、通常のCPU CIから明示的に分離する。

## バージョン管理
- `upstream` は `https://github.com/nerfstudio-project/gsplat.git`、`origin` は `git@github.com:uohige/gsplat.git` とする。
- `main` は `upstream/main` のfast-forward可能なミラーとし、自前commitを置かない。`custom/main` はdownstream機能を含む保護対象の利用ブランチとする。
- 公開済みの `custom/main` はrebaseせず、本家更新は `chore/sync-upstream-YYYY-MM` で `upstream/main` をmergeし、`custom/main` 宛てPull Requestとして統合する。通常の機能・文書変更は単一目的のPull Requestをsquash mergeし、本家同期はupstreamとの祖先関係を保持するmerge commitで統合する。
- 本家ミラー更新では `git merge --ff-only upstream/main` を使う。`--ff-only` が失敗した場合は通常mergeで回避せず、`main` への自前commit混入を調査する。
- downstreamの動作確認版は `mask-vMAJOR.MINOR.PATCH` 形式のannotated tagで管理し、対応upstream SHAと検証環境をGitHub Releaseへ記録する。
- `custom/main` への直接push、force-push、削除を行わない。

## コミットとプルリクエストのガイドライン
- 単一のタスクごとに適切な粒度でブランチを切る。
- ブランチ名は `feature/` / `fix/` / `docs/` / `chore/` などのプレフィックスで始め、変更内容を簡潔に表す名前にする。
- `tasks.md` 内のタスクを実装する場合は、タスク ID を含めて `feature/S123-short-description` のように命名する。
- タスクが更新・変更・完了した際には、関連するドキュメント（`README.md`, `requirements.md`, `design.md`, `tasks.md` など）も必要に応じて適切に更新する。
- コミットメッセージは必ず `add: ...` / `update: ...` / `fix: ...` / `delete: ...` のいずれかのプレフィックスで始め、その後に簡潔な説明を付ける。
- Pull Requestは単一の目的に絞り、base repositoryが `uohige/gsplat`、base branchが `custom/main` であることを確認する。本家へ提案する明示的な目的がない限り、`nerfstudio-project/gsplat` をbase repositoryに選ばない。
- Pull Requestでは必須CIを通し、maskやGPU挙動に影響する場合は追加の検証条件と結果を本文へ記録する。
