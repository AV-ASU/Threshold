# THRESHOLD — audio

The game ships **zero audio assets**. Every sound — foley, stings, beds,
"music" — is synthesized at startup in `systems/audio.py` (pure-Python
sample loops or numpy), optionally post-processed by `systems/dsp.py`
(scipy biquad filters + a Schroeder reverb), and handed to pygame as
finished `Sound`s. Nothing streams. If numpy/scipy are missing the
library falls back to dry generators (or silent stand-ins for the
numpy-only beds) and the game still runs.

This file is the audio map + the 2026-06 audit record. Design language
first, wiring second, findings at the bottom.

## Design language

THRESHOLD's soundscape is **anti-melodic dread**. The rules the library
follows (keep following them):

- **No tunes.** The music keys are drones. `home`/`village` are
  *haunted* versions of melodies that used to exist (a detuning
  music-box ping over a drone); `threshold_drone` is a bare low tritone
  (41 + 58 Hz) that never resolves. The tritone is the house interval.
- **Sub + partial.** Every low cue carries a mid partial (~200 Hz or a
  4th harmonic) so laptop speakers, which roll off ~120 Hz, still
  register it. A sub-only cue is an inaudible cue.
- **Breath, not stinger.** The threat vocabulary is built from breath
  shapes: `breath` (an inhale that cuts), `cult_lose` (an exhale),
  `yk_tone` (a *reversed* breath — air pulled from the room),
  `watcher_spawn` (a vacuum opening). Loud orchestral stings are not in
  the palette; `cult_lock` (sub kick + tritone) is as big as it gets.
- **Space is baked, not live.** The mixer can't do live reverb, so a
  space can only be baked into a cue that always plays in that space
  (the rite cues get `cellar`, the Carcosa set-pieces get `void`).
  Cues that play everywhere get **pre-baked per-profile variants**
  (`step_*` and `gunshot` × `cellar`/`outdoor`) picked at play time by
  `play_in_scene` from the scene tag (`Audio.set_scene_reverb`, called
  by `Game.load_scene_now`).
- **Silence is a move.** `force_silence` (the testimony beat: the wind
  stops and never comes back), `duck` (music drops so a horror cue
  lands in the gap), and the dead-air stretch inside `custody_bed` are
  deliberate. Don't fill them.

## Mixer + channel map

`pygame.mixer` at 22050 Hz / 16-bit / stereo, 16 channels. Reserved:

| ch | owner | content |
|----|-------|---------|
| 0 | `music_channel` | the looping scene drone (`play_music`) |
| 1 | `ambient_channel` | `falling_air` bed for the door-dream (`flashback_air`) |
| 2 | `king_channel` | `yk_tone` loop while the King is on screen (`king_tone`) |
| 3–5 | drive channels | opening drive: engine / radio / static (`start_drive` … `stop_drive`) |
| rest | dynamic | one-shots; `play(pan=…)` grabs a free channel for L/R bias |

Mix gains: `master_vol` × (`music_vol` | `sfx_vol`), settable live from
the pause menu (`set_volumes`). Single-session, like the save model.

## Spatial model

- `pan_for_world(world_x, player_x)` → −1..+1, with a 15% floor on the
  off ear so headphone listeners never lose a cue entirely.
- `distance_attenuation(sx, sy, px, py)` → 1/(1+(d/falloff)²).
- Apply both for positioned cues (enemy deaths, shots, phantom steps).
- `play_in_scene(name)` (ex-`play_footstep`) is the scene-reverb
  dispatch: plays `{name}_{profile}` if baked, else the dry cue.

## Threat wiring (who fires what)

| system | cues |
|--------|------|
| `_tick_visibility` / stillness (`game.py`) | `heartbeat` schedule above proximity 0.70 (interval tightens with threat, music ducks between beats) |
| cult AI (`threat_mixin`, `_cult_tick`) | `cult_lock` (LOS acquired, ducks music), `cult_lose` (LOS broken), `low_pulse` accents |
| watcher curse | `watcher_spawn` / `watcher_dispel` |
| hide state | `hide_enter` / `hide_exit` |
| King (`king_roam_mixin`, `_tick_king`) | `king_tone(on, vol)` — vol swells with proximity; off the instant he dissolves |
| infestation (`infest_mixin`) | `infest_throb` per stage transition; `sheriff_hunt` on the hollow lawman's spawn + chase start |
| deaths (`_trigger_death`) | `captured_bed` (cult), `custody_bed` (sheriff), Carcosa drone/roar loops (King) |
| case file (`narrative_mixin`) | `evidence_added` (canonical evidence only), `arg_chime` (notes) |
| recurring one-shots (`Scene.add_ambient`) | the scheduler: each entry fires every lo..hi s (re-rolled per fire) with volume jitter and a random pan within `pan_spread`. Ticked by `Scene.update`; additive, never clobbers `on_update_fn`. The depths/well rooms author theirs in the builders (`_ambient` helper); the surface gets them from the air pass below |
| infestation air (`infest_mixin._apply_ambient_air`) | the audible twin of the decal pass, applied on every scene load. Interiors (`music == "home"`) always carry the LIVING HOUSE base (`wood_creak` + rare `wood_pop`, panned); rot layers escalate with stage: `drip` at 1, `flies` at 2, `whisper` + `infest_throb` at 3. Outdoor scenes gain only the rot layers (the wind carries them otherwise). SAFE_SCENES stay clean until stage 3 (decal rule); underground and void scenes are skipped (authored / silent by design) |
| pursuer dressing | `breath`, `phantom_step`, `child_hum` in creepy scenes; every 12th creepy-tile step is delayed 0.12 s (the wrongness in the rhythm) |

