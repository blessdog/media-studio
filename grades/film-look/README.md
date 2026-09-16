# film-look — the Osmo Action 5 Pro film grade, from free finished tools

Writer: this session (2026-09-12), then whoever changes a node. Reader: Ryan on
the day the camera lands, and the agent that applies the saved grade later.
Fails when wrong: a node fed the wrong colour space, which looks like a bad
grade and is actually a wrong transform.

Everything here is a downloaded, already-tuned asset. Nothing is hand-rolled.
`manifest.json` is the provenance record (source URL, upstream commit or date,
sha256, license) and `tools/grade-library.py` fetches, installs and verifies it.

    python3 tools/grade-library.py fetch      # into grades/film-look/assets/
    python3 tools/grade-library.py install    # into Resolve's LUT folder, film-look/
    python3 tools/grade-library.py verify     # hashes, repo copy and installed copy
    python3 tools/grade-library.py validate   # Resolve open: compile every DCTL

Installed at `/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/film-look/`.
Resolve lists new files after **LUT browser > Update Lists**, or a restart.

## What is in the library

| Folder | File | What it is | Expects in | Gives out |
|---|---|---|---|---|
| `dji/` | DJI OSMO Action 5 Pro D-Log M to Rec.709 V1.cube | DJI's official conversion. Its header says it is the Mavic 3 Pro LUT | D-Log M | Rec.709 |
| `dji/looks/` | Mei, Ju, Zhu, Lan .cube | DJI's four finished creative looks for this camera | Rec.709 | Rec.709 |
| `melara/` | Rec709_Kodak_2383_D65, Rec709_Kodak_2393_D65, Rec709_Fujifilm_3510_D65 | Juan Melara's free print-stock emulations; the 2383 grey axis is measured identical to Resolve's shipped one | **Cineon Film Log (or ARRI LogC3), Rec.709 primaries** | Rec.709 |
| `thatcher/` | DJI Action 5 D-Log M to DWG.dctl | camera log to DaVinci Wide Gamut, fit to real Action 5 footage | D-Log M | DaVinci Intermediate |
| `thatcher/` | Halation, Film Grain, Film Curve, Subtractive Saturation, Gamut Compression | parameter tools, MIT | scene linear | scene linear |
| `thatcher/` | Printer Lights | per-shot exposure and balance in printer points | log | log |
| `cullen-kelly/` | Kodak 2383 (HUMAN download, see below) | print emulation built for DaVinci Wide Gamut timelines | DWG / DI | Rec.709 |
| Resolve's own `Film Looks/` | Rec709 Kodak 2383 D65.cube and friends | ships with Resolve, not copied | **Cineon Film Log**, Rec.709 primaries | Rec.709 |

## Chain A — camera-day morning (display-referred, all finished LUTs)

Project: DaVinci YRGB, not colour managed. Timeline colour space Rec.709 Gamma 2.4.
`tools/ingest-osmo.py` creates the project and stamps exactly this, and reads
it back. Do not set it by hand; a fresh project otherwise defaults to
"Rec.709 (Scene)".

| Node | On it | Notes |
|---|---|---|
| 1 | Temporal NR | Studio only. NR before anything else so grain later is not NR'd away |
| 2 | LUT: `film-look/dji/DJI OSMO Action 5 Pro D-Log M to Rec.709 V1.cube` | the conversion. Primaries on THIS node apply before the LUT, so exposure and balance corrections here happen in log, which is where they belong |
| 3 | primaries | contrast, saturation, warmth. Taste |
| 4 | LUT: one of `film-look/dji/looks/*.cube`, **or** for a print: CST Rec.709 Gamma 2.4 → Rec.709 gamut / Cineon Film Log, then LUT `film-look/melara/*.cube` | a print LUT fed display Rec.709 instead of log comes out too contrasty and too saturated; Melara's own instructions put the CST to log first. Key output 50 to 70 percent if it bites |
| 5 | Magic Mask, secondaries | only where something needs isolating |
| 6 | Depth Map, Lens Blur | optional, subtle, watch hair edges |
| timeline node | Film Look Creator, grain and halation only | Colour Space Override: input **and** output Rec.709 Gamma 2.4, because everything is display-referred by the time it arrives here |

Save the clip node tree as a PowerGrade named `osmo-film-look-A`, and the
timeline node as `osmo-timeline-A`. Those saved grades are what the scripting
API applies to every clip afterwards (ApplyGradeFromDRX, SetLUT, SetCDL).

