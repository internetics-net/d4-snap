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

# --- Shadow Git Checkpoints Config ---
CHECKPOINT_DIR = Path.home() / ".d4_snap" / ".d4_snap"


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
    return result


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
    abs_path = os.path.abspath(path)

    for member in tar.getmembers():
        member_path = os.path.abspath(os.path.join(abs_path, member.name))

        if not member_path.startswith(abs_path + os.sep) and member_path != abs_path:
            raise RuntimeError(f"Path traversal detected in tar: {member.name}")

        if member.islnk() or member.issym():
            link_target = member.linkname
            target_path = os.path.abspath(
                os.path.join(os.path.dirname(member_path), link_target)
            )
            if (
                not target_path.startswith(abs_path + os.sep)
                and target_path != abs_path
            ):
                raise RuntimeError(
                    f"Symlink escape detected in tar: {member.name} -> {link_target}"
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
    return {"favorite": False, "ai": False, "renamed": None, "deleted": False}


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
    result = run_shadow_cmd(
        ["show", f"{commit_hash}:{file_path}"],
        capture_output=True,
        check=False,
        quiet=True,
    )

    if result.returncode == 0:
        content = result.stdout
        if content is None:
            return False

        full_path = os.path.join(work_tree, file_path)
        try:
            atomic_write_file(full_path, content)
            return True
        except (OSError, TypeError):
            return False
    return False


def show_diff(commit_hash: str, path: Optional[str] = None) -> None:
    """Show diff between snapshot and current working directory"""
    if path:
        run_shadow_cmd(["diff", commit_hash, "--", path], check=False, quiet=False)
    else:
        run_shadow_cmd(["diff", commit_hash], check=False, quiet=False)


def cleanup_old_snapshots() -> None:
    """Cleanup snapshots older than 30 days (except favorites)"""
    run_shadow_cmd(
        ["reflog", "expire", "--expire=30.days", "refs/heads/master"], quiet=True
    )
    run_shadow_cmd(["gc", "--prune=30.days"], quiet=True)
