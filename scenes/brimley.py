"""Brimley -- the unified town map (60x60 redesign, 2026-07; TODO #18).

A compact northern-Minnesota corn town, split by a north-south river that
the planked bridge crosses at rows 24-26 (the fold road runs straight over
it). The seven buildings are scattered across a west-bank town clustered
around a central plaza (church + barn north, shop + school upper-middle,
sheriff + farmhouse south) with the kid's house on the narrow east bank,
where the lodge road comes in past the well square. The burn clearing and
the standing-stone ring sit out in the open fields. Nothing is where it
was on the old 100x100 map: this is a full reshape at the same content
density, not a scale-down (the square + torus wrap + fog rim all stay).

Atmosphere: black haze drawn by Game._draw_brimley_haze, ambient 'wind'
track played by music='wind'."""
import math
import random
from constants import TILE
from entities.decoration import Decoration
from entities.npc import NPC
from .base import Scene, dead_cars
from .dialogue import (_evidence, preacher_body_examine, chorus_dialogue,
                       PELL_CONVO, CALDER_CONVO, ROYCE_CONVO, GARRICK_CONVO)


def _raise_cult_camp(game, scene):
    """The newcomers' rest/gathering camp in the SE corn clearing. NOTHING at
    0 evidence (the town reads normal, NARRATIVE §2); at 1 evidence -- the cult
    awake -- the whole camp is set up: a lit ground fire ringed by bedrolls and
    felled-log seats, a hung lantern. The crew fills it from the cult spawn
    pool (systems/threat_mixin). Rebuilt every load once the cult wakes."""
    if game._evidence_count() < 1:
        return
    cx, cy = scene._camp_pos
    # Beat the worn packed ground in NOW (the cult set the camp up): the corn
    # underfoot goes to trodden dirt. On_enter runs before the first draw, so
    # the floor bake picks it up; scenes rebuild each load, so it re-applies.
    ctx, cty = int(cx // TILE), int(cy // TILE)
    for ty in range(cty - 2, cty + 2):
        for tx in range(ctx - 2, ctx + 3):
            if 0 <= ty < scene.h and 0 <= tx < scene.w \
                    and scene.floor[ty][tx] in (":", ";", "g"):
                scene.floor[ty][tx] = "d"
    scene.add_decoration(Decoration(cx, cy, "camp_fire", seed=71))
    for (dx, dy, kind, sd) in [
            (-42, -4, "bedroll", 1), (36, -12, "bedroll", 2), (-8, 40, "bedroll", 3),
            (44, 18, "log_seat", 4), (-44, 22, "log_seat", 5), (10, -40, "log_seat", 6)]:
        scene.add_decoration(Decoration(cx + dx, cy + dy, kind, seed=sd))
    scene.add_decoration(Decoration(cx + 48, cy - 34, "lantern"))


def _brimley_on_enter(game, scene):
    """On-enter set-pieces, rebuilt every load: the cult CAMP (raised once the
    cult wakes at 1 evidence) and the doomed Preacher's riverbank remains
    (2026-07 rework: he leaves his church to talk his flock home and is found
    here, never on his own floor)."""
    _raise_cult_camp(game, scene)
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
    falls back to their ambient loop."""
    def _fn(game, npc):
        portrait = getattr(npc, "portrait", None) or npc.sprite_kind
        for flag, pred, beat_pages in (beats or ()):
            if game.save.flag(flag):
                continue
            if pred(game):
                game.save.set_flag(flag, True)
                game.dialog.show(beat_pages, speaker=npc.name, voice=voice,
                                 portrait=portrait)
                return
        game.dialog.show(pages, speaker=npc.name, voice=voice,
                         portrait=portrait)
        if fold and hasattr(game, "_fold_mentioned"):
            game._fold_mentioned(npc.name)
    return _fn


def _stamp_building(objects_l, left, right, top, bot,
                     door_char, face, door_pos):
    """Stamp a rectangular building footprint into objects_l. Outer
    perimeter is wall (W); interior is roof (r); a single door tile
    (door_char) is punched through ONE face so the building can front the
    street it actually sits on -- `face` is 's'/'n' (door at column
    `door_pos`) or 'e'/'w' (door at row `door_pos`). The tilt + flat door
    renderers derive the opening direction from the wall geometry
    (`_door_room_dir`), so a door on any face draws correctly.

    Returns ((door_tx, door_ty), (out_tx, out_ty)) -- the door tile and the
    walkable tile just outside it (the approach + the spawn-back)."""
    for cx in range(left, right + 1):
        objects_l[top][cx] = "W"
        objects_l[bot][cx] = "W"
    for ry in range(top + 1, bot):
        objects_l[ry][left] = "W"
        objects_l[ry][right] = "W"
        for cx in range(left + 1, right):
            objects_l[ry][cx] = "r"
    if face == "s":
        dt, out = (door_pos, bot), (door_pos, bot + 1)
    elif face == "n":
        dt, out = (door_pos, top), (door_pos, top - 1)
    elif face == "e":
        dt, out = (right, door_pos), (right + 1, door_pos)
    else:  # "w"
        dt, out = (left, door_pos), (left - 1, door_pos)
    objects_l[dt[1]][dt[0]] = door_char
    return dt, out


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
    w = 60
    h = 60
    river_center_x = 30
    bridge_rows = (24, 25, 26)
    # The river runs N-S, bending gently. The bridge rows are pinned to
    # centre so the crossing stays put; the bend eases back to centre
    # across the four rows on either side of the bridge so there's no kink.
    def _river_cols(ty):
        if ty in bridge_rows:
            cx = river_center_x
        else:
            dist_to_bridge = min(abs(ty - bridge_rows[0]),
                                  abs(ty - bridge_rows[-1]))
            sine = math.sin(ty * 0.16) * 2.0
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
                    row.append("~")        # river water
            else:
                row.append("g")
        floor_rows.append("".join(row))
    # Broader river span for downstream protection (corn/marsh/border).
    river_cols = tuple(range(river_center_x - 3, river_center_x + 4))

    # Walkable corn-cover patches -- the ':' tile passively hides the
    # player (Game flips player.hidden to "corn"), turning the open town
    # into a field with cover lanes to sneak between the buildings. Kept
    # OFF the west-central glade (cols 8-20, rows 27-40) so the stealth
    # harness always measures on true open ground.
    corn_patches = [
        (8, 14, 15, 18), (3, 30, 8, 40), (24, 30, 30, 38),
        (40, 44, 48, 52), (44, 10, 52, 18), (34, 44, 42, 52),
        (5, 50, 12, 56),
    ]
    floor_rows = [list(r) for r in floor_rows]
    for (pl, pt, pr, pb) in corn_patches:
        cxm = (pl + pr) / 2.0
        cym = (pt + pb) / 2.0
        rxr = (pr - pl) / 2.0 + 1.0
        ryr = (pb - pt) / 2.0 + 1.0
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

    # No hard perimeter wall: Brimley wraps on both axes, the border is a
    # scattered semi-permeable forest band (stamped later). Bridge planks
    # at the river are set explicitly.
    objects_l = []
    for ty in range(h):
        row = ["."] * w
        if ty in bridge_rows:
            for cx in _river_cols(ty):
                row[cx] = "$"
        objects_l.append(row)

    # 3-wide lodge road opening along the EAST edge -- rows 24, 25, 26
    # (the fold-road level; the arriving PI drives straight onto it).
    for ry in (24, 25, 26):
        objects_l[ry][w - 1] = "4"

    # ---- Scattered buildings (6w x 5h) ----
    # Church + barn stand north; shop + school upper-middle; sheriff +
    # farmhouse south; the kid's house alone on the east bank. Every one is
    # somewhere new versus the old map, and each DOOR FRONTS THE STREET it
    # actually sits on: church + sheriff open EAST onto the central spine,
    # barn + farmhouse open WEST onto it, the shop + school (which sit right
    # above the E-W fold road) open SOUTH onto that main drag, and the kid's
    # house opens NORTH onto its access road. A natural mix, not a rule.
    church_left, church_right, church_top, church_bot = 6, 11, 8, 12
    church_dt, church_out = _stamp_building(
        objects_l, church_left, church_right, church_top, church_bot, "m", "e", 10)

    barn_left, barn_right, barn_top, barn_bot = 20, 25, 8, 12
    barn_dt, barn_out = _stamp_building(
        objects_l, barn_left, barn_right, barn_top, barn_bot, "n", "w", 10)

    shop_left, shop_right, shop_top, shop_bot = 8, 13, 18, 22
    shop_dt, shop_out = _stamp_building(
        objects_l, shop_left, shop_right, shop_top, shop_bot, "D", "s", 10)

    school_left, school_right, school_top, school_bot = 20, 25, 18, 22
    school_dt, school_out = _stamp_building(
        objects_l, school_left, school_right, school_top, school_bot, "B", "s", 22)

    sheriff_left, sheriff_right, sheriff_top, sheriff_bot = 7, 12, 44, 48
    sheriff_dt, sheriff_out = _stamp_building(
        objects_l, sheriff_left, sheriff_right, sheriff_top, sheriff_bot, "y", "e", 46)

    farm_left, farm_right, farm_top, farm_bot = 19, 24, 44, 48
    farm_dt, farm_out = _stamp_building(
        objects_l, farm_left, farm_right, farm_top, farm_bot, "o", "w", 46)
    # A lean-to shed bolted onto the farmhouse's east wall (cols 25-26,
    # rows 45-47, no door -- a closed store), so the footprint stops
    # reading as one clean rectangle.
    for cx in range(25, 27):
        objects_l[45][cx] = "W"
        objects_l[47][cx] = "W"
    objects_l[46][25] = "r"
    objects_l[46][26] = "W"

    kid_left, kid_right, kid_top, kid_bot = 44, 49, 36, 40
    kid_dt, kid_out = _stamp_building(
        objects_l, kid_left, kid_right, kid_top, kid_bot, "J", "n", 46)

    # Hand-placed cultist spawn ANCHORS (the maintainer's marks) -- 9 spread
    # over town + 5 at the SE camp. Defined here so the scattered-tree pass
    # below can keep them clear; wired to the scene as `cult_spawns` at the end.
    _ANCHORS = [
        (6, 6), (7, 16), (17, 24), (13, 28), (26, 31), (43, 30),
        (48, 22), (17, 51), (20, 43),                       # spread over town
        (40, 50), (44, 50), (41, 52), (43, 52), (42, 49),   # the camp crew
    ]

    # Road corridors poke cleanly through the 7-tile forest band so the
    # scattered trees don't grow over an exit or the lodge square.
    def _border_protected(tx, ty):
        if tx in (21, 22, 23) and ty <= 6:
            return True                                  # cornfield_maze corridor
        if tx in (35, 36, 37) and ty <= 6:
            return True                                  # cornfield_path arrival
        if tx in (49, 50, 51) and ty <= 6:
            return True                                  # gravel road '^'
        if ty in (24, 25, 26) and (tx <= 6 or tx >= 53):
            return True                                  # fold-road wrap ends + lodge lane
        if tx >= 47 and 12 <= ty <= 28:
            return True                                  # eastern lodge/well square
        if tx in (19, 20, 21) and ty >= 53:
            return True                                  # south macro-loop 'M'
        if 8 <= tx <= 12 and 48 <= ty <= 52:
            return True                                  # burn-clearing threshold pocket
        if tx in river_cols and (ty <= 6 or ty >= 53):
            return True                                  # river mouths
        return False

    BAND_DEPTH = 7

    # Forest LOBES -- the treeline pushed inward at a few places so the
    # playable space isn't a clean box. Each is an organic ellipse of
    # trees with a ragged hash-noise edge. Skips buildings, exits, the
    # river, the corn cover, and the west-central stealth glade.
    lobes = [
        (52, 34, 4, 5, 11),    # east bank between the square and the kid's house
        (6, 32, 4, 5, 23),     # west, below the shop
        (44, 8, 5, 4, 31),     # north-east, above the stone ring
        (14, 52, 5, 4, 37),    # south, between the sheriff and the clearing
        (34, 34, 3, 4, 43),    # a stand pushing off the east river bank
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
                # BROKEN-UP stands (maintainer note): thinner than a solid blob
                # and ~half passable ('p', identical-looking) so the lobe reads
                # as a scattered stand you can push through, never a wall.
                if d <= 0.4 or (d <= 1.0 and lr.random() < 0.4):
                    objects_l[ty][tx] = "p" if lr.random() < 0.5 else "T"

    # Lit windows flanking a few doors (the 'i' tile glows + a dark figure
    # passes behind the glass on its own clock), on the SAME wall face as
    # the door so they read together on the street front.
    for (wy, wx) in [(22, 21), (22, 23),     # school (south wall)
                     (22, 9), (22, 11),      # shop (south wall)
                     (36, 45), (36, 47)]:    # kid's house (north wall)
        objects_l[wy][wx] = "i"

    # ---- Worn dirt tracks + the roads ----
    floor_ll = [list(r) for r in floor_rows]
    trk = random.Random(7)
    # West-town N-S spine: down the plaza between the two building columns.
    _carve_track(floor_ll, objects_l, [(16, 8), (16, 25), (16, 52)], trk)
    # Spurs from the spine to each street-facing door (E doors on the west
    # row, W doors on the east row) so the door opens onto worn ground.
    _carve_track(floor_ll, objects_l, [(15, 10), (12, 10)], trk)   # -> Church (E)
    _carve_track(floor_ll, objects_l, [(17, 10), (19, 10)], trk)   # -> Barn (W)
    _carve_track(floor_ll, objects_l, [(10, 24), (10, 23)], trk)   # -> Shop (S, onto fold road)
    _carve_track(floor_ll, objects_l, [(22, 24), (22, 23)], trk)   # -> School (S, onto fold road)
    _carve_track(floor_ll, objects_l, [(15, 46), (13, 46)], trk)   # -> Sheriff (E)
    _carve_track(floor_ll, objects_l, [(17, 46), (18, 46)], trk)   # -> Farmhouse (W)
    _carve_track(floor_ll, objects_l, [(16, 40), (11, 46), (10, 50)], trk)   # -> clearing
    # East bank: the lodge square -> the kid's house (N door) down the
    # connector, then west to the door.
    _carve_track(floor_ll, objects_l, [(50, 26), (48, 33), (48, 35), (46, 35)], trk)
    # A cult path worn off the east bank out to the standing stones.
    _carve_track(floor_ll, objects_l, [(44, 20), (42, 17), (40, 15)], trk)

    # ---- THE FOLD ROAD ----
    # A dirt road east-west across town at row 25, right over the bridge.
    # brimley wraps on its x axis, so the road has no west/east edge: walk
    # off one side and you continue from the other.
    _carve_track(floor_ll, objects_l, [(58, 25), (40, 25), (33, 25)], trk)
    _carve_track(floor_ll, objects_l, [(29, 25), (16, 25), (1, 25)], trk)

    # ---- Marsh -- sodden low ground, organic blobs across the open
    # fields. Only plain grass converts, so the river, corn, tracks and
    # buildings survive. Kept off the west-central stealth glade.
    for (pl, pt, pr, pb) in [(3, 42, 12, 50), (33, 40, 41, 48),
                             (44, 44, 52, 52), (34, 10, 42, 20)]:
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

    # ---- THE MAIN ROAD (navigability pass) ----
    # One obvious wide dirt spine the player can always pick up: a 3-wide
    # E-W road across town (over the bridge, wrapping at both edges), the
    # west-town N-S spine, and the lodge-lane -> well-square connector.
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
    # E-W spine: rows 24-26, full width (wraps east-west at the edges).
    for ry in (24, 25, 26):
        for tx in range(w):
            _pave(tx, ry)
    # West-town N-S spine: cols 15-17, rows 8-52 (through the plaza).
    for tx in (15, 16, 17):
        for ty in range(8, 53):
            _pave(tx, ty)
    # East connector: the gravel-road 'R' + lodge square down to the fold
    # road (cols 50-52), and the branch south to the kid's house.
    for tx in (50, 51, 52):
        for ty in range(0, 27):
            _pave(tx, ty)
    for ty in range(26, 41):
        _pave(48, ty)

    # ---- Scattered field trees (maintainer note: break the empty fields) ----
    # The long open sightlines are the map's weak dread zone; sprinkle single
    # trees (mixed solid/passable) across the bare grass so the fields read as
    # a thinning wood, not a lawn -- the trees the broken-up clumps shed. Only
    # plain grass converts, so roads, corn cover, marsh, the river, and worn
    # tracks survive; skips building aprons, the protected corridors, the
    # stealth glade, the camp, and the cultist spawn anchors so nothing walls
    # off and the cover weave stays legible.
    _scatter = random.Random(88)
    _anchor_set = set(_ANCHORS)

    def _near_building(tx, ty):
        for oy in range(ty - 1, ty + 2):
            for ox in range(tx - 1, tx + 2):
                if (0 <= oy < h and 0 <= ox < w
                        and objects_l[oy][ox] in ("W", "r", "i")):
                    return True
        return False

    for ty in range(7, h - 7):
        for tx in range(7, w - 7):
            if objects_l[ty][tx] != "." or floor_ll[ty][tx] != "g":
                continue
            if _border_protected(tx, ty):
                continue
            if 8 <= tx <= 20 and 27 <= ty <= 40:          # the stealth glade
                continue
            if 38 <= tx <= 46 and 46 <= ty <= 54:         # the camp clearing
                continue
            if (tx, ty) in _anchor_set or _near_building(tx, ty):
                continue
            if _scatter.random() < 0.07:
                objects_l[ty][tx] = "p" if _scatter.random() < 0.45 else "T"

    # Stamp the permeable forest band on top of everything else.
    _band_bushes = []
    from .base import scatter_forest_band
    scatter_forest_band(floor_ll, objects_l, w, h,
                        depth=BAND_DEPTH, seed=53,
                        protected=_border_protected,
                        place_bush=lambda px, py:
                            _band_bushes.append((px, py)))
    # Fold guarantee: the band's de-clump skips the OUTERMOST ring, but
    # Brimley wraps on both axes -- an edge tree with no walkable neighbour
    # would block the torus crossing at that tile. Flip any such edge solid
    # to a passable tree ('p', identical-looking) so the wrap is never a
    # solid wall. Wrap-aware neighbour test.
    from .base import is_object_solid as _isolid, is_floor_solid as _fsolid
    def _blocks(tx, ty):
        return _isolid(objects_l[ty][tx]) or _fsolid(floor_ll[ty][tx])
    for ty in range(h):
        for tx in range(w):
            if not (tx in (0, w - 1) or ty in (0, h - 1)):
                continue
            if objects_l[ty][tx] != "T":
                continue
            nb = [((tx + 1) % w, ty), ((tx - 1) % w, ty),
                  (tx, (ty + 1) % h), (tx, (ty - 1) % h)]
            if not any(not _blocks(nx, ny) for nx, ny in nb):
                objects_l[ty][tx] = "p"
    floor_rows = ["".join(r) for r in floor_ll]

    objects = ["".join(r) for r in objects_l]

    sc = Scene("brimley", floor_rows, objects, music="wind")
    # The church-door point the pealing bell broadcasts from
    # (Game._tick_bell): cult hunters converge here while it rings.
    sc._bell_door = (church_out[0] * TILE + 16,
                     church_out[1] * TILE + 16)
    for bx, by in _band_bushes:
        sc.add_decoration(Decoration(bx, by, "bush"))
    # Brimley's world is toroidal on both axes -- the fold-road at row 25
    # wraps east-west; the perimeter forest wraps north-south.
    sc.wrap_x = True
    sc.wrap_y = True
    sc.add_exit("4", "country_lane",      "from_brimley")
    sc.add_exit("m", "church",            "from_brimley")
    sc.add_exit("o", "abandoned_farmhouse", "from_brimley")
    sc.add_exit("J", "toby_house",        "from_brimley")
    sc.add_exit("n", "barn",              "from_brimley")
    sc.add_exit("y", "sheriff_office",    "from_brimley")
    sc.add_exit("D", "shop",              "from_brimley")
    sc.add_exit("B", "schoolhouse",       "from_brimley")
    # NOTE the char: "R" is a SOLID rock in OBJECT_DEFS, so using it as an
    # exit made the north road out of town an invisible wall you bumped into
    # rather than a passage you walked onto (2026-07: found by walking it).
    # "^" is an outdoor_passage, like every other road exit in the game.
    sc.add_exit("^", "gravel_road_north", "from_brimley")
    sc.add_exit("M", "cornfield_maze",    "from_brimley_south")

    clearing_tx, clearing_ty = 10, 50
    objects_list = [list(r) for r in objects]
    objects_list[clearing_ty][clearing_tx] = "j"
    # Gravel road passage (north) on the east bank. Three tiles wide so you
    # can walk onto it without threading a needle, like the other passages.
    for _rx in (49, 50, 51):
        objects_list[0][_rx] = "^"
    # The fold road -- gaps in both tree walls at row 25 so the road can be
    # walked across the map east-to-west; wrap_x carries the seam.
    objects_list[25][0] = "."
    objects_list[25][w - 1] = "."
    # ---- The dead lots: the abandoned cars ----
    # Everyone drove into Brimley and nothing with an engine leaves, so the
    # cars pool where their drivers finally stopped: a rank beside the barn,
    # a give-up line on the fold-road shoulders, and a nose in the corn.
    _lot_cars = dead_cars(objects_list, [
        # the barn rank, noses at the barn's south wall (clear of the west door)
        (21, 13, "rust_coupe", 0.55, 24, "h"),
        (23, 13, "rust_wagon", -0.08, 22, "h", {"luggage": True}),
        # the give-up line on the fold-road shoulders (east of the bridge)
        (36, 23, "rust_wagon", 0.10, 31, "h"),
        (40, 23, "rust_coupe", -0.12, 32, "h"),
        (38, 27, "rust_van", 3.05, 33, "h"),
        # a nose in the corn on the east bank
        (46, 14, "rust_sedan", 0.35, 41, "h"),
    ])
    # South exit to cornfield_maze (the bottom of the loop): the spine
    # cuts down through the southern tree wall via a single 'M' tile.
    objects_list[h - 1][20] = "M"
    sc.objects = objects_list
    for _d in _lot_cars:
        sc.add_decoration(_d)
    sc.add_exit("j", "clearing", "from_brimley")

    # ---- Spawns ----
    sc.set_spawn("default", 57, 25)
    sc.set_spawn("from_country_lane", 57, 25)
    sc.set_spawn("from_lodge_yard", 57, 25)
    # (legacy) the woodshed door consolidated into the lodge yard; the
    # spawn survives on the east square in case anything routes here.
    sc.set_spawn("from_woodshed", 50, 21)
    sc.set_spawn("from_gravel_road", 50, 2)
    sc.set_spawn("from_cornfield_maze", 22, 1)
    sc.set_spawn("from_cornfield_path", 36, 1)
    sc.set_spawn("from_clearing", clearing_tx + 1, clearing_ty)
    sc.set_spawn("from_church",     *church_out)
    sc.set_spawn("from_sheriff_office", *sheriff_out)
    sc.set_spawn("from_abandoned_farmhouse", *farm_out)
    sc.set_spawn("from_shop",              *shop_out)
    sc.set_spawn("from_toby_house",         *kid_out)
    sc.set_spawn("from_barn",              *barn_out)
    sc.set_spawn("from_school",            *school_out)

    # ---- Ambience -- crows + grass tufts ----
    sc.add_decoration(Decoration(22 * TILE + 16, 15 * TILE + 16, "crow"))
    sc.add_decoration(Decoration(40 * TILE + 16, 30 * TILE + 16, "crow"))
    sc.add_decoration(Decoration(48 * TILE + 16, 45 * TILE + 16, "crow"))
    # Creepy bank dressing.
    sc.add_decoration(Decoration(35 * TILE + 16, 32 * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(28 * TILE + 16, 40 * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(43 * TILE + 16, 50 * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(36 * TILE + 16, 34 * TILE + 16, "hanging_figure"))
    sc.add_decoration(Decoration(46 * TILE + 16, 46 * TILE + 16, "hanging_figure"))
    sc.add_decoration(Decoration(33 * TILE + 16, 20 * TILE + 16, "dead_crow"))
    sc.add_decoration(Decoration(52 * TILE + 16, 50 * TILE + 16, "dead_crow"))
    # A WHIRLPOOL in the river: where the surface water drains down the
    # sink to the one running under the town (NARRATIVE §2: the river is
    # the artery the diggers followed to the door). Cold mist.
    _whirl_row = 38
    _whirl_col = _river_cols(_whirl_row)[1]
    sc.add_decoration(Decoration(_whirl_col * TILE + 16, _whirl_row * TILE + 16,
                                 "swallow_hole"))
    for _mx, _my in [(_whirl_col - 1, _whirl_row - 1),
                     (_whirl_col + 1, _whirl_row + 1)]:
        sc.add_decoration(Decoration(_mx * TILE + 16, _my * TILE + 8, "mist"))
    # The clearing-entrance threshold -- creepy_tree on the j tile, a
    # single bloody handprint, a candle melted to a stone at the foot.
    sc.add_decoration(Decoration(clearing_tx * TILE + 16,
                                 clearing_ty * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration((clearing_tx + 1) * TILE + 16,
                                 clearing_ty * TILE + 16, "bloody_handprint"))
    sc.add_decoration(Decoration((clearing_tx + 1) * TILE + 16,
                                 clearing_ty * TILE + 8, "candle"))
    # Watching-wound marks scattered near the buildings.
    for (mx, my) in [(3, 46), (2, 50),          # near sheriff / clearing
                     (27, 24), (52, 42)]:        # near river / kid's house
        sc.add_decoration(Decoration(mx * TILE + 24, my * TILE + 16,
                                     "watching_wound", size="small"))
    sc.add_decoration(Decoration(45 * TILE + 16, 45 * TILE + 16, "phantom_mark"))
    for tx, ty in [(20, 30), (34, 28), (46, 30), (52, 24),
                   (14, 45), (40, 40)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "grass_tuft"))
    # Tufts through each corn-cover patch so the ':' floor reads as field.
    rng_corn = random.Random(4242)
    for (pl, pt, pr, pb) in corn_patches:
        for _ in range(max(5, (pr - pl) * (pb - pt) // 7)):
            gx = rng_corn.randint(pl, pr) * TILE + rng_corn.randint(2, 28)
            gy = rng_corn.randint(pt, pb) * TILE + rng_corn.randint(2, 28)
            sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    for tx, ty, kind in [(19, 28, "dead_crow"), (5, 38, "creepy_tree"),
                         (34, 46, "hanging_figure"), (43, 10, "creepy_tree"),
                         (52, 30, "dead_crow"), (28, 44, "creepy_tree")]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16, kind))

    # ---- Brimley's people ----
    def _resident(tx, ty, name, kind, pages=None, movement="wander",
                  voice="blip_mid", radius=52, fold=False, beats=None,
                  stations=None, convo=None, vanish=True):
        if convo is not None:
            dfn = chorus_dialogue(convo, beats or ())
        else:
            dfn = _brimley_voice(pages, voice, fold=fold, beats=beats)
        n = NPC(tx * TILE + 16, ty * TILE + 16, name, kind,
                dialogue_fn=dfn,
                movement=movement, radius=radius)
        n._hb_vanish = vanish
        if stations:
            n.movement = "worker"
            n.stations = [{"x": sx * TILE + 16, "y": sy * TILE + 16,
                           "dwell": dw, "face": fc}
                          for (sx, sy, dw, fc) in stations]
        sc.add_npc(n)

    # Hettie keeps the shop open. A homebody: she steps out front to sweep
    # a step that doesn't get dirty, then ducks back inside for a spell.
    _resident(shop_out[0], shop_out[1], "Hettie", "hettie", [
        "Still open. Always open. The shelves don't empty anymore. Have you noticed.",
        "No deliveries. In a while now. But we manage. We always.",
        "I keep the lights on. So they know. Someone's keeping them on.",
    ], movement="homebody", radius=34)
    # Old Pell -- BESIDE the schoolhouse door (2 tiles east of the step), his
    # unopened seed corn beside him. He never ducks inside (the schoolhouse is
    # enterable and empty), and he no longer stands ON the door: his home is
    # clear of the door tile, its approach, and the return spawn, so he never
    # blocks the way in (play-notes: no NPC on a door or its approach).
    _resident(school_out[0] + 2, school_out[1], "Old Pell", "old_townsman",
              movement="homebody", radius=34, convo=PELL_CONVO,
              vanish=False,
        beats=[
            # The newspaper's ripple (TODO #2): once the PI has spent the
            # one copy on him, the sewn-shut stoop line would be a lie --
            # he has cut a sack open. The sown beat fires first and the
            # coal beat stands down for good.
            ("beat_pell_marked",
             lambda g: g.save.arg("paper_given") == "pell", [
                 "Cut the string on a sack this morning. First one "
                 "since the winter.",
                 "[c=dim]Can't say I'll get a crop out of it. Can't say "
                 "I won't. I'll put a few rows in and see.[/c]",
             ]),
            ("beat_pell_coal",
             lambda g: (g._evidence_count() >= 1
                        and g.save.arg("paper_given") != "pell"), [
                 "You've been digging at it. I can tell. It's on you like "
                 "coal dust.",
                 "Whatever you're finding out there, don't bring it up my step. I've got my seed where I want it. Sewn shut. Some of us need it left that way.",
             ]),
        ])
    # Mrs. Calder -- by the east-bank square. She sets a place for a guest
    # she can't name. She watches the road. She does not wave.
    _resident(50, 22, "Mrs. Calder", "townswoman",
              movement="idle", convo=CALDER_CONVO,
        beats=[("beat_calder_unlatched",
                lambda g: g._evidence_count() >= 1, [
            "Closer now. Whoever the place is set for. An old woman can "
            "feel a knock coming before it lands.",
            "I've started leaving the door unlatched at night. It seemed... polite.",
        ])])
    # Royce -- by the river bridge. He tried to drive out like everyone
    # did; the corn handed him back. He clings to the one fact: you got IN.
    _resident(28, 26, "Royce", "royce",
              convo=ROYCE_CONVO,
        stations=[(28, 26, (5.0, 9.0), (1, 0)),
                  (27, 27, (3.0, 6.0), (-1, 0)),
                  (28, 22, (4.0, 7.0), (0, -1))],
        beats=[("beat_royce_throat",
                lambda g: g._evidence_count() >= 2, [
            "You're still here. Course you're still here.",
            "I keep turning it over. Every road out of Brimley hands you back. Except the one that carried you in. If a door only opens the one way, mister, it isn't a door.",
            "[c=dim]It's a throat.[/c]",
        ])])
    # Garrick -- the old man at the well, town square, watching who comes
    # and goes. The law is hollow now; he says so plainly.
    _resident(50, 18, "Garrick", "old_townsman",
              convo=GARRICK_CONVO,
        stations=[(50, 18, (6.0, 10.0), (1, 0)),
                  (52, 16, (4.0, 8.0), (0, -1)),
                  (49, 20, (4.0, 7.0), (1, 0))],
        beats=[("beat_garrick_quiet",
                lambda g: g.save.flag("preacher_body_seen"), [
            "The reverend's gone quiet. Any other week you'd hear him "
            "clear from here, worked up over something or other.",
            "Nothing out of him for days now. Man spends his life raising his voice, then nothing at all.",
            "You go by and look in on him, son. Somebody ought to.",
        ])])

    # ---- Run-down + cult presence among the buildings ----
    sc.add_decoration(Decoration(22 * TILE + 16, 23 * TILE + 16, "yellow_sign"))
    sc.add_decoration(Decoration(10 * TILE + 20, 24 * TILE + 16, "yellow_sign"))
    sc.add_decoration(Decoration(23 * TILE + 16, 23 * TILE + 16, "dead_crow"))
    sc.add_decoration(Decoration(47 * TILE + 16, 41 * TILE + 16, "dead_crow"))
    sc.add_decoration(Decoration(22 * TILE + 16, 23 * TILE + 8, "bloody_handprint"))
    sc.add_decoration(Decoration(45 * TILE + 16, 34 * TILE + 16, "hanging_figure"))

    # ---- The loop, made visible ----
    # The payphone (won't connect), the news rack (seal-day paper), a
    # stopped calendar, the well, the noticeboard, Mrs. Calder's plate.
    _pp_x, _pp_y = 13 * TILE + 16, 23 * TILE + 16
    sc.add_decoration(Decoration(_pp_x, _pp_y, "payphone"))
    sc._payphone_pos = (_pp_x, _pp_y)
    # Burn barrels at the occupied yards -- the only warm light on the banks.
    for _bx, _by, _bs in ((49, 20, 61), (11, 23, 62), (47, 42, 63)):
        sc.add_decoration(Decoration(_bx * TILE + 16, _by * TILE + 16,
                                     "burn_barrel", seed=_bs))
    # The news rack outside the shop (its south front, onto the fold road),
    # still holding the seal-day issue.
    _nr_x, _nr_y = 12 * TILE + 16, 23 * TILE + 16
    sc.add_decoration(Decoration(_nr_x, _nr_y, "news_rack"))
    sc._news_rack_pos = (_nr_x, _nr_y)
    # The well -- dread set-dressing, not a way down (a dead town shaft;
    # the descent is the cult's dug mine at the grove, reached by the rite).
    # Sits in the eastern square, north of the lodge-road entry.
    well_x, well_y = 52 * TILE + 16, 17 * TILE + 16
    sc.add_decoration(Decoration(well_x, well_y, "well"))
    sc._well_pos = (well_x, well_y)
    # A wheelbarrow of "rusted" tools left by the square (the shed that
    # stood here is gone, but the cleaned tools remain -- the
    # contradiction is the point, still an evidence beat).
    barrow_x, barrow_y = 49 * TILE + 16, 18 * TILE + 16
    sc.add_decoration(Decoration(barrow_x, barrow_y, "wheelbarrow"))
    sc._barrow_pos = (barrow_x, barrow_y)
    sc.add_decoration(Decoration(8 * TILE + 16, 23 * TILE + 16, "missing_flyer"))
    # Old Pell's SEED CORN, still sewn shut on its pallet by his step
    # (TODO #28, replacing the stopped calendar). It is April: a corn man
    # who has not opened his seed has not started the year. His refusal to
    # mark time, said in his own trade instead of on a prop every room in
    # town also had.
    # Nailed to the schoolhouse wall beside the (south) door.
    # Two tiles east of Pell himself and four clear of the schoolhouse door,
    # on the grass above the road so it reads from the lane: a solid pallet
    # dropped on his own tile would stand inside the man.
    sc.add_decoration(Decoration(26 * TILE + 16, 23 * TILE + 12,
                                 "seed_corn"))
    sc.add_decoration(Decoration(54 * TILE + 16, 30 * TILE + 16, "pickup_truck"))

    # Mrs. Calder's table, laid out in the open by the kid's house: two
    # settings (hers, and the extra she lays every night for the guest she
    # can't name), a candle burned down, a chair knocked over.
    sc.add_decoration(Decoration(42 * TILE + 10, 42 * TILE + 12, "place_setting"))
    sc.add_decoration(Decoration(42 * TILE + 24, 42 * TILE + 12, "place_setting"))
    sc.add_decoration(Decoration(42 * TILE + 16, 42 * TILE + 2, "candle"))
    sc.add_decoration(Decoration(42 * TILE + 28, 44 * TILE + 12, "overturned_chair"))

    # ---- Gardens, on some lots and not others (food scarcity) ----
    sc.add_decoration(Decoration(int(43.5 * TILE), 41 * TILE, "garden_patch",
                                 tended=True, w=110, h=72, seed=41))
    sc.add_decoration(Decoration(int(25.5 * TILE), 49 * TILE,
                                 "garden_patch",
                                 tended=False, w=100, h=64, seed=42))

    # ---- The churchyard -- the too-even graves of the vanished ----
    hs = random.Random(91)
    for ry_ in (14, 16):
        for cx_ in (5, 7, 9, 11):
            sc.add_decoration(Decoration(
                cx_ * TILE + 16 + hs.randint(-6, 6),
                ry_ * TILE + 16 + hs.randint(-4, 4),
                "headstone", seed=hs.randint(0, 9999)))
    sc.add_decoration(Decoration(7 * TILE + 16, 14 * TILE + 6, "dead_crow"))
    sc.add_decoration(Decoration(9 * TILE + 16, 16 * TILE + 6, "crow"))

    # ---- Light is the mood: the town runs on electric, off gasoline ----
    # A gas GENERATOR tucked outside each occupied building. The fold cut
    # Brimley off the grid with everything else (NARRATIVE §1), so the town
    # keeps the lights on off gas now; a genset MUST sit outdoors (exhaust),
    # so it fronts the door and throws a small warm work-light across the
    # threshold (the pool the door lantern used to). Placed one tile off the
    # door -- the provenance behind the town's lights.
    for (lx, ly) in [(church_out[0], church_out[1] + 1),
                     (barn_out[0], barn_out[1] + 1),
                     (shop_out[0] - 1, shop_out[1]),     # beside the S door
                     (school_out[0] - 1, school_out[1]),  # beside the S door
                     (sheriff_out[0], sheriff_out[1] + 1),
                     (farm_out[0], farm_out[1] + 1),
                     (kid_out[0] + 1, kid_out[1])]:
        sc.add_decoration(Decoration(lx * TILE + 20,
                                     ly * TILE + 16, "generator"))
    # The bridge keeps a single HUNG lantern on the exposed crossing (a
    # personal light, not the civic grid), a creepy_tree on each bank for a
    # held-breath pocket.
    sc.add_decoration(Decoration(river_center_x * TILE + 16,
                                 26 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(34 * TILE + 16, 22 * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(27 * TILE + 16, 28 * TILE + 16, "creepy_tree"))

    # ---- Main-road waymarks: signs + the yard-light thread to follow ----
    # Dusk-to-dawn mercury-vapor yard lights on poles: the period-correct
    # civic light of a 1994 northern-Minnesota town, spaced far apart the way
    # farmstead yard lights are. Their glow is COLD blue-white, the deliberate
    # opposite of the warm fire the banks huddle at (burn barrels, braziers).
    sc.add_decoration(Decoration(56 * TILE + 16, 27 * TILE + 16, "town_sign",
                                 text="BRIMLEY", welcome=False))
    sc.add_decoration(Decoration(51 * TILE + 16, 24 * TILE + 20, "town_sign",
                                 text="TOWN", welcome=False))
    sc.add_decoration(Decoration(18 * TILE + 16, 26 * TILE + 16, "town_sign",
                                 text="TOWN", welcome=False))
    for lx in (8, 20, 40, 52):                  # yard lights on the E-W spine
        sc.add_decoration(Decoration(lx * TILE + 16, 24 * TILE + 16,
                                     "yard_light"))
    sc.add_decoration(Decoration(53 * TILE + 16, 18 * TILE + 16, "yard_light"))
    sc.add_decoration(Decoration(16 * TILE + 16, 15 * TILE + 16, "yard_light"))
    sc.add_decoration(Decoration(16 * TILE + 16, 38 * TILE + 16, "yard_light"))

    # Break the tidy boxes: a tipped wheelbarrow by the store, a dead
    # filling-station pump on the lane, mud tracked off the path.
    sc.add_decoration(Decoration(14 * TILE + 16, 23 * TILE + 16, "wheelbarrow"))
    sc.add_decoration(Decoration(19 * TILE + 16, 30 * TILE + 16, "gas_pump"))
    sc.add_decoration(Decoration(16 * TILE + 16, 28 * TILE + 16, "mud_footprint"))

    # Weeds reclaiming the foundations -- tufts crowding the ground just
    # OUTSIDE the walls, so the wall meets the ground in an overgrown line.
    weeds = random.Random(317)

    def _weed(px, py):
        tx, ty = int(px // TILE), int(py // TILE)
        if 0 <= ty < h and 0 <= tx < w and sc.objects[ty][tx] == ".":
            sc.add_decoration(Decoration(px, py, "grass_tuft"))

    for (bl, br, bt, bb) in [(church_left, church_right, church_top, church_bot),
                             (barn_left, barn_right, barn_top, barn_bot),
                             (shop_left, shop_right, shop_top, shop_bot),
                             (school_left, school_right, school_top, school_bot),
                             (sheriff_left, sheriff_right, sheriff_top, sheriff_bot),
                             (farm_left, farm_right, farm_top, farm_bot),
                             (kid_left, kid_right, kid_top, kid_bot)]:
        for _ in range(6):
            _weed(weeds.randint(bl, br) * TILE + weeds.randint(2, 28),
                  (bb + 1) * TILE + weeds.randint(2, 16))
        for _ in range(4):
            ry2 = weeds.randint(bt, bb) * TILE + weeds.randint(2, 28)
            _weed((bl - 1) * TILE + weeds.randint(16, 28), ry2)
            _weed((br + 1) * TILE + weeds.randint(2, 14), ry2)

    # Tall-grass meadows scattered across the open ground (pure decoration;
    # the player walks through them). Seeded stable across loads.
    meadow_rng = random.Random(8419)
    placed = 0
    attempts = 0
    while placed < 70 and attempts < 900:
        attempts += 1
        tx = meadow_rng.randint(2, w - 3)
        ty = meadow_rng.randint(2, h - 3)
        if sc.objects[ty][tx] != ".":
            continue
        if tx >= 47 and 12 <= ty <= 22:              # keep the well square clear
            continue
        if river_center_x - 4 <= tx <= river_center_x + 4:
            continue                                 # avoid the river corridor
        px = tx * TILE + meadow_rng.randint(4, 28)
        py = ty * TILE + meadow_rng.randint(4, 28)
        sc.add_decoration(Decoration(px, py, "tall_grass"))
        placed += 1

    # A dead grove on the bare bank -- leafless trees in the open, a focal
    # dread that offers no cover.
    for (gx, gy) in [(4, 34), (6, 36), (3, 38), (7, 39), (5, 41)]:
        sc.add_decoration(Decoration(gx * TILE + 16, gy * TILE + 16, "creepy_tree"))
    # A cult standing-stone ring in the open north-east field, a Yellow
    # Sign cut into the ground at its centre, lit by two braziers.
    for (px, py) in [(38, 14), (42, 14), (40, 13),
                     (37, 17), (43, 17), (40, 19)]:
        sc.add_decoration(Decoration(px * TILE + 16, py * TILE + 16,
                                     "standing_stone", seed=px * 7 + py))
    sc.add_decoration(Decoration(40 * TILE + 16, 16 * TILE + 16, "yellow_sign"))
    sc.add_decoration(Decoration(38 * TILE + 16, 16 * TILE + 16, "brazier"))
    sc.add_decoration(Decoration(42 * TILE + 16, 16 * TILE + 16, "brazier"))
    # The church steeple -- the one tall thing for miles, a landmark to
    # orient by, rising over the roof into the treeline.
    sc.add_decoration(Decoration(8 * TILE + 16, (church_top + 1) * TILE + 16,
                                 "steeple", rise=50, depth_bias=170))
    # A brazier marking the burn-clearing threshold.
    sc.add_decoration(Decoration((clearing_tx + 3) * TILE + 16,
                                 clearing_ty * TILE + 16, "brazier"))
    # A murder of crows posted along the treeline, watching.
    for (cx, cy) in [(2, 20), (2, 44), (30, 2), (52, 8), (57, 40), (28, 57)]:
        sc.add_decoration(Decoration(cx * TILE + 16, cy * TILE + 16,
                                     "dead_crow" if (cx + cy) % 2 else "crow"))

    # ---- Lived-in town dressing ----
    # The "Welcome to Brimley" sign by the east-edge lodge road, the first
    # lived-in detail the arriving PI sees.
    # It FACES EAST, at the traffic it greets. The board only had a front
    # and a back once it stopped being painted on both sides, so which way
    # it points became a real question: the PI drives in from the lodge
    # road on the east, and a welcome board a driver reads from behind is
    # not a welcome board.
    sc.add_decoration(Decoration(55 * TILE + 16, 23 * TILE + 16,
                                 "town_sign", text="BRIMLEY",
                                 yaw=math.pi / 2))
    # Schoolhouse flagpole -- flag at half-mast, faded, frayed (by its
    # south front now).
    sc.add_decoration(Decoration(20 * TILE + 16, 23 * TILE + 16, "flagpole"))
    # The community noticeboard at the well -- three flyers tacked tight
    # (the yard light in the lodge square throws over them now).
    for (fx, fy) in [(54 * TILE + 4, 16 * TILE + 22),
                     (54 * TILE + 16, 16 * TILE + 22),
                     (54 * TILE + 28, 16 * TILE + 22)]:
        sc.add_decoration(Decoration(fx, fy, "missing_flyer"))

    # ---- Placed noisemakers ----
    # The stalled pickup's cab radio: an E-toggleable lure.
    sc.add_noise_source(
        54 * TILE + 16, 31 * TILE + 16, "radio", sfx="radio_snatch",
        on_notice="The truck radio catches. A dead station rolls out "
                  "over the street.",
        off_notice="You kill the radio.",
        silenced_notice="The music stops dead.")
    sc.add_noise_trap(53 * TILE + 16, 31 * TILE + 24, "glass", seed=7)
    sc.add_noise_trap(23 * TILE + 16, 23 * TILE + 16, "cans", seed=8)
    sc.add_noise_trap(40 * TILE + 16, 20 * TILE + 16, "crow", seed=9)

    # ---- The cult's errands (Scene.add_cult_station) ----
    # The roaming regulars have JOBS: kneel at the stone ring, look in on
    # the well, stand over Mrs. Calder's laid table.
    sc.add_cult_station(40 * TILE + 16, 16 * TILE + 16, pose="kneel",
                        face=(0, -1), dwell=(6.0, 10.0))
    sc.add_cult_station(52 * TILE + 16, 18 * TILE + 16,
                        face=(1, 0), dwell=(4.0, 7.0))
    sc.add_cult_station(42 * TILE + 16, 43 * TILE + 16,
                        face=(0, -1), dwell=(5.0, 9.0))

    # ---- Cult-taken territory: the farmhouse's WEST front yard ----
    # The door fronts west now, so the "kept" attention (sigils, candles,
    # the brazier lighting the way in) lines the west approach.
    fox, foy = farm_out
    sc.add_decoration(Decoration(fox * TILE + 16, (foy - 2) * TILE + 16,
                                 "yellow_sign"))
    sc.add_decoration(Decoration(fox * TILE + 16, (foy + 2) * TILE + 16,
                                 "yellow_sign"))
    for (cx, cy) in [(fox - 1, foy - 1), (fox - 2, foy), (fox - 1, foy + 1)]:
        sc.add_decoration(Decoration(cx * TILE + 16, cy * TILE + 16,
                                     "candle"))
    sc.add_decoration(Decoration((fox - 3) * TILE + 16, foy * TILE + 16,
                                 "brazier"))

    # ---- Mist + marsh wisps ----
    for (mtx, mty, mw, mh) in [(30, 32, 90, 64), (30, 44, 90, 72),
                               (7, 46, 112, 72), (37, 44, 104, 64),
                               (48, 48, 104, 64), (38, 16, 96, 64)]:
        sc.add_decoration(Decoration(mtx * TILE + 16, mty * TILE + 16,
                                     "mist", w=mw, h=mh))
    for (wtx, wty) in [(7, 46), (37, 44), (48, 49), (38, 16)]:
        sc.add_decoration(Decoration(wtx * TILE + 16, wty * TILE + 16, "wisp"))

    # Ambient sky + wind.
    for (ftx, fty) in [(30, 12), (48, 34), (14, 40)]:
        sc.add_decoration(Decoration(ftx * TILE + 16, fty * TILE + 16, "flock"))
    for (ltx, lty) in [(20, 32), (34, 30), (44, 28), (14, 34),
                       (40, 42), (52, 38)]:
        sc.add_decoration(Decoration(ltx * TILE + 16, lty * TILE + 16, "leaves"))

    # ---- Surface enclosed cover (DESIGN.md §12) ----
    # The corn and tree lines are the CONCEALMENT out here; the one rooted
    # set-piece hide is the gap under the dead pickup's bed.
    sc.hide_spots = [
        (53 * TILE + 16, 31 * TILE + 8, "under"),
        # The 2026-07 stealth pass (TODO #5): a second rooted hide on the
        # east bank, under Mrs. Calder's outdoor supper table.
        (42 * TILE + 16, 43 * TILE + 16, "under"),
    ]

    # UNDER THE BRIDGE (TODO #5, maintainer pick): the mud shelf at the
    # span's east foot, tucked beneath the deck head. Everything in
    # Brimley crosses that bridge sooner or later; while you are under
    # it, whatever crosses knocks on the planks over your head
    # (Game._tick_bridge_knocks reads the deck band stored here).
    _deck_cols = [c for c in range(sc.w) if sc.objects[25][c] == "$"]
    if _deck_cols:
        _bc = max(_deck_cols) + 1
        if sc.floor[27][_bc] not in ("~", "@"):
            _bhx, _bhy = _bc * TILE + 16, 27 * TILE + 16
        else:
            _bc = min(_deck_cols) - 1
            _bhx, _bhy = _bc * TILE + 16, 27 * TILE + 16
        sc.hide_spots.append((_bhx, _bhy, "under"))
        sc._bridge_hide_px = (_bhx, _bhy)
        sc._bridge_deck_px = (min(_deck_cols) * TILE,
                              (max(_deck_cols) + 1) * TILE,
                              24 * TILE, 27 * TILE)

    # River stones scattered along both banks (TODO #5, the distraction
    # verb): the river gives stones. Placed by scan because the water
    # meanders; one per row, alternating banks, skipping the bridge rows.
    for _i, _row in enumerate((18, 28, 33, 41, 48)):
        _water = [c for c in range(26, 36)
                  if sc.floor[_row][c] in ("~", "@")]
        if not _water:
            continue
        _c = (min(_water) - 1) if _i % 2 == 0 else (max(_water) + 1)
        _wx, _wy = _c * TILE + 16, _row * TILE + 16
        if (sc.floor[_row][_c] not in ("~", "@")
                and not sc.is_solid_at(_wx, _wy)):
            sc.add_item(_wx, _wy, "stone")

    # The dead pickup is a big hulk -- solid tiles under its length so the
    # player can't walk through it (decoration at tile 54,30).
    objects_list = [list(r) for r in sc.objects]
    for cx in (52, 53, 54, 55):
        if 0 <= cx < sc.w:
            objects_list[30][cx] = "X"
    sc.objects = objects_list
    # Mrs. Calder's outdoor supper table as a real furniture volume, her
    # two place settings + candle seated on its top (2026-07 audit fix: it
    # was a raw 't' object tile, which no tilt set draws -- the settings
    # and candle sat on bare ground over an invisible collision block).
    sc.add_furniture("table", [(42, 42)], w=30, h=26)

    # ---- The cult camp footprint + the cultist spawn pool ----
    # The camp sits in the SE corn. At 0 evidence it is just a stand of corn
    # (only the trees are pre-cleared, so the spawn anchors + tend station stay
    # reachable); the WORN PACKED GROUND is not beaten in until the cult sets
    # the camp up at 1 evidence (_raise_cult_camp), so the ground itself is
    # their doing, not there before them.
    _camp_tx, _camp_ty = 42, 51
    for cy in range(_camp_ty - 2, _camp_ty + 2):
        for cx in range(_camp_tx - 2, _camp_tx + 3):
            if 0 <= cy < h and 0 <= cx < w and sc.objects[cy][cx] in ("T", "p"):
                sc.objects[cy][cx] = "."
    sc._camp_pos = (_camp_tx * TILE + 16, _camp_ty * TILE + 16)
    # A roamer tends the camp fire (an errand station just south of it, facing
    # the flames). Only occupied once the cult wakes and fills the pool.
    sc.add_cult_station(_camp_tx * TILE + 16, (_camp_ty + 1) * TILE + 16,
                        face=(0, -1), dwell=(8.0, 14.0))
    # Hand-placed cultist spawn ANCHORS (the maintainer's marks): the cult
    # ENTERS from these when it wakes (1 evidence) and roams normally (it is
    # NOT static). The scene keeps `cult_target` filled, prefilled on entry
    # from the farthest unoccupied anchors (systems/threat_mixin
    # _ensure_cultists / _spawn_cultist from_pool). 14 anchors, 10 kept.
    sc.cult_target = 10
    sc.cult_spawns = [(tx * TILE + 16, ty * TILE + 16) for (tx, ty) in _ANCHORS]

    def _brimley_interact(game):
        # The well -- dread set-dressing, fully SEVERED from the descent:
        # nobody went down HERE. The congregation went down the cult's dug
        # mine out at the grove, reached now only by the rite. This well is
        # a dead, dry town well gone wrong -- ominous, going nowhere.
        wx, wy = sc._well_pos
        if abs(game.player.x - wx) < 36 and abs(game.player.y - wy) < 36:
            if (game.save.flag("well_examined")
                    and game.player.inventory.count("stone") > 0):
                # A stone over the lip (TODO #5, the distraction verb):
                # the knocks fall away, the shaft's rattle carries across
                # the square -- and no bottom ever sounds. WORDLESS by
                # design (the missing landing IS the beat; the well stays
                # the bottomless dread it is).
                game.player.inventory.remove("stone", 1)
                game.audio.play("bump", 0.5)
                game._echoes.extend([
                    {"t": 0.35, "x": wx, "y": wy, "vol": 0.34},
                    {"t": 0.80, "x": wx, "y": wy, "vol": 0.22,
                     "emit": True},
                    {"t": 1.45, "x": wx, "y": wy, "vol": 0.12},
                ])
                return
            if not game.save.flag("well_examined"):
                game.save.set_flag("well_examined", True)
                game.audio.play("low_pulse", 0.4)
                game.dialog.show([
                    "[c=dim](You lean over the lip. The shaft drops "
                    "past where any water should be. No glint, no "
                    "bottom, just cold air climbing up out of it.)[/c]",
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
                _evidence(game, "barrow_tools",
                          "Digging tools left in the barrow, rusted over. "
                          "The edges are still bright.")
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
        # The payphone examine was CUT (play-notes): the dead phone stays as
        # silent set-dressing (the prop), but the narrator no longer says its
        # line for you. It carries no evidence or pointer, so nothing is lost.
    sc.add_interactable(sc._well_pos[0], sc._well_pos[1], 36)
    sc.add_interactable(sc._barrow_pos[0], sc._barrow_pos[1], 36)
    sc.add_interactable(sc._news_rack_pos[0], sc._news_rack_pos[1], 36)

    sc.on_interact_fn = _brimley_interact

    # The Preacher's end: the doom sends Crane out of his church, down to
    # the river after his flock. His remains lie on the west bank (the
    # cross; a case note, not counted evidence). Re-laid every entry.
    sc._preacher_bank_pos = (27 * TILE + 16, 30 * TILE + 16)
    sc.on_enter_fn = _brimley_on_enter
    sc.on_update_fn = _brimley_update
    return sc
