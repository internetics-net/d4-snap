<!-- d4-rag:start -->
# d4-rag — Code Intelligence

This project is indexed by **d4-ai-rag** (`structural.db` under `~/.d4/d4-ai-rag/vectors/`). Use the **d4-ai-rag MCP** tools (or `d4-rag` CLI) to understand code, assess impact, and navigate safely.

> Index stale? Run `d4-rag analyze` from the project root. Check with `d4-rag status`.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- Ad-hoc graph inspection: `sql({statement: "SELECT ..."})` (read-only SELECT/WITH against `structural.db`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `d4rag://repo/d4/context` | Stats, staleness |
| `d4rag://repo/d4/clusters` | Packages / subsystems |
| `d4rag://repo/d4/processes` | Heuristic execution flows |
| `d4rag://repo/d4/schema` | SQLite schema for `sql` |

## CLI

| Task | Skill |
|------|-------|
| Understand architecture | `.claude/skills/d4-rag/d4-rag-exploring/SKILL.md` |
| Blast radius | `.claude/skills/d4-rag/d4-rag-impact/SKILL.md` |
| Trace bugs | `.claude/skills/d4-rag/d4-rag-debugging/SKILL.md` |
| Tools and resources | `.claude/skills/d4-rag/d4-rag-guide/SKILL.md` |
| analyze / status / clean / mcp | `.claude/skills/d4-rag/d4-rag-cli/SKILL.md` |

PDG/taint (`explain`, `pdg_query`, `--pdg`) is **not** in this release.
<!-- d4-rag:end -->
