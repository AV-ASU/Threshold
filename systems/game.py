"""The top-level Game runtime: title screen, scene transitions, input,
combat, save/load, the main loop."""
import math
import random
import sys
import pygame

from constants import (
    SCREEN_W, SCREEN_H, TILE,
    C_BG, C_WHITE, C_BLACK, C_GOLD, C_BLOOD,
)
from rendering.sprites import (draw_player_sprite, draw_npc_sprite,
                               draw_npc_corpse, draw_infested_overlay,
                               draw_axe_swing, draw_axe_held,
                               draw_revolver_held, draw_gun_fire,
                               draw_king_death,
                               door_mask_surface, reset_king_fx,
                               view_from_facing, KING_UNFOLD,
                               KING_UNFOLD_SCALE)
from rendering.king_unfold import draw_unfold_catch
from rendering.transform import draw_vessel_bloom
from rendering.camera import Camera
from systems.look_control import LookController
from ui.fonts import make_fonts
from ui.dialog import DialogueBox
from ui.inventory_ui import InventoryUI
from ui.notebook_ui import NotebookUI
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
from systems.threat_mixin import ThreatMixin
from systems.king_roam_mixin import KingRoamMixin
from systems.infest_mixin import InfestationMixin, _corpse_examine
from systems.render_mixin import RenderMixin
from systems.narrative_mixin import NarrativeMixin


