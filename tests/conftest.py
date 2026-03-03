"""Pytest configuration and fixtures for d4-snap tests"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
import sys
import os

# Add the parent directory to the path so we can import d4_snap
sys.path.insert(0, str(Path(__file__).parent.parent))

# Also add the src directory to the path so we can import d4_snap
src_dir = str(Path(__file__).parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_git_repo(temp_dir):
    """Create a mock git repository"""
    repo_dir = temp_dir / "test_repo"
    repo_dir.mkdir()

    # Initialize git repo
    import subprocess

    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_dir, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        capture_output=True,
    )

    # Create a test file
    test_file = repo_dir / "test.txt"
    test_file.write_text("Initial content")
    subprocess.run(["git", "add", "test.txt"], cwd=repo_dir, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"], cwd=repo_dir, capture_output=True
    )

    return repo_dir


@pytest.fixture
def mock_config_file(temp_dir):
    """Create a mock config file"""
    config_dir = temp_dir / "config"
    config_dir.mkdir()
    config_file = config_dir / "d4_snap.yaml"
    config_file.write_text("""
main_menu:
  title: "Test Menu"
  options:
    - "1. Test Option"
  prompt: "Choose: "

save_snapshot:
  title: "Test Save"
  saving: "Saving..."
  success: "Success! {hash}"
  no_changes: "No changes"
""")
    return config_file


@pytest.fixture
def mock_checkpoint_dir(temp_dir):
    """Create a mock checkpoint directory"""
    checkpoint_dir = temp_dir / ".d4_snap"
    checkpoint_dir.mkdir()
    return checkpoint_dir


@pytest.fixture
def mock_menu_manager(mock_config_file):
    """Create a mock MenuManager instance"""
    from d4_snap.menu import MenuManager

    return MenuManager(mock_config_file)


@pytest.fixture
def mock_snapshot_manager():
    """Create a mock SnapshotManager instance"""
    from d4_snap.snapshot_manager import SnapshotManager

    return Mock(spec=SnapshotManager)


@pytest.fixture
def mock_git_operations():
    """Create a mock GitOperations instance"""
    from d4_snap.git_operations import GitOperations

    return Mock(spec=GitOperations)


@pytest.fixture
def mock_ui():
    """Create a mock UI instance"""
    from d4_snap.ui import UserInterface
    from unittest.mock import Mock

    ui_mock = Mock(spec=UserInterface)
    # Add the menu_mgr attribute that the tests expect
    ui_mock.menu_mgr = Mock()
    return ui_mock
