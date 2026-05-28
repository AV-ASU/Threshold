"""The depths -- everything below the basement level. The ritual at
well_bottom drops the player here; from this point the only
direction is down.

Floors, top to bottom:
  depths_antechamber  -- the fall zone
  depths_procession   -- the moving-candle column
  depths_hall         -- the kneeling grid
  depths_threshing    -- the threshing floor
  depths_stair        -- the empty spiral down
  dark                -- the hive: the congregation + Mara, turned (scene
                         key kept; was the old-family-bodies room)
  threshold           -- the doorframe

Hooded chasers populate the first three rooms. The flashlight is
force-disabled in all depths scenes. Hide spots placed liberally so
the player has cover to recover in.
"""
import math
import random
from constants import TILE
from entities.decoration import Decoration
from entities.enemy import Enemy
from entities.npc import NPC
from .base import Scene
from .dialogue import _evidence


def _ambient(scene, sfx, vol, lo, hi):
    """Wire a periodic ambient sfx to scene.on_update_fn. Each room
    gets its own cue + period so the depths read as different
    spaces, not one repeated basement."""
    scene._amb_t = random.uniform(lo, hi)
    def _tick(game, sc, dt):
        sc._amb_t -= dt
        if sc._amb_t <= 0:
            sc._amb_t = random.uniform(lo, hi)
            game.audio.play(sfx, vol)
    scene.on_update_fn = _tick


def _cultist(x, y, speed=1.0, waypoints=None):
    """Hooded chaser. Combat is gone, so atk is forced to 0 every
    tick by Enemy.update; the danger is contact -- the dread
    aperture slams to 0 if a cultist touches the player. Slightly
    slower than the player's walk so cover-running works. Aggro
    is short (~180px line of sight) and respects player.hidden, so
    the player can sneak past in cover and stand still in a hide
    spot to break the chase. Optional waypoints walk a fixed route
    while the player is out of aggro range."""
    e = Enemy(x, y, kind="cultist", hp=1, atk=0, speed=speed,
              aggro=180, atk_range=22, ai="chase",
              drops=[], can_charge=False)
    e.respawning = False
    e.respects_hide = True
    if waypoints:
        e.waypoints = list(waypoints)
        e._wp_i = 0
        e.wp_pause = 0.8
    return e


def _box(w, h):
    """Return a (floor, objects) pair for a w x h walled room with
    walkable interior. Caller punches exits into objects after."""
    floor = ["x" * w for _ in range(h)]
    objects_l = []
    for y in range(h):
        if y == 0 or y == h - 1:
            objects_l.append(list("#" * w))
        else:
            row = ["#"] + ["."] * (w - 2) + ["#"]
            objects_l.append(row)
    return floor, objects_l


