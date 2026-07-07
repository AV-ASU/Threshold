# THRESHOLD — STEALTH REWORK (design doc)

> **Status: MECHANIC BUILT (2026-07), placement pass (§6) DONE, and the
> 2026-07 continuation landed.** Pillars 1-3 + the struggle (§4) + the
> visibility model (§5) are in code and guarded end-to-end by
> `tests/stealth.py` (wired into the full gate). The scoring lives in
> `systems/stealth.py` (one source for both cult machines), tuning in
> the `SUS_*`/`STRUGGLE_*` blocks of `systems/config.py`. The
> continuation added Pillar 2A's **shadow cover** (darkness is leaky
> concealment: `SUS_CONCEAL_DARK` for an unlit player in a DARK scene
> outside every light pool, `Scene.lit_at` / `Game._tick_dark_cover`)
> and the formerly deferred **exit-takes-a-beat** window
> (`HIDE_EXIT_BEAT`: leaving an enclosed hide roots you for a beat,
> visible, before you can move -- bolting is a commitment). One
> deliberate deferral remains, a tuning-pass item: the Pillar-2 **peek**
> verb (free look under tilt already gives the information function).
> §1 below describes the REPLACED system, kept as the design record.
> Settled with the user 2026-06; built mechanic-first as planned.
>
> **Why:** two complaints with the current model — (1) it is **not tense or
> engaging** (hiding is a safe pause button; you wait out a timer), and (2)
> being **"inside" something feels too powerful** (total invisibility; an
> enemy can stand next to the bed you are under and never find you).
>
> Cross-check `NARRATIVE.md` before writing player-facing text, keep the
> no-dash rule, run the full gate (`python tests/run_all.py`) before commit,
> and add `tests/flow.py` guards as the new rules lock.

---

## 1. How hiding works today (the thing we are replacing)

The whole system hinges on one binary flag, `player.hidden`:

- Set it by stepping onto a corn tile (floor char `:`, auto-sets
  `hidden = "corn"`) or pressing **E** within 36 px of a hide spot
  (`hidden = "under"` / `"in"`, teleports the player onto the spot).
- While `player.hidden is not None`, detection is **unconditionally off**:
  - `has_los` returns `False` regardless of distance or facing
    (`entities/npc.py` surface chasers, `entities/enemy.py` underground).
  - The gaze term in `_tick_visibility` cannot raise visibility
    (`systems/threat_mixin.py`); only a lit flashlight leaks
    (`VIS_LIT_RISE`).
  - `visibility` drains at `VIS_HIDE_BLEED` (0.10/s).
- Cultists that lose line of sight demote to **SEARCH**, walk to the
  last-seen position, mill randomly within ~80 px for **6.0 s**, then revert
  to **SCOUT**. They never check the hide.

**Current constants** (`systems/config.py` unless noted):

| Constant | Value | Meaning |
|---|---|---|
| `VIS_GAZE` | 0.12/s | per cultist with clear LOS, visibility rise |
| `VIS_HIDE_BLEED` | 0.10/s | drain while `hidden` |
| `VIS_IDLE_DECAY` | 0.02/s | drain in the open, no gaze/light |
| `VIS_LIT_RISE` | 0.045/s | lit flashlight in the dark (leaks even in cover) |
| gaze / chase range | 180 px | LOS detection radius (npc); enemy uses `aggro` ~140 px |
| SEARCH duration | 6.0 s | mill at last-seen before giving up |
| INVESTIGATE duration | 4.0 s | mill at a noise source before giving up |
| mill radius | ~80 px | wander radius during SEARCH/INVESTIGATE |
| hide-spot pickup radius | 36 px | E-press range to enter a hide |

