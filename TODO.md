# THRESHOLD — TODO

> A live to-do list of work that is **genuinely still open**. This is now the
> **single** canon-alignment + build tracker: the former `GAME_CHANGES.md` was
> folded in here (2026-07) and deleted, so its open items live below tagged
> `(was GAME_CHANGES §N)` for provenance. `NARRATIVE.md` stays the canon
> source of truth. Built from a verification sweep of every TODO source
> (`NARRATIVE.md` §8) and pruned
> against the 2026-07 build sweep. Each candidate was checked against the
> actual code; **anything already implemented is deleted from this list
> outright** (no "done" archive).
> Cross-check against `NARRATIVE.md` before writing prose, run the full
> gate (`python tests/run_all.py`) before commit, and add a
> `tests/flow.py` guard when a new note locks a canon fact.

---

> **Model tags** (2026-07): each ticket is marked **[Opus]** (systems
> reasoning, geometry, rendering, correctness) or **[Fable]** (prose, voice,
> atmosphere). A few straddle and say so. Routing hint, not a rule.

## Open work

Grouped by readiness, not source-doc number. **Buildable now** items are
scoped and unblocked; **Blocked on a human** items are built but need
playtesting to finish; **Deferred** items are parked on purpose. Roughly
priority order within each group.

## Buildable now

### 1. **[Fable]** Investigation dialogue verb — the ask-questions layer  *(VERB LANDED 2026-07; principals + chorus all converted — still open: `_REVISIT_NUDGES` for Hettie/Toby/Crane as their case hooks land)*

You play a PI, but the only social verb is press-E-to-advance scripted lines:
every NPC conversation is a linear counter (`old_count`, `kid_count` ...). The
choice engine already exists and works (`ui/dialog.py show_choice`) but is used
in exactly ONE gameplay spot (the Sign Chamber altar fork, `scenes/well.py`
~L890). Build an ask-about-topics layer (the girl / the well / the strangers /
the preacher) with answers gated on evidence found + who is being asked. Makes
the core fantasy active for the first time (NARRATIVE §4: reading the town IS
the investigation). Content + design, not engine work. **Highest value-to-risk
item on the list: engine exists, canon is settled, payoff is the core fantasy.**

