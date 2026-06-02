"""EXPLORATION: what do other 4D base-forms look like for the King?

Compares three 4D objects, all everting through the same 4D rotation, same dark /
light-eating / sick-gold / surfacing-eyes aesthetic:

  1. tesseract        -- the blocky, man-made one (reads sci-fi)
  2. hypersphere      -- a 3-sphere: nested shells that turn inside-out (smooth)
  3. irregular blob   -- a lumpy, asymmetric 4D mass (organic, 'creature')

Outputs a comparison strip + an MP4 of each of the two new ones.

    python tools/explore_4d_shapes.py
"""
import os
import sys
import math
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
from rendering.king3d import _shade
from rendering.king_unfold import (_rot, _project, _eat_light, _eye, _yellow_sign,
                                   _MEM, _MEM_HI, _EDGE_DK, _EDGE_HI, _GOLD)

W, H = 420, 420


# --------------------------------------------------------------------------- #
# geometry builders -> (verts4, faces, eye_faces{fi:phase})
# --------------------------------------------------------------------------- #
def build_tesseract():
    verts = [(x * 0.9, y * 0.9, z * 0.9, w * 0.9)
             for x in (-1, 1) for y in (-1, 1) for z in (-1, 1) for w in (-1, 1)]
    faces, quad = [], [(-1, -1), (-1, 1), (1, 1), (1, -1)]
    for a in range(4):
        for b in range(a + 1, 4):
            others = [k for k in range(4) if k not in (a, b)]
            for fv0 in (-1, 1):
                for fv1 in (-1, 1):
                    f = []
                    for (va, vb) in quad:
                        co = [0, 0, 0, 0]
                        co[a] = va; co[b] = vb; co[others[0]] = fv0; co[others[1]] = fv1
                        f.append(verts.index(tuple(c * 0.9 for c in co)))
                    faces.append(f)
    r = random.Random(91)
    eye_faces = {fi: r.uniform(0, 9) for fi in r.sample(range(len(faces)), 7)}
    return verts, faces, eye_faces


def _sphere_grid(nlat, nlon, radial_fn):
    """Build a closed quad mesh over a 2-sphere param (lat,lon); radial_fn(dir)
    returns the 4D point for a unit direction (x,y,z) -- lets us make spheres,
    nested shells, or lumpy blobs from one routine."""
    verts, grid = [], []
    for i in range(nlat + 1):
        lat = math.pi * i / nlat
        row = []
        for j in range(nlon):
            lon = math.tau * j / nlon
            dx = math.sin(lat) * math.cos(lon)
            dy = math.cos(lat)
            dz = math.sin(lat) * math.sin(lon)
            verts.append(radial_fn((dx, dy, dz)))
            row.append(len(verts) - 1)
        grid.append(row)
    faces = []
    for i in range(nlat):
        for j in range(nlon):
            a = grid[i][j]; b = grid[i][(j + 1) % nlon]
            c = grid[i + 1][(j + 1) % nlon]; d = grid[i + 1][j]
            faces.append([a, b, c, d])
    return verts, faces


def build_hypersphere():
    """A 3-sphere as two nested 2-sphere shells (in 4D the 'inner' everts to the
    'outer' under rotation). Smooth, no man-made edges."""
    verts, faces = [], []
    shells = [(0.95, 0.30), (0.62, 0.78)]   # (radius, w-offset along 4th axis)
    for (rad, w0) in shells:
        def rf(d, rad=rad, w0=w0):
            return (d[0] * rad, d[1] * rad, d[2] * rad, w0)
        v, f = _sphere_grid(6, 10, rf)
        off = len(verts)
        verts += v
        faces += [[i + off for i in face] for face in f]
    r = random.Random(7)
    eye_faces = {fi: r.uniform(0, 9) for fi in r.sample(range(len(faces)), 10)}
    return verts, faces, eye_faces