Dialog voices: per-NPC blip names on `ui/dialog.py` (`blip_low/mid/
high/soft/kid/gruff`), `"__silence__"` for the things that shouldn't
have a voice.

## Audit 2026-06 — findings + status

Audited every `Audio` call site against the library (165 `play()`
sites, 8 music sites, channel helpers).

**Fixed in this pass:**

1. **The revolver had no report.** `player_fire_gun` played `swing`
   (the axe whoosh, a 280 Hz saw) + `bump` (the walk-into-a-wall cue).
   The gun is a major narrative device — it kills locals and feeds the
   visibility spike — and it sounded like furniture. Now:
   `gunshot` (`_build_gunshot`: crack + 320→140 Hz bark + 65 Hz thump +
   air tail, soft-clipped), played through `play_in_scene` so it slaps
   indoors (`cellar` bake) and rolls away outside (`outdoor` bake),
   with a 0.9 s music duck so the report owns the air.
2. **Empty chamber borrowed `door_locked`.** Same cue as rattling a
   door. Now `gun_dry` (`_build_gun_dry`: two thin hammer clicks).
3. **`play_footstep` renamed `play_in_scene`.** It was always the
   generic scene-reverb dispatch; the gunshot now rides it too, and the
   delayed-audio drain routes everything through it (safe: it falls
   back to dry when no variant exists).
4. **Surface interiors were acoustically flat.** The `_ambient`
   one-shot trick existed only underground. Now the scheduler is a
   first-class `Scene.add_ambient` (list-based, so cues stack and
   `on_update_fn` stays free), and every wooden interior gets the
   living-house base layer (`wood_creak`, `wood_pop`) from evidence 0.
5. **The ambience didn't rot with the world.** The visual infestation
   had no audible twin. `_apply_ambient_air` (in the infestation pass,
   every scene load) now escalates the air with the stage: `drip` /
   `flies` / `whisper` + `infest_throb`, same SAFE_SCENES-at-3 rule as
   the decals. The post-King `world_emptied` path skips the pass, so
   the emptied world goes acoustically dead along with its people.
6. **Door foley was a raw saw sweep.** Now real wood: `door_open` is
   a latch ping + a rising stick-slip hinge creak (the `wood_creak`
   friction trick, brighter and shorter); `door_close` is a swing of
   air, the frame thud, and the latch catching.
7. **UI cues were chiptune squares/triangles.** Now soft sine pairs
   (`_build_ui_tone`: fundamental + a quiet partial, eased attack).
   The pitch grammar is unchanged — open above close, confirm a warm
   fifth, cancel low — only the timbre moved. Dialog voice blips were
   left alone: they are character voices, not UI.
8. **`child_hum` now does what its comment promised.** It rides
   `Scene.add_ambient` in `CREEPY_SCENES` at a deliberately rare
   50–95 s cadence (most visits hear it at most once), panned so it
   drifts from somewhere — including down the well rooms. The scripted
   forest_path beat is untouched.

**Healthy, verified, leave alone:**

- Every scene `music=` key resolves (`home`, `village`, `basement`,
  `void`, `wrong`, `wind`, `outside`, + `threshold_drone` direct).
- Every dialog `voice` name resolves to a blip.
- No orphaned cues: everything in `self.sfx` has a live call site
  (footsteps via the surface dispatch, blips via dialog, beds via
  their systems).
- `pickup_rare` appears at 16 sites but with one consistent meaning
  (key story item acquired) — repetition is identity, not a bug.
- Ducking, silence windows, king-tone hygiene (faded the frame he
  dissolves) all behave.

**Known opportunities (deferred):**

- `Enemy.shoot_sfx` is plumbed (`game.py` plays it panned/attenuated)
  but no enemy sets it — dormant, not dead. If a shooting enemy is
  ever added the wiring is ready.
