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
