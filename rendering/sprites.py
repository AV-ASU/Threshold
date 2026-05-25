"""Character sprites: NPCs, enemies, the player."""
import math
import random
import pygame
from constants import C_BLACK

def draw_npc_sprite(surf, x, y, kind, facing, blink=False, gaze=False,
                    birth=None, gait=None, threat=None):
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
        _draw_king(surf, x, y, facing, t, b, g, threat)
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
        # A Watcher -- the curse made visible. NOT an eye: a tall,
        # ragged, faceless figure that stands at the edge of sight and
        # watches. Only the cursed see them. It is half-there -- it
        # phases on a slow sine, an apparition you can never quite fix
        # on -- and it looms a little nearer over its cycle. Two faint
        # sick pinpricks deep in the cowl are the only colour: the gaze.
        # Look straight at it (gaze=True) and the pinpricks go dark.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        phase = 0.35 + 0.5 * (math.sin(t * 1.1 + x * 0.01) * 0.5 + 0.5)
        loom = math.sin(t * 0.5 + x * 0.02) * 0.5 + 0.5      # 0..1, creeps in
        sway = int(math.sin(t * 0.8 + x * 0.03))
        layer = _pg.Surface((40, 64), _pg.SRCALPHA)
        bx = 20 + sway
        base_y = 60
        h = 38 + int(loom * 8)            # looms taller as it nears
        top = base_y - h
        shroud = (24, 22, 28, 255)
        shroud_lo = (11, 10, 14, 255)
        # Tapered shroud -- narrow shoulders to a wide, torn hem.
        body = [(bx - 4, top + 7), (bx + 4, top + 7),
                (bx + 10, base_y), (bx - 10, base_y)]
        _pg.draw.polygon(layer, shroud, body)
        _pg.draw.polygon(layer, shroud_lo, body, 1)
        # Ragged hem -- torn strips trailing into the dark.
        for hx in range(-9, 10, 3):
            _pg.draw.line(layer, shroud, (bx + hx, base_y - 3),
                          (bx + hx + 1, base_y + 3 + (hx % 3)), 2)
        # Drawn-up hood / faceless head.
        _pg.draw.circle(layer, shroud, (bx, top + 6), 6)
        _pg.draw.circle(layer, shroud_lo, (bx, top + 7), 5)
        # Thin reaching arms hinted down the body.
        _pg.draw.line(layer, shroud_lo, (bx - 4, top + 12), (bx - 8, top + 24), 2)
        _pg.draw.line(layer, shroud_lo, (bx + 4, top + 12), (bx + 8, top + 24), 2)
        # The gaze: two faint sick pinpricks (yellow used ONLY here, a
        # dim light in the dark), unless the player looks straight at it.
        if not gaze:
            g = 110 + int(math.sin(t * 2.0 + x) * 25)
            eye = (g, int(g * 0.85), 38, 255)
            _pg.draw.circle(layer, eye, (bx - 2, top + 6), 1)
            _pg.draw.circle(layer, eye, (bx + 2, top + 6), 1)
            halo = _pg.Surface((40, 64), _pg.SRCALPHA)
            _pg.draw.circle(halo, (60, 52, 22), (bx, top + 6), 7)
            layer.blit(halo, (0, 0), special_flags=_pg.BLEND_RGBA_ADD)
        layer.set_alpha(int(255 * phase))
        surf.blit(layer, (x - 20, y - base_y))
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
_YK_PALE, _YK_WHITE = (248, 232, 150), (255, 248, 224)   # bright gold -> white core
_YK_PIT = (10, 8, 12)
_YK_SHADOW, _YK_SHADOW_HI = (20, 16, 26), (52, 44, 64)   # dark grabbing arms
# Existence curve: the King stays a dark void until threat passes _LO, then the
# light blooms in hard, fully real by _HI -- so most of the approach is dread.
_YK_BLOOM_LO, _YK_BLOOM_HI = 0.45, 0.9
# PALLID mask tones -- sickly bone, jaundiced, cold against the warm light, so a
# dead face reads as it surfaces from the glow. Black voids, not warm sockets.
_YK_MHI, _YK_MMID, _YK_MLO, _YK_MPIT = (226, 224, 196), (172, 174, 132), (98, 100, 64), (12, 12, 10)


