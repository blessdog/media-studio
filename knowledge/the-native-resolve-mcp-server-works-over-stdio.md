---
id: the-native-resolve-mcp-server-works-over-stdio
kind: verdict
conflict-key: how-does-an-agent-reach-resolve-over-mcp
status: live
supersedes: []
verified-on: 2026-09-09
scope: DaVinci Resolve Studio 21.1.0.14 on this MacBook (macOS 26), external scripting = Local, Resolve already open; measured with the vendored samuelgursky server also connected for about ten seconds of overlap. Says nothing about a long shared session, and nothing about `File > Setup AI Assistants`, which was not run.
evidence: docs/research-raw/resolve-21.1/resolvemcp-smoke-transcript.txt (initialize, get_resolve_status, run_script returned page/project/version, sandbox refused `import os`); docs/research-raw/resolve-21.1/resolvemcp-dump-tools.json (the 14 tools); docs/RESOLVE-21.1-AGENTIC.md
asked-as:
  - does DaVinci Resolve 21.1 have a built-in MCP server
  - how do I connect Claude Code to Resolve natively
  - what tools does the native Resolve MCP server expose
  - where is ResolveMCP on disk
---

**Resolve Studio 21.1 ships its own MCP server and it works: the binary at
`/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Applications/ResolveMCP`
speaks stdio JSON-RPC (protocol 2024-11-05), and `run_script` executed Python
against the open Resolve and returned the current page, project and version.**

What it is, measured: 14 tools, not the 88 the press repeated (that number is a
third-party server). The core is `run_script`, a sandboxed Python 3.14 with
`resolve` and `project` pre-injected and `os`/`sys`/network/subprocess refused;
`run_script_unsafe` lifts the sandbox. Around it: `get_scripting_api` /
`search_scripting_api` (the `.pyi` stub), `get_scripting_docs` (the README),
`get_whats_new` (the changelog since a version), status/launch, and LUT/DCTL
authoring into `.../LUT/MCP`. `ResolveMCP --dump-tools` prints the tool list
without connecting, and reports Resolve "not running" even when it is; the
live `initialize` handshake is the truthful one.

How it reaches Claude Code: `File > Setup AI Assistants` inside Resolve writes
entries into `~/.claude.json`, `~/.codex/config.toml`
(`[mcp_servers.davinci_resolve]`), `~/.gemini/config/mcp_config.json` and
`~/.grok/config.toml`; Claude Desktop gets the `.mcpb` extension bundle. None
of that was run here; `.mcp.json` still names the vendored samuelgursky server
because replacing it is a locked decision Ryan owns (CLAUDE.md).

Related: [[the-mini-renders-the-story-ir-with-ffmpeg-not-resolve]],
[[obs-camera-isolates-in-movies-iso-are-an-untouch]] (21.1's multicam APIs
are the route that claim should take).
