# THRESHOLD — TODO

> The **live list of genuinely open work**, and nothing else. If a ticket
> is fully landed, it is deleted from this file outright and its history
> moves to `CHANGELOG.md` — no "done" archive lives here. `NARRATIVE.md`
> stays the canon source of truth for facts; `DESIGN.md` for how systems
> work; `CHANGELOG.md` for why they got that way. Cross-check against
> `NARRATIVE.md` and `DIALOGUE.md` before writing prose; land any
> dialogue/narrator-text change in the code and `DIALOGUE.md` together
> (the `DIALOGUE.md` contract); run the full gate
> (`python tests/run_all.py`) before commit; add a `tests/flow.py` guard
> when a new note locks a canon fact.
>
> **When a ticket lands:** write its story to `CHANGELOG.md` (what it was,
> why it changed, what shipped), then delete it from this file. If part of
> a ticket lands and part doesn't, trim it down to only the open remainder
> — don't leave "LANDED" narration sitting here as a trophy. This file
> should be short enough to read start to finish in one sitting; if it
> isn't, something in it is actually done.

> **Model tags** (2026-07): each ticket is marked **[Opus]** (systems
> reasoning, geometry, rendering, correctness) or **[Fable]** (prose, voice,
> atmosphere). A few straddle and say so. Routing hint, not a rule.

---

## Buildable now

### 1. **[Fable]** Investigation dialogue verb — remaining revisit-nudges

The ask-questions conversation engine shipped for all five principals plus
the chorus (`CHANGELOG.md`, "Close-up tableaux & the dialogue verb").
**Still open:** `_REVISIT_NUDGES` entries for Hettie, Toby, and Crane as
their case hooks land — a discovery should nudge the PI back to ask them
about it, the way `the_preacher` already points back to Vane.

### 2. **[Fable + Opus]** The favor economy — beyond the newspaper pilot

The newspaper's one-copy, six-recipient choice shipped as the pilot
(`CHANGELOG.md`). Still open, direction-stage only:
- **Requests variant (same engine):** a local asks for a thing → fulfill /
  refuse / SUBVERT (use it another way) → the town feels it.
- **Fences to hold if this grows:** rewards stay **incommensurable** (no
  dominant pick); **never evidence**; the ripple is **mood, not a meter**;
  it **never gates an ending**; **existing verbs only** (give via E /
  dialog).

### 4. **[Fable]** Outdoor dread — the composition pass

Open ground is the game's weakest dread zone (long sightlines, reads as an
open field). The heavy-tech answers (a Brimley reshape, a general ground
floor-roll) are parked on purpose — see `CHANGELOG.md`, "Brimley
geography" — because the tilt camera + blind-spot sight-gating already buy
most of the geometry illusion for free. The lever is **composition** with
tools already shipped:
- **Corn + treeline as outdoor walls.** Denser stands, winding corn lanes
  that break the long shot, a treeline that closes the rim. Draw +
  placement only; the standee billboards + `_corn_runs` LOD already exist.
- **Fog / mist volume** between the player and the distance, shortening
  the effective sightline. Rides the skybox/void rim, already ~80% there.
- **Landmark repetition + same-scene silent folds** (`Game.cross_fold`,
  draw-only) for the "handed back / the town rearranges" uncanny with no
  sim change.
- **Turf HILLS + unified roof caps** (shipped 2026-07 for the grove mine
  mouth): the `turf` wall material (grass top, stone sides, via `top_tint`) +
  the `hill_cap` dome prop raise a grassy hill from the game's OWN wall
  geometry — real occlusion + relief for an outdoor scene, static/correct
  from every facing, WITHOUT the parked heightfield floor-roll. A new lever
  for this pass (`rendering/props.py`, `scenes/terrain.py _WALL_STYLES`).

**To turn into work: name ONE scene and the ONE composition it gets** (this
sightline broken by this corn lane, this landmark passed twice in fog). Do
not start against the abstract goal. Keep the sim Euclidean-honest so
stealth distance-falloff + NPC nav stay true under any presentation lie.
**Preserve (load-bearing) if the scene is Brimley:** it stays ONE square
scene (do not split, do not reshape); the fold road + Royce/Garrick
looping-roads lines; the well as dread set-dressing (never the way down);
all exits/locals/cult stations; in player-facing text call it a bounded
fog-edge / void-ringed town, never "island."

