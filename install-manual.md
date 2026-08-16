# gsplat source installation with uv

この手順は、`gsplat` のソースツリーを clone し、`examples/` と本リポジトリ固有のマスク機能を含む状態で、`uv` の仮想環境内だけでできるだけ完結して使うためのものです。

目的は次の 3 点です。

- `examples/` 配下のスクリプトやディレクトリをそのまま使えるようにする
- Python パッケージはリポジトリ直下の `.venv` に閉じ込める
- 既存の別プロジェクトやグローバル Python 環境をなるべく汚さない

## 1. 先に理解しておくべきこと

`pip install git+https://github.com/nerfstudio-project/gsplat.git` は、`gsplat` パッケージ本体をインストールする方法です。`examples/` を作業ディレクトリとして手元に保持したい場合には向きません。

`examples/` を活用したいなら、`git clone --recursive` でリポジトリ全体を持ってきて、その clone 済みディレクトリの中に `uv` の仮想環境を作るのが自然です。

また、このリポジトリは source install になります。Python の依存は `.venv` に閉じ込められますが、CUDA driver やコンパイラなどのビルド要件までは完全には仮想環境だけで完結しません。ここは Python 環境とシステム要件を分けて考えてください。

## 2. 推奨方針

- Python は `3.11` を使う
- 既存プロジェクトとは別ディレクトリで作業する
- PyTorch を先に入れる
- その後、clone した `gsplat` を同じ `.venv` に source install する
- `examples/requirements.txt` も同じ `.venv` に入れる
- 再現性が必要なら `custom/main` のcommit SHAまたは検証済みの
  `mask-vMAJOR.MINOR.PATCH` tagを固定する

Python `3.11` を勧める理由は、PyTorch と CUDA 拡張の組み合わせで比較的無難だからです。これは厳密な公式固定値ではなく、実務上の保守的な推奨です。

## 3. 作業ディレクトリ

以下では、保存先を `~/projects/gsplat` とします。

本リポジトリ固有のマスク機能を利用するため、`uohige/gsplat` の
`custom/main` をcloneします。本家URLや `main` を直接cloneした場合、
downstream固有のマスク機能は含まれません。

```bash
mkdir -p ~/projects
cd ~/projects
git clone --recursive --branch custom/main git@github.com:uohige/gsplat.git
cd gsplat
```

すでに clone 済みなら:

```bash
cd ~/projects/gsplat
git switch custom/main
git pull --ff-only origin custom/main
git submodule update --init --recursive
```

## 4. Python 3.11 を固定する

`uv` で Python 3.11 を使うようにします。

```bash
cd ~/projects/gsplat
uv python install 3.11
uv python pin 3.11
```

`uv python pin 3.11` を実行すると、通常は `.python-version` が作られます。これにより、このリポジトリで使う Python バージョンが明示されます。

## 5. 仮想環境を作る

リポジトリ直下に `.venv` を作ります。

```bash
cd ~/projects/gsplat
uv venv --python 3.11 .venv
```

この `.venv` が、`gsplat` と examples 用依存のインストール先になります。

## 6. 仮想環境の使い方

以後の操作は、次のどちらかで行います。

方法 A: activate して使う

```bash
source .venv/bin/activate
```

方法 B: activate せず、`uv run` / `uv pip` を使う

```bash
uv run python --version
```

どちらでも構いませんが、作業手順を分かりやすく保つなら activate した方が理解しやすいです。

## 7. project ごとの CUDA 環境変数を用意する

このリポジトリは source install なので、`torch.utils.cpp_extension` が CUDA toolkit を見つけられる状態にしてからインストールする必要があります。

ここでは、グローバルな `~/.bashrc` に固定値を書くのではなく、この project 専用の設定ファイルをリポジトリ直下に置く方法を使います。

`~/projects/gsplat/env.cuda.sh` を作成します。

CUDA 12.8 を使う例:

```bash
cat > env.cuda.sh <<'EOF'
export CUDA_HOME=/usr/local/cuda-12.8
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
EOF
```

CUDA 13.0 を使う例:

```bash
cat > env.cuda.sh <<'EOF'
export CUDA_HOME=/usr/local/cuda-13.0
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
EOF
```

このファイルは、project ごとに `CUDA_HOME` を切り替えるためのものです。別の project では、その project 専用の `env.cuda.sh` を置いてください。

必要なら、`env.cuda.sh` ではなく `env.cuda.local.sh` のような名前にして `.gitignore` へ追加し、ローカル専用ファイルとして管理しても構いません。

## 8. 仮想環境を有効化したあとに CUDA 設定を読み込む

activate 済みであることを前提に、project 用の CUDA 設定を読み込みます。

```bash
source .venv/bin/activate
source ./env.cuda.sh
```

確認:

```bash
nvidia-smi
echo "$CUDA_HOME"
which nvcc
nvcc --version
```

最初に `nvidia-smi` がGPUとdriverを表示する必要があります。ここでdriverと通信できない場合、Pythonパッケージを変更してもCUDAは利用できません。`which nvcc` が空なら、指定したtoolkitがOSに入っていないか、`PATH` が正しく通っていません。

また、後で入れる PyTorch の CUDA 系と、この `CUDA_HOME` の系統は合わせるべきです。たとえば PyTorch を `cu128` で入れるなら、`CUDA_HOME=/usr/local/cuda-12.8` にそろえるのが安全です。

## 9. 先に PyTorch を入れる

`gsplat` の公式 README でも、PyTorch を先に入れる流れになっています。

現在の `examples/requirements.txt` は PyTorch 2.9.1 と torchvision 0.24.1 を固定しています。先に同じバージョンの `cu128` wheelを入れることで、後続の依存解決による意図しない置換を避けます。異なるバージョンを使う場合は、`examples/requirements.txt` の固定値との整合性を先に確認してください。

