# THRESHOLD — Claude guide

> **HARD RULE #0 — READ THIS FILE EVERY TURN, AND THE DOC YOUR CHANGE
> TOUCHES.** Before responding to ANY request about THRESHOLD, read
> **`CLAUDE.md`** (this file) in full — it is the operating guide and the
> index. Then read, IN FULL, whichever of the canon docs your work actually
> touches:
>
> | If the turn touches… | Read in full |
> |---|---|
> | **any word the player reads** (a line, a notice, a name, on-screen lettering) | **`DIALOGUE.md`** — non-negotiable |
> | **a fact the fiction asserts** (cast, place, timeline, evidence, endings) | **`NARRATIVE.md`** — non-negotiable |
> | how a system behaves, or its code map | the relevant **`DESIGN.md`** section |
> | how anything **looks** or is laid out | **`VISION.md`** (it is short; read it whole) |
> | what to work on, or a ticket's scope | **`TODO.md`** |
> | *why* something is the way it is | **`CHANGELOG.md`** (never required otherwise) |
>
> When in doubt, read it. Treat your memory of every doc as STALE — they
> change, and answering from a half-remembered version is how canon gets
> broken. The two rows marked non-negotiable are the ones that have actually
> broken things: **if your diff writes text the player reads, or asserts a
> fact about the fiction, the whole doc gets read, no exceptions.**
>
> **Why this is a router and not "read all six every time."** It used to be
> all six, ~90k tokens, every turn. It was replaced because it did not work:
> sessions that read the entire canon front to back still shipped a system
> font into a procedural-only renderer, props that render as flat stains,
> and a "verified all four facings" that was the same north view four times.
> **Reading was never the failure — applying at the moment of action was.**
> So the enforcement moved to where it can actually fire: **`tests/conventions.py`**,
> in the gate, which fails on the mechanical half of these rules (fonts,
> tilt-set registration, light-table pairing, dead doc references, scene-gate
> typos, lost-space silence). The docs keep what a machine cannot judge:
> canon facts, intent, taste, and why. **If you find yourself relying on
> memory of a rule that a script could check, the fix is to write the check**
> (see "Make the check, not the note" below).
>
> **The six docs are current-state only — history lives in `CHANGELOG.md`.**
> Each states what IS true today, once, without re-narrating how it got that
> way; the "2026-07 rework, superseded the old X" story for any landed change
> belongs in `CHANGELOG.md` instead. If a doc you're editing has drifted back
> into narrating its own history inline, that's rot the same as a stale fact:
> move the history out, leave the current state.
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
>   lore, and not a place for landed work either — once a ticket ships,
>   its story moves to `CHANGELOG.md` and it's deleted from here outright.
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
> These six files are the ENTIRE doc canon. When you change a canon fact,
> change it in its ONE home and reconcile the others: a detail that is true
> in one doc and stale in another is rot.
>
> **`README.md` is not canon, and is deliberately thin.** It's the public
> front door (install/run/controls), kept short on purpose so there's
> almost nothing in it to drift. It still falls under "docs are part of
> the change" below — if your diff changes install steps, controls, the
> save model, or the test command, update it in the same commit — but it
> is never required reading before answering, and architecture detail
> belongs in this file, not duplicated there.

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

# Full test gate — runs all seven harnesses (conventions + smoke + flow +
# stealth + fold_pursuit + king_roam + render_smoke) and exits nonzero if any
# fails. Self-configures SDL dummy drivers, so no env vars needed. Run from
# repo root before every commit/push.
python tests/run_all.py

# Or run a single harness (same drivers, standalone):
python tests/conventions.py  # the prose rules, enforced (runs in <1s)
python tests/smoke.py        # scene-builder / spawn / exit / drop-rate smoke
python tests/flow.py         # story-beat integration + canon guards

# WHAT TOOLS EXIST? Run this BEFORE writing a throwaway script -- there are
# 40+ headless tools and the one you want probably already exists.
python tools/index.py [word]         # the shelf, filtered
python tools/index.py --md           # regenerate TOOLS.md (gate checks it)

