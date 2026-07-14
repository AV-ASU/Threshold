# THRESHOLD — VISION (see it, don't guess it)

> The sixth canon doc, and the shortest. One rule, because it is the most
> repeated failure on this project: **do not guess how a scene looks from its
> code. Render it and LOOK.** The game is played through a fixed oblique tilt
> where a prop's tilt-set, a door's facing, an NPC's spawn tile, and a decal's
> warp all change what the player actually sees. Code that reads right renders
> wrong all the time. So we look.

---

## THE RULE

When you **change, dress, place, or judge how a scene looks or is laid out**,
you **render it and look at the result** before you call it done, and before
you tell the maintainer it is done. Not "the code adds a bedroll, so there is
a bedroll." Capture the frame; open the PNG; see it.

This binds scene/geometry/dressing/prop/portal/cutscene visual work. It does
**not** mean rendering four frames every time a scene is named in passing;
the trigger is *touching or evaluating the look*, not the mention.

**For your OWN verification: all four facings.** Under the tilt, most
geometry defects (an NPC on a door tile, furniture across a door, a prop that
swivels as a flat card, a portal with a floating base, a missing wall) hide on
the one facing you happened to check. View **N / E / S / W** before you trust
it (error class 8, `CLAUDE.md`). Then, when it matters, the same shot with the
**darkness / sight-gating ON** (players never see the brightened debug view).

**For SHOWING the maintainer: one angle is enough.** When you share a scene,
send **one** representative PNG (`SendUserFile`), not the whole four-facing
sheet. The maintainer wants to see it, not audit it. Pick the clearest angle.

---

## HOW TO RENDER

- **The fixed regression set** (`tools/capture_world.py --tag <t>`): boots the
  game, captures a small scene list at the default facing, writes
  `/tmp/world_<t>/<scene>.png`. Use `--diff a b` for the byte-identity gate on
  render refactors. It only covers a handful of scenes.
- **Any scene, any facing** (ad-hoc): boot the game headless
  (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`), `load_scene_now(key)`, set
  `player.x/y` + `player.facing` + `look.aim/head` to the facing, snap the
  camera (`_update_camera(snap=True)`), draw to an offscreen `Surface`
  (`draw_world`), and `pygame.image.save`. For CLEAN inspection stub
  `rendering.sight.visible_factor -> 1.0` (drop the cone) and
  `scenes.base.apply_grade -> None` (drop the film grade); for the REAL player
  view leave both on. A working template lives in the session scratchpad
  (`cap5.py`); keep one around.
- **Props in isolation** before placing: `tools/preview_props_sheet.py <kind>`
  (never place a kind by its name; render it first, `CLAUDE.md` SCENE-DRESSING).
- **Cutscenes / tableaux**: step the draw fn over `t` and save frames (as with
  the flashback and the close-up tableau previews).

## THE POINT

Every "that renders wrong" the maintainer has caught traces to someone
trusting the code instead of the frame. The cost of a capture is seconds. The
cost of guessing is a merged scene that reads broken. Always pay the seconds.
