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

### 0. Stealth rework — hiding mechanic + enemy/hide placement pass  *(see `STEALTH_REWORK.md`)*

The biggest planned change. Hiding today is a binary `player.hidden`
invisibility toggle: it is not tense (wait out a 6 s timer) and "inside"
something is too powerful (an enemy can stand next to your hide and never
find you). The agreed direction is **"concealment, not invisibility"** —
graded per-enemy suspicion, two cover classes (mobile/leaky vs
rooted/strong/checkable), searchers that sweep hides, and a timed **struggle**
when a searcher checks the enclosed hide you are in. Plus a placement pass
(the gauntlet is 17 cultists with 0 dedicated hides today). **Design is
settled and written up in `STEALTH_REWORK.md`; no code yet.** Build mechanic
first, then the placement pass.

### 1. Food scarcity — the VISUAL pass  *(NARRATIVE.md §8)*

The dialogue side is done (Hettie: "The shelves don't empty anymore... No
deliveries."; the Store-Owner: "Shelves are bare. Till's been empty since the
new year"). What's left is the **world art**, none of which exists yet:

- Visibly **bare store shelves** in the shop.
- **Gardens on some lots and not others** (the town feeding itself unevenly).
- A **cultist eating at a counter**.

Wallpaper, not a mechanic. Render under the oblique tilt (see
`HANDCRAFT_BACKLOG.md` for the volume/standee/decal mechanism map).

### 2. Counter "butcher" detail at the oblique angle  *(HANDCRAFT_BACKLOG.md §4)*

The `counter` FURNITURE kind is spec'd with **no detail function**
(`rendering/furniture.py`: `"counter": (..., None)`), so it reads as a plain
box under the tilt. The companion details (`fireplace`/`stove` firebox, `bed`
blanket folds, `shelf` book layout) already exist; the counter is the one
straggler. Add a `_d_*` detail hook and wire it into the FURNITURE spec.
Pairs naturally with the "cultist eating at a counter" beat above.

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

### 8. The descent midgame is hollow (both axes)  *(both passes)*

The Works (7 rooms) + Depths (5 rooms) are the longest stretch and the
emptiest. Mechanically: the same walk/hide/evade loop with no new threats,
hazards, or escalation across ~12 rooms. Narratively: ~3 plot beats total,
cultists never speak, rooms do not change as infestation rises. Fix
candidates: one diegetic beat per room (a shed-life object in the Sorting
Hall, a line at the Cistern/river, the rite-holder's weight), and a mechanical
wrinkle or two in the deep (a hazard, an enemy variant). Pairs with the
stealth placement pass (#0).

### 9. Ending fork is not legible  *(story pass)*

SEAL vs SPREAD are mechanically distinct but the player often will not grasp
what either *means*, or even that carrying the Mask up is an escape. No beat
states the stakes before the commit, so neither ending reads as won or lost.
Fix candidate: a clarifying sensation/voice beat at the fork (still no
cosmology spelled out), and an ending-text pass so each lands a clear feeling.

### 10. The town does not react to state  *(story pass, medium)*

Ambient locals (Royce, Old Pell, Calder, Garrick) speak once and never react
to the preacher's murder, rising infestation, or evidence count. The
`escalate()` system (`scenes/dialogue.py`) exists but is barely used. Fix
candidate: one state-dependent beat per named local so the town visibly
changes as the player learns more.

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

### 3. `drowned_body` — does it stay?  *(HANDCRAFT_BACKLOG.md "Genuinely open")*

The art is mechanically correct (a floor decal in the water plane) and a
submerged-read rework was already attempted and **rejected** (2026-06). The
remaining question is purely a **design decision**: keep the prop or cut it.
Not a code task until that call is made.

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
