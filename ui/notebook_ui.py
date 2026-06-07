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
from constants import SCREEN_W, SCREEN_H
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

    # The case card sits to the right; the index of beats to the left.
    _CARD_CENTER = (SCREEN_W - 250, SCREEN_H // 2 + 4)

    def draw(self, surf):
        if not self.open:
            return
        mc.darken(surf, 210)

        BONE = (200, 194, 180)
        FAINT = (132, 126, 116)
        head = self.fonts["serif_lg"].render("Case notes", True, BONE)
        surf.blit(head, (64, 44))
        surf.blit(self.fonts["serif_sm"].render(
            "What you have pieced together.", True, FAINT), (66, 86))

        entries = self._entries()
        lx = 84
        ly = 140
        if not entries:
            surf.blit(self.fonts["serif_it"].render(
                "The page is still blank.", True, FAINT), (lx, ly))
            self._draw_hint(surf)
            return

        # Clamp cursor so it stays valid if the list shrank.
        if self.cursor >= len(entries):
            self.cursor = max(0, len(entries) - 1)

        rf = self.fonts["serif"]
        for i, (name, _lines) in enumerate(entries):
            selected = (i == self.cursor)
            row_y = ly + i * 30
            if selected:
                mc.accent_bar(surf, lx - 18, row_y, rf.get_linesize())
            col = (214, 198, 150) if selected else (158, 152, 142)
            surf.blit(rf.render(_humanise(name), True, col), (lx, row_y))

        # The selected beat, rendered as a card the PI typed up.
        name, lines = entries[self.cursor]
        self._draw_case_card(surf, name, lines)
        self._draw_hint(surf)

    def _draw_case_card(self, surf, name, lines):
        W, H = 420, 470
        card = mc.paper(W, H, seed=sum(ord(c) for c in name) + 3,
                        base=mc.CARD_MANILA)
        # A typed header, upper-cased like a case label, ruled off below.
        title = self.fonts["mono"].render(
            _humanise(name).upper(), True, mc.CARD_INK)
        card.blit(title, (26, 30))
        pygame.draw.line(card, mc.CARD_RULE, (26, 58), (W - 26, 58), 1)
        if lines:
            mc.wrap(card, self.fonts["mono"], "\n".join(lines),
                    26, 76, W - 52, color=mc.CARD_INK, line_h=22)
        else:
            card.blit(self.fonts["mono"].render(
                "(nothing more set down)", True, mc.INK_FADE), (26, 76))
        mc.lay_page(surf, card, self._CARD_CENTER, tilt=-1.0)

    def _draw_hint(self, surf):
        mc.hint(surf, self.fonts["serif_sm"],
                "arrow keys to read . i for what you carry . "
                "n or esc to close the book",
                64, SCREEN_H - 34)