def build_irregular():
    """A lumpy, asymmetric 4D mass: a sphere whose radius AND 4th coordinate are
    pushed around by smooth noise -- it folds through itself like an organ."""
    def noise(d, s):
        return (math.sin(3.1 * d[0] + 1.3 * s) * math.sin(2.3 * d[1] + 2.1) *
                math.cos(2.7 * d[2] + 0.7) +
                0.5 * math.sin(4.2 * d[1] + 1.1) * math.cos(3.3 * d[2] + 2.4 + s))

    def rf(d):
        n = noise(d, 0.0)
        rad = 0.85 * (1.0 + 0.42 * n)
        w = 0.7 * noise(d, 2.0)
        return (d[0] * rad, d[1] * rad, d[2] * rad, w)
    verts, faces = _sphere_grid(8, 12, rf)
    r = random.Random(23)
    eye_faces = {fi: r.uniform(0, 9) for fi in r.sample(range(len(faces)), 12)}
    return verts, faces, eye_faces


# --------------------------------------------------------------------------- #
# generic everting renderer (same look as king_unfold)
# --------------------------------------------------------------------------- #
def draw_geom(surf, cx, cy, t, threat, scale, geom):
    verts4, faces, eye_faces = geom
    spd = 0.18 + 0.5 * threat
    a = t * spd * 0.9; b = t * spd * 0.7 + 1.3
    c = t * spd * 0.33; d = t * spd * 0.21
    sz = scale * (0.7 + 0.5 * threat)
    pts, depths = [], []
    for vi, v in enumerate(verts4):
        p = list(v)
        wob = 0.05 * math.sin(t * 1.3 + vi)
        p = [p[0] + wob, p[1] - wob, p[2], p[3]]
        p = _rot(p, 0, 3, a); p = _rot(p, 1, 3, b)
        p = _rot(p, 2, 1, c); p = _rot(p, 0, 1, d)
        sx, sy, z, k3 = _project(p, cx, cy, sz)
        pts.append((sx, sy)); depths.append(z)
    zmin, zmax = min(depths), max(depths); zr = (zmax - zmin) or 1.0
    _eat_light(surf, cx, cy, sz * 1.7, 55 + 95 * threat)
    lay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    order = sorted(range(len(faces)), key=lambda fi: sum(depths[i] for i in faces[fi]))
    most, sign_face = 0.0, None
    for fi in order:
        poly = [pts[i] for i in faces[fi]]
        if len(poly) < 3:
            continue
        area = 0.0
        for k in range(len(poly)):
            x0, y0 = poly[k]; x1, y1 = poly[(k + 1) % len(poly)]
            area += x0 * y1 - x1 * y0
        facing = area < 0
        zc = sum(depths[i] for i in faces[fi]) / len(faces[fi])
        dn = (zc - zmin) / zr
        al = int((30 + 70 * dn) * (0.55 + 0.45 * (1 if facing else 0.4)))
        col = _shade(_MEM_HI if facing else _MEM, 0.5 + 0.5 * dn)
        pygame.draw.polygon(lay, (col[0], col[1], col[2], al), poly)
        ecol = _shade(_EDGE_DK, 0.4 + 0.6 * dn)
        if dn > 0.7 and threat > 0.3:
            ecol = _shade(_EDGE_HI, 0.4 + 0.6 * threat)
        pygame.draw.polygon(lay, ecol, poly, max(1, int(1 + 2 * dn)))
        if facing and abs(area) > most:
            most = abs(area); sign_face = (poly, abs(area))
    if threat > 0.32:
        appear = (threat - 0.32) / 0.4
        for fi, ph in eye_faces.items():
            poly = [pts[i] for i in faces[fi]]
            area = 0.0
            for k in range(len(poly)):
                x0, y0 = poly[k]; x1, y1 = poly[(k + 1) % len(poly)]
                area += x0 * y1 - x1 * y0
            if area >= 0:
                continue
            zc = sum(depths[i] for i in faces[fi]) / len(faces[fi])
            dn = (zc - zmin) / zr
            if dn < 0.4:
                continue
            ex = sum(p[0] for p in poly) / len(poly)
            ey = sum(p[1] for p in poly) / len(poly)
            er = math.sqrt(abs(area)) * 0.24
            bz = (t * 0.7 + ph) % 5.0
            openf = (1.0 if bz > 0.2 else abs(bz - 0.1) / 0.1) * min(1.0, appear)
            _eye(lay, ex, ey, er, openf, math.sin(t * 0.3 + ph) * 0.6,
                 int(220 * min(1.0, appear)))
    if sign_face and threat > 0.45:
        poly, fa = sign_face
        sx = sum(p[0] for p in poly) / len(poly)
        sy = sum(p[1] for p in poly) / len(poly)
        pulse = max(0.0, math.sin(t * 0.5)) ** 3
        _yellow_sign(lay, sx, sy, math.sqrt(fa) * 0.28,
                     int(150 * pulse * min(1.0, (threat - 0.45) / 0.3)))
    surf.blit(lay, (0, 0))


