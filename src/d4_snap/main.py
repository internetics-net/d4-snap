"""
Main entry point for d4-snap
Integrates all modules: menu, ui, snapshot_manager, git_operations, and cli
"""

import sys
import re
from pathlib import Path

# Support both direct execution and package import
if __name__ == "__main__":
    # Add parent directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from d4_snap.cli import main, save_snapshot
    from d4_snap.snapshot_manager import get_snapshot_manager
    from d4_snap.tools import load_config
else:
    from .cli import main, save_snapshot
    from .snapshot_manager import get_snapshot_manager
    from .tools import load_config


def print_help():
    """Print help information"""
    help_text = """
d4-snap - Git Snapshot & Rollback Manager

USAGE:
    d4-snap                    Create a snapshot of current project and exit
    d4-snap menu               Show interactive menu
    d4-snap help               Show this help message
    d4-snap --help             Show this help message
    d4-snap -h                 Show this help message
    d4-snap /?                 Show this help message

DESCRIPTION:
    d4-snap is a lightweight, local-only Git helper that provides:
    * Shadow snapshots - isolated snapshots that don't touch main repo history
    * Quick progress saving without official Git commits
    * Restore working directory or specific files to previous snapshots
    * View diffs between snapshots and current state
    * Manage snapshots with favorites, renaming, and deletion

EXAMPLES:
    d4-snap                    # Quick snapshot
    d4-snap menu               # Interactive menu mode
    d4-snap help               # Show help

For more information, visit: https://github.com/yourorg/d4-snap
"""
    print(help_text)


def validate_argument(arg):
    """Validate command-line argument for security"""
    if not isinstance(arg, str):
        return False

    # Use whitelist approach - only allow safe characters
    # Allow alphanumeric, hyphens, underscores, and common help flags
    if not re.match(r"^[a-zA-Z0-9\-_/?h]+$", arg):
        return False

    # Length limit to prevent buffer overflow attempts
    if len(arg) > 50:
        return False

    return True


def cleanup_old_snapshots():
    """Cleanup snapshots older than configured days after an operation"""
    try:
        config = load_config()
        auto_cleanup_config = config.get("auto_cleanup", {})

        # Check if auto cleanup is enabled
        if not auto_cleanup_config.get("enabled", True):
            return

        # Get cleanup days from config, default to 90
        cleanup_days = auto_cleanup_config.get("auto_cleanup_days", 90)

        # Validate cleanup_days parameter
        if not isinstance(cleanup_days, int) or cleanup_days <= 0:
            print(
                f"⚠️  Invalid cleanup_days in config: {cleanup_days}. Using default 90."
            )
            cleanup_days = 90

        snapshot_manager = get_snapshot_manager()
        snapshot_manager.cleanup_very_old_snapshots(cleanup_days)
    except (OSError, RuntimeError) as e:
        # Don't let cleanup errors prevent the main operation
        print(f"⚠️  Cleanup warning: {e}")
    except ImportError as e:
        # Handle import errors separately
        print(f"⚠️  Import error during cleanup: {e}")


def run():
    """Run the application with command-line argument handling"""
    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        # Validate input for security
        if not validate_argument(arg):
            print("❌ Invalid argument format.")
            print_help()
            sys.exit(1)

        if arg in ["help", "--help", "-h", "/?"]:
            print_help()
            return
        elif arg == "menu":
            try:
                main()
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Exiting...")
            finally:
                cleanup_old_snapshots()
            return
        else:
            print(f"Unknown argument: {arg}")
            print_help()
            sys.exit(1)

    # Default behavior: create snapshot and exit
    try:
        print("📸 Creating snapshot of current project...")
        save_snapshot()
        print("✅ Snapshot operation completed.")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(1)
    except (OSError, RuntimeError, ImportError) as e:
        print(f"\n❌ Unexpected error during snapshot: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   • Ensure you're in a Git repository")
        print("   • Check if you have uncommitted changes")
        print("   • Verify Git is properly initialized")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        cleanup_old_snapshots()


if __name__ == "__main__":
    run()
