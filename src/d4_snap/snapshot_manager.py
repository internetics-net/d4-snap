"""
Snapshot management module - business logic for snapshot operations
"""

import re
import os
import hashlib
import subprocess
import threading
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from . import git_operations as git_ops

# Thread-safe singleton lock
_singleton_lock = threading.Lock()


class SnapshotManager:
    """Manages snapshot operations"""

    def __init__(self):
        git_ops.init_shadow_repo()

    def create_snapshot(self, is_claude: bool = False) -> Dict[str, Any]:
        """
        Create a new snapshot
        Returns: dict with 'success', 'message', 'hash' keys
        """
        # Generate timestamp-based name
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S%f")[:-3]

        # Get current branch and repo info
        current_branch = git_ops.get_current_branch()
        repo_root = git_ops.get_repo_root()
        repo_name = os.path.basename(repo_root) if repo_root else "unknown"
        repo_hash = (
            hashlib.md5(repo_root.encode()).hexdigest()[:8] if repo_root else "unknown"
        )

        # Create commit message with metadata
        commit_msg = f"Snapshot: {timestamp}\n\nBranch: {current_branch}\nRepo: {repo_name}\nHash: {repo_hash}"

        # Add all changes and create commit
        git_ops.run_shadow_cmd(["add", "."], quiet=True, check=False)
        try:
            result = git_ops.run_shadow_cmd(
                ["commit", "-m", commit_msg], quiet=True, capture_output=True
            )
            # Check if there's nothing to commit
            if (
                "nothing to commit" in result.stdout
                or "nothing to commit" in result.stderr
            ):
                return {"success": False, "message": "no changes", "hash": ""}
            # Extract just the hash from the commit output
            commit_lines = result.stdout.strip().split("\n")
            commit_hash = commit_lines[-1] if commit_lines else result.stdout.strip()
            # Get the actual commit hash
            hash_result = git_ops.run_shadow_cmd(
                ["rev-parse", "HEAD"], quiet=True, capture_output=True
            )
            commit_hash = hash_result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # Check if there's nothing to commit
            if "nothing to commit" in str(e):
                return {"success": False, "message": "no changes", "hash": ""}
            # Otherwise, there was an actual error
            return {"success": False, "message": "commit failed", "hash": ""}

        # Generate notes for the snapshot
        notes = self._generate_ai_notes()

        # Set metadata with notes instead of ai flag
        git_ops.set_snapshot_metadata(
            commit_hash,
            {"favorite": False, "notes": notes, "renamed": None, "deleted": False},
        )
        return {"success": True, "message": "saved", "hash": commit_hash}

    def get_snapshots(
        self, group_by_branch: bool = False, show_ai: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get list of snapshots
        Returns: list of snapshot dicts with hash, subject, branch, is_favorite, notes
        """
        # Note: group_by_branch parameter is kept for API compatibility
        # but the actual grouping is handled by the UI layer
        _ = group_by_branch  # Mark as intentionally unused to satisfy linters

        res = git_ops.run_shadow_cmd(
            ["log", "--pretty=format:%h|%s|%b%x1e", "-n", "100"],
            check=False,
            capture_output=True,
            quiet=True,
        )

        if res.returncode != 0 or not res.stdout.strip():
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

            meta = git_ops.get_snapshot_metadata(commit_hash)

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
                    "timestamp": "unknown",
                }
            )

        snapshots.sort(key=lambda x: (not x["is_favorite"]))
        return snapshots

    def _generate_ai_notes(self) -> str:
        """Generate AI-powered notes for the snapshot (up to 30 words)"""
        try:
            # Get the list of changed files
            result = git_ops.run_shadow_cmd(
                ["diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True,
                check=False,
                quiet=True,
            )

            if result.returncode != 0 or not result.stdout.strip():
                return "Initial snapshot"

            changed_files = result.stdout.strip().split("\n")
            if not changed_files or changed_files == [""]:
                return "No file changes detected"

            # Generate a concise summary of changed files
            file_summary = self._summarize_files(changed_files)
            return file_summary

        except Exception:
            return "Snapshot created"

    def _summarize_files(self, files: List[str]) -> str:
        """Summarize changed files into a concise description (up to 30 words)"""
        if not files:
            return "No changes"

        # Categorize files by type
        code_files = [
            f for f in files if f.endswith((".py", ".js", ".ts", ".java", ".cpp", ".c"))
        ]
        config_files = [
            f for f in files if f.endswith((".yaml", ".yml", ".json", ".toml", ".ini"))
        ]
        doc_files = [f for f in files if f.endswith((".md", ".txt", ".rst", ".doc"))]
        test_files = [
            f
            for f in files
            if "test" in f.lower() or f.endswith((".test.py", "_test.py", ".spec.js"))
        ]

        parts = []

        if code_files:
            parts.append(
                f"updated {len(code_files)} code file{'s' if len(code_files) != 1 else ''}"
            )

        if config_files:
            parts.append(
                f"modified {len(config_files)} config file{'s' if len(config_files) != 1 else ''}"
            )

        if doc_files:
            parts.append(
                f"updated {len(doc_files)} doc file{'s' if len(doc_files) != 1 else ''}"
            )

        if test_files:
            parts.append(
                f"added {len(test_files)} test{'s' if len(test_files) != 1 else ''}"
            )

        # If no specific categories, just count total files
        if not parts:
            parts.append(f"modified {len(files)} file{'s' if len(files) != 1 else ''}")

        # Join and limit to 30 words
        summary = ", ".join(parts)
        words = summary.split()
        if len(words) > 30:
            summary = " ".join(words[:30]) + "..."

        return summary

    def restore_full_snapshot(self, commit_hash: str) -> bool:
        """Restore entire snapshot to working directory"""
        _, work_tree = git_ops.get_shadow_repo_path()
        return git_ops.extract_snapshot_archive(commit_hash, work_tree)

    def restore_file_from_snapshot(self, commit_hash: str, file_path: str) -> bool:
        """Restore specific file from snapshot"""
        _, work_tree = git_ops.get_shadow_repo_path()
        return git_ops.extract_file_from_snapshot(commit_hash, file_path, work_tree)

    def toggle_favorite(self, commit_hash: str) -> bool:
        """Toggle favorite status of a snapshot"""
        meta = git_ops.get_snapshot_metadata(commit_hash)
        meta["favorite"] = not meta.get("favorite", False)
        git_ops.set_snapshot_metadata(commit_hash, meta)

        tag_name = f"favorite-{commit_hash}"
        if meta["favorite"]:
            git_ops.create_tag(tag_name, commit_hash)
        else:
            git_ops.delete_tag(tag_name)

        return meta["favorite"]

    def rename_snapshot(self, commit_hash: str, new_name: str) -> bool:
        """Rename a snapshot"""
        if not new_name:
            return False
        meta = git_ops.get_snapshot_metadata(commit_hash)
        meta["renamed"] = new_name
        git_ops.set_snapshot_metadata(commit_hash, meta)
        return True

    def delete_snapshot(self, commit_hash: str) -> Dict[str, Any]:
        """
        Delete a snapshot (mark as deleted)
        Returns: dict with 'success' and 'message' keys
        """
        meta = git_ops.get_snapshot_metadata(commit_hash)

        if meta.get("favorite", False):
            return {"success": False, "message": "is_favorite"}

        meta["deleted"] = True
        git_ops.set_snapshot_metadata(commit_hash, meta)

        tag_name = f"favorite-{commit_hash}"
        git_ops.delete_tag(tag_name)

        return {"success": True, "message": "deleted"}

    def delete_snapshots_up_to(
        self, snapshots: List[Dict[str, Any]], index: int
    ) -> int:
        """Delete snapshots from index 0 to index (inclusive)"""
        if index < 0 or index >= len(snapshots):
            return 0

        snapshots_to_delete = snapshots[: index + 1]
        count = 0

        for snap in snapshots_to_delete:
            hash_to_delete = snap["hash"]
            meta = git_ops.get_snapshot_metadata(hash_to_delete)
            meta["deleted"] = True
            git_ops.set_snapshot_metadata(hash_to_delete, meta)

            tag_name = f"favorite-{hash_to_delete}"
            git_ops.delete_tag(tag_name)
            count += 1

        return count

    def get_snapshot_files(self, commit_hash: str) -> List[str]:
        """Get list of files in a snapshot"""
        return git_ops.get_commit_files(commit_hash)

    def show_diff(self, commit_hash: str, path: Optional[str] = None) -> None:
        """Show diff between snapshot and current working directory"""
        git_ops.show_diff(commit_hash, path)

    def cleanup_old_snapshots(self) -> None:
        """Cleanup snapshots older than 30 days"""
        git_ops.cleanup_old_snapshots()

    def cleanup_very_old_snapshots(self, days: int = 90) -> None:
        """Cleanup snapshots older than specified days"""
        git_ops.cleanup_very_old_snapshots(days)


# Singleton instance - use thread-safe getter function
_snapshot_manager_instance = None


def get_snapshot_manager() -> SnapshotManager:
    """Get the SnapshotManager singleton instance (thread-safe)"""
    # Global statement is required for the singleton pattern implementation
    # pylint: disable=global-statement
    global _snapshot_manager_instance
    with _singleton_lock:
        if _snapshot_manager_instance is None:
            _snapshot_manager_instance = SnapshotManager()
    return _snapshot_manager_instance