## Chain B — scene-referred (DaVinci Wide Gamut), more range, one trap

Project: DaVinci YRGB Color Managed, timeline DaVinci Wide Gamut / Intermediate,
output Rec.709 Gamma 2.4. Set every Osmo clip's input colour space to
**Bypass** so Resolve does not also try its own D-Log guess.

| Node | On it | Notes |
|---|---|---|
| 1 | Temporal NR | as above |
| 2 | DCTL: `film-look/thatcher/DJI Action 5 D-Log M to DWG.dctl` | output DaVinci Intermediate, DaVinci Wide Gamut. **Not** the CST's "DJI D-Log" entry, which is the older Mavic curve |
| 3 | DCTL: `Printer Lights.dctl` or CDL | per-shot exposure and balance, in log |
| 4 | CST: DaVinci Intermediate to Linear (same gamut) | the Thatcher effects want linear |
| 5 | DCTL: `Subtractive Saturation.dctl`, then `Halation.dctl` | linear in, linear out |
| 6 | CST: Linear to DaVinci Intermediate | back to log for the print |
| 7 | **Print, two choices** | (a) Cullen Kelly 2383: DWG in, Rec.709 out, done. (b) Resolve's shipped Kodak 2383: **first** a CST from DaVinci Wide Gamut / Intermediate to **Rec.709 gamut with Cineon Film Log gamma**, then the LUT. Feeding the shipped LUT DaVinci Intermediate directly is the mistake every forum thread on this subject is about |
| timeline node | Film Look Creator grain and halation, or Thatcher `Film Grain.dctl` | if using FLC, set its colour space to what enters it |

Melara's LUTs go exactly where Resolve's shipped 2383 goes in node 7 (b): after
the CST to Rec.709 gamut / Cineon Film Log. They are numerically the same curve.

## Chain C — Ryan's approved look (utility-dctls, scene-linear)

Approved 2026-09-12 on iPhone clip IMG_0006: *"img-0006-rich-halation-grain-400.mp4 looks good."*
Built only from the utility-dctls DCTLs, wired in the clip's Fusion comp by
`jobs/film-look-mini/dctl_film_mini.py`, which builds this recipe when none is named.
The project is colour managed with a Rec.709 / Linear timeline and Rec.709 / Gamma 2.4 output.

| stage | DCTL | settings |
|---|---|---|
| 1 | Clamp | min 0, max off |
| 2 | Halation | reflection exposure lost -5 |
| 3 | Clamp | min 0, max off (stops speckles on saturated colour) |
| 4 | Film Grain (negative) | D max 2.6, 400 grains per pixel |
| 5 | Multiplication Function | gain solved by `film_chain.py` so 0.18 stays 0.18 |
| 6 | Film Curve (print) | gamma 2.8, D min 0.06, D max 3.2 |

Knobs and what they do, measured: `jobs/film-look-mini/evidence/2026-09-12-img-0006-knob-ladder-sheet.jpg`.
Reference frame: `evidence/2026-09-12-approved-look-img-0006-before-after.jpg`.

**Osmo D-Log M** (`--input dji-action5-dlogm`, 2026-09-16). Colour management has no D-Log M input, so
two stages run ahead of stage 1, and the clip's input is set to `Linear` so Resolve passes the code values through:

| stage | DCTL | settings |
|---|---|---|
| 0 | Fusion Resize | to the timeline size, so grain is drawn on the pixel grid the look was approved on |
| A | DJI Action 5 D-Log M to DWG | Output Transfer Function Linear, Output Color Gamut DaVinci Wide Gamut |
| B | Gamut Primaries Conversion | DaVinci Wide Gamut to Rec. 709 |

First clip: `jobs/film-look-mini/evidence/2026-09-16-osmo-dji-0001-dlogm-approved-look-sheet-scaled-first.jpg`
(grain 3.28 against the approved 3.60). The `...-sheet.jpg` beside it was made before stage 0 existed and shows
the thin grain (1.60). No verdict from Ryan on that clip. On the second clip (0004, indoor, about ISO 3200) he
rejected it: "looks like shit" (`knowledge/the-approved-film-look-fails-on-osmo-clip-0004.md`). Do not use Chain C
as the Osmo default.

## Candidates not yet in the library (searched 2026-09-16)

Found after Chain C failed on Osmo clip 0004. Nothing below is installed or rendered yet. Status words:
CHECKED (read or verified here), REPORTED (the vendor or a review says so).