**Hide-spot data shape:** `scene.hide_spots = [(x_px, y_px, kind), ...]`,
`kind` one of `"under"` / `"in"` / `"behind"`. Consumed in `systems/game.py`
(the E-press block + the movement-breaks-hide block + the corn floor-tile
block). Apex pursuers (`_force_chase`: King via `_yk_update`, hollow Sheriff)
ignore `hidden` entirely and never lose sight — **this stays true** (the
rework is anti-cultist stealth; apex threats remain unbeatable by hiding).

---

## 2. Design goals

1. **Cover changes how hard you are to detect, never whether you can be.**
   No more binary invisibility. This is the single load-bearing idea.
2. **"Inside" is powerful against distant threats but a trap up close.**
   Invert the current feel: the safest place at range becomes the scariest
   place when a searcher is closing.
3. **There is always a decision after you hide.** Peek, hold, or bolt — never
   "wait out a timer."
4. **Keep what already works:** real line-of-sight as the primary tell, the
   SEARCH/SCOUT loop, SAFE_SCENES as the one true refuge, the apex exemption.
5. **Reuse existing systems:** the sight cone (`sight.py`), the being-seen
   HUD (the suspicion read has a home there), the cult state machine.

---

## 3. The mechanic — three pillars

### Pillar 1 — Detection is GRADED (suspicion), not binary

Replace the instant `has_los && !hidden` lock with a per-enemy **suspicion**
value in [0, 1] that fills from a per-tick **detection score**:

```
score = los_clear(0 or 1)
      * distance_falloff(d)        # 1 near, 0 at gaze range
      * facing_factor(aim, d)      # reuse the sight cone in sight.py
      * concealment_factor(player) # 1 open, < 1 in cover
```

- **No clear LOS** (a wall/solid prop between enemy and player) → score 0.
  Cover as a hard sightline break stays exactly as fair as it is now.
