"""Headless pygame -> PNG. The 'see pygame output as an image' helper.

Importing this sets the dummy SDL drivers and inits pygame, so it works
with no display/server. Draw onto any Surface, then save_png() it
(optionally integer-upscaled for pixel art), view the file, and share
it.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

if not pygame.get_init():
    pygame.init()
    pygame.display.set_mode((1, 1))


def save_png(surface, out, scale=1):
    """Save a pygame Surface to `out` as a PNG.

    `scale` integer-upscales with nearest-neighbour so small pixel-art
    reads clearly (try 5-8 for a single sprite). Returns the path.
    """
    if scale != 1:
        w, h = surface.get_size()
        surface = pygame.transform.scale(surface, (w * scale, h * scale))
    pygame.image.save(surface, out)
    print(f"saved {out} {surface.get_size()}")
    return out
