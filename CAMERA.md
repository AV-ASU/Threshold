# THRESHOLD — the tilted camera (design + status)

The long-game vision: keep the game **100% procedural** (no image assets)
but render **most objects as volumetric solids projected to 2D**, lock the
camera to an **oblique ~55° pitch**, and let the player **turn their head**
to peek around the world. The void around each scene is filled with a
procedural **skybox**, not black. A horror **blind-spot vision** layer is the
ambitious payoff (terrain reveals on a peek; threats do not).

This file is the source of truth for that track. It is **scaffolding so
far** — the modules below are built, previewable, and pushed, but **not yet
wired into the live game** (`systems/game.py` still renders the flat top-down
view). Phase 1 (the camera seam) is the next live step.

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
  but **NPCs, items, and the infestation rot stay hidden until actually looked
  at** — gated to a forward sight cone (`rendering/sight.py`). Locked design
  calls: cone **62° half-angle / 280px** range; **re-hide** when out of the
  cone (no last-seen memory — the dread is uncertainty, not a stale ghost); the
  world **keeps simulating off-camera** (entities move/chase normally while
  unseen — "not looking ≠ not there"), only the *render* is gated, so a thing
  re-enters view wherever its own logic carried it. The **King is exempt** (a
  relentless apex you must be able to track).
- **UI stays flat / screen-space.** HUD, dialog, notebook, vignettes,
  full-screen overlays (transition fade, apex wash, death cards, the Carcosa
  cutscenes) are unaffected by the tilt and keep drawing in screen space.

---

## Why this fits the project

THRESHOLD already draws every sprite procedurally and **already rewrites
sprites at runtime** (the infestation overlays, the human→vessel morph in
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
| `rendering/occlusion.py` | **Don't-hide-the-player.** `occluder_alpha(...)` fades any solid that is nearer the camera than the focus actor AND covers it on screen (screen-space bbox overlap of base..top, feathered so walls ease rather than pop). |
| `rendering/sight.py` | **Blind-spot vision (Phase 4).** `visible_factor(px, py, heading, tx, ty, blocks)` → 0..1: a forward sight CONE keyed to the look heading (`SIGHT_HALF` 62°, `SIGHT_RANGE` 280px, an always-seen `SIGHT_NEAR` 30px bubble), gated to 0 by walls via `los_clear` (a coarse ray march against `Scene.blocks_sight`). Soft at the cone lips (`SIGHT_*_FEATHER`) so things fade in, not pop. Pure math; the gate the game draws through under tilt. |
| `rendering/pseudo3d.py` | The original proof: a volumetric Watcher (`draw_pseudo3d_watcher`) — self-occluding features (the gold eyes wrap around the back), travelling rim light. Superseded by `solids.py` for general use; kept as the worked reference. |

### Previews (headless; self-configure SDL dummy drivers)

```bash
python tools/preview_pseudo3d.py    # the Watcher turntable + spin gif
python tools/preview_tilt.py        # one room, pitch 0 -> 55 (the tilt itself)
python tools/preview_skybox.py      # fixed 55, yaw 0 -> 360, skybox in the void
python tools/preview_occlusion.py   # player-locked +/-45 head-turn arc, walls fade
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
| 3 | The **head-turn arc** (input clamp + ease, ±45°) + per-actor occlusion + depth-correct wall/actor interleave. | med | head-turn + clean depth |
| **4** ✅ | **Blind-spot vision (live).** `rendering/sight.py` is the heading-keyed visibility buffer; `draw_world` gates the DRAW of NPCs, enemies, corpses, items, and the infestation rot decals to `visible_factor` (soft-alpha fade at the cone lip via `draw_with_alpha`), keyed to `look.aim` and clipped by `Scene.blocks_sight`. The world keeps **simulating** off-camera (the update path is untouched) — only rendering is gated, so unseen things aren't shown and **re-hide** when the head turns away (SCP-173 dread; no last-seen memory). The **King is exempt** (relentless apex); the player is never gated. Previews: `tools/preview_sight.py` (schematic) + `tools/preview_blindspot_live.py` (live tilt). Gated pixel-identical at pitch 0 (`tools/capture_world.py`); smoke + flow green. | high | the horror mechanic |
| 5 | Reconcile top-down assumptions: wrap-clone seams re-project; per-scene `skybox kind`; tune dread framing. | low | polish |

### Things that will need care (known top-down assumptions)

- **Wrap-around (toroidal) scenes** clone decorations/NPCs at `±world` offsets;
  the clone offsets must be recomputed through the projection, not added in
  screen space.
- **Depth order** is currently *implicit* (draw order = list order). Phase 1
  must make it explicit (`Camera.depth`) or tall things will sort wrong on tilt.
- **Vignettes** (`_draw_brimley_haze`, `_draw_outdoor_vignette`) are radial and
  player-centred; fine as screen-space passes, but re-center on the player's
  *projected* position.
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