class Game(CutsceneMixin, ThreatMixin, KingRoamMixin, InfestationMixin,
           RenderMixin, NarrativeMixin):
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
        self.fonts = make_fonts()
        # Audio() synthesises the entire SFX + music library at startup (the
        # game ships zero audio assets) -- several seconds of pure-Python DSP
        # during which nothing else runs. Paint a quiet loading frame FIRST so
        # the window isn't a dead/"Not Responding" black rect on every launch.
        self._draw_boot_screen()
        self.audio = Audio()
        self.save = Save(slot=1)
        self.dialog = DialogueBox(self.audio, self.fonts)
        self.inv_ui = InventoryUI(self.fonts, self.audio, self.save)
        self.notebook_ui = NotebookUI(self.fonts, self.audio, self.save)
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
        # The single world->screen projection (CAMERA.md). At pitch 0 this is
        # exactly the legacy `int(x - cam_x)` top-down view; keeping every
        # render conversion behind it is what makes a future tilt a parameter
        # change rather than a 37-scene rewrite. `cam_x/cam_y` remain the
        # source of truth for the offset (camera update + input still use
        # them); the camera is re-synced to them each frame in draw_world.
        self.camera = Camera()
        # The oblique view is the DEFAULT (CAMERA.md): start at the locked tilt
        # pitch. F3 toggles back to the flat pitch-0 top-down view (which stays
        # byte-identical to the legacy raster). _reset_run_state re-seeds this on
        # every New Game.
        self._cam_pitch_target = math.radians(TILT_PITCH_DEG)
        self.camera.pitch = self._cam_pitch_target
        self.look = LookController()       # mouse-look heading model (tilt mode)
        self._rmb_last_x = None            # right-drag scene-rotate anchor
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
        # player is still inside a CREEPY_SCENES key (or anywhere after
        # world_emptied).
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
        # Ashfall motes (NARRATIVE 4b): live screen-space particle field,
        # eased toward a stage-driven target each frame. See _tick_ashfall.
        self._ashfall_parts = []

        # ---- THRESHOLD: the visibility meter ----
        # `visibility` is a float in [0, 1]: how visible the player is
        # to the King in Yellow right now. Watchers (spawned by a
        # cultist's curse) raise it; hiding bleeds it back down. At 1.0
        # the King materialises at the doorway and hunts; drop below
        # 0.90 and he dissolves. See _tick_visibility + _tick_king.
        self.visibility = 0.0
        self._vis_floor = 0.0        # evidence-driven minimum (NARRATIVE §3)
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
        # The King is the lethal apex. `_king` holds his NPC while he
        # is in the scene (None otherwise); `_king_anchor` is the
        # doorway the player entered from -- where he materialises. He
        # spawns when visibility hits 1.0 and dissolves below 0.90.
        # See _tick_king.
        self._king = None
        self._king_anchor = None
        self._reinforce_t = 0.0      # cultist reinforcement-wave cooldown
        self._gun_cd = 0.0           # seconds until the pistol can fire again
        # The roaming King (KING_ROAM rework): one persistent, world-positioned
        # apex that idles down the road, then roams + hunts. Survives scene
        # loads; only _reset_run_state wipes it. _king_dread (0..1) is the
        # cross-scene tell the ashfall + audio read when he is near.
        self._roam_king = self._new_roam_king_state()
        self._king_dread = 0.0
        # The King's portal (KING_ROAM M2): the active rift dict while one is
        # torn (None otherwise), and the pinned-100% charge timer toward it.
        self._portal = None
        self._portal_charge_t = 0.0
        # After juking through a rift: (target_scene, (x, y)) to drop the player
        # at the EXACT spot the rift showed (where the King was). Applied in
        # load_scene_now, then cleared.
        self._pending_emerge = None
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
        self._cursed = False           # the watcher-curse: active until cleared
        self._watchers = []            # Watcher NPCs currently manifested
        self._watcher_clone_t = 0.0    # exposure-gated timer between clones
        self._gaze_count = 0           # cultists watching the player this frame
        self._cult_topup_t = 0.0       # rate-limits cultist (re)spawns per scene
        self.flashlight_on = False     # player intent; only "lit" in DARK scenes

        # ---- THRESHOLD: flashback ----
        # Fires when the player reads Mara's journal through a third time.
        # Reading her words puts the PI back inside the ONE dream he had a
        # year ago, before Brimley (NARRATIVE 1b / §0: attuned exactly once,
        # it never took) -- the same door her journal describes. Not text -- a
        # wordless held shot: an open doorway of dried wood suspended in
        # black, a pulsing yellow glow radiating from it (cut off by the
        # frame), faint eyes peeking, and -- building from one face to a
        # swarm that all stare back -- a crowd of His dark-wood masks. The
        # "you can never arrive" of the whole game, at the scale of one dream.
        # _flashback_phase is None (inactive) or 0 (the one held phase).
        self._flashback_phase = None
        self._flashback_t = 0.0
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

    def _title_menu_options(self):
        """THRESHOLD is a single-session game -- there is no save file
        to continue from. The menu is just New Game / Quit."""
        return ["New Game", "Quit"]

    def title_input(self, ev):
        if ev.type != pygame.KEYDOWN: return
        if ev.key == pygame.K_F11:
            self._toggle_fullscreen(); return
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
            elif opt == "Quit":
                pygame.quit(); sys.exit(0)

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
        self.load_scene_now(self.save.data.get("scene", "bedroom"),
                             self.save.data.get("spawn", "default"))
        self.state = "playing"

    def _reset_run_state(self):
        """Wipe all per-run state so a New Game starts clean. The
        Game instance is reused across Quit-to-Title -> New Game, so
        in-memory run state from a previous run is cleared here."""
        # Debug oblique tilt (F3) starts off each run.
        # Oblique view is the default; New Game starts tilted (F3 -> flat).
        self._cam_pitch_target = math.radians(TILT_PITCH_DEG)
        self.camera.pitch = self._cam_pitch_target
        self.camera.yaw = 0.0
        self.look = LookController()
        self._rmb_last_x = None
        # Visibility meter + the King in Yellow
        self.visibility = 0.0
        self._vis_floor = 0.0
        self._being_seen = 0.0
        self._chant_t = 0.0
        self._breath_t = 0.0
        self._heartbeat_t = 0.0
        self._king = None
        self._king_anchor = None
        reset_king_fx()        # clear his render trail/particles across runs
        self._reinforce_t = 0.0
        self._gun_cd = 0.0
        self._roam_king = self._new_roam_king_state()
        self._king_dread = 0.0
        self._portal = None
        self._portal_charge_t = 0.0
        self._pending_emerge = None
        self._idle_king = None
        # Cultists, the curse, and Watchers
        self._cursed = False
        self._watchers = []
        self._watcher_clone_t = 0.0
        self._gaze_count = 0
        self._cult_topup_t = 0.0
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
        # Tilt look: the world heading the player is walking this frame (set by
        # update_player, consumed by _update_look to turn the body). Transient,
        # but reset here so it never leaks across a quit-to-title.
        self._move_heading = None
        # Stillness + heartbeat
        self.stillness_t = 0.0
        self._delayed_audio = []
        self._creepy_step_count = 0
        # Flashback / ending state
        self._flashback_phase = None
        self._flashback_t = 0.0
        self._flashback_masks = []
        self._flashback_pool = None
        self._flashback_spawn_acc = 0.0
        self._flashback_stab_done = False
        self._ending_active = None
        self._ending_phase = 0
        self._ending_phase_t = 0.0
        self._closure_locked = False
        # Death screen: None | "cultist" | "king". A catch triggers it;
        # _tick_death holds it (cultist ~2.8s CAPTURED card, king ~3.5s
        # Carcosa furnace) then ENDS the run -- both return to title.
        self._death_kind = None
        self._death_t = 0.0
        self._notebook_toast_t = 0.0   # evidence-scribble toast timer
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
        self._gaze_bind_t = 0.0        # cultist gaze-bind dwell (_tick_gaze_bind)
        self._sprint_step_t = 0.0      # sprint footstep cadence (_tick_sprint)
        self._rite_cues = set()        # one-shot rite cue latches (ending)
        self._folds = []               # seen-fold peek cache (_build_fold_cache)

    # ---- Scene management ----
    def begin_transition(self, target_scene, spawn_id="default"):
        if self.state == "transition": return
        # Seamless outdoor-to-outdoor crossing. Both scenes are part of
        # the continuous outside world (SEAMLESS_WORLD_SCENES). No
        # fade, no level-load semantic. Use the destination's canonical
        # spawn (because the spawn already accounts for the destination's
        # road position) and then shift the camera so the player stays
        # at the SAME SCREEN POSITION before and after the swap. From
        # their point of view nothing jumped -- the tiles around them
        # changed.
        current_key = self.scene.key if self.scene else None
        if (current_key is not None
                and current_key in SEAMLESS_WORLD_SCENES
                and target_scene in SEAMLESS_WORLD_SCENES
                and current_key != target_scene):
            screen_dx = self.player.x - self.cam_x
            screen_dy = self.player.y - self.cam_y
            self.load_scene_now(target_scene, spawn_id, keep_music=True)
            # load_scene_now snapped the camera; override so the
            # player stays at the same screen position. For non-wrap
            # destination scenes the camera may immediately drift on
            # the next frame due to clamping; that's fine -- the
            # transition moment itself is continuous.
            self.cam_x = self.player.x - screen_dx
            self.cam_y = self.player.y - screen_dy
            return
        # The cellar is no longer key-gated -- the Ledger (evidence #3) is a
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
        if (current == "bedroom" and target_scene == "house"
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
        self.transition_target = (target_scene, spawn_id)
        self.transition_dir = "out"
        self.transition_t = 0.0
        self.state = "transition"
        self.audio.play("door_open", 0.7)

    def load_scene_now(self, key, spawn_id="default", *, keep_music=False):
        if self.scene and self.scene.on_exit_fn:
            self.scene.on_exit_fn(self, self.scene)
        self.scene = load_scene(key)
        self.save.visit_scene(key)
        self.save.data["spawn"] = spawn_id
        spawn = self.scene.spawns.get(spawn_id, self.scene.spawns.get("default"))
        if spawn:
            self.player.x, self.player.y = spawn
        # Juked through a rift: drop the player at the EXACT spot it showed (the
        # King's vacated position), overriding the spawn, if it is walkable.
        pe = getattr(self, "_pending_emerge", None)
        if pe is not None and pe[0] == key and pe[1] is not None:
            ex, ey = pe[1]
            if not self.scene.is_solid_at(ex, ey):
                self.player.x, self.player.y = ex, ey
                spawn = (ex, ey)
        self._pending_emerge = None
        # The King materialises at the doorway the player entered from.
        # He stays behind on a scene change (cleared here) and re-forms
        # at the new entry if visibility is still pinned at the top.
        self._king = None
        reset_king_fx()        # his trail/particles don't follow across scenes
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
        self._gaze_count = 0
        self._cult_topup_t = 0.0
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
        else:
            self.scene._last_entry_exit_tile = None
        # Reset the step-event buffer on each scene load. A step in
        # one scene shouldn't bleed into the next.
        self.scene._last_step_event = None
        self._build_fold_cache()
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
        # Round-9: dying to the Yellow King empties the world. Every
        # scene loaded after `world_emptied` is set has its NPC list
        # cleared post-on_enter, so any villagers / shopkeep / kid /
        # innkeeper / terminal handler placed by the builder or
        # on_enter fn is removed before the player sees the scene. The
        # world keeps its layouts and items, just no people.
        if self.save.flag("world_emptied"):
            self.scene.npcs = []
        else:
            # Re-derive the world's infestation for this scene from the
            # evidence count (rot decals, turned/mutated locals, the
            # stage-3 Sheriff encounter). Corpses are NOT persisted across
            # scene loads (NARRATIVE 1b/3: the act costs in the moment, no
            # cross-scene ledger) -- a killed local lies there only while
            # you're in the room.
            self._apply_infestation()

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

    def _update_camera(self, snap=False):
        target_x = self.player.x - SCREEN_W // 2
        target_y = self.player.y - SCREEN_H // 2
        # Lead the camera in the way the player is walking so they can see
        # where a path is taking them BEFORE they commit -- vital where the
        # road bends or folds back on itself. In a torus (wrap) scene the
        # far side is already drawn as edge-clones, so leading toward a seam
        # actually shows what's waiting across the fold. Eased by the lerp
        # below so changing direction doesn't snap the view.
        fx, fy = self.player.facing
        flen = math.hypot(fx, fy) or 1.0
        target_x += (fx / flen) * CAM_LOOKAHEAD
        target_y += (fy / flen) * CAM_LOOKAHEAD
        scene_w = self.scene.w * Scene.TILE
        scene_h = self.scene.h * Scene.TILE
        if not self.scene.wrap_x:
            target_x = max(0, min(scene_w - SCREEN_W, target_x))
            if scene_w < SCREEN_W:
                target_x = (scene_w - SCREEN_W) // 2
        if not self.scene.wrap_y:
            target_y = max(0, min(scene_h - SCREEN_H, target_y))
            if scene_h < SCREEN_H:
                target_y = (scene_h - SCREEN_H) // 2
        if snap:
            self.cam_x = target_x; self.cam_y = target_y
            # Land already at the target pitch on a snap (game start / scene
            # load) so the default oblique view doesn't ease up from flat on
            # every door; the F3 toggle still eases (non-snap path below).
            self.camera.pitch = self._cam_pitch_target
        else:
            self.cam_x += (target_x - self.cam_x) * 0.18
            self.cam_y += (target_y - self.cam_y) * 0.18
            # Ease the tilt pitch toward its target (the F3 toggle). Zoom out
            # slightly as it tilts so more of the room reads; both are exactly
            # the shipping values at pitch 0 (scale 1.0), keeping that view
            # untouched.
            self.camera.pitch += (self._cam_pitch_target - self.camera.pitch) * TILT_EASE
        pf = self.camera.pitch / math.radians(TILT_PITCH_DEG)
        self.camera.scale = 1.0 - (1.0 - TILT_ZOOM) * pf
        # Keep the camera's spatial pivot in sync here (was only in draw_world)
        # so mouse->world (unproject) in _update_look reads the live frame.
        self.camera.origin = (SCREEN_W // 2, SCREEN_H // 2)
        self.camera.cam_x = self.cam_x + SCREEN_W // 2
        self.camera.cam_y = self.cam_y + SCREEN_H // 2

    def _tilt_on(self):
        """The oblique 'look' mode is engaged (F3). Mouse-look + camera-relative
        movement + cursor-aimed gun apply ONLY here; pitch 0 stays the shipping
        top-down game untouched."""
        return self._cam_pitch_target > 0.0

    def _update_look(self, dt):
        """Drive the LookController from the mouse and steer the camera yaw +
        player facing. Runs only in tilt mode and only during play."""
        if not (self._tilt_on() and self.state == "playing" and self.player):
            self._rmb_last_x = None
            return
        mx, my = pygame.mouse.get_pos()
        rmb_held = pygame.mouse.get_pressed()[2]
        rmb_dx = 0.0
        if rmb_held and self._rmb_last_x is not None:
            rmb_dx = mx - self._rmb_last_x
        self._rmb_last_x = mx if rmb_held else None
        # world heading from the player to the point under the cursor
        wx, wy = self.camera.unproject(mx, my)
        aim = math.atan2(wy - self.player.y, wx - self.player.x)
        move_heading = getattr(self, "_move_heading", None)
        self.look.update(move_heading=move_heading, aim_heading=aim,
                         rmb_dx=rmb_dx, rmb_held=rmb_held)
        self._move_heading = None      # consumed; movement re-sets it next frame
        self.camera.yaw = self.look.cam_yaw
        # the gun + sprite face where you aim (the head, clamped to the turn
        # arc); the body itself is turned by walking (update_player above).
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
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
        # Movement breaks explicit hide spots (those set
        # hide_origin so we can teleport the player back). Corn-
        # patch cover is *passive* -- the player walks through the
        # patch while hidden, no teleport on exit; the floor-tile
        # check after movement clears the hide when they step out.
        if (dx or dy) and self.player.hidden is not None:
            if self.player.hide_origin is not None:
                self.player.hidden = None
                self.player.x, self.player.y = self.player.hide_origin
                self.player.hide_origin = None
                self.show_notice("You step out of cover.",
                                  duration=1.6)
            # else: corn-state hide; let the floor check below
            # handle entry/exit transparently.
        if dx or dy:
            mag = math.hypot(dx, dy) or 1
            dx /= mag; dy /= mag
            if self._tilt_on():
                # World-relative movement; the body (and the camera that
                # follows it) turn toward where you WALK -- stash the travel
                # heading for _update_look to ease the body to. The mouse only
                # aims the head/gun, so aiming never turns the body (no spin).
                # (dx,dy) stay world directions; facing is owned by the mouse.
                self._move_heading = math.atan2(dy, dx)
            else:
                self.player.facing = (dx, dy)
            self.player.walk_phase += dt * 12
            # Base speed is reduced by the threat meter (spatial
            # compression -- the closer you are to being caught, the
            # harder it is to move) and boosted by active sprint.
            comp_mult = 1.0 - self.visibility * 0.45
            sprint_mult = 1.7 if self.player.sprint_active else 1.0
            effective_speed = (self.player.speed
                               * comp_mult * sprint_mult)
            new_x = self.player.x + dx * effective_speed * dt
            new_y = self.player.y + dy * effective_speed * dt
            blocked_x = (self.scene.is_solid_at(new_x, self.player.y)
                         or self._river_blocks(new_x, self.player.y))
            blocked_y = (self.scene.is_solid_at(self.player.x, new_y)
                         or self._river_blocks(self.player.x, new_y))
            moved = False
            if not blocked_x: self.player.x = new_x; moved = True
            if not blocked_y: self.player.y = new_y; moved = True
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
            if not moved:
                self.player.bump_timer -= dt
                if self.player.bump_timer <= 0:
                    self.audio.play("bump", 0.4)
                    self.player.bump_timer = 0.25
            else:
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
                elif (not on_corn) and self.player.hidden == "corn":
                    self.player.hidden = None
                # Sync the in_river state to whatever floor the player
                # is now standing on. River tile -> True, anything else
                # -> False. The blocker logic above ensures the player
                # only ever steps onto a river tile they're allowed on.
                self.player.in_river = (
                    self.scene.char_floor_at(self.player.x, self.player.y)
                    == "~"
                )
                self.player.step_timer -= dt
                if self.player.step_timer <= 0:
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
                        self.audio.play(sfx, 0.7)
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
                    now = pygame.time.get_ticks() / 1000.0
                    self.scene._last_step_event = (
                        self.player.x, self.player.y,
                        base * mult, now)
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

    # ---- Interaction ----
    def try_interact(self):
        # If currently hidden, E exits the hide.
        if self.player.hidden is not None:
            self.player.hidden = None
            if self.player.hide_origin is not None:
                self.player.x, self.player.y = self.player.hide_origin
                self.player.hide_origin = None
            self.show_notice("You slip out of cover.", duration=1.6)
            self.audio.play("blip_soft", 0.4)
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
            self.audio.play("blip_soft", 0.4)
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
            best.interact(self)
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
            return "The pile splinters apart."
        if ch == "q":
            sc_.objects[ty][tx] = "."
            self.save.set_flag(f"boards_broken_{sc_.key}_{tx}_{ty}", True)
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
        for e in self.scene.enemies:
            if not getattr(e, "alive", False):
                continue
            if (getattr(e, "kind", "") == "black_figure"
                    and math.hypot(e.x - cx, e.y - cy) < MELEE_REACH):
                e._stun_t = MELEE_STUN_DUR
                e.flash = 0.12
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
            self.audio.play("door_locked", 0.45)        # dry click
            self.show_notice("Empty. You need cartridges.", duration=1.4)
            self._gun_cd = GUN_CD
            return
        self._gun_cd = GUN_CD
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
        self.audio.play("swing", 0.4)
        self.audio.play("bump", 0.5)               # the report
        # A gunshot is loud -- feed the cult's investigate AI like a sprint.
        if self.scene is not None:
            self.scene._last_step_event = (p.x, p.y, 1.0,
                                           pygame.time.get_ticks() / 1000.0)
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
        self.audio.play("enemy_die", 0.55, pan=pan)
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
        # the body and a hard visibility spike. The body stays down for as
        # long as you're in the room (_make_corpse), but is NOT persisted
        # across scene loads -- the act costs in the moment, not a ledger
        # (NARRATIVE 1b/3).
        self.visibility = min(LOCAL_KILL_VIS_CAP,
                              max(self.visibility,
                                  self.visibility + LOCAL_KILL_VIS_SPIKE))
        if self.scene is not None:
            self.scene._last_step_event = (
                npc.x, npc.y, 1.0, pygame.time.get_ticks() / 1000.0)
        return True

    def _make_corpse(self, npc):
        """Convert a just-killed local NPC into a corpse for the rest of the
        time the player is in this room: it stops moving (alive=False
        already), stops blocking, and answers E with a one-shot examine
        instead of its old dialogue. Not persisted across scene loads
        (NARRATIVE 1b/3) -- the scene rebuilds the local live on re-entry."""
        npc._is_corpse = True
        npc._kill_processed = True
        npc.solid = False
        npc.movement = "idle"
        npc.dialogue_fn = _corpse_examine
        npc.no_prompt = False

    def _kill_enemy(self, e):
        """Run the death side-effects for `e`: marks dead, plays the
        death SFX, rolls drops (85% suppressed for respawning enemies),
        and fires on_kill. Called from melee and friendly-projectile
        paths so a pistol kill awards drops/on_kill the same way a
        sword kill does. Increments the kill counter, which the
        substrate references in late-game evidence files."""
        e.alive = False
        pan = self.audio.pan_for_world(e.x, self.player.x)
        self.audio.play("enemy_die", 0.6, pan=pan)
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
                self.audio.play(entry[1], entry[2], pan=pan)
            else:
                survivors.append(entry)
        self._delayed_audio = survivors

    _FB_GAZE = [(math.cos(a * math.tau / 8), math.sin(a * math.tau / 8))
                for a in range(8)] + [(0.0, 0.0)]

    # The PI's interior voice down the descent (NARRATIVE §6, GAME_CHANGES §8):
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
                "[c=dim]Their whole lives, sorted and shelved down here. Like "
                "they set everything human down at the door and walked in "
                "lighter. ...My pen won't hold still. That's new.[/c]",
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
                "shoulder for the rope. Still there. I say so to myself more "
                "than a steady man would.",
            ],
        },
        # The Playscript (the cult's notes): the SEED of the want-to-leave.
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
                "There's no rope to climb. So down.[/c]",
            ],
            "note": [
                "The stair took the rope when it opened. No way back up. Only "
                "down now.",
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
        else:
            self.show_notice("Another door, drawn where no door is. Bare "
                             "wall behind the chalk.")
        return True

    # ---- Endings ----

    # Ending scripts. Each is a list of (line, duration_seconds).
    # escape_alone is the SPREAD IT ending -- drive out with the Sign, the
    # only thing the fold opens for (NARRATIVE §1/§6). seal_threshold
    # (END IT) closes the Threshold on Brimley and on you (NARRATIVE §6).
    _ENDING_SCRIPTS = {
        "escape_alone": [
            ("You turn the key. The engine turns over.", 2.6),
            ("And over. The way it has every time before.", 2.6),
            ("Then, with the Sign beside you, it catches.", 3.0),
            ("You drive out, past the corn that never ended.", 3.2),
            ("You got out. You're the only one who ever has.", 3.4),
            ("Everyone will understand why, soon.", 3.8),
        ],
        "seal_threshold": [
            ("The frame drinks it down: the smoke, the sound, the long "
             "way you came.", 3.0),
            ("Above you the stair grinds shut. Then the Works. Then the "
             "well.", 3.0),
            ("Brimley folds the rest of the way closed, around the "
             "hunger, and around you.", 3.4),
            ("On every map after tonight the town is a blank, a place the "
             "roads decline to reach.", 3.6),
            ("It is done. Nothing leaves Brimley again.", 3.4),
            ("Not the hunger. Not you.", 4.0),
        ],
        # rite_broken is the TRAP game over (NARRATIVE §6). PURELY VISUAL --
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
                            or self.text_input.active)
            # Evidence-gated corruption: cultists only bloom into His maw
            # once you understand too much (3+ evidence). Read by the
            # cultist AI when it locks on (enemy._cult_tick / npc chaser).
            if self.scene is not None:
                self.scene._bloom_enabled = (
                    self._evidence_count() >= KING_GATE_EVIDENCE)
            if not world_frozen:
                exit_data = self.scene.find_exit_at(
                    self.player.x, self.player.y,
                    facing=self.player.facing)
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
                    self.begin_transition(*exit_data)
            # Suspend scene update (NPC patrols, decoration anims, triggers)
            # while any modal is up so the world freezes behind it.
            if not world_frozen:
                self.scene.update(dt, self)
            self.text_input.update(dt)
            for e in list(self.scene.enemies):
                if not world_frozen:
                    e.update(dt, self.scene, self.player)
                    if e.just_shot and e.shoot_sfx:
                        pan = self.audio.pan_for_world(e.x, self.player.x)
                        self.audio.play(e.shoot_sfx, 0.55, pan=pan)
                if not e.alive:
                    self.scene.enemies.remove(e)
            # A scene-placed cultist (the Works gauntlet uses Enemy-class
            # cultists, not the threat-system NPCs) reaching the player
            # TAKES them -- the same CAPTURED end the town cultists trigger.
            # Without this those cultists just chased and did nothing, so
            # capture felt random ("some take me, some don't"). Hidden /
            # invuln / mid-death are exempt, matching _tick_cultists.
            if (not world_frozen and self._death_kind is None
                    and self.player.hidden is None
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
                        self.audio.play("hit", 0.55, pan=pan)
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
            if self.player.hp <= 0:
                self._on_player_death()
            self._update_camera()
            self._update_look(dt)
            self.audio.update_silence()
            self.audio.update_duck()
            self.dialog.update(dt)
            self._tick_delayed_audio(dt)
            # The threat model is part of the world sim -- it freezes behind
            # a modal too, so visibility can't climb and the King can't close
            # while a box is up. Cutscene/audio drivers keep running.
            if not world_frozen:
                self._tick_cultists(dt)
                self._tick_fold_pursuit(dt)
                self._tick_sheriff(dt)
                self._tick_gaze_bind(dt)
                self._tick_watchers(dt)
                self._tick_visibility(dt)
                self._tick_heartbeat(dt)
                self._tick_cult_ambient(dt)
                if KING_ROAM:
                    self._tick_king_roam(dt)
                else:
                    self._tick_king(dt)
            self._tick_wake_muffle(dt)
            self._tick_ashfall(dt)        # atmosphere: drifts behind modals too
            self._tick_flashback(dt)
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

    def _on_player_death(self):
        if self.scene and self.scene.key == "well_bottom":
            if not self.save.flag("well_rope_broken"):
                self.save.set_flag("well_rope_broken", True)
        # Death in the void boss arena seals the secret path forever,
        # empties the world of NPCs, and respawns the player on the
        # town square rather than their bed. The world_emptied flag
        # is checked in load_scene_now so every scene from now on has
        # its npc list zeroed -- the layouts persist, the people don't.
        if self.scene and self.scene.key == "void_boss":
            self.save.set_flag("void_path_closed", True)
            self.save.set_flag("world_emptied", True)
            self.player.hp = self.player.max_hp
            self.show_notice("You wake on the town square. It is silent.")
            self.load_scene_now("brimley", "default")
            return
        self.player.hp = self.player.max_hp
        self.show_notice("You wake up in your bed.")
        self.load_scene_now("bedroom", "default")

    def _flash_notebook(self):
        """Fire the corner notebook-scribble toast -- a new evidence beat was
        just logged (the PI jotting it down)."""
        self._notebook_toast_t = NOTEBOOK_TOAST_DUR

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
        ("Inventory",           "I"),
        ("Notebook",            "N"),
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
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self._end_opening()            # silent skip, no on-screen tell
                elif self._opening_phase == "stall":
                    self._opening_restart()         # tap: the engine catches
                elif self._opening_phase == "dead":
                    self.audio.play("bump", 0.3)    # it just turns over
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
        if self.inv_ui.open:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_i, pygame.K_ESCAPE):
                    self.inv_ui.toggle()
                elif ev.key == pygame.K_n:
                    # Hot-swap from inventory to notebook so the
                    # player doesn't have to close one to open
                    # the other.
                    self.inv_ui.toggle()
                    self.notebook_ui.toggle()
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    self.inv_ui.move(-1, self.player.inventory)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.inv_ui.move(1, self.player.inventory)
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    self.inv_ui.change_tab(-1, self.player.inventory)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    self.inv_ui.change_tab(1, self.player.inventory)
                elif ev.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
                    self.inv_ui.use_selected(self.player)
            return
        if self.notebook_ui.open:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_n, pygame.K_ESCAPE):
                    self.notebook_ui.toggle()
                elif ev.key == pygame.K_i:
                    self.notebook_ui.toggle()
                    self.inv_ui.toggle()
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    self.notebook_ui.move(-1)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.notebook_ui.move(1)
            return
        if self.state in ("playing", "transition"):
            if ev.type == pygame.KEYDOWN:
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
                    self.inv_ui.toggle()
                elif ev.key == pygame.K_n:
                    self.notebook_ui.toggle()
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
                elif ev.key == pygame.K_F3:
                    # The oblique look mode is the DEFAULT (CAMERA.md); F3
                    # toggles it OFF to the flat pitch-0 top-down view and back.
                    # Pitch eases in _update_camera. On (re-)enable, seed the
                    # look heading from the player's current facing so the
                    # camera settles behind them with no rotation jump.
                    if self._cam_pitch_target:
                        self._cam_pitch_target = 0.0
                    else:
                        self._cam_pitch_target = math.radians(TILT_PITCH_DEG)
                        if self.player:
                            fx, fy = self.player.facing
                            self.look = LookController(math.atan2(fy, fx))
                            self.camera.yaw = self.look.cam_yaw
                        self._rmb_last_x = None
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
            pygame.display.flip()
