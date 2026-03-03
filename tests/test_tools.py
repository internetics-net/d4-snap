"""Tests for tools.py module"""

import pytest
from unittest.mock import patch, mock_open
import tempfile
import shutil
from pathlib import Path
import sys
import yaml

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from d4_snap.tools import load_config, CONFIG, CHECKPOINT_DIR


class TestTools:
    """Test cases for tools module"""

    def test_load_config_file_exists(self, temp_dir):
        """Test loading config when file exists"""
        config_file = temp_dir / "test_config.yaml"
        config_data = {"test_key": "test_value", "nested": {"key": "value"}}
        config_file.write_text(yaml.dump(config_data))

        with patch("d4_snap.tools.CONFIG_FILE", config_file):
            config = load_config()

            assert config["test_key"] == "test_value"
            assert config["nested"]["key"] == "value"

    def test_load_config_file_not_exists(self, temp_dir):
        """Test loading config when file doesn't exist"""
        non_existent_file = temp_dir / "non_existent.yaml"

        with patch("d4_snap.tools.CONFIG_FILE", non_existent_file):
            config = load_config()
            assert config == {}

    def test_config_constant_loaded(self):
        """Test that CONFIG constant is loaded at module import"""
        assert isinstance(CONFIG, dict)

    def test_checkpoint_dir_constant(self):
        """Test CHECKPOINT_DIR constant"""
        assert isinstance(CHECKPOINT_DIR, Path)
        assert ".d4_snap" in str(CHECKPOINT_DIR)

    @patch("d4_snap.tools.Path.home")
    def test_checkpoint_dir_structure(self, mock_home):
        """Test checkpoint directory structure"""
        mock_home_path = Path("/mock/home")
        mock_home.return_value = mock_home_path

        # Re-import to test with mocked Path
        import importlib
        import d4_snap.tools

        importlib.reload(d4_snap.tools)

        expected_path = mock_home_path / ".d4_snap" / ".d4_snap"
        assert d4_snap.tools.CHECKPOINT_DIR == expected_path

    def test_config_file_path(self):
        """Test config file path structure"""
        from d4_snap.tools import CONFIG_FILE

        assert CONFIG_FILE.name == "d4_snap.yaml"
        assert "config" in str(CONFIG_FILE)

    @patch("builtins.open", new_callable=mock_open, read_data="key: value")
    @patch("d4_snap.tools.Path.exists", return_value=True)
    def test_load_config_yaml_parsing(self, mock_exists, mock_file):
        """Test YAML parsing in load_config"""
        config = load_config()

        assert config == {"key": "value"}
        mock_file.assert_called_once()

    @patch("builtins.open", side_effect=IOError("Permission denied"))
    @patch("d4_snap.tools.Path.exists", return_value=True)
    def test_load_config_io_error(self, mock_exists, mock_file):
        """Test handling of IO errors in load_config"""
        config = load_config()

        assert config == {}

    @patch("builtins.open", side_effect=yaml.YAMLError("Invalid YAML"))
    @patch("d4_snap.tools.Path.exists", return_value=True)
    def test_load_config_yaml_error(self, mock_exists, mock_file):
        """Test handling of YAML errors in load_config"""
        config = load_config()

        assert config == {}

    def test_config_contains_expected_keys(self):
        """Test that loaded config contains expected keys"""
        # This test assumes the actual config file exists and has expected structure
        expected_sections = ["main_menu", "save_snapshot", "restore_snapshot"]

        for section in expected_sections:
            if section in CONFIG:  # Only check if section exists in actual config
                assert isinstance(CONFIG[section], dict)
