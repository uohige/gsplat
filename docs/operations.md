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

## 3. Downstream差分の確認

自作部分の境界は手書きのfile一覧ではなく、Gitの共通祖先から算出する。
作業前に本家refを更新し、標準診断scriptを実行する。

```bash
git fetch upstream --prune
lint/show-downstream-delta.sh
```

既定では `upstream/main` と現在の `HEAD` を比較する。branchを明示する場合は、
本家ref、downstream refの順に指定する。

```bash
lint/show-downstream-delta.sh upstream/main custom/main
```

出力の意味は次のとおりである。

- `Shared base`: 本家とdownstreamが最後に共有するcommit
- `Downstream-only commits`: 本家refから到達できず、downstream refから到達できるcommit
- `Changed paths since shared base`: 共通祖先からdownstream側で追加、変更、削除されたpath

変更内容を詳しく確認する場合は、scriptが表示した共通祖先を基準に `git diff` を実行する。

```bash
git diff upstream/main...custom/main
git diff upstream/main...custom/main -- examples/datasets/colmap.py
git log --oneline upstream/main..custom/main
```

`upstream/main` をfetchせずに古いrefのまま診断すると、すでに本家へ入った変更を
downstream固有と誤認する可能性がある。同期前後とも、診断より先にfetchする。

## 4. 本家mainのmirror更新

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

## 5. custom/mainへの本家更新取り込み

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

## 6. 通常の機能・文書変更

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

## 7. 検証済みreleaseの固定

実データと対応GPU環境で検証済みの `custom/main` commitだけをrelease対象とする。
tagは `mask-vMAJOR.MINOR.PATCH` 形式のannotated tagとし、公開済みtagを書き換えない。

初回の参照環境は次の組み合わせとする。

- Ubuntu 24.04 LTS
- NVIDIA GeForce RTX 4070
- CUDA toolkit 12.8
- Python 3.11
- PyTorch 2.9.1+cu128
- torchvision 0.24.1

GPUのdesktopまたはlaptop区分、VRAM容量、NVIDIA driver、Python patch、pycolmapは
検証時に使用した完全なversionを記録する。この参照環境は検証済みの1構成を示し、
他のGPUや依存versionを一括して保証するsupport matrixとして扱わない。

検証用datasetは、40〜60枚を目安とする特徴点の十分な静的シーンを撮影する。
動的対象を3か所以上へ移動し、各位置を5視点以上から撮影する。全画像へexclude maskを
対応付け、missing policyは `error` とする。dataset名、画像数、解像度、mask設定、
画像一覧のmanifest hashを記録し、dataset自体はrepositoryへcommitしない。

maskなし・maskありの比較では、dataset、split、seed、30,000 steps、
`data_factor=4`、default strategyを共通とし、単一GPU、viewer無効、PLY出力無効で
実行する。RTX 4070でOOMになる場合はpacked modeを両runへ適用し、その変更を記録する。
両runのcheckpointは同一valid mask領域で評価する。

releaseの合格条件は次のとおりとする。

- maskなし・maskありが例外やNaNなしで30,000 stepsを完了する
- mask filtering後にも初期SfM点が残る
- 除外された初期SfM点が100点以上、または元点群の1%以上である
- maskありのvalid領域PSNRがmaskなしより0.5 dBを超えて低下しない
- 事前選定した3 view以上のうち1 view以上で動的対象由来のghostが低減する
- 静的背景に新しい大規模な欠損、ぼけ、mask境界の破綻がない

SSIM、LPIPS、最終Gaussian数、所要時間、最大GPU memoryは比較結果へ記録するが、
初回releaseの合否閾値には使用しない。

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
- GPUのdesktopまたはlaptop区分とVRAM容量
- Python、PyTorch、torchvision、pycolmapのversion
- dataset名、画像数、解像度、manifest hash
- maskのmode、threshold、missing policy、SfM点filter設定
- maskなし・maskありの共通条件、初期SfM点、PSNR、SSIM、LPIPS、最終Gaussian数、所要時間、最大GPU memory
- 事前選定viewにおけるghost低減と静的背景の目視結果

必須情報または実データ検証が不足する状態を検証済みreleaseとして扱わない。
dataset、checkpoint、PLY、render結果はGit objectへ含めない。

versionは変更内容から次のように決定する。

- `MAJOR`: mask規約、dataset形式、CLIの意味、既定の安全動作に後方互換性のない変更
- `MINOR`: 後方互換なmask機能または対応環境の追加
- `PATCH`: 後方互換な修正、本家同期、依存・文書・CI更新

同一commitと同一検証内容を同じ環境で再確認しただけの場合は新versionを発行しない。

## 8. 障害時の確認

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
