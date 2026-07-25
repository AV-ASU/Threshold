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

### 27. **[Opus]** Remake the town sign (maintainer: "I want the town sign remade")

The old-timey painted BRIMLEY board (WELCOME TO / NORTHERNMOST CORN / EST.
1894) needs a redesign. It is also the game's **last font-rendered world
lettering** (`rendering/props.py`, 3 of the 3 uses in `FONT_BUDGET`), so the
remake is the chance to retire that: spell it in the procedural neon-tube
alphabet's cousin, a **painted**-letter stroke set (`_GLYPH` +
`_draw_neon_word` in `rendering/props.py` are the worked reference; a painted
board wants flat opaque strokes with wear, not tube glow). Drop the file's
`FONT_BUDGET` entry to 0 when it lands and the guard locks it shut.
Verify with `tools/capture_facings.py` (a roadside board is read from the
approach, so check the angles a driver/walker actually gets, not just N).
**Reconcile:** the SPREAD ending's drive-out sign (`rendering/spread_drive.py
_sign_back`) shares the board's shape and is already flagged under Optional
polish; do both in one pass so they cannot disagree.

### 28. **[Opus + Fable]** Cut the calendars (maintainer: "I hate it")

**Maintainer ruling: remove the calendars from the game**, including the beat
built entirely on one (Old Pell's) — explicitly acknowledged and accepted.
This is a canon change, not just a prop deletion, so it needs a decision on
the replacement before it is built:

- **The prop.** The `calendar` decoration (`entities/deco_horror.py
  _draw_calendar`, placed in `scenes/brimley.py` and read in the Vane
  tableau's dressing). Removing it also clears that file's 3 `FONT_BUDGET`
  entries (the month/day label), so the guard tightens for free.
- **Pell's whole thread rides it** (`scenes/dialogue.py`, `scenes/brimley.py`):
  the `beat_pell_coal` stoop line ("I've got the calendar where I want it.
  Stopped."), the `beat_pell_marked` ripple after the newspaper, and the
  `paper_pell` note ("He said he'd pencil today into his calendar"). His WANT
  (`DESIGN.md` §8: legacy, the harvest endures) survives fine; what needs
  reinventing is the **object that shows a man refusing to mark time**. Pick
  the new carrier deliberately — it is his only mechanical beat.
- **Canon to reconcile** (`NARRATIVE.md` §3 timeline, §4 chorus, and the
  invariant "every calendar in town stops at Jan 15"): the seal's date is
  load-bearing and is currently *shown* by the calendars. Decide what carries
  the stopped-January fact instead (the frozen news rack already dates itself
  Jan 15 and may be enough), then update NARRATIVE + DIALOGUE together.
- **Guards:** `tests/flow.py` asserts several Pell/paper beats; expect to
  update them in the same commit.

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

### 24. **[Opus + Fable]** INTERIORS PROGRAM — ensembles, floor plans, the prop fifteen

**Maintainer directive (2026-07 playtest): "props seem scattered without
any purpose... treat what you have as multiple props touching each other
and make those into ONE new object with more handcrafted detail."** The
rooms read as prop soup; the fix is composed ensembles, not more
placement.

- **THE ENSEMBLE RULE.** Props that touch each other or a shared wall
  merge into ONE handcrafted multi-tile object (a `SOLID_PROPS` volume
  with a designed silhouette), authored for the projection, never
  re-scattered as separates. Design each from the FIXED CAMERA's four
  facings, E/W FIRST (the historically weakest angles).
- **REAL FLOOR PLANS FIRST.** Before re-dressing a room, sketch it from a
  real reference plan (1990s Minnesota cabin / small hotel / farmhouse):
  work zones, walk lanes, furniture against walls, one focal wall using
  volume and negative space. Provenance stays king (SCENE-DRESSING
  PROCESS).
- **The prop fifteen (reusable ensembles, build as a library):**
  1. kitchen (wood stove + counter + stovepipe + hung pots),
  2. hearth wall (fireplace + mantle + fire tools + log basket),
  3. bearskin rug, 4. trophy wall (mounted wolf + buck + fish as ONE),
  5. bed corner (bed + nightstand + wall pegs + underfoot rug),
  6. writing nook (desk + chair + lamp + papers),
  7. dining set (table + benches + settings),
  8. wash corner (washstand + mirror + towel rail),
  9. gun rack wall, 10. coat wall (pegs + coats + boots under),
  11. pantry shelving (stocked and bare variants),
  12. reading chair + side table + oil lamp,
  13. workbench wall (hung tools + vise),
  14. woodpile + stove pairing,
  15. wardrobe with the robe made legible (Sable's closet: the tell
      reads the moment you round the partition, no squinting).
  Each through the render-first loop (preview sheet → approve → place).
- **15 INSIDE + 15 OUTSIDE (maintainer refinement).** The fifteen above
  are the INTERIOR library; a matching EXTERIOR fifteen follows (porch
  ensemble, lean-to + stacked wood, clothesline, rain barrel + gutter,
  fence-and-gate runs, mailbox post, burn barrel, machine shed face,
  pump + trough, chicken wire pen, propane/fuel tank, junk pile, tarped
  equipment, porch chair + rifle, antler-over-door). Same rules.
- **USE ALL SIX SURFACES.** This is a 3D environment: on top of, next
  to, underneath, hung from walls, standing on floors, and dropped from
  ceilings/rooflines are all placement options. An ensemble is allowed
  to span floor-to-ceiling (stovepipe up through the roof, hams hung
  from beams, a wall of pelts reaching the eave).
- **ANIMATE WHERE IT EARNS IT.** Each ensemble asks: could a part move,
  and does the world state show through it (a TV that plays static only
  while the genset runs, a stovepipe that smokes when lit, a fan that
  turns)? Powered behavior rides the light pillar's genset link (#21).
  Not everything can or should move; a still room with ONE moving thing
  is scarier than a busy one.
- **EVERY ENSEMBLE SHIPS ITS WEAR LAYER, WORLD-SPACE.** The object's
  years (rust, soot, scratches), its stains on the surfaces around it
  (the floor wears where feet stood), and at least one piece of honest
  mess -- with FEW, BIG, DISTINGUISHABLE items, never same-weight
  speckle. Every mark is projected geometry in its true plane (a plate
  is a world-plane circle); screen-aligned marks are error class 7.
  The floors set the bar; the decor rises to it.
- **Rug rework rides along:** the rug must read from every facing (its
  pattern/fringe currently only reads from N).
- **Blank building faces:** E/W exterior shells (the backwoods cabin is
  a bare grey slab from the side) need relief — windows, timber framing,
  a lean-to, stacked wood — via the exterior library, not one-offs.
- **Pilot: the LODGE COMMON ROOM** — LANDED (kitchen wall, dining set,
  hearth mass, the host's desk + key wall; `CHANGELOG.md`). **Wave 2
  rollout underway:** the shop's stockroom receiving corner landed
  (crate stack + check table + flour barrel as ONE object with its
  wear; the candle stays a separate emitter seated on the table).
  The sheriff's OFFICE quad landed next (the lawman's wall: cot +
  washstand + coat rack as one west-wall run; the lawman's desk: desk +
  radio + files + mug + tucked chair as one working surface). Next
  rooms: the office's booking/waiting corners if they earn it, then
  the church vestry.

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
  drawn gun or a sprint flinches or hurries indoors (rides
  homebody `_inside`); a kill nearby empties the street for the visit.
  Strictly mundane reactions only.
- **23c. The mechanical pieces (open), sequenced for the #5 tuning
  pass.** SEARCH **sweep partition** (multiple searchers divide
  `sweep_points`, no duplicate checks); **room posture** (a per-scene
  calm/uneasy/roused int raised by shots, struggles, found bodies,
  decaying; modulates walk speed, scan time, sweep budget — ship
  OFF-default behind config until the #5 tuning pass absorbs it); the
  **flank call** (a locked chaser pulls at most one nearby patrol to a
  flank point, same LOS/suspicion rules, normal search timer, never soft
  omniscience); **object-state investigation** (a left-on noisemaker, an
  opened door: pause at it, mark the room uneasy).
- **23d. Content passes (open, anytime, Fable).** Fuller local **day-loops**
  on the JOBS `stations` plumbing (Pell to the field edge he doesn't look
  at, Calder to her gate, Royce circling his truck; door-anchor honesty
  rules apply); **disposition framing** read off existing save flags
  (mood, never a meter).

### 25. **[Fable + Opus]** The King → the STORM (apex redesign, IN PROGRESS)

Replacing THE UNFOLDING (`rendering/king_unfold.py`) with the shadow family's
apex: the King is not one body, He is the **STORM** — His attention flooding
the flat plane so every dark space erupts amalgam-cuts (portals with a part
half-out). Locked with the maintainer this pass:
- **No apex body.** The "bearer" is just another amalgam; nothing marks it but
  the Mask.
- **The Mask is a PART** (the 18th), surfaced from its own cut in the family
  grammar, held by the flesh. His face made an object: **player scale** and a
  **real 3D object** (`draw_pallid_3d`) that turns a full 360 — the carved face
  toward the PI, the blank shell turned away, a curved lens at profile —
  superseding the earlier always-camera-facing call so it respects the tilted
  world. Timber is a bone↔wood blend (carved-pallid). No halo, no mouth, no nose.
- **One Mask storm-wide, MIGRATING** — surfaces on one unit, is borne, sinks,
  rises elsewhere (THE UNFOLDING's host/sink/rebond state, translated). It IS
  the focal "Him" and keeps luck-not-omniscience: the Mask surfacing near you
  is His attention finding you; while it is borne far off, His regard is
  elsewhere.
- **Light SLOWS the storm, never burns it** (burning stays the Watchers'
  privilege); the AI avoids light regardless. He is survived, never dispelled.
- **The storm fills ALL dark, corn included** ("no light = danger" taken to its
  end). Rides the ev-driven outdoor darkening (#4/#21). Light = the last
  refuge.
- The idle horizon King is **CUT** (maintainer ruling); the storm is the
  full-power apex at the source, so its overwhelm is the point.

**LANDED (dormant, wired into NOTHING in the game):**
- The **Mask part** in `rendering/amalgam.py`: `draw_pallid_3d` (the one
  reusable 3D Mask — a single bent SHEET, the front cap of an ellipsoid, NOT a
  closed egg; pale carved FACE on the front only: deep jagged sockets + gold,
  seam, crack, NO eyes from behind; BOTH sides pale so from behind you see its
  pale concave inside and it still reads as a mask; a bent-crescent profile)
  driven through `draw_pallid_mask_part` + a `mask=` kwarg on
  `draw_amalgam_sprite`, NEVER dealt by `assemble()`, so every ordinary amalgam
  is byte-identical. Player scale (`STORM_MASK_R`). Previews
  `tools/preview_mask_spin.py` (the full spin) + `tools/preview_bearer.py`.
- The **bearer power-up** (drawn ONLY when the storm passes `mask=`): the
  possessed amalgam is simply a **BIGGER** amalgam (`BEARER_SCALE`) wearing the
  Mask + a **crown** of ember-cuts (`_bearer_crown`) — size is the tell, not a
  busier body.
- The **storm ENGINE** `systems/storm.py` (`Storm`): the single migrating Mask
  bearer, units drifting to His **lagged sense** of the player (luck, not
  omniscience), **light slows + repels, never burns**. Sim + draw helper only;
  imported by nothing in the game. Preview `tools/preview_storm.py`.
- The **storm's STAGE** — the ev-driven surface darkening (LIVE). `STORM_STAGE_SCENES`
  (Brimley + `OUTDOOR_SCENES`) route through `_draw_dark` at a gloom that ramps
  with the rot stage (`STORM_DARK_GLOOM = (0, 44, 92, 138)`): stage 0 is full
  day (early-out, byte-identical), and by stage 3 it is night with the road
  yard-lights as ISLANDS and the flashlight enabled outdoors (so the
  light-draws-Him double-edge applies there too). This is world rot's LIGHT twin
  (understanding, not a clock — the daytime invariant holds, NARRATIVE §canon).
  VISUAL + flashlight only so far; no new threat mechanic yet — it is the STAGE
  the storm fills.

**OPEN, in build order:** (1) the **light/dark SPLIT as a MECHANIC** (the
visual darkening landed, above; #4/#21) — outdoors, light pools = cover and the
dark = exposure, so bring the surface storm-dark scenes into the shadow-cover
(`SUS_CONCEAL_DARK`) + Watcher-dark rules the dim interiors already use, giving
the storm a stage to open in; (2) **wire the storm engine in** — real scene
dark-spots as anchors (off the darkening), tilt-camera projection, spawn density
off evidence, and the **catch** (a bearer reaching you = the King-catch death);
(3) **retire THE UNFOLDING** and rewire the catch / death card / Carcosa
cutscene (flow-guarded) onto the storm; (4) reconcile canon (NARRATIVE §4/§8 the
King, DESIGN §1 the apex) ONLY as each piece lands —
the docs still describe THE UNFOLDING because that is what SHIPS until (3). Land
each visual beat through a VISION look-pass.

**The storm CUTS wear the rift's gold rim (approved 2026-07, option (a)+gold).**
The amalgam apertures should read as the same portal family as the fold/King
rift (`rendering/portal.py`): an **ANCHORED gold-rimmed cut** (not a billboard),
but with the off-angle falloff FLOORED so a storm cut thins yet never fully
vanishes (you always sense them). Same gold language as the rift's rim/pool, at
aperture size (gold rim + motes, no expensive see-through — the rift stays the
only full doorway). The maintainer weighed a "pool of water that faces you,
things fade into it" presentation and chose anchored-never-vanish over a
billboard (protects the pseudo-3D "object you can circle, not a billboard that
swivels" canon, DESIGN §7). The **fade-until-gone dissolve is reserved for the
CATCH/death beat** (a bearer reaches you → you fade into His portal), NOT
routine crossing (folds stay "the crossing is nothing, the frame is the
spectacle").

**Fences:** Mask stays player-scale + a real 3D object (it turns to face you or
away, never a billboard); one bearer at a time; the flood concentrates on His
last *sense* of you, not your true position (luck-not-omniscience); the
impossible count stays at one.

### 26. **[Opus + Fable]** The in-between / lost spaces — Brimley restructure (EXPLORATION, prototype landed)

**Maintainer idea (2026-07); the design conversation settled the MODEL, but it
is NOT yet a committed canon decision.** Dissolve one-square Brimley into
per-building scenes connected by a dark liminal IN-BETWEEN, so the fold is FELT
moment to moment (you get lost) rather than told. This OVERTURNS the current
preserve (NARRATIVE §5 / #4: "Brimley stays ONE square scene") and unparks the
reshape (#8) in a new, engine-aligned form (a **scene graph + a generator**, not
the parked heightfield / organic reshape). Reconcile NARRATIVE §5 + DESIGN §7
ONLY if/when the restructure is committed and wired.

**The model (locked in conversation):**
- Three layers: **interior -> yard -> safe path <-> lost spaces**. Buildings hang
  off a **safe lit PATH** (the paved road, lamp posts, NO tricks, navigable).
- The **lost spaces** are the dark liminal fields (corn / forest / road) you fall
  into off a **dark scene edge** (a lit edge is a wall, a dark edge is the mouth
  -- light gates entry). They are **procedurally generated, NON-REPEATING**
  (forward is always new ground, backrooms-style, NOT the torus wrap).
- The **exit is a light you HUNT**: held 6-20 tiles off, relocating out of your
  sight cone if you drift, so always escapable and always a search.
- Manipulation lives in the dark: observer-dependent layout (space reshuffles
  when unlooked-at), light = the only stable/true thing, asymmetric return (the
  way back isn't the way you came), the space breathes with threat, evidence
  swaps the field for a longer/warped/more-hostile version, odd landmarks for
  variety.

**The prototype is REACHABLE now, through one mouth.** The three biome
fields, the cult presence in them, the observer-dependent dark, and the
whole loop (interior -> yard -> treeline -> fall -> hunt -> climb out) are
built and wired to the lodge yard's north/south edge; the shipping system
and its code map are `DESIGN.md` §13, how it landed is `CHANGELOG.md`. It
is still here to be judged by FEEL: one mouth on one scene is a vertical
slice, not the restructure.

**The SAFE PATH layer landed** (`DESIGN.md` §14, `scenes/safe_path.py`): the
I / L / T shape vocabulary, a five-lane road in a nine-tile corridor, lamps
that keep the whole carriageway lit (which is what makes it safe, since the
mouth only opens on dark ground), and the river both seen and crossed.
Shipping network: `country_lane` (T) / `river_road` (I) / `river_bend` (L).
So two of the three layers exist. The missing one is the YARD.

**THE YARDS (maintainer: "I want each house to have its own yard").** Brimley
has **seven enterable buildings**, so **seven yards**, one each, plus the
Lodge's existing one: church, barn, shop, schoolhouse, sheriff's office, the
abandoned farmhouse, Toby's house. (An earlier pass proposed grouping the
three facing PAIRS into shared yards; overruled -- a yard is a household's
own ground, and sharing one flattens exactly the thing the layer exists to
say.)

**Who has a doorstep and who does not (audited).** Hettie stands at the shop,
Vane at his office, Crane at the church, Toby at his house. **Mrs. Calder,
Royce and Garrick stand on open ground with no building at all**, and Old
Pell loiters at the schoolhouse step, which is not his (he is the
`vanish=False` homebody precisely because that room is empty).

**On filling the empty three with them:** the maintainer's "we can put people
without houses into some empty ones" is right in principle but the three
empty buildings are the wrong three. The **schoolhouse** and the **barn** are
where the congregation bedded down before they went below (NARRATIVE §3/§4),
and their cobwebbed emptiness is a story beat the player is meant to walk
into; the **farmhouse** is abandoned in its own name. Moving locals in
overwrites all three. So: **add three small houses** for Calder, Royce and
Garrick instead. A corn town has more than seven buildings anyway, the yard
layer wants more to do, and an empty yard that reads empty is one of the best
details the layer can carry.

**WHAT GOES IN A YARD** (the vocabulary; a yard picks from it, it does not
get all of it). The point of the layer is that you learn a household without
talking to anyone.

- **The genset, one per occupied yard, and its state IS the household's.**
  The grid died with the seal and the town runs on gasoline (NARRATIVE §5).
  Running: a warm work-bulb, a fuel can standing beside it. Dead: cold, the
  can empty on its side. One glance tells you if anyone is still keeping the
  place. It is already a prop, it is a light source, a noise source, and it
  makes the blackout (#21) land per house instead of per scene.
- **One interrupted task, and only one.** The seal was January 15; it is
  April. Firewood half split with the axe still in the round. A car up on
  blocks with one wheel never put back. Laundry frozen on the line since
  winter. Storm windows half taken down. A bed turned over and never planted.
  Three months of stasis said without a line of dialogue, different per
  household.
- **The mail.** Deliveries stopped with the fold. A box out at the road,
  which is exactly where the yard meets the safe path: stuffed with January's
  last delivery and never emptied, or hanging open and empty since. The
  cheapest legible piece of the whole fiction, sitting on the layer seam.
- **An occupancy tell readable FROM THE ROAD**, before you commit to the
  path: the path itself worn through the dead grass or grown over; a lit
  window against the dark (worth much more now the streets are barely lit);
  curtains open or drawn; a dog chain with no dog.
- **The car that will not start.** Everyone drove in and nothing leaves
  (NARRATIVE §1). How it is parked is the characterisation: squared away by
  someone who gave up early, or nosed at the road with the driver's door
  still open by someone who tried and walked back.
- **A boundary that is not a wall**: wire on wooden posts, a hedge, a line of
  stones, or just the line where the mowing stopped. Mechanically this is
  where the mouth is, so it has to READ as an edge and be pushed through.
- **A step.** A stoop, a porch, two boards. Something between the ground and
  the door so going in reads as arriving.
- **The wrong yard**, for any house a newcomer took: the same vocabulary,
  subtly off. Tools stacked too neatly. A bed dug too deep and the wrong
  shape. A husk thing on the porch rail. The door-motif chalked on the siding
  where the weather has nearly taken it.

**The minimum for any yard**: a boundary, a step, one interrupted task, and
one occupancy tell. Everything else is per household.

**OPEN, in build order:** (1) the **YARDS**, per the spec above: seven of
them plus three new small houses, generalising what `lodge_yard` does by
hand. Each yard's non-road edges are mouths like a path's flanks; (2) the
rest of the **dark manipulation layer**: the observer-dependent reshuffle
landed, but the **asymmetric return** (the way back is not the way you came)
and **breathe-with-threat** (the space stretching as the meter fills) have
not; (3) **per-chunk** landmark/exit generation + a silent **re-origin** for
a truly endless walk (today: a large finite bound + spawn-at-centre); (4) the
**ev-warp** variants (the field swaps for a longer / warped / more-hostile
version with evidence) + richer linear field features (fences, ruined
buildings you can't enter); (5) the two remaining OLD thin roads --
`gravel_road_north` (which now carries a west turnout onto the bend) and
`arrival_road` -- rebuilt as safe paths, so the layer is consistent rather
than patchy; (6) IF the maintainer commits: the full Brimley **re-home** (the
fences: the car, the well, the refuges, the descent chain) + the canon
rewrite. **THE DECISION to restructure Brimley is NOT yet made** -- the
mouth is opt-in per scene precisely so judging the feel costs no canon.

**Fences:** the safe path is never tricked; the lost space is always escapable
(the exit light stays in the 6-20 band); a THREAT never blinks out via the
observer trick (only geometry lies); keep the impossible count at one (the fold
is the one phenomenon).

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
- **LANDED en route: the light audit overlay** (`tools/light_audit.py`,
  the dev design surface: mechanical radius + visible pool + the hatched
  dark map per scene) and the COLD ruling (wall_lamp cold blue-white;
  fire demoted to prop). Next placement passes run through the audit.
- **LANDED en route: cone fixtures** (`cone=(dir_x, dir_y, half_deg)`
  per-deco kwarg in all three layers, pilot on the shop's hooded east
  lamp; `CHANGELOG.md` "Lighting"). Aim further lamps per room as each
  placement pass reaches it.
- **The light-security loop (the core).** The FIRST SLICE landed
  (`CHANGELOG.md` "Lighting"): the genset→fixtures power link exists —
  per-scene power state (`Scene.power_on`, `Game._tick_power`,
  `_genset_down` timers), the ELECTRIC kinds die in all three layers at
  once during a blackout (pool, `lit_at` gate, and the fixture art
  itself goes dark; fire is exempt) for `BLACKOUT_DUR`, and the office
  radio's static crawl runs on power (the appliance tell). Guarded by
  `tests/stealth.py` §17. **No live trigger fires a blackout now** — the
  moth flare that used to was cut with the moths (2026-07); the gas
  fuel/failure economy below is what will feed it.
  **Lit-rooms-SECURED landed via the 2026-07 Watcher spawn rule** (a
  Watcher opens only at a dark spot with line of sight to the player,
  so a fully lit room cannot open anything; `CHANGELOG.md`). **Still
  open:** player verbs (restore/switch a fixture), the fuel item +
  siphon/refill economy, and lights decaying/failing on their own.
  Keep the tension: a lit town is a town He can see.
- **Watcher variety — LANDED as the AMALGAMS** (`rendering/amalgam.py`,
  DESIGN.md §1; history in `CHANGELOG.md` "The shadows program"). Still
  open from the blessed idea set: the beam forcing individual PARTS to
  retract (per-part light burn), and the build-out reading the hold
  timer rather than a fixed ramp.
- **The blackout trigger + response — deferred to the gas system.** The
  blackout machinery landed (a room's electric light dies), but its only
  live trigger, the moth flare, was cut with the moths (2026-07), so
  nothing fires a blackout in play yet. The gas-genset fuel/failure
  economy (above) is the intended trigger. Riding on it when it lands:
  the cult camp PROCESSES to a room going dark and fans out (a staged
  response, rides #23), and any screen-dim beat beyond the lights
  themselves dying.
- **Watchers-in-the-dark, remainder.** The spawn half landed (dark +
  line-of-sight spots only, 2026-07). Still open: dark-only EXISTENCE
  (a live Watcher caught by a room relighting should burn or flee, in
  any scene, not just the dim interiors) and opening them in every
  non-refuge room type. Keep the below-3 threat role.
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
channels, stealth asides) that duplicate or should live in
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
