"""THRESHOLD narrative + cutscenes -- the scripted story beats, extracted
from systems/game.py.

The journal door-dream flashback, the case-file / interior-voice note system
(_log_case_entry, _log_note, _log_dream_entry, _descent_voice, the fold-talk
note), the ending sequences (car escape, the rite, SPREAD/SEAL), and the
opening title crawl. A NarrativeMixin on the Game class; these run on the live
instance and tick from step(). Cutscene tuning lives in ui.cutscenes; the
whole-screen DRAW of these beats stays in CutsceneMixin. No behavior change.
"""
import math
import random

from constants import SCREEN_H
from rendering.sprites import door_mask_surface
from rendering.spread_drive import (
    SPREAD_T_SHIFT, SPREAD_T_GAZE, SPREAD_T_FLOOD, SPREAD_T_ON,
    SPREAD_T_KNOW, SPREAD_CROSS_AT,
)
from ui.cutscenes import (
    FLASHBACK_DUR, FLASHBACK_MASK_FRAMES,
    FLASHBACK_SWARM_START, FLASHBACK_SWARM_PEAK,
    FLASHBACK_RATE_MIN, FLASHBACK_RATE_MAX, FLASHBACK_FOCAL_Y,
    OPENING_SCROLL_SPEED, OPENING_ROLL_DUR, OPENING_STALL_TIMEOUT,
    OPENING_DEAD_HOLD, OPENING_STALLS,
    RITE_YANK_DUR,
)
from systems.config import *        # noqa: F401,F403


