"""
Shared layout constants used by both sceneManager.py and childWidget.py.
Keeping them here breaks the circular import that would arise if childWidget
imported from sceneManager.
"""

NAVBAR_H = 50
BASE_W   = 800
BASE_H   = 600

NAV_BG      = (18, 18, 42)
NAV_DIVIDER = (38, 38, 78)

SIDEBAR_W_FRAC = 0.28
GRID_PAD_FRAC  = 0.018
GRID_GAP_FRAC  = 0.012

default_scale={"C":  ["C", "D", "E", "F", "G", "A", "B"]}