# LOOK at a scene from all four facings (the VISION.md look pass). Sets the
# camera yaw itself and ASSERTS the facings differ, so it cannot hand back
# the same view four times the way a hand-rolled capture does.
python tools/capture_facings.py <scene_key> [--bright]

# LOOK at a prop kind in isolation before placing it (scene-dressing step 2),
# and ask what it is registered as (tilt set, light tables, placements).
python tools/preview_props_sheet.py <kind> [...]
python tools/kind.py <kind> [...]        # also: --stains, --unplaced

# THE MAINTAINER MARKED UP A SCREENSHOT -- turn the marks into tile coords.
# Under the tilt this is NOT eyeballable (yawed, foreshortened, the same
# screen row covers different world rows by depth); guessing has produced
# placements that looked plausible and matched none of the marks.
python tools/screen_to_world.py <scene> --facing S --ev 2 --at 60,245 --at ...
python tools/screen_to_world.py <scene> --facing S --grid /tmp/g.png

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
- `systems/game.py` — the orchestrator. State machine
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
  - `systems/rot_mixin.py` — world rot/ashfall + the hunting sheriff +
    the genset power link (`_tick_power`).
  - `systems/narrative_mixin.py` — the journal flashback, the case-file /
    interior-voice notes (`_log_case_entry` …), the endings + opening crawl.
  - `systems/tableau_mixin.py` — the **close-up examine tableaux**
    (`_open_desk_tableau` / `_tableau_input` / `_draw_tableau`): a modal
    close-up of a prop with a menu that mutates it live (take the gun off
    the desk, read the case file), the world frozen while it is up. Art
    (the procedural close-ups) lives in `ui/tableau.py`; the pilot is the
    bedroom writing desk. The **face-across-a-table principal talks** ride
    the same frame, all six seats: `clerk_dialogue` / `sheriff_dialogue` /
    `hettie_dialogue` / `preacher_dialogue` / `toby_dialogue` /
    `_mara_voice` each open their talk as a tableau (the `_open_*_tableau`
    openers + `open_conversation(..., tableau=True)`); the conversation's
    beats render as the caption and its menu as the option panel
    (`_convo_tableau_input`), and the art reads save flags so the close-up
    carries what the talk earned (Sable's photo/Invitation on the
    register; Vane's pose reading his despair ledger, the given paper, the
    opened cabinet; Hettie's door-glance idle, the tab leaving the spike,
    the traded paper; Crane's hands folding or gripping the lectern on the
    press fork; Toby's corn-line watch, the procession drawing, the brows
    the promise levels). **Mara is the last seat and carries the REVEAL:**
    the calling-out confrontation opens with her masked and hooded, one of
    the congregation, the caption LISTING her "One of them"
    (`MARA_CONVO["name"]` is a callable), until the greet's `("do", ...)`
    beat (`_mara_unmask`) pulls the carved mask off (the face from the
    photograph, gone thin) and the listing turns to her name; her
    captions page on Escape (the reveal can't be skipped), and the art
    reads `mara_lucid` (raised bleeding palms) / `mara_named` (her fist on
    the PI's coat, the rank stirring). The conversation engine's `("do",
    fn)` beats and callable `name` support this; `load_scene_now` drops a
    stale tableau alongside the convo. The chorus still floats its talk
    (not a tableau; `tests/flow.py` §26 float guards ride Royce). **THE
    TALK rides the frame too** (the tone inversion: `_cult_talk` →
    `_open_talk_tableau`, a scripted caption chain, not a Conversation —
    the grip close-up, the one reach-for-the-revolver choice, Escape
    pages instead of aborting). **THE PEDESTAL** (the Sign Chamber altar,
    `_open_altar_tableau`) is the OBJECT close-up of His face on the
    stone: LIFT the Mask (keystone + temptation) or TEAR IT DOWN (BREAK →
    `_play_ending("rite_broken")`), Escape backs out. Every close-up
    carries a soundscape: `lean_in` on open (the world holding its
    breath) + a per-seat ROOM TONE looped while it is up (`_TABLEAU_TONES`
    here, `Audio.room_tone`). Mara's seat stays silent by design
    (`_mara_voice` force-silences the room). How this landed (pilot →
    the six seats → the Talk → the pedestal → the sound pass) is in
    `CHANGELOG.md`. See `DESIGN.md` §11. Player-facing text is in
    `DIALOGUE.md` Part B.
- `scenes/` — `SCENE_BUILDERS` registry + `load_scene(key)`
  (`scenes/__init__.py`). A scene has spawns, exits,
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
  - `scenes/safe_path.py` — **the SAFE PATH** (`SafePath` / `build_path`;
    the SYSTEM is `DESIGN.md` §14): the lit paved spine, middle of the three
    layers (interior → yard → PATH ↔ lost spaces). A scene is built from
    ARMS (a subset of `"nesw"` around one centre junction): two opposite =
    an **I**, two adjacent = an **L**, three = a **T**. `build_path` lays the
    surface, lamps, verge, exits and mouths from that alone. **The road is
    safe by its GEOMETRY, not by its lamps** — §13's mouth only reaches a MAP
    EDGE, an arm's end is an exit (and `_tick_lost_edge` refuses on an exit
    tile), and a flank edge carries no asphalt; so the asphalt is safe
    everywhere while the verge beside it lets go like any flank. Guarded by
    `tests/flow.py` §34 as a WALK (every lane of every arm at ev3, none may
    fall). The LAMPS are SPARSE, sit on the OUTER shoulder edge, and never on
    the asphalt (every station is pushed outward until its tile is not
    asphalt, and dropped if it cannot get clear): one per arm end plus a
    staggered mid-run rhythm alternating between the two shoulders, and
    NOTHING at the junction itself. Placement is ART-DIRECTED per scene where
    it matters — `build_path(..., lamps=((tx,ty), ...))` overrides the derived
    rhythm outright, and `tools/screen_to_world.py` turns marks on a capture
    into that list (the country lane's eight are the maintainer's own).
    `street_lamp`
    (a new `SOLID_PROPS` volume, in BOTH light tables and in
    `_ELECTRIC_KINDS`) still gates stealth cover and dies with the gensets. Arms paint in two
    passes (all gravel, then all asphalt) so a junction is surfaced, not
    quartered; the dashed centre lane (`"Y"` N-S, `"-"` E-W — two floor chars
    because tiles cache BY CHAR) stops at the junction box. Every side is a
    mouth including the arms, with the road exit winning (exits span the full
    corridor, and `_tick_lost_edge` refuses on an exit tile); WHICH lost space
    is derived from the verge (`_VERGE_LOST`), never hand-picked. A `river=`
    channel keeps `RIVER_BANK` tiles of bank clear so the water is SEEN, and a
    crossing gets a paved deck plus a `bridge_rail` parapet down both lips.
    Ships `country_lane` (T) / `river_road` (I) / `river_bend` (L).
  - `scenes/lost_space.py` — **the LOST SPACES** (`LostSpace`, TODO #26;
    the SYSTEM and its code map are `DESIGN.md` §13): a procedurally-generated,
    NON-REPEATING dark field (backrooms in-between). It works BECAUSE the tilt
    renderer is already a camera-window system and collision/sight route through
    `char_object_at`/`char_floor_at`: a `Scene` whose `floor`/`objects` are
    generator-backed proxies (`_GenGrid`, bounded so stray full iteration stops)
    over a hashed per-tile field, with a huge finite `w/h` and the player at
    CENTRE (the edge never enters the window), gets collision + sight + render
    for free. It sets **`self.procedural = True`** — smoke (`tests/smoke.py`)
    skips flood-fill + full-grid scans for any `procedural` scene (an infinite
    field would hang them; `terrain._build_water_bank_edges` also early-outs on
    it). `nav_path` returns None (straight-line chasers). **Biome-parameterized**
    into three registered scenes — `lost_corn` / `lost_forest` / `lost_road`
    (plus `lost_space`, a back-compat alias → corn). Each is a hand-authored
    lit FOCAL ISLAND in the sea of generation: corn = a **crop circle** (grass
    clearing + a corn-wall ring + an abandoned cult camp lit by a wide
    `haven_fire`); forest = a **pond** (animated water + a see-over solid
    barrier, a near-bank `camp_fire` + far-shore lanterns, reeds + mist); road =
    a fenced filling-station **lot** (you land under a tall bright `neon_pylon`
    at the driveway; the sealed `gas_station` building -- a Casey's-style
    convenience store, **CASSILDA'S**, `STATION_NAME` in props, face-culled with
    every side dressed, brick wainscot + storefront + red awning + a
    procedural-neon-tube name fascia -- with a separate `pump_island` (canopy +
    pumps, split out so it depth-sorts on its own) sit NW, the `neon_pylon` is a
    googie bulb-star sign, `parking_bay` decals + `chain_fence` panels dress the
    lot, and a winding
    paved road generated river-style runs past the east edge, drifting west as it
    goes north). The island light is the haven; the
    hunted exit lantern is HELD until you leave that glow, then held 6-20 tiles
    off (`lit_at` reads deco positions live). All three sit in
    `LOST_SPACE_SCENES` (a `DARK_SCENES` subset with a heavier gloom so the
    island pops). New light kinds `haven_fire` + `neon_pylon` live in
    `FIXTURE_POOLS` (render_mixin) + `Scene._LIGHT_KINDS`; the road also adds
    non-light solids `gas_station` / `chain_fence` / `boulder` and the
    `parking_bay` floor decal. **How you get in and out (the loop):** a scene
    opts a NON-wrapping map edge in with `Scene.set_lost_edge(sides, key)`
    (`Scene.lost_edges`; None everywhere else, so an un-opted scene is
    unchanged), and `Game._tick_lost_edge` swallows you there only when the
    room is genuinely dark (`Game.scene_gloom() >= LOST_EDGE_GLOOM`, which on
    the surface is the storm climbing with the evidence count) AND the spot
    is unlit — **light gates entry: a lit edge is a wall.** The fall writes
    `Game._lost_return` (the scene + a spot `LOST_EDGE_BACKOFF` tiles back
    inside it) and crosses through `cross_fold`; reaching the hunted lantern
    spends that anchor and climbs you back out where you fell. No anchor (a
    direct load or a preview) falls back to the static `exit_to` chain. The
    fields also REARRANGE themselves behind you (`_tick_reshuffle`: only
    unlit, out-of-cone, far-off scatter props move, and only to somewhere
    also unlit and out-of-cone — geometry lies, threats never do), carry a
    manned camp + lamp-carrying cultists (so the lost scenes are in
    `CULTIST_SCENES` with `cult_target = 0`), and are WORDLESS, including
    `display_name = ""` so the HUD never names the place. Shipping mouth
    today: the lodge yard's treeline. Guards: `tests/flow.py` §32b,
    `tests/conventions.py` check 6.
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
    dispatched by `getattr(self, f"_draw_{kind}")`; the `_draw_*` methods
    are split by theme into **mixin siblings**
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
  - `amalgam.py` — **the AMALGAMS**, the Watcher-family shadows assembled
    from parts (`draw_amalgam_sprite(surf,x,y,seed,gaze,birth,dispel,mask)`):
    a seeded 3-5 part deal from a 17-part library, each part emerging
    from its own free-form cut; `AMALGAM_CHANCE` of Watcher spawns wear
    this skin, behavior unchanged (DESIGN.md §1). The **Pallid Mask part**
    (`draw_pallid_3d` — the one 3D shell — driven through
    `draw_pallid_mask_part`; the storm-King redesign, `TODO.md` #25) is an 18th
    part NEVER dealt by `assemble()`, driven ONLY by the `mask=` kwarg
    (player-scale, a REAL 3D object that turns a full 360 with the carved face
    on its front hemisphere only — no eyes from behind — one bearer storm-wide)
    — dormant until the storm system lands, so ordinary amalgams stay
    byte-identical. The possessed bearer is just a BIGGER amalgam + a crown
    (`BEARER_SCALE` / `_bearer_crown`). `carved_pallid_surface` is retained as
    the flat 2D face-art reference.
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
    fires from `_evidence`'s canonical branch (`scenes/dialogue.py`). A
    successful write flashes the **floppy save toast** (`_draw_save_toast`
    in `render_mixin`, a small 3.5in disk under the notebook scribble,
    `SAVE_TOAST_DUR`): the one reliable "that just saved" tell, gated on
    the write so it never lies about a failed disk.
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
  `on_complete` early rather than dropping it. **Conversation menus mark
  SPENT questions** (2026-07): every finished exchange sets its asked flag;
  re-askable spent rows render dimmed in both menu presentations, the
  cursor opens on the first fresh row, and a tableau menu swallows confirms
  for its first `CONVO_MENU_GUARD` beat so the E that skimmed the last
  caption can never pick an option unread.

## Threat model — the code map

**The full current-state description of every threat system lives in
`DESIGN.md`** (§1 the model + the King + the evidence ladder + the
Watchers + WADE, §2 world rot + Vane's fall, §12 graded stealth). This
section is the CODE MAP only — where each system lives:

- **visibility** [0,1] — `threat_mixin._tick_visibility`; `VIS_*` config.
- **Graded detection / suspicion** — `systems/stealth.py`, ONE source for
  both cult machines (`entities/npc.py` surface `_cult_tick`,
  `entities/enemy.py` underground); `SUS_*` config; the struggle
  `_tick_struggle`/`_struggle_win` + `STRUGGLE_*`; stones / glass / the
  well `STONE_*` / `GLASS_*` / `WELL_ECHO_*`; cult-liveness beats
  `stealth.sync_pause`/`handoff_step` (`CULT_SYNC_*`/`CULT_HANDOFF_*`).
  Guarded end-to-end by `tests/stealth.py`.
- **Deep-water WADE** — `Game._wading`, `WADE_*` config, the `_flood`
  helper (`scenes/depths.py`); stealth §10.
- **King roam** — `king_roam_mixin._tick_king_roam` (the SOLE King tick):
  arms at `KING_GATE_EVIDENCE` (3), catch birth-gated at
  `KING_CATCH_DIST`, `KING_FREE_SCENES` never host him; below the gate a
  maxed meter musters cultists (`_muster_reinforcements`). `KING_*` config.
- **Evidence ladder** (ev0 quiet town → ev1 cult wakes → ev2 he turns his
  head → ev3 he walks, after `KING_ARM_GRACE`) — gates in
  `_ensure_cultists` + `_tick_king_roam`; spawn geography
  `Scene.cult_spawns`/`cult_target` + `_spawn_cultist(from_pool=True)`
  (threat_mixin; prefill `_cult_prefilled`, top-up
  `CULT_TOPUP_INTERVAL`).
- **Watchers** — `_tick_watchers`/`_apply_curse`/`_dispel_watcher`
  (threat_mixin); `WATCHER_*` config; light pools + the beam BURN them
  (`WATCHER_LIGHT_BURN`); stealth §11.
- **Killing locals / corpses** — `_kill_npc` → `_make_corpse` + the
  `dead_locals` ledger, laid back down by `_apply_dead_locals` on every
  load; enemy cultists synthesize a corpse in `_kill_enemy`. Flow
  §27/§32.
- **World rot** — `rot_mixin._apply_rot` + `_apply_ambient_air` (stage =
  `min(3, evidence)`); the PI's four-tier register
  `_pi_tier`/`_pi_framing`/`_PI_WEATHER` (`scenes/dialogue.py`); Vane's
  ledger `VANE_*` + `_vane_ledger`/`_vane_share`/`_vane_is_hollow` +
  `_spawn_hunting_sheriff`; flow §17f.
- **Death / capture** — `_trigger_death(kind)` → `_tick_death`; THE TALK
  `_cult_talk` → `_open_talk_tableau` + two-touch `_cult_shrug_off`
  (threat_mixin); the calling-out `scenes/well.py _call_out`/
  `_sign_update`; flow §28b.

## Conventions & gotchas

- **Open canon-alignment work lives in `TODO.md`.** `NARRATIVE.md` is the
  **story bible** and the canon source of truth: it locks FACTS, never
  phrasings; states what IS, not what isn't; one fact, one home; canon
  invariants indexed at the bottom. Systems/design material lives in
  **`DESIGN.md`** — code comments cite `NARRATIVE §n` / `DESIGN.md §n`.
  Canon facts that override older code/comments: the
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
  the grove is the **mine mouth**: a physical dug SHAFT (2026-07 rework, no
  rift-portal, no re-gate at the grove — the way here was already earned).
  **§15 rework:** the descent is the GROVE RITE (the full door-dream,
  cutscene only, two-press E at the shaft lip); the dream IS the descent,
  and the grove's `on_update` carries the PI down to `well_bottom` the
  moment it ends. The circle then holds you and the way home is **keyed to
  the Mask** (crossing the shaft-floor return pane up sets `descent_sealed`,
  the SPREAD lock). The **Deep Stair is CUT**: the way
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
  same-scene `I`/`Q` relocations, the fall through a dark map edge into a
  lost space and the climb back out (`_tick_lost_edge`, DESIGN.md §13), and
  the King's rift juke — funnels
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
- **Thin-SLAB walls — REAL geometry, not draw-only (2026-07, `scenes/terrain.py`,
  DESIGN.md §6; maintainer "walls are no longer tiles / connect them by smoothing
  it out").** The step past the bevel: a wall tile becomes a THIN slab
  (`_SLAB_THICK` = 0.5·TILE). To keep the thin walls CONNECTED + smooth (no fat
  junction, no notch), `_wall_slab(scene, tx, ty)` returns the footprint as a
  LIST of up to two BANDS — a VERTICAL band (wall neighbour N or S) and/or a
  HORIZONTAL band (wall neighbour E or W). A run is one band; an L / T / cross is
  the union of both, meeting flush; each band reaches the edge only where the run
  continues, else stops at the crossbar (no stub into a room). Cross-thickness:
  floor/wall both sides → CENTRE (two-sided partition); one flank off-map → the
  SHELL, which hugs the EXTERIOR edge (outer face stays on the silhouette, no
  floor lip, thins inward). It is the SINGLE SOURCE for both draw layers
  (`_extrude_box`'s `foot` rect, looped per band + `_draw_wall_mass`'s union
  clip) AND the collision/sight/nav predicates (`scenes/base.py`
  `_obj_solid_here`, shared by `is_solid_at` / `blocks_sight` / `_nav_solid_at`,
  point-in-ANY-band, inclusive bounds so collision sits a hair proud of the drawn
  face and a nav-grid centre on a slab stays solid) — so what the player bumps
  and the AI sees IS what the player sees. Gated to `_SLAB_SCENES` (shop the
  pilot; now EVERY above-ground building interior — the Wave A refuges, the
  principal seats, and Wave 3's barn / schoolhouse / lodge_hall / lodge_cellar /
  farmhouse — each with a per-material style). The MINE (Works + Depths) instead
  renders full-thick hewn **ROCK** (`_ROCK_STYLE` / `_ROCK_SCENES`, Phase 3): the
  same styled rough-outline + prism DRAW, but `thick`=1.0, and it stays OUT of
  `_SLAB_SCENES` so its collision/sight/nav read the tile grid UNCHANGED (the
  roughening is draw-only). Only the OUTDOORS renders verbatim full-tile +
  byte-identical (`capture_world --diff` confirms the non-styled scenes).
  SUPERSEDES the bevel
  where both apply (`_bevel_corners` returns 0 in a slab scene, so a slab
  scene's `_BEVEL_SCENES` membership is inert). Roll out one interior at a time
  per VISION. **Corners are
  ROUNDED:** `_rounded_wall_poly` traces the band union to an outline and fillets
  each FREE corner (facing floor) into an arc while a wall-neighbour SEAM corner
  stays sharp (so tiles still connect flush); it drives the flat mass + a 3D
  `_extrude_prism`. Collision/sight/nav keep the square bands (rounding sits
  inside the drawn face). **Thickness + round + roughness + COLOUR are
  per-MATERIAL:** `_WALL_STYLES` (`{thick, round, rough, tint, top_tint?}`) keyed
  by scene via `_SLAB_STYLE`, read through `_wall_style(scene)`; `_SLAB_SCENES` is
  derived from it. So a scene reads its construction (`plank`/`plaster`/`timber`/
  `brick`/`stone`/`rock`/`turf`) from geometry AND a dark muddy colour `tint`
  (added to the near-black palette in both draw layers, Darkwood-safe); a
  non-slab scene's tint is (0,0,0) → byte-identical. Add a scene = one
  `_SLAB_STYLE` line. **`top_tint` (2026-07) tints the TOP cap face separately**
  from the sides (`_wall_top_tint_for`, applied in both draw layers): only
  `turf` sets it — a GRASS-green top over cold STONE sides, so a full-thick mound
  reads as a grassy HILL with bare stone where it is cut into (the effigy grove's
  mine mouth: a green hill in `_ROCK_STYLE` with a stone adit). Every other style
  omits `top_tint` → the top falls back to the side `tint` → byte-identical.
- **No diagonal-only wall joins in a slab scene (2026-07, maintainer "add a rule
  not to have walls like that").** Two walls that meet only at a DIAGONAL (the
  shared corner tile missing) look fine as fat full tiles but render as
  DISCONNECTED thin stubs under the slab. So a `_SLAB_SCENES` wall layout must
  never have one: where two perpendicular walls turn a corner, the corner TILE
  itself must be a wall (an orthogonal L), not a diagonal near-miss. Enforced by
  `tests/smoke.py [10/10]` via `terrain.diagonal_wall_joins(scene)`; fix a
  failure by adding the missing corner tile (on the non-room side) so the walls
  connect. Applies as each interior opts into `_SLAB_SCENES`.
- **No day/night cycle** — it was removed; everything reads as one
  (daytime) state. Don't reintroduce `day_phase` / `day_count`.
- **Scene-gating sets**: `SAFE_SCENES`, `DARK_SCENES`, `OUTDOOR_SCENES`
  drive King safety, flashlight darkness, etc. `DIM_INTERIOR_SCENES` (2026-07)
  is a `DARK_SCENES` subset for the explorable non-refuge interiors: a LIGHTER
  gloom (72) so a ground-floor room reads dim-lit-by-bulbs, not pitch-black
  (`_draw_dark`); lit by the genset `wall_lamp` fixture (DESIGN §6).
  `STORM_STAGE_SCENES` (Brimley + `OUTDOOR_SCENES`, 2026-07) is the surface
  world that DARKENS with the evidence count (the storm's stage, TODO #25 /
  DESIGN §2): `_draw_dark` runs there too at an ev-scaled gloom `STORM_DARK_GLOOM`
  (0 at ev0 -> early-out, byte-identical; night by ev3), so the road yard-lights
  become islands and the flashlight works outdoors. Understanding-driven, NOT a
  day cycle. `LOST_SPACE_SCENES` (the `lost_*` fields, 2026-07) is another
  `DARK_SCENES` subset with a HEAVIER gloom (150) so the lost space's lit focal
  island reads as a bright island in a black sea (TODO #26).
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
  An optional per-deco `cone=(dir_x, dir_y, half_deg)` kwarg turns the pool
  into a directional FAN in all three layers at once (visible draw,
  `Scene.lit_at` gate, audit overlay).
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
     game rule, a verb, or an evidence threshold (the old revolver "3+ evidence" tell,
     cut in the 2026-07 dialogue audit). State the
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
     facing) -- most of these hide on the one facing you happened to check. **Check E/W
     FIRST** (2026-07 playtest): the art was habitually authored for the N read, so the
     rotated facings are where floors go stripey, rugs stop reading, and building shells
     go blank.
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
  `begin_rite_dream` — completing it sets `rite_performed` (the grove's
  `on_update` then carries the PI down the mine shaft to `well_bottom` — the
  dream IS the descent, 2026-07) and also sets `flashback_seen`. `_tick_flashback` lives in `systems/narrative_mixin.py`;
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
  surfaces — and when it LANDS, don't just mark it: write what it was and why
  to `CHANGELOG.md`, then delete it from `TODO.md` outright (no "done"
  archive there, that's what turned it into 1400+ lines before the 2026-07
  restructure); **`NARRATIVE.md`** when a canon fact, invariant, or
  player-facing story detail changes; **`DESIGN.md`** when a system, a
  mechanic, or its code-map changes (state the CURRENT system; if you're
  narrating how it used to work, that paragraph belongs in `CHANGELOG.md`
  instead); **`DIALOGUE.md`** when ANY player-facing spoken line or narrator
  box changes (see the next bullet); **`VISION.md`** when the
  see-it-don't-guess rule or the capture workflow changes; **`CLAUDE.md`**
  when the layout, a convention, or a workflow changes; **`README.md`** when
  install steps, controls, the save model, or the test command change (it's
  not canon, but it's still part of this contract — see HARD RULE #0). One
  fact, one home, then reconcile the siblings (a detail true in one doc and
  stale in another is rot). A change is not "done" until its docs match it,
  so before you commit, ask which of the six canon docs (plus `README.md`)
  your diff just made stale and fix them in the same breath.
- **MAKE THE CHECK, NOT THE NOTE (the highest-leverage habit here).** When
  you break a rule, or the maintainer catches the same class of mistake
  twice, the fix is **not** another paragraph in a doc. Prose rules on this
  project have a measurable failure rate: the conventions that never regress
  (no dashes, no phantom furniture tiles, no diagonal wall joins) are the ones
  a harness asserts; the ones that regress are the ones written down and
  remembered. So:
  - If it can be **grepped, counted, loaded, or diffed**, it belongs in
    **`tests/conventions.py`** (in the gate, runs in under a second). Adding a
    check there is usually ~15 lines and permanently retires the mistake.
  - If it is about **how something LOOKS**, it belongs in a capture tool that
    fails loudly — `tools/capture_facings.py` asserts the four facings
    actually differ, because the eye demonstrably does not catch it.
  - **Prove the check can fail.** Introduce the violation, watch it go red,
    then revert. A check that cannot fail is not a check — this exact
    omission is what let a "verified four facings" ship twice.
  - **Freeze by COUNT, not by filename,** when allowlisting shipped
    exceptions (see `FONT_BUDGET`): allowlisting a whole file lets a new
    violation slip in beside an old one.
  - Then, and only then, write the one-line rule in the doc and point it at
    the check.
  - **Check the shelf before you hand-roll.** `python tools/index.py` lists
    every tool with its job. A session once wrote four scratchpad scripts to
    preview a prop, capture four facings, and inspect a light while
    `preview_props_sheet.py`, `capture_facings.py`, and `light_audit.py` sat
    in `tools/` doing each better. If the tool you need is genuinely missing,
    **write it into `tools/`, not the scratchpad**, so it exists next time.
- **CONSOLIDATE RULE LISTS, DON'T JUST APPEND.** The PLAYTEST ERROR CLASSES
  and SCENE-DRESSING PROCESS lists below exist because specific failures
  happened; that's healthy. But a list that only ever grows by appending a
  new numbered item eventually stops being readable, and each new failure
  might actually be an instance of a class already on the list. Before
  minting a new rule, check whether an existing one should just be worded
  wider to cover it. Prefer widening over appending.
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
  full gate: conventions + smoke + flow + stealth + fold_pursuit + king_roam +
  render_smoke) and confirm green BEFORE `git commit`/`push`. A commit was pushed twice this project with a
  `NameError` because edits were batched and not re-verified. For
  rendering/refactor work also run the byte-identity gate
  (`tools/capture_world.py --tag before/after`, then `--diff`). CI also runs
  `tools/check_canon_keys.py` (a cheap tripwire verifying the load-bearing
  item/scene keys named in `NARRATIVE.md`'s canon invariants still exist in
  the source) — run it locally too if you renamed or cut an item/scene key.
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
