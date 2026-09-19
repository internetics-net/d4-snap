# GitHub Copilot Repository Instructions

Read and follow the canonical repository policy in [AGENTS.md](../AGENTS.md).

When the d4-ai-rag MCP server is connected, use its indexed code-intelligence tools
for repository exploration. Load deferred `mcp_d4-ai-rag_*` tools with `tool_search`
and make required MCP calls in the parent session before delegating supporting work
to `/d4-ai-rag-intel`. Pass `repo` when multiple indexes are present.

Do not interpret tools omitted from a subagent as an MCP outage. Report MCP as
unavailable only after a direct call fails; include the failure and then use an
available documented CLI or source inspection check. Never invent an MCP result or
claim that an impact check passed when it did not run.
