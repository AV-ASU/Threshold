"""The Casebook -- one book, opened by I or N.

THRESHOLD used to split this in two: an Inventory (I) and a separate Case
Notebook (N), two full screens on two keys, with a confusing third "Notes"
tab inside the inventory that meant lore ITEMS, not case notes. This merges
all of it into ONE book you flip through:

  * CASE   -- what you've pieced together: the working theory, the
              timeline, the clues, the interior notes. The heart of it.
  * TOOLS  -- what you carry and use: the axe, the gun, keys, the
              flashlight.
  * PAPERS -- what you carry and read: Mara's journal + letter, the
              records, the cult's testimony, the Mask.

Both I and N open the SAME book; N lands on CASE (the case is the point),
I lands on TOOLS. Left/right turns the tab, up/down walks the index, Enter
reads or takes a thing in hand. The dead combat-era "Consumables" tab is
gone.

The chrome (paper leaves, gold-margin selection, quiet hints) is shared
with the pause menu via ui/menu_chrome, so the whole UI reads as one quiet,
filmic thing rather than an arcade menu.
"""
import pygame
from constants import SCREEN_W, SCREEN_H
from systems.items import ITEM_DEFS, effective_desc, journal_page
from ui.item_icons import draw_item_icon
from ui.case_titles import humanise as _humanise
from ui import menu_chrome as mc


# Tab order. CASE first (the case is the point); then the carried things,
# split TOOLS (used) vs PAPERS (read). Each carried tab claims a set of
# item kinds; PAPERS (last) also sweeps anything unclaimed so a new item is
# never invisible. Combat-era "armor"/"consumable" kinds collapse into
# TOOLS/PAPERS -- no empty tabs.
CASE_TAB = 0
TOOLS_TAB = 1
PAPERS_TAB = 2
TABS = [
    ("Case",   None),
    ("Tools",  ("weapon", "key", "armor")),
    ("Papers", ("lore", "consumable")),
]


