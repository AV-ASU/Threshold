# THRESHOLD — Design Notes

> How the systems deliver the fiction: the threat model, world rot,
> the implementation map, open design threads, the Works level design,
> art direction, and the fold mechanics. The FICTION itself (premise,
> door, timeline, cast, evidence, descent, endings, canon invariants)
> lives in `NARRATIVE.md`, the story bible; the exact player-facing TEXT
> (spoken lines + narrator boxes) lives in `DIALOGUE.md`; open work lives
> in `TODO.md`. These sections were relocated whole from the old
> NARRATIVE.md (2026-07 split); §-references here use this file's own
> numbering, and cross-references into the bible say `NARRATIVE §n`.

---

## 1. The Threat Model

A single meter: **VISIBILITY** `[0, 1]` — how visible you are to the King
right now. The **Watchers** (His gaze made manifest) are the main driver
below 3 evidence; cultist gaze adds on top. **Hiding** bleeds it back down
(passive corn-cover tiles, plus the few crawl-**under**-furniture
`hide_spots` via E). See the Watcher note in §4.

**The max-visibility overlay is TWO tiers keyed to WHO has you**
(`_draw_apex_overlay`, 2026-07 playtest fix: the wash was too intense
when only cultists were chasing). At `visibility >= 0.95`, if the King
is the threat (`_roam_king["armed"]`, or his body is in your room)
the **apex tier** paints His dried-blood red wash + a hard edge-crush
tunnel vignette; if only the cult has you (below the gate, no King
body) the milder **town tier** drops the red for a cold desaturated
tighten with a wider clear disc. The cult is human and does not get His
colour. Safe / dim-safe interiors break both.

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
walking. The **hollow Sheriff** (the `_force_chase` apex) is **exempt** — he
never loses sight of you and cover cannot break him. The roaming **King** is
not on that path: he honors `player.hidden` (stepping into corn OR an enclosed
hide drops his hunt to searching, guarded by `tests/king_roam.py`), though he
re-finds you rather than losing you for good, and his catch is birth-gated.

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
- **At 2 evidence (`KING_TURNS_HEAD_EV`):** the ramp's telegraph — he
  **turns his head** toward you (the `the_turning` note), aware but not yet
  moving, so the gate is not an ambush (play-notes).
- **At 3+ evidence:** the King himself **walks** — the roam arms and He
  hunts the world room by room (the design spine above; mechanics in
  `systems/king_roam_mixin.py`). But crossing the gate is not an ambush: the
  world **holds its breath** for `KING_ARM_GRACE` (~25s) first — he stands
  far and does not close (`arm_grace`, the `the_breath` note), the window to
  reach the lodge for the Invitation before the hunt begins (play-notes ramp;
  decouples the difficulty spike from progression). *You make Brimley deadly
  by understanding it.*

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
cellar and the Sheriff's office), so crossing that line strips
your agency on the exact line that arms the King:

- **Below 3 evidence:** a clean shot **kills** a cultist (they fall and
  later respawn), and cultists stay **mundane** — no bloom. You have agency.
- **At 3+ evidence:** the shot only **staggers** them (a brief stun), and a
  cultist that locks on **blooms into His maw** (the vessel transform). *The
  deeper you see, the less the world lets you kill.*

The gun never makes you safe: the cult still takes you — but the grab is
**two-touch** now (play-notes): the first grab of an encounter shoves you
free (`_cult_shrug_off`), and only a **second** grab before you reach a safe
zone is the CAPTURED fail state (a swarm or a corner still ends it). **The
King cannot be shot at all** — you can't fire down a direction you can't
point at (NARRATIVE §2).
A shot is **loud** — His gaze hears it. The flashlight, the splitting axe
(chop + stun), and hide-spots remain; the pistol sits alongside them, not
over them.

**The cruelest truth of the gun: it only ever works on the victims.** A
clean round drops any **local** instantly — Hettie, the Sheriff,
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
> evidence-pickup autosave (`Game._autosave`, play-notes) persists it like
> any other arg. Guarded: flow §27/§32.

---

## 2. World rot — the town curdling as you understand it

> **Reconciles with NARRATIVE §2.** The town was *already* wholly claimed,
> invisibly, before you arrived — nobody here is mid-conversion. The
> world rot is **not the townsfolk changing**; it is the **veil thinning
> for the PI** as he learns too much and He turns His eye back on the face
> from the dream. What the PI reads as the town "going wrong" is the truth
> **surfacing to him**, not allegiances being switched. Underneath, they
> were always His.

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
- **The people do NOT change — the man hearing them does (TODO #22c,
  2026-07).** The town stays ordinary end to end: every local keeps their
  exact sprite, portrait, body, AND words (the town reads NORMAL; the
  wrongness is the *place*, not the people, NARRATIVE §2/§6). What rises
  with the stage is the **PI's own reading** of them — a four-tier
  interior register (`_pi_tier` / `_pi_framing` / `_PI_WEATHER` in
  `scenes/dialogue.py`, keyed to evidence 0 / 1-2 / 3 / 4+) that colours
  each principal's opening framing while the NPC's line is untouched. The
  dread is the mundane line delivered warmly by someone the PI can no
  longer hear as safe — one impossible thing, and it is the door. (The old
  people-change layer — peace-makers *convert*, resisters *turn* — was CUT
  with this rework; DESIGN.md §9, NARRATIVE §6.)
