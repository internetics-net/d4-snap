---
name: d4-rag-impact
description: "Use when the user wants blast radius or what breaks if a symbol changes."
---

# Impact analysis with d4-ai-rag-intel

Follow the global safety and evidence rules in `AGENTS.md`. This skill covers blast
radius interpretation and the pre-commit sequence only.

## Workflow

```
1. impact({target: "symbolName", direction: "upstream"})
2. READ d4rag://repo/{name}/processes
3. detect_changes({scope: "unstaged"})
4. Report blast radius, affected processes, and risk
```

If HIGH or CRITICAL, warn before editing. If the name is ambiguous, use a candidate
`target_uid` or `qualname`. For hub symbols, request `summaryOnly: true` first.

- `upstream` means callers and what may break.
- `downstream` means callees and what the symbol uses.

## Depth

| Depth | Meaning |
|-------|---------|
| d=1 | Direct callers; likely immediate impact |
| d=2 | Likely affected callers |
| d=3 | May need testing |

## Pre-commit

```
detect_changes({scope: "unstaged"})
detect_changes({scope: "compare", base_ref: "<default branch from AGENTS.md>"})
```

If the index is stale, run `d4-ai-rag-intel analyze`, then reload MCP.
