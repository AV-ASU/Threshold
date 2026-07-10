# THRESHOLD — the tilted camera (design + status)

The long-game vision: keep the game **100% procedural** (no image assets)
but render **most objects as volumetric solids projected to 2D**, lock the
camera to an **oblique ~55° pitch**, and let the player **turn their head**
to peek around the world. The void around each scene is filled with a
procedural **skybox**, not black. A horror **blind-spot vision** layer is the
ambitious payoff (terrain reveals on a peek; threats do not).

This file is the source of truth for that track. **The track is COMPLETE
(Phases 0–5 all live).** The oblique view is now the **DEFAULT** — the game
boots tilted (~55°) with mouse-look. **F3 toggles back to the flat pitch-0
top-down view**, which stays **byte-identical** to the legacy raster (gated by
`tools/capture_world.py`, which pins pitch 0). The modules below are no longer
isolated scaffolding — they are the live render path under tilt.

---

## Decisions (locked with the user)

- **Pitch:** fixed oblique, target **~55°**. Not free-pitch.
- **Default camera:** glued **behind the player's facing** — whatever compass
  direction the player faces is "forward / camera home."
- **Rotation = a head-turn, not an orbit.** Free-smooth yaw, **clamped to a
  90° total arc** (±45° off forward), **eases back to center** on release.
  The player peeks left/right; they do not spin the world freely.
- **Skybox, not black voids.** A procedural far backdrop fills the area
  beyond the playfield and **parallaxes with yaw**. Scene-type aware: an
  `overcast` sallow sky for Brimley daytime, a near-black `void` surround for
  interiors/underground (the horror keeps its dark). This is a *skybox*, not a
  literal ceiling — we are filling the surround, never drawing a roof over the
  play area or over the UI.
- **Blind-spot vision (ambitious, on-theme) — BUILT (Phase 4).** When the head
  turns, the **terrain** behind/around the player is revealed (it just draws),
  but **NPCs, items, and the world rot rot stay hidden until actually looked
  at** — gated to a forward sight cone (`rendering/sight.py`). Locked design
  calls: cone **74° half-angle / 360px** range; **re-hide** when out of the
  cone (no last-seen memory — the dread is uncertainty, not a stale ghost); the
  world **keeps simulating off-camera** (entities move/chase normally while
  unseen — "not looking ≠ not there"), only the *render* is gated, so a thing
  re-enters view wherever its own logic carried it. The **King is exempt** (a
  relentless apex you must be able to track). The blind-spot **fog**
  (`_draw_sight_fog`) is **shadow-cast**: each ray across the cone stops at the
  first solid (`Scene.blocks_sight`), so the clear region is a true visibility
  polygon — you *see* your sightline cut off where a wall interrupts it (crisp
  tile-edged shadows), and the fog matches the actor gate instead of looking
  clear through walls.
- **UI stays flat / screen-space.** HUD, dialog, notebook, vignettes,
  full-screen overlays (transition fade, apex wash, death cards, the Carcosa
  cutscenes) are unaffected by the tilt and keep drawing in screen space.

---

## Why this fits the project

