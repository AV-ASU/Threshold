"""Font registry."""
import pygame

def make_fonts():
    pygame.font.init()
    # Monospace for typed/case-file text. SysFont always returns a usable
    # font (falls back to the default) so this is safe headless.
    mono = pygame.font.SysFont("couriernew,dejavusansmono,monospace", 15)
    mono_sm = pygame.font.SysFont("couriernew,dejavusansmono,monospace", 13)
    # Serif family for the diegetic documents (Mara's journal, menu
    # headings). A real book/letter face reads as paper-and-ink rather
    # than "game UI", which is the whole point of the menu overhaul.
    def serif(sz, italic=False):
        return pygame.font.SysFont(
            "georgia,liberationserif,dejavuserif,freeserif,serif",
            sz, italic=italic)
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
        # Diegetic document type.
        "serif_tiny":  serif(15),
        "serif_sm":    serif(17),
        "serif":       serif(20),
        "serif_it":    serif(20, italic=True),
        "serif_lg":    serif(28),
        "serif_title": serif(38),
        "serif_huge":  serif(56),
    }

