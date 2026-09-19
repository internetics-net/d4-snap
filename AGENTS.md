# Agent Policy (d4-ai-rag-intel)

This file is the canonical repository policy for coding agents. Client-specific
files should point here instead of duplicating these rules.

## Scope and precedence

- Apply these rules to work in this repository.
- Follow higher-priority system and user instructions when they conflict with this
  file.
- Do not fabricate tool results, APIs, symbols, paths, versions, test results, or
  runtime behavior.

## Required workflow

- Before editing a function, class, or method, run d4-ai-rag-intel `impact` with
  `direction: "upstream"`. Report direct callers, affected processes, and risk.
- Warn the user before proceeding when impact reports HIGH or CRITICAL risk.
- Before committing, run `detect_changes` and confirm changed symbols and execution
  flows match the intended scope. This repository uses `main` as its default
  comparison branch (override if the repo default differs).
- Prefer d4-ai-rag-intel `query` and `context` for unfamiliar indexed code. Use ordinary
  file inspection when MCP is unavailable or cannot answer the query.
- Pass `repo` when more than one indexed repository is registered.

## MCP and index lifecycle

- In clients that defer tools, use `tool_search` to load the relevant
  `mcp_d4-ai-rag_*` tool before concluding that MCP is unavailable. Make at least
  one direct MCP call as the availability check.
- A tool omitted from a subagent invocation is a tool-exposure limitation, not
  evidence of an MCP server outage. Run required MCP calls in the parent session
  when the parent exposes them.
- Check index freshness before relying on graph results. Run `d4-ai-rag-intel analyze` when
  the index is stale, then reload the d4-ai-rag MCP server.
- After `d4-ai-rag-intel analyze` or `d4-ai-rag-intel clean`, reload MCP before using its tools again.
- If a direct MCP call fails, report the concrete failure and do not present a
  guessed result as evidence. An equivalent CLI or source check may be used when
  available.
- Do not treat a missing impact result as proof that a change is safe.
- Do **not** use GitNexus (or any other parallel code-intel MCP) alongside d4-ai-rag.

## SQL and security

- Read `d4rag://repo/{name}/schema` before using the MCP `sql` tool.
- Submit one read-only `SELECT` or `WITH ... SELECT` statement only. Do not use
  `INSERT`, `UPDATE`, `DELETE`, `PRAGMA`, or `ATTACH` through MCP SQL.
- Use `explain` and `pdg_query` only after indexes were built with `--pdg`; absence
  of a finding is not proof of safety.

## Repository references

- MCP resources: `d4rag://repos` and `d4rag://repo/{name}/context`, `clusters`,
  `processes`, and `schema`.
- CLI reference: `.agents/skills/d4-rag-cli/SKILL.md` (also under
  `.claude/skills/d4-rag/`).
- Task-specific workflows: `.agents/skills/d4-rag-{exploring,debugging,guide,impact,pdg}/SKILL.md`.
- The installed MCP runtime is `d4-ai-rag[mcp]`, launched with
  `python -m d4_ai_rag.intel.cli mcp` or `d4-ai-rag-intel mcp`.
