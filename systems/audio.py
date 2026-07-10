"""Audio playback + procedurally generated SFX/music library."""
import time
import math
import random
import pygame

# DSP toolkit (numpy/scipy biquad filters + Schroeder reverb). Optional:
# if numpy/scipy aren't installed the import fails and the SFX library
# falls back to the raw generators with no post-processing, so the game
# still runs (just dryer). See systems/dsp.py.
try:
    from systems import dsp
    _HAVE_DSP = True
except Exception:
    dsp = None
    _HAVE_DSP = False

# The synthesized library, built ONCE per process and shared by every Audio
# instance. Synthesis is deterministic (pure DSP, no per-run inputs) but
# costs several seconds; the shipped game builds one Audio per launch, while
# the test harnesses construct dozens of Game()s per run and were paying the
# full build each time. Volumes are applied at play time (set_volume on every
# play/loop start), so sharing the Sound objects across instances is safe.
# Keyed cache fields: sfx dict, music dict, and the four named drive/Carcosa
# loops _build_library also produces.
_LIBRARY_CACHE = None


class Audio:                        #Starting screen needs music, something simple
    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
        except Exception:
            self.enabled = False
        self.sfx = {}
        # Mix gains [0, 1], settable live from the pause menu. master scales
        # everything; music/sfx scale their group. Single-session (no disk),
        # so they reset to default each launch -- consistent with the save
        # model. Applied at every final volume stage (play / king_tone /
        # play_music / set_drive / duck restore).
        self.master_vol = 1.0
        self.music_vol = 0.8
        self.sfx_vol = 1.0
        self.current_music = None
        self.music_muted = False
        self.music_channel = None
        self.ambient_channel = None
        self.king_channel = None
        self._king_on = False
        # Scene-reverb tag for play_in_scene -- "cellar" / "outdoor" /
        # None. Set by Game.load_scene_now from the scene's tag set
        # (UNDERGROUND_SCENES, OUTDOOR_SCENES). Cue variants are baked
        # at build time per profile; play_in_scene picks the one
        # matching the active scene and falls back to dry.
        self._scene_reverb = None
        if self.enabled:
            global _LIBRARY_CACHE
            if _LIBRARY_CACHE is None:
                self._build_library()
                _LIBRARY_CACHE = (dict(self.sfx), dict(self.music),
                                  self.engine_snd, self.radio_snd,
                                  self.carcosa_drone_snd,
                                  self.carcosa_roar_snd)
            else:
                (sfx, music, self.engine_snd, self.radio_snd,
                 self.carcosa_drone_snd,
                 self.carcosa_roar_snd) = _LIBRARY_CACHE
                self.sfx = dict(sfx)
                self.music = dict(music)
            self.music_channel = pygame.mixer.Channel(0)
            self.ambient_channel = pygame.mixer.Channel(1)
            self.king_channel = pygame.mixer.Channel(2)
            # Opening-drive channels: engine idle, car radio, and the static
            # it dissolves into as the town folds shut around you.
            self.drive_channel = pygame.mixer.Channel(3)
            self.radio_channel = pygame.mixer.Channel(4)
            self.static_channel = pygame.mixer.Channel(5)

    def _gen(self, freq, ms, vol=0.3, wave="sine", attack_ms=10, decay_ms=40, vibrato=0, noise_mix=0.0):
        sr = 22050
        n = int(sr * ms / 1000)
        buf = bytearray(n * 2)
        attack_n = max(1, int(sr * attack_ms / 1000))
        decay_n = max(1, int(sr * decay_ms / 1000))
        for i in range(n):
            t = i / sr
            f = freq
            if vibrato:
                f = freq + math.sin(2 * math.pi * vibrato * t) * (freq * 0.05)
            if wave == "sine":
                v = math.sin(2 * math.pi * f * t)
            elif wave == "square":
                v = 1.0 if math.sin(2 * math.pi * f * t) > 0 else -1.0
            elif wave == "triangle":
                v = 2.0 * abs(2.0 * (f * t - math.floor(f * t + 0.5))) - 1.0
            elif wave == "saw":
                v = 2.0 * (f * t - math.floor(0.5 + f * t))
            elif wave == "noise":
                v = random.uniform(-1, 1)
            else:
                v = math.sin(2 * math.pi * f * t)
            if noise_mix > 0:
                v = v * (1 - noise_mix) + random.uniform(-1, 1) * noise_mix
            if i < attack_n:
                env = i / attack_n
            elif i > n - decay_n:
                env = max(0.0, (n - i) / decay_n)
            else:
                env = 1.0
            sample = int(v * vol * env * 32767)
            sample = max(-32768, min(32767, sample))
            buf[i*2] = sample & 0xFF
            buf[i*2+1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i*4] = buf[i*2]
            stereo[i*4+1] = buf[i*2+1]
            stereo[i*4+2] = buf[i*2]
            stereo[i*4+3] = buf[i*2+1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _post(self, sound, *, reverb=None, lowpass=None, highpass=None,
              vol=1.0):
        """Run a finished Sound through the DSP toolkit -- a Schroeder
        reverb in one of dsp's named spaces (room/cellar/chapel/
        outdoor/void) plus optional biquad low/high-pass -- and return
        the processed Sound. This is how the raw procedural foley gets
        seated into a real acoustic space (a heartbeat in a stone
        cellar, the King's tone in the void). No-op fallback to the
        original Sound if the DSP toolkit isn't available or anything
        goes wrong, so audio never hard-fails on a synthesis edge."""
        if not (_HAVE_DSP and self.enabled):
            return sound
        try:
            arr = pygame.sndarray.array(sound).astype("float32") / 32768.0
            sig = arr.mean(axis=1) if arr.ndim == 2 else arr
            if highpass:
                sig = dsp.highpass(sig, highpass)
            if lowpass:
                sig = dsp.lowpass(sig, lowpass)
            if reverb:
                sig = dsp.reverb(sig, reverb)
            return dsp.to_sound(sig, vol)
        except Exception:
            return sound

    def _build_library(self):
        g = self._gen
        # SFX
        self.sfx["step_grass"]  = g(180, 60, 0.10, "noise", attack_ms=2, decay_ms=30, noise_mix=1.0)
        self.sfx["step_wood"]   = g(140, 70, 0.14, "square", attack_ms=2, decay_ms=40, noise_mix=0.4)
        self.sfx["step_stone"]  = g(110, 60, 0.12, "square", attack_ms=2, decay_ms=30, noise_mix=0.5)
        self.sfx["step_carpet"] = g(90, 80, 0.06, "noise", attack_ms=4, decay_ms=50, noise_mix=1.0)
        self.sfx["step_void"]   = g(40, 220, 0.18, "sine", attack_ms=20, decay_ms=180)
        # A wet splash: pure noise, soft attack, a longer wet tail than a
        # dry footfall (deep-water WADE, systems/config WADE_*).
        self.sfx["step_water"]  = g(70, 130, 0.20, "noise", attack_ms=6, decay_ms=150, noise_mix=1.0)
        self.sfx["bump"]        = g(80, 100, 0.18, "square", attack_ms=2, decay_ms=70, noise_mix=0.3)
        # Door foley: a latch + hinge-creak open and a whoosh + frame-
        # thud + latch close (the old raw saw sweeps read as synth, not
        # wood). Same stick-slip friction trick as wood_creak.
        self.sfx["door_open"]   = self._build_door_open()
        self.sfx["door_close"]  = self._build_door_close()
        # The church bell -- the town's one dominant noise source
        # (rung from the tower; see the BELL_* config block). A real
        # minor-third bell voicing: inharmonic partials over a beating
        # hum, struck once, left to ring.
        self.sfx["bell_toll"]   = self._build_bell_toll()
        # Placed-noisemaker foley (Scene.add_noise_trap / _source):
        # strewn cans, glass litter, a crow flushing (the loose plank
        # reuses wood_pop), the truck radio's dead-station snatch, and
        # the works valve's knock-and-hiss loop.
        self.sfx["cans_rattle"]  = self._build_cans_rattle()
        self.sfx["glass_crunch"] = self._build_glass_crunch()
        self.sfx["crow_flush"]   = self._build_crow_flush()
        self.sfx["radio_snatch"] = self._build_radio_snatch()
        self.sfx["valve_hiss"]   = self._build_valve_hiss()
        self.sfx["engine_die"]  = g(64, 900, 0.34, "saw", attack_ms=4, decay_ms=820, noise_mix=0.45, vibrato=11)
        self.sfx["carcosa_boom"] = g(50, 1100, 0.55, "sine", attack_ms=2, decay_ms=950, noise_mix=0.45)
        self.sfx["door_locked"] = g(220, 80, 0.22, "square", attack_ms=2, decay_ms=50)
        # UI cues: soft sine pairs (fundamental + a quiet partial).
        # The pitch grammar of the old square/triangle chirps is kept
        # (open above close, confirm bright, cancel low) but the
        # timbre no longer reads as chiptune against the organic
        # soundscape. Dialog voice blips are NOT touched -- they are
        # character voices, not UI.
        self.sfx["menu_open"]   = self._build_ui_tone(392, 110, 0.20)
        self.sfx["menu_close"]  = self._build_ui_tone(294, 110, 0.20)
        self.sfx["cursor"]      = self._build_ui_tone(523, 35, 0.16)
        self.sfx["confirm"]     = self._build_ui_tone(523, 110, 0.20,
                                                      partial=1.5)
        self.sfx["cancel"]      = self._build_ui_tone(220, 100, 0.18)
        self.sfx["blip_low"]    = g(200, 35, 0.16, "square", attack_ms=2, decay_ms=20)
        self.sfx["blip_mid"]    = g(330, 35, 0.16, "square", attack_ms=2, decay_ms=20)
        self.sfx["blip_high"]   = g(550, 30, 0.14, "square", attack_ms=2, decay_ms=18)
        self.sfx["blip_soft"]   = g(420, 40, 0.10, "sine", attack_ms=4, decay_ms=30)
        self.sfx["blip_kid"]    = g(720, 28, 0.16, "triangle", attack_ms=2, decay_ms=18)
        self.sfx["blip_gruff"]  = g(160, 40, 0.18, "saw", attack_ms=2, decay_ms=25, noise_mix=0.2)
        self.sfx["pickup"]      = g(660, 110, 0.20, "sine", attack_ms=2, decay_ms=90)
        self.sfx["pickup_rare"] = g(880, 280, 0.24, "sine", attack_ms=20, decay_ms=240, vibrato=8)
        self.sfx["swing"]       = g(280, 100, 0.18, "saw", attack_ms=2, decay_ms=60, noise_mix=0.3)
        self.sfx["hit"]         = g(180, 70, 0.20, "noise", attack_ms=2, decay_ms=50, noise_mix=1.0)
        # The revolver. `gunshot` is the live report (crack + bark +
        # sub thump + air tail, soft-clipped); `gun_dry` is the empty
        # chamber -- two small hammer clicks, distinct from the
        # door_locked rattle it used to borrow.
        self.sfx["gunshot"]     = self._build_gunshot()
        self.sfx["gun_dry"]     = self._build_gun_dry()
        self.sfx["enemy_die"]   = g(110, 380, 0.22, "saw", attack_ms=10, decay_ms=320, noise_mix=0.4)
        self.sfx["heartbeat"]   = self._build_heartbeat()
        self.sfx["static"]      = g(0, 600, 0.25, "noise", attack_ms=20, decay_ms=400, noise_mix=1.0)
        self.sfx["wrong"]       = g(33, 900, 0.32, "saw", attack_ms=80, decay_ms=700)
        self.sfx["whisper"]     = self._build_whisper()
        self.sfx["arg_chime"]   = g(311, 480, 0.22, "sine", attack_ms=20, decay_ms=400, vibrato=2)
        # Depths ambient layers: a low droning chant + a wet exhale.
        # Played at intervals that tighten as the dread aperture
        # closes, so the rite gets louder the closer the player is
        # to being taken.
        self.sfx["cult_chant"]  = g(58, 1800, 0.22, "saw", attack_ms=120, decay_ms=1500, vibrato=2)
        self.sfx["cult_breath"] = g(0, 900, 0.20, "noise", attack_ms=120, decay_ms=700, noise_mix=1.0)
        # The King in Yellow's signature tone. Reversed-breath
        # filtered noise (sharp on, slow fade -- the air pulled
        # from the room) layered with two dissonant sub-sines
        # bending downward. Played ONLY while his sprite is on
        # screen, never reused.
        self.sfx["yk_tone"]     = self._build_yk_tone()
        # First-void-entry sting. Single short low-sine pulse with a
        # noise edge -- played once per session the first time the
        # player crosses into a substrate scene, since the transition
        # itself is now a single-frame swap.
        self.sfx["void_sting"]  = g(60, 140, 0.30, "sine", attack_ms=4, decay_ms=120, noise_mix=0.3)
        # Round-13: a faint, short child-humming sample played in
        # creepy non-village scenes. Built as a quick three-note
        # arpeggio of the village melody at low volume so it reads
        # as "a kid humming somewhere distant".
        self.sfx["child_hum"]   = self._build_child_hum()
        # THRESHOLD pursuit/surveillance SFX. None of these are loud
        # or melodic -- they exist to ride underneath the player's
        # ears and make the air feel occupied.
        # `breath`: a slow inhale. ~1.4s of low filtered noise that
        # rises in volume then cuts. Played by the Pursuer system at
        # increasing frequency the longer the player has been in a
        # scene without leaving.
        self.sfx["breath"]      = self._build_breath()
        # `phantom_step`: a footstep that isn't the player's. Lower
        # pitch + softer envelope than the regular step sounds so it
        # reads as "behind you and a little far" rather than your own
        # walk cycle.
        self.sfx["phantom_step"] = g(70, 110, 0.16, "noise",
                                      attack_ms=4, decay_ms=80,
                                      noise_mix=1.0)
        # `low_pulse`: a single sub-bass pulse used for the rare moment
        # the Pursuer manifests strongly (e.g. when the player stands
        # still too long, or when a Watcher just despawned). Carries a
        # 200 Hz partial so laptop speakers (which roll off ~120 Hz)
        # still register a thump.
        self.sfx["low_pulse"]    = self._build_low_pulse()
        # `falling_air`: the bed under the journal door-dream (NARRATIVE
        # 1b). Not a melody -- the rush of air past you as you fall, plus
        # a low howl that sinks and never lands. Looped under the cutscene.
        self.sfx["falling_air"] = self._build_falling_air()
        # ---- Chase loop ----------------------------------------------
        # The stealth heartbeat: cult LOS lock + lose, watcher curse
        # spawn + dispel, player hide enter + exit. Wired in
        # threat_mixin (_cult_tick state transitions, _spawn_watcher,
        # _dispel_watcher) and game.py (corn auto-hide, try_interact).
        # cult_lock also ducks music briefly so the sting lands clean.
        self.sfx["cult_lock"]      = self._build_cult_lock()
        self.sfx["cult_lose"]      = self._build_cult_lose()
        self.sfx["watcher_spawn"]  = self._build_watcher_spawn()
        self.sfx["watcher_dispel"] = self._build_watcher_dispel()
        self.sfx["hide_enter"]     = self._build_hide_enter()
        self.sfx["hide_exit"]      = self._build_hide_exit()
        # ---- Death + world-rot beats ---------------------------------
        # Bespoke death-card beds (CAPTURED / TAKEN INTO CUSTODY) so
        # those endings carry their own identity instead of the generic
        # low_pulse. Both run for the death-screen hold (~2.8s) on a
        # single play() call from _trigger_death. infest_throb fires on
        # each evidence-driven stage transition (the world rots more).
        # evidence_added is the small case-file chime per canonical
        # evidence beat. sheriff_hunt is the hollow lawman's signature.
        self.sfx["captured_bed"]   = self._build_captured_bed()
        self.sfx["custody_bed"]    = self._build_custody_bed()
        self.sfx["infest_throb"]   = self._build_infest_throb()
        self.sfx["evidence_added"] = self._build_evidence_added()
        self.sfx["sheriff_hunt"]   = self._build_sheriff_hunt()
        # ---- Living-house + rot-air ambients -------------------------
        # The surface ambience layer. Interiors carry a quiet stick-
        # slip creak + a rare knock (Scene.add_ambient schedules them);
        # the air then rots with the infestation stage -- drips at 1,
        # flies at 2, whisper + structural groan at 3 (wired in
        # InfestationMixin._apply_ambient_air on every scene load).
        self.sfx["wood_creak"] = self._build_wood_creak()
        self.sfx["wood_pop"]   = g(150, 90, 0.20, "sine", attack_ms=1,
                                   decay_ms=70, noise_mix=0.35)
        self.sfx["drip"]       = self._build_drip()
        self.sfx["flies"]      = self._build_flies()

        # ---- DSP atmosphere pass --------------------------------------
        # Route the horror SFX through the dsp reverb + filter toolkit so
        # they sit in a real acoustic space instead of ringing dry. The
        # SFX library is built ONCE and shared across every scene, so a
        # space can only be baked into a sound that always plays in that
        # same space -- otherwise a cellar tail would follow it outdoors.
        # Only context-fixed cues qualify: the underground rite (cellar),
        # the void / Carcosa set-pieces (void), and the opening-drive
        # radio static. Footsteps, blips, breaths and pulses that play
        # everywhere stay dry. No-ops cleanly if the toolkit is missing.
        _atmos = {
            # Underground rite -- only ever heard in the Works / Depths.
            "cult_chant":   dict(reverb="cellar"),
            "cult_breath":  dict(reverb="cellar", lowpass=2600),
            "step_void":    dict(reverb="cellar"),
            # Void / Carcosa set-pieces.
            "carcosa_boom": dict(reverb="void"),
            "void_sting":   dict(reverb="void"),
            # Opening drive -- the radio dissolving into static.
            "static":       dict(highpass=500),
            # The bell always rings over open ground (heard from the
            # tower, the street, the fields) -- bake the outdoor air in.
            "bell_toll":    dict(reverb="outdoor"),
        }
        for key, kw in _atmos.items():
            if key in self.sfx:
                self.sfx[key] = self._post(self.sfx[key], **kw)

        # ---- Scene-aware cue variants --------------------------------
        # Pre-bake cellar + outdoor reverb variants for the cues that
        # play in every kind of space (footsteps, the gunshot) so
        # play_in_scene can pick a scene-appropriate take at play
        # time. step_void is excluded -- it already has cellar reverb
        # baked above and is the void scenes' bespoke step. The dry
        # originals remain in self.sfx as the room fallback.
        for _cue in ("step_grass", "step_wood", "step_stone",
                     "step_carpet", "step_water", "gunshot"):
            if _cue not in self.sfx:
                continue
            dry = self.sfx[_cue]
            self.sfx[f"{_cue}_cellar"]  = self._post(dry, reverb="cellar")
            self.sfx[f"{_cue}_outdoor"] = self._post(dry, reverb="outdoor")

        # MUSIC. THRESHOLD's tracks are intentionally not melodies --
        # most are drones, two are haunted-with-pings versions of the
        # original lullaby/lilting tunes. Older cheerful definitions
        # of `home` and `village` were dictionary collisions (they
        # were overwritten further down) so they are removed.
        self.music = {
            # void: drone + rests. Notes carry a 4th-harmonic partial
            # so the sub-only fundamentals reach laptop speakers.
            "void": self._music_loop([
                (55,4.0),(58,4.0),(52,4.0),
                (0,2.0),(48,4.0),(0,2.0),(60,4.0),
            ], beat_ms=900, vol=0.22, wave="sine", mid_partial=4),
            # wrong: extra notes
            "wrong": self._music_loop([
                (41,2.0),(0,1.0),(43,2.0),(0,1.0),
                (39,3.0),(0,2.0),(37,3.0),(0,1.0),(45,2.0),
            ], beat_ms=700, vol=0.22, wave="saw"),
            # basement: low pulse, very sparse, 1 melodic motif. Mid
            # partials keep the triangle drone present on small speakers.
            "basement": self._music_loop([
                (49,3.0),(0,2.0),(55,2.0),(0,3.0),
                (52,2.0),(0,4.0),
            ], beat_ms=700, vol=0.20, wave="triangle", mid_partial=4),
            # wind: 'music' for the brimley -- a long stereo wind bed
            # with gust modulation and a leaf-rustle layer (above the
            # base noise drone). Stops entirely once the player takes
            # the first cult testimony in the Works; the silence is
            # the point.
            "wind": self._wind_loop(),
            # threshold_drone: deeper, more pitched than wind. Title
            # screen + the "world isn't right" takeover. Two stacked
            # low sines a tritone apart, no melody at all.
            "threshold_drone": self._threshold_drone(),
            # `home` and `village` are haunted-pings on a low drone
            # -- enough to suggest a tune was once there. The keys
            # are what the scene wiring passes; the audio is wrong.
            "home": self._haunted_home(),
            "village": self._haunted_village(),
            "outside": self._wind_loop(duration_ms=12000, vol=0.13),
        }
        # Opening-drive loops (played on their own channels, not "music").
        self.engine_snd = self._engine_loop()
        self.radio_snd = self._radio_loop()
        # Carcosa ending loops: the rite's dread drone + the unleashed roar.
        self.carcosa_drone_snd = self._carcosa_drone()
        self.carcosa_roar_snd = self._carcosa_roar()

    def _engine_loop(self, duration_ms=3000, vol=0.5):
        """A low engine idle: a rumble (stacked low sines) + rough noise,
        amplitude-modulated by a ~9 Hz 'chug' so it reads as cylinders
        firing rather than flat drone. Loop length holds whole cycles of
        every component so it tiles seamlessly."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            t = i / sr
            smooth = 0.7 * smooth + 0.3 * random.uniform(-1, 1)   # rough noise
            rumble = (math.sin(2 * math.pi * 46 * t) * 0.5
                      + math.sin(2 * math.pi * 92 * t) * 0.22)
            chug = 0.55 + 0.45 * abs(math.sin(2 * math.pi * 9 * t))
            v = (rumble + smooth * 0.5) * chug
            sample = max(-32768, min(32767, int(v * vol * 0.32 * 32767)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4] = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _carcosa_drone(self, duration_ms=2000, vol=0.5):
        """Low ominous drone for the mask-yank -- two detuned sub sines + a
        thin high tension shimmer. Loop length holds whole cycles."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        for i in range(n):
            t = i / sr
            v = math.sin(2 * math.pi * 46 * t) * 0.5 + math.sin(2 * math.pi * 69 * t) * 0.3
            v += math.sin(2 * math.pi * 1500 * t) * 0.04 * (0.6 + 0.4 * math.sin(2 * math.pi * 7 * t))
            env = 0.8 + 0.2 * math.sin(2 * math.pi * 0.5 * t)
            sample = max(-32768, min(32767, int(max(-1, min(1, v)) * vol * env * 32767)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4] = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _carcosa_roar(self, duration_ms=3000, vol=0.55):
        """The unleashing: filtered noise roar + a low rumble undertone."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            t = i / sr
            smooth = 0.9 * smooth + 0.1 * random.uniform(-1, 1)
            v = smooth * 0.6 + math.sin(2 * math.pi * 40 * t) * 0.3
            sample = max(-32768, min(32767, int(max(-1, min(1, v)) * vol * 32767)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4] = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _radio_loop(self):
        """A thin, somber hymn on the car radio -- tinny (square) and low,
        the kind of late-night gospel station that's the last thing on the
        dial out here. It dissolves into static as you cross into Brimley."""
        return self._music_loop([
            (196, 2), (220, 2), (174, 2), (196, 4),
            (146, 2), (164, 2), (196, 2), (174, 4),
        ], beat_ms=520, vol=0.13, wave="square")

    def _build_child_hum(self):
        """A short hummed phrase pulled from the village melody opening
        (440 / 523 / 659 -- A4, C5, E5). Triangle wave, very low volume,
        soft attack/decay envelope. Plays as a single SFX burst at
        random intervals in CREEPY_SCENES so the player hears a kid
        humming somewhere they shouldn't."""
        sr = 22050
        # Three short notes back to back, ~300ms each, gentle envelope.
        notes = [(440, 320), (523, 280), (659, 360)]
        total_samples = 0
        segs = []
        for f, ms in notes:
            n = int(sr * ms / 1000)
            seg = bytearray(n * 2)
            attack_n = max(1, int(sr * 0.04))
            decay_n = max(1, int(sr * 0.08))
            for i in range(n):
                t = i / sr
                # Triangle wave for a soft "hum" timbre.
                v = 2.0 * abs(2.0 * (f * t - math.floor(f * t + 0.5))) - 1.0
                if i < attack_n:
                    env = i / attack_n
                elif i > n - decay_n:
                    env = max(0.0, (n - i) / decay_n)
                else:
                    env = 0.85
                # Low volume -- the hum is meant to be barely audible.
                sample = int(v * 0.06 * env * 32767)
                sample = max(-32768, min(32767, sample))
                seg[i * 2] = sample & 0xFF
                seg[i * 2 + 1] = (sample >> 8) & 0xFF
            segs.append(seg)
            total_samples += n
        flat = bytearray()
        for s in segs:
            flat.extend(s)
        stereo = bytearray(total_samples * 4)
        for i in range(total_samples):
            stereo[i * 4]     = flat[i * 2]
            stereo[i * 4 + 1] = flat[i * 2 + 1]
            stereo[i * 4 + 2] = flat[i * 2]
            stereo[i * 4 + 3] = flat[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_yk_tone(self, duration_ms=2400, vol=0.32):
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        smooth2 = 0.0
        for i in range(n):
            t = i / sr
            # Reversed breath: sharp on at 0, decays over full
            # duration to silence. The opposite of a natural inhale.
            ramp = i / n
            env = (1.0 - ramp) ** 1.6
            # Slow LFO modulating the noise -- gives it a whispered
            # "trying to speak" texture instead of flat hiss.
            lfo = 0.55 + 0.45 * math.sin(2 * math.pi * 1.4 * t)
            smooth = 0.93 * smooth + 0.07 * random.uniform(-1, 1)
            noise = smooth * lfo * 0.55
            # Two sub-sines a tritone apart, bending downward over
            # the duration -- 51->39 and 72->55 Hz. The interval
            # never resolves; the pitch sinks as it decays.
            f1 = 51 - 12 * ramp
            f2 = 72 - 17 * ramp
            sine = (math.sin(2 * math.pi * f1 * t) * 0.40
                    + math.sin(2 * math.pi * f2 * t) * 0.28)
            # Tail cut so the sample doesn't click.
            tail = 1.0
            if i > n - 200:
                tail = max(0.0, (n - i) / 200)
            v = (noise + sine) * env * tail
            smooth2 = 0.85 * smooth2 + 0.15 * v
            sample = int(smooth2 * vol * 32767)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_breath(self, duration_ms=1400, vol=0.18):
        """A long inhale. Filtered noise that ramps from near-silence
        up to vol over the full duration, then cuts. The sharp cut at
        the end is intentional -- a normal breath would have a tail.
        Triggered by the Pursuer system as a non-spatial cue: the
        player hears a single inhale that has nothing to do with the
        room they're in."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            smooth = 0.94 * smooth + 0.06 * random.uniform(-1, 1)
            # Volume envelope: smooth ramp 0 -> 1 across full length,
            # cut to 0 in the last 30 samples.
            ramp = i / n
            env = ramp * ramp
            if i > n - 30:
                env *= max(0.0, (n - i) / 30)
            sample = int(smooth * vol * env * 32767)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _threshold_drone(self, duration_ms=12000, vol=0.18):
        """Two stacked low sines a tritone apart (41Hz + 58Hz), with
        a slow breathing envelope and a faint smoothed-noise layer.
        No melody, no rhythm, no resolution. The tritone sits as a
        permanent unresolved interval -- the ear keeps waiting for
        a third note that never comes. Used for the title screen
        and the late-game 'world is wrong' takeover. Mid partials at
        the 4th harmonic (164 + 232 Hz) preserve the tritone identity
        an octave-and-fifth up so laptop speakers still hear it."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            t = i / sr
            # Low tritone: 41Hz (E1-ish) + 58Hz (Bb1-ish). The interval
            # is dissonant at every scale -- below the level the ear
            # can fully resolve as pitch, but it still feels wrong.
            tone = (math.sin(2 * math.pi * 41 * t) * 0.55
                    + math.sin(2 * math.pi * 58 * t) * 0.40)
            # Mid partials (4 * fundamental) at -12 dB. Same musical
            # identity, audible on small speakers.
            mid = (math.sin(2 * math.pi * 164 * t) * 0.22
                   + math.sin(2 * math.pi * 232 * t) * 0.16)
            smooth = 0.93 * smooth + 0.07 * random.uniform(-1, 1)
            v = tone * 0.85 + mid + smooth * 0.20
            # Slow breathing envelope -- 0.7 .. 1.1 over ~14 seconds.
            env = 0.90 + 0.20 * math.sin(2 * math.pi * 0.07 * t)
            sample = int(v * vol * env * 32767)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _haunted_home(self, duration_ms=14000, vol=0.16):
        """Replacement for the original C-major lullaby. A low drone
        with a single high triangle-wave note that pings at irregular
        intervals -- the suggestion of a music box that has stopped
        winding down properly. The ping note is C5 for the first beat
        of the loop, then drifts a quarter-tone flat for the next
        ping. The drone underneath does not change."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        # Ping schedule: (start_seconds, freq, length_seconds)
        pings = [
            (1.5,  523, 0.40),
            (5.2,  517, 0.45),   # quarter-tone flat
            (9.8,  511, 0.50),
            (12.6, 506, 0.55),
        ]
        for i in range(n):
            t = i / sr
            drone = (math.sin(2 * math.pi * 49 * t) * 0.55
                     + math.sin(2 * math.pi * 196 * t) * 0.18)
            smooth = 0.92 * smooth + 0.08 * random.uniform(-1, 1)
            v = drone * 0.80 + smooth * 0.18
            for start, freq, length in pings:
                if start <= t < start + length:
                    local = t - start
                    # Triangle wave with soft attack/decay.
                    tri = 2.0 * abs(2.0 * (freq * t - math.floor(freq * t + 0.5))) - 1.0
                    if local < 0.05:
                        envp = local / 0.05
                    elif local > length - 0.15:
                        envp = max(0.0, (length - local) / 0.15)
                    else:
                        envp = 0.7
                    v += tri * 0.22 * envp
            env = 0.90 + 0.10 * math.sin(2 * math.pi * 0.05 * t)
            sample = int(v * vol * env * 32767)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _haunted_village(self, duration_ms=13000, vol=0.16):
        """The village no longer lilts. Same drone treatment as
        _haunted_home but with a sparser, lower ping pattern that
        only fires twice across the full loop -- a public square
        that used to have music, and now has only the memory of it."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        pings = [
            (3.0,  440, 0.55),
            (10.0, 415, 0.65),   # half-step flat
        ]
        for i in range(n):
            t = i / sr
            drone = (math.sin(2 * math.pi * 55 * t) * 0.50
                     + math.sin(2 * math.pi * 73 * t) * 0.30
                     + math.sin(2 * math.pi * 220 * t) * 0.16
                     + math.sin(2 * math.pi * 292 * t) * 0.11)
            smooth = 0.91 * smooth + 0.09 * random.uniform(-1, 1)
            v = drone * 0.75 + smooth * 0.20
            for start, freq, length in pings:
                if start <= t < start + length:
                    local = t - start
                    tri = 2.0 * abs(2.0 * (freq * t - math.floor(freq * t + 0.5))) - 1.0
                    if local < 0.06:
                        envp = local / 0.06
                    elif local > length - 0.20:
                        envp = max(0.0, (length - local) / 0.20)
                    else:
                        envp = 0.65
                    v += tri * 0.18 * envp
            env = 0.88 + 0.14 * math.sin(2 * math.pi * 0.04 * t)
            sample = int(v * vol * env * 32767)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_falling_air(self, duration_ms=4000, vol=0.20):
        """Wind-and-falling bed for the journal door-dream. Three layers:
        a broadband AIR RUSH (smoothed noise, the wind past your ears), a
        thin HISS on top (the high edge of speed), and a low HOWL whose
        pitch slowly sinks and rises like wind down a shaft -- phase is
        integrated sample-by-sample so the bend is a true glide, not an
        artefact. A slow swell makes the fall feel bottomless. Loop length
        holds whole cycles of the swell so it tiles under the cutscene."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        hiss = 0.0
        phase = 0.0
        for i in range(n):
            t = i / sr
            # Air rush: one-pole smoothed noise (the body of the wind).
            smooth = 0.90 * smooth + 0.10 * random.uniform(-1, 1)
            # Thin hiss: barely-smoothed noise, quiet, the speed's high edge.
            hiss = 0.55 * hiss + 0.45 * random.uniform(-1, 1)
            rush = smooth * 0.80 + hiss * 0.16
            # Howl: low pitch wandering 58..120 Hz on a slow LFO, integrated.
            fhz = 88.0 + 30.0 * math.sin(2 * math.pi * 0.25 * t)
            phase += 2 * math.pi * fhz / sr
            howl = math.sin(phase) * 0.22
            # Bottomless swell -- one whole cycle across the loop.
            swell = 0.72 + 0.28 * math.sin(2 * math.pi * 0.25 * t - 1.2)
            v = (rush + howl) * swell
            sample = int(max(-1.0, min(1.0, v)) * vol * 32767)
            sample = max(-32768, min(32767, sample))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_heartbeat(self, duration_ms=220, vol=0.32):
        """The dread heartbeat. 55 Hz sine fundamental for the chest
        thump, plus a 200 Hz partial at ~-12 dB so laptop speakers
        (which roll off around 120 Hz) still register a perceivable
        beat. The fundamental alone reads as SUB-ONLY on small
        speakers; the partial rescues it without changing the
        identity."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        attack_n = max(1, int(sr * 0.020))
        decay_n = max(1, int(sr * 0.180))
        for i in range(n):
            t = i / sr
            fund = math.sin(2 * math.pi * 55 * t)
            mid = math.sin(2 * math.pi * 200 * t) * 0.60
            v = fund + mid
            if i < attack_n:
                env = i / attack_n
            elif i > n - decay_n:
                env = max(0.0, (n - i) / decay_n)
            else:
                env = 1.0
            sample = max(-32768, min(32767,
                                     int(v * vol * env * 32767 / 1.60)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_low_pulse(self, duration_ms=480, vol=0.32):
        """Sub-bass pulse with a 200 Hz upper-bass partial so the cue
        survives laptop speakers. The 36 Hz fundamental alone is
        inaudible on most consumer hardware; the partial gives the
        speaker something to actually push."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        attack_n = max(1, int(sr * 0.040))
        decay_n = max(1, int(sr * 0.400))
        for i in range(n):
            t = i / sr
            fund = math.sin(2 * math.pi * 36 * t)
            mid = math.sin(2 * math.pi * 200 * t) * 0.65
            v = fund + mid
            if i < attack_n:
                env = i / attack_n
            elif i > n - decay_n:
                env = max(0.0, (n - i) / decay_n)
            else:
                env = 1.0
            sample = max(-32768, min(32767,
                                     int(v * vol * env * 32767 / 1.65)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_whisper(self, duration_ms=700, vol=0.38):
        """A human-formant whisper. Noise band-passed to 800-2200 Hz
        (vocal speech range, the 'sibilant + vowel' band) with a slow
        amplitude LFO so it breathes. The previous whisper was raw
        wide-band noise with a faint 290 Hz tone; centroid landed at
        5.5 kHz (HARSH flag) and read as hiss, not breath."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        # Build noise, then band-pass via highpass + lowpass chain.
        # _HAVE_DSP gates the filtering; falls back to dry noise if
        # numpy/scipy aren't installed (matches _post's no-op path).
        raw = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            smooth = 0.55 * smooth + 0.45 * random.uniform(-1, 1)
            sample = max(-32768, min(32767, int(smooth * 32767)))
            raw[i * 2] = sample & 0xFF
            raw[i * 2 + 1] = (sample >> 8) & 0xFF
        if _HAVE_DSP:
            import numpy as _np
            sig = (_np.frombuffer(bytes(raw), dtype=_np.int16)
                   .astype(_np.float32) / 32768.0)
            sig = dsp.highpass(sig, 800)
            sig = dsp.lowpass(sig, 2200)
            # Slow amplitude LFO (0.4 Hz) + attack/decay envelope.
            t = _np.arange(len(sig)) / sr
            lfo = 0.7 + 0.3 * _np.sin(2 * _np.pi * 0.4 * t)
            env = _np.ones_like(sig)
            attack_n = max(1, int(sr * 0.080))
            decay_n = max(1, int(sr * 0.500))
            env[:attack_n] = _np.linspace(0, 1, attack_n)
            env[-decay_n:] = _np.linspace(1, 0, decay_n)
            sig = sig * lfo * env
            return dsp.to_sound(sig, vol)
        # Fallback: dry stereo (no formant, but no failure).
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = raw[i * 2]
            stereo[i * 4 + 1] = raw[i * 2 + 1]
            stereo[i * 4 + 2] = raw[i * 2]
            stereo[i * 4 + 3] = raw[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_cult_lock(self, duration_ms=380, vol=0.34):
        """The 'you've been seen' sting. Plays once per fresh chase: a
        sub kick + broadband transient (the heart drop) over a held
        tritone (50Hz / 71Hz, unresolvable) that fades across the
        duration. Loud enough to read over wind / depths beds, short
        enough not to step on the chase music."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            t = i / sr
            # Sub kick: 50 Hz sine, hard attack, drops over 80 ms.
            kick_env = max(0.0, 1.0 - t / 0.080) ** 1.4
            kick = math.sin(2 * math.pi * 50 * t) * kick_env * 0.85
            # Broadband transient: noise burst, 30 ms.
            smooth = 0.6 * smooth + 0.4 * random.uniform(-1, 1)
            trans_env = max(0.0, 1.0 - t / 0.030) ** 1.3
            trans = smooth * trans_env * 0.55
            # Held tritone: 50 + 71 Hz sub-tones, fade across full duration.
            held_env = max(0.0, 1.0 - t / dur_s) ** 1.6
            held = (math.sin(2 * math.pi * 50 * t) * 0.30
                  + math.sin(2 * math.pi * 71 * t) * 0.22) * held_env
            tail = max(0.0, (n - i) / 200) if i > n - 200 else 1.0
            v = (kick + trans + held) * tail
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_cult_lose(self, duration_ms=520, vol=0.32):
        """The 'they don't see you anymore' breath-out. Soft attack,
        long decay, lower in the spectrum than cult_lock. Plays on the
        chase -> search transition when a cultist loses line of sight."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        smooth = 0.0
        phase = 0.0
        for i in range(n):
            t = i / sr
            smooth = 0.93 * smooth + 0.07 * random.uniform(-1, 1)
            # Envelope: 80 ms attack, then power-curve decay across the rest.
            if t < 0.080:
                env = t / 0.080
            else:
                env = max(0.0, 1.0 - (t - 0.080) / (dur_s - 0.080)) ** 1.2
            sigh = smooth * env * 0.65
            # Sub drone with a downward pitch glide (60 -> 45 Hz). The
            # falling pitch reads as release. Integrated phase so the
            # bend has no zipper artefacts.
            f = 60.0 - 15.0 * (t / dur_s)
            phase += 2 * math.pi * f / sr
            sub = math.sin(phase) * env * 0.45
            v = sigh + sub
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_watcher_spawn(self, duration_ms=320, vol=0.40):
        """A vacuum opening -- the moment another Watcher's eye binds.
        Reverse-envelope (silence -> swell -> hard cut), with a tonal
        kernel that emerges late. Non-spatial (the curse attaches to
        the player, not the room)."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        phase = 0.0
        for i in range(n):
            t = i / sr
            ramp = i / n
            env = ramp ** 1.4
            if i > n - 20:
                env *= max(0.0, (n - i) / 20)
            # Whisper-y noise: the inhale toward the eye opening.
            smooth = 0.92 * smooth + 0.08 * random.uniform(-1, 1)
            air = smooth * 0.85
            # Tonal kernel emerges in the last 130 ms.
            if t > 0.180:
                local = t - 0.180
                if local < 0.080:
                    k_env = local / 0.080
                else:
                    k_env = max(0.0, 1.0 - (local - 0.080) / 0.060)
                phase += 2 * math.pi * 800.0 / sr
                kernel = math.sin(phase) * k_env * 0.32
            else:
                kernel = 0.0
            v = (air + kernel) * env
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_watcher_dispel(self, duration_ms=480, vol=0.36):
        """A Watcher's eye closes. Forward attack, long decay, with a
        pitched element that drops 700 -> 300 Hz across the duration.
        Plays on gaze-dispel, gun, or axe kill (same cue, since 'the
        eye closes' reads whichever way it dies)."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        phase = 0.0
        for i in range(n):
            t = i / sr
            ramp = i / n
            if ramp < 0.10:
                env = ramp / 0.10
            else:
                env = max(0.0, 1.0 - (ramp - 0.10) / 0.90) ** 1.3
            smooth = 0.90 * smooth + 0.10 * random.uniform(-1, 1)
            air = smooth * 0.70
            # 700 -> 300 Hz glide via integrated phase.
            f = 700.0 - 400.0 * ramp
            phase += 2 * math.pi * f / sr
            tone = math.sin(phase) * 0.40
            v = (air + tone) * env
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_ui_tone(self, freq, duration_ms, vol, partial=2.0,
                       partial_amp=0.30):
        """Soft UI cue: a sine fundamental + a quiet upper partial
        (default the octave; 1.5 gives a warm fifth), eased attack and
        a curved decay. The menu grammar lives in the pitch
        relationships, so callers only choose freq/length."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        attack_n = max(1, int(sr * 0.006))
        norm = 1.0 / (1.0 + partial_amp)
        for i in range(n):
            t = i / sr
            v = (math.sin(2 * math.pi * freq * t)
                 + math.sin(2 * math.pi * freq * partial * t) * partial_amp)
            if i < attack_n:
                env = i / attack_n
            else:
                env = max(0.0, 1.0 - (t - 0.006) / (dur_s - 0.006)) ** 1.3
            sample = max(-32768, min(32767,
                                     int(v * norm * vol * env * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_door_open(self, duration_ms=520, vol=0.30):
        """A real door opens: the latch frees (a small metallic ping +
        noise snap at t=0), then the hinge creaks as it swings -- a
        stick-slip tone rising 150 -> 240 Hz with grain flutter, the
        wood_creak friction trick, brighter and shorter."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        phase = 0.0
        smooth = 0.0
        grain = 0.0
        for i in range(n):
            t = i / sr
            latch = 0.0
            if t < 0.030:
                latch = (math.sin(2 * math.pi * 1500 * t)
                         * math.exp(-t / 0.006) * 0.55
                         + random.uniform(-1, 1)
                         * math.exp(-t / 0.004) * 0.45)
            creak = 0.0
            if t >= 0.050:
                local = t - 0.050
                ramp = local / (dur_s - 0.050)
                smooth = 0.92 * smooth + 0.08 * random.uniform(-1, 1)
                f = (150.0 + 90.0 * ramp
                     + 12.0 * math.sin(2 * math.pi * 7.1 * local)
                     + smooth * 12.0)
                phase += 2 * math.pi * max(60.0, f) / sr
                grain = 0.55 * grain + 0.45 * random.uniform(-1, 1)
                gate = 0.60 + 0.40 * grain
                if ramp < 0.18:
                    envc = ramp / 0.18
                else:
                    envc = max(0.0, 1.0 - (ramp - 0.18) / 0.82) ** 1.1
                creak = math.sin(phase) * gate * envc * 0.55
            v = latch + creak
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_door_close(self, duration_ms=430, vol=0.32):
        """A real door closes: a soft swing of air, the frame thud at
        t=0.20 (70 Hz kick + a noise burst), and the latch catching
        just after. Sibling of _build_door_open."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            t = i / sr
            smooth = 0.88 * smooth + 0.12 * random.uniform(-1, 1)
            whoosh = 0.0
            if t < 0.20:
                whoosh = smooth * math.sin(math.pi * t / 0.20) * 0.30
            thud = 0.0
            if t >= 0.20:
                local = t - 0.20
                thud = (math.sin(2 * math.pi * 70 * t)
                        * math.exp(-local / 0.070) * 0.85
                        + smooth * math.exp(-local / 0.018) * 0.50)
            latch = 0.0
            if t >= 0.30:
                local = t - 0.30
                latch = (math.sin(2 * math.pi * 1200 * t)
                         * math.exp(-local / 0.005) * 0.35
                         + random.uniform(-1, 1)
                         * math.exp(-local / 0.003) * 0.30)
            v = whoosh + thud + latch
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_bell_toll(self, duration_ms=3400, vol=0.42, f0=195.0):
        """One strike of a bronze church bell, left to ring. Real bell
        voicing: an inharmonic partial stack over the prime -- the hum
        an octave under (doubled a hair sharp so the pair BEATS, the
        slow wow of a big bell), the minor-third tierce that makes
        church bells sound mournful, quint, nominal, and two fast high
        partials that are mostly gone by the first half-second. Each
        partial decays at its own rate (high dies fast, hum outlasts
        everything), plus a click-and-noise strike transient."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        # (ratio to f0, amplitude, decay tau seconds)
        partials = (
            (0.500, 0.55, 1.90),      # hum
            (0.504, 0.30, 1.90),      # hum's beating twin (~0.8 Hz wow)
            (1.000, 0.50, 1.10),      # prime
            (1.200, 0.42, 0.90),      # tierce (the minor third)
            (1.500, 0.26, 0.70),      # quint
            (2.000, 0.36, 0.55),      # nominal
            (2.670, 0.16, 0.28),      # upper partials: the strike's
            (4.100, 0.10, 0.14),      #   metallic edge, gone fast
        )
        norm = 1.0 / sum(a for _r, a, _t in partials)
        for i in range(n):
            t = i / sr
            v = 0.0
            for ratio, amp, tau in partials:
                v += (math.sin(2 * math.pi * f0 * ratio * t)
                      * amp * math.exp(-t / tau))
            v *= norm
            if t < 0.012:
                # the clapper: a hard click + a breath of noise
                v += (math.sin(2 * math.pi * 2400 * t)
                      * math.exp(-t / 0.003) * 0.35
                      + random.uniform(-1, 1)
                      * math.exp(-t / 0.004) * 0.30)
            # 4 ms attack so the strike doesn't pop the speaker
            if t < 0.004:
                v *= t / 0.004
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _mono_to_sound(self, buf, n):
        """Duplicate a filled mono int16 bytearray into a stereo
        Sound -- the shared tail of every bespoke builder."""
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_cans_rattle(self, duration_ms=380, vol=0.30):
        """A boot through strewn tins: a scuff of noise at contact,
        then four small metallic pings knocked loose at staggered
        offsets, each a short ringing sine at its own pitch."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        pings = [(0.020, 1180.0), (0.075, 860.0),
                 (0.150, 1420.0), (0.235, 990.0)]
        for i in range(n):
            t = i / sr
            v = 0.0
            if t < 0.045:
                v += random.uniform(-1, 1) * math.exp(-t / 0.014) * 0.55
            for t0, f in pings:
                if t >= t0:
                    local = t - t0
                    v += (math.sin(2 * math.pi * f * local)
                          * math.exp(-local / 0.035) * 0.42)
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        return self._mono_to_sound(buf, n)

    def _build_glass_crunch(self, duration_ms=260, vol=0.28):
        """Glass litter underfoot: a dense fast-decaying crunch with
        three high tinks riding it -- shards pressed and split."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        tinks = [(0.015, 3400.0), (0.060, 2650.0), (0.115, 3900.0)]
        for i in range(n):
            t = i / sr
            v = random.uniform(-1, 1) * math.exp(-t / 0.045) * 0.6
            for t0, f in tinks:
                if t >= t0:
                    local = t - t0
                    v += (math.sin(2 * math.pi * f * local)
                          * math.exp(-local / 0.010) * 0.35)
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        return self._mono_to_sound(buf, n)

    def _build_crow_flush(self, duration_ms=820, vol=0.32):
        """A crow bursting off the ground: wingbeats as gated noise
        (~11 Hz flaps that recede as it climbs away) under one harsh
        caw -- a rough tone falling 950 -> 600 Hz with a torn noise
        edge."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            t = i / sr
            smooth = 0.80 * smooth + 0.20 * random.uniform(-1, 1)
            flap_gate = max(0.0, math.sin(2 * math.pi * 11.0 * t)) ** 2
            recede = max(0.0, 1.0 - t / dur_s) ** 1.2
            v = smooth * flap_gate * recede * 0.6
            if 0.10 <= t < 0.30:
                local = (t - 0.10) / 0.20
                f = 950.0 - 350.0 * local
                caw_env = math.sin(math.pi * local)
                v += ((math.sin(2 * math.pi * f * t) * 0.55
                       + random.uniform(-1, 1) * 0.45)
                      * caw_env * 0.55)
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        return self._mono_to_sound(buf, n)

    def _build_radio_snatch(self, duration_ms=1300, vol=0.26):
        """One bar of the dead station: three notes that don't resolve
        (a tune remembered wrong), each a sine doubled a hair sharp so
        it wows, over a constant bed of low static. Cut off mid-phrase
        with a short fade -- the source loops it every period, so the
        snatch never finishes."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        notes = [(0.00, 392.0), (0.45, 466.2), (0.90, 349.2)]
        for i in range(n):
            t = i / sr
            v = random.uniform(-1, 1) * 0.14        # the static bed
            for t0, f in notes:
                if t0 <= t < t0 + 0.42:
                    local = t - t0
                    env = math.sin(math.pi * min(1.0, local / 0.42))
                    trem = 0.75 + 0.25 * math.sin(2 * math.pi * 5.5 * t)
                    v += ((math.sin(2 * math.pi * f * t)
                           + math.sin(2 * math.pi * f * 1.012 * t))
                          * 0.5 * env * trem * 0.55)
            if t > dur_s - 0.03:                    # de-click the loop cut
                v *= (dur_s - t) / 0.03
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        return self._mono_to_sound(buf, n)

    def _build_valve_hiss(self, duration_ms=1000, vol=0.30):
        """The opened works valve: steam swelling through the line
        (smoothed noise) with two pipe knocks banging down the run as
        the pressure walks it."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            t = i / sr
            smooth = 0.90 * smooth + 0.10 * random.uniform(-1, 1)
            swell = min(1.0, t / 0.15) * max(0.0, 1.0 - t / dur_s) ** 0.7
            v = smooth * swell * 0.55
            for t0 in (0.15, 0.55):
                if t >= t0:
                    local = t - t0
                    v += (math.sin(2 * math.pi * 150.0 * local)
                          * math.exp(-local / 0.040) * 0.5)
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        return self._mono_to_sound(buf, n)

    def _build_wood_creak(self, duration_ms=750, vol=0.30):
        """An old joist easing -- stick-slip friction. A narrow tone
        sinking 260 -> 110 Hz with a slow wobble and a coarse grain
        flutter (the slip is uneven), over a faint smoothed-noise
        body. Quiet by design: it plays under the home drone at the
        edge of attention, panned randomly so the house creaks from
        somewhere."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        phase = 0.0
        smooth = 0.0
        grain = 0.0
        for i in range(n):
            t = i / sr
            ramp = i / n
            smooth = 0.92 * smooth + 0.08 * random.uniform(-1, 1)
            # Sinking pitch with wobble + noise jitter, integrated so
            # the bend glides without zipper artefacts.
            f = (260.0 - 150.0 * ramp
                 + 16.0 * math.sin(2 * math.pi * 6.3 * t)
                 + smooth * 14.0)
            phase += 2 * math.pi * max(60.0, f) / sr
            tone = math.sin(phase)
            # Grain flutter: barely-smoothed noise gating the tone.
            grain = 0.55 * grain + 0.45 * random.uniform(-1, 1)
            gate = 0.62 + 0.38 * grain
            if t < 0.12:
                env = t / 0.12
            elif t > dur_s - 0.25:
                env = max(0.0, (dur_s - t) / 0.25)
            else:
                env = 1.0
            v = (tone * gate * 0.80 + smooth * 0.18) * env
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_drip(self, duration_ms=190, vol=0.30):
        """A single wet drip. The classic plink: a short sine whose
        pitch RISES 950 -> 1500 Hz as the droplet's cavity closes,
        over a tiny low plop at the front. Stage-1 rot air."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        phase = 0.0
        for i in range(n):
            t = i / sr
            ramp = i / n
            f = 950.0 + 550.0 * ramp * ramp
            phase += 2 * math.pi * f / sr
            plink = math.sin(phase) * math.exp(-t / 0.060)
            plop = math.sin(2 * math.pi * 180 * t) * math.exp(-t / 0.020) * 0.5
            env = min(1.0, t / 0.002)
            if i > n - 60:
                env *= max(0.0, (n - i) / 60)
            v = (plink + plop) * env
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_flies(self, duration_ms=2200, vol=0.26):
        """A knot of flies passing. Two detuned voices (saw softened
        with a sine at the same phase) whose pitches wander on a fast
        random walk (the swerve), amplitude-fluttered ~24 Hz (the
        wingbeat), under a swell-in / swell-out envelope so the swarm
        drifts near and away rather than switching on. Stage-2 rot
        air, indoors and out."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        f1, f2 = 168.0, 233.0
        p1 = p2 = 0.0
        smooth = 0.0
        for i in range(n):
            t = i / sr
            f1 = min(260.0, max(120.0, f1 + random.uniform(-0.9, 0.9)))
            f2 = min(330.0, max(170.0, f2 + random.uniform(-1.1, 1.1)))
            p1 += 2 * math.pi * f1 / sr
            p2 += 2 * math.pi * f2 / sr
            v1 = (2.0 * ((p1 / (2 * math.pi)) % 1.0) - 1.0) * 0.5 \
                + math.sin(p1) * 0.5
            v2 = (2.0 * ((p2 / (2 * math.pi)) % 1.0) - 1.0) * 0.5 \
                + math.sin(p2) * 0.5
            flutter = 0.62 + 0.38 * math.sin(
                2 * math.pi * 24 * t + 1.7 * math.sin(2 * math.pi * 3 * t))
            swell = math.sin(math.pi * min(1.0, t / dur_s)) ** 1.5
            smooth = 0.80 * smooth + 0.20 * random.uniform(-1, 1)
            v = ((v1 * 0.55 + v2 * 0.40) * flutter + smooth * 0.08) * swell
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 1] = stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_gunshot(self, duration_ms=850, vol=0.50):
        """The revolver report. Four layers: an instant broadband
        CRACK (the muzzle blast, ~12 ms), a mid BARK whose pitch drops
        320 -> 140 Hz in the first 120 ms (the body of the report), a
        65 Hz SUB thump (the chest punch), and a low-passed noise TAIL
        (the air settling after, ~0.4 s). The mix is soft-clipped so
        it reads compressed and loud the way a close gunshot does on
        small speakers. Scene-reverb variants are baked alongside the
        footsteps, so a shot indoors slaps and a shot in the open
        rolls away. Replaces the old swing + bump pair, which read as
        a whoosh plus walking into a wall."""
        if not _HAVE_DSP:
            return self._gen(90, 320, 0.55, "noise", attack_ms=1,
                             decay_ms=300, noise_mix=1.0)
        import numpy as _np
        sr = 22050
        n = int(sr * duration_ms / 1000)
        t = _np.arange(n, dtype=_np.float32) / sr
        rng = _np.random.default_rng()
        crack = (rng.uniform(-1.0, 1.0, n).astype(_np.float32)
                 * _np.exp(-t / 0.012))
        f = 320.0 - 180.0 * _np.clip(t / 0.120, 0.0, 1.0)
        phase = _np.cumsum(2 * _np.pi * f / sr).astype(_np.float32)
        bark = _np.sin(phase) * _np.exp(-t / 0.070) * 0.85
        sub = _np.sin(2 * _np.pi * 65 * t) * _np.exp(-t / 0.100) * 0.75
        tail = dsp.lowpass(rng.uniform(-1.0, 1.0, n).astype(_np.float32),
                           1600)
        tail = tail * _np.exp(-t / 0.28) * _np.minimum(1.0, t / 0.015) * 0.40
        mix = crack * 0.90 + bark + sub + tail
        mix = _np.tanh(mix * 1.6) / math.tanh(1.6)
        return dsp.to_sound(mix, vol)

    def _build_gun_dry(self, duration_ms=170, vol=0.40):
        """Empty chamber. Two small mechanical clicks ~70 ms apart
        (hammer back, hammer fall) -- thin high transients with no
        body, so the cue reads as the gun itself rather than the
        door_locked rattle it used to borrow."""
        if not _HAVE_DSP:
            return self._gen(1400, 50, 0.30, "square", attack_ms=1,
                             decay_ms=30, noise_mix=0.4)
        import numpy as _np
        sr = 22050
        n = int(sr * duration_ms / 1000)
        t = _np.arange(n, dtype=_np.float32) / sr
        rng = _np.random.default_rng()
        out = _np.zeros(n, dtype=_np.float32)
        for click_t, f, amp in ((0.0, 1900.0, 0.55), (0.07, 1300.0, 0.85)):
            local = t - click_t
            env = _np.where(local >= 0,
                            _np.exp(-_np.maximum(local, 0.0) / 0.008),
                            0.0).astype(_np.float32)
            n_env = _np.where(local >= 0,
                              _np.exp(-_np.maximum(local, 0.0) / 0.004),
                              0.0).astype(_np.float32)
            out += _np.sin(2 * _np.pi * f * t) * env * amp
            out += rng.uniform(-1.0, 1.0, n).astype(_np.float32) * n_env * 0.45
        return dsp.to_sound(_np.clip(out, -1.0, 1.0), vol)

    def _build_hide_enter(self, duration_ms=200, vol=0.28):
        """Muffled thump + quick breath-in. Plays when player.hidden
        flips true (corn, under furniture)."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            t = i / sr
            # Sub kick at 80 Hz, decays in 60 ms.
            kick_env = max(0.0, 1.0 - t / 0.060) ** 1.3
            kick = math.sin(2 * math.pi * 80 * t) * kick_env * 0.55
            # Breath-in: low-pass noise rising for 80 ms then falling.
            smooth = 0.85 * smooth + 0.15 * random.uniform(-1, 1)
            if t < 0.080:
                b_env = t / 0.080
            else:
                b_env = max(0.0, 1.0 - (t - 0.080) / 0.120)
            breath = smooth * b_env * 0.40
            v = kick + breath
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_hide_exit(self, duration_ms=220, vol=0.32):
        """Soft breath-out + faint warmth. The 'standing back up' cue,
        sibling to hide_enter. Plays when player.hidden flips false."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            t = i / sr
            smooth = 0.88 * smooth + 0.12 * random.uniform(-1, 1)
            if t < 0.060:
                env = t / 0.060
            else:
                env = max(0.0, 1.0 - (t - 0.060) / 0.160) ** 1.1
            breath = smooth * env * 0.55
            # Faint warmth: 180 Hz sine pinned to the breath envelope.
            warm = math.sin(2 * math.pi * 180 * t) * env * 0.20
            v = breath + warm
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767)))
            buf[i * 2] = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_captured_bed(self, duration_ms=2800, vol=0.32):
        """The CAPTURED death-card bed. The cult has taken you for the
        hive. 2.8s, plays once on _trigger_death('cultist') over the
        death-screen hold. Numpy-vectorised so the synth doesn't add
        notable cost at startup.

        Beats in order: a grab thud (sub kick + breath spike), three
        chant voices entering at descending pitches with vibrato
        (58/65/72 Hz saws), a whisper layer in the vocal-formant
        band that builds as they drag you, and a final descending
        sub-glide as you go under."""
        if not _HAVE_DSP:
            return self._silent_stereo(duration_ms)
        import numpy as _np
        sr = 22050
        n = int(sr * duration_ms / 1000)
        t = _np.arange(n, dtype=_np.float32) / sr
        # Grab thud at t=0: 50 Hz sine + broadband noise spike, 250ms.
        kick_env = _np.exp(-t / 0.080).astype(_np.float32)
        rng = _np.random.default_rng()
        thud_noise = rng.uniform(-1.0, 1.0, n).astype(_np.float32)
        thud_noise_env = _np.exp(-t / 0.030).astype(_np.float32)
        kick = (_np.sin(2 * _np.pi * 50 * t) * 0.85 * kick_env
                + thud_noise * 0.55 * thud_noise_env)
        # Three chant voices, entering at t=0.3 / 0.6 / 0.9, holding
        # to ~2.0s. Saw waves with vibrato; pitches 58/65/72 Hz.
        def _chant(f, start, hold, vib_hz):
            mask = (t >= start) & (t < start + hold)
            local = _np.where(mask, t - start, 0.0)
            attack = _np.minimum(1.0, local / 0.30)
            decay = _np.maximum(0.0, 1.0 - (local - hold + 0.40) / 0.40)
            env = _np.where(mask, attack * decay, 0.0)
            # Saw wave with frequency vibrato.
            vib = 1.0 + 0.04 * _np.sin(2 * _np.pi * vib_hz * t)
            phase = _np.cumsum(2 * _np.pi * f * vib / sr).astype(_np.float32)
            saw = (2.0 * (phase / (2 * _np.pi)
                          - _np.floor(0.5 + phase / (2 * _np.pi))))
            return (saw * env).astype(_np.float32)
        chant = (_chant(58, 0.30, 1.80, 2.0) * 0.32
                 + _chant(65, 0.60, 1.50, 2.3) * 0.26
                 + _chant(72, 0.90, 1.20, 2.7) * 0.22)
        # Whisper band-passed (vocal formant), ramps in from t=1.0.
        breath = rng.uniform(-1.0, 1.0, n).astype(_np.float32)
        breath = dsp.highpass(breath, 800)
        breath = dsp.lowpass(breath, 2200)
        breath_env = _np.maximum(0.0, _np.minimum(1.0, (t - 1.0) / 0.80))
        breath_env = breath_env * _np.maximum(0.0, 1.0 - _np.maximum(0.0, t - 2.4) / 0.4)
        breath_layer = breath * 0.45 * breath_env
        # Final descending sub-glide t=2.3 -> 2.8, 80 -> 30 Hz.
        glide_mask = (t >= 2.3)
        glide_local = _np.where(glide_mask, (t - 2.3) / 0.5, 0.0)
        glide_f = _np.where(glide_mask, 80.0 - 50.0 * glide_local, 0.0)
        glide_phase = _np.cumsum(2 * _np.pi * glide_f / sr).astype(_np.float32)
        glide_env = _np.where(glide_mask,
                              _np.minimum(1.0, glide_local / 0.10)
                              * _np.maximum(0.0, 1.0 - (glide_local - 0.10) / 0.90),
                              0.0)
        glide = _np.sin(glide_phase) * 0.40 * glide_env
        mono = kick + chant + breath_layer + glide
        mono = _np.clip(mono * vol, -1.0, 1.0)
        stereo = _np.column_stack([mono, mono])
        return pygame.sndarray.make_sound((stereo * 32767)
                                          .astype(_np.int16))

    def _build_custody_bed(self, duration_ms=2800, vol=0.42):
        """The TAKEN INTO CUSTODY death-card bed. The hollow Sheriff
        takes you in. 2.8s, plays once on _trigger_death('sheriff').

        Beats: three slow boot thuds at t=0/0.5/1.0 (the lawman's
        weight settling), a metallic cuff click at t=1.2, dead-air
        silence over a thin sub rumble t=1.4-2.4, then a deep door
        slam at t=2.5 as the room closes."""
        if not _HAVE_DSP:
            return self._silent_stereo(duration_ms)
        import numpy as _np
        sr = 22050
        n = int(sr * duration_ms / 1000)
        t = _np.arange(n, dtype=_np.float32) / sr
        rng = _np.random.default_rng()
        out = _np.zeros(n, dtype=_np.float32)
        # Three boot thuds: 45 Hz sub kick + brief mid noise.
        for boot_t in (0.0, 0.50, 1.00):
            local = t - boot_t
            env = _np.where(local >= 0,
                            _np.exp(-local / 0.10), 0.0).astype(_np.float32)
            noise_env = _np.where(local >= 0,
                                  _np.exp(-local / 0.020), 0.0).astype(_np.float32)
            kick = _np.sin(2 * _np.pi * 45 * t) * env * 0.75
            scrape = rng.uniform(-1.0, 1.0, n).astype(_np.float32) * noise_env * 0.40
            out += kick + scrape
        # Cuff click at t=1.20: high transient (1200 Hz pluck + mid).
        click_t = 1.20
        click_local = t - click_t
        click_env = _np.where(click_local >= 0,
                              _np.exp(-click_local / 0.040), 0.0).astype(_np.float32)
        click = (_np.sin(2 * _np.pi * 1200 * t) * 0.30
                 + _np.sin(2 * _np.pi * 800 * t) * 0.20) * click_env
        out += click
        # Dead-air rumble t=1.4-2.4: thin sub at 40 Hz.
        rumble_mask = (t >= 1.4) & (t < 2.4)
        rumble = _np.where(rumble_mask,
                           _np.sin(2 * _np.pi * 40 * t) * 0.22, 0.0)
        out += rumble
        # Door slam at t=2.50: 55 Hz sub kick + broadband noise burst,
        # 250ms decay (heavy room-closing).
        slam_t = 2.50
        slam_local = t - slam_t
        slam_env = _np.where(slam_local >= 0,
                             _np.exp(-slam_local / 0.120), 0.0).astype(_np.float32)
        slam_noise_env = _np.where(slam_local >= 0,
                                   _np.exp(-slam_local / 0.040), 0.0).astype(_np.float32)
        slam = (_np.sin(2 * _np.pi * 55 * t) * 0.85 * slam_env
                + rng.uniform(-1.0, 1.0, n).astype(_np.float32)
                  * 0.55 * slam_noise_env)
        out += slam
        out = _np.clip(out * vol, -1.0, 1.0)
        stereo = _np.column_stack([out, out])
        return pygame.sndarray.make_sound((stereo * 32767)
                                          .astype(_np.int16))

    def _build_infest_throb(self, duration_ms=1600, vol=0.34):
        """A wet structural groan -- the world rots one stage further.
        Plays on each infestation stage transition (0->1, 1->2, 2->3).
        Slow attack so it reads as ambient pressure rather than a hit;
        sub fundamental + mid partial so laptop speakers carry it."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        smooth = 0.0
        phase = 0.0
        for i in range(n):
            tt = i / sr
            # Sub fundamental sliding downward 70 -> 35 Hz across the
            # duration -- pitch sinking = world giving way.
            f = 70.0 - 35.0 * (tt / dur_s)
            phase += 2 * math.pi * f / sr
            fund = math.sin(phase) * 0.65
            # Mid partial at 3x the (initial) fundamental so the cue
            # carries on small speakers.
            mid = math.sin(2 * math.pi * 210 * tt) * 0.22
            # Noise layer for the "structural" texture (creaking,
            # settling); smoothed so it isn't bright.
            smooth = 0.91 * smooth + 0.09 * random.uniform(-1, 1)
            noise = smooth * 0.35
            # Slow attack 400ms, slow decay across the rest.
            if tt < 0.40:
                env = (tt / 0.40) ** 1.5
            else:
                env = max(0.0, 1.0 - (tt - 0.40) / (dur_s - 0.40)) ** 1.2
            v = (fund + mid + noise) * env
            sample = max(-32768, min(32767,
                                     int(max(-1.0, min(1.0, v))
                                         * vol * 32767 / 1.20)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_evidence_added(self, duration_ms=420, vol=0.28):
        """A small warm chime for case-file beats -- played the moment
        a canonical evidence entry is appended. Two stacked sines at
        a perfect fifth (440 + 660 Hz) with a soft attack and a long
        decay. Warmer than `confirm`, colder than `pickup_rare` so it
        reads as 'noted' rather than 'won'."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        attack_n = max(1, int(sr * 0.030))
        for i in range(n):
            tt = i / sr
            # Slight vibrato on the upper voice, none on the lower.
            v1 = math.sin(2 * math.pi * 440 * tt) * 0.55
            v2 = math.sin(2 * math.pi * 660 * tt
                          + 0.10 * math.sin(2 * math.pi * 4.5 * tt)) * 0.40
            if i < attack_n:
                env = i / attack_n
            else:
                env = max(0.0, 1.0 - (tt - 0.030) / (dur_s - 0.030)) ** 1.4
            v = (v1 + v2) * env
            sample = max(-32768, min(32767, int(v * vol * 32767)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _build_sheriff_hunt(self, duration_ms=620, vol=0.40):
        """The hollow Sheriff's signature: a slow heavy boot thud + a
        held sub-tone (his presence). Fired on _spawn_hunting_sheriff
        and again when his intro ends and he starts chasing. The
        sub-tone holds across the duration so the cue lingers as
        'something just settled into the room'."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        dur_s = duration_ms / 1000.0
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            tt = i / sr
            # Boot thud: 45 Hz sub-kick with fast decay (180ms).
            kick_env = max(0.0, math.exp(-tt / 0.090))
            kick = math.sin(2 * math.pi * 45 * tt) * 0.85 * kick_env
            # Mid scrape: brief 220 Hz noise body (50ms).
            smooth = 0.55 * smooth + 0.45 * random.uniform(-1, 1)
            scrape_env = max(0.0, math.exp(-tt / 0.025))
            scrape = smooth * 0.40 * scrape_env
            # Held sub-tone: 60 Hz sine across the full duration with a
            # slow fade. Reads as 'his weight, sitting in the room'.
            hold_env = max(0.0, 1.0 - tt / dur_s) ** 1.4
            hold = math.sin(2 * math.pi * 60 * tt) * 0.32 * hold_env
            v = kick + scrape + hold
            sample = max(-32768, min(32767, int(max(-1.0, min(1.0, v))
                                                * vol * 32767 / 1.30)))
            buf[i * 2]     = sample & 0xFF
            buf[i * 2 + 1] = (sample >> 8) & 0xFF
        stereo = bytearray(n * 4)
        for i in range(n):
            stereo[i * 4]     = buf[i * 2]
            stereo[i * 4 + 1] = buf[i * 2 + 1]
            stereo[i * 4 + 2] = buf[i * 2]
            stereo[i * 4 + 3] = buf[i * 2 + 1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def flashback_air(self, on, volume=0.9):
        """Loop / stop the falling-air bed on the ambient channel for the
        journal door-dream. Mirrors king_tone's pattern (own channel, clean
        fade-out) so the cutscene owns the soundscape end to end."""
        if not self.enabled or self.ambient_channel is None:
            return
        if on:
            self.ambient_channel.play(self.sfx["falling_air"], loops=-1)
            self.ambient_channel.set_volume(
                max(0.0, min(1.0, volume)) * self._sfx_gain())
        else:
            self.ambient_channel.fadeout(600)

    def _wind_loop(self, duration_ms=24000, vol=0.28):
        """Wind ambient bed for Brimley. Long stereo loop with gust
        modulation and a leaf-rustle layer above the base noise drone.

        Four perceptual layers:
          * BASE     -- smoothed noise (the body of the air), independent
                        L/R streams so the field has width
          * GUSTS    -- scheduled at irregular intervals; each one
                        ramps amplitude + opens the rustle band
          * RUSTLE   -- thin barely-smoothed noise that only opens
                        during gust peaks (wind through dry leaves)
          * UNDERTONE -- low pitched body (55 Hz + 220 Hz partial so
                         laptop speakers carry the body)

        24 s is long enough that a full Brimley walk won't catch the
        loop point. Stereo decorrelation gives the bed depth so it
        doesn't read as a single noise source.

        Implementation is numpy-vectorised: building this in a pure
        Python sample loop took ~4 s at Audio init; vectorised it's
        ~0.2 s. Falls back to a no-op silent loop if numpy isn't
        available (matches dsp.py's optional-import pattern)."""
        if not _HAVE_DSP:
            return self._silent_stereo(duration_ms)
        import numpy as _np
        sr = 22050
        n = int(sr * duration_ms / 1000)
        t = _np.arange(n, dtype=_np.float32) / sr
        rng = _np.random.default_rng()
        # Gust envelope: triangle pulses with asymmetric attack/release.
        # (start_s, duration_s, peak_strength)
        gusts = [(2.5, 3.4, 0.65), (8.7, 4.2, 0.85),
                 (14.3, 2.6, 0.55), (18.2, 4.0, 0.75)]
        gust = _np.zeros(n, dtype=_np.float32)
        for gs, gd, gp in gusts:
            mask = (t >= gs) & (t < gs + gd)
            local = (t - gs) / gd
            env = _np.where(local < 0.20, local / 0.20,
                            _np.maximum(0.0,
                                         1.0 - (local - 0.20) / 0.80))
            gust = _np.maximum(gust, _np.where(mask, env * gp, 0.0))
        # Smoothed noise -- one-pole low-pass for each channel.
        smooth_coef = 0.92
        baseL = rng.uniform(-1.0, 1.0, n).astype(_np.float32)
        baseR = rng.uniform(-1.0, 1.0, n).astype(_np.float32)
        # y[n] = smooth_coef * y[n-1] + (1-smooth_coef) * x[n]
        # -> lfilter b=[1-c], a=[1, -c]
        from scipy import signal as _sig
        L_air = _sig.lfilter([1 - smooth_coef], [1, -smooth_coef],
                              baseL).astype(_np.float32)
        R_air = _sig.lfilter([1 - smooth_coef], [1, -smooth_coef],
                              baseR).astype(_np.float32)
        # Rustle -- shorter smoothing for brighter content.
        rust_coef = 0.45
        L_rust = _sig.lfilter([1 - rust_coef], [1, -rust_coef],
                               rng.uniform(-1.0, 1.0, n)).astype(_np.float32)
        R_rust = _sig.lfilter([1 - rust_coef], [1, -rust_coef],
                               rng.uniform(-1.0, 1.0, n)).astype(_np.float32)
        # Undertone (mono, shared L/R for centering).
        sub_env = 0.5 + 0.5 * _np.sin(2 * _np.pi * 0.07 * t)
        under = (_np.sin(2 * _np.pi * 55 * t) * 0.20
                 + _np.sin(2 * _np.pi * 220 * t) * 0.08) * sub_env
        L = L_air * 0.75 + L_rust * 0.20 * gust + under * 0.6
        R = R_air * 0.75 + R_rust * 0.20 * gust + under * 0.6
        env = (0.75 + 0.25 * _np.sin(2 * _np.pi * 0.04 * t)
               + 0.30 * gust)
        L = _np.clip(L * env * vol, -1.0, 1.0)
        R = _np.clip(R * env * vol, -1.0, 1.0)
        stereo = _np.column_stack([L, R])
        return pygame.sndarray.make_sound((stereo * 32767)
                                          .astype(_np.int16))

    def _silent_stereo(self, duration_ms):
        """Silent stereo Sound of the given duration. Used by the
        wind/whisper fallback paths when numpy isn't available."""
        n = int(22050 * duration_ms / 1000)
        return pygame.mixer.Sound(buffer=bytes(n * 4))

    def _music_loop(self, notes, beat_ms=400, vol=0.1, wave="sine",
                    mid_partial=0):
        """Build a procedural music loop from a (freq, beats) note list.
        `mid_partial` (0 = off, N > 0 = harmonic index) adds the Nth
        harmonic of each pitched note at -12 dB so sub-only drones
        (e.g. void at 48-60 Hz) carry an audible upper-bass band on
        laptop speakers. Norm divides amplitude to keep peak in check
        when the partial is added."""
        sr = 22050
        total_samples = 0
        segments = []
        norm = 1.0 / 1.25 if mid_partial else 1.0
        for f, beats in notes:
            ms = int(beat_ms * beats)
            n = int(sr * ms / 1000)
            seg = bytearray(n * 2)
            attack_n = max(1, int(sr * 0.02))
            decay_n = max(1, int(sr * 0.10))
            mf = f * mid_partial if (mid_partial and f > 0) else 0.0
            for i in range(n):
                t = i / sr
                if f <= 0:
                    v = 0.0
                elif wave == "sine":
                    v = math.sin(2 * math.pi * f * t)
                elif wave == "triangle":
                    v = 2.0 * abs(2.0 * (f * t - math.floor(f * t + 0.5))) - 1.0
                elif wave == "square":
                    v = 1.0 if math.sin(2 * math.pi * f * t) > 0 else -1.0
                elif wave == "saw":
                    v = 2.0 * (f * t - math.floor(0.5 + f * t))
                else:
                    v = math.sin(2 * math.pi * f * t)
                if mf > 0.0:
                    v += math.sin(2 * math.pi * mf * t) * 0.25
                if i < attack_n:
                    env = i / attack_n
                elif i > n - decay_n:
                    env = max(0.0, (n - i) / decay_n)
                else:
                    env = 0.85
                sample = int(v * vol * env * norm * 32767)
                sample = max(-32768, min(32767, sample))
                seg[i*2] = sample & 0xFF
                seg[i*2+1] = (sample >> 8) & 0xFF
            segments.append(seg)
            total_samples += n
        flat = bytearray()
        for s in segments:
            flat.extend(s)
        stereo = bytearray(total_samples * 4)
        for i in range(total_samples):
            stereo[i*4]   = flat[i*2]
            stereo[i*4+1] = flat[i*2+1]
            stereo[i*4+2] = flat[i*2]
            stereo[i*4+3] = flat[i*2+1]
        return pygame.mixer.Sound(buffer=bytes(stereo))

    def _sfx_gain(self):
        return self.master_vol * self.sfx_vol

    def _music_gain(self):
        return self.master_vol * self.music_vol

    def set_volumes(self, master=None, music=None, sfx=None):
        """Update mix gains live (pause-menu sliders). Re-applies the music
        channel volume immediately so a change is heard at once; in-flight
        SFX finish at their old gain, new ones pick up the change."""
        if master is not None:
            self.master_vol = max(0.0, min(1.0, master))
        if music is not None:
            self.music_vol = max(0.0, min(1.0, music))
        if sfx is not None:
            self.sfx_vol = max(0.0, min(1.0, sfx))
        if self.enabled and self.music_channel is not None:
            depth = getattr(self, "_duck_depth", 1.0) if getattr(
                self, "_duck_until", 0.0) else 1.0
            self.music_channel.set_volume(self._music_gain() * depth)

    def play(self, name, volume=1.0, pan=None):
        """Play a built SFX. When `pan` is provided (-1.0 = full left,
        0.0 = centred, +1.0 = full right), allocate a free channel and
        bias its L/R volume so the cue feels like it came from one
        side. Without `pan`, behaves as the original mono play.

        We keep a soft 15% floor on the opposite ear so a fully-panned
        cue still has a faint trace there -- prevents headphone-only
        listeners from missing a hard-panned phantom_step entirely."""
        if not self.enabled or name not in self.sfx:
            return
        volume *= self._sfx_gain()
        s = self.sfx[name]
        if pan is None:
            s.set_volume(volume)
            s.play()
            return
        pan = max(-1.0, min(1.0, pan))
        # Linear pan with a 15% floor on the off side.
        left = volume * max(0.15, 1.0 - max(0.0, pan))
        right = volume * max(0.15, 1.0 + min(0.0, pan))
        ch = pygame.mixer.find_channel()
        if ch is None:
            s.set_volume(volume)
            s.play()
            return
        # Sound-level volume to 1.0 so the channel L/R is the only
        # gain stage. Otherwise prior set_volume calls leak in.
        s.set_volume(1.0)
        ch.set_volume(left, right)
        ch.play(s)

    def set_scene_reverb(self, profile):
        """Set the active reverb profile for play_in_scene ('cellar' /
        'outdoor' / None). Game.load_scene_now calls this from the
        scene-tag dispatch."""
        self._scene_reverb = profile

    def play_in_scene(self, name, volume=1.0, pan=None):
        """Play a cue routed through the current scene's reverb
        (variants pre-baked per profile at startup -- footsteps and
        the gunshot). Falls back to the dry cue when no profile is
        active or no variant exists."""
        if self._scene_reverb:
            variant = f"{name}_{self._scene_reverb}"
            if variant in self.sfx:
                self.play(variant, volume=volume, pan=pan)
                return
        self.play(name, volume=volume, pan=pan)

    def king_tone(self, on, volume=0.5):
        """Loop the King's signature tone on its own channel while his sprite is
        on screen, and fade it out the instant he's gone. `volume` should swell
        as he closes -- the air being pulled from the room, getting nearer."""
        if not self.enabled or self.king_channel is None:
            return
        if on:
            if not self._king_on or not self.king_channel.get_busy():
                self.king_channel.play(self.sfx["yk_tone"], loops=-1)
                self._king_on = True
            self.king_channel.set_volume(
                max(0.0, min(1.0, volume)) * self._sfx_gain())
        elif self._king_on:
            self.king_channel.fadeout(450)
            self._king_on = False

    def pan_for_world(self, world_x, player_x, half_width=320.0):
        """Compute a pan value (-1..+1) from a sound source's world X
        relative to the player. `half_width` is the world-x distance at
        which a sound is fully panned to one side. Returns 0.0 when the
        source is at the player's column. Vertical offset is ignored --
        ear separation is left/right only."""
        return max(-1.0, min(1.0, (world_x - player_x) / half_width))

    def distance_attenuation(self, sx, sy, px, py, falloff=240.0):
        """Distance-based volume multiplier (0..1) for a positioned
        cue. Curve is 1 / (1 + (d/falloff)^2), so:
            d=0      -> 1.0
            d=120    -> 0.80
            d=240    -> 0.50  (the `falloff` half-volume point)
            d=480    -> 0.20
            d=720    -> 0.10
        Apply alongside pan_for_world so far-away sources both pan AND
        quiet, instead of just panning at full volume."""
        d = math.hypot(sx - px, sy - py)
        return 1.0 / (1.0 + (d / max(1.0, falloff)) ** 2)

    def play_music(self, track_name, fade_in_ms=400):
        if not self.enabled:
            return
        if self.music_muted:
            return
        if self.current_music == track_name:
            return
        self.current_music = track_name
        if track_name is None or track_name not in self.music:
            self.music_channel.fadeout(300)
            return
        self.music_channel.fadeout(150)
        self.music_channel.play(self.music[track_name], loops=-1, fade_ms=fade_in_ms)
        self.music_channel.set_volume(self._music_gain())

    def stop_music(self, fade_ms=200):
        self.current_music = None
        if self.enabled and self.music_channel:
            self.music_channel.fadeout(fade_ms)

    # ---- Opening drive: engine + car radio dissolving into static ----
    def start_drive(self):
        """Begin the opening-drive bed: engine idle + radio + static loops,
        all starting silent so the caller can ramp them per frame."""
        if not self.enabled:
            return
        self.stop_music(150)
        self.drive_channel.play(self.engine_snd, loops=-1)
        self.radio_channel.play(self.radio_snd, loops=-1)
        self.static_channel.play(self.sfx["static"], loops=-1)
        for ch in (self.drive_channel, self.radio_channel, self.static_channel):
            ch.set_volume(0.0)

    def set_drive(self, engine=0.0, radio=0.0, static=0.0):
        """Set the three drive-bed volumes (0..1) for this frame."""
        if not self.enabled:
            return
        g = self.master_vol
        self.drive_channel.set_volume(max(0.0, min(1.0, engine)) * g)
        self.radio_channel.set_volume(max(0.0, min(1.0, radio)) * g)
        self.static_channel.set_volume(max(0.0, min(1.0, static)) * g)

    def stop_drive(self):
        """Fade the whole drive bed out (engine dead, signal gone)."""
        if not self.enabled:
            return
        for ch in (self.drive_channel, self.radio_channel, self.static_channel):
            ch.fadeout(250)

    def force_silence(self, duration_s=None):
        self.music_muted = True
        self.stop_music(50)
        self.king_tone(False)
        if duration_s:
            self._silence_until = time.time() + duration_s
        else:
            self._silence_until = None

    def update_silence(self):
        if self.music_muted and getattr(self, "_silence_until", None):
            if time.time() >= self._silence_until:
                self.music_muted = False
                self._silence_until = None

    def duck(self, duration_s, depth=0.15):
        """Drop music_channel to `depth` x volume for `duration_s` so a
        horror cue can land in the gap. Auto-restored by update_duck.
        Stacking calls extend the window and pick the deeper depth."""
        if not self.enabled or self.music_channel is None:
            return
        until = time.time() + duration_s
        prev_until = getattr(self, "_duck_until", 0.0)
        prev_depth = getattr(self, "_duck_depth", 1.0)
        self._duck_until = max(prev_until, until)
        self._duck_depth = min(prev_depth, depth) if prev_until else depth
        self.music_channel.set_volume(self._music_gain() * self._duck_depth)

    def update_duck(self):
        if not self.enabled or self.music_channel is None:
            return
        until = getattr(self, "_duck_until", 0.0)
        if until and time.time() >= until:
            self._duck_until = 0.0
            self._duck_depth = 1.0
            self.music_channel.set_volume(self._music_gain())
