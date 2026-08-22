"""Git-aware path filtering for snapshot staging (respects .gitignore)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, Set

_ALWAYS_SKIP_SUFFIXES = (".pyc", ".pyo", ".pyd")
_ALWAYS_SKIP_PARTS = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "venv",
        "node_modules",
        ".git",
    }
)


def normalize_rel_path(rel_path: str) -> str:
    return rel_path.replace("\\", "/").strip("/")


def is_always_skipped_rel_path(rel_path: str) -> bool:
    """Hard-coded skips for artifacts .gitignore may not cover."""
    normalized = normalize_rel_path(rel_path)
    if not normalized:
        return True
    parts = normalized.split("/")
    if any(part in _ALWAYS_SKIP_PARTS for part in parts):
        return True
    lower = normalized.lower()
    return lower.endswith(_ALWAYS_SKIP_SUFFIXES)


def gitignored_rel_paths(project_root: Path, rel_paths: Iterable[str]) -> Set[str]:
    """Return relative paths treated as ignored (git + built-in skips)."""
    normalized = [normalize_rel_path(p) for p in rel_paths if p]
    ignored = {p for p in normalized if is_always_skipped_rel_path(p)}
    remaining = [p for p in normalized if p not in ignored]
    if not remaining:
        return ignored

    try:
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if inside.returncode != 0 or inside.stdout.strip() != "true":
            return ignored

        ignored.update(_git_check_ignore_batch(project_root, remaining))
    except (OSError, subprocess.SubprocessError):
        pass

    return ignored


def _git_check_ignore_batch(project_root: Path, rel_paths: list[str]) -> Set[str]:
    ignored: Set[str] = set()
    chunk_size = 200
    for start in range(0, len(rel_paths), chunk_size):
        chunk = rel_paths[start : start + chunk_size]
        proc = subprocess.run(
            ["git", "check-ignore", "--", *chunk],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        for line in proc.stdout.splitlines():
            line = normalize_rel_path(line.strip())
            if line:
                ignored.add(line)
    return ignored
