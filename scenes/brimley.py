"""The brimley -- 100x100 plain west of the Clerk's farm,
split roughly 1/3 / 2/3 by a north-south river. A planked bridge
crosses near its north end (rows 23-26 x cols 32-34). THRESHOLD
rework: the village's six buildings have been scattered across
this map. Three sit on the west bank (Church north, Sheriff +
Farmhouse south); three sit middle-south on the east bank (Shop,
Kid's House, Barn). Player walks the bank to find them. The
burn clearing and player's car are still here.

Atmosphere: black haze drawn by Game._draw_brimley_haze, ambient
'wind' track played by music='wind'."""
import math
import random
from constants import TILE
from entities.decoration import Decoration
from entities.npc import NPC
from .base import Scene, dead_cars
from .dialogue import (_evidence, preacher_body_examine, chorus_dialogue,
                       PELL_CONVO, CALDER_CONVO, ROYCE_CONVO, GARRICK_CONVO)


def _brimley_on_enter(game, scene):
    """Lay out the doomed Preacher's remains on the riverbank (2026-07
    rework: he leaves his church to talk his flock home and is found
    here, never on his own floor). Rebuilt every load after the doom."""
    if not game.save.flag("preacher_doomed"):
        return
    bx, by = scene._preacher_bank_pos
    scene.add_decoration(Decoration(bx - 6, by + 9, "bloodstain"))
    scene.add_decoration(Decoration(bx + 9, by - 6, "gore"))
    scene.add_decoration(Decoration(bx, by, "body"))
    scene.add_npc(NPC(bx, by, "The Preacher", "_invisible",
                      voice="blip_soft", portrait="narrator",
                      dialogue_fn=preacher_body_examine,
                      movement="idle", solid=True, tag="preacher_body"))


def _brimley_update(game, scene, dt):
    """Finding the body counts on SIGHT, not only on the E-press: walking
    up on the remains sets `preacher_body_seen`, the flag Sheriff Vane's
    and Hettie's murder one-shots key on (they can never announce a
    killing the player hasn't found)."""
    if (game.save.flag("preacher_doomed")
            and not game.save.flag("preacher_body_seen")):
        bx, by = scene._preacher_bank_pos
        if (abs(game.player.x - bx) < 110
                and abs(game.player.y - by) < 110):
            game.save.set_flag("preacher_body_seen", True)


def _brimley_voice(pages, voice="blip_mid", fold=False, beats=None):
    """NPC dialogue_fn from a fixed page list. Speaker name + portrait are
    read off the NPC at call time so each resident speaks as themselves.
    `fold=True` marks a local who describes the fold (looping roads): the
    FIRST such conversation files the PI's fold note (Game._fold_mentioned,
    globally one-shot, so only the first speaker triggers it).

    Since the chorus moved onto the ask verb (dialogue.py chorus_dialogue
    + the *_CONVO data), the only remaining speaker here is the doorstep
    Hettie cameo; her real conversation lives in the shop.

    `beats` makes the town REACT to state (TODO #10): a list of
    (flag, predicate, beat_pages). On each talk the first beat whose
    predicate(game) holds and whose one-shot save flag is unset fires
    INSTEAD of the base pages (and sets its flag); afterwards the local
    falls back to their ambient loop. The world rot convert/mutate
    swap overwrites dialogue_fn at its stage, so each beat's window is
    the local's pre-turn stretch -- fired once, in it, or never."""
    def _fn(game, npc):
        portrait = getattr(npc, "portrait", None) or npc.sprite_kind
        for flag, pred, beat_pages in (beats or ()):
            if game.save.flag(flag):
                continue
            if pred(game):
                game.save.set_flag(flag, True)
                game.dialog.show(beat_pages, speaker=npc.name, voice=voice,
                                 portrait=portrait)
                # NB: the fold note is NOT filed here -- the beat pages
                # are their own subject (the preacher, the digging, the
                # plate); only the base pages carry the looping-roads
                # account the `fold` mark attributes to this speaker.
                return
        game.dialog.show(pages, speaker=npc.name, voice=voice,
                         portrait=portrait)
        if fold and hasattr(game, "_fold_mentioned"):
            game._fold_mentioned(npc.name)
    return _fn


def _stamp_building(objects_l, left, right, top, bot,
                     door_char, door_col):
    """Stamp a rectangular building footprint into objects_l. Outer
    perimeter is wall (W); interior is roof (r); a single door tile
    (door_char) is punched through the south face at door_col. Used
    by build_brimley for each scattered village building."""
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


