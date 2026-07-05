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

## Open work

### 0. Stealth rework — the TUNING loop  *(needs a human at the keys)*

The mechanic AND the placement pass are built and guarded
(`tests/stealth.py` + flow §25; see `STEALTH_REWORK.md` for the design
and its status note). What remains only proves out against a human
player: the suspicion fill curve (`SUS_FILL_RATE`), the concealment
factors, the sweep budget, and the struggle window/presses. Also
deferred to this pass on purpose: the Pillar-2 **peek** verb (free look
under tilt already carries the information function) and an
exit-takes-a-beat vulnerability window on enclosed hides.

### 11. Combat / difficulty — judgment calls (decide on purpose)

Not bugs; deliberate choices worth confirming rather than leaving by default:
the gun goes **stun-only at 3 evidence** with ~14 rounds total per run, so the
main combat verb is removed exactly when danger spikes (agency loss vs
intended dread). There are **no difficulty options**, so the visibility/Watcher
death-spiral hits newcomers and is trivial to experts. Items are gates, not
resources (armor slots return 0). Consider: transforming the stun into a
tactical window rather than a tax, an easy/hard toggle, or light resource
tension — only if it serves the horror, not despite it.

### 4. The liminal-composition pass  *(NARRATIVE.md §8/§10)*

Per-scene level-design polish: composed emptiness, long sightlines, uncanny
repetition. Inherently ongoing/iterative rather than a single shippable
ticket — scope a concrete first scene before starting.

### 12. Brimley reshape — the sealed fog-island  *(design landed; not built)*

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

**Wishlist — spatial manipulation the layout unlocks (ideas, pick later):**
- *Draw-only (cheap/safe):* landmark repetition (pass "the same" well/pickup
  twice in fog); the town rearranges behind you (rides `sight.py`
  blind-spot draw-gating — sim runs, only the cone is drawn); the straight
  road that imperceptibly spirals back to start.
- *Geometry (needs sim kept Euclidean-honest under the lie):*
  **walls-closing-in** (animate the radius/drift inward over the run — this
  IS #2, made a variable; the standout); **well-gravity** (heading bends a
  few degrees toward the well each unmonitored moment); impossible adjacency
  / one-way internal folds via `cross_fold` (same-scene folds render silent,
  PORTALS.md); asymmetric in/out travel distance.
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

---

## Optional polish (no canon/lore change; do as time allows)

- **Rev. Asa Crane murder beat** *(GAME_CHANGES.md §12)* — the
  `preacher_doomed` -> gutted-on-the-floor reveal could be punched up for
  impact. Lore unchanged; not requested.
- **Held-weapon offset eyeball pass** *(HANDCRAFT_BACKLOG.md §3b)* — the
  `draw_axe_held` / `draw_revolver_held` code is in and working; this is just
  a visual check of the held-weapon offset at every camera yaw.
- **Permanently-visible King through an OPEN fold** *(KING_PROMPT.md portal
  pass)* — the King currently looms through the rift only while it *forms*,
  then steps through (intentional per `PORTALS.md`). A persistent silhouette
  on the far side of an already-open fold is not built; revisit only if the
  direction changes.

---

## Verified done (dropped from this list)

### 2026-07 build sweep (this branch; each flow/stealth-guarded)

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
