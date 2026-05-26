"""Inventory menu UI.

THRESHOLD: combat is gone, so the inventory is small and reads as
"what you carry" rather than "what you fight with." Three tabs --
Tools (axe, flashlight, keys, charcoal), Notes (lore: notebook,
polaroid, kid's drawing, diary pages, robe), Consumables (spare
batteries). The vestigial Apparel tab is gone; armor-kind items
from the combat era fall into Tools so old saves still surface
them. The Notebook (evidence review) lives in its own panel
keyed to N -- not in inventory tabs -- because it shows text
beats rather than carryable items.
"""
import pygame
from constants import (
    SCREEN_W, SCREEN_H,
    C_WHITE, C_GOLD, C_RED, C_DIM, C_PANEL, C_PANEL_BORDER,
)
from systems.items import ITEM_DEFS, effective_desc
from ui.item_icons import draw_item_icon


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
        # descriptions are static now (effective_desc ignores it).
        self.save = save
        self.open = False
        self.cursor = 0
        self.tab = 0
        # Round-14: tracks whether the polaroid was the highlighted
        # entry on the previous draw frame. Each fresh navigation onto
        # the polaroid bumps `polaroid_reads`; the polaroid description
        # devolves with each read (see effective_desc). Resets to False
        # when the player navigates off it.
        self._was_viewing_polaroid = False

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
            # No consumables remain in circulation (the flashlight and
            # its batteries were scrapped; combat-era potions are gone).
            self.audio.play("cancel", 0.4)
        elif d["kind"] in ("key", "lore"):
            # THRESHOLD: using mom_notebook advances the read
            # counter. Page 3 sets the flashback_pending flag the
            # Game system polls each frame to fire the witnessing
            # flashback.
            if key == "mom_notebook" and self.save:
                n = self.save.arg("notebook_pages_read", 0) + 1
                self.save.set_arg("notebook_pages_read", min(3, n))
                self.audio.play("blip_soft", 0.45)
                if n >= 3 and not self.save.flag("flashback_seen"):
                    self.save.set_flag("flashback_pending", True)
                    self.open = False
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
        veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 170))
        surf.blit(veil, (0, 0))

        panel = pygame.Rect(80, 60, SCREEN_W - 160, SCREEN_H - 120)
        pygame.draw.rect(surf, C_PANEL, panel)
        pygame.draw.rect(surf, C_PANEL_BORDER, panel, 2)

        title = self.fonts["lg"].render("Inventory", True, C_GOLD)
        surf.blit(title, (panel.x + 20, panel.y + 14))

        inv = player.inventory
        eq = inv.equipped
        # Combat is gone, so only the Tool slot is meaningful.
        # The Worn slot is vestigial -- not shown.
        eq_str = "Tool:  " + (ITEM_DEFS.get(eq["weapon"], {}).get("name", eq["weapon"])
                              if eq["weapon"] else "(none)")
        surf.blit(self.fonts["sm"].render(eq_str, True, C_WHITE),
                  (panel.x + 20, panel.y + 50))

        # Tab bar -- highlighted entry shows in gold, others dimmed.
        tab_y = panel.y + 92
        tab_x = panel.x + 20
        tab_font = self.fonts["sm"]
        for i, (_kinds, label) in enumerate(TABS):
            txt = f"[ {label} ]"
            col = C_GOLD if i == self.tab else C_DIM
            t_surf = tab_font.render(txt, True, col)
            surf.blit(t_surf, (tab_x, tab_y))
            tab_x += t_surf.get_width() + 8

        # Items list (filtered to active tab).
        items = self._filtered_items(inv)
        lx = panel.x + 20
        ly = panel.y + 122
        if not items:
            surf.blit(self.fonts["md"].render("(empty)", True, C_DIM), (lx, ly))
        else:
            for vi, (_orig, key, qty) in enumerate(items):
                d = ITEM_DEFS.get(key, {"name": key, "kind": "?"})
                color = C_GOLD if vi == self.cursor else C_WHITE
                prefix = ">" if vi == self.cursor else " "
                line = f"{prefix} {d['name']}"
                if qty > 1:
                    line += f" x{qty}"
                row_y = ly + vi * 26
                draw_item_icon(surf, lx, row_y + 2, key)
                surf.blit(self.fonts["md"].render(line, True, color),
                          (lx + 22, row_y))

        # Description panel on right of the selected item.
        if items and self.cursor < len(items):
            key = items[self.cursor][1]
            # Polaroid read tracking -- count one read per fresh
            # navigation onto the polaroid entry. The save's
            # polaroid_reads counter feeds effective_desc, which
            # progressively erases figures from the description.
            if key == "polaroid":
                if not self._was_viewing_polaroid and self.save:
                    n = self.save.arg("polaroid_reads", 0) + 1
                    self.save.set_arg("polaroid_reads", n)
                self._was_viewing_polaroid = True
            else:
                self._was_viewing_polaroid = False
            d = ITEM_DEFS.get(key, {})
            dx = panel.right - 320
            dy = panel.y + 122
            dpanel = pygame.Rect(dx, dy, 300, 310)
            pygame.draw.rect(surf, (24, 22, 32), dpanel)
            pygame.draw.rect(surf, C_PANEL_BORDER, dpanel, 1)
            surf.blit(self.fonts["md"].render(d.get("name", key), True, C_GOLD),
                      (dx + 10, dy + 10))
            desc = effective_desc(key, self.save)
            self._wrap_text(surf, desc, dx + 10, dy + 40, 280)

        hint = self.fonts["sm"].render(
            "[<-/->] tab   [Up/Down] item   [Enter] equip/use   "
            "[N] notebook   [I or Esc] close",
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
            surf.blit(font.render(line, True, C_WHITE), (x, y + i * line_h))
