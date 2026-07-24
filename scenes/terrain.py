"""Tile definitions + all terrain drawing (flat + tilted camera),
split out of scenes/base.py (2026-07). base.py imports and re-exports
every name defined here, so ``from scenes.base import <x>`` is
unchanged. This module depends only on ``constants`` and (lazily, inside
function bodies) the scene registry + rendering.* -- never on the Scene
class, so there is no import cycle with base."""
import math
import random
import pygame
from constants import SCREEN_W, SCREEN_H, TILE
from rendering.sight import SIGHT_EYE_H as _SIGHT_EYE_H


# ---- Darkwood lighting / shadow helpers ----
# Cheap, cached surfaces that turn the flat tile grid into something
# with depth and mood: soft contact shadows ground props, warm light
# pools relieve the dark, and a gradient strip casts wall shadows onto
# the floor below them.
_SHADOW_CACHE = {}

# Per-tile floor cache (see draw_scene_terrain). Floor rasterisation is a
# pure function of (ch, tx, ty) except the animated river/void tiles, so we
# render each tile once and blit it. Keyed by (ch, tx, ty); dropped wholesale
# when the active scene changes so it never grows past one scene's tiles.
_FLOOR_CACHE = {}
_FLOOR_CACHE_SCENE = None
_ANIM_FLOOR = frozenset({"~", "@"})   # floor chars that animate per frame


def _ground_shadow(surf, cx, cy, rw, rh, alpha=80):
    """Soft dark contact ellipse under a standing prop -- grounds it
    so it stops looking like a sticker on the grid."""
    key = (rw, rh, alpha)
    s = _SHADOW_CACHE.get(key)
    if s is None:
        s = pygame.Surface((rw * 2, rh * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, alpha), (0, 0, rw * 2, rh * 2))
        _SHADOW_CACHE[key] = s
    surf.blit(s, (int(cx - rw), int(cy - rh)))


_POOL_CACHE = {}


def _light_pool(surf, cx, cy, radius, color=(255, 170, 70), peak=70):
    """Warm radial light pool with falloff. Normal-alpha overlay so it
    reads as light spilling on the dark floor without blowing out."""
    key = (radius, color, peak)
    s = _POOL_CACHE.get(key)
    if s is None:
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        steps = 10
        for k in range(steps, 0, -1):
            r = max(1, int(radius * k / steps))
            a = int(peak * (1 - k / steps) ** 1.4) + 4
            pygame.draw.circle(s, (color[0], color[1], color[2], a),
                               (radius, radius), r)
        _POOL_CACHE[key] = s
    surf.blit(s, (int(cx - radius), int(cy - radius)))


_WALL_SHADOW = None


def _wall_shadow_strip():
    """A TILE-wide gradient (dark at top, fading down) blitted onto the
    floor tile south of a wall, faking cast shadow + height."""
    global _WALL_SHADOW
    if _WALL_SHADOW is None:
        h = (TILE * 3) // 4
        s = pygame.Surface((TILE, h), pygame.SRCALPHA)
        for yy in range(h):
            a = int(100 * (1 - yy / h))
            pygame.draw.line(s, (0, 0, 0, a), (0, yy), (TILE, yy))
        _WALL_SHADOW = s
    return _WALL_SHADOW


# Object chars tall enough to throw a shadow onto the floor below.
_SHADOW_CASTERS = frozenset("#WTpj%&lzqKR")
# draw_object kinds that get a soft contact shadow at their base.
_STANDING_KINDS = frozenset((
    "tree", "cornstalk", "rock", "bed", "table", "chair",
    "shelf", "stove", "crate", "debris", "timber_rack",
))

_DARK_TILES = {}


def _dark_tile(alpha):
    s = _DARK_TILES.get(alpha)
    if s is None:
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        s.fill((0, 0, 0, alpha))
        _DARK_TILES[alpha] = s
    return s


FLOOR_DEFS = {
    "g": {"color": (46, 58, 44),   "step": "step_grass"},
    "G": {"color": (34, 46, 36),   "step": "step_grass"},
    "_": {"color": (80, 78, 74),   "step": "step_stone"},
    "=": {"color": (88, 66, 42),   "step": "step_wood"},
    ",": {"color": (74, 40, 50),   "step": "step_carpet"},
    ".": {"color": (30, 28, 38),   "step": "step_stone"},
    "@": {"color": (8, 6, 14),     "step": "step_void"},
    # Round-13: river floor is no longer universally solid. The
    # brimley river enforces directional access via Game's
    # `_river_blocks` check (player.in_river state + designated entry
    # tile). Other scenes can still use `~` as decorative water; nothing
    # else currently does.
    "~": {"color": (26, 40, 40),   "step": "step_stone"},
    # Dirt footpath -- the worn-grass walking lane that runs through every
    # outdoor scene (replaces the round-4 stone corridor). Soft ochre so
    # it reads as packed dirt next to grass without going full road.
    "d": {"color": (96, 76, 52),   "step": "step_grass"},
    # Paved asphalt -- THE road (arrival_road): the one paved road in the game,
    # west of the start, where the King idles. Cold grey aggregate. "Y" is the
    # centre lane and paints the faded dashed centreline. Other roads stay dirt.
    "P": {"color": (44, 42, 47),   "step": "step_stone"},
    "Y": {"color": (44, 42, 47),   "step": "step_stone"},
    "x": {"color": (28, 22, 30),   "step": "step_stone"},  # basement floor
    # Smooth flat grey stone -- NO texture at all (no mottle, grout, jitter, or
    # macro shadow). The Threshold apron: an impossibly even, man-made-looking
    # floor where geometry serves the door (NARRATIVE §2). draw_floor flat-fills
    # it and returns early.
    "0": {"color": (94, 94, 100),  "step": "step_stone"},
    # Dense corn cover. Walkable + step_grass, but the per-tick
    # cover check in Game.update_player flips player.hidden to
    # "corn" while the player stands on this tile, dropping a
    # cultist's effective sight cone. Stepping off clears hide.
    # Visually a deeper corn-green than `g` so the patches read
    # at a glance; scenes are encouraged to layer grass_tuft
    # decorations on top for body.
    ":": {"color": (38, 52, 40),   "step": "step_grass"},
    # Marsh mud -- wet churned low ground, walkable. Stamped in organic
    # patches across the Brimley fields so the plain reads as a sodden
    # brimley marsh, not a flat lawn.
    ";": {"color": (40, 37, 30),   "step": "step_grass"},
}


OBJECT_DEFS = {
    ".": None,
    "#": {"solid": True, "kind": "stone_wall"},
    "W": {"solid": True, "kind": "wood_wall"},
    "T": {"solid": True, "kind": "tree"},
    "p": {"solid": False, "kind": "tree"},   # passable secret tree -- looks identical to T
    "C": {"solid": True, "kind": "cornstalk"},
    "A": {"solid": False, "kind": "cornstalk"},   # passable corn -- looks like C
    "R": {"solid": True, "kind": "rock"},
    "b": {"solid": True, "kind": "bed"},
    "t": {"solid": True, "kind": "table"},
    "c": {"solid": True, "kind": "chair"},
    "s": {"solid": True, "kind": "timber_rack"},   # the mine's lumber racks
    "i": {"solid": True, "kind": "window"},
    "f": {"solid": True, "kind": "fireplace"},
    "k": {"solid": True, "kind": "stove"},
    "5": {"solid": True, "kind": "counter", "see_over": True},   # kitchen counter (see over it)
    "X": {"solid": True, "kind": "invisible"},
    # Low solid footprint you can SEE OVER: solid for collision, but it does NOT
    # block line of sight (so someone behind a counter/low desk is visible over
    # it). Invisible itself -- the furniture/prop sprite supplies the visuals.
    "x": {"solid": True, "kind": "invisible", "see_over": True},
    "D": {"solid": False, "kind": "door"},
    "E": {"solid": False, "kind": "door"},   # depths chain east-exits
    "H": {"solid": False, "kind": "door"},
    "B": {"solid": False, "kind": "door"},
    "F": {"solid": False, "kind": "door"},
    "J": {"solid": False, "kind": "door"},   # door to toby_house interior
    # Per-house entry doors (each house in the new public square + the
    # Clerk's place in lodge_yard gets its own char so the layout
    # is self-documenting and the scene knows which interior to load).
    "m": {"solid": False, "kind": "door"},   # door to church
    "y": {"solid": False, "kind": "door"},   # door to sheriff_office
    "h": {"solid": False, "kind": "door"},   # door to innkeeper_house
    "n": {"solid": False, "kind": "door"},   # door to barn (south of village)
    "o": {"solid": False, "kind": "door"},   # door to abandoned_farmhouse (red herring)
    # Locked-house door: SOLID until unlocked. The brass-key gate fires
    # from village.on_interact_fn -- pressing E from an adjacent tile
    # transitions if the key is in inventory, otherwise shows a locked
    # notice. The wall blocks movement so the player can't just walk
    # through an unlocked-looking door.
    "z": {"solid": True,  "kind": "door"},   # door to locked_house (red herring)
    # Door "1" -> lives in clerk_room as the stair head DOWN to the guest
    # hall (the loft route: hall staircase 'U' up, this door back down).
    # ("2" is a vestigial tile from a cut scene; no active map places it.)
    "1": {"solid": False, "kind": "door"},   # door to clerk_room (Clerk's room)
    "2": {"solid": False, "kind": "door"},   # vestigial (cut scene)
    # Outdoor-passage style transition tiles -- non-solid, non-drawing
    # so the underlying floor (grass / water) shows through cleanly.
    # '4' is the village <-> brimley corridor.
    "4": {"solid": False, "kind": "outdoor_passage"},
    # Fake wall: looks like a wood wall, passable. Used inside the
    # abandoned_farmhouse red herring -- the player walks through it once to
    # find the symbol-portal room. After the portal is used, the scene
    # build replaces this with a real "W" so the route closes for good.
    "%": {"solid": False, "kind": "fake_wall"},
    # Facade door -- looks like a door but is solid. Used on NPC houses
    # whose interior we don't model. The closed-door visual sells the
    # building as occupied.
    "l": {"solid": True,  "kind": "door"},
    # Roof shingles -- decorative, non-solid. Painted ON TOP of every
    # interior tile of every overworld house so the building reads as a
    # closed-roof structure from above instead of a courtyard.
    "r": {"solid": False, "kind": "roof"},
    "V": {"solid": False, "kind": "void_passage"},
    "L": {"solid": False, "kind": "ladder_down"},   # basement stairs
    "U": {"solid": False, "kind": "ladder_up"},
    # Outdoor passages -- gaps in the tree line for outside <-> outside
    # transitions. Non-drawing, non-solid; the ground tile shows through.
    # Two distinct chars so a single scene can host multiple outdoor exits.
    "e": {"solid": False, "kind": "outdoor_passage"},
    "a": {"solid": False, "kind": "outdoor_passage"},
    # Exit-tree -- visually identical to a normal tree, but acts as a
    # transition tile. Used at the END of the secret void path so the
    # player walks through a continuous tree band, not into a black bar.
    "j": {"solid": False, "kind": "tree"},
    # THRESHOLD: outdoor passage chars for the new scenes.
    # "/" -> schoolhouse door (used in village south band)
    # "?" -> graveyard gate (used inside the church)
    # "!" -> cornfield_maze passage (north gap off the cornfield path)
    "/": {"solid": False, "kind": "outdoor_passage"},
    "?": {"solid": False, "kind": "outdoor_passage"},
    "!": {"solid": False, "kind": "outdoor_passage"},
    # "^" -> generic north-edge exit char. Used by the cornfield
    # maze's hidden passage out the top of the field, but available
    # to any scene that needs a second outdoor passage distinct
    # from "!".
    "^": {"solid": False, "kind": "outdoor_passage"},
    # Round-12: breakable debris pile blocking the village's west exit
    # to the brimley. Solid until the player presses E adjacent with the
    # lumber_axe, at which point Game._chop_tile swaps this tile to "4"
    # at the west edge (so the gap becomes a passage to brimley), else ".".
    "*": {"solid": True,  "kind": "debris"},
    # Boarded panel -- a passage covered with cross-nailed wooden
    # boards. Visually distinct from a regular wood wall (X-cross
    # painted across the planks) and breakable with the splitting
    # axe. Used to gate side rooms and shortcut paths so finding
    # the axe genuinely opens up the map. Pressing E adjacent with
    # the axe converts the tile to ".".
    "q": {"solid": True,  "kind": "boarded"},
    # (The 'K' loot-crate object was removed -- all crates were empty
    # and 'K' is now solely the kid-spawn marker below. The crate draw
    # kind in _draw_object is left in place but unreferenced.)
    # Round-12: planked footbridge tile -- non-solid, drawn over a
    # river. Used in the brimley to gap the N-S river at the bridge
    # rows.
    "$": {"solid": False, "kind": "bridge"},
    # Markers (consumed at scene-build time; never drawn)
    # P=basement photo, K=kid, S=shopkeep, O=oldman, M=mom, Z=basement note,
    # Q=relocation marker (threshold_extras), Y=sheriff, N=innkeeper (quest)
    "P": None, "K": None, "S": None, "O": None, "M": None, "Z": None,
    "Q": None, "Y": None, "N": None,
}


def _vary(seed, i):
    """Cheap deterministic hash -> 32-bit int. Lets one tile seed fan out
    into many independent values, so per-tile variation is stable no
    matter where the camera is (screen-space jitter shimmers when you
    walk; tile-space doesn't)."""
    v = (seed ^ ((i + 1) * 0x9E3779B1)) & 0xFFFFFFFF
    v ^= v >> 15
    v = (v * 0x2C1B3C6D) & 0xFFFFFFFF
    v ^= v >> 13
    return v


