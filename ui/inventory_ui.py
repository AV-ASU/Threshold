"""Inventory menu UI.

THRESHOLD: combat is gone, so the inventory is small and reads as
"what you carry" rather than "what you fight with." Two live tabs --
Tools (axe, keys) and Notes (lore: the journal, diary pages, robe,
the Mask). The Notebook (evidence review) lives in its own panel
keyed to N -- not in inventory tabs -- because it shows text beats
rather than carryable items.

The chrome (translucent panel, gold margin selection, quiet hints)
is shared with the notebook via ui/menu_chrome, to keep the menus
feeling like the same quiet, filmic UI rather than an arcade menu.
"""
import pygame
from constants import SCREEN_W, SCREEN_H, C_GOLD, C_DIM
from systems.items import ITEM_DEFS, effective_desc, journal_page
from ui.item_icons import draw_item_icon
from ui import menu_chrome as mc


# Tabs in display order. Each entry: (set-of-item-kinds shown,
# display label). The first tab to match an item's kind owns it,
# so order matters. "Tools" sweeps weapon+key+armor (combat-era
# armor stubs collapse here too -- one fewer empty tab). "Notes"
# is anything tagged "lore" -- the things the player reads, not
# uses. "Consumables" is its own tab because the player USES
# them differently (use vs equip).
TABS = [
    (("weapon", "key", "armor"),  "Tools"),
    (("lore",),                    "Notes"),
    (("consumable",),              "Consumables"),
]


class InventoryUI:
    def __init__(self, fonts, audio, save=None):
        self.fonts = fonts
        self.audio = audio
        # Optional save reference, kept for the inventory API. Item
        # descriptions are static now (effective_desc ignores it), but
        # the journal reads its current page off the save.
        self.save = save
        self.open = False
        self.cursor = 0
        self.tab = 0

    def toggle(self):
        self.open = not self.open
        self.cursor = 0
        self.tab = 0
        self.audio.play("menu_open" if self.open else "menu_close", 0.6)

    # ---- selection helpers ----

    def _filtered_items(self, inv):
        """Return list of (orig_index, key, qty) for items in the active tab."""
        kinds = TABS[self.tab][0]
        # Owned-kinds set: every kind claimed by any tab. Anything
        # whose kind isn't owned falls into the LAST tab as a
        # catch-all so unknown future items aren't invisible.
        owned = set()
        for tab_kinds, _ in TABS:
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

    def change_tab(self, dy, inventory):
        self.tab = (self.tab + dy) % len(TABS)
        self.cursor = 0
        self.audio.play("cursor", 0.5)

    def move(self, dy, inventory):
        items = self._filtered_items(inventory)
        n = max(1, len(items))
        self.cursor = (self.cursor + dy) % n
        self.audio.play("cursor", 0.5)

    def _selected_key(self, inv):
        items = self._filtered_items(inv)
        if not items or self.cursor >= len(items):
            return None
        return items[self.cursor][1]

    def use_selected(self, player):
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
        elif d["kind"] == "consumable":
            # No consumables remain in circulation (combat-era potions are
            # gone; the flashlight is a key-kind Tool toggled with [F], not
            # a consumable).
            self.audio.play("cancel", 0.4)
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
        # Re-clamp the cursor in case the filtered list shrank (e.g. a
        # consumable was used up).
        items = self._filtered_items(inv)
        if self.cursor >= len(items):
            self.cursor = max(0, len(items) - 1)

    # ---- drawing ----

    def draw(self, surf, player):
        if not self.open: return
        mc.darken(surf, 170)

        panel = pygame.Rect(80, 60, SCREEN_W - 160, SCREEN_H - 120)
        mc.panel(surf, panel)

        title = self.fonts["lg"].render("Inventory", True, C_GOLD)
        surf.blit(title, (panel.x + 24, panel.y + 16))

        inv = player.inventory
        eq = inv.equipped
        # Combat is gone, so only the Tool slot is meaningful.
        # The Worn slot is vestigial -- not shown.
        eq_str = "In hand:  " + (
            ITEM_DEFS.get(eq["weapon"], {}).get("name", eq["weapon"])
            if eq["weapon"] else "nothing")
        surf.blit(self.fonts["sm"].render(eq_str, True, (150, 146, 158)),
                  (panel.x + 24, panel.y + 52))

        # Tab bar -- the active tab is gold with a thin underline; the
        # others sit dim and quiet. No brackets.
        tab_y = panel.y + 90
        tab_x = panel.x + 24
        tab_font = self.fonts["sm"]
        for i, (_kinds, label) in enumerate(TABS):
            col = C_GOLD if i == self.tab else C_DIM
            t_surf = tab_font.render(label, True, col)
            surf.blit(t_surf, (tab_x, tab_y))
            if i == self.tab:
                pygame.draw.line(surf, C_GOLD,
                                 (tab_x, tab_y + t_surf.get_height() + 1),
                                 (tab_x + t_surf.get_width(),
                                  tab_y + t_surf.get_height() + 1))
            tab_x += t_surf.get_width() + 24

        # Items list (filtered to active tab).
        items = self._filtered_items(inv)
        lx = panel.x + 36
        ly = panel.y + 124
        if not items:
            surf.blit(self.fonts["md"].render("nothing here.", True, C_DIM),
                      (lx, ly))
        else:
            md = self.fonts["md"]
            for vi, (_orig, key, qty) in enumerate(items):
                d = ITEM_DEFS.get(key, {"name": key, "kind": "?"})
                selected = (vi == self.cursor)
                row_y = ly + vi * 28
                if selected:
                    mc.accent_bar(surf, lx - 14, row_y, md.get_linesize())
                draw_item_icon(surf, lx, row_y + 2, key)
                color = C_GOLD if selected else mc.TEXT_IDLE
                surf.blit(md.render(d["name"], True, color), (lx + 24, row_y))
                if qty > 1:
                    qx = lx + 24 + md.size(d["name"])[0] + 8
                    surf.blit(self.fonts["sm"].render(str(qty), True, C_DIM),
                              (qx, row_y + 4))

        # Reading pane on the right of the selected item.
        if items and self.cursor < len(items):
            key = items[self.cursor][1]
            d = ITEM_DEFS.get(key, {})
            dx = panel.right - 340
            dy = panel.y + 124
            dpanel = pygame.Rect(dx, dy, 316, 326)
            mc.panel(surf, dpanel, fill=mc.SUBPANEL_FILL, border=mc.PANEL_BORDER)
            surf.blit(self.fonts["md"].render(d.get("name", key), True, C_GOLD),
                      (dx + 14, dy + 12))
            tx = dx + 14
            ty = dy + 44
            tw = dpanel.width - 28
            if key == "mom_notebook":
                page, idx, total = journal_page(self.save)
                mc.wrap(surf, self.fonts["sm"], page, tx, ty, tw)
                # Page footer: which leaf, and the quiet turn-the-page tell.
                foot = f"page {idx + 1} of {total}"
                surf.blit(self.fonts["sm"].render(foot, True, C_DIM),
                          (tx, dpanel.bottom - 28))
                turn = ("enter . turn the page" if idx < total - 1
                        else "the last page")
                ts = self.fonts["sm"].render(turn, True, mc.HINT)
                surf.blit(ts, (dpanel.right - ts.get_width() - 14,
                               dpanel.bottom - 28))
            else:
                mc.wrap(surf, self.fonts["sm"],
                        effective_desc(key, self.save), tx, ty, tw)

        mc.hint(surf, self.fonts["sm"],
                "arrows move . left and right change tab . enter to "
                "read or equip . n for notes . esc to close",
                panel.x + 24, panel.bottom - 30)
