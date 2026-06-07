"""Notebook UI -- review the notes the player has accumulated.

Toggled with N. Lists every entry in save.arg("evidence"); the
cursor moves through entries, and the right pane reads back the
full text. There is no editing, no choices.

Each save entry is the dict shape `{"name": slug, "lines": [...]}`,
written by scenes/dialogue.py:_evidence. If a legacy save still
holds bare-string names, this UI tolerates them by showing the
slug as the title with no body.

Shares the quiet, filmic chrome with the inventory (ui/menu_chrome).
"""
import pygame
from constants import SCREEN_W, SCREEN_H, C_GOLD, C_DIM
from ui import menu_chrome as mc


def _humanise(slug):
    """Turn a slug like 'some_note' into a title 'Some Note'."""
    parts = slug.split("_")
    return " ".join(p.capitalize() for p in parts)


class NotebookUI:
    def __init__(self, fonts, audio, save=None):
        self.fonts = fonts
        self.audio = audio
        self.save = save
        self.open = False
        self.cursor = 0

    def toggle(self):
        self.open = not self.open
        self.cursor = 0
        self.audio.play("menu_open" if self.open else "menu_close", 0.5)

    def _entries(self):
        if self.save is None:
            return []
        log = self.save.arg("evidence", [])
        notes = self.save.arg("notes", [])
        out = []
        # Clues first (canonical evidence), then personal notes (the
        # door-dream). Notes live in their own save list so they never
        # count toward the evidence/King-gate -- see Game._log_dream_entry.
        for src in (log, notes):
            if not isinstance(src, list):
                continue
            for e in src:
                if isinstance(e, dict):
                    name = e.get("name", "?")
                    lines = e.get("lines", [])
                else:
                    name = str(e)
                    lines = []
                out.append((name, lines))
        return out

    def move(self, dy):
        n = max(1, len(self._entries()))
        self.cursor = (self.cursor + dy) % n
        self.audio.play("cursor", 0.4)

    def draw(self, surf):
        if not self.open:
            return
        mc.darken(surf, 180)
        panel = pygame.Rect(80, 60, SCREEN_W - 160, SCREEN_H - 120)
        mc.panel(surf, panel)
        title = self.fonts["lg"].render("Notebook", True, C_GOLD)
        surf.blit(title, (panel.x + 24, panel.y + 16))
        sub = self.fonts["sm"].render("What you have pieced together.",
                                      True, C_DIM)
        surf.blit(sub, (panel.x + 26, panel.y + 58))

        entries = self._entries()
        lx = panel.x + 36
        ly = panel.y + 96
        if not entries:
            empty = self.fonts["md"].render(
                "Nothing yet.", True, C_DIM)
            surf.blit(empty, (lx, ly))
            self._draw_hint(surf, panel)
            return

        # Clamp cursor so it stays valid if the list shrank.
        if self.cursor >= len(entries):
            self.cursor = max(0, len(entries) - 1)

        # Left column: titles. Right column: full body of selected.
        list_w = 240
        md = self.fonts["md"]
        for i, (name, _lines) in enumerate(entries):
            mc.row(surf, md, _humanise(name), lx, ly + i * 26,
                   i == self.cursor)

        name, lines = entries[self.cursor]
        dx = panel.x + 36 + list_w + 20
        dy = panel.y + 96
        dw = panel.right - dx - 24
        dh = panel.bottom - dy - 50
        body = pygame.Rect(dx, dy, dw, dh)
        mc.panel(surf, body, fill=mc.SUBPANEL_FILL, border=mc.PANEL_BORDER)
        surf.blit(self.fonts["md"].render(_humanise(name), True, C_GOLD),
                  (dx + 14, dy + 12))
        if lines:
            mc.wrap(surf, self.fonts["sm"], "\n".join(lines),
                    dx + 14, dy + 44, dw - 28)
        else:
            surf.blit(self.fonts["sm"].render(
                "Nothing more set down.", True, C_DIM),
                (dx + 14, dy + 44))

        self._draw_hint(surf, panel)

    def _draw_hint(self, surf, panel):
        mc.hint(surf, self.fonts["sm"],
                "arrows move . i for inventory . n or esc to close",
                panel.x + 24, panel.bottom - 30)
