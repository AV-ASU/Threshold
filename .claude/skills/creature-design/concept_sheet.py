"""Reusable concept-sheet renderer + drawing kit for THRESHOLD creature
design.

Write each candidate creature as a draw function ``fn(surface, x, y,
view)`` (x, y is the creature's feet/base, view in {"front","side",
"back"}) and hand a list of them to ``make_sheet`` to get a single
labelled comparison PNG -- rows = candidates, columns = views -- then
send it with the SendUserFile tool for the user to react to.

Headless: importing this sets the dummy SDL drivers and inits pygame,
so no display is needed.

Example
-------
    from concept_sheet import make_sheet, ball, glow, limb, PALE, GOLDG

    def thing(s, x, y, view):
        ball(s, x, y - 30, 12)
        glow(s, (x, y - 32), 3); pygame.draw.circle(s, GOLDG, (x, y-32), 1)
        limb(s, (x, y-20), (x-14, y-30), (x-18, y), w=2)   # broken limb

    make_sheet([("1. thing", thing)], out="/tmp/concepts.png")
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import math  # noqa: F401  (handy for callers)
import pygame

if not pygame.get_init():
    pygame.init()
    pygame.display.set_mode((1, 1))

# ---- shared grim palette (gold is a SICK GLOW, never a flat fill) ----
VOID = (14, 13, 17); DK = (30, 27, 34); TAR = (20, 18, 24); TAR_HI = (46, 42, 54)
PALE = (202, 192, 172); PALE_LO = (148, 138, 120); PALE_BACK = (112, 104, 90)
GOLD = (230, 186, 48); GOLDG = (255, 218, 96)
BONE = (192, 180, 158); BONE_LO = (120, 112, 96); GORE = (122, 24, 18)


def glow(s, pos, r, a=55, col=GOLD):
    """Additive sick-light bloom -- use sparingly, mainly behind eyes."""
    g = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(g, (col[0], col[1], col[2], a), (int(pos[0]), int(pos[1])), r)
    s.blit(g, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


def ball(s, cx, cy, r, col=TAR, edge=VOID):
    """A wet tar lump (the building block for tumour/face masses)."""
    cx, cy, r = int(cx), int(cy), int(r)
    pygame.draw.circle(s, col, (cx, cy), r)
    pygame.draw.circle(s, edge, (cx, cy), r, 1)
    pygame.draw.circle(s, TAR_HI, (cx - r // 3, cy - r // 3), max(1, r // 4))


def limb(s, a, b, c, w=2, col=DK):
    """A two-segment jointed limb a->b->c (b is the joint). Bend `b`
    the wrong way for broken-anatomy horror."""
    a = (int(a[0]), int(a[1])); b = (int(b[0]), int(b[1])); c = (int(c[0]), int(c[1]))
    pygame.draw.line(s, col, a, b, w + 1)
    pygame.draw.line(s, col, b, c, max(1, w - 1))


def make_sheet(candidates, views=("front", "side", "back"),
               out="/tmp/concepts.png", cw=104, ch=124, scale=6,
               bg=(24, 21, 28), name_w=176):
    """Render candidates into one labelled sheet and save it.

    candidates : list of (label, fn) where fn(surface, x, y, view).
    Returns the output path. Read it before sending to the user.
    """
    font = pygame.font.Font(None, 26)
    lab_h = 26
    rows, cols = len(candidates), len(views)
    sheet = pygame.Surface((name_w + cols * cw * scale, lab_h + rows * ch * scale))
    sheet.fill((20, 18, 24))
    for c, v in enumerate(views):
        sheet.blit(font.render(v.upper(), True, (214, 208, 194)),
                   (name_w + c * cw * scale + cw * scale // 2 - 26, 4))
    for r, (label, fn) in enumerate(candidates):
        ry = lab_h + r * ch * scale
        sheet.blit(font.render(str(label), True, (236, 230, 216)),
                   (8, ry + ch * scale // 2 - 8))
        for c, v in enumerate(views):
            cell = pygame.Surface((cw, ch)); cell.fill(bg)
            try:
                fn(cell, cw // 2, ch - 16, v)
            except Exception as e:                       # noqa: BLE001
                cell.fill((60, 20, 20))
                cell.blit(font.render("ERR", True, (240, 120, 120)), (4, 4))
                print(f"  {label}/{v}: {e}")
            sheet.blit(pygame.transform.scale(cell, (cw * scale, ch * scale)),
                       (name_w + c * cw * scale, ry))
    pygame.image.save(sheet, out)
    print(f"saved {out} {sheet.get_size()} -- {rows} candidate(s) x {cols} view(s)")
    return out
