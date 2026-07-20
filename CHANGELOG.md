# THRESHOLD — Changelog

> **This file is history, not canon.** It is the append-only record of how
> the six canon docs (`CLAUDE.md`, `NARRATIVE.md`, `DESIGN.md`, `TODO.md`,
> `DIALOGUE.md`, `VISION.md`) got to their current state, and why past
> decisions were made. **It is explicitly NOT part of HARD RULE #0's
> mandatory-read set** — the six canon docs are written to be
> self-sufficient and current-state-only; you should never need this file
> to understand what IS true today, only to understand *why*, or to look
> up a decision that predates your context. Read it when you're curious
> about the history behind a rule, chasing down when/why something
> changed, or writing a new entry for work you just landed. Never required
> before answering a question about the game.
>
> **Entries are append-only and dated.** Don't edit old entries to keep
> them "current" (that's the six docs' job) — if a past decision was later
> reversed, add a new entry saying so and let the old one stand as the
> historical record. Newest first within each section.
>
> **2026-07 doc restructure (this file's own origin).** Before this split,
> the six canon docs each carried their own change history inline —
> "(2026-07 rework, superseded the 2026-06 placement...)" narration
> threaded through current-state descriptions. That meant HARD RULE #0's
> full-read-every-turn requirement paid the cost of the entire project
> history on every single turn, including a one-line edit, and the cost
> only ever grows. This file exists to carry that history instead, so the
> six docs can shrink toward "current truth, stated once" without losing
> any of the reasoning. See the "Documentation process" section at the
> bottom for the mechanics of the split itself.

---

## Evidence & the case

- **2026-07 — Evidence reworked into Mara's trail (`TODO.md` #22, `DESIGN.md`
  §9, `NARRATIVE.md` §6).** The original model was a "pool of six, any 3"
  evidence set. Run against a rubric (must be Mara's, must be a pickup item,
  must be self-evident, one per room), four of the six failed it: the
  **Ledger** (she was never at the lodge — zero Mara relation), the
  **Preacher** (not Mara, and cult hostility was already proven), the
  **Mask** (needs the cosmology to read, and it's not hers — it's the
  keystone item), and the **Congregation** (Mara is proof, not evidence).
  Worse, "any 3 of 6 is the point of no return" was never true in play: the
  surface set was always mandatory (or Act 1 had no teeth), and the
  underground three drove no mechanic at all (every gate is ≤ 3 — cult
  wakes at 1, King arms at 3, rot caps at `min(3, evidence)`). Half the
  system was inert. Replaced with `CANONICAL_EVIDENCE` = Mara's five-station
  biography (`maras_receipt`, `maras_record`, `maras_journal`, `maras_dig`,
  `maras_room`) — felt it → did it → why → the result. The Ledger and
  Preacher now file as case **notes**; Mara herself is **proof**, not a
  counted beat.