- **Clear LOS, open ground** → `concealment_factor = 1.0`, suspicion fills
  fast (≈ today's instant feel, but with a brief telegraph window).
- **Clear LOS, in concealment cover (corn/shadow)** → `concealment_factor`
  small (≈0.2-0.35) AND distance_falloff bites hard, so far away you are
  effectively invisible, but an enemy a few feet away still fills suspicion.
  This kills the "sit in cover right next to a cultist" exploit.

**State transitions keyed to suspicion:**
- suspicion crosses `SUS_NOTICE` (≈0.5) → enemy turns toward you, slows,
  shows a rising "?" tell (SCOUT stays, but it is now alert).
- suspicion reaches `SUS_LOCK` (1.0) → **CHASE** (the hard lock we have now;
  fires the existing `cult_lock` audio).
- score 0 for a beat → suspicion decays at `SUS_DECAY`; if it was high, the
  enemy drops to **SEARCH** at the last-seen position (existing behaviour).

This adds the classic stealth "have they spotted me yet?" window the current
model skips entirely. New constants live in a `SUS_*` block in
`systems/config.py`; the fill/decay runs in the cult tick
(`entities/npc.py _cult_tick` + `entities/enemy.py`), reading
`concealment_factor` from a new helper on the player/scene.

### Pillar 2 — Two cover classes with opposite trade-offs

Today every hide is the same blackout. Split them:

**A. Concealment cover (mobile, leaky) — corn, shadow, behind low props.**
- You can **keep moving** through it (crouch-move).
- Breaks/!weakens LOS at range; a close enemy with LOS still builds suspicion
  (Pillar 1). You cannot camp it next to a searcher.
- Moving fast (running) rustles → a **noise event** (Pillar 3).
- Replaces the corn auto-`hidden` blackout with a `concealment_factor < 1`.

**B. Enclosed hide (rooted, strong, a trap) — under bed, closet, locker,
wardrobe, "in".**
- A hard LOS break vs enemies that do not come check it — **strong** at range.
- You are **rooted**: no movement while inside; exiting takes a beat and you
  are vulnerable during it.
- A **searching enemy that reaches the hide tile checks it** (looks under /
  opens the door). If you are inside → the **struggle** (below). This is the
  inversion: powerful far away, lethal when a searcher closes.
- You can **peek** (a key) to watch the approach and decide to bolt early; a
  peek raises your detection score slightly (risk for information).

### Pillar 3 — Searchers hunt, and you make noise

- **SEARCH sweeps cover.** Instead of milling randomly for 6 s, a searching
  enemy paths to and **checks nearby enclosed hides** and looks into nearby
  concealment cover around the last-seen position. The 6 s budget is spent
  hunting, not wandering. (Builds on the existing nav grid
  `Scene.nav_path`/`nav_toward`.)
- **Noise events.** Running, bursting out of a hide, and knocking a prop emit
  a noise event (reuse the existing loud-step → INVESTIGATE channel). Noise
  pulls searchers toward you — moving carelessly while hidden gets you found.
- **Peek** from an enclosed hide: see enemy positions/facing, at a small
  exposure cost. The active-tension verb.

---

## 4. Getting caught — the timed struggle (chosen)

When a searcher checks the enclosed hide you are in, it is **not** an instant
death and **not** a free escape. A brief **struggle** decides it:

- A short window opens (≈1.2-1.8 s) with a clear on-screen prompt to mash /
  press a key.
- **Win the mash** → you **burst out** (panic ejection): a one-time short
  **sprint** burst, the enemy is staggered for a beat, and a loud noise event
  fires (every searcher nearby now converges — you won the moment, not the
  room). This is the "tense survivable" outcome.
- **Lose / ignore** → you are **grabbed** → the normal cultist capture death
  (`_trigger_death("cultist")`, the CAPTURED card).
- The struggle is **only** reachable from an enclosed hide that gets checked;
  concealment cover never triggers it (you are mobile there — getting found in
  corn just resumes CHASE).

Implementation notes: a small struggle sub-state on the Game loop (freezes
movement, draws the prompt, counts mash presses vs a threshold), gated behind
the searcher reaching the hide tile while `player.hidden` is the enclosed
kind. Tune the press threshold so a ready player usually escapes and a
caught-flat-footed player usually does not.

---

## 5. Visibility model under the rework

`_tick_visibility` (`systems/threat_mixin.py`) changes from a binary
hidden/not-hidden branch to reading **concealment**:

- Open ground: unchanged (gaze sum × `VIS_GAZE`, minus idle decay).
- Concealment cover: gaze contribution scaled by `concealment_factor`
  (leaky, not zero) — so a distant cultist barely raises you, a near one
  still does.
- Enclosed hide (not yet checked): gaze contribution ≈ 0 (the strong break),
  but the flashlight leak (`VIS_LIT_RISE`) still applies, and the **check**
  is the real threat, not visibility.
- The evidence/Watcher **floor** is unchanged (`_vis_floor`,
  `WATCHER_FLOOR`, `VIS_FLOOR_TOTAL_CAP`) — hiding still cannot drop you below
  the floor, and SAFE_SCENES remain the only true refuge.
- Surface this through the **already-built being-seen HUD**: the per-enemy
  suspicion is the natural "rate" read (a rising "?" per enemy), with the
  visibility meter staying the accumulated "state". (See the verified-done
  being-seen HUD in `TODO.md`.)

---

## 6. The placement pass (enemy + hide audit)

From the scene inventory, the gauntlet is **17 cultists across the Works +
Depths with 0 dedicated hide spots** — intentionally exposed under the old
model, but with the rework it needs a deliberate cover rhythm. The 4 existing
hides are cosmetic "under" spots in zero-threat rooms.

**Principles for the pass:**
- Place enclosed hides **near patrol routes**, not in safe corners — they
  should be a *risky option* (a searcher might check it), not a panic room.
- Give each combat room a legible **cover rhythm**: sightline → cover →
  sightline, so a player can read a route. No more open boxes.
- Pair concealment cover (corn, pillars, racks, pews) along the long
  crossings so breaking LOS is always *possible* but never *free*.
- Keep SAFE_SCENES as refuges (their hides stay cosmetic / no searchers).
- Respect the camera: hides must read under the oblique tilt (volumes /
  standees / decals per the tilt dispatch map in `CLAUDE.md`), not flat stickers.

**Per-area first cut (to refine during the mechanic build):**

| Area | Today | Proposed |
|---|---|---|
| **well_passage** | 1 cultist, 0 hides | rack-maze already = concealment cover; add 1 enclosed hide off the patrol loop |
| **works_vats** (Cistern) | 2 cultists, 0 hides | wet-stone pillars as cover; 1 enclosed hide (a dry alcove) a searcher can sweep |
| **works_sorting** | 2 cultists, 0 hides ("hardest crossing") | the catalogued effects = crates/wardrobes → 1-2 enclosed hides among cover lanes |
| **works_scriptorium** | 1 oblivious scribe | desks as cover; 1 under-desk enclosed hide (echo the safe-room "under" but now checkable) |
| **works_sign** | 4 cultists (3 oblivious) | altar pillars as cover; the threat is the patrol, keep hides sparse + risky |
| **depths_antechamber → hall** | 1-3 cultists, 0 hides | cut-stone alcoves + columns as cover; 1 enclosed hide per room, near a route |
| **Surface (Brimley, forest, graveyard)** | roaming cultists, corn/trees only | corn/shadow concealment is the system; add a couple of enclosed hides (a shed, a cellar nook) as set-piece options |
| **SAFE_SCENES (house, son_room, bedroom)** | 3 cosmetic "under" hides | leave cosmetic; no searchers ever check them |

---

## 7. Build sequencing

**Mechanic first, then the placement pass** (matches the project's own advice
in NARRATIVE §3 / the roaming-King design: validate the room-to-room hunt loop
before scaling it):

1. **Concealment model + suspicion** (Pillar 1) on one or two rooms; confirm
   the "spotted-yet?" window feels fair. Retire the binary `hidden` blackout.
2. **Two cover classes** (Pillar 2): concealment vs enclosed; rooted hides.
3. **The struggle** (§4): searcher checks enclosed hide → timed mash.
4. **Searchers sweep + noise** (Pillar 3).
5. **HUD surfacing** of per-enemy suspicion (reuse being-seen HUD).
6. **The full placement pass** (§6) once the loop feels right with a human
   playing it.

---

## 8. Risks / open questions (raise before coding)

- **This touches the most-tested code** (`threat_mixin`, the cult AI in
  `npc.py`/`enemy.py`, and the chase-through-folds path
  `_note_fold_pursuit`/`_tick_fold_pursuit`). Budget for re-greening
  `tests/flow.py` §20/§21 and the `fold_pursuit` harness.
- **Tuning is the make-or-break and only proves out against a human player**
  (per NARRATIVE §3): the suspicion fill curve, the concealment factors,
  the struggle press-threshold. Expect a play-tuning loop, not one-shot
  numbers.
- **Fairness:** a death from a checked hide must read as a *choice* (you hid
  too close / too late), never as jank. Telegraph the searcher's approach and
  always give the peek/bolt option first.
- **Legibility:** the player must be able to tell concealment from enclosed,
  and "they are checking my hide" must be unmistakable.
- **Apex unchanged:** King + hollow Sheriff (`_force_chase`) still ignore all
  of this. Confirm no regression in `king_roam`.
- **Flow guards to add:** binary-invisibility is gone; enclosed hides are
  checkable; concealment leaks at close range; the struggle resolves to
  burst-out or capture; SAFE_SCENES never spawn searchers that check hides.

---

## 9. One-line summary

Hiding stops being an invisibility toggle and becomes a positional gamble:
cover lowers how detectable you are, distant enclosure is strong, a searcher
closing on your hiding place is terrifying, and getting caught in one is a
struggle you can still fight out of.
