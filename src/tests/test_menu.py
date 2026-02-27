"""Tests for menu.py module"""

import pytest
from unittest.mock import patch, mock_open
import yaml
from pathlib import Path
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from d4_snap.menu import MenuManager


class TestMenuManager:
    """Test cases for MenuManager class"""

    def test_init_with_config_path(self, mock_config_file):
        """Test MenuManager initialization with config path"""
        menu_mgr = MenuManager(mock_config_file)

        assert menu_mgr.config_path == mock_config_file
        assert menu_mgr.config is not None
        assert "main_menu" in menu_mgr.config
        assert menu_mgr.config["main_menu"]["title"] == "Test Menu"

    def test_init_without_config_path(self):
        """Test MenuManager initialization without config path"""
        with patch("d4_snap.menu.Path") as mock_path:
            mock_path.return_value.parent / "config" / "d4_snap.yaml"

            with patch(
                "builtins.open", mock_open(read_data="main_menu:\n  title: Test")
            ):
                menu_mgr = MenuManager()
                assert menu_mgr.config is not None

    def test_load_config_file_exists(self, mock_config_file):
        """Test loading config when file exists"""
        menu_mgr = MenuManager(mock_config_file)
        config = menu_mgr._load_config()

        assert config["main_menu"]["title"] == "Test Menu"
        assert "options" in config["main_menu"]

    def test_load_config_file_not_exists(self, temp_dir):
        """Test loading config when file doesn't exist"""
        non_existent_file = temp_dir / "non_existent.yaml"
        menu_mgr = MenuManager(non_existent_file)
        config = menu_mgr._load_config()

        assert config == {}

    def test_reload_config(self, mock_config_file):
        """Test reloading config"""
        menu_mgr = MenuManager(mock_config_file)
        original_config = menu_mgr.config.copy()

        # Modify the file
        new_content = (
            "main_menu:\n  title: Updated Menu\n  options:\n    - '1. New Option'"
        )
        mock_config_file.write_text(new_content)

        menu_mgr.reload_config()

        assert menu_mgr.config["main_menu"]["title"] == "Updated Menu"
        assert menu_mgr.config != original_config

    def test_display_menu(self, mock_menu_manager, capsys):
        """Test displaying a menu"""
        mock_menu_manager.display_menu("main_menu")

        captured = capsys.readouterr()
        assert "Test Menu" in captured.out
        assert "1. Test Option" in captured.out
        assert "Choose:" in captured.out

    def test_display_menu_nonexistent(self, mock_menu_manager, capsys):
        """Test displaying a non-existent menu"""
        mock_menu_manager.display_menu("nonexistent_menu")

        captured = capsys.readouterr()
        assert "Menu 'nonexistent_menu' not found" in captured.out

    def test_get_user_input(self, mock_menu_manager):
        """Test getting user input"""
        with patch("builtins.input", return_value="1"):
            result = mock_menu_manager.get_user_input("main_menu")
            assert result == "1"

    def test_display_and_get_choice(self, mock_menu_manager):
        """Test displaying menu and getting choice"""
        with patch("builtins.input", return_value="1"):
            result = mock_menu_manager.display_and_get_choice("main_menu")
            assert result == "1"

    def test_get_message(self, mock_menu_manager):
        """Test getting a message"""
        message = mock_menu_manager.get_message(
            "save_snapshot", "success", {"hash": "abc123"}
        )
        assert "Success! abc123" in message

    def test_get_message_with_default(self, mock_menu_manager):
        """Test getting a message with default fallback"""
        message = mock_menu_manager.get_message(
            "nonexistent", "nonexistent", "Default message"
        )
        assert message == "Default message"

    def test_print_message(self, mock_menu_manager, capsys):
        """Test printing a message"""
        mock_menu_manager.print_message("save_snapshot", "success", {"hash": "abc123"})

        captured = capsys.readouterr()
        assert "Success! abc123" in captured.out

    def test_get_snapshot_number_valid(self, mock_menu_manager):
        """Test getting valid snapshot number"""
        with patch("builtins.input", return_value="3"):
            result = mock_menu_manager.get_snapshot_number()
            assert result == 3

    def test_get_snapshot_number_invalid_then_valid(self, mock_menu_manager):
        """Test getting snapshot number with invalid then valid input"""
        with patch("builtins.input", side_effect=["invalid", "3"]):
            result = mock_menu_manager.get_snapshot_number()
            assert result == 3

    def test_get_snapshot_number_cancel(self, mock_menu_manager):
        """Test canceling snapshot number input"""
        with patch("builtins.input", return_value=""):
            result = mock_menu_manager.get_snapshot_number()
            assert result is None

    def test_get_confirm_yes(self, mock_menu_manager):
        """Test getting confirmation with yes"""
        with patch("builtins.input", return_value="y"):
            result = mock_menu_manager.get_confirm("Continue?")
            assert result is True

    def test_get_confirm_no(self, mock_menu_manager):
        """Test getting confirmation with no"""
        with patch("builtins.input", return_value="n"):
            result = mock_menu_manager.get_confirm("Continue?")
            assert result is False

    def test_get_confirm_invalid_then_no(self, mock_menu_manager):
        """Test getting confirmation with invalid then no"""
        with patch("builtins.input", side_effect=["invalid", "n"]):
            result = mock_menu_manager.get_confirm("Continue?")
            assert result is False

    def test_get_text_input(self, mock_menu_manager):
        """Test getting text input"""
        with patch("builtins.input", return_value="Test input"):
            result = mock_menu_manager.get_text_input("Enter text:")
            assert result == "Test input"

    def test_get_text_input_empty(self, mock_menu_manager):
        """Test getting empty text input"""
        with patch("builtins.input", return_value=""):
            result = mock_menu_manager.get_text_input("Enter text:")
            assert result == ""

    def test_validate_choice_valid(self, mock_menu_manager):
        """Test validating a valid choice"""
        result = mock_menu_manager.validate_choice("1", ["1", "2", "3"])
        assert result is True

    def test_validate_choice_invalid(self, mock_menu_manager):
        """Test validating an invalid choice"""
        result = mock_menu_manager.validate_choice("5", ["1", "2", "3"])
        assert result is False

    def test_validate_choice_empty(self, mock_menu_manager):
        """Test validating empty choice"""
        result = mock_menu_manager.validate_choice("", ["1", "2", "3"])
        assert result is False
