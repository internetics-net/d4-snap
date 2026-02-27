"""Tests for ui.py module"""

import pytest
from unittest.mock import patch, Mock
import tempfile
import shutil
from pathlib import Path
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from d4_snap.ui import UserInterface


class TestUserInterface:
    """Test cases for UserInterface class"""

    def test_ui_init(self, mock_menu_manager):
        """Test UI initialization"""
        ui = UserInterface()
        # Note: UserInterface gets its own menu_mgr via get_menu_manager()
        assert ui.menu_mgr is not None

    def test_display_title(self, mock_ui, capsys):
        """Test displaying title"""
        mock_ui.display_title("save_snapshot")

        captured = capsys.readouterr()
        assert "Test Save" in captured.out

    def test_display_title_nonexistent(self, mock_ui, capsys):
        """Test displaying non-existent title"""
        mock_ui.display_title("nonexistent")

        captured = capsys.readouterr()
        assert "Title 'nonexistent' not found" in captured.out

    def test_display_message(self, mock_ui, capsys):
        """Test displaying message"""
        mock_ui.display_message("save_snapshot", "success", {"hash": "abc123"})

        captured = capsys.readouterr()
        assert "Success! abc123" in captured.out

    def test_display_message_no_vars(self, mock_ui, capsys):
        """Test displaying message without variables"""
        mock_ui.display_message("save_snapshot", "saving")

        captured = capsys.readouterr()
        assert "Saving..." in captured.out

    def test_display_snapshots(self, mock_ui, capsys):
        """Test displaying snapshots list"""
        snapshots = [
            {
                "hash": "abc12345",
                "branch": "main",
                "description": "Test snapshot 1",
                "favorite": True,
                "timestamp": "2024-02-27 20:00:00",
            },
            {
                "hash": "def67890",
                "branch": "feature",
                "description": "Test snapshot 2",
                "favorite": False,
                "timestamp": "2024-02-27 19:00:00",
            },
        ]

        mock_ui.display_snapshots(snapshots)

        captured = capsys.readouterr()
        assert "abc1234" in captured.out  # Short hash
        assert "⭐" in captured.out  # Favorite indicator
        assert "main" in captured.out
        assert "Test snapshot 1" in captured.out

    def test_display_snapshots_grouped(self, mock_ui, capsys):
        """Test displaying grouped snapshots"""
        grouped_snapshots = {
            "main": [
                {
                    "hash": "abc12345",
                    "branch": "main",
                    "description": "Main snapshot",
                    "favorite": False,
                    "timestamp": "2024-02-27 20:00:00",
                }
            ],
            "feature": [
                {
                    "hash": "def67890",
                    "branch": "feature",
                    "description": "Feature snapshot",
                    "favorite": True,
                    "timestamp": "2024-02-27 19:00:00",
                }
            ],
        }

        mock_ui.display_snapshots(grouped_snapshots, group_by_branch=True)

        captured = capsys.readouterr()
        assert "main" in captured.out
        assert "feature" in captured.out
        assert "⭐" in captured.out

    def test_get_snapshot_selection_valid(self, mock_ui):
        """Test getting valid snapshot selection"""
        snapshots = [
            {"hash": "abc12345", "description": "Snapshot 1"},
            {"hash": "def67890", "description": "Snapshot 2"},
        ]

        with patch.object(mock_ui.menu_mgr, "get_snapshot_number", return_value=1):
            result = mock_ui.get_snapshot_selection(snapshots, "restore_snapshot")
            assert result == snapshots[0]

    def test_get_snapshot_selection_cancel(self, mock_ui):
        """Test canceling snapshot selection"""
        snapshots = [{"hash": "abc12345", "description": "Snapshot 1"}]

        with patch.object(mock_ui.menu_mgr, "get_snapshot_number", return_value=None):
            result = mock_ui.get_snapshot_selection(snapshots, "restore_snapshot")
            assert result is None

    def test_get_snapshot_selection_invalid(self, mock_ui):
        """Test invalid snapshot selection"""
        snapshots = [{"hash": "abc12345", "description": "Snapshot 1"}]

        with patch.object(mock_ui.menu_mgr, "get_snapshot_number", return_value=5):
            result = mock_ui.get_snapshot_selection(snapshots, "restore_snapshot")
            assert result is None

    def test_get_restore_choice_full(self, mock_ui):
        """Test getting full restore choice"""
        with patch.object(mock_ui.menu_mgr, "get_user_input", return_value="1"):
            result = mock_ui.get_restore_choice()
            assert result == "everything"

    def test_get_restore_choice_specific(self, mock_ui):
        """Test getting specific restore choice"""
        with patch.object(mock_ui.menu_mgr, "get_user_input", return_value="2"):
            result = mock_ui.get_restore_choice()
            assert result == "specific"

    def test_get_restore_choice_invalid(self, mock_ui):
        """Test invalid restore choice"""
        with patch.object(mock_ui.menu_mgr, "get_user_input", return_value="3"):
            result = mock_ui.get_restore_choice()
            assert result is None

    def test_get_file_path_valid(self, mock_ui):
        """Test getting valid file path"""
        with patch.object(
            mock_ui.menu_mgr, "get_text_input", return_value="src/test.py"
        ):
            result = mock_ui.get_file_path()
            assert result == "src/test.py"

    def test_get_file_path_empty(self, mock_ui):
        """Test getting empty file path"""
        with patch.object(mock_ui.menu_mgr, "get_text_input", return_value=""):
            result = mock_ui.get_file_path()
            assert result is None

    def test_get_manage_choice_valid(self, mock_ui):
        """Test getting valid manage choice"""
        with patch.object(mock_ui.menu_mgr, "get_user_input", return_value="1"):
            result = mock_ui.get_manage_choice()
            assert result == "toggle_favorite"

    def test_get_manage_choice_invalid(self, mock_ui):
        """Test invalid manage choice"""
        with patch.object(mock_ui.menu_mgr, "get_user_input", return_value="4"):
            result = mock_ui.get_manage_choice()
            assert result is None

    def test_get_new_name_valid(self, mock_ui):
        """Test getting valid new name"""
        with patch.object(
            mock_ui.menu_mgr, "get_text_input", return_value="New Snapshot Name"
        ):
            result = mock_ui.get_new_name("Old Name")
            assert result == "New Snapshot Name"

    def test_get_new_name_empty(self, mock_ui):
        """Test getting empty new name"""
        with patch.object(mock_ui.menu_mgr, "get_text_input", return_value=""):
            result = mock_ui.get_new_name("Old Name")
            assert result is None

    def test_get_confirm_restore_yes(self, mock_ui):
        """Test confirming restore with yes"""
        with patch.object(mock_ui.menu_mgr, "get_confirm", return_value=True):
            result = mock_ui.get_confirm_restore("abc12345")
            assert result is True

    def test_get_confirm_restore_no(self, mock_ui):
        """Test confirming restore with no"""
        with patch.object(mock_ui.menu_mgr, "get_confirm", return_value=False):
            result = mock_ui.get_confirm_restore("abc12345")
            assert result is False

    def test_display_diff(self, mock_ui, capsys):
        """Test displaying diff"""
        diff_content = """diff --git a/test.txt b/test.txt
-index 1234567..abcdefg 100644
--- a/test.txt
+++ b/test.txt
@@ -1 +1 @@
-old line
+new line
"""

        mock_ui.display_diff(diff_content)

        captured = capsys.readouterr()
        assert "old line" in captured.out
        assert "new line" in captured.out

    def test_display_diff_empty(self, mock_ui, capsys):
        """Test displaying empty diff"""
        mock_ui.display_diff("")

        captured = capsys.readouterr()
        assert "No differences found" in captured.out

    def test_display_operation_result_success(self, mock_ui, capsys):
        """Test displaying successful operation result"""
        result = {"success": True, "message": "Operation completed"}

        mock_ui.display_operation_result("restore_snapshot", result)

        captured = capsys.readouterr()
        assert "Operation completed" in captured.out

    def test_display_operation_result_failure(self, mock_ui, capsys):
        """Test displaying failed operation result"""
        result = {"success": False, "error": "Something went wrong"}

        mock_ui.display_operation_result("restore_snapshot", result)

        captured = capsys.readouterr()
        assert "Something went wrong" in captured.out

    def test_display_cleanup_result(self, mock_ui, capsys):
        """Test displaying cleanup result"""
        result = {"success": True, "expired_count": 5, "freed_space": "1.2 MB"}

        mock_ui.display_cleanup_result(result)

        captured = capsys.readouterr()
        assert "5 snapshots" in captured.out
        assert "1.2 MB" in captured.out
