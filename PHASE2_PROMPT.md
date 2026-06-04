# PROMPT — THRESHOLD Phase 2 (continue in a new chat)

> Paste this into a fresh Claude Code session on the THRESHOLD repo. It is
> self-contained. Everything below is already merged to **`main`** — start
> from there.

You are continuing **THRESHOLD**, a narrative-horror game in pygame played
through an **oblique tilted camera** (~55° default; F3 drops to a flat pitch-0
view). Every sprite is procedural; there is no art pipeline. The story is the
point; the bible is the source of truth.

## FIRST THING YOU DO

**Before writing any code, read the docs below, then tell me what you plan to
do for Phase 2 — a concrete, prioritized plan — and wait for my go.** Give me
a real, opinionated plan (sequencing, what you'd do first and why, anything
you'd push back on), not a restatement of this file. Once I approve, execute.

## Read these first, in order

1. **`NARRATIVE.md`** — the narrative bible (authoritative canon). When code
   and it disagree, it wins.
2. **`GAME_CHANGES.md`** — the per-task code TODO (the Phase 2 remainder lives
   here). Verify the `file:line` pointers; they drift.
3. **`CLAUDE.md`** — dev commands, conventions, the "Working agreements."

## What is already DONE (do not redo)

Phase 1 is complete and merged, plus a large feel/voice pass this round:

- **Phase 1 canon alignment** — Ledger → the Lodge front desk; Sable the
  most-attuned local; Royce stopped; Mrs. Calder's unnameable guest; Toby's
  well-clue; Playscript → "The Cult's Notes" (reskin); the keystone-to-door
  rework (the Deep Stair opens *without* consuming the keystone, the Threshold
  seal *consumes* it); the awareness-model sweep.
- **Opening depth** — the lodge arrival is staged (Sable behind a real 3D
  counter you see over, the relocated Ledger lit as the centerpiece); a
  floor/wall **tile-detailing** pass (per-tile variation, grime, grass/dirt,
  battered wall faces under the tilt).
- **West-of-lodge geography** — a new **arrival road** west of the lodge: the
  road the PI drove in on, closed into a seamless infinite loop (you don't
  notice until your own dead car comes back around — a sensory car-tell). The
  **SPREAD car** moved onto it. The **woodshed is consolidated into the lodge
  yard** (key-gated by the cellar key); removed from brimley.
- **The PI's interior voice** — fires on what he EXAMINES, not on room entry.
  Diverse triggers (`Game._descent_voice` / `_DESCENT_VOICE`,
  `_try_chalk_interact`, `_fold_mentioned`): a recurring **chalk-door** motif
  (floor + wall; `Scene.add_chalk_door` / `scatter_chalk_doors`), the dig's
  catalogued lives, **every piece of evidence** carries his voice, and a
  **fold-talk** note (the first local to describe the looping roads, named).
- **This effectively completes GAME_CHANGES §8** (Mask = "permission to
  leave" + escalating distressed notes): the **Playscript seeds the
  want-to-leave** (the King's pull to carry the Sign OUT, felt only as the
  PI's own confident judgment), the **Mask** is the peak, the **Depths** the
  thwarted want. The lure-unease seed of §10 also exists (`the_case` note).
- **Style sweep** — no em-dashes in any player-facing writing.

## Phase 2 — what REMAINS

Treat `GAME_CHANGES.md` as the list, but note the state above (do **not**
re-author §8 — it's done; §10 is a standing constraint per iron rules 2-3, NOT
a task — the lure chain stays unstated, the lone `the_case` touch already
exists, never elaborate it). The genuinely open work:

- **Ashfall (§9)** — the one independent system left. A drifting pale-yellow
  ashfall scaling with `_infest_stage()`, denser near the source, **never on
  the Threshold**. Procedural; preview headlessly before committing.
- **Buried lore inside the cult's notes (§6b)** — the *contents* of the
  Playscript: fragmentary, longing, unreliable **testimony the game never
  confirms** (the dig, the bargain, the longing). The wrapper + the leave-urge
  exist; the deeper lore fragments do not. Surface them where the notes are
  read. Never the author's voice; never "dimension."
- **Rev. Asa Crane (§12)** — dialogue/murder rework. Lore unchanged. **Settle
  the new presentation with me before writing.**

### Smaller follow-ups the last session flagged (optional, your call)
- A **resist-side counterweight** at the Deep Stair fork so carrying the
  keystone DOWN (seal) reads as the harder, costlier road (a counterweight to
  the Mask's leave-pull).
- **Spread the chalk-door motif** to more empty rooms (only the Scriptorium is
  swarmed; `Scene.scatter_chalk_doors(count, seed, wall_count)` exists).
- A couple more **object-specific voice triggers** (the Cistern/river, the
  Scriptorium's signs) for even more distinct sources down the descent.

## Iron rules (do not break)

1. **Verify narrative against `NARRATIVE.md` BEFORE writing it.** Quote the
   bible's intended voice; don't invent canon.
2. **Never write "dimension"** or otherwise *explain* the door. Cosmic truth
   arrives **only as sensation**. The King is **powerful, not omniscient — He
   got lucky** (keep the seam of chance).
3. **The King's influence is invisible to the PI.** Where his mind is being
   turned (the want-to-leave), it must read as **his own judgment** — he never
   notices his thoughts changing. The player infers the King; the text never
   does.
4. **NO em-dashes (or `--`) in player-facing writing. Keep it human.** A
   `tests/flow.py` guard tokenizes every source file and fails on any
   non-docstring string containing `--`. Comments/docstrings are exempt.
5. **Voice/lure beats are `notes`, never `evidence`** — only the six
   `CANONICAL_EVIDENCE` beats may touch `save.arg("evidence")` (it drives the
   King-gate + infestation).
6. **Item + scene KEYS are load-bearing** (saves + logic). Only display names
   and fiction change.
7. **One edit at a time on a shifting file;** for multi-site changes write a
   small patch script with `assert count == 1` per replacement.
8. **Verify before every commit:** `python -m compileall systems entities
   scenes rendering ui .` then `python tests/smoke.py` then
   `python tests/flow.py` — all green. **Add a `tests/flow.py` guard whenever
   you lock a canon or style fact.** Headless env is the SDL dummy drivers
   (the session hook sets them).
9. **Commit in logical chunks** with clear messages; push the working branch.
   Open a PR / merge to main only when I ask.

## Tools / workflow notes

- See sprites/scenes headlessly: render to PNG with the SDL dummy drivers +
  Pillow and view them (the `pygame-to-png` / `sprite-preview` skills, or a
  one-off capture script booting `Game()` at the locked tilt). Always *look*
  at visual changes before committing.
- `GAME_CHANGES.md` is the canonical TODO; keep it pruned as you finish items.
</content>
