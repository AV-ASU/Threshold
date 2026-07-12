"""Engine-wide constants: paths, screen geometry, colour palette.
No Python imports beyond stdlib -- safe to import from anywhere."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_DIR = os.path.join(HERE, ".archive")

SCREEN_W, SCREEN_H = 960, 640
TILE = 32

# Internal render scale for the WORLD layer (CAMERA/FPS). The oblique world +
# its full-screen atmosphere passes (grade, fog, haze, skybox) are the bulk of
# the frame and scale with pixel count, so the world is rendered to a buffer at
# this fraction of the window and upscaled once; the HUD/text still draw at full
# resolution on top, so they stay crisp. 1.0 = off (byte-identical to the
# unscaled path). ~0.8 trades a slight softening of the world for a real fps win
# that suits the hazy look.
RENDER_SCALE = 1.0

# Round-10: matches the @-floor void color exactly so when the camera
# can't fill the screen with a small scene (or when a scene's @-floor
# extends to a region the camera can show beyond the layout), there's
# no visible seam between scene and screen-edge. The "invisible ground"
# path off any invisible-ground scene reads as truly continuous now.
C_BG = (8, 6, 14)
C_WHITE = (240, 238, 230)
C_BLACK = (0, 0, 0)
C_GOLD = (232, 212, 77)
C_RED = (204, 50, 50)
C_BLOOD = (122, 22, 28)
C_BLUE = (90, 140, 220)
C_GREEN = (90, 200, 110)
C_PURPLE = (160, 90, 200)
C_PANEL = (14, 12, 22)
C_PANEL_BORDER = (90, 80, 110)
C_DIALOG_BG = (12, 10, 18)
C_DIM = (90, 88, 100)
