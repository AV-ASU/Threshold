# THRESHOLD — TODO

> A live to-do list of work that is **genuinely still open**, built from a
> 2026-06 verification sweep of every TODO source in the repo
> (`GAME_CHANGES.md`, `NARRATIVE.md` §8, `KING_PROMPT.md`,
> `HANDCRAFT_BACKLOG.md`) and pruned again by the 2026-07 build sweep.
> Each candidate was checked against the actual code; **anything already
> implemented was dropped** (see "Verified done" at the bottom).
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

### 1. **[Fable]** Investigation dialogue verb — the ask-questions layer  *(VERB LANDED as a pilot 2026-07; expand to the rest of the cast)*

You play a PI, but the only social verb is press-E-to-advance scripted lines:
every NPC conversation is a linear counter (`old_count`, `kid_count` ...). The
choice engine already exists and works (`ui/dialog.py show_choice`) but is used
in exactly ONE gameplay spot (the Sign Chamber altar fork, `scenes/well.py`
~L890). Build an ask-about-topics layer (the girl / the well / the strangers /
the preacher) with answers gated on evidence found + who is being asked. Makes
the core fantasy active for the first time (NARRATIVE §2: reading the town IS
the investigation). Content + design, not engine work. **Highest value-to-risk
item on the list: engine exists, canon is settled, payoff is the core fantasy.**

- **VERB BUILT + PILOTED on Mr. Sable (2026-07).** `scenes/dialogue.open_ask_menu`
  is the reusable layer: E opens a MODAL topic menu (the pick needs the cursor),
  the chosen answer FLOATS over the speaker's head (`ui/float_speech`) so asking
  never freezes the run, and the world keeps running while they talk. Topics are
  `(label, resolver)` where the resolver gates the reply on evidence found; a
  back-out is appended. Sable answers the girl / the well / the other guests /
  the Reverend, each with a colder tier that keys on the evidence count (his
  menace stays compulsion, never a confessed scheme). Wired after his two
  scripted intro visits (intro + register nudge preserved) at `clerk_count >= 3`.
  Guarded by `tests/flow.py` §17c. **To expand:** give Toby / Hettie / Vane /
  Crane their own `_TOPICS` tables and swap their linear-count tails for
  `open_ask_menu`, keeping each NPC's story-critical one-shots (witness, memory,
  handoff) firing first.

- **Pilot beat — the Crane choice** (proof-of-concept for the verb): in his
  2nd conversation, a two-option `show_choice` — provoke him (he goes off to
  "save" the cult) vs hold him back. Canon fence (§1b): the cult can NOT be
  saved or converted (they were answered, not deceived); Crane dies for
  believing he can. The provoke branch feeds the murder reveal below.

### 2. **[Opus]** Portal-door actor sight-gating  *(DONE 2026-07 — see Verified done)*

**DONE.** The see-through aperture now draws the far room's ACTORS as a
per-frame pass (`portal._draw_aperture_actors`) gated by the player's own sight
cone, so an empty room reads through the door but a corner-lurker the player
isn't looking at stays hidden. (Investigation found the through-view drew NO
actors at all before, so this both ADDED the far-room actors and gated them.)
Byte-identical at pitch 0; guarded by `tests/render_smoke.py` [4/4]; preview
`tools/preview_door_sight.py`. *(The softer half — opting in higher-contrast
doors — remains real polish; see Optional polish.)*

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

- **Deferred siblings (do NOT pull forward without a set-piece that demands
  them):** *3b.* Multi-floor buildings as same-building `cross_fold`s to a
  `lodge_upstairs`-style scene (no fade, stride preserved; the reveal is already
  free from `occlusion.py` + blind-spot gating) — compose shipped tools, do not
  build a continuous floor system. *3c.* Fully continuous traversable z (real
  ramps, actors at arbitrary heights, whole interior visible at once) —
  **deferred indefinitely**: big collision/AI/depth-sort/save lift, strains the
  "no roof over the play area" rule, and the payoff partly fights a game whose
  power is restricted sight.

### 3d. **[Opus]** Floor-roll warp — the real rolling ground  *(the next terrain build; unlocks large sloped areas)*

