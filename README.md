# d4-snap

Local-only Git snapshot manager — save shadow checkpoints of your working tree, diff against them, and restore files or the full directory without touching main repo history.

**Version:** `0.1.4` · **Python:** 3.10+

## Links

- [Repository](https://github.com/internetics-net/d4-snap)
- [Issues](https://github.com/internetics-net/d4-snap/issues)

## Quick start

```bash
pip install d4-snap

# Quick snapshot (creates checkpoint and exits)
d4-snap

# Interactive menu
d4-snap menu
```

From a dev checkout:

```bash
git clone https://github.com/internetics-net/d4-snap.git
cd d4-snap
poetry install
poetry run d4-snap menu
```

Run all commands from inside a Git repository.

## Why d4-snap?

Developers often want to save progress without cluttering the main branch with WIP commits. **d4-snap** stores snapshots in an isolated **bare Git repo** under `~/.d4_snap/.d4_snap/<repo-name>-<hash>`. Your primary repository history stays untouched; you can experiment, roll back, and clean up with confidence.

## Features

| Feature | Description |
|---------|-------------|
| Shadow snapshots | Bare repo per project; no commits on your main branch |
| Quick save | `d4-snap` with no args saves and exits |
| Full or partial restore | Overwrite the working tree or restore a single file |
| Diff viewer | Compare a snapshot to the current working directory |
| Metadata | Favorites, rename, soft-delete via `git notes` |
| Auto-naming | Timestamp format `YYYYMMDD-HHMMSSMMM` |
| AI notes | Optional short summary of changed files per snapshot |
| Auto-cleanup | Configurable retention on every run; favorites preserved |
| Safety | Path validation, safe tar extraction, YAML safe-load |

All operations are **local-only** — no remote pushes or pulls.

## CLI

| Command | Description |
|---------|-------------|
| `d4-snap` | Create a snapshot and exit |
| `d4-snap menu` | Interactive menu |
| `d4-snap help` | Show help (`--help`, `-h`, `/?` also work) |

### Main menu

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

### Menu actions

**Save snapshot** — stages the working tree in the shadow repo, commits with an auto-generated name, and stores metadata (notes, favorite flag).

**List / manage** — browse snapshots by branch; toggle favorite, rename, or soft-delete. Favorites are never auto-deleted.

**View diff** — pick a snapshot, optionally a relative file path, and run `git diff` against the current tree.

**Restore** — two modes:

1. **Restore everything** — extracts the full snapshot via `git archive` + safe tar extraction; warns before overwrite; deletes the restored snapshot and all newer ones.
2. **Restore specific file** — enter a repo-relative path (e.g. `src/d4_snap/cli.py`); only that file is written back.

**Cleanup** — manual purge of snapshots older than the configured manual retention (default 30 days); favorites kept.

## Configuration

Bundled defaults live in `src/d4_snap/config/d4_snap.yaml`. Menu labels, prompts, and cleanup behaviour are all configurable.

```yaml
auto_cleanup:
  enabled: true
  auto_cleanup_days: 90    # runs after every d4-snap execution
  manual_cleanup_days: 30  # menu option 5
```

- **Automatic cleanup** runs on every invocation unless `enabled: false`.
- **Favorites** are always preserved.
- **UI strings** (titles, prompts, success/error messages) can be customized in the same file.

## Architecture

```
main.py          Entry point, argument validation, auto-cleanup hook
cli.py           Menu orchestration
snapshot_manager Snapshot create/restore/list/metadata
git_operations   Shadow repo, git commands, safe tar extract
path_safety      Relative-path validation and directory containment
ui.py / menu.py  Interactive prompts and display
tools.py         Config loading (yaml.safe_load)
```

Shadow repo path: `~/.d4_snap/.d4_snap/<repo-basename>-<md5-hash[:12]>`

## Security

d4-snap is designed for local use on your own machine. Key safeguards in **0.1.4**:

- **Safe tar extraction** — `safe_extract_tar()` blocks path traversal and symlink escapes before `extractall`.
- **Path validation** — restore and diff reject absolute paths, `..` segments, and unsafe characters (`path_safety.py`).
- **Atomic writes** — single-file restore uses a temp file + `os.replace`.
- **Safe config** — `yaml.safe_load` only; no arbitrary code execution from config.
- **Subprocess** — git commands run as argument lists (`shell=False`).
- **CLI args** — whitelist validation in `main.validate_argument()`.

User-supplied paths must be **relative to the repository root** (e.g. `src/foo.py`, not `/etc/passwd` or `../../outside`).

## Examples

### Quick snapshot

```bash
$ d4-snap
Saving snapshot...
✅ Snapshot saved successfully! (Shadow hash: 0f7a40e)
```

### List snapshots

```
No.  Fav  Hash     Branch               Description                    Notes
----------------------------------------------------------------------------------------------------
1    ⭐   0f7a40e  main                 My custom name                 Fixed auth bug in login
2         36f3ca7  feature-branch       20260221-225542076             Added profile settings
```

### Restore everything

```
Choice (1-2): 1
WARNING: This will overwrite your current uncommitted changes with snapshot 36f3ca7. Continue? (y/n): y
✅ Restored working directory to snapshot 36f3ca7
Deleted 2 snapshot(s)
```

## Testing

**108 tests passing**

```bash
poetry run pytest

# With coverage
poetry run pytest --cov=d4_snap --cov-report=html

# Single module
poetry run pytest tests/test_path_safety.py -v
```

Coverage includes CLI, git operations, snapshot manager, UI, config loading, and path/tar security guards.

## FAQ

| Question | Answer |
|----------|--------|
| Do snapshots affect my Git history? | No. They live in a separate bare repo under `~/.d4_snap`. |
| Can I share snapshots? | Local only. Export the shadow folder or use `git bundle` on the bare repo. |
| What happens on full restore? | The restored snapshot and all newer snapshots are deleted automatically. |
| How do I keep a snapshot forever? | Mark it as a favorite in the manage menu. |
| Can I disable auto-cleanup? | Set `auto_cleanup.enabled: false` in the YAML config. |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `d4-snap: command not found` | Ensure your Python scripts directory (e.g. `~/.local/bin`) is on `PATH`. |
| `fatal: not a git repository` | `cd` into a Git repo first. |
| `Permission denied` on `~/.d4_snap` | Fix directory permissions (e.g. `chmod -R 700 ~/.d4_snap` on Unix). |
| Restore rejected for a path | Use a repo-relative path with no `..` segments. |

## Contributing

1. Fork the repo
2. Create a feature branch
3. Run `poetry run pytest`
4. Open a pull request

## License

MIT © 2026 d4-snap Developers — see [LICENSE](LICENSE).
