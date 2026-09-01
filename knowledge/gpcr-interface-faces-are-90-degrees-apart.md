---
id: gpcr-interface-faces-are-90-degrees-apart
kind: verdict
conflict-key: what-shape-is-the-a2a-d2-heterotetramer
status: live
supersedes: []
scope: >
  Class A GPCR heteromers assembled from real coordinates, specifically the
  A2AR-D2R heterotetramer built from 5MZP (A2A) and 6VMS (D2). Measured on CA
  atoms of the UniProt-annotated TM helices of P29274 and P14416.
evidence: >
  blender/lib_complex.py prints it; measured 2026-09-01. TM6 face vs TM4/TM5
  face, as XY unit vectors from the TM bundle axis: 93.5 deg on A2A, 96.2 deg
  on D2. Commit 109eb1d.
verified-on: 2026-09-01
asked-as:
  - what shape is the A2A D2 heterotetramer
  - is the receptor tetramer linear or a rhombus
  - how do I arrange four GPCR protomers by their TM interfaces
  - why can't I lay the heterotetramer out in a straight line
---

**The published "linear arrangement" of the A2AR-D2R heterotetramer cannot be
built from real coordinates. The tetramer is a rhombus.**

Ferré et al. 2018 (Front. Pharmacol. 9:243, Fig 3B) describes "a linear
arrangement with two internal interacting A2AR and D2R protomers and two
external non-interacting protomers", with symmetrical TM6 homodimer interfaces
and a symmetrical TM4/TM5 heteromer interface.

**Mechanism:** on a class A GPCR bundle those two faces are ~94 degrees apart
around the bundle axis, not 180. An internal protomer bonds via TM6 on one side
and TM4/TM5 on the other, so it MUST turn a corner. Collinearity is not
available to the molecule. Measured: 93.5 deg (A2A, 5MZP), 96.2 deg (D2, 6VMS).

**How to build it instead:** walk the interface chain. Rotate each protomer so
the face naming its bond points at the partner it bonds to, then let the next
bond direction fall out of that protomer's own geometry. Result: 38 A between
every bonded pair, 82 A across, rhombic. Do NOT solve for a line and absorb the
error — the residual is 94 degrees and would put the interfaces nowhere near
each other.

The paper's figure is a schematic of CONNECTIVITY, and it is correct as that.
It is not a statement about shape, and reading it as one produces a complex
that no membrane could hold.

Related: [[null-before-the-metric]] — the straight line was the plausible story;
the measured angle was the control that killed it.
