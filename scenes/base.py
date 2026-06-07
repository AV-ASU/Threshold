"""Scene primitives: tile definitions, tile-drawing helpers, the Scene
class itself. All scene builders consume these to define areas."""
import math
import random
import pygame
from constants import SCREEN_W, SCREEN_H, TILE


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
    "shelf", "stove", "crate", "debris",
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
    # floor where geometry serves the door (NARRATIVE 1b). draw_floor flat-fills
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
    "s": {"solid": True, "kind": "shelf"},
    "i": {"solid": True, "kind": "window"},
    "f": {"solid": True, "kind": "fireplace"},
    "k": {"solid": True, "kind": "stove"},
    "5": {"solid": True, "kind": "counter"},   # kitchen counter / cabinets
    "X": {"solid": True, "kind": "invisible"},
    "D": {"solid": False, "kind": "door"},
    "E": {"solid": False, "kind": "door"},   # depths chain east-exits
    "H": {"solid": False, "kind": "door"},
    "B": {"solid": False, "kind": "door"},
    "F": {"solid": False, "kind": "door"},
    "J": {"solid": False, "kind": "door"},   # door to kid_house interior
    # Per-house entry doors (each house in the new public square + the
    # Clerk's place in our_house_area gets its own char so the layout
    # is self-documenting and the scene knows which interior to load).
    "m": {"solid": False, "kind": "door"},   # door to old_man_house
    "y": {"solid": False, "kind": "door"},   # door to fisherman_cottage
    "h": {"solid": False, "kind": "door"},   # door to innkeeper_house
    "n": {"solid": False, "kind": "door"},   # door to barn (south of village)
    "o": {"solid": False, "kind": "door"},   # door to haunted_house (red herring)
    # Locked-house door: SOLID until unlocked. The brass-key gate fires
    # from village.on_interact_fn -- pressing E from an adjacent tile
    # transitions if the key is in inventory, otherwise shows a locked
    # notice. The wall blocks movement so the player can't just walk
    # through an unlocked-looking door.
    "z": {"solid": True,  "kind": "door"},   # door to locked_house (red herring)
    # Door "1" -> the Clerk's room (key 'son_room'), an unconditional
    # exit off the ground floor. ("2" is a vestigial tile from a cut
    # scene; no active map places it.)
    "1": {"solid": False, "kind": "door"},   # door to son_room (Clerk's room)
    "2": {"solid": False, "kind": "door"},   # vestigial (cut scene)
    # Outdoor-passage style transition tiles -- non-solid, non-drawing
    # so the underlying floor (grass / water) shows through cleanly.
    # '4' is the village <-> brimley corridor.
    "4": {"solid": False, "kind": "outdoor_passage"},
    # Fake wall: looks like a wood wall, passable. Used inside the
    # haunted_house red herring -- the player walks through it once to
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
    # Q=relocation marker (threshold_extras), Y=fisherman, N=innkeeper (quest)
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
    # Per-tile value jitter so adjacent tiles never read identical -- the
    # cheapest break of the grid lockstep (cached per (ch,tx,ty), so free
    # after the first draw). Animated floors (~,@) skip it: they reseed each
    # frame and a jitter would shimmer as you walk.
    if ch not in _ANIM_FLOOR and ch != "0":
        jv = (_vary(tx * 8009 + ty, 0) % 13) - 6        # -6..6, value only
        base = (max(0, min(255, base[0] + jv)),
                max(0, min(255, base[1] + jv)),
                max(0, min(255, base[2] + jv)))
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
        boards = ((0, 10), (10, 12), (22, 10))     # (y0, height) per board
        for b, (y0, bh) in enumerate(boards):
            row = ty * 3 + b
            v = ((row * 2654435761) & 0xff) / 255.0 - 0.5    # -0.5..0.5
            shade = (max(0, min(255, int(88 + v * 26))),
                     max(0, min(255, int(66 + v * 20))),
                     max(0, min(255, int(42 + v * 16))))
            pygame.draw.rect(surf, shade, (rx, ry + y0, TILE, bh))
            pygame.draw.line(surf, (52, 36, 22),
                             (rx, ry + y0), (rx + TILE, ry + y0), 1)
            pygame.draw.line(surf, (104, 80, 52),
                             (rx, ry + y0 + 1), (rx + TILE, ry + y0 + 1), 1)
            # Staggered end-joint -- only some boards, so planks run long.
            if (tx * 3 + row) % 5 == 0:
                jx = rx + ((row * 11 + tx * 7) % (TILE - 6)) + 3
                pygame.draw.line(surf, (50, 34, 20),
                                 (jx, ry + y0 + 1), (jx, ry + y0 + bh - 1), 1)
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
    # Macro shadow blotches: a low-frequency, world-anchored darkening
    # that rolls across many tiles at once, so the floor stops reading
    # as a grid of identical cells. Two cheap sine layers, darken-only.
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
    "house":                "the Inn",
    "son_room":              "the Clerk's Room",
    "maras_room":           "Mara's Room",
    "basement":             "the Cellar",
    "our_house_area":       "the Yard",
    "kid_house":            "the Kid's House",
    "shop":                 "General Store",
    "old_man_house":        "the Church",
    "fisherman_cottage":    "Sheriff's Office",
    "forest_path":          "Cornfield Path",
    "void_boss":            "the Clearing",
    "barn":                 "the Barn",
    "well_bottom":          "the Shaft Floor",
    "well_passage":         "the Drying Racks",
    "works_vats":           "the Cistern",
    "works_sorting":        "the Sorting Hall",
    "works_scriptorium":    "the Scriptorium",
    "works_sign":           "the Sign Chamber",
    "works_deepstair":      "the Deep Stair",
    "haunted_house":        "the Abandoned Farmhouse",
    "brimley":            "Brimley",
    "schoolhouse":          "the Schoolhouse",
    "graveyard":            "the Graveyard",
    "country_lane":         "the Country Lane",
    "gravel_road_north":    "the Gravel Road",
    "backwoods_cabin":      "the Hunter's Cabin",
    "backwoods_cabin_interior": "the Cabin",
    "river_crossing":       "the River Crossing",
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


def _tilt_standee(surf, camera, scene, tx, ty, ch):
    """Stand a tree / cornstalk up as a camera-facing billboard whose base sits
    on the floor at the tile centre. The flat tile art (_draw_tree/_draw_corn)
    is rendered onto a card with its trunk/stalk base at the bottom-centre, then
    draw_billboard foreshortens it consistently with the wall solids. Corn merges
    into a width-wide run card (LOD). Cards are CACHED + convert_alpha'd (cleared
    on scene change with the floor cache); trees keep a soft contact shadow."""
    from rendering.solids import draw_billboard
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
    wx = tx * TILE + (width * TILE) // 2   # run centre (single tile -> centre)
    wy = ty * TILE + 16
    if kind != "cornstalk":                # trees grounded; corn is too dense
        bx, by = camera.project(wx, wy, 0.0)
        _ground_shadow(surf, bx, by, 12, 5, 70)
    draw_billboard(surf, camera, wx, wy, card, h_anchor=1.0)


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
            pygame.draw.rect(surf, _WALL_BASE, (rx, ry, TILE, TILE))
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
                pygame.draw.rect(surf, _WALL_TOP, (rx, ry, TILE, 2))
                pygame.draw.line(surf, _WALL_FACE, (rx, ry + 2 + j),
                                 (rx + TILE, ry + 2 + j), 1)
            if not _is_wall(scene, tx, ty + 1):     # room below: foot shadow
                # Damp band wicking up from the ground + a little moss,
                # only where the wall actually meets open floor.
                pygame.draw.rect(surf, (12, 11, 15), (rx, ry + TILE - 8, TILE, 5))
                if hsh % 3 == 0:
                    mx = rx + (hsh % (TILE - 6)) + 2
                    pygame.draw.circle(surf, (44, 56, 40), (mx, ry + TILE - 3), 2)
                pygame.draw.rect(surf, _WALL_FOOT, (rx, ry + TILE - 2, TILE, 2))
                pygame.draw.line(surf, _WALL_FACE, (rx, ry + TILE - 3 - j),
                                 (rx + TILE, ry + TILE - 3 - j), 1)
                if hsh % 4 == 0:    # rubble/grime spilling onto the floor,
                    bx = rx + (hsh % 18) + 4   # crossing the tile boundary so
                    pygame.draw.rect(surf, (27, 25, 29),  # the room edge isn't
                                     (bx, ry + TILE, 7, 3))     # a clean line
                    pygame.draw.rect(surf, (15, 14, 18), (bx + 2, ry + TILE + 1, 3, 2))
            if not _is_wall(scene, tx - 1, ty):
                pygame.draw.line(surf, _WALL_FACE, (rx + j, ry),
                                 (rx + j, ry + TILE), 1)
            if not _is_wall(scene, tx + 1, ty):
                pygame.draw.line(surf, _WALL_FACE, (rx + TILE - 1 - j, ry),
                                 (rx + TILE - 1 - j, ry + TILE), 1)


