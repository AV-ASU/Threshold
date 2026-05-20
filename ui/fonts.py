"""Font registry."""
import pygame

def make_fonts():
    pygame.font.init()
    return {
        "tiny": pygame.font.Font(None, 14),
        "sm":   pygame.font.Font(None, 18),
        "md":   pygame.font.Font(None, 22),
        "lg":   pygame.font.Font(None, 30),
        "xl":   pygame.font.Font(None, 42),
        "title":pygame.font.Font(None, 64),
        "big":  pygame.font.Font(None, 36),
    }
