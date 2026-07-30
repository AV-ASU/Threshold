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
>
> **Ticket numbers are STABLE IDs, never an order.** Code comments and the
> other docs cite them, so a number is never reused, renumbered, or
> recycled when a ticket is cut — the order lives in the timeline below.
> A retired number is retired forever: cite the canon home
> (`NARRATIVE §n` / `DESIGN §n`) or `CHANGELOG.md` instead, never the dead
> number. Guarded by `tests/conventions.py` check 13, which fails on any
> `TODO #n` reference in the code or the docs that no longer resolves here.
>
> **Model tags:** each ticket is marked **[Opus]** (systems reasoning,
> geometry, rendering, correctness) or **[Fable]** (prose, voice,
> atmosphere). A few straddle and say so. Routing hint, not a rule.

---

## THE TIMELINE

One order for everything open, so the work stops being a pile. Phases are
sequential; items inside a phase are not. Nothing below is blocked on
anything above it except where it says so — the order is about **what the
game most needs next**, and the maintainer reshuffles it freely.

| # | Phase | Ticket | Why here |
|---|---|---|---|
| 1 | **IN FLIGHT** | **#26** the in-between + the town layer | The live rework: the yards and the paths between them, away from Brimley |
| 1 | | **#25** the storm | The live threat rework; three items left, art-first |
| 2 | **Standing asks** | **#28** cut the calendars | A maintainer directive with a canon hole to fill first |
| 2 | | **#27** remake the town sign | A maintainer directive; retires the last font-rendered lettering |
| 2 | | **#13b** quiet the routine reactions | A maintainer grievance; one ruling, then ~30 small cuts |
| 3 | **Make the case compound** | **#1** evidence askable | The story audit's central finding: finding and asking never touch |
| 3 | | **#12** Royce the trucker | The chorus thread the shop's bare shelves already imply |
| 3 | | **#2** the favor economy | Direction-stage; rides #1's conversation work |
| 4 | **The rooms and the ground** | **#24** the interiors program | Rooms read as prop soup; the biggest look debt in the game |
| 4 | | **#4** outdoor dread composition | The weakest dread zone; needs ONE scene named to start |
| 5 | **The pillar** | **#21** light is the pillar | The mandated ONE system to perfect; wants the rooms lit first |
| 6 | **Systems depth** | **#23** cultist + local behavior | Wants the #5 tuning pass to absorb it |
| 6 | | **#4c** freeform walls (Phase 4) | The wall program's north star; unlocks the deferred church shapes |
| 7 | **End-stage** | **#17** the ancient altar | A set-piece cap; needs a site now that Brimley is a street string |
| 7 | | **#20** endings redraw | Parked pending a fresh decision |
| 7 | | **#16** packaging | Do near ship |

