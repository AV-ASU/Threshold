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
from rendering.sprites import (draw_player_sprite, draw_npc_sprite,
                               draw_npc_corpse, draw_infested_overlay,
                               draw_axe_swing, draw_king_death, draw_carcosa,
                               draw_mask_yank)
from rendering.transform import draw_vessel_bloom
from ui.fonts import make_fonts
from ui.dialog import DialogueBox
from ui.inventory_ui import InventoryUI
from ui.notebook_ui import NotebookUI
from ui.text_input import TextInputModal
from systems.audio import Audio
from systems.save import Save
from systems.items import Inventory, ITEM_DEFS
from entities.player import Player
from entities.enemy import Enemy, Projectile
from entities.npc import NPC
from entities.decoration import Decoration
from scenes import load_scene, tile_footstep, Scene

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
# (SAFE_SCENES) are the only refuge. The special curse-priest only
# haunts the deep cult sites -- venturing there is what risks the
# permanent curse.
CULTIST_SCENES = {
    "forest_path", "our_house_area", "graveyard",
    "brimley", "country_lane",
    "gravel_road_north", "river_crossing", "backwoods_cabin",
    "cornfield_maze",
}
CURSER_SCENES = {"brimley", "graveyard", "cornfield_maze"}

CURSE_RITUAL_TIME = 3.0        # seconds of held sight to land a curse
WATCHERS_PER_CURSE = 3         # Watcher cap added per curse level
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
WATCHER_FLOOR = 0.12           # each live Watcher raises the visibility floor
WATCHER_CLONE_INTERVAL = 7.0   # seconds of EXPOSURE between clones
WATCHER_GAZE_DISPEL = 2.0      # seconds holding one in your gaze to dissolve it
VIS_FLOOR_TOTAL_CAP = 0.92     # summed floor stays just under the King (1.0)
CULT_REGULARS = 2              # roaming cultists kept per cult scene
CULT_TOPUP_INTERVAL = 8.0      # seconds between cultist (re)spawns
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
# The opening drive -- a scripted, near-on-rails sequence (game state
# "opening"): the PI's car rolling into Brimley at night, hours from anyone
# in the northern dark, until the engine dies at the Arcadia Lodge. ESC skips
# it silently, with no on-screen tell.
OPENING_SCROLL_SPEED = 220.0  # px/sec the road scrolls -- the sense of speed
OPENING_ROLL_DUR = 2.6        # seconds rolling between stalls
OPENING_STALL_TIMEOUT = 4.5   # auto-restart if the player never taps (no softlock)
OPENING_DEAD_HOLD = 3.0       # the final dead beat before the hand-off
OPENING_STALLS = 2            # normal stalls; the one after is the fatal one

# rite_broken ending: the mask-yank act (the culpable beat), then a HARD CUT
# to the Carcosa blast.
RITE_YANK_DUR = 3.0
RITE_BLAST_DUR = 7.0

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


from systems.game_draw import GameDrawMixin


