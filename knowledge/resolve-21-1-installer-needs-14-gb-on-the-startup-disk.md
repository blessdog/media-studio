---
id: resolve-21-1-installer-needs-14-gb-on-the-startup-disk
kind: verdict
conflict-key: how-much-space-does-resolve-need-to-install-on-the-mini
status: live
supersedes: []
verified-on: 2026-09-12
scope: DaVinci_Resolve_Studio_21.1_Mac.dmg ("Install Resolve 21.1.pkg", 11 GB) on macOS; the Mac mini (M1, 8 GB, internal disk 228 GB, external APFS SSD "BleSSD" 1.8 TB over USB)
evidence: the package's Distribution file (installKBytes summed over five pkg-refs, no <domains> element, volume-check pm_volume_check); `diskutil info /System/Volumes/Data` on the mini; `ls -ld "/Applications/DaVinci Resolve"` on the mini
asked-as:
  - why won't Resolve install on the Mac mini
  - how much disk space does DaVinci Resolve 21.1 need to install
  - can the Resolve installer install to an external drive
  - where is DaVinci Resolve installed on the Mac mini
---

**The Resolve 21.1 Studio installer needs about 14.1 GB free on the STARTUP
disk and cannot be pointed at another drive. On the Mac mini that is the
internal disk, whatever the Resolve folder links to.**

Measured 2026-09-12:

| fact | value |
|---|---|
| installKBytes, five pkg-refs summed | 14,771,117 KB = 14.1 GB (main manifest 13.5 GB) |
| install locations the package allows | startup disk only (no `<domains>` element) |
| mini internal disk free | 4.9 GB |
| mini `/Applications/DaVinci Resolve` | symlink to `/Volumes/BleSSD/Applications/DaVinciResolve` (old 21.0.4, 8.8 GB, on BleSSD) |
| installed footprint on the MacBook | 10 GB app folder + 1.2 GB in `/Library/Application Support/Blackmagic Design` |

Consequence: deleting the old Resolve frees nothing on the internal disk, and
clearing caches plus staged macOS updates recovers only about 5.5 GB. Ryan
chose on 2026-09-12 to make room by moving the 57 GB Spectrasonics STEAM
library to BleSSD with Spectrasonics' documented procedure.

Related: [[resolve-exportlut-bakes-the-node-grade-not-colour-management]].