- **VERB BUILT + PILOTED on Mr. Sable (2026-07), organic redesign.** The menu
  options ARE the PI's own first-person spoken lines (not abstract "The X"
  topics you infer), and picking one plays a real EXCHANGE: the PI speaks, the
  NPC answers, each floating over their own head (`ui/float_speech`) while the
  world keeps running; an exchange can branch on an inline choice (show him the
  photo, or don't) with a side effect. Engine: `ui/conversation.Conversation`
  (`open_conversation`) is a small state machine wired entirely through the
  float `on_complete` chain + `dialog.show_choice` callbacks (Game never ticks
  it). A conversation is plain data: a one-time `greet`, then `exchanges` of
  `{key, q, avail, once, beats}`; a beat is `("npc"/"pi", text)` or
  `("ask", prompt, [(label, [beats], on_pick)])`. **The case GROWS the talk:**
  questions gated by `avail` open as evidence is found (Sable's register + her-
  state questions unlock on `the_ledger` / `maras_journal`), and the discovery
  itself NUDGES the PI back, appending his interior line onto the find's
  narration and filing a case NOTE (`_REVISIT_NUDGES` / `_collect_revisit`,
  hooked into `_evidence`; never inflates the evidence count). Wired on Sable
  after the envelope handoff preempt. Guarded by `tests/flow.py` §17c (17
  checks) + the naming guard.

- **EXPANDED to all four remaining principals (2026-07).** Toby / Hettie /
  Vane / Crane each carry their own `*_CONVO` + `open_conversation`, with
  every story-critical one-shot (Toby's witness account + playscript + school
  warning, Hettie's preacher reaction + Mara memory + paper trade, Vane's
  murder-he-can't-report) still VOLUNTEERING itself ahead of the menu. Flow
  polish shipped with it: the **talk-hold** (`scenes/base.py Scene.update` —
  the conversation partner stands and faces the player instead of walking
  their worker route mid-exchange; pursuit exempt), the **earshot guard**
  (`ui/conversation.py _partner_here` — the menu only reopens while both
  parties are still at the talk; walking off ends it quietly), and
  `game._convo` is cleared on scene load / run reset. `_fold_mentioned` grew
  `reflect=False` so a convo exchange (Vane's car answer) can file the fold
  note without hijacking the float's `on_complete` chain — the exchange
  carries the PI's reflection as its own closing beat. New `_REVISIT_NUDGES`:
  `the_preacher` points the PI back at Vane. Guarded by `tests/flow.py` §17d.
  **Still open:** `_REVISIT_NUDGES` entries for Hettie/Toby/Crane as their
  case hooks land.

- ~~**Two guaranteed options on EVERY townsperson (the case's front door).**~~
  **DONE (2026-07), chorus included:** every principal's menu leads with
  the shared pair (`_opener_exchanges`: (1) the PI **introducing himself as a
  private investigator**, (2) **showing Mara's photograph**), intro first,
  photo second, answers per-NPC; greets no longer assume the case is known —
  the PI **initiates** (news does not spread). **The Brimley chorus (Old
  Pell, Mrs. Calder, Royce, Garrick) converted** to `*_CONVO` +
  `chorus_dialogue` (scenes/dialogue.py): the shared pair with short
  per-NPC answers, one or two signature questions each (Pell's calendar,
  Calder's plate, Royce's roads + his you-got-IN counter-ask, Garrick's
  road warning), the TODO #10 reactive beats still volunteering ahead of
  the menu, and the **fold note moved off the old any-talk trigger onto
  the exchanges that carry the account** (Royce/Garrick `on_ask`,
  `reflect=False`, earned by asking). Guarded by `tests/flow.py` §17e +
  the reworked §16c. **The unnamed "newcomer woman" NPC is CUT from the
  project entirely (maintainer call, 2026-07)** — an unexplained
  welcomer on the farmhouse path read as noise, not dread; her
  `ROT_CONVERT` stage-1 entry went with her (flow-guarded: she never
  spawns).

- **The choice box is SMALL — menu labels are authored short (2026-07).**
  An exchange carries an optional `label` (≤ ~44 chars, flow-guarded): the
  menu shows the label, picking it still floats the full `q` as the PI's
  spoken line. The option panel also sizes to its longest label and sits
  ABOVE the dialog band (`ui/dialog.py _draw_choices`) so it never lies over
  the prompt. And follow-up questions are **EARNED, not ambient**: Hettie's
  "who is they" and Crane's flock question wait on the intro being asked
  (`convo_<id>_intro_asked`); the way-out questions (Hettie, Toby) wait on a
  local having told the PI about the looping roads (`voice_fold_heard`).

- ~~**Pilot beat — the Crane choice**~~ **DONE (2026-07), upgraded to an
  inline `ask` fork in CRANE_CONVO's flock exchange:** press him (he takes
  the naming where they can hear it — `preacher_doomed` latches, evidence #4
  proceeds, and the PI's culpability lands as a NOTE `crane_provoked`) vs
  hold him back (the fire is only banked — the question stays open to press
  later; he is never savable-by-conversion, §1b — the player just decides
  whether HE is the one who points him). The provoke branch feeds the murder
  reveal below. NOTE the behavior change: his doom is no longer an automatic
  visit-2 counter. **The stall-breaker (R-gate finding):** only three beats
  are surface-reachable (journal, Ledger, preacher) and the descent needs
  three — so when the SECOND canonical beat lands with Crane met and still
  un-provoked, the PI's interior voice points him back at the pulpit
  (`_the_third_thread`, a NOTE, flow-guarded): the forced return reads as
  the investigation forcing his hand. Fixed alongside it: a silently-filed
  beat (`show=False`, the journal) now still lands its revisit nudges.

### 2. **[Fable + Opus]** The newspaper choice — pilot for the favor economy  *(planned with the user 2026-07; the broader favor economy stays direction-stage)*

The PI starts with the **April 14, 1994 paper** (existing item; today only
Hettie's one-shot cartridge trade). Make it a **choose-the-recipient gift**: a
town cut off since January, starved for word of the outside, one copy — and who
you give it to yields **different, incommensurable** payoffs, and the town
**feels** the allocation. This is the concrete **pilot for the favor economy**
(the action-choice half of the choices pillar, twin to #1's dialogue verb; the
full economy table is still to be drafted).

- **Recipients + payoffs (draft):** Hettie → cartridges (survival); Royce → his
  hoarded flashlight batteries + the one road he got furthest on (escape-hope;
  ties #12); Old Pell → he marks his calendar again, **no item** (mercy); Toby →
  the funny pages (mercy).
- **Sable → the null / eerie option (the tell).** Give the paper to the
  trap-keeper (the most-attuned local) and it lands nowhere: he takes it
  graciously and it means **nothing** — no reward, no thanks that reads as
  real, a quiet non-reaction that the outside no longer exists for him. The
  anti-reward that characterizes what Sable *is* (compulsion, not hospitality;
  NARRATIVE §4). Outcome is a `notes` beat / a chill, never an item.
- **Vane is a recipient too — and his is a TRAP, not a gift.** To Vane the paper
  is his **break lever, not a comfort**: Kurt Cobain (his favorite musician)
  dead on the front page reads, to a man who wants it all to *end*, as
  *permission*, not hope — the outside is dying the same death, one day north,
  and its brightest walked out of a room he could have left any time. Giving
  Vane the paper adds **+2 despair** (walks him to the lip of the hollow turn;
  the give-beat telegraphs it as mood, no number shown). **This is the one
  recipient whose allocation carries a TRACKED consequence** (the despair
  ledger, ticket #2a) — the deliberate exception to the "mood, not a meter"
  fence below, named here so it is not read as drift. One copy: giving it to
  Vane means Hettie/Royce/Pell/Sable/Toby go without.
- **What's on the page (real April '94):** Kurt Cobain's death is the thematic
  centerpiece (the outside world's own despair, the same wound that took
  Brimley), plus Rwanda and the Bosnia/Goražde NATO strikes. The paper is **not
  a comfort**.
- **Requests variant (same engine):** a local asks for a thing → **fulfill /
  refuse / SUBVERT** (use it another way) → the town feels it.
- **Fences (the choices rules):** rewards are **incommensurable** (no dominant
  pick); **never evidence**; the ripple is **mood, not a meter** (who greets you
  warm vs curt, whose hope you fed or killed); it **never gates an ending**
  (nothing stops the PI but himself); **existing verbs only** (give via E /
  dialog).

### 2a. **[Fable + Opus]** Sheriff Vane — the despair/hope arc + player-driven hollow turn  *(planned with the user 2026-07; couples #1's ask-verb + #2's newspaper; deepens a thin character)*

Rework Vane from a linear counter into a real arc (the goal is DEPTH — he had
little going on). Lore is settled in NARRATIVE §4 (his row) + §4 (the hollow
turn, rewritten off world rot-gating). Two halves:

- **Ask-verb conversion (rides #1).** Give Vane **multiple dialogue options**
  (his own `*_CONVO`): the two guaranteed openers (introduce-as-PI + Mara's
  photo, #1), plus his **investigation thread** — the nameless blind cultist,
  the *how*, the emptied school/barn/lodge — **gated on TRUST**. Trust is earned
  only by the player **sharing real discoveries** with him (he is
  another-outsider-wary by default; §2).
- **Player-driven hollow turn (replaces §4's world rot-stage-3 gate).** A
  hidden **despair/hope ledger** decides his fate — the player never sees a
  number, only his mood (the "mood, not a meter" fence is honored: it gates a
  *character's fate*, not an ending). Two triggers:
  - **The ledger** (fluid, latches — once hollow, no return). Starter constants,
    all playtest-tunable (a `VANE_*` config block, same bucket as the stealth
    `SUS_*` tuning): `VANE_HOLLOW_AT = 3` (net despair that latches the hollow
    turn); hope act **−1**, despair act **+1**; `VANE_PAPER_DESPAIR = 2` (the
    newspaper, #2 — walks him to the edge, not an instant kill from neutral);
    `VANE_DESPAIR_FLOOR = -2` (hope can bank down to −2, so a careful player can
    eat the paper and just survive; two ordinary bad beats can't undo real
    rapport).
  - **The neglect override** (hard, beats the ledger). Reach **3 evidence** with
    fewer than `VANE_MIN_INFORMED = 1` discoveries shared → he hollows
    regardless. Closes the "save him by pure inaction" loophole and keeps the
    rough old timing (~evidence 3), now *earned by neglect* instead of automatic.
- **The elegant coupling:** trust-by-sharing IS the hope currency — every real
  lead brought to Vane both opens his help and buys down despair; the newspaper
  (#2) is its exact inverse. So the same act builds the rapport that makes his
  fall hurt, and holds him back from it. Encounter mechanics unchanged (stands →
  force-chase → **TAKEN INTO CUSTODY**; escape out his door; best ammo cache).
  Add `tests/flow.py` guards when it lands (both trigger paths + the latch + the
  neglect gate).

### 3. **[Opus]** Ground heightfield — blind-spot hills  *(CAMERA.md Phase 6; PROTOTYPE landed 2026-07 — floor-roll rewrite + live authoring deferred)*

**PROTOTYPE DONE (behind a preview, dormant).** Built: `Scene.set_ground` /
`Scene.ground_z` (bilinear, 0.0 unopted → dead-flat + pitch-0 byte-identical),
the `_flood`-style `rendering/heightfield.build_heightfield`, the CREST
sight-occlusion (an optional `ground=` term in `sight.los_clear` /
`visible_factor` + `Scene.clear_sight_line`, `SIGHT_EYE_H`) feeding BOTH the
draw gate and the cult AI, `draw_ground_mesh` (a projected floor mesh over the
flat raster, tilt-only) + actor lift by `ground_z`. Movement stays 2D; height is
a passive READ (AI ignores it in v1). Preview `tools/preview_heightfield.py`;
guard `tests/render_smoke.py` [4/4]. **Key finding:** the tilt floor is ONE
affine warp (`_tilt_warp`), not per-tile — so no shipping scene opts in yet, and
two pieces are **deferred**: (a) rolling the whole floor RASTER (needs a
mesh/displaced warp replacing the global affine `_tilt_warp` + a perf pass on
the ~6000-tile bake), and (b) authoring a live Brimley hill + lifting every live
actor project site (safe/dormant until then). *(Original brief kept below.)*

The camera already carries a real height axis (`Camera.project(wx, wy, wz)`,
`z` rises by `sin(pitch)`); the *simulation* is flat XY. Add a per-scene
`ground_z(tx, ty)` sample, authored like the `_flood` water helper. It feeds
ONLY two places: the `wz` passed when projecting the floor + any standee/actor
on it (so ground rolls), and `blocks_sight` (a crest higher than the player's
eye occludes what's beyond it). Movement stays 2D; `player.z` is a passive READ
of the terrain under the feet, used for draw + sight only — no jump, no gravity,
no new collision. Lands directly on the shipped blind-spot vision (`sight.py`):
a hill you can't see over is the same dread primitive as a wall. **Constraints:**
strict no-op at pitch 0 (byte-identity gate, `tools/capture_world.py`), and
AI/pathing ignores height in v1 (cosmetic + sight-only). Prototype on one
Brimley scene behind a preview before wiring.

- **River spike DONE (2026-07):** `heightfield.carve_channel` cuts a sunken
  trough (banks from `build_heightfield`, bed below grade); `draw_ground_mesh`
  shades `~`/`@` bed tiles WET and the bank crest occludes the bed from the
  grade (the sight-pit the WADE routing wants). Preview
  `tools/preview_river_channel.py`; guard `tests/render_smoke.py` [4/4].

- **DECISION (2026-07): the carved channel is the shippable win; the general
  floor-roll + subsidence bowl are PARKED (see Deferred).** A design pass
  concluded the heightfield's payoff (outdoor sight-occlusion) fights its
  geometry at ~55° tilt: a crest tall enough to hide a standing figure over a
  SHORT outdoor sightline is a near-cliff, not a gentle hill, so "natural
  sloped boundary" and "occludes like a wall" are different terrain and a
  general rolling floor mostly reads wrong at this camera. And the tilt camera
  + blind-spot sight-gating already hide the ground geometry, so the illusion
  the roll was buying is largely already bought. The prototype stays DORMANT
  (paid for, byte-identical at pitch 0 — leave it), the carved channel ships (a
  trough is a controlled shape that dodges the cliff problem), and outdoor
  dread now routes through COMPOSITION (#4), not new terrain tech.

- **Deferred siblings (do NOT pull forward without a set-piece that demands
  them):** *3b.* Multi-floor buildings as same-building `cross_fold`s to a
  `lodge_upstairs`-style scene (no fade, stride preserved; the reveal is already
  free from `occlusion.py` + blind-spot gating) — compose shipped tools, do not
  build a continuous floor system. *3c.* Fully continuous traversable z (real
  ramps, actors at arbitrary heights, whole interior visible at once) —
  **deferred indefinitely**: big collision/AI/depth-sort/save lift, strains the
  "no roof over the play area" rule, and the payoff partly fights a game whose
  power is restricted sight.

### 4. **[Fable]** Outdoor dread — the composition pass  *(the outdoor-dread lever; replaces the parked Brimley reshape + terrain megabuilds)*

Open ground is the game's weakest dread zone (long sightlines, reads as an open
field). The 2026-07 design call PARKED the two big-tech answers to this (the
Brimley reshape and the ground floor-roll — see Deferred) because the tilt
camera + blind-spot sight-gating already carry the geometry illusion, and the
honest lever is COMPOSITION with tools already shipped, not new terrain tech.
Attack it on ONE named outdoor scene at a time (this is §10's liminal-
composition pass made concrete):
- **Corn + treeline are the outdoor walls.** Denser stands, winding corn lanes
  that break the long shot, a treeline that closes the rim. Draw + placement
  only; the standee billboards + the `_corn_runs` LOD already exist.
- **Fog / mist volume** between the player and the distance shortens the
  effective sightline directly (the job the subsidence bowl wanted, minus the
  geometry). Rides the skybox/void rim that is already ~80% there.
- **Landmark repetition + same-scene silent folds** (`cross_fold`, PORTALS.md,
  draw-only) give the "handed back / the town rearranges" uncanny with no sim
  change (`sight.py` blind-spot draw-gating already runs the sim while drawing
  only the cone).

**To turn into work:** name ONE scene (the Brimley approach road, or the
effigy grove) and the ONE composition it gets (this sightline broken by
this corn lane, this landmark passed twice in fog). Do NOT start against the
abstract goal. Keep the sim Euclidean-honest so stealth distance-falloff + NPC
nav stay true under any presentation lie. **Preserve (load-bearing) if the
scene is Brimley:** it stays ONE square scene (§11 merged village+mistlands on
purpose; do not split, do not reshape); the fold road + Royce/Garrick looping-
roads lines; the well as dread set-dressing (NOT the way down: the descent is
the cult's dug mine at the grove, reached by the rite); all exits/locals/cult stations;
in player-facing text call it a bounded fog-edge / void-ringed town, never
"island."

### 11. **[Fable]** Brimley = the northernmost corn town, est. 1894  *(was GAME_CHANGES §27)*

Brimley **STAYS** northern MN; the corn is town identity — stubborn 1894
founders made it the world's northernmost corn town and got good at it, a
century of pride. **GUARDRAIL:** the corn is a **mundane human feat** (hardy
short-season stock, a river-valley microclimate, skill), **never the door's
doing** — else a second impossible thing AND it breaks the ~1993 door timeline.
Keep the impossible count at one (§1b). Theme: founding hubris rhymes with
crossing the threshold; the dead, uncut April corn reads as their pride rotting.
Surfacing (mundane Americana that curdles): a weathered town sign ("BRIMLEY,
NORTHERNMOST CORN IN THE WORLD, EST. 1894"), a proud local line, county-fair
ribbons (no dashes). Keep the §1 April dead-corn note. `NARRATIVE.md` §1 setting
note 2 gets the identity + guardrail.

### 12. **[Fable + Opus]** Royce the trucker + the rusting semi  *(was GAME_CHANGES §28)*

Promote Royce to the man who drove **Brimley's supply run** — the severed
supply line made a person (Hettie's shelves are bare because *his* deliveries
stopped). Fable: a small dialogue nudge (he ran the route, goods in and out).
Opus: place his **picked-clean semi rusting at the town edge** (the town ate
its own last shipment; optional light scavenge, **never evidence**). Reconcile
with his worker job-loop (pacing the road) + his stage-3 convert.

### 13. **[Fable]** PI theory ladder — the notebook thinks  *(was GAME_CHANGES §20)*

An active "working theory" line in the case notebook that **REVISES** as
evidence lands (rational → strained → the one he refuses to write), plus terse
FACT / SOURCE / QUESTION entries. Never evidence, never a waypoint. Shows what
he forces himself to accept and how impossible this all is.

### 14. **[Opus]** The Works as a MINE — side-dug rooms, not hallways  *(was GAME_CHANGES §21)*

Make the Works read as a mining effort: timbered side-chambers dug off the
halls (some finished, some half-dug, the deepest hand-clawed), spoil heaps,
cart ruts, a degradation arc ending at the Deepest Face. A few pockets carry
loot / testimony placement; most is just labor made visible.

- **The FICTION half landed (2026-07, the mine retrofit + killer-cult
  scrub; guarded by flow §19b).** Room identities and text now read as the
  dig over old workings: `the_cells` = the diggers' bunk cells (captivity
  fiction cut), `the_ossuary` = the Old Stores (the bone vault is purged,
  `bone_rack` deleted from the furniture registry), every underground
  bloodstain/gore decal removed (the willing bled nobody), the Sorting
  Hall's "faces of the vanished" flyer wall cut, HUD display names cover
  the whole underground (the Deepest Face, not the cut Deep Stair).
- **The DRESSING half landed too (2026-07 art pass).** New procedural
  kinds, each registered in exactly one tilt set: `spoil_heap` /
  `shoring_frame` / `ore_cart` (SOLID_PROPS), `tally_marks` (wall deco),
  `mine_rail` (floor decal). Placed by mine logic: spoil + the barrow at
  the haul head (Shaft Floor), timber shoring at the gallery mouths and
  down the procession drift (the drift's stone pillars swapped to wood),
  the old workings' rail stubs under the candle line + the seized ore
  cart in a bay, inventory tallies over the Sorting Hall tables, and the
  degradation-arc climax at the Deepest Face (shift tallies by the face,
  unhauled spoil, downed hafts). The grain heap's baked-in "old blood"
  ring was recut to dark chaff (a killer-cult relic in the ART layer).
  The Sign Chamber stays deliberately bare: the one properly FINISHED
  room in the dig. What REMAINS here is the LEVEL-design half: timbered
  side-chambers dug off the halls (new geometry, some finished, some
  half-dug), doors under the cave-mouth adits.

### 15. **[Fable]** Deadpan narration editing pass  *(was GAME_CHANGES §22)*

Sweep every narrator / world caption to the settled voice: objective, deadpan,
a little curt (the talk-reaction register). Kill aphorism and poetry where it
crept in; keep the sensation-only cosmic rule (§1b). *(The liminal-beat pass —
was GAME_CHANGES §24 — folds into #4 and #7.)*

## Blocked on a human at the keys

These are BUILT and guarded; what remains cannot be settled from code
inspection and needs a person playing the game.

### 5. **[Opus]** Stealth rework — the TUNING loop

The mechanic AND the placement pass are built and guarded
(`tests/stealth.py` + flow §25; see `STEALTH_REWORK.md` for the design
and its status note). What remains only proves out against a human
player: the suspicion fill curve (`SUS_FILL_RATE`), the concealment
factors, the sweep budget, and the struggle window/presses. Also
deferred to this pass on purpose: the Pillar-2 **peek** verb (free look
under tilt already carries the information function) and an
exit-takes-a-beat vulnerability window on enclosed hides.

### 6. **[Opus]** Combat / difficulty — judgment calls (decide on purpose)

Not bugs; deliberate choices worth confirming rather than leaving by default:
the gun goes **stun-only at 3 evidence** with ~14 rounds total per run, so the
main combat verb is removed exactly when danger spikes (agency loss vs
intended dread). There are **no difficulty options**, so the visibility/Watcher
death-spiral hits newcomers and is trivial to experts. Items are gates, not
resources (armor slots return 0). Consider: transforming the stun into a
tactical window rather than a tax, an easy/hard toggle, or light resource
tension — only if it serves the horror, not despite it.

## Deferred / north star

### 7. **[Fable]** The liminal-composition pass  *(DESIGN.md §4/§10)*

Not a discrete ticket — a standing direction for per-scene level-design polish:
composed emptiness, long sightlines, uncanny repetition. Inherently
iterative. **To turn it into work, name ONE scene and the ONE composition it
gets** (this sightline, this repeated landmark); do not start against the
abstract goal. *(The buildable-now #4 is this pass aimed specifically at
outdoor dread — start there.)*

### 8. Parked — terrain & reshape megabuilds  *(2026-07 design call; do NOT pull forward without a set-piece that demands it AND a fresh decision)*

Cut from active work because their payoff (outdoor sight-occlusion / a sealed
bounded town) fights their cost, and the tilt camera already buys most of the
illusion for free. The cheap replacement is the composition pass (#4). The
DORMANT heightfield prototype + the SHIPPED carved river channel STAY (harmless,
byte-identical at pitch 0); it is the general-purpose builds below that are
parked.

- **Floor-roll warp (was #3d).** Replacing the global affine `_tilt_warp` with a
  height-displaced warp so the whole floor raster rolls. Parked: at ~55° a crest
  tall enough to occlude a standing figure over a short outdoor sightline is a
  near-cliff, not a gentle hill, so a general rolling floor reads wrong at this
  camera; plus a rendering rewrite + a perf pass on the ~6000-tile bake. The
  controlled-shape cases (the carved river trough) already ship without it.
- **Terrain design directions (was #3e).** The sunken-lane cover class, the King
  crest-reveal, terrain-herding toward the well, the deferred peek verb's home.
  All depend on the parked floor-roll and on AI that reads height (v1 ignores
  it). Revisit only if the floor-roll is ever un-parked for a specific set-piece.
- **Brimley reshape (was #4).** Round/organic fog-edge remask + radial
  "handed-back" membrane + subsidence bowl. Parked: **Brimley STAYS a square** —
  the tilt camera + sight cone + fog rim already mean the player never sees a
  corner or a straight edge, so the reshape spent a real build (stressing stealth
  suspicion + King/NPC nav) on an illusion break the camera does not allow. The
  torus wrap + fog rim it wanted to keep "underneath" are already the shipped
  substrate. The one salvaged win (a smaller grid, the actual FPS lever) is split
  out to Optional polish.

### 16. **[Opus]** Ship track — packaging  *(was GAME_CHANGES §25)*

Itch-ready build: pyinstaller (or equivalent) one-file win/linux builds,
save-dir sanity, a settings sanity pass, a version stamp. End-stage; do near ship.

### 17. **[Opus + Fable]** The ancient altar — the CAP of the last sealing  *(was GAME_CHANGES §17; rides #18)*

Move the mid-Brimley standing stones to the **riverbank** (over the point the
Threshold sits beneath; keep the worn cult path). Pre-cult dressing: lichened,
weathered, sunken, nothing yellow — reads OLDER than every cult mark. ONE worn
carving that recontextualizes after the player has seen the Sign (matches the
Mask grammar) + a single `notes` beat (never evidence, no cosmology, §1b). Gives
SEAL its precedent without a word. Lands with the compression pass.

### 18. **[Opus]** Brimley compression (~64x64)  *(was GAME_CHANGES §23)*

Compress Brimley toward ~64x64 at the same content density — cleaner road logic,
shorter dead walks; the altar move (#17) rides inside. **Reconcile with the
parked reshape (#8) + the Optional smaller-grid perf pass:** the SHAPE stays a
square (torus wrap + fog rim underneath); only the SIZE shrinks. The Optional
smaller-grid perf pass is the shippable core of this.

---

## Standing fences (guardrails, not tickets)

- **The lure chain is NEVER stated diegetically** *(was GAME_CHANGES §10)*.
  King → Mara → Walter → PI is felt, not said; the one faint unease
  (`the_case` note) already exists — do NOT build on it. King/Watcher moments
  read as **luck, not omniscience** (powerful, not infallible).
- **The corn is mundane, never the door's doing** (#11). Keep the impossible
  count at **one** (§1b): the single unexplained door, everything else ordinary
  cause-and-effect downstream of it.
- **No dashes in player-facing text** (HARD RULE; flow-guarded).

---

## Optional polish (no canon/lore change; do as time allows)

- **[Opus]** **Brimley smaller-grid perf pass** *(the one salvaged piece of the parked reshape, #8)* — cut `w`/`h` from 100×100 toward ~64–72 and re-pack the 7 buildings + well tighter, WITHOUT changing the shape or the boundary (the square + torus wrap + fog rim all stay). This is the real FPS/tedium win (the one-time whole-map tilt bake, `scenes/base.py` `_tilt_fullmap`, ~6000 tiles). Verify: `tools/profile_brimley.py` before/after, a `tools/capture_world.py` tilt capture, full `python tests/run_all.py` gate.
- **[Fable + Opus]** **Rev. Asa Crane murder reveal + sprite** *(NARRATIVE.md §4; feeds off the #1 provoke pilot)* — Fable for the reveal writing + staging, Opus for the procedural corpse sprite. Punch up
  the `preacher_doomed` death. ~~(1) New discovery location~~ **DONE
  (2026-07):** the doom sends Crane out of his church (the emptied nave's
  one-shot river-mud line points at the water) and his body is found on the
  **Brimley riverbank** (`_brimley_on_enter` / `_preacher_bank_pos`;
  `preacher_body_seen` sets on walking up, so Vane's + Hettie's one-shots can
  never announce an unfound killing). Still open: (2)
  **Bespoke sprite**: the current corpse is a placeholder medieval knight
  (`_draw_body`: helmet + spear + tabard-grey) — replace with a gutted-preacher
  draw (dark palette, white collar, cross in the mess). (3) Stage the approach
  (wrongness before sight, long sightline). Art only now;
  lore unchanged.
- **[Opus]** **Held-weapon offset per camera yaw** *(was HANDCRAFT_BACKLOG 3b)* — `draw_axe_held` reads at rest; the one remaining note is an eyeball pass on the equipped-weapon offset at every camera yaw so it never floats off the hand. Verify with a tilt capture across yaws.
- **[Fable + Opus]** **The grove reads north of Brimley, the river in view** *(2026-07 canon ruling)* — `effigy_grove` is the mouth of the cult's mine, north of town above the river (NARRATIVE §7), and the congregation walked there openly before the rite hid it; the scene art is still a bare corn crop circle. Dress the rim so the river reads below it (the water in view, the dug mouth framing the descent pane) and the northern placement lands without a line of dialogue. Decoration only; the rite, the gates, and the pane stay exactly as they are. Verify with a `tools/capture_world.py` tilt capture + the full `python tests/run_all.py` gate.
- **[Opus]** **Higher-contrast see-through doors** *(PORTALS.md)* — now that the
  aperture's actors are sight-gated, opt in the doors where the
  effect reads strongest: a lit room off a dark hall, the front door onto the
  yard. Draw/opt-in only; no new tech.
- **[Opus]** **Permanently-visible King through an OPEN fold** *(DESIGN.md §1 / `PORTALS.md`)* — the King currently looms through the rift only while it *forms*,
  then steps through (intentional per `PORTALS.md`). A persistent silhouette
  on the far side of an already-open fold is not built; revisit only if the
  direction changes.
- **[Opus]** **Mine retrofit tail cleanups** *(2026-07 code review; none player-visible)* — (a) cache the `_tilt_rack_box` extrusion per (tile, yaw-bucket) like the wall cards (well_passage re-projects ~280 points/frame live); (b) fold `_RACK_CHARS` into the shared wall-scan char-set plumbing instead of a third parallel set; (c) the cave `door_style` key list in `scenes/__init__.py` duplicates the `UNDERGROUND_SCENES` gating idea — derive from one source; (d) `husk_bundle` + `pillar` are registered kinds with no placements (keep as reusable art or cut). Verify: `tools/capture_world.py` tilt capture byte-diff + full gate.
- **[Fable + Opus]** **The barn reads lived-in by several people** *(scene dressing; `scenes/interiors.py`)* — the barn is where Mara went, and it carries her journal (evidence #2), but it currently reads as one person's spot. Dress it so it looks inhabited by MORE than one: multiple bedrolls/pallets, several sets of belongings, more than one place set. Decoration only, no canon or lore change (the journal beat + descent hook stay exactly as they are). Verify with a `tools/capture_world.py` tilt capture + the full `python tests/run_all.py` gate.

---

## Process

### R. **[Fable]** Cross-model review gate  *(process; new)*

After an **[Opus]** ticket lands, run a **Fable** review pass before it
merges. This is NOT a code-correctness re-audit (use `/code-review` or a
fresh Opus context for that, since a model self-reviewing its own diff is the
weakest check). Fable judges what it is strongest at for THIS game: **does the
change land the feeling and hold canon.** For a given diff + the running
build it answers:
- Does it read as dread, or as a mechanic showing through? (atmosphere,
  pacing, the tell)
- Does any player-facing string break the no-dashes rule or the
  `NARRATIVE.md` voice?
- Does it contradict a locked canon fact (`NARRATIVE.md`)?
- What is the cheapest change that would make it land harder?

Output is a short verdict + ranked notes, not a rewrite. The value is a
SECOND, independent model looking at the work, so the direction can flip: if
Fable is doing the implementing, an Opus pass reviews it the same way.
