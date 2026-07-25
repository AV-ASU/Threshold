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

**PROPS GET THE SAME RULE.** A kind is a thing you look at from every side
too, and "it read fine" almost always means "it read fine dead-on". Use
`tools/preview_props_sheet.py <kind> ...`, which **turntables by default** --
a row of four yaws per kind against a wall-height ruler. The two failures it
exists to catch:

- **A part placed off `cam.yaw` instead of the deco's own yaw.** It swings
  around the object as the view turns and vanishes from some headings. A
  mailbox whose flag is screen-relative is a grey lozenge on a stick from
  half the compass, and it looks perfect in a single dead-on shot.
- **A camera-facing card.** Its outline never changes as the row turns. Right
  for flame, a glow, or thin foliage; a bug for anything man-made (trap #1
  below).

Place identifying parts in WORLD space, off the deco's `yaw`. Use `draw_box`
for anything flat-sided and `draw_solid` only for a genuine body of
revolution -- `draw_solid` with equal radii is a drum, which is how a stoop
shipped looking like a butter-churn lid and a woodpile like a perforated
barrel.

**Build it from a REFERENCE, not from your own description.** Search for the
real object first and record what it is in `rendering/references.py` — real
dimensions, shape language, the tells. It is not a formality: "a tunnel with
an arched top and flat front, back and bottom, 23 x 11 x 13 inches" is what
turned a mailbox that had gone five revisions as a grey lozenge into one that
reads at a glance. `check_proportion` then compares the model against that
ratio in the gate, so a wrong shape fails before it is ever rendered.

**And record how tall it STANDS (`world_h`), not only its shape.**
`check_proportion` compares a model against itself, so it is blind to a prop
built perfectly at the wrong SIZE. The same mailbox later shipped 36 units
tall — a wall is 26, the player is 20 — holding a flawless 2.11 : 1 : 1.22,
because the legibility exaggeration baked into the model's `k` got applied a
second time to its post. From three of four facings it read as a bar on a
stick. `check_stature` now guards that: every reference records how tall the
thing stands in world units, judged against the player's 20 and the wall's
26. **A mount height is always in WORLD units, never the model's `k`** —
anything that says where a prop sits (a post, a sill, a tabletop) is
measured against the world, not against the prop.

**Judge it in a SCENE before you believe a colour.** The contact sheet's
neutral card flatters everything. Several materials were set by eye there
and turned out to be the palest objects in a Darkwood-dark yard — a stoop
that out-read the building it was attached to. `lift` compounds this: an
upward-facing face lands near `(1 + lift) x base`, and under a 55-degree
camera most of a low prop IS its top.

**A repeated shape is many OBJECTS, not one faked volume.** A woodpile is
logs, a fence is posts, a stack is things stacked. Every attempt to imply
that from a single mass failed at a different depth (a barrel with dots on
it, a table with coins beside it, ends floating off a raft), and each one
looked fine from the one angle it was tuned at. Build the unit, then place
the units, and **sort them back to front by `cam.depth()`** -- painting them
in loop order lets the further one cover the nearer one, which is what a
notch bitten out of a solid always means.

**For SHOWING the maintainer: one angle is enough.** When you share a scene,
send **one** representative PNG (`SendUserFile`), not the whole four-facing
sheet. The maintainer wants to see it, not audit it. Pick the clearest angle.

---

## IF IT ISN'T GOOD, REMAKE IT NOW

**When you look at a model or a design and think it is not good enough, do
not hand it over with a caveat. Remake it, in the same breath, until you
think it is good.** Not "it's proportionally correct but reads flat", not
"I'd rather judge it in situ", not "acceptable for now" -- those are all the
same move, which is shipping work you have already judged as poor and making
someone else say so.

This is not a licence to gold-plate. The bar is your own honest read: if you
would not defend it, it is not done. If you WOULD defend it and the
maintainer disagrees, that is a normal correction and costs one round.
Handing over something you already know is weak costs a round AND the trust
that your "this is done" means anything.

The economics are lopsided and worth being explicit about. Another iteration
now costs minutes, because everything is already loaded: the reference, the
preview, what you just tried, why it failed. The same iteration after a round
trip costs the maintainer's attention, a re-explanation, and your own
reconstruction of all that context. A prop that took five exchanges to get
right almost always took one exchange and four caveats that should have been
four more iterations.

The exception is a genuine fork -- two defensible directions where the choice
is a matter of taste, not quality. Then render both and ask. That is a real
question, not a caveat.

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
- **Any scene, all four facings — USE THE TOOL, don't hand-roll it:**

  ```bash
  python tools/capture_facings.py <scene_key> [--px X --py Y] [--bright]
  ```

  It writes the four PNGs plus a labelled contact sheet, and it **asserts the
  facings actually differ**, exiting nonzero if they don't. `--bright` drops
  the sight cone + film grade for clean geometry reading; without it you get
  the real player view.

  **Why the tool exists, and why hand-rolling this keeps failing:**
  `_update_camera` sets the camera POSITION only, **never its yaw**. The yaw is
  copied from `look.cam_yaw` inside `_update_look` (the live input loop), which
  no offline render path runs. Skip the explicit `camera.yaw = ...` and every
  "facing" renders at **yaw 0 — north, four times**. This has now shipped
  TWICE as "verified all four facings": once hiding an E/W-broken prop, once
  hiding a mirror-reversed neon sign and a field of black holes in the ground.
  Both times the sheet looked plausible and nobody noticed the panels were
  identical. That is exactly why the check is now machine-enforced instead of
  left to the eye: **a look pass that cannot fail is not a look pass.** If you
  must render a facing by hand, the contract is
  `look.body = look.aim = h` and `camera.yaw = look.cam_yaw = h + pi/2`
  (N `= -pi/2`, E `= 0`, S `= pi/2`, W `= pi`) — and then diff the frames.
- **Props in isolation** before placing: `tools/preview_props_sheet.py <kind>`
  (never place a kind by its name; render it first, `CLAUDE.md` SCENE-DRESSING).
- **One corner of a real scene, close up — the MIDDLE altitude:**

  ```bash
  python tools/inspect_spot.py <scene_key> --at TX,TY [--zoom 4] [--dark] [--ev N]
  ```

  Four facings centred on a tile you name, zoomed until you can actually see
  what is there. The dressing process asks for three altitudes and then the
  dark; the isolated sheet and the whole-scene capture covered the outer two
  and this middle one had no tool, so it kept being skipped. Both ways that
  fails are real: a woodpile signed off on a contact sheet at a magnification
  where proportion cannot be read, and six props called placed from a
  whole-scene shot too small to show they had rendered as **magenta
  placeholder squares**. `--dark` keeps the darkness/fog/grade the player
  actually meets, which is where a too-pale material gives itself away.

  Same trap as the yaw, one field over: `_update_camera` re-asserts
  `camera.scale = TILT_ZOOM` every call, so assigning `camera.scale` around a
  capture is silently undone before the draw. The tool moves `TILT_ZOOM` and
  then asserts the scale actually took.
- **Cutscenes / tableaux**: step the draw fn over `t` and save frames (as with
  the flashback and the close-up tableau previews).

## THE POINT

Every "that renders wrong" the maintainer has caught traces to someone
trusting the code instead of the frame. The cost of a capture is seconds. The
cost of guessing is a merged scene that reads broken. Always pay the seconds.
