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
VOID_SCENES = {"clearing"}


# Scenes where dread-state effects engage: the stillness heartbeat
# ramps up while the player stands still here, and the cult-site
# floors get the rare delayed-footstep trick.
CREEPY_SCENES = {"lodge_cellar", "clearing",
                 "abandoned_farmhouse", "well_bottom", "well_passage",
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
    ("brimley", "mid"):       [(12, 10, "bloody_handprint")],
    ("brimley", "high"):      [(12, 10, "bloody_handprint"),
                                (19, 10, "dead_crow"),
                                (10, 23, "claw_marks")],
    ("lodge_yard", "mid"):  [(5, 11, "claw_marks")],
    ("lodge_yard", "high"): [(5, 11, "claw_marks"),
                                  (15, 6, "phantom_mark"),
                                  (8, 13, "dead_crow")],
    ("cornfield_path", "mid"):   [(6, 8, "dead_crow")],
    ("cornfield_path", "high"):  [(6, 8, "dead_crow"),
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
OUTDOOR_SCENES = {"lodge_yard", "cornfield_path",
                  "clearing", "graveyard",
                  "country_lane", "cornfield_maze",
                  "arrival_road",
                  "gravel_road_north",
                  "backwoods_cabin"}

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
    # The rite-hidden grove -- reached only through the school rite's
    # pane; the crossing shouldn't feel a transition.
    "effigy_grove",
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

# Walk-cycle cadence (rad/s of walk_phase) at the BASE walking speed
# (Player.speed). The phase advance is scaled by the actual ground speed
# (hypot(vel) / base speed), so the legs never skate: a slow wade trudges, a
# sprint pumps, and at base speed the leg cycle syncs to the footstep cadence
# (one step = pi rad; 10 rad/s ~= the 0.32s step timer). Before this the phase
# advanced at a fixed rate, so halving the base speed (130 -> 64) left the legs
# cycling twice as fast as the ground covered.
WALK_ANIM_RATE = 10.0

# NPC talk reach (px, player centre to npc centre). Per-NPC override via
# npc.talk_reach: a counter seat (Sable's desk, Hettie's till) needs a
# longer arm than the default or the furniture between you outranges the
# talk and E falls through to the prop behind them.
NPC_TALK_REACH = 40

# Conversation-menu input guard (s): the E that skims a talk's last
# caption opens the question menu in the SAME press chain, so a held or
# spammed E used to pick an option the player never read. Confirms are
# swallowed for this long after a menu opens (arrows still move).
CONVO_MENU_GUARD = 0.30

# The save toast (s): a small floppy-disk glyph beside the notebook
# scribble whenever evidence pickup writes the disk slot (the clue IS the
# checkpoint; the icon is the one reliable "that just saved" tell).
SAVE_TOAST_DUR = 2.2

# Oblique-camera tilt (DESIGN.md §10). The tilt is the ONLY camera; the
# pitch is locked to TILT_PITCH_DEG for the life of the Game. No flat view.
TILT_PITCH_DEG = 55
TILT_ZOOM = 1.10             # camera scale at full tilt (1.0 = sprite-native)
# 2026-07 scale pass: 0.72 zoomed the WORLD out while sprites stayed
# fixed-size, so rooms/doors/buildings read cramped against the bodies (the
# maintainer's "world feels too small compared to the player"). 1.10 restores
# sprite-native proportions and tightens the visible window (less info on
# screen = more dread); the sight cone (360 world px) still fits the frame.
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

# ---- The gape-lunge (2026-07 King rework) ---------------------------------
# Near live prey the mass GATHERS (crawling, its leading face irising
# open around the Pallid Mask in its throat -- the tell, and the same
# image the catch cutscene takes you down), then SURGES. The telegraph
# slow-down is the counterplay window: read the mouth, break sideways.
KING_LUNGE_RANGE = 250.0     # px to the live player that arms a lunge
KING_LUNGE_TELE = 0.45       # s of gather: mouth irises open, speed drops
KING_LUNGE_DUR = 0.5         # s of surge, mouth wide
KING_LUNGE_MULT = 1.75       # surge speed multiplier
KING_LUNGE_GATHER = 0.30     # crawl multiplier during the telegraph
KING_LUNGE_CD_LO = 3.5       # s between lunges (randomised)
KING_LUNGE_CD_HI = 6.0

# ---- the Moths (2026-07): the King's heralds, the first flying entity.
# ONE source (the 2026-07-03 clarity rework): from MOTH_SHED_EV evidence
# on, every MOTH_SHED_EVERY seconds the King sheds MOTH_SHED_COUNT moths
# into whatever room HE currently occupies (the roam sim's scene). They
# PERSIST and STACK per room (game._moth_field, capped at
# MOTH_STACK_CAP): a room he lingers in fills with them, and the field
# only thins when the player SPENDS one (a pop, or a flare burning out
# into its husk). A player inside MOTH_RADIUS starts the KINDLE window
# (the counterplay: back out past the radius, or kill it -- the axe up
# close, a round from range); the window expiring is the FLARE: a
# MOTH_REACH noise every cult ear converges on, a visibility spike, the
# dark broken around it, then the husk falls and that moth is spent.
MOTH_SHED_EV = 3             # evidence gate: HIS-room shedding starts once
                             # he walks (the roam arms at the same gate)
MOTH_SHED_EVERY = 90.0       # seconds between sheds (his current room)
MOTH_SHED_COUNT = 2          # moths per shed
MOTH_STACK_CAP = 10          # per-room ceiling (fairness + draw cost)
# His attention finds YOU before his body does (the evidence-2 beat):
# from 2 evidence a single moth materialises in the PLAYER'S room every
# few minutes (never at a door), joining that room's field; once he
# walks at 3 the seeker eases to a slow drip on top of his own shedding.
MOTH_SEEK2_LO = 120.0        # ev2 seeker interval (s), rolled per spawn
MOTH_SEEK2_HI = 180.0
MOTH_SEEK3_LO = 300.0        # ev3+ seeker interval (s)
MOTH_SEEK3_HI = 360.0
MOTH_SPEED = 26.0            # drift speed px/s
MOTH_SEEK_BIAS = 0.35        # chance a fresh waypoint aims near the player
MOTH_RADIUS = 96.0           # trigger radius around the player
MOTH_KINDLE = 0.8            # seconds of kindle before the flare
MOTH_FLARE_DUR = 2.0         # seconds the flare burns before it falls
MOTH_FALL_DUR = 0.6          # seconds the burnt-out husk takes to drop
MOTH_FAST_MULT = 3.0         # the King's shed moths fly this much faster
MOTH_REACH = 620.0           # cult hearing reach of the flare noise
MOTH_VIS_SPIKE = 0.10        # visibility jump on flare (capped under the King)
MOTH_LIGHT_R = 110.0         # kindle/flare light pool (breaks dark cover)
# MOTH_SCENES (where they fly) is defined next to KING_ROAM_SCENES
# below: the moths' ground IS the King's ground, so his shedding can
# fill any room he can walk.

# Dark scenes -- underground / interior cult sites where the
# flashlight matters. Without the flashlight the screen is heavily
# dimmed with a small clear circle around the player. With it,
# the dimness lifts to a wider cone in the facing direction.
# Dim ground-floor INTERIORS (2026-07 interior lighting pass): DARK scenes,
# but a LIGHTER gloom than the deep -- they read "dim, lit by the genset's
# bulbs + window spill, dark in the corners," not a pitch-black cellar. The
# flashlight works (not cult-dark). This is the ground "no light = danger"
# will stand on (TODO #21); the refuge (SAFE_SCENES) is deliberately excluded.
DIM_INTERIOR_SCENES = {"shop", "church", "barn", "schoolhouse",
                       "sheriff_office"}

DARK_SCENES = {"lodge_cellar", "well_passage", "well_bottom",
               "works_cistern", "works_sorting", "maras_room",
               "works_scriptorium",
               "works_sign", "works_deepface",
               "abandoned_farmhouse",
               "depths_antechamber", "depths_procession",
               "depths_hall", "depths_threshing", "depths_stair",
               "the_sump", "the_cells", "the_old_stores",
               "dark", "threshold"} | DIM_INTERIOR_SCENES

# Cult-dark: a subset of DARK_SCENES where the flashlight is
# mechanically disabled and the dread aperture closes regardless
# of equipment. Reality is thinner here. Past the threshold of
# normal physics.
CULT_DARK_SCENES = {"depths_antechamber", "depths_procession",
                    "depths_hall", "depths_threshing",
                    "depths_stair", "the_old_stores",
                    "dark", "threshold"}

# Scenes where the reactive cult-ambient layer (proximity-driven
# cult_breath + cult_chant) runs. These are the rite spaces -- the
# Works rooms and the Depths corridors. The fire-and-forget per-scene
# _ambient hooks are scene colour; this layer is a SECOND layer that
# swells with cultist proximity and pans from the closest cultist.
CULT_AMBIENT_SCENES = {"works_cistern", "works_sorting", "works_scriptorium",
                       "works_sign", "works_deepface",
                       "depths_antechamber", "depths_procession",
                       "depths_hall", "depths_threshing", "depths_stair"}

# Safe interiors. Heavy overlays short-circuit here so the room
# reads cleanly. The Inn (bedroom + house) is the refuge that the
# rest of the world is pressing against -- standing inside should
# feel SAFE compared to outside. Hide vignette also suppressed
# (you are already safe; the cramped read is wrong here).
SAFE_SCENES = {"bedroom", "lodge", "lodge_hall", "guest_room_a",
               "guest_room_b", "clerk_room", "toby_house"}

# Refuges a chase can never cross (DESIGN.md §4): the safe houses above, plus
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
KING_FREE_SCENES = SAFE_SCENES | {"dark", "threshold", "maras_room"}

# Dim-but-clear interiors. The flashlight cone still draws -- the
# cellar wants the light -- but dread / apex / dip overlays are
# suppressed so the navigation read stays usable. Hide vignette
# still runs (cover here is meaningful).
DIM_SAFE_SCENES = {"lodge_cellar"}

# ---- THRESHOLD: cult geography + threat tuning ----
# Regular cultists roam every outdoor scene; the safe lodge interiors
# (SAFE_SCENES) are the only refuge.
# The cult WAKES at this evidence count (2026-07 ladder): below it the
# surface spawns no patrol at all -- the town is only wrong, not yet
# hostile. Your first find is what makes the hooded ones appear.
CULT_WAKE_EV = 1

CULTIST_SCENES = {
    "cornfield_path", "lodge_yard", "graveyard",
    "brimley", "country_lane",
    "gravel_road_north", "backwoods_cabin",
    "cornfield_maze",
}
# (The old GAZE_BIND high-visibility trigger was retired in the play-notes
# Watcher rework: Watchers now open on EXPOSURE from WATCHER_WAKE_EV evidence,
# not on a visibility threshold. See the WATCHER_* block below and
# systems/threat_mixin._tick_watchers.)

# King "existence" range: it's a dark void at/beyond _FAR px from the player and
# fully manifests (blazing) by _NEAR px -- tune to slide the materialize window.
KING_THREAT_NEAR = 48.0        # px: fully real / blazing inside this
KING_THREAT_FAR = 340.0        # px: a dark void at/beyond this
# The WATCHERS -- His gaze made manifest, and THE below-3 threat (play-notes
# rework). From WATCHER_WAKE_EV evidence, while the player is EXPOSED (in the
# open, not in cover / a safe room), the domain opens Watchers on a timer:
# WATCHER_GRACE seconds before the FIRST of a fresh wave (and after clearing
# one), then the evidence-scaled interval between the rest. Each live Watcher
# HOLDS you while you are exposed and drives visibility UP by WATCHER_GAZE per
# second (the active CLIMB -- the main visibility driver below the cult), on
# top of a small residual WATCHER_FLOOR: ignore them and it SNOWBALLS. Clear
# them all -- stare each down for WATCHER_GAZE_DISPEL s, or the axe / a round --
# and the domain looks elsewhere for the grace. Cover pauses the timer and
# drops the hold; safe rooms (KING_FREE_SCENES) suppress them entirely; and
# the gaze only OPENS under the open sky or in the deep (WATCHER_OPEN_SCENES,
# defined after UNDERGROUND_SCENES below): no Watcher ever manifests inside a
# surface building.
WATCHER_WAKE_EV = 1            # evidence at which the domain starts watching
WATCHER_MAX = 5               # the field caps here (survivable, just under King)
WATCHER_GRACE = 6.0           # s of exposure before the first Watcher of a wave
WATCHER_SPAWN_BASE = 7.0      # s between spawns at WATCHER_WAKE_EV ...
WATCHER_SPAWN_STEP = 1.0      # ... shaved per further evidence (He floods them
WATCHER_SPAWN_MIN = 3.0       #     deep) down to this floor
WATCHER_GAZE = 0.05           # visibility CLIMB per live Watcher per second
                              # while exposed -- the teeth of the mechanic
WATCHER_FLOOR = 0.07          # residual visibility floor per live Watcher
WATCHER_GAZE_DISPEL = 2.0     # seconds holding one in your gaze to dissolve it
WATCHER_LIGHT_BURN = 2.0      # "no light = danger" (TODO #21): a Watcher caught
                              # in a light pool / the flashlight beam dissolves
                              # this-much faster (on top of any gaze) -- light is
                              # how you clear them in a dark interior
# Walking through a rift FOLD has this chance to open an extra Watcher on the
# far side (His gaze reaching across the wrongness). Never past WATCHER_MAX.
FOLD_WATCHER_CHANCE = 0.05     # 1 in 20 per fold traversal
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
KING_ROAM_SCENES = (SEAMLESS_WORLD_SCENES - {"clearing"}) - SAFE_SCENES
# The Moths fly exactly the King's ground (they are his heralds): every
# room he can enter is a room his shed pair can attend.
MOTH_SCENES = set(KING_ROAM_SCENES)
KING_ROAM_START = "arrival_road"   # idle home: the looping road W of the Lodge
KING_HOP_INTERVAL = 6.0      # s between adjacent-scene hops while off-camera
KING_HOP_TOWARD = 0.55       # chance a search hop steps toward the player (lucky,
                             # not omniscient -- the rest is a random drift)
KING_SEARCH_TIME = 120.0     # s searching after losing you before he loosens to
                             # the "check one or two rooms away" wander
KING_SEE_RANGE = 360.0       # px; how far he can pick you out (LOS, unhidden)
KING_GAZE_RISE = 0.45        # /s visibility climb while he has eyes on you (fast)
KING_CATCH_DIST = 24.0       # px; contact range that ends the run (birth-gated)
KING_ROAM_SPEED = 1.95       # in-room float speed (px*60/s via _yk_update);
                             # ~117 px/s, just above the player's ~105 px/s
                             # sprint so a locked King always closes the gap
                             # (play-notes rebalance)
# Player sprint = PLAYER_SPRINT_MULT x the base walk (entities/player.py
# speed). With the walk doubled (play-notes), sprint is a modest gear-up
# that still lands ~0.9x the King above: you can never outrun the apex,
# only hide (TODO #5 is the human tuning loop; raising this needs the King
# raised too, or you outrun him).
PLAYER_SPRINT_MULT = 1.25
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

# ---- Stealth rework (DESIGN.md §12): graded suspicion + cover classes -
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
# Darkness is CONCEALMENT too (DESIGN.md §12 "corn, shadow"):
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
# Two-touch cult grab (play-notes): the cult CAPTURES, it does not kill, so a
# first grab is a shove, not the end. The FIRST grab of an encounter tears the
# PI free (grabbers stagger STRUGGLE_STUN, he bursts on STRUGGLE_BURST_T) with
# CULT_SHRUG_INVULN s of grace; a SECOND grab before he reaches a SAFE_SCENE is
# the capture. The touch count resets only on reaching a safe zone (no decay),
# so a swarm still buries you and getting cornered still ends the run. The
# one-time Talk (cult_talk_given) is still the very first contact of a run.
CULT_SHRUG_INVULN = 0.7       # s of grace after tearing free (no re-grab)
CULT_SHRUG_RANGE = 44.0       # px: grabbers within this stagger on the shove
# The stealth economy (TODO #5, tuned from the 2026-07 human playtest:
# "running around the cultist beats hiding"). Three levers, re-derived
# against the canonical speed ladder (King > player sprint 105 > chase >
# player walk 84 > scout 57): a LOCKED cultist shifts into a chase gear
# (85.5 px/s for the surface regular, 72-90 underground -- WALKING away
# no longer works; sprint still escapes, but sprint drains and winds); the
# cult's arm's reach widens so brushing past an awake cultist risks the
# grab (all Talk/two-touch gates unchanged); and sprinting inside a
# cultist's line of sight is CONSPICUOUS (the detection score
# multiplies), so running is the loud, seen, stamina-priced option and
# cover is the cheap one.
CULT_CHASE_MULT = 1.5         # locked-chase speed gear over base speed
CULT_GRAB_REACH = 30.0        # px: contact-grab reach (was a bare 22)
SUS_SPRINT_MULT = 1.6         # detection-score multiplier while sprinting
# River stones (TODO #5, the distraction verb): a thrown stone is a
# placed noise event, nothing more -- it rides the existing ear
# (stealth.hear_noise) untouched. Loudness sits between the scout
# threshold (0.7) and the searcher pull (0.9) ON PURPOSE: a stone turns
# an idle head but never breaks a sighting-born search, so it is a tool
# for routing patrols, not for shaking a hunt.
STONE_LOUD = 0.8              # lands between hear-min and search-pull
STONE_REACH = 210.0           # px: how far the clatter carries
STONE_RANGE = 170.0           # px: throw distance along the aim
STONE_SPEED = 300.0           # px/s flight speed
# A stone THROUGH A WINDOW is the loud tier: glass is the one thrown
# sound that sits over the searcher pull (a window breaks once, so the
# bigger lever has a scarcity price), and the pane stays broken for the
# RUN (the broken_windows save ledger, laid back down on every load).
GLASS_LOUD = 0.95             # over NOISE_SEARCH_PULL: glass diverts a search
GLASS_REACH = 300.0           # px: a smashed pane carries
# A stone dropped down the DEAD WELL: the knocks fall away, the shaft's
# rattle carries across the square, and no bottom ever sounds (the well
# stays the bottomless dread it is -- this buys a wide lure, not a fact).
WELL_ECHO_LOUD = 0.85         # scout-tier: routes the square, breaks no hunt
WELL_ECHO_REACH = 340.0       # px: the rattle carries across the square
# Cult liveness (TODO #23a, the behavior pilot): dressing on the SCOUT
# state only -- neither beat ever touches notice/chase/search/investigate,
# and detection keeps scoring straight through both (threat unchanged).
CULT_SYNC_PERIOD = 21.0       # s between synchrony beats: every idle cult
                              # scout in the room pauses mid-stride at the
                              # same instant (one shared clock), one breath
CULT_SYNC_HOLD = 0.8          # s the shared all-stop holds
CULT_HANDOFF_RANGE = 30.0     # px: two crossing scouts stop and face
CULT_HANDOFF_HOLD = 1.2       # s the silent meeting holds before they part
CULT_HANDOFF_CD = 40.0        # s per actor before another meeting

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

# ---- Deep-water WADE (the flooded deep is loud) ---------------------------
# The dig broke into the underground river, so the deepest works stand in
# black water. Wading a `~` tile in a WADE scene HALVES the player's speed
# (you cannot sprint clear of it) and throws a loud SPLASH the searchers
# converge on -- turning standing water from set-dressing into a routing
# risk (skirt it on dry stone, or take the wet shortcut and pay in noise;
# it doubles as a deliberate lure to pull a searcher one way and slip past
# on the dry). Scoped to the deep works so the Brimley river -- its own
# set-piece, with its own in/out rules -- is untouched. No new AI: the
# splash rides the existing Scene.emit_noise / stealth.hear_noise ear.
WADE_SCENES = {"the_sump", "works_cistern", "depths_threshing"}
WADE_SPEED_MULT = 0.5         # wading halves speed (sprint can't clear it)
WADE_STEP_EVERY = 0.46        # heavier, slower splash cadence than dry steps
WADE_SPLASH_LOUD = 0.95       # a splash is LOUD -- over NOISE_SEARCH_PULL
WADE_SPLASH_REACH = 260.0     # and carries further than an ordinary footfall

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
# Capped just under "unshakeable" so only the last beats pin him. (DESIGN.md §1.)
VIS_FLOOR_CAP = 0.9
EVIDENCE_FLOOR_DEFAULT = 0.10  # per-evidence floor weight if none recorded
# Investigating arms the apex. Below this many evidence, a maxed meter musters a
# cultist reinforcement wave at your entry instead of the King -- the net
# tightening, not yet lethal. At/above it, the same trigger brings the King.
KING_GATE_EVIDENCE = 3
# The King-arrival RAMP (play-notes). Crossing the gate shouldn't be an
# ambush: at KING_GATE_EVIDENCE the roam arms but the world HOLDS ITS BREATH
# for KING_ARM_GRACE seconds first -- he stands far and does not close, the
# window to reach the lodge for the Invitation before the hunt begins. One
# tier earlier (KING_TURNS_HEAD_EV) a single telegraph note lands: he has
# turned his head toward you, but has not moved yet.
KING_TURNS_HEAD_EV = 2        # evidence at which the "he turns his head" beat fires
KING_ARM_GRACE = 25.0         # s the world holds its breath before the hunt begins
REINFORCE_COUNT = 2            # cultists per wave
REINFORCE_COOLDOWN = 8.0      # seconds between waves (pulses, never floods)
# The notebook-scribble toast: the corner card the PI scribbles a beat onto
# when ANYTHING is written to the case book (a clue or a note). Diegetic "you
# wrote it down" feedback -- and now the ONLY per-write feedback, since the
# world no longer narrates a conclusion at the player on every pickup. It
# names the beat it recorded, so the player knows to go read it. Long enough
# to actually read the title.
NOTEBOOK_TOAST_DUR = 2.8


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

# ---- World rot (NARRATIVE §world rot) -----------------------------
# As the case is understood the surface rots (the DECALS + the ambient air,
# systems/rot_mixin), front-loaded to peak as the player commits underground
# at 3 evidence. The stage is min(3, evidence) for the surface (monotonic;
# the underground deepens past that on its own evidence clock).
#
# The TOWNSFOLK do NOT change (TODO #22c, NARRATIVE §2): the
# old ROT_CONVERT / ROT_TURN tables (peace-makers repainted cultist,
# resisters' dialogue curdled) were CUT. The world rot is the PI's now, and
# it lives in the four-tier conversation framing (scenes/dialogue._pi_framing
# / _pi_tier). Sheriff Vane's fall stays PLAYER-DRIVEN (the VANE_* ledger
# below, DESIGN.md §2).

# ---- Sheriff Vane's despair/hope ledger (DESIGN.md §2; was TODO #2a) --
# A hidden balance decides the last holdout's fate; the player never sees
# a number, only his mood (the conversation's framing line + the beats).
# HOPE is earned one way: the PI SHARING a real discovery with him
# (scenes/dialogue._vane_share) -- the same act that buys his trust and
# opens his investigation thread. DESPAIR comes from the beats that read,
# to a man who wants it all to end, as permission: the preacher's murder
# (+VANE_DESPAIR_ACT) and the newspaper's front page (+VANE_PAPER_DESPAIR,
# the break lever, TODO #2). Net despair >= VANE_HOLLOW_AT latches
# `vane_hollow` for good (once hollow, no return); his office then hosts
# _spawn_hunting_sheriff on the next load, whatever the rot stage. The
# NEGLECT OVERRIDE beats the ledger: reach VANE_NEGLECT_EVIDENCE canonical
# beats having shared fewer than VANE_MIN_INFORMED discoveries and he
# hollows regardless (evaluated at his office door, which every share
# must walk through -- so it cannot be dodged by sharing after the fact).
# All playtest-tunable, same bucket as the SUS_* stealth block.
VANE_HOLLOW_AT = 3            # net despair that latches the hollow turn
VANE_HOPE_ACT = -1            # one real discovery shared with him
VANE_DESPAIR_ACT = 1          # an ordinary bad beat (the preacher's murder)
VANE_PAPER_DESPAIR = 2        # the newspaper: walks him to the edge
VANE_DESPAIR_FLOOR = -2       # hope banks to -2 at most (never immunity)
VANE_MIN_INFORMED = 1         # shares needed to dodge the neglect override
VANE_NEGLECT_EVIDENCE = 3     # the descent line: 3 canonical beats
# Underground is wrong from the first rung -- a baseline world rot even
# at 0 evidence, deepening on the full evidence count (not capped at 3).
UNDERGROUND_SCENES = {
    "well_bottom", "well_passage",
    "works_cistern", "works_sorting", "works_scriptorium", "works_sign",
    "works_deepface",
    "depths_antechamber", "depths_procession", "depths_hall",
    "depths_threshing", "depths_stair",
    # the dead-end branch rooms hang off their parent corridors and share
    # its underground treatment (baseline rot + Enemy-cultist pursuit).
    "the_sump", "the_cells", "the_old_stores",
}

# Where His gaze can OPEN. He watches under the open sky, in His own deep, and
# -- since the "no light = danger" rework (TODO #21) -- inside the DARK
# non-refuge interiors (`DIM_INTERIOR_SCENES`), where the light is the refuge
# instead of the building: _tick_watchers treats being in the DARK there as
# exposure, and a light pool / the flashlight is the cover (and burns them,
# WATCHER_LIGHT_BURN). The true refuges (SAFE_SCENES) stay gaze-free by being
# excluded here AND KING_FREE. A new plain surface interior is still excluded
# by default. Read by _tick_watchers (the whole wave machine gates on it) and
# _roll_fold_watcher.
WATCHER_OPEN_SCENES = (OUTDOOR_SCENES | UNDERGROUND_SCENES
                       | DIM_INTERIOR_SCENES
                       | {"brimley", "effigy_grove"})

# Ashfall (DESIGN.md §2): a slow drifting pale-yellow ashfall, the pressure
# of the vessel made visible -- His attention settling on you, not snow, not
# weather. Density scales with the world rot stage (light at 1 -> a steady
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
