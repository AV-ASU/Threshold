"""The mistlands -- 100x100 plain west of the Clerk's farm,
split roughly 1/3 / 2/3 by a north-south river. A planked bridge
crosses near its north end (rows 23-26 x cols 32-34). THRESHOLD
rework: the village's six buildings have been scattered across
this map. Three sit on the west bank (Church north, Sheriff +
Farmhouse south); three sit middle-south on the east bank (Shop,
Kid's House, Barn). Player walks the bank to find them. The
cauldron clearing and player's car are still here.

Atmosphere: black haze drawn by Game._draw_mistlands_haze, ambient
'wind' track played by music='wind'."""
import random
from constants import TILE
from entities.decoration import Decoration
from entities.npc import NPC
from .base import Scene


def _brimley_voice(pages, voice="blip_mid"):
    """NPC dialogue_fn from a fixed page list. Speaker name + portrait are
    read off the NPC at call time so each resident speaks as themselves."""
    def _fn(game, npc):
        portrait = getattr(npc, "portrait", None) or npc.sprite_kind
        game.dialog.show(pages, speaker=npc.name, voice=voice,
                         portrait=portrait)
    return _fn


def _stamp_building(objects_l, left, right, top, bot,
                     door_char, door_col):
    """Stamp a rectangular building footprint into objects_l. Outer
    perimeter is wall (W); interior is roof (r); a single door tile
    (door_char) is punched through the south face at door_col. Used
    by build_mistlands for each scattered village building."""
    for cx in range(left, right + 1):
        objects_l[top][cx] = "W"
        objects_l[bot][cx] = "W"
    for ry in range(top + 1, bot):
        objects_l[ry][left] = "W"
        objects_l[ry][right] = "W"
        for cx in range(left + 1, right):
            objects_l[ry][cx] = "r"
    # Punch the door on the south face.
    objects_l[bot][door_col] = door_char


def _carve_track(floor_ll, objects_l, pts, rng):
    """Beat a worn 1-tile dirt track between successive waypoints, with a
    little per-step jitter so it staircases and wobbles instead of ruling
    a straight line. Only plain grass converts (g -> d): river, corn
    cover, trees, walls, roofs, bridge planks and doors are all left
    alone -- so a track can never punch through water or a building, it
    simply fades out where it runs into the corn and stops at a wall."""
    h, w = len(floor_ll), len(floor_ll[0])

    def carve(tx, ty):
        if (0 <= ty < h and 0 <= tx < w
                and objects_l[ty][tx] == "." and floor_ll[ty][tx] == "g"):
            floor_ll[ty][tx] = "d"

    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        x, y = x0, y0
        carve(x, y)
        guard = 0
        while (x, y) != (x1, y1) and guard < 4 * (w + h):
            guard += 1
            dx = (x1 > x) - (x1 < x)
            dy = (y1 > y) - (y1 < y)
            if dx and (not dy or abs(x1 - x) >= abs(y1 - y)) and rng.random() < 0.85:
                x += dx
            elif dy:
                y += dy
            else:
                x += dx
            carve(x, y)
            if rng.random() < 0.30:                  # perpendicular fray -> 2-wide wobble
                if dx:
                    carve(x, y + (1 if rng.random() < 0.5 else -1))
                else:
                    carve(x + (1 if rng.random() < 0.5 else -1), y)


