---
name: pygame-to-png
description: Render anything drawn with pygame to a PNG headlessly and show it in chat -- the foundational "see pygame output as an image" capability for the THRESHOLD game (which draws everything procedurally, with no asset files). Use whenever you want to visually inspect pygame output: a single sprite, a whole game scene/screen, or any generated surface. Triggers: "show me what X looks like", "render the village", "screenshot the game", "save a png of this surface". The sprite-preview and creature-design skills build on this.
---

# pygame -> PNG

THRESHOLD draws all its art in code (`rendering/`, `systems/game.py`) -- there
are no image files to open. So the only way to *see* anything is to render it
to a PNG. This skill is the minimal, general way to do that; `sprite-preview`
(sprite animation strips) and `creature-design` (monster design loop) are
specialisations of it.

## Core pattern

```python
import sys; sys.path.insert(0, ".claude/skills/pygame-to-png")
from to_png import save_png            # sets dummy SDL + inits pygame on import
import pygame

surf = pygame.Surface((64, 64)); surf.fill((20, 18, 24))
# ... draw onto surf ...
save_png(surf, "/tmp/out.png", scale=6)   # integer upscale so pixel-art reads
```

Then **Read `/tmp/out.png` yourself** (to catch blank/clipped/broken output),
then send it with **SendUserFile**.

- **Headless:** importing `to_png` sets `SDL_VIDEODRIVER`/`SDL_AUDIODRIVER` to
  `dummy`, so no display is needed.
- **Pixel art:** pass an integer `scale` (nearest-neighbour). Small sprites are
  illegible at 1x; render the cell small, then upscale 5-8x. Never smooth.
- **Comparison sheets:** make one big Surface and blit scaled cells into a grid
  with labels (see `creature-design/concept_sheet.py` for a ready-made one).

## Render a whole scene / the game screen

`Game()` creates the real 960x640 screen in its constructor, so:

```python
import sys; sys.path.insert(0, ".claude/skills/pygame-to-png")
from to_png import save_png
from systems.game import Game

g = Game(); g.save.new(); g._start_play()      # boots into the bedroom
g.load_scene_now("village", "default")         # any scene key
g.draw_world()                                  # renders to g.screen
save_png(g.screen, "/tmp/scene.png")            # already 960x640 -- no scaling
```

`draw_world()` draws the camera-framed scene to `g.screen`
(`constants.SCREEN_W, SCREEN_H = 960, 640`). To frame a specific spot, set
`g.player.x/y` (and `g._update_camera(snap=True)`) before drawing.

## Requirements

Needs `pygame` (pinned in `requirements.txt`). A `SessionStart` hook in
`.claude/settings.json` installs it at the start of every web session, so it's
available by default; if you ever hit `ModuleNotFoundError: pygame`, run
`pip install -r requirements.txt`.
