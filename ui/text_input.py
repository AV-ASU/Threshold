"""TextInputModal -- a 1990s-CRT-style text-entry overlay.

Captures a-z 0-9 + space + backspace + enter. ENTER submits the buffer
to the on_submit callback; ESC cancels (calls on_cancel if provided).
While active, the Game suspends gameplay and routes all key events here.
The modal renders a panel with the prompt line + a typed buffer line
underneath, with a blinking cursor."""
import pygame
from constants import (
    SCREEN_W, SCREEN_H,
    C_WHITE, C_GOLD, C_DIM, C_PANEL, C_PANEL_BORDER, C_BLACK,
)


class TextInputModal:
    def __init__(self, fonts, audio):
        self.fonts = fonts
        self.audio = audio
        # `active` (not `open`, to leave that name available for the open()
        # method) tells the Game whether to suspend play and route events
        # here. Game.text_input.active gates input/update suspension.
        self.active = False
        self.prompt = ""
        self.buffer = ""
        self.on_submit = None
        self.on_cancel = None
        self.t = 0.0
        # Allowed characters (case-insensitive membership check). The
        # buffer preserves the user's original casing so what they type
        # is what they see; the on_submit caller is responsible for
        # case-folding before comparing against any saved credential.
        # Dash is allowed because the bandit-foreman credential format
        # is "User-D###".
        self._allowed = set("abcdefghijklmnopqrstuvwxyz0123456789 -")

    def open(self, prompt="LOGIN:", on_submit=None, on_cancel=None):
        """Open the modal with `prompt` text and a submit/cancel callback.
        on_submit(string) fires on ENTER with the typed buffer; on_cancel()
        fires on ESC."""
        self.prompt = prompt
        self.buffer = ""
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.active = True
        self.t = 0.0

    def close(self):
        self.active = False
        self.prompt = ""
        self.buffer = ""
        self.on_submit = None
        self.on_cancel = None

    def update(self, dt):
        if not self.active: return
        self.t += dt

    def handle_event(self, ev):
        """Returns True if the event was consumed by the modal.
        Game.handle_event should call this first while active and bail out
        on a True return."""
        if not self.active: return False
        if ev.type != pygame.KEYDOWN: return True   # swallow everything
        if ev.key == pygame.K_ESCAPE:
            cb = self.on_cancel
            self.close()
            if cb:
                try: cb()
                except Exception: pass
            return True
        if ev.key == pygame.K_RETURN:
            buf = self.buffer
            cb = self.on_submit
            self.audio.play("confirm", 0.7)
            self.close()
            if cb:
                try: cb(buf)
                except Exception: pass
            return True
        if ev.key == pygame.K_BACKSPACE:
            if self.buffer:
                self.buffer = self.buffer[:-1]
                self.audio.play("cursor", 0.4)
            return True
        # Append printable characters from the unicode field. We check
        # membership case-insensitively but APPEND the original casing
        # (e.g. SHIFT+a -> 'A' both displays and stores as 'A'); the
        # submit-side comparator should case-fold.
        ch = ev.unicode or ""
        if len(ch) == 1 and ch.lower() in self._allowed:
            if len(self.buffer) < 32:
                self.buffer += ch
                self.audio.play("cursor", 0.3)
        return True

    def draw(self, surf):
        if not self.active: return
        # Darken the world behind the modal so attention focuses on the panel.
        veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 180))
        surf.blit(veil, (0, 0))

        panel_w = 460
        panel_h = 160
        panel_x = SCREEN_W // 2 - panel_w // 2
        panel_y = SCREEN_H // 2 - panel_h // 2

        # Outer panel -- 1990s beige/CRT vibe
        pygame.draw.rect(surf, (10, 14, 20),
                         (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(surf, (60, 180, 100),
                         (panel_x, panel_y, panel_w, panel_h), 2)
        # Inner CRT frame
        inner = pygame.Rect(panel_x + 6, panel_y + 6, panel_w - 12, panel_h - 12)
        pygame.draw.rect(surf, (6, 10, 14), inner)
        pygame.draw.rect(surf, (40, 100, 60), inner, 1)

        # Prompt line: "> LOGIN: "
        prompt_surf = self.fonts["lg"].render(
            "> " + self.prompt, True, (140, 230, 160))
        surf.blit(prompt_surf, (panel_x + 24, panel_y + 22))

        # Input line: the buffer + a blinking caret
        cursor_on = (int(self.t * 2) % 2) == 0
        buf_text = self.buffer + ("_" if cursor_on else " ")
        buf_surf = self.fonts["lg"].render(buf_text, True, (200, 240, 200))
        surf.blit(buf_surf, (panel_x + 24, panel_y + 64))

        # Footer hint
        hint = self.fonts["sm"].render(
            "[Enter] submit    [Esc] cancel    [Backspace] erase",
            True, (80, 140, 100))
        surf.blit(hint, (panel_x + 24, panel_y + panel_h - 28))

        # CRT scanlines for atmosphere
        for sy in range(inner.top, inner.bottom, 3):
            pygame.draw.line(surf, (8, 14, 18),
                             (inner.left + 1, sy),
                             (inner.right - 1, sy), 1)