def build_mistlands():
    w = 100
    h = 100
    river_cols = (32, 33, 34)
    bridge_rows = (23, 24, 25, 26)
    floor_rows = []
    for ty in range(h):
        row = []
        for tx in range(w):
            if tx in river_cols:
                if ty in bridge_rows:
                    row.append("g")        # walkable grass under bridge
                else:
                    row.append("~")        # river water (solid)
            else:
                row.append("g")
        floor_rows.append("".join(row))

    # Walkable corn-cover patches scattered across the banks. The ':'
    # tile passively hides the player (Game flips player.hidden to
    # "corn" while they stand on it), turning the open mistlands into a
    # field with cover lanes to sneak between the buildings past the
    # roaming cult -- the way the cornfields do. Stamped only on open
    # grass, clear of the river, the buildings, the car/cauldron, and
    # the spawn tiles.
    corn_patches = [
        (16, 18, 28, 30), (3, 35, 14, 47), (18, 52, 29, 64), (3, 70, 12, 78),
        (40, 14, 52, 27), (60, 30, 74, 44), (38, 60, 49, 74), (74, 50, 86, 63),
    ]
    floor_rows = [list(r) for r in floor_rows]
    for (pl, pt, pr, pb) in corn_patches:
        cxm = (pl + pr) / 2.0
        cym = (pt + pb) / 2.0
        rxr = (pr - pl) / 2.0 + 1.0
        ryr = (pb - pt) / 2.0 + 1.0
        # Elliptical falloff + hash noise so the patch is an organic
        # blob with a ragged edge, not a clean rectangle on the grid.
        for ty in range(pt - 1, pb + 2):
            for tx in range(pl - 1, pr + 2):
                if not (0 <= ty < h and 0 <= tx < w):
                    continue
                if floor_rows[ty][tx] != "g":
                    continue
                nx = (tx - cxm) / rxr
                ny = (ty - cym) / ryr
                d = nx * nx + ny * ny
                hsh = ((tx * 73856093) ^ (ty * 19349663)) % 100
                if d <= 0.62 or (d <= 1.1 and hsh < 52):
                    floor_rows[ty][tx] = ":"
    floor_rows = ["".join(r) for r in floor_rows]

    objects_l = []
    for ty in range(h):
        row = ["."] * w
        if ty == 0 or ty == h - 1:
            row = ["T"] * w
            for cx in river_cols:
                row[cx] = "."
        else:
            row[0] = "T"
            row[-1] = "T"
        if ty in bridge_rows:
            for cx in river_cols:
                row[cx] = "$"
        objects_l.append(row)

    # 3-wide opening to the village/farm along the east edge -- rows
    # 6, 7, 8.
    for ry in (6, 7, 8):
        objects_l[ry][w - 1] = "4"

    # ---- Scattered buildings ----
    # Same footprints (7w x 6h) for visual consistency. Each has its
    # door on the south face. Coordinates picked so:
    #   * Church (m) is the NORTH-WEST anchor.
    #   * Sheriff (y) is mid-south on the WEST bank.
    #   * Farmhouse (o) is deep south on the WEST bank.
    #   * Shop (D), Kid's House (J), Barn (n) are spread middle-to-
    #     south on the EAST bank, walking distance apart.
    # Door cols are stored so the door-side spawn in the building
    # interior maps back to the mistlands tile one south of the door.
    # Church (NORTH-WEST). Footprint cols 4..10 rows 4..9. Door at col 7.
    church_left, church_right = 4, 10
    church_top, church_bot = 4, 9
    church_door = 7
    _stamp_building(objects_l, church_left, church_right,
                    church_top, church_bot, "m", church_door)

    # Sheriff (SOUTH-WEST upper). Footprint cols 4..10 rows 60..65.
    sheriff_left, sheriff_right = 4, 10
    sheriff_top, sheriff_bot = 60, 65
    sheriff_door = 7
    _stamp_building(objects_l, sheriff_left, sheriff_right,
                    sheriff_top, sheriff_bot, "y", sheriff_door)

    # Farmhouse (SOUTH-WEST lower). Footprint cols 4..10 rows 88..93.
    farm_left, farm_right = 4, 10
    farm_top, farm_bot = 88, 93
    farm_door = 7
    _stamp_building(objects_l, farm_left, farm_right,
                    farm_top, farm_bot, "o", farm_door)
    # A lean-to shed bolted onto the farmhouse's east wall (cols 10-13,
    # rows 90-93, no door -- a closed store). A separate roof region, so
    # it gets its own small gable beside the house: the footprint stops
    # reading as one clean rectangle and gains an attached outbuilding.
    for cx in range(10, 14):
        objects_l[90][cx] = "W"
        objects_l[93][cx] = "W"
    for ry in range(91, 93):
        objects_l[ry][10] = "W"
        objects_l[ry][13] = "W"
        for cx in range(11, 13):
            objects_l[ry][cx] = "r"

    # Shop (EAST middle). Footprint cols 50..56 rows 55..60.
    shop_left, shop_right = 50, 56
    shop_top, shop_bot = 55, 60
    shop_door = 53
    _stamp_building(objects_l, shop_left, shop_right,
                    shop_top, shop_bot, "D", shop_door)

    # Kid's house (EAST middle-south). Footprint cols 65..71 rows 65..70.
    kid_left, kid_right = 65, 71
    kid_top, kid_bot = 65, 70
    kid_door = 68
    _stamp_building(objects_l, kid_left, kid_right,
                    kid_top, kid_bot, "J", kid_door)

    # Barn (EAST deep south). Footprint cols 80..86 rows 75..80.
    barn_left, barn_right = 80, 86
    barn_top, barn_bot = 75, 80
    barn_door = 83
    _stamp_building(objects_l, barn_left, barn_right,
                    barn_top, barn_bot, "n", barn_door)

    # Schoolhouse (EAST middle-north). The old town street's schoolhouse,
    # now standing on the open bank with the rest. Footprint cols 60..66
    # rows 48..53, door at col 63.
    school_left, school_right = 60, 66
    school_top, school_bot = 48, 53
    school_door = 63
    _stamp_building(objects_l, school_left, school_right,
                    school_top, school_bot, "B", school_door)

    # Thicken + fray the enclosing forest: a ragged second/third rank of
    # trees just inside the single-tile border, so the wall of woods has
    # depth and its inner line wavers instead of ruling straight (you
    # can't see out, and you can't tell how deep it goes). Skips the exit
    # gaps + border spawns, and never overwrites a building.
    def _border_protected(tx, ty):
        if ty in (6, 7, 8) and tx >= w - 4:
            return True                                  # east road exit + spawn
        if tx in (49, 50, 51) and ty <= 3:
            return True                                  # north passage + river_crossing spawn
        if tx in (39, 40, 41) and ty <= 3:
            return True                                  # cornfield_maze spawn
        if tx <= 2 and 83 <= ty <= 87:
            return True                                  # alter spawn
        if tx in river_cols and (ty <= 3 or ty >= h - 4):
            return True                                  # river mouths
        return False

    forest = random.Random(53)
    for ty in range(2, h - 2):                           # west + east ranks
        for edge_tx, step in ((1, 1), (w - 2, -1)):
            for dd in range(forest.randint(0, 2)):
                tx = edge_tx + step * dd
                if objects_l[ty][tx] == "." and not _border_protected(tx, ty):
                    objects_l[ty][tx] = "T"
    for tx in range(2, w - 2):                           # north + south ranks
        for edge_ty, step in ((1, 1), (h - 2, -1)):
            for dd in range(forest.randint(0, 2)):
                ty = edge_ty + step * dd
                if objects_l[ty][tx] == "." and not _border_protected(tx, ty):
                    objects_l[ty][tx] = "T"

    # (Church graveyard headstones are placed as crooked decorations
    # below, near the Preacher -- not grid-locked rock tiles.)

    # Lit windows flanking a few doors (the 'i' tile glows + a dark
    # figure passes behind the glass on its own clock). Someone's still
    # inside -- and something walks past the window when you're not
    # looking straight at it. South walls so they face the approach.
    for (wy, wx) in [(53, 61), (53, 65),     # schoolhouse
                     (60, 51), (60, 55),     # store
                     (70, 66), (70, 70)]:    # kid's house
        objects_l[wy][wx] = "i"

    # ---- Worn dirt tracks ----
    # The townsfolk and the cult have beaten paths across the field over
    # the years, linking the village entry and the river bridge to the
    # scattered buildings. They give the composed emptiness leading lines
    # to read by -- and they fade out where they run into the corn rather
    # than cutting through the cover. Tracks meet the bridge ends (the
    # river is the one crossing); the planks themselves stay planks.
    floor_ll = [list(r) for r in floor_rows]
    trk = random.Random(7)
    # East bank: village entry (east edge) -> east end of the bridge.
    _carve_track(floor_ll, objects_l,
                 [(w - 2, 7), (70, 10), (52, 18), (36, 22), (35, 24)], trk)
    # East-bank spine running south down the open lane between the
    # west-side and east-side buildings, with short spurs to each door.
    _carve_track(floor_ll, objects_l, [(52, 18), (58, 34), (58, 72)], trk)
    _carve_track(floor_ll, objects_l, [(58, 58), (54, 60), (53, 61)], trk)   # -> Shop door
    _carve_track(floor_ll, objects_l, [(58, 70), (64, 71), (68, 71)], trk)   # -> Kid's door
    _carve_track(floor_ll, objects_l, [(58, 52), (61, 53), (63, 54)], trk)   # -> Schoolhouse door
    _carve_track(floor_ll, objects_l,
                 [(58, 72), (70, 77), (80, 80), (83, 81)], trk)              # -> Barn door
    # West bank: bridge west end -> Church (north) and Sheriff +
    # Farmhouse (south), plus a spur toward the cauldron clearing.
    _carve_track(floor_ll, objects_l,
                 [(31, 24), (16, 16), (9, 11), (7, 10)], trk)                # -> Church door
    _carve_track(floor_ll, objects_l,
                 [(31, 24), (18, 44), (9, 58), (7, 66)], trk)                # -> Sheriff door
    _carve_track(floor_ll, objects_l, [(7, 66), (7, 80), (7, 94)], trk)      # -> Farmhouse door
    _carve_track(floor_ll, objects_l, [(7, 82), (11, 81), (14, 80)], trk)    # -> cauldron entrance
    # A cult path worn off the east lane out across the empty field to
    # the standing stones -- a leading line composing the void, fading
    # where it crosses the corn.
    _carve_track(floor_ll, objects_l,
                 [(58, 40), (66, 37), (74, 35), (78, 34)], trk)              # -> standing stones

    # ---- Marsh ----
    # Sodden low ground churned into mud + standing water, stamped as
    # organic blobs across the open fields (elliptical falloff + hash
    # noise so the edges are ragged). Only plain grass converts, so the
    # river, corn cover, worn tracks and buildings are left intact -- the
    # marsh just fills the open plain so it reads as wet mistlands.
    for (pl, pt, pr, pb) in [(16, 46, 26, 58), (40, 30, 50, 42),
                             (20, 84, 34, 94), (62, 82, 76, 92),
                             (44, 60, 56, 70)]:
        cxm, cym = (pl + pr) / 2.0, (pt + pb) / 2.0
        rxr, ryr = (pr - pl) / 2.0 + 1.0, (pb - pt) / 2.0 + 1.0
        for ty2 in range(pt - 1, pb + 2):
            for tx2 in range(pl - 1, pr + 2):
                if not (0 <= ty2 < h and 0 <= tx2 < w):
                    continue
                if floor_ll[ty2][tx2] != "g":
                    continue
                nx = (tx2 - cxm) / rxr
                ny = (ty2 - cym) / ryr
                dd = nx * nx + ny * ny
                hsh = ((tx2 * 73856093) ^ (ty2 * 19349663)) % 100
                if dd <= 0.6 or (dd <= 1.1 and hsh < 48):
                    floor_ll[ty2][tx2] = ";"
    floor_rows = ["".join(r) for r in floor_ll]

    objects = ["".join(r) for r in objects_l]

    sc = Scene("mistlands", floor_rows, objects, music="wind")
    # Village re-entry, the cauldron-clearing entrance, and the six
    # scattered building exits. Each building's door tile (m, y, o,
    # D, J, n) wires straight into its old interior scene -- the
    # buildings moved, but their interiors didn't.
    sc.add_exit("4", "village", "from_mistlands")
    sc.add_exit("a", "river_crossing", "from_mistlands")
    sc.add_exit("m", "old_man_house",     "from_mistlands")  # Church
    sc.add_exit("o", "haunted_house",     "from_mistlands")  # Farmhouse
    sc.add_exit("J", "kid_house",         "from_mistlands")  # Kid
    sc.add_exit("n", "barn",              "from_mistlands")  # Barn
    # The town has come apart into Brimley's fog: the Sheriff's office,
    # General Store and Schoolhouse stand out here on the bank now, all
    # enterable, their interiors returning to this scene.
    sc.add_exit("y", "fisherman_cottage", "from_mistlands")  # Sheriff's office
    sc.add_exit("D", "shop",              "from_mistlands")  # General Store
    sc.add_exit("B", "schoolhouse",       "from_mistlands")  # Schoolhouse
    cauldron_tx, cauldron_ty = 15, 80
    objects_list = [list(r) for r in objects]
    objects_list[cauldron_ty][cauldron_tx] = "j"
    # North passage to the river_crossing -- a single tile carved
    # into the north tree line, west of the river.
    objects_list[0][50] = "a"
    # Hand-authored loot crates. Both inside the playable area; the
    # west-bank crate sits near the cauldron path, the east-bank
    # crate sits just west of the relocated barn footprint.
    objects_list[78][14] = "K"
    objects_list[78][78] = "K"
    sc.objects = objects_list
    sc.add_exit("j", "void_boss", "from_mistlands")
    sc.set_spawn("default", w - 2, 7)
    sc.set_spawn("from_village", w - 2, 7)
    sc.set_spawn("from_mist_house", 7, church_bot + 1)
    sc.set_spawn("from_alter", 1, 85)
    sc.set_spawn("from_river_crossing", 50, 1)
    # Cornfield maze pushes north and emerges into the mistlands
    # a few tiles west of the river crossing -- the maze led you
    # somewhere wrong. Spawn point on the open north band.
    sc.set_spawn("from_cornfield_maze", 40, 1)
    # Returning from the clearing -- spawn one tile EAST of the j
    # tile so the player doesn't auto-retrigger.
    sc.set_spawn("from_clearing", cauldron_tx + 1, cauldron_ty)
    # Returning from each scattered building lands the player one
    # tile south of the door so they don't immediately re-enter.
    sc.set_spawn("from_old_man_house",     church_door,  church_bot + 1)
    sc.set_spawn("from_fisherman_cottage", sheriff_door, sheriff_bot + 1)
    sc.set_spawn("from_haunted_house",     farm_door,    farm_bot + 1)
    sc.set_spawn("from_shop",              shop_door,    shop_bot + 1)
    sc.set_spawn("from_kid_house",         kid_door,     kid_bot + 1)
    sc.set_spawn("from_barn",              barn_door,    barn_bot + 1)
    sc.set_spawn("from_school",            school_door,  school_bot + 1)
    # The farm's old town road now drops you into the heart of Brimley,
    # among the scattered buildings on the east bank.
    sc.set_spawn("from_village_road",      58, 30)

    # Ambience -- crows and grass tufts. The banks once sat bare west
    # of the river (the dread of no cover); they now carry the walkable
    # corn-cover patches stamped above, so the player can cross hidden.
    sc.add_decoration(Decoration(60 * TILE + 16, 12 * TILE + 16, "crow"))
    sc.add_decoration(Decoration(72 * TILE + 16, 40 * TILE + 16, "crow"))
    sc.add_decoration(Decoration(85 * TILE + 16, 70 * TILE + 16, "crow"))
    # Creepy bank dressing -- creepy_trees, hanging figures, dead
    # crows. The cauldron-clearing entrance at (15, 80) gets its own
    # creepy_tree so the player can SPOT it among the empty bank.
    # A bloody-handprint trail leads east-to-west across the bank
    # from the river to the entrance, marking the cult's path.
    sc.add_decoration(Decoration(50 * TILE + 16, 25 * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(78 * TILE + 16, 55 * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(68 * TILE + 16, 85 * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(55 * TILE + 16, 35 * TILE + 16, "hanging_figure"))
    sc.add_decoration(Decoration(82 * TILE + 16, 65 * TILE + 16, "hanging_figure"))
    sc.add_decoration(Decoration(63 * TILE + 16, 45 * TILE + 16, "dead_crow"))
    sc.add_decoration(Decoration(74 * TILE + 16, 78 * TILE + 16, "dead_crow"))
    # The cauldron-entrance threshold -- creepy_tree on the j tile
    # itself, a single bloody handprint at the threshold, and a
    # candle melted to a stone at the foot. Just enough cue for
    # the player to recognise the route without a blood trail
    # that telegraphs the discovery from the river.
    sc.add_decoration(Decoration(cauldron_tx * TILE + 16,
                                 cauldron_ty * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration((cauldron_tx + 1) * TILE + 16,
                                 cauldron_ty * TILE + 16,
                                 "bloody_handprint"))
    sc.add_decoration(Decoration((cauldron_tx + 1) * TILE + 16,
                                 cauldron_ty * TILE + 8, "candle"))
    # Marks scattered through the bank, placed near the buildings.
    # West-bank marks
    sc.add_decoration(Decoration(2 * TILE + 24, 62 * TILE + 16,
                                 "watching_wound", size="small")) # near sheriff
    sc.add_decoration(Decoration(2 * TILE + 24, 92 * TILE + 16,
                                 "watching_wound", size="small")) # farmhouse rim
    # East-bank marks
    sc.add_decoration(Decoration(48 * TILE + 16, 57 * TILE + 16,
                                 "watching_wound", size="small")) # near shop
    sc.add_decoration(Decoration(78 * TILE + 16, 77 * TILE + 16,
                                 "watching_wound", size="small")) # near barn
    # Original mid-bank scatter
    sc.add_decoration(Decoration(75 * TILE + 16, 75 * TILE + 16,
                                 "phantom_mark"))
    for tx, ty in [(50, 50), (60, 30), (70, 60), (80, 40), (90, 80),
                   (55, 80), (75, 20), (65, 75)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "grass_tuft"))
    # Body for the corn-cover patches: tufts scattered through each so
    # the ':' floor reads as a field, plus a few creepy accents now
    # that the banks aren't bare.
    rng_corn = random.Random(4242)
    for (pl, pt, pr, pb) in corn_patches:
        for _ in range(max(5, (pr - pl) * (pb - pt) // 7)):
            gx = rng_corn.randint(pl, pr) * TILE + rng_corn.randint(2, 28)
            gy = rng_corn.randint(pt, pb) * TILE + rng_corn.randint(2, 28)
            sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    for tx, ty, kind in [(22, 25, "dead_crow"), (8, 42, "creepy_tree"),
                         (24, 58, "hanging_figure"), (46, 20, "creepy_tree"),
                         (66, 38, "dead_crow"), (80, 57, "creepy_tree")]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16, kind))
    for tx, ty in [(44, 68), (40, 30), (12, 74)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "watching_wound", size="small"))

    # ---- Brimley's people ----
    # The town's residents, stranded here with everyone else. None of
    # them are cult -- but you can't be sealed inside a folding town
    # under the King's eye and stay whole. Innocent, and coming apart at
    # the edges: denial, time-loop confusion, a child saying the quiet
    # part out loud.
    def _resident(tx, ty, name, kind, pages, movement="wander",
                  voice="blip_mid", radius=52):
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16, name, kind,
                       dialogue_fn=_brimley_voice(pages, voice),
                       movement=movement, radius=radius))

    _resident(55, 62, "Hettie", "shopkeep", [
        "Still open. Always open -- have you noticed the shelves don't empty anymore?",
        "No deliveries in... a while, now. But we manage. We always manage.",
        "[c=dim]I keep the lights on so they know someone's keeping the lights on.[/c]",
    ], movement="idle")
    _resident(58, 44, "Old Pell", "old", [
        "Cold came in early this year. Came in early last year, too.",
        "Stopped marking the calendar. The days just fold back on themselves.",
        "[c=dim]You're new. We don't get new. Nobody gets in. Nobody gets--[/c]",
    ], voice="blip_low")
    _resident(70, 72, "Mrs. Calder", "mom", [
        "My husband walked out to the highway to flag down help. Tuesday, that was.",
        "He'll be back. I set his plate every night. Every night.",
        "[c=dim]Some nights I hear the door. I've stopped getting up to check.[/c]",
    ], movement="idle")
    _resident(37, 28, "Royce", "fisherman", [
        "Drove the river road to the county line. Two hours out. Came right back into Brimley.",
        "Tried it on foot. Same. The corn just hands you back where you started.",
        "[c=dim]You came IN. How did you come IN? ...Tell me how you came in.[/c]",
    ])
    _resident(61, 56, "the Tisdale boy", "kid", [
        "School's still on. The teacher doesn't blink. I counted to a hundred.",
        "There's a lady in yellow at the back of the field. She waves. You shouldn't wave back.",
        "[c=dim]Mara waved back.[/c]",
    ], voice="blip_kid", radius=40)
    _resident(9, 67, "Garrick", "old", [
        "You're asking questions. Folks who ask questions go quiet. Real quiet.",
        "The Sheriff'll smile at you. Don't let it talk you into staying for supper.",
        "[c=dim]Go on home, son. ...Oh. Right. None of us can.[/c]",
    ])
    sc.add_npc(NPC(45 * TILE + 16, 38 * TILE + 16, "A woman", "mom",
                   dialogue_fn=_brimley_voice([
                       "[c=dim]Hello.[/c]",
                       "[c=dim]You'll like it here. Everyone does, eventually.[/c]",
                       "[c=dim]It's easier once you stop trying the doors.[/c]",
                   ], "blip_soft"),
                   movement="watch"))

    # Run-down + cult presence among the buildings: the Yellow Sign
    # worked into the open ground, dead crows at the doorsteps, a bloody
    # handprint by the schoolhouse. The cult doesn't hide out here.
    sc.add_decoration(Decoration(60 * TILE + 16, 57 * TILE + 16, "yellow_sign"))
    sc.add_decoration(Decoration(52 * TILE + 20, 52 * TILE + 16, "yellow_sign"))
    sc.add_decoration(Decoration(54 * TILE + 16, 63 * TILE + 16, "dead_crow"))
    sc.add_decoration(Decoration(69 * TILE + 16, 73 * TILE + 16, "dead_crow"))
    sc.add_decoration(Decoration(63 * TILE + 16, 55 * TILE + 8, "bloody_handprint"))
    sc.add_decoration(Decoration(72 * TILE + 16, 55 * TILE + 16, "hanging_figure"))

    # ---- The loop, made visible ----
    # The residents say they can't leave; the town shows it. A payphone
    # that won't connect; missing-person flyers (one of them Mara);
    # a clock stopped dead and a calendar clawed with tally-marks where
    # the days fold back; the truck that drove for the county line and
    # was handed back, nosed dead into the east tree line; and Mrs.
    # Calder's plate, set for a husband who walked out to the highway.
    sc.add_decoration(Decoration(58 * TILE + 16, 62 * TILE + 16, "payphone"))
    sc._payphone_pos = (58 * TILE + 16, 62 * TILE + 16)
    sc.add_decoration(Decoration(61 * TILE + 16, 55 * TILE + 16, "missing_flyer"))  # Mara
    sc.add_decoration(Decoration(52 * TILE + 16, 61 * TILE + 16, "missing_flyer"))
    sc.add_decoration(Decoration(40 * TILE + 16, 27 * TILE + 16, "missing_flyer"))
    # The calendar, every day crossed off the same, nailed to the
    # schoolhouse wall beside the door (Old Pell: "the days fold back").
    sc.add_decoration(Decoration(62 * TILE + 16, 53 * TILE + 16, "calendar"))
    sc.add_decoration(Decoration(95 * TILE + 16, 55 * TILE + 16, "pickup_truck"))
    # A body face-down in the river, well south of the bridge -- the
    # water keeps what it takes.
    sc.add_decoration(Decoration(33 * TILE + 16, 45 * TILE + 16, "drowned_body"))
    # Mrs. Calder's table, laid out in the open by the kid's house: two
    # settings (hers, and his -- set every night), a candle burned down,
    # and his chair knocked over where he got up and never came back.
    # (The table itself is a solid 't' tile placed below.)
    sc.add_decoration(Decoration(71 * TILE + 10, 72 * TILE + 12, "place_setting"))
    sc.add_decoration(Decoration(71 * TILE + 24, 72 * TILE + 12, "place_setting"))
    sc.add_decoration(Decoration(71 * TILE + 16, 72 * TILE + 2, "candle"))
    sc.add_decoration(Decoration(71 * TILE + 28, 74 * TILE + 12, "overturned_chair"))

    # ---- The churchyard -- the too-even graves of the vanished ----
    # Crooked headstones in two rows: the uncanny rows-of-the-vanished,
    # each leaning its own way a few px off the lattice. (The Preacher's
    # body is no longer here -- evidence #4 is now found in his own church,
    # gutted for naming the cult; see scenes/villager_houses.py.)
    hs = random.Random(91)
    for ry_ in (12, 14):
        for cx_ in (4, 6, 8, 10):
            sc.add_decoration(Decoration(
                cx_ * TILE + 16 + hs.randint(-6, 6),
                ry_ * TILE + 16 + hs.randint(-4, 4),
                "headstone", seed=hs.randint(0, 9999)))
    sc.add_decoration(Decoration(6 * TILE + 16, 12 * TILE + 6, "dead_crow"))
    sc.add_decoration(Decoration(9 * TILE + 16, 14 * TILE + 6, "crow"))

    # ---- Light is the mood ----
    # A guttering lamppost in the yard just off each occupied door (these
    # 'lantern' decos are full lampposts -- standing them ON the door read
    # as a lamppost blocking it, so they sit one tile SW, on open ground,
    # throwing their pool across the threshold). A row of lit thresholds:
    # the town still keeping itself lit for someone. Light is the mercy.
    for (lx, ly) in [(7, 9), (7, 65), (7, 93),        # church, sheriff, farmhouse
                     (53, 60), (63, 53), (68, 70), (83, 80)]:  # shop, school, kid, barn
        sc.add_decoration(Decoration((lx - 1) * TILE + 20,
                                     (ly + 1) * TILE + 16, "lantern"))
    # The bridge: a single lantern on the exposed crossing -- the one
    # light, and the one place the river leaves you with no cover. A
    # creepy_tree on each bank gives a held-breath pocket before and
    # after the open span (hide-spots wired below).
    sc.add_decoration(Decoration(33 * TILE + 16, 25 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(37 * TILE + 16, 21 * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(29 * TILE + 16, 27 * TILE + 16, "creepy_tree"))

    # Break the tidy boxes: a tipped wheelbarrow by the store, a dead
    # filling-station pump stranded on the lane, mud tracked off the path.
    sc.add_decoration(Decoration(49 * TILE + 16, 59 * TILE + 16, "wheelbarrow"))
    sc.add_decoration(Decoration(60 * TILE + 16, 40 * TILE + 16, "gas_pump"))
    sc.add_decoration(Decoration(58 * TILE + 16, 47 * TILE + 16, "mud_footprint"))

    # Weeds reclaiming the foundations -- tufts crowding the ground just
    # OUTSIDE the walls (south footing + the east/west bases), so the
    # wall meets the ground in an overgrown line, never buried in the
    # wall itself. The town is being taken back.
    weeds = random.Random(317)

    def _weed(px, py):                           # only on open ground, never in a wall
        tx, ty = int(px // TILE), int(py // TILE)
        if 0 <= ty < h and 0 <= tx < w and sc.objects[ty][tx] == ".":
            sc.add_decoration(Decoration(px, py, "grass_tuft"))

    for (bl, br, bt, bb) in [(4, 10, 4, 9), (4, 10, 60, 65), (4, 10, 88, 93),
                             (50, 56, 55, 60), (60, 66, 48, 53),
                             (65, 71, 65, 70), (80, 86, 75, 80)]:
        for _ in range(6):                       # front footing, on the ground below
            _weed(weeds.randint(bl, br) * TILE + weeds.randint(2, 28),
                  (bb + 1) * TILE + weeds.randint(2, 16))
        for _ in range(4):                       # hugging the outside of the side walls
            ry2 = weeds.randint(bt, bb) * TILE + weeds.randint(2, 28)
            _weed((bl - 1) * TILE + weeds.randint(16, 28), ry2)
            _weed((br + 1) * TILE + weeds.randint(2, 14), ry2)

    # A dead grove on the bare west bank -- a stand of leafless trees out
    # in the open emptiness, a focal dread that offers no cover.
    for (gx, gy) in [(17, 39), (19, 41), (16, 43), (20, 44), (18, 46), (15, 41)]:
        sc.add_decoration(Decoration(gx * TILE + 16, gy * TILE + 16, "creepy_tree"))
    # A cult standing-stone ring in the open north-east field, a Yellow
    # Sign cut into the ground at its centre, lit by two braziers -- a
    # warm, watched focal point out in the dark.
    for (px, py) in [(77, 31), (81, 31), (79, 30),
                     (76, 34), (82, 34), (79, 36)]:
        sc.add_decoration(Decoration(px * TILE + 16, py * TILE + 16, "pillar"))
    sc.add_decoration(Decoration(79 * TILE + 16, 33 * TILE + 16, "yellow_sign"))
    sc.add_decoration(Decoration(77 * TILE + 16, 33 * TILE + 16, "brazier"))
    sc.add_decoration(Decoration(81 * TILE + 16, 33 * TILE + 16, "brazier"))
    # The church steeple -- the one tall thing for miles, a landmark to
    # orient by, rising over the roof into the treeline.
    sc.add_decoration(Decoration(7 * TILE + 16, 7 * TILE + 16, "steeple"))
    # A brazier marking the cauldron-clearing threshold.
    sc.add_decoration(Decoration(13 * TILE + 16, 80 * TILE + 16, "brazier"))
    # A murder of crows posted along the treeline, watching.
    for (cx, cy) in [(2, 22), (2, 71), (50, 2), (88, 31), (97, 60), (41, 97)]:
        sc.add_decoration(Decoration(cx * TILE + 16, cy * TILE + 16,
                                     "dead_crow" if (cx + cy) % 2 else "crow"))

    # ---- Mist + marsh wisps ----
    # Low fog clinging to the water and pooling over the marsh, and cold
    # will-o'-wisps drifting the bog -- the "mist" the lands are named
    # for, localized over the wet ground beneath the global haze.
    for (mtx, mty, mw, mh) in [(33, 36, 90, 64), (33, 58, 90, 72),
                               (33, 80, 90, 64),          # along the river
                               (21, 52, 112, 72), (45, 36, 104, 64),
                               (27, 89, 120, 72), (69, 87, 112, 72),
                               (50, 65, 104, 64)]:         # over the marsh
        sc.add_decoration(Decoration(mtx * TILE + 16, mty * TILE + 16,
                                     "mist", w=mw, h=mh))
    for (wtx, wty) in [(20, 53), (23, 50), (46, 37), (28, 90),
                       (70, 88), (50, 66)]:
        sc.add_decoration(Decoration(wtx * TILE + 16, wty * TILE + 16, "wisp"))

    # Ambient sky + wind: distant flocks drifting over, dead leaves
    # tumbling across the fields -- the world is never quite still.
    for (ftx, fty) in [(40, 15), (70, 48), (24, 68)]:
        sc.add_decoration(Decoration(ftx * TILE + 16, fty * TILE + 16, "flock"))
    for (ltx, lty) in [(45, 40), (55, 52), (30, 60), (62, 62),
                       (20, 40), (52, 80), (75, 42), (36, 30)]:
        sc.add_decoration(Decoration(ltx * TILE + 16, lty * TILE + 16, "leaves"))

    # Hide spots colocated with VISIBLE cover so the prompt always
    # matches what the player can see. Each entry sits on top of a
    # grass-tuft / watching-eye / dead-tree decoration on the east
    # bank; the empty west bank deliberately offers no cover.
    sc.hide_spots = [
        (50 * TILE + 16, 50 * TILE + 16, "behind"),  # eye + tuft
        (60 * TILE + 16, 30 * TILE + 16, "behind"),  # tuft
        (70 * TILE + 16, 60 * TILE + 16, "behind"),  # tuft
        (75 * TILE + 16, 75 * TILE + 16, "behind"),  # eye + tuft
        (55 * TILE + 16, 80 * TILE + 16, "behind"),  # tuft
        (80 * TILE + 16, 40 * TILE + 16, "behind"),  # tuft
        (37 * TILE + 16, 21 * TILE + 16, "behind"),  # creepy_tree, bridge east pocket
        (29 * TILE + 16, 27 * TILE + 16, "behind"),  # creepy_tree, bridge west pocket
    ]

    # Player's car: parked on the east bank, visible from the
    # village entry. Reaching it with car_keys triggers the escape
    # ending (the car was previously at the diner; moved here so
    # the mistlands river area IS the escape geography). 3-tile
    # footprint of solid 'X' tiles under the sprite so collision
    # matches the visual.
    car_tx, car_ty = 85, 8
    car_x = car_tx * TILE + 16
    car_y = car_ty * TILE + 16
    sc.add_decoration(Decoration(car_x, car_y, "player_car"))
    sc._car_pos = (car_x, car_y)
    objects_list = [list(r) for r in sc.objects]
    for cx in (car_tx - 1, car_tx, car_tx + 1):
        if 0 <= cx < sc.w:
            objects_list[car_ty][cx] = "X"
    # The dead pickup is a big hulk -- solid tiles under its length so
    # the player can't walk through it (decoration at tile 95,55).
    for cx in (93, 94, 95, 96):
        if 0 <= cx < sc.w:
            objects_list[55][cx] = "X"
    # Mrs. Calder's outdoor table (solid), her settings drawn on top.
    objects_list[72][71] = "t"
    sc.objects = objects_list
    # Hide spot beside the car (cover for a brief breather between
    # village and west bank).
    sc.hide_spots.append((car_x, (car_ty + 1) * TILE + 16, "behind"))

    def _mistlands_interact(game):
        cx, cy = sc._car_pos
        if (abs(game.player.x - cx) < 40
                and abs(game.player.y - cy) < 40):
            keys = game.player.inventory.has("car_keys")
            sign = game.player.inventory.has("sigil_rubbing")
            if keys and sign and hasattr(game, "_begin_car_escape"):
                game._begin_car_escape()          # the Sign breaks the fold
                return
            if keys:
                # The fold holds: without the Sign the engine never catches.
                game.audio.play("door_locked", 0.6)
                game.show_notice("The engine turns over. And over. "
                                 "It will not catch.")
                return
            game.audio.play("door_locked", 0.6)
            game.show_notice("Locked. The keys are with the innkeeper.")
            return
        # The payphone -- it won't dial out. The line is never dead,
        # though; something is always already on it.
        px, py = sc._payphone_pos
        if abs(game.player.x - px) < 40 and abs(game.player.y - py) < 40:
            game.audio.play("blip_low", 0.5)
            line = [
                "No dial tone. No ringing. The line is open to something.",
                "[c=dim]Far down it, under the hiss, you hear your own "
                "voice -- already mid-sentence.[/c]",
            ]
            game.dialog.show(line, speaker="", voice="blip_soft",
                             portrait="narrator")
    sc.on_interact_fn = _mistlands_interact
    return sc
