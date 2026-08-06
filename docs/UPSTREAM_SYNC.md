# Fork and upstream maintenance

このforkは、本家 `nerfstudio-project/gsplat` を継続的に取り込みながら、
静的シーン向けCOLMAPマスク機能とインストール手順を提供します。

## Remoteとブランチの役割

```text
upstream/main                    本家の正本
origin/main                      upstream/mainのミラー
origin/custom/main               動作確認済みの利用ブランチ
origin/feature/*                 機能開発
origin/chore/sync-upstream-*     本家更新の検証
```

remoteは次の組み合わせを正とします。

```bash
git remote -v
# origin    git@github.com:uohige/gsplat.git
# upstream  https://github.com/nerfstudio-project/gsplat.git
```

`main` へ自前コミットを直接追加しません。実際の学習や配布には
`custom/main` またはそこから作成したtagを使用します。

## 本家mainのミラー更新

```bash
git fetch upstream --prune
git switch main
git merge --ff-only upstream/main
git push origin main
```

`--ff-only` が失敗した場合、`main` に自前コミットが混入しています。
その場で通常mergeせず、履歴を確認してください。

## custom/mainへの本家更新取り込み

公開済みの `custom/main` はrebaseせず、更新用ブランチでmergeします。

```bash
git fetch upstream --prune
git switch custom/main
git pull --ff-only origin custom/main
git switch -c chore/sync-upstream-YYYY-MM
git merge upstream/main
```

競合を解消したら、最低限次を確認します。

```bash
.venv/bin/python -m pytest -q tests/test_colmap_masks.py tests/test_losses.py
source .venv/bin/activate
make -C docs html
```

その後、GitHubで次のPull Requestを作成します。

```text
uohige/gsplat:chore/sync-upstream-YYYY-MM
  -> uohige/gsplat:custom/main
```

本家へ提案する意図がない場合、PRのbase repositoryに
`nerfstudio-project/gsplat` を選択しないでください。

## 機能開発

```bash
git switch custom/main
git pull --ff-only origin custom/main
git switch -c feature/<short-description>
```

実装、テスト、commit、push後、自分のfork内で `custom/main` 宛てのPRを作ります。
`custom/main` への直接pushやforce pushは行いません。

## 動作確認版の固定

実データとGPUで検証したcommitにはannotated tagを付けます。

```bash
git switch custom/main
git pull --ff-only origin custom/main
git tag -a mask-vX.Y.Z -m "Static-scene masks based on upstream <SHA>"
git push origin mask-vX.Y.Z
```

GitHub Releaseには以下を記録します。

- 対応するupstream commit SHA
- Python、PyTorch、CUDA、driver、pycolmapのバージョン
- マスクのmode、threshold、SfM点フィルタ設定
- 検証に使用したデータとテスト結果

データセット、checkpoint、PLY、レンダリング結果はGitへcommitしません。

## 障害時の確認

```bash
git status --short --branch
git remote -v
git branch -vv
git log --oneline --decorate --graph --max-count=12
```

同期作業前には作業ツリーをcleanにし、必要なら作業ブランチを作成してから進めます。
`git reset --hard` や公開済みブランチへのforce pushは復旧手段として常用しません。