class JournalUI:
    def __init__(self, fonts, audio, save=None):
        self.fonts = fonts
        self.audio = audio
        self.save = save
        self.game = None        # set by Game; source of the derived theory
        self.open = False
        self.tab = CASE_TAB
        self.cursor = 0

    # ---- open / close ----

    def toggle(self, tab=None):
        self.open = not self.open
        if self.open and tab is not None:
            self.tab = tab
        self.cursor = 0
        self.audio.play("menu_open" if self.open else "menu_close", 0.6)

    def open_to(self, tab):
        """Open the book on a specific tab (or close it if that same tab is
        already showing). Lets I and N feel like two ribbons into one book."""
        if self.open and self.tab == tab:
            self.toggle()
            return
        if not self.open:
            self.open = True
            self.audio.play("menu_open", 0.6)
        self.tab = tab
        self.cursor = 0

    # ---- selection helpers ----

    def _inv(self):
        if self.game is not None and getattr(self.game, "player", None):
            return self.game.player.inventory
        return None

    def _filtered_items(self, inv):
        """(orig_index, key, qty) for items under the active carried tab.
        Empty on the CASE tab (it holds no items)."""
        kinds = TABS[self.tab][1]
        if kinds is None or inv is None:
            return []
        owned = set()
        for _label, tab_kinds in TABS:
            if tab_kinds:
                owned.update(tab_kinds)
        is_last = (self.tab == len(TABS) - 1)
        out = []
        for i, (key, qty) in enumerate(inv.items):
            d = ITEM_DEFS.get(key, {})
            k = d.get("kind", "misc")
            if k in kinds:
                out.append((i, key, qty))
            elif is_last and k not in owned:
                out.append((i, key, qty))
        return out

    def _case_entries(self):
        """Notebook entries: the derived pins (working theory, timeline)
        first, then the clues (canonical evidence), then the interior notes.
        Derived pins read live run state each open, so the book always lands
        on the freshest theory."""
        if self.save is None:
            return []
        out = []
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
        for src in (log, notes):
            if not isinstance(src, list):
                continue
            for e in src:
                if isinstance(e, dict):
                    out.append((e.get("name", "?"), e.get("lines", [])))
                else:
                    out.append((str(e), []))
        return out

    # Back-compat name for the notebook test harness (flow.py).
    def _entries(self):
        return self._case_entries()

    def _row_count(self):
        if self.tab == CASE_TAB:
            return len(self._case_entries())
        return len(self._filtered_items(self._inv()))

    def change_tab(self, dy, inventory=None):
        self.tab = (self.tab + dy) % len(TABS)
        self.cursor = 0
        self.audio.play("cursor", 0.5)

    def move(self, dy, inventory=None):
        n = max(1, self._row_count())
        self.cursor = (self.cursor + dy) % n
        self.audio.play("cursor", 0.4)

    def use_selected(self, player):
        """Enter on the active row. CASE entries are read-only (no action).
        A weapon equips; Mara's journal turns a leaf (and the third turn
        fires the door-dream); other papers/keys just acknowledge."""
        if self.tab == CASE_TAB:
            return
        inv = player.inventory
        items = self._filtered_items(inv)
        if not items or self.cursor >= len(items):
            return
        _, key, _ = items[self.cursor]
        d = ITEM_DEFS.get(key)
        if not d:
            return
        if d["kind"] in ("weapon", "armor"):
            inv.equip(key)
            self.audio.play("confirm", 0.7)
        elif key == "mom_notebook" and self.save:
            # Mara's Journal is paged: each Enter turns one leaf. The
            # door-dream now fires on PICKUP of the journal, not on the 3rd
            # read (play-notes; scenes/interiors.py _barn_update), so reading
            # it is just reading -- no flashback trigger here.
            n = self.save.arg("notebook_pages_read", 0) + 1
            self.save.set_arg("notebook_pages_read", min(3, n))
            self.audio.play("blip_soft", 0.45)
        else:
            self.audio.play("cursor", 0.5)
        items = self._filtered_items(inv)
        if self.cursor >= len(items):
            self.cursor = max(0, len(items) - 1)

    # ---- drawing ----

    _DOC_CENTER = (SCREEN_W - 246, SCREEN_H // 2 + 18)

    def draw(self, surf, player=None):
        if not self.open:
            return
        # A deep veil: the world recedes and the PI is left with his book by
        # a low light. Not a glass panel over a lit game.
        mc.darken(surf, 210)
        if player is None:
            player = getattr(self.game, "player", None)

        BONE = (200, 194, 180)
        FAINT = (132, 126, 116)

        # Heading + a one-line subtitle, set like a chapter head. The Tools
        # subtitle reports what's in hand; the others frame the tab.
        if self.tab == CASE_TAB:
            head_txt, sub = "Case notes", "What you have pieced together."
        elif TABS[self.tab][0] == "Tools":
            head_txt = "What you carry"
            eq = player.inventory.equipped if player else {"weapon": None}
            if eq.get("weapon"):
                held = ITEM_DEFS.get(eq["weapon"], {}).get("name", eq["weapon"])
                sub = f"In hand, the {held.lower()}."
            else:
                sub = "Your hands are empty."
        else:
            head_txt = "What you carry"
            sub = "Papers, and the things you have taken."
        surf.blit(self.fonts["serif_lg"].render(head_txt, True, BONE), (64, 40))
        surf.blit(self.fonts["serif_sm"].render(sub, True, FAINT), (66, 80))

        # The tab ribbon: always all three, the open one warm gold and
        # underlined, so the book reads as one thing you turn.
        self._draw_tabs(surf)

        if self.tab == CASE_TAB:
            self._draw_case_tab(surf)
        else:
            self._draw_items_tab(surf, player)

        self._draw_hint(surf)

    def _draw_tabs(self, surf):
        tab_y = 116
        tab_x = 66
        tf = self.fonts["serif"]
        for i, (label, _kinds) in enumerate(TABS):
            col = (210, 184, 110) if i == self.tab else (110, 104, 96)
            t = tf.render(label, True, col)
            surf.blit(t, (tab_x, tab_y))
            if i == self.tab:
                pygame.draw.line(surf, (170, 142, 80),
                                 (tab_x, tab_y + t.get_height() + 1),
                                 (tab_x + t.get_width(), tab_y + t.get_height() + 1))
            tab_x += t.get_width() + 30

    # -- CASE tab --

    _CARD_CENTER = (SCREEN_W - 250, SCREEN_H // 2 + 18)

    def _draw_case_tab(self, surf):
        FAINT = (132, 126, 116)
        entries = self._case_entries()
        lx, ly = 84, 166
        if not entries:
            surf.blit(self.fonts["serif_it"].render(
                "The page is still blank.", True, FAINT), (lx, ly))
            return
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
        name, lines = entries[self.cursor]
        self._draw_case_card(surf, name, lines)

    def _draw_case_card(self, surf, name, lines):
        W, H = 420, 470
        card = mc.paper(W, H, seed=sum(ord(c) for c in name) + 3,
                        base=mc.CARD_MANILA)
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

    # -- carried tabs (TOOLS / PAPERS) --

    def _draw_items_tab(self, surf, player):
        FAINT = (132, 126, 116)
        inv = player.inventory if player else None
        items = self._filtered_items(inv)
        lx, ly = 84, 166
        rf = self.fonts["serif"]
        if not items:
            surf.blit(self.fonts["serif_it"].render(
                "Nothing under this heading.", True, FAINT), (lx, ly))
            return
        if self.cursor >= len(items):
            self.cursor = max(0, len(items) - 1)
        for vi, (_orig, key, qty) in enumerate(items):
            d = ITEM_DEFS.get(key, {"name": key, "kind": "?"})
            selected = (vi == self.cursor)
            row_y = ly + vi * 32
            if selected:
                mc.accent_bar(surf, lx - 18, row_y, rf.get_linesize())
            draw_item_icon(surf, lx - 2, row_y + 3, key)
            color = (214, 198, 150) if selected else (158, 152, 142)
            surf.blit(rf.render(d["name"], True, color), (lx + 22, row_y))
            if qty > 1:
                qx = lx + 22 + rf.size(d["name"])[0] + 8
                surf.blit(self.fonts["serif_sm"].render(
                    str(qty), True, FAINT), (qx, row_y + 4))
        key = items[self.cursor][1]
        d = ITEM_DEFS.get(key, {})
        if key == "mom_notebook":
            self._draw_journal_leaf(surf)
        elif d.get("kind") == "lore":
            self._draw_paper_note(surf, key, d)
        else:
            self._draw_object(surf, key, d)

    def _draw_journal_leaf(self, surf):
        page, idx, total = journal_page(self.save)
        W, H = 388, 452
        line_h = 27
        top_pad = 96
        leaf = mc.paper(W, H, seed=7, base=mc.PAPER_CREAM,
                        ruled=True, line_h=line_h, top_pad=top_pad - line_h)
        leaf.blit(self.fonts["serif_it"].render(
            "Mara's Journal", True, mc.INK), (28, 34))
        pygame.draw.line(leaf, mc.RULE, (28, 70), (W - 28, 70), 1)
        mc.ink_wrap(leaf, self.fonts["serif_sm"], page,
                    28, top_pad, W - 56, color=mc.INK, line_h=line_h)
        leaf.blit(self.fonts["serif_sm"].render(
            f"page {idx + 1} of {total}", True, mc.INK_FADE), (28, H - 34))
        turn = ("turn the page" if idx < total - 1 else "her last page")
        ts = self.fonts["serif_it"].render(turn, True, mc.INK_FADE)
        leaf.blit(ts, (W - ts.get_width() - 28, H - 34))
        mc.lay_page(surf, leaf, self._DOC_CENTER, tilt=-1.4)

    def _draw_paper_note(self, surf, key, d):
        W, H = 388, 452
        leaf = mc.paper(W, H, seed=sum(ord(c) for c in key),
                        base=mc.PAPER_CREAM)
        leaf.blit(self.fonts["serif_it"].render(
            d.get("name", key), True, mc.INK), (28, 34))
        pygame.draw.line(leaf, mc.RULE, (28, 70), (W - 28, 70), 1)
        mc.ink_wrap(leaf, self.fonts["serif_sm"],
                    effective_desc(key, self.save),
                    28, 88, W - 56, color=mc.INK, line_h=24)
        mc.lay_page(surf, leaf, self._DOC_CENTER, tilt=1.1)

    def _draw_object(self, surf, key, d):
        cx, cy = self._DOC_CENTER
        glow = pygame.Surface((220, 220), pygame.SRCALPHA)
        for i in range(90, 0, -6):
            a = int(26 * (1 - i / 90))
            pygame.draw.circle(glow, (60, 56, 50, a), (110, 110), i)
        surf.blit(glow, (cx - 110, cy - 130))
        chip = pygame.Surface((16, 16), pygame.SRCALPHA)
        draw_item_icon(chip, 0, 0, key)
        big = pygame.transform.scale(chip, (112, 112))
        surf.blit(big, (cx - 56, cy - 150))
        name = self.fonts["serif_lg"].render(
            d.get("name", key), True, (206, 198, 182))
        surf.blit(name, (cx - name.get_width() // 2, cy - 24))
        mc.wrap(surf, self.fonts["serif_sm"], effective_desc(key, self.save),
                cx - 150, cy + 16, 300, color=(150, 144, 134))

    def _draw_hint(self, surf):
        mc.hint(surf, self.fonts["serif_sm"],
                "up down to look . left right to turn to the next tab . "
                "enter to read or take in hand . esc to close the book",
                64, SCREEN_H - 34)
