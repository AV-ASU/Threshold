# THRESHOLD — Narrative Bible

> Single source of truth for story, cast, geography, and the rules that
> bind them. Built against during implementation. When code and this doc
> disagree, this doc is the intent — fix the code or fix the doc, never
> leave them silently split.

---

## 1. Premise

Brimley, 1994. You are an unnamed **private investigator**. A man — the
client, **Walter Blaine** — hired you to find his adult daughter,
**Mara Blaine**, who cut ties, "found religion" out past the highway,
and was **last seen in Brimley**. (The premise is delivered twice: the
skippable opening drive carries the hook; the PI's **case notebook** on
the spare-room writing table is the persistent, re-readable version —
client, quarry, the job. The notebook also **closes on itself**: once
the player has met Mara in the hive (`hive_seen`), re-reading the
case-board rewrites the entry — *"Subject: located. Recovery: declined."*
The book the game opens on is the book it closes on.)

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

**What the fold actually is — the rite.** Brimley isn't sealed by ambient
weather; the **congregation's ongoing rite seals it**, and the **Sign (the
Pallid Mask) is that rite's keystone**. The Sign's presence *passively
pulled* people here — they "found religion," converged, became the
congregation (Mara was a late arrival). Once the congregation was whole,
they *bound the town shut*. Think of the rite as a **pressure vessel**: it
holds the King's influence compressed inside Brimley, and the pressure
only mounts. The fold is not a cage for *you* — **it is the cage for
*Him***. That single inversion drives the endings (§6): the kneeling cult
you'll want to stop is the only lid on the pot.

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
| **Lodge Clerk** (was "the Innkeeper") | Complicit | The smiling trap-keeper. Too-warm host who keeps you comfortable and never admits the town won't let you leave; escalates over visits to something colder. The old fetch-quest chain (crate -> cellar bottle -> car keys) is **cut** -- the car answers only to the Sign now, so he has no keys to dangle. |
| **The Sheriff** | Cult enforcer | The law that keeps everyone in. He killed your car. His outdoor patrols are surveillance. |
| **The Preacher** | **Innocent dissenter** | A small-town minister who **names the cult from his own pulpit** — oblivious to *what* they truly are, but loud that they're no church. Your **2nd** conversation (his hubris — "God's on my side of the door") sets `preacher_doomed`; on the next entry he's **gutted on his own church floor**, his cross in the viscera (evidence #4). The town murders the ones who name them. |
| **The Store-Owner** | Quiet resister | The shop is gutted -- shelves bare, till empty, **nothing to sell** (the old vendor items, charcoal + paper, are purged). His value is what he risks saying out loud: frightened warnings about who to trust, never said outright. He is the one NPC who **names Walter Blaine on-page** (visit 3) and ties the family to Brimley as *history* — Walter came through years back with Mara's mother, "before things turned." He also reacts once to the Preacher's death (one-shot, gated on `preacher_doomed`). |
| **The Kid** | Innocent witness | Saw Mara walk into the corn and **tells you so** — the only honest account in town. What he gives you is the truth, not an object (the old keepsake item is purged; no inventory pickup). Children notice what adults pretend not to. |
| **Mara Blaine** | The quarry — **already turned** | A willing member of the congregation now. Finding her proves there was never anyone to save. She is in the **hive**. |
| **Cult / curse-priest / Watchers / the King in Yellow** | The corruption | Operate in the cornfields, the abandoned farmhouse, and the depths/hive below. |

---

## 3. The Threat Model

A single meter: **VISIBILITY** `[0, 1]` — how visible you are to the King
right now. Cultist gaze + Watcher figures push it up; **hiding** bleeds
it back down (`hide_spots` via E, plus passive corn-cover tiles).

**The flashlight (`[F]`) is the player's hand on that meter.** Found in
the woodshed (beside the axe and rope), it casts a long beam **cone** in
the facing direction through `DARK_SCENES` — the only way to read a black
room far enough ahead to navigate it. But it is **double-edged**: a light
in the dark is a thing that can be seen, so while it burns visibility
*climbs* (`VIS_LIT_RISE`, ~30s of held light alone is enough to erupt the
King). See more / be seen more. The cellar (`DIM_SAFE_SCENES`) is the one
exception — the beam is free there, your room to read by. In the deep cult
sites (`CULT_DARK_SCENES`) the beam won't catch at all: that dark is not
the kind light fixes, and the dread aperture rules instead.

**Investigating arms the threat.** The lethal apex is gated behind the
case:

- **Below 3 evidence:** visibility hitting `1.0` spawns **two cultists at
  the door you entered from** (a reinforcement wave; short cooldown so it
  pulses, not floods). The net tightens, but it isn't lethal yet.
- **At 3+ evidence:** that same trigger spawns **the King** — the lethal
  apex. *You make Brimley deadly by understanding it.*

