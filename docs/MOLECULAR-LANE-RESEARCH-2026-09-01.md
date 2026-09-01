# Molecular Lane: the A2A–D2 heterotetramer / AC5 complex in Blender

**Date:** 2026-09-01
**Purpose:** Ryan wants a visual explainer on how caffeine *actually* works —
not "adenosine makes you sleepy, caffeine blocks the receptor," but the
striatal A2AR–D2R heterotetramer pre-coupled to adenylyl cyclase 5, and the
allosteric hit that adenosine binding lands on dopamine's affinity and efficacy
at D2.
**Method:** Law #0 prior-art search first (7 web searches), then every
structural claim checked against the live RCSB and AlphaFold REST APIs on
2026-09-01. `[VERIFIED]` = I hit the API and read the response.
**Owner triple:** writer = this session; reader = Ryan + the next cold agent;
fails-when-wrong = we hand-model a complex whose geometry contradicts the
literature, or we re-run this PDB hunt from zero next session.

---

## Part 0 — Prior art (Law #0). Do not hand-roll any of this.

| Thing | What it is | Verdict for us |
|---|---|---|
| **Molecular Nodes** v4.5.13 (Brady Johnston) | Blender extension. Imports `.pdb`/`.mmCIF`, MD trajectories, cryo-EM density; styles and animates via Geometry Nodes; built on MDAnalysis. Blender 5.1+, macOS Apple Silicon build published. | **This is the tool.** Not installed here yet. It replaces every line of "parse a PDB and instance spheres" we would otherwise write. |
| **RCSB PDB-101 "Caffeine and Adenosine: Antagonist and Agonist"** | Existing free educational video, uses PDB `2YDO` (adenosine) and `3RFM` (caffeine). | **This is exactly the standard story Ryan is bored of.** It is also our null/control: our film has to start where theirs stops. Nobody has animated the tetramer + AC5. |
| **ChimeraX → glTF/OBJ → Blender** | The older pipeline. | **Rejected on merits, not dogma.** Exports frozen geometry; documented vertex-colour-vs-texture friction into Blender; you lose the ability to restyle or re-select atoms in Blender. Fine for one static hero prop, wrong for a lane. |
| **CHARMM-GUI Membrane Builder / Quick Bilayer** | Web service. Orients a membrane protein in a real lipid bilayer, emits `step4_lipid.pdb`. | **Use it for the membrane.** A hand-modelled slab of "lipid-looking" geometry is a lie we would have to keep re-telling; this gives real lipids, real thickness, real orientation, importable by Molecular Nodes. |
| **AlphaFold DB / AlphaFold Server (AF3)** | Free for non-commercial. Per-protein models in DB; AF3 server predicts complexes. | **Use the DB for full-length chains that no experiment covers** (see the AC5 gap below). |
| **OPM (Orientations of Proteins in Membranes)** | Database of pre-oriented membrane proteins. | Needed so all four receptors sit in the *same* membrane plane. Not yet searched in depth — open item. |

---

## Part 1 — The parts list. Every ID below was verified against the RCSB API today.

| PDB | Title | Res. | Method | Role in the film |
|---|---|---|---|---|
| `5MZP` | Stabilized A2A adenosine receptor (A2AR-StaR2-bRIL) **in complex with caffeine** | 2.1 Å | X-ray | **The money shot.** Highest-resolution caffeine-in-the-pocket structure that exists. |
| `2YDO` | Thermostabilised human A2A receptor **with adenosine bound** | 3.0 Å | X-ray | The agonist state, to cut against `5MZP`. |
| `3RFM` | Thermostabilised A2A **in complex with caffeine** | 3.6 Å | X-ray | Lower res than 5MZP; only value is that PDB-101 used it, so it is the comparison. |
| `5G53` | A2A receptor **bound to an engineered G protein** (mini-Gs) | 3.4 Å | X-ray | The active, G-protein-engaged A2A — the conformation the heterotetramer arm needs. |
| `6VMS` | **D2 dopamine receptor–G protein complex in a lipid membrane** | 3.8 Å | cryo-EM | D2 in its active, Gi-coupled state, *and already in a bilayer*. |
| `6CM4` | D2 receptor bound to risperidone | 2.87 Å | X-ray | Inactive-state D2, higher resolution. The "before" pose. |
| `8SL3` | **Human adenylyl cyclase 5 in complex with Gβγ** | 7.0 Å | cryo-EM | The only experimental AC5. See the resolution warning below. |
| `8SL4` | **Dimeric form of human adenylyl cyclase 5** | 7.0 Å | cryo-EM | AC5 dimer — relevant because the model says two AC5 per unit. |
| `6R3Q` | Membrane adenylyl cyclase bound to activated Gs | 3.4 Å | cryo-EM | Different AC isoform, but the best atomic picture of *AC engaged by Gs*. Use for the Gs-docking beat. |

**AlphaFold DB, verified live (all v6):**
`P29274` Adenosine receptor A2a · `P14416` D(2) dopamine receptor ·
`O95622` Adenylate cyclase type 5.

