"""THE ASSEMBLED PROPS -- declared as parts, checked against a reference.

Each entry here is DATA (`rendering/assembly.Assembly`), not a draw function,
and each is built to the proportions recorded in `rendering/references.py`.
The two together are the whole point of the rework: a shape you can check
against a fact, made of parts that cannot get culling or draw order wrong.

Units are the game's world units, where a wall rises to about 26 and the
player is roughly 20 tall. Each builder converts the reference's real inches
into those units through one `k` factor, so the RATIO comes from the
reference and only the overall size is a scene decision -- which is exactly
the split that kept going wrong when both were eyeballed together.
"""
import math

from rendering import prim
from rendering.assembly import Assembly, Part


def _k(real, target_len):
    """World units per inch, from a reference length and the size we want."""
    return target_len / real[0]


# --------------------------------------------------------------- mailbox
# Reference: Joroleman 1915. A TUNNEL -- arched top, flat front, back and
# bottom -- on a post, flag on the flank. 23.2 x 11 x 13.4in, box floor
# 41-45in up. The version this replaces was a rectangular prism at 1.76 : 1
# : 1.06 against a real 2.11 : 1 : 1.22, which is why it read as a grey
# lozenge on a stick: the arch IS the silhouette.
def _mailbox():
    real = (23.2, 11.0, 13.4)
    k = _k(real, 16.0)                 # 16 world units long
    w, d = real[0] * k, real[1] * k
    springing = d * 0.42               # the flat sides stop, the vault starts
    rise = real[2] * k - springing
    post_h = 13.4 * k * 3.0            # the reference's 3x box height
    return Assembly(
        Part(prim.cyl(r=1.15, length=post_h, axis="z"),
             mat="cedar", name="post"),
        Part(prim.arch(w, d, springing, rise=rise),
             at=(0, 0, post_h - 1.0), mat="tin", name="box"),
        # the signal flag, on the FLANK near the door end
        Part(prim.box(0.7, 0.7, 6.0),
             at=(w * 0.26, d * 0.52, post_h + springing * 0.2),
             mat="flag_red", name="flagpost"),
        Part(prim.plate(3.2, 0.4, 2.6),
             at=(w * 0.26 + 1.4, d * 0.52, post_h + springing * 0.2 + 4.0),
             mat="flag_red", name="flag"),
    )


# ------------------------------------------------------------------ stoop
# Reference: a stoop is the LANDING at the door with steps coming off it.
# The first model was two treads and no landing, which is a flight of steps,
# and it read as slabs lying on grass however correct its rise-to-run was --
# so it was remade rather than shipped with a caveat (VISION, "if it isn't
# good, remake it now"). Side cheeks close the step ends; the nosing shadow
# is what reads as a step at distance.
def _stoop(steps=3):
    rise_in, run_in, wide_in, landing_in = 7.0, 11.0, 60.0, 36.0
    k = 24.0 / wide_in                 # 24 world units wide
    rise, run = rise_in * k, run_in * k
    wide, landing = wide_in * k, landing_in * k
    parts = []
    # THE LANDING: the platform at the door, the thing that makes it a stoop
    top = steps * rise
    parts.append(Part(prim.box(landing, wide, rise * 0.9, z0=top - rise * 0.9),
                      at=(landing / 2 + (steps - 1) * run, 0, 0),
                      mat="plank", name="landing"))
    parts.append(Part(prim.box(landing, wide, top - rise * 0.9),
                      at=(landing / 2 + (steps - 1) * run, 0, 0),
                      mat="concrete", name="landing_base"))
    # THE STEPS, coming down off it toward -x
    for i in range(steps):
        back = i * run
        parts.append(Part(prim.box(run, wide, (i + 1) * rise),
                          at=(back, 0, 0), mat="concrete", name=f"riser{i}"))
        nb = 2
        bw = wide / nb
        for b in range(nb):
            parts.append(Part(
                prim.box(run + rise * 0.34, bw * 0.94, rise * 0.28,
                         z0=(i + 1) * rise - rise * 0.28),
                at=(back - rise * 0.17, (b - (nb - 1) / 2.0) * bw, 0),
                mat="plank", name=f"tread{i}_{b}"))
    # SIDE CHEEKS: the boards closing the step ends, so the treads never
    # float. Without them a flight reads as loose slabs from the side.
    for sgn in (-1, 1):
        parts.append(Part(
            prim.wedge(steps * run, 1.4, steps * rise),
            at=((steps - 1) * run / 2 + run / 2, sgn * (wide / 2 + 0.5), 0),
            yaw=math.pi, mat="plank", name=f"cheek{sgn}"))
    return Assembly(*parts)


# --------------------------------------------------------------- woodpile
# Reference: it is LOGS. The separate pieces and the ragged ends are the
# entire read; every attempt to imply them from one mass failed.
def _woodpile(rows=6, seed=7):
    # THE AXES WERE WRONG BEFORE. A stack runs ALONG a wall with the log ends
    # facing out, so a log lies ACROSS the stack: the log axis is the stack's
    # DEPTH (+y, one log long), and the stack extends along +x and up. The
    # old model laid the logs along +x, which made a short chunky raft
    # instead of a wall of ends, and the proportion check caught it at
    # 1.28 : 1 : 1.08 against a real 3.00 : 1 : 1.88.
    LOG = 5.0                          # a split log's diameter
    DEEP = 13.0                        # one log's length -> the stack's depth
    ncol = 8                           # logs along the wall
    parts = []
    for row in range(rows):
        stagger = (row % 2) * (LOG * 0.5)
        for c in range(ncol):
            h = (seed + row * 31 + c * 17)
            x = (c - (ncol - 1) / 2.0) * LOG * 0.98 + stagger
            if abs(x) > (ncol * LOG) / 2.0:
                continue
            ln = DEEP * (0.88 + ((h >> 2) % 5) * 0.05)
            shove = (((h >> 5) % 7) - 3) * 0.55
            z = row * LOG * 0.90 + LOG / 2
            parts.append(Part(prim.cyl(r=LOG * 0.47, length=ln, axis="x"),
                              at=(x, shove, z), yaw=math.pi / 2,
                              mat="log_bark", name=f"log{row}_{c}"))
    return Assembly(*parts)


# ------------------------------------------------------------- yard fence
# Reference: split cedar posts, two or three SAGGING wire strands. One bay.
def _yard_fence(bay=42.0, seed=3):
    parts = []
    for i in (-1, 1):
        lean = ((seed + i) % 5 - 2) * 0.18
        parts.append(Part(prim.prism(6, 1.1, 20.0, rot=lean),
                          at=(i * bay / 2, 0, 0), mat="cedar",
                          name=f"post{i}"))
    # the strands are thin boxes spanning the bay, dropped a little at
    # mid-span so they read as sagging rather than strung
    for z, sag in ((18.0, 0.9), (12.0, 1.5), (6.0, 2.0)):
        parts.append(Part(prim.box(bay, 0.35, 0.35, z0=0.0),
                          at=(0, 0, z - sag), mat="steel",
                          name=f"wire{int(z)}"))
    return Assembly(*parts)


ASSEMBLIES = {
    "mailbox": _mailbox(),
    "stoop": _stoop(),
    "woodpile": _woodpile(),
    "yard_fence": _yard_fence(),
}
