---
name: d4-rag-debugging
description: "Use when tracing why something fails or how A reaches B."
---

# Debugging with d4-ai-rag-intel

Follow the global safety and evidence rules in `AGENTS.md`. This skill covers the
debugging sequence only.

## When to use

- "Why is X failing?"
- "How does A reach B?"
- Trace a bug through callers/callees without grepping first

## Workflow

```
1. context({name: "suspectFn"})           -> who calls it / what it calls
2. trace({frm: "A", to: "B"})             -> shortest CALLS path
3. detect_changes({scope: "all"})         -> what the working tree touched
4. sql({statement: "SELECT caller, callee FROM cg_edges WHERE callee LIKE '%suspect%'"})
5. check({relation: "IMPORTS"})            -> import cycles
6. explain({target: "suspectFn"})          -> taint findings (needs analyze --pdg)
7. pdg_query({mode: "controls", target: "suspectFn"}) -> what guards this
```

Read `d4rag://repo/{name}/process/{id}` for the heuristic flow that contains the suspect.

PDG/taint is opt-in (`d4-ai-rag-intel analyze --pdg`). Without that layer, `explain` /
`pdg_query` return `{results: [], note: "no taint layer"}`. `impact()` does not
walk PDG edges.

If the index is stale, run `d4-ai-rag-intel analyze` and reload MCP before continuing.
