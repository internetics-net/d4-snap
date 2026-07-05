"""Path resolution guards for d4-snap file reads and writes."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

_UNSAFE_CHARS = frozenset({"\0", "\n", "\r"})


def normalize_rel_posix(path: str) -> str:
    return path.replace("\\", "/").strip().strip("/")


def is_safe_relative_path(rel: str) -> bool:
    """Reject traversal, absolute paths, and unsafe characters in user paths."""
    if not rel or not isinstance(rel, str):
        return False
    if any(ch in rel for ch in _UNSAFE_CHARS):
        return False
    if Path(rel).is_absolute() or rel.startswith(("/", "~")):
        return False
    if len(rel) > 1 and rel[1] == ":":
        return False
    normalized = normalize_rel_posix(rel)
    if not normalized:
        return False
    if ".." in normalized.split("/"):
        return False
    return True


def is_within_directory(path: Path, base: Path) -> bool:
    """Return True when *path* resolves to a location under *base*."""
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except (ValueError, OSError):
        return False


def resolve_under_root(root: Path, rel_path: str) -> Optional[Path]:
    """Resolve *rel_path* under *root*, or None when unsafe."""
    if not is_safe_relative_path(rel_path):
        return None
    root_resolved = root.resolve()
    target = (root_resolved / rel_path).resolve()
    if not is_within_directory(target, root_resolved):
        return None
    return target
