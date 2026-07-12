"""Ground heightfield -- blind-spot hills (DESIGN.md §10).

The camera already carries a real height axis (`Camera.project(wx, wy, wz)`,
z rises by sin(pitch)); the simulation stays flat XY. A scene may opt in to a
per-tile ground height so the floor ROLLS under the tilt camera and a crest you
cannot see over occludes what is beyond it -- the same dread primitive as a
wall, landing directly on the shipped blind-spot vision (`rendering/sight.py`).

Two pieces live here:
  * `build_heightfield(w, h, bumps)` -- the _flood-style authoring helper: hand
    it tile-space radial bumps, get back the (h x w) float grid a scene attaches
    via `Scene.set_ground`. Cosine falloff so crests are rounded, not conical.
  * `draw_ground_mesh(surf, camera, scene)` -- draws the authored region as a
    projected floor MESH layered over the flat affine floor, so the ground
    visibly swells and actors standing on it (lifted by `Scene.ground_z`) sit on
    the surface instead of floating. TILT ONLY -- a strict no-op at pitch 0 and
    on any scene without a heightfield, so the byte-identity gate is untouched.

Movement stays 2D; height is a passive READ used for draw + sight only. AI and
pathing ignore height in v1 (cosmetic + sight-only), by design.
"""
import math

import pygame

from constants import TILE


def build_heightfield(w, h, bumps):
    """Build an (h x w) float grid of ground heights (world z, px) from a list
    of smooth radial bumps. Each bump is (cx, cy, radius_tiles, peak) in TILE
    coordinates; overlapping bumps take the max (hills merge, they don't stack).
    Cosine falloff -> a rounded crest that eases to 0 at the rim.

    Mirrors the `_flood` ergonomics: author with tile coords, get back a grid to
    hand to `Scene.set_ground`. Returns None if there are no bumps (so a caller
    can pass an empty list and stay dead-flat)."""
    if not bumps:
        return None
    grid = [[0.0] * w for _ in range(h)]
    for cx, cy, rad, peak in bumps:
        if rad <= 0:
            continue
        x0 = max(0, int(math.floor(cx - rad)))
        x1 = min(w - 1, int(math.ceil(cx + rad)))
        y0 = max(0, int(math.floor(cy - rad)))
        y1 = min(h - 1, int(math.ceil(cy + rad)))
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                dist = math.hypot(tx - cx, ty - cy)
                if dist >= rad:
                    continue
                z = peak * (0.5 + 0.5 * math.cos(math.pi * dist / rad))
                if z > grid[ty][tx]:
                    grid[ty][tx] = z
    return grid


def carve_channel(w, h, centerline, half_width, depth, grid=None):
    """Carve a river TROUGH into a heightfield: for each tile within
    `half_width` tiles of the centerline, sink the ground toward -`depth` (world
    z, px) at the channel axis, easing back to grade (0) at the rim (cosine).
    `centerline` is a list of (cx, cy) tile points -- the river's path; the
    trough is the union of the perpendicular cuts along it, so a bent river bends
    its banks. The carve takes the MIN, so it deepens an existing grid (banks
    from build_heightfield + a channel cut) instead of fighting it.

    The rim (z 0) meets the surrounding flat floor continuously; the bed sits at
    -depth, so a figure in the channel is below the bank crest and the crest
    occludes the bank tops from them (and them from the bank), which is exactly
    the sight-pit the WADE water routing wants. Pair with `~` water chars on the
    bed tiles so the mesh shades the trough wet."""
    grid = grid if grid is not None else [[0.0] * w for _ in range(h)]
    if half_width <= 0:
        return grid
    for cx, cy in centerline:
        x0 = max(0, int(math.floor(cx - half_width)))
        x1 = min(w - 1, int(math.ceil(cx + half_width)))
        y0 = max(0, int(math.floor(cy - half_width)))
        y1 = min(h - 1, int(math.ceil(cy + half_width)))
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                dist = math.hypot(tx - cx, ty - cy)
                if dist >= half_width:
                    continue
                z = -depth * (0.5 + 0.5 * math.cos(math.pi * dist / half_width))
                if z < grid[ty][tx]:
                    grid[ty][tx] = z
    return grid


# Earth-tone ramp the swell shades along: the mound reads by its LIGHT (a lit
# crown falling to a shadowed far flank), so the two ends are pulled far enough
# apart to read against the dark floor without looking like a foreign patch.
_MESH_LIT = (96, 88, 66)
_MESH_DARK = (20, 19, 15)
# Cold, near-black water ramp for a sunken channel bed: the wet trough reads by
# the same Lambert as the earth, just pulled to a drowned blue-grey so a river
# cut into the ground looks wet, not muddy.
_WATER_LIT = (44, 62, 74)
_WATER_DARK = (10, 16, 22)
# Fixed light: from the upper-left, a touch above the horizon. Slopes facing it
# catch light, the far flank falls to shadow -- the cue that reads as 3D form.
_LIGHT = (-0.42, -0.55, 0.72)


