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


def draw_player_sprite(surf, x, y, facing, walk_phase=0, armor=None,
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
    # Head
    pygame.draw.circle(surf, skin, (x, y - 12), 7)
    # Hair across the top
    pygame.draw.rect(surf, hair, (x - 7, y - 18, 14, 6))
    # Boots: walking animation
    leg_off = int(math.sin(walk_phase) * 2)
    pygame.draw.rect(surf, boots, (x - 6, y + 14, 5, 4 + max(0, -leg_off)))
    pygame.draw.rect(surf, boots, (x + 1, y + 14, 5, 4 + max(0, leg_off)))
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
# Pushed late on purpose: the blaze is a brief punctuation at the kill, not the
# bulk of the encounter. Most of the approach lives in the withheld void.
_YK_BLOOM_LO, _YK_BLOOM_HI = 0.6, 0.92
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
    # gold body, drawn opaque so it covers the centre. It SMOULDERS gold/pale
    # rather than blazing white -- the white-hot stab is added only on the lunge
    # (the flare punch in _draw_king), so darkness keeps the upper hand.
    for col, scl, grow in [(_YK_T3, 1.06, 3), (_YK_T3, 0.74, 1), (_YK_PALE, 0.36, 0)]:
        for ox, oy in subs:
            rx, ry = ox * ca - oy * sa, ox * sa + oy * ca
            pygame.draw.circle(layer, col,
                               (int(cx + rx * R * 0.6), int(cy + ry * R * 0.9)),
                               int(R * 0.5 * scl) + grow)
    for k in range(4):
        a = sw * 1.6 + k * 1.57
        _yk_radial(layer, cx + math.cos(a) * R * 0.42, cy + math.sin(a) * R * 0.42,
                   int(R * 0.36), _YK_GOLD, 34)
    _yk_radial(layer, cx, cy - 2, int(R * 0.42), _YK_PALE, 30)


# Slot/orb kind vocabulary -> facial expression. The faces read as people:
# a dead, pallid human face surfaces from the light, mostly shrieking.
_YK_EXPR = {"hollow": "gaunt", "crack": "scream", "plain": "calm"}


def _yk_face(m, mx, my, r, expr, detail, mouth=True):
    """A readable human face on mask-surface `m`: pallid oval lit upper-left,
    brow ridge, nose ridge, eyes + an expressive mouth. `detail` gates the
    eyes/brow/nose in as the mask surfaces (so it emerges as a blank pallid
    shape first); `mouth` gates the LOUD features (mouth, tears, crack)
    separately and later -- so a hollow, mouthless STARE precedes the scream."""
    hi, mid, lo, pit = _YK_MHI, _YK_MMID, _YK_MLO, _YK_MPIT
    rw, rh = r, int(r * 1.24)                             # a little oblong -- a head, not a ball
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
        if expr in ("vacant", "wail"):                   # deep OBLONG sockets (eye-shaped,
            w2 = max(2, int(ew * 1.7))                   # not round lenses), each holding a
            h2 = max(3, int(ew * 2.5))                   # golden gaze: a single pixel while
            for ex, ey in (eyl, eyr):                    # calm, flaring once angry
                pygame.draw.ellipse(m, pit, (int(ex - w2 / 2), int(ey - h2 / 2), w2, h2))
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
    if not mouth:                                        # hold on the hollow STARE:
        return                                           # mouth/tears/crack withheld
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
    elif expr == "vacant":                               # a gaping, downturned grimace -- :(
        gw = max(3, int(r * 0.52))
        gh = max(3, int(r * 0.5))
        gx, gy = int(mx - gw / 2), int(mym - r * 0.04)
        pygame.draw.ellipse(m, pit, (gx, gy, gw, gh))     # the open gape
        pygame.draw.line(m, pit, (gx + 1, int(gy + gh * 0.2)),               # corners
                         (int(mx - gw * 0.85), int(gy + gh * 0.95)), 1)      # pulled
        pygame.draw.line(m, pit, (gx + gw - 1, int(gy + gh * 0.2)),          # down into
                         (int(mx + gw * 0.85), int(gy + gh * 0.95)), 1)      # a frown
    elif expr == "smile":
        pts = [(mx - r * 0.4, mym - r * 0.1), (mx, mym + r * 0.2), (mx + r * 0.4, mym - r * 0.1)]
        pygame.draw.lines(m, pit, False, [(int(a), int(b)) for a, b in pts], 1)
    elif expr == "weep":
        pts = [(mx - r * 0.4, mym + r * 0.15), (mx, mym - r * 0.1), (mx + r * 0.4, mym + r * 0.15)]
        pygame.draw.lines(m, pit, False, [(int(a), int(b)) for a, b in pts], 1)
    else:
        pygame.draw.line(m, pit, (int(mx - r * 0.3), int(mym)), (int(mx + r * 0.3), int(mym)), 1)
    if expr in ("vacant", "wail"):                       # a jagged fracture down one side --
        crk = [(mx + r * 0.12, my - rh * 0.92), (mx + r * 0.32, my - r * 0.2),
               (mx + r * 0.14, my + r * 0.45), (mx + r * 0.3, my + rh * 0.6)]
        pygame.draw.lines(m, pit, False, [(int(a), int(b)) for a, b in crk], 1)


def _yk_mask(surf, cx, cy, r, vis, kind, mouth=True):
    """A dead human FACE surfacing from the light: pallid, translucent (the glow
    reads through it) + a luminous halo, rising (vis->1) and dissolving back into
    the glow (vis->0). 'double' is two faces fused, both shrieking. `mouth=False`
    holds the face on a mouthless stare even after the eyes have resolved."""
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
            _yk_face(m, mx + ddx, my, max(2, int(r * 0.78)), "scream", detail, mouth)
    else:
        _yk_face(m, mx, my, r, _YK_EXPR.get(kind, kind), detail, mouth)
    m.set_alpha(int(64 + 156 * vis))
    surf.blit(m, (cx - mx, cy - my))


# A shed SOUL-ORB in the wake is drawn in two passes (glow, then faces) so that
# every orb's masks sit on top of every orb's glow, regardless of shed order.
_YK_ORB_KINDS = ("plain", "scream", "hollow", "crack")


def _yk_orb_glow(surf, cx, cy, r, vis):
    """The orb's glowing gold clot (no faces) -- a small copy of the body."""
    if vis <= 0.04:
        return
    _yk_radial(surf, cx, cy, int(r * 2.4), _YK_T1, int(34 * vis))   # warm orange aura
    _yk_radial(surf, cx, cy, int(r * 1.8), _YK_GOLD, int(46 * vis))
    _yk_radial(surf, cx, cy, int(r * 1.05), _YK_T2, int(58 * vis))
    _yk_radial(surf, cx, cy, int(r * 0.62), _YK_T3, int(72 * vis))
    _yk_radial(surf, cx, cy, int(r * 0.32), _YK_T4, int(88 * vis))


def _yk_orb_faces(surf, cx, cy, r, vis, seed, t):
    """The mask(s) floating in the orb -- drawn in the second pass so they read
    over the whole wake of glow, not just their own orb."""
    if vis <= 0.04:
        return
    for k in range(2 if r >= 9 else 1):
        ang = seed * 1.7 + k * 2.4 + t * 1.4
        rad = r * 0.36
        _yk_mask(surf, cx + math.cos(ang) * rad, cy + math.sin(ang) * rad,
                 max(3, int(r * 0.44)), vis * 0.9, _YK_ORB_KINDS[(seed + k) % 4])


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


def _yk_spire(layer, bx, by, ang, length, R, t, idx, m, dk, gold, hot):
    """One spire of the crown: a bold black/gold bent arm (shoulder -> reflex
    elbow -> grasping claw) rising from the circlet as a crown point. Stable
    (always present -- a crown, not a flicker), with a slow sway and grasp."""
    a = ang + math.sin(t * 0.9 + idx * 1.1) * 0.09
    perp = (-math.sin(a), math.cos(a))
    bend = length * 0.22 * (1 if idx % 2 else -1)
    mid = (bx + math.cos(a) * length * 0.55, by + math.sin(a) * length * 0.55)
    elbow = (mid[0] + perp[0] * bend, mid[1] + perp[1] * bend)
    hand = (bx + math.cos(a) * length, by + math.sin(a) * length)
    ip = [(int(bx), int(by)), (int(elbow[0]), int(elbow[1])), (int(hand[0]), int(hand[1]))]
    w = max(2, int(R * 0.14))
    for px, py in ip:                                            # gold under-glow
        _yk_radial(layer, px, py, w + 1, _YK_GOLD, int(85 * m))
    pygame.draw.lines(layer, gold, False, ip, w + 1)             # gold edge
    pygame.draw.lines(layer, dk, False, ip, w)                   # black core
    grab = 0.4 + 0.45 * (0.5 + 0.5 * math.sin(t * 0.7 + idx * 0.8))
    ha = math.atan2(hand[1] - elbow[1], hand[0] - elbow[0])
    fl = length * 0.34
    for fa in (-38, 0, 38):                                      # grasping claw at the tip
        a2 = ha + math.radians(fa) - (1 if fa >= 0 else -1) * grab * 0.7
        tip = (hand[0] + math.cos(a2) * fl, hand[1] + math.sin(a2) * fl)
        pygame.draw.line(layer, dk, (int(hand[0]), int(hand[1])),
                         (int(tip[0]), int(tip[1])), max(1, w - 1))
        try:
            layer.set_at((int(tip[0]), int(tip[1])), hot)
        except (IndexError, ValueError):
            pass


def _yk_shatter_mask(surf, cx, cy, r, vis, kind, crack, t, R, aim=0.0, arms=True):
    """THE SILHOUETTE: the mask. Intact when calm, but as the King rouses it
    CRACKS and splits into shards that drift apart -- the grasping arms burst
    from the splits and span the gaps, the light blazing through the cracks. A
    broken face barely held together by the limbs inside it. `crack` also runs
    in REVERSE at birth (shards converging into the whole mask); `arms` is off
    then, so the birth is a clean assembly with no grasping."""
    if vis <= 0.03:
        return
    cx, cy, r = int(cx), int(cy), int(r)
    _yk_radial(surf, cx, cy, r + 3, _YK_HOT, int(36 * vis))
    pad = max(6, r)
    S = (r + pad) * 2
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    mxc = myc = r + pad
    # The mouth/scream is held back until the mask is genuinely cracking open --
    # the stare comes first, the scream is the late reveal.
    _yk_face(m, mxc, myc, r, _YK_EXPR.get(kind, kind), vis > 0.35, crack > 0.45)
    alpha = int(64 + 156 * vis)
    if crack <= 0.04:                                   # intact mask
        m.set_alpha(alpha)
        surf.blit(m, (cx - mxc, cy - myc))
        return
    n = 7
    n_arms = 4                                               # FEW arms -- deliberate, not a thicket
    dk, gold, hot = (*_YK_SHADOW, 255), (*_YK_GOLD, 255), (*_YK_HOT, 255)
    # A FEW arms root around the mass and reach SLOWLY for the player: a long,
    # deliberate stretch out and an equally slow draw back, each on its own
    # unhurried cycle. The closer it gets (crack -> 1) the further each reaches.
    # Suppressed during the birth assembly.
    for i in range(n_arms if arms else 0):
        rho = i * math.tau / n_arms + 0.5 * math.sin(i * 2.3)    # roots scattered around
        rx = cx + math.cos(rho) * r * 0.55
        ry = cy + math.sin(rho) * r * 0.55
        spd = 0.26 + 0.07 * (i % 3)                              # slow, each a little different
        ph = (t * spd + i * 0.41) % 1.0
        if ph < 0.5:                                             # slow, deliberate reach out
            u = ph / 0.5; lunge = u * u * (3 - 2 * u)
        else:                                                    # slow draw back
            u = (ph - 0.5) / 0.5; lunge = 1.0 - u * u * (3 - 2 * u)
        ln = r * (0.5 + (1.0 + 1.2 * crack) * lunge)             # reaches further up close
        ang = aim + math.sin(i * 1.7) * 0.4                      # each aimed near the player
        _yk_spire(surf, rx, ry, ang, ln, R, t, i, 1.0, dk, gold, hot)
    far = (r + pad) * 1.7
    off = r * 0.7 * crack                                # shards drift apart
    for i in range(n):
        a0 = i * math.tau / n
        bis = a0 + math.pi / n
        a1 = (i + 1) * math.tau / n
        poly = [(mxc, myc),
                (mxc + math.cos(a0) * far, myc + math.sin(a0) * far),
                (mxc + math.cos(bis) * far, myc + math.sin(bis) * far),
                (mxc + math.cos(a1) * far, myc + math.sin(a1) * far)]
        pm = pygame.Surface((S, S), pygame.SRCALPHA)
        pygame.draw.polygon(pm, (255, 255, 255, 255), [(int(x), int(y)) for x, y in poly])
        shard = m.copy()
        shard.blit(pm, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        shard.set_alpha(alpha)
        surf.blit(shard, (int(cx - mxc + math.cos(bis) * off),
                          int(cy - myc + math.sin(bis) * off)))


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
    # BIRTH: the King flashes into being mid-birth (visible regardless of how
    # near the player is), and the mask ASSEMBLES from scattered shards as it
    # forms -- the exact reverse of how it shatters when it gets mad.
    birth_vis = grow * (1.0 - grow) * 4.0                    # visible while it assembles
    ignite = max(0.0, (0.26 - bp) / 0.26)                   # a quick ignition flash, up front
    # Birth glow is kept low so the loud orb-cloud recedes and the quiet
    # shard-assembly of the mask is what reads -- a coalescing, not a firework.
    show = min(1.0, manifest + 0.5 * birth_vis + ignite)    # existence: threat OR birth
    # Birth runs the shatter in REVERSE: shards converge into the WHOLE mask,
    # always resolving to the calm intact face regardless of threat. Only once
    # fully formed does the threat actually crack it (and bring out the arms).
    # Crack LAGS the bloom: the mask first blooms INTACT (the void face becoming
    # real), and only shatters once it's mostly manifest -- so the calm void face
    # has faded before the shards appear, never a whole-face-behind-shards double.
    if bp >= 1.0:
        cm = max(0.0, (manifest - 0.45) / 0.55)
        crack = cm * cm * (3 - 2 * cm)
    else:
        crack = (1.0 - grow) * 2.2
    arms_on = bp >= 1.0 and crack > 0.05
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
    # BIRTH: it is ASSEMBLING, so soul-orbs are pulled INWARD -- they spawn out
    # at the perimeter and stream toward the mask to form it (not vomited out).
    if bp < 0.55:
        for _ in range(2):
            ang = _YK_PRNG.uniform(0, math.tau)
            dist = _YK_PRNG.uniform(R * 1.6, R * 3.0)
            spd = _YK_PRNG.uniform(50, 130)
            orb = _YK_PRNG.random() < 0.10          # mostly faint motes, few orbs
            _YK_PARTS.append({
                "kind": "orb" if orb else "mote", "seed": _YK_PRNG.randint(0, 999),
                "birth": True,                       # coalescence -> dim, faceless
                "x": mcx + math.cos(ang) * dist, "y": mcy + math.sin(ang) * dist,
                "vx": -math.cos(ang) * spd, "vy": -math.sin(ang) * spd,   # toward the mask
                "age": 0.0, "life": dist / spd,                           # arrives ~as it fades
                "r": _YK_PRNG.uniform(5, 9) if orb else _YK_PRNG.uniform(2, 4)})
    disp = math.hypot(mcx - _YK_TRAIL[-1][0], mcy - _YK_TRAIL[-1][1]) if _YK_TRAIL else 0.0
    _YK_TRAIL.append((mcx, mcy, t))
    _YK_TRAIL = _YK_TRAIL[-5:]
    tvx, tvy = (mcx - _YK_TRAIL[0][0], mcy - _YK_TRAIL[0][1])
    tl = math.hypot(tvx, tvy) or 1.0
    bvx, bvy = -tvx / tl, -tvy / tl
    # The wake of shed soul-orbs only trails once he has AWAKENED (the bloom has
    # begun). While a calm void he is JUST a mask -- no trail, however he drifts.
    awakened = manifest > 0.05
    if awakened:
        _YK_ACC[0] += disp
    else:
        _YK_ACC[0] = 0.0
    while awakened and disp > 0.4 and _YK_ACC[0] >= 12:      # space the orbs along the path
        _YK_ACC[0] -= 12
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
        keep.append((p, fr, (1.0 - fr) * show))      # a: no trail while it's a dark void
    _YK_PARTS[:] = [p for p, _, _ in keep]
    # Pass 1: lay down ALL the glow particles first...
    for p, fr, a in keep:
        if a <= 0.01:
            continue
        wdim = 0.4 if p.get("birth") else 0.42              # wake dimmed to match the head
        if p["kind"] == "orb":
            _yk_orb_glow(surf, p["x"], p["y"], p["r"] * (1 - 0.22 * fr), a * wdim)
        else:
            mr = max(2, p["r"] * (1 - 0.4 * fr))
            _yk_radial(surf, p["x"], p["y"], int(mr * 2.6), _YK_T1, int(60 * a * wdim))  # orange glow
            _yk_radial(surf, p["x"], p["y"], mr, _YK_GOLD, int(150 * a * wdim))
    # ...Pass 2: then every orb's masks on top, so no later glow buries them. Birth
    # orbs stay FACELESS (a quiet coalescence); the wake faces are KEPT -- the
    # implied victims -- but dimmed so the trail sits behind the head.
    for p, fr, a in keep:
        if p["kind"] == "orb" and a > 0.04 and not p.get("birth"):
            _yk_orb_faces(surf, p["x"], p["y"], p["r"] * (1 - 0.22 * fr), a * 0.8, p["seed"], t)
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
    va = max(0.05, valpha)
    dark_a = 1.0 - show
    # The PRIMARY mask: one steady face anchored as the "head", turned to track
    # the player. It is the first thing to exist (a pale mask in the void),
    # serene while the King is calm, and the scream the chorus erupts around as
    # it closes -- the same object the whole way, just becoming more real.
    hx = cx + fb[0] * 1.8
    hy = cy - R * 0.12 + fb[1] * 1.8
    # Vacuous void eyes throughout; serene mouth while calm, and a black-weeping
    # wail once it rouses to manifest.
    pmk = ("wail" if intensity >= 0.82 else "vacant") if bp >= 1.0 else "vacant"
    pfr = max(7, int(10 * max(0.3, grow)))
    # Motion sync: it hauls itself toward the aim as an arm completes its
    # stretch -- but only once it exists; dead still while a void.
    arm_speed = 0.32 + 0.4 * intensity                      # slow, deliberate reach
    lunge_env = (math.exp(-((((t * arm_speed) % 1.0) - 0.68) / 0.15) ** 2)
                 + math.exp(-((((t * arm_speed + 0.5) % 1.0) - 0.68) / 0.15) ** 2))
    surge = R * (0.12 + 0.28 * intensity) * grow * manifest * lunge_env
    sxo, syo = int(math.cos(aa) * surge), int(math.sin(aa) * surge)
    # A RARE, narrow white-hot stab -- one slow pulse, near-dark between, so full
    # brightness is a brief punctuation rather than the resting state.
    fph = (t * (0.16 + 0.12 * intensity)) % 1.0
    flare = math.exp(-((fph - 0.5) / 0.045) ** 2)
    # --- VOID form (dominant while far): a still dark mass + a faint pale mask.
    # Fades out by the time the bloom takes hold (show ~0.5), well before the
    # mask cracks -- so the whole calm face is gone before the shards show.
    void_fade = max(0.0, 1.0 - show / 0.5)
    if void_fade > 0.02 and grow > 0.1:
        void = pygame.Surface((L, L), pygame.SRCALPHA)
        _yk_void(void, cx, cy, int(R * max(0.4, grow)))
        # The ashen mask is THE thing watching from the void -- present and
        # readable the whole way (hollow eyes, no scream), just fainter far off
        # and firmer as he nears. Its MOUTH is withheld (mouth=False): a calm,
        # vacant, watching stare, never a shriek while he's still a void. The
        # scream is held for the break, when the mask actually cracks open.
        vmask = 0.6 + 0.18 * intensity
        _yk_mask(void, hx, hy, pfr, vmask, pmk, mouth=False)  # ashen mask, watching
        void.set_alpha(int(235 * void_fade * va))
        # Move with the SAME lurch offset as the manifest layer: the void and
        # the manifest are one head, so they must stay aligned -- otherwise the
        # calm void face and the manifest face read as TWO masks during the
        # crossfade. Surge is ~0 while far (manifest 0), so it's still then.
        surf.blit(void, (mcx - cx + sxo, mcy - cy + syo))
    # --- MANIFEST form (blooms in as it closes, and flashes in at birth).
    if show > 0.01:
        # Golden light SIZED TO THE MASK, sitting inside it -- so it reads as
        # light leaking FROM the mask: hidden when whole, blazing through the
        # cracks as it splits.
        _yk_glow(layer, hx, hy, max(6, int(pfr * 1.2)), t)
        # Birth ignition: a mask-scale white flash up front, before it assembles.
        if ignite > 0.02:
            _yk_radial(layer, hx, hy, int(pfr * (1.0 + 0.7 * ignite)),
                       _YK_WHITE, int(110 * ignite))
        # The white-hot core is a brief PUNCTUATION, not a constant glare: it
        # stabs only as he lunges (the same envelope that hauls the arms), so
        # the body mostly smoulders gold and full brightness stays rare.
        if intensity > 0.6 and flare > 0.04:
            _yk_radial(layer, hx, hy, int(pfr * (0.55 + 0.45 * intensity)), _YK_WHITE,
                       int(78 * (intensity - 0.6) / 0.4 * flare))
        # THE OTHER mask, directly behind -- a screaming face glimpsed through
        # the cracks once the front one splits open. Withheld until the cracks
        # actually open, so the scream is a reveal, not an ever-present chorus.
        _yk_mask(layer, hx, hy, pfr, min(1.0, max(0.0, crack - 0.3) * 1.5), "scream")
        # THE MASK -- our silhouette. Assembles from shards at birth, intact when
        # calm, and splits apart as it rouses -- the grasping arms bursting from
        # the splits and reaching toward the player.
        _yk_shatter_mask(layer, hx, hy, pfr, 0.92, pmk, crack, t, R * max(0.3, grow), aa, arms_on)
        layer.set_alpha(int(255 * va * show))
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


# ---- The Carcosa tableau: the rite_broken explosion ending --------------
# Distinct from draw_king_death (the King catching YOU). This is the rite
# torn down with the source still open (NARRATIVE §6): the King erupts as a
# TREE OF THE TAKEN -- every branch hung with a face He now wears -- and His
# influence floods DOWN and OUT over the drowned town. A wholly procedural
# homage in the Yellow palette; `t` = seconds since the break (held ~7s).
_CARCOSA_FACEKINDS = ("wail", "vacant", "gaunt", "hollow")


def _carcosa_branch(surf, x, y, ang, length, depth, grow, t, seed, masks,
                    cx0, cy0):
    """One recursive black tendril of the King's tree. Extends with `grow`
    (0..1) so the tree erupts over time, sways on a per-branch phase, and
    drops mask-anchors (x, y, r, seed) of WILDLY varied size along it (never
    piled at the core `cx0,cy0`) for faces drawn on top afterward."""
    if depth <= 0 or length < 6.0:
        return
    L = length * grow
    a = ang + math.sin(t * 0.6 + seed * 0.9) * 0.12
    x2 = x + math.cos(a) * L
    y2 = y + math.sin(a) * L
    pygame.draw.line(surf, (9, 7, 6), (int(x), int(y)), (int(x2), int(y2)),
                     max(2, depth + 1))                       # bold tendrils
    if depth <= 4 and grow > 0.18 and len(masks) < 130 \
            and _frand(seed + 9) > 0.7 \
            and math.hypot(x2 - cx0, y2 - cy0) > 60:          # not at the core
        r = int((3 + depth * 3) * (0.55 + 1.8 * _frand(seed + 11)))  # tiny..big
        masks.append((x2, y2, max(4, r), seed))
    branches = 2 if _frand(seed) > 0.4 else 3
    spread = 0.40 + 0.34 * _frand(seed + 1)
    for k in range(branches):
        na = a + (k - (branches - 1) / 2.0) * spread \
            + (_frand(seed + k + 7) - 0.5) * 0.42              # gnarlier
        _carcosa_branch(surf, x2, y2, na,
                        length * (0.64 + 0.12 * _frand(seed + k + 3)),
                        depth - 1, grow, t, seed * 3 + k + 5, masks, cx0, cy0)


def _carcosa_town(surf, w, h, base_y, t, flood):
    """A drowned gothic skyline along `base_y` with a rippling reflection
    below it, the King's gold light flooding down through and over it."""
    # A low horizon backlight so the skyline silhouettes read -- FILLED with
    # per-pixel alpha (composited, not additive) so it can't blow out into a
    # disc the way _yk_radial does. Brightens toward the waterline.
    bh_ = int(h * 0.26)
    band = pygame.Surface((w, bh_), pygame.SRCALPHA)
    for yy in range(bh_):
        a = int(64 * (yy / bh_) ** 1.6 * flood)
        if a > 0:
            pygame.draw.line(band, (96, 78, 32, a), (0, yy), (w, yy))
    surf.blit(band, (0, base_y - bh_ + 8))
    _yk_radial(surf, w // 2, base_y + 18, int(w * 0.08), _YK_HOT,
               int(9 * flood))     # a small glint on the water
    roofs = []
    x, i = -6, 0
    while x < w + 6:
        bw = 16 + int(30 * _frand(i * 3 + 1))
        bh = 16 + int(52 * _frand(i * 3 + 2))
        steeple = _frand(i * 3 + 5) > 0.78
        roofs.append((x, bw, bh))
        pygame.draw.rect(surf, (5, 5, 8), (x, base_y - bh, bw, bh + 80))
        pygame.draw.polygon(surf, (5, 5, 8),
                            [(x - 2, base_y - bh), (x + bw // 2, base_y - bh - 12),
                             (x + bw + 2, base_y - bh)])
        if steeple:
            sx = x + bw // 2
            pygame.draw.rect(surf, (5, 5, 8), (sx - 3, base_y - bh - 40, 6, 40))
            pygame.draw.polygon(surf, (5, 5, 8),
                                [(sx - 5, base_y - bh - 40), (sx, base_y - bh - 58),
                                 (sx + 5, base_y - bh - 40)])
        x += bw + 2
        i += 1
    for (rx, bw, bh) in roofs:                 # rippling reflection
        dx = int(math.sin(t * 1.1 + rx * 0.05) * 3)
        pygame.draw.rect(surf, (6, 6, 10), (rx + dx, base_y + 2, bw,
                                            int(bh * 0.72)))
    for k in range(7):                          # gold shimmer on the water
        a = int(30 * flood * (1 - k / 7.0) * (0.5 + 0.5 * math.sin(t * 2 + k)))
        if a <= 0:
            continue
        line = pygame.Surface((w, 2), pygame.SRCALPHA)
        line.fill((_YK_GOLD[0], _YK_GOLD[1], _YK_GOLD[2], a))
        surf.blit(line, (0, base_y + 5 + k * 7))


_CARCOSA_GRAIN = None


def _carcosa_post(surf, t):
    """Darkwood / Fear & Hunger grime applied to the whole cutscene frame so
    nothing reads as clean vector: chunky downsample, a muddy bile palette,
    animated dither-grain, a guttering flicker, and crushed edges."""
    w, h = surf.get_size()
    # Chunky downsample -> dirty low-res pixels (F&H grit).
    dw, dh = int(w / 2.5), int(h / 2.5)
    surf.blit(pygame.transform.scale(
        pygame.transform.smoothscale(surf, (dw, dh)), (w, h)), (0, 0))
    # Muddy the palette toward sick ochre/bile, but lightly -- keep the
    # sickly highlights bright against the dark (high contrast, not flat mud).
    tint = pygame.Surface((w, h))
    tint.fill((220, 210, 164))
    surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    grime = pygame.Surface((w, h), pygame.SRCALPHA)
    grime.fill((30, 34, 26, 14))
    surf.blit(grime, (0, 0))
    # Animated dither-grain (built once).
    global _CARCOSA_GRAIN
    if _CARCOSA_GRAIN is None:
        g = pygame.Surface((w, h), pygame.SRCALPHA)
        rg = random.Random(13)
        for _ in range(int(w * h * 0.11)):
            x, y = rg.randint(0, w - 1), rg.randint(0, h - 1)
            if rg.random() < 0.55:
                g.set_at((x, y), (0, 0, 0, rg.randint(40, 95)))
            else:
                g.set_at((x, y), (190, 168, 116, rg.randint(20, 60)))
        _CARCOSA_GRAIN = g
    surf.blit(_CARCOSA_GRAIN, (random.randint(-2, 2), random.randint(-2, 2)))
    # Guttering flicker -- the light stutters (Darkwood).
    if random.random() < 0.10:
        d = pygame.Surface((w, h))
        d.fill((16, 14, 10))
        surf.blit(d, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    # Crushed edge vignette.
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(60):
        a = int(165 * (1 - i / 60) ** 1.6)
        pygame.draw.rect(vig, (0, 0, 0, a), (i, i, w - 2 * i, h - 2 * i), 1)
    surf.blit(vig, (0, 0))


def _draw_carcosa_axe(surf, hx, hy, ang):
    """The splitting axe mid-swing: a wood handle + a steel wedge head."""
    dx, dy = math.cos(ang), math.sin(ang)
    tail = (int(hx - dx * 200), int(hy - dy * 200))
    pygame.draw.line(surf, (26, 18, 11), (int(hx), int(hy)), tail, 9)
    pygame.draw.line(surf, (76, 54, 31), (int(hx), int(hy)), tail, 6)
    px, py = -dy, dx
    blade = [(int(hx + px * 5), int(hy + py * 5)),
             (int(hx + dx * 34 + px * 30), int(hy + dy * 34 + py * 30)),
             (int(hx + dx * 34 - px * 30), int(hy + dy * 34 - py * 30)),
             (int(hx - px * 5), int(hy - py * 5))]
    pygame.draw.polygon(surf, (42, 44, 50), blade)
    pygame.draw.polygon(surf, (168, 172, 180), blade, 2)


def draw_mask_yank(surf, t):
    """The act that breaks the rite (NARRATIVE §6): you SHATTER the Pallid
    Mask with your splitting axe -- the catastrophic 'tear it down'. Dread
    stillness, the axe swings in, the mask bursts into shards and the Sign
    bleeds, whiting out into the blast. `t` = seconds into the act (~3s)."""
    w, h = surf.get_size()
    cx, cy = w // 2, int(h * 0.46)
    impact = 1.6
    sh = max(0.0, t - impact)                      # time since the blow lands
    flare = max(0.0, (t - 2.55) / 0.45)
    shake = min(1.0, sh / 0.3) if sh > 0 else 0.04 * (t / impact)
    shx = int(math.sin(t * 64) * (2 + 20 * shake))
    shy = int(math.cos(t * 70) * (1 + 12 * shake))
    sx, sy = cx + shx, cy + shy

    surf.fill((9, 8, 11))
    for i in range(7):                             # cellar-wall stone seams
        yy = int(h * (0.12 + 0.12 * i)) + (i % 2) * 6
        pygame.draw.line(surf, (16, 14, 18), (0, yy), (w, yy + 4), 1)
    # The daubed Yellow Sign + the dark socket the mask sits in.
    glyph = [(sx, sy - 96), (sx - 9, sy - 32), (sx - 44, sy - 12),
             (sx - 15, sy + 20), (sx - 28, sy + 76), (sx + 7, sy + 32),
             (sx + 42, sy + 64), (sx + 19, sy + 9), (sx + 50, sy - 26),
             (sx + 11, sy - 28)]
    pygame.draw.lines(surf, (70, 56, 24), False,
                      [(int(a), int(b)) for a, b in glyph], 2)
    pygame.draw.ellipse(surf, (5, 4, 7), (sx - 60, sy - 78, 120, 156))
    hitstop = 0.07                                 # frozen frames on contact
    if sh <= hitstop:
        # Mask whole. Tremor builds; the axe rears back, HOLDS, then drops.
        trem = int(math.sin(t * 36) * 2 * (t / impact))
        # Swing timeline: enter+cock [0.55,1.05] -> anticipation HOLD
        # [1.05,1.35] -> fast accel drop [1.35,impact].
        cocked = (sx + 230, sy - 250)              # axe held high, off upper-right
        contact = (sx + 24, sy - 18)
        if t < 1.05:
            p = max(0.0, (t - 0.55) / 0.5)
            ax = sx + 470 - (470 - 230) * p        # slide in from off-screen
            ay = sy - 250
            hxx, hyy = int(ax), int(ay)
        elif t < 1.35:
            hxx, hyy = cocked                      # the held beat (dread)
            hyy += int(math.sin(t * 30) * 2)       # a small quiver
        else:
            sw = ((t - 1.35) / (impact - 1.35)) ** 2.4   # hard accelerating drop
            hxx = int(cocked[0] + (contact[0] - cocked[0]) * sw)
            hyy = int(cocked[1] + (contact[1] - cocked[1]) * sw)
        ang = math.atan2(contact[1] - cocked[1], contact[0] - cocked[0])
        if sh <= 0:
            ms = 130
            msurf = pygame.Surface((ms, ms), pygame.SRCALPHA)
            _yk_mask(msurf, ms // 2, ms // 2, 58, 1.0, "wail")
            surf.blit(msurf, msurf.get_rect(center=(sx + trem, sy)))
            _draw_carcosa_axe(surf, hxx, hyy, ang)
        else:
            # CONTACT held: axe buried, a hairline crack lights, white spark.
            ms = 130
            msurf = pygame.Surface((ms, ms), pygame.SRCALPHA)
            _yk_mask(msurf, ms // 2, ms // 2, 58, 1.0, "wail")
            surf.blit(msurf, msurf.get_rect(center=(sx, sy)))
            crk = [(sx + (_frand(c) - 0.5) * 16, sy - 70 + c * 24)
                   for c in range(7)]
            pygame.draw.lines(surf, (255, 248, 224), False,
                              [(int(a), int(b)) for a, b in crk], 2)
            _draw_carcosa_axe(surf, contact[0], contact[1], ang)
            _yk_radial(surf, contact[0], contact[1], 26, (255, 248, 224), 220)
    else:
        # SHATTERED: the mask SPLITS down the strike line into two halves that
        # fall apart under gravity, gore bursts from the Sign, debris rains.
        s = sh - hitstop
        _yk_radial(surf, sx, sy, int(50 + 80 * shake), (150, 30, 22),
                   int(28 + 46 * shake))
        for i in range(5):                         # red bleeding rakes
            a = (i / 5.0) * math.tau + 0.4
            ln = 60 + 200 * min(1.0, s * 1.4)
            pygame.draw.line(surf, (110, 26, 18), (sx, sy),
                             (int(sx + math.cos(a) * ln), int(sy + math.sin(a) * ln)),
                             max(1, int(3 * min(1.0, s * 2))))
        # the two halves of the mask, cleaved down the centre
        ms = 130
        msurf = pygame.Surface((ms, ms), pygame.SRCALPHA)
        _yk_mask(msurf, ms // 2, ms // 2, 58, 1.0, "wail")
        gap = int(s * 90)
        drop = int(s * s * 520)                    # gravity
        for side, srcx in ((-1, 0), (1, ms // 2)):
            half = msurf.subsurface((srcx, 0, ms // 2, ms)).copy()
            half = pygame.transform.rotozoom(half, -side * s * 30, 1.0)
            surf.blit(half, half.get_rect(center=(
                int(sx + side * (ms * 0.22 + gap)), int(sy + drop))))
        for i in range(9):                         # secondary debris, falling
            a = (i / 9.0) * math.tau + (_frand(i * 5) - 0.5) * 0.5
            d = s * (180 + 180 * _frand(i * 5 + 1))
            px = sx + math.cos(a) * d
            py = sy + math.sin(a) * d - s * 30 + s * s * 460   # arc then fall
            shard = pygame.Surface((40, 40), pygame.SRCALPHA)
            col = (206, 196, 156) if i % 3 else (54, 50, 36)
            pygame.draw.polygon(shard, col, [(20, 4), (34, 30), (7, 28)])
            shard = pygame.transform.rotozoom(
                shard, s * 460 * (1 if i % 2 else -1) + i * 29,
                0.4 + 0.6 * _frand(i * 5 + 2))
            surf.blit(shard, shard.get_rect(center=(int(px), int(py))))
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(56):
        a = int(170 * (1 - i / 56) ** 1.6)
        pygame.draw.rect(vig, (0, 0, 0, a), (i, i, w - 2 * i, h - 2 * i), 1)
    surf.blit(vig, (0, 0))
    if flare > 0.01:
        fl = pygame.Surface((w, h), pygame.SRCALPHA)
        fl.fill((255, 244, 212, int(255 * min(1.0, flare))))
        surf.blit(fl, (0, 0))
    _carcosa_post(surf, t)


def _carcosa_one_rift(surf, px, py, pr, op, t, seed, reach=1.0,
                      ha=None, hand=True):
    """One torn rift: the gold strike that split it, a dark tear with a hot
    red rim, and (optionally) a HAND of the taken clawing through, writhing.
    `ha` aims the reaching arm; default is downward/outward into the world."""
    pr = int(pr)
    if pr < 4 or op <= 0.03:
        return
    px, py = int(px), int(py)
    pygame.draw.line(surf, (184, 150, 72), (px, py - pr * 3),
                     (int(px + _frand(seed + 5) * 14 - 7), py), max(1, int(2 * op)))
    pygame.draw.ellipse(surf, (4, 4, 7),
                        (px - pr, int(py - pr * 1.3), pr * 2, int(pr * 2.6)))
    pygame.draw.ellipse(surf, (140, 36, 26),
                        (px - pr, int(py - pr * 1.3), pr * 2, int(pr * 2.6)),
                        max(1, int(2 * op)))
    if not hand:
        return
    if ha is None:
        ha = math.pi / 2 + math.sin(t * 2.0 + seed) * 0.5
    else:
        ha = ha + math.sin(t * 2.0 + seed) * 0.4
    wl = pr * (1.4 + 0.9 * op) * reach
    hx, hy = px + math.cos(ha) * wl, py + math.sin(ha) * wl
    aw = max(2, pr // 4)
    pygame.draw.line(surf, (62, 48, 22), (px, py), (int(hx), int(hy)), aw + 2)
    pygame.draw.line(surf, (8, 7, 10), (px, py), (int(hx), int(hy)), aw)
    for f in range(4):
        fa = ha + (f - 1.5) * 0.34 + math.sin(t * 3 + seed + f) * 0.06
        tx, ty = hx + math.cos(fa) * pr * 0.9, hy + math.sin(fa) * pr * 0.9
        pygame.draw.line(surf, (8, 7, 10), (int(hx), int(hy)),
                         (int(tx), int(ty)), max(1, aw // 2))


def _carcosa_portal_hands(surf, w, h, cx, cy, spread, t):
    """Rifts tear open across the dark -- a gold strike splits each, then a
    HAND of the taken claws through, reaching into the world. His influence
    pouring through holes in reality (replaces the lone reaching monster)."""
    for i in range(9):
        op = max(0.0, min(1.0, (spread - i * 0.045) / 0.45))   # staggered tear
        if op <= 0.03:
            continue
        a = (i * 0.618034) * math.tau % math.tau
        dist = (0.24 + 0.22 * _frand(i * 7 + 1)) * w
        px = cx + math.cos(a) * dist
        py = cy + math.sin(a) * dist * 0.6 - h * 0.04
        pr = (16 + 34 * _frand(i * 7 + 2)) * op
        _carcosa_one_rift(surf, px, py, pr, op, t, i * 7)


def _carcosa_facemask(surf, w, h, cx, cy, R, reveal, dilate, t):
    """His FACE, formed from the breach itself -- not a mask that zooms in.
    A dark head-silhouette looms over the lit cloud; its features are RIFTS:
    two vertical eye-sockets that burn with the golden gaze, a wide mouth-gash,
    gaunt cheek/brow hollows -- each a portal the taken claw out through. As
    `dilate` rises He inhales: the sockets widen, the gaze swells, the hands
    surge. The face arrives by the holes ARRANGING into Him, never by scaling."""
    R = max(8, int(R))
    rv = max(0.0, min(1.0, reveal))
    dl = max(0.0, min(1.0, dilate))
    if rv <= 0.02:
        return
    pulse = dl * (0.55 + 0.45 * math.sin(t * 1.7))      # the climactic inhale

    # The PALLID MASK itself -- the unmistakable bone face of the King, fixed in
    # scale (tied to the cap, never engulf), set into the smoke as His head. It
    # is drawn solid so it COVERS the busy cloud behind it: a clean face the eye
    # locks onto. Its eyes and mouth are the only thing that "arrives" -- the
    # rifts open INSIDE them and the hands of the taken claw out.
    rw, rh = int(R * 0.70), int(R * 0.92)
    pad = max(6, rw // 3)
    S = (rw + pad) * 2
    mm = pygame.Surface((S, S), pygame.SRCALPHA)
    mcx = mcy = rw + pad
    sway = math.sin(t * 1.1) * 0.02                      # a slow living tilt
    # bone face, shaded upper-left -> a head, not a disc
    pygame.draw.ellipse(mm, _YK_MLO, (mcx - rw + 2, mcy - rh + 2, 2 * rw, 2 * rh))
    pygame.draw.ellipse(mm, _YK_MMID, (mcx - rw, mcy - rh, 2 * rw, 2 * rh))
    pygame.draw.ellipse(mm, _YK_MHI,
                        (mcx - rw + 2, mcy - rh, max(2, 2 * rw - 5),
                         max(2, 2 * rh - 7)))
    # gaunt cheek shadows + nose ridge so it reads as a starved face
    for sgn in (-1, 1):
        pygame.draw.ellipse(mm, _YK_MLO,
                            (int(mcx + sgn * rw * 0.34 - rw * 0.22),
                             int(mcy + rh * 0.02),
                             int(rw * 0.44), int(rh * 0.5)))
    pygame.draw.line(mm, _YK_MLO, (mcx, int(mcy - rh * 0.28)),
                     (mcx, int(mcy + rh * 0.18)), max(1, rw // 18))
    mm.set_alpha(int(45 + 200 * rv))
    rot = pygame.transform.rotozoom(mm, math.degrees(sway), 1.0)
    surf.blit(rot, rot.get_rect(center=(cx, cy)))

    eye_sep = R * 0.40
    eye_y = cy - R * 0.16
    eyes = [(cx - eye_sep, eye_y), (cx + eye_sep, eye_y)]
    mouth = (cx, cy + R * 0.50)

    # THE EYE-SOCKETS: vertical oblong rifts torn into the bone, a gold gaze
    # burning at the back, hands clawing up/out, dilating with the inhale.
    socket_h = R * (0.30 + 0.08 * pulse)
    socket_w = R * (0.15 + 0.05 * pulse)
    for ei, (ex, ey) in enumerate(eyes):
        pygame.draw.ellipse(surf, _YK_MPIT,
                            (int(ex - socket_w), int(ey - socket_h),
                             int(socket_w * 2), int(socket_h * 2)))
        gzR = R * (0.08 + 0.09 * rv + 0.07 * pulse)
        _yk_radial(surf, ex, ey, int(gzR * 2.2), _YK_GOLD,
                   int(70 * rv), add=False)
        _yk_radial(surf, ex, ey, int(gzR), _YK_HOT,
                   int(160 * min(1.0, rv * 1.4)))
        for hsgn in (-0.5, 0.5):
            _carcosa_one_rift(surf, ex + socket_w * hsgn, ey - socket_h * 0.3,
                              socket_w * 1.0, rv, t, ei * 9 + int(hsgn * 4) + 3,
                              reach=1.1 + 0.7 * dl,
                              ha=-math.pi / 2 + hsgn * 0.6)

    # THE MOUTH-GASH: the widest breach, a torn maw spilling the most hands.
    mw = R * (0.40 + 0.12 * pulse)
    mh = R * (0.22 + 0.08 * pulse)
    pygame.draw.ellipse(surf, _YK_MPIT,
                        (int(mouth[0] - mw), int(mouth[1] - mh),
                         int(mw * 2), int(mh * 2)))
    pygame.draw.ellipse(surf, (120, 30, 22),
                        (int(mouth[0] - mw), int(mouth[1] - mh),
                         int(mw * 2), int(mh * 2)), max(1, int(2 + 2 * rv)))
    _yk_radial(surf, mouth[0], mouth[1], int(mw * 0.6), (150, 36, 24),
               int(44 * rv), add=False)
    # the black tears the wail-mask weeps, down from each socket
    for ex, _ in eyes:
        pygame.draw.line(surf, _YK_MPIT, (int(ex), int(eye_y + socket_h)),
                         (int(ex + R * 0.04), int(cy + rh)), max(2, int(R * 0.05)))
    nh = 5
    for j in range(nh):
        u = (j + 0.5) / nh
        hx = mouth[0] + (u - 0.5) * mw * 1.6
        _carcosa_one_rift(surf, hx, mouth[1], mw * 0.34, rv, t, 200 + j * 7,
                          reach=1.2 + 0.8 * dl,
                          ha=math.pi / 2 + (u - 0.5) * 0.8)


def draw_carcosa(surf, t, mode="spread"):
    """rite_broken: His influence DETONATES -- a mushroom cloud of the taken.
    A flash + shockwave + shake at ground zero (the town/well); a stem of
    tendrils and faces PUNCHES upward; it billows into a cap of branching
    tendrils studded with the King's masks, His face riding the crown. Reads
    as both a dead tree and a blast. `t` = seconds since the break."""
    w, h = surf.get_size()

    def eo(x):                                   # ease-out: explosive punch
        x = max(0.0, min(1.0, x))
        return 1.0 - (1.0 - x) ** 2.3
    ramp = max(0.0, min(1.0, t / 0.25))
    flash = max(0.0, 1.0 - t / 0.4)              # the detonation flash
    rise = eo((t - 0.10) / 0.95)                 # stem height 0..1 (fast)
    capg = eo((t - 0.75) / 2.2)                  # cap billow 0..1
    wave = max(0.0, min(1.0, (t - 0.35) / 2.6))  # gold wash over the town
    flick = 0.92 + 0.06 * math.sin(t * 9.0)
    shake = max(0.0, 1.0 - t / 0.85)
    shx = int(math.sin(t * 57.0) * 11 * shake)
    shy = int(math.cos(t * 63.0) * 8 * shake)
    kx = w // 2
    gz_y = int(h * 0.82)                          # ground zero (the town/well)
    cap_y = int(h * 0.30)                         # the cap / the crown
    stem_top = int(gz_y - rise * (gz_y - cap_y))
    spread = eo((t - 1.4) / 2.8)                  # the breach WIDENING outward
    engulf = eo((t - 4.2) / 2.6)                  # He INHALES + the gaze ignites
    capR = w * 0.30 * capg * (1.0 + 0.35 * spread)

    scene = pygame.Surface((w, h))
    scene.fill((4, 4, 7))

    # Backdrop halo, growing with the cap (filled, not additive: no sun).
    maxd = math.hypot(w * 0.42, h * 0.40)
    for i in range(24, 0, -1):
        f = i / 24
        rad = int(maxd * f)
        g = (0.45 + 0.55 * capg)
        col = (int(58 * (1 - f) ** 1.6 * ramp * flick * g),
               int(46 * (1 - f) ** 1.6 * ramp * flick * g),
               int(18 * (1 - f) ** 1.6 * ramp))
        pygame.draw.ellipse(scene, col, (kx - rad, cap_y - int(rad * 0.7),
                                         rad * 2, int(rad * 1.4)))

    # The fold TEARING: gold breach-cracks forking out from the rift and
    # WIDENING as the influence pours through -- this is being unleashed, not
    # a blast that dissipates. They brighten + thicken with spread/engulf.
    if spread > 0.01:
        # The wound at the rift -- a sick red-gold weeping core.
        _yk_radial(scene, kx, (gz_y + cap_y) // 2, int(20 + 30 * spread),
                   (150, 30, 22), int(10 + 26 * spread))
        # Rifts tear open across the dark, hands of the taken clawing through.
        _carcosa_portal_hands(scene, w, h, kx, cap_y, spread, t)

    # Town at ground zero + the gold wave washing over it.
    _carcosa_town(scene, w, h, int(h * 0.86), t, wave)

    # Detonation fireball + an expanding shockwave ring.
    fb = max(0.0, 1.0 - t / 0.7)
    if fb > 0.01:
        _yk_radial(scene, kx, gz_y, int(w * 0.10 * fb), _YK_HOT, int(120 * fb))
    rr = int(t * 720)
    if 0.02 < t < 1.3 and rr < w * 1.3:
        rg = pygame.Surface((w, h), pygame.SRCALPHA)
        a = int(150 * max(0.0, 1.0 - t / 1.3))
        pygame.draw.circle(rg, (250, 232, 150, a), (kx, gz_y), rr,
                           max(2, int(13 * (1 - t / 1.3))))
        scene.blit(rg, (0, 0))

    masks = []
    # THE STEM: a column of gold glow + dark tendrils + rising faces, punched
    # up from ground zero to the current stem top.
    if rise > 0.02:
        col_w = max(6, int(w * 0.045 * (0.7 + 0.3 * capg)))
        gh = max(2, gz_y - stem_top + 4)
        glowcol = pygame.Surface((col_w * 2, gh), pygame.SRCALPHA)
        for xx in range(col_w * 2):
            d = abs(xx - col_w) / col_w
            pygame.draw.line(glowcol, (150, 120, 50, int(64 * (1 - d) ** 1.6)),
                             (xx, 0), (xx, gh))
        scene.blit(glowcol, (kx - col_w, stem_top))
        for j in range(5):                        # dark boiling tendrils
            sx = kx + (j - 2) * int(col_w * 0.55)
            pts = [(int(sx + math.sin(t * 2.2 + s2 * 0.5 + j) * 7),
                    int(gz_y - (gz_y - stem_top) * s2 / 10)) for s2 in range(11)]
            pygame.draw.lines(scene, (9, 7, 6), False, pts, 3)
        for j in range(5):                        # faces rising in the stem
            fp = (t * 0.55 + j * 0.21) % 1.0
            fy = gz_y - fp * (gz_y - stem_top)
            if fy >= stem_top - 4:
                masks.append((kx + (j - 2) * col_w * 0.5 + math.sin(t + j) * 7,
                              fy, 7 + int(7 * _frand(j * 3)), j * 5 + 2))

    # THE CAP: billowing cloud-lobes (lit from below by the fireball) +
    # branching tendrils + the taken.
    if capg > 0.02:
        nlobe = 11                                # dark cloud mass, domed
        for i in range(nlobe):
            u = i / (nlobe - 1)
            dome = 1.0 - (2 * u - 1) ** 2
            lx = kx + (u - 0.5) * capR * 2.1
            ly = cap_y - dome * capR * 0.48 + math.sin(t * 0.7 + i) * 4
            lr = int(capR * (0.30 + 0.15 * _frand(i * 5)) * (0.55 + 0.45 * dome))
            if lr > 3:
                pygame.draw.circle(scene, (8, 7, 10), (int(lx), int(ly)), lr)
                pygame.draw.circle(scene, (60, 48, 22),    # faint rim -> 3D roll
                                   (int(lx), int(ly - lr * 0.16)), lr, 1)
        ntr = 24                                  # tendrils over the dome + brim
        for i in range(ntr):
            frac = (i * 0.618034) % 1.0           # golden -> even fill, no pile
            ang = math.pi + frac * math.pi + (_frand(i * 31 + 3) - 0.5) * 0.22
            _carcosa_branch(scene, kx, cap_y, ang, capR * 0.72, 5, capg, t,
                            i * 17 + 1, masks, kx, cap_y)
        for s in (-1, 1):                         # the brim curling down
            _carcosa_branch(scene, kx + s * int(capR * 0.95), cap_y + 4,
                            s * 0.6, capR * 0.5, 4, capg, t, 400 + s,
                            masks, kx, cap_y)

    # THE KING. The breach RESOLVES into His face -- not a mask zooming in, but
    # the rifts ARRANGING into His features: two eye-sockets that burn with the
    # golden gaze, a mouth-gash, gaunt hollows, all clawing with the hands of
    # the taken. He arrives by the holes becoming Him. He looms, fixed in scale
    # (no swell); `engulf` only deepens the inhale and ignites the gaze.
    if capg > 0.05:
        faceR = capR * 0.50                                # tied to the cap, not engulf
        face_y = cap_y + int(capR * 0.34)                  # hung below the smoke-crown
        _carcosa_facemask(scene, w, h, kx, face_y, faceR, spread, engulf, t)

    # The taken surface in the TOWN too -- it isn't destroyed, it's claimed.
    if wave > 0.5:
        for i in range(4):
            tx = kx + (_frand(i * 7 + 1) - 0.5) * w * 0.7
            masks.append((tx, gz_y - 4 + _frand(i * 7 + 2) * 28,
                          8 + int(6 * _frand(i * 7 + 3)), i * 11 + 50))

    # The taken, in His own mask -- big-to-small so they layer with depth.
    for (mx, my, mr, seed) in sorted(masks[:130], key=lambda m: -m[2]):
        vis = min(1.0, capg * 1.4 + 0.3) * (0.62 + 0.38
                                            * (0.5 + 0.5 * math.sin(t * 1.2 + seed)))
        _yk_mask(scene, mx, my, mr, min(1.0, vis), _CARCOSA_FACEKINDS[seed % 4])

    # Gold embers rising through the column.
    for i in range(30):
        ex = kx + (_frand(i * 2 + 1) - 0.5) * w * (0.2 + 0.5 * capg)
        span = h + 50
        ey = (gz_y - ((t * (60 + 80 * _frand(i)) + _frand(i * 2 + 2) * span)
                      % span))
        er = 1 + int(2 * _frand(i * 3))
        pygame.draw.circle(scene, (240, 214, 140), (int(ex), int(ey)), er)

    # Edge vignette.
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(64):
        a = int(180 * (1 - i / 64) ** 1.5 * ramp)
        pygame.draw.rect(vig, (0, 0, 0, a), (i, i, w - 2 * i, h - 2 * i), 1)
    scene.blit(vig, (0, 0))

    # Compose with screen-shake. (No camera zoom -- the King's FIGURE grows
    # and advances on its own; a zoom just read as a close-up of the mask.)
    surf.fill((0, 0, 0))
    surf.blit(scene, (shx, shy))
    if engulf > 0.55:                              # the final engulf wash
        e2 = (engulf - 0.55) / 0.45
        fl = pygame.Surface((w, h), pygame.SRCALPHA)
        fl.fill((172, 142, 66, int(120 * e2)))
        surf.blit(fl, (0, 0))
    if flash > 0.01:                               # the detonation flash
        fl = pygame.Surface((w, h), pygame.SRCALPHA)
        fl.fill((255, 244, 212, int(230 * flash)))
        surf.blit(fl, (0, 0))
    _carcosa_post(surf, t)
