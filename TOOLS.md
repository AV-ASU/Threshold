# THRESHOLD — Tools

> **Generated file — do not hand-edit.** Rebuild with
> `python tools/index.py --md`. Each line is the first line of that
> tool's own docstring, so this list cannot drift from the shelf;
> `tests/conventions.py` fails if it does. Every tool is headless and
> self-configures the SDL dummy drivers.

Not canon, and never required reading — it is a shelf label. The
terminal version is `python tools/index.py [word]`.

## Start here — the reflex tools

- **`tools/capture_facings.py`** — LOOK at a scene from N/E/S/W. Asserts the facings differ, so it cannot hand back the same view four times. The VISION.md look pass.
- **`tools/preview_props_sheet.py`** — LOOK at a prop kind in isolation against a height ruler, BEFORE placing it. Scene-dressing step 2: never place a kind by its name.
- **`tools/kind.py`** — What tilt set / light tables / art / placements does a kind have? Answers 'will this render as a flat stain' without a scratch script.
- **`tools/light_audit.py`** — Coverage overlay for a scene's lighting: mechanical radius, visible pool, and THE DARK as a reviewable shape. Run before/after placing any fixture.
- **`tools/capture_world.py`** — The deterministic before/after render gate (--tag / --diff) for byte-identity on rendering refactors.
- **`tools/check_canon_keys.py`** — Tripwire: the load-bearing item/scene keys named in NARRATIVE.md still exist in the source.

## Look At The World

- `tools/capture_facings.py` — Four-facing capture for ONE scene -- the VISION.md look-pass harness.
- `tools/capture_world.py` — Deterministic draw_world capture — the before/after gate for the camera-seam
- `tools/contact_sheet.py` — Contact sheet for THRESHOLD's scenes.
- `tools/preview_arrival_road.py` — Headless preview of the arrival_road under the LIVE tilt camera.
- `tools/preview_phase5.py` — Phase 5 verification: the LIVE oblique view of a furnished room, exercising
- `tools/preview_scene_tilt.py` — Tilt a REAL scene — polished Phase 2 proof (headless).
- `tools/preview_skybox.py` — Fixed 55deg pitch + player-rotated yaw + skybox filling the void.
- `tools/preview_tilt.py` — Render a small room through the Camera at increasing pitch -- the tilt demo.
- `tools/preview_tilt_scene.py` — Hero preview of the LIVE tilted (oblique 55) view -- the DEFAULT player
- `tools/preview_wrap_fold_tilt.py` — Stress-test the tilt against WRAP seams and FOLDS (headless).
- `tools/render_scenes.py` — Headless scene previewer for THRESHOLD.

## Look At One Thing

- `tools/kind.py` — What do I need to know about this decoration KIND, before I place it?
- `tools/preview_ashfall.py` — Headless preview of the ashfall overlay (DESIGN.md §2).
- `tools/preview_bearer.py` — Preview the possessed BEARER's new features (TODO #25):
- `tools/preview_fold_shards.py` — VISION MOCKUP -- the 4D "floating pieces" look as the language of the FOLD.
- `tools/preview_king_unfold.py` — Preview THE UNFOLDING (rendering/king_unfold.py) headlessly -- the non-humanoid
- `tools/preview_mask_spin.py` — Preview the Pallid Mask as a REAL 3D object: `yaw` spins it a full 360 --
- `tools/preview_props_sheet.py` — Isolated prop contact sheet -- CLAUDE.md scene-dressing process step 2.
- `tools/preview_pseudo3d.py` — Render the pseudo-3D Watcher proto to a labelled turntable strip + a GIF.
- `tools/preview_storm.py` — Preview THE STORM (systems.storm.Storm): the sim run over time, six

## Light / Sight / Occlusion

- `tools/light_audit.py` — LIGHT AUDIT — the designer's coverage overlay (TODO #21).
- `tools/preview_blindspot_live.py` — Live blind-spot preview (DESIGN.md §10).
- `tools/preview_heightfield.py` — Ground heightfield preview -- blind-spot hills (DESIGN.md §10).
- `tools/preview_occlusion.py` — Wall-occlusion demo: player-locked 55deg camera, +/-45deg head-turn arc,
- `tools/preview_river_channel.py` — River-channel preview -- a sunken river with real depth (DESIGN.md §10).
- `tools/preview_sight.py` — Blind-spot sight preview (DESIGN.md §10).

## Portals & Doors

- `tools/portal_poc.py` — Non-Euclidean portal / hidden-fold proof of concept (offline, headless).
- `tools/preview_door_live.py` — LIVE verify -- see-through doors through the REAL game renderer.
- `tools/preview_door_sight.py` — See-through door ACTOR sight-gating preview (DESIGN.md §7; TODO #2).
- `tools/preview_portal.py` — VISION MOCKUP -- the PORTAL: a standing 4D pane with a dim black-gold electric
- `tools/preview_rift_anchored.py` — LIVE preview -- the ANCHORED rift frame, through the real game renderer.
- `tools/preview_seethrough_door.py` — PROTOTYPE preview -- the SEE-THROUGH DOOR.

## Audio

- `tools/audio_probe.py` — Audio probe -- judge THRESHOLD's procedural sound headlessly.
- `tools/preview_chase_cues.py` — Composite preview of a named cue set -- waveform + log-frequency
- `tools/preview_sfx.py` — Per-cue spectrogram preview -- the audio analogue to sprite-preview.

## Audit / Profile

- `tools/audit_transitions.py` — Step 1 of the geometry overhaul: enumerate every world transition the game
- `tools/audit_traversal.py` — Traversal-jank audit -- a headless sweep for the *signatured* feel-bugs that
- `tools/check_canon_keys.py` — Canon-key drift tripwire.
- `tools/profile_render.py` — Headless render profiler for the world draw (FPS work).

## Other

- `tools/band_gaps.py` — How PERMEABLE is a treeline? Measure it instead of arguing about it.
- `tools/discoveries.py` — THE DISCOVERY CATALOG -- every single thing the player can find, listed.
- `tools/inspect_spot.py` — LOOK CLOSE at one CORNER of a real scene -- the middle altitude.
- `tools/preview_amalgam.py` — Preview the AMALGAMS (rendering/amalgam.py): the Watcher-family shadows
- `tools/preview_apex.py` — Preview THE APEX (TODO #25) -- the Mask wearing a unit, in its various forms.
- `tools/preview_look_control.py` — Visualize the LookController on a real scene (headless) -- DESIGN.md §10.
- `tools/preview_terrain.py` — LOOK at the GROUND and what grows on it, in isolation.
- `tools/screen_to_world.py` — Turn SCREEN positions in a capture back into WORLD TILES.
