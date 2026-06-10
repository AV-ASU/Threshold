"""Volumetric NON-box props for the oblique camera (CAMERA.md Phase 4 dress).

rendering/furniture.py turns upright furniture into axis-aligned BOXES. This is
its sibling for the shapes a box can't express -- bodies of revolution: the
**well** (a round stone drum with a winch gallows), stone **pillars**, cistern
**basins** brimming with black water, and raked **grain heaps**. Each is keyed
by decoration `kind`, drawn through the same Camera in the tilt path (depth
sorted alongside furniture). The flat top-down game (F3) never calls this -- it
falls back to the 2D `_draw_<kind>` sprites in entities/decoration.py.
"""
import math
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
    # Board: a thin plank box at z = POST_H * 0.55 .. * 0.85
    BOARD_Z0 = POST_H * 0.55
    BOARD_Z1 = POST_H * 0.95
    BOARD_W = 14 * s
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
        font_h = max(7, int(7 * s * cam.scale))
        font = pygame.font.SysFont(None, font_h, bold=True)
        txt = font.render(text, True, (28, 18, 8))
        tcx = int((bb[0][0] + bb[1][0]) / 2)
        tcy = int((bb[0][1] + bt[1][1]) / 2)
        surf.blit(txt, (tcx - txt.get_width() // 2,
                        tcy - txt.get_height() // 2))
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
    """A raked cone of tithed grain, the dark of old blood pooled at its base."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    R = 15 * s
    H = 13 * s
    pal = {"body": (150, 126, 70), "lo": (80, 64, 35), "rim": (198, 174, 110)}
    draw_solid(surf, cam, wx, wy,
               [(0, R, R), (H * 0.6, R * 0.6, R * 0.6),
                (H, R * 0.12, R * 0.12)], pal)
    _disc(surf, cam, wx, wy, 0.5, R * 0.96, R * 0.96, (60, 30, 28),
          fill=False, width=2)


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


def _draw_waterfall_solid(surf, cam, deco):
    """A spring gushing from a HOLE in the cave cliff and falling into the river
    -- the visible mouth of the artery (NARRATIVE 1b). A dark source recess
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
    """THE THRESHOLD (NARRATIVE 1b): a plain, blank, unmarked frame -- 'about the
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
    climbing, frayed where it coils on the floor. (Flat F3 uses the 2D sprite.)"""
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


def _draw_cellar_hatch_solid(surf, cam, deco):
    """A timber cellar hatch with real volume: a low raised plank box on the
    floor (not a flat decal), cross-boarded and nailed shut, an iron pull-ring
    on top. (Flat F3 uses the 2D sprite.)"""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    w, d, rim = 26 * s, 24 * s, 6 * s
    pal = {"top": (120, 86, 50), "side": (84, 58, 34), "dark": (58, 40, 22)}
    _vbox(surf, cam, wx, wy, w, d, 0, rim, pal)
    hw, hd = w / 2, d / 2
    tl, tr = cam.project(wx - hw, wy - hd, rim), cam.project(wx + hw, wy - hd, rim)
    bl, br = cam.project(wx - hw, wy + hd, rim), cam.project(wx + hw, wy + hd, rim)
    # plank seams + the cross-boards nailed over the lid (shut)
    for f in (0.33, 0.66):
        a = (tl[0] + (bl[0] - tl[0]) * f, tl[1] + (bl[1] - tl[1]) * f)
        b = (tr[0] + (br[0] - tr[0]) * f, tr[1] + (br[1] - tr[1]) * f)
        pygame.draw.line(surf, pal["dark"], a, b, 1)
    pygame.draw.line(surf, _shade(pal["top"], 1.1), tl, br, max(2, int(2 * s)))
    pygame.draw.line(surf, _shade(pal["top"], 1.1), tr, bl, max(2, int(2 * s)))
    for c in (tl, tr, bl, br):                                  # nail heads
        pygame.draw.circle(surf, (54, 52, 58), (int(c[0]), int(c[1])), max(1, int(1.5 * s)))
    ring = cam.project(wx, wy, rim)                             # iron pull-ring
    pygame.draw.circle(surf, (176, 176, 196), (int(ring[0]), int(ring[1])),
                       max(2, int(4 * s)), 2)


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


SOLID_PROPS = {
    "doorframe":     _draw_doorframe_solid,
    "waterfall":     _draw_waterfall_solid,
    "shaft_ladder":  _draw_shaft_ladder_solid,
    "cellar_hatch":  _draw_cellar_hatch_solid,
    "well":          _draw_well_solid,
    "headstone":     _draw_headstone_solid,
    "town_sign":     _draw_town_sign_solid,
    "flagpole":      _draw_flagpole_solid,
    "pillar":        _draw_pillar_solid,
    "cistern_basin": _draw_cistern_basin_solid,
    "grain_heap":    _draw_grain_heap_solid,
    "player_car":    _draw_car_solid,
    "pickup_truck":  _draw_pickup_truck_solid,
    "stalagmite":    _draw_stalagmite_solid,
    "candle":        _draw_candle_solid,
    "kerosene_lamp": _draw_kerosene_lamp_solid,
    "lantern":       _draw_lantern_solid,
    "brazier":       _draw_brazier_solid,
    "wall_torch":    _draw_wall_torch_solid,
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
_STANDEE_GROUND = frozenset((
    "creepy_tree", "corn_doll", "corn_altar",
    "wheelbarrow", "pedestal", "steeple", "town_sign", "flagpole",
    "tall_grass", "grass_tuft", "doll", "husk_bundle",
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
