---
name: bug-hunt
description: Systematic, hypothesis-driven debugging for this codebase. Use whenever something misbehaves and the cause is not already known — a crash, a wrong behavior ("the King never spawns", "visibility sticks at 1.0", "the cultist walks through the wall"), a failing harness, or a visual glitch under the tilt. Prevents the classic failure of pattern-matching a symptom to a remembered cause and "fixing" the wrong thing.
---

# Bug hunt

Debugging is reasoning under uncertainty. The rule that governs
everything below: **never write the fix until you have watched the bug
happen under your own instrumentation.** A fix applied to a diagnosis
you inferred (rather than observed) has about even odds in a codebase
with this much cross-system coupling — visibility feeds the King, the
curse feeds visibility, infestation rebuilds scenes, scenes reset
hide-state — and a wrong fix here usually *masks* the symptom instead
of curing it.

## The loop

### 1. Reproduce headlessly first

Almost every bug in this game can be reproduced without a display:

```bash
export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=.
```

Write a minimal driver script in the scratchpad (NOT in the repo) that
boots `Game()`, loads the scene, sets the preconditions (evidence
count, visibility, curse state) directly on the save/game object, and
steps `game.step(dt)` in a loop while printing the state you care
about. `tests/flow.py` is the pattern to crib: it drives scene hooks
and interactions directly, no input simulation needed.

If you cannot reproduce it, you do not yet know what "it" is — narrow
the report (which scene? what evidence count? tilt or flat? cursed?)
before touching code.

### 2. Localize the layer before the line

Ask, in order, which layer owns the bug — each has a cheap test:

- **Scene build?** → `tests/smoke.py` builds every scene; run it, or
  build the one scene in isolation via `scenes.load_scene(key)`.
- **Simulation/update?** → your driver script with prints; the world
  simulates fully headless, and under tilt the *update* path is
  identical to flat (only rendering is gated).
- **Render only?** → if the state prints right but looks wrong, it's
  the draw layer (`systems/render_mixin.py`, `rendering/`). Use
  `tools/capture_world.py` or the sprite-preview skill to SEE it;
  for tilt-vs-flat suspicion, remember pitch 0 is byte-identical by
  contract — a diff there is itself a bug.
- **State bleed across runs/scenes?** → check the reset paths:
  `_reset_run_state` (New Game; the `Game` instance is REUSED across
  quit-to-title) and `load_scene_now` (clears `_king`, `_watchers`,
  hide-state — but `visibility` deliberately persists). Stale state
  from an incomplete reset is this project's signature bug class.

### 3. Hypothesize → predict → observe

State the hypothesis in one sentence with a *distinguishing
prediction*: "if X is the cause, then printing Y at Z will show W."
Then instrument exactly that and run. If the prediction fails, the
hypothesis is dead — do not rescue it with epicycles; form the next
one from what you actually saw. Keep a short written list of killed
hypotheses so you don't re-test them.

Binary-search tactics that work well here:

- Bisect time: print every frame, find the first bad frame, then dump
  full state at frame N-1 vs N.
- Bisect systems: stub a tick out (skip `_tick_king`, force
  `visibility = 0`) and see if the symptom survives.
- `git log -p -- <file>` / `git bisect` when it "used to work" — 137
  commits of small, well-messaged history make this cheap.

### 4. Explain the WHOLE symptom before fixing

The diagnosis must account for every observed detail, including the
weird ones ("...but why only in the grove?"). A leftover unexplained
detail usually means two interacting causes, and fixing one makes the
report mutate instead of close.

### 5. Fix at the cause, then prove it

- Fix where the invariant broke, not where the crash surfaced.
- Re-run your repro script: symptom gone.
- Run the full gate: `python tests/run_all.py` — the fix must not have
  moved the bug somewhere else.
- If the bug was a broken invariant worth keeping (a canon fact, a
  state-reset guarantee, a cap ordering), add a guard to
  `tests/flow.py` so it cannot silently regress. A bug that took real
  effort to find deserves a permanent tripwire.

## Anti-patterns

- **Pattern-match fix**: "this looks like the stale-hide bug, so I'll
  clear hide-state" — without reproducing first. The same symptom here
  routinely has different causes (see step 2's layer list).
- **Shotgun instrumentation**: printing everything everywhere instead
  of testing one prediction. You drown the signal.
- **Fixing in the dark**: editing game code as the *first* move. The
  first move is always a scratchpad repro.
- **Closing without a guard**: a subtle bug fixed with no test is a
  bug scheduled for re-entry.
