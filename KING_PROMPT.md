# THRESHOLD — The Yellow King rework (session-start prompt)

> This seeds a working session to rebuild the **King in Yellow** from a thing
> that *spawns and catches* into a **free-roaming, attention-fed apex that hunts
> you across the world and folds in through portals when you push it too far.**
> The whole design below was settled in a long design conversation. Treat it as
> the intent, not gospel: the goal of *this* session's opening is to pressure-
> test it with me before a line of code changes.

---

## HOW TO START THIS SESSION (read this first, do not skip)

**Discuss before you build. Do not write any code until I sign off on a plan.**

1. **Orient.** Read this file, then skim the real systems it names:
   `systems/threat_mixin.py` (the King, visibility, watcher-curse, pursuit,
   death), `systems/config.py` (the `KING_*` / `VIS_*` / `WATCHER_*` / `FOLD_*`
   blocks + `SAFE_SCENES`), `rendering/king_unfold.py` (THE UNFOLDING +
   `lean`), `rendering/sight.py` (blind-spot vision), the portal/fold path
   (`PORTALS.md`, `rendering/folds.py`, `scenes/hidden_folds.py`,
   `tests/fold_pursuit.py`, `tools/preview_portal.py`), and the road/opening
   (`systems/game.py` `_draw_opening` + the loop car-tell, `scenes/forest_path.py`,
   `scenes/hidden_folds.py` `highway_walk`). Also re-read the King + threat
   sections of `CLAUDE.md`, `NARRATIVE.md`, and `CAMERA.md`.
