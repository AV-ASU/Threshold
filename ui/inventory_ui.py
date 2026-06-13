"""Inventory menu UI.

THRESHOLD: combat is gone, so the inventory is small and reads as
"what you carry" rather than "what you fight with." Three tabs --
Tools (axe, keys), Notes (lore: the journal, diary pages, robe, the
Mask), and Case Notes (the beats the PI has pieced together: the six
canonical clues plus the personal door-dream note). The case notes used
to live in their own N-key panel; they are folded in here so the player
keeps everything in one book. N now opens the inventory straight to the
Case Notes tab.

The chrome (translucent panel, gold margin selection, quiet hints)
is shared with the menu helpers in ui/menu_chrome, to keep the menus
feeling like the same quiet, filmic UI rather than an arcade menu.
"""
import pygame
from constants import SCREEN_W, SCREEN_H
from systems.items import ITEM_DEFS, effective_desc, journal_page
from ui.item_icons import draw_item_icon
from ui import menu_chrome as mc


def _humanise(slug):
    """Turn a slug like 'some_note' into a title 'Some Note'."""
    parts = slug.split("_")
    return " ".join(p.capitalize() for p in parts)


# Tabs in display order. Each entry: (set-of-item-kinds shown OR None,
# display label). The first tab to match an item's kind owns it, so
# order matters. "Tools" sweeps weapon+key+armor (combat-era armor
# stubs collapse here too). "Notes" is anything tagged "lore" -- the
# things the player reads. "Case Notes" is the SPECIAL non-item tab
# (kinds=None): it reads the evidence/notes logs off the save rather
# than the inventory, replacing the old Consumables tab (no consumables
# remain in circulation).
CASE_NOTES = None
TABS = [
    (("weapon", "key", "armor"),  "Tools"),
    (("lore",),                    "Notes"),
    (CASE_NOTES,                   "Case Notes"),
]
# Index of the Case Notes tab, so N can jump straight to it.
NOTES_TAB = next(i for i, (k, _) in enumerate(TABS) if k is CASE_NOTES)


