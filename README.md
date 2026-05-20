# Threshold

[![CI](https://github.com/AV-ASU/Threshold/actions/workflows/ci.yml/badge.svg)](https://github.com/AV-ASU/Threshold/actions/workflows/ci.yml)

A 2D top-down narrative-horror game built with pygame. You arrive in a
small town in 1994 looking for someone, and slowly come to understand
what the town is. There is no combat -- only walking, watching, hiding,
and the thing that follows.

## Requirements

- Python 3.10+
- pygame (see `requirements.txt`)

## Install & run

```bash
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
python main.py
```

The game opens on the title screen. Choose **New Save** to start a run or
**Continue** to resume. There is no quicksave -- you save the game by
sleeping at the cot.

## Controls

| Action                       | Keys                 |
| ---------------------------- | -------------------- |
| Move                         | WASD / Arrow keys    |
| Sprint                       | Hold Shift           |
| Interact / advance dialogue  | E / Space / Enter    |
| Inventory                    | I                    |
| Notebook                     | N                    |
| Flashlight                   | F                    |
| Pause                        | Esc                  |
| Fullscreen                   | F11                  |

## Tests

```bash
python tests/smoke.py
```

`smoke.py` verifies that every scene builds, that spawn points are
walkable, and that every exit resolves to a valid target spawn. It forces
SDL to dummy drivers, so no display or audio device is required.

## Project layout

- `main.py` — entry point
- `constants.py` — screen geometry, colour palette, save paths
- `systems/` — the runtime (`game.py`: main loop, input, transitions, save/load) plus `save`, `items`, `audio`, `threat`
- `scenes/` — tile-grid scene builders and the scene registry (`__init__.py`)
- `entities/` — player, NPCs, enemies, decorations
- `ui/` — dialogue box, inventory, notebook, text-input modal
- `rendering/` — procedural sprite drawing
- `tests/` — smoke test