THRESHOLD already draws every sprite procedurally and **already rewrites
sprites at runtime** (the world rot overlays, the human→vessel morph in
`transform.py`, the King's per-frame `_YK_*` state). A 3D-points-projected-
to-2D approach is the same idiom — matrix math in the draw call — so it
honors the "no image-asset pipeline" rule in `CLAUDE.md`. We are **not**
pre-rendering models to sprite sheets (that would be an asset pipeline and is
explicitly off-ethos).

The whole game converts world→screen today with an ad-hoc
`sx = x - cam_x; sy = y - cam_y` at every draw site. That single conversion
is the only real chokepoint. Centralizing it (Phase 1) makes tilt + rotate a
parameter change instead of a 37-scene rewrite.

---

## Modules (built, isolated, pushed)

All live under `rendering/`, with headless previews under `tools/`. None are
imported by the live game yet.

| Module | Role |
| --- | --- |
| `rendering/camera.py` | **The seam.** `Camera.project(wx, wy, wz)` → screen; `world_to_screen()` is a drop-in for the old `x - cam_x` form (identity at pitch 0). `depth()` is the painter's-algorithm sort key. Owns `pitch`, `yaw`, `scale`, `origin`. `ground_squash()` / `height_rise()` are pitch-aware footprint helpers. |
| `rendering/solids.py` | **Volumetric kit.** `draw_solid` (body of revolution from stacked elliptical footprint sections — columns, figures, the Watcher), `draw_box` (crates, walls), `draw_billboard` (the **fallback**: a flat sprite stood up as a camera-facing card so un-converted objects still place correctly under tilt), `draw_with_alpha` (render-to-scratch helper used by occlusion). |
| `rendering/skybox.py` | **Backdrop.** `draw_skybox(surf, rect, yaw, kind)` — sky gradient + sallow Sign-band + fog horizon + a wrapping near-black treeline/rooftop silhouette that parallaxes on yaw. `kind ∈ {overcast, void}`. |
| `rendering/occlusion.py` | **Don't-hide-an-actor.** `occluder_alpha(...)` fades any solid that is nearer the camera than a focus actor AND covers it on screen (screen-space bbox overlap of base..top, feathered so walls ease rather than pop). Phase 5: `draw_world` calls it **per visible actor** and takes the min, so a wall fades for whichever actor it covers, not just the player. |
| `rendering/sight.py` | **Blind-spot vision (Phase 4).** `visible_factor(px, py, heading, tx, ty, blocks)` → 0..1: a forward sight CONE keyed to the look heading (`SIGHT_HALF` 74°, `SIGHT_RANGE` 360px, an always-seen `SIGHT_NEAR` 40px bubble), gated to 0 by walls via `los_clear` (a coarse ray march against `Scene.blocks_sight`). Soft at the cone lips (`SIGHT_*_FEATHER`) so things fade in, not pop. Pure math; the gate the game draws through under tilt. |
| `rendering/pseudo3d.py` | The original proof: a volumetric Watcher (`draw_pseudo3d_watcher`) — self-occluding features (the gold eyes wrap around the back), travelling rim light. Superseded by `solids.py` for general use; kept as the worked reference. |

### Previews (headless; self-configure SDL dummy drivers)

```bash
python tools/preview_pseudo3d.py    # the Watcher turntable + spin gif
python tools/preview_tilt.py        # one room, pitch 0 -> 55 (the tilt itself)
python tools/preview_skybox.py      # fixed 55, yaw 0 -> 360, skybox in the void
python tools/preview_occlusion.py   # +/-45 head-turn arc; walls fade per-actor
python tools/preview_look_control.py # the LookController on a real scene
python tools/preview_phase5.py      # LIVE furnished room: per-actor occlusion +
                                    # depth interleave across the head-turn arc
```

Each writes a labelled PNG strip (and a GIF if Pillow is present) to `/tmp/`.

---

## Coordinate convention

- world **x** → screen right
- world **y** → ground depth (screen-down at pitch 0)
- world **z** → height **off** the ground (0 = on the floor), screen-up

At `pitch = 0` this is exactly today's top-down view (z has no screen effect —
you see the tops of things). As pitch rises toward π/2 the ground foreshortens
(`cos pitch`) and height projects upward (`sin pitch`). Optional `yaw` spins
the world about the vertical axis (the head-turn).

---

## Roadmap

