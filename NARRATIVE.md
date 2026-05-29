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
client, quarry, the job. After the hive (`hive_seen`), re-reading the
case-board rewrites the entry — *"Subject: located. Recovery: declined."*)

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
*not* the Innkeeper's home. The PI came on purpose, and the town strands
them. **The car breaks because the fold breaks it** — the engine turns
over and never catches. No one in Brimley sabotaged it; the eldritch
seal won't let machines leave any more than it lets feet leave. The
Sheriff did *not* kill the car (cf. §2). It's the same wrongness that
loops the roads.

**Setting note 2 — where this is.** Brimley is a small town in
northern Minnesota, bumfuck nowhere. Walter Blaine is in Minneapolis.
**No local in Brimley has ever met Walter** — there is no reason any
of them would know an outsider from a city a long way south. The PI
is the only one who knows the client. Mara was an outsider too: she
came north to Brimley a few months ago, was passively pulled by the
Sign, "found religion," and joined the cult. She is one of the
newcomers (§2).

---

## 2. The Cast — locals and newcomers

Brimley has a **population split**, and reading it *is* the
investigation:

- **Locals** — born here, lived here, watched their town fall in on
  itself over the last few months. They don't understand what's
  happening. They haven't mapped the fold. They've just learned the
  lesson of futility — you can't drive out, the roads come back, the
  store doesn't get deliveries anymore, your husband walked out to
  flag down help and didn't come back. They cope by surrender, not
  by knowledge. They still try (Royce drives out again every week)
  but they expect nothing.
- **Newcomers** — arrived in the last weeks and months, drawn here
  by the Sign's passive pull. They "found religion." Mara was one
  of the latest. Once the congregation was whole they bound the
  town shut — the fold closed AROUND the locals, who didn't ask for
  any of this. The newcomers smile and act like they belong here.
  They do not. They are the cult.
- **The PI** — the only outsider to enter since the fold closed.
  Unclaimed; not yet His; the one thing the fold doesn't own.

The locals are TRAPPED WITH the newcomers. That's the specific dread.
Not "everyone is infected" — *some* people, *recently*, that nobody
ordered and nobody can refuse.

> **The cultists have to eat.** They have bodies. They sleep. They
> buy food. The Lodge is newcomer-run and supplied; the store's
> shelves are bare because the deliveries stopped when the fold
> closed; some locals can grow their own and some can't, and the
> ones who can't are sliding cult-ward by attrition. The horror is
> domestic — a cultist at the diner counter eating a sandwich,
> returning a borrowed shovel, picking up the Tisdale boy's mail.

