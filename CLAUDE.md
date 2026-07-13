# THRESHOLD — Claude guide

> **READ THIS FIRST — the four-doc canon.** This file (`CLAUDE.md`) is the
> project's entry point and operating guide. Before doing ANY work on
> THRESHOLD, read the other three canon docs in full and hold them in mind:
> - **`NARRATIVE.md`** — the story bible: premise, lore, cast, place, the
>   evidence trail, the endings, and the canon invariants. The source of
>   truth for anything the fiction asserts.
> - **`DESIGN.md`** — every game system and its code map: the threat model,
>   world rot, the fold, the tilted camera, audio, stealth, the Works level,
>   and art direction.
> - **`TODO.md`** — the live list of genuinely open work. Not a place for
>   lore.
>
> These four files are the ENTIRE doc canon. The old per-topic docs
> (`CAMERA.md`, `PORTALS.md`, `STEALTH_REWORK.md`, `AUDIO.md`, and the two
> audit files) were folded into them and deleted (2026-07), so every design
> or story reference now lives in one of these four. When you change a canon
> fact, change it in its ONE home and reconcile the others: a detail that is
> true in one doc and stale in another is rot.

> **HARD RULE — no dashes in player-facing text.** Never use em-dashes (—),
> en-dashes (–), or double-hyphen dashes (`--`) as punctuation in ANY text the
> player reads: item names/descriptions, dialogue, narrator beats, notices,
> evidence/notes entries, ending text, on-screen labels. Rewrite with a period,
> comma, colon, or a new sentence instead. (Code comments and these docs may
> still use them; this rule is about strings the player sees.)

A narrative-horror game in **pygame**, played through an **oblique
tilted camera** (the view tilts ~55°; it is the ONLY camera). The pitch is
locked to ~55°; there is no flat/pitch-0 view (the capture and preview tools
render that same tilt). Every sprite is drawn **procedurally** — there is
no image-asset pipeline. The core loop is stealth/dread (walk, watch,
hide), driven by a **visibility** meter that feeds the **King in Yellow**,
the lethal apex pursuer. (See the tilted-camera track below + `DESIGN.md §10`.)

## Dev commands

