# THRESHOLD — Claude guide

A top-down narrative-horror game in **pygame**. Every sprite is drawn
**procedurally** — there is no image-asset pipeline. The core loop is
stealth/dread (walk, watch, hide), driven by a **visibility** meter that
feeds the **King in Yellow**, the lethal apex pursuer.

## Dev commands

```bash
# Run (needs a display)
python main.py

# Tests — fast scene-builder / spawn / exit / drop-rate smoke checks.
# Self-configures SDL dummy drivers, so no env vars needed. Run from repo root.
python tests/smoke.py

# Syntax/compile check (the project has no configured linter)
python -m compileall systems entities scenes rendering ui .
```

Headless work (no display/audio — web sessions, ad-hoc scripts):

```bash
export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=.
```

`.claude/hooks/session-start.sh` sets this automatically for Claude Code
on the web. To *see* sprites/animations, use the `sprite-preview` skill —
it renders the procedural sprites to a labelled PNG strip.

## Layout

- `main.py` — entry point: `Game().run()`.
- `systems/game.py` — the orchestrator (large). State machine
  (`title` / `playing` / `transition`), `step(dt)`, `draw_world`, scene
  loading (`load_scene_now`), the threat model, and the closure/ending
  sequences. `_reset_run_state()` wipes per-run state on New Game (the
  `Game` instance is reused across quit-to-title).
- `scenes/` — `SCENE_BUILDERS` registry + `load_scene(key)`
  (`scenes/__init__.py`, ~37 scenes). A scene has spawns, exits,
  decorations, npcs, enemies, items, and optional
  `on_enter_fn` / `on_exit_fn` / `on_update` / `on_interact_fn` hooks.
- `entities/`
  - `player.py`
  - `npc.py` — movement modes (`idle`, `watch`, `wander`, `patrol`,
    `stalker`, `follower`, `chaser`). `chaser` runs the cultist state
    machine (`_cult_tick`: scout→chase→search→investigate). The
    `yellow_king` sprite short-circuits to `_yk_update` (the `_birth`
    eruption ramp, 0→1 over ~1.2s, during which he cannot move).
  - `enemy.py` — only `kind == "cultist"` runs the cult state machine;
    other kinds use a straight-line chase.
- `rendering/`
  - `sprites.py` — procedural sprite drawing (`draw_npc_sprite`,
    `_draw_king`). The King keeps per-frame state in module globals
    (`_YK_*`); fine for the single King in play.
  - `transform.py` — `draw_vessel_bloom`, the human→vessel morph.
- `systems/`
  - `save.py` — **in-memory only, no disk**. `Save.new()` builds from
    `DEFAULT_SAVE`; quitting to title throws it away (single-session).
  - `items.py` — `ITEM_DEFS`, `Inventory`.
  - `threat.py` — `proximity_tier` + `PROX_TIER_*` helpers.
- `ui/` — dialog, inventory, notebook, fonts, text input.

## Threat model (the core mechanic, all in `systems/game.py`)

- **`visibility`** ∈ [0, 1] (`_tick_visibility`): Watchers + cultist gaze
  raise it; hiding (`VIS_HIDE_BLEED`) and idle decay (`VIS_IDLE_DECAY`)
  lower it. Tuning lives in the `VIS_*` constant block.
- **King in Yellow** (`_tick_king`): at `visibility >= 1.0` he spawns at
  `_king_anchor` (the player's scene-entry point); below `0.90` he
  dissolves; he catches at distance `< 24` **only once `_birth >= 1.0`**
  (the eruption is the grace window). `SAFE_SCENES` never host him.
- **Curse** (the watcher-curse): a cultist ritual (`_tick_ritual` →
  `_apply_curse`) binds a **Watcher** to you (`_cursed`). It **clones** —
  up to `WATCHER_MAX` (5) — while you stay **exposed** (in the open;
  cloning pauses in cover), and **each live Watcher raises the visibility
  floor** by `WATCHER_FLOOR` (summed, capped at `VIS_FLOOR_TOTAL_CAP`
  0.92 — just under the King, so it's survivable). You **cure** it by
  clearing them all (`_tick_watchers`/`_dispel_watcher`): hold one in
  your **gaze** for `WATCHER_GAZE_DISPEL` s (its eyes go dark, then it
  dissolves), or put one down instantly with the **axe** arc or a
  **round**. `SAFE_SCENES` only *suppress* Watchers; they re-form on the
  way out. The gun and axe **share one weapon slot** (left-click / `K` to
  use, `Q` to swap).
- A pursuer reaching the player triggers the **death** sequence
  (`_trigger_death(kind)` → `_tick_death`): `kind="cultist"` shows the
  **CAPTURED** card (taken alive for the hive); `kind="king"` plays the
  **Carcosa** mask-furnace cutscene. Both end the run and return to title.

## Conventions & gotchas

- **No day/night cycle** — it was removed; everything reads as one
  (daytime) state. Don't reintroduce `day_phase` / `day_count`.
- **Scene-gating sets**: `SAFE_SCENES`, `DARK_SCENES`, `OUTDOOR_SCENES`
  drive King safety, flashlight darkness, etc.
- `visibility` persists across scene loads (only `_reset_run_state`
  clears it); `_king`, `_watchers`, and hide-state are cleared on every
  `load_scene_now`.
- Sprites are 100% procedural — no art assets to edit.
- `__pycache__/` is gitignored; never commit `.pyc`.
