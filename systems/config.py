"""Gameplay tuning + scene-gating sets for THRESHOLD.

Pure data extracted verbatim from systems/game.py (the orchestrator was a
5k-line file; this is the config/logic split, step 1). No imports, no
behavior -- just the constants the Game class and its mixins read. game.py
does `from systems.config import *`, so every bare-name reference there and
every external `from systems.game import <CONST>` keeps resolving unchanged.
"""

# THRESHOLD: scene sets keyed to the cult fiction. The cult sites
# (cult_chamber, the burn clearing) bypass the standard fade --
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

# Camera follow rate: max world radians/sec the body heading chases the mouse
# aim in the tilted view (the camera rides behind body, so this is the speed at
# which the camera catches up to where the cursor is pointing). Mouse-driven
# steering replaced explicit A/D turn input; A/D now strafes.
TURN_RATE = 2.0

# Dead-zone (radians) within which the body ignores small mouse-aim deltas, so
# micro-jitter on the cursor doesn't shake the camera. ~17 degrees of arc near
# straight-up where the chase does NOTHING.
AIM_DEAD_ZONE = 0.30

# Outer bound of the chase cone (radians from straight-up). Beyond this the
# chase disengages — a few degrees of dead arc near the horizontal so the
# transition between chase and free-look isn't an edge. ~75 degrees from up.
CHASE_MAX_OFFSET = 1.30
# Aim-steady rules (2026-07): aiming must never be a standing order to
# swing the view. While the trigger is held (and for CHASE_FIRE_LOCK
# seconds after a shot) the body-chase is OFF entirely; standing still
# damps it to CHASE_STATIONARY_MULT of TURN_RATE; the full rate applies
# only while movement keys are actually driving.
CHASE_FIRE_LOCK = 0.40
CHASE_STATIONARY_MULT = 0.35

# Velocity smoothing time constant (seconds). Player velocity eases toward the
# input-driven target over this window, giving a tactile accel/decel feel.
MOVE_SMOOTH_TAU = 0.12

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
# sight. This is the only King: the per-scene spawn-at-vis-1.0 model is gone,
# and pinning visibility at 100% tears a portal he folds through.
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
KING_ROAM_SPEED = 1.7        # in-room float speed (px*60/s via _yk_update)
KING_DREAD_ASH = 70          # extra ash motes when he is one room away (the tell)

# The portal (KING_PROMPT M2): pin visibility at 100% for PORTAL_CHARGE_TIME and
# he tears a rift connecting your room to the room he stands in, then folds
# through to hunt. Break 100% before it forms and the rift collapses unformed
# (agency, not a death timer). It opens at a distance, never on top of you, and
# it is ALSO your escape: step through to the room he just left and strand him.
# It is one-way for HIM (he can't go back through), and shuts the moment you
# cross it or leave the scene. Never forms in a safe room / the boss arena, nor
# where he already stands. Same gold-on-black motif as the folds; NOT the
# Threshold doorframe (canon: the real door never screams).
PORTAL_PIN_VIS = 0.999       # visibility counts as "pinned at 100%" at/above this
PORTAL_CHARGE_TIME = 5.5     # s of pinned 100% before the tear (5-6s window)
PORTAL_CROSS_DIST = 26.0     # px; step into the rift to juke through it
PORTAL_EMERGE_GRACE = 0.8    # s after the tear before his body steps through

# The idle state (KING_PROMPT): before the 3-evidence gate the King stands at
# full bloom far up THE road (arrival_road), barely visible by distance,
# indifferent, unreachable. He is NOT a scene entity -- no collision, no
# interaction, no catch -- just a receding horizon render: he hangs a fixed gap
# NORTH of the player, so running up the treadmill road never closes on him
# (the road grows between you). Only drawn in arrival_road while not armed.
IDLE_KING_GAP = 23 * 32      # he hangs this many world px NORTH of the player
                             # every tick. arrival_road is a wrap_y treadmill, so
                             # the gap never closes however far you walk up -- a
                             # receding horizon you can never reach or touch. The
                             # larger the gap, the further up the road he sits, so
                             # he reads near the TOP EDGE / vanishing point rather
                             # than mid-screen.
IDLE_KING_SCALE = 56.0       # small + distant: a figure at the road's end near the
                             # top edge, not a big shape filling the upper screen
