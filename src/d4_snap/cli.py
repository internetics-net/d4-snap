"""Command-line interface orchestration module"""

from .menu import get_menu_manager
from .ui import get_ui
from .snapshot_manager import get_snapshot_manager


def save_snapshot(is_claude=False):
    """Save current work snapshot"""
    ui = get_ui()
    snap_mgr = get_snapshot_manager()

    ui.display_title("save_snapshot")
    ui.display_message("save_snapshot", "saving")

    result = snap_mgr.create_snapshot(is_claude)

    if result["success"]:
        ui.display_message("save_snapshot", "success", {"hash": result["hash"][:7]})
    else:
        ui.display_message("save_snapshot", "no_changes")


def list_snapshots(group_by_branch=False, show_ai=True):
    """List all snapshots"""
    ui = get_ui()
    snap_mgr = get_snapshot_manager()

    snapshots = snap_mgr.get_snapshots(group_by_branch, show_ai)

    if not snapshots:
        ui.display_message("list_snapshots", "no_snapshots")
        return []

    ui.display_snapshots(snapshots, group_by_branch)
    return snapshots


def restore_snapshot():
    """Restore a snapshot"""
    ui = get_ui()
    snap_mgr = get_snapshot_manager()

    ui.display_title("restore_snapshot")
    snapshots = list_snapshots()

    if not snapshots:
        return

    snap = ui.get_snapshot_selection(snapshots, "restore_snapshot")
    if not snap:
        return

    commit_hash = snap["hash"]
    restore_opt = ui.get_restore_option()

    if restore_opt == "1":
        # Restore everything
        if ui.get_confirmation("restore_snapshot", "warning", {"hash": commit_hash}):
            if snap_mgr.restore_full_snapshot(commit_hash):
                ui.display_message(
                    "restore_snapshot", "success_all", {"hash": commit_hash}
                )

                # Delete restored snapshot and newer ones
                selected_index = snapshots.index(snap)
                count = snap_mgr.delete_snapshots_up_to(snapshots, selected_index)
                ui.display_success(f"Deleted {count} snapshot(s)")
            else:
                ui.display_error(f"Could not restore snapshot {commit_hash}")

    elif restore_opt == "2":
        # Restore specific file
        path = ui.get_file_path("restore_snapshot", "prompt_path")
        if path:
            if snap_mgr.restore_file_from_snapshot(commit_hash, path):
                ui.display_message(
                    "restore_snapshot",
                    "success_path",
                    {"path": path, "hash": commit_hash},
                )
            else:
                ui.display_error(
                    f"Could not restore '{path}' from snapshot {commit_hash}"
                )
                files = snap_mgr.get_snapshot_files(commit_hash)
                if files:
                    from . import git_operations

                    _, work_tree = git_operations.get_shadow_repo_path()
                    ui.display_available_files(files, work_tree)


def view_diff():
    """View diff between snapshot and current state"""
    ui = get_ui()
    snap_mgr = get_snapshot_manager()

    ui.display_title("view_diff")
    snapshots = list_snapshots()

    if not snapshots:
        return

    snap = ui.get_snapshot_selection(snapshots, "view_diff")
    if not snap:
        return

    commit_hash = snap["hash"]
    path = ui.get_file_path("view_diff", "prompt_path")

    ui.display_message("view_diff", "diff_title", {"hash": commit_hash})
    snap_mgr.show_diff(commit_hash, path if path else None)


def manage_snapshots():
    """Manage snapshots (favorite, rename, delete)"""
    ui = get_ui()
    snap_mgr = get_snapshot_manager()
    menu_mgr = get_menu_manager()

    while True:
        menu_mgr.display_menu("manage_menu")
        opt = menu_mgr.get_user_input("manage_menu")

        if opt == "0":
            break

        if opt in ["1", "2", "3"]:
            snapshots = list_snapshots()
            if not snapshots:
                return

            snap = ui.get_snapshot_selection(snapshots, "manage_snapshots")
            if not snap:
                continue

            commit_hash = snap["hash"]

            if opt == "1":
                # Toggle favorite
                is_favorite = snap_mgr.toggle_favorite(commit_hash)
                status = "Added" if is_favorite else "Removed"
                ui.display_message(
                    "manage_snapshots",
                    "favorite_added",
                    {"status": status, "hash": commit_hash},
                )

            elif opt == "2":
                # Rename snapshot
                new_name = ui.get_new_snapshot_name(snap["subject"])
                if new_name and snap_mgr.rename_snapshot(commit_hash, new_name):
                    ui.display_message(
                        "manage_snapshots", "rename_success", {"name": new_name}
                    )

            elif opt == "3":
                # Delete snapshot
                result = snap_mgr.delete_snapshot(commit_hash)
                if result["success"]:
                    ui.display_message(
                        "manage_snapshots", "delete_success", {"hash": commit_hash}
                    )
                else:
                    if result["message"] == "is_favorite":
                        ui.display_message("manage_snapshots", "delete_warning")


def cleanup_shadow_repo():
    """Cleanup old snapshots"""
    ui = get_ui()
    snap_mgr = get_snapshot_manager()

    ui.display_title("cleanup")
    ui.display_message("cleanup", "description")

    snap_mgr.cleanup_old_snapshots()
    ui.display_message("cleanup", "success")


def main():
    """Main CLI loop"""
    menu_mgr = get_menu_manager()

    while True:
        choice = menu_mgr.display_and_get_choice("main_menu")

        if choice == "1":
            save_snapshot()
        elif choice == "2":
            manage_snapshots()
        elif choice == "3":
            view_diff()
        elif choice == "4":
            restore_snapshot()
        elif choice == "5":
            cleanup_shadow_repo()
        elif choice == "0":
            menu_mgr.print_message("messages", "goodbye")
            break
        else:
            menu_mgr.print_message("messages", "invalid_choice")


if __name__ == "__main__":
    main()
