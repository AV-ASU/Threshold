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
> **Every ticket here is phrased as work that can start now.** A ticket
> that only says "wait for X" is not a ticket; either it is real work with
> a first move, or it belongs in Deferred with a one-line statement of what
> would make it worth doing. Do not write gating steps into this file.
>
> **Bullets only. Tickets have NAMES, not numbers or letters.** Cite one by
> its name ("the gas economy", "the interiors program") when you cite it here.
> The old numbering is retired: it looked stable and was not, and by the time
> it was dropped nine of the numbers still cited in code pointed at tickets
> that no longer existed. A name survives a renumber; a number survives
> nothing. The forwarding map lives in `CHANGELOG.md`, "Brimley geography".
>
> **THE CODE DOES NOT CITE THIS FILE.** Open work lives here and nowhere else;
> a comment that points at a ticket goes stale the moment that ticket lands and
> is deleted, which is exactly what happened to 183 of them. A comment cites
> `DESIGN.md` (how the system works) or `CHANGELOG.md` (why it got that way),
> or it just says the thing. Enforced by `tests/conventions.py` check 13, which
> also fails on a bare `TODO` or `FIXME` marker.
>
> **The geography is the string of house islands** (`DESIGN.md` §13/§14/§15):
> interior → yard → safe path ↔ lost spaces. There is no town map and no
> `brimley` scene; a ticket that names a cross-town coordinate is written
> against a world that does not exist. The streets are `store_row`,
> `chapel_row`, `south_row`, `bank_row`, `lane_end`; the approach is
> `arrival_road` → `country_lane` → `gravel_road_north` → `store_row`, with
> `river_road` / `river_bend` carrying the river off that approach.

> **Model tags** (2026-07): each ticket is marked **[Opus]** (systems
> reasoning, geometry, rendering, correctness) or **[Fable]** (prose, voice,
> atmosphere). A few straddle and say so. Routing hint, not a rule.

---

## Buildable now

- ### Make evidence ASKABLE — the investigation loop **[Fable]**

  Of 31 authored questions across the whole cast, three opened on something
  the PI had found, and two of those three were the Ledger, which is not case
  evidence. You could lift Mara's booking slip out of the Sheriff's own
  cabinet and never mention it to the Sheriff. Finding and asking were
  parallel activities that never touched, so the case accumulated instead of
  compounding, and the town went inert once every principal's rows were spent.

  **The shape.** A find opens a question with the person it came from, or the
  person it points at. No new systems: the engine already does it with `avail`
  + `beats`. The detention-night pilot is worked and shipped (`CHANGELOG.md`).

  Build order:
  - **Garrick's witness** — canon since NARRATIVE §6 and DESIGN §9 and still
    unbuilt: he saw her curse at the sky, and Vane's `the_night` now points at
    him without naming him. He has exactly one question today. This closes the
    detention night at both ends and is the payoff for the pilot's unpointed
    lead, so it goes first.
  - **The receipt** → Hettie (a year of her own handwriting), Vane (paper with
    dates, his stated appetite).
  - **The journal** → Crane (she sat his pews twice, so he can date when she
    stopped), Toby (the barn he named).
  - **Not the deep two.** The dig leaf and the letter reach nobody by design;
    there is no one down there to tell, and that isolation is doing work.

  **The pattern the rest of the cast follows** (from the maintainer's pass on
  Vane): a POSSESSION gate hides the row (you cannot ask about a thing you are
  not holding), but a TRUST or disposition gate does NOT — the question is
  askable and the character refuses it in their own voice, naming what would
  change their mind. Hidden options teach nothing; refusals are
  characterisation and a reason to come back. The refusal branch must never
  fire the grant.

  **Fences:** a statement is a note, never evidence (NARRATIVE §6); the lead is
  stated, never pointed at (no "I should go ask him" append — see the interior
  voice ticket); every new line lands in `DIALOGUE.md` in the same commit.

- ### The favor economy — the requests variant **[Fable + Opus]**

  The newspaper's one-copy, six-recipient choice shipped as the pilot
  (`CHANGELOG.md`). Build the second instance on the same engine: a local asks
  for a thing → fulfill / refuse / SUBVERT (use it another way) → the town
  feels it. Pick the asker and the object from the cast's existing WANTs
  (`DESIGN.md` §8) rather than minting a new need.

  **Fences:** rewards stay incommensurable (no dominant pick); never evidence;
  the ripple is mood, not a meter; it never gates an ending; existing verbs
  only (give via E / dialog).

