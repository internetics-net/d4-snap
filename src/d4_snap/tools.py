# src/d4_crc/tools.py
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import uuid

import yaml

# --- Shadow Git Checkpoints Config ---
CHECKPOINT_DIR = Path.home() / ".d4_snap" / ".d4_snap"
CONFIG_FILE = Path(__file__).parent / "config" / "d4_snap.yaml"


def load_config():
    """Load configuration from YAML file with error handling"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config is None:
                    return {}
                return config
        else:
            # Config file doesn't exist, return empty dict
            return {}
    except (IOError, yaml.YAMLError) as e:
        # Log the error but don't crash the application
        print(f"⚠️  Warning: Failed to load config file {CONFIG_FILE}: {e}")
        return {}


CONFIG = load_config()
# -------------------------------------


def run_cmd(cmd, check=True, capture_output=False, quiet=False, binary=False):
    """Execute shell command with proper error handling"""
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
        # Raise CalledProcessError as expected by the test
        raise subprocess.CalledProcessError(
            result.returncode, cmd, output=result.stdout, stderr=result.stderr
        )
    return result


def get_current_branch():
    res = run_cmd(
        ["git", "branch", "--show-current"],
        capture_output=True,
        check=False,
        quiet=True,
    )
    return res.stdout.strip()


def get_repo_root():
    res = run_cmd(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        check=False,
        quiet=True,
    )
    return res.stdout.strip() if res.returncode == 0 else os.getcwd()


# --- Helper Functions for Security and Atomicity ---


def _safe_extract_tar(tar, path):
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


def _atomic_write_file(file_path, content):
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


# --- Shadow Checkpoints Implementation ---


def get_shadow_repo_path():
    repo_root = get_repo_root()
    repo_hash = hashlib.md5(repo_root.encode()).hexdigest()[:12]
    repo_name = os.path.basename(repo_root)
    shadow_path = CHECKPOINT_DIR / f"{repo_name}-{repo_hash}"
    return str(shadow_path), repo_root


def init_shadow_repo():
    shadow_path, _ = get_shadow_repo_path()
    if not os.path.exists(shadow_path):
        os.makedirs(shadow_path, exist_ok=True)
        run_cmd(["git", "init", "--bare", shadow_path], quiet=True)
        run_shadow_cmd(["config", "notes.rewriteRef", "refs/notes/commits"], quiet=True)
    return shadow_path


def run_shadow_cmd(args, capture_output=False, check=True, quiet=False, binary=False):
    shadow_path, work_tree = get_shadow_repo_path()
    cmd = ["git", f"--git-dir={shadow_path}", f"--work-tree={work_tree}"] + args
    return run_cmd(
        cmd, capture_output=capture_output, check=check, quiet=quiet, binary=binary
    )


def get_snapshot_metadata(commit_hash):
    res = run_shadow_cmd(
        ["notes", "show", commit_hash], check=False, capture_output=True, quiet=True
    )
    if res.returncode == 0 and res.stdout.strip():
        try:
            return json.loads(res.stdout.strip())
        except json.JSONDecodeError:
            pass
    return {"favorite": False, "notes": "", "renamed": None, "deleted": False}


def set_snapshot_metadata(commit_hash, metadata):
    meta_str = json.dumps(metadata)
    run_shadow_cmd(["notes", "add", "-f", "-m", meta_str, commit_hash], quiet=True)


def save_snapshot(is_claude=False):
    msgs = CONFIG.get("save_snapshot", {})
    print(msgs.get("title", "\n--- Save Work Snapshot (Shadow Repo) ---"))
    init_shadow_repo()
    branch = get_current_branch() or "unknown-branch"

    now = datetime.now(timezone.utc)
    timestamp_name = now.strftime("%Y%m%d-%H%M%S%f")[:17] + f"_{uuid.uuid4().hex[:6]}"
    name = timestamp_name
    if is_claude:
        name = f"Claude-{timestamp_name}"

    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    commit_msg = f"{name}\n\nBranch: {branch}\nTimestamp: {timestamp}"

    print(msgs.get("saving", "Saving snapshot."))
    run_shadow_cmd(["add", "."], quiet=True)

    res = run_shadow_cmd(
        ["commit", "-m", commit_msg], check=False, capture_output=True, quiet=True
    )

    if "nothing to commit" in res.stdout or "nothing to commit" in res.stderr:
        print(msgs.get("no_changes", "No changes to save."))
    else:
        commit_hash = run_shadow_cmd(
            ["rev-parse", "HEAD"], capture_output=True, quiet=True
        ).stdout.strip()
        set_snapshot_metadata(
            commit_hash,
            {"favorite": False, "notes": "", "renamed": None, "deleted": False},
        )
        print(
            msgs.get(
                "success", "✅ Snapshot saved successfully! (Shadow hash: {hash})"
            ).format(hash=commit_hash[:7])
        )


def list_snapshots(group_by_branch=False, show_ai=True):
    init_shadow_repo()
    msgs = CONFIG.get("list_snapshots", {})

    res = run_shadow_cmd(
        ["log", "--pretty=format:%h|%s|%b%x1e", "-n", "100"],
        check=False,
        capture_output=True,
        quiet=True,
    )

    if res.returncode != 0 or not res.stdout.strip():
        print(msgs.get("no_snapshots", "No snapshots found."))
        return []

    snapshots = []
    for record in res.stdout.strip().split("\x1e"):
        if not record.strip():
            continue
        parts = record.strip().split("|", 2)
        commit_hash = parts[0]
        subject = parts[1] if len(parts) > 1 else ""
        body = parts[2] if len(parts) > 2 else ""

        branch = "unknown"
        if "Branch: " in body:
            branch_match = re.search(r"Branch: ([^\n]+)", body)
            if branch_match:
                branch = branch_match.group(1)

        meta = get_snapshot_metadata(commit_hash)

        if meta.get("deleted", False):
            continue

        # Note: show_ai parameter is kept for API compatibility but now filters by notes
        if not show_ai and meta.get("notes", ""):
            continue

        display_name = meta.get("renamed") or subject

        snapshots.append(
            {
                "hash": commit_hash,
                "subject": display_name,
                "branch": branch,
                "is_favorite": meta.get("favorite", False),
                "notes": meta.get("notes", ""),
                "timestamp": "unknown",  # We could extract from body if needed
            }
        )

    snapshots.sort(key=lambda x: (not x["is_favorite"]))

    if group_by_branch:
        branches = {}
        for snap in snapshots:
            branches.setdefault(snap["branch"], []).append(snap)
        print(
            msgs.get("title_grouped", "\n--- Shadow Snapshots (Grouped by Branch) ---")
        )
        idx = 1
        flat_list = []
        for br, snaps in branches.items():
            print(msgs.get("branch_prefix", "\n📁 Branch: {branch}").format(branch=br))
            print(msgs.get("header_grouped", "No.  Fav  Hash     Description"))
            print(msgs.get("separator_grouped", "-" * 50))
            for snap in snaps:
                fav_icon = "⭐" if snap["is_favorite"] else ""
                notes = snap.get("notes", "")
                notes_display = f" | {notes}" if notes else ""
                print(
                    f"{idx:<4} {fav_icon:<4} {snap['hash']:<8} {snap['subject']}{notes_display}"
                )
                flat_list.append(snap)
                idx += 1
        return flat_list
    else:
        print(msgs.get("title_normal", "\n--- Shadow Snapshots ---"))
        print(
            msgs.get(
                "header_normal",
                "No.  Fav  Hash     Branch               Description                    Notes",
            )
        )
        print(msgs.get("separator_normal", "-" * 100))
        for i, snap in enumerate(snapshots):
            fav_icon = "⭐" if snap["is_favorite"] else ""
            notes = snap.get("notes", "")
            # Truncate notes if too long
            notes_display = notes[:27] + "..." if len(notes) > 30 else notes
            print(
                f"{i+1:<4} {fav_icon:<4} {snap['hash']:<8} {snap['branch']:<20} {snap['subject']:<25} {notes_display:<30}"
            )
        return snapshots


def restore_snapshot():
    msgs = CONFIG.get("restore_snapshot", {})
    print(msgs.get("title", "\n--- Restore Snapshot (Shadow Repo) ---"))
    snapshots = list_snapshots()
    if not snapshots:
        return

    choice = input(
        msgs.get(
            "prompt_number",
            "\nEnter snapshot number to restore (or press Enter to cancel): ",
        )
    ).strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(snapshots):
        return

    snap = snapshots[int(choice) - 1]
    commit_hash = snap["hash"]

    print(msgs.get("options_title", "\nRestore Options:"))
    print(
        msgs.get(
            "option_all", "1. Restore everything (Overwrite current working directory)"
        )
    )
    print(msgs.get("option_specific", "2. Restore specific file/folder"))

    opt = input(msgs.get("choice_prompt", "Choice (1-2): ")).strip()

    if opt == "1":
        confirm = input(
            msgs.get(
                "warning",
                "WARNING: This will overwrite your current uncommitted changes with snapshot {hash}. Continue? (y/n): ",
            ).format(hash=commit_hash)
        )
        if confirm.lower() == "y":
            # Use git archive to extract all files from the snapshot
            _, work_tree = get_shadow_repo_path()
            os.chdir(work_tree)

            # Extract using git archive and tar
            result = run_shadow_cmd(
                ["archive", "--format=tar", commit_hash],
                capture_output=True,
                check=False,
                quiet=True,
                binary=True,
            )

            if result.returncode == 0 and result.stdout:
                # Create a temporary file for the tar content
                with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp:
                    tmp.write(result.stdout)
                    tmp_path = tmp.name

                try:
                    with tarfile.open(tmp_path, "r") as tar:
                        tar.extractall(path=work_tree)
                finally:
                    os.unlink(tmp_path)

                # Mark snapshot as restored
                print(f"✅ Snapshot {commit_hash[:7]} restored successfully.")
            else:
                print("❌ Failed to restore snapshot.")
    elif opt == "2":
        # Restore specific file
        path = input("Enter file path to restore: ").strip()
        if path:
            try:
                # Extract specific file
                _, work_tree = get_shadow_repo_path()
                result = run_shadow_cmd(
                    ["archive", "--format=tar", commit_hash, path],
                    capture_output=True,
                    check=False,
                    quiet=True,
                    binary=True,
                )

                if result.returncode == 0 and result.stdout:
                    # Create a temporary file for the tar content
                    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp:
                        tmp.write(result.stdout)
                        tmp_path = tmp.name

                    try:
                        with tarfile.open(tmp_path, "r") as tar:
                            tar.extractall(path=work_tree)
                    finally:
                        os.unlink(tmp_path)

                    print(f"✅ File {path} restored successfully.")
                else:
                    print("❌ Failed to restore file.")
            except (OSError, subprocess.SubprocessError, tarfile.TarError) as e:
                print(f"❌ Error restoring file: {e}")


def view_diff():
    """View diff of a snapshot"""
    snapshots = list_snapshots()
    if not snapshots:
        return

    view_diff_cfg = CONFIG.get("view_diff", {})
    choice = input(
        view_diff_cfg.get("prompt_number", "\nEnter snapshot number to view diff: ")
    ).strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(snapshots):
        return

    snap = snapshots[int(choice) - 1]
    commit_hash = snap["hash"]

    # Show git diff for the snapshot
    run_shadow_cmd(["diff", commit_hash], quiet=False)


def manage_snapshots():
    """Manage snapshots (toggle favorite, rename, delete)"""
    snapshots = list_snapshots()
    if not snapshots:
        return

    manage_menu = CONFIG.get("manage_menu", {})
    manage_cfg = CONFIG.get("manage_snapshots", {})

    print(manage_menu.get("title", "\n--- Manage Snapshots ---"))
    for i, snap in enumerate(snapshots, 1):
        status = "⭐" if snap["is_favorite"] else "   "
        print(f"{i}. {status} {snap['hash'][:7]} - {snap['subject']}")

    choice = input(manage_cfg.get("prompt_number", "\nEnter snapshot number: ")).strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(snapshots):
        return

    snap = snapshots[int(choice) - 1]
    commit_hash = snap["hash"]
    meta = get_snapshot_metadata(commit_hash)

    for option in manage_menu.get(
        "options",
        ["1. Toggle Favorite", "2. Rename Snapshot", "3. Delete Snapshot", "0. Back"],
    ):
        print(option)

    opt = input(manage_menu.get("prompt", "\nChoice (0-3): ")).strip()
    if opt == "1":
        meta["favorite"] = not meta.get("favorite", False)
        set_snapshot_metadata(commit_hash, meta)
        status = "Added" if meta["favorite"] else "Removed"

        # Create or delete a tag to prevent/allow git gc to clean it up
        tag_name = f"favorite-{commit_hash}"
        if meta["favorite"]:
            run_shadow_cmd(["tag", tag_name, commit_hash], check=False, quiet=True)
        else:
            run_shadow_cmd(["tag", "-d", tag_name], check=False, quiet=True)

        print(
            manage_cfg.get("favorite_added", "✅ {status} favorite for {hash}").format(
                status=status, hash=commit_hash
            )
        )

    elif opt == "2":
        new_name = input(
            manage_cfg.get(
                "rename_prompt", "Enter new name for snapshot (current: {current}): "
            ).format(current=snap["subject"])
        ).strip()
        if new_name:
            meta["renamed"] = new_name
            set_snapshot_metadata(commit_hash, meta)
            print(
                manage_cfg.get(
                    "rename_success", "✅ Snapshot renamed to '{name}'"
                ).format(name=new_name)
            )

    elif opt == "3":
        if meta.get("favorite", False):
            print(
                manage_cfg.get(
                    "delete_warning",
                    "⚠️ Cannot delete a favorite snapshot. Unfavorite it first.",
                )
            )
            return
        confirm = input(
            manage_cfg.get("delete_confirm", "Delete snapshot {hash}? (y/n): ").format(
                hash=commit_hash
            )
        ).strip()
        if confirm.lower() == "y":
            meta["deleted"] = True
            set_snapshot_metadata(commit_hash, meta)
            print(
                manage_cfg.get(
                    "delete_success", "✅ Snapshot {hash} deleted (hidden)."
                ).format(hash=commit_hash)
            )


def cleanup_shadow_repo():
    """Cleanup shadow repository"""
    msgs = CONFIG.get("cleanup", {})
    print(msgs.get("title", "\n--- Auto-Cleanup Shadow Repo ---"))
    print(
        msgs.get(
            "description",
            "This will remove snapshots older than 30 days that are not marked as favorites.",
        )
    )
    # First, expire all reflogs older than 30 days
    run_shadow_cmd(
        ["reflog", "expire", "--expire=30.days", "refs/heads/master"], quiet=True
    )
    # Then prune unreachable objects older than 30 days
    run_shadow_cmd(["gc", "--prune=30.days"], quiet=True)
    print(msgs.get("success", "✅ Cleanup complete."))
