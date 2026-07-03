---
name: creature-design
description: Design or redesign a creature / enemy / boss sprite for the THRESHOLD game through a concept -> preview -> approve -> implement -> verify loop. Use whenever the user wants a new or reworked monster (the King in Yellow, cultists, the Watcher, etc.). It encodes the game's art-direction rules, the headless concept-sheet workflow, the sprite + animation wiring map, and how to verify. Triggers: "redesign the King", "make a new enemy", "the Watcher needs a new look", "draw me monster concepts", "that creature isn't scary/eldritch".
---

# Creature design (THRESHOLD)

Sprites here are **drawn in code** (`rendering/sprites.py`) -- there are no
asset files. Designing a creature means writing draw routines and judging
them by rendering to PNG. Iterate on the LOOK first (cheap, visual), then
wire the approved design into the game and verify.

## Art direction (hard rules, learned the hard way)

- **Grim. Yellow is restrained.** Bodies are near-black; gold/yellow appears
  ONLY as a sick eye-glint or faint glow, never a flat fill. (Yellow as
  *cloth* can work; yellow as flesh reads cheap/goofy.)
- **Eldritch = unparseable.** Avoid clean, recognisable silhouettes (a deer,
  a spider, a robed-crowned man all got rejected as "not eldritch"). If the
  eye resolves it instantly, it's wrong. Favour wrongness: violated anatomy,
  too many joints, things half-submerged in a mass, asymmetry.
- **Body-horror seed:** the cult's victims fused/absorbed -- embedded faces,
  mouths, eyes are good, but as *suggestion*, not a tidy totem.
- **Three views that read distinctly** (front / side / back) -- the King is
  chased down under an oblique overhead camera, so facing must be legible. The **back is occluded by the
  body's own bulk**: never draw "backs of heads"; the rear is just mass,
  limbs, tatters, maybe one eye peering past.
- **Movement sells dread.** Looming/gliding or wrong-gaited beats clean
  walking. The apex should also **phase** (half-seen, like the Watcher).
- Keep it **legible at gameplay scale**: fewer, larger features beat a busy
  cluster that mushes into noise when small and moving.

## Workflow

1. **Sketch concepts.** Write a throwaway `/tmp/*.py` that imports the helper
   below and defines each candidate as `fn(surface, x, y, view)`. Render a
   labelled sheet, **Read the PNG yourself** to catch broken/ugly cells, then
   send it with **SendUserFile** for the user to choose.
   ```python
   import sys; sys.path.insert(0, ".claude/skills/creature-design")
   from concept_sheet import make_sheet, ball, glow, limb, PALE, GOLDG, TAR
   def candidate_a(s, x, y, view): ...     # draw one creature, per view
   make_sheet([("1. name", candidate_a), ("2. name", candidate_b)],
              out="/tmp/concepts.png")
   ```
   `concept_sheet` runs headless (sets dummy SDL) and gives a grim palette +
   `glow` (eye bloom), `ball` (tar lump), `limb` (two-segment jointed limb --
   bend the joint the wrong way for broken anatomy).
   For previewing sprites that ALREADY exist in the game, use the sibling
   **`sprite-preview`** skill instead.
2. **Converge.** If the direction is ambiguous after a miss, use
   **AskUserQuestion** with concrete, distinct options rather than guessing
   again. Refine the chosen one until the user signs off on the look.
3. **Implement** the approved design in the game (next section).
4. **Verify**, then **commit + push**.

## Wiring map (where sprites live)

- `rendering/sprites.py` -> `draw_npc_sprite(surf, x, y, kind, facing, blink,
  gaze, birth, gait)` dispatches per `kind`. Most creatures are an `elif kind
  == "..."` block. The King (`kind == "yellow_king"`) dispatches to
  `_draw_king(surf, x, y, facing, t, birth, gait)` at the end of the file --
  replace that function to restyle the King.
- **Pick the view from `facing`** inside the draw (front when facing toward
  the camera / down, back when away / up, side otherwise; mirror left<->right).
- **Animation state is already plumbed for the King:**
  `entities/npc.py:_yk_update` ramps `_birth` (0->1; the King cannot move
  until born) and accumulates `_gait` from distance moved;
  `systems/game.py:_spawn_king` seeds `_birth`/`_gait`; the render call
  (`systems/game.py`, ~the `draw_npc_sprite(self.screen, ...)` line) passes
  `birth`/`gait` off the NPC. Use `birth` for the **eruption-from-a-cultist**
  sequence and `gait` for the **run/walk** cycle; apply a phasing alpha for
  the half-seen look.
- New `kind`s: add the `elif` block in `draw_npc_sprite`, give the NPC that
  `sprite_kind`, and (if it needs new animation inputs) plumb them like the
  King's `birth`/`gait`.

## Verify

Run from the repo root: `python tests/smoke.py` (scenes/exits) and the
threat-engine scripts `python /tmp/king_test.py`, `/tmp/cult_test.py`, and
especially `/tmp/integ_test.py` (a 900-frame real-loop run that renders, so
it catches draw-time crashes). If those scripts are gone, reconstruct a tiny
headless harness: `Game(); g.save.new(); g._start_play()`, force the creature
in, and step/draw a few hundred frames.

## Git

Develop on the working branch; `git add` the changed files, commit with a
clear message, push. Do not open a PR unless asked.

## Shipped creatures (canon -- do not re-pitch)

- **The King** is **THE UNFOLDING** (`rendering/king_unfold.py`): a 4D
  everting wet-flesh mass, the Pallid Mask bonded to a host facet
  (surfaces/sinks with the churn), a gape-lunge telegraph, the
  throat-swallow catch. The old BROKEN BODY brief is superseded.
- **The Moth** (`rendering/moth.py`): the King's herald, first flying
  entity -- tented ragged wings at rest, kindle -> flare alarm -> falls
  as a husk. Sim in `systems/infest_mixin.py`.

No active job. When the user asks for a new creature, start at step 1
(concept sheet) and converge before wiring.
