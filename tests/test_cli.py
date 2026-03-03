"""Tests for cli.py module"""

from unittest.mock import patch, Mock

from d4_snap.cli import save_snapshot, list_snapshots, main


class TestCLI:
    """Test cases for CLI functions"""

    @patch("d4_snap.cli.get_ui")
    @patch("d4_snap.cli.get_snapshot_manager")
    def test_save_snapshot_success(self, mock_snap_mgr, mock_ui):
        """Test successful snapshot save"""
        # Setup mocks
        mock_ui_instance = Mock()
        mock_snap_mgr_instance = Mock()
        mock_ui.return_value = mock_ui_instance
        mock_snap_mgr.return_value = mock_snap_mgr_instance

        # Mock successful snapshot creation
        mock_snap_mgr_instance.create_snapshot.return_value = {
            "success": True,
            "hash": "abc12345",
        }

        # Call the function
        save_snapshot()

        # Verify calls
        mock_ui_instance.display_title.assert_called_once_with("save_snapshot")
        assert mock_ui_instance.display_message.call_count == 2
        mock_snap_mgr_instance.create_snapshot.assert_called_once()

    @patch("d4_snap.cli.get_ui")
    @patch("d4_snap.cli.get_snapshot_manager")
    def test_save_snapshot_no_changes(self, mock_snap_mgr, mock_ui):
        """Test snapshot save with no changes"""
        mock_ui_instance = Mock()
        mock_snap_mgr_instance = Mock()
        mock_ui.return_value = mock_ui_instance
        mock_snap_mgr.return_value = mock_snap_mgr_instance

        # Mock no changes scenario
        mock_snap_mgr_instance.create_snapshot.return_value = {
            "success": False,
            "message": "No changes to save",
        }

        save_snapshot()

        mock_ui_instance.display_message.assert_called()

    @patch("d4_snap.cli.get_ui")
    @patch("d4_snap.cli.get_snapshot_manager")
    def test_list_snapshots_with_data(self, mock_snap_mgr, mock_ui):
        """Test listing snapshots with data"""
        mock_ui_instance = Mock()
        mock_snap_mgr_instance = Mock()
        mock_ui.return_value = mock_ui_instance
        mock_snap_mgr.return_value = mock_snap_mgr_instance

        # Mock snapshot data
        mock_snapshots = [
            {"hash": "abc123", "description": "Test snapshot"},
            {"hash": "def456", "description": "Another snapshot"},
        ]
        mock_snap_mgr_instance.get_snapshots.return_value = mock_snapshots

        result = list_snapshots()

        assert result == mock_snapshots
        mock_ui_instance.display_snapshots.assert_called_once_with(
            mock_snapshots, False
        )

    @patch("d4_snap.cli.get_ui")
    @patch("d4_snap.cli.get_snapshot_manager")
    def test_list_snapshots_empty(self, mock_snap_mgr, mock_ui):
        """Test listing snapshots when empty"""
        mock_ui_instance = Mock()
        mock_snap_mgr_instance = Mock()
        mock_ui.return_value = mock_ui_instance
        mock_snap_mgr.return_value = mock_snap_mgr_instance

        mock_snap_mgr_instance.get_snapshots.return_value = []

        result = list_snapshots()

        assert result == []
        mock_ui_instance.display_message.assert_called_once()

    @patch("d4_snap.cli.get_menu_manager")
    def test_main_loop_exit(self, mock_menu_mgr):
        """Test main loop exit"""
        mock_menu_mgr_instance = Mock()
        mock_menu_mgr.return_value = mock_menu_mgr_instance

        # Mock user choosing to exit
        mock_menu_mgr_instance.display_and_get_choice.return_value = "0"

        with patch("d4_snap.cli.save_snapshot"):
            main()

        mock_menu_mgr_instance.print_message.assert_called_once_with(
            "messages", "goodbye"
        )

    @patch("d4_snap.cli.get_menu_manager")
    def test_main_loop_save_option(self, mock_menu_mgr):
        """Test main loop save option"""
        mock_menu_mgr_instance = Mock()
        mock_menu_mgr.return_value = mock_menu_mgr_instance

        # Mock user choosing save, then exit
        mock_menu_mgr_instance.display_and_get_choice.side_effect = ["1", "0"]

        with patch("d4_snap.cli.save_snapshot") as mock_save:
            main()

        mock_save.assert_called_once()

    @patch("d4_snap.cli.get_menu_manager")
    def test_main_loop_invalid_choice(self, mock_menu_mgr):
        """Test main loop invalid choice handling"""
        mock_menu_mgr_instance = Mock()
        mock_menu_mgr.return_value = mock_menu_mgr_instance

        # Mock invalid choice, then exit
        mock_menu_mgr_instance.display_and_get_choice.side_effect = ["invalid", "0"]

        with patch("d4_snap.cli.save_snapshot"):
            main()

        mock_menu_mgr_instance.print_message.assert_any_call(
            "messages", "invalid_choice"
        )
