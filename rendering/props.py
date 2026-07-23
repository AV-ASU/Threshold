"""Volumetric NON-box props for the oblique camera (DESIGN.md §10 dress).

rendering/furniture.py turns upright furniture into axis-aligned BOXES. This is
its sibling for the shapes a box can't express -- bodies of revolution: the
**well** (a round stone drum with a winch gallows), stone **pillars**, cistern
**basins** brimming with black water, and raked **grain heaps**. Each is keyed
by decoration `kind`, drawn through the same Camera in the tilt path (depth
sorted alongside furniture). The flat top-down game (pitch 0) never calls this -- it
falls back to the 2D `_draw_<kind>` sprites in entities/decoration.py.
"""
import math
import random
import pygame
from rendering.solids import draw_solid, draw_box, draw_billboard, _shade


def _disc(surf, cam, wx, wy, hz, rx, ry, col, fill=True, width=2):
    """A pitch-squashed ellipse cap at world height hz (radii in world px)."""
    cx, cy = cam.project(wx, wy, hz)
    hw = int(rx * cam.scale)
    hd = int(ry * cam.ground_squash() * cam.scale)
    if hw < 1 or hd < 1:
        return
    pygame.draw.ellipse(surf, col, (cx - hw, cy - hd, hw * 2, hd * 2),
                        0 if fill else max(1, width))


