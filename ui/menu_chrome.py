"""Shared chrome for the full-screen menus (inventory, notebook, pause).

This pulls the menu look away from the old bracketed arcade style toward
something quieter and more filmic, to match the rest of THRESHOLD:

  * a translucent panel laid over the darkened world, not an opaque slab
  * a single hairline border instead of a hard 2px frame
  * selection shown by a soft gold margin accent + a small indent, never
    a ">" caret
  * dim, lowercase, period separated prose for the key hints (the same
    voice as the title screen's "arrow keys . enter . F11")

Keeping it in one place means the inventory and notebook stay in
lockstep, and retires the two copies of the old word-wrap helper.
No dashes in any string a player reads (project hard rule).
"""
import math
import random
import pygame
from constants import SCREEN_W, SCREEN_H, C_GOLD, C_WHITE

# The panel reads as smoked glass over the world rather than a lit box.
PANEL_FILL = (10, 9, 16, 236)
PANEL_BORDER = (64, 58, 78)
SUBPANEL_FILL = (18, 16, 26, 230)
ACCENT = C_GOLD
TEXT = C_WHITE
TEXT_IDLE = (150, 146, 158)
HINT = (96, 92, 108)


def darken(surf, alpha=180):
    """Veil the whole screen so the world reads as receded behind glass."""
    veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    veil.fill((0, 0, 0, alpha))
    surf.blit(veil, (0, 0))


def panel(surf, rect, fill=PANEL_FILL, border=PANEL_BORDER):
    """A translucent panel with a hairline border."""
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    s.fill(fill)
    surf.blit(s, rect.topleft)
    if border is not None:
        pygame.draw.rect(surf, border, rect, 1)


def accent_bar(surf, x, y, h, color=ACCENT):
    """The thin gold margin tick that marks the selected row."""
    pygame.draw.rect(surf, color, (x, y + 2, 2, max(2, h - 4)))


def row(surf, font, label, x, y, selected, color=ACCENT, idle=TEXT_IDLE,
        indent=12):
    """Draw one selectable list row. Selected rows get a gold margin tick
    and an indent + gold text; idle rows stay flush and pale. Returns the
    x the label text was drawn at."""
    if selected:
        accent_bar(surf, x, y, font.get_linesize(), color)
        tx = x + indent
        col = color
    else:
        tx = x + indent - 8
        col = idle
    surf.blit(font.render(label, True, col), (tx, y))
    return tx


def hint(surf, font, text, x, y):
    """A dim, quiet hint line."""
    surf.blit(font.render(text, True, HINT), (x, y))


# --- Diegetic documents (paper + ink) ------------------------------------
#
# The menus stop being floating UI panels and start being THINGS the PI is
# holding: an aged journal leaf, a typed case card. Paper is procedural and
# cached (a stable grain per size/seed/tint, so it never shimmers), and the
# caller draws ink onto a copy before laying it down with a soft shadow and a
# faint tilt -- so it reads as a photographed document, not a dialog box.

# Mara's journal: warm cream leaf, dark sepia ink.
PAPER_CREAM = (214, 201, 172)
INK = (44, 33, 26)
INK_FADE = (96, 80, 62)
RULE = (150, 134, 104)
# The PI's case card: cooler, greyer manila, near-black typed ink.
CARD_MANILA = (196, 186, 162)
CARD_INK = (34, 30, 28)
CARD_RULE = (138, 128, 110)

_PAPER_CACHE = {}


