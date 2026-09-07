---
id: an-rsync-remote-path-with-a-space-arrives-as-two-arguments
kind: refuted
conflict-key: how-to-rsync-to-a-remote-path-containing-a-space
status: live
supersedes: []
verified-on: 2026-09-07
mechanism: rsync hands the remote path to the remote login shell as text, the shell word-splits it, and the far-side rsync (openrsync on macOS 26) starts with two arguments where it expected one
asked-as:
  - why does rsync to the mini fail with server receiver mode requires two argument
  - how do I rsync into a folder with a space in its name on the Mac mini
  - why did the DaVinci Resolve copy to BleSSD fail
  - rsync poll hangup on nonblocking write
---

**Dead end: `rsync -a src/ mini:/Volumes/BleSSD/Applications/DaVinci Resolve/`.
The far side sees `.../DaVinci` and `Resolve/` as two arguments and refuses:
`server receiver mode requires two argument`, then `poll: hangup on
nonblocking write` on this side.**

Measured 2026-09-07 while copying Resolve Studio (10 GB) from the MacBook to
the mini. The local rsync is fine with the space; the remote path is passed
through the login shell unquoted. macOS 26 ships openrsync, which does not
take `--protect-args`, so the usual fix is unavailable.

What works: give the remote side a path with no spaces and let a symlink
supply the spaced name where the app expects it.

    rsync -a src/ mini:/Volumes/BleSSD/Applications/DaVinciResolve/
    ssh mini 'ln -sfn /Volumes/BleSSD/Applications/DaVinciResolve "/Applications/DaVinci Resolve"'

Same family as the studio's own NO SPACES rule for media paths handed to
Resolve (AGENTS.md hard doctrine): a space in a path is a bug-in-waiting on
every hop that goes through a shell.
