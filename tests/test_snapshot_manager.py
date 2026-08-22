"""Tests for snapshot_manager.py module"""

from unittest.mock import patch, Mock

from d4_snap.snapshot_manager import SnapshotManager


class TestSnapshotManager:
    """Test cases for SnapshotManager class"""

    def test_snapshot_manager_init(self):
        """Test SnapshotManager initialization"""
        with patch("d4_snap.snapshot_manager.git_ops.init_shadow_repo") as mock_init:
            snap_mgr = SnapshotManager()
            assert snap_mgr is not None
            mock_init.assert_called_once()

    def test_create_snapshot_success(self):
        """Test creating snapshot successfully"""
        with patch("d4_snap.snapshot_manager.git_ops.init_shadow_repo"):
            with patch(
                "d4_snap.snapshot_manager.git_ops.get_current_branch",
                return_value="main",
            ):
                with patch(
                    "d4_snap.snapshot_manager.git_ops.stage_worktree_for_snapshot"
                ) as mock_stage:
                    with patch(
                        "d4_snap.snapshot_manager.git_ops.run_shadow_cmd"
                    ) as mock_run:
                        mock_commit_result = Mock()
                        mock_commit_result.stdout = "commit hash"
                        mock_commit_result.stderr = ""
                        mock_commit_result.returncode = 0

                        mock_rev_result = Mock()
                        mock_rev_result.stdout = "abc123456789"
                        mock_rev_result.returncode = 0

                        mock_diff_result = Mock()
                        mock_diff_result.returncode = 0
                        mock_diff_result.stdout = "src/foo.py\nsrc/bar.py\n"

                        mock_metadata_result = Mock()
                        mock_metadata_result.returncode = 0

                        mock_run.side_effect = [
                            mock_commit_result,
                            mock_rev_result,
                            mock_diff_result,
                            mock_metadata_result,
                        ]

                        snap_mgr = SnapshotManager()
                        result = snap_mgr.create_snapshot()

                        mock_stage.assert_called_once()
                        assert result["success"] is True
                        assert "hash" in result

    def test_create_snapshot_no_changes(self):
        """Test creating snapshot with no changes"""
        with patch("d4_snap.snapshot_manager.git_ops.init_shadow_repo"):
            with patch(
                "d4_snap.snapshot_manager.git_ops.get_current_branch",
                return_value="main",
            ):
                with patch(
                    "d4_snap.snapshot_manager.git_ops.run_shadow_cmd"
                ) as mock_run:
                    # Mock no changes - need to check for "nothing to commit" in stdout or stderr
                    mock_run.return_value = Mock(
                        returncode=0, stdout="nothing to commit", stderr=""
                    )

                    snap_mgr = SnapshotManager()
                    result = snap_mgr.create_snapshot()

                    assert result["success"] is False
