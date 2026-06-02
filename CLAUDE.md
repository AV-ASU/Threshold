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
    `stalker`, `follower`, `homebody`, `chaser`). `homebody` loiters
    near the NPC's doorstep (`home`), then steps inside — sets
    `_inside` True, drops `solid`, and Game skips drawing/talking to it
    — for a spell, then re-emerges (the door-anchored Brimley locals).
    `chaser` runs the cultist state
    machine (`_cult_tick`: scout→chase→search→investigate). The
    `yellow_king` sprite short-circuits to `_yk_update` (the `_birth`
    eruption ramp, 0→1 over ~1.2s, during which he cannot move). It also
    eases `_yk_lean` 0→1 (smoothed locomotion magnitude) while actually
    travelling — the Unfolding everts forward along `self.facing` by this
    much (a travel tell; 0 while born/stalled).
  - `enemy.py` — only `kind == "cultist"` runs the cult state machine;
    other kinds use a straight-line chase.
- `rendering/`
  - `sprites.py` — procedural sprite drawing (`draw_npc_sprite`,
    `_draw_king`). The flat pallid-mask `_draw_king` keeps per-frame state in
    module globals (`_YK_*`); fine for the single King in play.
  - `king_unfold.py` — **THE UNFOLDING**, the non-humanoid King now in play. A
    real 4D everting mass (mass + hypersphere heart rotate through 4D planes,
    project 4D→3D→2D, silhouette never repeats), faceless, with eyes opening
    across the skin, 3D limbs that erupt where the body everts forward and reach
    the player (≥2 above threat 0.8), and 3D toothed eversion-maws that warp with
    the flesh (patch-bound). `draw_king_unfold(surf,x,y,t,threat,scale,to_player,
    birth,lean)` — `lean` is the screen-space travel dir × speed; the mass everts
    FORWARD along it (leading hemisphere surges+swells, tail tapers) as the
    locomotion tell — and the death `draw_unfold_catch(surf,t)` (the throat-swallow).
    **Wired as `yellow_king`:** `draw_npc_sprite` routes there when
    `sprites.KING_UNFOLD` is True (False → the old flat King); death routes from
    `_draw_death_screen`. Stateless except a one-time cached `_FORM`.
    **Under tilt** `draw_world` also (a) **depth-scales** him via a `scale_mul`
    on `draw_npc_sprite` — a perspective divide about the player's depth plane
    (`KING_TILT_DEPTH_*`), so he looms as he closes the view-depth gap and
    shrinks as he hangs back (pitch 0 untouched); and (b) **occludes him by his
    OWN depth (decided: hybrid)** — he's DEFERRED out of the actor pass and
    composited against the walls after the wall passes (`_composite_tilt_king`):
    walls nearer the camera than him occlude his base, he draws over walls
    farther than him (the shared player-depth split mis-orders a tall actor).
    His billboard towering into a *far* wall is intentional; don't make him
    always-on-top. `draw_terrain_tilted` returns `(front, all_walls)` for this.
  - `transform.py` — `draw_vessel_bloom`, the human→vessel morph.
  - **Tilted-camera track (LIVE — the oblique view is the default now):**
    `camera.py` (`Camera.project(wx,wy,wz)`, the single world→screen seam +
    `depth()` sort key), `solids.py` (volumetric
    `draw_solid`/`draw_box`/`draw_billboard`), `skybox.py` (procedural
    void-fill backdrop), `occlusion.py` (fade walls that hide the player),
    `pseudo3d.py` (the Watcher proof). The plan — render most objects as
    3D solids projected to 2D, lock pitch ~55°, head-turn ±45°, skybox in
    the voids — lives in **`CAMERA.md`**. Previews:
    `tools/preview_{tilt,skybox,occlusion,pseudo3d}.py`. **The camera is
    locked at `TILT_PITCH_DEG` (~55°) by default** (`_reset_run_state` /
    `_start_play` seed it; look heading seeded from the player's facing);
    **F3 toggles back to flat top-down (pitch 0) for debugging.**
- `systems/`
  - `save.py` — **in-memory only, no disk**. `Save.new()` builds from
    `DEFAULT_SAVE`; quitting to title throws it away (single-session).
    Killed innocent **locals** lie where they fell **only while the player
    is in that room** (`_make_corpse`); the body is *not* persisted across
    scene loads — the scene rebuilds the local live on re-entry (the act
    costs in the moment, not a ledger; NARRATIVE 1b/3).
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
  way out. The gun and axe **share one weapon slot** (left-click to use;
  switch which one is equipped from the inventory screen).
- **Killing locals**: the gun is *not* cult-only. A clean round drops any
  living **local** instantly (lethal regardless of the evidence stagger
  gate, which only ever protected the cult — see `Projectile._strike` /
  `_BULLET_PHANTOM`). A local kill spikes `visibility`
  (`LOCAL_KILL_VIS_SPIKE`, capped just under the King), pings the cult to
  investigate the body, and leaves a corpse **for as long as the player is
  in that room** (`_kill_npc` returns keep → `_make_corpse`; cultists are
  still swept/removed). The body is **not** persisted across scene loads
  (no `dead_locals` ledger) — the scene rebuilds the local live on re-entry.
- **Infestation** (`_apply_infestation`, called from `load_scene_now`):
  the world rots as a pure, monotonic function of evidence —
  `_infest_stage()` = `min(3, evidence)`, **front-loaded** so the surface
  peaks as the player commits underground at 3. Scenes rebuild each load,
  so the pass is deterministic + additive (never accumulates). It (a)
  scatters escalating rot decals (`_infest_decals`, seeded; surface +
  safe-rooms-at-3 + underground, which is baseline-rotted from ev0), (b)
  transforms surface locals by name: **converts** the peace-makers
  (`INFEST_CONVERT` → `_convert_local`: sprite→`cultist`, tag
  `cult_convert` = *passive* cult, gaze-only via `_tick_cultists`, never
  grabs) and **mutates** the resisters (`INFEST_MUTATE` → `_mutated` flag):
  their flesh deforms into a **bespoke body-horror form** with the fold's
  gold/Sign in the wound — Toby (head cleaves to a maw), Hettie (face
  peels, Sign carved in), Garrick (skinned to sallow raw flesh, a black-gold
  cancer of pop-out tumors erupting through it, fed by engorged vessels),
  others use a generic fallback. Authored at BOTH scales that must agree:
  the world sprite (`draw_infested_overlay` in `sprites.py`, `_INFEST_WORLD`)
  and the dialog portrait (`Dialogue._draw_infested_portrait`, shown via
  the `infested=True` flag on `show()` from `_mutated_local_dialogue`).
  And (c) at stage 3 turns
  the Sheriff's office into a **unique threat**: `_spawn_hunting_sheriff`
  (`sheriff_hollow` sprite) holds for an intro beat then force-chases
  (`_tick_sheriff`); contact → `_trigger_death("sheriff")`. Player-killed
  locals are drawn by `draw_npc_corpse` at **`mold=0`** (a clean fresh
  kill) — since corpses no longer persist across loads, there's no growing
  rot stage to track. (`draw_npc_corpse` still *accepts* a `mold` 0..3 and
  the fold-claim art — `_CORPSE_CLAIM` for named resisters, `_CORPSE_ECHO`
  compulsion echoes — survives in `sprites.py` as reusable art, just no
  longer driven by an accumulating stage.)
- A pursuer reaching the player triggers the **death** sequence
  (`_trigger_death(kind)` → `_tick_death`): `kind="cultist"` shows the
  **CAPTURED** card (taken alive for the hive); `kind="sheriff"` the
  **TAKEN INTO CUSTODY** card (the hollow lawman); `kind="king"` plays the
  **Carcosa** mask-furnace cutscene. All end the run and return to title.

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

## The journal door-dream + "He knows you" (NARRATIVE §1b / §0)

- **Trigger:** reading `mom_notebook` (Mara's journal) a third time sets
  `flashback_pending` (`ui/inventory_ui.py`); `Game._tick_flashback` polls it,
  sets `flashback_seen`, and runs a ~7s wordless cutscene
  (`_draw_flashback`). Tuning constants are the `FLASHBACK_*` block in
  `systems/game.py` (`_DUR`, `_MASK_FRAMES`, `_SWARM_START/_PEAK`,
  `_RATE_MIN/_MAX`, `_FOCAL_Y`).
- **Visuals:** dried-wood doorframe in black; a pulsing gold glow pooled at
  the door's **base** (`FLASHBACK_FOCAL_Y`), contained by the frame; faint
  peeking eyes; and an **accelerating swarm** of carved dark-wood masks
  (`_spawn_flashback_masks` → pre-rendered `_build_flashback_pool`) that clip
  on the jamb and whose gold gazes all aim back at the player. Mask art is
  `door_mask_surface(height, vis, gaze, seed)` in `rendering/sprites.py`
  (recessed sockets, no mouth; `gaze=(gx,gy)` points the pupils; `_jag_blob`
  gives irregular shapes). Audio bed: `Audio.flashback_air()` +
  `falling_air` SFX in `systems/audio.py`.
- **CANON — do not break:** the PI dreamed the door **exactly once, a year
  ago, and never reached it** (it never took root). The journal *reminds* him
  of that single dream — it is **not** recurring. The case note
  (`Game._log_dream_entry`) must read as that half-dismissed memory.
- **"He knows you":** `_log_dream_entry` writes the dream to save arg
  **`notes`** (shown by `NotebookUI` after the clues). It must NOT go in
  `evidence` — `_evidence_count` is `len(save.arg("evidence"))` and drives the
  King-gate + infestation; only the six `CANONICAL_EVIDENCE` beats belong
  there. At the real Threshold (`scenes/depths.py build_threshold`
  `on_enter`), if `flashback_seen`, a recognition line lands before the
  doorframe beat: *"You have stood here before. In sleep."*

## Working agreements (process — learned the hard way)

- **Verify before you commit.** Run compile + `tests/smoke.py` + (for
  narrative/scene work) `tests/flow.py` and confirm green BEFORE
  `git commit`/`push`. A commit was pushed twice this project with a
  `NameError` because edits were batched and not re-verified.
- **One edit at a time on a shifting file.** Don't batch many `Edit`s against
  the same file in one turn; an early edit moves line context and later ones
  silently mis-apply. For multi-site mechanical changes, write a small Python
  patch script with `assert count == 1` per replacement, then run + verify.
- **Check narrative text against `NARRATIVE.md` BEFORE writing it**, not
  after. The bible is the source of truth; quote its intended voice.
- **`tests/flow.py`** is the integration harness (separate from `smoke.py`):
  boots a game, drives scene hooks, asserts story beats. It also carries
  **canon-guards** (e.g. the dream note must say "a year" and contain no
  recurrence language). Keep it green; add a guard when you lock a canon fact.
- **Watch for stale refs from the village→brimley merge.** Scene keys, the
  well position (`scene._well_pos`, col 94/row 13), and NPC names changed —
  the Kid is **"the Tisdale boy"** (Toby Tisdale), not "Village Kid".
- **Previewing visuals headlessly:** render to PNG/GIF with
  `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` + Pillow (installable) and
  send with the file tool. For whole-screen cutscenes, step
  `_tick_flashback` / `_draw_flashback` in a loop and capture
  `pygame.image.tostring`.