**The two in Phase 1 are what is actually on the bench right now** (maintainer,
2026-07: *"the storm is still something I am working on. We are trying to set
up those paths in between each scene's yard, we are trying to abandon
Brimley"*). Everything under them is queued, not started.

Off the timeline on purpose: **#5** and **#6** need a person at the keys
(below); the **dead ends** are closed and listed so they are not
restarted; the **standing fences**, **optional polish**, **voice polish**
and **process** sections are reference, not sequence.

---

# Phase 1 — IN FLIGHT: the town layer, and the storm

### 26. **[Opus + Fable]** The in-between — the manipulation layer's remainder

The three-layer world SHIPS: **interior → yard → safe path ↔ lost spaces**
(`DESIGN.md` §13/§14/§15). The lost fields, the safe path, the yards and the
retirement of the one-square town all landed (`CHANGELOG.md`).

**WHERE THE TOWN STANDS TODAY** — the abandon-Brimley work is DONE, and this
is the whole surface, verified by loading it (`brimley` is out of
`SCENE_BUILDERS`, guarded by `tests/flow.py`; every yard reaches a street,
every street chains to the next, and the whole thing walks from
`arrival_road`):

| street | households off it |
|---|---|
| `arrival_road` | lodge |
| `country_lane` | *(through-road)* |
| `gravel_road_north` | *(through-road)* |
| `store_row` | school, shop |
| `chapel_row` | barn, church |
| `south_row` | farm, sheriff |
| `bank_row` | Calder, Toby |
| `lane_end` | Garrick, Pell, Royce |
| `river_road` / `river_bend` | *(the river run)* |

Ten street scenes, twelve yards, one household each, every resident inside
their own building. So what is left here is NOT the town layer — it is the
half of the model that was only ever a design conversation:

1. **The rest of the dark manipulation layer.** The observer-dependent
   reshuffle landed; the **asymmetric return** (the way back is not the way
   you came) and **breathe-with-threat** (the space stretching as the meter
   fills) have not.
2. **A truly endless walk.** Per-chunk landmark/exit generation + a silent
   **re-origin**; today it is a large finite bound with the player spawned at
   centre.
3. **The ev-warp variants** — the field swaps for a longer / warped /
   more-hostile version as evidence climbs — plus richer linear field features
   (fences, ruined buildings you can't enter).
4. **Interiors for the yard buildings that have none.** The three new
   households (Mrs. Calder, Royce, Garrick) have small one-room interiors; no
   other yard building gained interior work. Nothing needs it, and it is the
   obvious next ask.

**Judge the shipped slice by FEEL first.** One mouth on one scene (the lodge
yard's treeline) is a vertical slice, not the restructure — how many mouths
the world wants is a play question, not a code one.

**Fences:** the safe path is never tricked; the lost space is always escapable
(the exit light stays in the 6-20 tile band); a THREAT never blinks out via the
observer trick (only geometry lies); keep the impossible count at one (the fold
is the one phenomenon).

---

### 25. **[Fable + Opus]** The King as the STORM — the remainder

The storm, the apex, the migrating Mask, the face, the screech and the reach
all SHIP (`DESIGN.md` §1, `CHANGELOG.md`). Three things are left, in build
order:

1. **THE BEARER'S CATCH ANIMATION.** The apex's death card is a placeholder
   wordless fade, on purpose. It needs its own art, built from the amalgam
   grammar rather than the Unfolding's: the parts, the gold cuts, the Mask
   coming in. Hooked up and timed already (`_death_kind == "apex"`, 3.8s,
   `render_mixin._draw_death_screen`), so this is purely the drawing. Land it
   through a `VISION.md` look-pass. His deaths carry no label, so there is no
   player-facing text here and none owed to `DIALOGUE.md`.
2. **RETIRE THE UNFOLDING** (`rendering/king_unfold.py`, the `KING_UNFOLD`
   flag, and the `sprites_king._draw_king` fallback under it). The apex no
   longer touches that art at all; what remains is the roaming King's own path
   — his death card and the Carcosa cutscene (both flow-guarded) rewired onto
   the storm. **The canon reconciliation rides this:** `NARRATIVE.md` §8's
   "one pursuit, two shapes" describes the walking King because that is what
   ships until this lands, and collapses back to one shape when it does.
3. **THE STORM'S CUTS WEAR THE RIFT'S GOLD** (approved 2026-07, option
   (a)+gold, unbuilt). The amalgam apertures should read as the same portal
   family as the fold/King rift (`rendering/portal.py`): an **ANCHORED**
   gold-rimmed cut, not a billboard, with the off-angle falloff FLOORED so a
   storm cut thins yet never fully vanishes (you always sense them). Same gold
   language as the rift's rim/pool, at aperture size (gold rim + motes, no
   expensive see-through — the rift stays the only full doorway). A "pool of
   water that faces you" billboard presentation was weighed and rejected: it
   breaks the pseudo-3D "an object you can circle, not a billboard that
   swivels" canon (`DESIGN.md` §7). The **fade-until-gone dissolve is reserved
   for the CATCH beat** (a bearer reaches you → you fade into His portal),
   never routine crossing (folds stay "the crossing is nothing, the frame is
   the spectacle").

**Movement ideas discussed and NOT chosen** (open directions, pick or drop
deliberately rather than drifting): it uses APERTURES instead of pathing (sink
and rise past a wall rather than walk around it — the migration machinery
already exists); STILLNESS instead of idling (perfectly motionless, facing
you, at the edge of the light); speed tied to whether you are LOOKING at it
(inverts the family's own gaze rule, so the player's trained instinct becomes
a cost); and arriving ALREADY THERE rather than walking in.

**Fences:** the Mask stays player-scale and a real 3D object (it turns to face
you or away, never a billboard); **one bearer at a time**; the flood
concentrates on His last *sense* of you, not your true position
(luck-not-omniscience); **the impossible count stays at one** — the storm's
face is a SLICE of Him, never the keystone object (`NARRATIVE.md` §6a, guarded
by `tests/conventions.py` check 12); light SLOWS and repels the storm and
never burns it (burning stays the Watchers' privilege).

---

# Phase 2 — the standing asks

### 28. **[Opus + Fable]** Cut the calendars (maintainer: "I hate it")

**Maintainer ruling: remove the calendars from the game**, including the beat
built entirely on one (Old Pell's) — explicitly acknowledged and accepted.
This is a canon change, not just a prop deletion, so it needs a decision on
the replacement before it is built:

- **The prop.** The `calendar` decoration (`entities/deco_horror.py
  _draw_calendar`, placed in `scenes/yards.py` on Old Pell's own siding and
  read in the Vane tableau's dressing). Removing it also clears that file's 3
  `FONT_BUDGET` entries (the month/day label), so the guard tightens for free.
- **Pell's whole thread rides it** (`scenes/dialogue.py`, `scenes/yards.py`):
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
**Do both signs in one pass so they cannot disagree:** the SPREAD ending's
drive-out board (`rendering/spread_drive.py _sign_back`) still carries the old
blank-back shape — its proportions/posts need to match the new board (the back
stays blank/unpainted by design; only the shape agrees). Verify that half with
a headless capture of the SPREAD drive-out.

### 13b. **[Fable]** Interior voice — quiet the routine reactions

**The maintainer's grievance: "every interaction does something and never
leaves the player thinking."** On-screen PI narrator captions still fire on
nearly every world-prop examine. Cut candidates (~30 sites, prop examines that
editorialize a conclusion instead of stating the fact): the lodge
register/ledger recaps, the well / news-rack monologues, headstone +
candle re-examines, `bell_tower` / `the_fall` / `threshing_floor` /
`works_cistern_seen` / `the_doorframe` flavor `_evidence` calls (these write
nothing to the book — caption only). Trim each to a terse factual line or
silence, so the player draws the inference.

**One ruling first:** the revisit-nudges (`_REVISIT_NUDGES`, the "I should go
back and ask him" appends) are the clearest instance of "the game does the
thinking for you" — decide with the maintainer whether they go. #1 assumes
they do (a question that is simply THERE when he arrives is the same beat
without the hand-holding).

**KEEP, do not touch:** the five `CANONICAL_EVIDENCE` beats, the
descent-voice arc, the dream, the Mask temptation, Mara's calling-out, the
fold notes, the threshold recognition, and the deliberate atmospheric
one-shots that ARE the dread (the frozen news rack, the empty church).
Each cut must keep the `tests/flow.py` guards green (§16, §17b/c/d, §24
assert on several of these captions/notes) and update the ones whose
behavior legitimately changes.

---

# Phase 3 — make the case compound

### 1. **[Fable]** Make evidence ASKABLE — the investigation loop

**What the 2026-07 story audit measured.** Of 31 authored questions across the
whole cast, three opened on something the PI had found, and two of those three
were the Ledger, which is not case evidence. Not one of the five canonical
pieces except the journal opened a question anywhere. You could lift Mara's
booking slip out of the Sheriff's own cabinet and never mention it to the
Sheriff. Finding and asking were parallel activities that never touched, so
the case accumulated instead of compounding, and the town went inert once
every principal's rows were spent.

**The shape.** A find should open a question with the person it came from, or
the person it points at. No new systems: the engine already does it with
`avail` + `beats`, and the whole pattern is worked in Vane (the detention
night, the pilot — `CHANGELOG.md`).

**Open, in build order:**
- **Garrick's witness** — canon since `NARRATIVE.md` §6 / `DESIGN.md` §9 and
  still unbuilt: he saw her curse at the sky, and Vane's `the_night` already
  points at him without naming him. He has exactly one question today. This
  closes the detention night at both ends and is the payoff for the pilot's
  unpointed lead, so it goes first.
- **The receipt** → Hettie (a year of her own handwriting), Vane (paper with
  dates, his stated appetite).
- **The journal** → Crane (she sat his pews twice, so he can date when she
  stopped), Toby (the barn he named).
- **Not the deep two.** The dig leaf and the letter reach nobody by design;
  there is no one down there to tell, and that isolation is doing work.

**The gate pattern** (from the maintainer's pass on Vane): a **POSSESSION**
gate hides the row (you cannot ask about a thing you are not holding), but a
**TRUST or disposition** gate does NOT — the question is askable and the
character refuses it in their own voice, naming what would change their mind.
Hidden options teach nothing; refusals are characterisation and a reason to
come back. The refusal branch must never fire the grant.

**Fences:** a statement is a note, never evidence (`NARRATIVE.md` §6); the
lead is stated, never pointed at (no "I should go ask him" append — see #13b);
every new line lands in `DIALOGUE.md` in the same commit.

### 12. **[Fable + Opus]** Royce the trucker + the rusting semi

Promote Royce to the man who drove Brimley's supply run (Hettie's shelves are
bare because *his* deliveries stopped). **[Fable]** a small dialogue nudge (he
ran the route, goods in and out) — his newspaper exchange already carries some
of this; confirm it's enough or add the nudge. **[Opus]** place his
picked-clean semi rusting at the town edge (optional light scavenge, never
evidence) — it wants a road or yard scene now that there is no town map.
Reconcile with his worker job-loop.

### 2. **[Fable + Opus]** The favor economy — beyond the newspaper pilot

The newspaper's one-copy, six-recipient choice shipped as the pilot
(`CHANGELOG.md`). Still open, direction-stage only:
- **Requests variant (same engine):** a local asks for a thing → fulfill /
  refuse / SUBVERT (use it another way) → the town feels it.
- **Fences to hold if this grows:** rewards stay **incommensurable** (no
  dominant pick); **never evidence**; the ripple is **mood, not a meter**; it
  **never gates an ending**; **existing verbs only** (give via E / dialog).

---

# Phase 4 — the rooms and the ground

### 24. **[Opus + Fable]** INTERIORS PROGRAM — ensembles, floor plans, the prop fifteen

**Maintainer directive (2026-07 playtest): "props seem scattered without any
purpose... treat what you have as multiple props touching each other and make
those into ONE new object with more handcrafted detail."** The rooms read as
prop soup; the fix is composed ensembles, not more placement.

- **THE ENSEMBLE RULE.** Props that touch each other or a shared wall merge
  into ONE handcrafted multi-tile object (a `SOLID_PROPS` volume with a
  designed silhouette), authored for the projection, never re-scattered as
  separates. Design each from the FIXED CAMERA's four facings, E/W FIRST (the
  historically weakest angles).
- **REAL FLOOR PLANS FIRST.** Before re-dressing a room, sketch it from a real
  reference plan (1990s Minnesota cabin / small hotel / farmhouse): work
  zones, walk lanes, furniture against walls, one focal wall using volume and
  negative space. Provenance stays king (SCENE-DRESSING PROCESS, `CLAUDE.md`).
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
  15. wardrobe with the robe made legible (Sable's closet: the tell reads the
      moment you round the partition, no squinting).
  Each through the render-first loop (preview sheet → approve → place).
- **15 INSIDE + 15 OUTSIDE (maintainer refinement).** The fifteen above are
  the INTERIOR library; a matching EXTERIOR fifteen follows (porch ensemble,
  lean-to + stacked wood, clothesline, rain barrel + gutter, fence-and-gate
  runs, mailbox post, burn barrel, machine shed face, pump + trough, chicken
  wire pen, propane/fuel tank, junk pile, tarped equipment, porch chair +
  rifle, antler-over-door). Same rules.
- **USE ALL SIX SURFACES.** This is a 3D environment: on top of, next to,
  underneath, hung from walls, standing on floors, and dropped from
  ceilings/rooflines are all placement options. An ensemble is allowed to span
  floor-to-ceiling (stovepipe up through the roof, hams hung from beams, a
  wall of pelts reaching the eave).
- **ANIMATE WHERE IT EARNS IT.** Each ensemble asks: could a part move, and
  does the world state show through it (a TV that plays static only while the
  genset runs, a stovepipe that smokes when lit, a fan that turns)? Powered
  behavior rides the light pillar's genset link (#21). Not everything can or
  should move; a still room with ONE moving thing is scarier than a busy one.
- **EVERY ENSEMBLE SHIPS ITS WEAR LAYER, WORLD-SPACE.** The object's years
  (rust, soot, scratches), its stains on the surfaces around it (the floor
  wears where feet stood), and at least one piece of honest mess — with FEW,
  BIG, DISTINGUISHABLE items, never same-weight speckle. Every mark is
  projected geometry in its true plane (a plate is a world-plane circle);
  screen-aligned marks are error class 7. The floors set the bar; the decor
  rises to it.
- **Rug rework rides along:** the rug must read from every facing (its
  pattern/fringe currently only reads from N).
- **Blank building faces:** E/W exterior shells (the backwoods cabin is a bare
  grey slab from the side) need relief — windows, timber framing, a lean-to,
  stacked wood — via the exterior library, not one-offs.
- **Where the rollout stands.** The lodge common room was the pilot; wave 2 has
  landed the shop's stockroom receiving corner and the sheriff's office quad
  (`CHANGELOG.md`). **Next rooms:** the office's booking/waiting corners if
  they earn it, then the church vestry.

### 4. **[Fable + Opus]** Outdoor dread — the composition pass

Open ground is the game's weakest dread zone (long sightlines, reads as an
open field). This ticket also absorbed the standing **liminal-composition**
direction (composed emptiness, long sightlines, uncanny repetition; the
retired #7) — the two were separate tickets saying the same thing, and this is
the one aimed at a zone that actually needs it. The heavy-tech answers (a general ground
floor-roll, a whole-map reshape) are parked on purpose (#8) because the tilt
camera + blind-spot sight-gating already buy most of the geometry illusion for
free. The lever is **composition** with tools already shipped:
- **Corn + treeline as outdoor walls.** Denser stands, winding corn lanes that
  break the long shot, a treeline that closes the rim. Draw + placement only;
  the billboards + `_corn_runs` LOD already exist.
- **Fog / mist volume** between the player and the distance, shortening the
  effective sightline. Rides the skybox/void rim, already ~80% there.
- **Landmark repetition + same-scene silent folds** (`Game.cross_fold`,
  draw-only) for the "handed back / the town rearranges" uncanny with no sim
  change.
- **Turf HILLS + unified roof caps** (shipped for the grove mine mouth): the
  `turf` wall material (grass top, stone sides, via `top_tint`) + the
  `hill_cap` dome prop raise a grassy hill from the game's OWN wall geometry —
  real occlusion + relief for an outdoor scene, static/correct from every
  facing, WITHOUT the parked heightfield floor-roll
  (`rendering/props.py`, `scenes/terrain.py _WALL_STYLES`).

**To turn into work: name ONE scene and the ONE composition it gets** (this
sightline broken by this corn lane, this landmark passed twice in fog). Do not
start against the abstract goal. Keep the sim Euclidean-honest so stealth
distance-falloff + NPC nav stay true under any presentation lie.

# Phase 5 — the pillar

### 21. **[Opus + Fable]** LIGHT IS THE PILLAR — the perfected system

**Maintainer mandate: after the quality-floor sprint, light is the ONE system
to perfect** — the game's missing mastery verb. The doctrine that keeps it
coherent with everything shipped: **light is safety from the small things and
a beacon to the big one** (Watchers die in it; the flashlight burn + the
King's attention still price it).

**Read "safety" as ACTIVE, not passive (ruled 2026-07).** Light is a WEAPON
and a DENIAL, never a hiding place. It kills Watchers and it takes away the
dark spots they need to open. It does **not** shelter you: standing in a pool
is not cover from the gaze, and standing in the dark is not cover from
anything. The player's tool is the beam they point, not the square they stand
on. Every future item here is judged against that: **a light verb that makes a
tile safe is the wrong verb.**

Landed already (`CHANGELOG.md`, "Lighting" / "The light pillar"): the lighting
foundation, interior lighting, `WATCHER_LIGHT_BURN`, light working everywhere,
the flashlight on the PI's desk, the light audit overlay
(`tools/light_audit.py` — run placement passes through it), the COLD ruling
(`wall_lamp` cold blue-white, fire demoted to prop), cone fixtures
(`cone=(dir_x, dir_y, half_deg)`, pilot on the shop's hooded east lamp — aim
further lamps per room as each placement pass reaches them), the
genset→fixtures power link, and the Watcher spawn rule that makes a fully lit
room secured.

**Open, in build order:**
- **The gas economy — the core, and the missing trigger.** The blackout
  machinery exists (`Scene.power_on`, `Game._tick_power`, `BLACKOUT_DUR`, the
  ELECTRIC kinds dying in all three layers at once) but **nothing fires a
  blackout in play** — the moth flare that used to was cut with the moths. The
  fuel item + siphon/refill economy is the intended trigger, alongside lights
  decaying and failing on their own, and the player verbs to answer it
  (restore/switch a fixture). Keep the tension: a lit town is a town He can
  see.
- **Riding on the gas economy when it lands:** the cult camp PROCESSES to a
  room going dark and fans out (a staged response, rides #23), and any
  screen-dim beat beyond the lights themselves dying.
- **Dark-only EXISTENCE (the Watcher remainder).** A live Watcher caught by a
  room RELIGHTING should burn or flee where it stands, in any scene, not only
  when the player's beam finds it — this is light acting on THEM, so it is the
  right kind of rule. Keep the below-3-evidence threat role. The old "a lit
  spot is cover from the gaze" half was CUT; do not rebuild it in any scene.
- **Amalgam light response.** From the blessed idea set and still open: the
  beam forcing individual PARTS to retract (per-part light burn), and the
  build-out reading the hold timer rather than a fixed ramp.
- **The capture thread.** `capture → King unleashed` and
  procession-across-scenes staging sit here, unscoped. **The fork is RULED:
  capture is GAME OVER** — the CAPTURED card stays a hard run-end, no
  capture-as-continuation. The corollary work item: cultists must EARN that
  ending (the "cultists feel too weak" playtest note), which lands through the
  #5/#6 tuning loop, not a new system.

---

# Phase 6 — systems depth

### 23. **[Opus + Fable]** Complex behavior for cultists and locals

Built in pilots, inside hard fences: systemic not scripted; the people do NOT
change (only the cult may act wrong, and only in cult ways; locals stay
mundane and never signal the cosmology); nothing touches the pacing ratios,
the `SAFE_SCENES` refuge, fold-only pursuit carry, or the Talk/two-touch
gates; no new behavior ships with explanatory player-facing text (the behavior
IS the tell); the King and hollow Sheriff keep their exemptions.

- **23a remainder:** job-station authoring for the patrolled cult rooms that
  have none (`works_sign`'s lone patrol) — place via the SCENE-DRESSING
  PROCESS (render first, never by name). The synchrony + hand-off beats
  themselves are landed (`CHANGELOG.md`).
- **23b. The town half.** The **yield**: a local a cult patrol passes steps
  off the lane, eyes down, waits, resumes; the cultist never acknowledges
  them. **Mundane witness reactions**: a local who sees the drawn gun or a
  sprint flinches or hurries indoors (rides homebody `_inside`); a kill nearby
  empties the street for the visit. Strictly mundane reactions only.
- **23c. The mechanical pieces, sequenced for the #5 tuning pass.** SEARCH
  **sweep partition** (multiple searchers divide `sweep_points`, no duplicate
  checks); **room posture** (a per-scene calm/uneasy/roused int raised by
  shots, struggles, found bodies, decaying; modulates walk speed, scan time,
  sweep budget — ship OFF-default behind config until the #5 tuning pass
  absorbs it); the **flank call** (a locked chaser pulls at most one nearby
  patrol to a flank point, same LOS/suspicion rules, normal search timer,
  never soft omniscience); **object-state investigation** (a left-on
  noisemaker, an opened door: pause at it, mark the room uneasy).
- **23d. Content passes (anytime, Fable).** Fuller local **day-loops** on the
  JOBS `stations` plumbing (Pell to the field edge he doesn't look at, Calder
  to her gate, Royce circling his truck; door-anchor honesty rules apply);
  **disposition framing** read off existing save flags (mood, never a meter).
  The last of the food-scarcity pass belongs here too: the domestic-horror beat
  of a cultist eating an ordinary meal at a counter (`DESIGN.md` §4).
  Wallpaper, not a mechanic.

### 4c. **[Opus]** Wall program — Phase 4 (freeform walls)

The interior-door rollout and the wall-material rollout (thin-slab + rounded +
per-material styles, Phase 2 every above-ground interior, Phase 3 the mine as
full-thick hewn `rock`) are COMPLETE (`CHANGELOG.md`, "Walls & interior
geometry"). **Still open:**
- **Phase 4 — freeform walls** (the north star): a wall SEGMENT primitive off
  the tile grid, unlocking diagonal walls, a curved church apse, a round
  silo/tower. Prototype ONE curved feature first.
- **Deferred church shapes** (the curved apse / arched-window geometry) wait
  on Phase 4.
- **Cross-cutting:** thinner walls occlude less, so re-derive interior cover
  as styles land; extend `tests/stealth.py` §16; VISION toward the Darkwood
  organic read.

---

# Phase 7 — end-stage

### 17. **[Opus + Fable]** The ancient altar — the CAP of the last sealing

The spent surface altar over the point the Threshold sits beneath: pre-cult
dressing, lichened, weathered, sunken, nothing yellow, reading OLDER than
every cult mark. ONE worn carving that recontextualizes after the player has
seen the Sign (matches the Mask grammar) + a single `notes` beat (never
evidence, no cosmology). Gives SEAL its precedent without a word.

**Needs a site.** The ticket used to say "move the mid-Brimley standing stones
to the riverbank" — there is no Brimley scene to move them from now. Pick the
river path scene that sits above the Threshold (`river_road` / `river_bend`)
and place it there with its worn cult path, or fold it into #4's composition
pass for that scene.

### 20. **[Opus + Fable]** Endings redraw with the close-up techniques

Parked, NOT scoped. The ending presentations (the King-catch furnace, SEAL's
lines-on-black tableau, SPREAD's drive-out, BREAK's mask-yank + blast) predate
the close-up tableau art pass and could in principle be redrawn with those
techniques (bespoke portrait register, reactive state, a corrected vignette
ramp — note the older shared vignette loop actually darkens the CENTER, so any
redraw should use Mara's frame's corrected ramp instead). The endings
themselves are approved, flow-guarded set-pieces (their lines + palettes are
canon), so this is a re-presentation question, not a gap. Do not start without
a fresh maintainer decision; land each ending only through a `VISION.md` look
pass. **Carcosa's colour is the one real defect in the set:** any pale-teal or
green cast is off-model (`NARRATIVE.md` §5 — black ground note, black stars,
twin suns, His gold the only light).

### 16. **[Opus]** Ship track — packaging

Itch-ready build: pyinstaller (or equivalent) one-file win/linux builds,
save-dir sanity, a settings sanity pass, a version stamp. End-stage; do near
ship.

---

# Blocked on a human at the keys

These are BUILT and guarded; what remains cannot be settled from code
inspection and needs a person playing the game.

### 5. **[Opus]** Stealth rework — the TUNING loop

The mechanic, the placement pass, and a first human tuning pass all landed
(`CHANGELOG.md`, "Stealth & threat" — includes what that pass found and
fixed). What remains proves out only against further play: the new constants'
FEEL, the suspicion fill curve (`SUS_FILL_RATE`), the concealment factors, the
sweep budget, and the struggle window/press count. Also deferred on purpose:
the Pillar-2 **peek** verb (free look under tilt already carries the
information function) and an exit-takes-a-beat vulnerability window on
enclosed hides. Spitballed and parked for a decision: the crouch stance (after
the next playtest) and the window-vault prototype (one building, look-passed,
last).

**Also needs a person walking it: how PERMEABLE the treelines feel.** Since
trees became solid with round sub-tile feet, a stand is something you thread
and the gaps fall out of the geometry, which is right and has one cost —
connectivity passing says only that SOME route exists, not that pushing north
at a treeline feels like walking rather than pinball.
`tools/band_gaps.py` measures the thing the eye cannot: what fraction of
sub-tile lanes admit a STRAIGHT walk through a band (straight, because a
player holding north holds north). Where it stands today, pushing 8 tiles in:

| scene | n | e | s | w |
|---|---|---|---|---|
| store_row | 25% | 31% | 24% | **14%** |
| lodge_yard | **14%** | 52% | 25% | 27% |
| cornfield_path | 24% | 27% | 29% | 35% |

The street's WEST band and the lodge yard's NORTH band are the two tightest
real outdoor bands in the game, and the lodge yard's north is also the §13
MOUTH, where tight may well be the point. Nothing here is broken; the question
is whether ~14% reads as a wood you thread or a wood you fight, and only a
person walking it can answer that. (The `clearing`, `effigy_grove` and
`cornfield_maze` figures the tool also prints are hard tree WALLS with one
authored doorway, so their low numbers are the design, not a finding.)

### 6. **[Opus]** Combat / difficulty — judgment calls (decide on purpose)

Not bugs; deliberate choices worth confirming rather than leaving by default:
the gun goes **stun-only at 3 evidence** with ~14 rounds total per run, so the
main combat verb is removed exactly when danger spikes (agency loss vs.
intended dread). There are **no difficulty options**, so the visibility/Watcher
death-spiral hits newcomers hard and is trivial to experts. Items are gates,
not resources (armor slots return 0). The two-touch grab softening already
landed (`CHANGELOG.md`) and directly answered the "nothing you can do once
they're on you" play-note; still open here: the gun stun-window and whether to
add difficulty options — consider transforming the stun into a tactical window
rather than a tax, an easy/hard toggle, or light resource tension, only if it
serves the horror, not despite it.

---

# Dead ends — closed, do not restart

Directions that were live enough to be written down and are now decided
against or obsolete. Kept as a short list so nobody rediscovers them; the
reasoning lives in `CHANGELOG.md`.

- **#4b — the Brimley river-centered rebuild, both banks.** Approved as a
  redistribution of 7 buildings across the river on the one 60x60 square map.
  **Obsolete:** that scene is retired and the town is a string of yard scenes
  off street scenes (`DESIGN.md` §15), so there is no map to redistribute. What
  the ticket actually wanted — the river as a spine you cross to reach the law
  — is now a question for the street network's shape, and belongs to #4.
- **A round / organic Brimley reshape** (was part of #8). Same reason.
- **Darkness as the player's cover.** `SUS_CONCEAL_DARK` and `_tick_dark_cover`
  are deleted, and light is not cover from a Watcher's gaze either. The dark is
  the CONDITION His things need, so hiding in it was hiding inside the threat
  (ruled 2026-07; guarded, `tests/stealth.py` §11 + §18). Do not rebuild
  either half in any scene.
- **The idle horizon King** (a distant standing figure on the skyline). Cut by
  maintainer ruling with the storm: the storm is the full-power apex at the
  source, and its overwhelm is the point.
- **A second Mask object.** There is exactly ONE, on the cult's altar until the
  PI lifts it; the storm's face is a SLICE of Him (`NARRATIVE.md` §6a). Guarded
  by `tests/conventions.py` check 12.
- **Capture as continuation.** Capture is GAME OVER; the CAPTURED card is a
  hard run-end (ruled). What is open is making the cultists EARN it (#5/#6).
- **A billboarded storm cut / mask.** Rejected in favour of anchored geometry
  (#25 item 3); a swivelling card breaks the pseudo-3D canon (`DESIGN.md` §7).
- **The general ground floor-roll** and the terrain directions that depend on
  it (sunken-lane cover, King crest-reveal, terrain-herding, the peek verb's
  home) stay parked, not cut — see #8 below.
- **Two dead prototypes still on disk.** `systems/storm.py` (the timer-driven
  migration engine, superseded by the earned apex hop in
  `threat_mixin`/`npc`; imported by nothing, and its docstring still states the
  superseded camera-facing Mask rule) and `rendering/pseudo3d.py` (the Watcher
  volumetric proof, used only by its own preview tool). Both are candidates for
  deletion; they are listed here so their contents are never mistaken for
  shipping behaviour.

### 8. **[Opus]** Parked — terrain megabuilds

Do NOT pull forward without a set-piece that demands it AND a fresh decision.
The reasoning lives in `CHANGELOG.md`, "Brimley geography". Cut from active
work because their payoff fights their cost at this camera. The DORMANT
heightfield prototype (`rendering/heightfield.py`, wired but no scene opts in)
and the SHIPPED carved river channel STAY — harmless. What is parked is the
general-purpose floor-roll warp and the terrain design directions that depend
on it. The **turf hill** (#4) is the cheap answer that landed instead.

---

# Standing fences (guardrails, not tickets)

- **The lure chain is NEVER stated diegetically.** King → Mara → Walter → PI
  is felt, not said. Do NOT build on any of it. King/Watcher moments read as
  **luck, not omniscience** (powerful, not infallible).
- **The corn is mundane, never the door's doing.** Keep the impossible count at
  **one**: the single unexplained door, everything else ordinary
  cause-and-effect downstream of it.
- **Sable's misdirection is never resolved in text** (maintainer ruling). He
  points suspicion at the cold old families; Hettie says the warm easy ones
  went soonest. They contradict each other, Sable is the wrong one, and **that
  is on purpose and for the player to notice.** Do NOT build a beat where the
  PI puts one man's line to the other, and do NOT file a note that draws the
  conclusion. The story audit flagged this as a gap; it is not one.
- **No dashes in player-facing text** (HARD RULE; flow-guarded).
- **L5 — complexity hotspots (awareness only, not a ticket).** The largest
  function bodies (`tests/flow.py main`, `scenes/yards.build_yard_scene`,
  `systems/render_mixin.draw_world`, `rendering/sprites_npc.draw_npc_sprite`,
  `rendering/king_unfold.draw_king_unfold`) match the project's deliberate
  "one cohesive beat per function" style and sit behind the test gate. Listed
  so growth stays a choice, not an accident — not a call to split them.

---

# Backlog — polish (no canon/lore change; do as time allows)

- **[Fable + Opus]** **Rev. Asa Crane murder reveal + sprite** — the discovery
  location + staging landed (`CHANGELOG.md`). Still open: (1) **bespoke
  sprite** — the current corpse is a placeholder medieval knight (`_draw_body`);
  replace with a gutted-preacher draw (dark palette, white collar, cross in the
  mess). (2) Stage the approach (wrongness before sight, long sightline). Art
  only; lore unchanged.
- **[Opus]** **Held-weapon offset per camera yaw** — `draw_axe_held` reads at
  rest; eyeball the equipped-weapon offset at every camera yaw so it never
  floats off the hand. Verify with a tilt capture across yaws.
- **[Opus]** **Higher-contrast see-through doors** — opt in the doors where the
  sight-gated aperture effect reads strongest: a lit room off a dark hall, the
  front door onto the yard. Draw/opt-in only; no new tech.
- **[Opus]** **Permanently-visible King through an OPEN fold** — currently he
  looms through the rift only while it forms, then steps through (intentional).
  A persistent silhouette on the far side of an already-open fold is not built;
  revisit only if the direction changes.
- **[Opus]** **Mine retrofit tail cleanups** (none player-visible) — (a) cache
  the `_tilt_rack_box` extrusion per (tile, yaw-bucket) like the wall cards
  (`well_passage` re-projects ~280 points/frame live); (b) fold `_RACK_CHARS`
  into the shared wall-scan char-set plumbing instead of a third parallel set;
  (c) the cave `door_style` key list in `scenes/__init__.py` duplicates the
  `UNDERGROUND_SCENES` gating idea, derive from one source; (d) `pillar` is a
  registered kind with no placements (keep as reusable art or cut).
- **[Opus]** **Grove mine-hill finish level-up** (deferred, maintainer "fine for
  now") — the mouth is a green turf HILL with a stone adit; its grass-dome ROOF
  got a full detail pass, but the stone side/cut faces + the adit mouth are
  plainer by comparison. Bring the stone up to the roof's finish (strata,
  cracks, a little scree/moss at the base) and make the adit read a touch more
  as the focal point, so the whole object sits at one level of craft.
  `hill_cap` (`rendering/props.py`) + the `turf` walls + `_grove_interact`
  dressing (`scenes/hidden_folds.py`).
- **[Opus]** **Louvered belfry openings** — the bell tower's belfry uses the
  glazed cottage-window char (`'i'`), which renders as glass everywhere. A
  belfry wants louvered slats, which needs its own window style or a wall-deco
  louver over the openings (a small per-scene window-style mechanism).
- **[Opus]** **Dormant plumbing to use or cut:** `Enemy.shoot_sfx` is wired and
  never fired.

---

# Backlog — voice / polish (player-facing text)

- Descent interior voice wobbles POV (first-person notes vs. second-person
  on-screen beats, `systems/game.py`) — confirm this is the deliberate
  self-vs-lure split `DIALOGUE.md` documents (`chalk_surface`/`descent_dig`/
  `chalk_deep` first-person vs. `descent_leave`/`descent_mask` second-person)
  and not accidental drift elsewhere.
- HUD fall-through labels: "Dark" (the Hive!), "Depths Antechamber", "Effigy
  Grove", "Threshold" (`scenes/base.py` fallback).
- NPC object names "Clerk"/"Sheriff"/"Preacher" leak on generic paths (corpse
  examine: "Clerk. Face-down where the round put them.").
- Placeholder texts on cued interactions: "A small stash.", "A weathered
  headstone.", "A scarecrow.", "A key.", "An axe for chopping wood."
- Small ones: Sable's "last night"/"tonight" against elapsed play; the robe
  "hangs... pressed and folded"; the Invitation's "Sleep where we slept" with
  no sleep verb at the school; threshold recognition + "A doorframe with no
  wall." fire at the cave mouth, 13 sight-gated rows before the frame is
  visible; lowercase hide notices; "waking the dark ." double space;
  "midwestern" casing; Garrick and hollow Vane both call the PI "son"; two
  simultaneous Hetties (door + counter); duplicate candle decoration in Toby's
  house.
- Missing canon clincher: `NARRATIVE.md` §4's ledger entry promises "your own
  name, signed in tonight, already among them" — the cellar text only gestures
  at it and the desk sign-in is optional; one clause conditioned on
  `register_signed` closes the loop.

---

# Process

### D. **[Fable]** Doc consolidation — remainder

The threat section moved to `DESIGN.md` §1; the tableau system, the Casebook,
and the dialogue-channel model moved out of `CLAUDE.md` into `DESIGN.md`
§11/§16 with code-map pointers left behind; the single timeline above replaced
this file's readiness buckets (`CHANGELOG.md`, "Documentation process").
**Still open:** `CLAUDE.md`'s Layout section is still the longest thing read
every turn — keep moving system narration to its one home one section per
pass, leaving a code-map pointer, so the every-turn read keeps shrinking.

### R. **[Fable]** Cross-model review gate

After an **[Opus]** ticket lands, run a **Fable** review pass before it
merges. This is NOT a code-correctness re-audit (use `/code-review` or a fresh
Opus context for that, since a model self-reviewing its own diff is the
weakest check). Fable judges what it is strongest at for THIS game: **does the
change land the feeling and hold canon.** For a given diff + the running build
it answers:
- Does it read as dread, or as a mechanic showing through? (atmosphere,
  pacing, the tell)
- Does any player-facing string break the no-dashes rule or the `NARRATIVE.md`
  voice?
- Does it contradict a locked canon fact (`NARRATIVE.md`)?
- What is the cheapest change that would make it land harder?

Output is a short verdict + ranked notes, not a rewrite. The value is a
SECOND, independent model looking at the work, so the direction can flip: if
Fable is doing the implementing, an Opus pass reviews it the same way.