def _draw_tree(surf, rx, ry, seed):
    """An oversized, irregular canopy that spills past its tile and
    overhangs its neighbours -- a run of trees reads as one organic
    canopy line, not a grid of identical discs. Center, radius, lean,
    lobe layout and tint all vary per tile (deterministic). Light reads
    from the upper-left, matching the wall faces."""
    cx = rx + 16 + (_vary(seed, 0) % 11) - 5            # -5..+5
    cy = ry + 12 + (_vary(seed, 1) % 9) - 5             # -5..+3 (bias up)
    R = 18 + (_vary(seed, 2) % 9)                       # 18..26 > half-tile -> overhangs
    # Slow wind sway: the canopy leans a few px on a per-tree phase, so a
    # run of trees ripples out of sync rather than swaying as one block.
    cx += int(math.sin(pygame.time.get_ticks() / 1100.0
                       + (seed & 511) * 0.0123) * 2.6)
    lean = (_vary(seed, 3) % 7) - 3
    tw = 5 + (_vary(seed, 4) % 2)
    bx = rx + 16 - tw // 2 + lean                       # short trunk, mostly hidden
    pygame.draw.rect(surf, (44, 32, 22), (bx, ry + 18, tw, 14))
    pygame.draw.rect(surf, (28, 20, 13), (bx, ry + 18, 2, 14))
    g = _vary(seed, 5) % 12
    base = (16 + g // 2, 38 + g, 22 + g // 2)
    mid = (26 + g, 56 + g, 32 + g)
    lite = (42 + g, 78 + g, 46 + g)
    for k, (ox, oy, rr) in enumerate((
            (0.0, 0.10, 1.00), (-0.55, 0.22, 0.64), (0.55, 0.16, 0.60),
            (-0.30, -0.46, 0.58), (0.34, -0.40, 0.54), (0.0, 0.48, 0.50))):
        wob = (_vary(seed, 10 + k) % 5) - 2
        pygame.draw.circle(surf, base,
                           (int(cx + ox * R), int(cy + oy * R)),
                           max(3, int(rr * R) + wob))
    for ox, oy, rr in ((-0.18, -0.10, 0.72), (0.30, 0.06, 0.54),
                       (-0.05, -0.42, 0.46)):
        pygame.draw.circle(surf, mid,
                           (int(cx + ox * R), int(cy + oy * R)),
                           max(2, int(rr * R)))
    for ox, oy, rr in ((-0.34, -0.34, 0.34), (-0.06, -0.20, 0.24)):
        pygame.draw.circle(surf, lite,
                           (int(cx + ox * R), int(cy + oy * R)),
                           max(2, int(rr * R)))


def _draw_corn(surf, rx, ry, seed):
    """A corn clump taller and wider than its tile: stalks lean, overhang
    sideways and spill above the tile top, so a corn block reads as a
    dense continuous field rather than a grid of identical plants. Sway
    is time-animated; everything else varies per tile (deterministic)."""
    t = pygame.time.get_ticks() / 600.0
    n = 3 + (_vary(seed, 0) % 2)                         # 3-4 stalks
    g = _vary(seed, 1) % 10
    stalk = (58 + g, 72 + g, 38 + g // 2)
    blade = (82 + g, 96 + g, 48 + g)
    tip = (150 + g, 130, 70)
    amp = 2.0 + (_vary(seed, 2) % 3)
    ph = (seed % 628) / 100.0                            # per-tile sway phase (camera-stable)
    for s in range(n):
        sx = rx + 5 + int(s * (TILE - 8) / max(1, n - 1)) \
            + (_vary(seed, 10 + s) % 7) - 3              # spread across + overhang
        bx = rx + 13 + (_vary(seed, 30 + s) % 8) - 4     # base clustered, foot of tile
        top = ry - 6 + (_vary(seed, 20 + s) % 9)         # tops spill above the tile
        bottom = ry + 31
        tipx = sx + int(math.sin(t + ph + s * 0.7) * amp)
        midx, midy = (bx + tipx) // 2, (bottom + top) // 2
        pygame.draw.line(surf, stalk, (bx, bottom), (midx, midy), 2)
        pygame.draw.line(surf, stalk, (midx, midy), (tipx, top), 2)
        pygame.draw.line(surf, blade, (midx, midy),
                         (midx - 8, midy - 2), 2)
        pygame.draw.line(surf, blade, (midx + 1, midy + 4),
                         (midx + 9, midy + 1), 2)
        pygame.draw.line(surf, tip, (tipx, top), (tipx, top - 5), 2)


def draw_object(surf, ch, rx, ry, tx, ty):
    od = OBJECT_DEFS.get(ch)
    if not od or od["kind"] in ("invisible", "void_passage", "outdoor_passage"):
        return
    kind = od["kind"]
    if kind in _STANDING_KINDS:
        _ground_shadow(surf, rx + TILE // 2, ry + TILE - 5, 11, 4, 70)
    if kind == "stone_wall":
        pygame.draw.rect(surf, (64, 62, 66), (rx, ry, TILE, TILE))
        pygame.draw.rect(surf, (34, 32, 38), (rx, ry, TILE, TILE), 1)
        pygame.draw.line(surf, (34, 32, 38), (rx, ry + 16), (rx + TILE, ry + 16), 1)
        pygame.draw.line(surf, (34, 32, 38), (rx + 16, ry), (rx + 16, ry + 16), 1)
        pygame.draw.line(surf, (34, 32, 38), (rx + 8, ry + 16), (rx + 8, ry + TILE), 1)
        pygame.draw.line(surf, (34, 32, 38), (rx + 24, ry + 16), (rx + 24, ry + TILE), 1)
        # Height bevel: lit top edge, shadowed base -- fakes a block
        # with mass instead of a flat painted tile.
        pygame.draw.line(surf, (88, 86, 92), (rx, ry), (rx + TILE - 1, ry), 1)
        pygame.draw.rect(surf, (22, 20, 26), (rx, ry + TILE - 3, TILE, 3))
    elif kind == "wood_wall" or kind == "fake_wall":
        # fake_wall draws identically to wood_wall so the player can't
        # distinguish them visually -- the only tell is that walking
        # into a fake_wall doesn't bump.
        pygame.draw.rect(surf, (80, 58, 40), (rx, ry, TILE, TILE))
        pygame.draw.rect(surf, (48, 32, 20), (rx, ry, TILE, TILE), 1)
        pygame.draw.line(surf, (48, 32, 20), (rx, ry + 10), (rx + TILE, ry + 10), 1)
        pygame.draw.line(surf, (48, 32, 20), (rx, ry + 22), (rx + TILE, ry + 22), 1)
        pygame.draw.line(surf, (104, 80, 56), (rx, ry), (rx + TILE - 1, ry), 1)
        pygame.draw.rect(surf, (40, 28, 18), (rx, ry + TILE - 3, TILE, 3))
    elif kind == "tree":
        _draw_tree(surf, rx, ry, (tx * 73856093) ^ (ty * 19349663))
    elif kind == "cornstalk":
        _draw_corn(surf, rx, ry, (tx * 73856093) ^ (ty * 19349663))
    elif kind == "rock":
        pygame.draw.circle(surf, (100, 100, 110), (rx + 16, ry + 18), 12)
        pygame.draw.circle(surf, (70, 70, 80), (rx + 12, ry + 14), 4)
    elif kind == "bed":
        # Iron-frame cot, top-down: dark frame, a dingy thin mattress
        # with a lit top edge + foot shadow, a grimy pillow, a heavy
        # dark blanket pulled up with a fold, and an old stain.
        pygame.draw.rect(surf, (42, 30, 20), (rx + 2, ry + 4, 28, 26))      # frame
        pygame.draw.rect(surf, (116, 108, 100), (rx + 4, ry + 6, 24, 22))   # mattress
        pygame.draw.rect(surf, (138, 130, 122), (rx + 4, ry + 6, 24, 2))    # lit top
        pygame.draw.rect(surf, (70, 64, 58), (rx + 4, ry + 26, 24, 2))      # foot shadow
        pygame.draw.rect(surf, (146, 138, 130), (rx + 6, ry + 8, 20, 6))    # pillow
        pygame.draw.rect(surf, (120, 112, 104), (rx + 6, ry + 13, 20, 1))
        pygame.draw.rect(surf, (90, 48, 52), (rx + 4, ry + 16, 24, 12))     # blanket
        pygame.draw.rect(surf, (110, 60, 64), (rx + 4, ry + 16, 24, 2))     # lit edge
        pygame.draw.line(surf, (66, 36, 40), (rx + 14, ry + 18), (rx + 14, ry + 27), 1)
        pygame.draw.rect(surf, (62, 42, 32), (rx + 18, ry + 20, 6, 5))      # stain
    elif kind == "table":
        # Plank table in dark, grimy wood: grained top with a lit back
        # edge + shadowed front lip, two visible legs beneath.
        pygame.draw.rect(surf, (48, 32, 20), (rx + 5, ry + 22, 4, 8))       # leg
        pygame.draw.rect(surf, (48, 32, 20), (rx + 23, ry + 22, 4, 8))      # leg
        pygame.draw.rect(surf, (76, 54, 34), (rx + 2, ry + 6, 28, 18))      # top
        pygame.draw.rect(surf, (98, 72, 46), (rx + 2, ry + 6, 28, 2))       # lit back
        pygame.draw.rect(surf, (42, 28, 17), (rx + 2, ry + 21, 28, 3))      # front lip
        for gx in (9, 16, 23):                                             # grain
            pygame.draw.line(surf, (58, 40, 24),
                             (rx + gx, ry + 9), (rx + gx, ry + 20), 1)
    elif kind == "chair":
        # Backed wooden chair in dark wood: legs, a seat with a lit
        # edge, a slatted back.
        pygame.draw.rect(surf, (48, 32, 20), (rx + 9, ry + 23, 3, 6))       # legs
        pygame.draw.rect(surf, (48, 32, 20), (rx + 20, ry + 23, 3, 6))
        pygame.draw.rect(surf, (66, 46, 28), (rx + 8, ry + 6, 16, 9))       # back
        pygame.draw.line(surf, (44, 30, 18), (rx + 13, ry + 7), (rx + 13, ry + 14), 1)
        pygame.draw.line(surf, (44, 30, 18), (rx + 19, ry + 7), (rx + 19, ry + 14), 1)
        pygame.draw.rect(surf, (78, 56, 34), (rx + 8, ry + 15, 16, 9))      # seat
        pygame.draw.rect(surf, (98, 72, 44), (rx + 8, ry + 15, 16, 2))      # lit seat
    elif kind == "timber_rack":
        # A mine lumber rack: two dark end posts bearing stacked sawn
        # boards on their sides -- horizontal plank bands with end-grain
        # ticks, nothing shelved, nothing bound (2026-07: the old 's'
        # tiles drew BOOKSHELVES, which failed the man-made-dig logic).
        pygame.draw.rect(surf, (40, 30, 19), (rx + 2, ry + 6, 4, 22))    # end posts
        pygame.draw.rect(surf, (40, 30, 19), (rx + 26, ry + 6, 4, 22))
        for i, by in enumerate((ry + 8, ry + 13, ry + 18, ry + 23)):
            ln = 24 - ((tx * 7 + ty * 13 + i * 5) % 3) * 3              # board lengths vary
            bcol = (96, 74, 48) if i % 2 else (84, 64, 41)
            pygame.draw.rect(surf, bcol, (rx + 4, by, ln, 4))
            pygame.draw.rect(surf, (52, 40, 27), (rx + 4, by, ln, 4), 1)
            pygame.draw.rect(surf, (120, 100, 66), (rx + 4, by + 1, 2, 2))  # end grain
        pygame.draw.rect(surf, (58, 44, 28), (rx + 2, ry + 6, 28, 2))    # top rail
    elif kind == "shelf":
        # Bookshelf in dark, grimy wood: a framed case with a lit top +
        # two under-shadowed shelf boards and rows of leaning books in
        # muted, faded tones.
        pygame.draw.rect(surf, (62, 46, 28), (rx + 2, ry + 2, 28, 28))      # case
        pygame.draw.rect(surf, (34, 24, 15), (rx + 2, ry + 2, 28, 28), 1)
        pygame.draw.rect(surf, (84, 62, 38), (rx + 2, ry + 2, 28, 2))       # lit top
        cols = [(92, 46, 42), (48, 58, 74), (56, 72, 48),
                (104, 86, 46), (74, 52, 78)]
        for row, by in enumerate((ry + 4, ry + 15)):
            pygame.draw.rect(surf, (36, 26, 15), (rx + 3, by + 9, 26, 2))   # shelf board
            bx = rx + 4
            i = 0
            while bx < rx + 27:
                bw = 2 + ((tx * 7 + ty * 13 + row * 5 + i * 3) % 3)
                bh = 6 + ((tx * 3 + row * 7 + i * 11) % 4)
                col = cols[(tx + ty + row + i) % len(cols)]
                pygame.draw.rect(surf, col, (bx, by + (9 - bh), bw, bh))
                pygame.draw.rect(surf, (col[0] // 2, col[1] // 2, col[2] // 2),
                                 (bx, by + (9 - bh), bw, 1))
                bx += bw + 1
                i += 1
    elif kind == "window":
        # Wood frame + sky-blue glass. A faint dark vertical strip
        # passes left-to-right behind the glass on a slow per-tile
        # schedule -- a silhouette walking by outside. Most of the
        # cycle the strip is off-tile so the window reads as normal.
        # Per-tile seed via pygame.time + position so adjacent windows
        # don't pass the same figure at the same instant.
        pygame.draw.rect(surf, (96, 70, 50), (rx, ry, TILE, TILE))
        pygame.draw.rect(surf, (60, 40, 25), (rx, ry, TILE, TILE), 1)
        # Lit-from-within: a dim, sickly amber pane (no cheerful primary
        # blue) with a warmer core, so a window reads as an oil lamp
        # burning behind grimy glass at dusk -- occupied, and wrong.
        pygame.draw.rect(surf, (138, 104, 50), (rx + 6, ry + 6, 20, 20))
        pygame.draw.rect(surf, (170, 138, 78), (rx + 9, ry + 9, 14, 14))
        # Passing-figure anomaly. Each window is on its own clock,
        # AND its cycle length is jittered by up to +/-20% based on
        # tile position so adjacent windows can never sync into a
        # readable pattern (a beat that repeats reads as a draw bug
        # rather than a haunting). 2-px dark strip drifts across the
        # visible glass over ~1.6s, off-screen the rest of the cycle.
        ticks = pygame.time.get_ticks()
        tile_id = (rx * 13 + ry * 29) // TILE
        # Per-tile cycle length in [11200, 16800] ms (~14s ± 20%).
        cycle = 14000 + ((tile_id * 271) % 5601) - 2800
        seed_off = (tile_id * 311) % cycle
        local = (ticks + seed_off) % cycle
        if local < 1600:
            phase = local / 1600.0  # 0.0 -> 1.0
            fx = int(rx + 6 + phase * 20)
            if rx + 6 <= fx <= rx + 24:
                pygame.draw.rect(surf, (40, 30, 50),
                                 (fx, ry + 8, 2, 16))
        pygame.draw.line(surf, (74, 54, 34), (rx + 16, ry + 6), (rx + 16, ry + 26), 1)
        pygame.draw.line(surf, (74, 54, 34), (rx + 6, ry + 16), (rx + 26, ry + 16), 1)
        pygame.draw.rect(surf, (60, 40, 25), (rx + 6, ry + 6, 20, 20), 1)
    elif kind == "fireplace":
        # Stone hearth, dark mouth, animated flame. At a rare phase
        # of the flame's slow cycle, two dark gaps appear in the
        # inner flame -- the fire briefly resembles a face with two
        # hollow eyes. Held for ~80ms then the flame returns to its
        # normal taper.
        _light_pool(surf, rx + 16, ry + 22, 44, (255, 140, 50), 92)
        pygame.draw.rect(surf, (64, 62, 66), (rx, ry, TILE, TILE))
        pygame.draw.rect(surf, (10, 8, 12), (rx + 6, ry + 8, 20, 20))
        t = pygame.time.get_ticks() / 100.0
        f_h = 6 + int(math.sin(t) * 2)
        pygame.draw.polygon(surf, (220, 90, 30),
                            [(rx + 16, ry + 26 - f_h),
                             (rx + 10, ry + 26),
                             (rx + 22, ry + 26)])
        pygame.draw.polygon(surf, (255, 200, 80),
                            [(rx + 16, ry + 24 - int(f_h * 0.6)),
                             (rx + 12, ry + 26),
                             (rx + 20, ry + 26)])
        # Face anomaly: rare phase where two black gaps sit where
        # eyes would be in the inner flame.
        face_phase = (pygame.time.get_ticks() + (rx * 7 + ry * 13)) % 6000
        if face_phase < 90:
            pygame.draw.rect(surf, (10, 8, 12),
                             (rx + 14, ry + 21, 1, 2))
            pygame.draw.rect(surf, (10, 8, 12),
                             (rx + 18, ry + 21, 1, 2))
    elif kind == "stove":
        # Cast-iron range: a dark body with a lit cooktop + base shadow,
        # two burner rings, an oven door with a handle, and a faint
        # ember glow bleeding through the vent.
        pygame.draw.rect(surf, (44, 44, 50), (rx + 2, ry + 4, 28, 26))      # body
        pygame.draw.rect(surf, (62, 62, 70), (rx + 2, ry + 4, 28, 2))       # lit top
        pygame.draw.rect(surf, (24, 24, 30), (rx + 2, ry + 28, 28, 2))      # base shadow
        pygame.draw.rect(surf, (28, 28, 34), (rx + 2, ry + 4, 28, 26), 1)
        for cxk in (10, 22):                                               # burners
            pygame.draw.circle(surf, (20, 20, 26), (rx + cxk, ry + 11), 4)
            pygame.draw.circle(surf, (12, 12, 16), (rx + cxk, ry + 11), 2)
        pygame.draw.rect(surf, (18, 18, 22), (rx + 6, ry + 18, 20, 10))     # oven door
        pygame.draw.rect(surf, (72, 72, 80), (rx + 9, ry + 17, 14, 2))      # handle
        pygame.draw.rect(surf, (200, 90, 30), (rx + 11, ry + 25, 10, 2))    # ember vent
    elif kind == "counter":
        # A dark-wood worktop seen from ABOVE (top-down, like the table
        # and stove): a grimy butcher surface with a raised edge that
        # catches a little light, plank grain, knife scoring and old
        # stains. Dark + desaturated for the lodge's darkwood dread --
        # never a clean cabinet face. Tiles into a continuous run.
        pygame.draw.rect(surf, (52, 38, 26), (rx, ry, TILE, TILE))           # dark top
        for gy in (ry + 8, ry + 16, ry + 24):                                # plank grain
            pygame.draw.line(surf, (40, 28, 18), (rx, gy), (rx + TILE, gy), 1)
        pygame.draw.line(surf, (80, 60, 40), (rx, ry + 1), (rx + TILE, ry + 1), 1)   # lit lip
        pygame.draw.rect(surf, (26, 18, 11), (rx, ry + TILE - 3, TILE, 3))   # base shadow
        pygame.draw.line(surf, (30, 21, 13), (rx, ry), (rx, ry + TILE), 1)   # edges
        pygame.draw.line(surf, (30, 21, 13),
                         (rx + TILE - 1, ry), (rx + TILE - 1, ry + TILE), 1)
        seed = tx * 23 + ty * 47
        for i in range(2):                                                   # knife scoring
            sx = rx + 5 + (seed * (i + 1)) % 20
            pygame.draw.line(surf, (38, 27, 17), (sx, ry + 6), (sx + 5, ry + 13), 1)
        if seed % 3 == 0:                                                    # old dark stain
            pygame.draw.ellipse(surf, (46, 18, 16),
                                (rx + (seed % 14) + 5, ry + 11, 8, 5))
    elif kind == "ladder_down":
        # Round-7 redraw: cellar HATCH (was a ladder visual). A square
        # wood box flush to the ground, two horizontal plank seams, and
        # a clear iron pull-ring centred on top so the player reads it
        # as a closed hatch with a handle, not a rope ladder.
        pygame.draw.rect(surf, (110, 80, 50), (rx + 4, ry + 4, 24, 24))
        pygame.draw.rect(surf, (60, 38, 24), (rx + 4, ry + 4, 24, 24), 2)
        # Plank seams (horizontal)
        pygame.draw.line(surf, (60, 38, 24), (rx + 4, ry + 12),
                                              (rx + 28, ry + 12), 1)
        pygame.draw.line(surf, (60, 38, 24), (rx + 4, ry + 20),
                                              (rx + 28, ry + 20), 1)
        # Iron base plate + pull-ring handle, centred
        pygame.draw.rect(surf, (50, 50, 60), (rx + 12, ry + 13, 8, 4))
        pygame.draw.rect(surf, (30, 30, 38), (rx + 12, ry + 13, 8, 4), 1)
        pygame.draw.circle(surf, (180, 180, 200), (rx + 16, ry + 18), 4, 2)
        pygame.draw.circle(surf, (90, 90, 110), (rx + 16, ry + 18), 4, 1)
    elif kind == "ladder_up":
        pygame.draw.rect(surf, (90, 60, 30), (rx + 6, ry + 4, 20, 28))
        for i in range(4):
            pygame.draw.line(surf, (200, 180, 120), (rx + 8, ry + 8 + i * 6),
                             (rx + 24, ry + 8 + i * 6), 1)
    elif kind == "boarded":
        # Cross-nailed wooden boards over a passage. Lighter wood
        # than wood_wall so it reads as nailed-on planks, with two
        # diagonal planks crossed in an X to sell "boarded shut."
        # The four nail heads at each plank tip are visible too.
        pygame.draw.rect(surf, (130, 95, 60), (rx, ry, TILE, TILE))
        pygame.draw.rect(surf, (60, 40, 25), (rx, ry, TILE, TILE), 1)
        # Vertical plank seams
        pygame.draw.line(surf, (60, 40, 25),
                         (rx + 10, ry), (rx + 10, ry + TILE), 1)
        pygame.draw.line(surf, (60, 40, 25),
                         (rx + 22, ry), (rx + 22, ry + TILE), 1)
        # Cross planks (X)
        pygame.draw.line(surf, (90, 60, 35),
                         (rx + 4, ry + 4), (rx + TILE - 4, ry + TILE - 4), 3)
        pygame.draw.line(surf, (90, 60, 35),
                         (rx + TILE - 4, ry + 4), (rx + 4, ry + TILE - 4), 3)
        # Nail heads (4 corners of the cross)
        for nx, ny in ((4, 4), (TILE - 5, 4),
                       (4, TILE - 5), (TILE - 5, TILE - 5)):
            pygame.draw.rect(surf, (40, 40, 50),
                             (rx + nx, ry + ny, 2, 2))
    elif kind == "crate":
        # Wooden cargo crate. Plank seams run vertical; iron banding
        # at top + bottom; rivet dots at each corner. Slightly
        # darker than wood_wall so it reads as cargo, not building.
        pygame.draw.rect(surf, (118, 80, 46),
                         (rx + 2, ry + 4, TILE - 4, TILE - 8))
        pygame.draw.rect(surf, (60, 38, 24),
                         (rx + 2, ry + 4, TILE - 4, TILE - 8), 1)
        # Vertical plank seams
        for sx in (10, 18, 24):
            pygame.draw.line(surf, (60, 38, 24),
                             (rx + sx, ry + 4),
                             (rx + sx, ry + TILE - 4), 1)
        # Iron banding (top + bottom horizontal strips)
        pygame.draw.rect(surf, (50, 48, 56),
                         (rx + 2, ry + 5, TILE - 4, 2))
        pygame.draw.rect(surf, (50, 48, 56),
                         (rx + 2, ry + TILE - 7, TILE - 4, 2))
        # Rivet dots at each banding corner
        for nx, ny in ((4, 5), (TILE - 6, 5),
                       (4, TILE - 7), (TILE - 6, TILE - 7)):
            pygame.draw.rect(surf, (180, 175, 180),
                             (rx + nx, ry + ny, 1, 1))
    elif kind == "debris":
        # Tangled pile of fallen branches + planks. Solid until the
        # player presses E adjacent with the lumber_axe. Draw as a few
        # crossed logs over a low pile of leaves.
        pygame.draw.rect(surf, (50, 40, 26), (rx + 2, ry + 18, TILE - 4, 12))
        pygame.draw.rect(surf, (90, 60, 36), (rx + 2, ry + 12, TILE - 4, 8))
        pygame.draw.rect(surf, (60, 40, 24), (rx + 2, ry + 12, TILE - 4, 8), 1)
        pygame.draw.line(surf, (50, 32, 18), (rx + 4, ry + 8),
                         (rx + TILE - 4, ry + 22), 2)
        pygame.draw.line(surf, (50, 32, 18), (rx + TILE - 4, ry + 8),
                         (rx + 4, ry + 22), 2)
        pygame.draw.circle(surf, (40, 70, 36), (rx + 8, ry + 26), 2)
        pygame.draw.circle(surf, (40, 70, 36), (rx + 22, ry + 26), 2)
    elif kind == "bridge":
        # Weathered wood plank deck. Per-tile seed makes plank widths
        # and knot positions vary so the bridge doesn't read as a
        # repeated stamp.
        seed = (tx * 73856093) ^ (ty * 19349663)
        rng = random.Random(seed)
        base = (96, 70, 40)
        lit = (124, 92, 58)
        dark = (60, 42, 22)
        grain = (50, 32, 18)
        # Base
        pygame.draw.rect(surf, base, (rx, ry, TILE, TILE))
        # Plank divisions running with the flow of the river (N-S
        # lines) so the player walks ACROSS the planks. 3-4 planks
        # per tile, widths jittered.
        x = 0
        while x < TILE - 1:
            step = rng.randint(7, 10)
            x += step
            if x < TILE - 1:
                pygame.draw.line(surf, grain,
                                 (rx + x, ry), (rx + x, ry + TILE - 1), 1)
        # Knot blobs -- 0-2 per tile.
        for _ in range(rng.randint(0, 2)):
            kx = rx + rng.randint(3, TILE - 4)
            ky = ry + rng.randint(3, TILE - 4)
            pygame.draw.circle(surf, dark, (kx, ky), 2)
            pygame.draw.circle(surf, grain, (kx, ky), 1)
        # Lit top edge + shadowed bottom edge so each plank tile reads
        # as a slightly raised deck. Lit on the north (top) row only
        # if the tile north of us isn't bridge; shadowed on the south
        # row similarly. Cheap proxy: always draw a thin top highlight
        # and bottom shadow so adjacent tiles seam together.
        pygame.draw.line(surf, lit, (rx, ry), (rx + TILE - 1, ry), 1)
        pygame.draw.line(surf, (40, 26, 14),
                         (rx, ry + TILE - 1),
                         (rx + TILE - 1, ry + TILE - 1), 1)
    elif kind == "roof":
        # Drawn by the unified gabled-roof pass (_draw_scene_roofs), not
        # per tile -- one overhanging roof per building instead of a flat
        # grid of shingle tiles. Nothing to do here.
        pass


def draw_floor(surf, ch, rx, ry, tx, ty):
    fd = FLOOR_DEFS.get(ch, FLOOR_DEFS["."])
    base = fd["color"]
    # Sub-tile value noise + the macro shadow, evaluated per 8px cell and
    # BILINEAR across tile corners (corner hashes are shared with the
    # neighbouring tiles), so ground brightness rolls smoothly ACROSS tile
    # edges. The old whole-tile jitter + per-tile shadow alpha stepped at
    # every tile boundary and read as a checkerboard of 32px squares (the
    # 2026-07 quality sprint's "square patches of grass"). Cost lands only
    # on the first draw (tiles are cached); animated floors (~,@) keep the
    # flat fill + the per-tile tail shadow (they redraw every frame).
    smooth = ch not in _ANIM_FLOOR and ch != "0"
    if smooth:
        def _cj(cx, cy):
            return (_vary(cx * 8009 + cy * 7919, 0) % 15) - 7
        c00, c10 = _cj(tx, ty), _cj(tx + 1, ty)
        c01, c11 = _cj(tx, ty + 1), _cj(tx + 1, ty + 1)
        cell = TILE // 4
        for syc in range(4):
            v = (syc + 0.5) / 4.0
            for sxc in range(4):
                u = (sxc + 0.5) / 4.0
                jv = ((c00 * (1 - u) + c10 * u) * (1 - v)
                      + (c01 * (1 - u) + c11 * u) * v)
                # Amplitude tuned DOWN with the smoothing (2026-07): the
                # old per-tile stepping read as texture, but a smooth
                # -58-value blob read as the hard shadow of nothing (the
                # playtest's "weird dark patch outside the cabin").
                sh = (math.sin((tx + u) * 0.23 + (ty + v) * 0.15)
                      + 0.6 * math.sin((tx + u) * 0.09 - (ty + v) * 0.19))
                lv = jv - min(30.0, max(0.0, -sh) * 17.0)
                col = (max(0, min(255, int(base[0] + lv))),
                       max(0, min(255, int(base[1] + lv))),
                       max(0, min(255, int(base[2] + lv))))
                pygame.draw.rect(surf, col, (rx + sxc * cell,
                                             ry + syc * cell, cell, cell))
    else:
        pygame.draw.rect(surf, base, (rx, ry, TILE, TILE))
    if ch == "0":
        # Smooth flat grey stone: a single flat fill, nothing else -- no detail,
        # no per-tile jitter, and NOT the macro shadow blotch below. Perfectly,
        # unnaturally even (the Threshold apron).
        return
    if ch in ("g", "G"):
        # Grass with layered detail: a faint base mottle on every
        # tile, occasional grass blades, occasional darker dead-clump,
        # and a very rare bone-white speck (something old buried).
        seed = tx * 37 + ty * 53
        # Soft mottle -- every tile gets one or two darker patches so
        # the grass never reads as a flat green field.
        for i in range(2):
            sx = (seed * (i * 3 + 1)) % 28
            sy = (seed * (i * 5 + 7)) % 28
            pygame.draw.rect(surf, (40, 50, 40),
                             (rx + sx, ry + sy, 2, 2))
        if seed % 7 == 0:
            pygame.draw.rect(surf, (54, 64, 46),
                             (rx + (seed % 26), ry + (seed * 3 % 26), 2, 4))
        if seed % 11 == 0:
            # Dead clump
            pygame.draw.rect(surf, (66, 56, 34),
                             (rx + (seed * 2 % 26),
                              ry + (seed * 5 % 26), 3, 2))
        if seed % 9 == 0:
            # Bare earth scuffed through the grass -- a patch of dirt.
            ex, ey = rx + (seed * 7 % 22) + 2, ry + (seed * 11 % 22) + 2
            pygame.draw.ellipse(surf, (60, 48, 34), (ex, ey, 7, 5))
            pygame.draw.rect(surf, (50, 40, 28), (ex + 2, ey + 1, 2, 2))
        if seed % 13 == 0:
            # A taller blade clump, lighter green, catching what light there is.
            bx, by = rx + (seed * 5 % 28), ry + (seed * 3 % 22) + 6
            for k in range(3):
                pygame.draw.line(surf, (72, 86, 54),
                                 (bx + k * 2, by), (bx + k * 2 - 1, by - 5 - k), 1)
        if seed % 73 == 0:
            # Bone speck -- very rare. The kind of thing a player
            # only catches on the second or third walk through.
            pygame.draw.rect(surf, (210, 200, 180),
                             (rx + (seed * 3 % 28),
                              ry + (seed * 7 % 28), 1, 1))
        elif seed % 57 == 0:
            # A rare pale weed-flower -- a fleck of off-white in the green.
            pygame.draw.rect(surf, (172, 170, 142),
                             (rx + (seed * 9 % 28), ry + (seed * 13 % 28), 1, 1))
    elif ch == "_":
        pygame.draw.rect(surf, (92, 90, 86),
                         (rx + 1, ry + 1, TILE - 2, TILE - 2), 1)
        # Scatter a few darker grout lines so stone reads as paved
        # rather than a single block.
        seed = tx * 29 + ty * 41
        if seed % 4 == 0:
            pygame.draw.line(surf, (90, 88, 86),
                             (rx + 16, ry + 1),
                             (rx + 16, ry + TILE - 1), 1)
        if seed % 5 == 0:
            pygame.draw.line(surf, (90, 88, 86),
                             (rx + 1, ry + 16),
                             (rx + TILE - 1, ry + 16), 1)
    elif ch == "=":
        # Wood plank floor: three horizontal boards per tile, each a
        # slightly different tone (keyed to its global board row) so
        # long planks read across the room -- shadowed seams, a lit
        # edge under each, staggered end-joints, knots.
        # The boards must vary ALONG their length too, or an E/W facing
        # (boards rotated to vertical) reads as long uniform stripes
        # (2026-07 playtest: "the floor on the east/west looks like
        # straight lines"). Per-tile grain patches + end-joints every ~3
        # tiles of run give the cross-grain rhythm; the macro shadow is
        # folded into the board shade (these rects overdraw the smooth
        # base cells, which used to silently drop it).
        msh = (math.sin((tx + 0.5) * 0.23 + (ty + 0.5) * 0.15)
               + 0.6 * math.sin((tx + 0.5) * 0.09 - (ty + 0.5) * 0.19))
        mdark = min(30.0, max(0.0, -msh) * 17.0)
        boards = ((0, 10), (10, 12), (22, 10))     # (y0, height) per board
        for b, (y0, bh) in enumerate(boards):
            row = ty * 3 + b
            v = ((row * 2654435761) & 0xff) / 255.0 - 0.5    # -0.5..0.5
            g2 = (((row * 40503 + tx * 9176) & 0xff) / 255.0 - 0.5)
            shade = (max(0, min(255, int(88 + v * 26 + g2 * 14 - mdark))),
                     max(0, min(255, int(66 + v * 20 + g2 * 10 - mdark))),
                     max(0, min(255, int(42 + v * 16 + g2 * 8 - mdark * 0.8))))
            pygame.draw.rect(surf, shade, (rx, ry + y0, TILE, bh))
            # A part-tile grain patch so one board's tone shifts mid-run.
            if (row * 13 + tx * 5) % 3 == 0:
                px0 = rx + ((row * 17 + tx * 23) % 16)
                pw = 10 + ((row + tx) % 8)
                patch = tuple(max(0, min(255,
                                         c + (6 if (row + tx) % 2 else -6)))
                              for c in shade)
                pygame.draw.rect(surf, patch, (px0, ry + y0 + 1, pw, bh - 2))
            pygame.draw.line(surf, (52, 36, 22),
                             (rx, ry + y0), (rx + TILE, ry + y0), 1)
            pygame.draw.line(surf, (104, 80, 52),
                             (rx, ry + y0 + 1), (rx + TILE, ry + y0 + 1), 1)
            # Staggered end-joints every ~3 tiles of board run (a lit edge
            # beside each so the butt reads under the tilt).
            if (row * 7 + tx * 3) % 3 == 0:
                jx = rx + ((row * 11 + tx * 7) % (TILE - 6)) + 3
                pygame.draw.line(surf, (50, 34, 20),
                                 (jx, ry + y0 + 1), (jx, ry + y0 + bh - 1), 1)
                pygame.draw.line(surf, (110, 86, 56),
                                 (jx + 1, ry + y0 + 1),
                                 (jx + 1, ry + y0 + bh - 1), 1)
        # Dark knots, sparse.
        seed = tx * 31 + ty * 17
        if seed % 6 == 0:
            kx = rx + (seed % 26) + 3
            ky = ry + (seed * 3 % 22) + 3
            pygame.draw.circle(surf, (60, 38, 22), (kx, ky), 2)
            pygame.draw.circle(surf, (40, 26, 16), (kx, ky), 1)
        # Tracked-in grit + the place half-abandoned: sparse dust specks, a
        # rare ground-in grime smear, and very rarely a blade of grass pushing
        # up through a board seam. Reads grimy and lived-in, not a clean floor.
        if seed % 4 == 0:
            for k in range(2):
                gx = rx + (_vary(seed, k) % 28) + 2
                gy = ry + (_vary(seed, k + 5) % 28) + 2
                pygame.draw.rect(surf, (44, 33, 22), (gx, gy, 1, 1))
        if seed % 13 == 0:
            pygame.draw.ellipse(surf, (40, 30, 20),
                                (rx + (seed * 3 % 22) + 4,
                                 ry + (seed * 5 % 22) + 4, 6, 3))
        if seed % 29 == 0:
            # A weed through a floorboard seam -- nature creeping back in.
            wx = rx + (seed % 24) + 4
            wb = ry + 8 + (seed % 14)
            for k in range(2):
                pygame.draw.line(surf, (62, 78, 48),
                                 (wx + k, wb), (wx + k - 1, wb - 5), 1)
    elif ch == ",":
        pygame.draw.rect(surf, (80, 30, 50), (rx, ry, TILE, TILE), 1)
        for i in range(0, TILE, 6):
            pygame.draw.line(surf, (140, 60, 80),
                             (rx + i, ry), (rx + i, ry + TILE), 1)
        # Worn patch -- every few tiles a faded rectangle.
        if (tx * 13 + ty * 19) % 5 == 0:
            pygame.draw.rect(surf, (110, 50, 70),
                             (rx + 8, ry + 12, 14, 8))
    elif ch == "~":
        # A dead, cold river -- murky and scummed over, not clean blue.
        # Organic DARK PATCHES pool in the deeper middle of the channel
        # (depth + slow current), under slow dim ripples, algae, and a rare
        # cold glint instead of bright foam.
        seed = tx * 11 + ty * 23
        # Low-frequency field -> large, ORGANIC dark regions (the deep
        # channel) rather than a per-tile checker, drifting slowly downstream.
        # The ellipses overrun the tile edge on purpose so patches flow
        # continuously across neighbouring water tiles.
        drift = pygame.time.get_ticks() / 5200.0
        field = (math.sin(tx * 0.55 + drift)
                 + math.cos(ty * 0.42 - drift * 0.7)
                 + math.sin((tx + ty) * 0.30 + drift * 0.5))
        if field > 0.55:
            depth_c = (12, 22, 24) if field > 1.5 else (18, 29, 31)
            for k in range(2):
                ex = rx + (seed * (k + 3) % 14) - 2
                ey = ry + ((seed // (k + 2)) % 14) - 2
                ew = 14 + (seed >> k) % 12
                eh = 9 + (seed >> (k + 1)) % 7
                pygame.draw.ellipse(surf, depth_c, (ex, ey, ew, eh))
        t = (tx + ty + pygame.time.get_ticks() // 320) % 8
        pygame.draw.line(surf, (40, 54, 52), (rx + t, ry + 9),
                         (rx + t + 7, ry + 9), 1)
        pygame.draw.line(surf, (40, 54, 52), (rx + (t + 4) % TILE, ry + 23),
                         (rx + (t + 4) % TILE + 7, ry + 23), 1)
        if seed % 7 == 0:                          # algae scum
            pygame.draw.ellipse(surf, (50, 62, 40),
                                (rx + (seed % 18) + 4,
                                 ry + ((seed // 7) % 18) + 4, 9, 5))
        if seed % 19 == 0:                         # rare cold glint
            pygame.draw.rect(surf, (88, 104, 100),
                             (rx + (seed % 26), ry + (seed * 5 % 26), 1, 1))
        # Cold sky-glints: a couple of tiny moving specks per tile, faintly
        # whiter than the algae ripples, drifting downstream. They give the
        # surface a live shimmer that sells "water" rather than "wet mud" --
        # especially under tilt where the dark patches don't read alone.
        gt = pygame.time.get_ticks()
        for k in range(2):
            phase = (gt // 110 + (seed >> k)) & 0x7FF
            gx = (phase + (seed * (k + 1))) % TILE
            gy = ((phase * 3) >> 1) % TILE
            life = phase & 31
            if life < 5:                           # only briefly visible
                bright = 96 + life * 6
                col = (min(255, bright - 12),
                       min(255, bright), min(255, bright - 4))
                pygame.draw.rect(surf, col, (rx + gx, ry + gy, 1, 1))
    elif ch == "@":
        # Void floor -- animated speck drift, plus a static darker
        # mottle so the void never reads as flat black.
        seed = tx * 73 + ty * 91 + pygame.time.get_ticks() // 80
        if seed % 13 == 0:
            pygame.draw.rect(surf, (40, 20, 60),
                             (rx + (seed % 28), ry + (seed * 3 % 28),
                              1, 1))
        static_seed = tx * 31 + ty * 47
        if static_seed % 5 == 0:
            pygame.draw.rect(surf, (16, 12, 24),
                             (rx + (static_seed % 26),
                              ry + (static_seed * 3 % 26), 2, 2))
    elif ch == "x":
        # Basement / interior stone-and-earth floor -- packed dark with
        # faint flagstone grout + a low mottle so it isn't a flat void,
        # then cracks, dark stains, and tally scratches over the top.
        seed = tx * 19 + ty * 41
        for i in range(2):                          # low-contrast mottle
            mx = rx + (seed * (i * 3 + 1)) % 26 + 2
            my = ry + (seed * (i * 5 + 3)) % 26 + 2
            pygame.draw.rect(surf, (36, 30, 38), (mx, my, 3, 3))
        if seed % 3 == 0:                           # faint flagstone grout
            pygame.draw.line(surf, (19, 15, 21),
                             (rx + 16, ry + 1), (rx + 16, ry + TILE - 1), 1)
        if seed % 4 == 0:
            pygame.draw.line(surf, (19, 15, 21),
                             (rx + 1, ry + 16), (rx + TILE - 1, ry + 16), 1)
        if seed % 11 == 0:
            pygame.draw.line(surf, (10, 8, 14),
                             (rx + 4, ry + (seed % 24)),
                             (rx + 28, ry + (seed % 24)), 1)
        if seed % 9 == 0:
            # A small dark stain -- never quite cleaned.
            pygame.draw.rect(surf, (16, 12, 16),
                             (rx + (seed * 2 % 24) + 2,
                              ry + (seed * 5 % 24) + 2, 4, 3))
        if seed % 17 == 0:
            # A scratched mark -- a vertical line, like a tally.
            pygame.draw.line(surf, (40, 32, 36),
                             (rx + (seed % 28), ry + 6),
                             (rx + (seed % 28), ry + 12), 1)
    elif ch == "d":
        # Dirt path -- pebbles + drag marks + occasional dark wet
        # patch so the path reads as worn AND grimy.
        seed = tx * 23 + ty * 47
        for i in range(3):
            sx = rx + ((seed * (i + 1)) % 24) + 4
            sy = ry + ((seed * (i + 3)) % 24) + 4
            col = (96, 72, 48) if i != 2 else (78, 56, 36)
            pygame.draw.rect(surf, col, (sx, sy, 2, 2))
        if seed % 5 == 0:
            pygame.draw.line(surf, (108, 82, 56), (rx + 2, ry + 16),
                             (rx + TILE - 2, ry + 16), 1)
        if seed % 9 == 0:
            # Dark wet patch -- the path remembers something.
            pygame.draw.rect(surf, (66, 44, 28),
                             (rx + (seed * 3 % 22) + 4,
                              ry + (seed * 7 % 22) + 4, 4, 3))
    elif ch in ("P", "Y"):
        # Paved asphalt -- cold grey aggregate speckle, the odd hairline crack
        # and a tar-dark patch. "Y" is the centre lane: it paints the faded
        # dashed centreline so the run of tiles reads as one paved road.
        seed = tx * 31 + ty * 17
        for i in range(4):
            sx = rx + ((seed * (i + 1)) % 26) + 3
            sy = ry + ((seed * (i + 2)) % 26) + 3
            g = 56 + (seed * (i + 1)) % 18
            pygame.draw.rect(surf, (g, g, g + 4), (sx, sy, 1, 1))    # aggregate
        if seed % 6 == 0:                          # tar-dark patch
            pygame.draw.rect(surf, (30, 29, 33),
                             (rx + (seed * 3 % 22) + 3,
                              ry + (seed * 5 % 22) + 3, 4, 3))
        if seed % 7 == 0:                          # hairline crack
            cx, cy = rx + (seed % 18) + 5, ry + 3
            pygame.draw.line(surf, (24, 23, 26), (cx, cy),
                             (cx + (seed % 6) - 3, cy + TILE - 6), 1)
        if ch == "Y" and (ty % 2 == 0):            # faded dashed centreline
            pygame.draw.rect(surf, (150, 138, 86),
                             (rx + TILE // 2 - 1, ry + 6, 2, TILE - 12))
    elif ch == ";":
        # Marsh mud -- wet, churned ground. Dark puddle blotches with a
        # cold standing-water glint, dead reeds, hairline mud cracks.
        seed = tx * 17 + ty * 29
        if seed % 2 == 0:
            pygame.draw.ellipse(surf, (27, 26, 22),
                                (rx + (seed % 16) + 2,
                                 ry + ((seed // 5) % 16) + 2, 13, 8))
        if seed % 5 == 0:                          # standing water
            pygame.draw.ellipse(surf, (42, 50, 50),
                                (rx + (seed % 14) + 5, ry + ((seed // 7) % 14) + 7, 9, 4))
            pygame.draw.ellipse(surf, (60, 70, 70),
                                (rx + (seed % 14) + 7, ry + ((seed // 7) % 14) + 8, 3, 1))
        if seed % 4 == 0:                          # dead reed
            fx = rx + (seed % 26) + 2
            pygame.draw.line(surf, (72, 68, 44), (fx, ry + 22), (fx - 1, ry + 13), 1)
        if seed % 7 == 0:                          # mud crack
            cx = rx + (seed % 20) + 4
            pygame.draw.line(surf, (20, 19, 16), (cx, ry + 8), (cx + 5, ry + 13), 1)
    elif ch == ".":
        # Plain dark stone -- the bare interior/dark-scene floor. It used to
        # draw as a flat fill; give it a low mottle, a faint grout seam, and
        # sparse grit so it stops reading as a single block.
        seed = tx * 23 + ty * 53
        for i in range(2):
            mx = rx + (_vary(seed, i) % 26) + 2
            my = ry + (_vary(seed, i + 3) % 26) + 2
            pygame.draw.rect(surf, (37, 35, 46), (mx, my, 3, 3))
        if seed % 4 == 0:
            pygame.draw.line(surf, (22, 20, 28),
                             (rx + 16, ry + 1), (rx + 16, ry + TILE - 1), 1)
        if seed % 5 == 0:
            pygame.draw.line(surf, (22, 20, 28),
                             (rx + 1, ry + 16), (rx + TILE - 1, ry + 16), 1)
        if seed % 9 == 0:
            pygame.draw.rect(surf, (24, 22, 30),
                             (rx + (seed * 3 % 24) + 2, ry + (seed * 5 % 24) + 2, 4, 3))
    # Macro shadow blotches for the ANIMATED floors only (the smooth cells
    # above already folded the shadow into the static tiles per sub-cell).
    if not smooth:
        shade = (math.sin(tx * 0.23 + ty * 0.15)
                 + 0.6 * math.sin(tx * 0.09 - ty * 0.19))
        a = int(max(0.0, -shade) * 30)
        if a:
            surf.blit(_dark_tile(min(58, a)), (rx, ry))


def is_floor_solid(ch):
    return FLOOR_DEFS.get(ch, {}).get("solid", False)


def is_object_solid(ch):
    od = OBJECT_DEFS.get(ch)
    return bool(od and od.get("solid"))


def floor_step_sound(ch):
    return FLOOR_DEFS.get(ch, FLOOR_DEFS["."])["step"]


# Human-readable scene labels for the HUD scene tag. The internal
# key is preserved (saves, exits, patrol routing all reference
# scene keys); only the on-screen label changes. Anything missing
# from this dict falls back to titlecase(key.replace('_', ' ')).
DISPLAY_NAMES = {
    "bedroom":              "the Spare Room",
    "lodge":                "Arcadia Lodge",
    "lodge_hall":           "the Guest Hall",
    "guest_room_a":         "a Guest Room",
    "guest_room_b":         "a Guest Room",
    "clerk_room":              "the Clerk's Loft",
    "maras_room":           "Mara's Room",
    "lodge_cellar":             "the Cellar",
    "lodge_yard":       "the Yard",
    "toby_house":            "the Kid's House",
    "shop":                 "General Store",
    "church":        "the Church",
    "sheriff_office":    "Sheriff's Office",
    "cornfield_path":          "Cornfield Path",
    "clearing":            "the Clearing",
    "barn":                 "the Barn",
    "well_bottom":          "the Shaft Floor",
    "well_passage":         "the Timber Racks",
    "works_cistern":           "the Cistern",
    "works_sorting":        "the Sorting Hall",
    "works_scriptorium":    "the Scriptorium",
    "works_sign":           "the Sign Chamber",
    # (the Deep Stair concept is CUT -- the room is the dig's dead end,
    # DESIGN.md §5 room 7)
    "works_deepface":      "the Deepest Face",
    "the_sump":             "the Sump",
    "the_cells":            "the Cells",
    "the_old_stores":          "the Old Stores",
    "depths_antechamber":   "the Old Workings",
    "depths_procession":    "the Procession",
    "depths_hall":          "the Kneeling Hall",
    "depths_threshing":     "the Threshing Floor",
    "depths_stair":         "the Winding Stair",
    "dark":                 "the Dark",
    "threshold":            "the Threshold",
    "effigy_grove":         "the Effigy Grove",
    "abandoned_farmhouse":        "the Abandoned Farmhouse",
    "brimley":            "Brimley",
    "schoolhouse":          "the Schoolhouse",
    "graveyard":            "the Graveyard",
    "country_lane":         "the Country Lane",
    "gravel_road_north":    "the Gravel Road",
    "backwoods_cabin":      "the Backwoods Cabin",
    "backwoods_cabin_interior": "the Cabin",
    "bell_tower":           "the Bell Tower",
    "cornfield_maze":       "the Cornfield",
}


def scene_display_name(scene):
    """Resolve a scene's HUD label. Builder override > DISPLAY_NAMES
    table > titlecased key."""
    if scene is None:
        return ""
    if getattr(scene, "display_name", None):
        return scene.display_name
    label = DISPLAY_NAMES.get(scene.key)
    if label:
        return label
    return scene.key.replace("_", " ").title()


# ---- Continuous wall mass (break the tile grid) ----
# Wall tiles are rendered as one near-black form with lit edges only on
# faces that touch open floor -- no per-tile borders or grout, so a run
# of wall stops reading as a row of grey blocks (the RimWorld tell).
_WALL_CHARS = frozenset("#W%&")
_COUNTER_CHARS = frozenset("5")   # kitchen counter / peninsula divider (waist-high box under tilt)
_RACK_CHARS = frozenset("s")      # the mine's lumber racks (low timber box under tilt)
# Door tiles cast the same floor-shadow as walls so a door in a south
# wall grounds into the building instead of leaving a lit threshold gap
# between the shadows of its flanking walls.
_DOOR_CHARS = frozenset(c for c, d in OBJECT_DEFS.items()
                        if d and d.get("kind") == "door")
_WINDOW_CHARS = frozenset(c for c, d in OBJECT_DEFS.items()
                          if d and d.get("kind") == "window")
# Trees and cornstalks: under tilt they're 3D STANDEES (camera-facing billboards
# stood up off the floor), not flat decals warped onto the ground, and they join
# the wall/occluder set returned by draw_terrain_tilted -- so a tree or a stalk
# in the maze depth-sorts + fades per-actor exactly like a wall. Collision is
# unchanged (passable 'j'/'p'/'A' still are; 'T'/'C' still solid).
_TILT_BILLBOARD_CHARS = frozenset(c for c, d in OBJECT_DEFS.items()
                                  if d and d.get("kind") in ("tree", "cornstalk"))
_CORN_CHARS = frozenset(c for c, d in OBJECT_DEFS.items()
                        if d and d.get("kind") == "cornstalk")
# Corn LOD: a field/maze is hundreds of stalks. Merge each maximal HORIZONTAL
# run of cornstalks (capped at _CORN_RUN_CAP wide) into ONE wide standee +
# occluder -- a thin maze wall or a dense block becomes a handful of cards, not
# one per tile (~40-70% fewer). Trees never merge (sparse).
_CORN_RUN_CAP = 4
_CORN_RUN_CACHE = {}


def _corn_runs(scene):
    """Per-scene LOD decomposition -> (anchors {(tx,ty): width}, suppressed
    {(tx,ty)}). A run's LEFT tile is its anchor (draws a width-wide card); the
    rest are suppressed (skipped, drawn by the anchor). Cached per scene id,
    cleared with the floor cache so a freed scene's id can't be reused stale."""
    c = _CORN_RUN_CACHE.get(id(scene))
    if c is not None:
        return c
    o = scene.objects
    W, H = scene.w, scene.h
    anchors, suppressed = {}, set()
    for y in range(H):
        x = 0
        while x < W:
            if o[y][x] in _CORN_CHARS:
                n = 1
                while (n < _CORN_RUN_CAP and x + n < W
                       and o[y][x + n] in _CORN_CHARS):
                    n += 1
                if n > 1:
                    anchors[(x, y)] = n
                    for i in range(1, n):
                        suppressed.add((x + i, y))
                x += n
            else:
                x += 1
    c = (anchors, suppressed)
    _CORN_RUN_CACHE[id(scene)] = c
    return c


_TILT_STANDEE_CACHE = {}


# Distance-LOD threshold (world-px, squared) for the tilted billboards. A tree
# or cornstalk farther than this from the camera centre is drawn with fewer
# rings / stalks and no fine detail: at that range it's small on screen and sits
# under Brimley's haze + sight fog, so the simplification is imperceptible but it
# roughly halves the per-tile solid cost for the dense back ranks of the woods
# and cornfield (the panning worst case). ~11 tiles out.
_TILT_LOD_FAR2 = (11 * TILE) ** 2

# Hard cull for billboard tiles (trees / cornstalks). Under the oblique camera
# the floor window reaches far toward the vanishing point, so a road/forest
# corridor (arrival_road tiles its treeline endlessly north) collects hundreds
# of tree tiles per frame -- but everything past this range sits at/above the
# fog horizon under the haze + sight fog and isn't visible. The tilt camera is
# orthographic, so those far trees are full-size, just stacked in the fog: pure
# wasted draws. Buildings (walls/doors/windows) are NOT culled -- only the
# billboards, which read as a solid treeline at range anyway.
_TILT_BILLBOARD_CULL_TILES = 21
_TILT_BILLBOARD_CULL2 = (_TILT_BILLBOARD_CULL_TILES * TILE) ** 2


def _tilt_lod_far(camera, tx, ty):
    """Is this billboard tile beyond the near-detail radius? (cheap, no trig)."""
    wx = tx * TILE + TILE / 2
    wy = ty * TILE + TILE / 2
    dx = wx - camera.cam_x
    dy = wy - camera.cam_y
    return (dx * dx + dy * dy) > _TILT_LOD_FAR2


# Tree-card cache. A tree's SHAPE (its silhouette relative to its ground point)
# depends only on its per-tile seed + the camera ANGLES (yaw/pitch/scale) --
# never on where the camera is panned to, since panning is a pure screen
# translation. So the 3D tree is rendered ONCE per (tile, angle bucket) into a
# small card and blitted at its projected base every frame after. During panning
# (constant angles) every tree is a cache hit: one project + one blit instead of
# 2-3 draw_solid, a dozen projects, and the polygon fills (the real per-frame
# cost). The cache re-renders only when the head turns (yaw bucket changes); the
# locked tilt pitch + zoom are effectively constant. FIFO-capped so roaming the
# 100x100 town doesn't grow it without bound.
_TREE_CARD_CACHE = {}
_TREE_CARD_ORDER = []
_TREE_CARD_CAP = 1600

# Passable, walk-through greenery ('p', 'j') reads as low BRUSH/saplings rather
# than a full tree, so the player can tell at a glance which growth blocks them
# ('T', solid) and which they can slip through -- a stealth-navigation tell --
# and the woods get a low understory layer instead of one stamped canopy height.
_TILT_BRUSH_CHARS = frozenset({"p", "j"})


def _draw_brush_body(surf, camera, wx, wy, seed, far):
    """A low scrub bush: a short woody stem under a clumped, ground-hugging mound
    of foliage (a couple of offset lobes near rank). Clearly under knee/waist
    height next to a tree, so passable growth reads as passable."""
    from rendering.solids import draw_solid
    g = _vary(seed, 5) % 12
    r = 8 + (_vary(seed, 2) % 5)            # spread 8..12
    hgt = 9 + (_vary(seed, 3) % 6)          # low: 9..14 world tall
    foliage = {
        "body": (30 + g, 50 + g, 26 + g // 2),
        "lo":   (18 + g // 2, 34 + g, 16 + g // 2),
        "rim":  (54 + g, 78 + g, 42 + g),
    }
    stem = {"body": (54 + g // 3, 42 + g // 4, 28 + g // 4),
            "lo": (30, 22, 14), "rim": (86, 62, 40)}
    # stubby woody base
    draw_solid(surf, camera, wx, wy,
               [(0, 1.6, 1.6), (hgt * 0.5, 1.2, 1.2)], stem)
    # main low foliage mound
    z0 = hgt * 0.30
    draw_solid(surf, camera, wx, wy,
               [(z0,             r * 0.5,  r * 0.5),
                (z0 + hgt * 0.45, r,        r),
                (z0 + hgt * 0.85, r * 0.7,  r * 0.7),
                (z0 + hgt * 1.10, r * 0.25, r * 0.25)],
               foliage)
    # a clumped side lobe or two so it reads as a bush, not a green ball
    if not far:
        for li in range(1 + (_vary(seed, 6) % 2)):
            ox = ((_vary(seed, 7 + li * 3) % 11) - 5) * 0.8
            oy = ((_vary(seed, 8 + li * 3) % 7) - 3) * 0.4
            rr = r * 0.55
            zb = z0 * 0.6
            draw_solid(surf, camera, wx + ox, wy + oy,
                       [(zb,            rr * 0.4, rr * 0.4),
                        (zb + rr,       rr,       rr),
                        (zb + rr * 1.9, rr * 0.3, rr * 0.3)],
                       foliage)


def _tilt_tree_solid(surf, camera, scene, tx, ty, ch, far=False):
    """Draw a tree by blitting its cached card (see _TREE_CARD_CACHE). The 3D
    body is rendered through `_tilt_tree_draw` on a cache miss; identical look,
    a fraction of the per-frame cost."""
    bx, by = camera.project(tx * TILE + 16, ty * TILE + 16, 0)
    # Trees + brush are bodies of revolution: rotating the view about the
    # vertical axis barely touches their silhouette (measured <=0.02% pixel
    # change across a FULL turn -- the lean/lobe offsets are sub-pixel at this
    # scale). So the card is keyed WITHOUT yaw: one build per (tile, pitch,
    # scale) that survives camera turns, instead of rebuilding every frame the
    # view rotates (the dominant per-frame cost in a treed scene). pitch +
    # scale stay in the key -- they DO reshape the projected body.
    key = (tx, ty, ch, far, round(camera.pitch, 2), round(camera.scale, 2))
    entry = _TREE_CARD_CACHE.get(key)
    if entry is None:
        entry = _build_tree_card(camera, scene, tx, ty, ch, far)
        _TREE_CARD_CACHE[key] = entry
        _TREE_CARD_ORDER.append(key)
        if len(_TREE_CARD_ORDER) > _TREE_CARD_CAP:
            _TREE_CARD_CACHE.pop(_TREE_CARD_ORDER.pop(0), None)
    card, ax, ay = entry
    if card is not None:
        surf.blit(card, (bx - ax, by - ay))


def _build_tree_card(camera, scene, tx, ty, ch, far):
    """Cache-miss path: render one tree to a tight SRCALPHA card. Returns
    (surface, anchor_x, anchor_y) where the anchor is the tree's ground point
    within the card, so the caller blits at (base_x - anchor_x, base_y -
    anchor_y). Uses a throwaway camera at the same angles whose origin pins the
    base to a fixed spot on a padded scratch surface; the tight crop comes from
    the rendered pixels' bounding rect."""
    from rendering.camera import Camera
    PAD = 90
    tmp = pygame.Surface((PAD * 2, PAD * 2), pygame.SRCALPHA)
    anchor = (PAD, int(PAD * 1.45))
    tcam = Camera(cam_x=tx * TILE + 16, cam_y=ty * TILE + 16,
                  pitch=camera.pitch, yaw=camera.yaw,
                  scale=camera.scale, origin=anchor)
    _tilt_tree_draw(tmp, tcam, scene, tx, ty, ch, far)
    rect = tmp.get_bounding_rect()
    if rect.width == 0 or rect.height == 0:
        return (None, 0, 0)
    card = tmp.subsurface(rect).copy().convert_alpha()
    return (card, anchor[0] - rect.x, anchor[1] - rect.y)


def _tilt_tree_draw(surf, camera, scene, tx, ty, ch, far=False):
    """A tree as a real volumetric body: a brown cylindrical trunk + a tapered
    canopy projected through the camera as a body of revolution. Anchored to
    the tile, the silhouette varies correctly under yaw (a billboard never
    does -- it always faces the camera, swinging with the head turn). Per-
    tile seed varies trunk girth, canopy size, lean, palette + an occasional
    secondary lobe so a band of trees doesn't read as a stamped row.
    Rendered once per (tile, angle) into a card by _tilt_tree_solid."""
    from rendering.solids import draw_solid
    seed = (tx * 73856093) ^ (ty * 19349663)
    wx = tx * TILE + 16
    wy = ty * TILE + 16
    if ch in _TILT_BRUSH_CHARS:
        _draw_brush_body(surf, camera, wx, wy, seed, far)
        return
    trunk_r = 2.4 + (_vary(seed, 0) % 10) * 0.12   # 2.4..3.5
    trunk_h = 13 + (_vary(seed, 1) % 7)            # 13..19
    canopy_r = 11 + (_vary(seed, 2) % 6)           # 11..16
    canopy_h = 24 + (_vary(seed, 3) % 9)           # 24..32
    lean_x = ((_vary(seed, 4) % 7) - 3) * 0.6      # -1.8..1.8
    g = _vary(seed, 5) % 12
    # Trunk -- the gnarled bole, slight base flare
    trunk_pal = {
        "body": (60 + g // 3, 42 + g // 4, 26 + g // 4),
        "lo":   (32 + g // 4, 22 + g // 4, 14 + g // 4),
        "rim":  (102 + g // 2, 72 + g // 3, 46 + g // 3),
    }
    draw_solid(surf, camera, wx, wy,
               [(0, trunk_r * 1.22, trunk_r * 1.22),
                (trunk_h * 0.5, trunk_r, trunk_r),
                (trunk_h, trunk_r * 0.86, trunk_r * 0.86)],
               trunk_pal)
    # The stand is NORTH-WOODS APRIL (2026-07 quality sprint; the old
    # summer-green canopy blobs read as "weird shaped trees" -- a smooth
    # body of revolution at this size is a lampshade). Two species by
    # seed: ~2/3 boreal SPRUCE -- a ragged dark cone of stacked, jittered
    # tiers, the shape this renderer is genuinely good at -- and ~1/3
    # BARE deciduous, a taller trunk with seeded branch strokes and no
    # canopy at all (the sealed winter only just let go; nothing has
    # leafed). Seasonally true (NARRATIVE §3: April, last year's corn
    # dead standing) and darker on the skyline than the green ever was.
    species = _vary(seed, 6) % 3
    if species < 2:
        # SPRUCE: stacked drooping tiers, each ring jittered so no two
        # trees repeat and no tier is a clean circle.
        spruce_pal = {
            "body": (18 + g // 2, 38 + g // 2, 26 + g // 3),
            "lo":   (10 + g // 3, 24 + g // 3, 16 + g // 3),
            "rim":  (32 + g // 2, 56 + g // 2, 38 + g // 2),
        }
        z0 = trunk_h * 0.55
        h = canopy_h * 1.15
        tiers = 2 if far else 3 + (_vary(seed, 7) % 2)
        for i in range(tiers):
            t = i / max(1, tiers - 1)              # 0 bottom .. 1 top
            jr = 0.82 + (_vary(seed, 8 + i) % 9) * 0.045   # 0.82..1.18
            rr = canopy_r * (1.05 - 0.62 * t) * jr
            tz = z0 + h * (0.06 + 0.86 * t)
            th = h * (0.34 if i < tiers - 1 else 0.26)
            jx = ((_vary(seed, 12 + i) % 7) - 3) * 0.5
            draw_solid(surf, camera, wx + lean_x + jx, wy,
                       [(tz, rr, rr),
                        (tz + th * 0.55, rr * 0.62, rr * 0.62),
                        (tz + th, rr * 0.22, rr * 0.22)],
                       spruce_pal)
    else:
        # BARE: the trunk carries on past its bole into a leader + seeded
        # branch strokes. Projected as world lines at build time (the card
        # is yaw-keyless like every tree; branch parallax across a head
        # turn is background-subtle).
        bare = (54 + g // 3, 40 + g // 4, 28 + g // 4)
        top_h = trunk_h + canopy_h * 0.9
        p0 = camera.project(wx + lean_x * 0.4, wy, trunk_h * 0.8)
        p1 = camera.project(wx + lean_x, wy, top_h)
        pygame.draw.line(surf, bare, p0, p1, 2)
        n_br = 3 if far else 5 + (_vary(seed, 7) % 3)
        for i in range(n_br):
            fz = 0.35 + 0.6 * ((_vary(seed, 8 + i) % 97) / 97.0)
            bz = trunk_h * 0.8 + (top_h - trunk_h * 0.8) * fz
            ang = ((_vary(seed, 16 + i) % 628) / 100.0)
            ln = canopy_r * (0.55 + (_vary(seed, 24 + i) % 7) * 0.09) \
                * (1.0 - 0.5 * fz)
            bx0 = wx + lean_x * fz
            q0 = camera.project(bx0, wy, bz)
            q1 = camera.project(bx0 + math.cos(ang) * ln,
                                wy + math.sin(ang) * ln * 0.5,
                                bz + ln * 0.7)
            pygame.draw.line(surf, bare, q0, q1, 1)
            if not far and i % 2 == 0:
                q2 = camera.project(bx0 + math.cos(ang) * ln * 1.25,
                                    wy + math.sin(ang) * ln * 0.6,
                                    bz + ln * 1.05)
                pygame.draw.line(
                    surf, (bare[0] - 12, bare[1] - 10, bare[2] - 8),
                    q1, q2, 1)


# Corn-card cache. With the sway frozen (see _tilt_corn_draw) a corn cluster
# renders once into a card and blits thereafter instead of re-projecting ~50
# stalk lines every frame. Cards are YAW-INDEPENDENT (2026-07 FPS fix): the
# cluster is a seeded bundle of near-vertical stalks with no coherent facing,
# so a yaw-0 card blitted at the live projected anchor is indistinguishable
# from a re-projection at play scale -- exactly how the trees work. (The old
# per-0.04-rad-bucket keys needed ~15k cards for a look sweep across the
# maze's ~420 visible tiles against a 1200 cap: FIFO thrash rebuilt every
# card every frame and a head-turn in the cornfield ran at slideshow speed.)
_CORN_CARD_CACHE = {}
_CORN_CARD_ORDER = []
_CORN_CARD_CAP = 1200


def _tilt_corn_solid(surf, camera, scene, tx, ty, ch, far=False):
    """Draw a corn cluster by blitting its cached card (see _CORN_CARD_CACHE).
    The stalks are rendered through `_tilt_corn_draw` on a cache miss."""
    bx, by = camera.project(tx * TILE + 16, ty * TILE + 16, 0)
    key = (tx, ty, far, round(camera.pitch, 2), round(camera.scale, 2))
    entry = _CORN_CARD_CACHE.get(key)
    if entry is None:
        entry = _build_corn_card(camera, scene, tx, ty, ch, far)
        _CORN_CARD_CACHE[key] = entry
        _CORN_CARD_ORDER.append(key)
        if len(_CORN_CARD_ORDER) > _CORN_CARD_CAP:
            _CORN_CARD_CACHE.pop(_CORN_CARD_ORDER.pop(0), None)
    card, ax, ay = entry
    if card is not None:
        surf.blit(card, (bx - ax, by - ay))


def _build_corn_card(camera, scene, tx, ty, ch, far):
    """Cache-miss path: render one corn cluster to a tight SRCALPHA card via a
    throwaway camera pinned at the tile centre. Always built at YAW 0 so one
    card serves every look direction (the anchor still projects through the
    live camera, so the FIELD rotates; only the parallax INSIDE one 30px
    cluster is frozen, which nothing at play scale can read)."""
    from rendering.camera import Camera
    # Scratch the cluster is drawn into before the tight crop, sized from the
    # measured worst-case corn extents across every corn scene (up=49,
    # down=10, half=27) at full tilt and padded.
    PADX, PADY, BASE = 40, 65, 20
    tmp = pygame.Surface((PADX * 2, PADY + BASE), pygame.SRCALPHA)
    anchor = (PADX, PADY)
    tcam = Camera(cam_x=tx * TILE + 16, cam_y=ty * TILE + 16,
                  pitch=camera.pitch, yaw=0.0,
                  scale=camera.scale, origin=anchor)
    _tilt_corn_draw(tmp, tcam, scene, tx, ty, ch, far)
    rect = tmp.get_bounding_rect()
    if rect.width == 0 or rect.height == 0:
        return (None, 0, 0)
    card = tmp.subsurface(rect).copy().convert_alpha()
    return (card, anchor[0] - rect.x, anchor[1] - rect.y)


def _tilt_corn_draw(surf, camera, scene, tx, ty, ch, far=False):
    """A corn tile as 5-6 stalks drawn as REAL 3D lines projected through the
    camera: each stalk has a ground base, a midpoint, a wind-leaned tip, four
    leaves (a low pair + an upper pair) fanning at mid-height, and a paler
    tassel + tassel beard at the top. Anchored in the scene so the cluster
    turns with yaw (a camera-facing card never does). The layout mirrors the
    flat _draw_corn proportions but uses thicker strokes + extra leaves so
    a dense cornfield reads as a wall under tilt, not a thicket of bare twigs.
    The tip lean is STATIC (seeded per stalk) rather than animated, so the
    cluster is a pure function of (tile, angle) and renders once into a cached
    card like the trees -- the sway was a ~2px wiggle, invisible at play scale
    but the one thing that kept corn redrawn every frame."""
    seed = (tx * 73856093) ^ (ty * 19349663)
    wx0 = tx * TILE
    wy0 = ty * TILE
    # Far LOD: 3 stalks and body-only (no leaves, no ears, no tassel beard). A
    # dense back-rank corn tile reads as the same green wall at range, but the
    # per-stalk leaf/ear/beard projections were the bulk of the cost.
    n = 3 if far else 7 + (_vary(seed, 0) % 2)   # 7 or 8 stalks (near) -- denser
                                                 # so a lane reads as a wall of
                                                 # corn, not standing grass
    g = _vary(seed, 1) % 10
    stalk_dk = (40 + g // 2, 54 + g // 2, 26 + g // 3)
    stalk_col = (58 + g, 72 + g, 38 + g // 2)
    blade_col = (82 + g, 96 + g, 48 + g)
    blade_hi = (108 + g, 124 + g, 64 + g)
    tip_col   = (170 + g, 142, 72)
    tassel_col = (208 + g, 184, 96)
    amp = 2.0 + (_vary(seed, 2) % 3)
    ph  = (seed % 628) / 100.0
    for si in range(n):
        bx_off = 5 + (si * (TILE - 10)) / max(1, n - 1) + (_vary(seed, 30 + si) % 5) - 2
        sx_off = bx_off + (_vary(seed, 10 + si) % 7) - 3
        top_h  = TILE + 18 + (_vary(seed, 20 + si) % 12)      # world height
                                                              # taller (~50-62)
                                                              # so a stalk
                                                              # over-tops a
                                                              # player and the
                                                              # lane feels
                                                              # head-deep
        # Per-stalk wy jitter so they don't all line up at the tile's south edge
        wy_jit = (_vary(seed, 40 + si) % 9) - 4
        # Static per-stalk wind-lean (was an animated sin sway). Seeded so the
        # field still bends every-which-way and reads as varied, not stamped.
        tip_sway = (math.sin(ph + si * 0.7) + 0.4 * math.sin(ph * 2.3 + si)) * amp
        wx_base = wx0 + bx_off
        wy_base = wy0 + TILE - 1 + wy_jit * 0.4
        wx_top  = wx0 + sx_off + tip_sway
        wx_mid  = (wx_base + wx_top) / 2
        wz_mid  = top_h / 2
        p_base = camera.project(wx_base, wy_base, 0)
        p_mid  = camera.project(wx_mid,  wy_base, wz_mid)
        p_top  = camera.project(wx_top,  wy_base, top_h)
        # Dark backing stroke -> lighter front stroke for body
        pygame.draw.line(surf, stalk_dk,  p_base, p_mid, 3)
        pygame.draw.line(surf, stalk_dk,  p_mid,  p_top, 3)
        pygame.draw.line(surf, stalk_col, p_base, p_mid, 2)
        pygame.draw.line(surf, stalk_col, p_mid,  p_top, 2)
        # Two pairs of leaves (lower + upper) fanning out in world space, plus
        # an occasional ear of corn. Far LOD drops them (body-only): these
        # per-stalk projections were the bulk of the cost and don't read at range.
        if not far:
            for ly_off, side in (
                    (wz_mid * 0.55, -1), (wz_mid * 0.55, 1),
                    (wz_mid * 1.05, -1), (wz_mid * 1.05, 1)):
                base_x = wx_base + (wx_mid - wx_base) * (ly_off / wz_mid)
                leaf_x = base_x + side * 9
                leaf_y = wy_base + side * 0.6
                leaf_z = ly_off - 1
                p_attach = camera.project(base_x, wy_base, ly_off)
                p_tip = camera.project(leaf_x, leaf_y, leaf_z)
                pygame.draw.line(surf, blade_col, p_attach, p_tip, 2)
                # Lit upper edge
                p_tip_hi = camera.project(leaf_x - side * 0.5, leaf_y, leaf_z + 1)
                pygame.draw.line(surf, blade_hi, p_attach, p_tip_hi, 1)
            # Ear of corn at ~60% height on ~half the stalks. A short husked
            # cylinder offset from the stalk on the side opposite the highest
            # leaf, so the cluster reads as "ears of corn in the rows" rather
            # than pure foliage. Tiny, but it sells the stalks as edible crop.
            if (_vary(seed, 50 + si) & 1):
                ear_side = 1 if (_vary(seed, 60 + si) & 1) else -1
                ear_z = top_h * 0.58
                ear_x = wx_base + ear_side * 3.5
                ear_y = wy_base + 1
                ear_b = camera.project(ear_x, ear_y, ear_z - 3)
                ear_t = camera.project(ear_x, ear_y, ear_z + 3)
                pygame.draw.line(surf, (190, 168, 96), ear_b, ear_t, 3)
                pygame.draw.line(surf, (108, 92, 50), ear_b, ear_t, 1)
                # silk: a couple of fine wisps at the cob tip
                silk = camera.project(ear_x + ear_side * 1.0, ear_y,
                                      ear_z + 3 + 1.5)
                pygame.draw.line(surf, (228, 208, 130), ear_t, silk, 1)
        # Tassel head: a pale paddle + a beard of fine strokes radiating out
        # (the beard is near-LOD only).
        p_tassel_top = camera.project(wx_top, wy_base, top_h + 5)
        pygame.draw.line(surf, tip_col, p_top, p_tassel_top, 2)
        pygame.draw.circle(surf, tassel_col,
                           (int(p_tassel_top[0]), int(p_tassel_top[1])), 2)
        if not far:
            for k in range(3):
                ang = -math.pi / 2 + (k - 1) * 0.6
                p_b = camera.project(wx_top + math.cos(ang) * 3,
                                     wy_base + math.sin(ang) * 0.6,
                                     top_h + 5 + math.sin(ang) * 2)
                pygame.draw.line(surf, tassel_col, p_tassel_top, p_b, 1)


_GRASS_CARD_CACHE = {}
_GRASS_CARD_ORDER = []
_GRASS_CARD_CAP = 1200


def _tilt_grass_solid(surf, camera, scene, tx, ty, far=False):
    """A `:` cover-floor tile stood up as a TALL-GRASS tuft (the stealth
    visibility fix, TODO #5: cover the player can hide in must READ as
    something to wade into, not a floor tint). Same cached-card pattern as
    the corn clusters; the blades are the concealment made visible and
    change nothing about collision, sight, or the cover rules."""
    bx, by = camera.project(tx * TILE + 16, ty * TILE + 16, 0)
    key = (tx, ty, far, round(camera.pitch, 2), round(camera.scale, 2))
    entry = _GRASS_CARD_CACHE.get(key)
    if entry is None:
        entry = _build_grass_card(camera, scene, tx, ty, far)
        _GRASS_CARD_CACHE[key] = entry
        _GRASS_CARD_ORDER.append(key)
        if len(_GRASS_CARD_ORDER) > _GRASS_CARD_CAP:
            _GRASS_CARD_CACHE.pop(_GRASS_CARD_ORDER.pop(0), None)
    card, ax, ay = entry
    if card is not None:
        surf.blit(card, (bx - ax, by - ay))


def _build_grass_card(camera, scene, tx, ty, far):
    """Cache-miss path: render one tuft to a tight SRCALPHA card via a
    throwaway camera pinned at the tile centre (the corn-card recipe)."""
    from rendering.camera import Camera
    PADX, PADY, BASE = 26, 34, 14
    tmp = pygame.Surface((PADX * 2, PADY + BASE), pygame.SRCALPHA)
    anchor = (PADX, PADY)
    tcam = Camera(cam_x=tx * TILE + 16, cam_y=ty * TILE + 16,
                  pitch=camera.pitch, yaw=0.0,
                  scale=camera.scale, origin=anchor)
    _tilt_grass_draw(tmp, tcam, tx, ty, far)
    rect = tmp.get_bounding_rect()
    if rect.width == 0 or rect.height == 0:
        return (None, 0, 0)
    card = tmp.subsurface(rect).copy().convert_alpha()
    return (card, anchor[0] - rect.x, anchor[1] - rect.y)


def _tilt_grass_draw(surf, camera, tx, ty, far=False):
    """One tuft: 5-7 waist-high blades as projected 3D lines, seeded
    static lean, dead-straw accents (April canon: last year's growth,
    never lush). Far LOD drops to 3 plain blades."""
    seed = (tx * 73856093) ^ (ty * 19349663)
    wx0 = tx * TILE
    wy0 = ty * TILE
    n = 3 if far else 5 + (_vary(seed, 0) % 3)
    g = _vary(seed, 1) % 8
    blade_dk = (40 + g, 50 + g, 32 + g // 2)
    blade_col = (54 + g, 66 + g, 42 + g // 2)
    blade_hi = (68 + g, 80 + g, 50 + g)
    straw = (96 + g, 90 + g, 54 + g // 2)
    for si in range(n):
        bx_off = 4 + (si * (TILE - 8)) / max(1, n - 1) + (_vary(seed, 30 + si) % 5) - 2
        h = 10 + (_vary(seed, 20 + si) % 9)              # waist-high, uneven
        lean = ((_vary(seed, 10 + si) % 9) - 4) * 0.9
        gx = wx0 + bx_off
        gy = wy0 + 10 + (_vary(seed, 40 + si) % 14)
        p0 = camera.project(gx, gy, 0)
        p1 = camera.project(gx + lean * 0.4, gy, h * 0.55)
        p2 = camera.project(gx + lean, gy, h)
        col = blade_col if si % 3 else blade_hi
        if not far and (_vary(seed, 50 + si) % 4) == 0:
            col = straw                                  # a dead-dry blade
        pygame.draw.line(surf, blade_dk, p0[:2], p1[:2], 2)
        pygame.draw.line(surf, col, p1[:2], p2[:2], 1 if far else 2)


def _tilt_standee(surf, camera, scene, tx, ty, ch):
    """Stand a tree / cornstalk up as a WORLD-ANCHORED card whose base sits on
    the floor at the tile centre and whose horizontal axis tracks world-X. The
    flat tile art (_draw_tree/_draw_corn) is rendered onto a card with the
    trunk/stalk base at the bottom-centre; the card is then scaled to the
    projected screen-width of its world footprint AND rotated to follow the
    row's tilt under yaw, so the foliage anchors in the scene instead of
    swinging to face the camera. Corn merges into a width-wide run card (LOD);
    cards are CACHED + convert_alpha'd (cleared on scene change with the floor
    cache); trees keep a soft contact shadow."""
    kind = OBJECT_DEFS.get(ch, {}).get("kind")
    width = 1
    if kind == "cornstalk":                # LOD: this tile may anchor a run
        wtx = tx % scene.w if scene.wrap_x else tx
        wty = ty % scene.h if scene.wrap_y else ty
        width = _corn_runs(scene)[0].get((wtx, wty), 1)
        key = (kind, wtx, wty, width)
    else:
        key = (kind, (tx * 73856093) ^ (ty * 19349663))
    card = _TILT_STANDEE_CACHE.get(key)
    if card is None:
        CH = 60
        if kind == "cornstalk":
            CW = width * TILE + 16         # one row of `width` stalk clumps
            card = pygame.Surface((CW, CH), pygame.SRCALPHA)
            for i in range(width):
                s = ((wtx + i) * 73856093) ^ (wty * 19349663)
                _draw_corn(card, 8 + i * TILE, CH - TILE, s)
        else:
            CW = 72                        # canopy spills past the tile
            card = pygame.Surface((CW, CH), pygame.SRCALPHA)
            _draw_tree(card, CW // 2 - 16, CH - TILE,
                       (tx * 73856093) ^ (ty * 19349663))
        card = card.convert_alpha()        # fast per-pixel-alpha blits
        _TILT_STANDEE_CACHE[key] = card
    # The card represents a width-wide strip of foliage anchored along the
    # world's +X axis. Its bottom edge is a horizontal world-line at z=0; its
    # top edge is the same line lifted to the card's pixel height in world
    # units. Project both endpoints of the bottom edge to screen; the segment
    # between them is the row's WORLD-anchored base under the current yaw,
    # so as the camera turns the row foreshortens / leans with the field
    # instead of swinging to face the camera.
    sw, sh = card.get_size()
    half_world = sw / 2.0                  # card's half-extent in WORLD units
    wx_center = tx * TILE + (width * TILE) // 2
    wy_world = ty * TILE + 16
    p_left = camera.project(wx_center - half_world, wy_world, 0.0)
    p_right = camera.project(wx_center + half_world, wy_world, 0.0)
    if kind != "cornstalk":                # trees grounded; corn is too dense
        bx, by = camera.project(wx_center, wy_world, 0.0)
        _ground_shadow(surf, bx, by, 12, 5, 70)
    base_len = math.hypot(p_right[0] - p_left[0], p_right[1] - p_left[1])
    if base_len < 2:
        return                              # seen edge-on along the row -> a sliver
    rise = sh * (0.4 + 0.6 * camera.ground_squash())   # foreshortened upright
    scaled = pygame.transform.scale(card,
                                    (max(2, int(base_len)), max(2, int(rise))))
    angle = math.degrees(math.atan2(-(p_right[1] - p_left[1]),
                                    p_right[0] - p_left[0]))
    if abs(angle) > 0.5:
        final = pygame.transform.rotate(scaled, angle)
    else:
        final = scaled
    nw, nh = final.get_size()
    # pygame.rotate keeps the surface's geometric centre in place. The card's
    # original bottom-centre (offset (0, rise/2) from its centre before
    # rotation) lands at (rise/2 * sin(a), rise/2 * cos(a)) from the new
    # centre once rotated -- anchor that point to the projected mid-base so
    # the stalks/canopy stand ON the floor at the row.
    a_rad = math.radians(angle)
    bc_off_x = (rise / 2.0) * math.sin(a_rad)
    bc_off_y = (rise / 2.0) * math.cos(a_rad)
    mid_x = (p_left[0] + p_right[0]) / 2.0
    mid_y = (p_left[1] + p_right[1]) / 2.0
    surf.blit(final, (int(mid_x - nw / 2.0 - bc_off_x),
                      int(mid_y - nh / 2.0 - bc_off_y)))


_WALL_BASE = (19, 18, 23)
_WALL_FACE = (50, 48, 56)
_WALL_TOP = (74, 72, 82)
_WALL_FOOT = (8, 7, 11)


def _is_wall(scene, tx, ty):
    if scene.wrap_y:
        ty %= scene.h
    if scene.wrap_x:
        tx %= scene.w
    if 0 <= ty < scene.h and 0 <= tx < scene.w:
        return scene.objects[ty][tx] in _WALL_CHARS
    return True   # off-map reads as wall so the mass closes at edges


# --- Interior partition corner BEVEL (2026-07, DESIGN.md §6) -----------------
# The blocky 90deg corner where an interior partition wall juts into a room
# reads as a chunky box tip. BEVEL only the exposed CONVEX corners of a wall
# tile: a convex corner exists ONLY where two ADJACENT tile faces are both open
# to interior floor (and the diagonal too, so two masses that merely kiss at a
# point don't open a peek gap). That makes it orthogonal to the wall-run MERGE
# (DESIGN §6 continuous mass): a mid-run / tee / shell tile has < 2 adjacent
# open sides -> no convex corner -> byte-identical. Draw-only (collision + sight
# stay tile-based, like the interior-door leaves). Gated to _BEVEL_SCENES so
# every other scene is a strict no-op.
_BEVEL_INSET = TILE * 0.28              # pull-in along each meeting edge (~9px)
# The above-ground BUILDING interiors (framed/plank walls): their partition
# juts get chamfered. NOT the mine (hewn rock reads right thick) nor outdoors.
_BEVEL_SCENES = frozenset({
    "shop", "church", "barn", "schoolhouse", "sheriff_office",
    "bedroom", "clerk_room", "guest_room_a", "guest_room_b",
    "lodge", "lodge_hall", "toby_house",
    "abandoned_farmhouse", "lodge_cellar",
})
_BV_NW, _BV_NE, _BV_SE, _BV_SW = 1, 2, 4, 8


def _bevel_corners(scene, tx, ty):
    """Bitmask of this wall tile's exposed convex corners to bevel (0 = none,
    the verbatim square box). A corner is beveled iff BOTH its orthogonal
    neighbours AND its diagonal are open interior floor ('.'). Pure function of
    the tile + its 8 neighbour chars + the scene gate, so the wall-box card
    cache stays valid (equal key -> identical geometry)."""
    if getattr(scene, "key", None) not in _BEVEL_SCENES:
        return 0
    if getattr(scene, "key", None) in _SLAB_SCENES:
        return 0                           # the slab supersedes the bevel here
    W, H = scene.w, scene.h

    def _c(x, y):
        if scene.wrap_x:
            x %= W
        if scene.wrap_y:
            y %= H
        if 0 <= x < W and 0 <= y < H:
            return scene.objects[y][x]
        return None                    # off-map: not floor -> never bevels

    if _c(tx, ty) not in _WALL_CHARS:
        return 0

    def f(x, y):
        return _c(x, y) == "."         # strictly interior walkable floor

    fN, fS = f(tx, ty - 1), f(tx, ty + 1)
    fE, fW = f(tx + 1, ty), f(tx - 1, ty)
    m = 0
    if fN and fW and f(tx - 1, ty - 1):
        m |= _BV_NW
    if fN and fE and f(tx + 1, ty - 1):
        m |= _BV_NE
    if fS and fE and f(tx + 1, ty + 1):
        m |= _BV_SE
    if fS and fW and f(tx - 1, ty + 1):
        m |= _BV_SW
    return m


def _bevel_poly_local(bevel, size, inset):
    """The tile's flat-mass footprint polygon in LOCAL pixel coords (origin at
    the tile's top-left, +x east / +y south), with each beveled corner's square
    vertex replaced by two points pulled `inset` in along each edge. Order walks
    the perimeter; a non-beveled corner emits its raw vertex twice (degenerate,
    harmless)."""
    s, b = size, inset
    nw_n = (b, 0) if bevel & _BV_NW else (0, 0)
    ne_n = (s - b, 0) if bevel & _BV_NE else (s, 0)
    ne_e = (s, b) if bevel & _BV_NE else (s, 0)
    se_e = (s, s - b) if bevel & _BV_SE else (s, s)
    se_s = (s - b, s) if bevel & _BV_SE else (s, s)
    sw_s = (b, s) if bevel & _BV_SW else (0, s)
    sw_w = (0, s - b) if bevel & _BV_SW else (0, s)
    nw_w = (0, b) if bevel & _BV_NW else (0, 0)
    return [nw_n, ne_n, ne_e, se_e, se_s, sw_s, sw_w, nw_w]


# --- Thin-slab walls (2026-07, maintainer "walls are no longer tiles") -------
# A wall tile stops being a full TILE box and becomes a THIN SLAB. To keep the
# thinned walls CONNECTED and smooth (the maintainer's second ask -- no fat
# junction bulging out of thin runs, no notch), a tile's footprint is the UNION
# of up to two BANDS:
#   - a VERTICAL band (present when the tile has a wall neighbour N or S, i.e.
#     it is part of a vertical run) and/or
#   - a HORIZONTAL band (present when it has a wall neighbour E or W).
# A straight run is ONE band; an L-corner / T / cross is the union of both, so
# the thin walls meet flush. Each band is THIN across (its cross-thickness) and
# reaches to the tile edge ONLY where the run continues (a wall neighbour), else
# stops at the other band's crossbar -- so a corner/end never pokes a stub into
# a room. The cross-thickness hugs by the neighbours' openness: floor/wall BOTH
# sides -> CENTRE; open ONE side (the other off-map) -> HUG the open side (the
# building SHELL thins toward the void, the room face unchanged); a lone pillar
# with no wall neighbour stays FULL.
# Single-sourced: both draw layers (_draw_wall_mass flat footprint + _extrude_box
# 3D box, looped per band) AND the collision/sight/nav predicates
# (scenes/base.py, point-in-ANY-band) read this, so the geometry the player SEES
# is what they bump and the AI's line of sight obeys -- unlike the draw-only
# bevel. Gated to _SLAB_SCENES; every other scene returns None -> full tile.
#
# MATERIAL STYLES (2026-07, the rollout foundation): a slab scene picks a
# material from _WALL_STYLES via _SLAB_STYLE, so thickness + corner round + (1b)
# surface roughness read the CONSTRUCTION -- a thin smooth plank partition vs a
# fat rough stone wall vs a heavy timber -- from one table. `thick` is the band
# thickness as a fraction of TILE; `round` the fillet radius as a fraction of
# that thickness (0 = square); `rough` the outline jitter amplitude in px
# (0 = smooth; Phase 1b). Adding a scene is one _SLAB_STYLE line.
# `tint` is a (dr, dg, db) delta added to the near-black wall palette so each
# material carries a COLOUR too (kept dark + muddy + desaturated, the Darkwood
# rule -- no cheerful primaries): warm pine, cold stone, red-brown old timber,
# pale plaster. It reads only where the interior light pools land.
_WALL_STYLES = {
    "plank":   {"thick": 0.50, "round": 0.50, "rough": 0.0, "tint": (30, 14, -6)},   # warm pine
    "plaster": {"thick": 0.44, "round": 0.28, "rough": 0.0, "tint": (26, 22, 12)},   # pale warm grey
    "timber":  {"thick": 0.66, "round": 0.34, "rough": 1.4, "tint": (34, 6, -16)},   # dark red-brown
    "stone":   {"thick": 0.80, "round": 0.30, "rough": 2.6, "tint": (2, 14, 26)},    # cold blue-grey
    "brick":   {"thick": 0.62, "round": 0.22, "rough": 1.0, "tint": (44, 2, -18)},   # dark fired clay
    # hewn ROCK (the mine, Phase 3): full-THICK (thick 1.0 -> the slab bands fill
    # the whole tile, so DRAW roughens but collision stays the tile grid), NO
    # corner round (rock breaks sharp + jagged, not filleted arcs), and a heavy
    # rough so the wall face reads irregular/organic instead of a machined box.
    "rock":    {"thick": 1.00, "round": 0.00, "rough": 3.2, "tint": (14, 10, 4)},    # dark muddy earth-rock
    # A grassy HILL cut open: the SIDE/foot faces are cold exposed STONE (the
    # `tint`), but the flat TOP is GRASS (`top_tint` -- a per-face override, so
    # a mound reads as green turf on top with bare stone showing where it is cut
    # into, e.g. an adit mouth). Only `turf` sets top_tint; every other style
    # (and every non-styled scene) leaves it None -> the top uses `tint` ->
    # byte-identical.
    "turf":    {"thick": 1.00, "round": 0.55, "rough": 3.0, "tint": (2, 12, 18),
                "top_tint": (-18, 26, -36)},                                        # green grass on stone
}
_SLAB_STYLE = {
    "shop": "plank",
    # Wave A -- the small refuges (thin walls, gentle; SAFE_SCENES stay flat-lit)
    "bedroom": "plaster",
    "clerk_room": "plaster",
    "guest_room_a": "plaster",
    "guest_room_b": "plaster",
    "toby_house": "plank",
    # Wave B/C -- the three principal-seat interiors (maintainer call): the
    # church reads its BOARD walls (plank, matching draw_crane_tableau), the
    # Sheriff's office a pale institutional plaster, the Arcadia common room its
    # rustic timber (the antler/firewood/buck-head lodge dressing).
    "church": "plank",
    "sheriff_office": "plaster",
    "lodge": "timber",
    # Wave 3 -- the rest of the above-ground interiors (finishes Phase 2): the
    # barn's heavy timber, the schoolhouse's board plank, the Arcadia guest
    # corridor's plaster (matching its rooms), the lodge cellar's rough STONE
    # masonry (the first stone scene), the weathered farmhouse's timber.
    "barn": "timber",
    "schoolhouse": "plank",
    "lodge_hall": "plaster",
    "lodge_cellar": "stone",
    "abandoned_farmhouse": "timber",
}
_SLAB_SCENES = frozenset(_SLAB_STYLE)    # derived: the scenes that render THIN

# Phase 3 -- the MINE reimagined as hewn rock. The Works + Depths get the `rock`
# style (full-thick, so the DRAW roughens but collision/sight/nav stay the tile
# grid -- these scenes are deliberately NOT in _SLAB_SCENES, so `_obj_solid_here`
# never routes them through the thin-band collision; only the styled DRAW picks
# them up via `_wall_style`). The list mirrors config.UNDERGROUND_SCENES + Mara's
# cell (hardcoded here to keep terrain dependency-free, like _SLAB_STYLE).
_ROCK_STYLE = {k: "rock" for k in (
    "well_bottom", "well_passage",
    "works_cistern", "works_sorting", "works_scriptorium", "works_sign",
    "works_deepface", "maras_room",
    "depths_antechamber", "depths_procession", "depths_hall",
    "depths_threshing", "depths_stair",
    "the_sump", "the_cells", "the_old_stores",
)}
# The effigy grove is outdoors, but its mine MOUTH is a HILL with stone cut into
# it (the W tiles): the `turf` style renders the mound with a GRASS top and bare
# STONE side/cut faces, so it reads as a green hill with a stone adit dug into
# it, in the game's own wall-geometry (not a grey building wall). Full-thick like
# rock (collision reads the tile grid), so it joins _ROCK_STYLE for that routing
# but with the turf material.
_ROCK_STYLE["effigy_grove"] = "turf"
_ROCK_SCENES = frozenset(_ROCK_STYLE)    # derived: full-thick + rough-hewn rock


def _wall_style(scene):
    """The wall material style dict for this scene, or None if it has no styled
    walls (renders verbatim full-tile). A THIN slab scene reads _SLAB_STYLE; a
    full-thick ROCK scene (the mine) reads _ROCK_STYLE. Single source for band
    thickness + corner round + roughness + colour tint. (A test that injects a
    key into _SLAB_STYLE still resolves.)"""
    key = getattr(scene, "key", None)
    if key in _SLAB_SCENES:                 # THIN slab (a test may inject here)
        return _WALL_STYLES.get(_SLAB_STYLE.get(key, "plank"), _WALL_STYLES["plank"])
    if key in _ROCK_STYLE:                  # full-thick hewn ROCK (the mine)
        return _WALL_STYLES.get(_ROCK_STYLE[key], _WALL_STYLES["stone"])
    return None


def _tint_col(col, t):
    """Apply a material tint delta to a palette colour, clamped to [0, 255]."""
    return (max(0, min(255, col[0] + t[0])),
            max(0, min(255, col[1] + t[1])),
            max(0, min(255, col[2] + t[2])))


def _wall_tint_for(scene):
    """The material tint delta for this scene's walls, or (0,0,0) if none
    (non-slab scene, or a slab scene whose style declares no tint)."""
    style = _wall_style(scene)
    return style.get("tint", (0, 0, 0)) if style else (0, 0, 0)


def _wall_top_tint_for(scene):
    """The tint delta for the wall TOP face -- a style's `top_tint` override
    (e.g. `turf`'s green grass over stone sides), else the same as the side
    `tint`. A style without `top_tint` and a non-styled scene both fall back to
    the side tint, so the top is byte-identical to before this override."""
    style = _wall_style(scene)
    if not style:
        return (0, 0, 0)
    return style.get("top_tint", style.get("tint", (0, 0, 0)))


def _wall_slab(scene, tx, ty):
    """This wall tile's thin-slab footprint as a LIST of tile-local rects
    (x0, y0, x1, y1) px -- one per present band (1 for a run, 2 for a
    corner/tee/cross) -- or None for a FULL tile (non-slab scene, non-wall tile,
    or a lone pillar). Pure function of the tile + its 4 orthogonal neighbour
    chars + the scene gate, so the wall-box card cache and the nav grid stay
    valid."""
    style = _wall_style(scene)
    if style is None:
        return None
    W, H = scene.w, scene.h

    def _c(x, y):
        if scene.wrap_x:
            x %= W
        if scene.wrap_y:
            y %= H
        if 0 <= x < W and 0 <= y < H:
            return scene.objects[y][x]
        return None                        # off-map (the void beyond the map)

    if _c(tx, ty) not in _WALL_CHARS:
        return None
    cN, cS = _c(tx, ty - 1), _c(tx, ty + 1)
    cE, cW = _c(tx + 1, ty), _c(tx - 1, ty)
    wN, wS = cN in _WALL_CHARS, cS in _WALL_CHARS      # a wall run continues
    wE, wW = cE in _WALL_CHARS, cW in _WALL_CHARS
    oN, oS = cN is not None, cS is not None            # "open" = not off-map
    oE, oW = cE is not None, cW is not None
    v_present = wN or wS                                # part of a vertical run
    h_present = wE or wW                                # part of a horizontal run
    if not (v_present or h_present):
        return None                        # lone pillar / free nub: keep full
    T = TILE
    th = T * style["thick"]                 # band thickness from the material
    p = T - th

    def cross(open_neg, open_pos):
        """Thin cross-extent (lo, hi) of a band from its two flanks' openness
        ('open' = the flank is on-map, i.e. interior). Both open (a partition
        between two rooms) -> CENTRE. One flank off-map (the building SHELL) ->
        hug the OFF-MAP edge: the outer face stays on the building silhouette
        (no floor lip past the wall) and the wall thins INward, growing the
        room a little. Both off-map (a rare spike) -> centre."""
        if open_neg and open_pos:
            return p / 2.0, T - p / 2.0
        if not open_neg:
            return 0.0, th                 # exterior on the neg side: hug it
        if not open_pos:
            return p, T                    # exterior on the pos side: hug it
        return p / 2.0, T - p / 2.0

    vx0, vx1 = cross(oW, oE) if v_present else (0.0, T)     # V band X thinness
    hy0, hy1 = cross(oN, oS) if h_present else (0.0, T)     # H band Y thinness
    rects = []
    if v_present:
        # reach the N/S edge where the run continues (a wall), else stop at the
        # crossbar (the H band) so a corner/end never overshoots into a room.
        vy0 = 0.0 if wN else (hy0 if h_present else 0.0)
        vy1 = T if wS else (hy1 if h_present else T)
        rects.append((vx0, vy0, vx1, vy1))
    if h_present:
        hx0 = 0.0 if wW else (vx0 if v_present else 0.0)
        hx1 = T if wE else (vx1 if v_present else T)
        rects.append((hx0, hy0, hx1, hy1))
    return rects


def _gap_slab(scene, tx, ty):
    """The thin-slab footprint THROUGH a non-wall gap tile (a doorway or a
    window) sitting in a wall run -- a list of tile-local rects like
    _wall_slab's, or None (non-slab scene, or no wall neighbour carries a
    band through this tile). Without this, a door/window tile in a thin-slab
    wall extruded as a FULL-tile box and jutted from the wall line as a dark
    monolith (the 2026-07 quality sprint's "glitched door" / "wrong windows"
    playtest finds). Same cross() rules as _wall_slab, so the gap band meets
    its flanking wall bands flush."""
    style = _wall_style(scene)
    if style is None:
        return None
    W, H = scene.w, scene.h

    def _c(x, y):
        if scene.wrap_x:
            x %= W
        if scene.wrap_y:
            y %= H
        if 0 <= x < W and 0 <= y < H:
            return scene.objects[y][x]
        return None

    cN, cS = _c(tx, ty - 1), _c(tx, ty + 1)
    cE, cW = _c(tx + 1, ty), _c(tx - 1, ty)
    wN, wS = cN in _WALL_CHARS, cS in _WALL_CHARS
    wE, wW = cE in _WALL_CHARS, cW in _WALL_CHARS
    oN, oS = cN is not None, cS is not None
    oE, oW = cE is not None, cW is not None
    T = TILE
    th = T * style["thick"]
    p = T - th

    def cross(open_neg, open_pos):
        if open_neg and open_pos:
            return p / 2.0, T - p / 2.0
        if not open_neg:
            return 0.0, th
        if not open_pos:
            return p, T
        return p / 2.0, T - p / 2.0

    # The band runs ALONG the wall it gaps: E/W wall neighbours carry a
    # horizontal band through the tile, N/S a vertical one. A straight run
    # (both flanking walls present) wins over a corner-adjacent single.
    if (wE and wW) or ((wE or wW) and not (wN or wS)):
        y0, y1 = cross(oN, oS)
        return [(0.0, y0, T, y1)]
    if wN or wS:
        x0, x1 = cross(oW, oE)
        return [(x0, 0.0, x1, T)]
    return None


# --- Rounded wall outline (2026-07, maintainer "rounded corners where the walls
# connect") ------------------------------------------------------------------
# The thin bands (_wall_slab) still meet at square 90deg corners. Round the FREE
# corners (the ones facing open floor) into arcs so the walls flow into each
# other; the corners that sit on a wall-neighbour SEAM stay sharp so the tile
# still connects flush to its neighbour. The rounded outline drives BOTH draw
# layers (the flat mass fill + the 3D prism extrude); collision/sight/nav keep
# the square bands (the few-px rounding sits INSIDE the drawn face, so collision
# is a hair proud -- the safe direction). Pure function of the footprint +
# neighbour seams, cached.
_ROUND_POLY_CACHE = {}                  # fillet radius is per-material now (style)


def _round_seams(scene, tx, ty):
    W, H = scene.w, scene.h

    def _c(x, y):
        if scene.wrap_x:
            x %= W
        if scene.wrap_y:
            y %= H
        return scene.objects[y][x] if 0 <= x < W and 0 <= y < H else None
    return (_c(tx, ty - 1) in _WALL_CHARS, _c(tx, ty + 1) in _WALL_CHARS,
            _c(tx + 1, ty) in _WALL_CHARS, _c(tx - 1, ty) in _WALL_CHARS)


def _rounded_wall_poly(scene, tx, ty):
    """(pts, draw) for the wall tile's THIN footprint with free corners rounded,
    or None for a full/absent slab. pts = local-px outline (CW); draw[i] flags
    whether edge pts[i]->pts[i+1] is EXPOSED (drawn) vs a merged neighbour seam
    (skipped). Cached per (footprint, seams)."""
    bands = _wall_slab(scene, tx, ty)
    if bands is None:
        return None
    style = _wall_style(scene)
    radius = TILE * style["thick"] * style["round"]     # fillet radius (px)
    rough = style["rough"]
    sN, sS, sE, sW = _round_seams(scene, tx, ty)
    # A rough wall jitters PER TILE so masonry doesn't tile; a smooth wall
    # (rough 0) keeps seed 0 so all like-shaped tiles share one cached outline.
    seed = (((tx * 73856093) ^ (ty * 19349663)) & 0xffff) if rough > 0 else 0
    key = (tuple(bands), sN, sS, sE, sW, round(radius, 2), round(rough, 2), seed)
    hit = _ROUND_POLY_CACHE.get(key)
    if hit is None:
        hit = _build_rounded_poly(bands, sN, sS, sE, sW, radius, rough, seed)
        _ROUND_POLY_CACHE[key] = hit
    return hit


def _build_rounded_poly(bands, sN, sS, sE, sW, radius, rough=0.0, seed=0):
    T = TILE
    SUP = 4                             # upsample for a clean mask outline
    surf = pygame.Surface((T * SUP, T * SUP), pygame.SRCALPHA)
    for (x0, y0, x1, y1) in bands:
        pygame.draw.rect(surf, (255, 255, 255, 255),
                         (round(x0 * SUP), round(y0 * SUP),
                          round((x1 - x0) * SUP), round((y1 - y0) * SUP)))
    mask = pygame.mask.from_surface(surf)
    comps = mask.connected_components()
    raw = (comps[0] if comps else mask).outline(2)
    if len(raw) < 4:
        return None
    loop = [(px / SUP, py / SUP) for px, py in raw]
    if loop[0] == loop[-1]:
        loop.pop()
    corners = _poly_corners(loop)         # rectilinear vertices only
    if len(corners) < 4:
        return None

    def on_seam(pt):
        x, y = pt
        eps = 0.5
        return ((y <= eps and sN) or (y >= T - eps and sS)
                or (x >= T - eps and sE) or (x <= eps and sW))

    out = []
    n = len(corners)
    for i in range(n):
        A = corners[(i - 1) % n]
        C = corners[i]
        B = corners[(i + 1) % n]
        if on_seam(C):
            out.append(C)                 # a connection corner: keep it sharp
        else:
            out.extend(_fillet(A, C, B, radius))
    # edge draw flags: an edge on a shared seam side is merged (not drawn)
    draw = []
    m = len(out)
    for i in range(m):
        p, q = out[i], out[(i + 1) % m]
        seam = ((p[1] <= 0.5 and q[1] <= 0.5 and sN)
                or (p[1] >= T - 0.5 and q[1] >= T - 0.5 and sS)
                or (p[0] >= T - 0.5 and q[0] >= T - 0.5 and sE)
                or (p[0] <= 0.5 and q[0] <= 0.5 and sW))
        draw.append(not seam)
    if rough > 0.0:
        out, draw = _roughen(out, draw, rough, seed)
    return (out, draw)


def _roughen(pts, draw, rough, seed):
    """Hew the FREE (drawn) outline edges: subdivide each long exposed edge and
    kick its interior points along the edge normal by a seeded amount, so a
    timber/stone wall reads rough-hewn, not machined. SEAM edges and the shared
    corner points stay put (tiles still connect flush, corners stay rounded);
    draw-only, so collision/sight/nav are untouched (they read the square
    bands). Amplitude is small (a few px), well inside the collision band."""
    def rnd(k):                            # deterministic (-1, 1) from seed + k
        v = (seed * 2654435761 + k * 40503 + 0x9e37) & 0xffffffff
        v ^= v >> 13
        v = (v * 2246822519) & 0xffffffff
        v ^= v >> 16
        return (v / 0xffffffff) * 2.0 - 1.0
    out, od, k = [], [], 0
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        out.append(a)
        od.append(draw[i])
        if not draw[i]:
            continue                       # seam edge: leave dead straight
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 6.0:                        # short edge / arc segment: leave it
            continue
        nx, ny = -dy / L, dx / L           # unit edge normal
        segs = int(L // 5) + 1             # a kink roughly every 5 px
        for s in range(1, segs):
            f = s / segs
            amp = rnd(k) * rough
            k += 1
            out.append((a[0] + dx * f + nx * amp, a[1] + dy * f + ny * amp))
            od.append(True)
    return out, od


def _poly_corners(loop):
    """Reduce a dense rectilinear outline to its corner vertices (drop points
    that continue straight)."""
    n = len(loop)
    out = []
    for i in range(n):
        ax, ay = loop[(i - 1) % n]
        bx, by = loop[i]
        cx, cy = loop[(i + 1) % n]
        # cross product of the two edges; ~0 -> collinear, drop it
        if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 0.01:
            out.append(loop[i])
    return out


def _fillet(A, C, B, r):
    """Quarter-arc points replacing corner C (between edges A->C and C->B),
    radius r clamped to half of each edge. Convex or concave (short arc either
    way). Returns >=2 points from the incoming edge, around, to the outgoing."""
    import math as _m
    ax, ay = A
    cx, cy = C
    bx, by = B
    din = (cx - ax, cy - ay)
    dou = (bx - cx, by - cy)
    lin = _m.hypot(*din) or 1.0
    lou = _m.hypot(*dou) or 1.0
    r = min(r, lin / 2.0, lou / 2.0)
    if r < 0.6:
        return [C]
    uin = (din[0] / lin, din[1] / lin)
    uou = (dou[0] / lou, dou[1] / lou)
    p1 = (cx - uin[0] * r, cy - uin[1] * r)       # back up the incoming edge
    p2 = (cx + uou[0] * r, cy + uou[1] * r)       # forward the outgoing edge
    o = (p1[0] + p2[0] - cx, p1[1] + p2[1] - cy)  # arc centre (90deg corner)
    a1 = _m.atan2(p1[1] - o[1], p1[0] - o[0])
    a2 = _m.atan2(p2[1] - o[1], p2[0] - o[0])
    while a2 - a1 > _m.pi:
        a2 -= 2 * _m.pi
    while a2 - a1 < -_m.pi:
        a2 += 2 * _m.pi
    seg = 4
    return [(o[0] + r * _m.cos(a1 + (a2 - a1) * k / seg),
             o[1] + r * _m.sin(a1 + (a2 - a1) * k / seg)) for k in range(seg + 1)]


def diagonal_wall_joins(scene):
    """List of ((x,y),(nx,ny)) DIAGONAL-ONLY wall joins: two diagonally adjacent
    wall tiles whose BOTH orthogonal bridge tiles are open (floor/door), so the
    walls connect only at a point. Under a full-tile render the fat blocks kiss
    and it reads fine, but under the THIN-SLAB render the two thin walls end in
    disconnected stubs (the maintainer's "walls like that"). The rule for a
    _SLAB_SCENES scene: there must be NONE -- close the corner (make a bridge
    tile a wall) so the walls connect orthogonally into a clean rounded L.
    Guarded by tests/smoke.py."""
    objs, W, H = scene.objects, scene.w, scene.h

    def wall(x, y):
        return 0 <= x < W and 0 <= y < H and objs[y][x] in _WALL_CHARS

    def opn(x, y):
        return 0 <= x < W and 0 <= y < H and objs[y][x] not in _WALL_CHARS
    out, seen = [], set()
    for y in range(H):
        for x in range(W):
            if not wall(x, y):
                continue
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                if wall(x + dx, y + dy) and opn(x + dx, y) and opn(x, y + dy):
                    k = tuple(sorted(((x, y), (x + dx, y + dy))))
                    if k not in seen:
                        seen.add(k)
                        out.append(k)
    return out


def _draw_wall_mass(surf, scene, cam_x, cam_y, x0, y0, x1, y1):
    W, H = scene.w, scene.h
    wx, wy = scene.wrap_x, scene.wrap_y
    for ty in range(y0, y1):
        wty = ty % H if wy else ty
        if not (0 <= wty < H):
            continue
        for tx in range(x0, x1):
            wtx = tx % W if wx else tx
            if not (0 <= wtx < W):
                continue
            obj = scene.objects[wty][wtx]
            if obj not in _WALL_CHARS:
                continue
            rx = tx * TILE - cam_x
            ry = ty * TILE - cam_y
            poly = _rounded_wall_poly(scene, tx, ty)
            bv = _bevel_corners(scene, tx, ty)
            if poly is not None:
                # Thin slab: render the tile's flat content into a scratch and
                # clip it to the SAME rounded outline the 3D prism uses, so the
                # near-black mass under the wall matches the thinned, rounded box
                # and the room floor shows through where the wall was thinned.
                scratch = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                _wall_tile_flat(scratch, scene, tx, ty, 0, 0)
                mask = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                pygame.draw.polygon(mask, (255, 255, 255, 255), poly[0])
                scratch.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(scratch, (rx, ry))
            elif bv:
                # Beveled tile: render the tile's flat content into a scratch,
                # then clip it to the same beveled footprint the 3D box uses so
                # no near-black corner triangle sits on the room floor beyond
                # the box base. Flat inset is 1px MORE than the box so any
                # yaw-bucket divergence in motion falls as a hair of floor, not
                # a dark nub on the lit floor.
                scratch = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                _wall_tile_flat(scratch, scene, tx, ty, 0, 0)
                mask = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                pygame.draw.polygon(
                    mask, (255, 255, 255, 255),
                    _bevel_poly_local(bv, TILE, _BEVEL_INSET + 1.0))
                scratch.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(scratch, (rx, ry))
            else:
                _wall_tile_flat(surf, scene, tx, ty, rx, ry)


def _wall_tile_flat(surf, scene, tx, ty, rx, ry):
    """One wall tile's flat near-black mass footprint + battered accents, drawn
    at (rx, ry). Extracted from _draw_wall_mass so the bevel path can render it
    into a scratch and clip it; the non-beveled call is byte-identical. The four
    palette colours carry the material tint (a slab scene's `_WALL_STYLES`
    colour); a non-slab scene's tint is (0,0,0) -> byte-identical."""
    tint = _wall_tint_for(scene)
    base = _tint_col(_WALL_BASE, tint)
    face = _tint_col(_WALL_FACE, tint)
    top = _tint_col(_WALL_TOP, _wall_top_tint_for(scene))    # grass over stone for turf
    foot = _tint_col(_WALL_FOOT, tint)
    pygame.draw.rect(surf, base, (rx, ry, TILE, TILE))
    hsh = (tx * 73856093) ^ (ty * 19349663)
    if hsh % 5 == 0:                       # pitting / grime
        pygame.draw.rect(surf, (11, 10, 14),
                         (rx + (hsh % (TILE - 6)) + 3,
                          ry + ((hsh // 7) % (TILE - 6)) + 3, 3, 2))
    elif hsh % 9 == 0:                      # hairline crack
        cx = rx + (hsh % (TILE - 4)) + 2
        cy = ry + ((hsh // 5) % (TILE - 8)) + 2
        pygame.draw.line(surf, (30, 28, 35), (cx, cy), (cx, cy + 5), 1)
    if hsh % 7 == 0:                        # water-stain dribble
        sx = rx + (hsh % (TILE - 6)) + 3
        pygame.draw.line(surf, (12, 11, 15), (sx, ry + 2),
                         (sx + ((hsh >> 5) & 1), ry + TILE - 3), 2)
    elif hsh % 8 == 0:                      # exposed boards where it's rotted through
        bx = rx + (hsh % (TILE - 8)) + 3
        for k in range(3):
            pygame.draw.line(surf, (46, 37, 30),
                             (bx + k * 3, ry + 4), (bx + k * 3, ry + TILE - 4), 1)
    j = (hsh >> 3) & 1     # 1px edge jitter -> hand-drawn wobble
    if not _is_wall(scene, tx, ty - 1):     # room above: lit cap
        pygame.draw.rect(surf, top, (rx, ry, TILE, 2))
        pygame.draw.line(surf, face, (rx, ry + 2 + j),
                         (rx + TILE, ry + 2 + j), 1)
    if not _is_wall(scene, tx, ty + 1):     # room below: foot shadow
        # Damp band wicking up from the ground + a little moss,
        # only where the wall actually meets open floor.
        pygame.draw.rect(surf, (12, 11, 15), (rx, ry + TILE - 8, TILE, 5))
        if hsh % 3 == 0:
            mx = rx + (hsh % (TILE - 6)) + 2
            pygame.draw.circle(surf, (44, 56, 40), (mx, ry + TILE - 3), 2)
        pygame.draw.rect(surf, foot, (rx, ry + TILE - 2, TILE, 2))
        pygame.draw.line(surf, face, (rx, ry + TILE - 3 - j),
                         (rx + TILE, ry + TILE - 3 - j), 1)
        if hsh % 4 == 0:    # rubble/grime spilling onto the floor,
            bx = rx + (hsh % 18) + 4   # crossing the tile boundary so
            pygame.draw.rect(surf, (27, 25, 29),  # the room edge isn't
                             (bx, ry + TILE, 7, 3))     # a clean line
            pygame.draw.rect(surf, (15, 14, 18), (bx + 2, ry + TILE + 1, 3, 2))
    if not _is_wall(scene, tx - 1, ty):
        pygame.draw.line(surf, face, (rx + j, ry),
                         (rx + j, ry + TILE), 1)
    if not _is_wall(scene, tx + 1, ty):
        pygame.draw.line(surf, face, (rx + TILE - 1 - j, ry),
                         (rx + TILE - 1 - j, ry + TILE), 1)


def _build_roof_regions(scene):
    """Flood-fill the roof ('r') tiles into one region per building and
    cache each region's tile bounding box on the scene. Also builds a
    `wall_to_region` map so each wall tile knows which building it belongs
    to (used to give per-building wall colour under tilt). Roof layout is
    static after build, so this runs once."""
    regions = getattr(scene, "_roof_regions", None)
    if regions is not None:
        return regions
    objs, h, w = scene.objects, scene.h, scene.w
    seen = [[False] * w for _ in range(h)]
    regions = []
    wall_map = {}
    for ty in range(h):
        for tx in range(w):
            if objs[ty][tx] != "r" or seen[ty][tx]:
                continue
            stack = [(tx, ty)]
            seen[ty][tx] = True
            minx = maxx = tx
            miny = maxy = ty
            cells = [(tx, ty)]
            while stack:
                cx, cy = stack.pop()
                minx = min(minx, cx); maxx = max(maxx, cx)
                miny = min(miny, cy); maxy = max(maxy, cy)
                for ax, ay in ((cx + 1, cy), (cx - 1, cy),
                               (cx, cy + 1), (cx, cy - 1)):
                    if (0 <= ax < w and 0 <= ay < h
                            and not seen[ay][ax] and objs[ay][ax] == "r"):
                        seen[ay][ax] = True
                        stack.append((ax, ay))
                        cells.append((ax, ay))
            region = (minx, miny, maxx, maxy)
            regions.append(region)
            # Walk each roof tile's 4 neighbours; if neighbour is a wall (or
            # a door or a window: they're embedded IN the wall), tag it as
            # belonging to this region. A wall on the seam between two
            # buildings would be claimed by whichever region we hit first
            # (no shared walls in this game's town layouts).
            for (cx, cy) in cells:
                for ax, ay in ((cx + 1, cy), (cx - 1, cy),
                               (cx, cy + 1), (cx, cy - 1)):
                    if not (0 <= ax < w and 0 <= ay < h):
                        continue
                    ch = objs[ay][ax]
                    if (ch in _WALL_CHARS or ch in _DOOR_CHARS
                            or ch in _WINDOW_CHARS) and (ax, ay) not in wall_map:
                        wall_map[(ax, ay)] = region
    scene._roof_regions = regions
    scene._wall_region_map = wall_map
    return regions


def wall_region_for(scene, tx, ty):
    """Which building (roof region) this wall/door/window tile belongs to,
    or None for free-standing walls (a fence, a depths corridor)."""
    if getattr(scene, "_wall_region_map", None) is None:
        _build_roof_regions(scene)
    return scene._wall_region_map.get((tx, ty))


def _draw_gable_roof(surf, region, cam_x, cam_y):
    """One overhanging gabled roof over a building footprint: rounded
    corners, two pitched slopes split at a sagging ridge, deep eaves on
    the back + sides (it spills past the walls, so the silhouette is the
    roof, not the tile rectangle), shingle courses, blown-out holes to
    the joists, moss, and a crooked chimney. The FRONT (south) edge
    stops at the top of the south wall so the door stays visible under
    the eave."""
    minx, miny, maxx, maxy = region
    rng = random.Random((minx * 73856093) ^ (maxy * 19349663))
    E = 9                                            # eave overhang
    L = int((minx - 1) * TILE - cam_x - E)
    R = int((maxx + 2) * TILE - cam_x + E)
    T = int((miny - 1) * TILE - cam_y - E)
    # Stop the front (south) edge of the roof at the TOP of the
    # south-wall row, plus 8 px for a shallow eave lip. Previously
    # Bf extended a full row past maxy, which buried the door tile
    # under the eave and made doors invisible on most buildings.
    Bf = int(maxy * TILE - cam_y + 8)
    Wd, Hd = R - L, Bf - T
    if Wd < 8 or Hd < 8:
        return
    # Ground drop-shadow so the roof has height + overhangs onto the yard.
    sh = pygame.Surface((Wd + 16, Hd + 18), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 96), (8, 14, Wd, Hd), border_radius=11)
    surf.blit(sh, (L - 8, T - 7))
    mat = rng.randint(0, 2)                          # roof material varies per building
    if mat == 1:                                     # rusted corrugated tin
        base, lit, dark = (66, 68, 70), (96, 98, 100), (48, 50, 53)
        c_lit, c_dark, ridge_c, vertical = (118, 64, 36), (40, 42, 45), (40, 42, 44), True
    elif mat == 2:                                   # tar-paper
        base, lit, dark = (46, 44, 48), (62, 60, 65), (32, 30, 34)
        c_lit, c_dark, ridge_c, vertical = (54, 52, 57), (24, 22, 26), (20, 18, 22), False
    else:                                            # weathered cedar shingle
        base, lit, dark = (92, 60, 42), (124, 86, 58), (74, 48, 33)
        c_lit, c_dark, ridge_c, vertical = (104, 72, 48), (60, 39, 27), (44, 28, 19), False
    pygame.draw.rect(surf, base, (L, T, Wd, Hd), border_radius=10)
    ridge_y = T + int(Hd * 0.42)
    pygame.draw.rect(surf, lit, (L + 2, T + 2, Wd - 4, ridge_y - T - 2),
                     border_top_left_radius=9, border_top_right_radius=9)
    pygame.draw.rect(surf, dark, (L + 2, ridge_y, Wd - 4, Bf - ridge_y - 2),
                     border_bottom_left_radius=9, border_bottom_right_radius=9)
    if vertical:                                     # tin: vertical corrugation ribs
        for xx in range(L + 6, R - 5, 5):
            pygame.draw.line(surf, c_lit if (xx // 5) % 3 == 0 else c_dark,
                             (xx, T + 3), (xx, Bf - 4), 1)
    else:                                            # shingle / tar: horizontal courses
        for yy in range(T + 5, ridge_y - 1, 5):
            pygame.draw.line(surf, c_lit, (L + 5, yy), (R - 5, yy), 1)
        for yy in range(ridge_y + 4, Bf - 3, 5):
            pygame.draw.line(surf, c_dark, (L + 5, yy), (R - 5, yy), 1)
    sag = max(2, Wd // 22)                            # ridge beam, sagging in the middle
    mid_x = (L + R) // 2
    pygame.draw.lines(surf, ridge_c, False,
                      [(L + 4, ridge_y), (mid_x, ridge_y + sag), (R - 4, ridge_y)], 2)
    if Wd > 40 and Hd > 36 and rng.random() < 0.4:   # a caved-in section -> the rafters
        hx = L + rng.randint(Wd // 4, max(Wd // 4 + 1, 3 * Wd // 4))
        hy = T + rng.randint(Hd // 4, max(Hd // 4 + 1, Hd // 2))
        hw, hh = rng.randint(10, 18), rng.randint(8, 13)
        pygame.draw.ellipse(surf, (19, 16, 15), (hx, hy, hw, hh))
        for jx in range(hx + 2, hx + hw - 1, 4):
            pygame.draw.line(surf, (40, 32, 26), (jx, hy + 1), (jx, hy + hh - 1), 1)
    for _ in range(max(1, (Wd * Hd) // 1700)):       # blown-out patches
        hx = L + rng.randint(5, max(6, Wd - 9))
        hy = T + rng.randint(5, max(6, Hd - 8))
        pygame.draw.rect(surf, (26, 21, 18), (hx, hy, rng.randint(4, 7), 4))
    if mat != 1:                                     # moss (not on tin)
        for _ in range(max(1, (Wd * Hd) // 2000)):
            mx = L + rng.randint(4, max(5, Wd - 6))
            my = T + rng.randint(4, max(5, Hd - 6))
            pygame.draw.circle(surf, (56, 70, 46), (mx, my), 2)
    else:                                            # rust streaks (tin)
        for _ in range(max(1, (Wd * Hd) // 1500)):
            rx2 = L + rng.randint(6, max(7, Wd - 8))
            ry2 = T + rng.randint(4, max(5, Hd // 2))
            pygame.draw.line(surf, (96, 52, 30), (rx2, ry2),
                             (rx2, ry2 + rng.randint(5, 12)), 1)
    chx, chy = R - 18, T + 6                          # crooked chimney
    pygame.draw.rect(surf, (58, 40, 36), (chx, chy, 10, 13))
    pygame.draw.rect(surf, (30, 22, 20), (chx, chy, 10, 13), 1)
    pygame.draw.rect(surf, (40, 30, 28), (chx + 1, chy - 2, 8, 2))


def _draw_scene_roofs(surf, scene, cam_x, cam_y, x0, y0, x1, y1):
    for region in _build_roof_regions(scene):
        minx, miny, maxx, maxy = region
        if maxx + 2 < x0 or minx - 2 > x1 or maxy + 2 < y0 or miny - 2 > y1:
            continue
        _draw_gable_roof(surf, region, cam_x, cam_y)


# -- 3D gabled roofs for the tilt path --------------------------------------
# The flat-pitch `_draw_gable_roof` above paints the roof art into the top-
# down floor surface, which under tilt warps onto the GROUND as a flat plate
# (skipped from the tilt floor pass via `skip_roofs=True`). The tilt path
# instead emits one of these volumetric roofs per building region into the
# depth-sorted draw queue, so each building is a real prism rising above the
# walls + a ridge beam + a chimney. Material + tint are seeded per region so
# the houses read as distinct without losing town cohesion.

# Eave overhang in world px, shared by the roof prism geometry and its
# depth key (emit_tilt_roofs) so the two can never drift apart.
_ROOF_EAVE = 9


def _building_palette(seed_a, seed_b):
    """Per-region (wall tint, trim accent, roof palette). Stable from the
    region's geometry seed so a given building keeps its look across reloads.
    `roof["mat"]` names the material so the slope texture pass can draw
    courses (shingle), down-slope ribs (tin), or lap seams (tar-paper).
    """
    rng = random.Random((seed_a * 73856093) ^ (seed_b * 19349663))
    mat = rng.randint(0, 2)
    if mat == 1:                                # rusted corrugated tin
        roof = {"col": (94, 96, 100), "lit": (132, 134, 138),
                "dark": (52, 54, 58), "ridge": (40, 42, 44),
                "chimney": (60, 42, 36)}
    elif mat == 2:                              # tar-paper (lifted 2026-07:
        # the old (54,50,56) went to black under the outdoor haze grade --
        # a barn-sized void. Still tar-dark, but it keeps its form.)
        roof = {"col": (76, 70, 78), "lit": (106, 100, 108),
                "dark": (48, 44, 52), "ridge": (34, 32, 38),
                "chimney": (44, 36, 36)}
    else:                                       # weathered cedar shingle
        roof = {"col": (118, 80, 56), "lit": (158, 110, 76),
                "dark": (74, 50, 34), "ridge": (44, 28, 19),
                "chimney": (58, 40, 36)}
    roof["mat"] = mat
    # Per-building wall warmth: each house gets its own RGB offset so the
    # weathered wood reads cooler/warmer house to house. Wider than purely
    # subtle so adjacent buildings are unambiguously distinct but the
    # palette stays in town-cohesion range (no pinks/greens).
    wall_dr = rng.randint(-22, 28)
    wall_dg = rng.randint(-18, 22)
    wall_db = rng.randint(-20, 20)
    trim_choices = [(120, 64, 52), (90, 70, 40), (60, 80, 70),
                    (110, 100, 80), (80, 60, 50)]
    trim = trim_choices[rng.randint(0, len(trim_choices) - 1)]
    return roof, (wall_dr, wall_dg, wall_db), trim


_BUILDING_PALETTE_CACHE = {}


def _get_building_palette(region):
    minx, miny, maxx, maxy = region
    key = (minx, miny, maxx, maxy)
    pal = _BUILDING_PALETTE_CACHE.get(key)
    if pal is None:
        pal = _building_palette(minx, maxy)
        _BUILDING_PALETTE_CACHE[key] = pal
    return pal


def _roof_slope_texture(surf, camera, rng, roof, e0, e1, r0, r1,
                        base=None, sparse=False):
    """Material texture over ONE roof slope, the quad between its EAVE
    edge (e0->e1) and RIDGE edge (r0->r1), all world (x, y, z) triples
    with e0 below r0. The flat-pitch roof draws shingle courses and
    wear; without this the tilt prisms read as blank CAD. Shingle (mat
    0) lays courses parallel to the ridge, corrugated tin (mat 1) runs
    ribs DOWN the slope, tar-paper (mat 2) lays lap seams + patch
    blotches. `base` overrides the slope colour (the shadow slope gets a
    fainter pass); `sparse` halves the detail there. Seeded per region,
    so no per-frame flicker."""
    col = base if base is not None else roof["col"]
    dk = _shade_col(col, 0.8)
    lt = _shade_col(col, 1.18)
    mat = roof.get("mat", 0)

    def lerp(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                a[2] + (b[2] - a[2]) * t)

    def pj(p):
        x, y = camera.project(p[0], p[1], p[2])
        return (int(x), int(y))

    def at(t, u):                     # bilinear point on the slope
        return lerp(lerp(e0, e1, u), lerp(r0, r1, u), t)
    run = math.dist(e0, r0)
    width = math.dist(e0, e1)
    if mat == 1:
        # corrugation ribs run eave -> ridge
        n = max(3, int(width // (16 if sparse else 8)))
        for k in range(1, n):
            u = k / n
            pygame.draw.line(surf, dk if k % 2 else lt,
                             pj(lerp(e0, e1, u)), pj(lerp(r0, r1, u)), 1)
        if not sparse:
            for _ in range(max(2, int(width // 26))):   # rust at the eave
                p = pj(at(rng.uniform(0.04, 0.3), rng.uniform(0.05, 0.95)))
                pygame.draw.circle(surf, (104, 58, 34), p, rng.randint(1, 2))
    elif mat == 2:
        # tar-paper lap seams + darker patches
        n = max(2, int(run // (22 if sparse else 12)))
        for k in range(1, n + 1):
            t = k / (n + 1)
            pygame.draw.line(surf, dk, pj(lerp(e0, r0, t)),
                             pj(lerp(e1, r1, t)), 1)
        if not sparse:
            for _ in range(rng.randint(2, 4)):
                t = rng.uniform(0.1, 0.8)
                u = rng.uniform(0.08, 0.8)
                dt, du = rng.uniform(0.08, 0.16), rng.uniform(0.04, 0.1)
                pygame.draw.polygon(surf, _shade_col(col, 0.68), [
                    pj(at(t, u)), pj(at(t, u + du)),
                    pj(at(t + dt, u + du)), pj(at(t + dt, u))])
    else:
        # shingle courses parallel to the ridge, plus moss/wear specks
        n = max(3, int(run // (14 if sparse else 7)))
        for k in range(1, n):
            t = k / n
            pygame.draw.line(surf, dk, pj(lerp(e0, r0, t)),
                             pj(lerp(e1, r1, t)), 1)
        if not sparse:
            for _ in range(max(3, int(width * run // 3200))):
                p = pj(at(rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95)))
                pygame.draw.circle(
                    surf, (58, 66, 48) if rng.random() < 0.5 else lt,
                    p, 1)


def _draw_building_3d(surf, camera, region, scene):
    """A real volumetric gabled roof over the building's footprint plus a
    ridge beam and a crooked chimney. All four slopes are drawn opaque so the
    roof fully encloses the interior under tilt (no peek-in). Per-region
    palette gives each building a subtle but recognisable look.

    Ridge runs along the building's LONGER axis (the door direction --
    typically the road-facing wall -- becomes the gable end). Aligned-with-
    the-road buildings get their gable end facing the street naturally."""
    minx, miny, maxx, maxy = region
    # outer footprint in world px (wall outer edges + eave overhang)
    xL = (minx - 1) * TILE - _ROOF_EAVE
    xR = (maxx + 2) * TILE + _ROOF_EAVE
    yT = (miny - 1) * TILE - _ROOF_EAVE
    yB = (maxy + 2) * TILE + _ROOF_EAVE
    rng = random.Random((minx * 73856093) ^ (maxy * 19349663) ^ 0x5EED)
    width = xR - xL
    depth = yB - yT
    z_wall = _TILT_WALL_RISE
    H = max(14, min(28, int(min(width, depth) * 0.32)))
    z_apex = z_wall + H
    roof, _wall_tint, trim = _get_building_palette(region)

    ridge_ew = width >= depth         # longer than deep -> ridge runs east-west
    # 4 base corners
    NW = camera.project(xL, yT, z_wall)
    NE = camera.project(xR, yT, z_wall)
    SW = camera.project(xL, yB, z_wall)
    SE = camera.project(xR, yB, z_wall)

    if ridge_ew:
        yMid = (yT + yB) / 2
        Rw = camera.project(xL, yMid, z_apex)
        Re = camera.project(xR, yMid, z_apex)
        # Camera under typical tilt looks DOWN+SOUTH, so:
        # - north slope is the FAR (back) face -- draw first
        # - south slope is the NEAR (front) face -- draw last so it covers
        # Gables on east + west, between the two slopes.
        pygame.draw.polygon(surf, roof["dark"], [NW, NE, Re, Rw])  # back slope
        pygame.draw.polygon(surf, roof["dark"], [NW, SW, Rw])      # west gable
        pygame.draw.polygon(surf, roof["dark"], [NE, SE, Re])      # east gable
        pygame.draw.polygon(surf, roof["col"], [SW, SE, Re, Rw])   # front slope
        # material texture: full detail on the lit slope, a sparse pass
        # on the shadow slope so it reads as the same surface in shade
        _roof_slope_texture(surf, camera, rng, roof,
                            (xL, yB, z_wall), (xR, yB, z_wall),
                            (xL, yMid, z_apex), (xR, yMid, z_apex))
        _roof_slope_texture(surf, camera, rng, roof,
                            (xL, yT, z_wall), (xR, yT, z_wall),
                            (xL, yMid, z_apex), (xR, yMid, z_apex),
                            base=_shade_col(roof["dark"], 1.12), sparse=True)
        # gable rim outlines so the form catches the light
        pygame.draw.line(surf, roof["lit"], NW, Rw, 1)
        pygame.draw.line(surf, roof["lit"], NE, Re, 1)
        pygame.draw.line(surf, roof["lit"], SW, Rw, 1)
        pygame.draw.line(surf, roof["lit"], SE, Re, 1)
        # ridge beam
        pygame.draw.line(surf, roof["ridge"], Rw, Re, 2)
        # chimney near the back-east corner of the ridge
        cx_w = xR - TILE * 0.6
        cy_w = yT + (yB - yT) * 0.35
        ch_base_z = z_wall + H * 0.25
        ch_top_z = z_apex + 4
        chx_w = TILE * 0.25
        chy_w = TILE * 0.25
    else:
        xMid = (xL + xR) / 2
        Rn = camera.project(xMid, yT, z_apex)
        Rs = camera.project(xMid, yB, z_apex)
        pygame.draw.polygon(surf, roof["dark"], [NW, SW, Rs, Rn])  # west slope
        pygame.draw.polygon(surf, roof["dark"], [NW, NE, Rn])      # north gable
        pygame.draw.polygon(surf, roof["dark"], [SW, SE, Rs])      # south gable
        pygame.draw.polygon(surf, roof["col"], [NE, SE, Rs, Rn])   # east slope
        _roof_slope_texture(surf, camera, rng, roof,
                            (xR, yT, z_wall), (xR, yB, z_wall),
                            (xMid, yT, z_apex), (xMid, yB, z_apex))
        _roof_slope_texture(surf, camera, rng, roof,
                            (xL, yT, z_wall), (xL, yB, z_wall),
                            (xMid, yT, z_apex), (xMid, yB, z_apex),
                            base=_shade_col(roof["dark"], 1.12), sparse=True)
        pygame.draw.line(surf, roof["lit"], NW, Rn, 1)
        pygame.draw.line(surf, roof["lit"], SW, Rs, 1)
        pygame.draw.line(surf, roof["lit"], NE, Rn, 1)
        pygame.draw.line(surf, roof["lit"], SE, Rs, 1)
        pygame.draw.line(surf, roof["ridge"], Rn, Rs, 2)
        cx_w = xL + (xR - xL) * 0.3
        cy_w = yT + TILE * 0.6
        ch_base_z = z_wall + H * 0.25
        ch_top_z = z_apex + 4
        chx_w = TILE * 0.25
        chy_w = TILE * 0.25

    # chimney: short box on top of the roof
    cb_NW = camera.project(cx_w - chx_w, cy_w - chy_w, ch_base_z)
    cb_NE = camera.project(cx_w + chx_w, cy_w - chy_w, ch_base_z)
    cb_SW = camera.project(cx_w - chx_w, cy_w + chy_w, ch_base_z)
    cb_SE = camera.project(cx_w + chx_w, cy_w + chy_w, ch_base_z)
    ct_NW = camera.project(cx_w - chx_w, cy_w - chy_w, ch_top_z)
    ct_NE = camera.project(cx_w + chx_w, cy_w - chy_w, ch_top_z)
    ct_SW = camera.project(cx_w - chx_w, cy_w + chy_w, ch_top_z)
    ct_SE = camera.project(cx_w + chx_w, cy_w + chy_w, ch_top_z)
    chim = roof["chimney"]
    pygame.draw.polygon(surf, chim, [cb_SW, cb_SE, ct_SE, ct_SW])   # front face
    pygame.draw.polygon(surf, _shade_col(chim, 0.72),
                        [cb_SW, cb_NW, ct_NW, ct_SW])               # left face
    pygame.draw.polygon(surf, _shade_col(chim, 0.72),
                        [cb_SE, cb_NE, ct_NE, ct_SE])               # right face
    pygame.draw.polygon(surf, _shade_col(chim, 1.18),
                        [ct_NW, ct_NE, ct_SE, ct_SW])               # cap top
    pygame.draw.polygon(surf, _shade_col(chim, 0.50),
                        [ct_NW, ct_NE, ct_SE, ct_SW], 1)            # cap rim
    # ground/midpoint for depth sort
    return ((xL + xR) / 2, (yT + yB) / 2, z_apex / 2)


def _shade_col(col, f):
    return (max(0, min(255, int(col[0] * f))),
            max(0, min(255, int(col[1] * f))),
            max(0, min(255, int(col[2] * f))))


_WATER_EDGE_CHUNK = 16          # tiles per spatial bucket -- matches the
                                # decoration chunk size so the marsh edges
                                # cull the same way the marsh trees do


def _build_water_bank_edges(scene):
    """Precompute every water-land boundary segment AND bucket them into a
    spatial chunk index. Each edge is (cx_world, cy_world, ndx, ndy, seed).
    The emit walker iterates only buckets the camera window overlaps, so a
    full-marsh scan (212 edges in brimley) drops to ~30 per frame."""
    edges = getattr(scene, "_water_bank_edges", None)
    if edges is not None:
        return edges
    if getattr(scene, "procedural", False):
        # An unbounded generator field can't be full-scanned for "~" tiles
        # (the lost-space pond hand-places its own bank reeds). Skip it.
        scene._water_bank_edges = []
        scene._water_bank_chunks = {}
        return scene._water_bank_edges
    floor, h, w = scene.floor, scene.h, scene.w
    edges = []
    chunks = {}
    for ty in range(h):
        for tx in range(w):
            if floor[ty][tx] != "~":
                continue
            for si, (ndx, ndy) in enumerate(((0, -1), (0, 1),
                                             (-1, 0), (1, 0))):
                nx, ny = tx + ndx, ty + ndy
                if not (0 <= nx < w and 0 <= ny < h):
                    continue
                if floor[ny][nx] not in _BANK_LAND:
                    continue
                # Boundary midpoint sits ON the water tile's land-facing edge
                cx_w = tx * TILE + TILE / 2 + ndx * (TILE / 2 - 1)
                cy_w = ty * TILE + TILE / 2 + ndy * (TILE / 2 - 1)
                seed = (tx * 73856093) ^ (ty * 19349663) ^ (si * 40503)
                rec = (cx_w, cy_w, ndx, ndy, seed)
                edges.append(rec)
                cx = tx // _WATER_EDGE_CHUNK
                cy = ty // _WATER_EDGE_CHUNK
                chunks.setdefault((cx, cy), []).append(rec)
    scene._water_bank_edges = edges
    scene._water_bank_chunks = chunks
    return edges


def _draw_reed_cluster(surf, camera, cx_w, cy_w, ndx, ndy, seed, wt):
    """3 upright reeds at a bank edge. Each is a thin near-vertical line
    projected through the camera so it stands at the right pitch; the tip
    sways with the marsh wind. Density throttled by the seed -- not every
    edge gets reeds, so the bank reads patchy + organic."""
    if (seed % 5) >= 3:                  # ~40% of edges actually get reeds
        return
    reed = (80, 88, 46)
    reed_dk = (50, 58, 30)
    # The boundary direction is perpendicular to (ndx, ndy) -- reeds spread
    # ALONG the boundary so they form a small line, not a single point.
    if ndx:
        ax, ay = 0, 1
    else:
        ax, ay = 1, 0
    n = 3
    for k in range(n):
        u = ((k - (n - 1) / 2.0) / float(n)) * TILE * 0.7
        jitter_x = ((seed >> (k * 3)) & 3) - 1
        jitter_y = ((seed >> (k * 3 + 4)) & 3) - 1
        bx = cx_w + ax * u + jitter_x * 0.5
        by = cy_w + ay * u + jitter_y * 0.5
        h_reed = 7 + ((seed >> (k * 2)) & 7)
        sway = math.sin(wt + seed * 0.013 + k * 0.7) * 1.7
        b = camera.project(bx, by, 0)
        t = camera.project(bx + sway, by, h_reed)
        if abs(t[0] - b[0]) + abs(t[1] - b[1]) < 200:    # cull off-screen
            pygame.draw.line(surf, reed_dk,
                             (int(b[0]), int(b[1])),
                             (int(t[0]), int(t[1])), 1)
            pygame.draw.line(surf, reed,
                             (int(b[0]) + 1, int(b[1])),
                             (int(t[0]) + 1, int(t[1])), 1)


def emit_tilt_water_reeds(emit_fn, scene, camera, surf, x0, y0, x1, y1):
    """Emit one depth-sorted reed cluster per visible water-bank edge so
    the marsh fringe stands UP under tilt instead of being painted flat
    onto the warped floor. Walks only the spatial chunks the camera window
    overlaps so a marsh row visits ~30 edges per frame, not all 212."""
    _build_water_bank_edges(scene)
    chunks = getattr(scene, "_water_bank_chunks", None)
    if not chunks:
        return
    wt = pygame.time.get_ticks() / 650.0
    cx0 = x0 // _WATER_EDGE_CHUNK - 1
    cy0 = y0 // _WATER_EDGE_CHUNK - 1
    cx1 = x1 // _WATER_EDGE_CHUNK + 1
    cy1 = y1 // _WATER_EDGE_CHUNK + 1
    for cy in range(cy0, cy1 + 1):
        for cx in range(cx0, cx1 + 1):
            bucket = chunks.get((cx, cy))
            if not bucket:
                continue
            for (cx_w, cy_w, ndx, ndy, seed) in bucket:
                tx, ty = int(cx_w // TILE), int(cy_w // TILE)
                if tx < x0 - 1 or tx > x1 + 1 or ty < y0 - 1 or ty > y1 + 1:
                    continue
                emit_fn(camera.depth(cx_w, cy_w, 4),
                        lambda cx_w=cx_w, cy_w=cy_w, ndx=ndx, ndy=ndy,
                        seed=seed, wt=wt, surf=surf:
                        _draw_reed_cluster(surf, camera, cx_w, cy_w,
                                           ndx, ndy, seed, wt))


def emit_tilt_roofs(emit_fn, scene, camera, surf, x0, y0, x1, y1):
    """Emit one depth-sorted draw closure per visible building region. The
    closure draws the volumetric roof + ridge + chimney for that region. The
    flat (pitch-0) gabled roof is unrelated and still drawn by Scene.draw.

    The roof keys at its NEAREST outer corner (max depth over the four
    eave corners), never the building centre: the roof physically
    overhangs every wall of its own footprint, so it must sort AFTER all
    of them at any camera yaw. A centre key let the near-side wall boxes
    paint their flat tops over the eave -- the crenellated 'teeth' rim on
    every big building."""
    for region in _build_roof_regions(scene):
        minx, miny, maxx, maxy = region
        if maxx + 2 < x0 or minx - 2 > x1 or maxy + 2 < y0 or miny - 2 > y1:
            continue
        xL = (minx - 1) * TILE - _ROOF_EAVE
        xR = (maxx + 2) * TILE + _ROOF_EAVE
        yT = (miny - 1) * TILE - _ROOF_EAVE
        yB = (maxy + 2) * TILE + _ROOF_EAVE
        near = max(camera.depth(xL, yT, 0), camera.depth(xR, yT, 0),
                   camera.depth(xL, yB, 0), camera.depth(xR, yB, 0))
        emit_fn(near,
                lambda region=region, scene=scene, camera=camera, surf=surf:
                _draw_building_3d(surf, camera, region, scene))


def _door_room_dir(scene, tx, ty):
    """Which way the door opens -- the floor (room) side its leaf swings
    into. Off-map edges don't count as wall, so a building's south-edge
    exit still opens toward its interior."""
    # A window ('i') is part of the wall LINE (structure), not a floor side:
    # counting it lets a door flanked by lit windows still resolve its wall
    # axis (else both perpendicular neighbours read as non-wall and the door
    # mis-detects). Only affects window-flanked doors; the rest are unchanged.
    struct = _WALL_CHARS | _WINDOW_CHARS
    def w(ax, ay):
        return (0 <= ay < scene.h and 0 <= ax < scene.w
                and scene.objects[ay][ax] in struct)
    def fl(ax, ay):
        return (0 <= ay < scene.h and 0 <= ax < scene.w
                and scene.objects[ay][ax] not in struct)
    def roof(ax, ay):
        # A building's INTERIOR is roof ('r'); the door opens the OTHER way,
        # toward the exterior/street. Both sides of a 1-thick wall read as
        # non-wall (roof interior + open exterior), so pick the exterior by
        # ruling out the roof side. Leaves S/E doors byte-identical (the roof
        # always sits on the interior side, which the old default already
        # skipped) and correctly resolves N/W doors the old code mis-called.
        return (0 <= ay < scene.h and 0 <= ax < scene.w
                and scene.objects[ay][ax] == "r")
    wl, wr, wu, wd = w(tx - 1, ty), w(tx + 1, ty), w(tx, ty - 1), w(tx, ty + 1)
    if (wu or wd) and not (wl or wr):           # vertical wall -> opens L/R
        if roof(tx + 1, ty) and not roof(tx - 1, ty):
            return "W"                          # interior east -> opens west
        if roof(tx - 1, ty) and not roof(tx + 1, ty):
            return "E"                          # interior west -> opens east
        return "E" if fl(tx + 1, ty) else "W"
    if (wl or wr) and not (wu or wd):           # horizontal wall -> opens up/down
        if roof(tx, ty + 1) and not roof(tx, ty - 1):
            return "N"                          # interior south -> opens north
        if roof(tx, ty - 1) and not roof(tx, ty + 1):
            return "S"                          # interior north -> opens south
        return "S" if fl(tx, ty + 1) else "N"
    if fl(tx, ty + 1):                          # corner / ambiguous
        return "S"
    if fl(tx + 1, ty):
        return "E"
    if fl(tx, ty - 1):
        return "N"
    return "W"


def _draw_door_opening(surf, rx, ry, room, tx, ty, style="wood"):
    """The doorway itself, drawn in-tile during the terrain pass: the
    wall fills through (continuous mass) with a dark opening punched in
    it + a lit face on the room side. The swung leaf is a separate,
    unconfined sprite drawn later (draw_scene_doors). style="cave" (the
    mine adit, 2026-07): the opening is a jagged rock mouth with two
    timber posts and no leaf."""
    pygame.draw.rect(surf, _WALL_BASE, (rx, ry, TILE, TILE))
    hsh = (tx * 73856093) ^ (ty * 19349663)
    if hsh % 4 == 0:
        pygame.draw.rect(surf, (11, 10, 14),
                         (rx + (hsh % 22) + 4, ry + ((hsh // 7) % 22) + 4, 3, 2))
    if room == "S":
        pygame.draw.rect(surf, _WALL_FACE, (rx, ry + TILE - 2, TILE, 2))
    elif room == "N":
        pygame.draw.rect(surf, _WALL_TOP, (rx, ry, TILE, 2))
    elif room == "E":
        pygame.draw.rect(surf, _WALL_FACE, (rx + TILE - 2, ry, 2, TILE))
    else:
        pygame.draw.rect(surf, _WALL_FACE, (rx, ry, 2, TILE))
    if style == "cave":
        # The adit mouth: an irregular dark blob (never a neat rect) with
        # a rock-crumb rim and two timber post ends at the room side.
        cx, cy = rx + 16, ry + 16
        pts = []
        for i in range(8):
            a = i * math.tau / 8
            rr = 8 + ((hsh >> (i * 3)) % 5)          # 8..12 px, per-tile jitter
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        pygame.draw.polygon(surf, (3, 2, 5), pts)
        for i in range(0, 8, 2):                     # rim crumbs
            px_, py_ = pts[i]
            pygame.draw.rect(surf, (52, 50, 56), (int(px_) - 1, int(py_) - 1, 2, 2))
        wood = (72, 54, 32)
        if room in ("S", "N"):
            py_ = ry + (TILE - 6 if room == "S" else 2)
            pygame.draw.rect(surf, wood, (rx + 5, py_, 3, 4))
            pygame.draw.rect(surf, wood, (rx + TILE - 8, py_, 3, 4))
        else:
            px_ = rx + (TILE - 6 if room == "E" else 2)
            pygame.draw.rect(surf, wood, (px_, ry + 5, 4, 3))
            pygame.draw.rect(surf, wood, (px_, ry + TILE - 8, 4, 3))
        return
    pygame.draw.rect(surf, (3, 2, 5), (rx + 9, ry + 9, 14, 14))      # the dark doorway


def _leaf_quad(hx, hy, ang, L, Wd):
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy, dx
    return [(hx, hy), (hx + px * Wd, hy + py * Wd),
            (hx + dx * L + px * Wd, hy + dy * L + py * Wd),
            (hx + dx * L, hy + dy * L)]


def _draw_door_leaf(surf, rx, ry, room, seed):
    """The door leaf as an UNCONFINED sprite -- hung on a hinge at one
    CORNER of the doorway and swung out into the room, the way a real
    door pivots. It spills past the tile (collision stays on the grid;
    the doorway tile is passable). Hinge corner, swing angle and length
    vary per door (deterministic) so no two hang alike."""
    skew = 0.22 + (seed % 50) / 100.0           # swing angle varies per door
    L = 26 + (seed // 7) % 5                      # door span -- a touch longer; spills past tile
    Wd = 5                                        # door thickness, seen top-down
    TL = (rx + 8, ry + 8); TR = (rx + 24, ry + 8)
    BL = (rx + 8, ry + 24); BR = (rx + 24, ry + 24)
    # Fixed hinge corner per wall (right-handed doors); the leaf swings
    # in toward the room. A north-wall door (room to the south) hinges
    # at the bottom-left corner of the cell.
    if room == "S":          # north wall -> swings down into the room below
        hx, hy, ang = BL[0], BL[1], math.pi / 2 - skew
    elif room == "N":        # south wall -> swings up
        hx, hy, ang = TR[0], TR[1], -math.pi / 2 - skew
    elif room == "E":        # west wall -> swings right
        hx, hy, ang = BR[0], BR[1], -skew
    else:                    # east wall -> swings left
        hx, hy, ang = TL[0], TL[1], math.pi - skew
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy, dx
    face = [(int(x), int(y)) for x, y in _leaf_quad(hx, hy, ang, L, Wd)]
    pygame.draw.polygon(surf, (58, 43, 27), face)
    pygame.draw.polygon(surf, (88, 66, 40), face, 1)
    for f in (0.45, 0.78):                       # cross-planks
        ax_, ay_ = hx + dx * L * f, hy + dy * L * f
        pygame.draw.line(surf, (37, 26, 15), (int(ax_), int(ay_)),
                         (int(ax_ + px * Wd), int(ay_ + py * Wd)), 1)
    kx = hx + dx * (L - 3) + px * Wd * 0.5       # knob near the free end
    ky = hy + dy * (L - 3) + py * Wd * 0.5
    pygame.draw.circle(surf, (124, 114, 96), (int(kx), int(ky)), 2)
    pygame.draw.circle(surf, (28, 26, 31), (int(hx), int(hy)), 2)  # hinge knuckle


_PATH_GRASS = frozenset(("g", "G", ":"))


_PATH_FRINGE_MARGIN = 8                 # the fringe blobs spill ~3 px into the
                                        # adjacent tile; 8 px margin is plenty.
_PATH_FRINGE_CACHE = {}                 # (tx, ty) -> cached SRCALPHA surface


def _build_path_fringe_card(scene, tx, ty):
    """Render the four-edge fringe + grass-tuft bite-backs ONCE into a
    TILE+2m square SRCALPHA card, so the per-frame call is a single blit
    instead of ~30 circle draws per path tile. Pure function of scene.floor
    around (tx, ty); cleared in _draw_path_fringe when the scene changes."""
    floor, h, w = scene.floor, scene.h, scene.w
    dirt, dirt2 = (88, 68, 45), (74, 56, 37)
    m = _PATH_FRINGE_MARGIN
    card = pygame.Surface((TILE + 2 * m, TILE + 2 * m), pygame.SRCALPHA)
    # Local rx, ry of the tile origin inside the card.
    rx = m
    ry = m
    for si, (ndx, ndy) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):
        nx, ny = tx + ndx, ty + ndy
        if not (0 <= nx < w and 0 <= ny < h) or floor[ny][nx] not in _PATH_GRASS:
            continue
        grass = FLOOR_DEFS[floor[ny][nx]]["color"]
        seed = (tx * 73856093) ^ (ty * 19349663) ^ (si * 83492791)
        if ndy:
            ex = rx; ey = ry + (TILE if ndy > 0 else 0); ax, ay = 1, 0
        else:
            ex = rx + (TILE if ndx > 0 else 0); ey = ry; ax, ay = 0, 1
        for k in range(6):
            u = (k + (_vary(seed, k) % 3) / 3.0) / 6.0
            depth = (_vary(seed, 10 + k) % 9) - 3
            cx = int(ex + ax * TILE * u + ndx * depth)
            cy = int(ey + ay * TILE * u + ndy * depth)
            col = dirt if (_vary(seed, 30 + k) % 3) else dirt2
            pygame.draw.circle(card, col, (cx, cy), 3 + (_vary(seed, 20 + k) % 3))
        for k in range(2):
            u = (1 + 2 * k) / 4.0
            d = 2 + (_vary(seed, 40 + k) % 3)
            cx = int(ex + ax * TILE * u - ndx * d)
            cy = int(ey + ay * TILE * u - ndy * d)
            pygame.draw.circle(card, grass, (cx, cy), 2 + (_vary(seed, 50 + k) % 2))
    return card.convert_alpha()


def _draw_path_fringe(surf, scene, tx, ty, rx, ry):
    """Fray a dirt-path tile's edge wherever it meets grass. Cached as a
    pre-rendered card per (tx, ty); the per-frame cost is one blit instead
    of the ~30 pygame.draw.circle calls the function used to make. The cache
    rides on the same scene-change reset that drops _FLOOR_CACHE."""
    key = (tx, ty)
    card = _PATH_FRINGE_CACHE.get(key)
    if card is None:
        card = _build_path_fringe_card(scene, tx, ty)
        _PATH_FRINGE_CACHE[key] = card
    surf.blit(card, (rx - _PATH_FRINGE_MARGIN, ry - _PATH_FRINGE_MARGIN))


_BANK_LAND = frozenset(("g", "G", ":", "d"))


def _draw_bank_fringe(surf, scene, tx, ty, rx, ry):
    """Muddy, reedy bank where the river meets land: mud bleeding across
    the waterline and reeds rising at the edge, so the river reads as a
    silted marsh channel, not a clean-edged blue stripe. Only water tiles
    fringe their land-facing sides."""
    floor, h, w = scene.floor, scene.h, scene.w
    mud, mud2 = (54, 44, 30), (38, 31, 21)
    reed, reed_dk = (80, 88, 46), (50, 58, 30)
    for si, (ndx, ndy) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):
        nx, ny = tx + ndx, ty + ndy
        if not (0 <= nx < w and 0 <= ny < h) or floor[ny][nx] not in _BANK_LAND:
            continue
        seed = (tx * 73856093) ^ (ty * 19349663) ^ (si * 40503)
        if ndy:
            ex = rx; ey = ry + (TILE if ndy > 0 else 0); ax, ay = 1, 0
        else:
            ex = rx + (TILE if ndx > 0 else 0); ey = ry; ax, ay = 0, 1
        for k in range(5):                       # silt straddling the waterline
            u = (k + (_vary(seed, k) % 3) / 3.0) / 5.0
            depth = (_vary(seed, 10 + k) % 7) - 3
            cx = int(ex + ax * TILE * u + ndx * depth)
            cy = int(ey + ay * TILE * u + ndy * depth)
            pygame.draw.circle(surf, mud if (_vary(seed, 30 + k) % 3) else mud2,
                               (cx, cy), 3 + (_vary(seed, 20 + k) % 2))
        wind = pygame.time.get_ticks() / 650.0
        for k in range(3):                       # reeds rising at the edge, swaying
            u = (k + 0.5) / 3.0
            bx = int(ex + ax * TILE * u + ndx * 2)
            by = int(ey + ay * TILE * u + ndy * 2)
            tipx = bx + (_vary(seed, 60 + k) % 3) - 1 \
                + int(math.sin(wind + seed * 0.01 + k) * 2)
            tipy = by - (6 + (_vary(seed, 70 + k) % 6))
            pygame.draw.line(surf, reed_dk, (bx, by), (tipx, tipy), 1)
            pygame.draw.line(surf, reed, (bx, by), (tipx, tipy - 1), 1)


def _round_water_corners(surf, scene, tx, ty, rx, ry):
    """Smooth the river's blocky outline. CARVES the land colour into the
    water: convex corners get a big grass quarter-round (the corner reads as a
    curve), and each straight land-facing edge gets seeded grass bumps eating
    into the water so the waterline MEANDERS instead of running dead straight.
    A muddy rim on each carve keeps the silted-bank read. Pairs with the bank
    fringe; applies to any '~' water tile."""
    floor, h, w = scene.floor, scene.h, scene.w

    def _land(nx, ny):
        return (not (0 <= nx < w and 0 <= ny < h)) or floor[ny][nx] in _BANK_LAND
    grass, mud = (46, 58, 44), (54, 44, 30)
    seed = (tx * 73856093) ^ (ty * 19349663)
    # convex corners -> a grass quarter-round carves off the square corner
    for d1, d2, cxp, cyp in (((0, -1), (-1, 0), rx, ry),
                             ((0, -1), (1, 0), rx + TILE, ry),
                             ((0, 1), (-1, 0), rx, ry + TILE),
                             ((0, 1), (1, 0), rx + TILE, ry + TILE)):
        if _land(tx + d1[0], ty + d1[1]) and _land(tx + d2[0], ty + d2[1]):
            pygame.draw.circle(surf, grass, (cxp, cyp), 12)
            pygame.draw.circle(surf, mud, (cxp, cyp), 12, 2)      # muddy waterline on the curve
    # straight land-facing edges -> seeded grass bumps undulate the waterline
    for si, (ndx, ndy) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):
        if not _land(tx + ndx, ty + ndy):
            continue
        for k in range(2):
            u = (k + 0.5) / 2.0
            if ndy:
                ecx = rx + TILE * u
                ecy = ry + (TILE if ndy > 0 else 0)
            else:
                ecx = rx + (TILE if ndx > 0 else 0)
                ecy = ry + TILE * u
            r = 5 + (_vary(seed, si * 7 + k) % 4)
            inset = (_vary(seed, si * 3 + k) % 5)        # how far it eats into the water
            cxp = int(ecx - ndx * inset)
            cyp = int(ecy - ndy * inset)
            pygame.draw.circle(surf, grass, (cxp, cyp), r)
            pygame.draw.circle(surf, mud, (cxp, cyp), r, 1)


# The VOID SURROUND (2026-07): alpha veil per tile past the map's edge. Three
# rim tiles continue the nearest in-bounds ground under a deepening veil, then
# the flat build's near-black takes over -- the world's edge reads as ground
# falling away into dark, not a hard cut or a tiling artifact.
_VOID_RIM_FADE = (150, 200, 236)
_VOID_VEILS = {}


def _void_rim_veil(alpha):
    v = _VOID_VEILS.get(alpha)
    if v is None:
        v = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        v.fill((6, 6, 10, alpha))
        _VOID_VEILS[alpha] = v
    return v


def _void_surround_pass(surf, scene, cam_x, cam_y, x0, y0, x1, y1):
    """Compose what lies past the map's edge (the tilt window's off-map area).

    The floor raster skips off-map tiles (draw_scene_terrain used to paint
    them as endless "." floor -- the checkered void around every interior).
    This pass draws the edge instead: for _VOID_RIM_FADE's few tiles past the
    bounds, the rim continues the nearest in-bounds floor char under a
    deepening dark veil, so the ground visibly falls away into the void's
    near-black. Wrapped axes never reach here (no off-map exists there);
    seamless neighbor strips paint real world content OVER this fade where a
    neighbor exists (draw_terrain_tilted runs them after this pass)."""
    W, H = scene.w, scene.h
    wx = scene.wrap_x
    fade = _VOID_RIM_FADE
    depth = len(fade)
    for ty in range(y0, y1):
        ty2 = scene.render_row(ty)
        for tx in range(x0, x1):
            tx2 = tx % W if wx else tx
            if 0 <= ty2 < H and 0 <= tx2 < W:
                continue
            cy2 = min(max(ty2, 0), H - 1)
            cx2 = min(max(tx2, 0), W - 1)
            d = max(abs(ty2 - cy2), abs(tx2 - cx2))
            if d > depth:
                continue
            rx = tx * TILE - cam_x
            ry = ty * TILE - cam_y
            ch = scene.floor[cy2][cx2]
            if ch in _ANIM_FLOOR:
                ch = "."           # the rim ghost never animates
            draw_floor(surf, ch, rx, ry, tx, ty)
            surf.blit(_void_rim_veil(fade[d - 1]), (rx, ry))


def draw_scene_terrain(surf, scene, cam_x, cam_y, x0, y0, x1, y1,
                       skip_billboard=False, skip_roofs=False,
                       bake_static=False):
    """Floor -> path fringe -> wall-cast shadows -> continuous wall mass
    -> non-wall objects, for a tile window. Shared by Scene.draw (camera
    window) and the offline full-map renderer. When scene.wrap_x or
    .wrap_y is True, tile lookups wrap mod self.w / self.h so x0/x1 /
    y0/y1 may extend past the map bounds and the render stays seamless
    across the wrap line.

    `skip_billboard` (the tilt floor pass) omits trees/cornstalks here so they
    aren't painted flat on the warped floor -- draw_terrain_tilted stands them
    up as billboards instead.
    `skip_roofs` (also tilt) omits the gabled roof art so it doesn't render
    as a warped flat plate on the warped floor; the walls supply the
    building's vertical mass under tilt."""
    W, H = scene.w, scene.h
    wx = scene.wrap_x          # row wrap/banding is handled by scene.render_row
    def _lookup_floor(ty, tx):
        ty = scene.render_row(ty)
        if wx: tx %= W
        if not (0 <= ty < H and 0 <= tx < W):
            return "."
        return scene.floor[ty][tx]
    def _lookup_obj(ty, tx):
        ty = scene.render_row(ty)
        if wx: tx %= W
        if not (0 <= ty < H and 0 <= tx < W):
            return "."
        return scene.objects[ty][tx]
    # Floor tiles are a pure deterministic function of (ch, tx, ty) -- the
    # grass mottle, plank shading, stone grout etc. are all seeded from
    # tx/ty and never change -- so render each tile ONCE into a cached
    # surface and blit it thereafter. Only the animated river/void tiles
    # (~/@, which key off get_ticks) are drawn live every frame. This turns
    # ~5ms of per-frame floor rasterisation into a handful of blits on the
    # heavy outdoor scenes. The cache is dropped when the scene changes so
    # it never holds more than one scene's worth of tiles.
    global _FLOOR_CACHE_SCENE
    if _FLOOR_CACHE_SCENE is not scene:
        _FLOOR_CACHE.clear()
        _TILT_STANDEE_CACHE.clear()  # tree/corn billboard cards are scene-keyed
        _CORN_RUN_CACHE.clear()      # corn-run LOD decomposition is per scene
        _PATH_FRINGE_CACHE.clear()   # path-edge fringe cards are scene-keyed
        _FLOOR_CACHE_SCENE = scene   # hold the ref so its identity can't be reused
    def _off_map(ty, tx):
        # Mirrors _lookup_floor's wrap handling: a tile is off-map only after
        # the wrap axes have had their say. Off-map tiles are NOT rastered as
        # "." floor anymore (that painted the endless phantom-tile plain the
        # maintainer called the checkered void); _void_surround_pass composes
        # the world's edge instead.
        ty = scene.render_row(ty)
        if wx:
            tx %= W
        return not (0 <= ty < H and 0 <= tx < W)
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            if _off_map(ty, tx):
                continue
            ch = _lookup_floor(ty, tx)
            rx = tx * TILE - cam_x
            ry = ty * TILE - cam_y
            if ch in _ANIM_FLOOR:
                # `bake_static` (the whole-map floor bake) leaves animated water
                # out -- the tilt path redraws it live over the baked window, so
                # baking it would only freeze it (and its swaying reeds) under
                # the live copy. The (10,10,14) fill it leaves is fully covered
                # by that live water tile.
                if not bake_static:
                    draw_floor(surf, ch, rx, ry, tx, ty)
                continue
            key = (ch, tx, ty)
            tile = _FLOOR_CACHE.get(key)
            if tile is None:
                tile = pygame.Surface((TILE, TILE)).convert()
                draw_floor(tile, ch, 0, 0, tx, ty)
                _FLOOR_CACHE[key] = tile
            surf.blit(tile, (rx, ry))
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            ch = _lookup_floor(ty, tx)
            if ch == "d":
                _draw_path_fringe(surf, scene, tx, ty,
                                  tx * TILE - cam_x, ty * TILE - cam_y)
            elif ch == "~" and not bake_static:
                # Skipped in the static bake (see above) -- the live water
                # overlay redraws the bank fringe + rounded corners each frame.
                _draw_bank_fringe(surf, scene, tx, ty,
                                  tx * TILE - cam_x, ty * TILE - cam_y)
                _round_water_corners(surf, scene, tx, ty,
                                     tx * TILE - cam_x, ty * TILE - cam_y)
    strip = _wall_shadow_strip()
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            ch = _lookup_obj(ty, tx)
            if ch in _SHADOW_CASTERS or ch in _DOOR_CHARS:
                surf.blit(strip, (tx * TILE - cam_x,
                                  (ty + 1) * TILE - cam_y))
    _draw_wall_mass(surf, scene, cam_x, cam_y, x0, y0, x1, y1)
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            ch = _lookup_obj(ty, tx)
            if ch == "." or ch in _WALL_CHARS:
                continue
            if skip_billboard and (ch in _TILT_BILLBOARD_CHARS
                                   or ch in _COUNTER_CHARS
                                   or ch in _RACK_CHARS):
                continue                     # stood up as a 3D box/standee under tilt
            if (skip_billboard and ch in _WINDOW_CHARS
                    and _gap_slab(scene, tx, ty) is not None):
                # Thin-slab scene: the 3D band + set-in pane carry the whole
                # window read; the flat full-tile art would peek out past the
                # thin band as a lit strip at the wall's foot.
                continue
            rx = tx * TILE - cam_x
            ry = ty * TILE - cam_y
            if ch in _DOOR_CHARS:
                _draw_door_opening(surf, rx, ry, _door_room_dir(scene, tx, ty),
                                   tx, ty,
                                   style=getattr(scene, "door_style", "wood"))
            else:
                draw_object(surf, ch, rx, ry, tx, ty)
    # Unified gabled roofs, drawn over the walls so each building reads
    # as one overhanging roof (door stays visible under the front eave).
    # Tilt skips this -- a top-down roof drawn into the warped floor pass
    # reads as a flat plate ON THE GROUND. The walls + furniture supply
    # vertical mass instead.
    if not skip_roofs:
        _draw_scene_roofs(surf, scene, cam_x, cam_y, x0, y0, x1, y1)


# --- Tilted (oblique-camera) terrain (DESIGN.md §10) -------------------
# Active only when camera.pitch > 0. The floor is a flat z=0 plane, so we
# render the visible window flat (exactly the legacy raster, wrap-aware) and
# warp the whole image to the oblique plane -- preserving every procedural
# floor detail -- then extrude wall tiles as upright quads on top.
_TILT_WALL_RISE = 26

# Single-slot cache for the warped floor (the raster + rotate + scale in
# draw_terrain_tilted). That surface is a pure function of the camera pose +
# scene, and the camera eases to a stop whenever the player is settled
# (standing still, in dialogue, in a menu), so once it stops moving we rebuild
# the same warped floor every frame for nothing. Keyed on the rounded camera
# pose; a miss (the camera moved, or a new scene) rebuilds it. This was the
# single biggest per-frame cost in the wrapped town.
_TILT_FLOOR_CACHE = {"key": None, "surf": None}

# Whole-scene flat-floor bake. On a big wrap scene (Brimley: 100x100) the tilt
# floor pass rastered a ~78x78 tile window EVERY frame the camera panned -- four
# passes over ~6000 tiles plus ~6000 blits, the dominant walking-frame cost.
# But the floor is STATIC: render the entire map's flat floor ONCE into a cached
# surface, then each frame blit the window sub-region out of it (wrap-aware, a
# handful of blits) and warp that. Only the animated water tiles are redrawn
# live on top. Gated to wrap scenes within a pixel budget (large AND small --
# a small torus wraps many copies of itself into the window, so it gains the
# most); non-wrap rooms keep the per-tile path (cheap already, and they own the
# byte-identity gate via the flat Scene.draw, which is untouched).
_TILT_FULLMAP_CACHE = {"scene": None, "surf": None, "water": None}

# Single-slot cache for the wall-tile window scan in draw_terrain_tilted.
# The scan touches every tile in the visible window (~6000 on Brimley) every
# frame, but its result only changes when the tile window moves or the object
# grid mutates. Holds the scene ref so a recycled id() can't false-hit.
# Invalidated by invalidate_tilt_objects() whenever a tile is opened/changed
# at runtime (axe chops, consumed markers).
_TILT_WALL_SCAN_CACHE = {"key": None, "walls": None, "scene": None}


def invalidate_tilt_objects():
    """Call after mutating a Scene's `objects` grid mid-play (chopped boards,
    consumed markers) so the tilt render caches drop their stale geometry."""
    _TILT_WALL_SCAN_CACHE["key"] = None
    _TILT_WALL_SCAN_CACHE["walls"] = None
    # Wall box cards key on neighbour exposure; an opened tile changes the
    # faces of the walls around it.
    _WALL_BOX_CACHE.clear()
    _WALL_BOX_ORDER.clear()
    # The warped-floor cache keys on the camera pose only; flat-drawn objects
    # (debris '*', boards 'q') are painted INTO it, so a settled camera would
    # keep showing a chopped tile until the player moved. Drop it too.
    _TILT_FLOOR_CACHE["key"] = None
    _TILT_FLOOR_CACHE["surf"] = None
_TILT_FULLMAP_BUDGET_PX = 16 * 1024 * 1024   # don't bake maps bigger than this


def _tilt_use_fullmap(scene):
    # Every wrap scene within the pixel budget bakes. Big ones (Brimley) for
    # the obvious reason; SMALL ones even more so -- a 24x22 torus under the
    # tilt window wraps ~10 copies of itself, so the per-tile path rasters
    # thousands of wrapped tiles per panned frame while its whole-map bake is
    # a few hundred KB blitted a handful of times (the cornfield_maze was the
    # worst walking-fps scene in the game for exactly this reason).
    return ((scene.wrap_x or scene.wrap_y)
            and (scene.w * TILE) * (scene.h * TILE) <= _TILT_FULLMAP_BUDGET_PX)


def _tilt_fullmap(scene):
    """The cached whole-map flat floor + the list of animated floor tiles.
    Built once per scene (lazy); the bake reuses draw_scene_terrain so it is
    pixel-for-pixel the per-tile raster, just done for the entire map at world
    origin instead of a moving window."""
    c = _TILT_FULLMAP_CACHE
    if c["scene"] is scene:
        return c["surf"], c["water"]
    W, H = scene.w, scene.h
    full = pygame.Surface((W * TILE, H * TILE))
    full.fill((10, 10, 14))
    draw_scene_terrain(full, scene, 0, 0, 0, 0, W, H,
                       skip_billboard=True, skip_roofs=True, bake_static=True)
    water = [(tx, ty) for ty in range(H) for tx in range(W)
             if scene.floor[ty][tx] in _ANIM_FLOOR]
    c["scene"] = scene
    c["surf"] = full
    c["water"] = water
    # The per-tile floor cache just filled with the whole map (~10k tiles);
    # we blit from the baked surface now, so drop it to reclaim that memory.
    _FLOOR_CACHE.clear()
    return full, water


def _blit_window_wrapped(dst, src, wx0, wy0, wrap_x, wrap_y):
    """Blit the world rect starting at (wx0, wy0) of size = dst out of the
    whole-map surface `src`, tiling it across the wrap seam (up to 2x2 copies)."""
    sw, sh = dst.get_size()
    mw, mh = src.get_size()
    kx = (range(math.floor(wx0 / mw), math.floor((wx0 + sw - 1) / mw) + 1)
          if wrap_x else [0])
    jy = (range(math.floor(wy0 / mh), math.floor((wy0 + sh - 1) / mh) + 1)
          if wrap_y else [0])
    for j in jy:
        for k in kx:
            dst.blit(src, (int(k * mw - wx0), int(j * mh - wy0)))


def _overlay_anim_water(dst, scene, water, wx0, wy0, span):
    """Redraw the animated water (floor + swaying bank reeds + rounded corners)
    live over the baked window, for every water tile -- and wrap-clone -- inside
    it. Two passes so the draw order matches the per-tile raster exactly: all
    water floors first, then the fringes/corners on top. The fringe/corner
    helpers self-guard on map bounds, so wrap-clones draw only their floor (the
    same quirk the per-tile path has)."""
    if not water:
        return
    W, H = scene.w, scene.h
    mw, mh = W * TILE, H * TILE
    kx = (range(math.floor(wx0 / mw), math.floor((wx0 + span - 1) / mw) + 1)
          if scene.wrap_x else [0])
    jy = (range(math.floor(wy0 / mh), math.floor((wy0 + span - 1) / mh) + 1)
          if scene.wrap_y else [0])
    cells = []
    for j in jy:
        for k in kx:
            for (tx, ty) in water:
                rtx, rty = tx + k * W, ty + j * H
                rx = rtx * TILE - wx0
                ry = rty * TILE - wy0
                if -TILE <= rx < span and -TILE <= ry < span:
                    cells.append((rtx, rty, int(rx), int(ry)))
    for (rtx, rty, rx, ry) in cells:
        draw_floor(dst, "~", rx, ry, rtx, rty)
    for (rtx, rty, rx, ry) in cells:
        _draw_bank_fringe(dst, scene, rtx, rty, rx, ry)
        _round_water_corners(dst, scene, rtx, rty, rx, ry)



def _tilt_window_half(camera):
    """Smallest centred half-span (world px) whose flat window still covers
    the tilted screen. Unproject the screen corners (+ upward wall headroom)
    and take the farthest world offset from the view centre. Uses the live
    VIEWPORT size (camera.origin is its centre), not the window constants, so a
    low-res render buffer computes the right -- smaller -- window."""
    vw, vh = camera.origin[0] * 2, camera.origin[1] * 2
    corners = [(0, 0), (vw, 0), (0, vh), (vw, vh),
               (vw // 2, -_TILT_WALL_RISE)]
    half = 0.0
    for sx, sy in corners:
        wx, wy = camera.unproject(sx, sy)
        half = max(half, abs(wx - camera.cam_x), abs(wy - camera.cam_y))
    return half + TILE


def _tilt_warp(flat, camera, fast=False):
    """Affine warp of the flat floor to match camera.project() for z=0:
    world-rotate by yaw, then scale x by scale and y by scale*cos(pitch).
    At yaw 0 (the eased-to-rest head position, i.e. most walking frames) the
    rotate is skipped entirely -- transform.rotate(s, 0) still copies the
    whole large window surface for nothing.

    At nonzero yaw the order is uniform-shrink FIRST, then rotate, then
    the cos(pitch) y-squash: rotation commutes with a UNIFORM scale, so
    the transform is identical, but the expensive rotate runs on
    scale^2 (~half) of the pixels -- it was the top per-frame cost of a
    head-turn. `scale` (nearest) rather than `smoothscale` throughout:
    the floor raster is a low-detail tile pattern under the tilt +
    Brimley's haze, and smoothscale on surfaces this size was ~10x.

    `fast` (2026-07 cornfield FPS fix): DYNAMIC RESOLUTION for a look in
    progress -- the whole pipeline runs at half res and one nearest
    upscale lands it on the full target, quartering the rotate's pixels.
    Motion hides the softness; the caller rebuilds SHARP the frame the
    yaw settles."""
    cp = max(0.05, math.cos(camera.pitch))
    s = camera.scale
    deg = math.degrees(camera.yaw)
    w, h = flat.get_size()
    if abs(deg) <= 1e-4:
        return pygame.transform.scale(
            flat, (max(1, int(w * s)), max(1, int(h * s * cp))))
    if fast:
        small = pygame.transform.scale(
            flat, (max(1, int(w * s * 0.5)), max(1, int(h * s * 0.5))))
        rotated = pygame.transform.rotate(small, deg)
        rw, rh = rotated.get_size()
        return pygame.transform.scale(
            rotated, (rw * 2, max(1, int(rh * 2 * cp))))
    small = pygame.transform.scale(
        flat, (max(1, int(w * s)), max(1, int(h * s))))
    rotated = pygame.transform.rotate(small, deg)
    rw, rh = rotated.get_size()
    return pygame.transform.scale(rotated, (rw, max(1, int(rh * cp))))


_DOOR_HEAD = 19      # doorway opening height; the lintel beam runs head->rise


def _quad_pt(quad, fx, fy):
    """A point inside a projected quad (bl, br, tr, tl) at fractions
    fx (0..1 left->right along the base) and fy (0..1 bottom->top)."""
    bl, br, tr, tl = quad
    bx = bl[0] + (br[0] - bl[0]) * fx; by = bl[1] + (br[1] - bl[1]) * fx
    tx_ = tl[0] + (tr[0] - tl[0]) * fx; ty_ = tl[1] + (tr[1] - tl[1]) * fx
    return (bx + (tx_ - bx) * fy, by + (ty_ - by) * fy)


def _extrude_box(surf, camera, scene, tx, ty, z0, z1, neigh=_WALL_CHARS,
                 face_col=None, top_col=None, bevel=0, foot=None):
    """One tile extruded between heights z0..z1. Rotation-correct: every
    EXPOSED side face (neighbour char not in `neigh`) is drawn, depth-sorted
    far->near so near faces overdraw far, capped with a flat shaded top quad
    (no axis-aligned texture that would overflow once the camera yaws).
    `face_col` / `top_col` default to the near-black wall palette; pass wood
    tones for a counter/furniture box. `bevel` (a corner bitmask from
    `_bevel_corners`) chamfers the given exposed convex corners; 0 draws the
    verbatim square box (byte-identical). `foot` (a tile-local (x0,y0,x1,y1) px
    rect from `_wall_slab`) shrinks the box to a THIN SLAB inside the tile; None
    is the full tile (byte-identical). bevel and foot are never both set (a slab
    scene gates the bevel off)."""
    face_col = _WALL_FACE if face_col is None else face_col
    top_col = _WALL_TOP if top_col is None else top_col
    wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
    hw = TILE / 2
    # Footprint edges as offsets from the tile CENTRE (None -> the full square).
    if foot is None:
        fx0, fy0, fx1, fy1 = -hw, -hw, hw, hw
    else:
        fx0, fy0, fx1, fy1 = foot[0] - hw, foot[1] - hw, foot[2] - hw, foot[3] - hw
    mx, my = (fx0 + fx1) / 2.0, (fy0 + fy1) / 2.0

    def P(dx, dy, dz):
        return camera.project(wx + dx, wy + dy, dz)
    near = tuple(int(c * 0.5) for c in face_col)     # N/S faces
    side = tuple(int(c * 0.7) for c in face_col)     # E/W faces
    # Per-tile value jitter so the mass reads as many battered blocks rather
    # than one flat slab (tile-seeded -> stable, no shimmer as the camera
    # moves; matches the floor jitter).
    jv = (_vary(tx * 8009 + ty, 3) % 15) - 7
    near = tuple(max(0, min(255, c + jv)) for c in near)
    side = tuple(max(0, min(255, c + jv)) for c in side)

    def is_n(ax, ay):
        if scene.wrap_y: ay %= scene.h
        if scene.wrap_x: ax %= scene.w
        if 0 <= ay < scene.h and 0 <= ax < scene.w:
            return scene.objects[ay][ax] in neigh
        return True

    if not bevel:
        g = [P(fx0, fy0, z0), P(fx1, fy0, z0), P(fx1, fy1, z0), P(fx0, fy1, z0)]
        t = [P(fx0, fy0, z1), P(fx1, fy0, z1), P(fx1, fy1, z1), P(fx0, fy1, z1)]
        # (neighbour dx, dy, face centroid offset, quad corners, colour) per side
        faces = (
            (0, 1, (mx, fy1), (g[3], g[2], t[2], t[3]), near),    # south
            (0, -1, (mx, fy0), (g[0], g[1], t[1], t[0]), near),   # north
            (-1, 0, (fx0, my), (g[0], g[3], t[3], t[0]), side),   # west
            (1, 0, (fx1, my), (g[1], g[2], t[2], t[1]), side),    # east
        )
        vis = [(camera.depth(wx + ox, wy + oy, (z0 + z1) / 2), quad, col)
               for ndx, ndy, (ox, oy), quad, col in faces
               if not is_n(tx + ndx, ty + ndy)]
        vis.sort(key=lambda f: f[0])                      # far first
        for _, quad, col in vis:
            pygame.draw.polygon(surf, col, quad)
        # Battered detail on the exposed near (south) face so no two wall faces
        # read the same: a per-tile dark water-stain streak, a pit cluster, or a
        # faint lit course line. Projected through the quad so it leans correctly.
        if z1 - z0 > TILE * 0.4 and not is_n(tx, ty + 1):
            sq = (g[3], g[2], t[2], t[3])
            hsh = _vary(tx, ty + 7)
            if hsh % 3 == 0:                               # water-stain dribble
                fx = 0.2 + (hsh % 6) / 10.0
                a = _quad_pt(sq, fx, 0.05); b = _quad_pt(sq, fx, 0.85)
                pygame.draw.line(surf, tuple(int(c * 0.6) for c in near),
                                 (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1)
            elif hsh % 4 == 0:                             # pitting cluster
                for k in range(3):
                    p = _quad_pt(sq, 0.25 + ((hsh >> k) % 6) / 12.0,
                                 0.25 + ((hsh >> (k + 2)) % 5) / 12.0)
                    pygame.draw.rect(surf, tuple(int(c * 0.7) for c in near),
                                     (int(p[0]), int(p[1]), 2, 2))
            elif hsh % 5 == 0:                             # a faint lit course line
                a = _quad_pt(sq, 0.04, 0.5); b = _quad_pt(sq, 0.96, 0.5)
                pygame.draw.line(surf, tuple(min(255, int(c * 1.4)) for c in near),
                                 (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1)
        # flat shaded top cap: lit but kept dark to read as the game's near-black
        # walls -- top clearly lighter than the sides for form, darker grout edge.
        pygame.draw.polygon(surf, tuple(int(c * 0.72) for c in top_col), t)
        pygame.draw.polygon(surf, tuple(int(c * 0.4) for c in top_col), t, 1)
        return

    # --- beveled path: chamfer the exposed convex corners in `bevel` ---------
    B = _BEVEL_INSET
    # Each cardinal face slides its endpoint(s) IN along the face at any corner
    # that is beveled; the raw corner otherwise. (dx along the N/S edges, dy
    # along the E/W edges.)
    nw_nx = -hw + B if bevel & _BV_NW else -hw   # NW pt on the north edge
    ne_nx = hw - B if bevel & _BV_NE else hw     # NE pt on the north edge
    sw_sx = -hw + B if bevel & _BV_SW else -hw   # SW pt on the south edge
    se_sx = hw - B if bevel & _BV_SE else hw     # SE pt on the south edge
    nw_wy = -hw + B if bevel & _BV_NW else -hw   # NW pt on the west edge
    sw_wy = hw - B if bevel & _BV_SW else hw     # SW pt on the west edge
    ne_ey = -hw + B if bevel & _BV_NE else -hw   # NE pt on the east edge
    se_ey = hw - B if bevel & _BV_SE else hw     # SE pt on the east edge
    faces = (
        (0, 1, (0, hw),      # south (y=hw): SW -> SE
         (P(sw_sx, hw, z0), P(se_sx, hw, z0), P(se_sx, hw, z1), P(sw_sx, hw, z1)), near),
        (0, -1, (0, -hw),    # north (y=-hw): NW -> NE
         (P(nw_nx, -hw, z0), P(ne_nx, -hw, z0), P(ne_nx, -hw, z1), P(nw_nx, -hw, z1)), near),
        (-1, 0, (-hw, 0),    # west (x=-hw): NW -> SW
         (P(-hw, nw_wy, z0), P(-hw, sw_wy, z0), P(-hw, sw_wy, z1), P(-hw, nw_wy, z1)), side),
        (1, 0, (hw, 0),      # east (x=hw): NE -> SE
         (P(hw, ne_ey, z0), P(hw, se_ey, z0), P(hw, se_ey, z1), P(hw, ne_ey, z1)), side),
    )
    vis = [(camera.depth(wx + ox, wy + oy, (z0 + z1) / 2), quad, col)
           for ndx, ndy, (ox, oy), quad, col in faces
           if not is_n(tx + ndx, ty + ndy)]
    # A vertical chamfer face bridging each beveled corner's two edge points.
    # Never culled (a back-facing one is overdrawn by the far->near sort).
    for bit, (ax_, ay_), (bx_, by_) in (
            (_BV_NW, (nw_nx, -hw), (-hw, nw_wy)),
            (_BV_NE, (ne_nx, -hw), (hw, ne_ey)),
            (_BV_SE, (se_sx, hw), (hw, se_ey)),
            (_BV_SW, (sw_sx, hw), (-hw, sw_wy))):
        if not (bevel & bit):
            continue
        quad = (P(ax_, ay_, z0), P(bx_, by_, z0), P(bx_, by_, z1), P(ax_, ay_, z1))
        cxw, cyw = wx + (ax_ + bx_) / 2.0, wy + (ay_ + by_) / 2.0
        vis.append((camera.depth(cxw, cyw, (z0 + z1) / 2), quad, near))
    vis.sort(key=lambda f: f[0])
    for _, quad, col in vis:
        pygame.draw.polygon(surf, col, quad)
    # Beveled top cap (a raw corner's two perimeter points coincide -> harmless).
    top_poly = [
        P(nw_nx, -hw, z1), P(ne_nx, -hw, z1),   # north edge
        P(hw, ne_ey, z1), P(hw, se_ey, z1),     # east edge
        P(se_sx, hw, z1), P(sw_sx, hw, z1),     # south edge
        P(-hw, sw_wy, z1), P(-hw, nw_wy, z1),   # west edge
    ]
    pygame.draw.polygon(surf, tuple(int(c * 0.72) for c in top_col), top_poly)
    pygame.draw.polygon(surf, tuple(int(c * 0.4) for c in top_col), top_poly, 1)


def _tilt_wall_tint(scene, tx, ty):
    """(face_col, top_col) for this wall tile, or (None, None) if it's not
    in a building (use the default near-black palette). Cached per-tile on
    the scene so the hot wall loop doesn't recompute the building palette
    every frame; cleared with the wall_region_map when scenes rebuild."""
    cache = getattr(scene, "_wall_tint_cache", None)
    if cache is None:
        cache = scene._wall_tint_cache = {}
    key = (tx, ty)
    cached = cache.get(key)
    if cached is not None:
        return cached
    region = wall_region_for(scene, tx, ty)
    if region is None:
        face_col = top_col = None
    else:
        _roof, (dr, dg, db), _trim = _get_building_palette(region)
        face_col = (max(0, min(255, _WALL_FACE[0] + dr)),
                    max(0, min(255, _WALL_FACE[1] + dg)),
                    max(0, min(255, _WALL_FACE[2] + db)))
        top_col = (max(0, min(255, _WALL_TOP[0] + dr)),
                   max(0, min(255, _WALL_TOP[1] + dg)),
                   max(0, min(255, _WALL_TOP[2] + db)))
    cache[key] = (face_col, top_col)
    return face_col, top_col


def _extrude_prism(surf, camera, scene, tx, ty, z0, z1, poly, draw_edges,
                   face_col, top_col):
    """Extrude a local-px OUTLINE polygon (the rounded thin-wall footprint)
    between z0..z1: exposed side faces (draw_edges[i] False = a merged neighbour
    seam, skipped) depth-sorted far->near, capped with the top polygon. The
    rounded-corner sibling of _extrude_box for _SLAB_SCENES walls."""
    wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
    hw = TILE / 2

    def P(lx, ly, dz):                     # local px -> world offset -> screen
        return camera.project(wx + lx - hw, wy + ly - hw, dz)
    near = tuple(int(c * 0.5) for c in face_col)     # N/S faces
    side = tuple(int(c * 0.7) for c in face_col)     # E/W faces
    jv = (_vary(tx * 8009 + ty, 3) % 15) - 7
    near = tuple(max(0, min(255, c + jv)) for c in near)
    side = tuple(max(0, min(255, c + jv)) for c in side)
    n = len(poly)
    ground = [P(px, py, z0) for px, py in poly]
    top = [P(px, py, z1) for px, py in poly]
    faces = []
    for i in range(n):
        if not draw_edges[i]:
            continue
        j = (i + 1) % n
        (ax, ay), (bx, by) = poly[i], poly[j]
        mx, my = (ax + bx) / 2 - hw, (ay + by) / 2 - hw
        col = near if abs(bx - ax) >= abs(by - ay) else side
        quad = (ground[i], ground[j], top[j], top[i])
        faces.append((camera.depth(wx + mx, wy + my, (z0 + z1) / 2), quad, col))
    faces.sort(key=lambda f: f[0])
    for _, quad, col in faces:
        pygame.draw.polygon(surf, col, quad)
    pygame.draw.polygon(surf, tuple(int(c * 0.72) for c in top_col), top)
    pygame.draw.polygon(surf, tuple(int(c * 0.4) for c in top_col), top, 1)


def _tilt_wall_box(surf, camera, scene, tx, ty):
    face_col, top_col = _tilt_wall_tint(scene, tx, ty)
    poly = _rounded_wall_poly(scene, tx, ty)
    if poly is None:
        _extrude_box(surf, camera, scene, tx, ty, 0, _TILT_WALL_RISE,
                     face_col=face_col, top_col=top_col,
                     bevel=_bevel_corners(scene, tx, ty))
    else:
        pts, draw_edges = poly
        tint = _wall_tint_for(scene)       # material colour, matching the mass
        fc = _tint_col(face_col if face_col else _WALL_FACE, tint)
        tc = _tint_col(top_col if top_col else _WALL_TOP,
                       _wall_top_tint_for(scene))   # top may be grass over stone
        _extrude_prism(surf, camera, scene, tx, ty, 0, _TILT_WALL_RISE,
                       pts, draw_edges, fc, tc)


_COUNTER_RISE = 15      # waist-high: a divider you can see over, not a wall


def _tilt_counter_box(surf, camera, scene, tx, ty):
    """The kitchen counter / peninsula divider: a waist-high wood box (shorter
    than a wall) so the common-room divider reads as a solid 3D bar under the
    tilt instead of a flat painted strip. Adjacent counter tiles merge into one
    run (counter neighbours cull their shared faces)."""
    _extrude_box(surf, camera, scene, tx, ty, 0, _COUNTER_RISE,
                 neigh=_WALL_CHARS | _COUNTER_CHARS,
                 face_col=(96, 72, 48), top_col=(122, 98, 66))


_RACK_RISE = 22         # a lumber rack: stacked to the shoulder -- it
                        # BLOCKS sight (the rack maze is the room's
                        # cover ladder), so the stack must look too
                        # tall to see over (2026-07 stealth pass)


def _tilt_rack_box(surf, camera, scene, tx, ty):
    """The mine's lumber rack as a real low volume: a chest-high timber
    box (stacked sawn boards between end posts), with board seams on the
    near face so it reads as lumber, not masonry. Adjacent racks merge
    into one run (2026-07: the old 's' tiles drew flat bookshelf sprites
    warped onto the floor)."""
    _extrude_box(surf, camera, scene, tx, ty, 0, _RACK_RISE,
                 neigh=_WALL_CHARS | _RACK_CHARS,
                 face_col=(78, 60, 39), top_col=(100, 78, 51))
    wx0, wx1 = tx * TILE + 2, tx * TILE + TILE - 2
    wyf = ty * TILE + TILE
    for z in (5, 10, 15, 19):
        p0 = camera.project(wx0, wyf, z)
        p1 = camera.project(wx1, wyf, z)
        pygame.draw.line(surf, (52, 40, 27), p0, p1, 1)
    # end grain: a pale tick at one end of the top board
    pg = camera.project(wx0 + 2, wyf, _RACK_RISE - 2)
    pygame.draw.rect(surf, (124, 102, 68), (int(pg[0]), int(pg[1]), 2, 2))


def _tilt_door_box(surf, camera, scene, tx, ty):
    """A doorway in the extruded wall: a lintel BEAM spanning the top of the
    tile (head->rise) with the passage open below. The flanking wall tiles
    supply the jambs; a swung leaf hangs in the opening. Faces abutting walls
    OR other doors are culled so a multi-tile gate reads as one clean opening.
    In a slab scene the lintel takes the wall's slab footprint through the gap
    (_gap_slab) and the wall's material tint, so the doorway sits IN the thin
    wall line instead of jutting from it as a full-tile monolith."""
    wtx = tx % scene.w if scene.wrap_x else tx
    wty = ty % scene.h if scene.wrap_y else ty
    bands = _gap_slab(scene, wtx, wty)
    if bands:
        face_col, top_col = _tilt_wall_tint(scene, tx, ty)
        tint = _wall_tint_for(scene)
        fc = _tint_col(face_col if face_col else _WALL_FACE, tint)
        tc = _tint_col(top_col if top_col else _WALL_TOP,
                       _wall_top_tint_for(scene))
        for band in bands:
            _extrude_box(surf, camera, scene, tx, ty, _DOOR_HEAD,
                         _TILT_WALL_RISE, neigh=_WALL_CHARS | _DOOR_CHARS,
                         face_col=fc, top_col=tc, foot=band)
    else:
        _extrude_box(surf, camera, scene, tx, ty, _DOOR_HEAD, _TILT_WALL_RISE,
                     neigh=_WALL_CHARS | _DOOR_CHARS)
    _draw_doorway(surf, camera, scene, tx, ty)


def _draw_doorway(surf, camera, scene, tx, ty):
    """A framed doorway: a dark recess set into the wall, a wood frame (jambs +
    lintel) around the opening, and a leaf hung on one jamb -- ajar for passable
    doors, shut (filling the opening) for facade/locked ones. Everything is
    projected on the doorway plane so it leans correctly under the camera."""
    wtx = tx % scene.w if scene.wrap_x else tx
    wty = ty % scene.h if scene.wrap_y else ty
    if not (0 <= wty < scene.h and 0 <= wtx < scene.w):
        return
    ch = scene.objects[wty][wtx]
    solid = bool(OBJECT_DEFS.get(ch, {}).get("solid"))
    r = {"N": (0, -1), "S": (0, 1), "E": (1, 0),
         "W": (-1, 0)}[_door_room_dir(scene, wtx, wty)]
    wv = (-r[1], r[0])                       # wall axis (perp to room dir)
    wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
    hw = TILE / 2
    head = _DOOR_HEAD
    wood, wood_lo, wood_hi = (84, 59, 36), (52, 36, 22), (108, 80, 50)

    def Q(u, z, off=0.0):
        # u: along the wall axis [-hw, hw]; z: height; off: depth into room (-)
        return camera.project(wx + wv[0] * u + r[0] * off,
                              wy + wv[1] * u + r[1] * off, z)
    # 1. the recess (set slightly INTO the wall, off +): normally a flat dark
    # doorway, but for an opted-in SEE-THROUGH door it shows the ACTUAL room
    # beyond, rendered through this same tilt camera and masked to the recess
    # (rendering.portal.draw_through_aperture). The frame + leaf draw on top.
    rec = [Q(-hw + 1, 0, 3), Q(hw - 1, 0, 3), Q(hw - 1, head, 3), Q(-hw + 1, head, 3)]
    views = getattr(scene, "_door_views", None)
    view = views.get((wtx, wty)) if (views and not solid) else None
    if view is not None:
        try:
            from rendering.portal import draw_through_aperture
            draw_through_aperture(surf, view["target"], view["anchor_px"], rec,
                                  camera, 0.0,
                                  cache_key=("door", id(scene), wtx, wty),
                                  desaturate=False, door_world=(wx, wy),
                                  sight=getattr(scene, "_door_actor_sight", None))
        except Exception:
            pygame.draw.polygon(surf, (7, 6, 9), rec)
    else:
        pygame.draw.polygon(surf, (7, 6, 9), rec)
    if getattr(scene, "door_style", "wood") == "cave":
        # THE ADIT (2026-07, the mine retrofit): a rough rock mouth with
        # timber shoring instead of a framed, hinged door. No leaf -- a
        # mine adit has no door; the dark (or the see-through room) shows
        # straight through. Jagged rock lumps overlap the recess edges so
        # the opening never reads as a neat rectangle, and the shoring is
        # old work: one post leans, the lintel beam sags a little.
        seed = (wtx * 73856093) ^ (wty * 19349663)
        rock, rock_lo = (58, 55, 62), (34, 32, 38)

        def _j(i, span=5):
            return (seed >> (i * 3)) % span
        for i in range(4):                       # rim lumps down both jambs
            z0 = head * (0.12 + 0.22 * i)
            bulge = 2.5 + _j(i)
            for u_edge, sgn in ((-hw + 1, 1), (hw - 1, -1)):
                pygame.draw.polygon(surf, rock_lo if i % 2 else rock, [
                    Q(u_edge, z0, 2),
                    Q(u_edge + sgn * bulge, z0 + head * 0.10, 1),
                    Q(u_edge, z0 + head * 0.20, 2)])
        for i in range(3):                       # teeth hanging under the head
            u0 = -hw + 4 + i * (2 * hw - 8) / 2.6 + _j(i + 4, 3)
            drop = 3.0 + _j(i + 8, 4)
            pygame.draw.polygon(surf, rock_lo, [
                Q(u0 - 2.5, head, 2), Q(u0 + 2.5, head, 2),
                Q(u0, head - drop, 1)])
        wood_f, wood_e = (86, 64, 40), (54, 40, 24)
        lean = 1.0 + _j(9, 3) * 0.5
        for u0, u1, tshift in ((-hw + 1.0, -hw + 4.5, 0.0),
                               (hw - 4.5 - lean, hw - 1.0, lean)):
            post = [Q(u0, 0, -1), Q(u1, 0, -1),
                    Q(u1 + tshift, head - 2, -1), Q(u0 + tshift, head - 2, -1)]
            pygame.draw.polygon(surf, wood_f, post)
            pygame.draw.polygon(surf, wood_e, post, 1)
        sag = 1.5 + _j(10, 3)
        beam = [Q(-hw - 1, head - 1, -1.5), Q(hw + 1, head - 1 - sag, -1.5),
                Q(hw + 1, head + 3 - sag, -1.5), Q(-hw - 1, head + 3, -1.5)]
        pygame.draw.polygon(surf, wood_f, beam)
        pygame.draw.polygon(surf, wood_e, beam, 1)
        return
    # 2. wood frame on the room face (off -), a "n" around the opening
    tw, th, off = 4.0, 3.0, -1.0

    def face(u0, u1, z0, z1, col):
        pygame.draw.polygon(surf, col, [Q(u0, z0, off), Q(u1, z0, off),
                                        Q(u1, z1, off), Q(u0, z1, off)])
    face(-hw, -hw + tw, 0, head, wood)            # left jamb
    face(hw - tw, hw, 0, head, wood)              # right jamb
    face(-hw, hw, head - th, head, wood_hi)       # lintel
    # 3. the leaf, hinged at the left jamb. At rest a passable door
    # hangs ajar and a locked/facade one sits shut; a live door_pulse
    # (someone passing through -- the player leaving, the noise-bleed
    # visitor arriving) swings it wide and Game._tick_doors eases it
    # back. Tilt-only: the flat pitch-0 view keeps its static leaves.
    a = 0.0 if solid else math.radians(26)        # shut vs ajar
    anim = getattr(scene, "_door_anim", None)
    if anim and not solid:
        st = anim.get((wtx, wty))
        if st is not None:
            k = max(0.0, min(1.0, st["open"]))
            k = k * k * (3.0 - 2.0 * k)           # smoothstep ease
            a = math.radians(26.0 + 62.0 * k)     # ajar -> swung wide
    ca, sa = math.cos(a), math.sin(a)
    hu = -hw + tw                                  # hinge at inner left jamb
    L = (2 * hw - 2 * tw)                          # spans the clear opening
    hx, hy = wx + wv[0] * hu, wy + wv[1] * hu
    fdx = wv[0] * ca + r[0] * sa
    fdy = wv[1] * ca + r[1] * sa
    fx, fy = hx + fdx * L, hy + fdy * L
    bH0, bH1 = camera.project(hx, hy, 0), camera.project(hx, hy, head - 1)
    bF0, bF1 = camera.project(fx, fy, 0), camera.project(fx, fy, head - 1)
    leaf = [bH0, bF0, bF1, bH1]
    pygame.draw.polygon(surf, wood, leaf)
    pygame.draw.polygon(surf, wood_lo, leaf, 1)
    for f in (0.5,):                               # a plank seam
        s0 = (bH0[0] + (bF0[0] - bH0[0]) * f, bH0[1] + (bF0[1] - bH0[1]) * f)
        s1 = (bH1[0] + (bF1[0] - bH1[0]) * f, bH1[1] + (bF1[1] - bH1[1]) * f)
        pygame.draw.line(surf, wood_lo, s0, s1, 1)
    hh = (bF0[0] * 0.82 + bH0[0] * 0.18, bF0[1] * 0.82 + bH0[1] * 0.18)
    hh1 = (bF1[0] * 0.82 + bH1[0] * 0.18, bF1[1] * 0.82 + bH1[1] * 0.18)
    handle = ((hh[0] + hh1[0]) / 2, (hh[1] + hh1[1]) / 2)
    pygame.draw.circle(surf, (212, 192, 124), (int(handle[0]), int(handle[1])), 2)


# Decals that LIE on the floor -- they must warp onto the oblique floor plane
# (rotate with yaw, squash with pitch) like the terrain raster, not paste as a
# screen-aligned sprite that ignores the camera.
_FLOOR_DECAL_KINDS = frozenset((
    "rug", "bloodstain", "gore", "yellow_sign", "bloody_handprint", "bloody_pile",
    "chalk_door",
    # Things that lie IN the ground plane (sigils scratched in stone, a sink
    # where the river drains, a floor hatch, a slumped body in its pool): warped
    # flat onto the floor so they turn with the room instead of standing up as a
    # top-down sticker under tilt. Pitch 0 draws them flat via Scene.draw as before.
    "symbol", "binding_sigil", "swallow_hole", "phantom_mark",
    "body", "water_trail", "child_drawing", "campfire",
    "effects_pile", "garden_patch",
    # Low overhead foliage (drawn top-down): a flat warped decal reads as a
    # shrub on the ground, where a standee would stand the overhead blob up
    # vertically as a smear.
    "bush",
    # Marks scratched into the floor or the body of something laid in the dirt:
    # all read as ground decals and want to turn with the room under tilt.
    "mud_footprint", "claw_marks", "dead_crow", "watching_wound",
    # Low ground fog hugging the wet earth, and dead leaves tumbling across the
    # ground: both want to warp onto the floor under tilt, not stand up as
    # vertical stickers.
    "mist", "leaves",
    # Noise-trap litter (add_noise_trap): tins, shards, and a board all
    # lie IN the ground plane. (The trap crow is the standing `crow`.)
    "tin_cans", "glass_litter", "loose_plank",
    # The mine art pass (2026-07): old haul rail lies in the floor plane.
    "mine_rail",
    # The cult camp (2026-07): a laid-out bedroll and a felled log seat both
    # lie flat on the ground and warp onto the floor under tilt (the lit
    # `camp_fire` centrepiece is a SOLID volume instead).
    "bedroll", "log_seat",
    # The lost ROAD station (2026-07): painted parking-bay stall lines lie flat
    # on the lot and warp onto the ground under tilt.
    "parking_bay",
))

# Decals that lie flat on a RAISED surface (a ledger open on a desktop): warped
# flat like a floor decal, but lifted to the prop's height (deco kwarg `z`) and
# DEPTH-SORTED with the props by the caller -- so the counter box doesn't paint
# over them and they read as resting ON the desk, not the floor, and not as a
# camera-facing billboard. Skipped in the terrain pass; emitted by render_mixin.
_SURFACE_DECAL_KINDS = frozenset((
    "ledger",
    # A plate + cutlery IS flat: warp it onto the table top (or the floor when
    # not seated) instead of standing a top-down sticker up under tilt.
    "place_setting",
))

# Small props that REST on a tabletop: when one is placed on a furniture
# footprint tile, seat_tabletop_props lifts it onto that surface (a deco `z`)
# instead of leaving it floating at the furniture's base. Curated so structural
# decor on a furniture tile isn't lifted by accident.
_TABLETOP_PROP_KINDS = frozenset((
    "candle", "lantern", "kerosene_lamp", "oil_lamp", "lamp", "ledger",
    "bowl", "cup", "mug", "bottle", "jar", "plate", "radio", "papers",
    "book", "photo", "photo_frame", "tankard", "teapot",
    "wrong_radio", "place_setting",
    # the shop counter's till + its receipt spike, the lodge desk's service
    # bell, and the crayons on Toby's table (tableau-parity pass): all rest ON
    # furniture, seated by seat_tabletop_props.
    "cash_register", "bill_spike", "service_bell", "crayons",
))

# Wall-mounted decorations. Under tilt these are lifted onto the wall face as
# camera-facing billboards (and depth-sorted with the walls) instead of lying
# flat on the floor -- they HANG, they don't sit. _WALL_MOUNT_Z is how far up
# the wall (walls rise to _TILT_WALL_RISE = 26). Pitch 0 draws them flat as
# before (Scene.draw).
_WALL_DECO_KINDS = frozenset((
    "mirror", "photo", "wrong_photo", "missing_flyer", "polaroid_wall",
    "banner", "calendar", "clock", "apology_wall",
    "buck_head", "antler_rack", "mounted_fish", "wrong_taxidermy",
    "chalk_door_wall", "chalkboard", "wall_cross",
    # the Yellow Sign daubed on a wall face (the Sign Chamber apse; the
    # tableau-parity pass) -- the floor `yellow_sign` warps onto the ground.
    "wall_sign",
    # Framed needlework, a varnish-dark portrait, and a larder shelf of
    # preserves: all HANG on the wall face.
    "sampler", "oil_portrait", "preserve_shelf",
    # Things that belong ON a wall, not lying flat on the floor: a cobweb
    # spans a corner; a passing silhouette glides past a window.
    "cobweb", "passing_silhouette",
    # the lodge reception key board + Toby's taped crayon drawings
    # (tableau-parity pass): hung on the wall face.
    "key_rack", "crayon_drawing",
    # The mine art pass (2026-07): shift tallies scratched into the rock face.
    "tally_marks",
))
_WALL_MOUNT_Z = 18


_FLOOR_DECAL_CARD_CACHE = {}        # (id(deco), yaw_bkt, scale_bkt, pitch_bkt)
                                    #     -> pre-warped Surface
# How tightly we quantise yaw/pitch/scale for the cache. Yaw eases by ~0.004
# rad/frame during mouselook, so 0.05 rad (~3 deg) buckets give the cache
# hits during smooth play and only re-warp on real turns. Pitch + scale are
# typically constant in actual play -- the pitch is dev/capture-only and not wired in
# game; scale is fixed at TILT_ZOOM -- so coarse buckets are fine.
_FLOOR_DECAL_YAW_BKT = 0.05
_FLOOR_DECAL_SCALE_BKT = 0.05
# Formless natural decals (foliage clumps, scattered leaves, mist) have no
# meaningful orientation, so warping them with the camera yaw just spins their
# fixed light/shadow as the head turns -- visibly wrong, and the per-turn
# rotate of every one (Brimley has ~100 bushes) was the top cost left in the
# tilted view. These skip the yaw rotate and key WITHOUT yaw: built once and
# only pitch-squashed onto the floor, so they hold still and cost nothing on a
# turn. Directional decals (signs, prints, the Yellow Sign, a dead crow) keep
# the yaw rotate so they stay pinned to the ground as it turns.
_FLOOR_DECAL_YAW_INVARIANT = frozenset({"bush", "mist", "leaves"})


def _draw_floor_decal(surf, camera, deco, woff=(0.0, 0.0)):
    """Render a flat decal to a canvas, then warp it onto the floor plane (same
    rotate+squash as _tilt_warp) and blit at the projected anchor, so a rug or
    bloodstain lies on the ground and turns with the room instead of standing up
    as a billboard. The fill -> rotate -> smoothscale pipeline is CACHED per
    decoration + camera-orientation bucket; the per-frame cost on a cache hit
    is just one project + blit. `woff` is the wrap-clone WORLD offset (added
    before projection so the seam clone lands through the camera, not in
    screen space; DESIGN.md §10)."""
    drawfn = getattr(deco, f"_draw_{deco.kind}", None)
    if drawfn is None:
        return
    spin = deco.kind not in _FLOOR_DECAL_YAW_INVARIANT
    yaw_bkt = round(camera.yaw / _FLOOR_DECAL_YAW_BKT) if spin else 0
    scale_bkt = round(camera.scale / _FLOOR_DECAL_SCALE_BKT)
    pitch_bkt = round(camera.pitch / _FLOOR_DECAL_YAW_BKT)
    key = (id(deco), yaw_bkt, scale_bkt, pitch_bkt)
    scaled = _FLOOR_DECAL_CARD_CACHE.get(key)
    if scaled is None:
        if deco.kind in ("rug", "garden_patch"):
            w = int(deco.kwargs.get("w", 88)); h = int(deco.kwargs.get("h", 60))
            bound = max(w, h) + 18
        else:
            bound = 60
        canvas = pygame.Surface((bound, bound), pygame.SRCALPHA)
        drawfn(canvas, bound // 2, bound // 2)
        rot = (pygame.transform.rotate(canvas, math.degrees(camera.yaw))
               if spin else canvas)
        cp = max(0.05, math.cos(camera.pitch))
        sw = max(1, int(rot.get_width() * camera.scale))
        sh = max(1, int(rot.get_height() * camera.scale * cp))
        scaled = pygame.transform.smoothscale(rot, (sw, sh)).convert_alpha()
        _FLOOR_DECAL_CARD_CACHE[key] = scaled
        # Bound memory: drop the oldest entries when the cache gets fat. A
        # single scene's worth of decals at one yaw bucket is ~100 entries; a
        # few-thousand cap covers head turns + scene changes without leaking.
        if len(_FLOOR_DECAL_CARD_CACHE) > 4096:
            for k_ in list(_FLOOR_DECAL_CARD_CACHE)[:1024]:
                _FLOOR_DECAL_CARD_CACHE.pop(k_, None)
    sw, sh = scaled.get_size()
    # `z` lifts the flat decal onto a raised surface (a ledger on a desktop);
    # 0 keeps it on the floor (rugs, stains).
    zlift = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    sx, sy = camera.project(deco.x + woff[0], deco.y + woff[1], zlift)
    surf.blit(scaled, (sx - sw // 2, sy - sh // 2))


def _draw_water_channel_tilt(surf, camera, deco, woff=(0.0, 0.0)):
    """Draw a water_channel as a projected FLOOR polyline: each waypoint
    (anchor + offset) is Chaikin-smoothed in world space then projected to z=0
    and connected. Lies on the floor + follows the tilt, with no big per-frame
    canvas -- so the thread can span the whole cave. Murky teal to match `~`."""
    path = deco.kwargs.get("path")
    if not path or len(path) < 2:
        return
    raw = [(deco.x + woff[0] + dx, deco.y + woff[1] + dy) for dx, dy in path]
    for _ in range(2):                         # Chaikin smoothing in world space
        sm = [raw[0]]
        for i in range(len(raw) - 1):
            p, q = raw[i], raw[i + 1]
            sm.append((p[0] * 0.75 + q[0] * 0.25, p[1] * 0.75 + q[1] * 0.25))
            sm.append((p[0] * 0.25 + q[0] * 0.75, p[1] * 0.25 + q[1] * 0.75))
        sm.append(raw[-1])
        raw = sm
    pts = [camera.project(wx, wy, 0) for wx, wy in raw]
    pts = [(int(x), int(y)) for x, y in pts]
    Wd = max(3, int(7 * camera.scale))
    pygame.draw.lines(surf, (22, 34, 34), False, pts, Wd + 4)   # soaked halo
    pygame.draw.lines(surf, (30, 48, 46), False, pts, Wd + 1)   # water body
    pygame.draw.lines(surf, (46, 68, 62), False, pts, Wd)
    for p in pts:                                               # round the joints
        pygame.draw.circle(surf, (46, 68, 62), p, max(1, Wd // 2))
    pygame.draw.lines(surf, (74, 98, 90), False, pts, 1)        # cold core
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
           for i in range(len(pts) - 1)]
    total = sum(seg)
    if total > 0:                                               # sheen glints flowing
        for k in range(4):
            f = ((deco.t * 0.06 + k / 4.0) % 1.0) * total
            acc = 0.0
            for i, d in enumerate(seg):
                if acc + d >= f and d > 0:
                    u = (f - acc) / d
                    gx = int(pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u)
                    gy = int(pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u)
                    pygame.draw.circle(surf, (104, 128, 116), (gx, gy), 2)
                    break
                acc += d


def _wall_normal(scene, wx, wy):
    """The inward normal of the wall a decoration hangs on -- the way it FACES,
    forward off the wall into the room. Rooms are scene-sized, so a wall is the
    nearest perimeter; face inward from the closest scene edge."""
    tx, ty = int(wx // TILE), int(wy // TILE)
    W, H = scene.w, scene.h
    opts = [(ty, (0, 1)), (H - 1 - ty, (0, -1)),
            (tx, (1, 0)), (W - 1 - tx, (-1, 0))]
    opts.sort(key=lambda o: o[0])
    return opts[0][1]


def draw_wall_deco(surf, camera, scene, deco, mount_z, woff=(0.0, 0.0)):
    """Draw a wall-hung decoration as a card FIXED to the wall plane: it faces
    forward off the wall and foreshortens / turns as the camera yaws past it --
    it does NOT billboard (follow the camera). The card lies along the wall's
    horizontal axis at `mount_z` up the wall; project both ends of that span,
    then fit + rotate the flat sprite onto the screen span so it reads as part
    of the wall, edge-on (a sliver) when you look along it."""
    nx, ny = _wall_normal(scene, deco.x, deco.y)
    ax, ay = -ny, nx                       # along the wall (perp to the normal)
    half = (70.0 if deco.kind == "chalkboard"
            else 15.0 if deco.kind == "chalk_door_wall" else 11.0)
    bx, by = deco.x + woff[0], deco.y + woff[1]
    p1 = camera.project(bx - ax * half, by - ay * half, mount_z)
    p2 = camera.project(bx + ax * half, by + ay * half, mount_z)
    cx, cy = (p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5
    sw_, sh_ = surf.get_size()
    if cx < -48 or cx > sw_ + 48 or cy < -48 or cy > sh_ + 48:
        return
    width = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    if width < 3:
        return                             # edge-on -> a sliver; skip
    drawfn = getattr(deco, f"_draw_{deco.kind}", deco._draw_unknown)
    C = (56 if deco.kind == "chalkboard"
         else 28 if deco.kind == "chalk_door_wall" else 22)
    canvas = pygame.Surface((C * 2, C * 2), pygame.SRCALPHA)
    drawfn(canvas, C, C)
    h = int(C * 2 * 0.66)                   # card screen height (upright)
    if deco.kind == "chalk_door_wall":     # a door is tall, not a small plaque
        h = int(C * 2 * 0.95)
    if deco.kind == "chalkboard":          # wide board: square card -> art keeps
        h = max(3, int(width))             # its drawn (wide-but-short) proportions
    dx_, dy_ = p2[0] - p1[0], p2[1] - p1[1]
    if abs(dy_) <= abs(dx_):
        # N/S wall: the span is screen-horizontal, so a rotated rectangle is
        # exact (the card's height axis stays vertical). Unchanged path.
        card = pygame.transform.scale(canvas, (max(3, int(width)), max(3, h)))
        ang = math.degrees(math.atan2(-dy_, dx_))
        if abs(ang) > 0.5:
            card = pygame.transform.rotate(card, ang)
        surf.blit(card, (int(cx) - card.get_width() // 2,
                         int(cy) - card.get_height() // 2))
        return
    # E/W wall: the span projects near-vertical, but the card's HEIGHT must
    # stay the world vertical (screen-vertical) -- rotating the rectangle laid
    # the art down flat along the wall foot. The true projected shape is a
    # parallelogram whose vertical edges stay vertical, so draw it as 1px
    # vertical strips lerped along the span (an exact affine fit). Its screen
    # WIDTH is the span's horizontal extent: zero at yaw 0 (the face is
    # edge-on; honestly invisible) and opening up as the camera yaws past.
    Wpx = int(abs(dx_))
    if Wpx < 3:
        return                             # face edge-on at this yaw
    card = pygame.transform.scale(canvas, (Wpx, max(3, h)))
    for i in range(Wpx):
        t = i / max(1, Wpx - 1)
        sxp = p1[0] + dx_ * t
        syp = p1[1] + dy_ * t
        surf.blit(card, (int(sxp), int(syp - h / 2)),
                  area=pygame.Rect(i, 0, 1, card.get_height()))


def _draw_window_pane(surf, camera, wx, wy, ndx, ndy, broken=False,
                      face_off=None, daylight=False):
    """A glazed pane set into one wall face: wood frame, glass, a lighter
    core and a muntin cross. `(ndx, ndy)` is the exposed face direction.
    `face_off` is the distance from the tile centre to that face's true
    plane (a thin-slab wall's face is NOT the tile edge); None keeps the
    full-tile face. `daylight` swaps the warm lit-from-within amber for flat
    overcast daylight (interior scenes look OUT at the grey sky; the warm
    glass belongs on the town's facades, DESIGN.md §6). `broken` (a thrown
    stone, TODO #5) swaps the glass for a dark hole with shard teeth left in
    the frame -- the light is out for the run."""
    hw = TILE / 2
    pv = (-ndy, ndx)                 # along-wall axis on this face
    ph = hw * 0.60                   # half pane width
    z0, z1 = 7.0, 19.0
    off = hw * 0.99 if face_off is None else face_off

    def Q(u, z):
        return camera.project(wx + ndx * off + pv[0] * u,
                              wy + ndy * off + pv[1] * u, z)
    frame = [Q(-ph - 2, z0 - 2), Q(ph + 2, z0 - 2), Q(ph + 2, z1 + 2), Q(-ph - 2, z1 + 2)]
    glass = [Q(-ph, z0), Q(ph, z0), Q(ph, z1), Q(-ph, z1)]
    pygame.draw.polygon(surf, (96, 70, 50), frame)
    pygame.draw.polygon(surf, (60, 40, 25), frame, 1)
    if broken:
        pygame.draw.polygon(surf, (14, 12, 17), glass)             # the dark hole
        for u0, u1, zt in ((-ph, -ph * 0.4, z1 - 4), (ph * 0.2, ph, z1 - 5),
                           (-ph * 0.5, ph * 0.1, z0 + 4)):
            pygame.draw.polygon(surf, (108, 96, 62),               # shard teeth
                                [Q(u0, z1 if zt > (z0 + z1) / 2 else z0),
                                 Q(u1, z1 if zt > (z0 + z1) / 2 else z0),
                                 Q((u0 + u1) / 2, zt)])
        pygame.draw.polygon(surf, (60, 40, 25), glass, 1)
        return
    core = [Q(-ph * 0.5, z0 + 3), Q(ph * 0.5, z0 + 3),
            Q(ph * 0.5, z1 - 3), Q(-ph * 0.5, z1 - 3)]
    if daylight:
        pygame.draw.polygon(surf, (96, 100, 94), glass)
        pygame.draw.polygon(surf, (124, 128, 120), core)
    else:
        pygame.draw.polygon(surf, (138, 104, 50), glass)
        pygame.draw.polygon(surf, (170, 138, 78), core)
    pygame.draw.line(surf, (74, 54, 34), Q(0, z0), Q(0, z1), 1)               # mullion
    pygame.draw.line(surf, (74, 54, 34), Q(-ph, (z0 + z1) / 2), Q(ph, (z0 + z1) / 2), 1)
    pygame.draw.polygon(surf, (60, 40, 25), glass, 1)


def _tilt_window_box(surf, camera, scene, tx, ty):
    """A window is a SOLID wall tile, so it extrudes as a wall box -- the
    wall's slab footprint in a slab scene (_gap_slab), full-tile elsewhere. A
    pane is then set into each camera-facing exposed face ON that face's true
    plane (dark + shard-toothed once a thrown stone has broken it --
    scene._broken_windows). Glazing reads by scene: an INTERIOR scene's
    windows hold flat overcast DAYLIGHT (the dim room looks out at the grey
    sky); an exterior facade keeps the warm lit-from-within glass (the town
    keeping its lights on, DESIGN.md §6)."""
    wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
    hw = TILE / 2
    wtx = tx % scene.w if scene.wrap_x else tx
    wty = ty % scene.h if scene.wrap_y else ty
    bands = _gap_slab(scene, wtx, wty)
    if bands:
        face_col, top_col = _tilt_wall_tint(scene, tx, ty)
        tint = _wall_tint_for(scene)
        fc = _tint_col(face_col if face_col else _WALL_FACE, tint)
        tc = _tint_col(top_col if top_col else _WALL_TOP,
                       _wall_top_tint_for(scene))
        for band in bands:
            _extrude_box(surf, camera, scene, tx, ty, 0, _TILT_WALL_RISE,
                         neigh=_WALL_CHARS, face_col=fc, top_col=tc,
                         foot=band)
    else:
        _tilt_wall_box(surf, camera, scene, tx, ty)
    broken = (wtx, wty) in getattr(scene, "_broken_windows", ())
    try:
        from systems.config import SEAMLESS_WORLD_SCENES as _SWS
        daylight = getattr(scene, "key", None) not in _SWS
    except Exception:
        daylight = False
    cd = camera.depth(wx, wy, _TILT_WALL_RISE / 2)
    for ndx, ndy in ((0, 1), (0, -1), (-1, 0), (1, 0)):
        if _is_wall(scene, tx + ndx, ty + ndy):
            continue                                     # buried face
        if camera.depth(wx + ndx * hw, wy + ndy * hw, _TILT_WALL_RISE / 2) <= cd:
            continue                                     # faces away from camera
        face_off = None
        if bands:
            b = bands[0]
            if ndy > 0:
                face_off = (b[3] - hw) + 0.5
            elif ndy < 0:
                face_off = (hw - b[1]) + 0.5
            elif ndx > 0:
                face_off = (b[2] - hw) + 0.5
            else:
                face_off = (hw - b[0]) + 0.5
        _draw_window_pane(surf, camera, wx, wy, ndx, ndy, broken=broken,
                          face_off=face_off, daylight=daylight)


_WALL_BOX_CACHE = {}
_WALL_BOX_ORDER = []
_WALL_BOX_CAP = 2200


def _tilt_wall_box_cached(surf, camera, scene, tx, ty):
    """Plain wall tiles are static geometry (no animation), and like the trees
    their box's shape depends only on the camera angle + which neighbours are
    walls -- never on where the camera pans. So render each wall tile's box
    once per (scene, tile, angle) into a card and blit it at the projected tile
    centre. The bulk of the town's ~640 wall tiles become blits while panning.
    Yaw is BUCKETED at 0.04 rad (~2.3 deg): a continuous head-turn used to
    mint a fresh key every frame (a full-visible-wall rebuild per frame, the
    dominant look-around cost); inside a bucket the shape error is ~1px on a
    card this size, invisible mid-swing."""
    key = (scene.key, tx, ty, int(camera.yaw / 0.04),
           round(camera.pitch, 2), round(camera.scale, 2))
    entry = _WALL_BOX_CACHE.get(key)
    if entry is None:
        entry = _build_wall_box_card(camera, scene, tx, ty)
        _WALL_BOX_CACHE[key] = entry
        _WALL_BOX_ORDER.append(key)
        if len(_WALL_BOX_ORDER) > _WALL_BOX_CAP:
            _WALL_BOX_CACHE.pop(_WALL_BOX_ORDER.pop(0), None)
    card, ax, ay = entry
    if card is not None:
        bx, by = camera.project(tx * TILE + TILE / 2, ty * TILE + TILE / 2, 0)
        surf.blit(card, (bx - ax, by - ay))


def _build_wall_box_card(camera, scene, tx, ty):
    """Cache-miss path: render one wall tile's box to a tight SRCALPHA card via
    a throwaway camera at the same angle, pinned at the tile centre. The tight
    rect is ANALYTIC -- the drawn box lies inside the projected hull of the
    tile's eight extruded corners -- because get_bounding_rect's full-pixel
    scan was ~70% of every rebuild (and a head-turn rebuilds every visible
    wall)."""
    from rendering.camera import Camera
    PAD = 90
    tmp = pygame.Surface((PAD * 2, PAD * 2), pygame.SRCALPHA)
    anchor = (PAD, int(PAD * 1.3))
    tcam = Camera(cam_x=tx * TILE + TILE / 2, cam_y=ty * TILE + TILE / 2,
                  pitch=camera.pitch, yaw=camera.yaw,
                  scale=camera.scale, origin=anchor)
    _tilt_wall_box(tmp, tcam, scene, tx, ty)
    xs = []
    ys = []
    for cxw in (tx * TILE, tx * TILE + TILE):
        for cyw in (ty * TILE, ty * TILE + TILE):
            for z in (0, _TILT_WALL_RISE):
                sxp, syp = tcam.project(cxw, cyw, z)
                xs.append(sxp)
                ys.append(syp)
    rx0 = max(0, min(xs) - 2)
    ry0 = max(0, min(ys) - 2)
    rx1 = min(PAD * 2, max(xs) + 3)
    ry1 = min(PAD * 2, max(ys) + 3)
    if rx1 - rx0 <= 0 or ry1 - ry0 <= 0:
        return (None, 0, 0)
    rect = pygame.Rect(rx0, ry0, rx1 - rx0, ry1 - ry0)
    return (tmp.subsurface(rect).copy().convert_alpha(), anchor[0] - rect.x, anchor[1] - rect.y)


def _tilt_tile_box(surf, camera, scene, tx, ty):
    """Dispatch a tile to its tilt solid: a wall-mass box, a doorway (lintel +
    swung leaf), a window (box + lit pane), a 3D tree (trunk + canopy bodies
    of revolution) or a 3D corn cluster (per-stalk projected lines). Trees /
    corn project through the camera so they anchor in the scene; the legacy
    rotated-billboard standee survives as a fallback for any future kind."""
    wtx = tx % scene.w if scene.wrap_x else tx
    wty = scene.render_row(ty)
    ch = (scene.objects[wty][wtx]
          if 0 <= wty < scene.h and 0 <= wtx < scene.w else "")
    if (ch in (".", " ") and 0 <= wty < scene.h and 0 <= wtx < scene.w
            and scene.floor[wty][wtx] == ":"):
        # A bare cover-floor tile: the tall-grass tuft (concealment made
        # visible; mirrors the wall-scan's append condition exactly).
        _tilt_grass_solid(surf, camera, scene, tx, ty,
                          far=_tilt_lod_far(camera, tx, ty))
        return
    if ch in _TILT_BILLBOARD_CHARS:
        kind = OBJECT_DEFS.get(ch, {}).get("kind")
        if kind == "tree":
            _tilt_tree_solid(surf, camera, scene, tx, ty, ch,
                             far=_tilt_lod_far(camera, tx, ty))
        elif kind == "cornstalk":
            _tilt_corn_solid(surf, camera, scene, tx, ty, ch,
                             far=_tilt_lod_far(camera, tx, ty))
        else:
            _tilt_standee(surf, camera, scene, tx, ty, ch)
    elif ch in _COUNTER_CHARS:
        _tilt_counter_box(surf, camera, scene, tx, ty)
    elif ch in _RACK_CHARS:
        _tilt_rack_box(surf, camera, scene, tx, ty)
    elif ch in _DOOR_CHARS:
        _tilt_door_box(surf, camera, scene, tx, ty)
    elif ch in _WINDOW_CHARS:
        _tilt_window_box(surf, camera, scene, tx, ty)
    else:
        _tilt_wall_box_cached(surf, camera, scene, tx, ty)


# Spatial bucket size for the decoration cull (Move 1+2 of the perf strategy:
# stop drawing what the camera can't see). 16 tiles = 512 px gives Brimley
# (100x100 wrap_x+wrap_y) ~7x7 chunks of ~12 props each. The camera's visible
# rect typically hits ~4x3 chunks per wrap offset, so 9-offset toroidal draws
# touch ~100-200 props instead of the ~5,500 the naive loop produces.
_DECO_CHUNK_TILES = 16
_DECO_CHUNK_PX = _DECO_CHUNK_TILES * TILE
# World-px margin added to the visible rect when picking chunks, so a tall
# standee whose BASE sits just outside the visible square but whose TOP
# pokes into view still gets considered. Trees rise ~60 px on the card; at
# scale 0.72 and sin(55 deg)=0.82 that's ~35 screen px, well under a full
# chunk -- 1 tile of world margin is enough.
_DECO_TALL_MARGIN = TILE


def _deco_index(scene):
    """Categorise scene.decorations into the four downstream paths and bucket
    the per-frame-culled subset into a spatial grid. Lazy + cached on the
    scene; rebuilt when scene.decorations changes length (covers world rot /
    runtime additions). Pure data, no draw."""
    cache = getattr(scene, "_deco_index_cache", None)
    if cache is not None and cache["len"] == len(scene.decorations):
        return cache
    from rendering.furniture import is_solid_furniture
    from rendering.props import is_solid_prop
    solid_decos = []
    solid_chunks = {}                # spatial bucket for the solid-prop cull
    wall_decos = []
    water_channels = []
    chunks = {}
    for d in scene.decorations:
        if is_solid_furniture(d.kind) or is_solid_prop(d.kind):
            solid_decos.append(d)
            cx = int(d.x // _DECO_CHUNK_PX)
            cy = int(d.y // _DECO_CHUNK_PX)
            solid_chunks.setdefault((cx, cy), []).append(d)
            continue
        if d.kind in _WALL_DECO_KINDS:
            wall_decos.append(d)
            continue
        if d.kind in _SURFACE_DECAL_KINDS or \
                float(getattr(d, "kwargs", {}).get("z", 0.0)) > 0:
            continue                 # seated on a surface; depth-sorted upstream
        if d.kind == "water_channel":
            water_channels.append(d)
            continue
        cx = int(d.x // _DECO_CHUNK_PX)
        cy = int(d.y // _DECO_CHUNK_PX)
        chunks.setdefault((cx, cy), []).append(d)
    cache = {"solid": solid_decos, "solid_chunks": solid_chunks,
             "wall": wall_decos, "water": water_channels,
             "chunks": chunks, "len": len(scene.decorations)}
    scene._deco_index_cache = cache
    return cache


_NEIGHBOR_SCENE_CACHE = {}


def _neighbor_scene(key):
    """Built neighbor scene for the seam strips, cached by key. The strips
    sample only the neighbor's static terrain (its `objects` grid + wrap flags)
    every frame, but load_scene() rebuilds the whole scene from scratch -- so
    calling it per frame re-ran the neighbor's entire builder (e.g. Brimley +
    its forest scatter) ~twice a frame. Terrain is deterministic per key and
    the strips never mutate it, so one cached build per key is correct."""
    sc = _NEIGHBOR_SCENE_CACHE.get(key)
    if sc is None:
        from scenes import load_scene
        sc = load_scene(key)
        _NEIGHBOR_SCENE_CACHE[key] = sc
    return sc


def _collect_neighbor_solids(scene, camera, x0, y0, x1, y1):
    """Walk the visible tile window's OUT-OF-BOUNDS region for each seamless
    neighbor and collect the wall-class tiles to be drawn as standing boxes
    later (in render_mixin's depth-sorted pass). Returns a list of
    `(neighbor_scene, ntx, nty, host_world_x, host_world_y, sat_camera)`.

    The satellite camera mirrors the host camera shifted by the neighbor's
    offset; projecting a neighbor world point through it lands at the same
    screen pixel a host world point at the equivalent seam location would.
    The depth sort still uses the host camera + host world coords, so a
    neighbor wall in front of an actor sorts correctly."""
    from rendering.world_neighbors import get_neighbors
    neighbors = get_neighbors(scene)
    if not neighbors:
        return []
    from scenes import load_scene
    from rendering.camera import Camera
    H, W = scene.h, scene.w
    out = []
    for n in neighbors:
        try:
            tgt = _neighbor_scene(n.target_key)
        except Exception:
            continue
        sat_cam = Camera(cam_x=camera.cam_x + n.offset_dx,
                         cam_y=camera.cam_y + n.offset_dy,
                         pitch=camera.pitch, yaw=camera.yaw,
                         scale=camera.scale, origin=camera.origin)
        tw, th = tgt.w, tgt.h
        for ty in range(y0, y1):
            if 0 <= ty < H:
                continue
            for tx in range(x0, x1):
                if 0 <= tx < W:
                    continue
                ntx = int((tx * TILE + TILE // 2 + n.offset_dx) // TILE)
                nty = int((ty * TILE + TILE // 2 + n.offset_dy) // TILE)
                if tgt.wrap_x: ntx %= tw
                if tgt.wrap_y: nty %= th
                if not (0 <= ntx < tw and 0 <= nty < th):
                    continue
                ch = tgt.objects[nty][ntx]
                if (ch in _WALL_CHARS or ch in _DOOR_CHARS
                        or ch in _WINDOW_CHARS
                        or ch in _TILT_BILLBOARD_CHARS
                        or ch in _COUNTER_CHARS
                        or ch in _RACK_CHARS):
                    out.append((tgt, ntx, nty,
                                tx * TILE + TILE / 2,
                                ty * TILE + TILE / 2,
                                sat_cam))
    return out


def _draw_neighbor_strips(flat, scene, wx0, wy0, x0, y0, x1, y1):
    """Paint the seamless neighbor scenes' floor tiles into the host flat for
    every (tx, ty) in the visible tile window that sits OUTSIDE the host
    scene's tile bounds. Each neighbor knows its world-coord offset (set up
    at scene-load time by rendering.world_neighbors); we translate the host
    tile coord into the neighbor's grid and draw the neighbor's floor char
    using the SAME cached path draw_scene_terrain uses, so the strip blends
    visually with the host's floor pattern. Terrain only at this phase --
    walls, decorations, actors come later."""
    from rendering.world_neighbors import get_neighbors
    neighbors = get_neighbors(scene)
    if not neighbors:
        return
    from scenes import load_scene
    H, W = scene.h, scene.w
    for n in neighbors:
        try:
            tgt = _neighbor_scene(n.target_key)
        except Exception:
            continue
        # The target tile that a host (tx, ty) tile maps to.
        # host world point = (tx*TILE + TILE/2, ty*TILE + TILE/2)
        # target world point = host world point + (offset_dx, offset_dy)
        tw, th = tgt.w, tgt.h
        for ty in range(y0, y1):
            ty_in = 0 <= ty < H
            for tx in range(x0, x1):
                # Skip only tiles the HOST actually renders (both coords in
                # bounds). The old per-axis skips dropped every N/S and E/W
                # edge strip -- only diagonal corners ever painted, so the
                # seamless seam never actually showed the neighbor.
                if ty_in and 0 <= tx < W:
                    continue
                nx_px = tx * TILE + TILE // 2 + n.offset_dx
                ny_px = ty * TILE + TILE // 2 + n.offset_dy
                ntx = int(nx_px // TILE)
                nty = int(ny_px // TILE)
                if tgt.wrap_x:
                    ntx %= tw
                if tgt.wrap_y:
                    nty %= th
                if not (0 <= ntx < tw and 0 <= nty < th):
                    continue                 # outside the neighbor too
                ch = tgt.floor[nty][ntx]
                rx = tx * TILE - wx0
                ry = ty * TILE - wy0
                if ch in _ANIM_FLOOR:
                    draw_floor(flat, ch, rx, ry, ntx, nty)
                    continue
                key = (ch, ntx, nty)
                tile = _FLOOR_CACHE.get(key)
                if tile is None:
                    tile = pygame.Surface((TILE, TILE)).convert()
                    draw_floor(tile, ch, 0, 0, ntx, nty)
                    _FLOOR_CACHE[key] = tile
                flat.blit(tile, (rx, ry))


def draw_terrain_tilted(surf, scene, camera, sight=None):
    """Floor warp + flat decals for the oblique camera. Skybox is the caller's
    job (drawn first); actors are drawn after by the game, already projected
    through the same camera so they stand on this floor.

    The upright occluders -- WALL tiles and SOLID furniture/props -- are NOT
    drawn here. They are RETURNED as `(wall_tiles, solid_decos)` so the caller
    can depth-interleave them with the actors and fade each per-actor
    (DESIGN.md §10: every actor + prop sorts against every wall by
    Camera.depth, and a wall fades for whichever actor it actually covers, not
    just the player). Only the flat layer -- the warped floor raster and the
    ground decals / billboard decorations that lie on or rise from it -- is
    drawn now (it can never occlude an actor).

    `sight` is the optional Phase 4 blind-spot factor fn(wx, wy) -> 0..1
    (rendering/sight.py). When given, decorations flagged `_sight_gated`
    (the world rot rot) only draw where the player actually looks -- the
    world's rot reveals on a peek and re-hides off-camera."""
    cx, cy = camera.cam_x, camera.cam_y
    half = _tilt_window_half(camera)
    span = int(half * 2)
    wx0, wy0 = cx - half, cy - half
    x0 = int(math.floor(wx0 / TILE)); y0 = int(math.floor(wy0 / TILE))
    x1 = int(math.ceil((wx0 + span) / TILE)); y1 = int(math.ceil((wy0 + span) / TILE))
    # The warped floor is cached (see _TILT_FLOOR_CACHE). The build is
    # anchored to a TILE-quantized camera centre: the warp is AFFINE
    # (rotate + scale), so panning within a tile reuses the cached
    # surface blitted at the projected offset instead of re-rastering +
    # re-warping the whole window every moving frame (that rebuild was
    # the single biggest walking cost). One extra TILE of margin covers
    # the largest sub-tile shift. x0..y1 / wx0,wy0 are still computed
    # every frame from the TRUE camera -- the wall + neighbor passes
    # below need them.
    qx = math.floor(cx / TILE) * TILE
    qy = math.floor(cy / TILE) * TILE
    fkey = (id(scene), getattr(scene, "key", None), scene.w, scene.h,
            qx, qy, round(camera.yaw, 4),
            round(camera.pitch, 4), round(camera.scale, 4))
    _fc = _TILT_FLOOR_CACHE
    if _fc["key"] == fkey:
        # A soft (half-res) floor whose key held still: the look has
        # settled -- re-warp SHARP once from the cached flat raster (no
        # re-raster; only the transforms rerun).
        if _fc.get("soft") and _fc.get("flat") is not None:
            _fc["surf"] = _tilt_warp(_fc["flat"], camera)
            _fc["soft"] = False
        warped = _fc["surf"]
    else:
        # Only the yaw moved since the last build = a look in progress:
        # warp at half res (dynamic resolution; motion hides it). Any
        # other change (pan across a tile, pitch/scale ease) builds
        # sharp as before.
        pk = _fc["key"]
        fast_look = (pk is not None and pk[:6] == fkey[:6]
                     and pk[7:] == fkey[7:] and pk[6] != fkey[6])
        half_b = half + TILE                 # margin for the sub-tile shift
        span_b = int(half_b * 2)
        bx0, by0 = qx - half_b, qy - half_b
        tx0 = int(math.floor(bx0 / TILE)); ty0 = int(math.floor(by0 / TILE))
        tx1 = int(math.ceil((bx0 + span_b) / TILE))
        ty1 = int(math.ceil((by0 + span_b) / TILE))
        # Reuse the flat scratch between rebuilds -- allocating a fresh
        # span x span surface (several MB) every rebuilt frame was churn.
        flat = _fc.get("flat")
        if flat is None or flat.get_size() != (span_b, span_b):
            flat = pygame.Surface((span_b, span_b))
            _fc["flat"] = flat
        flat.fill((10, 10, 14))
        if _tilt_use_fullmap(scene):
            # Big wrap scene: blit the window out of the whole-map bake (a few
            # wrap-aware blits) and redraw only the animated water on top,
            # instead of rastering ~6000 tiles every frame.
            full, water = _tilt_fullmap(scene)
            _blit_window_wrapped(flat, full, bx0, by0,
                                 scene.wrap_x, scene.wrap_y)
            _overlay_anim_water(flat, scene, water, bx0, by0, span_b)
            # A one-axis wrap scene (the Yard's E-W loop) still has off-map
            # past its non-wrapped edges; compose that edge too.
            if not (scene.wrap_x and scene.wrap_y):
                _void_surround_pass(flat, scene, bx0, by0,
                                    tx0, ty0, tx1, ty1)
        else:
            draw_scene_terrain(flat, scene, bx0, by0, tx0, ty0, tx1, ty1,
                               skip_billboard=True, skip_roofs=True)
            _void_surround_pass(flat, scene, bx0, by0, tx0, ty0, tx1, ty1)
            # Seamless-world neighbor strips: where the visible window extends
            # past a non-wrap host's bounds AND a neighbor exists there
            # (per world_neighbors), paint the neighbor scene's floor content
            # OVER the rim fade -- real world beyond the seam. Elsewhere the
            # fade stays: ground falling away into the dark.
            if not (scene.wrap_x or scene.wrap_y):
                _draw_neighbor_strips(flat, scene, bx0, by0,
                                      tx0, ty0, tx1, ty1)
        warped = _tilt_warp(flat, camera, fast=fast_look)
        _fc["key"] = fkey
        _fc["surf"] = warped
        _fc["soft"] = fast_look
    # Blit so the cached surface's centre (world point (qx, qy)) lands at
    # its CURRENT projection -- the affine shift that makes the tile-
    # anchored build valid for every sub-tile camera position.
    px, py = camera.project(qx, qy, 0)
    surf.blit(warped, (px - warped.get_width() // 2,
                       py - warped.get_height() // 2))
    # Collect the visible wall tiles (returned for the unified depth pass; the
    # caller sorts + fades them). Wrap-aware: tx/ty may sit outside [0,W) for a
    # toroidal scene and the box projects at the un-wrapped world position.
    # The scan walks every tile in the window (~6000 on Brimley) but its result
    # only changes when the TILE window shifts (sub-tile camera pans land in
    # the same window), so it's cached on the window. The billboard cull keys
    # on the camera's tile too -- a sub-tile-stale fog boundary is invisible.
    W, H = scene.w, scene.h
    wkey = (x0, y0, x1, y1,
            int(camera.cam_x // TILE), int(camera.cam_y // TILE))
    _wc = _TILT_WALL_SCAN_CACHE
    if _wc["key"] == wkey and _wc["scene"] is scene:
        walls = _wc["walls"]
    else:
        walls = []
        # Corn now renders as per-tile 3D stalks (_tilt_corn_solid), so each
        # cornstalk tile depth-sorts on its own; the legacy card-merging LOD is
        # bypassed (its anchors-and-suppressed map is unused under the 3D path).
        for ty in range(y0, y1):
            wty = scene.render_row(ty)
            if not (0 <= wty < H):
                continue
            for tx in range(x0, x1):
                wtx = tx % W if scene.wrap_x else tx
                if not (0 <= wtx < W):
                    continue
                ch = scene.objects[wty][wtx]
                if (ch in _WALL_CHARS or ch in _DOOR_CHARS
                        or ch in _WINDOW_CHARS
                        or ch in _TILT_BILLBOARD_CHARS
                        or ch in _COUNTER_CHARS
                        or ch in _RACK_CHARS):
                    if ch in _TILT_BILLBOARD_CHARS:
                        dx = (tx * TILE + 16) - camera.cam_x
                        dy = (ty * TILE + 16) - camera.cam_y
                        if dx * dx + dy * dy > _TILT_BILLBOARD_CULL2:
                            continue        # far treeline -> lost in the fog
                    walls.append((tx, ty))
                elif ch in (".", " ") and scene.floor[wty][wtx] == ":":
                    # Bare cover floor: the tall-grass tuft joins the
                    # depth-sorted set so the player wades INTO it (the
                    # stealth visibility fix; _tilt_tile_box dispatches it).
                    dx = (tx * TILE + 16) - camera.cam_x
                    dy = (ty * TILE + 16) - camera.cam_y
                    if dx * dx + dy * dy <= _TILT_BILLBOARD_CULL2:
                        walls.append((tx, ty))
        _wc["key"] = wkey
        _wc["walls"] = walls
        _wc["scene"] = scene
    # Decorations. Ground decals (rugs, stains, blood) stay flat on the warped
    # floor; non-solid billboards rise from it -- both drawn now, wrap-cloned
    # across the seam THROUGH the projection (DESIGN.md §10) so a torus
    # scene's decor doesn't tear or pop at the fold under tilt/yaw. Curated
    # upright furniture/props are SOLID occluders -> returned for the caller.
    from rendering.furniture import is_solid_furniture
    from rendering.props import is_solid_prop
    from rendering.solids import draw_with_alpha
    world_w, world_h = W * TILE, H * TILE
    offsets = [(0.0, 0.0)]
    if scene.wrap_x:
        offsets += [(-world_w, 0.0), (world_w, 0.0)]
    if scene.wrap_y:
        offsets += [(0.0, -world_h), (0.0, world_h)]
    if scene.wrap_x and scene.wrap_y:
        offsets += [(-world_w, -world_h), (-world_w, world_h),
                    (world_w, -world_h), (world_w, world_h)]
    solid_decos = []
    sw, sh = surf.get_size()
    # Cull box for decoration clones. Generous on the BOTTOM so a tall standee
    # whose ground point sits just off the lower edge still draws (it rises UP
    # into view under tilt); modest on the other sides. Floor decals lie at the
    # ground point, so the side/top margins cover them too. This is the big
    # toroidal-scene win: a wrap_x+wrap_y scene (Brimley) clones every one of
    # its ~600 decorations 9x, and almost all clones -- plus most base decos --
    # are nowhere near the view, yet every one used to be drawn every frame.
    MX, MTOP, MBOT = 120, 110, 240
    # Pull the cached categorisation + spatial bucket. _deco_index is O(N) on
    # cache miss (scene change / decoration added) and O(1) otherwise.
    idx = _deco_index(scene)
    solid_decos.extend(idx["solid"])
    wall_decos = list(idx["wall"])
    # Water channels are projected polylines, not per-frame culled here -- a
    # toroidal scene's road can run the full world axis; let the polyline
    # clipper handle it.
    for d in idx["water"]:
        for woff in offsets:
            _draw_water_channel_tilt(surf, camera, d, woff)
    # Bucket-cull the rest. For each wrap-clone offset, take the camera's
    # visible world rect (with a 1-tile tall-prop margin), find the chunks it
    # spans, and only iterate THOSE chunks. Brimley used to project all ~5,500
    # clones each frame; this typically projects ~150-300.
    chunks = idx["chunks"]
    half = _tilt_window_half(camera) + _DECO_TALL_MARGIN
    vx0 = camera.cam_x - half
    vy0 = camera.cam_y - half
    vx1 = camera.cam_x + half
    vy1 = camera.cam_y + half
    for woff in offsets:
        # The prop is drawn at world (d.x + woff). For it to appear in the
        # visible rect, d.x must be in [vx0 - woff_x, vx1 - woff_x].
        cx0 = int((vx0 - woff[0]) // _DECO_CHUNK_PX)
        cy0 = int((vy0 - woff[1]) // _DECO_CHUNK_PX)
        cx1 = int((vx1 - woff[0]) // _DECO_CHUNK_PX) + 1
        cy1 = int((vy1 - woff[1]) // _DECO_CHUNK_PX) + 1
        for cy in range(cy0, cy1):
            for cx in range(cx0, cx1):
                bucket = chunks.get((cx, cy))
                if not bucket:
                    continue
                for d in bucket:
                    a = 255
                    if sight is not None and getattr(d, "_sight_gated", False):
                        f = sight(d.x, d.y)
                        if f <= 0.03:
                            continue
                        a = 255 if f >= 0.99 else int(255 * f)
                    psx, psy = camera.project(d.x + woff[0], d.y + woff[1])
                    if not (-MX <= psx <= sw + MX
                            and -MTOP <= psy <= sh + MBOT):
                        continue                  # tight screen-px cull
                    # `a` < 255 only for sight-gated rot decals fading at the
                    # cone lip; bound their scratch composite near the deco.
                    drect = (None if a >= 255
                             else (psx - 140, psy - 180, 280, 300))
                    if d.kind in _FLOOR_DECAL_KINDS:
                        draw_with_alpha(surf, a, lambda s, d=d, woff=woff:
                                        _draw_floor_decal(s, camera, d, woff),
                                        rect=drect)
                    else:
                        draw_with_alpha(surf, a, lambda s, d=d, woff=woff:
                                        d.draw(s, 0, 0, camera,
                                               wox=woff[0], woy=woff[1]),
                                        rect=drect)
    # Neighbor walls/standees for the seamless strip. Same Phase 2 deferral:
    # wrap hosts get no strip yet. Returned as a parallel list so render_mixin
    # can dispatch each through a satellite camera while still depth-sorting
    # against the host actors via host-frame world coords.
    neighbor_solids = []
    if not (scene.wrap_x or scene.wrap_y):
        neighbor_solids = _collect_neighbor_solids(scene, camera, x0, y0, x1, y1)
    return walls, solid_decos, wall_decos, neighbor_solids


def draw_scene_doors(surf, scene, cam_x, cam_y, x0, y0, x1, y1):
    """Late pass: the swung door leaves, drawn unconfined so each spills
    out of its tile into the room. Called after terrain + decorations
    and before entities, so a leaf sits over the floor but under anyone
    walking through the doorway. Cave-mouth scenes hang no leaves (a
    mine adit has no door)."""
    if getattr(scene, "door_style", "wood") == "cave":
        return
    W, H = scene.w, scene.h
    wx, wy = scene.wrap_x, scene.wrap_y
    for ty in range(y0, y1):
        wty = ty % H if wy else ty
        if not (0 <= wty < H):
            continue
        for tx in range(x0, x1):
            wtx = tx % W if wx else tx
            if not (0 <= wtx < W):
                continue
            ch = scene.objects[wty][wtx]
            if ch not in _DOOR_CHARS:
                continue
            seed = (tx * 73856093) ^ (ty * 19349663)
            _draw_door_leaf(surf, tx * TILE - cam_x, ty * TILE - cam_y,
                            _door_room_dir(scene, tx, ty), seed)


# ---- Screen-space film grade (grain + vignette + desaturate + tint) ----
# A whole-frame pass that fuses the image into one grimy film look --
# the thing hand-recoloring tiles can't do. Applied to the finished
# frame by the game each draw, and by the offline renderer.
_GRAIN_TILE = None
_VIGNETTE_CACHE = {}
_GRADE_TINT = (16, 20, 22)
_TINT_CACHE = {}     # static full-frame tint fill, per buffer size

# The desaturation half-res smoothscale+grayscale+upscale is the single most
# expensive per-frame op in the live grade. The grey is only ever blended back
# at ~32% alpha, so a one-frame-stale grey is imperceptible: refresh it every
# GRADE_DESAT_EVERY frames and reuse the cached surface between. Only the live
# game passes `frame` (its frame counter); offline tools omit it and recompute
# every call, so single-shot composites are byte-identical.
GRADE_DESAT_EVERY = 2
_GREY_CACHE = {"frame": None, "size": None, "surf": None}


def _grain_tile():
    global _GRAIN_TILE
    if _GRAIN_TILE is None:
        size = 256
        g = pygame.Surface((size, size), pygame.SRCALPHA)
        rng = random.Random(99)
        for _ in range((size * size) // 5):
            gx = rng.randint(0, size - 1)
            gy = rng.randint(0, size - 1)
            v = rng.randint(0, 255)
            if v < 128:
                g.set_at((gx, gy), (0, 0, 0, 18 if v < 40 else 9))
            else:
                g.set_at((gx, gy), (255, 255, 255, 13 if v > 220 else 6))
        _GRAIN_TILE = g
    return _GRAIN_TILE


def _vignette(w, h):
    v = _VIGNETTE_CACHE.get((w, h))
    if v is None:
        base = 192
        s = pygame.Surface((base, base), pygame.SRCALPHA)
        cx = cy = base / 2.0
        maxd = (cx * cx + cy * cy) ** 0.5
        for yy in range(base):
            for xx in range(base):
                d = (((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5) / maxd
                a = int(max(0.0, d - 0.44) / 0.56 * 140)
                if a:
                    s.set_at((xx, yy), (0, 0, 0, min(140, a)))
        v = pygame.transform.smoothscale(s, (w, h))
        _VIGNETTE_CACHE[(w, h)] = v
    return v


def apply_grade(surf, t=0.0, desat=82, frame=None):
    """Grade a finished frame in place: partial desaturation, a cool
    tint, a radial vignette, and animated film grain.

    `frame` (live game only) lets the costly desaturation be refreshed every
    GRADE_DESAT_EVERY frames and reused between; omit it (offline tools) to
    recompute every call."""
    w, h = surf.get_size()
    # Desaturate via a HALF-RESOLUTION grayscale pass. The grey is blended
    # back at ~32% alpha, so the downscale is imperceptible, but grayscaling
    # a quarter of the pixels (then scaling the result back up) is ~2x
    # cheaper than a full-frame grayscale every frame -- the single largest
    # per-frame cost otherwise. smoothscale DOWN (clean average), plain
    # scale UP (cheap; the soft grey hides the blockiness). The grey is also
    # reused for GRADE_DESAT_EVERY frames (see _GREY_CACHE) since it is barely
    # visible at 32% alpha -- halving even this op's cost.
    try:
        reuse = (frame is not None
                 and _GREY_CACHE["surf"] is not None
                 and _GREY_CACHE["size"] == (w, h)
                 and _GREY_CACHE["frame"] is not None
                 and 0 <= frame - _GREY_CACHE["frame"] < GRADE_DESAT_EVERY)
        if reuse:
            grey = _GREY_CACHE["surf"]
        else:
            small = pygame.transform.smoothscale(surf, (w // 2, h // 2))
            grey = pygame.transform.grayscale(small)
            grey = pygame.transform.scale(grey, (w, h))
            if frame is not None:
                _GREY_CACHE["surf"] = grey
                _GREY_CACHE["size"] = (w, h)
                _GREY_CACHE["frame"] = frame
        grey.set_alpha(desat)
        surf.blit(grey, (0, 0))
    except Exception:
        pass
    tint = _TINT_CACHE.get((w, h))
    if tint is None:
        tint = pygame.Surface((w, h), pygame.SRCALPHA)
        tint.fill((_GRADE_TINT[0], _GRADE_TINT[1], _GRADE_TINT[2], 38))
        _TINT_CACHE[(w, h)] = tint
    surf.blit(tint, (0, 0))
    surf.blit(_vignette(w, h), (0, 0))
    g = _grain_tile()
    gw, gh = g.get_size()
    ox = int(t * 41) % gw
    oy = int(t * 67) % gh
    yy = -oy
    while yy < h:
        xx = -ox
        while xx < w:
            surf.blit(g, (xx, yy))
            xx += gw
        yy += gh


