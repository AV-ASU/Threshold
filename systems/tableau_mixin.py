"""Close-up examine TABLEAUX -- the Game-side state machine.

A tableau is a modal close-up (the art lives in `ui/tableau.py`): the world
freezes, an animated close-up draws, and a menu of options mutates it live.
Wired into Game like the flashback cutscene: `_tableau is not None` freezes the
world (`world_frozen`), `_tick_tableau` animates it, `_draw_tableau` paints it
over everything, and `handle_event` routes input to `_tableau_input` while it
is up. The pilot is the bedroom writing desk (the pistol + the case file);
`ui/tableau.draw_desk_tableau` is its art. New tableaux add an art fn there and
an opener here. The face-across-a-table principal talks (Sable's reception
desk, Vane's office, Hettie's counter, Crane's lectern, Toby's little table,
and Mara's confrontation at the Sign Chamber, the seat with the REVEAL: she
opens as one more hooded mask of the congregation, listed as one of them,
until the greet's reveal beat lifts the mask away)
HOST a live Conversation instead of a fixed option list:
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
                        draw_crane_tableau, draw_toby_tableau,
                        draw_talk_tableau, draw_altar_tableau,
                        draw_mara_tableau)

_STRIP = re.compile(r"\[/?c(=\w+)?\]")


def _plain(s):
    return _STRIP.sub("", s)


# Each close-up's ROOM TONE (the #2b sound pass, 2026-07): a quiet bed
# looped on the ambient channel while the tableau is up, because the
# world-freeze also freezes the scene's scheduled ambients and every
# close-up sat in dead air. (cue_name, volume); the ONE kind with no
# entry is SILENT ON PURPOSE -- Mara's confrontation plays in the
# force_silence _mara_voice lays down (silence is a move).
_TABLEAU_TONES = {
    "sable":  ("fan_air", 0.9),       # the ceiling fan's warm push
    "vane":   ("window_wind", 0.9),   # thin cold wind at the glass
    "hettie": ("bulb_hum", 0.9),      # her one kept bulb, wavering
    "crane":  ("nave_air", 0.9),      # the empty church's volume
    "toby":   ("corn_hiss", 0.9),     # the dead stalks past his window
    "talk":   ("talk_breath", 1.0),   # his breathing, behind the wood
    "altar":  ("altar_air", 1.0),     # the tritone pressure of the room
    "desk":   ("desk_air", 0.9),      # the Arcadia being quiet at you
}


class TableauMixin:
    # ------------------------------------------------------------------ open
    def _tableau_open_audio(self, kind):
        """The close-up's soundscape: `lean_in` (the world holding its
        breath as the frame closes) for the seats + the desk, and the
        kind's room tone. THE TALK skips the intake (the grab's own cues
        just fired; his breathing is the whole event) and THE PEDESTAL
        keeps its low_pulse in place of it."""
        if kind not in ("talk", "altar"):
            self.audio.play("lean_in", 0.55)
        tone = _TABLEAU_TONES.get(kind)
        if tone is not None:
            self.audio.room_tone(tone[0], tone[1])

    def _open_desk_tableau(self):
        """The spare-room writing desk: pistol + flashlight + case file
        under the lamp (the PI's own kit, laid out the night he checked
        in; the flashlight moved here from the woodshed in the 2026-07
        light pass -- light is the game's spine, so the player's hand on
        it starts in the opening close-up)."""
        self._tableau = {
            "kind": "desk",
            "t": 0.0,
            "cursor": 0,
            "reading": None,
            "state": {
                "gun_present": not self.save.flag("desk_pistol_taken"),
                "fl_present": not self.save.flag("desk_flashlight_taken"),
            },
        }
        self._tableau_open_audio("desk")

    def _close_tableau(self):
        self._tableau = None
        self.audio.room_tone(None)

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
        self._tableau_open_audio("sable")
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
        self._tableau_open_audio("vane")
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
        self._tableau_open_audio("hettie")
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
        self._tableau_open_audio("crane")
        from ui.conversation import open_conversation
        from scenes.dialogue import CRANE_CONVO
        open_conversation(self, npc, CRANE_CONVO, tableau=True)

    def _crane_tableau_state(self):
        """The close-up's live state: the press fork, latched for good by
        `preacher_doomed` (`_crane_provoked`). Mirrors `_crane_prompt` so
        the pose and the framing line always tell the same story."""
        return {"doomed": self.save.flag("preacher_doomed")}

    # ----------------------------------------------------- Toby conversation
    def _open_toby_tableau(self, npc):
        """Toby across the little table, PRESENTED as a frozen close-up: the
        one almost-normal room in Brimley. Plain daylight, his drawings
        taped to the wall, the closet door with its own drawing, the toy
        radio, crayons on the table. His idle watches the corn line out the
        window (the framing line made pose); the procession drawing goes up
        once he has told what he saw, and his worried brows level out once
        the PI has made the promise."""
        self._tableau = {
            "kind": "toby", "t": 0.0, "npc": npc,
            "caption": None, "menu": None,
        }
        self._tableau_open_audio("toby")
        from ui.conversation import open_conversation
        from scenes.dialogue import TOBY_CONVO
        open_conversation(self, npc, TOBY_CONVO, tableau=True)

    def _toby_tableau_state(self):
        """The room's live state: the procession drawing hangs once he has
        told it (toby_told, the photo exchange), and the worried brow slant
        levels once the PI has promised (the holding_up exchange). The
        window-watch is idle-driven and added at draw time."""
        return {
            "drawing_present": self.save.flag("toby_told"),
            "believed": self.save.flag("convo_toby_holding_up_asked"),
        }

    # ----------------------------------------------------- Mara conversation
    def _open_mara_tableau(self, npc):
        """Mara's confrontation (the last #2b seat), PRESENTED as a frozen
        close-up with the rite still running at her back. She opens as ONE
        OF THEM: the carved mask and hood of the congregation fill the
        frame, and the caption lists her as one of them, until the greet's
        reveal beat lifts the mask away (`_mara_unmask`) and the listing
        turns to her name. The talk is MARA_CONVO in tableau mode; the
        close-up reads the confrontation's turns live (`lucid` drops her
        eyes to her ruined hands, `named` closes her fist on the PI's
        coat and stirs the rank)."""
        self._tableau = {
            "kind": "mara", "t": 0.0, "npc": npc,
            "caption": None, "menu": None, "state": {"unmask_t": None},
        }
        # No lean_in, no room tone: _mara_voice just force-silenced the
        # room, and her confrontation plays inside that silence.
        from ui.conversation import open_conversation
        from scenes.well import MARA_CONVO
        open_conversation(self, npc, MARA_CONVO, tableau=True)

    def _mara_unmask(self):
        """The reveal beat (fired by MARA_CONVO's greet): she lifts the
        carved mask away. Latches the run flag (the caption listing reads
        it) and stamps the close-up's animation clock."""
        self.save.set_flag("mara_unmasked", True)
        tb = self._tableau
        if tb is not None and tb.get("kind") == "mara":
            tb["state"]["unmask_t"] = tb["t"]
        self.audio.play("wood_creak", 0.32)
        self.audio.play("low_pulse", 0.3)

    def _mara_tableau_state(self):
        """The close-up's live state: the confrontation's turns, as save
        flags. `lucid` is the father card's slip (her eyes drop to her
        hands); `named` is the name-beat (her fist on your coat, the rank
        stirring). The unmask progress is tableau-local (`unmask_t`)."""
        return {
            "unmasked": self.save.flag("mara_unmasked"),
            "lucid": self.save.flag("mara_lucid"),
            "named": self.save.flag("mara_named"),
        }

    # ------------------------------------------------------------- THE TALK
    def _open_talk_tableau(self, on_done):
        """The first cult grab of a run, PRESENTED as the closest close-up
        in the game: the carved mask fills the frame, his hand is on your
        shoulder at the corner, and he leans in the whole time. NOT a
        Conversation: a scripted caption chain (the locked warning lines)
        with ONE choice when the PI carries the revolver: hold still, or
        reach for it and learn his other hand is already there. Escape
        never aborts it (you do not walk out of the grip; it pages).
        `on_done` is _cult_talk's release: the stand-down, the grace, the
        note, the reaction caption. It ALWAYS runs, on every path."""
        tb = {
            "kind": "talk", "t": 0.0, "npc": None,
            "caption": None, "menu": None, "state": {"reaching": False},
        }
        self._tableau = tb
        self._tableau_open_audio("talk")
        has_gun = (self.player is not None
                   and self.player.inventory.has("pistol"))

        def _fin():
            self._close_tableau()
            on_done()

        def _run_line():
            self._tableau_caption("npc", "", "\"Run.\"", _fin)

        def _hold():
            self._tableau_caption("pi", "", "(You hold still.)", _run_line)

        def _reach():
            tb["state"]["reaching"] = True
            self._tableau_caption(
                "pi", "",
                "(Your hand starts for your coat. His other hand is "
                "already on your wrist. Resting there. That is all it "
                "does.)",
                lambda: self._tableau_caption(
                    "npc", "", "None of that, now. We're only talking.",
                    _run_line))

        def _choice():
            if not has_gun:
                _run_line()
                return
            self._tableau_choices(
                "He waits, hand where it landed.",
                ["Hold still.", "Reach for the revolver."],
                lambda i: (_hold if i == 0 else _reach)())

        def _warn():
            self._tableau_caption(
                "npc", "",
                "\"Hey. You go back to your hotel room if you know what's "
                "good for you.\"", _choice)

        self._tableau_caption(
            "pi", "",
            "[c=dim]The hand lands on your shoulder before you hear him "
            "coming. The grip is friendly. Nothing else about it is.[/c]",
            _warn)

    # ---------------------------------------------------- THE PEDESTAL (altar)
    def _open_altar_tableau(self, on_lift, on_break):
        """The Sign Chamber altar, PRESENTED as an object close-up: the
        Pallid Mask on the hewn stone under the daubed Sign, the kneeling
        congregation behind, His face warm and gazing. The two instincts
        (NARRATIVE §8) ride on top as the tableau menu: LIFT the mask (the
        keystone, the Spread/Seal fork) or TEAR IT DOWN (BREAK -- the trap,
        the rite is the only lid; `on_break` runs `_play_ending`). Backing
        out (Escape) leaves the mask on the altar, re-interactable."""
        self._tableau = {
            "kind": "altar", "t": 0.0, "npc": None,
            "caption": None, "menu": None, "state": {},
        }
        self.audio.play("low_pulse", 0.5)
        self._tableau_open_audio("altar")

        def _pick(idx):
            self._close_tableau()
            (on_lift if idx == 0 else on_break)()

        self._tableau_choices(
            "The whole machine of it, here in reach.",
            ["Lift the mask.", "Tear it down. End this."], _pick)

    # The two presentation hooks the Conversation calls in tableau mode.
    def _tableau_caption(self, who, name, text, on_complete):
        tb = self._tableau
        if tb is None:
            return
        tb["caption"] = {"who": who, "name": name, "text": text,
                         "cb": on_complete}
        tb["menu"] = None

    def _tableau_choices(self, prompt, labels, pick, spent=None):
        tb = self._tableau
        if tb is None:
            return
        # The cursor opens on the first FRESH option: spent rows stay
        # pickable (a re-read is allowed) but a spammed E should never
        # land on one by default. `opened` stamps the tableau clock so
        # the confirm guard can swallow the same press chain that opened
        # the menu (CONVO_MENU_GUARD).
        cur = 0
        if spent:
            for i, s in enumerate(spent):
                if not s:
                    cur = i
                    break
        tb["menu"] = {"prompt": prompt, "labels": list(labels),
                      "pick": pick, "cursor": cur,
                      "spent": list(spent) if spent else None,
                      "opened": tb.get("t", 0.0)}
        tb["caption"] = None

    def _convo_tableau_input(self, ev, tb):
        """Input for any caption/menu tableau (the principal seats + the
        Talk): E advances the caption, up/down/E works the menu, Escape
        ends a SEAT's talk and drops the close-up. Two exceptions: THE
        TALK never aborts (you do not walk out of the grip, so Escape
        pages like E; its release must always run), and MARA's captions
        page too (the calling-out is not walked out of mid-line, so the
        greet's reveal always lands; her menu still takes Escape as
        "Say nothing.")."""
        esc_pages = (tb["kind"] == "talk"
                     or (tb["kind"] == "mara"
                         and tb.get("caption") is not None))
        if ev.key == pygame.K_ESCAPE and not esc_pages:
            if getattr(self, "_convo", None) is not None:
                self._convo.active = False
            self._close_tableau()
            return
        cap, menu = tb.get("caption"), tb.get("menu")
        adv = (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE)
        if cap is not None:
            if ev.key in adv or (esc_pages and ev.key == pygame.K_ESCAPE):
                cb = cap["cb"]
                tb["caption"] = None
                if cb:
                    cb()
            return
        if menu is not None:
            n = len(menu["labels"])
            if ev.key in (pygame.K_UP, pygame.K_w):
                menu["cursor"] = (menu["cursor"] - 1) % n
                self.audio.play("cursor", 0.45)
            elif ev.key in (pygame.K_DOWN, pygame.K_s):
                menu["cursor"] = (menu["cursor"] + 1) % n
                self.audio.play("cursor", 0.45)
            elif ev.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                # The E that skimmed the last caption opens this menu in
                # the same synchronous chain; a held/spammed E then picked
                # an option the player never read. Swallow confirms for
                # the menu's first beat (arrows still move immediately).
                from systems.config import CONVO_MENU_GUARD
                if tb.get("t", 0.0) - menu.get("opened", 0.0) < CONVO_MENU_GUARD:
                    return
                self.audio.play("confirm", 0.45)
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
        if tb["state"].get("fl_present"):
            opts.append(("Take the flashlight", self._tableau_take_flashlight))
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

    def _tableau_take_flashlight(self):
        tb = self._tableau
        tb["state"]["fl_present"] = False
        self.save.set_flag("desk_flashlight_taken", True)
        self.player.inventory.add("flashlight", 1)
        self.audio.play("pickup", 0.7)
        self.show_notice("Your flashlight. Press [F] in the dark, "
                         "but light draws the eye.")
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
                "MARA BLAINE, 24. Cut ties, drove north, quit calling "
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
        if tb["kind"] in ("sable", "vane", "hettie", "crane", "toby",
                          "mara", "talk", "altar"):
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
            self.audio.play("cursor", 0.45)
        elif ev.key in (pygame.K_DOWN, pygame.K_s):
            tb["cursor"] = (tb["cursor"] + 1) % len(opts)
            self.audio.play("cursor", 0.45)
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
        if tb["kind"] == "toby":
            self._draw_toby_tableau(surf, tb)
            return
        if tb["kind"] == "mara":
            self._draw_mara_tableau(surf, tb)
            return
        if tb["kind"] == "talk":
            draw_talk_tableau(surf, tb["t"], tb["state"])
            if tb.get("caption") is not None:
                self._draw_tableau_caption(surf, tb["caption"])
            elif tb.get("menu") is not None:
                self._draw_tableau_menu(surf, tb["menu"])
            return
        if tb["kind"] == "altar":
            draw_altar_tableau(surf, tb["t"], tb["state"])
            if tb.get("menu") is not None:
                self._draw_tableau_menu(surf, tb["menu"])
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

    def _draw_toby_tableau(self, surf, tb):
        # His idle watch of the corn line: every few seconds his eyes go to
        # the window, hold, and come back. Time-driven, eased both ways.
        ph = tb["t"] % 7.4
        watch = 0.0
        if 5.0 <= ph < 6.8:
            watch = min(1.0, (ph - 5.0) / 0.4, (6.8 - ph) / 0.4)
        st = self._toby_tableau_state()
        st["watch"] = watch
        draw_toby_tableau(surf, tb["t"], st)
        if tb.get("caption") is not None:
            self._draw_tableau_caption(surf, tb["caption"])
        elif tb.get("menu") is not None:
            self._draw_tableau_menu(surf, tb["menu"])

    def _draw_mara_tableau(self, surf, tb):
        # The unmask animates from the reveal beat's stamp (worn until it
        # fires; a re-opened talk after the reveal shows her bare-faced
        # from the first frame). Her idle, once bare: the glance pulled
        # back toward the rite behind her, eased both ways -- suspended
        # while a turn of the talk holds her (lucid/named).
        st = self._mara_tableau_state()
        ut = tb["state"].get("unmask_t")
        if not st.pop("unmasked"):
            u = 0.0
        elif ut is None:
            u = 1.0
        else:
            u = min(1.0, (tb["t"] - ut) / 1.6)
        st["unmask"] = u
        glance = 0.0
        if u >= 1.0 and not (st["lucid"] or st["named"]):
            ph = tb["t"] % 7.8
            if 5.6 <= ph < 7.3:
                glance = min(1.0, (ph - 5.6) / 0.4, (7.3 - ph) / 0.4)
        st["glance"] = glance
        draw_mara_tableau(surf, tb["t"], st)
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
        spent = menu.get("spent")
        for i, label in enumerate(menu["labels"]):
            sel = (i == cur)
            if sel:
                pygame.draw.rect(surf, (200, 162, 84), (x0 - 16, y + 4, 6, 24))
                col = (246, 230, 160)
            else:
                col = (150, 146, 132) if i == last else (176, 168, 146)
                # A SPENT question (asked before, still re-askable) sinks
                # into the page so the fresh ones read at a glance.
                if spent and i < len(spent) and spent[i] and i != last:
                    col = (118, 114, 102)
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