- **Sheriff Vane falls last, and hardest — and his fall is
  player-driven (TODO #2a, built 2026-07).** The last holdout, and the
  one soul in town **claimed but unattuned** (he never dreamed the door;
  NARRATIVE §4). The world rot never turns him on its own; a hidden
  **despair/hope ledger** decides his fate (`vane_despair`, the `VANE_*`
  config block; surfaced only as his **mood** — the conversation's
  framing line, the beats, and (2026-07) his **pose in the office
  tableau** (`_vane_tableau_state` mirrors `_vane_prompt`'s thresholds:
  despair turns him to the window, hope leans him in) — never a number). **Hope has one
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
- **Cultist spawn geography** (`systems/threat_mixin.py` `_ensure_cultists` /
  `_spawn_cultist`): a cult scene is kept topped to `Scene.cult_target`
  roamers (default `CULT_REGULARS`), spawned at the farthest unoccupied point
  in `Scene.cult_spawns` (a hand-placed anchor pool, `from_pool=True`) or the
  map corners if none is defined. The scene is PREFILLED to target on the
  first awake tick after each load (`_cult_prefilled`) so it reads populated
  on entry, then refills one at a time on the `CULT_TOPUP_INTERVAL` breather.
  All of it stays behind the `CULT_WAKE_EV` gate. **Brimley** uses
  `cult_target = 10` over 14 anchors (9 spread + a 5-strong SE **cult camp**
  crew, `_camp_pos`); the crew fills from the pool when the cult wakes. At ev 0
  the camp spot is just a stand of corn (only its trees are pre-cleared so the
  anchors + tend station stay reachable). The camp itself is raised in
  `_raise_cult_camp` (`scenes/brimley.py` on_enter) only at 1+ evidence
  (nothing at ev 0 -- the town reads normal): the **worn packed ground** is
  beaten in (corn -> dirt) and a lit `camp_fire` (a new SOLID light volume,
  distinct from the dead indoor `campfire` scorch decal) is ringed by
  `bedroll` + `log_seat` floor decals and a hung lantern, with a tend-the-fire
  errand station just south of the flames. The ground is the cult's OWN doing,
  so it appears with them, not before.
- **Evidence count:** `len(self.save.arg("evidence", []))`.
- **Evidence logging:** `_evidence(game, name, content)` in
  `scenes/dialogue.py` → appends to `save.arg("evidence")`, shown on the
  Casebook's Case tab (`ui/journal_ui.py`).
- **Threat geography constants** (`systems/config.py`, star-imported by
  `game.py`): `CULTIST_SCENES`, `SAFE_SCENES`, `OUTDOOR_SCENES`,
  `DARK_SCENES`, `KING_FREE_SCENES`.
- **Evidence is a log, not inventory.** "Evidence" = entries appended to
  `save.arg("evidence")` by `_evidence(game, name, ...)` (shown on the
  Casebook's Case tab). The count for the 3-gate is `len(save.arg("evidence"))` —
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
  `_force_chase` apex stays straight and **never loses sight** (relentless). A
  chase carries **only across a direction-gated rift FOLD** now
  (`_note_fold_pursuit`/`_tick_fold_pursuit` — surface NPC chasers AND
  underground Enemy cultists, the latter spawned native to the destination); an
  **ordinary crossing shakes it** — a door, ladder, rope, a seamless outdoor
  passage, a road loop, or any non-fold target — so a chaser follows within a
  scene and across a fold but **never across an ordinary scene boundary**
  (play-notes narrowing, 2026-07). **SAFE_SCENES** stay the refuge a fold can't
  breach. The Watcher-curse gaze still seeds on any fold OR passage
  (`_exit_is_fold`) — that is His attention reaching across the wrongness, not
  a cultist on foot. Guards: flow.py §20 (no preset routes + nav routes around
  cover) and §21 (only a rift fold carries the chase; the refuge is never
  breached), plus tests/fold_pursuit.py.
- ~~**Scrub the eat-cult fiction (code ↔ NARRATIVE §2).**~~ **DONE.** Canon is a
  **claiming** cult that renders no bodies (no cannibalism). The `works_cistern`
  is **the Cistern** (the dig hitting the river — *"the water runs on,
  downward, and does not echo back"*); `depths_threshing` is a literal grain
  **tithe** (*"The town's whole harvest, carried down and never carried
  back up."*); and the last tallow leak — the basement lodge-candle
  callback (*"wax on your thumb… tasting it"*) — is re-cut to candle
  **devotion** (*"the same guttering candles as the dark below, kept
  burning up here too"* — its old "part of it the whole time" tail was
  later cut in the #13b editorializing trim). A flow.py guard
  (§19) locks the fiction out of the scene source.
- ~~**Scrub time-loop language (code ↔ NARRATIVE §2).**~~ **DONE.** The fold is
  **spatial, not temporal**. Old Pell reads as **stasis** (*"I've got the
  calendar where I want it. Stopped."*); the road carries the **fold**
  (Royce: *"The corn handed me back every time."*). No line says the days
  repeat / fold back on themselves. Locked by the flow.py §19 guard.
- ~~**Cut Toby's "dad" line.**~~ **DONE.** *"My dad went down too. He
  still comes home for dinner."* is gone (it leaked that claiming is
  *perceptible* + happens by *individual descent*, both forbidden by NARRATIVE §2). His
  unnameable-wrongness register survives in his convo (*"I tried to lie
  yesterday. My mouth wouldn't."*); the old tongue line lives on only as
  his tableau's held-shut mouth (an art direction note, no longer spoken).
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
- ~~**Rehome the Watchers as His gaze (§1).**~~ **DONE (2026-07), then made
  THE below-3 threat (play-notes rework).** The Watchers are His gaze made
  manifest and the primary visibility driver below the King-gate. From
  `WATCHER_WAKE_EV` (1) evidence, while the player is EXPOSED (open, not in
  cover / a safe room), the domain OPENS Watchers on a timer
  (`_tick_watchers`): `WATCHER_GRACE` (6s) before the first of a wave and
  after clearing one, then the evidence-scaled `_watcher_spawn_interval`
  between the rest (the King floods them deep). Each live Watcher HOLDS the
  exposed player and drives visibility UP by `WATCHER_GAZE`/s (the active
  climb, `_watcher_gaze`) plus a small residual `WATCHER_FLOOR`, so ignoring
  them SNOWBALLS toward the King line; the field caps at `WATCHER_MAX`. Clear
  them (gaze `WATCHER_GAZE_DISPEL` s / axe / round, `_dispel_watcher`); cover
  pauses the timer and drops the hold. The old high-visibility
  `_tick_gaze_bind` / `GAZE_BIND_*` trigger is retired. A Watcher opening
  carries **no narrator box at all** (play-notes cut): the void-sting and
  the eye itself are the tell — any future text must read as **His eye
  reaching into the plane**, never a side-cult's spell. Internal names
  (`_cursed`, `_apply_curse`) stay plumbing.
  **The gaze only OPENS under the open sky or in the deep (2026-07 ruling,
  `WATCHER_OPEN_SCENES`): no Watcher ever manifests inside a surface
  building.** Step through any interior door and the wave clears; step back
  out and the grace runs before it re-forms. A fold into a surface interior
  binds nothing (`_roll_fold_watcher` exempts non-open destinations).
  Guarded by `tests/stealth.py` §11.
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
  "Drove north in the fall, quit calling home by the new year," Mara's
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
| 3 | **The Cistern** (was "Tallow Vats" — cut) | `works_cistern` | Where the dig **broke into the underground river** — the artery to the door (NARRATIVE §2), and the diggers' proof they were close. Wet stone, rising damp, 2 tending cultists, 2 hides. *No rendering, no tallow, no bodies — the claiming cult eats no one. The scene key is now `works_cistern` (renamed 2026-07 to match the Cistern).* |
| 4 | The Sorting Hall | `works_sorting` | The **worldly lives the congregation shed** when they were claimed — and the effects of the few the fold took — sorted and catalogued. 2 cultists, 3 hides (hardest crossing). A side door north → **Mara's room**. |
| 4a | **Mara's Room** | `maras_room` | A convert's cell off the hall: cot, her cult robe + the unsent letter. **Evidence: the unsent letter (`maras_room`, a canonical trail beat — NARRATIVE §6).** A quiet beat off the gauntlet, 1 hide. |
| 5 | The Scriptorium | `works_scriptorium` | The Sign copied endlessly — the **attuned compulsively bleeding the dream-image out** onto every surface, none of them the door itself (NARRATIVE §2). 1 oblivious scribe, 2 hides. **The Calling** — the first of three cult-testimony fragments (NARRATIVE §9), the one bound, whole volume among the loose copies: the congregation's own personal testimony (their voice in the item description, the PI's reaction in his notes). Pure lore; it gates nothing (the keystone is the Mask alone). The Bargain + The Digging are found deeper (the Sump, the Old Stores). |
| 6 | The Sign Chamber | `works_sign` | The Sign daubed on the wall + an altar; the kneeling rank (set-piece NPCs) + 1 patrol. **The calling-out (2026-07):** Mara kneels among them; first entry, the kneelers rise, one says her name, she comes to you — the confrontation lands (Mara is **proof, not a counted beat** since the TODO #22 rework: the calling-out fires but no longer counts). The talk itself is the last **close-up tableau** (`_open_mara_tableau`, TODO #2b): she opens masked and hooded, listed as one of the congregation, until the greet unmasks her — the reveal. **Lift the Pallid Mask → `pallid_mask`** — the **keystone item**, not a case beat (it left the count; NARRATIVE §6). No charcoal; you take the object itself. |
| 7 | **The Deepest Face** | `works_deepface` | The dig's END — the cult's testimony left "a few feet of earth"; there is no stair, no gate. With the **Mask in hand** (the sweep finished) and **powder from the Sump**, a two-press charge **blasts the floor through into the old workings**: the FALL into `depths_antechamber` is the one-way step. The Mask is **not consumed** — carried down and spent at the Threshold door. |

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
  kind, kept); `the_old_stores` is the old workings' **Old
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
  eastern lodge/well square just inside the lodge-road entry — a
  landmark just off the road; `scene._well_pos`, col 52 row 17 since the
  60x60 redesign, TODO #18).

**Re-audit (2026-06):** the 7-room gauntlet above matches the build
exactly. Not tabled here but registered and reachable: three **dead-end
side branches** off the Works — `the_sump` (off `works_cistern`, an ammo
cache), `the_cells` (off `works_sorting`; the diggers' bunk cells since
the 2026-07 mine retrofit), and `maras_room` (4a, the cell
off the Sorting Hall) — plus the **Depths**, which has grown to five rooms
(`depths_antechamber` → `depths_procession` → `depths_hall` →
`depths_threshing` → `depths_stair`, with `the_old_stores` — the **Old
Stores** since the retrofit — branching off the
procession) before the **Hive** (`dark`, the claimed congregation, past
names — Mara (the calling-out) moved up to the Sign Chamber, 2026-07) and
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
  shadows** under props, **wall-cast shadows** + lit wall faces, and
  **light pools** with falloff from every emitter. Light is the only relief
  in the dark.
  - **Two light families, cold vs warm (2026-07 lighting pass).** The
    town's **civic** light is period-correct **electric**: rural
    dusk-to-dawn **yard lights** on poles (`yard_light`, mercury-vapor
    **cold** blue-white) threading the roads, run off **gas generators**
    (`generator`) tucked outside each building. Provenance: the fold cut
    Brimley off the grid with everything else (NARRATIVE §1), so the town
    keeps its lights on off gasoline; a genset MUST sit outdoors (exhaust),
    so it fronts the doors. Against that cold institutional glow, all
    **fire** stays **warm** and is the thing the town *huddles* at (burn
    barrels, cult braziers, the intimate candles at Calder's table). The
    cold-electric-vs-warm-fire split is the deliberate read; the civic
    lanterns Brimley used to run on (a 19th-century lamppost) were the wrong
    century and are gone (the bridge keeps one hung lantern as a personal
    accent). Both prop kinds are anchored `SOLID_PROPS` volumes (never
    swiveling cards), verified in the 3D tilt.
  - **The shared light logic (the "carry it underground" foundation).**
    `_draw_dark` (`systems/render_mixin.py`) no longer special-cases
    `wall_torch`: it iterates **`FIXTURE_POOLS`** (the visible-pool twin of
    `Scene._LIGHT_KINDS`) across **every** light-emitting decoration in the
    room, so any real fixture -- a cult brazier, a Sign-Chamber candle, a
    town yard light, a genset work-bulb -- punches its own colored,
    navigable pool into the gloom. One table drives the surface (if it ever
    darkens) and the deep, with no per-scene special-casing (`wall_torch`
    keeps its exact legacy numbers, so torch-only rooms stay byte-identical).
    The **deep still swallows the flashlight** (`CULT_DARK_SCENES`, DESIGN §1's
    deliberate dread is preserved): the cult sites are lit by the cult's OWN
    ritual fires now, not by your beam. Fully retiring the "special darkness"
    beam-off is a separate dread decision (`TODO.md`), not folded in here.
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
come out wrong-side of where they went in."* Locals don't theorise
about the fold; they just know don't go off the path.

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

- **brimley.wrap_x** -- the cross-town fold road at row 25 loops
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

- **brimley** south edge ('M' tile, col 20 row 59) → cornfield_maze
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

### The rift pane -- 4D construction and look

> Folded in from the retired `PORTALS.md` (2026-07). Its "decisions
> landed" material was already this section's "one phenomenon, two
> presentations"; these are the parts unique to it.

A portal is the edge of a 4D "pane" poking up into Brimley. Face it
**head-on** and you see through it (the peek) and can step through; step to
the **side** and a pane seen edge-on is a thin line, nearly invisible;
there is **no back** (its other faces point in the 4th direction, a way you
can't walk), so from any angle but head-on it isn't there. We are not
adding a rule -- we are drawing the rule already written (the pane reads as
floor from any other angle).

We run **no 4D world simulation**. We reuse the King's existing 4D math
(`rendering/king_unfold.py`: `_rot` spins through the W axis, `_to3d`
flattens back) in three spots only: the **border** (the lit grazing edge,
the King's dim gold rim-light), the **peek** (the destination spun in
through 4D -- impossible depth that naturally fades to nothing as the pane
turns edge-on), and the **crossing** (stepping in *turns* the pane: this
scene rotates out through W, the next rotates in -- a quick turn, not a
fade, the brief "floating pieces" moment). Everything else -- walking,
walls, tilt camera -- is unchanged.

**Visual spec:** a tall thin **standing** slit that depth-sorts with
trees/corn (never a floor mark, which would read as a stain), with a **dark
core / mouth** so the rim has contrast at small size under the tilt, a
**dim, desaturated gold** rim (cursed gold, not treasure gold), and thin
**jagged electric arcs** that flick along the edge and die in a few frames
(the living wound). The peek shows the **real destination** -- a
recognizable place, live actors resolving out of the fog at the seam,
fogging out toward the slit edges. **Hold the line:** black + dim-gold
keeps it eldritch and out of Tron-blue; no bright/cyan "electric."

### State-driven folds

A scene may gate an exit on game state (`Scene.exit_gate_fn(game, char)`)
and drive a fold's formation charge per frame (`Scene.fold_charge_fn(game,
char)` → 0..1 into `draw_rift_door`'s charge ramp; 0 = not drawn, reads as
floor). Direction-gated exits also route straight through `cross_fold`
regardless of set membership, so a fold can join ANY two scenes --
including surface↔underground. Shipped uses: the **effigy grove's descent
fold** (clarity = evidence/3, opens at 3, lands at `well_bottom`, dies at
`descent_sealed`), its **shaft-floor keyed return** (answers only the Mask
after the grove rite), and the **school door** (opened by the chalk-door
rite, then permanent). Folds stay two-way until they DIE or are **KEYED** --
never one-way (the King keeps his signature). Live proof sheet:
`tools/preview_rift_anchored.py`.

### See-through doors and the blind spot (2026-07)

The mundane **see-through door** (`portal.draw_through_aperture`, opted in
per scene via `Scene.seethrough_doors`) shows the ACTUAL room beyond
through the opening. Its terrain is a cached CCTV-style buffer, but the far
room's **actors are a per-frame pass** (`portal._draw_aperture_actors`)
gated by the player's own sight cone: a far actor is mapped to its apparent
host-world position (both cameras share pitch/yaw/scale) and culled by
`scene._door_actor_sight` (the frame's sight fn, set in `draw_world`). So an
empty room reads through the door but a threat in a corner the player isn't
looking at stays hidden -- the same restricted-sight rule the open world
obeys, and the mundane door's point of difference from the RIFT, which
shows everything by design (the King's violence has no blind spot). The
figure is clipped to the opening. Preview: `tools/preview_door_sight.py`.

**Door opening direction is geometry-derived.** A door can be punched into any
wall face; `_door_room_dir` (`scenes/terrain.py`, used by BOTH the flat
`_draw_door_opening` and the tilt `_draw_doorway`) reads the door's wall
neighbours to resolve which way it opens. It counts windows (`i`) as part of the
wall line and treats a building's roof (`r`) as the INTERIOR side, so a door
flanked by lit windows on an east/west/north face still resolves correctly (not
just the old south default). This is what lets an overworld building FRONT the
street it sits on -- Brimley's houses face east/west/north onto the central
spine and their access road rather than all facing south (TODO #18 follow-up).

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

---

## 9. The Case (evidence as Mara's trail)

> The evidence rework, settled with the user 2026-07. This is the DESIGN
> of record; the hard canon (the set, the invariants) lives in
> NARRATIVE §6, and the code catch-up is TODO #22. It supersedes the
> "pool of six, any 3" model, which was never true in play.

**Three categories, and only one is evidence.**

- **Statement** — testimony. What a person *says*. Fallible by nature:
  they lie, misremember, or do not understand. Hettie's memory, Toby's
  account, Royce's roads, the cult's own testimony. These are **notes**,
  never evidence.
- **Evidence** — a tangible thing, tied to Mara, that proves itself.
  Four tests, all required: (1) **it is Mara's**; (2) **it is a pickup
  ITEM** — carried, not a walk-into-a-room examine, so it is never
  missable and never ambiguous; (3) **it is self-evident** — you could
  photograph that one moment and anyone would understand it, no
  cosmology and no witness required to read it; (4) **one per room** —
  the trail is walked, not vacuumed from a single jackpot.
- **Proof** — the found person. Mara herself. The case's
  **resolution**, never a log entry.

**Why the old six failed.** Run them through the rubric and four die:
the **Ledger** (she was never at the lodge — zero Mara relation), the
**Preacher** (not Mara; and "the cult is hostile" is already proven by
the sealed town and the grabbing cultists), the **Mask** (its meaning
needs the cosmology to read, and it is not Mara's — it is the keystone
ITEM), and the **Congregation** (Mara is proof, not evidence). Only the
journal and the cell/letter survive. And "any 3 of 6 is the point of no
return" was a **fiction**: the only pre-descent evidence is the surface
pieces and the descent needs 3, so the surface set was always
mandatory, while the underground three drove **no mechanic at all**
(every evidence gate is ≤ 3 — cult wakes at 1, King arms at 3, rot caps
at `min(3, evidence)`). Half the system was inert.

**Evidence is a biography, not a keypad.** The case reconstructs one
woman's descent, and the trail has a shape: **felt it** (the journal) →
**did it** (the dig) → **why** (the letter) → **the result** (Mara,
found). The surface stations are the **people she touched**; the
underground stations are the **things she did**.

**The surface trail — her interactions with the town (and it MUST
exist, or the game is a walking sim).** The threat is gated on evidence
(cult wakes at 1, King arms at 3), so evidence has to live on the
surface or Act 1 has no teeth. Mara barely existed visibly in town, so
her surface trail is the physical TRACE she left in people's lives,
findable in ANY order, each in its own place, each rising in
temperature though the player walks them in any order:

- **The receipt** (Hettie) — matches, canned milk. She *lived* here, a
  resident buying staples, not a visitor. The mundane.
- **The detention record** (Vane) — he had to book her. She was coming
  apart in public. The crack. (Garrick's "she cursed at the sky" is the
  **statement** that witnesses the same incident — testimony, not
  evidence.)
- **The journal** (the barn) — her own hand, the grief and the dream.
  The turn. Fires the door-dream cutscene.

The NPC is the **warm delivery** (show the photograph, they react and
hand it over); the paper is **world-persistent**, so it outlives them
(the Sable-drop precedent: the receipt is still on the shop spike, the
record still in the office files, if the local is dead) — **no
soft-lock, no looting a corpse required.** This makes Hettie, Vane, and
Toby the load-bearing locals, and deepens three who were already
central rather than inventing new ones.

**The secret fourth — the bear.** The private Mara, against the three
public records. The PI is numb everywhere but soft with children, and
that one trait is the **key**: you cannot interrogate the bear out of
Toby, you have to be the man he *wants* to give it to. He **lends** it —
"she gave me the only toy in town; if you find her, give it back?" — so
the PI carries a dead son's bear down toward the mother who gave it
away, for a reunion he already knows can't happen. The tag reads the
boy's name (**Sam**; NARRATIVE §4). On the surface it is a strange,
tender, *unexplained* thing in a boy's hands; underground the letter
names the son and **the bear detonates**. A plant in Act 1, a payoff in
Act 2. The least admissible piece and the most devastating — and
**optional**, so it can never gate progression.

**The underground trail — her descent.** The **dig item** (proof she
*laboured*, willing hands — a work-tally or the Sign in her own hand, in
a room that is not the cell), then the **cell / letter** (the son, why
she won't leave), then **Mara = proof** (the terminus; the trail ends
at the found person, alive and unrecoverable).

**The four jobs on one axis (evidence is the crux).** How far up Mara's
trail you have climbed = **how hard He looks** (the lure chain: Mara is
His bait, so tracing her is walking His own line back to Him) = **how
much danger** the world holds = **how far gone the PI is.** One meter,
personal, not bureaucratic.

**The PI is the one who rots (four tiers).** The world rot was built
backwards from its own bible (NARRATIVE §2: "the wrongness is the
place, not the people"; STORY_AUDIT B6 caught it): the code turns
locals into cultist sprites and curdles their dialogue. Relocate ALL of
it to the PI. The town stays **ordinary to the end**; what deteriorates
is the man hearing it, across four evidence tiers — **0** (safe town,
professional) / **1–2** (unsettled, the seams show) / **3** (he knows;
the King arms, the descent opens) / **4+** (underground, past return).
The NPC's words never change; the PI's framing does (the conversation
`prompt`, his interior beats — the engine already supports a
`prompt(game)` callable, as Vane's mood proves). The uncanny inverts:
not "their words curdle" but "his hearing does" — and warm-but-claimed
is worse than curdled, because it never lets the player off the hook.
This also **revives the inert underground evidence**: 4/5/6 turn the
sanity screw even after the King-gate maxes.

**The confrontation's cruelest reach — the name.** With the bear in
hand, the PI can say the boy's name to Mara. He may mean it kindly (an
acknowledgment: *you would have been a good mother to Sam*), but it is
the one word she cannot survive: it drags the son out from under the
god and forcibly **splits the fused "he"** she has spent months
protecting. The reaction is **explosive** — she seizes the PI, the
rite's stillness cracks, the congregation stirs — and in the break she
reveals the bottom of herself: **she knows he is not down there, has
always known, and digs anyway, because stopping means he is nowhere at
all.** It changes her fate not at all (she buries him again and turns
back to the dig); it only shatters her further and costs the player,
who reached for the one word and gained nothing but the wound. The
sharpest knife in the game, and it cuts only the hand that holds it.


## 10. The tilted camera

> Folded in from the retired `CAMERA.md` (2026-07). The oblique view is
> the shipped default; this section is its source of truth.

Keep the game **100% procedural** (no image assets) but render **most
objects as volumetric solids projected to 2D**, lock the camera to an
**oblique ~55° pitch**, and let the player **turn their head** to peek
around the world. The void around each scene is filled with a procedural
**skybox**, not black. A horror **blind-spot vision** layer is the
ambitious payoff (terrain reveals on a peek; threats do not).

**LIVE + DEFAULT.** The game boots tilted (~55°) with mouse-look, and the
oblique view is the **only camera** (`Game._tilt_on`, always true). The
pitch is locked to ~55° for the life of the Game; there is no flat/pitch-0
view. The capture/preview tools render that same tilt, and
`tools/capture_world.py` is the tilt render-regression gate. The modules below are
the live render path under tilt, not isolated scaffolding.

### Decisions (locked with the user)

- **Pitch:** fixed oblique, target **~55°**. Not free-pitch.
- **Default camera:** glued **behind the player's facing** -- whatever
  compass direction the player faces is "forward / camera home."
- **Rotation = a head-turn, not an orbit.** Free-smooth yaw, **clamped to
  a 90° total arc** (±45° off forward), **eases back to center** on
  release. The player peeks left/right; they do not spin the world freely.
- **Skybox, not black voids.** A procedural far backdrop fills the area
  beyond the playfield and **parallaxes with yaw**. Scene-type aware: an
  `overcast` sallow sky for Brimley daytime, a near-black `void` surround
  for interiors/underground. It is a *skybox*, never a roof over the play
  area or the UI.
- **Blind-spot vision (Phase 4).** When the head turns, the **terrain**
  behind/around the player is revealed (it just draws), but **NPCs and
  the world-rot decals stay hidden until actually looked at** -- gated
  to a forward sight cone (`rendering/sight.py`). Locked calls: cone **74°
  half-angle / 360px** range, an always-seen **40px** near bubble;
  **re-hide** when out of the cone (no last-seen memory -- the dread is
  uncertainty, not a stale ghost); the world **keeps simulating
  off-camera** (entities move/chase normally while unseen -- "not looking ≠
  not there"), only the *render* is gated, so a thing re-enters view
  wherever its own logic carried it. The **King is exempt** (a relentless
  apex you must be able to track); the player is never gated. **Pickup
  items are exempt too** -- a pickup is not a threat, so it always draws
  (it was tiny + easy to miss), and it joins the occlusion **focus** set
  so an occluding wall/prop fades for a gem instead of hiding it. The
  blind-spot **fog** (`_draw_sight_fog`) is **shadow-cast**: each ray
  across the cone stops at the first solid (`Scene.blocks_sight`), so the
  clear region is a true visibility polygon with crisp tile-edged shadows.
- **UI stays flat / screen-space.** HUD, dialog, notebook, vignettes, and
  full-screen overlays (transition fade, apex wash, death cards, the
  Carcosa cutscenes) are unaffected by the tilt and keep drawing in screen
  space. Do **not** route them through the camera.

### Why this fits the project

THRESHOLD already draws every sprite procedurally and **already rewrites
sprites at runtime** (the world-rot overlays, the human→vessel morph in
`transform.py`, the King's per-frame `_YK_*` state). A
3D-points-projected-to-2D approach is the same idiom -- matrix math in the
draw call -- so it honors the "no image-asset pipeline" rule. We are
**not** pre-rendering models to sprite sheets (that would be an asset
pipeline and is off-ethos). The whole game converts world→screen with an
ad-hoc `sx = x - cam_x; sy = y - cam_y` at every draw site; centralizing
that one seam makes tilt + rotate a parameter change instead of a
per-scene rewrite.

### Coordinate convention

- world **x** → screen right
- world **y** → ground depth (screen-down at pitch 0)
- world **z** → height **off** the ground (0 = on the floor), screen-up

At `pitch = 0` this is exactly the top-down view (z has no screen effect --
you see the tops of things). As pitch rises toward π/2 the ground
foreshortens (`cos pitch`) and height projects upward (`sin pitch`).
Optional `yaw` spins the world about the vertical axis (the head-turn).

### Modules (all under `rendering/`)

| Module | Role |
| --- | --- |
| `camera.py` | **The seam.** `Camera.project(wx, wy, wz)` → screen; `world_to_screen()` is a drop-in for the old `x - cam_x` form (identity at pitch 0). `depth()` is the painter's-algorithm sort key. Owns `pitch`, `yaw`, `scale`, `origin`. `ground_squash()` / `height_rise()` are pitch-aware footprint helpers. |
| `solids.py` | **Volumetric kit.** `draw_solid` (body of revolution from stacked elliptical sections -- columns, figures, the Watcher), `draw_box` (crates, walls), `draw_billboard` (the fallback: a flat sprite stood up as a camera-facing card so un-converted objects still place under tilt), `draw_with_alpha` (render-to-scratch helper used by occlusion). |
| `skybox.py` | **Backdrop.** `draw_skybox(surf, rect, yaw, kind)` -- sky gradient + sallow Sign-band + fog horizon + a wrapping near-black treeline/rooftop silhouette that parallaxes on yaw. `kind ∈ {overcast, void}`. |
| `occlusion.py` | **Don't-hide-an-actor.** `occluder_alpha(...)` fades any solid nearer the camera than a focus actor AND covering it on screen (feathered so walls ease rather than pop). `draw_world` calls it **per visible actor** and takes the min, so a wall fades for whichever actor it covers. |
| `sight.py` | **Blind-spot vision.** `visible_factor(px, py, heading, tx, ty, blocks)` → 0..1: a forward cone keyed to the look heading (`SIGHT_HALF` 74°, `SIGHT_RANGE` 360px, `SIGHT_NEAR` 40px), gated to 0 by walls via `los_clear` (a coarse ray march against `Scene.blocks_sight`). Soft at the cone lips (`SIGHT_*_FEATHER`). The gate the game draws through under tilt. |
| `pseudo3d.py` | The original proof: a volumetric Watcher (`draw_pseudo3d_watcher`) with self-occluding features and travelling rim light. Superseded by `solids.py` for general use; kept as the worked reference. |

### Working agreements for this track

- **The tilt is the only camera.** There is no flat/pitch-0 view; the pitch
  is locked. Verify render changes with a before/after tilt capture
  (`tools/capture_world.py`), not just smoke.
- **Keep it asset-free.** No PNGs, no bake step. Solids are math.
- **Previews before live wiring.** Render to PNG/GIF headless, eyeball it,
  *then* touch `game.py`. Previews (headless, self-configure SDL dummy
  drivers): `tools/preview_{pseudo3d,tilt,skybox,occlusion,look_control,sight,blindspot_live}.py`.

### Ground heightfield (PROTOTYPE, dormant)

A per-scene ground height so terrain rolls and a crest you can't see over
occludes like a wall. `Scene.set_ground(grid)` / `Scene.ground_z(x_px,
y_px)` (bilinear, 0.0 when unopted → dead-flat, pitch-0 byte-identical);
authored with `rendering/heightfield.build_heightfield(w, h, bumps)`. It
feeds SIGHT (an optional ground-crest term in `sight.los_clear` /
`visible_factor` and `Scene.clear_sight_line`, `SIGHT_EYE_H`, so a hill
hides what is beyond it in both the draw gate and the cult AI) and DRAW
(`heightfield.draw_ground_mesh` lays a projected floor mesh over the flat
affine raster where a scene authored hills, tilt-only; actors/standees
lift by `ground_z`). Movement stays 2D (height is a passive READ; AI
ignores it in v1). **River spike:** `heightfield.carve_channel` cuts a
sunken trough (banks from `build_heightfield`, bed below grade), shaded WET
on `~`/`@` bed tiles, the bank crest occluding the bed (the sight-pit the
WADE water routing wants). Wired but **dormant** -- no shipping scene opts
in yet. Guard: `tests/render_smoke.py` [4/4]. Preview:
`tools/preview_heightfield.py`, `tools/preview_river_channel.py`.
**Deferred:** rolling the whole floor raster (a mesh/displaced warp
replacing the global affine `_tilt_warp`); multi-floor buildings;
continuous traversable z (a big collision/AI/depth-sort/save lift).

---

## 11. Audio

> Folded in from the retired `AUDIO.md` (2026-07). The 2026-06 call-site
> audit that also lived there was fully actioned and has been dropped.

The game ships **zero audio assets**. Every sound -- foley, stings, beds,
"music" -- is synthesized at startup in `systems/audio.py` (pure-Python
sample loops or numpy), optionally post-processed by `systems/dsp.py`
(scipy biquad filters + a Schroeder reverb), and handed to pygame as
finished `Sound`s. Nothing streams. If numpy/scipy are missing the library
falls back to dry generators (or silent stand-ins for the numpy-only beds)
and the game still runs. The library is built **once per process**
(`_LIBRARY_CACHE`) and shared across `Audio` instances (the test-gate win).

### Design language -- anti-melodic dread

- **No tunes.** The music keys are drones. `home`/`village` are *haunted*
  versions of melodies that used to exist (a detuning music-box ping over a
  drone); `threshold_drone` is a bare low tritone (41 + 58 Hz) that never
  resolves. The tritone is the house interval.
- **Sub + partial.** Every low cue carries a mid partial (~200 Hz or a 4th
  harmonic) so laptop speakers, which roll off ~120 Hz, still register it.
  A sub-only cue is an inaudible cue.
- **Breath, not stinger.** The threat vocabulary is built from breath
  shapes: `breath` (an inhale that cuts), `cult_lose` (an exhale),
  `yk_tone` (a *reversed* breath -- air pulled from the room),
  `watcher_spawn` (a vacuum opening). Loud orchestral stings are not in the
  palette; `cult_lock` (sub kick + tritone) is as big as it gets.
- **Space is baked, not live.** The mixer can't do live reverb, so a space
  is baked into a cue that always plays there (the rite cues get `cellar`,
  the Carcosa set-pieces get `void`). Cues that play everywhere get
  **pre-baked per-profile variants** (`step_*` and `gunshot` ×
  `cellar`/`outdoor`) picked at play time by `play_in_scene` from the scene
  tag (`Audio.set_scene_reverb`, called by `Game.load_scene_now`).
- **Silence is a move.** `force_silence` (the testimony beat: the wind
  stops and never comes back), `duck` (music drops so a horror cue lands in
  the gap), and the dead-air stretch inside `custody_bed` are deliberate.
  Don't fill them.

### Mixer + channel map

`pygame.mixer` at 22050 Hz / 16-bit / stereo, 16 channels. Reserved:

| ch | owner | content |
|----|-------|---------|
| 0 | `music_channel` | the looping scene drone (`play_music`) |
| 1 | `ambient_channel` | `falling_air` bed for the door-dream (`flashback_air`), and the tableau room tones (`room_tone`; a tableau and the dream both freeze the world, so the two never contend) |
| 2 | `king_channel` | `yk_tone` loop while the King is on screen (`king_tone`) |
| 3-5 | drive channels | opening drive: engine / radio / static (`start_drive` … `stop_drive`) |
| rest | dynamic | one-shots; `play(pan=…)` grabs a free channel for L/R bias |

Mix gains: `master_vol` × (`music_vol` | `sfx_vol`), settable live from the
pause menu (`set_volumes`). Single-session, like the save model.

### Spatial model

- `pan_for_world(world_x, player_x)` → −1..+1, with a 15% floor on the off
  ear so headphone listeners never lose a cue entirely.
- `distance_attenuation(sx, sy, px, py)` → 1/(1+(d/falloff)²).
- Apply both for positioned cues (enemy deaths, shots, phantom steps).
- `play_in_scene(name)` is the scene-reverb dispatch: plays
  `{name}_{profile}` if baked, else the dry cue.

### Threat wiring (who fires what)

| system | cues |
|--------|------|
| `_tick_visibility` / stillness (`game.py`) | `heartbeat` schedule above proximity 0.70 (interval tightens with threat, music ducks between beats) |
| cult AI (`threat_mixin`, `_cult_tick`) | `cult_lock` (LOS acquired, ducks music), `cult_lose` (LOS broken), `low_pulse` accents |
| watcher curse | `watcher_spawn` / `watcher_dispel` |
| hide state | `hide_enter` / `hide_exit` |
| King (`king_roam_mixin`, `_tick_king`) | `king_tone(on, vol)` -- vol swells with proximity; off the instant he dissolves |
| world rot (`rot_mixin`) | `rot_throb` per stage transition; `sheriff_hunt` on the hollow lawman's spawn + chase start |
| deaths (`_trigger_death`) | `captured_bed` (cult), `custody_bed` (sheriff), Carcosa drone/roar loops (King) |
| case file (`narrative_mixin`) | `evidence_added` (canonical evidence only), `arg_chime` (notes) |
| recurring one-shots (`Scene.add_ambient`) | the scheduler: each entry fires every lo..hi s (re-rolled per fire) with volume jitter and a random pan within `pan_spread`. Ticked by `Scene.update`; additive, never clobbers `on_update_fn` |
| world-rot air (`rot_mixin._apply_ambient_air`) | the audible twin of the decal pass, applied on every scene load. Interiors (`music == "home"`) always carry the LIVING HOUSE base (`wood_creak` + rare `wood_pop`, panned); rot layers escalate with stage: `drip` at 1, `flies` at 2, `whisper` + `rot_throb` at 3. Outdoor scenes gain only the rot layers. SAFE_SCENES stay clean until stage 3; underground/void scenes are skipped (authored / silent by design) |
| pursuer dressing | `breath`, `phantom_step`, `child_hum` in creepy scenes; every 12th creepy-tile step is delayed 0.12 s (the wrongness in the rhythm) |

Dialog voices: per-NPC blip names in `ui/dialog.py` (`blip_low/mid/high/
soft/kid/gruff`), `"__silence__"` for the things that shouldn't have a
voice. **Deferred (dormant, not dead):** `Enemy.shoot_sfx` is plumbed
(`game.py` plays it panned/attenuated) but no enemy sets it; the wiring is
ready if a shooting enemy is ever added.

### The close-up tableaux (the #2b sound pass, 2026-07)

A tableau freezes the world sim, which also froze the scene's scheduled
ambients -- every close-up sat in dead air under the music drone. Two
additions, both inside the design language above (breath, not stinger; no
tunes; silence is a move):

- **`lean_in`** -- the shared OPEN cue: a soft intake (filtered noise
  swelling under a 58 Hz body with a 232 Hz partial, the laptop rule)
  that CUTS rather than resolves -- the world holding its breath as the
  frame closes in. It replaces the old `blip_low` open (a character
  voice blip spent on a cinematic beat). THE TALK skips it (the grab's
  own cues just fired; his breathing is the whole event) and THE
  PEDESTAL keeps its `low_pulse` in its place.
- **Room tones** (`Audio.room_tone`, looped on the ambient channel while
  the close-up is up; the kind→tone map is `_TABLEAU_TONES` in
  `systems/tableau_mixin.py`): Sable **`fan_air`** (the ceiling fan's
  warm push, three sweeps a loop -- the lodge is the warm seat), Vane
  **`window_wind`** (thin cold wind at the glass, the warmth filtered
  out), Hettie **`bulb_hum`** (her one kept bulb: bare mains hum that
  sags twice a loop, the filament wavering), Crane **`nave_air`** (the
  volume of an empty church, one soft timber settle mid-loop), Toby
  **`corn_hiss`** (the dead stalks past his window at a distance -- the
  quietest of the set; his room is the almost-normal one), the Talk
  **`talk_breath`** (two slow breath cycles behind wood that does not
  move), the pedestal **`altar_air`** (the house tritone, 41 + 58 Hz, at
  whisper level, breathing once per loop on the daubed Sign's painted
  period). Every tone is mixed UNDER the caption voice blips (peaks
  0.05-0.13), loop-seam crossfaded, and modulated on whole cycles so
  `loops=-1` never clicks. **Mara's seat carries NO tone on purpose:**
  `_mara_voice` force-silences the room, and her confrontation plays
  inside that silence. The tone stops on tableau close, on scene load,
  and on run reset (`room_tone(None)`); `Audio._room_tone` tracks the
  active cue name for the headless harnesses (flow guards it).

Smaller redesigns in the same pass: a conversation caption in a tableau
now speaks **one voice blip at line start** (`ui/conversation._float`,
tableau branch -- the seats had been mute per-beat while every other
dialogue channel voices its lines; the Talk's scripted captions stay
wordless as authored, the words come from behind wood), tableau menu
motion borrows the dialog band's `cursor`/`confirm` pair instead of
spending a voice blip on UI movement, and Mara's unmask carries a quiet
`low_pulse` under its `wood_creak` (the reveal's weight).

---

## 12. Stealth -- detection is graded

> Folded in from the retired `STEALTH_REWORK.md` (2026-07). The mechanic is
> BUILT and guarded end-to-end by `tests/stealth.py`; the replaced binary
> `hidden`-flag system and the build-sequencing plan that also lived there
> have been dropped as fossils. Tuning is the open item (`TODO.md` #5).

Hiding is not an invisibility toggle; it is a **positional gamble**: cover
lowers how detectable you are, distant enclosure is strong, a searcher
closing on your hiding place is terrifying, and getting caught in one is a
struggle you can still fight out of. The scoring lives in
`systems/stealth.py` (one source for both cult machines -- `entities/npc.py`
surface + `entities/enemy.py` underground); tuning in the
`SUS_*`/`STRUGGLE_*` blocks of `systems/config.py`.

**Design goals (the load-bearing ideas):** cover changes how hard you are
to detect, never *whether* you can be (no binary invisibility); "inside" is
powerful against distant threats but a trap up close; there is always a
decision after you hide (hold, or bolt -- never wait out a timer); keep
what worked (real line-of-sight as the primary tell, the SEARCH/SCOUT loop,
SAFE_SCENES as the one true refuge, the apex exemption).

### Pillar 1 -- detection is GRADED (suspicion), not binary

A per-enemy **suspicion** value in [0, 1] fills from a per-tick
**detection score**:

```
score = los_clear(0 or 1)
      * distance_falloff(d)        # 1 near, 0 at gaze range
      * facing_factor(aim, d)      # the sight cone in sight.py
      * concealment_factor(player) # 1 open, < 1 in cover
```

- **No clear LOS** (a wall/solid prop between enemy and player) → score 0.
  Cover as a hard sightline break stays exactly as fair as it is now
  (windows + water do not block).
- **Clear LOS, open ground** → `concealment_factor = 1.0`, suspicion fills
  fast (≈ instant feel, but with a brief telegraph window).
- **Clear LOS, in concealment cover (corn/shadow)** → `concealment_factor`
  small AND `distance_falloff` bites hard, so far away you are effectively
  invisible but an enemy a few feet away still fills suspicion. This kills
  the "sit in cover right next to a cultist" exploit.

**State transitions keyed to suspicion:** crossing `SUS_NOTICE` → the enemy
turns toward you, slows, shows a rising "?" tell (SCOUT stays, but alert);
reaching `SUS_LOCK` (1.0) → **CHASE** (the hard lock, fires the existing
`cult_lock` audio); score 0 for a beat → suspicion decays at `SUS_DECAY`,
and if it was high the enemy drops to **SEARCH** at the last-seen position.
This adds the classic "have they spotted me yet?" window.

### Pillar 2 -- two cover classes with opposite trade-offs

**A. Concealment cover (mobile, leaky)** -- corn, shadow, behind low props.
You can keep moving through it; it weakens LOS at range, but a close enemy
with LOS still builds suspicion (you cannot camp it next to a searcher);
moving fast rustles → a noise event. Corn scales score + gaze by
`SUS_CONCEAL_CORN`. **Shadow cover:** `SUS_CONCEAL_DARK` for an unlit
player in a DARK scene outside every light pool (`Scene.lit_at` /
`Game._tick_dark_cover`).

**B. Enclosed hide (rooted, strong, a trap)** -- under bed, closet, locker,
"in". A hard LOS break vs enemies that do not come check it (strong at
range); you are **rooted** (no movement while inside); exiting takes a beat
and you are vulnerable during it (`HIDE_EXIT_BEAT` -- bolting is a
commitment). A **searching enemy that reaches the hide tile checks it**
(`sweep_points`) → the **struggle**. The inversion: powerful far away,
lethal when a searcher closes.

### Pillar 3 -- searchers hunt, and you make noise

- **SEARCH sweeps cover.** Instead of milling randomly, a searching enemy
  paths to and **checks nearby enclosed hides** and looks into nearby
  concealment around the last-seen position (builds on the nav grid
  `Scene.nav_path`/`nav_toward`).
- **Noise events.** Running, bursting out of a hide, knocking a prop, and
  the **deep-water WADE splash** (`WADE_SPLASH_LOUD` via `Scene.emit_noise`,
  in the `WADE_SCENES`) emit a noise event through the existing loud-step →
  INVESTIGATE channel (`stealth.hear_noise`); noise pulls searchers toward
  you.

### Getting caught -- the timed struggle

When a searcher checks the enclosed hide you are in, a brief **struggle**
decides it (`_tick_struggle`/`_struggle_win` in `threat_mixin`,
`STRUGGLE_*` config): a short window (≈1.2-1.8 s) with a mash prompt. **Win**
→ you burst out (a one-time short sprint burst, the checker is staggered for
a beat, and a loud noise event converges every nearby searcher -- you won
the moment, not the room). **Lose / ignore** → grabbed → the normal cultist
capture death (`_trigger_death("cultist")`, the CAPTURED card). Only
reachable from a checked enclosed hide; concealment cover never triggers it
(getting found in corn just resumes CHASE). The **first cult grab of a run
is THE TALK** (a warning, not a capture -- threat model §1), and after that
every cult grab is **two-touch**: the first hold of an encounter shoves you
free (`_cult_shrug_off` -- the grabbers stagger, you burst loose with a beat
of grace), and only a SECOND grab before you reach a SAFE_SCENE is the
capture (`_cult_touch_count`, reset only on a safe zone, so a swarm or a
corner still takes you). A struggle LOSS counts as a grab through the same
path.

### Visibility model under the rework

`_tick_visibility` reads **concealment**, not a binary hidden flag: open
ground unchanged (gaze sum × `VIS_GAZE`, minus idle decay); concealment
cover scales the gaze contribution by `concealment_factor` (leaky, not
zero); an enclosed hide contributes ≈ 0 (the strong break) but the
flashlight leak (`VIS_LIT_RISE`) still applies and the **check** is the real
threat. The evidence floor is unchanged (`VIS_FLOOR_TOTAL_CAP`); the Watcher
contribution is now an active CLIMB while exposed (`WATCHER_GAZE`) plus a
smaller residual floor (`WATCHER_FLOOR`) -- the play-notes below-3 threat
(§1). Only an enclosed hide keeps the strong
`VIS_HIDE_BLEED` drain (corn gets idle decay). SAFE_SCENES remain the only
true refuge. The **hollow Sheriff** (`_force_chase`) bypasses suspicion and
cover entirely. The roaming **King** honors `player.hidden` instead (corn or
an enclosed hide drops his hunt to searching, `tests/king_roam.py`); he is
relentless in that he re-finds you and his catch is birth-gated, not in that
cover fails against him.

### The stealth economy (2026-07, the first human tuning pass)

The playtest verdict was "the whole system is avoided because it is just
better to run around the cultist," and the numbers agreed (cultists
patrolled AND chased at 68% of the player's walk). The batch that landed
against it (`tests/stealth.py` §13 guards the contract):

- **The speed ladder is now a real ladder:** King > player sprint (105)
  > locked chase (`CULT_CHASE_MULT`, 85.5 px/s for the surface regular)
  > player walk (84) > scout (57). Walking away from a locked cultist no
  longer works; sprint still escapes but drains and winds (the existing
  stamina), and the King stays the one thing sprint never beats.
- **Sprint is conspicuous** (`SUS_SPRINT_MULT`, in
  `stealth.detection_score`): a running figure in the line of sight
  multiplies the detection score, so blowing past a scout lights the
  bar. Running is the loud, seen, stamina-priced option; cover is the
  cheap one.
- **The cult has an arm's reach** (`CULT_GRAB_REACH`, every grab site):
  brushing past any AWAKE cultist risks the contact grab, not only a
  locked chaser. All the grab gates hold (the Talk, two-touch,
  grab_allowed: concealment yields only to a locked pursuer, an
  enclosed hide never grabs, set-piece kneelers never grab).
- **Cover is VISIBLE:** every bare `:` cover tile stands up as a
  waist-high tall-grass tuft under the tilt (`_tilt_grass_solid`,
  scenes/terrain.py -- dead-straw blades, depth-sorted with the corn so
  the player wades IN). Draw only; collision, sight, and the cover rules
  are untouched.
- **Entering cover is WORDLESS:** the corn and shadow teach notices were
  cut (playtest ruling; DIALOGUE.md reconciled). The `hide_enter` /
  `hide_exit` cues and the visible cover are the only tells.
- **The surface hide desert was watered:** +6 enclosed hides on existing
  props (TODO #5 lists them and what is still open).
- **River stones are the distraction verb** (`STONE_*` config; landed
  with the pass): finite walk-over pickups scattered where the water
  runs (both Brimley banks, the Cistern shores, the Sump ledge).
  Right-click lobs one along the aim; the landing is a placed NOISE
  EVENT and nothing else -- no damage, no stagger, riding the existing
  ear untouched. Its loudness sits between the scout threshold and the
  searcher pull ON PURPOSE: a stone turns an idle head but never breaks
  a sighting-born search, so it routes patrols rather than shaking a
  hunt. A rooted enclosed hide cannot throw; corn can. Guarded by
  `tests/stealth.py` §14. Two follow-ons ride the same plumbing:
  - **A stone through a WINDOW smashes it** (`GLASS_*`): the one thrown
    sound loud enough to divert even a sighting-born search -- the
    bigger lever priced by scarcity (a pane breaks once, stays dark and
    shard-toothed for the RUN via the `broken_windows` save ledger,
    laid back down on every load). The break changes draw only:
    collision and sight are untouched, and it is never an entrance
    (the window-vault idea stays parked).
  - **A stone down the DEAD WELL** (`WELL_ECHO_*`, `_brimley_interact`):
    E at the well with a stone in pocket drops it; the knocks fall
    away, the shaft's rattle carries across the square (scout-tier,
    never a search-breaker), and **no bottom ever sounds** -- wordless
    by design; the missing landing is the beat, and the well stays the
    bottomless dread it is (NARRATIVE §5).
- **The under-bridge hide** (`Game._tick_bridge_knocks`,
  `scene._bridge_hide_px` / `_bridge_deck_px`): a rooted enclosed hide
  on the mud shelf at the Brimley bridge's foot, the town's exact
  centre that everything crosses. While you are tucked under it,
  anything walking the deck overhead KNOCKS on the planks (a
  `wood_creak` pulse + a faint screen-space dust-fall,
  `_draw_bridge_dust`). Pure DRESSING: the crossers neither know you are
  below nor react to the footfalls -- the dread is hearing the town pass
  over your head while you wait. Guarded by `tests/stealth.py` §14 (the
  hide is registered; a crosser raises the tell but never routes to the
  player below).

### Cult liveness -- the scout is a body (TODO #23a pilot, 2026-07)

Two beats of body language on the SCOUT state alone, shared by both cult
machines (`systems/stealth.py` `sync_pause` / `handoff_step`;
`CULT_SYNC_*` / `CULT_HANDOFF_*` in config). The **synchrony beat**: on
one shared slow clock, every idle cult scout in the room pauses
mid-stride at the same instant for one breath, then resumes -- the
claimed-as-one-body wrongness (the Sign Chamber rank's "stirs all at
once") generalized into ambient, wordless behavior. The **hand-off**:
two scouts whose rounds cross stop, face each other for a silent beat,
and part on a long per-actor cooldown -- NARRATIVE §4's
ordinary-people-with-bodies, staged in movement. Neither beat ever owns
a tick outside scout: detection, hearing, and suspicion all score
BEFORE the beats run, so a frozen scout still fills and still promotes,
and notice/chase/search/investigate never pause (guarded by
`tests/stealth.py` §12). Set-piece kneelers keep their scripted
stillness. The rest of the approved behavior plan is `TODO.md` #23.

### Placement principles (the tuning-pass guide, `TODO.md` #5)

Place enclosed hides **near patrol routes**, not in safe corners (a risky
option, not a panic room). Give each combat room a legible cover rhythm
(sightline → cover → sightline). Pair concealment cover along long
crossings so breaking LOS is always possible but never free. Keep
SAFE_SCENES as refuges (cosmetic hides, no searchers). Respect the camera:
hides must read under the oblique tilt (volumes / standees / decals per the
tilt dispatch map), not flat stickers. The Pillar-2 **peek** verb is
deliberately deferred (free look under tilt already gives the information
function).
