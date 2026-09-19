---
name: d4-rag-pdg
description: "Use when querying Python PDG/taint: explain findings, pdg_query controls/flows, or d4-ai-rag-intel analyze --pdg."
---

# d4-ai-rag-intel PDG and taint

Follow the global safety and evidence rules in `AGENTS.md`. This skill covers the
optional Python PDG and taint layer only.

PDG is Python-only and opt-in. Default `d4-ai-rag-intel analyze` writes zero `pdg_*` rows
and clears stale PDG data from a previous `--pdg` run.

```bash
d4-ai-rag-intel analyze --pdg [--repo PATH]
d4-ai-rag-intel explain [target] [--repo] [--limit]
d4-ai-rag-intel pdg_query controls|flows TARGET [--variable NAME] [--repo] [--limit]
```

Reload MCP after `analyze`.

## Tool selection

| Need | Tool |
|------|------|
| Taint findings | `explain` |
| Conditions guarding a statement | `pdg_query` with `controls` |
| Variable data flow | `pdg_query` with `flows` |
| Function/class blast radius | `impact`, not PDG |

No PDG layer returns empty results with a note; absence of a finding is not proof
of safety. `pdg_query` requires a target. `explain` without a target enumerates
bounded findings.

## Caveats

The layer can miss closures, callbacks, field-sensitive access paths, guard-style
sanitizers, and async behavior. Exception edges are conservative. JavaScript and
TypeScript CFG is not built.
