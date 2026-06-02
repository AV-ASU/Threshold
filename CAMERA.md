# THRESHOLD — the tilted camera (design + status)

The long-game vision: keep the game **100% procedural** (no image assets)
but render **most objects as volumetric solids projected to 2D**, lock the
camera to an **oblique ~55° pitch**, and let the player **turn their head**
to peek around the world. The void around each scene is filled with a
procedural **skybox**, not black. A horror **blind-spot vision** layer is the
ambitious payoff (terrain reveals on a peek; threats do not).

This file is the source of truth for that track. The camera seam, the oblique
tilt, the skybox, occlusion, and the **blind-spot vision** are **all live and
wired** — **F3** toggles pitch 0↔55, and pitch 0 stays the byte-identical
shipping flat view. **One phase remains: Phase 5**, the finish/polish pass
described below (it also absorbs the old head-turn + per-actor-depth work).
Everything before it is built and pushed.

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
is the only real chokepoint. Centralizing it (the `Camera` seam) makes tilt +
rotate a parameter change instead of a 37-scene rewrite.

---

## Modules (built, isolated, pushed)

All live under `rendering/`, with headless previews under `tools/`. These are
now wired into the live game; the tilt ships behind the **F3** toggle.

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

**Phases 0–4 are done and live** — the camera seam (pitch-0 byte-identical),
the oblique tilt of floor/walls, the skybox in the voids, occlusion, and the
**blind-spot vision**. F3 toggles the tilt; smoke + flow are green. **Phase 5
is the only remaining phase.** It now also absorbs the old Phase 3 (the
head-turn arc + per-actor depth), so it is the single push that takes the tilt
track from "lands behind a toggle" to **finished**.

## Phase 5 — finish the oblique view (the only open phase)

The work, in rough order of payoff:

1. **Per-actor occlusion + depth-correct interleave.** Today walls split and
   fade on the **player's** depth only (`occluder_alpha` keyed to the player) —
   fine when rooms were near-empty, *wrong* now that every interior is full of
   mid-floor props and partition walls (the reshaped/furnished world merged in
   PR #12). Make the wall/actor interleave **per-actor**: each actor and prop
   sorts against each wall by `Camera.depth`, and an occluding wall fades for
   whichever actor it actually covers, not just the player. This is the
   correctness fix the furnished rooms now need.
2. **The head-turn arc (±45°).** Free-smooth yaw clamped to a 90° total arc off
   forward, easing back to center on release (the locked decision above). Drive
   `Camera.yaw` from the look input so the **view swings** with the peek —
   today the blind-spot cone (`look.aim`) moves but the camera does not, so the
   mechanic reads as disembodied. `tools/preview_occlusion.py` already
   exercises the arc against fading walls.
3. **Reconcile the remaining top-down assumptions** (the original Phase 5):
   - **Wrap-clone seams** — toroidal scenes clone decor/NPCs at `±world`
     offsets; recompute those offsets **through** the projection, not in screen
     space, or the seam tears under tilt/yaw.
   - **Per-scene `skybox kind`** — wire each scene to `overcast` vs `void`
     (interiors/underground keep the near-black surround).
   - **Tune the dread framing** — zoom/pitch/cone, and re-center the radial
     vignettes (`_draw_brimley_haze`, `_draw_outdoor_vignette`) on the player's
     **projected** position (they sit ~15px off under tilt today).

### Guardrails (non-negotiable for this phase)

- **Pitch 0 stays byte-identical.** Gate every change with
  `tools/capture_world.py`; the flat (F3-off) view must not move a pixel.
- **Keep smoke + flow green** (`tests/smoke.py`, `tests/flow.py`).
- **Asset-free** — solids are math, no PNGs, no bake step.
- **Preview headless first.** Render to PNG/GIF with the SDL dummy drivers and
  eyeball it *before* wiring `game.py`; ship behind the **F3** toggle until it's
  good so `main` stays playable.
