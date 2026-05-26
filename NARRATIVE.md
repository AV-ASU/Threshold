# THRESHOLD — Narrative Bible

> Single source of truth for story, cast, geography, and the rules that
> bind them. Built against during implementation. When code and this doc
> disagree, this doc is the intent — fix the code or fix the doc, never
> leave them silently split.

---

## 1. Premise

Brimley, 1994. You are an unnamed **private investigator**. A man — the
client, surname **Blaine** — hired you to find his adult daughter,
**Mara Blaine**, who cut ties, "found religion" out past the highway,
and was **last seen in Brimley**.

You drove in to ask a few questions and drive out. **You can't.** The
King in Yellow's influence has the town folded shut: the roads loop, the
corn never ends, your engine turns over and over and never catches. The
fold is **containment** — Brimley scarred over so that what festers here
never reaches the world — and nothing leaves unless it carries a shard of
His authority. So there are two ways out, and both damn something:
**down** the well to the source, to *end it* — or out past the corn as
the breach itself, the **Sign** in your hands, to *spread it*.

The fold **admits but never releases** — you drove *in* without trouble;
it is only *out* that loops. And you are the **only outsider to enter
since it closed**: unclaimed, not yet His. That is why the Sign can carry
*you* out where it could never carry one of the congregation — a
townsperson holding it still belongs to Him. You are the one thing in
Brimley the fold doesn't own, which is exactly what makes you the only
thing that could ever take Carcosa past the corn.

**Tone:** *Darkwood* (oppressive hide-or-die dread, a spreading
corruption, bleak and ambiguous) + *Fear & Hunger* (grimdark descent to
the god at the bottom, ritual and body-horror, no clean win).

**Setting note:** The **Arcadia Lodge** is a hotel the PI is staying at —
*not* the Innkeeper's home. The README's "car broke down" framing is
retired: the PI came on purpose, and the town strands them.

---

## 2. The Cast — a split town

Some townsfolk are cult, some aren't. Reading who's who *is* the
investigation.

| Who | Side | Their thread |
|---|---|---|
| **Lodge Clerk** (was "the Innkeeper") | Complicit | The smiling trap-keeper. Holds your car keys ("settle your tab"), burns your clock with errands. Same NPC + quest chain, recast. |
| **The Sheriff** | Cult enforcer | The law that keeps everyone in. He killed your car. His outdoor patrols are surveillance. |
| **The Preacher** | **Innocent dissenter** | A small-town minister who **names the cult from his own pulpit** — oblivious to *what* they truly are, but loud that they're no church. Your **2nd** conversation (his hubris — "God's on my side of the door") sets `preacher_doomed`; on the next entry he's **gutted on his own church floor**, his cross in the viscera (evidence #4). The town murders the ones who name them. |
| **The Store-Owner** | Quiet resister | Sells the flashlight, charcoal, paper (survival + clue tools). Frightened hints, never says it outright. |
| **The Kid** | Innocent witness | Saw Mara go into the corn. Gives you a **keepsake of hers**. Children notice what adults pretend not to. |
| **Mara Blaine** | The quarry — **already turned** | A willing member of the congregation now. Finding her proves there was never anyone to save. She is in the **hive**. |
| **Cult / curse-priest / Watchers / the King in Yellow** | The corruption | Operate in the cornfields, the abandoned farmhouse, and the depths/hive below. |

---

## 3. The Threat Model

A single meter: **VISIBILITY** `[0, 1]` — how visible you are to the King
right now. Cultist gaze + Watcher figures push it up; **hiding** bleeds
it back down (`hide_spots` via E, plus passive corn-cover tiles).

**Investigating arms the threat.** The lethal apex is gated behind the
case:

- **Below 3 evidence:** visibility hitting `1.0` spawns **two cultists at
  the door you entered from** (a reinforcement wave; short cooldown so it
  pulses, not floods). The net tightens, but it isn't lethal yet.
- **At 3+ evidence:** that same trigger spawns **the King** — the lethal
  apex. *You make Brimley deadly by understanding it.*

---

## 4. Evidence — the thread that drags you down

A pool of six. **Any 3 = the point of no return** (arms the King).
Searching the lodge thoroughly (1 + 2 + 3) arms Him while you're *still
on the surface* — a fair, brutal "you dug too deep, too fast."

