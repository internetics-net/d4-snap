"""
Git operations module - low-level git commands and shadow repository management
"""

import os
import subprocess
import hashlib
import json
import sys
import tarfile
import io
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

from .path_safety import is_safe_relative_path, is_within_directory, resolve_under_root

# --- Shadow Git Checkpoints Config ---
# All snapshots live under ~/.d4/d4_snap/<repo-name>-<hash>/
CHECKPOINT_DIR = Path.home() / ".d4" / "d4_snap"


def run_cmd(
    cmd: List[str],
    check: bool = True,
    capture_output: bool = False,
    quiet: bool = False,
    binary: bool = False,
) -> subprocess.CompletedProcess:
    """Execute a shell command"""
    if not quiet:
        print(f"\n> {' '.join(cmd)}")

    result = None
    try:
        result = subprocess.run(cmd, text=not binary, capture_output=capture_output)
        if check and result.returncode != 0:
            if not quiet:
                print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
                if capture_output:
                    stderr = result.stderr
                    if stderr:
                        if isinstance(stderr, bytes):
                            stderr = stderr.decode("utf-8", errors="replace")
                        if stderr:
                            print(stderr, file=sys.stderr)
            # Raise CalledProcessError as expected by the test
            raise subprocess.CalledProcessError(
                result.returncode, cmd, output=result.stdout, stderr=result.stderr
            )
        return result
    except Exception:
        # Ensure proper cleanup if result was created
        if (
            result is not None
            and hasattr(result, "stdout")
            and isinstance(result.stdout, bytes)
        ):
            # Clean up any binary data if needed
            pass
        raise


def get_current_branch() -> str:
    """Get the current git branch name"""
    res = run_cmd(
        ["git", "branch", "--show-current"],
        capture_output=True,
        check=False,
        quiet=True,
    )
    return res.stdout.strip()


def get_repo_root() -> str:
    """Get the root directory of the current git repository"""
    res = run_cmd(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        check=False,
        quiet=True,
    )
    return res.stdout.strip() if res.returncode == 0 else os.getcwd()


def safe_extract_tar(tar: tarfile.TarFile, path: str) -> None:
    """
    Safely extract tar archive, preventing path traversal and symlink attacks.
    Raises RuntimeError if any member would escape the target path.
    """
    base = Path(path).resolve()

    for member in tar.getmembers():
        member_path = (base / member.name).resolve()
        if not is_within_directory(member_path, base):
            raise RuntimeError(f"Path traversal detected in tar: {member.name}")

        if member.islnk() or member.issym():
            link_target = Path(member.linkname)
            if link_target.is_absolute():
                target_path = link_target.resolve()
            else:
                target_path = (member_path.parent / member.linkname).resolve()
            if not is_within_directory(target_path, base):
                raise RuntimeError(
                    f"Symlink escape detected in tar: {member.name} -> {member.linkname}"
                )

    tar.extractall(path=path)