def _build_roof_regions(scene):
    """Flood-fill the roof ('r') tiles into one region per building and
    cache each region's tile bounding box on the scene. Roof layout is
    static after build, so this runs once. Each region -> one gabled
    roof drawn over its footprint."""
    regions = getattr(scene, "_roof_regions", None)
    if regions is not None:
        return regions
    objs, h, w = scene.objects, scene.h, scene.w
    seen = [[False] * w for _ in range(h)]
    regions = []
    for ty in range(h):
        for tx in range(w):
            if objs[ty][tx] != "r" or seen[ty][tx]:
                continue
            stack = [(tx, ty)]
            seen[ty][tx] = True
            minx = maxx = tx
            miny = maxy = ty
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
            regions.append((minx, miny, maxx, maxy))
    scene._roof_regions = regions
    return regions


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


def _door_room_dir(scene, tx, ty):
    """Which way the door opens -- the floor (room) side its leaf swings
    into. Off-map edges don't count as wall, so a building's south-edge
    exit still opens toward its interior."""
    def w(ax, ay):
        return (0 <= ay < scene.h and 0 <= ax < scene.w
                and scene.objects[ay][ax] in _WALL_CHARS)
    def fl(ax, ay):
        return (0 <= ay < scene.h and 0 <= ax < scene.w
                and scene.objects[ay][ax] not in _WALL_CHARS)
    wl, wr, wu, wd = w(tx - 1, ty), w(tx + 1, ty), w(tx, ty - 1), w(tx, ty + 1)
    if (wu or wd) and not (wl or wr):           # vertical wall -> opens L/R
        return "E" if fl(tx + 1, ty) else "W"
    if (wl or wr) and not (wu or wd):           # horizontal wall -> opens up/down
        return "S" if fl(tx, ty + 1) else "N"
    if fl(tx, ty + 1):                          # corner / ambiguous
        return "S"
    if fl(tx + 1, ty):
        return "E"
    if fl(tx, ty - 1):
        return "N"
    return "W"


def _draw_door_opening(surf, rx, ry, room, tx, ty):
    """The doorway itself, drawn in-tile during the terrain pass: the
    wall fills through (continuous mass) with a dark opening punched in
    it + a lit face on the room side. The swung leaf is a separate,
    unconfined sprite drawn later (draw_scene_doors)."""
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


def _draw_path_fringe(surf, scene, tx, ty, rx, ry):
    """Fray a dirt-path tile's edge wherever it meets grass: dirt tongues
    spill raggedly into the grass and a few grass tufts bite back into the
    dirt, so the worn track wanders instead of reading as a clean
    rectangle. Run after every floor fill so the blobs paint across the
    tile boundary. Dirt only frays its grass-facing sides, so adjacent
    path tiles leave their shared (interior) edge clean."""
    floor, h, w = scene.floor, scene.h, scene.w
    dirt, dirt2 = (88, 68, 45), (74, 56, 37)
    for si, (ndx, ndy) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):
        nx, ny = tx + ndx, ty + ndy
        if not (0 <= nx < w and 0 <= ny < h) or floor[ny][nx] not in _PATH_GRASS:
            continue
        grass = FLOOR_DEFS[floor[ny][nx]]["color"]
        seed = (tx * 73856093) ^ (ty * 19349663) ^ (si * 83492791)
        if ndy:                                  # horizontal edge (N/S)
            ex = rx; ey = ry + (TILE if ndy > 0 else 0); ax, ay = 1, 0
        else:                                    # vertical edge (W/E)
            ex = rx + (TILE if ndx > 0 else 0); ey = ry; ax, ay = 0, 1
        for k in range(6):                       # ragged dirt fringe, mostly into grass
            u = (k + (_vary(seed, k) % 3) / 3.0) / 6.0
            depth = (_vary(seed, 10 + k) % 9) - 3
            cx = int(ex + ax * TILE * u + ndx * depth)
            cy = int(ey + ay * TILE * u + ndy * depth)
            col = dirt if (_vary(seed, 30 + k) % 3) else dirt2
            pygame.draw.circle(surf, col, (cx, cy), 3 + (_vary(seed, 20 + k) % 3))
        for k in range(2):                       # grass tufts biting back into the dirt
            u = (1 + 2 * k) / 4.0
            d = 2 + (_vary(seed, 40 + k) % 3)
            cx = int(ex + ax * TILE * u - ndx * d)
            cy = int(ey + ay * TILE * u - ndy * d)
            pygame.draw.circle(surf, grass, (cx, cy), 2 + (_vary(seed, 50 + k) % 2))


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


def draw_scene_terrain(surf, scene, cam_x, cam_y, x0, y0, x1, y1,
                       skip_billboard=False):
    """Floor -> path fringe -> wall-cast shadows -> continuous wall mass
    -> non-wall objects, for a tile window. Shared by Scene.draw (camera
    window) and the offline full-map renderer. When scene.wrap_x or
    .wrap_y is True, tile lookups wrap mod self.w / self.h so x0/x1 /
    y0/y1 may extend past the map bounds and the render stays seamless
    across the wrap line.

    `skip_billboard` (the tilt floor pass) omits trees/cornstalks here so they
    aren't painted flat on the warped floor -- draw_terrain_tilted stands them
    up as billboards instead."""
    W, H = scene.w, scene.h
    wx, wy = scene.wrap_x, scene.wrap_y
    def _lookup_floor(ty, tx):
        if wy: ty %= H
        if wx: tx %= W
        if not (0 <= ty < H and 0 <= tx < W):
            return "."
        return scene.floor[ty][tx]
    def _lookup_obj(ty, tx):
        if wy: ty %= H
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
        _FLOOR_CACHE_SCENE = scene   # hold the ref so its identity can't be reused
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            ch = _lookup_floor(ty, tx)
            rx = tx * TILE - cam_x
            ry = ty * TILE - cam_y
            if ch in _ANIM_FLOOR:
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
            elif ch == "~":
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
                                   or ch in _COUNTER_CHARS):
                continue                     # stood up as a 3D box/standee under tilt
            rx = tx * TILE - cam_x
            ry = ty * TILE - cam_y
            if ch in _DOOR_CHARS:
                _draw_door_opening(surf, rx, ry, _door_room_dir(scene, tx, ty), tx, ty)
            else:
                draw_object(surf, ch, rx, ry, tx, ty)
    # Unified gabled roofs, drawn over the walls so each building reads
    # as one overhanging roof (door stays visible under the front eave).
    _draw_scene_roofs(surf, scene, cam_x, cam_y, x0, y0, x1, y1)


