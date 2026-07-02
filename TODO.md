# THRESHOLD — TODO

> A live to-do list of work that is **genuinely still open**, built from a
> 2026-06 verification sweep of every TODO source in the repo
> (`GAME_CHANGES.md`, `NARRATIVE.md` §8, `KING_PROMPT.md`,
> `HANDCRAFT_BACKLOG.md`). Each candidate was checked against the actual
> code; **anything already implemented was dropped** (see "Verified done"
> at the bottom). Cross-check against `NARRATIVE.md` before writing prose,
> run the full gate (`python tests/run_all.py`) before commit, and add a
> `tests/flow.py` guard when a new note locks a canon fact.

---

## Open work

### 0. Stealth rework — MECHANIC DONE (2026-07); the placement pass remains

**The mechanic is built and guarded** (`tests/stealth.py`, in the full
gate): graded per-enemy suspicion (score = los x distance x facing cone x
concealment, `systems/stealth.py` + the `SUS_*` config block), the NOTICE
"?" tell before the lock, two cover classes (corn = mobile leaky
concealment a locked chaser can still grab you in; enclosed "under"/"in"
hides = rooted, sight-proof, CHECKABLE), searchers that sweep enclosed
hides around last-seen, and the timed mash **struggle** on a checked hide
(burst-out + stagger + a loud converge, or the CAPTURED death). Apex
pursuers stay exempt. Deferred to the human-tuning pass: the peek verb +
the exit-beat (see `STEALTH_REWORK.md` status note).

**The placement pass is DONE too (2026-07):** every gauntlet room now
carries at least one enclosed, checkable hide on walkable ground, placed
near the patrol routes per the §6 table (well_passage bay rack;
works_vats basin lee; works_sorting two table hides on the hardest
crossing; works_scriptorium centre desk; works_sign one risky pew spot;
depths_antechamber/procession crate hides; depths_hall nave pew; the
dead pickup on the Brimley surface). Flow-guarded (§25: every declared
hide sits on walkable ground). What remains of #0 is pure TUNING: the
numbers (`SUS_FILL_RATE`, concealment factors, the struggle window) only
prove out against a human player.

### ~~1. Food scarcity — the VISUAL pass~~ — DONE (2026-07)

All three beats landed, verified with headless tilt captures:

- **Bare store shelves**: the shop floor's two goods runs are now the
  `bare_shelf` FURNITURE kind (empty runs, dust-ghosts where stock stood,
  one tin left; flat art in `entities/decoration.py`, tilt detail
  `_d_bare_shelves`). The storeroom shelf stays stocked (Hettie's
  preserves; nobody buys). The regular `_d_shelves` detail gained book
  spines so stocked vs bare contrast under tilt.
