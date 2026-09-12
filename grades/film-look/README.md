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
| `melara/` | Rec709_Kodak_2383_D65, Rec709_Kodak_2393_D65, Rec709_Fujifilm_3510_D65 | Juan Melara's free print-stock emulations | Rec.709 | Rec.709 |
| `thatcher/` | DJI Action 5 D-Log M to DWG.dctl | camera log to DaVinci Wide Gamut, fit to real Action 5 footage | D-Log M | DaVinci Intermediate |
| `thatcher/` | Halation, Film Grain, Film Curve, Subtractive Saturation, Gamut Compression | parameter tools, MIT | scene linear | scene linear |
| `thatcher/` | Printer Lights | per-shot exposure and balance in printer points | log | log |
| `cullen-kelly/` | Kodak 2383 (HUMAN download, see below) | print emulation built for DaVinci Wide Gamut timelines | DWG / DI | Rec.709 |
| Resolve's own `Film Looks/` | Rec709 Kodak 2383 D65.cube and friends | ships with Resolve, not copied | **Cineon Film Log**, Rec.709 primaries | Rec.709 |

## Chain A — camera-day morning (display-referred, all finished LUTs)

Project: DaVinci YRGB, not colour managed. Timeline colour space Rec.709 Gamma 2.4.

| Node | On it | Notes |
|---|---|---|
| 1 | Temporal NR | Studio only. NR before anything else so grain later is not NR'd away |
| 2 | LUT: `film-look/dji/DJI OSMO Action 5 Pro D-Log M to Rec.709 V1.cube` | the conversion. Primaries on THIS node apply before the LUT, so exposure and balance corrections here happen in log, which is where they belong |
| 3 | primaries | contrast, saturation, warmth. Taste |
| 4 | LUT: one of `film-look/melara/*.cube`, or one of `film-look/dji/looks/*.cube` | the print or the DJI look. Key output at 50 to 70 percent if it bites too hard |
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

Melara's LUTs also fit chain B at the very end, after the output transform to
Rec.709, since they expect Rec.709 in.

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
- Dewarp or narrower field of view. The 155 degree look reads action-cam regardless.

## What has been verified and what has not

Verified (2026-09-12): every fetched file matches its recorded sha256, both the
repo copy and the installed copy; the two zips list the cubes recorded in the
manifest. `validate` asks Resolve to compile each DCTL.

Not verified: how any of this LOOKS. There is no D-Log M footage on this machine
yet. The first clip off the camera is the test, and the verdict is Ryan's eyes.