---

## 4. Evidence — the thread that drags you down

A pool of six. **Any 3 = the point of no return** (arms the King). Three
sit on the **surface** — the **journal** (barn, #2), the **Ledger**
(cellar, #3), and the **Preacher** (church, #4) — so a thorough town search
arms Him while you're *still above ground*: a fair, brutal "you dug too
deep, too fast." The deeper truths — **Mara's cell** (#1), the **Mask**
(#5), and the **Congregation** (#6) — wait below, in the Works and the
hive.

| # | Evidence | Item / scene key | Where | What it proves |
|---|---|---|---|---|
| 1 | **Mara's Room** | `maras_room` (`robe` + `unsent_letter`, both pickups) | **Underground** — a convert's cell off the Sorting Hall (`works_sorting`) | She didn't rent a room and vanish — she *moved in* down here. She joined willingly; she was already home. The letter is its own re-readable inventory item so her last sane line — *"I'm not lost. I've never been this close."* — is still in the player's hand when she turns in the Dark |
| 2 | **Mara's Journal** | `mom_notebook` | The **barn** (`barn`) — behind the workbench | Her descent, in her own words (page 3 → the flashback) |
| 3 | **The Ledger** (the Lodge's guest register) | read in place | Arcadia cellar (`basement`) — hidden behind a loose wall panel | Guests who check in and never out — and your own name, signed in tonight, already among them |
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
route down and **no secret paths**. The surface is one connected sprawl:
the **Arcadia** (lodge, yard, cornfields) ↔ the **village** crossroads
(where the well is) ↔ the **Mistlands map, which *is* Brimley** — the
church (Preacher), the store, the sheriff, the school, the barn, the kid's
house, and the car all sit out there. Going *deeper* than the first
underground layer is gated by the **playscript**.

```
SURFACE         The ARCADIA (lodge + yard + cornfields) ─▶ the VILLAGE
                crossroads (the WELL) ─▶ the MISTLANDS map, which IS
                Brimley: church (Preacher), store, sheriff, school, barn,
                kid's house, and the CAR (Spread it). One connected sprawl.
                  │
                  │   THE ONLY WAY DOWN — a rope down the village WELL.
                  │   No other route. No secret paths.
                  ▼
THE WORKS       The cult's underground labour, reached by the well: a
(Basement Level)   built 7-room gauntlet (§9). Mara's cell branches off it;
                the Playscript + the Pallid Mask are found down here.
                  │
                  │   gated by the Playscript
                  ▼
DEEPER          The Depths → the Threshold (END IT / seal) → the Hive
                (the congregation; Mara is here).   (built)
                  ┊  lose to the King anywhere →
[not a place]   CARCOSA — the King's fire-and-masks catch-cutscene.
```

- **Surface:** one connected sprawl — the Arcadia (lodge/yard/cornfields) ↔ the village crossroads (the well) ↔ the Mistlands map that *is* Brimley (church, store, sheriff, school, barn, kid's house, the Preacher's body, the car). Sealed; sole way down = the well (rope).
- **The Works** (a.k.a. the Basement Level): the first underground layer, reached by the well — a built 7-room gauntlet (§9): Mara's cell, the Playscript, the Pallid Mask.
- **Deeper (playscript-gated):** the Depths, the Threshold (**End it**), and the Hive where **Mara** is — all built: the `dark` scene holds the kneeling congregation and Mara's one-shot recognition (evidence #6).

> **Naming, to avoid the collision:** the **lodge cellar** is the
> `basement` *scene* — the Arcadia's own cellar, a *surface* interior
> (holds the Ledger, #3; Mara's journal is in the barn). **The Works**
> (a.k.a. the Basement Level) is the underground stratum below the well.
> Different places, similar words.

**Carcosa is not a level.** Your King sprite is the floating
glow-of-faces, so Carcosa *is* the inside of Him: every mask drifting in
that fire is someone He already took. You only ever see it by losing.

---

## 6. How a run ends

| Trigger | Outcome | Presentation | Existing hook |
|---|---|---|---|
| **A cultist catches you** | The cult takes you for the ritual | Stark text card — **CAPTURED** (cult takes you alive; worse than killed, and feeds the hive) | `_trigger_death("cultist")` → `_tick_death` (exists) |
| **The King catches you** (vis `1.0`, *3+ evidence*, He reaches you) | He takes you into Himself | Brief cutscene: fire/hell, the floating masks of His sprite drifting in it — title **Carcosa** | `_trigger_death("king")` → `_tick_death` (exists; the bespoke `_trigger_closure` path was replaced by the shared death system) |
| **Seal the threshold** — *END IT* | Contain the hunger; Brimley + you become a hole in the map | Ending sequence. *"It is done. Nothing leaves Brimley again. Not the hunger. Not you."* | `_play_ending("seal_threshold")` (exists) |
| **Drive out with the Sign** — *SPREAD IT* | You pull the rite's keystone and carry it out; the release rides out *with you* as a latent bomb that detonates on His timeline | Ending sequence — the engine catches *for the first time*: *"You got out. You're the only one who ever has. Everyone will understand why, soon."* | `_begin_car_escape()` → `_play_ending("escape_alone")` (exists). Gates on the **Sign** (`sigil_rubbing`) **alone** — your own car, no keys; the fold is the only lock, and only a shard of Him opens it. |
| **Break the rite before sealing** — *YOU FUCKED UP* (a game over) | You tear down the rite *in place* — the obvious heroic move — with the source still open. The lid comes off a pressurized pot: His influence floods out, uncontained, here and now | Ending sequence: you destroy the altar/Sign/kneeling, one breath of quiet, then the flood — *"It was never a cage for you. It was a cage for Him."* | `_play_ending("rite_broken")`. Triggered at the **Sign Chamber altar** (the FIRST place you meet the active rite): a choice — *take the mask* (controlled) vs *tear it down* (the trap). |

### The Fork — the Deep Stair (where Seal and Spread split)

Both *chosen* endings branch from **one object in one place**: the
**Pallid Mask** at the **Deep Stair**, at the bottom of the Works. The
Mask *is* the Sign — pale board with the Yellow Sign burned into it — and
there is only one. You can do exactly one thing with it:

- **Feed it to the stair → go deeper (SEAL).** The Mask and the
  **Playscript** press into the black stone *together* (the Sign and its
  liturgy), and the way down opens; the rope behind you won't outlast it.
  Down is the Depths, the hive (Mara), and the Threshold you *End it* at.
  Spend the Mask here and you can never carry it out.
- **Keep it, climb out → spread it (SPREAD).** Turn back with the Mask
  still on you, take the rope up, and drive past the fold no one else can
  cross. What you carry out is the Sign itself, and Carcosa bleeds through
  the hole you made.

The case ends on that one question, and the PI hears it as two pulls:

> **Take it back.** *You have enough — the register, the names, the
> Preacher, the girl her father sent you for, and the Mask in your hands.
> A case heavy enough to drop the law on Brimley like a roof. Climb out
> while the rope holds and carry it all back to people with badges.*

> **Go deeper.** *Or you press the Mask and the Play into the stone
> together, the stair opens, and you go down — past her, to the thing all
> of this kneels to. Somewhere back up the rope you stopped being sure
> whether you mean to end it, or only to stand in front of it once.*

The "authorities" pull is the lie that dresses Spread as duty: carrying
the Sign out *is* the breach. "Deeper" is the Seal — you end it at the
source and become, with Brimley, a hole in the map. Both ways out damn
something (§1).

### The pressure model — and the trap

The rite is a **pressure vessel** holding the King compressed (§1). Three
ways to touch it, and an **order rule**:

- **SEAL** — go *past* the rite and cap the **source** (the Threshold).
  With the source capped the pressure has nowhere to go; the rite can
  lapse safely *because you sealed first*. Brimley and you become a
  permanent sealed hole.
- **SPREAD** — pull the keystone (take the Sign) and carry it *out*. The
  rite breaks, but the release is **channeled through the Sign/you** — it
  rides out as a latent charge, a bomb that goes off later, on His clock.
- **THE TRAP** — disrupt the rite *in place* before the source is sealed
  and without carrying the keystone out. You uncap a still-pressurized pot:
  **uncontained blowout, here and now.** Everyone, you included, taken
  immediately. (`rite_broken` game over.)

> **Order rule:** the rite is only safe to break *after* the Threshold is
> sealed. Break it early → catastrophe.

**Design intent — the cruel teach.** The game is sequenced so the player
**meets the rite first** (the Sign Chamber altar, kneelers worshipping His
face) — *before* they could possibly have sealed anything. The natural,
heroic instinct — *destroy this evil, stop the ritual, free the girl* — is
the **catastrophic** one. You're meant to reach for it, and to lose. The
horror is the lesson (Fear & Hunger: you die to learn). The only safe
moves are *seal the source first* or *carry the keystone away clean*; the
kneeling congregation that looks like the enemy is the only lid on the
pot.

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
  count (Mara's journal, the Ledger, the Sign rubbing) must ALSO fire
  a matching `_evidence()` call, or it won't move the gate.
- **Endings and deaths both exist (built).** `_ENDING_SCRIPTS` holds
  `escape_alone` (Spread it) and `seal_threshold` (End it). The death
  system is wired too: `_trigger_death(kind)` → `_tick_death` renders the
  **CAPTURED card** (`kind="cultist"`, ~2.8s) and the **Carcosa** furnace
  cutscene (`kind="king"`, ~3.5s); both end the run and return to title.

### Reworks the new fiction forces
- **One mouth down.** The well + rope is the *only* surface→underground
  route. Close the `well_passage` → `barn` hatch (and any other
  shortcut) so there are no secret paths down.
- The `polaroid` (Case Photo) item is **purged** — it was a placeholder
  cellar pickup, not real evidence. The Kid's keepsake is now what he
  *tells* you (§2), no inventory item. The way *deeper* (the Works → the
  Depths) opens on the **`playscript` + the Pallid Mask *together*** at the
  Deep Stair (§6, the Fork), and nothing is consumed to land at the well.
- `dark` room bodies (`ellie / father / mother`, old family) — **remove
  them** and their evidence beats. Cleaned up, not recast.
- The Deep Stair opens on the **`playscript` + the Pallid Mask together**
  (not the Play alone — §6, the Fork): the `playscript` is taken in the
  **Scriptorium** (`works_scriptorium`), the Mask in the **Sign Chamber**.
  Feeding both to the stair is the Seal path; keeping the Mask is Spread,
  so the Spread escape gates on holding the **Mask** (align the item key —
  it supersedes the old `sigil_rubbing` gate in §6). The `mist_house`
  surface chest is **emptied** (no surface source → no soft-lock), so the
  `black_figure` shadows + wind-cut stay dormant; the now-unreachable Clerk
  turn-in and alter/void offering chain are dead code (follow-up cleanup).
- `threshold` seal trigger item (`kid_drawing`) — re-fictionalize.
- **Innkeeper → Lodge Clerk** across dialogue + `DISPLAY_NAMES` (done).
  `son_room` is now **"the Clerk's Room"** (his pressed cult robe is the
  only tell); Mara's room is the new underground `maras_room` cell.
- **Item renames** (display only): `mom_notebook` → Mara's Journal, etc.
  (The `polaroid` item is removed entirely, not renamed.)
- **README rewrite:** PI premise, sealed town, drop "car broke down."

---

## 8. Still loose (design TODO)
- **The liminal-composition pass** (§10): per-scene level design —
  composed emptiness, long sightlines, uncanny repetition.
- Each NPC's dialogue arc — the principals (Clerk, Sheriff Vane, Preacher,
  Store-Owner, the Kid) are written; the bit-part villagers are thinner.

**Resolved (kept here as a record):**
- ~~The hive layout~~ — built (§5, §9; the `dark` scene + Mara's
  recognition).
- ~~Mara's journal text~~ — written (her last entries, `interiors.py` barn
  pickup), and the page-3 flashback stills are authored.
- ~~The death-card word~~ — **CAPTURED** (shipped; see §6/§7).
- ~~The client's given name~~ — **Walter Blaine** (§1).

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
| 4 | The Sorting Hall | `works_sorting` | Belongings of the vanished, 2 cultists, 3 hides (hardest crossing). A side door north → **Mara's room**. |
| 4a | **Mara's Room** | `maras_room` | A convert's cell off the hall: cot, her cult robe + the unsent letter. **Evidence #1.** A quiet beat off the gauntlet, 1 hide. |
| 5 | The Scriptorium | `works_scriptorium` | The Sign copied endlessly, 1 oblivious scribe, 2 hides. **The Playscript** — the one bound, whole Play among the flat copies — is taken here (the deep-gate key). |
| 6 | The Sign Chamber | `works_sign` | The Sign daubed on the wall + an altar; 3 kneelers + 1 patrol. **Lift the Pallid Mask → `sigil_rubbing` + evidence #5** (no charcoal — you take the object itself). |
| 7 | The Deep Stair | `works_deepstair` | The **playscript-gate**: spend the Playscript → opens to `depths_antechamber` **and snaps the rope** (the point of no return). |

**Rules wired:**
- **One mouth:** rope down the well only; the barn cellar hatch is now
  sealed (`scenes/interiors.py`). The tied rope persists as a two-way
  climb until it breaks.
- **Point of no return:** the playscript now lives *in* the Works (the
  Scriptorium), so you never carry it down. **Spending it at the Deep
  Stair** (Room 7) snaps the rope (`well_rope_broken`) — the gauntlet stays
  retreatable up the ladder until you commit to the Depths.
- **Playscript-gate:** Room 7 consumes the playscript to open the stair to
  the Depths (`deepstair_open`) and snaps the rope in the same act.
- The well sprite was redesigned and repositioned in `village` (col 16,
  row 11 — a landmark just off the road).

**Note:** the old cult chamber (`symbol_portal_room`) has been **removed
entirely** — its only entrance was the `haunted_house` hatch, which is now
a nailed-shut dead end (a deliberate in-fiction seal: the well + rope is
the sole way down). Saves are in-memory only, so there were no persistent
saves to keep it registered for. The `diner_gas_station` spur off the
cornfield was likewise removed (the car moved to the Mistlands); the
cornfield's east end is now a closed tree wall.

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
