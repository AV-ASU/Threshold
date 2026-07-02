"""Floating, non-modal NPC speech (2026-07 sound overhaul).

Casual talkable-NPC lines rise as a caption over the SPEAKER'S HEAD
instead of dropping the cinematic modal band, so the world keeps
running while someone talks to you: the cult still walks its errands,
the King still closes, you can still move and look. It reuses the
dialogue markup parser (colour/voice tags, letter-by-letter reveal)
but is otherwise its own tiny state machine.

What floats (Game routes it, DialogueBox.show decides): a line WITH a
named speaker, an NPC portrait (not the narrator), no choice, no
on_complete callback, reached through the interact path. Narrator
beats, evidence, choices, the mutated-local infested portrait, and any
scripted beat with a completion callback stay MODAL -- those want the
frozen world and the full box.

Advance: auto after a page's read-time, or E while standing near the
speaker. on_complete fires when the queue empties. Floats are never
sight-gated -- a voice you can hear should show even at the edge of
the cone.
"""
import math
import pygame

from constants import SCREEN_W, SCREEN_H, C_WHITE, C_GOLD
from ui.dialog import parse_dialogue


class FloatSpeech:
    def __init__(self, audio, fonts):
        self.audio = audio
        self.fonts = fonts
        self.active = False
        self.speaker = None          # the NPC the caption tracks
        self.name = ""
        self.pages = []              # list[list[DialogueGlyph]]
        self.page_idx = 0
        self.revealed = 0
        self.timer = 0.0
        self.hold_t = 0.0            # read-time countdown once fully revealed
        self.voice = "blip_mid"
        self.color = C_WHITE
        self.on_complete = None
        self.chars_per_sec = 34

    def begin(self, speaker, pages, name="", voice="blip_mid",
              color=C_WHITE, on_complete=None):
        """Start (or replace) a floating conversation over `speaker`.
        `pages` is a list of raw markup strings."""
        if isinstance(pages, str):
            pages = [pages]
        self.pages = [parse_dialogue(p, default_color=color,
                                     default_voice=voice) for p in pages]
        if not self.pages:
            if on_complete:
                on_complete()
            return
        self.speaker = speaker
        self.name = name
        self.voice = voice
        self.color = color
        self.on_complete = on_complete
        self.page_idx = 0
        self.revealed = 0
        self.timer = 0.0
        self.hold_t = 0.0
        self.active = True
        self.audio.play("cursor", 0.4)

    def _page(self):
        return self.pages[self.page_idx]

    def _read_time(self):
        """How long a fully-revealed page lingers before auto-advancing
        -- scaled to its length so a long line gets read."""
        n = len(self._page())
        return max(1.6, min(6.0, 1.2 + n / 26.0))

    def update(self, dt, game):
        if not self.active:
            return
        # The speaker walked off-scene / died -> drop the caption.
        sp = self.speaker
        if sp is not None and (not getattr(sp, "alive", True)
                               or getattr(sp, "_is_corpse", False)):
            self._finish()
            return
        page = self._page()
        if self.revealed < len(page):
            self.timer += dt
            while self.revealed < len(page) and self.timer > 0:
                g = page[self.revealed]
                if g.speed >= 999:
                    self.revealed += 1
                    continue
                step = 1.0 / (self.chars_per_sec * max(0.05, g.speed))
                if self.timer >= step:
                    self.timer -= step
                    if g.ch.strip() and self.revealed % 2 == 0:
                        self.audio.play(g.voice or self.voice, 0.5)
                    self.revealed += 1
                    if g.pause_after > 0:
                        self.timer = -g.pause_after
                else:
                    break
            if self.revealed >= len(page):
                self.hold_t = self._read_time()
            return
        # Fully revealed: hold for read-time, then auto-advance.
        self.hold_t -= dt
        if self.hold_t <= 0.0:
            self._advance()

    def advance_from_input(self, game):
        """E near the speaker: skip the reveal, else next page. Returns
        True if it consumed the press (so the interact path stops)."""
        if not self.active or self.speaker is None:
            return False
        p = self.speaker
        if math.hypot(p.x - game.player.x, p.y - game.player.y) > 52:
            return False
        page = self._page()
        if self.revealed < len(page):
            self.revealed = len(page)
            self.hold_t = self._read_time()
        else:
            self._advance()
        return True

    def _advance(self):
        self.page_idx += 1
        if self.page_idx < len(self.pages):
            self.revealed = 0
            self.timer = 0.0
            self.hold_t = 0.0
            self.audio.play("cursor", 0.4)
        else:
            self._finish()

    def _finish(self):
        self.active = False
        self.speaker = None
        cb = self.on_complete
        self.on_complete = None
        if cb:
            cb()

    def draw(self, surf, game):
        if not self.active or self.speaker is None:
            return
        sp = self.speaker
        # Anchor over the speaker's head, in screen space. Under tilt the
        # camera projects with a height lift; flat view falls back to the
        # cam offset. Not sight-gated on purpose.
        cam = getattr(game, "camera", None)
        if cam is not None and game._tilt_on():
            hx, hy = cam.project(sp.x, sp.y, 34)
        else:
            hx = int(sp.x - game.cam_x)
            hy = int(sp.y - game.cam_y) - 40
        page = self._page()
        # Wrap the revealed glyphs into lines (word-aware), then draw a
        # soft plate behind them and the caption on top, centred over
        # the head and clamped on-screen.
        font = self.fonts.get("serif_sm", self.fonts["serif"])
        max_w = 240
        space_w = font.size(" ")[0]
        lines = [[]]
        line_w = [0]
        word = []
        word_w = 0

        def flush_word():
            nonlocal word, word_w
            if not word:
                return
            add = word_w + (space_w if lines[-1] else 0)
            if line_w[-1] + add > max_w and lines[-1]:
                lines.append([])
                line_w.append(0)
                add = word_w
            elif lines[-1]:
                lines[-1].append((" ", font, C_WHITE))
            lines[-1].extend(word)
            line_w[-1] += add
            word = []
            word_w = 0

        for i in range(self.revealed):
            g = page[i]
            if g.ch == "":
                continue
            if g.ch == " ":
                flush_word()
                continue
            word.append((g.ch, self.fonts.get(g.font_key, font), g.color))
            word_w += self.fonts.get(g.font_key, font).size(g.ch)[0]
        flush_word()
        if not any(lines):
            lines = [[]]
        lh = font.get_linesize()
        name_h = lh if self.name else 0
        block_h = name_h + lh * len(lines) + 10
        name_w = font.size(self.name)[0] if self.name else 0
        block_w = min(max_w + 40, max(max(line_w), name_w)) + 16
        bx = int(hx - block_w / 2)
        by = int(hy - block_h - 6)
        bx = max(6, min(SCREEN_W - block_w - 6, bx))
        by = max(6, min(SCREEN_H - block_h - 6, by))
        plate = pygame.Surface((block_w, block_h), pygame.SRCALPHA)
        plate.fill((12, 11, 16, 180))
        surf.blit(plate, (bx, by))
        pygame.draw.line(surf, (70, 64, 84), (bx, by), (bx + block_w, by))
        # a little stem pointing down at the speaker (only when the plate
        # actually sits above the head -- clamping can shove it aside)
        stem_x = max(bx + 6, min(bx + block_w - 6, hx))
        pygame.draw.polygon(surf, (12, 11, 16),
                            [(stem_x - 5, by + block_h),
                             (stem_x + 5, by + block_h),
                             (stem_x, by + block_h + 6)])
        cy = by + 5
        if self.name:
            nm = font.render(self.name, True, C_GOLD)
            surf.blit(nm, (bx + 8, cy))
            cy += lh
        for ln in lines:
            cx = bx + 8
            for ch, f, col in ln:
                surf.blit(f.render(ch, True, col), (cx, cy))
                cx += f.size(ch)[0]
            cy += lh
