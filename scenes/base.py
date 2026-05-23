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
    # mistlands river enforces directional access via Game's
    # `_river_blocks` check (player.in_river state + designated entry
    # tile). Other scenes can still use `~` as decorative water; nothing
    # else currently does.
    "~": {"color": (30, 52, 78),   "step": "step_stone"},
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
}


OBJECT_DEFS = {
    ".": None,
    "#": {"solid": True, "kind": "stone_wall"},
    "W": {"solid": True, "kind": "wood_wall"},
    "T": {"solid": True, "kind": "tree"},
    "p": {"solid": False, "kind": "tree"},   # passable secret tree -- looks identical to T
    "C": {"solid": True, "kind": "cornstalk"},
    "R": {"solid": True, "kind": "rock"},
    "b": {"solid": True, "kind": "bed"},
    "t": {"solid": True, "kind": "table"},
    "c": {"solid": True, "kind": "chair"},
    "s": {"solid": True, "kind": "shelf"},
    "i": {"solid": True, "kind": "window"},
    "f": {"solid": True, "kind": "fireplace"},
    "k": {"solid": True, "kind": "stove"},
    "X": {"solid": True, "kind": "invisible"},
    "D": {"solid": False, "kind": "door"},
    "E": {"solid": False, "kind": "door"},   # depths chain east-exits
    "H": {"solid": False, "kind": "door"},
    "B": {"solid": False, "kind": "door"},
    "F": {"solid": False, "kind": "door"},
    "J": {"solid": False, "kind": "door"},   # door to kid_house interior
    # Per-house entry doors (each house in the new public square + the
    # Innkeeper's place in our_house_area gets its own char so the layout
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
    # Conditional doors in the player's main room. Both are placed by
    # house_on_enter only after their gating item has been picked up:
    # the son's-room door appears once the broken_crutch is in the
    # player's pack, the daughter's-room door once the old_doll has
    # been recovered. Pre-flag the wall is solid W (unrevealed).
    "1": {"solid": False, "kind": "door"},   # door to son_room
    "2": {"solid": False, "kind": "door"},   # door to daughter_room
    # Outdoor-passage style transition tiles -- non-solid, non-drawing
    # so the underlying floor (grass / water) shows through cleanly.
    # '4' is the village <-> mistlands corridor.
    "4": {"solid": False, "kind": "outdoor_passage"},
    # Bandit-cave sub-room doors (round-5 expansion: the cave splits into
    # a main room + 3 sub-rooms, one of which has the boss that yields
    # the LOGIN code).
    "u": {"solid": False, "kind": "door"},   # bandit cave -> boss room (north)
    "v": {"solid": False, "kind": "door"},   # bandit cave -> east sub-room
    "w": {"solid": False, "kind": "door"},   # bandit cave -> west sub-room
    # Fake wall: looks like a wood wall, passable. Used inside the
    # haunted_house red herring -- the player walks through it once to
    # find the symbol-portal room. After the portal is used, the scene
    # build replaces this with a real "W" so the route closes for good.
    "%": {"solid": False, "kind": "fake_wall"},
    # Stone fake wall: draws identically to a "#" but is passable. Used
    # in the bandit_cave_boss room as the conditional gate to the void
    # boss arena -- the wall is only made non-solid (kept as &) when the
    # player carries the broken_crutch and hasn't yet won or died at the
    # boss; otherwise the on_enter swaps it back to "#" for solid.
    "&": {"solid": False, "kind": "stone_wall"},
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
    # "!" -> diner_gas_station (used at east end of cornfield_path)
    "/": {"solid": False, "kind": "outdoor_passage"},
    "?": {"solid": False, "kind": "outdoor_passage"},
    "!": {"solid": False, "kind": "outdoor_passage"},
    # "^" -> generic north-edge exit char. Used by the cornfield
    # maze's hidden passage out the top of the field, but available
    # to any scene that needs a second outdoor passage distinct
    # from "!".
    "^": {"solid": False, "kind": "outdoor_passage"},
    # Round-12: breakable debris pile blocking the village's west exit
    # to the mistlands. Solid until the player swings a charged
    # lumber_axe at it, at which point Game._try_break_debris swaps
    # this tile to "4" (so the gap becomes a passage to mistlands).
    "*": {"solid": True,  "kind": "debris"},
    # Boarded panel -- a passage covered with cross-nailed wooden
    # boards. Visually distinct from a regular wood wall (X-cross
    # painted across the planks) and breakable with the splitting
    # axe. Used to gate side rooms and shortcut paths so finding
    # the axe genuinely opens up the map. Pressing E adjacent with
    # the axe converts the tile to ".".
    "q": {"solid": True,  "kind": "boarded"},
    # THRESHOLD: hand-authored loot crate. Solid until the player
    # swings a charged lumber_axe at it; on break, drops the item
    # registered in CRATE_LOOT for this (scene_key, tx, ty) and the
    # tile becomes walkable. Persistence via per-coord save flag so
    # broken crates stay broken across re-entries. Crates are
    # ALWAYS placed inside the playable area, never on the edge --
    # the gateway role is reserved for `*`.
    "K": {"solid": True,  "kind": "crate"},
    # Round-12: planked footbridge tile -- non-solid, drawn over a
    # river. Used in the mistlands to gap the N-S river at the bridge
    # rows.
    "$": {"solid": False, "kind": "bridge"},
    # Markers (consumed at scene-build time; never drawn)
    # P=basement photo, K=kid, S=shopkeep, O=oldman, M=mom, Z=basement note,
    # Q=guard, Y=fisherman, N=innkeeper (quest)
    "P": None, "K": None, "S": None, "O": None, "M": None, "Z": None,
    "Q": None, "Y": None, "N": None,
}


