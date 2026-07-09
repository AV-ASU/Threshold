# PORTALS — design plan (the visible 4D crossing)

> **STATUS: landed.** The portal/fold 4D crossing described here is built: the
> King tears a rift when you pin visibility at 100% and folds through
> (`systems/king_roam_mixin.py` `_tick_portal`), rendered by `rendering/portal.py`.
> This file is kept as the **design archive** for the portal/fold direction; the
> canonical in-fiction account lives in `NARRATIVE.md` §11 ("The Fold, made
> mechanical").

## Vocabulary (locked)

Three spatial-transition flavors; two of them share one trick.

| Term (this doc / chat) | `NARRATIVE.md` name | What it does |
|---|---|---|
| **Portal** | "the standing folds (the rift panes)" (§11) | Connects to a *different* scene. **The visible 4D piece.** (The walk-in secret-area folds this family once included were cut, 2026-07; the shipped portals are the rite panes + the King's.) |
| **Fold** | "the Fold" / torus wrap (§11) | Loops you inside *one* map (the corn maze never ends). **Invisible by canon.** |
| Door / ladder / well | — | Ordinary plumbing; fade-to-black. |

Shared foundation: **seamless scene transition** — no fade, music keeps
playing, the player stays put on screen. Both portal and fold are uses of it;
**neither may reintroduce a loading-screen feel.** That seamlessness was the
biggest win and is the thing to protect.

## The one idea: a portal is a 4D pane

A portal is the edge of a 4D "pane" poking up into Brimley.

- Face it **head-on** → you see through it (the peek) and can step through.
- Step to the **side** → a pane seen edge-on is a thin line; nearly invisible.
- There is **no back** → the pane's other faces point in the 4th direction, a
  way you can't walk. So from any angle but head-on, it isn't there.

This is exactly the canon rule (§11): *"From any other angle the tile reads as
floor and the player walks over it without consequence."* We are not adding a
rule — we're **drawing the rule already written.**

## How little 4D we actually use

No 4D world simulation. We reuse the King's existing 4D math
(`rendering/king_unfold.py`: `_rot` = spin through the W axis, `_to3d` =
flatten back) in **three spots only**:

1. **Border** = the lit grazing edge of the pane (reuse the King's dim gold
   rim-light, `_GOLD_RIM`).
2. **Peek** = the destination spun in through 4D → reads with impossible depth,
   and naturally fades to nothing as the pane turns edge-on.
3. **Crossing** = stepping in *turns* the pane: this scene rotates out through
   W, the next rotates in. A quick **turn, not a fade** → seamless preserved.
   This is the brief "floating pieces" moment.

Everything else — walking, walls, tilt camera — is unchanged.

## Visual spec (agreed)

- **Standing pane**, not a floor mark: a tall thin slit that stands up in the
  world and **depth-sorts with trees/corn** (passes in front of / behind
  actors like any standee).
- **Dim black-gold electric border:**
  - a **dark core / mouth** so the rim has contrast (this is what makes it read
    at small size under the 55° tilt);
  - a **dim, desaturated gold** rim — *cursed* gold, not treasure gold;
  - thin **jagged electric arcs** that flick along the edge and die in a few
    frames (the "living wound").
- **Peek shows the REAL destination** — readable, a recognizable place, with
  live actors resolving out of the fog at the seam (as the current
  `folds.py` peek does). Fogs out toward the slit edges.
- **Hold the line:** keep it eldritch, never sci-fi. **Black + dim-gold** is
  precisely what keeps it from going Tron-blue. No bright/cyan "electric."

## Readability under tilt (the watch-item)

The pane must stand **vertical** and be **depth-sorted**; painted flat on the
ground it reads as a stain. The dark core gives the gold rim something to sit
against so it's legible from across a room at the oblique angle.

## Folds — leave alone

Canon wants the fold **invisible** (visual sameness hides the wrap; the horror
is *futility*, not spectacle — §11). 4D stays the *hidden logic* of the loop
(a looping space is naturally a 4D torus), never an on-screen effect. The only
sanctioned place for subtle fold-wrongness is **"off the roads, come out
wrong-side"** (Garrick's warning), or **escalation with infestation** — but
that last one is a **canon change** to decide deliberately, not a freebie.

## The Threshold doorframe — stays plain

Deliberately **not** 4D. The world's portals scream; the real Threshold is a
plain doorframe with no wall. The **restraint is the payoff** (§1b: *it never
opens, Carcosa is never shown, the not-knowing is the flame*). It only lands
because the world taught the player that portals are supposed to scream.

## The unifying picture

A looping map (torus) and a one-directional pane are **both 4D objects.** So
this isn't 4D bolted onto two unrelated systems: the **whole town is one
folded 4D space**, and portals are the places where its edge pokes up where you
can see it. That is the bible's line made literal — *"the looping roads and the
level floor are the same wrongness at different sizes"* (§1b).

## Decisions landed (2026-06 consolidation)

The open questions below were settled in the teleportation-consolidation
pass (NARRATIVE.md §11 "One phenomenon, two presentations"):

- **The crossing is NOTHING.** Not barely-there — literally nothing: no
  flourish, no sting, no fade, no input hitch. All crossings funnel through
  one primitive (`Game.cross_fold`) that preserves stride, look, music, and
  screen position. The frame is the monument; its threshold is silent.
- **One border, one family.** Every visible fold wears the same standing
  rift frame (`rendering/portal.py draw_rift_door`), ANCHORED in the world:
  the pane stands along its world seam (it foreshortens with the view like
  a wall, never billboards), its contact shadow and gold pool lie on the
  floor plane, and it thins/dims to nothing as the approach goes oblique
  (the pane has no back). The King's portal is the same frame torn loudly
  (charge/looming), with its orientation fixed at tear time.
- **Hidden folds are SEEN now** (a deliberate canon change): faced head-on
  they show the frame; discovery is choosing, not stumbling.
- **The wrap stays invisible** — futility, not spectacle, unchanged.
- **One-way is the King's signature.** Static folds are two-way; the wrap
  loops; the only one-way crossing is the juke through HIS tear.
- **In-maze relocations** are ordinary same-scene direction-gated exits
  now (silent — no frame; the lie is the world itself).
- **Folds can be STATE-DRIVEN (2026-06 descent rework).** A scene may gate
  an exit on game state (`Scene.exit_gate_fn(game, char)`) and drive a
  fold's formation charge per frame (`Scene.fold_charge_fn(game, char)` →
  0..1 into `draw_rift_door`'s charge ramp; 0 = not drawn, reads as
  floor). Direction-gated exits also route straight through `cross_fold`
  regardless of set membership, so a fold can join ANY two scenes —
  including surface↔underground. The shipped uses: the **effigy grove's
  descent fold** (clarity = evidence/3, opens at 3, lands at
  `well_bottom`, dies at `descent_sealed`), its **return pane** at the
  shaft floor, and the **school door** (opened by the chalk-door rite,
  then permanent). Folds stay two-way until they DIE or are **KEYED**
  (the shaft-floor pane answers only the Mask after the grove rite) —
  never one-way (the King keeps his signature).
- **The rift family keeps ONE presentation (decision re-affirmed,
  2026-06).** A "throat" ground-opening variant was prototyped for the
  grove rite and CUT the same day: the rite's open descent is the same
  regular standing pane as every other fold, torn fully open. If a
  ground-anchored presentation is ever revisited, project a world-space
  ring point by point (a floor ellipse under tilt) — never a vertical
  cylinder, which pinches at the side tangents.

- **See-through doors obey the blind spot (2026-07).** The mundane
  see-through door (`portal.draw_through_aperture`, opted in per scene via
  `Scene.seethrough_doors`) shows the ACTUAL room beyond through the
  opening. Its terrain is a cached CCTV-style buffer, but the far room's
  **actors are a per-frame pass** (`portal._draw_aperture_actors`) gated by
  the player's own sight cone: a far actor is mapped to its apparent
  host-world position (both cameras share pitch/yaw/scale, so a far actor at
  `(ax, ay)` shows where the host camera would draw `door_world + (actor -
  anchor)`) and culled by `scene._door_actor_sight` (the frame's sight fn,
  set in `draw_world`). So an empty room reads through the door but a threat
  in a corner the player isn't looking at stays hidden — the same
  restricted-sight rule the open world obeys. This is the mundane door's
  point of difference from the RIFT, which shows everything by design (the
  King's violence has no blind spot). The figure is clipped to the opening
  (you see only the framed slice). Preview: `tools/preview_door_sight.py`.

Live proof sheet: `tools/preview_rift_anchored.py`.
