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

**The flashlight (`[F]`) is the player's hand on that meter.** The PI's
own kit, taken off the bedroom desk in the opening close-up (beside the
pistol; it moved there from the woodshed in the 2026-07 light pass — light
is the game's spine, so the player's hand on it starts in the first
close-up). It casts a long beam **cone** in
the facing direction through `DARK_SCENES` — the only way to read a black
room far enough ahead to navigate it. But it is **double-edged**: a light
in the dark is a thing that can be seen, so while it burns visibility
*climbs* (`VIS_LIT_RISE`, ~30s of held light alone is enough to erupt the
King). See more / be seen more. The cellar (`DIM_SAFE_SCENES`) is the one
exception — the beam is free there, your room to read by. **The beam works
everywhere dark, the deep included** (the old `CULT_DARK_SCENES` beam-off
is retired, 2026-07 light-pass ruling: a deliberate mechanic that read as
a bug to its only player IS a bug; the deep's dread is what light costs
and attracts, not a dead switch). `CULT_DARK_SCENES` keeps its deepest
gloom tier and the cult sites stay lit by the cult's own ritual fires.

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

### The evidence ladder, the Watchers, the deep-water WADE

> Moved whole from `CLAUDE.md` (2026-07 doc consolidation: one fact, one
> home -- these systems' only full descriptions used to live in the entry
> point instead of the design doc). The **Moths were cut (2026-07)**: the
> King's herald swarm never had a home in the fiction (NARRATIVE never
> named them), doubled the Watchers' "His attention made local" job, and
> inverted the game's own light metaphor (light draws Him, yet a moth is
> the thing drawn to light). Their telegraph beats survive as the
> `the_turning` / `the_breath` notes; the ladder below reads without them.

- **The evidence LADDER (2026-07)**: each surface beat flips a visible
  world state. **Ev 0**: the town is only wrong — **no cult patrols
  spawn** (`CULT_WAKE_EV`, gated at `_ensure_cultists`), the idle King
  far up the road. **Ev 1**: the
  cult wakes (patrols spawn). **Cultist spawn geography (2026-07):** a cult
  scene keeps `Scene.cult_target` roamers filled (default `CULT_REGULARS` 2),
  spawning them at the farthest unoccupied point in `Scene.cult_spawns` (a
  hand-placed spawn-anchor pool) else the map corners — `_spawn_cultist(...,
  from_pool=True)`. On the first awake tick after a load the scene is
  PREFILLED straight to target (`_cult_prefilled`, reset per load) so it reads
  populated the moment you enter; killed cultists then respawn one at a time on
  the `CULT_TOPUP_INTERVAL` breather. The town's **streets and yards** are all
  `CULTIST_SCENES` (§15), so the patrol walks the whole string; a scene with
  no hand-placed anchor pool takes the default target and enters from the map
  corners. All of it is evidence-gated like any patrol. **Ev 2** (`KING_TURNS_HEAD_EV`): his
  attention finds YOU — a one-time telegraph note lands
  (`the_turning`, `_tick_king_roam`): he has **turned his head** toward you
  but has not moved — the ramp's "he sees you" beat so ev3 is not an ambush
  (play-notes). **Ev 3**: he walks (the roam arms) — but the world **holds
  its breath** first: `KING_ARM_GRACE` (~25s) where he stands far and does
  NOT close (`arm_grace` in `_roam_king`; the `the_breath` note fires), the
  window to reach the lodge for the Invitation before the hunt begins
  (decouples the spike from progression).
