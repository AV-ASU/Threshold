"""Animated decorative props (candles, smoke, the well, gore...).
Pure draw functions, no game logic."""
import time
import math
import random
import pygame
from constants import (
    SCREEN_W, SCREEN_H,
    C_BLACK, C_GOLD, C_RED,
)

# Compass-octant lookup. Index = 0..7 starting from EAST and walking
# clockwise (E, SE, S, SW, W, NW, N, NE). Each entry is a unit-circle
# offset; multiplied by per-axis travel inside _compass_offset.
_COMPASS_UNIT = (
    ( 1.0,  0.0),   # 0 E
    ( 0.7,  0.7),   # 1 SE
    ( 0.0,  1.0),   # 2 S
    (-0.7,  0.7),   # 3 SW
    (-1.0,  0.0),   # 4 W
    (-0.7, -0.7),   # 5 NW
    ( 0.0, -1.0),   # 6 N
    ( 0.7, -0.7),   # 7 NE
)


def _compass_offset(dx, dy, travel_x, travel_y):
    """Bucket a (dx, dy) world-vector into one of 8 compass directions
    (E, SE, S, SW, W, NW, N, NE) and return an integer (ox, oy) pixel
    offset capped to (travel_x, travel_y). Used by watching_eye and
    watching_wound to snap their tracking to discrete states instead
    of smooth analog drift -- the discrete shift is what the player's
    peripheral vision catches.

    `dx` is east-positive; `dy` is south-positive (screen coords).
    Player directly on top of the prop returns (0, 0). atan2 gives an
    angle in [-pi, pi]; we add pi/8 and divide by pi/4 so the
    quantisation lines up centred on each octant rather than on the
    octant boundary."""
    if abs(dx) < 1.0 and abs(dy) < 1.0:
        return (0, 0)
    ang = math.atan2(dy, dx)            # -pi..pi, 0=E, +pi/2=S
    # Shift so EAST sits at the centre of bucket 0, then floor.
    bucket = int(math.floor((ang + math.pi / 8) / (math.pi / 4))) % 8
    ux, uy = _COMPASS_UNIT[bucket]
    return (int(round(ux * travel_x)), int(round(uy * travel_y)))


# ---- Darkwood lighting helpers (mirror of scenes.base; kept local so
# entities/ doesn't import scenes/) ----
_DECO_SHADOW_CACHE = {}


def _ground_shadow(surf, cx, cy, rw, rh, alpha=80):
    key = (rw, rh, alpha)
    s = _DECO_SHADOW_CACHE.get(key)
    if s is None:
        s = pygame.Surface((rw * 2, rh * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, alpha), (0, 0, rw * 2, rh * 2))
        _DECO_SHADOW_CACHE[key] = s
    surf.blit(s, (int(cx - rw), int(cy - rh)))


_DECO_POOL_CACHE = {}


def _light_pool(surf, cx, cy, radius, color=(255, 170, 70), peak=70):
    key = (radius, color, peak)
    s = _DECO_POOL_CACHE.get(key)
    if s is None:
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        steps = 10
        for k in range(steps, 0, -1):
            r = max(1, int(radius * k / steps))
            a = int(peak * (1 - k / steps) ** 1.4) + 4
            pygame.draw.circle(s, (color[0], color[1], color[2], a),
                               (radius, radius), r)
        _DECO_POOL_CACHE[key] = s
    surf.blit(s, (int(cx - radius), int(cy - radius)))


_GROUNDED_DECOS = frozenset((
    "well", "creepy_tree", "pickup_truck", "player_car", "cauldron",
    "gas_pump", "payphone", "pedestal", "pillar", "wheelbarrow",
    "headstone", "brazier", "town_sign", "flagpole", "bush",
    "corn_doll", "corn_altar", "stalk_marker",
))

# Kinds that must NOT use the generic upscale path (they draw absolute
# light pools, track the player, animate ambiently, or are already large
# -- upscaling via a local canvas would misplace or clip them). The rug
# sizes itself via w/h kwargs instead, so it opts out too.
_NO_SCALE_DECOS = frozenset((
    "candle", "lantern", "brazier", "wall_torch", "swallow_hole",
    "smoke", "mist", "mote", "wisp",
    "flock", "leaves", "well", "steeple", "pickup_truck", "player_car",
    "cauldron", "watching_eye", "watching_wound", "passing_silhouette",
    "gas_pump", "payphone", "terminal", "computer", "mirror", "rug",
    "creepy_tree", "crow", "flock", "town_sign", "flagpole",
))


