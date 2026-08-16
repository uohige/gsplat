# Fork保守運用

本書は、`uohige/gsplat` におけるfork運用、本家同期、検証済みreleaseの固定、
障害時確認の正本である。利用者向けの環境構築は
[`install-manual.md`](../install-manual.md) を参照する。

## 1. Remoteとbranchの責務

```text
upstream/main                    本家の正本
origin/main                      upstream/mainのfast-forward mirror
origin/custom/main               downstream機能を含む保護対象の利用branch
origin/feature/*, fix/*, docs/*  通常変更の作業branch
origin/chore/sync-upstream-*     本家同期の検証branch
```

remoteは次の組み合わせを正とする。

```bash
git remote -v
# origin    git@github.com:uohige/gsplat.git
# upstream  https://github.com/nerfstudio-project/gsplat.git
```

remoteが不足または不一致の場合は、作業を始める前に修正する。

```bash
git remote set-url origin git@github.com:uohige/gsplat.git
git remote add upstream https://github.com/nerfstudio-project/gsplat.git
```

`upstream` が既に存在してURLだけが異なる場合は、`git remote add` ではなく
`git remote set-url upstream https://github.com/nerfstudio-project/gsplat.git` を使う。

`main` にdownstream固有commitを置かない。実際の学習と配布には
`custom/main` または検証済みの `mask-vMAJOR.MINOR.PATCH` tagを使う。

## 2. 作業前の共通確認

同期、機能開発、release作成の前に、remote、branch、作業treeを確認する。

```bash
git status --short --branch
git remote -v
git branch -vv
git fetch --all --prune
```

未commitの変更がある場合は、その変更を対応する作業branchでcommitしてから進める。
dataset、checkpoint、PLY、render結果、ローカルCUDA設定はcommitしない。

## 3. 本家mainのmirror更新

`main` は `upstream/main` をfast-forward可能な状態で維持する。

```bash
git fetch upstream --prune
git switch main
git merge --ff-only upstream/main
git push origin main
```

`--ff-only` が失敗した場合は通常mergeで回避せず、`main` への自前commit混入や
remoteの取り違えを調査する。

```bash
git log --oneline --left-right --graph main...upstream/main
git remote -v
```

原因を確認せずに `main` をresetまたはforce-pushしない。

## 4. custom/mainへの本家更新取り込み

公開済みの `custom/main` はrebaseしない。本家更新は専用branchでmergeし、
upstreamとの祖先関係を保持したPull Requestとして統合する。

```bash
git fetch upstream --prune
git switch custom/main
git pull --ff-only origin custom/main
git switch -c chore/sync-upstream-YYYY-MM
git merge upstream/main
```

競合は同期branch上で解消する。解消後は、少なくともdownstreamのCPU回帰と
Sphinx文書を検証する。

```bash
.venv/bin/python -m pytest -q tests/test_colmap_masks.py tests/test_losses.py
make -C docs html SPHINXOPTS="-W --keep-going"
```

Pull Requestは次の向きで作成する。

```text
uohige/gsplat:chore/sync-upstream-YYYY-MM
  -> uohige/gsplat:custom/main
```

base repositoryに `nerfstudio-project/gsplat` を選ばない。同期Pull Requestは
通常変更のsquash mergeではなくmerge commitで統合し、upstreamとの祖先関係を
保持する。

## 5. 通常の機能・文書変更

通常変更は最新の `custom/main` からタスク単位のbranchを作る。

```bash
git switch custom/main
git pull --ff-only origin custom/main
git switch -c docs/A123-short-description
```

branch名は変更種別に応じて `feature/`、`fix/`、`docs/`、`chore/` などを使い、
管理対象タスクではtask IDを含める。実装、テスト、commit、push後、
`uohige/gsplat:custom/main` 宛てに単一目的のPull Requestを作成する。
通常変更はsquash mergeする。

`custom/main` への直接push、force-push、branch削除は行わない。branch protectionの
必須checkである `Mask and loss tests` と `Documentation` が成功してから統合する。

## 6. 検証済みreleaseの固定

実データと対応GPU環境で検証済みの `custom/main` commitだけをrelease対象とする。
tagは `mask-vMAJOR.MINOR.PATCH` 形式のannotated tagとし、公開済みtagを書き換えない。

```bash
git switch custom/main
git pull --ff-only origin custom/main
git status --short --branch
git tag -a mask-vMAJOR.MINOR.PATCH -m "Static-scene masks based on upstream UPSTREAM_SHA"
git push origin mask-vMAJOR.MINOR.PATCH
```

GitHub Releaseには次を記録する。

- release対象のdownstream commit SHA
- 対応するupstream commit SHA
- OS、GPU、NVIDIA driver、CUDA toolkit
- Python、PyTorch、pycolmapのversion
- maskのmode、threshold、missing policy、SfM点filter設定
- maskなし・maskありの検証条件と結果

必須情報または実データ検証が不足する状態を検証済みreleaseとして扱わない。
dataset、checkpoint、PLY、render結果はGit objectへ含めない。

## 7. 障害時の確認

まず現在地と履歴を採取する。

```bash
git status --short --branch
git remote -v
git branch -vv
git log --oneline --decorate --graph --max-count=12
```

症状ごとの確認点は次のとおりである。

- `main` をfast-forwardできない: `main...upstream/main` の左右差と自前commit混入を確認する。
- `custom/main` をfast-forwardできない: rebaseやforce-pushをせず、remote更新とlocal commitの帰属を確認する。
- 本家同期で競合する: `chore/sync-upstream-YYYY-MM` 上だけで解消し、downstreamテストと文書buildを再実行する。
- 必須checkが失敗する: GitHub Actionsの `Mask and loss tests` または `Documentation` の失敗stepを再現し、成功するまで統合しない。
- source buildが失敗する: [`install-manual.md`](../install-manual.md) のdriver、CUDA toolkit、PyTorch、pycolmapの順で境界を確認する。

復旧時も `git reset --hard`、公開済みbranchのrebase、force-pushを通常手段として
使用しない。履歴変更が必要に見える場合は、対象branchと影響範囲を確認してから
repository管理者と方針を合意する。