activate 済みなら:

```bash
uv pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu128
```

activate していないなら:

```bash
uv pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu128
```

確認:

```bash
python -c "import torch; print(torch.__version__); print(torch.version.cuda)"
```

または:

```bash
uv run python -c "import torch; print(torch.__version__); print(torch.version.cuda)"
```

## 10. 利用版を固定したい場合

常に最新の `custom/main` を追う場合でも、動作確認に使ったSHAは記録してください。

clone後に現在のbranchとcommitを確認します。

```bash
git branch --show-current
git rev-parse HEAD
```

branchが `custom/main` であることを確認し、SHAを記録します。公開済みの検証済み
releaseを使う場合は、対象の `mask-vMAJOR.MINOR.PATCH` tagをcheckoutします。

```bash
git fetch origin --tags
git switch --detach mask-vMAJOR.MINOR.PATCH
```

tagから変更を始める場合は、detached HEADのままcommitせず作業branchを作成します。

## 11. clone した repo から `gsplat` をインストールする

リポジトリのソースコードをそのまま使いたいなら、editable install が便利です。

```bash
uv pip install --no-build-isolation -e .
```

このコマンドの意味は次のとおりです。

- `-e .`: clone した作業ツリーをそのまま参照する
- `--no-build-isolation`: build 時に別の isolated 環境を作らず、今の `.venv` の PyTorch を使う

`--no-build-isolation` を勧める理由は、source build 時に別環境で異なる `torch` や CUDA 組み合わせが選ばれる事故を減らせるからです。これは公式 README の文言そのままではなく、実務上の安定化策です。

editable install にしたくない場合は:

```bash
uv pip install --no-build-isolation .
```

ただし、examples を見ながらコードを触る前提なら `-e` の方が扱いやすいです。

## 12. examples 用依存を入れる

`gsplat` の examples は別依存を持つので、公式 README に従って `examples/requirements.txt` も入れます。

```bash
uv pip install -r examples/requirements.txt --no-build-isolation
```

これで examples で必要な追加ライブラリが同じ `.venv` に入ります。

公式COLMAP bindingへ移行できていることも確認します。`SceneManager`しかない旧fork版が残っている場合は、依存更新に失敗しています。

```bash
python -c "import pycolmap; print(pycolmap.__version__); print(pycolmap.Reconstruction)"
```

このリポジトリはupstreamの `pyproject.toml` をアプリケーション用のuv projectへ作り替えていないため、空の `uv.lock` を再現性の根拠にはしません。再現性は、Git commit SHA、`examples/requirements.txt` の固定値、使用したPyTorch wheel indexを記録して確保します。

## 13. インストール確認

本体確認:

```bash
python -c "import gsplat; print(gsplat.__file__)"
```

または:

```bash
uv run python -c "import gsplat; print(gsplat.__file__)"
```

examples ディレクトリの存在確認:

```bash
ls examples
```

これで `examples/` のスクリプトを repo 上からそのまま実行できます。

## 14. examples を実行する

例:

```bash
python examples/simple_trainer.py
```

activate していない場合:

```bash
uv run python examples/simple_trainer.py
```

個々の example に追加のデータセットや引数が必要な場合は、その example の README やスクリプト先頭の引数定義を確認してください。

## 15. 更新方法

本家の更新を取り込んだforkブランチへ追従する場合:

```bash
cd ~/projects/gsplat
source .venv/bin/activate
source ./env.cuda.sh
git switch custom/main
git pull --ff-only origin custom/main
git submodule update --init --recursive
uv pip install --no-build-isolation -e .
uv pip install -r examples/requirements.txt --no-build-isolation
```

この流れで、作業ツリーと仮想環境を同期できます。

## 16. ローカル環境を汚さないための注意点

- Python 依存は `~/projects/gsplat/.venv` に閉じる
- 別プロジェクトの `.venv` は使い回さない
- `sudo pip install` は使わない
- `uv add` で別アプリ用の `pyproject.toml` に混ぜず、このrepository専用の `.venv` として扱う
- `CUDA_HOME` は project ごとの `env.cuda.sh` で切り替え、`~/.bashrc` に固定しない
- `custom/main` を業務用途で固定したいならcommit SHAまたは検証済みtagを保存する

## 17. うまくいかないときの見直し順

1. Python が `3.11` になっているか
2. `.venv` を本当に `~/projects/gsplat/.venv` で作っているか
3. `source ./env.cuda.sh` のあとに `which nvcc` と `echo "$CUDA_HOME"` が正しいか
4. PyTorch を先に入れているか
5. `uv pip install --no-build-isolation -e .` で入れているか
6. `examples/requirements.txt` を同じ `.venv` に入れているか
7. `torch.version.cuda` と `CUDA_HOME` の系統が合っているか
8. CUDA toolchain や driver が source build 要件を満たしているか
9. `pycolmap.Reconstruction` が存在し、旧 `SceneManager` 版が残っていないか

## 18. 参考

- gsplat README: https://github.com/nerfstudio-project/gsplat
- examples requirements: https://raw.githubusercontent.com/nerfstudio-project/gsplat/main/examples/requirements.txt
- Windows source install guide: https://github.com/nerfstudio-project/gsplat/blob/main/docs/INSTALL_WIN.md

forkの同期やrelease作成を行う保守者は、正本の
[`docs/operations.md`](docs/operations.md) も参照してください。

この手順は、examples を使う前提では `pip install git+...` よりも扱いやすく、Python 依存を `.venv` に閉じ込めたまま `custom/main` を追いやすい構成です。
