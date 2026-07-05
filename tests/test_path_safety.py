"""Tests for path_safety.py and tar/file restore guards."""

import io
import tarfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from d4_snap.path_safety import (
    is_safe_relative_path,
    is_within_directory,
    resolve_under_root,
)
from d4_snap.git_operations import (
    safe_extract_tar,
    extract_file_from_snapshot,
    show_diff,
)


class TestPathSafety:
    def test_is_safe_relative_path_accepts_normal(self):
        assert is_safe_relative_path("src/foo.py") is True
        assert is_safe_relative_path("README.md") is True

    def test_is_safe_relative_path_rejects_traversal(self):
        assert is_safe_relative_path("../etc/passwd") is False
        assert is_safe_relative_path("src/../../outside") is False

    def test_is_safe_relative_path_rejects_absolute(self):
        assert is_safe_relative_path("/etc/passwd") is False
        assert is_safe_relative_path("C:/Windows/system.ini") is False

    def test_resolve_under_root(self, temp_dir):
        root = temp_dir / "repo"
        root.mkdir()
        target = resolve_under_root(root, "src/app.py")
        assert target == (root / "src/app.py").resolve()

    def test_resolve_under_root_rejects_escape(self, temp_dir):
        root = temp_dir / "repo"
        root.mkdir()
        assert resolve_under_root(root, "../outside.txt") is None

    def test_is_within_directory(self, temp_dir):
        root = temp_dir / "repo"
        root.mkdir()
        child = root / "a" / "b.txt"
        child.parent.mkdir(parents=True)
        child.write_text("x")
        assert is_within_directory(child, root) is True
        assert is_within_directory(temp_dir / "other", root) is False


class TestSafeExtractTar:
    def test_rejects_path_traversal_member(self, temp_dir):
        extract_dir = temp_dir / "extract"
        extract_dir.mkdir()
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            info = tarfile.TarInfo(name="../escape.txt")
            info.size = 4
            tar.addfile(info, io.BytesIO(b"evil"))

        buf.seek(0)
        with tarfile.open(fileobj=buf, mode="r:") as tar:
            with pytest.raises(RuntimeError, match="Path traversal"):
                safe_extract_tar(tar, str(extract_dir))

    def test_allows_safe_member(self, temp_dir):
        extract_dir = temp_dir / "extract"
        extract_dir.mkdir()
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            data = b"hello"
            info = tarfile.TarInfo(name="safe.txt")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        buf.seek(0)
        with tarfile.open(fileobj=buf, mode="r:") as tar:
            safe_extract_tar(tar, str(extract_dir))

        assert (extract_dir / "safe.txt").read_text() == "hello"


class TestExtractFileFromSnapshot:
    def test_rejects_path_traversal(self, temp_dir):
        work_tree = temp_dir / "repo"
        work_tree.mkdir()
        assert (
            extract_file_from_snapshot("abc123", "../../../etc/passwd", str(work_tree))
            is False
        )

    @patch("d4_snap.git_operations.run_shadow_cmd")
    def test_writes_under_work_tree(self, mock_run, temp_dir):
        work_tree = temp_dir / "repo"
        work_tree.mkdir()
        mock_run.return_value = Mock(returncode=0, stdout="restored")

        ok = extract_file_from_snapshot("abc123", "src/foo.py", str(work_tree))

        assert ok is True
        assert (work_tree / "src" / "foo.py").read_text() == "restored"
        mock_run.assert_called_once_with(
            ["show", "abc123:src/foo.py"],
            capture_output=True,
            check=False,
            quiet=True,
        )


class TestShowDiff:
    @patch("d4_snap.git_operations.run_shadow_cmd")
    def test_rejects_unsafe_path(self, mock_run):
        show_diff("abc123", "../../../etc/passwd")
        mock_run.assert_not_called()

    @patch("d4_snap.git_operations.run_shadow_cmd")
    def test_passes_safe_path(self, mock_run):
        show_diff("abc123", "src/foo.py")
        mock_run.assert_called_once_with(
            ["diff", "abc123", "--", "src/foo.py"],
            check=False,
            quiet=False,
        )
