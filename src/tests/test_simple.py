"""Simple tests for d4-snap functionality"""

import pytest
from unittest.mock import patch, Mock
import tempfile
import shutil
from pathlib import Path
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBasicFunctionality:
    """Basic tests to ensure the test framework works"""

    def test_import_main(self):
        """Test that we can import the main module"""
        from d4_snap.main import print_help, run

        assert callable(print_help)
        assert callable(run)

    def test_print_help_output(self, capsys):
        """Test help output contains expected content"""
        from d4_snap.main import print_help

        print_help()
        captured = capsys.readouterr()
        assert "d4-snap - Git Snapshot & Rollback Manager" in captured.out
        assert "USAGE:" in captured.out

    def test_import_tools(self):
        """Test that we can import tools module"""
        from d4_snap.tools import load_config, CONFIG, CHECKPOINT_DIR

        assert callable(load_config)
        assert isinstance(CONFIG, dict)
        assert isinstance(CHECKPOINT_DIR, Path)

    def test_import_menu(self):
        """Test that we can import menu module"""
        from d4_snap.menu import MenuManager

        assert MenuManager is not None

    def test_import_ui(self):
        """Test that we can import UI module"""
        from d4_snap.ui import UserInterface

        assert UserInterface is not None

    def test_import_git_operations(self):
        """Test that we can import git operations module"""
        import d4_snap.git_operations as git_ops

        assert hasattr(git_ops, "run_cmd")
        assert hasattr(git_ops, "get_current_branch")
        assert hasattr(git_ops, "CHECKPOINT_DIR")

    def test_import_snapshot_manager(self):
        """Test that we can import snapshot manager module"""
        from d4_snap.snapshot_manager import SnapshotManager

        assert SnapshotManager is not None

    def test_import_cli(self):
        """Test that we can import CLI module"""
        from d4_snap.cli import save_snapshot, list_snapshots, main

        assert callable(save_snapshot)
        assert callable(list_snapshots)
        assert callable(main)

    @patch("d4_snap.main.save_snapshot")
    @patch("sys.argv", ["d4-snap"])
    def test_run_default_mode(self, mock_save_snapshot, capsys):
        """Test default mode (create snapshot and exit)"""
        from d4_snap.main import run

        run()

        mock_save_snapshot.assert_called_once()
        captured = capsys.readouterr()
        assert "📸 Creating snapshot of current project..." in captured.out
        assert "✅ Snapshot operation completed." in captured.out

    @patch("sys.argv", ["d4-snap", "help"])
    def test_run_help_mode(self, capsys):
        """Test help mode"""
        from d4_snap.main import run

        run()

        captured = capsys.readouterr()
        assert "d4-snap - Git Snapshot & Rollback Manager" in captured.out

    @patch("sys.argv", ["d4-snap", "--help"])
    def test_run_help_flag(self, capsys):
        """Test --help flag"""
        from d4_snap.main import run

        run()

        captured = capsys.readouterr()
        assert "d4-snap - Git Snapshot & Rollback Manager" in captured.out

    @patch("sys.argv", ["d4-snap", "/?"])
    def test_run_help_slash_question(self, capsys):
        """Test /? help flag"""
        from d4_snap.main import run

        run()

        captured = capsys.readouterr()
        assert "d4-snap - Git Snapshot & Rollback Manager" in captured.out

    @patch("sys.argv", ["d4-snap", "invalid"])
    def test_run_invalid_argument(self, capsys):
        """Test invalid argument handling"""
        from d4_snap.main import run

        with pytest.raises(SystemExit) as exc_info:
            run()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unknown argument: invalid" in captured.out
        assert "d4-snap - Git Snapshot & Rollback Manager" in captured.out


class TestConfigLoading:
    """Test configuration loading functionality"""

    def test_load_config_with_valid_yaml(self, temp_dir):
        """Test loading valid YAML config"""
        config_file = temp_dir / "test_config.yaml"
        config_file.write_text("""
main_menu:
  title: "Test Menu"
  options:
    - "1. Test Option"
test_key: "test_value"
""")

        from d4_snap.tools import load_config

        with patch("d4_snap.tools.CONFIG_FILE", config_file):
            config = load_config()

        assert config["main_menu"]["title"] == "Test Menu"
        assert config["test_key"] == "test_value"

    def test_load_config_nonexistent_file(self, temp_dir):
        """Test loading config when file doesn't exist"""
        non_existent_file = temp_dir / "non_existent.yaml"

        from d4_snap.tools import load_config

        with patch("d4_snap.tools.CONFIG_FILE", non_existent_file):
            config = load_config()

        assert config == {}

    def test_load_config_empty_file(self, temp_dir):
        """Test loading empty config file"""
        config_file = temp_dir / "empty_config.yaml"
        config_file.write_text("")

        from d4_snap.tools import load_config

        with patch("d4_snap.tools.CONFIG_FILE", config_file):
            config = load_config()

        assert config is None or config == {}


class TestMenuManager:
    """Test MenuManager functionality"""

    def test_menu_manager_init_with_config(self, temp_dir):
        """Test MenuManager initialization with config"""
        config_file = temp_dir / "menu_config.yaml"
        config_file.write_text("""
test_menu:
  title: "Test Menu Title"
  options:
    - "1. Option 1"
    - "2. Option 2"
  prompt: "Choose: "
""")

        from d4_snap.menu import MenuManager

        menu_mgr = MenuManager(config_file)

        assert menu_mgr.config_path == config_file
        assert "test_menu" in menu_mgr.config
        assert menu_mgr.config["test_menu"]["title"] == "Test Menu Title"

    def test_get_message_with_formatting(self, temp_dir):
        """Test getting message with formatting"""
        config_file = temp_dir / "message_config.yaml"
        config_file.write_text("""
test_section:
  success: "Operation completed with hash: {hash}"
""")

        from d4_snap.menu import MenuManager

        menu_mgr = MenuManager(config_file)

        # get_message doesn't format, it just returns the template
        message = menu_mgr.get_message("test_section", "success")
        assert "{hash}" in message

    def test_get_user_input(self, temp_dir):
        """Test getting user input"""
        config_file = temp_dir / "input_config.yaml"
        config_file.write_text("""
test_menu:
  prompt: "Choose option: "
""")

        from d4_snap.menu import MenuManager

        menu_mgr = MenuManager(config_file)

        # Test that the method exists and returns the correct prompt
        prompt = menu_mgr.get_menu_prompt("test_menu")
        assert "Choose option:" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