# Threat fed to the idle render. NOT a hunt state -- purely how much of the form
# resolves: maws only draw above 0.45 and eyes/gold-gloss/eversion strengthen
# with it, so keep it past the maw threshold so he reads as the King, not a
# dark lump. Stays under 0.8 (no player-reaching limbs -- he is indifferent).
IDLE_KING_THREAT = 0.6
# The idle King's BODY renders to a small card reused between refreshes
# (a full UNFOLDING every frame was the road's top cost). At 6 the
# eversion visibly STEPPED (~5 fps warping -- read as broken); at 2 it
# holds 15 fps, smooth for a slow distant churn, at ~2 ms/frame average
# (affordable after the tilt-renderer cache fixes). 1 = every frame.
IDLE_KING_CARD_REFRESH = 2
# The idle churn runs at half time: he is INDIFFERENT, not hunting --
# the mass turns over like weather, not like appetite. (The hunt King's
# eversion tempo is untouched.)
IDLE_KING_TEMPO = 0.5
# His unlight at idle, scaled down from the hunt disc: at the vanishing
# point the full disc read as a hard black hole pasted on the road.
IDLE_KING_EAT = 0.75

# ---- Being-seen readout (KING_PROMPT legibility milestone) -------------
# A second HUD layer that splits the RATE (how hard eyes are on you THIS second)
# from the visibility STATE (the accumulated meter that drives the gate/floor).
# It surfaces the per-frame human/cult gaze sum that already drives visibility
# (_tick_visibility), so eyes-on -> the bar fills and visibility climbs;
# being-seen 0 -> the drain opens and visibility creeps toward the floor. The
# King's OWN gaze is deliberately excluded (it's added straight to visibility in
# the roam tick), so the bar reads the solvable cult stealth puzzle precisely
# while the cosmic threat stays FELT (ashfall / the tone / the red apex wash),
# never a clean number. Notched so units map to gaze sources (a cultist, the
# torch each add a known amount).
BEING_SEEN_NOTCHES = 10       # discrete ticks on the bar
BEING_SEEN_FULL = 0.60        # gaze rate (/s) that lights all the notches

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

# ---- Stealth rework (STEALTH_REWORK.md): graded suspicion + cover classes -
# Detection is GRADED, not binary: each cultist carries a suspicion value in
# [0, 1] filled per tick by score = los * distance_falloff * facing_cone *
# concealment. Cover changes how HARD you are to detect, never WHETHER you
# can be. Two cover classes: CONCEALMENT (corn -- mobile, leaky: a distant
# cultist barely reads you, a near one still fills) and ENCLOSED ('under'/
# 'in' hide spots -- rooted, a hard sight break, but a SEARCHING cultist
# that reaches the hide CHECKS it -> the struggle). Apex pursuers
# (_force_chase: the King, the hollow Sheriff) bypass all of this.
SUS_NOTICE = 0.45             # alert threshold: turn toward you, the "?" tell
SUS_FILL_RATE = 2.6           # /s at score 1.0 -> point-blank open lock ~0.4s
SUS_DECAY = 0.55              # /s drain while the score is broken
SUS_SCORE_HOLD = 0.12         # min score that sustains an active CHASE
SUS_NEAR = 44.0               # px: inside this, facing no longer matters
SUS_CONE_HALF = 1.40          # rad (~80 deg) enemy sight-cone half-angle
SUS_CONE_FEATHER = 0.35       # rad soft edge on the cone lip
SUS_CONCEAL_CORN = 0.30       # concealment factor in corn (leaky, not zero)
# Darkness is CONCEALMENT too (STEALTH_REWORK Pillar 2A "corn, shadow"):
# in a DARK scene, with the flashlight unlit and outside every light
# pool (Scene.lit_at), the player reads as half-swallowed by the gloom.
# Weaker than corn (a shape in the dark is still a shape), and it never
# stacks with other cover (the better factor wins). Apex pursuers and
# respects_hide=False eyes ignore it like all cover.
SUS_CONCEAL_DARK = 0.45
# Leaving an enclosed hide takes a BEAT (the deferred exit-takes-a-beat
# window): you are out, visible, and unable to move while you unfold.
HIDE_EXIT_BEAT = 0.35
# Searchers sweep cover instead of milling: enclosed hides near the
# last-seen point get walked to and CHECKED (looked under / opened).
SUS_SWEEP_RADIUS = 170.0      # px around last-seen a searcher will sweep
SUS_CHECK_DIST = 22.0         # px: close enough to check a swept hide
SUS_CHECK_PAUSE = 0.7         # s spent looking into each swept spot
# The struggle: a searcher checks the enclosed hide you are in. A short
# mash window decides it -- win = burst out (sprint burst, the checker
# staggers, a LOUD noise event converges the room), lose = taken (the
# CAPTURED card). Tuned so a ready player usually escapes.
STRUGGLE_WINDOW = 1.6         # s to win the mash
STRUGGLE_PRESSES = 5          # E/SPACE presses needed
STRUGGLE_BURST_T = 0.9        # s of panic-burst speed after winning
STRUGGLE_BURST_MULT = 1.8     # burst speed multiplier
STRUGGLE_STUN = 1.4           # s the checker staggers after a burst-out

