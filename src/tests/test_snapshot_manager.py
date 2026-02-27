"""Tests for snapshot_manager.py module"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import tempfile
import shutil
from pathlib import Path
import sys
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from d4_snap.snapshot_manager import SnapshotManager


class TestSnapshotManager:
    """Test cases for SnapshotManager class"""

    def test_snapshot_manager_init(self, mock_git_operations, mock_ui):
        """Test SnapshotManager initialization"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        assert snap_mgr.git_ops == mock_git_operations
        assert snap_mgr.ui == mock_ui

    def test_create_snapshot_success(self, mock_git_operations, mock_ui, mock_git_repo):
        """Test creating snapshot successfully"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        # Mock all the git operations
        mock_git_operations.get_repo_name.return_value = "test_repo"
        mock_git_operations.get_repo_hash.return_value = "abc12345"
        mock_git_operations.init_bare_repo.return_value = True
        mock_git_operations.add_remote.return_value = True
        mock_git_operations.create_shadow_branch.return_value = True
        mock_git_operations.push_to_shadow.return_value = True
        mock_git_operations.get_current_branch.return_value = "main"

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = snap_mgr.create_snapshot()

            assert result["success"] is True
            assert "hash" in result
            assert len(result["hash"]) == 7  # Short hash

    def test_create_snapshot_no_git_repo(self, mock_git_operations, mock_ui):
        """Test creating snapshot when not in git repo"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        mock_git_operations.get_repo_name.return_value = None

        result = snap_mgr.create_snapshot()

        assert result["success"] is False
        assert "error" in result

    def test_create_snapshot_bare_repo_failure(self, mock_git_operations, mock_ui):
        """Test creating snapshot when bare repo init fails"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        mock_git_operations.get_repo_name.return_value = "test_repo"
        mock_git_operations.get_repo_hash.return_value = "abc12345"
        mock_git_operations.init_bare_repo.return_value = False

        result = snap_mgr.create_snapshot()

        assert result["success"] is False
        assert "error" in result

    def test_get_snapshots_success(self, mock_git_operations, mock_ui):
        """Test getting snapshots successfully"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        # Mock git log output
        mock_log_output = """abc12345 2024-02-27 20:00:00 +0000 main
def67890 2024-02-27 19:00:00 +0000 feature-branch
"""

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=mock_log_output)

            snapshots = snap_mgr.get_snapshots()

            assert len(snapshots) == 2
            assert snapshots[0]["hash"] == "abc12345"
            assert snapshots[0]["branch"] == "main"
            assert snapshots[1]["hash"] == "def67890"
            assert snapshots[1]["branch"] == "feature-branch"

    def test_get_snapshots_group_by_branch(self, mock_git_operations, mock_ui):
        """Test getting snapshots grouped by branch"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        mock_log_output = """abc12345 2024-02-27 20:00:00 +0000 main
def67890 2024-02-27 19:00:00 +0000 main
ghi98765 2024-02-27 18:00:00 +0000 feature-branch
"""

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=mock_log_output)

            snapshots = snap_mgr.get_snapshots(group_by_branch=True)

            assert len(snapshots) == 2  # Two groups
            assert "main" in snapshots
            assert "feature-branch" in snapshots
            assert len(snapshots["main"]) == 2
            assert len(snapshots["feature-branch"]) == 1

    def test_get_snapshots_no_snapshots(self, mock_git_operations, mock_ui):
        """Test getting snapshots when none exist"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="")

            snapshots = snap_mgr.get_snapshots()

            assert snapshots == []

    def test_get_snapshot_details_success(self, mock_git_operations, mock_ui):
        """Test getting snapshot details successfully"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        mock_log_output = """abc12345 2024-02-27 20:00:00 +0000 main
commit message
"""

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=mock_log_output)

            details = snap_mgr.get_snapshot_details("abc12345")

            assert details["hash"] == "abc12345"
            assert details["branch"] == "main"
            assert "commit message" in details["message"]

    def test_get_snapshot_details_not_found(self, mock_git_operations, mock_ui):
        """Test getting details for non-existent snapshot"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            details = snap_mgr.get_snapshot_details("nonexistent")

            assert details is None

    def test_restore_snapshot_success(self, mock_git_operations, mock_ui):
        """Test restoring snapshot successfully"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        # Mock the snapshot details
        mock_snapshot = {"hash": "abc12345", "branch": "main", "message": "Test commit"}

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = snap_mgr.restore_snapshot(mock_snapshot, "everything")

            assert result["success"] is True

    def test_restore_snapshot_specific_file(self, mock_git_operations, mock_ui):
        """Test restoring specific file from snapshot"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        mock_snapshot = {"hash": "abc12345", "branch": "main", "message": "Test commit"}

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = snap_mgr.restore_snapshot(mock_snapshot, "specific", "src/test.py")

            assert result["success"] is True

    def test_delete_snapshot_success(self, mock_git_operations, mock_ui):
        """Test deleting snapshot successfully"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = snap_mgr.delete_snapshot("abc12345")

            assert result["success"] is True

    def test_delete_snapshot_failure(self, mock_git_operations, mock_ui):
        """Test deleting snapshot with failure"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = snap_mgr.delete_snapshot("abc12345")

            assert result["success"] is False

    def test_toggle_favorite_success(self, mock_git_operations, mock_ui):
        """Test toggling favorite status successfully"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = snap_mgr.toggle_favorite("abc12345")

            assert result["success"] is True

    def test_rename_snapshot_success(self, mock_git_operations, mock_ui):
        """Test renaming snapshot successfully"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = snap_mgr.rename_snapshot("abc12345", "New Name")

            assert result["success"] is True

    def test_cleanup_old_snapshots_success(self, mock_git_operations, mock_ui):
        """Test cleaning up old snapshots successfully"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = snap_mgr.cleanup_old_snapshots()

            assert result["success"] is True

    def test_get_diff_success(self, mock_git_operations, mock_ui):
        """Test getting diff successfully"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        mock_diff_output = """diff --git a/test.txt b/test.txt
index 1234567..abcdefg 100644
--- a/test.txt
+++ b/test.txt
@@ -1 +1 @@
-old content
+new content
"""

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=mock_diff_output)

            diff = snap_mgr.get_diff("abc12345")

            assert "old content" in diff
            assert "new content" in diff

    def test_get_diff_specific_file(self, mock_git_operations, mock_ui):
        """Test getting diff for specific file"""
        snap_mgr = SnapshotManager(mock_git_operations, mock_ui)

        with patch("d4_snap.snapshot_manager.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="file diff")

            diff = snap_mgr.get_diff("abc12345", "test.txt")

            assert diff == "file diff"
            mock_run.assert_called_with(
                ["git", "diff", "abc12345", "--", "test.txt"],
                capture_output=True,
                quiet=True,
            )
