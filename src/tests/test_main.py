"""Tests for main.py module"""

import pytest
from unittest.mock import patch, Mock
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from d4_snap.main import print_help, run


class TestMain:
    """Test cases for main module"""

    def test_print_help(self, capsys):
        """Test help output"""
        print_help()
        captured = capsys.readouterr()

        assert "d4-snap - Git Snapshot & Rollback Manager" in captured.out
        assert "USAGE:" in captured.out
        assert (
            "d4-snap                    Create a snapshot of current project and exit"
            in captured.out
        )
        assert "d4-snap menu               Show interactive menu" in captured.out
        assert "d4-snap help               Show this help message" in captured.out
        assert "d4-snap --help             Show this help message" in captured.out
        assert "d4-snap /?                 Show this help message" in captured.out

    @patch("d4_snap.main.save_snapshot")
    @patch("sys.argv", ["d4-snap"])
    def test_run_default_mode(self, mock_save_snapshot, capsys):
        """Test default mode (create snapshot and exit)"""
        run()

        mock_save_snapshot.assert_called_once()
        captured = capsys.readouterr()
        assert "📸 Creating snapshot of current project..." in captured.out
        assert "✅ Snapshot operation completed." in captured.out

    @patch("d4_snap.main.main")
    @patch("sys.argv", ["d4-snap", "menu"])
    def test_run_menu_mode(self, mock_main):
        """Test menu mode"""
        run()

        mock_main.assert_called_once()

    @patch("sys.argv", ["d4-snap", "help"])
    def test_run_help_mode(self, capsys):
        """Test help mode"""
        run()

        captured = capsys.readouterr()
        assert "d4-snap - Git Snapshot & Rollback Manager" in captured.out

    @patch("sys.argv", ["d4-snap", "--help"])
    def test_run_help_flag(self, capsys):
        """Test --help flag"""
        run()

        captured = capsys.readouterr()
        assert "d4-snap - Git Snapshot & Rollback Manager" in captured.out

    @patch("sys.argv", ["d4-snap", "/?"])
    def test_run_help_slash_question(self, capsys):
        """Test /? help flag"""
        run()

        captured = capsys.readouterr()
        assert "d4-snap - Git Snapshot & Rollback Manager" in captured.out

    @patch("sys.argv", ["d4-snap", "invalid"])
    def test_run_invalid_argument(self, capsys):
        """Test invalid argument handling"""
        with pytest.raises(SystemExit) as exc_info:
            run()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unknown argument: invalid" in captured.out
        assert "d4-snap - Git Snapshot & Rollback Manager" in captured.out

    @patch("d4_snap.main.save_snapshot")
    @patch("sys.argv", ["d4-snap"])
    def test_run_keyboard_interrupt(self, mock_save_snapshot, capsys):
        """Test keyboard interrupt handling"""
        mock_save_snapshot.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            run()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Interrupted by user. Exiting..." in captured.out

    @patch("d4_snap.main.save_snapshot")
    @patch("sys.argv", ["d4-snap"])
    def test_run_exception_handling(self, mock_save_snapshot, capsys):
        """Test general exception handling"""
        mock_save_snapshot.side_effect = Exception("Test error")

        with pytest.raises(SystemExit) as exc_info:
            run()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌ Unexpected error: Test error" in captured.out
        assert "Traceback" in captured.out
