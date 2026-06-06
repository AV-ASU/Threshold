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
| **Portal** | "direction-sensitive hidden fold" (§11) | Connects to a *different* scene. **The visible 4D piece.** |
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

## Open questions (next planning bites)

- How loud is the crossing "turn" — barely-there, or a real beat the player
  feels every time?
- Does every portal share one border, or do special ones (the curse-grove,
  `scarecrow_ring`) escalate?
- Fold: keep invisible forever, or evolve the canon so it turns visibly wrong
  as Brimley rots? (a story decision, not an art one)