def atomic_write_file(file_path: str, content: Any) -> None:
    """
    Atomically write content to a file using a temporary file and os.replace.
    Handles both text (str) and binary (bytes) content.
    """
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)

    dir_path = os.path.dirname(file_path) or "."

    with tempfile.NamedTemporaryFile(dir=dir_path, delete=False, mode="wb") as tmp:
        if isinstance(content, str):
            tmp.write(content.encode("utf-8"))
        elif isinstance(content, bytes):
            tmp.write(content)
        else:
            raise TypeError(f"Content must be str or bytes, got {type(content)}")
        tmp_name = tmp.name

    try:
        os.replace(tmp_name, file_path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def get_shadow_repo_path() -> Tuple[str, str]:
    """Get the shadow repository path and work tree path"""
    repo_root = get_repo_root()
    repo_hash = hashlib.md5(repo_root.encode()).hexdigest()[:12]
    repo_name = os.path.basename(repo_root)
    shadow_path = CHECKPOINT_DIR / f"{repo_name}-{repo_hash}"
    return str(shadow_path), repo_root


def init_shadow_repo() -> str:
    """Initialize the shadow repository if it doesn't exist"""
    shadow_path, _ = get_shadow_repo_path()
    if not os.path.exists(shadow_path):
        os.makedirs(shadow_path, exist_ok=True)
        run_cmd(["git", "init", "--bare", shadow_path], quiet=True)
        run_shadow_cmd(["config", "notes.rewriteRef", "refs/notes/commits"], quiet=True)
    return shadow_path


def run_shadow_cmd(
    args: List[str],
    capture_output: bool = False,
    check: bool = True,
    quiet: bool = False,
    binary: bool = False,
) -> subprocess.CompletedProcess:
    """Execute a git command in the shadow repository"""
    shadow_path, work_tree = get_shadow_repo_path()
    cmd = ["git", f"--git-dir={shadow_path}", f"--work-tree={work_tree}"] + args
    return run_cmd(
        cmd, capture_output=capture_output, check=check, quiet=quiet, binary=binary
    )


def stage_worktree_for_snapshot() -> None:
    """Stage working-tree changes for a snapshot, respecting .gitignore."""
    from .git_paths import gitignored_rel_paths

    _, work_tree = get_shadow_repo_path()
    project_root = Path(work_tree).resolve()

    run_shadow_cmd(
        ["add", "-A", "--ignore-errors", "--", "."],
        quiet=True,
        check=False,
    )

    to_unstage: list[str] = []

    ignored_tracked = run_shadow_cmd(
        ["ls-files", "-ci", "--exclude-standard"],
        capture_output=True,
        check=False,
        quiet=True,
    )
    if ignored_tracked.returncode == 0 and ignored_tracked.stdout.strip():
        to_unstage.extend(
            normalize_rel_path(line)
            for line in ignored_tracked.stdout.splitlines()
            if line.strip()
        )

    indexed = run_shadow_cmd(
        ["ls-files"],
        capture_output=True,
        check=False,
        quiet=True,
    )
    if indexed.returncode == 0 and indexed.stdout.strip():
        indexed_paths = [
            normalize_rel_path(line)
            for line in indexed.stdout.splitlines()
            if line.strip()
        ]
        ignored_indexed = gitignored_rel_paths(project_root, indexed_paths)
        to_unstage.extend(p for p in indexed_paths if p in ignored_indexed)

    unique = sorted(set(to_unstage))
    if unique:
        chunk_size = 200
        for start in range(0, len(unique), chunk_size):
            run_shadow_cmd(
                ["reset", "--", *unique[start : start + chunk_size]],
                quiet=True,
                check=False,
            )


def normalize_rel_path(rel_path: str) -> str:
    return rel_path.replace("\\", "/").strip("/")


def get_snapshot_metadata(commit_hash: str) -> Dict[str, Any]:
    """Get metadata for a snapshot"""
    res = run_shadow_cmd(
        ["notes", "show", commit_hash], check=False, capture_output=True, quiet=True
    )
    if res.returncode == 0 and res.stdout.strip():
        try:
            return json.loads(res.stdout.strip())
        except json.JSONDecodeError:
            pass
    return {"favorite": False, "notes": "", "renamed": None, "deleted": False}


def set_snapshot_metadata(commit_hash: str, metadata: Dict[str, Any]) -> None:
    """Set metadata for a snapshot"""
    meta_str = json.dumps(metadata)
    run_shadow_cmd(["notes", "add", "-f", "-m", meta_str, commit_hash], quiet=True)


def create_tag(tag_name: str, commit_hash: str) -> None:
    """Create a git tag"""
    run_shadow_cmd(["tag", tag_name, commit_hash], check=False, quiet=True)


def delete_tag(tag_name: str) -> None:
    """Delete a git tag"""
    run_shadow_cmd(["tag", "-d", tag_name], check=False, quiet=True)


def get_commit_files(commit_hash: str) -> List[str]:
    """Get list of files in a commit"""
    ls_result = run_shadow_cmd(
        ["ls-tree", "-r", "--name-only", commit_hash],
        capture_output=True,
        check=False,
        quiet=True,
    )
    if ls_result.returncode == 0:
        return ls_result.stdout.strip().split("\n")
    return []


def extract_snapshot_archive(commit_hash: str, work_tree: str) -> bool:
    """Extract entire snapshot to work tree"""
    result = run_shadow_cmd(
        ["archive", "--format=tar", commit_hash],
        capture_output=True,
        check=False,
        quiet=True,
        binary=True,
    )

    if result.returncode == 0 and result.stdout:
        tar_data = result.stdout
        if not tar_data:
            return False

        try:
            with tarfile.open(fileobj=io.BytesIO(tar_data), mode="r:*") as tar:
                safe_extract_tar(tar, work_tree)
            return True
        except (tarfile.TarError, RuntimeError):
            return False
    return False


def extract_file_from_snapshot(
    commit_hash: str, file_path: str, work_tree: str
) -> bool:
    """Extract a specific file from snapshot"""
    resolved = resolve_under_root(Path(work_tree), file_path)
    if resolved is None:
        return False

    safe_path = resolved.relative_to(Path(work_tree).resolve()).as_posix()
    result = run_shadow_cmd(
        ["show", f"{commit_hash}:{safe_path}"],
        capture_output=True,
        check=False,
        quiet=True,
    )

    if result.returncode == 0:
        content = result.stdout
        if content is None:
            return False

        try:
            atomic_write_file(str(resolved), content)
            return True
        except (OSError, TypeError):
            return False
    return False


def show_diff(commit_hash: str, path: Optional[str] = None) -> None:
    """Show diff between snapshot and current working directory"""
    if path:
        if not is_safe_relative_path(path):
            return
        run_shadow_cmd(["diff", commit_hash, "--", path], check=False, quiet=False)
    else:
        run_shadow_cmd(["diff", commit_hash], check=False, quiet=False)


def get_shadow_current_branch() -> Optional[str]:
    """Get the current branch from the shadow repository"""
    try:
        result = run_shadow_cmd(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            quiet=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (OSError, subprocess.SubprocessError):
        return None


def cleanup_old_snapshots() -> None:
    """Cleanup snapshots older than 30 days (except favorites)"""
    # Get current branch from shadow repository instead of main repo
    try:
        current_branch = get_shadow_current_branch()
        if not current_branch:
            current_branch = "master"  # fallback
    except (OSError, subprocess.SubprocessError):
        current_branch = "master"  # fallback

    ref_name = f"refs/heads/{current_branch}"
    try:
        run_shadow_cmd(["reflog", "expire", "--expire=30.days", ref_name], quiet=True)
    except subprocess.CalledProcessError:
        # Reflog might not exist, which is fine for new repositories
        pass

    try:
        run_shadow_cmd(["gc", "--prune=30.days"], quiet=True)
    except subprocess.CalledProcessError:
        # GC might fail if there's nothing to clean up
        pass


def cleanup_very_old_snapshots(days: int = 90) -> None:
    """Cleanup snapshots older than specified days (except favorites)"""
    # Validate days parameter
    if not isinstance(days, int) or days <= 0:
        raise ValueError(f"Invalid cleanup days: {days}. Must be a positive integer.")

    # Get current branch from shadow repository instead of main repo
    try:
        current_branch = get_shadow_current_branch()
        if not current_branch:
            current_branch = "master"  # fallback
    except (OSError, subprocess.SubprocessError):
        current_branch = "master"  # fallback

    ref_name = f"refs/heads/{current_branch}"
    try:
        run_shadow_cmd(
            ["reflog", "expire", f"--expire={days}.days", ref_name], quiet=True
        )
    except subprocess.CalledProcessError:
        # Reflog might not exist, which is fine for new repositories
        pass

    try:
        run_shadow_cmd(["gc", f"--prune={days}.days"], quiet=True)
    except subprocess.CalledProcessError:
        # GC might fail if there's nothing to clean up
        pass


class GitOperations:
    """Git operations class providing a high-level interface to git operations."""

    def __init__(self, checkpoint_dir: Optional[Path] = None):
        """Initialize GitOperations with optional checkpoint directory."""
        # Use the provided checkpoint_dir or fall back to the default
        self.checkpoint_dir = (
            checkpoint_dir if checkpoint_dir is not None else CHECKPOINT_DIR
        )

    def get_repo_name(self) -> Optional[str]:
        """Get the repository name from current directory."""
        try:
            result = run_cmd(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                check=False,
                quiet=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return os.path.basename(result.stdout.strip())
            return None
        except (OSError, subprocess.SubprocessError):
            return None

    def get_repo_hash(self) -> Optional[str]:
        """Get a short hash for the repository."""
        try:
            result = run_cmd(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                check=False,
                quiet=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                repo_root = result.stdout.strip()
                return hashlib.md5(repo_root.encode()).hexdigest()[:8]
            return None
        except (OSError, subprocess.SubprocessError):
            return None

    def init_bare_repo(self, repo_name: str) -> bool:
        """Initialize a bare repository."""
        try:
            bare_repo_path = self.checkpoint_dir / repo_name
            result = run_cmd(["git", "init", "--bare", str(bare_repo_path)], quiet=True)
            return result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def add_remote(self, repo_name: str, remote_path: str) -> bool:
        """Add a remote repository."""
        try:
            result = run_cmd(
                ["git", "remote", "add", "shadow", remote_path], quiet=True
            )
            return result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def push_to_shadow(self, branch: str = "main") -> bool:
        """Push current branch to shadow repository."""
        try:
            result = run_cmd(["git", "push", "shadow", branch], quiet=True)
            return result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def create_shadow_branch(self, branch_name: str) -> bool:
        """Create a new branch for shadow operations."""
        try:
            result = run_cmd(["git", "checkout", "-b", branch_name], quiet=True)
            return result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def get_current_branch(self) -> Optional[str]:
        """Get the current git branch name."""
        try:
            result = run_cmd(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                quiet=True,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (OSError, subprocess.SubprocessError):
            return None
