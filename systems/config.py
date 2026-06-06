"""Gameplay tuning + scene-gating sets for THRESHOLD.

Pure data extracted verbatim from systems/game.py (the orchestrator was a
5k-line file; this is the config/logic split, step 1). No imports, no
behavior -- just the constants the Game class and its mixins read. game.py
does `from systems.config import *`, so every bare-name reference there and
every external `from systems.game import <CONST>` keeps resolving unchanged.
"""

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
                  "arrival_road",
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
    "effigy_grove", "lodge_arrival", "highway_walk",
    "husk_grove", "scarecrow_ring",
}

# How far (px) the camera leads the player in their facing direction so
# they can see where a path/fold is taking them before they walk into it.
# ~3 tiles -- enough lead to read a bend or a wrap-seam, small enough that
# the player stays comfortably on screen.
CAM_LOOKAHEAD = 96

# Oblique-camera tilt (CAMERA.md Phase 2). The tilt is the DEFAULT view;
# F3 toggles back to the flat pitch-0 view (the legacy raster) and eases in.
# pitch 0 = that flat fallback. TILT_PITCH_DEG is the locked ~55deg default.
TILT_PITCH_DEG = 55
TILT_EASE = 0.12             # per-frame lerp of pitch toward its target
TILT_ZOOM = 0.72             # camera scale at full tilt (1.0 = top-down)
TILT_ACTOR_STAND = 15        # default px a sprite centre rises to stand
# Blind-spot fog: thin cold gray veiling the AREA outside the forward sight
# cone under tilt (the cone itself is punched clear). Low alpha so off-cone
# terrain stays dimly navigable -- the dread is "fogged", not "blind".
SIGHT_FOG_ALPHA = 96
# Taller sprites need their centre lifted further so their feet meet the
# floor (foot-offset in sprite px); falls back to TILT_ACTOR_STAND.
TILT_LIFT = {"yellow_king": 30, "sheriff_hollow": 22, "watcher": 20}
# The world projection is orthographic, so the King -- the apex -- gets a
# deliberate perspective-style depth scale under tilt: he LOOMS larger as he
# closes the view-depth gap toward the camera and shrinks as he hangs back, so a
# charge reads as bulk rushing the lens. Pure visual (catch is distance-gated).
KING_TILT_DEPTH_CAM = 360.0    # effective camera->player-plane distance (world px)
KING_TILT_DEPTH_MIN = 0.7      # scale-mul clamp (far / behind the player)
KING_TILT_DEPTH_MAX = 1.7      # scale-mul clamp (near / in front, looming)

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
               "the_sump", "the_cells", "the_ossuary",
               "dark", "threshold"}

# Cult-dark: a subset of DARK_SCENES where the flashlight is
# mechanically disabled and the dread aperture closes regardless
# of equipment. Reality is thinner here. Past the threshold of
# normal physics.
CULT_DARK_SCENES = {"depths_antechamber", "depths_procession",
                    "depths_hall", "depths_threshing",
                    "depths_stair", "the_ossuary",
                    "dark", "threshold"}

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

# Refuges a chase can never cross (NARRATIVE §8): the safe houses above, plus
# Mara's cell -- a deliberate underground refuge that hosts no cult, so a
# pursuer fled into it is shaken. (A chase is also shaken by a mundane interior
# door, but that's keyed on the EXIT type in _note_fold_pursuit, not the scene.)
FOLD_REFUGE_SCENES = SAFE_SCENES | {"maras_room"}

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
# claimed town under open sky (NARRATIVE.md 1b/3). The curse is His own
# attention. Safe rooms are exempt via KING_FREE_SCENES.
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

# ---- The roaming King (KING_PROMPT rework) -----------------------------
# The apex reworked from a per-scene spawn-at-vis-1.0 into ONE persistent,
# world-positioned entity: he sits IDLE at full bloom down the road until the
# 3-evidence gate, then roams the surface scene-to-scene SEARCHING, HUNTS on
# sight (visibility climbs fast), and de-escalates when you break his line of
# sight. Flag-gated so the legacy King (_tick_king) and the old tests' subject
# stay intact; flip False to fall back. Portals are a later milestone.
KING_ROAM = True
# The surface domain he may occupy: the continuous outdoor world + the seen
# fold groves. Never indoors, never a safe room, never the boss arena. He
# travels only the edges BETWEEN these (passages + folds); a door/ladder into
# an interior is the player's escape, never his.
KING_ROAM_SCENES = (SEAMLESS_WORLD_SCENES - {"void_boss"}) - SAFE_SCENES
KING_ROAM_START = "arrival_road"   # idle home: the looping road W of the Lodge
KING_HOP_INTERVAL = 6.0      # s between adjacent-scene hops while off-camera
KING_HOP_TOWARD = 0.55       # chance a search hop steps toward the player (lucky,
                             # not omniscient -- the rest is a random drift)
KING_SEARCH_TIME = 120.0     # s searching after losing you before he loosens to
                             # the "check one or two rooms away" wander
KING_SEE_RANGE = 360.0       # px; how far he can pick you out (LOS, unhidden)
KING_GAZE_RISE = 0.45        # /s visibility climb while he has eyes on you (fast)
KING_CATCH_DIST = 24.0       # px; contact range that ends the run (birth-gated)
KING_HUNT_DROP_VIS = 0.90    # visibility floor of the hunt; below it (or once you
                             # break his sight) hunting falls back to searching.
                             # The six evidence beats sum to exactly 0.90, so at
                             # FULL evidence the meter alone can't dip under it --
                             # breaking his line of sight (cover) is the relief
                             # that always works (knowing dooms you, NARRATIVE 3).
KING_ROAM_SPEED = 1.7        # in-room float speed (px*60/s via _yk_update)
KING_DREAD_ASH = 70          # extra ash motes when he is one room away (the tell)

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
    # the dead-end branch rooms hang off their parent corridors and share
    # its underground treatment (baseline rot + Enemy-cultist pursuit).
    "the_sump", "the_cells", "the_ossuary",
}

# Ashfall (NARRATIVE 4b): a slow drifting pale-yellow ashfall, the pressure
# of the vessel made visible -- His attention settling on you, not snow, not
# weather. Density scales with the infestation stage (light at 1 -> a steady
# yellow drift at 3) and thickens underground (nearer the source). Never on
# the Threshold (the eye of it is still, 1b), and safe rooms stay clear until
# stage 3 (mirrors the rot decals). Pure screen-space overlay, procedural.
ASHFALL_BY_STAGE = {0: 0, 1: 46, 2: 110, 3: 196}   # target motes by stage
ASHFALL_SOURCE_MUL = 1.7      # denser underground (nearer the source)
ASHFALL_MAX = 360             # hard ceiling on live motes
ASHFALL_COLOR = (210, 176, 86)    # jaundiced pale yellow
ASHFALL_FALL_MIN, ASHFALL_FALL_MAX = 11.0, 30.0    # px/s downward drift
ASHFALL_WIND = 7.0            # px/s steady sideways drift
ASHFALL_SWAY = 9.0            # px sway amplitude as a mote falls
ASHFALL_GROW = 70.0           # motes/s the field eases toward its target