def _yk_slots():
    """Deterministic swirl params for the faces (own RNG so the global stream the
    game relies on is never touched). Index 0 is the dominant central mask (drawn
    anchored, not orbiting); the rest orbit and erupt around it as it manifests."""
    r = random.Random(20240611)
    faces = [(0.16, 0.0, 0.22, 10, 0.55, 0.0, "scream")]
    for k in ["hollow", "double", "scream", "hollow", "scream"]:
        faces.append((
            r.uniform(0.34, 0.82), r.uniform(0, math.tau), r.uniform(0.30, 0.80),
            r.randint(6, 9), r.uniform(0.5, 1.2), r.uniform(0, 6.28), k))
    return faces


_YK_FACES = _yk_slots()


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
    """A clot of bright gold light. Orange lives ONLY in the soft aura behind the
    mass, so it reads as the warm outline of the whole silhouette; the bright
    lumpy body is drawn opaque on top, so it never goes orange between its blobs."""
    R = int(R * (1 + 0.06 * math.sin(t * 2.0)))
    # warm orange outline: a broad aura behind everything (shows only at the rim).
    _yk_radial(layer, cx, cy, int(R * 1.95), _YK_T1, 72)
    _yk_radial(layer, cx, cy, int(R * 1.5), _YK_T2, 58)
    subs = [(0, 0), (-0.4, -0.18), (0.4, -0.12), (-0.12, 0.4),
            (0.22, 0.32), (-0.3, 0.2), (0.12, -0.34)]
    sw = t * 0.6
    ca, sa = math.cos(sw), math.sin(sw)
    # bright gold -> white body, drawn opaque so it covers the centre.
    for col, scl, grow in [(_YK_T3, 1.06, 3), (_YK_PALE, 0.78, 1), (_YK_WHITE, 0.5, 0), (_YK_WHITE, 0.28, 0)]:
        for ox, oy in subs:
            rx, ry = ox * ca - oy * sa, ox * sa + oy * ca
            pygame.draw.circle(layer, col,
                               (int(cx + rx * R * 0.6), int(cy + ry * R * 0.9)),
                               int(R * 0.5 * scl) + grow)
    for k in range(4):
        a = sw * 1.6 + k * 1.57
        _yk_radial(layer, cx + math.cos(a) * R * 0.42, cy + math.sin(a) * R * 0.42,
                   int(R * 0.42), _YK_WHITE, 70)
    _yk_radial(layer, cx, cy - 2, int(R * 0.55), _YK_WHITE, 78)


# Slot/orb kind vocabulary -> facial expression. The faces read as people:
# a dead, pallid human face surfaces from the light, mostly shrieking.
_YK_EXPR = {"hollow": "gaunt", "crack": "scream", "plain": "calm"}


