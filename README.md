# Threshold

A 2D narrative-horror game built with pygame, played entirely through an
oblique tilted camera (~55° pitch, mouse-look head-turn; it's the only
camera the game has). Every sprite is drawn procedurally at runtime, no
image assets. In 1994 you drive into **Brimley** as a private investigator
hired to find a missing woman, Mara. You came to ask a few questions and
drive home. You can't: the **King in Yellow** has folded the town shut,
and the only way out is down, to the source. It isn't a combat game, you
walk, watch, and hide while a thing follows. A **visibility** meter rises
under the cult's gaze; gather enough of the truth and it arms the King,
the lethal apex pursuer.

## Requirements

- Python 3.10+
- pygame, numpy, scipy (see `requirements.txt`; numpy/scipy drive the
  procedural audio synthesis, the game ships zero audio assets too)

## Install & run

```bash
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
python main.py
```

The game opens on the title screen. Choose **New Game** to start a run.
There is a single disk save slot, written automatically whenever you pick
up a piece of case evidence (it snapshots hp, inventory, current scene,
and a cooled-down visibility). **Continue** on the title reads it back and
wakes you at the scene the last clue was found in; a death or a quit to
the title costs progress since that last clue, never the whole run.

## Controls

| Action                        | Keys                 |
| ------------------------------ | --------------------- |
| Move                           | WASD / Arrow keys     |
| Sprint                         | Hold Shift            |
| Look / aim (camera head-turn)  | Mouse                 |
| Use equipped weapon            | Left click            |
| Throw a held river stone       | Right click           |
| Interact / advance dialogue    | E / Space / Enter     |
| Casebook (Case / Tools / Papers)| I or N                |
| Flashlight                     | F                     |
| Pause                          | Esc                   |
| Fullscreen                     | F11                   |

The gun and axe share one weapon slot; switch which is equipped from the
Tools tab of the Casebook.

## Tests

```bash
python tests/run_all.py   # the full gate: every harness below, in order
```

Or run one harness standalone: `tests/smoke.py` (every scene builds, every
spawn point is walkable, every exit resolves), `tests/flow.py` (drives a
full headless run through the critical path to every ending), plus
`tests/stealth.py`, `tests/fold_pursuit.py`, `tests/king_roam.py`, and
`tests/render_smoke.py`. All of them force SDL to dummy video/audio
drivers, so no display or audio device is required. CI runs the same full
gate (plus a canon-key drift check) on every push and PR.

## Project layout

`main.py` is the entry point; `constants.py` holds screen geometry and
the colour palette. The runtime lives in `systems/`, tile-grid scenes in
`scenes/`, actors and props in `entities/`, procedural draw code in
`rendering/`, UI in `ui/`, and the test harnesses in `tests/`. For the
real architecture map, the threat model, and the project's conventions,
see `CLAUDE.md`.
