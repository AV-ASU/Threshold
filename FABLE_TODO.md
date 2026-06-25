# FABLE TODO — the warping / detail-horror direction

> Design backlog captured from a 2026-06 design session. These are
> **proposals, not yet built**, and several **supersede / conflict with**
> the current shipped systems (the §3 mutation threat model and the §4b
> infestation/convert-mutate pass). Reconcile into `NARRATIVE.md` (§3, §4b,
> §5/§6) before any code moves. Player-facing text from any of these must
> still obey the HARD RULE (no dashes).

---

## 1. Corruption grammar: spatial warping, not biological mutation

Replace body-horror mutation (tumors, gore, gold-in-wound, flesh peeling)
with **spatial warping** as the single corruption grammar. The wrongness is
geometry "bruising through" the flat plane — the same impossible thing as the
door, at every scale.

- **Environment warps.** Stretched / skewed decorations, hallways too long,
  rooms that loop, labyrinth pockets where corridors fold back on themselves —
  but **diegetic to Brimley** (the barn that goes on too long, the same corn
  road four times, a parlor whose far wall recedes), never a generic liminal
  void; always Brimley's own rooms turned wrong.
- **Keep the yellow ashfall.** It is the cosmic anchor (the Sign's jaundice);
  it fits warping even better than it fit mutation.
- **Drive it off the existing ramp:** `_infest_stage = min(3, evidence)`. Same
  monotonic, evidence-keyed escalation; just swap what each stage spawns.
  Stage 1: subtle (a stretched prop, a hall one tile too long). Stage 2: a
  room loops once. Stage 3: full labyrinth pockets, safe rooms warp too.
- **Why:** unifies the "weird bits" under one phenomenon (the fold), and
  fixes a real contradiction — §1b says the visible wrongness should be the
  **place, not the people**, which the old mutation system violated.
- **Tech reuse (cheap):** `cross_fold`, per-scene torus (`wrap_x/wrap_y`),
  in-maze relocations, the rift renderer, occlusion already exist. A loop
  pocket is "an interior scene with wrap on." Warped props = a draw-time
  stretch/skew on procedurally-drawn props (no asset pipeline).

## 2. Sculpted vs situational — who warps how, and why

The warp **encodes the town's cult/local split into the horror itself**
(reading who-was-what by how they are broken = the investigation).

- **Cult = sculpted.** They submitted ("gave themselves over", §1b), so the
  King has authorship. He warps them **uniformly, into purposes** —
  deliberate, functional, like vessels.
- **Locals = situational.** Netted by the rite without consent or awareness,
  so there is **no sculptor**. Their warping is involuntary entropy, shaped by
  **who they were** — a frozen sentence about their life:
  - Mrs. Calder (sets a place for a guest she can't name) → stretched
    *reaching* toward the empty chair forever.
  - Royce (couldn't stop trying to drive out) → elongated down the road,
    pointing at a horizon he'll never reach.
  - Old Pell (counted) → the tally warped into the body, ribs as marks.
- **All warping is spatial-stretch** (elongation, wrong proportions), **NOT
  biological gore.** A stretched man and a stretched hallway are the same
  impossible thing. Gore would break the unity; stretch keeps it.
- **Never name it in player text.** The situational warps stay unnamed:
  the game never names its monsters (everything is felt), and naming the
  shape would also drag in loaded real-world labels. Keep dev shorthand
  out of anything the player reads.

## 3. The spear-cult (the keeper mechanic)

At **3+ evidence** (when the King has finished sculpting them, the same beat
he becomes lethal and the gun stops working on them) cultists warp into
**committed lunge-spears**:

- **Telegraphed** by an aiming-limb wind-up formation (fair, readable horror:
  a person folding into a spear pointed at you).
- **Spent on a miss** — they fall dead. Spent bodies stay as terrain (a field
  of failed thrusts).
- **The dread is the wastage**, not the individual: the supply feels
  inexhaustible, the King spends them like ammunition (the rite is a battery,
  the souls are fuel, §1). Fear = expendability + the endless quiver.
- **A hit drags you down for the hive → CAPTURED.** NOT a clean kill —
  preserve the taken-alive fate (load-bearing for the hive / Mara / "no one
  to save").
- **Layer, don't replace.** Below 3 evidence cultists stay the line-of-sight
  stalkers they are now (the slow dread). The spear-form is the late-game
  intensifier. Keep the stealth identity ("it isn't a combat game").
- **Tone: idle / silent / sad, not frantic.** The lunge is the one kinetic
  exception against an otherwise still, watching world. Keep the action-game
  energy out of everything else.
- **The King stays the relentless, unshootable apex** above all of it (the
  contrast: cult survivable with skill, He is not).

## 4. Twisted Mara

Mara **is** twisted/sculpted like the rest of the congregation (she is cult —
submitted; keeping her un-warped broke our own sculpted rule). It strengthens
**"there was no one to bring back"** — whole Mara left the door open ("maybe I
could get her out"); twisted Mara slams it (what would you even drag up?).

Hard constraints on **how**:

- **Twisted but content, not suffering.** Serene in an inhuman shape.
  Preserves "she was answered, she went gladly" — the peace is the horror.
- **Still, not kinetic. NOT a fight, NOT a spear, NOT a wall.** The moment
  she's something you kill/fight to pass, the player gets relief + a task and
  the grief evaporates. The Hive stays the silent recognition beat.
- **Recognition + evidence #6 intact.** Strongest staging: folded
  indistinguishably into the kneeling choir; you have to *find* her; when she
  turns, human words come out of something that barely has a face left.
  *"I'm not lost. I've never been this close."* (Human voice, inhuman shape.)

## 5. The focal detail canvas (the most important feature)

Interaction focus that **tightens awareness without pausing the world.**
Pausing the world to examine a thing kills the tension; instead, leaning in
should narrow the player's attention onto one subject while the world keeps
living and threatening at the edges.

**Primary purpose: high-detail horror delivery.** At gameplay scale on the
oblique camera, a warped local or twisted Mara reads only as a silhouette. The
focal moment is where the wrongness **resolves** in detail. This is the
delivery mechanism that makes all the warping work above actually land — and it
**resolves the restraint-vs-detail tension**: restrained at gameplay scale (on
theme), visceral on examine (horror on demand). Pure "don't spend the flame."

- **Procedural is the ideal substrate.** Detail on demand, paid only on one
  subject while summoned. It is a **third authoring tier** above the existing
  two (world sprite + dialog portrait; cf. `_INFEST_WORLD` vs
  `_draw_infested_portrait`). `king_unfold.py` already proves the engine can do
  real normal-lit shading.
- **Mechanic (welds onto the core loop):** focusing **costs peripheral
  awareness.** Reuse `sight.py` — tighten the sight cone onto the subject so
  the cult is gated out of view while you're focused; the **King is exempt**
  and still looms in. Reading evidence in the open becomes a gamble →
  reinforces break-LOS-then-read. The world keeps simulating (a cultist can
  reach you mid-examine).
- **Craft rules:**
  1. **Ration it** — rare = powerful. Best beat: thing reads normal at
     distance, the lean-in is when it goes wrong.
  2. **Wrong-specific-detail over gore volume** (uncanny, not bloody — one
     precise wrong thing).
  3. **Stillness + one micro-movement** (a blink, a breath) beats writhing.
  4. **Real lighting passes** (light dying in folds, rim light) — affordable
     because it is one subject, rarely.
- **Cautions:**
  - Reserve for **examines / dialogue / key objects**, not every door or
    pickup (doors already fade). Else it is motion sickness + pacing death.
  - **Don't let the live sim wreck a scripted beat** (Mara recognition,
    endings). Gate those to safe/controlled contexts or freeze threats for the
    scripted lines. The Hive is already controlled.
  - **Cheap impl first:** cone tighten + re-aim the existing `apply_grade`
    vignette/desat toward the target + ease the focal center (a soft push, not
    a real zoom). Defer the true 3D dolly-zoom (it fights the tilt projection
    + occlusion sort).
- **Detail-canvas priority subjects:** twisted Mara, warped situational
  locals, the spear-cult aiming contortion, evidence/notes (the Sign
  breathing, the cult's hand), ashfall settling on a face.

---

## Suggested first step

Prototype the **focal detail render of one subject** (twisted Mara or a warped
local) to a PNG — the whole direction rests on whether the procedural draw
layer delivers genuinely upsetting detail when handed the canvas. Validate that
before reconciling the bible or touching the threat/infestation code.
