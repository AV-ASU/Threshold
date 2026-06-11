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
| scenes (`scenes/depths.py _ambient`) | per-room timed ambients (`cult_chant`, `cult_breath`, `low_pulse`, `heartbeat`) |
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

**Known opportunities (deferred, in rough priority order):**

- Door foley (`door_open`/`door_close`) is still a raw saw sweep — the
  weakest remaining cue. A creak (descending narrow-band noise) +
  latch transient would carry the house scenes better.
- UI cues (`cursor`/`confirm`/`menu_*`) are bright square/triangle
  blips — chiptune-adjacent against an otherwise organic palette.
  Acceptable as non-diegetic UI, but a softer filtered take would sit
  better.
- `Enemy.shoot_sfx` is plumbed (`game.py` plays it panned/attenuated)
  but no enemy sets it — dormant, not dead. If a shooting enemy is
  ever added the wiring is ready.
- The `whisper` cue is only used twice; the formant band-pass work in
  `_build_whisper` could carry more of the late-game surface dread.