2. **Then talk, do not act.** Come back and tell me, in your own words:
   - **what you think the King *is*** (the philosophy below, restated as you
     understand it),
   - **what you think the King should *do*** (your proposed behavior model and
     the order you'd build it in),
   - **the open decisions** you need me to settle (a short list, see the
     "Decisions to settle with me" section, plus anything you'd add).
3. **Wait for my feedback.** I will react, we will adjust, and only then do we
   plan implementation. The first message back to me is a *discussion*, not a
   diff and not an ExitPlanMode plan.

Process rules that always apply: verify file/line refs before editing (lines
drift); one edit at a time on a shifting file; run the full gate
(`python tests/run_all.py`) green before any commit; no em-dashes / no dashes
in any player-facing string (`CLAUDE.md` hard rule); develop on the branch I
give you.

---

## The philosophy (the *why* under the mechanics)

The King is not a monster you fight. He is a **verdict**. Internalize these or
the mechanics will land hollow:

- **He feeds on attention.** Worship and war are the same meal: the kneeling
  zealot and the charging hero both point their regard at him and feed him.
  The only thing that starves him is **indifference** — a god known and
  unworshipped, an evil left to rot. The survivable path is always to *deny him
  your visibility*, never to confront him.
- **Visibility is his attention.** Being seen is the danger. The meter is not a
  stealth gauge, it is *how much he is looking at you*.
- **Lucky, not omniscient.** He does not know where you are. He **hunts** and
  has to **find** you. When he loses you he searches; he does not teleport to
  your position. Keep the seam of chance: a vast thing that got lucky and was
  delighted, never clockwork inevitability.
- **The asymmetry is godhood.** *You can never reach him* (the road grows
  between you; he won't let you close). *He can always reach you* (the portal).
  Distance is his to spend, never yours. You step into his footprints; you
  never catch him.
- **Knowledge is the danger; agency is a trap.** Reaching the evidence gate is
  what arms him. The player's instinct to confront is the mistake.
- **Systemic, not scripted.** We are NOT authoring set-pieces. We build the
  *rules* whose collisions *produce* the dread, so every run authors its own.
  The designer guarantees the physics of fear; the player + the systems author
  the event. (The scenarios below are illustrations of the rulebook executing,
  not scenes to place by hand.)

---

## What the King should DO (the converged behavior model)

**One King.** Not a per-scene spawn. A single, persistent, world-positioned
entity with these states and rules:

1. **Horizon / loom (default).** He starts and idles at the **end of the road
   north** (the highway). Walk out there and you find him **full-bloom**,
   everting through 4D, **sky-huge**, **indifferent, not hunting**. The road
   *grows between you* (new asphalt resolving out of haze, never a catchable
   seam) so you can never close the distance. This is the safe look at the god,
   the thing that broke Royce, and the wall the Sign later gets you past
   (SPREAD setup). He must read as **alive and everting** here, never a static
   poster (drive `king_unfold` `lean`).

2. **Free-roam + attention.** He roams the world with a real position.
   **Visibility is his attention**; as it rises he turns toward you and begins
   to close. The **approach is sight-driven, not physical pathing** — walls do
   not stop a 4D thing; they are *sight-blockers*. Breaking line of sight /
   dropping below the dissolve threshold (~0.90, reuse existing) makes him lose
   the scent and drop from **charging -> searching**.

3. **Search (Mr. X / Alien Isolation).** Once he has you he hunts; when he
   loses you he **searches**, he does not vanish. **Soft de-escalation:** stay
   hidden long enough and search cools to a distant wander back toward the
   horizon. **Never a hard banish** (no cheap reset), but real relief so it is
   not exhausting or unfair. (Lean on the cult state-machine shape:
   scout -> chase -> search -> investigate, but slower and more dreadful.)

4. **The portal (the "you messed up bad" delivery).** Sustain **100% visibility
   for ~8 seconds** -> he tears a **portal** (the gold-yellow electric fold
   seam, the *same* motif as fold-pursuit; **NOT** the Threshold door, which
   keeps its own identity) connecting **your current room <-> the room the King
   is currently in.** He comes through to get you.
   - **Cancellable:** break visibility during the ~8s and the portal collapses
     unformed. The window is agency, not a death timer.
   - **Opens at a distance**, never on top of the player.
   - **It is also your escape.** You can flee back through it into the room he
     just vacated -> a genuine **juke**: bait him through, slip past, bolt back,
     strand him on the wrong side.
   - **It shuts the moment you cross.** One-time juke per rift, not a reusable
     hatch. That is what manufactures the distance (he must re-path the long
     way) and lets you safely lower visibility.

5. **Underground.** The visibility economy "breaks down" below, so you **cannot
   trigger a fresh portal underground** -> the deep is a refuge *from the
   summon* (this is the incentive to descend). **But** a King already hot when
   you descend **follows via the fold-seam** (the well / Deep Stair) — he does
   **not** climb ladders, he **manipulates space / folds down**. Conditional:
   shake him to search-and-evade first = descend clean; descend while he is hot
   = you drag the god down with you.

6. **Tells of the approach (reuse what exists).** As he closes: **ashfall
   intensifies**, the **screen thumps red** (vignette pulse), his **shifting
   maw bleeds into the player's periphery** (via `sight.py`), audio swells.

7. **Portals as windows.** A rift **shows the room on its other side** (a second
   view through the camera seam) **desaturating to gray** at the threshold
   (liminal). Converge it with the **sight system** so they hold hands: a rift
   is a sanctioned hole in blind-spot vision. You see the King **looming
   through it before he comes**, and you see *where you are about to flee.* The
   gray reinforces the theme: the spaces *between* are colorless; the room you
   stand in is where the color lives.

8. **Safe areas stay sacred.** A persistent hunter is only fair if there is
   guaranteed relief. Keep `SAFE_SCENES` refuges; the deep already has some
   (e.g. `maras_room`, guarded in `tests/flow.py`).

**A scene the rulebook should be able to PRODUCE (not a script):** 3rd evidence
collected, crossing Brimley, the cult fixes on you and you never break their
sight, so visibility pins at 100%. A rift tears open elsewhere in town and the
King closes; ashfall thickens, the screen thumps red, his maw leaks into the
corner of your eye. You duck behind a house into the corn, barely scrape under
90%, and wait in the stalks hoping his search drifts away instead of onto you.

---

## TODO: the being-seen / exposure UI (legibility milestone, deliberately stressful)

A second HUD reading that **splits the rate from the state**, so the player can
read their exposure moment to moment. Settled as the best option of a UI
discussion; the buzz of it is a *feature* (a little extra mental load = tension).

- **Two layers, faucet + bathtub.** Keep the existing **visibility** meter as
  the *state* (accumulated, drives the gate/floor). Add a **being-seen** reading
  as the *rate* (instantaneous: how hard eyes are on you *this second*). Make the
  being-seen reading visibly *drive* visibility: eyes on you -> level climbs;
  being-seen at 0 -> the drain opens and visibility creeps down. That immediate
  cause/effect is what teaches "unseen is good" in real time (a single meter
  teaches it far too slowly).
- **Notched, ~10 units.** Discrete ticks so the player can map *units to gaze
  sources* (a cultist, open ground, the flashlight each add a known amount) and
  do mental stealth math. Supports the legibility pillar of the hunt loop.
- **Cult-legible, King-felt (the key call).** The bar reads **human/cult gaze
  precisely** (a fair, solvable stealth puzzle). The **King's** contribution is
  rendered **diegetically, never as a clean number** (the red flash, ashfall,
  the maw in the periphery, a quickening pulse). A crisp "the King sees you 7/10"
  would drain his dread; keep the cosmic threat *felt*, the mundane one *read*.
- **Bias the feedback to screen-space, not a billboard you stare at.** Lean on
  edge vignette / a red pulse / a heartbeat that quickens with exposure so eyes
  stay on the *world*; keep the notched bar small and peripheral as the precise
  reference. Horror wants the dashboard quiet.
- **It teaches the hidden floor for free.** When exposure hits 0 but visibility
  refuses to drain below the evidence floor (`KING_HUNT_DROP_VIS` 0.90 at full
  evidence), the player *sees* "knowing dooms you" without a tutorial. Make that
  stuck-at-the-floor state legible (the bar pins + flashes).
- **Cheap.** This mostly **surfaces the per-frame gaze sum that already drives
  visibility** (`_tick_visibility` / the gaze count in `threat_mixin`), not a new
  system. Wire it into `_draw_hud` (`render_mixin`).

---

## TODO: portal rendering — camera-respecting black-gold seams (visual-fidelity pass)

Sharpens behaviour item 7 (portals as windows). This is the *look* pass, done
**after** the portal mechanic works (M2+), like M1 deferred the idle-King
"road-grows" visual. Not gold-plating: a flat portal is the worst offender of
the tilt's "sticker on the floor" failure mode (CAMERA.md / HANDCRAFT_BACKLOG),
because the one object that must read as a hole in space is the one flatness
most contradicts.

- **Respect the tilt.** The rift *and the view through it* project through
  `camera.project` like everything else and depth-sort into the world. Never a
  flat screen-space decal or a top-down sticker. It should read as a real
  oriented opening in 3D space.
- **What's behind respects the camera too (the hard part).** Use the *same*
  projection so the far side reads as a coherent continuation of space, not a
  pasted photo. **Cheap path (do first):** a stylised black-gold void + the King
  silhouette at correct perspective/scale + the gray liminal falloff. **Expensive
  path (only if perf allows):** a real clipped second-scene render. It is CPU-side
  surface clipping in pygame, so watch the per-frame cost.
- **Black-gold lighting that uses the pseudo-3D.** The seam is a *light in the
  scene*, not an overlay: a gold floor-pool projected at z=0, an additive rim on
  the neighbouring solids/billboards, a glow on the player as they near it. Hook
  the existing light-pool / `occlusion` / `solids` pass; a localised faked glow
  that projects correctly is fine (do not build real GI).
- **Palette = identity.** Black + gold electric is the *portal/fold* signature
  the player learns to read. Keep it OFF the Threshold door (its own thing).
- Tech: `rendering/folds.py` + `camera.py` (the one projection seam) +
  `solids.py` / `occlusion.py`; preview headless (`tools/preview_portal.py`)
  before committing.

---

## Decisions to settle with me (raise these in the opening discussion)

1. **Feel:** slow-inevitability (watch him cross) vs. acute portal-panic ("it's
   tearing open, RUN"). My lean is the synthesis (horizon = dread, portal =
   strike), but name it on purpose.
2. **Global relocation:** the rift connects to *wherever he is*, so fleeing it
   can fling you across the map (surface <-> underground). Feature (chaotic
   fold-escape that costs descent progress) or bounded (same depth band)?
3. **Rope-snap / point of no return:** persistent portal-exits may rework the
   Deep-Stair rope snap (fresh canon, `GAME_CHANGES` #7). My lean: keep the
   commitment, change the mechanism — portals only ever go *lateral or deeper*,
   never back *up* to safety, so one-way-down dread survives.
3b. **Director layer:** emergence does not respect pacing. Do we add a light
   director (cf. Alien Isolation / Left 4 Dead) that nudges roam + rift odds
   toward a tension curve (escalate after safe-too-long, relief after a
   near-miss) without scripting events?
4. **Where does the highway-King live** spatially, and how does "the road grows
   between you" get built (reuse `_draw_opening` road tech?).

---

## Honest constraints + sequencing (do not let the elegance hide the cost)

- This is the **biggest systems lift in the game** and it touches the **most
  important and most-tested** code (`threat_mixin`, the King gate,
  `fold_pursuit`). The **portal is cheap and spectacular; the free-roaming
  cross-scene stalker AI underneath it is the mountain.**
- **The search-AI *feel* is the make-or-break, and it only proves out against a
  human playing it.** Systemic design = tuning the *distribution* of emergent
  outcomes so the good moments are common and jank/anticlimax is rare; you
  cannot see that distribution from inside your own head.
- **Sequencing:** build and validate the **room-to-room hunt loop first** (does
  hide-and-evade feel tense and fair?), *then* add the portal on top. Build the
  stalker on a foundation a real player has confirmed, not a hypothesis.
- **Guard two pillars:** **legibility** (the player can read the rules and their
  situation) and **fairness** (a death feels earned by a choice, never by jank
  or geometry-stuck).

## Tech to reuse (do not reinvent)

Portal/fold path (`folds.py`, fold-pursuit, `PORTALS.md`), `king_unfold.py`
(`lean` locomotion), `sight.py` (blind-spot + periphery), ashfall + the
vignette pulse, the visibility model + ~0.90 dissolve threshold
(`threat_mixin` / `config`), the cult state machine, `SAFE_SCENES`, and the
opening-drive road tech for the highway.

## Canon guardrails

King feeds on attention; lucky-not-omniscient; the lure chain is felt, never
stated; no day/night cycle; `SAFE_SCENES` exist; **the Threshold door is NOT
the gold-yellow portal aesthetic** (only the fold seams are); no em-dashes / no
dashes in player-facing text. Check `GAME_CHANGES.md` before touching the fork,
the Deep Stair, or the keystone.

## Verification

`python tests/run_all.py` (smoke + flow + fold_pursuit + render_smoke) green
before every commit; add a `tests/flow.py` guard when a King-rule locks; for
visuals, preview headlessly to PNG before committing (`tools/preview_*`).
