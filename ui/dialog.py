"""Animated, multi-style dialogue box."""
import time
import math
import random
import pygame
from constants import (
    SCREEN_W, SCREEN_H,
    C_WHITE, C_GOLD, C_RED, C_BLOOD, C_GREEN, C_BLUE, C_PURPLE,
    C_DIM, C_DIALOG_BG, C_PANEL_BORDER, C_BLACK,
)

NAMED_COLORS = {
    "white": C_WHITE, "red": C_RED, "blood": C_BLOOD,
    "blue": C_BLUE, "green": C_GREEN, "gold": C_GOLD,
    "purple": C_PURPLE, "dim": C_DIM, "black": C_BLACK,
}


class DialogueGlyph:
    __slots__ = ("ch","color","font_key","shake","glitch","speed","pause_after","voice")
    def __init__(self, ch, color, font_key, shake=False, glitch=False, speed=1.0, pause_after=0.0, voice=None):
        self.ch = ch
        self.color = color
        self.font_key = font_key
        self.shake = shake
        self.glitch = glitch
        self.speed = speed
        self.pause_after = pause_after
        self.voice = voice


def parse_dialogue(text, default_color=C_WHITE, default_font="md", default_voice="blip_mid"):
    glyphs = []
    color_stack = [default_color]
    font_stack = [default_font]
    speed_stack = [1.0]
    shake_stack = [False]
    glitch_stack = [False]
    voice_stack = [default_voice]
    i = 0
    while i < len(text):
        if text[i] == "[":
            end = text.find("]", i)
            if end == -1:
                glyphs.append(DialogueGlyph(text[i], color_stack[-1], font_stack[-1],
                                            shake_stack[-1], glitch_stack[-1], speed_stack[-1],
                                            voice=voice_stack[-1]))
                i += 1
                continue
            tag = text[i+1:end]
            i = end + 1
            if tag.startswith("c="):
                color_stack.append(NAMED_COLORS.get(tag[2:], default_color))
            elif tag == "/c":
                if len(color_stack) > 1: color_stack.pop()
            elif tag.startswith("f="):
                font_stack.append(tag[2:])
            elif tag == "/f":
                if len(font_stack) > 1: font_stack.pop()
            elif tag.startswith("s="):
                v = tag[2:]
                speed = {"slow": 0.4, "veryslow": 0.2, "fast": 2.0, "instant": 999}.get(v, 1.0)
                speed_stack.append(speed)
            elif tag == "/s":
                if len(speed_stack) > 1: speed_stack.pop()
            elif tag == "shake":
                shake_stack.append(True)
            elif tag == "/shake":
                if len(shake_stack) > 1: shake_stack.pop()
            elif tag == "glitch":
                glitch_stack.append(True)
            elif tag == "/glitch":
                if len(glitch_stack) > 1: glitch_stack.pop()
            elif tag.startswith("w="):
                try: pause = float(tag[2:])
                except ValueError: pause = 0.0
                if glyphs:
                    glyphs[-1].pause_after = pause
                else:
                    glyphs.append(DialogueGlyph(" ", color_stack[-1], font_stack[-1], pause_after=pause))
            elif tag == "silence":
                glyphs.append(DialogueGlyph("", color_stack[-1], font_stack[-1], voice="__silence__"))
            elif tag.startswith("voice="):
                voice_stack.append(tag[6:])
            elif tag == "/voice":
                if len(voice_stack) > 1: voice_stack.pop()
        else:
            ch = text[i]
            glyphs.append(DialogueGlyph(
                ch, color_stack[-1], font_stack[-1],
                shake=shake_stack[-1], glitch=glitch_stack[-1],
                speed=speed_stack[-1], voice=voice_stack[-1],
            ))
            i += 1
    return glyphs


