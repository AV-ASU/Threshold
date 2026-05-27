"""Font registry."""
import pygame

def make_fonts():
    pygame.font.init()
    # Monospace for typed/case-file text. SysFont always returns a usable
    # font (falls back to the default) so this is safe headless.
    mono = pygame.font.SysFont("couriernew,dejavusansmono,monospace", 15)
    mono_sm = pygame.font.SysFont("couriernew,dejavusansmono,monospace", 13)
    return {
        "tiny": pygame.font.Font(None, 14),
        "sm":   pygame.font.Font(None, 18),
        "md":   pygame.font.Font(None, 22),
        "lg":   pygame.font.Font(None, 30),
        "xl":   pygame.font.Font(None, 42),
        "title":pygame.font.Font(None, 64),
        "big":  pygame.font.Font(None, 36),
        "mono":    mono,
        "mono_sm": mono_sm,
    }
