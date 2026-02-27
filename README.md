# d4-snap – Git Snapshot & Rollback Manager

**d4-snap** is a lightweight, local-only Git helper that gives you a simple, reproducible way to:

* Keep *shadow checkpoints* – isolated snapshots that don't touch your main repo history
* Quickly save your progress locally without making official Git commits
* Restore your entire working directory or specific files to a previous snapshot
* View diffs between snapshots and your current state
* Manage snapshots with favorites, renaming, and deletion
* Automatic snapshot cleanup when restoring

> **Why d4-snap?**
> The tool was built for developers who want a quick, interactive workflow to seamlessly save code iterations without cluttering the main repo. All operations happen locally in a hidden bare repo, so you can experiment freely and clean up with confidence.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Commands & Options](#commands--options)
- [Examples](#examples)
- [FAQ](#faq)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Feature | Description |
|---------|-------------|
| Snapshot Storage | Stores snapshots as a bare Git repo in `~/.d4_snap/.d4_snap/<repo-name>-<hash>`. |
| Metadata | Uses `git notes` to store: `favorite`, `renamed`, `ai`, `deleted`. |
| Auto-naming | Snapshots are automatically named with timestamp format `YYYYMMDD-HHMMSSMMM`. |
| Snapshot Management | Save, restore, view diff, list, rename, delete, toggle favorite. |
| Auto-deletion | When restoring a snapshot, automatically deletes that snapshot and all newer ones. |
| Cleanup | Expire reflogs and run garbage-collection to remove non-favorite snapshots older than 30 days. |

All commands are **local-only** – no remote pushes or pulls are involved.

---

## Installation

### Prerequisites

* Python 3.8+
* Git (≥ 2.20)

### pip

```bash
pip install d4-snap
```

### From source

```bash
git clone https://github.com/yourorg/d4-snap.git
cd d4-snap
python -m pip install .
```

> **Note:** The package installs a console script named `d4-snap` that will be available in your PATH.

---

## Usage

d4-snap provides both a quick snapshot mode and an interactive menu-driven interface.

### Quick Snapshot Mode

```bash
# Create a snapshot of current project and exit
d4-snap
```

### Interactive Menu Mode

```bash
# Show interactive menu
d4-snap menu
```

### Help

```bash
# Show help information
d4-snap help
d4-snap --help
d4-snap /?
```

All commands should be run from within a Git repository.

### Main Menu

```
🚀 Git Checkpoint & Rollback Manager (Shadow Checkpoints)
========================================
1. Save Snapshot
2. List / Manage Snapshots
3. View Diff
4. Restore Snapshot
5. Cleanup Old Snapshots
0. Exit
```

---

## Commands & Options

### 1. Save Snapshot

* Saves the current working directory, including all files, into the shadow repo
* Automatically generates a timestamp-based name (format: `YYYYMMDD-HHMMSSMMM`)
* Creates a commit in the isolated shadow repository
* Stores metadata using Git notes

### 2. List / Manage Snapshots

Displays all snapshots with:
* Snapshot number
* Favorite indicator (⭐)
* Commit hash (short)
* Branch name
* Description/name

Management options:
* **Toggle Favorite status** - Mark/unmark snapshots as favorites (prevents auto-deletion)
* **Rename a snapshot** - Give snapshots custom names
* **Delete a snapshot** - Soft-delete snapshots (cannot delete favorites)

### 3. View Diff

* Select a snapshot from the list
* Choose to view diff for all files or a specific file/folder
* Shows `git diff` between the snapshot and current working directory

### 4. Restore Snapshot

Two restore options:

**Option 1: Restore everything**
* Extracts all files from the snapshot to your working directory
* **Automatically deletes the restored snapshot and all newer snapshots**
* Provides a warning before overwriting current changes

**Option 2: Restore specific file/folder**
* Enter the relative path to restore (e.g., `src/d4_snap/cli.py`)
* Only restores the specified file/folder
* Does not trigger automatic snapshot deletion

### 5. Cleanup Old Snapshots

* Runs `git reflog expire --expire=30.days` and `git gc --prune=30.days`
* Removes snapshots older than 30 days that are not marked as favorites
* Favorites are always preserved

---

## Examples

### Saving a Snapshot

```
Select an option (0-5): 1

--- Save Work Snapshot (Shadow Repo) ---
Saving snapshot...
✅ Snapshot saved successfully! (Shadow hash: 0f7a40e)
```

### Listing Snapshots

```
Select an option (0-5): 2

--- Shadow Snapshots ---
No.  Fav  Hash     Branch               Description
---------------------------------------------------------------------------
1    ⭐   0f7a40e  main                 My custom name
2         36f3ca7  feature-branch       20260221-225542076
3         ffa0250  main                 20260221-224736433
```

### Restoring a Snapshot

```
Select an option (0-5): 4

--- Restore Snapshot (Shadow Repo) ---
Enter snapshot number to restore: 2

Restore Options:
1. Restore everything (Overwrite current working directory)
2. Restore specific file/folder
Choice (1-2): 1

WARNING: This will overwrite your current uncommitted changes with snapshot 36f3ca7. Continue? (y/n): y
✅ Restored working directory to snapshot 36f3ca7

Deleting 2 snapshot(s)...
✅ Deleted 2 snapshot(s)
```

### Managing Snapshots

```
Select an option (0-5): 2

--- Manage Snapshots ---
1. Toggle Favorite status
2. Rename a snapshot
3. Delete a snapshot
0. Back to main menu

Choice (0-3): 2
Enter snapshot number: 1
Enter new name for snapshot (current: 20260221-225555884): My custom name
✅ Snapshot renamed to 'My custom name'
```

---

## FAQ

| Question | Answer |
|----------|--------|
| **Do snapshots affect my Git history?** | No. Snapshots are stored in a *bare* repo under `~/.d4_snap/.d4_snap/...`. Your main repo stays untouched. |
| **Can I share snapshots with teammates?** | They are local only. To share, export the snapshot folder or use `git bundle` on the bare repo. |
| **How to remove old snapshots?** | Run option 5 (Cleanup Old Snapshots) from the main menu. Favorites will be preserved. |
| **What happens when I restore a snapshot?** | When you restore everything (option 1), the snapshot and all newer snapshots are automatically deleted. This prevents confusion about which state you're in. |
| **Can I prevent a snapshot from being deleted?** | Yes! Mark it as a favorite using the "Toggle Favorite status" option in the Manage Snapshots menu. Favorites are never auto-deleted. |
| **What does the "AI" flag mean?** | An optional metadata flag to track snapshots created by AI assistants. Currently not used in the UI. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `d4-snap: command not found` | `pip` did not add the script to PATH | Ensure `~/.local/bin` (or your Python bin directory) is in `$PATH`. |
| `fatal: not a git repository` | You’re not inside a Git repo | `cd` to a repo first. |
| `Permission denied` on `~/.d4_snap` | Permissions issue | Run `chmod -R 700 ~/.d4_snap` (or adjust as needed). |

---

## Configuration

All menu texts are externalized in `src/d4_snap/config/d4_snap.yaml` for easy customization. You can modify:
* Menu titles
* Option labels
* Prompts
* Success/error messages

## Contributing

1. Fork the repo
2. Create a feature branch
3. Run the test suite (if available)
4. Submit a pull request

We welcome issues, feature requests, and PRs.

---

## License

MIT © 2026 d4-snap Developers
See [LICENSE](LICENSE) for details.