class Decoration:
    # Class-level player position cache. Game updates this every step
    # so a Decoration draw can read the player's world coords without
    # the draw signature having to plumb them through. Used by the
    # watching_eye to point its pupil at the player and by any future
    # tracking decoration.
    player_world = (0, 0)

    def __init__(self, x, y, kind, scale=1.0, seed=None, **kwargs):
        self.x = x; self.y = y
        self.kind = kind
        self.scale = scale
        self.t = random.uniform(0, 100)
        self.seed = seed if seed is not None else random.randint(0, 9999)
        self.kwargs = kwargs

    def update(self, dt):
        self.t += dt

    def draw(self, surf, cam_x, cam_y, camera=None, wox=0.0, woy=0.0,
             mount_z=0.0):
        # Route the point anchor through the shared projection when the live
        # game supplies a camera (CAMERA.md); fall back to the legacy
        # top-down conversion for headless tools that pass raw offsets. At
        # pitch 0 the two are arithmetically identical. `wox/woy` is the
        # wrap-clone world offset (0 for the primary draw), passed explicitly
        # so projection doesn't depend on the camera's pivot convention.
        # `mount_z` lifts the anchor off the ground (wall-hung decorations) so
        # the flat sprite reads as a card stood up the wall, not on the floor.
        if camera is not None:
            sx, sy = camera.project(self.x + wox, self.y + woy, mount_z)
        else:
            sx = int(self.x - cam_x)
            sy = int(self.y - cam_y)
        if sx < -64 or sx > SCREEN_W + 64 or sy < -64 or sy > SCREEN_H + 64:
            return
        if self.kind in _GROUNDED_DECOS:
            _ground_shadow(surf, sx, sy + 16, 13, 5, 75)
        drawfn = getattr(self, f"_draw_{self.kind}", self._draw_unknown)
        # Scale support: small static props/stains can be enlarged to
        # fill a room and break the tile grid. Opt-in (scale != 1.0), so
        # every existing 1.0 placement is byte-identical. Risky kinds
        # (lights, player-trackers, ambient, already-large) opt out.
        if self.scale != 1.0 and self.kind not in _NO_SCALE_DECOS:
            C = 48
            canvas = pygame.Surface((C * 2, C * 2), pygame.SRCALPHA)
            drawfn(canvas, C, C)
            side = max(1, int(C * 2 * self.scale))
            scaled = pygame.transform.scale(canvas, (side, side))
            surf.blit(scaled, (sx - side // 2, sy - side // 2))
        else:
            drawfn(surf, sx, sy)

    def _draw_unknown(self, surf, x, y):
        pygame.draw.rect(surf, (255, 0, 255), (x - 4, y - 4, 8, 8))

    # -- Flat (pitch-0 / F3) fallbacks for the volumetric props in
    #    rendering/props.py + the new box furniture. The tilt camera draws
    #    these as real solids; the flat top-down view uses these 2D sprites.
    def _draw_cistern_basin(self, surf, x, y):
        pygame.draw.ellipse(surf, (92, 96, 98), (x - 13, y - 9, 26, 18))
        pygame.draw.ellipse(surf, (50, 54, 56), (x - 13, y - 9, 26, 18), 1)
        pygame.draw.ellipse(surf, (14, 22, 26), (x - 9, y - 6, 18, 12))

    def _draw_swallow_hole(self, surf, x, y):
        """A sink where the river spirals down into the earth and is gone --
        the underground river's mouth (NARRATIVE 1b: the river is the artery;
        water finds the lowest place and creeps to the door). Depth rings that
        darken to black at the centre + a slow draining swirl. Used on the
        surface (the river vanishes here) and in the Sump (the same artery,
        deeper). `scale` kwarg sizes it."""
        # wet stone rim, irregular
        pygame.draw.ellipse(surf, (40, 42, 40), (x - 17, y - 12, 34, 24))
        pygame.draw.ellipse(surf, (62, 64, 60), (x - 17, y - 12, 34, 24), 1)
        # depth rings: water -> near-black at the centre (it goes DOWN)
        rings = [(48, 56, 58), (34, 44, 48), (22, 32, 36), (13, 20, 24),
                 (6, 11, 14), (2, 4, 6)]
        for i, col in enumerate(rings):
            rw = max(2, 14 - i * 2)
            rh = max(1, 10 - i * 2)
            pygame.draw.ellipse(surf, col, (x - rw, y - rh, rw * 2, rh * 2))
        # draining swirl: spiral arms rotating with time (the current going down)
        for arm in range(3):
            base = self.t * 1.8 + arm * (2 * math.pi / 3)
            pts = []
            for k in range(11):
                r = 2.0 + k * 1.15
                a = base + k * 0.5
                pts.append((x + math.cos(a) * r, y + math.sin(a) * r * 0.62))
            pygame.draw.lines(surf, (66, 80, 84), False, pts, 1)
        # a wet glint catching the light off the lip
        pygame.draw.line(surf, (104, 116, 118), (x - 10, y - 6), (x - 4, y - 8), 1)

    def _draw_grain_heap(self, surf, x, y):
        pygame.draw.circle(surf, (150, 126, 70), (x, y), 13)
        pygame.draw.circle(surf, (80, 64, 35), (x, y), 13, 1)
        pygame.draw.circle(surf, (198, 174, 110), (x - 3, y - 3), 5)

    def _draw_wall_torch(self, surf, x, y):
        # A wall sconce: an iron bracket rising off the wall with a guttering
        # flame at the top. The ROOM lighting is punched by Game._draw_dark
        # (which finds wall_torch decos); this is the visible fixture + a tight
        # flame halo. Drawn tall and anchored at the wall base so the billboard
        # reads as mounted up the wall.
        _light_pool(surf, x, y - 16, 28, (255, 170, 80), 78)
        pygame.draw.line(surf, (38, 34, 36), (x, y), (x, y - 14), 3)          # iron post
        pygame.draw.line(surf, (62, 56, 50), (x - 3, y - 14), (x + 3, y - 14), 2)  # cup
        f = math.sin(self.t * 16) + (random.random() - 0.5)
        fh = 11 + f * 2.2
        bx = x + int(math.sin(self.t * 9) * 1.2)                             # waver
        top = int(y - 15 - fh)
        pygame.draw.ellipse(surf, (190, 70, 24), (bx - 4, top, 8, int(fh)))           # ember
        pygame.draw.ellipse(surf, (245, 165, 48),
                            (bx - 3, int(y - 14 - fh * 0.78), 6, int(fh * 0.78)))     # body
        pygame.draw.ellipse(surf, (255, 236, 175),
                            (bx - 1, int(y - 13 - fh * 0.45), 3, int(fh * 0.45)))     # core

    def _draw_cot(self, surf, x, y):
        pygame.draw.rect(surf, (94, 65, 41), (x - 14, y - 7, 28, 14))
        pygame.draw.rect(surf, (52, 35, 22), (x - 14, y - 7, 28, 14), 1)
        pygame.draw.rect(surf, (150, 142, 128), (x - 12, y - 5, 24, 7))

    def _draw_bone_rack(self, surf, x, y):
        pygame.draw.rect(surf, (150, 144, 126), (x - 13, y - 6, 26, 12))
        pygame.draw.rect(surf, (104, 99, 86), (x - 13, y - 6, 26, 12), 1)
        for ox in (-7, 0, 7):
            pygame.draw.line(surf, (196, 190, 170),
                             (x + ox, y - 6), (x + ox, y + 6), 2)

    def _draw_pew(self, surf, x, y):
        pygame.draw.rect(surf, (72, 49, 31), (x - 20, y - 5, 40, 10))
        pygame.draw.rect(surf, (52, 35, 22), (x - 20, y - 5, 40, 10), 1)

    def _draw_doll(self, surf, x, y):
        """A small bound effigy -- cloth body, twine waist, stick arms,
        two dark X-marks for eyes. The cult's watching-charm, set on the
        charred edges around the cauldron clearing. ~14px tall."""
        # Drop shadow.
        sh = pygame.Surface((12, 5), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 90), (0, 0, 12, 5))
        surf.blit(sh, (x - 6, y + 5))
        cloth = (122, 96, 70)
        cloth_dk = (84, 64, 46)
        twine = (70, 48, 28)
        # Body wedge (skirt wider at the base).
        pygame.draw.polygon(surf, cloth_dk,
                            [(x - 4, y + 5), (x + 4, y + 5),
                             (x + 3, y - 4), (x - 3, y - 4)])
        pygame.draw.polygon(surf, cloth,
                            [(x - 3, y + 4), (x + 3, y + 4),
                             (x + 2, y - 3), (x - 2, y - 3)])
        # Stick arms + twine waist.
        pygame.draw.line(surf, twine, (x - 3, y - 1), (x - 6, y + 1), 1)
        pygame.draw.line(surf, twine, (x + 3, y - 1), (x + 6, y + 1), 1)
        pygame.draw.line(surf, twine, (x - 3, y + 1), (x + 3, y + 1), 1)
        # Head + two tiny X eyes.
        pygame.draw.circle(surf, cloth, (x, y - 6), 3)
        pygame.draw.circle(surf, cloth_dk, (x, y - 6), 3, 1)
        for ex in (x - 1, x + 2):
            pygame.draw.line(surf, (20, 16, 14), (ex - 1, y - 7), (ex, y - 6), 1)
            pygame.draw.line(surf, (20, 16, 14), (ex - 1, y - 6), (ex, y - 7), 1)

    def _draw_rope(self, surf, x, y):
        """A hanging cord -- a bell-pull / hoist line. A slightly kinked
        vertical rope with a frayed knot at the bottom; hangs from the
        prop placed above it. ~22px tall."""
        cord = (132, 110, 70)
        cord_dk = (92, 74, 44)
        top, bot = y - 11, y + 11
        midx = x + 1
        pygame.draw.line(surf, cord_dk, (x, top), (midx, y), 2)
        pygame.draw.line(surf, cord_dk, (midx, y), (x, bot), 2)
        pygame.draw.line(surf, cord, (x, top), (midx, y), 1)
        pygame.draw.line(surf, cord, (midx, y), (x, bot), 1)
        # Frayed knot.
        pygame.draw.circle(surf, cord_dk, (x, bot), 2)
        pygame.draw.line(surf, cord, (x - 2, bot + 2), (x, bot), 1)
        pygame.draw.line(surf, cord, (x + 2, bot + 3), (x, bot), 1)

    # ---- Sized darkwood furniture (drawn centred at x,y; pixel size
    # via w/h kwargs so a piece can span several tiles or sit shy of
    # one, breaking the tile grid). Collision is handled separately by
    # invisible solid 'X' tiles under the footprint. ----
    def _draw_bed(self, surf, x, y):
        w = int(self.kwargs.get("w", 56)); h = int(self.kwargs.get("h", 64))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (40, 29, 19), (rx, ry, w, h))             # frame
        pygame.draw.rect(surf, (22, 15, 9), (rx, ry, w, h), 1)
        ix, iy, iw, ih = rx + 3, ry + 3, w - 6, h - 6
        pygame.draw.rect(surf, (112, 104, 96), (ix, iy, iw, ih))         # mattress
        pygame.draw.rect(surf, (132, 124, 116), (ix, iy, iw, 2))         # lit top
        pygame.draw.rect(surf, (146, 138, 130), (ix + 3, iy + 3, iw - 6, h // 5))  # pillow
        pygame.draw.rect(surf, (118, 110, 102), (ix + 3, iy + 3 + h // 5, iw - 6, 1))
        by = iy + ih * 2 // 5
        pygame.draw.rect(surf, (86, 44, 48), (ix, by, iw, iy + ih - by)) # blanket
        pygame.draw.rect(surf, (108, 58, 62), (ix, by, iw, 2))           # lit edge
        pygame.draw.line(surf, (62, 32, 36), (x, by + 2), (x, iy + ih - 2), 1)  # fold
        pygame.draw.rect(surf, (58, 38, 30), (ix + iw // 2, by + ih // 4, 7, 6))  # stain

    def _draw_bookshelf(self, surf, x, y):
        # Long + shallow: sits flush to a wall, books leaning along it.
        w = int(self.kwargs.get("w", 58)); h = int(self.kwargs.get("h", 18))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (56, 41, 25), (rx, ry, w, h))             # case
        pygame.draw.rect(surf, (30, 22, 12), (rx, ry, w, h), 1)
        pygame.draw.rect(surf, (78, 58, 36), (rx, ry, w, 2))             # lit top rail
        pygame.draw.rect(surf, (24, 17, 9), (rx, ry + h - 2, w, 2))      # base shadow
        cols = [(92, 46, 42), (48, 58, 74), (56, 72, 48), (104, 86, 46), (74, 52, 78)]
        bx, i = rx + 3, 0
        while bx < rx + w - 3:
            bw = 3 + ((self.seed + i * 7) % 3)
            bh = (h - 6) - ((self.seed + i * 5) % 3)
            col = cols[i % len(cols)]
            pygame.draw.rect(surf, col, (bx, ry + h - 3 - bh, bw, bh))
            pygame.draw.rect(surf, (col[0] // 2, col[1] // 2, col[2] // 2),
                             (bx, ry + h - 3 - bh, bw, 1))
            bx += bw + 1; i += 1

    def _draw_table(self, surf, x, y):
        w = int(self.kwargs.get("w", 54)); h = int(self.kwargs.get("h", 38))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (40, 27, 16), (rx + 3, ry + h - 8, 5, 8))     # legs
        pygame.draw.rect(surf, (40, 27, 16), (rx + w - 8, ry + h - 8, 5, 8))
        th = h - 8
        pygame.draw.rect(surf, (74, 52, 32), (rx, ry, w, th))                # top
        pygame.draw.rect(surf, (96, 70, 44), (rx, ry, w, 2))                 # lit back
        pygame.draw.rect(surf, (40, 27, 16), (rx, ry + th - 3, w, 3))        # front lip
        for gx in range(rx + 8, rx + w - 4, 11):
            pygame.draw.line(surf, (56, 38, 22), (gx, ry + 4), (gx, ry + th - 5), 1)

    def _draw_chair(self, surf, x, y):
        w = int(self.kwargs.get("w", 22)); h = int(self.kwargs.get("h", 28))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (44, 30, 18), (rx + 3, ry + h - 6, 3, 6))     # legs
        pygame.draw.rect(surf, (44, 30, 18), (rx + w - 6, ry + h - 6, 3, 6))
        pygame.draw.rect(surf, (64, 44, 26), (rx + 2, ry, w - 4, h // 3))    # back
        pygame.draw.rect(surf, (78, 56, 34), (rx + 2, ry + h // 3, w - 4, h // 3 + 2))  # seat
        pygame.draw.rect(surf, (98, 72, 44), (rx + 2, ry + h // 3, w - 4, 2))

    def _draw_wardrobe(self, surf, x, y):
        # Tall + narrow: a standing cabinet against a wall, twin doors.
        w = int(self.kwargs.get("w", 26)); h = int(self.kwargs.get("h", 52))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (60, 44, 27), (rx, ry, w, h))                 # carcass
        pygame.draw.rect(surf, (30, 22, 12), (rx, ry, w, h), 1)
        pygame.draw.rect(surf, (82, 60, 38), (rx, ry, w, 2))                 # lit top
        pygame.draw.rect(surf, (24, 17, 9), (rx, ry + h - 3, w, 3))          # base shadow
        pygame.draw.line(surf, (32, 23, 13), (x, ry + 2), (x, ry + h - 2), 1)  # door split
        for hy in (ry + h // 2 - 4, ry + h // 2 + 2):                        # handles
            pygame.draw.rect(surf, (38, 27, 16), (x - 3, hy, 2, 4))
            pygame.draw.rect(surf, (38, 27, 16), (x + 2, hy, 2, 4))

    def _draw_stove(self, surf, x, y):
        # Cast-iron range drawn canonically facing DOWN (cooktop at top,
        # oven door + ember toward the bottom = the front). `wall` (N/E/S/W
        # = the wall it stands against) rotates it so the oven door faces
        # INTO the room off any wall -- e.g. wall="W" turns the front to
        # the east. Default "N" keeps the original south-facing look.
        w = int(self.kwargs.get("w", 34)); h = int(self.kwargs.get("h", 40))
        lay = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(lay, (42, 42, 48), (0, 0, w, h))                    # body
        pygame.draw.rect(lay, (60, 60, 68), (0, 0, w, 2))                    # lit top
        pygame.draw.rect(lay, (22, 22, 28), (0, h - 3, w, 3))                # base shadow
        pygame.draw.rect(lay, (28, 28, 34), (0, 0, w, h), 1)
        for cxk in (w // 3, 2 * w // 3):                                     # burners
            pygame.draw.circle(lay, (18, 18, 24), (cxk, 9), 4)
            pygame.draw.circle(lay, (10, 10, 14), (cxk, 9), 2)
        pygame.draw.rect(lay, (16, 16, 20), (4, h - 16, w - 8, 11))          # oven door
        pygame.draw.rect(lay, (70, 70, 78), (7, h - 17, w - 14, 2))          # handle
        pygame.draw.rect(lay, (200, 90, 30), (w // 2 - 5, h - 7, 10, 2))     # ember
        ang = {"N": 0, "E": -90, "S": 180, "W": 90}.get(
            self.kwargs.get("wall", "N"), 0)
        if ang:
            lay = pygame.transform.rotate(lay, ang)
        surf.blit(lay, (x - lay.get_width() // 2, y - lay.get_height() // 2))


    # ---- Northern-MN lodge decor (wall mounts draw face-on like the
    # photo/clock; floor pieces are placed via add_furniture). ----
    def _draw_buck_head(self, surf, x, y):
        # Mounted buck on a wood plaque. Drawn canonically facing DOWN
        # (mounted on a north wall, antlers toward the wall); `wall`
        # (N/E/S/W) rotates it to face into the room off any wall.
        lay = pygame.Surface((46, 48), pygame.SRCALPHA)
        cx, cy = 23, 27
        plaque = [(cx - 11, cy - 11), (cx + 11, cy - 11), (cx + 13, cy + 8),
                  (cx, cy + 13), (cx - 13, cy + 8)]
        pygame.draw.polygon(lay, (58, 42, 26), plaque)
        pygame.draw.polygon(lay, (34, 24, 14), plaque, 1)
        for s in (-1, 1):
            bx = cx + s * 5
            pygame.draw.line(lay, (118, 106, 82), (bx, cy - 7), (bx + s * 8, cy - 18), 2)
            pygame.draw.line(lay, (118, 106, 82), (bx + s * 3, cy - 11), (bx + s * 9, cy - 14), 1)
            pygame.draw.line(lay, (118, 106, 82), (bx + s * 5, cy - 14), (bx + s * 7, cy - 21), 1)
        pygame.draw.ellipse(lay, (72, 52, 36), (cx - 7, cy - 8, 14, 18))
        pygame.draw.ellipse(lay, (50, 36, 24), (cx - 7, cy - 8, 14, 18), 1)
        pygame.draw.ellipse(lay, (38, 27, 19), (cx - 4, cy + 4, 8, 6))
        pygame.draw.circle(lay, (18, 14, 10), (cx - 3, cy - 1), 2)
        pygame.draw.circle(lay, (18, 14, 10), (cx + 3, cy - 1), 2)
        pygame.draw.circle(lay, (130, 118, 96), (cx - 3, cy - 2), 1)
        ang = {"N": 0, "E": -90, "S": 180, "W": 90}.get(self.kwargs.get("wall", "N"), 0)
        if ang:
            lay = pygame.transform.rotate(lay, ang)
        surf.blit(lay, (x - lay.get_width() // 2, y - lay.get_height() // 2))

    def _draw_mounted_fish(self, surf, x, y):
        # A trophy walleye on a varnished board (always horizontal on the
        # wall). `flip` points the head the other way.
        lay = pygame.Surface((34, 16), pygame.SRCALPHA)
        cx, cy = 16, 8
        pygame.draw.rect(lay, (66, 48, 30), (0, cy - 7, 32, 14), border_radius=3)
        pygame.draw.rect(lay, (36, 26, 15), (0, cy - 7, 32, 14), 1)
        pygame.draw.ellipse(lay, (96, 104, 86), (cx - 12, cy - 4, 22, 8))
        pygame.draw.ellipse(lay, (70, 78, 62), (cx - 12, cy - 4, 22, 8), 1)
        pygame.draw.polygon(lay, (96, 104, 86), [(cx + 9, cy), (cx + 15, cy - 4), (cx + 15, cy + 4)])
        pygame.draw.polygon(lay, (80, 88, 70), [(cx - 2, cy - 4), (cx + 2, cy - 8), (cx + 4, cy - 4)])
        pygame.draw.line(lay, (60, 68, 54), (cx - 10, cy), (cx + 8, cy), 1)
        pygame.draw.circle(lay, (216, 206, 176), (cx - 9, cy - 1), 2)
        pygame.draw.circle(lay, (10, 10, 12), (cx - 9, cy - 1), 1)
        if self.kwargs.get("flip", False):
            lay = pygame.transform.flip(lay, True, False)
        surf.blit(lay, (x - lay.get_width() // 2, y - lay.get_height() // 2))

    def _draw_wrong_taxidermy(self, surf, x, y):
        # A mounted... thing -- a stoat or grouse, but the eyes are wrong:
        # too many, sickly-yellow, catching the light. Underground only.
        # `wall` rotates it to face into the room.
        lay = pygame.Surface((22, 20), pygame.SRCALPHA)
        cx, cy = 11, 10
        pygame.draw.rect(lay, (58, 42, 26), (cx - 10, cy - 9, 20, 18), border_radius=2)
        pygame.draw.rect(lay, (34, 24, 14), (cx - 10, cy - 9, 20, 18), 1)
        pygame.draw.ellipse(lay, (70, 56, 40), (cx - 7, cy - 6, 14, 12))
        pygame.draw.ellipse(lay, (48, 36, 24), (cx - 7, cy - 6, 14, 12), 1)
        rng = random.Random(self.seed)
        for _ in range(6):
            ex = cx - 5 + rng.randint(0, 10)
            ey = cy - 4 + rng.randint(0, 8)
            pygame.draw.circle(lay, (208, 196, 64), (ex, ey), 1)
        ang = {"N": 0, "E": -90, "S": 180, "W": 90}.get(self.kwargs.get("wall", "N"), 0)
        if ang:
            lay = pygame.transform.rotate(lay, ang)
        surf.blit(lay, (x - lay.get_width() // 2, y - lay.get_height() // 2))

    def _draw_cobweb(self, surf, x, y):
        # A faint corner cobweb: radial threads + a few connecting arcs.
        # `ang` kwarg points it into the corner it hangs from.
        col = (118, 118, 130)
        base = self.kwargs.get("ang", 0.0)
        span = math.pi / 2
        n = 5
        R = int(self.kwargs.get("r", 17))
        for i in range(n):
            a = base + span * (i / (n - 1))
            pygame.draw.line(surf, col, (x, y),
                             (int(x + math.cos(a) * R), int(y + math.sin(a) * R)), 1)
        for ring in (R // 3, 2 * R // 3, R - 1):
            pts = [(int(x + math.cos(base + span * (i / (n - 1))) * ring),
                    int(y + math.sin(base + span * (i / (n - 1))) * ring))
                   for i in range(n)]
            pygame.draw.lines(surf, col, False, pts, 1)

    def _draw_kerosene_lamp(self, surf, x, y):
        # A brass oil lamp: warm pool, a fuel font, a glass chimney, flame.
        _light_pool(surf, x, y - 4, 30, (255, 168, 80), 60)
        pygame.draw.rect(surf, (96, 74, 40), (x - 5, y + 3, 10, 4))        # base
        pygame.draw.polygon(surf, (120, 96, 56),
                            [(x - 4, y + 3), (x + 4, y + 3), (x + 2, y - 3), (x - 2, y - 3)])  # font
        chim = pygame.Surface((10, 12), pygame.SRCALPHA)
        pygame.draw.polygon(chim, (210, 196, 150, 80), [(2, 11), (8, 11), (7, 0), (3, 0)])
        surf.blit(chim, (x - 5, y - 15))
        fh = 5 + math.sin(self.t * 16 + self.seed) * 1.2
        pygame.draw.polygon(surf, (255, 206, 96),
                            [(x, int(y - 4 - fh)), (x - 2, y - 4), (x + 2, y - 4)])

    def _draw_firewood(self, surf, x, y):
        # A stack of split logs -- pale ringed ends in a dark cradle.
        w = int(self.kwargs.get("w", 40)); h = int(self.kwargs.get("h", 24))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (38, 27, 17), (rx, ry, w, h))
        pygame.draw.rect(surf, (24, 17, 10), (rx, ry, w, h), 1)
        r = 5
        row = 0
        oy = ry + r + 1
        while oy < ry + h - 1:
            cx = rx + r + 1 + (row % 2) * r
            while cx < rx + w - 1:
                pygame.draw.circle(surf, (92, 68, 44), (cx, oy), r)
                pygame.draw.circle(surf, (58, 40, 24), (cx, oy), r, 1)
                pygame.draw.circle(surf, (120, 92, 60), (cx, oy), max(1, r - 2), 1)
                cx += r * 2
            oy += r * 2 - 1
            row += 1

    def _draw_antler_rack(self, surf, x, y):
        # An antler/branch coat-rack: a post on a base, antler arms up
        # top, a dark wool coat hung from it.
        h = int(self.kwargs.get("h", 46))
        top = y - h // 2 + 6
        pygame.draw.ellipse(surf, (34, 24, 14), (x - 7, y + h // 2 - 8, 14, 7))  # base
        pygame.draw.rect(surf, (48, 34, 20), (x - 2, top, 4, h - 12))            # post
        for s in (-1, 1):
            pygame.draw.line(surf, (118, 106, 82), (x, top), (x + s * 9, top - 7), 2)
            pygame.draw.line(surf, (118, 106, 82), (x + s * 5, top - 3), (x + s * 8, top - 10), 1)
        coat = [(x - 7, top + 3), (x + 7, top + 3), (x + 5, y + 8), (x - 5, y + 8)]
        pygame.draw.polygon(surf, (46, 44, 50), coat)                           # hung coat
        pygame.draw.polygon(surf, (28, 26, 32), coat, 1)

    def _draw_rug(self, surf, x, y):
        """A worn area rug -- a multi-tile floor covering (w x h px via
        kwargs) that breaks up the plank grid. Faded field, a woven
        border, a centre motif, fringe at the ends, and a few worn
        patches. Drawn flat on the floor, under furniture/props."""
        w = int(self.kwargs.get("w", 88))
        h = int(self.kwargs.get("h", 60))
        base = self.kwargs.get("color", (96, 44, 46))
        border = tuple(min(255, int(c * 1.5) + 18) for c in base)
        dark = tuple(int(c * 0.6) for c in base)
        rx, ry = x - w // 2, y - h // 2
        sh = pygame.Surface((w + 10, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 55), (0, 0, w + 10, 16))
        surf.blit(sh, (rx - 5, ry + h - 8))
        pygame.draw.rect(surf, base, (rx, ry, w, h), border_radius=3)
        pygame.draw.rect(surf, dark, (rx, ry, w, h), 1, border_radius=3)
        pygame.draw.rect(surf, border, (rx + 3, ry + 3, w - 6, h - 6), 2)
        pygame.draw.polygon(surf, border, [
            (x, ry + 8), (rx + w - 8, y), (x, ry + h - 8), (rx + 8, y)], 1)
        pygame.draw.circle(surf, border, (x, y), 3, 1)
        for fxp in range(rx + 4, rx + w - 3, 5):       # fringe at the ends
            pygame.draw.line(surf, border, (fxp, ry - 2), (fxp, ry), 1)
            pygame.draw.line(surf, border, (fxp, ry + h), (fxp, ry + h + 2), 1)
        for i in range(3):                             # worn patches
            wx = rx + 6 + (self.seed * (i + 1)) % max(1, w - 12)
            wy = ry + 6 + (self.seed * (i + 3)) % max(1, h - 12)
            pygame.draw.rect(surf, dark, (wx, wy, 4, 3))

    def _draw_candle(self, surf, x, y):
        _light_pool(surf, x, y - 2, 30, (255, 170, 80), 58)
        pygame.draw.rect(surf, (180, 180, 200), (x - 2, y, 4, 8))
        pygame.draw.rect(surf, (240, 230, 200), (x - 1, y - 4, 2, 4))
        f_h = 6 + math.sin(self.t * 18) * 1 + (random.random() - 0.5)
        f_w = 3 + math.sin(self.t * 13) * 0.5
        # Optional scripted dip: the flame nearly snuffs and re-grows
        # over ~0.7s when something passes the candle (the opening
        # watcher manifestation cue). Set kwargs["dip_t0"] = time.time()
        # to fire. Outside the dip window the candle is unchanged.
        dip_t0 = self.kwargs.get("dip_t0", 0.0)
        if dip_t0:
            elapsed = time.time() - dip_t0
            if 0.0 <= elapsed < 0.7:
                if elapsed < 0.15:
                    dim = 1.0 - (elapsed / 0.15) * 0.70
                else:
                    dim = 0.30 + 0.70 * ((elapsed - 0.15) / 0.55)
                f_h *= dim
                f_w *= dim
        pygame.draw.polygon(surf, (255, 200, 80), [(x, y - 4 - f_h), (x - f_w, y - 4), (x + f_w, y - 4)])
        pygame.draw.polygon(surf, (255, 240, 180),
                            [(x, y - 4 - f_h * 0.7), (x - f_w * 0.5, y - 4), (x + f_w * 0.5, y - 4)])

    def _draw_mud_footprint(self, surf, x, y):
        # A single BOOT print -- one connected sole (rounded toe/ball, a
        # narrow arch, a heel) with a faint tread, NOT separate toe dabs
        # (which read as an animal paw). `dir` (0..3) rotates it so a
        # trail suggests direction; `alpha` fades it.
        d = self.kwargs.get("dir", 0)
        a = max(20, min(220, int(self.kwargs.get("alpha", 180))))
        layer = pygame.Surface((16, 22), pygame.SRCALPHA)
        col = (32, 22, 14, a)
        tread = (22, 15, 9, a)
        # Ball of the foot (front), wide and rounded.
        pygame.draw.ellipse(layer, col, (3, 1, 10, 12))
        # Arch / instep -- a narrow waist linking the ball to the heel.
        pygame.draw.rect(layer, col, (5, 9, 6, 8))
        # Heel -- rounded, a touch narrower than the ball.
        pygame.draw.ellipse(layer, col, (4, 14, 8, 8))
        # Tread bars: two across the ball, one across the heel.
        pygame.draw.line(layer, tread, (4, 5), (11, 5), 1)
        pygame.draw.line(layer, tread, (4, 8), (11, 8), 1)
        pygame.draw.line(layer, tread, (5, 18), (10, 18), 1)
        # rotate per direction (0=up, 1=right, 2=down, 3=left)
        if d:
            layer = pygame.transform.rotate(layer, -90 * d)
        surf.blit(layer, (x - layer.get_width() // 2,
                          y - layer.get_height() // 2))

    def _draw_calendar(self, surf, x, y):
        """Stripped-down wall calendar. Just the month abbreviation
        and the day number on a small paper card -- no grid, no X
        marks, no week-day headers. Reads kwargs:
          today_d -- 1-based day-of-month for the current day
          month   -- numeric month (10, 11, 12, or 1)
        `month_days` is still accepted for compatibility but ignored.

        The Game advances `today_d` and `month` on each sleep; this
        prop just rerenders the new label. Cached SysFont surface so
        we don't re-rasterise every frame."""
        today_d = self.kwargs.get("today_d", 4)
        month = self.kwargs.get("month", 10)
        # Paper. Smaller now that the grid is gone -- a tear-off
        # day-card pinned to the wall.
        paper_w, paper_h = 26, 26
        px = x - paper_w // 2
        py = y - paper_h // 2
        pygame.draw.rect(surf, (224, 218, 200), (px, py, paper_w, paper_h))
        pygame.draw.rect(surf, (50, 40, 30), (px, py, paper_w, paper_h), 1)
        # Header band carries the month abbreviation.
        pygame.draw.rect(surf, (40, 30, 24), (px, py, paper_w, 8))
        name = {10: "OCT", 11: "NOV", 12: "DEC", 1: "JAN"}.get(month, "OCT")
        # The day number, big and centred on the lower portion.
        day_str = str(today_d)
        try:
            cache = self.kwargs.get("_label_cache")
            cache_key = self.kwargs.get("_label_cache_key")
            target_key = (name, day_str)
            if cache is None or cache_key != target_key:
                month_font = pygame.font.SysFont(None, 10)
                day_font = pygame.font.SysFont(None, 18)
                month_surf = month_font.render(
                    name, False, (224, 218, 200))
                day_surf = day_font.render(
                    day_str, False, (40, 30, 24))
                cache = (month_surf, day_surf)
                self.kwargs["_label_cache"] = cache
                self.kwargs["_label_cache_key"] = target_key
            month_surf, day_surf = cache
            surf.blit(month_surf,
                      (px + (paper_w - month_surf.get_width()) // 2,
                       py + 1))
            surf.blit(day_surf,
                      (px + (paper_w - day_surf.get_width()) // 2,
                       py + 9))
        except Exception:
            pass

    def _draw_wheelbarrow(self, surf, x, y):
        """Single-wheel wooden wheelbarrow seen from a 3/4 angle.
        Loaded with a small pile of rusted hand tools (claw hammer
        head, bent wrench, the tip of a saw). The tools are
        deliberately drawn looking dirty/old at distance, but the
        scene's interaction text ('these have been recently
        cleaned') contradicts what the player is seeing -- the
        horror is in the contradiction. Static, not animated."""
        # Tray (the bucket of the wheelbarrow). Trapezoid with a
        # darker rim. Brown weathered wood.
        tray_top_w = 26
        tray_bot_w = 18
        tray_h = 10
        tray_top_y = y - 4
        # Use polygon for the trapezoid silhouette.
        pygame.draw.polygon(surf, (110, 78, 50), [
            (x - tray_top_w // 2, tray_top_y),
            (x + tray_top_w // 2, tray_top_y),
            (x + tray_bot_w // 2, tray_top_y + tray_h),
            (x - tray_bot_w // 2, tray_top_y + tray_h),
        ])
        pygame.draw.polygon(surf, (60, 40, 24), [
            (x - tray_top_w // 2, tray_top_y),
            (x + tray_top_w // 2, tray_top_y),
            (x + tray_bot_w // 2, tray_top_y + tray_h),
            (x - tray_bot_w // 2, tray_top_y + tray_h),
        ], 1)
        # Plank seam across the tray.
        pygame.draw.line(surf, (60, 40, 24),
                         (x - tray_top_w // 2 + 2, tray_top_y + tray_h // 2),
                         (x + tray_top_w // 2 - 2, tray_top_y + tray_h // 2), 1)
        # Two front legs poking down past the tray.
        pygame.draw.rect(surf, (60, 40, 24), (x - 9, tray_top_y + tray_h, 2, 5))
        pygame.draw.rect(surf, (60, 40, 24), (x + 7, tray_top_y + tray_h, 2, 5))
        # Wheel out the front.
        pygame.draw.circle(surf, (40, 28, 20), (x - 12, y + 3), 4)
        pygame.draw.circle(surf, (16, 12, 10), (x - 12, y + 3), 4, 1)
        pygame.draw.line(surf, (90, 70, 50), (x - 16, y + 3),
                         (x - 8, y + 3), 1)
        # Long handle running back-right (the user's grip end).
        pygame.draw.line(surf, (90, 60, 36),
                         (x + 12, y), (x + 18, y + 5), 2)
        # Tools poking out of the tray. Rusty steel + dark wood.
        # Hammer head (rectangular block with a dark eye for the haft).
        pygame.draw.rect(surf, (130, 90, 70), (x - 4, tray_top_y - 4, 5, 4))
        pygame.draw.rect(surf, (60, 40, 30), (x - 4, tray_top_y - 4, 5, 4), 1)
        pygame.draw.rect(surf, (60, 40, 30), (x - 2, tray_top_y - 3, 1, 2))
        # Wrench at an angle (a bent steel rod with a notched head).
        pygame.draw.line(surf, (140, 110, 90),
                         (x + 2, tray_top_y - 2),
                         (x + 9, tray_top_y - 6), 2)
        pygame.draw.rect(surf, (140, 110, 90),
                         (x + 8, tray_top_y - 8, 3, 4))
        pygame.draw.rect(surf, (60, 40, 30),
                         (x + 8, tray_top_y - 8, 3, 4), 1)
        # Saw tip protruding (a small triangle of toothed steel).
        pygame.draw.polygon(surf, (170, 150, 140), [
            (x - 8, tray_top_y - 1),
            (x - 1, tray_top_y - 6),
            (x - 1, tray_top_y - 4),
        ])
        # Rust streaks down the tray face.
        pygame.draw.line(surf, (130, 60, 30),
                         (x - 6, tray_top_y + 2),
                         (x - 5, tray_top_y + tray_h - 1), 1)
        pygame.draw.line(surf, (130, 60, 30),
                         (x + 4, tray_top_y + 1),
                         (x + 4, tray_top_y + tray_h - 1), 1)

    def _draw_watching_wound(self, surf, x, y):
        """Vertical slit-cut on a stone or bark surface, with a wet
        glint at the edge that catches the player's facing. Reads as
        an open wound rather than an eye -- no iris, no pupil. The
        glint is what tracks; the wound itself is just a dark cut.

        Same `size` kwarg as `watching_eye` (small / large). Designed
        to be placed alongside watching_eye decorations so the cult
        marks read as a mix of literal eyes and abstract cuts. The
        gaze sensation comes from the moving glint, not from a pupil
        the player can see directly."""
        size = self.kwargs.get("size", "small")
        if size == "large":
            slit_w, slit_h = 6, 28
            glint_w = 4
        else:
            slit_w, slit_h = 3, 14
            glint_w = 2
        # The cut itself -- a dark vertical slot. Slight outer halo
        # of bruised tissue where the surface has parted.
        pygame.draw.ellipse(surf, (60, 30, 32),
                            (x - slit_w // 2 - 2, y - slit_h // 2 - 2,
                             slit_w + 4, slit_h + 4))
        pygame.draw.ellipse(surf, (8, 4, 8),
                            (x - slit_w // 2, y - slit_h // 2,
                             slit_w, slit_h))
        # A thin rim of dried-blood smear around the rim.
        pygame.draw.ellipse(surf, (90, 22, 28),
                            (x - slit_w // 2, y - slit_h // 2,
                             slit_w, slit_h), 1)
        # The wet glint -- a 1-2px streak inside the cut. Snaps to one
        # of 8 compass positions inside the slit based on where the
        # player is standing. The discrete shift is what catches
        # peripheral vision; the player notices the wound's eye dart
        # as they cross a diagonal.
        ox, oy = _compass_offset(
            Decoration.player_world[0] - self.x,
            Decoration.player_world[1] - self.y,
            travel_x=max(1, slit_w // 4),
            travel_y=max(1, slit_h // 3),
        )
        # A slow wet pulse so the glint doesn't sit static.
        pulse = 0.7 + 0.3 * math.sin(self.t * 1.4 + self.seed)
        glint_alpha = max(40, int(180 * pulse))
        layer = pygame.Surface((slit_w + 4, slit_h + 4),
                                pygame.SRCALPHA)
        pygame.draw.rect(layer, (220, 210, 200, glint_alpha),
                         (slit_w // 2 + 2 + ox - glint_w // 2,
                          slit_h // 2 + oy,
                          glint_w, 2))
        surf.blit(layer, (x - (slit_w + 4) // 2,
                          y - (slit_h + 4) // 2))

    def _draw_passing_silhouette(self, surf, x, y):
        # One-shot scripted silhouette: a dark vertical strip drifts
        # left-to-right across the window glass over `dur` seconds
        # starting at `t0`. Outside that window the decoration is
        # invisible; the scene removes it after dur+1.
        t0 = self.kwargs.get("t0", 0.0)
        dur = self.kwargs.get("dur", 1.8)
        if not t0:
            return
        elapsed = time.time() - t0
        if elapsed < 0.0 or elapsed > dur:
            return
        phase = elapsed / dur            # 0..1 across the glass
        # Window glass spans roughly +/-10px around (x, y). Strip is
        # 3px wide, 18px tall; soft edges via per-column alpha.
        fx = int(x - 12 + phase * 24)
        strip = pygame.Surface((4, 20), pygame.SRCALPHA)
        for col_x in range(4):
            edge = 1.0 - abs(col_x - 1.5) / 1.8
            a = max(0, int(170 * edge))
            pygame.draw.rect(strip, (8, 6, 14, a), (col_x, 0, 1, 20))
        surf.blit(strip, (fx, y - 10))

    def _draw_lantern(self, surf, x, y):
        # Lamppost: vertical iron pole grounded at y+18, cross-arm at the
        # top, lantern hangs from the arm tip. Earlier rounds drew only
        # the lantern + a stub of chain, which read as floating in the
        # corridor. The pole anchors it to the ground.
        _light_pool(surf, x + 8, y, 40, (255, 175, 80), 72)
        ground_y = y + 18
        top_y = y - 22
        # vertical pole
        pygame.draw.line(surf, (50, 50, 60), (x, ground_y), (x, top_y), 2)
        # base flare
        pygame.draw.rect(surf, (50, 50, 60), (x - 3, ground_y - 1, 7, 3))
        # cross-arm reaching right to where the lantern hangs
        pygame.draw.line(surf, (50, 50, 60), (x, top_y), (x + 8, top_y), 2)
        sway = math.sin(self.t * 1.2 + self.seed) * 1
        # short chain from arm tip down to lantern body
        pygame.draw.line(surf, (60, 60, 70),
                         (x + 8, top_y),
                         (x + 8 + sway, y - 6), 1)
        # lantern body
        pygame.draw.rect(surf, (80, 60, 30), (x + 3 + sway, y - 6, 10, 12))
        flick = (255, 200 + int(math.sin(self.t * 20) * 20), 80)
        pygame.draw.rect(surf, flick, (x + 5 + sway, y - 4, 6, 8))

    def _draw_smoke(self, surf, x, y):
        for i in range(4):
            phase = (self.t * 0.6 + i * 0.4 + self.seed * 0.1) % 1.0
            ox = math.sin(phase * 6 + self.seed) * 3
            oy = -phase * 36
            r = int(4 + phase * 6)
            alpha = int((1 - phase) * 130)
            puff = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(puff, (160, 160, 170, alpha), (r + 1, r + 1), r)
            surf.blit(puff, (x + ox - r, y + oy - r))

    def _draw_clock(self, surf, x, y):
        pygame.draw.rect(surf, (90, 60, 40), (x - 8, y - 16, 16, 28))
        pygame.draw.rect(surf, (40, 25, 15), (x - 8, y - 16, 16, 28), 1)
        pygame.draw.circle(surf, (240, 230, 210), (x, y - 8), 6)
        pygame.draw.circle(surf, (40, 25, 15), (x, y - 8), 6, 1)
        pygame.draw.line(surf, C_BLACK, (x, y - 13), (x, y - 12), 1)
        pygame.draw.line(surf, C_BLACK, (x, y - 4), (x, y - 3), 1)
        minute = self.t * 0.05
        second = math.floor(self.t * 1.0) * (math.pi / 30)
        mx = x + math.cos(minute - math.pi / 2) * 4
        my = (y - 8) + math.sin(minute - math.pi / 2) * 4
        pygame.draw.line(surf, C_BLACK, (x, y - 8), (mx, my), 1)
        sx2 = x + math.cos(second - math.pi / 2) * 5
        sy2 = (y - 8) + math.sin(second - math.pi / 2) * 5
        pygame.draw.line(surf, C_RED, (x, y - 8), (sx2, sy2), 1)
        sw = math.sin(self.t * 2) * 3
        pygame.draw.line(surf, (40, 25, 15), (x, y - 4), (x + sw, y + 8), 1)
        pygame.draw.circle(surf, (200, 180, 60), (int(x + sw), y + 8), 2)

    def _draw_meat(self, surf, x, y):
        # A haunch of meat hung on a hook: a rounded red slab with fat
        # marbling and a pale bone nub at the base, swaying slightly,
        # the occasional drip. Reads clearly as hung meat / a larder.
        sway = math.sin(self.t * 0.8 + self.seed) * 1.5
        cx = int(x + sway)
        # Hook + the line it hangs from.
        pygame.draw.line(surf, (150, 150, 162), (x, y - 18), (x, y - 9), 2)
        pygame.draw.line(surf, (150, 150, 162), (x, y - 9), (cx - 3, y - 7), 2)
        # Haunch body on its own layer so the shape reads cleanly.
        body = pygame.Surface((24, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(body, (118, 26, 34), (3, 0, 18, 22))      # meat
        pygame.draw.ellipse(body, (150, 44, 52), (6, 3, 11, 12))      # lit side
        pygame.draw.ellipse(body, (86, 16, 24), (3, 0, 18, 22), 1)    # rim
        pygame.draw.line(body, (196, 152, 150), (7, 9), (16, 13), 1)  # fat
        pygame.draw.line(body, (196, 152, 150), (6, 14), (14, 17), 1)
        pygame.draw.rect(body, (222, 216, 198), (10, 19, 4, 6))       # bone nub
        pygame.draw.circle(body, (236, 232, 216), (12, 25), 3)
        surf.blit(body, (cx - 12, y - 7))
        drip = (self.t * 0.3 + self.seed * 0.07) % 3.0
        if drip < 1.0:
            pygame.draw.rect(surf, (88, 16, 24),
                             (cx, y + 19 + int(drip * 8), 1, 2))

    def _draw_banner(self, surf, x, y):
        col = self.kwargs.get("color", (140, 60, 70))
        for i in range(8):
            wy = math.sin(self.t * 3 + i * 0.5 + self.seed) * 1.5
            pygame.draw.line(surf, col, (x - 6, y + i * 2 + wy), (x + 6, y + i * 2 + wy), 2)

    def _draw_well(self, surf, x, y):
        # Redesign: a fuller, ominous wellhead -- the ONLY way down into
        # the Works. Mossy ring of fitted stones, a bottomless black
        # shaft, a winch frame, and the rope that descends into the dark.
        # Outer stone ring (3/4 top-down ellipse)
        pygame.draw.ellipse(surf, (78, 78, 88), (x - 18, y - 8, 36, 22))
        pygame.draw.ellipse(surf, (54, 54, 64), (x - 18, y - 8, 36, 22), 2)
        # Fitted stones around the rim
        for i in range(8):
            ang = i / 8 * math.tau
            sx = x + int(math.cos(ang) * 15)
            sy = y + 3 + int(math.sin(ang) * 8)
            pygame.draw.rect(surf, (96, 96, 106), (sx - 2, sy - 2, 4, 4))
            pygame.draw.rect(surf, (50, 50, 60), (sx - 2, sy - 2, 4, 4), 1)
        # Moss creeping the near rim
        pygame.draw.arc(surf, (54, 86, 54), (x - 16, y + 1, 32, 15), 3.5, 6.0, 2)
        # Bottomless shaft -- no water, just dark that keeps going
        pygame.draw.ellipse(surf, (10, 8, 14), (x - 12, y - 3, 24, 14))
        pygame.draw.ellipse(surf, (2, 2, 4), (x - 8, y - 1, 16, 9))
        # Winch frame: two posts + crossbar on the north side
        pygame.draw.line(surf, (84, 56, 36), (x - 13, y - 6), (x - 13, y - 22), 3)
        pygame.draw.line(surf, (84, 56, 36), (x + 13, y - 6), (x + 13, y - 22), 3)
        pygame.draw.line(surf, (70, 46, 28), (x - 15, y - 22), (x + 15, y - 22), 3)
        # Winch drum on the crossbar
        pygame.draw.rect(surf, (60, 40, 24), (x - 6, y - 24, 12, 4))
        # The rope -- from the drum straight down into the shaft
        pygame.draw.line(surf, (150, 130, 90), (x, y - 22), (x, y + 3), 1)

    def _draw_radio(self, surf, x, y):
        pygame.draw.rect(surf, (90, 60, 40), (x - 10, y - 4, 20, 12))
        pygame.draw.rect(surf, (40, 25, 15), (x - 10, y - 4, 20, 12), 1)
        pygame.draw.rect(surf, (20, 18, 22), (x - 8, y - 2, 12, 6))
        nx = x - 8 + int((math.sin(self.t * 0.6) + 1) * 6)
        pygame.draw.line(surf, (220, 60, 60), (nx, y - 2), (nx, y + 4), 1)

    def _draw_photo(self, surf, x, y):
        pygame.draw.rect(surf, (140, 110, 70), (x - 10, y - 8, 20, 16))
        pygame.draw.rect(surf, (60, 40, 25), (x - 10, y - 8, 20, 16), 1)
        pygame.draw.rect(surf, (180, 180, 200), (x - 8, y - 6, 16, 12))
        pygame.draw.circle(surf, (220, 190, 160), (x - 4, y - 2), 1)
        pygame.draw.circle(surf, (220, 190, 160), (x, y - 2), 1)
        pygame.draw.circle(surf, (220, 190, 160), (x + 4, y - 2), 1)

    def _draw_crow(self, surf, x, y):
        hop = int(abs(math.sin(self.t * 0.8)) * 1)
        head_turn = int(math.sin(self.t * 0.5) * 2)
        # Body
        pygame.draw.ellipse(surf, (10, 10, 14), (x - 5, y - 2 - hop, 10, 6))
        # Anomaly: at a rare per-seed phase, the head is flipped to
        # the OPPOSITE side of the body -- the crow is looking
        # backwards. Held for ~120ms (~one stale frame) so the
        # player only catches it if they happen to look at this crow
        # during that window.
        anomaly_phase = (self.t + self.seed * 0.13) % 9.0
        looking_back = anomaly_phase > 8.88
        if looking_back:
            head_x = x - 4 - head_turn
            eye_x = x - 5 - head_turn
        else:
            head_x = x + 4 + head_turn
            eye_x = x + 5 + head_turn
        pygame.draw.circle(surf, (10, 10, 14), (head_x, y - 4 - hop), 2)
        pygame.draw.circle(surf, (220, 200, 50), (eye_x, y - 4 - hop), 1)

    def _draw_grass_tuft(self, surf, x, y):
        sway = math.sin(self.t * 2 + self.seed) * 1
        col = (50, 110, 60)
        for i in range(3):
            pygame.draw.line(surf, col,
                             (x - 2 + i * 2, y + 4),
                             (x - 2 + i * 2 + sway, y - 2 - i), 1)

    def _draw_chalk_door(self, surf, x, y):
        """A door drawn in chalk where no door is -- the cult's compulsion
        (the door's dream made into a crude life-size drawing). A floor decal
        (see _FLOOR_DECAL_KINDS): a dark 'step-down' interior, jambs, lintel, a
        knob it cannot open, all hand-drawn (jittered + doubled strokes) so it
        reads as chalked by hand, not stamped. `seed` varies each one."""
        rng = random.Random(self.seed * 7 + 3)
        chalk = (234, 231, 221)
        faint = (168, 165, 154)
        w, h = 30, 48
        L, R, T, B = x - w // 2, x + w // 2, y - h // 2, y + h // 2
        # a faint dark wash inside the frame -- the "down through it" void that
        # makes the chalk lines read even on a dark floor
        void = pygame.Surface((w - 4, h - 4), pygame.SRCALPHA)
        void.fill((6, 6, 9, 70))
        surf.blit(void, (L + 2, T + 2))

        def hand(x0, y0, x1, y1, col, wdt=2, passes=2):
            for _ in range(passes):
                mx = (x0 + x1) // 2 + rng.randint(-1, 1)
                my = (y0 + y1) // 2 + rng.randint(-1, 1)
                pygame.draw.lines(surf, col, False,
                                  [(x0 + rng.randint(-1, 1), y0 + rng.randint(-1, 1)),
                                   (mx, my),
                                   (x1 + rng.randint(-1, 1), y1 + rng.randint(-1, 1))], wdt)
        hand(L, B, L, T, chalk)              # left jamb
        hand(R, B, R, T, chalk)              # right jamb
        hand(L, T, R, T, chalk)              # lintel
        hand(L, B, R, B, faint, 1, 1)        # threshold line
        # the knob -- the cruel detail; there is nothing to open
        pygame.draw.circle(surf, chalk, (R - 4, y + 4), 2)
        # chalk dust / scuff around it
        for _ in range(8):
            px = max(0, min(surf.get_width() - 1, x + rng.randint(-w, w)))
            py = max(0, min(surf.get_height() - 1, y + rng.randint(-h // 2, h // 2)))
            surf.set_at((px, py), faint)

    # The same chalk door, but hung on a WALL (a _WALL_DECO_KINDS card lifted
    # onto the wall plane) instead of lying on the floor. Same drawing.
    _draw_chalk_door_wall = _draw_chalk_door

    def _draw_bush(self, surf, x, y):
        """A dense leafy bush -- walkable, but if the floor under it
        is corn-cover (':') the player hides in it. Used in the
        permeable forest band so the player can duck off a road and
        break sightlines. Rendered as a cluster of overlapping leafy
        blobs with edge highlights so it reads as foliage and not a
        small tree."""
        rng = random.Random(self.seed)
        # 4-7 overlapping ovals form the bush mass. Per-bush palette
        # variation so a band of these doesn't read as stamped.
        base_g = 70 + (rng.randint(-12, 12))
        leaf = (28, max(40, base_g - 12), 38)
        leaf_lit = (54, base_g + 10, 60)
        leaf_dark = (16, max(28, base_g - 24), 24)
        n = rng.randint(4, 7)
        # Drop shadow on the ground.
        shadow = pygame.Surface((28, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), (0, 0, 28, 14))
        surf.blit(shadow, (x - 14, y + 4))
        # Leafy blobs, layered back-to-front.
        for i in range(n):
            ox = rng.randint(-9, 9)
            oy = rng.randint(-3, 1) - i // 2
            rx = rng.randint(7, 11)
            ry = rng.randint(5, 8)
            col = leaf_dark if i < n // 3 else leaf
            pygame.draw.ellipse(surf, col,
                                (x + ox - rx, y - 2 + oy - ry,
                                 rx * 2, ry * 2))
        # Upper-left highlights -- a few small lit ovals.
        for _ in range(2):
            ox = rng.randint(-6, 0)
            oy = rng.randint(-7, -3)
            pygame.draw.ellipse(surf, leaf_lit,
                                (x + ox - 4, y + oy - 2, 8, 4))

    def _draw_corn_doll(self, surf, x, y):
        """A small corn-husk effigy -- bundled stalks tied at the
        waist with twine, vaguely humanoid. The cult's curse-work
        tool. Specific to the cornfield maze; doesn't appear
        anywhere else. ~16px tall on the ground."""
        rng = random.Random(self.seed)
        # Drop shadow.
        sh = pygame.Surface((14, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 90), (0, 0, 14, 6))
        surf.blit(sh, (x - 7, y + 4))
        husk = (162, 138, 84)
        husk_dark = (108, 86, 48)
        twine = (74, 50, 28)
        # Body: a wedge of husks, wider at the bottom (skirt).
        pygame.draw.polygon(surf, husk_dark, [
            (x - 5, y + 4), (x + 5, y + 4),
            (x + 3, y - 6), (x - 3, y - 6)])
        pygame.draw.polygon(surf, husk, [
            (x - 4, y + 4), (x + 4, y + 4),
            (x + 2, y - 5), (x - 2, y - 5)])
        # Husk strands at the base
        for i in (-3, 0, 3):
            pygame.draw.line(surf, husk_dark,
                             (x + i, y + 4), (x + i + rng.randint(-1, 1),
                                              y + 8), 1)
        # Waist twine
        pygame.draw.line(surf, twine,
                         (x - 4, y), (x + 4, y), 1)
        # Head -- a tied bundle, small.
        pygame.draw.circle(surf, husk_dark, (x, y - 8), 3)
        pygame.draw.circle(surf, husk, (x - 1, y - 9), 2)
        # Crooked stick arms
        pygame.draw.line(surf, husk_dark,
                         (x - 4, y - 3), (x - 7, y), 1)
        pygame.draw.line(surf, husk_dark,
                         (x + 4, y - 3), (x + 7, y - 2), 1)
        # Tiny dark eye -- not always present.
        if rng.random() < 0.6:
            ex = x + rng.choice((-1, 1))
            pygame.draw.line(surf, (10, 8, 4),
                             (ex, y - 8), (ex, y - 7), 1)

    def _draw_corn_altar(self, surf, x, y):
        """A small ritual mound -- cobs stacked on a base of crossed
        husk-stalks, with a half-burned candle stub on top. The
        cult's offering. Maze-specific."""
        # Drop shadow
        sh = pygame.Surface((22, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 100), (0, 0, 22, 8))
        surf.blit(sh, (x - 11, y + 4))
        stalk = (96, 80, 44)
        stalk_lit = (130, 110, 64)
        cob = (218, 192, 88)
        cob_dark = (160, 130, 56)
        kernel = (250, 226, 130)
        # Two crossed stalks at the base
        pygame.draw.line(surf, stalk, (x - 9, y + 6), (x + 9, y - 2), 2)
        pygame.draw.line(surf, stalk, (x + 9, y + 6), (x - 9, y - 2), 2)
        pygame.draw.line(surf, stalk_lit, (x - 9, y + 5),
                         (x + 9, y - 3), 1)
        # Three cobs stacked
        for i, (ox, oy, rx, ry) in enumerate(
                [(-3, 0, 4, 2), (3, -1, 4, 2), (0, -4, 4, 2)]):
            pygame.draw.ellipse(surf, cob_dark,
                                (x + ox - rx, y + oy - ry,
                                 rx * 2, ry * 2))
            pygame.draw.ellipse(surf, cob,
                                (x + ox - rx + 1, y + oy - ry,
                                 rx * 2 - 2, ry * 2 - 1))
            # Kernel highlights
            for kx in (-1, 1):
                pygame.draw.line(surf, kernel,
                                 (x + ox + kx, y + oy - 1),
                                 (x + ox + kx, y + oy), 1)
        # Candle stub on top with a tiny flame
        pygame.draw.rect(surf, (208, 200, 178),
                         (x - 1, y - 8, 2, 4))
        # Flame
        flick = math.sin(self.t * 6 + self.seed) * 0.5
        pygame.draw.line(surf, (240, 184, 80),
                         (x, y - 9), (x + int(flick), y - 11), 1)

    def _draw_stalk_marker(self, surf, x, y):
        """A single corn stalk standing taller than the rest with a
        strip of cloth tied around it and a small dark token hung
        from the cloth. The cult marks the next to be taken. Maze-
        specific. Sways slightly."""
        sway = math.sin(self.t * 1.4 + self.seed * 0.13) * 1.6
        # Drop shadow
        sh = pygame.Surface((10, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 80), (0, 0, 10, 4))
        surf.blit(sh, (x - 5, y + 4))
        # Tall stalk
        stalk = (74, 102, 50)
        stalk_dark = (44, 64, 30)
        tip_x = x + int(sway)
        pygame.draw.line(surf, stalk_dark, (x, y + 4), (tip_x, y - 18), 2)
        pygame.draw.line(surf, stalk, (x - 1, y + 4),
                         (tip_x - 1, y - 18), 1)
        # A frayed husk leaf at mid-height
        leaf_x = x + int(sway * 0.5) - 4
        leaf_y = y - 6
        pygame.draw.line(surf, stalk_dark, (x - 1, y - 4),
                         (leaf_x, leaf_y), 1)
        pygame.draw.line(surf, stalk_dark, (x + 1, y - 4),
                         (leaf_x + 8, leaf_y - 1), 1)
        # Cloth strip around the upper third, sun-bleached red
        cloth = (164, 80, 60)
        cloth_dark = (100, 44, 36)
        pygame.draw.rect(surf, cloth_dark,
                         (tip_x - 4, y - 14, 8, 4))
        pygame.draw.rect(surf, cloth,
                         (tip_x - 3, y - 14, 7, 3))
        # A small dark token dangling from the cloth -- could be a
        # locket, a key, a tooth. Player fills in.
        pygame.draw.line(surf, (40, 32, 24),
                         (tip_x + 1, y - 10), (tip_x + 1, y - 6), 1)
        pygame.draw.circle(surf, (32, 26, 20),
                           (tip_x + 1, y - 5), 1)

    def _draw_tall_grass(self, surf, x, y):
        """Knee-high grass clump -- decoration only, no gameplay effect.
        Five to seven stalks that sway out of phase, each ~14px tall.
        The clump's exact shape varies by `seed` so a meadow of these
        doesn't read as a stamped pattern."""
        rng = random.Random(self.seed)
        col_back = (38, 78, 46)
        col_front = (62, 118, 70)
        n = rng.randint(5, 8)
        base_sway = math.sin(self.t * 1.3 + self.seed) * 1.5
        for i in range(n):
            ox = rng.randint(-5, 5)
            height = rng.randint(10, 16)
            phase = self.seed * 0.13 + i * 0.7
            tip_sway = base_sway + math.sin(self.t * 1.8 + phase) * 1.2
            stalk_col = col_back if i < n // 2 else col_front
            pygame.draw.line(surf, stalk_col,
                             (x + ox, y + 4),
                             (x + ox + tip_sway, y + 4 - height), 1)

    def _draw_town_sign(self, surf, x, y):
        """A wooden signpost with two crossbeams reading the town's
        name. Weathered, the paint mostly gone. The text is the
        decoration's `text` kwarg ('BRIMLEY' by default). Two posts
        with the boards nailed across them, edge highlights so the
        sign reads as raised."""
        text = self.kwargs.get("text", "BRIMLEY")
        post_col = (62, 44, 28)
        post_lit = (88, 64, 40)
        board_col = (96, 70, 44)
        board_lit = (124, 92, 58)
        board_dark = (60, 42, 22)
        # Two posts, 4px wide, 26px tall
        for px in (x - 10, x + 10):
            pygame.draw.rect(surf, post_col, (px - 2, y - 18, 4, 26))
            pygame.draw.line(surf, post_lit, (px - 2, y - 18),
                             (px - 2, y + 8), 1)
        # Board: 28px wide, 12px tall, centred at (x, y-10)
        bw, bh = 28, 14
        bx, by = x - bw // 2, y - 18
        pygame.draw.rect(surf, board_col, (bx, by, bw, bh))
        pygame.draw.rect(surf, board_dark, (bx, by, bw, bh), 1)
        pygame.draw.line(surf, board_lit, (bx + 1, by + 1),
                         (bx + bw - 1, by + 1), 1)
        # Text rendered tiny.
        font = pygame.font.SysFont(None, 12, bold=True)
        txt = font.render(text, True, (30, 20, 10))
        txt_x = bx + (bw - txt.get_width()) // 2
        txt_y = by + (bh - txt.get_height()) // 2
        surf.blit(txt, (txt_x, txt_y))

    def _draw_flagpole(self, surf, x, y):
        """A weathered metal flagpole with a tattered flag. The flag
        is half-mast; the rope is frayed. Used in front of the
        schoolhouse. Sway driven by self.t so the flag flutters."""
        pole_col = (130, 132, 138)
        pole_lit = (172, 174, 180)
        # Pole: 28px tall, 2px wide
        ph = 28
        pygame.draw.line(surf, pole_col, (x, y + 4), (x, y - ph), 2)
        pygame.draw.line(surf, pole_lit, (x - 1, y + 4), (x - 1, y - ph), 1)
        # Knob at top
        pygame.draw.circle(surf, (180, 180, 188), (x, y - ph), 2)
        # Half-mast flag -- a frayed strip 8x12. The trailing edge
        # ripples with self.t.
        sway = math.sin(self.t * 2.2 + self.seed * 0.1) * 1.4
        fy = y - ph + 8
        # Faded dark cloth (former colour, now near-black).
        cloth = (66, 50, 50)
        cloth_dark = (40, 28, 28)
        pts = [
            (x + 1, fy),
            (x + 12 + sway, fy + 1),
            (x + 11 + sway, fy + 10),
            (x + 1, fy + 9),
        ]
        pygame.draw.polygon(surf, cloth, pts)
        pygame.draw.line(surf, cloth_dark, (x + 1, fy), (x + 11 + sway, fy + 9), 1)
        # Frayed trailing edge
        for i in range(3):
            tx = int(x + 10 + sway - i)
            ty = fy + 2 + i * 3
            pygame.draw.line(surf, cloth_dark, (tx, ty), (tx + 3, ty + 1), 1)

    def _draw_mote(self, surf, x, y):
        dx = math.sin(self.t * 0.4 + self.seed) * 8
        dy = math.cos(self.t * 0.3 + self.seed * 0.7) * 4
        col = (200, 200, 220)
        try:
            surf.set_at((int(x + dx), int(y + dy)), col)
            surf.set_at((int(x + dx + 1), int(y + dy)), col)
        except (IndexError, ValueError):
            pass

    def _draw_mist(self, surf, x, y):
        """Low ground fog -- soft translucent pools that breathe and
        slide on the wind. Sized via kwargs w/h; laid over the water and
        the marsh so the fog clings to the wet ground."""
        ww = self.kwargs.get("w", 96)
        hh = self.kwargs.get("h", 48)
        drift = int(math.sin(self.t * 0.18 + self.seed) * 10)
        breath = 1.0 + math.sin(self.t * 0.25 + self.seed * 0.5) * 0.12
        pad = 30
        fog = pygame.Surface((ww + pad * 2, hh + pad * 2), pygame.SRCALPHA)
        rng = random.Random(self.seed)
        for _ in range(5):
            ew = int(rng.randint(ww // 2, ww) * breath)
            eh = int(rng.randint(hh // 2, hh) * breath)
            ox = pad + rng.randint(-ww // 4, ww // 4) + (ww - ew) // 2
            oy = pad + rng.randint(-hh // 4, hh // 4) + (hh - eh) // 2
            pygame.draw.ellipse(fog, (150, 156, 162, 22), (ox, oy, ew, eh))
        surf.blit(fog, (x - ww // 2 - pad + drift, y - hh // 2 - pad))

    def _draw_wisp(self, surf, x, y):
        """A will-o'-the-wisp -- a small cold pale glow drifting low over
        the bog. Marsh gas, or something out there carrying a light."""
        cx = int(x + math.sin(self.t * 0.5 + self.seed) * 14)
        cy = int(y + math.cos(self.t * 0.37 + self.seed * 0.6) * 8)
        glow = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(glow, (110, 168, 146, 38), (11, 11), 10)
        pygame.draw.circle(glow, (150, 200, 174, 70), (11, 11), 5)
        surf.blit(glow, (cx - 11, cy - 11))
        try:
            surf.set_at((cx, cy), (210, 235, 220))
        except (IndexError, ValueError):
            pass

    def _draw_brazier(self, surf, x, y):
        """A cult fire-bowl on an iron tripod -- a warm focal light at a
        ritual site, the flame guttering. Pools of fire are the only
        warmth out here, and the eye goes straight to them."""
        _light_pool(surf, x, y - 6, 40, (255, 150, 56), 82)
        pygame.draw.line(surf, (28, 26, 30), (x, y - 2), (x - 6, y + 11), 2)
        pygame.draw.line(surf, (28, 26, 30), (x, y - 2), (x + 6, y + 11), 2)
        pygame.draw.line(surf, (28, 26, 30), (x, y - 2), (x, y + 12), 2)
        pygame.draw.ellipse(surf, (42, 40, 44), (x - 9, y - 5, 18, 8))
        pygame.draw.ellipse(surf, (18, 16, 20), (x - 7, y - 4, 14, 5))
        t = self.t * 6 + self.seed
        fh = 8 + int(math.sin(t) * 3)
        pygame.draw.polygon(surf, (208, 88, 28),
                            [(x, y - 5 - fh), (x - 5, y - 3), (x + 5, y - 3)])
        pygame.draw.polygon(surf, (250, 178, 68),
                            [(x, y - 4 - int(fh * 0.6)), (x - 3, y - 3), (x + 3, y - 3)])

    def _draw_steeple(self, surf, x, y):
        """A church bell-tower, near-top-down: a tall narrow spire rising
        up the screen from its base, a dark louvered belfry with a faint
        bell, a pointed cap + a crooked cross, and a long shadow thrown
        across the ground -- the one TALL thing for miles, the landmark
        you orient by."""
        H = 74
        topx = x + int(math.sin(self.seed) * 4)        # leans a touch
        top = y - H
        sh = pygame.Surface((64, 30), pygame.SRCALPHA)  # long cast shadow, down-right
        pygame.draw.polygon(sh, (0, 0, 0, 88), [(0, 26), (14, 26), (58, 4), (44, 0)])
        surf.blit(sh, (x - 6, y - 6))
        bw = 16
        body = [(x - bw // 2, y), (topx - bw // 2 + 3, top + 14),
                (topx + bw // 2 - 3, top + 14), (x + bw // 2, y)]
        pygame.draw.polygon(surf, (70, 64, 54), body)
        pygame.draw.polygon(surf, (38, 34, 28), body, 1)
        pygame.draw.line(surf, (98, 92, 80),
                         (x - bw // 2, y), (topx - bw // 2 + 3, top + 14), 2)
        pygame.draw.rect(surf, (15, 13, 17), (topx - 5, top + 14, 10, 12))  # belfry
        bell_dx = int(math.sin(self.t * 1.7 + self.seed) * 2)               # tolling
        pygame.draw.circle(surf, (66, 58, 42), (topx + bell_dx, top + 21), 3)
        pygame.draw.line(surf, (28, 24, 18), (topx + bell_dx, top + 18),
                         (topx + bell_dx, top + 24), 1)                      # clapper line
        spire = [(topx - bw // 2 + 2, top + 14), (topx, top - 8),
                 (topx + bw // 2 - 2, top + 14)]
        pygame.draw.polygon(surf, (54, 40, 30), spire)
        pygame.draw.polygon(surf, (32, 24, 18), spire, 1)
        pygame.draw.line(surf, (44, 40, 32), (topx, top - 8), (topx, top - 18), 2)
        pygame.draw.line(surf, (44, 40, 32), (topx - 4, top - 14), (topx + 4, top - 14), 2)

    def _draw_flock(self, surf, x, y):
        """A few distant birds drifting across the grey, wings beating.
        Loops slowly so the sky is never quite still. `span`/`speed`
        kwargs tune the drift."""
        span = self.kwargs.get("span", 180)
        speed = self.kwargs.get("speed", 0.5)
        lead = ((self.t * speed * 16 + self.seed * 7) % (span + 60)) - 30
        n = 3 + (self.seed % 3)
        for i in range(n):
            bx = int(x + lead - i * (11 + (self.seed + i) % 8))
            by = int(y + (i % 3 - 1) * 8 + math.sin(self.t * 0.6 + i) * 3)
            flap = int(math.sin(self.t * 6 + i * 1.3) * 4)
            # ground shadow offset below -> reads as flying above the field
            pygame.draw.line(surf, (10, 12, 15), (bx - 4, by + 11),
                             (bx, by + 9), 1)
            pygame.draw.line(surf, (10, 12, 15), (bx + 4, by + 11),
                             (bx, by + 9), 1)
            col = (52, 52, 60)                            # lit-from-above silhouette
            pygame.draw.line(surf, col, (bx - 5, by + flap), (bx, by), 2)
            pygame.draw.line(surf, col, (bx + 5, by + flap), (bx, by), 2)

    def _draw_leaves(self, surf, x, y):
        """Dead leaves and grit tumbling across the ground on the wind --
        a low, restless drift that loops near the anchor."""
        cols = [(86, 68, 40), (70, 56, 34), (54, 60, 36), (60, 48, 30)]
        for i in range(4 + (self.seed % 4)):
            ph = self.t * 0.6 + i * 0.9 + self.seed
            dx = math.sin(ph) * 16 + ((self.t * 9 + i * 19) % 74) - 37
            dy = math.cos(ph * 1.3) * 9 + math.sin(ph * 0.5) * 4
            sz = 1 + (i & 1)
            pygame.draw.rect(surf, cols[i % 4], (int(x + dx), int(y + dy), sz, sz))

    def _draw_terminal(self, surf, x, y):
        pygame.draw.rect(surf, (10, 12, 14), (x - 12, y - 10, 24, 20))
        pygame.draw.rect(surf, (40, 40, 50), (x - 12, y - 10, 24, 20), 1)
        for i in range(5):
            ly = (y - 8 + i * 4 + int(self.t * 8)) % 16 + (y - 10)
            w = (self.seed + i * 31) % 12 + 4
            pygame.draw.line(surf, (50, 200, 80), (x - 10, ly), (x - 10 + w, ly), 1)

    def _draw_cauldron(self, surf, x, y):
        """THRESHOLD: cast-iron cauldron suspended on a triangular
        iron frame over a fire pit. Used in the clearing scene
        (the cult's purification site). Black-iron body with a
        rolled rim, three-leg frame angling out from above the pot,
        embers visible at the base when 'lit' kwarg is True."""
        # Triangular frame (three iron rods crossing above the pot)
        rod = (30, 28, 34)
        pygame.draw.line(surf, rod, (x - 14, y - 18), (x, y - 22), 2)
        pygame.draw.line(surf, rod, (x + 14, y - 18), (x, y - 22), 2)
        pygame.draw.line(surf, rod, (x - 14, y - 18), (x - 18, y + 6), 2)
        pygame.draw.line(surf, rod, (x + 14, y - 18), (x + 18, y + 6), 2)
        # Hanging chain
        for i in range(3):
            pygame.draw.line(surf, rod,
                             (x, y - 22 + i * 4),
                             (x, y - 18 + i * 4), 1)
        # Cauldron body (cast iron)
        pygame.draw.ellipse(surf, (16, 14, 18), (x - 12, y - 10, 24, 16))
        pygame.draw.ellipse(surf, (40, 36, 42), (x - 12, y - 10, 24, 16), 1)
        # Rolled rim
        pygame.draw.ellipse(surf, (50, 46, 52), (x - 12, y - 12, 24, 6))
        pygame.draw.ellipse(surf, (8, 6, 10), (x - 10, y - 11, 20, 4))
        # Liquid surface (dark, slightly steaming)
        if self.kwargs.get("lit", True):
            pygame.draw.ellipse(surf, (60, 30, 30), (x - 9, y - 10, 18, 4))
            # Steam wisps
            wisp_t = self.t * 2
            for i in range(3):
                wy = int(y - 18 - (wisp_t + i * 4) % 12)
                wx = int(x - 4 + i * 3 + math.sin(wisp_t + i) * 2)
                pygame.draw.rect(surf, (100, 90, 100), (wx, wy, 2, 2))
        # Embers at the base
        if self.kwargs.get("lit", True):
            for i in range(4):
                ex = x - 8 + i * 5
                ey = y + 8
                col = (200 + int(math.sin(self.t * 6 + i) * 20),
                       80, 30)
                pygame.draw.rect(surf, col, (ex, ey, 2, 2))

    def _draw_bowl(self, surf, x, y):
        # ceramic bowl on table — empty by default; if "filled" kwarg is True, contains an egg
        pygame.draw.ellipse(surf, (180, 170, 155), (x - 10, y - 4, 20, 10))
        pygame.draw.ellipse(surf, (130, 120, 110), (x - 10, y - 4, 20, 10), 1)
        pygame.draw.ellipse(surf, (60, 50, 45), (x - 8, y - 3, 16, 6))
        if self.kwargs.get("filled"):
            # painted egg in bowl
            cols = [(220, 80, 80), (80, 180, 220), (220, 200, 80)]
            pygame.draw.ellipse(surf, (240, 220, 200), (x - 5, y - 8, 10, 12))
            pygame.draw.ellipse(surf, cols[0], (x - 4, y - 6, 4, 2))
            pygame.draw.ellipse(surf, cols[1], (x, y - 4, 4, 2))
            pygame.draw.ellipse(surf, cols[2], (x - 3, y - 2, 4, 2))

    def _draw_item_drop(self, surf, x, y):
        # generic loot bob: small box that bobs gently with subtle glow
        bob = int(math.sin(self.t * 2) * 1)
        col = self.kwargs.get("color", C_GOLD)
        pygame.draw.rect(surf, col, (x - 4, y - 4 + bob, 8, 8))
        pygame.draw.rect(surf, C_BLACK, (x - 4, y - 4 + bob, 8, 8), 1)
        if int(self.t * 4) % 4 == 0:
            pygame.draw.line(surf, (255, 255, 200), (x - 6, y - 6 + bob), (x - 4, y - 4 + bob), 1)

    def _draw_bloody_pile(self, surf, x, y):
        # Lumpy mound of meat / cloth scraps in a pool of blood. Used
        # in the barn after the doll is taken -- the room dirties
        # immediately, this deco appears next to the chest. Static
        # (no animation): the horror is in finding it, not watching it.
        pool = (90, 8, 14)
        dark = (50, 4, 10)
        flesh = (130, 50, 50)
        scrap = (160, 110, 100)
        # Pool of blood underneath
        pygame.draw.ellipse(surf, pool, (x - 14, y - 2, 28, 12))
        pygame.draw.ellipse(surf, dark, (x - 9, y + 2, 18, 6))
        # Mound (three lumps)
        pygame.draw.ellipse(surf, flesh, (x - 10, y - 8, 14, 10))
        pygame.draw.ellipse(surf, flesh, (x - 2, y - 10, 12, 9))
        pygame.draw.ellipse(surf, flesh, (x + 1, y - 5, 10, 8))
        pygame.draw.ellipse(surf, dark, (x - 10, y - 8, 14, 10), 1)
        pygame.draw.ellipse(surf, dark, (x - 2, y - 10, 12, 9), 1)
        # Scraps poking out
        pygame.draw.line(surf, scrap, (x - 6, y - 4), (x - 9, y - 8), 1)
        pygame.draw.line(surf, scrap, (x + 4, y - 6), (x + 8, y - 9), 1)

    def _draw_drowned_body(self, surf, x, y):
        """Slumped, tied, drowned figure. Built on the same silhouette
        as the well-passage `gore` decoration -- broken pose, dark
        underbody pool, head turned -- but the palette is drowned
        (cold blue-grey) and the figure is bound at wrists and ankles
        with long hair fanning out into the water. Bobs slowly on the
        current."""
        y += int(math.sin(self.t * 0.55 + self.seed) * 1.6)   # bob on the water
        # Underbody pool -- not blood here, just the dark water /
        # silt under the body. Same shape language as the well gore.
        pygame.draw.ellipse(surf, (10, 18, 36), (x - 18, y, 36, 14))
        pygame.draw.ellipse(surf, (16, 28, 56), (x - 14, y - 2, 28, 10))
        pygame.draw.ellipse(surf, (4, 10, 24), (x - 6, y + 2, 12, 6))
        # Slumped torso (cold cloth)
        pygame.draw.rect(surf, (50, 60, 80), (x - 9, y - 12, 18, 14))
        pygame.draw.rect(surf, (24, 30, 44), (x - 9, y - 12, 18, 14), 1)
        # Splayed limb to the right (same direction as the gore)
        pygame.draw.rect(surf, (50, 60, 80), (x + 8, y - 4, 12, 5))
        pygame.draw.rect(surf, (24, 30, 44), (x + 8, y - 4, 12, 5), 1)
        # Rope binding the wrists where the splayed limb meets the
        # body -- a cinched dark band.
        pygame.draw.rect(surf, (140, 110, 70), (x + 6, y - 4, 4, 5))
        pygame.draw.line(surf, (90, 60, 30), (x + 10, y - 1),
                         (x + 14, y + 4), 1)
        # Rope binding the ankles -- visible band across the lower
        # body where the legs are pinned together.
        pygame.draw.rect(surf, (140, 110, 70), (x - 6, y + 6, 12, 2))
        # Head turned away (off-centre to the left like the gore).
        pygame.draw.circle(surf, (170, 180, 190), (x - 6, y - 14), 5)
        pygame.draw.circle(surf, (40, 50, 70), (x - 6, y - 14), 5, 1)
        # Eyes-open variant -- triggered after the player has come
        # close once. Two small bright dots where the closed eyes
        # used to be lineless. The body has not moved otherwise.
        if self.kwargs.get("eyes_open"):
            pygame.draw.circle(surf, (240, 240, 250), (x - 7, y - 14), 1)
            pygame.draw.circle(surf, (240, 240, 250), (x - 5, y - 14), 1)
        # Long hair fanning OUT from the head into the surrounding
        # water -- streaks on every side, longer than the head is wide.
        hair = (30, 24, 28)
        for ang_step in range(8):
            ang = (ang_step / 8) * 6.283
            length = 12 + (ang_step % 3) * 2
            ex = x - 6 + int(math.cos(ang) * length)
            ey = y - 14 + int(math.sin(ang) * length)
            pygame.draw.line(surf, hair, (x - 6, y - 14), (ex, ey), 1)
        # A few darker smudges for texture (matches well-gore style).
        pygame.draw.line(surf, (4, 10, 18), (x - 10, y + 4),
                         (x + 12, y + 6), 1)
        pygame.draw.line(surf, (4, 10, 18), (x - 8, y + 8),
                         (x + 10, y + 8), 1)

    def _draw_watching_eye(self, surf, x, y):
        """An eye that always looks at the player. The pupil rotates
        toward the player's world position each frame using the
        class-level Decoration.player_world cache. Random blink every
        few seconds. Sized via self.kwargs.get('size', 'small') to
        either 'small' (sclera ~10px) or 'large' (~22px) so the same
        kind serves close embedded eyes and far peripheral ones.

        The eye is meant to be placed where the player will see it
        only out of the corner of their attention -- in tree lines,
        wall faces, water surfaces. The pupil following them is the
        beat that makes the player feel observed.

        Cosmetic upgrades: bloodshot vein lines etched into the sclera
        (deterministic per-seed so each eye has its own pattern), and
        a vertical-slit pupil variant when `slit=True` is passed via
        kwargs -- used in the late-game cult sites to push the gaze
        from human to inhuman."""
        # THRESHOLD redesign: drop the cartoon-eyeball palette. The eye
        # now reads as something *carved* or *sunken* into the surface
        # it sits on -- a narrow lid-slit framing a recessed iris that
        # tracks the player. No bright sclera, no catchlight, no
        # candy-coloured iris. Same kwargs (`size`, `slit`) so all
        # existing scene wiring keeps working.
        #
        # 8-WAY DIRECTIONAL TRACKING: instead of a continuous pupil
        # offset (which feels like a smooth analog stick), the iris
        # now snaps to ONE of eight compass positions (N / NE / E /
        # SE / S / SW / W / NW) based on the player's bearing from
        # this eye. The discrete jump catches peripheral vision
        # better -- the player notices the eye SHIFT when they
        # cross a diagonal, instead of an iris that just slowly
        # drifts. Reads as someone making a deliberate look.
        size = self.kwargs.get("size", "small")
        slit = self.kwargs.get("slit", False)
        if size == "large":
            socket_w, socket_h = 26, 12
            pupil_r = 5
            travel = 6
        else:
            socket_w, socket_h = 14, 7
            pupil_r = 2
            travel = 3
        # Blink schedule: every ~6s, the slit closes for 0.18s.
        cycle = 6.0
        local = (self.t + self.seed * 0.1) % cycle
        blinking = local > (cycle - 0.18)
        # Recessed socket -- a dark horizontal hollow carved into the
        # surface. Slight inner shadow to suggest depth.
        pygame.draw.ellipse(surf, (16, 12, 16),
                            (x - socket_w // 2, y - socket_h // 2,
                             socket_w, socket_h))
        pygame.draw.ellipse(surf, (4, 2, 6),
                            (x - socket_w // 2, y - socket_h // 2,
                             socket_w, socket_h), 1)
        if blinking:
            # Lid closed -- the slit goes opaque. No pupil this frame.
            pygame.draw.rect(surf, (24, 18, 22),
                             (x - socket_w // 2, y - 1,
                              socket_w, 2))
            return
        # Bucket the player bearing into one of 8 compass octants.
        # Vertical travel halved so the iris stays inside the
        # horizontal socket on N/S looks.
        ox, oy = _compass_offset(
            Decoration.player_world[0] - self.x,
            Decoration.player_world[1] - self.y,
            travel, max(1, travel // 2),
        )
        # Iris -- desaturated dried-blood ring rather than purple.
        # Smaller than before so the eye doesn't bulge out of the socket.
        if pupil_r >= 3:
            pygame.draw.circle(surf, (90, 30, 30),
                               (x + ox, y + oy), pupil_r)
        if slit:
            # Vertical-slit pupil -- inhuman, animal. Two pixels wide.
            slit_w = 1
            slit_h = max(2, pupil_r + 1)
            pygame.draw.ellipse(surf, (4, 2, 6),
                                (x + ox - slit_w, y + oy - slit_h // 2,
                                 slit_w * 2, slit_h))
        else:
            pygame.draw.circle(surf, (4, 2, 6),
                               (x + ox, y + oy), max(1, pupil_r - 1))
        # Faint wet glint at the socket's inner edge -- on the side
        # the iris is looking from, so the moisture catches with
        # the gaze direction.
        if ox > 0:
            glint_x = x - (socket_w // 2) + 2
        elif ox < 0:
            glint_x = x + (socket_w // 2) - 2
        else:
            # Pure N / S look -- glint sits centre.
            glint_x = x
        pygame.draw.rect(surf, (60, 50, 50),
                         (glint_x, y, 1, 1))

    def _draw_polaroid_wall(self, surf, x, y):
        """The polaroid family pinned to the bedroom wall above the bed
        after polaroid_taken flips. Reads as a photo frame containing
        the four-figure family from the polaroid item -- tall man,
        blonde woman, small boy, small girl. The frame is intact;
        the figures all face out, looking at the bed."""
        # Frame
        pygame.draw.rect(surf, (90, 60, 40), (x - 9, y - 12, 18, 16))
        pygame.draw.rect(surf, (40, 25, 15), (x - 9, y - 12, 18, 16), 1)
        # Photo paper
        pygame.draw.rect(surf, (210, 200, 180), (x - 7, y - 10, 14, 12))
        # Tall man (centre)
        pygame.draw.rect(surf, (60, 50, 70), (x - 1, y - 8, 2, 7))
        pygame.draw.circle(surf, (200, 180, 160), (x, y - 9), 1)
        # Blonde woman (right of man, leans on him)
        pygame.draw.rect(surf, (160, 80, 100), (x + 2, y - 7, 2, 6))
        pygame.draw.circle(surf, (220, 200, 140), (x + 3, y - 8), 1)
        # Boy (front of man, on crutches)
        pygame.draw.rect(surf, (200, 180, 80), (x - 3, y - 4, 1, 4))
        pygame.draw.circle(surf, (200, 180, 160), (x - 3, y - 5), 1)
        pygame.draw.line(surf, (90, 60, 30), (x - 4, y - 4),
                         (x - 4, y), 1)
        # Girl (next to boy)
        pygame.draw.rect(surf, (200, 100, 130), (x - 5, y - 4, 1, 4))
        pygame.draw.circle(surf, (200, 180, 160), (x - 5, y - 5), 1)
        # All four faces have black-dot eyes that point AT the viewer.
        for ex, ey in [(x, y - 9), (x + 3, y - 8),
                       (x - 3, y - 5), (x - 5, y - 5)]:
            pygame.draw.circle(surf, (10, 10, 14), (ex, ey), 1)

    def _draw_small_chair(self, surf, x, y):
        """A child-sized chair pulled out from the writing table after
        crutch_taken. Wood-toned, smaller proportions than the regular
        chair object tile. Sits diagonally as if just stood up from."""
        pygame.draw.rect(surf, (110, 80, 60), (x - 6, y - 4, 12, 10))
        pygame.draw.rect(surf, (90, 60, 40), (x - 6, y - 8, 12, 6))
        pygame.draw.rect(surf, (60, 40, 25), (x - 6, y - 8, 12, 14), 1)
        pygame.draw.rect(surf, (70, 50, 32), (x - 5, y + 6, 2, 4))
        pygame.draw.rect(surf, (70, 50, 32), (x + 3, y + 6, 2, 4))

    def _draw_overturned_chair(self, surf, x, y):
        pygame.draw.rect(surf, (110, 80, 60), (x - 10, y - 2, 18, 6))
        pygame.draw.rect(surf, (60, 40, 25), (x - 10, y - 2, 18, 6), 1)
        pygame.draw.rect(surf, (70, 50, 32), (x + 8, y - 8, 4, 6))
        pygame.draw.rect(surf, (70, 50, 32), (x + 8, y, 4, 6))
        pygame.draw.rect(surf, (90, 60, 40), (x - 10, y - 8, 6, 14))

    def _draw_place_setting(self, surf, x, y):
        """A single place setting on the writing table after the player
        carries the reservation slip back into the bedroom: one plate,
        one chair, one candle. The other three settings the slip
        listed are conspicuously absent."""
        # Plate
        pygame.draw.ellipse(surf, (220, 220, 230), (x - 7, y - 4, 14, 8))
        pygame.draw.ellipse(surf, (60, 60, 70), (x - 7, y - 4, 14, 8), 1)
        pygame.draw.ellipse(surf, (240, 240, 250), (x - 5, y - 3, 10, 6))
        # Fork to the left
        pygame.draw.line(surf, (180, 180, 200), (x - 10, y - 2),
                         (x - 10, y + 4), 1)
        pygame.draw.line(surf, (180, 180, 200), (x - 11, y - 2),
                         (x - 9, y - 2), 1)
        # Knife to the right
        pygame.draw.line(surf, (180, 180, 200), (x + 10, y - 2),
                         (x + 10, y + 4), 1)
        # Tiny candle
        pygame.draw.rect(surf, (220, 200, 160), (x - 1, y - 12, 2, 7))
        glow = 0.7 + math.sin(self.t * 4 + self.seed) * 0.3
        pygame.draw.circle(surf, (240, 200, 100),
                           (x, y - 13), max(2, int(3 * glow)))

    def _draw_apology_wall(self, surf, x, y):
        """A patch of wall covered in scratched 'I'M SORRY' text,
        repeated overlapping rows in cramped uneven handwriting.
        The lines are deterministic per-instance via self.seed so
        adjacent placements don't share identical patterns. Drawn
        as short white scratches so the text reads as carved/etched
        rather than written. Static -- no animation."""
        rng = random.Random(self.seed)
        col = (210, 210, 220)
        # 4 stacked rows of "I'M SORRY" using simple stroke shapes
        # for each letter. Each row jittered slightly horizontally
        # so the text feels written by hand, not typeset.
        word = "IM SORRY"
        for row in range(4):
            ry = y - 14 + row * 8
            rx = x - 22 + rng.randint(-2, 2)
            for ch in word:
                if ch == " ":
                    rx += 3
                    continue
                self._draw_etched_char(surf, ch, rx, ry, col, rng)
                rx += 5
        # Outer scratches around the patch suggest more text just
        # off the visible area.
        for _ in range(6):
            sx = x + rng.randint(-22, 22)
            sy = y + rng.randint(-14, 14)
            ex = sx + rng.randint(-3, 3)
            ey = sy + rng.randint(-2, 2)
            pygame.draw.line(surf, col, (sx, sy), (ex, ey), 1)

    def _draw_etched_char(self, surf, ch, x, y, col, rng):
        """Skeletal stroke renderer for a single letter inside an
        apology-wall patch. Tiny 4x6 characters drawn with short
        line strokes -- only the letters used by I'M SORRY are
        defined."""
        if ch == "I":
            pygame.draw.line(surf, col, (x + 1, y), (x + 1, y + 5), 1)
        elif ch == "M":
            pygame.draw.line(surf, col, (x, y + 5), (x, y), 1)
            pygame.draw.line(surf, col, (x, y), (x + 2, y + 2), 1)
            pygame.draw.line(surf, col, (x + 2, y + 2), (x + 4, y), 1)
            pygame.draw.line(surf, col, (x + 4, y), (x + 4, y + 5), 1)
        elif ch == "S":
            pygame.draw.line(surf, col, (x + 3, y), (x, y), 1)
            pygame.draw.line(surf, col, (x, y), (x, y + 2), 1)
            pygame.draw.line(surf, col, (x, y + 2), (x + 3, y + 3), 1)
            pygame.draw.line(surf, col, (x + 3, y + 3), (x + 3, y + 5), 1)
            pygame.draw.line(surf, col, (x + 3, y + 5), (x, y + 5), 1)
        elif ch == "O":
            pygame.draw.rect(surf, col, (x, y, 4, 6), 1)
        elif ch == "R":
            pygame.draw.line(surf, col, (x, y + 5), (x, y), 1)
            pygame.draw.line(surf, col, (x, y), (x + 3, y), 1)
            pygame.draw.line(surf, col, (x + 3, y), (x + 3, y + 2), 1)
            pygame.draw.line(surf, col, (x + 3, y + 2), (x, y + 2), 1)
            pygame.draw.line(surf, col, (x, y + 2), (x + 3, y + 5), 1)
        elif ch == "Y":
            pygame.draw.line(surf, col, (x, y), (x + 2, y + 2), 1)
            pygame.draw.line(surf, col, (x + 4, y), (x + 2, y + 2), 1)
            pygame.draw.line(surf, col, (x + 2, y + 2), (x + 2, y + 5), 1)

    def _draw_pillar(self, surf, x, y):
        """Stone pillar. `large=True` draws a fat 32x44 column with a
        capital and base; default is a slim 18x36 supporting pillar.
        When `filled=True` the pillar shows its offering: the orb
        (large) or a big fish (small) sits on top of the capital with
        a soft glow."""
        large = self.kwargs.get("large", False)
        filled = self.kwargs.get("filled", False)
        if large:
            body = (130, 130, 140)
            edge = (70, 70, 80)
            cap = (160, 160, 170)
            pygame.draw.rect(surf, body, (x - 16, y - 30, 32, 44))
            pygame.draw.rect(surf, edge, (x - 16, y - 30, 32, 44), 1)
            pygame.draw.rect(surf, cap, (x - 18, y - 34, 36, 6))
            pygame.draw.rect(surf, edge, (x - 18, y - 34, 36, 6), 1)
            pygame.draw.rect(surf, cap, (x - 18, y + 12, 36, 6))
            pygame.draw.rect(surf, edge, (x - 18, y + 12, 36, 6), 1)
            pygame.draw.line(surf, edge, (x, y - 28), (x, y + 12), 1)
            if filled:
                # Orb resting on top of the capital. Soft purple glow,
                # subtle pulse via self.t.
                pulse = 0.7 + math.sin(self.t * 2.0 + self.seed) * 0.3
                glow = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.circle(glow, (180, 80, 220, int(80 * pulse)),
                                   (20, 20), int(16 * pulse))
                surf.blit(glow, (x - 20, y - 56))
                pygame.draw.circle(surf, (60, 30, 80), (x, y - 40), 7)
                pygame.draw.circle(surf, (200, 120, 240), (x, y - 40), 6)
                pygame.draw.circle(surf, (255, 220, 255),
                                   (x - 2, y - 42), 2)
        else:
            body = (118, 118, 128)
            edge = (60, 60, 70)
            cap = (150, 150, 160)
            pygame.draw.rect(surf, body, (x - 9, y - 22, 18, 32))
            pygame.draw.rect(surf, edge, (x - 9, y - 22, 18, 32), 1)
            pygame.draw.rect(surf, cap, (x - 11, y - 26, 22, 5))
            pygame.draw.rect(surf, edge, (x - 11, y - 26, 22, 5), 1)
            pygame.draw.rect(surf, cap, (x - 11, y + 8, 22, 5))
            pygame.draw.rect(surf, edge, (x - 11, y + 8, 22, 5), 1)
            if filled:
                # Fish lying across the capital, head left. Static.
                fish_body = (90, 110, 140)
                fish_dark = (50, 60, 80)
                belly = (180, 190, 200)
                pygame.draw.ellipse(surf, fish_body,
                                    (x - 9, y - 33, 18, 7))
                pygame.draw.ellipse(surf, fish_dark,
                                    (x - 9, y - 33, 18, 7), 1)
                pygame.draw.ellipse(surf, belly,
                                    (x - 7, y - 31, 14, 4))
                pygame.draw.polygon(surf, fish_body,
                                    [(x + 8, y - 30), (x + 12, y - 33),
                                     (x + 12, y - 27)])
                pygame.draw.circle(surf, (20, 20, 30),
                                   (x - 6, y - 30), 1)

    def _draw_pedestal(self, surf, x, y):
        # Stone pedestal: a tapered grey block. Used at the end of the
        # abducted_hallway to stage the final diary page. Slow inner
        # glow when `lit=True` is passed via kwargs.
        body = (110, 110, 120)
        edge = (60, 60, 70)
        pygame.draw.rect(surf, body, (x - 9, y - 4, 18, 12))
        pygame.draw.rect(surf, edge, (x - 9, y - 4, 18, 12), 1)
        pygame.draw.rect(surf, body, (x - 11, y + 6, 22, 4))
        pygame.draw.rect(surf, edge, (x - 11, y + 6, 22, 4), 1)
        pygame.draw.rect(surf, (140, 140, 150), (x - 7, y - 6, 14, 3))
        if self.kwargs.get("lit", True):
            pulse = 0.6 + math.sin(self.t * 2.0 + self.seed) * 0.4
            glow = pygame.Surface((18, 8), pygame.SRCALPHA)
            alpha = int(120 * pulse)
            pygame.draw.ellipse(glow, (200, 180, 220, alpha), (0, 0, 18, 8))
            surf.blit(glow, (x - 9, y - 10))

    def _draw_bloodstain(self, surf, x, y):
        # static blob
        pygame.draw.ellipse(surf, (90, 10, 14), (x - 8, y - 3, 16, 8))
        pygame.draw.ellipse(surf, (60, 6, 10), (x - 4, y, 8, 4))

    def _draw_symbol(self, surf, x, y):
        # Pulsing arcane sigil on the floor. Two concentric circles + an
        # inner triangle, all in violet. Pulses size with a slow sine so
        # it reads as 'active' rather than painted.
        pulse = 1.0 + math.sin(self.t * 1.5 + self.seed) * 0.18
        col = (180, 80, 220)
        r1 = max(2, int(14 * pulse))
        r2 = max(2, int(8 * pulse))
        pygame.draw.circle(surf, col, (x, y), r1, 1)
        pygame.draw.circle(surf, col, (x, y), r2, 1)
        h = max(2, int(8 * pulse))
        pygame.draw.polygon(surf, col, [
            (x, y - h),
            (x - h, y + h // 2),
            (x + h, y + h // 2),
        ], 1)

    def _draw_binding_sigil(self, surf, x, y):
        # A golden triangle scratched into the stone, point up. Three
        # bright lines drift across it at three different slow periods
        # regardless of the player -- the sigil is doing its work
        # whether anyone watches it or not.
        gold      = (200, 170, 60)
        gold_lo   = (130, 100, 30)
        h = 18
        pts = [(x, y - h), (x - h, y + h - 4), (x + h, y + h - 4)]
        pygame.draw.polygon(surf, gold_lo, pts)
        pygame.draw.polygon(surf, gold, pts, 1)
        for i, period in enumerate((9.0, 13.0, 17.0)):
            f = ((self.t / period) + i * 0.31) % 1.0
            ly = int(y - h + f * (h * 2 - 4))
            tri_t = (ly - (y - h)) / float(h * 2 - 4)
            w = max(1, int(h * tri_t))
            pygame.draw.line(surf, gold, (x - w, ly), (x + w, ly), 1)

    def _draw_yellow_sign(self, surf, x, y):
        # The Yellow Sign -- the cult's glyph, daubed on stone. An
        # asymmetric three-armed curl in jaundiced yellow, breathing
        # faintly. Deliberately wrong: the arms don't match, and the
        # eye sits off-centre. This is the cosmic-horror anchor; it
        # repeats at scale across the Scriptorium and Sign Chamber.
        pulse = 1.0 + math.sin(self.t * 1.1 + self.seed) * 0.10
        # A sickly jaundiced glow behind the glyph -- the one note of
        # real colour in the muck, and a focal point the eye catches.
        _light_pool(surf, int(x), int(y), int(30 * pulse), (206, 188, 84),
                    int(46 + 10 * math.sin(self.t * 1.1 + self.seed)))
        col = (196, 178, 72)
        dark = (92, 80, 28)
        R = 13 * pulse
        arms = ((-1.5, 1.05), (1.15, 0.85), (0.25, 1.3))
        for base_ang, lscale in arms:
            L = R * lscale
            pts = []
            seg = 6
            for i in range(seg + 1):
                t = i / seg
                a = base_ang + t * 1.05      # curl as the arm extends
                rr = L * t
                pts.append((int(x + math.cos(a) * rr),
                            int(y + math.sin(a) * rr)))
            pygame.draw.lines(surf, dark, False, pts, 4)
            pygame.draw.lines(surf, col, False, pts, 2)
        # Off-centre hooked eye at the heart of the glyph.
        ex, ey = int(x - 1), int(y + 1)
        pygame.draw.circle(surf, dark, (ex, ey), int(5 * pulse))
        pygame.draw.circle(surf, col, (ex, ey), int(5 * pulse), 1)
        pygame.draw.circle(surf, col, (ex + 2, ey - 1), 2)

    def _draw_chest(self, surf, x, y):
        # Wooden chest. Closed = lid down with a gold lock plate (and a
        # padlock if locked=True). Open = lid swung up and a dark
        # empty interior. State is driven by `open` (bool) and `locked`
        # (bool) kwargs; the scene's on_interact_fn flips `open` once
        # the chest has been emptied.
        open_state = self.kwargs.get("open", False)
        locked = self.kwargs.get("locked", False)
        # Body (lower half)
        pygame.draw.rect(surf, (110, 80, 50), (x - 9, y - 2, 18, 12))
        pygame.draw.rect(surf, (60, 40, 25), (x - 9, y - 2, 18, 12), 1)
        pygame.draw.line(surf, (40, 30, 20), (x - 9, y + 4),
                         (x + 9, y + 4), 1)
        if open_state:
            # Lid swung up, dark interior visible
            pygame.draw.polygon(surf, (130, 95, 60), [
                (x - 9, y - 2), (x - 9, y - 14),
                (x + 9, y - 14), (x + 9, y - 2),
            ])
            pygame.draw.polygon(surf, (60, 40, 25), [
                (x - 9, y - 2), (x - 9, y - 14),
                (x + 9, y - 14), (x + 9, y - 2),
            ], 1)
            pygame.draw.rect(surf, (10, 8, 6), (x - 6, y, 12, 6))
        else:
            # Lid closed
            pygame.draw.rect(surf, (130, 95, 60), (x - 9, y - 6, 18, 5))
            pygame.draw.rect(surf, (60, 40, 25), (x - 9, y - 6, 18, 5), 1)
            # Gold lock plate
            pygame.draw.rect(surf, (200, 180, 60), (x - 2, y - 3, 4, 5))
            pygame.draw.rect(surf, (40, 30, 20), (x - 2, y - 3, 4, 5), 1)
            if locked:
                # Iron padlock hanging from the plate
                pygame.draw.rect(surf, (60, 60, 70), (x - 1, y - 8, 2, 3))
                pygame.draw.circle(surf, (90, 90, 100), (x, y - 6), 2, 1)

    def _draw_missing_flyer(self, surf, x, y):
        # Pinned paper flyer -- beige sheet with a small portrait sketch
        # at the top, MISSING bar in red, and three text lines below.
        # Two corner tacks sell the "pinned to wood" read; the bottom-
        # right corner curls slightly so it doesn't look freshly
        # printed.
        # Paper body
        pygame.draw.rect(surf, (220, 200, 160), (x - 7, y - 12, 14, 24))
        pygame.draw.rect(surf, (60, 40, 25), (x - 7, y - 12, 14, 24), 1)
        # Corner curl (bottom-right)
        pygame.draw.polygon(surf, (180, 160, 130),
                            [(x + 7, y + 8), (x + 7, y + 12), (x + 3, y + 12)])
        pygame.draw.line(surf, (60, 40, 25), (x + 7, y + 8),
                         (x + 3, y + 12), 1)
        # MISSING bar (red) at top
        pygame.draw.rect(surf, (160, 30, 30), (x - 5, y - 11, 10, 2))
        # Portrait circle
        pygame.draw.circle(surf, (40, 28, 22), (x, y - 6), 3, 1)
        # Text lines
        for i in range(3):
            pygame.draw.line(surf, (60, 40, 25),
                             (x - 5, y + i * 3),
                             (x + 5, y + i * 3), 1)
        # Tacks
        pygame.draw.circle(surf, (200, 60, 60), (x - 5, y - 11), 1)
        pygame.draw.circle(surf, (200, 60, 60), (x + 5, y - 11), 1)

    def _draw_phantom_mark(self, surf, x, y):
        # A small chalk symbol scratched into a wall. Static (no anim).
        # Shape is suggestive but doesn't match any other game mark.
        pygame.draw.line(surf, (220, 220, 230), (x - 6, y - 4), (x + 6, y - 4), 1)
        pygame.draw.line(surf, (220, 220, 230), (x, y - 6), (x, y + 4), 1)
        pygame.draw.line(surf, (220, 220, 230), (x - 4, y + 4), (x + 4, y + 4), 1)
        pygame.draw.circle(surf, (220, 220, 230), (x, y), 1)

    def _draw_body(self, surf, x, y):
        # A slumped, fallen body. The kit reads at a glance: helmet beside the
        # head, spear on the ground, blood pool. Static -- this is a
        # decoration, not an NPC. Disappears after 2 re-entries via the
        # scene's on_enter logic.
        # Blood pool
        pygame.draw.ellipse(surf, (60, 6, 10), (x - 14, y + 2, 28, 8))
        pygame.draw.ellipse(surf, (90, 10, 14), (x - 11, y + 1, 22, 6))
        # Slumped torso (tabard-grey)
        pygame.draw.rect(surf, (110, 110, 130), (x - 9, y - 6, 18, 10))
        pygame.draw.rect(surf, (50, 50, 70), (x - 9, y - 6, 18, 10), 1)
        # Helmet, fallen sideways to the left of the body
        pygame.draw.rect(surf, (140, 140, 160), (x - 16, y - 4, 10, 7))
        pygame.draw.rect(surf, (40, 40, 60), (x - 14, y - 2, 4, 2))
        # Spear, dropped diagonally to the right
        pygame.draw.line(surf, (60, 40, 25), (x + 6, y - 4), (x + 18, y + 6), 2)
        pygame.draw.polygon(surf, (200, 200, 220),
                            [(x + 18, y + 6), (x + 14, y + 4), (x + 19, y + 3)])

    def _draw_gore(self, surf, x, y):
        # A slumped, broken figure. Read as "could be a person"; not an
        # animated NPC. Wide blood pool around it. The crutch pickup sits
        # adjacent so the noun does the heavy lifting.
        # Pool of blood (large, irregular-feeling via two ellipses)
        pygame.draw.ellipse(surf, (60, 6, 10), (x - 18, y, 36, 14))
        pygame.draw.ellipse(surf, (90, 10, 14), (x - 14, y - 2, 28, 10))
        pygame.draw.ellipse(surf, (40, 4, 8), (x - 6, y + 2, 12, 6))
        # Slumped torso
        pygame.draw.rect(surf, (60, 30, 30), (x - 9, y - 12, 18, 14))
        pygame.draw.rect(surf, (40, 18, 22), (x - 9, y - 12, 18, 14), 1)
        # Splayed limb
        pygame.draw.rect(surf, (60, 30, 30), (x + 8, y - 4, 12, 5))
        # Head, turned away
        pygame.draw.circle(surf, (80, 50, 50), (x - 6, y - 14), 5)
        # A few darker smudges for texture
        pygame.draw.line(surf, (30, 4, 6), (x - 10, y + 4), (x + 12, y + 6), 1)
        pygame.draw.line(surf, (30, 4, 6), (x - 8, y + 8), (x + 10, y + 8), 1)

    def _draw_computer(self, surf, x, y):
        # Beige 1990s-era CRT on a small desk. Power LED blinks. Screen
        # shows a slow pulsing cursor / scanlines -- nothing readable yet
        # (the ARG content lives behind this for later).
        # Desk
        pygame.draw.rect(surf, (110, 80, 50), (x - 14, y + 4, 28, 10))
        pygame.draw.rect(surf, (60, 40, 25), (x - 14, y + 4, 28, 10), 1)
        # CRT body
        pygame.draw.rect(surf, (200, 190, 170), (x - 12, y - 14, 24, 18))
        pygame.draw.rect(surf, (110, 100, 90), (x - 12, y - 14, 24, 18), 1)
        # Screen
        pygame.draw.rect(surf, (10, 14, 20), (x - 9, y - 12, 18, 14))
        # Scanlines (animated)
        for i in range(3):
            ly = y - 11 + ((int(self.t * 8) + i * 4) % 12)
            pygame.draw.line(surf, (40, 80, 60), (x - 8, ly), (x + 8, ly), 1)
        # Cursor blink
        if int(self.t * 2) % 2 == 0:
            pygame.draw.rect(surf, (120, 220, 140), (x - 8, y - 4, 3, 2))
        # Power LED
        led = (220, 80, 60) if int(self.t * 3) % 2 == 0 else (120, 40, 30)
        pygame.draw.rect(surf, led, (x + 9, y + 5, 2, 2))

    def _draw_creepy_tree(self, surf, x, y):
        """A leafless, gnarled tree. The trunk leans slightly off
        vertical so it never lines up with the regular trees on the
        same row -- a wrongness the player feels before they see it.
        Two darker oblong gouges in the bark sit where eyes would be,
        and a vertical gash beneath them suggests a pulled-open mouth.
        Branches splay outward like fingers, bare of all leaves."""
        trunk = (38, 28, 20)
        bark = (24, 16, 12)
        knot = (10, 6, 6)
        # Slow wind: the bare crown bends from a fixed base, branches
        # creaking sideways -- a dead tree working in the wind.
        sw = int(math.sin(self.t * 0.6 + self.seed) * 1.7)
        xt = x + sw
        # Leaning trunk -- base fixed at x, crown swayed to xt
        pygame.draw.polygon(surf, trunk, [
            (x - 4, y + 12), (xt - 5, y - 18),
            (xt + 4, y - 18), (x + 3, y + 12),
        ])
        pygame.draw.polygon(surf, bark, [
            (x - 4, y + 12), (xt - 5, y - 18),
            (xt + 4, y - 18), (x + 3, y + 12),
        ], 1)
        # Vertical bark cracks
        pygame.draw.line(surf, knot, (xt - 1, y - 16), (x - 2, y + 8), 1)
        pygame.draw.line(surf, knot, (xt + 1, y - 12), (x + 2, y + 4), 1)
        # Face in the bark -- eye gouges
        pygame.draw.ellipse(surf, knot, (xt - 3, y - 10, 2, 3))
        pygame.draw.ellipse(surf, knot, (xt + 1, y - 10, 2, 3))
        # Mouth gash (two stacked lines so it reads as torn-open)
        pygame.draw.line(surf, knot, (xt - 2, y - 4), (xt + 2, y - 4), 1)
        pygame.draw.line(surf, knot, (xt - 1, y - 3), (xt + 1, y - 3), 1)
        # Bare finger-branches
        for s, m, t in [
            ((xt, y - 16), (xt - 12, y - 22), (xt - 18, y - 18)),
            ((xt, y - 16), (xt + 12, y - 22), (xt + 18, y - 16)),
            ((xt, y - 18), (xt - 6, y - 28), (xt - 4, y - 36)),
            ((xt, y - 18), (xt + 6, y - 28), (xt + 4, y - 36)),
            ((xt, y - 18), (xt, y - 32), (xt + 2, y - 38)),
        ]:
            pygame.draw.line(surf, bark, s, m, 2)
            pygame.draw.line(surf, bark, m, t, 1)
        # Twigs at branch tips so they read as fingers, not sticks
        for tx_, ty_, dx_ in [(-18, -18, -1), (18, -16, 1),
                               (-4, -36, -1), (4, -36, 1), (2, -38, 1)]:
            pygame.draw.line(surf, bark,
                             (xt + tx_, y + ty_),
                             (xt + tx_ + dx_, y + ty_ - 3), 1)

    def _draw_hanging_figure(self, surf, x, y):
        """Vague humanoid silhouette suspended from a rope going off-
        tile upward. Slumped, no facial detail, very small slow sway.
        Used in the deep tree band of brimley and the cornfield's
        far rows."""
        sway = math.sin(self.t * 0.45 + self.seed) * 2.6
        sx_ = int(sway)
        # Long rope going up out of frame
        pygame.draw.line(surf, (140, 110, 70),
                         (x, y - 32), (x + sx_, y - 14), 1)
        # Knot at neck
        pygame.draw.circle(surf, (90, 60, 30), (x + sx_, y - 14), 2)
        # Slumped head
        pygame.draw.circle(surf, (20, 16, 22), (x + sx_, y - 10), 4)
        # Body / robes (trapezoid hanging straight down)
        pygame.draw.polygon(surf, (16, 12, 18), [
            (x + sx_ - 5, y - 8), (x + sx_ + 5, y - 8),
            (x + sx_ + 7, y + 12), (x + sx_ - 7, y + 12),
        ])
        pygame.draw.polygon(surf, (4, 2, 6), [
            (x + sx_ - 5, y - 8), (x + sx_ + 5, y - 8),
            (x + sx_ + 7, y + 12), (x + sx_ - 7, y + 12),
        ], 1)
        # Limp arms drooping at sides
        pygame.draw.line(surf, (16, 12, 18),
                         (x + sx_ - 5, y - 6), (x + sx_ - 7, y + 4), 2)
        pygame.draw.line(surf, (16, 12, 18),
                         (x + sx_ + 5, y - 6), (x + sx_ + 7, y + 4), 2)
        # Limp feet
        pygame.draw.line(surf, (8, 6, 10),
                         (x + sx_ - 4, y + 12), (x + sx_ - 4, y + 14), 2)
        pygame.draw.line(surf, (8, 6, 10),
                         (x + sx_ + 4, y + 12), (x + sx_ + 4, y + 14), 2)

    def _draw_dead_crow(self, surf, x, y):
        """A crow lying on its side -- one stiff leg pointing up, wing
        splayed, glazed-film eye. A few loose feathers around it.
        Static. Read as a dead bird, not a sleeping one."""
        # Body
        pygame.draw.ellipse(surf, (8, 8, 12), (x - 6, y - 1, 12, 5))
        pygame.draw.ellipse(surf, (16, 16, 20), (x - 6, y - 1, 12, 5), 1)
        # Head turned away with film-eye
        pygame.draw.circle(surf, (8, 8, 12), (x - 7, y), 2)
        pygame.draw.circle(surf, (90, 90, 70), (x - 8, y), 1)
        # Stiff leg sticking up + foot
        pygame.draw.line(surf, (40, 30, 20), (x + 2, y - 1), (x + 2, y - 6), 1)
        pygame.draw.line(surf, (40, 30, 20), (x + 2, y - 6), (x + 4, y - 7), 1)
        # Splayed wing
        pygame.draw.polygon(surf, (4, 4, 8),
                            [(x + 1, y - 1), (x + 7, y - 4),
                             (x + 6, y), (x + 1, y + 1)])
        # Loose feathers
        for fx, fy in [(-9, 4), (8, 4), (-3, 5)]:
            pygame.draw.line(surf, (8, 8, 12),
                             (x + fx, y + fy),
                             (x + fx + 1, y + fy - 2), 1)

    def _draw_claw_marks(self, surf, x, y):
        """Five parallel deep gouges torn diagonally across a wall.
        Each gouge has a rawer outer band and a near-black floor so
        it reads as cut INTO the surface, not painted on. Stroke
        jitter is per-instance via self.seed."""
        rng = random.Random(self.seed)
        outer = (60, 30, 30)
        deep = (16, 6, 10)
        for i in range(5):
            ox = -10 + i * 5 + rng.randint(-1, 1)
            top = (x + ox, y - 8)
            bot = (x + ox + 4 + rng.randint(-1, 1), y + 8)
            pygame.draw.line(surf, outer, top, bot, 2)
            pygame.draw.line(surf, deep, top, bot, 1)

    def _draw_bloody_handprint(self, surf, x, y):
        """A blood-red handprint pressed onto a surface, with three
        downward streaks where the fingers dragged on the way off.
        Palm sits darker than the fingertip pads -- the hand pushed
        off and smeared as it left."""
        palm = (140, 20, 28)
        drip = (80, 10, 18)
        bright = (180, 32, 36)
        # Palm
        pygame.draw.ellipse(surf, palm, (x - 5, y - 2, 10, 7))
        # Four finger pads + thumb
        pygame.draw.circle(surf, bright, (x - 4, y - 5), 1)
        pygame.draw.circle(surf, bright, (x - 1, y - 6), 1)
        pygame.draw.circle(surf, bright, (x + 2, y - 6), 1)
        pygame.draw.circle(surf, bright, (x + 5, y - 4), 1)
        pygame.draw.circle(surf, bright, (x - 6, y - 1), 1)
        # Downward drag streaks
        pygame.draw.line(surf, drip, (x - 3, y + 4), (x - 3, y + 12), 1)
        pygame.draw.line(surf, drip, (x, y + 4), (x, y + 14), 1)
        pygame.draw.line(surf, drip, (x + 3, y + 4), (x + 3, y + 11), 1)

    def _draw_cellar_hatch(self, surf, x, y):
        """A floor hatch -- wood box flush to the ground, plank seams,
        iron pull-ring centred on top. Identical visual to the `L`
        ladder-down tile but drawn as a decoration so the scene can
        gate the trip down behind an E-press handler instead of an
        auto-transition. Used in the barn to replace the chest-as-
        trapdoor placeholder."""
        pygame.draw.rect(surf, (110, 80, 50), (x - 12, y - 12, 24, 24))
        pygame.draw.rect(surf, (60, 38, 24), (x - 12, y - 12, 24, 24), 2)
        pygame.draw.line(surf, (60, 38, 24),
                         (x - 12, y - 4), (x + 12, y - 4), 1)
        pygame.draw.line(surf, (60, 38, 24),
                         (x - 12, y + 4), (x + 12, y + 4), 1)
        pygame.draw.rect(surf, (50, 50, 60), (x - 4, y - 3, 8, 4))
        pygame.draw.rect(surf, (30, 30, 38), (x - 4, y - 3, 8, 4), 1)
        pygame.draw.circle(surf, (180, 180, 200), (x, y + 2), 4, 2)
        pygame.draw.circle(surf, (90, 90, 110), (x, y + 2), 4, 1)

    def _draw_gas_pump(self, surf, x, y):
        """A 1990s rural gas pump. Beige body, red side panel, a
        rubber hose looping back into the pump. The dial wheel
        creeps slowly so the pump reads as plugged in but unused."""
        body = (200, 190, 170)
        edge = (60, 50, 40)
        red = (160, 40, 40)
        hose = (20, 18, 22)
        # Base
        pygame.draw.rect(surf, (90, 90, 100), (x - 6, y + 8, 12, 4))
        # Body column
        pygame.draw.rect(surf, body, (x - 6, y - 16, 12, 24))
        pygame.draw.rect(surf, edge, (x - 6, y - 16, 12, 24), 1)
        # Red side panel
        pygame.draw.rect(surf, red, (x - 6, y - 16, 12, 6))
        # Display window
        pygame.draw.rect(surf, (10, 14, 20), (x - 4, y - 8, 8, 5))
        # Slowly creeping dial digits
        digit = int(self.t * 0.7) % 10
        pygame.draw.rect(surf, (40, 200, 60),
                         (x - 3 + (digit % 4) * 2, y - 7, 1, 3))
        # Nozzle hook + hose looping back
        pygame.draw.line(surf, hose, (x + 6, y - 6), (x + 9, y - 4), 1)
        pygame.draw.line(surf, hose, (x + 9, y - 4), (x + 9, y + 4), 1)
        pygame.draw.line(surf, hose, (x + 9, y + 4), (x + 6, y + 6), 1)
        # Logo decal
        pygame.draw.rect(surf, (220, 200, 80), (x - 3, y - 14, 6, 2))

    def _draw_payphone(self, surf, x, y):
        """1990s glass-walled phone booth. Vertical box with metal
        framing, clear glass body, a black handset on a chrome cord,
        and a small red 'in use' light that blinks irregularly. The
        receiver sits slightly off the cradle on a per-seed schedule
        -- as if someone just hung up. The booth replaces a 'lantern'
        placeholder in village.py."""
        # Foundation slab
        pygame.draw.rect(surf, (60, 60, 70), (x - 9, y + 12, 18, 4))
        # Booth body (glass)
        pygame.draw.rect(surf, (140, 170, 200), (x - 8, y - 22, 16, 34))
        # Frame
        pygame.draw.rect(surf, (40, 40, 50), (x - 8, y - 22, 16, 34), 1)
        pygame.draw.line(surf, (40, 40, 50),
                         (x - 8, y - 6), (x + 8, y - 6), 1)
        # Roof cap
        pygame.draw.rect(surf, (50, 50, 60), (x - 10, y - 24, 20, 4))
        # Inner phone unit (metal box on the back wall)
        pygame.draw.rect(surf, (90, 90, 100), (x - 5, y - 16, 10, 8))
        pygame.draw.rect(surf, (40, 40, 50), (x - 5, y - 16, 10, 8), 1)
        # Handset hanging slightly off the hook (off-cradle anomaly)
        off_cradle = (self.t + self.seed * 0.07) % 8.0
        cord_y = y - 4 if off_cradle < 4.0 else y - 2
        # Cord (chromed line)
        pygame.draw.line(surf, (180, 180, 200),
                         (x - 4, y - 12), (x - 4, cord_y), 1)
        # Handset body
        pygame.draw.rect(surf, (10, 10, 14), (x - 6, cord_y, 4, 2))
        # Red "in use" light, blinks irregularly
        light_phase = (self.t * 1.7 + self.seed * 0.3) % 3.0
        if light_phase < 0.4:
            pygame.draw.rect(surf, (220, 60, 50), (x + 3, y - 18, 2, 2))
        else:
            pygame.draw.rect(surf, (90, 24, 20), (x + 3, y - 18, 2, 2))
        # Coin slot
        pygame.draw.line(surf, (10, 10, 14),
                         (x - 1, y - 10), (x + 1, y - 10), 1)

    def _draw_pickup_truck(self, surf, x, y):
        """A dead farm pickup, ~2.5 tiles long -- big, weathered, and
        long abandoned: faded muddy paint eaten through with rust,
        cracked-out windows, sagging on a flat tire, weeds growing up
        through the bed. The truck that drove for the county line and got
        handed back. Pair with solid 'X' tiles so the player can't walk
        through it. Faces right (nosed east, into the tree line)."""
        rng = random.Random(self.seed)
        # Sunk, oversized contact shadow under the whole hulk.
        sh = pygame.Surface((110, 34), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 95), (0, 0, 110, 34))
        surf.blit(sh, (x - 52, y + 6))
        body = (96, 88, 66)          # faded, dirtied paint -- muddy tan/olive
        body_dark = (52, 48, 36)
        rust = (118, 60, 32)
        rust_dk = (78, 40, 22)
        glass = (60, 70, 70)         # dead, grimy glass
        tire = (24, 22, 26)
        # ---- Bed (rear/left), a big open rusted box ----
        pygame.draw.rect(surf, body, (x - 50, y - 16, 38, 30))
        pygame.draw.rect(surf, body_dark, (x - 50, y - 16, 38, 30), 2)
        pygame.draw.rect(surf, (40, 38, 30), (x - 46, y - 12, 30, 22))   # cavity
        # Weeds growing up through the bed and the wheel wells.
        for _ in range(9):
            wx = x - 44 + rng.randint(0, 28)
            wy = y - 10 + rng.randint(0, 18)
            g = 60 + rng.randint(0, 40)
            pygame.draw.line(surf, (44, g, 44), (wx, wy), (wx - 1, wy - 6), 1)
        # ---- Cab ----
        pygame.draw.rect(surf, body, (x - 12, y - 24, 34, 38))
        pygame.draw.rect(surf, body_dark, (x - 12, y - 24, 34, 38), 2)
        # Roof, sun-bleached + rust-blistered.
        pygame.draw.rect(surf, (108, 100, 78), (x - 10, y - 22, 30, 12))
        # Windshield -- cracked, mostly dark.
        pygame.draw.polygon(surf, glass, [
            (x - 6, y - 20), (x + 16, y - 20), (x + 19, y - 8), (x - 6, y - 8)])
        pygame.draw.line(surf, (150, 150, 140), (x - 2, y - 20), (x + 10, y - 9), 1)
        pygame.draw.line(surf, (150, 150, 140), (x + 10, y - 18), (x + 4, y - 8), 1)
        pygame.draw.rect(surf, body_dark, (x - 6, y - 20, 25, 12), 1)
        # Side window, glass gone -- just a dark hole.
        pygame.draw.rect(surf, (22, 22, 26), (x + 14, y - 6, 8, 12))
        # ---- Hood / front (right) ----
        pygame.draw.rect(surf, body, (x + 22, y - 8, 16, 22))
        pygame.draw.rect(surf, body_dark, (x + 22, y - 8, 16, 22), 2)
        pygame.draw.rect(surf, (150, 140, 90), (x + 37, y - 2, 3, 6))    # dead headlight
        # Bent front bumper, hanging.
        pygame.draw.line(surf, (96, 92, 96), (x + 38, y + 12), (x + 42, y + 16), 2)
        # ---- Rust eating the body (deterministic blotches) ----
        for _ in range(14):
            bx = x - 48 + rng.randint(0, 84)
            by = y - 22 + rng.randint(0, 34)
            r = rng.randint(2, 5)
            pygame.draw.circle(surf, rust if rng.random() < 0.6 else rust_dk,
                               (bx, by), r)
        # Long rust runs bleeding down from the seams.
        for sx0 in (x - 44, x - 30, x - 6, x + 16, x + 30):
            pygame.draw.line(surf, rust_dk, (sx0, y + 2), (sx0, y + 12), 1)
        # ---- Wheels: rear sound, front flat (the hulk sags forward) ----
        pygame.draw.circle(surf, tire, (x - 36, y + 13), 7)
        pygame.draw.circle(surf, (60, 58, 60), (x - 36, y + 13), 3)
        pygame.draw.ellipse(surf, tire, (x + 20, y + 13, 18, 8))         # flat tire
        pygame.draw.rect(surf, (60, 58, 60), (x + 27, y + 15, 4, 3))

    def _draw_headstone(self, surf, x, y):
        """A weathered grave marker set crooked in the dirt -- a
        rounded slab or a cross, leaning, mossy, its inscription worn to
        illegible scratches. Per-instance variation (seed) so a row of
        them reads as graves, never a clean grid of identical rocks."""
        rng = random.Random(self.seed)
        h = rng.randint(18, 26)
        w = rng.randint(11, 15)
        lean = rng.randint(-4, 4)              # top shifted sideways = crooked
        cross = rng.random() < 0.30
        stone = (94, 92, 90)
        stone_dk = (56, 54, 54)
        moss = (58, 74, 50)
        # Sit the marker's foot down on its ground shadow (drawn at y+16).
        # Without this the stone's base rested at the tile centre while the
        # shadow sat a half-tile lower, so the graves read as floating.
        b = y + 14
        tx = x + lean
        top = b - h
        # Turned dirt at the foot.
        pygame.draw.ellipse(surf, (30, 26, 23), (x - w // 2 - 2, b, w + 4, 7))
        if cross:
            pygame.draw.line(surf, stone, (tx, top), (x, b), 5)
            pygame.draw.line(surf, stone, (tx - w // 2, top + h // 3),
                             (tx + w // 2, top + h // 3), 5)
            pygame.draw.line(surf, stone_dk, (tx, top), (x, b), 1)
        else:
            pts = [(x - w // 2, b), (x - w // 2 + lean, top + 5),
                   (tx - w // 4, top), (tx + w // 4, top),
                   (x + w // 2 + lean, top + 5), (x + w // 2, b)]
            pygame.draw.polygon(surf, stone, pts)
            pygame.draw.polygon(surf, stone_dk, pts, 1)
            for i in range(2):                 # illegible inscription
                ly = top + 9 + i * 5
                lx = x - w // 4 + int(lean * (1 - (ly - top) / h))
                pygame.draw.line(surf, stone_dk, (lx, ly), (lx + w // 2, ly), 1)
        pygame.draw.circle(surf, moss, (x - w // 4, b - 2), 2)

    def _draw_player_car(self, surf, x, y):
        """A faded-red 1990s sedan, parked. Approx 3 tiles wide, 1.5
        tiles tall -- properly sized so it reads as a real vehicle
        the player physically can't squeeze past. Pair with a solid
        'X' tile under it so collision matches the silhouette."""
        body = (140, 60, 60)
        body_dark = (80, 32, 32)
        glass = (140, 170, 200)
        tire = (20, 18, 22)
        chrome = (200, 200, 210)
        # Lower body
        pygame.draw.rect(surf, body, (x - 28, y - 4, 56, 16))
        pygame.draw.rect(surf, body_dark, (x - 28, y - 4, 56, 16), 1)
        # Greenhouse / roof
        pygame.draw.rect(surf, body, (x - 18, y - 16, 36, 12))
        pygame.draw.rect(surf, body_dark, (x - 18, y - 16, 36, 12), 1)
        # Windshield + rear window slants
        pygame.draw.polygon(surf, glass, [
            (x - 18, y - 4), (x - 14, y - 14),
            (x - 6, y - 14), (x - 6, y - 4),
        ])
        pygame.draw.polygon(surf, glass, [
            (x + 6, y - 4), (x + 6, y - 14),
            (x + 14, y - 14), (x + 18, y - 4),
        ])
        # Side window
        pygame.draw.rect(surf, glass, (x - 5, y - 14, 10, 11))
        pygame.draw.rect(surf, body_dark, (x - 5, y - 14, 10, 11), 1)
        # Door seam (centre split)
        pygame.draw.line(surf, body_dark, (x, y - 3), (x, y + 10), 1)
        # Roof rack with rolled tarp
        pygame.draw.line(surf, chrome, (x - 18, y - 16), (x + 18, y - 16), 1)
        pygame.draw.rect(surf, (110, 80, 60), (x - 14, y - 19, 28, 3))
        pygame.draw.line(surf, (60, 40, 25),
                         (x - 14, y - 17), (x + 14, y - 17), 1)
        # Headlights
        pygame.draw.rect(surf, (220, 220, 180), (x + 27, y - 1, 2, 4))
        pygame.draw.rect(surf, (220, 220, 180), (x + 27, y + 5, 2, 4))
        # Tail lights
        pygame.draw.rect(surf, (200, 30, 30), (x - 29, y - 1, 2, 4))
        pygame.draw.rect(surf, (200, 30, 30), (x - 29, y + 5, 2, 4))
        # Bumpers (chrome)
        pygame.draw.rect(surf, chrome, (x - 30, y + 10, 60, 2))
        # Wheels
        pygame.draw.circle(surf, tire, (x - 19, y + 12), 5)
        pygame.draw.circle(surf, tire, (x + 19, y + 12), 5)
        pygame.draw.circle(surf, chrome, (x - 19, y + 12), 2)
        pygame.draw.circle(surf, chrome, (x + 19, y + 12), 2)
        # Antenna
        pygame.draw.line(surf, chrome, (x + 16, y - 16), (x + 18, y - 24), 1)

    def _draw_mirror(self, surf, x, y):
        """Wall-mounted mirror with a slim wood frame. The reflection
        shows a faint grey humanoid silhouette that doesn't match the
        room (no player, no NPC -- just an extra figure). On a slow
        per-seed cycle, the silhouette's position shifts by a pixel
        as if it stepped sideways while you weren't looking. The
        wrongness is small enough that the player questions whether
        they imagined it."""
        frame = (90, 60, 40)
        edge = (50, 32, 18)
        glass = (60, 70, 90)
        glass_hl = (110, 130, 160)
        # Frame
        pygame.draw.rect(surf, frame, (x - 7, y - 12, 14, 22))
        pygame.draw.rect(surf, edge, (x - 7, y - 12, 14, 22), 1)
        # Glass
        pygame.draw.rect(surf, glass, (x - 5, y - 10, 10, 18))
        # Reflection highlights (diagonal gleam)
        pygame.draw.line(surf, glass_hl,
                         (x - 4, y - 9), (x + 1, y - 4), 1)
        pygame.draw.line(surf, glass_hl,
                         (x + 1, y + 5), (x + 4, y + 2), 1)
        # The wrong silhouette inside the glass. Position shifts by 1
        # pixel on a slow cycle keyed to seed so each mirror has its
        # own anomaly schedule.
        cycle = 11.0
        local = (self.t + self.seed * 0.13) % cycle
        shift = -1 if local > (cycle / 2) else 1
        sil_col = (30, 28, 36)
        pygame.draw.rect(surf, sil_col,
                         (x - 2 + shift, y - 5, 3, 8))
        pygame.draw.circle(surf, sil_col,
                           (x - 1 + shift, y - 6), 1)
        # Eye-glints on the silhouette -- two pinprick whites that
        # only appear during the brief "wrong" window.
        if local < 0.4:
            try:
                surf.set_at((x - 2 + shift, y - 6), (240, 240, 240))
                surf.set_at((x + shift, y - 6), (240, 240, 240))
            except (IndexError, ValueError):
                pass

    def _draw_wrong_radio(self, surf, x, y):
        """A 1990s portable transistor radio sitting on a surface.
        Brown plastic body, chrome tuning dial, leather carry strap
        slumped beside it. The dial creeps clockwise on a slow cycle
        -- nobody is touching it. Visible static lines crawl across
        the speaker grille. Replaces or layers on top of the
        existing 'radio' deco when the wrongness should be visible."""
        body = (90, 60, 40)
        edge = (50, 32, 18)
        chrome = (180, 180, 200)
        # Body
        pygame.draw.rect(surf, body, (x - 10, y - 5, 20, 12))
        pygame.draw.rect(surf, edge, (x - 10, y - 5, 20, 12), 1)
        # Speaker grille (left side) with crawling static lines
        pygame.draw.rect(surf, (20, 18, 22), (x - 9, y - 3, 8, 8))
        rng_t = self.t * 6
        for i in range(3):
            sy = int(y - 3 + (rng_t + i * 3) % 8)
            pygame.draw.line(surf, (110, 130, 110),
                             (x - 8, sy), (x - 2, sy), 1)
        # Tuning dial (right side) -- needle creeps
        pygame.draw.rect(surf, (20, 18, 22), (x, y - 3, 8, 6))
        pygame.draw.line(surf, edge, (x, y), (x + 8, y), 1)
        needle_x = x + int((math.sin(self.t * 0.4 + self.seed) + 1) * 4)
        pygame.draw.line(surf, (220, 60, 60),
                         (needle_x, y - 3), (needle_x, y + 3), 1)
        # Antenna
        pygame.draw.line(surf, chrome, (x + 8, y - 5), (x + 12, y - 12), 1)
        # Carry strap slumped
        pygame.draw.line(surf, (50, 32, 18), (x - 10, y - 5), (x - 14, y), 1)

    def _draw_wrong_photo(self, surf, x, y):
        """A framed photograph whose subjects degrade between visits.
        First visit: a family of three. Subsequent visits: faces
        progressively erased -- eyes go first, then mouths, then the
        whole face. Driven by `stage` kwarg (0..3). When stage>=2,
        a single fresh red dot appears in the corner of the frame
        as if someone marked it."""
        stage = self.kwargs.get("stage", 0)
        # Frame
        pygame.draw.rect(surf, (140, 110, 70), (x - 10, y - 8, 20, 16))
        pygame.draw.rect(surf, (60, 40, 25), (x - 10, y - 8, 20, 16), 1)
        # Photo paper
        pygame.draw.rect(surf, (200, 190, 170), (x - 8, y - 6, 16, 12))
        # Three figures
        skin = (220, 190, 160)
        clothes_a = (160, 80, 100)
        clothes_b = (80, 100, 140)
        clothes_c = (180, 160, 80)
        # Adult man (centre)
        pygame.draw.rect(surf, clothes_b, (x - 1, y - 2, 2, 6))
        pygame.draw.circle(surf, skin, (x, y - 3), 1)
        # Adult woman (right)
        pygame.draw.rect(surf, clothes_a, (x + 2, y - 2, 2, 6))
        pygame.draw.circle(surf, skin, (x + 3, y - 3), 1)
        # Child (left)
        pygame.draw.rect(surf, clothes_c, (x - 4, y, 2, 4))
        pygame.draw.circle(surf, skin, (x - 3, y - 1), 1)
        # Eye dots -- present at stage 0, gone by stage 1+.
        if stage < 1:
            pygame.draw.circle(surf, (10, 10, 14), (x, y - 3), 1)
            pygame.draw.circle(surf, (10, 10, 14), (x + 3, y - 3), 1)
            pygame.draw.circle(surf, (10, 10, 14), (x - 3, y - 1), 1)
        # Mouth lines -- gone by stage 2+.
        if stage < 2:
            pygame.draw.line(surf, (90, 60, 70),
                             (x - 1, y - 2), (x + 1, y - 2), 1)
        # Face-erase scratches -- appear at stage 2+, oblitering each
        # face entirely.
        if stage >= 2:
            for ex, ey in [(x, y - 3), (x + 3, y - 3), (x - 3, y - 1)]:
                pygame.draw.line(surf, (200, 190, 170),
                                 (ex - 1, ey), (ex + 1, ey), 1)
        # Red corner dot
        if stage >= 2:
            pygame.draw.circle(surf, (200, 40, 40),
                               (x + 8, y - 6), 1)