The `draw_ground_mesh` prototype lays a projected mesh over the flat floor —
fine for a discrete hill or a carved channel, but the surrounding raster stays
flat, so relief is thin edge-on and it will not carry a whole rolling area. The
honest fix is to replace the global affine `_tilt_warp` (`scenes/base.py`) with
a **height-displaced warp** so the floor raster itself rolls with `ground_z`.
**Constraints:** still strictly no-op when a scene has no heightfield (byte-
identity gate, all shipping scenes flat); a perf pass on the one-time whole-map
tilt bake (`_tilt_fullmap`, ~6000 tiles); feed `ground_z` into every live actor/
standee/decoration `project()` **and** its paired `depth()` (so a figure on a
bank sorts over the trough). This is the prerequisite for a large sloped
outdoor area (the Brimley subsidence bowl below). Prototype behind
`tools/capture_world.py` + a live tilt capture before wiring a scene.

### 3e. **[Opus]** Terrain design directions — how terrain earns its keep  *(design note, not one ticket)*

Terrain is the ONE tool that gives sight-occlusion in OPEN ground, where walls
can't go — so it extends the game's core restricted-sight dread outdoors, its
weakest zone. Standing directions (each rides the shipped heightfield + crest
LOS; pick a set-piece before building):
- **A third cover class — the sunken lane / ditch:** a depression you crouch-
  move through BELOW a searcher's sightline. Unlike corn it isn't leaky; unlike
  an enclosed hide it doesn't root you — mobile cover that slots into graded
  suspicion (a searcher scores nothing until he crests the ridge). Also the
  natural home for the deferred Pillar-2 **peek** verb (crest a rise slowly).
- **King roam, crest-hidden:** put rises on his road so he crests a hill and is
  suddenly close, or drops into a hollow and out of view. He stays sight-exempt
  (always tracks you); the terrain hides HIM from YOU — the scarier asymmetry.
- **Staged reveals (NARRATIVE §8/§10):** wrongness before sight, then crest and
  SEE it — the exact approach the **Crane murder discovery** (Optional polish)
  wants (a body found away from the church, long sightline, reveal on the rise).
- **Herding without walls + the descent made physical:** a valley/bowl that
  funnels toward the well (well-gravity as literal downhill), ridges that channel
  movement onto the roads (roads-as-lifeline). Feeds the Brimley reshape below.
- **Caution:** AI ignores height in v1, so terrain cover is a PLAYER-only
  affordance for now (good asymmetry, but no cultist takes the high ground yet);
  keep the sim Euclidean-honest so stealth distance-falloff + NPC nav stay true.

### 4. **[Opus]** Brimley reshape — the sealed fog-edge town  *(design landed; not built)*

Shrink Brimley and make it read as a bounded town swallowed by the fold,
not a rectangle with edges. **Stays ONE scene** (`scenes/brimley.py`
`build_brimley`, ~1236 lines). Do NOT split the buildings into a separate
area — `NARRATIVE.md` §11 merged village+mistlands into one Brimley on
purpose; splitting re-creates the discarded topology.

**Decided (build this):**
- **Smaller grid** — cut `w`/`h` from 100×100 toward ~64–72, re-pack the 7
  buildings + well tighter. This is the real FPS/tedium win (the one-time
  whole-map tilt bake, `scenes/base.py` `_tilt_fullmap`, ~6000 tiles).
- **Circular/organic playable mask** — beyond a radius, fill with
  treeline/void so the tilt camera + skybox render the rim as fog. Player
  never sees a corner or a straight edge. (The border band + lobes are
  already ~80% of this.)
- **Boundary = two mechanics combined:**
  1. Keep the rectangular torus `wrap_x/wrap_y` running *underneath*, hidden
     by the fog rim (proven, low risk; wrap keys off `player.x >= world_w`
     in `systems/game.py` ~1190).
  2. Off the roads, a radial "handed-back" membrane: push into the fog and
     your heading bends back with a **drift toward the center** (the well).
     Royce's "the corn handed me back" made literal; claustrophobic by
     design.