# --- Tilted (oblique-camera) terrain (CAMERA.md Phase 2) -------------------
# Active only when camera.pitch > 0. The floor is a flat z=0 plane, so we
# render the visible window flat (exactly the legacy raster, wrap-aware) and
# warp the whole image to the oblique plane -- preserving every procedural
# floor detail -- then extrude wall tiles as upright quads on top.
_TILT_WALL_RISE = 26


def _tilt_window_half(camera):
    """Smallest centred half-span (world px) whose flat window still covers
    the tilted screen. Unproject the screen corners (+ upward wall headroom)
    and take the farthest world offset from the view centre."""
    corners = [(0, 0), (SCREEN_W, 0), (0, SCREEN_H), (SCREEN_W, SCREEN_H),
               (SCREEN_W // 2, -_TILT_WALL_RISE)]
    half = 0.0
    for sx, sy in corners:
        wx, wy = camera.unproject(sx, sy)
        half = max(half, abs(wx - camera.cam_x), abs(wy - camera.cam_y))
    return half + TILE


def _tilt_warp(flat, camera):
    """Affine warp of the flat floor to match camera.project() for z=0:
    world-rotate by yaw, then scale x by scale and y by scale*cos(pitch)."""
    rotated = pygame.transform.rotate(flat, math.degrees(camera.yaw))
    cp = max(0.05, math.cos(camera.pitch))
    w, h = rotated.get_size()
    # `scale` (nearest) rather than `smoothscale` (bilinear): the floor raster
    # is a low-detail tile pattern sitting under the tilt + Brimley's haze, so
    # the smoothing is imperceptible, but smoothscale on this large surface was
    # the single biggest per-frame cost in the wrapped town (~10x scale's cost).
    return pygame.transform.scale(
        rotated, (max(1, int(w * camera.scale)),
                  max(1, int(h * camera.scale * cp))))


_DOOR_HEAD = 19      # doorway opening height; the lintel beam runs head->rise


def _quad_pt(quad, fx, fy):
    """A point inside a projected quad (bl, br, tr, tl) at fractions
    fx (0..1 left->right along the base) and fy (0..1 bottom->top)."""
    bl, br, tr, tl = quad
    bx = bl[0] + (br[0] - bl[0]) * fx; by = bl[1] + (br[1] - bl[1]) * fx
    tx_ = tl[0] + (tr[0] - tl[0]) * fx; ty_ = tl[1] + (tr[1] - tl[1]) * fx
    return (bx + (tx_ - bx) * fy, by + (ty_ - by) * fy)


def _extrude_box(surf, camera, scene, tx, ty, z0, z1, neigh=_WALL_CHARS,
                 face_col=None, top_col=None):
    """One tile extruded between heights z0..z1. Rotation-correct: every
    EXPOSED side face (neighbour char not in `neigh`) is drawn, depth-sorted
    far->near so near faces overdraw far, capped with a flat shaded top quad
    (no axis-aligned texture that would overflow once the camera yaws).
    `face_col` / `top_col` default to the near-black wall palette; pass wood
    tones for a counter/furniture box."""
    face_col = _WALL_FACE if face_col is None else face_col
    top_col = _WALL_TOP if top_col is None else top_col
    wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
    hw = TILE / 2

    def P(dx, dy, dz):
        return camera.project(wx + dx, wy + dy, dz)
    g = [P(-hw, -hw, z0), P(hw, -hw, z0), P(hw, hw, z0), P(-hw, hw, z0)]
    t = [P(-hw, -hw, z1), P(hw, -hw, z1), P(hw, hw, z1), P(-hw, hw, z1)]
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
    # (neighbour dx, dy, face centroid offset, quad corners, colour) per side
    faces = (
        (0, 1, (0, hw), (g[3], g[2], t[2], t[3]), near),    # south
        (0, -1, (0, -hw), (g[0], g[1], t[1], t[0]), near),  # north
        (-1, 0, (-hw, 0), (g[0], g[3], t[3], t[0]), side),  # west
        (1, 0, (hw, 0), (g[1], g[2], t[2], t[1]), side),    # east
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


def _tilt_wall_box(surf, camera, scene, tx, ty):
    _extrude_box(surf, camera, scene, tx, ty, 0, _TILT_WALL_RISE)


_COUNTER_RISE = 15      # waist-high: a divider you can see over, not a wall


def _tilt_counter_box(surf, camera, scene, tx, ty):
    """The kitchen counter / peninsula divider: a waist-high wood box (shorter
    than a wall) so the common-room divider reads as a solid 3D bar under the
    tilt instead of a flat painted strip. Adjacent counter tiles merge into one
    run (counter neighbours cull their shared faces)."""
    _extrude_box(surf, camera, scene, tx, ty, 0, _COUNTER_RISE,
                 neigh=_WALL_CHARS | _COUNTER_CHARS,
                 face_col=(96, 72, 48), top_col=(122, 98, 66))


def _tilt_door_box(surf, camera, scene, tx, ty):
    """A doorway in the extruded wall: a lintel BEAM spanning the top of the
    tile (head->rise) with the passage open below. The flanking wall tiles
    supply the jambs; a swung leaf hangs in the opening. Faces abutting walls
    OR other doors are culled so a multi-tile gate reads as one clean opening."""
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
    # 1. dark recess, set slightly INTO the wall (off +)
    rec = [Q(-hw + 1, 0, 3), Q(hw - 1, 0, 3), Q(hw - 1, head, 3), Q(-hw + 1, head, 3)]
    pygame.draw.polygon(surf, (7, 6, 9), rec)
    # 2. wood frame on the room face (off -), a "n" around the opening
    tw, th, off = 4.0, 3.0, -1.0

    def face(u0, u1, z0, z1, col):
        pygame.draw.polygon(surf, col, [Q(u0, z0, off), Q(u1, z0, off),
                                        Q(u1, z1, off), Q(u0, z1, off)])
    face(-hw, -hw + tw, 0, head, wood)            # left jamb
    face(hw - tw, hw, 0, head, wood)              # right jamb
    face(-hw, hw, head - th, head, wood_hi)       # lintel
    # 3. the leaf, hinged at the left jamb
    a = 0.0 if solid else math.radians(26)        # shut vs ajar
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
    "body", "drowned_body", "water_trail", "child_drawing", "campfire",
    "effects_pile",
    # Low overhead foliage (drawn top-down): a flat warped decal reads as a
    # shrub on the ground, where a standee would stand the overhead blob up
    # vertically as a smear.
    "bush",
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
    "chalk_door_wall", "chalkboard",
))
_WALL_MOUNT_Z = 18


def _draw_floor_decal(surf, camera, deco, woff=(0.0, 0.0)):
    """Render a flat decal to a canvas, then warp it onto the floor plane (same
    rotate+squash as _tilt_warp) and blit at the projected anchor, so a rug or
    bloodstain lies on the ground and turns with the room instead of standing up
    as a billboard. `woff` is the wrap-clone WORLD offset (added before
    projection so the seam clone lands through the camera, not in screen space;
    CAMERA.md Phase 5)."""
    drawfn = getattr(deco, f"_draw_{deco.kind}", None)
    if drawfn is None:
        return
    if deco.kind == "rug":
        w = int(deco.kwargs.get("w", 88)); h = int(deco.kwargs.get("h", 60))
        bound = max(w, h) + 18
    else:
        bound = 60
    canvas = pygame.Surface((bound, bound), pygame.SRCALPHA)
    drawfn(canvas, bound // 2, bound // 2)
    rot = pygame.transform.rotate(canvas, math.degrees(camera.yaw))
    cp = max(0.05, math.cos(camera.pitch))
    sw = max(1, int(rot.get_width() * camera.scale))
    sh = max(1, int(rot.get_height() * camera.scale * cp))
    scaled = pygame.transform.smoothscale(rot, (sw, sh))
    sx, sy = camera.project(deco.x + woff[0], deco.y + woff[1], 0)
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
    card = pygame.transform.scale(canvas, (max(3, int(width)), max(3, h)))
    ang = math.degrees(math.atan2(-(p2[1] - p1[1]), p2[0] - p1[0]))
    if abs(ang) > 0.5:
        card = pygame.transform.rotate(card, ang)
    surf.blit(card, (int(cx) - card.get_width() // 2,
                     int(cy) - card.get_height() // 2))


def _draw_window_pane(surf, camera, wx, wy, ndx, ndy):
    """A lit amber pane set into one wall face: wood frame, sickly glass, a warm
    core and a muntin cross. `(ndx, ndy)` is the exposed face direction."""
    hw = TILE / 2
    pv = (-ndy, ndx)                 # along-wall axis on this face
    ph = hw * 0.60                   # half pane width
    z0, z1 = 7.0, 19.0
    off = hw * 0.99                  # sit just proud of the face

    def Q(u, z):
        return camera.project(wx + ndx * off + pv[0] * u,
                              wy + ndy * off + pv[1] * u, z)
    frame = [Q(-ph - 2, z0 - 2), Q(ph + 2, z0 - 2), Q(ph + 2, z1 + 2), Q(-ph - 2, z1 + 2)]
    glass = [Q(-ph, z0), Q(ph, z0), Q(ph, z1), Q(-ph, z1)]
    core = [Q(-ph * 0.5, z0 + 3), Q(ph * 0.5, z0 + 3),
            Q(ph * 0.5, z1 - 3), Q(-ph * 0.5, z1 - 3)]
    pygame.draw.polygon(surf, (96, 70, 50), frame)
    pygame.draw.polygon(surf, (60, 40, 25), frame, 1)
    pygame.draw.polygon(surf, (138, 104, 50), glass)
    pygame.draw.polygon(surf, (170, 138, 78), core)
    pygame.draw.line(surf, (74, 54, 34), Q(0, z0), Q(0, z1), 1)               # mullion
    pygame.draw.line(surf, (74, 54, 34), Q(-ph, (z0 + z1) / 2), Q(ph, (z0 + z1) / 2), 1)
    pygame.draw.polygon(surf, (60, 40, 25), glass, 1)


def _tilt_window_box(surf, camera, scene, tx, ty):
    """A window is a SOLID wall tile, so it extrudes as a full wall box; a lit
    pane is then set into each camera-facing exposed face."""
    _tilt_wall_box(surf, camera, scene, tx, ty)
    wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
    hw = TILE / 2
    cd = camera.depth(wx, wy, _TILT_WALL_RISE / 2)
    for ndx, ndy in ((0, 1), (0, -1), (-1, 0), (1, 0)):
        if _is_wall(scene, tx + ndx, ty + ndy):
            continue                                     # buried face
        if camera.depth(wx + ndx * hw, wy + ndy * hw, _TILT_WALL_RISE / 2) <= cd:
            continue                                     # faces away from camera
        _draw_window_pane(surf, camera, wx, wy, ndx, ndy)


def _tilt_tile_box(surf, camera, scene, tx, ty):
    """Dispatch a tile to its tilt solid: a wall-mass box, a doorway (lintel +
    swung leaf), a window (box + lit pane), or a tree/cornstalk STANDEE."""
    wtx = tx % scene.w if scene.wrap_x else tx
    wty = ty % scene.h if scene.wrap_y else ty
    ch = (scene.objects[wty][wtx]
          if 0 <= wty < scene.h and 0 <= wtx < scene.w else "")
    if ch in _TILT_BILLBOARD_CHARS:
        _tilt_standee(surf, camera, scene, tx, ty, ch)
    elif ch in _COUNTER_CHARS:
        _tilt_counter_box(surf, camera, scene, tx, ty)
    elif ch in _DOOR_CHARS:
        _tilt_door_box(surf, camera, scene, tx, ty)
    elif ch in _WINDOW_CHARS:
        _tilt_window_box(surf, camera, scene, tx, ty)
    else:
        _tilt_wall_box(surf, camera, scene, tx, ty)


def draw_terrain_tilted(surf, scene, camera, sight=None):
    """Floor warp + flat decals for the oblique camera. Skybox is the caller's
    job (drawn first); actors are drawn after by the game, already projected
    through the same camera so they stand on this floor.

    The upright occluders -- WALL tiles and SOLID furniture/props -- are NOT
    drawn here. They are RETURNED as `(wall_tiles, solid_decos)` so the caller
    can depth-interleave them with the actors and fade each per-actor
    (CAMERA.md Phase 5: every actor + prop sorts against every wall by
    Camera.depth, and a wall fades for whichever actor it actually covers, not
    just the player). Only the flat layer -- the warped floor raster and the
    ground decals / billboard decorations that lie on or rise from it -- is
    drawn now (it can never occlude an actor).

    `sight` is the optional Phase 4 blind-spot factor fn(wx, wy) -> 0..1
    (rendering/sight.py). When given, decorations flagged `_sight_gated`
    (the infestation rot) only draw where the player actually looks -- the
    world's rot reveals on a peek and re-hides off-camera."""
    cx, cy = camera.cam_x, camera.cam_y
    half = _tilt_window_half(camera)
    span = int(half * 2)
    flat = pygame.Surface((span, span))
    flat.fill((10, 10, 14))
    wx0, wy0 = cx - half, cy - half
    x0 = int(math.floor(wx0 / TILE)); y0 = int(math.floor(wy0 / TILE))
    x1 = int(math.ceil((wx0 + span) / TILE)); y1 = int(math.ceil((wy0 + span) / TILE))
    draw_scene_terrain(flat, scene, wx0, wy0, x0, y0, x1, y1,
                       skip_billboard=True)
    warped = _tilt_warp(flat, camera)
    ox, oy = camera.origin
    surf.blit(warped, (ox - warped.get_width() // 2,
                       oy - warped.get_height() // 2))
    # Collect the visible wall tiles (returned for the unified depth pass; the
    # caller sorts + fades them). Wrap-aware: tx/ty may sit outside [0,W) for a
    # toroidal scene and the box projects at the un-wrapped world position.
    walls = []
    W, H = scene.w, scene.h
    corn_suppressed = _corn_runs(scene)[1]   # LOD: tiles drawn by a run anchor
    for ty in range(y0, y1):
        wty = ty % H if scene.wrap_y else ty
        if not (0 <= wty < H):
            continue
        for tx in range(x0, x1):
            wtx = tx % W if scene.wrap_x else tx
            if not (0 <= wtx < W):
                continue
            ch = scene.objects[wty][wtx]
            if ch in _CORN_CHARS and (wtx, wty) in corn_suppressed:
                continue                         # part of a run; its anchor draws it
            if (ch in _WALL_CHARS or ch in _DOOR_CHARS or ch in _WINDOW_CHARS
                    or ch in _TILT_BILLBOARD_CHARS or ch in _COUNTER_CHARS):
                walls.append((tx, ty))
    # Decorations. Ground decals (rugs, stains, blood) stay flat on the warped
    # floor; non-solid billboards rise from it -- both drawn now, wrap-cloned
    # across the seam THROUGH the projection (CAMERA.md Phase 5) so a torus
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
    wall_decos = []
    for d in scene.decorations:
        if is_solid_furniture(d.kind) or is_solid_prop(d.kind):
            solid_decos.append(d)
            continue
        if d.kind in _WALL_DECO_KINDS:
            # Hung on the wall, not lying on the floor: returned so the caller
            # lifts + depth-sorts it with the walls (drawn flat here would put
            # it on the ground and behind the wall box).
            wall_decos.append(d)
            continue
        if d.kind == "water_channel":
            # A long floor thread: drawn as a projected polyline (no canvas), so
            # it can run the length of the scene. Under everything (terrain pass).
            for woff in offsets:
                _draw_water_channel_tilt(surf, camera, d, woff)
            continue
        # Phase 4: rot decals are a world change -- gated to line of sight.
        a = 255
        if sight is not None and getattr(d, "_sight_gated", False):
            f = sight(d.x, d.y)
            if f <= 0.03:
                continue
            a = 255 if f >= 0.99 else int(255 * f)
        floor_decal = d.kind in _FLOOR_DECAL_KINDS
        for woff in offsets:
            psx, psy = camera.project(d.x + woff[0], d.y + woff[1])
            if not (-MX <= psx <= sw + MX and -MTOP <= psy <= sh + MBOT):
                continue                         # off-screen clone -> skip
            if floor_decal:
                draw_with_alpha(surf, a, lambda s, d=d, woff=woff:
                                _draw_floor_decal(s, camera, d, woff))
            else:
                draw_with_alpha(surf, a, lambda s, d=d, woff=woff:
                                d.draw(s, 0, 0, camera, wox=woff[0], woy=woff[1]))
    return walls, solid_decos, wall_decos


def draw_scene_doors(surf, scene, cam_x, cam_y, x0, y0, x1, y1):
    """Late pass: the swung door leaves, drawn unconfined so each spills
    out of its tile into the room. Called after terrain + decorations
    and before entities, so a leaf sits over the floor but under anyone
    walking through the doorway."""
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


def apply_grade(surf, t=0.0, desat=82):
    """Grade a finished frame in place: partial desaturation, a cool
    tint, a radial vignette, and animated film grain."""
    w, h = surf.get_size()
    # Desaturate via a HALF-RESOLUTION grayscale pass. The grey is blended
    # back at ~32% alpha, so the downscale is imperceptible, but grayscaling
    # a quarter of the pixels (then scaling the result back up) is ~2x
    # cheaper than a full-frame grayscale every frame -- the single largest
    # per-frame cost otherwise. smoothscale DOWN (clean average), plain
    # scale UP (cheap; the soft grey hides the blockiness).
    try:
        small = pygame.transform.smoothscale(surf, (w // 2, h // 2))
        grey = pygame.transform.grayscale(small)
        grey = pygame.transform.scale(grey, (w, h))
        grey.set_alpha(desat)
        surf.blit(grey, (0, 0))
    except Exception:
        pass
    tint = pygame.Surface((w, h), pygame.SRCALPHA)
    tint.fill((_GRADE_TINT[0], _GRADE_TINT[1], _GRADE_TINT[2], 38))
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


_DIRECTION_VECTORS = {
    "north": (0, -1),
    "south": (0, 1),
    "east":  (1, 0),
    "west":  (-1, 0),
}


def scatter_forest_band(floor_ll, objects_l, w, h, *,
                         depth=7, seed=53,
                         tree_density=0.48, tree_floor=0.04,
                         passable_ratio=0.6,
                         blotch_dim=0.22, blotch_corn=0.09,
                         bush_density=0.10,
                         solid_char="T", passable_char="p",
                         protected=None, place_bush=None):
    """Stamp a permeable scattered band around the perimeter of an
    outdoor scene. The wrap mechanic moves the player; this is the
    visual camouflage that hides the transition. Both floor_ll and
    objects_l are mutated in place.

    - Walls (default 'T' solid / 'p' passable trees; pass solid_char +
      passable_char to use corn 'C'/'A' or whatever else) seeded at
      decreasing density from the outer edge inward across `depth`
      tiles. `passable_ratio` of placements are passable so navigation
      is forgiving.
    - Ground blotch: ';' dim grass + ':' corn cover (which hides the
      player) mixed into the open grass in the same band.
    - De-clump pass: any 2x2 block of solid chars gets one corner
      converted to passable so the player is never stopped by a wall.
    - Bushes: `place_bush(x_px, y_px)` is called for each chosen
      decoration position; the floor under each bush is forced to ':'
      so stepping into it hides. Pass a callback that adds the bush
      Decoration to the scene.

    `protected(tx, ty) -> bool` exempts tiles from EVERY pass (walls,
    blotch, bushes). Used for road corridors and spawn approaches.
    """
    rng = random.Random(seed)
    prot = protected or (lambda tx, ty: False)
    # Pass 1 -- walls in objects.
    def _wall_char():
        return passable_char if rng.random() < passable_ratio else solid_char
    for ty in range(h):
        for tx in range(w):
            edge_dist = min(tx, w - 1 - tx, ty, h - 1 - ty)
            if edge_dist >= depth:
                continue
            if objects_l[ty][tx] != ".":
                continue
            if prot(tx, ty):
                continue
            t = edge_dist / depth
            density = tree_density * (1 - t) + tree_floor
            if rng.random() < density:
                objects_l[ty][tx] = _wall_char()
    # Pass 2 -- de-clump: break any 2x2 block of solid walls.
    for ty in range(h - 1):
        for tx in range(w - 1):
            quad = [objects_l[ty][tx], objects_l[ty][tx + 1],
                    objects_l[ty + 1][tx], objects_l[ty + 1][tx + 1]]
            if quad.count(solid_char) == 4:
                cands = [(tx, ty), (tx + 1, ty),
                         (tx, ty + 1), (tx + 1, ty + 1)]
                cx, cy = min(cands,
                             key=lambda p: (p[0] - w / 2) ** 2 +
                                           (p[1] - h / 2) ** 2)
                if not prot(cx, cy):
                    objects_l[cy][cx] = passable_char
    # Pass 3 -- ensure every solid wall has at least one passable
    # orthogonal neighbour; otherwise it's a dead-end clump and gets
    # swapped to passable.
    open_set = (".", passable_char)
    for ty in range(1, h - 1):
        for tx in range(1, w - 1):
            if objects_l[ty][tx] != solid_char:
                continue
            if prot(tx, ty):
                continue
            neighbors = [objects_l[ty - 1][tx], objects_l[ty + 1][tx],
                         objects_l[ty][tx - 1], objects_l[ty][tx + 1]]
            if not any(n in open_set for n in neighbors):
                objects_l[ty][tx] = passable_char
    # Pass 4 -- ground blotch in the same band.
    blotch_rng = random.Random(seed + 1)
    for ty in range(h):
        for tx in range(w):
            edge_dist = min(tx, w - 1 - tx, ty, h - 1 - ty)
            if edge_dist >= depth:
                continue
            if floor_ll[ty][tx] != "g":
                continue
            if prot(tx, ty):
                continue
            t = edge_dist / depth
            falloff = (1 - t)
            roll = blotch_rng.random()
            if roll < blotch_dim * falloff:
                floor_ll[ty][tx] = ";"
            elif roll < (blotch_dim + blotch_corn) * falloff:
                floor_ll[ty][tx] = ":"
    # Pass 5 -- bushes. Scatter them on open ('.') tiles in the band,
    # set the floor under each to ':' (corn cover, hides the player),
    # and call back to add the Decoration.
    if place_bush is not None:
        bush_rng = random.Random(seed + 2)
        for ty in range(h):
            for tx in range(w):
                edge_dist = min(tx, w - 1 - tx, ty, h - 1 - ty)
                if edge_dist >= depth:
                    continue
                if objects_l[ty][tx] != ".":
                    continue
                if prot(tx, ty):
                    continue
                t = edge_dist / depth
                # Lighter falloff than trees -- bushes spread further
                # in so the band has hideable spots even on its inner
                # rim.
                density = bush_density * (1 - 0.5 * t)
                if bush_rng.random() < density:
                    floor_ll[ty][tx] = ":"
                    px = tx * TILE + 16 + bush_rng.randint(-6, 6)
                    py = ty * TILE + 16 + bush_rng.randint(-6, 6)
                    place_bush(px, py)
    return floor_ll, objects_l


class Scene:
    TILE = TILE

    def __init__(self, key, floor_rows, object_rows=None, music="home"):
        self.key = key
        self.floor = [list(r) for r in floor_rows]
        self.h = len(self.floor)
        self.w = max(len(r) for r in self.floor) if self.floor else 0
        for i, r in enumerate(self.floor):
            if len(r) < self.w:
                self.floor[i] = r + ["."] * (self.w - len(r))
        if object_rows is None:
            self.objects = [["." for _ in range(self.w)] for _ in range(self.h)]
        else:
            self.objects = [list(r) for r in object_rows]
            for i, r in enumerate(self.objects):
                if len(r) < self.w:
                    self.objects[i] = r + ["."] * (self.w - len(r))
            while len(self.objects) < self.h:
                self.objects.append(["."] * self.w)
        self.music = music
        # If True, the world is toroidal on the matching axis: tile
        # lookups wrap mod self.w / self.h, the camera doesn't clamp,
        # and the player's x / y wrap as well. Used to make a road or
        # a field loop back on itself with no visible transition (the
        # fold). Off by default.
        self.wrap_x = False
        self.wrap_y = False
        # Oblique-camera skybox surround (CAMERA.md Phase 5). None = let the
        # game pick by scene type ("overcast" sallow sky for OUTDOOR_SCENES,
        # near-black "void" for interiors/underground so the horror keeps its
        # dark). A scene builder may pin "overcast"/"void" explicitly to
        # override the heuristic. Unused at pitch 0 (no skybox).
        self.skybox_kind = None
        self.exits = {}
        # Direction-sensitive exit chars: char -> "north"/"south"/etc.
        # If a char is in this dict, find_exit_at only fires the exit
        # when the player's facing matches that compass direction.
        self.exit_directions = {}
        self.spawns = {"default": (self.w * 16, self.h * 16)}
        self.npcs = []
        self.decorations = []
        self.enemies = []
        self.items = []          # list of {x,y,key,qty,on_pickup?}
        self.projectiles = []    # ranged-attack bullets
        self.triggers = []
        self.on_enter_fn = None
        self.on_exit_fn = None
        self.on_interact_fn = None    # called when E pressed and no NPC nearby
        # Points the [E] prompt should hover over for on_interact_fn-driven
        # readables/pickups (the case notebook, the cellar Ledger, the Mask
        # altar...). Without these, scene interactions handled in
        # on_interact_fn had no cue at all and players walked past them.
        # Each entry is (x, y, radius). See Game._draw_interact_prompt.
        self.interactables = []
        self.on_update_fn = None      # called every tick if set: fn(game, scene, dt)
        self.combat = False
        # Optional human-readable name for HUD display. When None,
        # the HUD falls back to a name lookup (DISPLAY_NAMES below)
        # and finally to titlecasing the scene key. Builders can
        # override for bespoke labels (e.g. "the Cellar").
        self.display_name = None
        # Watcher cameras. Each entry is a dict:
        #   {"x": px, "y": px, "range": px, "_t": 0.0}
        # The Game's _tick_eye_cameras polls them every frame: if
        # the player is unhidden and within `range`, the watcher's
        # `_t` accumulates. At threshold (~2.5 s) the watcher
        # fires a proximity bump + alert audio. Hide breaks line
        # of sight and the timer decays. (No scenes populate this
        # list currently.)
        self.eye_cameras = []

    def world_dx(self, from_x, to_x):
        """Shortest signed x-delta from from_x to to_x respecting
        the scene's wrap_x. Without wrap this is just to_x - from_x;
        with wrap it can be the opposite sign if the wrap is shorter."""
        dx = to_x - from_x
        if self.wrap_x:
            w_px = self.w * TILE
            if dx > w_px / 2:
                dx -= w_px
            elif dx < -w_px / 2:
                dx += w_px
        return dx

    def world_dy(self, from_y, to_y):
        """Shortest signed y-delta respecting wrap_y."""
        dy = to_y - from_y
        if self.wrap_y:
            h_px = self.h * TILE
            if dy > h_px / 2:
                dy -= h_px
            elif dy < -h_px / 2:
                dy += h_px
        return dy

    def world_dist(self, from_x, from_y, to_x, to_y):
        """Shortest world distance respecting wrap on both axes."""
        import math as _math
        dx = self.world_dx(from_x, to_x)
        dy = self.world_dy(from_y, to_y)
        return _math.hypot(dx, dy)

    def char_floor_at(self, x_px, y_px):
        tx = int(x_px // TILE); ty = int(y_px // TILE)
        if self.wrap_y:
            ty %= self.h
        if self.wrap_x:
            tx %= self.w
        if 0 <= ty < self.h and 0 <= tx < self.w:
            return self.floor[ty][tx]
        return "#"

    def char_object_at(self, x_px, y_px):
        tx = int(x_px // TILE); ty = int(y_px // TILE)
        if self.wrap_y:
            ty %= self.h
        if self.wrap_x:
            tx %= self.w
        if 0 <= ty < self.h and 0 <= tx < self.w:
            return self.objects[ty][tx]
        return "#"

    # --- Cover-aware navigation (cultist pursuit, NARRATIVE §8) ----------
    # The cult AI (entities/enemy.py + npc.py) routes AROUND the volumetric
    # cover now standing mid-floor (pillars, pews, cots, basins) via a
    # wrap-aware BFS over a walkable tile grid, while staying a straight shot
    # in the open. Folds are first-class: the grid wraps and the line test
    # crosses the seam, so a chase carries seamlessly THROUGH a fold.
    def _nav_solid_at(self, x_px, y_px):
        """STATIC blocker test for navigation -- walls + furniture only, NOT
        the (moving) NPCs that is_solid_at also counts. Baking live bodies
        into the path grid would leave phantom walls where someone briefly
        stood. Wrap-aware via the char_*_at lookups."""
        return (is_object_solid(self.char_object_at(x_px, y_px))
                or is_floor_solid(self.char_floor_at(x_px, y_px)))

    def nav_grid(self):
        """Cached [h][w] bool grid -- True where a tile centre is walkable.
        Built once per scene instance (objects/floor are static after the
        build pass; infestation only adds non-solid decals + swaps NPCs)."""
        g = getattr(self, "_nav_grid", None)
        if g is None:
            half = TILE // 2
            g = [[not self._nav_solid_at(tx * TILE + half, ty * TILE + half)
                  for tx in range(self.w)] for ty in range(self.h)]
            self._nav_grid = g
        return g

    def nav_clear_line(self, x0, y0, x1, y1, step=10):
        """True if the straight (wrap-aware) segment from (x0,y0) to (x1,y1)
        crosses no static blocker -- the cheap shortcut that keeps motion
        straight in the open and only pays for BFS when cover intervenes."""
        dx = self.world_dx(x0, x1)
        dy = self.world_dy(y0, y1)
        # max(1, ...) so a target within one `step` still samples the
        # endpoint -- otherwise n==0 skips the loop and reports a clear line
        # to a solid tile a few px away.
        n = max(1, int(math.hypot(dx, dy) // step))
        for i in range(1, n + 1):
            if self._nav_solid_at(x0 + dx * i / n, y0 + dy * i / n):
                return False
        return True

    def clear_sight_line(self, x0, y0, x1, y1, step=10):
        """True if the straight (wrap-aware) segment from (x0,y0) to (x1,y1)
        crosses no SIGHT blocker -- walls and solid props occlude; windows and
        floor (water/pits) do NOT (see `blocks_sight`). This is the line-of-
        sight predicate the cult AI uses to decide if it can actually SEE the
        player, not merely sense distance: step behind a wall or a solid prop
        and you break the chase. Distinct from `nav_clear_line` (which treats
        water/pits as solid for pathing); a cultist can see ACROSS a pit it
        cannot walk through, so sight must not reuse the nav predicate."""
        dx = self.world_dx(x0, x1)
        dy = self.world_dy(y0, y1)
        n = max(1, int(math.hypot(dx, dy) // step))
        for i in range(1, n + 1):
            if self.blocks_sight(x0 + dx * i / n, y0 + dy * i / n):
                return False
        return True

    def nav_path(self, fx, fy, tx, ty, max_visit=None):
        """Wrap-aware BFS over the walkable grid. Returns a list of world-
        centre points from the step AFTER the start up to the goal tile, or
        None if unreachable (caller falls back to a straight step).
        8-connected, with no diagonal corner-cutting through a solid."""
        from collections import deque
        g = self.nav_grid()
        w, h = self.w, self.h
        # Explore the whole (small) underground rooms fully; only the big
        # surface maps hit a bound -- there a far blocked goal is rare and a
        # straight fallback is fine. Sized so a reachable goal is never missed
        # in the rooms that actually have mid-floor cover.
        if max_visit is None:
            max_visit = min(w * h, 4000)

        def norm(i, j):
            if self.wrap_x:
                i %= w
            if self.wrap_y:
                j %= h
            return i, j

        def ok(i, j):
            i, j = norm(i, j)
            return 0 <= i < w and 0 <= j < h and g[j][i]

        si, sj = norm(int(fx // TILE), int(fy // TILE))
        gi, gj = norm(int(tx // TILE), int(ty // TILE))
        if (si, sj) == (gi, gj) or not ok(gi, gj):
            return None
        came = {(si, sj): None}
        q = deque([(si, sj)])
        found = False
        while q:
            ci, cj = q.popleft()
            if (ci, cj) == (gi, gj):
                found = True
                break
            if len(came) > max_visit:
                break
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nij = norm(ci + di, cj + dj)
                if nij in came or not ok(*nij):
                    continue
                if di and dj and not (ok(ci + di, cj) and ok(ci, cj + dj)):
                    continue                      # don't cut a solid corner
                came[nij] = (ci, cj)
                q.append(nij)
        if not found:
            return None
        path = []
        cur = (gi, gj)
        half = TILE // 2
        while cur is not None and cur != (si, sj):
            ci, cj = cur
            path.append((ci * TILE + half, cj * TILE + half))
            cur = came[cur]
        path.reverse()
        return path

    def nav_toward(self, fx, fy, tx, ty):
        """Immediate (sx, sy) a pursuer at (fx,fy) should step toward to reach
        (tx,ty) while routing around cover. Straight to the target when the
        line is clear; otherwise the FARTHEST path node still on a clear line
        (string-pulling, so motion arcs smoothly around corners rather than
        zig-zagging tile-to-tile). Returns the target unchanged when no route
        exists -- the caller's per-axis slide then nudges along the wall."""
        if self.nav_clear_line(fx, fy, tx, ty):
            return tx, ty
        path = self.nav_path(fx, fy, tx, ty)
        if not path:
            return tx, ty
        nxt = path[0]
        for p in path:
            if self.nav_clear_line(fx, fy, p[0], p[1]):
                nxt = p
            else:
                break
        return nxt

    def blocks_sight(self, x_px, y_px):
        """True where the tile occludes the player's LINE OF SIGHT (Phase 4
        blind-spot vision, rendering/sight.py). Walls and solid props block;
        windows do NOT (you see through glass), and the floor never blocks
        (water/pits don't hide what's beyond them). Wrap-aware via the
        char_*_at lookups."""
        ch = self.char_object_at(x_px, y_px)
        if ch in _WINDOW_CHARS:
            return False
        return ch in _WALL_CHARS or is_object_solid(ch)

    def is_solid_at(self, x_px, y_px, ignore=None):
        if is_object_solid(self.char_object_at(x_px, y_px)): return True
        if is_floor_solid(self.char_floor_at(x_px, y_px)): return True
        for npc in self.npcs:
            if npc is ignore or not npc.solid: continue
            # Wrap-aware proximity so NPC blocking still works across a
            # fold seam (raw abs() would miss a body one tile away on
            # the other side of the wrap).
            if (abs(self.world_dx(x_px, npc.x)) < 12
                    and abs(self.world_dy(y_px, npc.y)) < 12):
                return True
        return False

    def find_exit_at(self, x_px, y_px, facing=None):
        """Return the (target_scene, spawn) for the tile at the player
        position, or None. If the exit has a direction requirement and
        the player's facing doesn't match (dot product < 0.6), return
        None -- the tile reads as floor and the player walks over it.
        Used for fold-stitched hidden scenes that only open if you
        approach them from a specific direction."""
        ch = self.char_object_at(x_px, y_px)
        data = self.exits.get(ch)
        if data is None:
            return None
        required_dir = self.exit_directions.get(ch)
        if required_dir and facing is not None:
            vec = _DIRECTION_VECTORS.get(required_dir)
            if vec is not None:
                fx, fy = facing
                dx, dy = vec
                if (dx * fx + dy * fy) < 0.6:
                    return None
        return data

    def add_exit(self, char, target_scene, spawn_id="default",
                 direction=None):
        """Register an exit. `direction` (optional) is one of
        'north', 'south', 'east', 'west' -- the exit fires only when
        the player crosses the tile heading that way. Used for hidden
        fold scenes the player has to stumble into from a specific
        approach."""
        self.exits[char] = (target_scene, spawn_id)
        if direction:
            self.exit_directions[char] = direction

    def set_spawn(self, name, tx, ty):
        self.spawns[name] = (tx * TILE + TILE // 2, ty * TILE + TILE // 2)

    def add_npc(self, npc):
        self.npcs.append(npc)

    def add_decoration(self, deco):
        self.decorations.append(deco)

    def add_furniture(self, kind, tiles, **kw):
        """Place a sized furniture decoration centred over `tiles` (a
        list of (tx, ty)) and mark those tiles solid + invisible ('X')
        for collision -- so furniture can span several tiles (or sit shy
        of one) instead of reading as uniform 1-tile squares. `kw`
        (w, h, seed, color, ...) pass through to the decoration."""
        from entities.decoration import Decoration
        if self.objects and isinstance(self.objects[0], str):
            self.objects = [list(r) for r in self.objects]
        xs = [t[0] for t in tiles]
        ys = [t[1] for t in tiles]
        for tx, ty in tiles:
            if 0 <= ty < len(self.objects) and 0 <= tx < len(self.objects[ty]):
                self.objects[ty][tx] = "X"
        cx = (min(xs) * TILE + (max(xs) + 1) * TILE) // 2
        cy = (min(ys) * TILE + (max(ys) + 1) * TILE) // 2
        deco = Decoration(cx + kw.pop("dx", 0), cy + kw.pop("dy", 0), kind, **kw)
        self.add_decoration(deco)
        return deco

    def add_enemy(self, enemy):
        self.enemies.append(enemy)

    def add_item(self, x, y, key, qty=1, on_pickup=None):
        self.items.append({"x": x, "y": y, "key": key, "qty": qty, "on_pickup": on_pickup})

    def add_interactable(self, x, y, radius=40):
        """Register a point the [E] prompt should hover over -- for
        readables/pickups resolved in on_interact_fn (which the prompt
        system otherwise can't see)."""
        self.interactables.append((x, y, radius))

    def add_chalk_door(self, x, y, voice=None, seed=0, wall=False):
        """Place a chalk-drawn door (the cult's drawn-door compulsion) AND an
        [E]-examinable point. `wall=False` draws it flat on the FLOOR (a decal
        you'd step down into); `wall=True` hangs it on the nearest perimeter
        WALL. Examining one surfaces the PI's interior voice
        (Game._try_chalk_interact): the FIRST chalk door examined in a scene
        that set `voice` fires that beat; the rest give a brief flat line. Most
        chalk doors are placed voice-less -- they are the creeping VISUAL
        motif; only a few key ones carry a beat."""
        from entities.decoration import Decoration
        kind = "chalk_door_wall" if wall else "chalk_door"
        self.add_decoration(Decoration(x, y, kind, seed=seed))
        if not hasattr(self, "_chalk_doors"):
            self._chalk_doors = []
        self._chalk_doors.append((x, y))
        if voice is not None:
            self._chalk_voice = voice
        self.add_interactable(x, y, 40)

    def scatter_chalk_doors(self, count, seed=0, wall_count=0):
        """Obsessively fill an empty-feeling room with chalk doors -- drawn
        over and over, NONE overlapping. Places `count` floor doors on open
        interior tiles (min spacing) and `wall_count` against perimeter walls.
        These are the creeping VISUAL swarm: examinable (a flat line) but NOT
        [E]-prompted, so they don't spam the prompt. The one door that carries
        a voice beat is added separately via add_chalk_door(voice=...)."""
        import random as _r
        from entities.decoration import Decoration
        rng = _r.Random(seed * 131 + 7)
        W, H = self.w, self.h
        if not hasattr(self, "_chalk_doors"):
            self._chalk_doors = []
        taken = {(int(cx // TILE), int(cy // TILE)) for cx, cy in self._chalk_doors}
        # Keep clear of E-points (the desk/altar/etc.) so a swarmed door never
        # steals another interactable's press.
        inter = {(int(ix // TILE), int(iy // TILE))
                 for ix, iy, _ in self.interactables}

        def is_open(tx, ty):
            if not (1 <= tx < W - 1 and 1 <= ty < H - 1
                    and self.objects[ty][tx] == "."):
                return False
            return not any(abs(tx - ix) + abs(ty - iy) < 2 for ix, iy in inter)

        def place(cands, n, wall):
            laid = 0
            rng.shuffle(cands)
            for tx, ty in cands:
                if laid >= n:
                    break
                if any(abs(tx - ax) + abs(ty - ay) < 2 for ax, ay in taken):
                    continue
                self.add_decoration(Decoration(
                    tx * TILE + 16, ty * TILE + 16,
                    "chalk_door_wall" if wall else "chalk_door",
                    seed=rng.randint(1, 9999)))
                self._chalk_doors.append((tx * TILE + 16, ty * TILE + 16))
                taken.add((tx, ty))
                laid += 1

        floor = [(tx, ty) for ty in range(1, H - 1) for tx in range(1, W - 1)
                 if is_open(tx, ty)]
        place(list(floor), count, False)
        if wall_count:
            edge = [(tx, ty) for tx, ty in floor
                    if tx in (1, W - 2) or ty in (1, H - 2)]
            place(edge, wall_count, True)

    def find_marker(self, ch):
        for ty, r in enumerate(self.objects):
            for tx, c in enumerate(r):
                if c == ch:
                    return tx, ty
        return None

    def consume_marker(self, ch):
        pos = self.find_marker(ch)
        if pos:
            tx, ty = pos
            self.objects[ty][tx] = "."
            return tx, ty
        return None

    def update(self, dt, game):
        for npc in self.npcs:
            npc.update(dt, self, game.player)
        for d in self.decorations:
            d.update(dt)
        px, py = game.player.x, game.player.y
        for tr in self.triggers:
            if tr.get("once") and tr.get("fired"): continue
            x1, y1, x2, y2 = tr["rect"]
            if x1 <= px <= x2 and y1 <= py <= y2:
                tr["fired"] = True
                tr["fn"](game)
        if self.on_update_fn is not None:
            self.on_update_fn(game, self, dt)

    def draw(self, surf, cam_x, cam_y, camera=None):
        if self.wrap_x:
            x0 = int(cam_x // TILE) - 1
            x1 = int((cam_x + SCREEN_W) // TILE) + 2
        else:
            x0 = max(0, int(cam_x // TILE) - 1)
            x1 = min(self.w, int((cam_x + SCREEN_W) // TILE) + 2)
        if self.wrap_y:
            y0 = int(cam_y // TILE) - 1
            y1 = int((cam_y + SCREEN_H) // TILE) + 2
        else:
            y0 = max(0, int(cam_y // TILE) - 1)
            y1 = min(self.h, int((cam_y + SCREEN_H) // TILE) + 2)
        draw_scene_terrain(surf, self, cam_x, cam_y, x0, y0, x1, y1)
        world_w_px = self.w * TILE
        world_h_px = self.h * TILE
        for d in self.decorations:
            d.draw(surf, cam_x, cam_y, camera)
            # Wrap-clones so decorations stay in view across the seam.
            offsets = [(0, 0)]
            if self.wrap_x:
                offsets += [(-world_w_px, 0), (world_w_px, 0)]
            if self.wrap_y:
                offsets += [(0, -world_h_px), (0, world_h_px)]
            if self.wrap_x and self.wrap_y:
                offsets += [(-world_w_px, -world_h_px),
                            (-world_w_px, world_h_px),
                            (world_w_px, -world_h_px),
                            (world_w_px, world_h_px)]
            for dx_off, dy_off in offsets[1:]:
                # legacy path uses the shifted cam; camera path uses the
                # explicit world offset (the clone sits at self.pos + off).
                d.draw(surf, cam_x - dx_off, cam_y - dy_off, camera,
                       wox=dx_off, woy=dy_off)
        draw_scene_doors(surf, self, cam_x, cam_y, x0, y0, x1, y1)


def tile_footstep(ch):
    return floor_step_sound(ch)


def drop_ammo_cache(game, scene, tx, ty, qty, flag):
    """Place a one-time pistol_ammo pickup at tile (tx, ty), gated by a
    save flag so re-entering the scene can't farm infinite rounds. Called
    from a scene's on_enter_fn (needs game.save). Auto-picked on contact."""
    if game.save.flag(flag):
        return
    scene.add_item(tx * TILE + 16, ty * TILE + 16, "pistol_ammo", qty,
                   on_pickup=lambda g: g.save.set_flag(flag, True))


def chest_interact(game, scene, chest_x, chest_y, flag_key, loot,
                   key_required=None, range_px=44):
    """Generic chest interaction. Call from a scene's on_interact_fn
    after a proximity check is acceptable -- this helper does its own
    range check first, so a single on_interact_fn can chain multiple
    chest_interact() calls with early-return.

    Returns True if the chest was just opened (so the caller can
    short-circuit), False otherwise. Loot is a list of item keys; each
    entry is added to the player's inventory and surfaced in the
    notice queue. The chest's decoration is flipped to its `open`
    visual on a successful open."""
    if (abs(game.player.x - chest_x) > range_px
            or abs(game.player.y - chest_y) > range_px):
        return False
    if game.save.flag(flag_key):
        game.show_notice("Empty.")
        return True
    if key_required and not game.player.inventory.has(key_required):
        game.audio.play("door_locked", 0.7)
        game.show_notice("Locked.")
        return True
    game.save.set_flag(flag_key, True)
    from systems.items import ITEM_DEFS
    for item_key in loot:
        game.player.inventory.add(item_key, 1)
        d = ITEM_DEFS.get(item_key, {"name": item_key})
        game.show_notice(f"Got: {d['name']}.")
    game.audio.play("pickup_rare", 0.7)
    # Flip the chest decoration to its open visual.
    for deco in scene.decorations:
        if (deco.kind == "chest"
                and abs(deco.x - chest_x) < 8
                and abs(deco.y - chest_y) < 8):
            deco.kwargs["open"] = True
            break
    return True
