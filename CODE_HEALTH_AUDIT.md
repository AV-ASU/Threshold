# THRESHOLD — Code health audit (2026-07-10)

A full-repo health pass: baseline verification, structural cross-checks,
dead-code and hygiene sweeps, test-gate economics, and doc-drift spot checks.
Audit only — no behavior was changed. Every finding below was verified
against the code (grep/AST/runtime), not inferred.

**Baseline:** 118 Python files, ~54,200 lines. `python -m compileall` clean.
All six harnesses pass individually (smoke, flow, stealth, fold_pursuit,
king_roam, render_smoke). Overall the codebase is in notably good shape for
its size: the scene registry, config gating sets, and exit graph are fully
consistent; the sanctioned conventions (no dashes in player-facing text,
single-source stealth detection, atomic save writes, procedural-only art)
all hold up under verification.

---

## What was verified healthy

- **Scene graph integrity.** All 44 registered scenes build headlessly.
  Every one of the 17 `*_SCENES` gating sets in `systems/config.py` refers
  only to registered scenes. Every `add_exit` target resolves to a real
  scene AND a real spawn id in that scene. The two scenes never named by a
  static exit (`woodshed`, `depths_antechamber`) are reached by scripted
  paths (the key-gated shed door; the one-way blast fall), not orphaned.
- **The no-dash HARD RULE holds.** Every em-dash/en-dash/`--` hit in `.py`
  files is a comment or docstring; no player-facing string violates it.
- **Single-source stealth.** Both cult machines (`entities/npc.py`,
  `entities/enemy.py`) import `detection_score` / `update_suspicion` /
  `hear_noise` from `systems/stealth.py` as documented; no duplicated
  detection math has crept back in.
- **The infested-overlay cut is complete.** No `draw_infested_overlay` /
  `_draw_infested_portrait` / `infested=` leftovers outside
  `sprites_infested.py`'s kept `_gold_in_wound`; `tests/flow.py` guards it.
- **Save slot.** `systems/save.py` writes via `tempfile.mkstemp` +
  `os.replace` — genuinely atomic.
- **Exception hygiene.** Zero bare `except:` clauses repo-wide. 59
  `except Exception` handlers, almost all narrow and deliberate; only ~14
  swallow silently (see L4).
- **No mutable default arguments** anywhere in game packages.
- **Repo hygiene.** No binaries, captures, or `.pyc` tracked; `.gitignore`
  covers preview outputs; only source + docs + CI config in the tree.
- **`rendering/sprites.py` facade.** Imports resolve; nothing outside
  `rendering/` bypasses it to reach the `sprites_*` siblings.

---

## High findings

### H1. The test gate spends ~9 of its ~15 minutes re-synthesizing identical audio

`Game.__init__` (`systems/game.py:103`) constructs a fresh `Audio()`, and
`Audio.__init__` (`systems/audio.py:19`) synthesizes the entire 77-cue
procedural SFX/music library from scratch every time: measured **5.2–6.7 s
per construction** in this container. The harnesses build many games:

| harness       | `new_game()` calls | audio-synthesis cost |
|---------------|--------------------|----------------------|
| flow.py       | 69                 | ~6.5 min             |
| stealth.py    | 26                 | ~2.4 min             |

Measured wall-clock: `flow.py` ≈ 7 min, the full `tests/run_all.py` gate
≈ 15 min in a headless container — dominated by rebuilding a deterministic
sound library 95+ times. The synthesis output depends on nothing per-run,
so a module-level cache (synthesize once per process, share the built
`sfx` dict across `Audio` instances) would cut the gate to roughly a third
with zero behavior change in the shipped game (a single `Game()` per
launch). This is the single highest-leverage improvement available: it
directly enables H2.

### H2. CI does not run the canon guards or the stealth/threat harnesses

`.github/workflows/ci.yml` runs only `tests/smoke.py` and
`tests/render_smoke.py`. `flow.py` (the story-beat integration + canon
guards), `stealth.py`, `fold_pursuit.py`, and `king_roam.py` are enforced
only by local discipline — which CLAUDE.md itself records failing twice
(a `NameError` pushed to main). The likely reason they're excluded is
their runtime (H1). Once the audio cache lands, adding
`python tests/run_all.py` to CI becomes practical (~5 min/job) and closes
the gap between "the gate exists" and "the gate is enforced."

---

## Medium findings

### M1. The live King renderer's per-run state is never reset by the game