def draw_object(surf, ch, rx, ry):
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
        pygame.draw.rect(surf, (60, 40, 25), (rx + 13, ry + 22, 6, 10))
        pygame.draw.circle(surf, (24, 56, 30), (rx + 16, ry + 14), 14)
        pygame.draw.circle(surf, (40, 80, 46), (rx + 12, ry + 12), 6)
        pygame.draw.circle(surf, (40, 80, 46), (rx + 20, ry + 14), 5)
    elif kind == "cornstalk":
        # Per-tile jitter so rows never line up into a clean grid, and
        # muddier stalk colors to sit in the desaturated palette.
        rx += ((rx * 13 + ry * 7) % 7) - 3
        ry += ((rx * 5 + ry * 11) % 5) - 2
        t = pygame.time.get_ticks() / 600.0
        sway = int(math.sin(t + (rx + ry) * 0.07) * 1.5)
        for cx in (8, 16, 24):
            pygame.draw.line(surf, (78, 86, 46),
                             (rx + cx, ry + 30),
                             (rx + cx + sway, ry + 2), 2)
        for cx, cy in ((6, 6), (12, 10), (22, 6), (26, 12),
                       (10, 18), (20, 20)):
            pygame.draw.ellipse(surf, (96, 104, 54),
                                (rx + cx + sway, ry + cy, 8, 4))
        pygame.draw.ellipse(surf, (150, 134, 68),
                            (rx + 14 + sway, ry + 4, 4, 7))
    elif kind == "rock":
        pygame.draw.circle(surf, (100, 100, 110), (rx + 16, ry + 18), 12)
        pygame.draw.circle(surf, (70, 70, 80), (rx + 12, ry + 14), 4)
    elif kind == "bed":
        pygame.draw.rect(surf, (150, 142, 138), (rx + 3, ry + 6, 26, 22))
        pygame.draw.rect(surf, (120, 70, 78), (rx + 3, ry + 6, 26, 6))
        pygame.draw.rect(surf, (178, 170, 162), (rx + 5, ry + 8, 8, 4))
        pygame.draw.rect(surf, (66, 46, 32), (rx + 3, ry + 26, 26, 4))
        # An old stain, the kind that doesn't wash out.
        pygame.draw.rect(surf, (92, 84, 66), (rx + 17, ry + 16, 7, 7))
    elif kind == "table":
        pygame.draw.rect(surf, (160, 120, 90), (rx + 2, ry + 6, 28, 20))
        pygame.draw.rect(surf, (90, 60, 40), (rx + 2, ry + 22, 28, 6))
        pygame.draw.rect(surf, (90, 60, 40), (rx + 2, ry + 24, 4, 6))
        pygame.draw.rect(surf, (90, 60, 40), (rx + 26, ry + 24, 4, 6))
    elif kind == "chair":
        pygame.draw.rect(surf, (110, 80, 60), (rx + 8, ry + 14, 16, 14))
        pygame.draw.rect(surf, (90, 60, 40), (rx + 8, ry + 6, 16, 8))
    elif kind == "shelf":
        pygame.draw.rect(surf, (130, 100, 70), (rx + 2, ry + 2, 28, 28))
        pygame.draw.line(surf, (60, 40, 25), (rx + 2, ry + 12), (rx + 30, ry + 12), 2)
        pygame.draw.line(surf, (60, 40, 25), (rx + 2, ry + 22), (rx + 30, ry + 22), 2)
        for i in range(3):
            col = [(120, 60, 55), (66, 78, 110), (78, 104, 72)][i]
            pygame.draw.rect(surf, col, (rx + 4 + i * 8, ry + 4, 6, 6))
            pygame.draw.rect(surf, col, (rx + 4 + i * 8, ry + 14, 6, 6))
    elif kind == "window":
        # Wood frame + sky-blue glass. A faint dark vertical strip
        # passes left-to-right behind the glass on a slow per-tile
        # schedule -- a silhouette walking by outside. Most of the
        # cycle the strip is off-tile so the window reads as normal.
        # Per-tile seed via pygame.time + position so adjacent windows
        # don't pass the same figure at the same instant.
        pygame.draw.rect(surf, (96, 70, 50), (rx, ry, TILE, TILE))
        pygame.draw.rect(surf, (60, 40, 25), (rx, ry, TILE, TILE), 1)
        pygame.draw.rect(surf, (140, 170, 200), (rx + 6, ry + 6, 20, 20))
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
        pygame.draw.line(surf, (60, 60, 80), (rx + 16, ry + 6), (rx + 16, ry + 26), 1)
        pygame.draw.line(surf, (60, 60, 80), (rx + 6, ry + 16), (rx + 26, ry + 16), 1)
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
        pygame.draw.rect(surf, (50, 50, 56), (rx + 2, ry + 4, 28, 26))
        pygame.draw.rect(surf, (30, 30, 36), (rx + 2, ry + 4, 28, 26), 1)
        pygame.draw.circle(surf, (10, 10, 14), (rx + 10, ry + 12), 4)
        pygame.draw.circle(surf, (10, 10, 14), (rx + 22, ry + 12), 4)
        pygame.draw.rect(surf, (10, 10, 14), (rx + 6, ry + 18, 20, 10))
    elif kind == "door":
        # A doorframe + slab drawn OVER the floor -- no full-tile dark
        # fill. In a wall the jamb posts blend into the black mass; out
        # in the open they read as frame posts. Either way the floor
        # shows around it, so a door never becomes a black box jutting
        # out of the floor.
        pygame.draw.rect(surf, (10, 9, 12), (rx + 5, ry + 28, 22, 3))    # threshold shadow
        pygame.draw.rect(surf, (15, 14, 18), (rx + 5, ry + 3, 4, 27))    # left jamb
        pygame.draw.rect(surf, (15, 14, 18), (rx + 23, ry + 3, 4, 27))   # right jamb
        pygame.draw.rect(surf, (15, 14, 18), (rx + 5, ry + 3, 22, 3))    # head
        pygame.draw.rect(surf, (44, 32, 21), (rx + 9, ry + 5, 14, 24))   # frame
        pygame.draw.rect(surf, (57, 42, 26), (rx + 10, ry + 6, 12, 22))  # slab
        for sx in (14, 18):                                             # planks
            pygame.draw.line(surf, (37, 26, 15),
                             (rx + sx, ry + 7), (rx + sx, ry + 27), 1)
        # Ajar gap -- a real slice of black down the hinge edge.
        pygame.draw.rect(surf, (3, 2, 5), (rx + 10, ry + 6, 3, 22))
        pygame.draw.line(surf, (70, 53, 32), (rx + 13, ry + 6),
                         (rx + 13, ry + 27), 1)                          # lit jamb
        # Dim iron knob (no bright brass to draw the eye).
        pygame.draw.circle(surf, (112, 102, 88), (rx + 20, ry + 16), 2)
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
        pygame.draw.rect(surf, (96, 70, 40), (rx, ry, TILE, TILE))
        pygame.draw.line(surf, (50, 32, 18), (rx, ry + 6),
                         (rx + TILE, ry + 6), 1)
        pygame.draw.line(surf, (50, 32, 18), (rx, ry + 16),
                         (rx + TILE, ry + 16), 1)
        pygame.draw.line(surf, (50, 32, 18), (rx, ry + 26),
                         (rx + TILE, ry + 26), 1)
    elif kind == "roof":
        # Wood-shingle ridge stripe. Each tile draws three rows of shingles
        # offset to suggest the ridge runs east-west; deterministic per tile
        # via tx/ty so adjacent tiles align into a continuous roof surface.
        pygame.draw.rect(surf, (110, 70, 50), (rx, ry, TILE, TILE))
        for sy in range(3):
            row_y = ry + 2 + sy * 10
            offset = (sy & 1) * 4
            for sx in range(-1, 4):
                shingle_x = rx + offset + sx * 9
                pygame.draw.rect(surf, (140, 95, 70),
                                 (shingle_x, row_y, 8, 8))
                pygame.draw.line(surf, (60, 38, 24),
                                 (shingle_x, row_y + 8),
                                 (shingle_x + 8, row_y + 8), 1)
        # Central ridge highlight so the roof reads as a peaked surface
        pygame.draw.line(surf, (60, 38, 24),
                         (rx, ry + TILE // 2),
                         (rx + TILE, ry + TILE // 2), 1)


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
        # Wood plank floor with seam noise -- knots scattered
        # deterministically so old boards read as USED.
        pygame.draw.line(surf, (90, 60, 40),
                         (rx, ry + 10), (rx + TILE, ry + 10), 1)
        pygame.draw.line(surf, (90, 60, 40),
                         (rx, ry + 22), (rx + TILE, ry + 22), 1)
        if (tx + ty) % 3 == 0:
            pygame.draw.line(surf, (90, 60, 40),
                             (rx + 16, ry), (rx + 16, ry + 10), 1)
        # Dark knots
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
        # Water with two phase-offset ripples and a rare foam fleck.
        t = (tx + ty + pygame.time.get_ticks() // 200) % 8
        pygame.draw.rect(surf, (44, 68, 96),
                         (rx + t, ry + 8, 8, 2))
        pygame.draw.rect(surf, (44, 68, 96),
                         (rx + (t + 4) % TILE, ry + 22, 8, 2))
        seed = tx * 11 + ty * 23
        if seed % 13 == 0:
            pygame.draw.rect(surf, (120, 150, 175),
                             (rx + (seed % 28), ry + (seed * 5 % 28),
                              1, 1))
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
        # Basement / interior dirt floor -- cracks + dark stains.
        seed = tx * 19 + ty * 41
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
    "son_room":              "the Innkeeper's Room",
    "basement":             "the Cellar",
    "our_house_area":       "the Yard",
    "kid_house":            "the Kid's House",
    "village":              "Town Crossroads",
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
    "symbol_portal_room":   "the Stone Chamber",
    "mistlands":            "the River",
    "schoolhouse":          "the Schoolhouse",
    "graveyard":            "the Graveyard",
    "diner_gas_station":    "the Diner",
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
    if 0 <= ty < scene.h and 0 <= tx < scene.w:
        return scene.objects[ty][tx] in _WALL_CHARS
    return True   # off-map reads as wall so the mass closes at edges


def _draw_wall_mass(surf, scene, cam_x, cam_y, x0, y0, x1, y1):
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            if scene.objects[ty][tx] not in _WALL_CHARS:
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
            j = (hsh >> 3) & 1     # 1px edge jitter -> hand-drawn wobble
            if not _is_wall(scene, tx, ty - 1):     # room above: lit cap
                pygame.draw.rect(surf, _WALL_TOP, (rx, ry, TILE, 2))
                pygame.draw.line(surf, _WALL_FACE, (rx, ry + 2 + j),
                                 (rx + TILE, ry + 2 + j), 1)
            if not _is_wall(scene, tx, ty + 1):     # room below: foot shadow
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


def draw_scene_terrain(surf, scene, cam_x, cam_y, x0, y0, x1, y1):
    """Floor -> wall-cast shadows -> continuous wall mass -> non-wall
    objects, for a tile window. Shared by Scene.draw (camera window) and
    the offline full-map renderer."""
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            draw_floor(surf, scene.floor[ty][tx],
                       tx * TILE - cam_x, ty * TILE - cam_y, tx, ty)
    strip = _wall_shadow_strip()
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            ch = scene.objects[ty][tx]
            if ch in _SHADOW_CASTERS or ch in _DOOR_CHARS:
                surf.blit(strip, (tx * TILE - cam_x,
                                  (ty + 1) * TILE - cam_y))
    _draw_wall_mass(surf, scene, cam_x, cam_y, x0, y0, x1, y1)
    for ty in range(y0, y1):
        for tx in range(x0, x1):
            ch = scene.objects[ty][tx]
            if ch == "." or ch in _WALL_CHARS:
                continue
            draw_object(surf, ch, tx * TILE - cam_x, ty * TILE - cam_y)


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
        self.exits = {}
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

    def char_floor_at(self, x_px, y_px):
        tx = int(x_px // TILE); ty = int(y_px // TILE)
        if 0 <= ty < self.h and 0 <= tx < self.w:
            return self.floor[ty][tx]
        return "#"

    def char_object_at(self, x_px, y_px):
        tx = int(x_px // TILE); ty = int(y_px // TILE)
        if 0 <= ty < self.h and 0 <= tx < self.w:
            return self.objects[ty][tx]
        return "#"

    def is_solid_at(self, x_px, y_px, ignore=None):
        if is_object_solid(self.char_object_at(x_px, y_px)): return True
        if is_floor_solid(self.char_floor_at(x_px, y_px)): return True
        for npc in self.npcs:
            if npc is ignore or not npc.solid: continue
            if abs(npc.x - x_px) < 12 and abs(npc.y - y_px) < 12:
                return True
        return False

    def find_exit_at(self, x_px, y_px):
        ch = self.char_object_at(x_px, y_px)
        return self.exits.get(ch)

    def add_exit(self, char, target_scene, spawn_id="default"):
        self.exits[char] = (target_scene, spawn_id)

    def set_spawn(self, name, tx, ty):
        self.spawns[name] = (tx * TILE + TILE // 2, ty * TILE + TILE // 2)

    def add_npc(self, npc):
        self.npcs.append(npc)

    def add_decoration(self, deco):
        self.decorations.append(deco)

    def add_enemy(self, enemy):
        self.enemies.append(enemy)

    def add_item(self, x, y, key, qty=1, on_pickup=None):
        self.items.append({"x": x, "y": y, "key": key, "qty": qty, "on_pickup": on_pickup})

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
        x0 = max(0, int(cam_x // TILE) - 1)
        y0 = max(0, int(cam_y // TILE) - 1)
        x1 = min(self.w, int((cam_x + SCREEN_W) // TILE) + 2)
        y1 = min(self.h, int((cam_y + SCREEN_H) // TILE) + 2)
        draw_scene_terrain(surf, self, cam_x, cam_y, x0, y0, x1, y1)
        for d in self.decorations:
            d.draw(surf, cam_x, cam_y)


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
