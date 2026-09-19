---
name: d4-rag-guide
description: "d4-ai-rag-intel MCP tools, d4rag:// resources, and SQL over structural.db."
---

# d4-ai-rag-intel guide

Global repository policy is in `AGENTS.md`. This skill is the MCP tool, resource,
and SQL reference; it does not repeat task workflows.

MCP server: `d4-ai-rag-intel mcp` (optional extra `d4-ai-rag[mcp]`). `repo` is the registry
database id / vector_id.

## Tools

| Tool | Role |
|------|------|
| `list_repos` | Paginated registry + staleness |
| `query` | Process-grouped concept search |
| `context` | Symbol 360-degree view |
| `impact` | Multi-hop blast radius |
| `detect_changes` | Git diff to symbols / flows |
| `trace` | Shortest CALLS path |
| `check` | Directed cycles |
| `sql` | Read-only SELECT/WITH |
| `explain` | Taint findings after `analyze --pdg` |
| `pdg_query` | CDG controls / REACHING_DEF flows |
| `get_context` | RAG chunks without chat LLM |

## Resources

`d4rag://repos`, `d4rag://repo/{name}/context|clusters|cluster/{id}|processes|process/{id}|schema`

Read `d4rag://repo/{name}/schema` before using `sql`. Submit one read-only
`SELECT` or `WITH ... SELECT` statement, never write operations.

The installed MCP runtime is `d4-ai-rag[mcp]`; configure it with
`python -m d4_ai_rag.intel.cli mcp`.