def _yk_face(m, mx, my, r, expr, detail):
    """A readable human face on mask-surface `m`: pallid oval lit upper-left,
    brow ridge, nose ridge, eyes + an expressive mouth. `detail` gates the
    features in as the mask surfaces (so it emerges as a blank pallid shape
    first)."""
    hi, mid, lo, pit = _YK_MHI, _YK_MMID, _YK_MLO, _YK_MPIT
    rw, rh = r, int(r * 1.12)
    pygame.draw.ellipse(m, lo, (mx - rw + 1, my - rh + 1, 2 * rw, 2 * rh))
    pygame.draw.ellipse(m, mid, (mx - rw, my - rh, 2 * rw, 2 * rh))
    pygame.draw.ellipse(m, hi, (mx - rw + 1, my - rh, max(1, 2 * rw - 2), max(1, 2 * rh - 3)))
    if not detail or r < 3:
        return
    ew = max(1, r // 3)
    eyl = (mx - r * 0.42, my - r * 0.12)
    eyr = (mx + r * 0.42, my - r * 0.12)
    bw = max(1, r // 4)
    pygame.draw.line(m, lo, (int(mx - r * 0.7), int(my - r * 0.45)), (int(mx - r * 0.05), int(my - r * 0.30)), bw)
    pygame.draw.line(m, lo, (int(mx + r * 0.7), int(my - r * 0.45)), (int(mx + r * 0.05), int(my - r * 0.30)), bw)
    pygame.draw.line(m, lo, (int(mx), int(my - r * 0.1)), (int(mx), int(my + r * 0.25)), 1)
    pygame.draw.line(m, hi, (int(mx - 1), int(my - r * 0.1)), (int(mx - 1), int(my + r * 0.2)), 1)
    if expr in ("scream", "gaunt", "vacant", "wail"):    # vacuous void sockets
        if expr in ("vacant", "wail"):                   # deep ROUND sockets (not lenses),
            sr = max(2, int(ew * 1.05))                  # clearly separate, each holding a
            for ex, ey in (eyl, eyr):                    # golden gaze: a single pixel while
                pygame.draw.circle(m, pit, (int(ex), int(ey)), sr)   # calm, flaring once angry
                if expr == "wail":
                    _yk_radial(m, ex, ey, 2, _YK_HOT, 150)
                try:
                    m.set_at((int(ex), int(ey)), _YK_HOT)
                except (IndexError, ValueError):
                    pass
        else:
            for ex, ey in (eyl, eyr):
                pygame.draw.ellipse(m, pit, (int(ex - ew), int(ey - ew), 2 * ew, int(2.2 * ew)))
    else:
        for ex, ey in (eyl, eyr):
            pygame.draw.line(m, pit, (int(ex - ew), int(ey)), (int(ex + ew), int(ey)), 1)
        if expr == "weep":
            for ex, ey in (eyl, eyr):
                pygame.draw.line(m, hi, (int(ex), int(ey + 1)), (int(ex), int(my + r * 0.6)), 1)
    if expr == "wail":                                   # black tears down the mask
        for ex, ey in (eyl, eyr):
            pygame.draw.line(m, pit, (int(ex), int(ey + ew)),
                             (int(ex + r * 0.06), int(my + r * 0.98)), max(1, r // 5))
    mym = my + r * 0.55
    if expr in ("scream", "wail"):
        pygame.draw.ellipse(m, pit, (int(mx - r * 0.32), int(mym - r * 0.1),
                                     max(2, int(r * 0.64)), max(3, int(r * 0.85))))
    elif expr == "gaunt":
        pygame.draw.ellipse(m, pit, (int(mx - r * 0.28), int(mym - r * 0.05),
                                     max(2, int(r * 0.56)), max(2, int(r * 0.5))))
        pygame.draw.line(m, lo, (int(mx - r * 0.7), int(my)), (int(mx - r * 0.5), int(my + r * 0.4)), 1)
        pygame.draw.line(m, lo, (int(mx + r * 0.7), int(my)), (int(mx + r * 0.5), int(my + r * 0.4)), 1)
    elif expr == "vacant":                               # a slack, dead jaw hanging ajar
        pygame.draw.ellipse(m, pit, (int(mx - r * 0.16), int(mym + r * 0.04),
                                     max(2, int(r * 0.32)), max(2, int(r * 0.36))))
    elif expr == "smile":
        pts = [(mx - r * 0.4, mym - r * 0.1), (mx, mym + r * 0.2), (mx + r * 0.4, mym - r * 0.1)]
        pygame.draw.lines(m, pit, False, [(int(a), int(b)) for a, b in pts], 1)
    elif expr == "weep":
        pts = [(mx - r * 0.4, mym + r * 0.15), (mx, mym - r * 0.1), (mx + r * 0.4, mym + r * 0.15)]
        pygame.draw.lines(m, pit, False, [(int(a), int(b)) for a, b in pts], 1)
    else:
        pygame.draw.line(m, pit, (int(mx - r * 0.3), int(mym)), (int(mx + r * 0.3), int(mym)), 1)
    if expr in ("vacant", "wail"):                       # a hairline crack -- a broken mask
        pygame.draw.line(m, pit, (int(mx + r * 0.2), int(my - rh * 0.85)),
                         (int(mx - r * 0.06), int(my + r * 0.55)), 1)


def _yk_mask(surf, cx, cy, r, vis, kind):
    """A dead human FACE surfacing from the light: pallid, translucent (the glow
    reads through it) + a luminous halo, rising (vis->1) and dissolving back into
    the glow (vis->0). 'double' is two faces fused, both shrieking."""
    if vis <= 0.03:
        return
    cx, cy, r = int(cx), int(cy), int(r)
    _yk_radial(surf, cx, cy, r + 3, _YK_HOT, int(36 * vis))
    pad = max(3, r // 2)
    S = (r + pad) * 2
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    mx = my = r + pad
    detail = vis > 0.35
    if kind == "double":
        off = max(2, r // 2)
        for ddx in (-off, off):
            _yk_face(m, mx + ddx, my, max(2, int(r * 0.78)), "scream", detail)
    else:
        _yk_face(m, mx, my, r, _YK_EXPR.get(kind, kind), detail)
    m.set_alpha(int(64 + 156 * vis))
    surf.blit(m, (cx - mx, cy - my))


def _yk_grab_arm(surf, cx, cy, ang, reach, t, phase, scale, lit, alpha=255, side=1, speed=0.62):
    """An arm that buds from nothing, stretches out ahead getting bigger as its
    hand opens to grab, then fades as a fresh arm takes its place -- the King
    hauling itself forward on handholds that dissolve behind it. `phase` offsets
    each arm's lifecycle so there is always one reaching; `speed` sets its pace."""
    life = (t * speed + phase) % 1.0
    if life < 0.12:                                  # born from nothing
        fade = life / 0.12
    elif life > 0.7:                                 # then it vanishes
        fade = max(0.0, (1.0 - life) / 0.3)
    else:
        fade = 1.0
    if fade <= 0.02:
        return
    armA = int(alpha * fade)
    a = ang + math.sin(t * 1.3 + phase) * 0.07
    ext = 0.18 + 1.05 * life                         # stretches further out over its life
    grow = 0.4 + 0.95 * life                         # ...and gets bigger
    grab = min(1.0, life * 1.7)                      # hand closes as it stretches to grab
    sd, sh_hi = (*_YK_SHADOW, armA), (*_YK_SHADOW_HI, armA)
    sh = (cx + math.cos(ang) * reach * 0.1, cy + math.sin(ang) * reach * 0.1)
    hand = (cx + math.cos(a) * reach * ext, cy + math.sin(a) * reach * ext)
    # Smooth curved arm: a quadratic bezier that bows early and straightens as it
    # stretches out.
    perp = (-math.sin(a), math.cos(a))
    bend = reach * (0.26 - 0.16 * life) * side
    ctrl = ((sh[0] + hand[0]) / 2 + perp[0] * bend, (sh[1] + hand[1]) / 2 + perp[1] * bend)
    m = 9
    path = []
    for i in range(m + 1):
        u = i / m
        path.append(((1 - u) ** 2 * sh[0] + 2 * (1 - u) * u * ctrl[0] + u * u * hand[0],
                     (1 - u) ** 2 * sh[1] + 2 * (1 - u) * u * ctrl[1] + u * u * hand[1]))
    base_w = max(1.5, scale * 3.2 * grow)
    for i in range(m):
        u = i / m
        w = max(1, int(round(base_w * (1 - 0.62 * u))))   # thick shoulder -> thin wrist
        p0 = (int(path[i][0]), int(path[i][1]))
        p1 = (int(path[i + 1][0]), int(path[i + 1][1]))
        pygame.draw.line(surf, sh_hi, p0, p1, w + 1)
        pygame.draw.line(surf, sd, p0, p1, w)
    # Grabbing hand: three curved fingers + a thumb, curling with `grab`.
    ha = math.atan2(hand[1] - path[-2][1], hand[0] - path[-2][0])
    fl = reach * 0.22 * grow
    fw = max(1, int(base_w * 0.55))
    for fa, fr in ((-30, 0.85), (0, 1.0), (30, 0.85), (78, 0.6)):
        sgn = 1 if fa >= 0 else -1
        a2 = ha + math.radians(fa) - sgn * grab * 0.55
        k1 = (hand[0] + math.cos(a2) * fl * fr * 0.55, hand[1] + math.sin(a2) * fl * fr * 0.55)
        a3 = a2 - sgn * (0.25 + grab * 0.9)
        tip = (k1[0] + math.cos(a3) * fl * fr * 0.5, k1[1] + math.sin(a3) * fl * fr * 0.5)
        pygame.draw.lines(surf, sd, False,
                          [(int(hand[0]), int(hand[1])), (int(k1[0]), int(k1[1])),
                           (int(tip[0]), int(tip[1]))], fw)
        if lit:
            try:
                surf.set_at((int(tip[0]), int(tip[1])), (*_YK_MHI, armA))
            except (IndexError, ValueError):
                pass


def _yk_orb(surf, cx, cy, r, vis, seed, t):
    """A shed SOUL-ORB in the wake: a small glowing gold clot with a mask or two
    floating in it, fading out behind the King. Quiet light -- no arms of its
    own (the main body tells the grabbing story)."""
    if vis <= 0.04:
        return
    _yk_radial(surf, cx, cy, int(r * 2.4), _YK_T1, int(34 * vis))   # warm orange aura
    _yk_radial(surf, cx, cy, int(r * 1.8), _YK_GOLD, int(46 * vis))
    _yk_radial(surf, cx, cy, int(r * 1.05), _YK_T2, int(58 * vis))
    _yk_radial(surf, cx, cy, int(r * 0.62), _YK_T3, int(72 * vis))
    _yk_radial(surf, cx, cy, int(r * 0.32), _YK_T4, int(88 * vis))
    kinds = ("plain", "scream", "hollow", "crack")
    for k in range(2 if r >= 9 else 1):
        ang = seed * 1.7 + k * 2.4 + t * 1.4
        rad = r * 0.36
        _yk_mask(surf, cx + math.cos(ang) * rad, cy + math.sin(ang) * rad,
                 max(3, int(r * 0.44)), vis * 0.9, kinds[(seed + k) % 4])


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


def _yk_void(layer, cx, cy, R):
    """The barely-existing form, seen while the King is still far: a void darker
    than the dark, edged in a cold shimmer, and DEAD STILL. The only thing that
    moves or shows a face is the pale mask, drawn over this by the caller."""
    _yk_radial(layer, cx, cy, int(R * 1.4), (58, 62, 86), 50)    # cold shimmer rim
    subs = [(0, 0), (-0.4, -0.18), (0.4, -0.12), (-0.12, 0.4),
            (0.22, 0.32), (-0.3, 0.2), (0.12, -0.34)]
    for ox, oy in subs:                                          # static lumps -- no swirl
        pygame.draw.circle(layer, (8, 7, 12),
                           (int(cx + ox * R * 0.6), int(cy + oy * R * 0.9)), int(R * 0.58), 0)


def _draw_king(surf, x, y, facing, t, birth, gait, threat=None):
    """THE KING IN YELLOW (see header). `birth` (0..1, already de-None'd by the
    dispatch) drives the rift eruption; `t` animates; `gait` is accepted but the
    float needs no leg cycle. `threat` (0..1, the player's nearness to death)
    drives the calm->frenzy escalation: how many faces erupt, how bright it
    flares, how far and fast the arms haul. It never phases out."""
    global _YK_TRAIL
    R = 22
    intensity = 0.85 if threat is None else max(0.0, min(1.0, threat))
    # How much of the King has bled into the world (0 = dark void, 1 = full
    # blaze). Blooms late so the approach stays dreadful and the blaze is sudden.
    mr = max(0.0, min(1.0, (intensity - _YK_BLOOM_LO) / (_YK_BLOOM_HI - _YK_BLOOM_LO)))
    manifest = mr * mr * (3 - 2 * mr)
    mcx, mcy = x, int(y - 42 + math.sin(t * 1.1) * 3)        # floats above the feet
    bp = 1.0 if birth is None else max(0.0, min(1.0, birth))
    grow = bp * bp * (3 - 2 * bp)                            # body eases in
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
    while disp > 0.4 and _YK_ACC[0] >= 8:                    # space the orbs along the path
        _YK_ACC[0] -= 8
        _YK_PARTS.append({
            "kind": "orb", "seed": _YK_PRNG.randint(0, 999),
            "x": mcx + _YK_PRNG.uniform(-5, 5), "y": mcy + _YK_PRNG.uniform(-5, 5),
            "vx": bvx * 9 + _YK_PRNG.uniform(-8, 8),
            "vy": bvy * 9 + _YK_PRNG.uniform(-8, 8),
            "age": 0.0, "life": _YK_PRNG.uniform(1.8, 2.8),
            "r": _YK_PRNG.uniform(7, 15)})
        for _ in range(2):
            _YK_PARTS.append({
                "kind": "mote", "seed": 0,
                "x": mcx + _YK_PRNG.uniform(-9, 9), "y": mcy + _YK_PRNG.uniform(-9, 9),
                "vx": bvx * 18 + _YK_PRNG.uniform(-16, 16),
                "vy": bvy * 18 + _YK_PRNG.uniform(-16, 16),
                "age": 0.0, "life": _YK_PRNG.uniform(0.7, 1.2),
                "r": _YK_PRNG.uniform(1.5, 3.0)})
    if len(_YK_PARTS) > 160:
        del _YK_PARTS[:len(_YK_PARTS) - 160]
    keep = []
    for p in _YK_PARTS:
        p["age"] += dt
        fr = p["age"] / p["life"]
        if fr >= 1.0:
            continue
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        a = (1.0 - fr) * manifest                    # no trail while it's a dark void
        if p["kind"] == "orb":
            _yk_orb(surf, p["x"], p["y"], p["r"] * (1 - 0.22 * fr), a, p["seed"], t)
        else:
            mr = max(2, p["r"] * (1 - 0.4 * fr))
            _yk_radial(surf, p["x"], p["y"], int(mr * 2.6), _YK_T1, int(60 * a))  # orange glow
            _yk_radial(surf, p["x"], p["y"], mr, _YK_GOLD, int(150 * a))
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
    va = max(0.05, valpha)
    dark_a = 1.0 - manifest
    # The PRIMARY mask: one steady face anchored as the "head", turned to track
    # the player. It is the first thing to exist (a pale mask in the void),
    # serene while the King is calm, and the scream the chorus erupts around as
    # it closes -- the same object the whole way, just becoming more real.
    hx = cx + fb[0] * 1.8
    hy = cy - R * 0.12 + fb[1] * 1.8
    # Vacuous void eyes throughout; serene mouth while calm, and a black-weeping
    # wail once it rouses to manifest.
    pmk = "wail" if intensity >= 0.5 else "vacant"
    pfr = max(7, int(10 * max(0.3, grow)))
    # Motion sync: it hauls itself toward the aim as an arm completes its
    # stretch -- but only once it exists; dead still while a void.
    arm_speed = 0.32 + 0.4 * intensity                      # slow, deliberate reach
    surge = R * (0.12 + 0.28 * intensity) * grow * manifest * (
        math.exp(-((((t * arm_speed) % 1.0) - 0.68) / 0.15) ** 2)
        + math.exp(-((((t * arm_speed + 0.5) % 1.0) - 0.68) / 0.15) ** 2))
    sxo, syo = int(math.cos(aa) * surge), int(math.sin(aa) * surge)
    # --- Two slow MAIN arms FIRST so they sit BEHIND the rest of the sprite,
    # rooting from offset spots low on the body (not the face) and reaching out
    # past the glow. They grow out only as it manifests, hand over hand.
    if manifest > 0.05 and grow > 0.1:
        arms = pygame.Surface((L, L), pygame.SRCALPHA)
        reach = R * (1.4 + 1.4 * intensity) * grow
        ascale = max(1.0, grow * (1.0 + 0.4 * intensity))
        _yk_grab_arm(arms, cx - R * 0.55, cy + R * 0.32, aa - 0.42, reach, t, 0.0,
                     ascale, True, side=-1, speed=arm_speed)
        _yk_grab_arm(arms, cx + R * 0.5, cy + R * 0.55, aa + 0.28, reach, t, 0.5,
                     ascale, True, side=1, speed=arm_speed)
        arms.set_alpha(int(235 * va * manifest))
        surf.blit(arms, (mcx - cx + sxo, mcy - cy + syo))
    # --- VOID form (dominant while far): a still dark mass + a faint pale mask.
    if dark_a > 0.02 and grow > 0.1:
        void = pygame.Surface((L, L), pygame.SRCALPHA)
        _yk_void(void, cx, cy, int(R * max(0.4, grow)))
        _yk_mask(void, hx, hy, pfr, 0.72, pmk)              # ashen mask, watching
        void.set_alpha(int(235 * dark_a * va))
        surf.blit(void, (mcx - cx, mcy - cy))               # the void doesn't lurch
    # --- MANIFEST form (blooms in as it closes): light, the mask, the chorus.
    if manifest > 0.01:
        if bp < 1.0:
            _yk_birth_rift(surf, mcx, mcy, R, bp)
        _yk_glow(layer, cx, cy, R * max(0.18, grow), t)
        if intensity > 0.6:                                 # roused: white-hot flare
            _yk_radial(layer, cx, cy, int(R * (0.6 + 0.5 * intensity)), _YK_WHITE,
                       int(95 * (intensity - 0.6) / 0.4))
        nfaces = int(round(manifest * (len(_YK_FACES) - 1)))  # chorus erupts around it
        for fi in range(1, 1 + nfaces):
            rn, ba, asp, fr, vsp, vph, kind = _YK_FACES[fi]
            ang = ba + t * asp
            rr = rn * (0.9 + 0.1 * math.sin(t * 0.8 + vph))
            fxp = cx + math.cos(ang) * R * 0.82 * rr * grow + fb[0]
            fyp = cy + math.sin(ang) * R * 0.95 * rr * grow + fb[1]
            if kind == "double":
                vis = max(0.0, min(1.0, (math.sin(t * vsp + vph) - 0.55) / 0.4))
            else:
                vis = max(0.0, min(1.0, 0.5 + 0.72 * math.sin(t * vsp + vph)))
            _yk_mask(layer, fxp, fyp, fr, vis * manifest, kind)
        _yk_mask(layer, hx, hy, pfr, 0.9, pmk)              # central mask ON TOP of the chorus
        layer.set_alpha(int(255 * va * manifest))
        surf.blit(layer, (mcx - cx + sxo, mcy - cy + syo))


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
        _yk_mask(surf, mx, my, r, vis, kinds[i % len(kinds)])

    # 5. The looming mask: rises from the core and swells to fill the
    #    screen -- the King's face closing over you.
    grow = 36 + min(1.0, t / 3.2) ** 1.4 * 152
    cvis = min(1.0, 0.55 + t / 3.0) * ramp
    _yk_radial(surf, w // 2, core_y, int(grow * 1.7), _YK_HOT, int(58 * ramp))
    _yk_mask(surf, w // 2, core_y, int(grow), cvis, "scream")

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
