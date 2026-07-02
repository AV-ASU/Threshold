---
name: tuning-brain
description: Reasoning aid for changing the threat-model tuning — any VIS_* / KING_* / WATCHER_* / FOLD_* / LOCAL_KILL_* constant, or the logic in _tick_visibility / _tick_king / _tick_watchers. Use when a change touches how fast the player is seen, when the King spawns, how survivable the curse is, or difficulty in general (e.g. "make the corn safer", "the King spawns too fast", "buff the watchers", "hiding drains too slow"). The constants form a lattice of invariants; this skill is how to change one without silently breaking the game's survivability contract.
---

# Tuning brain

The threat constants are not independent knobs. They form a small
economy — rise rates vs decay rates vs floors vs the 1.0 King line —
and the game's core promise ("dread that is always survivable by a
player who uses cover") lives in the *relationships*, not the values.
Change a number in isolation and you can make the game unwinnable
without any test failing loudly.

Tuning lives in `systems/config.py`; the consuming logic is
`systems/threat_mixin.py` (and `systems/king_roam_mixin.py` for the
roaming King). Read the actual current values before reasoning — do
not trust remembered ones.

## The invariant lattice (check every one your change touches)

1. **All floors stay under the King line.** `visibility >= 1.0` spawns
   the King, so every *passive* floor must cap below it:
   `VIS_FLOOR_TOTAL_CAP` (0.92, the summed Watcher floor) < 1.0, and
   `LOCAL_KILL_VIS_CAP` (0.96) < 1.0. If a floor can reach 1.0, the
   player can be locked into a guaranteed King with no counterplay —
   the curse stops being survivable and becomes a death sentence.
2. **The Watcher floor must sum safely.** `WATCHER_MAX` ×
   `WATCHER_FLOOR` (5 × 0.12 = 0.60) is the uncapped sum; the cap does
   the real guarding, but if you raise either factor, re-check the
   *time to clear*: `WATCHER_MAX` × `WATCHER_GAZE_DISPEL` seconds of
   standing still and staring, under a raised floor, must be a tense
   task, not an impossible one.
3. **Escape must outrun exposure.** The point of cover: hiding bleed
   (`VIS_HIDE_BLEED` 0.10/s) must be meaningfully faster than idle
   decay (`VIS_IDLE_DECAY` 0.02/s), and gaze rise (`VIS_GAZE` 0.12/s
   per cultist, `KING_GAZE_RISE` 0.45/s for the King) must beat both —
   the meter should fill under eyes, drain in cover, and barely move
   idle. If a rise rate drops below the hide bleed, being seen stops
   mattering; if bleed drops below a floor's practical level, cover
   stops mattering.
4. **The dissolve gap is the mercy window.** The King spawns at 1.0
   and dissolves below 0.90. That 0.10 hysteresis is what makes an
   encounter recoverable (hide, bleed 0.10/s, ~1 second per 0.10).
   Narrow the gap or slow the bleed and every spawn becomes a death.
5. **Birth is the grace period.** He catches at `KING_CATCH_DIST`
   (24 px) only once `_birth >= 1.0` (~1.2 s eruption, during which he
   cannot move). He spawns at the player's scene-ENTRY anchor, so the
   grace assumes the player has moved off it; anything that spawns him
   nearer the player must respect the birth gate.
6. **Gates hold their order.** `KING_GATE_EVIDENCE` (3) is also the
   infestation peak (`min(3, evidence)`) and the gun's kill→stun
   threshold. These are deliberately the same beat: the world turns
   hostile all at once as the player commits. Moving one without the
   others desynchronizes the act structure.
7. **Scene exemptions are canon.** `SAFE_SCENES` never host the King
   and only *suppress* (not cure) Watchers; apex pursuers
   (`_force_chase`: King, hollow Sheriff) never lose LOS. Tuning must
   not create a loophole where an exemption becomes a cheese (e.g. a
   safe room adjacent to a spawn anchor with a too-slow bleed).

## The method

1. **State the intent as an experience, not a number.** "The corn
   should feel safe for ~8 seconds under one cultist's gaze" — then
   derive the number (0.12/s gaze ⇒ ~0.96 in 8 s ⇒ works only from a
   low meter, etc.). A number without an experience attached cannot be
   judged.
2. **Walk the lattice** above and write down which invariants the
   change touches and why each still holds.
3. **Simulate before shipping.** The whole threat model runs headless.
   Write a scratchpad script that boots `Game()`, forces the scenario
   (N cultists with LOS, cursed with K watchers, hidden/exposed), steps
   `step(dt)`, and prints `visibility` per second. Check the derived
   quantities: time-to-King under sustained gaze, time-to-recover in
   cover, time-to-clear a full curse. Compare before/after values in
   your report — those numbers ARE the review.
4. **Gate it.** `python tests/run_all.py` (flow.py asserts the spine
   is completable; king_roam and fold_pursuit exercise the pursuit
   math). If your change establishes a new relationship worth keeping
   (a new cap, a new ordering), add a flow guard that asserts the
   *relationship* (e.g. `CAP < 1.0`), not the raw value — values are
   allowed to move, orderings are not.
5. **Respect the design's direction.** This game tunes toward dread,
   not fairness-by-spreadsheet: the King is meant to be lucky
   (`KING_HOP_TOWARD` 0.55) and relentless, and per TODO.md §11 the
   difficulty cliffs are *judgment calls to confirm with the user*,
   not bugs to quietly sand down. If a tuning request would flatten
   the dread (e.g. "make the King fair"), surface the trade-off
   instead of just complying.
