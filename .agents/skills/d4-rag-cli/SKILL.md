---
name: d4-rag-cli
description: "Use when indexing, checking status, cleaning, or starting the d4-ai-rag-intel MCP server."
---

# d4-ai-rag-intel CLI

Global repository policy, impact requirements, and MCP fallback behavior are in
`AGENTS.md`. This skill covers command syntax and server lifecycle only.

Indexes stay in `~/.d4/d4-ai-rag/vectors/<env>/<vector_id>/` (override with `VECTOR_FOLDER`, `RAG_ENVIRONMENT`, `D4_RAG_HOME`). There is no `.d4-ai-rag-intel/` folder in the repo.

```bash
d4-ai-rag-intel analyze [--repo PATH] [--vector-id ID] [--force] [--embeddings] [--pdg]
d4-ai-rag-intel status
d4-ai-rag-intel list
d4-ai-rag-intel doctor
d4-ai-rag-intel clean --force [--repo ID]
d4-ai-rag-intel query "call graph"
d4-ai-rag-intel context SYMBOL
d4-ai-rag-intel impact SYMBOL --direction upstream
d4-ai-rag-intel detect_changes [--scope unstaged|staged|all|compare]
d4-ai-rag-intel trace FROM TO
d4-ai-rag-intel check [--relation IMPORTS]
d4-ai-rag-intel sql "SELECT name FROM cg_symbols LIMIT 10"
d4-ai-rag-intel explain [TARGET]
d4-ai-rag-intel pdg_query controls|flows TARGET [--variable NAME]
d4-ai-rag-intel mcp
d4-ai-rag-intel mcp stop
d4-ai-rag-intel mcp status
```

`--pdg` builds Python CFG / PDG / taint (`pdg_*` tables). Omit it to keep those
tables empty (a later non-`--pdg` analyze clears stale PDG). After `analyze` or
`clean`, reload the MCP server.

## MCP client

Install the published package with `python -m pip install "d4-ai-rag[mcp]"` and use
the same interpreter in the client configuration. Remove any GitNexus /
`user-gitnexus` MCP entry so only d4-ai-rag provides code intelligence.

```json
{
  "servers": {
    "d4-ai-rag": {
      "type": "stdio",
      "command": "C:/path/to/python.exe",
      "args": ["-m", "d4_ai_rag.intel.cli", "mcp"]
    }
  }
}
```

If `d4-ai-rag-intel` is on PATH, `d4-ai-rag-intel mcp` is also sufficient.
