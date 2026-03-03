"""
User interaction module - handles all user input/output operations
"""

from typing import List, Dict, Any, Optional
from .menu import get_menu_manager


class UserInterface:
    """Handles all user interaction and display logic"""

    def __init__(self):
        self.menu_mgr = get_menu_manager()

    def display_title(self, section: str, key: str = "title", default: str = ""):
        """Display a section title from config"""
        self.menu_mgr.print_message(section, key, default=default)

    def display_message(
        self,
        section: str,
        key: str,
        format_args: Optional[Dict] = None,
        default: str = "",
    ):
        """Display a message from config with optional formatting"""
        self.menu_mgr.print_message(section, key, format_args, default)

    def get_snapshot_selection(
        self, snapshots: List[Dict[str, Any]], section: str = "restore_snapshot"
    ) -> Optional[Dict[str, Any]]:
        """Get snapshot selection from user"""
        if not snapshots:
            return None

        choice = self.menu_mgr.get_snapshot_number(section, "prompt_number")

        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(snapshots):
            return None

        return snapshots[int(choice) - 1]

    def get_restore_option(self) -> str:
        """Get restore option from user (1=all, 2=specific)"""
        return self.menu_mgr.get_restore_option()

    def get_file_path(
        self, section: str = "restore_snapshot", prompt_key: str = "prompt_path"
    ) -> str:
        """Get file path input from user"""
        return self.menu_mgr.get_path_input(section, prompt_key)

    def get_confirmation(
        self, section: str, prompt_key: str, format_args: Optional[Dict] = None
    ) -> bool:
        """Get yes/no confirmation from user"""
        response = self.menu_mgr.get_confirmation(section, prompt_key, format_args)
        return response.lower() == "y"

    def get_new_snapshot_name(self, current_name: str) -> str:
        """Get new snapshot name from user"""
        return self.menu_mgr.get_new_name_input(current_name)

    def display_snapshots(
        self, snapshots: List[Dict[str, Any]], grouped: bool = False
    ) -> None:
        """Display list of snapshots"""
        msgs = self.menu_mgr.get_menu_config("list_snapshots")

        if not snapshots:
            print(msgs.get("no_snapshots", "No snapshots found."))
            return

        if grouped:
            # Group by branch
            from collections import defaultdict

            by_branch = defaultdict(list)
            for snap in snapshots:
                by_branch[snap["branch"]].append(snap)

            idx = 1
            for branch, snaps in sorted(by_branch.items()):
                print(
                    msgs.get("branch_prefix", "\n📁 Branch: {branch}").format(
                        branch=branch
                    )
                )
                print(msgs.get("separator_grouped", "-" * 50))
                for snap in snaps:
                    fav_icon = "⭐" if snap["is_favorite"] else ""
                    notes = snap.get("notes", "")
                    notes_display = f" | {notes}" if notes else ""
                    print(
                        f"{idx:<4} {fav_icon:<4} {snap['hash']:<8} {snap['subject']}{notes_display}"
                    )
                    idx += 1
        else:
            # Normal display with Notes column
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

    def display_manage_options(self):
        """Display snapshot management options"""
        manage_menu = self.menu_mgr.get_menu_config("manage_menu")
        for option in manage_menu.get(
            "options",
            [
                "1. Toggle Favorite",
                "2. Rename Snapshot",
                "3. Delete Snapshot",
                "0. Back",
            ],
        ):
            print(option)

    def get_manage_option(self) -> str:
        """Get management option from user"""
        manage_menu = self.menu_mgr.get_menu_config("manage_menu")
        return input(manage_menu.get("prompt", "\nChoice (0-3): ")).strip()

    def display_available_files(self, files: List[str], work_tree: str):
        """Display available files in a snapshot"""
        restore_cfg = self.menu_mgr.get_menu_config("restore_snapshot")
        print(
            restore_cfg.get(
                "available_files_title", "\nAvailable files in this snapshot:"
            )
        )
        for f in files[:15]:
            print(f"  - {f}")
        if len(files) > 15:
            print(
                restore_cfg.get(
                    "available_files_more", "  ... and {count} more files"
                ).format(count=len(files) - 15)
            )
        print(
            restore_cfg.get(
                "available_files_hint",
                "\nHint: Enter paths relative to the working directory: {work_tree}",
            ).format(work_tree=work_tree)
        )

    def display_error(self, message: str):
        """Display error message"""
        print(f"❌ {message}")

    def display_success(self, message: str):
        """Display success message"""
        print(f"✅ {message}")

    def display_warning(self, message: str):
        """Display warning message"""
        print(f"⚠️ {message}")


# Singleton instance
_ui_instance = None


def get_ui() -> UserInterface:
    """Get the UserInterface singleton instance"""
    global _ui_instance
    if _ui_instance is None:
        _ui_instance = UserInterface()
    return _ui_instance
