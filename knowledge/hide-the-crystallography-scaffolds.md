---
id: hide-the-crystallography-scaffolds
kind: law
conflict-key: what-parts-of-a-deposited-structure-go-on-screen
status: live
supersedes: []
verified-on: 2026-09-01
asked-as:
  - what parts of a PDB structure should not be rendered
  - what is bRIL and should I show it
  - why does my receptor have an extra blob on it
  - can I just render the whole PDB file
---

**A deposited structure contains parts that exist only so the structure could be
solved. Those parts are not in the viewer's body and must never be rendered.**

Membrane proteins are routinely made crystallisable or cryo-EM-tractable by
bolting on fusion domains and binders. Rendering the file naively puts a protein
on screen that is not in the tissue being explained — the picture asserts
something false while looking authoritative.

Found in this project's own two structures:

- **5MZP residues 1001-1106** — soluble cytochrome b562 ("bRIL"), spliced into
  intracellular loop 3. The mmCIF entity name says it outright: *"Adenosine
  receptor A2a, Soluble cytochrome b562, Adenosine receptor A2a"*.
- **6VMS chain E** — scFv16, a stabilising antibody fragment holding the
  Gi complex together for imaging.

**Check before rendering any new structure:** read `_entity.pdbx_description`
in the mmCIF. A comma-separated protein name is the tell — it means a fusion.
Then list the chains and ask what each one is for. Anything whose job was to
help the experiment gets excluded by selection, not by hoping the camera
misses it.

Related: [[gpcr-interface-faces-are-90-degrees-apart]].
