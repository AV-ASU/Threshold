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


def wrap(surf, font, text, x, y, w, color=TEXT, line_h=None):
    """Word-wrap `text` into width `w`, honouring explicit newlines (a
    blank line for "\\n\\n"). Returns the y past the last line."""
    line_h = line_h or font.get_linesize()
    cy = y
    for raw in text.split("\n"):
        if raw == "":
            cy += line_h
            continue
        cur = ""
        for word in raw.split(" "):
            test = (cur + " " + word).strip()
            if cur and font.size(test)[0] > w:
                surf.blit(font.render(cur, True, color), (x, cy))
                cy += line_h
                cur = word
            else:
                cur = test
        surf.blit(font.render(cur, True, color), (x, cy))
        cy += line_h
    return cy
