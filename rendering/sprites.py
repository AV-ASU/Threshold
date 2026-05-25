"""Character sprites: NPCs, enemies, the player."""
import math
import random
import pygame
import pygame.gfxdraw
from constants import C_BLACK

def draw_npc_sprite(surf, x, y, kind, facing, blink=False, gaze=False,
                    birth=None, gait=None):
    """`blink=True` suppresses eye dots for NPC kinds that have human
    eyes (mom/kid/bandit/policeman). Used by Game.draw to make a single
    NPC's eyes vanish for a single frame -- a subliminal wrongness.
    `gaze=True` lights the watcher's eyes (sees the player). Watchers
    only.
    while the player stands still."""
    if kind == "_invisible":
        return
    if kind == "mom":
        # red dress (desaturated, slightly dirtied), dark bun, apron with
        # a faint smudge along the hem so she doesn't read as a fairytale
        # housewife. Eyes sit in shallow hollows so she always looks a
        # little exhausted; on `blink` the dots become 2x2 voids rather
        # than disappearing -- a frame where her face is wrong.
        pygame.draw.rect(surf, (150, 56, 70), (x - 9, y - 2, 18, 18))
        pygame.draw.rect(surf, (200, 196, 188), (x - 6, y + 2, 12, 14))  # apron
        pygame.draw.rect(surf, (130, 96, 90), (x - 6, y + 14, 12, 2))    # apron hem stain
        pygame.draw.circle(surf, (228, 198, 168), (x, y - 12), 7)
        pygame.draw.circle(surf, (50, 32, 24), (x - 6, y - 18), 4)  # hair
        pygame.draw.circle(surf, (50, 32, 24), (x + 6, y - 18), 4)
        # Sunken eye hollows (skin-shadow band under the brow)
        pygame.draw.line(surf, (170, 130, 110), (x - 4, y - 11), (x - 1, y - 11), 1)
        pygame.draw.line(surf, (170, 130, 110), (x + 1, y - 11), (x + 4, y - 11), 1)
        if blink:
            # Void frame: oversized black holes where the eyes were.
            pygame.draw.rect(surf, (4, 2, 4), (x - 3, y - 13, 2, 2))
            pygame.draw.rect(surf, (4, 2, 4), (x + 1, y - 13, 2, 2))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 12), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 12), 1)
            # Tiny wet glint above each pupil
            try:
                surf.set_at((x - 3, y - 13), (240, 240, 250))
                surf.set_at((x + 1, y - 13), (240, 240, 250))
            except (IndexError, ValueError):
                pass
    elif kind == "old":
        # Brown coat, hat, beard, cane. The face slot under the hat brim
        # is darkened into a shadow band so two faint pinprick eyes glint
        # from inside the shadow rather than reading as plain face. Beard
        # is now off-white / ash-yellow so he reads as kept-too-long.
        pygame.draw.rect(surf, (78, 60, 42), (x - 9, y - 2, 18, 18))
        pygame.draw.circle(surf, (200, 178, 158), (x, y - 12), 7)
        pygame.draw.rect(surf, (200, 196, 180), (x - 7, y - 5, 14, 6))  # beard (yellowed)
        pygame.draw.rect(surf, (30, 20, 12), (x - 9, y - 22, 18, 4))   # hat brim
        pygame.draw.rect(surf, (30, 20, 12), (x - 6, y - 28, 12, 7))   # crown
        # Hat-brim shadow band across the eyes
        pygame.draw.rect(surf, (60, 40, 30), (x - 6, y - 14, 12, 3))
        # Pinprick eyes inside the shadow
        if not blink:
            pygame.draw.circle(surf, (210, 200, 160), (x - 2, y - 13), 1)
            pygame.draw.circle(surf, (210, 200, 160), (x + 2, y - 13), 1)
        pygame.draw.line(surf, (90, 60, 30), (x + 10, y - 4), (x + 10, y + 14), 2)  # cane
    elif kind == "shopkeep":
        # Blue apron, bald top, glasses. Lenses are now FILLED black
        # instead of outlined -- you can't see his eyes through them, the
        # two black rectangles ARE the eye-read. Subtle and uncanny: every
        # time he turns toward you, you fail to find his gaze.
        pygame.draw.rect(surf, (54, 70, 104), (x - 9, y - 2, 18, 18))
        pygame.draw.rect(surf, (200, 196, 190), (x - 6, y, 12, 16))  # apron
        pygame.draw.circle(surf, (200, 170, 140), (x, y - 12), 7)
        pygame.draw.arc(surf, (40, 28, 22), (x - 8, y - 18, 16, 8), 0, math.pi, 1)  # hair ring
        # Glasses frames + filled black lenses (no eyes visible)
        pygame.draw.rect(surf, (10, 10, 14), (x - 4, y - 13, 3, 2))     # glasses L lens
        pygame.draw.rect(surf, (10, 10, 14), (x + 1, y - 13, 3, 2))     # glasses R lens
        pygame.draw.line(surf, (40, 40, 50), (x - 1, y - 12), (x + 1, y - 12), 1)  # bridge
        # A faint reflection-line on each lens so they read as glass,
        # not eyeholes -- but the reflection is on the WRONG side of
        # each lens (both reflect from the right), which is impossible
        # if the light source is overhead and singular.
        try:
            surf.set_at((x - 2, y - 13), (140, 150, 160))
            surf.set_at((x + 3, y - 13), (140, 150, 160))
        except (IndexError, ValueError):
            pass
    elif kind == "kid":
        # Desaturated yellow tunic; the original bright primary made the
        # kid read as cheerful, which fights the "trailing creep" use.
        # Hair hangs lower over the brow; the cheek dots used to be
        # freckles, now they sit slightly low and asymmetric so they
        # read as old tear-streaks when you look twice.
        pygame.draw.rect(surf, (172, 156, 70), (x - 7, y, 14, 14))
        pygame.draw.circle(surf, (228, 196, 168), (x, y - 8), 6)
        pygame.draw.rect(surf, (80, 50, 30), (x - 7, y - 13, 14, 5))
        # Long fringe -- a fringe-band lower over the eyes than the hair
        # cap, so the kid always looks like he's peering up through it.
        pygame.draw.rect(surf, (80, 50, 30), (x - 6, y - 9, 12, 2))
        # Sunken eye hollows
        pygame.draw.line(surf, (170, 130, 100), (x - 4, y - 7), (x - 1, y - 7), 1)
        pygame.draw.line(surf, (170, 130, 100), (x + 1, y - 7), (x + 4, y - 7), 1)
        if blink:
            # Void blink: oversized 3x2 black holes that overflow the
            # eye area -- bigger than the head ought to allow.
            pygame.draw.rect(surf, (2, 0, 4), (x - 4, y - 9, 3, 3))
            pygame.draw.rect(surf, (2, 0, 4), (x + 1, y - 9, 3, 3))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 8), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 8), 1)
            try:
                surf.set_at((x - 3, y - 9), (240, 240, 250))
                surf.set_at((x + 1, y - 9), (240, 240, 250))
            except (IndexError, ValueError):
                pass
        # Cheek marks -- low and asymmetric so the eye reads them as
        # old tear tracks before settling on "freckles".
        pygame.draw.circle(surf, (150, 90, 80), (x - 4, y - 5), 1)
        pygame.draw.circle(surf, (140, 84, 76), (x + 5, y - 4), 1)
    elif kind == "bandit":
        # THRESHOLD: re-skinned as a hooded cultist. Coarse undyed-
        # wool robe (dirty cream) over a dark inner shirt; deep hood
        # casts a shadow across the eyes; faint ash on the hem from
        # the cauldron fire. Used by the patrol_cultist NPCs that
        # appear at higher Pursuer proximity.
        robe       = (170, 156, 130)     # undyed wool
        robe_dark  = (110, 100, 84)      # shadow seam
        inner      = (40, 36, 40)        # shirt under the robe
        skin_dim   = (180, 156, 130)     # face in hood-shadow
        ash        = (60, 54, 50)        # scorched hem
        # Body / robe
        pygame.draw.rect(surf, robe, (x - 9, y - 4, 18, 20))
        pygame.draw.rect(surf, robe_dark, (x - 9, y - 4, 18, 20), 1)
        # Vertical seam
        pygame.draw.line(surf, robe_dark, (x, y - 4), (x, y + 14), 1)
        # Inner shirt peek at the collar
        pygame.draw.rect(surf, inner, (x - 4, y - 4, 8, 3))
        # Head (in hood shadow)
        pygame.draw.circle(surf, skin_dim, (x, y - 12), 7)
        # Hood drape over the head and shoulders
        pygame.draw.rect(surf, robe, (x - 10, y - 22, 20, 10))
        pygame.draw.rect(surf, robe_dark, (x - 10, y - 22, 20, 10), 1)
        # Hood shadow across the eyes -- pure-black band, slightly
        # deeper than skin. The shadow now extends a row lower so it
        # darkens the cheekbones too, killing any "person" read.
        pygame.draw.rect(surf, (4, 2, 6), (x - 7, y - 14, 14, 5))
        if blink:
            # Void blink: yellow pinpricks vanish and a faint pale jaw
            # shape ghosts through the shadow -- the suggestion of teeth
            # / skull where a face ought to be. The mouth-row sits below
            # the shadow band, never visible at rest.
            pygame.draw.line(surf, (180, 168, 152), (x - 4, y - 9), (x + 4, y - 9), 1)
            pygame.draw.line(surf, (140, 128, 112), (x - 3, y - 8), (x + 3, y - 8), 1)
            # Two faint nose-cavity pricks in the shadow band
            pygame.draw.rect(surf, (12, 10, 14), (x - 1, y - 11, 1, 1))
            pygame.draw.rect(surf, (12, 10, 14), (x + 1, y - 11, 1, 1))
        else:
            # Eyes -- two faint pinpricks in the hood shadow
            pygame.draw.circle(surf, (200, 180, 60), (x - 2, y - 12), 1)
            pygame.draw.circle(surf, (200, 180, 60), (x + 2, y - 12), 1)
        # Scorched hem
        pygame.draw.rect(surf, ash, (x - 9, y + 14, 18, 2))
    elif kind == "policeman":
        # Navy uniform, peaked cap, gold badge. Cap-brim shadow falls
        # across the upper face so the eyes sit in a permanent dark
        # band; sunken hollows beneath. On `blink` the eyes become
        # 2x2 voids -- the cop's face goes wrong for a frame.
        pygame.draw.rect(surf, (32, 50, 100), (x - 9, y - 4, 18, 18))   # blue body
        pygame.draw.circle(surf, (200, 170, 140), (x, y - 12), 7)
        pygame.draw.rect(surf, (22, 30, 70), (x - 9, y - 22, 18, 6))    # cap brim
        pygame.draw.rect(surf, (22, 30, 70), (x - 7, y - 28, 14, 7))    # cap crown
        pygame.draw.rect(surf, (140, 50, 50), (x - 7, y - 7, 14, 4))    # collar/tie
        # Cap-brim shadow band across the upper face
        pygame.draw.rect(surf, (50, 40, 50), (x - 6, y - 15, 12, 2))
        # Sunken hollows
        pygame.draw.line(surf, (160, 130, 110), (x - 4, y - 12), (x - 1, y - 12), 1)
        pygame.draw.line(surf, (160, 130, 110), (x + 1, y - 12), (x + 4, y - 12), 1)
        if blink:
            pygame.draw.rect(surf, (4, 2, 4), (x - 3, y - 14, 2, 2))
            pygame.draw.rect(surf, (4, 2, 4), (x + 1, y - 14, 2, 2))
        else:
            pygame.draw.circle(surf, C_BLACK, (x - 2, y - 13), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 2, y - 13), 1)
            try:
                surf.set_at((x - 3, y - 14), (240, 240, 250))
                surf.set_at((x + 1, y - 14), (240, 240, 250))
            except (IndexError, ValueError):
                pass
        # Gold badge on the chest
        pygame.draw.rect(surf, (220, 200, 80), (x - 1, y, 3, 3))
        pygame.draw.rect(surf, C_BLACK, (x - 1, y, 3, 3), 1)
        # Black belt
        pygame.draw.rect(surf, (10, 10, 18), (x - 9, y + 6, 18, 2))
    elif kind == "fisherman":
        # Mustard coat, weathered hat. Hat brim shadows the eyes; an
        # extra small dark line runs across the upper face so the eye
        # area reads as deeply shadowed even in bright scenes. Beard
        # has a damp green-grey cast (algae / pond-water).
        pygame.draw.rect(surf, (140, 112, 76), (x - 9, y - 2, 18, 18))
        pygame.draw.circle(surf, (200, 178, 158), (x, y - 12), 7)
        pygame.draw.rect(surf, (180, 162, 64), (x - 10, y - 22, 20, 4))  # hat brim
        pygame.draw.rect(surf, (180, 162, 64), (x - 7, y - 28, 14, 7))   # crown
        pygame.draw.rect(surf, (160, 170, 150), (x - 6, y - 5, 12, 8))   # beard (damp/mossy)
        # Hat-brim shadow band
        pygame.draw.rect(surf, (50, 40, 28), (x - 6, y - 14, 12, 3))
        if not blink:
            pygame.draw.circle(surf, (200, 200, 220), (x - 2, y - 13), 1)
            pygame.draw.circle(surf, (200, 200, 220), (x + 2, y - 13), 1)
        pygame.draw.line(surf, (80, 60, 40), (x - 10, y), (x - 14, y - 10), 2)  # rod
    elif kind == "guard":
        # Iron helmet + spear. The visor slit is now a deeper, pitch-
        # black void with two faint red glints inside -- you don't see
        # eyes, you see something looking out from inside the helm.
        pygame.draw.rect(surf, (96, 96, 116), (x - 9, y - 2, 18, 18))
        pygame.draw.circle(surf, (200, 170, 140), (x, y - 12), 7)
        pygame.draw.rect(surf, (130, 130, 150), (x - 9, y - 22, 18, 12))  # helmet
        # Visor slit -- pitch black with two pinprick reds
        pygame.draw.rect(surf, (4, 2, 4), (x - 4, y - 14, 8, 4))
        if not blink:
            pygame.draw.circle(surf, (180, 30, 30), (x - 2, y - 12), 1)
            pygame.draw.circle(surf, (180, 30, 30), (x + 2, y - 12), 1)
        pygame.draw.line(surf, (60, 40, 25), (x + 12, y - 18), (x + 12, y + 16), 2)
        pygame.draw.polygon(surf, (200, 200, 220),
                            [(x + 12, y - 18), (x + 9, y - 22), (x + 15, y - 22)])
    elif kind == "shadow":
        pygame.draw.rect(surf, (8, 4, 12), (x - 8, y - 4, 16, 18))
        pygame.draw.circle(surf, (8, 4, 12), (x, y - 10), 8)
        pygame.draw.circle(surf, (220, 30, 30), (x - 3, y - 11), 1)
        pygame.draw.circle(surf, (220, 30, 30), (x + 3, y - 11), 1)
    elif kind == "tall_shadow":
        # Tall, THIN smear of darkness. ~2.5x a normal NPC vertically, but
        # narrow enough that it reads as not-quite-human. In lore the
        # figure is a pilgrim of the Yellow King -- which is why the eyes
        # are three jaundiced dots stacked vertically, not a face we
        # recognise.
        # The silhouette now BREATHES on a slow sine: top of the body
        # drifts left/right by a pixel, and the seam wavers. Adds a
        # subliminal "this isn't standing still" cue without changing
        # the silhouette enough to mistake for movement.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        sway = math.sin(t * 0.9) * 1
        body_rect = pygame.Rect(x - 8 + int(sway), y - 50, 16, 64)
        pygame.draw.rect(surf, (4, 2, 8), body_rect)
        pygame.draw.rect(surf, (12, 8, 18), body_rect.inflate(-4, -6))
        # Wavering vertical seam
        for sy_step in range(0, 60, 4):
            seam_x = x + int(math.sin(t * 1.3 + sy_step * 0.2) * 1)
            pygame.draw.line(surf, (2, 0, 4),
                             (seam_x, y - 48 + sy_step),
                             (seam_x, y - 48 + sy_step + 4), 1)
        # Three vertical eye dots. One of the three flickers off on a
        # staggered cycle so the row is rarely all lit at the same time
        # -- the eyes never quite "match" each other.
        flicker = int(t * 2.4) % 7
        if flicker != 0:
            pygame.draw.circle(surf, (210, 188, 70), (x, y - 42), 1)
        if flicker != 3:
            pygame.draw.circle(surf, (210, 188, 70), (x, y - 38), 1)
        if flicker != 5:
            pygame.draw.circle(surf, (210, 188, 70), (x, y - 34), 1)
    elif kind == "yellow_king":
        # The King in Yellow -- a floating tear-in-space: a churning clot of
        # gold light packed with the cult's fused faces, arms reaching out to
        # grasp, trailing a wake of glowing soul-orbs. The full drawing, rift
        # birth, and motion live in _draw_king. `birth` (0..1) and `gait` come
        # from the live NPC; when absent (a preview) they loop off the clock so
        # the eruption still shows.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        if birth is None:
            cyc = t % 7.0
            b = min(1.0, cyc / 1.6)            # erupt over ~1.6s
            g = max(0.0, cyc - 1.6) * 7.0      # then drift the rest
        else:
            b = birth
            g = gait if gait is not None else t * 7.0
        _draw_king(surf, x, y, facing, t, b, g)
    elif kind == "wolf":
        # Lean grey quadruped, low to the ground. Yellow eyes give a
        # threat read at a glance even with the small sprite size.
        body = (90, 88, 100)
        dark = (50, 48, 56)
        # Torso (low horizontal oval)
        pygame.draw.ellipse(surf, body, (x - 11, y - 4, 22, 12))
        pygame.draw.ellipse(surf, dark, (x - 11, y - 4, 22, 12), 1)
        # Tail
        pygame.draw.line(surf, dark, (x - 11, y - 4), (x - 18, y - 8), 2)
        # Legs (4 short stumps)
        for lx in (-7, -3, 3, 7):
            pygame.draw.rect(surf, dark, (x + lx - 1, y + 4, 2, 6))
        # Head (right side)
        pygame.draw.circle(surf, body, (x + 8, y - 8), 6)
        pygame.draw.circle(surf, dark, (x + 8, y - 8), 6, 1)
        # Snout
        pygame.draw.polygon(surf, body, [(x + 11, y - 6), (x + 17, y - 5), (x + 11, y - 4)])
        pygame.draw.polygon(surf, dark, [(x + 11, y - 6), (x + 17, y - 5), (x + 11, y - 4)], 1)
        # Pointed ears (two triangles)
        pygame.draw.polygon(surf, dark, [(x + 4, y - 12), (x + 6, y - 17), (x + 8, y - 12)])
        pygame.draw.polygon(surf, dark, [(x + 9, y - 12), (x + 11, y - 17), (x + 13, y - 12)])
        # Eye (yellow)
        pygame.draw.circle(surf, (220, 200, 60), (x + 9, y - 9), 1)
    elif kind == "black_figure":
        # Pure-black humanoid silhouette, NPC proportions. No eyes, no
        # facial detail -- just the hole-shaped outline of a person.
        # Spawned in the player's house on the 7th re-entry.
        outline = (0, 0, 0)
        # Slight darker-than-black aura behind the body so it reads as
        # absence rather than a flat sprite on dark floors.
        aura = pygame.Surface((30, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (0, 0, 0, 90), (0, 0, 30, 36))
        surf.blit(aura, (x - 15, y - 18))
        # Body
        pygame.draw.rect(surf, outline, (x - 9, y - 4, 18, 18))
        # Head
        pygame.draw.circle(surf, outline, (x, y - 12), 7)
        # Shoulders / cloak hint
        pygame.draw.rect(surf, outline, (x - 11, y - 4, 22, 6))
        # Legs
        pygame.draw.rect(surf, outline, (x - 6, y + 14, 5, 8))
        pygame.draw.rect(surf, outline, (x + 1, y + 14, 5, 8))
    elif kind == "cultist":
        # Hooded cultist -- a grim, near-black robe and a deep cowl that
        # is simply a void; the cult has taken his face. He trudges: the
        # whole body rocks and rises on each step so he reads as
        # advancing on you, not idling. Two cold, recessed pinpricks of
        # sick light sit far back in the cowl -- menace, not glow.
        t = pygame.time.get_ticks() / 1000.0
        gait = math.sin(t * 3.0 + x * 0.02)
        lean = int(gait * 2)                      # rock the body
        bob = int(abs(math.sin(t * 3.0)) * 2)     # rise on each step
        robe = (50, 45, 42)                       # grim charcoal
        robe_lo = (28, 25, 24)
        cowl = (12, 11, 13)                       # black void
        top = y - 10 - bob
        pygame.draw.polygon(surf, robe,
                            [(x - 9, y + 16), (x - 7 + lean, top),
                             (x + 7 + lean, top), (x + 9, y + 16)])
        pygame.draw.polygon(surf, robe_lo,
                            [(x - 9, y + 16), (x - 7 + lean, top),
                             (x + 7 + lean, top), (x + 9, y + 16)], 1)
        # Deep cowl -- a black hood, the face a hole.
        head_cy = top - 1
        pygame.draw.ellipse(surf, cowl, (x - 7 + lean, head_cy - 7, 14, 14))
        # Two cold recessed eyes (dim sick amber), blinking on a cycle.
        if (t + x * 0.05) % 4.0 > 0.2:
            pygame.draw.circle(surf, (116, 100, 50), (x - 3 + lean, head_cy), 1)
            pygame.draw.circle(surf, (116, 100, 50), (x + 3 + lean, head_cy), 1)
        # Dried blood down the robe + a black hem.
        pygame.draw.line(surf, (64, 16, 14), (x, y + 2), (x + 1, y + 15), 2)
        pygame.draw.line(surf, (16, 12, 12),
                         (x - 8, y + 16), (x + 8, y + 16), 2)
    elif kind == "curse_priest":
        # The cult's curse-priest -- the special cultist that binds the
        # Watchers to you. Taller and gaunter than the rank-and-file:
        # a blood-dark robe, a low hood over a pale ruined face with a
        # stitched-shut mouth and hollow sockets, hands raised mid-rite
        # with ichor dripping from the fingertips. A vertical row of
        # small yellow curse-eyes opens down its chest -- the curse,
        # looking out. Sways, twitches, and drips.
        t = pygame.time.get_ticks() / 1000.0
        sway = math.sin(t * 1.2 + x * 0.02)
        lean = int(sway)
        robe = (54, 40, 44)
        robe_lo = (32, 22, 26)
        blood = (122, 24, 22)
        face = (190, 180, 165)
        face_lo = (120, 110, 100)
        # Tall robe body.
        pygame.draw.polygon(surf, robe,
                            [(x - 10, y + 18), (x - 7 + lean, y - 18),
                             (x + 7 + lean, y - 18), (x + 10, y + 18)])
        pygame.draw.polygon(surf, robe_lo,
                            [(x - 10, y + 18), (x - 7 + lean, y - 18),
                             (x + 7 + lean, y - 18), (x + 10, y + 18)], 1)
        # Blood down the robe front.
        pygame.draw.line(surf, blood, (x + lean, y - 14), (x, y + 16), 2)
        pygame.draw.line(surf, (70, 14, 12), (x - 3, y + 2), (x - 2, y + 16), 1)
        # A slow rite: the arms rise and fall together, ichor beading
        # off the fingertips. They lift highest as the curse-eyes flare
        # (below) -- that upswing is the moment it binds you.
        rite = math.sin(t * 1.3) * 0.5 + 0.5          # 0..1, arms down..up
        hy = y - 4 - int(rite * 9)
        for s in (-1, 1):
            hx = x + s * (9 + int(rite * 3))
            pygame.draw.line(surf, robe, (x + s * 5, y - 8), (hx, hy), 3)
            pygame.draw.circle(surf, face, (hx, hy), 2)
            drip = (t * 0.9 + (s + 1) * 0.4) % 1.0
            pygame.draw.circle(surf, blood, (hx, hy + 2 + int(drip * 10)), 1)
        # Hood + ruined pale face.
        pygame.draw.ellipse(surf, robe_lo, (x - 7 + lean, y - 26, 14, 16))
        pygame.draw.ellipse(surf, face, (x - 4 + lean, y - 23, 8, 11))
        pygame.draw.ellipse(surf, face_lo, (x - 4 + lean, y - 23, 8, 11), 1)
        # Hollow sockets -- no light there.
        pygame.draw.circle(surf, (12, 8, 10), (x - 2 + lean, y - 19), 1)
        pygame.draw.circle(surf, (12, 8, 10), (x + 2 + lean, y - 19), 1)
        # Stitched-shut mouth.
        my = y - 14
        pygame.draw.line(surf, (60, 20, 22),
                         (x - 3 + lean, my), (x + 3 + lean, my), 1)
        for sx in range(-3, 4, 2):
            pygame.draw.line(surf, (40, 12, 14),
                             (x + lean + sx, my - 1), (x + lean + sx, my + 1), 1)
        # A vertical row of small curse-eyes down the chest, flaring
        # sick-bright on the rite's upswing -- the curse, looking out.
        ecol = (150 + int(rite * 55), 120 + int(rite * 50), 56)
        for i in range(3):
            if (t * 1.1 + i * 0.8) % 3.0 > 0.3:
                pygame.draw.circle(surf, ecol, (x + lean, y - 6 + i * 6), 1)
        # Dark hem.
        pygame.draw.line(surf, (24, 14, 16),
                         (x - 9, y + 18), (x + 9, y + 18), 2)
    elif kind == "vessel_avatar":
        # A towering Yellow-King vessel with reaching tentacles. Body is
        # the tall_shadow silhouette enlarged + four wiggling tentacles
        # that point in the `facing` direction (toward the player when
        # in chase). Animated by pygame.time so the wiggle keeps moving
        # even when the figure is mid-lunge.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        body_rect = pygame.Rect(x - 11, y - 56, 22, 72)
        pygame.draw.rect(surf, (4, 2, 8), body_rect)
        pygame.draw.rect(surf, (12, 8, 18), body_rect.inflate(-6, -8))
        pygame.draw.line(surf, (2, 0, 4), (x, y - 54), (x, y + 14), 1)
        for ey in (-46, -42, -38):
            pygame.draw.circle(surf, (210, 188, 70), (x, y + ey), 2)
        fx, fy = facing
        for i in range(4):
            phase = t * 6 + i * 1.4
            wiggle = math.sin(phase) * 6
            sway_x = -fy * wiggle
            sway_y = fx * wiggle
            origin = (x + (i - 1.5) * 4, y - 4)
            mid = (origin[0] + fx * 12 + sway_x * 0.5,
                   origin[1] + fy * 12 + sway_y * 0.5)
            tip = (origin[0] + fx * 26 + sway_x,
                   origin[1] + fy * 26 + sway_y)
            pygame.draw.line(surf, (8, 6, 14),
                             (int(origin[0]), int(origin[1])),
                             (int(mid[0]), int(mid[1])), 3)
            pygame.draw.line(surf, (16, 12, 24),
                             (int(mid[0]), int(mid[1])),
                             (int(tip[0]), int(tip[1])), 2)
            pygame.draw.circle(surf, (210, 188, 70),
                               (int(tip[0]), int(tip[1])), 1)
    elif kind == "static_figure":
        pygame.draw.rect(surf, (40, 40, 50), (x - 8, y - 2, 16, 18))
        pygame.draw.circle(surf, (200, 180, 160), (x, y - 10), 7)
        pygame.draw.rect(surf, (30, 25, 20), (x - 8, y - 17, 16, 8))
    elif kind == "doll":
        # Pink-dress doll with X-stitched eyes. Once every ~4 seconds
        # there's a brief frame where the X eyes invert into open
        # round pupils -- the doll is looking at you. The window is
        # ~80ms (one stale frame) so the player questions whether
        # they saw it. Tear streak under the right eye.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        anomaly = (t % 4.0) > 3.92
        pygame.draw.rect(surf, (200, 100, 130), (x - 6, y - 2, 12, 14))
        pygame.draw.circle(surf, (250, 230, 220), (x, y - 9), 6)
        if anomaly:
            # Open black eyes
            pygame.draw.circle(surf, C_BLACK, (x - 3, y - 10), 1)
            pygame.draw.circle(surf, C_BLACK, (x + 3, y - 10), 1)
        else:
            pygame.draw.line(surf, C_BLACK, (x - 4, y - 11), (x - 2, y - 9), 1)
            pygame.draw.line(surf, C_BLACK, (x - 2, y - 11), (x - 4, y - 9), 1)
            pygame.draw.line(surf, C_BLACK, (x + 2, y - 11), (x + 4, y - 9), 1)
            pygame.draw.line(surf, C_BLACK, (x + 4, y - 11), (x + 2, y - 9), 1)
        # Faint tear streak under the right eye (always visible)
        pygame.draw.line(surf, (180, 130, 140),
                         (x + 3, y - 7), (x + 3, y - 4), 1)
    elif kind == "watcher":
        # A Watcher -- the curse made visible. The same sculpted mask the
        # King wears, but cold and ashen: his gold gone to dead bone. It
        # hangs in the air at the edge of sight, never a clean object --
        # it phases on a slow sine (you can never quite fix on it) and
        # drifts a little nearer over its cycle, a dark scrap of fabric
        # dissolving beneath it. Each Watcher wears its own morbid face
        # (vacuous / hollow / scream / mutated), seeded by where it stands.
        # Look straight at it (gaze=True) and it thins toward nothing --
        # the faint ember of his gold in one socket is the last to go.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        phase = 0.35 + 0.5 * (math.sin(t * 1.1 + x * 0.01) * 0.5 + 0.5)
        loom = math.sin(t * 0.5 + x * 0.02) * 0.5 + 0.5       # 0..1, creeps in
        sway = math.sin(t * 0.8 + x * 0.03)
        kinds = ("hollow", "vacuous", "scream", "mutated")
        wk = kinds[int(abs(x) // 7) % 4]
        chip = (int(abs(x) // 13) % 2 == 0)
        r = 12 + int(loom * 2)                                # looms larger as it nears
        layer = _pg.Surface((40, 64), _pg.SRCALPHA)
        bx, my = 20, 26
        # A torn scrap of shroud dissolving away beneath the face -- a hint
        # of a body without being a figure.
        for k in range(3):
            a = 40 - k * 12
            wv = int(sway * (k + 1))
            _pg.draw.polygon(layer, (16, 15, 19, a),
                             [(bx - 5 - k, my + 6 + k * 6), (bx + 5 + k, my + 6 + k * 6),
                              (bx + 3 + wv, my + 16 + k * 7), (bx - 3 + wv, my + 16 + k * 7)])
        _face_mask(layer, bx, my, r, _WATCH_MASK_P, int(abs(x)) + 1, wk, chip=chip)
        if not gaze:
            # one faint ember deep in the left socket -- a whisper of his fire
            ex, ey = bx - r // 2, my - r // 5
            halo = _pg.Surface((40, 64), _pg.SRCALPHA)
            g = 70 + int(math.sin(t * 2.0 + x) * 20)
            _pg.draw.circle(halo, (g, int(g * 0.72), 26), (ex, ey), 3)
            layer.blit(halo, (0, 0), special_flags=_pg.BLEND_RGBA_ADD)
        # Looked at, it thins toward nothing; otherwise it half-fades on
        # its phase -- always an apparition, never solid.
        layer.set_alpha(int(255 * (phase * 0.45 if gaze else phase)))
        surf.blit(layer, (x - bx, y - my - 16))    # floats at head height
    elif kind == "glitch_npc":
        for _ in range(30):
            ox = random.randint(-9, 9); oy = random.randint(-12, 8)
            col = (random.randint(80,255), random.randint(0,60), random.randint(0,60))
            pygame.draw.rect(surf, col, (x + ox, y + oy, 2, 2))
    else:
        # generic placeholder
        pygame.draw.rect(surf, (200, 200, 200), (x - 8, y - 8, 16, 16))


def draw_player_sprite(surf, x, y, facing, walk_phase=0, armor=None, mud=0.0,
                        prone=False):
    """THRESHOLD: the private investigator, 1994. A long dark wool
    overcoat over a pale collar, dark trousers, scuffed work boots --
    the silhouette of a man who drove here on a case, not a tourist.
    Muted to sit in the graded, desaturated palette. Armor overlays
    are vestigial (combat is gone) but still draw if equipped so old
    saves render cleanly.

    A faint ground-shadow ellipse roots the player in the scene.
    None of the NPCs cast a shadow, by design -- the player is the
    only thing here that's properly *here*."""
    coat    = (56, 52, 56)        # worn dark wool overcoat
    coat_lo = (37, 34, 39)        # coat shadow side / hem
    collar  = (150, 146, 138)     # pale shirt collar
    pants   = (40, 38, 45)        # dark trousers
    boots   = (34, 26, 20)        # scuffed work boots
    skin    = (188, 158, 134)     # muted
    hair    = (52, 40, 30)
    if prone:
        # Lying on the cot. Compress the figure to a horizontal
        # silhouette with a thin blanket overlay. Drawn off-centre
        # so it reads as resting on the bedding rather than on the
        # floor.
        bx = x - 12
        by = y - 2
        # Blanket / quilt
        pygame.draw.rect(surf, (90, 60, 70), (bx, by, 24, 9))
        pygame.draw.rect(surf, (60, 40, 50), (bx, by, 24, 9), 1)
        # Head poking out at one end
        pygame.draw.circle(surf, skin, (bx + 22, by + 4), 4)
        pygame.draw.rect(surf, hair, (bx + 19, by, 7, 4))
        # Eyes closed: a thin dark line
        pygame.draw.line(surf, (40, 30, 24),
                         (bx + 21, by + 4), (bx + 24, by + 4), 1)
        # One boot peeking out the foot end
        pygame.draw.rect(surf, boots, (bx, by + 5, 4, 3))
        return
    # Ground shadow under the boots (drawn first so the body sits on it).
    shadow = pygame.Surface((22, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), (0, 0, 22, 8))
    surf.blit(shadow, (x - 11, y + 16))
    # Trousers (legs), under the coat hem.
    pygame.draw.rect(surf, pants, (x - 6, y + 9, 12, 6))
    # The overcoat: a long slab from shoulders to mid-thigh -- the PI
    # silhouette. Shadowed on the right side + along the hem for form.
    pygame.draw.rect(surf, coat, (x - 8, y - 5, 16, 17))
    pygame.draw.rect(surf, coat_lo, (x + 3, y - 5, 5, 17))   # right shadow side
    pygame.draw.rect(surf, coat_lo, (x - 8, y + 9, 16, 3))   # hem shadow
    pygame.draw.line(surf, coat_lo, (x, y - 3), (x, y + 8), 1)  # front seam
    # Pale collar at the throat.
    pygame.draw.rect(surf, collar, (x - 3, y - 5, 6, 3))
    # Vestigial armor overlay (combat is gone; if a player has
    # equipped armor from a legacy save it still renders so the
    # save isn't broken visually).
    if armor == "cloth_tunic":
        pygame.draw.rect(surf, (200, 180, 140), (x - 7, y - 2, 14, 10))
    elif armor == "leather_armor":
        pygame.draw.rect(surf, (110, 70, 40), (x - 8, y - 3, 16, 12))
    elif armor == "iron_armor":
        pygame.draw.rect(surf, (140, 145, 160), (x - 8, y - 4, 16, 14))
    # Head
    pygame.draw.circle(surf, skin, (x, y - 12), 7)
    # Hair across the top
    pygame.draw.rect(surf, hair, (x - 7, y - 18, 14, 6))
    # Boots: walking animation
    leg_off = int(math.sin(walk_phase) * 2)
    pygame.draw.rect(surf, boots, (x - 6, y + 14, 5, 4 + max(0, -leg_off)))
    pygame.draw.rect(surf, boots, (x + 1, y + 14, 5, 4 + max(0, leg_off)))
    # THRESHOLD wake-state mud. The player's boots are caked when the
    # opening fires; the splatter recedes as they walk. Two flecks of
    # darker brown on each boot + a smear up the jeans cuff that
    # fades with `mud` (0..1).
    if mud > 0.05:
        m_a = max(40, min(220, int(180 * mud)))
        mud_col = (28, 18, 10)
        pygame.draw.rect(surf, mud_col, (x - 6, y + 14, 5, 2))
        pygame.draw.rect(surf, mud_col, (x + 1, y + 14, 5, 2))
        # cuff smear
        cuff = pygame.Surface((14, 4), pygame.SRCALPHA)
        pygame.draw.rect(cuff, (30, 22, 14, m_a), (0, 0, 14, 4))
        surf.blit(cuff, (x - 7, y + 12))
        # one fleck higher up the leg, only when very muddy
        if mud > 0.5:
            pygame.draw.rect(surf, mud_col, (x - 4, y + 9, 2, 2))
            pygame.draw.rect(surf, mud_col, (x + 3, y + 10, 2, 2))
    # Eyes (look in facing direction)
    fx, fy = facing
    eye_y = y - 12 + int(fy * 2)
    eye_dx = int(fx * 2)
    pygame.draw.circle(surf, C_BLACK, (x - 2 + eye_dx, eye_y), 1)
    pygame.draw.circle(surf, C_BLACK, (x + 2 + eye_dx, eye_y), 1)


# ===========================================================================
# THE KING IN YELLOW
#
# A floating tear-in-space: a churning clot of sick-gold light packed with the
# cult's fused faces, broken arms reaching out to grasp, shedding a wake of
# glowing soul-orbs as it drifts -- hell, chasing you. It births by tearing a
# rift open (driven by the NPC's `birth` 0..1), floats and never phases out
# (only the individual masks surface and dissolve), and the reaching arms
# swivel smoothly toward the player. Drawn from draw_npc_sprite's yellow_king
# dispatch as _draw_king(surf, x, y, facing, t, birth, gait).
# ===========================================================================
_YK_TRAIL = []                       # recent mass-centre screen positions
_YK_PARTS = []                       # particle wake: dicts x,y,vx,vy,age,life,r,kind
_YK_LAST = [0.0]                     # last draw time (for particle dt)
_YK_ACC = [0.0]                      # distance accumulator (spaces shed orbs)
_YK_AIM = [None]                     # smoothed arm-aim angle (swivels to player)
_YK_PRNG = random.Random(99)         # own RNG -> never touches the game's stream
_YK_T1, _YK_T2, _YK_T3, _YK_T4 = (140, 96, 22), (196, 150, 42), (236, 198, 66), (252, 226, 120)
_YK_GOLD, _YK_HOT = (236, 204, 64), (252, 226, 120)
_YK_DK, _YK_DK_HI = (28, 25, 34), (60, 55, 72)
_YK_BONE = (150, 128, 70)
_YK_PIT = (10, 8, 12)
# Warm, gold-tinted mask tones so the masks read as part of the light (drawn
# translucent + luminous) rather than separate pale objects floating in it.
_YK_MHI, _YK_MMID, _YK_MLO, _YK_MPIT = (238, 222, 174), (210, 178, 108), (150, 116, 52), (78, 52, 18)

# --- Shared mask geometry -------------------------------------------------
# ONE sculpted form, two palettes: the King's mask (warm gold, drawn
# luminous + translucent) and the Watcher's (cold ash, the curse made
# visible) are the SAME imperfect, worn, morbid face -- only the colour
# and the light differ. "His gold, the Watcher's dark."
_KING_MASK_P = dict(lo=_YK_MLO, mid=_YK_MMID, hi=_YK_MHI, pit=_YK_MPIT,
                    milk=(246, 228, 170), tooth=(248, 236, 200),
                    crack=(86, 58, 24), rim=_YK_MLO, glint=(255, 226, 120),
                    sheen=(255, 248, 214))
_WATCH_MASK_P = dict(lo=(54, 51, 58), mid=(84, 80, 88), hi=(118, 114, 120),
                     pit=(12, 11, 14), milk=(158, 156, 150), tooth=(150, 146, 138),
                     crack=(20, 18, 22), rim=(34, 32, 38), glint=(150, 110, 40),
                     sheen=(128, 124, 130))


def _mask_pts(cx, cy, r, seed, elong=1.12, chip=False):
    """An imperfect, slightly-elongated, lumpy outline -- never a clean
    circle. `chip` dents one stretch of the rim (a broken-off piece)."""
    rnd = random.Random(seed)
    ph = rnd.uniform(0, 6.28)
    chip_i = rnd.randint(0, 17) if chip else -99
    pts = []
    for i in range(18):
        a = i / 18 * math.tau
        rr = r * (0.92 + 0.10 * math.sin(a * 2 + ph) + 0.07 * math.sin(a * 3 - ph)
                  + 0.05 * (rnd.random() - 0.5))
        if abs(i - chip_i) <= 1 or abs(i - chip_i) >= 17:
            rr *= 0.62
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * elong))
    return pts


def _mask_sc(pts, cx, cy, f, dx=0, dy=0):
    return [(cx + (x - cx) * f + dx, cy + (y - cy) * f + dy) for x, y in pts]


def _mask_poly(s, c, pts, w=0):
    pygame.draw.polygon(s, c, [(int(a), int(b)) for a, b in pts], w)


def _mask_jag(s, c, x0, y0, x1, y1, seed, w=1):
    rnd = random.Random(seed)
    pts = [(x0, y0)]
    for i in range(1, 5):
        t = i / 5
        pts.append((x0 + (x1 - x0) * t + rnd.uniform(-2, 2),
                    y0 + (y1 - y0) * t + rnd.uniform(-2, 2)))
    pts.append((x1, y1))
    pygame.draw.lines(s, c, False, [(int(a), int(b)) for a, b in pts], w)


def _face_mask(s, cx, cy, r, P, seed, kind, chip=False):
    """The shared mask face. Flat 3-tone sculpt on an imperfect outline,
    with worn detail (brow / nose / teeth / hairline cracks / grime) that
    only surfaces once `r` is large enough to carry it -- below that it
    reads as a clean morbid blob so it survives gameplay scale. `kind`
    sets the eyes: vacuous (blind milk) / hollow (void pits) / scream
    (pits + gaping maw) / mutated (eyes opening across the face) /
    plain+crack (simple pit eyes, for the King's rotation)."""
    cx, cy, r = int(cx), int(cy), int(r)
    rnd = random.Random(seed * 7 + 3)
    pts = _mask_pts(cx, cy, r, seed, chip=chip)
    _mask_poly(s, P['lo'], _mask_sc(pts, cx, cy, 1.0, 1, 1))
    _mask_poly(s, P['mid'], pts)
    # GLOSS -- smoother shading: an extra mid->hi tone band so the sculpt
    # ramps in 4 steps instead of 3, and an anti-aliased silhouette edge so
    # the rim isn't a hard pixel staircase.
    midhi = ((P['mid'][0] + P['hi'][0]) // 2, (P['mid'][1] + P['hi'][1]) // 2,
             (P['mid'][2] + P['hi'][2]) // 2)
    _mask_poly(s, midhi, _mask_sc(pts, cx, cy, 0.91, -1, -1))
    _mask_poly(s, P['hi'], _mask_sc(pts, cx, cy, 0.80, -2, -2))
    try:
        pygame.gfxdraw.aapolygon(s, [(int(a), int(b)) for a, b in pts], P['mid'])
    except (ValueError, OverflowError):
        pass
    detail = r >= 10
    ew = max(2, r // 3)
    lx, rx, ey = cx - r // 2, cx + r // 2, cy - r // 5
    if detail:
        for i in range(5, 11):                       # lit upper-left rim
            a = i / 18 * math.tau
            try:
                s.set_at((int(cx + math.cos(a) * r * 0.96),
                          int(cy + math.sin(a) * r * 1.07)), P['hi'])
            except (IndexError, ValueError):
                pass
        pygame.draw.line(s, P['crack'], (lx - 2, ey - ew),
                         (rx + 2, ey - ew + rnd.randint(-1, 1)), 1)   # brow
        pygame.draw.line(s, P['lo'], (cx, ey + 1), (cx - 1, cy + r // 4), 1)  # nose
        pygame.draw.circle(s, P['pit'], (cx - 2, int(cy + r // 4)), 1)
        pygame.draw.circle(s, P['pit'], (cx + 2, int(cy + r // 4)), 1)
    er = ew + (1 if rnd.random() < 0.5 else 0)        # a touch asymmetric
    if kind == "vacuous":
        pygame.draw.circle(s, P['milk'], (lx, ey), ew)
        pygame.draw.circle(s, P['milk'], (rx, ey), er)
        if detail:
            try:
                s.set_at((lx - 1, ey - 1), P['hi']); s.set_at((rx - 1, ey - 1), P['hi'])
            except (IndexError, ValueError):
                pass
    elif kind == "scream":
        pygame.draw.circle(s, P['pit'], (lx, ey), ew)
        pygame.draw.circle(s, P['pit'], (rx, ey), er)
        pygame.draw.ellipse(s, P['pit'], (cx - r // 3, cy + r // 5, 2 * r // 3, r))
        if detail:
            for tk in range(-1, 2):
                pygame.draw.rect(s, P['tooth'], (cx + tk * (r // 5) - 1, cy + r // 5, 2, 3))
    elif kind == "mutated":
        for px, py in [(lx, ey), (rx, ey), (cx, cy - r // 2),
                       (cx + r // 2, cy + r // 4), (cx - r // 3, cy + r // 2)]:
            pygame.draw.circle(s, P['pit'], (int(px), int(py)), max(1, ew - 1))
    else:  # hollow / plain / crack -- empty pit eyes
        pygame.draw.circle(s, P['pit'], (lx, ey), ew)
        pygame.draw.circle(s, P['pit'], (rx, ey), er)
        if kind == "crack" and detail:
            _mask_jag(s, P['crack'], cx - 1, cy - r, cx + 2, cy + r, seed, 1)
    if detail and kind != "scream":
        for ex in (lx, rx):                           # lid-shadow arc
            pygame.draw.arc(s, P['crack'], (ex - ew, ey - ew, 2 * ew, 2 * ew), 0.3, 2.84, 1)
        if kind != "mutated":                         # downturned mouth seam
            my = cy + int(r * 0.62)
            pygame.draw.line(s, P['crack'], (cx - r // 3, my - 1), (cx, my + 1), 1)
            pygame.draw.line(s, P['crack'], (cx, my + 1), (cx + r // 3, my - 1), 1)
    if detail:
        for ci in range(rnd.randint(1, 2)):           # hairline cracks
            a0 = rnd.uniform(0, math.tau)
            _mask_jag(s, P['crack'], cx + math.cos(a0) * r * 0.9, cy + math.sin(a0) * r * 0.9,
                      cx + rnd.uniform(-0.3, 0.3) * r, cy + rnd.uniform(-0.2, 0.5) * r, seed + ci, 1)
        placed = 0                                    # grime, clamped inside the rim
        while placed < 6:
            gx = cx + rnd.uniform(-0.7, 0.7) * r
            gy = cy + rnd.uniform(-0.7, 0.9) * r
            if (gx - cx) ** 2 + ((gy - cy) / 1.12) ** 2 < (r * 0.85) ** 2:
                try:
                    s.set_at((int(gx), int(gy)), P['crack'])
                except (IndexError, ValueError):
                    pass
                placed += 1
    # GLOSS -- wet luminous sheen: a glossy hot spot riding the upper-left of
    # the dome, so the gold reads as molten/lacquered (lit from within) rather
    # than matte. Palette-driven, so the King glistens while the Watcher stays
    # ashen.
    shr = max(1, r // 4)
    sgx, sgy = int(cx - r * 0.32), int(cy - r * 0.42)
    if shr >= 2:
        pygame.draw.circle(s, P['sheen'], (sgx, sgy), shr)
        try:
            pygame.gfxdraw.aacircle(s, sgx, sgy, shr, P['hi'])
        except (ValueError, OverflowError):
            pass
        try:
            s.set_at((sgx - shr // 3, sgy - shr // 3), (255, 255, 244))
        except (IndexError, ValueError):
            pass
    else:
        try:
            s.set_at((sgx, sgy), P['sheen'])
        except (IndexError, ValueError):
            pass
    try:
        pygame.gfxdraw.aapolygon(s, [(int(a), int(b)) for a, b in pts], P['rim'])
    except (ValueError, OverflowError):
        pass
    _mask_poly(s, P['rim'], pts, 1)
    try:
        s.set_at((lx, ey), P['glint'])                # the one ember of his gold
    except (IndexError, ValueError):
        pass


def _yk_slots():
    """Deterministic swirl params for the faces + eyes (own RNG so the global
    stream the game relies on is never touched). Each face orbits the core at
    its own radius/speed and surfaces/dissolves on its own fade cycle."""
    r = random.Random(20240611)
    faces, eyes = [], []
    # mask designs: plain, screaming, hollow/gaunt, cracked, and a melted
    # double (two faces fused) that only POPS UP now and then.
    kinds = ["plain", "scream", "hollow", "plain", "crack", "double",
             "plain", "scream", "hollow", "double", "hollow", "scream",
             "plain", "crack"]                       # GLOSS -- denser face clot
    for k in kinds:
        faces.append((
            r.uniform(0.22, 0.82), r.uniform(0, math.tau), r.uniform(0.30, 0.85),
            r.randint(4, 8), r.uniform(0.5, 1.3), r.uniform(0, 6.28), k))
    for _ in range(4):
        eyes.append((r.uniform(0.2, 0.7), r.uniform(0, math.tau),
                     r.uniform(0.3, 0.8), r.uniform(0, 6.28)))
    return faces, eyes


_YK_FACES, _YK_EYES = _yk_slots()


def _yk_radial(surf, x, y, R, color, a0, add=True):
    """Soft glowing/fading disc built from concentric circles."""
    R = max(2, int(R))
    g = pygame.Surface((R * 2 + 2, R * 2 + 2), pygame.SRCALPHA)
    c = (R + 1, R + 1); st = max(6, R // 2)
    for i in range(st, 0, -1):
        a = int(a0 * (1 - i / st) ** 1.7)
        if a > 0:
            pygame.draw.circle(g, (color[0], color[1], color[2], a), c, int(R * i / st))
    surf.blit(g, (int(x) - R - 1, int(y) - R - 1),
              special_flags=pygame.BLEND_RGBA_ADD if add else 0)


def _yk_glow(layer, cx, cy, R, t):
    """The hovering clot of golden light -- soft bloom over a lumpy amber mass
    brightening to a hot core, churning on a slow swirl."""
    R = int(R * (1 + 0.06 * math.sin(t * 2.0)))
    _yk_radial(layer, cx, cy, int(R * 1.8), _YK_GOLD, 66)
    _yk_radial(layer, cx, cy, int(R * 1.18), _YK_GOLD, 60)
    subs = [(0, 0), (-0.4, -0.18), (0.4, -0.12), (-0.12, 0.4),
            (0.22, 0.32), (-0.3, 0.2), (0.12, -0.34)]
    sw = t * 0.6
    ca, sa = math.cos(sw), math.sin(sw)
    for col, scl, grow in [(_YK_T1, 1.0, 3), (_YK_T2, 0.74, 1), (_YK_T3, 0.5, 0), (_YK_T4, 0.28, 0)]:
        for ox, oy in subs:
            rx, ry = ox * ca - oy * sa, ox * sa + oy * ca
            pygame.draw.circle(layer, col,
                               (int(cx + rx * R * 0.6), int(cy + ry * R * 0.9)),
                               int(R * 0.5 * scl) + grow)
    for k in range(4):
        a = sw * 1.6 + k * 1.57
        _yk_radial(layer, cx + math.cos(a) * R * 0.42, cy + math.sin(a) * R * 0.42,
                   int(R * 0.42), _YK_T4, 76)
    _yk_radial(layer, cx, cy - 2, int(R * 0.55), _YK_T4, 78)
    # GLOSS -- wet sheen: a bright specular cap riding the upper clot so the
    # whole mass reads as molten/lacquered light, not a matte glow.
    _yk_radial(layer, cx - int(R * 0.16), cy - int(R * 0.34), int(R * 0.30),
               (255, 248, 222), 92)


def _yk_mask(surf, cx, cy, r, vis, kind, seed=0):
    """A MASK made of the same light: warm gold-tinted, translucent (the glow
    reads through it) + a luminous halo, surfacing (vis->1) and dissolving back
    into the glow (vis->0). The face is the shared sculpt (`_face_mask`) so the
    King and the Watcher wear the same form. 'double' is two melted into one."""
    if vis <= 0.03:
        return
    cx, cy, r = int(cx), int(cy), int(r)
    _yk_radial(surf, cx, cy, r + 3, _YK_HOT, int(36 * vis))
    pad = max(3, r // 2)
    S = (r + pad) * 2
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    mx = my = r + pad
    if kind == "double":
        off = max(2, r // 2)
        for i, ddx in enumerate((-off, off)):
            _face_mask(m, mx + ddx, my, r, _KING_MASK_P, seed + i,
                       "hollow" if vis > 0.4 else "plain")
        pygame.draw.line(m, _YK_MLO, (mx, my - r), (mx, my + r), 1)
    else:
        _face_mask(m, mx, my, r, _KING_MASK_P, seed, kind)
    m.set_alpha(int(64 + 156 * vis))
    surf.blit(m, (cx - mx, cy - my))


def _yk_orb(surf, cx, cy, r, vis, seed, t):
    """A shed SOUL-ORB: a small copy of the body -- a glowing gold clot with a
    mask or two floating in it -- fading out in the wake."""
    if vis <= 0.04:
        return
    _yk_radial(surf, cx, cy, int(r * 1.8), _YK_GOLD, int(46 * vis))
    _yk_radial(surf, cx, cy, int(r * 1.05), _YK_T2, int(58 * vis))
    _yk_radial(surf, cx, cy, int(r * 0.62), _YK_T3, int(72 * vis))
    _yk_radial(surf, cx, cy, int(r * 0.32), _YK_T4, int(88 * vis))
    kinds = ("plain", "scream", "hollow", "crack")
    for k in range(2 if r >= 9 else 1):
        ang = seed * 1.7 + k * 2.4 + t * 1.4
        rad = r * 0.36
        _yk_mask(surf, cx + math.cos(ang) * rad, cy + math.sin(ang) * rad,
                 max(3, int(r * 0.44)), vis * 0.9, kinds[(seed + k) % 4], seed=seed + k)


def _yk_birth_rift(surf, cx, cy, R, bp):
    """The birth: space tears open. A vertical gold rift cracks wide and flares
    white-hot early, then fattens and seals into the forming body."""
    opening = math.sin(min(1.0, bp / 0.5) * 1.5708)
    seal = max(0.0, (bp - 0.5) / 0.5)
    h = R * (0.5 + 2.7 * opening) * (1 - 0.55 * seal)
    n = max(3, int(h / 4))
    for i in range(n):
        f = i / (n - 1)
        yy = cy - h + 2 * h * f
        rr = (R * 0.14 + R * 0.55 * seal) * (0.4 + 0.6 * math.sin(f * math.pi))
        _yk_radial(surf, cx, yy, max(2, int(rr)), _YK_T4, int(118 * (1 - 0.4 * seal)))
    flare = max(0.0, 1.0 - abs(bp - 0.28) / 0.28)
    if flare > 0:
        _yk_radial(surf, cx, cy, int(R * (0.4 + 0.95 * flare)), (255, 250, 232), int(100 * flare))


def _yk_arm(layer, cx, cy, ang, length, R, t, idx):
    """A broken arm reaching out of the light: it extends and draws back on its
    own cycle, reflex elbow, clawing hand."""
    wob = math.sin(t * 1.9 + idx * 1.3) * 0.14
    ext = 0.55 + 0.45 * max(0.0, math.sin(t * 1.5 + idx * 0.9))
    reach = length * ext
    root = (cx + math.cos(ang) * R * 0.5, cy + math.sin(ang) * R * 0.5)
    hand = (cx + math.cos(ang + wob) * reach, cy + math.sin(ang + wob) * reach)
    mx, my = (root[0] + hand[0]) / 2, (root[1] + hand[1]) / 2
    perp = (-math.sin(ang), math.cos(ang)); k = (R * 0.5) * (1 if idx % 2 else -1)
    elbow = (mx + perp[0] * k, my + perp[1] * k)
    pts = [(int(a), int(b)) for a, b in (root, elbow, hand)]
    w = max(3, int(R * 0.34))
    pygame.draw.lines(layer, _YK_DK_HI, False, pts, w + 2)
    pygame.draw.lines(layer, _YK_DK, False, pts, w)
    ha = math.atan2(hand[1] - elbow[1], hand[0] - elbow[0])
    pygame.draw.circle(layer, _YK_DK, (int(hand[0]), int(hand[1])), max(2, w // 2))
    for fa in (-42, -14, 16, 44):
        a2 = ha + math.radians(fa)
        tip = (hand[0] + math.cos(a2) * R * 0.5, hand[1] + math.sin(a2) * R * 0.5)
        pygame.draw.line(layer, _YK_DK, (int(hand[0]), int(hand[1])),
                         (int(tip[0]), int(tip[1])), 2)
        try:
            layer.set_at((int(tip[0]), int(tip[1])), _YK_BONE)
        except (IndexError, ValueError):
            pass


def _draw_king(surf, x, y, facing, t, birth, gait):
    """THE KING IN YELLOW (see header). `birth` (0..1, already de-None'd by the
    dispatch) drives the rift eruption; `t` animates; `gait` is accepted but the
    float needs no leg cycle. It never phases out -- only masks come and go.

    NOTE: the King's render INCLUDES its particle wake -- the shed soul-orbs
    and gold motes streamed along his path (module globals `_YK_PARTS` /
    `_YK_TRAIL`, updated and drawn here every frame). The particles are an
    INTEGRAL part of the sprite, not a separable layer: they are spawned from
    his motion and drawn in this same call. Anything that draws, moves, or
    re-homes the King must carry the wake with it (the trail self-resets on a
    teleport jump, below). Do not split the particles out of `_draw_king`."""
    global _YK_TRAIL
    R = 22
    mcx, mcy = x, int(y - 42 + math.sin(t * 1.1) * 3)        # floats above the feet
    bp = 1.0 if birth is None else max(0.0, min(1.0, birth))
    grow = bp * bp * (3 - 2 * bp)                            # body eases in
    ag = max(0.0, (bp - 0.4) / 0.6)
    agrow = ag * ag * (3 - 2 * ag)                           # arms erupt in the back half
    valpha = 1.0 if bp >= 1.0 else 0.4 + 0.6 * grow
    dt = t - _YK_LAST[0]
    _YK_LAST[0] = t
    if dt <= 0 or dt > 0.2:
        dt = 0.016
    # Wake reset on a teleport/respawn jump (re-seeds the swivel too).
    if _YK_TRAIL:
        px, py, pt = _YK_TRAIL[-1]
        if (mcx - px) ** 2 + (mcy - py) ** 2 > 70 ** 2 or (t - pt) > 0.45:
            _YK_TRAIL = []
            _YK_PARTS.clear()
            _YK_ACC[0] = 0.0
            _YK_AIM[0] = None
    # BIRTH: while the rift is opening, vomit a radial burst of soul-orbs.
    if bp < 0.18:
        for _ in range(2):
            ang = _YK_PRNG.uniform(0, math.tau)
            spd = _YK_PRNG.uniform(45, 120)
            orb = _YK_PRNG.random() < 0.4
            _YK_PARTS.append({
                "kind": "orb" if orb else "mote", "seed": _YK_PRNG.randint(0, 999),
                "x": mcx, "y": mcy,
                "vx": math.cos(ang) * spd, "vy": math.sin(ang) * spd,
                "age": 0.0, "life": _YK_PRNG.uniform(0.4, 0.8),
                "r": _YK_PRNG.uniform(6, 12) if orb else _YK_PRNG.uniform(2, 4)})
    disp = math.hypot(mcx - _YK_TRAIL[-1][0], mcy - _YK_TRAIL[-1][1]) if _YK_TRAIL else 0.0
    _YK_TRAIL.append((mcx, mcy, t))
    _YK_TRAIL = _YK_TRAIL[-5:]
    tvx, tvy = (mcx - _YK_TRAIL[0][0], mcy - _YK_TRAIL[0][1])
    tl = math.hypot(tvx, tvy) or 1.0
    bvx, bvy = -tvx / tl, -tvy / tl
    _YK_ACC[0] += disp
    while disp > 0.4 and _YK_ACC[0] >= 6:        # GLOSS -- denser wake (was 8)
        _YK_ACC[0] -= 6
        _YK_PARTS.append({
            "kind": "orb", "seed": _YK_PRNG.randint(0, 999),
            "x": mcx + _YK_PRNG.uniform(-5, 5), "y": mcy + _YK_PRNG.uniform(-5, 5),
            "vx": bvx * 9 + _YK_PRNG.uniform(-8, 8),
            "vy": bvy * 9 + _YK_PRNG.uniform(-8, 8),
            "age": 0.0, "life": _YK_PRNG.uniform(0.8, 1.25),
            "r": _YK_PRNG.uniform(7, 15)})
        for _ in range(3):
            _YK_PARTS.append({
                "kind": "mote", "seed": 0,
                "x": mcx + _YK_PRNG.uniform(-9, 9), "y": mcy + _YK_PRNG.uniform(-9, 9),
                "vx": bvx * 18 + _YK_PRNG.uniform(-16, 16),
                "vy": bvy * 18 + _YK_PRNG.uniform(-16, 16),
                "age": 0.0, "life": _YK_PRNG.uniform(0.25, 0.5),
                "r": _YK_PRNG.uniform(1.5, 3.0)})
    if len(_YK_PARTS) > 130:                     # GLOSS -- room for the denser wake
        del _YK_PARTS[:len(_YK_PARTS) - 130]
    keep = []
    for p in _YK_PARTS:
        p["age"] += dt
        fr = p["age"] / p["life"]
        if fr >= 1.0:
            continue
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        a = 1.0 - fr
        if p["kind"] == "orb":
            _yk_orb(surf, p["x"], p["y"], p["r"] * (1 - 0.22 * fr), a, p["seed"], t)
        else:
            _yk_radial(surf, p["x"], p["y"], max(2, p["r"] * (1 - 0.4 * fr)),
                       _YK_GOLD, int(150 * a))
        keep.append(p)
    _YK_PARTS[:] = keep
    # Faint floating shadow on the ground, far below the mass.
    sh = pygame.Surface((40, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 80), (0, 0, 40, 12))
    surf.blit(sh, (x - 20, y - 4))
    # Body on its own layer.
    L = 170
    layer = pygame.Surface((L, L), pygame.SRCALPHA)
    cx = cy = L // 2
    # Arms swivel smoothly toward the player (facing).
    fxx, fyy = facing if facing != (0, 0) else (0, 1)
    tgt = math.atan2(fyy, fxx)
    if _YK_AIM[0] is None:
        _YK_AIM[0] = tgt
    da_ = (tgt - _YK_AIM[0] + math.pi) % math.tau - math.pi
    _YK_AIM[0] += da_ * min(1.0, dt * 7.0)
    aa = _YK_AIM[0]
    fb = (math.cos(aa) * R * 0.22, math.sin(aa) * R * 0.22)
    if bp < 1.0:
        _yk_birth_rift(surf, mcx, mcy, R, bp)                # space tears open
    _yk_glow(layer, cx, cy, R * max(0.18, grow), t)
    for fi, (rn, ba, asp, fr, vsp, vph, kind) in enumerate(_YK_FACES):
        ang = ba + t * asp
        rr = rn * (0.9 + 0.1 * math.sin(t * 0.8 + vph))
        fxp = cx + math.cos(ang) * R * 0.82 * rr * grow + fb[0]
        fyp = cy + math.sin(ang) * R * 0.95 * rr * grow + fb[1]
        if kind == "double":
            vis = max(0.0, min(1.0, (math.sin(t * vsp + vph) - 0.55) / 0.4))
        else:
            vis = max(0.0, min(1.0, 0.5 + 0.72 * math.sin(t * vsp + vph)))
        _yk_mask(layer, fxp, fyp, fr, vis, kind, seed=fi + 1)
    for rn, ba, asp, ph in _YK_EYES:
        if math.sin(t * 2.1 + ph) > 0.1:
            ang = ba + t * asp
            ex = cx + math.cos(ang) * R * 0.7 * rn * grow + fb[0]
            ey = cy + math.sin(ang) * R * 0.7 * rn * grow + fb[1]
            _yk_radial(layer, ex, ey, 5, _YK_HOT, 110)
            pygame.draw.circle(layer, _YK_PIT, (int(ex), int(ey)), 1)
    layer.set_alpha(int(255 * max(0.05, valpha)))
    surf.blit(layer, (mcx - cx, mcy - cy))
    # Arms LAST (own layer over the wake + glow); they erupt in the back half.
    if agrow > 0.02:
        arml = pygame.Surface((L, L), pygame.SRCALPHA)
        for idx, (da, ln) in enumerate([(0.0, R * 2.05), (0.45, R * 1.7), (-0.45, R * 1.7),
                                        (0.95, R * 1.45), (-0.95, R * 1.45)]):
            _yk_arm(arml, cx, cy, aa + da, ln * agrow, R * max(0.4, agrow), t, idx)
        arml.set_alpha(int(255 * max(0.05, valpha)))
        surf.blit(arml, (mcx - cx, mcy - cy))


# ---------------------------------------------------------------------------
# Player axe swing -- the one attack, gated on the splitting axe.
# ---------------------------------------------------------------------------
def draw_axe_swing(surf, px, py, facing, prog):
    """The splitting axe swung in a flat arc through the facing
    hemisphere. `prog` (0..1) walks the head from the wind-up side
    across the front. Procedural: a wood haft + a steel head, with a
    short motion smear behind the head so the chop reads as motion."""
    prog = max(0.0, min(1.0, prog))
    fx, fy = facing
    if fx == 0 and fy == 0:
        fy = 1.0
    base = math.atan2(fy, fx)
    sweep = math.radians(150)
    a = base - sweep / 2 + prog * sweep          # current haft angle
    R = 21                                        # haft length
    ox = px + math.cos(base) * 3                  # pivot just ahead of hands
    oy = py + math.sin(base) * 3
    hx, hy = ox + math.cos(a) * R, oy + math.sin(a) * R
    # Motion smear: the recent path of the head, fading behind it.
    smear = []
    for k in range(7):
        aa = base - sweep / 2 + max(0.0, prog - k * 0.06) * sweep
        smear.append((int(ox + math.cos(aa) * R), int(oy + math.sin(aa) * R)))
    if len(smear) >= 2:
        pygame.draw.lines(surf, (208, 204, 196), False, smear, 1)
    # Haft (wood), dark edge under a lit core.
    pygame.draw.line(surf, (70, 48, 28), (int(ox), int(oy)), (int(hx), int(hy)), 4)
    pygame.draw.line(surf, (128, 92, 54), (int(ox), int(oy)), (int(hx), int(hy)), 2)
    # Steel head: a wedge perpendicular at the haft end.
    pdx, pdy = -math.sin(a), math.cos(a)          # perpendicular
    ddx, ddy = math.cos(a), math.sin(a)           # along the haft
    bw, bl = 6, 8                                 # blade half-width, reach
    quad = [
        (hx + pdx * bw, hy + pdy * bw),
        (hx - pdx * bw, hy - pdy * bw),
        (hx + ddx * bl - pdx * (bw - 2), hy + ddy * bl - pdy * (bw - 2)),
        (hx + ddx * bl + pdx * (bw - 2), hy + ddy * bl + pdy * (bw - 2)),
    ]
    quad = [(int(x), int(y)) for x, y in quad]
    pygame.draw.polygon(surf, (170, 176, 186), quad)
    pygame.draw.polygon(surf, (232, 238, 246), quad, 1)
    # Bright leading edge catching the light.
    pygame.draw.line(surf, (245, 248, 252),
                     (int(hx + ddx * bl), int(hy + ddy * bl)),
                     (int(hx + pdx * bw), int(hy + pdy * bw)), 1)


# ---------------------------------------------------------------------------
# King-in-Yellow death screen -- a furnace of his masks, fire all around.
# ---------------------------------------------------------------------------
def _frand(i):
    """Cheap deterministic [0,1) noise -- no RNG state to disturb."""
    x = math.sin(i * 12.9898) * 43758.5453
    return x - math.floor(x)


def _flame_tongue(surf, bx, by, dx, dy, length, width, ph):
    """One flame licking from base (bx,by) along direction (dx,dy):
    three nested tapering triangles, outer ember -> hot core."""
    pdx, pdy = -dy, dx                            # perpendicular
    sway = math.sin(ph * 3.0) * 0.32

    def tongue(frac_len, frac_w, col):
        tip = (bx + dx * length * frac_len + pdx * sway * width * frac_w,
               by + dy * length * frac_len + pdy * sway * width * frac_w)
        l = (bx + pdx * frac_w * width * 0.5, by + pdy * frac_w * width * 0.5)
        r = (bx - pdx * frac_w * width * 0.5, by - pdy * frac_w * width * 0.5)
        pygame.draw.polygon(surf, col,
                            [(int(l[0]), int(l[1])), (int(r[0]), int(r[1])),
                             (int(tip[0]), int(tip[1]))])
    tongue(1.0, 1.0, (196, 58, 16))
    tongue(0.72, 0.62, (252, 146, 30))
    tongue(0.46, 0.30, (255, 226, 128))


def _yk_flames(surf, w, h, t, ramp):
    """A wall of fire along the bottom edge plus licks up the sides --
    the furnace burning all around. A bright base glow seats the flames
    so they don't read as floating triangles."""
    # Hot base glow band along the bottom (additive).
    glow = pygame.Surface((w, int(h * 0.22)), pygame.SRCALPHA)
    gh = glow.get_height()
    for i in range(gh):
        a = int(120 * (1 - i / gh) ** 1.5 * ramp)
        pygame.draw.line(glow, (255, 120, 30, a), (0, gh - i), (w, gh - i))
    surf.blit(glow, (0, h - gh), special_flags=pygame.BLEND_RGBA_ADD)
    # Edges: (dir, fixed-coord, span, step, height-scale).
    edges = (
        (0, -1, h, w, 18, 2.05),    # bottom, pointing up   -- the wall
        (1,  0, 0, h, 30, 0.95),    # left, pointing right
        (-1, 0, w, h, 30, 0.95),    # right, pointing left
    )
    for dx, dy, fixed, span, step, scale in edges:
        horizontal = dx != 0
        for s in range(0, span + step, step):
            seed = s * 0.07 + (0 if dx >= 0 else 3.3)
            fh = ((30 + 48 * (0.5 + 0.5 * math.sin(t * 6 + seed))
                   + 24 * math.sin(t * 11 + seed * 2)) * scale * ramp)
            if fh < 4:
                continue
            if horizontal:
                bx, by = fixed, s
            else:
                bx, by = s, fixed
            _flame_tongue(surf, bx, by, dx, dy, fh, step * 1.05, t + seed)


def draw_king_death(surf, t):
    """Full-screen King-in-Yellow death: a dark furnace his gold masks
    rise out of, fire all around, one mask looming up to take the whole
    screen. `t` is seconds since the catch (the caller holds ~3.5s)."""
    w, h = surf.get_size()
    ramp = max(0.0, min(1.0, t / 0.5))            # fade-in
    flick = 0.88 + 0.12 * math.sin(t * 19.0) + 0.04 * math.sin(t * 41.0)
    core_y = int(h * 0.56)

    # 1. Dark furnace base: near-black at the top, deepening ember-red
    #    toward a hot belly low-centre. The darkness lets the masks pop.
    bands = 56
    bh = int(h / bands) + 2
    for i in range(bands):
        f = i / (bands - 1)
        col = (int((14 + 132 * f * f) * flick * ramp),
               int((5 + 40 * f * f) * flick * ramp),
               int((6 + 8 * f) * ramp))
        pygame.draw.rect(surf, col, (0, int(f * h), w, bh))

    # 2. The furnace mouth: a pulsing hot core low-centre that the
    #    looming mask rises out of.
    pulse = 0.5 + 0.5 * math.sin(t * 3.0)
    _yk_radial(surf, w // 2, core_y, int(w * (0.30 + 0.05 * pulse)),
               (190, 64, 18), int(72 * ramp))
    _yk_radial(surf, w // 2, core_y, int(w * 0.15),
               (255, 132, 38), int(82 * ramp))

    # 3. Rising heat -- soft additive blooms drifting up and fading,
    #    so the air reads as shimmering, not as orange discs.
    for i in range(7):
        hx = int((0.08 + 0.84 * _frand(i * 5 + 1)) * w
                 + math.sin(t * 0.7 + i) * 22)
        prog = (t * 0.32 + _frand(i * 5 + 2)) % 1.0
        hy = int(h - prog * h * 1.05)
        a = int(30 * ramp * (1.0 - prog))
        if a > 0:
            _yk_radial(surf, hx, hy, int(34 + 28 * _frand(i * 5 + 3)),
                       (255, 124, 38), a)

    # 4. Mask field -- surfacing from the heat and dissolving back, each
    #    on its own pulse so they breathe in and out of the dark.
    kinds = ("scream", "hollow", "crack", "plain")
    for i in range(10):
        mx = int(_frand(i * 7 + 3) * w + math.sin(t * 0.9 + i * 1.7) * 14)
        my = int((0.10 + 0.78 * _frand(i * 7 + 5)) * h
                 + math.cos(t * 0.8 + i * 2.1) * 10)
        r = 12 + int(30 * _frand(i * 7 + 9))
        vis = (0.5 + 0.5 * math.sin(t * 1.7 + i * 1.9)) ** 1.3 * ramp
        _yk_mask(surf, mx, my, r, vis, kinds[i % len(kinds)], seed=i + 1)

    # 5. The looming mask: rises from the core and swells to fill the
    #    screen -- the King's face closing over you.
    grow = 36 + min(1.0, t / 3.2) ** 1.4 * 152
    cvis = min(1.0, 0.55 + t / 3.0) * ramp
    _yk_radial(surf, w // 2, core_y, int(grow * 1.7), _YK_HOT, int(58 * ramp))
    _yk_mask(surf, w // 2, core_y, int(grow), cvis, "scream", seed=7)

    # 6. Fire all around.
    _yk_flames(surf, w, h, t, ramp)

    # 7. Embers streaming upward.
    for i in range(56):
        ex = (_frand(i * 2 + 1) * w + math.sin(t * 1.4 + i) * 11) % w
        span = h + 50
        ey = (h + 24 - ((t * (44 + 70 * _frand(i)))
                        + _frand(i * 2 + 2) * span) % span)
        er = 1 + int(2 * _frand(i * 3))
        if er >= 2:
            _yk_radial(surf, int(ex), int(ey), er * 3, (255, 176, 70),
                       int(56 * ramp))
        pygame.draw.circle(surf, (255, 226, 150), (int(ex), int(ey)), er)

    # 8. Smoke-dark vignette at the top corners so the furnace frames in.
    vig = pygame.Surface((w, int(h * 0.4)), pygame.SRCALPHA)
    vh = vig.get_height()
    for i in range(vh):
        a = int(150 * (1 - i / vh) ** 1.4 * ramp)
        pygame.draw.line(vig, (0, 0, 0, a), (0, i), (w, i))
    surf.blit(vig, (0, 0))
