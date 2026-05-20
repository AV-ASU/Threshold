"""The top-level Game runtime: title screen, scene transitions, input,
combat, save/load, the main loop."""
import time
import math
import random
import sys
import pygame

from constants import (
    SCREEN_W, SCREEN_H, TILE,
    C_BG, C_WHITE, C_BLACK, C_GOLD, C_RED, C_BLOOD,
    C_BLUE, C_GREEN, C_PURPLE, C_PANEL, C_PANEL_BORDER, C_DIM,
)
from rendering.sprites import draw_player_sprite, draw_npc_sprite
from ui.fonts import make_fonts
from ui.dialog import DialogueBox
from ui.inventory_ui import InventoryUI
from ui.notebook_ui import NotebookUI
from ui.text_input import TextInputModal
from systems.audio import Audio
from systems.save import Save
from systems.items import Inventory, ITEM_DEFS
from entities.player import Player
from entities.enemy import Enemy
from entities.npc import NPC
from entities.decoration import Decoration
from scenes import load_scene, tile_footstep, Scene

# THRESHOLD: scene sets keyed to the cult fiction. The cult sites
# (cult_chamber, the cauldron clearing) bypass the standard fade --
# crossing into them is meant to feel like a snap, not a door.
VOID_SCENES = {"void_boss", "symbol_portal_room"}


# Day-phase cycle. Sleeping in the cot advances the phase by one
# step; phases loop morning -> afternoon -> dusk -> night -> morning.
# Future content can gate events to specific phases (e.g. patrols
# only walk at dusk, the cauldron only fires at night) by reading
# save.arg("day_phase").
_DAY_PHASE_ORDER = ("morning", "afternoon", "dusk", "night")


def _next_day_phase(phase):
    try:
        i = _DAY_PHASE_ORDER.index(phase)
    except ValueError:
        i = 0
    return _DAY_PHASE_ORDER[(i + 1) % len(_DAY_PHASE_ORDER)]


# THRESHOLD calendar. day_count == 1 on the first wake; it ticks up
# every time the player sleeps in the cot. Day 1 maps to Oct 4 so
# the journal's "Day 4 at the inn" lines up with what the wall
# calendar shows on the first morning. Three days (Oct 1, 2, 3)
# are already X'd off when the player first sees it -- the time
# the protagonist has been here before the game opens.
_KEY_DATES = {
    (10, 31): "halloween",
    (12, 21): "solstice",
    (12, 31): "new_years_eve",
}

def day_count_to_date(d):
    """day 1 -> (10, 4)  (Oct 4)
       day 28 -> (10, 31) (Halloween)
       day 79 -> (12, 21) (Solstice)
       day 89 -> (12, 31) (NYE)
       day 90+ -> (1, n)  (post-NYE; calendar shows January)"""
    offset = d + 3
    if offset <= 31:
        return (10, offset)
    offset -= 31
    if offset <= 30:
        return (11, offset)
    offset -= 30
    if offset <= 31:
        return (12, offset)
    return (1, max(1, offset - 31))

def days_in_month(month):
    return {10: 31, 11: 30, 12: 31, 1: 31}.get(month, 31)

# Scenes where dread-state effects engage: the stillness heartbeat
# ramps up while the player stands still here, and the cult-site
# floors get the rare delayed-footstep trick.
CREEPY_SCENES = {"basement", "void_boss", "symbol_portal_room",
                 "haunted_house", "well_bottom", "well_passage",
                 "mistlands"}

# Hand-authored crate loot. Keyed by (scene_key, tile_x, tile_y);
# value is the item key dropped when the player chops the crate
# open with the splitting axe. Crates are placed inside the
# playable area (never on the edge -- the gateway role belongs
# to '*' debris). Every entry here corresponds to a `K` tile in
# that scene's object map. Saves persist a per-coord
# `crate_broken_<scene>_<tx>_<ty>` flag so a broken crate stays
# broken across re-entries.
CRATE_LOOT = {
    # Cornfield maze -- a side crate the player finds while
    # searching for the liquor crate. Holds a stick of charcoal.
    ("cornfield_maze", 5, 6):  "charcoal",
    # Country lane -- a crate against the inner corn wall, the kind
    # of stash a runner leaves for a pickup that never came.
    # Holds a torn diary page (the kid's family, in the player's
    # own handwriting).
    ("country_lane",   8, 4):  "diary_page_2",
    # Mistlands west bank -- a crate near the cauldron path, holding
    # a sigil rubbing the cult left for a courier who never showed.
    ("mistlands",     14, 78): "sigil_rubbing",
    # Mistlands east bank -- a crate behind the relocated barn
    # holding a kid's drawing pinned to the inside lid.
    ("mistlands",     78, 78): "kid_drawing",
    # Forest path -- a crate set against an interior corn stalk,
    # holding a clear vial.
    ("forest_path",    8, 5):  "potion_clear",
    # Village (the new farm) -- a crate just west of the woodshed
    # holding spare batteries.
    ("village",       21, 16): "spare_batteries",
}

# Capture-trace deposits. Each non-closure capture plants the next
# entry in this list as a persistent decoration in the named scene.
# The index into this list is `save.arg("capture_traces", 0)`.
# After all entries are used the player has accumulated a small
# museum of evidence that the world remembers what happened to them.
# Tiles are tile-coords (x, y); decorations are placed at tile
# centre. Scenes the player is virtually guaranteed to revisit are
# preferred (bedroom, yard, village).
CAPTURE_TRACE_DEPOSITS = [
    ("bedroom",        2, 4, "bloody_handprint"),
    ("our_house_area", 6, 6, "phantom_mark"),
    ("village",        9, 8, "bloody_handprint"),
    ("bedroom",        4, 6, "claw_marks"),
    ("our_house_area", 11, 13, "phantom_mark"),
    ("village",        14, 11, "phantom_mark"),
    ("bedroom",        6, 4, "phantom_mark"),
]

# Outdoor decay tier. Each scene gets a small list of "this is
# what's been added" decorations as Pursuer proximity climbs.
# Keyed by (scene, tier) -> list of (tx, ty, kind). Mid tier
# (proximity >= 0.33) plants a single subtle prop near a door or
# threshold; high tier (proximity >= 0.66) layers two more so the
# scene visibly worsens. Re-applied on every scene load -- the
# player coming back through after the line has tightened sees a
# changed world even though no NPC mentioned it.
#
# The mistlands is intentionally absent: it's already heavily
# dressed, and a rework is in flight.
OUTDOOR_DECAY = {
    ("village", "mid"):       [(8, 7, "bloody_handprint")],
    ("village", "high"):      [(8, 7, "bloody_handprint"),
                                (12, 9, "dead_crow"),
                                (4, 11, "claw_marks")],
    ("our_house_area", "mid"):  [(5, 11, "claw_marks")],
    ("our_house_area", "high"): [(5, 11, "claw_marks"),
                                  (15, 6, "phantom_mark"),
                                  (8, 13, "dead_crow")],
    ("forest_path", "mid"):   [(6, 8, "dead_crow")],
    ("forest_path", "high"):  [(6, 8, "dead_crow"),
                                (10, 12, "claw_marks"),
                                (3, 5, "bloody_handprint")],
    ("graveyard", "mid"):     [(7, 9, "phantom_mark")],
    ("graveyard", "high"):    [(7, 9, "phantom_mark"),
                                (4, 6, "dead_crow")],
    ("country_lane", "mid"):  [(5, 4, "dead_crow")],
    ("country_lane", "high"): [(5, 4, "dead_crow"),
                                (8, 7, "claw_marks")],
    ("diner_gas_station", "mid"):  [(9, 6, "bloody_handprint")],
    ("diner_gas_station", "high"): [(9, 6, "bloody_handprint"),
                                     (4, 8, "phantom_mark")],
}

# Outdoor scenes -- everywhere the player is walking under sky.
# A soft always-on player-centred vignette darkens the world edges
# in these scenes so the world never feels safe between buildings.
# Mistlands runs its own (heavier) vignette via _draw_mistlands_haze
# and is intentionally NOT in this set so the two don't stack.
OUTDOOR_SCENES = {"our_house_area", "village", "forest_path",
                  "void_boss", "graveyard", "diner_gas_station",
                  "country_lane", "cornfield_maze",
                  "gravel_road_north", "river_crossing"}

# Dark scenes -- underground / interior cult sites where the
# flashlight matters. Without the flashlight the screen is heavily
# dimmed with a small clear circle around the player. With it,
# the dimness lifts to a wider cone in the facing direction.
DARK_SCENES = {"basement", "well_passage", "well_bottom",
               "symbol_portal_room", "haunted_house",
               "depths_antechamber", "depths_procession",
               "depths_hall", "depths_threshing", "depths_stair",
               "dark", "threshold"}

# Cult-dark: a subset of DARK_SCENES where the flashlight is
# mechanically disabled and the dread aperture closes regardless
# of equipment. Reality is thinner here. Past the threshold of
# normal physics.
CULT_DARK_SCENES = {"depths_antechamber", "depths_procession",
                    "depths_hall", "depths_threshing",
                    "depths_stair", "dark", "threshold"}

# Safe interiors. Heavy overlays short-circuit here so the room
# reads cleanly. The Inn (bedroom + house) is the refuge that the
# rest of the world is pressing against -- standing inside should
# feel SAFE compared to outside. Hide vignette also suppressed
# (you are already safe; the cramped read is wrong here).
SAFE_SCENES = {"bedroom", "house", "son_room", "kid_house"}

# Dim-but-clear interiors. The flashlight cone still draws -- the
# cellar wants the light -- but dread / apex / dip overlays are
# suppressed so the navigation read stays usable. Hide vignette
# still runs (cover here is meaningful).
DIM_SAFE_SCENES = {"basement"}

# 80% combined-darkness cap. Full-screen black overlays
# (visibility dip, apex wash, hide wash, YK vignette) decrement
# this budget per frame so the screen never goes opaque even when
# every overlay fires together. Player-centred radial vignettes
# don't participate -- their clear hole already protects the
# player's feet.
MAX_FULLSCREEN_DARK = 204

# Day/night design pivot: cultists are creatures of the night.
# Patrols only walk during the night phase, in mistlands (which is
# always night), or after the day-7 cap when the night-gate breaks
# entirely. The day is the player's preparation window; the night
# is the horror. _effective_phase() is the single source of truth
# for "what phase is this scene actually in".
PERMANENT_NIGHT_SCENES = {"mistlands"}
# Day count after which the day/night cycle stops working. The
# world is past saving by here -- there is no morning anymore.
DAY_NIGHT_BREAKS_AFTER = 7



# Mistlands river entry tile (col 34 = east edge of the river, row 60).
# Walking from land onto this tile is the only way to enter the river.
# Once in the river, the player can move freely between river tiles
# until they step onto land or bridge, which flips in_river False.
RIVER_ENTRY_TILE = (34, 60)