- **The Watchers** (His gaze made manifest; the play-notes rework made them
  **THE below-3 threat**, `_tick_watchers`/`_apply_curse`). From
  `WATCHER_WAKE_EV` (1) evidence, while you are **exposed** (in the open, not
  in cover / a safe room), the domain **opens** a Watcher on a timer:
  `WATCHER_GRACE` (6s) before the FIRST of a wave (and after you clear one),
  then the **evidence-scaled** interval between the rest
  (`_watcher_spawn_interval`: `WATCHER_SPAWN_BASE` shaved per further
  evidence down to `WATCHER_SPAWN_MIN` — the King floods them deep). Each live
  Watcher **HOLDS you while you are exposed and drives visibility UP** by
  `WATCHER_GAZE`/s (the active climb — `_watcher_gaze`, the main visibility
  driver below the cult), on top of a small residual `WATCHER_FLOOR` (summed,
  capped `VIS_FLOOR_TOTAL_CAP` 0.92, just under the King). Ignore them and it
  **snowballs** (more open, faster); it caps at `WATCHER_MAX` (5). You clear
  them (`_dispel_watcher`): hold one in your **gaze** `WATCHER_GAZE_DISPEL` s
  (its eyes go dark, then it dissolves), or the **axe** / a **round**.
  **Cover pauses the spawn timer and drops the hold**; `SAFE_SCENES` /
  `KING_FREE_SCENES` suppress them (re-form on the way out); a rift fold has a
  `FOLD_WATCHER_CHANCE` to open an extra. **The gaze OPENS under the open sky,
  in the deep, AND in a DARK non-refuge interior ("no light = danger", TODO
  #21; `WATCHER_OPEN_SCENES` folds in `DIM_INTERIOR_SCENES`).** **EXPOSED means
  NOT IN COVER, and nothing else** (maintainer ruling, 2026-07: "Watchers should
  be able to gaze at you while you're standing in the light, that's the whole
  point of them"). **Light is NOT cover from the gaze.** A Watcher holds you
  perfectly well in a lamp pool; the wave keeps building while you stand in one.
  Being seen when you cannot hide is what they ARE, so a lamp can never be a
  safe square -- that would let the player opt out of the one threat that must
  not be opt-out-able. Every way light does work against them is about the light
  on **THEM**, never the light on you: it denies them anywhere to open (the
  spawn rule below) and it **BURNS** one caught in a pool or the beam
  (`WATCHER_LIGHT_BURN`). **You clear them with light; you never hide in it.**
  Guarded, `tests/stealth.py` §11 + §18. **A Watcher can only OPEN at a spot
  that is DARK and holds LINE OF SIGHT to the player (2026-07 spawn rule,
  `_spawn_watcher`):** it manifests where you could answer it with your
  gaze, never in a sealed room or an out-of-bounds pocket, so there is no
  unanswerable accumulation -- and the corollary is the light-security
  promise: a room with no dark spot in view of you cannot open anything.
  **A fully lit room is SECURED; a blackout un-secures it** (guarded,
  `tests/stealth.py` §11).
  **THE STORM is this same wave in a second MODE** (TODO #25, 2026-07), not a
  separate spawner: `Game._storm_active()` is true past `STORM_GATE_EVIDENCE`
  (3) in a room the dark has taken (`scene_gloom() > 0`). While it is up the cap
  lifts (`WATCHER_MAX` 5 → `STORM_MAX` 22, a MEASURED bound -- see the config
  note; the per-unit sprite cache below is what makes 22 affordable), the cadence tightens, spawns drop the line-of-sight requirement and
  open across the whole room, and every unit switches from standing still to
  **walking at the player** (`npc._storm_tick`), refusing any step into light --
  so **light is the only safety** and standing in a pool makes them ring its
  edge. A unit **cannot touch or kill**: walking onto you is a scare, nothing
  more. **Every dispel still works** in a storm -- gaze, light, axe, round.
  Watchers do NOT stop at the gate; they become the storm. Units also stop
  obeying the sight cone and take the apex's fog curve instead
  (`Game.actor_smear_range`, `STORM_SEE_RANGE`): a live 22-unit storm had ZERO
  units pass the plain cone, so the flood was invisible and "they ring the light"
  was unreadable. Guarded, `tests/stealth.py` §19.
  **THE APEX is the storm's one real threat** (TODO #25, 2026-07): the Mask that
  WEARS a unit. **Not the keystone** -- the one Mask OBJECT is on the cult's
  altar until the PI lifts it, and the face riding a shadow here is a SLICE of
  Him (NARRATIVE §6a; guarded, `tests/conventions.py` check 12, which fails if
  this path ever touches the `pallid_mask` item).
  It is Game state, not scene state (`Game._apex`, like `_king`) --
  one bearer storm-wide is a fence and the wave is cleared on every load, so the
  Mask projects a host into whatever room you are in. It arrives at
  `APEX_VIS_GATE` visibility and withdraws below it, FLOATS to the nearest unit,
  then DELETES that amalgam and becomes it, wearing the unit's own deal verbatim
  plus 2-3 added parts. **It pierces and is immune to light** -- neither a lamp
  pool nor the flashlight turns it aside, where both hold a regular unit off --
  and it moves at `KING_ROAM_SPEED`, above player sprint, so it cannot be outrun
  either. **The answer is the axe or a round**, which destroys the HOST and not
  the Mask: the Mask drops to seeking and re-hosts on the nearest unit after
  `APEX_MIGRATE_CD`, so fighting it buys seconds and never distance. Contact ends the run on its
  OWN death card (`_death_kind == "apex"`) -- deliberately NOT the Unfolding's
  throat-swallow, which is the art of the body the storm replaces; it is a
  wordless placeholder fade until the amalgam's own catch animation is made
  (TODO #25). **Its FACE expresses** (`intent` / `strain` / `skew` on
  `draw_pallid_3d`, eased from apex state by `_apex_face`): a carved object must
  never EMOTE, so the Mask WORKS instead -- sockets narrowing to a slot as it
  acquires you, the seam gapping and the crack running as it closes to take you,
  the two disagreeing on their own wandering clock. Driven by state rather than a
  loop, so it is a tell the player can learn to read.
  **It SCREECHES once when it decides on you** (`Audio.apex_roar`, fired from
  `_apex_face` the frame `intent` crosses `APEX_ROAR_INTENT`): the apex is
  otherwise entirely continuous, and horror needs the moment the rules changed.
  One-shot per host, re-armed from ZERO when the host dies, and silent at a
  hidden player, so it never announces a lock it does not have.
  **And it REACHES for you** (`amalgam._reach_limbs`, aimed by the screen-space
  vector in `_apex_mask_for`, extended by `APEX_REACH_INTENT` * intent +
  `APEX_REACH_STRAIN` * strain): grabbing limbs that grow out of its body toward
  where you actually are and clutch, each on its own phase. Every other part of
  every amalgam idles on a clock and would do the same in an empty room; these
  exist only when it has you. They are also the catch's TELEGRAPH -- they are
  fully out before `APEX_CATCH_DIST`, so the hands arrive before the body does.
  **While a host is worn the roaming Unfolding stands down** ("the
  impossible count stays at one"). Guarded, `tests/stealth.py` §20. The **true refuges stay gaze-free**
  (`SAFE_SCENES` are excluded + `KING_FREE`); a plain interior outside both
  sets is gaze-free too (`tests/stealth.py` §11). (The old GAZE_BIND
  high-visibility trigger is retired.) **The gaze wears two skins (the
  shadow family), and the AMALGAM is now the ordinary one:** `AMALGAM_CHANCE`
  is 0.9, so the OG shroud Watcher is the rare spawn the maintainer asked to
  keep rather than the default. A manifestation is an
  **AMALGAM** (`rendering/amalgam.py`) -- a
  seeded assembly of 3-5 parts from a 22-part library (44 with MIRRORING --
  every part carries a flip flag, so a limb on the left is not the same
  silhouette as the same limb on the right), each part emerging
  from its own free-form CUT (flesh clipped dead flat against the line,
  rim lip on the absent side, haze the only tissue; nothing touches).
  **Its CUTS wear the rift's GOLD** (`CUT_RIM`, 2026-07): an aperture He opens
  reads as the same portal family as the fold / King rift (§7), not a separate
  cold-blue phenomenon. **And each part is OUTLINED** (`AMALGAM_EDGE`, one bone
  pixel around its silhouette) so a shadow in a black room can be seen and
  located while staying as black as it ever was. A blurred glow was tried first
  and cut: a bloom has to be BRIGHT to register, and brightness spread over a
  near-black body reads as a glowing spirit rather than a shadow. An outline
  states the EDGE and spends nothing on VALUE. Bone and not gold on purpose --
  **gold is the portal language** here (the rift, the folds, and an amalgam's
  own cuts all wear it), so a gold outline would blur the distinction the
  family is built on: the holes are gold, the flesh coming through them is not.
  It is **presentation only** and must stay so: it is not in `Scene._LIGHT_KINDS` or
  `FIXTURE_POOLS`, casts no pool, and is invisible to `lit_at`, so it can never
  deny a Watcher a spawn spot, burn anything, or gate the lost-space mouth. The
  creature is visible, not lit.
  Three legibility rules landed 2026-07 after the shapes read as "weird,
  something missing": the flesh palette carries a real VALUE SPREAD (it was
  three tones within six values, so an outlined part was a hollow cut-out with
  no interior); **the GAZE is paler than the aperture gold** (`EMBER` vs
  `CUT_RIM`) and incidental `dim` eyes are pinpricks, because a gaze dimmer
  than the scenery around it cannot be found and a deal's five or six filled
  eye-discs cluster into berries; and the parts sit CLOSE (spread tightened
  from 58px of scatter) with visible haze threads between them, so a deal reads
  as one creature rather than debris. They still never touch.
  **The BODY is dealt first and the legs find it** (2026-07): weight parts
  distribute under the mass centroid as a stance, so a thing stands on its legs
  instead of standing beside them, and `_MASS_DY` normalises each mass part's
  own vertical offset (they range 40..62) so a body lands where the legs reach.
  **Some FLOATING is correct and stays** -- a part arrives through its own
  aperture, so a mass hanging clear of anything holding it is the portal
  carrying it; about a quarter of deals ride high on purpose. What was fixed is
  that floating used to happen by ACCIDENT, to nearly every deal.
  Composition rules bind every deal: at least one weight-bearing part on
  the ground, masses centre, and ALWAYS at least one eye-bearing part
  (every amalgam watches; the dim-ember tone is bright enough to survive
  game scale). Behavior is the Watcher's, identical (this spawn rule, the
  hold, gaze/axe/round/light dispel); the amalgam adds presentation only:
  a staggered part-by-part BUILD-OUT on manifest (`npc._birth`, ticked in
  `_tick_watchers`), and the gaze-dispel plays as a PEELING -- parts
  retract into their cuts in reverse while you stare (`npc._gait`, the
  dispel fraction, set in `_tick_watcher_gaze`; both attrs are draw-only).
  Limbs walk backwards into their cuts; masses breathe themselves shut; a
  dying cut smokes. The gun and axe **share one weapon slot** (left-click
  to use; switch which is equipped from the inventory screen).
- **Deep-water WADE** (`WADE_*` config, `Game._wading`): the
  flooded deep works (`WADE_SCENES` = works_cistern / the_sump /
  depths_threshing) stand in walkable `~` water. Wading a water tile
  **halves the player's speed** (sprint can't clear it) and throws a
  **loud splash** (`WADE_SPLASH_LOUD`, over `NOISE_SEARCH_PULL`, via
  `Scene.emit_noise` kind `"splash"`) that searchers converge on, so
  standing water is a routing risk, not just dressing. No new AI (rides
  the existing `stealth.hear_noise` ear); the SURFACE river is **excluded**
  (not a WADE scene -- the safe path carries a see-over solid on every water
  tile, so it is a barrier you cannot get into rather than water you wade). Water is authored per
  scene with the `_flood` helper (`scenes/depths.py`); guarded by
  `tests/stealth.py` §10.

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
- **The daylight drains — the surface darkens with the stage (the storm's
  STAGE; TODO #25, LIVE).** The outdoor world (`STORM_STAGE_SCENES`, which is
  `OUTDOOR_SCENES` -- every road, street and yard) dims monotonically with the rot stage, routed through the
  same `_draw_dark` lightmap the dim interiors use at a gloom that ramps 0 → 138
  (`STORM_DARK_GLOOM`): stage 0 is full day (early-out, byte-identical), stage 3
  is night. The civic yard-lights threading the roads (§6) become ISLANDS, and
  the flashlight earns its place outdoors (with its light-draws-Him cost, §1).
  The blind-spot sight fog (`_draw_sight_fog`, drawn after `_draw_dark`) darkens
  and thickens with the SAME stage gloom, so the unseen region is the darkest
  part of the night rather than a bright gray wash floating over a dark town.
  It is the ashfall's LIGHT twin — the veil thinning as His attention gathers,
  never a day/night cycle (no `day_phase`/`day_count`; the daytime invariant
  holds, NARRATIVE §canon). It carries one real mechanic today: the lost-space
  MOUTH (§13) only lets go at `LOST_EDGE_GLOOM` (stage 2), so falling out of the
  world is a consequence of this darkening. What the dark pointedly does NOT do
  is help the player -- it is never concealment (§12) and a lamp pool is never
  cover from the gaze (§1). The dark is the CONDITION His things need, not a
  tool you get to use; what is still missing is the flood it exists to hold: the
  amalgam-cut storm (TODO #25).
- **The people do NOT change — the man hearing them does.** The town stays ordinary end to end: every local keeps their
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
  player-driven.** The last holdout, and the
  one soul in town **claimed but unattuned** (he never dreamed the door;
  NARRATIVE §4). The world rot never turns him on its own; a hidden
  **despair/hope ledger** decides his fate (`vane_despair`, the `VANE_*`
  config block; surfaced only as his **mood** — the conversation's
  framing line, the beats, and (2026-07) his **pose in the office
  tableau** (`_vane_tableau_state` mirrors `_vane_prompt`'s thresholds:
  despair turns him to the window, hope leans him in) — never a number). **Hope has one
  currency:** the PI **sharing a real discovery** with him
  (`share_journal` in `VANE_CONVO`, `_vane_share` — Mara's journal, the
  case he is being asked to believe in; the Ledger share was cut 2026-07,
  the registers being Sable's thread), so tending him and earning his help
  are one gesture.

  **Trust gates the ANSWER, never the QUESTION** (maintainer ruling,
  2026-07). His withheld exchanges — the cult question (the blind-cultist
  *how*) and the gun cabinet — are **askable from the moment their
  situation exists**, and a Vane who has been given nothing simply refuses
  them, in his own voice, saying what would change his mind. He is a
  mistrusting man, so let him be seen mistrusting: an option greyed out of
  the menu teaches the player nothing, while a refusal is characterisation,
  a stated price, and a reason to come back. Both rows stay askable until
  he has actually answered (`vane_how_told` / `vane_gave_cache` retire
  them), so a refusal is never a lockout, and the refusal branch must never
  fire the grant — the `("do", ...)` beat sits at the END of the trusted
  branch only. **Despair** comes from the beats
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
  All of it stays behind the `CULT_WAKE_EV` gate. The **cult camp**
  (`_camp_pos`) stands in the **farm yard**, the one lot in town the newcomers
  already hold; its crew fills from the pool when the cult wakes. The camp is
  raised in `_cult_camp` (`scenes/yards.py`, the scene's on_enter) only at 1+
  evidence
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

> The **concrete code changes** for canon-alignment work live in
> **`TODO.md`**; the decisions themselves are canon and live where canon
> lives (`NARRATIVE.md` §§1, 2, 4, 6, 8, 9). The history of everything this
> section used to list as loose, and how it landed, moved to
> `CHANGELOG.md`. What's still genuinely open is below.

- Dynamic cultist AI (no preset patrol coordinates, line-of-sight
  detection, nav-aware pursuit, fold-only chase carry), the eat-cult and
  time-loop fiction scrubs, Toby's cut "dad" line, the journal door-dream,
  the maker-less effigy grove, the Watchers' rehoming as His gaze, the
  gun's false-power threshold, corpse persistence, the "he knows you"
  threshold recognition, and naming the principal locals are all landed —
  see `CHANGELOG.md` for what each was and why it changed.
- **The liminal-composition pass** (§6): per-scene level design —
  composed emptiness, long sightlines, uncanny repetition.
- **Food scarcity — the VISUAL pass (mostly done).** The dialogue side is
  done (Hettie: "The shelves don't empty anymore... No deliveries.";
  "Shelves are bare. Till's been empty since the new year"), and the world
  art largely landed: the shop's `bare_shelf` runs (dust-ghosts where the
  stock stood, one tin left), Hettie's storeroom preserves, garden patches
  on some town lots and not others. Still open: the domestic-horror beat
  of a cultist eating an ordinary meal at a counter (NARRATIVE §4). Wallpaper, not a
  mechanic.

---

## 5. The Basement Level — "The Works" (built)

The cult's **year-long excavation**, reached *only* through the effigy
grove's mine shaft — the descent is the door-dream rite at the shaft mouth
(2026-07), which lands at the Shaft Floor of the cult's own mine (scene key
`well_bottom` — a legacy name; the town well itself is dread set-dressing
and goes nowhere, NARRATIVE §7). The attuned didn't build a
temple — they **dug**, following
the water down toward the door the dream promised (NARRATIVE §2). The seven rooms
are the **dig** at successive depths; partway down it broke into the
underground river (Room 3), the diggers' proof they were close. A
seven-room stealth gauntlet, descending. Built in `scenes/well.py`; all
rooms are `DARK_SCENES` (flashlight works, but the cultists' gaze still
finds you — run it on cover, timing, and breaking their line of sight).

| # | Room | Key | Contents |
|---|---|---|---|
| 1 | The Shaft Floor | `well_bottom` | The descent (the door-dream down the shaft) lands you here; its return pane (the way back up) stands where the rope once hung. Quiet airlock, 1 hide. |
| 2 | The Timber Racks | `well_passage` | The dig's staged shoring lumber, racked on its way to the faces (renamed 2026-07: the old drying-corn-doll-material fiction was cut -- an obsessive dig runs no craft room). A LONG rack gallery (24 tiles, lengthened 2026-07 -- the stealth pass: graded suspicion needs distance), 2 patrolling cultists offset down the run, 2 hides. **Two dug side-chambers off the run (#14 pilot, 2026-07):** a FINISHED store squared into the east wall (crates, staged boards, a kept candle, a wall tally) and a HALF-DUG niche the diggers quit in the west (a low spoil pile, pick gouges, no light), each reached through a single timbered ADIT off the corridor (distinct from the open central bay). Exploration texture off the patrol lane; the tuned E-W run, racks, and hides are untouched. |
| 3 | **The Cistern** (was "Tallow Vats" — cut) | `works_cistern` | Where the dig **broke into the underground river** — the artery to the door (NARRATIVE §2), and the diggers' proof they were close. Wet stone, rising damp, 2 tending cultists, 2 hides. *No rendering, no tallow, no bodies — the claiming cult eats no one. The scene key is now `works_cistern` (renamed 2026-07 to match the Cistern).* **#14 (2026-07):** a HALF-DUG niche clawed into the dry SW corner stone (a timbered adit off the crossing, a low spoil pile capping the corner, pick gouges, a cold seep, no light) — where the dig tried for the river through the corner and gave up. |
| 4 | The Sorting Hall | `works_sorting` | The **worldly lives the congregation shed** when they were claimed — and the effects of the few the fold took — sorted and catalogued. 2 cultists, 3 hides (hardest crossing). A side door north → **Mara's room**. **Two dug side-chambers off the sorting floor (#14, 2026-07):** a FINISHED overflow store (crates, a shed-life pile, a kept candle, a wall tally) and a HALF-DUG niche (a low spoil pile, pick gouges, no light), each through a single ADIT cut into the north block clear of the tally + taxidermy mounts, off the patrol floor so the tuned crossing/tables/hides are untouched. |
| 4a | **Mara's Room** | `maras_room` | A convert's cell off the hall: cot, her cult robe + the unsent letter. **Evidence: the unsent letter (`maras_room`, a canonical trail beat — NARRATIVE §6).** A quiet beat off the gauntlet, 1 hide. |
| 5 | The Scriptorium | `works_scriptorium` | The Sign copied endlessly — the **attuned compulsively bleeding the dream-image out** onto every surface, none of them the door itself (NARRATIVE §2). 1 oblivious scribe, 2 hides. **The Calling** — the first of three cult-testimony fragments (NARRATIVE §9), the one bound, whole volume among the loose copies: the congregation's own personal testimony (their voice in the item description, the PI's reaction in his notes). Pure lore; it gates nothing (the keystone is the Mask alone). The Bargain + The Digging are found deeper (the Sump, the Old Stores). |
| 6 | The Sign Chamber | `works_sign` | The Sign daubed on the wall + an altar; the kneeling rank (set-piece NPCs) + 1 patrol. **The calling-out (2026-07):** Mara kneels among them; first entry, the kneelers rise, one says her name, she comes to you — the confrontation lands (Mara is **proof, not a counted beat**: the calling-out fires but no longer counts). The talk itself is the last **close-up tableau** (`_open_mara_tableau`, §16): she opens masked and hooded, listed as one of the congregation, until the greet unmasks her — the reveal. **Lift the Pallid Mask → `pallid_mask`** — the **keystone item**, not a case beat (it left the count; NARRATIVE §6). No charcoal; you take the object itself. |
| 7 | **The Deepest Face** | `works_deepface` | The dig's END — the cult's testimony left "a few feet of earth"; there is no stair, no gate. With the **Mask in hand** (the sweep finished) and **powder from the Sump**, a two-press charge **blasts the floor through into the old workings**: the FALL into `depths_antechamber` is the one-way step. The Mask is **not consumed** — carried down and spent at the Threshold door. |

**Rules wired:**
- **One way down:** the grove rite (the door-dream at the mine shaft) only;
  the barn cellar hatch stays sealed (`scenes/interiors.py`). The shaft-floor
  return pane is
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
  the purged `bone_rack` furniture kind). The mine's dressing (spoil heaps,
  shoring frames, cart ruts, wall tallies) landed with the art pass; the
  LEVEL-DESIGN half -- timbered side-chambers dug off four halls (the Timber
  Racks, Sorting Hall, Kneeling Hall, and Cistern), some finished, some
  half-dug, reached through single timbered adits -- landed room by room per
  VISION (the octagonal/cavern rooms carry the dig read by shape + existing
  dressing; `CHANGELOG.md`, "The Works, the mine").
  **The corridors walk LONG (2026-07, the stealth pass):** the graded
  suspicion model (distance falloff) only reads when "far" exists, so the
  three corridor rooms were stretched -- the Timber Racks gallery (24
  tiles, 2 patrols, 2 hides), the Depths' **procession drift** (30 tiles,
  the main hallway: 3 patrols in spread phase, 3 bay hides down the run),
  and the Kneeling Hall's nave (20 tiles, pews + a hide in each half).
  Rule of thumb when touching these: every long room keeps a rooted
  enclosed hide in each half, and patrol phases are spread so no half is
  permanently clear.
