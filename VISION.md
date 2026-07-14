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

## TWO TILT TRAPS TO CATCH

**1. Camera-facing is the EXCEPTION, not the norm.** A sprite that looks the
**same from all four cardinal directions** is "facing the camera" (a billboard
/ standee that swivels to the view). A few things genuinely read better that
way and should stay so: **fire / flame, a glow, and thin organic things**
(grass, a wisp) are easier and truer as a camera-facing card. Those are
**rare**. For anything **man-made or solid**, camera-facing is a bug: it reads
as a flat sticker that pivots to look at you. So the rule: **anything that
faces the camera must carry a stated REASON why** (a comment, or an obvious
tilt-set choice like fire). If a camera-facing object has **no good reason**,
it is wrong and gets updated to fit the tilt: a real `SOLID_PROPS` /
`FURNITURE` volume for a man-made thing, or a `_WALL_DECO` for a hung detail
(the tilt dispatch map in `CLAUDE.md`). When you render a scene, actively ask
of each swiveling card: *should this really face the camera?*

**2. Wall detail can HIDE at the cardinal facings (check +/- 45 degrees, on
EVERY wall).** Details attached to a wall (`_WALL_DECO`, hung things, window
and door trim, anything on a wall face) go **edge-on, occluded, or
depth-sorted away** at a given camera angle, so a pure N/E/S/W sweep can miss
them entirely and you will think a wall is bare when it is dressed. This is
**not just the east/west walls** (the obvious edge-on case). It is **every
wall, N/E/S/W alike**: a near wall can occlude its own face, a far wall's
detail can sink behind the wall mass, and any hung thing can be swallowed by
the depth sort from some facings and clear from others. Do **not** assume a
wall is safe because you put its detail on the "camera-facing" north wall (it
isn't) or because one facing looked fine. So the rule: **whenever you dress a
wall, render +/- 45 degrees off each facing for that wall** (the same
head-turn arc the player has), and do it for every wall you touched, not only
the side ones. Look at what sits on the walls from the angles that actually
reveal each wall face, not just dead-on.

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
