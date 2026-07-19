# THRESHOLD — Claude guide

> **HARD RULE #0 — READ THE CANON IN FULL, EVERY TIME, BEFORE YOU ANSWER.**
> Before responding to ANY request about THRESHOLD — a question, a review, a
> design chat, a one-line edit, anything — you MUST read **`CLAUDE.md`,
> `NARRATIVE.md`, `DESIGN.md`, `TODO.md`, `DIALOGUE.md`, and `VISION.md` IN
> FULL**, from top to bottom, in this same turn.
> Not a section. Not a grep. Not "I read them earlier." Not from memory or a
> summary. All six, whole, every single time, no exceptions. Treat your
> memory of them as STALE by default — the docs are the only source of truth,
> they change, and answering from a half-remembered version is how canon gets
> broken (it has been, repeatedly). If you have not read all six this turn,
> you are not ready to answer: read them first, then answer. This is the
> project's non-negotiable first step; do it automatically, never wait to be
> asked, and never announce you are "about to" instead of doing it.
>
> **The six-doc canon.** This file (`CLAUDE.md`) is the project's entry
> point and operating guide, and now the first of the six you read in full;
> the other five named above are the rest of the canon:
> - **`NARRATIVE.md`** — the story bible: premise, lore, cast, place, the
>   evidence trail, the endings, and the canon invariants. The source of
>   truth for anything the fiction asserts.
> - **`DESIGN.md`** — every game system and its code map: the threat model,
>   world rot, the fold, the tilted camera, audio, stealth, the Works level,
>   and art direction.
> - **`TODO.md`** — the live list of genuinely open work. Not a place for
>   lore.
> - **`DIALOGUE.md`** — the dialogue & narrator bible: every word the player
>   reads (spoken NPC/PI lines and narrator/world boxes), organized by WHO
>   says what and WHAT causes what, plus the voice rules. **Its contract:
>   the code and `DIALOGUE.md` are ONE — any change to a player-facing line
>   in code is a change to `DIALOGUE.md` in the SAME commit, and the reverse.
>   A disagreement between them is rot.**
> - **`VISION.md`** — see it, don't guess it: the one rule that when you
>   change, dress, or judge how a scene LOOKS, you render it and LOOK (all
>   four facings for your own check; one angle when you show the maintainer)
>   instead of trusting the code. Plus how to capture.
>
> These six files are the ENTIRE doc canon. The old per-topic docs
> (`CAMERA.md`, `PORTALS.md`, `STEALTH_REWORK.md`, `AUDIO.md`, and the two
> audit files) were folded into them and deleted (2026-07), so every design
> or story reference now lives in one of these six. When you change a canon
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
  NarrativeMixin, TableauMixin)`) — they are
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
  - `systems/tableau_mixin.py` — the **close-up examine tableaux**
    (`_open_desk_tableau` / `_tableau_input` / `_draw_tableau`): a modal
    close-up of a prop with a menu that mutates it live (take the gun off the
    desk, read the case file), the world frozen while it is up. Art (the
    procedural close-ups) lives in `ui/tableau.py`; the pilot is the bedroom
    writing desk. The **face-across-a-table principal talks** ride the same
    frame (2026-07, all six principal seats): `clerk_dialogue` /
    `sheriff_dialogue` / `hettie_dialogue` / `preacher_dialogue` /
    `toby_dialogue` / `_mara_voice` open the talk as a tableau (the
    `_open_*_tableau`
    openers + `open_conversation(..., tableau=True)`), the conversation's
    beats render as the caption and its menu as the option panel
    (`_convo_tableau_input`), and the art reads save flags so the close-up
    carries what the talk earned (Sable's photo/Invitation on the register;
    Vane's pose reading his despair ledger, the given paper, the opened
    cabinet; Hettie's door-glance idle, the tab leaving the spike, the
    traded paper; Crane's hands folding or gripping the lectern on the press
    fork; Toby's corn-line watch, the procession drawing, the brows the
    promise levels). **MARA is the last seat and carries the REVEAL**
    (2026-07): the calling-out confrontation opens with her masked and
    hooded, one of the congregation, the caption LISTING her "One of them"
    (`MARA_CONVO["name"]` is a callable), until the greet's `("do", ...)`
    beat (`_mara_unmask`) pulls the carved mask off — the face from the
    photograph, gone thin — and the listing turns to her name; her captions
    page on Escape (the reveal can't be skipped), and the art reads
    `mara_lucid` (raised bleeding palms) / `mara_named` (her fist on the
    PI's coat, the rank stirring). The conversation engine grew `("do",
    fn)` beats + callable `name` for it, and `load_scene_now` now drops a
    stale tableau alongside the convo. The chorus still floats its talk
    (the `tests/flow.py`
    §26 float guards ride Royce). **THE TALK rides the frame too** (the tone
    inversion: `_cult_talk` → `_open_talk_tableau`, a scripted caption chain,
    not a Conversation — the grip close-up, the one reach-for-the-revolver
    choice, Escape pages instead of aborting). **THE PEDESTAL** (the Sign
    Chamber altar, `_open_altar_tableau`) is the OBJECT close-up of His face
    on the stone: LIFT the Mask (keystone + temptation) or TEAR IT DOWN
    (BREAK → `_play_ending("rite_broken")`), Escape backs out. All #2b
    seats ship. **The #2b sound pass (2026-07)** gave every close-up its
    soundscape: `lean_in` on open (the world holding its breath) + a
    per-seat ROOM TONE looped while it is up (`_TABLEAU_TONES` here,
    `Audio.room_tone`; the world-freeze had left the frames in dead
    air). Mara's seat stays silent by design (`_mara_voice`
    force-silences the room). See `DESIGN.md` §11. Player-facing text is
    in `DIALOGUE.md` Part B.
- `scenes/` — `SCENE_BUILDERS` registry + `load_scene(key)`
  (`scenes/__init__.py`, ~47 scenes). A scene has spawns, exits,
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
    The vanish is only honest when the door doesn't lie: spawn with
    `_hb_vanish=False` (a `_resident(..., vanish=False)` arg) for a
    homebody at an ENTERABLE-but-empty building (Old Pell's schoolhouse
    step) so it keeps its step instead of disappearing into a room the
    player can walk into and find empty. Hettie keeps `vanish=True` — her
    shop interior holds a Hettie.
    `worker` (2026-07, the JOBS layer) walks a personal
    `npc.stations` route — travel, dwell facing the work, next — on
    the cult's errand machinery (`stealth.errand_step`; Garrick,
    Royce, the store Hettie, Rev. Crane). `chaser` runs the cultist state
    machine (`_cult_tick`: scout→chase→search→investigate). SCOUT carries
    the **cult-liveness beats** (TODO #23a; `systems/stealth.py`
    `sync_pause`/`handoff_step`, `CULT_SYNC_*`/`CULT_HANDOFF_*` config):
    the shared-clock synchrony all-stop and the crossing hand-off —
    dressing that never touches the threat states (a frozen scout still
    fills suspicion; `tests/stealth.py` §12 guards it; DESIGN.md §12).
    The `yellow_king` sprite short-circuits to `_yk_update` (the `_birth`
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
    `draw_world` gates what is **drawn** (NPCs, enemies, corpses, and
    the world-rot decals — flagged `_sight_gated`) to a forward sight
    cone keyed to `look.aim` and clipped by `Scene.blocks_sight`, via
    `visible_factor(...)` → a soft-alpha fade (`draw_with_alpha`). The world
    keeps **simulating** off-camera (the update path is untouched); unseen
    things simply aren't rendered and **re-hide** when you look away (no
    last-seen memory). The **King is exempt** (relentless apex); the player is
    never gated. **Pickup items are exempt too** (`_vis_alpha(..., exempt=True)`)
    — they always READ as existing in the world (they were tiny + easy to
    miss) and are added to the occlusion **focus** set, so an occluding
    wall/prop **fades** for a gem the same way it does for an actor rather
    than hiding it under the tilt. All gating sits behind `_sight is not None` (always live now, since the
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
    builds from `DEFAULT_SAVE`; the ONLY writer of the slot is now
    **evidence pickup** (`Game._autosave`, play-notes: the clue IS the
    checkpoint, not a trip to the cot): it snapshots hp/inventory/current
    scene + a COOLED visibility (halved, so a reload never lands in a
    maxed-out death), atomic write to `~/.threshold` /
    `%APPDATA%\THRESHOLD` (`THRESHOLD_SAVE_DIR` overrides for tests), and
    fires from `_evidence`'s canonical branch (`scenes/dialogue.py`).
    Continue reads it back and **wakes at the scene the last clue was
    found in** (its `default` spawn); a death or a quit costs everything
    since the last clue, never the run. The **cot** (`Game._sleep_at_cot`)
    is now a pure **REST** (heal + visibility cool), NOT a save. Killed
    innocent **locals stay dead for the run** (2026-07 ruling): the kill is
    written to the `dead_locals` save arg (`_record_dead_local`) and
    `_apply_dead_locals` (run from `load_scene_now` before the rot pass)
    lays the body back down where it fell on every re-entry. New Game
    clears it; the autosave snapshots it like any arg (NARRATIVE §5 /
    DESIGN.md §1; flow §27/§32).
  - `items.py` — `ITEM_DEFS`, `Inventory`.
  - `threat.py` — `proximity_tier` + `PROX_TIER_*` helpers.
- `ui/` — dialog, the Casebook, fonts, text input. **The Casebook is ONE
  book now (2026-07 merge):** the old split Inventory (I) + Case Notebook
  (N) were fused into `ui/journal_ui.py` (`JournalUI`), a single tabbed book
  — **Case** (the working theory + timeline + clues + interior notes),
  **Tools** (axe, gun, keys, flashlight), **Papers** (Mara's journal +
  letter, the records, the cult testimony, the Mask). Both `I` and `N` open
  the SAME book (N lands on Case, I on Tools; pressing the ribbon you're on
  closes it); left/right turns the tab, up/down walks the index, Enter reads
  or takes in hand. `game.inv_ui` / `game.notebook_ui` are kept as **aliases**
  onto the one `game.journal_ui`, so old call sites (draw gating, tests)
  still resolve. Note titles for save slugs live in `ui/case_titles.py`
  (`humanise`), shared by the book AND the corner scribble toast. The dead
  combat-era "Consumables" tab is gone. **Writing to the case book fires the
  corner scribble toast** (`_flash_notebook(name)` → `_draw_notebook_toast`
  in `render_mixin`): a small leaf the PI scribbles a beat onto, now NAMED
  (the humanised title beside it) so the player knows what was recorded —
  the one reliable per-write tell. EVERY note/evidence write flashes it now
  (the module `_log_note`, `the_ledger`/`the_preacher`, and the revisit
  notes used to file silently — a bug). **Dialog is
  three channels:** `dialog.py`'s modal band survives ONLY
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
  decay). **The stealth economy (2026-07 first human tuning pass,
  DESIGN.md §12, stealth §13):** the speed ladder is King > sprint >
  locked chase (`CULT_CHASE_MULT`) > walk > scout, sprint in LOS
  multiplies the detection score (`SUS_SPRINT_MULT`), every grab site
  reaches `CULT_GRAB_REACH`, cover entry is WORDLESS (the teach notices
  are cut), and bare `:` cover tiles render as tall-grass tufts under
  the tilt so concealment is visible. **River stones** (`STONE_*`,
  item `stone`, right-click) are the placed-noise distraction verb:
  they turn idle scouts, never divert a sighting-born search -- except
  through a WINDOW (`GLASS_*`: the smash diverts even a search, and the
  pane stays broken for the run, the `broken_windows` ledger) -- and a
  stone dropped down the dead well rattles the whole square with no
  bottom ever sounding (`WELL_ECHO_*`; stealth §14). The **hollow Sheriff**
  (`_force_chase`) is **exempt** — it bypasses
  suspicion and cover entirely. The roaming **King** honors `player.hidden`
  (corn OR an enclosed hide drops his hunt to searching, `tests/king_roam.py`);
  he is relentless in re-finding you, not in seeing through cover. Guarded
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
  cult wakes (patrols spawn). **Cultist spawn geography (2026-07):** a cult
  scene keeps `Scene.cult_target` roamers filled (default `CULT_REGULARS` 2),
  spawning them at the farthest unoccupied point in `Scene.cult_spawns` (a
  hand-placed spawn-anchor pool) else the map corners — `_spawn_cultist(...,
  from_pool=True)`. On the first awake tick after a load the scene is
  PREFILLED straight to target (`_cult_prefilled`, reset per load) so it reads
  populated the moment you enter; killed cultists then respawn one at a time on
  the `CULT_TOPUP_INTERVAL` breather. **Brimley** sets `cult_target = 10` over
  **14 anchors** (9 spread + a 5-strong crew at the SE cult camp), all
  evidence-gated like any patrol. **Ev 2** (`KING_TURNS_HEAD_EV`): his
  attention finds YOU — a single SEEKER moth materialises in the player's
  room every `MOTH_SEEK2_*` (2-3 min; `_tick_moth_seek`, never at a door,
  drops in on the `"b"` arrival ramp), AND a one-time telegraph note lands
  (`the_turning`, `_tick_king_roam`): he has **turned his head** toward you
  but has not moved — the ramp's "he sees you" beat so ev3 is not an ambush
  (play-notes). **Ev 3**: he walks (the roam arms) — but the world **holds
  its breath** first: `KING_ARM_GRACE` (~25s) where he stands far and does
  NOT close (`arm_grace` in `_roam_king`; the `the_breath` note fires), the
  window to reach the lodge for the Invitation before the hunt begins
  (decouples the spike from progression). Then his shedding starts and the
  seeker slows to `MOTH_SEEK3_*` (5-6 min).
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
- **The Watchers** (His gaze made manifest; the play-notes rework made them
  **THE below-3 threat**, `_tick_watchers`/`_apply_curse`). From
  `WATCHER_WAKE_EV` (1) evidence, while you are **exposed** (in the open, not
  in cover / a safe room), the domain **opens** a Watcher on a timer:
  `WATCHER_GRACE` (6s) before the FIRST of a wave (and after you clear one),
  then the **evidence-scaled** interval between the rest
  (`_watcher_spawn_interval`: `WATCHER_SPAWN_BASE` shaved per further
  evidence down to `WATCHER_SPAWN_MIN` — the King floods them deep). Each live
  Watcher **HOLDS you while you are exposed and drives visibility UP** by
  `WATCHER_GAZE`/s (the active climb — `_watcher_gaze`, the main visibility
  driver below the cult), on top of a small residual `WATCHER_FLOOR` (summed,
  capped `VIS_FLOOR_TOTAL_CAP` 0.92, just under the King). Ignore them and it
  **snowballs** (more open, faster); it caps at `WATCHER_MAX` (5). You clear
  them (`_dispel_watcher`): hold one in your **gaze** `WATCHER_GAZE_DISPEL` s
  (its eyes go dark, then it dissolves), or the **axe** / a **round**.
  **Cover pauses the spawn timer and drops the hold**; `SAFE_SCENES` /
  `KING_FREE_SCENES` suppress them (re-form on the way out); a rift fold has a
  `FOLD_WATCHER_CHANCE` to open an extra. **The gaze OPENS under the open sky,
  in the deep, AND in a DARK non-refuge interior ("no light = danger", TODO
  #21; `WATCHER_OPEN_SCENES` now folds in `DIM_INTERIOR_SCENES`):** in those
  dim rooms exposure is being in the DARK, a light POOL (`Scene.lit_at`) or
  the flashlight is the cover, and a Watcher caught in a pool / the beam
  **BURNS** out (`WATCHER_LIGHT_BURN`). The **true refuges stay gaze-free**
  (`SAFE_SCENES` are excluded + `KING_FREE`); a plain interior outside both
  sets is gaze-free too (`tests/stealth.py` §11). (The old GAZE_BIND
  high-visibility trigger is retired.) The gun and axe **share one weapon slot** (left-click
  to use; switch which is equipped from the inventory screen).
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
  (threat_mixin) plays the courteous warning as the **grip close-up
  tableau** (`_open_talk_tableau`, art `ui/tableau.draw_talk_tableau`;
  one reach-for-the-revolver choice if the PI carries it, Escape pages
  instead of aborting), stands the room down, grants a short re-grab
  grace, and files a NOTE (flag `cult_talk_given`; gates every grab
  site, struggle losses included). After the Talk, the
  cult grab is **TWO-TOUCH** (play-notes): the FIRST grab of an encounter
  shoves the PI free (`_cult_shrug_off` — grabbers stagger `STRUGGLE_STUN`,
  he tears loose on a `STRUGGLE_BURST_T` burst with `CULT_SHRUG_INVULN`
  grace); only a SECOND grab before he reaches a `SAFE_SCENE` is the
  capture (`_cult_touch_count`, reset on a safe-scene load, no time decay,
  so a swarm or a corner still takes you). The cult CAPTURES, it does not
  kill. Then `kind="cultist"` shows the **CAPTURED** card (taken alive for
  the hive); `kind="sheriff"` the
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
- **Interior doors — the subroom divider (2026-07, DESIGN.md §7).** The
  third door kind, and NOT a teleport: a swinging leaf on a floor GAP in a
  wall line WITHIN one scene, the tool that splits a box building into
  several subrooms. State on `Scene._inner_doors`; author with
  `Scene.add_inner_door(tx, ty, kind, open=False)` on a floor tile inside a
  wall run. A shut leaf behaves like a wall (hooked into `is_solid_at` +
  `blocks_sight` — so it occludes AND breaks a pursuer's line of sight,
  buying time; the same `blocks_sight` `clear_sight_line` runs, one hook for
  render + cult AI), open passes both; `_nav_solid_at` never counts a door
  tile so NPCs route AT it and open their own way through. `Scene.update`
  runs the open/close (most start CLOSED; an NPC nearing a shut door opens
  it, it swings shut a beat after the last actor leaves); the player toggles
  the nearest with **E** (`toggle_nearest_inner_door`, last in
  `try_interact`). Kinds: `plank` (opaque wood) / `bars` + `half`
  (see-through, block the body but not the sight cone — `_SEE_THROUGH_DOOR_KINDS`)
  / `curtain` (drape). Draw: `rendering.props.draw_inner_door`, emitted +
  depth-sorted in `draw_world`'s tilt pass. **Vary the wall**: `ew` (the swing
  axis) is derived from the tile's wall neighbours, so a door in a SIDE (N-S)
  wall opens E-W and a door in an E-W wall opens N-S. Don't put every door of a
  building in E-W walls or the leaves all "face south" (error class #8); mix
  side-wall and E-W-wall doors by what the geometry wants (the shop does).
  Guard: `tests/stealth.py` §15.
- **Interior partition corners are BEVELED (2026-07, `scenes/terrain.py`,
  DESIGN.md §6).** A wall tile's exposed CONVEX corners (both adjacent faces +
  the diagonal open to floor `.`) are chamfered in BOTH wall draw layers —
  `_extrude_box` (a `bevel` bitmask param from `_bevel_corners`) and
  `_draw_wall_mass` (clips `_wall_tile_flat` to `_bevel_poly_local`) — so the
  chunky 90° jut softens while runs/tees/shell stay a full-thickness continuous
  mass (byte-identical, no convex corner there). Draw-only; gated to
  `_BEVEL_SCENES` (frozenset of the above-ground building interiors — shop,
  church, barn, schoolhouse, sheriff_office, bedroom, clerk/guest rooms, lodge +
  lodge_hall, toby_house, farmhouse, lodge_cellar — never the mine or outdoors).
  `_BEVEL_INSET` = 0.28·TILE tunes the chamfer. Cache-safe (pure function of
  tile + neighbours).
- **No day/night cycle** — it was removed; everything reads as one
  (daytime) state. Don't reintroduce `day_phase` / `day_count`.
- **Scene-gating sets**: `SAFE_SCENES`, `DARK_SCENES`, `OUTDOOR_SCENES`
  drive King safety, flashlight darkness, etc. `DIM_INTERIOR_SCENES` (2026-07)
  is a `DARK_SCENES` subset for the explorable non-refuge interiors: a LIGHTER
  gloom (72) so a ground-floor room reads dim-lit-by-bulbs, not pitch-black
  (`_draw_dark`); lit by the genset `wall_lamp` fixture (DESIGN §6).
- `visibility` persists across scene loads (only `_reset_run_state`
  clears it); `_king`, `_watchers`, and hide-state are cleared on every
  `load_scene_now`.
- Sprites are 100% procedural — no art assets to edit.
- **Adding a new decoration/prop kind under the tilt** (the dispatch map from
  the retired HANDCRAFT_BACKLOG): register it in exactly ONE set or it renders
  as a flat stain on the floor. **And never place furniture as a raw OBJECT
  tile** (`t`/`b`/`c`/`k`/`f`): the tilt occluder scan only draws
  wall/door/window/billboard/counter/rack chars, so a raw furniture tile is an
  INVISIBLE solid under the only shipping camera (2026-07 audit: 13 such
  phantom blocks, incl. the lodge fireplace and the Scriptorium's evidence
  desks). Use `add_furniture` (a real volume + footprint); smoke [9/9] now
  fails any scene that ships one. `FURNITURE` / `SOLID_PROPS` = a real projected
  volume; `_STANDEE_KINDS` (`props.py`, `scenes/terrain.py _tilt_standee`) = a flat
  card stood up; `_WALL_DECO_KINDS` = hung on a wall; `_FLOOR_DECAL_KINDS` /
  `_SURFACE_DECAL_KINDS` = warped flat onto the floor/surface plane;
  `_TABLETOP_PROP_KINDS` (+ `seat_tabletop_props`) = seated on furniture. A kind
  that must stay ANIMATED needs a LIVE solid fn (standee cards freeze at t=0).
  Verify with a `tools/capture_world.py` tilt capture before/after.
  **A LIGHT-emitting kind lives in TWO tables (2026-07 lighting pass):**
  `Scene._LIGHT_KINDS` (`scenes/base.py`, the MECHANICAL pool radius the
  stealth `lit_at`/shadow-cover gate reads) AND `FIXTURE_POOLS`
  (`systems/render_mixin.py`, the VISIBLE light `_draw_dark` casts in a dark
  scene: `radius, color, peak, src_z, arm, flicker_amp, flicker_speed`).
  `_draw_dark` iterates EVERY emitter through `FIXTURE_POOLS` (not just
  `wall_torch`), so a fixture missing from it will read + gate as lit but cast
  no visible light in the dark. `src_z` is the light source's real world
  HEIGHT and `arm` its gooseneck offset: the pool is a tilt-squashed ELLIPSE
  cast on the floor UNDER the 3D source, pools blend ADDITIVELY (they combine
  + lift the objects they lie on), and solid casters throw SUBTRACTIVE cast
  shadows away from each source (DESIGN §6, the 3D light-interaction model).
  Cold electric (`yard_light`) vs warm fire is a colour choice in that table.
  **Prefer a real `SOLID_PROPS`/`FURNITURE` volume over a standee card for
  MAN-MADE things** (they read as flat cards that swivel to face the camera
  otherwise; the sprite-depth-anchoring pass converted `standing_stone` /
  `wheelbarrow` / `pedestal` / `corn_altar` / `butter_churn` / `washstand` /
  `birdcage` / `steeple` / `radio` / `wrong_radio` / `church_bell` / `valve`).
  Standees stay right only for genuinely organic/thin things (trees, grass, the
  corn-husk effigies, a doll). A tall solid at a building's centre is buried by
  its own opaque 3D roof (the roof depth-sorts after it); the escape hatch is
  the per-prop **`depth_bias`** kwarg (read in `render_mixin`'s solid-emit;
  defaults 0) plus a `rise` so the prop grows OUT of the roof (the Brimley
  `steeple` uses both).
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
- **PLAYTEST ERROR CLASSES (audit for these BEFORE calling a scene, interaction, or
  line "done" -- a 2026-07 play-test surfaced every one of them, and each is a CLASS,
  not a one-off).** When you touch anything nearby, actively hunt the whole class
  (a grep/preview that catches all of a kind beats fixing one instance):
  1. **Wrong interaction verb.** Evidence and pickups are **walk-over ground items**
     (`scene.add_item` + the auto-pickup path), NOT an `[E]` proximity prompt. An `[E]`
     cue is only for readables/handoffs that must run a side effect the auto-pickup loop
     can't. When you see a new `add_interactable` / `_pos` readable, ask "should this just
     be a pickup?"
  2. **Side-effect fires on the wrong beat.** A note/dream/pointer must trigger on the
     event the fiction names (the door-dream ON PICKUP of the journal, not the 3rd read;
     the desk-pointer only after meeting Sable; never write a case note before the PI has
     actually read the thing). When you add a trigger, state the exact beat it fires on
     and verify it.
  3. **Mechanics in player-facing text.** No name/description/note/caption may state a
     game rule, a verb, or an evidence threshold (the old revolver "3+ evidence", the old
     moth note's "kill them quiet" tail, cut in the 2026-07 dialogue audit). State the
     FICTION; never the system. (Companion to
     the no-dashes HARD RULE: player-facing strings are held to a higher bar than code.)
  4. **Editorializing / over-written captions.** A narrator beat states the fact and
     stops; it never spells out the conclusion the player is meant to draw, and a routine
     action (a key, a body, a prop) never becomes a long unstoppable blob. If a beat wants
     a close-up it earns a mini-cutscene, else it is a terse line or nothing.
  5. **Knowledge the speaker can't have.** No PI or NPC line may assume a fact the player
     hasn't earned; testimony must not STATE the cosmology the game is built to make the
     player infer (what the door promises, "what do you want most").
  6. **Raw markup leaking as text.** `[c=...]` / `[/c]` and any style token must be
     stripped on EVERY render path (notebook, scribble toast, caption), never printed
     literally.
  7. **Tilt-projection artifacts.** A prop must be in exactly the right tilt set (a
     man-made thing is a `SOLID_PROPS`/`FURNITURE` volume or a `_WALL_DECO`, never a
     swivelling standee); portals stand on a seam with **no reachable back and no floating
     bottom frame**; wall decos and doors occlude honestly. Preview before placing (the
     SCENE-DRESSING PROCESS above).
  8. **Scene-geometry defects.** No NPC home/spawn on a door tile or its single approach
     tile; a door **replaces** a wall segment, it is not a hole punched inside one; no
     missing walls; no walkable water the fiction says is a barrier; break the grid
     lockstep (no perfect straight prop rows); decorate more than just the one north wall
     face; beds/furniture sit in the room's back, not across the door. **VIEW EVERY ROOM
     FROM ALL FOUR N/E/S/W FACINGS before calling it done** (`tools/capture_world.py` per
     facing) -- most of these hide on the one facing you happened to check.
  9. **Threat pacing.** Speed ratios are intentional (player sprint below the King so a
     locked apex can't be outrun but CAN be hidden from); pursuit rules, apex spawn
     placement (never on the player's exit tile), and monster visibility/design must
     preserve dread rather than expose it. Re-derive the ratios whenever you touch a speed.

## The journal door-dream + "He knows you" (NARRATIVE §4)

- **Trigger (two-stage):** picking up `mom_notebook` (Mara's journal, a
  WALK-OVER pickup in the barn, `scenes/interiors.py _barn_update`) sets
  `flashback_pending` (play-notes: the dream fires ON PICKUP, not the old
  3rd-read; reading the journal is now just reading); `Game._tick_flashback`
  polls it, sets `flashback_seen`, and fires a ~2.2s MEMORY FLASH (a dwelling
  fade-in/hold/out look at the door, no swarm; `FLASHBACK_FLASH_DUR`). The
  pickup logs the gate beat QUIETLY (`_evidence(..., quiet=True)`) so no case
  note pops before he has read it. The FULL ~7s wordless dream
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
  **`notes`** (shown on the Casebook's Case tab after the clues). It must NOT go in
  `evidence` — `_evidence_count` is `len(save.arg("evidence"))` and drives the
  King-gate + world rot; only the five `CANONICAL_EVIDENCE` beats of Mara's
  trail (`maras_receipt`/`maras_record`/`maras_journal`/`maras_dig`/`maras_room`;
  NARRATIVE §6, TODO #22) belong there — the bear is an optional non-counting
  item, and the Ledger/Preacher/dream file as notes. At the real Threshold (`scenes/depths.py build_threshold`
  `on_enter`), if `flashback_seen`, a recognition line lands before the
  doorframe beat: *"You have stood here before. In sleep."*

## Working agreements (process — learned the hard way)

- **NEVER use the `AskUserQuestion` tool — it errors out every time (the
  permission stream closes) and burns a turn.** When you need the maintainer to
  choose between options or clarify something, ask in plain text in your reply
  (a short numbered list with your recommendation) and stop for their answer.
- **DOCS ARE PART OF THE CHANGE, NOT A FOLLOW-UP (do this automatically, top
  priority).** Whenever you touch code, updating the doc that governs what you
  touched is part of the SAME task and belongs in the SAME commit; it ranks
  above declaring the work done. NEVER wait to be asked. Match the doc to what
  moved: **`TODO.md`** when a ticket lands, changes scope, or a new task
  surfaces (mark it, do not leave it stale); **`NARRATIVE.md`** when a canon
  fact, invariant, or player-facing story detail changes; **`DESIGN.md`** when
  a system, a mechanic, or its code-map changes; **`DIALOGUE.md`** when ANY
  player-facing spoken line or narrator box changes (see the next bullet);
  **`VISION.md`** when the see-it-don't-guess rule or the capture workflow
  changes; **`CLAUDE.md`** when the layout, a convention, or a workflow
  changes. One fact, one home, then reconcile the siblings (a detail true in
  one doc and stale in another is rot). A change is not "done" until its docs
  match it, so before you commit, ask which of the six canon docs your diff
  just made stale and fix them in the same breath.
- **DIALOGUE AND ITS DOC ARE ONE (non-negotiable, `DIALOGUE.md` contract).**
  Every word the player reads lives in two homes: the code that ships it and
  `DIALOGUE.md`. They are the same text. If your diff changes, adds, or cuts
  a spoken line or a narrator box, it changes `DIALOGUE.md` in the SAME
  commit, and vice versa. There is no "update the dialogue doc later." A
  disagreement between code and `DIALOGUE.md` is a bug (rot), reconciled on
  sight; a `tests/flow.py` canon-guard on an exact wording wins over both.
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
  well position (`scene._well_pos`, col 52 row 17 since the 60x60 redesign,
  TODO #18), and NPC names changed — the Kid is **Toby** (sprite/portrait/
  dialogue kind `toby`), not "Village Kid". **Brimley is 60x60 now** (a full
  reshape at the same content density; the square + torus wrap + fog rim all
  stay). Nothing in the town sits where the old 100x100 code put it, so a
  hard-coded brimley tile coordinate in another file is a red flag: read the
  scene, don't trust a remembered spot.
- **Previewing visuals headlessly:** render to PNG/GIF with
  `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` + Pillow (installable) and
  send with the file tool. For whole-screen cutscenes, step
  `_tick_flashback` / `_draw_flashback` in a loop and capture
  `pygame.image.tostring`.