### `[VERIFIED]` The AC5 resolution problem — and why it matters on screen

`8SL3` and `8SL4` are **7.0 Å**. At 7 Å you can see the 3×4 array of twelve
transmembrane helices as tubes; you cannot see a side chain, and there are no
atoms to render honestly. The paper's own approach was to fit an **AlphaFold2
model of AC5** into that 7 Å envelope. So our AC5 hero asset is
`AF-O95622` (AlphaFold, full length) **posed against** the `8SL3` map — never
a claim of an experimental atomic AC5. If we render AC5 at the same visual
fidelity as the 2.1 Å caffeine pocket, the picture asserts a precision that
does not exist.

---

## Part 2 — The complex geometry, from the literature

There is **no experimental structure of the A2AR–D2R heterotetramer.** The
quaternary model is a pharmacological/biochemical inference — Ferré, Navarro
and colleagues — with the interfaces mapped by **TM-interfering peptides**
(synthetic peptides matching one transmembrane helix, which disrupt the
complex if that helix is at an interface), not by crystallography.

`[VERIFIED — Front. Pharmacol. 2018, Ferré et al., "Essential Control of the
Function of the Striatopallidal Neuron by Pre-coupled Complexes…"]`

- **Minimal functional unit:** two A2AR–D2R heterotetramers + **two AC5**.
- **One heterotetramer = 4 protomers:** two A2AR + two D2R, as **two homodimers**.
- **A2AR homodimer interface: symmetrical TM6.**
- **D2R homodimer interface: symmetrical TM6.**
- **A2AR–D2R heteromer interface: symmetrical TM4/TM5.**
- **Arrangement is LINEAR:** two *internal* interacting protomers (one A2AR,
  one D2R) flanked by two *external* non-interacting protomers.
- **G proteins hang off the external protomers:** Golf (a Gs isoform) on A2AR,
  Gi/o on D2R. Both converge on the same AC5 — that is the "canonical Gs–Gi
  antagonistic interaction at the level of AC5."
- **Gβγ released from Gi** is a second, separate inhibitory route (via PLC),
  independent of the canonical AC5 inhibition. The `8SL3` structure shows Gβγ
  binding the coiled-coil that links AC5's TM region to its catalytic core.
- **AC5 contact surface (peptide competition, Navarro et al. 2018):** A2AR
  **TM1, TM5, TM6**; D2R **TM1, TM4, TM5, TM6**.

### The story beat this unlocks
The standard explainer's causal chain is `caffeine → blocks A2A → less
sleepiness`. The real chain, and the one Ryan's n-of-1 matches, is:
`adenosine at A2A → allosterically lowers dopamine's affinity AND intrinsic
efficacy at D2 (within the tetramer) → plus Golf raises cAMP at AC5 against
Gi lowering it → indirect-pathway striatopallidal neuron gets more excitable →
"brakes on." Caffeine removes the allosteric brake-press, so dopamine at D2
works better.` **Caffeine is not a stimulant; it is a disinhibitor of
dopamine's own signal.**

---

## Part 3 — Open questions before any build

1. **Assembly method for the tetramer.** Options: (a) manually dock four
   experimental protomers onto the TM6/TM4-5 interface spec above in Blender;
   (b) AlphaFold Server / AF3 prediction of the multimer and check whether it
   reproduces the published interfaces; (c) look for a published coordinate
   file from the Ferré/Casadó groups. Not yet searched — **do (c) first.**
2. **OPM orientation** so all protomers share one membrane plane.
3. **Honesty layer.** The film mixes 2.1 Å fact with 7 Å envelope with
   inferred quaternary model. Needs a visual grammar that distinguishes them.
4. **Does this become a repo lane?** `blender/` currently holds one scene
   (`orbit-cube.py`); `studio/blender.py` runs Blender headless
   `--factory-startup`, which **will not load Molecular Nodes**. That flag is a
   real conflict to resolve before a molecular scene can render in the lane.

---

## Sources

- Molecular Nodes — https://bradyajohnston.github.io/MolecularNodes/ · https://extensions.blender.org/add-ons/molecularnodes/
- Ferré et al. 2018, Front. Pharmacol. — https://www.frontiersin.org/articles/10.3389/fphar.2018.00243/full
- Navarro et al. 2018, BMC Biology (pre-coupled complexes) — https://pubmed.ncbi.nlm.nih.gov/29593213/
- Yen et al. 2024, Nat. Struct. Mol. Biol. (AC5–Gβγ) — https://www.nature.com/articles/s41594-024-01263-0
- RCSB entries — https://www.rcsb.org/structure/5MZP · /5G53 · /6VMS · /8SL3
- RCSB PDB-101 caffeine video — https://pdb101.rcsb.org/learn/videos/caffeine-and-adenosine-antagonist-and-agonist
- CHARMM-GUI Membrane Builder — https://pubs.acs.org/doi/pdf/10.1021/acs.jctc.2c01246
- AlphaFold — https://alphafold.ebi.ac.uk/
