"""Pytest configuration and fixtures for d4-snap tests"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import sys
import os

# Add the parent directory to the path so we can import d4_snap
sys.path.insert(0, str(Path(__file__).parent.parent))


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