| Candidate | What it is | Fits this lane because | Status |
|---|---|---|---|
| **spektrafilm OFX** 0.4.7 ([site](https://spektrafilm.114c.de/), [repo](https://github.com/chaert-s/spektrafilm-ofx)) | a free spectral film simulation: camera negative, then print, with grain, halation, diffusion. 35 stocks incl. Kodak Vision3 50D/250D/200T/500T; prints 2383, 2393 | a finished emulator instead of parts we wire. Its Input Color Space takes DaVinci Intermediate WideGamut, which the D-Log M DCTL outputs. Output Role "Display Out SDR" to Rec.709 Gamma 2.4, or "RCM/ACES" back to the working space | CHECKED: GPL-3.0; pkg signed "Developer ID Installer: Aedan Diez (3495LZ53BZ)" and notarized 2026-09-09; zip sha256 39c94770…; installs spektrafilm, spektrafilm_flow and spektrafilm_lens into `/Library/OFX/Plugins` (admin password); Studio only per its install notes. UNKNOWN: whether a script can add it to a Fusion comp, and under what id |
| **OpenDRT** ([repo](https://github.com/jedypod/open-display-transform)) | a free display-rendering DCTL with look presets | runs through the existing DCTL stage system, no admin | REPORTED |
| **JP-2499 DRT** ([repo](https://github.com/JuanPabloZambrano/DCTL/tree/main/2499_DRT)) | a free film-inspired image formation DCTL, not a film emulation | same | REPORTED |
| **Jamie Fenn DWG 2383 and Fuji 351** ([page](https://www.jamiefenn.com/p/free-dwg-film-emulation-luts/)) | free print LUTs for DaVinci Wide Gamut | the Chain B node 7 slot | REPORTED |
| **ProColor free 2383** ([page](https://procolor.ist/freelut/)) | a free scene-referred 2383 for DWG or ACES | same | REPORTED |
| **Mononodes free PowerGrades** ([page](https://mononodes.com/film-emulation/)) | .drx photochemical emulation | `ApplyGradeFromDRX` applies .drx by script | REPORTED |

Already here and never rendered on Osmo footage: DJI's own D-Log M cube and its four looks, Melara prints fed
Cineon, Resolve's Film Looks folder, Film Look Creator.

## The one human download

Cullen Kelly's free Kodak 2383 for DaVinci Wide Gamut sits behind an email form
at https://freelut.cullenkellycolor.com/. Save the .cube into
`grades/film-look/assets/cullen-kelly/` and run `install` again. Everything
else in the library was fetched by the tool.

## Camera settings that decide more than any node

- D-Log M, 10-bit. Always.
- 24p or 25p. 60p only for shots meant to be slowed.
- Shutter 1/48 or 1/50. Outdoors that needs ND: sunny at ISO 100 is ND64,
  overcast ND8 to ND16. DJI's ND 8/16/32/64 set fits this camera.
- Slow shutter plus max RockSteady smears. One or the other.
- Sharpness and in-camera NR at minimum.
- ISO ceiling 1600 for graded work (chosen line; reviews call 3200+ destructive).
  Clip 0004 (2026-09-16) broke four lines of this list under auto exposure: 29.97, shutter 1/110 to 1/200,
  about ISO 3200, and Ryan read the result as low light (`knowledge/osmo-clip-0004-was-shot-at-about-iso-3200.md`).
  Read a clip's settings with `exiftool -ee -u -G3 -s -n -ShutterSpeed -Dvtm_ac204_3-2-3-1 <clip>`.
- Dewarp or narrower field of view. The 155 degree look reads action-cam regardless.

## What has been verified and what has not

Verified (2026-09-12): every fetched file matches its recorded sha256, both the
repo copy and the installed copy; the two zips list the cubes recorded in the
manifest. `validate` asks Resolve to compile each DCTL.

Not verified: how any of this LOOKS. There is no D-Log M footage on this machine
yet. The first clip off the camera is the test, and the verdict is Ryan's eyes.

iPhone clips (Apple Log, Apple Log 2): the same chains apply. Chain A node 2 becomes a CST node (Apple Log → Rec.709 Gamma 2.4, Resolve has it natively); chain B node 2 is `thatcher/Apple Log 2 to DWG.dctl` (iPhone 17 Pro) or `Apple Log to DWG.dctl` (15/16 Pro).
