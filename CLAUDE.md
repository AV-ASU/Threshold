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
> tilt-set registration, light-table pairing, dead doc references, dead ticket
> references, scene-gate typos, lost-space silence). The docs keep what a
> machine cannot judge:
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
> - **`TODO.md`** — the live list of genuinely open work, ordered as ONE
>   timeline. Not a place for lore, and not a place for landed work either —
>   once a ticket ships, its story moves to `CHANGELOG.md` and it's deleted
>   from here outright. **A ticket number is a stable ID, never an order:**
>   numbers are never reused or recycled, a retired number stays retired, and
>   anything that has landed is cited by its canon home (`NARRATIVE §n` /
>   `DESIGN §n`) or `CHANGELOG.md` rather than by a dead number (guarded,
>   `tests/conventions.py` check 13).
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

# Full test gate — runs all eight harnesses (conventions + smoke + flow +
# stealth + fold_pursuit + king_roam + render_smoke + layouts) and exits
# nonzero if any fails. Self-configures SDL dummy drivers, so no env vars needed. Run from
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

# LOOK CLOSE at one corner of a REAL scene -- the middle altitude, between
# the isolated prop sheet and the whole-map capture. Judging a placed prop
# from a full-scene shot is how six of them shipped as magenta squares.
python tools/inspect_spot.py <scene> --at TX,TY [--zoom 4] [--dark] [--ev N]

# LOOK at the GROUND and what grows on it, in isolation -- floor chars as
# blocks, char-vs-char seams, or the plants. A floor char judged from a
# whole-scene shot is four pixels; that is how a near-black marsh tile
# sprinkled through grass read as square holes for months.
python tools/preview_terrain.py [--chars g d ";"] [--seams] [--plants]

# THE MAINTAINER MARKED UP A SCREENSHOT -- turn the marks into tile coords.
# Under the tilt this is NOT eyeballable (yawed, foreshortened, the same
# screen row covers different world rows by depth); guessing has produced
# placements that looked plausible and matched none of the marks.
python tools/screen_to_world.py <scene> --facing S --ev 2 --at 60,245 --at ...
python tools/screen_to_world.py <scene> --facing S --grid /tmp/g.png

# THE WORKBENCH -- one running game you LOOK at, EDIT and PLAY. Deliberately
# ONE tool: the forty-seven others each boot their own game and none of them
# can change anything, so every job started by picking between sporks and
# ended in a still of a world you could not touch. This holds a game open.
#   LOOK  scene/face/spin/at/close/zoom/shot -- the WHOLE map, no interface
#         painted over it (the clock is frozen for reproducibility, which also
#         means a notice never times out, so they are cleared per frame).
#   EDIT  put/rm/mv/tile/floor/fill/npc/item/exit/spawn/undo -- and EVERY edit
#         answers with a fresh PNG, because an edit you cannot see is a guess.
#   PLAY  play/walk/key/step -- the real controls, the real interface, the
#         real darkness. `look` goes back.
#   SAVE  save writes the scene as a LAYOUT (scenes/layout.py).
python tools/look.py serve &          # boot once, leave it up
python tools/look.py scene shop_yard  # then: put woodpile 12 9 / play / walk s 20
python tools/look.py help             # the full verb list

# HOW DOES THE SURFACE CONNECT? There is no town map (DESIGN.md §15) -- the
# geography lives in two dozen scenes' exit tables, so READ it out of the built
# scenes rather than remembering it. Also reports the seams where the two
# scenes disagree about which way the other lies, which is a crossing that
# reads as a sideways teleport.
python tools/surface_map.py [--svg out.svg] [--json net.json]

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
    (`_open_desk_tableau` / `_tableau_input` / `_draw_tableau`, art in
    `ui/tableau.py`, room tones in `_TABLEAU_TONES`): a modal close-up of a
    prop or a face, world frozen, menu mutating it live. The six principal
    seats, Mara's unmask, THE TALK and THE PEDESTAL all ride this one frame
    — **the SYSTEM is `DESIGN.md` §16**, its sound is §11, its words are
    `DIALOGUE.md` Part B.
