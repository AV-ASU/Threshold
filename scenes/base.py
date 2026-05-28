"""Scene primitives: tile definitions, tile-drawing helpers, the Scene
class itself. All scene builders consume these to define areas."""
import time
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
    "x": {"color": (28, 22, 30),   "step": "step_stone"},  # basement floor
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
    # to the brimley. Solid until the player swings a charged
    # lumber_axe at it, at which point Game._try_break_debris swaps
    # this tile to "4" (so the gap becomes a passage to brimley).
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
    # Q=guard, Y=fisherman, N=innkeeper (quest)
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
        # Tangled pile of fallen branches + planks. Solid until a
        # charged lumber_axe swing breaks it. Draw as a few crossed
        # logs over a low pile of leaves.
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
    pygame.draw.rect(surf, fd["color"], (rx, ry, TILE, TILE))
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
        if seed % 73 == 0:
            # Bone speck -- very rare. The kind of thing a player
            # only catches on the second or third walk through.
            pygame.draw.rect(surf, (210, 200, 180),
                             (rx + (seed * 3 % 28),
                              ry + (seed * 7 % 28), 1, 1))
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
        # Darker depths, slow dim ripples, patches of algae, and only a
        # rare cold glint instead of bright foam.
        seed = tx * 11 + ty * 23
        if seed % 3 == 0:                          # darker depth mottle
            pygame.draw.rect(surf, (17, 28, 30),
                             (rx + (seed % 22) + 2,
                              ry + ((seed // 5) % 22) + 2, 9, 6))
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
    "works_vats":           "the Tallow Vats",
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
# Door tiles cast the same floor-shadow as walls so a door in a south
# wall grounds into the building instead of leaving a lit threshold gap
# between the shadows of its flanking walls.
_DOOR_CHARS = frozenset(c for c, d in OBJECT_DEFS.items()
                        if d and d.get("kind") == "door")
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


def _draw_building_eaves(surf, scene, cam_x, cam_y, x0, y0, x1, y1):
    """Hang a ragged shingle eave + overhang shadow off the exterior
    walls of roofed buildings where they meet open ground, so a building
    reads as a structure with an overhanging roof instead of a flat
    rectangle stamped on the grass. Keyed off roof-adjacency, so ONLY
    roofed overworld houses get eaves -- interior room walls (no roof
    tile behind them) are left as the clean continuous mass."""
    objs = scene.objects
    h, w = scene.h, scene.w

    def roof(ax, ay):
        return 0 <= ay < h and 0 <= ax < w and objs[ay][ax] == "r"

    def openg(ax, ay):
        if not (0 <= ay < h and 0 <= ax < w):
            return False
        ch = objs[ay][ax]
        return ch not in _WALL_CHARS and ch != "r" and ch not in _DOOR_CHARS

    eave = (90, 58, 42)
    lip = (120, 82, 58)
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            if objs[ty][tx] not in _WALL_CHARS:
                continue
            if not (roof(tx, ty - 1) or roof(tx, ty + 1)
                    or roof(tx - 1, ty) or roof(tx + 1, ty)):
                continue
            rx = tx * TILE - cam_x
            ry = ty * TILE - cam_y
            j = (tx * 7 + ty * 13) & 3                 # irregular overhang depth
            if openg(tx, ty + 1):                      # south overhang (front)
                d = 5 + j
                _ground_shadow(surf, rx + TILE // 2, ry + TILE + d, 17, 4, 85)
                pygame.draw.rect(surf, eave, (rx, ry + TILE - 1, TILE, d))
                pygame.draw.rect(surf, lip, (rx, ry + TILE - 1 + d, TILE, 1))
            if openg(tx, ty - 1):                      # north (back)
                d = 3 + (j & 1)
                pygame.draw.rect(surf, eave, (rx, ry - d, TILE, d))
            if openg(tx - 1, ty):                      # west
                d = 4 + (j & 1)
                pygame.draw.rect(surf, eave, (rx - d, ry, d, TILE))
            if openg(tx + 1, ty):                      # east
                d = 4 + (j & 1)
                pygame.draw.rect(surf, eave, (rx + TILE, ry, d, TILE))


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


def draw_scene_terrain(surf, scene, cam_x, cam_y, x0, y0, x1, y1):
    """Floor -> path fringe -> wall-cast shadows -> continuous wall mass
    -> non-wall objects, for a tile window. Shared by Scene.draw (camera
    window) and the offline full-map renderer. When scene.wrap_x or
    .wrap_y is True, tile lookups wrap mod self.w / self.h so x0/x1 /
    y0/y1 may extend past the map bounds and the render stays seamless
    across the wrap line."""
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
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            draw_floor(surf, _lookup_floor(ty, tx),
                       tx * TILE - cam_x, ty * TILE - cam_y, tx, ty)
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            ch = _lookup_floor(ty, tx)
            if ch == "d":
                _draw_path_fringe(surf, scene, tx, ty,
                                  tx * TILE - cam_x, ty * TILE - cam_y)
            elif ch == "~":
                _draw_bank_fringe(surf, scene, tx, ty,
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
            rx = tx * TILE - cam_x
            ry = ty * TILE - cam_y
            if ch in _DOOR_CHARS:
                _draw_door_opening(surf, rx, ry, _door_room_dir(scene, tx, ty), tx, ty)
            else:
                draw_object(surf, ch, rx, ry, tx, ty)
    # Unified gabled roofs, drawn over the walls so each building reads
    # as one overhanging roof (door stays visible under the front eave).
    _draw_scene_roofs(surf, scene, cam_x, cam_y, x0, y0, x1, y1)


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
    try:
        grey = pygame.transform.grayscale(surf)
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

    def draw(self, surf, cam_x, cam_y):
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
            d.draw(surf, cam_x, cam_y)
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
                d.draw(surf, cam_x - dx_off, cam_y - dy_off)
        draw_scene_doors(surf, self, cam_x, cam_y, x0, y0, x1, y1)


def tile_footstep(ch):
    return floor_step_sound(ch)


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