| Who | Origin | Their thread |
|---|---|---|
| **Lodge Clerk** | **Newcomer** (early arrival, became recruiter) | The smiling trap-keeper. Runs the only inn in town, the only place an outsider would naturally stay. Too-warm host who keeps you comfortable and never admits the town won't let you leave; escalates over visits to something colder. The old fetch-quest chain (crate -> cellar bottle -> car keys) is **cut** -- the car answers only to the Sign now, so he has no keys to dangle. |
| **The Sheriff** | **Local** | Born here. Has stood at the rim of the well. Knows the fold is real and that none of his deputies will be coming back. **He did not kill your car — the fold did.** He patrols because patrolling is what he did before; he tells outsiders "leave, son" out of muscle memory, even though he knows you can't and he can't either. Not a believer, not a cultist. A witness who can't help. The badge is just clothing now. |
| **The Preacher** | **Local — innocent dissenter** | A small-town minister who **names the cult from his own pulpit** — oblivious to *what* they truly are, but loud that they're no church. Your **2nd** conversation (his hubris) sets `preacher_doomed`; on the next entry he's **gutted on his own church floor**, his cross in the viscera (evidence #4). The town murders the ones who name them. |
| **The Store-Owner** | **Local — quiet resister** | The shop is gutted -- shelves bare, till empty, **nothing to sell** (deliveries stopped when the fold closed). His value is what he risks saying out loud: frightened warnings about who to trust, never said outright. He has a one-shot reaction to the Preacher's death. **He does not know Walter Blaine.** No local does — Walter is a voice in Minneapolis and Brimley locals would have no reason to recognize the name. |
| **The Kid** | **Local — innocent witness** | Saw Mara go to the well with the procession and **tells you so** — the only honest account in town. What he gives you is the truth, not an object (the old keepsake item is purged; no inventory pickup). Children notice what adults pretend not to. |
| **The Brimley chorus** (Hettie, Old Pell, Mrs. Calder, Royce, Garrick, the Tisdale boy) | **Locals** | The town still tries to live. Hettie keeps the store open. Mrs. Calder sets her husband's plate every night for a man who walked out to the highway. Old Pell stopped marking the calendar. Royce drives the river road out every week and comes back into Brimley every time. They all know the fold is real; none of them understand it. **Naming the principal locals** (the Sheriff, the Preacher, the Kid, the Store-Owner) is **still TODO** — see §8. |
| **Mara Blaine** | **Newcomer** — the quarry, **already turned** | Arrived in Brimley a few months ago, "found religion," joined the cult, **went down the well** (not into the corn — she is not a "corn lady"). A willing member of the congregation now. Finding her proves there was never anyone to save. She is in the **hive**. |
| **Walter Blaine** | **Outsider, off-screen** | The client. A Minneapolis voice on a phone that no longer connects. **No one in Brimley has ever met him.** He exists only through the PI's case notebook and (optionally — see §8) the polaroid he sent with the case. |
| **Cult / curse-priest / Watchers / the King in Yellow** | **Newcomers + Their god** | The congregation are the newcomers. The Watchers and the King are the corruption they're channelling. |

> **The fold is incomprehensible, not predictable.** Locals haven't
> "figured out" which roads still work. They've learned that *none*
> of them do. There is no workaround until the Sign. When a local
> talks about the fold, they describe failure, not pattern: *"I've
> tried them all. They all bring you back."*

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

**The pistol — agency the world takes back.** The PI carries a sidearm from
the start (limited rounds; caches in the woodshed, the cellar, the Sheriff's
office). It is hung on the **same 3-evidence line** as everything else, so
crossing that line turns the world against you on every axis at once:

- **Below 3 evidence:** a clean shot **kills** a cultist (they fall and
  later respawn), and cultists stay **mundane** — no bloom. You have agency.
- **At 3+ evidence:** the shot only **staggers** them (a brief stun), and a
  cultist that locks on **blooms into His maw** (the vessel transform). *The
  deeper you see, the less the world lets you kill.*

The gun never makes you safe: **capture-on-contact is still the fail state**
(a cultist that reaches you takes you — CAPTURED). A shot is **loud** — the
cult hears it and investigates. The flashlight, the splitting axe (chop +
stun), and hide-spots remain; the pistol sits alongside them, not over them.

**The gun can be turned on the innocent.** A clean round drops any
**local** instantly — Hettie, the Sheriff, the Tisdale boy — *regardless*
of the evidence gate (that gate only ever protected the cult). It is never
without cost: a local kill **spikes visibility** hard (the town turns its
head) and pings the cult to **investigate the body**, and the corpse
**stays where it fell** — it is there, in its blood, every time you walk
back through. The bodies persist for the rest of the run.

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
| 1 | **Mara's Room** | `maras_room` (robe + unsent letter) | **Underground** — a convert's cell off the Sorting Hall (`works_sorting`) | She didn't rent a room and vanish — she *moved in* down here. She joined willingly; she was already home. Her last sane line — *"I'm not lost. I've never been this close."* — stays in your hand all the way to the Dark |
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

## 4b. Infestation — the world rotting as you understand it

Knowing dooms you, and it **shows**. Surface corruption is a pure,
monotonic function of the evidence count — `_infest_stage = min(3,
evidence)` — and it is deliberately **front-loaded** to peak exactly as
you commit underground at 3. (The hard lock is *opening the Deep Stair*,
not crossing 3; you can still resurface — and a fully-rotted town greets
you when you do.) The underground is the asymmetry: it is **already
wrong from the first rung** (a baseline at 0 evidence) and **deepens on
the full count**, so the well is a wound the rest of the world only
catches up to.

What rises with the stage:

- **The ground curdles.** Escalating rot decals spread across the
  surface — phantom marks and dead crows, then claw-marks, the Sign, and
  gore, then hanging figures by stage 3. The **safe rooms** (your cot,
  the kid's house) stay clean until stage 3, then turn too: *even here.*
- **The people go — and *how* they go means something.** The
  **peace-makers convert** — the welcoming newcomer (first, at stage 1),
  Mrs. Calder who "hears the door" (2), Garrick and Royce (3). A convert
  is **passive cult**: they turn toward you and their watching raises
  visibility, but they never chase or grab. The **resisters mutate** —
  Hettie (2), Old Pell and the Tisdale boy (3): they keep their identity
  and their defiance, but their bodies betray them (eye-voids, the Sign
  etched into the chest, a jaundiced cast). Still themselves, rotting.
- **Sheriff Vane is neither.** The last holdout. At stage 3 his office is
  no longer a place you visit — he has gone **hollow**, a unique threat
  encounter: he stands, says the line he can't say anymore ("leave,
  son… I can't say it"), then comes for you, slow and unrelenting. He
  catches you → **TAKEN INTO CUSTODY**. You escape by getting back out
  his door (a run outpaces him). The best ammo cache in town is now his.
- **The dead don't rest.** A persisted **corpse** you left grows `mold`
  with the stage — grey-green discolour, then pale fungal threads, then a
  corn-stalk and the Sign growing up out of the body. Claimed, never
  risen.

---

## 5. The Descent — "how deep does this go"

The descent is strictly **vertical**, and it has exactly **one mouth**:
the **well in Brimley**. You go down it on a **rope** — there is no
other route down and **no secret paths**. The surface is one connected
sprawl: the **Arcadia Lodge** (lodge, yard, cornfields) ↔ **Brimley**
(the town itself — the well, the church, the store, the sheriff's
office, the school, the barn, the kid's house, and the car). Going
*deeper* than the first underground layer is gated by the
**playscript**.

> **Brimley is one place.** The old code had two scenes (`mistlands`
> and `village`); they were merged into a single `brimley` scene so
> the world reads as one continuous town: walk west to find the well,
> east to find the church, north to find the car. The "Mistlands"
> name is retired — there was no separate Mistlands; that was always
> Brimley.

```
SURFACE         The ARCADIA LODGE (lodge + yard + cornfields) ─▶ BRIMLEY
                (one map: well at the centre, church, store, sheriff,
                school, barn, kid's house, named locals on their stoops,
                the CAR parked at the edge of town).
                  │
                  │   THE ONLY WAY DOWN — a rope down the well in Brimley.
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

- **Surface:** the Arcadia (lodge/yard/cornfields) ↔ Brimley (one map: the well, the church, the store, the sheriff's office, the school, the barn, the kid's house, the locals, the car). Sealed; sole way down = the well (rope).
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

### Load-bearing invariants (do not regress)

The reworks the new fiction forced are all shipped. What must stay true:

- **One mouth down.** The well + rope is the *only* surface→underground
  route. The barn→well_passage hatch is nailed shut from below; no
  secret paths.
- **Deep Stair gate.** Both the **Playscript** (taken in the Scriptorium)
  and the **Pallid Mask** (taken in the Sign Chamber) are required to
  open the stair to the Depths. Spending both is Seal; keeping the Mask
  is Spread; tearing the Mask down at the Sign Chamber altar is the
  Trap (§6).
- **The car answers only to the Sign.** No keys, no tab, no fetch chain
  — Brimley itself is the lock and only a shard of Him opens it.
- **Innkeeper → Lodge Clerk** throughout. `son_room` is the Clerk's
  Room (his pressed cult robe is the only tell). Mara's room is the
  underground `maras_room` cell off the Sorting Hall.
- **Item keys are load-bearing** (saves and game logic depend on them):
  `mom_notebook`, `sigil_rubbing`, `playscript`, `cross`, `robe`,
  `unsent_letter`, `flashlight`, `rope`, `lumber_axe`, `woodshed_key`.
  Display names and fiction may change; keys may not.

---

## 8. Still loose (design TODO)
- **Name the principal locals.** The Sheriff, the Preacher, the
  Store-Owner, the Kid are role-tags. Locals in a small town know
  each other by name. The wax-museum quality of the cast is partly
  this. (The Brimley chorus is already named: Hettie, Old Pell,
  Mrs. Calder, Royce, Garrick, the Tisdale boy.)
- **The liminal-composition pass** (§10): per-scene level design —
  composed emptiness, long sightlines, uncanny repetition.
- **Curse-priest in dialog / evidence beats.** The `curse_grove`
  hidden fold (§11) gave him a visible workshop and a clear thing
  he's doing — but he's still mute. Wire him into a beat (a line
  if you catch him at the brazier, or evidence pulled from the
  workshop).
- **Food scarcity — the VISUAL pass.** The dialogue side is done
  (Hettie: "The shelves don't empty anymore... No deliveries."; the
  Store-Owner: "Shelves are bare. Till's been empty since the spring").
  What's left is the world art: visibly bare store shelves, gardens on
  some lots and not others, a cultist eating at a counter. Wallpaper,
  not a mechanic.

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
- The well sprite was redesigned and repositioned in `brimley` (the
  east village square — a landmark just off the road).

**Note:** the old cult chamber (`symbol_portal_room`) has been **removed
entirely** — its only entrance was the `haunted_house` hatch, which is now
a nailed-shut dead end (a deliberate in-fiction seal: the well + rope is
the sole way down). Saves are in-memory only, so there were no persistent
saves to keep it registered for. The `diner_gas_station` spur off the
cornfield was likewise removed (the car lives in the lodge yard); the
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

---

## 11. The Fold, made mechanical

The bible's central image -- *the roads loop, the corn never ends, you
walk through the woods only to be spit out where you walked in* -- now
has mechanical existence beyond the dread aperture. The outside world
is built as a torus, with hidden direction-sensitive folds layered on
top.

### Permeable forest border

The wrap is the transition; the forest is the camouflage. Instead of a
hard tree-wall perimeter, every outdoor scene gets a **scattered
forest band** ~6-7 tiles deep around its edge. Trees are seeded
probabilistically (densest at the very edge, fading to ~0 at the
band's inner edge), mixed solid/passable so the player can push
through, with a blotchy ground variation (grass, dim grass, corn
cover) underfoot. The visual sameness across all four edges is what
hides the wrap: the player walks into the trees, the wrap fires
somewhere in the middle of the band, and they emerge into the same
forest on the other side.

Roads cut through the band as clean dirt corridors -- they're the only
*predictable* navigation. Garrick (an old local at the well) drops the
warning offhand: *"Stay on the roads. People who go off the roads
come out wrong-side."* Locals don't theorise about the fold; they
just know don't go off the path.

The helper (`scenes/base.scatter_forest_band`) is char-parameterised:
the outdoor scenes get trees ('T' solid / 'p' passable); the
`cornfield_maze` gets corn ('C' solid / 'A' passable) so the maze's
endless-corn identity is preserved while the outer wall still wraps
seamlessly. Two de-clump passes guarantee no impassable cluster --
every solid wall in the band has at least one walkable neighbour.

Hideable bushes are scattered through every band. A bush is a walkable
decoration; the floor under each one is forced to ':' corn cover, which
the existing `player.hidden = "corn"` system reads, so stepping into a
bush hides you immediately.

### Per-scene torus

`brimley`, `cornfield_maze`, `forest_path`, and the Lodge yard
(`our_house_area`) all wrap on the relevant axes:

- **brimley.wrap_x** -- the cross-town road at row 24 loops
  east-west. Walking off either side carries you back in on the
  other.
- **brimley.wrap_y** -- the perimeter forest loops north-south.
- **cornfield_maze.wrap_x = wrap_y = True** -- corn never ends in
  any direction. The exit tiles (^ to brimley, ! to forest_path, Z
  to the curse-grove) are the only escape, and finding them is the
  whole point.
- **forest_path.wrap_x = wrap_y = True** -- the woods spit you out
  where you walked in.
- **our_house_area.wrap_x** -- walking east past the Lodge wraps you
  back to the west. There is no past-the-Lodge highway.

### Cross-scene macro-loop

Three direct south-chain exits close the outdoor world into one
closed system:

- **brimley** south edge ('M' tile, col 48 row 99) → cornfield_maze
- **cornfield_maze** south ('!' tile) → forest_path
- **forest_path** south ('S' tile) → brimley north

Walking south through any of the three eventually returns the player
to brimley north. No direction escapes.

### Seamless outdoor crossings

Transitions between any two of the `SEAMLESS_WORLD_SCENES` skip the
fade, keep the music playing, and preserve the player's screen
position. The outside world reads as one continuous wrapped space.
Indoor doorways (Lodge interior, the Works, cellar) still fade --
they *are* doorways, and the player should feel that.

### Wrap-aware NPC AI

Cultists in wrap scenes compute distance and chase direction modulo
the world dimensions. A cultist on the east edge reads a player on
the west edge as one tile away (through the wrap) and pursues that
way. The fold stops being an escape.

### Direction-sensitive hidden folds

Three hidden scenes are accessed only by walking a specific tile in a
specific direction. From any other angle the tile reads as floor and
the player walks over it without consequence. All three are in
`SEAMLESS_WORLD_SCENES` so the crossing has no fade -- the player
stumbles into the fold without realising they crossed a boundary.

| Scene key | Where it lives | Access | What it shows |
|---|---|---|---|
| `curse_grove` | new scene | `cornfield_maze` tile (6, 10), walked WEST | The curse-priest at his fire pit -- effigies in a circle (one per local being cursed), polaroid board of faces, hanging figures at the corners. Gives the priest a home and a visible thing he's doing (§8) — but he is still mute here; wiring him into dialog / an evidence drop is **still open** (§8). |
| `lodge_arrival` | new scene | `our_house_area` tile (5, 12), walked NORTH | The Lodge porch at the moment Mara walked up to it. Mara with a suitcase, the Clerk smiling in the doorway. Neither sees the PI. Makes the bible's "she chose this" concrete -- the player *witnesses* the choice. |
| `highway_walk` | new scene | `country_lane` tile (28, 6), walked EAST | A stretch of empty highway. Two figures walk east, their backs to the PI -- the locals who walked out to flag down help. The road wraps; they stay ahead; nobody arrives anywhere. |
| `husk_grove` | new scene | `cornfield_maze` tile (21, 8), walked EAST | A small clearing where the cult assembles its corn-dolls. Two altars used as workbenches, unfinished dolls scattered, a stalk-marker, a candle still lit. No NPC -- the work is here, the worker isn't. |
| `scarecrow_ring` | new scene | `cornfield_maze` tile (2, 14), walked WEST | A ring of six scarecrows facing inward around a doubled Yellow Sign in charred dirt. Two braziers, bloodstains underfoot. The cult's central mark in the corn. |

**In-maze fold relocations.** Two additional tiles inside the
`cornfield_maze` (one at (8, 6) walked SOUTH, one at (16, 11) walked
NORTH) don't open a new scene -- they teleport the player to another
spot in the same maze, camera offset preserved so the swap is
invisible at the moment of crossing. The player notices when their
surroundings stop matching.

**Visible perimeter side passages.** The maze's outer wall has four
clear dirt-lane gaps (west edge at rows 5 + 13, east edge at rows 8 +
16) that look like ways out. Walking through one wraps the player to
the opposite edge -- the maze visibly has many exits and all of them
loop.

The framework (`Scene.add_exit(direction=...)` + `find_exit_at(facing=)`)
is general -- more direction-sensitive folds can be added as wanted.
