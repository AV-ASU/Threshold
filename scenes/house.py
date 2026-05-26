"""The Clerk's house (above the inn): spare_room (player's cot),
main floor (kitchen + living + front door), the Clerk's bedroom
(locked, holds the playscript + car keys + robe), the basement (photograph,
notebook, flashlight, bulkhead exit).

The bedroom KEY means the spare room above the inn. The house KEY
means the Clerk's downstairs. Geometries, pickups, decorations,
NPCs, and triggers are preserved.
"""
import math
import time
import random
import pygame
from constants import TILE
from entities.npc import NPC
from entities.decoration import Decoration
from .base import Scene
from .dialogue import basement_photo_dialogue, clerk_dialogue, _evidence


# ---- spare_room (key: 'bedroom') ----

def build_bedroom():
    """The player's spare room above the inn. THRESHOLD redesign:
    larger and more lived-in -- a wardrobe in the corner, a
    bookshelf next to the writing table, a rag rug on the floor,
    layered candles, and more wall props so the room reads as a
    place a person has been *staying*, not just sleeping. The cot
    is still the save point.

    Hide spots: behind the wardrobe (real cover this time) and
    under the writing table. The cot is the save trigger, not a
    hide spot."""
    floor = ["=" * 16 for _ in range(12)]
    # Furniture is drawn as sized decorations (multi-tile / sub-tile)
    # with invisible solid 'X' tiles under their footprints for
    # collision: a 2x2 cot in the NW corner, a long shallow bookshelf on
    # the north wall, a writing desk, and a tall wardrobe on the west
    # wall. 'i' = window, 'D' = south door.
    objects = [
        "WWWWWWiWWWWiWWWW",   # 0  north wall, two windows
        "W.XX.......XXX.W",   # 1  cot head (2-3) + long bookshelf (11-13)
        "W.XX...........W",   # 2  cot footprint (cols 2-3, rows 1-3)
        "W.XX...........W",   # 3
        "W..............W",   # 4
        "W.........XX...W",   # 5  writing desk footprint (cols 10-11)
        "W..............W",   # 6
        "W.X............W",   # 7  wardrobe footprint (col 2, rows 7-8)
        "W.X............W",   # 8
        "W..............W",   # 9
        "W..............W",   # 10
        "WWWWWWWDWWWWWWWW",   # 11 south wall, door D at col 7
    ]
    sc = Scene("bedroom", floor, objects, music="home")
    sc.add_exit("D", "house", "from_bedroom")
    sc.set_spawn("default", 7, 6)
    sc.set_spawn("from_house", 7, 10)
    # The cot fills the NW corner (cols 2-3, rows 2-3). The player
    # stands one tile east at col 4 row 3 to sleep/save.
    sc._cot_pos = (4 * TILE + 16, 3 * TILE + 16)
    # Hide spots: BESIDE the wardrobe (col 3 row 8) and UNDER the
    # writing desk (col 11 row 6).
    sc.hide_spots = [
        (3 * TILE + 16,  8 * TILE + 16, "behind"),   # beside wardrobe
        (11 * TILE + 16, 6 * TILE + 16, "under"),    # under writing desk
    ]

    # Worn rug over the open centre -- a multi-tile covering, set
    # off-grid so it breaks the plank tiling. Added first so the props
    # below draw on top of it.
    sc.add_decoration(Decoration(7 * TILE + 24, 7 * TILE + 8, "rug",
                                 w=120, h=76, color=(86, 42, 46), seed=17))
    # Sized darkwood furniture (decorations over the 'X' collision
    # footprints in the object map). A 2x2 cot in the corner, a long
    # shallow bookshelf on the north wall, a writing desk + chair, a
    # tall wardrobe on the west wall.
    sc.add_decoration(Decoration(3 * TILE, 2 * TILE + 16, "bed", w=60, h=92))
    # Bookshelf shoved up against the north wall so it covers the lower
    # part of the east window -- a tall room, a long low case crowding
    # the glass.
    sc.add_decoration(Decoration(12 * TILE + 16, 1 * TILE - 6, "bookshelf",
                                 w=86, h=22, seed=5))
    sc.add_decoration(Decoration(11 * TILE, 5 * TILE + 12, "table", w=58, h=42))
    sc.add_decoration(Decoration(12 * TILE + 18, 6 * TILE + 4, "chair",
                                 w=22, h=28))
    sc.add_decoration(Decoration(2 * TILE + 16, 8 * TILE, "wardrobe",
                                 w=26, h=54))
    # Duffel bag beside the cot.
    sc.add_decoration(Decoration(2 * TILE + 28, 5 * TILE + 16, "bowl",
                                 filled=True))
    # Lit clock on the writing table.
    sc.add_decoration(Decoration(11 * TILE + 16, 5 * TILE + 6, "clock"))
    # Two candles on the bedside (north wall edge) and one on the
    # writing table.
    sc.add_decoration(Decoration(2 * TILE + 8,  0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(13 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(11 * TILE + 16, 5 * TILE + 4, "candle"))
    # Northern-MN lodge dressing on the north wall: a mounted buck
    # (replaces the old generic photo) between the windows, a trophy
    # walleye to the west, and cobwebs fanning from the high corners.
    sc.add_decoration(Decoration(9 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(4 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(14 * TILE + 24, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    # A phantom_mark scratched into the wood near the door -- subtle,
    # easy to miss the first session.
    sc.add_decoration(Decoration(4 * TILE + 12, 9 * TILE + 16,
                                 "phantom_mark"))
    # Drifting motes through the room -- dust in old light.
    for i in range(7):
        sc.add_decoration(Decoration(3 * TILE + i * 64,
                                     3 * TILE + (i % 3) * 40, "mote"))
    # A small bloodstain near the south door -- subtle, the kind
    # of thing you don't notice on day one.
    sc.add_decoration(Decoration(8 * TILE + 8, 10 * TILE + 16,
                                 "bloodstain"))

    sc.on_enter_fn = bedroom_on_enter
    sc.on_interact_fn = bedroom_interact
    sc.on_update_fn = bedroom_on_update
    return sc


def bedroom_on_enter(game, scene):
    """Opening sequence + idempotent. The first session in this
    scene is the game's first minute: the wake notice, the
    candle-dip + creak when the doorway watcher manifests, and the
    suppressed sprint. (The arrival drive -- the car into Brimley,
    the dying engine -- plays before this, in the Game's "opening"
    state.) These pieces fire from `bedroom_on_update` so they can
    be paced over real seconds rather than crammed into entry. We
    seed them here.

    Subsequent visits (after sleeping in the cot, or returning
    later in the run) skip the opening entirely -- only the
    cot-as-save-point remains."""
    if game.save.flag("wake_up"):
        return
    game.save.set_flag("wake_up", True)
    # Wake-state audio: muffled music + slow heartbeat. The
    # Game side reads `_wake_muffle_t` to drive these so audio
    # cleanup happens in one place.
    game._wake_muffle_t = 8.0
    game._wake_heartbeat_t = 0.6
    # Pacing slots tracked on the scene itself so each event
    # fires once per session. `_opening_t` ticks up in
    # bedroom_on_update; the slots check thresholds.
    scene._opening_t = 0.0
    scene._opening_slots = {
        "wake_notice_armed":   True,    # fires on first step
    }
    scene._spawn_pos = scene.spawns.get("default", (0, 0))


def bedroom_on_update(game, scene, dt):
    """First-minute pacing for the spare room. Counts elapsed
    seconds since the player woke and fires the opening beats
    on real time rather than entry. All slots are guarded so
    nothing fires twice."""
    slots = getattr(scene, "_opening_slots", None)
    if slots is None:
        return
    scene._opening_t = getattr(scene, "_opening_t", 0.0) + dt
    p = game.player
    if p is None:
        return
    # First-movement gate. The wake notice + the watcher manifest
    # only after the player has actually input movement, so the
    # opening line lands as the character noticing what the
    # player just noticed (not a frame-one overlay).
    sx, sy = scene._spawn_pos
    moved = (abs(p.x - sx) + abs(p.y - sy)) > 6
    if slots["wake_notice_armed"] and moved:
        slots["wake_notice_armed"] = False
        game.show_notice(
            "You wake up.",
            duration=5.0,
        )
    # Door-stuck recoil: when begin_transition rejects the first
    # attempt to leave, it sets `_door_stuck_recoil` on the
    # scene. We dip the candle once in response so the player
    # has something subliminal to mark the moment, then clear
    # the flag.
    if getattr(scene, "_door_stuck_recoil", False):
        scene._door_stuck_recoil = False
        for d in scene.decorations:
            if d.kind == "candle":
                d.kwargs["dip_t0"] = time.time()


def bedroom_interact(game):
    """E near the cot: a furniture-only save point in this build.
    E near the writing table: read a short notebook. The notebook
    is diegetic (no inventory pickup); re-reading is allowed. First
    read sets `read_journal` so other systems can react."""
    sc = game.scene
    px, py = game.player.x, game.player.y
    # Writing table -- col 8 row 6. Range 40 matches the cot's.
    tx = 8 * TILE + 16
    ty = 6 * TILE + 16
    if abs(px - tx) <= 40 and abs(py - ty) <= 40:
        game.dialog.show([
            "[c=dim](A lined notebook on the writing table.)[/c]",
            "[c=dim]The pages are blank.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
        if not game.save.flag("read_journal"):
            game.save.set_flag("read_journal", True)
        return
    # The cot is just furniture now -- single-session game, no sleeping
    # or saving.
    cx, cy = sc._cot_pos
    if abs(px - cx) > 40 or abs(py - cy) > 40:
        return
    game.show_notice("A cot. You don't feel like lying down.")


# ---- innkeeper_house (key: 'house') ----

def build_house():
    """The Clerk's downstairs: kitchen on the left half, living
    room on the right half. Wall divider with a door between them.
    Front door on the south wall (B exit -- the player may be
    blocked here by the Clerk). Cellar hatch in the
    kitchen. Door to spare_room hallway on the north (col 13). Door
    to the Clerk's bedroom on the north (col 4) -- locked
    initially."""
    floor = [
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
        "==================",
    ]
    # Kitchen (left of the col-7 counter bar): a dining table + chairs,
    # the stove, and a run of base cabinets ('5' = counter). The bar
    # ('5' down col 7) reads as a kitchen peninsula dividing the kitchen
    # from the living room, replacing the old blank wall divider.
    objects = [
        "WWWW1WWWWWWWWBWWWW",
        "W................W",
        "W................W",
        "W.tt...5.........W",
        "W.cc...5....f....W",
        "W.k....5.........W",
        "W.55...5.........W",
        "W................W",
        "W................W",
        "W..L.............W",
        "W................W",
        "WWWWWWWDWWWWWWWWWW",
    ]
    sc = Scene("house", floor, objects, music="home")
    # B = front door (south wall, col 13). The Clerk blocks this.
    sc.add_exit("B", "bedroom", "from_house")
    # 1 = Clerk's bedroom door (col 4). Locked at first.
    sc.add_exit("1", "son_room", "from_house")
    # D = back door, leads to the gravel yard.
    sc.add_exit("D", "our_house_area", "from_house")
    # L = cellar hatch in the kitchen.
    sc.add_exit("L", "basement", "from_house")
    sc.set_spawn("default", 9, 9)
    # The B door (spare-room) is at col 13 of the north wall.
    # The 1 door (Clerk's bedroom) is at col 4. They were both
    # set to (4, 1) which trapped the spare-room arrival south of
    # the kitchen table at (4, 3). Each spawn is now under its own
    # door.
    sc.set_spawn("from_bedroom", 13, 1)        # south of B (spare-room)
    sc.set_spawn("from_son_room", 4, 1)        # south of 1 (Clerk's bedroom)
    sc.set_spawn("from_our_house_area", 7, 10)
    # The L cellar hatch is at (3, 9). Spawning even one tile north
    # of it (3, 8) shares the same column -- a south key press would
    # walk the player straight back onto L and re-enter the basement.
    # Offset the spawn one column east so the player has to actively
    # navigate back to the hatch to descend again.
    sc.set_spawn("from_basement", 4, 8)

    # A large worn rug before the hearth in the living room -- off-grid
    # and multi-tile so it breaks the plank tiling. Added first so the
    # props below sit on top of it.
    sc.add_decoration(Decoration(11 * TILE + 24, 7 * TILE + 12, "rug",
                                 w=140, h=92, color=(70, 58, 40), seed=23))
    # Sized darkwood kitchen furniture (decorations over invisible
    # collision tiles): a 2-tile dining table + two chairs, the range.
    # The counter bar/cabinets stay as object tiles.
    sc.add_furniture("table", [(2, 3), (3, 3)], w=58, h=40)
    sc.add_furniture("chair", [(2, 4)], w=22, h=28)
    sc.add_furniture("chair", [(3, 4)], w=22, h=28)
    sc.add_furniture("stove", [(2, 5)], w=30, h=40)
    # Decorations: kitchen clutter on the left, fireplace on the
    # right, wall items on the NORTH wall (row 0).
    sc.add_decoration(Decoration(10 * TILE + 16, 0 * TILE + 18, "clock"))
    sc.add_decoration(Decoration(3 * TILE + 16, 0 * TILE + 22, "meat"))
    sc.add_decoration(Decoration(2 * TILE + 16, 3 * TILE + 14, "candle"))  # on table
    sc.add_decoration(Decoration(0 * TILE + 24, 5 * TILE + 16, "banner",
                                 color=(140, 60, 70)))
    sc.add_decoration(Decoration(12 * TILE + 16, 4 * TILE + 14, "candle"))  # on fireplace
    for i in range(6):
        sc.add_decoration(Decoration(40 + i * 90,
                                     80 + (i % 3) * 60, "mote"))
    # THRESHOLD liminal dressing: the lodge common room reads
    # wrong-empty. A wall of the vanished by the north wall of the
    # living room (the same guests the cellar Ledger records), a meal
    # abandoned mid-setting on the kitchen table, and a single chair
    # knocked over in all that empty floor -- the one wrong detail in
    # the void.
    sc.add_decoration(Decoration(9 * TILE + 16, 0 * TILE + 22, "missing_flyer"))
    sc.add_decoration(Decoration(11 * TILE + 16, 0 * TILE + 24, "polaroid_wall"))
    sc.add_decoration(Decoration(14 * TILE + 16, 0 * TILE + 22, "missing_flyer"))
    sc.add_decoration(Decoration(2 * TILE + 16, 3 * TILE + 8, "place_setting"))
    sc.add_decoration(Decoration(13 * TILE + 16, 6 * TILE + 16, "overturned_chair"))
    sc.add_decoration(Decoration(10 * TILE + 16, 8 * TILE + 16, "small_chair"))
    sc.add_decoration(Decoration(15 * TILE + 16, 7 * TILE + 16, "small_chair"))
    sc.add_decoration(Decoration(8 * TILE + 16, 9 * TILE + 16, "phantom_mark"))

    # Northern-MN lodge decor. Wall mounts (no collision) along the
    # east + west walls; an oil lamp on the kitchen counter; cobwebs in
    # the high corners; firewood and an antler coat-rack on the floor
    # (collision, tucked against walls so they never block a path).
    # Trophy mounts flush on the NORTH wall (row 0), facing down into the
    # room -- the buck replaces the old generic photo; a walleye on the
    # kitchen-side wall. (The "wrong" taxidermy lives underground now.)
    sc.add_decoration(Decoration(15 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 24, "mounted_fish"))
    sc.add_decoration(Decoration(2 * TILE + 14, 6 * TILE + 2, "kerosene_lamp"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb", ang=0.0))
    sc.add_decoration(Decoration(16 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_furniture("firewood", [(15, 8), (16, 8)], w=58, h=24)
    sc.add_furniture("antler_rack", [(16, 2)], w=22, h=46)

    # The kitchen drawer position -- where 'paper' lives. Sits beside
    # the stove (col 2 after the kitchen-cluster shift, drawer at col 3).
    sc._drawer_pos = (3 * TILE + 16, 5 * TILE + 16)
    # Hide spots: under the kitchen table, behind the kitchen shelves,
    # beside the fireplace. Each spot lands on a walkable tile next
    # to the visible cover (not on top of a solid prop).
    sc.hide_spots = [
        (3 * TILE + 16, 3 * TILE + 16, "under"),    # under the kitchen table
        (3 * TILE + 16, 6 * TILE + 16, "behind"),   # beside the shelves
        (11 * TILE + 16, 4 * TILE + 16, "behind"),  # beside the fireplace
    ]

    sc.on_enter_fn = house_on_enter
    sc.on_interact_fn = house_interact
    return sc


def house_on_enter(game, scene):
    """Place the kitchen drawer's paper pickup, the Clerk NPC
    himself (visible going about his business until the
    confrontation fires), and the blocking variant after
    confrontation. Two states for the Clerk:

      pre-confrontation:  visible NPC near the fireplace, talkable
                          (uses clerk_dialogue). Wanders within
                          the living room. Solid.
      post-confrontation: planted in the front doorway, no_prompt
                          (no dialogue offered), solid. The 'sit
                          back down' line is one-shot from the
                          confrontation handler."""
    if not game.save.flag("paper_taken"):
        scene.add_item(
            scene._drawer_pos[0], scene._drawer_pos[1], "paper",
            on_pickup=lambda g: g.save.set_flag("paper_taken", True),
        )
    # Strip any stale host instance so re-entries don't stack.
    scene.npcs = [n for n in scene.npcs
                  if getattr(n, "tag", None) not in
                  ("blocking_innkeeper", "host_innkeeper")]
    scene._key_hook_pos = None
    if game.save.flag("innkeeper_confronted"):
        nx = 6 * TILE + 16
        ny = 10 * TILE + 16
        host = NPC(nx, ny, "Clerk", "old",
                   solid=True, no_prompt=True,
                   voice="blip_low", portrait="old")
        host.facing = (0, -1)
        host.tag = "blocking_innkeeper"
        host.dialogue_fn = None
        scene.add_npc(host)
    else:
        # Daytime: the Clerk is at the table by the fireplace on
        # the east side of the living room. He wanders a small
        # circuit (kitchen <-> living room) so the player sees him
        # moving when they pass through.
        nx = 13 * TILE + 16
        ny = 7 * TILE + 16
        host = NPC(nx, ny, "Clerk", "old",
                   solid=True, no_prompt=False,
                   voice="blip_low", portrait="old",
                   dialogue_fn=clerk_dialogue,
                   movement="patrol", speed=0.6,
                   waypoints=[
                       (13 * TILE + 16, 7 * TILE + 16),   # by fireplace
                       (15 * TILE + 16, 8 * TILE + 16),   # east
                       (10 * TILE + 16, 8 * TILE + 16),   # toward kitchen
                       (10 * TILE + 16, 4 * TILE + 16),   # north
                   ],
                   patrol_pause=2.5)
        host.facing = (-1, 0)
        host.tag = "host_innkeeper"
        scene.add_npc(host)


def house_interact(game):
    """Living-room interact handler. The night key-on-hook
    interaction is gone (the woodshed key lives in the cellar
    now). Function preserved as a stub so future on-interact
    needs (sleeping-Clerk hint, etc.) have a place to land."""
    return


# ---- the Clerk's Room (key: 'son_room') ----
# The Lodge Clerk's private room, off the main floor. No evidence lives
# here -- Mara's room (robe + letter, #1) and the journal (#2) moved to the
# Sorting-Hall cell and the barn, and the Playscript to the Scriptorium
# (scenes/well.py, scenes/interiors.py). The one tell is a pressed cult
# robe in his closet: the smiling trap-keeper is one of them.

def build_son_room():
    """The Lodge Clerk's private room. A bed, a closet (his pressed cult
    robe -- the tell that he's complicit), a bare dresser (he keeps your
    car keys downstairs, behind the tab), a window."""
    floor = [
        "==========",
        "==========",
        "==========",
        "==========",
        "==========",
        "==========",
        "==========",
        "==========",
    ]
    # ONE bed and ONE closet (the original three stacked b + three
    # stacked s read as three beds and three closets). Single
    # tiles each. Dresser (table sprite) at row 6.
    objects = [
        "WWWiWWWWWW",   # 0 north wall, window col 3
        "W........W",   # 1
        "W........W",   # 2
        "W........W",   # 3
        "W..b...s.W",   # 4 bed (col 3) + closet (col 7)
        "W........W",   # 5
        "W.....t..W",   # 6 dresser (col 5; off the door column)
        "WWW1WWWWWW",   # 7 south wall, door 1 at col 3
    ]
    sc = Scene("son_room", floor, objects, music="home")
    sc.add_exit("1", "house", "from_son_room")
    # Door is at (3, 7); spawn at (4, 6) is open floor and one tile
    # off-axis so the player doesn't auto-retrigger.
    sc.set_spawn("default", 4, 6)
    sc.set_spawn("from_house", 4, 6)

    # The dresser (table sprite) holds the car keys. Moved off col 3
    # because col 3 is the door column -- a solid prop directly above
    # the door previously trapped the player inside.
    sc._dresser_pos = (5 * TILE + 16, 6 * TILE + 16)
    # The closet (shelf sprite) holds the Clerk's pressed cult robe -- a
    # flavor clue (he's complicit), not counted evidence.
    sc._closet_pos = (7 * TILE + 16, 4 * TILE + 16)
    # Hide spots: beside the bed, and inside the Clerk's wardrobe.
    sc.hide_spots = [
        (4 * TILE + 16, 4 * TILE + 16, "under"),
        (7 * TILE + 16, 4 * TILE + 16, "in"),
    ]

    # Sized darkwood furniture: a 2x2 bed, a tall closet (the Clerk's robe
    # -> _closet_pos), a low dresser (bare -> _dresser_pos).
    sc.add_furniture("bed", [(2, 3), (3, 3), (2, 4), (3, 4)], w=56, h=56)
    sc.add_furniture("wardrobe", [(7, 3), (7, 4)], w=26, h=54)
    sc.add_furniture("table", [(5, 6), (6, 6)], w=54, h=32)

    # Wall items mounted on the NORTH wall (row 0). Lodge dressing: a
    # mounted buck (replaces the old generic photo) and a trophy
    # walleye flank the window; a cobweb hangs in the NE corner and a
    # kerosene lamp burns on the dresser.
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(7 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(5 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish", flip=True))
    sc.add_decoration(Decoration(8 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_decoration(Decoration(6 * TILE + 16, 6 * TILE + 2,
                                 "kerosene_lamp"))
    for i in range(4):
        sc.add_decoration(Decoration(40 + i * 60,
                                     60 + (i % 2) * 40, "mote"))

    sc.on_interact_fn = clerk_room_interact
    return sc


def clerk_room_interact(game):
    """The Clerk's room. CLOSET (E): his pressed cult robe -- the tell that
    the smiling trap-keeper is one of them. A one-shot flavor clue, NOT
    counted evidence ('clerk_robe' is not in CANONICAL_EVIDENCE, so it
    narrates but never moves the King-gate). DRESSER (E): bare."""
    sc = game.scene
    px, py = game.player.x, game.player.y
    cx, cy = sc._closet_pos
    if abs(px - cx) <= 40 and abs(py - cy) <= 40:
        _evidence(game, "clerk_robe",
                  "A cult robe hangs in the Clerk's closet, pressed and "
                  "folded, ready. The smiling man at the desk is one of "
                  "them.")
        return
    dx, dy = sc._dresser_pos
    if abs(px - dx) <= 40 and abs(py - dy) <= 40:
        game.show_notice("His dresser. Bare -- he keeps your car keys "
                         "downstairs, behind your tab.")


# ---- innkeeper_basement (key: 'basement') ----

def build_basement():
    """The Arcadia Lodge's cellar -- the Clerk's domain. Stone walls,
    packed dirt floor, a single hanging bulb. A photograph stands on a
    shelf; the workbench holds the tab-settling bottle, the woodshed key,
    charcoal. Behind a loose panel in the stone the Clerk keeps the real
    guest register -- the Ledger (evidence #3): everyone who checked into
    the Arcadia and never checked out.

    Single entry/exit via the kitchen cellar hatch. A previous build
    had a south-wall bulkhead leading to the back yard; removed
    because it created the impression of a duplicate basement door
    on the same building footprint. The cellar is now strictly a
    one-way-down room with the ladder back as the only return."""
    floor = ["x" * 12 for _ in range(10)]
    objects_l = []
    for y in range(10):
        if y == 0 or y == 9:
            objects_l.append(list("#" * 12))
        else:
            row = ["#"] + ["."] * 10 + ["#"]
            objects_l.append(row)
    objects_l[1][10] = "U"          # ladder up to the kitchen
    objects_l[5][8]  = "P"          # photo marker -- consumed at build
    objects = ["".join(r) for r in objects_l]
    sc = Scene("basement", floor, objects, music="basement")
    sc.add_exit("U", "house", "from_basement")
    sc.set_spawn("default", 9, 1)
    sc.set_spawn("from_house", 9, 1)

    # A photograph -- placed via the P marker, with the photo
    # NPC (basement_photo_dialogue) hosting interaction.
    pos = sc.consume_marker("P")
    if pos:
        tx, ty = pos
        photo = NPC(tx * TILE + 16, ty * TILE + 16, "Photo", "_invisible",
                    voice="blip_soft", portrait="narrator",
                    dialogue_fn=basement_photo_dialogue,
                    movement="idle", solid=False, tag="basement_photo")
        sc.add_npc(photo)
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 6,
                                     "photo"))

    # Workbench in the SW corner (tab bottle, woodshed key, charcoal).
    # The Clerk's real guest register -- the Ledger (evidence #3) -- is
    # hidden behind a loose panel in the west wall; the candle beside it
    # draws the eye. Found via the wall-panel interact (basement_interact).
    sc._workbench_pos = (2 * TILE + 16, 7 * TILE + 16)
    sc._wall_panel_pos = (1 * TILE + 16, 4 * TILE + 16)
    # Hide spots: under the workbench, behind the chest area.
    sc.hide_spots = [
        (sc._workbench_pos[0], sc._workbench_pos[1] + 8, "under"),
        (5 * TILE + 16, 7 * TILE + 24, "behind"),
    ]
    sc.add_decoration(Decoration(sc._workbench_pos[0],
                                 sc._workbench_pos[1] - 8, "chest",
                                 open=False))

    sc.add_decoration(Decoration(5 * TILE + 20, 7 * TILE + 12,
                                 "bloodstain", scale=3.2))
    sc.add_decoration(Decoration(1 * TILE + 24, 4 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(10 * TILE + 8, 4 * TILE + 16, "candle"))
    # A "wrong" mount on the cellar wall -- too many eyes in the dark.
    sc.add_decoration(Decoration(4 * TILE + 16, 0 * TILE + 20,
                                 "wrong_taxidermy", wall="N", seed=11))
    # One claw gouge etched into the cellar wall.
    sc.add_decoration(Decoration(7 * TILE + 16, 1 * TILE + 8, "claw_marks",
                                 scale=2.2))
    # Cellar grime + a split-wood stack against the SE wall. Cobwebs
    # fan from the high corners; the firewood is collision furniture
    # tucked clear of the workbench, photo, and ladder paths.
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(10 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_furniture("firewood", [(8, 8), (9, 8)], w=58, h=24)
    for mx, my in [(2, 5), (6, 6), (4, 3), (8, 7)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))

    sc.on_enter_fn = basement_on_enter
    sc.on_interact_fn = basement_interact
    return sc


def basement_on_enter(game, scene):
    """Place the charcoal pickup on the workbench (idempotent via save
    flags). The notebook is gated behind the wall_panel interaction in
    basement_interact."""
    game._provoke_cult(0.10)
    wbx, wby = scene._workbench_pos
    if not game.save.flag("charcoal_taken"):
        scene.add_item(
            wbx + 12, wby + 4, "charcoal",
            on_pickup=lambda g: g.save.set_flag("charcoal_taken", True),
        )
    # The cellar bottle. The innkeeper holds the player's car keys
    # "until you settle your tab" -- this bottle is the settle.
    # Placed off to one side of the workbench so it doesn't pile
    # on top of the other pickups.
    if not game.save.flag("cellar_bottle_taken"):
        scene.add_item(
            wbx + 32, wby + 4, "cellar_bottle",
            on_pickup=lambda g: g.save.set_flag("cellar_bottle_taken", True),
        )
    # Woodshed key on a hook beside the workbench. The player
    # descends with the cellar key, finds this, and now has a
    # path to the splitting axe. Trade chain spine: alc -> cellar
    # -> shed -> axe. (Was previously sitting on a hook by the
    # sleeping Clerk; that interaction is removed because
    # the new chain wants the cellar to be the gating space.)
    # The inventory check covers old saves where the player got
    # the key from the legacy night-Clerk interaction or the
    # legacy crate-trade reward without the flag being set --
    # don't drop a duplicate on the workbench.
    if (not game.save.flag("woodshed_key_taken")
            and not game.player.inventory.has("woodshed_key")):
        scene.add_item(
            wbx + 32, wby - 12, "woodshed_key",
            on_pickup=lambda g: g.save.set_flag("woodshed_key_taken", True),
        )
    # Sync workbench chest visual to whether it's been emptied.
    for deco in scene.decorations:
        if deco.kind == "chest":
            deco.kwargs["open"] = game.save.flag("charcoal_taken")


def basement_interact(game):
    """E at the loose wall panel: the Clerk's hidden guest register --
    the Ledger, evidence #3. One-shot via the evidence flag. The closing
    beat lands the pattern on the PI: you signed in tonight like every
    guest before you, and like them there's no check-out beside your name
    (prospective dread -- you won't be leaving either). No time has passed;
    the opening's cut to the room is the same night."""
    sc = game.scene
    px, py = game.player.x, game.player.y
    wpx, wpy = sc._wall_panel_pos
    if abs(px - wpx) > 40 or abs(py - wpy) > 40:
        return
    if game.save.flag("evidence_the_ledger"):
        game.show_notice("The ledger, back behind its panel. You've read "
                         "enough.")
        return
    game.audio.play("pickup_rare", 0.7)
    game.audio.play("low_pulse", 0.45)
    _evidence(game, "the_ledger", [
        "A panel in the stone swings loose. Behind it, a ledger -- not the "
        "one at the front desk. The real one.",
        "Guests going back years, all in the Clerk's hand. A few check-outs, "
        "every one of them old. Then none. No one has left the Arcadia in a "
        "long, long time.",
        "Your own name sits near the bottom, tonight's ink still wet. No "
        "check-out beside it -- the same blank as every name above it.",
        "You came to ask your questions and drive home by morning. So did "
        "all of them.",
    ])