| Phase | Work | Risk | Visual change |
| --- | --- | --- | --- |
| 0 ✅ | Pseudo-3D + camera + solids + skybox + occlusion scaffolding (this file) | — | none (isolated demos) |
| **1** 🟧 | **Camera seam (live):** route world→screen through `Camera` at **pitch 0**. **DONE:** `Game.camera` synced each frame; items, corpses, NPCs, enemies, player, the five player-centred overlays, and decorations (incl. wrap-clones) all go through `camera.project()`. Gated pixel-identical by `tools/capture_world.py`. **REMAINING:** terrain / walls / roofs / doors are area/quad-based (`scenes/base.py`) and need real per-tile **quad** projection — moved to Phase 2 (it's geometry, not a 1:1 point swap). The fold pass (`rendering/folds.py`) and `enemy.draw` internals still take raw offsets. | low | **none** (pixel-identical) |
| **2** ✅ | **Tilt the floor/walls (live).** `scenes/base.draw_terrain_tilted` warps the visible floor window (wrap-aware) + extrudes wall boxes; `draw_world` branches at pitch>0 with skybox + decorations; actors stand via Phase-1 projection + a sin(pitch) lift (per-kind for tall sprites); camera pivots about screen centre + eases a zoom-out (scale→0.72); **F3** debug-toggles pitch 0↔55. **Depth/occlusion:** walls split on the player's depth — behind drawn before actors, in-front drawn after + faded by `occluder_alpha`. **Enemies/projectiles** routed through the camera; **folds** stand up anchored to the projected floor seam. Gated pixel-identical at pitch 0; smoke+flow green. **Deferred (imperceptible/secondary):** overlay vignettes re-center ~15px off under tilt; per-ACTOR (vs player-only) wall depth interleave. | med | the tilt lands (F3) |
| 3 ✅ | The **head-turn arc** (input clamp + ease, ±45°) — `systems/look_control.py` drives `Camera.yaw` from the mouse (`LookController`: aim leads the body by ≤45°, the view leans + eases to centre on release). Done together with Phase 5's per-actor occlusion + depth-correct interleave (this row folded into Phase 5). | med | head-turn + clean depth |
| **4** ✅ | **Blind-spot vision (live).** `rendering/sight.py` is the heading-keyed visibility buffer; `draw_world` gates the DRAW of NPCs, enemies, corpses, items, and the world-rot decals to `visible_factor` (soft-alpha fade at the cone lip via `draw_with_alpha`), keyed to `look.aim` and clipped by `Scene.blocks_sight`. The world keeps **simulating** off-camera (the update path is untouched) — only rendering is gated, so unseen things aren't shown and **re-hide** when the head turns away (SCP-173 dread; no last-seen memory). The **King is exempt** (relentless apex); the player is never gated. Previews: `tools/preview_sight.py` (schematic) + `tools/preview_blindspot_live.py` (live tilt). Gated pixel-identical at pitch 0 (`tools/capture_world.py`); smoke + flow green. | high | the horror mechanic |
| **6** 🟧 | **Ground heightfield — blind-spot hills (PROTOTYPE, behind a preview).** A per-scene ground height so terrain rolls and a crest you can't see over occludes like a wall. `Scene.set_ground(grid)` / `Scene.ground_z(x_px, y_px)` (bilinear, 0.0 when unopted → dead-flat, pitch-0 byte-identical); authored with `rendering/heightfield.build_heightfield(w, h, bumps)` (the `_flood`-style helper, cosine bumps). Feeds TWO things: (a) SIGHT — an optional ground-crest term in `sight.los_clear`/`visible_factor` (`ground=` cb) and in `Scene.clear_sight_line`, so a hill hides what is beyond it in BOTH the draw gate and the cult AI (`SIGHT_EYE_H`); (b) DRAW — `rendering/heightfield.draw_ground_mesh` lays a projected floor mesh over the flat affine raster where a scene authored hills (tilt-only; the flat `_tilt_warp` is unchanged), and actors/standees lift by `ground_z`. Movement stays 2D; height is a passive READ for draw + sight only (AI/pathing ignore it in v1). Wired but **dormant** — no shipping scene opts in yet. Preview: `tools/preview_heightfield.py`. Byte-identical at pitch 0 (`tools/capture_world.py`); full gate green (guard: `tests/render_smoke.py` [4/4]). **River spike:** `heightfield.carve_channel` cuts a sunken TROUGH (banks from `build_heightfield`, bed below grade); `draw_ground_mesh` shades `~`/`@` bed tiles WET, and the bank crest occludes the bed from the grade (the sight-pit the WADE water routing wants). Preview: `tools/preview_river_channel.py`. **Deferred:** rolling the whole floor raster (a mesh/displaced warp replacing the global affine `_tilt_warp` — the honest fix for a large watery area, since mesh-over-flat relief is thin edge-on); multi-floor buildings (3b); continuous traversable z (3c). Verticality design note (stairs as `cross_fold` tier-seams, slopes as heightfield, river as carved channel + WADE) lives in the PR thread. | med | ground rolls + hill blind spots |
| **5** ✅ | **The finishing push (absorbs old Phase 3).** (1) **Per-actor occlusion + depth-correct interleave:** `draw_terrain_tilted` now draws only the flat layer (warped floor + ground decals + billboard decor) and **returns** the upright occluders (wall tiles + solid props); `draw_world` folds walls, props, and actors into **one depth-sorted list** (`Camera.depth`) and draws back-to-front, so the furnished rooms' mid-floor props + partition walls interleave correctly. Each wall fades for whichever **visible** actor it covers (`occluder_alpha` min over the focus set), not just the player. (2) **Head-turn arc** swings `Camera.yaw` (Phase 3, above). (3) **Reconciled top-down assumptions:** wrap-clone decor + solid props re-project **through the projection** under tilt (no screen-space seam tear); per-scene **`Scene.skybox_kind`** (overcast vs void, defaulting by `OUTDOOR_SCENES`); the player-centred overlays (vignettes, flashlight cone, apex/hide discs) re-centre on the player's **projected + lifted** position (`_player_screen`), no longer ~15px low under tilt. Pitch 0 byte-identical (`tools/capture_world.py`); smoke + flow green. Preview: `tools/preview_phase5.py`. | med | polish + clean depth |

### Top-down assumptions — all reconciled (Phase 5 ✅)

- ✅ **Wrap-around (toroidal) scenes** clone decorations/NPCs/solid props at
  `±world` offsets recomputed **through the projection** (added in world space
  before `Camera.project`), not in screen space — actors already did this; the
  tilt decor + prop clones now do too (`draw_terrain_tilted` / `_draw_solid_prop`).
- ✅ **Depth order** is explicit under tilt: `draw_world` builds one list keyed
  by `Camera.depth` and draws back-to-front (at pitch 0 it stays in legacy
  insertion order → byte-identical).
- ✅ **Vignettes** (`_draw_vignette`, `_draw_outdoor_vignette`) + the apex/hide
  discs + the flashlight cone re-centre on the player's **projected + lifted**
  position (`_player_screen`); at pitch 0 the lift is 0, so they don't move.
- **HUD / overlays** stay screen-space (intended) — do **not** route them
  through the camera.

---

## Working agreements for this track

- **Phase 1 must be visually identical.** The win condition is "the diff is a
  refactor; the game looks pixel-for-pixel the same at pitch 0." Verify with a
  before/after capture, not just smoke.
- **Keep it asset-free.** No PNGs, no bake step. Solids are math.
- **Previews before live wiring.** Same loop that built this: render to PNG/GIF
  headless, eyeball it, *then* touch `game.py`.
- **Tilt ships behind a toggle** until it's good, so `main` stays playable.