def build_depths_antechamber():
    floor, objs = _box(10, 10)
    objs[5][9] = "E"   # east passage to procession
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_antechamber", floor, objects, music="basement")
    sc.add_exit("E", "depths_procession", "from_antechamber")
    sc.set_spawn("default",   4, 5)
    sc.set_spawn("from_above", 4, 5)
    sc.add_decoration(Decoration(2 * TILE + 16, 3 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(7 * TILE + 16, 6 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(4 * TILE + 16, 4 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(5 * TILE + 16, 7 * TILE + 16, "bloodstain"))
    # Cobweb grime in the corners of the fall zone.
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(8 * TILE + 26, 8 * TILE + 26, "cobweb",
                                 ang=math.pi))
    # Two pillar-style hide spots in opposite corners.
    sc.hide_spots = [
        (1 * TILE + 24, 8 * TILE + 16, "behind"),
        (8 * TILE + 16, 1 * TILE + 24, "behind"),
    ]
    # One cultist patrolling a small loop near the east passage.
    sc.add_enemy(_cultist(8 * TILE + 16, 8 * TILE + 16, speed=0.85,
                          waypoints=[(8 * TILE + 16, 8 * TILE + 16),
                                     (8 * TILE + 16, 3 * TILE + 16),
                                     (5 * TILE + 16, 3 * TILE + 16),
                                     (5 * TILE + 16, 8 * TILE + 16)]))
    _ambient(sc, "cult_breath", 0.18, 6.0, 10.0)

    def _interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - (4 * TILE + 16)) < 36 and abs(py - (4 * TILE + 16)) < 36:
            _evidence(game, "the_fall",
                "The rope is gone above you and you are not hurt -- the way "
                "down didn't want you broken, only delivered. Cut stone, "
                "worn smooth by years of feet that came this way before you."
            )
    sc.on_interact_fn = _interact

    def _on_enter(game, scene):
        if game.save.flag("first_antechamber"):
            return
        game.save.set_flag("first_antechamber", True)
        game.show_notice("This is what the well was a throat for. The work "
                         "of the town goes on down here, in the dark.",
                         duration=4.0)
    sc.on_enter_fn = _on_enter
    return sc


def build_depths_procession():
    floor, objs = _box(14, 8)
    objs[4][13] = "E"   # east to hall
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_procession", floor, objects, music="basement")
    sc.add_exit("E", "depths_hall", "from_procession")
    sc.set_spawn("default",          1, 4)
    sc.set_spawn("from_antechamber", 1, 4)
    # A line of candles along the centre, suggesting the procession
    # column. Two cultists walking it at this hour.
    for cx in range(2, 13, 2):
        sc.add_decoration(Decoration(cx * TILE + 16, 4 * TILE + 16,
                                     "candle"))
    # Cobweb grime in the high corners of the procession column.
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(12 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = [
        (3 * TILE + 16, 1 * TILE + 24, "behind"),
        (10 * TILE + 16, 6 * TILE + 16, "behind"),
        (6 * TILE + 16, 6 * TILE + 16, "behind"),
    ]
    # Two cultists walking the column, single file, opposite phases
    # so they meet between (5..10) and pass each other. Endpoints
    # held away from the west-edge spawn (col 1) so the player
    # arrives with breathing room.
    sc.add_enemy(_cultist(5 * TILE + 16, 4 * TILE + 16, speed=0.9,
                          waypoints=[(12 * TILE + 16, 4 * TILE + 16),
                                     (5  * TILE + 16, 4 * TILE + 16)]))
    sc.add_enemy(_cultist(10 * TILE + 16, 4 * TILE + 16, speed=0.9,
                          waypoints=[(4  * TILE + 16, 4 * TILE + 16),
                                     (10 * TILE + 16, 4 * TILE + 16)]))
    _ambient(sc, "blip_soft", 0.12, 2.5, 4.5)

    def _on_enter(game, scene):
        if game.save.flag("first_procession"):
            return
        game.save.set_flag("first_procession", True)
        game.show_notice("A column of candles, walked single file. They came "
                         "down here singing, once. Now they only walk.",
                         duration=4.0)
    sc.on_enter_fn = _on_enter
    return sc


def build_depths_hall():
    floor, objs = _box(14, 10)
    objs[5][13] = "E"   # east to threshing floor
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_hall", floor, objects, music="basement")
    sc.add_exit("E", "depths_threshing", "from_hall")
    sc.set_spawn("default",        1, 5)
    sc.set_spawn("from_procession", 1, 5)
    # The east wall holds the iron door the kneeling grid faces.
    # Three cultists in the room: two flanking the door, one on
    # patrol. Hide spots scatter so the player can pick a route.
    sc.add_decoration(Decoration(12 * TILE + 16, 5 * TILE + 16,
                                 "phantom_mark"))
    # A "wrong" mount watching from the wall -- belongs to the dark.
    sc.add_decoration(Decoration(8 * TILE + 16, 0 * TILE + 18,
                                 "wrong_taxidermy", wall="N", seed=21))
    sc.add_decoration(Decoration(6 * TILE + 16, 4 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(6 * TILE + 16, 6 * TILE + 16, "candle"))
    # Cobweb grime in the low corners (the kneeling grid faces the
    # north iron door).
    sc.add_decoration(Decoration(1 * TILE + 6, 8 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.add_decoration(Decoration(12 * TILE + 26, 8 * TILE + 26, "cobweb",
                                 ang=math.pi))
    sc.hide_spots = [
        (1 * TILE + 24, 2 * TILE + 16, "behind"),
        (1 * TILE + 24, 7 * TILE + 16, "behind"),
        (8 * TILE + 16, 1 * TILE + 24, "behind"),
        (8 * TILE + 16, 8 * TILE + 16, "behind"),
    ]
    # Two stationary cultists kneel at the iron door, facing east.
    # Aggro starts at 0 (oblivious) so they don't react until the
    # centre-aisle trigger flips them. Single-point waypoint pins
    # them in place; lock_facing keeps them turned toward the door.
    # The third cultist patrols a vertical strip on the west side,
    # regardless.
    kneel_a = _cultist(11 * TILE + 16, 4 * TILE + 16, speed=0.8,
                       waypoints=[(11 * TILE + 16, 4 * TILE + 16)])
    kneel_b = _cultist(11 * TILE + 16, 6 * TILE + 16, speed=0.8,
                       waypoints=[(11 * TILE + 16, 6 * TILE + 16)])
    for k in (kneel_a, kneel_b):
        k.aggro = 0
        k.facing = (1, 0)
        k.lock_facing = True
    sc.add_enemy(kneel_a)
    sc.add_enemy(kneel_b)
    # Patrol starts at the south end so the player (arriving from
    # the west at (1,5)) doesn't spawn within touch range.
    sc.add_enemy(_cultist(2 * TILE + 16, 8 * TILE + 16, speed=0.95,
                          waypoints=[(2 * TILE + 16, 2 * TILE + 16),
                                     (2 * TILE + 16, 8 * TILE + 16)]))

    # Centre-aisle trigger: stepping into the middle column wakes
    # the kneelers. Trigger rect spans the full vertical run of the
    # aisle, x = cols 6..7 inclusive.
    def _alert_kneelers(game):
        for e in sc.enemies:
            if e.kind == "cultist" and getattr(e, "aggro", 0) == 0:
                e.aggro = 600
                e.lock_facing = False
                e.waypoints = None
        game.audio.play("low_pulse", 0.55)
    sc.triggers.append({
        "rect": (6 * TILE, 1 * TILE, 8 * TILE, 9 * TILE),
        "fn": _alert_kneelers,
        "once": True,
        "fired": False,
    })
    _ambient(sc, "whisper", 0.14, 7.0, 12.0)

    def _on_enter(game, scene):
        if game.save.flag("first_hall"):
            return
        game.save.set_flag("first_hall", True)
        game.show_notice("Rows worn into the floor where knees have pressed, "
                         "all of them turned to the iron door. They are "
                         "waiting for it to open.", duration=4.0)
    sc.on_enter_fn = _on_enter
    return sc


def build_depths_threshing():
    floor, objs = _box(12, 10)
    objs[5][11] = "E"   # east to stair
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_threshing", floor, objects, music="basement")
    sc.add_exit("E", "depths_stair", "from_threshing")
    sc.set_spawn("default",   1, 5)
    sc.set_spawn("from_hall", 1, 5)
    # The yield. Grain mixed with old blood. No cultists -- the room
    # itself does the work. One hide spot tucked at the far edge.
    for bx, by in [(4, 4), (6, 5), (8, 6), (5, 7), (7, 4)]:
        sc.add_decoration(Decoration(bx * TILE + 16, by * TILE + 16,
                                     "bloodstain"))
    sc.add_decoration(Decoration(6 * TILE + 16, 5 * TILE + 16,
                                 "phantom_mark"))
    # Cobweb grime in the high corners of the threshing floor.
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(10 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = [
        (2 * TILE + 16, 8 * TILE + 16, "behind"),
        (10 * TILE + 16, 1 * TILE + 24, "behind"),
    ]
    _ambient(sc, "step_grass", 0.22, 3.5, 6.0)

    def _interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - (6 * TILE + 16)) < 36 and abs(py - (5 * TILE + 16)) < 36:
            _evidence(game, "threshing_floor",
                "The yield, raked into low heaps: grain, and threaded "
                "through it something darker and old. This is where what "
                "the town takes in gets broken down small enough to feed "
                "what waits below."
            )
    sc.on_interact_fn = _interact
    return sc


def build_depths_stair():
    floor, objs = _box(8, 10)
    objs[8][4] = "D"   # south to dark
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_stair", floor, objects, music="basement")
    sc.add_exit("D", "dark", "from_stair")
    sc.set_spawn("default",        1, 5)
    sc.set_spawn("from_threshing", 1, 5)
    # One candle at the head of the stair. The Stair is empty per
    # design -- silence is the keeper.
    sc.add_decoration(Decoration(4 * TILE + 16, 4 * TILE + 16, "candle"))
    sc.hide_spots = [
        (1 * TILE + 24, 8 * TILE + 16, "behind"),
        (6 * TILE + 16, 1 * TILE + 24, "behind"),
    ]
    _ambient(sc, "low_pulse", 0.10, 11.0, 16.0)

    def _on_enter(game, scene):
        if game.save.flag("first_depthstair"):
            return
        game.save.set_flag("first_depthstair", True)
        game.show_notice("The stair spirals down past the last of the "
                         "candlelight. No guards. Nothing down here needs "
                         "guarding -- no one who reaches it ever turns back.",
                         duration=4.0)
    sc.on_enter_fn = _on_enter
    return sc


def _mara_voice(game, npc):
    """Mara's one-shot recognition -- the #6 payoff. The case was never a
    rescue; you went deeper and found her already gone. After it, she has
    gone back to the kneeling."""
    if game.save.flag("hive_seen"):
        game.dialog.show(
            ["[c=dim]She has gone back to the kneeling. She won't look at "
             "you again.[/c]"],
            speaker="", voice="blip_soft", portrait="narrator")
        return
    game.save.set_flag("hive_seen", True)
    game.audio.force_silence()
    game.audio.play("low_pulse", 0.6)
    game.dialog.show([
        "[c=dim](You say her name. The hooded head lifts.)[/c]",
        "It is Mara.",
        "[s=slow]\"I'm not lost. I've never been this close.\"[/s]",
    ], speaker="", voice="blip_soft", portrait="narrator")
    _evidence(game, "the_congregation", [
        "Mara, kneeling with the congregation. Turned. There was never "
        "anyone to bring back -- only this, and now you're in it with her.",
    ])


def build_dark():
    floor, objs = _box(12, 10)
    objs[8][3] = "D"   # south-west to threshold -- off the centre aisle,
                       # so the player never has to push through Mara
    objects = ["".join(r) for r in objs]
    sc = Scene("dark", floor, objects, music="basement")
    sc.add_exit("D", "threshold", "from_dark")
    sc.set_spawn("default",    6, 1)
    sc.set_spawn("from_stair", 6, 1)
    # The hive. The flashlight is force-off here (CULT_DARK_SCENES) so the
    # dread aperture's clear circle is the only light -- you find the
    # congregation a face at a time. They're NPCs, not enemies: no chase,
    # no contact penalty. The room's whole work is the recognition.
    def _murmur(game, npc):
        game.dialog.show(
            ["[c=dim]The kneeler doesn't stir. Its lips move, no sound.[/c]"],
            speaker="", voice="blip_soft", portrait="narrator")
    # The congregation: hooded, idle, facing the south doorframe they
    # worship. Solid, so the player threads between them in the dark.
    for kx, ky in [(3, 4), (8, 4), (4, 6), (9, 6), (8, 7)]:
        n = NPC(kx * TILE + 16, ky * TILE + 16, "A kneeler", "cultist",
                dialogue_fn=_murmur, movement="idle")
        n.facing = (0, 1)
        sc.add_npc(n)
    # Mara, front and centre on the aisle -- the one head that lifts when
    # you speak. Just one more hooded kneeler until you reach her.
    mara = NPC(6 * TILE + 16, 5 * TILE + 16, "Mara", "cultist",
               dialogue_fn=_mara_voice, movement="idle")
    mara.facing = (0, -1)
    sc.add_npc(mara)
    sc.hide_spots = [
        (1 * TILE + 24, 8 * TILE + 16, "behind"),
        (10 * TILE + 16, 1 * TILE + 24, "behind"),
    ]
    _ambient(sc, "heartbeat", 0.18, 3.5, 5.0)
    return sc


def build_threshold():
    floor, objs = _box(10, 10)
    objects = ["".join(r) for r in objs]
    sc = Scene("threshold", floor, objects, music="void")
    sc.set_spawn("default",   5, 1)
    sc.set_spawn("from_dark", 5, 1)
    # Doorframe at the centre. Pressing E at it seals the door
    # (seal_threshold ending) -- no item gate. The Mask and the Play were
    # already spent at the Deep Stair to open the way down here, so a
    # player who descended can always finish; nothing to soft-lock on.
    lintel_x, lintel_y = 5 * TILE + 16, 5 * TILE + 16
    sc._lintel_pos = (lintel_x, lintel_y)
    sc.add_decoration(Decoration(lintel_x, lintel_y - TILE, "smoke"))

    def _threshold_on_enter(game, scene):
        if game.save.flag("first_threshold"):
            return
        game.save.set_flag("first_threshold", True)
        _evidence(game, "the_doorframe",
            "A doorframe with no wall."
        )
    sc.on_enter_fn = _threshold_on_enter

    def _threshold_interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - lintel_x) > 40 or abs(py - lintel_y) > 40:
            return
        game.audio.force_silence()
        game.audio.play("arg_chime", 0.7)
        game.dialog.show([
            "[c=dim](You set both hands to the cold frame. You spent His "
            "face and His Play to come this far. There is nothing left to "
            "give it but the rest of you.)[/c]",
            "[s=slow][c=dim]...the smoke stops.[/c][/s]",
        ], speaker="", voice="blip_soft", portrait="narrator")
        _evidence(game, "the_seal", "It is done.")
        game._play_ending("seal_threshold")
    sc.on_interact_fn = _threshold_interact
    return sc
