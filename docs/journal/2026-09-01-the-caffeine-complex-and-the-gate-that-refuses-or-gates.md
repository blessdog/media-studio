# 2026-09-01 — The caffeine complex, and the gate that refuses or-gates

Two things happened today. One was building a molecular lane from nothing to an
animated A2A–D2 heterotetramer. The other was Ryan catching me handing him
arbitrary decisions twice in one session, and wiring a gate so it cannot happen
a third time. The second one is the more valuable entry.

---

## Era: the molecular lane

### Tried — search before building anything
**Happened.** Molecular Nodes exists: a Blender extension that imports PDB and
mmCIF, builds cartoon/ribbon geometry through Geometry Nodes, and plays back MD
trajectories. Also found: OPM (membrane-oriented structures), CHARMM-GUI
(bilayer construction), and — importantly — RCSB PDB-101's *existing* caffeine
explainer using 2YDO and 3RFM.
**Mechanism.** The PDB-101 video is the null. It tells the standard story
(caffeine blocks the sleepy receptor) very well. Knowing it exists is what
defined the whole brief: the heterotetramer and AC5 layer is the part nobody has
animated, and that is the only reason to make another caffeine video.
**Verdict — law.** Nothing here parses a coordinate file by hand. See
`docs/MOLECULAR-LANE-RESEARCH-2026-09-01.md`.

### Tried — dropping `--factory-startup` to load the add-on
**Happened.** Didn't have to. Blender's `--addons` flag enables a declared list
*on top of* factory startup.
**Mechanism.** `--factory-startup` skips user preferences, and add-ons are
enabled in preferences — so the flag and the add-on look mutually exclusive.
They aren't. Declaring the add-on set as a constant in `studio/blender.py` is
strictly better than inheriting it from whatever was clicked in the UI: renders
stay a pure function of the scene script, and the enabled set is now versioned.
**Verdict — law.** Never trade determinism for a dependency without checking for
the surgical flag first.

### Tried — assembling the tetramer as the literature draws it
**Happened.** It doesn't fit. Ferré et al. 2018 describes "a linear arrangement";
measured on real coordinates, the TM6 face and the TM4/TM5 face sit **93.5° apart
on A2A and 96.2° on D2**, not 180°.
**Mechanism.** An internal protomer bonds via TM6 on one side and TM4/TM5 on the
other. With those faces perpendicular, it must turn a corner — collinearity is
not available to the molecule. The published figure is a schematic of
*connectivity*, and it is correct as that. It is not a statement about shape.
**Verdict — law.** `knowledge/gpcr-interface-faces-are-90-degrees-apart.md`.
Walk the interface chain and let measured face angles set the geometry. The
result is a rhombus: 38 Å between every bonded pair, 82 Å across — and a better
image than the diagram everyone copies.

### Tried — rendering the deposited files as they come
**Happened.** 5MZP entity 1 is literally named *"Adenosine receptor A2a, Soluble
cytochrome b562, Adenosine receptor A2a"* — a bRIL fusion spliced into ICL3. And
6VMS chain E is scFv16, a stabilising antibody fragment.
**Mechanism.** Membrane proteins are made tractable by bolting on scaffolds.
Rendering them puts confident-looking protein on screen that is not in the
viewer's body. Same error class, later found again in the AlphaFold AC5 model:
21% of it sits below pLDDT 70, which is the model saying *I don't know*, drawn
as sprawling loops.
**Verdict — law.** `knowledge/hide-the-crystallography-scaffolds.md`. The tell
is a comma-separated protein name in `_entity.pdbx_description`.

### Tried — eyeballing a camera distance multiplier
**Happened.** Zoomed the wrong way and made the framing worse.
**Mechanism.** I reasoned correctly that a 16:9 frame constrains on the vertical
axis, then picked the number by feel instead of deriving it. Half-right reasoning
with a guessed constant is indistinguishable from wrong reasoning at the output.
**Verdict — law.** `dist = radius / sin(atan(sensor_v / 2·lens)) · margin`. One
chosen number (the margin), and it is labelled as chosen.

### Tried — proving the caffeine/adenosine competition
**Happened.** Superposed 2YDO onto 5MZP: RMSD 1.62 Å over 168 shared TM
α-carbons, and the two ligand centroids land **1.8 Å apart**.
**Mechanism.** Adenosine is resolved only in 2YDO and caffeine only in 5MZP, so
"they compete for the same site" is normally an assertion the animator makes.
Superposition turns it into a measurement from two independent structures.
**Verdict — open, and the best thing in the film.** That number belongs in the
narration.

---

## Era: the gate

### Tried — asking Ryan which piece of work to do next
**Happened.** Twice in one session. He named the damage precisely:

> "You make it a decision gate, work on the one decision, and then come up with
> another decision gate, and totally misbuilding the main key component of the
> structure that shouldn't have been a decision in the first place. **They should
> have both have been done.**"

**Mechanism.** The rule had been in `~/.claude/CLAUDE.md` since 2026-08-06 in his
own words, and I broke it anyway. Asking costs the model nothing and *feels like
deference*; deciding costs it the risk of being wrong. That asymmetry runs one
direction forever unless something refuses it. And the damage is not the
question — it is the drift: an or-gate creates a place for the loser to die, and
nothing binds anyone to come back for it.
**Verdict — LAW #4, enforced.** `hooks/false_fork_gate.py` (PreToolUse on
AskUserQuestion) plus the pre-existing `false_fork_stop.py` on turn text. The
test: *if they pick A, does B still get built?* If yes it is not a question.

### Tried — the gate on its own output
**Happened.** The stop hook fired on a turn that pasted its own passing test
transcript in a fenced block.
**Mechanism.** The transcript contains offending questions *by construction* —
that is what it tests. A gate that fires on its own passing test teaches you to
ignore it, which costs more than the miss it prevents. A second, older bug
surfaced in the same pass: exclusivity was checked per sentence, so an honestly
declared fork whose "and the other does not get built" fell in the next breath
was still blocked — punishing the correct behaviour.
**Verdict — law.** A gate needs a regression suite like any other code. This one
now has 8 cases and they all pass. Quoted material (fenced blocks, blockquotes)
is not the author speaking.