```bash
# Run (needs a display)
python main.py

# Full test gate — runs all six harnesses (smoke + flow + stealth +
# fold_pursuit + king_roam + render_smoke) and exits nonzero if any fails.
# Self-configures SDL dummy drivers, so no env vars needed. Run from repo
# root before every commit/push.
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
- `systems/game.py` — the orchestrator (~3k lines). State machine
  (`title` / `playing` / `transition`), `step(dt)`, scene loading
  (`load_scene_now`), the core update/input loop, combat, and
  `_reset_run_state()` (wipes per-run state on New Game; the `Game` instance
  is reused across quit-to-title). The big cohesive subsystems were split off
  into **mixins** that `Game` inherits (`class Game(CutsceneMixin,
  ThreatMixin, KingRoamMixin, RotMixin, RenderMixin,
  NarrativeMixin)`) — they are
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
  - `systems/rot_mixin.py` — world rot/ashfall + the moth sim + the
    hunting sheriff.
  - `systems/narrative_mixin.py` — the journal flashback, the case-file /
    interior-voice notes (`_log_case_entry` …), the endings + opening crawl.
- `scenes/` — `SCENE_BUILDERS` registry + `load_scene(key)`
  (`scenes/__init__.py`, ~44 scenes). A scene has spawns, exits,
  decorations, npcs, enemies, items, and optional
  `on_enter_fn` / `on_exit_fn` / `on_update` / `on_interact_fn` hooks.
  - `scenes/base.py` — the `Scene` class + scene-builder helpers
    (`scatter_forest_band`, `chest_interact` …). Since 2026-07 it is a
    **facade**: the tile definitions + the entire terrain draw layer
    (flat + tilted camera: `draw_terrain_tilted`, `draw_scene_terrain`,
    the `_tilt_*` set, walls/roofs/water/doors, `apply_grade`) live in
    the leaf `scenes/terrain.py`, which base re-exports wholesale
    (public AND `_private` names, plus the `import scenes.base as _sb`
    wildcard). So `from scenes.base import <x>` is unchanged; edit
    `terrain.py` for draw code, `base.py` for the Scene model. terrain
    depends only on `constants` + lazy `scenes`/`rendering.*` imports,
    never on `Scene`, so there is no cycle.
- `entities/`
  - `player.py`
  - `npc.py` — movement modes (`idle`, `watch`, `wander`, `patrol`,
    `stalker`, `follower`, `homebody`, `worker`, `chaser`). `homebody`
    loiters near the NPC's doorstep (`home`), then steps inside — sets
    `_inside` True, drops `solid`, and Game skips drawing/talking to it
    — for a spell, then re-emerges (the door-anchored Brimley locals).
    `worker` (2026-07, the JOBS layer) walks a personal
    `npc.stations` route — travel, dwell facing the work, next — on
    the cult's errand machinery (`stealth.errand_step`; Garrick,
    Royce, the store Hettie, Rev. Crane). `chaser` runs the cultist state
    machine (`_cult_tick`: scout→chase→search→investigate). The
    `yellow_king` sprite short-circuits to `_yk_update` (the `_birth`
    eruption ramp, 0→1 over ~1.2s, during which he cannot move).
  - `enemy.py` — only `kind == "cultist"` runs the cult state machine;
    other kinds use a straight-line chase.
  - `decoration.py` — the `Decoration` prop class. Its per-kind draw is
    dispatched by `getattr(self, f"_draw_{kind}")`; since 2026-07 the
    ~128 `_draw_*` methods are split by theme into **mixin siblings**
    (`deco_furniture` / `deco_lighting` / `deco_nature` / `deco_structure`
    / `deco_mine` / `deco_horror`, mixed into `Decoration`), with shared
    lighting/compass helpers in `decoration_common.py`. Like the
    `sprites.py` facade, `from entities.decoration import Decoration` is
    unchanged; add a new prop kind by dropping a `_draw_<kind>` method
    into the fitting mixin.
- `rendering/`
  - `sprites.py` — procedural sprite drawing (`draw_npc_sprite`). This is now a
    thin **facade** that re-exports the public surface from themed siblings, so
    `from rendering.sprites import <name>` is unchanged. The siblings:
    `sprites_common.py` (shared palettes + the `KING_UNFOLD` flags),
    `sprites_cultist.py`, `sprites_npc.py` (`draw_npc_sprite` + per-view body/
    head helpers), `sprites_corpse.py`, `sprites_wound.py`,
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
    `draw_king_unfold(surf,x,y,t,threat,scale,to_player,birth,lean,gape)` —
    `lean` is the screen-space travel dir × speed; the mass everts FORWARD
    along it (leading hemisphere surges+swells, tail tapers) as the locomotion
    tell. 2026-07 rework: an in-place blur melts the facets into wet flesh
    (specular pass + drooling maws on top); above threat 0.25 the **Pallid
    Mask BONDS to one host facet** and is drawn in that facet's projected
    basis (`_pallid_mask_aff` — it skews/rolls/foreshortens WITH the flesh,
    never billboarded; when its host churns away it SINKS under a tar welt
    and rebonds; state in `_MASK_SURF`, reset via `reset_king_unfold_fx`);
    `gape` (0..1, fed from `npc._gape` by the `KING_LUNGE_*` state machine in
    `entities/npc.py _yk_update`) irises the leading face into the huge
    toothed mouth with the Mask in its throat — the lunge telegraph. The
    death `draw_unfold_catch(surf,t)` is the throat-swallow (mouth iris → tunnel
    of teeth → gold furnace), routed from `_draw_death_screen`. Game feeds it
    live `threat`, `birth`, screen-space `to_player`/`lean`, and a tilt-only
    `scale_mul` depth-scale (`KING_TILT_DEPTH_*`, looms as he closes). Stateless
    except a one-time cached `_FORM` + `_MASK_SURF`. Preview:
    `tools/preview_king_unfold.py`.
  - `moth.py` — **the Moth**, the King's herald + first flying entity
    (`draw_moth(surf,x,y,t,spread,glow,seed,flap,husk)`): tented ragged
    wings at rest, a limb-knot snap at the flare, a crumpled husk on the
    ground. Sim + spawn live in `systems/rot_mixin.py` (below).
  - `transform.py` — `draw_vessel_bloom`, the human→vessel morph.
  - **Tilted-camera track (LIVE — the oblique view is the ONLY camera; the
    pitch is locked, there is no flat/pitch-0 view):** `camera.py` (`Camera.project(wx,wy,wz)`,
    the single world→screen seam + `depth()` sort key), `solids.py`
    (volumetric `draw_solid`/`draw_box`/`draw_billboard`), `skybox.py`
    (procedural void-fill backdrop), `occlusion.py` (fade walls that hide the
    player), `pseudo3d.py` (the Watcher proof), `sight.py` (the **Phase 4
    blind-spot vision** buffer). The plan — render most objects as 3D solids
    projected to 2D, lock pitch ~55°, head-turn ±45°, skybox in the voids —
    lives in **`DESIGN.md §10`**. Camera FEEL (2026-07): the position
    lookahead follows the last WALK direction, eased, holding while you
    stand (`_update_camera` `_cam_lead`) — it must never ride the aim
    cursor; the yaw chase is aim-steady (trigger locks it, standing
    damps it, `CHASE_*`/`TURN_RATE` config). Previews:
    `tools/preview_{tilt,skybox,occlusion,pseudo3d,sight,blindspot_live}.py`.
    Under tilt, **trees + cornstalks stand up as 3D billboards** (`_tilt_standee`
    in `scenes/terrain.py`, cached cards + a horizontal-run corn LOD `_corn_runs`)
    and join the wall/occluder set returned by `draw_terrain_tilted` — so they
    depth-sort + fade per-actor like walls (`_TILT_BILLBOARD_CHARS` in the
    collection + `_tilt_tile_box` dispatch; the flat floor raster skips them via
    `draw_scene_terrain(..., skip_billboard=True)`). Collision is unchanged;
    flat top-down draws them flat as before.
  - **Blind-spot vision (`sight.py`, DESIGN.md §10):** under tilt,
    `draw_world` gates what is **drawn** (NPCs, enemies, corpses, items, and
    the world-rot decals — flagged `_sight_gated`) to a forward sight
    cone keyed to `look.aim` and clipped by `Scene.blocks_sight`, via
    `visible_factor(...)` → a soft-alpha fade (`draw_with_alpha`). The world
    keeps **simulating** off-camera (the update path is untouched); unseen
    things simply aren't rendered and **re-hide** when you look away (no
    last-seen memory). The **King is exempt** (relentless apex); the player is
    never gated. All gating sits behind `_sight is not None` (always live now, since the
    tilt is the only camera; `tools/capture_world.py` captures that view).
    The **see-through doors** feed this SAME gate into the room beyond: the
    aperture actor pass (`portal._draw_aperture_actors`, driven by
    `scene._door_actor_sight` = the frame's sight fn) culls a figure in the far
    room by the player's cone, so an empty room shows through the opening but a
    corner-lurker stays hidden (the rift is exempt — it shows all by design).
    Preview: `tools/preview_door_sight.py`.
  - **Ground heightfield (`rendering/heightfield.py`, DESIGN.md §10 —
    PROTOTYPE, dormant):** a per-scene ground height so terrain rolls and a
    crest you can't see over occludes like a wall. `Scene.set_ground(grid)` /
    `Scene.ground_z(x_px, y_px)` (0.0 when unopted → dead-flat, pitch-0
    byte-identical); author with `build_heightfield(w, h, bumps)`. Feeds SIGHT
    (an optional `ground=` crest term in `sight.los_clear` + `clear_sight_line`,
    `SIGHT_EYE_H`) and DRAW (`draw_ground_mesh` lays a projected floor mesh over
    the flat affine raster, tilt-only; actors lift by `ground_z`). Movement
    stays 2D (height is a passive READ; AI ignores it in v1). No shipping scene
    opts in yet. Preview: `tools/preview_heightfield.py`.
- `systems/`
  - `save.py` — the run state + **ONE disk slot (2026-07)**. `Save.new()`
    builds from `DEFAULT_SAVE`; the ONLY writer of the slot is sleeping
    at the spare-room cot (`Game._sleep_at_cot`: snapshots
    hp/inventory/visibility, wake lands at the cot, atomic write to
    `~/.threshold` / `%APPDATA%\THRESHOLD`, `THRESHOLD_SAVE_DIR`
    overrides for tests). Continue on the title reads it back; a death
    or a quit costs everything since the last sleep, never the run.
    Killed innocent **locals stay dead for the run** (2026-07 ruling):
    the kill is written to the `dead_locals` save arg
    (`_record_dead_local`) and `_apply_dead_locals` (run from
    `load_scene_now` before the rot pass) lays the body back down where
    it fell on every re-entry. New Game clears it; the cot save
    snapshots it like any arg (NARRATIVE §5 / DESIGN.md §1; flow §32).
  - `items.py` — `ITEM_DEFS`, `Inventory`.
  - `threat.py` — `proximity_tier` + `PROX_TIER_*` helpers.
- `ui/` — dialog, inventory, notebook, fonts, text input. **Dialog is
  three channels now (2026-07):** `dialog.py`'s modal band survives ONLY
  for choices and scripted beats with an
  `on_complete`; a named NPC line through the interact path floats over
  the speaker's head (`float_speech.py`); narrator/world-object text
  (examines, pickups, every `_evidence` beat) runs as the frameless
  lower-third caption in `narration.py` while the WORLD KEEPS RUNNING.
  `DialogueBox.show` does the routing. E answers the world first and only
  skims the caption when nothing else takes the press (last in
  `try_interact`). Replacing an active caption fires its pending
  `on_complete` early rather than dropping it.

## Threat model (the core mechanic, in `systems/threat_mixin.py`)

- **`visibility`** ∈ [0, 1] (`_tick_visibility`): Watchers + cultist gaze
  raise it; hiding (`VIS_HIDE_BLEED`) and idle decay (`VIS_IDLE_DECAY`)
  lower it. Tuning lives in the `VIS_*` constant block.
- **Detection is GRADED (2026-07 stealth rework; `DESIGN.md §12`).**
  Binary invisibility is gone. Each cultist carries a per-enemy
  **suspicion** ∈ [0, 1] filled per tick by a detection **score** =
  `los * distance_falloff * facing_cone * concealment`
  (`systems/stealth.py` — one source for both cult machines,
  `entities/npc.py` surface + `entities/enemy.py` underground; tuning in
  the `SUS_*` config block). Only a FULL bar locks the CHASE; at
  `SUS_NOTICE` the cultist stops and turns toward you (the rising "?"
  tell, `_draw_sus_tell` in `render_mixin`). Walls/solid props still
  occlude absolutely (`Scene.clear_sight_line`, wrap-aware; windows +
  water do not block). **Two cover classes:** CONCEALMENT — corn: mobile
  and leaky (`SUS_CONCEAL_CORN` scales score + gaze; a far cultist barely
  reads you, a near one still fills, and a LOCKED chaser can grab you in
  the stalks) — vs ENCLOSED — the `"under"`/`"in"` E-press hides: rooted,
  zero score/gaze, but a SEARCHING cultist **sweeps and CHECKS** nearby
  hides (`sweep_points`) → the timed **struggle**
  (`_tick_struggle`/`_struggle_win` in `threat_mixin`, `STRUGGLE_*`
  config): mash E to burst out (the checker staggers; a LOUD noise event
  converges the room) or the window expires into the CAPTURED death.
  `_tick_visibility` reads the concealment-weighted gaze; only an
  enclosed hide keeps the strong `VIS_HIDE_BLEED` drain (corn gets idle
  decay). Apex pursuers (`_force_chase`: King, hollow Sheriff) are
  **exempt** — they bypass suspicion and cover entirely. Guarded
  end-to-end by `tests/stealth.py`. (The Pillar-2 "peek" verb is
  deliberately deferred — free look under tilt already gives the
  information function; revisit in the human-tuning pass.)
- **Deep-water WADE** (TODO #8, `WADE_*` config, `Game._wading`): the
  flooded deep works (`WADE_SCENES` = works_cistern / the_sump /
  depths_threshing) stand in walkable `~` water. Wading a water tile
  **halves the player's speed** (sprint can't clear it) and throws a
  **loud splash** (`WADE_SPLASH_LOUD`, over `NOISE_SEARCH_PULL`, via
  `Scene.emit_noise` kind `"splash"`) that searchers converge on, so
  standing water is a routing risk, not just dressing. No new AI (rides
  the existing `stealth.hear_noise` ear); the Brimley river is **excluded**
  (not a WADE scene, keeps its own in/out rules). Water is authored per
  scene with the `_flood` helper (`scenes/depths.py`); guarded by
  `tests/stealth.py` §10.
- **King in Yellow** (`systems/king_roam_mixin.py` `_tick_king_roam`, the
  sole King tick): the roam **arms at `KING_GATE_EVIDENCE` (3)** — he
  walks scene to scene, concrete in the player's room, abstract elsewhere,
  and hunts on sight. Below the gate a maxed meter (`visibility >= 1.0`,
  cult awake) musters a cultist wave at `_king_anchor` instead
  (`_muster_reinforcements`). He catches at `KING_CATCH_DIST` (24 px)
  **only once `_birth >= 1.0`** (the eruption is the grace window).
  `KING_FREE_SCENES` (the safe rooms + dark/threshold) never host him.
- **The evidence LADDER (2026-07)**: each surface beat flips a visible
  world state. **Ev 0**: the town is only wrong — **no cult patrols
  spawn** (`CULT_WAKE_EV`, gated at `_ensure_cultists`), the idle King
  far up the road, ONE omen moth pre-drifting his road
  (`_moth_field = {KING_ROAM_START: 1}` at run start). **Ev 1**: the
  cult wakes (patrols spawn). **Ev 2**: his attention finds YOU — a
  single SEEKER moth materialises in the player's room every
  `MOTH_SEEK2_*` (2-3 min; `_tick_moth_seek`, never at a door, drops
  in on the `"b"` arrival ramp). **Ev 3**: he walks (the roam arms),
  his own shedding starts, the seeker slows to `MOTH_SEEK3_*`
  (5-6 min).
- **The Moths** (the King's heralds; `MOTH_*` config, sim in
  `systems/rot_mixin.py` `_tick_moth_shed`/`_tick_moth_seek`/
  `_spawn_moths`/`_tick_moths`, drawn as hovering sight-gated
  billboards in `render_mixin`). From `MOTH_SHED_EV` (3) evidence,
  every `MOTH_SHED_EVERY` (90s) the King sheds `MOTH_SHED_COUNT` (2)
  moths into whatever room HE occupies (`_roam_king["scene"]`), plus
  the player-seeker drip above. They **PERSIST and STACK per room**
  (`game._moth_field`, capped `MOTH_STACK_CAP`); rooms he lingers in
  fill fuller and fuller, and the field only thins when the player
  **spends** one (`_moth_spent`: a pop, or a flare burning out). So a
  room whipping with fast fliers means *he keeps coming back here*.
  Enter one's `MOTH_RADIUS` and it KINDLES (`MOTH_KINDLE` window: back
  out, axe it quietly up close, or spend a round from range); the
  window expiring is the **FLARE**: a `MOTH_REACH` noise the cult
  converges on, a visibility spike capped under the King, the dark
  broken around it (`_tick_dark_cover`) — it burns `MOTH_FLARE_DUR`,
  then **falls** as a charred husk that stays for the visit. First
  flare files a case NOTE (never evidence). Guarded by
  `tests/stealth.py` §9.
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
  investigate the body, and leaves a corpse **for the rest of the run**
  (`_kill_npc` returns keep → `_make_corpse`, and writes the kill to the
  `dead_locals` ledger; `_apply_dead_locals` lays the body back down on
  every re-entry — 2026-07 ruling: dead locals stay dead, flow §32; a
  dead Vane also suppresses the hollow-turn `sheriff_hunt` spawn). **Cultists
  leave bodies too** (override of the old "the cult reclaims its own"
  sweep): NPC cultists keep via `_kill_npc` (no visibility spike — that's
  local-only), and **enemy** cultists (well/depths, `kind="cultist"`)
  synthesize a corpse NPC in `_kill_enemy` so the npc-corpse draw path
  renders them. Cultist bodies are the one exception to persistence:
  they last only the visit (patrols are dynamic spawns and respawn by
  design).
- **World rot** (`_apply_rot`, called from `load_scene_now`):
  the world rots as a pure, monotonic function of evidence —
  `_rot_stage()` = `min(3, evidence)`, **front-loaded** so the surface
  peaks as the player commits underground at 3. Scenes rebuild each load,
  so the pass is deterministic + additive (never accumulates). It (a)
  scatters escalating rot decals (`_rot_decals`, seeded; surface +
  safe-rooms-at-3 + underground, which is baseline-rotted from ev0), (b)
  escalates the **ambient air** to match (`_apply_ambient_air`:
  `drip`/`flies`/`whisper` + `rot_throb` by stage, same SAFE_SCENES-at-3
  rule as the decals; DESIGN.md §11). **The people do NOT change**
  (2026-07 rework, TODO #22c): the town stays visually ordinary end to
  end. The old people-transform layer was CUT —
  `_convert_local` / `_turned_local_dialogue` / `ROT_TURN_LINES` /
  `_rot_locals` / `_spawn_counter_eater` and the `ROT_CONVERT` / `ROT_TURN`
  config are gone (as was the earlier `_mutated` body-horror overlay —
  `draw_infested_overlay` / `_draw_infested_portrait` / the `infested=True`
  `show()` path — TODO #9; `sprites_wound.py` keeps only the shared
  `_gold_in_wound` helper the corpse art still uses). What rots now is the
  **investigator**: the four-tier conversation framing
  (`_pi_tier` / `_pi_framing` / `_PI_WEATHER` in `scenes/dialogue.py`) keyed
  to evidence (0 / 1-2 / 3 / 4+) gives each principal's opening framing the
  PI's deepening interior weather while the NPC's own words never change —
  the wrongness is the *place* and the man hearing it, never the people
  (NARRATIVE §2/§6, DESIGN.md §9).
  Sheriff Vane is exempt from the rot pass: his fall is
  **player-driven (TODO #2a, 2026-07)** — a hidden despair/hope ledger
  (`vane_despair`, the `VANE_*` config block; `_vane_ledger`/`_vane_share`
  in `scenes/dialogue.py`) surfaced only as his MOOD (the convo's framing
  line + the beats, never a number). Sharing a discovery with him is both
  the hope currency and the TRUST that opens his blind-cultist thread; the
  preacher's murder (+1) and the newspaper give (+2, his break lever) are
  the despair acts; net `VANE_HOLLOW_AT` (3) **latches `vane_hollow`**
  (once hollow, no return), and the **neglect override**
  (`_vane_is_hollow`, rot_mixin) hollows him regardless at 3 evidence
  with fewer than `VANE_MIN_INFORMED` (1) discoveries shared. Once
  hollow, the next office load turns it into a **unique threat**:
  `_spawn_hunting_sheriff`
  (`sheriff_hollow` sprite) holds for an intro beat then force-chases
  (`_tick_sheriff`); contact → `_trigger_death("sheriff")`; the spawn is
  skipped if the player already killed Vane (dead locals stay dead — his
  body holds the office). Guarded by flow §17f. Player-killed
  locals are drawn by `draw_npc_corpse` at **`mold=0`** (a clean fresh
  kill) — the body persists across loads (the `dead_locals` ledger) but
  no rot stage accumulates on it. (`draw_npc_corpse` still *accepts* a `mold` 0..3 and
  the fold-claim art — `_CORPSE_CLAIM` for named resisters, `_CORPSE_ECHO`
  compulsion echoes — survives in `sprites.py` as reusable art, just no
  longer driven by an accumulating stage.)
- A pursuer reaching the player triggers the **death** sequence
  (`_trigger_death(kind)` → `_tick_death`). **THE TALK (2026-07): the
  FIRST cult grab of a run is a warning, not a capture** — `_cult_talk`
  (threat_mixin) plays the courteous one-liner, stands the room down,
  grants a short re-grab grace, and files a NOTE (flag `cult_talk_given`;
  gates every grab site, struggle losses included). After that,
  `kind="cultist"` shows the **CAPTURED** card (taken alive for the
  hive); `kind="sheriff"` the
  **TAKEN INTO CUSTODY** card (the hollow lawman); `kind="king"` plays the
  **Carcosa** mask-furnace cutscene. All end the run and return to title.
- **The calling-out (2026-07):** Mara kneels among the Sign Chamber
  congregation (`works_sign`, set-piece NPCs, no cult tag). First entry
  stages it (`_call_out` trigger + `_sign_update` in `scenes/well.py`):
  the kneelers rise, one says her name, she walks to the player and her
  canon-guarded exchange fires (Mara is **proof, not evidence** since the
  TODO #22 rework: the calling-out still fires but no longer counts toward
  the gate; the deep hive `dark` keeps a nameless congregation). Flow §28b
  guards it.

## Conventions & gotchas

- **Open canon-alignment work lives in `TODO.md`.** A 2026-06 narrative-
  alignment pass settled a batch of story decisions; the **code changes to
  make the game match** were tracked in the former `GAME_CHANGES.md`, now
  **folded into `TODO.md`** (2026-07) with its open items tagged
  `(was GAME_CHANGES §N)`. `NARRATIVE.md` is the **story bible** and the
  canon source of truth (rewritten 2026-07: it locks FACTS, never
  phrasings; states what IS, not what isn't; one fact, one home; canon
  invariants indexed at the bottom). The systems/design material that
  used to live in it (threat-model canon, world rot, the implementation
  map, the Works level design, art direction, fold mechanics) moved to
  **`DESIGN.md`** — code comments cite `NARRATIVE §n` / `DESIGN.md §n`
  in the NEW numbering.
  Highlights that override older code/comments: the
  **Ledger is the boxed old registers in the PADLOCKED Lodge cellar**
  (2026-07 rework, superseding the 2026-06 front-desk placement: the
  cellar key hangs on a nail behind the house, the desk keeps the
  sign-in register + the lead pointing down; Sable himself never points
  at the cellar), **Mr.
  Sable is the most-attuned *local*** (not a newcomer), the **Playscript is
  the cult's own notes**, and the **Deep Stair no longer consumes the
  keystone** (Mask + notes are carried down and spent at the Threshold to
  SEAL). **The rope is CUT (2026-06, §14): the descent is the RITE** — at 3
  evidence Sable hands over the Invitation (`rite_envelope`), the school
  rite (incense + the final chalk door) opens the school↔grove fold, and
  the grove's **descent fold** (clarity = evidence count via
  `Scene.fold_charge_fn`; crossable at 3 via `Scene.exit_gate_fn`) lands at
  `well_bottom`. **§15 rework:** the crossing is opened by the GROVE
  RITE (the full door-dream, cutscene only, two-press); the circle then
  holds you and the way home is **keyed to the Mask** (crossing up sets
  `descent_sealed`, the SPREAD lock). The **Deep Stair is CUT**: the way
  deeper is the **blast** at the deepest face (`powder` from the Sump,
  Mask in hand, two-press) → the one-way FALL into the Depths. The
  Brimley well is dread set-dressing; the Ledger's checkout dates stop
  **a year** back (flow-guarded). Check `NARRATIVE.md` (and `TODO.md` for
  open work) before touching the cast, the ledger, the fork, the descent,
  or the face.
- **Teleportation is consolidated — one primitive, don't add bespoke
  paths.** Doors/ladders fade (`begin_transition`'s fade path);
  EVERY other traversal — seamless world edges, direction-gated fold
  exits (these now route straight through `cross_fold` whatever scenes
  they join, so a fold can cross surface↔underground), the maze's
  same-scene `I`/`Q` relocations, and the King's rift juke — funnels
  through `Game.cross_fold` (`systems/game.py`): no fade,
  no sting, stride/look/screen-position preserved. The crossing is
  deliberately nothing; the FRAME is the spectacle. Visible folds + the
  King's portal share ONE anchored frame renderer
  (`rendering/portal.py draw_rift_door`: pane stands along its world
  seam, foreshortens like a wall, thins to nothing off-angle). Same-scene
  folds are SILENT (skipped by `_build_fold_cache` — the lie is the world
  itself). One-way is the King's signature alone. See DESIGN.md §7 "One
  phenomenon, two presentations" + DESIGN.md §7 "Decisions landed". Live
  proof sheet: `tools/preview_rift_anchored.py`.
- **No day/night cycle** — it was removed; everything reads as one
  (daytime) state. Don't reintroduce `day_phase` / `day_count`.
- **Scene-gating sets**: `SAFE_SCENES`, `DARK_SCENES`, `OUTDOOR_SCENES`
  drive King safety, flashlight darkness, etc.
- `visibility` persists across scene loads (only `_reset_run_state`
  clears it); `_king`, `_watchers`, and hide-state are cleared on every
  `load_scene_now`.
- Sprites are 100% procedural — no art assets to edit.
- **Adding a new decoration/prop kind under the tilt** (the dispatch map from
  the retired HANDCRAFT_BACKLOG): register it in exactly ONE set or it renders
  as a flat stain on the floor. `FURNITURE` / `SOLID_PROPS` = a real projected
  volume; `_STANDEE_KINDS` (`props.py`, `scenes/terrain.py _tilt_standee`) = a flat
  card stood up; `_WALL_DECO_KINDS` = hung on a wall; `_FLOOR_DECAL_KINDS` /
  `_SURFACE_DECAL_KINDS` = warped flat onto the floor/surface plane;
  `_TABLETOP_PROP_KINDS` (+ `seat_tabletop_props`) = seated on furniture. A kind
  that must stay ANIMATED needs a LIVE solid fn (standee cards freeze at t=0).
  Verify with a `tools/capture_world.py` tilt capture before/after.
- **SCENE-DRESSING PROCESS (2026-07 — five failures were caught by the
  maintainer in one session; every one traces to skipping a step below.
  Follow ALL of it before placing a single detail):**
  1. **PROVENANCE.** Every detail answers: who made or carried this, with
     what tools, why HERE, why does it remain? Place by WORK FLOW (haul
     heads get spoil, portal mouths get shoring, dead faces get downed
     tools), never by vibes. An obsessive dig runs no craft room; the
     willing bleed nobody; nothing underground was made on a lathe.
  2. **NEVER PLACE A KIND BY ITS NAME.** Render it first
     (`tools/preview_props_sheet.py <kind> ...`): "pillar" was a fluted
     Roman column, the `'s'` "shelf" tile a bookcase with colored book
     spines, "husk_bundle" a stalagmite-shaped pale cone.
  3. **DESIGN FOR THE PROJECTION.** Man-made things are flat-sided
     yaw-rotated boxes/quads (a smooth body of revolution reads as a
     lampshade); the parts that IDENTIFY the object (wheels, a tied
     waist, board seams, a crossbeam) must be visible from the fixed
     camera, not hidden under the volume.
  4. **MISTAKEN-IDENTITY TEST.** Say out loud what else the silhouette
     could be (especially natural-vs-man-made collisions). If it
     collides, restyle before placing.
  5. **VERIFY AT THREE ALTITUDES, THEN IN THE DARK.** Isolated contact
     sheet (vs a wall-height ruler) -> room crop with actors stripped ->
     live room -> the SAME shot with the darkness/aperture ON. Players
     never see the brightened debug view; detail must survive
     candlelight or sit beside a light source.
  6. **PLACEMENT.** Never on walking lanes or cover weave gaps; solid
     footprints re-checked with smoke's flood-fill (hides + exits
     reachable) BEFORE the full gate.
- `__pycache__/` is gitignored; never commit `.pyc`.

## The journal door-dream + "He knows you" (NARRATIVE §4)

- **Trigger (two-stage since the §15 rework):** reading `mom_notebook`
  (Mara's journal) a third time sets `flashback_pending`
  (`ui/inventory_ui.py`); `Game._tick_flashback` polls it, sets
  `flashback_seen`, and fires a ~0.5s MEMORY FLASH (two flickers of the
  door, no swarm; `FLASHBACK_FLASH_DUR`). The FULL ~7s wordless dream
  (`_draw_flashback`, mode "rite") plays at the GROVE RITE via
  `begin_rite_dream` — completing it opens the descent fold
  (`rite_performed`) and also sets `flashback_seen`. `_tick_flashback` lives in `systems/narrative_mixin.py`;
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
  King-gate + world rot; only the five `CANONICAL_EVIDENCE` beats of Mara's
  trail (`maras_receipt`/`maras_record`/`maras_journal`/`maras_dig`/`maras_room`;
  NARRATIVE §6, TODO #22) belong there — the bear is an optional non-counting
  item, and the Ledger/Preacher/dream file as notes. At the real Threshold (`scenes/depths.py build_threshold`
  `on_enter`), if `flashback_seen`, a recognition line lands before the
  doorframe beat: *"You have stood here before. In sleep."*

## Working agreements (process — learned the hard way)

- **"Push to main" MEANS MERGE TO MAIN.** When the maintainer says "push to
  main" / "PR and push to main", that is an instruction to open the PR **and
  merge it into `main`** in the same action — not to stop after creating the
  PR and ask. Don't ask for a second confirmation.
- **Verify before you commit.** Run compile + `python tests/run_all.py` (the
  full gate: smoke + flow + stealth + fold_pursuit + king_roam + render_smoke) and confirm green
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
  the Kid is **Toby** (sprite/portrait/dialogue kind `toby`), not "Village Kid".
- **Previewing visuals headlessly:** render to PNG/GIF with
  `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` + Pillow (installable) and
  send with the file tool. For whole-screen cutscenes, step
  `_tick_flashback` / `_draw_flashback` in a loop and capture
  `pygame.image.tostring`.
