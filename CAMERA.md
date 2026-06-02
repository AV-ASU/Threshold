# THRESHOLD — the tilted camera (design + status)

The long-game vision: keep the game **100% procedural** (no image assets)
but render **most objects as volumetric solids projected to 2D**, lock the
camera to an **oblique ~55° pitch**, and let the player **turn their head**
to peek around the world. The void around each scene is filled with a
procedural **skybox**, not black. A horror **blind-spot vision** layer is the
ambitious payoff (terrain reveals on a peek; threats do not).

This file is the source of truth for that track. It is **LIVE** — Phases 1–3
landed (see the phase table) and **the oblique ~55° view is now the game's
default** (`TILT_PITCH_DEG`; `Game._start_play`/`_reset_run_state` lock it in
and seed the look heading behind the player). **F3** toggles back to the flat
top-down view for debugging. Remaining work is polish (Phases 4–5).

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
- **Blind-spot vision (ambitious, on-theme).** When the head turns, the
  **terrain** behind/around the player may be revealed, but **NPCs, items, and
  map changes stay hidden until actually looked at** — the world is allowed to
  rearrange in the blind spot (Weeping-Angels / SCP-173 dread). Phases 1-3 have
  landed (camera seam, tilt, head-turn), so this is the next build — it now just
  needs a heading-keyed visibility buffer. Not built yet (Phase 4).
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

## Modules

All live under `rendering/`, with headless previews under `tools/`. These are
now wired into the live game (the oblique view is the default).

| Module | Role |
| --- | --- |
| `rendering/camera.py` | **The seam.** `Camera.project(wx, wy, wz)` → screen; `world_to_screen()` is a drop-in for the old `x - cam_x` form (identity at pitch 0). `depth()` is the painter's-algorithm sort key. Owns `pitch`, `yaw`, `scale`, `origin`. `ground_squash()` / `height_rise()` are pitch-aware footprint helpers. |
| `rendering/solids.py` | **Volumetric kit.** `draw_solid` (body of revolution from stacked elliptical footprint sections — columns, figures, the Watcher), `draw_box` (crates, walls), `draw_billboard` (the **fallback**: a flat sprite stood up as a camera-facing card so un-converted objects still place correctly under tilt), `draw_with_alpha` (render-to-scratch helper used by occlusion). |
| `rendering/skybox.py` | **Backdrop.** `draw_skybox(surf, rect, yaw, kind)` — sky gradient + sallow Sign-band + fog horizon + a wrapping near-black treeline/rooftop silhouette that parallaxes on yaw. `kind ∈ {overcast, void}`. |
| `rendering/occlusion.py` | **Don't-hide-the-player.** `occluder_alpha(...)` fades any solid that is nearer the camera than the focus actor AND covers it on screen (screen-space bbox overlap of base..top, feathered so walls ease rather than pop). |
| `rendering/pseudo3d.py` | The original proof: a volumetric Watcher (`draw_pseudo3d_watcher`) — self-occluding features (the gold eyes wrap around the back), travelling rim light. Superseded by `solids.py` for general use; kept as the worked reference. |
| `rendering/king_unfold.py` | **THE UNFOLDING — the live King** (see `CLAUDE.md`). A real 4D everting mass projected 4D→3D→2D, faceless, with eyes/maws/limbs, a birth ramp, locomotion lean, depth-scale and per-depth wall occlusion. Routed from `sprites.draw_npc_sprite` when `KING_UNFOLD` is True. Preview: `tools/preview_king_unfold.py`. |
| `rendering/king3d.py` | The earlier porcelain MASK-PLATE King (3D shards + reaching arms + particle wake, driven by `threat`/`birth`). **Superseded by THE UNFOLDING** — now only the fallback when `sprites.KING_UNFOLD` is False. Preview: `tools/preview_king3d.py`. |

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
| **1** ✅ | **Camera seam (live):** world→screen through `Camera`. `Game.camera` synced each frame; items, corpses, NPCs, enemies, player, the five player-centred overlays, decorations (incl. wrap-clones), terrain/walls/roofs/doors, folds — all go through `camera.project()`. Gated pixel-identical at pitch 0 by `tools/capture_world.py`. | low | **none** (pixel-identical) |
| **2** ✅ | **Tilt the floor/walls (live + DEFAULT).** `scenes/base.draw_terrain_tilted` warps the visible floor window (wrap-aware) + extrudes wall boxes + stands trees/corn up as billboard occluders (`_tilt_standee`, corn-run LOD); `draw_world` branches at pitch>0 with skybox + decorations; actors stand via Phase-1 projection + a sin(pitch) lift (per-kind for tall sprites); camera pivots about screen centre + eases a zoom-out (scale→0.72). **The oblique ~55° view is the DEFAULT; F3 toggles back to flat top-down.** **Depth/occlusion:** walls split on the player's depth (behind before actors, in-front after + faded by `occluder_alpha`); **tall actors** (King/sheriff/watcher) deferred + composited by their OWN depth (`_composite_tilt_actors`); player-centred overlays re-centred on the lifted sprite anchor. Gated pixel-identical at pitch 0; smoke+flow green. | med | the tilt (default) |
| **3** ✅ | The **head-turn arc** (input clamp + ease, ±45°) — **live** via `systems/look_control.py` (`LookController`: mouse → aim/body/`cam_yaw`, eased, clamped) + `Game._update_look`. The non-humanoid **King is THE UNFOLDING** now (`rendering/king_unfold.py`, gated on `KING_UNFOLD`); the old `king3d.py` mask is the fallback. Lean + depth-scale + per-depth wall occlusion all live. | med | head-turn + the 3D King |
| 4 | **Blind-spot vision** layer: terrain reveals on peek; NPCs/items/map-changes gated to line-of-sight. **← next.** | high | the horror mechanic |
| 5 | Reconcile remaining top-down assumptions: wrap-clone seams re-project; per-scene `skybox kind`; tune dread framing. | low | polish |

### Things that will need care (known top-down assumptions)

- **Wrap-around (toroidal) scenes** clone decorations/NPCs at `±world` offsets;
  the clone offsets must be recomputed through the projection, not added in
  screen space.
- **HUD / overlays** stay screen-space (intended) — do **not** route them
  through the camera. (Player-centred *world* overlays — vignettes, flashlight —
  DO re-center on the player's lifted projected anchor; done via
  `_player_screen_center`.)

---

## Working agreements for this track

- **Pitch 0 must stay visually identical.** The flat top-down view (F3) is the
  refactor baseline — keep it pixel-for-pixel the same so the tilt is purely
  additive. Verify with a capture, not just smoke.
- **Keep it asset-free.** No PNGs, no bake step. Solids are math.
- **Previews before live wiring.** Same loop that built this: render to PNG/GIF
  headless, eyeball it, *then* touch `game.py`.
- **The tilt is the DEFAULT now** (locked ~55°); F3 drops to flat top-down for
  debugging. Keep that escape hatch working.
