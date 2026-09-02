# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "lint" / "show-downstream-delta.sh"


def _git(repository: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _commit_file(repository: Path, name: str, contents: str, message: str) -> None:
    (repository / name).write_text(contents, encoding="utf-8")
    _git(repository, "add", name)
    _git(repository, "commit", "-m", message)


def _install_script(repository: Path) -> Path:
    installed_script = repository / "lint" / SCRIPT.name
    installed_script.parent.mkdir()
    shutil.copy2(SCRIPT, installed_script)
    return installed_script


def test_reports_commits_and_paths_since_shared_base(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.name", "Downstream Test")
    _git(tmp_path, "config", "user.email", "downstream@example.invalid")
    _commit_file(tmp_path, "upstream.txt", "base\n", "upstream base")
    _git(tmp_path, "branch", "upstream/main")
    base_sha = _git(tmp_path, "rev-parse", "--short=12", "HEAD").stdout.strip()
    _commit_file(tmp_path, "custom.txt", "custom\n", "downstream change")
    installed_script = _install_script(tmp_path)

    result = subprocess.run(
        ["bash", str(installed_script)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    assert f"Shared base: {base_sha}" in result.stdout
    assert "Downstream-only commits: 1" in result.stdout
    assert "Changed paths since shared base: 1" in result.stdout
    assert "downstream change" in result.stdout
    assert "A\tcustom.txt" in result.stdout


def test_fails_for_unknown_ref(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    installed_script = _install_script(tmp_path)
    result = subprocess.run(
        ["bash", str(installed_script), "missing-ref", "HEAD"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Git ref does not resolve to a commit: missing-ref" in result.stderr


def test_fails_when_refs_have_no_common_ancestor(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.name", "Downstream Test")
    _git(tmp_path, "config", "user.email", "downstream@example.invalid")
    _commit_file(tmp_path, "upstream.txt", "base\n", "upstream base")
    _git(tmp_path, "branch", "upstream/main")
    _git(tmp_path, "checkout", "--orphan", "disconnected")
    (tmp_path / "upstream.txt").unlink()
    _commit_file(tmp_path, "custom.txt", "custom\n", "disconnected change")
    installed_script = _install_script(tmp_path)

    result = subprocess.run(
        ["bash", str(installed_script), "upstream/main", "disconnected"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "The selected refs have no common ancestor." in result.stderr