# ---- The noise core (2026-07 sound overhaul) ------------------------------
# World noises broadcast through Scene.emit_noise; the cult hears them
# through systems/stealth.hear_noise. SCOUTS turn on anything at or over
# NOISE_HEAR_MIN; SEARCHERS/INVESTIGATORS already own a target and are
# only PULLED OFF it by something louder (NOISE_SEARCH_PULL -- a gunshot,
# the struggle burst, the bell). Every reaction starts with the
# turn-first telegraph: face the source and hold NOISE_REACT_PAUSE before
# walking. Set-piece kneelers (lock_facing / aggro 0) are deaf on
# purpose: their wake is scripted. CHASE never diverts; apex never hears.
NOISE_HEAR_MIN = 0.7          # min loudness that turns a scout's head
NOISE_FRESH = 0.4             # s an event stays audible
NOISE_REACT_PAUSE = 0.45      # the face-the-sound beat before walking
NOISE_SEARCH_PULL = 0.9       # loudness that diverts a searcher
NOISE_WALK_SPEED = 55.0       # px/s travel estimate that sizes an
                              # investigator's walk budget by distance,
                              # so a far pull (the bell) isn't abandoned
                              # halfway across the field

# ---- The church bell (the town's one dominant noise source) ---------------
# Rung from the bell tower (E on the pull, scenes/threshold_extras.py).
# While it peals: every surface scene is MASKED (small noises, the
# player's steps, drown under it) and in Brimley it broadcasts a
# map-wide pull at the church door -- every cult hunter converges on the
# church. A hunter that reaches the door stills the rope; otherwise the
# peal rings itself out. Apex pursuers never hear it (they hunt YOU).
BELL_RING_DUR = 20.0          # s the peal lasts if nothing stops it
BELL_TOLL_PERIOD = 2.6        # s between strikes
BELL_MASK_LEVEL = 0.85        # emit_noise events quieter than this drown
BELL_MASK_RADIUS = 100000.0   # the peal covers the whole scene
BELL_REACH = 100000.0         # the pull is heard map-wide
BELL_STOP_DIST = 70.0         # a hunter this close to the door stills it

# ---- Placed noisemakers (Scene.add_noise_trap / add_noise_source) ---------
# Passive traps underfoot (cans, glass, a loose plank, a crow that
# flushes) fire on entry and re-arm after the player leaves; toggleable
# sources (the truck radio, the works valve) loop a lure until a cult
# hunter reaches them and shuts them off.
TRAP_REARM = 2.0              # s before a left-and-re-entered trap re-fires
NOISE_SRC_SILENCE_DIST = 40.0 # a hunter this close shuts a source off

# ---- One-hop noise bleed (the tunnels carry sound) -------------------------
# A LOUD noise in an underground room (a gunshot, the struggle burst)
# reaches the NEXT room: after a short walk-time a transient cultist
# comes through the nearest exit door (the leaf swings -- the tell),
# looks the noise over, and leaves the way he came. One live visitor at
# a time, a long cooldown between visits, never in safe rooms/refuges,
# and never into a room already crowded with cult.
BLEED_LOUD = 0.9              # min loudness that carries next door
BLEED_DELAY_LO = 3.0          # walk-time before he appears
BLEED_DELAY_HI = 6.0
BLEED_CD = 45.0               # s between visits
BLEED_CAP = 3                 # no visit if this many cult already here
BLEED_LINGER = 20.0           # hard cap on the look-around before leaving

# Visibility rates, per second. Watchers + cultist gaze push the meter
# up; hiding pulls it down. Enough Watchers out-pace even hiding --
# that is the spiral toward a King the player can no longer shake.
# (Rework: the gaze term is now WEIGHTED by concealment -- corn scales
# it by SUS_CONCEAL_CORN, an enclosed hide zeroes it; VIS_HIDE_BLEED
# drains only in an enclosed hide, corn gets the idle decay.)
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
# Garrick, and Old Pell each have a dedicated incident in rendering.sprites
# / ui.dialog; Old Pell's resolves by NAME, since he shares Garrick's
# old_townsman sprite kind). Values are the evidence stage at which they
# turn.
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
