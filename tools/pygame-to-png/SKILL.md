---
name: pygame-to-png
description: Render anything drawn with pygame to a PNG headlessly and view/share it -- the "see pygame output as an image" capability for ANY pygame project (which usually has nothing on disk to open). Use whenever you want to visually inspect pygame output: a sprite, an arbitrary surface, or a whole display/screen. Triggers: "show me what X looks like", "screenshot the pygame app", "render this surface", "save a png of the game screen".
---

# pygame -> PNG

pygame draws to in-memory Surfaces -- there's nothing on disk to open. To SEE
output you render it to a PNG, headless (no display needed), then view or send
the file.

## The whole trick (no dependencies beyond pygame)

```python
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
pygame.init(); pygame.display.set_mode((1, 1))   # dummy display, no window

surf = pygame.Surface((64, 64)); surf.fill((20, 18, 24))
# ... draw onto surf ...
pygame.image.save(surf, "/tmp/out.png")
```

Then view `/tmp/out.png` (read/open it) and share it.

## Helper

`to_png.py` (next to this file) does the headless setup on import and adds
`save_png(surface, out, scale=1)` -- `scale` integer-upscales (nearest-
neighbour) so small pixel-art reads:

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills/pygame-to-png"))
from to_png import save_png
save_png(my_surface, "/tmp/out.png", scale=6)
```

## Tips

- **Headless:** the dummy SDL video + audio drivers let it run with no display
  or sound server.
- **Pixel art:** integer-upscale (nearest-neighbour); never smooth, or it blurs.
- **Whole screen:** if the app created its display with
  `pygame.display.set_mode((W, H))`, that returned Surface is drawable and
  saveable -- render one frame, then `pygame.image.save` it (no scaling needed).
- **Comparison sheets:** blit scaled cells into one big Surface with text labels
  to compare variants side by side.
- **Always look before you share:** open the PNG to catch blank / clipped /
  all-black output before sending it on.
