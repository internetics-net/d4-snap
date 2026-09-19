---
name: d4-rag-exploring
description: "Use when the user asks how this repository's code works, wants architecture, or execution flows."
---

# Exploring with d4-ai-rag-intel

Follow the global safety and evidence rules in `AGENTS.md`. This skill covers the
exploration sequence only.

## When to use

- "How does X work?"
- "What's the project structure?"
- "What calls this function?"
- Unfamiliar code in an indexed repo

## Workflow

```
1. READ d4rag://repo/{name}/context          -> stats + staleness
2. query({search_query: "<concept>"})        -> process-grouped flows
3. context({name: "<symbol>"})               -> callers / callees / processes
4. READ d4rag://repo/{name}/process/{id}     -> step list
```

If context is stale, run `d4-ai-rag-intel analyze`, then reload the d4-ai-rag MCP server.
Pass `repo: "d4-ai-rag"` when more than one database is registered.

## Resources

| Resource | What you get |
|----------|--------------|
| `d4rag://repos` | Indexed databases + staleness |
| `d4rag://repo/{name}/context` | Stats, `commitsBehind` |
| `d4rag://repo/{name}/clusters` | Packages / subsystems |
| `d4rag://repo/{name}/cluster/{name}` | Members of one package/subsystem |
| `d4rag://repo/{name}/processes` | Heuristic execution flows |
| `d4rag://repo/{name}/process/{id}` | Ordered CALLS walk |
| `d4rag://repo/{name}/schema` | SQLite tables for `sql` |

## Tools

**query** searches concepts by process:

```
query({search_query: "call graph persist"})
```

**context** provides a symbol's callers, callees, and processes:

```
context({name: "open_structural_db"})
```

If the name is ambiguous, use a candidate `qualname` or `uid`.
