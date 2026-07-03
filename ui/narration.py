"""Non-modal narration: the PI's interior voice as a lower-third caption.

The old cinematic band (portrait box + frozen world) is retired for
world-object text: examining a corpse, flipping the register, reading a
carving, every `_evidence` beat. Those lines now rise as a frameless
subtitle low on the screen while the WORLD KEEPS RUNNING: the Clerk
keeps watching you read his register, the cult keeps walking its
errands, visibility keeps ticking. Reading is diegetic time now, not a
pause menu.

What lands here (DialogueBox.show routes it): a line with NO speaker
and a narrator/absent portrait, no choice, no completion callback.
Named NPC speech floats over the speaker's head (ui/float_speech.py);
choices, infested portraits, and scripted beats with on_complete keep
the modal band and the frozen world.

Advance: auto after a read-time hold, or E anywhere (the caption owns
the press before hides/NPCs so a skim never triggers something else).
"""
import math
import pygame

from constants import SCREEN_W, SCREEN_H, C_WHITE, C_GOLD
from ui.dialog import parse_dialogue


class Narration:
    def __init__(self, audio, fonts):
        self.audio = audio
        self.fonts = fonts
        self.active = False
        self.pages = []              # list[list[DialogueGlyph]]
        self.page_idx = 0
        self.revealed = 0
        self.timer = 0.0
        self.hold_t = 0.0            # read-time countdown once revealed
        self.voice = "blip_soft"
        self.color = C_WHITE
        self.on_complete = None
        self.chars_per_sec = 40

    def begin(self, pages, voice="blip_soft", color=C_WHITE,
              on_complete=None):
        if isinstance(pages, str):
            pages = [pages]
        self.pages = [parse_dialogue(p, default_color=color,
                                     default_voice=voice) for p in pages]
        if not self.pages:
            if on_complete:
                on_complete()
            return
        self.voice = voice
        self.color = color
        self.on_complete = on_complete
        self.page_idx = 0
        self.revealed = 0
        self.timer = 0.0
        self.hold_t = 0.0
        self.active = True

    def clear(self):
        """Drop the caption without firing on_complete (scene loads,
        death, quit-to-title)."""
        self.active = False
        self.pages = []
        self.on_complete = None

    def _page(self):
        return self.pages[self.page_idx]

    def _read_time(self):
        """How long a fully revealed page lingers before auto-advancing.
        Narration pages run long (the register, a corpse), so the ceiling
        sits higher than the float captions'."""
        n = len(self._page())
        return max(1.8, min(8.0, 1.4 + n / 24.0))

    def update(self, dt):
        if not self.active:
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
                    if g.ch.strip() and self.revealed % 3 == 0:
                        self.audio.play(g.voice or self.voice, 0.35)
                    self.revealed += 1
                    if g.pause_after > 0:
                        self.timer = -g.pause_after
                else:
                    break
            if self.revealed >= len(page):
                self.hold_t = self._read_time()
            return
        self.hold_t -= dt
        if self.hold_t <= 0.0:
            self._advance()

    def advance_from_input(self):
        """E: skip the reveal, else next page. Returns True if it
        consumed the press (so try_interact stops)."""
        if not self.active:
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
            self.audio.play("cursor", 0.35)
        else:
            self.active = False
            cb = self.on_complete
            self.on_complete = None
            if cb:
                cb()

    def draw(self, surf):
        if not self.active:
            return
        page = self._page()
        font = self.fonts.get("serif", self.fonts["serif_sm"])
        max_w = int(SCREEN_W * 0.56)
        space_w = font.size(" ")[0]
        # Word-wrap the revealed glyphs into centred lines.
        lines = [[]]
        line_w = [0]
        word = []
        word_w = 0

        def flush_word(force_newline=False):
            nonlocal word, word_w
            if word:
                add = word_w + (space_w if lines[-1] else 0)
                if line_w[-1] + add > max_w and lines[-1]:
                    lines.append([])
                    line_w.append(0)
                    add = word_w
                elif lines[-1]:
                    lines[-1].append((" ", font, self.color))
                    line_w[-1] += space_w
                lines[-1].extend(word)
                line_w[-1] += word_w
                word = []
                word_w = 0
            if force_newline and lines[-1]:
                lines.append([])
                line_w.append(0)

        for i in range(self.revealed):
            g = page[i]
            if g.ch == "":
                continue
            if g.ch == "\n":
                flush_word(force_newline=True)
                continue
            if g.ch == " ":
                flush_word()
                continue
            f = self.fonts.get(g.font_key, font)
            word.append((g.ch, f, g.color))
            word_w += f.size(g.ch)[0]
        flush_word()
        while len(lines) > 1 and not lines[-1]:
            lines.pop()
            line_w.pop()
        lh = font.get_linesize()
        block_h = lh * len(lines)
        base_y = SCREEN_H - 64 - block_h
        # A soft full-width legibility wash behind the text: darkest at
        # the text band, feathering to nothing above and below. No frame,
        # no portrait, no panel.
        pad = 18
        wash_h = block_h + pad * 2
        wash = pygame.Surface((SCREEN_W, wash_h), pygame.SRCALPHA)
        for i in range(wash_h):
            f = i / max(1, wash_h - 1)
            a = int(150 * math.sin(f * math.pi) ** 0.8)
            wash.fill((8, 7, 12, a), (0, i, SCREEN_W, 1))
        surf.blit(wash, (0, base_y - pad))
        cy = base_y
        for li, ln in enumerate(lines):
            cx = (SCREEN_W - line_w[li]) // 2
            for ch, f, col in ln:
                surf.blit(f.render(ch, True, col), (cx, cy))
                cx += f.size(ch)[0]
            cy += lh
        # A small gold tick once the page is read and more pages wait.
        if (self.revealed >= len(page)
                and self.page_idx < len(self.pages) - 1):
            t = pygame.time.get_ticks() / 250.0
            yo = int(math.sin(t) * 2)
            tx = SCREEN_W // 2
            ty = base_y + block_h + 8 + yo
            pygame.draw.polygon(surf, C_GOLD,
                                [(tx - 5, ty), (tx + 5, ty), (tx, ty + 6)])