# --------------------------------------------------------------------------- #
def _bg():
    import random
    r = random.Random(3)
    s = pygame.Surface((W, H)); cx, cy = W // 2, H // 2
    maxr = math.hypot(cx, cy)
    for i in range(60, 0, -1):
        rr = int(maxr * i / 60); f = 1 - i / 60; v = 16 + int(26 * f)
        pygame.draw.circle(s, (int(v * 0.82), int(v * 0.86), int(v * 0.96)), (cx, cy), rr)
    for _ in range(1800):
        x, y = r.randrange(W), r.randrange(H); dd = r.randint(-7, 9)
        c = s.get_at((x, y))
        s.set_at((x, y), tuple(max(0, min(255, c[k] + dd)) for k in range(3)))
    return s


def _vig():
    v = pygame.Surface((W, H), pygame.SRCALPHA); cx, cy = W // 2, H // 2
    maxr = math.hypot(cx, cy)
    for i in range(26):
        pygame.draw.circle(v, (0, 0, 0, min(175, int(4.2 * i))),
                           (cx, cy), int(maxr * (1 - i / 26)))
    return v


VIG = None


def strip():
    global VIG
    VIG = _vig()
    font = pygame.font.SysFont("monospace", 12)
    items = [("tesseract", build_tesseract(), 78),
             ("hypersphere", build_hypersphere(), 92),
             ("irregular blob", build_irregular(), 95)]
    out = pygame.Surface((W * len(items), H + 18)); out.fill((4, 4, 6))
    for i, (lbl, geom, sc) in enumerate(items):
        s = _bg()
        draw_geom(s, W // 2, H // 2, 3.2, 0.92, sc, geom)
        s.blit(VIG, (0, 0))
        out.blit(s, (i * W, 0))
        out.blit(font.render(lbl, True, (160, 160, 170)), (i * W + 6, H + 3))
    pygame.image.save(out, "/tmp/explore_4d.png")
    print("wrote /tmp/explore_4d.png")


def mp4(name, geom, sc):
    import imageio.v2 as imageio
    import numpy as np
    fps = 24; T = 11.0; n = int(T * fps); frames = []
    for i in range(n):
        t = i / fps; u = i / (n - 1)
        threat = 0.1 + 0.85 * min(1.0, u / 0.7)
        s = _bg(); draw_geom(s, W // 2, H // 2, t, threat, sc, geom); s.blit(VIG, (0, 0))
        frames.append(np.transpose(pygame.surfarray.array3d(s), (1, 0, 2)))
    imageio.mimsave("/tmp/%s.mp4" % name, frames, fps=fps, macro_block_size=1)
    print("wrote /tmp/%s.mp4" % name)


if __name__ == "__main__":
    strip()
    mp4("explore_hypersphere", build_hypersphere(), 92)
    mp4("explore_irregular", build_irregular(), 95)
    print("done")
