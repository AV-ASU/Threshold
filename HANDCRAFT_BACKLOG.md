# HANDCRAFT BACKLOG — sprites/art that don't fit the 3D tilt yet

> The oblique tilt camera is the default. Under it, things should render as
> **volumetric solids** (`rendering/furniture.py`, `rendering/props.py`) or
> **stood-up billboards/standees** (`scenes/base.py` `_tilt_standee`,
> `_TILT_BILLBOARD_CHARS`). Anything still drawn **flat top-down** reads as a
> *stain on the floor* under tilt. This is the slow-burn list to hand-craft.
>
> **What already has 3D:** the 14 `FURNITURE` kinds (`furniture.py`: table,
> chair, bed, bookshelf, shelf, wardrobe, stove, fireplace, counter, firewood,
> crate, barrel, cot, bone_rack, pew), the 4 `SOLID_PROPS` (`props.py`: well,
> pillar, cistern_basin, grain_heap), wall/door/window **tiles**, and
> tree/cornstalk **tiles** (billboarded). Floor decals (rug, bloodstain, gore,
> yellow_sign, bloody_handprint, bloody_pile) are *intentionally* flat. Pure
> particles (smoke, mist, mote, wisp, leaves, flock) are intentionally flat.
>
> Everything below is a **`Decoration` kind** (`entities/decoration.py`) with
> **no** solid/billboard treatment — flat under tilt.

## Tier 1 — high-visibility, frequently placed

### Kitchen / dining (the called-out group)
- `place_setting` — plate/cutlery drawn top-down (brimley, house interiors)
- `calendar` — wall calendar drawn as a flat grid (should hang on a wall)
- `clock` — wall clock face, flat circle+hands (should hang on a wall)
- `radio` / `wrong_radio` — flat speaker grille + dial
- `cauldron`, `bowl` — circular rims seen from straight above

### Wall decoration / signage (the called-out group)
- `mirror` — flat disc; should be a vertical wall billboard
- `photo` / `wrong_photo`, `polaroid_wall` — flat frames on the wall
- `missing_flyer` — flat poster (very common: brimley, houses)
- `banner`, `apology_wall`, `symbol` — flat cloth / wall-scrawl / painted mark
- `town_sign`, `steeple` — stand tall in the world but drawn flat

### Standing furniture missing a solid
- `chest` — top-down box; belongs in `FURNITURE` (it's a real volume)
- `small_chair`, `overturned_chair` — chair variants not in `FURNITURE`
- mounts: `buck_head`, `antler_rack`, `mounted_fish`, `wrong_taxidermy` — wall trophies drawn flat

### Interactive / readable
- `terminal`, `computer` — functional, flat screens
- `rope`, `cellar_hatch` — flat coil / hatch

## Tier 2 — outdoor & atmospheric
- Vehicles/roadside: `player_car`, `pickup_truck`, `gas_pump`, `payphone`,
  `flagpole` — prominent, all flat (a stood-up billboard would fix most)
- Graveyard/ritual: `headstone`, `pedestal`, `wheelbarrow`, `stalk_marker`,
  `corn_altar`, `corn_doll`, `doll`, `bush`, `creepy_tree`, `tall_grass`
- Birds: `crow`, `dead_crow`

## Tier 3 — ground marks (lie flat — mostly fine, but listed)
`binding_sigil`, `etched_char`, `phantom_mark`, `claw_marks`, `mud_footprint`,
`cobweb` — flat evidence/marks. These reading flat is *acceptable* (they're on
surfaces), but they overlap with category 2 below.

---

## 2. Ground-indication gaps (pickups float / no footprint)

Items are drawn as small bobbing boxes (`systems/game.py` `_draw_item`,
~line 3760) with **no ground shadow/decal**, so under tilt a pickup reads as
floating with no contact with the floor — and **notes/evidence are easy to
miss**.

- **Fix shape:** give every pickup a small ground-contact shadow/marker
  (a faint dark ellipse + maybe a glint) projected at z=0 under the bobbing
  icon, like a "something is here" decal. Cheap and uniform.
- Affected: all inventory pickups (key, letter, journal, cross, robe, axe,
  flashlight, ammo) and every scene-placed note/evidence. `item_drop`
  (`decoration.py`) gets a tiny box but **no** shadow.

---

## 3. The river (Brimley)

- **Water tile `~`** drawn in `scenes/base.py` (~line 715): a flat uniform
  `(26,40,40)` tint with scrolling ripple lines + algae specks. **No depth.**
  - **Want:** darker, organic patches in the *middle* of the channel that
    read as depth/current/silt — layered darker blobs (irregular, drifting),
    not a flat tint. River geometry/bends: `scenes/brimley.py` (~line 96).
- **The `drowned_body`** decoration the dev dislikes:
  `scenes/brimley.py` ~line 446 places it at tile (33,45) — deep water south
  of the bridge; art in `entities/decoration.py` (`drowned_body`, flat figure
  bobbing on the surface).
  - **Want:** either rework it as a submerged/partly-sunk volume (project
    lower, fade, ripple-distort) or reconsider whether it stays at all.

---

## 3b. Player / weapons

- **Held axe idle pose** — the revolver now draws *in hand* whenever it's the
  active weapon (`draw_revolver_held`), but the axe still only appears during
  its swing (`draw_axe_swing`); idle, the player looks unarmed with the axe
  equipped. Add a `draw_axe_held` to match (so the equipped weapon always
  reads). `rendering/sprites.py`.
- **Player sprite under tilt** — `draw_player_sprite` has 2.5D head-turn views
  (`view_from_facing`); double-check the held-weapon offset reads at every
  camera yaw (the gun is drawn in screen space off `facing`, so it should, but
  eyeball it).

## 4. General 3D-misfit / polish candidates (lower urgency)

These *do* render under tilt but the procedural art is simplistic at an angle
and would benefit from handcraft: the `fireplace`/`stove` tile sprites, the
`bed` blanket folds, `shelf` book layout, `counter` butcher detail. Not 3D
*bugs* — just flat-feeling detail.

---

## Suggested order
1. The river (single dramatic, player-faces-it centerpiece).
2. Pickup ground shadows (one fix, helps every note/evidence everywhere).
3. Kitchen + wall-decor billboards (Tier 1) — most rooms read furnished.
4. Vehicles/roadside billboards (Tier 2) — the town exterior.
5. Everything else as time allows.

> Mechanism reminder when implementing: add a kind to `FURNITURE`/`SOLID_PROPS`
> for a real volume, or to the billboard/standee path for a flat-card-stood-up.
> Floor-bound marks can stay in `_FLOOR_DECAL_KINDS`. Verify with a tilt
> capture (`/tmp/cap_*.py` pattern) before/after.
