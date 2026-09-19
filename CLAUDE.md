# Claude Repository Instructions

Use [AGENTS.md](AGENTS.md) as the canonical repository policy. The
`.agents/skills/d4-rag-*` files (mirrored under `.claude/skills/d4-rag/`) provide
detailed, task-specific workflows and should be loaded only when their task
matches the request.

Use the installed `d4-ai-rag[mcp]` server (`d4-ai-rag-intel`) for indexed code
intelligence when it is available. If MCP is unavailable, report the limitation
and use verified local CLI or source inspection checks instead.

Do not use GitNexus or other parallel code-intel servers in this repository.
