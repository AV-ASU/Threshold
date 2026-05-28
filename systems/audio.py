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
        self.current_music = None
        self.music_muted = False
        self.music_channel = None
        self.ambient_channel = None
        self.king_channel = None
        self._king_on = False
        if self.enabled:
            self._build_library()
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
        self.sfx["bump"]        = g(80, 100, 0.18, "square", attack_ms=2, decay_ms=70, noise_mix=0.3)
        self.sfx["door_open"]   = g(180, 250, 0.25, "saw", attack_ms=20, decay_ms=200, noise_mix=0.2)
        self.sfx["door_close"]  = g(120, 220, 0.25, "saw", attack_ms=10, decay_ms=180, noise_mix=0.25)
        self.sfx["engine_die"]  = g(64, 900, 0.34, "saw", attack_ms=4, decay_ms=820, noise_mix=0.45, vibrato=11)
        self.sfx["carcosa_boom"] = g(50, 1100, 0.55, "sine", attack_ms=2, decay_ms=950, noise_mix=0.45)
        self.sfx["door_locked"] = g(220, 80, 0.22, "square", attack_ms=2, decay_ms=50)
        self.sfx["transition"]  = g(280, 350, 0.18, "sine", attack_ms=40, decay_ms=300)
        self.sfx["menu_open"]   = g(440, 90, 0.20, "triangle", attack_ms=2, decay_ms=70)
        self.sfx["menu_close"]  = g(330, 90, 0.20, "triangle", attack_ms=2, decay_ms=70)
        self.sfx["cursor"]      = g(660, 35, 0.18, "square", attack_ms=2, decay_ms=20)
        self.sfx["confirm"]     = g(880, 80, 0.22, "triangle", attack_ms=2, decay_ms=60)
        self.sfx["cancel"]      = g(220, 80, 0.20, "triangle", attack_ms=2, decay_ms=60)
        self.sfx["save"]        = g(523, 200, 0.22, "sine", attack_ms=10, decay_ms=180)
        self.sfx["save_chime2"] = g(659, 220, 0.22, "sine", attack_ms=10, decay_ms=200)
        self.sfx["blip_low"]    = g(200, 35, 0.16, "square", attack_ms=2, decay_ms=20)
        self.sfx["blip_mid"]    = g(330, 35, 0.16, "square", attack_ms=2, decay_ms=20)
        self.sfx["blip_high"]   = g(550, 30, 0.14, "square", attack_ms=2, decay_ms=18)
        self.sfx["blip_soft"]   = g(420, 40, 0.10, "sine", attack_ms=4, decay_ms=30)
        self.sfx["blip_kid"]    = g(720, 28, 0.16, "triangle", attack_ms=2, decay_ms=18)
        self.sfx["blip_glitch"] = g(180, 50, 0.22, "noise", attack_ms=2, decay_ms=30, noise_mix=1.0)
        self.sfx["blip_gruff"]  = g(160, 40, 0.18, "saw", attack_ms=2, decay_ms=25, noise_mix=0.2)
        self.sfx["pickup"]      = g(660, 110, 0.20, "sine", attack_ms=2, decay_ms=90)
        self.sfx["pickup_rare"] = g(880, 280, 0.24, "sine", attack_ms=20, decay_ms=240, vibrato=8)
        self.sfx["chest"]       = g(440, 350, 0.22, "triangle", attack_ms=20, decay_ms=300)
        self.sfx["swing"]       = g(280, 100, 0.18, "saw", attack_ms=2, decay_ms=60, noise_mix=0.3)
        self.sfx["hit"]         = g(180, 70, 0.20, "noise", attack_ms=2, decay_ms=50, noise_mix=1.0)
        self.sfx["enemy_die"]   = g(110, 380, 0.22, "saw", attack_ms=10, decay_ms=320, noise_mix=0.4)
        self.sfx["player_hurt"] = g(160, 200, 0.24, "saw", attack_ms=2, decay_ms=160, noise_mix=0.3)
        self.sfx["heartbeat"]   = g(55, 220, 0.30, "sine", attack_ms=20, decay_ms=180)
        self.sfx["static"]      = g(0, 600, 0.25, "noise", attack_ms=20, decay_ms=400, noise_mix=1.0)
        self.sfx["wrong"]       = g(33, 900, 0.32, "saw", attack_ms=80, decay_ms=700)
        self.sfx["whisper"]     = g(290, 700, 0.16, "noise", attack_ms=80, decay_ms=500, noise_mix=0.85)
        self.sfx["arg_chime"]   = g(311, 480, 0.22, "sine", attack_ms=20, decay_ms=400, vibrato=2)
        # Trespass alarm: a long ringing brass-bell tone. Used by
        # eye-cameras flagged alarm=True (church, sheriff's office).
        self.sfx["alarm_bell"]  = g(420, 1200, 0.30, "sine", attack_ms=8, decay_ms=1100, vibrato=3)
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
        self.sfx["heal"]        = g(660, 260, 0.20, "sine", attack_ms=20, decay_ms=220, vibrato=4)
        # First-void-entry sting. Single short low-sine pulse with a
        # noise edge -- played once per session the first time the
        # player crosses into a substrate scene, since the transition
        # itself is now a single-frame swap.
        self.sfx["void_sting"]  = g(60, 140, 0.30, "sine", attack_ms=4, decay_ms=120, noise_mix=0.3)
        # Pistol gunshot. Sharp square+noise burst; used for the
        # player's pistol attack and (eventually) the policeman's
        # ranged volleys.
        self.sfx["pistol_shot"] = g(220, 90, 0.32, "square", attack_ms=2, decay_ms=70, noise_mix=0.7)
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
        # `door_distant`: a faint door-close from a room you can't
        # see. Half the volume of the regular door_close, lower pitch,
        # longer tail.
        self.sfx["door_distant"] = g(80, 360, 0.14, "saw",
                                      attack_ms=20, decay_ms=320,
                                      noise_mix=0.4)
        # `low_pulse`: a single sub-bass pulse used for the rare moment
        # the Pursuer manifests strongly (e.g. when the player stands
        # still too long, or when a Watcher just despawned).
        self.sfx["low_pulse"]    = g(36, 480, 0.30, "sine",
                                      attack_ms=40, decay_ms=400)
        # `threshold_chime`: replaces the cheerful save_chime2 on the
        # 5th and 9th save -- a slightly out-of-tune dyad that says
        # "saved" but feels wrong. Same trigger points, different
        # affect.
        self.sfx["threshold_chime"] = g(207, 380, 0.20, "sine",
                                         attack_ms=20, decay_ms=350,
                                         vibrato=1)

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
        }
        for key, kw in _atmos.items():
            if key in self.sfx:
                self.sfx[key] = self._post(self.sfx[key], **kw)

        # MUSIC. THRESHOLD's tracks are intentionally not melodies --
        # most are drones, two are haunted-with-pings versions of the
        # original lullaby/lilting tunes. Older cheerful definitions
        # of `home` and `village` were dictionary collisions (they
        # were overwritten further down) so they are removed.
        self.music = {
            # encounter: pulsing bass + 2 stabs + rests. Used by
            # combat-bearing scenes; THRESHOLD doesn't need it for
            # the player but the legacy bandit cave still references
            # it via the scene registry.
            "encounter": self._music_loop([
                (220,0.5),(294,0.5),(330,0.5),(294,0.5),
                (220,0.5),(196,0.5),(220,1.0),(196,1.0),
                (165,1.0),(0,0.5),(220,0.5),(0,0.5),
            ], beat_ms=240, vol=0.12, wave="square"),
            # cave: low slow drone for the bandit cave family.
            "cave": self._music_loop([
                (165,2.0),(0,1.5),(196,1.0),(165,2.0),
                (0,2.5),(220,1.0),(196,1.5),(0,3.0),
            ], beat_ms=520, vol=0.08, wave="triangle"),
            # void: drone + rests = more uneasy
            "void": self._music_loop([
                (55,4.0),(58,4.0),(52,4.0),
                (0,2.0),(48,4.0),(0,2.0),(60,4.0),
            ], beat_ms=900, vol=0.14, wave="sine"),
            # wrong: extra notes
            "wrong": self._music_loop([
                (41,2.0),(0,1.0),(43,2.0),(0,1.0),
                (39,3.0),(0,2.0),(37,3.0),(0,1.0),(45,2.0),
            ], beat_ms=700, vol=0.18, wave="saw"),
            # basement: low pulse, very sparse, 1 melodic motif
            "basement": self._music_loop([
                (49,3.0),(0,2.0),(55,2.0),(0,3.0),
                (52,2.0),(0,4.0),
            ], beat_ms=700, vol=0.12, wave="triangle"),
            # easter: bouncy, contrast
            "easter": self._music_loop([
                (523,0.5),(659,0.5),(784,0.5),(880,0.5),
                (784,0.5),(659,0.5),(523,1.0),
                (587,0.5),(659,0.5),(587,1.0),(0,0.5),
            ], beat_ms=180, vol=0.11, wave="square"),
            # wind: 'music' for the brimley -- a long noise drone
            # with a subtle pitched undertone, no melody, no rhythm.
            # Stops entirely once the playscript is picked up; the silence
            # is the point.
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
            "outside": self._wind_loop(duration_ms=8000, vol=0.07),
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

    def _threshold_drone(self, duration_ms=12000, vol=0.10):
        """Two stacked low sines a tritone apart (41Hz + 58Hz), with
        a slow breathing envelope and a faint smoothed-noise layer.
        No melody, no rhythm, no resolution. The tritone sits as a
        permanent unresolved interval -- the ear keeps waiting for
        a third note that never comes. Used for the title screen
        and the late-game 'world is wrong' takeover."""
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
            smooth = 0.93 * smooth + 0.07 * random.uniform(-1, 1)
            v = tone * 0.85 + smooth * 0.20
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

    def _haunted_home(self, duration_ms=14000, vol=0.09):
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
            drone = math.sin(2 * math.pi * 49 * t) * 0.55
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

    def _haunted_village(self, duration_ms=13000, vol=0.08):
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
                     + math.sin(2 * math.pi * 73 * t) * 0.30)
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

    def _wind_loop(self, duration_ms=8000, vol=0.08):
        """Build a long noise-based ambient loop that reads as wind --
        filtered (smoothed) noise + a low pitched undertone, modulated
        by a slow envelope so the loudness breathes. No tonal hits;
        the goal is texture, not music."""
        sr = 22050
        n = int(sr * duration_ms / 1000)
        buf = bytearray(n * 2)
        smooth = 0.0
        for i in range(n):
            t = i / sr
            # Smoothed white noise (one-pole low-pass)
            smooth = 0.92 * smooth + 0.08 * random.uniform(-1, 1)
            # Slow undertone (low sine modulated by slower sine)
            under = math.sin(2 * math.pi * 55 * t) * 0.25 \
                  * (0.5 + 0.5 * math.sin(2 * math.pi * 0.07 * t))
            v = smooth * 0.85 + under
            # Breathing envelope -- gentle 0.5 .. 1.2 oscillation
            env = 0.85 + 0.35 * math.sin(2 * math.pi * 0.12 * t)
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

    def _music_loop(self, notes, beat_ms=400, vol=0.1, wave="sine"):
        sr = 22050
        total_samples = 0
        segments = []
        for f, beats in notes:
            ms = int(beat_ms * beats)
            n = int(sr * ms / 1000)
            seg = bytearray(n * 2)
            attack_n = max(1, int(sr * 0.02))
            decay_n = max(1, int(sr * 0.10))
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
                if i < attack_n:
                    env = i / attack_n
                elif i > n - decay_n:
                    env = max(0.0, (n - i) / decay_n)
                else:
                    env = 0.85
                sample = int(v * vol * env * 32767)
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
            self.king_channel.set_volume(max(0.0, min(1.0, volume)))
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
        self.drive_channel.set_volume(max(0.0, min(1.0, engine)))
        self.radio_channel.set_volume(max(0.0, min(1.0, radio)))
        self.static_channel.set_volume(max(0.0, min(1.0, static)))

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
        self.music_channel.set_volume(self._duck_depth)

    def update_duck(self):
        if not self.enabled or self.music_channel is None:
            return
        until = getattr(self, "_duck_until", 0.0)
        if until and time.time() >= until:
            self._duck_until = 0.0
            self._duck_depth = 1.0
            self.music_channel.set_volume(1.0)
