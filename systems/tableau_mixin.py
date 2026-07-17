"""Close-up examine TABLEAUX -- the Game-side state machine.

A tableau is a modal close-up (the art lives in `ui/tableau.py`): the world
freezes, an animated close-up draws, and a menu of options mutates it live.
Wired into Game like the flashback cutscene: `_tableau is not None` freezes the
world (`world_frozen`), `_tick_tableau` animates it, `_draw_tableau` paints it
over everything, and `handle_event` routes input to `_tableau_input` while it
is up. The pilot is the bedroom writing desk (the pistol + the case file);
`ui/tableau.draw_desk_tableau` is its art. New tableaux add an art fn there and
an opener here. The face-across-a-table principal talks (Sable's reception
desk, Vane's office) HOST a live Conversation instead of a fixed option list:
`open_conversation(..., tableau=True)` routes its spoken beats to
`_tableau_caption` and its question menu to `_tableau_choices`, and the art
reads the save flags so the close-up carries what the talk has earned.

Player-facing text (the menu labels + the case-file lines) is mirrored in
DIALOGUE.md Part B, per the contract.
"""
import re
import pygame

from ui.tableau import (draw_desk_tableau, draw_sable_tableau,
                        draw_vane_tableau, draw_hettie_tableau,
                        draw_crane_tableau)

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

    # ---------------------------------------------------- Sable conversation
    def _open_sable_tableau(self, npc):
        """Mr. Sable's reception-desk talk, PRESENTED as a frozen close-up:
        the world holds, his host face animates, and the ask-verb conversation
        (SABLE_CONVO) renders its beats as the tableau's caption and its menu
        as the option panel. The photo + the Invitation appear on the desk
        live as the talk earns them (the art reads the save flags)."""
        self._tableau = {
            "kind": "sable", "t": 0.0, "npc": npc,
            "caption": None, "menu": None,
        }
        self.audio.play("blip_low", 0.4)
        from ui.conversation import open_conversation
        from scenes.dialogue import SABLE_CONVO
        open_conversation(self, npc, SABLE_CONVO, tableau=True)

    # ----------------------------------------------------- Vane conversation
    def _open_vane_tableau(self, npc):
        """Sheriff Vane's office talk, PRESENTED as a frozen close-up: cold
        window daylight, the JAN 15 calendar, the cell-bars sliver, the gun
        cabinet in the back. His POSE reads the hidden despair ledger the
        same way the menu's framing line does (mood, never a number), and
        the desk carries what the talk has earned (the newspaper he was
        given, the cabinet he opened)."""
        self._tableau = {
            "kind": "vane", "t": 0.0, "npc": npc,
            "caption": None, "menu": None,
        }
        self.audio.play("blip_low", 0.4)
        from ui.conversation import open_conversation
        from scenes.dialogue import VANE_CONVO
        open_conversation(self, npc, VANE_CONVO, tableau=True)

    def _vane_tableau_state(self):
        """The close-up's live state. The mood thresholds MIRROR the menu
        framing (`_vane_prompt`, scenes/dialogue.py): despair at net >= 2
        (he is looking at the window, not at you), hope at net <= -1 (the
        hooked-out chair), else he waits you out. Props are the earned
        flags: the paper exchange's once-flag, the opened cabinet."""
        net = int(self.save.arg("vane_despair", 0) or 0)
        mood = ("despair" if net >= 2
                else "hope" if net <= -1 else "neutral")
        return {
            "mood": mood,
            "paper_present": self.save.flag("convo_vane_paper_asked"),
            "cache_open": self.save.flag("vane_gave_cache"),
        }

    # --------------------------------------------------- Hettie conversation
    def _open_hettie_tableau(self, npc):
        """Hettie's shop counter, PRESENTED as a frozen close-up: the gutted
        shelves with their dust-ghosts and the one tin left, the till empty
        since the new year, her ONE kept bulb burning over the counter. Her
        idle keeps glancing at the door (the framing line made pose), and
        the counter carries what the talk has earned: Mara's tab leaves the
        spike when it is lifted, the traded newspaper lies open after."""
        self._tableau = {
            "kind": "hettie", "t": 0.0, "npc": npc,
            "caption": None, "menu": None,
        }
        self.audio.play("blip_low", 0.4)
        from ui.conversation import open_conversation
        from scenes.dialogue import HETTIE_CONVO
        open_conversation(self, npc, HETTIE_CONVO, tableau=True)

    def _hettie_tableau_state(self):
        """The counter's live state: Mara's tab stays curled on the spike
        until the receipt is taken (however it was earned), and the traded
        newspaper lies open once the barter has happened. The door glance
        is idle-driven and added at draw time, not state."""
        return {
            "tab_present": not self.save.flag("evidence_maras_receipt"),
            "paper_present": self.save.flag("newspaper_traded"),
        }

    # ---------------------------------------------------- Crane conversation
    def _open_crane_tableau(self, npc):
        """Rev. Crane at his lectern, PRESENTED as a frozen close-up: the
        chancel in candled dusk, the plain cross, the arched window, the
        bell rope dead at the frame's edge. His HANDS carry the fork
        the way the framing line does: folded over the lectern while he
        waits, gripping its corners once the press has latched."""
        self._tableau = {
            "kind": "crane", "t": 0.0, "npc": npc,
            "caption": None, "menu": None,
        }
        self.audio.play("blip_low", 0.4)
        from ui.conversation import open_conversation
        from scenes.dialogue import CRANE_CONVO
        open_conversation(self, npc, CRANE_CONVO, tableau=True)

    def _crane_tableau_state(self):
        """The close-up's live state: the press fork, latched for good by
        `preacher_doomed` (`_crane_provoked`). Mirrors `_crane_prompt` so
        the pose and the framing line always tell the same story."""
        return {"doomed": self.save.flag("preacher_doomed")}

    # The two presentation hooks the Conversation calls in tableau mode.
    def _tableau_caption(self, who, name, text, on_complete):
        tb = self._tableau
        if tb is None:
            return
        tb["caption"] = {"who": who, "name": name, "text": text,
                         "cb": on_complete}
        tb["menu"] = None

    def _tableau_choices(self, prompt, labels, pick):
        tb = self._tableau
        if tb is None:
            return
        tb["menu"] = {"prompt": prompt, "labels": list(labels),
                      "pick": pick, "cursor": 0}
        tb["caption"] = None

    def _convo_tableau_input(self, ev, tb):
        """Input for any conversation-hosting tableau (Sable, Vane): E
        advances the caption, up/down/E works the menu, Escape ends the
        talk and drops the close-up."""
        if ev.key == pygame.K_ESCAPE:
            if getattr(self, "_convo", None) is not None:
                self._convo.active = False
            self._close_tableau()
            return
        cap, menu = tb.get("caption"), tb.get("menu")
        if cap is not None:
            if ev.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                cb = cap["cb"]
                tb["caption"] = None
                if cb:
                    cb()
            return
        if menu is not None:
            n = len(menu["labels"])
            if ev.key in (pygame.K_UP, pygame.K_w):
                menu["cursor"] = (menu["cursor"] - 1) % n
                self.audio.play("blip_low", 0.3)
            elif ev.key in (pygame.K_DOWN, pygame.K_s):
                menu["cursor"] = (menu["cursor"] + 1) % n
                self.audio.play("blip_low", 0.3)
            elif ev.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                idx, pick = menu["cursor"], menu["pick"]
                tb["menu"] = None
                pick(idx)

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
        if tb["kind"] in ("sable", "vane", "hettie", "crane"):
            self._convo_tableau_input(ev, tb)
            return
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
        if tb["kind"] == "sable":
            self._draw_sable_tableau(surf, tb)
            return
        if tb["kind"] == "vane":
            self._draw_vane_tableau(surf, tb)
            return
        if tb["kind"] == "hettie":
            self._draw_hettie_tableau(surf, tb)
            return
        if tb["kind"] == "crane":
            self._draw_crane_tableau(surf, tb)
            return
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

    # ------------------------------------------------ Sable close-up drawing
    def _draw_sable_tableau(self, surf, tb):
        state = {
            "photo_present": self.save.flag("sable_showed_photo"),
            "envelope_present": self.save.flag("rite_envelope_given"),
        }
        draw_sable_tableau(surf, tb["t"], state)
        if tb.get("caption") is not None:
            self._draw_tableau_caption(surf, tb["caption"])
        elif tb.get("menu") is not None:
            self._draw_tableau_menu(surf, tb["menu"])

    def _draw_vane_tableau(self, surf, tb):
        draw_vane_tableau(surf, tb["t"], self._vane_tableau_state())
        if tb.get("caption") is not None:
            self._draw_tableau_caption(surf, tb["caption"])
        elif tb.get("menu") is not None:
            self._draw_tableau_menu(surf, tb["menu"])

    def _draw_hettie_tableau(self, surf, tb):
        # Her idle door-glance: every few seconds her head turns toward the
        # shop door, holds a beat, and comes back. Time-driven, eased both
        # ways; the rest of the state is the earned counter props.
        ph = tb["t"] % 6.8
        glance = 0.0
        if 4.8 <= ph < 6.4:
            glance = min(1.0, (ph - 4.8) / 0.35, (6.4 - ph) / 0.35)
        st = self._hettie_tableau_state()
        st["glance"] = glance
        draw_hettie_tableau(surf, tb["t"], st)
        if tb.get("caption") is not None:
            self._draw_tableau_caption(surf, tb["caption"])
        elif tb.get("menu") is not None:
            self._draw_tableau_menu(surf, tb["menu"])

    def _draw_crane_tableau(self, surf, tb):
        draw_crane_tableau(surf, tb["t"], self._crane_tableau_state())
        if tb.get("caption") is not None:
            self._draw_tableau_caption(surf, tb["caption"])
        elif tb.get("menu") is not None:
            self._draw_tableau_menu(surf, tb["menu"])

    def _draw_tableau_scrim(self, surf, top_frac):
        """A gradient darkening from `top_frac` down, so text reads over the
        counter without fully hiding Sable or the props."""
        W, H = surf.get_width(), surf.get_height()
        y0 = int(H * top_frac)
        scrim = pygame.Surface((W, H - y0), pygame.SRCALPHA)
        for yy in range(0, H - y0, 2):
            a = min(206, 40 + int(200 * yy / max(1, H - y0)))
            pygame.draw.rect(scrim, (6, 4, 3, a), (0, yy, W, 2))
        surf.blit(scrim, (0, y0))

    def _draw_tableau_caption(self, surf, cap):
        W, H = surf.get_width(), surf.get_height()
        self._draw_tableau_scrim(surf, 0.70)
        f = self.fonts["serif_lg"]
        fi = self.fonts["serif_it"]
        x0, y = 48, int(H * 0.745)
        dim = (cap["who"] == "pi") or ("[c=dim]" in cap["text"])
        col = (176, 168, 150) if dim else (232, 220, 196)
        if cap["name"]:
            surf.blit(fi.render(cap["name"], True, (202, 170, 98)), (x0, y - 28))
        for wln in _wrap(_plain(cap["text"]), f, int(W * 0.84)):
            surf.blit(f.render(wln, True, col), (x0, y))
            y += f.get_height() + 4
        surf.blit(fi.render("[E]", True, (150, 140, 118)), (W - 64, H - 42))

    def _draw_tableau_menu(self, surf, menu):
        W, H = surf.get_width(), surf.get_height()
        self._draw_tableau_scrim(surf, 0.50)
        pf = self.fonts["serif_it"]
        of = self.fonts["serif_lg"]
        x0, y = 48, int(H * 0.52)
        for pln in _wrap(_plain(menu["prompt"]), pf, int(W * 0.86)):
            surf.blit(pf.render(pln, True, (198, 186, 160)), (x0, y))
            y += pf.get_height() + 2
        y += 12
        cur = menu["cursor"]
        last = len(menu["labels"]) - 1
        for i, label in enumerate(menu["labels"]):
            sel = (i == cur)
            if sel:
                pygame.draw.rect(surf, (200, 162, 84), (x0 - 16, y + 4, 6, 24))
                col = (246, 230, 160)
            else:
                col = (150, 146, 132) if i == last else (176, 168, 146)
            surf.blit(of.render(("  " if sel else "   ") + _plain(label),
                                True, col), (x0, y))
            y += 34


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
