---
id: compile-py-still-uses-project-setsetting-resolve
kind: open
conflict-key: should-we-compile-py-still-uses-project-setsetting-resolve
status: live
supersedes: []
proven: false
verified-on: 2026-09-12
asked-as:
  - compile.py still uses Project.SetSetting; Resolve 21.1 deprecates it for SetSettings({...})
  - compile py still uses project setsetting resolve
---

**This is a PLAN, not a finding. `proven: false`. Do not build against it.**

## compile.py still uses Project.SetSetting; Resolve 21.1 deprecates it for SetSettings({...})

**Why it matters:** README.md line 595 in the installed Scripting docs marks SetSetting/GetSetting deprecated; still works today, will not forever; migrate when compile.py is next touched

Bookmarked 2026-09-12 at the moment of deferral, because the record of a deferral is what fails, not the decision to defer.