- **2026-07 — The bear + the name-beat landed** alongside the above. New
  item `bear` (Toby's loan, tag reads Sam), optional, never gates, detonates
  once the letter is read. The bear-gated name-beat lets the PI say the
  boy's name to Mara; she seizes him, the rite cracks, and her fate is
  unchanged (2026-07 ruling: she refuses the bear and turns back to the
  dig). Invariant locked: Mara never says the name, only the PI and the tag
  do.
- **2026-07 — The PI rots, not the town (four tiers).** The world rot was
  originally built as townsfolk *converting* — `_convert_local`,
  `_turned_local_dialogue`, `ROT_TURN_LINES`, an `infested=True` body-horror
  overlay. This directly contradicted the story bible ("the wrongness is
  the place, not the people," `NARRATIVE.md` §2) — the whole layer was cut.
  Replaced with a four-tier PI interior register (`_pi_tier`/`_PI_WEATHER`/
  `_pi_framing` in `scenes/dialogue.py`) that colours each principal's
  conversation *framing* by evidence count (0 / 1-2 / 3 / 4+) while the
  NPC's own words never change. The town stays ordinary to the end; the man
  hearing it doesn't.

## World rot & Sheriff Vane

- **2026-07 — Vane's fall made player-driven (`TODO.md` #2a).** Originally
  Vane, like every other local, would auto-convert under the old rot-people
  system. Replaced with a hidden despair/hope ledger (`vane_despair`): the
  PI sharing a real discovery with him is both the hope currency and the
  trust that opens his blind-cultist testimony thread; the preacher's
  murder and the newspaper give are despair acts; net despair at
  `VANE_HOLLOW_AT` latches the hollow turn (no return); a neglect override
  hollows him regardless at 3 evidence if he was never once informed. Once
  hollow, the next office load spawns `_spawn_hunting_sheriff`, a unique
  force-chase threat, "TAKEN INTO CUSTODY" on contact.
- **2026-07 — Corpse persistence: scrapped, then reinstated in a simpler
  form.** An earlier pass removed corpse persistence entirely (no replay,
  no accumulating `mold` decay stage). The 2026-07 ruling reinstated
  persistence in its simplest form: a `dead_locals` save-arg ledger,
  `_apply_dead_locals` lays each killed local's body back down on every
  scene re-entry, no mold stage (corpses draw at 0, a clean fresh kill).
  Cultist bodies are the one exception — they last only the visit, since
  patrols are dynamic spawns and respawn by design.

## Stealth & threat

- **2026-07 — Binary hidden-flag stealth replaced with graded suspicion
  (`DESIGN.md` §12, formerly its own `STEALTH_REWORK.md`).** The old system
  was an on/off `hidden` flag. Replaced with a per-enemy `suspicion` value
  in [0,1] filled by a detection score (`los * distance_falloff *
  facing_cone * concealment`), two cover classes (leaky mobile concealment
  vs. rooted enclosed hides), SEARCH sweeping nearby hides, and a timed
  struggle mini-game on discovery instead of instant capture.
- **2026-07 — First human playtest pass on the stealth rework.** Found four
  faults: hiding spots too rare (23 enclosed hides, nearly all
  underground); corn/tall grass rendered as a flat floor tint (invisible as
  cover); no narrator boxes taught the mechanic (fixed by cutting the
  teach notices instead — wordless cover entry, the visible tuft render +
  audio cues are the only tells); and, confirmed by the numbers, "running
  around the cultist beats hiding" — cultists patrolled *and* chased at 68%
  of the player's walk speed. Landed against it: the speed ladder (King >
  sprint > locked chase > walk > scout), sprint-in-LOS multiplying
  detection score, an arm's-reach contact grab, and +7 surface hides. River
  stones (a noise-distraction throwable), the window-smash and dead-well
  variants, and the under-bridge hide landed in the same pass. **Tuning
  itself (the suspicion fill curve, sweep budget, struggle window) remains
  open** — see `TODO.md` #5.
- **2026-07 — The cult grab softened to two-touch, with a one-time warning
  first.** Originally any grab was an instant CAPTURED. Landed: the first
  cult grab of any run plays as "the Talk" (a courteous warning, not a
  capture, presented as a close-up tableau since the tableau system
  landed — see below); after that, the first grab of an encounter shoves
  the PI free (`_cult_shrug_off`), and only a second grab before reaching a
  safe scene is the capture.
- **2026-07 — The Watchers rehomed as His gaze, then made the below-3
  threat, then made light-driven.** Originally a `GAZE_BIND`
  high-visibility trigger (now retired). Rehomed as "His gaze made
  manifest" and promoted to the primary visibility driver below the
  King-gate: they spawn on a timer while the player is exposed, hold and
  drive visibility up while live, and are cleared by gaze-dispel/axe/round.
  A later pass ("no light = danger," `TODO.md` #21) extended exposure to
  mean *being in the dark* inside non-refuge interiors, with light pools
  and the flashlight as the counter (a Watcher caught in light burns out).
  True refuges (`SAFE_SCENES`, `KING_FREE_SCENES`) stay gaze-free
  throughout every version of this system.
- **2026-07 — Cult liveness pilot (`TODO.md` #23a).** Two scout-only body-
  language beats landed: a shared-clock synchrony pause (every idle scout
  in a room freezes mid-stride together for one breath) and a crossing
  hand-off (two scouts whose rounds cross stop and face each other). Both
  run after detection/suspicion score each tick, so neither ever pauses a
  threat state. Station authoring for the remaining patrolled rooms is
  still open.

## The King, the Moths, the evidence ladder

- **2026-07 — The evidence ladder built out in full.** Ev 0: town reads
  wrong but no cult patrols spawn. Ev 1: cult wakes. Ev 2
  (`KING_TURNS_HEAD_EV`): a telegraph note ("the_turning") — his attention
  finds the player, but he hasn't moved, so ev3 isn't an ambush. Ev 3: the
  roam arms, but a ~25s grace window (`KING_ARM_GRACE`) holds him at
  distance first (`the_breath` note) — the window to reach the lodge for
  the Invitation before the hunt truly begins. This staged telegraph
  (rather than an instant spike at the gate) was a direct response to
  played sessions where crossing 3 evidence felt like an ambush.
- **2026-07 — The Moths added as the King's herald and first flying
  entity** (`rendering/moth.py`, sim in `systems/rot_mixin.py`). They
  persist and stack per room the King lingers in, kindle on approach, and
  flare into a loud, visibility-spiking, cult-converging event if not
  spent in time. First flare files a note, never evidence.

## Close-up tableaux & the dialogue verb

- **2026-07 -- #13b interior-voice trim, first pass.** The maintainer's
  grievance was that "every interaction does something and never leaves the
  player thinking" -- on-screen narrator captions fire on nearly every
  world-prop examine, and several editorialize the conclusion the player was
  meant to draw. Applied the pattern "state the fact and stop" to the three
  clearest caption-only flavor examines (all non-canonical `_evidence` calls
  that write nothing to the book, none flow-guarded): the **dead well** lost
  its dry-well recap + "no way down it if there were" conclusion (the
  bottomless shaft lands alone; the re-read notice still carries the
  no-way-down fact); **`the_burning`** lost the "big enough to stand a family
  around" framing and the "what it burned was not all wood" lead-in (the
  slagged effects in the ash are the tell); **`threshing_floor`** lost the
  "the town's whole harvest, carried down and never carried back up"
  conclusion. `DIALOGUE.md` reconciled; full gate green. The fuller ~30-site
  sweep (procession candles, the ledger re-examine, placeholder one-liners)
  and the decision on the `_REVISIT_NUDGES` remain open per `TODO.md` #13b --
  they are taste calls left for a maintainer read of this pattern first.

- **2026-07 — The ask-questions dialogue verb, piloted then expanded to
  all six principals + the chorus (`TODO.md` #1).** Before this, every NPC
  conversation was a linear press-E counter. Built `ui/conversation.py` (a
  small state machine driven by float-speech `on_complete` chains +
  `dialog.show_choice`), piloted on Mr. Sable, then expanded to Toby,
  Hettie, Vane, Crane, and the chorus (Old Pell, Mrs. Calder, Royce,
  Garrick). Every principal's menu leads with the same two PI-initiated
  openers (introduce himself, show the photograph) since the sealed town
  means news doesn't spread.
- **2026-07 — Close-up examine tableaux built out to all six principal
  seats plus the Talk and the pedestal (`TODO.md` #2b).** Piloted on the
  bedroom writing desk, then landed as the presentation for every
  face-across-a-table principal conversation in order: Sable → Vane →
  Hettie → Crane → Toby → Mara (the last seat, carrying the unmask REVEAL —
  she opens listed as "One of them," masked and hooded among the
  congregation, until the greet beat pulls the mask away). THE TALK
  (the first cult grab) and THE PEDESTAL (the Sign Chamber altar, an
  object close-up rather than a person) shipped in the same arc. A sound
  pass followed (`lean_in` on open, a per-seat room tone) once the
  world-freeze was noticed to have left every close-up in dead air.
- **2026-07 — Tableau-scene environment parity pass (`TODO.md` #2c).** A
  parity audit found the close-ups showed props the walkable scene didn't
  actually carry (Hettie's till, Crane's lectern, Vane's gun cabinet,
  Sable's key rack, Toby's crayon drawings, the altar's mask). Dressed each
  walkable scene to match its close-up, one at a time, VISION-verified.

## The newspaper choice (favor economy pilot)

- **2026-07 — Landed (`TODO.md` #2).** The PI's starting April 14 paper
  became a one-copy, choose-the-recipient gift with six mutually exclusive,
  incommensurable doors (Hettie/cartridges, Royce/batteries+testimony,
  Pell/mercy, Toby/funnies, Sable/the tell of no reaction, Vane/the trap —
  the one recipient whose allocation is tracked as a hidden despair
  consequence rather than pure mood). Never evidence, never gates an
  ending. Pilot for a broader "favor economy" that has not been built past
  this one instance.

## Walls & interior geometry

- **2026-07 -- #4c interior-door rollout COMPLETE; four interiors left whole
  on purpose.** With the shop pilot, the church vestry, the barn, the abandoned
  farmhouse, the sheriff's office, and Toby's closet all doored, the rollout is
  done. The remaining candidates were assessed and deliberately LEFT undivided,
  per the settled principle (the door mechanic completes buildings that ARE
  divided but lack the leaf; it never forces a warren onto an authentic open
  space):
  - **schoolhouse** -- the fiction is a "one-room schoolhouse" the commune
    crammed into as an open dormitory ("they slept all over then"), and the
    chalk-door rite fold stands in the open middle of the floor. A partition
    would fight both the fiction and the rite geometry.
  - **lodge (common room)** -- a deliberately open-plan hotel common room; its
    col-7 counter peninsula replaced a wall on purpose, so re-walling it would
    revert that choice.
  - **lodge_hall** -- already a "hall of rooms": its rooms (the spare room, the
    two guest rooms, the loft) are separate scenes off the corridor, and its
    locked 'l' facade doors are deliberate uncanny dressing (they open onto
    nothing), not real subrooms.
  - **lodge_cellar** -- an authentic single L-shaped storage cellar, "strictly
    a one-way-down room" with no side room to divide.

  The single hotel guest rooms and the PI's bedroom are single rooms by nature.
  TODO #4c's interior-door-rollout half is closed (the wall-material Phase 4 +
  the deferred church-apse shapes remain).

- **2026-07 -- #4c: Toby's closet got a curtain (the refuge, kept gentle).**
  The kid's house was room + closet through an OPEN col-5 gap. Toby's house is
  a SAFE_SCENE refuge, so the leaf is the gentlest in the set: a maroon
  `curtain` (`add_inner_door(5, 3)`), a drape over a child's closet nook where
  a plank door would read too institutional. Shut (its default), the opaque
  drape keeps the closet the BLIND SPOT it is meant to be -- the corn dolls,
  the phantom marks, and the crayon King stay hidden until the player draws it
  back (the shut curtain blocks the sight cone; open passes). The col-5 wall is
  N-S, so it hangs across an E-W doorway. No lighting concern (the refuge stays
  flat-lit). Reachability holds (smoke [10/10]); VISION-verified four facings.

- **2026-07 -- #4c: the sheriff's office rebuilt into FOUR rooms.** First pass
  just doored the existing records gap, but the office still read as "two rooms"
  (maintainer). Redesigned the whole interior on a cross of partition walls into
  four legible spaces: a public FRONT (the entry off the field), Vane's OFFICE
  (his desk + cot, behind a see-over front counter), the back RECORDS room (the
  case board, the payphone, his ammo cabinet, Mara's booking slip), and a
  BOOKING room with the barred holding CELL. Connected by inner doors in VARIED
  walls + kinds: a see-over **`half` counter** (front<->office, the FIRST
  shipping use of that kind), `plank` leaves (office<->records swings E-W,
  records<->booking swings N-S), and the cell's `bars` gate. Every room carries
  its own genset `wall_lamp` + a candle (no dark box). Load-bearing wiring
  preserved: `maras_record` (the booking slip) stays in the records filing table
  and the ammo cache still drops there (world-persistent, no soft-lock), Vane
  still watches from his desk. Grid validated (no diagonal-only joins);
  reachability holds through the door chain (smoke [10/10] flood-fill); LOS
  correct (opaque leaves block shut, the counter + bars see through);
  VISION-verified four facings + real-view dark + a counter close-up.

- **2026-07 -- #4c: the abandoned farmhouse became a four-room warren.** The
  farmhouse was a "box + one side room"; a house warrants real rooms, and
  being abandoned it carries almost no load (just the sealed cellar hatch).
  Quartered it with a cross of partition walls (a col-6 vertical + a row-4
  horizontal meeting at a solid corner) into a KITCHEN (the entry), a PARLOR,
  a BEDROOM, and a BACK ROOM (the hatch), connected by three inner doors in
  varied walls (a curtain over the bedroom, plank leaves elsewhere; the
  kitchen<->parlor door swings E-W, the two cross-wall doors swing N-S).
  Re-dressed per room: the preserves shelf in the kitchen, the open birdcage
  in the parlor, the bed in the bedroom, the hatch in the back room, and a
  candle burning in each (the farmhouse keeps the darker gloom + candles, so
  the division needed a light in every room -- who lit them, in an empty
  house). Reachability holds through the doors (smoke [10/10]);
  VISION-verified four facings + dark.

- **2026-07 -- #4c: the barn divided into a three-room warren.** The barn was
  the flagship "box + one back stall" grievance, but its open floor is the
  commune dormitory ("they slept all over then"), which should stay open.
  Resolved by dividing the UPPER floor with a row-5 partition into a FRONT BAY
  (the entry + racked gear) while keeping the LOWER floor the open dormitory
  (all six bedrolls sit there, the read intact); the old back stall is the
  enclosed WORKROOM (Mara's journal + the sealed hatch). Two `plank` inner
  doors in varied walls: the front-bay door swings N-S (E-W wall), the workroom
  door swings E-W (N-S wall). Both start shut; a shut leaf blocks the sight
  cone, so the workroom is a real back blind spot. The division cut the
  dormitory off from the front-bay lamp, so a second genset wall_lamp was hung
  on the partition to light the sleeping floor. Reachability holds through the
  doors (smoke [10/10], no diagonal-only joins from the new wall);
  VISION-verified four facings + dark.

- **2026-07 -- #4c interior-door rollout continues: the church vestry got
  its swinging leaf.** The church was already nave + vestry + bell-tower,
  but the vestry was reached through an OPEN gap -- no door mechanic. Added
  a `plank` inner door on that gap (`add_inner_door(3, 6)`): shut, it blocks
  the sight cone, so the vestry (the preacher's quarters + the tower stairs)
  is now a real shut-able blind spot a pursuer's line of sight breaks on,
  not just a doorway. It starts closed (the preacher opens his own way
  through on his cot round; the player toggles it with E) and sits in an E-W
  wall, so the leaf swings N-S -- varied from the shop's E-W-swinging
  stockroom/pantry doors. Reachability holds (smoke routes through the gap
  tile); VISION-verified the leaf reads from all facings. Still open per
  `TODO.md` #4c: the barn, sheriff's office, schoolhouse, Toby's house, the
  Lodge interiors.

- **2026-07 -- Wall-material rollout finished: Phase 2 complete + Phase 3
  (the mine as hewn rock).** Wave 3 opted the remaining above-ground
  interiors into `_SLAB_STYLE` (`barn` + `abandoned_farmhouse` = timber,
  `schoolhouse` = plank, `lodge_hall` = plaster, `lodge_cellar` = stone, the
  first stone scene), completing Phase 2 -- every above-ground building
  interior now renders thin material-coloured walls. Phase 3 added the `rock`
  material and `_ROCK_STYLE`/`_ROCK_SCENES` (the 16 Works/Depths/Mara's-cell
  scenes): full-thick (`thick`=1.0) but the rough-outline + prism draw, so
  the hewn walls read irregular, not blocky. Because `thick`=1.0 makes
  `_wall_slab` return full-tile bands AND rock stays OUT of `_SLAB_SCENES`,
  collision/sight/nav read the tile grid UNCHANGED (the roughening is
  draw-only, the mine's stealth footprint untouched). Guarded by
  `tests/stealth.py` §16; every non-slab/non-rock scene stays byte-identical.
- **2026-07 -- Redecoration-audit deferred polish landed, and a render-recipe
  bug that had hidden a defect.** The LOW items from the 17-scene visual audit
  shipped: the bell tower got a bespoke timber bell-stock (a braced trestle,
  not a scaled table box), the schoolhouse cots were jittered off the grid,
  `_draw_hanging_figure` was redrawn as a suspended pendulum body (was a
  standing hooded blob), the lodge missing-flyer/polaroid "wall of the
  vanished" was clustered above the desk (KEPT, not cut -- surface town-dread
  dressing, distinct from the underground read that was cut), and the
  lodge_hall sampler/side-table were re-homed. The barn was also dressed as a
  commune dormitory (six bedrolls + shed belongings, Toby's "they slept all
  over then"). **The catch:** the bell-stock ran every beam E-W (planar in X)
  and collapsed to a thin diagonal stick when viewed edge-on from E/W -- but
  it "passed" a four-facing check because the ad-hoc render script never set
  `camera.yaw` (that copy lives in `_update_look`, which the headless path
  skips), so every "N/E/S/W" capture stayed at yaw 0, the NORTH facing, four
  times. A whole session of "VISION-verified four facings" was really
  north-only. Root-caused, `VISION.md`'s render recipe corrected to spell out
  the `camera.yaw = look.cam_yaw` step (+ a "confirm the room rotates" check),
  the bell-stock rebuilt with a mid-height ledger ring + N-S top caps so it
  carries members in both planes and reads as a frame from every facing, and
  the session's other touched scenes re-swept from genuine four facings (all
  clean; the rest were facing-invariant standees / wall-decos / floor-decals).

- **2026-07 — Four-stage evolution of interior wall rendering, landed
  incrementally on the shop pilot then rolled out.** (1) **Beveled convex
  corners** — chamfered the chunky 90° jut where a partition wall met open
  floor, draw-only. (2) **Thin-slab walls** — walls became real thin-slab
  geometry (not just a draw trick): `_wall_slab` returns the footprint as
  up to two bands, read by collision/sight/nav as well as both draw
  layers, so what the player bumps is what they see. Superseded the bevel
  where both applied. (3) **Rounded corners** — `_rounded_wall_poly`
  fillets free (floor-facing) corners while keeping wall-seam corners
  sharp so runs still connect flush. (4) **Per-material styles**
  (`_WALL_STYLES`: plank/plaster/timber/brick/stone, each with thickness,
  corner round, roughness, and a dark muddy tint) — a room's construction
  now reads from geometry and colour together. Rollout order: shop
  (pilot) → Wave A refuges → the three principal seats (church, sheriff's
  office, lodge) → barn/schoolhouse and the mine still open. A same-session
  rule was added after the shop pilot exposed it: two walls that meet only
  at a diagonal render as disconnected thin stubs under the slab system,
  so `tests/smoke.py` now fails any such layout.
- **2026-07 — Interior doors added as a third door kind (`DESIGN.md`
  §7).** Distinct from fade-doors (scene boundaries) and see-through doors
  (a different scene's room shown through an opening): a swinging leaf on
  a floor gap within one scene, splitting a box building into subrooms. A
  shut leaf blocks both body and sight (so it can break a pursuer's lock);
  most start closed and auto-open for NPCs. Piloted on a full shop
  redesign (an L-shaped floor → stockroom → pantry, two doors deep).
  Rollout to the remaining box-shaped interiors (barn, church, sheriff's
  office, schoolhouse, Toby's house, the Lodge) is still open per
  `TODO.md` #4c.

## Lighting

- **2026-07 — Two-family light model + shared fixture table.** Brimley's
  civic light was originally anachronistic (19th-century lampposts);
  replaced with period-correct 1994 electric (cold `yard_light` poles on
  gas `generator`s, since the fold cut the grid). All fire stays warm by
  contrast. `_draw_dark` was generalized to iterate every light-emitting
  decoration through a shared `FIXTURE_POOLS` table instead of
  special-casing `wall_torch`, so any real fixture — including underground
  candles — now casts a visible pool. Pools carry real 3D source height +
  gooseneck offset, blend additively, and cast subtractive shadows.
- **2026-07 — Interior lighting pass, then "no light = danger" Watcher
  extension (`TODO.md` #21, done as "3 then 1").** Explorable non-refuge
  interiors (shop, church, barn, schoolhouse, sheriff's office) became
  `DARK_SCENES` at a lighter gloom, lit by a new period `wall_lamp`
  fixture with candles demoted to accent. Once that shipped, the Watcher
  gaze was extended into those same rooms: being in the dark (outside any
  light pool or the flashlight beam) counts as exposure, and a Watcher
  caught in light burns out. True refuges stayed excluded throughout. The
  moth-triggered blackout and a full "Watchers exist only in the dark"
  rework were sketched in the same design session but were **not built**
  — parked pending a fresh maintainer call (`TODO.md` #21).

## The fold & portals

- **2026-07 — Portal/fold system consolidated from the retired
  `PORTALS.md`.** Landed the "one phenomenon, two presentations" model
  (doors fade; everything else is the Fold, either shown as a standing
  rift frame or hidden as a silent torus-wrap/relocation lie), the 4D pane
  construction (reusing the King's existing 4D math for the border/peek/
  crossing only, no live 4D simulation), and see-through doors gated by
  the same sight cone the open world uses.
- **2026-07 — The walk-in discovery folds were cut.** Individually
  reachable secret-area folds (the effigy grove's old corn back door, the
  `husk_grove`/`scarecrow_ring` clearings) were removed once the story
  settled that the congregation walked to the grove openly before the
  closing rite claimed everyone at once — there was no honest way for a
  lone tile in the corn to still "discover" a hidden site the whole town
  once walked to in the open. `effigy_grove` survives as the rite-hidden
  clearing, reached only through the school rite's pane.

## The Works, the mine, and cast fiction

- **2026-07 -- #14 level-design half landed: side-dug chambers off the mine
  halls.** Timbered side-chambers were cut off four box/cruciform Works/Depths
  rooms -- the Timber Racks (`well_passage`), the Sorting Hall (`works_sorting`),
  the Kneeling Hall (`depths_hall`), and the Cistern (`works_cistern`) -- each a
  FINISHED store (crates, staged goods, a kept candle, a wall tally) and/or a
  HALF-DUG niche (a low spoil pile, pick gouges, no light), reached through a
  single timbered ADIT off the floor, cut into a sealed wall block clear of the
  patrol lane so the tuned crossings/props/hides stay untouched. The
  octagonal/cavern rooms (Shaft Floor, Scriptorium, Deepest Face, antechamber,
  threshing, Old Stores, stair) were assessed and left as-is (their `_bevel`/
  `_cavern` walls fight clean rectangular cut-ins, and each is already dressed
  as the dig); the cave-mouth adit doors were already done (`door_style="cave"`
  on every `UNDERGROUND_SCENES` room). A follow-up correction pass added the
  Cistern niche's missing spoil pile (the half-dug signature its two sibling
  niches carried) and closed a boxed dead-floor tile in the well_passage store.
  Reachability re-checked per room (smoke flood-fill); full gate green.

- **2026-07 — The killer-cult fiction scrub.** Early scene text implied
  the cult rendered/ate victims (a "Tallow Vats" room, bone-rack furniture,
  a bloodstain layer). All of it was purged once canon settled that the
  cult **claims souls**, not bodies — `works_cistern` (was "Tallow Vats")
  is where the dig broke into the underground river; `the_cells` are bunk
  cells, not captivity; `the_old_stores` replaced a bone vault. Guarded by
  a `tests/flow.py` token scan of the mine scene source so the fiction
  can't silently regress.
- **2026-07 — Time-loop language scrub.** Early lines implied the fold was
  temporal (days repeating). Corrected throughout: the fold is spatial
  only: roads loop, the calendar runs forward and stopped in January.
- **2026-07 — Named the principal locals.** Role-tags ("the Sheriff," "the
  Preacher") became names (Hollis Vane, Rev. Asa Crane, Hettie, Toby, Mr.
  Sable) once it was noted a small town's residents would know each other
  by name.
- **2026-07 — The unnamed "newcomer woman" NPC cut entirely.** An
  unexplained welcomer on the farmhouse path read as noise rather than
  dread; removed outright, along with the people-convert layer she rode
  (later fully superseded by the PI-rot rework above).
- **2026-07 — Carcosa palette re-graded off pale-teal/green onto the
  codified black + dim-gold family** (`TODO.md` #19), matching the SEAL
  ending's reference image. Landed pending a maintainer visual sign-off.
- **2026-07 — `symbol_portal_room` and `diner_gas_station` removed
  outright** once their only access points became dead ends by design (the
  farmhouse hatch nailed shut, the car moved to the lodge yard). Saves are
  in-memory only, so there was no persistence concern in cutting them.

## Brimley geography

- **2026-07 — Brimley rebuilt from 100x100 to 60x60 (`TODO.md` #18), a
  full reshape, not a scale-down.** The river moved to a central spine
  with a bridge crossing, all seven buildings redistributed around it,
  the well/noticeboard/wheelbarrow gathered into an eastern lodge square.
  Shape stayed a square with the torus wrap + fog rim underneath — nothing
  about the boundary changed, only the redistribution. A follow-up pass
  reoriented every building's door onto the wall facing its adjacent road
  (a natural mix of N/S/E/W instead of a uniform south-facing row).
- **2026-07 — A further river-centered rebuild was approved in concept but
  is not yet built** (`TODO.md` #4b) — the current layout still has 6 of 7
  buildings on one bank.
- **2026-07 — Terrain/reshape megabuilds parked.** A round/organic Brimley
  reshape and a general floor-roll heightfield were both explicitly
  decided against: at the ~55° tilt camera, a crest tall enough to occlude
  a standing figure over a short outdoor sightline is a near-cliff, not a
  gentle hill, so the geometry investment doesn't pay off at this camera
  angle — the tilt + sight-cone + fog rim already buy most of the
  illusion for free. The carved river channel (a controlled trough shape)
  shipped instead as the one heightfield use that dodges the cliff
  problem. See `TODO.md` #8 for what stays parked.

## Save model

- **2026-07 — Save model simplified to one disk slot, autosaved on
  evidence pickup.** Earlier iterations saved at the cot. The current
  model: the cot is a pure REST (heal + visibility cool, no save); the
  only save writer is evidence pickup (`Game._autosave`), snapshotting a
  cooled visibility so a reload never lands in a maxed-out death. A death
  or quit costs progress since the last clue, never the whole run.

## Interaction-logic bug sweep (from the retired `STORY_AUDIT.md`)

- **2026-07 — Every C-tier interaction-logic bug found in the story audit
  was resolved.** `C1` a fast Mara exchange could clobber the lure caption
  (fixed by holding the rite-holder closer while narration is active).
  `C2` a death/quit mid-staging could eat the next run's calling-out
  (`_reset_run_state` now clears `_mara_stage`). `C4` the cellar-key
  pickup gave off dialogue for a plain key (deleted outright, quiet
  walk-over pickup only). `C5` a church "LOGIN terminal" gave an
  always-"ACCESS DENIED" ARG-game tone in a 1994 parsonage (removed
  outright). `C7` "You dream of a doorway" could render outside rite mode,
  contradicting the dream-once canon (gated to rite mode only). `C10`
  Garrick's "days now" beat could fire before the preacher's body was
  found (gated to match Vane's condition). `C12` the hollow sheriff's
  intro sting re-fired on every load (now once per run). `C13` Sable's
  fold reproach could be a lie if the player hadn't actually walked a fold
  (now requires `crossed_a_fold`, not just having heard the note). `C14`
  several dead `[E]` cues with no handler were dropped or given a deadpan
  notice. `C15` the blast's lone-trigger point-of-no-return got an
  explanatory comment (it's deliberate — the fork is spent upstream).
  `C16` the go-back-to-Sable's-desk pointer could be missed by a player
  who never formally greeted him (requirement dropped). `C3` was found to
  be moot on re-verification (the audit's reasoning was wrong — the path
  it worried about is reachable). `C6`/`C8` were unreachable dead code,
  deleted in an earlier sweep; `C9`/`C11` were already resolved before
  this pass. Every fix landed with its own regression guard.
- **2026-07 — The code-health audit's findings were fixed on-branch**,
  down to one deliberate awareness-only item (function-size hotspots — see
  `TODO.md`'s "Standing fences," L5). Everything else that audit raised
  was actioned, not deferred.
- **2026-07 — A Fable prose/tense sweep landed** across every
  ended-arrivals line that had drifted into present tense describing a
  past event (Crane's greet + intro, Sable's "faces came," Vane's "kept to
  their own"), and the narrator-voice "vanished into the corn" line was
  cut everywhere except Crane's own testimony (kept deliberately there —
  it's his fallible impression, in his own mouth, not the narrator
  asserting it).

## Documentation process

- **2026-07 — The six-doc canon consolidated from many per-topic docs.**
  `CAMERA.md`, `PORTALS.md`, `STEALTH_REWORK.md`, `AUDIO.md`, and two audit
  files (`STORY_AUDIT.md`, `CODE_HEALTH_AUDIT.md`) were folded into
  `DESIGN.md`/`NARRATIVE.md`/`TODO.md` and deleted, on the reasoning that
  scattered per-topic docs let canon drift out of sync with itself. Their
  substance is now indexed above under the section it landed in.
  `GAME_CHANGES.md` (a canon-alignment tracker) was folded into `TODO.md`
  the same way.
- **2026-07 — HARD RULE #0 introduced.** Full-doc reads before every
  response were made mandatory after canon broke "repeatedly" under
  lighter-touch approaches (partial reads, reliance on memory, grep-only
  lookups) — a real, recurring failure mode this rule was written to stop.
  A code-review pass the same era ("a new set of eyes") observed that the
  six docs' size had grown enough that the rule's *cost* was becoming
  disproportionate to trivial tasks, and that the docs mixed current-state
  facts with the entire history of how they got that way, meaning full
  reads paid for both every time. This changelog, plus the compaction pass
  that shrank `TODO.md`/`DESIGN.md`/`CLAUDE.md`/`NARRATIVE.md` to
  current-state-only content, is the resulting fix: same full-read
  guarantee over substantially less text. `README.md` was also brought
  under the "docs are part of the change" contract as a thin pointer file
  rather than a second copy of facts that can drift (it had: it described
  a save model two generations out of date, and a controls table missing
  the tilted-camera mouse-look entirely — see the review that prompted
  this pass). An automated `tools/check_canon_keys.py` CI check was added
  the same pass, to catch load-bearing key drift mechanically rather than
  relying solely on a full read catching it.
