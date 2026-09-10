---
id: the-native-resolve-mcp-server-works-over-stdio
kind: verdict
conflict-key: how-does-an-agent-reach-resolve-over-mcp
status: live
supersedes: []
verified-on: 2026-09-09
scope: DaVinci Resolve Studio 21.1.0.14 on this MacBook (macOS 26), external scripting = Local, Resolve already open; measured with the vendored samuelgursky server also connected, first for ten seconds, then for a two-call session on the summer-reel project. Says nothing about a long shared session, and nothing about `File > Setup AI Assistants`, which was not run.
evidence: docs/research-raw/resolve-21.1/resolvemcp-smoke-transcript.txt (initialize, get_resolve_status, run_script returned page/project/version, sandbox refused `import os`); docs/research-raw/resolve-21.1/resolvemcp-dump-tools.json (the 14 tools); jobs/summer-reel/mcp-readback.py + jobs/summer-reel/README.md (read back a compiled 10-edit timeline item by item, DuplicateTimeline + AddTransition on the copy, GetNormalizeAudioModes); docs/RESOLVE-21.1-AGENTIC.md
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

Second measurement, same day, on `summer-reel@b9996010`: `run_script` read the compiled timeline back item by item (10 items, 900 frames, 10 markers, matching the Story IR exactly), `DuplicateTimeline` + `AddTransition({type:'Cross Dissolve', category:'simple', position:'start', duration:20})` returned a 20-frame transition item on the copy, and `GetNormalizeAudioModes` listed 14 modes. The IR-compiled timeline was left untouched.

Related: [[the-mini-renders-the-story-ir-with-ffmpeg-not-resolve]],
[[obs-camera-isolates-in-movies-iso-are-an-untouch]] (21.1's multicam APIs
are the route that claim should take).
