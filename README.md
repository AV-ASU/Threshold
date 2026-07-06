# Threshold

A 2D narrative-horror game built with pygame, played through an oblique
tilted camera (~55° by default; F3 drops to the flat pitch-0 view). In 1994 you drive
into **Brimley** -- a private investigator hired by a man named Blaine to
find his daughter Mara, who found religion out past the highway and
vanished. You came to ask a few questions and drive home. You can't: the
**King in Yellow** has folded the town shut, and the only way out is
**down**, to the source. It isn't a combat game -- you walk, watch, and
hide while a thing follows. You carry a sidearm, but using it is a choice
the world makes you pay for. A **visibility** meter rises under the cult's
gaze; gather enough of the truth and it arms the King, the lethal apex
pursuer.

## Requirements

- Python 3.10+
- pygame (see `requirements.txt`)

## Install & run

```bash
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
python main.py
```

The game opens on the title screen. Choose **New Game** to start a run.
There is a single disk save slot, written only when you sleep at the
spare-room cot (it snapshots hp, inventory, and visibility). **Continue**
on the title reads it back; a death or a quit to the title costs
everything since the last sleep, never the whole run.

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
python tests/smoke.py   # scene-build / spawn / exit checks
python tests/flow.py    # drives the full critical path end-to-end
```

`smoke.py` verifies that every scene builds, that spawn points are
walkable, and that every exit resolves to a valid target spawn. `flow.py`
drives a headless run down through the Works (the cult's dug mine) to the
Deep-Stair fork, across the Depths to the hive, and into both endings, proving the
path is completable with no soft-lock. Both force SDL to dummy drivers, so
no display or audio device is required.

## Project layout

- `main.py` — entry point
- `constants.py` — screen geometry and colour palette
- `systems/` — the runtime (`game.py`: main loop, input, transitions) plus `save` (one disk slot, written at the cot), `items`, `audio`, `threat`
- `scenes/` — tile-grid scene builders and the scene registry (`__init__.py`)
- `entities/` — player, NPCs, enemies, decorations
- `ui/` — dialogue box, inventory, notebook, text-input modal
- `rendering/` — procedural sprite drawing
- `tests/` — smoke + flow harnesses