def _paper_texture(w, h, seed, base, ruled, line_h, top_pad):
    key = (w, h, seed, base, ruled, line_h, top_pad)
    cached = _PAPER_CACHE.get(key)
    if cached is not None:
        return cached
    rng = random.Random(seed * 2654435761 & 0xFFFFFFFF)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((*base, 255))
    br, bg, bb = base
    # Fibrous grain: a sparse field of slightly lighter/darker motes.
    for _ in range((w * h) // 26):
        x = rng.randint(0, w - 1); y = rng.randint(0, h - 1)
        d = rng.randint(-16, 12)
        surf.set_at((x, y), (max(0, min(255, br + d)),
                             max(0, min(255, bg + d)),
                             max(0, min(255, bb + d)), 255))
    # A few soft foxing stains (age blooms) low on the leaf.
    for _ in range(rng.randint(3, 6)):
        sx = rng.randint(8, w - 8); sy = rng.randint(8, h - 8)
        sr = rng.randint(10, 30)
        blot = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
        for i in range(sr, 0, -2):
            a = int(18 * (1 - i / sr))
            pygame.draw.circle(blot, (120, 92, 54, a), (sr, sr), i)
        surf.blit(blot, (sx - sr, sy - sr))
    # Faint ruled writing lines.
    if ruled and line_h > 0:
        rule_c = RULE if base == PAPER_CREAM else CARD_RULE
        y = top_pad
        while y < h - 6:
            ln = pygame.Surface((w - 24, 1), pygame.SRCALPHA)
            ln.fill((*rule_c, 70))
            surf.blit(ln, (12, y))
            y += line_h
    # Edge darkening: the leaf is older and dirtier at its border.
    edge = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(10):
        a = int(60 * (1 - i / 10))
        pygame.draw.rect(edge, (40, 28, 16, a), (i, i, w - 2 * i, h - 2 * i), 1)
    surf.blit(edge, (0, 0))
    _PAPER_CACHE[key] = surf
    return surf


def paper(w, h, seed=0, base=PAPER_CREAM, ruled=False, line_h=0, top_pad=0):
    """Return a fresh copy of a cached parchment leaf to draw ink onto."""
    return _paper_texture(w, h, seed, base, ruled, line_h, top_pad).copy()


def lay_page(surf, page, center, tilt=0.0):
    """Lay a finished page (ink already drawn) onto `surf` at `center` with
    a soft drop shadow and an optional small tilt, so it reads as a real
    sheet set down rather than a UI panel."""
    img = page
    if abs(tilt) > 0.01:
        img = pygame.transform.rotozoom(page, tilt, 1.0)
    rect = img.get_rect(center=center)
    # Drop shadow: a blurred-ish dark slab, offset down-right.
    sh = pygame.Surface((rect.w + 18, rect.h + 18), pygame.SRCALPHA)
    for i in range(6):
        a = 26 - i * 3
        pygame.draw.rect(sh, (0, 0, 0, max(0, a)),
                         (i, i, rect.w + 18 - 2 * i, rect.h + 18 - 2 * i),
                         border_radius=4)
    surf.blit(sh, (rect.x - 6, rect.y + 2))
    surf.blit(img, rect.topleft)
    return rect


def ink_wrap(surf, font, text, x, y, w, color=INK, line_h=None):
    """Like `wrap`, but for dark ink on paper (default INK colour)."""
    return wrap(surf, font, text, x, y, w, color=color, line_h=line_h)


def wrap_lines(font, text, w):
    """Word-wrap `text` into width `w` and return the LINES, drawing nothing.
    Split out so a caller that has to paginate (the Casebook's running
    notebook) measures with exactly the same rules that `wrap` draws with,
    rather than keeping a second wrapper that can disagree with it."""
    out = []
    for raw in text.split("\n"):
        if raw == "":
            out.append("")
            continue
        cur = ""
        for word in raw.split(" "):
            test = (cur + " " + word).strip()
            if cur and font.size(test)[0] > w:
                out.append(cur)
                cur = word
            else:
                cur = test
        out.append(cur)
    return out


def wrap(surf, font, text, x, y, w, color=TEXT, line_h=None):
    """Word-wrap `text` into width `w`, honouring explicit newlines (a
    blank line for "\\n\\n"). Returns the y past the last line."""
    line_h = line_h or font.get_linesize()
    cy = y
    for line in wrap_lines(font, text, w):
        if line:
            surf.blit(font.render(line, True, color), (x, cy))
        cy += line_h
    return cy
