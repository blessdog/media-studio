# 2026-09-09 — Resolve 21.1's native MCP server, and a summer reel to test it

Resolve 21.1 landed the day before with a native MCP server inside the app.
Ryan asked for the state of the art, then handed over ten clips from Photos:
*"lets test it out … lets make a fun video out of these."*

## The native server

**Tried.** Found `ResolveMCP` in the app bundle, ran it over stdio with a
hand-written JSON-RPC client while Resolve was open.

**Happened.** It works. Fourteen tools, not the 88 the press repeated; the
core is `run_script`, a sandboxed Python 3.14 with `resolve` and `project`
injected, plus the type stub, the README and the changelog as tools.
`import os` inside the sandbox raises. Report: `../RESOLVE-21.1-AGENTIC.md`.

**Mechanism.** Blackmagic chose "code as the tool": the agent reads the
`.pyi` and writes Python, instead of one MCP tool per API method. That is the
opposite shape from the vendored third-party server, which is now about 160
releases behind upstream.

**Verdict.** Open, Ryan's: which server Claude Code holds, whether
`run_script_unsafe` is acceptable, and that the LUT/DCTL generators stay
unused under "agents apply, Ryan authors".

## The summer reel

**Tried.** Ten clips dragged from Photos into the chat, cut on an 80 BPM grid
(the SP-404 in one clip reads 80), compiled from a Story IR, read back through
the native server, rendered on the mini. Job: `../../jobs/summer-reel/`.

**Happened.** The dragged files were derivative JPEGs and the library's
originals folder was empty: iCloud-optimised. `osxphotos export
--download-missing` pulled the ten `.mov` files in 25 s once the terminal was
granted Photos access. `build.py` conformed them (portrait scale, landscape
blurred fill, loudnorm to −18 LUFS), wrote the IR, compiled
`summer-reel@058a7a33`. `run_script` read the timeline back and matched the IR
item for item; on a duplicate, `AddTransition` put a 20-frame cross dissolve
on the cut into the bear. The mini encoded the whole reel in 7 s.

![the ten in-points](../../jobs/summer-reel/evidence/cut-points-10.png)

**Mechanism of the one failure.** The first compile had the cave and the
concert swapped: two landscape clips mislabeled from their filmstrips, so a
six-beat "singer" slot showed rock. No check caught it. Extracting the actual
in-point frames did, in one look. A cut list wants its in-point frames as
evidence before compile, not after.

**Verdicts.** Every cut is Ryan's. Beyond the cuts: blurred fill or centre
crop for the three landscape clips; whether the dissolve on the trial copy
is wanted, which would make transitions an IR field; which track goes under
it, if any.

Store: `the-native-resolve-mcp-server-works-over-stdio` (verdict, extended
today), `photos-library-originals-come-down-with-osxphotos` (procedure).