class InventoryUI:
    def __init__(self, fonts, audio, save=None):
        self.fonts = fonts
        self.audio = audio
        # Optional save reference, kept for the inventory API. Item
        # descriptions are static now (effective_desc ignores it), but
        # the journal reads its current page off the save, and the Case
        # Notes tab reads the evidence/notes logs.
        self.save = save
        self.open = False
        self.cursor = 0
        self.tab = 0

    def toggle(self):
        self.open = not self.open
        self.cursor = 0
        self.tab = 0
        self.audio.play("menu_open" if self.open else "menu_close", 0.6)

    def open_case_notes(self):
        """Open (or reveal) the book straight on the Case Notes tab --
        what N does now that the notebook is no longer its own panel."""
        if not self.open:
            self.open = True
            self.audio.play("menu_open", 0.6)
        self.tab = NOTES_TAB
        self.cursor = 0

    # ---- selection helpers ----

    def _is_notes_tab(self, tab=None):
        return TABS[self.tab if tab is None else tab][0] is CASE_NOTES

    def _case_entries(self):
        """The case-notes list: the canonical clues first, then the PI's
        personal notes (the door-dream). Each entry is (title, lines).
        Notes live in their own save list so they never count toward the
        evidence/King-gate (see Game._log_dream_entry)."""
        if self.save is None:
            return []
        out = []
        for key in ("evidence", "notes"):
            src = self.save.arg(key, [])
            if not isinstance(src, list):
                continue
            for e in src:
                if isinstance(e, dict):
                    out.append((e.get("name", "?"), e.get("lines", [])))
                else:
                    out.append((str(e), []))
        return out

    def _filtered_items(self, inv):
        """Return list of (orig_index, key, qty) for items in the active tab.
        The Case Notes tab holds no items (it reads the save), so it
        returns an empty list here."""
        kinds = TABS[self.tab][0]
        if kinds is CASE_NOTES:
            return []
        # Owned-kinds set: every item-kind claimed by any tab. Anything
        # whose kind isn't owned falls into the LAST item-tab as a
        # catch-all so unknown future items aren't invisible.
        owned = set()
        for tab_kinds, _ in TABS:
            if tab_kinds is not CASE_NOTES:
                owned.update(tab_kinds)
        # The last ITEM tab (not the case-notes tab) is the catch-all.
        item_tabs = [i for i, (k, _) in enumerate(TABS) if k is not CASE_NOTES]
        is_last = (self.tab == item_tabs[-1])
        out = []
        for i, (key, qty) in enumerate(inv.items):
            d = ITEM_DEFS.get(key, {})
            k = d.get("kind", "misc")
            if k in kinds:
                out.append((i, key, qty))
            elif is_last and k not in owned:
                out.append((i, key, qty))
        return out

    def change_tab(self, dy, inventory):
        self.tab = (self.tab + dy) % len(TABS)
        self.cursor = 0
        self.audio.play("cursor", 0.5)

    def move(self, dy, inventory):
        if self._is_notes_tab():
            n = max(1, len(self._case_entries()))
        else:
            n = max(1, len(self._filtered_items(inventory)))
        self.cursor = (self.cursor + dy) % n
        self.audio.play("cursor", 0.5)

    def _selected_key(self, inv):
        items = self._filtered_items(inv)
        if not items or self.cursor >= len(items):
            return None
        return items[self.cursor][1]

    def use_selected(self, player):
        # The Case Notes tab is read-only -- there is nothing to "use."
        if self._is_notes_tab():
            self.audio.play("cursor", 0.4)
            return
        inv = player.inventory
        items = self._filtered_items(inv)
        if not items: return
        if self.cursor >= len(items): return
        _, key, _ = items[self.cursor]
        d = ITEM_DEFS.get(key)
        if not d: return
        if d["kind"] in ("weapon", "armor"):
            inv.equip(key)
            self.audio.play("confirm", 0.7)
        elif d["kind"] in ("key", "lore"):
            # THRESHOLD: Mara's Journal is a readable, paged item. Each
            # Enter turns one leaf (advancing the read counter so the
            # description panel shows the next page); turning past the
            # LAST leaf fires the witnessing door-dream flashback.
            if key == "mom_notebook" and self.save:
                n = self.save.arg("notebook_pages_read", 0) + 1
                self.save.set_arg("notebook_pages_read", min(3, n))
                if n >= 3 and not self.save.flag("flashback_seen"):
                    self.save.set_flag("flashback_pending", True)
                    self.open = False
                else:
                    # A soft page-turn while there are leaves left to read.
                    self.audio.play("blip_soft", 0.45)
            else:
                self.audio.play("cursor", 0.5)
        # Re-clamp the cursor in case the filtered list shrank.
        items = self._filtered_items(inv)
        if self.cursor >= len(items):
            self.cursor = max(0, len(items) - 1)

    # ---- drawing ----

    # The document leaf lives on the right; the carried-things index on
    # the left. Geometry shared by draw() and the document helpers.
    _DOC_CENTER = (SCREEN_W - 246, SCREEN_H // 2 + 6)

    def draw(self, surf, player):
        if not self.open: return
        # A deep, near-opaque veil: the world recedes and we're left with
        # the PI going through what he carries by a low light. Not a glass
        # panel floating over a lit game.
        mc.darken(surf, 210)
        inv = player.inventory

        BONE = (200, 194, 180)
        FAINT = (132, 126, 116)

        # Heading + what's in his hand, set in serif like a chapter head
        # rather than a menu title.
        head = self.fonts["serif_lg"].render("What you carry", True, BONE)
        surf.blit(head, (64, 44))
        eq = inv.equipped
        if eq["weapon"]:
            held = ITEM_DEFS.get(eq["weapon"], {}).get("name", eq["weapon"])
            eq_str = f"In hand, the {held.lower()}."
        else:
            eq_str = "Your hands are empty."
        surf.blit(self.fonts["serif_sm"].render(eq_str, True, FAINT), (66, 86))

        # Tabs: serif words, the open one in warm ink-gold and underlined,
        # the rest recede. No brackets, no buttons.
        tab_y = 122
        tab_x = 66
        tf = self.fonts["serif"]
        for i, (_kinds, label) in enumerate(TABS):
            col = (210, 184, 110) if i == self.tab else (110, 104, 96)
            t = tf.render(label, True, col)
            surf.blit(t, (tab_x, tab_y))
            if i == self.tab:
                pygame.draw.line(surf, (170, 142, 80),
                                 (tab_x, tab_y + t.get_height() + 1),
                                 (tab_x + t.get_width(),
                                  tab_y + t.get_height() + 1))
            tab_x += t.get_width() + 30

        if self._is_notes_tab():
            self._draw_case_notes(surf, FAINT)
        else:
            self._draw_items(surf, inv, FAINT)

        mc.hint(surf, self.fonts["serif_sm"],
                "arrow keys to look . left and right to turn the page . "
                "enter to read or take in hand . esc to put it away",
                64, SCREEN_H - 34)

    def _draw_items(self, surf, inv, FAINT):
        # The index of things, down the left.
        items = self._filtered_items(inv)
        lx = 84
        ly = 172
        rf = self.fonts["serif"]
        if not items:
            surf.blit(self.fonts["serif_it"].render(
                "Nothing under this heading.", True, FAINT), (lx, ly))
        else:
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

        # The selected thing, rendered as the object it is.
        if items and self.cursor < len(items):
            key = items[self.cursor][1]
            d = ITEM_DEFS.get(key, {})
            if key == "mom_notebook":
                self._draw_journal_leaf(surf)
            elif d.get("kind") == "lore":
                self._draw_paper_note(surf, key, d)
            else:
                self._draw_object(surf, key, d)

    def _draw_case_notes(self, surf, FAINT):
        """The Case Notes tab: an index of pieced-together beats down the
        left, the selected one typed up as a case card on the right. The
        evidence/dream notes that used to live behind the N key."""
        entries = self._case_entries()
        lx = 84
        ly = 172
        rf = self.fonts["serif"]
        if not entries:
            surf.blit(self.fonts["serif_it"].render(
                "The page is still blank.", True, FAINT), (lx, ly))
            return
        if self.cursor >= len(entries):
            self.cursor = max(0, len(entries) - 1)
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
        """A case beat the PI typed up -- manila card, mono header ruled
        off, the body in typewriter ink (ported from the old notebook)."""
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
        mc.lay_page(surf, card, self._DOC_CENTER, tilt=-1.0)

    def _draw_journal_leaf(self, surf):
        """Mara's journal as an aged, ruled leaf with her words in ink."""
        page, idx, total = journal_page(self.save)
        W, H = 388, 452
        line_h = 27
        top_pad = 96
        leaf = mc.paper(W, H, seed=7, base=mc.PAPER_CREAM,
                        ruled=True, line_h=line_h, top_pad=top_pad - line_h)
        title = self.fonts["serif_it"].render("Mara's Journal", True, mc.INK)
        leaf.blit(title, (28, 34))
        pygame.draw.line(leaf, mc.RULE, (28, 70), (W - 28, 70), 1)
        mc.ink_wrap(leaf, self.fonts["serif_sm"], page,
                    28, top_pad, W - 56, color=mc.INK, line_h=line_h)
        foot = self.fonts["serif_sm"].render(
            f"page {idx + 1} of {total}", True, mc.INK_FADE)
        leaf.blit(foot, (28, H - 34))
        turn = ("turn the page" if idx < total - 1 else "her last page")
        ts = self.fonts["serif_it"].render(turn, True, mc.INK_FADE)
        leaf.blit(ts, (W - ts.get_width() - 28, H - 34))
        mc.lay_page(surf, leaf, self._DOC_CENTER, tilt=-1.4)

    def _draw_paper_note(self, surf, key, d):
        """A lore fragment (letter, the cult's testimony) as a paper note."""
        W, H = 388, 452
        leaf = mc.paper(W, H, seed=sum(ord(c) for c in key),
                        base=mc.PAPER_CREAM)
        title = self.fonts["serif_it"].render(
            d.get("name", key), True, mc.INK)
        leaf.blit(title, (28, 34))
        pygame.draw.line(leaf, mc.RULE, (28, 70), (W - 28, 70), 1)
        mc.ink_wrap(leaf, self.fonts["serif_sm"],
                    effective_desc(key, self.save),
                    28, 88, W - 56, color=mc.INK, line_h=24)
        mc.lay_page(surf, leaf, self._DOC_CENTER, tilt=1.1)

    def _draw_object(self, surf, key, d):
        """A tool or key: the object itself, held up to the light, with a
        plain ink-pale caption. Not paper, not a card -- a thing."""
        cx, cy = self._DOC_CENTER
        # Soft pool of light behind the object.
        glow = pygame.Surface((220, 220), pygame.SRCALPHA)
        for i in range(90, 0, -6):
            a = int(26 * (1 - i / 90))
            pygame.draw.circle(glow, (60, 56, 50, a), (110, 110), i)
        surf.blit(glow, (cx - 110, cy - 130))
        # The icon, blown up large with nearest-neighbour pixel edges.
        chip = pygame.Surface((16, 16), pygame.SRCALPHA)
        draw_item_icon(chip, 0, 0, key)
        big = pygame.transform.scale(chip, (112, 112))
        surf.blit(big, (cx - 56, cy - 150))
        name = self.fonts["serif_lg"].render(
            d.get("name", key), True, (206, 198, 182))
        surf.blit(name, (cx - name.get_width() // 2, cy - 24))
        mc.wrap(surf, self.fonts["serif_sm"], effective_desc(key, self.save),
                cx - 150, cy + 16, 300, color=(150, 144, 134))