- **Gardens on some lots and not others**: a new `garden_patch` floor
  decal (`tended=True/False`). The Tisdales keep a working April bed
  beside their house (turned rows, staked string, first cold-hardy
  shoots); the farmhouse plot has gone over (collapsed furrows, last
  year's stubble). Other lots never dug.
- **A cultist eating at a counter**: Hettie's shop counter is now real
  `counter` furniture (shows the new butcher detail), and from
  infestation stage 2 a convert stands at it eating from a tin bowl
  (`pose="eat"` in `sprites_cultist.py`, spawned by
  `_spawn_counter_eater` in `systems/infest_mixin.py` on the
  depths-digger ambient contract: idle, no tag, no gaze, no prompt).

### ~~2. Counter "butcher" detail at the oblique angle~~ — DONE (2026-07)

`_d_counter` added in `rendering/furniture.py` and wired into the FURNITURE
spec: butcher-block plank seams, a worn pale lip, knife scores, and one old
dark stain with a drip on the near face. Verified under tilt.

---

## Design review findings (2026-06 critique pass)

> From a critical review of gamification + story (two independent passes).
> Ranked by impact; the top two were flagged by **both** passes. These are
> bigger than the polish items above. Some are arguably intentional dread-first
> design (minimal combat, oblique storytelling) — flagged as judgment calls,
> not bugs. Decide scope before building; none are settled like the stealth
> rework yet.

### 5. Onboarding / guidance gap  *(highest impact, both passes)*

The game is hostile to a player who has not read `NARRATIVE.md`. No objective
system, no tutorial, no map/waypoints; the notebook records what you *found*,
not what to do next. The only in-game mechanic taught is the axe stun
(`systems/game.py`); hiding, the visibility meter, limited ammo, and the
curse are never explained. A first-timer spawns in the bedroom with no idea
what the game is or where to go. Fix candidates: an opening framing beat, a
light "objectives/leads" view in the notebook (`ui/notebook_ui.py`), and a
couple of proactive teach-moments instead of fail-state-only teaching.

### 6. Mara's arc is undelivered  *(highest impact, story pass)*

The case is "find Mara," but the player never learns her *ache* (what the door
answered) — she is a name, a journal, a cell, and a kneeling mass with one
good final line. The tragedy the bible promises ("not deceived, answered")
never lands, and the case evaporates after Act 1. Fix candidates: an unsent
letter in her cell that names what she fled; one local who knew her; the
door-dream showing *her* at the frame; evidence #6 as a short exchange, not a
single line. Hold the §1b/§10 fence (no cosmology stated). Add a flow guard.

### 7. The lure chain is invisible in-play  *(story pass)*

The deepest plot — the PI was marked a year ago and *sent* to Brimley — lives
only in `NARRATIVE.md` and three scattered notebook notes (`the_case`,
`the_dream`), never connected for a play-only player, so the ending feels
arbitrary. Fix candidate: ONE oblique moment (near the Threshold, or on
learning of Mara) that links the dream + the case + Mara's presence — felt,
never explained (this brushes the §10 fence; keep it a sensation, not a
reveal).

### 8. The descent midgame — narrative half CLOSED (2026-07); one wrinkle open

A 2026-07 re-verification found the "~3 beats" claim stale: the 2026-06
descent rework had already landed an interior-voice arc (descent_dig /
descent_leave / descent_mask, chalk beats), three cult testimonies, and
per-room flavor (works_vats_seen, effects_pile, the_fall,
threshing_floor). The genuinely-missing beats are now in: the
**procession candle line** (wax on old wax, a NOTE, never evidence), the
**kneeler-wake line** in depths_hall ("Not startled. Called."), and the
**rite-holder's weight** (a one-shot trigger in the works_sign apse).
depths_stair stays deliberately empty ("silence is the keeper"). The
stealth placement pass (#0) closed the mechanical-monotony half for
cover; **still open: ONE mechanical wrinkle in the deep** — best
candidate now that the noise model exists: deep-water wade (slow +
splash noise on the dressed '~' tiles in works_vats/the_sump/
depths_threshing), or a listener-cultist variant built on the suspicion
model. Decide the fiction before building.

### 9. Ending fork is not legible  *(story pass)*

SEAL vs SPREAD are mechanically distinct but the player often will not grasp
what either *means*, or even that carrying the Mask up is an escape. No beat
states the stakes before the commit, so neither ending reads as won or lost.
Fix candidate: a clarifying sensation/voice beat at the fork (still no
cosmology spelled out), and an ending-text pass so each lands a clear feeling.

### ~~10. The town does not react to state~~ — DONE (2026-07)

Each ambient local now carries ONE pre-mutation state beat (a one-shot
via the `beats` hook on `_brimley_voice`, fired before their ambient
loop and before the infestation convert/mutate swap overwrites them):
**Garrick** clocks the pulpit going silent (preacher_doomed — the direct
murder reaction, and a lead to the church), **Old Pell** reads the
digging on the PI like coal dust (evidence 1), **Mrs. Calder** starts
leaving the door unlatched (evidence 1, inside her pre-convert window),
**Royce** works out that a road that only opens one way is a throat
(evidence 2). All flow-guarded (§24: one-shot, gated, never evidence,
no-dash, no-cosmology). `escalate()` was confirmed inert (both call
sites pass identical tiers) — kept but documented as such; the false
module docstring in `scenes/dialogue.py` is fixed.

### 11. Combat / difficulty — judgment calls (decide on purpose)

Not bugs; deliberate choices worth confirming rather than leaving by default:
the gun goes **stun-only at 3 evidence** with ~14 rounds total per run, so the
main combat verb is removed exactly when danger spikes (agency loss vs
intended dread). There are **no difficulty options**, so the visibility/Watcher
death-spiral hits newcomers and is trivial to experts. Items are gates, not
resources (armor slots return 0). Consider: transforming the stun into a
tactical window rather than a tax, an easy/hard toggle, or light resource
tension — only if it serves the horror, not despite it.

---

## Design calls (decide before building)

### ~~3. `drowned_body` — does it stay?~~ — DECIDED: CUT (2026-07)

The maintainer called it: cut. The `well_bottom` placement, the
`_draw_drowned_body` draw fn, and the `_FLOOR_DECAL_KINDS` entry are
removed; the seep pool and claw gouges carry the room's dread.

### 4. The liminal-composition pass  *(NARRATIVE.md §8/§10)*

Per-scene level-design polish: composed emptiness, long sightlines, uncanny
repetition. Inherently ongoing/iterative rather than a single shippable
ticket — scope a concrete first scene before starting.

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

## Verified done (dropped from this list, 2026-06 sweep)

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
  `_d_mattress`, `_d_shelves`, `_d_logs` exist and are wired in (only the
  `counter` detail above remains).
