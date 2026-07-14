"""Close-up examine TABLEAUX -- the Game-side state machine.

A tableau is a modal close-up (the art lives in `ui/tableau.py`): the world
freezes, an animated close-up draws, and a menu of options mutates it live.
Wired into Game like the flashback cutscene: `_tableau is not None` freezes the
world (`world_frozen`), `_tick_tableau` animates it, `_draw_tableau` paints it
over everything, and `handle_event` routes input to `_tableau_input` while it
is up. The pilot is the bedroom writing desk (the pistol + the case file);
`ui/tableau.draw_desk_tableau` is its art. New tableaux add an art fn there and
an opener here.

Player-facing text (the menu labels + the case-file lines) is mirrored in
DIALOGUE.md Part B, per the contract.
"""
import re
import pygame

from ui.tableau import draw_desk_tableau

_STRIP = re.compile(r"\[/?c(=\w+)?\]")


def _plain(s):
    return _STRIP.sub("", s)


class TableauMixin:
    # ------------------------------------------------------------------ open
    def _open_desk_tableau(self):
        """The spare-room writing desk: pistol + case file under the lamp."""
        self._tableau = {
            "kind": "desk",
            "t": 0.0,
            "cursor": 0,
            "reading": None,
            "state": {"gun_present": not self.save.flag("desk_pistol_taken")},
        }
        self.audio.play("blip_low", 0.4)

    def _close_tableau(self):
        self._tableau = None

    # --------------------------------------------------------------- options
    def _tableau_options(self):
        """The live menu, recomputed from state so a taken gun drops its
        option. Each entry is (label, callback)."""
        tb = self._tableau
        if tb is None or tb["kind"] != "desk":
            return []
        opts = []
        if tb["state"].get("gun_present"):
            opts.append(("Take the pistol", self._tableau_take_gun))
        opts.append(("Read the case file", self._tableau_read_case))
        opts.append(("Step back", self._close_tableau))
        return opts

    def _tableau_take_gun(self):
        tb = self._tableau
        tb["state"]["gun_present"] = False
        self.save.set_flag("desk_pistol_taken", True)
        for d in self.scene.decorations:
            if getattr(d, "tag", None) == "writing_desk":
                d.gun_present = False
                self._invalidate_prop_card(d)
        self.player.inventory.add("pistol", 1)
        self.player.inventory.equipped["weapon"] = "pistol"
        self.audio.play("pickup", 0.7)
        self.show_notice("You take your pistol off the desk.")
        tb["cursor"] = 0

    def _tableau_read_case(self):
        """The case file, readable AT the close-up. After the Dark it has
        rewritten itself. Same lines as the old desk read (DIALOGUE.md)."""
        if self.save.flag("hive_seen"):
            self.save.set_flag("case_closed_read", True)
            self._tableau["reading"] = [
                "Subject: located. Recovery: declined.",
                "The handwriting is yours. You don't remember writing it.",
            ]
        else:
            self.save.set_flag("read_journal", True)
            self._tableau["reading"] = [
                "CLIENT: Walter Blaine. Wants his daughter found and "
                "brought home.",
                "MARA BLAINE, 26. Cut ties, drove north, quit calling "
                "home. The trail runs cold at Brimley.",
                "The job: ask my questions, find the girl, drive home by "
                "morning.",
                "The drive in was easy. Then the engine died at the lodge "
                "steps and wouldn't catch again.",
            ]

    # ----------------------------------------------------------------- input
    def _tableau_input(self, ev):
        if ev.type != pygame.KEYDOWN or self._tableau is None:
            return
        tb = self._tableau
        if tb["reading"] is not None:
            # Reading the file: E/Enter goes back to the menu; anything else
            # (a movement key, Esc) is walking away -- it drops the whole
            # close-up, interrupting the notes (play-notes).
            if ev.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                tb["reading"] = None
            else:
                self._close_tableau()
            return
        opts = self._tableau_options()
        if not opts:
            self._close_tableau()
            return
        if ev.key in (pygame.K_UP, pygame.K_w):
            tb["cursor"] = (tb["cursor"] - 1) % len(opts)
            self.audio.play("blip_low", 0.3)
        elif ev.key in (pygame.K_DOWN, pygame.K_s):
            tb["cursor"] = (tb["cursor"] + 1) % len(opts)
            self.audio.play("blip_low", 0.3)
        elif ev.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            opts[min(tb["cursor"], len(opts) - 1)][1]()
        elif ev.key == pygame.K_ESCAPE:
            self._close_tableau()

    # ---------------------------------------------------------------- update
    def _tick_tableau(self, dt):
        if self._tableau is not None:
            self._tableau["t"] += dt

    # ------------------------------------------------------------------ draw
    def _draw_tableau(self):
        tb = getattr(self, "_tableau", None)
        if tb is None:
            return
        surf = self.screen
        W, H = surf.get_width(), surf.get_height()
        if tb["kind"] == "desk":
            draw_desk_tableau(surf, tb["t"], tb["state"])

        if tb["reading"] is not None:
            self._draw_tableau_reading(surf, tb["reading"])
            return
        # the menu (diegetic option list, lower-right)
        opts = self._tableau_options()
        f = self.fonts["serif_lg"]
        pad, lh = 16, 40
        pw = max(f.size(o[0])[0] for o in opts) + 60
        panel_h = len(opts) * lh + 20
        bx, by = W - pw - 40, H - panel_h - 40
        panel = pygame.Surface((pw, panel_h), pygame.SRCALPHA)
        panel.fill((10, 8, 5, 210))
        surf.blit(panel, (bx, by))
        pygame.draw.rect(surf, (120, 96, 40), (bx, by, pw, panel_h), 1)
        cur = min(tb["cursor"], len(opts) - 1)
        for i, (label, _cb) in enumerate(opts):
            sel = (i == cur)
            col = (240, 224, 150) if sel else (150, 140, 118)
            pre = "> " if sel else "   "
            surf.blit(f.render(pre + label, True, col),
                      (bx + pad, by + 10 + i * lh))

    def _draw_tableau_reading(self, surf, lines):
        W, H = surf.get_width(), surf.get_height()
        rd = pygame.Surface((W, H), pygame.SRCALPHA)
        rd.fill((0, 0, 0, 165))
        surf.blit(rd, (0, 0))
        f = self.fonts["serif_lg"]
        fi = self.fonts["serif_it"]
        maxw = int(W * 0.72)
        x0, y = int(W * 0.14), int(H * 0.30)
        for ln in lines:
            for wln in _wrap(_plain(ln), f, maxw):
                surf.blit(f.render(wln, True, (222, 214, 196)), (x0, y))
                y += f.get_height() + 6
            y += 10
        surf.blit(fi.render("(walk away to close)", True, (150, 140, 118)),
                  (x0, y + 8))


def _wrap(text, font, maxw):
    out, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if font.size(trial)[0] <= maxw:
            line = trial
        else:
            if line:
                out.append(line)
            line = word
    if line:
        out.append(line)
    return out
