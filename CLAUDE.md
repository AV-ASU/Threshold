# THRESHOLD — Claude guide

> **HARD RULE — no dashes in player-facing text.** Never use em-dashes (—),
> en-dashes (–), or double-hyphen dashes (`--`) as punctuation in ANY text the
> player reads: item names/descriptions, dialogue, narrator beats, notices,
> evidence/notes entries, ending text, on-screen labels. Rewrite with a period,
> comma, colon, or a new sentence instead. (Code comments and these docs may
> still use them; this rule is about strings the player sees.)

A narrative-horror game in **pygame**, played through an **oblique
tilted camera** (the view tilts ~55°; it is the only in-game camera). The
flat pitch-0 view is **dev-only** now (there is no in-game toggle): the
headless capture tools (`tools/capture_world.py`, the previews) set pitch 0
directly for frame capture. Every sprite is drawn **procedurally** — there is
no image-asset pipeline. The core loop is stealth/dread (walk, watch,
hide), driven by a **visibility** meter that feeds the **King in Yellow**,
the lethal apex pursuer. (See the tilted-camera track below + `CAMERA.md`.)

## Dev commands

```bash
# Run (needs a display)
python main.py

# Full test gate — runs all five harnesses (smoke + flow + fold_pursuit +
# king_roam + render_smoke) and exits nonzero if any fails. Self-configures SDL
# dummy drivers, so no env vars needed. Run from repo root before every commit/push.
python tests/run_all.py

# Or run a single harness (same drivers, standalone):
python tests/smoke.py        # scene-builder / spawn / exit / drop-rate smoke
python tests/flow.py         # story-beat integration + canon guards

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
- `systems/game.py` — the orchestrator (~2k lines). State machine
  (`title` / `playing` / `transition`), `step(dt)`, scene loading
  (`load_scene_now`), the core update/input loop, combat, and
  `_reset_run_state()` (wipes per-run state on New Game; the `Game` instance
  is reused across quit-to-title). The big cohesive subsystems were split off
  into **mixins** that `Game` inherits (`class Game(CutsceneMixin,
  ThreatMixin, InfestationMixin, RenderMixin, NarrativeMixin)`) — they are
  still `Game` methods, just housed in their own files:
  - `systems/config.py` — gameplay tuning constants + scene-gating sets
    (`SAFE_SCENES`, `CULTIST_SCENES`, `UNDERGROUND_SCENES`, the `VIS_*` /
    `KING_*` / `WATCHER_*` / `FOLD_*` blocks …). `game.py` does
    `from systems.config import *`, so bare-name refs and external
    `from systems.game import <CONST>` both still resolve.
  - `systems/threat_mixin.py` — the threat model (below): King, watcher-curse,
    cultist + fold/portal pursuit, visibility + evidence floor, death.
  - `systems/render_mixin.py` — the draw layer: `draw_world`, overlays, HUD,
    the title/pause/settings screens, the death card.
  - `systems/infest_mixin.py` — infestation/ashfall + the hunting sheriff,
    plus the infested-local dialogue helpers.
  - `systems/narrative_mixin.py` — the journal flashback, the case-file /
    interior-voice notes (`_log_case_entry` …), the endings + opening crawl.
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
    eruption ramp, 0→1 over ~1.2s, during which he cannot move).
  - `enemy.py` — only `kind == "cultist"` runs the cult state machine;
    other kinds use a straight-line chase.
- `rendering/`
  - `sprites.py` — procedural sprite drawing (`draw_npc_sprite`). This is now a
    thin **facade** that re-exports the public surface from themed siblings, so
    `from rendering.sprites import <name>` is unchanged. The siblings:
    `sprites_common.py` (shared palettes + the `KING_UNFOLD` flags),
    `sprites_cultist.py`, `sprites_npc.py` (`draw_npc_sprite` + per-view body/
    head helpers), `sprites_corpse.py`, `sprites_infested.py`,
    `sprites_player.py` (`draw_player_sprite`, `view_from_facing`),
    `sprites_king.py` (the pallid `_draw_king` fallback + `_YK_*` FX +
    `door_mask_surface`), `sprites_weapons.py`, and `sprites_carcosa.py` (the
    death + Carcosa cutscene art). Edit the sibling, not the facade. The
    `yellow_king` sprite routes to **THE UNFOLDING** (`king_unfold.py`) when
    `KING_UNFOLD` is True (the default); flip it False (in `sprites_common.py`)
    to fall back to the flat pallid-mask `_draw_king` (keeps per-frame state in
    `_YK_*` globals).
  - `king_unfold.py` — **THE UNFOLDING**, the non-humanoid 4D King in play. A
    real 4D everting mass (mass + hypersphere heart rotate through 4D planes,
    project 4D→3D→2D, silhouette never repeats), faceless, with eyes opening
    across the skin, 3D limbs that erupt where it everts forward and reach the
    player (≥2 above threat 0.8), and 3D toothed eversion-maws (patch-bound).
    `draw_king_unfold(surf,x,y,t,threat,scale,to_player,birth,lean)` — `lean`
    is the screen-space travel dir × speed; the mass everts FORWARD along it
    (leading hemisphere surges+swells, tail tapers) as the locomotion tell. The
    death `draw_unfold_catch(surf,t)` is the throat-swallow (mouth iris → tunnel
    of teeth → gold furnace), routed from `_draw_death_screen`. Game feeds it
    live `threat`, `birth`, screen-space `to_player`/`lean`, and a tilt-only
    `scale_mul` depth-scale (`KING_TILT_DEPTH_*`, looms as he closes). Stateless
    except a one-time cached `_FORM`. Preview: `tools/preview_king_unfold.py`.
  - `transform.py` — `draw_vessel_bloom`, the human→vessel morph.
  - **Tilted-camera track (LIVE — the oblique view is the default; F3
    toggles back to flat pitch-0):** `camera.py` (`Camera.project(wx,wy,wz)`,
    the single world→screen seam + `depth()` sort key), `solids.py`
    (volumetric `draw_solid`/`draw_box`/`draw_billboard`), `skybox.py`
    (procedural void-fill backdrop), `occlusion.py` (fade walls that hide the
    player), `pseudo3d.py` (the Watcher proof), `sight.py` (the **Phase 4
    blind-spot vision** buffer). The plan — render most objects as 3D solids
    projected to 2D, lock pitch ~55°, head-turn ±45°, skybox in the voids —
    lives in **`CAMERA.md`**. Previews:
    `tools/preview_{tilt,skybox,occlusion,pseudo3d,sight,blindspot_live}.py`.
    Under tilt, **trees + cornstalks stand up as 3D billboards** (`_tilt_standee`
    in `scenes/base.py`, cached cards + a horizontal-run corn LOD `_corn_runs`)
    and join the wall/occluder set returned by `draw_terrain_tilted` — so they
    depth-sort + fade per-actor like walls (`_TILT_BILLBOARD_CHARS` in the
    collection + `_tilt_tile_box` dispatch; the flat floor raster skips them via
    `draw_scene_terrain(..., skip_billboard=True)`). Collision is unchanged;
    flat top-down draws them flat as before.
  - **Blind-spot vision (`sight.py`, CAMERA.md Phase 4):** under tilt,
    `draw_world` gates what is **drawn** (NPCs, enemies, corpses, items, and
    the infestation rot decals — flagged `_sight_gated`) to a forward sight
    cone keyed to `look.aim` and clipped by `Scene.blocks_sight`, via
    `visible_factor(...)` → a soft-alpha fade (`draw_with_alpha`). The world
    keeps **simulating** off-camera (the update path is untouched); unseen
    things simply aren't rendered and **re-hide** when you look away (no
    last-seen memory). The **King is exempt** (relentless apex); the player is
    never gated. All gating sits behind `_sight is not None` (set only when
    `_tilt_on()`), so **pitch 0 is byte-identical** (`tools/capture_world.py`).
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

## Threat model (the core mechanic, in `systems/threat_mixin.py`)

- **`visibility`** ∈ [0, 1] (`_tick_visibility`): Watchers + cultist gaze
  raise it; hiding (`VIS_HIDE_BLEED`) and idle decay (`VIS_IDLE_DECAY`)
  lower it. Tuning lives in the `VIS_*` constant block.
- **Hiding is positional (cult line of sight).** The cult AI detects by
  **real line of sight**, not distance X-ray: `has_los` (`entities/enemy.py`
  underground + `entities/npc.py` surface) gates on
  `Scene.clear_sight_line(x0,y0,x1,y1)` — a wrap-aware march over the
  `blocks_sight` predicate (walls + solid props occlude; windows + water do
  not). Put cover between you and a cultist and the lock drops → SEARCH
  (walk to last-seen, mill, give up). So the player breaks a chase by
  **moving behind cover** (a wall, a pillar, the corn). The old "behind"
  `hide_spots` were **removed** as redundant with this; the only E-press
  hides left are the handful of crawl-**under**-furniture spots (`"under"`,
  e.g. under a bed/desk/cot), which set `player.hidden` the same way corn
  does (`game.py`). Apex pursuers (`_force_chase`: King, hollow Sheriff)
  are **exempt** — they never lose sight.
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
  in that room** (`_kill_npc` returns keep → `_make_corpse`). **Cultists now
  leave bodies too** (override of the old "the cult reclaims its own" sweep):
  NPC cultists keep via `_kill_npc` (no visibility spike — that's local-only),
  and **enemy** cultists (well/depths, `kind="cultist"`) synthesize a corpse
  NPC in `_kill_enemy` so the npc-corpse draw path renders them. The body is
  **not** persisted across scene loads (no `dead_locals` ledger) — the scene
  rebuilds live on re-entry.
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

- **Canon TODO lives in `GAME_CHANGES.md`.** A 2026-06 narrative-alignment
  pass settled a batch of story decisions and the **code changes to make
  the game match** are tracked in `GAME_CHANGES.md` (with `NARRATIVE.md` §8
  pointing to it). Highlights that override older code/comments: the
  **Ledger is on the Lodge front desk** (the cellar copy is cut), **Mr.
  Sable is the most-attuned *local*** (not a newcomer), the **Playscript is
  the cult's own notes**, and the **Deep Stair no longer consumes the
  keystone** (Mask + notes are carried down and spent at the Threshold to
  SEAL). Check `GAME_CHANGES.md` before touching the cast, the ledger, the
  fork, or the Deep Stair.
- **Teleportation is consolidated — one primitive, don't add bespoke
  paths.** Doors/ladders/ropes fade (`begin_transition`'s fade path);
  EVERY other traversal — seamless world edges, direction-gated fold
  exits, the maze's same-scene `I`/`Q` relocations, and the King's rift
  juke — funnels through `Game.cross_fold` (`systems/game.py`): no fade,
  no sting, stride/look/screen-position preserved. The crossing is
  deliberately nothing; the FRAME is the spectacle. Visible folds + the
  King's portal share ONE anchored frame renderer
  (`rendering/portal.py draw_rift_door`: pane stands along its world
  seam, foreshortens like a wall, thins to nothing off-angle). Same-scene
  folds are SILENT (skipped by `_build_fold_cache` — the lie is the world
  itself). One-way is the King's signature alone. See NARRATIVE §11 "One
  phenomenon, two presentations" + PORTALS.md "Decisions landed". Live
  proof sheet: `tools/preview_rift_anchored.py`.
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
  (`_draw_flashback`). `_tick_flashback` lives in `systems/narrative_mixin.py`;
  the `FLASHBACK_*` tuning block (`_DUR`, `_MASK_FRAMES`, `_SWARM_START/_PEAK`,
  `_RATE_MIN/_MAX`, `_FOCAL_Y`) is defined in `ui/cutscenes.py`.
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

- **Verify before you commit.** Run compile + `python tests/run_all.py` (the
  full gate: smoke + flow + fold_pursuit + king_roam + render_smoke) and confirm green
  BEFORE `git commit`/`push`. A commit was pushed twice this project with a
  `NameError` because edits were batched and not re-verified. For
  rendering/refactor work also run the byte-identity gate
  (`tools/capture_world.py --tag before/after`, then `--diff`).
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
