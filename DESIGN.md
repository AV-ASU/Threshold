# THRESHOLD — Design Notes

> How the systems deliver the fiction: the threat model, world rot,
> the implementation map, open design threads, the Works level design,
> art direction, and the fold mechanics. The FICTION itself (premise,
> door, timeline, cast, evidence, descent, endings, canon invariants)
> lives in `NARRATIVE.md`, the story bible; open work lives in
> `TODO.md`. These sections were relocated whole from the old
> NARRATIVE.md (2026-07 split); §-references here use this file's own
> numbering, and cross-references into the bible say `NARRATIVE §n`.

---

## 1. The Threat Model

A single meter: **VISIBILITY** `[0, 1]` — how visible you are to the King
right now. Cultist gaze + Watcher figures push it up; **hiding** bleeds
it back down (passive corn-cover tiles, plus the few crawl-**under**-
furniture `hide_spots` via E).

> **The King is a verdict, not a monster** *(the design spine of the roaming
> King; the mechanics + tuning live in `CLAUDE.md` and the `KING_*` config,
> this is the canon behind them).* Internalize these or the mechanics land
> hollow:
> - **He feeds on attention.** Worship and war are the same meal — the kneeling
>   zealot and the charging hero both point their regard at Him and feed Him.
>   The one thing that starves Him is **indifference**: a god known and left
>   unworshipped, an evil left to rot. The survivable path is always to deny
>   Him your visibility, never to confront Him. **Visibility *is* His
>   attention** — the meter is how hard He is looking at you, not a stealth
>   gauge.
> - **Lucky, not omniscient** (NARRATIVE §1). He does not know where you are; He hunts,
>   has to *find* you, and *searches* when He loses you. Keep the seam of chance.
> - **The asymmetry is godhood.** You can never reach Him (the road grows
>   between you; He won't let you close); He can always reach you (the portal).
>   Distance is His to spend, never yours.
> - **Knowledge is the danger; agency is the trap.** Reaching the evidence gate
>   is what arms Him; the instinct to confront is the mistake.
> - **The horizon King.** By default He idles at the **end of the road north**,
>   full-bloom and sky-huge but **indifferent, not hunting** — the safe look at
>   the god, the thing that broke Royce, and the wall the Sign later gets you
>   past (the SPREAD setup). The road grows between you so you never close it.
> - **Systemic, not scripted.** The rules produce the dread; every run authors
>   its own. We guarantee the physics of fear, not the scene.

**Breaking a chase is positional.** The cult AI now has **real line of
sight** (`Scene.clear_sight_line` over the `blocks_sight` predicate): a
wall or a solid prop between a cultist and you drops their lock, and they
fall to SEARCH (walk to where they last saw you, mill, give up). So you
shake a pursuer by **putting cover between you** — round a pillar, slip
behind a wall, melt into the corn — not by pressing E at a marked spot.
The only E-press hides left are the handful where you **crawl under**
furniture (a bed, a desk, the cot), a distinct act you can't do by simply
walking. The apex pursuers (the King, the hollow Sheriff) are **exempt** —
they never lose sight of you.

**The flashlight (`[F]`) is the player's hand on that meter.** Found in
the woodshed (beside the axe), it casts a long beam **cone** in
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

- **Below 3 evidence:** visibility hitting `1.0` musters **a wave of two
  cultists at the door you entered from** (a reinforcement pulse on a
  cooldown, and only once the cult is awake at 1+ evidence — the ev-0 town
  spawns no patrols at all). The net tightens, but it isn't lethal yet.
- **At 3+ evidence:** the King himself **walks** — the roam arms and He
  hunts the world room by room (the design spine above; mechanics in
  `systems/king_roam_mixin.py`). *You make Brimley deadly by understanding
  it.*

> **The King's pursuit is personal.** He isn't drawn to noise — he's drawn
> back to the **face he met in the dream** (NARRATIVE §2). Read visibility as *how
> far you've re-entered His attention*; at `1.0`, the one soul that got
> close and walked away is worth coming for in person.

**The pistol — the false-power threshold (it exists to fail).** The PI
carries a sidearm **from the start**, and that is deliberate: power has to
be *believed in* before it can be *taken away*. The gun is the player's
first answer to fear — *I can fight this* — and the whole game is the slow
proof that the real thing **cannot be shot**. It is hung on the **same
3-evidence line** as everything else (limited rounds; caches in the
woodshed, the cellar, the Sheriff's office), so crossing that line strips
your agency on the exact line that arms the King:

- **Below 3 evidence:** a clean shot **kills** a cultist (they fall and
  later respawn), and cultists stay **mundane** — no bloom. You have agency.
- **At 3+ evidence:** the shot only **staggers** them (a brief stun), and a
  cultist that locks on **blooms into His maw** (the vessel transform). *The
  deeper you see, the less the world lets you kill.*

The gun never makes you safe: **capture-on-contact is still the fail state**
(a cultist that reaches you takes you — CAPTURED), and **the King cannot be
shot at all** — you can't fire down a direction you can't point at (NARRATIVE §2).
A shot is **loud** — His gaze hears it. The flashlight, the splitting axe
(chop + stun), and hide-spots remain; the pistol sits alongside them, not
over them.

**The cruelest truth of the gun: it only ever works on the victims.** A
clean round drops any **local** instantly — Hettie, the Sheriff, the
Toby — *regardless* of the evidence gate (that gate only ever
protected the cult). So the one thing your weapon reliably kills is the
**claimed innocents you came to help and can't save** — your instrument of
control, lethal only in the most useless, self-damning direction. It is
never without cost: a local kill **spikes visibility** hard (the town turns
its head) and pings the cult to **investigate the body**, and the body
**lies there for the rest of the run**.

> **The kill costs in the moment, and then it keeps (2026-07 ruling:
> dead locals stay dead).** The visibility spike and the town's turned
> head land in the moment; the body itself is written to the
> **dead-locals ledger** (`save.arg("dead_locals")`) and laid back down
> where it fell on every re-entry (`_apply_dead_locals`, run from
> `load_scene_now` before the rot pass). Nobody leaves Brimley, not
> even by dying (NARRATIVE §5); a New Game clears the ledger, and the
> cot save snapshots it like any other arg. Guarded: flow §32.

---

## 2. World rot — the town curdling as you understand it

> **Reconciles with NARRATIVE §2.** The town was *already* wholly claimed,
> invisibly, before you arrived — nobody here is mid-conversion. The
> world rot is **not the townsfolk changing**; it is the **veil thinning
> for the PI** as he learns too much and He turns His eye back on the face
> from the dream. "Convert" and "turn" are how the truth **surfaces to
> you**, not allegiances being switched. Underneath, they were always His.

> **The people underneath the rot are read by their WANTING (§8).** The
> world rot is how the truth surfaces to the PI; §8 is why each local is
> what the rot reveals. The two are one picture: the door strands every
> want in Brimley, and the rot is the veil thinning until the PI can see
> the stranding.

Knowing dooms you, and it **shows**. Surface corruption is a pure,
monotonic function of the evidence count — `_rot_stage = min(3,
evidence)` — and it is deliberately **front-loaded** to peak exactly as
you commit underground at 3. (The hard lock is the **blast at the
deepest face**, not crossing 3; you can still resurface — and a
fully-rotted town greets you when you do.) The underground is the asymmetry: it is **already
wrong from the first rung** (a baseline at 0 evidence) and **deepens on
the full count**, so the well is a wound the rest of the world only
catches up to.

What rises with the stage:

- **The ground curdles.** Escalating rot decals spread across the
  surface — phantom marks and dead crows, then claw-marks, the Sign, and
  gore, then hanging figures by stage 3. The **safe rooms** (your cot,
  the kid's house) stay clean until stage 3, then turn too: *even here.*
- **The air thickens — a drifting pale-yellow ashfall.** As the PI
  understands more, a slow fall of jaundiced ash sifts across the world,
  denser as you near the source (and never on the Threshold itself, NARRATIVE §2).
  It is **the pressure of the vessel made visible** — His attention
  settling on you, not snow, not weather. Light at stage 1, a steady
  yellow drift by stage 3.
- **The people go — and *how* they go means something.** The
  **peace-makers convert** — the welcoming newcomer (first, at stage 1),
  Mrs. Calder who "hears the door" (2), Garrick and Royce (3). A convert
  is **passive cult**: they turn toward you and their watching raises
  visibility, but they never chase or grab. The **resisters turn** —
  Hettie (2), Garrick, Old Pell and Toby (3): they keep their identity,
  their defiance, and their **exact bodies** (the town reads NORMAL; the
  wrongness is the *place*, not the people, NARRATIVE §2). What betrays them is what
  they **say**: their talk goes flat and off, reporting small ordinary
  things from behind a face that no longer means them, and never
  acknowledging the gap. The dread is the mundane line delivered by
  someone who is no longer home behind it — one impossible thing, and it
  is the door.
- **Sheriff Vane falls last, and hardest — and his fall is
  player-driven (TODO #2a, built 2026-07).** The last holdout, and the
  one soul in town **claimed but unattuned** (he never dreamed the door;
  NARRATIVE §4). The world rot never turns him on its own; a hidden
  **despair/hope ledger** decides his fate (`vane_despair`, the `VANE_*`
  config block; surfaced only as his **mood** — the conversation's
  framing line and the beats — never a number). **Hope has one
  currency:** the PI **sharing a real discovery** with him (the
  `share_*` exchanges in `VANE_CONVO`, `_vane_share`) — the same act is
  the **trust** that opens his investigation thread (the blind-cultist
  *how* waits on a share, not on evidence found), so tending him and
  earning his help are one gesture. **Despair** comes from the beats
  that read, to a man who wants it all to *end*, as permission: the
  preacher's murder (`+VANE_DESPAIR_ACT`) and the newspaper's front page
  (`+VANE_PAPER_DESPAIR` — the break lever, TODO #2; the give-beat
  telegraphs it as mood). Net despair at `VANE_HOLLOW_AT` **latches the
  hollow turn** (`vane_hollow`) — once hollow, no return — and hope
  banks only to `VANE_DESPAIR_FLOOR`, so rapport is real but never
  immunity. The hard **neglect override** beats the ledger
  (`_vane_is_hollow`, evaluated at his office door, which every share
  must walk through): reach the descent (**3 evidence**) having never
  let him into a single discovery, and his last hope, that someone was
  actually working it, dies with the silence, and he falls. Tend him
  instead and he **holds** — the holdout who lives as much as anyone
  here does. The encounter itself is unchanged either way: on the next
  office load `_spawn_hunting_sheriff` stands the hollow lawman up
  (`sheriff_hollow` sprite), he holds for an intro beat — says the line
  he can no longer finish — then force-chases (`_tick_sheriff`), slow
  and unrelenting; contact → **TAKEN INTO CUSTODY**; a run outpaces him
  back out his door; the best ammo cache in town is his. Guarded end to
  end by `tests/flow.py` §17f. **Why the King takes him so
  completely:** what Vane wants most is for all of it to *end*, and the
  King can only ever offer endless *more* — the one appetite the door
  cannot answer; and being unattuned, the claim can **compel him but not
  steer him** — the only soul who runs *from* the door instead of toward
  it, so he goes **hollow** as a malfunction, not a convert.
- **The dead.** A local you shoot lies where they fell **for the rest
  of the run** (2026-07 ruling: dead locals stay dead). The kill is
  written to the `dead_locals` ledger and the scene lays the body back
  down on every re-entry (§1); the rot pass skips the dead, and a shot
  Vane never stands back up hollow — his body holds the office instead
  of the `sheriff_hunt` spawn, whatever his ledger says.

---

## 3. Implementation map (code ↔ canon)

**Load-bearing — do NOT change:** item *keys* (`systems/items.py`) and
scene *keys* (`scenes/__init__.py`). Saves and game logic depend on them.
Only display names and fiction change.

- **King gate:** `systems/king_roam_mixin.py` `_tick_king_roam` (the sole
  King tick). The roam arms at `KING_GATE_EVIDENCE` (3); below the gate a
  maxed meter (`visibility >= 1.0`, cult awake at `CULT_WAKE_EV`, scene not
  in `KING_FREE_SCENES`) musters `REINFORCE_COUNT` (2) cultists at
  `_king_anchor` on a cooldown (`_muster_reinforcements`).
- **Evidence count:** `len(self.save.arg("evidence", []))`.
- **Evidence logging:** `_evidence(game, name, content)` in
  `scenes/dialogue.py` → appends to `save.arg("evidence")`, shown in the
  notebook UI.
- **Threat geography constants** (`systems/config.py`, star-imported by
  `game.py`): `CULTIST_SCENES`, `SAFE_SCENES`, `OUTDOOR_SCENES`,
  `DARK_SCENES`, `KING_FREE_SCENES`.
- **Evidence is a log, not inventory.** "Evidence" = entries appended to
  `save.arg("evidence")` by `_evidence(game, name, ...)` (shown in the
  notebook UI). The count for the 3-gate is `len(save.arg("evidence"))` —
  it counts *log entries*, not held items. So every pickup that should
  count (Mara's journal, the Ledger, the Pallid Mask) must ALSO fire
  a matching `_evidence()` call, or it won't move the gate.
- **Endings and deaths both exist (built).** `_ENDING_SCRIPTS` holds
  `escape_alone` (Spread it) and `seal_threshold` (End it). The death
  system is wired too: `_trigger_death(kind)` → `_tick_death` renders the
  **CAPTURED card** (`kind="cultist"`, ~2.8s) and the **Carcosa** furnace
  cutscene (`kind="king"`, ~3.5s); both end the run and return to title.

## 4. Still loose (design TODO)

> **2026-06 canon-alignment pass (settled with the user).** A batch of
> story/canon decisions were locked that session; the **concrete code
> changes** to make the game match live in **`TODO.md`** (the former
> `GAME_CHANGES.md` handoff tracker, folded into `TODO.md` in 2026-07).
> The decisions themselves are canon now and live where canon lives:
> the Ledger placement, Sable as the most-attuned local, Royce, Mrs.
> Calder, the testimony fragments, the Mask-as-permission temptation,
> the keystone spent at the Threshold, the lure chain, and the awareness
> model are all stated in `NARRATIVE.md` (§§1, 2, 4, 6, 8, 9). This
> section keeps only what is genuinely still loose below.

- ~~**Cultist movement → dynamic AI, not preset patrol coordinates.**~~
  **DONE.** The hard-coded `waypoints=[...]` are gone from `_cultist` and all
  14 spawns. SCOUT now **pure-roams** — each cultist picks its own reachable
  goals, wanders, pauses to scan — and pursuit is **cover-aware** in two
  ways. (1) **Detection is line-of-sight**, not X-ray: `has_los` gates on
  `Scene.clear_sight_line` (the `blocks_sight` predicate — walls + solid props
  occlude, windows + water do not), so stepping behind cover drops the lock
  and the cultist falls to SEARCH. This is the hide system now — you break a
  chase by **positioning**, not by an E-press (the old "behind" `hide_spots`
  were removed as redundant; only crawl-**under**-furniture hides remain). (2)
  **Pathing routes around cover**: a wrap-aware BFS nav layer
  (`Scene.nav_grid`/`nav_clear_line`/`nav_path`/`nav_toward` in
  `scenes/base.py`) steers pursuers **around** the volumetric props (pillars,
  pews, cots, basins) while staying a straight shot in the open. Both wired
  into both cult paths (`enemy.py` underground + `npc.py` surface chasers); the
  `_force_chase` apex stays straight and **never loses sight** (relentless). A chase carries **through
  portals and folds** alike (`_note_fold_pursuit`/`_tick_fold_pursuit` —
  surface NPC chasers AND underground Enemy cultists, the latter spawned native
  to the destination), with **SAFE_SCENES the one refuge** that always shakes
  it. Guards: flow.py §20 (no preset routes + nav routes around cover) and §21
  (portals carry the chase; the refuge is never breached).
- ~~**Scrub the eat-cult fiction (code ↔ NARRATIVE §2).**~~ **DONE.** Canon is a
  **claiming** cult that renders no bodies (no cannibalism). The `works_vats`
  is **the Cistern** (the dig hitting the river — *"the water runs on,
  downward, and does not echo back"*); `depths_threshing` is a literal grain
  **tithe** (*"An offering. Not a stockpile."*); and the last tallow leak —
  the basement lodge-candle callback (*"wax on your thumb… tasting it"*) — is
  re-cut to candle **devotion** (*"the same guttering candles as the dark
  below… the Lodge has been part of it the whole time"*). A flow.py guard
  (§19) locks the fiction out of the scene source.
- ~~**Scrub time-loop language (code ↔ NARRATIVE §2).**~~ **DONE.** The fold is
  **spatial, not temporal**. Old Pell reads as **stasis** (*"where would I be
  counting toward?"*); the road carries the **fold** (Royce: *"the corn just
  hands you back where you started"*). No line says the days repeat / fold
  back on themselves. Locked by the flow.py §19 guard.
- ~~**Cut Toby's "dad" line.**~~ **DONE.** *"My dad went down too. He
  still comes home for dinner."* is gone (it leaked that claiming is
  *perceptible* + happens by *individual descent*, both forbidden by NARRATIVE §2). His
  unnameable-wrongness lines stay (*"I keep biting my tongue. To check."*).
  Locked by the flow.py §19 guard.
- **Seed the door's dream (DONE).** The origin (NARRATIVE §2) is now diegetic: reading
  Mara's journal through a third time triggers a wordless **door-dream
  cutscene** (`_tick_flashback` in `systems/narrative_mixin.py`,
  `_draw_flashback` in `ui/cutscenes.py`), and
  living it writes a half-dismissed memory to the **case notebook**
  (`_log_dream_entry`, stored in save arg `notes`, NOT `evidence`). Canon:
  the PI dreamed the door **once, a year ago, never reached it** — the note
  must read that way (a flow.py canon-guard enforces "a year" + no recurrence
  language).
- ~~**Reskin `effigy_grove` as a maker-less dread tableau.**~~ **DONE.**
  Individual cursing is redundant now the closing rite claims the whole town
  at once (NARRATIVE §2), so there is no maker. `effigy_grove` is a maker-less dread
  tableau — a crop circle in the corn north of Brimley, above the river (the
  corn itself is the border): the dead fire, the effigy ring, three weathered
  standing stones with the nailed-up faces fixed to one, all tended by no one
  you'll ever see — the work, no worker. Locked in `tests/flow.py`. *(Its
  one-time siblings `husk_grove` / `scarecrow_ring` were cut with the walk-in
  discovery folds, 2026-07.)*
- ~~**Rehome the Watchers as His gaze (§1).**~~ **DONE (2026-07).** The
  mechanic is unchanged (they raise visibility; dispel by breaking the
  gaze / axe / round) and both halves are re-pointed: the trigger is His
  own gaze (`_tick_gaze_bind`), and the bind/escalate/clear notices in
  `_apply_curse`/`_dispel_watcher` read as **His eye reaching into the
  plane** ("An eye has opened on you"), never a side-cult's spell.
  Internal names (`_cursed`, `_apply_curse`) stay as code plumbing.
- ~~**Gun = false-power threshold (§1).**~~ **DONE + flow-guarded.** The
  mechanic matches canon and `tests/flow.py` locks all four facts:
  **< 3 evidence kills cultists**, **3+ only staggers**, the **King and
  the Watchers are bullet-phantom** (unshootable — you can't fire down a
  direction you can't point at), and a **clean round always kills a
  local** (the gate only ever protected the cult).
- ~~**Scrap corpse persistence (§1, §2).**~~ **SUPERSEDED (2026-07
  ruling: dead locals stay dead).** The scrap removed the old replay
  and the accumulating corpse `mold` stage; the ruling reinstated
  persistence in its simplest form — a `dead_locals` save-arg ledger +
  `_apply_dead_locals` on scene load lays each killed local's body back
  down where it fell. No mold stage returns (corpses draw at 0, a clean
  fresh kill); the visibility spike and the cult body-investigate ping
  are unchanged; cultist bodies still last only the visit. Guarded by
  flow §32.
- **Mara's journal → the door (DONE).** Reading `mom_notebook` to the end
  drops the **door-dream cutscene** (the lure that took her) — the game's
  clearest, wordless look at NARRATIVE §2: a dried-wood doorframe in black, a pulsing
  gold glow pooled at the door's base, eyes peeking, and an **accelerating
  swarm of His dark-wood masks** whose gold gazes all converge on the player,
  over a wind/falling audio bed (`falling_air`). Mara is *answered, not
  deceived*.
- **Surface "He knows you" where it can land (DONE — NOT the lethal King).**
  The PI's single year-ago dream sits in the **case notebook** (`the_dream`
  note). When he first reaches the **real Threshold** (`scenes/depths.py
  build_threshold`), having dreamed it (`flashback_seen`), one quiet line
  lands before the doorframe beat: *"You have stood here before. In sleep."*
  (canon-accurate: he did stand at the door, once, in the dream).
- ~~**Name the principal locals.**~~ **DONE.** Locals in a small town know
  each other by name; the wax-museum quality is partly the old role-tags.
  Now named, surfaced as the dialogue speaker: the Sheriff is **Hollis
  Vane**, the Preacher **Rev. Asa Crane**, the Store-Owner/quiet-resister
  is **Hettie** (one person, not two — merged with the chorus Hettie), the
  Kid **Toby**, and the Lodge Clerk **Mr. Sable** (a local — the most
  attuned of them; the genteel name is the funereal-hospitality tell). The rest of the Brimley
  chorus was already named: Old Pell, Mrs. Calder, Royce, Garrick. Locked in
  `tests/flow.py`.
- **The liminal-composition pass** (§6): per-scene level design —
  composed emptiness, long sightlines, uncanny repetition.
- ~~Individual-curser in dialog / evidence beats.~~ **Superseded:** the
  closing rite makes an individual curser redundant (see the build-order
  above).
- ~~**Reconcile the calendar (April 14).**~~ **DONE.** The seal is locked
  to **mid-January 1994** and the full chain lives in NARRATIVE §1 setting note 3
  (door wakes ~April '93 → attuned from summer '93 → Mara north in the
  fall → rite mid-January → the PI in on April 15, 1994). Swept: Hettie's
  till is empty "since the new year" (both lines), the case note reads
  "Drove north in the fall. Stopped calling home by the new year," Mara's
  cell journal says the rest "had been here since the summer," the
  threshing tithe dropped its "season on season," and every wall calendar
  in town now defaults to a stopped **JAN 15** card. Flow-guarded
  (`tests/flow.py` §23a). See NARRATIVE §1 setting note 3 (the timeline).
- **Food scarcity — the VISUAL pass (mostly done).** The dialogue side is
  done (Hettie: "The shelves don't empty anymore... No deliveries.";
  "Shelves are bare. Till's been empty since the new year"), and the world
  art largely landed: the shop's `bare_shelf` runs (dust-ghosts where the
  stock stood, one tin left), Hettie's storeroom preserves, garden patches
  on some Brimley lots and not others. Still open: the domestic-horror beat
  of a cultist eating an ordinary meal at a counter (NARRATIVE §4). Wallpaper, not a
  mechanic.

---

## 5. The Basement Level — "The Works" (built)

The cult's **year-long excavation**, reached *only* through the effigy
grove's descent fold, which lands at the Shaft Floor of the cult's own
mine (scene key `well_bottom` — a legacy name; the town well itself is
dread set-dressing and goes nowhere, NARRATIVE §7). The attuned didn't build a
temple — they **dug**, following
the water down toward the door the dream promised (NARRATIVE §2). The seven rooms
are the **dig** at successive depths; partway down it broke into the
underground river (Room 3), the diggers' proof they were close. A
seven-room stealth gauntlet, descending. Built in `scenes/well.py`; all
rooms are `DARK_SCENES` (flashlight works, but the cultists' gaze still
finds you — run it on cover, timing, and breaking their line of sight).

| # | Room | Key | Contents |
|---|---|---|---|
| 1 | The Shaft Floor | `well_bottom` | The descent fold lands you here; its return pane (the way back up) stands where the rope once hung. Quiet airlock, 1 hide. |
| 2 | The Timber Racks | `well_passage` | The dig's staged shoring lumber, racked on its way to the faces (renamed 2026-07: the old drying-corn-doll-material fiction was cut -- an obsessive dig runs no craft room). A LONG rack gallery (24 tiles, lengthened 2026-07 -- the stealth pass: graded suspicion needs distance), 2 patrolling cultists offset down the run, 2 hides. |
| 3 | **The Cistern** (was "Tallow Vats" — cut) | `works_vats` | Where the dig **broke into the underground river** — the artery to the door (NARRATIVE §2), and the diggers' proof they were close. Wet stone, rising damp, 2 tending cultists, 2 hides. *No rendering, no tallow, no bodies — the claiming cult eats no one. Fiction redress is a code TODO (§4); the scene key stays `works_vats`.* |
| 4 | The Sorting Hall | `works_sorting` | The **worldly lives the congregation shed** when they were claimed — and the effects of the few the fold took — sorted and catalogued. 2 cultists, 3 hides (hardest crossing). A side door north → **Mara's room**. |
| 4a | **Mara's Room** | `maras_room` | A convert's cell off the hall: cot, her cult robe + the unsent letter. **Evidence #1.** A quiet beat off the gauntlet, 1 hide. |
| 5 | The Scriptorium | `works_scriptorium` | The Sign copied endlessly — the **attuned compulsively bleeding the dream-image out** onto every surface, none of them the door itself (NARRATIVE §2). 1 oblivious scribe, 2 hides. **The Calling** — the first of three cult-testimony fragments (NARRATIVE §9), the one bound, whole volume among the loose copies: the congregation's own personal testimony (their voice in the item description, the PI's reaction in his notes). Pure lore; it gates nothing (the keystone is the Mask alone). The Bargain + The Digging are found deeper (the Sump, the Old Stores). |
| 6 | The Sign Chamber | `works_sign` | The Sign daubed on the wall + an altar; the kneeling rank (set-piece NPCs) + 1 patrol. **The calling-out (2026-07):** Mara kneels among them; first entry, the kneelers rise, one says her name, she comes to you — the confrontation lands **evidence #6**. **Lift the Pallid Mask → `pallid_mask` + evidence #5** (no charcoal — you take the object itself). |
| 7 | **The Deepest Face** | `works_deepstair` | The dig's END — the cult's testimony left "a few feet of earth"; there is no stair, no gate. With the **Mask in hand** (the sweep finished) and **powder from the Sump**, a two-press charge **blasts the floor through into the old workings**: the FALL into `depths_antechamber` is the one-way step. The Mask is **not consumed** — carried down and spent at the Threshold door. |

**Rules wired:**
- **One way down:** the grove rite's opened pane only; the barn cellar hatch
  stays sealed (`scenes/interiors.py`). The shaft-floor return pane is
  **keyed to the Mask** (never one-way); crossing it up seals the
  descent (`descent_sealed`, the SPREAD lock).
- **Point of no return:** the FALL through the blasted face (Room 7;
  sets the `depths_breached` flag) — the Works stay walkable both ways for the
  Mask-bearer; the Depths do not give you back. **Seal vs. Spread is
  experiential, not a menu:** both live anytime you hold the Mask
  underground; the fork is where you carry His face (up through the
  keyed pane = SPREAD lock; down to the door = SEAL).
- **Gate (§3/§14/§15, DONE):** the blast requires the **Mask in hand**
  (the investigator finishes the sweep before he blows the scene) and
  **does not consume it**. You carry the Mask down and spend it at the
  Threshold door (SEAL). The cult's notes are decoupled (pure lore, NARRATIVE §9).
- **The underground is a MINE (locked 2026-07 — the fiction retrofit).**
  Every room below reads as the dig, or as the **old workings** beneath it
  that the blast breaks into: timber, stores, water, spoil, worn stone.
  **No charnel fiction anywhere** — the claiming cult spills no one (NARRATIVE §2),
  so there are no bone rooms, no captivity, no blood in the mine.
  `the_cells` are the diggers' own **bunk cells** (Mara's cell is the same
  kind, kept); `the_ossuary` (legacy key) is the old workings' **Old
  Stores** — racked gear, tagged hafts, The Digging left on a shelf.
  Guarded by `tests/flow.py` §19b (token scan of `well.py`/`depths.py` +
  the purged `bone_rack` furniture kind). The ART half of the mine read
  (timbered side-chambers, spoil heaps, cart ruts) is TODO #14.
  **The corridors walk LONG (2026-07, the stealth pass):** the graded
  suspicion model (distance falloff) only reads when "far" exists, so the
  three corridor rooms were stretched -- the Timber Racks gallery (24
  tiles, 2 patrols, 2 hides), the Depths' **procession drift** (30 tiles,
  the main hallway: 3 patrols in spread phase, 3 bay hides down the run),
  and the Kneeling Hall's nave (20 tiles, pews + a hide in each half).
  Rule of thumb when touching these: every long room keeps a rooted
  enclosed hide in each half, and patrol phases are spread so no half is
  permanently clear.
- The well sprite was redesigned and repositioned in `brimley` (the
  east village square — a landmark just off the road).

**Re-audit (2026-06):** the 7-room gauntlet above matches the build
exactly. Not tabled here but registered and reachable: three **dead-end
side branches** off the Works — `the_sump` (off `works_vats`, an ammo
cache), `the_cells` (off `works_sorting`; the diggers' bunk cells since
the 2026-07 mine retrofit), and `maras_room` (4a, the cell
off the Sorting Hall) — plus the **Depths**, which has grown to five rooms
(`depths_antechamber` → `depths_procession` → `depths_hall` →
`depths_threshing` → `depths_stair`, with `the_ossuary` — the **Old
Stores** since the retrofit — branching off the
procession) before the **Hive** (`dark`, the claimed congregation, past
names — Mara and evidence #6 moved up to the Sign Chamber, 2026-07) and
the **Threshold** (`threshold`, the doorframe). The
descent order is: grove rite → Works (7) → the blast → Depths (5) →
Hive → Threshold.

**Note:** the old cult chamber (`symbol_portal_room`) has been **removed
entirely** — its only entrance was the `abandoned_farmhouse` hatch, which is now
a nailed-shut dead end (a deliberate in-fiction seal: the grove's descent
fold is the sole way down). Saves are in-memory only, so there were no persistent
saves to keep it registered for. The `diner_gas_station` spur off the
cornfield was likewise removed (the car lives in the lodge yard); the
cornfield's east end is now a closed tree wall.

---

## 6. Art direction — the Darkwood look

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

## 7. The Fold, made mechanical

The bible's central image -- *the roads loop, the corn never ends, you
walk through the woods only to be spit out where you walked in* -- now
has mechanical existence beyond the dread aperture. The outside world
is built as a torus, with the rite's standing folds and the silent
same-scene relocations layered on top.

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

`brimley`, `cornfield_maze`, `cornfield_path`, and the Lodge yard
(`lodge_yard`) all wrap on the relevant axes:

- **brimley.wrap_x** -- the cross-town road at row 24 loops
  east-west. Walking off either side carries you back in on the
  other.
- **brimley.wrap_y** -- the perimeter forest loops north-south.
- **cornfield_maze.wrap_x = wrap_y = True** -- corn never ends in
  any direction. The exit tiles (^ to brimley, ! to cornfield_path)
  are the only escape, and finding them is the whole point.
- **cornfield_path.wrap_x = wrap_y = True** -- the woods spit you out
  where you walked in.
- **lodge_yard.wrap_x** -- walking east past the Lodge wraps you
  back to the west. There is no past-the-Lodge highway.

### Cross-scene macro-loop

Three direct south-chain exits close the outdoor world into one
closed system:

- **brimley** south edge ('M' tile, col 48 row 99) → cornfield_maze
- **cornfield_maze** south ('!' tile) → cornfield_path
- **cornfield_path** south ('S' tile) → brimley north

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

### The standing folds (the rift panes)

**The walk-in discovery folds are CUT (2026-07, decided).** The maze's
direction-gated secret-area folds — the effigy grove's corn back door,
and the `husk_grove` / `scarecrow_ring` clearings that only those folds
reached (both scenes removed with them, on the `symbol_portal_room`
precedent, §5 note) — are gone. The congregation **walked to the grove
openly before the closing rite**; the rite is what hid it, so no tile in
the corn can reach it anymore. `effigy_grove` survives as the rite-hidden
clearing at the mouth of the cult's mine, **north of Brimley above the
river**, reached ONLY through the school rite's pane (NARRATIVE §7).

**The standing-pane canon (2026-06) holds for every fold that shows
itself** — the school↔grove pane, the grove's descent fold, the shaft
floor's keyed return, and the King's portal. Faced head-on, a fold SHOWS
itself: a standing black-gold rift frame anchored on its world seam, one
visual family with the King's portal (`rendering/portal.py
draw_rift_door`). Step to the side and the pane thins and dims toward
nothing; from behind it isn't there at all (a 4D pane has no back) -- so
from any other angle the tile reads as floor. The crossing itself stays
NOTHING -- no fade, no sting, no beat; the frame is the spectacle and
stepping through is just walking. The world's silent lies remain the
torus wrap and the in-maze relocations, which never show a frame.

**In-maze fold relocations.** Two additional tiles inside the
`cornfield_maze` (one at (8, 6) walked SOUTH, one at (16, 11) walked
NORTH) don't open a new scene -- they teleport the player to another
spot in the same maze, camera offset preserved so the swap is
invisible at the moment of crossing. The player notices when their
surroundings stop matching. Mechanically they are ordinary
direction-gated exits whose target is the maze itself
(`Game.cross_fold` handles the same-scene case with no load); they are
SILENT by canon -- a relocation never shows a frame, because here the
lie is the world itself.

**Visible perimeter side passages.** The maze's outer wall has four
clear dirt-lane gaps (west edge at rows 5 + 13, east edge at rows 8 +
16) that look like ways out. Walking through one wraps the player to
the opposite edge -- the maze visibly has many exits and all of them
loop.

The framework (`Scene.add_exit(direction=...)` + `find_exit_at(facing=)`)
is general -- the rite panes and the relocations ride it. (The hidden-
scene discovery folds that also rode it were cut, 2026-07.)

### One phenomenon, two presentations (the consolidation)

There are exactly two kinds of spatial transition in THRESHOLD:

- **Doors** (doors, ladders): ordinary plumbing. They
  fade, they make a sound, they feel like doorways. Architecture is
  the player-only escape.
- **The Fold**: everything else. One phenomenon with two faces:
  - **The fold you SEE** -- the standing rift frame: the rite's panes
    (the school door, the grove's descent fold, the shaft floor's keyed
    return -- at rest, quiet) and the King's portal (the same frame torn
    violently). One renderer, one black-gold grammar.
  - **The fold you DON'T** -- the silent lie: the torus wrap, the
    seamless world edges, the in-maze relocations. The horror here is
    futility, never spectacle; no frame is ever shown.

Every fold crossing goes through one primitive (`Game.cross_fold`):
no fade, music keeps playing, stride and look preserved, the player
holds their screen position while the world swaps around them. The
crossing is deliberately nothing; the frame is the monument.
One-way-ness is the King's signature alone: the town's geometry is
symmetric (every static fold has its return), the wrap is a loop, and
the single one-way crossing in the game is the juke through the tear
HE made (it shuts behind you). The Threshold doorframe stays plain --
the world's folds scream so that the real door's silence lands (NARRATIVE §2).

---

## 8. Desire, and how the fold strands it

> The reading that keeps the whole cast honest -- the character-design
> twin of the world rot (§2). Every future line for a Brimley local
> should be checkable against it, the way every cosmology line is
> checkable against the bearing rule (NARRATIVE §2: the door promises,
> never provides). It states the SHAPE of each person's wanting; the
> hard per-character FACTS that are locked (Mara's son, Sable's full
> house, Vane's ending) live in NARRATIVE §4.

**The King does not kill desire. He strands it.** That is the engine,
and it is crueler than taking anything. Every soul in Brimley still
wants exactly what they wanted before; the door severed the want from
its object and left the wanting switched on. Pell still wants his
harvest, and it is rotting in the field he can no longer look at.
Calder still wants a guest, and sets the plate for one who will never
come. Vane still wants it to end, and it only ever offers more. **Hell
here is a want with its object cut away and the appetite left running.**
The fold "admits but never releases" (NARRATIVE §1) -- and what it will
not release is the wanting.

> Internalize this or the cast reads as generic sad villagers:
> - **The machine runs on ordinary wants.** A full house, a harvest, a
>   guest at supper, a road home, to save someone, to keep the shop
>   open, for a child to be safe, for it all to end. Nothing cosmic --
>   the door deals in the wants EVERYONE has, because those are the ones
>   everyone has. "Someone wants something simple and doesn't get it,
>   and there is forever no way to get it back" is the design doc for
>   the entire town.
> - **To want is to be strandable; to not want is to be already dead.**
>   There is no safe dose. The PI is safe from the machine only because
>   he refuses to feel (his numbness is walled-off want, NARRATIVE §2),
>   and that refusal is its own death -- which is exactly why SPREAD is
>   the cruelest ending (it hands the numb man his wanting back, as the
>   damnation, §8/NARRATIVE §8).
> - **The absent thing is the internal want.** An "invincible summer" is
>   a want that lives inside you, that no external severing can reach --
>   and no one in Brimley has one. Every want in this town points at an
>   object the fold can cut. That absence IS the horror; do not
>   accidentally give a character a self-sufficient want, or you have
>   handed them an exit the game denies everyone.

**Two families, one mechanism at two scales.** The door takes an
individual's want and gives it a false BEARING (the leash); the closing
rite took a whole town's wants and FROZE them (the stasis). Same act --
separate a wanting creature from the thing it wants, permanently, leave
the wanting intact -- performed on one person by the dream and on the
collective by the seal.

- **The attuned (the cult) -- desire as a LEASH.** The door gave the
  ache a direction (down) and they follow it forever, never arriving.
  Motion without destination; obsession is what that looks like from
  outside. Their want is why they are His (attunement = the size of the
  hole, NARRATIVE §2).
- **The locals -- desire in STASIS.** Netted by the rite regardless of
  what they wanted, they are frozen mid-reach with every object severed.
  The appetite with nowhere to go; "stagnation" is what that looks like
  from outside. Their want is NOT why they are His (see the guardrail
  below) -- it is what the fold is doing to them now.

**The roster** (each want is simple; the second column is the strand):

| Who | The simple want | What the machine did to it | Family |
|---|---|---|---|
| **The PI** | (refused -- walled off) | nothing can bait what won't be felt; the armor is a death | control |
| **Mara** | her stillborn son | the dream aimed it DOWN; she digs toward a door he is not behind | leash |
| **The congregation** | each their own ache | the same bearing, the same dig; the self spent into the labor | leash |
| **Sable** | a full house | FED, for one season, then bereaved (the migration filled his rooms, the door gave nothing); the anomaly, NARRATIVE §4 | fed, then taken |
| **Vane** | for it all to end | the one appetite the door cannot answer; stasis so total it malfunctions into the hollow turn | stasis |
| **Crane** | to save them, to matter | a dying ministry handed a real devil; the rescue instinct walks him to the river. **He is the player's Sign-Chamber mistake, previewed** | stasis |
| **Hettie** | to provide, protect her kin | the supply line cut; she performs empty commerce over bare shelves, starved for word of the outside | stasis |
| **Pell** | his legacy, the harvest endures | the corn dead standing, uncut; "I don't look at the fields long anymore" | stasis |
| **Calder** | someone to come | the eternal plate; **she is the town's kitchen light** (Mara's letter: "somebody to wait up for") -- a guest who never crosses the table | stasis |
| **Royce** | out; to drive somewhere | the road hands him back; he pins his last hope on the one exception (the PI got IN), not knowing the exception is a mouth | stasis |
| **Garrick** | to watch, to warn, to matter | vigilance made futile; he sees everything, can stop nothing, warns toward roads that all loop | stasis |
| **Toby** | to be safe, to be told the truth | the child's baseline want, answered by the one adult who listens with a promise the endings guarantee is a lie | stasis |

The closest thing to an internal want anyone reaches is **the PI's
promise to Toby** -- warmth generated from inside, pointed outward,
expecting nothing back. The endings break even that (no reachable
future returns for the boy), which is the point: the one summer the
game lets a character find, it takes.

> **GUARDRAIL -- keep the two mechanisms distinct.** The cult was
> LURED (desire -> door, the leash); the locals were NETTED by the rite
> regardless of their wants (desire -> stranded, the stasis). Do NOT
> retrofit a local's want into a door-lure: their wants do not explain
> why they are His, only what the fold does to them now. Collapse the
> two and Brimley becomes a town of secret volunteers, which kills the
> "claimed without ever knowing" horror (NARRATIVE §2) and cheapens the
> whole cosmology. One impossible thing; the wanting is ordinary
> downstream of it.