class NarrativeMixin:
    def _start_flashback(self, mode):
        """Arm the door-dream renderer in one of its two modes.
        "flash": the journal's intrusive MEMORY (two flickers, ~0.5s, no
        swarm, no bed) -- the half-dismissed memory surfacing, not a
        scene. "rite": the FULL dream at the grove rite (the memory,
        finished): swarm, falling bed, the works."""
        from ui.cutscenes import FLASHBACK_DUR, FLASHBACK_FLASH_DUR
        self._flashback_mode = mode
        self._flashback_dur = (FLASHBACK_FLASH_DUR if mode == "flash"
                               else FLASHBACK_DUR)
        self._flashback_stills = [(None, self._flashback_dur)]
        self._flashback_phase = 0
        self._flashback_t = 0.0
        self._flashback_masks = []
        self._flashback_pool = None
        self._flashback_spawn_acc = 0.0
        self._flashback_stab_done = False
        if mode == "rite":
            self.audio.force_silence()
            self.audio.play("low_pulse", 0.85)
            self.audio.flashback_air(True)        # wind + falling bed
        else:
            self.audio.play("low_pulse", 0.6)     # the memory jolts

    def begin_rite_dream(self):
        """The grove rite: the PI consciously re-enters his ONE dream
        (a year old, never recurred) and finally answers the door. A
        pure cutscene (no input); completion tears the descent fold open
        and keys the way home to His face (_finish_rite, below)."""
        if self._flashback_phase is not None:
            return
        self.save.set_flag("flashback_seen", True)
        self._start_flashback("rite")

    def _finish_rite(self):
        """Rite-dream completion: the pane tears open, the circle seals.
        DIEGETIC only -- no banner, no 'accepted' notice. The PI's note
        registers it obliquely (a NOTE, never evidence)."""
        import pygame as _pg
        self.save.set_flag("rite_performed", True)
        self._rite_fold_t0 = _pg.time.get_ticks()    # the opening ramp
        self.audio.play("void_sting", 0.8)
        self.audio.play("low_pulse", 0.95)
        self._log_note("the_rite", [
            "I went back into the dream. On purpose, this time. The "
            "same door, the same light under it, a year old and not "
            "one day faded.",
            "I walked up to it the way I never did in my sleep. It "
            "knew me. It let me in.",
            "When I came out of it the fire was open and the corn "
            "had closed. I am not saying that to anyone the way I "
            "just said it here.",
        ])

    def _tick_flashback(self, dt):
        """Poll the flashback_pending save flag (set by inventory_ui
        when the player reads page 3 of Mom's notebook) -> the SHORT
        memory flash. (The grove rite starts the FULL dream directly
        via begin_rite_dream.) Once started, walk the stills phase by
        phase."""
        if (self._flashback_phase is None
                and self.save.flag("flashback_pending")):
            self.save.set_flag("flashback_pending", False)
            self.save.set_flag("flashback_seen", True)
            self._start_flashback("flash")
        if self._flashback_phase is None:
            return
        self._flashback_t += dt
        if self._flashback_mode != "flash":
            self._spawn_flashback_masks(dt)
        _, dur = self._flashback_stills[self._flashback_phase]
        if self._flashback_t >= dur:
            self._flashback_phase += 1
            self._flashback_t = 0.0
            if self._flashback_phase >= len(self._flashback_stills):
                mode = self._flashback_mode
                self._flashback_phase = None
                self._flashback_masks = []
                self._flashback_pool = None
                if mode == "rite":
                    # Done -- restore music, play a final chord.
                    self.audio.flashback_air(False)
                    self.audio.music_muted = False
                    self.audio.play("breath", 0.7)
                    if self.scene and self.scene.music:
                        self.audio.play_music(self.scene.music)
                    self._finish_rite()
                else:
                    # The flash: the memory surfaces, the note lands.
                    # Bump proximity hard -- the player KNOWS now.
                    self._provoke_cult(0.20)
                    self._log_dream_entry()

    def _build_flashback_pool(self):
        """Pre-render the mask pool (gaze-direction x seed) so the swarm
        climax blits dozens of faces per frame without re-rendering."""
        base = max(40, int(SCREEN_H * 0.22))
        pool = {}
        for gi, gz in enumerate(self._FB_GAZE):
            for sd in range(4):
                pool[(gi, sd)] = door_mask_surface(height=base, vis=0.66,
                                                   gaze=gz, seed=sd)
        self._flashback_pool = pool

    def _spawn_flashback_masks(self, dt):
        """Spawn dark-wood faces into the opening at an ACCELERATING rate --
        slow at first, a crowd by the climax. Each gets a random spot (may
        overrun the edges so the jamb clips it), a random size, and the gaze
        variant aimed back at the player (opening centre)."""
        if self._flashback_phase is None:
            return
        t = self._flashback_t
        if t < FLASHBACK_SWARM_START:
            return
        if self._flashback_pool is None:
            self._build_flashback_pool()
        p = min(1.0, (t - FLASHBACK_SWARM_START)
                / max(0.01, FLASHBACK_SWARM_PEAK - FLASHBACK_SWARM_START))
        rate = FLASHBACK_RATE_MIN + (FLASHBACK_RATE_MAX - FLASHBACK_RATE_MIN) * p ** 2.4
        if not self._flashback_stab_done:         # one stab as faces begin
            self.audio.play("wrong", 0.5)
            self._flashback_stab_done = True
        self._flashback_spawn_acc += rate * dt
        n = int(self._flashback_spawn_acc)
        self._flashback_spawn_acc -= n
        for _ in range(n):
            xf = random.uniform(-0.14, 1.14)      # edge overrun -> clipped
            yf = random.triangular(-0.08, 1.08, FLASHBACK_FOCAL_Y)
            scale = random.uniform(0.16, 0.30)
            if random.random() < 0.18:
                scale = random.uniform(0.34, 0.52)
            vx, vy = 0.5 - xf, FLASHBACK_FOCAL_Y - yf
            if abs(vx) < 0.10 and abs(vy) < 0.10:
                gi = 8
            else:
                gi = round(math.atan2(vy, vx) / (math.tau / 8)) % 8
            self._flashback_masks.append(
                [xf, yf, scale, gi, random.randint(0, 3), FLASHBACK_MASK_FRAMES])

    def _log_dream_entry(self):
        """Write the door-dream into the case notebook as a NOTE. CANON
        (NARRATIVE §2 / spectrum note): the PI dreamed of the door exactly
        ONCE, a year ago -- walked up, looked in, met His eye for a blip, and
        never reached it; it never took root. Reading Mara's journal through
        REMINDS him of that single dream (what the flashback renders), and he
        sets it down as a half-dismissed memory -- NOT a recurring dream.
        Stored in save arg 'notes', NOT 'evidence': the evidence log is
        canonical-clues-only and its length is _evidence_count (the King-gate
        + world rot driver), so a note must never land there. The notebook
        UI shows notes alongside clues. Idempotent via name-dedup."""
        if self.save is None:
            return
        notes = self.save.arg("notes", [])
        if not isinstance(notes, list):
            notes = []
        if any(isinstance(e, dict) and e.get("name") == "the_dream"
               for e in notes):
            return
        notes.append({"name": "the_dream", "lines": [
            "Her journal put me back inside the one odd dream. A year"
            " back, before any of this. I'd forgotten I had it.",
            "A door standing open in the dark. No wall around it, just"
            " the frame, old dry wood.",
            "Light behind it the colour of old gold, breathing in and out"
            " like something asleep.",
            "I walked up. I looked in. For a blip something looked back,"
            " met my eye, and then it broke.",
            "I never reached it. One dream, a year ago, and it never came"
            " again. So why do I know this place.",
        ]})
        self.save.set_arg("notes", notes)
        if hasattr(self, "_flash_notebook"):
            self._flash_notebook()

    def _current_lead(self):
        """The single soft "where the thread points" line the notebook
        shows (TODO #5). DERIVED from run state on every read, so there
        is no wiring to go stale and no scatter of setters: the deepest
        milestone that holds wins. Authored, oblique, PI-voiced. Never
        a checklist, never a waypoint, never evidence."""
        s = self.save
        if s is None:
            return None
        inv = getattr(self.player, "inventory", None)

        def has(k):
            return bool(inv is not None and inv.has(k))
        if s.flag("descent_sealed"):
            return ("Up was spent the moment you crossed. The car on the "
                    "arrival road answers what you carry.")
        if s.flag("depths_breached"):
            return "Old stone under the face. It is close now. Down."
        if has("pallid_mask"):
            return ("His face opens every door left in this town. Where "
                    "you carry it is the whole of the choice.")
        if s.flag("rite_performed"):
            return "The circle took you once already. Down."
        if s.flag("school_door_open"):
            return ("The clearing deep in the corn. Speak nothing there. "
                    "The dead fire knows the way down.")
        if has("rite_envelope"):
            return ("The Invitation names the school. Sleep where they "
                    "slept. Sweeten the air. Draw the last door.")
        if self._evidence_count() >= 3:
            return ("Enough of it holds together now. The Arcadia's desk "
                    "has been waiting for you to know that much.")
        if self._evidence_count() >= 1:
            return ("Pull the threads. The register at the Lodge, the "
                    "barn she slept in, the river the boy watched. The "
                    "town talks around what it knows.")
        return ("Ask the town about the Blaine girl. Start where anyone "
                "starts. The store, the law, the church.")

    def _log_note(self, name, lines):
        """Append a PI case-notebook NOTE (arg `notes`, never `evidence`).
        Idempotent by `name` so re-triggering a pickup never dupes. Used by
        the cult-testimony fragments (the cult's voice is the item desc; this
        is the PI's reaction). NOTES never inflate `_evidence_count`, so they
        never arm the King or the world rot -- only the five CANONICAL_EVIDENCE
        beats do."""
        notes = self.save.arg("notes", [])
        if not isinstance(notes, list):
            notes = []
        if any(isinstance(e, dict) and e.get("name") == name for e in notes):
            return
        notes.append({"name": name, "lines": list(lines)})
        self.save.set_arg("notes", notes)
        if hasattr(self, "_flash_notebook"):
            self._flash_notebook()

    def _log_case_entry(self):
        """Seed the case notebook with the PI's intake the moment a run
        begins. CANON (NARRATIVE §1/1b): the case is the LURE -- the King
        found the one appetite a numb investigator can't refuse, an
        unsolved thing, and walked the marked soul back to His door. This
        note must NEVER name that (truth arrives only as sensation): it
        reads as a hard man's grudging case summary, and the hook sits in
        the one line he can't account for -- why he took a grief job he'd
        normally wave off. Together with the_dream ('why do I know this
        place') and the_congregation ('there was never anyone to bring
        back'), it lets the lure surface ACROSS the notebook without a
        word of explanation. A NOTE, not evidence -- it must not arm the
        King-gate. Idempotent via name-dedup."""
        if self.save is None:
            return
        notes = self.save.arg("notes", [])
        if not isinstance(notes, list):
            notes = []
        if any(isinstance(e, dict) and e.get("name") == "the_case"
               for e in notes):
            return
        notes.insert(0, {"name": "the_case", "lines": [
            "Walter Blaine, Minneapolis. The client. Grief in the voice"
            " you could lean a ladder on.",
            "His girl, Mara, 26. Drove north in the fall. Stopped"
            " calling home by the new year.",
            "Last address: Brimley. Had to find it on a map. North woods,"
            " near nothing.",
            "Skip-trace. A weekend's work. Ask around, turn up the girl,"
            " drive back by dawn.",
            "I don't take grief jobs. Took this one. Couldn't tell you why"
            ". Only that the not-knowing itched, and I wanted it gone.",
        ]})
        self.save.set_arg("notes", notes)

    def _descent_voice(self, name, note_only=False):
        """Fire one interior-voice beat (see `_DESCENT_VOICE`): file the note
        to the case notebook and surface the brief on-screen flash. One-shot
        per beat (flag `voice_<name>`). The note goes in save arg 'notes',
        NEVER 'evidence' -- it must not move the King-gate.

        `note_only=True` files the note and flag but skips the on-screen
        beat, for callers that chain the display off a live text channel
        (`_descent_voice_beat`). A chained callback can be dropped without
        firing (narration.clear() on a scene load), so the note must never
        ride the chain."""
        if self.save is None:
            return
        spec = self._DESCENT_VOICE.get(name)
        if spec is None:
            return
        flag = f"voice_{name}"
        if self.save.flag(flag):
            return
        self.save.set_flag(flag, True)
        notes = self.save.arg("notes", [])
        if not isinstance(notes, list):
            notes = []
        if not any(isinstance(e, dict) and e.get("name") == name
                   for e in notes):
            notes.append({"name": name, "lines": list(spec["note"])})
            self.save.set_arg("notes", notes)
            if hasattr(self, "_flash_notebook"):
                self._flash_notebook()
        if not note_only:
            self.dialog.show(spec["beat"], speaker="", voice="blip_soft",
                             portrait="narrator")

    def _descent_voice_beat(self, name):
        """The on-screen half of `_descent_voice` alone, for beats whose
        note was already filed via `note_only=True`. At-most-once by
        construction: the chained on_complete it rides fires once or is
        dropped."""
        spec = self._DESCENT_VOICE.get(name)
        if spec is None:
            return
        self.dialog.show(spec["beat"], speaker="", voice="blip_soft",
                         portrait="narrator")

    def _fold_mentioned(self, name, reflect=True):
        """The FIRST time any local describes the fold -- the roads that loop,
        the town you can't drive out of -- the PI files a note and a short
        reflection. One-shot globally (flag `voice_fold_heard`); the note names
        whoever told him. A NOTE, never evidence. §1b-safe: it is the SPATIAL
        fold (perceptible -- looping roads), never the door/cosmology. Chains
        the reflection off the NPC's line so it lands after they finish.

        `reflect=False` files the note only: an organic conversation
        (ui/conversation) drives itself through the float's on_complete
        chain, so it must NOT be hijacked here -- the exchange carries the
        PI's reflection as its own closing beat instead."""
        if self.save is None or self.save.flag("voice_fold_heard"):
            return
        self.save.set_flag("voice_fold_heard", True)
        notes = self.save.arg("notes", [])
        if not isinstance(notes, list):
            notes = []
        if not any(isinstance(e, dict) and e.get("name") == "the_fold_told"
                   for e in notes):
            notes.append({"name": "the_fold_told", "lines": [
                f"{name} told me you can't drive out of Brimley. The roads "
                "loop. Make for the county line and the corn hands you back "
                "where you started.",
                "Said it flat. The way you'd say it always rains here. No fear "
                "left in it. A fact they've all stopped arguing with.",
                "A whole town doesn't go strange like that over a lie. [c=dim]"
                "And my own engine turned over and died at the lodge steps. "
                "So.[/c]",
            ]})
            self.save.set_arg("notes", notes)
            if hasattr(self, "_flash_notebook"):
                self._flash_notebook()

        if not reflect:
            return

        def _beat():
            self.dialog.show([
                f"[c=dim]{name} says there's no driving out of here. The "
                "roads loop, the corn hands you back. Said it like weather.[/c]",
                "[c=dim]A town doesn't talk like that about nothing. And my "
                "car died at the steps. ...So.[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
        if self.dialog.active:
            self.dialog.on_complete = _beat
        elif self.float_speech.active:
            # The local's line floats now -- land the reflection after
            # they finish, not on top of them.
            self.float_speech.on_complete = _beat
        else:
            _beat()

    def _begin_car_escape(self):
        """The car on the arrival road. The fold only opens for a shard of His
        authority, so escape requires the Pallid Mask (His face, lifted off
        the Sign Chamber altar), not just the keys -- with it the engine
        catches for the first time and you drive out as the breach:
        SPREAD IT (NARRATIVE §1/§6)."""
        if self._ending_active:
            return
        if not (self.player and self.player.inventory.has("pallid_mask")):
            return
        self._play_ending("escape_alone")

    def _play_ending(self, name):
        """Begin a multi-phase ending. Phase 0 sets up; phase 1+
        are text stills shown via _tick_ending. Each ending defines
        its own stills and final notice."""
        if self._ending_active:
            return
        self._ending_active = name
        self._ending_phase = 0
        self._ending_phase_t = 0.0
        self.audio.force_silence()
        # Lock input via the closure-locked flag (re-using the
        # mechanism so the player can't move during the sequence).
        self._closure_locked = True
        # Cue the appropriate audio.
        if name == "seal_threshold":
            # No sting here: the live warp already chimed and roared; the
            # black text opens in dead silence. _tick_seal_audio lands the
            # door-slam and the tableau's low approach.
            self._seal_cues = set()
        elif name == "rite_broken":
            # The dread drone for the mask-yank; the boom/roar come at the cut
            # (see _tick_rite_audio). Runs on the idle drive_channel.
            self._rite_cues = set()
            if self.audio.enabled:
                self.audio.drive_channel.play(self.audio.carcosa_drone_snd,
                                              loops=-1)
                self.audio.drive_channel.set_volume(0.0)
        elif name == "escape_alone":
            # The drive out rides the opening's engine/radio/static bed,
            # started silent; _tick_spread_audio shapes it beat by beat.
            self._spread_cues = set()
            self.audio.start_drive()
        else:
            self.audio.play("door_close", 0.7)

    def _tick_ending(self, dt):
        """Walk through the active ending's stills. Each phase is a
        single line shown for its specified duration via the same
        overlay system as the flashback."""
        if not self._ending_active:
            return
        self._ending_phase_t += dt
        if self._ending_active == "rite_broken" and self.audio.enabled:
            self._tick_rite_audio()
        elif self._ending_active == "escape_alone" and self.audio.enabled:
            self._tick_spread_audio()
        elif self._ending_active == "seal_threshold" and self.audio.enabled:
            self._tick_seal_audio()
        script = self._ENDING_SCRIPTS.get(self._ending_active, [])
        if not script:
            self._end_ending()
            return
        if self._ending_phase >= len(script):
            self._end_ending()
            return
        _, dur = script[self._ending_phase]
        if self._ending_phase_t >= dur:
            self._ending_phase += 1
            self._ending_phase_t = 0.0
            if self._ending_phase >= len(script):
                self._end_ending()

    def _tick_rite_audio(self):
        """rite_broken soundtrack, matched to the visual beats: a swelling
        dread drone over the mask-yank, a boom at the cut, the unleashed roar
        swelling then fading as His face engulfs, an apex swell near the end.
        Runs on the (otherwise idle) drive_channel."""
        yt = self._ending_phase_t
        dc = self.audio.drive_channel
        cues = getattr(self, "_rite_cues", None)
        if cues is None:
            cues = self._rite_cues = set()
        if yt < RITE_YANK_DUR:
            if yt < 2.7:
                dc.set_volume(min(0.7, yt / 2.0))             # drone swells
            else:
                dc.set_volume(max(0.0, 0.7 * (1 - (yt - 2.7) / 0.3)))  # ...dead silence
            if yt > 1.55 and "shatter" not in cues:       # the axe-blow lands
                cues.add("shatter")
                self.audio.play("hit", 0.7)
                self.audio.play("static", 0.4)
        else:
            bt = yt - RITE_YANK_DUR
            if "boom" not in cues:                            # the cut
                cues.add("boom")
                self.audio.play("carcosa_boom", 0.9)
                dc.play(self.audio.carcosa_roar_snd, loops=-1)
                dc.set_volume(0.0)
            dc.set_volume(min(0.75, bt / 1.5) if bt < 3.5
                          else max(0.0, 0.75 * (1 - (bt - 3.5) / 3.0)))
            if bt > 1.4 and "whisper1" not in cues:           # whispers of the taken
                cues.add("whisper1"); self.audio.play("whisper", 0.5)
            if bt > 3.0 and "whisper2" not in cues:
                cues.add("whisper2"); self.audio.play("whisper", 0.6)
            if bt > 3.3 and "swell" not in cues:
                cues.add("swell"); self.audio.play("yk_tone", 0.7)

    def _ending_elapsed(self):
        """Seconds since the active ending began (phases walked so far
        plus the time inside the current one) -- the clock the spread
        cutscene's picture and soundtrack both run on."""
        script = self._ENDING_SCRIPTS.get(self._ending_active, [])
        return (sum(d for _, d in script[:self._ending_phase])
                + self._ending_phase_t)

    def _tick_spread_audio(self):
        """escape_alone soundtrack, matched to the drive-out's beats: the
        key clicks dead, the engine catches and ROARS for the first time
        in the game, the radio hunts between stations on the way to the
        edge, the seat creaks as the mask turns, a heartbeat under the
        gaze -- and at the crossing the static simply DIES (the non-event
        is the cue). Then the feeling floods in (yk_tone, whispers), the
        engine returns steady for the drive south, and everything settles
        to a slow pulse under the verdict. Runs the opening drive's
        engine/radio/static bed, started silent in _play_ending."""
        t = self._ending_elapsed()
        cues = getattr(self, "_spread_cues", None)
        if cues is None:
            cues = self._spread_cues = set()

        def cue(name, at, snd, vol):
            if t >= at and name not in cues:
                cues.add(name)
                self.audio.play(snd, vol)

        cue("key", 0.9, "gun_dry", 0.3)              # the key turns
        cue("catch", 1.35, "bump", 0.55)             # ...and it CATCHES
        cue("creak", SPREAD_T_SHIFT + 1.3, "wood_creak", 0.55)  # the shift
        for i, at in enumerate((0.6, 1.4, 2.1, 2.7)):           # the gaze
            cue(f"hb{i}", SPREAD_T_GAZE + at, "heartbeat", 0.30 + 0.06 * i)
        cue("breath", SPREAD_T_FLOOD - 0.7, "breath", 0.7)
        cue("flood", SPREAD_T_FLOOD + 0.4, "yk_tone", 0.6)
        cue("wh1", SPREAD_T_FLOOD + 2.2, "whisper", 0.45)
        cue("wh2", SPREAD_T_FLOOD + 4.4, "whisper", 0.55)
        cue("know", SPREAD_T_KNOW + 0.3, "low_pulse", 0.9)
        cue("fog", SPREAD_T_ON + 2.8, "rot_throb", 0.40)   # it followed
        cue("fog2", SPREAD_T_KNOW + 1.8, "rot_throb", 0.5)
        cue("know2", SPREAD_T_KNOW + 3.2, "low_pulse", 0.6)

        # Engine envelope: dead -> the roar -> settled cruise -> falling
        # away under the gaze -> idle while he is overcome -> steady for
        # the drive on -> gone with the car.
        if t < 1.35:
            eng = 0.0
        elif t < 1.9:
            eng = 0.85 * (t - 1.35) / 0.55
        elif t < SPREAD_T_SHIFT:
            eng = 0.62 + 0.23 * max(0.0, 1.0 - (t - 1.9) / 0.8)
        elif t < SPREAD_T_GAZE:
            eng = 0.46
        elif t < SPREAD_CROSS_AT:
            eng = 0.46 - 0.32 * ((t - SPREAD_T_GAZE)
                                 / max(0.01, SPREAD_CROSS_AT - SPREAD_T_GAZE))
        elif t < SPREAD_T_FLOOD:
            eng = 0.12
        elif t < SPREAD_T_ON:
            eng = 0.26
        elif t < SPREAD_T_KNOW:
            eng = min(0.55, 0.26 + (t - SPREAD_T_ON) / 0.8 * 0.29)
        else:
            eng = max(0.0, 0.55 * (1.0 - (t - SPREAD_T_KNOW) / 2.2))

        # Radio: hunting between stations all the way to the fold, then
        # CUT DEAD at the crossing -- and coming back CLEAN south of it
        # (the first working signal of the game).
        rad = stat = 0.0
        if SPREAD_T_SHIFT - 6.0 < t < SPREAD_CROSS_AT and t > 2.4:
            hunt = math.sin(t * 0.9)
            duck = 0.5 if t > SPREAD_T_SHIFT else 1.0    # lower inside the cab
            rad = 0.10 * max(0.0, hunt) * duck
            stat = (0.05 + 0.09 * max(0.0, -hunt)) * duck
        elif SPREAD_T_ON < t:
            rad = 0.10 * max(0.0, min(1.0, (SPREAD_T_KNOW + 1.5 - t) / 1.5))
        self.audio.set_drive(eng, rad, stat)

    def _tick_seal_audio(self):
        """seal_threshold soundtrack. The black text plays in dead silence
        (the live warp's roar just cut out) except ONE hit: the door slam
        under its line. Then the wordless tableau gets a low approaching
        drone -- Rage approaches -- that dies before the cut to title, so
        the run ends in true silence. Cue times key off total elapsed
        across phases (durations: 3.4/3.6/3.2/3.0/3.4/8.0 -> the slam line
        starts at 10.2, the tableau at 16.6)."""
        script = self._ENDING_SCRIPTS["seal_threshold"]
        tt = (sum(d for _, d in script[:self._ending_phase])
              + self._ending_phase_t)
        dc = self.audio.drive_channel
        cues = getattr(self, "_seal_cues", None)
        if cues is None:
            cues = self._seal_cues = set()
        if tt > 10.35 and "slam" not in cues:         # the door slams shut
            cues.add("slam")
            self.audio.play("carcosa_boom", 0.85)
            self.audio.play("door_close", 0.6)
        if tt > 13.3 and "rage" not in cues:          # Rage approaches.
            cues.add("rage")
            self.audio.play("yk_tone", 0.4)
        if tt > 13.9 and "rage_w" not in cues:        # ...and is heard coming
            cues.add("rage_w")
            self.audio.play("whisper", 0.28)
        if tt > 16.6:                                 # the wordless tableau
            if "loom" not in cues:
                cues.add("loom")
                dc.play(self.audio.carcosa_drone_snd, loops=-1)
                dc.set_volume(0.0)
            bt = tt - 16.6
            dc.set_volume(min(0.42, bt / 7.0) if bt < 5.2
                          else max(0.0, 0.42 * (1 - (bt - 5.2) / 1.8)))
            if bt > 1.2 and "whisper" not in cues:
                cues.add("whisper")
                self.audio.play("whisper", 0.30)
            if bt > 3.8 and "whisper2" not in cues:
                cues.add("whisper2")
                self.audio.play("whisper", 0.38)
            if bt > 6.2 and "embers" not in cues:     # the eyes open
                cues.add("embers")
                self.audio.play("carcosa_boom", 0.5)
                self.audio.play("yk_tone", 0.35)

    def _end_ending(self):
        """Wrap up the ending sequence and return to title."""
        if self._ending_active == "escape_alone":
            self.audio.stop_drive()        # engine + radio + static bed
        if self.audio.enabled:
            self.audio.drive_channel.fadeout(300)
        self._ending_active = None
        self._ending_phase = 0
        self._ending_phase_t = 0.0
        self._closure_locked = False
        self.audio.music_muted = False
        self.state = "title"
        self.audio.play_music("threshold_drone")

    # ---- The opening drive ----
    def _begin_opening(self):
        """Start the cold-open drive into Brimley (state "opening"). A
        near-on-rails sequence; hands off to the normal start when it ends or
        the player silently skips it (ESC)."""
        self._opening_t = 0.0
        self._opening_scroll = 0.0
        self._opening_speed = 0.0
        self._opening_phase = "roll"          # roll | stall | dead
        self._opening_phase_t = 0.0
        self._opening_stalls_left = OPENING_STALLS
        self._opening_fig_cued = False        # the figure's one audio sting
        self.state = "opening"
        self.audio.start_drive()              # engine + radio + static bed

    def _tick_opening(self, dt):
        self._opening_t += dt
        self._opening_phase_t += dt
        ph = self._opening_phase
        # Speed eases toward full while rolling, toward 0 while stalled -- the
        # car coasts to a stop and lurches back up rather than snapping.
        target = OPENING_SCROLL_SPEED if ph == "roll" else 0.0
        self._opening_speed += (target - self._opening_speed) * min(1.0, dt * 4.0)
        self._opening_scroll += self._opening_speed * dt
        if ph == "roll":
            # The final approach: something stands far up the road (the
            # renderer draws it) -- one quiet tone under the engine, once.
            if (self._opening_stalls_left == 0
                    and not getattr(self, "_opening_fig_cued", False)):
                self._opening_fig_cued = True
                self.audio.play("yk_tone", 0.18)
            if self._opening_phase_t >= OPENING_ROLL_DUR:
                self._opening_phase = "stall"
                self._opening_phase_t = 0.0
                self.audio.play("bump", 0.4)
        elif ph == "stall":
            if self._opening_phase_t >= OPENING_STALL_TIMEOUT:
                self._opening_restart()        # don't softlock if they wait
        elif ph == "dead":
            if self._opening_phase_t >= OPENING_DEAD_HOLD:
                self._end_opening()
        # Drive audio: the engine tracks speed and dies in the dead phase;
        # the radio dissolves into static as you cross into Brimley, then the
        # signal is lost entirely -- the town cutting you off from the world.
        sp = max(0.0, min(1.0, self._opening_speed / OPENING_SCROLL_SPEED))
        ot = self._opening_t
        if self._opening_phase == "dead":
            eng = max(0.0, 0.5 * (1.0 - self._opening_phase_t / 0.8))
            rad = 0.0
            stat = max(0.0, 0.16 * (1.0 - self._opening_phase_t / 0.5))
        else:
            eng = 0.20 + 0.50 * sp
            deg = max(0.0, min(1.0, (ot - 2.5) / 3.0))    # radio -> static
            lost = max(0.0, min(1.0, (ot - 6.5) / 2.5))   # signal lost entirely
            rad = 0.16 * (1.0 - deg)
            stat = 0.22 * deg * (1.0 - lost)
        self.audio.set_drive(eng, rad, stat)

    def _opening_restart(self):
        """A stall resolves: the engine catches and lurches on -- or, on the
        fatal stall at the Lodge (no stalls left), it won't, and it's dead."""
        if self._opening_phase != "stall":
            return
        if self._opening_stalls_left > 0:
            self._opening_stalls_left -= 1
            self._opening_phase = "roll"
            self._opening_phase_t = 0.0
            self._opening_speed = OPENING_SCROLL_SPEED * 0.7   # the lurch
            self.audio.play("door_close", 0.4)
        else:
            self._opening_phase = "dead"
            self._opening_phase_t = 0.0
            self.audio.play("engine_die", 0.7)    # the engine that won't catch

    def _end_opening(self):
        """Hand the cold open off to the real start (reset, player, the
        bedroom wake). Called on completion or a silent ESC skip."""
        self.audio.stop_drive()                   # kill the engine/radio bed
        self._start_play()
