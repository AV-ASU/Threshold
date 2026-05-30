# Session status — journal door-dream → "He knows you"

Branch: `claude/game-state-verify-tcQKO`  ·  tip: **`e5c1da1`** (local == remote, tree clean)

## What's done & verified

### 1. The journal door-dream (NARRATIVE 1b) — wordless visual cutscene
Replaces the old three text stills. Fires when the player reads Mara's
journal through a third time (`flashback_pending` → `_tick_flashback`).
- Dried-wood **doorframe** suspended in black; **pulsing yellow glow** pooled
  at the **base of the doorway** (`FLASHBACK_FOCAL_Y`), contained by the frame
  (no leak past the wood).
- Faint **eyes peeking** in the light.
- A **mask swarm**: carved dark-wood faces flash all over the opening, starting
  slow ~2s in and **accelerating** to a staring crowd, then fading with the
  dream. Faces clip on the jamb; **gold pupils aim back at the player**
  (`door_mask_surface(gaze=…)`). Driven by `_spawn_flashback_masks` (rate ramp)
  + a pre-rendered pool (`_build_flashback_pool`).
- Audio: `falling_air` wind/fall bed on the ambient channel + a `wrong` stab
  as the faces begin.

### 2. "He knows you"
- `_log_dream_entry()` writes a **case-notebook NOTE** ("the_dream") in the
  PI's voice after the dream. Stored in save arg **`notes`**, deliberately NOT
  `evidence` — `_evidence_count()` is `len(evidence)` and drives the King-gate
  + infestation, so a flavor note must never land there. Idempotent.
- `NotebookUI` lists clues (evidence) then personal notes.
- Real **Threshold** (`scenes/depths.py build_threshold`): if the dream was seen
  (`flashback_seen`), one quiet line lands first — *"You have stood here before.
  In sleep."* — then the doorframe narration (chained via dialog `on_complete`).
  Never-dreamed path is unchanged.

## Verification (all green)
- `compileall` clean.
- `tests/smoke.py`: all pass.
- `tests/flow.py`: 51 ok, incl. all flashback + 6 new "heknows" checks.
- Full end-to-end arc test (read→dream→note→threshold) passes; re-entry
  idempotent; recognition only when dreamed.

## ⚠️ Pre-existing failures (NOT mine — left untouched)
`tests/flow.py` has 3 failures unrelated to this arc, present on the pre-arc
base (`7c15a0b`):
- `well: rope ties on first descent`
- `well: rope consumed into the rig`
- `kid: the Kid is present in his house`

## ⚠️ History note — needs your call
The mask-swarm work pushed **two broken commits** before the verified one
superseded them (both had a `NameError`; tip is correct & working):
- `9e62773`, `06b3b67` — "Journal dream: mask SWARM…" (broken intermediates)
- superseded by `90c701a` (verified) and later commits.
I did **not** rewrite/squash history (don't rewrite shared history without
your OK). If you want a clean history, say so and I'll interactive-rebase
those out.

## Open tuning knobs (visual/feel — your judgement)
- `FLASHBACK_RATE_MAX` (climax density), `FLASHBACK_SWARM_START/_PEAK` (timing),
  `FLASHBACK_MASK_FRAMES` (flicker), `FLASHBACK_FOCAL_Y` (focal height).
- Audio is synthesized to spec but I can't hear it — confirm the `falling_air`
  bed + `wrong` stab land by ear when you run it.

## Possible next steps (didn't start — need your direction)
- Squash the two broken commits (your call above).
- Any further narrative beats.
- A play-through pass once you can run it with a display.
