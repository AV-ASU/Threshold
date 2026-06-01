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
                               draw_axe_swing, draw_king_death,
                               door_mask_surface, reset_king_fx)
from rendering.transform import draw_vessel_bloom
from rendering.camera import Camera
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

# THRESHOLD: scene sets keyed to the cult fiction. The cult sites
# (cult_chamber, the cauldron clearing) bypass the standard fade --
# crossing into them is meant to feel like a snap, not a door.
VOID_SCENES = {"void_boss"}


# Day-phase cycle. Sleeping in the cot advances the phase by one
# Scenes where dread-state effects engage: the stillness heartbeat
# ramps up while the player stands still here, and the cult-site
# floors get the rare delayed-footstep trick.
CREEPY_SCENES = {"basement", "void_boss",
                 "haunted_house", "well_bottom", "well_passage",
                 "brimley"}


# Outdoor decay tier. Each scene gets a small list of "this is
# what's been added" decorations as Pursuer proximity climbs.
# Keyed by (scene, tier) -> list of (tx, ty, kind). Mid tier
# (proximity >= 0.33) plants a single subtle prop near a door or
# threshold; high tier (proximity >= 0.66) layers two more so the
# scene visibly worsens. Re-applied on every scene load -- the
# player coming back through after the line has tightened sees a
# changed world even though no NPC mentioned it.
#
# The brimley is intentionally absent: it's already heavily
# dressed, and a rework is in flight.
OUTDOOR_DECAY = {
    ("brimley", "mid"):       [(8, 7, "bloody_handprint")],
    ("brimley", "high"):      [(8, 7, "bloody_handprint"),
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
}

# Outdoor scenes -- everywhere the player is walking under sky.
# A soft always-on player-centred vignette darkens the world edges
# in these scenes so the world never feels safe between buildings.
# Brimley runs its own (heavier) vignette via _draw_brimley_haze
# and is intentionally NOT in this set so the two don't stack.
OUTDOOR_SCENES = {"our_house_area", "forest_path",
                  "void_boss", "graveyard",
                  "country_lane", "cornfield_maze",
                  "gravel_road_north", "river_crossing"}

# The continuous outside world. Crossing between any two of these is
# a seamless transition: no fade, no door sound, the player position
# is carried as a relative offset on the matching edge so they appear
# at the same lateral fraction of the destination's entry edge. The
# scenes are different sizes (intentionally -- they have different
# design jobs), but the EDGE BETWEEN them is continuous. Brimley is
# in this set even though it isn't in OUTDOOR_SCENES (it has its own
# vignette and doesn't want the outdoor one stacked on top).
SEAMLESS_WORLD_SCENES = OUTDOOR_SCENES | {
    "brimley",
    # Hidden fold scenes -- the player stumbles into them through
    # direction-sensitive exits and shouldn't feel a transition.
    "curse_grove", "lodge_arrival", "highway_walk",
    "husk_grove", "scarecrow_ring",
}

# How far (px) the camera leads the player in their facing direction so
# they can see where a path/fold is taking them before they walk into it.
# ~3 tiles -- enough lead to read a bend or a wrap-seam, small enough that
# the player stays comfortably on screen.
CAM_LOOKAHEAD = 96

# Dark scenes -- underground / interior cult sites where the
# flashlight matters. Without the flashlight the screen is heavily
# dimmed with a small clear circle around the player. With it,
# the dimness lifts to a wider cone in the facing direction.
DARK_SCENES = {"basement", "well_passage", "well_bottom",
               "works_vats", "works_sorting", "maras_room",
               "works_scriptorium",
               "works_sign", "works_deepstair",
               "haunted_house",
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

# Scenes where the reactive cult-ambient layer (proximity-driven
# cult_breath + cult_chant) runs. These are the rite spaces -- the
# Works rooms and the Depths corridors. The fire-and-forget per-scene
# _ambient hooks are scene colour; this layer is a SECOND layer that
# swells with cultist proximity and pans from the closest cultist.
CULT_AMBIENT_SCENES = {"works_vats", "works_sorting", "works_scriptorium",
                       "works_sign", "works_deepstair",
                       "depths_antechamber", "depths_procession",
                       "depths_hall", "depths_threshing", "depths_stair"}

# Safe interiors. Heavy overlays short-circuit here so the room
# reads cleanly. The Inn (bedroom + house) is the refuge that the
# rest of the world is pressing against -- standing inside should
# feel SAFE compared to outside. Hide vignette also suppressed
# (you are already safe; the cramped read is wrong here).
SAFE_SCENES = {"bedroom", "house", "son_room", "kid_house"}

# The King never manifests in these: the homey refuges above PLUS the two
# narrative set-pieces whose whole work is recognition / resolution rather
# than a chase -- the hive (dark) and the Threshold itself. Without this a
# curse carried down from the surface keeps spawning Watchers here (they
# ignore CULTIST_SCENES gating), drives visibility to 1.0, and lets the
# apex erupt in the one room that must not host him.
KING_FREE_SCENES = SAFE_SCENES | {"dark", "threshold"}

# Dim-but-clear interiors. The flashlight cone still draws -- the
# cellar wants the light -- but dread / apex / dip overlays are
# suppressed so the navigation read stays usable. Hide vignette
# still runs (cover here is meaningful).
DIM_SAFE_SCENES = {"basement"}

# ---- THRESHOLD: cult geography + threat tuning ----
# Regular cultists roam every outdoor scene; the safe lodge interiors
# (SAFE_SCENES) are the only refuge.
CULTIST_SCENES = {
    "forest_path", "our_house_area", "graveyard",
    "brimley", "country_lane",
    "gravel_road_north", "river_crossing", "backwoods_cabin",
    "cornfield_maze",
}
# Scenes open enough for His gaze to fix on you and bind a Watcher -- the
# claimed town under open sky (NARRATIVE.md 1b/3). There is NO curse-priest;
# the curse is His own attention. Safe rooms are exempt via KING_FREE_SCENES.
GAZE_BIND_SCENES = {"brimley", "graveyard", "cornfield_maze"}
# Sustained exposure (seconds) at high visibility before His eye fixes and the
# first Watcher opens; hiding / dropping visibility bleeds the timer back.
GAZE_BIND_TIME = 6.0
GAZE_BIND_VIS = 0.45          # visibility below which His gaze can't fix

# King "existence" range: it's a dark void at/beyond _FAR px from the player and
# fully manifests (blazing) by _NEAR px -- tune to slide the materialize window.
KING_THREAT_NEAR = 48.0        # px: fully real / blazing inside this
KING_THREAT_FAR = 340.0        # px: a dark void at/beyond this
WATCHER_SPAWN_INTERVAL = 4.0   # seconds between Watcher manifestations
# The watcher-curse (replaces the old permanent curse-level spiral): being
# cursed binds ONE Watcher to you; it clones (up to WATCHER_MAX) while you
# stay EXPOSED (in the open), and each live Watcher raises the visibility
# FLOOR. Clear them all -- stare each down for WATCHER_GAZE_DISPEL seconds,
# or put one down instantly with the axe or a round -- and the curse lifts.
WATCHER_MAX = 5                # the curse-swarm clones up to this many
# Walking through a FOLD or a seamless world-passage has this chance to
# manifest +1 Watcher on the far side. The first one BINDS the curse (it's
# what starts the cloning); later rolls add to the swarm. Never fires once
# the player already carries the max (WATCHER_MAX) -- that's the ceiling.
FOLD_WATCHER_CHANCE = 0.05     # 1 in 20 per fold/portal traversal
WATCHER_FLOOR = 0.12           # each live Watcher raises the visibility floor
WATCHER_CLONE_INTERVAL = 7.0   # seconds of EXPOSURE between clones
WATCHER_GAZE_DISPEL = 2.0      # seconds holding one in your gaze to dissolve it
VIS_FLOOR_TOTAL_CAP = 0.92     # summed floor stays just under the King (1.0)
CULT_REGULARS = 2              # roaming cultists kept per cult scene
CULT_TOPUP_INTERVAL = 8.0      # seconds between cultist (re)spawns

# Fold pursuit (Stage 3): a cultist hot on the player's heels follows them
# through a hidden FOLD (a direction-gated exit) "a beat behind" -- it
# re-emerges at the entry seam shortly after the player. Mundane exits
# (doors / ladders / ropes) are NOT folds: fleeing through ordinary
# architecture shakes the chase (the cult moves through the world's
# wrongness, not your ladders). Only the single nearest active chaser
# within FOLD_PURSUE_RANGE carries; it appears after FOLD_PURSUE_DELAY but
# never within FOLD_PURSUE_MIN_GAP of the player, and is forced in
# FOLD_PURSUE_FORCE seconds later so a dawdling player can't stall it.
FOLD_PURSUE_RANGE = 180.0    # px; pursuer must be this close to follow through
FOLD_PURSUE_DELAY = 0.7      # s; the beat-behind before it emerges
FOLD_PURSUE_MIN_GAP = 56.0   # px; never spawn on top of the player
FOLD_PURSUE_FORCE = 2.5      # s after the delay; emerge even if player lingers
# Axe swing: the player's only attack, gated on the splitting axe. A
# non-lethal arc that splinters barricades and STUNS a cultist/shadow.
MELEE_CD = 0.85                # seconds between swings
MELEE_STUN_DUR = 1.6           # seconds a target stays frozen
MELEE_REACH = 30               # px from the swing point a target must be
AXE_SWING_DUR = 0.34           # seconds the swing arc takes to draw
# The PI's pistol. Tied to the evidence count (NARRATIVE: the more you
# understand, the less the world lets you kill): below KING_GATE_EVIDENCE a
# clean shot KILLS a cultist; at/above it the round only STAGGERS. Limited
# ammo (pistol_ammo); starts with 8.
GUN_CD = 0.45                  # seconds between shots
GUN_DMG = 100                  # one clean shot kills any cultist (hp 1 or 30)
GUN_STUN_DUR = 1.4             # stagger time at 3+ evidence
# Shooting an innocent local is loud AND wrong: it ratchets visibility
# hard (the town turns its head) but is capped just under 1.0 so a single
# murder can't itself summon the King -- the meter still has to climb the
# last sliver on its own.
LOCAL_KILL_VIS_SPIKE = 0.35
LOCAL_KILL_VIS_CAP = 0.96
GUN_PROJECTILE_SPEED = 340
GUN_PROJECTILE_COLOR = (236, 232, 214)   # pale lead, distinct from cult amber
# Visibility rates, per second. Watchers + cultist gaze push the meter
# up; hiding pulls it down. Enough Watchers out-pace even hiding --
# that is the spiral toward a King the player can no longer shake.
VIS_HIDE_BLEED = 0.10
VIS_IDLE_DECAY = 0.02
VIS_WATCHER_OPEN = 0.03
VIS_WATCHER_HIDDEN = 0.015
VIS_GAZE = 0.12               # a cultist's gaze fills the meter fast
VIS_LIT_RISE = 0.045          # per second the flashlight is ON in the dark:
                              # light marks you, so visibility climbs. Net of
                              # idle decay this is a slow burn toward the King
                              # (~30s of held light, alone, to erupt him) --
                              # use the beam in bursts, not as a crutch.

# Evidence raises a VISIBILITY FLOOR: the more of the case you understand, the
# higher your baseline exposure. You can hide back down TO the floor but never
# below it -- so late, hiding stops saving you. The floor is summed from each
# logged evidence's weight (scenes.dialogue._evidence); deeper finds weigh more.
# Capped just under "unshakeable" so only the last beats pin him. (NARRATIVE §3.)
VIS_FLOOR_CAP = 0.9
EVIDENCE_FLOOR_DEFAULT = 0.10  # per-evidence floor weight if none recorded
# Investigating arms the apex. Below this many evidence, a maxed meter musters a
# cultist reinforcement wave at your entry instead of the King -- the net
# tightening, not yet lethal. At/above it, the same trigger brings the King.
KING_GATE_EVIDENCE = 3
REINFORCE_COUNT = 2            # cultists per wave
REINFORCE_COOLDOWN = 8.0      # seconds between waves (pulses, never floods)
# A small notebook-scribble toast flashes in a corner when a new evidence beat
# is logged -- the PI jotting it down. Diegetic "you wrote it down (and that's
# what doomed you)" feedback, paired with the floor seared a notch higher.
NOTEBOOK_TOAST_DUR = 1.4


# ~80% combined-darkness cap. The two full-screen black washes that
# can stack -- the apex/King wash (_draw_apex_overlay, claims twice:
# wash + edge) and the hide wash (_draw_hidden_overlay) -- route their
# alpha through _claim_dark, which decrements this budget per frame so
# the screen never goes fully opaque when both fire together. The
# player-centred radial vignettes, the scene gloom (_draw_dark) and the
# brimley haze draw directly and don't participate -- their clear
# centre already protects the player's feet.
MAX_FULLSCREEN_DARK = 204

# Brimley river entry tile (col 34 = east edge of the river, row 60).
# Walking from land onto this tile is the only way to enter the river.
# Once in the river, the player can move freely between river tiles
# until they step onto land or bridge, which flips in_river False.
RIVER_ENTRY_TILE = (34, 60)

# ---- Infestation (NARRATIVE §infestation) -----------------------------
# As the case is understood the surface rots, front-loaded to peak as the
# player commits underground at 3 evidence. The stage is min(3, evidence)
# for the surface (monotonic; the underground deepens past that on its own
# evidence clock). Two ways a local goes:
#   CONVERT -- the peace-makers cleanly join the cult (passive: they watch
#              and raise visibility, but never chase or grab). Keyed by
#              name -> the stage at which they turn.
#   MUTATE  -- the resisters keep their identity and their defiance, but
#              their bodies betray them (a render overlay of wrongness).
# Sheriff Vane is neither: at stage 3 he becomes a unique threat encounter
# in his own office (_spawn_hunting_sheriff).
# CONVERT -- peace-makers cleanly join the cult (passive). MUTATE -- the
# resisters whose flesh deforms into a bespoke fold-horror (Toby, Hettie,
# Garrick each have a dedicated incident in rendering.sprites /
# ui.dialog; Old Pell + Royce use the generic fallback). Values are the
# evidence stage at which they turn.
INFEST_CONVERT = {"A woman": 1, "Mrs. Calder": 2, "Royce": 3}
INFEST_MUTATE = {"Hettie": 2, "Garrick": 3, "Old Pell": 3,
                 "the Tisdale boy": 3}
# Underground is wrong from the first rung -- a baseline infestation even
# at 0 evidence, deepening on the full evidence count (not capped at 3).
UNDERGROUND_SCENES = {
    "well_bottom", "well_passage",
    "works_vats", "works_sorting", "works_scriptorium", "works_sign",
    "works_deepstair",
    "depths_antechamber", "depths_procession", "depths_hall",
    "depths_threshing", "depths_stair",
}


def _corpse_examine(game, npc):
    """E on a local you killed. A flat, dim line -- no absolution, just
    the fact of it lying there. Varies a little on repeat reads."""
    n = game.save.arg("corpse_reads", 0) + 1
    game.save.set_arg("corpse_reads", n)
    name = getattr(npc, "name", "A body")
    if n == 1:
        lines = [f"[c=dim]{name}. Face-down where the round put them. "
                 f"You did this.[/c]"]
    else:
        lines = ["[c=dim]Still here. The cold won't let it keep, and won't "
                 "let it go.[/c]"]
    game.dialog.show(lines, speaker="", voice="blip_soft", portrait="narrator")


def _converted_local_dialogue(game, npc):
    """A local who has made their peace and joined. They no longer answer
    as themselves -- they turn toward you and speak with the others'
    mouth. A flat, patient line; no name."""
    lines = [
        "[c=dim]They turn toward you, unhurried. The face is the one you "
        "knew. The voice underneath it is not.[/c]",
        "[c=dim]\"It's easier once you stop trying the doors.\"[/c]",
    ]
    game.dialog.show(lines, speaker="", voice="blip_soft", portrait="narrator")


# Mutated resisters: their flesh has turned, but they talk to you as if
# nothing has. The horror is the GAP -- a flat, mundane, domestic line
# delivered from a face that is now a wound. No cosmic-poetry; they report
# small specifics and don't acknowledge what they've become.
INFEST_MUTATE_LINES = {
    "Hettie": [
        "Truck still comes Thursdays. I unload it myself now.",
        "The driver won't get out of the cab anymore. That's all right. I "
        "manage the crates.",
        "[c=dim]Don't mind me. I've a customer face on. You get used to "
        "putting it on.[/c]",
    ],
    "the Tisdale boy": [
        "Mom set my place at supper. I sat down for it.",
        "[c=dim]It falls right through. I keep trying. She doesn't say "
        "anything.[/c]",
        "I can still talk. Listen. I sound just the same.",
    ],
    "Garrick": [
        "I still know everyone comes up this road. Don't need to look.",
        "[c=dim]Saw you coming a long way off. Didn't need eyes for it.[/c]",
        "You'll want to keep moving, son. I'd point you the way, but my "
        "arm doesn't.",
    ],
    "Old Pell": [
        "Crossed off the 14th this morning. It was already crossed.",
        "[c=dim]So I did it again, over the top. Mine's the heavier line. "
        "You can tell.[/c]",
    ],
}


def _mutated_local_dialogue(game, npc):
    """A resister whose flesh has turned. They speak to you flatly, about
    small ordinary things, from a face that is now a wound -- and never
    acknowledge it. The portrait shows their bespoke infested form."""
    name = getattr(npc, "name", "")
    lines = INFEST_MUTATE_LINES.get(name, [
        "[c=dim]They answer something ordinary, in their own voice. They "
        "do not seem to know what has happened to their face.[/c]",
    ])
    game.dialog.show(lines, speaker=name,
                     voice=getattr(npc, "voice", "blip_low"),
                     portrait=getattr(npc, "portrait", None),
                     infested=True)


class Game(CutsceneMixin):
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

        # ---- THRESHOLD: the visibility meter ----
        # `visibility` is a float in [0, 1]: how visible the player is
        # to the King in Yellow right now. Watchers (spawned by a
        # cultist's curse) raise it; hiding bleeds it back down. At 1.0
        # the King materialises at the doorway and hunts; drop below
        # 0.90 and he dissolves. See _tick_visibility + _tick_king.
        self.visibility = 0.0
        self._vis_floor = 0.0        # evidence-driven minimum (NARRATIVE §3)
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

        # ---- THRESHOLD: cultists, the curse, and Watchers ----
        # Regular cultists roam the outdoor scenes (chaser AI: scout,
        # chase on sight, search, investigate). Their gaze raises
        # visibility while they hold line of sight; contact spikes it.
        # The special curse-priest (a stalker) runs a ritual: hold the
        # player in its sightline long enough and it lands a *permanent*
        # curse. Each curse manifests Watchers -- staring figures only
        # the cursed sees -- and every Watcher pushes visibility up,
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

    def _draw_boot_screen(self):
        """A single quiet frame shown while Audio() synthesises the sound
        library at startup (a few seconds of blocking DSP). Keeps the window
        from reading as hung/black on launch. Drawn once, before the audio
        build -- no clock, no animation, just the title word and a hint."""
        self.screen.fill((4, 3, 7))
        word = self.fonts["title"].render("THRESHOLD", True, (60, 56, 70))
        self.screen.blit(word, (SCREEN_W // 2 - word.get_width() // 2,
                                SCREEN_H // 2 - word.get_height() // 2 - 10))
        sub = self.fonts["sm"].render("waking the dark .", True, (40, 38, 50))
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2,
                               SCREEN_H // 2 + 26))
        pygame.display.flip()
        # Pump the event queue once so the OS marks the window as responsive
        # rather than "Not Responding" during the synth that follows.
        pygame.event.pump()

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
            if i == self.title_choice:
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
        # Visibility meter + the King in Yellow
        self.visibility = 0.0
        self._vis_floor = 0.0
        self._chant_t = 0.0
        self._breath_t = 0.0
        self._heartbeat_t = 0.0
        self._king = None
        self._king_anchor = None
        reset_king_fx()        # clear his render trail/particles across runs
        self._reinforce_t = 0.0
        self._gun_cd = 0.0
        # Cultists, the curse, and Watchers
        self._cursed = False
        self._watchers = []
        self._watcher_clone_t = 0.0
        self._gaze_count = 0
        self._cult_topup_t = 0.0
        self.flashlight_on = False
        self._void_sting_played = False
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

    def load_scene_now(self, key, spawn_id="default", *, keep_music=False):
        if self.scene and self.scene.on_exit_fn:
            self.scene.on_exit_fn(self, self.scene)
        self.scene = load_scene(key)
        self.save.visit_scene(key)
        self.save.data["spawn"] = spawn_id
        spawn = self.scene.spawns.get(spawn_id, self.scene.spawns.get("default"))
        if spawn:
            self.player.x, self.player.y = spawn
        # The King materialises at the doorway the player entered from.
        # He stays behind on a scene change (cleared here) and re-forms
        # at the new entry if visibility is still pinned at the top.
        self._king = None
        reset_king_fx()        # his trail/particles don't follow across scenes
        self._king_anchor = (self.player.x, self.player.y)
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
        # innkeeper / guard / terminal handler placed by the builder or
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
                self.show_notice("You knock it back -- it won't stay "
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
                             "much -- they won't die for you anymore.",
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
            return False        # cultist: swept away, may re-form later
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

    # ---- Infestation -------------------------------------------------
    def _infest_stage(self):
        """Surface infestation stage 0..3, front-loaded to peak as the
        player commits underground at 3 evidence. Monotonic with the
        evidence count (knowing rots the world, and you can't un-know)."""
        return min(3, self._evidence_count())

    def _apply_infestation(self):
        """Re-derive the world's rot for the freshly-loaded scene from the
        evidence count. Scenes rebuild every load, so this is deterministic
        and additive each time -- never accumulates. Runs after on_enter so
        it can transform the live locals in place."""
        if self.scene is None:
            return
        key = self.scene.key
        surface_stage = self._infest_stage()
        underground = key in UNDERGROUND_SCENES
        if underground:
            # Wrong from the first rung: a baseline even at 0 evidence,
            # deepening on the FULL evidence count.
            self._infest_decals(max(1, self._evidence_count()), underground=True)
        elif surface_stage > 0:
            self._infest_decals(surface_stage, underground=False)
        # Locals turn (convert) or rot (mutate) on the surface.
        if surface_stage > 0:
            self._infest_locals(surface_stage)
        # Sheriff Vane's office becomes a unique threat at stage 3.
        if surface_stage >= 3 and key == "fisherman_cottage":
            self._spawn_hunting_sheriff()

    def _infest_decals(self, stage, underground=False):
        """Scatter escalating infestation decorations on walkable tiles,
        seeded by (scene, stage) so the spread is stable per load. Surface
        scenes (outdoor + the safe rooms at stage 3) and underground
        scenes only -- ordinary interiors are left to their own dressing."""
        key = self.scene.key
        surface = key in OUTDOOR_SCENES or key == "brimley"
        safe = key in SAFE_SCENES
        if not underground and not surface and not (safe and stage >= 3):
            return
        rng = random.Random((hash(key) ^ (stage * 2654435761)) & 0xffffffff)
        pool = ["phantom_mark", "dead_crow", "watching_wound"]
        if stage >= 2:
            pool += ["claw_marks", "yellow_sign", "gore", "bloodstain"]
        if stage >= 3 and not underground:
            pool += ["hanging_figure", "corn_doll", "watching_eye"]
        if underground:
            # Tight corridors: signs and wounds only, never a hanging body.
            pool = ["phantom_mark", "watching_wound", "yellow_sign",
                    "binding_sigil", "gore"]
        # Surface scenes get a heavier spread than the small safe rooms.
        per = 3 if (surface or underground) else 1
        count = stage * per
        spawns = list(self.scene.spawns.values())
        placed = tries = 0
        while placed < count and tries < count * 10:
            tries += 1
            tx = rng.randint(1, max(1, self.scene.w - 2))
            ty = rng.randint(1, max(1, self.scene.h - 2))
            wx, wy = tx * TILE + 16, ty * TILE + 16
            if self.scene.is_solid_at(wx, wy):
                continue
            if any(abs(wx - sx) < 28 and abs(wy - sy) < 28
                   for sx, sy in spawns):
                continue
            self.scene.add_decoration(Decoration(wx, wy, rng.choice(pool)))
            placed += 1

    def _infest_locals(self, stage):
        """Turn or rot the surface locals by name. Converts become passive
        cult (a 'cult_convert' tag -- _tick_cultists counts their gaze but
        they never grab); mutates keep themselves under a wrongness overlay."""
        for n in self.scene.npcs:
            if not getattr(n, "alive", True) or getattr(n, "_is_corpse", False):
                continue
            nm = getattr(n, "name", "")
            cs = INFEST_CONVERT.get(nm)
            ms = INFEST_MUTATE.get(nm)
            if cs is not None and stage >= cs:
                self._convert_local(n)
            elif ms is not None and stage >= ms:
                n._mutated = True
                # Their body has started speaking for the fold; the
                # dialogue curdles to match the overlay.
                n.dialogue_fn = _mutated_local_dialogue

    def _convert_local(self, n):
        """A peace-maker, joined. Becomes a masked cultist that watches
        you (raising visibility via the gaze count) but never chases or
        grabs -- passive cult. Their old dialogue is gone."""
        n.sprite_kind = "cultist"
        n.portrait = None
        n.tag = "cult_convert"
        n.movement = "watch"
        n.dialogue_fn = _converted_local_dialogue
        n.no_prompt = False
        n.solid = True
        n._gaze_range = 150
        n._mutated = False

    def _spawn_hunting_sheriff(self):
        """Stage 3: Sheriff Vane's office is no longer a place you visit.
        Replace the watching Sheriff with the hollow thing he became -- a
        unique, relentless pursuer. He holds for a beat (his last words),
        then comes for you. Reaching you ends the run (the 'sheriff' card).
        You escape by getting back out the door; he's slower than a run."""
        self.scene.npcs = [n for n in self.scene.npcs
                           if getattr(n, "name", "") != "Sheriff"]
        hx, hy = 8 * TILE + 16, 2 * TILE + 16
        s = NPC(hx, hy, "Sheriff Vane", "sheriff_hollow",
                movement="idle", solid=True, speed=0.78, tag="sheriff_hunt")
        s.dialogue_fn = None
        s.facing = (0, 1)
        self.scene.add_npc(s)
        self._sheriff_intro_t = 2.0
        self.show_notice("Sheriff Vane stands. \"I'm supposed to tell you "
                         "to leave, son. I can't say it anymore.\"",
                         duration=3.2)
        self.audio.play("low_pulse", 0.6)

    def _tick_sheriff(self, dt):
        """Drive the stage-3 Sheriff encounter: hold for the intro beat,
        then set him hunting (force-chase), and end the run if he reaches
        the player. No-op in any scene without a sheriff_hunt NPC."""
        if self.scene is None or self.player is None:
            return
        s = next((n for n in self.scene.npcs
                  if getattr(n, "tag", "") == "sheriff_hunt"
                  and getattr(n, "alive", True)), None)
        if s is None:
            return
        intro = getattr(self, "_sheriff_intro_t", 0.0)
        if intro > 0:
            self._sheriff_intro_t = intro - dt
            if self._sheriff_intro_t <= 0:
                s.movement = "chaser"
                s._force_chase = True
                self.audio.play("void_sting", 0.6)
            return
        d = math.hypot(s.x - self.player.x, s.y - self.player.y)
        if d < 24 and self.player.invuln <= 0:
            self._trigger_death("sheriff")

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

    def _draw_brimley_haze(self):
        """Atmospheric overlay. Brimley and alter_room always run the
        outdoor haze + vignette. EVERY OTHER SCENE also runs the
        outdoor haze + vignette while the player is carrying the
        playscript -- the playscript's presence is hostile, the world dims around
        it."""
        if self.scene is None:
            return
        key = self.scene.key
        # Safe / dim-safe interiors break the playscript-haze. Walking
        # back to the Inn (or the cellar) with the playscript is meant
        # to feel like a refuge from the hostile dim, not a
        # continuation of it.
        if key in SAFE_SCENES or key in DIM_SAFE_SCENES:
            return
        holds_playscript = (self.player is not None
                     and self.player.inventory.has("playscript"))
        if key == "brimley" or holds_playscript:
            self._draw_haze(170, (40, 40, 50, 80), 14, 24, 0.3, 30)
            self._draw_vignette()

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
        Wider clear hole and lower peak alpha than the brimley
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
        level = 1 if self.visibility > 0.55 else 0
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

    def _draw_apex_overlay(self):
        """Apex-tier rendering: when visibility hits >= 0.95,
        the world goes wrong. Heavy red wash across the whole screen
        (interiors and exteriors alike); the screen edges crush in
        with a hard black vignette so the player's view narrows;
        the overlay pulses on a slow sine so the dread reads as
        active, not static. Cheap: two SRCALPHA blits per frame."""
        if self.scene is None or self.player is None:
            return
        if self.visibility < 0.95:
            return
        # Safe / dim-safe interiors break the apex wash. The Inn is
        # the refuge. Standing inside it lifts the apex pressure --
        # only stepping out re-engages it. Reads as a deliberate
        # sanctuary mechanic rather than a hole in the horror.
        if (self.scene.key in KING_FREE_SCENES
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

    def _draw_dark(self):
        """Dark interiors/underground (DARK_SCENES) render as a navigable
        gloom: a moderate black tint over the whole scene so it reads
        dim-but-legible, with a clear pool around the player.

        With the flashlight LIT (`_flashlight_lit`) the near pool warms and
        a long beam cone is carved out of the gloom in the player's facing
        direction -- they can read the room far ahead. Without it, only a
        cold "eyes-adjusted" pool lifts the near floor out of pure black.
        Cult-dark rooms force the beam off (handled by `_flashlight_lit`)
        and sit a touch heavier."""
        if self.scene is None or self.player is None:
            return
        if self.scene.key not in DARK_SCENES:
            return
        from scenes.base import _light_pool
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        lit = self._flashlight_lit()
        # Build the beam cone geometry once (apex -> left -> tip -> right).
        cone = None
        if lit:
            fx, fy = getattr(self.player, "facing", (0, 1)) or (0, 1)
            flen = math.hypot(fx, fy) or 1.0
            ang = math.atan2(fy / flen, fx / flen)
            reach, spread = 300, math.radians(30)
            tip = (psx + reach * math.cos(ang), psy + reach * math.sin(ang))
            left = (psx + reach * math.cos(ang - spread),
                    psy + reach * math.sin(ang - spread))
            right = (psx + reach * math.cos(ang + spread),
                     psy + reach * math.sin(ang + spread))
            cone = [(psx, psy), left, tip, right]
        if lit:
            # A warm held-light pool at the feet -- not eyes adjusting.
            _light_pool(self.screen, psx, psy, 96, (240, 226, 165), 72)
        else:
            _light_pool(self.screen, psx, psy, 112, (118, 124, 150), 96)
        gloom = 130 if self.scene.key in CULT_DARK_SCENES else 100
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, gloom))
        rings = [(30 + i * 14, int(gloom * i / 8)) for i in range(8)]
        for rr, aa in sorted(rings, key=lambda p: -p[0]):
            pygame.draw.circle(overlay, (0, 0, 0, aa), (psx, psy), rr)
        if cone:
            # Carve the beam clear of the gloom (alpha 0 inside the cone).
            pygame.draw.polygon(overlay, (0, 0, 0, 0), cone)
        self.screen.blit(overlay, (0, 0))
        if cone:
            # A faint warm wash inside the cone sells it as a light source.
            beam = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.polygon(beam, (250, 232, 170, 26), cone)
            self.screen.blit(beam, (0, 0))

    def _draw_haze(self, base_alpha, fog_rgba, fog_n, drift_x, sway_amp,
                   sway_y_amt):
        """Reusable haze helper: a flat black tint at `base_alpha` plus
        `fog_n` drifting translucent SQUARE patches tinted `fog_rgba`.
        Used by the brimley overlay with different parameters."""
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
            self._flashback_masks = []
            self._flashback_pool = None
            self._flashback_spawn_acc = 0.0
            self._flashback_stab_done = False
            self.audio.force_silence()
            self.audio.play("low_pulse", 0.85)
            self.audio.flashback_air(True)        # wind + falling bed
        if self._flashback_phase is None:
            return
        self._flashback_t += dt
        self._spawn_flashback_masks(dt)
        _, dur = self._flashback_stills[self._flashback_phase]
        if self._flashback_t >= dur:
            self._flashback_phase += 1
            self._flashback_t = 0.0
            if self._flashback_phase >= len(self._flashback_stills):
                # Done -- restore music, play a final chord.
                self._flashback_phase = None
                self._flashback_masks = []
                self._flashback_pool = None
                self.audio.flashback_air(False)   # fade the falling bed out
                self.audio.music_muted = False
                self.audio.play("breath", 0.7)
                if self.scene and self.scene.music:
                    self.audio.play_music(self.scene.music)
                # Bump proximity hard -- the player KNOWS now.
                self._provoke_cult(0.20)
                self._log_dream_entry()

    _FB_GAZE = [(math.cos(a * math.tau / 8), math.sin(a * math.tau / 8))
                for a in range(8)] + [(0.0, 0.0)]

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
        (NARRATIVE 1b / spectrum note): the PI dreamed of the door exactly
        ONCE, a year ago -- walked up, looked in, met His eye for a blip, and
        never reached it; it never took root. Reading Mara's journal through
        REMINDS him of that single dream (what the flashback renders), and he
        sets it down as a half-dismissed memory -- NOT a recurring dream.
        Stored in save arg 'notes', NOT 'evidence': the evidence log is
        canonical-clues-only and its length is _evidence_count (the King-gate
        + infestation driver), so a note must never land there. The notebook
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
            "A door standing open in the dark -- no wall around it, just"
            " the frame, old dry wood.",
            "Light behind it the colour of old gold, breathing in and out"
            " like something asleep.",
            "I walked up. I looked in. For a blip something looked back --"
            " met my eye -- and then it broke.",
            "I never reached it. One dream, a year ago, and it never came"
            " again. So why do I know this place.",
        ]})
        self.save.set_arg("notes", notes)
        if hasattr(self, "_flash_notebook"):
            self._flash_notebook()

    def _log_case_entry(self):
        """Seed the case notebook with the PI's intake the moment a run
        begins. CANON (NARRATIVE 1/1b): the case is the LURE -- the King
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
            "His girl -- Mara, 26. Drove north in the spring. Stopped"
            " calling home by the thaw.",
            "Last address: Brimley. Had to find it on a map. North woods,"
            " near nothing.",
            "Skip-trace. A weekend's work -- ask around, turn up the girl,"
            " drive back by dawn.",
            "I don't take grief jobs. Took this one. Couldn't tell you why"
            " -- only that the not-knowing itched, and I wanted it gone.",
        ]})
        self.save.set_arg("notes", notes)

    # ---- Endings ----

    def _begin_car_escape(self):
        """The car at the river's edge. The fold only opens for a shard of His
        authority, so escape requires the SIGN (sigil_rubbing), not just the
        keys -- with it the engine catches for the first time and you drive out
        as the breach: SPREAD IT (NARRATIVE §1/§6)."""
        if self._ending_active:
            return
        if not (self.player and self.player.inventory.has("sigil_rubbing")):
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
            self.audio.play("arg_chime", 0.7)
        elif name == "rite_broken":
            # The dread drone for the mask-yank; the boom/roar come at the cut
            # (see _tick_rite_audio). Runs on the idle drive_channel.
            self._rite_cues = set()
            if self.audio.enabled:
                self.audio.drive_channel.play(self.audio.carcosa_drone_snd,
                                              loops=-1)
                self.audio.drive_channel.set_volume(0.0)
        else:
            self.audio.play("door_close", 0.7)

    # Ending scripts. Each is a list of (line, duration_seconds).
    # escape_alone is the SPREAD IT ending -- drive out with the Sign, the
    # only thing the fold opens for (NARRATIVE §1/§6). seal_threshold
    # (END IT) closes the Threshold on Brimley and on you (NARRATIVE §6).
    _ENDING_SCRIPTS = {
        "escape_alone": [
            ("You turn the key. The engine turns over.", 2.6),
            ("And over. The way it has every time before.", 2.6),
            ("Then -- with the Sign beside you -- it catches.", 3.0),
            ("You drive out, past the corn that never ended.", 3.2),
            ("You got out. You're the only one who ever has.", 3.4),
            ("Everyone will understand why, soon.", 3.8),
        ],
        "seal_threshold": [
            ("The frame drinks it down -- the smoke, the sound, the long "
             "way you came.", 3.0),
            ("Above you the stair grinds shut. Then the Works. Then the "
             "well.", 3.0),
            ("Brimley folds the rest of the way closed -- around the "
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

    def _tick_ending(self, dt):
        """Walk through the active ending's stills. Each phase is a
        single line shown for its specified duration via the same
        overlay system as the flashback."""
        if not self._ending_active:
            return
        self._ending_phase_t += dt
        if self._ending_active == "rite_broken" and self.audio.enabled:
            self._tick_rite_audio()
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

    def _end_ending(self):
        """Wrap up the ending sequence and return to title."""
        if self.audio.enabled:
            self.audio.drive_channel.fadeout(300)
        self._ending_active = None
        self._ending_phase = 0
        self._ending_phase_t = 0.0
        self._closure_locked = False
        self.audio.music_muted = False
        self.state = "title"
        self.audio.play_music("threshold_drone")

    def _tick_cultists(self, dt):
        """Regular cultists roam every outdoor scene (chaser AI: scout,
        chase on sight, search, investigate). Their gaze raises
        visibility while they hold line of sight, and contact spikes it
        -- but they never kill (the King is the only kill). The special
        curse-priest runs a ritual: hold the player in its sightline
        long enough and a permanent curse lands. Safe interiors are
        refuges -- no cultists, and the gaze-pressure lifts."""
        self._gaze_count = 0
        if self.scene is None or self.player is None:
            return
        key = self.scene.key
        # Safe interiors + non-cult scenes: sweep any strays and bail.
        if key in SAFE_SCENES or key not in CULTIST_SCENES:
            if any(str(getattr(n, "tag", "")).startswith("cult_")
                   for n in self.scene.npcs):
                self.scene.npcs = [
                    n for n in self.scene.npcs
                    if not str(getattr(n, "tag", "")).startswith("cult_")
                ]
            return
        self._ensure_cultists(key, dt)
        hidden = self.player.hidden is not None
        for n in self.scene.npcs:
            tag = getattr(n, "tag", "")
            if not isinstance(tag, str) or not tag.startswith("cult_"):
                continue
            if getattr(n, "_stun_t", 0) > 0:
                continue                     # shoved: blind + can't grab
            d = math.hypot(n.x - self.player.x, n.y - self.player.y)
            sees = (d < getattr(n, "_gaze_range", 180)) and not hidden
            if sees:
                self._gaze_count += 1
            if tag == "cult_convert":
                # A turned local: passive cult. Their watching raises
                # visibility (counted above) but they never chase, spot,
                # grab, or flank. The fallen town just stares.
                continue
            # Regular cultist: one "they've seen you" beat per fresh
            # spawn. Reaching you is the cult TAKING you -- the CAPTURED
            # card, then the run ends (you feed the hive). Not a kill.
            if sees and not getattr(n, "_has_been_spotted", False):
                n._has_been_spotted = True
                self.audio.play("low_pulse", 0.5)
                self.show_notice("They've seen you.", duration=2.4)
            if d < 22 and not hidden and self.player.invuln <= 0:
                self._trigger_death("cultist")
                return
        self._flank_cultists()

    def _tick_gaze_bind(self, dt):
        """His gaze, binding the curse (NARRATIVE 1b/3) -- replaces the old
        curse-priest ritual. In a GAZE_BIND_SCENES scene, staying EXPOSED (not
        hidden) while visibility is high lets His eye fix on you: a timer
        climbs, and crossing GAZE_BIND_TIME binds the first Watcher. Hiding,
        or dropping below GAZE_BIND_VIS, bleeds the timer back -- cover and
        keeping your head down are the only way out. Once cursed, the Watcher
        system (_tick_watchers) owns the swarm; this only lands the seed."""
        if self._cursed:
            self._gaze_bind_t = 0.0
            return
        if (self.scene is None or self.player is None
                or self.scene.key not in GAZE_BIND_SCENES
                or self.scene.key in KING_FREE_SCENES):
            self._gaze_bind_t = 0.0
            return
        exposed = (self.player.hidden is None
                   and self.visibility >= GAZE_BIND_VIS)
        t = getattr(self, "_gaze_bind_t", 0.0)
        if exposed:
            if t == 0.0:
                self.audio.play("low_pulse", 0.6)
                self.show_notice("You feel it find you. Get out of the open.",
                                 duration=3.0)
            t += dt
            if t >= GAZE_BIND_TIME:
                self._apply_curse()
                t = 0.0
        else:
            t = max(0.0, t - dt * 1.5)
        self._gaze_bind_t = t

    def _ensure_cultists(self, key, dt):
        """Keep the current cult scene topped up with CULT_REGULARS roaming
        cultists. Rate-limited so killing one buys a breather, not an instant
        respawn. (No curse-priest -- the watcher-curse is now His own gaze,
        bound in _tick_gaze_bind, not a priest's ritual; NARRATIVE 1b/3.)"""
        self._cult_topup_t -= dt
        if self._cult_topup_t > 0:
            return
        self._cult_topup_t = CULT_TOPUP_INTERVAL
        regulars = [n for n in self.scene.npcs
                    if getattr(n, "tag", "") == "cult_regular"
                    and getattr(n, "alive", True)]
        if len(regulars) < CULT_REGULARS:
            self._spawn_cultist("cult_regular", "cultist",
                                 speed=0.85, gaze_range=180)

    def _flank_cultists(self):
        """When 2+ regular cultists are chasing in an open scene, the
        closest leads a straight chase and the rest peel to perpendicular
        flanks to cut the player off. Tight scenes fall back to a
        straight pile-on."""
        chasers = [n for n in self.scene.npcs
                   if getattr(n, "tag", "") == "cult_regular"
                   and getattr(n, "_cult_state", "") == "chase"]
        if (len(chasers) >= 2
                and self._openness_around(self.player.x,
                                          self.player.y) >= 6):
            chasers.sort(key=lambda n: math.hypot(n.x - self.player.x,
                                                  n.y - self.player.y))
            leader = chasers[0]
            leader._flank_target = None
            for follower in chasers[1:]:
                ldx = self.player.x - leader.x
                ldy = self.player.y - leader.y
                ld = math.hypot(ldx, ldy) or 1.0
                offset = max(60.0, min(160.0, ld * 0.8))
                cand_a = (self.player.x + (-ldy / ld) * offset,
                          self.player.y + (ldx / ld) * offset)
                cand_b = (self.player.x + (ldy / ld) * offset,
                          self.player.y + (-ldx / ld) * offset)
                da = math.hypot(follower.x - cand_a[0],
                                follower.y - cand_a[1])
                db = math.hypot(follower.x - cand_b[0],
                                follower.y - cand_b[1])
                follower._flank_target = cand_a if da < db else cand_b
        else:
            for n in chasers:
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

    def _build_fold_cache(self):
        """After a scene load, find every SEEN fold in it (direction-gated
        exits) and pre-load the small set of target scenes once. A seen fold
        is drawn as a peek into its target (rendering.folds.draw_fold)."""
        self._folds = []
        scene = self.scene
        if scene is None:
            return
        from rendering.folds import _DIRV
        from scenes import load_scene
        cache = {}
        for ch, direction in scene.exit_directions.items():
            exit_data = scene.exits.get(ch)
            if not exit_data:
                continue
            target_key, spawn_id = exit_data
            pos = scene.find_marker(ch)
            if pos is None:
                continue
            tx, ty = pos
            if target_key not in cache:
                try:
                    cache[target_key] = load_scene(target_key)
                except Exception:
                    continue
            target = cache[target_key]
            # Look through the actual EXIT: aim the peek at the tile the
            # player will arrive on (the target's spawn for this exit's
            # spawn_id), so the peek frames where you'd emerge -- not some
            # arbitrary scene centre. Falls back to the centre if the spawn
            # is missing.
            spawn = target.spawns.get(spawn_id) or target.spawns.get("default")
            if spawn:
                anchor_tile = (int(spawn[0] // TILE), int(spawn[1] // TILE))
            else:
                anchor_tile = (target.w // 2, target.h // 2)
            self._folds.append({
                "normal": _DIRV.get(direction, (0, -1)),
                "target": target,
                "anchor_tile": anchor_tile,
                "fold_px": (tx * TILE + TILE // 2, ty * TILE + TILE // 2),
            })

    def _draw_folds(self):
        """Composite every seen fold in the current scene -- a one-sided peek
        into its target, only visible when the player faces into it."""
        folds = getattr(self, "_folds", None)
        if not folds or self.player is None:
            return
        from rendering.folds import draw_fold
        t = pygame.time.get_ticks() / 1000.0
        for face in folds:
            draw_fold(self.screen, face, self.cam_x, self.cam_y,
                      self.player, t)

    def _exit_is_fold(self, exit_data):
        """True if taking this exit is a FOLD or a seamless world-passage --
        the world's wrongness (a direction-gated fold) or its open ground (an
        outdoor-to-outdoor crossing). A mundane fade -- a door, ladder, or
        rope into an interior -- is NOT a fold. Shared by the fold-pursuit
        stash and the fold-watcher roll so both read 'fold' the same way."""
        if self.scene is None or self.player is None:
            return False
        target_scene = exit_data[0]
        ch = self.scene.char_object_at(self.player.x, self.player.y)
        is_fold = ch in self.scene.exit_directions
        cur = self.scene.key
        is_passage = (cur in SEAMLESS_WORLD_SCENES
                      and target_scene in SEAMLESS_WORLD_SCENES)
        return is_fold or is_passage

    def _roll_fold_watcher(self, exit_data):
        """Walking through a fold/portal has a FOLD_WATCHER_CHANCE (1/20) to
        manifest +1 Watcher -- the seed that STARTS the curse cloning. Called
        the instant an exit fires (before the swap); it BINDS the curse, and
        the destination's _tick_watchers then manifests the seed Watcher on
        arrival and begins cloning it. Never fires when the player already
        carries WATCHER_MAX -- that's the ceiling a fold can't push past. A
        SAFE destination is exempt (Watchers are only suppressed there)."""
        if not self._exit_is_fold(exit_data):
            return
        if exit_data[0] in SAFE_SCENES:
            return
        if len(self._watchers) >= WATCHER_MAX:   # already at the ceiling -- no +1
            return
        if random.random() >= FOLD_WATCHER_CHANCE:
            return
        self._cursed = True

    def _note_fold_pursuit(self, exit_data):
        """Called the instant an exit fires, BEFORE the scene swaps. If the
        exit is a hidden FOLD (a direction-gated exit) and a cultist is in
        active chase within FOLD_PURSUE_RANGE, stash that one pursuer so it
        can follow a beat behind. Any other exit -- door, ladder, rope --
        clears the stash: ordinary architecture shakes the chase. The
        refuge (SAFE_SCENES) is never breached."""
        target_scene, _spawn_id = exit_data
        # The cult moves through the world's wrongness AND its open ground:
        # a hidden fold (direction-gated) or a seamless outdoor passage both
        # carry the chase. Only a fade transition into an interior -- a door,
        # ladder, or rope -- shakes them. The refuge is never breached.
        if (not self._exit_is_fold(exit_data)) or target_scene in SAFE_SCENES:
            self._fold_pursuer = None
            return
        hot, hot_d = None, FOLD_PURSUE_RANGE
        for n in self.scene.npcs:
            if getattr(n, "movement", "") != "chaser":
                continue
            if getattr(n, "_cult_state", "") != "chase":
                continue
            if not getattr(n, "alive", True):
                continue
            d = math.hypot(n.x - self.player.x, n.y - self.player.y)
            if d <= hot_d:
                hot, hot_d = n, d
        if hot is None:
            self._fold_pursuer = None
            return
        # Just enough to rebuild it on the far side of the fold.
        self._fold_pursuer = {
            "kind": hot.sprite_kind,
            "speed": getattr(hot, "speed", 0.85),
            "gaze_range": getattr(hot, "_gaze_range", 180),
            "tag": getattr(hot, "tag", "cult_regular"),
        }

    def _tick_fold_pursuit(self, dt):
        """Spawn the stashed fold-pursuer a beat behind the player, at the
        seam they entered through -- never on top of them. It resumes the
        chase already knowing where the player is (it came through after
        them). Consumed once it fires."""
        if self._fold_pursuer is None or self.player is None:
            return
        info = self._fold_pursuer
        if "entry_tile" not in info:      # stashed but not yet armed by a load
            return
        self._fold_pursuer_grace -= dt
        if self._fold_pursuer_grace > 0:
            return
        et = info.get("entry_tile")
        if not et:
            self._fold_pursuer = None
            return
        sx = et[0] * TILE + TILE // 2
        sy = et[1] * TILE + TILE // 2
        gap = math.hypot(sx - self.player.x, sy - self.player.y)
        # Hold until the player steps off the seam -- unless they dawdle past
        # the force window, in which case the lunge lands anyway.
        if (gap < FOLD_PURSUE_MIN_GAP
                and self._fold_pursuer_grace > -FOLD_PURSUE_FORCE):
            return
        if self.scene.is_solid_at(sx, sy):
            self._fold_pursuer = None
            self._fold_pursuer_grace = 0.0
            return
        npc = self._spawn_cultist(info["tag"], info["kind"],
                                  speed=info["speed"],
                                  gaze_range=info["gaze_range"],
                                  at=(sx, sy))
        if npc is not None:
            npc._cult_state = "chase"
            npc._last_seen_pos = (self.player.x, self.player.y)
        self._fold_pursuer = None
        self._fold_pursuer_grace = 0.0

    def _spawn_cultist(self, tag, kind, speed=0.85, gaze_range=180,
                       movement="chaser", name="", at=None):
        """Plant a cultist. If `at` (x, y) is given and walkable, they enter
        there (the door you came in by -- for reinforcement waves); otherwise
        at the farthest walkable scene corner from the player, so they enter
        from the edges rather than on top of you. Returns the NPC, or None."""
        scene = self.scene
        best = None
        if at is not None:
            ax = at[0] + random.uniform(-12, 12)
            ay = at[1] + random.uniform(-12, 12)
            if not scene.is_solid_at(ax, ay):
                best = (ax, ay)
        if best is None:
            corners = [
                (4 * Scene.TILE, 4 * Scene.TILE),
                ((scene.w - 4) * Scene.TILE, 4 * Scene.TILE),
                (4 * Scene.TILE, (scene.h - 4) * Scene.TILE),
                ((scene.w - 4) * Scene.TILE, (scene.h - 4) * Scene.TILE),
            ]
            best_d = -1.0
            for sx, sy in corners:
                if scene.is_solid_at(sx, sy):
                    continue
                d = math.hypot(sx - self.player.x, sy - self.player.y)
                if d > best_d:
                    best_d, best = d, (sx, sy)
        if best is None:
            return None
        n = NPC(best[0], best[1], name, kind,
                voice="blip_low", portrait=None,
                movement=movement, speed=speed,
                no_prompt=True, solid=False)
        n.tag = tag
        n.dialogue_fn = None
        n._gaze_range = gaze_range
        n._has_been_spotted = False
        self.scene.add_npc(n)
        return n

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

    def _enemy_sees_player(self):
        """True if any hostile currently has line of sight on the
        player. Hostiles are the patrol/chaser NPCs; their sight
        range matches the chaser AI (180 px). Hiding (corn cover or
        a hide spot) breaks line of sight unconditionally, which is
        what makes cover the player's main tool for shedding threat."""
        if self.scene is None or self.player is None:
            return False
        if self.player.hidden is not None:
            return False
        px, py = self.player.x, self.player.y
        for n in self.scene.npcs:
            if not getattr(n, "alive", True):
                continue
            tag = getattr(n, "tag", None)
            hostile = ((isinstance(tag, str) and tag.startswith("patrol_"))
                       or getattr(n, "movement", None) in ("chaser",
                                                            "stalker"))
            if not hostile:
                continue
            if math.hypot(n.x - px, n.y - py) < 180:
                return True
        return False

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

    def _tick_visibility(self, dt):
        """The visibility meter [0, 1] -- how visible the player is to
        the King in Yellow. Watchers (spawned by a cultist's curse)
        push it up; hiding bleeds it down. At 1.0 the King materialises
        (see _tick_king); claw it back under 0.90 and he dissolves.

        Heavy curses tip the balance: enough Watchers out-pace even
        hiding -- the spiral toward a King the player can no longer
        shake."""
        if self.scene is None or self.player is None:
            return
        hidden = getattr(self.player, "hidden", None) is not None
        n_watch = len(self._watchers)
        # A burning flashlight marks you. The cost applies everywhere the
        # beam is lit EXCEPT the safe cellar (DIM_SAFE) -- there the light
        # is a free comfort, your one room to read by. Cover can't hide a
        # lit torch, so the rise lands in both branches.
        lit_rise = (VIS_LIT_RISE
                    if (self._flashlight_lit()
                        and self.scene.key not in DIM_SAFE_SCENES)
                    else 0.0)
        if hidden:
            # In cover the cult's gaze breaks; only a lit torch still leaks.
            self.visibility += dt * (lit_rise - VIS_HIDE_BLEED)
        else:
            rise = self._gaze_count * VIS_GAZE + lit_rise
            self.visibility += dt * (rise - VIS_IDLE_DECAY)
        # FLOORS the meter can't bleed below: evidence (the more you
        # understand, the higher your baseline) PLUS each live Watcher of the
        # curse. Capped just under the King so the curse presses you to the
        # edge but stays survivable -- and thus curable by clearing them.
        watcher_floor = n_watch * WATCHER_FLOOR
        self._vis_floor = min(VIS_FLOOR_TOTAL_CAP,
                              self._evidence_floor() + watcher_floor)
        self.visibility = max(self._vis_floor, min(1.0, self.visibility))

    def _evidence_count(self):
        """How many distinct evidence beats have been logged -- the gate
        that arms the King (NARRATIVE §3)."""
        log = self.save.arg("evidence", []) if self.save else []
        return len(log) if isinstance(log, list) else 0

    def _evidence_floor(self):
        """Visibility floor summed from each logged evidence's weight. The
        more of the case you understand, the higher your baseline exposure;
        capped just under unshakeable. Tolerates legacy bare-string entries."""
        log = self.save.arg("evidence", []) if self.save else []
        if not isinstance(log, list):
            return 0.0
        total = sum(e.get("weight", EVIDENCE_FLOOR_DEFAULT)
                    if isinstance(e, dict) else EVIDENCE_FLOOR_DEFAULT
                    for e in log)
        return min(VIS_FLOOR_CAP, total)

    def _tick_king(self, dt):
        """The King in Yellow -- the lethal apex. The instant
        visibility hits 1.0 he materialises at the doorway the player
        entered from and hunts relentlessly; reaching the player ends
        the run (the closure sequence). Drop visibility below 0.90 --
        by hiding -- and he dissolves. Safe rooms never host him."""
        if self.scene is None or self.player is None:
            return
        in_safe = self.scene.key in KING_FREE_SCENES
        if self._reinforce_t > 0:
            self._reinforce_t -= dt
        if self._king is None:
            self.audio.king_tone(False)
            if self.visibility >= 1.0 and not in_safe:
                # Investigating arms the apex: 3+ evidence and a maxed meter
                # bring the King himself; below that, only a cultist wave.
                if self._evidence_count() >= KING_GATE_EVIDENCE:
                    self._spawn_king()
                else:
                    self._muster_reinforcements()
            return
        # He is here. Dissolve if visibility falls or the player
        # reaches a refuge; otherwise check for the catch.
        if self.visibility < 0.90 or in_safe:
            self._despawn_king()
            return
        d = math.hypot(self._king.x - self.player.x,
                       self._king.y - self.player.y)
        # His signature tone loops while he's on screen and swells the closer
        # he gets -- the same nearness curve that cracks the mask open.
        prox = max(0.0, min(1.0, 1.0 - (d - KING_THREAT_NEAR) /
                            (KING_THREAT_FAR - KING_THREAT_NEAR)))
        self.audio.king_tone(True, 0.28 + 0.6 * prox)
        # Don't let the King catch mid-eruption: while _birth ramps
        # 0->1 (~1.2s, npc._yk_update) he can't move, so he mustn't
        # kill either -- that ramp is the player's grace window.
        if d < 24 and getattr(self._king, "_birth", 1.0) >= 1.0:
            self._trigger_death("king")

    def _muster_reinforcements(self):
        """Below the evidence gate, a maxed meter musters a cultist wave at the
        entry the player came in by -- the net tightening, not yet lethal.
        Pulsed on a cooldown so it never floods, and only where the cult can
        actually hold (CULTIST_SCENES); elsewhere the meter just sits maxed."""
        if self._reinforce_t > 0 or self.scene is None:
            return
        if self.scene.key not in CULTIST_SCENES:
            return
        self._reinforce_t = REINFORCE_COOLDOWN
        for _ in range(REINFORCE_COUNT):
            self._spawn_cultist("cult_regular", "cultist",
                                 speed=0.85, gaze_range=180,
                                 at=self._king_anchor)

    def _spawn_king(self):
        """Materialise the King at the entry doorway (_king_anchor),
        falling back to the player's position if no anchor was set."""
        ax, ay = self._king_anchor or (self.player.x, self.player.y)
        king = NPC(ax, ay, "", "yellow_king",
                   movement="chaser", speed=2.4,
                   no_prompt=True, solid=False)
        king.tag = "king"
        king.dialogue_fn = None
        king._birth = 0.0      # 0..1 eruption progress (renderer reads it)
        king._gait = 0.0       # run-cycle phase, advanced by movement
        self.scene.add_npc(king)
        self._king = king
        self.audio.play("void_sting", 0.7)

    def _despawn_king(self):
        if self._king is not None and self.scene is not None:
            try:
                self.scene.npcs.remove(self._king)
            except ValueError:
                pass
        self._king = None
        reset_king_fx()        # drop his trail/particles so they don't bleed on
        self.audio.king_tone(False)

    def _apply_curse(self):
        """Land the watcher-curse. Rather than a permanent escalation it
        BINDS a Watcher to you; it clones (up to WATCHER_MAX) while you stay
        exposed, and each live Watcher raises the visibility FLOOR. Clear
        them all -- stare each down, or put one down with the axe or a round
        -- and the curse lifts. Safe interiors only suppress them."""
        self.audio.play("void_sting", 0.8)
        if not self._cursed:
            self._cursed = True
            self._watcher_clone_t = WATCHER_CLONE_INTERVAL
            self.show_notice("Something has been bound to you. It will not "
                             "stop watching until you make it.", duration=3.8)
            self._spawn_watcher()
        else:
            self.visibility = min(1.0, self.visibility + 0.1)
            self.show_notice("The binding tightens. More will open.",
                             duration=3.0)

    def _tick_watchers(self, dt):
        """The watcher-curse. While cursed a Watcher is bound to the player
        and CLONES (up to WATCHER_MAX) while the player is EXPOSED (in the
        open); each live Watcher raises the visibility floor (in
        _tick_visibility). Safe interiors only suppress them -- they re-form
        on the way out. The curse lifts only when the player clears them all
        (gaze / axe / shot), handled in _dispel_watcher."""
        if self.scene is None or self.player is None:
            return
        # Drop any swept on load/death.
        self._watchers = [w for w in self._watchers if w in self.scene.npcs]
        if not self._cursed:
            if self._watchers:
                self.scene.npcs = [n for n in self.scene.npcs
                                   if getattr(n, "tag", "") != "watcher"]
                self._watchers = []
            return
        if self.scene.key in KING_FREE_SCENES:      # safe room: suppress only
            if self._watchers:
                self.scene.npcs = [n for n in self.scene.npcs
                                   if getattr(n, "tag", "") != "watcher"]
                self._watchers = []
            return
        if not self._watchers:                      # re-form the seed on exit
            self._spawn_watcher()
            self._watcher_clone_t = WATCHER_CLONE_INTERVAL
        # Cloning is EXPOSURE-gated: advances in the open, pauses in cover.
        if self.player.hidden is None and len(self._watchers) < WATCHER_MAX:
            self._watcher_clone_t -= dt
            if self._watcher_clone_t <= 0:
                self._watcher_clone_t = WATCHER_CLONE_INTERVAL
                self._spawn_watcher()
        # Staring one down dissolves it (the cure).
        self._tick_watcher_gaze(dt)

    def _spawn_watcher(self):
        """Manifest one Watcher at a walkable tile a little way off, in a
        random direction around the player. It stands and stares (the
        'watch' movement). A faint breath and a small visibility nudge
        mark the moment it opens its eyes."""
        scene = self.scene
        spot = None
        for _ in range(12):
            ang = random.uniform(0, math.tau)
            r = random.uniform(180, 300)
            wx = self.player.x + math.cos(ang) * r
            wy = self.player.y + math.sin(ang) * r
            if (0 < wx < scene.w * Scene.TILE
                    and 0 < wy < scene.h * Scene.TILE
                    and not scene.is_solid_at(wx, wy)):
                spot = (wx, wy)
                break
        if spot is None:
            return
        w = NPC(spot[0], spot[1], "", "watcher",
                voice="blip_low", portrait="watcher",
                movement="watch", speed=0.0,
                no_prompt=True, solid=False)
        w.tag = "watcher"
        w.dialogue_fn = None
        scene.add_npc(w)
        self._watchers.append(w)
        self.visibility = min(1.0, self.visibility + 0.03)
        self.audio.play("breath", 0.4)

    def _tick_watcher_gaze(self, dt):
        """Holding a Watcher in your gaze (facing it, within range) dissolves
        it over WATCHER_GAZE_DISPEL seconds -- its eyes are already dark while
        looked at. Look away and the progress bleeds back. This is the free
        (but slow, and exposed) way to clear them."""
        p = self.player
        fdx, fdy = p.facing
        for w in list(self._watchers):
            pdx, pdy = w.x - p.x, w.y - p.y
            d = math.hypot(pdx, pdy) or 1.0
            looking = ((pdx / d) * fdx + (pdy / d) * fdy) > 0.55 and d < 360
            gt = getattr(w, "_gaze_dispel_t", 0.0)
            if looking:
                gt += dt
                if gt >= WATCHER_GAZE_DISPEL:
                    self._dispel_watcher(w, reason="gaze")
                    continue
            else:
                gt = max(0.0, gt - dt * 1.5)
            w._gaze_dispel_t = gt

    def _dispel_watcher(self, w, reason="gaze"):
        """Dissolve one Watcher. If it was the last one and we're not merely
        being suppressed by a safe room, the curse lifts (you're cured)."""
        if w in self._watchers:
            self._watchers.remove(w)
        if self.scene is not None and w in self.scene.npcs:
            self.scene.npcs.remove(w)
        self.audio.play("breath" if reason == "gaze" else "void_sting", 0.45)
        if (self._cursed and not self._watchers and self.scene is not None
                and self.scene.key not in KING_FREE_SCENES):
            self._cursed = False
            self.show_notice("The last of the eyes closes. The curse lifts "
                             "-- for now.", duration=3.2)

    def _dispel_watcher_in_line(self, p, fx, fy):
        """A round (or the axe arc) puts a Watcher down instantly. The gun
        version: dissolve the nearest Watcher roughly along the facing line.
        Costs the same scarce round the shot already spent, and the report
        still draws the cult -- so it's the fast, loud, costly clear."""
        best, bestd = None, 1e9
        for w in self._watchers:
            pdx, pdy = w.x - p.x, w.y - p.y
            d = math.hypot(pdx, pdy) or 1.0
            if d > 520:
                continue
            if ((pdx / d) * fx + (pdy / d) * fy) < 0.82:   # must be ~in front
                continue
            if d < bestd:
                bestd, best = d, w
        if best is not None:
            self._dispel_watcher(best, reason="shot")

    # A transgression the cult notices -- entering the cult basement,
    # picking up evidence, tripping a trespass camera, being captured,
    # the flashback, the Clerk's confrontation. Spikes visibility by
    # `bump` (a one-off step toward being seen) and latches the
    # `cult_provoked` save flag.
    # NOTE: the flag is currently only a RECORD that provocation
    # happened -- nothing reads it to gate behaviour (cultist gaze
    # already drives visibility in CULTIST_SCENES from the start). It's
    # left as a hook for a future "dormant until provoked" gate; the
    # visibility bump is the live effect.
    def _provoke_cult(self, bump=0.0):
        if not self.save.flag("cult_provoked"):
            self.save.set_flag("cult_provoked", True)
        if bump > 0:
            self.visibility = min(1.0, self.visibility + bump)

    def _trigger_death(self, kind):
        """A pursuer has reached the player. Hand off to the death
        screen: `kind` is 'cultist' (the CAPTURED card -- the cult takes
        you alive for the hive) or 'king' (the King-in-Yellow furnace of
        masks / Carcosa, ~3.5s). Both end the run and return to title. Input
        is locked for the duration via _closure_locked (the shared
        sequence lock). Guarded so it can't re-trigger."""
        if self._death_kind is not None:
            return
        self._death_kind = kind
        self._death_t = 0.0
        self._closure_locked = True
        self.audio.force_silence()
        if kind == "king":
            self.audio.play("void_sting", 0.9)
            self.audio.play("low_pulse", 0.8)
        else:
            self.audio.play("low_pulse", 0.7)

    def _tick_death(self, dt):
        """Hold the death screen, then resolve -- both END the run.
        Cultist: ~2.8s CAPTURED card, then back to title (the cult took
        you for the hive). King: ~3.5s of the mask furnace (Carcosa),
        then back to title, visibility held at 0.40 (never zero)."""
        if self._death_kind is None:
            return
        self._death_t += dt
        if self._death_kind in ("cultist", "sheriff"):
            if self._death_t >= 2.8:
                self._death_kind = None
                self._closure_locked = False
                self.audio.music_muted = False
                self.state = "title"
                self.audio.play_music("threshold_drone")
        else:  # king
            if self._death_t >= 3.8:
                self._death_kind = None
                self._closure_locked = False
                self._king = None
                self.visibility = 0.40        # not zero; never zero
                self.audio.music_muted = False
                self.state = "title"
                self.audio.play_music("threshold_drone")

    def _draw_death_screen(self):
        """Render the active death card over everything. King = the
        furnace of masks (sprites.draw_king_death) stamped CARCOSA;
        cultist = a stark CAPTURED card over a near-black wash."""
        if self._death_kind == "king":
            draw_king_death(self.screen, self._death_t)
            if self._death_t > 3.0:                  # the name surfaces over the descent
                w, h = self.screen.get_size()
                ta = min(235, int((self._death_t - 3.0) / 0.55 * 235))
                tt = self.fonts["title"].render("CARCOSA", True, (236, 204, 64))
                tt.set_alpha(ta)
                self.screen.blit(tt, (w // 2 - tt.get_width() // 2,
                                      h // 2 - tt.get_height() // 2))
            return
        # Cultist: the cult takes you (CAPTURED). Sheriff: the hollow
        # lawman takes you in (TAKEN INTO CUSTODY). Fade to near-black,
        # then the card. The Sheriff card is tinted his dull tin-star gold.
        w, h = self.screen.get_size()
        fade = min(255, int(self._death_t / 0.4 * 255))
        wash = pygame.Surface((w, h))
        wash.fill((6, 5, 7))
        wash.set_alpha(fade)
        self.screen.blit(wash, (0, 0))
        if self._death_kind == "sheriff":
            label, col, sub = ("TAKEN INTO CUSTODY", (188, 172, 96),
                               "The badge was just clothing. The hold is not.")
        else:
            label, col, sub = ("CAPTURED", (170, 150, 90), None)
        if self._death_t > 0.35:
            ta = min(255, int((self._death_t - 0.35) / 0.4 * 255))
            big = self.fonts["title"].render(label, True, col)
            big.set_alpha(ta)
            self.screen.blit(big, (w // 2 - big.get_width() // 2,
                                   h // 2 - big.get_height() // 2))
            if sub and self._death_t > 0.9:
                sa = min(210, int((self._death_t - 0.9) / 0.5 * 210))
                st = self.fonts["sm"].render(sub, True, (150, 140, 110))
                st.set_alpha(sa)
                self.screen.blit(st, (w // 2 - st.get_width() // 2,
                                      h // 2 + big.get_height()))

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
                    # Stash a hot pursuer iff this exit is a FOLD; a mundane
                    # exit clears the stash (architecture shakes the chase).
                    self._note_fold_pursuit(exit_data)
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
                self._tick_king(dt)
            self._tick_wake_muffle(dt)
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

    # ---- Draw ----
    def draw_world(self):
        if self.state == "opening":
            self._draw_opening()
            return
        self.screen.fill(C_BG)
        if not self.scene: return
        # Re-sync the projection to the live camera offset for this frame.
        # (pitch/yaw stay 0 in Phase 1 -> identical to the legacy view.)
        self.camera.cam_x = self.cam_x
        self.camera.cam_y = self.cam_y
        self.scene.draw(self.screen, self.cam_x, self.cam_y)
        self._draw_folds()
        for it in self.scene.items:
            sx, sy = self.camera.project(it["x"], it["y"])
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
            human_kinds = ("townswoman", "tisdale_boy", "old_townsman",
                           "hettie", "sheriff", "royce", "preacher", "clerk")
            human_npcs = [i for i, n in enumerate(self.scene.npcs)
                          if n.sprite_kind in human_kinds]
            if human_npcs:
                blink_idx = random.choice(human_npcs)
        # Wrap-clone offsets. In a toroidal scene an actor near one seam
        # must also be drawn at the opposite edge, or it pops out of
        # existence when the player straddles the fold (decorations are
        # already cloned this way in Scene.draw). For non-wrap scenes
        # this is exactly [(0, 0)] -- identical to the old single draw.
        sc = self.scene
        _offsets = [(0, 0)]
        if sc.wrap_x:
            _ww = sc.w * TILE
            _offsets += [(-_ww, 0), (_ww, 0)]
        if sc.wrap_y:
            _wh = sc.h * TILE
            _offsets += [(0, -_wh), (0, _wh)]
        if sc.wrap_x and sc.wrap_y:
            _offsets += [(-_ww, -_wh), (-_ww, _wh), (_ww, -_wh), (_ww, _wh)]

        def _on_screen(sx, sy):
            return -64 <= sx <= SCREEN_W + 64 and -64 <= sy <= SCREEN_H + 64

        for i, npc in enumerate(self.scene.npcs):
            # A homebody currently inside their door: not drawn at all.
            if getattr(npc, "_inside", False):
                continue
            # A corpse: draw it prone in its blood and skip all the
            # living-NPC logic (morph, blink, king-threat, gaze). A fresh
            # kill (mold=0) -- corpses don't persist across loads anymore, so
            # there's no growing rot stage to track (NARRATIVE 1b/3).
            if not getattr(npc, "alive", True):
                for ox, oy in _offsets:
                    sx, sy = self.camera.project(npc.x + ox, npc.y + oy)
                    if not _on_screen(sx, sy):
                        continue
                    draw_npc_corpse(self.screen, sx, sy, npc.sprite_kind,
                                    seed=id(npc) & 0xffff, mold=0)
                continue
            m = getattr(npc, "morph", 0.0)
            king_threat = None
            if npc.sprite_kind == "yellow_king" and self.player:
                d = math.hypot(npc.x - self.player.x, npc.y - self.player.y)
                span = KING_THREAT_FAR - KING_THREAT_NEAR
                # Existence is purely proximity: a far void that blooms only
                # as he closes. Visibility is NOT mixed in here -- it's the
                # spawn/despawn gate (_tick_king), and while he's present it
                # only ever sits in [0.90, 1.0], far too narrow a band to
                # read as existence (it would just pin him near-real the
                # whole time he's on screen). The 0.15 floor keeps him a
                # faint watching void, never fully gone, until he nears.
                king_threat = max(0.15, min(1.0, 1.0 - (d - KING_THREAT_NEAR) / span))
            for ox, oy in _offsets:
                sx, sy = self.camera.project(npc.x + ox, npc.y + oy)
                if not _on_screen(sx, sy):
                    continue
                if m > 0.0:
                    draw_vessel_bloom(self.screen, sx, sy, npc.sprite_kind,
                                      npc.facing, m, seed=id(npc) & 0xffff)
                else:
                    # (No curse-priest -- the curse is His own gaze now;
                    # NARRATIVE 1b/3. curse_v stays 0 for all normal NPCs.)
                    curse_v = 0.0
                    # A Watcher being stared down: its eyes go dark (gaze) and
                    # it fades as the dispel timer fills, so the cure reads.
                    w_gaze = (npc.sprite_kind == "watcher"
                              and getattr(npc, "_gaze_dispel_t", 0.0) > 0.05)
                    draw_npc_sprite(self.screen, sx, sy, npc.sprite_kind,
                                    npc.facing, blink=(i == blink_idx),
                                    birth=getattr(npc, "_birth", None),
                                    gait=getattr(npc, "_gait", None),
                                    threat=king_threat, seed=id(npc) & 0xffff,
                                    curse=curse_v, gaze=w_gaze)
                    # A resister whose flesh has turned: their bespoke
                    # fold-horror form, laid over the person they were.
                    if getattr(npc, "_mutated", False):
                        draw_infested_overlay(self.screen, sx, sy,
                                              npc.sprite_kind)
            # THRESHOLD: NPC name labels removed. They were the
            # last RPG-tell on screen -- the player should learn
            # who an NPC is by interacting with them, not by
            # reading a tag floating over their head. Strangers
            # on the road read as STRANGERS until they speak.
        for e in self.scene.enemies:
            for ox, oy in _offsets:
                sx, sy = self.camera.project(e.x + ox, e.y + oy)
                if not _on_screen(sx, sy):
                    continue
                e.draw(self.screen, self.cam_x - ox, self.cam_y - oy)
        for p in self.scene.projectiles:
            p.draw(self.screen, self.cam_x, self.cam_y)
        if self.player:
            psx, psy = self.camera.project(self.player.x, self.player.y)
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
                                   prone=getattr(self.player, "prone", False))
            # The axe swing: a wood haft + steel head arcing through the
            # facing hemisphere, with a brief motion smear so the chop
            # reads. Progress walks 0->1 as melee_swing_t bleeds down.
            if self.player.melee_swing_t > 0:
                prog = 1.0 - (self.player.melee_swing_t / AXE_SWING_DUR)
                draw_axe_swing(self.screen, psx, psy,
                               self.player.melee_dir, prog)
        # Reset the per-frame full-screen darkness budget. Each
        # whole-screen black overlay below claims a slice via
        # _claim_dark() so the combined wash never exceeds
        # MAX_FULLSCREEN_DARK. The player's feet stay readable even
        # when hide + apex stack.
        self._overlay_dark_used = 0
        self._draw_brimley_haze()
        self._draw_dark()
        self._draw_outdoor_vignette()
        self._draw_apex_overlay()
        self._draw_hidden_overlay()
        # Film grade over the whole world layer (desaturate, cool tint,
        # vignette, animated grain) -- fuses the frame into one grimy
        # image. Applied before the HUD so UI text stays crisp.
        from scenes.base import apply_grade
        apply_grade(self.screen, pygame.time.get_ticks() / 1000.0)
        self._draw_interact_prompt()
        self._draw_hud()
        self._draw_notebook_toast()
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
        # Flashback overlay -- preempts everything for the duration of
        # the witnessing sequence.
        self._draw_flashback()
        # Ending overlay -- preempts everything during the ending
        # sequences.
        self._draw_ending()
        # Death screen -- the King's mask furnace or the cultist KILLED
        # card. Drawn over EVERYTHING (HUD, dialog) so the catch takes
        # the whole frame.
        if self._death_kind is not None:
            self._draw_death_screen()

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
        """Float an [E] over whatever pressing E would act on right now,
        mirroring try_interact's priority so the cue never lies: a
        hide-spot first (the core stealth affordance), then an adjacent
        axe-chop target, a chest, or an NPC to talk to. Drawn over the
        world, under the HUD."""
        if (self.dialog.active or self.inv_ui.open or self.notebook_ui.open
                or self.text_input.active
                or self.state != "playing"):
            return
        if self.player.hidden is not None:
            return
        px, py = self.player.x, self.player.y
        target = None
        # 1. Hide spot within reach -- the single most important cue in a
        # hide-or-die game: tell the player where cover is.
        for hx, hy, _k in (getattr(self.scene, "hide_spots", None) or []):
            if math.hypot(hx - px, hy - py) < 36:
                target = (hx, hy)
                break
        # 2. Axe-chop target on an adjacent tile (debris / boards).
        if target is None and self.player.inventory.has("lumber_axe"):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                tx = int((px + dx * TILE) // TILE)
                ty = int((py + dy * TILE) // TILE)
                if (0 <= ty < self.scene.h and 0 <= tx < self.scene.w
                        and self.scene.objects[ty][tx] in ("*", "q", "K")):
                    target = (tx * TILE + 16, ty * TILE + 16)
                    break
        # 3. A chest within reach -- but only if it's actually openable.
        # Decorative chests (e.g. the Sorting Hall's sealed cases) pass
        # interactive=False so they don't advertise a dead [E].
        if target is None:
            for d in self.scene.decorations:
                if (getattr(d, "kind", "") == "chest"
                        and d.kwargs.get("interactive", True)
                        and math.hypot(d.x - px, d.y - py) < 40):
                    target = (d.x, d.y - 8)
                    break
        # 4. An NPC to talk to.
        if target is None:
            for npc in self.scene.npcs:
                if getattr(npc, "no_prompt", False):
                    continue
                if math.hypot(npc.x - px, npc.y - py) < 40:
                    target = (npc.x, npc.y)
                    break
        # 5. A scene interactable (on_interact_fn readable/pickup -- the
        # case notebook, the cellar Ledger, the Mask altar). Last, to
        # mirror try_interact running on_interact_fn after NPCs.
        if target is None:
            for ix, iy, irad in getattr(self.scene, "interactables", ()):
                if math.hypot(ix - px, iy - py) < irad:
                    target = (ix, iy)
                    break
        if target is None:
            return
        sx = int(target[0] - self.cam_x)
        sy = int(target[1] - self.cam_y) - 40
        t = pygame.time.get_ticks() / 250.0
        yo = int(math.sin(t) * 2)
        txt = self.fonts["sm"].render("[E]", True, C_GOLD)
        self.screen.blit(txt, (sx - txt.get_width() // 2, sy + yo))

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
        # Ammo readout, lower-right -- only while carrying the pistol. Red
        # when empty. Dim, like the rest of the HUD.
        if self.player.inventory.has("pistol"):
            ammo = self.player.inventory.count("pistol_ammo")
            col = (200, 70, 60) if ammo <= 0 else (140, 136, 112)
            a = self.fonts["tiny"].render(f"rounds  {ammo}", True, col)
            self.screen.blit(a, (SCREEN_W - a.get_width() - 14,
                                 SCREEN_H - 22))
        # Flashlight state -- only surfaces in the dark, and only once you
        # carry a light. Warm amber when the beam's actually burning (so
        # the cost it's adding to the meter is legible), cold and dim when
        # off, and a dead grey in cult-dark where the beam won't catch.
        if (self.scene.key in DARK_SCENES
                and self.player.inventory.has("flashlight")):
            if self._flashlight_lit():
                lbl, col = "[F] light: on", (210, 180, 90)
            elif self.scene.key in CULT_DARK_SCENES:
                lbl, col = "[F] light: dead here", (70, 66, 78)
            else:
                lbl, col = "[F] light: off", (96, 92, 108)
            ls = self.fonts["tiny"].render(lbl, True, col)
            self.screen.blit(ls, (14, SCREEN_H - 36))
        # Threat meter -- thin bar upper-right. Tracks Pursuer
        # proximity (the threat fiction's spine). Stays dim and
        # quiet at low values; warms amber in the middle band; goes
        # bone-cold red and pulses at >= 0.95, where the Yellow King
        # avatar is loose. Player has no number, just a feel for
        # the line tightening.
        prox = max(0.0, min(1.0, self.visibility))
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
        # The evidence FLOOR is seared in -- a dead, locked base the meter can
        # never bleed below. The bright live fill rides ABOVE it, so the
        # reclaimable headroom you can still hide back into visibly shrinks the
        # more of the case you understand. (NARRATIVE §3, made legible.)
        floor = max(0.0, min(1.0, getattr(self, "_vis_floor", 0.0)))
        fw = int(bar_w * floor)
        pw = int(bar_w * prox)
        if fw > 0:                                   # locked, seared base
            pygame.draw.rect(self.screen, (66, 30, 28), (tx, ty, fw, bar_h))
        if pw > fw:                                  # live reclaimable headroom
            pygame.draw.rect(self.screen, col, (tx + fw, ty, pw - fw, bar_h))
        if fw > 0:                                   # the locked watermark
            pygame.draw.line(self.screen, (122, 52, 44),
                             (tx + fw, ty), (tx + fw, ty + bar_h - 1))
        # Stamina (sprint wind) -- lower-left, just above the scene
        # label. Hidden while full + idle so the minimalist HUD stays
        # quiet; it surfaces the instant you spend wind. Cool blue while
        # you still have breath, red + refilling while you're blown and
        # locked out -- so a chase becomes a gamble: sprint now and risk
        # being caught winded, or keep something in reserve to break for
        # cover.
        p = self.player
        winded = p.sprint_cd > 0
        if p.sprint_active or winded or p.sprint_t < p.sprint_t_max - 0.01:
            sw, sh = 70, 4
            sx2, sy2 = 14, SCREEN_H - 32
            if winded:
                ratio = 1.0 - max(0.0, min(1.0, p.sprint_cd / p.sprint_cd_max))
                fill = (150, 60, 60)
            else:
                ratio = max(0.0, min(1.0, p.sprint_t / p.sprint_t_max))
                fill = (110, 150, 170)
            pygame.draw.rect(self.screen, (40, 36, 50),
                             (sx2 - 1, sy2 - 1, sw + 2, sh + 2), 1)
            pygame.draw.rect(self.screen, fill,
                             (sx2, sy2, int(sw * ratio), sh))

    def _flash_notebook(self):
        """Fire the corner notebook-scribble toast -- a new evidence beat was
        just logged (the PI jotting it down)."""
        self._notebook_toast_t = NOTEBOOK_TOAST_DUR

    def _draw_notebook_toast(self):
        """A small page in the upper-left that the PI scribbles a beat onto,
        then it fades -- the diegetic 'added to the notebook' tell, fired by
        _flash_notebook when _evidence logs a new entry."""
        tt = getattr(self, "_notebook_toast_t", 0.0)
        if tt <= 0:
            return
        frac = max(0.0, min(1.0, (NOTEBOOK_TOAST_DUR - tt) / NOTEBOOK_TOAST_DUR))
        if frac < 0.15:
            a = frac / 0.15
        elif frac > 0.75:
            a = max(0.0, (1.0 - frac) / 0.25)
        else:
            a = 1.0
        if a <= 0.0:
            return
        W, H = 34, 42
        surf = pygame.Surface((W, H), pygame.SRCALPHA)

        def C(r, g, b, al=255):
            return (r, g, b, int(al * a))
        # Page + edge + a dog-eared top-right corner.
        pygame.draw.rect(surf, C(224, 218, 202), (2, 3, W - 6, H - 6))
        pygame.draw.rect(surf, C(150, 142, 120), (2, 3, W - 6, H - 6), 1)
        pygame.draw.polygon(surf, C(198, 190, 172),
                            [(W - 8, 3), (W - 8, 9), (W - 4, 3)])
        # Ink lines write on left-to-right over frac ~0.12..0.78.
        write = max(0.0, min(1.0, (frac - 0.12) / 0.66))
        lx0, lx1 = 6, W - 9
        head = None
        for i in range(4):
            lp = max(0.0, min(1.0, write * 4 - i))
            if lp <= 0:
                break
            ly = 12 + i * 7
            x_end = lx0 + int((lx1 - lx0) * lp)
            pts, x = [], lx0
            while x <= x_end:
                pts.append((x, ly + (1 if (x // 3) % 2 == 0 else 0)))
                x += 3
            if len(pts) >= 2:
                pygame.draw.lines(surf, C(38, 32, 42), False, pts, 1)
            head = (x_end, ly)
        # Pen nib at the writing head while it's still scribbling.
        if 0.12 < frac < 0.8 and head:
            px, py = head
            pygame.draw.polygon(surf, C(26, 24, 32),
                                [(px, py - 1), (px + 3, py - 6), (px + 4, py - 1)])
        self.screen.blit(surf, (14, 14))

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

    def draw_pause(self):
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        if self.pause_view == "controls":
            self._draw_controls_screen()
            return
        if self.pause_view == "settings":
            self._draw_settings_screen()
            return
        title = self.fonts["xl"].render("PAUSED", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 160))
        for i, opt in enumerate(self.pause_options):
            color = C_GOLD if i == self.pause_choice else C_WHITE
            label = f"> {opt}" if i == self.pause_choice else f"  {opt}"
            txt = self.fonts["lg"].render(label, True, color)
            self.screen.blit(txt, (SCREEN_W//2 - 90, 260 + i * 50))

    def _draw_controls_screen(self):
        title = self.fonts["xl"].render("CONTROLS", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 90))
        x_label = SCREEN_W//2 - 230
        x_key = SCREEN_W//2 + 20
        y0 = 180
        for i, (action, keys) in enumerate(self.CONTROLS_REFERENCE):
            y = y0 + i * 34
            a = self.fonts["md"].render(action, True, (200, 196, 210))
            k = self.fonts["md"].render(keys, True, C_GOLD)
            self.screen.blit(a, (x_label, y))
            self.screen.blit(k, (x_key, y))
        hint = self.fonts["sm"].render("Esc / Enter . back", True, (120, 116, 132))
        self.screen.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H - 60))

    def _draw_settings_screen(self):
        title = self.fonts["xl"].render("SETTINGS", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 130))
        rows = [
            ("Master volume", self.audio.master_vol),
            ("Music volume",  self.audio.music_vol),
            ("Sound volume",  self.audio.sfx_vol),
        ]
        x_label = SCREEN_W//2 - 200
        bar_x = SCREEN_W//2 + 10
        bar_w = 180
        for i, (name, val) in enumerate(rows):
            y = 240 + i * 56
            sel = (i == self.settings_choice)
            color = C_GOLD if sel else C_WHITE
            label = f"> {name}" if sel else f"  {name}"
            self.screen.blit(self.fonts["lg"].render(label, True, color),
                             (x_label, y))
            # Slider track + fill + percent.
            pygame.draw.rect(self.screen, (60, 56, 70),
                             (bar_x, y + 14, bar_w, 6), 1)
            pygame.draw.rect(self.screen, color,
                             (bar_x, y + 14, int(bar_w * val), 6))
            pct = self.fonts["sm"].render(f"{int(round(val * 100))}%", True, color)
            self.screen.blit(pct, (bar_x + bar_w + 12, y + 8))
        hint = self.fonts["sm"].render(
            "Up/Down . select    Left/Right . adjust    Esc . back",
            True, (120, 116, 132))
        self.screen.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H - 60))

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
