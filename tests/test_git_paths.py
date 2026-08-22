"""Tests for git_paths module."""

from pathlib import Path

from d4_snap.git_paths import gitignored_rel_paths, is_always_skipped_rel_path


def test_is_always_skipped_venv():
    assert is_always_skipped_rel_path(".venv/lib/site.py")
    assert is_always_skipped_rel_path("venv/bin/python")
    assert not is_always_skipped_rel_path("src/mod.py")


def test_gitignored_rel_paths_respects_gitignore(tmp_path: Path):
    import subprocess

    project = tmp_path / "proj"
    project.mkdir()
    (project / ".gitignore").write_text(".venv/\n", encoding="utf-8", newline="\n")
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "add", ".gitignore"], cwd=project, check=True, capture_output=True)

    ignored = gitignored_rel_paths(
        project,
        ["src/main.py", ".venv/lib/site.py"],
    )
    assert "src/main.py" not in ignored
    assert ".venv/lib/site.py" in ignored