### 4b. **[Opus]** Brimley river-centered rebuild, both banks

**Concept approved 2026-07, not yet built.** A top-down layout check found
6 of 7 buildings on one bank with the river as an unused spine. Approved
fix: redistribute the 7 buildings tight on BOTH banks around the river +
bridge — a redistribution, not a shape/boundary change (Brimley still
stays one square scene with the torus wrap; see #4).

- **Flow, from the real topology:** the player enters from the EAST (the
  Arcadia sits off-map via the east lodge road), so the near bank is
  first-contact town (shop, barn, Toby's house) and the sheriff sits on
  the FAR bank — "cross the river to reach the law" falls out of geography
  with no gate needed.
- **Acceptance test:** everything fits IN SCALE on the 60x60 map at real
  building footprints, with cover lanes per bank, NPC/King nav across the
  torus wrap, the fold-road E-W loop, homebody door anchors, and every
  exit/spawn reconciled; reachability re-checked with smoke's flood-fill.
- Its own build, scoped to run after the conversation/tableau work so two
  big changes are never in the air at once.

### 4c. **[Opus]** Wall program — Phase 4 (freeform walls)

The **interior-door rollout is COMPLETE** (`CHANGELOG.md`, "Walls & interior
geometry"): the shop pilot, the church vestry, the barn, the abandoned
farmhouse, the sheriff's office, and Toby's closet are all doored, and the
schoolhouse + the Lodge interiors were assessed and deliberately left whole as
authentic open spaces (a one-room schoolhouse with the rite fold in the open
floor; an open-plan lodge common room; a hall of separate room-scenes; a
single-room cellar). The **wall-material rollout program** (thin-slab + rounded
+ per-material styles) has landed Phase 2 (every above-ground interior) and
Phase 3 (the mine as full-thick hewn `rock`), `CHANGELOG.md`. **Still open:**
- **Phase 4 — freeform walls** (the north star): a wall SEGMENT primitive
  off the tile grid, unlocking diagonal walls, a curved church apse, a
  round silo/tower. Prototype ONE curved feature first.
- **Deferred church shapes** (the curved apse / arched-window geometry)
  wait on Phase 4.
- **Cross-cutting every phase:** thinner walls occlude less, so re-derive
  interior cover as styles land; extend `tests/stealth.py` §16; VISION
  toward the Darkwood organic read.

### 12. **[Fable + Opus]** Royce the trucker + the rusting semi

Promote Royce to the man who drove Brimley's supply run (Hettie's shelves
are bare because *his* deliveries stopped). **[Fable]** a small dialogue
nudge (he ran the route, goods in and out) — his newspaper exchange
already carries some of this; confirm it's enough or add the nudge.
**[Opus]** place his picked-clean semi rusting at the town edge (optional
light scavenge, never evidence). Reconcile with his worker job-loop.

### 13b. **[Fable]** Interior voice — quiet the routine reactions

The Casebook structure landed (Case/Tools/Papers tabs, the Working Theory
pinned first, the named scribble toast — `CHANGELOG.md`), and a first trim
cut the three worst offenders. **Still open — the maintainer's actual
grievance ("every interaction does something and never leaves the player
thinking"):** on-screen PI narrator captions still fire on nearly every
world-prop examine. Cut candidates (~30 sites, prop examines that
editorialize a conclusion instead of stating the fact): the lodge
register/ledger recaps, the well / news-rack monologues, headstone +
candle re-examines, `barrow_tools` / `scarecrow` / `backwoods_note` /
`worn_stone` / `bell_tower` / `the_burning` / `the_fall` /
`threshing_floor` / `works_cistern_seen` / `the_doorframe` flavor
`_evidence` calls (these write nothing to the book — caption only). Trim
each to a terse factual line or silence, so the player draws the
inference. **The revisit-nudges** (`_REVISIT_NUDGES`, the "I should go
back and ask him" appends) are the clearest instance of "the game does
the thinking for you" — decide with the maintainer whether they go.
**KEEP, do not touch:** the five `CANONICAL_EVIDENCE` beats, the
descent-voice arc, the dream, the Mask temptation, Mara's calling-out, the
fold notes, the threshold recognition, and the deliberate atmospheric
one-shots that ARE the dread (the frozen news rack, the empty church).
Each cut must keep the `tests/flow.py` guards green (§16, §17b/c/d, §24
assert on several of these captions/notes) and update the ones whose
behavior legitimately changes.

### 23. **[Opus + Fable]** Complex behavior for cultists and locals

Built in pilots, inside hard fences: systemic not scripted; the people do
NOT change (only the cult may act wrong, and only in cult ways; locals
stay mundane and never signal the cosmology); nothing touches the pacing
ratios, the SAFE_SCENES refuge, fold-only pursuit carry, or the
Talk/two-touch gates; no new behavior ships with explanatory player-facing
text (the behavior IS the tell); the King and hollow Sheriff keep their
exemptions.

- **23a remainder:** job-station authoring for the patrolled cult rooms
  that have none (`works_sign`'s lone patrol) — place via the
  SCENE-DRESSING PROCESS (render first, never by name). The synchrony +
  hand-off beats themselves are landed (`CHANGELOG.md`).
- **23b. The town half (open).** The **yield**: a local a cult patrol
  passes steps off the lane, eyes down, waits, resumes; the cultist never
  acknowledges them. **Mundane witness reactions**: a local who sees the
  drawn gun, a sprint, or a moth axed flinches or hurries indoors (rides
  homebody `_inside`); a kill nearby empties the street for the visit.
  Strictly mundane reactions only.
- **23c. The mechanical pieces (open), sequenced for the #5 tuning
  pass.** SEARCH **sweep partition** (multiple searchers divide
  `sweep_points`, no duplicate checks); **room posture** (a per-scene
  calm/uneasy/roused int raised by flares, shots, struggles, found bodies,
  decaying; modulates walk speed, scan time, sweep budget — ship
  OFF-default behind config until the #5 tuning pass absorbs it); the
  **flank call** (a locked chaser pulls at most one nearby patrol to a
  flank point, same LOS/suspicion rules, normal search timer, never soft
  omniscience); **object-state investigation** (a left-on noisemaker, an
  opened door, a moth husk: pause at it, mark the room uneasy).
- **23d. Content passes (open, anytime, Fable).** Fuller local **day-loops**
  on the JOBS `stations` plumbing (Pell to the field edge he doesn't look
  at, Calder to her gate, Royce circling his truck; door-anchor honesty
  rules apply); **disposition framing** read off existing save flags
  (mood, never a meter).

---

## Blocked on a human at the keys

These are BUILT and guarded; what remains cannot be settled from code
inspection and needs a person playing the game.

### 5. **[Opus]** Stealth rework — the TUNING loop

The mechanic, the placement pass, and a first human tuning pass all landed
(`CHANGELOG.md`, "Stealth & threat" — includes what that pass found and
fixed). What remains proves out only against further play: the new
constants' FEEL, the suspicion fill curve (`SUS_FILL_RATE`), the
concealment factors, the sweep budget, and the struggle window/press
count. Also deferred on purpose: the Pillar-2 **peek** verb (free look
under tilt already carries the information function) and an
exit-takes-a-beat vulnerability window on enclosed hides. Spitballed and
parked for a decision: the crouch stance (after the next playtest) and
the window-vault prototype (one building, look-passed, last).

### 6. **[Opus]** Combat / difficulty — judgment calls (decide on purpose)

Not bugs; deliberate choices worth confirming rather than leaving by
default: the gun goes **stun-only at 3 evidence** with ~14 rounds total
per run, so the main combat verb is removed exactly when danger spikes
(agency loss vs. intended dread). There are **no difficulty options**, so
the visibility/Watcher death-spiral hits newcomers hard and is trivial to
experts. Items are gates, not resources (armor slots return 0). The
two-touch grab softening already landed (`CHANGELOG.md`) and directly
answered the "nothing you can do once they're on you" play-note; still
open here: the gun stun-window and whether to add difficulty options —
consider transforming the stun into a tactical window rather than a tax,
an easy/hard toggle, or light resource tension, only if it serves the
horror, not despite it.

---

## Deferred / north star

### 7. **[Fable]** The liminal-composition pass

Not a discrete ticket — a standing direction for per-scene level-design
polish: composed emptiness, long sightlines, uncanny repetition.
Inherently iterative. **To turn it into work, name ONE scene and the ONE
composition it gets** (this sightline, this repeated landmark); do not
start against the abstract goal. *(The buildable-now #4 is this pass aimed
specifically at outdoor dread — start there.)*

### 8. Parked — terrain & reshape megabuilds

Do NOT pull forward without a set-piece that demands it AND a fresh
decision. The reasoning for parking these lives in `CHANGELOG.md`,
"Brimley geography." Cut from active work because their payoff fights
their cost at this camera. The DORMANT heightfield prototype + the SHIPPED
carved river channel STAY (harmless, byte-identical at pitch 0); it's the
general-purpose builds that are parked: the floor-roll warp, the terrain
design directions that depend on it (sunken-lane cover, King crest-reveal,
terrain-herding, the peek verb's home), and the round/organic Brimley
reshape.

### 20. **[Opus + Fable]** Endings redraw with the close-up techniques

Parked, NOT scoped. The ending presentations (the King-catch furnace,
SEAL's lines-on-black tableau, SPREAD's drive-out, BREAK's mask-yank +
blast) predate the close-up tableau art pass and could in principle be
redrawn with those techniques (bespoke portrait register, reactive state,
a corrected vignette ramp — note the older shared vignette loop actually
darkens the CENTER, so any redraw should use Mara's frame's corrected
ramp instead). The endings themselves are approved, flow-guarded
set-pieces (their lines + palettes are canon), so this is a
re-presentation question, not a gap. Do not start without a fresh
maintainer decision; land each ending only through a VISION.md look pass.

### 21. **[Opus + Fable]** LIGHT IS THE PILLAR — the perfected system

**Maintainer mandate (2026-07 QC discussion): after the quality-floor
sprint, light is the ONE system to perfect** — the game's missing
mastery verb. The doctrine that keeps it coherent with everything
shipped: **light is safety from the small things and a beacon to the big
one** (Watchers die in it; the flashlight burn + the King's attention
still price it). Landed already: the lighting foundation, interior
lighting, `WATCHER_LIGHT_BURN`, the beam-off retirement (light works
everywhere), and the flashlight opening on the PI's desk
(`CHANGELOG.md`, "Lighting" / "The light pillar"). Open, in build order:
- **The light-security loop (the core).** Buildings' fixtures can be
  restored/switched; lit rooms are SECURED against Watchers; lights decay
  or fail over time; gasoline for the gensets is the cost (canon-ready:
  the fold cut the grid, the town runs on gensets, `generator` props
  front the doors). Needs: a genset→fixtures power link, per-scene light
  state, a fuel item + siphon/refill verb. Keep the tension: a lit town
  is a town He can see.
- **Watcher variety.** Wildly different silhouettes per canon (each is a
  different cross-section of the same higher-dimensional gaze —
  NARRATIVE §4 makes this free). Fast/skittery movement prototyped ONE
  design at a time through the creature-design loop; dark-only existence.
- **The moth blackout.** A moth flare knocks out a genset (drop the
  yard-light pools), the screen dims, the cult camp processes to the
  flash and fans out. Rides the power link above.
- **A full Watchers-in-the-dark rework** (they can open in any room but
  only EXIST in the dark) — couples with the blackout into the perfect
  storm. A real rework of `_tick_watchers`; keep the below-3 threat role.
- The **capture→King-unleashed** thread and **procession-across-scenes**
  staging sit here too, unscoped. **The capture fork is RULED (2026-07,
  maintainer): capture is GAME OVER** — the CAPTURED card stays a hard
  run-end, no capture-as-continuation. The corollary work item: cultists
  must EARN that ending (the "cultists feel too weak" playtest note) —
  lands through the #5/#6 tuning loop, not a new system.

### 16. **[Opus]** Ship track — packaging

Itch-ready build: pyinstaller (or equivalent) one-file win/linux builds,
save-dir sanity, a settings sanity pass, a version stamp. End-stage; do
near ship.

### 17. **[Opus + Fable]** The ancient altar — the CAP of the last sealing

Move the mid-Brimley standing stones to the riverbank (over the point the
Threshold sits beneath; keep the worn cult path). Pre-cult dressing:
lichened, weathered, sunken, nothing yellow, reads OLDER than every cult
mark. ONE worn carving that recontextualizes after the player has seen the
Sign (matches the Mask grammar) + a single `notes` beat (never evidence,
no cosmology). Gives SEAL its precedent without a word. Lands with the
compression pass (#4b).

---

## Standing fences (guardrails, not tickets)

- **The lure chain is NEVER stated diegetically.** King → Mara → Walter →
  PI is felt, not said. Do NOT build on any of it. King/Watcher moments
  read as **luck, not omniscience** (powerful, not infallible).
- **The corn is mundane, never the door's doing.** Keep the impossible
  count at **one**: the single unexplained door, everything else ordinary
  cause-and-effect downstream of it.
- **No dashes in player-facing text** (HARD RULE; flow-guarded).
- **L5 — complexity hotspots (awareness only, not a ticket).** The largest
  function bodies (`tests/flow.py main`, `scenes/brimley.build_brimley`,
  `systems/render_mixin.draw_world`, `rendering/sprites_npc.draw_npc_sprite`,
  `rendering/king_unfold.draw_king_unfold`) match the project's deliberate
  "one cohesive beat per function" style and sit behind the test gate.
  Listed so growth stays a choice, not an accident — not a call to split
  them.

---

## Optional polish (no canon/lore change; do as time allows)

- **[Opus]** **SPREAD ending sign sync** — the intro drive-in sign and the
  in-game welcome sign render the old-timey BRIMLEY board (WELCOME TO /
  NORTHERNMOST CORN / EST. 1894). The SPREAD ending's drive-out still shows
  the old blank-back sign shape (`rendering/spread_drive.py _sign_back`).
  Update its proportions/posts to match the new board (the back stays
  blank/unpainted by design; only the shape needs to agree). Verify with a
  headless capture of the SPREAD drive-out.
- **[Fable + Opus]** **Rev. Asa Crane murder reveal + sprite** — the
  discovery location + staging landed (`CHANGELOG.md`). Still open: (1)
  **bespoke sprite** — the current corpse is a placeholder medieval knight
  (`_draw_body`); replace with a gutted-preacher draw (dark palette, white
  collar, cross in the mess). (2) Stage the approach (wrongness before
  sight, long sightline). Art only; lore unchanged.
- **[Opus]** **Held-weapon offset per camera yaw** — `draw_axe_held` reads
  at rest; eyeball the equipped-weapon offset at every camera yaw so it
  never floats off the hand. Verify with a tilt capture across yaws.
- **[Opus]** **Higher-contrast see-through doors** — opt in the doors where
  the sight-gated aperture effect reads strongest: a lit room off a dark
  hall, the front door onto the yard. Draw/opt-in only; no new tech.
- **[Opus]** **Permanently-visible King through an OPEN fold** — currently
  he looms through the rift only while it forms, then steps through
  (intentional). A persistent silhouette on the far side of an already-open
  fold is not built; revisit only if the direction changes.
- **[Opus]** **Mine retrofit tail cleanups** (none player-visible) — (a)
  cache the `_tilt_rack_box` extrusion per (tile, yaw-bucket) like the wall
  cards (`well_passage` re-projects ~280 points/frame live); (b) fold
  `_RACK_CHARS` into the shared wall-scan char-set plumbing instead of a
  third parallel set; (c) the cave `door_style` key list in
  `scenes/__init__.py` duplicates the `UNDERGROUND_SCENES` gating idea,
  derive from one source; (d) `husk_bundle` + `pillar` are registered
  kinds with no placements (keep as reusable art or cut).
- **[Opus]** **Grove mine-hill finish level-up** (deferred, maintainer "fine
  for now") — the mouth is a green turf HILL with a stone adit; its grass-dome
  ROOF got a full detail pass, but the stone side/cut faces + the adit mouth
  are plainer by comparison. Bring the stone up to the roof's finish (strata,
  cracks, a little scree/moss at the base) and make the adit read a touch more
  as the focal point, so the whole object sits at one level of craft.
  `hill_cap` (`rendering/props.py`) + the `turf` walls + `_grove_interact`
  dressing (`scenes/hidden_folds.py`).
- **[Opus]** **Louvered belfry openings** — the bell tower's belfry uses
  the glazed cottage-window char (`'i'`), which renders as glass everywhere.
  A belfry wants louvered slats, which needs its own window style or a
  wall-deco louver over the openings (a small per-scene window-style
  mechanism). Deferred from the redecoration-audit polish (the rest of which
  landed, `CHANGELOG.md`).

---

## Voice / polish (player-facing text — still open)

- Descent interior voice wobbles POV (first-person notes vs. second-person
  on-screen beats, `systems/game.py`) — confirm this is the deliberate
  self-vs-lure split `DIALOGUE.md` documents (`chalk_surface`/
  `descent_dig`/`chalk_deep` first-person vs. `descent_leave`/
  `descent_mask` second-person) and not accidental drift elsewhere.
- HUD fall-through labels: "Dark" (the Hive!), "Depths Antechamber",
  "Effigy Grove", "Threshold" (`scenes/base.py` fallback).
- NPC object names "Clerk"/"Sheriff"/"Preacher" leak on generic paths
  (corpse examine: "Clerk. Face-down where the round put them.").
- Placeholder texts on cued interactions: "A small stash.", "A weathered
  headstone.", "A scarecrow.", "A key.", "An axe for chopping wood."
- Small ones: Sable's "last night"/"tonight" against elapsed play; the
  robe "hangs... pressed and folded"; the Invitation's "Sleep where we
  slept" with no sleep verb at the school; threshold recognition + "A
  doorframe with no wall." fire at the cave mouth, 13 sight-gated rows
  before the frame is visible; lowercase hide notices; "waking the dark ."
  double space; "midwestern" casing; Garrick and hollow Vane both call the
  PI "son"; two simultaneous Hetties (door + counter); duplicate candle
  decoration in Toby's house.
- Missing canon clincher: `NARRATIVE.md` §4's ledger entry promises "your
  own name, signed in tonight, already among them" — the cellar text only
  gestures at it and the desk sign-in is optional; one clause conditioned
  on `register_signed` closes the loop.

---

## Process

### D. **[Fable]** Doc consolidation — remainder

Phase 1 landed (the threat section moved to DESIGN §1; `CHANGELOG.md`,
"Documentation process"). Still open: CLAUDE.md's Layout section carries a
tableau mega-paragraph and several system narrations (Casebook, dialogue
channels, moth/stealth asides) that duplicate or should live in
DESIGN/DIALOGUE; move each to its one home and leave a code-map pointer,
one section per pass, keeping the every-turn read shrinking.

### R. **[Fable]** Cross-model review gate

After an **[Opus]** ticket lands, run a **Fable** review pass before it
merges. This is NOT a code-correctness re-audit (use `/code-review` or a
fresh Opus context for that, since a model self-reviewing its own diff is
the weakest check). Fable judges what it is strongest at for THIS game:
**does the change land the feeling and hold canon.** For a given diff +
the running build it answers:
- Does it read as dread, or as a mechanic showing through? (atmosphere,
  pacing, the tell)
- Does any player-facing string break the no-dashes rule or the
  `NARRATIVE.md` voice?
- Does it contradict a locked canon fact (`NARRATIVE.md`)?
- What is the cheapest change that would make it land harder?

Output is a short verdict + ranked notes, not a rewrite. The value is a
SECOND, independent model looking at the work, so the direction can flip:
if Fable is doing the implementing, an Opus pass reviews it the same way.