class Game(GameDrawMixin):
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
        # Set when the player reads Mara's journal through a third time.
        # _flashback_phase tracks which still is showing. None means no
        # flashback active. Each phase shows a single line of text on a
        # black overlay. The "witnessing" flashback: reading her descent
        # in her own words pulls you a step into it (NARRATIVE §4).
        self._flashback_phase = None
        self._flashback_t = 0.0
        self._flashback_stills = [
            ("You read it a third time, and the page won't let go of you.",
             2.6),
            ("For a moment you are her -- walking the rows, the corn "
             "closing behind you like water.", 3.2),
            ("Something far under the town turns over in its sleep, and "
             "calls you the rest of the way down.", 3.6),
        ]

        # ---- THRESHOLD: ending state ----
        # _ending_active is the name of the ending currently
        # playing (or None). _ending_phase / _ending_phase_t walk
        # through the ending's stills.
        self._ending_active = None
        self._ending_phase = 0
        self._ending_phase_t = 0.0

    # ---- TITLE ----

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
        # Stillness + heartbeat
        self.stillness_t = 0.0
        self._delayed_audio = []
        self._creepy_step_count = 0
        # Flashback / ending state
        self._flashback_phase = None
        self._flashback_t = 0.0
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
        from entities.decoration import Decoration
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
            # Re-instate any local the player killed here on a prior visit:
            # the builder re-spawns them live every load, so swap them for
            # persistent corpses.
            self._replay_dead_locals()
            # Re-derive the world's infestation for this scene from the
            # evidence count (rot decals, turned/mutated locals, the
            # stage-3 Sheriff encounter).
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
                   or getattr(npc, "sprite_kind", None)
                   in ("cultist", "curse_priest"))
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
        # the body, a hard visibility spike, and a body that stays down.
        self.visibility = min(LOCAL_KILL_VIS_CAP,
                              max(self.visibility,
                                  self.visibility + LOCAL_KILL_VIS_SPIKE))
        if self.scene is not None:
            self.scene._last_step_event = (
                npc.x, npc.y, 1.0, pygame.time.get_ticks() / 1000.0)
        self._record_corpse(npc)
        return True

    def _corpse_id(self, npc):
        """Stable per-scene identity for a downed local. Tag if it has
        one, else the display name -- both are unique within a scene."""
        return getattr(npc, "tag", None) or getattr(npc, "name", "?")

    def _make_corpse(self, npc):
        """Convert a just-killed local NPC into a persistent corpse: it
        stops moving (alive=False already), stops blocking, and answers
        E with a one-shot examine instead of its old dialogue."""
        npc._is_corpse = True
        npc._kill_processed = True
        npc.solid = False
        npc.movement = "idle"
        npc.dialogue_fn = _corpse_examine
        npc.no_prompt = False

    def _record_corpse(self, npc):
        """Persist a local's death so the body is still there on re-entry.
        Keyed by scene -> list of {id, x, y, kind, name}."""
        dead = self.save.arg("dead_locals", {})
        key = self.scene.key
        recs = dead.get(key, [])
        cid = self._corpse_id(npc)
        if any(r.get("id") == cid for r in recs):
            return
        recs.append({"id": cid, "x": npc.x, "y": npc.y,
                     "kind": npc.sprite_kind, "name": npc.name})
        dead[key] = recs
        self.save.set_arg("dead_locals", dead)

    def _replay_dead_locals(self):
        """On scene load, re-instate any local the player killed here on a
        previous visit. Removes the live (re-spawned) version and drops a
        corpse in its place so the body persists across re-entries."""
        dead = self.save.arg("dead_locals", {})
        recs = dead.get(self.scene.key, [])
        if not recs:
            return
        ids = {r["id"] for r in recs}
        self.scene.npcs = [n for n in self.scene.npcs
                           if self._corpse_id(n) not in ids]
        from entities.npc import NPC
        for r in recs:
            body = NPC(r["x"], r["y"], r.get("name", "A body"), r["kind"],
                       movement="idle", solid=False,
                       dialogue_fn=_corpse_examine, tag="corpse")
            body.alive = False
            body._is_corpse = True
            body._kill_processed = True
            self.scene.add_npc(body)

    # ---- Infestation -------------------------------------------------
    def _infest_stage(self):
        """Surface infestation stage 0..3, front-loaded to peak as the
        player commits underground at 3 evidence. Monotonic with the
        evidence count (knowing rots the world, and you can't un-know)."""
        return min(3, self._evidence_count())

    def _apply_infestation(self):
        """Re-derive the world's rot for the freshly-loaded scene from the
        evidence count. Scenes rebuild every load, so this is deterministic
        and additive each time -- never accumulates. Runs after on_enter +
        _replay_dead_locals so it can transform the live locals in place."""
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
        from entities.decoration import Decoration
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
        from entities.npc import NPC
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
            if tag == "cult_curser":
                self._tick_ritual(n, dt, sees)
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

    def _tick_ritual(self, npc, dt, sees):
        """The curse-priest's ritual. While it holds the player in
        sight the timer climbs; cross CURSE_RITUAL_TIME and a permanent
        curse lands. Breaking sight -- cover, a corner, distance --
        bleeds the timer back down. The only way out is to not be seen."""
        cd = getattr(npc, "_curse_cd", 0.0)
        if cd > 0:
            # Respite after a curse: it can't re-bind for a beat.
            npc._curse_cd = max(0.0, cd - dt)
            npc._ritual_t = 0.0
            return
        t = getattr(npc, "_ritual_t", 0.0)
        if sees:
            if t == 0.0:
                self.audio.play("low_pulse", 0.6)
                self.show_notice("It fixes you with its gaze. Break its "
                                 "sight.", duration=3.0)
            t += dt
            if t >= CURSE_RITUAL_TIME:
                self._apply_curse()
                t = 0.0
                npc._curse_cd = CURSE_RITUAL_TIME
        else:
            t = max(0.0, t - dt * 1.5)
        npc._ritual_t = t

    def _ensure_cultists(self, key, dt):
        """Keep the current cult scene topped up: CULT_REGULARS roaming
        cultists, plus the curse-priest in the deep cult sites. Rate-
        limited so killing one buys a breather, not an instant respawn."""
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
        if key in CURSER_SCENES:
            curser = [n for n in self.scene.npcs
                      if getattr(n, "tag", "") == "cult_curser"
                      and getattr(n, "alive", True)]
            if not curser:
                self._spawn_cultist("cult_curser", "curse_priest",
                                     speed=0.6, gaze_range=210,
                                     movement="stalker", name="The Preacher")

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

    def _spawn_cultist(self, tag, kind, speed=0.85, gaze_range=180,
                       movement="chaser", name="", at=None):
        """Plant a cultist. If `at` (x, y) is given and walkable, they enter
        there (the door you came in by -- for reinforcement waves); otherwise
        at the farthest walkable scene corner from the player, so they enter
        from the edges rather than on top of you. Returns the NPC, or None."""
        from entities.npc import NPC
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
        n._ritual_t = 0.0
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
        from entities.npc import NPC
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
        from entities.npc import NPC
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
                self._tick_sheriff(dt)
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
        # village green rather than their bed. The world_emptied flag
        # is checked in load_scene_now so every scene from now on has
        # its npc list zeroed -- the layouts persist, the people don't.
        if self.scene and self.scene.key == "void_boss":
            self.save.set_flag("void_path_closed", True)
            self.save.set_flag("world_emptied", True)
            self.player.hp = self.player.max_hp
            self.show_notice("You wake on the village green. It is silent.")
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

    def _item_color(self, key):
        d = ITEM_DEFS.get(key, {})
        return {
            "weapon": (200, 200, 220),
            "armor":  (140, 110, 80),
            "consumable": (220, 80, 80),
            "key": (220, 200, 80),
            "lore": (180, 180, 220),
        }.get(d.get("kind"), (220, 220, 220))



    def _flash_notebook(self):
        """Fire the corner notebook-scribble toast -- a new evidence beat was
        just logged (the PI jotting it down)."""
        self._notebook_toast_t = NOTEBOOK_TOAST_DUR



    def show_notice(self, text, duration=2.5):
        self.notice_text = text
        self.notice_t = duration


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
