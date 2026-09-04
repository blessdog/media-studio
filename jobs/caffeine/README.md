# Job: how caffeine actually works

**Deliverable:** a visual explainer. Ryan narrates to camera; this job supplies
the visuals of the thing he is describing — the striatal A2AR–D2R heterotetramer
pre-coupled to adenylyl cyclase 5.

**Why it exists.** The standard explanation — *adenosine makes you sleepy,
caffeine blocks the receptor, sleepiness has nowhere to go* — is where every
other caffeine video stops, including [RCSB PDB-101's own](https://pdb101.rcsb.org/learn/videos/caffeine-and-adenosine-antagonist-and-agonist).
That video is the null. The heterotetramer and the AC5 pre-coupling are the part
nobody has animated, and they are the only reason to make another one.

**Register (Ryan, 2026-09-01):** general public, not medical students. Clarity of
message over molecular rigor — *"it can be a stick and some fucking noodles
swirling around"*. Good visuals make the video more appealing, but conveying the
message is the only requirement. Do not bog the film down in what was and wasn't
crystallographically determined.

---

## The narration, and what is on screen for each line

| # | Ryan's line | Visual |
|---|---|---|
| 1 | concentrated in the striatum, on GABAergic striatopallidal neurons of the indirect pathway | locate, descend to membrane |
| 2 | those same neurons predominantly co-express D2 | two receptor species, one membrane |
| 3 | the two receptors physically associate into heteromers | they find each other; TM4/TM5 interface closes |
| 4 | a tetrameric complex | two homodimers, TM6 interfaces, rhombic |
| 5 | pre-coupled to adenylyl cyclase type 5 | **AC5 is already there** — it does not arrive |
| 6 | adenosine at A2A reduces affinity *and* intrinsic efficacy of dopamine at D2 | the allosteric hit crosses the interface |
| 7 | Gs/olf raises cAMP, Gi lowers it, converging on the same cyclase | two arms, one target, opposed |
| 8 | caffeine blocks that allosteric modulation | occupancy at A2A; beat 6 stops firing |
| 9 | blocking A2A enhances D2-mediated locomotor activation | consequence |

Beats **5** and **6** are the differentiators. Beat 6 is the one the standard
explainer has never shown.

## Status

| Beat | State |
|---|---|
| 3–5, 7 assembly + pre-coupling | **works** — `scenes/tetramer-mechanism.py` |
| 6, 8 allosteric transmission | **not legible** — see below |
| 1–2, 9 | not started |

**Known defect, beat 6.** The dopamine marker is anchored to D2 Asp114, which
sits *inside* the helical bundle, and the pulse travels between two enclosed
pockets — so emissive markers are lighting the interior of the protein and
cannot be seen. The fix is not a brighter emitter: route the transmission along
the *outside* of the TM4/TM5 interface, where the contact actually is, or make
the front protomer translucent for that beat.

Also open: the close-up dolly distance (`CLOSE = WIDE * 0.62`) was chosen by
feel and overshoots — it should be derived from the ligand's size the way the
wide shot is derived from the complex's. And Gi is visually the largest object
in frame, pulling the eye off the subject.

## Layout

```
complex.py            this job's structural spec: which receptors, which
                      helices, which arrangement, which scaffolds to hide.
                      Run it standalone to check the geometry without Blender.
scenes/               Blender scene scripts, run via tools/forge-blender.py
structures/           pinned PDB/mmCIF — renders work offline, RCSB uptime
                      is not a dependency
evidence/             stills a claim actually cites (outputs/ is gitignored)
research.md           the prior-art + parts-list report, every ID verified
                      against the live RCSB API
```

The reusable half lives outside this job: `blender/lib_membrane.py` (membrane
orientation, interface faces, Kabsch superposition — no molecule knows its
name), plus `blender/prep-opm.py` and `blender/prep-alphafold.py`.

## Run it

```bash
python3 jobs/caffeine/complex.py                     # solve + check geometry, no Blender
.venv/bin/python tools/forge-blender.py caffeine \
    jobs/caffeine/scenes/tetramer-mechanism.py --frames 288 --size 1280x720
```

Renders land in `outputs/projects/caffeine/forge/blender/` (gitignored).

## The three numbers this job earned

- **94°** — the angle between the TM6 and TM4/TM5 faces on both receptors.
  Ferré et al. describe a *linear* arrangement; at 94° an internal protomer
  bonded by TM6 on one side and TM4/TM5 on the other must turn a corner, so a
  straight tetramer is not available to the molecule. The published figure is a
  schematic of connectivity. The real complex is a rhombus.
  → `knowledge/gpcr-interface-faces-are-90-degrees-apart.md`
- **1.8 Å** — the separation between the adenosine and caffeine centroids after
  superposition (RMSD 1.62 Å over 168 shared TM α-carbons). Adenosine is
  resolved only in 2YDO and caffeine only in 5MZP, so "they compete for the same
  site" is normally an animator's assertion. Here it is a measurement from two
  independent structures. **This belongs in the narration.**
- **87.9%** — the fraction of AC5's TM α-carbons inside the bilayer slab after
  orientation. OPM has no AC5 entry, so the normal was derived from its own
  helix geometry; below 85% the orientation would be rejected rather than shown.
