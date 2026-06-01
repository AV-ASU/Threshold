---
name: sprite-preview
description: Render this game's procedurally-drawn pygame sprites to a labelled animation-strip PNG so they can be seen and shared in chat. Use whenever the user wants to preview, see, compare, or iterate on a sprite or its animation (e.g. "show me the watcher", "render the king animation", "what does the cultist look like now", "did the gore change land?").
---

# Sprite preview

The creatures in this game are **drawn in code** (`rendering/sprites.py`,
`draw_npc_sprite`) and animate off `pygame.time.get_ticks()`. There are
no PNG/asset files to open, so the only way to *see* a sprite — or judge
an animation — is to render it. This skill does that and produces a
single still you can attach to chat.

## How it works

`render_sprites.py` runs headless (it sets the dummy SDL video/audio
drivers itself, so no display is required), draws each requested sprite
onto an off-screen `Surface`, and lays the results out as a sheet:

- **one row per sprite kind**, labelled with the kind name;
- **one column per frame**, labelled with the animation time;
- the animation clock is monkeypatched (`pygame.time.get_ticks`) so each
  column is a fixed, reproducible frame stepped across `--span` seconds —
  that's what makes a still image show the motion.

It saves a PNG with `pygame.image.save(...)`. That's the whole trick:
render to a Surface, save as PNG. (Sending it to the user is a separate
step — attach the saved file in your reply.)

## Usage

Run from the repo root:

```bash
# Default: the threat creatures (cultist, watcher, yellow_king)
python .claude/skills/sprite-preview/render_sprites.py

# Specific kinds
python .claude/skills/sprite-preview/render_sprites.py watcher cultist

# Tune the strip
python .claude/skills/sprite-preview/render_sprites.py yellow_king \
    --frames 10 --span 4 --scale 6 --out /tmp/king.png

# The watcher reacts to being looked at:
python .claude/skills/sprite-preview/render_sprites.py watcher --gaze
```

Flags: `--out PATH` (default `/tmp/sprite_preview.png`), `--frames N`,
`--scale S`, `--span SECONDS` (animation spread across the row),
`--facing dx,dy`, `--gaze`, `--bg R,G,B` (cell background).

`kind` can be any value `draw_npc_sprite` handles (yellow_king,
cultist, watcher, wolf, doll, black_figure, ...). Unknown
kinds render an `ERR` cell rather than crashing the sheet.

## Workflow

1. Run the script for the kind(s) of interest.
2. Read the printed save path and **attach that PNG in your reply** so
   the user can see it.
3. To iterate: edit the sprite in `rendering/sprites.py`, re-run, re-send.

## Notes / gotchas

- A single static cell can't show motion — keep `--frames` ≥ 6 for
  anything animated.
- The script monkeypatches `pygame.time.get_ticks`; it's a throwaway
  preview process, so that's fine. Do not import it into game code.
- Player sprites use a different entry point (`draw_player_sprite`) with
  its own args; this skill targets NPC/creature sprites.