- The well sprite was redesigned and now stands on **the square**, the
  crossing outside the store on `store_row` (a landmark just off the road;
  `scene._well_pos`, laid by `_town_square` relative to the junction rather
  than by a tile number).

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
- **THE GROUND is the biggest surface in the frame, and it is built in
  three layers.** Under a fixed 55-degree camera the floor is most of what
  the player looks at, so a flat fill is a flat fill across half the screen.
  (1) The BASE is a per-char colour bilinearly smoothed across tile corners
  together with the macro shadow, so brightness rolls ACROSS tile edges
  rather than stepping at them. (2) The DETAIL is clustered, never
  sprinkled: grass is one to three tufts of blades plus last year's straw
  mat, dirt is fine grain with a few seated stones and a short angled
  scuff. Detail runs mostly DARKER than the base -- turf at this distance is
  the shadow between the blades -- and both the count and the placement vary
  per tile, because a fixed count is itself a pattern. Nothing may carry a
  screen axis: a full-width mark at a fixed tile row becomes a stripe on a
  rotated facing (`d` had one, and the plank floor had the same bug before
  it). (3) The SEAM between two chars is frayed by `_build_path_fringe_card`
  for every char in `_PATCH_CHARS`, in both chars' colours. Tiles are cached
  BY CHAR so no tile can know its neighbours, which makes every unfrayed
  boundary a hard straight step at the grid -- and a lone tile of a
  different colour then reads as a hole rather than as ground. Values sit in
  one damp April family: the dirt paths must never be the brightest thing
  outdoors, and wet ground gets its darkness from the puddles drawn on it,
  not from a near-black base.
- **OBJECTS ARE NOT TILES, AND OCCLUSION FOLLOWS FROM HEIGHT.** The rule
  walls established with `_wall_slab` -- authored per tile, but carrying a
  real sub-tile footprint that is the SINGLE SOURCE for the draw layers and
  for `is_solid_at` / `blocks_sight` / `_nav_solid_at` -- now applies to
  plants too (`scenes/terrain.py` `tree_footprint`). A tree stands off its
  cell centre and blocks as a round foot, so a stand reads as a wood instead
  of a grid and the player slips between trunks on the diagonal the way the
  silhouette promises. Jitter plus foot is held under 0.7 of a tile so a tree
  can never seal a corridor it was not authored into.
  Because the player collides as a POINT and a trunk is a circle, the gaps
  between trees are now a property of the stand rather than something a
  designer marks tile by tile. That retired the walk-through tree outright
  (about half the forest was one); a band of solid trees still admits a
  straight north crossing at 25-55% of its width, and far more on the
  diagonal, which is the "push through the woods" feel the permeable band
  was hand-authored to fake. It also retired the tile-granular reachability
  guard: `tests/smoke.py` floods sub-tile through `is_solid_at` in any scene
  with solid plants, because a coarse 4-way tile walk cannot see a diagonal
  gap and was rejecting real routes.
  Occlusion is then a consequence of geometry rather than of draw order.
  Two rules make that true: **nothing gets a privileged layer** (anything
  with height joins the one depth-sorted pass -- `bush` used to be a floor
  decal, drawn before the pass, and so could never occlude anything at any
  position), and **every occluder reports its own height** (`tree_height`)
  to both the depth key and the fade box, instead of the flat wall rise of
  26 that a 50-tall spruce and a knee-high scrub both used to claim.
