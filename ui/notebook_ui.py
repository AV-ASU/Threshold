"""Notebook UI -- review the notes the player has accumulated.

Toggled with N. Lists every entry in save.arg("evidence"); the
cursor moves through entries, and the right pane reads back the
full text. There is no editing, no choices.

Each save entry is the dict shape `{"name": slug, "lines": [...]}`,
written by scenes/dialogue.py:_evidence. If a legacy save still
holds bare-string names, this UI tolerates them by showing the
slug as the title with no body.
"""
import pygame
from constants import (
    SCREEN_W, SCREEN_H,
    C_WHITE, C_GOLD, C_DIM, C_PANEL, C_PANEL_BORDER,
)


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
        if not isinstance(log, list):
            return []
        out = []
        for e in log:
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
        veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 180))
        surf.blit(veil, (0, 0))
        panel = pygame.Rect(80, 60, SCREEN_W - 160, SCREEN_H - 120)
        pygame.draw.rect(surf, C_PANEL, panel)
        pygame.draw.rect(surf, C_PANEL_BORDER, panel, 2)
        title = self.fonts["lg"].render("Notebook", True, C_GOLD)
        surf.blit(title, (panel.x + 20, panel.y + 14))
        sub = self.fonts["sm"].render(
            "Your notes.", True, C_DIM)
        surf.blit(sub, (panel.x + 22, panel.y + 56))

        entries = self._entries()
        lx = panel.x + 20
        ly = panel.y + 92
        if not entries:
            empty = self.fonts["md"].render(
                "(nothing yet.)", True, C_DIM)
            surf.blit(empty, (lx, ly))
            self._draw_hint(surf, panel)
            return

        # Clamp cursor so it stays valid if the list shrank.
        if self.cursor >= len(entries):
            self.cursor = max(0, len(entries) - 1)

        # Left column: titles. Right column: full body of selected.
        list_w = 240
        for i, (name, _lines) in enumerate(entries):
            color = C_GOLD if i == self.cursor else C_WHITE
            prefix = ">" if i == self.cursor else " "
            label = f"{prefix} {_humanise(name)}"
            surf.blit(self.fonts["md"].render(label, True, color),
                      (lx, ly + i * 24))

        name, lines = entries[self.cursor]
        dx = panel.x + 20 + list_w + 20
        dy = panel.y + 92
        dw = panel.right - dx - 20
        dh = panel.bottom - dy - 50
        body = pygame.Rect(dx, dy, dw, dh)
        pygame.draw.rect(surf, (24, 22, 32), body)
        pygame.draw.rect(surf, C_PANEL_BORDER, body, 1)
        surf.blit(self.fonts["md"].render(_humanise(name), True, C_GOLD),
                  (dx + 10, dy + 10))
        if lines:
            self._wrap_text(surf, "\n".join(lines),
                            dx + 10, dy + 40, dw - 20)
        else:
            surf.blit(self.fonts["sm"].render(
                "(no detail recorded)", True, C_DIM),
                (dx + 10, dy + 40))

        self._draw_hint(surf, panel)

    def _draw_hint(self, surf, panel):
        hint = self.fonts["sm"].render(
            "[Up/Down] entry   [N or Esc] close",
            True, C_DIM)
        surf.blit(hint, (panel.x + 20, panel.bottom - 30))

    def _wrap_text(self, surf, text, x, y, w):
        font = self.fonts["sm"]
        line_h = font.get_linesize()
        lines = []
        for raw_line in text.split("\n"):
            words = raw_line.split(" ")
            cur = ""
            for word in words:
                test = (cur + " " + word).strip()
                if font.size(test)[0] > w:
                    lines.append(cur)
                    cur = word
                else:
                    cur = test
            lines.append(cur)
        for i, line in enumerate(lines):
            surf.blit(font.render(line, True, C_WHITE),
                      (x, y + i * line_h))
