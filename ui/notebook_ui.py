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


# Case-file headers for the save slugs that do not read like something
# the PI typed ("Maras Room", "Descent Mask", "Showed The Clerk"...).
# Slugs are load-bearing (saves and logic) and never change; only the
# display does. Anything unmapped falls back to Title Case.
_TITLES = {
    "working_theory":          "Working Theory",
    "case_timeline":           "Timeline",
    "maras_room":              "Mara's Room",
    "maras_journal":           "Mara's Journal",
    "the_ledger":              "The Old Registers",
    "chalk_surface":           "The Chalk Door",
    "chalk_works":             "The Works",
    "chalk_deep":              "Past the Deepest Face",
    "descent_dig":             "The Dig",
    "descent_leave":           "The Urge to Leave",
    "descent_mask":            "Permission to Leave",
    "showed_the_clerk":        "The Clerk, Shown Her Photo",
    "revisit_sable_checkouts": "Back to the Desk",
    "revisit_sable_smile":     "Ask the Clerk About Her",
    "revisit_vane_murder":     "Tell the Sheriff",
    "the_fold_told":           "The Roads",
    "crane_provoked":          "The Preacher, Provoked",
    "calder_table":            "Mrs. Calder's Table",
    "cult_calling":            "The Calling",
    "cult_bargain":            "The Bargain",
    "cult_digging":            "The Digging",
    "backwoods_note":          "The Backwoods Stash",
    "barrow_tools":            "The Barrow",
    "bell_tower_view":         "From the Bell Tower",
    "clerk_robe":              "The Pressed Robe",
    "lodge_candle_callback":   "Candles at the Lodge",
    "scarecrow":               "The Scarecrow",
    "the_old_stores_shelves":     "The Old Stores",
    "threshing_floor":         "The Threshing Floor",
    "works_cistern_seen":         "The Water Below",
    "worn_stone":              "The Worn Stone",
}


def _humanise(slug):
    """Case-file title for a save slug: the authored header where one
    exists, else 'some_note' becomes 'Some Note'."""
    t = _TITLES.get(slug)
    if t:
        return t
    parts = slug.split("_")
    return " ".join(p.capitalize() for p in parts)


class NotebookUI:
    def __init__(self, fonts, audio, save=None):
        self.fonts = fonts
        self.audio = audio
        self.save = save
        self.game = None       # set by Game; source of the soft lead line
        self.open = False
        self.cursor = 0

    def toggle(self):
        self.open = not self.open
        self.cursor = 0
        self.audio.play("menu_open" if self.open else "menu_close", 0.5)

    def _entries(self):
        if self.save is None:
            return []
        out = []
        # Pinned first (TODO #13): the PI's live working theory + reconstructed
        # timeline, derived from run state each open (never save entries), so
        # opening the book lands on the theory card by default.
        g = self.game
        if g is not None:
            if hasattr(g, "_working_theory"):
                wt = g._working_theory()
                if wt:
                    out.append(("working_theory", wt))
            if hasattr(g, "_case_timeline"):
                tl = g._case_timeline()
                if tl:
                    out.append(("case_timeline", tl))
        log = self.save.arg("evidence", [])
        notes = self.save.arg("notes", [])
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