- **Interior walls render as thin-slab geometry, per material (current
  state; `scenes/terrain.py`; how this evolved -- bevel -> slab -> rounded ->
  materials -> the mine as hewn rock -- is in `CHANGELOG.md`, "Walls &
  interior geometry").** `_wall_slab(scene, tx, ty)` returns a wall tile's
  footprint as the union of up to two BANDS (a vertical band where the tile
  has a wall neighbour N/S, a horizontal band where E/W), so
  runs/corners/tees/crosses meet FLUSH with no fat junction and no notch.
  Cross-thickness reads the flanks' openness: floor/wall both sides CENTRES a
  two-sided partition; one flank off-map is the building SHELL, hugging the
  exterior edge (no floor lip, thinning inward). This is the SINGLE SOURCE
  for both draw layers (`_extrude_box`'s `foot` param, `_draw_wall_mass`'s
  clip) AND the collision/sight/nav predicates (`scenes/base.py`
  `_obj_solid_here`, point-in-ANY-band) -- the wall the player bumps and the
  AI's line of sight obey the wall drawn. `_rounded_wall_poly`/`_fillet`
  round every FREE corner (facing open floor) into an arc while wall-seam
  corners stay sharp so tiles connect flush; collision/sight/nav keep the
  square bands underneath (the rounding sits inside the drawn face).
  Thickness, corner round, surface roughness, and a dark muddy colour tint
  are per-MATERIAL (`_WALL_STYLES`:
  plank/plaster/timber/brick/stone/rock/turf), keyed per scene via
  `_SLAB_STYLE` and read through `_wall_style(scene)`; `_SLAB_SCENES` is
  derived from it, so adding a scene is one `_SLAB_STYLE` line. An optional
  **`top_tint` tints the TOP cap face separately** from the sides
  (`_wall_top_tint_for`, applied in both draw layers) and only `turf` sets
  one: a GRASS-green top over cold STONE sides, so a full-thick mound reads
  as a grassy HILL with bare stone where it has been cut into (the grove's
  mine mouth is a turf hill in `_ROCK_STYLE` with a stone adit). Every other
  style omits it, the top falls back to the side tint, and those scenes stay
  byte-identical. Gated to `_SLAB_SCENES` -- every
  above-ground building interior has opted in; every non-slab scene returns
  `None` -> full tile -> byte-identical. The MINE (Works + Depths + Mara's
  cell) instead renders full-thick hewn ROCK (`_ROCK_STYLE`/`_ROCK_SCENES`:
  `thick`=1.0, so `_wall_slab` returns full-tile bands AND it stays OUT of
  `_SLAB_SCENES` -- collision/sight/nav read the tile grid UNCHANGED, only
  the styled outline roughens). This SUPERSEDES the older draw-only corner
  bevel where both would apply (`_bevel_corners` returns 0 in a slab scene).
  Cache-safe throughout (pure functions of the tile + its neighbour chars +
  the gate). Roll `_SLAB_STYLE` out one interior at a time per VISION.
  **Doors and windows take the slab THROUGH the gap (`_gap_slab`).** A
  door/window tile is not a wall char, so `_wall_slab` returns None for it;
  `_gap_slab` carries the flanking walls' band through the gap tile instead
  (same `cross()` rules, so it meets the neighbour bands flush). The door's
  lintel box, the window's box, and the window pane's face plane all read
  it, in the wall's material tint -- without it they extruded as full-tile
  near-black monoliths jutting from the thin wall line. Under tilt a slab
  scene also skips the flat full-tile window art (the 3D band + set-in pane
  carry the read).

  **A WINDOW PANE IS AN ASSERTION** (`Scene.window_glass`,
  `terrain._window_glass`), and there are three of them:

  | glass | what it says |
  |---|---|
  | `"lit"` | warm amber lit from within: **somebody is home** |
  | `"dark"` | a dead pane, the room's dark behind it and a thin cold sheen at the top of the glass so it still reads as glass: **nobody is** |
  | `"daylight"` | flat overcast: you are INSIDE, looking out |

  A scene STATES it rather than having it inferred, because "lit" is a claim
  about who is home and the fiction has buildings that are empty on purpose
  (NARRATIVE §3 -- the school and the barn the congregation walked out of,
  the farmhouse abandoned in its own name). Warm panes on one of those, with
  a silhouette drifting behind the glass, quietly unsay the beat the player
  walks in to find. Unstated, the fallback is the honest one: outdoors you
  are looking at a facade, so `"lit"`; anywhere else you are inside one, so
  `"daylight"`.

  **In town it is DERIVED, not authored twice.** The household's genset is
  already the statement of whether the lights are on -- this town runs on
  gasoline (§15) -- so `Yard.genset` sets the panes from it: running means
  lit, cold means dark. One source, no way for the two to disagree, the same
  trick `running=False` already plays by also passing `broken` so the bulb
  and the ground cannot disagree. It falls out exactly right without anybody
  authoring it: the school, the barn, the farmhouse and Garrick's house all
  have cold gensets, and all four now have black windows. Guarded by
  `tests/conventions.py`.
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
  - **A light kind lives in TWO tables, and the gate checks it.** The
    MECHANICAL cover radius stealth reads (`Scene._LIGHT_KINDS`) and the
    VISIBLE pool `_draw_dark` casts (`FIXTURE_POOLS`) must both carry any
    emitting kind: in only the first it gates as lit but shines nothing, in
    only the second it shines but gives no cover. `tests/conventions.py`
    asserts the two agree, with the shipped disagreements named as explicit
    exceptions to triage (`campfire`, the DEAD indoor scorch decal, currently
    gates as lit; `burn_barrel` shines without giving cover).
  - **The shared light logic (the "carry it underground" foundation).**
    `_draw_dark` (`systems/render_mixin.py`) no longer special-cases
    `wall_torch`: it iterates **`FIXTURE_POOLS`** (the visible-light twin of
    `Scene._LIGHT_KINDS`) across **every** light-emitting decoration in the
    room, so any real fixture -- a cult brazier, a Sign-Chamber candle, a
    town yard light, a genset work-bulb -- lights the dark it stands in. One
    table drives the surface (if it ever darkens) and the deep, with no
    per-scene special-casing. **The beam works in the deep too** (the old
    `CULT_DARK_SCENES` beam-off was retired, 2026-07 light pass — see the
    flashlight note in §1); the cult sites keep the deepest gloom tier and
    stay lit by the cult's OWN ritual fires, with your beam a priced
    option on top.
  - **The light is 3D, and it interacts (2026-07 light-model pass).** Each
    emitter carries a real world SOURCE HEIGHT (`src_z`) and a screen-relative
    gooseneck offset (`arm`): a yard-light head rides high on its pole, a
    candle sits at the floor. `_draw_dark` casts each pool onto the ground
    UNDER that 3D source as a **tilt-foreshortened ellipse** (not a flat
    screen circle -- a floor disc squashes by `Camera.ground_squash()`).
    **The darkness itself composes through a LIGHTMAP (2026-07 rework):**
    every source (pools, fans, the flashlight cone, the player's bubble)
    accumulates additively into ONE luminance field over the room's
    ambient floor, and the frame is multiplied by it once -- so two
    overlapping pools genuinely BRIGHTEN their shared floor and no pool
    ever re-darkens a neighbour's centre (the old per-pool alpha carve
    was painter's-order and left ring seams between adjacent pendants).
    The **colored** pools then blend additively on top (`BLEND_RGB_ADD`,
    warm + cold summing toward white), lifting the walls / props /
    actors standing in them -- **light interacting with light, and with
    objects.** On top, a **cast-shadow** pass throws a soft shadow
    across the floor AWAY from each source for every solid caster in range
    (player, NPCs, solid props): a LOW source (a candle) throws a long shadow,
    a HIGH one (a yard-light head) a short one, and under several lights an
    object throws several. The shadow **subtracts** the pool's glow
    (`BLEND_RGB_SUB`, a cool-grey) rather than painting black over it -- black
    over warm light reads as a brown STAIN, subtraction reads as dark floor.
    Both the pool and the shadow are cached per shape (`_floor_pool_surf`).
    **Light is not only a circle:** a fixture deco may carry
    `cone=(dir_x, dir_y, half_deg)` and throw a directional FAN instead --
    the one kwarg drives the visible fan (`_draw_dark`), the mechanical
    gate (`Scene.lit_at`'s angular test: behind a hooded lamp is honest
    dark), the cast-shadow pass, and the audit overlay's outline.
  - **Electric light runs on the gensets, LIVE (the power link;
    TODO #21 first slice).** The ELECTRIC kinds (`Scene._ELECTRIC_KINDS`:
    `wall_lamp`, `drop_bulb`, `yard_light`) emit only while their scene's
    power is on (`Scene.power_on`, maintained by `Game._tick_power` off
    the `_genset_down` blackout timers). A **blackout blacks its room
    out** for `BLACKOUT_DUR` (no live trigger since the moths were cut,
    2026-07 -- the gas-genset failure that will fire it is deferred,
    TODO #21; the mechanism stands ready, guarded synthetically by
    `tests/stealth.py` §17); during it the electric fixtures die in
    every layer at once -- no visible pool, no mechanical `lit_at` cover,
    and the fixture ART itself goes dark (a dead lamp is dark glass; the
    office radio's static crawl and creeping needle stop, the
    world-state-through-an-appliance tell). Fire is exempt throughout:
    candles, kerosene, and braziers burn on, so a blackout hands the
    room to the warm accents. Power returns on its own; wordless by
    design (the lights dying IS the tell). Guarded by
    `tests/stealth.py` §17.
  - **The interior light is COLD, and darkness is designed (2026-07
    light ruling).** No warm-lamp cosiness indoors: `wall_lamp` casts cold
    blue-white (the maintainer's "LED" read; in 1994 the same light is a
    fluorescent tube / cold bulb, so the period holds) with a fast shallow
    shimmer instead of a candle flicker, and **`drop_bulb`** is its
    ceiling-hung sibling: a simple PENDANT (drop cord into a steel dish
    shade, the bulb glowing under the lip -- the dark shade silhouette
    is what sells 'fixture'; a bare glow read as a floating orb,
    2026-07 maintainer catch). Per-placement hang height via the `z`
    kwarg -- hang it above head height or it vanishes into whoever
    stands at the counter. A dead pendant keeps its dish (dark enamel,
    dark glass), so a blackout leaves visible dead fixtures, never
    vanished lights. Fire
    (candles, kerosene, the hearth) is a PROP with a small warm pool,
    never a room's light source; the **kerosene lamp emits** that small
    warm accent (its draw burns a live flame everywhere, so a poolless
    one was a lie). Fixtures are placed by COVERAGE across different
    walls, and **`tools/light_audit.py`** is the design surface: it
    overlays every emitter's mechanical `lit_at` radius (filled), its
    visible pool (ring, in the fixture's colour), and cross-hatches
    everywhere no radius reaches -- THE DARK as a reviewable shape --
    and prints COVERAGE (% of walkable floor inside a visible pool /
    inside a mechanical radius). **The 90% rule (maintainer, 2026-07):
    with every light on, at least 90% of a dim interior's walkable floor
    sits inside a visible pool; the ~10% dark is chosen, not left over.**
    All five `DIM_INTERIOR_SCENES` hold it (drop cords strung through
    the roof beams are the workhorse), which is what makes a genset
    blackout dramatic: a 90%-lit room falls back to its two flames. Run
    the audit before and after placing any fixture. **And the pendants
    hang in ROWS (maintainer, 2026-07): lights run on one axis at even
    spacing, never scatter** -- cords come off joists and joists run
    parallel, so an open hall gets a straight run down its length (or
    matched runs over its seating/beds), a small room gets ONE centered
    fixture, and adjacent rooms share a pendant line where the framing
    would carry it (the sheriff's north line runs three cords through
    two rooms). Scatter is the light placement's version of the grid
    lockstep failure, inverted: props break the grid, wiring obeys it.
    **The REVERSE LIGHT (maintainer, 2026-07):** an invisible `dark_pool`
    deco (kwargs `r`, `depth`) SUBTRACTS from the lightmap AFTER every
    light has added -- placed darkness that always wins where it contends
    with a lamp, blacker than the room's ambient, with no texture because
    it is only darkness. The audit draws it as a deep-blue ring. Draw-layer
    only (the mechanical `lit_at` gate is untouched); it is the tool for
    authoring blackness exactly where the design wants it (the shop
    pantry's cult tells sit in one). **Moving light sources are expected**
    (not just the flashlight): the visible lightmap rebuilds from live
    deco positions every frame, and `Scene.light_sources` caches the deco
    LIST, never positions, so a carried or swinging source gates
    correctly in the mechanical layer too.
    **And every room carries 1-2 BROKEN lights (maintainer, 2026-07):**
    a `broken=True` fixture kwarg kills it in every layer at once (no
    pool, no `lit_at`, dead in the audit -- which marks it a red X) and
    its art shows WHY (a shattered stub for a bulb, the dish knocked
    askew, the cord's dead kink). Provenance: no deliveries means no
    replacement bulbs, so a dead gap in a straight run is the town
    failing in miniature -- the 90% target is the WIRING's design, and
    the burnouts carve the lived-in dark below it (rooms sit at ~81-88%
    live). Guarded by `tests/stealth.py` §17. **The shop is the first audit-designed room:** lit on
    purpose at the counter (Hettie's kept bulb over the till, the warm
    kerosene accent inside its cold pool) and the east floor
    (`wall_lamp`); dark on purpose in the north aisle, the stove corner,
    the office nook, and the stockroom->pantry chain (candle, then pitch
    black for the cult tells).
  - **Interiors run on the gensets too (2026-07 interior lighting pass).** The
    explorable non-refuge interiors (`DIM_INTERIOR_SCENES`: shop, church, barn,
    schoolhouse, sheriff's office) are `DARK_SCENES` at a **lighter gloom**
    (72, vs 100 for the deep and 130 cult-dark) -- they read "dim, lit by the
    genset's bulbs + window spill, dark in the corners," not a pitch-black
    cellar, and the flashlight works. Their MAIN light is the period-electric
    **`wall_lamp`** (a 1994 bulkhead/utility fixture: conduit + frosted shade +
    steady warm bulb, the indoor twin of the yard light), with the old candles
    / kerosene lamps demoted to **backup accent** (realistic for a town on
    failing genset power). The **refuge is deliberately excluded**
    (`SAFE_SCENES` -- the PI's room, toby_house -- stay flat-lit + safe;
    DESIGN §12), and the truly-abandoned interiors (`abandoned_farmhouse`,
    `lodge_cellar`) keep the darker gloom + their candles. This is the ground
    the "no light = danger" Watcher rework will stand on (`TODO.md` #21).
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

`cornfield_maze`, `cornfield_path`, and the Lodge yard (`lodge_yard`) all
wrap on the relevant axes. The town itself no longer wraps at all: it is a
string of house islands on the street network (§15), and a street is a
`SafePath` whose arms end at exits, which is the opposite of a torus. The
wrap belongs to the CORN, which is where it always meant something.

- **cornfield_maze.wrap_x = wrap_y = True** -- corn never ends in
  any direction. The exit tiles (^ to the country lane, ! to cornfield_path)
  are the only escape, and finding them is the whole point.
- **cornfield_path.wrap_x = wrap_y = True** -- the woods spit you out
  where you walked in.
- **lodge_yard.wrap_x** -- walking east past the Lodge wraps you
  back to the west. There is no past-the-Lodge highway.

### Cross-scene macro-loop

The corn belt closes the outdoor world into one closed system, and it hangs
off the road network at ONE junction -- the country lane's south arm, which is
the one arm the standing corn already grew up to:

- **country_lane** south arm ('4' tile) → cornfield_maze
- **cornfield_maze** north ('^' tile) → country_lane, south ('!') →
  cornfield_path
- **cornfield_path** south ('S' tile) → country_lane

Walking south through the corn returns you to the lane, and the lane returns
you to the corn. No direction escapes. The loop closes the long way round
too: lodge yard → cornfield_path → the maze → the lane → the arrival road →
the lodge yard.

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
itself** — the school↔grove pane, the shaft floor's keyed return, and the
King's portal. (The grove's DOWN is no longer a fold: it is the physical
mine shaft, descended by the door-dream rite, 2026-07.) Faced head-on, a fold SHOWS
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
    (the school door and the shaft floor's keyed return -- at rest, quiet)
    and the King's portal (the same frame torn violently). One renderer,
    one black-gold grammar. (The grove's DOWN left this family in 2026-07:
    it is the physical mine shaft now, descended by the door-dream.)
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
including surface↔underground. Shipped uses: the **shaft-floor keyed
return** (`well_bottom` → grove, answers only the Mask, then seals), and the
**school door** (opened by the chalk-door rite, then permanent). (The grove's
DOWN was a state-driven fold until 2026-07; it is now the physical mine shaft
below, descended by the door-dream rite and lands at `well_bottom` via the
grove's `on_update`, no fold.) Folds stay two-way until they DIE or are **KEYED** --
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
street it sits on -- a yard's house faces whichever way its own door is in
(§15: which way it fronts is one of the things a yard says) rather than all
facing south.

### Interior doors -- dividing a building into subrooms (2026-07)

The third door kind, distinct from the two above. A fade-door is a scene
boundary; a see-through door shows a *different* scene's room through an
opening. An **interior door** is neither: it is a swinging leaf on a floor
GAP in a wall line **inside one scene**, the tool that turns a box building
into several subrooms (the room-redesign lever -- buildings divided into
several subrooms, not one open box).

State lives on `Scene._inner_doors` (`(tx, ty) -> {open, kind, swing,
close_t, seed}`); author with `Scene.add_inner_door(tx, ty, kind, open=False)`
on a floor tile that sits in a wall run. It hooks the three existing
predicates so a **shut** leaf behaves exactly like a wall and an **open** one
like a gap, with no bespoke pathing:

- `is_solid_at` -- a shut door blocks the body (a wall); open passes.
- `blocks_sight` -- a shut door blocks the sight cone (so the room beyond
  stays hidden until it is opened), **except** the see-through kinds
  (`_SEE_THROUGH_DOOR_KINDS` = bars / half: they stop the body but you look
  through them, the cell-gate / counter read). Open always passes. This is
  the same `blocks_sight` that `clear_sight_line` runs, so ONE hook covers
  both the render sight-gate AND the cult-AI line of sight -- **a shut door
  breaks a pursuer's lock and buys time** (the design ask).
- `_nav_solid_at` -- a door tile is never a nav wall, so NPCs route AT it and
  open their own way through.

**Most start closed.** `Scene.update` runs the open/close: an NPC within ~1.5
tiles of a shut door opens it (a `wood_creak`), the door holds open while any
actor is near, and it swings shut a beat (`close_t`) after the last one
leaves. The player toggles the nearest door in reach with **E**
(`toggle_nearest_inner_door`, wired last in `try_interact`). The `swing`
value lerps toward the open/shut target each frame and drives only the draw.

**Draw** (`rendering/props.draw_inner_door`, emitted in `draw_world`'s tilt
pass, depth-sorted with the walls/props): the leaf swings on its hinge from
across-the-gap (shut) to along-the-wall (open); `ew` (an E-W wall, read from
the tile's wall neighbours) sets the hinge axis, so a door in a SIDE (N-S)
wall opens east/west and a door in an E-W wall opens north/south. Kinds carry
their own look: **plank** (wood panel, seams + knob), **bars** (a see-through
iron cell gate), **curtain** (a maroon drape), **half** (a low counter door
you see over).

**Placement -- vary the wall, don't face them all one way.** Because `ew` is
derived from the tile, WHICH wall you cut the gap into decides which way the
leaf faces. Do not put every door of a building in E-W walls (they would all
"face south" -- the same monotony the exterior-door rule and playtest error
class 8 warn against). Mix side-wall (N-S) doors that open east/west with
E-W-wall doors that open north/south, chosen by what the room's geography
wants. The shop pilot does this: the stockroom and office doors sit in side
walls (open E-W), the nested pantry door in an E-W wall (opens N-S). Verify
under the tilt -- both orientations render (a side-wall door is a vertical
leaf shut, swinging perpendicular open).

Guarded by `tests/stealth.py` §15 (shut = solid + blocks sight + nav
routes through; open passes both; a bars door is solid but see-through;
shutting breaks the LOS across it; the E-toggle flips the nearest).

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
> NARRATIVE §6, and the code implements it. It supersedes the
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

**The notebook is a running document** (2026-07). Everything the PI writes
down, evidence and note alike, lives in ONE continuous record read in the
order he wrote it, and nothing in it is ever reordered or rewritten. Two
consequences are load-bearing. His CONCLUSIONS are written once, at the moment
he reaches them, and stay: the wrong read he is canonically allowed to keep
(the robes are the ones who could stop this) sits on its page for the rest of
the run instead of silently editing itself into something less wrong, so a
player who reads the book start to finish watches a man's understanding change
and is never told so. And there is NO derived chronology: the PI writes dates
down as he finds them, and assembling this-then-this-then-this out of them is
the player's work, not the book's. Underneath, `evidence` and `notes` remain
two save lists because the King-gate counts one and must not count the other;
a `seq` stamp carries the order, and the split never reaches the player.

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
record still in the office files) — **no soft-lock, no looting a corpse
required.** This makes Hettie, Vane, and Toby the load-bearing locals,
and deepens three who were already central rather than inventing new
ones.

**The fallback is a fallback, not a second front door.** The paper opens
only once the person can no longer hand it over — Hettie dead, Vane dead
or **hollow** (his despair latch is reachable before the photograph ever
comes out, so it counts). While they still stand there, the drawer and
the spike refuse. Leave both paths live at once and the warm delivery
becomes optional set-dressing on a pickup, which is how the record shipped
for months: an `[E]` on a filing cabinet, liftable from a Sheriff who had
never been spoken to and whose answer to her photograph did not mention
the night he arrested her.

**A find should open a question.** The trail is walked, and each piece of
it is worth carrying back to the person it came from: the paper says what
was written down, and the person says what they saw. Vane is the worked
model at both ends — the photograph earns the booking slip, and the slip
opens `the_night`, his account of the arrest, which is a **statement**
(a note, never counted) and which leaves a second witness as a plain
stated fact. **The lead is never pointed at.** He says the man who
fetched him sits the square all day; he does not say Garrick, and no PI
line closes the gap. Connecting it is the player's, and that act is the
whole difference between investigating and collecting.

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

> The oblique view is the shipped camera; this section is its source of truth.

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
- **Scale: sprite-native (`TILT_ZOOM` 1.10).** Sprites draw at fixed pixel
  size (they do not scale with the camera), so the camera scale IS the
  body:world proportion. The tilt originally shipped zoomed out to 0.72 to
  show more world, which shrank rooms/doors/buildings against the bodies
  (the "world feels too small compared to the player" playtest verdict) and
  left most of the frame as void. 1.10 restores the drawn proportions and
  tightens the visible window; the sight cone (360 world px) still fits the
  frame with margin.
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
- **The void surround (the map's edge under tilt).** Off-map tiles are
  never rastered as floor (they used to paint as an endless "." default
  floor plain -- the checkered void around every interior). Instead the
  floor raster skips them and `_void_surround_pass` (`scenes/terrain.py`)
  composes the edge: a three-tile rim continues the nearest in-bounds
  ground under a deepening dark veil, then near-black -- the world's edge
  reads as ground falling away into the dark. Wrapped axes have no off-map;
  seamless neighbor strips paint real neighbor terrain OVER the fade where
  a `world_neighbors` entry exists (and the strip painter now fills true
  N/S/E/W edge strips, not just diagonal corners).
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
- **Judge a scene from all four facings with the TOOL**
  (`tools/capture_facings.py <scene> [--bright]`), never a hand-rolled
  capture. `_update_camera` sets the camera POSITION only and never its yaw,
  so an ad-hoc render silently produces the NORTH view four times; the tool
  sets the yaw itself and fails if the facings do not differ. Most tilt
  defects (a mirrored sign face, an undecorated flank, a swivelling card, a
  floating portal base) are invisible from the one angle you would have
  checked. See `VISION.md`.
- **Keep it asset-free.** No PNGs, no bake step. Solids are math. World
  lettering is drawn geometry too (`rendering/props.py` `_GLYPH` +
  `_draw_neon_word`), not a system font; `tests/conventions.py` freezes the
  remaining font uses by count so a new one fails the gate.
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
  period), and the bedroom desk **`desk_air`** (2026-07 quality sprint:
  the Arcadia keeping its hours around the spare room -- near-still air, a
  soft warm body, one distant floor settle; deliberately the plainest of
  the set). Every tone is mixed UNDER the caption voice blips (peaks
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

> BUILT and guarded end-to-end by `tests/stealth.py`. Tuning is the open
> item (`TODO.md` #5).

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

**A. Concealment cover (mobile, leaky)** -- corn, behind low props.
You can keep moving through it; it weakens LOS at range, but a close enemy
with LOS still builds suspicion (you cannot camp it next to a searcher);
moving fast rustles → a noise event. Corn scales score + gaze by
`SUS_CONCEAL_CORN`.

**DARKNESS IS NOT COVER** (maintainer ruling, 2026-07: "darkness shouldn't hide
you AT ALL"). There is no shadow-cover class and no `SUS_CONCEAL_DARK` in
config. Cover is something you put BETWEEN yourself and an eye -- corn, a hide,
a wall. An unlit spot is not that. **The dark belongs to Him:** it is the
condition His things need in order to open at all (§1), so hiding in it was
hiding inside the threat, and it read as a reward for turning the flashlight
off in exactly the rooms that should be worst. It cuts against the player only,
everywhere, indoors and out. Guarded, `tests/stealth.py` §11 + §18.

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
  runs (both banks of the river run and the bend, the Cistern shores, the
  Sump ledge).
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
  - **A stone down the DEAD WELL** (`WELL_ECHO_*`, `safe_path._town_square`):
    E at the well with a stone in pocket drops it; the knocks fall
    away, the shaft's rattle carries across the square (scout-tier,
    never a search-breaker), and **no bottom ever sounds** -- wordless
    by design; the missing landing is the beat, and the well stays the
    bottomless dread it is (NARRATIVE §5).
- **The under-bridge hide** (`Game._tick_bridge_knocks`,
  `scene._bridge_hide_px` / `_bridge_deck_px`): a rooted enclosed hide
  on the mud shelf under the downstream lip of the river bend's deck, the
  one crossing on the whole network. While you are tucked under it,
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

---

## 13. The lost spaces -- the in-between (TODO #26)

Three procedurally-generated, non-repeating dark fields
(`scenes/lost_space.py`; `lost_corn` / `lost_forest` / `lost_road`, plus the
`lost_space` back-compat alias onto corn). They are the backrooms
in-between: mostly EMPTY generated ground with sparse wrong things in it,
built around ONE hand-authored lit island. The full model, the fences, and
what is still open live in `TODO.md` #26; this section is the shipping
system and its code map.

### The shape of a field

A `LostSpace` is a `Scene` whose `floor` / `objects` are generator-backed
proxies (`_GenGrid` / `_GenRow`) over a hashed per-tile field, with a huge
finite `w`/`h` and the player spawned at CENTRE, so collision, sight, and
the tilt render all work unchanged and the map edge never enters the camera
window. `procedural = True` tells `tests/smoke.py` to skip flood-fill and
full-grid scans (an unbounded field would hang them); `nav_path` returns
None, so chasers run straight-line. `display_name` is the empty string: a
lost space is a place with no name you know, so the HUD corner that labels
every other scene stays blank here.

Each field has its own hand-authored **focal island** in the sea of
generation: corn is a crop circle around an abandoned camp fire, forest is a
pond with a fire on the near bank and lanterns across the water, road is a
filling-station lot under a neon pylon. Because the island is the only lit
thing, `LOST_SPACE_SCENES` carries a heavier gloom (150) than the other
dark scenes so it reads as a bright island in a black sea.

### The loop, end to end

1. **The mouth.** A scene opts a non-wrapping map edge in with
   `Scene.set_lost_edge(sides, lost_key)`, which fills `Scene.lost_edges`
   (`{side: lost_scene_key}`; None on every other scene, so an un-opted
   scene is exactly what it was). `Game._tick_lost_edge` runs from
   `update_player` right after the wrap clamp, because the map edge is
   where the clamp just refused to let them through.
2. **Light gates entry.** The edge only opens when the ambient is dark
   (`Game.scene_gloom() >= LOST_EDGE_GLOOM`) AND the spot itself is unlit
   (`Scene.lit_at` false, flashlight off). On the surface the gloom is the
   STORM, which climbs with the evidence count, so the lost spaces cost no
   new system: at ev0 the world is daylight and every bound is the
   invisible wall it always was, and only once understanding has darkened
   the world do its edges stop holding. A lit spot never opens, which makes
   the yard lights and a carried flame real protection.
   Pressing OUTWARD is required: you fall through by walking into the edge,
   never by loitering near it.
3. **The fall** writes the return anchor (`Game._lost_return` = the scene
   and a spot `LOST_EDGE_BACKOFF` tiles back INTO the world) and crosses via
   `cross_fold` -- the same one primitive as every other non-door
   traversal, so there is no fade and no sting. The biome you land in is
   the one the edge looked like.
4. **The island** is a lit dead end. While you stand in its glow there is
   no way out at all.
5. **The hunt.** Leave the glow and the exit light (a lantern) appears,
   held 6-20 tiles off and relocating out of your sight cone if you drift,
   so the way out is always findable and never free.
6. **Climbing out** spends the anchor and returns you to the yard a few
   strides in from the edge that took you. With no anchor (a direct load, a
   preview) the fields chain to each other instead, so they stay walkable
   on their own.

Guarded end to end by `tests/flow.py` §32b, including that a lit edge
refuses, a lit spot in a dark world refuses, and the return lands clear of
the mouth. **Shipping mouth today: the lodge yard's treeline (N/S).** The
yard's x axis is the torus and stays the torus -- `set_lost_edge` refuses a
wrapping edge outright, because a seam has no far side to fall off.

### The dark rearranges itself

`LostSpace._tick_reshuffle` moves the FIELD's scatter landmarks (never the
island, never a camp, never a light) every `_SHUFFLE_EVERY` seconds, at
most `_SHUFFLE_MAX` at a time, with a rotating cursor so it works its way
through the whole set rather than shuffling the same three forever. The
rule it enforces is the one the whole in-between runs on: **what the light
touches is TRUE; the dark is not.** A landmark is only moved when it is
outside your sight cone, unlit, and farther than `_SHUFFLE_NEAR`, and it
only lands somewhere that is also outside the cone, unlit, and not solid.
Only GEOMETRY lies -- a threat never blinks out this way.

### Who else is out there

Two kinds of light that are not the exit. The **occupied camp** is a
second, manned fire on a hashed bearing 26-36 tiles out, its crew spawned
on approach and released when you leave; it comes in three flavours (rest /
watch / work) so the camp you stumble into is not always the camp you
stumbled into last time. The **lamp-carriers** are cultists walking the
dark with a light in hand, and they exist precisely so a distant warm glow
is ambiguous: the way out, or someone coming. All of them are ordinary cult
NPCs, so the lost scenes sit in `CULTIST_SCENES` (with `cult_target = 0`,
so the field never musters a patrol of its own).

### The fields are WORDLESS

No narrator boxes, no notices, no case-notebook writes, no place name. The
dark and the hunted light are the entire text; a caption would explain away
the one beat the space exists to deliver. Enforced by
`tests/conventions.py` check 6.

---

## 14. The safe path -- the lit spine (TODO #26)

The middle of the three layers: **interior -> yard -> SAFE PATH <-> lost
spaces** (`scenes/safe_path.py`). A path scene is a wide paved road under
civic lamps, and it is the one part of the outdoors that does not lie. Its
arms go where they say, its geometry never rearranges, and nothing on the
asphalt moves when you look away. It is Garrick's standing advice made into
level geometry: *"Stay on the roads. People who go off the roads come out
wrong-side of where they went in."*

### The road is safe by its GEOMETRY, and the light is sparse

Walk the asphalt anywhere, at any hour, at any evidence count, and the world
cannot take you. That is the shape of the thing rather than the lamps: §13's
mouth can only open within `LOST_EDGE_BAND` of a MAP EDGE, an arm's end is an
EXIT (and `Game._tick_lost_edge` refuses on an exit tile), and a flank edge
has no asphalt anywhere near it. Step off the shoulder into the dark grass at
a flank and it lets go like any other verge. So the rule the player learns is
short and true: **the road carries you on, everything beside it does not.**

`tests/flow.py` §34 asserts this as a WALK -- every lane of every arm of
every path scene, driven end to end at ev3 with the lamps sparse, none of
which may fall out of the world.

The LAMPS are therefore not the safety, and there are far fewer than the
first cut's end-to-end coverage (which read like an airport runway). The
pattern is the maintainer's own, read off eight X's drawn on a capture of the
country lane and generalised in `_lamp_stations` so every road in the network
is lit the same way:

* **A junction is lit at its CORNERS, never at its centre.** A mast goes in
  each corner that lies between two arms, so the poles flank the mouth of the
  side road instead of standing in the crossing. A side with no arm has
  nothing to flank, so that shoulder takes one mast on the centreline, which
  closes the junction's fourth side without lighting a road that is not there.
* **Runs are lit in PAIRS**, facing each other across the road every
  `LAMP_STEP` (11) tiles out from the junction.
* **The ends of a run go dark.** The last pair falls where the stride falls
  and nothing is added to light the way out. A road fading into unlit distance
  is the point.

Masts sit on the OUTER edge of the shoulder, where the right-of-way ends and
the grass starts.

**Placement is ART-DIRECTED, not derived, where it matters.**
`build_path(..., lamps=((tx, ty), ...))` overrides the rhythm outright, and
`tools/screen_to_world.py` turns marks on a capture into that list. Lamp
positions are a thing the maintainer draws on a screenshot, and a derived
rhythm that looks reasonable is not the same as the one that was asked for --
the country lane's eight are the maintainer's own. A scene nobody has
directed keeps the default.

**No mast ever stands on the carriageway.** A lamp post in the middle of a
road is a thing you would swerve around in a car and walk into on foot. Every
station is pushed outward until its tile is not asphalt and dropped if it
cannot get clear; an explicit `lamps=` position on asphalt raises at build
time. `tests/flow.py` §34 fails on any mast in the road.

The light still does real work. It keeps the verge's dark off the asphalt at
the rim, and standing under a mast makes you VISIBLE to anything hunting
(stealth reads the same `Scene.lit_at`). Being ELECTRIC (`street_lamp` is in
`Scene._ELECTRIC_KINDS`) it goes out with the gensets, so a blackout takes
even that away. `street_lamp` (`rendering/props.py`) is the fixture: the same
cold mercury-vapor head the town hangs in its yards, up a tall galvanized
mast with a long gooseneck over the carriageway and a poured footing.

### Shapes: I, L and T

A path is built from ARMS, a subset of "nesw" around one junction at the
scene's centre. Two opposite arms is an **I** (a straight run), two adjacent
an **L** (the road turns), three a **T** (a junction). `build_path` lays the
surface, the lamps, the verge, the exits and the mouths from that alone, so a
new segment is a call rather than a hand-drawn grid.

Arms are painted in two passes -- every arm's gravel, then every arm's
asphalt on top -- so a junction comes out surfaced rather than quartered by
whichever arm was drawn last. The dashed centre lane stops at the junction
box, because a real crossroads has no line through it. `"Y"` is the N-S
centre lane and `"-"` the E-W one; they are two floor chars rather than one
neighbour-aware char because floor tiles are cached BY CHAR.

**Not too thin** (maintainer). Five tiles of asphalt inside a nine-tile
corridor with the shoulders. The road it replaced was a three-tile dirt strip
in a twelve-tile scene, which read as a corridor rather than a road you can
stand in the middle of.

### Every side is a mouth, and the biome is a rule

Every side of a path scene opens on a lost space, arms included: the grass
either side of an arm's end is as dark as a flank's. The road exit wins where
it is laid (`Game._tick_lost_edge` refuses on an exit tile, and a path's
exits span the whole corridor including both shoulders), so the rule the
player learns is the true one -- **the asphalt carries you on, everything
beside it lets go.**

WHICH lost space is derived, not authored: a flank opens on whatever its
verge is planted with (`_VERGE_LOST`: pine -> `lost_forest`, dead corn ->
`lost_corn`), and an arm's end opens on `lost_road`, because what you stepped
off there was a roadside. Hand-picking per scene is how you end up pushing
through a wall of corn and landing in a pine wood.

### The river

The river is the artery of the whole nightmare (NARRATIVE §2) and it has to
be visible from the path, so `build_path` takes a channel and keeps
`RIVER_BANK` tiles of open bank clear of verge growth either side of it --
at full density the trees close over the water and bury it. Water is `~`
floor over the see-over solid `x` (the lost-space pond precedent): it blocks
the body but not the sight cone, so the far bank shows across it.

Where a road arm crosses the channel it becomes a **bridge**: the deck is
paved across the whole corridor (a deck that stopped at the asphalt would
leave two dirt strips walking over open water) and `_rail_the_deck` runs a
timber parapet down both exposed lips. The rail is not trim -- under the tilt
a bridge without one is a brown patch of ground that happens to sit on water.

### The shipping network

Three segments east and north of town, one of each shape, closing a loop with
the two roads that were already there:

| scene | shape | arms | what it is |
|---|---|---|---|
| `country_lane` | **X** | W / E / N / S | the junction east of town: the gravel road west, the arrival road east, the river run north, and the standing corn south (the maze hangs off that arm). |
| `river_road` | **I** | S / N | a straight run north with the water off the east shoulder the whole way. Pine going black to the west, with the hidden trunk through to the burn clearing in it, and the Preacher's remains on the bank once he is doomed. |
| `river_bend` | **L** | S / E | the road turns east and crosses the river on the planks, with the mud shelf under the deck's downstream lip -- the network's one rooted hide, and the deck knocks overhead while you wait under it. |
| `gravel_road_north` | **X** | S / N / W / E | the country lane south, the backwoods north, the bend west, and the town's own streets east. Gravel-shouldered, pines to the kerb; keeps its boarded chop-target alcove. |

`arrival_road` is the one road that is NOT a `SafePath`, and deliberately so:
its endless-north illusion is built from a `_render_band` + a `_treadmill` +
a silent same-scene south loop, none of which a generic path builder models.
It took the cross-section and the lamp pattern instead, widened from 15 to 23
tiles so a nine-tile corridor fits, with every column derived from `ROAD_C`
and the shared constants rather than written as a literal. Its car, sign and
boards moved out onto the verge. (One flow guard had to change with it: the
band-is-landmark-free check tested for "no `d` in the row", which was a valid
proxy only while dirt appeared solely on the E-W crossing; it now tests the
two real landmarks, a full-width dirt row and the car footprint.)

---

## 15. The yards -- a household without a word (TODO #26)

The innermost of the three layers: **safe path -> YARD -> house**
(`scenes/yards.py`). A yard is one household's own ground, and its whole job
is to tell you who lives there and what they stopped doing, before you knock
and without anybody speaking. The seal was January 15 and it is April, so
whatever is standing in a back garden has been standing there three months.

**A YARD IS A SCENE.** One building in it, a road exit on one edge and that
building's door on the other side of the ground you cross. Not a dressed
patch of a bigger map: the walk from the road to somebody's door is the
layer, and it only exists if it is a place you travel to.
`lodge_yard` and `backwoods_cabin` were already this shape;
`yards.build_yard_scene` is that shape made general, and it hands back the
scene together with a `Yard` bound to the building so the caller dresses it
with the vocabulary below instead of counting tiles.

**Each building gets its OWN yard. They are never shared** -- a yard is a
household's ground, and sharing one flattens the thing the layer exists to
say.

**A yard is a PLACE, not a doorstep with a road attached.** The lot is large
enough that the walk from the gate to the door is a walk. It is still
deliberately SMALLER than the camera window: the black beyond the verge is
wanted, and it is what makes a yard read as a lit clearing with nothing
around it rather than as a room.

**The grass thickens where nobody walks.** Nothing has been mown in three
months and a lot's far corners go over first, so growth is seeded against
distance from the house and the worn track. What stays short is exactly the
ground the household actually crosses, which fills a big lot without unsaying
"kept": the read is a yard somebody keeps the middle of, not a lawn.

**A YARD IS NOT A SEAMLESS SCENE, and that is the shape of the layer.** A
scene in `SEAMLESS_WORLD_SCENES` draws its neighbour's floor into the void
past its own bounds (`terrain._draw_neighbor_strips`) and takes the overcast
skybox. A yard left in that set paints the adjoining street's asphalt straight
across its black rim, and an island whose edges show you the mainland is not
an island. So `YARD_SCENES` is subtracted from the seamless set: a yard is
outdoor (the storm darkens it, which is what lets its mouths open) but it gets
the VOID skybox, no neighbour bleed, and a real transition on the way in and
out. The streets stay seamless with each other, because a road does continue.

**And the OUTER RING carries growth too.** The scene ends before the camera
does and its edge dissolves into black -- which is wanted, and only works if
there is something out there to dissolve. An edge of bare grass stopping dead
reads as the end of a level; growth thinning into the dark reads as the world
going on without you. Every side gets it, so the four facings agree.

**EVERY EDGE THAT IS NOT THE ROAD IS A MOUTH.** A yard is the last lit ground
before the world stops caring: the way you came is the only way that stays
true, and walking off the back of somebody's lot in the dark drops you into
the in-between (§13). Which field you land in is derived from the VERGE you
pushed through -- `_VERGE_LOST`, the same rule the safe path's flanks use --
so it is never corn on this side and pine on the other. The mouth is still
light-gated, so at ev0 a yard's edge is the wall it has always been and it
only lets go once the storm has darkened the surface.

The chain is wired with ordinary parts, no new engine: the street is a
`SafePath` like any other and the yard hangs off one of its ARMS, and the
interior gets a door in a spare wall pointing at its yard. While the town map
still stood, that was a SECOND door and the old route kept working beside the
new one; when the map retired, the old street doors were bricked back into
the wall (`Scene.wall_up`) and the yard door is the only way in.

**The rule that makes it work is that yards DIFFER.** A vocabulary applied
evenly says the same thing about every house in town, which is exactly what
the layer exists not to do. So the module is thin and the authoring is per
household: a `Yard` knows the building's footprint, which face the door is
in, and the walkable tile just outside it, and offers the vocabulary against
that geometry. What any one yard actually says is written out in the scene.

### The vocabulary

A yard PICKS from this; it never gets all of it.

| piece | what it says | code |
|---|---|---|
| **the genset** | the fastest sentence in town, one per yard. Running: a warm work-bulb and a fuel can standing. Dead: a cold bulb and the can on its side. `running=False` also passes `broken`, which both light tables read to stop a fixture emitting, so the dark bulb and the dark ground can never disagree. | `Yard.genset` |
| **one interrupted task, and only one** | firewood half split with the axe still in the round; washing frozen on the line since winter; the delivery crates nobody came back for; a bed turned over in autumn and never planted. | `woodpile` / `washing` / `crates` / `bed` |
| **the mail** | deliveries stopped with the fold. Still stuffed with January's last one, or hanging open ever since. It sits on the seam where the yard meets the safe path. | `Yard.mailbox` |
| **an occupancy tell from the ROAD** | before you commit to the path: the track worn through the dead grass or grown over, a lit window, the genset's pool at night. | the scene's `_carve_track` + the `i` window tiles |
| **the car that will not start** | everyone drove in and nothing leaves (NARRATIVE §1). How it is PARKED is the characterisation: squared away by somebody who gave up early, or slewed at the road with the driver's door still open by somebody who tried and walked back (`door_open` on the `rust_*` kinds). | `base.dead_cars` |
| **a boundary that is not a wall** | wire on leaning posts, or an overgrown hedge line. It reads as an edge rather than a wall, and it ENCLOSES: a run laid across the front and nowhere else is a line, not a lot, so the boundary returns up the sides. | `Yard.fence` / `Yard.hedge` |
| **a GATE, and it is not a GAP** | the way in a household USES is a hung timber leaf (`Yard.fence(gate=...)`). The bay whose wire is DOWN (`gap=`) is a different object saying the opposite thing: a boundary pushed THROUGH, which is what a §13 mouth sits behind. Walking onto somebody's lot through their broken fence unsays everything a kept yard is saying with the rest of its pieces. | `yard_gate` / `yard_fence(gap=)` |
| **a step** | something between the ground and the door, so going in reads as arriving. | `Yard.step` |
| **the WRONG yard** | for a lot a newcomer took: the same vocabulary, subtly off. Crates squared away too neatly, a husk thing by the step, the door-motif chalked on the siding where the weather has nearly taken it. | `Yard.siding` + the cult dressing already on that lot |

**The minimum for any yard:** a boundary, a step, one interrupted task, and
one occupancy tell.

### The placement assert

Every piece goes through `Yard.put`, which refuses three tiles: the building
itself, the door, and the door's one approach. That is playtest error class
#8 (a prop across the way in) turned into a build-time failure instead of
something you find by rendering four facings and noticing. `Yard.siding` is
the one exception and has its own rule: a `_WALL_DECO` goes on the OPEN tile
the wall faces, never on the wall tile, because a wall decoration is drawn at
its own position and depth-sorted against the walls -- one placed on the wall
tile sits inside the wall's own volume and is painted over by it.

`terrain._wall_normal` reads which side the wall is on from the same
neighbours. It used to answer "the nearest scene EDGE", which is right for an
interior (a room IS the scene) and wrong for a building standing in an
outdoor map. Local geometry wins now, ranked by the same nearest-edge key, so
interiors resolve identically.

### The town's own streets

The path network grew to carry the yards. `gravel_road_north` was the only
shipped path with a side that had no road on it, so it went from a T to an X
and its east arm is the town turning; `store_row` is the first of the town's
streets, an L that runs off it to the store's gate. A street GROWS as
households land on it (an L becomes a T becomes an X), so one street ends up
serving several doors while every yard behind it stays its own.

### What each household says

These read against each other; the table is the whole town.

| yard | state | what it carries |
|---|---|---|
| church | kept, then stopped mid-sentence | genset running for a congregation that is under the ground; the axe still in the round; a hedge line into the burying ground |
| barn | **canon-empty** (NARRATIVE §3) | the congregation's washing still frozen on the line, the genset cold with the can over, the fence trodden through where the feet went |
| shop | occupied, lit | Hettie's genset running; the delivery crates broken open and never collected; a box she still walks out to that is always empty |
| schoolhouse | **canon-empty** | the spring bed turned over and never planted, the fence slack, the genset cold, the calendar by the door stopped on the same day |
| sheriff's office | occupied, failing | the ONE yard where the machine runs and the can beside it is already empty; his car slewed at the spine with the door still open |
| farmhouse | **the wrong yard** | crates squared too neatly, a husk thing by the step, the door-motif chalked on the siding, the genset cold because whoever is here does not need light |
| Toby's house | lived in, a child in it | the wood half split with the axe still in the block, because whose job that was went below; the one tended bed left in town |
| Royce's house | still fighting | genset running, can already empty, the car nosed out of town and shut, ready to be tried again |
| Mrs. Calder's house | kept, waiting | the supper table laid out in the open where the road can see it, two settings, a candle burned down, a chair over; her gate stands open |
| Garrick's house | given up on lights | genset cold, can over; the wood he was splitting when he stopped; a hedge line older than wire |
| Old Pell's | HELD, not interrupted | the one yard that did not stop mid-motion: it is kept exactly where he chose to stop it. Genset running, can full, and the calendar nailed on HIS siding at last. Seed crates roped and never opened, for a planting he is not going to do. The corn band is deeper here than anywhere on the string and comes right up to the lot, because he has not cut it and will not |

**BRIMLEY THE SCENE IS RETIRED.** The 60x60 town map is gone: the town is
this string of islands and nothing else. It was kept untouched, working, and
undeleted the whole time the yards were built beside it, and then retired in
one piece rather than eroded a building at a time -- so there was never a
half-town. What it carried went with it, each thing to the place that owns it:

| what Brimley held | where it lives now |
|---|---|
| the well, the barrow, the news rack, the dead payphone | **`store_row`** -- the crossing outside the store is THE SQUARE (`_town_square`), the one place in a town this size that everybody passes |
| the planked bridge, the under-deck hide, the river stones | **`river_bend`** (`_bridge_hide`) and **`river_road`** (`_river_stones`) |
| the Preacher's remains on the bank | **`river_road`** (`_preacher_bank`) -- he walked out of his church down the water after his flock, and this is the length of bank the road runs beside |
| the hidden trunk through to the burn clearing | **`river_road`** (`_clearing_doorway`), in the pine flank |
| the church door the bell calls hunters to | **`church_yard`** (`_bell_door`) |
| the cult's camp and its tend station | **`farm_yard`** (`_cult_camp`) -- the wrong yard, whose ground the newcomers already hold |
| the dead pickup and the gap under its bed | **`barn_yard`** -- one truck stayed where a crowd left in one direction |
| the roaming cult, the Watchers, the storm stage | every street and yard, by set membership (`CULTIST_SCENES`, `WATCHER_OPEN_SCENES`, `STORM_STAGE_SCENES`) |
| the four chorus locals and their reactive beats | their own houses (below) |
| the toroidal wrap and the cross-town fold road | **nothing** -- a street's arms end at exits, which is the opposite of a torus, and the wrap now belongs to the corn where it always meant something |

The buildings kept their yard doors and had their old street doors bricked
back into the wall (`Scene.wall_up`): a leaf onto a scene nobody can reach is
a door that does nothing, which reads as a broken building rather than a
changed world.

**PEOPLE LIVE IN HOUSES; YARDS ARE EMPTY OF THEM.** That is not an
oversight, it is the layer's whole premise: a yard tells you about a household
*without anybody there to say it*, and a resident standing in their own yard
does that job for it and makes the props redundant. So every resident is
inside their own building -- Hettie in the shop, Crane in the church, Vane in
his office, Toby in his house, Sable at the Arcadia desk, and Mrs. Calder,
Royce and Garrick in the three small houses below. The barn, the schoolhouse
and the farmhouse are empty inside AND out, which is the one case where the
yard and the interior say the same thing on purpose.

**Old Pell had nothing at all.** He loitered at the schoolhouse step and it
was never his, so the retirement left him nowhere to stand or live. He gets
the last arm of `lane_end`, and the dead end is the right address for the man
who stopped marking the days: past his gate the string has nothing left on
it. His calendar came with him off the schoolhouse wall.

**The one person in a yard is Hettie, and she is on her way back inside.**
`homebody` is somebody who is INSIDE and briefly out -- she steps onto the
shop step to sweep a step that does not get dirty, drops solid and stops
being drawn while she is behind the door, and the shop interior holds a
Hettie, so walking in finds her there. A store that is still open is a store
with its keeper visible at the door, and she is the only household in town
still performing that. It is the exception that proves the rule rather than a
hole in it: every other yard is empty of people, on purpose.

**A yard's `path_side` is the OPPOSITE of the street's exit side, always.**
The street declares which way it leaves to reach the yard and the yard declares
which edge its road is on, so the same seam is authored twice and the two
halves have to agree. When they do not, both scenes think the other is in the
same direction and the crossing reads as a sideways teleport. `farm_yard` shipped
that way until 2026-07 -- the one yard of the twelve that broke the pattern.
`tools/surface_map.py` finds the whole class by trying to lay the network on a
grid, and `--editor` makes it unauthorable by DERIVING the side from where a
scene sits instead of taking it as a typed value.

**The three small houses.** Mrs. Calder, Royce and Garrick stood on open
ground with no building at all. The three EMPTY buildings are the wrong three
to move them into: the schoolhouse and the barn are where the congregation
bedded down before they went below and the farmhouse is abandoned in its own
name (NARRATIVE §3/§4), and walking into that emptiness is a beat. So they
got new 5x4 houses with the FACADE door `l` -- solid, closed, no interior
modelled. The yard is what tells you about the household; the door only has
to be a door somebody comes out of.

---

## 16. The surfaces the words arrive on

Everything the player READS or leans into reaches them through one of four
surfaces. The words themselves are `DIALOGUE.md`'s; this is the machinery
that carries them, and the reason each channel exists.

### The three dialogue channels

`DialogueBox.show` routes every line, and which channel takes it is a design
decision, not a formatting one:

- **The modal band** (`ui/dialog.py`) survives ONLY for choices and for
  scripted beats with an `on_complete`. It stops the world, so it is spent
  only where a stop is the point.
- **Float speech** (`ui/float_speech.py`) carries a named NPC's line through
  the interact path, over the speaker's head. A person talking is a person in
  the room, so the room keeps running.
- **The narrator caption** (`ui/narration.py`) carries narrator and
  world-object text — examines, pickups, every `_evidence` beat — as a
  frameless lower-third while the WORLD KEEPS RUNNING. This is the channel the
  PI's interior voice uses, and the reason a caption can never be a modal
  stop: his thinking is not an event.

Two rules fall out of that: **E answers the world first** and only skims the
caption when nothing else takes the press (it is last in `try_interact`), and
replacing an active caption **fires its pending `on_complete` early** rather
than dropping it, so a beat chained behind a caption can never be lost to a
fast reader.

### The Casebook — one book, three ribbons

The old split Inventory (I) + Case Notebook (N) are ONE book
(`ui/journal_ui.py`, `JournalUI`), because a PI carries one case and the split
was a menu convention rather than a fiction:

- **Case** — the PI's RUNNING NOTEBOOK: everything he has written down, in the
  order he wrote it, paged. No index, no cards, nothing reordered or
  overwritten, so an early wrong read stays legible next to the later one (§9,
  "the notebook is a running document").
- **Tools** — axe, gun, keys, flashlight.
- **Papers** — Mara's journal + letter, the records, the cult testimony, the
  Mask.

Both `I` and `N` open the SAME book (N lands on Case, I on Tools; pressing the
ribbon you are already on closes it); left/right turns the tab, up/down walks
the index, Enter reads or takes in hand. `game.inv_ui` / `game.notebook_ui`
are aliases onto the one `game.journal_ui`. Note titles for save slugs live in
`ui/case_titles.py` (`humanise`), shared by the book AND the corner toast.

**Every write to the book is SEEN.** `_flash_notebook(name)` →
`_draw_notebook_toast` (`render_mixin`) is a small leaf the PI scribbles a beat
onto, NAMED with the humanised title, and it fires on every note and evidence
write. A silent write is a bug: the player has no other reliable tell that
something was recorded. The **floppy save toast** (`_draw_save_toast`) is its
sibling and is gated on the disk write actually succeeding, so it can never
lie about a failed save (§3, the save model).

**Conversation menus mark SPENT questions.** Every finished exchange sets its
asked flag; re-askable spent rows render dimmed in both menu presentations,
the cursor opens on the first fresh row, and a tableau menu swallows confirms
for its first `CONVO_MENU_GUARD` beat, so the E that skimmed the last caption
can never pick an option unread.

### The close-up tableaux

`systems/tableau_mixin.py` (`_open_desk_tableau` / `_tableau_input` /
`_draw_tableau`); the art is `ui/tableau.py`. A tableau is a modal close-up of
a prop with a menu that mutates it LIVE — take the gun off the desk, read the
case file — with the world frozen while it is up. The pilot is the bedroom
writing desk.

**The face-across-a-table talks ride the same frame, all six seats.**
`clerk_dialogue` / `sheriff_dialogue` / `hettie_dialogue` /
`preacher_dialogue` / `toby_dialogue` / `_mara_voice` each open their talk as a
tableau (the `_open_*_tableau` openers + `open_conversation(..., tableau=True)`);
the conversation's beats render as the caption and its menu as the option panel
(`_convo_tableau_input`). **The art reads save flags, so the close-up carries
what the talk earned** — Sable's photo/Invitation on the register; Vane's pose
reading his despair ledger, the given paper, the opened cabinet; Hettie's
door-glance idle, the tab leaving the spike, the traded paper; Crane's hands
folding or gripping the lectern on the press fork; Toby's corn-line watch, the
procession drawing, the brows the promise levels. The chorus still FLOATS its
talk (not a tableau) — the frame is for the people the case turns on.

**Mara is the last seat and carries the REVEAL.** The calling-out opens with
her masked and hooded, one of the congregation, the caption LISTING her as
"One of them" (`MARA_CONVO["name"]` is a callable), until the greet's
`("do", ...)` beat (`_mara_unmask`) pulls the carved mask off — the face from
the photograph, gone thin — and the listing turns to her name. Her captions
page on Escape (the reveal cannot be skipped), and the art reads `mara_lucid`
(raised bleeding palms) / `mara_named` (her fist on the PI's coat, the rank
stirring). The conversation engine's `("do", fn)` beats and callable `name`
exist for this; `load_scene_now` drops a stale tableau alongside the convo.

**Two non-conversation frames.** THE TALK is the tone inversion (`_cult_talk`
→ `_open_talk_tableau`): a scripted caption chain rather than a Conversation —
the grip close-up, the one reach-for-the-revolver choice, Escape pages instead
of aborting. THE PEDESTAL (`_open_altar_tableau`) is the OBJECT close-up of
His face on the stone: LIFT the Mask (keystone + temptation) or TEAR IT DOWN
(BREAK → `_play_ending("rite_broken")`), Escape backs out.

Every close-up carries a soundscape — `lean_in` on open plus a per-seat room
tone while it is up, and Mara's seat is silent on purpose. That layer is §11,
"The close-up tableaux (the sound pass)". The words are `DIALOGUE.md` Part B.
