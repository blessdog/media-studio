---
id: resolve-exportlut-bakes-the-node-grade-not-colour-management
kind: verdict
conflict-key: can-a-resolve-grade-be-baked-into-a-lut-for-ffmpeg
status: live
supersedes: []
verified-on: 2026-09-12
scope: Resolve Studio 21.1.0, TimelineItem.ExportLUT(EXPORT_LUT_65PTCUBE) on a clip in a davinciYRGBColorManagedv2 project with a clip input colour space and a Cineon working space; the Hald-lattice bake was tried once and is not settled
evidence: two exports from two projects with different clip input spaces (Apple Log 2, Rec.709 Scene) were byte-identical, sha256 08846543...; ffmpeg lut3d with that cube missed Resolve's still by 13 to 43 levels of 255
asked-as:
  - export the Resolve grade as a LUT so ffmpeg can render it on the Mac mini
  - does ExportLUT include the input color space transform
  - render a Resolve colour grade without Resolve
---

**`ExportLUT` bakes only the node graph. It leaves out colour management: the
clip's input transform and the working-space conversion. A cube exported from a
colour-managed project cannot reproduce Resolve's picture in ffmpeg.**

Measured 2026-09-12: the Apple Log 2 clip and the iPhone SDR clip, in two
projects with different input spaces and the same Kodak 2383 on node 1,
exported byte-identical 65-point cubes. Applied in ffmpeg to each source frame,
the cube missed Resolve's still by a mean 13 to 43 levels per channel.

Second attempt, NOT settled: render an identity Hald lattice TIFF through the
same project and apply it with ffmpeg `haldclut`. It missed by 31 to 41 levels
because the lattice clip did not take the video clip's input interpretation:
with `separateColorSpaceAndGamma` on, `SetClipProperty('Input Gamma', ...)`
returned False for both 'Apple Log' and 'Rec.709', and 'Rec.709 (Scene)' was
refused as an input space for the TIFF. An input-matched lattice is the open
question, not a dead end.

Until one of those matches, grade colour renders in Resolve. Resolve on the Mac
mini (21.0.4, never launched, no licence folder) needs Studio activation for
Film Look Creator, CineFocus and temporal NR.

Related: [[a-print-lut-needs-a-cineon-working-space-in-resolve]].