`rendering/king_unfold.py:74` (`_MASK_SURF`) says "Reset per run like the
other King fx state," and `reset_king_unfold_fx()` (line 71) exists for
exactly that — but its only callers are in `tools/preview_king_unfold.py`.
The game resets only the **fallback** renderer's state (`reset_king_fx`
from `sprites_king.py`) at all three reset sites (`systems/game.py:483`,
`systems/game.py:753`, `systems/threat_mixin.py:770`). Since `KING_UNFOLD`
is the default, the shipped renderer's mask-bond state (`host`, `em`,
`vf`, `lt`) leaks across scene loads, King despawns, and New Game. Impact
is cosmetic (the mask can start a fresh run already bonded/emerged, and a
stale `lt` timestamp briefly distorts the emergence dt), but the code
contradicts its own contract; the fix is one call beside each existing
`reset_king_fx()`.

### M2. Test processes silently ignore SIGTERM (SDL swallows it)

SDL installs a SIGTERM handler that converts the signal into a quit event,
so `timeout N python tests/flow.py` does NOT stop the harness: it runs to
completion anyway while `timeout` reports exit 124. Observed directly
during this audit — flow "timed out" at 240 s yet its log ended with
"All flow checks passed" written minutes later. Consequences: CI
cancellation, `timeout` wrappers, and script kills need SIGKILL to be
effective, and a wrapped harness can report failure (124) after actually
passing. Worth restoring default signal disposition in the harness
bootstrap (e.g. `signal.signal(SIGTERM, SIG_DFL)` after `pygame.init`)
or documenting the `timeout -s KILL` requirement in CLAUDE.md.

---

## Low findings

### L1. Three dead config constants

Defined in `systems/config.py`, referenced nowhere else in the repo
(verified against all 173 config constants):
- `WATCHER_SPAWN_INTERVAL` (`systems/config.py:277`)
- `VIS_WATCHER_OPEN` (`systems/config.py:540`)
- `VIS_WATCHER_HIDDEN` (`systems/config.py:541`)

All three look like leftovers of the watcher-curse rework (the live tuning
is the `WATCHER_*` clone/floor/gaze block). Dead tuning is a trap: someone
adjusts it and nothing happens.

### L2. Four dead private helpers in rendering/

Zero references repo-wide (AST scan of every top-level function, then
whole-corpus grep):
- `_aperture_mask` (`rendering/portal.py:267`) and `_tear_glow`
  (`rendering/portal.py:312`) — superseded by the current aperture pass.
- `_flame_tongue` (`rendering/sprites_carcosa.py:22`).
- `_project` (`rendering/king_unfold.py:215`) — its comment says "kept for
  tools/explore_4d_shapes.py compat," but that tool no longer exists.

### L3. Doc drift (minor)

- CLAUDE.md calls `systems/game.py` "~2k lines"; it is 3,118.
- Eleven comments across the code still cite "GAME_CHANGES §N" for
  provenance; the file was deleted (folded into TODO.md). Harmless but the
  pointers now dangle for a new reader.

### L4. Swallowed callback exceptions in text input

`ui/text_input.py:67` and `:76` wrap the `on_cancel` / `on_submit`
callbacks in `try/except Exception: pass`. A bug in a submit handler
(e.g. a save-name hook) vanishes without a traceback. If the intent is
crash-proofing the input layer, printing the traceback before continuing
would keep the safety without the silence.

### L5. Complexity hotspots (awareness, not action)

Largest function bodies (AST-measured): `tests/flow.py main` 2,297 lines,
`build_brimley` 1,144 (`scenes/brimley.py:139`), `draw_world` 782
(`systems/render_mixin.py:874`), `draw_npc_sprite` 694
(`rendering/sprites_npc.py:202`), `draw_king_unfold` 479
(`rendering/king_unfold.py:693`). These match the project's deliberate
"one cohesive beat per function" style and all sit behind the test gate;
listed so growth is a choice rather than an accident. The per-frame
allocations inside `draw_world` (a full-screen fade surface and a few
small SRCALPHA scratch surfaces per frame) are minor and only worth
touching if profiling ever says so.

---

## Suggested order of attack

1. **H1** — module-level audio library cache (small, safe, huge gate win).
2. **H2** — add the full gate to CI once H1 lands.
3. **M1** — call `reset_king_unfold_fx()` beside the three
   `reset_king_fx()` sites.
4. **M2** — restore SIGTERM disposition in the harness bootstrap.
5. **L1/L2** — delete the seven dead names in one sweep.
6. **L3/L4** — opportunistic cleanup.
