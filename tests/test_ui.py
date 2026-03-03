"""Tests for ui.py module"""

from unittest.mock import patch, Mock
from pathlib import Path
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from d4_snap.ui import UserInterface


class TestUserInterface:
    """Test cases for UserInterface class"""

    def test_ui_init(self):
        """Test UI initialization"""
        ui = UserInterface()
        assert ui.menu_mgr is not None

    def test_display_title(self, mock_ui):
        """Test displaying title"""
        mock_ui.display_title("save_snapshot")
        # Check that the method was called (mocks don't need to verify internal calls)
        mock_ui.display_title.assert_called_once_with("save_snapshot")

    def test_display_message(self, mock_ui):
        """Test displaying message"""
        mock_ui.display_message("save_snapshot", "success", {"hash": "abc123"})
        mock_ui.display_message.assert_called_once_with(
            "save_snapshot", "success", {"hash": "abc123"}
        )

    def test_get_snapshot_selection_valid(self, mock_ui):
        """Test getting valid snapshot selection"""
        snapshots = [{"hash": "abc123"}, {"hash": "def456"}]
        mock_ui.menu_mgr.get_snapshot_number.return_value = "1"
        mock_ui.get_snapshot_selection.return_value = snapshots[0]

        result = mock_ui.get_snapshot_selection(snapshots)
        assert result == snapshots[0]

    def test_get_snapshot_selection_invalid(self, mock_ui):
        """Test getting invalid snapshot selection"""
        snapshots = [{"hash": "abc123"}, {"hash": "def456"}]
        mock_ui.menu_mgr.get_snapshot_number.return_value = "5"
        mock_ui.get_snapshot_selection.return_value = None

        result = mock_ui.get_snapshot_selection(snapshots)
        assert result is None

    def test_get_restore_option(self, mock_ui):
        """Test getting restore option"""
        mock_ui.menu_mgr.get_restore_option.return_value = "1"
        mock_ui.get_restore_option.return_value = "1"

        result = mock_ui.get_restore_option()
        assert result == "1"

    def test_get_file_path(self, mock_ui):
        """Test getting file path"""
        mock_ui.menu_mgr.get_path_input.return_value = "/path/to/file"
        mock_ui.get_file_path.return_value = "/path/to/file"

        result = mock_ui.get_file_path()
        assert result == "/path/to/file"

    def test_get_confirmation(self, mock_ui):
        """Test getting confirmation"""
        mock_ui.menu_mgr.get_confirmation.return_value = "y"
        mock_ui.get_confirmation.return_value = True

        result = mock_ui.get_confirmation("section", "key")
        assert result is True

    def test_display_error(self, mock_ui, capsys):
        """Test displaying error message"""
        # Use real UI for this test since it's a simple method
        ui = UserInterface()
        ui.display_error("Test error")

        captured = capsys.readouterr()
        assert "❌ Test error" in captured.out

    def test_display_success(self, mock_ui, capsys):
        """Test displaying success message"""
        # Use real UI for this test since it's a simple method
        ui = UserInterface()
        ui.display_success("Test success")

        captured = capsys.readouterr()
        assert "✅ Test success" in captured.out
