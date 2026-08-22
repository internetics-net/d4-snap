"""Tests for git_operations.py module"""

import pytest
from unittest.mock import patch, Mock
import subprocess

from d4_snap.git_operations import GitOperations, run_cmd


class TestGitOperations:
    """Test cases for GitOperations class"""

    def test_git_operations_init(self, mock_checkpoint_dir):
        """Test GitOperations initialization"""
        git_ops = GitOperations(checkpoint_dir=mock_checkpoint_dir)
        assert git_ops.checkpoint_dir == mock_checkpoint_dir

    def test_get_repo_name_success(self, mock_git_repo, mock_checkpoint_dir):
        """Test getting repository name successfully"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.CHECKPOINT_DIR", mock_checkpoint_dir):
            with patch("d4_snap.git_operations.run_cmd") as mock_run_cmd:
                # Mock the git command to return our test repo path
                mock_run_cmd.return_value = Mock(
                    returncode=0, stdout=str(mock_git_repo)
                )

                repo_name = git_ops.get_repo_name()

                assert repo_name == "test_repo"

    def test_get_repo_name_no_git(self, temp_dir, mock_checkpoint_dir):
        """Test getting repository name when not in git repo"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="")
            repo_name = git_ops.get_repo_name()

            assert repo_name is None

    def test_get_repo_hash_success(self, mock_git_repo, mock_checkpoint_dir):
        """Test getting repository hash successfully"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.CHECKPOINT_DIR", mock_checkpoint_dir):
            with patch("d4_snap.git_operations.Path.cwd", return_value=mock_git_repo):
                repo_hash = git_ops.get_repo_hash()

                assert repo_hash is not None
                assert len(repo_hash) == 8  # Short hash length

    def test_get_repo_hash_no_git(self, temp_dir, mock_checkpoint_dir):
        """Test getting repository hash when not in git repo"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="")
            repo_hash = git_ops.get_repo_hash()

            assert repo_hash is None

    def test_init_bare_repo_success(self, mock_checkpoint_dir):
        """Test initializing bare repository successfully"""
        git_ops = GitOperations(checkpoint_dir=mock_checkpoint_dir)
        bare_repo_path = mock_checkpoint_dir / "test_repo-hash"

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = git_ops.init_bare_repo("test_repo-hash")

            assert result is True
            mock_run.assert_called_with(
                ["git", "init", "--bare", str(bare_repo_path)], quiet=True
            )

    def test_init_bare_repo_failure(self, mock_checkpoint_dir):
        """Test initializing bare repository with failure"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = git_ops.init_bare_repo("test_repo-hash")

            assert result is False

    def test_add_remote_success(self, mock_checkpoint_dir):
        """Test adding remote successfully"""
        git_ops = GitOperations()
        bare_repo_path = mock_checkpoint_dir / "test_repo-hash"

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = git_ops.add_remote("test_repo-hash", str(bare_repo_path))

            assert result is True
            mock_run.assert_called_with(
                ["git", "remote", "add", "shadow", str(bare_repo_path)], quiet=True
            )

    def test_add_remote_failure(self, mock_checkpoint_dir):
        """Test adding remote with failure"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = git_ops.add_remote("test_repo-hash", "/path/to/repo")

            assert result is False

    def test_push_to_shadow_success(self, mock_checkpoint_dir):
        """Test pushing to shadow repo successfully"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = git_ops.push_to_shadow("main")

            assert result is True
            mock_run.assert_called_with(["git", "push", "shadow", "main"], quiet=True)

    def test_push_to_shadow_failure(self, mock_checkpoint_dir):
        """Test pushing to shadow repo with failure"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = git_ops.push_to_shadow("main")

            assert result is False

    def test_create_shadow_branch_success(self, mock_checkpoint_dir):
        """Test creating shadow branch successfully"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = git_ops.create_shadow_branch("shadow-branch")

            assert result is True
            mock_run.assert_called_with(
                ["git", "checkout", "-b", "shadow-branch"], quiet=True
            )

    def test_create_shadow_branch_failure(self, mock_checkpoint_dir):
        """Test creating shadow branch with failure"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = git_ops.create_shadow_branch("shadow-branch")

            assert result is False

    def test_get_current_branch_success(self, mock_git_repo, mock_checkpoint_dir):
        """Test getting current branch successfully"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="main\n")

            result = git_ops.get_current_branch()

            assert result == "main"
            mock_run.assert_called_with(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                quiet=True,
                check=False,
            )

    def test_get_current_branch_failure(self, mock_checkpoint_dir):
        """Test getting current branch with failure"""
        git_ops = GitOperations()

        with patch("d4_snap.git_operations.run_cmd") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = git_ops.get_current_branch()

            assert result is None


class TestRunCmd:
    """Test cases for run_cmd function"""

    def test_run_cmd_success(self):
        """Test successful command execution"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="output")

            result = run_cmd(["echo", "test"])

            assert result.returncode == 0
            assert result.stdout == "output"
            mock_run.assert_called_once()

    def test_run_cmd_failure_with_check(self):
        """Test command failure with check=True"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            with pytest.raises(subprocess.CalledProcessError):
                run_cmd(["false"], check=True)

    def test_run_cmd_failure_without_check(self):
        """Test command failure with check=False"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = run_cmd(["false"], check=False)

            assert result.returncode == 1

    def test_run_cmd_capture_output(self):
        """Test command with capture_output=True"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="captured")

            result = run_cmd(["echo", "test"], capture_output=True)

            assert result.stdout == "captured"
            mock_run.assert_called_with(
                ["echo", "test"], text=True, capture_output=True
            )

    def test_run_cmd_quiet(self):
        """Test command with quiet=True"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = run_cmd(["echo", "test"], quiet=True)

            assert result.returncode == 0

    def test_run_cmd_binary(self):
        """Test command with binary=True"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=b"binary")

            result = run_cmd(["echo", "test"], binary=True)

            assert result.stdout == b"binary"
            mock_run.assert_called_with(
                ["echo", "test"], text=False, capture_output=False
            )


class TestStageWorktreeForSnapshot:
    """Tests for ignore-aware snapshot staging."""

    def test_stage_worktree_for_snapshot_unstages_gitignored(self):
        from d4_snap.git_operations import stage_worktree_for_snapshot

        with patch("d4_snap.git_operations.run_shadow_cmd") as mock_shadow:
            mock_shadow.side_effect = [
                Mock(returncode=0),  # add -A
                Mock(returncode=0, stdout=".venv/lib/site.py\n"),  # ls-files -ci
                Mock(
                    returncode=0, stdout="src/main.py\n.venv/lib/site.py\n"
                ),  # ls-files
                Mock(returncode=0),  # reset chunk
            ]
            with patch("d4_snap.git_operations.get_shadow_repo_path") as mock_paths:
                mock_paths.return_value = ("/shadow", "/work/tree")
                with patch("d4_snap.git_paths.gitignored_rel_paths") as mock_ignored:
                    mock_ignored.return_value = {".venv/lib/site.py"}
                    stage_worktree_for_snapshot()

            calls = [call.args[0] for call in mock_shadow.call_args_list]
            assert calls[0][:3] == ["add", "-A", "--ignore-errors"]
            assert calls[-1][0] == "reset"
            assert ".venv/lib/site.py" in calls[-1]