- **Exit rule — roads pierce the fog, open ground repels.** A road runs into
  the grey and doesn't come back out on your side; that crossing *is* the
  scene transition (fade to the next sealed room). Everywhere else the fog
  turns you back. The player **arrives on the road** (from `country_lane` /
  the Lodge), so road-as-lifeline is taught at entry; the existing lit-lamp
  road thread becomes load-bearing.
- **No walkable escape.** Every edge is lateral — hands you to another sealed
  room, and the "roads out" (south macro-loop) loop back to Brimley north.
  The only true exits are DOWN (the well, at center, where the drift herds
  you) and the Mask drive-out (SPREAD ending, a cutscene, never a walkable
  rim).

**Sequencing (scope guard):** ship the DECIDED half first (smaller grid +
fog mask + road/repel boundary) and verify the sim stays Euclidean-honest;
only THEN pick ONE wishlist toy. Do not build the boundary and the spatial
illusions in the same pass — each illusion below stresses stealth suspicion
and King/NPC nav, so they land one at a time behind their own verify.

**TERRAIN is now the recommended tool for this ticket (2026-07).** The ground
heightfield (#3) + the floor-roll warp (#3d) turn Brimley from a see-everything
field into a **subsidence bowl** whose ground sags toward the well at center —
which does the herding (well-gravity as literal downhill), gives outdoor
sight-occlusion where walls can't go (hollows + ridges break the long
sightlines that currently kill outdoor dread), hides the King roam behind rises
(he crests a hill and he's suddenly close), and turns the river into a stealth
artery (the carved channel, `carve_channel`: bridge = exposed high route, wade
the trough = hidden but slow + splashing, sight-trapped below the banks). This
is the set-piece that earns the #3d floor-roll rewrite. Sequence: #3d first,
then the bowl + sunken lanes behind a preview (as the river spike was). Keep the
sim Euclidean-honest so stealth distance-falloff + nav stay true under the roll.

**Wishlist — spatial manipulation the layout unlocks (ideas, pick later):**
- *Draw-only (cheap/safe):* landmark repetition (pass "the same" well/pickup
  twice in fog); the town rearranges behind you (rides `sight.py`
  blind-spot draw-gating — sim runs, only the cone is drawn); the straight
  road that imperceptibly spirals back to start.
- *Geometry (needs sim kept Euclidean-honest under the lie):*
  **walls-closing-in** (animate the radius/drift inward over the run — this
  IS boundary mechanic #2, made a variable; the standout); **well-gravity**
  (heading bends a few degrees toward the well each unmonitored moment);
  impossible adjacency / one-way internal folds via `cross_fold` (same-scene
  folds render silent, PORTALS.md); asymmetric in/out travel distance.
- **Caution:** distance/collision tricks stress stealth suspicion (distance
  falloff) and NPC/King nav — keep the sim honest even while presentation
  lies. Star pairing with the decided work: **walls-closing-in +
  landmark repetition.**

**Preserve (load-bearing):** the fold road + Royce/Garrick looping-roads
lines, the well (sole Works entrance), all exits, locals, cult stations.
**Naming:** in player-facing text call it a bounded fog-edge / void-ringed
town, not "island" (implies water). **Verify:** `tools/profile_brimley.py`
before/after, a `tools/capture_world.py` tilt capture, full
`python tests/run_all.py` gate.

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

### 7. **[Fable]** The liminal-composition pass  *(NARRATIVE.md §8/§10)*

Not a discrete ticket — a standing direction for per-scene level-design polish:
composed emptiness, long sightlines, uncanny repetition. Inherently
iterative. **To turn it into work, name ONE scene and the ONE composition it
gets** (this sightline, this repeated landmark); do not start against the
abstract goal.

---

## Optional polish (no canon/lore change; do as time allows)

- **[Fable + Opus]** **Rev. Asa Crane murder reveal + sprite** *(GAME_CHANGES.md §12)* — Fable for the reveal writing + staging, Opus for the procedural corpse sprite. Punch up
  the `preacher_doomed` death, three parts. (1) **New discovery location**: the
  provoke choice (item #1 pilot) sends him to the cult's ground, so find his body
  AWAY from the church — e.g. the well/grove edge, reaching for the souls he
  couldn't save — a real investigative find, not a pop on re-entry. (2)
  **Bespoke sprite**: the current corpse is a placeholder medieval knight
  (`_draw_body`: helmet + spear + tabard-grey) — replace with a gutted-preacher
  draw (dark palette, white collar, cross in the mess). (3) Stage the approach
  (wrongness before sight, long sightline). Art + placement + a location move;
  lore unchanged.
- **[Opus]** **Higher-contrast see-through doors** *(PORTALS.md; the softer half of item
  #2)* — once the aperture's actors are sight-gated, opt in the doors where the
  effect reads strongest: a lit room off a dark hall, the front door onto the
  yard. Draw/opt-in only; no new tech.
- **[Opus]** **Held-weapon offset eyeball pass** *(HANDCRAFT_BACKLOG.md §3b)* — the
  `draw_axe_held` / `draw_revolver_held` code is in and working; this is just
  a visual check of the held-weapon offset at every camera yaw.
- **[Opus]** **Permanently-visible King through an OPEN fold** *(KING_PROMPT.md portal
  pass)* — the King currently looms through the rift only while it *forms*,
  then steps through (intentional per `PORTALS.md`). A persistent silhouette
  on the far side of an already-open fold is not built; revisit only if the
  direction changes.

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
- Does it contradict a locked canon fact (`NARRATIVE.md` / `GAME_CHANGES.md`)?
- What is the cheapest change that would make it land harder?

Output is a short verdict + ranked notes, not a rewrite. The value is a
SECOND, independent model looking at the work, so the direction can flip: if
Fable is doing the implementing, an Opus pass reviews it the same way.

---

## Verified done (dropped from this list)

### 2026-07 build sweep (this branch; each flow/stealth-guarded)

- **Doc/code drift quick-win** — fixed the two stale docs the code had
  outgrown: `README.md` claimed "no disk save" (the cot save-slot in
  `systems/save.py` has existed since 2026-07), and `CAMERA.md` listed the
  blind-spot sight cone as 62°/280/30 where `rendering/sight.py` ships
  74°/360/40 (`SIGHT_HALF`/`SIGHT_RANGE`/`SIGHT_NEAR`). Docs now match code.
- **Portal-door actor sight-gating (was Open #2)** — the see-through aperture
  drew NO far-room actors before; now it draws them as a per-frame pass
  (`portal._draw_aperture_actors`) gated by the player's sight cone (mapping
  each far actor to its apparent host-world pos, since both cameras share
  pitch/yaw/scale) and clipped to the opening. Empty room shows through, a
  blind-spot lurker does not; the rift stays exempt. Byte-identical at pitch 0;
  guarded by `tests/render_smoke.py` [4/4]; preview `tools/preview_door_sight.py`.
- **Ground heightfield PROTOTYPE (Open #3, partial)** — `Scene.ground_z` +
  `build_heightfield` + the crest sight-occlusion (`sight` `ground=` term, in
  both the draw gate and the cult AI) + `draw_ground_mesh` + actor lift, all
  dormant (no scene opts in) so pitch 0 stays byte-identical. Preview
  `tools/preview_heightfield.py`; guarded by `tests/render_smoke.py` [4/4]. The
  floor-raster roll (replacing the affine `_tilt_warp`) + live authoring stay
  deferred (see Open #3).
- **#0 Stealth rework, mechanic + placement** — graded per-enemy suspicion
  (`systems/stealth.py`, `SUS_*` config), two cover classes, searchers that
  sweep + CHECK enclosed hides, the timed struggle, the "?" tell, and an
  enclosed hide in every gauntlet room. `tests/stealth.py` is the sixth
  gate suite. Docs updated (`CLAUDE.md`, `STEALTH_REWORK.md`).
- **#8 Deep mechanical wrinkle, the deep-water WADE** — the flooded deep
  works (works_vats / the_sump / depths_threshing) now stand in walkable
  `~` water: wading HALVES the player's speed (no sprinting clear) and
  throws a loud splash searchers converge on, so standing water is a
  routing risk (skirt it dry, take the wet shortcut and pay in noise, or
  splash to bait a searcher and slip past). Self-contained: rides the
  existing `Scene.emit_noise` / `stealth.hear_noise` ear, no new AI. The
  Brimley river is excluded (its own set-piece). `WADE_*` config,
  `Game._wading`, the `_flood` scene helper, a `step_water` splash SFX;
  guarded by `tests/stealth.py` §10. (The listener-cultist alternative
  was the road not taken.)
- **#1 Food-scarcity visuals** — bare_shelf shop runs (+ book spines on
  stocked shelves), tended vs gone-over `garden_patch` beds in Brimley,
  and the stage-2 counter-eater in the shop (`pose="eat"`).
- **#2 Counter detail** — `_d_counter` (neutral: seams + worn lip) on every
  counter; the butcher extras (knife scores, the old stain) live on the
  shop's own `butcher_counter` kind so the Lodge desk stays mundane.
- **#3 drowned_body** — DECIDED: CUT. Placement, draw fn, and kind-set
  entry removed; the seep pool + claw gouges carry the room.
- **#5 Onboarding, the soft version** — the notebook's italic "The thread:"
  line, derived live from run state (`_current_lead` milestone ladder),
  plus two one-shot stealth teach cues (first corn entry, first strong
  being-seen fill). Never a checklist, never a waypoint.
- **#6 Mara's arc** — the journal desc/barn log reconciled to the
  ache-bearing pages, the letter carries the ache as a shape, Hettie's
  counter memory of the girl; and the REAL bug fixed: the evidence
  one-liner was clobbering her four-line hive exchange in the same frame,
  so the "answered, not deceived" payoff had never displayed.
- **#7 The lure collision** — one private narrator beat after Mara's lines
  (gated on `flashback_seen`): dream + case + her, and the PI declines to
  finish the thought. Never evidence, never a note.
- **#8 Descent narrative half** — the procession candle NOTE, the
  kneeler-wake line, the rite-holder's weight trigger; depths_stair stays
  deliberately empty.
- **#9 Ending fork** — the SPREAD counterweight beat at the shaft floor
  with the Mask in hand names the other road; the crossing stays a silent
  non-event; the locked ending texts untouched by choice.
- **#10 Town reactivity** — one pre-mutation state beat per ambient local
  (Garrick / Old Pell / Mrs. Calder / Royce) via the `beats` hook;
  `escalate()` documented as inert; the dialogue.py docstring fixed.
- **Review-pass fixes (2026-07)** — the sight-fringe chase/search
  oscillation (sub-`SUS_SCORE_HOLD` scores no longer fill suspicion), the
  search budget scaling with the sweep, the struggle burst now CONVERGES
  the room's hunters, the "?" tell scoped to scouts, the fold note no
  longer misattributed by state beats, one shared `grab_allowed` gate,
  shared suspicion/sweep helpers for both cult machines, per-frame
  import/Surface/Font.render waste removed, and the dead `respects_hide`
  distance zap deleted.

### 2026-06 sweep

Checked against code and confirmed implemented; kept here so the next sweep
does not re-add them:

- **Being-seen / exposure HUD** — notched 10-unit rate bar in `_draw_hud`,
  `_being_seen` rate split from `visibility` state in `threat_mixin.py`.
- **Portal rendering (camera-respecting black-gold pseudo-3D seams)** —
  `rendering/portal.py draw_rift_door` foreshortens like a wall, thins
  off-angle, with the gold light-pool/rim and the desaturated through-view.
- **Watchers rehomed as His gaze** — fiction throughout `threat_mixin.py`
  already frames the curse as His eye reaching into the plane, not a
  side-cult spell.
- **Gun = false-power threshold** — all four sub-rules hold and are
  flow-guarded (<3 ev kills cultists, 3+ only stuns, King unshootable, a
  clean round always kills a local).
- **Corpse persistence scrapped** — no `dead_locals` ledger or `mold`
  accumulation; in-room bodies only.
- **Fireplace / stove / bed / shelf oblique detail** — `_d_firebox`,
  `_d_mattress`, `_d_shelves`, `_d_logs` exist and are wired in.