def build_brimley():
    w = 100
    h = 100
    river_center_x = 33
    bridge_rows = (23, 24, 25, 26)
    # The river bends gently as it runs N-S. At each row the centre
    # offsets by a sine of the row index -- amplitude 2, two full cycles
    # over the 100 rows. The bridge rows are pinned to centre=33 so the
    # crossing stays where the original bridge planks were laid; the
    # bend interpolates back to centre across the rows on either side
    # of the bridge so there's no kink.
    def _river_cols(ty):
        if ty in bridge_rows:
            cx = river_center_x
        else:
            # Smooth blend back to centre within 4 rows of the bridge.
            dist_to_bridge = min(abs(ty - bridge_rows[0]),
                                  abs(ty - bridge_rows[-1]))
            sine = math.sin(ty * 0.13) * 2.0
            if dist_to_bridge < 4:
                sine *= dist_to_bridge / 4.0
            cx = int(round(river_center_x + sine))
        return (cx - 1, cx, cx + 1)
    floor_rows = []
    for ty in range(h):
        rc = _river_cols(ty)
        row = []
        for tx in range(w):
            if tx in rc:
                if ty in bridge_rows:
                    row.append("g")        # walkable grass under bridge
                else:
                    row.append("~")        # river water (solid)
            else:
                row.append("g")
        floor_rows.append("".join(row))
    # Keep the broader river_cols tuple for downstream code that needs a
    # max-span set (corn-patch protection, border-protection, etc.).
    river_cols = tuple(range(river_center_x - 3, river_center_x + 4))

    # Walkable corn-cover patches scattered across the banks. The ':'
    # tile passively hides the player (Game flips player.hidden to
    # "corn" while they stand on it), turning the open brimley into a
    # field with cover lanes to sneak between the buildings past the
    # roaming cult -- the way the cornfields do. Stamped only on open
    # grass, clear of the river, the buildings, the car/clearing, and
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

    # No hard perimeter wall any more. Brimley wraps on both axes, and
    # the border is treated below as a scattered, semi-permeable forest
    # band -- the player can walk into it, the wrap fires somewhere in
    # the middle, and the visual sameness across edges hides the
    # transition. Bridge planks at the river still get set explicitly.
    objects_l = []
    for ty in range(h):
        row = ["."] * w
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
    # interior maps back to the brimley tile one south of the door.
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
        # Road corridors poke through the 6-tile band cleanly so the
        # scattered forest doesn't tree over them. Each protected
        # range extends from the edge inward by BAND_DEPTH (6 tiles)
        # so the road keeps a clear visual line from the band into
        # the playable interior.
        if ty in (6, 7, 8) and tx >= w - 7:
            return True                                  # east road corridor
        if tx in (49, 50, 51) and ty <= 6:
            return True                                  # north river_crossing corridor
        if tx in (39, 40, 41) and ty <= 11:
            return True                                  # cornfield_maze corridor (clear through the northern lobe too)
        if tx in (95, 96, 97) and ty <= 6:
            return True                                  # gravel-road corridor
        if ty in (23, 24, 25) and (tx <= 6 or tx >= w - 7):
            return True                                  # fold-loop road both ends
        if tx in (93, 94, 95) and ty <= 25:
            return True                                  # entry + well -> main-road connector
        if tx in (47, 48, 49) and ty >= h - 7:
            return True                                  # south macro-loop exit
        if tx in (47, 48, 49) and ty <= 6:
            return True                                  # north macro-loop arrival
        if tx <= 6 and 83 <= ty <= 87:
            return True                                  # alter corridor
        if tx in river_cols and (ty <= 6 or ty >= h - 7):
            return True                                  # river mouths
        return False

    # Scattered forest BAND, not a wall. A 6-tile-deep zone around the
    # whole perimeter where trees are seeded probabilistically: high
    # density at the very edge, fading toward the interior. The player
    # can walk into the band, gets lost in the visual sameness, and
    # the wrap mechanic carries them to the opposite side (which looks
    # the same). Roads + building approaches stay clean via
    # _border_protected.
    BAND_DEPTH = 7
    # The scattered forest band is built later (after floor_ll has been
    # finalised) so the helper can stamp both layers atomically.

    # Forest LOBES -- the rectangle treeline pushed inward at a few
    # places so the playable space isn't a clean box. Each lobe is an
    # organic blob of trees nudged some distance off the edge. The
    # blob is elliptical with hash noise on the edge so the inner
    # line reads ragged rather than ruled. Skips buildings, exit
    # tiles, the river, and the corn cover.
    lobes = [
        # (cx, cy, rx, ry, seed) -- centre, x/y radius, RNG seed.
        # Eastern lobe pushing in between the well and the bridge --
        # narrows the corridor coming in from the Lodge.
        (88, 32, 6, 5, 11),
        # Southeast lobe between the kid's house and the barn --
        # breaks the long eastern bank up.
        (95, 72, 5, 8, 19),
        # Western lobe pushing in below the church -- creates a
        # natural clearing the player has to step around.
        (8,  28, 5, 6, 23),
        # Western lobe between the sheriff and the farm.
        (12, 78, 4, 5, 29),
        # Northern lobe between the cornfield-maze exit and the
        # river crossing.
        (44, 6,  6, 4, 31),
        # Southern lobe between the burn clearing and the barn.
        (60, 95, 9, 4, 37),
    ]
    for (lx, ly, rx, ry, seed) in lobes:
        lr = random.Random(seed)
        for ty in range(ly - ry - 1, ly + ry + 2):
            for tx in range(lx - rx - 1, lx + rx + 2):
                if not (0 <= ty < h and 0 <= tx < w):
                    continue
                if objects_l[ty][tx] != ".":
                    continue
                if _border_protected(tx, ty):
                    continue
                nx = (tx - lx) / float(rx + 1)
                ny = (ty - ly) / float(ry + 1)
                d = nx * nx + ny * ny
                hsh = lr.random()
                if d <= 0.55 or (d <= 1.0 and hsh < 0.55):
                    objects_l[ty][tx] = "T"
    # (north + south thin-rank pass removed -- the full scatter band
    # below now stamps all four edges via scatter_forest_band.)

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
    # Farmhouse (south), plus a spur toward the burn clearing.
    _carve_track(floor_ll, objects_l,
                 [(31, 24), (16, 16), (9, 11), (7, 10)], trk)                # -> Church door
    _carve_track(floor_ll, objects_l,
                 [(31, 24), (18, 44), (9, 58), (7, 66)], trk)                # -> Sheriff door
    _carve_track(floor_ll, objects_l, [(7, 66), (7, 80), (7, 94)], trk)      # -> Farmhouse door
    _carve_track(floor_ll, objects_l, [(7, 82), (11, 81), (14, 80)], trk)    # -> clearing entrance
    # ---- THE FOLD ROAD ----
    # A dirt road that runs east-west across Brimley at row 24, passing
    # right over the bridge. The brimley scene wraps on its x axis (see
    # sc.wrap_x below), so the road has no west or east edge in fiction
    # -- walking west off the map seamlessly continues from the east
    # side of the same map. No narrator, no fade, no transition. The
    # fold is a property of the world.
    _carve_track(floor_ll, objects_l, [(98, 24), (62, 24), (35, 24)], trk)
    _carve_track(floor_ll, objects_l, [(31, 24), (16, 24), (1, 24)], trk)
    # Pin the road exactly at row 24 across the wrap zones so the seam
    # between west-edge cols and east-edge cols is invisible. The
    # adjacent rows (23 + 25) are forced back to grass so the carved
    # wobble doesn't kink across the wrap line.
    for tx in list(range(0, 5)) + list(range(95, 100)):
        floor_ll[24][tx] = "d"
        if floor_ll[23][tx] == "d":
            floor_ll[23][tx] = "g"
        if floor_ll[25][tx] == "d":
            floor_ll[25][tx] = "g"
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
    # marsh just fills the open plain so it reads as wet brimley.
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
    # Eastern village-square footpaths: lead the eye from the
    # country-lane entry (98, 7) S/W to the well (94, 13), then on to
    # the woodshed door (91, 16). Without these the merged content
    # reads as lost in the meadow.
    for ftx in range(94, 99):
        floor_ll[7][ftx] = "d"
    for fty in range(8, 14):
        floor_ll[fty][94] = "d"
    floor_ll[14][93] = "d"
    floor_ll[14][92] = "d"
    for fty in range(15, 17):
        floor_ll[fty][91] = "d"

    # ---- THE MAIN ROAD (navigability pass) ----
    # The carved tracks above read as faint, wandering footpaths -- easy to
    # lose in the wrapped meadow. This lays ONE obvious, wide dirt spine the
    # player can always pick up and follow: a 3-wide E-W road across town
    # (over the bridge, wrapping at both edges), a connector from the Lodge
    # entry past the WELL (the central landmark) down to it, and an
    # east-bank branch to the store/school/kid/barn cluster. Walls, roofs,
    # bridge planks and open water are never paved; band trees sitting on a
    # new road tile are cleared so the line stays clean.
    def _pave(tx, ty):
        if not (0 <= tx < w and 0 <= ty < h):
            return
        if objects_l[ty][tx] in ("W", "r", "$"):
            return                                   # walls / roofs / bridge planks
        if floor_ll[ty][tx] == "~":
            return                                   # open water
        floor_ll[ty][tx] = "d"
        if objects_l[ty][tx] in ("T", "p"):
            objects_l[ty][tx] = "."                  # clear trees off the road
    # E-W spine: rows 23-25, full width (wraps east-west at the edges).
    for ry in (23, 24, 25):
        for tx in range(w):
            _pave(tx, ry)
    # Entry square + well -> spine: a 3-wide vertical run on the east side.
    for tx in (93, 94, 95):
        for ty in range(6, 26):
            _pave(tx, ty)
    # The LODGE LANE (2026-07 playtest fix): the east-edge opening is 3
    # tiles (rows 6-8), so the road that meets it is too -- a full-width
    # lane from the edge to the junction, not a one-tile footpath the
    # player can arrive beside and never see. The junction corner squares
    # off against the north-south connector above.
    for tx in range(93, w):
        for ty in (6, 7, 8):
            _pave(tx, ty)
    # East-bank branch: spine -> the store/school/kid/barn cluster.
    for tx in (57, 58, 59):
        for ty in range(25, 74):
            _pave(tx, ty)

    # Stamp the permeable forest band on top of everything else -- trees,
    # ground blotch, de-clump, and hideable bushes -- using the shared
    # helper so every outdoor scene gets the same treatment.
    _band_bushes = []
    from .base import scatter_forest_band
    scatter_forest_band(floor_ll, objects_l, w, h,
                        depth=BAND_DEPTH, seed=53,
                        protected=_border_protected,
                        place_bush=lambda px, py:
                            _band_bushes.append((px, py)))
    floor_rows = ["".join(r) for r in floor_ll]

    objects = ["".join(r) for r in objects_l]

    sc = Scene("brimley", floor_rows, objects, music="wind")
    # The church-door point the pealing bell broadcasts from
    # (Game._tick_bell): cult hunters converge here while it rings, and
    # a hunter reaching it stills the rope. One step outside the door
    # tile so the walk target lands on open ground.
    sc._bell_door = (church_door * TILE + 16,
                     (church_bot + 1) * TILE + 16)
    # Hideable bushes the band helper queued -- each sits on a corn-
    # cover (':') tile so stepping into one hides the player.
    for bx, by in _band_bushes:
        sc.add_decoration(Decoration(bx, by, "bush"))
    # Brimley's world is toroidal on both axes -- the fold-road at
    # row 24 wraps east-west; the perimeter forest wraps north-south.
    # Walking off any side of the map seamlessly continues from the
    # opposite side. No transition, no teleport, no fade -- the town
    # is a closed loop, exactly as the bible describes the fold.
    sc.wrap_x = True
    sc.wrap_y = True
    # The east edge of Brimley is the road back to the Lodge via the
    # country lane. The other building doors wire into their interiors.
    sc.add_exit("4", "country_lane",      "from_brimley")
    sc.add_exit("a", "river_crossing", "from_brimley")
    sc.add_exit("m", "church",     "from_brimley")  # Church
    sc.add_exit("o", "abandoned_farmhouse",     "from_brimley")  # Farmhouse
    sc.add_exit("J", "toby_house",         "from_brimley")  # Kid
    sc.add_exit("n", "barn",              "from_brimley")  # Barn
    # The town has come apart into Brimley's fog: the Sheriff's office,
    # General Store and Schoolhouse stand out here on the bank now, all
    # enterable, their interiors returning to this scene.
    sc.add_exit("y", "sheriff_office", "from_brimley")  # Sheriff's office
    sc.add_exit("D", "shop",              "from_brimley")  # General Store
    sc.add_exit("B", "schoolhouse",       "from_brimley")  # Schoolhouse
    sc.add_exit("R", "gravel_road_north", "from_brimley")  # North gravel road
    sc.add_exit("M", "cornfield_maze",    "from_brimley_south")  # South: macro-loop
    # (The east-west road wrap is handled by the engine via wrap_x --
    # no exit tile, no spawn. See the gaps carved at row 24 below.)
    clearing_tx, clearing_ty = 15, 80
    objects_list = [list(r) for r in objects]
    objects_list[clearing_ty][clearing_tx] = "j"
    # North passage to the river_crossing -- a single tile carved
    # into the north tree line, west of the river.
    objects_list[0][50] = "a"
    # ---- Eastern village square (merged from the old `village` scene) ----
    # The town's well + woodshed sit just inside the east edge so the
    # player walks in from the Lodge and sees the landmark immediately.
    # Footpaths to the well + shed are carved earlier in the floor pass.
    # The well at col 94, row 13 -- dread set-dressing, NOT a way down. It is
    # the town's dead shaft (worn smooth, no rope, no rigging one); it goes
    # nowhere the player can follow. The real throat down is the cult's dug
    # MINE out at the effigy grove by the river -- reached by the rite, never
    # by this well.
    # Surrounding floor was already grass; the well is a decoration.
    # (The woodshed moved to the Lodge yard -- scenes/lodge_yard. Brimley
    # no longer hosts a shed; the footpath that once led here is left as worn
    # ground to nowhere.)
    # Gravel road passage (north) -- single 'R' tile at col 96. Uses
    # 'R' rather than 'a' to avoid collision with the river-crossing
    # 'a' exit (exit chars are scene-global, not per-tile).
    objects_list[0][96] = "R"
    # The fold road -- gaps in both tree walls at row 24 so the road
    # can be walked across the whole map east-to-west. There's no exit
    # tile and no fade: walking off the edge is caught by the engine's
    # wrap_x (player coord + camera shift) so the road simply continues
    # onto the opposite edge. Both edges open at the same row, so the
    # wrap lands on road, not a tree.
    objects_list[24][0] = "."
    objects_list[24][99] = "."
    # ---- The dead lots (2026-07): the abandoned cars ----
    # Everyone drove into Brimley and nothing with an engine leaves
    # (Royce/Vane, NARRATIVE §4), so the cars pool where their drivers
    # finally stopped: a ragged rank beside the barn (the commune's own
    # fleet, walked away from the night they went below), a give-up
    # line on the fold-road shoulders east of the bridge, and two noses
    # swallowed in the corn where somebody tried the field itself.
    # dead_cars stamps a 2-tile solid 'X' footprint per hull (bump +
    # hard cover); the Decorations are added after sc.objects lands.
    _lot_cars = dead_cars(objects_list, [
        # the barn rank, noses at the barn's west wall
        (73, 73, "rust_coupe", 0.55, 24, "h"),
        (75, 75, "rust_sedan", 0.10, 21, "h"),
        (75, 77, "rust_wagon", -0.08, 22, "h", {"luggage": True}),
        (75, 79, "rust_van", 0.15, 23, "h"),
        # the give-up line on the fold-road shoulders
        (56, 22, "rust_wagon", 0.10, 31, "h"),
        (61, 22, "rust_coupe", -0.12, 32, "h"),
        (66, 22, "rust_van", 3.05, 33, "h"),
        (59, 26, "rust_sedan", 3.22, 34, "h"),
        (64, 26, "rust_sedan", 0.05, 35, "h"),
        # noses in the corn
        (57, 36, "rust_wagon", 0.35, 41, "h"),
        (26, 21, "rust_coupe", 2.95, 42, "h"),
    ])
    # South exit to cornfield_maze (the bottom of the loop). The road
    # at col 50 cuts down through the southern tree wall via a single
    # 'M' tile. Walking south long enough through cornfield_maze ->
    # cornfield_path -> here brings you back to Brimley north.
    objects_list[h - 1][48] = "M"
    sc.objects = objects_list
    for _d in _lot_cars:
        sc.add_decoration(_d)
    sc.add_exit("j", "clearing", "from_brimley")
    sc.set_spawn("default", w - 2, 7)
    # Coming in from the Lodge via the country lane (east edge).
    sc.set_spawn("from_country_lane", w - 2, 7)
    # Legacy alias for any old "from_village" save references; resolves
    # to the same east-edge entry now that village is merged.
    sc.set_spawn("from_village", w - 2, 7)
    sc.set_spawn("from_lodge_yard", w - 2, 7)
    # Climbing back out of the well lands beside it.
    sc.set_spawn("from_well", 94, 13)
    # Coming out of the woodshed door (the lumber axe + flashlight shed).
    # Spawn ONE TILE NORTH of the door so the player doesn't immediately
    # re-trigger and isn't stuck inside the shed walls.
    sc.set_spawn("from_woodshed", 91, 15)
    # The north passage to the gravel road (cult-priest territory).
    sc.set_spawn("from_gravel_road", 96, 2)
    sc.set_spawn("from_mist_house", 7, church_bot + 1)
    sc.set_spawn("from_alter", 1, 85)
    sc.set_spawn("from_river_crossing", 50, 1)
    # Cornfield maze pushes north and emerges into the brimley
    # a few tiles west of the river crossing -- the maze led you
    # somewhere wrong. Spawn point on the open north band.
    sc.set_spawn("from_cornfield_maze", 40, 1)
    # The macro-loop return spawn: arriving from cornfield_path's south
    # exit drops the player on Brimley's north edge.
    sc.set_spawn("from_cornfield_path", 48, 1)
    # Returning from the clearing -- spawn one tile EAST of the j
    # tile so the player doesn't auto-retrigger.
    sc.set_spawn("from_clearing", clearing_tx + 1, clearing_ty)
    # Returning from each scattered building lands the player one
    # tile south of the door so they don't immediately re-enter.
    sc.set_spawn("from_church",     church_door,  church_bot + 1)
    sc.set_spawn("from_sheriff_office", sheriff_door, sheriff_bot + 1)
    sc.set_spawn("from_abandoned_farmhouse",     farm_door,    farm_bot + 1)
    sc.set_spawn("from_shop",              shop_door,    shop_bot + 1)
    sc.set_spawn("from_toby_house",         kid_door,     kid_bot + 1)
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
    # crows. The burn-clearing entrance at (15, 80) gets its own
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
    # A WHIRLPOOL in the river: the water keeps flowing past it, but at this
    # spot it spirals down a sink in the bed -- where the surface river drains
    # into the one running under the town (NARRATIVE §2: the river is the
    # artery the water, and the diggers, followed down to the door). Cold mist.
    _whirl_row = 38
    _whirl_col = _river_cols(_whirl_row)[1]
    sc.add_decoration(Decoration(_whirl_col * TILE + 16, _whirl_row * TILE + 16,
                                 "swallow_hole"))
    for _mx, _my in [(_whirl_col - 1, _whirl_row - 1), (_whirl_col + 1, _whirl_row + 1)]:
        sc.add_decoration(Decoration(_mx * TILE + 16, _my * TILE + 8, "mist"))
    # The clearing-entrance threshold -- creepy_tree on the j tile
    # itself, a single bloody handprint at the threshold, and a
    # candle melted to a stone at the foot. Just enough cue for
    # the player to recognise the route without a blood trail
    # that telegraphs the discovery from the river.
    sc.add_decoration(Decoration(clearing_tx * TILE + 16,
                                 clearing_ty * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration((clearing_tx + 1) * TILE + 16,
                                 clearing_ty * TILE + 16,
                                 "bloody_handprint"))
    sc.add_decoration(Decoration((clearing_tx + 1) * TILE + 16,
                                 clearing_ty * TILE + 8, "candle"))
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
    def _resident(tx, ty, name, kind, pages=None, movement="wander",
                  voice="blip_mid", radius=52, fold=False, beats=None,
                  stations=None, convo=None):
        # A resident either carries the organic ask verb (`convo`, the
        # chorus conversion; reactive beats volunteer ahead of the menu)
        # or the old fixed page-list (`pages`, the doorstep cameo).
        if convo is not None:
            dfn = chorus_dialogue(convo, beats or ())
        else:
            dfn = _brimley_voice(pages, voice, fold=fold, beats=beats)
        n = NPC(tx * TILE + 16, ty * TILE + 16, name, kind,
                dialogue_fn=dfn,
                movement=movement, radius=radius)
        if stations:
            # The JOBS layer (GAME_CHANGES §19): a personal station
            # route -- walk there, stand the work a while, move on.
            # Tile coords in; errand_step skips any station the nav web
            # can't reach, so a bad spot degrades, never wedges.
            n.movement = "worker"
            n.stations = [{"x": sx * TILE + 16, "y": sy * TILE + 16,
                           "dwell": dw, "face": fc}
                          for (sx, sy, dw, fc) in stations]
        sc.add_npc(n)

    # The locals anchored to their houses -- not patrolling random
    # waypoints. Each one stands within sight of where they actually
    # live, so the town reads as inhabited rather than as NPCs in a
    # field. Bible §2: locals were born here; they cope by staying put.
    # Hettie keeps the shop open. A homebody: she steps out front to
    # sweep a step that doesn't get dirty, then ducks back inside the
    # shop for a spell -- the only time you catch her is at her own door.
    _resident(53, 61, "Hettie", "hettie", [
        "Still open. Always open. The shelves don't empty anymore. Have you noticed.",
        "No deliveries. In a while now. But we manage. We always.",
        "[c=dim]I keep the lights on. So they know. Someone's keeping them on.[/c]",
    ], movement="homebody", radius=34)
    # Old Pell -- the schoolhouse step, the calendar nailed to the wall
    # behind him. He stopped marking it. Another homebody: out on the
    # step a while, then back indoors for a spell.
    # Ask verb (PELL_CONVO); the fold note now files from Royce/Garrick,
    # whose exchanges actually carry the looping-roads account.
    _resident(63, 54, "Old Pell", "old_townsman",
              movement="homebody", radius=34, convo=PELL_CONVO,
        # TODO #10: the town reacts to what the PI learns. Pell reads the
        # digging on him like weather (stasis register; he mutates at
        # stage 3, so this lives in his pre-turn window).
        beats=[("beat_pell_coal",
                lambda g: g._evidence_count() >= 1, [
            "You've been digging at it. I can tell. It's on you like "
            "coal dust.",
            "[c=dim]Whatever you're finding out there, don't bring it up "
            "my step. I've got the calendar where I want it. Stopped. "
            "Some of us need it stopped.[/c]",
        ])])
    # Mrs. Calder is by the east-edge road. She sets a place at supper
    # for a guest she can't name -- a certainty she can't explain that
    # someone is coming. No vanished husband (that read as a perceptible
    # individual loss, forbidden by §1b); just the compulsion she doesn't
    # question. She watches the road. She does not wave.
    _resident(96, 8, "Mrs. Calder", "townswoman",
              movement="idle", convo=CALDER_CONVO,
        # TODO #10: the waiting sharpens as the case opens (she converts
        # at stage 2, so this is her only pre-turn window: evidence 1).
        beats=[("beat_calder_unlatched",
                lambda g: g._evidence_count() >= 1, [
            "Closer now. Whoever the place is set for. An old woman can "
            "feel a knock coming before it lands.",
            "[c=dim]I've started leaving the door unlatched at night. It "
            "seemed... polite.[/c]",
        ])])
    # Royce -- by the river bridge. He tried to drive out like everyone
    # in town did (northern Minnesota; everyone drives) and the corn
    # handed him back every time; he gave it up with the rest. He still
    # clings to the one fact he can't square: you got IN.
    _resident(29, 24, "Royce", "royce",
              convo=ROYCE_CONVO,
        # His job now is the road itself: he paces the stretch he used
        # to drive, west toward the county line, back toward the
        # bridge, and stands looking down it a long while each way.
        stations=[(29, 24, (5.0, 9.0), (-1, 0)),
                  (25, 24, (3.0, 6.0), (-1, 0)),
                  (33, 24, (4.0, 7.0), (1, 0))],
        # TODO #10: his one impossible fact curdles as the case opens (he
        # converts at stage 3; window is evidence 0-2, fires at 2).
        beats=[("beat_royce_throat",
                lambda g: g._evidence_count() >= 2, [
            "You're still here. Course you're still here.",
            "[c=dim]I keep turning it over. Every road out of Brimley "
            "hands you back. Except the one that carried you in. If a "
            "door only opens the one way, mister, it isn't a door.[/c]",
            "[c=dim]It's a throat.[/c]",
        ])])
    # Toby lives INSIDE the kid's house (the `toby_house`
    # scene, kid_dialogue). He used to also stand here on the front step,
    # but that put a solid NPC right on the `from_toby_house` doorway
    # spawn (col 68, row 71) -- so leaving the house wedged the player
    # against him -- and split one child into two. He's now a single NPC,
    # indoors; nothing stands on the step.
    # Garrick -- the old man at the well. Town centre, watching
    # everyone come and go. The law is hollow now; he says so plainly.
    _resident(91, 12, "Garrick", "old_townsman",
              convo=GARRICK_CONVO,
        # Town-centre rounds: his spot, a look in on the well, a stretch
        # of the track where he watches who comes and goes.
        stations=[(91, 12, (6.0, 10.0), (1, 0)),
                  (94, 15, (4.0, 8.0), (0, -1)),
                  (88, 13, (4.0, 7.0), (1, 0))],
        # TODO #10: the direct preacher-murder reaction. Garrick watches
        # the whole town from the well; the pulpit going silent is
        # exactly the kind of thing he'd clock first (he also SAID this
        # would happen: folks who ask questions go quiet).
        beats=[("beat_garrick_quiet",
                lambda g: g.save.flag("preacher_doomed"), [
            "The reverend's gone quiet. Any other week you'd hear him "
            "clear from here, worked up over something or other.",
            "[c=dim]Nothing out of him for days now. Man spends his life "
            "raising his voice, then nothing at all.[/c]",
            "[c=dim]You go by and look in on him, son. Somebody ought "
            "to.[/c]",
        ])])
    # (The unnamed "newcomer woman" who used to stand on the farmhouse
    # path was CUT entirely, maintainer call 2026-07: an unexplained
    # welcomer read as noise, not dread. Brimley's people are the named
    # locals above; the cult presence out here is the set dressing
    # below.)

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
    # a clock stopped dead and a calendar marked up to JAN 15 (the
    # mid-January seal, NARRATIVE §1 setting note 3) and then stopped --
    # the season kept turning, the marking didn't (the
    # fold is spatial, NARRATIVE §2); the truck that drove for the county line and
    # was handed back, nosed dead into the east tree line; and Mrs.
    # Calder's plate, set at supper for a guest she can't name.
    sc.add_decoration(Decoration(58 * TILE + 16, 62 * TILE + 16, "payphone"))
    sc._payphone_pos = (58 * TILE + 16, 62 * TILE + 16)
    # Burn barrels at the occupied yards: no garbage service since the
    # January seal, so the town burns what it can't keep. Lit fires --
    # the only warm light on the banks, and the eye crosses to them.
    for _bx, _by, _bs in ((93, 6, 61), (48, 58, 62), (66, 74, 63)):
        sc.add_decoration(Decoration(_bx * TILE + 16, _by * TILE + 16,
                                     "burn_barrel", seed=_bs))
    # The news rack outside the shop, still holding the seal-day issue.
    # The examine (below) carries the January 15 date; pairs with the
    # stopped calendar and Hettie's newspaper trade.
    _nr_x, _nr_y = 55 * TILE + 16, 61 * TILE + 6
    sc.add_decoration(Decoration(_nr_x, _nr_y, "news_rack"))
    sc._news_rack_pos = (_nr_x, _nr_y)
    # The well -- dread set-dressing, not a way down (a dead town shaft; the
    # descent is the cult's dug mine at the grove, reached by the rite). Sits
    # in the eastern village-square area, south of the country-lane entry.
    well_x = 94 * TILE + 16
    well_y = 13 * TILE + 16
    sc.add_decoration(Decoration(well_x, well_y, "well"))
    sc._well_pos = (well_x, well_y)
    # A wheelbarrow of "rusted" tools left on the east edge (the shed that
    # stood here is gone, but the cleaned tools remain -- the contradiction
    # is the point, still an evidence beat).
    barrow_x = 93 * TILE + 16
    barrow_y = 15 * TILE + 16
    sc.add_decoration(Decoration(barrow_x, barrow_y, "wheelbarrow"))
    sc._barrow_pos = (barrow_x, barrow_y)
    sc.add_decoration(Decoration(52 * TILE + 16, 61 * TILE + 16, "missing_flyer"))
    # The calendar, marked up to JAN 15 (the seal) and then just
    # stopped -- the season kept turning, the marking didn't (NARRATIVE
    # 1b: time runs normally; it's space that folds). Nailed to the
    # schoolhouse wall beside the door.
    sc.add_decoration(Decoration(62 * TILE + 16, 53 * TILE + 16, "calendar"))
    sc.add_decoration(Decoration(95 * TILE + 16, 55 * TILE + 16, "pickup_truck"))
    # (The flat drowned-body decoration that used to float here was removed --
    # it read as a sprite laid on top of the water. The reworked organic dark
    # river patches now carry the dread of the channel on their own. It can be
    # reinstated as a properly submerged form if wanted.)
    # Mrs. Calder's table, laid out in the open by the kid's house: two
    # settings (hers, and the extra place she lays every night for the
    # guest she can't name -- NARRATIVE §4), a candle burned down, and a
    # chair knocked over. Since TODO #22c she never converts and never stops
    # waiting: both settings stand for the whole run (the town stays
    # ordinary; the wrongness is the PI's, never Mrs. Calder's).
    # (The table itself is a solid 't' tile placed below.)
    sc.add_decoration(Decoration(71 * TILE + 10, 72 * TILE + 12, "place_setting"))
    sc.add_decoration(Decoration(71 * TILE + 24, 72 * TILE + 12, "place_setting"))
    sc.add_decoration(Decoration(71 * TILE + 16, 72 * TILE + 2, "candle"))
    sc.add_decoration(Decoration(71 * TILE + 28, 74 * TILE + 12, "overturned_chair"))

    # ---- Gardens, on some lots and not others (food scarcity, NARRATIVE
    # 8): with no deliveries since the new year, the town feeds itself
    # unevenly. Toby's folks keep a working bed dug in beside their house
    # (fresh-turned rows, a staked string, the first cold-hardy shoots);
    # the farmhouse plot has gone over -- collapsed furrows and last
    # year's stubble, let go when its people were. The other lots never
    # dug at all.
    sc.add_decoration(Decoration(int(73.5 * TILE), 67 * TILE, "garden_patch",
                                 tended=True, w=110, h=72, seed=41))
    sc.add_decoration(Decoration(int(12.5 * TILE), 86 * TILE,
                                 "garden_patch",
                                 tended=False, w=100, h=64, seed=42))

    # ---- The churchyard -- the too-even graves of the vanished ----
    # Crooked headstones in two rows: the uncanny rows-of-the-vanished,
    # each leaning its own way a few px off the lattice. (The Preacher's
    # body is no longer here -- the preacher's death (a case note, not counted evidence) is now found in his own church,
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

    # ---- Main-road waymarks: signs + a lamp thread to follow ----
    # A welcome sign where the Lodge road comes in, directional signs at the
    # spine's junctions (the well, the town cluster), and a run of lamps along
    # the main road -- the lit thread the player can always pick up and follow
    # across the wrapped town.
    # The welcome sign stands on the lane's SOUTH shoulder (the lane
    # itself is road now), and a TOWN board waits at the junction where
    # the lane turns south -- the arriving player reads the turn.
    sc.add_decoration(Decoration(97 * TILE + 16, 9 * TILE + 24, "town_sign",
                                 text="BRIMLEY"))
    sc.add_decoration(Decoration(92 * TILE + 16, 7 * TILE + 20, "town_sign",
                                 text="TOWN"))
    sc.add_decoration(Decoration(92 * TILE + 16, 22 * TILE + 16, "town_sign",
                                 text="WELL"))
    sc.add_decoration(Decoration(60 * TILE + 16, 26 * TILE + 16, "town_sign",
                                 text="TOWN"))
    for lx in (12, 24, 46, 70, 88):                  # lamps along the E-W spine
        sc.add_decoration(Decoration(lx * TILE + 16, 22 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(95 * TILE + 16, 16 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(60 * TILE + 16, 45 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(60 * TILE + 16, 64 * TILE + 16, "lantern"))

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

    # Tall-grass meadows scattered across the open ground. Pure
    # decoration -- the player walks through them. They give the bare
    # banks somewhere for the eye to settle and the wind something to
    # move that isn't a dread mark. Seeded from a fixed RNG so the
    # pattern is stable across loads.
    meadow_rng = random.Random(8419)
    # ~120 clumps placed on open object-tiles that aren't on the road
    # tracks, not in the river, not under a building. Reject samples
    # that land on a non-"." object tile.
    placed = 0
    attempts = 0
    while placed < 120 and attempts < 1200:
        attempts += 1
        tx = meadow_rng.randint(2, w - 3)
        ty = meadow_rng.randint(2, h - 3)
        if sc.objects[ty][tx] != ".":
            continue
        # Avoid the immediate east-village square so it doesn't crowd
        # the well/shed read.
        if tx >= 88 and 6 <= ty <= 18:
            continue
        # Avoid the river corridor (the bent river spans cols ~30-36).
        if 29 <= tx <= 37:
            continue
        px = tx * TILE + meadow_rng.randint(4, 28)
        py = ty * TILE + meadow_rng.randint(4, 28)
        sc.add_decoration(Decoration(px, py, "tall_grass"))
        placed += 1

    # A dead grove on the bare west bank -- a stand of leafless trees out
    # in the open emptiness, a focal dread that offers no cover.
    for (gx, gy) in [(17, 39), (19, 41), (16, 43), (20, 44), (18, 46), (15, 41)]:
        sc.add_decoration(Decoration(gx * TILE + 16, gy * TILE + 16, "creepy_tree"))
    # A cult standing-stone ring in the open north-east field, a Yellow
    # Sign cut into the ground at its centre, lit by two braziers -- a
    # warm, watched focal point out in the dark. (2026-07: real weathered
    # standing stones now; the placeholder fluted "pillar" columns read
    # as Roman architecture in a Minnesota corn field.)
    for (px, py) in [(77, 31), (81, 31), (79, 30),
                     (76, 34), (82, 34), (79, 36)]:
        sc.add_decoration(Decoration(px * TILE + 16, py * TILE + 16,
                                     "standing_stone", seed=px * 7 + py))
    sc.add_decoration(Decoration(79 * TILE + 16, 33 * TILE + 16, "yellow_sign"))
    sc.add_decoration(Decoration(77 * TILE + 16, 33 * TILE + 16, "brazier"))
    sc.add_decoration(Decoration(81 * TILE + 16, 33 * TILE + 16, "brazier"))
    # The church steeple -- the one tall thing for miles, a landmark to
    # orient by, rising over the roof into the treeline.
    sc.add_decoration(Decoration(7 * TILE + 16, 7 * TILE + 16, "steeple"))
    # A brazier marking the burn-clearing threshold.
    sc.add_decoration(Decoration(13 * TILE + 16, 80 * TILE + 16, "brazier"))
    # A murder of crows posted along the treeline, watching.
    for (cx, cy) in [(2, 22), (2, 71), (50, 2), (88, 31), (97, 60), (41, 97)]:
        sc.add_decoration(Decoration(cx * TILE + 16, cy * TILE + 16,
                                     "dead_crow" if (cx + cy) % 2 else "crow"))

    # ---- Lived-in town dressing ----
    # The "Welcome to Brimley" sign just north of the east-edge road,
    # right beside the entry the PI drives in on. Weathered, paint
    # mostly gone. First lived-in detail the player sees.
    sc.add_decoration(Decoration(95 * TILE + 16, 5 * TILE + 16,
                                 "town_sign", text="BRIMLEY"))
    # Schoolhouse flagpole -- flag at half-mast, faded, frayed at the
    # trailing edge. Nobody lowered it; it's been there since.
    sc.add_decoration(Decoration(63 * TILE + 16, 55 * TILE + 16,
                                 "flagpole"))
    # The community noticeboard at the well -- three missing-person
    # flyers tacked tight together with a hooded lantern above them so
    # the cluster reads as "someone used to read these." Phantom mark
    # below for the dread layer.
    sc.add_decoration(Decoration(92 * TILE + 16, 14 * TILE + 16, "lantern"))
    for (fx, fy) in [(92 * TILE + 4, 14 * TILE + 22),
                     (92 * TILE + 16, 14 * TILE + 22),
                     (92 * TILE + 28, 14 * TILE + 22)]:
        sc.add_decoration(Decoration(fx, fy, "missing_flyer"))

    # ---- Placed noisemakers (2026-07 sound overhaul) ----
    # The stalled pickup's cab radio: an E-toggleable lure. Turn it on,
    # slip away, and the patrol walks to the music instead of you,
    # until a hand reaches into the cab and kills it.
    sc.add_noise_source(
        95 * TILE + 16, 56 * TILE + 16, "radio", sfx="radio_snatch",
        on_notice="The truck radio catches. A dead station rolls out "
                  "over the street.",
        off_notice="You kill the radio.",
        silenced_notice="The music stops dead.")
    # Passive litter along the routes: glass under the truck's door,
    # tins in the schoolyard lee, and a crow posted on the open
    # approach to the stone ring that flushes screaming.
    sc.add_noise_trap(94 * TILE + 16, 56 * TILE + 24, "glass", seed=7)
    sc.add_noise_trap(61 * TILE + 16, 55 * TILE + 16, "cans", seed=8)
    sc.add_noise_trap(75 * TILE + 16, 38 * TILE + 16, "crow", seed=9)

    # ---- The cult's errands (Scene.add_cult_station) ----
    # The roaming regulars have JOBS, not beats: kneel at the stone
    # ring, look in on the well, stand over Mrs. Calder's laid table.
    # They walk their rounds between stations and any noise or
    # sighting peels them off (systems/stealth.errand_step). This is
    # what makes the town read as THEIRS -- and what the bell and the
    # lures interrupt. (The burn clearing is a sealed pocket off the
    # walkable web, so no station goes there.)
    sc.add_cult_station(79 * TILE + 16, 34 * TILE + 16, pose="kneel",
                        face=(0, -1), dwell=(6.0, 10.0))
    sc.add_cult_station(93 * TILE + 16, 13 * TILE + 16,
                        face=(1, 0), dwell=(4.0, 7.0))
    sc.add_cult_station(71 * TILE + 16, 73 * TILE + 16,
                        face=(0, -1), dwell=(5.0, 9.0))

    # ---- Cult-taken territory: the south-west farmhouse ----
    # Bible §2: newcomers ARE the cult, and one or two contiguous lots
    # would be "their" houses. The abandoned_farmhouse already reads as the
    # creep house; mark it as the newcomers' explicit territory. Yellow
    # sigils on the south wall, candles in the front yard (lit nightly
    # by no one anyone has met), brazier at the path -- the rest of
    # Brimley has no such "kept" attention paid to it.
    farm_door_x = farm_door * TILE + 16
    # Two yellow sigils in the FRONT YARD flanking the approach to the
    # door -- painted on the ground (or planted on stakes; whichever
    # the player wants to read). Drawn beneath the door tile so the
    # wall mass doesn't clip them.
    sc.add_decoration(Decoration((farm_door - 2) * TILE + 16,
                                 (farm_bot + 2) * TILE + 16, "yellow_sign"))
    sc.add_decoration(Decoration((farm_door + 2) * TILE + 16,
                                 (farm_bot + 2) * TILE + 16, "yellow_sign"))
    # Front-yard candles -- lit, kept burning. The newcomers tend them.
    for (cx, cy) in [(farm_door - 1, farm_bot + 3),
                     (farm_door,       farm_bot + 4),
                     (farm_door + 1, farm_bot + 3)]:
        sc.add_decoration(Decoration(cx * TILE + 16, cy * TILE + 16,
                                     "candle"))
    # A brazier on the approach path -- the newcomers light the way in.
    sc.add_decoration(Decoration(farm_door_x, (farm_bot + 5) * TILE + 16,
                                 "brazier"))

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

    # Surface enclosed cover (STEALTH_REWORK §6): the corn and the tree
    # lines are the CONCEALMENT system out here; the one rooted set-piece
    # option is the gap under the dead pickup's bed. A searcher can check
    # it like any other enclosed hide.
    sc.hide_spots = [
        (94 * TILE + 16, 56 * TILE + 8, "under"),   # under the dead pickup
    ]

    # The PI's car has MOVED to the arrival road west of the Lodge (where it
    # died on the way in -- the SPREAD escape now lives there, scenes/
    # lodge_yard.build_arrival_road). Brimley keeps only the dead pickup.
    objects_list = [list(r) for r in sc.objects]
    # The dead pickup is a big hulk -- solid tiles under its length so
    # the player can't walk through it (decoration at tile 95,55).
    for cx in (93, 94, 95, 96):
        if 0 <= cx < sc.w:
            objects_list[55][cx] = "X"
    # Mrs. Calder's outdoor table (solid), her settings drawn on top.
    objects_list[72][71] = "t"
    sc.objects = objects_list

    def _brimley_interact(game):
        # The well -- DEMOTED to dread set-dressing, and fully SEVERED from
        # the descent (2026-07): nobody went down HERE. The congregation went
        # down the cult's dug MINE out at the grove (down the river; Toby is
        # the witness, §2), reached now only by the rite (the Invitation ->
        # the school door -> the grove's descent fold). This well is just a
        # dead, dry town well gone wrong -- bottomless, cold air climbing out
        # -- ominous, and going nowhere. The act-one descent question is
        # Toby's job now, not the well's.
        wx, wy = sc._well_pos
        if abs(game.player.x - wx) < 36 and abs(game.player.y - wy) < 36:
            if not game.save.flag("well_examined"):
                game.save.set_flag("well_examined", True)
                game.audio.play("low_pulse", 0.4)
                game.dialog.show([
                    "[c=dim](You lean over the lip. The shaft drops "
                    "past where any water should be. No glint, no "
                    "bottom, just cold air climbing up out of it.)[/c]",
                    "[c=dim]A dead well, dry a long time. The lip is worn "
                    "smooth where the town used to lean and draw, back when "
                    "it drew anything.[/c]",
                    "Nothing down there now. And no way down it if there "
                    "were.",
                ], speaker="", voice="blip_soft", portrait="narrator")
                return
            game.audio.play("low_pulse", 0.4)
            game.show_notice("Cold air climbs out of the dark. No way "
                             "down for you here.")
            return
        # Wheelbarrow of "rusted" tools -- the diggers keep them cleaned.
        bx, by = sc._barrow_pos
        if abs(game.player.x - bx) < 36 and abs(game.player.y - by) < 36:
            if not game.save.flag("barrow_inspected"):
                game.save.set_flag("barrow_inspected", True)
                _evidence(game, "barrow_tools", "Some old tools.")
            return
        # The news rack outside the shop -- the last issue it was fed.
        nx_, ny_ = sc._news_rack_pos
        if abs(game.player.x - nx_) < 36 and abs(game.player.y - ny_) < 36:
            game.audio.play("blip_low", 0.4)
            game.dialog.show([
                "A coin rack of newspapers, bleached behind the scratched "
                "plastic. The county weekly.",
                "[c=dim]Dated January 15. Every copy in the stack. Nobody "
                "ever fed it another.[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return
        # The payphone -- it won't dial out. The line is never dead,
        # though; something is always already on it.
        px, py = sc._payphone_pos
        if abs(game.player.x - px) < 40 and abs(game.player.y - py) < 40:
            game.audio.play("blip_low", 0.5)
            line = [
                "No dial tone. No ringing. The line is open to something.",
                "[c=dim]Far down it, under the hiss, you hear your own "
                "voice, already mid-sentence.[/c]",
            ]
            game.dialog.show(line, speaker="", voice="blip_soft",
                             portrait="narrator")
    # [E] cues for the interactions resolved in _brimley_interact -- the well
    # (dread set-dressing), the woodshed door, the tool barrow and the payphone
    # had NO prompt before, so the player had to guess where to press E. Radii
    # match the handler's checks. (The car moved to the arrival road.)
    sc.add_interactable(sc._well_pos[0], sc._well_pos[1], 36)
    sc.add_interactable(sc._barrow_pos[0], sc._barrow_pos[1], 36)
    sc.add_interactable(sc._payphone_pos[0], sc._payphone_pos[1], 40)
    sc.add_interactable(sc._news_rack_pos[0], sc._news_rack_pos[1], 36)

    sc.on_interact_fn = _brimley_interact

    # The Preacher's end (2026-07 rework): the doom sends Crane out of his
    # church, down to the river after his flock. His remains lie on the
    # west bank (the cross; a case note, not counted evidence); the emptied church's river-mud
    # line points here. The scene rebuilds each load, so the remains are
    # re-laid every entry after the doom.
    sc._preacher_bank_pos = (31 * TILE + 16, 52 * TILE + 16)
    sc.on_enter_fn = _brimley_on_enter
    sc.on_update_fn = _brimley_update
    return sc