- ### Outdoor dread — the composition pass **[Fable]**

  Open ground is the game's weakest dread zone (long sightlines, reads as an
  open field). The heavy-tech answers (a general ground floor-roll) stay parked
  — see `CHANGELOG.md`, "Brimley geography" — because the tilt camera +
  blind-spot sight-gating already buy most of the geometry illusion for free.
  The lever is **composition** with tools already shipped.

  **The named target: `farm_yard`, and the one composition is the corn closing
  the rim.** It is the cult camp's lot off `south_row`, so dread is already its
  job, and it is the clearest case of the new geography's open ground: a lot
  you cross with the camp sitting in plain sight from the road exit. Close the
  rim with a dense stand so the camp is not seen until you are committed to the
  lot, and the walk back out is the shot that was denied on the way in. Draw +
  placement only; the billboards + `_corn_runs` LOD already exist.

  The levers, once the first one is walked:
  - **Corn + treeline as outdoor walls.** Denser stands, winding corn lanes
    that break the long shot, a treeline that closes the rim.
  - **Fog / mist volume** between the player and the distance, shortening the
    effective sightline. Rides the skybox/void rim, already ~80% there.
  - **Landmark repetition + same-scene silent folds** (`Game.cross_fold`,
    draw-only) for the "handed back / the town rearranges" uncanny with no sim
    change.
  - **Turf HILLS + unified roof caps** (shipped 2026-07 for the grove mine
    mouth): the `turf` wall material (grass top, stone sides, via `top_tint`) +
    the `hill_cap` dome prop raise a grassy hill from the game's OWN wall
    geometry — real occlusion + relief for an outdoor scene, static/correct
    from every facing, WITHOUT the parked heightfield floor-roll.

  **Preserve (load-bearing) across the whole pass:** the fold road + the
  Royce/Garrick looping-roads lines; the well as dread set-dressing and never
  the way down (it is on the square, `safe_path._town_square` off `store_row`);
  every exit/local/cult station on the street network; the safe path is never
  tricked (`DESIGN.md` §14). In player-facing text the world is a bounded
  fog-edge, a void-ringed country, never an "island" — that word is the
  maintainer's dev shorthand for the layout, not a thing the fiction says.

- ### Wall program — freeform walls **[Opus]**

  The interior-door rollout and the wall-material rollout (thin-slab + rounded
  + per-material styles) are complete (`CHANGELOG.md`, "Walls & interior
  geometry"). What is left is the north star.
  - A wall SEGMENT primitive off the tile grid, unlocking diagonal walls, a
    curved apse, a round silo/tower.
  - **Prototype it on the church apse**, which is the deferred shape that has
    been waiting on it and the one place a curve is already designed for. One
    feature, look-passed, before any second use.
  - Cross-cutting: thinner walls occlude less, so re-derive interior cover as
    the segment lands; extend `tests/stealth.py` §16; VISION toward the
    Darkwood organic read.

- ### Stealth — the deferred verbs and the tight bands **[Opus]**

  The mechanic, the placement pass, and a first tuning pass all landed
  (`CHANGELOG.md`, "Stealth & threat"). What is open is buildable:
  - **The exit-takes-a-beat vulnerability window on enclosed hides.** Leaving
    a wardrobe or an under-deck hide is currently instantaneous, which makes an
    enclosed hide strictly better than cover. Give it a beat where you are out
    and not yet moving.
  - **The crouch stance.** A third movement speed under walk, with its own
    suspicion fill and its own silhouette; the peek verb stays cut (free look
    under tilt already carries the information function).
  - **The window-vault prototype**, one building, look-passed. The shop is the
    worked interior and has the frontage for it.
  - **Widen `store_row`'s WEST band.** `tools/band_gaps.py` measures what the
    eye cannot: the fraction of sub-tile lanes admitting a STRAIGHT walk
    through a band. The street's west band sits at 14%, the tightest real
    outdoor band in the game, on the scene every player crosses most. Thin the
    stand until it reads as a wood you thread. Leave `lodge_yard`'s north band
    alone — it is the lost-space MOUTH, and tight is the point there. The
    `clearing`, `effigy_grove` and `cornfield_maze` figures the tool prints are
    hard tree WALLS with one authored doorway, so their low numbers are the
    design.

- ### Combat — the stun window and the difficulty toggle **[Opus]**

  Two deliberate choices to build out rather than leave by default.
  - **Turn the 3-evidence gun stun into a tactical window, not a tax.** Today
    the main combat verb is removed exactly when danger spikes (~14 rounds per
    run, stun-only past the gate). Make the stun buy a real, readable opening:
    a fixed window where the target is out of the fight and you choose what to
    spend it on (distance, the axe, a door). Same round count, same removal of
    the kill; what changes is that the round does something you can plan around.
  - **Difficulty options.** The visibility/Watcher spiral hits newcomers hard
    and is trivial to experts, with nothing between. Add an easy/hard toggle
    that moves the fill curves and the Watcher cap, and nothing else — it must
    not open a "turn the horror off" setting.
  - Items stay gates, not resources (armor slots return 0); leave that.

- ### Royce the trucker + the rusting semi **[Fable + Opus]**

  Promote Royce to the man who drove the town's supply run (Hettie's shelves
  are bare because *his* deliveries stopped).
  - **[Fable]** A small dialogue nudge (he ran the route, goods in and out) —
    his newspaper exchange already carries some of this; confirm it's enough or
    add the nudge.
  - **[Opus]** Put his picked-clean semi in `royce_yard`, his own lot off
    `lane_end`, which is both his household and the far end of the town's
    street chain (optional light scavenge, never evidence). Reconcile with his
    worker job-loop.