def _shade(nx, ny, nz, lit=_MESH_LIT, dark=_MESH_DARK):
    """Directional Lambert for a ground face with (approx, un-normalised)
    surface normal (nx, ny, nz). Bright where the slope faces the light, dark on
    the far flank -- the shading that makes the swell read as a rounded form.
    `lit`/`dark` pick the palette (earth by default, water for a channel bed)."""
    ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    d = (nx * _LIGHT[0] + ny * _LIGHT[1] + nz * _LIGHT[2]) / ln
    k = max(0.0, min(1.0, 0.30 + 0.70 * d))
    return (int(dark[0] + (lit[0] - dark[0]) * k),
            int(dark[1] + (lit[1] - dark[1]) * k),
            int(dark[2] + (lit[2] - dark[2]) * k))


def draw_ground_mesh(surf, camera, scene, alpha=200):
    """Draw the scene's authored ground swell as a projected quad mesh over the
    flat floor. TILT ONLY; a no-op if the scene has no heightfield or the camera
    is flat (so pitch 0 stays byte-identical). Only tiles whose corners carry
    real height are drawn, so a small authored hill costs a small mesh, not the
    whole map.

    Each floor tile becomes a quad of its four corner ground points projected
    with their height; the quads are depth-sorted far->near and filled with a
    height/normal shade. A faint contour darkening on the far flank sells the
    crest that the sight system is hiding things behind."""
    hf = getattr(scene, "_ground_hf", None)
    if hf is None or camera.pitch <= 0.02:
        return
    h = len(hf)
    w = len(hf[0]) if h else 0
    if w == 0:
        return

    def cz(tx, ty):
        tx = 0 if tx < 0 else (w - 1 if tx >= w else tx)
        ty = 0 if ty < 0 else (h - 1 if ty >= h else ty)
        return hf[ty][tx]

    floor = getattr(scene, "floor", None)
    fh = len(floor) if floor else 0

    def is_water(tx, ty):
        # a mesh tile reads WET if the ground under it is a water char, so a
        # channel BED renders as the sunken river rather than mud
        if not floor or not (0 <= ty < fh):
            return False
        row = floor[ty]
        return 0 <= tx < len(row) and row[tx] in ("~", "@")

    quads = []
    for ty in range(h - 1):
        for tx in range(w - 1):
            z00 = cz(tx, ty)
            z10 = cz(tx + 1, ty)
            z01 = cz(tx, ty + 1)
            z11 = cz(tx + 1, ty + 1)
            # a tile whose four corners are all (near) grade keeps the flat
            # raster; raised OR sunken corners get a mesh quad (a channel bed
            # dips below 0, so test magnitude, not sign)
            if (abs(z00) <= 1e-6 and abs(z10) <= 1e-6
                    and abs(z01) <= 1e-6 and abs(z11) <= 1e-6):
                continue
            # tile corners in world px (corners sit on the tile grid; the
            # per-tile heights sit at tile CENTRES, so a corner reads the mean
            # of the four tiles that meet there -- cheap and smooth enough)
            wx0 = (tx + 0.5) * TILE
            wy0 = (ty + 0.5) * TILE
            wx1 = wx0 + TILE
            wy1 = wy0 + TILE
            p00 = camera.project(wx0, wy0, z00)
            p10 = camera.project(wx1, wy0, z10)
            p11 = camera.project(wx1, wy1, z11)
            p01 = camera.project(wx0, wy1, z01)
            # surface normal from the height gradient across the tile (world x/y
            # measured in px, so z shares the unit): n = (-dz/dx, -dz/dy, 1) up.
            dzdx = (z10 - z00 + z11 - z01) * 0.5
            dzdy = (z01 - z00 + z11 - z10) * 0.5
            if is_water(tx, ty) or is_water(tx + 1, ty + 1):
                col = _shade(-dzdx, -dzdy, TILE, _WATER_LIT, _WATER_DARK)
            else:
                col = _shade(-dzdx, -dzdy, TILE)
            depth = camera.depth((wx0 + wx1) * 0.5, (wy0 + wy1) * 0.5,
                                 (z00 + z11) * 0.5)
            quads.append((depth, (p00, p10, p11, p01), col))
    quads.sort(key=lambda q: q[0])
    for _d, poly, col in quads:
        pygame.draw.polygon(surf, col, poly)