| # | Evidence | Item / scene key | Where | What it proves |
|---|---|---|---|---|
| 1 | **Mara's Room** | `son_room` (robe + `orb`) | Lodge — her rented room | She came, and she joined *willingly* |
| 2 | **Mara's Journal** | `mom_notebook` | Lodge cellar wall-panel | Her descent, in her own words |
| 3 | **The Ledger** (the Lodge's guest register) | (new) | Arcadia Lodge — its cellar (`basement` scene) | Brimley's pattern — guests who check in and never out |
| 4 | **The Preacher** | his **cross** (item `cross`) taken from the viscera | The **church** (`old_man_house`) — his own floor | The town murders the ones who name them — gutted for preaching against the cult |
| 5 | **The Sign — the Pallid Mask** | `sigil_rubbing` (reskinned to the Mask; key kept for saves) | Sign Chamber (well) | His face made an object: what they worship, the shard the fold opens for (the **escape key** → *SPREAD IT*), and the mask that seats into the Play's cover |
| 6 | **The Congregation** | (Mara, turned) | The Depths / the hive | There was never anyone to save |

> **The Sign IS the Pallid Mask.** Not a glyph — the King's own pale
> half-mask, made an object. The jaundiced sigil scrawled through the
> cult's halls (the `yellow_sign` decoration) is only its 2D *brand*.
> This one fact binds the set: the Mask seats into the Play's mask-shaped
> cover (the unmasking — *"I wear no mask"*), carrying it breaks the fold
> (it is *a shard of Him*), and possessing it draws Him. The escape key
> and evidence #5 are the **Mask itself**, not a charcoal rubbing.

---

## 5. The Descent — "how deep does this go"

The descent is strictly **vertical**, and it has exactly **one mouth**:
the village **well**. You go down it on a **rope** — there is no other
route down and **no secret paths**. The Mistlands are *not* part of the
descent; they're the surface **edge** (the cult's outdoor sites, the
Preacher's body, the car). Going *deeper* than the first underground
layer is gated by the **orb**.

```
SURFACE         Brimley — town, Arcadia Lodge, yard, cornfields, church.
                West, across the broken debris: the MISTLANDS — river,
                fog, cult buildings, the Preacher's body, the CAR (Spread it).
                  │
                  │   THE ONLY WAY DOWN — a rope down the village WELL.
                  │   No other route. No secret paths.
                  ▼
THE BASEMENT    The first layer of the cult's works, reached by the well.
LEVEL              >>> being redesigned wholesale — see §9 <<<
                  │
                  │   gated by the ORB
                  ▼
DEEPER          The Depths → the Threshold (END IT / seal) → the Hive
                (the congregation; Mara is here).   (soon)
                  ┊  lose to the King anywhere →
[not a place]   CARCOSA — the King's fire-and-masks catch-cutscene.
```

- **Surface:** Brimley + the **Mistlands** edge — the investigation, the cult's outdoor sites, the Preacher's body, the car. Sealed. Sole way down = the well (rope).
- **The Basement Level:** the first underground layer, reached by the well. *Whole-layer redesign in progress (§9).*
- **Deeper (orb-gated):** the Depths, the Threshold (**End it**), and the Hive where **Mara** is. (soon)

> **Naming, to avoid the collision:** the **lodge cellar** is the
> `basement` *scene* — the Arcadia's own cellar, a *surface* interior
> (holds the Ledger + Mara's journal). **The Basement Level** is the
> underground stratum below the well. Different places, similar words.

**Carcosa is not a level.** Your King sprite is the floating
glow-of-faces, so Carcosa *is* the inside of Him: every mask drifting in
that fire is someone He already took. You only ever see it by losing.

---

## 6. How a run ends

| Trigger | Outcome | Presentation | Existing hook |
|---|---|---|---|
| **A cultist catches you** | The cult takes you for the ritual | Stark text card — **CAPTURED** (cult takes you alive; worse than killed, and feeds the hive) | new |
| **The King catches you** (vis `1.0`, *3+ evidence*, He reaches you) | He takes you into Himself | Brief cutscene: fire/hell, the floating masks of His sprite drifting in it — title **Carcosa** | **net-new.** Today the catch routes to `_trigger_closure` → `_begin_threshold_closure` (a bespoke in-place sequence); the Carcosa cutscene must be authored. |
| **Seal the threshold** — *END IT* | Contain the hunger; Brimley + you become a hole in the map | Ending sequence. *"It is done. Nothing leaves Brimley again. Not the hunger. Not you."* | `_play_ending("seal_threshold")` (exists) |
| **Drive out with the Sign** — *SPREAD IT* | The Sign breaks the fold; you pass where no one else can, and Carcosa bleeds into the world through the hole you made | Ending sequence — the engine catches *for the first time*: *"You got out. You're the only one who ever has. Everyone will understand why, soon."* | `_begin_car_escape()` → `_play_ending("escape_alone")`. **REWORK:** gate the escape on possessing the **Sign** (`sigil_rubbing`), not just car keys; replace the stale `escape_alone` script ("you turn the key / the engine starts / you drive away") with the line at left. |

---

## 7. Implementation map (code ↔ canon)

**Load-bearing — do NOT change:** item *keys* (`systems/items.py`) and
scene *keys* (`scenes/__init__.py`). Saves and game logic depend on them.
Only display names and fiction change.

- **King gate:** `systems/game.py` `_tick_king` (~L2027). Spawn condition
  becomes `visibility >= 1.0 and not in_safe and evidence_count >= 3`;
  the `else` branch spawns 2 cultists at `_king_anchor` (with a cooldown).
- **Evidence count:** `len(self.save.arg("evidence", []))`.
- **Evidence logging:** `_evidence(game, name, content)` in
  `scenes/dialogue.py` → appends to `save.arg("evidence")`, shown in the
  notebook UI.
- **Threat geography constants** (`game.py`): `CULTIST_SCENES`,
  `CURSER_SCENES`, `SAFE_SCENES`, `OUTDOOR_SCENES`, `DARK_SCENES`.
- **Evidence is a log, not inventory.** "Evidence" = entries appended to
  `save.arg("evidence")` by `_evidence(game, name, ...)` (shown in the
  notebook UI). The count for the 3-gate is `len(save.arg("evidence"))` —
  it counts *log entries*, not held items. So every pickup that should
  count (Mara's photo, journal, the orb, the Sign rubbing) must ALSO fire
  a matching `_evidence()` call, or it won't move the gate.
- **Endings exist; deaths don't.** `_ENDING_SCRIPTS` currently holds only
  `escape_alone` (Spread it) and `seal_threshold` (End it). The
  **CAPTURED card** (cultist catch) and the **Carcosa cutscene** (King
  catch) are both net-new — there is no death-card system today.

### Reworks the new fiction forces
- **One mouth down.** The well + rope is the *only* surface→underground
  route. Close the `well_passage` → `barn` hatch (and any other
  shortcut) so there are no secret paths down.
- `well_bottom` currently **consumes the `polaroid`** to open the floor.
  The polaroid is now evidence (Mara's photo) — instead, the **`orb`**
  is the key that opens the way *deeper* (Basement Level → the Depths).
- `dark` room bodies (`ellie / father / mother`, old family) — **remove
  them** and their evidence beats. Cleaned up, not recast.
- The `orb` now lives in **Mara's room** (evidence #1). Remove the
  `mist_house` orb chest; prune the `black_figure` shadows and the
  alter / void-room offering chain.
- `threshold` seal trigger item (`kid_drawing`) — re-fictionalize.
- **Innkeeper → Lodge Clerk** across dialogue + `DISPLAY_NAMES`
  (`son_room` → "Mara's Room", etc.).
- **Item renames** (display only): `polaroid` → Case Photo (Mara),
  `mom_notebook` → Mara's Journal, etc.
- **README rewrite:** PI premise, sealed town, drop "car broke down."

---

## 8. Still loose (design TODO)
- **The Basement Level redesign** (active — see §9).
- The **hive** layout (the deeper layer).
- Mara's journal text; each NPC's dialogue arc.
- The death-card word: **CAPTURED** (leaning) vs KILLED.
- The client's given name (surname Blaine).

---

## 9. The Basement Level — "The Works" (built)

The cult's underground labour, reached *only* by the rope down the
village well. A seven-room stealth gauntlet, descending. Built in
`scenes/well.py`; all rooms are `DARK_SCENES` (flashlight works, but the
cultists' gaze still finds you — run it on cover, timing, hides).

| # | Room | Key | Contents |
|---|---|---|---|
| 1 | The Shaft Floor | `well_bottom` | Rope landing + the ladder back up. Quiet airlock, 1 hide. |
| 2 | The Drying Racks | `well_passage` | Rack-maze, 1 patrolling cultist, 2 hides. |
| 3 | The Tallow Vats | `works_vats` | Steaming vats, 2 tending cultists, 2 hides. |
| 4 | The Sorting Hall | `works_sorting` | Belongings of the vanished, 2 cultists, 3 hides (hardest crossing). |
| 5 | The Scriptorium | `works_scriptorium` | The Sign copied endlessly, 1 oblivious scribe, 2 hides. |
| 6 | The Sign Chamber | `works_sign` | The Sign + 3 kneelers + 1 patrol. **Rubbing → `sigil_rubbing` + evidence #5** (needs charcoal). |
| 7 | The Deep Stair | `works_deepstair` | The **orb-gate**: place the orb → opens to `depths_antechamber`. |

**Rules wired:**
- **One mouth:** rope down the well only; the barn cellar hatch is now
  sealed (`scenes/interiors.py`). The tied rope persists as a two-way
  climb until it breaks.
- **Point of no return:** descend carrying the **orb** and the rope
  **snaps** (`well_bottom` on_enter sets `well_rope_broken`) — the
  ladder up is dead; only deeper remains.
- **Orb-gate:** Room 7 consumes the orb to open the stair to the Depths
  (sets `deepstair_open`).
- The well sprite was redesigned and repositioned in `village` (col 16,
  row 11 — a landmark just off the road).

**Note:** `symbol_portal_room` (old cult chamber) is now unreachable but
stays registered for old saves.

---

## 10. Art direction — the Darkwood look

Reference register: *Darkwood* (oppressive, hide-or-die, muddy
desaturation, hard light/dark) + *Fear & Hunger* (grimdark descent).
Built into the procedural draw layer (`scenes/base.py`,
`entities/decoration.py`) so every scene gets it for free.

> ### ⛓ CORE DESIGN PRINCIPLE — break the tile lockstep
> A grid stops looking like a grid the moment things stop respecting
> cell boundaries. **Everything should aim to bleed across multiple
> squares, or occupy less than one** — never one-object-per-cell in
> lockstep. Oversized/overhanging trees and corn that overlap their
> neighbours, walls with irregular jutting edges, doors that swing out
> *past* their tile, props at varied sub-tile scale and offset, grime
> that blobs across many tiles. This is the through-line for ALL art
> and layout work: when something reads "RimWorld," it is almost always
> snapping cleanly to the grid. The fix is to make it spill.

**Locked rules:**
- **Break the grid — walls are a continuous mass, not blocks.** The #1
  RimWorld tell was per-tile grey wall blocks with borders/grout. Walls
  (`#W%&`) now render as one near-black form via `_draw_wall_mass` (in
  `scenes/base.py`): no per-tile borders, lit edges only on faces that
  touch open floor, faint pitting/cracks. The seams vanish; a run reads
  as a single battered surface. Terrain rendering is shared through
  `draw_scene_terrain` (Scene.draw + the offline renderer use the same).
- **Frame film grade.** `apply_grade` runs over the whole world layer
  each frame (game.py `draw_world`, before the HUD): partial
  desaturation, a cool tint, a radial vignette, and animated film grain.
  This is what hand-recoloring tiles couldn't do — it fuses everything
  into one grimy film image.
- **Palette: muddy + desaturated.** Earthy olive grass, murky water,
  muddy dirt, greyed stone, plus a **macro shadow** layer (low-frequency
  sine darkening that rolls across many tiles) so floors stop reading as
  a grid of identical cells. Cornstalks are jittered off the grid. No
  cheerful primaries — props aged/stained.
- **Lighting is the mood.** Cheap cached primitives: soft **contact
  shadows** under props, **wall-cast shadows** + lit wall faces, and warm
  **light pools** with falloff from every emitter (candle, lantern,
  fireplace). Light is the only relief in the dark.
- **The Yellow Sign is the cosmic anchor.** A bespoke, asymmetric,
  jaundiced glyph (`yellow_sign` decoration) — *not* random scratches.
  Repeated at scale across the Scriptorium and Sign Chamber, faintly
  breathing.
- These compound with the runtime dread-aperture / flashlight / vignette
  (the static look is the floor; in-game dark scenes go darker).

**Still TODO (the liminal-composition pass):** composed emptiness, long
sightlines, and uncanny repetition (identical houses, endless identical
corn rows) — that's per-scene level design, not a global draw change.