- ### Interior voice — quiet the routine reactions **[Fable]**

  The Casebook structure landed and a first trim cut the three worst offenders
  (`CHANGELOG.md`). The grievance is unfixed: on-screen PI narrator captions
  still fire on nearly every world-prop examine, so the game does the thinking
  for the player.
  - **Cut the revisit-nudges** (`_REVISIT_NUDGES`, the "I should go back and
    ask him" appends). They are the clearest instance of the grievance, and the
    investigation-loop ticket is built on the opposite principle: a question
    that is simply THERE when he arrives is the same beat without the
    hand-holding.
  - **Trim ~30 prop-examine captions** that editorialize a conclusion instead
    of stating the fact: the lodge register/ledger recaps, the well / news-rack
    monologues, headstone + candle re-examines, `bell_tower` / `the_fall` /
    `threshing_floor` / `works_cistern_seen` / `the_doorframe` flavor
    `_evidence` calls (these write nothing to the book — caption only). Each
    becomes a terse factual line or silence.
  - **KEEP, do not touch:** the five `CANONICAL_EVIDENCE` beats, the
    descent-voice arc, the dream, the Mask temptation, Mara's calling-out, the
    fold notes, the threshold recognition, and the deliberate atmospheric
    one-shots that ARE the dread (the frozen news rack, the empty church).
  - Each cut keeps the `tests/flow.py` guards green (§16, §17b/c/d, §24 assert
    on several of these captions/notes) and updates the ones whose behavior
    legitimately changes.

- ### Ship track — packaging **[Opus]**

  Itch-ready build, buildable today against the current tree: a pyinstaller
  one-file spec for win + linux, save-dir sanity (`~/.threshold` /
  `%APPDATA%\THRESHOLD`, `THRESHOLD_SAVE_DIR` honored in the frozen build), a
  settings sanity pass, and a version stamp surfaced on the title screen.

- ### The ancient altar — the CAP of the last sealing **[Opus + Fable]**

  Put the standing stones on `river_road`, the length of bank the road actually
  runs beside and the scene that already carries the Preacher's remains, with a
  worn cult path to them. Pre-cult dressing: lichened, weathered, sunken,
  nothing yellow, reads OLDER than every cult mark. ONE worn carving that
  recontextualizes after the player has seen the Sign (matches the Mask
  grammar) + a single `notes` beat (never evidence, no cosmology). Gives SEAL
  its precedent without a word.

- ### LIGHT IS THE PILLAR — the perfected system **[Opus + Fable]**

  **Light is the ONE system to perfect** — the game's missing mastery verb. The
  doctrine that keeps it coherent: light is safety from the small things and a
  beacon to the big one (Watchers die in it; the flashlight burn + the King's
  attention still price it).

  **Read "safety" as ACTIVE, not passive (ruled 2026-07).** Light is a WEAPON
  and a DENIAL, never a hiding place. It kills Watchers and it takes away the
  dark spots they need to open. It does **not** shelter you: standing in a pool
  is not cover from the gaze, and standing in the dark is not cover from
  anything (the `SUS_CONCEAL_DARK` shadow-cover pass was CUT — see the storm
  ticket). The player's tool is the beam they point, not the square they stand
  on. Every item here is judged against that: a light verb that makes a tile
  safe is the wrong verb.

  The foundation, interior lighting, `WATCHER_LIGHT_BURN`, the light audit
  overlay, cone fixtures, and the genset→fixtures power link are all shipped
  (`CHANGELOG.md`, "Lighting" / "The light pillar"). Open, in build order:
  - **The gas economy — this is the keystone and it goes first.** The blackout
    machinery exists (a room's electric light dies for `BLACKOUT_DUR`, in all
    three layers at once) but nothing in play fires it since the moth flare was
    cut. Build the fuel item + the siphon/refill verbs, make gensets consume
    and fail, and let that be the blackout trigger. A lit town becomes a town
    you are maintaining, and a town He can see.
  - **Player verbs on fixtures:** restore a dead one, switch a live one off.
    Both are the beam-not-the-square rule applied to the room.
  - **Dark-only EXISTENCE for Watchers.** The spawn half landed (a Watcher
    opens only at a dark spot with line of sight, so a fully lit room cannot
    open anything). Still open: a live Watcher caught by a room RELIGHTING
    burns or flees where it stands, in any scene, not only when the player's
    beam finds it. That is light acting on THEM, so it is the right kind of
    rule. Keep the below-3 threat role.
  - **Per-part light burn on the amalgams:** the beam forces individual PARTS
    to retract, and the build-out reads the hold timer rather than a fixed ramp.
  - **The cult response to a dark room** (rides the complex-behavior ticket):
    the camp PROCESSES to a room going dark and fans out, a staged response
    rather than an alarm.
  - **The capture fork is RULED: capture is GAME OVER.** The CAPTURED card
    stays a hard run-end, no capture-as-continuation. The corollary work is
    that cultists must EARN that ending — it lands through the stealth and
    combat tickets, not a new system.

- ### Complex behavior for cultists and locals **[Opus + Fable]**

  Built in pilots, inside hard fences: systemic not scripted; the people do NOT
  change (only the cult may act wrong, and only in cult ways; locals stay
  mundane and never signal the cosmology); nothing touches the pacing ratios,
  the SAFE_SCENES refuge, fold-only pursuit carry, or the Talk/two-touch gates;
  no new behavior ships with explanatory player-facing text (the behavior IS
  the tell); the King and hollow Sheriff keep their exemptions.

  - **The cult remainder.** Job-station authoring for the patrolled cult rooms
    that have none (`works_sign`'s lone patrol) — place via the SCENE-DRESSING
    PROCESS (render first, never by name). The synchrony + hand-off beats
    themselves are landed (`CHANGELOG.md`).
  - **The town half.** The **yield**: a local a cult patrol passes steps off
    the lane, eyes down, waits, resumes; the cultist never acknowledges them.
    **Mundane witness reactions**: a local who sees the drawn gun or a sprint
    flinches or hurries indoors (rides homebody `_inside`); a kill nearby
    empties the street for the visit. Strictly mundane reactions only.
  - **The mechanical pieces.** SEARCH **sweep partition** (multiple searchers
    divide `sweep_points`, no duplicate checks); **room posture** (a per-scene
    calm/uneasy/roused int raised by shots, struggles, found bodies, decaying;
    modulates walk speed, scan time, sweep budget — ships with its constants
    set conservatively, tuned alongside the rest of `SUS_*`); the **flank call**
    (a locked chaser pulls at most one nearby patrol to a flank point, same
    LOS/suspicion rules, normal search timer, never soft omniscience);
    **object-state investigation** (a left-on noisemaker, an opened door: pause
    at it, mark the room uneasy).
  - **Content passes [Fable].** Fuller local **day-loops** on the JOBS
    `stations` plumbing (Pell to the field edge he doesn't look at, Calder to
    her gate, Royce circling his truck; door-anchor honesty rules apply);
    **disposition framing** read off existing save flags (mood, never a meter).

- ### INTERIORS PROGRAM — ensembles, floor plans, the prop fifteen **[Opus + Fable]**

  **Maintainer directive: "props seem scattered without any purpose... treat
  what you have as multiple props touching each other and make those into ONE
  new object with more handcrafted detail."** The rooms read as prop soup; the
  fix is composed ensembles, not more placement.

  - **THE ENSEMBLE RULE.** Props that touch each other or a shared wall merge
    into ONE handcrafted multi-tile object (a `SOLID_PROPS` volume with a
    designed silhouette), authored for the projection, never re-scattered as
    separates. Design each from the FIXED CAMERA's four facings, E/W FIRST (the
    historically weakest angles).
  - **REAL FLOOR PLANS FIRST.** Before re-dressing a room, sketch it from a
    real reference plan (1990s Minnesota cabin / small hotel / farmhouse): work
    zones, walk lanes, furniture against walls, one focal wall using volume and
    negative space. Provenance stays king (SCENE-DRESSING PROCESS).
  - **The prop fifteen (reusable ensembles, build as a library):**
    - kitchen (wood stove + counter + stovepipe + hung pots)
    - hearth wall (fireplace + mantle + fire tools + log basket)
    - bearskin rug
    - trophy wall (mounted wolf + buck + fish as ONE)
    - bed corner (bed + nightstand + wall pegs + underfoot rug)
    - writing nook (desk + chair + lamp + papers)
    - dining set (table + benches + settings)
    - wash corner (washstand + mirror + towel rail)
    - gun rack wall
    - coat wall (pegs + coats + boots under)
    - pantry shelving (stocked and bare variants)
    - reading chair + side table + oil lamp
    - workbench wall (hung tools + vise)
    - woodpile + stove pairing
    - wardrobe with the robe made legible (Sable's closet: the tell reads the
      moment you round the partition, no squinting)

    Each through the render-first loop (preview sheet → approve → place).
  - **Fifteen INSIDE and fifteen OUTSIDE.** The set above is the INTERIOR
    library; a matching EXTERIOR set follows (porch ensemble, lean-to + stacked
    wood, clothesline, rain barrel + gutter, fence-and-gate runs, mailbox post,
    burn barrel, machine shed face, pump + trough, chicken wire pen,
    propane/fuel tank, junk pile, tarped equipment, porch chair + rifle,
    antler-over-door). Same rules. The exterior half now has eleven yards to
    serve, so it carries more weight than it did when the town was one map.
  - **USE ALL SIX SURFACES.** On top of, next to, underneath, hung from walls,
    standing on floors, dropped from ceilings/rooflines. An ensemble may span
    floor-to-ceiling (stovepipe up through the roof, hams hung from beams, a
    wall of pelts reaching the eave).
  - **ANIMATE WHERE IT EARNS IT.** Each ensemble asks: could a part move, and
    does the world state show through it (a TV that plays static only while the
    genset runs, a stovepipe that smokes when lit, a fan that turns)? Powered
    behavior rides the genset link (the light pillar). A still room with ONE
    moving thing is scarier than a busy one.
  - **EVERY ENSEMBLE SHIPS ITS WEAR LAYER, WORLD-SPACE.** The object's years
    (rust, soot, scratches), its stains on the surfaces around it (the floor
    wears where feet stood), and at least one piece of honest mess — with FEW,
    BIG, DISTINGUISHABLE items, never same-weight speckle. Every mark is
    projected geometry in its true plane; screen-aligned marks are error
    class 7.
  - **Rug rework rides along:** the rug must read from every facing (its
    pattern/fringe currently only reads from N).
  - **Blank building faces:** E/W exterior shells (the backwoods cabin is a
    bare grey slab from the side) need relief — windows, timber framing, a
    lean-to, stacked wood — via the exterior library, not one-offs. Every yard
    scene puts a house face in the middle of the shot, so this is now the most
    visible gap in the game.
  - **Rollout.** The lodge common room (pilot), the shop's stockroom receiving
    corner, and the sheriff's office quad are landed (`CHANGELOG.md`). Next, in
    order: the church vestry, Toby's house, and Hettie's shop floor.

- ### The King becomes the STORM — apex redesign, IN PROGRESS **[Fable + Opus]**

  The King is not one body, He is the **STORM**: His attention flooding the flat
  plane so every dark space erupts amalgam-cuts. The flood, the apex (the Mask
  that wears a unit), its face, its screech and its reach are all shipped
  (`CHANGELOG.md`, "The shadows program"). The design rulings that are still
  live fences:
  - **No apex body.** The bearer is just another amalgam; nothing marks it but
    the Mask and its size.
  - **The Mask is a PART** (the eighteenth), player-scale and a real 3D object
    that turns a full 360 — never a billboard. **One Mask storm-wide,
    MIGRATING**, and the hop is EARNED, not on a dwell timer.
  - **Its Mask is NOT the `pallid_mask` keystone.** There is one Mask object
    and it is on the altar; the storm's face is a **SLICE** of Him, the same
    cross-section as the drifting masks in fire. That is what keeps the
    impossible count at one (NARRATIVE §2/§6a; `tests/conventions.py` check 12).
  - **Light REPELS the storm, never burns it** (burning stays the un-stormed
    Watcher's privilege): a unit refuses any step that would put it in a pool
    or the beam, so standing in light makes them ring its edge. This was the
    written rule all along and the code had drifted from it; it is now what
    ships. The apex ignores light entirely. He is survived, never dispelled.
  - **The storm fills ALL dark, corn included.** Light is the last refuge.
  - The idle horizon King is **CUT**; the storm is the full-power apex at the
    source, and its overwhelm is the point.
  - **The storm CUTS wear the rift's gold rim** (approved 2026-07): an
    ANCHORED gold-rimmed cut, not a billboard, with the off-angle falloff
    FLOORED so a cut thins yet never fully vanishes. Gold rim + motes at
    aperture size; the rift stays the only full doorway. The fade-until-gone
    dissolve is reserved for the CATCH beat, never routine crossing.

  Build order:
  - **THE FLOOD IS INVISIBLE, AND ON THE SAFE PATH IT CANNOT REACH YOU.**
    Measured on the live system with `tools/capture_storm.py`, not judged off a
    still. In `farm_yard` at full evidence: 18 units up, all 18 on screen, 11
    inside `STORM_SEE_RANGE`, and **one or two legible in the frame**. The bone
    outline is the only thing that makes a unit findable at all, and it is
    doing that job alone. Two separate problems live here:
    - **Reach.** In `store_row` the same run puts 13 units up with the nearest
      at 231px and exactly ONE inside the smear range. The cause is geometry,
      not the units: the safe path is **69% lit** (the lamp chain floods the
      whole carriageway by design, `DESIGN.md` §14), and a unit refuses any
      step into light, so the flood physically cannot come onto a street. Every
      street in the game is storm-proof. That may be the right answer — the
      path is the safe layer — but it is currently an accident of two correct
      rules meeting, and it means the town's whole connective tissue is a
      no-storm zone. Decide it on purpose.
    - **Absence.** `lost_corn` builds **zero** units, because the crop circle's
      corn ring is solid and the `STORM_SPAWN_NEAR..FAR` band has nowhere to
      open. The lost spaces are the darkest scenes in the game and the storm
      never arrives in them, which contradicts "the storm fills ALL dark".
      Small enclosed rooms are the same shape of failure (`well_passage` and
      `lodge_yard` each build a single unit).
    **Reach is RULED and closed** (maintainer, 2026-07): the road is
    storm-proof and the light is what does it, deliberately (`DESIGN.md` §1).
    **Legibility is PARTLY fixed** -- `AMALGAM_EDGE_W` went to 2px, which took
    a `farm_yard` frame from one findable unit to five or six. Two things were
    tried and MEASURED not to be the lever, so do not re-try them: the
    blind-spot fog floor (units in the sight cone are already at alpha 255) and
    the room gloom (forcing it to 0 moved the median peak delta 14.0 -> 15.2).
    A near-black body has no value to spend; only the EDGE can carry it.
    **THE LANTERN EYE landed** and is the answer to "the body has nothing in
    it": a guaranteed eyeball part throwing decorative light onto the
    creature's own flesh (`CHANGELOG.md`, `DESIGN.md` §1). Interior value now
    exists, so the outline is no longer carrying legibility alone.
    **Still open, and this is the honest state: the units are STILL not
    legible enough.** The eye works in isolation (lamp-off vs lamp-on on one
    creature measures a peak delta of 96) but cropped 1:1 from a real dark
    scene at 130px it reads as a faint dot, not a lit body. The mechanism is
    right and the SCALE is wrong. Things worth trying, in order: draw the
    creature LARGER at game scale (they are small enough that no amount of
    interior detail survives); raise `AMALGAM_LAMP_*` further and widen
    `EYE_LAMP_R` so the lit area is a body rather than a bulb; and once the
    interior really carries, drop `AMALGAM_EDGE_W` back to 1, which would also
    settle the preview sheet's fair complaint that 2px reads as line-art.
    **Do not trust `--measure` alone for this** -- its peak deltas sit at 14-15
    whatever you change, because the diff is dominated by the occluder fade a
    visible actor triggers rather than by the creature. Crop 1:1 and look.
    **`lost_corn` is FIXED** and the cause was not what it looked like: the
    lost spaces were absent from `WATCHER_OPEN_SCENES`, so the gaze could never
    open there at all while `_storm_active()` reported True. All three fields
    now storm (`lost_corn` reaches the cap of 22). `abandoned_farmhouse` had
    the same gap. Guarded by `tests/conventions.py` check 15.
    **`AMALGAM_EDGE_W` back to 1: tried, UNRESOLVED, left at 2.** Two scene
    A/Bs both landed with the units outside the beam, so neither frame showed
    a creature at either width and the comparison proved nothing. 2px stays
    because it is the safer read; settle it with a frame that has units close
    and lit, or by scripting the player to face them.
  - **THE AMALGAM'S CATCH ANIMATION.** The apex's death card is a wordless
    placeholder fade, hooked up and timed already (`_death_kind == "apex"`,
    3.8s, `render_mixin._draw_death_screen`), so this is purely the drawing:
    built from the amalgam grammar rather than the Unfolding's — the parts, the
    gold cuts, the Mask coming in. Wordless by design, so there is no label and
    nothing owed to `DIALOGUE.md`. Land it through a VISION look pass.
  - **Retire THE UNFOLDING.** Rewire the roaming King's own card and the
    Carcosa cutscene (flow-guarded) onto the storm. The apex no longer touches
    that art at all, so what remains is the King path itself.
  - **The last canon reconciliation.** NARRATIVE §8 describes the walking King
    as the thing that reaches you because that is what ships until the
    Unfolding retires; "one pursuit, two shapes" collapses back to one shape
    when it does.

  **Movement vocabulary to choose from when the catch lands** (none picked
  yet): it uses APERTURES instead of pathing (sink and rise past a wall rather
  than walk around it — the migration machinery already exists); STILLNESS
  instead of idling (perfectly motionless, facing you, at the edge of the
  light); speed tied to whether you are LOOKING at it (inverts the family's own
  gaze rule, so the player's trained instinct becomes a cost); arriving ALREADY
  THERE rather than walking in.

  **Fences:** Mask stays player-scale + a real 3D object; one bearer at a time;
  the flood concentrates on His last *sense* of you, not your true position
  (luck-not-omniscience); the impossible count stays at one.

- ### The lost spaces — the dark manipulation layer **[Opus + Fable]**

  The restructure is committed and shipped: three layers (interior → yard →
  safe path ↔ lost spaces), eleven yards on five streets, the three biome
  fields reachable through the lodge yard's treeline mouth, and no town map at
  all (`DESIGN.md` §13/§14/§15; `CHANGELOG.md`). What is open is the half that
  makes the restructure pay off — the manipulation that is supposed to be FELT
  moment to moment rather than told.

  Build order:
  - **Asymmetric return.** The way back is not the way you came. Today the
    hunted lantern climbs you out where you fell (`Game._lost_return`); the
    field should be able to put you out somewhere else on the same street
    network, so a lost space is a thing you come out of changed in position,
    not a detour.
  - **Breathe with threat.** The space stretches as the meter fills: the exit
    light's 6-20 tile band, the reshuffle rate, and the field's feature density
    all read the visibility meter, so being hunted makes the walk longer.
  - **More mouths.** One mouth on one scene is a vertical slice. Open the
    remaining dark, non-wrapping edges that earn it — the street verges already
    derive WHICH field they lead to (`_VERGE_LOST`), so this is `set_lost_edge`
    calls plus a look pass per edge.
  - **Per-chunk generation + a silent re-origin** for a truly endless walk
    (today: a large finite bound + spawn-at-centre), with landmark/exit
    generation moving per-chunk with it.
  - **The ev-warp variants:** the field swaps for a longer / warped /
    more-hostile version with evidence, plus richer linear features (fences,
    ruined buildings you cannot enter).
  - **Interiors for the yard buildings that have none.** Mrs. Calder, Royce and
    Garrick got small one-room interiors with the yard layer; the other
    households have their exteriors only. Give the ones a scene actually sends
    you into a room, through the interiors library.

  **Fences:** the safe path is never tricked; the lost space is always escapable
  (the exit light stays in the 6-20 band); a THREAT never blinks out via the
  observer trick (only geometry lies); keep the impossible count at one.

- ### Remake the town sign **[Opus]**

  The old-timey painted BRIMLEY board (WELCOME TO / NORTHERNMOST CORN / EST.
  1894) needs a redesign, and the retirement changed what it is: `town_sign` is
  now the game's **wayfinding system**, not one roadside prop. It ships as the
  arrival board on `arrival_road`, the two directional boards flanking the
  lodge crossing (BRIMLEY / LODGE), the lodge yard's west-mouth board, and the
  square's board on `store_row`. The remake has to serve a two-word directional
  board and a full welcome board with the same construction.

  It is also the game's **last font-rendered world lettering**
  (`rendering/props.py`, 3 of the 3 uses in `FONT_BUDGET`), so the remake
  retires that: spell it in the procedural neon-tube alphabet's cousin, a
  **painted**-letter stroke set (`_GLYPH` + `_draw_neon_word` in
  `rendering/props.py` are the worked reference; a painted board wants flat
  opaque strokes with wear, not tube glow). Drop the file's `FONT_BUDGET` entry
  to 0 when it lands and the guard locks it shut. Verify with
  `tools/capture_facings.py` at the angles a walker actually gets, not just N.
  **Reconcile in the same pass:** the SPREAD ending's drive-out sign
  (`rendering/spread_drive.py _sign_back`) shares the board's shape, so both
  move together and cannot disagree.

- ### Cut the calendars **[Opus + Fable]**

  **Maintainer ruling: remove the calendars from the game**, including the beat
  built entirely on one (Old Pell's) — explicitly acknowledged and accepted.
  - **The prop.** The `calendar` decoration (`entities/deco_horror.py
    _draw_calendar`, placed in `scenes/yards.py` on Old Pell's own siding and
    read in the Vane tableau's dressing). Removing it clears that file's 3
    `FONT_BUDGET` entries (the month/day label), so the guard tightens for free.
  - **The stopped-January fact moves to the news rack.** NARRATIVE §3's
    timeline and the invariant "every calendar in town stops at Jan 15" are
    load-bearing and currently *shown* by the calendars; the frozen news rack
    on the square already dates itself Jan 15 and carries it alone once they
    are gone. Reword the invariant to name the rack, and reconcile NARRATIVE +
    DIALOGUE in the same commit.
  - **Pell's thread needs a new carrier** (`scenes/dialogue.py`,
    `scenes/yards.py`): the `beat_pell_coal` stoop line ("I've got the calendar
    where I want it. Stopped."), the `beat_pell_marked` ripple after the
    newspaper, and the `paper_pell` note. His WANT (`DESIGN.md` §8: legacy, the
    harvest endures) survives fine; what needs reinventing is the **object that
    shows a man refusing to mark time**. Pick it in this pass — it is his only
    mechanical beat, so it does not get to become a gap.
  - **Guards:** `tests/flow.py` asserts several Pell/paper beats; update them
    in the same commit.

---

## Deferred / north star

- ### The liminal-composition pass **[Fable]**

  A standing direction for per-scene level-design polish: composed emptiness,
  long sightlines, uncanny repetition. Inherently iterative, and it only
  becomes work when a scene and a composition are named — the outdoor-dread
  ticket is this pass aimed at open ground and has both, so it is the live
  instance.

- ### Parked — terrain megabuilds

  The general-purpose ground floor-roll warp and the terrain design directions
  that depend on it (sunken-lane cover, King crest-reveal, terrain-herding).
  Their payoff fights their cost at this camera; the reasoning lives in
  `CHANGELOG.md`, "Brimley geography". They come back only with a set-piece
  that demands them. The DORMANT heightfield prototype and the SHIPPED carved
  river channel STAY — both are harmless and byte-identical unopted. The `turf`
  hill in the outdoor-dread ticket is the cheap substitute that covers most of
  what the warp was for.

- ### Endings redraw with the close-up techniques **[Opus + Fable]**

  The ending presentations (the King-catch furnace, SEAL's lines-on-black
  tableau, SPREAD's drive-out, BREAK's mask-yank + blast) predate the close-up
  tableau art pass. The endings themselves are approved, flow-guarded
  set-pieces and their lines + palettes are canon, so this is a
  re-presentation question, not a gap. If it is taken up: bespoke portrait
  register, reactive state, and Mara's frame's corrected vignette ramp (the
  older shared vignette loop darkens the CENTER). Each ending lands only
  through a VISION look pass.

---

## Standing fences (guardrails, not tickets)

- **The lure chain is NEVER stated diegetically.** King → Mara → Walter → PI
  is felt, not said. Do NOT build on any of it. King/Watcher moments read as
  **luck, not omniscience** (powerful, not infallible).
- **The corn is mundane, never the door's doing.** Keep the impossible count
  at **one**: the single unexplained door, everything else ordinary
  cause-and-effect downstream of it.
- **Sable's misdirection is never resolved in text.** He points suspicion at
  the cold old families; Hettie says the warm easy ones went soonest. They
  contradict each other, Sable is the wrong one, and **that is on purpose and
  for the player to notice.** Do NOT build a beat where the PI puts one man's
  line to the other, and do NOT file a note that draws the conclusion.
- **No dashes in player-facing text** (HARD RULE; flow-guarded).
- **There is no town map.** No scene holds a cross-town coordinate; a
  remembered "brimley tile" is a red flag twice over. Public fixtures live
  where the yard layer put them (`CLAUDE.md`, "THERE IS NO TOWN MAP").
- **Complexity hotspots (awareness only, not a ticket).** The largest function
  bodies (`tests/flow.py main`, `scenes/yards.build_yard_scene`,
  `systems/render_mixin.draw_world`, `rendering/sprites_npc.draw_npc_sprite`,
  `rendering/king_unfold.draw_king_unfold`) match the project's deliberate
  "one cohesive beat per function" style and sit behind the test gate. Listed
  so growth stays a choice, not an accident.

---

## Optional polish (no canon/lore change; do as time allows)

- **[Fable + Opus]** **Rev. Asa Crane murder reveal + sprite** — the
  discovery location + staging landed (`CHANGELOG.md`). Still open: the
  **bespoke sprite** (the current corpse is a placeholder medieval knight,
  `_draw_body`; replace with a gutted-preacher draw — dark palette, white
  collar, cross in the mess), and staging the approach (wrongness before
  sight, long sightline). Art only; lore unchanged.
- **[Opus]** **Held-weapon offset per camera yaw** — `draw_axe_held` reads at
  rest; eyeball the equipped-weapon offset at every camera yaw so it never
  floats off the hand. Verify with a tilt capture across yaws.
- **[Opus]** **Higher-contrast see-through doors** — opt in the doors where
  the sight-gated aperture effect reads strongest: a lit room off a dark
  hall, a front door onto its yard. Draw/opt-in only; no new tech.
- **[Opus]** **Permanently-visible King through an OPEN fold** — currently he
  looms through the rift only while it forms, then steps through
  (intentional). A persistent silhouette on the far side of an already-open
  fold is not built; it comes back only if the direction changes.
- **[Opus]** **Mine retrofit tail cleanups** (none player-visible) — cache the
  `_tilt_rack_box` extrusion per (tile, yaw-bucket) like the wall cards
  (`well_passage` re-projects ~280 points/frame live); fold `_RACK_CHARS` into
  the shared wall-scan char-set plumbing instead of a third parallel set; the
  cave `door_style` key list in `scenes/__init__.py` duplicates the
  `UNDERGROUND_SCENES` gating idea, so derive from one source; `husk_bundle` +
  `pillar` are registered kinds with no placements (keep as reusable art or
  cut).
- **[Opus]** **Grove mine-hill finish level-up** — the mouth is a green turf
  HILL with a stone adit; its grass-dome ROOF got a full detail pass, but the
  stone side/cut faces + the adit mouth are plainer by comparison. Bring the
  stone up to the roof's finish (strata, cracks, a little scree/moss at the
  base) and make the adit read a touch more as the focal point, so the whole
  object sits at one level of craft. `hill_cap` (`rendering/props.py`) + the
  `turf` walls + `_grove_interact` dressing (`scenes/hidden_folds.py`).
- **[Opus]** **Louvered belfry openings** — the bell tower's belfry uses the
  glazed cottage-window char (`'i'`), which renders as glass everywhere. A
  belfry wants louvered slats, which needs its own window style or a
  wall-deco louver over the openings (a small per-scene window-style
  mechanism).

---

## Voice / polish (player-facing text — still open)

- Descent interior voice wobbles POV (first-person notes vs. second-person
  on-screen beats, `systems/game.py`) — confirm this is the deliberate
  self-vs-lure split `DIALOGUE.md` documents (`chalk_surface`/`descent_dig`/
  `chalk_deep` first-person vs. `descent_leave`/`descent_mask`
  second-person) and not accidental drift elsewhere.
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
  simultaneous Hetties (door + counter); duplicate candle decoration in
  Toby's house.
- Missing canon clincher: `NARRATIVE.md` §4's ledger entry promises "your own
  name, signed in tonight, already among them" — the cellar text only
  gestures at it and the desk sign-in is optional; one clause conditioned on
  `register_signed` closes the loop.

---

## Process

- ### Doc consolidation — remainder **[Fable]**

  Phase 1 landed (the threat section moved to DESIGN §1; `CHANGELOG.md`,
  "Documentation process"). Still open: CLAUDE.md's Layout section carries a
  tableau mega-paragraph and several system narrations (Casebook, dialogue
  channels, stealth asides) that duplicate or should live in DESIGN/DIALOGUE;
  move each to its one home and leave a code-map pointer, one section per pass,
  keeping the every-turn read shrinking.

- ### Cross-model review gate **[Fable]**

  After an **[Opus]** ticket lands, run a **Fable** review pass before it
  merges. This is NOT a code-correctness re-audit (use `/code-review` or a
  fresh Opus context for that, since a model self-reviewing its own diff is the
  weakest check). Fable judges what it is strongest at for THIS game: does the
  change land the feeling and hold canon. For a given diff + the running build
  it answers:
  - Does it read as dread, or as a mechanic showing through? (atmosphere,
    pacing, the tell)
  - Does any player-facing string break the no-dashes rule or the
    `NARRATIVE.md` voice?
  - Does it contradict a locked canon fact (`NARRATIVE.md`)?
  - What is the cheapest change that would make it land harder?

  Output is a short verdict + ranked notes, not a rewrite. The value is a
  SECOND, independent model looking at the work, so the direction can flip: if
  Fable is doing the implementing, an Opus pass reviews it the same way.