def _draw_well_solid(surf, cam, deco):
    """The wellhead, as a real volume. Big enough to lean over. Course-laid
    fitted-stone drum with a mossy crown, a sunken throat that fades from rim
    light into abyss black across multiple inset rings (the descent), and a
    timber winch gallows with a hand crank, rope wrap, and a battered bucket
    half-into the shaft. The ONLY way down to the Works -- it must read like
    a thing, not a tile."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    R = 28 * s                                  # was 17 -- monumental
    H_DRUM = 16 * s                             # drum rises above the path
    drum = {"body": (96, 94, 100), "lo": (52, 50, 56), "rim": (152, 152, 164)}
    # Body of revolution: belled base + straight drum + slight flare at the rim
    draw_solid(surf, cam, wx, wy,
               [(0, R * 1.06, R * 1.06),
                (3 * s, R, R),
                (H_DRUM - 2 * s, R, R),
                (H_DRUM, R * 1.04, R * 1.04)], drum)
    # Stone-course joint bands so the drum reads as fitted stone, not a tube
    for hz in (5 * s, 9 * s, 13 * s):
        _disc(surf, cam, wx, wy, hz, R * 1.005, R * 1.005,
              _shade(drum["lo"], 0.85), fill=False, width=1)
    # Crown ring: a darker mortar groove just under the rim, then the rim cap
    _disc(surf, cam, wx, wy, H_DRUM - 1 * s, R * 0.99, R * 0.99,
          _shade(drum["lo"], 0.6), fill=False, width=1)
    _disc(surf, cam, wx, wy, H_DRUM, R * 1.04, R * 1.04,
          drum["rim"], fill=False, width=2)
    # Moss on the crown: a few short arcs, not a closed ring, so it looks
    # patchy rather than painted on. Two clumps, NE and SW.
    moss = (74, 92, 56)
    cx, cy = cam.project(wx, wy, H_DRUM)
    rxp = int(R * 1.02 * cam.scale)
    ryp = int(R * 1.02 * cam.ground_squash() * cam.scale)
    if rxp > 2 and ryp > 1:
        rect = (cx - rxp, cy - ryp, rxp * 2, ryp * 2)
        pygame.draw.arc(surf, moss, rect, math.radians(20),
                        math.radians(70), 2)
        pygame.draw.arc(surf, moss, rect, math.radians(200),
                        math.radians(245), 2)
        pygame.draw.arc(surf, _shade(moss, 1.2), rect, math.radians(30),
                        math.radians(55), 1)
    # THROAT: nested inset rings that fade from inner-rim grey to abyss black
    # so the shaft reads as a deep hole, not a painted dot. Each ring sits a
    # touch lower than the previous so the descent has a real lip.
    for i, (r_f, h_f, col) in enumerate([
            (0.90, H_DRUM - 0.5 * s, (28, 26, 30)),
            (0.80, H_DRUM - 1.8 * s, (16, 14, 16)),
            (0.66, H_DRUM - 3.5 * s, (6, 6, 8)),
            (0.50, H_DRUM - 5.5 * s, (2, 2, 3)),
            (0.32, H_DRUM - 8.0 * s, (0, 0, 0))]):
        _disc(surf, cam, wx, wy, h_f, R * r_f, R * r_f, col)
    # A faint rim-light scratch where the inner stones meet the throat
    _disc(surf, cam, wx, wy, H_DRUM - 0.4 * s, R * 0.92, R * 0.92,
          _shade(drum["rim"], 0.7), fill=False, width=1)
    # Timber winch gallows: thicker posts (a real beam you'd hang weight on),
    # cross-beam over the centre, a hand crank on the east post, rope wrap on
    # the beam, and the rope feeding into the dark.
    post = (120, 88, 52)
    beam_h = 44 * s
    py = wy + R * 0.55
    lw = max(3, int(4 * s))
    for ox in (-R * 0.92, R * 0.92):
        bx, by = cam.project(wx + ox, py, 0)
        tx, ty = cam.project(wx + ox, py, beam_h)
        # post shaft (thick)
        pygame.draw.line(surf, post, (bx, by), (tx, ty), lw)
        pygame.draw.line(surf, _shade(post, 0.6), (bx, by), (tx, ty), 1)
        pygame.draw.line(surf, _shade(post, 1.25),
                         (bx - 1, by), (tx - 1, ty), 1)
    # Diagonal brace timbers between post base and beam centre (a sturdier
    # silhouette than two thin uprights)
    for ox in (-R * 0.92, R * 0.92):
        a = cam.project(wx + ox, py, 6 * s)
        b = cam.project(wx + ox * 0.35, py, beam_h - 1 * s)
        pygame.draw.line(surf, _shade(post, 0.85), a, b, max(2, int(2 * s)))
    bl = cam.project(wx - R * 0.92, py, beam_h)
    br = cam.project(wx + R * 0.92, py, beam_h)
    pygame.draw.line(surf, _shade(post, 1.25), bl, br, lw)
    pygame.draw.line(surf, _shade(post, 0.55), bl, br, 1)
    # Hand-crank: a small dark drum + handle off the east post
    cdx = R * 0.92
    cdh = beam_h * 0.6
    cd_b = cam.project(wx + cdx - 4 * s, py - 1, cdh)
    cd_t = cam.project(wx + cdx + 4 * s, py + 1, cdh)
    pygame.draw.line(surf, _shade(post, 0.45),
                     cd_b, cd_t, max(3, int(4 * s)))
    handle = cam.project(wx + cdx + 6 * s, py + 4 * s, cdh - 2 * s)
    pygame.draw.line(surf, post, cd_t, handle, max(2, int(2 * s)))
    # Rope wrap on the beam centre + the rope down into the throat
    rope = (152, 132, 94)
    rw_a = cam.project(wx - 3 * s, py, beam_h)
    rw_b = cam.project(wx + 3 * s, py, beam_h)
    pygame.draw.line(surf, rope, rw_a, rw_b, max(2, int(3 * s)))
    rt = cam.project(wx, py, beam_h - 1 * s)
    rb = cam.project(wx, wy + R * 0.15, H_DRUM - 6 * s)
    pygame.draw.line(surf, rope, rt, rb, max(1, int(2 * s)))
    # The bucket: a small wooden cylinder hanging off-centre on the rope,
    # half-eaten by the throat shadow. Anchors the gallows visually + gives
    # the well a "in use" feel.
    bx_w = wx - 1 * s
    by_w = wy + R * 0.12
    bz0 = H_DRUM - 7 * s
    bz1 = H_DRUM - 2 * s
    bR = 3.5 * s
    bk = {"body": (96, 70, 44), "lo": (50, 36, 22), "rim": (140, 104, 64)}
    draw_solid(surf, cam, bx_w, by_w, [(bz0, bR, bR), (bz1, bR, bR)], bk)
    _disc(surf, cam, bx_w, by_w, bz1, bR, bR, _shade(bk["lo"], 0.7),
          fill=False, width=1)
    # Rope's last inch sits ON the bucket handle
    bh_a = cam.project(bx_w - bR, by_w, bz1 + 1 * s)
    bh_b = cam.project(bx_w + bR, by_w, bz1 + 1 * s)
    pygame.draw.line(surf, rope, bh_a, bh_b, max(1, int(1.5 * s)))


def _draw_town_sign_solid(surf, cam, deco):
    """A wooden roadside signpost as real volume: two thin upright posts +
    a thicker board nailed across them, the town name burnt into the front
    face. The board catches the camera tilt as a flat plane instead of
    pointing at you forever."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    text = deco.kwargs.get("text", "BRIMLEY") if hasattr(deco, "kwargs") else "BRIMLEY"
    post_col = (62, 44, 28)
    post_lit = (88, 64, 40)
    board_col = (96, 70, 44)
    board_lit = (124, 92, 58)
    board_dk = (60, 42, 22)
    POST_H = 26 * s
    POST_T = 1.6 * s
    POST_DX = 9 * s
    # Two upright posts (thin box-extrude). Board is mounted to the FRONT
    # (south-facing) face so it reads facing the road.
    for ox in (-POST_DX, POST_DX):
        b = (cam.project(wx + ox - POST_T / 2, wy - POST_T / 2, 0),
             cam.project(wx + ox + POST_T / 2, wy - POST_T / 2, 0),
             cam.project(wx + ox + POST_T / 2, wy + POST_T / 2, 0),
             cam.project(wx + ox - POST_T / 2, wy + POST_T / 2, 0))
        t = (cam.project(wx + ox - POST_T / 2, wy - POST_T / 2, POST_H),
             cam.project(wx + ox + POST_T / 2, wy - POST_T / 2, POST_H),
             cam.project(wx + ox + POST_T / 2, wy + POST_T / 2, POST_H),
             cam.project(wx + ox - POST_T / 2, wy + POST_T / 2, POST_H))
        pygame.draw.polygon(surf, post_col, [b[3], b[2], t[2], t[3]])
        pygame.draw.polygon(surf, _shade(post_col, 0.7),
                            [b[1], b[2], t[2], t[1]])
        pygame.draw.polygon(surf, post_lit, [t[0], t[1], t[2], t[3]])
    # Board: a thin plank box. The BRIMLEY welcome board is bigger and
    # carries the town's civic boast; directional signs stay compact.
    welcome = (text == "BRIMLEY")
    BOARD_Z0 = POST_H * (0.38 if welcome else 0.55)
    BOARD_Z1 = POST_H * (1.00 if welcome else 0.95)
    BOARD_W = (22 if welcome else 14) * s
    BOARD_DEPTH = 1.0 * s
    by = wy - POST_T / 2 - BOARD_DEPTH * 0.6     # nailed to the FRONT of posts
    bb = (cam.project(wx - BOARD_W, by - BOARD_DEPTH / 2, BOARD_Z0),
          cam.project(wx + BOARD_W, by - BOARD_DEPTH / 2, BOARD_Z0),
          cam.project(wx + BOARD_W, by + BOARD_DEPTH / 2, BOARD_Z0),
          cam.project(wx - BOARD_W, by + BOARD_DEPTH / 2, BOARD_Z0))
    bt = (cam.project(wx - BOARD_W, by - BOARD_DEPTH / 2, BOARD_Z1),
          cam.project(wx + BOARD_W, by - BOARD_DEPTH / 2, BOARD_Z1),
          cam.project(wx + BOARD_W, by + BOARD_DEPTH / 2, BOARD_Z1),
          cam.project(wx - BOARD_W, by + BOARD_DEPTH / 2, BOARD_Z1))
    # FRONT face (this is what reads the text)
    front = [bb[0], bb[1], bt[1], bt[0]]
    pygame.draw.polygon(surf, board_col, front)
    pygame.draw.polygon(surf, board_dk, front, 1)
    # bottom edge highlight
    pygame.draw.line(surf, board_lit,
                     (int(bb[0][0]), int(bb[0][1])),
                     (int(bb[1][0]), int(bb[1][1])), 1)
    # top edge cap
    pygame.draw.polygon(surf, _shade(board_col, 1.18),
                        [bt[0], bt[1], bt[2], bt[3]])
    # right face (east end of board)
    pygame.draw.polygon(surf, _shade(board_col, 0.7),
                        [bb[1], bb[2], bt[2], bt[1]])
    # Render the text onto the FRONT face. We render at native pixel size
    # then warp via a polygon-bounded blit -- simpler approach: render onto
    # a small surface and blit centered on the projected board front centre
    # (the board is mostly facing the camera under pitch 55, so this reads).
    try:
        tcx = int((bb[0][0] + bb[1][0]) / 2)
        top_y = (bt[0][1] + bt[1][1]) / 2
        bot_y = (bb[0][1] + bb[1][1]) / 2
        span = max(1.0, bot_y - top_y)
        if welcome:
            # Three stacked lines: the name, the corn boast, the founding
            # year -- an old-timey painted welcome board (TODO #11; the
            # corn pride is a mundane human feat, never the door's doing).
            big = pygame.font.SysFont(None, max(9, int(9 * s * cam.scale)),
                                      bold=True)
            sm = pygame.font.SysFont(None, max(6, int(6 * s * cam.scale)),
                                     bold=True)
            for img, fr in ((big.render("BRIMLEY", True, (30, 20, 8)), 0.24),
                            (sm.render("NORTHERNMOST CORN", True,
                                       (44, 32, 16)), 0.55),
                            (sm.render("EST. 1894", True, (44, 32, 16)), 0.80)):
                yy = int(top_y + span * fr)
                surf.blit(img, (tcx - img.get_width() // 2,
                                yy - img.get_height() // 2))
        else:
            font = pygame.font.SysFont(None, max(7, int(7 * s * cam.scale)),
                                       bold=True)
            txt = font.render(text, True, (28, 18, 8))
            surf.blit(txt, (tcx - txt.get_width() // 2,
                            int((top_y + bot_y) / 2) - txt.get_height() // 2))
    except Exception:
        pass


def _draw_flagpole_solid(surf, cam, deco):
    """A weathered metal flagpole. Tall cylinder body of revolution + a
    rounded knob cap. The flag is a small drooping cloth quad that sways
    with deco.t. Half-mast and tattered, matching the schoolyard read."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    t = getattr(deco, "t", 0.0)
    seed = getattr(deco, "seed", 0)
    H = 34 * s
    R = 0.8 * s
    pole_pal = {"body": (130, 132, 138), "lo": (78, 80, 86),
                "rim": (190, 192, 200)}
    draw_solid(surf, cam, wx, wy,
               [(0, R * 1.2, R * 1.2), (2 * s, R, R), (H, R, R)],
               pole_pal)
    # rounded knob cap
    knob = cam.project(wx, wy, H)
    pygame.draw.circle(surf, pole_pal["rim"], knob, max(2, int(2 * s)))
    pygame.draw.circle(surf, pole_pal["lo"], knob, max(1, int(1 * s)), 1)
    # Half-mast flag: a small drooping cloth from z = H*0.55..H*0.75
    cloth = (66, 50, 50)
    cloth_dk = (40, 28, 28)
    sway = math.sin(t * 2.2 + seed * 0.1) * 1.4 * s
    fy_top = H * 0.78
    fy_bot = H * 0.52
    FW = 9 * s
    # Flag hangs off the east side of the pole (so it catches the wind in
    # the camera's view); its trailing edge ripples with sway.
    a_t = cam.project(wx + 0.5 * s, wy, fy_top)
    a_b = cam.project(wx + 0.5 * s, wy, fy_bot)
    b_t = cam.project(wx + FW + sway, wy + sway * 0.4, fy_top - 1 * s)
    b_b = cam.project(wx + FW * 0.7 + sway * 0.6, wy + sway * 0.4,
                      fy_bot + 1 * s)
    pygame.draw.polygon(surf, cloth, [a_t, b_t, b_b, a_b])
    pygame.draw.polygon(surf, cloth_dk, [a_t, b_t, b_b, a_b], 1)
    # frayed trailing edge: a few short rips
    for k in range(3):
        rx = b_t[0] + (b_b[0] - b_t[0]) * (k + 0.5) / 3
        ry = b_t[1] + (b_b[1] - b_t[1]) * (k + 0.5) / 3
        pygame.draw.line(surf, cloth_dk, (int(rx), int(ry)),
                         (int(rx + 1 + sway * 0.3), int(ry + 2)), 1)


def _draw_headstone_solid(surf, cam, deco):
    """A grave marker as a real volume: a thin stone slab leaning a few
    degrees off vertical, mossed at the foot, with a turned-dirt mound at
    its base. ~30% are crosses; the rest are rounded slabs. Per-seed
    variation so a row reads as graves, never a clean grid."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    seed = getattr(deco, "seed", 0)
    rng_h = 10 + (seed % 11)                       # 10..20 world units tall
    rng_w = 6 + ((seed >> 3) % 4)                  # 6..9 wide
    thick = 1.6 + ((seed >> 5) % 4) * 0.3          # ~1.6..2.5 deep
    lean_x = (((seed >> 7) % 9) - 4) * 0.25 * s    # crooked sideways lean
    lean_y = (((seed >> 9) % 5) - 1) * 0.20 * s    # forward/back lean
    cross = ((seed >> 11) & 7) == 0                # ~12% crosses
    H = rng_h * s
    W = rng_w * s
    T = thick * s
    # Turned-dirt mound (a flat dark oval on the ground beneath)
    _disc(surf, cam, wx, wy, 0.2, W + 4, T + 3, (32, 26, 22))
    _disc(surf, cam, wx, wy, 0.2, W + 1, T + 1, (52, 42, 32),
          fill=False, width=1)
    stone = {"body": (94, 92, 90), "lo": (52, 50, 50),
             "rim": (160, 158, 156)}
    if cross:
        # 3D cross: an upright beam + a transverse crossbar, both as thin
        # boxes so they catch a side face under tilt.
        # Upright trunk
        cx_top = wx + lean_x
        cy_top = wy + lean_y
        # box extruded between z=0 and z=H, x size T, y size T
        b = (cam.project(wx - T / 2, wy - T / 2, 0),
             cam.project(wx + T / 2, wy - T / 2, 0),
             cam.project(wx + T / 2, wy + T / 2, 0),
             cam.project(wx - T / 2, wy + T / 2, 0))
        t = (cam.project(cx_top - T / 2, cy_top - T / 2, H),
             cam.project(cx_top + T / 2, cy_top - T / 2, H),
             cam.project(cx_top + T / 2, cy_top + T / 2, H),
             cam.project(cx_top - T / 2, cy_top + T / 2, H))
        # near (south) face + east face
        pygame.draw.polygon(surf, stone["lo"], [b[3], b[2], t[2], t[3]])
        pygame.draw.polygon(surf, stone["body"], [b[1], b[2], t[2], t[1]])
        pygame.draw.polygon(surf, stone["rim"], [t[0], t[1], t[2], t[3]])
        # Crossbar at ~2/3 up the trunk
        cz = H * 0.66
        arm_w = W * 0.9
        arm_t = T * 0.9
        arm_h = T * 0.9
        # along x axis: from -arm_w to +arm_w, centred on the trunk
        # Apply the same lean fraction
        bx_off = lean_x * (cz / H)
        by_off = lean_y * (cz / H)
        # Two endpoints of the arm
        for sgn in (-1, 1):
            ax = wx + bx_off + sgn * arm_w * 0.5
            ay = wy + by_off
            ab = (cam.project(ax - arm_w / 2, ay - arm_t / 2, cz),
                  cam.project(ax + arm_w / 2, ay - arm_t / 2, cz),
                  cam.project(ax + arm_w / 2, ay + arm_t / 2, cz),
                  cam.project(ax - arm_w / 2, ay + arm_t / 2, cz))
            at = (cam.project(ax - arm_w / 2, ay - arm_t / 2, cz + arm_h),
                  cam.project(ax + arm_w / 2, ay - arm_t / 2, cz + arm_h),
                  cam.project(ax + arm_w / 2, ay + arm_t / 2, cz + arm_h),
                  cam.project(ax - arm_w / 2, ay + arm_t / 2, cz + arm_h))
            pygame.draw.polygon(surf, stone["lo"],
                                [ab[3], ab[2], at[2], at[3]])
            pygame.draw.polygon(surf, stone["rim"],
                                [at[0], at[1], at[2], at[3]])
    else:
        # Slab: a flat tablet, rounded top hinted by inset corner points.
        # Build the 8 corners (base 4 + top 4) of a leaning box.
        cx_top = wx + lean_x
        cy_top = wy + lean_y
        b = (cam.project(wx - W / 2, wy - T / 2, 0),
             cam.project(wx + W / 2, wy - T / 2, 0),
             cam.project(wx + W / 2, wy + T / 2, 0),
             cam.project(wx - W / 2, wy + T / 2, 0))
        # Rounded top: pinch the top width to 80% of base width
        topw = W * 0.84
        t = (cam.project(cx_top - topw / 2, cy_top - T / 2, H),
             cam.project(cx_top + topw / 2, cy_top - T / 2, H),
             cam.project(cx_top + topw / 2, cy_top + T / 2, H),
             cam.project(cx_top - topw / 2, cy_top + T / 2, H))
        # front (south, camera-facing) face
        pygame.draw.polygon(surf, stone["body"],
                            [b[3], b[2], t[2], t[3]])
        # west / east edge faces
        pygame.draw.polygon(surf, stone["lo"],
                            [b[0], b[3], t[3], t[0]])
        pygame.draw.polygon(surf, stone["lo"],
                            [b[1], b[2], t[2], t[1]])
        # cap top (catches the light)
        pygame.draw.polygon(surf, stone["rim"],
                            [t[0], t[1], t[2], t[3]])
        # Two scratched inscription lines on the front face
        sq = (b[3], b[2], t[2], t[3])
        for k, fy in enumerate((0.45, 0.60)):
            a = _quad_pt(sq, 0.20, fy)
            c = _quad_pt(sq, 0.80, fy)
            pygame.draw.line(surf, stone["lo"],
                             (int(a[0]), int(a[1])),
                             (int(c[0]), int(c[1])), 1)
    # Moss clump at the SW foot (low on the stone, near the dirt)
    moss = (58, 74, 50)
    moss_dk = (38, 50, 32)
    mx, my = cam.project(wx - W * 0.35, wy + T * 0.2, H * 0.12)
    pygame.draw.circle(surf, moss_dk, (int(mx), int(my)),
                       max(1, int(1.8 * s)))
    pygame.draw.circle(surf, moss, (int(mx - 1), int(my - 1)),
                       max(1, int(1.2 * s)))


def _quad_pt(quad, fx, fy):
    """Bilinear interpolation inside a 4-pt projected quad (TL, TR, BR, BL).
    Used to paint detail onto the leaning front face."""
    tl, tr, br, bl = quad
    ax = tl[0] + (tr[0] - tl[0]) * fx
    ay = tl[1] + (tr[1] - tl[1]) * fx
    bx = bl[0] + (br[0] - bl[0]) * fx
    by = bl[1] + (br[1] - bl[1]) * fx
    return (ax + (bx - ax) * fy, ay + (by - ay) * fy)


def _draw_pillar_solid(surf, cam, deco):
    """A round fitted-stone column with a flared base + capital, rising into
    the dark -- a colonnade upright + an occluder to round."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    R = 9 * s
    H = 50 * s
    pal = {"body": (104, 101, 106), "lo": (56, 54, 58), "rim": (150, 148, 154)}
    draw_solid(surf, cam, wx, wy,
               [(0, R * 1.18, R * 1.18), (5 * s, R, R),
                (H - 5 * s, R, R), (H, R * 1.2, R * 1.2)], pal)
    # faint banded joints
    for hz in (18 * s, 33 * s):
        _disc(surf, cam, wx, wy, hz, R, R, _shade(pal["lo"], 1.05),
              fill=False, width=1)


def _draw_cistern_basin_solid(surf, cam, deco):
    """A low round stone basin brimming with black water, a cold sheen on it."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    R = 13 * s
    H = 11 * s
    pal = {"body": (92, 96, 98), "lo": (50, 54, 56), "rim": (140, 146, 148)}
    draw_solid(surf, cam, wx, wy, [(0, R, R), (H, R, R)], pal)
    _disc(surf, cam, wx, wy, H, R * 0.82, R * 0.82, (14, 22, 26))
    _disc(surf, cam, wx, wy, H, R * 0.5, R * 0.5, (32, 52, 60),
          fill=False, width=1)


def _draw_grain_heap_solid(surf, cam, deco):
    """A raked cone of tithed grain, a ring of dark chaff settled at its
    base. (2026-07 mine retrofit: the old-blood ring is cut -- the tithe
    is an offering carried down by the willing; nobody bled into it.)"""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    R = 15 * s
    H = 13 * s
    pal = {"body": (150, 126, 70), "lo": (80, 64, 35), "rim": (198, 174, 110)}
    draw_solid(surf, cam, wx, wy,
               [(0, R, R), (H * 0.6, R * 0.6, R * 0.6),
                (H, R * 0.12, R * 0.12)], pal)
    _disc(surf, cam, wx, wy, 0.5, R * 0.96, R * 0.96, (58, 48, 30),
          fill=False, width=2)


def _draw_spoil_heap_solid(surf, cam, deco):
    """Shoveled spoil -- broken earth and stone waiting on the haul.
    Built from several offset lumps (never one smooth cone: a body of
    revolution reads as a lampshade under the tilt, not dug ground),
    with rubble scattered off its skirt and stones caught in the slope.
    The 2026-07 mine art pass: spoil lives where the work put it."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    seed = getattr(deco, "seed", 0)
    rng_v = [(seed >> (i * 3)) % 7 for i in range(8)]
    pal = {"body": (96, 82, 62), "lo": (56, 48, 36), "rim": (126, 110, 86)}
    pal_lo = {"body": (82, 70, 54), "lo": (48, 41, 31), "rim": (108, 94, 74)}
    # the main mound + two shoulder lumps, each its own squat cone with a
    # jittered footprint so the merged silhouette is irregular
    lumps = [
        (0.0, 0.0, (11 + rng_v[0]) * s, (10 + rng_v[1] % 4) * s, pal),
        ((-7 - rng_v[2]) * 0.9 * s, (4 + rng_v[3] % 3) * s,
         (7 + rng_v[3] % 3) * s, (6 + rng_v[4] % 3) * s, pal_lo),
        ((6 + rng_v[5] % 3) * s, (-5 - rng_v[6] % 3) * s,
         (6 + rng_v[6] % 3) * s, (5 + rng_v[7] % 3) * s, pal_lo),
    ]
    lumps.sort(key=lambda l: l[1])              # far-to-near for overdraw
    for lx, ly, lr, lh, lpal in lumps:
        draw_solid(surf, cam, wx + lx, wy + ly,
                   [(0, lr, lr * 0.92), (lh * 0.5, lr * 0.7, lr * 0.62),
                    (lh, lr * 0.22, lr * 0.18)], lpal)
    # rubble kicked off the skirt (flat, on the ground plane)
    for i in range(5):
        a = 0.7 + i * 1.27 + (seed % 5) * 0.5
        rr = (13 + rng_v[i % 8]) * 1.15 * s
        p = cam.project(wx + math.cos(a) * rr, wy + math.sin(a) * rr * 0.8, 0.5)
        pygame.draw.circle(surf, (74, 66, 54), (int(p[0]), int(p[1])),
                           max(1, int((1.0 + (rng_v[(i + 3) % 8] % 2)) * s)))
    # stones caught in the slope, catching what light there is
    for i in range(4):
        a = 0.9 + i * 1.6 + (seed % 5) * 0.4
        p = cam.project(wx + math.cos(a) * 6 * s,
                        wy + math.sin(a) * 5 * s, (4 + rng_v[i] % 4) * s)
        pygame.draw.circle(surf, (128, 124, 126), (int(p[0]), int(p[1])),
                           max(1, int(1.5 * s)))


def _draw_shoring_frame_solid(surf, cam, deco):
    """A DIY timber SET -- the mine's support frame in the Threshold's
    own grammar: two board uprights and a header beam you walk UNDER,
    built entirely from yaw-rotated boxes so the frame holds from every
    camera angle (never a flat card, never a turned column). kwargs:
    `ang` = the frame line's axis (the uprights sit +-span/2 along it),
    `span` = distance between upright centres in px. span<=1 draws a
    BROKEN set (a doubled upright and a sheared beam stub) -- the old
    workings' collapsed props."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    seed = getattr(deco, "seed", 0)
    ang = float(deco.kwargs.get("ang", 0.0))
    span = float(deco.kwargs.get("span", 0.0)) * s
    wood = {"top": (98, 76, 50), "side": (76, 58, 38), "dark": (62, 48, 32)}
    wood2 = {"top": (86, 66, 43), "side": (66, 50, 33), "dark": (46, 36, 25)}
    H = (26 + seed % 4) * s
    dx, dy = math.cos(ang), math.sin(ang)

    def upright(ux, uy, pal, hh):
        # a doubled sawn board (two thin boxes, one an offcut shorter)
        _vbox(surf, cam, ux - dx * 2.2 * s, uy - dy * 2.2 * s,
              4.4 * s, 3.0 * s, 0, hh, pal, yaw=ang, outline=False)
        _vbox(surf, cam, ux + dx * 2.2 * s, uy + dy * 2.2 * s,
              4.4 * s, 3.0 * s, 0, hh - (1 + seed % 2) * s, wood2,
              yaw=ang, outline=False)
        n = cam.project(ux, uy, hh - 2 * s)
        pygame.draw.circle(surf, (34, 30, 28), (int(n[0]), int(n[1])), 1)

    if span <= 1:
        # the broken set: one upright still standing, its beam sheared
        # off short -- the rest went with whatever it was holding
        upright(wx, wy, wood, H)
        _vbox(surf, cam, wx + dx * 6 * s, wy + dy * 6 * s,
              13 * s, 4.5 * s, H, H + 3 * s, wood, yaw=ang)
        return
    hs = span / 2.0
    half = deco.kwargs.get("half")
    if half == "a":
        # The -axis upright alone. Spanning frames are SPLIT by
        # Scene.add_decoration so each post depth-sorts at its own
        # anchor: one shared anchor gave the whole set a single depth
        # and the far post popped in front of an actor in the lane.
        upright(wx, wy, wood, H)
        return
    if half == "b":
        # The +axis upright, carrying the header beam, sag, and brace.
        # The frame centre sits -hs back along the axis from this
        # anchor, so the beam still spans both posts.
        cx, cy = wx - dx * hs, wy - dy * hs
        upright(wx, wy, wood2, H - (seed % 2) * s)
        _vbox(surf, cam, cx, cy, span + 9 * s, 4.5 * s, H, H + 3.5 * s,
              wood, yaw=ang)
        mza = H + 0.4 * s
        m0 = cam.project(cx - dx * hs * 0.7, cy - dy * hs * 0.7, mza)
        mm = cam.project(cx, cy, mza - 1.2 * s)
        m1 = cam.project(cx + dx * hs * 0.7, cy + dy * hs * 0.7, mza)
        pygame.draw.lines(surf, wood["dark"], False, [m0, mm, m1], 1)
        bx0 = cam.project(wx - dx * 8 * s, wy - dy * 8 * s, 2 * s)
        bx1 = cam.project(wx, wy, H * 0.75)
        pygame.draw.line(surf, wood2["side"], bx0, bx1,
                         max(2, int(2.2 * s)))
        pygame.draw.line(surf, wood["dark"], bx0, bx1, 1)
        return
    # unsplit fallback (a frame authored with an explicit half=None)
    ends = [(wx - dx * hs, wy - dy * hs, wood, H),
            (wx + dx * hs, wy + dy * hs, wood2, H - (seed % 2) * s)]
    ends.sort(key=lambda e: e[1])                 # far upright first
    for ux, uy, pal, hh in ends:
        upright(ux, uy, pal, hh)
    # the header beam spanning both uprights, overhanging each end
    _vbox(surf, cam, wx, wy, span + 9 * s, 4.5 * s, H, H + 3.5 * s,
          wood, yaw=ang)
    # its sag: a dark underline that dips mid-span (old work, holding)
    mza = H + 0.4 * s
    m0 = cam.project(wx - dx * hs * 0.7, wy - dy * hs * 0.7, mza)
    mm = cam.project(wx, wy, mza - 1.2 * s)
    m1 = cam.project(wx + dx * hs * 0.7, wy + dy * hs * 0.7, mza)
    pygame.draw.lines(surf, wood["dark"], False, [m0, mm, m1], 1)
    # a diagonal brace board on one upright
    bx0 = cam.project(wx + dx * (hs - 8 * s), wy + dy * (hs - 8 * s), 2 * s)
    bx1 = cam.project(wx + dx * hs, wy + dy * hs, H * 0.75)
    pygame.draw.line(surf, wood2["side"], bx0, bx1, max(2, int(2.2 * s)))
    pygame.draw.line(surf, wood["dark"], bx0, bx1, 1)


def _draw_ore_cart_solid(surf, cam, deco):
    """A seized ore cart -- the old workings' haul tub, shoved aside a
    cycle ago and rusted where it stopped. Designed FOR the tilt: the
    near-side wheels show under the tub (dark iron discs, standing
    vertical), rivet strap bands ride the visible faces, the lip wears a
    bright rust rim, and the whole tub sits with one end dropped (off
    its rail, never level). Mute machine evidence, per canon."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    seed = getattr(deco, "seed", 0)
    yaw = ((seed % 7) - 3) * 0.12
    c, sn = math.cos(yaw), math.sin(yaw)
    rust = {"top": (94, 72, 56), "side": (72, 55, 44), "dark": (50, 38, 31)}

    def L(lx, ly, lz):
        return cam.project(wx + lx * c - ly * sn, wy + lx * sn + ly * c, lz)
    # the near-side wheels: vertical iron discs, visible UNDER the tub
    for wxo in (-8 * s, 8 * s):
        hub = L(wxo, 8.2 * s, 3.5 * s)
        pygame.draw.circle(surf, (44, 38, 34), (int(hub[0]), int(hub[1])),
                           max(2, int(3.6 * s)))
        pygame.draw.circle(surf, (92, 82, 74), (int(hub[0]), int(hub[1])),
                           max(2, int(3.6 * s)), 1)
        pygame.draw.circle(surf, (110, 100, 90), (int(hub[0]), int(hub[1])),
                           1)
    # the axle shadow line between them
    a0, a1 = L(-9 * s, 8 * s, 2 * s), L(9 * s, 8 * s, 2 * s)
    pygame.draw.line(surf, (30, 26, 24), a0, a1, 1)
    # the tub: flared iron box, one end dropped ~2px (derailed, not level)
    drop = 2.0 * s
    zlo, zhi = 6 * s, 17 * s
    corners = [(-12 * s, -8 * s), (12 * s, -8 * s),
               (12 * s, 8 * s), (-12 * s, 8 * s)]
    lip = [(-14 * s, -9.5 * s), (14 * s, -9.5 * s),
           (14 * s, 9.5 * s), (-14 * s, 9.5 * s)]

    def ring(pts, z):
        return [L(px, py, z - (drop if px < 0 else 0)) for px, py in pts]
    base, waist, mouth = ring(corners, zlo), ring(corners, zhi - 3 * s), \
        ring(lip, zhi)
    # near face (the south side), then the two end faces, then the lip
    pygame.draw.polygon(surf, rust["dark"],
                        [base[3], base[2], waist[2], waist[3]])
    pygame.draw.polygon(surf, rust["side"],
                        [base[0], base[3], waist[3], waist[0]])
    pygame.draw.polygon(surf, rust["side"],
                        [base[2], base[1], waist[1], waist[2]])
    pygame.draw.polygon(surf, rust["dark"],
                        [waist[3], waist[2], mouth[2], mouth[3]])
    pygame.draw.polygon(surf, rust["top"], mouth)
    # the open mouth, dark, a settle of old spoil in one end
    inner = ring([(-11 * s, -7 * s), (11 * s, -7 * s),
                  (11 * s, 7 * s), (-11 * s, 7 * s)], zhi)
    pygame.draw.polygon(surf, (24, 20, 18), inner)
    sp = L(-6 * s, 0, zhi - drop)
    pygame.draw.circle(surf, (70, 60, 46), (int(sp[0]), int(sp[1])),
                       max(2, int(3 * s)))
    # rivet strap bands down the near face + the bright lip rim
    for bx in (-6 * s, 4 * s):
        b0 = L(bx, 8 * s, zlo - (drop if bx < 0 else 0))
        b1 = L(bx, 8 * s, zhi - 1 - (drop if bx < 0 else 0))
        pygame.draw.line(surf, (48, 34, 26), b0, b1, 2)
    pygame.draw.lines(surf, (114, 90, 68), True, mouth, 1)


def _draw_stalagmite_solid(surf, cam, deco):
    """A wet limestone spike rising from the cave floor -- a tapered cone (body
    of revolution), so it stands oriented in the room and occludes/depth-sorts
    instead of facing the camera. Height + girth vary by seed; a damp sheen
    catches the dark near the tip."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    seed = getattr(deco, "seed", 0)
    R = (5 + (seed % 5)) * s
    H = (18 + (seed % 16)) * s
    lean = ((seed % 7) - 3) * 0.4 * s           # a slight off-vertical lean
    pal = {"body": (96, 94, 100), "lo": (48, 48, 54), "rim": (150, 150, 160)}
    # taper base -> point; the apex section is offset by `lean` so it isn't a
    # perfectly upright cone (caves don't grow them straight).
    draw_solid(surf, cam, wx, wy,
               [(0, R, R * 0.78), (H * 0.5, R * 0.55, R * 0.46),
                (H, R * 0.12, R * 0.12)], pal)
    tip = cam.project(wx + lean, wy, H * 0.86)
    pygame.draw.circle(surf, pal["rim"], (int(tip[0]), int(tip[1])),
                       max(1, int(1.6 * s)))
    wet = cam.project(wx - R * 0.3, wy + R * 0.2, H * 0.35)
    pygame.draw.circle(surf, (118, 122, 130), (int(wet[0]), int(wet[1])),
                       max(1, int(1.2 * s)))


def _vbox(surf, cam, wx, wy, w, d, z0, z1, pal, yaw=0.0, outline=True):
    """A box from height z0 to z1 (footprint w x d), yaw-rotated about its
    centre -- used to stack a vehicle from a body + cabin + wheels."""
    hw, hd = w / 2.0, d / 2.0
    c, s = math.cos(yaw), math.sin(yaw)

    def P(sx, sy, sz):
        return cam.project(wx + sx * c - sy * s, wy + sx * s + sy * c, sz)
    fbl, fbr = P(-hw, hd, z0), P(hw, hd, z0)        # near bottom
    tbl, tbr = P(-hw, hd, z1), P(hw, hd, z1)        # near top
    bbl, bbr = P(-hw, -hd, z0), P(hw, -hd, z0)      # far bottom
    ttl, ttr = P(-hw, -hd, z1), P(hw, -hd, z1)      # far top
    pygame.draw.polygon(surf, pal["side"], [bbl, fbl, tbl, ttl])   # left
    pygame.draw.polygon(surf, pal["side"], [bbr, fbr, tbr, ttr])   # right
    pygame.draw.polygon(surf, pal["dark"], [fbl, fbr, tbr, tbl])   # near face
    pygame.draw.polygon(surf, pal["top"], [tbl, tbr, ttr, ttl])    # top
    if outline:
        pygame.draw.polygon(surf, _shade(pal["top"], 0.55),
                            [tbl, tbr, ttr, ttl], 1)


def _vehicle_shadow(surf, cam, wx, wy, bl, bw):
    shw = max(4, int(bl * 0.5 * cam.scale * 1.05))
    shh = max(2, int(bw * 0.5 * cam.ground_squash() * cam.scale * 1.05))
    bx, by = cam.project(wx, wy, 0)
    sh = pygame.Surface((shw * 2 + 4, shh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 105), (2, 2, shw * 2, shh * 2))
    surf.blit(sh, (bx - shw - 2, by - shh - 2))


def _vframe(cam, wx, wy, yaw):
    """A local->screen projector for a vehicle: local (lx along length, ly across
    width, lz height) rotated by yaw about the placement and projected."""
    c, s = math.cos(yaw), math.sin(yaw)

    def P(lx, ly, lz):
        return cam.project(wx + lx * c - ly * s, wy + lx * s + ly * c, lz)
    return P


def _qp(surf, P, locs, col, w=0):
    pygame.draw.polygon(surf, col,
                        [(int(x), int(y)) for x, y in (P(*p) for p in locs)], w)


def _lp(surf, P, a, b, col, w=1):
    pa, pb = P(*a), P(*b)
    pygame.draw.line(surf, col, (int(pa[0]), int(pa[1])),
                     (int(pb[0]), int(pb[1])), w)


def _round_wheel(surf, P, lx, ly, r):
    """A tyre as a real disc standing in the length/height plane at local
    (lx, ly): a 12-gon black tyre + a metal hubcap, projected through the
    camera so it reads as a round wheel at the oblique angle."""
    n = 12
    pts = [P(lx + math.cos(math.tau * i / n) * r, ly,
             r + math.sin(math.tau * i / n) * r) for i in range(n)]
    pts = [(int(x), int(y)) for x, y in pts]
    pygame.draw.polygon(surf, (20, 20, 22), pts)        # tyre
    pygame.draw.polygon(surf, (46, 46, 50), pts, 1)
    h = P(lx, ly, r)
    hr = max(2, int(r * 0.46))
    pygame.draw.circle(surf, (120, 122, 128), (int(h[0]), int(h[1])), hr)
    pygame.draw.circle(surf, (64, 66, 72), (int(h[0]), int(h[1])), hr, 1)
    pygame.draw.circle(surf, (170, 172, 178), (int(h[0]), int(h[1])), max(1, hr // 2))


def _draw_car_solid(surf, cam, deco):
    """A 1994 sedan as a real volume: a low body on four round wheels, a glassed
    cabin set back on top (side + windshield + rear glass with a B-pillar), a
    chrome grille + bumpers, headlights at the nose and red tail-lamps, a door
    seam + handle + side trim. Faded dead-paint palette."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    yaw = float(deco.kwargs.get("yaw", 0.0))
    P = _vframe(cam, wx, wy, yaw)
    L, W = 52 * s, 26 * s
    hL, hW = L / 2, W / 2
    z0, z1 = 5 * s, 14 * s                        # body band
    cz1 = z1 + 11 * s                             # cabin top
    cf, cb = 9 * s, -17 * s                       # cabin front / back (local x)
    chW = W * 0.84 / 2
    r, wbx = 6 * s, hL * 0.60                      # wheel radius + wheelbase
    body = {"top": (112, 126, 142), "side": (78, 92, 110), "dark": (46, 56, 70)}
    cab = {"top": (70, 84, 102), "side": (50, 62, 78), "dark": (28, 36, 48)}
    glass, glass_hi, chrome = (46, 60, 64), (98, 118, 124), (172, 176, 184)
    _vehicle_shadow(surf, cam, wx, wy, L, W)
    _round_wheel(surf, P, wbx, -hW, r)            # far wheels (behind body)
    _round_wheel(surf, P, -wbx, -hW, r)
    _vbox(surf, cam, wx, wy, L, W, z0, z1, body, yaw=yaw)
    ccx = (cf + cb) / 2
    _vbox(surf, cam, wx + ccx * math.cos(yaw), wy + ccx * math.sin(yaw),
          cf - cb, W * 0.84, z1, cz1, cab, yaw=yaw)
    ny = hW + 0.2                                  # near side plane
    # cabin glass: near-side band (with B-pillar + top highlight), windshield, rear
    _qp(surf, P, [(cb + 2, chW + 0.2, z1 + 1.5), (cf - 2, chW + 0.2, z1 + 1.5),
                  (cf - 2, chW + 0.2, cz1 - 1.5), (cb + 2, chW + 0.2, cz1 - 1.5)], glass)
    _lp(surf, P, (ccx, chW + 0.3, z1 + 1.5), (ccx, chW + 0.3, cz1 - 1.5), cab["dark"], 1)
    _lp(surf, P, (cb + 2, chW + 0.3, cz1 - 1.6), (cf - 2, chW + 0.3, cz1 - 1.6), glass_hi, 1)
    _qp(surf, P, [(cf, -chW, z1 + 1.5), (cf, chW, z1 + 1.5),
                  (cf, chW, cz1 - 1.5), (cf, -chW, cz1 - 1.5)], glass)
    _qp(surf, P, [(cb, -chW, z1 + 1.5), (cb, chW, z1 + 1.5),
                  (cb, chW, cz1 - 1.5), (cb, -chW, cz1 - 1.5)], glass)
    # near-side door seam + handle + chrome trim
    _lp(surf, P, (-2 * s, ny, z0 + 1), (-2 * s, ny, z1), _shade(body["dark"], 0.8), 1)
    _lp(surf, P, (-7 * s, ny, z1 - 3 * s), (-12 * s, ny, z1 - 3 * s), chrome, 1)
    _lp(surf, P, (-hL + 3, ny, z0 + 4 * s), (hL - 3, ny, z0 + 4 * s),
        _shade(body["side"], 1.3), 1)
    # bumpers (front bright, rear dim) + front grille bars
    _qp(surf, P, [(hL, -hW, z0), (hL, hW, z0), (hL, hW, z0 + 3 * s), (hL, -hW, z0 + 3 * s)], chrome)
    _qp(surf, P, [(-hL, -hW, z0), (-hL, hW, z0), (-hL, hW, z0 + 3 * s), (-hL, -hW, z0 + 3 * s)],
        _shade(chrome, 0.65))
    for ey in (-6 * s, -2 * s, 2 * s, 6 * s):
        _lp(surf, P, (hL, ey, z0 + 4 * s), (hL, ey, z1 - 2 * s), _shade(body["dark"], 0.7), 1)
    # head / tail lamps
    for ey in (-hW * 0.62, hW * 0.62):
        hp = P(hL, ey, z1 - 3 * s)
        pygame.draw.circle(surf, (230, 224, 188), (int(hp[0]), int(hp[1])), max(2, int(2.2 * s)))
        tp = P(-hL, ey, z1 - 3 * s)
        pygame.draw.circle(surf, (178, 42, 38), (int(tp[0]), int(tp[1])), max(2, int(2 * s)))
    _round_wheel(surf, P, wbx, hW, r)             # near wheels (exposed)
    _round_wheel(surf, P, -wbx, hW, r)
    _lp(surf, P, (-hL + 3, -hW + 2, z1), (hL - 3, -hW + 2, z1), _shade(body["top"], 1.15), 1)


def _draw_pickup_truck_solid(surf, cam, deco):
    """A pickup as a real volume: a cab at the front (glassed), an OPEN bed
    behind (recessed dark floor, side rails, a tailgate), four round wheels, a
    grille + bumper + lamps at the nose. Faded farm-green paint."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    yaw = float(deco.kwargs.get("yaw", 0.0))
    P = _vframe(cam, wx, wy, yaw)
    L, W = 56 * s, 27 * s
    hL, hW = L / 2, W / 2
    z0, z1 = 5 * s, 13 * s
    cf, cb = hL, 7 * s                             # cab spans nose -> x=7
    cz1 = z1 + 13 * s
    cW = W * 0.92
    chW = cW / 2
    r, wbx = 7 * s, hL * 0.62
    body = {"top": (92, 100, 82), "side": (64, 72, 56), "dark": (40, 46, 34)}
    cab = {"top": (74, 82, 66), "side": (52, 60, 46), "dark": (30, 36, 26)}
    glass, glass_hi, chrome = (46, 58, 60), (96, 114, 118), (166, 170, 176)
    _vehicle_shadow(surf, cam, wx, wy, L, W)
    _round_wheel(surf, P, wbx, -hW, r)
    _round_wheel(surf, P, -wbx, -hW, r)
    _vbox(surf, cam, wx, wy, L, W, z0, z1, body, yaw=yaw)
    ccx = (cf + cb) / 2
    _vbox(surf, cam, wx + ccx * math.cos(yaw), wy + ccx * math.sin(yaw),
          cf - cb, cW, z1, cz1, cab, yaw=yaw)
    # OPEN bed behind the cab: recessed dark floor + side rails + tailgate
    bf, bb = cb - 1 * s, -hL + 1
    railz = z1 + 5 * s
    _qp(surf, P, [(bb, -hW + 1, z1), (bf, -hW + 1, z1),
                  (bf, hW - 1, z1), (bb, hW - 1, z1)], (28, 30, 24))     # bed floor
    for ly in (-hW, hW):                                                 # side rails
        _qp(surf, P, [(bb, ly, z1), (bf, ly, z1), (bf, ly, railz), (bb, ly, railz)],
            body["side"] if ly > 0 else _shade(body["side"], 0.8))
    _qp(surf, P, [(bb, -hW, z1), (bb, hW, z1), (bb, hW, railz), (bb, -hW, railz)],
        body["dark"])                                                    # tailgate
    _lp(surf, P, (bb, hW + 0.2, railz), (bf, hW + 0.2, railz), _shade(body["top"], 1.1), 1)
    # cab glass: near side + windshield
    ny = hW + 0.2
    _qp(surf, P, [(cb + 2, chW + 0.2, z1 + 2), (cf - 3, chW + 0.2, z1 + 2),
                  (cf - 3, chW + 0.2, cz1 - 2), (cb + 2, chW + 0.2, cz1 - 2)], glass)
    _lp(surf, P, (cb + 2, chW + 0.3, cz1 - 2), (cf - 3, chW + 0.3, cz1 - 2), glass_hi, 1)
    _qp(surf, P, [(cf, -chW, z1 + 2), (cf, chW, z1 + 2),
                  (cf, chW, cz1 - 2), (cf, -chW, cz1 - 2)], glass)
    # door seam + trim on the cab near side
    _lp(surf, P, (cb + 3 * s, ny, z0 + 1), (cb + 3 * s, ny, z1), _shade(cab["dark"], 0.8), 1)
    _lp(surf, P, (cb + 1, ny, z0 + 4 * s), (hL - 3, ny, z0 + 4 * s), _shade(body["side"], 1.3), 1)
    # nose: bumper, grille, lamps
    _qp(surf, P, [(hL, -hW, z0), (hL, hW, z0), (hL, hW, z0 + 4 * s), (hL, -hW, z0 + 4 * s)], chrome)
    for ey in (-7 * s, -2.5 * s, 2.5 * s, 7 * s):
        _lp(surf, P, (hL, ey, z0 + 5 * s), (hL, ey, z1 - 1 * s), _shade(body["dark"], 0.7), 1)
    for ey in (-hW * 0.6, hW * 0.6):
        hp = P(hL, ey, z1 - 2 * s)
        pygame.draw.circle(surf, (230, 224, 188), (int(hp[0]), int(hp[1])), max(2, int(2.4 * s)))
        tp = P(-hL, ey, railz - 2 * s)
        pygame.draw.circle(surf, (178, 42, 38), (int(tp[0]), int(tp[1])), max(2, int(2 * s)))
    _round_wheel(surf, P, wbx, hW, r)
    _round_wheel(surf, P, -wbx, hW, r)


# ---- The dead lots: abandoned rusted cars (2026-07) ----------------------
# Everyone DROVE into Brimley (northern Minnesota: the newcomers came on
# their own wheels and the locals all drive), and nothing with an engine
# leaves -- so the cars pool where their drivers finally stopped: ragged
# ranks by the barn, a give-up line on the fold-road shoulder, noses
# swallowed in the corn. Four body styles, all long dead. Seeded per
# instance: faded period paint, rust eating up from the rockers, weeds
# at the tyres, one blown corner, glass grimy or gone. Pair placements
# with solid invisible 'X' tiles (the lodge-yard truck convention).

_RUST_BASES = [
    (128, 62, 52),    # dusty red
    (86, 104, 122),   # faded blue
    (150, 142, 118),  # dirty cream
    (98, 84, 60),     # dun brown
    (92, 102, 74),    # olive
    (146, 118, 62),   # mustard
]


# Plate colors across the 1994 states the newcomers drove from: white,
# gold, pale blue, sun-cooked tan. Variety IS the story (they came from
# everywhere); no lettering at this scale, just a registration smudge.
_PLATE_COLS = [
    (204, 200, 188),
    (196, 186, 122),
    (172, 184, 198),
    (188, 168, 148),
]


def _rust_pal(rng):
    base = _RUST_BASES[rng.randrange(len(_RUST_BASES))]
    fade = rng.uniform(0.72, 0.98)
    return {
        "top":  tuple(min(255, int(c * 1.10 * fade)) for c in base),
        "side": tuple(int(c * 0.76 * fade) for c in base),
        "dark": tuple(int(c * 0.42 * fade) for c in base),
    }


def _flat_wheel(surf, P, lx, ly, r):
    """A blown tyre: the same standing disc, sagged to a low oval settled
    into the dirt."""
    n = 12
    pts = [P(lx + math.cos(math.tau * i / n) * r * 1.12, ly,
             r * 0.58 + math.sin(math.tau * i / n) * r * 0.58)
           for i in range(n)]
    pts = [(int(x), int(y)) for x, y in pts]
    pygame.draw.polygon(surf, (20, 20, 22), pts)
    pygame.draw.polygon(surf, (46, 46, 50), pts, 1)
    h = P(lx, ly, r * 0.58)
    pygame.draw.circle(surf, (96, 92, 86), (int(h[0]), int(h[1])),
                       max(1, int(r * 0.4)))


def _rust_dress(surf, P, rng, hL, ny, z0, z1, n):
    """Rust eating the NEAR flank: a rotted rocker streak at the sill,
    blotches climbing from it."""
    _lp(surf, P, (-hL + 2, ny, z0 + 1), (hL - 2, ny, z0 + 1), (84, 46, 26), 2)
    for _ in range(n):
        lx = rng.uniform(-hL + 3, hL - 3)
        lz = z0 + abs(rng.gauss(0.0, (z1 - z0) * 0.4))
        p = P(lx, ny, min(z1 - 0.5, lz))
        pygame.draw.circle(
            surf, (118, 60, 32) if rng.random() < 0.6 else (78, 40, 22),
            (int(p[0]), int(p[1])), rng.randint(1, 3))


def _weed_dress(surf, P, rng, hL, hWs, n):
    """Weeds grown up along the near flank (`hWs` is the SIGNED near-side
    y); nothing has moved in months."""
    sgn = 1.0 if hWs >= 0 else -1.0
    for _ in range(n):
        base = P(rng.uniform(-hL, hL), hWs + rng.uniform(1, 4) * sgn, 0)
        g = 58 + rng.randint(0, 42)
        pygame.draw.line(surf, (44, g, 44), (int(base[0]), int(base[1])),
                         (int(base[0]) - rng.randint(0, 2),
                          int(base[1]) - rng.randint(4, 9)), 1)


def _rust_car_solid(surf, cam, deco, L, W, cf, cb, cab_up, wagon=False,
                    van=False):
    """Shared dead-car engine: a low body band + glassed cabin set on top
    (or one tall slab box for the van), four wheels with one blown
    corner, dead-steel bumpers, dead lamps, seeded paint/rust/weeds.
    `cf`/`cb` are the cabin front/back in local x; `cab_up` its rise
    above the body band. kwargs: `yaw` (radians) spins the hull."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    yaw = float(deco.kwargs.get("yaw", 0.0))
    rng = random.Random(deco.seed)
    P = _vframe(cam, wx, wy, yaw)
    L, W = L * s, W * s
    hL, hW = L / 2, W / 2
    sink = rng.uniform(0.5, 1.5) * s              # settled into the dirt
    z0 = 4 * s - sink
    z1 = z0 + (17 * s if van else 9 * s)
    cz1 = z1 + cab_up * s
    cf, cb = cf * s, cb * s
    chW = hW * (0.98 if van else 0.84)
    r, wbx = 6 * s, hL * 0.60
    # Which local side faces the camera flips with yaw: resolve the NEAR
    # side sign from the projection so wheels/glass/rust always dress
    # the flank the player actually sees.
    ns = 1.0 if P(0, hW, 0)[1] >= P(0, -hW, 0)[1] else -1.0
    ny = (hW + 0.2) * ns
    cny = (chW + 0.2) * ns
    body = _rust_pal(rng)
    cab = {"top": _shade(body["top"], 0.9),
           "side": _shade(body["side"], 0.72),
           "dark": _shade(body["dark"], 0.72)}
    flat_i = rng.randrange(4)                     # which corner is blown
    glass_gone = rng.random() < 0.45
    glass = (16, 17, 19) if glass_gone else (52, 60, 58)
    steel = (108, 104, 96)
    _vehicle_shadow(surf, cam, wx, wy, L, W)
    for i, lx in enumerate((wbx, -wbx)):          # far wheels
        (_flat_wheel if 2 + i == flat_i else _round_wheel)(
            surf, P, lx, -hW * ns, r)
    _vbox(surf, cam, wx, wy, L, W, z0, z1, body, yaw=yaw)
    if van:
        # the tall box IS the cabin: a high windshield on the nose, a
        # small near-side cab window, sliding-door + rear-door seams
        _qp(surf, P, [(hL - 0.5, -chW * 0.8, z1 - 9 * s),
                      (hL - 0.5, chW * 0.8, z1 - 9 * s),
                      (hL - 0.5, chW * 0.8, z1 - 2 * s),
                      (hL - 0.5, -chW * 0.8, z1 - 2 * s)], glass)
        _qp(surf, P, [(hL - 4 * s, ny, z1 - 9 * s),
                      (hL - 13 * s, ny, z1 - 9 * s),
                      (hL - 13 * s, ny, z1 - 3 * s),
                      (hL - 4 * s, ny, z1 - 3 * s)], glass)
        _lp(surf, P, (2 * s, ny, z0 + 1), (2 * s, ny, z1 - 1),
            _shade(body["dark"], 0.8), 1)
        _lp(surf, P, (-15 * s, ny, z0 + 1), (-15 * s, ny, z1 - 1),
            _shade(body["dark"], 0.8), 1)
        # rear barn doors: a centre seam + hinges on the tail face, and a
        # roof edge line so the slab reads as a closed van from behind
        _lp(surf, P, (-hL - 0.2, 0, z0 + 2), (-hL - 0.2, 0, z1 - 2 * s),
            _shade(body["dark"], 0.7), 1)
        _lp(surf, P, (-hL - 0.2, -chW * 0.5, z1 - 6 * s),
            (-hL - 0.2, -chW * 0.32, z1 - 6 * s), _shade(body["dark"], 0.7), 1)
        _lp(surf, P, (-hL, -chW, z1), (-hL, chW, z1),
            _shade(body["top"], 1.3), 1)
        _lp(surf, P, (-hL + 1, chW * ns, z1), (hL - 1, chW * ns, z1),
            _shade(body["top"], 1.3), 1)
    else:
        ccx = (cf + cb) / 2
        _vbox(surf, cam, wx + ccx * math.cos(yaw), wy + ccx * math.sin(yaw),
              cf - cb, chW * 2, z1, cz1, cab, yaw=yaw)
        # near-side glass band + windshield + rear glass. PILLARS split
        # the band into real windows -- without them the long dark band
        # reads as an OPEN BED (the wagon failed the mistaken-identity
        # test as a trailer).
        _qp(surf, P, [(cb + 2, cny, z1 + 1.5), (cf - 2, cny, z1 + 1.5),
                      (cf - 2, cny, cz1 - 1.5), (cb + 2, cny, cz1 - 1.5)],
            glass)
        n_pil = 2 if wagon else 1
        for k in range(1, n_pil + 1):
            px = cb + (cf - cb) * k / (n_pil + 1)
            _lp(surf, P, (px, cny, z1 + 1), (px, cny, cz1 - 1),
                cab["side"], 2)
        if not glass_gone:
            _lp(surf, P, (cb + 2, cny, cz1 - 1.6),
                (cf - 2, cny, cz1 - 1.6), (86, 102, 100), 1)
        _qp(surf, P, [(cf, -chW, z1 + 1.5), (cf, chW, z1 + 1.5),
                      (cf, chW, cz1 - 1.5), (cf, -chW, cz1 - 1.5)], glass)
        _qp(surf, P, [(cb, -chW, z1 + 1.5), (cb, chW, z1 + 1.5),
                      (cb, chW, cz1 - 1.5), (cb, -chW, cz1 - 1.5)], glass)
        # roof edge highlight so the lid reads CLOSED at the low pitch
        _lp(surf, P, (cb + 1, chW * ns, cz1), (cf - 1, chW * ns, cz1),
            _shade(cab["top"], 1.35), 1)
        if wagon:
            # roof-rack rails the length of the long wagon roof
            for ly in (-chW * 0.55, chW * 0.55):
                _lp(surf, P, (cb + 2, ly, cz1 + 1), (cf - 2, ly, cz1 + 1),
                    _shade(cab["top"], 1.25), 1)
            if deco.kwargs.get("luggage"):
                # suitcases still strapped to the rack: whatever they
                # came for mattered more than unpacking ever did again
                for (lx0, lx1, hh, colc) in (
                        (-20 * s, -8 * s, 4.5 * s, (88, 62, 42)),
                        (-6 * s, 6 * s, 3.6 * s, (118, 104, 78))):
                    lcx = (lx0 + lx1) / 2
                    _vbox(surf, cam, wx + lcx * math.cos(yaw),
                          wy + lcx * math.sin(yaw), lx1 - lx0, chW * 1.1,
                          cz1 + 1, cz1 + 1 + hh,
                          {"top": _shade(colc, 1.15), "side": colc,
                           "dark": _shade(colc, 0.6)}, yaw=yaw)
                    _lp(surf, P, (lcx, -chW * 0.6, cz1 + 1.5 + hh),
                        (lcx, chW * 0.6, cz1 + 1.5 + hh), (40, 34, 30), 1)
        _lp(surf, P, ((cb + cf) / 2, ny, z0 + 1), ((cb + cf) / 2, ny, z1),
            _shade(body["dark"], 0.8), 1)          # door seam
    # bumpers dulled to dead steel; the rear one sometimes hangs
    _qp(surf, P, [(hL, -hW, z0), (hL, hW, z0), (hL, hW, z0 + 2.5 * s),
                  (hL, -hW, z0 + 2.5 * s)], steel)
    if rng.random() < 0.5:
        _lp(surf, P, (-hL, hW * ns, z0 + 2 * s),
            (-hL + 3 * s, (hW + 2 * s) * ns, 0), _shade(steel, 0.8), 2)
    else:
        _qp(surf, P, [(-hL, -hW, z0), (-hL, hW, z0), (-hL, hW, z0 + 2.5 * s),
                      (-hL, -hW, z0 + 2.5 * s)], _shade(steel, 0.7))
    # lamps long dead: dim sockets, one sometimes smashed dark
    for k, ey in enumerate((-hW * 0.62, hW * 0.62)):
        hp = P(hL, ey, z1 - 2.5 * s)
        col = (30, 30, 32) if (glass_gone and k == 0) else (150, 142, 108)
        pygame.draw.circle(surf, col, (int(hp[0]), int(hp[1])),
                           max(1, int(2 * s)))
        tp = P(-hL, ey, z1 - 2.5 * s)
        pygame.draw.circle(surf, (96, 30, 26), (int(tp[0]), int(tp[1])),
                           max(1, int(1.8 * s)))
    # license plates, seeded from a spread of state colors: the
    # newcomers drove in from EVERYWHERE, and the lots say so. Tail
    # plate always; nose plate on the two-plate states.
    plate = _PLATE_COLS[rng.randrange(len(_PLATE_COLS))]
    pw, pz = 3.4 * s, z0 + 1.5 * s
    _qp(surf, P, [(-hL - 0.3, -pw, pz), (-hL - 0.3, pw, pz),
                  (-hL - 0.3, pw, pz + 2.6 * s),
                  (-hL - 0.3, -pw, pz + 2.6 * s)], plate)
    _lp(surf, P, (-hL - 0.3, -pw * 0.7, pz + 1.3 * s),
        (-hL - 0.3, pw * 0.7, pz + 1.3 * s), (60, 62, 70), 1)
    if rng.random() < 0.6:
        _qp(surf, P, [(hL + 0.3, -pw, pz), (hL + 0.3, pw, pz),
                      (hL + 0.3, pw, pz + 2.6 * s),
                      (hL + 0.3, -pw, pz + 2.6 * s)], plate)
    _rust_dress(surf, P, rng, hL, ny, z0, z1, 12 if van else 10)
    for i, lx in enumerate((wbx, -wbx)):          # near wheels
        (_flat_wheel if i == flat_i else _round_wheel)(
            surf, P, lx, hW * ns, r)
    _weed_dress(surf, P, rng, hL, hW * ns, 8)


def _draw_rust_sedan_solid(surf, cam, deco):
    """A dead 80s sedan: mid-set cabin on a low body, rust and weeds."""
    _rust_car_solid(surf, cam, deco, 52, 26, 9, -17, 8)


def _draw_rust_wagon_solid(surf, cam, deco):
    """A dead station wagon: the roof runs long to the tail, rack rails
    still on it."""
    _rust_car_solid(surf, cam, deco, 56, 26, 10, -25, 8, wagon=True)


def _draw_rust_coupe_solid(surf, cam, deco):
    """A dead two-door coupe: a short greenhouse set back on a low body."""
    _rust_car_solid(surf, cam, deco, 46, 24, 3, -15, 7)


def _draw_rust_van_solid(surf, cam, deco):
    """A dead panel van: one tall slab-sided box, high windshield, a
    sliding-door seam on the near flank."""
    _rust_car_solid(surf, cam, deco, 54, 28, 0, 0, 0, van=True)


def _draw_waterfall_solid(surf, cam, deco):
    """A spring gushing from a HOLE in the cave cliff and falling into the river
    -- the visible mouth of the artery (NARRATIVE §2). A dark source recess
    gouged in the rock at the top, then a sheet of water sheeting down into the
    channel, foam churning where it strikes. Drawn each frame (animated; streaks
    scroll DOWN), depth-sorted against the wall. `ang` (radians) yaws the sheet
    onto its wall; default faces +y (toward a south-standing camera)."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    ang = float(deco.kwargs.get("ang", 0.0))
    ca, sn = math.cos(ang), math.sin(ang)
    H = 24 * s
    # `w` is the sheet width in WORLD px (defaults to ~one tile); a 3-wide fall
    # passes w ~= 90 so a single object covers the whole river mouth.
    halfw = float(deco.kwargs.get("w", 18)) * 0.5 * s
    t = deco.t

    def P(across, z):                       # across the sheet width, height z
        return cam.project(wx + across * ca, wy + across * sn, z)
    # the source HOLE: a dark recess in the cliff the water gushes from, set just
    # above the falling sheet with a lit rock rim so it reads as a mouth in rock
    hole = [P(-halfw * 1.02, H - 2 * s), P(halfw * 1.02, H - 2 * s),
            P(halfw * 0.82, H + 12 * s), P(-halfw * 0.82, H + 12 * s)]
    pygame.draw.polygon(surf, (5, 9, 9), hole)
    pygame.draw.polygon(surf, (44, 58, 54), hole, 1)
    # the wet dark rock the sheet sheets over
    pygame.draw.polygon(surf, (20, 30, 30),
                        [P(-halfw, 0), P(halfw, 0), P(halfw, H), P(-halfw, H)])
    # falling streaks: dashed vertical runs that scroll downward over time. Same
    # murky teal-green as the river (`~`), foam a paler version of it.
    cols = [(70, 104, 96), (50, 80, 74), (96, 124, 114)]
    n = max(6, int(halfw / 3))
    for i in range(n):
        across = -halfw + (i + 0.5) * (2 * halfw / n)
        col = cols[i % 3]
        off = (t * 42 * s + i * 7) % (8 * s + 0.01)
        z = H - off
        while z > 0:
            pygame.draw.line(surf, col, P(across, z),
                             P(across, max(0, z - 4 * s)), 1)
            z -= 8 * s
    pygame.draw.line(surf, (124, 150, 138), P(-halfw, H), P(halfw, H), 2)  # crest
    # foam pool + spray where it strikes the river
    fb = cam.project(wx, wy, 0)
    fw = max(3, int(halfw * cam.scale * 1.15))
    fh = max(2, int(halfw * 0.4 * cam.ground_squash() * cam.scale))
    foam = pygame.Surface((fw * 2 + 4, fh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(foam, (90, 120, 110, 150), (2, 2, fw * 2, fh * 2))
    pygame.draw.ellipse(foam, (140, 168, 154, 175),
                        (fw - fw // 2 + 2, fh - fh // 2 + 2, fw, fh))
    surf.blit(foam, (int(fb[0]) - fw - 2, int(fb[1]) - fh - 2))
    for i in range(6):
        fa = t * 3.0 + i * 1.1
        p = P(math.cos(fa) * halfw * 0.8, abs(math.sin(fa)) * 4 * s)
        pygame.draw.circle(surf, (150, 176, 162), (int(p[0]), int(p[1])), 1)


def _draw_doorframe_solid(surf, cam, deco):
    """THE THRESHOLD (NARRATIVE §2): a plain, blank, unmarked frame -- 'about the
    size of a car stood on its nose' -- standing DEAD STRAIGHT on the impossible
    apron. 'Too slight to hold itself upright, yet it stands.' It is ONLY a
    frame: nothing fills the opening, you see the cave straight through it (walk
    through and you stand in the same room; that walk-through is the seal). Two
    slight jambs + a lintel, pale bone-stone, unnaturally precise against the
    leaning cave around it -- geometry serving the door."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    Wf, Hf, t, Df = 30 * s, 54 * s, 5 * s, 6 * s
    half = Wf / 2
    pal = {"top": (158, 156, 164), "side": (110, 108, 116), "dark": (74, 72, 80)}
    # cold ground-contact shadow so it seats on the apron
    bx, by = cam.project(wx, wy, 0)
    shw = max(4, int(half * cam.scale * 1.1))
    shh = max(2, int(Df * cam.ground_squash() * cam.scale))
    shsurf = pygame.Surface((shw * 2 + 4, shh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(shsurf, (0, 0, 0, 90), (2, 2, shw * 2, shh * 2))
    surf.blit(shsurf, (bx - shw - 2, by - shh - 2))
    # jambs + lintel as slight upright boxes, dead straight (no lean). The
    # opening is left EMPTY -- whatever the camera already drew behind it (the
    # cave, the far wall) shows through.
    _vbox(surf, cam, wx - half + t / 2, wy, t, Df, 0, Hf, pal)
    _vbox(surf, cam, wx + half - t / 2, wy, t, Df, 0, Hf, pal)
    _vbox(surf, cam, wx, wy, Wf, Df, Hf - t, Hf, pal)
    # a thin pale rule down each inner edge -- precise, machined
    for ex in (-half + t, half - t):
        a = cam.project(wx + ex, wy, t)
        b = cam.project(wx + ex, wy, Hf - t)
        pygame.draw.line(surf, pal["top"], a, b, 1)


def _draw_shaft_ladder_solid(surf, cam, deco):
    """The way UP from the shaft floor: a single thick ROPE hanging from a hatch
    in the rock ceiling down to the landing. The dark shaft + a framed hatch sit
    high overhead; the rope sways slightly on its slack, knotted at intervals for
    climbing, frayed where it coils on the floor. (The flat pitch-0 view uses the 2D sprite.)"""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    H = 82 * s
    lean = -3.0 * s         # the top leans back (north) into the rock

    def at(f):              # a point on the rope at height fraction f
        wav = math.sin(f * 7.0 + 0.5) * 2.4 * s            # the rope's slack sway
        return cam.project(wx + wav, wy + lean * f, f * H)

    # contact shadow so the foot seats on the floor
    bx, by = cam.project(wx, wy, 0)
    shw = max(3, int(5 * s * cam.scale))
    shh = max(2, int(3 * s * cam.ground_squash() * cam.scale))
    sh = pygame.Surface((shw * 2 + 4, shh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 90), (2, 2, shw * 2, shh * 2))
    surf.blit(sh, (int(bx) - shw - 2, int(by) - shh - 2))
    # the dark shaft + timber hatch frame high overhead
    fr = 12 * s
    fy = wy + lean
    frame = [cam.project(wx - fr, fy - fr, H), cam.project(wx + fr, fy - fr, H),
             cam.project(wx + fr, fy + fr, H), cam.project(wx - fr, fy + fr, H)]
    pygame.draw.polygon(surf, (6, 6, 8), frame)                 # black shaft going up
    pygame.draw.polygon(surf, (88, 62, 36), frame, max(2, int(2 * s)))   # hatch frame
    # the rope itself: thick, with a dark edge, a lit strand, twist texture
    pts = [at(i / 18.0) for i in range(19)]
    pygame.draw.lines(surf, (92, 72, 44), False, pts, max(3, int(4 * s)))    # body/edge
    pygame.draw.lines(surf, (146, 124, 84), False, pts, max(2, int(3 * s)))  # mid
    pygame.draw.lines(surf, (184, 162, 114), False, pts, 1)                  # lit strand
    for i in range(2, 18, 2):                                   # twisted-strand ticks
        p = at(i / 18.0)
        pygame.draw.line(surf, (96, 76, 48),
                         (int(p[0]) - 2, int(p[1]) - 1), (int(p[0]) + 2, int(p[1]) + 1), 1)
    for f in (0.34, 0.66):                                      # climbing knots (bulges)
        kp = at(f)
        pygame.draw.circle(surf, (120, 98, 60), (int(kp[0]), int(kp[1])), max(2, int(3 * s)))
        pygame.draw.circle(surf, (176, 154, 108),
                           (int(kp[0]) - 1, int(kp[1]) - 1), max(1, int(1.4 * s)))
    foot = at(0.0)                                              # frayed coil on the floor
    pygame.draw.ellipse(surf, (120, 98, 60),
                        (int(foot[0]) - int(6 * s), int(foot[1]) - int(2 * s),
                         int(12 * s), int(5 * s)), max(1, int(2 * s)))


def _draw_staircase_solid(surf, cam, deco):
    """A wooden flight of stairs climbing AWAY from the camera (north) up to a
    loft. Built as a stack of tread boxes: each successive step sits further
    north and rises higher, so the near risers occlude the ones behind and the
    tops read as treads. The top step climbs well past wall height (26), so it
    reads as going up to a second floor. `yaw` rotates the whole flight (default
    ascends north). (The flat pitch-0 view uses the 2D sprite.)"""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    steps = 6
    W = 30 * s                     # tread width
    total_d = 44 * s               # depth the whole flight covers
    step_d = total_d / steps
    rise = 9 * s                   # height gained per step
    pal = {"top": (110, 80, 50), "side": (80, 56, 34), "dark": (56, 39, 24)}
    yaw = getattr(deco, "yaw", 0.0) or 0.0
    c, sn = math.cos(yaw), math.sin(yaw)
    # contact shadow under the whole footprint
    bx, by = cam.project(wx, wy, 0)
    shw = max(4, int(W * 0.5 * cam.scale * 1.1))
    shh = max(3, int(total_d * 0.5 * cam.ground_squash() * cam.scale * 1.1))
    sh = pygame.Surface((shw * 2 + 4, shh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 95), (2, 2, shw * 2, shh * 2))
    surf.blit(sh, (int(bx) - shw - 2, int(by) - shh - 2))
    # far (top) step first so the near risers paint over the ones behind
    for i in range(steps - 1, -1, -1):
        # local depth centre: near step (i=0) at +total_d/2, far (top) at -total_d/2
        ly = total_d / 2 - (i + 0.5) * step_d
        cx = wx + (-ly) * sn        # yaw the depth axis into world x
        cy = wy + ly * c
        _vbox(surf, cam, cx, cy, W, step_d, 0, (i + 1) * rise, pal, yaw=yaw)
    # a dark loft mouth above the top step -- the way up reads as an opening
    ty = total_d / 2 - steps * step_d
    mx = wx + (-ty) * sn
    my = wy + ty * c
    top_z = steps * rise
    mw = W * 0.42
    mouth = [cam.project(mx - mw, my, top_z), cam.project(mx + mw, my, top_z),
             cam.project(mx + mw, my, top_z + 12 * s),
             cam.project(mx - mw, my, top_z + 12 * s)]
    pygame.draw.polygon(surf, (10, 8, 12), mouth)


def _draw_kitchen_wall_solid(surf, cam, deco):
    """THE KITCHEN WALL (interiors pilot, TODO #24): the lodge's cooking
    run composed as ONE object against a west wall. Cookstove on legs
    with its pipe climbing past the eave, a counter run north of it with
    the pot shelf over, three hung pots, the house ham on the shelf's
    end hook, a wood crate under the counter lip. Provenance: Sable
    keeps a working kitchen for a full house that no longer comes.
    Anchor = the stove's floor point; the run extends NORTH (-y); the
    wall is WEST (-x)."""
    wx, wy = deco.x, deco.y
    iron = {"top": (56, 56, 62), "side": (40, 40, 46), "dark": (24, 24, 28)}
    iron_d = {"top": (44, 44, 50), "side": (30, 30, 36), "dark": (18, 18, 22)}
    wood = {"top": (104, 80, 50), "side": (78, 58, 38), "dark": (48, 34, 22)}
    wood_d = {"top": (86, 66, 42), "side": (62, 46, 30), "dark": (40, 28, 18)}
    T = 32
    rng = random.Random(int(wx * 7 + wy * 13) & 0xffff)

    # World-space helpers: everything on a surface is projected geometry
    # (a plate is a circle in the WORLD's plane, foreshortened by the
    # camera), never a screen-aligned mark -- error class 7.
    def _ell(cx, cy, z, rx_, ry_, col, width=0):
        pts = [cam.project(cx + rx_ * math.cos(a), cy + ry_ * math.sin(a), z)
               for a in [i * math.pi / 6.0 for i in range(12)]]
        pygame.draw.polygon(surf, col, pts, width)

    def _wline(x0, y0, z0_, x1, y1, z1_, col, w=1):
        pygame.draw.line(surf, col, cam.project(x0, y0, z0_),
                         cam.project(x1, y1, z1_), w)

    # --- the UNDER-LAYER (drawn first, beneath everything): the years on
    # the floor and the wall. A working kitchen stains its room.
    sy0_pre = wy - T * 2.1
    # grease + ash staining around the stove's feet, in the floor plane
    for _ in range(4):
        _ell(wx + rng.uniform(-6, 16), wy + rng.uniform(-12, 14), 0.2,
             rng.uniform(4, 8), rng.uniform(2.5, 5), (24, 20, 16))
    # the worn pale path where feet stood at the counter, years of it
    _ell(wx + 16, sy0_pre + T * 1.0, 0.2, 12, 7, (96, 76, 50))
    _ell(wx + 16, sy0_pre + T * 1.0, 0.3, 7, 4, (104, 84, 56))
    # soot fan up the wall behind the pipe (the wall's vertical plane)
    pygame.draw.polygon(surf, (16, 15, 16), [
        cam.project(wx - 10, wy - 7, 26), cam.project(wx - 10, wy - 9, 40),
        cam.project(wx - 10, wy + 4, 42), cam.project(wx - 10, wy + 6, 26)])

    # --- the pot shelf (wall-most, drawn first): a thin plank at z26
    sy0 = wy - T * 2.1          # shelf spans the counter run
    _vbox(surf, cam, wx - 6, sy0 + T * 0.9, 14, T * 2.2, 26, 29, wood_d)
    # two iron shelf brackets against the wall
    for by in (sy0 + 4, sy0 + T * 1.7):
        _vbox(surf, cam, wx - 9, by, 3, 3, 20, 26, iron_d, outline=False)

    # --- the stovepipe: up from the stove top, elbow into the wall
    _vbox(surf, cam, wx - 2, wy - 2, 6, 6, 24, 46, iron_d, outline=False)
    _vbox(surf, cam, wx - 8, wy - 2, 10, 6, 40, 46, iron_d, outline=False)
    # pipe collar
    _vbox(surf, cam, wx - 2, wy - 2, 8, 8, 24, 26, iron, outline=False)

    # --- the counter run (two tiles north of the stove; the darker
    # palette keeps it welded to the ensemble instead of popping loose)
    _vbox(surf, cam, wx - 1, sy0 + T * 0.95, 22, T * 1.9, 0, 15, wood_d)
    # counter-top dressing: a stew bowl and a cutting board with cleaver
    _ell(wx - 3, sy0 + T * 0.5, 15, 5, 5, (140, 132, 116))
    _ell(wx - 3, sy0 + T * 0.5, 15, 5, 5, (86, 80, 68), 1)
    _ell(wx - 3, sy0 + T * 0.5, 15.5, 3, 3, (96, 78, 58))
    bd = [cam.project(wx - 6, sy0 + T * 1.22, 15),
          cam.project(wx + 6, sy0 + T * 1.18, 15),
          cam.project(wx + 7, sy0 + T * 1.44, 15),
          cam.project(wx - 5, sy0 + T * 1.48, 15)]
    pygame.draw.polygon(surf, (116, 92, 60), bd)
    pygame.draw.polygon(surf, (74, 56, 36), bd, 1)
    _wline(wx - 2, sy0 + T * 1.28, 15.5, wx + 5, sy0 + T * 1.34, 15.5,
           (150, 152, 158), 2)                       # the cleaver blade
    _wline(wx - 5, sy0 + T * 1.26, 15.5, wx - 2, sy0 + T * 1.28, 15.5,
           (70, 52, 32), 2)                          # its wood handle

    # --- the cookstove: legs, body, top plates, fire door
    for lx, ly in ((-9, -8), (9, -8), (-9, 8), (9, 8)):
        _vbox(surf, cam, wx + lx, wy + ly, 3, 3, 0, 4, iron_d, outline=False)
    _vbox(surf, cam, wx, wy, 24, 20, 4, 24, iron)
    for py_ in (-5, 5):          # two round plates on the top
        pp = cam.project(wx + 2, wy + py_, 24)
        pygame.draw.ellipse(surf, (26, 26, 30),
                            (int(pp[0]) - 4, int(pp[1]) - 2, 9, 5))
        pygame.draw.ellipse(surf, (70, 70, 78),
                            (int(pp[0]) - 4, int(pp[1]) - 2, 9, 5), 1)
    # fire door on the ROOM (+x) face, ember glow behind the grate
    d0 = cam.project(wx + 12, wy - 6, 8)
    d1 = cam.project(wx + 12, wy + 6, 8)
    d2 = cam.project(wx + 12, wy + 6, 19)
    d3 = cam.project(wx + 12, wy - 6, 19)
    pygame.draw.polygon(surf, (16, 16, 20), [d0, d1, d2, d3])
    pygame.draw.polygon(surf, (60, 60, 68), [d0, d1, d2, d3], 1)
    gm = cam.project(wx + 12, wy, 13)
    for gi, (gox, goy) in enumerate(((-3, 0), (0, 1), (3, 0), (-1, -2))):
        pygame.draw.rect(surf, (168 - gi * 18, 74 - gi * 10, 24),
                         (int(gm[0]) + gox, int(gm[1]) + goy, 2, 1))

    # --- three pots hung under the shelf: real hanging VOLUMES (small
    # kettle boxes with flared world-plane rims), never screen ellipses
    for i, py_ in enumerate((0.35, 0.95, 1.55)):
        hy = sy0 + T * py_
        r = 3.0 + (i % 2)
        _wline(wx - 3, hy, 26, wx - 3, hy, 23 - i % 2, (150, 150, 160))
        pot = {"top": (44, 44, 50), "side": (32, 32, 38),
               "dark": (20, 20, 24)}
        _vbox(surf, cam, wx - 3, hy, r * 2, r * 2, 17 - (i % 2),
              23 - i % 2, pot, outline=False)
        _ell(wx - 3, hy, 23 - i % 2, r + 1, r + 1, (66, 66, 74), 1)

    # --- the ham on the shelf's north end hook: a hanging body drawn in
    # the world's vertical plane (a y-z circle sweep), netted
    hx, hy2 = wx - 3, sy0 - 2
    _wline(hx, hy2, 26, hx, hy2, 23, (150, 150, 160))
    for rz, rr, col in ((17.5, 4.6, (118, 62, 50)),
                        (17.5, 4.6, None)):
        pts = [cam.project(hx, hy2 + rr * math.cos(a),
                           rz + 5.5 * math.sin(a))
               for a in [i2 * math.pi / 6.0 for i2 in range(12)]]
        if col:
            pygame.draw.polygon(surf, col, pts)
        else:
            pygame.draw.polygon(surf, (86, 44, 36), pts, 1)
    for nz in (15.0, 18.0, 21.0):    # the net, wrapped in world space
        _wline(hx, hy2 - 4.4, nz, hx, hy2 + 4.4, nz, (170, 154, 128))

    # --- the wood crate under the counter's south lip
    _vbox(surf, cam, wx - 1, wy + T * 0.75, 18, 14, 0, 11, wood_d)
    cp = cam.project(wx + 8, wy + T * 0.75, 6)
    for lox in (-3, 2):
        pygame.draw.circle(surf, (120, 96, 62),
                           (int(cp[0]) + lox, int(cp[1])), 2)
        pygame.draw.circle(surf, (70, 52, 32),
                           (int(cp[0]) + lox, int(cp[1])), 2, 1)

    # --- THE WEAR + THE MESS, all WORLD-SPACE (2026-07 rework: the first
    # pass drew screen-aligned marks -- error class 7, "props face the
    # camera" -- and too many same-weight specks. Fewer, BIGGER objects,
    # each in its true plane, each distinguishable at arm's length).
    # rust bleeding down the stove's room face: world-vertical streaks
    for _ in range(4):
        ry_ = wy + rng.uniform(-8, 8)
        rz0 = rng.uniform(14, 20)
        _wline(wx + 12.4, ry_, rz0, wx + 12.4, ry_,
               rz0 - rng.uniform(4, 8), (96, 60, 40))
    # THE SKILLET on the stove's front plate: big black iron, its handle
    # swung toward the room -- the one object the eye lands on first
    _ell(wx + 2, wy + 5, 24.6, 6.5, 6.5, (26, 26, 30))
    _ell(wx + 2, wy + 5, 24.6, 6.5, 6.5, (74, 74, 82), 1)
    _ell(wx + 2, wy + 5, 25.0, 4.2, 4.2, (38, 36, 40))
    _wline(wx + 7, wy + 8, 24.6, wx + 14, wy + 12, 24.6, (30, 30, 34), 2)
    # ash spilled from the fire door onto the boards, a smeared fan
    _ell(wx + 15, wy + 1, 0.4, 5.5, 3.5, (58, 56, 54))
    _ell(wx + 18, wy + 2, 0.3, 3.0, 2.0, (42, 40, 39))
    # soot rings where the pipe sections join (bands around the pipe)
    for jz in (28.0, 38.0):
        _wline(wx - 5, wy - 2, jz, wx + 1, wy - 2, jz, (14, 14, 16), 2)
    # counter top: three long knife scratches + two cup rings, in-plane
    for _ in range(3):
        sx0 = wx + rng.uniform(-6, 0)
        sy_ = sy0 + T * rng.uniform(0.4, 1.5)
        _wline(sx0, sy_, 15.2, sx0 + rng.uniform(5, 9),
               sy_ + rng.uniform(-2, 3), 15.2, (58, 42, 26))
    for ry2 in (0.6, 1.1):
        _ell(wx - 3, sy0 + T * ry2, 15.2, 2.6, 2.6, (52, 38, 24), 1)
    # THE DISH STACK: two full-size plates, rims ringed, slightly offset
    for i, pr in enumerate((6.0, 5.2)):
        _ell(wx - 3 + i, sy0 + T * 0.8, 15.0 + i * 1.4, pr, pr,
             (168, 160, 146))
        _ell(wx - 3 + i, sy0 + T * 0.8, 15.0 + i * 1.4, pr, pr,
             (104, 98, 86), 1)
        _ell(wx - 3 + i, sy0 + T * 0.8, 15.1 + i * 1.4, pr * 0.55,
             pr * 0.55, (140, 132, 118), 1)
    # the tin mug: a real little cylinder with a world-space handle
    mug = {"top": (138, 142, 148), "side": (112, 116, 124),
           "dark": (84, 88, 96)}
    _vbox(surf, cam, wx + 1, sy0 + T * 1.0, 4, 4, 15, 20, mug,
          outline=False)
    _wline(wx + 4, sy0 + T * 1.0, 19, wx + 6, sy0 + T * 1.0, 17,
           (112, 116, 124))
    # silverware: ONE fork, ONE spoon, laid in-plane by the board; one
    # more spoon dropped to the floorboards mid-room
    _wline(wx - 5, sy0 + T * 1.6, 15.2, wx + 1, sy0 + T * 1.62, 15.2,
           (154, 156, 162))
    for pxo in (-0.8, 0.0, 0.8):
        _wline(wx + 1 + pxo, sy0 + T * 1.62, 15.2,
               wx + 2.4 + pxo, sy0 + T * 1.63, 15.2, (154, 156, 162))
    _wline(wx - 4, sy0 + T * 1.75, 15.2, wx + 1, sy0 + T * 1.76, 15.2,
           (154, 156, 162))
    _ell(wx + 2, sy0 + T * 1.76, 15.2, 1.4, 1.4, (154, 156, 162))
    _wline(wx + 13, sy0 + T * 1.9, 0.3, wx + 18, sy0 + T * 1.95, 0.3,
           (128, 130, 136))
    _ell(wx + 19, sy0 + T * 1.95, 0.3, 1.4, 1.4, (128, 130, 136))
    # the rag draped over the counter's room edge: top flap in the
    # counter plane, hanging flap down the face
    rgx, rgy = wx + 9, sy0 + T * 1.3
    pygame.draw.polygon(surf, (140, 126, 104), [
        cam.project(rgx - 4, rgy - 3, 15.2),
        cam.project(rgx + 1, rgy + 4, 15.2),
        cam.project(rgx + 2, rgy + 4, 15.2),
        cam.project(rgx - 2, rgy - 3, 15.2)])
    pygame.draw.polygon(surf, (128, 114, 94), [
        cam.project(rgx + 1, rgy - 2, 15.0),
        cam.project(rgx + 1, rgy + 3, 15.0),
        cam.project(rgx + 1, rgy + 3, 8.0),
        cam.project(rgx + 1, rgy - 2, 9.0)])
    # a chipped plate leaning against the wall on the shelf: a circle in
    # the world's VERTICAL plane, so it turns honestly with the camera
    lpx, lpy = wx - 5, sy0 + T * 0.55
    lpp = [cam.project(lpx, lpy + 4.2 * math.cos(a),
                       29.0 + 4.2 * (1 + math.sin(a)))
           for a in [i2 * math.pi / 6.0 for i2 in range(12)]]
    pygame.draw.polygon(surf, (160, 152, 138), lpp)
    pygame.draw.polygon(surf, (104, 98, 86), lpp, 1)


def _draw_dining_set_solid(surf, cam, deco):
    """THE DINING SET (interiors pilot, TODO #24, ensemble 2): the lodge
    common room's table composed as one object. A plank table on four
    legs, two chairs tucked at lived angles, and ONE place set clean and
    waiting: Sable keeps the room ready for the full house that no
    longer comes. The second seat's place is bare wood. Wear layer per
    the #24 rule: cup rings, scuffed floor where chairs drag, a splinted
    leg, seat centres worn pale. All world-space geometry."""
    wx, wy = deco.x, deco.y
    wood = {"top": (100, 76, 48), "side": (72, 54, 34), "dark": (44, 32, 20)}
    wood_d = {"top": (80, 60, 38), "side": (58, 42, 28), "dark": (36, 26, 16)}

    def _ell(cx, cy, z, rx_, ry_, col, width=0):
        pts = [cam.project(cx + rx_ * math.cos(a), cy + ry_ * math.sin(a), z)
               for a in [i * math.pi / 6.0 for i in range(12)]]
        pygame.draw.polygon(surf, col, pts, width)

    def _wline(x0, y0, z0_, x1, y1, z1_, col, w=1):
        pygame.draw.line(surf, col, cam.project(x0, y0, z0_),
                         cam.project(x1, y1, z1_), w)

    # --- floor wear first: drag scuffs where the chairs live
    for cxo in (-14, 14):
        _wline(wx + cxo - 4, wy + 22, 0.2, wx + cxo + 5, wy + 26, 0.2,
               (58, 44, 28))
        _wline(wx + cxo - 2, wy + 25, 0.2, wx + cxo + 6, wy + 28, 0.2,
               (52, 40, 26))

    # --- two chairs, tucked at slightly different angles (yaw'd volumes)
    for cxo, cyaw in ((-14, 0.18), (14, -0.30)):
        cx = wx + cxo
        cy = wy + 24
        _vbox(surf, cam, cx, cy, 13, 12, 0, 10, wood_d, yaw=cyaw)
        _vbox(surf, cam, cx, cy + 5, 13, 3, 10, 24, wood_d, yaw=cyaw,
              outline=False)
        # the seat's centre worn pale by years of sitting
        _ell(cx, cy - 1, 10.3, 3.5, 3.0, (96, 74, 48))

    # --- the table: four legs, then the plank top with overhang
    for lx, ly in ((-22, -12), (22, -12), (-22, 12), (22, 12)):
        _vbox(surf, cam, wx + lx, wy + ly, 4, 4, 0, 13, wood_d,
              outline=False)
    # the splinted leg: a paler new batten strapped to the NE leg
    _wline(wx + 24, wy - 12, 2, wx + 24, wy - 12, 11, (128, 104, 66), 2)
    _vbox(surf, cam, wx, wy, 56, 32, 13, 16, wood)
    # plank seams along the top, in the table's plane
    for py_ in (-8, 0, 8):
        _wline(wx - 27, wy + py_, 16.2, wx + 27, wy + py_, 16.2,
               (58, 44, 28))
    # table wear: two old cup rings + a long scratch, bare of any cloth
    _ell(wx + 12, wy - 4, 16.2, 2.6, 2.6, (56, 42, 26), 1)
    _ell(wx + 15, wy - 2, 16.2, 2.6, 2.6, (56, 42, 26), 1)
    _wline(wx - 20, wy + 5, 16.2, wx - 4, wy + 7, 16.2, (58, 44, 28))

    # --- THE ONE SET PLACE (the west seat): plate, fork, knife, folded
    # cloth, all squared and clean. Nobody has eaten off it in months.
    px_, py2 = wx - 14, wy - 2
    _ell(px_, py2, 16.4, 5.6, 5.6, (176, 168, 152))
    _ell(px_, py2, 16.4, 5.6, 5.6, (110, 104, 92), 1)
    _ell(px_, py2, 16.5, 3.4, 3.4, (150, 142, 128), 1)
    _wline(px_ - 9, py2 - 4, 16.4, px_ - 9, py2 + 4, 16.4,
           (158, 160, 166))                      # the fork, squared
    for pxo in (-0.9, 0.0, 0.9):
        _wline(px_ - 9 + pxo, py2 - 6, 16.4, px_ - 9 + pxo, py2 - 4,
               16.4, (158, 160, 166))
    _wline(px_ + 9, py2 - 4, 16.4, px_ + 9, py2 + 4, 16.4,
           (158, 160, 166))                      # the knife
    _wline(px_ + 10.2, py2 - 4, 16.4, px_ + 10.2, py2 + 1, 16.4,
           (128, 130, 136))
    cl = [cam.project(px_ - 3, py2 + 7, 16.4),
          cam.project(px_ + 4, py2 + 7, 16.4),
          cam.project(px_ + 5, py2 + 10, 16.4),
          cam.project(px_ - 2, py2 + 10, 16.4)]
    pygame.draw.polygon(surf, (150, 138, 116), cl)  # the folded cloth
    pygame.draw.polygon(surf, (108, 98, 82), cl, 1)
    # the OTHER seat's place: bare wood, and the faint clean rectangle
    # where a second setting once lay (the dust remembers it)
    dr2 = [cam.project(wx + 8, wy - 8, 16.15),
           cam.project(wx + 21, wy - 8, 16.15),
           cam.project(wx + 21, wy + 4, 16.15),
           cam.project(wx + 8, wy + 4, 16.15)]
    pygame.draw.polygon(surf, (106, 82, 52), dr2)


def _draw_bar_dressing_solid(surf, cam, deco):
    """THE SERVICE BAR dressing (interiors pilot, TODO #24, ensemble 3):
    what lives on the lodge's pass-through counter run. The counter tiles
    themselves stay the '5' boxes (collision + see-over unchanged); this
    deco lays Sable's service along the top, world-space, with its wear:
    a water pitcher, the tray of upturned glasses kept ready, folded
    towels, ONE used glass at the far end (the only guest in months
    drank from it), ring stains down the service edge, and a towel over
    the lip. Anchor = the run's centre; the run extends north-south."""
    wx, wy = deco.x, deco.y
    Z = 15.2                      # the counter top plane (_COUNTER_RISE)

    def _ell(cx, cy, z, rx_, ry_, col, width=0):
        pts = [cam.project(cx + rx_ * math.cos(a), cy + ry_ * math.sin(a), z)
               for a in [i * math.pi / 6.0 for i in range(12)]]
        pygame.draw.polygon(surf, col, pts, width)

    def _wline(x0, y0, z0_, x1, y1, z1_, col, w=1):
        pygame.draw.line(surf, col, cam.project(x0, y0, z0_),
                         cam.project(x1, y1, z1_), w)

    # ring stains wandering down the service (east) edge, years of cups
    for oy, orr in ((-52, 2.4), (-20, 2.8), (18, 2.2), (44, 2.6)):
        _ell(wx + 4, wy + oy, Z, orr, orr, (54, 40, 26), 1)
    # the worn pale patch where Sable's hand rests at the pass-through
    _ell(wx + 2, wy + 58, Z, 6, 4, (112, 88, 56))

    # the pitcher at the north end: a real vessel with a lip and handle
    pit = {"top": (146, 150, 156), "side": (116, 120, 128),
           "dark": (86, 90, 98)}
    _vbox(surf, cam, wx - 1, wy - 52, 6, 6, 15, 25, pit, outline=False)
    _ell(wx - 1, wy - 52, 25, 3.4, 3.4, (86, 90, 98), 1)
    _wline(wx + 3, wy - 55, 24, wx + 5, wy - 52, 21, (116, 120, 128))

    # the tray of upturned glasses, squared and READY (the host's habit)
    tr = [cam.project(wx - 6, wy - 34, Z), cam.project(wx + 6, wy - 34, Z),
          cam.project(wx + 6, wy - 16, Z), cam.project(wx - 6, wy - 16, Z)]
    pygame.draw.polygon(surf, (96, 74, 46), tr)
    pygame.draw.polygon(surf, (58, 44, 28), tr, 1)
    for gy in (-30, -25, -20):
        for gx in (-3, 2):
            _ell(wx + gx, wy + gy, Z + 3.5, 1.8, 1.8, (150, 154, 160), 1)

    # folded towels mid-run: two clean stacked quads
    for i in range(2):
        tw = [cam.project(wx - 5, wy - 2 + i, Z + i * 1.2),
              cam.project(wx + 4, wy - 3 + i, Z + i * 1.2),
              cam.project(wx + 5, wy + 6 + i, Z + i * 1.2),
              cam.project(wx - 4, wy + 7 + i, Z + i * 1.2)]
        pygame.draw.polygon(surf, (152, 140, 118) if i else (138, 126, 106),
                            tw)
        pygame.draw.polygon(surf, (104, 94, 78), tw, 1)

    # THE ONE USED GLASS at the south end, its ring beside it: the only
    # guest in months set it down here
    gl = {"top": (150, 154, 160), "side": (122, 126, 134),
          "dark": (94, 98, 106)}
    _vbox(surf, cam, wx - 2, wy + 34, 3.6, 3.6, 15, 20, gl, outline=False)
    _ell(wx - 2, wy + 34, 20, 2.2, 2.2, (94, 98, 106), 1)
    _ell(wx + 3, wy + 38, Z, 2.4, 2.4, (54, 40, 26), 1)

    # the towel over the counter's west lip, top flap + hanging face
    pygame.draw.polygon(surf, (140, 126, 104), [
        cam.project(wx - 8, wy + 12, Z), cam.project(wx - 2, wy + 12, Z),
        cam.project(wx - 2, wy + 20, Z), cam.project(wx - 8, wy + 20, Z)])
    pygame.draw.polygon(surf, (124, 110, 90), [
        cam.project(wx - 8, wy + 13, Z), cam.project(wx - 8, wy + 19, Z),
        cam.project(wx - 8, wy + 19, 7.0), cam.project(wx - 8, wy + 13, 8.0)])


def _draw_cellar_hatch_solid(surf, cam, deco):
    """A timber cellar hatch with real volume: a low raised plank box on the
    floor (not a flat decal), an iron pull-ring on top. Default lid is
    cross-boarded and nailed shut (the barn/farmhouse sealed hatches);
    kwargs: `padlock=True` swaps the cross-boards for a hasp + hanging lock
    (the Lodge's freshly-oiled padlock), `open=True` draws the frame's dark
    mouth with the lid thrown back (the unlocked way down). (The flat
    pitch-0 view uses the 2D sprite.)"""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    kw = getattr(deco, "kwargs", {}) or {}
    w, d, rim = 26 * s, 24 * s, 6 * s
    pal = {"top": (120, 86, 50), "side": (84, 58, 34), "dark": (58, 40, 22)}
    hw, hd = w / 2, d / 2
    if kw.get("open"):
        # the frame's rim, the dark mouth below, the lid thrown back
        _vbox(surf, cam, wx, wy, w, d, 0, rim * 0.5, pal)
        z = rim * 0.5
        mouth = [cam.project(wx - hw + 3 * s, wy - hd + 3 * s, z),
                 cam.project(wx + hw - 3 * s, wy - hd + 3 * s, z),
                 cam.project(wx + hw - 3 * s, wy + hd - 3 * s, z),
                 cam.project(wx - hw + 3 * s, wy + hd - 3 * s, z)]
        pygame.draw.polygon(surf, (10, 8, 8), mouth)
        lid = [cam.project(wx - hw, wy - hd, z),
               cam.project(wx + hw, wy - hd, z),
               cam.project(wx + hw, wy - hd + 4 * s, z + 20 * s),
               cam.project(wx - hw, wy - hd + 4 * s, z + 20 * s)]
        pygame.draw.polygon(surf, pal["side"], lid)
        pygame.draw.polygon(surf, pal["dark"], lid, 1)
        return
    _vbox(surf, cam, wx, wy, w, d, 0, rim, pal)
    tl, tr = cam.project(wx - hw, wy - hd, rim), cam.project(wx + hw, wy - hd, rim)
    bl, br = cam.project(wx - hw, wy + hd, rim), cam.project(wx + hw, wy + hd, rim)
    # plank seams
    for f in (0.33, 0.66):
        a = (tl[0] + (bl[0] - tl[0]) * f, tl[1] + (bl[1] - tl[1]) * f)
        b = (tr[0] + (br[0] - tr[0]) * f, tr[1] + (br[1] - tr[1]) * f)
        pygame.draw.line(surf, pal["dark"], a, b, 1)
    if kw.get("padlock"):
        # hasp over the front edge + the padlock hanging on it
        hp = cam.project(wx, wy + hd - 2 * s, rim)
        pygame.draw.rect(surf, (70, 70, 82),
                         (int(hp[0]) - int(4 * s), int(hp[1]) - int(2 * s),
                          int(8 * s), int(4 * s)))
        lk = cam.project(wx, wy + hd, rim * 0.35)
        r = max(2, int(3 * s))
        pygame.draw.circle(surf, (118, 112, 96), (int(lk[0]), int(lk[1])), r)
        pygame.draw.circle(surf, (46, 44, 40), (int(lk[0]), int(lk[1])), r, 1)
    else:
        # the cross-boards nailed over the lid (shut for good)
        pygame.draw.line(surf, _shade(pal["top"], 1.1), tl, br,
                         max(2, int(2 * s)))
        pygame.draw.line(surf, _shade(pal["top"], 1.1), tr, bl,
                         max(2, int(2 * s)))
    for c in (tl, tr, bl, br):                                  # nail heads
        pygame.draw.circle(surf, (54, 52, 58), (int(c[0]), int(c[1])), max(1, int(1.5 * s)))
    ring = cam.project(wx, wy, rim)                             # iron pull-ring
    pygame.draw.circle(surf, (176, 176, 196), (int(ring[0]), int(ring[1])),
                       max(2, int(4 * s)), 2)


def _draw_hill_cap_solid(surf, cam, deco):
    """One unified grassy DOME over a turf mound: the hill's whole top drawn as
    a SINGLE smooth radial-shaded surface at the wall-top height, so the roof
    reads as ONE object instead of a grid of per-tile tops. `rx`/`ry` are the
    mound's world-px radii and `z` the top height (kwargs); a slight centre
    bulge + a rim->crest grass gradient give it a rounded dome. It sits over the
    tile tops (a `depth_bias` keys it after the mound walls), leaving the stone
    side/cut faces the walls draw below it untouched."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    kw = getattr(deco, "kwargs", {})
    rx = float(kw.get("rx", 100)) * s
    ry = float(kw.get("ry", 88)) * s
    z = float(kw.get("z", 26))
    bulge = float(kw.get("bulge", 9)) * s
    rng = random.Random(getattr(deco, "seed", 0) or 0)
    N = 30
    wob = [1.0 + rng.uniform(-0.05, 0.05) for _ in range(N)]      # organic rim, world-fixed
    rim, crest = (40, 70, 33), (76, 108, 56)                      # grass: dark rim -> lit crest
    steps = 9
    for k in range(steps):
        t = k / (steps - 1)                     # 0 rim .. 1 crest
        scale = 1.0 - 0.94 * t
        zc = z + bulge * t                      # the centre bulges up -> a dome
        col = tuple(int(rim[j] + (crest[j] - rim[j]) * (t ** 0.85)) for j in range(3))
        ring = [cam.project(wx + rx * wob[i] * scale * math.cos(2 * math.pi * i / N),
                            wy + ry * wob[i] * scale * math.sin(2 * math.pi * i / N), zc)
                for i in range(N)]
        pygame.draw.polygon(surf, col, ring)
    # --- DETAIL over the dome (all world-fixed by seed so it never crawls) ---
    def _pt(a, rr, lift=0.0):
        return (wx + rx * rr * math.cos(a), wy + ry * rr * math.sin(a),
                z + bulge * (1.0 - rr) + lift)

    # (a) soft grass CLUMPS -- mottled darker/lighter patches for tonal relief,
    #     so the crown isn't one flat gradient
    for _ in range(int(16 * s)):
        a = rng.uniform(0, 6.283); rr = math.sqrt(rng.random()) * 0.86
        gx, gy, gz = _pt(a, rr)
        c = cam.project(gx, gy, gz)
        pr = int(rng.uniform(6, 13) * s)
        shade = rng.choice([(28, 52, 24), (52, 84, 44), (66, 98, 52)])
        patch = pygame.Surface((pr * 2 + 2, pr + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(patch, (*shade, 85), (0, 0, pr * 2, pr))
        surf.blit(patch, (int(c[0]) - pr, int(c[1]) - pr // 2))

    # (b) STONES poking through the turf -- the hill's own rock showing
    for _ in range(int(5 * s)):
        a = rng.uniform(0, 6.283); rr = math.sqrt(rng.random()) * 0.72
        gx, gy, gz = _pt(a, rr)
        c = cam.project(gx, gy, gz)
        sr = int(rng.uniform(3, 6) * s)
        rk = (int(c[0]) - sr, int(c[1]) - sr // 2, sr * 2, max(2, sr))
        pygame.draw.ellipse(surf, (40, 43, 49), rk)
        pygame.draw.ellipse(surf, (86, 88, 96),
                            (rk[0] + 1, rk[1], rk[2] - 3, max(1, rk[3] - 2)))

    # (c) dense GRASS TUFTS -- varied length, lean and shade, the odd dry gold
    #     tip tying the crown to the field around it
    greens = [(28, 52, 24), (46, 80, 38), (62, 96, 50), (80, 112, 58)]
    for _ in range(int(78 * s)):
        a = rng.uniform(0, 6.283); rr = math.sqrt(rng.random()) * 0.94
        gx, gy, gz = _pt(a, rr)
        p0 = cam.project(gx, gy, gz)
        hh = rng.uniform(2.5, 6.5) * s
        p1 = cam.project(gx + rng.uniform(-1.7, 1.7) * s, gy, gz + hh)
        pygame.draw.line(surf, rng.choice(greens), p0, p1, 1)
        if rng.random() < 0.09:                       # a dry gold blade tip
            pygame.draw.line(surf, (154, 142, 80), p1,
                             (p1[0], p1[1] - max(1, int(1.5 * s))), 1)


# ---- Lighting fixtures as real volumetric props ---------------------------
# Each reads `deco.kwargs['z']` for the base height (a candle on a tabletop
# stands ON the tabletop, not hovering at floor level), then builds the body
# UP from there and projects the flame through the camera. The pitch-0 view
# still uses the 2D `_draw_<kind>` sprite via Scene.draw, byte-identical.
# Game._draw_dark drives the lit pool independently (ground projection of the
# decoration anchor), so all of these stay compatible with the dark-scene
# lighting pass.

def _flame_tri(surf, cam, wx, wy, z_base, fh, fw, col_outer, col_inner):
    """A 2-tone screen-space flame triangle: tip at world height z_base + fh,
    base at z_base. fw is the screen-px half-width at the base."""
    base = cam.project(wx, wy, z_base)
    tip = cam.project(wx, wy, z_base + fh)
    pygame.draw.polygon(surf, col_outer,
                        [(base[0] - fw, base[1]),
                         (base[0] + fw, base[1]),
                         tip])
    inner_tip_y = tip[1] + (base[1] - tip[1]) * 0.35
    pygame.draw.polygon(surf, col_inner,
                        [(base[0] - fw * 0.5, base[1]),
                         (base[0] + fw * 0.5, base[1]),
                         (tip[0], inner_tip_y)])


def _draw_candle_solid(surf, cam, deco):
    """A stout wax pillar with a wick and a guttering flame. Lifts to
    `kwargs['z']` so a candle on a desk stands ON the desk."""
    wx, wy = deco.x, deco.y
    z0 = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    s = (getattr(deco, "scale", 1.0) or 1.0)
    r = 2.2 * s
    h = 8 * s
    wax = {"body": (236, 222, 192), "lo": (164, 152, 128),
           "rim": (252, 240, 218)}
    draw_solid(surf, cam, wx, wy,
               [(z0, r, r), (z0 + h * 0.9, r * 0.95, r * 0.95),
                (z0 + h, r * 0.78, r * 0.78)], wax)
    t = getattr(deco, "t", 0.0)
    fh = (6 + math.sin(t * 18) * 1.0) * s
    fw = (1.6 + math.sin(t * 13) * 0.3) * s * cam.scale
    wick_b = cam.project(wx, wy, z0 + h)
    wick_t = cam.project(wx, wy, z0 + h + 1.0 * s)
    pygame.draw.line(surf, (40, 30, 28), wick_b, wick_t, 1)
    _flame_tri(surf, cam, wx, wy, z0 + h + 0.8 * s, fh, fw,
               (255, 200, 80), (255, 240, 180))


def _draw_kerosene_lamp_solid(surf, cam, deco):
    """A brass oil lamp: cylindrical font, glass chimney, a small flame inside.
    Lifts to `kwargs['z']` for tabletop placement."""
    wx, wy = deco.x, deco.y
    z0 = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    s = (getattr(deco, "scale", 1.0) or 1.0)
    # brass base + font (a low cylinder + a rounded font on top)
    brass = {"body": (152, 110, 50), "lo": (78, 56, 24),
             "rim": (208, 168, 92)}
    rb = 4.5 * s
    base_h = 3 * s
    font_h = 4.5 * s
    chimney_h = 9 * s
    draw_solid(surf, cam, wx, wy,
               [(z0, rb, rb), (z0 + base_h, rb, rb),
                (z0 + base_h + 0.3 * s, rb * 0.78, rb * 0.78),
                (z0 + base_h + font_h, rb * 0.62, rb * 0.62)], brass)
    # glass chimney: a thin translucent cylinder rising above the font
    cz = z0 + base_h + font_h
    rcb = rb * 0.62
    rct = rb * 0.55
    glass_col = (210, 220, 230)
    # draw as 4 vertical edges + 2 caps for a wireframe glass look
    for ang_off in (0.0, math.pi):
        sx0, sy0 = cam.project(wx + math.cos(cam.yaw + ang_off) * rcb,
                               wy + math.sin(cam.yaw + ang_off) * rcb, cz)
        sx1, sy1 = cam.project(wx + math.cos(cam.yaw + ang_off) * rct,
                               wy + math.sin(cam.yaw + ang_off) * rct,
                               cz + chimney_h)
        pygame.draw.line(surf, glass_col, (sx0, sy0), (sx1, sy1), 1)
    # subtle chimney top ring
    _disc(surf, cam, wx, wy, cz + chimney_h, rct, rct,
          _shade(glass_col, 0.9), fill=False, width=1)
    # flame in the chimney
    t = getattr(deco, "t", 0.0)
    fh = (5 + math.sin(t * 16 + deco.seed) * 1.2) * s
    fw = 1.5 * s * cam.scale
    _flame_tri(surf, cam, wx, wy, cz + 1.0 * s, fh, fw,
               (255, 206, 96), (255, 244, 186))


def _draw_lantern_solid(surf, cam, deco):
    """A 19th-century iron lamppost: a vertical pole on the ground, a
    cross-arm at the top, a square lantern hung from the arm. The town-square
    fixture; under dark cult-rooms it's the only legible light."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    iron = (52, 52, 60)
    iron_hi = (96, 96, 108)
    # pole
    pole_h = 30 * s
    base = cam.project(wx, wy, 0)
    top = cam.project(wx, wy, pole_h)
    pygame.draw.line(surf, iron, base, top, max(2, int(2 * s)))
    # cross-arm: a short horizontal beam to one side of the pole
    arm_len = 6 * s
    arm_ax = math.cos(cam.yaw + math.pi / 2)
    arm_ay = math.sin(cam.yaw + math.pi / 2)
    arm_end = cam.project(wx + arm_ax * arm_len, wy + arm_ay * arm_len, pole_h)
    pygame.draw.line(surf, iron, top, arm_end, max(2, int(2 * s)))
    # lantern body hung from the arm end -- a small box
    lx = wx + arm_ax * arm_len
    ly = wy + arm_ay * arm_len
    box_h = 7 * s
    box_w = 5 * s
    lantern_pal = {"top": (60, 56, 50), "side": (38, 36, 40),
                   "dark": (24, 22, 26)}
    draw_box(surf, cam, lx, ly, box_w, box_w, box_h, lantern_pal)
    # chain bit
    hang_top = cam.project(lx, ly, pole_h)
    hang_bot = cam.project(lx, ly, pole_h - 1 * s)
    pygame.draw.line(surf, iron_hi, hang_top, hang_bot, 1)
    # lit window: a small bright square on the lantern's near face
    win_z = pole_h - 1.0 * s - box_h * 0.5
    win = cam.project(lx, ly + box_w * 0.55, win_z)
    ww = max(2, int(box_w * 0.5 * cam.scale))
    wh = max(2, int(box_h * 0.55 * cam.scale))
    pygame.draw.rect(surf, (255, 196, 120),
                     (int(win[0] - ww / 2), int(win[1] - wh / 2), ww, wh))
    pygame.draw.rect(surf, (255, 232, 180),
                     (int(win[0] - ww / 4), int(win[1] - wh / 4),
                      max(1, ww // 2), max(1, wh // 2)))


def _draw_brazier_solid(surf, cam, deco):
    """A cult fire-bowl on an iron tripod: three splayed legs grounded in a
    triangle, a wide flat bowl set on top, the flame guttering above. Reads as
    a real ritual fixture under tilt instead of a 2D sticker."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    iron = (28, 26, 30)
    iron_hi = (66, 64, 70)
    bowl_z = 12 * s
    leg_r = 6 * s
    # three legs, 120deg apart, ground -> bowl center
    apex = cam.project(wx, wy, bowl_z)
    for k in range(3):
        ang = k * (2 * math.pi / 3) + 0.5
        bx = wx + math.cos(ang) * leg_r
        by = wy + math.sin(ang) * leg_r
        base = cam.project(bx, by, 0)
        pygame.draw.line(surf, iron, base, apex, max(2, int(2 * s)))
        pygame.draw.line(surf, iron_hi, base, apex, 1)
    # bowl: a low cylinder, wider at the top -- the rim shows
    rb = 8 * s
    rim_r = 9 * s
    bowl_pal = {"body": (42, 40, 44), "lo": (18, 16, 20),
                "rim": (96, 78, 60)}
    draw_solid(surf, cam, wx, wy,
               [(bowl_z, rb, rb), (bowl_z + 3 * s, rim_r, rim_r)], bowl_pal)
    # dark coals visible inside the rim
    _disc(surf, cam, wx, wy, bowl_z + 3 * s, rim_r * 0.7, rim_r * 0.7,
          (18, 16, 20))
    # flame
    t = getattr(deco, "t", 0.0)
    fh = (8 + math.sin(t * 6 + deco.seed) * 3) * s
    fw = 4 * s * cam.scale
    _flame_tri(surf, cam, wx, wy, bowl_z + 3 * s, fh, fw,
               (208, 88, 28), (250, 178, 68))


def _draw_burn_barrel_solid(surf, cam, deco):
    """A 55 gallon burn drum, lit. No garbage service since the January
    seal, so the town burns what it can't keep: a rusted drum at the
    yard corner, scorched black at the rim, a trash fire guttering
    inside. The fire is a LIGHT; the eye crosses a dark yard to it."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    r = 7 * s
    h = 16 * s
    drum = {"body": (104, 66, 44), "lo": (48, 30, 22), "rim": (30, 24, 20)}
    draw_solid(surf, cam, wx, wy, [(0, r, r), (h, r * 0.96, r * 0.96)], drum)
    # rolling rings around the drum
    for rz in (h * 0.3, h * 0.68):
        _disc(surf, cam, wx, wy, rz, r * 0.99, r * 0.99, (66, 42, 28),
              fill=False, width=1)
    # scorched mouth + the coal bed inside
    _disc(surf, cam, wx, wy, h, r * 0.98, r * 0.98, (26, 20, 16))
    _disc(surf, cam, wx, wy, h, r * 0.7, r * 0.7, (52, 26, 14))
    # vent holes punched near the base, glowing with the fire behind them
    t = getattr(deco, "t", 0.0)
    for k, vx in enumerate((-r * 0.45, 0.0, r * 0.45)):
        vp = cam.project(wx + vx, wy + r * 0.85, 3 * s)
        gl = 190 + int(math.sin(t * 7 + deco.seed + k * 2.1) * 40)
        pygame.draw.circle(surf, (gl, 96, 30), (int(vp[0]), int(vp[1])),
                           max(1, int(1.2 * s)))
    # the fire
    fh = (9 + math.sin(t * 6 + deco.seed) * 3) * s
    fw = 4.5 * s * cam.scale
    _flame_tri(surf, cam, wx, wy, h, fh, fw, (208, 88, 28), (250, 178, 68))


def _draw_camp_fire_solid(surf, cam, deco):
    """A lit ground fire at the cult camp: a ring of fieldstones, a glowing
    coal bed, a low teepee of charred logs, and guttering flame. A LIGHT the
    dark field crosses to (the crew gathers around it). Distinct from the dead
    indoor `campfire` scorch decal."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    t = getattr(deco, "t", 0.0)
    # ash + coal bed on the ground
    _disc(surf, cam, wx, wy, 0, 9 * s, 6.5 * s, (36, 30, 26))
    _disc(surf, cam, wx, wy, 0, 5.5 * s, 4 * s, (70, 40, 22))
    gl = 150 + int(math.sin(t * 5 + deco.seed) * 40)
    _disc(surf, cam, wx, wy, 0, 3 * s, 2.2 * s, (gl, 60, 24))
    # ring of fieldstones
    for k in range(9):
        a = k * (2 * math.pi / 9) + 0.3
        sx = wx + math.cos(a) * 11 * s
        sy = wy + math.sin(a) * 11 * s
        _disc(surf, cam, sx, sy, 0, 2.3 * s, 1.9 * s, (98, 94, 98))
        _disc(surf, cam, sx, sy, 0, 2.3 * s, 1.9 * s, (58, 56, 60),
              fill=False, width=1)
    # a low teepee of charred logs leaning into the middle
    log = {"body": (54, 38, 24), "lo": (28, 18, 12), "rim": (86, 62, 38)}
    for k in range(3):
        a = k * (2 * math.pi / 3) + 0.5
        lx = wx + math.cos(a) * 5.5 * s
        ly = wy + math.sin(a) * 5.5 * s
        draw_solid(surf, cam, lx, ly,
                   [(0, 2.2 * s, 2.2 * s), (8 * s, 1.1 * s, 1.1 * s)], log)
    # flame
    for k, (fx, fy, m) in enumerate(((0, 0, 1.0), (-3.2 * s, 1.4 * s, 0.66),
                                     (3.2 * s, -1.2 * s, 0.72))):
        fh = (11 + math.sin(t * 6 + deco.seed + k * 1.7) * 4.5) * s * m
        fw = 4.6 * s * cam.scale * (0.7 + 0.3 * m)
        _flame_tri(surf, cam, wx + fx, wy + fy, 4 * s, fh, fw,
                   (206, 84, 26), (250, 182, 74))


def _draw_news_rack_solid(surf, cam, deco):
    """A coin-op newspaper vending box on four stub legs, enamel gone
    chalky, the window still showing the last issue it was ever fed
    (the January 15 seal-day weekly; the examine carries the date).
    Faces SOUTH; placements stand it against a south wall face."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    bw, bd = 13 * s, 9 * s
    legz, topz = 5 * s, 20 * s
    red = (128, 54, 46)
    pal = {"top": _shade(red, 1.15), "side": _shade(red, 0.8),
           "dark": _shade(red, 0.55)}
    hw, hd = bw / 2, bd / 2
    for lx, ly in ((-hw + 1, -hd + 1), (hw - 1, -hd + 1),
                   (-hw + 1, hd - 1), (hw - 1, hd - 1)):
        a = cam.project(wx + lx, wy + ly, 0)
        b = cam.project(wx + lx, wy + ly, legz)
        pygame.draw.line(surf, (40, 40, 44), a, b, 2)
    _vbox(surf, cam, wx, wy, bw, bd, legz, topz, pal)

    def PP(lx, lz):
        p = cam.project(wx + lx, wy + hd + 0.2, lz)
        return (int(p[0]), int(p[1]))
    # display window: bleached newsprint behind scratched plastic
    paper = (186, 180, 160)
    pygame.draw.polygon(surf, paper, [
        PP(-hw + 2 * s, legz + 7 * s), PP(hw - 2 * s, legz + 7 * s),
        PP(hw - 2 * s, topz - 2 * s), PP(-hw + 2 * s, topz - 2 * s)])
    pygame.draw.line(surf, (52, 50, 48), PP(-hw + 3 * s, topz - 4 * s),
                     PP(hw - 3 * s, topz - 4 * s), 2)       # the headline
    pygame.draw.line(surf, (108, 104, 94), PP(-hw + 3 * s, topz - 6 * s),
                     PP(hw - 3 * s, topz - 6 * s), 1)       # column smudge
    pygame.draw.line(surf, (108, 104, 94), PP(-hw + 3 * s, topz - 8 * s),
                     PP(-2 * s, topz - 8 * s), 1)
    # coin box seam + slot below the window
    pygame.draw.line(surf, pal["dark"], PP(-hw + 1, legz + 6 * s),
                     PP(hw - 1, legz + 6 * s), 1)
    slot = PP(hw - 4 * s, legz + 3 * s)
    pygame.draw.rect(surf, (24, 24, 26), (slot[0], slot[1], max(1, int(2 * s)),
                                          max(1, int(1 * s))))


def _draw_wall_torch_solid(surf, cam, deco):
    """An iron wall sconce: a short vertical post rising off the floor with a
    flat iron cup at the top, a guttering flame in the cup. Drawn standing
    upright at the deco's ground point (placements line it against the wall
    already). Game._draw_dark drives the warm pool around it."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    iron = (38, 34, 36)
    iron_hi = (74, 70, 72)
    post_h = 14 * s
    base = cam.project(wx, wy, 0)
    top = cam.project(wx, wy, post_h)
    pygame.draw.line(surf, iron, base, top, max(2, int(2 * s)))
    pygame.draw.line(surf, iron_hi, base, top, 1)
    # cup: a wide flat disc
    _disc(surf, cam, wx, wy, post_h, 3 * s, 3 * s, (62, 56, 50))
    _disc(surf, cam, wx, wy, post_h, 3 * s, 3 * s, iron, fill=False, width=1)
    # flame
    t = getattr(deco, "t", 0.0)
    fh = (11 + math.sin(t * 16) * 2.2) * s
    fw = 2.5 * s * cam.scale
    _flame_tri(surf, cam, wx, wy, post_h + 0.5 * s, fh, fw,
               (190, 70, 24), (245, 165, 48))
    # bright core
    core_b = cam.project(wx, wy, post_h + 1.0 * s)
    core_t = cam.project(wx, wy, post_h + 1.0 * s + fh * 0.45)
    pygame.draw.line(surf, (255, 236, 175), core_b, core_t,
                     max(1, int(1.5 * s)))


def _draw_wall_lamp_solid(surf, cam, deco):
    """A period interior electric fixture: a short conduit up the wall, a
    bracket out toward the room, a frosted shade, and a STEADY warm bulb. The
    1994 indoor twin of the yard light -- what the town's gensets actually
    power inside (a bulkhead / utility light), not a candle. Drawn mounted up
    the wall at its ground point (placements line it against the wall);
    Game._draw_dark casts its warm pool."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    metal = (60, 58, 62)
    metal_hi = (98, 96, 102)
    mount_h = 20 * s
    base = cam.project(wx, wy, 0)
    top = cam.project(wx, wy, mount_h)
    pygame.draw.line(surf, metal, base, top, max(1, int(1.5 * s)))       # conduit
    pygame.draw.line(surf, metal_hi, base, top, 1)
    # frosted shade: a small pale dome atop the conduit. SYMMETRIC (no arm),
    # so it reads mounted on ANY wall regardless of orientation, never a
    # bracket poking into the wall.
    draw_solid(surf, cam, wx, wy,
               [(mount_h - 3.2 * s, 3.0 * s, 3.0 * s),
                (mount_h - 0.6 * s, 2.6 * s, 2.6 * s),
                (mount_h, 1.4 * s, 1.4 * s)],
               {"body": (150, 146, 140), "lo": (92, 88, 84),
                "rim": (178, 174, 168)})
    # the steady warm bulb glowing at the shade's lower lip
    lamp = cam.project(wx, wy + 1.8 * s, mount_h - 3.4 * s)
    lr = max(2, int(2.2 * s * cam.scale))
    glow = pygame.Surface((lr * 6, lr * 6), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 210, 150, 66), (lr * 3, lr * 3), lr * 3)
    pygame.draw.circle(glow, (255, 224, 176, 120), (lr * 3, lr * 3), lr * 2)
    surf.blit(glow, (int(lamp[0] - lr * 3), int(lamp[1] - lr * 3)))
    pygame.draw.circle(surf, (255, 230, 182), (int(lamp[0]), int(lamp[1])), lr)


def _draw_smoke_solid(surf, cam, deco):
    """A rising column of smoke -- four puffs ascending in world z, each
    larger and more faded than the last. Reads as a real column you can
    walk around instead of a 2D sticker stuck to the wall."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    z0 = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    t = getattr(deco, "t", 0.0)
    seed = getattr(deco, "seed", 0)
    for i in range(4):
        phase = (t * 0.6 + i * 0.4 + seed * 0.1) % 1.0
        ox = math.sin(phase * 6 + seed) * 3 * s
        rise = z0 + 4 * s + phase * 36 * s
        r = (4 + phase * 6) * s
        alpha = int((1 - phase) * 130)
        cx, cy = cam.project(wx + ox, wy, rise)
        rs = max(2, int(r * cam.scale))
        puff = pygame.Surface((rs * 2 + 2, rs * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(puff, (160, 160, 170, alpha),
                           (rs + 1, rs + 1), rs)
        surf.blit(puff, (cx - rs, cy - rs))


def _draw_wisp_solid(surf, cam, deco):
    """A will-o-the-wisp: a cold pale glow drifting LOW over the bog. Drawn
    as a small floating orb projected at a marsh-gas height, so it reads as a
    light in the air, not painted on the ground."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    t = getattr(deco, "t", 0.0)
    seed = getattr(deco, "seed", 0)
    z_air = 8 * s
    drift_x = math.sin(t * 0.5 + seed) * 14 * s
    drift_y = math.cos(t * 0.37 + seed * 0.6) * 8 * s
    z_bob = math.sin(t * 0.42 + seed * 0.3) * 2 * s
    cx, cy = cam.project(wx + drift_x, wy + drift_y, z_air + z_bob)
    rs = max(2, int(10 * s * cam.scale))
    glow = pygame.Surface((rs * 2 + 4, rs * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(glow, (110, 168, 146, 38),
                       (rs + 2, rs + 2), rs)
    pygame.draw.circle(glow, (150, 200, 174, 70),
                       (rs + 2, rs + 2), max(1, rs // 2))
    pygame.draw.circle(glow, (210, 235, 220),
                       (rs + 2, rs + 2), max(1, rs // 5))
    surf.blit(glow, (cx - rs - 2, cy - rs - 2))


def _draw_rope_solid(surf, cam, deco):
    """A hung cord: a vertical rope dropping from a hang height down toward
    the anchor, frayed knot at the bottom. Reads as a real hanging line in
    3D space instead of a curved sticker on the floor."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    z_hang = 24 * s
    z_bot = 4 * s
    seed = getattr(deco, "seed", 0)
    kink_x = math.sin(seed * 0.7) * 1.0 * s
    cord = (132, 110, 70)
    cord_dk = (92, 74, 44)
    top = cam.project(wx, wy, z_hang)
    mid = cam.project(wx + kink_x, wy, (z_hang + z_bot) / 2)
    bot = cam.project(wx, wy, z_bot)
    pygame.draw.line(surf, cord_dk, top, mid, max(2, int(2 * s)))
    pygame.draw.line(surf, cord_dk, mid, bot, max(2, int(2 * s)))
    pygame.draw.line(surf, cord, top, mid, 1)
    pygame.draw.line(surf, cord, mid, bot, 1)
    pygame.draw.circle(surf, cord_dk, bot, max(2, int(2 * s)))


def _draw_mote_solid(surf, cam, deco):
    """A floating dust mote: a single pixel-sized speck lifted off the floor
    to about head height, drifting slowly. Reads as suspended in the air
    instead of a glitter on the ground."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    t = getattr(deco, "t", 0.0)
    seed = getattr(deco, "seed", 0)
    z_air = 16 * s
    dx = math.sin(t * 0.4 + seed) * 8 * s
    dy = math.cos(t * 0.3 + seed * 0.7) * 4 * s
    z_bob = math.sin(t * 0.32 + seed * 0.4) * 3 * s
    cx, cy = cam.project(wx + dx, wy + dy, z_air + z_bob)
    col = (200, 200, 220)
    try:
        surf.set_at((cx, cy), col)
        surf.set_at((cx + 1, cy), col)
    except (IndexError, ValueError):
        pass


def _draw_flock_solid(surf, cam, deco):
    """A few distant birds drifting across the grey, wings beating. Each
    silhouette is projected at sky height so the flock reads as overhead
    under tilt instead of pasted on the field."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    t = getattr(deco, "t", 0.0)
    seed = getattr(deco, "seed", 0)
    span = deco.kwargs.get("span", 180)
    speed = deco.kwargs.get("speed", 0.5)
    lead = ((t * speed * 16 + seed * 7) % (span + 60)) - 30
    n = 3 + (seed % 3)
    z_sky = 60 * s
    for i in range(n):
        bx_w = wx + lead - i * (11 + (seed + i) % 8)
        bz = z_sky + (i % 3 - 1) * 6 * s + math.sin(t * 0.6 + i) * 3 * s
        by_w = wy + (i % 3 - 1) * 4 * s
        flap = math.sin(t * 6 + i * 1.3) * 4 * s
        cx, cy = cam.project(bx_w, by_w, bz)
        wing_dx = max(3, int(5 * s * cam.scale))
        wing_dy = max(2, int(flap * cam.scale))
        col = (52, 52, 60)
        pygame.draw.line(surf, col, (cx - wing_dx, cy + wing_dy), (cx, cy), 2)
        pygame.draw.line(surf, col, (cx + wing_dx, cy + wing_dy), (cx, cy), 2)


def _draw_crow_solid(surf, cam, deco):
    """A perched crow stood up off the ground: contact shadow at z=0, legs,
    body and head projected at real heights so it sits IN the scene instead of
    lying flat. Drawn live every frame (not a cached standee card) so the hop,
    the head-turn, and the rare looking-backwards anomaly all survive under
    tilt (the anomaly is a designed beat; freezing it on a card would kill it)."""
    t = getattr(deco, "t", 0.0)
    seed = getattr(deco, "seed", 0)
    s = cam.scale
    hop = abs(math.sin(t * 0.8)) * 1.0
    head_turn = math.sin(t * 0.5) * 2.0
    ink = (10, 10, 14)
    bx, by = cam.project(deco.x, deco.y, 0)
    # contact shadow so the perch reads grounded
    sw = max(3, int(6 * s))
    sh = max(2, int(3 * s * cam.ground_squash()))
    shadow = pygame.Surface((sw * 2, sh * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 70), (0, 0, sw * 2, sh * 2))
    surf.blit(shadow, (bx - sw, by - sh))
    # body
    cx, cy = cam.project(deco.x, deco.y, 3.0 + hop)
    bw = max(4, int(10 * s))
    bh = max(3, int(6 * s))
    # stick legs from the body underside to the ground point
    for lx in (-2, 2):
        pygame.draw.line(surf, ink,
                         (cx + int(lx * s), cy + bh // 2 - 1),
                         (bx + int(lx * s), by), 1)
    pygame.draw.ellipse(surf, ink, (cx - bw // 2, cy - bh // 2, bw, bh))
    # tail tick off the back
    pygame.draw.line(surf, ink, (cx - bw // 2, cy),
                     (cx - bw // 2 - max(2, int(3 * s)), cy - 1), 1)
    # head -- same rare looking-backwards anomaly as the flat art: at a
    # per-seed phase the head flips to the opposite side for ~120ms.
    anomaly_phase = (t + seed * 0.13) % 9.0
    side = -1 if anomaly_phase > 8.88 else 1
    hx, hy = cam.project(deco.x, deco.y, 7.0 + hop)
    head_x = int(hx + side * (4 + head_turn) * s)
    pygame.draw.circle(surf, ink, (head_x, hy), max(1, int(2 * s)))
    eye_x = int(hx + side * (5 + head_turn) * s)
    pygame.draw.circle(surf, (220, 200, 50), (eye_x, hy), 1)


def _draw_stalk_marker_solid(surf, cam, deco):
    """A single corn stalk taller than the rest with a sun-bleached red cloth
    tied around it. The cult marks the next to be taken. Rises as a real
    vertical line under tilt, swaying."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    t = getattr(deco, "t", 0.0)
    seed = getattr(deco, "seed", 0)
    H = 26 * s
    sway = math.sin(t * 1.4 + seed * 0.13) * 1.6 * s
    stalk = (74, 102, 50)
    stalk_dk = (44, 64, 30)
    base = cam.project(wx, wy, 0)
    tip_ground_dx = sway
    tip = cam.project(wx + tip_ground_dx, wy, H)
    pygame.draw.line(surf, stalk_dk, base, tip, max(2, int(2 * s)))
    pygame.draw.line(surf, stalk, base, tip, 1)
    # husk leaf at mid-height
    mid_z = H * 0.45
    mid_a = cam.project(wx, wy, mid_z)
    mid_b = cam.project(wx + 4 * s, wy, mid_z + 1 * s)
    pygame.draw.line(surf, stalk_dk, mid_a, mid_b, 1)
    # cloth band near the top
    cloth = (164, 80, 60)
    cloth_dk = (100, 44, 36)
    band_z0 = H * 0.78
    band_z1 = H * 0.92
    b_lo = cam.project(wx + tip_ground_dx * 0.85, wy, band_z0)
    b_hi = cam.project(wx + tip_ground_dx * 0.85, wy, band_z1)
    bw = max(2, int(4 * s * cam.scale))
    bh = max(2, int(abs(b_hi[1] - b_lo[1])))
    rect = (b_hi[0] - bw // 2, b_hi[1], bw, bh)
    pygame.draw.rect(surf, cloth_dk, rect)
    pygame.draw.rect(surf, cloth, (rect[0] + 1, rect[1] + 1,
                                    rect[2] - 2, max(1, rect[3] - 2)))
    # token hung from the cloth
    tok = cam.project(wx + tip_ground_dx * 0.85 + 2 * s, wy, band_z0 - 3 * s)
    pygame.draw.circle(surf, (40, 30, 24),
                       (int(tok[0]), int(tok[1])), max(1, int(1.5 * s)))


# -- Anchored volumes (the sprite-depth-anchoring pass) --------------------
# Props that used to draw as flat CAMERA-FACING cards (standees) or flat
# top-down stickers under tilt because they were registered in no solid set.
# Each now renders as world-oriented geometry so it depth-sorts + foreshortens
# with the room instead of pointing at the camera forever. Palettes + silhouettes
# match the authored 2D art in entities/deco_* so the object stays recognizable.


def _draw_standing_stone_solid(surf, cam, deco):
    """A weathered monolith as a real leaning slab: a tapering stone with two
    visible side faces catching the tilt, moss at the foot, lichen up one face,
    a hairline crack. Seeded so a row reads as siblings, never copies (matches
    entities/deco_structure `_draw_standing_stone`)."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    seed = getattr(deco, "seed", 0)
    H = (26 + (seed % 12)) * s                     # world height
    W = (9 + ((seed >> 3) % 4)) * s                # base width
    T = (4.0 + ((seed >> 5) % 3) * 0.8) * s        # depth
    lean_x = (((seed >> 7) % 7) - 3) * 0.5 * s
    lean_y = (((seed >> 9) % 5) - 2) * 0.3 * s
    stone = {"body": (96, 94, 98), "lo": (52, 50, 56), "rim": (126, 124, 130)}
    _disc(surf, cam, wx, wy, 0.3, W * 0.7 + 2, T + 2, (34, 40, 30))   # moss foot
    cxt, cyt = wx + lean_x, wy + lean_y
    topw = W * 0.5                                 # tapers toward the crown
    b = (cam.project(wx - W / 2, wy - T / 2, 0),
         cam.project(wx + W / 2, wy - T / 2, 0),
         cam.project(wx + W / 2, wy + T / 2, 0),
         cam.project(wx - W / 2, wy + T / 2, 0))
    t = (cam.project(cxt - topw / 2, cyt - T / 2, H),
         cam.project(cxt + topw / 2, cyt - T / 2, H),
         cam.project(cxt + topw / 2, cyt + T / 2, H),
         cam.project(cxt - topw / 2, cyt + T / 2, H))
    pygame.draw.polygon(surf, stone["body"], [b[3], b[2], t[2], t[3]])   # near
    pygame.draw.polygon(surf, stone["lo"], [b[0], b[3], t[3], t[0]])     # west
    pygame.draw.polygon(surf, stone["lo"], [b[1], b[2], t[2], t[1]])     # east
    pygame.draw.polygon(surf, stone["rim"], [t[0], t[1], t[2], t[3]])    # crown
    pygame.draw.line(surf, stone["rim"], t[0], t[3], 1)
    # a hairline crack wandering down the near face
    fq = (t[3], t[2], b[2], b[3])                  # TL,TR,BR,BL of the near face
    fx = 0.45 + ((seed >> 2) % 4) * 0.05
    cr = []
    for k in range(4):
        fx += (((seed >> (k + 1)) % 3) - 1) * 0.06
        cr.append(_quad_pt(fq, min(0.9, max(0.1, fx)), 0.12 + k * 0.24))
    pygame.draw.lines(surf, stone["lo"], False,
                      [(int(px), int(py)) for px, py in cr], 1)
    lich = _quad_pt(fq, 0.72, 0.4)                 # lichen bloom
    pygame.draw.circle(surf, (134, 138, 118), (int(lich[0]), int(lich[1])),
                       max(1, int(2 * s)))
    mo = cam.project(wx - W * 0.3, wy + T * 0.2, H * 0.1)   # moss clump
    pygame.draw.circle(surf, (58, 74, 50), (int(mo[0]), int(mo[1])),
                       max(1, int(2 * s)))


def _draw_wheelbarrow_solid(surf, cam, deco):
    """A single-wheel barrow as real volume: an open tapered tub on a wheel at
    the front + two rear legs + two handles running back and up, a pile of
    rusted tools in the tub. Built FOR the tilt (the wheel + handles that
    identify it are the visible parts). `yaw` kwarg turns it."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    yaw = float(getattr(deco, "kwargs", {}).get("yaw", 0.9))
    P = _vframe(cam, wx, wy, yaw)
    L, W = 24 * s, 16 * s
    hL, hW = L / 2, W / 2
    z0, z1 = 6 * s, 13 * s
    r = 5 * s
    wood = {"top": (120, 86, 54), "side": (92, 64, 40), "dark": (60, 40, 24)}
    _vehicle_shadow(surf, cam, wx, wy, L, W)
    _round_wheel(surf, P, hL + 2 * s, 0, r)        # single wheel at the front
    for ly in (-hW * 0.7, hW * 0.7):               # two rear legs
        pygame.draw.line(surf, wood["dark"],
                         P(-hL + 2 * s, ly, 0), P(-hL + 2 * s, ly, z0 + 1 * s),
                         max(2, int(2 * s)))
    _vbox(surf, cam, wx, wy, L, W, z0, z1, wood, yaw=yaw)
    mouth = [P(-hL + 2 * s, -hW + 1.5 * s, z1), P(hL - 2 * s, -hW + 1.5 * s, z1),
             P(hL - 2 * s, hW - 1.5 * s, z1), P(-hL + 2 * s, hW - 1.5 * s, z1)]
    pygame.draw.polygon(surf, (40, 28, 20), mouth)     # open tub mouth
    tp = P(2 * s, 0, z1 + 1 * s)                        # tool pile
    pygame.draw.circle(surf, (150, 120, 96), (int(tp[0]), int(tp[1])),
                       max(2, int(2.4 * s)))
    pygame.draw.line(surf, (170, 150, 140), P(-4 * s, -2 * s, z1 + 1 * s),
                     P(6 * s, 2 * s, z1 + 3 * s), max(1, int(1.5 * s)))
    for ly in (-hW * 0.8, hW * 0.8):                   # two handles back-and-up
        pygame.draw.line(surf, wood["side"], P(-hL, ly, z1 - 1 * s),
                         P(-hL - 9 * s, ly, z1 + 4 * s), max(2, int(2 * s)))
    pygame.draw.lines(surf, _shade(wood["top"], 1.2), True,
                      [P(-hL, -hW, z1), P(hL, -hW, z1),
                       P(hL, hW, z1), P(-hL, hW, z1)], 1)


def _draw_pedestal_solid(surf, cam, deco):
    """A stone pedestal as a stacked plinth: a wide base slab, a slimmer shaft,
    a wide cap slab -- square faces that catch the tilt (the flat card read as
    a floating tablet). Keeps the soft `lit` glow pooled above the cap."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    body = {"top": (120, 120, 130), "side": (96, 96, 106), "dark": (60, 60, 70)}
    slab = {"top": (140, 140, 150), "side": (110, 110, 120), "dark": (72, 72, 82)}
    _vbox(surf, cam, wx, wy, 22 * s, 16 * s, 0, 3 * s, slab)          # base
    _vbox(surf, cam, wx, wy, 17 * s, 12 * s, 3 * s, 15 * s, body)     # shaft
    _vbox(surf, cam, wx, wy, 22 * s, 16 * s, 15 * s, 18 * s, slab)    # cap
    if getattr(deco, "kwargs", {}).get("lit", True):
        pulse = 0.6 + math.sin(getattr(deco, "t", 0.0) * 2.0 + deco.seed) * 0.4
        cx, cy = cam.project(wx, wy, 20 * s)
        gw = int(10 * s * cam.scale)
        gh = max(2, int(4 * s * cam.ground_squash() * cam.scale))
        glow = pygame.Surface((gw * 2 + 2, gh * 2 + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (200, 180, 220, int(120 * pulse)),
                            (1, 1, gw * 2, gh * 2))
        surf.blit(glow, (cx - gw - 1, cy - gh - 1))


def _draw_corn_altar_solid(surf, cam, deco):
    """The cult's small offering as a mounded solid: a low husk-stalk heap,
    three corn cobs stacked on top, a half-burned candle stub with a live
    flame -- depth instead of a flat top-down sticker."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    t = getattr(deco, "t", 0.0)
    husk = {"body": (110, 92, 52), "lo": (66, 52, 30), "rim": (140, 118, 66)}
    draw_solid(surf, cam, wx, wy,
               [(0, 11 * s, 9 * s), (4 * s, 8 * s, 6 * s),
                (7 * s, 4 * s, 3 * s)], husk)
    cob = {"body": (218, 192, 88), "lo": (160, 130, 56), "rim": (250, 226, 130)}
    for ox, oy, cz in [(-3 * s, 1 * s, 7 * s), (3 * s, -1 * s, 7 * s),
                       (0, 0, 9 * s)]:
        draw_solid(surf, cam, wx + ox, wy + oy,
                   [(cz, 3 * s, 2 * s), (cz + 4 * s, 1.4 * s, 1 * s)], cob)
    zc = 12 * s
    draw_solid(surf, cam, wx, wy,
               [(zc, 1.4 * s, 1.4 * s), (zc + 3 * s, 1.2 * s, 1.2 * s)],
               {"body": (208, 200, 178), "lo": (150, 144, 126),
                "rim": (230, 224, 206)})
    fh = (5 + math.sin(t * 15) * 0.8) * s
    _flame_tri(surf, cam, wx, wy, zc + 3 * s, fh, 1.4 * s * cam.scale,
               (255, 200, 80), (255, 240, 180))


def _draw_butter_churn_solid(surf, cam, deco):
    """A barrel butter churn as a body of revolution: tapered staves, two iron
    hoops, a lid, the plunger staff leaning out of it. Lifts to `kwargs['z']`
    if it sits on a surface (else on the floor)."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    z0 = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    H, Rb, Rt = 18 * s, 7 * s, 5.5 * s
    wood = {"body": (92, 66, 40), "lo": (56, 40, 24), "rim": (120, 92, 58)}
    draw_solid(surf, cam, wx, wy,
               [(z0, Rb, Rb), (z0 + H * 0.9, Rt, Rt),
                (z0 + H, Rt * 0.92, Rt * 0.92)], wood)
    iron = (70, 68, 74)
    _disc(surf, cam, wx, wy, z0 + H * 0.16, Rb * 0.99, Rb * 0.99, iron,
          fill=False, width=2)
    _disc(surf, cam, wx, wy, z0 + H * 0.72, Rt * 1.02, Rt * 1.02, iron,
          fill=False, width=2)
    _disc(surf, cam, wx, wy, z0 + H, Rt * 0.9, Rt * 0.9, (70, 50, 30))   # lid
    p0 = cam.project(wx, wy, z0 + H)
    p1 = cam.project(wx + 4 * s, wy - 1 * s, z0 + H + 12 * s)
    pygame.draw.line(surf, (84, 62, 40), p0, p1, max(2, int(2 * s)))
    pygame.draw.circle(surf, (84, 62, 40), (int(p1[0]), int(p1[1])),
                       max(2, int(2 * s)))


def _draw_washstand_solid(surf, cam, deco):
    """A bedroom washstand as real volume: a box stand with a porcelain basin
    sunk in the top (the water a shade too dark), a ewer jug beside it, a limp
    towel over the near edge."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    W, D, H = 19 * s, 13 * s, 13 * s
    wood = {"top": (72, 54, 38), "side": (56, 42, 30), "dark": (38, 28, 20)}
    _vbox(surf, cam, wx, wy, W, D, 0, H, wood)
    _disc(surf, cam, wx, wy, H, W * 0.32, W * 0.32, (208, 202, 188))   # basin
    _disc(surf, cam, wx, wy, H, W * 0.22, W * 0.22, (44, 48, 50))      # dark water
    ex, ey = wx + W * 0.3, wy - D * 0.15                               # ewer jug
    draw_solid(surf, cam, ex, ey,
               [(H, 2.6 * s, 2.6 * s), (H + 3 * s, 3 * s, 3 * s),
                (H + 5.5 * s, 1.6 * s, 1.6 * s)],
               {"body": (208, 202, 188), "lo": (148, 142, 130),
                "rim": (230, 224, 210)})
    tw = [cam.project(wx - W * 0.5, wy + D * 0.35, H * 0.9),            # towel
          cam.project(wx - W * 0.5, wy + D * 0.5, H * 0.9),
          cam.project(wx - W * 0.5, wy + D * 0.5, H * 0.25),
          cam.project(wx - W * 0.5, wy + D * 0.35, H * 0.25)]
    pygame.draw.polygon(surf, (168, 160, 144), tw)
    pygame.draw.polygon(surf, (132, 124, 110), tw, 1)


def _draw_birdcage_solid(surf, cam, deco):
    """A domed wire birdcage on a floor stand as a real cage: a stand post, a
    ring of vertical bars (near bars brighter than far), a stepped dome cap, a
    finial, the empty perch swaying. The bars stand in the room, not on a card."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    t = getattr(deco, "t", 0.0)
    seed = getattr(deco, "seed", 0) or 0
    stand, bar, bar_dk = (70, 66, 60), (96, 90, 78), (60, 56, 48)
    post_h = 8 * s
    pygame.draw.line(surf, stand, cam.project(wx, wy, 0),
                     cam.project(wx, wy, post_h), max(2, int(2 * s)))
    _disc(surf, cam, wx, wy, 0.3, 4 * s, 4 * s, (40, 38, 36))          # foot
    R = 6 * s
    z_lo, z_hi = post_h, post_h + 16 * s
    _disc(surf, cam, wx, wy, z_lo, R, R, bar_dk, fill=False, width=2)  # base ring
    n = 10
    bars = sorted(range(n), key=lambda i: math.sin(i * math.tau / n))  # far first
    for i in bars:
        ang = i * math.tau / n
        bx, by = wx + math.cos(ang) * R, wy + math.sin(ang) * R
        col = bar if math.sin(ang) > -0.3 else bar_dk
        pygame.draw.line(surf, col, cam.project(bx, by, z_lo),
                         cam.project(bx, by, z_hi), 1)
    for rz, rr in ((z_hi, R), (z_hi + 2 * s, R * 0.78),                # stepped dome
                   (z_hi + 3.5 * s, R * 0.48)):
        _disc(surf, cam, wx, wy, rz, rr, rr, bar_dk, fill=False, width=1)
    fin = cam.project(wx, wy, z_hi + 5 * s)                            # finial
    pygame.draw.circle(surf, bar, (int(fin[0]), int(fin[1])), max(1, int(1.4 * s)))
    sway = math.sin(t * 0.9 + seed) * 1.2 * s                          # empty perch
    pygame.draw.line(surf, (84, 62, 40),
                     cam.project(wx - R * 0.6 + sway, wy, (z_lo + z_hi) / 2),
                     cam.project(wx + R * 0.6 + sway, wy, (z_lo + z_hi) / 2), 1)


def _draw_steeple_solid(surf, cam, deco):
    """The church bell-tower as a real tapered tower: a square shaft rising into
    a dark louvered belfry (a bell hung inside), a pyramidal spire cap, a
    crooked cross on top -- the one TALL thing for miles, a landmark that
    foreshortens + depth-sorts instead of swivelling to face the camera.

    `rise` (kwarg, world units) lifts the visible shaft base so the tower grows
    OUT OF the church roof: with a matching `depth_bias` (set at the placement)
    the tower sorts just after its own opaque roof and the belfry + spire read
    clearly above the roofline instead of being buried under it. `rise=0` (the
    default) grows a full tower from the ground for any free-standing use."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    seed = getattr(deco, "seed", 0) or 0
    rise = float(getattr(deco, "kwargs", {}).get("rise", 0.0)) * s
    lean = math.sin(seed) * 0.4 * s
    body = {"top": (86, 78, 66), "side": (70, 64, 54), "dark": (46, 42, 34)}
    TH = 40 * s                                    # tower height above the rise
    z0 = rise
    z_bel0, z_bel1 = rise + TH * 0.48, rise + TH * 0.72
    z_cap = rise + TH                              # spire base
    Wb, Wt = 7.5 * s, 5.5 * s

    def sq(hw, cx, cy, z):
        return [cam.project(cx - hw, cy - hw, z), cam.project(cx + hw, cy - hw, z),
                cam.project(cx + hw, cy + hw, z), cam.project(cx - hw, cy + hw, z)]
    b = sq(Wb, wx, wy, z0)
    tp = sq(Wt, wx + lean, wy, z_bel0)             # shaft up to the belfry
    pygame.draw.polygon(surf, body["top"], [b[0], b[1], tp[1], tp[0]])   # far (lit)
    pygame.draw.polygon(surf, body["side"], [b[0], b[3], tp[3], tp[0]])  # west
    pygame.draw.polygon(surf, body["side"], [b[1], b[2], tp[2], tp[1]])  # east
    pygame.draw.polygon(surf, body["dark"], [b[3], b[2], tp[2], tp[3]])  # near
    bel0 = sq(Wt * 1.04, wx + lean, wy, z_bel0)                          # belfry box
    bel1 = sq(Wt * 1.04, wx + lean, wy, z_bel1)
    pygame.draw.polygon(surf, (34, 30, 26), [bel0[0], bel0[1], bel1[1], bel1[0]])
    pygame.draw.polygon(surf, (24, 21, 18), [bel0[1], bel0[2], bel1[2], bel1[1]])
    pygame.draw.polygon(surf, (15, 13, 17), [bel0[3], bel0[2], bel1[2], bel1[3]])
    bl = cam.project(wx + lean, wy + Wt * 0.7, (z_bel0 + z_bel1) / 2)    # hung bell
    pygame.draw.circle(surf, (108, 92, 56), (int(bl[0]), int(bl[1])),
                       max(2, int(2.4 * s)))
    pygame.draw.circle(surf, (60, 50, 32), (int(bl[0]), int(bl[1])),
                       max(2, int(2.4 * s)), 1)
    apex = cam.project(wx + lean, wy, z_cap + 12 * s)                    # spire cap
    tc = sq(Wt, wx + lean, wy, z_bel1)
    pygame.draw.polygon(surf, (58, 44, 32), [tc[0], tc[1], apex])        # far
    pygame.draw.polygon(surf, (36, 28, 20), [tc[3], tc[2], apex])        # near
    pygame.draw.polygon(surf, (48, 36, 26), [tc[0], tc[3], apex])
    pygame.draw.polygon(surf, (48, 36, 26), [tc[1], tc[2], apex])
    cz = z_cap + 12 * s                                                  # crooked cross
    pygame.draw.line(surf, (52, 48, 40), cam.project(wx + lean, wy, cz),
                     cam.project(wx + lean, wy, cz + 8 * s), 2)
    pygame.draw.line(surf, (52, 48, 40),
                     cam.project(wx + lean - 3.5 * s, wy, cz + 5 * s),
                     cam.project(wx + lean + 3.5 * s, wy, cz + 5 * s), 2)


def _draw_lodge_gable_solid(surf, cam, deco):
    """The Arcadia's upper storey / loft, as a gabled dormer block rising above
    the main roofline so the hotel reads as two-storey (2026-07 expansion). A
    dark upper wall with a warm lit loft window, capped by a shingled gable.
    Like the steeple, `rise` lifts its base onto the roof and a matching
    `depth_bias` (set at placement) sorts it above the opaque roof."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    rise = float(getattr(deco, "kwargs", {}).get("rise", 0.0)) * s
    wall = {"top": (78, 60, 44), "side": (60, 46, 33), "dark": (42, 32, 23)}
    W, D = 34 * s, 15 * s
    z0, z1 = rise, rise + 16 * s                    # the upper-storey wall
    _vbox(surf, cam, wx, wy, W, D, z0, z1, wall)
    hw, hd = W / 2, D / 2
    peak = 13 * s
    ridge_f = cam.project(wx, wy - hd, z1 + peak)
    ridge_n = cam.project(wx, wy + hd, z1 + peak)
    fl, fr = cam.project(wx - hw, wy - hd, z1), cam.project(wx + hw, wy - hd, z1)
    nl, nr = cam.project(wx - hw, wy + hd, z1), cam.project(wx + hw, wy + hd, z1)
    # W + E roof slopes, then the near + far gable triangles
    pygame.draw.polygon(surf, (48, 37, 29), [nl, ridge_n, ridge_f, fl])   # W slope
    pygame.draw.polygon(surf, (66, 51, 39), [nr, ridge_n, ridge_f, fr])   # E slope
    pygame.draw.polygon(surf, (40, 31, 24), [fl, fr, ridge_f])            # far gable
    pygame.draw.polygon(surf, (56, 43, 33), [nl, nr, ridge_n])            # near gable
    pygame.draw.polygon(surf, (30, 23, 17), [nl, nr, ridge_n], 1)
    # the warm loft window on the near (south) face of the upper wall
    P = _vframe(cam, wx, wy, 0.0)
    win = [(-6 * s, hd, z0 + 4 * s), (6 * s, hd, z0 + 4 * s),
           (6 * s, hd, z1 - 2 * s), (-6 * s, hd, z1 - 2 * s)]
    _qp(surf, P, win, (198, 150, 74))
    _qp(surf, P, win, (46, 34, 22), w=1)
    _lp(surf, P, (0, hd, z0 + 4 * s), (0, hd, z1 - 2 * s), (46, 34, 22), 1)
    _lp(surf, P, (-6 * s, hd, (z0 + z1) / 2), (6 * s, hd, (z0 + z1) / 2),
        (46, 34, 22), 1)


def _draw_radio_solid(surf, cam, deco):
    """A radio as a small box volume: wood body, a dark speaker/dial face on the
    near side, the red tuning needle creeping. Lifts to `kwargs['z']` so a radio
    on a counter sits ON it (was a flat card pointing at the camera)."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    z0 = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    t = getattr(deco, "t", 0.0)
    body = {"top": (104, 72, 50), "side": (90, 60, 40), "dark": (66, 44, 28)}
    W, D, H = 20 * s, 10 * s, 10 * s
    _vbox(surf, cam, wx, wy, W, D, z0, z0 + H, body)
    P = _vframe(cam, wx, wy, 0.0)
    hD = D / 2
    _qp(surf, P, [(-8 * s, hD, z0 + 2 * s), (4 * s, hD, z0 + 2 * s),
                  (4 * s, hD, z0 + H - 2 * s), (-8 * s, hD, z0 + H - 2 * s)],
        (20, 18, 22))
    nx = -8 * s + (math.sin(t * 0.6) + 1) * 6 * s
    _lp(surf, P, (nx, hD, z0 + 2 * s), (nx, hD, z0 + H - 2 * s), (220, 60, 60), 1)


def _draw_wrong_radio_solid(surf, cam, deco):
    """The transistor radio nobody is touching, as a box volume: brown body, a
    static-crawling speaker grille + a chrome tuning dial whose needle creeps,
    the antenna raised, the carry strap slumped. Reads z for tabletop placement."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    z0 = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    t = getattr(deco, "t", 0.0)
    seed = getattr(deco, "seed", 0) or 0
    body = {"top": (104, 72, 50), "side": (90, 60, 40), "dark": (66, 44, 28)}
    W, D, H = 20 * s, 10 * s, 11 * s
    _vbox(surf, cam, wx, wy, W, D, z0, z0 + H, body)
    P = _vframe(cam, wx, wy, 0.0)
    hD = D / 2
    _qp(surf, P, [(-9 * s, hD, z0 + 2 * s), (-1 * s, hD, z0 + 2 * s),        # grille
                  (-1 * s, hD, z0 + H - 2 * s), (-9 * s, hD, z0 + H - 2 * s)],
        (20, 18, 22))
    for i in range(3):
        sz = z0 + 2 * s + (t * 6 + i * 3) % (H - 4 * s)
        _lp(surf, P, (-8.5 * s, hD, sz), (-1.5 * s, hD, sz), (110, 130, 110), 1)
    _qp(surf, P, [(1 * s, hD, z0 + 3 * s), (8 * s, hD, z0 + 3 * s),          # dial
                  (8 * s, hD, z0 + H - 3 * s), (1 * s, hD, z0 + H - 3 * s)],
        (20, 18, 22))
    nx = 1 * s + (math.sin(t * 0.4 + seed) + 1) * 3.4 * s
    _lp(surf, P, (nx, hD, z0 + 3 * s), (nx, hD, z0 + H - 3 * s), (220, 60, 60), 1)
    _lp(surf, P, (8 * s, hD, z0 + H), (12 * s, hD, z0 + H + 8 * s),          # antenna
        (180, 180, 200), 1)
    _lp(surf, P, (-W / 2, hD, z0 + H), (-W / 2 - 4 * s, hD, z0 + H * 0.4),   # strap
        (50, 32, 18), 1)


def _draw_church_bell_solid(surf, cam, deco):
    """The church bell hung in its hoist frame as real volume: two grounded
    uprights, the yoke beam across them, the aged-bronze bell swinging between
    (a pendulum lean while `ring_t` lives, dead-still at rest). Anchored, not a
    flat card standing on the floor."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    t = getattr(deco, "t", 0.0)
    ring = getattr(deco, "ring_t", 0.0)
    sway = 0.0
    if ring > 0.0:
        sway = math.sin(t * 5.4) * 3.0 * s * min(1.0, ring / 2.0)
    wood = {"top": (68, 54, 40), "side": (56, 44, 32), "dark": (34, 26, 20)}
    H = 26 * s
    for ox in (-11 * s, 11 * s):                        # two uprights
        _vbox(surf, cam, wx + ox, wy, 3 * s, 3 * s, 0, H, wood)
    _vbox(surf, cam, wx, wy, 26 * s, 3.5 * s, H, H + 4 * s, wood)   # yoke beam
    bronze = {"body": (118, 100, 62), "lo": (78, 66, 42), "rim": (178, 160, 108)}
    bz_bot, bz_top = H - 13 * s, H - 1 * s
    bx = wx + sway
    draw_solid(surf, cam, bx, wy,                       # bell (wide lip -> shoulder)
               [(bz_bot, 6.5 * s, 5.5 * s), (bz_bot + 3 * s, 5.5 * s, 4.6 * s),
                (bz_bot + 8 * s, 3.2 * s, 2.7 * s), (bz_top, 2.4 * s, 2.0 * s)],
               bronze)
    _disc(surf, cam, bx, wy, bz_bot, 6.5 * s, 5.5 * s, (178, 160, 108),
          fill=False, width=1)                          # bright lip
    cl = cam.project(bx, wy, bz_top)                    # crown loop
    pygame.draw.circle(surf, (78, 66, 42), (int(cl[0]), int(cl[1])),
                       max(1, int(1.6 * s)))


def _draw_valve_solid(surf, cam, deco):
    """The diggers' dewatering PITCHER PUMP as real volume: a driven pipe out of
    the ground, an iron pump body, the spout, the long wood-handled pump arm
    raised, the hose slumping to its basin. Kind name kept for the noise_source
    mechanic (matches entities/deco_mine `_draw_valve`)."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    iron = {"body": (58, 60, 64), "lo": (34, 36, 40), "rim": (96, 92, 84)}
    wood = (76, 58, 38)
    draw_solid(surf, cam, wx, wy,                       # driven standpipe
               [(0, 1.4 * s, 1.4 * s), (10 * s, 1.4 * s, 1.4 * s)], iron)
    _vbox(surf, cam, wx, wy, 5 * s, 4 * s, 10 * s, 18 * s,          # pump body
          {"top": (72, 74, 80), "side": (58, 60, 64), "dark": (34, 36, 40)})
    pygame.draw.lines(surf, iron["body"], False,        # spout, mouth down
                      [cam.project(wx + 2 * s, wy, 15 * s),
                       cam.project(wx + 6 * s, wy, 15 * s),
                       cam.project(wx + 7 * s, wy, 12 * s)], max(2, int(2 * s)))
    a0 = cam.project(wx, wy, 17 * s)                    # pump arm, raised
    pygame.draw.line(surf, iron["lo"], a0,
                     cam.project(wx - 8 * s, wy, 24 * s), max(2, int(2 * s)))
    pygame.draw.line(surf, wood, cam.project(wx - 7 * s, wy, 23 * s),
                     cam.project(wx - 12 * s, wy, 27 * s), max(3, int(3 * s)))
    pygame.draw.circle(surf, (96, 92, 84), (int(a0[0]), int(a0[1])),
                       max(1, int(1.4 * s)))
    pygame.draw.lines(surf, iron["lo"], False,          # hose slump
                      [cam.project(wx + 6 * s, wy, 10 * s),
                       cam.project(wx + 9 * s, wy + 3 * s, 4 * s),
                       cam.project(wx + 8 * s, wy + 5 * s, 0)], max(2, int(2 * s)))


def _draw_yard_light_solid(surf, cam, deco):
    """A rural dusk-to-dawn yard light: a tall wood pole, a downswept
    gooseneck arm, a shallow galvanized reflector hood, and a cold mercury-
    vapor lamp burning under it. The period-correct town light -- 1994
    northern Minnesota ran on these, not lanterns -- and its glow is COLD
    blue-white, the deliberate opposite of the warm fire the town huddles
    at (burn barrels, braziers, candles). Runs off the generators now the
    fold cut the grid (NARRATIVE §1)."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    wood = (74, 60, 44)
    wood_hi = (104, 86, 62)
    galv = (120, 122, 130)
    galv_lo = (70, 72, 80)
    pole_h = 46 * s
    base = cam.project(wx, wy, 0)
    top = cam.project(wx, wy, pole_h)
    pygame.draw.line(surf, wood, base, top, max(2, int(3 * s)))
    pygame.draw.line(surf, wood_hi, base, top, max(1, int(1 * s)))
    # a gooseneck arm: UP off the pole and OUT to one side (screen-relative to
    # the yaw, so the head stays anchored off the pole from any facing, never a
    # billboard), then a short drop to the lamp head
    arm_len = 13 * s
    ax = math.cos(cam.yaw + math.pi / 2)
    ay = math.sin(cam.yaw + math.pi / 2)
    hx = wx + ax * arm_len
    hy = wy + ay * arm_len
    hood_z = pole_h - 3 * s
    knee = cam.project(wx + ax * arm_len * 0.55,
                       wy + ay * arm_len * 0.55, pole_h + 2 * s)
    head_top = cam.project(hx, hy, hood_z + 3 * s)
    pygame.draw.line(surf, galv, top, knee, max(2, int(2 * s)))
    pygame.draw.line(surf, galv, knee, head_top, max(2, int(2 * s)))
    # the reflector hood: a taller galvanized DOME (a cone narrowing upward),
    # opening downward over the lamp -- reads as a hood, not a flat ring
    draw_solid(surf, cam, hx, hy,
               [(hood_z, 4.8 * s, 4.8 * s),
                (hood_z + 2.6 * s, 2.6 * s, 2.6 * s),
                (hood_z + 4.0 * s, 0.8 * s, 0.8 * s)],
               {"body": galv, "lo": galv_lo, "rim": (152, 154, 162)})
    # a photocell nub perched on top of the dome
    pc = cam.project(hx, hy, hood_z + 4.6 * s)
    pygame.draw.circle(surf, galv_lo, (int(pc[0]), int(pc[1])),
                       max(1, int(1.2 * s)))
    # a faint cold spill on the ground under the head (always on, so the
    # fixture reads as CASTING light even in daylight; the real navigable
    # pool is punched by _draw_dark when the scene is dark)
    _disc(surf, cam, hx, hy + 1.0 * s, 0.2 * s, 7.0 * s, 5.0 * s,
          (150, 176, 210))
    # the cold mercury-vapor lamp poking out the hood's lower FRONT lip
    lamp = cam.project(hx, hy + 3.0 * s, hood_z - 1.6 * s)
    lr = max(2, int(2.4 * s * cam.scale))
    glow = pygame.Surface((lr * 6, lr * 6), pygame.SRCALPHA)
    pygame.draw.circle(glow, (200, 224, 255, 60), (lr * 3, lr * 3), lr * 3)
    pygame.draw.circle(glow, (216, 232, 255, 120), (lr * 3, lr * 3), lr * 2)
    surf.blit(glow, (int(lamp[0] - lr * 3), int(lamp[1] - lr * 3)))
    pygame.draw.circle(surf, (232, 242, 255), (int(lamp[0]), int(lamp[1])), lr)
    pygame.draw.circle(surf, (255, 255, 255), (int(lamp[0]), int(lamp[1])),
                       max(1, lr // 2))


def _draw_generator_solid(surf, cam, deco):
    """A portable gas generator, tucked against a building's outside wall.
    The fold cut Brimley off the grid with everything else (NARRATIVE §1),
    so the town keeps its lights on off gasoline now: a low steel frame, a
    fuel tank slung on top, a control panel of outlets, a stub muffler, and
    a bare work-bulb clamped to the frame -- a small WARM light, the running
    tell. A DETAIL, kept small (it must sit OUTSIDE, so it fronts the doors)."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    t = getattr(deco, "t", 0.0)
    steel = {"top": (86, 84, 92), "side": (56, 54, 62), "dark": (34, 33, 40)}
    bw, bd, bh = 12 * s, 8 * s, 6 * s               # the engine frame
    draw_box(surf, cam, wx, wy, bw, bd, bh, steel)
    # fuel tank: a short upright canister on the frame's top
    tank = {"body": (120, 62, 46), "lo": (66, 34, 26), "rim": (150, 92, 70)}
    draw_solid(surf, cam, wx - 1.5 * s, wy,
               [(bh, 3.0 * s, 3.0 * s), (bh + 3.4 * s, 3.0 * s, 3.0 * s)], tank)
    # stub muffler canister on the frame's other end
    draw_solid(surf, cam, wx + bw * 0.34, wy,
               [(bh, 1.4 * s, 1.4 * s), (bh + 2.2 * s, 1.4 * s, 1.4 * s)],
               {"body": (52, 50, 54), "lo": (30, 28, 32), "rim": (80, 78, 82)})
    # control panel + two outlet dots on the near (south) face
    panel = cam.project(wx, wy + bd * 0.5, bh * 0.5)
    pw = max(2, int(3 * s * cam.scale))
    ph = max(2, int(2 * s * cam.scale))
    pygame.draw.rect(surf, (40, 40, 46),
                     (int(panel[0] - pw), int(panel[1] - ph), pw * 2, ph * 2))
    for ox in (-pw // 2, pw // 2):
        pygame.draw.circle(surf, (150, 150, 158),
                           (int(panel[0] + ox), int(panel[1])),
                           max(1, int(1 * s)))
    # a bare work-bulb clamped to the frame corner, warm, faintly wavering
    stalk_base = cam.project(wx + bw * 0.5, wy - bd * 0.3, bh)
    bl = cam.project(wx + bw * 0.5 + 1.5 * s, wy - bd * 0.3, bh + 2.4 * s)
    pygame.draw.line(surf, (70, 68, 74), stalk_base, bl, max(1, int(1 * s)))
    fl = 0.9 + 0.1 * math.sin(t * 5 + deco.seed)
    br = max(2, int(2.0 * s * cam.scale))
    glow = pygame.Surface((br * 6, br * 6), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 210, 150, int(70 * fl)),
                       (br * 3, br * 3), br * 3)
    surf.blit(glow, (int(bl[0] - br * 3), int(bl[1] - br * 3)))
    pygame.draw.circle(surf, (255, 224, 170), (int(bl[0]), int(bl[1])), br)


def draw_inner_door(surf, cam, wx, wy, ew, swing, kind="plank", seed=0):
    """An interior door leaf between two subrooms, swinging on its hinge from
    across-the-gap (swing 0, SHUT) to along-the-wall (swing 1, OPEN). `ew` =
    the door sits in an E-W wall (its opening faces N-S). Kinds: plank / bars
    (a see-through cell gate) / curtain (a drape) / half (a counter door).
    The collision + sight state lives on Scene._inner_doors; this only draws."""
    from scenes.base import _TILT_WALL_RISE
    leaf = 28.0
    thick = 4.0
    height = _TILT_WALL_RISE * (0.55 if kind == "half" else 0.9)
    if ew:                              # E-W wall: shut leaf lies along X
        hx, hy = wx - leaf / 2.0, wy
        ang = swing * (math.pi / 2.0)
    else:                              # N-S wall: shut leaf lies along Y
        hx, hy = wx, wy - leaf / 2.0
        ang = math.pi / 2.0 - swing * (math.pi / 2.0)
    ca, sa = math.cos(ang), math.sin(ang)
    bx, by = hx + (leaf / 2.0) * ca, hy + (leaf / 2.0) * sa
    if kind == "bars":
        iron = (58, 58, 66)
        # frame + a low rail, then vertical bars you see between
        rail = {"top": (46, 46, 52), "side": (30, 30, 36), "dark": (16, 16, 20)}
        draw_box(surf, cam, bx, by, leaf, thick, height * 0.12, rail, yaw=ang)
        top_rail = cam.project(hx + leaf * ca, hy + leaf * sa, height * 0.92)
        hinge_top = cam.project(hx, hy, height * 0.92)
        pygame.draw.line(surf, iron, hinge_top, top_rail, 2)
        for i in range(5):
            f = (i + 0.5) / 5.0
            gx, gy = hx + leaf * f * ca, hy + leaf * f * sa
            pygame.draw.line(surf, iron, cam.project(gx, gy, 0),
                             cam.project(gx, gy, height * 0.92), 2)
        return
    if kind == "curtain":
        pal = {"top": (104, 62, 60), "side": (78, 44, 44), "dark": (46, 26, 26)}
    else:
        pal = {"top": (98, 76, 50), "side": (68, 52, 34), "dark": (40, 30, 20)}
    draw_box(surf, cam, bx, by, leaf, thick, height, pal, yaw=ang)
    if kind == "plank":               # a couple seams + a knob
        for fz in (0.35, 0.68):
            a = cam.project(hx + leaf * 0.12 * ca, hy + leaf * 0.12 * sa,
                            height * fz)
            b = cam.project(hx + leaf * 0.88 * ca, hy + leaf * 0.88 * sa,
                            height * fz)
            pygame.draw.line(surf, (52, 40, 26), a, b, 1)
        knob = cam.project(hx + leaf * 0.82 * ca, hy + leaf * 0.82 * sa,
                           height * 0.5)
        pygame.draw.circle(surf, (156, 146, 96),
                           (int(knob[0]), int(knob[1])), max(1, 2))


def _draw_cash_register_solid(surf, cam, deco):
    """An old brass shop register: a shut cash drawer with a pull, a bank of
    round keys on the near face, and a tall amount-flag housing standing off the
    top with the pop-up number flags reading nothing behind its glass -- an
    empty till. The housing carries its identity from above the counter (the
    counter front hides the drawer/keys); lifts to `kwargs['z']` so it sits ON
    the counter ("Till's been empty since the new year" made an object; the
    walkable shop had none)."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    z0 = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    body = {"top": (132, 110, 64), "side": (100, 82, 48), "dark": (66, 54, 32)}
    draw = {"top": (90, 74, 42), "side": (68, 56, 32), "dark": (46, 38, 22)}
    W, D, H = 18 * s, 13 * s, 11 * s
    hD = D / 2
    _vbox(surf, cam, wx, wy, W, D, z0, z0 + 4 * s, draw)                 # drawer
    _vbox(surf, cam, wx, wy, W - 2 * s, D - 1.5 * s, z0 + 4 * s,
          z0 + H, body)                                                  # body
    P = _vframe(cam, wx, wy, 0.0)
    # the cash-drawer pull, low on the near face
    _lp(surf, P, (-4.5 * s, hD, z0 + 2 * s), (4.5 * s, hD, z0 + 2 * s),
        (208, 184, 120), 2)
    # the round key bank on the near face of the body (3 rows x 4)
    for kz in (z0 + 5.3 * s, z0 + 7.0 * s, z0 + 8.7 * s):
        for ci in range(4):
            px, py = P((-5.2 + ci * 3.4) * s, hD - 0.8 * s, kz)
            r = max(1, int(1.2 * s * cam.scale))
            pygame.draw.circle(surf, (202, 180, 122), (int(px), int(py)), r)
            pygame.draw.circle(surf, (72, 60, 36), (int(px), int(py)), r, 1)
    # the amount-flag housing: a prominent box standing off the top, the read
    # from above the counter. Sits at the back so the sloped keys front it.
    fy = wy - (hD - 2.2 * s)
    fz0, fz1 = z0 + H, z0 + H + 9 * s
    _vbox(surf, cam, wx, fy, 14 * s, 4 * s, fz0, fz1, body)              # housing
    Pf = _vframe(cam, wx, fy, 0.0)
    fd = 2 * s
    _qp(surf, Pf, [(-5.6 * s, fd, fz0 + 1.6 * s), (5.6 * s, fd, fz0 + 1.6 * s),
                   (5.6 * s, fd, fz1 - 1.6 * s), (-5.6 * s, fd, fz1 - 1.6 * s)],
        (24, 22, 20))                                                    # glass
    # the pop-up number flags behind the glass, blank (an empty sale)
    for dx in (-3.4 * s, -0.4 * s, 2.6 * s):
        dp = Pf(dx, fd, fz0 + 4.6 * s)
        pygame.draw.rect(surf, (156, 152, 138),
                         (int(dp[0]) - 1, int(dp[1]) - 4,
                          max(2, int(2.2 * s)), max(4, int(5 * s))))
    # a brass crest bead along the top of the housing
    _lp(surf, Pf, (-5.6 * s, fd, fz1 - 0.6 * s), (5.6 * s, fd, fz1 - 0.6 * s),
        (196, 172, 112), max(1, int(1.4 * s)))


def _draw_bill_spike_solid(surf, cam, deco):
    """A receipt spike: a weighted base, a thin steel needle, and a fan of
    impaled paper slips crowding the upper half (Mara's tab, the one Hettie
    works off the spike). Lifts to `kwargs['z']` for the counter."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    z0 = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    base = {"top": (96, 96, 104), "side": (70, 70, 78), "dark": (48, 48, 56)}
    _vbox(surf, cam, wx, wy, 7 * s, 6 * s, z0, z0 + 2 * s, base)         # base
    P = _vframe(cam, wx, wy, 0.0)
    tip = z0 + 13 * s
    _lp(surf, P, (0, 0, z0 + 2 * s), (0, 0, tip), (176, 178, 188),
        max(1, int(1.2 * s)))                                           # needle
    # the impaled slips, a curling fan up the needle
    for ox, oz, pw, col in ((-3.2 * s, tip - 6.5 * s, 6, (176, 168, 148)),
                            (2.6 * s, tip - 5.0 * s, 5, (162, 154, 134)),
                            (-2.4 * s, tip - 3.4 * s, 5, (178, 170, 150)),
                            (1.6 * s, tip - 2.0 * s, 4, (166, 158, 138))):
        a = P(ox, 0.4 * s, oz)
        b = P(ox * 0.25, 0.4 * s, oz + 1.8 * s)
        pygame.draw.line(surf, col, (int(a[0]), int(a[1])),
                         (int(b[0]), int(b[1])), max(2, int(pw * 0.55 * s)))


def _draw_altar_mask_solid(surf, cam, deco):
    """The Pallid Mask resting on the cult's altar, face-out to the kneeling: a
    pale drowned face, black eye sockets each holding a warm gold ember (it
    knows your hands). A flat object shown to the congregation, so it faces
    south by design (NARRATIVE 6a); a soft warm underglow. Lifts to kwargs['z']
    (the pedestal cap); the scene drops it once the Mask is taken."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    z0 = float(getattr(deco, "kwargs", {}).get("z", 18.0))
    t = getattr(deco, "t", 0.0)
    seed = getattr(deco, "seed", 0) or 0
    hw, hh = 4.2 * s, 5.4 * s
    fy = 5.5 * s                       # forward (south), the front of the cap
    zc = z0 + hh + 1.5 * s             # mask centre height
    gx, gy = cam.project(wx, wy + fy, zc)
    gw = max(2, int(hw * cam.scale * 1.6)); gh = max(2, int(hh * cam.scale * 1.6))
    glow = pygame.Surface((gw * 2 + 2, gh * 2 + 2), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (150, 118, 66, 66), (1, 1, gw * 2, gh * 2))
    surf.blit(glow, (int(gx) - gw - 1, int(gy) - gh - 1),
              special_flags=pygame.BLEND_RGB_ADD)
    pts = []
    for i in range(16):
        a = i / 16.0 * 2 * math.pi
        pts.append(cam.project(wx + math.cos(a) * hw, wy + fy,
                               zc + math.sin(a) * hh))
    ipts = [(int(px), int(py)) for px, py in pts]
    pygame.draw.polygon(surf, (204, 200, 192), ipts)
    pygame.draw.polygon(surf, (150, 148, 142), ipts, 1)
    n0 = cam.project(wx, wy + fy, zc + 1.0 * s)
    n1 = cam.project(wx, wy + fy, zc - 2.2 * s)
    pygame.draw.line(surf, (172, 168, 160), (int(n0[0]), int(n0[1])),
                     (int(n1[0]), int(n1[1])), 1)
    ember = 0.55 + 0.45 * math.sin(t * 1.6 + seed)
    for ex in (-1.9 * s, 1.9 * s):
        sk = cam.project(wx + ex, wy + fy, zc + 1.4 * s)
        pygame.draw.circle(surf, (10, 9, 11), (int(sk[0]), int(sk[1])),
                           max(1, int(1.4 * s * cam.scale)))
        eg = cam.project(wx + ex, wy + fy, zc + 0.6 * s)
        ec = (int(120 + 90 * ember), int(70 + 46 * ember), 30)
        pygame.draw.circle(surf, ec, (int(eg[0]), int(eg[1])),
                           max(1, int(0.7 * s * cam.scale)))


def _draw_crayons_solid(surf, cam, deco):
    """A child's crayons and a half-drawn sheet on the table: a pale sheet with
    a couple of crude crayon strokes, and several short colored crayon sticks
    scattered beside it. Lifts to kwargs['z'] for the tabletop (Toby's table)."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    z0 = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    P = _vframe(cam, wx, wy, 0.0)
    zsheet = z0 + 0.4 * s
    _qp(surf, P, [(-8 * s, 6 * s, zsheet), (4 * s, 6 * s, zsheet),
                  (4 * s, -6 * s, zsheet), (-8 * s, -6 * s, zsheet)],
        (208, 202, 186))                                          # sheet
    # a couple crude crayon strokes on the sheet (a sun, a stroke)
    sc0 = P(-2 * s, 2 * s, zsheet + 0.1 * s)
    pygame.draw.circle(surf, (228, 198, 82), (int(sc0[0]), int(sc0[1])),
                       max(1, int(1.6 * s)))
    a = P(-6 * s, -3 * s, zsheet + 0.1 * s); b = P(1 * s, -3 * s, zsheet + 0.1 * s)
    pygame.draw.line(surf, (90, 170, 90), (int(a[0]), int(a[1])),
                     (int(b[0]), int(b[1])), max(1, int(1.4 * s)))
    # the crayon sticks scattered beside the sheet, short low colored cylinders
    for ox, oy, col in ((7 * s, 4 * s, (200, 70, 60)), (8.5 * s, 1.5 * s, (70, 120, 200)),
                        (6.5 * s, -1.5 * s, (90, 180, 90)), (9 * s, -4 * s, (230, 200, 80)),
                        (7.5 * s, -6 * s, (180, 90, 180))):
        ca = P(ox, oy, z0 + 0.8 * s); cb = P(ox + 3.4 * s, oy - 0.8 * s, z0 + 0.8 * s)
        pygame.draw.line(surf, col, (int(ca[0]), int(ca[1])),
                         (int(cb[0]), int(cb[1])), max(2, int(1.8 * s)))


def _draw_service_bell_solid(surf, cam, deco):
    """A brass reception service bell: a domed bell on a round base with a small
    press button on top. Lifts to kwargs['z'] for the desk. Sable's tableau
    keeps one on the register; the walkable desk had none."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    z0 = float(getattr(deco, "kwargs", {}).get("z", 0.0))
    brass = {"body": (150, 128, 74), "lo": (104, 86, 48), "rim": (198, 174, 112)}
    draw_solid(surf, cam, wx, wy, [
        (z0 + 0.0, 5.0 * s, 4.2 * s),        # base disc
        (z0 + 1.3 * s, 4.5 * s, 3.7 * s),
        (z0 + 2.1 * s, 4.8 * s, 4.0 * s),    # dome shoulder
        (z0 + 4.2 * s, 3.3 * s, 2.7 * s),
        (z0 + 5.6 * s, 1.5 * s, 1.2 * s),
        (z0 + 6.2 * s, 0.9 * s, 0.8 * s),    # cap
    ], brass)
    P = _vframe(cam, wx, wy, 0.0)
    st = P(0, 0, z0 + 6.2 * s)
    b = P(0, 0, z0 + 7.5 * s)
    pygame.draw.line(surf, (120, 100, 58), (int(st[0]), int(st[1])),
                     (int(b[0]), int(b[1])), max(1, int(1.2 * s)))
    pygame.draw.circle(surf, (208, 186, 124), (int(b[0]), int(b[1])),
                       max(1, int(1.4 * s)))


def _draw_lectern_solid(surf, cam, deco):
    """A church reading lectern: a narrow dark-wood column on a foot, a small
    brass cross on the front, and the open book on a board slanted toward the
    nave (near edge low, far edge high, so the camera looks down onto the pale
    pages). The preacher's whole seat, the centrepiece of his tableau -- the
    walkable church had only a bare altar table."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    wood = {"top": (80, 60, 40), "side": (60, 44, 30), "dark": (40, 30, 20)}
    _vbox(surf, cam, wx, wy, 12 * s, 11 * s, 0, 2.5 * s, wood)      # foot
    _vbox(surf, cam, wx, wy, 7 * s, 7 * s, 2.5 * s, 16 * s, wood)   # column
    P = _vframe(cam, wx, wy, 0.0)
    # a small brass cross on the front (south) face of the column
    cz = 9 * s
    _lp(surf, P, (0, 3.5 * s, cz - 2.6 * s), (0, 3.5 * s, cz + 2.6 * s),
        (178, 154, 98), max(1, int(1.5 * s)))
    _lp(surf, P, (-1.9 * s, 3.5 * s, cz + 0.9 * s), (1.9 * s, 3.5 * s, cz + 0.9 * s),
        (178, 154, 98), max(1, int(1.5 * s)))
    # the slanted book board: near (south) edge low, far (north) edge high
    zlo, zhi = 16 * s, 20.5 * s
    _qp(surf, P, [(-7 * s, 5 * s, zlo), (7 * s, 5 * s, zlo),
                  (7 * s, -5 * s, zhi), (-7 * s, -5 * s, zhi)], wood["dark"])
    # the open book on the board: two pale pages, a dark gutter, faint text
    _qp(surf, P, [(-6 * s, 4 * s, zlo + 0.5 * s), (6 * s, 4 * s, zlo + 0.5 * s),
                  (6 * s, -4 * s, zhi - 0.5 * s), (-6 * s, -4 * s, zhi - 0.5 * s)],
        (198, 190, 170))
    _lp(surf, P, (0, 4 * s, zlo + 0.5 * s), (0, -4 * s, zhi - 0.5 * s),
        (118, 110, 94), max(1, int(1.3 * s)))
    for lx in (-3 * s, 3 * s):
        _lp(surf, P, (lx, 2.6 * s, zlo + 1.5 * s), (lx, -2.6 * s, zhi - 1.5 * s),
            (150, 142, 124), 1)


def _draw_bell_stock_solid(surf, cam, deco):
    """The church bell's timber BELL-STOCK: a braced trestle -- four canted
    posts rising to a HEADSTOCK beam the bell's gudgeons ride in, tied by a
    mid-height ledger RING and diagonal knee braces on every face. Carries
    horizontal members in BOTH planes (E-W ties + N-S ties, an E-W headstock
    + N-S top caps) so it reads as a bell frame from ALL FOUR facings, not
    just broadside (2026-07 fix: the first build ran every beam E-W, so it
    was planar in X and collapsed to a thin stick when viewed edge-on from
    E/W -- a defect a genuine four-facing check surfaces). The church_bell
    hangs off the headstock centre."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    wood = {"top": (108, 84, 55), "side": (82, 62, 41), "dark": (56, 42, 28)}
    wood2 = {"top": (95, 73, 48), "side": (71, 53, 35), "dark": (47, 36, 24)}
    H = 46 * s          # post height to the headstock
    c = 15 * s          # half-footprint (posts near the 2x2 corners)
    post = 4.2 * s
    tie = 2.6 * s       # ledger-tie thickness
    span = c * 2 + post
    # four corner posts, canted very slightly inward (base out at +-c, so the
    # trestle reads as splayed legs, not a table's straight legs)
    corners = ((-c, -c, wood), (c, -c, wood2), (-c, c, wood2), (c, c, wood))
    for (px, py, pal) in corners:
        _vbox(surf, cam, wx + px, wy + py, post, post, 0, H, pal, outline=False)
    # a mid-height ledger RING joining the posts on ALL FOUR sides -- so a
    # horizontal member reads in both planes (the anti-thin fix): E-W ties at
    # front + back, N-S ties at left + right.
    zt0, zt1 = H * 0.44, H * 0.44 + 3 * s
    for py in (-c, c):                       # E-W ties (broadside from N/S)
        _vbox(surf, cam, wx, wy + py, span, tie, zt0, zt1, wood2, outline=False)
    for px in (-c, c):                       # N-S ties (broadside from E/W)
        _vbox(surf, cam, wx + px, wy, tie, span, zt0, zt1, wood2, outline=False)
    # diagonal KNEE braces from every corner post up under the headstock (they
    # cant inward in BOTH x and y, so a brace shows on every facing)
    for px in (-c, c):
        for py in (-c, c):
            a = cam.project(wx + px, wy + py, H * 0.40)
            b = cam.project(wx + px * 0.28, wy + py * 0.55, H)
            pygame.draw.line(surf, wood["dark"], a, b, max(1, int(2 * s)))
    # N-S top caps at the ends (broadside from E/W) so the TOP of the frame
    # reads edge-on too, then the stouter E-W HEADSTOCK across the centre (the
    # bell's pivot), drawn last so it sits highest.
    for px in (-c, c):
        _vbox(surf, cam, wx + px, wy, tie + 1 * s, span, H, H + 4.0 * s,
              wood2, outline=False)
    _vbox(surf, cam, wx, wy, span + 5 * s, 6.0 * s, H, H + 6.0 * s, wood)
    # the two iron gudgeon straps the bell's cannons ride in, under the beam
    for px in (-4 * s, 4 * s):
        g0 = cam.project(wx + px, wy - 3 * s, H)
        g1 = cam.project(wx + px, wy - 3 * s, H - 4 * s)
        pygame.draw.line(surf, (40, 38, 40), g0, g1, max(1, int(1.6 * s)))


SOLID_PROPS = {
    "bell_stock":    _draw_bell_stock_solid,
    "doorframe":     _draw_doorframe_solid,
    "waterfall":     _draw_waterfall_solid,
    "shaft_ladder":  _draw_shaft_ladder_solid,
    "staircase":     _draw_staircase_solid,
    "cellar_hatch":  _draw_cellar_hatch_solid,
    "kitchen_wall":  _draw_kitchen_wall_solid,
    "dining_set":    _draw_dining_set_solid,
    "bar_dressing":  _draw_bar_dressing_solid,
    "hill_cap":      _draw_hill_cap_solid,
    "well":          _draw_well_solid,
    "headstone":     _draw_headstone_solid,
    "town_sign":     _draw_town_sign_solid,
    "flagpole":      _draw_flagpole_solid,
    "pillar":        _draw_pillar_solid,
    "cistern_basin": _draw_cistern_basin_solid,
    "grain_heap":    _draw_grain_heap_solid,
    # the mine art pass (2026-07): the dig's own furniture
    "spoil_heap":    _draw_spoil_heap_solid,
    "shoring_frame": _draw_shoring_frame_solid,
    "ore_cart":      _draw_ore_cart_solid,
    "player_car":    _draw_car_solid,
    "pickup_truck":  _draw_pickup_truck_solid,
    "rust_sedan":    _draw_rust_sedan_solid,
    "rust_wagon":    _draw_rust_wagon_solid,
    "rust_coupe":    _draw_rust_coupe_solid,
    "rust_van":      _draw_rust_van_solid,
    "burn_barrel":   _draw_burn_barrel_solid,
    "camp_fire":     _draw_camp_fire_solid,
    "news_rack":     _draw_news_rack_solid,
    "stalagmite":    _draw_stalagmite_solid,
    # anchored volumes (the sprite-depth-anchoring pass): props that used to
    # draw as flat camera-facing cards / stickers under tilt
    "standing_stone": _draw_standing_stone_solid,
    "wheelbarrow":    _draw_wheelbarrow_solid,
    "pedestal":       _draw_pedestal_solid,
    "corn_altar":     _draw_corn_altar_solid,
    "butter_churn":   _draw_butter_churn_solid,
    "washstand":      _draw_washstand_solid,
    "birdcage":       _draw_birdcage_solid,
    "steeple":        _draw_steeple_solid,
    "lodge_gable":    _draw_lodge_gable_solid,
    "radio":          _draw_radio_solid,
    "wrong_radio":    _draw_wrong_radio_solid,
    "cash_register":  _draw_cash_register_solid,
    "bill_spike":     _draw_bill_spike_solid,
    "service_bell":   _draw_service_bell_solid,
    "crayons":        _draw_crayons_solid,
    "altar_mask":     _draw_altar_mask_solid,
    "lectern":        _draw_lectern_solid,
    "church_bell":    _draw_church_bell_solid,
    "valve":          _draw_valve_solid,
    "candle":        _draw_candle_solid,
    "kerosene_lamp": _draw_kerosene_lamp_solid,
    "lantern":       _draw_lantern_solid,
    "yard_light":    _draw_yard_light_solid,
    "generator":     _draw_generator_solid,
    "brazier":       _draw_brazier_solid,
    "wall_torch":    _draw_wall_torch_solid,
    "wall_lamp":     _draw_wall_lamp_solid,
    "smoke":         _draw_smoke_solid,
    "wisp":          _draw_wisp_solid,
    "rope":          _draw_rope_solid,
    "stalk_marker":  _draw_stalk_marker_solid,
    "mote":          _draw_mote_solid,
    "flock":         _draw_flock_solid,
    "crow":          _draw_crow_solid,
}


# -- Standees: stand authored 2D elevation art UP on the floor -------------
# Props whose `_draw_<kind>` art in entities/decoration.py is a side-on
# ELEVATION (a thing seen standing, base at the anchor) -- trees, effigies,
# signs. Under tilt these used to blit FLAT at the
# projected point, reading as a top-down sticker lying in a tilted world. We
# now render that same authored art onto a card cropped to its silhouette and
# stand it up GROUNDED, depth-sorted + occluding alongside the walls (the same
# language as the object-map tree standees). The flat pitch-0 view still draws
# the 2D sprite via Scene.draw, so it stays byte-identical. `hanging_figure`
# hangs instead: its card is hung from a mount height so the body dangles.
_STANDEE_HANG = frozenset(("hanging_figure",))
# corn_altar / standing_stone / wheelbarrow / pedestal / steeple were promoted
# from flat standee cards to anchored SOLID_PROPS volumes (the sprite-depth-
# anchoring pass); town_sign / flagpole already draw as solids. What remains
# here is genuinely organic (trees, grass, corn-husk effigies) or too slight to
# volumize (the doll), where a stood-up card is the right read.
_STANDEE_GROUND = frozenset((
    "creepy_tree", "corn_doll", "tall_grass", "grass_tuft", "doll",
    "husk_bundle",
))
_STANDEE_KINDS = _STANDEE_GROUND | _STANDEE_HANG
_STANDEE_HANG_MOUNT = 34          # world height the hanging card is hung from
_STANDEE_CARD_CACHE = {}          # (kind, seed, scale) -> cropped card | False


def _standee_card(deco):
    """The decoration's own 2D elevation art rendered to a card cropped to its
    silhouette, cached per (kind, seed, scale). Animation is frozen at t=0 (a
    standee is a static occluder, like the cached tree cards). Returns the card
    Surface, or None if the art is empty / missing."""
    s = round(getattr(deco, "scale", 1.0) or 1.0, 2)
    key = (deco.kind, deco.seed, s)
    card = _STANDEE_CARD_CACHE.get(key)
    if card is None:
        fn = getattr(deco, f"_draw_{deco.kind}", None)
        if fn is None:
            _STANDEE_CARD_CACHE[key] = False
            return None
        C = 128
        big = pygame.Surface((C, C), pygame.SRCALPHA)
        t0 = deco.t
        deco.t = 0.0
        try:
            fn(big, C // 2, C // 2)
        except Exception:
            _STANDEE_CARD_CACHE[key] = False
            return None
        finally:
            deco.t = t0
        rect = big.get_bounding_rect()
        if not rect.width or not rect.height:
            _STANDEE_CARD_CACHE[key] = False
            return None
        card = big.subsurface(rect).copy()
        if s != 1.0:
            card = pygame.transform.smoothscale(
                card, (max(1, int(card.get_width() * s)),
                       max(1, int(card.get_height() * s))))
        _STANDEE_CARD_CACHE[key] = card
    return card or None


def draw_standee(surf, cam, deco):
    """Stand the decoration's elevation card up on the floor (or hang it).
    Returns True if it was a standee kind (and drawn)."""
    card = _standee_card(deco)
    if card is None:
        return False
    if deco.kind in _STANDEE_HANG:
        sw = card.get_width()
        tx, ty = cam.project(deco.x, deco.y, _STANDEE_HANG_MOUNT)
        surf.blit(card, (int(tx - sw / 2), int(ty)))
    else:
        draw_billboard(surf, cam, deco.x, deco.y, card, h_anchor=1.0)
    return True


def is_solid_prop(kind):
    """A decoration that, under tilt, draws as world-oriented geometry (a
    body-of-revolution solid OR a grounded standee) instead of a flat top-down
    sticker. Both route through draw_prop_solid + the unified depth pass."""
    return kind in SOLID_PROPS or kind in _STANDEE_KINDS


def draw_prop_solid(surf, cam, deco):
    """Draw one decoration as a volumetric body-of-revolution prop or a grounded
    standee. Returns True if it was a known solid/standee (and drawn), False
    otherwise so the caller can fall back."""
    fn = SOLID_PROPS.get(deco.kind)
    if fn is not None:
        fn(surf, cam, deco)
        return True
    if deco.kind in _STANDEE_KINDS:
        return draw_standee(surf, cam, deco)
    return False
