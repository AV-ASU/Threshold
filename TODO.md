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
  every story-critical one-shot (Hettie's preacher reaction + Mara memory +
  paper trade, Vane's murder-he-can't-report) still VOLUNTEERING itself
  ahead of the menu. Toby is the exception since the 2026-07 rework: his
  witness account is EARNED on the photo exchange (a kid can't know the
  case on sight), and his playscript flinch + school warning were cut as
  structurally unreachable (he turns at 3 evidence; the envelope and the
  cult book only exist at 3). Flow
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
  per-NPC answers, one or two signature questions each (Pell's corn
  pride, Calder's plate, Royce's roads + his you-got-IN counter-ask,
  Garrick's road warning), the TODO #10 reactive beats still volunteering ahead of
  the menu, and the **fold note moved off the old any-talk trigger onto
  the exchanges that carry the account** (Royce/Garrick `on_ask`,
  `reflect=False`, earned by asking). Guarded by `tests/flow.py` §17e +
  the reworked §16c. **The unnamed "newcomer woman" NPC is CUT from the
  project entirely (maintainer call, 2026-07)** — an unexplained
  welcomer on the farmhouse path read as noise, not dread; she never spawns
  (flow-guarded), and the whole convert layer she rode was later cut
  (TODO #22c).

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
  the naming where they can hear it — `preacher_doomed` latches, his death
  proceeds, and the PI's culpability lands as a NOTE `crane_provoked`) vs
  hold him back (the fire is only banked — the question stays open to press
  later; he is never savable-by-conversion, §1b — the player just decides
  whether HE is the one who points him). The provoke branch feeds the murder
  reveal below. NOTE the behavior change: his doom is no longer an automatic
  visit-2 counter. (**The old `_the_third_thread` stall-breaker was CUT
  with the TODO #22 rework.**) The surface set is now three fixed,
  always-reachable pickups — the receipt (Hettie's shop), the detention
  record (Vane's office), and the journal (the barn), findable in any order —
  so the case can no longer stall waiting on a provoke, and Crane's press/hold
  choice is a pure character beat rather than a gate. The removal is
  flow-guarded. The silently-filed journal beat (`show=False`) still lands
  its revisit nudges.

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
  lucky host and it lands nowhere: he takes it graciously and it means
  **nothing** — no reward, no thanks that reads as real. The whole town
  aches for word of the outside; his want was never the outside, it was
  the rooms full (NARRATIVE §4), and a newspaper cannot touch it. The
  anti-reward that characterizes what Sable *is*. Outcome is a `notes`
  beat / a chill, never an item.
- ~~**Vane is a recipient too — and his is a TRAP, not a gift.**~~ **DONE
  (2026-07, shipped with the Vane arc):** the `paper` exchange in
  `VANE_CONVO` (Kurt Cobain dead on the front page reads, to a man who
  wants it all to *end*, as *permission*, not hope) adds
  `VANE_PAPER_DESPAIR` (+2) on the hidden despair ledger — the one
  recipient whose allocation carries a TRACKED consequence, the deliberate
  exception to the "mood, not a meter" fence below. The give-beat
  telegraphs it as mood (the PI's own closing line), no number shown; one
  copy, so giving it to Vane means Hettie (and the recipients above, when
  they land) go without. Guarded by `tests/flow.py` §17f.
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

### 3. **[Opus]** Ground heightfield — blind-spot hills  *(DESIGN.md §10; PROTOTYPE landed 2026-07 — floor-roll rewrite + live authoring deferred)*

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
- **Landmark repetition + same-scene silent folds** (`cross_fold`, DESIGN.md §7,
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
Surfacing (mundane Americana that curdles): ~~a weathered town sign ("BRIMLEY,
NORTHERNMOST CORN IN THE WORLD, EST. 1894")~~ (LANDED 2026-07: the old-timey
welcome board carries the boast + EST. 1894 in BOTH the intro drive-in sign
(`ui/cutscenes.py _draw_road_sign`) and the in-game welcome sign
(`rendering/props.py _draw_town_sign_solid`, the BRIMLEY variant only;
directional TOWN/WELL signs stay compact) — matching designs. **Still open:**
the SPREAD ending's blank-back BRIMLEY sign (`rendering/spread_drive.py
_sign_back`) was left untouched on purpose; sync it to the new board, see
Optional polish below), ~~a proud local line~~ (LANDED
2026-07: Old Pell is the grower — his PELL_CONVO corn exchange carries the
pride and the uncut-fields grief), county-fair ribbons (no dashes). Keep the §1 April dead-corn note. `NARRATIVE.md` §1 setting
note 2 gets the identity + guardrail.

### 12. **[Fable + Opus]** Royce the trucker + the rusting semi  *(was GAME_CHANGES §28)*

Promote Royce to the man who drove **Brimley's supply run** — the severed
supply line made a person (Hettie's shelves are bare because *his* deliveries
stopped). Fable: a small dialogue nudge (he ran the route, goods in and out).
Opus: place his **picked-clean semi rusting at the town edge** (the town ate
its own last shipment; optional light scavenge, **never evidence**). Reconcile
with his worker job-loop (pacing the road). Royce no longer converts (the
rot-people layer was cut, TODO #22c); he stays an ordinary local.

### 13. **[Fable]** PI theory ladder — the notebook thinks  *(LANDED 2026-07; was GAME_CHANGES §20)*

**DONE.** The case book carries two derived, first-person surfaces pinned
above the clue list (`ui/journal_ui.py`, the merged Casebook's Case tab;
`Game._working_theory` / `_case_timeline` in `systems/narrative_mixin.py`,
guarded by `tests/flow.py` §24d):
- **Working Theory** — a **set-aware** synthesis composed from WHICH clues are
  held, in any order (not a count tier): the read of Mara (taken → willing, the
  pivot needs the dig), the **bear-gated** son thread, the trap ("how do I get
  out?"), the **robes-as-lever** WRONG conclusion the game never corrects, and
  the Mask's SPREAD gravity. Absent threads simply are not there.
- **Timeline** — Mara's life in HER order (barn → store tab → booking → dig →
  letter), dated where the paper gives one and best-guess otherwise, capped by
  the frozen town clock.

The **wrong-space** beats fire from `cross_fold` (`_note_fold_portal` = a visible
pane, awe; `_note_fold_loop` = the SECOND silent loop, the creep), latching
`crossed_a_fold`. The FACT/SOURCE/QUESTION idea from the original brief became
the Timeline (a chronology reads truer than a flat list). Canon locked: the
NARRATIVE invariant "the PI accepts the impossible; he never learns the
mechanism."

**Opening rework (maintainer review):** the old soft-lead line (`_current_lead`)
is **cut from the notebook display** — the direction lives in the case file now,
not a header (the method + its §24c guard linger as dead code; retire both if the
soft-lead is fully abandoned). Theory + timeline are **earned** — pinned only
once they have content — so a fresh run opens on just `the_case`, never an empty
"theory." `the_case` was rewritten as a real case file (`Client:` / `Subject:`
format): minimal intake knowledge (drove north, went silent, trail to Brimley, no
religion or cult on the page), Walter's plea after the PI leveled with him, and
the PI's finisher pride SHOWN not told. The **robes-as-lever** thread now gates on
actually meeting the cult (the grab / their testimony), not the evidence count,
so the notebook never gets ahead of what he has met. First person throughout
(`_PI_WEATHER` too; §23/§24c green). *(Open polish: a scrollable card if the
theory outgrows one page; interior-beat tiering, parked from #22c.)*

### 13b. **[Fable]** Interior voice — quiet the routine reactions  *(maintainer call 2026-07; the Casebook merge landed the structure, this is the copy pass)*

**Structure LANDED (2026-07 Casebook merge, `ui/journal_ui.py`):** Inventory
(I) + Case Notebook (N) are ONE tabbed book now (Case | Tools | Papers), and
the Case tab opens on the **Working Theory pinned first**, so the notebook
READS as an evolving theory rather than a flat pile of reactions. Every
case-book write fires the (now NAMED + enlarged) corner scribble toast, the
one reliable per-write tell. **Still open (the maintainer's actual grievance:
"every interaction does something and never leaves the player thinking"):**
the on-screen PI narrator captions still fire on nearly every world-prop
examine. The census (grouped) for the copy pass:
- **Cut candidates (ROUTINE-REACTION, ~30 sites)** — prop examines that
  editorialize a conclusion: the lodge register/ledger recaps, the well /
  news-rack / payphone / cellar-key monologues, headstone + candle
  re-examines, `barrow_tools` / `scarecrow` / `backwoods_note` / `worn_stone`
  / `bell_tower` / `the_burning` / `the_fall` / `threshing_floor` /
  `works_cistern_seen` / `the_doorframe` flavor `_evidence` (these write
  NOTHING to the book — caption only). Trim to a terse factual line (state
  the thing, cut the PI's spelled-out conclusion) or silence, so the player
  draws the inference. **The revisit-nudges** (`_REVISIT_NUDGES`, the
  "I should go back and ask him" appends) are the clearest "the game does the
  thinking for you" — decide with the maintainer whether they go.
- **KEEP (not reactions-to-random-things):** the five CANONICAL_EVIDENCE
  beats, the descent-voice arc (`_DESCENT_VOICE`), the dream, the Mask
  temptation, Mara's calling-out, the fold notes, the threshold recognition,
  and the deliberate atmospheric one-shots that ARE the dread (the frozen
  news rack, the payphone with your own voice, the empty church). Cutting
  these would hurt the game.
- Each cut must keep the flow.py guards green (many assert on these
  captions/notes — §16, §17b/c/d, §24) and update the ones whose behavior
  legitimately changes.

### 14. **[Opus]** The Works as a MINE — side-dug rooms, not hallways  *(was GAME_CHANGES §21)*

Make the Works read as a mining effort: timbered side-chambers dug off the
halls (some finished, some half-dug, the deepest hand-clawed), spoil heaps,
cart ruts, a degradation arc ending at the Deepest Face. A few pockets carry
loot / testimony placement; most is just labor made visible.

- **The FICTION half landed (2026-07, the mine retrofit + killer-cult
  scrub; guarded by flow §19b).** Room identities and text now read as the
  dig over old workings: `the_cells` = the diggers' bunk cells (captivity
  fiction cut), `the_old_stores` = the Old Stores (the bone vault is purged,
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

### 19. **[Opus]** Carcosa palette alignment — one look, every glimpse  *(2026-07 ruling; NARRATIVE §5)*

**LANDED 2026-07 (`claude/opus-tasks-selection` branch) — pending the
maintainer's visual sign-off.** `_cold_fire_pit`
(`rendering/sprites_carcosa.py`) was re-graded off the pale-teal/green
palette into the codified black + dim-gold family: the receding-shaft
gradient, the rim tongues `(150,214,184)`/`(206,204,130)` → muted golds, the
writhing-form ellipse `(52,92,78)` → dark gold-brown, and the wet streaks
`(188,220,188)`/`(220,212,140)` → paler dim golds. The BREAK hard-cut
inherits it through `draw_king_death` / `draw_carcosa("spread")`. The
"cold/wrong fire" now reads through darkness + the writhing/drooling motion,
not hue. Before/after captures rendered; the full `python tests/run_all.py`
gate is green. The one thing left is a maintainer LOOK before it merges (the
call code can't settle). Original brief kept below.

Carcosa's look is codified (NARRATIVE §5): black is the ground note — black
sky, black stars, twin suns low, His gold fire the only light (the rift's
black-gold grammar at cosmic scale); the SEAL tableau is the reference image.
The King-catch furnace and the BREAK blast are off-model: `_cold_fire_pit`
(`rendering/sprites_carcosa.py`) burns pale-TEAL/green — tongues
`(150, 214, 184)` / `(188, 220, 188)`, forms `(52, 92, 78)` — and the BREAK
hard-cut (`draw_carcosa(..., "spread")`, `ui/cutscenes.py`) inherits it.
Re-grade the cold fire into the black + gold family ("fire, but wrong and
cold" must survive the recolor — wrongness by behavior and darkness, not by
hue). Verify with a before/after frame capture at sampled timestamps
(`tests/render_smoke.py` drives every ending) and a look from the maintainer
before it lands.

### 22. **[Opus + Fable]** The Case — evidence as Mara's trail (the big rework)  *(2026-07, settled with the user; canon NARRATIVE §6, design DESIGN.md §9)*

The evidence system is the game's crux (it drives attention, danger, and
the PI's unraveling) and it is currently half-dead: the "pool of six, any
3" never held (the surface three are mandatory, and evidence 4/5/6 gate
NOTHING — every threshold is ≤ 3). Rework it into **Mara's trail**: a
biography reconstructed from carryable, self-evident, Mara-only items.
Canon + design are written; this is the code catch-up. Big — touches
`CANONICAL_EVIDENCE`, the King-gate, the rot mixin, the confrontation,
and the tests. Sequence it:

- **22a. The roster. LANDED (2026-07).** `CANONICAL_EVIDENCE` is now the
  trail: `maras_receipt` (the store tab, Hettie's shop), `maras_record`
  (the booking slip, Vane's office), `maras_journal` (barn), `maras_dig`
  (the Sign in Mara's own hand, the Scriptorium — a room that is not the
  cell), `maras_room` (the unsent letter, her cell). All are **pickup
  items** (new items `receipt` / `detention_record` / `maras_scrawl`). The
  gate re-points for free (the count is `len(save.arg("evidence"))`, and
  `_evidence` only logs canonical names) — no gate-constant edits; the
  **three surface beats** keep the Act-1 ramp reachable above ground.
  `the_ledger` + `the_preacher` now file as case **notes** (`_evidence(...,
  note=True)`); `the_sign` leaves the count (the Mask stays the keystone
  item); **Mara is proof** (`the_congregation` files a note via
  `_log_note`, the calling-out still fires). **World-persistence:** the
  records live in the scene (the shop spike, the office files), not on the
  NPC, so a dead Hettie/Vane can never soft-lock the descent (warm handover
  still rides Hettie's Mara-memory beat). The obsolete `_the_third_thread`
  Crane-provoke stall-breaker was removed (the surface trail needs no
  provoke). Guards: smoke's canonical-wired scan follows the dict; flow §9
  gathers the three surface beats + a world-persistence check (§9b); the
  ledger/sign/preacher/congregation guards flipped to notes/proof. Full
  gate green.

- **22b. The bear + the name. LANDED (2026-07).** New item `bear` (tag
  reads **SAM**; the letter stays "a boy" unnamed, per the 2026-07 ruling,
  so the tag is the ONLY place the name appears besides the PI's mouth).
  Toby **lends** it as a VOLUNTEERED beat, earned by the PI's patience with
  a scared kid (`toby_told` + the `holding_up` reassurance), never
  interrogable; optional, never in `CANONICAL_EVIDENCE`, files a note. On
  the surface it is tender and unexplained; once the PI reads the letter
  (`evidence_maras_room`) its inventory desc **detonates** (dynamic
  `effective_desc`). The **name-beat** (`MARA_CONVO` "name" exchange,
  bear-gated, `ends:True`): the PI says the name, she seizes him, the rite
  cracks, she reveals she has always known the boy is not down there and
  digs on anyway, and **REFUSES the bear** (2026-07 ruling); fate unchanged
  (turns back to the dig). **Invariant guarded** (flow §28c): Mara never
  says the name; only the PI and the tag do. Full gate green. *(Open polish:
  a bespoke bear inventory sprite with a visible tag; the name currently
  lands through the item desc + dialog.)*

- **22c. The PI rots, not the town (four tiers). LANDED (2026-07).** The
  world rot is the INVESTIGATOR'S now (`DESIGN.md` §9; fixes STORY_AUDIT B6,
  NARRATIVE §2). The people-change is CUT: `_convert_local`,
  `_turned_local_dialogue`, `_converted_local_dialogue`, `ROT_TURN_LINES`,
  `_rot_locals`, and the `_spawn_counter_eater` tableau are gone, and
  `ROT_CONVERT` / `ROT_TURN` are removed from config. The town stays
  ordinary to the end (Mrs. Calder never joins and keeps both place
  settings; the resisters keep their voices; the rot DECALS + ambient air
  still run, the place still rots). In their place, a four-tier PI register
  (`scenes/dialogue._pi_tier` / `_PI_WEATHER` / `_pi_framing`) composes the
  PI's deepening interior weather onto each surface principal's conversation
  framing, keyed to evidence (0 / 1-2 / 3 / 4+); the NPC's words never
  change, only the man's read of them (Vane keeps his own mood prompt). Per
  the 2026-07 ruling, the converts' lost gaze pressure is **NOT** re-sourced
  (the cult enemy patrols carry it). Guarded by flow §23 (c)/(c2). *(Open:
  interior-beat tiering inside exchanges, and the theory-ladder notebook
  #13, both left for later.)*

- **Guards:** DONE across 22a-c. smoke's canonical scan follows the dict;
  flow §9/§9b (roster + world-persistence), §28c (bear + name invariant +
  bear-gated ending), §23 (no-people-change rot + four-tier register). Full
  gate green. `DESIGN.md` §3 describes the mechanism generically (unchanged
  by the key swap) and §9 already documents the model, so no §3 edit was
  needed.

**#22 is COMPLETE (22a + 22b + 22c all landed 2026-07).**

## Blocked on a human at the keys

These are BUILT and guarded; what remains cannot be settled from code
inspection and needs a person playing the game.

### 5. **[Opus]** Stealth rework — the TUNING loop

The mechanic AND the placement pass are built and guarded
(`tests/stealth.py` + flow §25; see `DESIGN.md §12` for the design
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
  King → Mara → Walter → PI is felt, not said. The faint unease now lives in the
  `the_dream` and `the_congregation` notes (NOT `the_case`, which the 2026-07
  review rewrote into a clean mundane intake, cutting its old "couldn't say why"
  beat); the "why is a finisher this deep on a nothing-case" disproportion is
  left to be FELT in play, never stated. Do NOT build on any of it. King/Watcher
  moments read as **luck, not omniscience** (powerful, not infallible).
- **The corn is mundane, never the door's doing** (#11). Keep the impossible
  count at **one** (§1b): the single unexplained door, everything else ordinary
  cause-and-effect downstream of it.
- **No dashes in player-facing text** (HARD RULE; flow-guarded).

---

## Optional polish (no canon/lore change; do as time allows)

- **[Opus]** **SPREAD ending sign sync** *(2026-07; deferred with the intro-sign rework, TODO #11)* — the intro drive-in sign and the in-game welcome sign now render the old-timey BRIMLEY board (WELCOME TO / NORTHERNMOST CORN / EST. 1894, POP struck through). The SPREAD ending's drive-OUT shows the **blank back** of that same sign (`rendering/spread_drive.py _sign_back`, "the side they never painted"), which was left untouched. Update `_sign_back` so its board proportions + posts match the new welcome board (the back stays blank/unpainted by design; only the shape needs to agree). Verify with a headless capture of the SPREAD drive-out (`tests/render_smoke.py` drives every ending). Do NOT touch the rest of the ending.
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
- **[Opus]** **Higher-contrast see-through doors** *(DESIGN.md §7)* — now that the
  aperture's actors are sight-gated, opt in the doors where the
  effect reads strongest: a lit room off a dark hall, the front door onto the
  yard. Draw/opt-in only; no new tech.
- **[Opus]** **Permanently-visible King through an OPEN fold** *(DESIGN.md §1 / `DESIGN.md §7`)* — the King currently looms through the rift only while it *forms*,
  then steps through (intentional per `DESIGN.md §7`). A persistent silhouette
  on the far side of an already-open fold is not built; revisit only if the
  direction changes.
- **[Opus]** **Mine retrofit tail cleanups** *(2026-07 code review; none player-visible)* — (a) cache the `_tilt_rack_box` extrusion per (tile, yaw-bucket) like the wall cards (well_passage re-projects ~280 points/frame live); (b) fold `_RACK_CHARS` into the shared wall-scan char-set plumbing instead of a third parallel set; (c) the cave `door_style` key list in `scenes/__init__.py` duplicates the `UNDERGROUND_SCENES` gating idea — derive from one source; (d) `husk_bundle` + `pillar` are registered kinds with no placements (keep as reusable art or cut). Verify: `tools/capture_world.py` tilt capture byte-diff + full gate.
- **[Fable + Opus]** **The barn reads lived-in by several people** *(scene dressing; `scenes/interiors.py`)* — the barn is where Mara went, and it carries her journal (the `maras_journal` trail beat), but it currently reads as one person's spot. Dress it so it looks inhabited by MORE than one: multiple bedrolls/pallets, several sets of belongings, more than one place set. Decoration only, no canon or lore change (the journal beat + descent hook stay exactly as they are). Verify with a `tools/capture_world.py` tilt capture + the full `python tests/run_all.py` gate.

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

---

## Story & dialogue audit — open findings (re-verified 2026-07)

> Folded in from the retired `STORY_AUDIT.md`. The audit's **A** (broken
> beats) and **B** (canon breaks) tiers were resolved on-branch; **B6** and
> the convert half of **B7** are mooted by the TODO #22c people-change cut.
> Every **C** item below was **re-verified against the current tree**
> (2026-07); FIXED/MOOT ones were dropped or marked. The **D** voice/polish
> items are player-facing TEXT (still open); the audit's "stale dev comments"
> item is **DONE** (see the note under D).

### C. Interaction-logic bugs — ALL RESOLVED (2026-07)

The whole C tier is closed. The batch C1, C2, C4, C5, C7, C10, C12, C13,
C14, C15, C16 landed on the `claude/opus-tasks-selection` branch (verified
against the current tree first, then fixed + guarded); the earlier sweep
had already handled C6/C8 (dead code removed) and C9/C11 (dropped), and C3
was MOOT. Kept as a resolution log, not open work.

- **C1. RESOLVED.** `_sign_update` step 4 (`scenes/well.py`) now holds the
  rite-holder closer while `game.narration.active`, so a fast Mara exchange
  no longer clobbers the lure caption (which has no `on_complete`).
- **C2. RESOLVED.** `_reset_run_state` (`systems/game.py`) now clears
  `_mara_stage`, so a death/quit mid-staging can't eat the next run's
  calling-out.
- **C3. MOOT (audit reasoning was wrong).** The `< 3` grove-meter beats
  (`scenes/hidden_folds.py`) are reachable via the ungated `sable_on_death`
  Invitation drop. Residual: on the intended path the gradual fill is never
  seen (an authored-for-an-unreachable-progression smell, not dead code).
- **C4. RESOLVED.** The cellar-key pickup narration (`scenes/lodge_yard.py`
  `_took`) dropped the phantom "a doorframe stands against the boards"
  paragraph (the 'M' fold was cut); only the key-on-a-nail beat remains.
- **C5. RESOLVED.** The church LOGIN terminal (`scenes/villager_houses.py`)
  was removed outright — the `_open_login_terminal` handler, the invisible
  interact NPC, and the CRT prop — killing the always-"ACCESS DENIED" ARG
  tone in a 1994 parsonage. The leftover `C` map marker is blanked to floor.
- **C6. RESOLVED (dead code removed, earlier sweep).** The unreachable
  `blocking_innkeeper` branch and its docstring were deleted; the bedroom is
  intentionally ungated.
- **C7. RESOLVED.** "You dream of a doorway." (`ui/cutscenes.py`) is now
  gated to rite mode, so it no longer renders during the waking memory flash
  (the dream-once canon).
- **C8. RESOLVED (dead code removed, earlier sweep).** The unreachable
  `_on_player_death` respawn path was deleted.
- **C10. RESOLVED.** Garrick's "days now" beat (`scenes/brimley.py`) now
  gates on `preacher_body_seen` (matching Vane), so it can't fire the
  instant Crane is pressed.
- **C12. RESOLVED.** `_spawn_hunting_sheriff` (`systems/rot_mixin.py`) still
  spawns + holds every hollow-office load (the room stays lethal), but the
  intro notice + sting now fire once per run (`_sheriff_announced`), and the
  line trails off ("But I can't ...") instead of reporting the failure.
- **C13. RESOLVED.** The Sable fold reproach (`scenes/dialogue.py`) now
  requires `crossed_a_fold` in addition to the `the_fold_told` note, so the
  first-person "it set me back down" is never a lie (flow guards updated).
- **C14. RESOLVED.** (a) the handler-less dresser `[E]` cue was dropped
  (`scenes/lodge.py`); (b) Toby's closet drawing left as-is (decoration
  only, no false prompt); (c) the altar `[E]` cue is now dropped once the
  Mask is taken (`scenes/well.py` `on_enter_fn`); (d) the barn + farmhouse
  sealed hatches now show a deadpan notice (`scenes/interiors.py`,
  `scenes/villager_houses.py`).
- **C15. RESOLVED (annotated).** `_threshold_seal` (`scenes/depths.py`) got
  the explicit comment that the lone-trigger is DELIBERATE — the
  point-of-no-return fork is spent upstream at the blast, so carrying the
  Mask to the frame IS the commit.
- **C16. RESOLVED.** `_ready_for_the_desk` (`scenes/dialogue.py`) dropped the
  `sable_greeted` requirement (the PI checked in at that desk on arrival), so
  a player who never greeted Sable still gets the go-back-to-the-desk pointer
  at 3 evidence.

*(Earlier: **C9** — Pell no longer `fold=True`; **C11** — Toby's cold-open
is gone, his witness account is photo-earned.)*

### D. Voice / polish (player-facing text — still open)

- Narrator "vanished into the corn" (`scenes/villager_houses.py`) adopts
  Crane's drift-away impression as fact; canon is one night procession, and
  §2 corrects the image for Mara ("not into the corn"). Crane's "more every
  season" and Sable's "no end of those this past year... They come" keep
  arrivals in the habitual present; arrivals ended before the seal.
- Revolver description leaks mechanics: "(3+ evidence)" (`systems/items.py`);
  also "fires it in the way you're facing."
- Descent interior voice wobbles POV (first-person notes vs second-person
  on-screen beats, `systems/game.py`).
- ~~Notebook headers from slugs (`ui/notebook_ui.py`): "Maras Room", "Chalk
  Deep", "Descent Mask", "Showed The Clerk" — dev slugs where the case file
  should read like the PI typed it.~~ **MOSTLY DONE (2026-07 Casebook merge):**
  the slug→title map moved to `ui/case_titles.py` (`humanise`, shared by the
  book and the scribble toast) and was expanded to cover the interior beats;
  any unmapped slug still falls back to Title Case, so add authored titles
  there as new beats land.
- HUD fall-through labels: "Dark" (the Hive!), "Depths Antechamber", "Effigy
  Grove", "Threshold" (`scenes/base.py` fallback), plus `"lodge": "the Inn"`
  against "Arcadia Lodge" everywhere else.
- NPC object names "Clerk"/"Sheriff"/"Preacher" leak on generic paths
  (corpse examine: "Clerk. Face-down where the round put them.").
- Placeholder texts on cued interactions: "Some old tools." (the beat's
  designed contradiction is lost), "A small stash.", "A weathered
  headstone.", "A scarecrow.", "A key.", "An axe for chopping wood."
- Small ones: payphone "your own voice, already mid-sentence" (make it
  spatial); Sable's "last night"/"tonight" against elapsed play; the robe
  "hangs... pressed and folded"; the Invitation's "Sleep where we slept" with
  no sleep verb at the school; Mara's "I have never been this close" vs the
  letter's locked "I've never been this close"; the handoff's "the day they
  were ready" (canon: HE was ready); burn-site "All of their things." vs the
  Sorting Hall cataloguing everything; Mask desc "So, you suspect, does the
  door in the deep" plants "the door can open"; threshold recognition + "A
  doorframe with no wall." fire at the cave mouth, 13 sight-gated rows before
  the frame is visible; lowercase hide notices; "waking the dark ." double
  space; "midwestern" casing; Garrick and hollow Vane both call the PI "son";
  two simultaneous Hetties (door + counter); duplicate candle decoration in
  Toby's house.
- Missing canon clincher: §4's ledger entry promises "your own name, signed
  in tonight, already among them" — the cellar text only gestures at it and
  the desk sign-in is optional; one clause conditioned on `register_signed`
  closes the loop.
- ~~Stale dev comments that will mislead future edits.~~ **DONE (2026-07
  comment pass):** the Deep Stair live-descriptions, the `[E] cue: the
  Playscript` / testimony refs, the lodge car-keys/tab comments, the phantom
  'M' fold, the cornfield_path preacher-patrol note, and the farmhouse
  glitch-wall docstring were all corrected — along with every dangling
  citation to a deleted doc (`GAME_CHANGES §N`, `STEALTH_REWORK`,
  `STORY_AUDIT B6`, `HANDCRAFT_BACKLOG`), the dead in-game `F3` references,
  and the C-item lying comments. Accurate "was CUT" provenance notes were left intact. (The legacy scene
  keys and the `sigil_rubbing` save-migration were renamed / removed in the
  follow-up legacy-key pass, per the 2026-07 no-backward-compat ruling.)

### From the code-health audit (retired `CODE_HEALTH_AUDIT.md`)

Every high/medium/low finding from that pass was fixed on-branch; only one
awareness-only item remains: **L5 — complexity hotspots.** The largest
function bodies (`tests/flow.py main`, `scenes/brimley.build_brimley`,
`systems/render_mixin.draw_world`, `rendering/sprites_npc.draw_npc_sprite`,
`rendering/king_unfold.draw_king_unfold`) match the project's deliberate
"one cohesive beat per function" style and sit behind the test gate; listed
so growth stays a choice, not an accident.
