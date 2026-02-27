import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class MenuManager:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "d4_snap.yaml"
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def reload_config(self):
        self.config = self._load_config()

    def get_menu_config(self, menu_name: str) -> Dict[str, Any]:
        return self.config.get(menu_name, {})

    def get_message(self, section: str, key: str, default: str = "") -> str:
        return self.config.get(section, {}).get(key, default)

    def display_menu(self, menu_name: str) -> None:
        menu = self.get_menu_config(menu_name)
        title = menu.get("title", "")
        options = menu.get("options", [])

        if title:
            if menu_name == "main_menu":
                print("\n" + "=" * 40)
                print(title)
                print("=" * 40)
            else:
                print(title)

        for option in options:
            print(option)

    def get_menu_prompt(self, menu_name: str, default: str = "\nChoice: ") -> str:
        menu = self.get_menu_config(menu_name)
        return menu.get("prompt", default)

    def get_user_input(self, menu_name: str, default_prompt: str = "\nChoice: ") -> str:
        prompt = self.get_menu_prompt(menu_name, default_prompt)
        return input(prompt).strip()

    def display_and_get_choice(self, menu_name: str) -> str:
        self.display_menu(menu_name)
        return self.get_user_input(menu_name)

    def get_snapshot_number(
        self, section: str = "manage_snapshots", prompt_key: str = "prompt_number"
    ) -> str:
        prompt = self.get_message(section, prompt_key, "\nEnter snapshot number: ")
        return input(prompt).strip()

    def get_restore_option(self) -> str:
        restore_config = self.get_menu_config("restore_snapshot")
        print(restore_config.get("options_title", "\nRestore Options:"))
        print(restore_config.get("option_all", "1. Restore everything"))
        print(restore_config.get("option_specific", "2. Restore specific file/folder"))
        prompt = restore_config.get("choice_prompt", "Choice (1-2): ")
        return input(prompt).strip()

    def get_path_input(
        self,
        section: str,
        prompt_key: str = "prompt_path",
        default: str = "Enter path: ",
    ) -> str:
        prompt = self.get_message(section, prompt_key, default)
        return input(prompt).strip()

    def get_confirmation(
        self, section: str, prompt_key: str, format_args: Optional[Dict] = None
    ) -> str:
        prompt = self.get_message(section, prompt_key, "Continue? (y/n): ")
        if format_args:
            prompt = prompt.format(**format_args)
        return input(prompt).strip()

    def print_message(
        self,
        section: str,
        key: str,
        format_args: Optional[Dict] = None,
        default: str = "",
    ) -> None:
        message = self.get_message(section, key, default)
        if format_args:
            message = message.format(**format_args)
        print(message)

    def get_new_name_input(self, current_name: str) -> str:
        prompt = self.get_message(
            "manage_snapshots",
            "rename_prompt",
            "Enter new name for snapshot (current: {current}): ",
        )
        return input(prompt.format(current=current_name)).strip()


_menu_manager_instance = None


def get_menu_manager() -> MenuManager:
    global _menu_manager_instance
    if _menu_manager_instance is None:
        _menu_manager_instance = MenuManager()
    return _menu_manager_instance


def show_main_menu():
    menu_mgr = get_menu_manager()
    menu_mgr.display_menu("main_menu")


def show_manage_menu():
    menu_mgr = get_menu_manager()
    menu_mgr.display_menu("manage_menu")


def get_main_choice() -> str:
    menu_mgr = get_menu_manager()
    return menu_mgr.get_user_input("main_menu")


def get_manage_choice() -> str:
    menu_mgr = get_menu_manager()
    return menu_mgr.get_user_input("manage_menu")


def get_snapshot_choice() -> str:
    menu_mgr = get_menu_manager()
    return menu_mgr.get_snapshot_number()


def get_restore_choice() -> str:
    menu_mgr = get_menu_manager()
    return menu_mgr.get_restore_option()


def get_path_input(section: str = "restore_snapshot") -> str:
    menu_mgr = get_menu_manager()
    return menu_mgr.get_path_input(section)
