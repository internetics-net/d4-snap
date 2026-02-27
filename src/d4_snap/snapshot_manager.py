"""
Snapshot management module - business logic for snapshot operations
"""

import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from . import git_operations as git_ops


class SnapshotManager:
    """Manages snapshot operations"""

    def __init__(self):
        git_ops.init_shadow_repo()

    def create_snapshot(self, is_claude: bool = False) -> Dict[str, Any]:
        """
        Create a new snapshot
        Returns: dict with 'success', 'message', 'hash' keys
        """
        branch = git_ops.get_current_branch() or "unknown-branch"

        now = datetime.now(timezone.utc)
        timestamp_name = (
            now.strftime("%Y%m%d-%H%M%S%f")[:17] + f"_{uuid.uuid4().hex[:6]}"
        )
        name = timestamp_name
        if is_claude:
            name = f"Claude-{timestamp_name}"

        timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        commit_msg = f"{name}\n\nBranch: {branch}\nTimestamp: {timestamp}"

        git_ops.run_shadow_cmd(["add", "."], quiet=True)

        res = git_ops.run_shadow_cmd(
            ["commit", "-m", commit_msg], check=False, capture_output=True, quiet=True
        )

        if "nothing to commit" in res.stdout or "nothing to commit" in res.stderr:
            return {"success": False, "message": "no_changes", "hash": None}
        else:
            commit_hash = git_ops.run_shadow_cmd(
                ["rev-parse", "HEAD"], capture_output=True, quiet=True
            ).stdout.strip()
            git_ops.set_snapshot_metadata(
                commit_hash,
                {"favorite": False, "ai": is_claude, "renamed": None, "deleted": False},
            )
            return {"success": True, "message": "saved", "hash": commit_hash}

    def get_snapshots(
        self, group_by_branch: bool = False, show_ai: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get list of snapshots
        Returns: list of snapshot dicts with hash, subject, branch, is_favorite, is_ai
        """
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

            if not show_ai and meta.get("ai", False):
                continue

            display_name = meta.get("renamed") or subject

            snapshots.append(
                {
                    "hash": commit_hash,
                    "subject": display_name,
                    "branch": branch,
                    "is_favorite": meta.get("favorite", False),
                    "is_ai": meta.get("ai", False),
                    "timestamp": "unknown",
                }
            )

        snapshots.sort(key=lambda x: (not x["is_favorite"]))
        return snapshots

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


# Singleton instance
_snapshot_manager_instance = None


def get_snapshot_manager() -> SnapshotManager:
    """Get the SnapshotManager singleton instance"""
    global _snapshot_manager_instance
    if _snapshot_manager_instance is None:
        _snapshot_manager_instance = SnapshotManager()
    return _snapshot_manager_instance