class DialogueBox:
    GLITCH_CHARS = "@#$%&*<>?/\\|~^"

    def __init__(self, audio, fonts):
        self.audio = audio
        self.fonts = fonts
        self.active = False
        self.pages = []
        self.page_idx = 0
        self.glyphs = []
        self.revealed = 0
        self.timer = 0.0
        self.chars_per_sec = 38
        self.speaker_name = ""
        self.voice = "blip_mid"
        self.color = C_WHITE
        self.on_complete = None
        self.choices = None
        self.choice_idx = 0
        self.choice_callback = None
        self.portrait_kind = None

    def show(self, pages, speaker="", voice="blip_mid", color=C_WHITE, portrait=None, on_complete=None):
        if isinstance(pages, str):
            pages = [pages]
        self.pages = [parse_dialogue(p, default_color=color, default_voice=voice) for p in pages]
        self.page_idx = 0
        self.glyphs = self.pages[0]
        self.revealed = 0
        self.timer = 0.0
        self.speaker_name = speaker
        self.voice = voice
        self.color = color
        self.portrait_kind = portrait
        self.active = True
        self.on_complete = on_complete
        self.choices = None
        self.choice_callback = None
        self.audio.play("menu_open", 0.5)

    def show_choice(self, prompt, options, callback, speaker="", voice="blip_mid", portrait=None):
        self.show([prompt], speaker=speaker, voice=voice, portrait=portrait)
        self.choices = options
        self.choice_idx = 0
        self.choice_callback = callback

    def update(self, dt):
        if not self.active: return
        if self.revealed < len(self.glyphs):
            self.timer += dt
            while self.revealed < len(self.glyphs) and self.timer > 0:
                g = self.glyphs[self.revealed]
                if g.speed >= 999:
                    self.revealed += 1
                    continue
                step = 1.0 / (self.chars_per_sec * max(0.05, g.speed))
                if self.timer >= step:
                    self.timer -= step
                    if g.voice == "__silence__":
                        self.audio.force_silence()
                    elif g.ch.strip():
                        if self.revealed % 2 == 0:
                            self.audio.play(g.voice or self.voice, 0.6)
                    self.revealed += 1
                    if g.pause_after > 0:
                        self.timer = -g.pause_after
                else:
                    break

    def advance(self):
        if not self.active: return False
        if self.choices is not None:
            cb = self.choice_callback
            idx = self.choice_idx
            self.active = False
            self.choices = None
            self.choice_callback = None
            self.audio.play("confirm", 0.7)
            if cb: cb(idx)
            return True
        if self.revealed < len(self.glyphs):
            self.revealed = len(self.glyphs)
            return True
        self.page_idx += 1
        if self.page_idx < len(self.pages):
            self.glyphs = self.pages[self.page_idx]
            self.revealed = 0
            self.timer = 0.0
            self.audio.play("cursor", 0.5)
            return True
        self.active = False
        self.audio.play("menu_close", 0.5)
        cb = self.on_complete
        self.on_complete = None
        if cb: cb()
        return True

    def move_choice(self, dy):
        if self.choices is None: return
        self.choice_idx = (self.choice_idx + dy) % len(self.choices)
        self.audio.play("cursor", 0.6)

    def draw(self, surf):
        if not self.active: return
        box_h = 160
        box_y = SCREEN_H - box_h - 14
        box = pygame.Rect(20, box_y, SCREEN_W - 40, box_h)
        s = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
        s.fill((*C_DIALOG_BG, 232))
        surf.blit(s, box.topleft)
        pygame.draw.rect(surf, C_PANEL_BORDER, box, 2)
        portrait_x = box.x + 14
        portrait_y = box.y + 14
        portrait_size = 64
        prect = pygame.Rect(portrait_x, portrait_y, portrait_size, portrait_size)
        pygame.draw.rect(surf, (24, 22, 32), prect)
        pygame.draw.rect(surf, C_PANEL_BORDER, prect, 1)
        self._draw_portrait(surf, prect, self.portrait_kind)
        if self.speaker_name:
            name_surf = self.fonts["sm"].render(self.speaker_name, True, C_GOLD)
            surf.blit(name_surf, (portrait_x, portrait_y + portrait_size + 6))
        tx = portrait_x + portrait_size + 16
        ty = box.y + 16
        max_w = box.right - tx - 14
        self._draw_glyphs(surf, tx, ty, max_w)
        if self.choices is not None and self.revealed >= len(self.glyphs):
            self._draw_choices(surf, box)
        elif self.revealed >= len(self.glyphs):
            tri_t = pygame.time.get_ticks() / 250.0
            yo = int(math.sin(tri_t) * 2)
            tri = [(box.right - 22, box.bottom - 18 + yo),
                   (box.right - 12, box.bottom - 18 + yo),
                   (box.right - 17, box.bottom - 12 + yo)]
            pygame.draw.polygon(surf, C_GOLD, tri)

    def _draw_glyphs(self, surf, x, y, max_w):
        cx, cy = x, y
        line_h = self.fonts["md"].get_linesize()
        t = pygame.time.get_ticks() / 1000.0
        word_buf = []
        word_w = 0
        def flush_word(force_newline=False):
            nonlocal cx, cy, word_buf, word_w
            if not word_buf:
                if force_newline:
                    cx = x; cy += line_h
                return
            if cx + word_w > x + max_w:
                cx = x; cy += line_h
            for g, _ in word_buf:
                if g.shake:
                    ox = int(math.sin(t * 30 + cx) * 1.5)
                    oy = int(math.cos(t * 30 + cy) * 1.5)
                else:
                    ox, oy = 0, 0
                ch = g.ch
                if g.glitch and random.random() < 0.4:
                    ch = random.choice(self.GLITCH_CHARS)
                font = self.fonts.get(g.font_key, self.fonts["md"])
                color = g.color
                if g.glitch:
                    color = (random.randint(120,255), random.randint(0,80), random.randint(0,80))
                surf.blit(font.render(ch, True, color), (cx + ox, cy + oy))
                cx += font.size(ch)[0]
            word_buf = []
            word_w = 0
            if force_newline:
                cx = x; cy += line_h

        for i in range(self.revealed):
            g = self.glyphs[i]
            if g.ch == "":
                continue
            if g.ch == "\n":
                flush_word(force_newline=True)
                continue
            font = self.fonts.get(g.font_key, self.fonts["md"])
            ch_w = font.size(g.ch)[0]
            if g.ch == " ":
                flush_word()
                if cx + ch_w > x + max_w:
                    cx = x; cy += line_h
                else:
                    cx += ch_w
            else:
                word_buf.append((g, g.ch))
                word_w += ch_w
        flush_word()

    def _draw_choices(self, surf, box):
        ox = box.x + 60
        oy = box.bottom + 8
        h = 32 + 28 * len(self.choices)
        cw = 220
        crect = pygame.Rect(ox, oy - h, cw, h)
        if crect.bottom > SCREEN_H - 8:
            crect.bottom = SCREEN_H - 8
        s = pygame.Surface((crect.width, crect.height), pygame.SRCALPHA)
        s.fill((*C_DIALOG_BG, 240))
        surf.blit(s, crect.topleft)
        pygame.draw.rect(surf, C_PANEL_BORDER, crect, 2)
        for i, opt in enumerate(self.choices):
            color = C_GOLD if i == self.choice_idx else C_WHITE
            prefix = ">" if i == self.choice_idx else " "
            txt = self.fonts["md"].render(f"{prefix} {opt}", True, color)
            surf.blit(txt, (crect.x + 14, crect.y + 12 + i * 28))

    def _draw_portrait(self, surf, rect, kind):
        cx = rect.centerx; cy = rect.centery
        if kind is None or kind == "narrator":
            return
        if kind == "kid":
            pygame.draw.circle(surf, (240, 210, 180), (cx, cy - 6), 16)
            pygame.draw.rect(surf, (110, 70, 40), (cx - 16, cy - 22, 32, 12))
            pygame.draw.circle(surf, C_BLACK, (cx - 5, cy - 6), 2)
            pygame.draw.circle(surf, C_BLACK, (cx + 5, cy - 6), 2)
            pygame.draw.line(surf, C_BLACK, (cx - 4, cy + 4), (cx + 4, cy + 4), 1)
            # freckles
            for fx, fy in [(-3, 0), (3, 0), (-7, 1), (7, 1)]:
                pygame.draw.circle(surf, (180, 140, 100), (cx + fx, cy + fy), 1)
        elif kind == "mom":
            pygame.draw.circle(surf, (240, 210, 180), (cx, cy - 6), 16)
            pygame.draw.rect(surf, (200, 80, 90), (cx - 18, cy - 22, 36, 14))
            # bun hair
            pygame.draw.circle(surf, (60, 40, 30), (cx, cy - 24), 6)
            pygame.draw.circle(surf, C_BLACK, (cx - 5, cy - 5), 2)
            pygame.draw.circle(surf, C_BLACK, (cx + 5, cy - 5), 2)
            pygame.draw.arc(surf, C_BLACK, (cx - 6, cy - 2, 12, 8), math.pi, 2*math.pi, 1)
        elif kind == "old":
            pygame.draw.circle(surf, (220, 200, 180), (cx, cy - 6), 16)
            # hat
            pygame.draw.rect(surf, (60, 40, 25), (cx - 18, cy - 22, 36, 4))
            pygame.draw.rect(surf, (60, 40, 25), (cx - 12, cy - 28, 24, 7))
            # beard
            pygame.draw.rect(surf, (220, 220, 220), (cx - 12, cy + 4, 24, 8))
            pygame.draw.circle(surf, C_BLACK, (cx - 5, cy - 4), 2)
            pygame.draw.circle(surf, C_BLACK, (cx + 5, cy - 4), 2)
        elif kind == "shopkeep":
            pygame.draw.circle(surf, (210, 180, 150), (cx, cy - 6), 16)
            # bald top
            pygame.draw.arc(surf, (60, 40, 30), (cx - 16, cy - 20, 32, 12), 0, math.pi, 2)
            # glasses
            pygame.draw.rect(surf, (40, 40, 50), (cx - 8, cy - 6, 6, 5), 1)
            pygame.draw.rect(surf, (40, 40, 50), (cx + 2, cy - 6, 6, 5), 1)
            pygame.draw.line(surf, (40, 40, 50), (cx - 2, cy - 4), (cx + 2, cy - 4), 1)
            pygame.draw.line(surf, C_BLACK, (cx - 5, cy + 4), (cx + 5, cy + 4), 1)
        elif kind == "bandit":
            # bandanna face cover, dark hood
            pygame.draw.rect(surf, (40, 60, 40), (cx - 18, cy - 22, 36, 16))
            pygame.draw.circle(surf, (210, 180, 150), (cx, cy - 6), 16)
            pygame.draw.rect(surf, (180, 60, 60), (cx - 14, cy + 2, 28, 6))
            pygame.draw.circle(surf, C_BLACK, (cx - 5, cy - 6), 2)
            pygame.draw.circle(surf, C_BLACK, (cx + 5, cy - 6), 2)
        elif kind == "fisherman":
            # sou'wester hat + beard
            pygame.draw.rect(surf, (220, 200, 80), (cx - 16, cy - 24, 32, 6))
            pygame.draw.rect(surf, (220, 200, 80), (cx - 18, cy - 20, 36, 4))
            pygame.draw.circle(surf, (220, 200, 180), (cx, cy - 6), 16)
            pygame.draw.rect(surf, (160, 130, 90), (cx - 10, cy + 4, 20, 8))
            pygame.draw.circle(surf, C_BLACK, (cx - 5, cy - 4), 2)
            pygame.draw.circle(surf, C_BLACK, (cx + 5, cy - 4), 2)
        elif kind == "shadow":
            pygame.draw.rect(surf, (8, 6, 14), rect.inflate(-4, -4))
            pygame.draw.circle(surf, (10, 8, 16), (cx, cy), 18)
            pygame.draw.circle(surf, (220, 30, 30), (cx - 5, cy - 4), 2)
            pygame.draw.circle(surf, (220, 30, 30), (cx + 5, cy - 4), 2)
        elif kind == "static_figure":
            pygame.draw.rect(surf, (40, 40, 50), rect.inflate(-8, -8))
            pygame.draw.circle(surf, (200, 180, 160), (cx, cy - 4), 12)
            pygame.draw.rect(surf, (30, 25, 20), (cx - 12, cy - 14, 24, 10))
        elif kind == "doll":
            pygame.draw.rect(surf, (200, 100, 130), (cx - 9, cy - 2, 18, 16))
            pygame.draw.circle(surf, (250, 230, 220), (cx, cy - 9), 9)
            pygame.draw.line(surf, C_BLACK, (cx - 6, cy - 12), (cx - 2, cy - 8), 1)
            pygame.draw.line(surf, C_BLACK, (cx - 2, cy - 12), (cx - 6, cy - 8), 1)
            pygame.draw.line(surf, C_BLACK, (cx + 2, cy - 12), (cx + 6, cy - 8), 1)
            pygame.draw.line(surf, C_BLACK, (cx + 6, cy - 12), (cx + 2, cy - 8), 1)
        elif kind == "glitch":
            for _ in range(80):
                px = rect.x + random.randint(2, rect.w - 4)
                py = rect.y + random.randint(2, rect.h - 4)
                col = (random.randint(0,255), random.randint(0,80), random.randint(0,80))
                pygame.draw.rect(surf, col, (px, py, 2, 2))