- `scenes/` — `SCENE_BUILDERS` registry + `load_scene(key)`
  (`scenes/__init__.py`). A scene has spawns, exits,
  decorations, npcs, enemies, items, and optional
  `on_enter_fn` / `on_exit_fn` / `on_update` / `on_interact_fn` hooks.
  - `scenes/layout.py` — **A SCENE AS SAVED DATA** (`dump` /
    `build_from_layout`, files in `scenes/layouts/`). The split that makes it
    work: **placement is data, behaviour is not.** Tiles, props and their
    kwargs, people and their numbers, and anything else a builder stashed on
    the scene all travel as data (tuples and sets survive; JSON has neither).
    Hooks, dialogue and any callable hung on the scene travel as
    `module:name` and are imported back — so a layout can move a woodpile but
    can never invent what happens when you knock. A closure defined inside a
    builder has no importable name and fails LOUDLY at load rather than
    handing back a room that lost its story; 40 scenes still do that, frozen
    by count in `tests/layouts.py`, and lifting a hook to module level is what
    finishes the move. Guarded: every scene is built, dumped, rebuilt and
    compared field by field.
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
  - `scenes/safe_path.py` — **the SAFE PATH** (`SafePath` / `build_path`; the
    SYSTEM is `DESIGN.md` §14): the lit paved spine, middle of the three
    layers (interior → yard → PATH ↔ lost spaces). A scene is declared as
    ARMS off one centre junction (two opposite = **I**, two adjacent = **L**,
    three = **T**) and `build_path` lays surface, lamps, verge, exits and
    mouths from that alone. Two things to hold when editing it: **the road is
    safe by its GEOMETRY, not by its lamps** (guarded, `tests/flow.py` §34 as
    a WALK), and the lamp pattern is the maintainer's own — override it with
    `build_path(..., lamps=(...))` for an art-directed scene rather than
    editing the pattern. `tools/screen_to_world.py` turns marks on a capture
    into that list. Ships `country_lane` (T) / `river_road` (I) /
    `river_bend` (L).
  - `scenes/yards.py` — **the YARDS** (the SYSTEM is `DESIGN.md` §15):
    **SAFE PATH → YARD → HOUSE.** A yard is the innermost of the three layers
    and it is a **SCENE** — one building, a road exit on one edge, that
    building's door across the ground you cross; never a dressed patch of a
    bigger map, and never shared between buildings. Every non-road edge is a
    §13 mouth. `build_yard_scene` makes the scene; `Yard` is the THIN
    vocabulary you dress the lot with (`step` / `genset` / `mailbox` / `fence`
    / `hedge` / `woodpile` / `washing` / `crates` / `bed` / `siding` / `put`),
    and **WHAT a yard says is authored per household in the scene** — a
    vocabulary applied evenly says the same thing about every house, which is
    the one thing the layer exists not to do. Three rules to hold when editing:
    **every piece goes through `put`** (it refuses the building, the door and
    the door's one approach, so a prop across the way in is a build-time
    failure); `siding` is the exception with the opposite rule (a `_WALL_DECO`
    goes on the OPEN tile the wall faces, never the wall tile); and the genset
    passes `broken` alongside `running=False` so both light tables agree.
    Ships ELEVEN yards on five town streets, one per household, each resident
    INSIDE their building. `shop_yard` off `store_row` is the worked chain.
  - `scenes/lost_space.py` — **the LOST SPACES** (`LostSpace`; the SYSTEM and
    its full code map are `DESIGN.md` §13): a procedurally-generated,
    NON-REPEATING dark field, three biomes (`lost_corn` / `lost_forest` /
    `lost_road`, plus a `lost_space` alias → corn), each a hand-authored lit
    FOCAL ISLAND in a sea of generation. It works BECAUSE the tilt renderer is
    already a camera-window system and collision/sight route through
    `char_object_at`/`char_floor_at`: a `Scene` whose `floor`/`objects` are
    generator-backed proxies (`_GenGrid`) over a hashed per-tile field, huge
    finite `w/h`, player at CENTRE, gets collision + sight + render for free.
    The two things that bite when editing: it sets **`self.procedural = True`**
    and `tests/smoke.py` skips flood-fill + full-grid scans for any such scene
    (an infinite field hangs them), and `nav_path` returns None (straight-line
    chasers). The loop in and out is `Scene.set_lost_edge(sides, key)` +
    `Game._tick_lost_edge` — **light gates entry: a lit edge is a wall.**
    Shipping mouth today: the lodge yard's treeline. Guards:
    `tests/flow.py` §32b, `tests/conventions.py` check 6.
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
  - **THE PROP PIPELINE (2026-07 rework).** A prop is DATA, not a draw
    function. Four files, and the split between them is the point:
    - `prim.py` — parametric solids returning FACES (`verts, normal, role`)
      in local space, drawing nothing: `box` / `plate` / `arch` (a tunnel
      vault) / `cyl` (z or x axis) / `prism` / `frustum` (a TAPERED prism —
      `sides=4` a lantern housing, `r1=0` a peaked cap, high `sides` a cone)
      / `wedge` / `revolve`, plus `bounds`. The library is wide on purpose —
      props used to be built out of whatever primitive was closest rather
      than the shape the object IS (a rural mailbox is a tunnel arch and
      shipped as a rectangular prism; a lantern head TAPERS and shipped as a
      straight prism, which reads as a tin can). When the shape you need has
      no primitive, **add the primitive** — that is the whole point of the
      split.
    - `materials.py` — the ONE colour table (`MATERIALS`, `ROLE_SHADE`,
      `shade_for`). Every prop used to inline its own RGB, which is why
      things didn't sit together. Shading takes the face role AND how far up
      it faces, so a cylinder gets a crown-to-belly gradient for free. Judge
      a new material in a SCENE, in the dark (`tools/inspect_spot.py --dark`):
      the preview sheet's neutral card flatters everything, and `lift`
      compounds it (an upward face lands near `(1 + lift) x base`, and under
      the 55° camera most of a low prop IS its top).
    - `assembly.py` — `Part` (a primitive + local transform + material) and
      `Assembly`, plus `draw()` which culls, depth-sorts and shades ONCE for
      every prop, and `validate()`. Culling/order/shading being central is
      what makes the old failures inexpressible: a box painting its own back
      faces, parts placed off `cam.yaw`, pieces painted in loop order.
      `Assembly(..., shadow=f)` opts into a contact pool, for a prop held
      clear of the ground (a truck on its wheels reads as hovering without
      one); default 0 leaves every existing prop untouched.
    - `assemblies.py` — the declared props themselves, and
      `references.py` — what each one is SUPPOSED to be (real dimensions,
      shape language, tells, source URL). `check_proportion` compares the
      model's L:W:H against the real object's; `real` is in the MODEL's axes
      (+x length, +y across, +z up), not the way a catalogue quotes it.
      `check_stature` compares how tall it STANDS against the reference's
      `world_h` — proportion alone is blind to a prop built correctly at the
      wrong size, which is how a mailbox shipped 36 units tall (a wall is 26,
      the player 20) with a flawless ratio. **A mount height is in WORLD
      units, never the model's exaggerated `k`.**
    An `ASSEMBLIES` value may be a finished `Assembly` OR a **variant
    factory** — a function whose parameters are read from the decoration's
    kwargs (`variant()`, built once per combination and cached; `base(kind)`
    is the default, which is what the reference measures). That is how a
    scene asks for the loaded mailbox, the woodpile with the axe still in the
    block, or the fence bay whose wire is down. Before it existed those
    kwargs were silently dropped while the comment beside them went on
    describing an axe nobody could see.
    `draw_prop_solid` prefers an assembly and falls back to the hand-written
    function, so kinds convert as they're touched rather than in one sweep.
    **Converting a kind means DELETING its old `SOLID_PROPS` entry and adding
    it to `is_solid_prop`** — leave it in `SOLID_PROPS` and you keep a dead
    draw free to disagree with what ships (`lantern` was converted as a
    hand-carried hurricane lantern while its unreachable function went on
    being the iron POST lamp the scenes and light tables had always meant);
    leave it out of `is_solid_prop` and the scene calls it a flat decal and
    ships a MAGENTA SQUARE. Both are guarded (`tests/conventions.py` checks 8
    and 8b). Preview with `tools/preview_props_sheet.py`, which turntables
    and prints the reference beside the render, then `tools/inspect_spot.py`
    to see it in the actual scene.
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
    a seeded 3-5 part deal from a 22-part library (44 with the per-part
    mirror flag), each part emerging
    from its own free-form cut; `AMALGAM_CHANCE` (0.9) of Watcher spawns wear
    this skin, so it is the ORDINARY shadow and the shroud Watcher is the rare
    one; behavior unchanged (DESIGN.md §1). Cuts wear the rift's GOLD
    (`CUT_RIM`), and each part is stroked with a
    one-pixel bone **outline** (`AMALGAM_EDGE`) so a black creature stays
    legible in a black room (a blurred glow was tried and cut -- it read as a
    ghost; gold was rejected because gold is the PORTAL colour). The outline is
    DRAW ONLY, never a light source -- keep it out of `Scene._LIGHT_KINDS` /
    `FIXTURE_POOLS` or it starts gating Watcher spawns and the lost-space
    mouth. The **Pallid Mask part**
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
    Under tilt, **trees + cornstalks are VOLUMETRIC bodies, not cards**
    (`_tilt_tree_draw` / `_tilt_corn_draw` in `scenes/terrain.py`, each
    rendered once into a per-tile card by `_tilt_tree_solid` /
    `_tilt_corn_solid`, plus a horizontal-run corn LOD `_corn_runs`). They
    join the wall/occluder set returned by `draw_terrain_tilted` — so they
    depth-sort + fade per-actor like walls (`_TILT_BILLBOARD_CHARS` in the
    collection + `_tilt_tile_box` dispatch, which routes by KIND and is
    guarded by `tests/conventions.py` check 8c so a new billboard kind with
    no branch fails instead of drawing nothing). Collision is unchanged.
    **EVERY plant is ONE renderer, `draw_tree_body`, with three species**
    (`TREE_SPECIES`): `spruce` (drooping needled tiers via `_spruce_tier`,
    each tier a shaded fan rather than a `draw_solid` body — draw_solid rings
    every body with a base ellipse and a brightened cap disc, which up a
    conifer reads as stacked lampshades), `bare` (a tapered bole continuing
    into a leader with recursively forking limbs), and `brush` (squat clumped
    mounds — walk-through growth). They share one palette family, one light
    direction and one height model, which is what makes a stand read as one
    wood. The `bush` and `creepy_tree` DECORATIONS route here too
    (`props.py` `_draw_bush_solid` / `_draw_creepy_tree_solid`) — `bush` was
    a flat floor decal and `creepy_tree` a camera-facing standee. The flat
    `_draw_tree` / `_draw_corn` are NOT this: they are the pitch-0 tile art,
    live only in the cutscene forest (`ui/cutscenes.py`).
    **A tree is not bound to its tile** (`tree_footprint`, the same contract
    `_wall_slab` gave walls): authored per tile, placed freely inside it, and
    blocking as a ROUND foot at its own position. That one function is the
    single source for the draw AND for `is_solid_at` / `blocks_sight` /
    `_nav_solid_at` (via `Scene._obj_solid_here`), so what the player bumps
    is what the player sees, and the stand stops reading as a grid.
    **Heights are real** (`tree_height`): the depth key and the occluder fade
    box in `render_mixin` take the object's own height, not the flat wall
    rise of 26 that every occluder but a counter used to claim.
    **There are no walk-through trees.** `p` used to be a passable tree (967
    of them, about half the forest) because full-tile square collision makes
    a stand a wall, so permeability had to be authored by hand. Round feet
    plus a POINT-collided player make the gaps fall out of the geometry, so
    `p` is now an ordinary solid tree and `_TILT_BRUSH_CHARS` is empty;
    undergrowth is a `bush` decoration a scene places deliberately. `j` stays
    passable because it is a hidden DOORWAY, and it now draws as a normal
    tree, which is what made it hidden in the first place.
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
- `ui/` — the surfaces the words arrive on; **the SYSTEM is `DESIGN.md` §16**
  (why each channel exists, the Casebook's three ribbons, the tableau frame).
  The code map: `journal_ui.py` (`JournalUI`, the one Casebook — `game.inv_ui`
  and `game.notebook_ui` are aliases onto `game.journal_ui`), `case_titles.py`
  (`humanise`, shared by the book and the corner toast), `dialog.py` (the
  modal band: choices + `on_complete` beats only), `float_speech.py` (a named
  NPC's line over their head), `narration.py` (the frameless lower-third
  caption; the world keeps running), `conversation.py` (menus, spent rows,
  `CONVO_MENU_GUARD`), plus fonts + text input. `DialogueBox.show` does the
  routing.

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
- **The STORM** — a MODE of the Watcher wave, never a second spawner (design:
  `DESIGN.md` §1): `_storm_active()` (past `STORM_GATE_EVIDENCE` in a room with
  `scene_gloom() > 0`), `_sync_storm_mode`, `npc._storm_tick` (walks at the
  player, refuses any step into light, cannot touch), `actor_smear_range`
  (units ignore the sight cone or the flood is invisible), `STORM_*` config;
  cap lifts to `STORM_MAX` and every dispel still works. Guards:
  `tests/stealth.py` §19.
- **THE APEX** — the Mask that wears a unit: `Game._apex` +
  `_tick_apex`/`_apex_take`/`_apex_lose_host` (threat_mixin) +
  `npc._apex_tick`; `APEX_*` config; the face `_apex_face`
  (`intent`/`strain`/`skew`), the screech `Audio.apex_roar`, the reach
  `amalgam._reach_limbs` (aimed by the SCREEN-space vector `_apex_mask_for`
  puts in `mask["reach"]`). The axe/gun kill its HOST, not the Mask (hooked in
  `_dispel_watcher`); its catch is its OWN `_death_kind == "apex"`, never the
  Unfolding's card; `_tick_king_roam` stands the Unfolding down while a host is
  worn. **Its Mask is NOT the `pallid_mask` keystone** — one Mask object exists
  and it is on the altar; this is a SLICE of Him (NARRATIVE §6a, conventions
  check 12). Guards: `tests/stealth.py` §20.
  **Two performance traps.** `draw_amalgam_sprite` CACHES each unit's composed
  surface at `UNIT_ANIM_HZ`, staggered per unit by a HASHED seed offset (a
  modulo offset clusters neighbouring seeds and the whole storm re-renders in
  lockstep — conventions check 11); and anything on the bearer that TRACKS the
  player (reach, face, gaze) is HELD to that same bucket with the Mask layer
  memoised (`_MASK_PART_CACHE`), or the bearer re-composes every frame (40.8ms
  → 7.3ms on a 22-unit storm). A tool drawing several apexes in one frame must
  `reset_amalgam_cache()` between them or the hold shows it one pose.
- **Watchers** — `_tick_watchers`/`_apply_curse`/`_dispel_watcher`
  (threat_mixin); `WATCHER_*` config. Light works on THEM, never on you: it
  denies them a spawn spot (`_spawn_watcher` needs dark + line of sight) and
  BURNS one caught in a pool/beam (`WATCHER_LIGHT_BURN`), but standing in light
  is NOT cover — exposed means not-in-cover, full stop. stealth §11 + §18.
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
- **Walls are thin-SLAB GEOMETRY, per material — the SYSTEM is `DESIGN.md`
  §6.** What matters at the point of edit: `_wall_slab` is the SINGLE SOURCE
  for the draw AND for collision/sight/nav, so never special-case one of them;
  thickness/round/roughness/tint/`top_tint` are per-material in `_WALL_STYLES`,
  so **adding a scene is one `_SLAB_STYLE` line** (and a non-slab scene stays
  byte-identical); the mine is full-thick hewn `rock` and deliberately stays
  OUT of `_SLAB_SCENES` so its collision reads the tile grid unchanged. Roll
  out one interior at a time per VISION, and re-derive interior cover as you go
  (thinner walls occlude less).
- **No diagonal-only wall joins in a slab scene** (maintainer: "add a rule not
  to have walls like that"). Two walls meeting only at a DIAGONAL — the shared
  corner tile missing — look fine as fat full tiles and render as DISCONNECTED
  thin stubs under the slab. So where two perpendicular walls turn a corner,
  the corner TILE itself must be a wall (an orthogonal L). Enforced by
  `tests/smoke.py [10/10]` via `terrain.diagonal_wall_joins(scene)`; fix a
  failure by adding the missing corner tile on the non-room side.
- **Interior doors — the subroom divider (the SYSTEM is `DESIGN.md` §7).** The
  third door kind and NOT a teleport: a swinging leaf on a floor GAP in a wall
  line WITHIN one scene, the tool that splits a box building into subrooms.
  Author with `Scene.add_inner_door(tx, ty, kind, open=False)` on a floor tile
  inside a wall run; kinds are `plank` / `bars` + `half` (see-through: stop the
  body, not the sight cone) / `curtain`. **Vary the wall**: the swing axis is
  derived from the tile's wall neighbours, so a door in a side (N-S) wall opens
  E-W and vice versa — put every door of a building in E-W walls and the leaves
  all "face south" (error class #8). Guard: `tests/stealth.py` §15.
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
  day cycle. **The dark is never the player's tool** (ruling, 2026-07:
  "darkness shouldn't hide you AT ALL"): it does not conceal you from the cult
  anywhere in the game (there is no `SUS_CONCEAL_DARK`), and standing in a lamp
  pool is not cover from a Watcher's gaze either. The dark is the CONDITION His
  things need to open, so hiding in it would be hiding inside the threat.
  `tests/stealth.py` §11 + §18 fail if either comes back. `LOST_SPACE_SCENES` (the `lost_*` fields, 2026-07) is another
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
  volume; `_STANDEE_KINDS` (`props.py` `draw_standee`) = a flat card stood up; `_WALL_DECO_KINDS` = hung on a wall; `_FLOOR_DECAL_KINDS` /
  `_SURFACE_DECAL_KINDS` = warped flat onto the floor/surface plane;
  `_TABLETOP_PROP_KINDS` (+ `seat_tabletop_props`) = seated on furniture. A kind
  that must stay ANIMATED needs a LIVE solid fn (standee cards freeze at t=0).
  Verify with a `tools/capture_world.py` tilt capture before/after.
  **`tools/kind.py` answers "which set is it in" for any kind** (including the
  `ASSEMBLIES` table), so ask it rather than grepping the tables by hand.
  **A `_WALL_DECO` goes on the OPEN tile the wall FACES, never on the wall
  tile.** It is drawn at its own position and depth-sorted against the walls,
  so one placed on the wall tile sits inside that wall's volume and is painted
  over by it: correct-looking code, nothing on screen. `terrain._wall_normal`
  reads which side the wall is on from the same neighbours (local geometry
  first, the nearest-scene-edge rule only as a fallback, so an outdoor building
  and an interior both resolve).
  **A LIGHT-emitting kind lives in TWO tables (2026-07 lighting pass):**
  `Scene._LIGHT_KINDS` (`scenes/base.py`, the MECHANICAL pool radius
  `Scene.lit_at` reads — the Watcher spawn/burn gate and the lost-edge gate;
  NOT a concealment gate, darkness never hides you) AND `FIXTURE_POOLS`
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

## The journal door-dream — the code map (canon is NARRATIVE §2/§4)

- **Trigger (two-stage):** picking up `mom_notebook` (a WALK-OVER pickup in
  the barn, `scenes/interiors.py _barn_update`) sets `flashback_pending`;
  `Game._tick_flashback` (`systems/narrative_mixin.py`) polls it, sets
  `flashback_seen`, and fires a ~2.2s MEMORY FLASH (`FLASHBACK_FLASH_DUR`, no
  swarm). The pickup logs its gate beat QUIETLY (`_evidence(..., quiet=True)`)
  so no case note pops before he has read the thing. The FULL ~7s wordless
  dream (`_draw_flashback`, mode "rite") plays at the GROVE RITE via
  `begin_rite_dream`; completing it sets `rite_performed` (the grove's
  `on_update` then carries the PI down to `well_bottom` — the dream IS the
  descent) and `flashback_seen`. Tuning: the `FLASHBACK_*` block in
  `ui/cutscenes.py`. Art: `door_mask_surface` (`rendering/sprites.py`) +
  `_build_flashback_pool`; audio `Audio.flashback_air()` + `falling_air`.
- **The trap to know:** `_log_dream_entry` writes the dream to save arg
  **`notes`**, never `evidence`. `_evidence_count` is
  `len(save.arg("evidence"))` and drives the King-gate + world rot, so only
  the five `CANONICAL_EVIDENCE` beats of Mara's trail belong there
  (NARRATIVE §6); the bear, the Ledger, the Preacher and the dream are notes.
- **Canon, guarded:** he dreamed the door exactly ONCE, a year ago, and never
  reached it; the journal reminds him, it is not recurring (NARRATIVE §2, the
  invariants). The threshold recognition rides `flashback_seen`
  (`scenes/depths.py build_threshold`); its wording is `DIALOGUE.md`'s.

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
- **IF IT ISN'T GOOD, REMAKE IT NOW (`VISION.md`).** When you look at a
  model, a scene, or a design and judge it not good enough, remake it in the
  same breath rather than handing it over with a caveat attached. "Reads a
  bit flat", "acceptable for now", "I'd rather judge it in situ" are all the
  same move: shipping work you have already decided is poor and making the
  maintainer say so. Another pass now is minutes, because the reference, the
  preview and the last failed attempt are all still loaded; the same pass
  after a round trip costs their attention and your context. The one
  exception is a genuine fork between two defensible directions, which is a
  question, not a caveat.
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
  **Never delete a function by cutting to the next `def`.** Module-level
  constants live in those gaps, and the cut takes them silently: it has now
  removed `_RUST_BASES`/`_PLATE_COLS` (the dead-car palette) and
  `_WALL_BASE`/`_WALL_FACE`/`_WALL_TOP`/`_WALL_FOOT` while removing an
  unrelated dead draw. `compileall` does not catch it -- only the gate does,
  as a `NameError` from `render_smoke`. Delete the exact body, then grep the
  removed span for assignments before writing the file.
- **Check narrative text against `NARRATIVE.md` BEFORE writing it**, not
  after. The bible is the source of truth; quote its intended voice.
- **`tests/flow.py`** is the integration harness (separate from `smoke.py`):
  boots a game, drives scene hooks, asserts story beats. It also carries
  **canon-guards** (e.g. the dream note must say "a year" and contain no
  recurrence language). Keep it green; add a guard when you lock a canon fact.
- **THERE IS NO TOWN MAP.** The one 60x60 `brimley` scene was retired in
  2026-07 (`DESIGN.md` §15): the town is a **string of house islands** on the
  street network — each household its own yard scene off its own street, each
  resident inside their own building. So there is no scene to hold a
  cross-town coordinate, and a remembered "brimley tile" is a red flag twice
  over. The public fixtures live where the layer put them: the well, the
  barrow, the news rack and the payphone on **the square**
  (`safe_path._town_square`, on `store_row`); the bridge hide on `river_bend`;
  the Preacher's remains and the clearing's hidden trunk on `river_road`; the
  bell door on `church_yard`; the cult camp on `farm_yard`. NPC names: the Kid
  is **Toby** (sprite/portrait/dialogue kind `toby`), not "Village Kid".
- **Previewing visuals headlessly:** render to PNG/GIF with
  `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` + Pillow (installable) and
  send with the file tool. For whole-screen cutscenes, step
  `_tick_flashback` / `_draw_flashback` in a loop and capture
  `pygame.image.tostring`.