class Game:
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
        self.state = "title"   # title, playing, paused, transition
        # Title-screen ambient: the wind drone, no melody. The title
        # is meant to feel cold and unresolved -- if the player hesitates
        # on the menu, all they hear is the same wind that lives in the
        # mistlands. Scene music takes over the moment they continue.
        self.audio.play_music("threshold_drone")
        self.transition_t = 0.0
        self.transition_target = None
        self.transition_dir = "out"
        self.cam_x = 0
        self.cam_y = 0
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
        self.pause_options = ["Resume", "Quit to Title"]
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
        self._next_heartbeat_t = 0.0
        self._heartbeat_count = 0
        # Delayed-audio queue: list of [seconds_left, sfx_name, volume].
        # Used by the void/basement footstep "out of body" effect that
        # fires the step SFX a fraction of a second after the visual
        # step. Ticked in step().
        self._delayed_audio = []
        # Counter used to space the void/basement delayed-step trick;
        # every Nth eligible step plays late.
        self._creepy_step_count = 0
        # Cached vignette surface for the mistlands / alter scenes.
        # Built once on first need; blitted at the player's screen
        # position each frame so it "closes around" them.
        self._vignette_surf = None
        # Soft outdoor vignette. Always-on radial darkness centred on
        # the player whenever they're in an OUTDOOR_SCENES key. Less
        # intense than the mistlands vignette but never goes away --
        # the world edges are always pressing in. Cached on first need.
        self._outdoor_vignette_surf = None
        # Pursuer-glimpse: at very high proximity, after a scene
        # transition, a tall_shadow flashes at the screen edge for a
        # few frames. `_glimpse_t` ticks down per frame; non-zero
        # means draw it this frame.
        self._glimpse_t = 0.0
        self._glimpse_pos = (0, 0)
        # Countdown to the next orb-whisper. Ticks down every frame
        # while the player carries the orb; on zero, plays a faint
        # whisper SFX and reschedules between 8 and 18 seconds. Reset
        # to a small positive value at __init__ so the first whisper
        # arrives soon after the player picks up the orb.
        self._orb_whisper_t = 4.0
        # Schedule for the distant child-humming ambient -- ticks down
        # only while the player is inside a non-village scene that
        # gates the effect (basement / well / void). Fires the village
        # melody as a brief single-tone hum.
        self._humming_t = 12.0
        # Giant-eye overlay scheduling -- counts down between
        # appearances (sec). `_giant_eye_phase` > 0 means currently
        # visible; `_giant_eye_pos` is the screen-space anchor.
        self._giant_eye_t = -1.0
        self._giant_eye_phase = 0.0
        self._giant_eye_pos = (0, 0)
        # Visitor-silence latch: True while a tall_shadow is on
        # screen, so we only call force_silence / restore on the
        # transitions, not every frame.
        self._visitor_silence = False
        # Child trailer: while the player is in a creepy scene and
        # facing forward, a small kid sprite renders behind them.
        # Looking at it (player facing toward it) hides it for a few
        # seconds. The horror is that the player can never actually
        # see it -- it's always at the back of vision.
        self._trailer_hide_until = 0.0

        # ---- THRESHOLD: the Pursuer ----
        # The Pursuer is the thing that is following the player. It
        # never appears on screen. It manifests as audio (a phantom
        # footstep, a distant door, a slow inhale) and as occasional
        # text notices ("you hear footsteps. they are not yours.").
        # `pursuer_proximity` is a float in [0, 1]:
        #   0.0  = the player just left a safe room; quiet
        #   0.5  = ambient cues every 20-40 seconds
        #   1.0  = constant pressure; the threshold is closing
        # It rises automatically over real seconds played, jumps when
        # the player lingers (stillness), drops slightly on scene
        # transitions (the door cuts the line for a beat), and
        # persists across scenes -- it never resets to zero. It is
        # NOT serialised to the save: each loaded session starts
        # with a clean line, but the line tightens fast.
        self.pursuer_proximity = 0.0
        # Dread aperture: 1.0 = open / full sight, 0.0 = closed / the
        # ring of King in Yellow figures has reached the player. Decays
        # passively in DARK_SCENES without working flashlight; recovers
        # in hide_spots while standing still with no chaser nearby.
        # When it hits 0 the player is taken (closure trigger).
        self.dread_aperture = 1.0
        # Heartbeat schedule -- time to next thump. Kicks in only at
        # proximity >= 0.70 and only while the player is unhidden.
        # Period shortens with proximity so the pulse races at apex.
        # Independent of room ambients (that's environmental); this
        # one is biometric.
        self._heartbeat_t = 0.0
        # Visibility-dip timer. Set briefly above 0 by events that
        # tank the player's eyesight: a watcher banished by the
        # flashlight cone, eyes scattered when the player turns to
        # see them. Each tick decays back to 0; while active the
        # screen gets a heavy dark vignette overlay on top of the
        # normal one (drawn in _draw_visibility_dip).
        self._visibility_dip_t = 0.0
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
        # One-frame Pursuer silhouette held briefly when closure
        # arms (proximity hits 0.95). Drawn screen-centred over the
        # apex red wash. Player will not be sure they saw it.
        self._apex_silhouette_t = 0.0
        self._last_pos = (0.0, 0.0)  # for "standing still" detection
        self._chant_t = 0.0          # depths cult-chant ambient timer
        self._breath_t = 0.0         # depths cult-breath ambient timer
        # Schedule of next manifestation event (seconds). Set when
        # the pursuer fires an event; tightens as proximity grows.
        self._pursuer_next_event = 8.0
        # Total seconds since pursuer init -- drives the slow ramp.
        self._pursuer_t = 0.0
        # Prevents two close-cousin events from firing back-to-back.
        self._pursuer_last_event = ""
        # The "closure" countdown. Once proximity hits ~0.95, this
        # counts down 18 seconds and then triggers the ending. The
        # player can hold it off by transitioning scenes (each
        # transition adds 6 seconds back). They cannot prevent it.
        self._pursuer_closure_t = -1.0
        # Notice strings the Pursuer surfaces. Picked at random,
        # never the same one twice in a row. Trimmed to environmental
        # observations only -- the player narrates "behind you" /
        # "closer now" themselves once the audio has done its job.
        # What the notice does is point the eye at something the player
        # might not have inferred from the sound alone.
        self._pursuer_notices = [
            "a door closed somewhere.",
            "something moved in the next room.",
            "the sound of breathing.",
            "the candle was lit. it isn't now.",
            "the floorboards above you settle.",
        ]
        self._pursuer_last_notice = ""

        # ---- THRESHOLD: Watchers ----
        # Watchers are almost-visible figures the world places at the
        # edges of vision. They are NOT enemies -- they don't move,
        # they don't attack, they don't even exist on the scene.npcs
        # list. They appear at random world coordinates near the
        # camera edge, hold for a few seconds, and despawn the
        # instant the player either looks toward them (camera centres
        # on them) or steps too close.
        # Each entry is a dict: {x, y, t_left, fade}.
        self._watchers = []
        # Schedule the next watcher spawn (seconds). Independent of
        # the Pursuer schedule -- watchers are observation, the
        # Pursuer is closure.
        self._watcher_next_t = 14.0
        # Track scenes the player has visited; watcher spawn rate
        # increases per visit count.

        # ---- THRESHOLD: cult patrols ----
        # Multiple cult members teleport through the outdoor scenes,
        # scaling with Pursuer proximity. Each entry is a dict that
        # tracks its own current scene and re-roll timer. Patrols
        # whose `min_prox` is above current proximity stay dormant.
        # When active, they chase the player on sight.
        self._sheriff_scenes = (
            "village", "forest_path", "our_house_area",
            "graveyard", "diner_gas_station", "mistlands",
            "country_lane",
            "gravel_road_north", "river_crossing",
            "backwoods_cabin",
            "cornfield_maze",
        )
        self._patrols = [
            # The Preacher: emerges from the church at proximity >=
            # 0.40. He used to be church-bound; once the cult is
            # mobilising, he walks the road too. Slowest of the
            # human patrols -- the player should read his silhouette
            # as a deliberate, unhurried walker.
            {"tag": "patrol_preacher", "name": "Preacher",
             "kind": "old", "min_prox": 0.40,
             "scene": None, "t": 45.0,
             "next_min": 40.0, "next_max": 75.0,
             "speed": 0.55},
            # A generic cultist: appears at proximity >= 0.65. The
            # town's other adults coming out to look for the
            # outsider. Uses the bandit sprite as a cult-robe stand-
            # in (hood, dim eyes).
            {"tag": "patrol_cultist", "name": "Cultist",
             "kind": "bandit", "min_prox": 0.65,
             "scene": None, "t": 70.0,
             "next_min": 25.0, "next_max": 50.0},
            # The Hunter -- the King in Yellow avatar. Activates at
            # proximity >= 0.30. Walks DIRECTLY at the player (no
            # scout phase) regardless of distance, force-chasing
            # through walls of the player's scene. Catches scale
            # with proximity: standard 22 px contact at low/mid,
            # 60 px reach at apex (>= 0.85) where any catch is the
            # closure ending. Uses the yellow_king sprite (alpha-
            # pulse, mass of eyes).
            {"tag": "patrol_hunter", "name": "",
             "kind": "yellow_king", "min_prox": 0.95,
             "scene": None, "t": 50.0,
             "next_min": 30.0, "next_max": 55.0,
             "speed": 0.55},
            # The Choir: a procession of cult children walking in
            # formation, humming. Activates at mid proximity.
            # Slow, but unsettling -- the player sees a kid
            # silhouette and has half a second to decide if it's
            # the trustworthy kid or one of THEM. Uses the `kid`
            # sprite kind so the silhouette ambiguity is real.
            {"tag": "patrol_choir", "name": "",
             "kind": "kid", "min_prox": 0.50,
             "scene": None, "t": 60.0,
             "next_min": 35.0, "next_max": 70.0,
             "speed": 0.55},
            # The Hound: a cult dog (`wolf` sprite). Activates at
            # high proximity, faster than the human patrols, and
            # closes the distance hard once spotted. Forces the
            # player to break for cover earlier.
            {"tag": "patrol_hound", "name": "",
             "kind": "wolf", "min_prox": 0.70,
             "scene": None, "t": 55.0,
             "next_min": 25.0, "next_max": 50.0,
             "speed": 1.35},
            # Ambient hooded cultists -- always-active, restricted
            # to the forest walkways. Three slots so the player
            # usually encounters 1-2 in any forest scene at once.
            # Bandit sprite (hood + dim eyes). The chaser AI's
            # scout-mode wandering means they look like searchers
            # rather than homing missiles -- they pick a tile,
            # walk there, look around, repeat. Spotting the
            # player (within 180 px, not hidden) flips them to
            # chase exactly like the named cultist patrol.
            {"tag": "patrol_amb_cult_a", "name": "",
             "kind": "bandit", "min_prox": 0.0,
             "scene": None, "t": 5.0,
             "next_min": 25.0, "next_max": 50.0,
             "speed": 0.8,
             "scenes": ("forest_path", "cornfield_maze")},
            {"tag": "patrol_amb_cult_b", "name": "",
             "kind": "bandit", "min_prox": 0.0,
             "scene": None, "t": 14.0,
             "next_min": 30.0, "next_max": 60.0,
             "speed": 0.8,
             "scenes": ("forest_path", "cornfield_maze")},
            {"tag": "patrol_amb_cult_c", "name": "",
             "kind": "bandit", "min_prox": 0.0,
             "scene": None, "t": 22.0,
             "next_min": 35.0, "next_max": 70.0,
             "speed": 0.8,
             "scenes": ("forest_path", "cornfield_maze")},
        ]
        # Notice flag set the first time each higher-tier patroller
        # activates so the player gets a single "more of them are
        # out" beat.
        self._patrol_announced = set()

        # ---- THRESHOLD: Kid follower ----
        # When the player picks Yes at kid visit 7, this flag flips
        # on. The kid then spawns as a 'follower' NPC in every
        # scene the player loads. Follower presence applies a 15%
        # walk-speed reduction AND pauses Pursuer proximity ramp
        # (the Ire was promised the kid; it pauses when the kid is
        # visibly with the player).
        self._kid_follower_active = False

        # ---- THRESHOLD: flashback ----
        # Set when the player reads page 3 of Mom's notebook.
        # _flashback_phase tracks which still is showing. None means
        # no flashback active. Each phase shows a single line of
        # text on a black overlay for ~1.6 seconds.
        self._flashback_phase = None
        self._flashback_t = 0.0
        # The flashback stills, in order. Last one is the gut-punch.
        self._flashback_stills = [
            ("the clearing.", 1.6),
            ("robed figures around a fire.", 1.6),
            ("a cast-iron cauldron, steaming.", 1.6),
            ("a man held face-down in the water.", 2.0),
            ("the Innkeeper's face turning to look at you.", 3.0),
        ]

        # ---- THRESHOLD: ending state ----
        # _ending_active is the name of the ending currently
        # playing (or None). _ending_phase / _ending_phase_t walk
        # through the ending's stills.
        self._ending_active = None
        self._ending_phase = 0
        self._ending_phase_t = 0.0

    # ---- TITLE ----
    def draw_title(self):
        """Stark title. Black field with a slow noise grain, the word
        THRESHOLD held still in the centre, options below in a quiet
        column. No music other than the wind drone -- if the player
        sits on this screen, all they hear is the wind. The title text
        breathes very slightly (1px vertical drift on a 6-second
        period) so the screen never feels frozen, but never feels
        alive either."""
        t = pygame.time.get_ticks() / 1000.0
        self.screen.fill((4, 3, 7))
        # Slow grain: a sparse field of single-pixel noise that drifts
        # imperceptibly. Just enough to keep the screen from looking
        # like a static frame.
        grain_seed = int(t * 6) & 0xFFFF
        for i in range(200):
            n = (i * 9931 + grain_seed * 17) & 0xFFFFFF
            sx = n % SCREEN_W
            sy = (n >> 8) % SCREEN_H
            v = 14 + ((n >> 16) & 0x1F)
            self.screen.set_at((sx, sy), (v, v, v + 4))
        # The title itself. Held dead centre, no shake, no colour
        # cycling. Letter-spacing widened so the word reads as a slab
        # rather than a friendly logo.
        title_text = "T H R E S H O L D"
        title_font = self.fonts["title"]
        title_surf = title_font.render(title_text, True, (170, 168, 174))
        # 1px vertical breath, very slow.
        breath = int(math.sin(t * 1.05) * 1)
        tx = SCREEN_W // 2 - title_surf.get_width() // 2
        ty = 180 + breath
        # A faint shadow, no offset bounce.
        shadow = title_font.render(title_text, True, (0, 0, 0))
        self.screen.blit(shadow, (tx + 2, ty + 2))
        self.screen.blit(title_surf, (tx, ty))
        # No subtitle. Negative space below the word.
        opts = self._title_menu_options()
        # Clamp the cursor in case the option list shrank (e.g. the
        # player hit Delete Save while highlighting it -- the slot
        # stays valid but the label flipped).
        if self.title_choice >= len(opts):
            self.title_choice = len(opts) - 1
        for i, opt in enumerate(opts):
            if opt == "Continue" and not self.save.exists():
                color = (50, 48, 56)
            elif i == self.title_choice:
                color = (220, 218, 226)
            else:
                color = (96, 92, 104)
            txt = self.fonts["lg"].render(opt, True, color)
            tx2 = SCREEN_W // 2 - txt.get_width() // 2
            ty2 = 360 + i * 44
            if i == self.title_choice:
                # A single small bracket on the left only -- asymmetric,
                # never resolves to a neat selector.
                marker = self.fonts["lg"].render("[", True, (220, 218, 226))
                self.screen.blit(marker, (tx2 - 24, ty2))
            self.screen.blit(txt, (tx2, ty2))
        hint = self.fonts["sm"].render(
            "arrow keys . enter . F11", True, (60, 58, 68))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2,
                                SCREEN_H - 28))

    def _title_menu_options(self):
        """Compute the title-screen menu fresh on every read. The
        middle slot is 'Delete Save' when a save file exists and
        'New Save' when it doesn't -- so the user can't accidentally
        overwrite an existing run with one keypress. Deleting the
        save flips the label to 'New Save' on the next render; a
        second confirm starts the new run."""
        middle = "Delete Save" if self.save.exists() else "New Save"
        return ["Continue", middle, "Quit"]

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
            if opt == "Continue":
                if not self.save.exists():
                    self.audio.play("cancel", 0.7); return
                self.save.load()
                self.audio.play("confirm", 0.8)
                self._start_play()
            elif opt == "Delete Save":
                # Two-step flow: deletion only. Stay on the menu;
                # the next render will show "New Save" in this
                # slot, and the player has to confirm again to
                # actually start a new run.
                self.save.delete()
                self.audio.play("menu_close", 0.6)
            elif opt == "New Save":
                self.save.new()
                self.audio.play("confirm", 0.8)
                self._start_play()
            elif opt == "Quit":
                pygame.quit(); sys.exit(0)

    def _toggle_flashlight(self):
        """F-key handler. Flips the flashlight on/off if the player
        has it in inventory AND battery > 0. Plays a soft click. If
        the player has no flashlight, surfaces the lack. The
        flashlight does not work in CULT_DARK_SCENES -- the bulb
        flickers and dies on contact with the rite."""
        if not self.player.inventory.has("flashlight"):
            self.show_notice("You don't have a flashlight.")
            self.audio.play("cancel", 0.4)
            return
        if self.scene is not None and self.scene.key in CULT_DARK_SCENES:
            self.player.flashlight_on = False
            self.audio.play("static", 0.35)
            self.show_notice("The bulb flickers. It will not light.")
            return
        if self.player.battery_charge <= 0 and not self.player.flashlight_on:
            self.show_notice("The batteries are dead.")
            self.audio.play("cancel", 0.4)
            return
        self.player.flashlight_on = not self.player.flashlight_on
        self.audio.play("blip_soft", 0.45)

    def _tick_flashlight(self, dt):
        """Drain the battery while the flashlight is on. When the
        battery hits zero, force the flashlight off and surface a
        diegetic notice -- the player has to find / use spare
        batteries to relight."""
        if not self.player:
            return
        if not self.player.flashlight_on:
            return
        self.player.battery_charge = max(
            0.0, self.player.battery_charge - dt * 1.0
        )
        if self.player.battery_charge <= 0:
            self.player.flashlight_on = False
            self.show_notice("The flashlight dies.")
            self.audio.play("static", 0.35)

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
        self.player = Player(0, 0)
        self.player.from_save(self.save.data)
        self.load_scene_now(self.save.data.get("scene", "bedroom"),
                             self.save.data.get("spawn", "default"))
        self.state = "playing"

    def _reset_run_state(self):
        """Wipe all per-run horror state so a new save load starts
        clean. Anything not persisted to disk that would otherwise
        leak between save files belongs here."""
        # Kid follower + trailer
        self._kid_follower_active = False
        self._trailer_hide_until = 0.0
        # Pursuer
        self.pursuer_proximity = 0.0
        self.dread_aperture = 1.0
        self._last_pos = (0.0, 0.0)
        self._chant_t = 0.0
        self._breath_t = 0.0
        self._pursuer_next_event = 8.0
        self._pursuer_t = 0.0
        self._pursuer_last_event = ""
        self._pursuer_closure_t = -1.0
        self._heartbeat_t = 0.0
        self._apex_silhouette_t = 0.0
        self._visibility_dip_t = 0.0
        self._pursuer_last_notice = ""
        # Watchers
        self._watchers = []
        self._watcher_next_t = 14.0
        # Cult patrols -- reset each entry's scene + countdown to its
        # initial spawn timer. The list itself stays (NPC kinds /
        # min_prox thresholds are static config, not run state).
        for p in self._patrols:
            p["scene"] = None
            p["t"] = {"patrol_preacher": 45.0,
                      "patrol_cultist": 70.0,
                      "patrol_hunter": 50.0,
                      "patrol_choir": 60.0,
                      "patrol_hound": 55.0,
                      "patrol_amb_cult_a": 5.0,
                      "patrol_amb_cult_b": 14.0,
                      "patrol_amb_cult_c": 22.0}.get(p["tag"], 30.0)
        self._patrol_announced = set()
        # Ambient cues
        self._humming_t = 12.0
        self._giant_eye_t = -1.0
        self._giant_eye_phase = 0.0
        self._giant_eye_pos = (0, 0)
        self._visitor_silence = False
        self._void_sting_played = False
        self._orb_whisper_t = 4.0
        # Stillness + heartbeat
        self.stillness_t = 0.0
        self._next_heartbeat_t = 0.0
        self._heartbeat_count = 0
        self._delayed_audio = []
        self._creepy_step_count = 0
        # Flashback / ending state
        self._flashback_phase = None
        self._flashback_t = 0.0
        self._ending_active = None
        self._ending_phase = 0
        self._ending_phase_t = 0.0
        self._closure_locked = False
        # Pursuer-glimpse
        self._glimpse_t = 0.0
        self._glimpse_pos = (0, 0)
        # Opening wake state. When the bedroom_on_enter fires for
        # the first session it sets these to non-zero values; the
        # _tick_wake_muffle ticker then dampens the music channel
        # and pulses the "heartbeat" SFX while the player's head is
        # still pounding. Decays to 0 over ~8 seconds.
        self._wake_muffle_t = 0.0
        self._wake_muffle_max = 8.0
        self._wake_heartbeat_t = 0.0
        # Save-as-ritual state. None when awake; a phase string
        # ("lay_down" | "fade_out" | "hold_black" | "fade_in") while
        # the player is asleep at the cot. Phase durations are in
        # `_SLEEP_PHASE_DURS` below. While sleeping, all input is
        # locked, the world doesn't tick, the player sprite renders
        # prone on the cot, and a black overlay fades in/out.
        self._sleep_phase = None
        self._sleep_t = 0.0
        self._sleep_save_done = False

    # ---- Scene management ----
    def begin_transition(self, target_scene, spawn_id="default"):
        if self.state == "transition": return
        # THRESHOLD: front-door confrontation. If the player is
        # leaving the Innkeeper's house ('house' -> 'our_house_area')
        # AND they have any cult evidence in inventory AND haven't
        # been confronted yet, the Innkeeper blocks the door. The
        # transition is cancelled, a confrontation dialog fires, and
        # the front door is sealed for this run.
        if self._check_innkeeper_confrontation(target_scene):
            return
        if (target_scene == "basement"
                and not self.player.inventory.has("cellar_key")):
            self.audio.play("door_locked", 0.5)
            self.show_notice("The hatch is padlocked.", duration=2.0)
            return
        # Every transition buys the player a beat -- the Pursuer
        # loses ground when the door closes between rooms.
        # Caps at 0.0; never affects the closure countdown itself
        # (once that's armed the door doesn't help anymore).
        if self._pursuer_closure_t < 0:
            self.pursuer_proximity = max(0.0,
                                          self.pursuer_proximity - 0.04)
        else:
            # Closure armed: each transition adds a small reprieve to
            # the countdown so the player can flee through a few
            # doors before it ends, but never escape it.
            self._pursuer_closure_t += 6.0
        # Round-9: the forest secret-tree -> void_boss redirect was
        # removed. The forest j-tile now leads to the original empty
        # void (easter_egg + rust_key). The void_boss arena is reached
        # via a conditional fake stone wall in the bandit_cave_boss
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

    def _check_kill_evidence(self):
        """Fire substrate-voice evidence beats keyed off the hidden
        kill counters. Each beat is one-shot via _evidence's per-name
        flag. The Visitors are watching the player's behavior and
        counting -- the player never sees the count, just the notes
        the Visitors leave when the count crosses thresholds."""
        from scenes.dialogue import _evidence
        if self.save is None:
            return
        n = self.save.arg("enemy_kills", 0)
        nh = self.save.arg("nonhostile_kills", 0)
        an = self.save.arg("animal_kills", 0)
        if n >= 5:
            _evidence(self, "kill_count_5",
                "five so far.\n"
                "we are keeping count."
            )
        if n >= 15:
            _evidence(self, "kill_count_15",
                "he likes this.\n"
                "give him more."
            )
        if nh >= 1:
            _evidence(self, "first_nonhostile",
                "the first one is the hardest.\n"
                "it was not.\n"
                "he did not even pause."
            )
        if nh >= 3:
            _evidence(self, "asked_for_three",
                "we asked for three.\n"
                "he gave us three.\n"
                "and the others. we did not ask for the others."
            )
        if an >= 4:
            _evidence(self, "animal_count",
                "the dogs were tired before he started.\n"
                "they are not tired now."
            )

    def load_scene_now(self, key, spawn_id="default"):
        if self.scene and self.scene.on_exit_fn:
            self.scene.on_exit_fn(self, self.scene)
        self.scene = load_scene(key)
        self.save.visit_scene(key)
        self.save.data["spawn"] = spawn_id
        spawn = self.scene.spawns.get(spawn_id, self.scene.spawns.get("default"))
        if spawn:
            self.player.x, self.player.y = spawn
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
        # Capture the entry tile for the Hunter's door-block target.
        # The player just walked in through this tile; the avatar
        # routes here to cut off retreat. Tile coords (tx, ty) so
        # _yk_pick_target's BFS in tile-space can target it directly.
        # Stashed on the Scene so npc.update can read it without a
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
        self._update_camera(snap=True)
        if not self.audio.music_muted:
            self.audio.play_music(self.scene.music)
        else:
            self.audio.stop_music()
        if self.scene.on_enter_fn:
            self.scene.on_enter_fn(self, self.scene)
        # Capture-trace deposits. Each deposit corresponds to one
        # non-closure capture the player has survived; the world
        # keeps the receipt. Drop in any deposit whose scene matches
        # the one we just loaded and whose index is below the
        # accumulated count.
        from entities.decoration import Decoration
        n_traces = self.save.arg("capture_traces", 0)
        for idx, (key, tx, ty, kind) in enumerate(CAPTURE_TRACE_DEPOSITS):
            if idx >= n_traces:
                break
            if key != self.scene.key:
                continue
            self.scene.add_decoration(
                Decoration(tx * TILE + 16, ty * TILE + 16, kind)
            )
        # Outdoor decay: re-apply tier-additive decorations every
        # load so a scene visibly worsens as the line tightens.
        # Pulls from OUTDOOR_DECAY by (scene_key, tier).
        from systems.threat import (proximity_tier,
                                     PROX_TIER_MID, PROX_TIER_HIGH)
        tier = proximity_tier(self.pursuer_proximity)
        if tier in (PROX_TIER_MID, PROX_TIER_HIGH):
            extras = OUTDOOR_DECAY.get((self.scene.key, tier), [])
            for tx, ty, kind in extras:
                self.scene.add_decoration(
                    Decoration(tx * TILE + 16, ty * TILE + 16, kind)
                )
        # Persist axe chops across re-entries: any '*' debris, 'q'
        # boarded panel, or 'K' loot crate that was chopped in a
        # previous session has its tile opened. Crates do NOT re-
        # drop their loot on subsequent loads -- the broken-flag
        # gates both the tile state AND the loot spawn.
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
                elif ch == "K":
                    if self.save.flag(
                            f"crate_broken_{self.scene.key}_{tx}_{ty}"):
                        self.scene.objects[ty][tx] = "."
        # Round-9: dying to the alien boss empties the world. Every
        # scene loaded after `world_emptied` is set has its NPC list
        # cleared post-on_enter, so any villagers / shopkeep / kid /
        # innkeeper / guard / terminal handler placed by the builder or
        # on_enter fn is removed before the player sees the scene. The
        # world keeps its layouts and items, just no people.
        if self.save.flag("world_emptied"):
            self.scene.npcs = []
        self._check_kill_evidence()
        # Schedule a Pursuer glimpse at very high proximity. After a
        # scene transition lands and the player gets oriented, a
        # tall_shadow flashes briefly at a screen edge -- the
        # following thing is suddenly almost in the room with you.
        if self.pursuer_proximity > 0.85:
            self._glimpse_t = 0.18
            edge = random.choice(("left", "right"))
            gx = 24 if edge == "left" else SCREEN_W - 24
            gy = SCREEN_H // 2 + random.randint(-40, 40)
            self._glimpse_pos = (gx, gy)
        else:
            self._glimpse_t = 0.0

    def _river_blocks(self, target_x, target_y):
        """Custom passability for the mistlands river. The `~` floor is
        non-solid by default, so this is the gate: in any other scene
        it's a no-op, and in the mistlands a `~` tile is walkable only
        if (a) the player is already in the river, OR (b) the target
        tile is the designated entry tile. Falling-back-into-the-river
        from land or bridge is blocked everywhere else."""
        if self.scene is None or self.scene.key != "mistlands":
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
        scene_w = self.scene.w * Scene.TILE
        scene_h = self.scene.h * Scene.TILE
        target_x = max(0, min(scene_w - SCREEN_W, target_x))
        target_y = max(0, min(scene_h - SCREEN_H, target_y))
        if scene_w < SCREEN_W:
            target_x = (scene_w - SCREEN_W) // 2
        if scene_h < SCREEN_H:
            target_y = (scene_h - SCREEN_H) // 2
        if snap:
            self.cam_x = target_x; self.cam_y = target_y
        else:
            self.cam_x += (target_x - self.cam_x) * 0.18
            self.cam_y += (target_y - self.cam_y) * 0.18

    # ---- Player update ----
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
            self.player.facing = (dx, dy)
            self.player.walk_phase += dt * 12
            # THRESHOLD: base speed is reduced by Pursuer proximity
            # (spatial compression), boosted by active sprint, and
            # reduced 15% if the kid follower is active (he can't
            # keep up with full pace).
            comp_mult = 1.0 - self.pursuer_proximity * 0.45
            sprint_mult = 1.7 if self.player.sprint_active else 1.0
            follower_mult = 0.85 if self._kid_follower_active else 1.0
            effective_speed = (self.player.speed
                               * comp_mult * sprint_mult * follower_mult)
            new_x = self.player.x + dx * effective_speed * dt
            new_y = self.player.y + dy * effective_speed * dt
            blocked_x = (self.scene.is_solid_at(new_x, self.player.y)
                         or self._river_blocks(new_x, self.player.y))
            blocked_y = (self.scene.is_solid_at(self.player.x, new_y)
                         or self._river_blocks(self.player.x, new_y))
            moved = False
            if not blocked_x: self.player.x = new_x; moved = True
            if not blocked_y: self.player.y = new_y; moved = True
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
        self.player.attack_timer = max(0, self.player.attack_timer - dt)
        self.player.swing_t = max(0, self.player.swing_t - dt)
        self.player.invuln = max(0, self.player.invuln - dt)
        if self.player.charging:
            self.player.charge_t = min(2.0, self.player.charge_t + dt)
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
                if key in self.CULT_EVIDENCE_KEYS:
                    self._provoke_cult(0.10)

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
                "behind":"you crouch behind it.",
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
            sc_ = self.scene
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                tx = int((self.player.x + dx * TILE) // TILE)
                ty = int((self.player.y + dy * TILE) // TILE)
                if 0 <= ty < sc_.h and 0 <= tx < sc_.w:
                    ch = sc_.objects[ty][tx]
                    if ch == "*":
                        is_west_edge = (tx == 0)
                        sc_.objects[ty][tx] = "4" if is_west_edge else "."
                        self.audio.play("hit", 0.8)
                        self.audio.play("bump", 0.5)
                        self.save.set_flag(
                            f"debris_broken_{sc_.key}_{tx}_{ty}", True)
                        self.show_notice("The pile splinters apart.")
                        return
                    if ch == "q":
                        sc_.objects[ty][tx] = "."
                        self.audio.play("hit", 0.85)
                        self.audio.play("bump", 0.55)
                        self.save.set_flag(
                            f"boards_broken_{sc_.key}_{tx}_{ty}", True)
                        self.show_notice("The boards splinter away.")
                        return
                    if ch == "K":
                        # Hand-authored loot crate. Splinter the
                        # tile and drop the item from CRATE_LOOT
                        # at the player's feet so they pick it up
                        # on the next step. Persisted via
                        # `crate_broken_<scene>_<tx>_<ty>`.
                        sc_.objects[ty][tx] = "."
                        self.audio.play("hit", 0.85)
                        self.audio.play("bump", 0.6)
                        self.save.set_flag(
                            f"crate_broken_{sc_.key}_{tx}_{ty}", True)
                        loot = CRATE_LOOT.get((sc_.key, tx, ty))
                        if loot:
                            sc_.add_item(
                                tx * TILE + 16, ty * TILE + 16,
                                loot,
                            )
                            from systems.items import ITEM_DEFS
                            name = ITEM_DEFS.get(loot, {}).get("name", loot)
                            self.show_notice(
                                f"The crate splinters open. {name}.")
                        else:
                            self.show_notice(
                                "The crate splinters open. Empty.")
                        return
        # Standard NPC interaction
        best = None; bd = 1e9
        for npc in self.scene.npcs:
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
        # The line varies by scene + day_phase so the world feels
        # reactive across days. Checks the four cardinal-adjacent
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
        """Press an ear to a closed door. Plays a soft door tap and
        shows a one-line muffled overhear. Content keyed by current
        scene + day_phase. Locked doors ('z') stay locked -- the
        listen is a SECOND option on top of the locked feedback."""
        phase = self.save.arg("day_phase", "afternoon")
        # Per-scene line picks. Each entry maps phase -> line.
        # Falls back to a generic listen line for scenes without
        # bespoke content.
        per_scene = {
            "village": {
                "morning":  "Two voices arguing inside. They stop.",
                "afternoon":"Someone is sweeping. They stop.",
                "dusk":     "A chair scrapes. Then nothing.",
                "night":    "Low chanting, very faint. You cannot make out words.",
            },
            "old_man_house": {
                "morning":  "The Preacher is reading aloud. It isn't English.",
                "afternoon":"A chair creaking. A cough.",
                "dusk":     "Someone weeping, briefly.",
                "night":    "Many voices in unison. You back away.",
            },
            "shop": {
                "morning":  "The shopkeep humming. The village melody.",
                "afternoon":"Coins being counted. Slowly.",
                "dusk":     "The radio: static, then a name. Yours.",
                "night":    "Nothing. But the door is warm.",
            },
            "kid_house": {
                "morning":  "The Kid talking to himself. Or to someone.",
                "afternoon":"The Kid drawing. Pencil on paper.",
                "dusk":     "The Kid is silent. You can hear him breathing.",
                "night":    "The Kid is asleep. Someone else is in there too.",
            },
            "diner_gas_station": {
                "morning":  "An old radio, tuned between stations.",
                "afternoon":"A fly on the inside of the glass.",
                "dusk":     "A radio voice reads names. Not a station you know.",
                "night":    "Footsteps inside. There shouldn't be.",
            },
            "haunted_house": {
                "morning":  "Wind. Nothing else.",
                "afternoon":"Floorboards settling. A long pause.",
                "dusk":     "Humming. A child. Or close to one.",
                "night":    "The cauldron is not in there. But you can smell the smoke.",
            },
            "locked_house": {
                "morning":  "Nothing.",
                "afternoon":"A clock ticking. Faintly.",
                "dusk":     "Someone breathing. Close to the door.",
                "night":    "Two people whispering. One says your name.",
            },
        }
        defaults = {
            "morning":  "Nothing on the other side.",
            "afternoon":"You press your ear to the door. Quiet.",
            "dusk":     "Muffled movement. Then silence.",
            "night":    "Breathing on the other side. You step back.",
        }
        lines = per_scene.get(scene_key, defaults)
        line = lines.get(phase, defaults[phase])
        self.audio.play("door_locked", 0.35)
        self.audio.play("breath", 0.30)
        # Locked-house door (z) keeps the locked stinger -- listen
        # is supplementary, not a replacement.
        if ch == "z":
            self.show_notice("Locked. " + line, duration=3.0)
        else:
            self.show_notice(line, duration=3.0)

    # ---- Combat ----
    def player_start_charge(self):
        """Press attack input. Begins a charge; the actual swing fires
        on release (release_charge). No SFX here -- the swing sound
        plays at release so a tap and a charged release both feel like
        single discrete attacks."""
        self.player.start_charge()

    def player_release_charge(self):
        """Release attack input. Routes to the right SFX (and spawns a
        projectile for pistol). Pistol fires a bullet in player.facing;
        bare-fist and melee weapons keep the swing animation. A
        charged lumber_axe also tries to break adjacent debris in the
        facing direction."""
        result = self.player.release_charge()
        if result is None:
            return
        if result == "shoot":
            self.audio.play("pistol_shot", 0.6)
            self._spawn_player_bullet()
        else:
            self.audio.play("swing", 0.6)
        if (result == "swing_charged"
                and self.player.inventory.equipped["weapon"] == "lumber_axe"):
            self._try_break_debris()
        if (result in ("swing", "swing_charged")
                and self.player.inventory.equipped["weapon"] == "fishing_pole"
                and self.player.in_river):
            self._try_fish()

    def _try_fish(self):
        """Fishing-pole roll. 50% nothing, 35% small_fish, 15% big_fish.
        Only fires when the player is standing in the mistlands river
        (gated by player.in_river)."""
        r = random.random()
        if r < 0.50:
            self.show_notice("Nothing on the line.")
            return
        if r < 0.85:
            self.player.inventory.add("small_fish", 1)
            self.audio.play("pickup", 0.7)
            self.show_notice("Caught: Small Fish.")
        else:
            self.player.inventory.add("big_fish", 1)
            self.audio.play("pickup_rare", 0.7)
            self.show_notice("Caught: Big Fish.")

    def _try_break_debris(self):
        """If a debris ('*') tile sits in front of the player along
        their facing direction (within ~one tile), promote it to '4'
        (the village->mistlands exit char) and play a chunky impact.
        Persisted via per-coord save flag so the gap stays open
        across re-entries. Edge-of-map debris doubles as the exit
        tile once broken; debris elsewhere just becomes walkable."""
        sc = self.scene
        if sc is None:
            return
        fx, fy = self.player.facing
        for r in (TILE, TILE * 1.5):
            tx = int((self.player.x + fx * r) // TILE)
            ty = int((self.player.y + fy * r) // TILE)
            if 0 <= ty < sc.h and 0 <= tx < sc.w:
                if sc.objects[ty][tx] == "*":
                    is_west_edge = (tx == 0)
                    sc.objects[ty][tx] = "4" if is_west_edge else "."
                    self.audio.play("hit", 0.8)
                    self.audio.play("bump", 0.5)
                    self.save.set_flag(f"debris_broken_{sc.key}_{tx}_{ty}", True)
                    self.show_notice("The pile splinters apart.")
                    return

    def _spawn_player_bullet(self):
        """Spawn a Projectile in the player's facing direction with the
        equipped pistol's atk as damage. Lives in the same projectiles
        list as enemy shots, but `friendly=True` flips collision so it
        damages enemies instead of the player."""
        from entities.enemy import Projectile
        fx, fy = self.player.facing
        dmg = self.player.inventory.weapon_atk()
        proj = Projectile(self.player.x + fx * 14,
                          self.player.y + fy * 14,
                          fx, fy, dmg=dmg,
                          color=(255, 240, 180), speed=380,
                          lifespan=0.9)
        proj.friendly = True
        self.scene.projectiles.append(proj)

    def apply_attack_damage(self):
        rect, dmg = self.player.attack_hitbox()
        if rect is None: return
        for e in self.scene.enemies:
            if not e.alive: continue
            er = pygame.Rect(0, 0, 22, 22)
            er.center = (int(e.x), int(e.y))
            if rect.colliderect(er):
                e.hp -= dmg
                e.flash = 0.12
                self.audio.play("hit", 0.55)
                if e.hp <= 0 and e.alive:
                    self._kill_enemy(e)
        # Round-14: NPCs are also valid targets. Killing them feeds
        # the hidden kill counter and triggers their on_kill (e.g.
        # the fisherman drops three big_fish). The substrate notices.
        for n in list(self.scene.npcs):
            if not getattr(n, "alive", True):
                continue
            nr = pygame.Rect(0, 0, 22, 22)
            nr.center = (int(n.x), int(n.y))
            if rect.colliderect(nr):
                n.take_damage(dmg)
                self.audio.play("hit", 0.55)
                if not n.alive and not getattr(n, "_kill_processed", False):
                    n._kill_processed = True
                    self._kill_npc(n)

    def _kill_npc(self, npc):
        """Side-effects of an NPC kill: increment the hidden non-hostile
        counter (the substrate watches this), play the death SFX, drop
        any items the NPC was carrying, and fire on_kill if present.
        The NPC is removed from the scene's list on the next step."""
        self.audio.play("enemy_die", 0.55)
        n = self.save.arg("nonhostile_kills", 0) + 1
        self.save.set_arg("nonhostile_kills", n)
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

    def _kill_enemy(self, e):
        """Run the death side-effects for `e`: marks dead, plays the
        death SFX, rolls drops (85% suppressed for respawning enemies),
        and fires on_kill. Called from melee and friendly-projectile
        paths so a pistol kill awards drops/on_kill the same way a
        sword kill does. Increments the kill counter, which the
        substrate references in late-game evidence files."""
        e.alive = False
        self.audio.play("enemy_die", 0.6)
        kind = getattr(e, "kind", "")
        if kind == "wolf":
            arg = "animal_kills"
        else:
            arg = "enemy_kills"
        self.save.set_arg(arg, self.save.arg(arg, 0) + 1)
        # Respawning combat enemies (forest_path bandits, cave bandits,
        # easter_egg_room mob set) drop nothing 85% of the time.
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

    def _draw_mistlands_haze(self):
        """Atmospheric overlay. Mistlands and alter_room always run the
        outdoor haze + vignette. EVERY OTHER SCENE also runs the
        outdoor haze + vignette while the player is carrying the
        orb -- the orb's presence is hostile, the world dims around
        it."""
        if self.scene is None:
            return
        key = self.scene.key
        # Safe / dim-safe interiors break the orb-haze. Walking
        # back to the Inn (or the cellar) with the orb is meant
        # to feel like a refuge from the hostile dim, not a
        # continuation of it.
        if key in SAFE_SCENES or key in DIM_SAFE_SCENES:
            return
        holds_orb = (self.player is not None
                     and self.player.inventory.has("orb"))
        if key in ("mistlands", "alter_room") or holds_orb:
            self._draw_haze(170, (40, 40, 50, 80), 14, 24, 0.3, 30)
            self._draw_vignette()

    def _draw_child_trailer(self):
        """Render a small kid sprite ~2 tiles BEHIND the player (in
        the direction opposite their facing). Only fires in
        CREEPY_SCENES. If the player rotates to face the trailer
        (i.e. turns around), it disappears for 3 seconds, so the
        player can never actually look at it head-on.

        World-space draw, so the trailer is at a believable physical
        offset rather than a fixed screen offset."""
        if self.scene is None or self.scene.key not in CREEPY_SCENES:
            return
        now = pygame.time.get_ticks() / 1000.0
        if now < self._trailer_hide_until:
            return
        fx, fy = self.player.facing
        # Player's "behind" direction is opposite their facing. Place
        # the trailer two tiles behind, slightly offset.
        bx = self.player.x - fx * (TILE * 2.2)
        by = self.player.y - fy * (TILE * 2.2)
        # World-to-screen
        sx = int(bx - self.cam_x)
        sy = int(by - self.cam_y)
        if sx < -32 or sx > SCREEN_W + 32 or sy < -32 or sy > SCREEN_H + 32:
            return
        # Detect "looking at" the trailer: if the player's facing dot
        # the trailer-direction is positive, they're rotating toward
        # it. (We compute trailer-direction = bx-px, by-py = -fx*..,
        # and `dot(facing, trailer_dir) = -1` means facing away.)
        # We only hide when the player turns to face it -- player's
        # facing roughly aligns with the trailer's direction-from-
        # player. If the player walks backwards (facing toward the
        # trailer), it should hide.
        # Simpler heuristic: the trailer is always BEHIND, so it's
        # always anti-aligned with facing. If the player's last move
        # direction is anti-parallel (player walked backwards toward
        # it) -- skip detection complexity, just hide on any direction
        # change toward the trailer's tile.
        # Render: a static pale-skin small kid silhouette, no facing.
        draw_npc_sprite(self.screen, sx, sy, "kid", (0, -1))
        # Add a faint dim overlay so it doesn't read as a real NPC.
        dim = pygame.Surface((30, 36), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 60))
        self.screen.blit(dim, (sx - 15, sy - 24))

    def _draw_giant_eye(self):
        """A massive eye fades in over the haze for ~2.5 seconds at
        random rare intervals (every 30-90s while in mistlands or
        alter_room). Pupil tracks the player. Fades out without
        comment. The player either sees it or convinces themselves
        they didn't. The Visitors are watching from above the haze."""
        if self.scene is None or self.scene.key not in (
                "mistlands", "alter_room"):
            self._giant_eye_t = -1.0
            self._giant_eye_phase = 0.0
            return
        # Schedule next appearance
        if self._giant_eye_t < 0:
            self._giant_eye_t = random.uniform(20.0, 50.0)
            self._giant_eye_phase = 0.0
            return
        if self._giant_eye_phase > 0:
            # Currently visible -- count down phase, fade in/out.
            self._giant_eye_phase -= 1.0 / 60.0
            if self._giant_eye_phase <= 0:
                self._giant_eye_phase = 0.0
                self._giant_eye_t = random.uniform(30.0, 90.0)
                return
            self._render_giant_eye(self._giant_eye_phase)
        else:
            self._giant_eye_t -= 1.0 / 60.0
            if self._giant_eye_t <= 0:
                # Trigger appearance
                self._giant_eye_phase = 2.5
                # Pick a screen quadrant for placement (random each fire)
                self._giant_eye_pos = (
                    random.randint(SCREEN_W // 4, SCREEN_W * 3 // 4),
                    random.randint(SCREEN_H // 4, SCREEN_H // 2),
                )

    def _render_giant_eye(self, phase):
        """Draw the giant eye at self._giant_eye_pos with alpha
        ramping in and out across the 2.5s phase. The pupil rotates
        toward the player on screen."""
        # Fade: 0 -> max_alpha at phase=2.0 (i.e. first 0.5s), hold,
        # then fade out in the last 0.5s.
        if phase > 2.0:
            ratio = (2.5 - phase) / 0.5
        elif phase < 0.5:
            ratio = phase / 0.5
        else:
            ratio = 1.0
        alpha = max(0, min(180, int(180 * ratio)))
        if alpha <= 4:
            return
        ex, ey = self._giant_eye_pos
        sclera_r = 110
        pupil_r = 38
        # Pupil offset toward the player's screen position
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        dx = psx - ex
        dy = psy - ey
        d = math.hypot(dx, dy) or 1.0
        travel = 50
        ox = int((dx / d) * travel)
        oy = int((dy / d) * travel)
        # Build the eye on a translucent surface so we can apply
        # the fade alpha cleanly.
        layer = pygame.Surface((sclera_r * 2 + 12, sclera_r * 2 + 12),
                               pygame.SRCALPHA)
        cx, cy = sclera_r + 6, sclera_r + 6
        pygame.draw.circle(layer, (220, 215, 200, alpha),
                           (cx, cy), sclera_r)
        pygame.draw.circle(layer, (40, 30, 30, alpha),
                           (cx, cy), sclera_r, 2)
        pygame.draw.circle(layer, (60, 30, 80, alpha),
                           (cx + ox, cy + oy), pupil_r)
        pygame.draw.circle(layer, (10, 10, 14, alpha),
                           (cx + ox, cy + oy), pupil_r - 6)
        pygame.draw.circle(layer, (240, 240, 250, alpha),
                           (cx + ox - 8, cy + oy - 8), 4)
        self.screen.blit(layer, (ex - cx, ey - cy))

    def _draw_vignette(self):
        """Player-centred radial darkness. Stillness ENCROACHES: the
        clear hole shrinks as `stillness_t` grows, so a player who
        stops moving in the haze feels the dark close on them. Walking
        opens the hole back up.

        Cached: 4 vignette surfaces at different inner radii built on
        first need; one of them is picked each frame based on the
        stillness phase. Costs a single alpha-blit."""
        if self.player is None:
            return
        if self._vignette_surf is None:
            self._vignette_surf = self._build_vignette_levels()
        # Stillness phase 0 = moving (widest hole), 3 = locked-in
        # (tightest). 1.5s, 4s, 8s thresholds.
        st = self.stillness_t
        if st < 1.5:
            level = 0
        elif st < 4.0:
            level = 1
        elif st < 8.0:
            level = 2
        else:
            level = 3
        surf = self._vignette_surf[level]
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        size = surf.get_width()
        self.screen.blit(surf, (psx - size // 2, psy - size // 2))

    def _build_vignette_levels(self):
        """Four vignette surfaces at decreasing inner_r (the clear
        hole). Higher level = tighter hole = more encroachment.
        Floors raised from the prior pass -- locked-in stillness
        no longer blots the player out. Even level 3 keeps a
        ~2-tile clear radius so the player can read where they
        are while the haze closes in."""
        size = max(SCREEN_W, SCREEN_H) * 2
        surfaces = []
        # inner_r values for stillness levels 0..3 (widest -> tightest)
        for inner_r in (160, 120, 90, 70):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            cx, cy = size // 2, size // 2
            outer_r = size // 2
            steps = 60
            for i in range(steps):
                ratio = i / (steps - 1)
                r = int(outer_r - ratio * (outer_r - inner_r))
                alpha = int(230 * (1.0 - ratio))
                pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), r)
            surfaces.append(surf)
        return surfaces

    def _draw_outdoor_vignette(self):
        """Soft, always-on player-centred vignette for OUTDOOR_SCENES.
        Wider clear hole and lower peak alpha than the mistlands
        vignette -- doesn't oppress, just keeps the corners of the
        screen unsafe. Pursuer proximity tightens the hole over time:
        the world literally narrows as the threshold closes."""
        if self.scene is None or self.player is None:
            return
        if self.scene.key not in OUTDOOR_SCENES:
            return
        if self._outdoor_vignette_surf is None:
            self._outdoor_vignette_surf = self._build_outdoor_vignette()
        # Pursuer proximity selects between two cached surfaces:
        # 0 = early game (wide), 1 = late (tighter). Avoids
        # rebuilding the gradient every frame.
        level = 1 if self.pursuer_proximity > 0.55 else 0
        surf = self._outdoor_vignette_surf[level]
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        size = surf.get_width()
        self.screen.blit(surf, (psx - size // 2, psy - size // 2))

    def _build_outdoor_vignette(self):
        """Two outdoor vignette surfaces: wide hole (early game) and
        tightened hole (late game). Tuned so the player can read
        ~3-4 tiles in every direction comfortably; corners still
        press in but the cone of vision is wide enough to
        navigate. Late-game vignette tightens the hole and
        deepens the corner alpha as proximity climbs."""
        size = max(SCREEN_W, SCREEN_H) * 2
        surfaces = []
        # (inner_r, peak_alpha). 260 ~= 8-tile clear radius early;
        # 210 ~= 6.5-tile clear radius late. Peak alphas (130/165)
        # let the outer dark read as dim-but-readable rather than
        # opaque -- crucial for the post-stack visibility budget.
        for inner_r, peak in ((260, 130), (210, 165)):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            cx, cy = size // 2, size // 2
            outer_r = size // 2
            steps = 60
            for i in range(steps):
                ratio = i / (steps - 1)
                r = int(outer_r - ratio * (outer_r - inner_r))
                alpha = int(peak * (1.0 - ratio))
                pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), r)
            surfaces.append(surf)
        return surfaces

    def _draw_dusk_tint(self):
        """Proximity-driven colour tint applied across the whole screen
        for outdoor scenes. As Pursuer proximity climbs, the world
        shifts from neutral toward an oppressive blue-grey/red dusk.
        Cheap: a single SRCALPHA blit per frame. Skipped indoors
        (interiors run their own lighting through scene music)."""
        if self.scene is None or self.player is None:
            return
        if self.scene.key not in OUTDOOR_SCENES:
            return
        p = self.pursuer_proximity
        if p < 0.20:
            return
        # Tint colour interpolates from a cool dusk-blue at mid
        # proximity toward a sickly red at near-closure. The high-
        # end target is C_BLOOD so the dusk + apex palette stay in
        # the same red family instead of clashing primaries.
        t = min(1.0, (p - 0.20) / 0.75)
        r = int(20 + t * (C_BLOOD[0] - 20))
        g = int(20 + t * (C_BLOOD[1] - 20))
        b = int(40 + t * (C_BLOOD[2] - 40))
        alpha = int(40 + t * 80)   # 40 .. 120
        tint = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        tint.fill((r, g, b, alpha))
        self.screen.blit(tint, (0, 0))

    def _draw_dread_ring(self):
        """Tightening dark vignette around the player as the dread
        aperture closes. The interior stays clear so the player can
        see themselves and a small radius around them; everything
        else dims to black. No figure overlay -- the King in Yellow
        approaches as a real patrol entity, not a ring of copies."""
        if self.scene is None or self.player is None:
            return
        if self.scene.key not in DARK_SCENES:
            return
        # Safe / dim-safe interiors: no encroaching ring. Basement
        # is dark enough that the flashlight cone alone reads as
        # the gating mechanic; the dread aperture stops here.
        if (self.scene.key in SAFE_SCENES
                or self.scene.key in DIM_SAFE_SCENES):
            return
        a = self.dread_aperture
        if a >= 0.99:
            return
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        radius = int(28 + a * 232)
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        outer_alpha = int(220 * (1.0 - a))
        vignette.fill((0, 0, 0, outer_alpha))
        for r_step in range(8):
            r = max(4, radius + 18 - r_step * 4)
            pygame.draw.circle(vignette, (0, 0, 0, 0),
                               (psx, psy), r)
        self.screen.blit(vignette, (0, 0))

    def _draw_yk_vignette(self):
        if not getattr(self, "_yk_present", False):
            return
        # Safe / dim-safe scenes break the YK vignette. If the
        # avatar somehow crosses into the Inn or cellar, it should
        # not paint the room.
        if self.scene is not None and (
                self.scene.key in SAFE_SCENES
                or self.scene.key in DIM_SAFE_SCENES):
            return
        period = 2.4
        t_in = period - getattr(self, "_yk_tone_t", 0.0)
        ramp = max(0.0, min(1.0, t_in / period))
        env = (1.0 - ramp) ** 1.6
        max_alpha = 130
        alpha = self._claim_dark(int(max_alpha * env))
        if alpha <= 2:
            return
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, alpha))
        clear_r = int(120 + 80 * (1.0 - env))
        for r_step in range(10):
            r = max(20, clear_r + 30 - r_step * 6)
            pygame.draw.circle(vignette, (0, 0, 0, 0),
                               (psx, psy), r)
        self.screen.blit(vignette, (0, 0))

    def _draw_apex_overlay(self):
        """Apex-tier rendering: when Pursuer proximity hits >= 0.95,
        the world goes wrong. Heavy red wash across the whole screen
        (interiors and exteriors alike, unlike _draw_dusk_tint which
        only touches OUTDOOR_SCENES); the screen edges crush in
        with a hard black vignette so the player's view narrows;
        the overlay pulses on a slow sine so the dread reads as
        active, not static. Cheap: two SRCALPHA blits per frame.
        Always runs above the dusk tint so the apex state is
        visually distinct from regular high-proximity unease."""
        if self.scene is None or self.player is None:
            return
        if self.pursuer_proximity < 0.95:
            return
        # Safe / dim-safe interiors break the apex wash. The Inn is
        # the refuge. Standing inside it lifts the apex pressure --
        # only stepping out re-engages it. Reads as a deliberate
        # sanctuary mechanic rather than a hole in the horror.
        if (self.scene.key in SAFE_SCENES
                or self.scene.key in DIM_SAFE_SCENES):
            return
        t = pygame.time.get_ticks() / 1000.0
        pulse = 0.85 + 0.15 * math.sin(t * 1.4)
        # Red wash across the whole screen. Uses C_BLOOD (a desaturated
        # dried-blood red) rather than primary red so the apex tone
        # reads as "wrong" without going carnival-haunted. Wash alpha
        # routed through _claim_dark so the combined-darkness budget
        # caps stacked overlays.
        wash_a = self._claim_dark(int(70 * pulse))
        wash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        wash.fill((C_BLOOD[0], C_BLOOD[1], C_BLOOD[2], wash_a))
        self.screen.blit(wash, (0, 0))
        # Edge-crush vignette: heavy black ring around the screen
        # with a clear ~110-px disc around the player. Forces the
        # player to feel tunnel-vision. Inner radius pulses with
        # the wash so the disc breathes with the world.
        edge_a = self._claim_dark(int(180 * pulse))
        edge = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        edge.fill((0, 0, 0, edge_a))
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        clear_r = int(110 + 6 * math.sin(t * 1.4))
        pygame.draw.circle(edge, (0, 0, 0, 0), (psx, psy), clear_r)
        self.screen.blit(edge, (0, 0))

    def _draw_hidden_overlay(self):
        """While player.hidden is set, render a dark vignette
        around the player so the screen FEELS cramped -- the player
        is crouched in cover, vision narrow. Draws on top of every
        other overlay. Does not block gameplay; the camera still
        shows what's there, just dimmer at the edges. Softened
        from the prior pass: 60% wash with a wider clear disc so
        the cover read is "narrow" not "blind"."""
        if self.scene is None or self.player is None:
            return
        if getattr(self.player, "hidden", None) is None:
            return
        # Corn cover is walking-through-stalks, not crouched. The
        # player can still see forward; the vignette would lie
        # about that. Cultist sight cone IS still reduced (the
        # player.hidden flag handles that), so the mechanical
        # benefit stands.
        if self.player.hidden == "corn":
            return
        # Safe interiors: you're already safe, the hide-cramp read
        # is wrong here. Basement (DIM_SAFE) keeps the cramp -- its
        # hide spots are still meaningful cover.
        if self.scene.key in SAFE_SCENES:
            return
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        # 60% wash (153 alpha) routed through the darkness cap so
        # hide stacked with apex/dip never blots the whole screen.
        wash_a = self._claim_dark(153)
        layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        layer.fill((0, 0, 0, wash_a))
        clear_r = 95
        for r_step in range(8):
            r = max(8, clear_r + 16 - r_step * 4)
            pygame.draw.circle(layer, (0, 0, 0, 0), (psx, psy), r)
        self.screen.blit(layer, (0, 0))

    def _tick_visibility_dip(self, dt):
        if self._visibility_dip_t > 0:
            self._visibility_dip_t = max(
                0.0, self._visibility_dip_t - dt)

    def _claim_dark(self, requested):
        """Reserve a slice of the per-frame full-screen darkness
        budget. Returns the alpha the caller is allowed to use
        (0..requested). Increments the running total so the next
        caller sees less budget. Reset to 0 at the top of the
        overlay block. Vignettes (radial, clear at player) do NOT
        participate -- only whole-screen black washes."""
        avail = max(0, MAX_FULLSCREEN_DARK - self._overlay_dark_used)
        used = min(requested, avail)
        self._overlay_dark_used += used
        return used

    def _draw_visibility_dip(self):
        """Black wash over the screen scaled to _visibility_dip_t.
        Decays linearly over ~1.2s. Used by watcher-banish and
        eye-scatter events to give the player a brief moment of
        'I can't see' after a horror beat -- the lit-up moment is
        followed by a stumble."""
        t = self._visibility_dip_t
        if t <= 0:
            return
        # Safe / dim-safe scenes don't dip. The Inn (and the
        # cellar) is the room you walked back into to recover --
        # it should not be dipping on you.
        if (self.scene is not None
                and (self.scene.key in SAFE_SCENES
                     or self.scene.key in DIM_SAFE_SCENES)):
            return
        ratio = min(1.0, t / 1.2)
        alpha = self._claim_dark(int(180 * ratio))
        if alpha <= 4:
            return
        layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        layer.fill((0, 0, 0, alpha))
        self.screen.blit(layer, (0, 0))

    def _draw_apex_silhouette(self):
        """A held black silhouette in the centre of the screen for the
        ~110ms after closure arms. Tall human shape, no detail. Drawn
        on top of every other overlay so the player can't miss it --
        but the duration is short enough that they cannot be sure
        they did not imagine it. Fires once per closure-arm event;
        a second arm in the same session is only possible if the
        timer was reset (it is not under normal play)."""
        if self._apex_silhouette_t <= 0:
            return
        cx = SCREEN_W // 2
        cy = SCREEN_H // 2
        # Tall figure: ~2 tiles wide x ~3.5 tiles tall. No face,
        # no shading, no animation -- just a hole in the wash.
        w = 56
        h = 116
        pygame.draw.ellipse(self.screen, (2, 2, 4),
                            (cx - 18, cy - h // 2, 36, 38))
        pygame.draw.rect(self.screen, (2, 2, 4),
                         (cx - w // 2, cy - h // 2 + 28, w, h - 28))
        # Slight asymmetry on the lower edge -- shoulders, not a
        # rectangle. Mirrors a body the player did not consent to
        # see clearly.
        pygame.draw.polygon(self.screen, (2, 2, 4), [
            (cx - w // 2 - 6, cy - h // 2 + 36),
            (cx - w // 2,     cy - h // 2 + 28),
            (cx - w // 2,     cy - h // 2 + 60),
        ])
        pygame.draw.polygon(self.screen, (2, 2, 4), [
            (cx + w // 2 + 6, cy - h // 2 + 36),
            (cx + w // 2,     cy - h // 2 + 28),
            (cx + w // 2,     cy - h // 2 + 60),
        ])

    def _tick_apex_silhouette(self, dt):
        if self._apex_silhouette_t > 0:
            self._apex_silhouette_t = max(0.0, self._apex_silhouette_t - dt)

    def _draw_flashlight(self):
        """When the player carries the flashlight AND has it toggled
        on AND has battery, dark scenes get a bright cone in the
        facing direction. Off / dead-battery / no-flashlight all
        fall back to a heavy darkness overlay with only a small
        clear circle around the player.

        'Dark' is two cases: any scene in DARK_SCENES (interiors
        always dark), OR an OUTDOOR_SCENES scene at dusk/night
        phase. This means the flashlight is useful at night
        anywhere outside, not just in the basement -- previously
        the cone never drew outside DARK_SCENES, so players who
        toggled the light outdoors saw no effect."""
        if self.scene is None or self.player is None:
            return
        phase = self._effective_phase()
        is_outdoor_dark = (self.scene.key in OUTDOOR_SCENES
                           and phase in ("dusk", "night"))
        if self.scene.key not in DARK_SCENES and not is_outdoor_dark:
            return
        has_light = (self.player.inventory.has("flashlight")
                     and self.player.flashlight_on
                     and self.player.battery_charge > 0)
        # Build a dark overlay with a clear cone for the flashlight, or
        # a small clear circle for unlit baseline. Outdoor-dusk uses
        # a softer ceiling than full interior dark -- moonlight, not
        # cellar.
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        if is_outdoor_dark and self.scene.key not in DARK_SCENES:
            base_alpha = 130 if has_light else 160
        else:
            base_alpha = 200 if not has_light else 170
        overlay.fill((0, 0, 0, base_alpha))
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        if has_light:
            # Cone of light in the facing direction. We carve a clear
            # area by blitting BLEND_RGBA_SUB with progressively
            # smaller circles along the cone.
            fx, fy = self.player.facing
            # Anchor near the player's chest; project the cone forward
            for step in range(8):
                d = step * 22
                cx = psx + int(fx * d)
                cy = psy + int(fy * d) - 4
                r = max(8, 56 - step * 5)
                a = max(40, 220 - step * 22)
                pygame.draw.circle(overlay, (0, 0, 0, 0),
                                   (cx, cy), r)
                # Soft halo around the cone interior
                pygame.draw.circle(overlay, (0, 0, 0, max(0, base_alpha - a)),
                                   (cx, cy), r + 8, 4)
        else:
            # Baseline: tiny clear circle right around the player.
            pygame.draw.circle(overlay, (0, 0, 0, 0),
                               (psx, psy), 22)
        self.screen.blit(overlay, (0, 0))

    def _draw_pursuer_glimpse(self):
        """At very high Pursuer proximity, a tall_shadow silhouette
        renders for a single frame at the screen edge -- the Pursuer
        briefly visible in peripheral vision. Held for ~80ms then
        gone. Schedule fires only when proximity > 0.85 and a scene
        transition recently completed (an exhausted moment when the
        player just walked into a new room). Tracks `_glimpse_t` -- a
        countdown that's set on transition exit."""
        if self.scene is None or self.player is None:
            return
        if self.pursuer_proximity < 0.85:
            return
        if self._glimpse_t <= 0:
            return
        # Render the tall_shadow at the chosen screen edge for the
        # remaining frames.
        from rendering.sprites import draw_npc_sprite
        draw_npc_sprite(self.screen,
                        self._glimpse_pos[0], self._glimpse_pos[1],
                        "tall_shadow", (0, 1))
        self._glimpse_t -= 1.0 / 60.0

    def _draw_haze(self, base_alpha, fog_rgba, fog_n, drift_x, sway_amp,
                   sway_y_amt):
        """Reusable haze helper: a flat black tint at `base_alpha` plus
        `fog_n` drifting translucent SQUARE patches tinted `fog_rgba`.
        Used by the mistlands overlay with different parameters."""
        if base_alpha:
            dim = pygame.Surface((SCREEN_W, SCREEN_H))
            dim.fill((0, 0, 0))
            dim.set_alpha(base_alpha)
            self.screen.blit(dim, (0, 0))
        t = pygame.time.get_ticks() / 1000.0
        size = 160
        for i in range(fog_n):
            fx = ((i * 137 + int(t * drift_x + i * 50))
                  % (SCREEN_W + 240) - 120)
            fy = ((i * 73) % SCREEN_H
                  + int(math.sin(t * sway_amp + i * 0.7) * sway_y_amt))
            fog = pygame.Surface((size, size), pygame.SRCALPHA)
            fog.fill(fog_rgba)
            self.screen.blit(fog, (fx, fy))

    def _draw_subliminal(self):
        """Once in roughly 2000 frames, render a single-frame King
        in Yellow figure or hooded cultist silhouette in the player's
        peripheral. No SFX, no log entry, no follow-up. Players will
        think they imagined it. Suppressed during transitions and
        modals so it doesn't fight any active fade or dialog draw."""
        if (self.dialog.active or self.inv_ui.open or self.notebook_ui.open
                or self.text_input.active
                or self.state != "playing"):
            return
        if random.random() >= 1 / 2000:
            return
        kind = random.choice(("yellow_king", "cultist"))
        # Pick a screen position near the edge but not behind the HUD
        # bar. Avoid the immediate area around the player so it lands
        # in peripheral vision rather than centered.
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        for _ in range(8):
            sx = random.randint(40, SCREEN_W - 40)
            sy = random.randint(40, SCREEN_H - 80)
            if math.hypot(sx - psx, sy - psy) > 140:
                draw_npc_sprite(self.screen, sx, sy, kind, (0, 1))
                return

    def _tick_visitor_silence(self, dt):
        """When a `tall_shadow` enemy is visible on screen, cut the
        music to silence. Restore on the next tick where none are
        visible. The dread is in the absence -- the world stops
        having a soundtrack the moment a Visitor enters frame.
        Drives `audio.force_silence` / restore via `music_muted`."""
        if self.scene is None:
            return
        # Test visibility: enemy world position transformed to screen
        # space lies within the camera bounds.
        visible = False
        for e in self.scene.enemies:
            if not e.alive:
                continue
            if e.kind != "tall_shadow":
                continue
            sx = e.x - self.cam_x
            sy = e.y - self.cam_y
            if -32 <= sx <= SCREEN_W + 32 and -32 <= sy <= SCREEN_H + 32:
                visible = True
                break
        if visible and not self._visitor_silence:
            self._visitor_silence = True
            self.audio.force_silence()
        elif not visible and self._visitor_silence:
            self._visitor_silence = False
            self.audio.music_muted = False
            if self.scene.music:
                self.audio.play_music(self.scene.music)

    def _tick_haunt_audio(self, dt):
        """Two independent ambient tracks fired off random schedules.

         * orb whisper -- faint whisper while the orb is in inventory.
         * child humming -- the village melody hummed in non-village
           creepy scenes (basement, well, void, haunted house, the
           abducted hallway). The player hears a kid where there
           shouldn't be one.

        Each track has its own timer field initialised in __init__ so
        leaving and returning to the trigger condition resets the
        wait. They don't share schedules, so they won't sync up
        rhythmically across long sessions."""
        if self.player is None:
            return
        inv = self.player.inventory
        # Orb whisper
        if not inv.has("orb"):
            self._orb_whisper_t = 4.0
        else:
            self._orb_whisper_t -= dt
            if self._orb_whisper_t <= 0:
                self.audio.play("whisper", 0.45)
                self._orb_whisper_t = random.uniform(8.0, 18.0)
        # Distant child humming -- only in creepy non-village scenes.
        scene_key = self.scene.key if self.scene else None
        humming_scenes = {
            "basement", "well_bottom", "well_passage",
            "void", "void_boss", "symbol_portal_room",
            "haunted_house", "haunted_house_glitch",
            "abducted_hallway",
        }
        if scene_key not in humming_scenes:
            self._humming_t = 12.0
        else:
            self._humming_t -= dt
            if self._humming_t <= 0:
                self.audio.play("child_hum", 0.6)
                self._humming_t = random.uniform(20.0, 45.0)

    def _tick_eye_cameras(self, dt):
        """Cult eye-cameras: stationary watchers placed in cult sites
        (haunted_house, well_passage, void_boss). Each entry on
        scene.eye_cameras has {x, y, range, _t}. While the player
        is unhidden and within `range`, _t accumulates. Past 2.5s
        the watcher fires: bumps Pursuer proximity by +0.10, plays
        an alert pulse, and (if the player is still in range)
        spawns a hunter patrol nearby on the next tick by setting
        the hunter's scene to here. Hide breaks line-of-sight; the
        timer decays at half-speed so the player can't game it
        with rapid hide/unhide flicker.

        The visible prop is a `watching_eye` decoration with
        slit=True placed at the same coord by the scene builder.
        This tick does not draw anything -- the eye decoration
        already shows where the watcher is."""
        if self.scene is None or self.player is None:
            return
        if self.state != "playing":
            return
        cams = getattr(self.scene, "eye_cameras", None)
        if not cams:
            return
        px = self.player.x
        py = self.player.y
        hidden = self.player.hidden is not None
        for cam in cams:
            cx = cam["x"]
            cy = cam["y"]
            r = cam.get("range", 140)
            d = math.hypot(px - cx, py - cy)
            if d <= r and not hidden:
                cam["_t"] = cam.get("_t", 0.0) + dt
                if cam["_t"] >= 2.5 and not cam.get("fired", False):
                    cam["fired"] = True
                    pan = self.audio.pan_for_world(cx, self.player.x)
                    if cam.get("alarm", False):
                        # Trespass alarm: louder, hits Pursuer harder.
                        # Used in cult-aligned interiors (the church,
                        # the sheriff's office) where being seen is
                        # also being reported.
                        self.audio.play("alarm_bell", 0.8, pan=pan)
                        self.audio.play("low_pulse", 0.85)
                        self._provoke_cult(0.25)
                        self.show_notice(
                            "A bell starts ringing. They are coming.",
                            duration=3.0)
                    else:
                        self.audio.play("low_pulse", 0.65)
                        self.audio.play("breath", 0.55, pan=pan)
                        self._provoke_cult(0.10)
                        self.show_notice(
                            "The eye sees you. It knows where you are.",
                            duration=2.4)
                    # Steer the Hunter patrol here so the spotting
                    # has a follow-through. (No-op below activation
                    # threshold; harmless.)
                    for p in self._patrols:
                        if p["tag"] == "patrol_hunter":
                            p["scene"] = self.scene.key
                            p["t"] = 4.0
                            break
            else:
                # Decay. Half-speed when hidden so quick flickering
                # doesn't reset the timer instantly.
                rate = dt * (0.5 if hidden else 1.0)
                cam["_t"] = max(0.0, cam.get("_t", 0.0) - rate)
                if cam["_t"] == 0.0:
                    cam["fired"] = False

    def _tick_yk_tone(self, dt):
        if self.scene is None:
            return
        present = any(getattr(n, "sprite_kind", None) == "yellow_king"
                      for n in self.scene.npcs)
        self._yk_present = present
        self._yk_tone_t = getattr(self, "_yk_tone_t", 0.0) - dt
        if present and self._yk_tone_t <= 0:
            self.audio.play("yk_tone", 0.85)
            self._yk_tone_t = 2.4
        if not present:
            self._yk_tone_t = 0.0

    def _tick_dread_aperture(self, dt):
        """Drive the dread aperture (1.0 open -> 0.0 closed). In
        DARK_SCENES without a working flashlight, the aperture
        closes; the King in Yellow ring is drawn at radius
        proportional to it. While hidden + standing still + no
        chaser within range, the aperture re-opens. At 0 the ring
        has reached the player -- triggers closure (capture).

        Cult-dark scenes force-disable the flashlight so the
        aperture closes in spite of any battery."""
        if self.scene is None or self.player is None:
            return
        if self._ending_active or getattr(self, "_closure_started", False):
            return
        # Cult-dark forces the flashlight off every tick. Keeps the
        # state consistent if the player toggled it before entering.
        if self.scene.key in CULT_DARK_SCENES and self.player.flashlight_on:
            self.player.flashlight_on = False
        in_dark = self.scene.key in DARK_SCENES
        has_light = (in_dark
                     and self.player.flashlight_on
                     and self.player.battery_charge > 0
                     and self.scene.key not in CULT_DARK_SCENES)
        if not in_dark or has_light:
            self.dread_aperture = min(1.0, self.dread_aperture + dt * 0.50)
            return
        # Standing-still detection: position changed less than 1px
        # since last tick. Use _last_pos cache rather than asking
        # the player for a velocity attribute.
        lp = self._last_pos
        still = (abs(self.player.x - lp[0]) + abs(self.player.y - lp[1]) < 1.0)
        self._last_pos = (self.player.x, self.player.y)
        hidden = self.player.hidden is not None
        # Chaser within range -- any enemy tagged as a depths chaser
        # (or any enemy at all in cult-dark, since combat is gone).
        # Touch-range contact slams the aperture to 0 immediately,
        # which routes through the pulled-through-the-doorframe
        # closure cinematic.
        chaser_near = False
        for e in self.scene.enemies:
            if not e.alive:
                continue
            d = math.hypot(e.x - self.player.x, e.y - self.player.y)
            if d < 22:
                self.dread_aperture = 0.0
                self._begin_pulled_through_closure()
                return
            if d < 220:
                chaser_near = True
        if hidden and still and not chaser_near:
            # THRESHOLD hide-spot trade: cover from sight halts the
            # aperture's closure, but does NOT reverse it. The held
            # breath is a stay, not a heal. Recovery only happens
            # at full safe-room interactions (the cot, the inn).
            pass
        else:
            # Closing rate: faster when a chaser sees the player
            # unhidden, slower in baseline darkness.
            rate = 0.04
            if chaser_near and not hidden:
                rate = 0.18
            self.dread_aperture = max(0.0, self.dread_aperture - dt * rate)
        if self.dread_aperture <= 0.0:
            self._begin_pulled_through_closure()
            return
        # Depths ambient layer: distant chant + wet exhale on
        # tightening intervals as the aperture closes. Both fire
        # only in cult-dark scenes -- the upper basement / well
        # bottom stay clean of these layers.
        if self.scene.key in CULT_DARK_SCENES:
            close = 1.0 - self.dread_aperture
            vol = 0.18 + 0.55 * close
            self._chant_t += dt
            chant_period = 9.0 - 6.0 * close
            if self._chant_t >= chant_period:
                self._chant_t = 0.0
                self.audio.play("cult_chant", vol)
            self._breath_t += dt
            breath_period = 5.5 - 3.5 * close
            if self._breath_t >= breath_period:
                self._breath_t = 0.0
                self.audio.play("cult_breath", vol * 0.8)

    def _tick_watchers(self, dt):
        """Spawn, age, and despawn Watchers. Watchers are placed at
        world coordinates just inside the camera's edge -- close
        enough to read as a figure, far enough that the player has
        to turn the camera (i.e. walk a few tiles) to centre them.
        They despawn when:
          * the camera centres them (player looks toward them), or
          * the player steps within ~80 px, or
          * t_left runs out.
        Disabled in the bedroom on the very first session so the
        opening minute reads as ordinary."""
        if self.scene is None or self.player is None:
            return
        # Don't spawn during transitions or modals -- they look like
        # a draw bug if they appear over a black fade.
        if self.state != "playing":
            return
        # Spawn cadence: rises with Pursuer proximity, but also has
        # a baseline so they exist even early on. Suppressed entirely
        # in the bedroom until the player has left the bedroom at
        # least once -- the opening minute owns its own scripted
        # watcher (planted in bedroom_on_update) and shouldn't have
        # ambient figures stacking onto it.
        in_opening_room = (self.scene is not None
                           and self.scene.key == "bedroom"
                           and not self.save.flag("left_bedroom"))
        self._watcher_next_t -= dt
        if (self._watcher_next_t <= 0 and len(self._watchers) < 2
                and not in_opening_room):
            self._spawn_watcher()
            base = 14.0 - self.pursuer_proximity * 8.0
            self._watcher_next_t = max(5.0, base + random.uniform(-2.0, 4.0))
        # Pre-compute flashlight state ONCE per tick so the inner
        # loop's dot-product check is cheap. The cone projects from
        # the player in their facing direction; a watcher inside the
        # cone is banished instantly with a phantom_step echo.
        light_on = (self.player.inventory.has("flashlight")
                    and self.player.flashlight_on
                    and self.player.battery_charge > 0)
        fxp, fyp = self.player.facing
        # Age & despawn loop.
        survivors = []
        for w in self._watchers:
            w["t_left"] -= dt
            sx = w["x"] - self.cam_x
            sy = w["y"] - self.cam_y
            dx_c = sx - SCREEN_W / 2
            dy_c = sy - SCREEN_H / 2
            looked_at = abs(dx_c) < 110 and abs(dy_c) < 90
            w["looked_at"] = looked_at
            dx_p = w["x"] - self.player.x
            dy_p = w["y"] - self.player.y
            d_p = math.hypot(dx_p, dy_p)
            close = d_p < 80
            # Flashlight cone behaviour. Below mid proximity the
            # cone banishes a watcher outright -- the gaze AND the
            # light agree, the figure has nowhere to be. From mid
            # to high proximity the cone only PAUSES the watcher:
            # it stops creeping for ~1.5s but does not despawn,
            # so the player can buy a breath but not a clean
            # delete. At apex (>= 0.85) the cone has no effect at
            # all -- the world is past the point where a 9V
            # flashlight does anything to it.
            #
            # Banishing a watcher costs the player visibility for
            # a beat -- the lit-up moment leaves the rest of the
            # scene feeling darker by contrast.
            if light_on and 0 < d_p < 220:
                dot = (dx_p * fxp + dy_p * fyp) / d_p
                if dot > 0.55:
                    pan = self.audio.pan_for_world(w["x"], self.player.x)
                    prox_now = self.pursuer_proximity
                    if prox_now < 0.60:
                        self.audio.play("phantom_step", 0.45, pan=pan)
                        self._visibility_dip_t = max(
                            self._visibility_dip_t, 1.0)
                        continue   # drop without survivor
                    elif prox_now < 0.85:
                        # Pause -- watcher freezes for 1.5s but
                        # does not despawn. Reuses defiant_t as
                        # an anti-step timer (clamped from below
                        # so this can stack with prior pauses).
                        w["pause_t"] = max(w.get("pause_t", 0.0), 1.5)
                        self._visibility_dip_t = max(
                            self._visibility_dip_t, 0.7)
                    # else: apex band -- the cone does nothing.
            # SLENDER MECHANIC: when the watcher is OFF-SCREEN or just
            # outside the centred-look window, it steps toward the
            # player. While the player has it centred (looked_at), it
            # holds still -- the gaze freezes it. Step distance scales
            # with Pursuer proximity.
            #
            # The OPENING WATCHER (planted in bedroom_on_update) has
            # `still=True` so it stands in the threshold instead of
            # creeping closer -- its job is to be seen, not to chase.
            #
            # Creepers ignore the gaze-freezes-it rule: they step in
            # whether the player is looking at them or not. The
            # player's eye does not stop them.
            creeper = w.get("creeper", False)
            # Decrement any flashlight-induced pause; while > 0 the
            # watcher freezes regardless of look state.
            paused = w.get("pause_t", 0.0)
            if paused > 0:
                w["pause_t"] = max(0.0, paused - dt)
            should_step = (not close and d_p > 0
                           and not w.get("still", False)
                           and (not looked_at or creeper)
                           and w.get("pause_t", 0.0) <= 0)
            if should_step:
                step = (8.0 + self.pursuer_proximity * 24.0) * dt
                w["x"] -= (dx_p / d_p) * step
                w["y"] -= (dy_p / d_p) * step
            # Opening watcher only dissolves on look or approach,
            # never from boredom -- the first horror beat must not
            # be missable.
            timed_out = (w["t_left"] <= 0
                         and not w.get("opening_watcher", False))
            # Defiant watchers hold ~1s on look before vanishing.
            # Creepers don't dissolve on look at all -- only on touch.
            dissolve_on_look = looked_at and not creeper
            if dissolve_on_look and w.get("defiant", False):
                w["defiant_t"] = w.get("defiant_t", 1.0) - dt
                if w["defiant_t"] > 0:
                    dissolve_on_look = False
            if timed_out or dissolve_on_look or close:
                # Opening watcher leaves a residue: a slightly
                # louder phantom_step + a sub-bass low_pulse +
                # a brief mote at the spot where it stood, so
                # the player has a tiny piece of evidence the
                # figure was real.
                pan = self.audio.pan_for_world(w["x"], self.player.x)
                if w.get("opening_watcher", False) and (looked_at or close):
                    self.audio.play("phantom_step", 0.45, pan=pan)
                    self.audio.play("low_pulse", 0.30)
                    if self.scene is not None:
                        from entities.decoration import Decoration
                        self.scene.add_decoration(
                            Decoration(w["x"], w["y"] - 6, "mote")
                        )
                elif (looked_at or close) and self.pursuer_proximity > 0.4:
                    if random.random() < 0.35:
                        self.audio.play("phantom_step", 0.32, pan=pan)
                continue
            survivors.append(w)
        self._watchers = survivors
        # Visibility ramp: while at least one survivor is on screen
        # and the player isn't hidden, the cult's eyes are on them.
        # Provokes the cult and ramps Pursuer. Hide breaks it.
        if self._watchers and self.player.hidden is None:
            on_screen = False
            for w in self._watchers:
                sx = w["x"] - self.cam_x
                sy = w["y"] - self.cam_y
                if -32 <= sx <= SCREEN_W + 32 and -48 <= sy <= SCREEN_H + 32:
                    on_screen = True
                    break
            if on_screen:
                self._provoke_cult(dt * 0.04)

    def _spawn_watcher(self):
        """Place a watcher at a random tile near the camera edge,
        clamped to walkable floor inside the scene bounds. We try a
        handful of candidate tiles; if none work the spawn is
        skipped silently."""
        scene = self.scene
        if scene is None:
            return
        cam_l = int(self.cam_x // TILE)
        cam_r = int((self.cam_x + SCREEN_W) // TILE)
        cam_t = int(self.cam_y // TILE)
        cam_b = int((self.cam_y + SCREEN_H) // TILE)
        for _ in range(10):
            edge = random.choice(("left", "right", "top", "bottom"))
            if edge == "left":
                tx = cam_l + random.randint(0, 2)
                ty = random.randint(cam_t, cam_b)
            elif edge == "right":
                tx = cam_r - random.randint(0, 2)
                ty = random.randint(cam_t, cam_b)
            elif edge == "top":
                tx = random.randint(cam_l, cam_r)
                ty = cam_t + random.randint(0, 2)
            else:
                tx = random.randint(cam_l, cam_r)
                ty = cam_b - random.randint(0, 2)
            if not (0 <= tx < scene.w and 0 <= ty < scene.h):
                continue
            wx = tx * TILE + TILE // 2
            wy = ty * TILE + TILE // 2
            # Reject if the tile is solid -- no floating watchers
            # inside walls. Use a small probe rather than the exact
            # is_solid_at so a tile next to a wall still counts.
            if scene.is_solid_at(wx, wy):
                continue
            # Reject if too close to the player to begin with.
            if math.hypot(wx - self.player.x, wy - self.player.y) < 140:
                continue
            self._watchers.append({
                "x": wx,
                "y": wy,
                "t_left": random.uniform(2.0, 4.5),
                # `seen` flips true once the watcher has been on
                # screen for one full frame -- prevents the despawn
                # from firing on the same frame as the spawn if the
                # camera was already centred on it.
                "seen": False,
                # Rule-breaks. Most watchers obey: hold while looked
                # at, despawn when the gaze lands. A small minority
                # break the rule so the player can never be sure of
                # the system. Creeper: keeps stepping closer even
                # while looked at (the gaze does not freeze it).
                # Defiant: holds an extra ~1.0s on look before
                # vanishing -- the moment the player thinks "it's
                # gone" it is still standing there.
                "creeper": random.random() < 0.01,
                "defiant": random.random() < 0.05,
                "defiant_t": 1.0,
            })
            return

    def _draw_watchers(self):
        """Render each active watcher in world space. Suppressed
        during transitions / dialog modals so the figure doesn't
        sit over a black fade."""
        if (self.dialog.active or self.inv_ui.open or self.notebook_ui.open
                or self.text_input.active
                or self.state != "playing"):
            return
        for w in self._watchers:
            sx = int(w["x"] - self.cam_x)
            sy = int(w["y"] - self.cam_y)
            if sx < -32 or sx > SCREEN_W + 32:
                continue
            if sy < -48 or sy > SCREEN_H + 32:
                continue
            draw_npc_sprite(self.screen, sx, sy, "watcher", (0, 1),
                            gaze=w.get("looked_at", False))
            w["seen"] = True

    def _tick_flashback(self, dt):
        """Poll the flashback_pending save flag (set by inventory_ui
        when the player reads page 3 of Mom's notebook). When set,
        start the flashback and clear the flag. Once started, walk
        through the stills phase by phase."""
        if (self._flashback_phase is None
                and self.save.flag("flashback_pending")):
            self.save.set_flag("flashback_pending", False)
            self.save.set_flag("flashback_seen", True)
            self._flashback_phase = 0
            self._flashback_t = 0.0
            self.audio.force_silence()
            self.audio.play("low_pulse", 0.85)
        if self._flashback_phase is None:
            return
        self._flashback_t += dt
        _, dur = self._flashback_stills[self._flashback_phase]
        if self._flashback_t >= dur:
            self._flashback_phase += 1
            self._flashback_t = 0.0
            if self._flashback_phase >= len(self._flashback_stills):
                # Done -- restore music, play a final chord.
                self._flashback_phase = None
                self.audio.music_muted = False
                self.audio.play("breath", 0.7)
                if self.scene and self.scene.music:
                    self.audio.play_music(self.scene.music)
                # Bump proximity hard -- the player KNOWS now.
                self._provoke_cult(0.20)

    def _draw_flashback(self):
        """Render the flashback overlay if active. Black field, large
        white text in the centre, no other UI."""
        if self._flashback_phase is None:
            return
        line, dur = self._flashback_stills[self._flashback_phase]
        # Fade in over first 0.3s, hold, fade out over last 0.3s.
        t = self._flashback_t / max(0.01, dur)
        if t < 0.15:
            alpha = int((t / 0.15) * 255)
        elif t > 0.85:
            alpha = int(((1.0 - t) / 0.15) * 255)
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))
        # Black field underneath.
        veil = pygame.Surface((SCREEN_W, SCREEN_H))
        veil.fill((0, 0, 0))
        self.screen.blit(veil, (0, 0))
        # Text -- white, fading.
        s = self.fonts["lg"].render(line, True, (220, 218, 226))
        s.set_alpha(alpha)
        self.screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2,
                             SCREEN_H // 2 - s.get_height() // 2))

    def _is_dusk(self):
        """Dusk fires when proximity >= 0.70 OR scene-visit count for
        any cult-relevant scene >= 6. Cult-relevant scenes are the
        well_bottom, the clearing (void_boss), the cult_chamber
        (symbol_portal_room), and the cauldron-fed visits."""
        if self.pursuer_proximity >= 0.70:
            return True
        cult_scenes = ("well_bottom", "void_boss", "symbol_portal_room",
                       "haunted_house", "graveyard")
        total = sum(self.save.visits(k) for k in cult_scenes)
        return total >= 6

    # ---- Endings ----

    def _begin_car_escape(self):
        """Player reached the car at the diner with car_keys.
        Two flavors: 'with_kid' if the kid follower is active,
        'alone' otherwise. Sets the appropriate ending and hands
        off to _play_ending."""
        if self._ending_active:
            return
        if self._kid_follower_active:
            self._play_ending("escape_with_kid")
        else:
            self._play_ending("escape_alone")

    def _check_dusk_endings(self):
        """Retired. The destroy_cult and sacrifice_kid endings were
        gated on dusk + kid follower + a specific scene -- both were
        replaced by the polaroid ritual at well_bottom and the
        seal_threshold ending at the doorframe. Kept as a no-op so
        the per-tick caller in step() doesn't have to be branched."""
        return

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
        if name in ("seal_threshold", "seal_threshold_with_kid"):
            self.audio.play("arg_chime", 0.7)
        elif name == "pulled_through":
            self.audio.play("low_pulse", 0.95)
        else:
            self.audio.play("door_close", 0.7)

    # Ending scripts. Each is a list of (line, duration_seconds).
    _ENDING_SCRIPTS = {
        "escape_alone": [
            ("you turn the key. it catches.", 2.5),
            ("the engine starts. it shouldn't have.", 2.5),
            ("you don't look in the rearview.", 2.5),
            ("the road runs out at the county line.", 2.5),
            ("you do not stop driving for a long time.", 3.0),
            ("you left him.", 3.5),
        ],
        "escape_with_kid": [
            ("you put him in the passenger seat.", 2.5),
            ("you turn the key. it catches.", 2.5),
            ("he doesn't say anything for an hour.", 2.5),
            ("you cross the county line at full dark.", 2.5),
            ("he sleeps against the window.", 2.5),
            ("they will look for him. they will look for you.", 3.0),
            ("you keep driving.", 3.0),
        ],
        "pulled_through": [
            ("the air goes still.", 2.5),
            ("a yellow figure stands where you were.", 3.0),
            ("he is not looking at the camera.", 2.5),
            ("he is looking at you.", 3.5),
            ("the doorframe fills the room.", 2.5),
            ("you go through it.", 3.5),
        ],
        "seal_threshold": [
            ("you press the drawing against the stone.", 2.5),
            ("the eye on the lintel turns inside out.", 2.5),
            ("the smoke stops.", 2.5),
            ("the door is just a door now.", 2.5),
            ("the King in the Field is somewhere else now.", 3.0),
            ("you don't have to go through it.", 3.0),
            ("the boy is asleep at the inn.", 3.0),
            ("he will wake up.", 3.0),
        ],
        "seal_threshold_with_kid": [
            ("you give him back the drawing.", 2.5),
            ("he presses it against the stone himself.", 2.5),
            ("the eye on the lintel turns inside out.", 2.5),
            ("the smoke stops.", 2.5),
            ("he doesn't say anything for a long time.", 3.0),
            ("the door is just a door now.", 2.5),
            ("the King in the Field is somewhere else now.", 3.0),
            ("you carry him out.", 3.0),
            ("he wakes up in the morning.", 3.0),
        ],
    }

    def _tick_ending(self, dt):
        """Walk through the active ending's stills. Each phase is a
        single line shown for its specified duration via the same
        overlay system as the flashback."""
        if not self._ending_active:
            return
        self._ending_phase_t += dt
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

    def _end_ending(self):
        """Wrap up the ending sequence and return to title."""
        self._ending_active = None
        self._ending_phase = 0
        self._ending_phase_t = 0.0
        self._closure_locked = False
        self.audio.music_muted = False
        self.state = "title"
        self.audio.play_music("threshold_drone")

    def _draw_ending(self):
        """Render the active ending's current still. Same overlay
        treatment as the flashback."""
        if not self._ending_active:
            return
        script = self._ENDING_SCRIPTS.get(self._ending_active, [])
        if self._ending_phase >= len(script):
            return
        line, dur = script[self._ending_phase]
        t = self._ending_phase_t / max(0.01, dur)
        if t < 0.15:
            alpha = int((t / 0.15) * 255)
        elif t > 0.85:
            alpha = int(((1.0 - t) / 0.15) * 255)
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))
        veil = pygame.Surface((SCREEN_W, SCREEN_H))
        veil.fill((0, 0, 0))
        self.screen.blit(veil, (0, 0))
        s = self.fonts["lg"].render(line, True, (220, 218, 226))
        s.set_alpha(alpha)
        self.screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2,
                             SCREEN_H // 2 - s.get_height() // 2))

    def _effective_phase(self):
        """The day phase as the world experiences it. Single
        source of truth for "is it night here?":
          * PERMANENT_NIGHT_SCENES (mistlands) are always night.
          * Past DAY_NIGHT_BREAKS_AFTER, the cycle has broken --
            every phase reads as night. There is no morning
            anymore.
          * Otherwise, the saved day_phase.
        Drives patrol activation, the dusk tint, and the outdoor
        flashlight gate."""
        if self.scene is not None and self.scene.key in PERMANENT_NIGHT_SCENES:
            return "night"
        if self.save is not None:
            if self.save.arg("day_count", 1) >= DAY_NIGHT_BREAKS_AFTER:
                return "night"
            return self.save.arg("day_phase", "afternoon")
        return "afternoon"

    def _patrols_active(self):
        """Cultists walk only at night (or in permanent-night
        scenes, or after the day-7 cap). Day = preparation
        window; night = horror. The Inn (SAFE_SCENES) is always
        patrol-free regardless of phase."""
        if self.scene is None:
            return False
        if self.scene.key in SAFE_SCENES:
            return False
        return self._effective_phase() == "night"

    def _tick_sheriff(self, dt):
        """Run all cult patrols. Each patroller reads its min_prox
        threshold; below it, they stay dormant (no scene picked, no
        NPC spawned). At or above, they teleport between random
        outdoor scenes every 30-60s. If they land in the player's
        current scene, an NPC sprite spawns and starts walking
        toward the player ('chaser' AI). On sight (within range,
        player not hidden) the patroller bumps proximity by 0.20
        once per scene visit. On touch (within ~22 px) the closure
        triggers.

        Hard-gated to night: cultists are creatures of the dark.
        The day is the player's exploration window. _patrols_active
        owns the phase + scene + day-cap rules."""
        if self.scene is None or self.player is None:
            return
        # SAFE_SCENES are refuges -- no patrol presence here.
        # Walking into the Inn lifts the cult pressure; this is the
        # sanctuary mechanic that makes the rest of the world's
        # closing-in feel meaningful. Despawn any leftover patrol
        # NPCs that wandered in from a prior scene's tick.
        if self.scene.key in SAFE_SCENES:
            self.scene.npcs = [
                n for n in self.scene.npcs
                if not (isinstance(getattr(n, "tag", None), str)
                        and n.tag.startswith("patrol_"))
            ]
            return
        # Day/night gate: outside permanent-night scenes (mistlands)
        # and outside the day-7 cap, patrols stay in their burrows
        # during morning/afternoon/dusk. Despawn any leftover NPCs
        # so the player walking into a scene at dawn sees an empty
        # village, not a frozen cultist mid-step.
        if not self._patrols_active():
            for patrol in self._patrols:
                patrol["scene"] = None
            self.scene.npcs = [
                n for n in self.scene.npcs
                if not (isinstance(getattr(n, "tag", None), str)
                        and n.tag.startswith("patrol_"))
            ]
            return
        prox = self.pursuer_proximity
        # Per-patrol phase gates collapsed into the global night
        # gate above (every patrol is night-only now). Each patrol
        # still owns its proximity floor.
        for patrol in self._patrols:
            tag = patrol["tag"]
            # Activation gate.
            if prox < patrol["min_prox"]:
                # Despawn any leftover NPC from a previous activation
                # (proximity could have ticked back down past a
                # transition reprieve, or the day has rolled into
                # a phase where this patroller doesn't walk).
                self.scene.npcs = [n for n in self.scene.npcs
                                    if getattr(n, "tag", None) != tag]
                patrol["scene"] = None
                continue
            # Announce each higher-tier patroller's first activation.
            if tag not in self._patrol_announced:
                self._patrol_announced.add(tag)
                if tag == "patrol_hunter":
                    self.audio.play("low_pulse", 0.85)
                    self.show_notice(
                        "Something is walking. Hide.",
                        duration=4.0)
                    self._yk_grace_t = 10.0
                elif tag.startswith("patrol_amb_cult"):
                    # Ambient cultists are always present; no
                    # one-shot announcement -- they're the world,
                    # not an event.
                    pass
                else:
                    self.audio.play("low_pulse", 0.45)
                    self.show_notice("More of them are out today.",
                                      duration=3.0)
            # The Yellow King re-routes to the player's scene every
            # tick -- not on re-roll. Doorways don't outrun him.
            # Exception: a brief grace period after his first
            # activation lets the "Something is walking" beat land
            # before he's literally in the room.
            if tag == "patrol_hunter":
                self._yk_grace_t = max(0.0,
                                        getattr(self, "_yk_grace_t", 0.0) - dt)
                if self._yk_grace_t <= 0:
                    patrol["scene"] = self.scene.key
            # Re-roll the patroller's current scene. Re-roll fires
            # when the timer expires OR when scene is None (just-
            # activated from dormancy, or first frame). The
            # player's current scene is weighted higher so cult
            # presence is felt -- at proximity 0 it's 1x weight
            # (mostly random), at full proximity it's 5x more
            # likely to land where the player is.
            patrol["t"] -= dt
            if patrol["t"] <= 0 or patrol["scene"] is None:
                patrol["t"] = random.uniform(patrol["next_min"],
                                              patrol["next_max"])
                if tag == "patrol_hunter":
                    # The King in Yellow walks straight at you
                    # through scenes whenever active. Apex still
                    # escalates via 60px catch radius and reading
                    # through hide -- routing is the same.
                    patrol["scene"] = self.scene.key
                else:
                    # Per-patrol scene pool override -- ambient
                    # cultists restrict to forest walkways so the
                    # player encounters hooded scouts there as a
                    # constant. Falls back to the global
                    # _sheriff_scenes pool otherwise.
                    pool_src = patrol.get("scenes",
                                           self._sheriff_scenes)
                    weight = 1 + int(prox * 4)
                    pool = list(pool_src)
                    if self.scene.key in pool_src:
                        pool += [self.scene.key] * weight
                    patrol["scene"] = random.choice(pool)
            # Find existing NPC for this patrol in the current scene.
            npc = None
            for n in self.scene.npcs:
                if getattr(n, "tag", None) == tag:
                    npc = n
                    break
            # If patrol is supposed to be here, ensure NPC exists.
            if patrol["scene"] == self.scene.key:
                if npc is None:
                    npc = self._spawn_patrol_in_current(patrol)
            else:
                # Patrol moved on -- remove the NPC if it's still here.
                if npc is not None:
                    self.scene.npcs.remove(npc)
                    npc = None
            if npc is None:
                continue
            # The Hunter is the King in Yellow avatar. Force-chase
            # (no scout wander) so it always walks straight at the
            # player. Speed accelerates smoothly with Pursuer
            # proximity from 0.55 baseline up to 2.4 at apex --
            # early it lurches, late it sprints.
            #
            # Visibility grace: when the Hunter NPC is freshly
            # spawned in the player's scene, he gets a 1.5s window
            # where he CANNOT catch the player. The player must
            # see him approaching first -- no instant teleport-and-
            # touch. The grace timer ticks down each frame.
            if tag == "patrol_hunter":
                npc.speed = 0.55 + 1.85 * prox
                npc._force_chase = True
                if not hasattr(npc, "_yk_grace_t"):
                    npc._yk_grace_t = 1.5
                    # First-spawn beat: a low pulse so the player's
                    # ear catches him before the eye does.
                    self.audio.play("low_pulse", 0.55)
                if npc._yk_grace_t > 0:
                    npc._yk_grace_t = max(0.0, npc._yk_grace_t - dt)
            # Spotting check. The flag lives on the NPC instance so
            # each fresh spawn (re-entering a scene creates a new
            # one) gets a clean slate -- the spotted-line beat
            # fires every re-entry, not once per scene per session.
            d = math.hypot(npc.x - self.player.x,
                            npc.y - self.player.y)
            if d < 180 and self.player.hidden is None:
                if not getattr(npc, "_has_been_spotted", False):
                    npc._has_been_spotted = True
                    self._on_patrol_spot(patrol, npc)
            # Catch check. At LOW proximity the catch is a setback,
            # not a game-ender: the player blacks out, wakes back in
            # the cot, the day advances by one, and Pursuer proximity
            # ratchets up by 0.25. At HIGH proximity (>= 0.85) a catch
            # IS the closure ending -- the threshold is too tight to
            # walk back from.
            #
            # Yellow King grace: while his per-spawn grace timer is
            # still running, he literally cannot catch the player.
            # The player must have time to see him approach.
            if (tag == "patrol_hunter"
                    and getattr(npc, "_yk_grace_t", 0.0) > 0):
                continue
            if d < 22 and self.player.hidden is None:
                if self.pursuer_proximity >= 0.85:
                    # Apex band: closure ending. The line is too
                    # tight to walk back from.
                    self._trigger_closure()
                elif self.pursuer_proximity >= 0.55:
                    # Mid band: the cult searches the player.
                    # They keep their lore items, but the
                    # flashlight battery is drained and any spare
                    # batteries are taken. The setback bites
                    # mechanically -- the player has to re-find
                    # batteries before relying on the cone in
                    # dark scenes again.
                    self._trigger_capture(patrol, npc, tier="mid")
                else:
                    # Low band: the existing soft setback.
                    self._trigger_capture(patrol, npc, tier="low")
                return
        # Group flanking pass. Runs after every patrol has been
        # processed for this tick. When 2+ patrol NPCs share a
        # CHASE state in the player's scene, designate the
        # closest as leader (straight chase) and assign each
        # other a perpendicular flank target so they cut off
        # either side of the player. Suppressed in tight scenes
        # via the openness check -- corridors fail it and fall
        # back to a straight pile-on. Hunter excluded: he runs
        # his own door-block routing.
        chasers = []
        for n in self.scene.npcs:
            tag = getattr(n, "tag", "")
            if not isinstance(tag, str) or not tag.startswith("patrol_"):
                continue
            if tag == "patrol_hunter":
                continue
            if getattr(n, "_cult_state", "") == "chase":
                chasers.append(n)
        flank_ok = (len(chasers) >= 2
                    and self._openness_around(
                        self.player.x, self.player.y) >= 6)
        if flank_ok:
            chasers.sort(key=lambda n: math.hypot(
                n.x - self.player.x, n.y - self.player.y))
            leader = chasers[0]
            leader._flank_target = None
            for follower in chasers[1:]:
                ldx = self.player.x - leader.x
                ldy = self.player.y - leader.y
                ld = math.hypot(ldx, ldy) or 1.0
                offset = max(60.0, min(160.0, ld * 0.8))
                # Two perpendicular candidates around the player.
                cand_a = (self.player.x + (-ldy / ld) * offset,
                          self.player.y + ( ldx / ld) * offset)
                cand_b = (self.player.x + ( ldy / ld) * offset,
                          self.player.y + (-ldx / ld) * offset)
                # Pick whichever is closer to the follower's
                # current position so they don't cross the leader.
                da = math.hypot(follower.x - cand_a[0],
                                 follower.y - cand_a[1])
                db = math.hypot(follower.x - cand_b[0],
                                 follower.y - cand_b[1])
                follower._flank_target = cand_a if da < db else cand_b
        else:
            # Not enough chasers (or scene too tight): clear any
            # leftover flank intent from previous ticks.
            for n in self.scene.npcs:
                if isinstance(getattr(n, "tag", None), str) and (
                        n.tag.startswith("patrol_")):
                    n._flank_target = None

    def _openness_around(self, x, y, ring_r=64):
        """Count how many of 8 ring points around (x,y) are
        walkable. Used to gate group flanking -- in tight
        corridors the perpendicular flank targets land in walls
        and cultists end up stuck, so flanking is suppressed
        when openness < 6/8."""
        if self.scene is None:
            return 0
        n = 0
        for ang_step in range(8):
            ang = ang_step * (math.pi / 4)
            sx = x + math.cos(ang) * ring_r
            sy = y + math.sin(ang) * ring_r
            if not self.scene.is_solid_at(sx, sy):
                n += 1
        return n

    def _spawn_patrol_in_current(self, patrol):
        """Plant a patrol NPC at one of the scene's four corners,
        avoiding solid tiles. Prefers a corner > 200 px from the
        player; if no corner is that far (small scenes like the
        bedroom), falls back to the FARTHEST available walkable
        corner. Previously the >200 hard requirement silently
        failed in tight rooms, so apex Yellow King catches never
        landed there -- the patrol existed but never spawned."""
        from entities.npc import NPC
        scene = self.scene
        candidates = [
            (4 * Scene.TILE, 4 * Scene.TILE),
            ((scene.w - 4) * Scene.TILE, 4 * Scene.TILE),
            (4 * Scene.TILE, (scene.h - 4) * Scene.TILE),
            ((scene.w - 4) * Scene.TILE,
             (scene.h - 4) * Scene.TILE),
        ]
        random.shuffle(candidates)
        # First pass: prefer a corner with breathing room.
        for sx, sy in candidates:
            if not scene.is_solid_at(sx, sy):
                if math.hypot(sx - self.player.x,
                               sy - self.player.y) > 200:
                    return self._make_patrol_npc(patrol, sx, sy)
        # Fallback: pick the farthest available walkable corner so
        # tight scenes still get a spawn instead of silently failing.
        best = None
        best_d = -1.0
        for sx, sy in candidates:
            if scene.is_solid_at(sx, sy):
                continue
            d = math.hypot(sx - self.player.x, sy - self.player.y)
            if d > best_d:
                best_d = d
                best = (sx, sy)
        if best is not None:
            return self._make_patrol_npc(patrol, *best)
        return None

    def _make_patrol_npc(self, patrol, sx, sy):
        from entities.npc import NPC
        n = NPC(sx, sy, patrol["name"], patrol["kind"],
                voice="blip_low", portrait="guard",
                movement="chaser",
                speed=patrol.get("speed", 0.85),
                no_prompt=True, solid=False)
        n.tag = patrol["tag"]
        n.dialogue_fn = None
        self.scene.add_npc(n)
        return n

    def _trigger_capture(self, patrol, npc, tier="low"):
        """Patrol caught the player at sub-closure proximity. Cuts
        to a short blackout, advances the in-world day by one,
        wakes the player back in the cot scene, ratchets Pursuer
        proximity by 0.25 (the line tightens with every capture).

        Two tiers:
          * 'low'  (Pursuer < 0.55) -- the soft setback. Items
                                       intact. Time + ground lost.
          * 'mid'  (0.55 <= Pursuer < 0.85) -- the cult searches
                                       the player. Flashlight
                                       battery drained to 0; any
                                       spare_batteries removed
                                       from inventory. Lore /
                                       evidence items preserved
                                       (the cult doesn't read
                                       what you've found, just
                                       takes the lights).

        The capture line varies per patroller (and tier) so the
        player gets feedback on what just happened to them."""
        # Per-tier per-patrol line. Tier-specific lines live in
        # `mid`; anything missing falls back to the `low` line.
        low_lines = {
            "patrol_preacher": "The Preacher whispers something. Then nothing.",
            "patrol_cultist": "They take you. You wake up later.",
            "patrol_choir": "The choir circles you. Their hands are on you.",
            "patrol_hound": "The dog has you down. You wake up bandaged.",
        }
        mid_lines = {
            "patrol_preacher": "The Preacher empties your pockets. Softly.",
            "patrol_cultist": "They pat you down. They take the batteries.",
            "patrol_choir": "Small hands in your coat. The lights are gone.",
            "patrol_hound": "They pull you off the dog. Your pockets are lighter.",
        }
        line_pool = mid_lines if tier == "mid" else low_lines
        line = line_pool.get(
            patrol["tag"],
            low_lines.get(patrol["tag"], "They take you. You wake up later."))
        self.audio.force_silence()
        self.audio.play("low_pulse", 0.85)
        self.show_notice(line, duration=4.0)
        # Day advances; Pursuer ratchet. Day_phase resets to
        # "morning" too -- without this, a player captured at
        # night would wake on the next day_count but with the
        # phase still "night", and walking out of the bedroom
        # would step them into night patrols immediately
        # (re-capture loop). Capture costs the day, not the
        # night.
        self.save.set_arg(
            "day_count", self.save.arg("day_count", 1) + 1
        )
        self.save.set_arg("day_phase", "morning")
        self.save.set_flag(
            f"captured_by_{patrol['tag']}", True
        )
        self._provoke_cult(0.25)
        # Mid-tier extra: the cult searches the player. Flashlight
        # battery drained, all spare_batteries taken. Pure
        # mechanical sting on top of the setback.
        if tier == "mid":
            self.player.battery_charge = 0
            inv = self.player.inventory
            while inv.has("spare_batteries"):
                inv.remove("spare_batteries", 99)
            # If the player had the flashlight on, force it off
            # so the toggle state isn't lying when they wake up.
            self.player.flashlight_on = False
            self.save.set_flag(
                f"searched_by_{patrol['tag']}", True
            )
        # The world bears witness. Each non-closure capture deposits
        # one persistent trace decoration in a frequently-visited
        # scene; the player wakes up but the world keeps a tally
        # they did not consent to. Scenes already loaded won't show
        # the new trace until next entry; this is intentional --
        # the trace appears the next time the player walks through
        # somewhere they thought was safe.
        n = self.save.arg("capture_traces", 0)
        if n < len(CAPTURE_TRACE_DEPOSITS):
            self.save.set_arg("capture_traces", n + 1)
        # Snap them back to the cot scene. Use the standard
        # transition so the fade hides the seam.
        self.begin_transition("bedroom", "default")

    def _on_patrol_spot(self, patrol, npc):
        """First time this patroller sees the player in this scene."""
        self.audio.play("low_pulse", 0.55)
        self.pursuer_proximity = min(1.0,
                                      self.pursuer_proximity + 0.20)
        # Different notice text per patroller for variety.
        line = {
            "patrol_preacher": "The Preacher has spotted you.",
            "patrol_cultist": "They see you.",
            "patrol_hunter": "It sees you. It has always seen you.",
            "patrol_choir": "The children stop singing. They look up.",
            "patrol_hound": "The dog catches your scent.",
        }.get(patrol["tag"], "They see you.")
        self.show_notice(line, duration=2.6)

    def _tick_kid_follower(self, dt):
        """If kid_follower_active and the kid isn't already in the
        scene, spawn him at the player's last position. Apply the
        follower walk-speed penalty and the Ire-pause to the
        proximity ramp."""
        if not self._kid_follower_active:
            return
        if self.scene is None or self.player is None:
            return
        kid = None
        for n in self.scene.npcs:
            if getattr(n, "tag", None) == "kid_follower":
                kid = n
                break
        if kid is None:
            from entities.npc import NPC
            kid = NPC(self.player.x - 18, self.player.y + 12,
                      "", "kid", voice="blip_kid", portrait="kid",
                      movement="follower", speed=1.5,
                      solid=False, no_prompt=True)
            kid.tag = "kid_follower"
            kid.dialogue_fn = None
            self.scene.add_npc(kid)

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
        # Cooldown drain
        if p.sprint_cd > 0:
            p.sprint_cd -= dt
            if p.sprint_cd <= 0:
                p.sprint_cd = 0.0
                # Cooldown done -- refresh the sprint window.
                p.sprint_t = p.sprint_t_max
        # Sprint logic
        if shift_held and p.sprint_cd <= 0 and p.sprint_t > 0:
            if not p.sprint_active:
                p.sprint_active = True
            p.sprint_t -= dt
            if self.save.flag("cult_provoked"):
                self.pursuer_proximity = min(
                    1.0, self.pursuer_proximity + dt * 0.05
                )
            # Periodic loud step every ~0.35s so the Pursuer hears.
            self._sprint_step_t = getattr(self, "_sprint_step_t", 0.0) - dt
            if self._sprint_step_t <= 0:
                self._sprint_step_t = 0.35
                self.audio.play("phantom_step", 0.55)
            if p.sprint_t <= 0:
                p.sprint_t = 0.0
                p.sprint_active = False
                p.sprint_cd = p.sprint_cd_max
        else:
            if p.sprint_active:
                p.sprint_active = False

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
        prox = self.pursuer_proximity
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

    def _tick_pursuer(self, dt):
        """Run the Pursuer's life. The Pursuer is invisible -- this
        method only schedules audio events, notices, and (eventually)
        the closure countdown that ends the game.

        Proximity ramps:
          * +0.005/sec passively (about 3 minutes from 0 to 1)
          * +0.02/sec while the player is standing still
          * -0.04 on every scene transition (the door delays it)
          * +0.10 on the rare moment the player passes through the
            same exit twice in a short window (it has noticed)

        The set of audio events tightens as proximity grows: at low
        proximity it's mostly distant doors; at high proximity it's
        breath cues every few seconds and a low_pulse pulse that
        kicks in once per minute. Past ~0.95 the closure timer arms,
        and once that hits zero, _trigger_closure is called."""
        if self.scene is None or self.player is None:
            return
        self._pursuer_t += dt
        # Passive + stillness ramps are dormant until the cult is
        # provoked (see _provoke_cult). The line doesn't tighten on
        # an outsider who hasn't done anything yet.
        if self.save.flag("cult_provoked"):
            passive_rate = 0.005
            if self.player.hidden is not None:
                passive_rate *= 0.5
            self.pursuer_proximity += dt * passive_rate
            if self.stillness_t > 1.5 and self.player.hidden is None:
                self.pursuer_proximity += dt * 0.02
        # Kid follower: the cult is owed him, so the Pursuer holds
        # back -- they expect to collect at the doorframe. Cap proximity
        # below the apex band while he's with the player AND the
        # threshold scene hasn't been reached. The cap LIFTS the
        # instant the player enters `threshold` with the kid (handled
        # in `_kid_threshold_arrival`), spiking proximity to 0.95 so
        # the closure timer arms right as the kid steps onto the slab.
        if (self._kid_follower_active
                and not self.save.flag("kid_at_threshold")
                and self._pursuer_closure_t < 0):
            self.pursuer_proximity = min(self.pursuer_proximity, 0.70)
        # Cap at 1.0 unless closure is already armed.
        if self._pursuer_closure_t < 0:
            self.pursuer_proximity = min(1.0, self.pursuer_proximity)
        # Closure arming: at 0.95+ proximity, start an 18-second
        # countdown to the ending.
        if (self.pursuer_proximity >= 0.95
                and self._pursuer_closure_t < 0):
            self._pursuer_closure_t = 18.0
            # A long low pulse marks the moment the Pursuer steps
            # over the threshold. The apex also tears the world
            # down: music cuts to silence (force_silence latches
            # until ending dispatch), the screen wash goes red and
            # the edges crush in -- handled in _draw_apex_overlay.
            self.audio.play("low_pulse", 0.85)
            self.audio.force_silence()
            self.show_notice("It is in this room.", duration=4.0)
            # Held silhouette: ~110ms of a screen-centred black
            # figure on top of the red wash. Long enough to be
            # noticed, short enough to not be confused for a draw
            # bug. The player will not be sure they saw it. The
            # actual draw is in _draw_apex_silhouette.
            self._apex_silhouette_t = 0.11
        if self._pursuer_closure_t > 0:
            self._pursuer_closure_t -= dt
            if self._pursuer_closure_t <= 0:
                self._trigger_closure()
                return
        # Schedule the next manifestation event. Interval scales
        # inversely with proximity: at 0.0, ~30s between events;
        # at 1.0, ~3s.
        self._pursuer_next_event -= dt
        if self._pursuer_next_event > 0:
            return
        # Pick the next interval before firing so the schedule keeps
        # ticking even if we early-out below. Apex band (>= 0.95)
        # collapses the cadence to ~1.6s so the breathing/pulse
        # feels directly overhead.
        prox = self.pursuer_proximity
        if prox >= 0.95:
            base = 1.6
            jitter = random.uniform(-0.4, 0.6)
            self._pursuer_next_event = max(0.8, base + jitter)
        else:
            base = 30.0 - prox * 26.0   # 30 .. 4
            jitter = random.uniform(-1.0, 3.0)
            self._pursuer_next_event = max(2.0, base + jitter)
        # Choose an event by proximity band. Notices are kept rare --
        # the audio cues are the narration; the on-screen text is for
        # the rare environmental beat the player cannot infer from
        # sound alone.
        events = []
        if prox < 0.30:
            events = ["distant_door", "phantom_step", "phantom_step"]
        elif prox < 0.55:
            events = ["distant_door", "phantom_step", "phantom_step",
                      "breath", "notice"]
        elif prox < 0.80:
            events = ["phantom_step", "phantom_step", "breath",
                      "breath", "low_pulse", "notice"]
        elif prox < 0.95:
            events = ["breath", "breath", "breath", "phantom_step",
                      "low_pulse", "notice"]
        else:
            # Apex: the breath is in the room. Drop the steps and
            # notices; everything is breath and bass pulse, almost
            # constant. The notice is gone -- there is nothing
            # left to "notice."
            events = ["breath", "breath", "breath", "breath",
                      "low_pulse", "low_pulse"]
        # Avoid immediate repeats so two breaths don't land back-to-back.
        candidates = [e for e in events if e != self._pursuer_last_event]
        if not candidates:
            candidates = events
        ev = random.choice(candidates)
        self._pursuer_last_event = ev
        # Spatial bias: pursuer cues come from one side of the player,
        # not the centre of their head. Steps + doors hard-pan; breath
        # rides close to centre with a subtle drift; low_pulse stays
        # centred (sub-bass localisation is weak anyway). Sign is
        # random per event so the player can't learn a side.
        side = random.choice((-1.0, 1.0))
        # Music duck: at mid-prox and above, drop the drone briefly so
        # the cue lands in negative space. The cue itself is queued to
        # fire ~0.5s after the duck starts so the gap is audible.
        ducking = prox >= 0.55 and ev in ("phantom_step", "breath",
                                           "distant_door")
        if ducking:
            self.audio.duck(1.6, depth=0.10)
            cue_delay = 0.5
        else:
            cue_delay = 0.0
        def _queue(name, vol, pan):
            if cue_delay <= 0:
                self.audio.play(name, vol, pan=pan)
            else:
                self._delayed_audio.append([cue_delay, name, vol, pan])
        if ev == "phantom_step":
            pan = side * random.uniform(0.55, 0.95)
            _queue("phantom_step", 0.50 + prox * 0.30, pan)
        elif ev == "distant_door":
            pan = side * random.uniform(0.40, 0.80)
            _queue("door_distant", 0.45 + prox * 0.30, pan)
        elif ev == "breath":
            pan = side * random.uniform(0.05, 0.25)
            _queue("breath", 0.40 + prox * 0.40, pan)
        elif ev == "low_pulse":
            self.audio.play("low_pulse", 0.55 + prox * 0.30)
        elif ev == "notice":
            self._pursuer_show_notice()

    def _pursuer_show_notice(self):
        """Pick a Pursuer notice line, avoiding immediate repeats,
        and surface it as a dim text overlay. The notices read as
        the player's own narration of what they heard -- the game
        never confirms it directly."""
        candidates = [n for n in self._pursuer_notices
                      if n != self._pursuer_last_notice]
        if not candidates:
            candidates = self._pursuer_notices
        line = random.choice(candidates)
        self._pursuer_last_notice = line
        self.show_notice(line, duration=2.6)

    # Until the cult is provoked, passive/stillness/sprint Pursuer
    # ramps stay dormant -- proximity holds at 0 even on long idle.
    # Provocation = doing something the cult notices: entering the
    # cult basement, picking up evidence, tripping a trespass camera,
    # being captured, the flashback hitting, the Innkeeper's
    # confrontation. Each transgression site calls _provoke_cult.
    def _provoke_cult(self, bump=0.0):
        if not self.save.flag("cult_provoked"):
            self.save.set_flag("cult_provoked", True)
        if bump > 0:
            self.pursuer_proximity = min(1.0,
                                          self.pursuer_proximity + bump)

    # ---- Innkeeper's confrontation ----
    # Cult-evidence inventory keys -- carrying any of these toward
    # the Innkeeper's front door triggers his block. The orb and the
    # robe are both sourced from his bedroom; the rubbing is the
    # player's own hand-made evidence; the notebook is Mom's.
    CULT_EVIDENCE_KEYS = ("orb", "robe", "sigil_rubbing", "mom_notebook",
                          "polaroid")

    def _check_innkeeper_confrontation(self, target_scene):
        """Return True (cancelling the transition) if the Innkeeper is
        about to block the player's exit. Triggers when the player
        carries cult evidence ITEMS or has accumulated enough
        evidence BEATS that the Innkeeper can read it on their face.

        Branching by what the player knows:
          * 'soft'  -- an item or 3+ beats. Mild line.
          * 'sharp' -- both an item AND 3+ beats. Sharper line.
          * 'lethal' -- 6+ beats AND a key cult item. The Innkeeper
                        stops pretending. Pursuer takes a much
                        bigger ratchet.

        Sets `innkeeper_intensity` to the chosen tier so downstream
        content (endings, NPC reactions, kid arc) can branch on it."""
        if self.scene is None or self.scene.key != "house":
            return False
        if target_scene != "our_house_area":
            return False
        if self.save.flag("innkeeper_confronted"):
            # Already confronted -- the front door is sealed. Treat
            # any future attempt as a soft block with a notice.
            self.audio.play("door_locked", 0.5)
            self.show_notice("He is in the doorway.")
            return True
        inv = self.player.inventory
        carrying = any(inv.has(k) for k in self.CULT_EVIDENCE_KEYS)
        # Evidence-beat count from the rich list. Tolerates the
        # legacy bare-string shape so old saves don't crash here.
        evidence_log = self.save.arg("evidence", [])
        if isinstance(evidence_log, list):
            beats = len(evidence_log)
        else:
            beats = 0
        # Trigger gate: either an item, OR 3+ beats. Knowledge alone
        # is enough -- the Innkeeper can see it on you.
        if not carrying and beats < 3:
            return False
        # Pick tier.
        if carrying and beats >= 6:
            tier = "lethal"
        elif carrying and beats >= 3:
            tier = "sharp"
        else:
            tier = "soft"
        self.save.set_flag("innkeeper_confronted", True)
        self.save.set_arg("innkeeper_intensity", tier)
        self.audio.play("low_pulse", 0.85)
        self.audio.force_silence()
        # Strip the wandering host so we don't end up with two
        # Innkeepers on screen.
        self.scene.npcs = [n for n in self.scene.npcs
                           if getattr(n, "tag", None) != "host_innkeeper"]
        # Plant the Innkeeper sprite in the front-door tile so he is
        # visibly standing there.
        from entities.npc import NPC
        nx = 6 * Scene.TILE + 16
        ny = 10 * Scene.TILE + 16
        host = NPC(nx, ny, "Innkeeper", "old",
                   solid=True, no_prompt=True,
                   voice="blip_low", portrait="old")
        host.facing = (0, -1)
        host.dialogue_fn = None
        host.tag = "blocking_innkeeper"
        self.scene.add_npc(host)
        # Push the player one tile north so the dialog lines up.
        self.player.y -= Scene.TILE
        # Tiered dialog. Each tier shows what the Innkeeper can read
        # on the player. The 'lethal' tier drops the host pretence
        # entirely.
        if tier == "lethal":
            if inv.has("polaroid"):
                self.dialog.show([
                    "Put it back.",
                    "[c=dim]She isn't yours to take. Not anymore.[/c]",
                    "[c=dim]You see her face going. That's the binding.[/c]",
                    "[c=dim]Put it back on the shelf and sit down.[/c][w=0.5]",
                    "He is not asking.",
                ], speaker="Innkeeper", voice="blip_low", portrait="old")
            else:
                self.dialog.show([
                    "You shouldn't have looked.",
                    "[c=dim]Did you think I didn't know what's in your pockets.[/c]",
                    "[c=dim]Sit. Down.[/c][w=0.5]",
                    "He is not asking.",
                ], speaker="Innkeeper", voice="blip_low", portrait="old")
            prox_bump = 0.40
        elif tier == "sharp":
            self.dialog.show([
                "Where do you think you're going.",
                "[c=dim]With my things in your hands. With that look on your face.[/c]",
                "[c=dim]Sit back down.[/c]",
            ], speaker="Innkeeper", voice="blip_low", portrait="old")
            prox_bump = 0.30
        else:  # soft
            self.dialog.show([
                "Where do you think you're going.",
                "[c=dim]I made coffee.[/c][w=0.4]",
                "[c=dim]Sit back down.[/c]",
            ], speaker="Innkeeper", voice="blip_low", portrait="old")
            prox_bump = 0.20
        self._provoke_cult(prox_bump)
        return True

    def _trigger_closure(self):
        """The Pursuer has reached the player. Hand off to the
        ending sequence. Implemented in _begin_threshold_closure;
        called once when the closure countdown hits zero."""
        # Guard so the closure can't re-trigger if proximity stays
        # pinned at 1.0 after the ending begins.
        if getattr(self, "_closure_started", False):
            return
        self._closure_started = True
        self._begin_threshold_closure()

    def _begin_pulled_through_closure(self):
        """Aperture-zero death in a dark scene: the King in Yellow
        has reached the player. Snap the player to the threshold
        scene, wipe the stage, then fire the pulled_through ending
        script. The cinematic plays while the player stands at the
        doorframe; final still fades and returns to title."""
        if getattr(self, "_closure_started", False):
            return
        self._closure_started = True
        self._closure_locked = True
        self.audio.force_silence()
        if self.scene is None or self.scene.key != "threshold":
            self.load_scene_now("threshold", "default")
        if self.scene is not None:
            self.scene.npcs = []
            self.scene.enemies = []
            self.scene.items = []
            self.scene.projectiles = []
        self._play_ending("pulled_through")

    def _begin_threshold_closure(self):
        """The Pursuer has reached the player. The threshold closes.

        THRESHOLD rework: the closure no longer stages a kid figure
        in the doorway. The room just goes still and dark. The
        player stands alone in the empty bedroom while the world
        ends. The kid arc lives entirely in the seal_threshold
        ending now, not in death.

        Sequence (driven by self._closure_phase, ticked in step):
          0  -> snap-load the bedroom, lock input, low_pulse drone.
          1  -> ~3 seconds of stillness on the still room.
          2  -> a few slow lines of dim narration.
          3  -> 8-second fade to pure black.
          4  -> title returns; proximity holds at 0.40 (never zero).
        """
        self._closure_phase = 0
        self._closure_phase_t = 0.0
        # Force-load the bedroom right now. Bypass begin_transition
        # so there's no fade in/out -- the world simply is the
        # bedroom. The Pursuer doesn't open a door; it puts you here.
        if self.scene is None or self.scene.key != "bedroom":
            self.load_scene_now("bedroom", "default")
        # Wipe NPCs, enemies, items, projectiles. The room reads
        # empty except for the player. No figure in the doorway.
        if self.scene is not None:
            self.scene.npcs = []
            self.scene.enemies = []
            self.scene.items = []
            self.scene.projectiles = []
        # Park the player in the lower portion of the room.
        if self.scene is not None and self.player is not None:
            self.player.x = self.scene.w * Scene.TILE // 2
            self.player.y = self.scene.h * Scene.TILE * 3 // 4
            self.player.facing = (0, -1)
        # Cut all music and start the low drone underneath.
        self.audio.force_silence()
        self.audio.play("low_pulse", 0.85)
        # Lock input. handle_event short-circuits everything except
        # advancing the dialog while _closure_locked is True.
        self._closure_locked = True
        self._update_camera(snap=True)

    def _tick_closure(self, dt):
        """Advance the closure sequence. Called from step() while
        `_closure_locked` is True. Walks through phases described in
        _begin_threshold_closure. No-op if the closure isn't the
        thing holding the input lock (an active ending also locks
        input but uses its own tick)."""
        if not getattr(self, "_closure_locked", False):
            return
        if self._ending_active:
            return
        if not hasattr(self, "_closure_phase_t"):
            return
        self._closure_phase_t += dt
        ph = self._closure_phase
        if ph == 0:
            # Brief pause on the still room.
            if self._closure_phase_t >= 1.5:
                self._closure_phase = 1
                self._closure_phase_t = 0.0
        elif ph == 1:
            # Held silence beat. The dim notice that the threshold
            # closed is already on screen from _trigger_closure.
            if self._closure_phase_t >= 3.0:
                # Plain, unattributed narration. No figure, no
                # voice -- just the room going still around you.
                self.dialog.show([
                    "[c=dim][s=slow]the room goes still.[/s][/c]",
                    "[c=dim][s=slow]the air won't move.[/s][/c]",
                    "[c=dim][s=slow]you don't turn around.[/s][/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                self._closure_phase = 2
                self._closure_phase_t = 0.0
        elif ph == 2:
            # Wait until the dialog's been dismissed (or auto-advance
            # after 14s if the player just sits).
            if not self.dialog.active or self._closure_phase_t >= 14.0:
                self.audio.play("breath", 0.85)
                self._closure_phase = 3
                self._closure_phase_t = 0.0
        elif ph == 3:
            # The slow fade. Drawn separately in draw_world via the
            # _closure_fade_alpha read.
            if self._closure_phase_t >= 8.0:
                self._closure_phase = 4
                self._closure_phase_t = 0.0
        elif ph == 4:
            # Hold on full black for 3s, then return to title.
            if self._closure_phase_t >= 3.0:
                self._closure_locked = False
                self._closure_started = False
                self._closure_phase = -1
                self.pursuer_proximity = 0.40   # not zero; never zero
                self._pursuer_closure_t = -1.0
                self.audio.music_muted = False
                self.state = "title"
                self.audio.play_music("threshold_drone")

    def _closure_fade_alpha(self):
        """Return the alpha [0..255] of the closure fade-to-black.
        Returns 0 if no closure is active. Phase 3 ramps 0->255 over
        8 seconds; phase 4 holds 255."""
        if not getattr(self, "_closure_locked", False):
            return 0
        ph = getattr(self, "_closure_phase", -1)
        if ph == 3:
            t = self._closure_phase_t / 8.0
            return max(0, min(255, int(t * 255)))
        if ph == 4:
            return 255
        return 0

    def _tick_dread(self, dt):
        """Stillness-driven heartbeat ramp. Engages while the player is
        standing still inside a CREEPY_SCENES key (or anywhere once
        `world_emptied` flips). The interval between beats tightens
        with each beat: 8s, 7s, 6s, ... down to 4s. Movement resets
        the count."""
        if self.scene is None:
            return
        in_creepy = (self.scene.key in CREEPY_SCENES
                     or self.save.flag("world_emptied"))
        if not in_creepy or self.stillness_t < 3.0:
            self._next_heartbeat_t = 0.0
            self._heartbeat_count = 0
            return
        self._next_heartbeat_t -= dt
        if self._next_heartbeat_t <= 0:
            self.audio.play("heartbeat", 0.35)
            interval = max(4.0, 8.0 - self._heartbeat_count * 0.5)
            self._next_heartbeat_t = interval
            self._heartbeat_count += 1

    # ---- Step ----
    def step(self, dt):
        keys = pygame.key.get_pressed()
        self.title_t += dt
        # Save-as-ritual short-circuits the normal play tick: while
        # the sleep state machine is running, the world holds still
        # except for the dialog/notice timers (so the post-save line
        # ticks down).
        if self._sleep_phase is not None:
            self._tick_sleeping(dt)
            self.dialog.update(dt)
            # Notice text intentionally does NOT tick down during the
            # sleep ritual -- the post-save "Day N. You slept." line
            # gets its full visible duration once the fade clears.
            return
        if self.state == "playing":
            self.update_player(dt, keys)
            if (not self.dialog.active and not self.inv_ui.open
                    and not self.notebook_ui.open
                    and not self.text_input.active):
                exit_data = self.scene.find_exit_at(self.player.x, self.player.y)
                if exit_data:
                    self.begin_transition(*exit_data)
            # Suspend scene update (NPC patrols, decoration anims, triggers)
            # while the text-input modal is active so the world freezes
            # behind the prompt.
            if not self.text_input.active:
                self.scene.update(dt, self)
            self.text_input.update(dt)
            for e in list(self.scene.enemies):
                if not self.text_input.active:
                    e.update(dt, self.scene, self.player)
                    if e.just_shot and e.shoot_sfx:
                        self.audio.play(e.shoot_sfx, 0.55)
                if not e.alive:
                    self.scene.enemies.remove(e)
            # Tick projectiles AFTER enemies so a brand-new shot doesn't
            # also move on the same frame it was fired (cleaner travel).
            if not self.text_input.active:
                for p in list(self.scene.projectiles):
                    p.update(dt, self.scene, self.player)
                    if p.hit:
                        self.audio.play("hit", 0.55)
                    if not p.alive:
                        self.scene.projectiles.remove(p)
                # Resolve friendly-projectile kills (pistol). Melee kills
                # are handled inline in apply_attack_damage; this sweeps
                # any enemies a bullet just flagged.
                for e in self.scene.enemies:
                    if e.alive and e.hp <= 0:
                        self._kill_enemy(e)
                # Sweep dead NPCs (killed by player melee or bullet).
                # Fire kill side-effects exactly once per NPC, then
                # remove them so they stop drawing and being patrolled.
                for n in list(self.scene.npcs):
                    if getattr(n, "alive", True):
                        continue
                    if not getattr(n, "_kill_processed", False):
                        n._kill_processed = True
                        self._kill_npc(n)
                    self.scene.npcs.remove(n)
            self.apply_attack_damage()
            if self.player.hp <= 0:
                self._on_player_death()
            self._update_camera()
            self.audio.update_silence()
            self.audio.update_duck()
            self.dialog.update(dt)
            self._tick_delayed_audio(dt)
            self._tick_dread(dt)
            self._tick_haunt_audio(dt)
            self._tick_visitor_silence(dt)
            self._tick_pursuer(dt)
            self._tick_heartbeat(dt)
            self._tick_apex_silhouette(dt)
            self._tick_visibility_dip(dt)
            self._tick_wake_muffle(dt)
            self._tick_watchers(dt)
            self._tick_eye_cameras(dt)
            self._tick_yk_tone(dt)
            self._tick_dread_aperture(dt)
            self._tick_flashlight(dt)
            self._tick_sheriff(dt)
            self._tick_kid_follower(dt)
            self._tick_closure(dt)
            self._tick_flashback(dt)
            self._tick_ending(dt)
            self._check_dusk_endings()
            # Push the player's world coords into Decoration's class
            # cache so the watching_eye decoration can rotate its
            # pupil toward the player every frame.
            from entities.decoration import Decoration as _Deco
            _Deco.player_world = (self.player.x, self.player.y)
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
        # village green rather than their bed. The world_emptied flag
        # is checked in load_scene_now so every scene from now on has
        # its npc list zeroed -- the layouts persist, the people don't.
        if self.scene and self.scene.key == "void_boss":
            self.save.set_flag("void_path_closed", True)
            self.save.set_flag("world_emptied", True)
            self.player.hp = self.player.max_hp
            self.show_notice("You wake on the village green. It is silent.")
            self.load_scene_now("village", "default")
            return
        self.player.hp = self.player.max_hp
        self.show_notice("You wake up in your bed.")
        self.load_scene_now("bedroom", "default")

    # ---- Draw ----
    def draw_world(self):
        self.screen.fill(C_BG)
        if not self.scene: return
        self.scene.draw(self.screen, self.cam_x, self.cam_y)
        for it in self.scene.items:
            sx = int(it["x"] - self.cam_x); sy = int(it["y"] - self.cam_y)
            t = pygame.time.get_ticks() / 200.0
            bob = int(math.sin(t + (it["x"] + it["y"]) * 0.01) * 1)
            color = self._item_color(it["key"])
            pygame.draw.rect(self.screen, color, (sx - 4, sy - 4 + bob, 8, 8))
            pygame.draw.rect(self.screen, C_BLACK, (sx - 4, sy - 4 + bob, 8, 8), 1)
        # Pick at most one NPC to "blink" this frame -- their eye dots
        # will skip drawing for a single frame. Only fires while the
        # player is standing still, and only rarely. The villagers
        # don't blink, except, very rarely, one does.
        blink_idx = -1
        if self.stillness_t > 1.5 and random.random() < 1 / 300:
            human_kinds = ("mom", "kid", "bandit", "policeman")
            human_npcs = [i for i, n in enumerate(self.scene.npcs)
                          if n.sprite_kind in human_kinds]
            if human_npcs:
                blink_idx = random.choice(human_npcs)
        for i, npc in enumerate(self.scene.npcs):
            sx = int(npc.x - self.cam_x); sy = int(npc.y - self.cam_y)
            draw_npc_sprite(self.screen, sx, sy, npc.sprite_kind, npc.facing,
                            blink=(i == blink_idx))
            # THRESHOLD: NPC name labels removed. They were the
            # last RPG-tell on screen -- the player should learn
            # who an NPC is by interacting with them, not by
            # reading a tag floating over their head. Strangers
            # on the road read as STRANGERS until they speak.
        for e in self.scene.enemies:
            e.draw(self.screen, self.cam_x, self.cam_y)
        for p in self.scene.projectiles:
            p.draw(self.screen, self.cam_x, self.cam_y)
        if self.player:
            psx = int(self.player.x - self.cam_x)
            psy = int(self.player.y - self.cam_y)
            if self.player.invuln > 0 and int(self.player.invuln * 12) % 2 == 0:
                pass
            elif self.player.hidden is not None:
                # THRESHOLD: hidden player draws on a low-alpha layer
                # so the silhouette is barely visible -- the cover
                # is reading as cover. Also draws a single faint
                # "[hidden]" tag above so the player knows the state
                # is on without needing a HUD widget.
                hide_layer = pygame.Surface((40, 60), pygame.SRCALPHA)
                draw_player_sprite(hide_layer, 20, 30, self.player.facing,
                                   0,
                                   armor=self.player.inventory.equipped["armor"],
                                   mud=getattr(self.player, "mud", 0.0),
                                   prone=getattr(self.player, "prone", False))
                hide_layer.set_alpha(80)
                self.screen.blit(hide_layer, (psx - 20, psy - 30))
                tag = self.fonts["tiny"].render("[hidden]", True,
                                                 (160, 158, 170))
                self.screen.blit(tag, (psx - tag.get_width() // 2,
                                       psy - 40))
            else:
                draw_player_sprite(self.screen, psx, psy, self.player.facing,
                                   self.player.walk_phase,
                                   armor=self.player.inventory.equipped["armor"],
                                   mud=getattr(self.player, "mud", 0.0),
                                   prone=getattr(self.player, "prone", False))
            # THRESHOLD: no swing visual, no charge ring -- the player
            # has no attack to telegraph.
        # THRESHOLD: legacy effects disabled.
        #   _draw_child_trailer: spawned a "kid sprite at the back of
        #     vision" in CREEPY_SCENES. In THRESHOLD the kid is a
        #     real follower NPC -- a phantom kid sprite tagging
        #     along confuses the relationship.
        #   _draw_giant_eye: a fading massive eye in mistlands /
        #     alter_room. Belonged to the alien-Visitors lore. The
        #     watching_eye decorations on cult sites carry the gaze
        #     in THRESHOLD; the giant overlay is gone.
        #   _draw_subliminal: 1-in-2000 random yellow_king /
        #     cultist flickers in the periphery.
        # Reset the per-frame full-screen darkness budget. Each
        # whole-screen black overlay below claims a slice via
        # _claim_dark() so the combined wash never exceeds
        # MAX_FULLSCREEN_DARK. The player's feet stay readable even
        # when hide + apex + dip + YK all stack.
        self._overlay_dark_used = 0
        self._draw_watchers()
        self._draw_mistlands_haze()
        self._draw_flashlight()
        self._draw_outdoor_vignette()
        self._draw_dusk_tint()
        self._draw_dread_ring()
        self._draw_yk_vignette()
        self._draw_apex_overlay()
        self._draw_hidden_overlay()
        self._draw_visibility_dip()
        self._draw_apex_silhouette()
        self._draw_pursuer_glimpse()
        self._draw_interact_prompt()
        self._draw_hud()
        self.dialog.draw(self.screen)
        self.inv_ui.draw(self.screen, self.player)
        self.notebook_ui.draw(self.screen)
        # Text-input modal (LOGIN: terminal etc.) drawn over inventory so
        # it always wins focus.
        self.text_input.draw(self.screen)
        if self.notice_text:
            self._draw_notice()
        if self.state == "transition":
            t = self.transition_t / 0.85
            alpha = int(t * 255) if self.transition_dir == "out" else int((1 - t) * 255)
            alpha = max(0, min(255, alpha))
            fade = pygame.Surface((SCREEN_W, SCREEN_H))
            fade.fill(C_BLACK)
            fade.set_alpha(alpha)
            self.screen.blit(fade, (0, 0))
        # Sleep ritual fade. Drawn over the world (and HUD) so the
        # screen genuinely darkens as the player drifts off and
        # comes back. Notice text still draws above this so the
        # "Day N. You slept." line is visible during fade_in.
        sleep_alpha = self._sleep_fade_alpha()
        if sleep_alpha > 0:
            sleep_fade = pygame.Surface((SCREEN_W, SCREEN_H))
            sleep_fade.fill(C_BLACK)
            sleep_fade.set_alpha(sleep_alpha)
            self.screen.blit(sleep_fade, (0, 0))
        # THRESHOLD: closure fade. Drawn over EVERYTHING (including
        # dialog) so the screen darkens through the final whispered
        # lines and settles to pure black before the title returns.
        closure_alpha = self._closure_fade_alpha()
        if closure_alpha > 0:
            fade = pygame.Surface((SCREEN_W, SCREEN_H))
            fade.fill(C_BLACK)
            fade.set_alpha(closure_alpha)
            self.screen.blit(fade, (0, 0))
        # Flashback overlay -- preempts everything (including the
        # closure fade) for the duration of the witnessing sequence.
        self._draw_flashback()
        # Ending overlay -- preempts everything during the four-
        # ending sequences.
        self._draw_ending()

    def _item_color(self, key):
        d = ITEM_DEFS.get(key, {})
        return {
            "weapon": (200, 200, 220),
            "armor":  (140, 110, 80),
            "consumable": (220, 80, 80),
            "key": (220, 200, 80),
            "lore": (180, 180, 220),
        }.get(d.get("kind"), (220, 220, 220))

    def _draw_interact_prompt(self):
        if (self.dialog.active or self.inv_ui.open or self.notebook_ui.open
                or self.text_input.active
                or self.state != "playing"):
            return
        for npc in self.scene.npcs:
            if getattr(npc, "no_prompt", False):
                continue
            d = math.hypot(npc.x - self.player.x, npc.y - self.player.y)
            if d < 40:
                sx = int(npc.x - self.cam_x)
                sy = int(npc.y - self.cam_y) - 40
                t = pygame.time.get_ticks() / 250.0
                yo = int(math.sin(t) * 2)
                txt = self.fonts["sm"].render("[E]", True, C_GOLD)
                self.screen.blit(txt, (sx - txt.get_width()//2, sy + yo))
                return

    def _draw_hud(self):
        """THRESHOLD HUD. No HP bar, no equipped-weapon label. The
        player has no health to track and no weapon they can use. All
        that's left is a small dim line in the corner that names the
        current threshold -- the only HUD element is an admission of
        where you've ended up."""
        if not self.player or not self.scene:
            return
        # Scene-name label, very small, very dim, lower-left.
        from scenes.base import scene_display_name
        scene_label = scene_display_name(self.scene)
        s = self.fonts["tiny"].render(scene_label, True, (60, 56, 70))
        self.screen.blit(s, (14, SCREEN_H - 22))
        # Threat meter -- thin bar upper-right. Tracks Pursuer
        # proximity (the threat fiction's spine). Stays dim and
        # quiet at low values; warms amber in the middle band; goes
        # bone-cold red and pulses at >= 0.95, where the Yellow King
        # avatar is loose. Player has no number, just a feel for
        # the line tightening.
        prox = max(0.0, min(1.0, self.pursuer_proximity))
        bar_w = 80
        bar_h = 4
        tx = SCREEN_W - 14 - bar_w
        ty = 14
        # Color blends with proximity. Dim violet -> amber -> red.
        if prox < 0.5:
            t = prox / 0.5
            col = (int(60 + (200 - 60) * t),
                   int(60 + (170 - 60) * t),
                   int(80 + (60 - 80) * t))
        else:
            t = (prox - 0.5) / 0.5
            col = (int(200 + (220 - 200) * t),
                   int(170 + (40 - 170) * t),
                   int(60 + (40 - 60) * t))
        # At max threat, pulse the fill so the bar feels alive --
        # signals the apex state where hiding is the only option.
        if prox >= 0.95:
            t_now = pygame.time.get_ticks() / 1000.0
            pulse = 0.6 + 0.4 * abs(math.sin(t_now * 3.0))
            col = (int(col[0] * pulse), int(col[1] * pulse),
                   int(col[2] * pulse))
        # Frame
        pygame.draw.rect(self.screen, (40, 36, 50),
                         (tx - 1, ty - 1, bar_w + 2, bar_h + 2), 1)
        # Fill
        pygame.draw.rect(self.screen, col,
                         (tx, ty, int(bar_w * prox), bar_h))
        # Battery indicator -- visible only when the player has the
        # flashlight AND it's on (or recently died). A thin bar in
        # the lower-right with a soft glow when lit.
        if self.player.inventory.has("flashlight"):
            bar_w = 60
            bar_h = 4
            bx = SCREEN_W - 14 - bar_w
            by = SCREEN_H - 18
            ratio = max(0.0, min(1.0, self.player.battery_charge
                                 / self.player.battery_max))
            # Background frame
            pygame.draw.rect(self.screen, (40, 36, 50),
                             (bx - 1, by - 1, bar_w + 2, bar_h + 2), 1)
            # Fill (warm yellow when on, dim grey when off)
            on = self.player.flashlight_on
            fill_col = (220, 200, 80) if on else (90, 84, 70)
            pygame.draw.rect(self.screen, fill_col,
                             (bx, by, int(bar_w * ratio), bar_h))
            # Tiny "F" label
            f_label = self.fonts["tiny"].render(
                "F", True, (140, 130, 110))
            self.screen.blit(f_label, (bx - 14, by - 3))

    def _draw_notice(self):
        s = self.fonts["sm"].render(self.notice_text, True, C_WHITE)
        bg = pygame.Surface((s.get_width() + 24, s.get_height() + 14), pygame.SRCALPHA)
        bg.fill((10, 8, 14, 220))
        x = SCREEN_W // 2 - bg.get_width() // 2
        y = 90
        self.screen.blit(bg, (x, y))
        self.screen.blit(s, (x + 12, y + 7))

    def show_notice(self, text, duration=2.5):
        self.notice_text = text
        self.notice_t = duration

    def draw_pause(self):
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        title = self.fonts["xl"].render("PAUSED", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 160))
        for i, opt in enumerate(self.pause_options):
            color = C_GOLD if i == self.pause_choice else C_WHITE
            label = f"> {opt}" if i == self.pause_choice else f"  {opt}"
            txt = self.fonts["lg"].render(label, True, color)
            self.screen.blit(txt, (SCREEN_W//2 - 90, 260 + i * 50))

    def pause_input(self, ev):
        if ev.type != pygame.KEYDOWN: return
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
            elif opt == "Quit to Title":
                # No autosave: the cot is the only save point.
                # Anything done since the last sleep is lost when
                # the player walks away. The pause menu warns by
                # not pretending otherwise.
                self.state = "title"
                # Back to the title drone -- the same wind-and-tritone
                # the player heard on launch.
                self.audio.play_music("threshold_drone")

    # ---- Save-as-ritual ----

    # Phase durations (seconds). Total ritual is ~4.1s.
    _SLEEP_PHASE_DURS = {
        "lay_down":   0.6,
        "fade_out":   1.0,
        "hold_black": 1.5,
        "fade_in":    1.0,
    }

    def _begin_sleep(self):
        """Enter the sleep ritual. Locks input, flips the player
        sprite to prone, and starts the lay_down phase. The
        actual save + day-advance fires in the middle of
        hold_black so the player sees the X mark advance as the
        screen comes back up."""
        if self._sleep_phase is not None:
            return
        self._sleep_phase = "lay_down"
        self._sleep_t = 0.0
        self._sleep_save_done = False
        if self.player is not None:
            self.player.prone = True
            # Snap player to the cot's interaction position so the
            # prone sprite reads as resting on the bedding.
            sc = self.scene
            if sc is not None and getattr(sc, "_cot_pos", None):
                self.player.x, self.player.y = sc._cot_pos

    def _tick_sleeping(self, dt):
        """Advance the sleep ritual. Called every frame from step()
        when `_sleep_phase` is set. The hold_black phase fires the
        actual _save_game() at its midpoint -- this is the only path
        through which the cot advances the day."""
        if self._sleep_phase is None:
            return
        self._sleep_t += dt
        dur = self._SLEEP_PHASE_DURS[self._sleep_phase]
        # Audio: lay_down dims the music; fade_out completes the cut.
        ch = getattr(self.audio, "music_channel", None)
        if self._sleep_phase == "lay_down":
            if ch is not None:
                try:
                    ch.set_volume(max(0.10, 1.0 - self._sleep_t / dur * 0.9))
                except Exception:
                    pass
        elif self._sleep_phase == "fade_out":
            if ch is not None:
                try:
                    ch.set_volume(max(0.0, 0.10 * (1.0 - self._sleep_t / dur)))
                except Exception:
                    pass
        elif self._sleep_phase == "hold_black":
            # At the midpoint of pure black, fire the save once.
            if not self._sleep_save_done and self._sleep_t >= 0.4:
                self._sleep_save_done = True
                self._save_game()
        elif self._sleep_phase == "fade_in":
            # Music ramps back in from silence to full as we fade up.
            if ch is not None:
                try:
                    ch.set_volume(min(1.0, self._sleep_t / dur))
                except Exception:
                    pass
        if self._sleep_t < dur:
            return
        self._sleep_t = 0.0
        order = ["lay_down", "fade_out", "hold_black", "fade_in"]
        idx = order.index(self._sleep_phase)
        if idx + 1 < len(order):
            self._sleep_phase = order[idx + 1]
        else:
            # Done.
            self._sleep_phase = None
            if self.player is not None:
                self.player.prone = False
            if ch is not None:
                try:
                    ch.set_volume(1.0)
                except Exception:
                    pass

    def _sleep_fade_alpha(self):
        """Black-overlay alpha for the current sleep phase. 0 when
        not sleeping. lay_down is unfaded (the room is still
        visible while you settle); fade_out ramps to full; hold
        is full; fade_in ramps back."""
        if self._sleep_phase is None:
            return 0
        dur = self._SLEEP_PHASE_DURS[self._sleep_phase]
        t = self._sleep_t / max(0.001, dur)
        if self._sleep_phase == "lay_down":
            return 0
        if self._sleep_phase == "fade_out":
            return int(min(255, t * 255))
        if self._sleep_phase == "hold_black":
            return 255
        if self._sleep_phase == "fade_in":
            return int(max(0, (1.0 - t) * 255))
        return 0

    def _save_game(self):
        self.save.data["player"] = self.player.to_save()
        self.save.data["inventory"] = self.player.inventory.to_save()
        # Sleeping in the cot advances the in-world day. Day count
        # also drives day_phase (morning/afternoon/dusk/night cycle)
        # so future content can gate events to specific days/phases.
        prev_day = self.save.arg("day_count", 1)
        day = prev_day + 1
        self.save.set_arg("day_count", day)
        self.save.set_arg("day_phase", _next_day_phase(
            self.save.arg("day_phase", "afternoon")))
        # Sleep flashback escalation. At proximity >= 0.55, every
        # sleep surfaces a fragment of the protagonist's hidden
        # history -- the still progression deepens across the run.
        # The horror is that skipping nights doesn't escape the
        # Ire; it shows you what you did. Tracked in save state so
        # the same fragment doesn't replay if the player saves and
        # quits between sleeps.
        # Read proximity BEFORE the post-sleep bleed below; the
        # check is on the pre-sleep state (the line tonight, not
        # the slackened one come morning).
        prox_at_sleep = self.pursuer_proximity
        # Sleeping is a real strategic verb: rest BLEEDS Pursuer
        # proximity by 0.20 (the line slackens overnight) and tops
        # the flashlight battery back up. Without this the player
        # had no mechanical reason to use the cot beyond saving --
        # making the cot a true risk/reward spot, since proximity
        # ramps right back up if you sleep too often or with cult
        # presence already in the room.
        self.pursuer_proximity = max(0.0,
                                      self.pursuer_proximity - 0.20)
        self.player.battery_charge = self.player.battery_max
        if (prox_at_sleep >= 0.55
                or prev_day >= DAY_NIGHT_BREAKS_AFTER):
            n_seen = self.save.arg("flashback_progress", 0)
            stills = len(self._flashback_stills)
            # Advance to the next still; once the run has shown
            # all five, sleep at high proximity continues to fire
            # the last (the gut-punch).
            phase_idx = min(n_seen, stills - 1)
            self._flashback_phase = phase_idx
            self._flashback_t = 0.0
            self.save.set_arg("flashback_progress",
                               min(stills, n_seen + 1))
        self.save.write()
        n = self.save.arg("save_count", 0) + 1
        self.save.set_arg("save_count", n)
        self.audio.play("threshold_chime", 0.55)
        # Day-7 cap: the night-gate breaks. The world stops having
        # mornings. Fire a one-shot notice the moment the player
        # wakes to the day after the threshold so the change is
        # legible, not just felt.
        if day == DAY_NIGHT_BREAKS_AFTER and not self.save.flag(
                "day_seven_announced"):
            self.save.set_flag("day_seven_announced", True)
            self.show_notice("There is no morning anymore.",
                              duration=4.0)
        else:
            self.show_notice(f"Day {day}. You slept. The line slackens.",
                              duration=3.0)
        # Sync the bedroom calendar so the X mark advances visibly
        # before the wake fade clears (when the save came from the
        # cot ritual). Also fires any key-date easter egg beats.
        self._sync_calendar()
        self._check_dated_events(day)

    def _sync_calendar(self):
        """Point the bedroom calendar decoration at the current
        day_count. Safe to call from any scene -- if the bedroom
        scene isn't loaded right now, the next bedroom_on_enter
        will resync from save state."""
        sc = self.scene
        if sc is None or sc.key != "bedroom":
            return
        deco = getattr(sc, "_calendar", None)
        if deco is None:
            return
        d = self.save.arg("day_count", 1)
        month, day_of_month = day_count_to_date(d)
        deco.kwargs["today_d"] = day_of_month
        deco.kwargs["month"] = month
        deco.kwargs["month_days"] = days_in_month(month)
        # Force the cached month-label to redraw if month changed.
        deco.kwargs["_label_cache"] = None

    def _check_dated_events(self, day):
        """Easter-egg horror beats keyed to the calendar. The player
        will only reach these by deliberately sleeping a lot, so the
        intent is atmospheric reward for the curious -- not gated
        progression. Each beat is one-shot via a per-event save flag
        so save-scumming the day boundary doesn't repeat them."""
        month, day_of_month = day_count_to_date(day)
        key = _KEY_DATES.get((month, day_of_month))
        if key is None:
            return
        flag = f"dated_event_{key}"
        if self.save.flag(flag):
            return
        self.save.set_flag(flag, True)
        if key == "halloween":
            # All Hallows' Eve: the cult's high holiday. The line
            # tightens hard despite the player having just slept.
            self.pursuer_proximity = min(1.0,
                                          self.pursuer_proximity + 0.25)
            self.audio.play("cult_chant", 0.45)
            self.show_notice("All Hallows' Eve. The town is humming.",
                              duration=4.0)
        elif key == "solstice":
            # The longest night. Brief inversion -- a single low
            # pulse, a whisper, and a notice. No mechanical bite;
            # this is texture for a player who slept their way here.
            self.audio.play("low_pulse", 0.55)
            self.audio.play("whisper", 0.40)
            self.show_notice("The longest night. The candle won't catch.",
                              duration=4.0)
        elif key == "new_years_eve":
            # The conceptual horizon. The protagonist counted to
            # this. The Pursuer is loud now. No closure forced --
            # the player can keep going past, but the calendar
            # rolls into Jan and the easter-egg track is over.
            self.pursuer_proximity = min(1.0,
                                          self.pursuer_proximity + 0.40)
            self.audio.play("yk_tone", 0.55)
            self.show_notice("New Year's Eve. You're still here.",
                              duration=5.0)

    # ---- Events / main loop ----
    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            # No autosave on window close. Save lives at the cot.
            pygame.quit(); sys.exit(0)
        if self.state == "title":
            self.title_input(ev); return
        if self.state == "paused":
            self.pause_input(ev); return
        # THRESHOLD: during the closure sequence, only allow advancing
        # the dialog. Everything else (movement, interaction, save,
        # pause, inventory) is locked. The player cannot escape the
        # ending by hitting ESC.
        if getattr(self, "_closure_locked", False):
            if self.dialog.active and ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                    self.dialog.advance()
            return
        # Sleep ritual: input is fully locked while the player is
        # asleep. F11 is the lone exception so toggling fullscreen
        # mid-fade still works.
        if self._sleep_phase is not None:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
                self._toggle_fullscreen()
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
                elif ev.key in (pygame.K_j, pygame.K_z):
                    # THRESHOLD: combat is gone. The attack input still
                    # registers so muscle memory doesn't cause UI bugs,
                    # but it does nothing. The player will press it once,
                    # then twice, then realise.
                    pass
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
                elif ev.key == pygame.K_ESCAPE:
                    self.state = "paused"
                    self.audio.play("menu_open", 0.6)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                pass  # No attack on click either.
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
