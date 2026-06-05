# Session status — shippability review → game.py refactor → health pass

> This is the **current** live-state doc. It supersedes the prior door-dream
> status (that arc is long landed; see HANDOFF.md history for it).

Branch: `claude/game-shippability-review-B1c5e` · pushed (local == remote).

## What landed this session (all verified green: `python tests/run_all.py`)

### 1. Fold-pursuit fix — a chaser follows through grove folds
A cultist hot on your heels now follows you through a hidden-fold grove
(`husk_grove` / `effigy_grove` / `scarecrow_ring`), even though those rooms host
no cult of their own. The old gate keyed the carry on the *destination* being a
cult/underground scene, so a grove fold wrongly shook the chase.
- `_note_fold_pursuit` (now in `systems/threat_mixin.py`) carries through a FOLD
  or seamless PASSAGE, or a descent into cult-held ground; it still shakes on a
  refuge (`FOLD_REFUGE_SCENES`) or a mundane interior door (via `_exit_is_fold`).
- The followed chaser is flagged `_fold_follower`; `_tick_cultists` spares it
  from the non-cult-scene sweep and lets it reach you, while the grove still
  draws no patrol/gaze/reinforcements. Mara's cell stays a refuge.
- Locked by `tests/fold_pursuit.py` (8/8).

### 2. systems/game.py refactor — 5163 → 2069 lines (−60%)
Behavior-preserving extraction into mixins (`class Game(CutsceneMixin,
ThreatMixin, InfestationMixin, RenderMixin, NarrativeMixin)`):
- `systems/config.py` — tuning constants + scene-gating sets.
- `systems/threat_mixin.py` — King, watcher-curse, cultist/fold pursuit,
  visibility + evidence floor, death.
- `systems/infest_mixin.py` — infestation/ashfall + hunting sheriff (+ the
  infested-local dialogue helpers).
- `systems/render_mixin.py` — `draw_world`, overlays, HUD, menus, death card.
- `systems/narrative_mixin.py` — flashback, case-log/notes, endings, opening.

Method moves were `ast`-exact (whole bodies only); each step verified with the
full gate **and** the `tools/capture_world.py` byte-identity diff (render output
identical within the documented ambient-spawn noise floor). No MRO method-name
collisions across the mixins.

### 3. Test gate + dead-code sweep
- **`tests/run_all.py`** — one command runs all four harnesses (smoke + flow +
  fold_pursuit + render_smoke) and exits nonzero on any failure. Documented in
  CLAUDE.md (dev commands + working agreements).
- **Dead code swept** (~550 lines): removed `rendering/king3d.py` (whole module,
  superseded by `king_unfold.py`) and 12 unreferenced functions
  (`sprites.py` `_cult_eye`/`_scream_face`/`_noir_grit`/`_yk_glow`/`_yk_void`/
  `_yk_flames`, `dsp.py` `pitch_shift`/`fade_in`/`fade_out`, `sight.py`
  `is_seen`, `base.py` `_draw_building_eaves`, `our_house_area.py`
  `_yard_cache_pickup`). Verified 0 call sites + 0 doc refs before removal; the
  live `_yk_glow_disc` and the `_draw_king` fallback were left intact.

### 4. Docs updated to match
CLAUDE.md (mixin layout, threat-model location, dev commands, working
agreements, flashback tuning pointer → `ui/cutscenes.py`), this file, HANDOFF.md.

## Health snapshot (2026-06)
- Compiles clean; `python tests/run_all.py` all green; 120-frame runtime sweep
  across 5 scenes + king-spawn path with no exceptions.
- Player-facing dash rule clean; zero TODO/FIXME markers; deps pinned in
  `requirements.txt`; no committed `.pyc`.
- No open ship-blockers found.

## Open / next (need direction)
- **GAME_CHANGES.md §12 — Rev. Asa Crane: DONE.** Added his pulpit condemnation
  (the cult are *willing* apostates who cast God aside for gain, not puppets) to
  the doomed 2nd-conversation sermon in `scenes/dialogue.py`. Only an *optional*
  murder-beat polish remains. No required narrative work is now open.
- **Optional deeper refactor:** the god-methods inside the mixins
  (`draw_world` ~466L, `update_player`, `_log_case_entry` 169L) were left intact
  — splitting their internals is real surgery (z-order/logic risk), now safely
  behind the `capture_world.py` golden gate if you want it.
- **Doc scatter:** several overlapping kickoff prompts remain
  (`CONTINUE_PROMPT.md`, `SESSION_PROMPT.md`, `PHASE1/2_PROMPT.md`) — historical;
  consolidate/prune if you want a tidier root.
- Branch is well ahead of `main`; merge when ready.
