"""The top-level Game runtime: title screen, scene transitions, input,
combat, save/load, the main loop."""
import math
import random
import sys
import pygame

from constants import (
    SCREEN_W, SCREEN_H, TILE, RENDER_SCALE,
    C_BG, C_WHITE, C_BLACK, C_GOLD, C_BLOOD,
)
from rendering.sprites import (draw_player_sprite, draw_npc_sprite,
                               draw_npc_corpse,
                               draw_axe_swing, draw_axe_held,
                               draw_revolver_held, draw_gun_fire,
                               draw_king_death,
                               door_mask_surface, reset_king_fx,
                               view_from_facing, KING_UNFOLD,
                               KING_UNFOLD_SCALE)
from rendering.king_unfold import draw_unfold_catch, reset_king_unfold_fx
from rendering.spread_drive import SPREAD_BEAT_DURS
from rendering.transform import draw_vessel_bloom
from rendering.camera import Camera
from systems.look_control import LookController
from ui.fonts import make_fonts
from ui.dialog import DialogueBox
from ui.float_speech import FloatSpeech
from ui.narration import Narration
from ui.journal_ui import (
    JournalUI, CASE_TAB as JOURNAL_CASE_TAB, TOOLS_TAB as JOURNAL_TOOLS_TAB,
)
from ui.text_input import TextInputModal
from systems.audio import Audio
from systems.save import Save
from systems.items import ITEM_DEFS
from entities.player import Player
from entities.enemy import Projectile
from entities.npc import NPC
from entities.decoration import Decoration
from scenes import load_scene, tile_footstep, Scene
# Cutscene rendering (flashback / endings / opening drive) lives in its own
# module as a mixin. It OWNS the flashback/opening/rite tuning constants;
# re-export them here so `systems.game.FLASHBACK_DUR` etc. keep resolving
# (tests and any external reader rely on that name).
from ui.cutscenes import (
    CutsceneMixin,
    FLASHBACK_DUR, FLASHBACK_MASK_FRAMES,
    FLASHBACK_SWARM_START, FLASHBACK_SWARM_PEAK,
    FLASHBACK_RATE_MIN, FLASHBACK_RATE_MAX, FLASHBACK_FOCAL_Y,
    OPENING_SCROLL_SPEED, OPENING_ROLL_DUR, OPENING_STALL_TIMEOUT,
    OPENING_DEAD_HOLD, OPENING_STALLS,
    RITE_YANK_DUR,
)

# Gameplay tuning + scene-gating sets live in systems/config.py now (the
# config/logic split). Imported * so every bare-name reference below -- and
# every external `from systems.game import <CONST>` -- resolves unchanged.
from systems.config import *        # noqa: F401,F403
from systems.stealth import (grab_allowed as _grab_ok,
                             enter_search as _cult_enter_search,
                             is_enclosed as _is_enclosed_hide)
from systems.threat_mixin import ThreatMixin
from systems.king_roam_mixin import KingRoamMixin
from systems.rot_mixin import RotMixin, _corpse_examine
from systems.render_mixin import RenderMixin
from systems.narrative_mixin import NarrativeMixin
from systems.tableau_mixin import TableauMixin


class Game(CutsceneMixin, ThreatMixin, KingRoamMixin, RotMixin,
           RenderMixin, NarrativeMixin, TableauMixin):
    def __init__(self):
        pygame.init()
        self.fullscreen = True
        self.screen = None
        for flags in (pygame.FULLSCREEN | pygame.SCALED, pygame.SCALED, 0):
            try:
                self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
                self.fullscreen = bool(flags & pygame.FULLSCREEN)
                break
            except pygame.error:
                continue
        if self.screen is None:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
            self.fullscreen = False
        pygame.display.set_caption("THRESHOLD")
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        # Low-res world-render buffer (constants.RENDER_SCALE); lazily sized in
        # draw_world. None when render scale is 1.0 (the world draws straight to
        # the window).
        self._world_buf = None
        # Cached blind-spot fog layer (render_mixin._draw_sight_fog): rebuilt
        # only when the player/aim/camera actually move.
        self._sight_fog_cache = {}
        # Cached haze surfaces (render_mixin._draw_haze): the dim layer + one
        # patch per fog tint, reused across frames.
        self._haze_cache = {}
        self.fonts = make_fonts()
        # Audio() synthesises the entire SFX + music library at startup (the
        # game ships zero audio assets) -- several seconds of pure-Python DSP
        # during which nothing else runs. Paint a quiet loading frame FIRST so
        # the window isn't a dead/"Not Responding" black rect on every launch.
        self._draw_boot_screen()
        self.audio = Audio()
        self.save = Save(slot=1)
        self.dialog = DialogueBox(self.audio, self.fonts)
        self.dialog.game = self        # so show() can route casual NPC
        #                                lines to the floating layer
        # Floating, non-modal NPC speech (above the speaker's head; the
        # world keeps running). DialogueBox.show decides what floats.
        self.float_speech = FloatSpeech(self.audio, self.fonts)
        self._speaking_npc = None      # set during an interact so show()
        #                                knows whose head to float over
        # Non-modal narration: narrator/world-object text as a lower-third
        # caption; the world keeps running while the PI reads.
        self.narration = Narration(self.audio, self.fonts)
        # ONE book (I + N merged): the Casebook holds the case notes AND
        # the carried tools/papers behind a tab ribbon. `inv_ui` and
        # `notebook_ui` are kept as aliases onto it so the many existing
        # call sites (draw gating, tests) resolve to the single object.
        self.journal_ui = JournalUI(self.fonts, self.audio, self.save)
        self.journal_ui.game = self    # the derived theory reads live state
        self.inv_ui = self.journal_ui
        self.notebook_ui = self.journal_ui
        # Text-input modal -- used by the old man's computer terminal
        # (LOGIN: prompt) and reusable for any future ARG hooks. While
        # active, the Game suspends play and routes key events here.
        self.text_input = TextInputModal(self.fonts, self.audio)
        self.player = None
        self.scene = None
        self.state = "title"   # title, opening, playing, paused, transition
        self._opening_t = 0.0
        self._opening_scroll = 0.0
        self._opening_speed = 0.0
        self._opening_phase = "roll"
        self._opening_phase_t = 0.0
        self._opening_stalls_left = OPENING_STALLS
        # Title-screen ambient: the wind drone, no melody. The title
        # is meant to feel cold and unresolved -- if the player hesitates
        # on the menu, all they hear is the same wind that lives in the
        # brimley. Scene music takes over the moment they continue.
        self.audio.play_music("threshold_drone")
        self.transition_t = 0.0
        self.transition_target = None
        self.transition_dir = "out"
        self.cam_x = 0
        self.cam_y = 0
        # The single world->screen projection (DESIGN.md §10). At pitch 0 this is
        # exactly the legacy `int(x - cam_x)` top-down view; keeping every
        # render conversion behind it is what makes a future tilt a parameter
        # change rather than a 37-scene rewrite. `cam_x/cam_y` remain the
        # source of truth for the offset (camera update + input still use
        # them); the camera is re-synced to them each frame in draw_world.
        self.camera = Camera()
        # The oblique tilt is the ONLY camera (DESIGN.md §10). Pitch is locked
        # here for the life of the Game; there is no flat/pitch-0 view.
        self.camera.pitch = math.radians(TILT_PITCH_DEG)
        self.look = LookController()       # look/heading model (tilt mode)
        # Dev perf overlay (F1): FPS + frame-time readout, off by default. The
        # last frame's dt feeds the ms number; clock.get_fps() is pygame's own
        # rolling average. Purely diagnostic -- never shown unless toggled.
        self._show_fps = False
        self._last_dt = 0.0
        # Live-toggleable world render scale (F2 cycles it). Lower = the world
        # layer renders to a smaller buffer and upscales (HUD stays crisp),
        # trading sharpness for fps. Starts at the constant default.
        self._render_scale = RENDER_SCALE
        self.title_choice = 0
        # title_options is computed each render via _title_menu_options
        # so the middle slot can flip between "Delete Save" (when a
        # save exists) and "New Save" (when it doesn't). The two-step
        # delete-then-new flow prevents the player from accidentally
        # nuking a run by hitting "New Game" out of habit.
        self.pause_choice = 0
        # Save lives at the cot only -- the pause menu can't write
        # state. Quitting without sleeping = lose progress to the
        # last sleep. The bed is the save point. Resident-Evil-
        # typewriter rule, weighted by horror.
        self.pause_options = ["Resume", "Controls", "Settings", "Quit to Title"]
        # Pause sub-screens: "menu" (the options above), "controls" (a
        # read-only key reference), "settings" (the three mix sliders).
        self.pause_view = "menu"
        self.settings_choice = 0
        self.notice_text = None
        self.notice_t = 0
        self.frame_count = 0
        self.title_t = 0.0
        # Session-only flag: the void sting plays on the first entry
        # into a substrate scene per launch. Not persisted; subsequent
        # entries (this session) stay silent so the cut keeps reading
        # as instant rather than gated by a sound effect.
        self._void_sting_played = False
        # Stillness tracking. `stillness_t` accumulates seconds the
        # player has not moved; resets to 0 on any movement. Drives the
        # creepy-scene heartbeat ramp and the rare NPC blink. The
        # heartbeat schedule fires at tightening intervals while the
        # player is still inside a CREEPY_SCENES key.
        self.stillness_t = 0.0
        # Delayed-audio queue: list of [seconds_left, sfx_name, volume].
        # Used by the void/basement footstep "out of body" effect that
        # fires the step SFX a fraction of a second after the visual
        # step. Ticked in step().
        self._delayed_audio = []
        # Counter used to space the void/basement delayed-step trick;
        # every Nth eligible step plays late.
        self._creepy_step_count = 0
        # Cached vignette surface for the brimley / alter scenes.
        # Built once on first need; blitted at the player's screen
        # position each frame so it "closes around" them.
        self._vignette_surf = None
        # Soft outdoor vignette. Always-on radial darkness centred on
        # the player whenever they're in an OUTDOOR_SCENES key. Less
        # intense than the brimley vignette but never goes away --
        # the world edges are always pressing in. Cached on first need.
        self._outdoor_vignette_surf = None
        # Ashfall motes (DESIGN.md §2): live screen-space particle field,
        # eased toward a stage-driven target each frame. See _tick_ashfall.
        self._ashfall_parts = []

        # ---- THRESHOLD: the visibility meter ----
        # `visibility` is a float in [0, 1]: how visible the player is
        # to the King in Yellow right now. Watchers (spawned by a
        # cultist's curse) raise it; hiding bleeds it back down. While
        # the King hunts, holding it at 100% tears a portal he folds
        # through. See _tick_visibility + _tick_king_roam.
        self.visibility = 0.0
        self._vis_floor = 0.0        # evidence-driven minimum (DESIGN.md §1)
        self._being_seen = 0.0       # instantaneous cult/human gaze RATE (HUD)
        # Heartbeat schedule -- time to next thump. Kicks in only at
        # proximity >= 0.70 and only while the player is unhidden.
        # Period shortens with proximity so the pulse races at apex.
        # Independent of room ambients (that's environmental); this
        # one is biometric.
        self._heartbeat_t = 0.0
        # Per-frame budget for full-screen black overlays. Reset to 0
        # each draw frame; each overlay calls _claim_dark(requested)
        # which returns the alpha it's allowed to use and increments
        # this counter. Caps the total at MAX_FULLSCREEN_DARK so
        # hide+apex+dip stacking never blots out the player's feet.
        self._overlay_dark_used = 0
        # Last loud step + entry-tile bookkeeping is mirrored onto
        # `self.scene._last_step_event` and
        # `self.scene._last_entry_exit_tile` so cultist NPCs (which
        # only have access to `scene` in update()) can read them
        # without a back-reference to the Game. Set in the step
        # block + load_scene_now respectively.
        self._chant_t = 0.0          # depths cult-chant ambient timer
        self._breath_t = 0.0         # depths cult-breath ambient timer
        # ---- THRESHOLD: the King in Yellow ----
        # The King is the lethal apex (see _tick_king_roam). `_king`
        # holds his concrete NPC while he shares the player's scene
        # (None otherwise); `_king_anchor` is the doorway the player
        # entered from -- where a below-gate cult wave musters.
        self._king = None
        self._king_anchor = None
        self._reinforce_t = 0.0      # cultist reinforcement-wave cooldown
        self._gun_cd = 0.0           # seconds until the pistol can fire again
        # The roaming King (KING_PROMPT rework): one persistent, world-positioned
        # apex that idles down the road, then roams + hunts. Survives scene
        # loads; only _reset_run_state wipes it. _king_dread (0..1) is the
        # cross-scene tell the ashfall + audio read when he is near.
        self._roam_king = self._new_roam_king_state()
        self._king_dread = 0.0
        # The King's portal (the roaming-King rift): the active rift dict while one is
        # torn (None otherwise), and the pinned-100% charge timer toward it.
        self._portal = None
        self._portal_charge_t = 0.0
        # The idle state's receding horizon King (world x,y on THE road, or
        # None). Recomputed each tick by _tick_idle_king; drawn faint + far.
        self._idle_king = None

        # ---- THRESHOLD: cultists, the curse, and Watchers ----
        # Regular cultists roam the outdoor scenes (chaser AI: scout,
        # chase on sight, search, investigate). Their gaze raises
        # visibility while they hold line of sight; contact spikes it.
        # His gaze itself binds the curse: stay exposed in its sightline
        # long enough and a *permanent* curse lands. Each curse manifests
        # Watchers -- staring figures only the cursed sees -- and every
        # Watcher pushes visibility up,
        # marching the player toward a King they can no longer shake.
        self._cursed = False           # a Watcher wave is active until cleared
        self._watchers = []            # Watcher NPCs currently manifested
        self._watcher_clone_t = WATCHER_GRACE   # exposure timer to next spawn
        self._watcher_gaze = 0.0       # live Watchers holding the exposed player
        self._cult_touch_count = 0     # two-touch cult grab: resets in a safe zone
        self._gaze_count = 0           # cultists watching the player this frame
        self._cult_topup_t = 0.0       # rate-limits cultist (re)spawns per scene
        self._cult_prefilled = False   # per-load: filled roamers to scene target yet?
        self.flashlight_on = False     # player intent; only "lit" in DARK scenes

        # ---- THRESHOLD: flashback ----
        # Fires when the player reads Mara's journal through a third time.
        # Reading her words puts the PI back inside the ONE dream he had a
        # year ago, before Brimley (NARRATIVE §2 / §0: attuned exactly once,
        # it never took) -- the same door her journal describes. Not text -- a
        # wordless held shot: an open doorway of dried wood suspended in
        # black, a pulsing yellow glow radiating from it (cut off by the
        # frame), faint eyes peeking, and -- building from one face to a
        # swarm that all stare back -- a crowd of His dark-wood masks. The
        # "you can never arrive" of the whole game, at the scale of one dream.
        # _flashback_phase is None (inactive) or 0 (the one held phase).
        self._flashback_phase = None
        self._flashback_t = 0.0
        # Close-up examine tableau (None, or the active modal dict).
        self._tableau = None
        self._flashback_stills = [(None, FLASHBACK_DUR)]
        # Mask swarm: tick spawns dark-wood faces (accelerating) into
        # _flashback_masks; draw blits + ages them. _flashback_pool caches
        # pre-rendered masks (gaze x seed) so the climax is cheap.
        self._flashback_masks = []
        self._flashback_pool = None
        self._flashback_spawn_acc = 0.0
        self._flashback_stab_done = False

        # ---- THRESHOLD: ending state ----
        # _ending_active is the name of the ending currently
        # playing (or None). _ending_phase / _ending_phase_t walk
        # through the ending's stills.
        self._ending_active = None
        self._ending_phase = 0
        self._ending_phase_t = 0.0
        # SEAL live warp state (the threshold scene pours through the
        # doorframe before the ending proper; scenes/depths.py drives it).
        self._seal_warp = None

    def _title_menu_options(self):
        """THRESHOLD is a single-session game -- there is no save file
        to continue from. Continue appears once the cot has written the
        disk slot (systems/save.py; the typewriter rule)."""
        if self.save.disk_exists():
            return ["Continue", "New Game", "Quit"]
        return ["New Game", "Quit"]

    def title_input(self, ev):
        if ev.type != pygame.KEYDOWN: return
        if ev.key == pygame.K_F11:
            self._toggle_fullscreen(); return
        if ev.key == pygame.K_F1:
            self._show_fps = not self._show_fps; return
        if ev.key == pygame.K_F2:
            self._cycle_render_scale(); return
        opts = self._title_menu_options()
        if ev.key in (pygame.K_UP, pygame.K_w):
            self.title_choice = (self.title_choice - 1) % len(opts)
            self.audio.play("cursor", 0.7)
        elif ev.key in (pygame.K_DOWN, pygame.K_s):
            self.title_choice = (self.title_choice + 1) % len(opts)
            self.audio.play("cursor", 0.7)
        elif ev.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
            if self.title_choice >= len(opts):
                self.title_choice = len(opts) - 1
            opt = opts[self.title_choice]
            if opt == "New Game":
                self.save.new()
                self.audio.play("confirm", 0.8)
                self._begin_opening()
            elif opt == "Continue":
                # Wake at the cot, exactly as the last sleep left things.
                if self.save.load_disk():
                    self.audio.play("confirm", 0.8)
                    self._start_play()
                else:
                    self.audio.play("bump", 0.4)
            elif opt == "Quit":
                pygame.quit(); sys.exit(0)

    def _cycle_render_scale(self):
        """F2: cycle the world render scale (1.0 -> 0.85 -> 0.7 -> 1.0). Lower
        renders the world to a smaller buffer + upscales (HUD stays crisp) for
        more fps. Flashes a notice so the current setting is visible."""
        steps = [1.0, 0.85, 0.7]
        cur = getattr(self, "_render_scale", 1.0)
        i = min(range(len(steps)), key=lambda k: abs(steps[k] - cur))
        self._render_scale = steps[(i + 1) % len(steps)]
        pct = int(round(self._render_scale * 100))
        self.show_notice(f"Render scale: {pct}%", duration=1.5)

    def _toggle_fullscreen(self):
        try:
            pygame.display.toggle_fullscreen()
            self.fullscreen = not self.fullscreen
        except Exception:
            pass

    def _start_play(self):
        # The horror layer (Pursuer, watchers, kid follower, patrols,
        # heartbeat schedule, etc.) is intentionally NOT serialised --
        # each loaded session begins with a clean line. But the Game
        # instance is reused across Quit-to-Title -> Continue, so the
        # in-memory state from a previous run leaks into the next save
        # unless we explicitly clear it. Most visibly the kid follower
        # would re-spawn into the new save's scenes if `_kid_follower_
        # active` carried over.
        self._reset_run_state()
        self._log_case_entry()        # the PI starts with the case in hand
        self.player = Player(0, 0)
        self.player.from_save(self.save.data)
        # A continued save wakes with the town's attention where sleep
        # left it (cooled at the cot); a fresh save reads 0.
        self.visibility = float(self.save.arg("visibility_at_sleep", 0.0)
                                or 0.0)
        self.load_scene_now(self.save.data.get("scene", "bedroom"),
                             self.save.data.get("spawn", "default"))
        self.state = "playing"

    def _autosave(self):
        """Autosave on evidence pickup (play-notes: the clue IS the
        checkpoint, not a trip back to the cot). Snapshots hp + inventory +
        the current scene, plus a COOLED visibility so a reload never drops
        you straight into a maxed-out death. Evidence / notes / flags /
        dead_locals are already live in save.data; this persists them.
        Continue wakes at this scene's entry spawn."""
        if self.save is None or self.player is None or self.scene is None:
            return
        p = self.player
        self.save.data["player"] = p.to_save()
        self.save.data["inventory"] = p.inventory.to_save()
        self.save.data["scene"] = self.scene.key
        self.save.data["spawn"] = "default"
        self.save.set_arg("visibility_at_sleep",
                          round(self.visibility * 0.5, 3))
        self.save.write_disk()

    def _sleep_at_cot(self):
        """Rest in the spare-room cot. Saving moved to evidence pickup
        (_autosave, play-notes), so the cot is now purely the game's REST: hp
        restored and the town's attention cools while the PI is out of its
        sight (visibility halves; the evidence floor pulls it back up on its
        own). It no longer writes the disk slot."""
        p = self.player
        p.hp = p.max_hp
        self.visibility = round(self.visibility * 0.5, 3)
        self.audio.play("low_pulse", 0.5)
        self.audio.play("confirm", 0.5)
        self.dialog.show([
            "You lie down. The Arcadia keeps its hours around you, and for "
            "a while nothing asks anything of you.",
            "You wake rested. A little steadier.",
        ], speaker="", voice="blip_soft", portrait="narrator")

    def _reset_run_state(self):
        """Wipe all per-run state so a New Game starts clean. The
        Game instance is reused across Quit-to-Title -> New Game, so
        in-memory run state from a previous run is cleared here."""
        # Oblique view is the default; New Game starts tilted. Pitch 0 is
        # dev/capture-only now (the headless tools set it directly).
        self.camera.pitch = math.radians(TILT_PITCH_DEG)
        self.camera.yaw = 0.0
        self.look = LookController()
        # Visibility meter + the King in Yellow
        self.visibility = 0.0
        self._vis_floor = 0.0
        self._being_seen = 0.0
        # The hide-check struggle (DESIGN.md §12): a searcher checking
        # the enclosed hide the player is in opens a timed mash window.
        self._struggle = None
        # Aim-steady camera state: the post-shot chase lock and the
        # movement-input flag _update_look reads (see CHASE_FIRE_LOCK).
        self._chase_lock_t = 0.0
        self._move_input_active = False
        # The eased walk-lead the camera follows (see _update_camera).
        self._cam_lead = (0.0, 0.0)
        self._cam_lead_dir = None
        # The church bell: remaining peal time + the strike cadence
        # accumulator (see _ring_bell / _tick_bell, BELL_* config).
        self._bell_t = 0.0
        self._bell_toll_t = 0.0
        # The one-hop noise bleed: the live visit (scene-local, also
        # cleared on every load) + the between-visits cooldown.
        self._bleed = None
        self._bleed_cd = 0.0
        # Floating NPC speech + the interact speaker context.
        self.float_speech.active = False
        self.float_speech.speaker = None
        self.narration.clear()
        self._speaking_npc = None
        self._convo = None
        # TODO #13: count of SILENT-fold crossings this run; the "walked in
        # circles" case note fires on the second (the repeat is the tell).
        self._fold_loop_count = 0
        self._chant_t = 0.0
        self._breath_t = 0.0
        self._heartbeat_t = 0.0
        self._king = None
        self._king_anchor = None
        # The Moth FIELD: scene_key -> live moth count. Fed by the
        # King's timed shedding (_tick_moth_shed, his room, ev3+) and
        # the seeker drip (_tick_moth_seek, YOUR room, ev2+); thinned
        # only by the player spending one (a pop / a flare's burn-out).
        # Persistent for the run; wiped on New Game / Continue. ONE
        # moth pre-drifts the King's own road from the first minute:
        # the omen, and the safe lesson in the kindle rule.
        self._moth_field = {KING_ROAM_START: 1}
        self._moth_shed_t = 0.0
        self._moth_seek_t = None      # rolled per spawn by _tick_moth_seek
        reset_king_fx()        # clear his render trail/particles across runs
        reset_king_unfold_fx() # and the UNFOLDING's mask-bond state with them
        self._reinforce_t = 0.0
        self._gun_cd = 0.0
        self._roam_king = self._new_roam_king_state()
        self._king_dread = 0.0
        self._portal = None
        self._portal_charge_t = 0.0
        self._idle_king = None
        # Cultists, the curse, and Watchers
        self._cursed = False
        self._watchers = []
        self._watcher_clone_t = WATCHER_GRACE
        self._watcher_gaze = 0.0
        self._cult_touch_count = 0
        self._gaze_count = 0
        self._cult_topup_t = 0.0
        self._cult_prefilled = False
        self.flashlight_on = False
        self._void_sting_played = False
        self._ashfall_parts = []      # clear the ash field on New Game
        # The opening "door won't open the first time" beat is a
        # once-per-run latch. The Game instance is reused across
        # quit-to-title, so without this reset a second New Game in the
        # same session skips the scripted recoil. (Pairs with the save
        # flag `bedroom_door_passed`, which the fresh save clears.)
        self._bedroom_door_stuck_done = False
        # Fold pursuit (Stage 3) -- see _note_fold_pursuit / _tick_fold_pursuit.
        self._fold_pursuer = None
        self._fold_pursuer_grace = 0.0
        # Stillness + heartbeat
        self.stillness_t = 0.0
        self._delayed_audio = []
        self._creepy_step_count = 0
        # World rot stage-transition tracker (rot_mixin fires
        # rot_throb when the surface stage steps up). New game
        # starts at 0 so 0 -> 1 trips on the first evidence cross.
        self._last_infest_stage = 0
        # Flashback / ending state
        self._flashback_phase = None
        self._flashback_t = 0.0
        self._tableau = None
        self.audio.room_tone(None)   # a quit mid-close-up drops its bed
        self._flashback_masks = []
        self._flashback_pool = None
        self._flashback_spawn_acc = 0.0
        self._flashback_stab_done = False
        self._ending_active = None
        self._ending_phase = 0
        self._ending_phase_t = 0.0
        self._seal_warp = None
        self._closure_locked = False
        # Death screen: None | "cultist" | "king". A catch triggers it;
        # _tick_death holds it (cultist ~2.8s CAPTURED card, king ~3.5s
        # Carcosa furnace) then ENDS the run -- both return to title.
        self._death_kind = None
        self._death_t = 0.0
        self._notebook_toast_t = 0.0   # case-book scribble toast timer
        self._notebook_toast_name = None   # the beat the scribble names
        # Opening wake state. When the bedroom_on_enter fires for
        # the first session it sets these to non-zero values; the
        # _tick_wake_muffle ticker then dampens the music channel
        # and pulses the "heartbeat" SFX while the player's head is
        # still pounding. Decays to 0 over ~8 seconds.
        self._wake_muffle_t = 0.0
        self._wake_muffle_max = 8.0
        self._wake_heartbeat_t = 0.0
        # Misc per-run timers/sets that various tickers lazily (re)create.
        # Reset them explicitly so a New Game starts clean rather than
        # inheriting the previous run's value -- and so they don't rely on
        # scattered getattr(self, ..., default) guards at each use site.
        # (_folds is also rebuilt every load by _build_fold_cache; cleared
        # here too so the title/opening state carries nothing stale.)
        self._sheriff_intro_t = 0.0    # hunting-Sheriff intro hold (_tick_sheriff)
        self._sheriff_announced = False  # one-shot hollow-Sheriff intro notice/sting
        self._sprint_step_t = 0.0      # sprint footstep cadence (_tick_sprint)
        self._rite_cues = set()        # one-shot rite cue latches (ending)
        self._folds = []               # seen-fold peek cache (_build_fold_cache)
        # Mara calling-out staging (scenes/well.py _call_out/_sign_update).
        # Cleared per run so a death/quit mid-staging can't leave a stale
        # stage that makes _call_out early-return on the next run's first
        # works_sign entry (the trigger latches 'fired' before on_update
        # can clear it) and silently eat the calling-out.
        self._mara_stage = None

    # ---- Scene management ----
    def cross_fold(self, target_scene, spawn_id="default", dest_pos=None,
                   is_rift=False):
        """The ONE seamless fold-crossing primitive. Every non-door traversal
        funnels here: seamless world edges, direction-gated fold exits, the
        maze's same-scene relocations, and the King's rift juke. The crossing
        itself is deliberately NOTHING. No fade, no sting, no facing yank, no
        input hitch. The music keeps playing, the player keeps their stride
        and their screen position, and the world swaps around them. The FRAME
        is the spectacle (rendering.portal.draw_rift_door); stepping through
        is just walking. Doors / ladders / ropes stay on the fade path in
        begin_transition; they ARE doorways and should feel like them.

        `dest_pos` (world px) overrides the named spawn. The rift juke uses it
        (you emerge at the King's vacated spot); it is snapped to walkable
        ground because he phases, so the spot can sit inside a wall."""
        if self.scene is None or self.player is None:
            return
        screen_dx = self.player.x - self.cam_x
        screen_dy = self.player.y - self.cam_y
        same_scene = (target_scene == self.scene.key)
        # The wrong-space beats for the PI's notebook (TODO #13). Classify
        # this crossing: a SILENT fold (same-scene maze loop or a seamless
        # world edge -- no visible frame, the roads just loop) vs a VISIBLE
        # fold pane (he saw the gold-rimmed door and stepped through). The
        # rift juke (dest_pos, mid-chase) is no time to write, so skip it.
        if self.save is not None and dest_pos is None:
            src = self.scene.key
            if same_scene or (src in SEAMLESS_WORLD_SCENES
                              and target_scene in SEAMLESS_WORLD_SCENES):
                self._note_fold_loop(src)
            elif is_rift:
                self._note_fold_portal()
            # else: a SEE-THROUGH door (a mundane door with no fade, the far
            # room already in view) -- NOT a rift, so no "saw the door" note
            # (play-notes: it wrongly fired on the lodge interior doors).
        if same_scene:
            # A same-scene relocation (the maze 'I'/'Q' tiles): no load, no
            # per-load state clears. The world IS the same room; it just put
            # you somewhere else in it. Hide-state is re-derived below: a
            # relocation moves you, so the cover you stood in does not carry.
            dest = (dest_pos or self.scene.spawns.get(spawn_id)
                    or self.scene.spawns.get("default"))
            if dest is None:
                return
            self.player.x, self.player.y = dest
            self.player.hidden = None
            self.player.hide_origin = None
            if self.scene.char_floor_at(self.player.x, self.player.y) == ":":
                self.player.hidden = "corn"
        else:
            # Cross-scene: a real load (all the per-load clears apply) with
            # the stride preserved across it. load_scene_now orients the
            # player INTO the room, which is right for a door you just
            # opened but wrong for a fold you walked through, so the look
            # and facing are restored after the swap.
            facing = self.player.facing
            look = getattr(self, "look", None)
            look_state = ((look.body, look.aim, look.cam_yaw)
                          if look is not None else None)
            self.load_scene_now(target_scene, spawn_id, keep_music=True)
            if dest_pos is not None:
                safe = self._nearest_walkable(self.scene,
                                              dest_pos[0], dest_pos[1])
                if safe is not None:
                    self.player.x, self.player.y = safe
                self.scene._last_entry_exit_tile = (
                    int(self.player.x // TILE), int(self.player.y // TILE))
                if self.scene.char_floor_at(self.player.x,
                                            self.player.y) == ":":
                    self.player.hidden = "corn"
            self.player.facing = facing
            if look is not None and look_state is not None:
                look.body, look.aim, look.cam_yaw = look_state
        # The player never moves on screen: the camera carries the offset
        # through the swap. For non-wrap destinations the camera may drift on
        # the next frame due to clamping; that's fine -- the crossing moment
        # itself is continuous.
        self.cam_x = self.player.x - screen_dx
        self.cam_y = self.player.y - screen_dy

    def begin_transition(self, target_scene, spawn_id="default", seamless=False):
        if self.state == "transition": return
        current_key = self.scene.key if self.scene else None
        # A same-scene exit is a fold RELOCATION (the maze 'I'/'Q' tiles):
        # the world folds you elsewhere in the same room, seamlessly.
        if current_key is not None and target_scene == current_key:
            self.cross_fold(target_scene, spawn_id)
            return
        # Seamless outdoor-to-outdoor crossing. Both scenes are part of
        # the continuous outside world (SEAMLESS_WORLD_SCENES). No
        # fade, no level-load semantic. The destination's canonical
        # spawn already accounts for its road position; cross_fold then
        # shifts the camera so the player stays at the SAME SCREEN
        # POSITION before and after the swap. From their point of view
        # nothing jumped -- the tiles around them changed.
        if (current_key is not None
                and current_key in SEAMLESS_WORLD_SCENES
                and target_scene in SEAMLESS_WORLD_SCENES):
            self.cross_fold(target_scene, spawn_id)
            return
        # The cellar is no longer key-gated -- the Ledger (a case note, not counted evidence) is a
        # core clue and shouldn't hide behind a fetch-quest. The Clerk's old
        # crate/key/bottle chain has been cut entirely.
        # Crossing a threshold eases the meter a touch -- you've put a
        # wall between yourself and the room behind. With hiding, this
        # is how the player claws visibility back under 0.90 to shake
        # the King.
        self.visibility = max(0.0, self.visibility - 0.04)
        # Round-9: the forest secret-tree -> void_boss redirect was
        # removed. The forest j-tile now leads to the original empty
        # void (easter_egg + rust_key). The void_boss arena is reached
        # via a conditional fake stone wall in the old cave-boss
        # room -- gating logic lives there, not here.
        current = self.scene.key if self.scene else None
        # Opening: the FIRST attempt to leave the spare room is
        # silently rejected. No SFX, no notice -- the door just
        # doesn't open. The player has to turn back, do anything
        # else, and try again. While they were turned away the
        # candle dips once (handled in bedroom_on_update via the
        # `_door_stuck_recoil` flag below). Second attempt opens
        # normally and from then on this gate is permanently down.
        if (current == "bedroom" and target_scene == "lodge_hall"
                and not self.save.flag("bedroom_door_passed")):
            if not getattr(self, "_bedroom_door_stuck_done", False):
                self._bedroom_door_stuck_done = True
                # Bump the player one tile north off the door tile
                # so they aren't standing on it when control returns
                # -- otherwise the next frame would re-trigger the
                # exit check immediately. The bump is small and
                # silent; reads as "the door pushed back."
                self.player.y = 7 * TILE + 16
                # Trigger the room mutation in bedroom_on_update.
                if self.scene is not None:
                    self.scene._door_stuck_recoil = True
                return
            self.save.set_flag("bedroom_door_passed", True)
        # Opening: the moment the player crosses the threshold out of
        # the spare room, sprint unlocks and ambient watchers can
        # populate normally. Set once and never cleared.
        if (current == "bedroom" and target_scene != "bedroom"
                and not self.save.flag("left_bedroom")):
            self.save.set_flag("left_bedroom", True)
        if target_scene in VOID_SCENES or current in VOID_SCENES:
            if target_scene in VOID_SCENES and not self._void_sting_played:
                self.audio.play("void_sting", 0.55)
                self._void_sting_played = True
            self.load_scene_now(target_scene, spawn_id)
            return
        if seamless:
            # A SEE-THROUGH door: the room beyond was already visible through
            # the opening, so crossing the sill should be continuous, not a
            # fade to black. All the door gates above still applied (threshold
            # ease, the bedroom stuck-gate, flags); we just step through with
            # the seamless primitive -- the leaf swings, the door sounds, and
            # the world swaps around a preserved stride + screen position.
            self.audio.play("door_open", 0.7)
            self.cross_fold(target_scene, spawn_id)
            return
        self.transition_target = (target_scene, spawn_id)
        self.transition_dir = "out"
        self.transition_t = 0.0
        self.state = "transition"
        self.audio.play("door_open", 0.7)

    def _entry_facing(self, scene, x, y):
        """Heading to orient the player on entry: look INTO the open room. Prefer
        the heading toward the scene centre, but if that runs into a wall within
        ~2 tiles (a door tucked in a corner, the centre through a wall), fall back
        to the compass direction with the most clear space ahead -- so you never
        spawn staring at a wall with the room behind you."""
        def clear(h):                       # tiles clear ahead before a solid
            for step in range(1, 13):
                if scene.is_solid_at(x + math.cos(h) * step * TILE,
                                     y + math.sin(h) * step * TILE):
                    return step - 1
            return 12
        cx, cy = scene.w * TILE / 2.0, scene.h * TILE / 2.0
        center = math.atan2(cy - y, cx - x)
        if (cx - x or cy - y) and clear(center) >= 2:
            return center
        best_c, best_h = -1, center
        for k in range(8):
            h = k * math.pi / 4.0
            c = clear(h)
            if c > best_c:
                best_c, best_h = c, h
        return best_h

    def load_scene_now(self, key, spawn_id="default", *, keep_music=False):
        if self.scene and self.scene.on_exit_fn:
            self.scene.on_exit_fn(self, self.scene)
        self.scene = load_scene(key)
        # Stamp a stable per-build identity on the builder's NPCs for the
        # dead-locals ledger: scene builders create NPCs in deterministic
        # order, so the index matches across loads. NPCs added later
        # (on_enter staging, cult top-ups) carry none and are keyed by
        # name alone if they ever reach the ledger.
        for _bi, _bn in enumerate(self.scene.npcs):
            _bn._build_idx = _bi
        self.save.visit_scene(key)
        self.save.data["spawn"] = spawn_id
        spawn = self.scene.spawns.get(spawn_id, self.scene.spawns.get("default"))
        if spawn:
            self.player.x, self.player.y = spawn
        # Face the player INTO the open room on entry. You just walked in, so you
        # look forward at the room (and whoever's standing in it) instead of back
        # at the door -- otherwise anyone ahead of the spawn sits in the blind-
        # spot sight cone and reads as invisible until you turn around (the church
        # Preacher did). The camera rides behind this heading, so it orients the
        # sight cone too.
        if getattr(self, "look", None) is not None and self.player is not None:
            h = self._entry_facing(self.scene, self.player.x, self.player.y)
            self.look.body = h
            self.look.aim = h
            self.look.cam_yaw = h + math.pi / 2
            self.player.facing = (math.cos(h), math.sin(h))
        # The King materialises at the doorway the player entered from.
        # He stays behind on a scene change (cleared here) and re-forms
        # at the new entry if visibility is still pinned at the top.
        self._king = None
        reset_king_fx()        # his trail/particles don't follow across scenes
        reset_king_unfold_fx() # nor the UNFOLDING's mask-bond state
        self._king_anchor = (self.player.x, self.player.y)
        # A torn portal belongs to the room it opened in: leaving the scene
        # (through the rift or any other exit) collapses it. The roaming King's
        # own position (_roam_king) persists -- only the rift is per-scene.
        self._portal = None
        self._portal_charge_t = 0.0
        # Watchers are tied to YOU, not the room -- they re-manifest in
        # the new scene from the persistent curse. Clear the old set and
        # the per-scene cultist top-up timer so cultists re-populate.
        self._watchers = []
        # Reaching a SAFE_SCENE resets the two-touch cult grab (play-notes):
        # you can't be mid-grab inside a refuge, so a fresh encounter after
        # starts the touch count over.
        if key in SAFE_SCENES:
            self._cult_touch_count = 0
        self._gaze_count = 0
        self._cult_topup_t = 0.0
        # Fresh scene: re-fill roaming cultists to the scene's target on the
        # first awake tick (so a cult scene reads populated the moment you
        # enter), then rate-limit single respawns after (_ensure_cultists).
        self._cult_prefilled = False
        # Hide state never carries across scenes. Corn cover (`:`
        # tile) is per-tile; an explicit hide_spot's hide_origin
        # would point at OLD-scene coords if it leaked through.
        # Clear both unconditionally on every load. Re-enter cover
        # in the new scene via E (hide_spot) or by stepping onto
        # a corn tile.
        if self.player is not None:
            self.player.hidden = None
            self.player.hide_origin = None
            # If the spawn lands the player directly on a corn
            # tile, re-derive the corn-state immediately so the
            # cover read is correct without requiring a first
            # step. The movement-tick floor check would otherwise
            # leave a one-tick window of false visibility.
            if spawn:
                floor_ch = self.scene.char_floor_at(
                    self.player.x, self.player.y)
                if floor_ch == ":":
                    self.player.hidden = "corn"
        # Capture the entry tile (tile coords) on the Scene so NPC
        # update() code can read where the player walked in without a
        # back-reference to the Game.
        if spawn:
            self.scene._last_entry_exit_tile = (
                int(self.player.x // TILE),
                int(self.player.y // TILE),
            )
            # The door you came through swings shut behind you (tilt
            # view): pulse any door on or beside the entry tile.
            # quiet: the transition fade already plays the arrival's
            # door_close, so the swing itself stays silent.
            for ddx, ddy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                self._pulse_door_at(self.player.x + ddx * TILE,
                                    self.player.y + ddy * TILE,
                                    hold=0.35, quiet=True)
        else:
            self.scene._last_entry_exit_tile = None
        # Reset the noise channel on each scene load. A step in one
        # scene shouldn't bleed into the next (the one-hop bleed system
        # is the deliberate exception, and it re-emits on this side).
        self.scene._last_step_event = None
        self.scene._noise_events = []
        self.scene._noise_mask = None
        # A pending/live bleed visit belongs to the room it was armed
        # in; the transient itself was rebuilt away with the scene.
        self._bleed = None
        # A floating conversation's speaker was rebuilt away with the
        # scene -- drop the caption on load. Narration goes too: an
        # examine line (and any chained callback) belongs to the room
        # it fired in. An organic conversation (ui/conversation) dies
        # with its partner for the same reason, and so does a close-up
        # tableau (its prop/partner was rebuilt with the scene).
        self.float_speech.active = False
        self.float_speech.speaker = None
        self.narration.clear()
        self._convo = None
        self._tableau = None
        self.audio.room_tone(None)
        self._build_fold_cache()
        self._build_door_views()
        # Fold pursuit hand-off: if the player fled here through a fold with
        # a hot cultist (stashed by _note_fold_pursuit), arm the beat-behind
        # spawn at the entry seam. Consume-once; the refuge is never breached.
        if self._fold_pursuer is not None and key not in SAFE_SCENES:
            self._fold_pursuer["entry_tile"] = self.scene._last_entry_exit_tile
            self._fold_pursuer_grace = FOLD_PURSUE_DELAY
        else:
            self._fold_pursuer = None
            self._fold_pursuer_grace = 0.0
        self._update_camera(snap=True)
        # Seamless transitions in the outside world (handled in
        # begin_transition) ask for keep_music so the track doesn't
        # restart at the scene boundary. The reactive cult-ambient
        # timers (_chant_t, _breath_t, heartbeat) already live on the
        # Game instance, not on the scene, so they carry through
        # automatically.
        if not keep_music:
            if not self.audio.music_muted:
                self.audio.play_music(self.scene.music)
            else:
                self.audio.stop_music()
        # Scene-aware footstep reverb. UNDERGROUND_SCENES route through
        # the cellar profile (stone tail); OUTDOOR_SCENES + brimley use
        # outdoor (subtle slap-back); everything else stays dry.
        if key in UNDERGROUND_SCENES:
            self.audio.set_scene_reverb("cellar")
        elif key in OUTDOOR_SCENES or key == "brimley":
            self.audio.set_scene_reverb("outdoor")
        else:
            self.audio.set_scene_reverb(None)
        if self.scene.on_enter_fn:
            self.scene.on_enter_fn(self, self.scene)
        # Outdoor decay: re-apply tier-additive decorations every
        # load so a scene visibly worsens as the line tightens.
        # Pulls from OUTDOOR_DECAY by (scene_key, tier).
        from systems.threat import (proximity_tier,
                                     PROX_TIER_MID, PROX_TIER_HIGH)
        tier = proximity_tier(self.visibility)
        if tier in (PROX_TIER_MID, PROX_TIER_HIGH):
            extras = OUTDOOR_DECAY.get((self.scene.key, tier), [])
            for tx, ty, kind in extras:
                self.scene.add_decoration(
                    Decoration(tx * TILE + 16, ty * TILE + 16, kind)
                )
        # Persist axe chops across re-entries: any '*' debris or 'q'
        # boarded panel chopped in a previous session has its tile
        # opened.
        for ty in range(self.scene.h):
            for tx in range(self.scene.w):
                ch = self.scene.objects[ty][tx]
                if ch == "*":
                    if self.save.flag(
                            f"debris_broken_{self.scene.key}_{tx}_{ty}"):
                        self.scene.objects[ty][tx] = (
                            "4" if tx == 0 else "."
                        )
                elif ch == "q":
                    if self.save.flag(
                            f"boards_broken_{self.scene.key}_{tx}_{ty}"):
                        self.scene.objects[ty][tx] = "."
        # THE LEDGER OF THE DEAD (2026-07 ruling): a killed local
        # stays dead for the rest of the run. Lay the run's bodies
        # back down where they fell BEFORE the rot pass so a corpse
        # is never disturbed (rot skips _is_corpse). Nobody leaves
        # Brimley, not even by dying (NARRATIVE §5).
        self._apply_dead_locals()
        # Re-derive the world rot for this scene from the evidence
        # count (rot decals, the ambient air, the stage-3 Sheriff).
        self._apply_rot()
        # The Moths (the King's heralds) seed with the scene:
        # evidence-scaled on the open surface, a retinue in the
        # King's own room (rot_mixin, MOTH_* config).
        self._spawn_moths()

    def _river_blocks(self, target_x, target_y):
        """Custom passability for the brimley river. The `~` floor is
        non-solid by default, so this is the gate: in any other scene
        it's a no-op, and in the brimley a `~` tile is walkable only
        if (a) the player is already in the river, OR (b) the target
        tile is the designated entry tile. Falling-back-into-the-river
        from land or bridge is blocked everywhere else."""
        if self.scene is None or self.scene.key != "brimley":
            return False
        if self.scene.char_floor_at(target_x, target_y) != "~":
            return False
        if self.player.in_river:
            return False
        ttx = int(target_x // Scene.TILE)
        tty = int(target_y // Scene.TILE)
        return (ttx, tty) != RIVER_ENTRY_TILE

    def _wading(self):
        """True when the player stands in deep water: a `~` floor tile in a
        WADE scene (the flooded deep works). Drives the wade slow + the loud
        splash noise. The Brimley river is deliberately excluded -- it is not
        a WADE scene, so its `~` keeps its own rules (see WADE_SCENES)."""
        sc = self.scene
        return (sc is not None and sc.key in WADE_SCENES
                and sc.char_floor_at(self.player.x, self.player.y) == "~")

    def _update_camera(self, snap=False):
        target_x = self.player.x - SCREEN_W // 2
        target_y = self.player.y - SCREEN_H // 2
        # Lead the camera in the way the player is WALKING so they can see
        # where a path is taking them BEFORE they commit -- vital where the
        # road bends or folds back on itself. Under tilt the lead follows
        # the last movement direction with its own easing, and HOLDS there
        # while standing (2026-07 camera tuning): it must never ride the
        # aim cursor, or every mouse flick drags the whole view around the
        # player. The flat dev view keeps the old facing lead so pitch-0
        # captures stay byte-identical.
        if self._tilt_on():
            ld = getattr(self, "_cam_lead_dir", None)
            gx = gy = 0.0
            if ld is not None:
                gx, gy = ld[0] * CAM_LOOKAHEAD, ld[1] * CAM_LOOKAHEAD
            lx, ly = getattr(self, "_cam_lead", (gx, gy))
            if snap:
                lx, ly = gx, gy
            else:
                lx += (gx - lx) * 0.06
                ly += (gy - ly) * 0.06
            self._cam_lead = (lx, ly)
            target_x += lx
            target_y += ly
        else:
            fx, fy = self.player.facing
            flen = math.hypot(fx, fy) or 1.0
            target_x += (fx / flen) * CAM_LOOKAHEAD
            target_y += (fy / flen) * CAM_LOOKAHEAD
        # The oblique tilt follows the player (the skybox fills the voids);
        # there is no flat scene-centre clamp.
        if snap:
            self.cam_x = target_x; self.cam_y = target_y
        else:
            self.cam_x += (target_x - self.cam_x) * 0.18
            self.cam_y += (target_y - self.cam_y) * 0.18
        # Pitch is locked to the tilt, so the paired zoom-out is constant.
        self.camera.scale = TILT_ZOOM
        # Keep the camera's spatial pivot in sync here (was only in draw_world)
        # so mouse->world (unproject) in _update_look reads the live frame.
        self.camera.origin = (SCREEN_W // 2, SCREEN_H // 2)
        self.camera.cam_x = self.cam_x + SCREEN_W // 2
        self.camera.cam_y = self.cam_y + SCREEN_H // 2

    def _tilt_on(self):
        """The oblique tilt is the only camera. Kept as a stable predicate for
        the render/look code: always true, there is no flat/pitch-0 view."""
        return True

    def _update_look(self, dt):
        """The camera rides behind the player's body heading. The body chases
        the cursor's SCREEN offset from the player's screen position, but only
        when the cursor is in the UPPER half of the screen (above the player).
        The lower half is free-look space — drop the cursor below the player
        to scan or fire backwards without the camera following you around.
        Chase is rate-capped at TURN_RATE rad/s with a small dead-zone so
        micro-jitter near straight-ahead doesn't shake the view. The sprite +
        gun still face the unprojected world cursor directly (free aim).
        Tilt mode only."""
        if not (self.state == "playing" and self.player):
            return
        mx, my = pygame.mouse.get_pos()
        # Free aim for the gun: world heading to the point under the cursor.
        wx, wy = self.camera.unproject(mx, my)
        aim = math.atan2(wy - self.player.y, wx - self.player.x)
        self.look.update(aim_heading=aim)
        # Camera steering: cursor's screen offset from the player's screen
        # position. Screen-up is (0, -1); positive offset = cursor to the right
        # of straight ahead, which should rotate body the same direction.
        # Screen offset is camera-yaw-independent, so the chase converges
        # instead of spinning (a world-unprojected aim would feed back: the
        # world point under the cursor rotates 1:1 with cam_yaw).
        psx, psy = self.camera.project(self.player.x, self.player.y)
        dxs = mx - psx
        dys = my - psy
        # Aim-steady rules (2026-07): holding the trigger (or the beat
        # after a shot) locks the chase entirely -- lining up a shot is
        # a stable platform, never a standing order to swing. Standing
        # still damps the chase hard; the full turn rate only applies
        # while movement keys are actually driving.
        self._chase_lock_t = max(0.0,
                                 getattr(self, "_chase_lock_t", 0.0) - dt)
        if pygame.mouse.get_pressed()[0] or self._chase_lock_t > 0.0:
            chase_rate = 0.0
        elif getattr(self, "_move_input_active", False):
            chase_rate = TURN_RATE
        else:
            chase_rate = TURN_RATE * CHASE_STATIONARY_MULT
        if dys < 0 and chase_rate > 0.0:
            offset = math.atan2(dxs, -dys)
            # Chase only inside the FORWARD cone: AIM_DEAD_ZONE arc near
            # straight-up (no chase), out to CHASE_MAX_OFFSET near the
            # horizontal (no chase). Both bounds give the camera a few degrees
            # of rest before it starts swinging.
            if abs(offset) < CHASE_MAX_OFFSET:
                self.look.chase_by(offset, dt, chase_rate, AIM_DEAD_ZONE)
        self.camera.yaw = self.look.cam_yaw
        # The sprite + gun face the cursor (free aim), independent of body.
        ax, ay = self.look.aim_vec()
        self.player.facing = (ax, ay)

    def update_player(self, dt, keys):
        if (self.dialog.active or self.inv_ui.open or self.notebook_ui.open
                or self.text_input.active):
            return
        # During the threshold-closure sequence, the player cannot
        # move. They can only watch.
        if getattr(self, "_closure_locked", False):
            return
        # Mid-struggle the player is pinned in the hide: no movement,
        # no interaction -- the mash (E/SPACE, handled in the event
        # loop) is the only verb until it resolves.
        if getattr(self, "_struggle", None) is not None:
            return
        # Emerging from an enclosed hide takes a BEAT (the deferred
        # exit-takes-a-beat window, DESIGN.md §12): out, visible, and
        # rooted while you unfold. The struggle burst-out bypasses this
        # (it has its own panic sprint).
        emerge = getattr(self.player, "emerge_t", 0.0)
        if emerge > 0.0:
            self.player.emerge_t = emerge - dt
            return
        # Tick the sprint timers regardless of input -- cooldown has
        # to drain even when the player is standing still.
        self._tick_sprint(dt, keys)
        # Hide is a STRATEGIC verb: while hidden the player is safe
        # from patrol spotting AND the proximity ramp slows to a
        # crawl (only the halved passive rate -- no stillness
        # penalty applies). This makes hide a real choice for
        # investigation pauses, not a panic-trap that punishes the
        # player for using cover.
        dx = dy = 0
        if self._tilt_on():
            # Camera-relative movement. W/S = forward/back along the body
            # heading; A/D = strafe perpendicular. Steering happens by looking:
            # _update_look drags the body (and the camera) toward the mouse aim
            # at TURN_RATE rad/s through a dead-zone. The sprite + gun face the
            # cursor independently.
            fwd = ((1.0 if keys[pygame.K_w] or keys[pygame.K_UP] else 0.0)
                   - (1.0 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0.0))
            side = ((1.0 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0.0)
                    - (1.0 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0.0))
            if fwd or side:
                fx, fy = self.look.facing_vec()
                # Right-perpendicular to body in world coords (+y = down):
                # rotate body by +90 deg → (-fy, fx).
                px, py = -fy, fx
                dx = fx * fwd + px * side
                dy = fy * fwd + py * side
        else:
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
        # Movement breaks explicit hide spots (those set
        # hide_origin so we can teleport the player back). Corn-
        # patch cover is *passive* -- the player walks through the
        # patch while hidden, no teleport on exit; the floor-tile
        # check after movement clears the hide when they step out.
        input_active = bool(dx or dy)
        # Shared with _update_look: the camera chase runs at full rate
        # only while movement keys are actually driving (aim-steady).
        self._move_input_active = input_active
        # The camera's walk-lead direction (see _update_camera): the last
        # direction the keys actually drove, held while standing so the
        # view rests instead of recentring.
        if input_active:
            mlen = math.hypot(dx, dy) or 1.0
            self._cam_lead_dir = (dx / mlen, dy / mlen)
        if input_active and self.player.hidden is not None:
            if self.player.hide_origin is not None:
                self.player.hidden = None
                self.player.x, self.player.y = self.player.hide_origin
                self.player.hide_origin = None
                self.show_notice("You step out of cover.",
                                  duration=1.6)
            # else: corn-state hide; let the floor check below
            # handle entry/exit transparently.
        # Quadratic visibility compression: barely shows in normal play, bites
        # only as visibility approaches the King-gate. Sprint multiplies on top.
        comp_mult = 1.0 - self.visibility * self.visibility * 0.45
        sprint_mult = PLAYER_SPRINT_MULT if self.player.sprint_active else 1.0
        # The panic burst out of a won struggle: a short adrenaline window
        # (doesn't stack with sprint -- the stronger of the two applies).
        bt = getattr(self.player, "_burst_t", 0.0)
        if bt > 0.0:
            self.player._burst_t = max(0.0, bt - dt)
            sprint_mult = max(sprint_mult, STRUGGLE_BURST_MULT)
        effective_speed = self.player.speed * comp_mult * sprint_mult
        # Deep water drags: wading a flooded `~` tile halves your speed on top
        # of everything else, so you cannot sprint clear of it (WADE_*).
        if self._wading():
            effective_speed *= WADE_SPEED_MULT
        # Build the input-driven TARGET velocity (world units/sec), then ease
        # the actual velocity toward it over MOVE_SMOOTH_TAU. Releasing input
        # coasts to a stop instead of cutting cold.
        if input_active:
            mag = math.hypot(dx, dy) or 1
            ndx, ndy = dx / mag, dy / mag
            # (dx,dy) is already a world heading vector (W/S along the body
            # facing, A/D strafe); the sprite faces the cursor, set by
            # _update_look.
            target_vx = ndx * effective_speed
            target_vy = ndy * effective_speed
        else:
            target_vx = target_vy = 0.0
        k = 1.0 - math.exp(-dt / MOVE_SMOOTH_TAU)
        self.player.vel_x += (target_vx - self.player.vel_x) * k
        self.player.vel_y += (target_vy - self.player.vel_y) * k
        # Snap to zero when coasting tail is below 1 unit/sec so we don't
        # accumulate jitter.
        if (not input_active and abs(self.player.vel_x) < 1.0
                and abs(self.player.vel_y) < 1.0):
            self.player.vel_x = 0.0
            self.player.vel_y = 0.0
        vx, vy = self.player.vel_x, self.player.vel_y
        in_motion = bool(input_active or vx or vy)
        if in_motion:
            # Stride cadence tracks ACTUAL ground speed, so the legs never
            # skate: scale the walk-phase advance by how fast we're really
            # moving (WALK_ANIM_RATE is the cadence at the base walk speed).
            # A fixed rate made the feet cycle twice as fast as the ground
            # covered after the base speed was halved (130 -> 64 px/s).
            spd = math.hypot(vx, vy)
            self.player.walk_phase += (dt * WALK_ANIM_RATE
                                       * (spd / self.player.speed))
            new_x = self.player.x + vx * dt
            new_y = self.player.y + vy * dt
            blocked_x = (self.scene.is_solid_at(new_x, self.player.y)
                         or self._river_blocks(new_x, self.player.y))
            blocked_y = (self.scene.is_solid_at(self.player.x, new_y)
                         or self._river_blocks(self.player.x, new_y))
            moved = False
            if not blocked_x:
                self.player.x = new_x
                moved = True
            else:
                # Wall on this axis: kill the residual velocity so we don't
                # keep grinding into it next frame.
                self.player.vel_x = 0.0
            if not blocked_y:
                self.player.y = new_y
                moved = True
            else:
                self.player.vel_y = 0.0
            # Toroidal wrap. When the scene is wrap_x / wrap_y, the
            # player's coord cycles mod world width / height and the
            # camera is shifted by the same amount so the world
            # appears to keep extending under them -- no jump, no
            # transition. The fold made felt.
            if self.scene.wrap_x:
                world_w = self.scene.w * Scene.TILE
                if self.player.x < 0:
                    self.player.x += world_w
                    self.cam_x += world_w
                elif self.player.x >= world_w:
                    self.player.x -= world_w
                    self.cam_x -= world_w
            if self.scene.wrap_y:
                world_h = self.scene.h * Scene.TILE
                if self.player.y < 0:
                    self.player.y += world_h
                    self.cam_y += world_h
                elif self.player.y >= world_h:
                    self.player.y -= world_h
                    self.cam_y -= world_h
            # Treadmill BAND (arrival_road): only a small northern stretch loops.
            # Cross the band's north edge walking up and you wrap back to its
            # south edge (player + camera shift together, so no jump) -- the road
            # loops a small landmark-free part forever. Walking south just leaves
            # the band into the fixed arrival stretch (no wrap that way).
            _tm = getattr(self.scene, "_treadmill", None)
            if _tm is not None:
                _band_top, _band_bottom = _tm
                if self.player.y < _band_top:
                    _band = _band_bottom - _band_top
                    self.player.y += _band
                    self.cam_y += _band
            if input_active and not moved:
                self.player.bump_timer -= dt
                if self.player.bump_timer <= 0:
                    self.audio.play("bump", 0.4)
                    self.player.bump_timer = 0.25
            elif moved:
                self.stillness_t = 0.0
                # Corn-patch cover: passive hide while standing on
                # `:` tiles. Doesn't compete with explicit hide
                # spots (those set hide_origin) -- if the player is
                # already in a hide-spot, leave that state alone.
                # Corn-state hide is cleared the moment they step
                # off a corn tile, so the cover is genuinely
                # tile-bound.
                floor_ch_now = self.scene.char_floor_at(
                    self.player.x, self.player.y)
                on_corn = (floor_ch_now == ":")
                if on_corn and self.player.hidden is None:
                    self.player.hidden = "corn"
                    self.audio.play("hide_enter", 0.55)
                    # One-shot teach (TODO #5): corn is CONCEALMENT, not
                    # invisibility (the stealth rework's core rule).
                    if self.save and not self.save.flag("teach_corn"):
                        self.save.set_flag("teach_corn", True)
                        self.show_notice("The stalks take you in. Distance "
                                         "hides you. Close eyes still find "
                                         "you.", duration=3.6)
                elif (not on_corn) and self.player.hidden == "corn":
                    self.player.hidden = None
                    self.audio.play("hide_exit", 0.55)
                # Sync the in_river state to whatever floor the player
                # is now standing on. River tile -> True, anything else
                # -> False. The blocker logic above ensures the player
                # only ever steps onto a river tile they're allowed on.
                self.player.in_river = (
                    self.scene.char_floor_at(self.player.x, self.player.y)
                    == "~"
                )
                self.player.step_timer -= dt
                if self.player.step_timer <= 0 and self._wading():
                    # A wet footfall in the flooded deep: slow, heavy, and
                    # LOUD -- a splash (over NOISE_SEARCH_PULL) the searchers
                    # converge on (WADE_*). No creepy-desync, no sprint
                    # scaling: water is loud whether you creep or run.
                    self.player.step_timer = WADE_STEP_EVERY
                    self.audio.play_in_scene("step_water", 0.75)
                    self.scene.emit_noise(self.player.x, self.player.y,
                                          WADE_SPLASH_LOUD, kind="splash",
                                          reach=WADE_SPLASH_REACH)
                elif self.player.step_timer <= 0:
                    self.player.step_timer = 0.32
                    ch = self.scene.char_floor_at(self.player.x, self.player.y)
                    sfx = tile_footstep(ch)
                    # Out-of-body trick: every 12th step on void or
                    # basement tiles, delay the SFX by ~0.12s so it
                    # lands after the visual step. Subtle desync, no
                    # comment for the player, just a wrongness in the
                    # rhythm.
                    creepy_tile = (sfx == "step_void") or (ch == "x")
                    delayed = False
                    if creepy_tile:
                        self._creepy_step_count += 1
                        if self._creepy_step_count % 12 == 0:
                            self._delayed_audio.append([0.12, sfx, 0.7])
                            delayed = True
                    if not delayed:
                        self.audio.play_in_scene(sfx, 0.7)
                    # Broadcast the step to listening cultists. Per-
                    # surface base loudness, scaled 1.5x while
                    # sprinting. Cultists in SCOUT poll
                    # _last_step_event each tick and transition to
                    # INVESTIGATE if it's recent + close + above
                    # their hearing threshold.
                    # Per-surface base loudness. Wood/stone are loud
                    # enough to trip cultist hearing on a walk;
                    # grass/carpet/void need a sprint to clear the
                    # 0.7 threshold. Sprint multiplier is 2.0 so
                    # sprint-on-grass triggers (0.4 * 2 = 0.8) while
                    # walk-on-grass stays inert (0.4).
                    base = {
                        "step_grass":   0.40,
                        "step_carpet":  0.30,
                        "step_wood":    0.85,
                        "step_stone":   0.90,
                        "step_void":    0.50,
                    }.get(sfx, 0.50)
                    mult = 2.0 if self.player.sprint_active else 1.0
                    self.scene.emit_noise(self.player.x, self.player.y,
                                          base * mult, kind="step")
        else:
            self.player.walk_phase = 0
            self.stillness_t += dt
        self.player.melee_cd = max(0, self.player.melee_cd - dt)
        self._gun_cd = max(0.0, self._gun_cd - dt)
        self.player.melee_swing_t = max(0, self.player.melee_swing_t - dt)
        self.player.invuln = max(0, self.player.invuln - dt)
        for it in list(self.scene.items):
            if math.hypot(self.player.x - it["x"], self.player.y - it["y"]) < 18:
                key = it["key"]
                d = ITEM_DEFS.get(key, {"name": key})
                self.player.inventory.add(key, it.get("qty", 1))
                self.scene.items.remove(it)
                self.audio.play("pickup", 0.7)
                self.show_notice(f"Picked up: {d['name']}")
                if it.get("on_pickup"):
                    it["on_pickup"](self)

    # ---- The church bell (the town's dominant noise source) ----
    def _ring_bell(self):
        """E on the pull rope in the bell tower (scenes/threshold_extras).
        Arms the peal: BELL_RING_DUR seconds of wall-clock ringing that
        _tick_bell drives every frame, whatever scene the player walks
        through. The peal MASKS every small surface noise (the player's
        own steps drown under it) and pulls the cult across Brimley to
        the church door. A hunter that reaches the door stills the
        rope; otherwise the peal rings itself out."""
        if self._bell_t > 0.0:
            self.show_notice("The bell is already swinging.",
                             duration=1.6)
            return
        self._bell_t = BELL_RING_DUR
        self._bell_toll_t = 0.0          # first strike lands this frame
        self.save.set_flag("bell_rung", True)
        self.show_notice(
            "You haul the rope. The bell swings out over the town.",
            duration=2.6)

    def _tick_bell(self, dt):
        """Drive a live peal (armed by _ring_bell). Lives on Game, not
        the scene, so the bell keeps ringing across scene loads: haul
        the rope, climb down, and walk out into the town it is calling
        in. Each strike plays the toll, re-arms the surface noise MASK
        (so loud it hides small sounds), and in Brimley broadcasts a
        map-wide pull at the church door. Cult hunters converge on it;
        the first to reach the door stills the rope and searches the
        churchyard. Apex pursuers never hear it. The deep places never
        hear it either."""
        if self._bell_t <= 0.0:
            return
        self._bell_t -= dt
        sc = self.scene
        if sc is None:
            return
        key = sc.key
        bell_door = getattr(sc, "_bell_door", None)
        # The tower prop swings while the peal lives.
        if key == "bell_tower":
            for deco in sc.decorations:
                if deco.kind == "church_bell":
                    deco.ring_t = max(0.0, self._bell_t)
        # A cult hunter reaching the church door stills the rope. Only
        # a scene that declares the door (Brimley) can be silenced --
        # elsewhere nobody can reach the rope and the 20s peal is the
        # only clock.
        if bell_door is not None:
            bx, by = bell_door
            for n in sc.npcs:
                tag = str(getattr(n, "tag", ""))
                if not tag.startswith("cult_") or tag == "cult_convert":
                    continue
                if (not getattr(n, "alive", True)
                        or getattr(n, "_is_corpse", False)):
                    continue
                if getattr(n, "_force_chase", False):
                    continue            # apex hunts YOU, not the noise
                if sc.world_dist(n.x, n.y, bx, by) <= BELL_STOP_DIST:
                    self._bell_t = 0.0
                    sc.clear_noise_mask()
                    # A stilled bell stops calling: purge its still-
                    # fresh events so they can't yank the silencer (or
                    # anyone else) straight back into an investigate.
                    sc._noise_events = [e for e in sc._noise_events
                                        if e[4] != "bell"]
                    # The silencer lingers: it sweeps the churchyard
                    # before drifting back to its rounds.
                    n._last_seen_pos = (bx, by)
                    _cult_enter_search(n, sc)
                    self.audio.play("bump", 0.5)
                    self.show_notice("The bell stops mid swing.",
                                     duration=2.4)
                    return
        if self._bell_t <= 0.0:
            sc.clear_noise_mask()        # rang itself out
            return
        # The strike cadence.
        self._bell_toll_t -= dt
        if self._bell_toll_t > 0.0:
            return
        self._bell_toll_t = BELL_TOLL_PERIOD
        underground = key in UNDERGROUND_SCENES
        if underground:
            vol = 0.0                    # the peal doesn't reach down here
        elif key == "bell_tower":
            vol = 0.95                   # you are standing under it
        elif key == "church":
            vol = 0.70                   # the church nave, one floor down
        elif bell_door is not None:
            vol = max(0.25, 0.85 * self.audio.distance_attenuation(
                bell_door[0], bell_door[1],
                self.player.x, self.player.y, falloff=900.0))
        else:
            vol = 0.30                   # a far peal through the trees
        if vol > 0.0:
            self.audio.play("bell_toll", vol)
        if not underground:
            # The peal drowns every smaller noise on the surface...
            cx, cy = bell_door if bell_door is not None else (
                sc.w * TILE * 0.5, sc.h * TILE * 0.5)
            sc.set_noise_mask(cx, cy, BELL_MASK_RADIUS, BELL_MASK_LEVEL,
                              BELL_TOLL_PERIOD + 0.6)
            # ...and calls the cult in: a map-wide pull at the church
            # door. Only the scene that declares the door has anyone
            # who can answer it.
            if bell_door is not None:
                sc.emit_noise(bell_door[0], bell_door[1], 1.0,
                              kind="bell", reach=BELL_REACH)

    # ---- Placed noisemakers (traps underfoot + toggleable sources) ----
    def _trip_noise_traps(self, dt):
        """Passive noisemakers underfoot (Scene.add_noise_trap): strewn
        cans, glass litter, a loose plank, a crow that flushes. Fire ON
        ENTRY into the trap's radius -- once -- then re-arm only after
        the player leaves it (plus TRAP_REARM), so standing in the
        litter doesn't machine-gun events. The crow is one-shot per
        load: the bird is gone. A live bell mask still swallows the
        event (loud hides small); the foley plays regardless."""
        sc = self.scene
        traps = getattr(sc, "noise_traps", None)
        if not traps:
            return
        px, py = self.player.x, self.player.y
        for tr in traps:
            if tr.get("dead"):
                continue
            tr["cool"] = max(0.0, tr["cool"] - dt)
            inside = sc.world_dist(px, py, tr["x"], tr["y"]) <= tr["r"]
            fire = inside and not tr["inside"] and tr["cool"] <= 0.0
            tr["inside"] = inside
            if not fire:
                continue
            tr["cool"] = TRAP_REARM
            sc.emit_noise(tr["x"], tr["y"], tr["loud"], kind=tr["kind"])
            if tr["sfx"]:
                self.audio.play_in_scene(tr["sfx"], 0.8)
            if tr["kind"] == "crow":
                tr["dead"] = True
                d = tr.get("deco")
                if d is not None:
                    d.flushed_at = d.t       # the draw animates the flush

    def _tick_noise_sources(self, dt):
        """Drive the toggleable lure sources (Scene.add_noise_source).
        A playing source emits its event every `period` (with its own
        `reach`, at 0.8 -- turns scout heads, never breaks a
        sighting-born search) and plays its loop foley panned/attenuated
        to the player's ear. The first mobile cult hunter to reach it
        shuts it off and sweeps around it, exactly like the bell;
        set-piece kneelers and apex pursuers never touch it."""
        sc = self.scene
        srcs = getattr(sc, "noise_sources", None)
        if not srcs:
            return
        for s in srcs:
            if not s["on"]:
                continue
            silencer = None
            for group in (sc.npcs, sc.enemies):
                for a in group:
                    if not getattr(a, "alive", True):
                        continue
                    if getattr(a, "_is_corpse", False):
                        continue
                    is_cult = (str(getattr(a, "tag", "")).startswith("cult_")
                               or getattr(a, "kind", "") == "cultist")
                    if not is_cult or getattr(a, "tag", "") == "cult_convert":
                        continue
                    if getattr(a, "_force_chase", False):
                        continue
                    if (getattr(a, "lock_facing", False)
                            or getattr(a, "aggro", 1) == 0):
                        continue
                    if sc.world_dist(a.x, a.y, s["x"], s["y"]) \
                            <= NOISE_SRC_SILENCE_DIST:
                        silencer = a
                        break
                if silencer is not None:
                    break
            if silencer is not None:
                s["on"] = False
                # a dead lure stops calling (same rule as the bell)
                sc._noise_events = [e for e in sc._noise_events
                                    if e[4] != s["kind"]]
                silencer._last_seen_pos = (s["x"], s["y"])
                _cult_enter_search(silencer, sc)
                self.audio.play("bump", 0.4)
                if s.get("silenced_notice"):
                    self.show_notice(s["silenced_notice"], duration=2.4)
                continue
            s["t"] -= dt
            if s["t"] > 0.0:
                continue
            s["t"] = s["period"]
            sc.emit_noise(s["x"], s["y"], s["loud"], kind=s["kind"],
                          reach=s["reach"])
            if s["sfx"]:
                pan = self.audio.pan_for_world(s["x"], self.player.x)
                dmult = self.audio.distance_attenuation(
                    s["x"], s["y"], self.player.x, self.player.y,
                    falloff=420.0)
                self.audio.play(s["sfx"], 0.8 * dmult, pan=pan)

    def _try_toggle_source(self):
        """E on a placed noise source flips it. Runs after the NPC
        check in try_interact (talking always wins) and before the
        scene's own on_interact_fn."""
        srcs = getattr(self.scene, "noise_sources", None)
        if not srcs:
            return False
        for s in srcs:
            if math.hypot(s["x"] - self.player.x,
                          s["y"] - self.player.y) > 40:
                continue
            s["on"] = not s["on"]
            self.audio.play("bump", 0.35)
            if s["on"]:
                s["t"] = 0.0             # first emit lands this tick
                if s.get("on_notice"):
                    self.show_notice(s["on_notice"], duration=2.6)
            else:
                if s.get("off_notice"):
                    self.show_notice(s["off_notice"], duration=1.8)
            return True
        return False

    # ---- Darkness as concealment (DESIGN.md §12) ----
    def _tick_dark_cover(self):
        """Stamp player._in_dark once per frame: True in a DARK scene
        with the flashlight unlit and the player outside every light
        pool (Scene.lit_at). systems/stealth.concealment_factor reads
        the stamp, so the gloom scales every cult eye's score (and the
        gaze pressure) by SUS_CONCEAL_DARK -- leaky cover, like corn.
        Apex pursuers ignore all cover as ever. A one-shot teach cue
        fires the first time the dark takes you with the cult near."""
        p = self.player
        if p is None or self.scene is None:
            return
        in_dark = (self.scene.key in DARK_SCENES
                   and not self._flashlight_lit()
                   and not self.scene.lit_at(p.x, p.y))
        if in_dark:
            # a kindling/flaring Moth is a lamp: its pool breaks the
            # gloom around the player (the alarm also UNHIDES you)
            for m in (getattr(self.scene, "_moths", None) or []):
                if (m["glow"] > 0.3 and self.scene.world_dist(
                        m["x"], m["y"], p.x, p.y) < MOTH_LIGHT_R):
                    in_dark = False
                    break
        was = getattr(p, "_in_dark", False)
        p._in_dark = in_dark
        if (in_dark and not was
                and not self.save.flag("teach_dark_seen")):
            near = False
            for grp in (self.scene.npcs, self.scene.enemies):
                for a in grp:
                    if not getattr(a, "alive", True):
                        continue
                    is_cult = (str(getattr(a, "tag", "")).startswith("cult_")
                               or getattr(a, "kind", "") == "cultist")
                    if is_cult and self.scene.world_dist(
                            a.x, a.y, p.x, p.y) < 260:
                        near = True
                        break
                if near:
                    break
            if near:
                self.save.set_flag("teach_dark_seen", True)
                self.show_notice(
                    "The dark takes the edge off their eyes. It will "
                    "not save you up close.", duration=3.0)

    # ---- Animated doors + the one-hop noise bleed ----
    def _pulse_door_at(self, x, y, hold=0.9, quiet=False):
        """Swing the door leaf at world (x, y) if that tile holds a
        door; plays the positional door_open foley when the pulse
        opens a resting leaf. The tell for anything passing through.
        `quiet=True` for pulses whose sound is already covered -- the
        transition fade plays its own door_open/door_close pair, so
        the player-passage swings must not double it."""
        sc = self.scene
        if sc is None:
            return
        tx, ty = int(x // TILE), int(y // TILE)
        wtx = tx % sc.w if sc.wrap_x else tx
        wty = ty % sc.h if sc.wrap_y else ty
        if not (0 <= wty < sc.h and 0 <= wtx < sc.w):
            return
        from scenes.base import _DOOR_CHARS
        if sc.objects[wty][wtx] not in _DOOR_CHARS:
            return
        if sc.door_pulse(wtx, wty, hold=hold, quiet=quiet) and not quiet:
            pan = self.audio.pan_for_world(x, self.player.x)
            dm = self.audio.distance_attenuation(
                x, y, self.player.x, self.player.y)
            self.audio.play("door_open", 0.55 * dm, pan=pan)

    def _tick_doors(self, dt):
        """Ease every live door-leaf swing (Scene.door_pulse): open
        while the hold lasts, shut after, with the door_close foley as
        the leaf seats. Anim state lives on the scene, so a scene load
        drops it with the room."""
        sc = self.scene
        anim = getattr(sc, "_door_anim", None)
        if not anim:
            return
        done = []
        for key, st in anim.items():
            if st["hold"] > 0.0:
                st["hold"] -= dt
                st["open"] = min(1.0, st["open"] + dt / 0.22)
            else:
                st["open"] -= dt / 0.30
                if st["open"] <= 0.0:
                    done.append(key)
        for key in done:
            quiet = anim[key].get("quiet", False)
            del anim[key]
            if quiet:
                continue        # its foley is the transition's own pair
            wx, wy = key[0] * TILE + 16, key[1] * TILE + 16
            pan = self.audio.pan_for_world(wx, self.player.x)
            dm = self.audio.distance_attenuation(
                wx, wy, self.player.x, self.player.y)
            self.audio.play("door_close", 0.45 * dm, pan=pan)

    def _nearest_exit_tile(self, x, y):
        """The (tx, ty) of the scene exit nearest to world (x, y) --
        the door the next room's visitor comes through. None if the
        scene has no exits on the grid."""
        sc = self.scene
        best = None
        best_d = 1e18
        for ty in range(sc.h):
            row = sc.objects[ty]
            for tx in range(sc.w):
                if row[tx] not in sc.exits:
                    continue
                d = sc.world_dist(x, y, tx * TILE + 16, ty * TILE + 16)
                if d < best_d:
                    best_d = d
                    best = (tx, ty)
        return best

    def _tick_bleed(self, dt):
        """The one-hop noise bleed: the tunnels carry sound. A LOUD
        noise (>= BLEED_LOUD -- a gunshot, the struggle burst) in an
        underground room brings ONE transient cultist through the
        nearest exit a few seconds later (the leaf swings, the tell).
        He walks to the noise, looks it over, and leaves the way he
        came -- unless he finds YOU, in which case he is a real threat
        and stays hot until the machine cools. Capped: one live visitor,
        a long cooldown, never in safe rooms or refuges, never into a
        room already crowded with cult."""
        self._bleed_cd = max(0.0, self._bleed_cd - dt)
        sc = self.scene
        if sc is None or self.player is None:
            return
        b = self._bleed
        if b is None:
            if self._bleed_cd > 0.0:
                return
            key = sc.key
            if (key not in UNDERGROUND_SCENES or key in SAFE_SCENES
                    or key in FOLD_REFUGE_SCENES):
                return
            live = 0
            for grp in (sc.npcs, sc.enemies):
                for a in grp:
                    if not getattr(a, "alive", True):
                        continue
                    if getattr(a, "_is_corpse", False):
                        continue
                    if (str(getattr(a, "tag", "")).startswith("cult_")
                            or getattr(a, "kind", "") == "cultist"):
                        live += 1
            if live >= BLEED_CAP:
                return
            now = sc._noise_now
            for (ex, ey, loud, et, _kind, _reach) in sc._noise_events:
                if loud < BLEED_LOUD or now - et >= NOISE_FRESH:
                    continue
                door = self._nearest_exit_tile(ex, ey)
                if door is None:
                    return
                self._bleed = {"t": random.uniform(BLEED_DELAY_LO,
                                                   BLEED_DELAY_HI),
                               "door": door, "src": (ex, ey),
                               "npc": None, "linger": 0.0}
                return
            return
        if b["npc"] is None:
            b["t"] -= dt
            if b["t"] > 0.0:
                return
            tx, ty = b["door"]
            wx, wy = tx * TILE + 16, ty * TILE + 16
            if sc.is_solid_at(wx, wy):
                self._bleed = None
                self._bleed_cd = BLEED_CD
                return
            from scenes.depths import _cultist
            e = _cultist(wx, wy, speed=0.9)
            e._cult_state = "investigate"
            e._last_seen_pos = b["src"]
            e._cult_state_t = 6.0 + sc.world_dist(
                wx, wy, b["src"][0], b["src"][1]) / NOISE_WALK_SPEED
            e._noise_loud = 0.95
            e._bleed_transient = True
            sc.enemies.append(e)
            b["npc"] = e
            self._pulse_door_at(wx, wy, hold=1.2)   # the door is the tell
            return
        e = b["npc"]
        if not getattr(e, "alive", True) or e not in sc.enemies:
            self._bleed = None
            self._bleed_cd = BLEED_CD
            return
        b["linger"] += dt
        if e._cult_state in ("chase", "search"):
            return                        # he found something; he stays hot
        tx, ty = b["door"]
        wx, wy = tx * TILE + 16, ty * TILE + 16
        if (not b.get("leaving")
                and e._cult_state == "investigate"
                and b["linger"] < BLEED_LINGER):
            return
        # done looking: back out the way he came, and gone
        b["leaving"] = True
        e._cult_state = "investigate"
        e._last_seen_pos = (wx, wy)
        e._cult_state_t = max(getattr(e, "_cult_state_t", 0.0), 6.0)
        e._noise_loud = 0.95
        if sc.world_dist(e.x, e.y, wx, wy) < 22:
            e.alive = False
            if e in sc.enemies:
                sc.enemies.remove(e)
            self._pulse_door_at(wx, wy, hold=0.6)
            self._bleed = None
            self._bleed_cd = BLEED_CD

    # ---- Interaction ----
    def try_interact(self):
        # If currently hidden, E exits the hide. Leaving an ENCLOSED
        # hide takes a beat (HIDE_EXIT_BEAT): you are out and visible
        # before you can move -- bolting is a commitment, not a blink.
        if self.player.hidden is not None:
            enclosed = _is_enclosed_hide(self.player)
            self.player.hidden = None
            if self.player.hide_origin is not None:
                self.player.x, self.player.y = self.player.hide_origin
                self.player.hide_origin = None
            if enclosed:
                self.player.emerge_t = HIDE_EXIT_BEAT
            self.show_notice("You slip out of cover.", duration=1.6)
            self.audio.play("hide_exit", 0.7)
            return
        # A floating conversation is up and you're beside the speaker:
        # E advances it (skip the reveal, then next line) instead of
        # starting something new.
        if self.float_speech.advance_from_input(self):
            return
        # Hide-spot pickup: scenes declare hide_spots = [(x,y,kind)]
        # where kind is 'under', 'in', or 'behind'. Closest within
        # 36 px wins. Fires before NPC interaction so the player
        # can hide at the foot of an NPC if they need to.
        hide_spots = getattr(self.scene, "hide_spots", None) or []
        bestH = None; bdH = 1e9
        for hx, hy, hkind in hide_spots:
            d = math.hypot(hx - self.player.x, hy - self.player.y)
            if d < bdH and d < 36:
                bdH = d; bestH = (hx, hy, hkind)
        if bestH:
            self.player.hidden = bestH[2]
            self.player.hide_origin = (self.player.x, self.player.y)
            self.player.x = bestH[0]; self.player.y = bestH[1]
            verb = {
                "under": "you crawl under cover.",
                "in":    "you step inside.",
            }.get(bestH[2], "you take cover.")
            self.show_notice(verb, duration=1.8)
            self.audio.play("hide_enter", 0.7)
            return
        # Splitting axe: if the player has the lumber_axe in their
        # inventory and is adjacent to a chop-eligible tile (`*`
        # debris OR `q` boarded panel), pressing E swings it. Combat
        # is gone, so the equip-and-charge-attack route the original
        # game used is replaced with a single E press. Each chop is
        # persisted by per-coord save flag so the gap stays open
        # across re-entries.
        if self.player.inventory.has("lumber_axe"):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                tx = int((self.player.x + dx * TILE) // TILE)
                ty = int((self.player.y + dy * TILE) // TILE)
                notice = self._chop_tile(tx, ty)
                if notice:
                    self.player.melee_swing_t = AXE_SWING_DUR
                    self.player.melee_dir = (dx, dy)
                    self.audio.play("swing", 0.55)
                    self.audio.play("hit", 0.85)
                    self.audio.play("bump", 0.55)
                    self.show_notice(notice)
                    return
        # Chalk doors -- the cult's drawn-door compulsion. Examining one
        # surfaces the PI's interior voice (the descent's escalation lives on
        # what he EXAMINES, not on bare room entry). Placed clear of other
        # interactables, so it's safe to resolve before the NPC/scene checks.
        if self._try_chalk_interact():
            return
        # Standard NPC interaction
        best = None; bd = 1e9
        for npc in self.scene.npcs:
            if getattr(npc, "_inside", False):
                continue        # homebody is behind their door
            d = math.hypot(npc.x - self.player.x, npc.y - self.player.y)
            if d < bd and d < 40:
                bd = d; best = npc
        if best:
            self.audio.play("confirm", 0.6)
            # Mark the speaker so DialogueBox.show can float a casual
            # line over their head; cleared right after so scene hooks
            # that call dialog.show stay modal.
            self._speaking_npc = best
            try:
                best.interact(self)
            finally:
                self._speaking_npc = None
            return
        # Toggleable noise sources (the truck radio, the works valve) --
        # after NPCs (talking always wins), before the scene handler.
        if self._try_toggle_source():
            return
        if self.scene.on_interact_fn:
            self.scene.on_interact_fn(self)
            return
        # Last-resort feedback: if no NPC, no scene-specific E-handler,
        # and the player is pressed up against a facade door ('l') or a
        # locked-house door ('z'), give them a LISTEN beat -- press
        # your ear to the door and hear what's on the other side.
        # The line varies by scene. Checks the four cardinal-adjacent
        # tiles within ~1.5 tiles.
        sc = self.scene
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            tx = int((self.player.x + dx * TILE) // TILE)
            ty = int((self.player.y + dy * TILE) // TILE)
            if 0 <= ty < sc.h and 0 <= tx < sc.w:
                ch = sc.objects[ty][tx]
                if ch in ("l", "z"):
                    self._listen_at_door(ch, sc.key)
                    return
        # A narration caption with nothing else answering the press: E
        # skims it (finish the reveal, then next page). LAST on purpose:
        # the caption is ambient, and it must never gate the world -- a
        # bell pull, a hide, a door all win the E over the text. (Re-
        # pressing an object that re-shows its OWN caption pages it
        # instead of restarting; that is handled in Narration.begin.)
        if self.narration.advance_from_input():
            return

    def _listen_at_door(self, ch, scene_key):
        """Press an ear to a closed door. Plays a soft tap and shows a
        neutral one-line overhear. Locked doors ('z') keep the locked
        stinger; the listen is supplementary."""
        line = "You press your ear to the door. Quiet."
        self.audio.play("door_locked", 0.35)
        self.audio.play("breath", 0.30)
        if ch == "z":
            self.show_notice("Locked. " + line, duration=3.0)
        else:
            self.show_notice(line, duration=3.0)

    # ---- Combat ----
    def _chop_tile(self, tx, ty):
        """Break a single axe-eligible tile -- debris ('*') or boards
        ('q') -- and persist it by per-coord save flag so the gap stays
        open across re-entries. Returns a notice string when something
        broke, else None. Shared by the E-interact and the axe swing so
        both clear barricades identically."""
        sc_ = self.scene
        if not (0 <= ty < sc_.h and 0 <= tx < sc_.w):
            return None
        ch = sc_.objects[ty][tx]
        if ch == "*":
            # West-edge debris becomes the '4' exit tile when cleared.
            sc_.objects[ty][tx] = "4" if tx == 0 else "."
            self.save.set_flag(f"debris_broken_{sc_.key}_{tx}_{ty}", True)
            from scenes.base import invalidate_tilt_objects
            invalidate_tilt_objects()
            return "The pile splinters apart."
        if ch == "q":
            sc_.objects[ty][tx] = "."
            self.save.set_flag(f"boards_broken_{sc_.key}_{tx}_{ty}", True)
            from scenes.base import invalidate_tilt_objects
            invalidate_tilt_objects()
            return "The boards splinter away."
        return None

    def player_axe_swing(self):
        """The player's only attack -- GATED on the splitting axe. With
        the axe in hand a swing arcs through the tile in front: it
        splinters any barricade caught there (debris, boards) and
        STUNS a cultist or shadow in the arc (frozen + blind for a beat).
        The swing never kills -- it buys the seconds to break line of
        sight and reach cover. Without the axe the player has no attack."""
        p = self.player
        if (self.state != "playing" or p.hidden is not None
                or p.melee_cd > 0 or self.dialog.active):
            return
        if not p.inventory.has("lumber_axe"):
            return                       # no axe -> no swing at all
        p.melee_cd = MELEE_CD
        p.melee_swing_t = AXE_SWING_DUR
        p.melee_dir = p.facing
        self.audio.play("swing", 0.6)
        fx, fy = p.facing
        # Splinter a barricade in the swing's reach: the facing tile.
        bx = int((p.x + fx * TILE) // TILE)
        by = int((p.y + fy * TILE) // TILE)
        broke = self._chop_tile(bx, by)
        if broke:
            self.audio.play("hit", 0.85)
            self.audio.play("bump", 0.55)
            self.show_notice(broke)
        cx, cy = p.x + fx * 22, p.y + fy * 22
        hit = False
        for n in self.scene.npcs:
            if not str(getattr(n, "tag", "")).startswith("cult_"):
                continue
            if not getattr(n, "alive", True):
                continue
            if math.hypot(n.x - cx, n.y - cy) < MELEE_REACH:
                n._stun_t = MELEE_STUN_DUR
                n.flash = 0.12
                n._has_been_spotted = False      # they lose the lock on you
                hit = True
        # The axe also instantly dissolves a Watcher of the curse caught in
        # the arc (silent, free, but you must close to it).
        for w in list(self._watchers):
            if math.hypot(w.x - cx, w.y - cy) < MELEE_REACH * 1.4:
                self._dispel_watcher(w, reason="axe")
                hit = True
                break
        if hit:
            self.audio.play("hit", 0.5)
            if not self.save.flag("stun_taught"):
                self.save.set_flag("stun_taught", True)
                self.show_notice("You knock it back. It won't stay "
                                 "down. Run.", duration=2.6)

    def player_fire_gun(self):
        """Fire the pistol in the facing direction. The evidence count
        gates the effect (NARRATIVE -- the more you understand, the less
        the world lets you kill): below KING_GATE_EVIDENCE a clean shot
        KILLS a cultist; at/above it the round only STAGGERS. Costs one
        round. A round also drops any innocent LOCAL it hits -- always
        lethal, regardless of the evidence gate (the gate only ever
        protected the cult). The report is loud -- the cult hears it and
        investigates -- and a local kill spikes visibility besides."""
        p = self.player
        if (self.state != "playing" or p.hidden is not None
                or self.dialog.active or self.inv_ui.open
                or self.notebook_ui.open or self.text_input.active):
            return
        if not p.inventory.has("pistol") or self._gun_cd > 0:
            return
        if p.inventory.count("pistol_ammo") <= 0:
            self.audio.play("gun_dry", 0.5)
            self.show_notice("Empty. You need cartridges.", duration=1.4)
            self._gun_cd = GUN_CD
            return
        self._gun_cd = GUN_CD
        # Firing braces the camera: the body-chase stays locked for a
        # beat so the view cannot swing mid-shot (see _update_look).
        self._chase_lock_t = CHASE_FIRE_LOCK
        p.inventory.remove("pistol_ammo", 1)
        fx, fy = p.facing
        proj = Projectile(p.x + fx * 16, p.y + fy * 16, fx, fy,
                          dmg=GUN_DMG, color=GUN_PROJECTILE_COLOR,
                          speed=GUN_PROJECTILE_SPEED)
        proj.friendly = True
        # The gun is no longer cult-only: a round drops any living person
        # in its path, cultist or innocent local. Putting a local down is
        # lethal and loud, and the cult takes a hard interest (handled in
        # _kill_npc: a visibility spike + an investigate ping at the body).
        proj.cult_only = False
        # A round also puts down a Watcher of the curse in the line of fire
        # (they're real to the cursed). Fast + loud + costs the round.
        if self._cursed and self._watchers:
            self._dispel_watcher_in_line(p, fx, fy)
        proj.stun_only = (self._evidence_count() >= KING_GATE_EVIDENCE)
        proj.stun_dur = GUN_STUN_DUR
        self.scene.projectiles.append(proj)
        p.melee_swing_t = AXE_SWING_DUR             # brief recoil/muzzle tell
        p.melee_dir = p.facing
        self.audio.play_in_scene("gunshot", 0.85)
        self.audio.duck(0.9, depth=0.35)            # let the report own the air
        # A gunshot is loud -- it re-tasks even searchers (NOISE_SEARCH_PULL).
        if self.scene is not None:
            self.scene.emit_noise(p.x, p.y, 1.0, kind="shot")
        # One-time teach about the evidence gate the first time it staggers.
        if proj.stun_only and not self.save.flag("gun_stun_taught"):
            self.save.set_flag("gun_stun_taught", True)
            self.show_notice("The shot barely staggers it now. You know too "
                             "much. They won't die for you anymore.",
                             duration=3.0)

    def _active_weapon(self):
        """The single slot the gun and axe SHARE. Returns the equipped weapon
        key if still carried, else auto-latches one the player owns (gun
        preferred). None if unarmed."""
        inv = self.player.inventory
        w = inv.equipped.get("weapon")
        if w and inv.has(w):
            return w
        w = ("pistol" if inv.has("pistol")
             else "lumber_axe" if inv.has("lumber_axe") else None)
        inv.equipped["weapon"] = w
        return w

    def _use_weapon(self):
        """The main action button (left-click): use the equipped weapon."""
        w = self._active_weapon()
        if w == "pistol":
            self.player_fire_gun()
        elif w == "lumber_axe":
            self.player_axe_swing()

    def _kill_npc(self, npc):
        """Side-effects of an NPC kill: increment the kill counter (the
        substrate watches this), play the death SFX, drop any items the
        NPC was carrying, and fire on_kill if present.

        Returns True if the body should PERSIST as a corpse (an innocent
        local you put down), False if it should be swept away as before
        (a cultist -- the cult reclaims its own). A local kill also drops
        an investigate ping at the body and spikes visibility: the town
        turns its head toward what you just did."""
        pan = self.audio.pan_for_world(npc.x, self.player.x)
        dmult = self.audio.distance_attenuation(npc.x, npc.y,
                                                self.player.x, self.player.y)
        self.audio.play("enemy_die", 0.55 * dmult, pan=pan)
        tag = getattr(npc, "tag", None)
        is_cult = ((isinstance(tag, str) and tag.startswith("cult_"))
                   or getattr(npc, "sprite_kind", None) == "cultist")
        arg = "enemy_kills" if is_cult else "nonhostile_kills"
        self.save.set_arg(arg, self.save.arg(arg, 0) + 1)
        for drop in getattr(npc, "drops", []):
            self.scene.items.append({
                "x": npc.x + random.uniform(-8, 8),
                "y": npc.y + random.uniform(-8, 8),
                "key": drop, "qty": 1,
            })
        ok = getattr(npc, "on_kill", None)
        if ok:
            try:
                ok(self)
            except Exception:
                pass
        if is_cult:
            # A downed cultist now STAYS as a body for as long as the player is
            # in the room (override of the old "the cult reclaims its own"
            # sweep). No visibility spike and no investigate ping -- those only
            # ever fired for an innocent local. Like a local's body it is not
            # persisted across scene loads; the scene rebuilds live on re-entry.
            return True
        # An innocent local. The cult reaction: a loud investigate ping at
        # the body and a hard visibility spike. The body stays down for
        # good: the kill is written to the dead-locals ledger and the body
        # is laid back down on every re-entry (_apply_dead_locals) -- dead
        # locals stay dead for the rest of the run (NARRATIVE §5 /
        # DESIGN.md §1).
        self.visibility = min(LOCAL_KILL_VIS_CAP,
                              max(self.visibility,
                                  self.visibility + LOCAL_KILL_VIS_SPIKE))
        if self.scene is not None:
            self.scene.emit_noise(npc.x, npc.y, 1.0, kind="body")
        self._record_dead_local(npc)
        return True

    def _make_corpse(self, npc):
        """Convert a just-killed local NPC into a corpse: it stops moving
        (alive=False already), stops blocking, and answers E with a flat
        examine instead of its old dialogue. An innocent local's corpse is
        also ledgered (_record_dead_local at the kill) and laid back down
        on every re-entry (NARRATIVE §5 / DESIGN.md §1: dead locals stay
        dead); a cultist's body lasts only the visit."""
        npc._is_corpse = True
        npc._kill_processed = True
        npc.solid = False
        npc.movement = "idle"
        npc.dialogue_fn = _corpse_examine
        npc.no_prompt = False

    def _record_dead_local(self, npc):
        """Write a killed local into the run's dead-locals ledger (save arg
        `dead_locals`): scene, resting position, and an identity the scene
        rebuild can be matched against (name first; the builder index from
        load_scene_now for the nameless). The office Sheriff is normalized
        to one identity so the watching "Sheriff" and the stage-3 hollow
        "Sheriff Vane" cannot both exist once either is dead."""
        if self.scene is None:
            return
        nm = getattr(npc, "name", "") or ""
        if nm == "Sheriff Vane":
            nm = "Sheriff"
        bi = getattr(npc, "_build_idx", None)
        if not nm and bi is None:
            return                      # dynamic + nameless: not ledgerable
        key = f"{self.scene.key}:{nm if nm else '#%d' % bi}"
        dead = self.save.arg("dead_locals", {}) or {}
        dead[key] = {"scene": self.scene.key,
                     "x": npc.x, "y": npc.y,
                     "name": nm, "idx": bi}
        self.save.set_arg("dead_locals", dead)

    def _local_is_dead(self, name):
        """True if a local with this ledgered name was killed this run."""
        dead = self.save.arg("dead_locals", {}) or {}
        return any(rec.get("name") == name for rec in dead.values())

    def _apply_dead_locals(self):
        """Re-lay the run's killed locals on scene load (dead locals stay
        dead, NARRATIVE §5): each ledgered body belonging to this scene
        finds its rebuilt NPC (by name, else by builder index), moves it
        to where it fell, and settles it back into a corpse. Runs BEFORE
        _apply_rot so the rot pass skips the dead."""
        dead = self.save.arg("dead_locals", {}) or {}
        if not dead or self.scene is None:
            return
        claimed = set()
        for rec in dead.values():
            if rec.get("scene") != self.scene.key:
                continue
            nm, bi = rec.get("name") or "", rec.get("idx")
            target = None
            for n in self.scene.npcs:
                if id(n) in claimed or getattr(n, "_is_corpse", False):
                    continue
                if nm:
                    if getattr(n, "name", "") == nm:
                        target = n
                        break
                elif bi is not None and getattr(n, "_build_idx", None) == bi:
                    target = n
                    break
            if target is None:
                continue                # rebuilt away (staged NPCs etc.)
            claimed.add(id(target))
            target.alive = False
            target.x = rec.get("x", target.x)
            target.y = rec.get("y", target.y)
            target._inside = False      # a dead homebody can't be indoors
            self._make_corpse(target)

    def _kill_enemy(self, e):
        """Run the death side-effects for `e`: marks dead, plays the
        death SFX, rolls drops (85% suppressed for respawning enemies),
        and fires on_kill. Called from melee and friendly-projectile
        paths so a pistol kill awards drops/on_kill the same way a
        sword kill does. Increments the kill counter, which the
        substrate references in late-game evidence files."""
        e.alive = False
        pan = self.audio.pan_for_world(e.x, self.player.x)
        dmult = self.audio.distance_attenuation(e.x, e.y,
                                                self.player.x, self.player.y)
        self.audio.play("enemy_die", 0.6 * dmult, pan=pan)
        kind = getattr(e, "kind", "")
        if kind == "wolf":
            arg = "animal_kills"
        else:
            arg = "enemy_kills"
        self.save.set_arg(arg, self.save.arg(arg, 0) + 1)
        # Respawning combat enemies (forest_path, cave, and
        # easter_egg_room mob sets) drop nothing 85% of the time.
        # First-spawn / boss / shadow drops bypass this rule -- they're
        # set respawning=False.
        skip_drops = (
            getattr(e, "respawning", False)
            and random.random() < 0.85
        )
        if not skip_drops:
            for drop in e.drops:
                self.scene.items.append({
                    "x": e.x + random.uniform(-8, 8),
                    "y": e.y + random.uniform(-8, 8),
                    "key": drop, "qty": 1,
                })
        if e.on_kill:
            try:
                e.on_kill(self)
            except Exception:
                pass
        # A downed cultist now leaves a BODY (override of the old vanish-on-
        # death; the cult no longer reclaims its own). Enemy cultists live in
        # scene.enemies and get swept on death, so synthesize a corpse NPC at
        # the spot -- the existing npc-corpse draw path renders it, and it is
        # NOT persisted across loads (the scene rebuilds live on re-entry).
        if kind == "cultist" and self.scene is not None:
            from entities.npc import NPC
            corpse = NPC(e.x, e.y, "A cultist", "cultist",
                         movement="idle", solid=False, no_prompt=True)
            # the body keeps the dead cultist's face (mask variant)
            corpse.sprite_seed = getattr(e, "sprite_seed",
                                         corpse.sprite_seed)
            corpse.alive = False
            corpse._is_corpse = True
            corpse._kill_processed = True
            self.scene.npcs.append(corpse)

    def _tick_delayed_audio(self, dt):
        """Drain the queued late-play SFX list. An entry is [t, name,
        vol] or [t, name, vol, pan]; t counts down each tick and the
        SFX plays when it reaches zero. The queue is short (current
        usage spawns at most one per 12 creepy-tile steps) so a linear
        scan is fine."""
        if not self._delayed_audio:
            return
        survivors = []
        for entry in self._delayed_audio:
            entry[0] -= dt
            if entry[0] <= 0:
                pan = entry[3] if len(entry) > 3 else None
                self.audio.play_in_scene(entry[1], entry[2], pan=pan)
            else:
                survivors.append(entry)
        self._delayed_audio = survivors

    _FB_GAZE = [(math.cos(a * math.tau / 8), math.sin(a * math.tau / 8))
                for a in range(8)] + [(0.0, 0.0)]

    # The PI's interior voice down the descent (NARRATIVE §8):
    # the put-together investigator coming apart as he understands too much,
    # baited toward the Mask's off-ramp (carry it OUT -- SPREAD). Each beat is
    # one-shot: a brief first-person flash on-screen, plus a fuller entry filed
    # to the case notebook. NOTES, never evidence -- they must not arm the
    # King-gate. §1b discipline: the door is never explained; the dread is all
    # sensation, and the Mask-certainty reads "the way you know a thing in a
    # dream" (the lure, never named).
    _DESCENT_VOICE = {
        # SURFACE -- the barn (Mara's, the cult's old quarters). The first
        # chalk door. Still the professional, mildly curious.
        "chalk_surface": {
            "beat": [
                "[c=dim]A door, chalked onto the floorboards. The size of a "
                "real one, and careful about it. A frame laid flat, like you "
                "could step down through it. ...Kids do stranger. I wrote it "
                "down anyway.[/c]",
            ],
            "note": [
                "Someone chalked a door onto the barn floor. Full size, and "
                "they weren't careless about it. Jambs, a lintel, even a knob. "
                "Drawn flat, like a thing you'd step down into. Around nothing. "
                "Bare plank under it.",
                "Could be a child. Doesn't read like a child. It reads like "
                "practice.",
                "Filing it. Probably nothing. I've filed nothing before and "
                "been wrong.",
            ],
        },
        # THE WORKS -- the Sorting Hall. NOT a chalk door: examining the
        # catalogued lives the diggers shed. The scale lands; first fear.
        "descent_dig": {
            "beat": [
                "[c=dim]Their whole lives, sorted and shelved down here. "
                "...My pen won't hold still. That's new.[/c]",
            ],
            "note": [
                "This is no cellar. It's a dig. Room after room of it, going "
                "down, and it cost them a year of hands.",
                "Everything they owned is catalogued in here. Coats, "
                "photographs, a child's shoe, folded. Set down neat, the way "
                "you leave a thing you mean never to need again.",
                "I've worked bad rooms. This is the first one to put a shake "
                "in my hands. I do not like how far down I am.",
            ],
        },
        # THE WORKS -- the drawn doors multiply, cruder, obsessive. Rattled,
        # and clinging to the way back up.
        "chalk_works": {
            "beat": [
                "[c=dim]Down here it's nothing but the drawn doors. Walls, "
                "floor, over each other. None of them open onto anything. They "
                "knew that. They kept drawing.[/c]",
            ],
            "note": [
                "The whole dig is papered in them. Chalk doors on chalk doors, "
                "hundreds, going down with the tunnel.",
                "Not one opens onto anything. They knew. You can see them "
                "pressing harder, trying to get it right, like the right one "
                "would finally come loose from the wall.",
                "I came down for a missing girl. I keep checking over my "
                "shoulder for the way back up. Still open. I say so to "
                "myself more than a steady man would.",
            ],
        },
        # The cult's testimony (The Calling): the SEED of the want-to-leave.
        # CANON (NARRATIVE §1/§6): this is the King's influence riding their
        # notes into the PI's head -- the pull to carry the Sign OUT and spread
        # Him. NEVER stated as His doing; felt only as a want he can't find the
        # start of (the §1b line -- he can't tell it isn't his own thought).
        "descent_leave": {
            "beat": [
                "[c=dim]You turn through the bound notes. Their own hands, "
                "page on page. ...You've got plenty here. More than plenty.[/c]",
                "[c=dim]A case this size, you don't keep digging it. You carry "
                "it up and let the people who can drop a roof on this town do "
                "the rest. Time to climb out.[/c]",
            ],
            "note": [
                "Read the bound one. Their own notes. There's enough in this "
                "town to hang it twice over. Past enough.",
                "No call to go deeper. You don't work a case past the point "
                "it's made. You bring it up to the ones who can finish it.",
                "Climb out. Make the call. Let the law come down on Brimley "
                "like a roof. That's the job. [c=dim]That's always been the "
                "job.[/c]",
            ],
        },
        # The Mask: THE TEMPTATION. With this, the town lets me out -- the lie
        # that dresses Spread up as duty and rest. (The want the notes seeded,
        # now handed the means.)
        "descent_mask": {
            "beat": [
                "[c=dim]His face, in your hands. Light as folded paper, cold, "
                "and it knows your grip.[/c]",
                "[c=dim]The pale mask hums in your hand.[/c]",
                "[c=dim]And you KNOW it, the way you know a thing in a dream. "
                "Carry this, and the town opens. The roads let you out.[/c]",
                "[c=dim]The names, the register, the girl her father wanted "
                "found. You have enough. You could be in the car by morning. "
                "You could just go.[/c]",
            ],
            "note": [
                "I have the mask off the altar. His face. Pale as a drowned "
                "man, cold, light as paper.",
                "And I'm sure of a thing I've no right to be sure of. This is "
                "the way out. Whoever carries it, the town lets go.",
                "I have enough for any court that would hear me. I could climb "
                "out and never look down again.",
                "I want to. God help me, I want to. I'm setting it down here "
                "so I remember that I did.",
            ],
        },
        # THE DEPTHS -- past the point of no return. Panic; the doors in his
        # head now. The put-together man, gone.
        "chalk_deep": {
            "beat": [
                "[c=dim]The drawn doors are behind my eyes now, every time I "
                "shut them. Everything in me is pulling for the surface. "
                "The way back is shut. So down.[/c]",
            ],
            "note": [
                "The stair shut the way behind me when it opened. No way back "
                "up. Only down now.",
                "Everything in me is pulling for the surface. The car, the "
                "road, the county line. And there is nothing left to climb. So "
                "I go down, because down is the only direction left.",
                "I shut my eyes and the chalk doors are still there, drawn on "
                "the inside of them. I could draw one from memory now. [c=dim]I "
                "don't want to know that about myself.[/c]",
            ],
        },
    }

    def _try_chalk_interact(self):
        """E on a chalk door (registered via Scene.add_chalk_door). The FIRST
        examined in a scene that set `_chalk_voice` fires that interior-voice
        beat; any other chalk door gives a brief flat line. Returns True if a
        chalk door was examined (so try_interact stops)."""
        doors = getattr(self.scene, "_chalk_doors", None)
        if not doors:
            return False
        if not any(abs(self.player.x - cx) < 40 and abs(self.player.y - cy) < 40
                   for cx, cy in doors):
            return False
        self.audio.play("confirm", 0.5)
        voice = getattr(self.scene, "_chalk_voice", None)
        if voice and not self.save.flag(f"voice_{voice}"):
            self._descent_voice(voice)
        return True

    # ---- Endings ----

    # Ending scripts. Each is a list of (line, duration_seconds).
    # escape_alone is the SPREAD IT ending -- the drive-out CUTSCENE (the
    # claiming, lines locked 2026-06): the engine answers the mask, the
    # mask turns in the passenger seat, the PI answers the gaze his one
    # dream broke off a year ago, and what he longed for most -- to FEEL
    # -- floods in as he crosses out. The visuals live in
    # rendering/spread_drive.py; the durations come from its beat table
    # so the captions and the picture can never drift. seal_threshold
    # (END IT) closes the Threshold on Brimley and on you (NARRATIVE §8).
    _ENDING_SCRIPTS = {
        "escape_alone": list(zip((
            "You turn the key and the engine roars to life.",
            "You drive down the highway further than you could before, "
            "and near the edge of Brimley.",
            "The mask shifts in the seat, as if to look at you.",
            "You gaze into the mask's deep sunken eyes.",
            "And for the first time in twenty years, you feel. All of it, "
            "all at once. You have to stop the car because you are "
            "laughing, or weeping. You can't tell. You don't care. "
            "It's back.",
            "When you drive on, your hands are steady and the road south "
            "is wide open. For the first time in your life, you know "
            "exactly where you are going.",
            "Everyone will know.",
        ), SPREAD_BEAT_DURS)),
        # The approved SEAL text (2026-06). It plays AFTER the live warp
        # (the threshold scene pours through the doorframe around you,
        # scenes/depths.py) and hands off to the wordless wide-shot
        # tableau (the final empty line; draw_seal_tableau).
        "seal_threshold": [
            ("You stood at the Threshold and held the Mask out before "
             "you. You took the step.", 3.4),
            ("The moment it crossed, you were pulled through with it. "
             "And Brimley came after, every acre.", 3.6),
            ("The sky holds black stars. The twin suns peek at the "
             "horizon.", 3.2),
            ("You look up as the door slams shut.", 3.0),
            ("Rage approaches.", 3.4),
            ("", 8.0),
        ],
        # rite_broken is the TRAP game over (NARRATIVE §8). PURELY VISUAL --
        # no text boxes -- and two beats the draw path special-cases: the
        # mask-yank (the culpable act, RITE_YANK_DUR) cutting to the Carcosa
        # blast (RITE_BLAST_DUR).
        "rite_broken": [("", 3.0 + 7.0)],
    }

    def _tick_wake_muffle(self, dt):
        """Opening wake-state. While `_wake_muffle_t` is positive the
        music channel is dimmed and a slow heartbeat SFX pulses
        underneath -- the world heard through a head that's still
        clearing. Both fade out over the duration. Cleanly ends with
        the music channel restored to full volume so nothing else
        downstream notices the dampening was ever there."""
        if self._wake_muffle_t <= 0:
            return
        self._wake_muffle_t = max(0.0, self._wake_muffle_t - dt)
        progress = self._wake_muffle_t / max(0.001, self._wake_muffle_max)
        # Music: 0.30 at full muffle, 1.0 when clear. Curve so the
        # last second or two opens out audibly rather than linearly.
        target_vol = 0.30 + 0.70 * (1.0 - progress * progress)
        ch = getattr(self.audio, "music_channel", None)
        if ch is not None:
            try:
                ch.set_volume(target_vol)
            except Exception:
                pass
        # Heartbeat: a slow pulse, ~0.85s apart while muffled deep,
        # widening as the head clears. Stops entirely below 0.15
        # progress -- the last second is just the music opening up.
        if progress > 0.15:
            self._wake_heartbeat_t -= dt
            if self._wake_heartbeat_t <= 0:
                interval = 0.85 + (1.0 - progress) * 0.6
                self._wake_heartbeat_t = interval
                # Volume tracks the muffle: louder while deep,
                # dimmer as it clears.
                self.audio.play("heartbeat", 0.20 + 0.30 * progress)
        # Cleanup: when we just hit zero, restore music channel to
        # full so no other code has to know we were touching it.
        if self._wake_muffle_t == 0.0 and ch is not None:
            try:
                ch.set_volume(1.0)
            except Exception:
                pass

    def _tick_sprint(self, dt, keys):
        """Resolve sprint state per frame. SHIFT held + cooldown <= 0
        + sprint_t > 0 = active; otherwise idle. Active sprint drains
        sprint_t. Empty sprint kicks the cooldown. Released SHIFT
        ends the active sprint immediately. Sprinting also fires a
        louder phantom-step ambient -- the Pursuer hears the player
        running.

        Sprint also raises Pursuer proximity by 0.05 per second of
        sprinting (the Ire knows when you panic).

        OPENING GATE: sprint is silently disabled while the player
        is still in the spare room on their first session. The
        head-pounding wake state has to feel physically heavy --
        running undercuts the disorientation. Cleared the moment
        they leave the bedroom for the first time
        (begin_transition sets `left_bedroom`)."""
        p = self.player
        if (self.scene is not None
                and self.scene.key == "bedroom"
                and not self.save.flag("left_bedroom")):
            if p.sprint_active:
                p.sprint_active = False
            return
        shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        # Winded lockout drain (only entered on a FULL depletion). Counts
        # down regardless of input; clearing it restores full wind.
        if p.sprint_cd > 0:
            p.sprint_cd -= dt
            if p.sprint_cd <= 0:
                p.sprint_cd = 0.0
                p.sprint_t = p.sprint_t_max   # caught your breath
        # Sprint logic
        if shift_held and p.sprint_cd <= 0 and p.sprint_t > 0:
            if not p.sprint_active:
                p.sprint_active = True
            p.sprint_t -= dt
            # Periodic loud step every ~0.35s.
            self._sprint_step_t = getattr(self, "_sprint_step_t", 0.0) - dt
            if self._sprint_step_t <= 0:
                self._sprint_step_t = 0.35
                self.audio.play("phantom_step", 0.55)
            if p.sprint_t <= 0:
                p.sprint_t = 0.0
                p.sprint_active = False
                p.sprint_cd = p.sprint_cd_max   # blown -> winded lockout
        else:
            if p.sprint_active:
                p.sprint_active = False
            # Regenerate wind whenever not actively sprinting and not in
            # the winded lockout -- the meter recovers on its own, so a
            # short burst no longer costs a full cooldown wait.
            if p.sprint_cd <= 0 and p.sprint_t < p.sprint_t_max:
                p.sprint_t = min(p.sprint_t_max,
                                 p.sprint_t + dt * p.sprint_regen)

    def _tick_heartbeat(self, dt):
        """Player-state heartbeat. Above proximity 0.70 and while the
        player is not hidden, schedule a single low heartbeat pulse on
        a period that shortens as the line tightens. Hide-spots break
        the schedule (the player held still; their pulse drops). Cued
        regardless of scene -- this is the body, not the room."""
        if self.scene is None or self.player is None:
            return
        if self.state != "playing":
            return
        prox = self.visibility
        if prox < 0.70 or self.player.hidden is not None:
            self._heartbeat_t = 0.0
            return
        self._heartbeat_t -= dt
        if self._heartbeat_t > 0:
            return
        # Period: 5.0s at 0.70, ~1.2s at 0.95+. Linear in (prox - 0.70).
        t = max(0.0, min(1.0, (prox - 0.70) / 0.25))
        self._heartbeat_t = 5.0 - t * 3.8
        self.audio.play("heartbeat", 0.40 + prox * 0.30)
        # As the King-spawn threshold (1.0) closes in, duck the music
        # so each beat lands cleanly. Depth ramps with proximity: a
        # subtle 0.65 at the prox=0.85 entry point, hardening to 0.30
        # when the player is about to lose. Half a beat's worth of
        # duck so the gap re-closes between heartbeats.
        if prox > 0.85:
            depth = 0.65 - 0.35 * max(0.0, min(1.0, (prox - 0.85) / 0.15))
            self.audio.duck(self._heartbeat_t * 0.6, depth=depth)

    def _tick_cult_ambient(self, dt):
        """Reactive cult-rite audio bed. In CULT_AMBIENT_SCENES, the
        closest cultist's distance drives a swelling layer of
        cult_breath + cult_chant. The breath layer engages from ~280px
        in; the chant layer only kicks in when a cultist is within
        ~140px (close enough that you hear the work itself, not just
        the room). Both pan from the closest cultist's world-x. Silent
        when no cultist is in earshot -- the layer should never compete
        with the existing fire-and-forget _ambient cues, only ride
        underneath them when a cultist is nearby.

        Uses _breath_t and _chant_t, which were declared in __init__
        and reset by _reset_run_state but never actually wired."""
        if (self.scene is None or self.player is None
                or self.scene.key not in CULT_AMBIENT_SCENES):
            return
        closest = None
        cd = 1e9
        for e in self.scene.enemies:
            if not e.alive:
                continue
            d = math.hypot(e.x - self.player.x, e.y - self.player.y)
            if d < cd:
                cd = d
                closest = e
        if closest is None:
            return
        # Breath: audible from BREATH_FAR (~280px) down to BREATH_NEAR
        # (~60px). Closer = louder + more frequent.
        BREATH_FAR = 280.0
        BREATH_NEAR = 60.0
        if cd >= BREATH_FAR:
            self._breath_t = 5.0
            self._chant_t = 9.0
            return
        nearness = max(0.0, min(1.0,
                                (BREATH_FAR - cd) / (BREATH_FAR - BREATH_NEAR)))
        self._breath_t -= dt
        if self._breath_t <= 0:
            # Period: 5.0s far -> 1.2s near (with +/- 20% jitter so the
            # bed never feels metronomic).
            period = (5.0 - 3.8 * nearness) * random.uniform(0.8, 1.2)
            self._breath_t = period
            pan = self.audio.pan_for_world(closest.x, self.player.x)
            self.audio.play("cult_breath", 0.10 + 0.20 * nearness, pan=pan)
        # Chant only at close range -- the player is standing next to
        # someone doing the work.
        CHANT_NEAR = 140.0
        if cd > CHANT_NEAR:
            self._chant_t = 9.0
            return
        chant_t = max(0.0, min(1.0,
                               (CHANT_NEAR - cd) / (CHANT_NEAR - BREATH_NEAR)))
        self._chant_t -= dt
        if self._chant_t <= 0:
            self._chant_t = (9.0 - 5.5 * chant_t) * random.uniform(0.8, 1.2)
            pan = self.audio.pan_for_world(closest.x, self.player.x)
            self.audio.play("cult_chant", 0.12 + 0.16 * chant_t, pan=pan)
            # Duck the depths music so the chant carries. Depth scales
            # with proximity -- a close chant ducks harder. The 2.7s
            # window covers the chant's reverb tail (cult_chant is
            # 1.8s dry + ~0.9s cellar tail).
            self.audio.duck(2.7, depth=0.40 - 0.20 * chant_t)

    def _flashlight_lit(self):
        """Is the flashlight actually casting a beam right now? True only
        when the player carries it, has it switched on, and stands in a
        DARK scene that isn't cult-dark (the deep cult sites swallow any
        ordinary light -- the dread aperture rules there instead)."""
        if self.player is None or self.scene is None:
            return False
        if not self.flashlight_on:
            return False
        if not self.player.inventory.has("flashlight"):
            return False
        if self.scene.key not in DARK_SCENES:
            return False
        if self.scene.key in CULT_DARK_SCENES:
            return False
        return True

    def _toggle_flashlight(self):
        """[F]: flip the flashlight. Refuses (with feedback) if the player
        has no light, and warns -- once -- that the deep dark eats the beam
        in cult-dark scenes."""
        if self.player is None:
            return
        if not self.player.inventory.has("flashlight"):
            self.audio.play("bump", 0.4)
            self.show_notice("You have no light.", duration=1.6)
            return
        self.flashlight_on = not self.flashlight_on
        self.audio.play("blip_low" if self.flashlight_on else "bump", 0.6)
        if (self.flashlight_on and self.scene is not None
                and self.scene.key in CULT_DARK_SCENES):
            self.show_notice("The beam dies the moment it leaves the lens. "
                             "The dark here is not the kind light fixes.",
                             duration=2.6)
        elif (self.flashlight_on and self.scene is not None
                and self.scene.key not in DARK_SCENES):
            # A lit room: the beam does nothing here (it only bites in the
            # dark), so tell the player rather than click a dead switch.
            self.show_notice("Bright enough here without it.", duration=1.8)

    # ---- Step ----
    def step(self, dt):
        keys = pygame.key.get_pressed()
        self.title_t += dt
        if self.state == "playing":
            # Death screen holds the world frozen until it resolves
            # (respawn or title). Tick it alone and skip the sim.
            if self._death_kind is not None:
                self._tick_death(dt)
                return
            self._notebook_toast_t = max(0.0, self._notebook_toast_t - dt)
            self.update_player(dt, keys)
            # Any open modal (dialogue, inventory, notebook, text prompt)
            # FREEZES the world sim: NPC patrols, enemies, projectiles and
            # the whole threat model hold still. Otherwise a dialogue box
            # turned the player into a sitting duck -- cultists kept closing
            # in and visibility kept rising while they could only read.
            world_frozen = (self.dialog.active or self.inv_ui.open
                            or self.notebook_ui.open
                            or self.text_input.active
                            # The door-dream (flash or rite) freezes the
                            # sim: nothing closes in while the PI is inside
                            # the memory.
                            or self._flashback_phase is not None
                            # A close-up examine tableau freezes the world too.
                            or self._tableau is not None)
            # Evidence-gated corruption: cultists only bloom into His maw
            # once you understand too much (3+ evidence). Read by the
            # cultist AI when it locks on (enemy._cult_tick / npc chaser).
            if self.scene is not None:
                # Arm blooms once the FIRST cultist of the run has been met
                # human (a chaser sets _bloom_arm_pending on the scene): the
                # first-ever cultist is introduced mundane, every one after
                # it erupts (play-notes: the "100 eyes on my first cultist"
                # break). The pending flag is per-scene/frame; the armed
                # state is a run save-flag so it survives scene loads.
                if getattr(self.scene, "_bloom_arm_pending", False):
                    self.save.set_flag("bloom_armed", True)
                self.scene._bloom_enabled = (
                    self._evidence_count() >= KING_GATE_EVIDENCE)
                self.scene._bloom_armed = self.save.flag("bloom_armed")
            if not world_frozen:
                exit_data = self.scene.find_exit_at(
                    self.player.x, self.player.y,
                    facing=self.player.facing)
                if exit_data:
                    exit_ch = self.scene.char_object_at(
                        self.player.x, self.player.y)
                    # A scene may GATE an exit on game state (the grove's
                    # descent fold opens only at 3 evidence; the school door
                    # only once drawn). A gated-shut exit reads as floor.
                    gate = getattr(self.scene, "exit_gate_fn", None)
                    if gate is not None and not gate(self, exit_ch):
                        exit_data = None
                if exit_data:
                    # Stash a hot pursuer so an active chase carries through
                    # this exit -- portal or fold alike (only a SAFE room
                    # shakes it). The far side rebuilds it a beat behind.
                    self._note_fold_pursuit(exit_data)
                    # The roaming King follows the player scene-to-scene through
                    # his own ground (passages/folds), but never through a door.
                    self._note_king_follow(exit_data)
                    # A fold/portal traversal has a 1/20 chance to bind +1
                    # Watcher (the seed that starts the curse cloning), unless
                    # already at the 5-Watcher ceiling.
                    self._roll_fold_watcher(exit_data)
                    # A direction-gated exit IS a fold: it crosses seamlessly
                    # whatever scenes it joins (the grove's way down, the
                    # school door). Everything else keeps the set-membership
                    # routing in begin_transition (seamless passages vs the
                    # door fade).
                    if exit_ch in self.scene.exit_directions:
                        self.cross_fold(*exit_data, is_rift=True)
                    else:
                        # The leaf swings as you go through (tilt view).
                        # quiet: begin_transition plays its own
                        # door_open, so the swing must not double it.
                        self._pulse_door_at(self.player.x, self.player.y,
                                            quiet=True)
                        # A SEE-THROUGH door crosses seamlessly (cross_fold, no
                        # fade) since the far room was already in view; a plain
                        # door keeps the fade. Both run the same door gates.
                        seethrough = exit_ch in (
                            self.scene.seethrough_doors or ())
                        self.begin_transition(*exit_data, seamless=seethrough)
            # Suspend scene update (NPC patrols, decoration anims, triggers)
            # while any modal is up so the world freezes behind it.
            if not world_frozen:
                # Stamp darkness-concealment BEFORE the cult ticks run
                # (NPC updates inside scene.update + the enemy loop
                # below both read player._in_dark through the shared
                # concealment_factor).
                self._tick_dark_cover()
                self.scene.update(dt, self)
            self.text_input.update(dt)
            for e in list(self.scene.enemies):
                if not world_frozen:
                    e.update(dt, self.scene, self.player)
                    if e.just_shot and e.shoot_sfx:
                        pan = self.audio.pan_for_world(e.x, self.player.x)
                        dmult = self.audio.distance_attenuation(
                            e.x, e.y, self.player.x, self.player.y)
                        self.audio.play(e.shoot_sfx, 0.55 * dmult, pan=pan)
                if not e.alive:
                    self.scene.enemies.remove(e)
            # A scene-placed cultist (the Works gauntlet uses Enemy-class
            # cultists, not the threat-system NPCs) reaching the player
            # TAKES them -- the same CAPTURED end the town cultists trigger.
            # Without this those cultists just chased and did nothing, so
            # capture felt random ("some take me, some don't"). Enclosed
            # hides / invuln / mid-death are exempt, matching
            # _tick_cultists -- one gate for every grab site
            # (systems/stealth.py grab_allowed; the loop below requires
            # chase state, so concealment yields to a locked pursuer).
            if (not world_frozen and self._death_kind is None
                    and _grab_ok(self.player, True)
                    and self.player.invuln <= 0):
                for e in self.scene.enemies:
                    # Only an AWARE cultist (actively chasing) takes you --
                    # the oblivious kneelers at the Sign Chamber altar
                    # (aggro 0) never enter "chase", so you can still sneak
                    # past them to lift the Mask.
                    if (e.alive and e.kind == "cultist"
                            and getattr(e, "_cult_state", "") == "chase"
                            and math.hypot(e.x - self.player.x,
                                           e.y - self.player.y) < 22):
                        self._trigger_death("cultist")
                        break
            # Tick projectiles AFTER enemies so a brand-new shot doesn't
            # also move on the same frame it was fired (cleaner travel).
            if not world_frozen:
                for p in list(self.scene.projectiles):
                    p.update(dt, self.scene, self.player)
                    if p.hit:
                        pan = self.audio.pan_for_world(p.x, self.player.x)
                        dmult = self.audio.distance_attenuation(
                            p.x, p.y, self.player.x, self.player.y)
                        self.audio.play("hit", 0.55 * dmult, pan=pan)
                    if not p.alive:
                        self.scene.projectiles.remove(p)
                # Sweep any enemy a projectile flagged dead. (The melee
                # swing only STUNS -- it never deals damage -- so this is
                # the sole kill path.)
                for e in self.scene.enemies:
                    if e.alive and e.hp <= 0:
                        self._kill_enemy(e)
                # Sweep dead NPCs. Fire kill side-effects exactly once per
                # NPC. A cultist is removed (the cult reclaims its own); an
                # innocent local is left as a persistent corpse on the floor.
                for n in list(self.scene.npcs):
                    if getattr(n, "alive", True):
                        continue
                    if getattr(n, "_is_corpse", False):
                        continue        # already a settled corpse
                    if not getattr(n, "_kill_processed", False):
                        n._kill_processed = True
                        if self._kill_npc(n):
                            self._make_corpse(n)
                            continue     # keep the body in the scene
                    self.scene.npcs.remove(n)
            self._update_camera()
            self._update_look(dt)
            self.audio.update_silence()
            self.audio.update_duck()
            self.dialog.update(dt)
            # Floating NPC speech reveals + auto-advances with the world
            # (it IS the non-modal path; it pauses when a modal freezes
            # the world, same as everything else).
            if not world_frozen:
                self.float_speech.update(dt, self)
                self.narration.update(dt)
            self._tick_delayed_audio(dt)
            # The threat model is part of the world sim -- it freezes behind
            # a modal too, so visibility can't climb and the King can't close
            # while a box is up. Cutscene/audio drivers keep running.
            if not world_frozen:
                # Advance the noise channel's SIM clock (event
                # freshness + mask expiry key to it; it freezes with
                # the world behind modals).
                if self.scene is not None:
                    self.scene._noise_now += dt
                self._tick_bell(dt)
                self._trip_noise_traps(dt)
                self._tick_noise_sources(dt)
                self._tick_doors(dt)
                self._tick_bleed(dt)
                self._tick_cultists(dt)
                self._tick_moths(dt)
                self._tick_moth_shed(dt)
                self._tick_moth_seek(dt)
                self._tick_struggle(dt)
                self._tick_chase_cues_enemies(dt)
                self._tick_fold_pursuit(dt)
                self._tick_sheriff(dt)
                self._tick_watchers(dt)
                self._tick_visibility(dt)
                self._tick_heartbeat(dt)
                self._tick_cult_ambient(dt)
                self._tick_king_roam(dt)
            self._tick_wake_muffle(dt)
            self._tick_ashfall(dt)        # atmosphere: drifts behind modals too
            self._tick_flashback(dt)
            self._tick_tableau(dt)
            self._tick_ending(dt)
        elif self.state == "transition":
            self.transition_t += dt
            # THRESHOLD: transitions are slow on purpose. Every door
            # holds the screen black for 0.85s out and 0.85s in --
            # the player feels the threshold resist. The longer-than-
            # expected fade is the room not quite letting them go.
            out_dur = 0.85
            in_dur = 0.85
            if self.transition_dir == "out":
                if self.transition_t >= out_dur:
                    target, spawn = self.transition_target
                    self.load_scene_now(target, spawn)
                    self.transition_dir = "in"
                    self.transition_t = 0.0
                    self.audio.play("door_close", 0.6)
            else:
                if self.transition_t >= in_dur:
                    self.state = "playing"
        elif self.state == "opening":
            self._tick_opening(dt)
        if self.notice_text:
            self.notice_t -= dt
            if self.notice_t <= 0:
                self.notice_text = None

    def _flash_notebook(self, name=None):
        """Fire the corner notebook-scribble toast -- something was just
        written to the case book (a clue or a note), the PI jotting it down.
        `name` is the beat's save slug; the toast titles the card with it so
        the player knows what got recorded and can go read it in the book."""
        self._notebook_toast_t = NOTEBOOK_TOAST_DUR
        self._notebook_toast_name = name

    def show_notice(self, text, duration=2.5):
        self.notice_text = text
        self.notice_t = duration

    # The control reference shown on the pause "Controls" screen. Mirrors
    # the live bindings in handle_event / _tick_sprint / try_interact. The
    # weapon is used with left-click and SWITCHED from the inventory (the
    # gun and axe share one slot) -- there are no K/Q keys.
    CONTROLS_REFERENCE = [
        ("Move",                "WASD / Arrow keys"),
        ("Sprint",              "Hold Shift"),
        ("Interact / Hide",     "E  (or Space)"),
        ("Use weapon",          "Left-click"),
        ("Switch weapon",       "Equip it in the Inventory"),
        ("Flashlight",          "F  (in the dark)"),
        ("Casebook (tools)",    "I"),
        ("Casebook (notes)",    "N"),
        ("Pause / Back",        "Esc"),
        ("Fullscreen",          "F11"),
        ("Save",                "Sleep at the cot"),
    ]

    def pause_input(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        if self.pause_view == "controls":
            if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_e,
                          pygame.K_SPACE):
                self.pause_view = "menu"
                self.audio.play("menu_close", 0.6)
            return
        if self.pause_view == "settings":
            self._settings_input(ev)
            return
        if ev.key in (pygame.K_UP, pygame.K_w):
            self.pause_choice = (self.pause_choice - 1) % len(self.pause_options)
            self.audio.play("cursor", 0.6)
        elif ev.key in (pygame.K_DOWN, pygame.K_s):
            self.pause_choice = (self.pause_choice + 1) % len(self.pause_options)
            self.audio.play("cursor", 0.6)
        elif ev.key == pygame.K_ESCAPE:
            self.state = "playing"
            self.audio.play("menu_close", 0.6)
        elif ev.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
            opt = self.pause_options[self.pause_choice]
            if opt == "Resume":
                self.state = "playing"
                self.audio.play("menu_close", 0.6)
            elif opt == "Controls":
                self.pause_view = "controls"
                self.audio.play("menu_open", 0.6)
            elif opt == "Settings":
                self.pause_view = "settings"
                self.settings_choice = 0
                self.audio.play("menu_open", 0.6)
            elif opt == "Quit to Title":
                # No autosave: the cot is the only save point.
                # Anything done since the last sleep is lost when
                # the player walks away. The pause menu warns by
                # not pretending otherwise.
                self.state = "title"
                # Back to the title drone -- the same wind-and-tritone
                # the player heard on launch.
                self.audio.play_music("threshold_drone")

    def _settings_input(self, ev):
        if ev.key == pygame.K_ESCAPE:
            self.pause_view = "menu"
            self.audio.play("menu_close", 0.6)
            return
        if ev.key in (pygame.K_UP, pygame.K_w):
            self.settings_choice = (self.settings_choice - 1) % 3
            self.audio.play("cursor", 0.6)
        elif ev.key in (pygame.K_DOWN, pygame.K_s):
            self.settings_choice = (self.settings_choice + 1) % 3
            self.audio.play("cursor", 0.6)
        elif ev.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            step = 0.1 if ev.key in (pygame.K_RIGHT, pygame.K_d) else -0.1
            which = ("master", "music", "sfx")[self.settings_choice]
            cur = (self.audio.master_vol, self.audio.music_vol,
                   self.audio.sfx_vol)[self.settings_choice]
            self.audio.set_volumes(**{which: cur + step})
            # A quiet blip so the SFX/master change is audible at the new level.
            self.audio.play("cursor", 0.6)

    # ---- Events / main loop ----
    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            # No autosave on window close. Save lives at the cot.
            pygame.quit(); sys.exit(0)
        if self.state == "title":
            self.title_input(ev); return
        if self.state == "paused":
            self.pause_input(ev); return
        if self.state == "opening":
            # A passive cutscene: only ESC skips it (silent, no on-screen
            # tell). The stalls coast and the engine catches on their own
            # timer in _tick_opening -- no key-press is asked of the player.
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self._end_opening()
            return
        # THRESHOLD: during the closure sequence, only allow advancing
        # the dialog. Everything else (movement, interaction, save,
        # pause, inventory) is locked. The player cannot escape the
        # ending by hitting ESC.
        if getattr(self, "_closure_locked", False):
            if self.dialog.active and ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                    self.dialog.advance()
            return
        if self.text_input.active:
            # Modal owns all input while active. It swallows the event.
            self.text_input.handle_event(ev)
            return
        if self.journal_ui.open:
            # One book: left/right turns the tab (Case | Tools | Papers),
            # up/down walks the index, Enter reads or takes in hand. I jumps
            # to the Tools ribbon, N to the Case ribbon (pressing the ribbon
            # you're already on closes the book), Esc always closes.
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.journal_ui.toggle()
                elif ev.key == pygame.K_i:
                    self.journal_ui.open_to(JOURNAL_TOOLS_TAB)
                elif ev.key == pygame.K_n:
                    self.journal_ui.open_to(JOURNAL_CASE_TAB)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    self.journal_ui.move(-1)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.journal_ui.move(1)
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    self.journal_ui.change_tab(-1)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    self.journal_ui.change_tab(1)
                elif ev.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
                    self.journal_ui.use_selected(self.player)
            return
        if self._tableau is not None:
            # A close-up examine tableau owns all input while it is up: the
            # menu cursor, selecting, reading, and walking away to close.
            self._tableau_input(ev)
            return
        if self.state in ("playing", "transition"):
            if ev.type == pygame.KEYDOWN:
                # The hide-check struggle owns E/SPACE while it runs: each
                # press is a wrench against the hands reaching in. Enough
                # presses inside the window tears the player free
                # (_struggle_win); the timer running out is the grab.
                if getattr(self, "_struggle", None) is not None:
                    if ev.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                        self._struggle["presses"] += 1
                        self.audio.play("bump", 0.35)
                        if self._struggle["presses"] >= STRUGGLE_PRESSES:
                            self._struggle_win()
                    return
                # Post-win swallow: the player is still mashing when the
                # struggle resolves -- a stray E must not re-enter the
                # hide they just tore out of.
                if (getattr(self, "_post_struggle_t", 0.0) > 0.0
                        and ev.key in (pygame.K_e, pygame.K_SPACE,
                                       pygame.K_RETURN)):
                    return
                if self.dialog.active:
                    if ev.key in (pygame.K_UP, pygame.K_w):
                        self.dialog.move_choice(-1)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        self.dialog.move_choice(1)
                    elif ev.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                        # If the player is currently hidden and a dialog
                        # interrupts (e.g. a Pursuer evidence beat), the
                        # first E press unhides them rather than advancing
                        # the dialog -- otherwise they can be permanently
                        # trapped in cover by an unrelated notice.
                        if self.player.hidden is not None:
                            self.try_interact()
                        else:
                            self.dialog.advance()
                    return
                if ev.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                    self.try_interact()
                elif ev.key == pygame.K_i:
                    self.journal_ui.open_to(JOURNAL_TOOLS_TAB)
                elif ev.key == pygame.K_n:
                    self.journal_ui.open_to(JOURNAL_CASE_TAB)
                elif ev.key == pygame.K_f:
                    self._toggle_flashlight()
                elif ev.key == pygame.K_F5:
                    # The cot is the only save point. F5 used to
                    # write a snapshot from anywhere; that lifted
                    # the horror of the bed-as-typewriter rule.
                    # Tell the player so the lesson lands once.
                    self.audio.play("bump", 0.4)
                    self.show_notice("Sleep at the cot to save.",
                                      duration=2.0)
                elif ev.key == pygame.K_F11:
                    self._toggle_fullscreen()
                elif ev.key == pygame.K_F1:
                    self._show_fps = not self._show_fps
                elif ev.key == pygame.K_F2:
                    self._cycle_render_scale()
                elif ev.key == pygame.K_ESCAPE:
                    self.state = "paused"
                    self.pause_view = "menu"
                    self.pause_choice = 0
                    self.audio.play("menu_open", 0.6)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Left-click is the only action button: use whatever weapon
                # is in hand -- fire the revolver or swing the axe.
                self._use_weapon()
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                pass

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            self._last_dt = dt
            self.frame_count += 1
            for ev in pygame.event.get():
                self.handle_event(ev)
            if self.state == "title":
                self.draw_title()
            else:
                self.step(dt)
                self.draw_world()
                if self.state == "paused":
                    self.draw_pause()
            if self._show_fps:
                self._draw_fps_overlay()
            pygame.display.flip()
