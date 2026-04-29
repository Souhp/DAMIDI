"""
pygame_note_shapes.py
─────────────────────
Pygame-native note-shape primitives.

Color locking
─────────────
Each PygameShape has a color_locked flag.  When locked, set_color() is a
no-op, so edit_shape() calls that reset notes to black each frame silently
skip already-green (or otherwise pinned) shapes.

Use the module helpers:
	lock_note_shapes(shape_list)	– lock all non-fill-mask shapes
	unlock_note_shapes(shape_list)	– unlock all shapes (call on expiry)

Inner "hole" polygons of hollow noteheads carry _is_fill_mask = True and
are never locked/unlocked by these helpers, so they always stay white.

Rest shapes
───────────
Rest type strings passed to pygame_shape_constructor:
	'whole_rest'		— filled rect hanging below a line
	'half_rest'			— filled rect sitting on top of a line
	'quarter_rest'		— classic squiggly zigzag
	'eighth_rest'		— dot + curved stem
	'16th_rest'			— two dots + curved stem
	'32nd_rest'			— three dots + curved stem
	'double_whole_rest' — two thick vertical bars

	shape_y for whole_rest	= the line the rect hangs FROM (top of rect)
	shape_y for half_rest	= the line the rect sits ON  (bottom of rect)
	shape_y for all others	= vertical centre of the symbol
"""

from __future__ import annotations
import math
import pygame
from typing import Sequence

# ─────────────────────────────────────────────────────────────────────────────
# Color helpers
# ─────────────────────────────────────────────────────────────────────────────

RGBA = tuple[int, int, int, int]   # 0-255

_NAMED: dict[str, RGBA] = {
	"black":	   (0,	 0,   0,   255),
	"white":	   (255, 255, 255, 255),
	"red":		   (255, 0,   0,   255),
	"green":	   (0,	 128, 0,   255),
	"blue":		   (0,	 0,   255, 255),
	"grey":		   (128, 128, 128, 255),
	"gray":		   (128, 128, 128, 255),
	"transparent": (0,	 0,   0,   0  ),
	"green400":    (102, 220, 100, 255),
}

_BLACK: RGBA = (0, 0, 0, 255)
_WHITE: RGBA = (255, 255, 255, 255)


def parse_color(color) -> RGBA:
	if hasattr(color, "color"):
		return parse_color(color.color)

	if isinstance(color, (tuple, list)) and len(color) == 4:
		if all(isinstance(v, float) and v <= 1.0 for v in color):
			return tuple(int(v * 255) for v in color)
		return tuple(int(v) for v in color)

	if not isinstance(color, str):
		return _BLACK

	low = color.strip().lower()
	if low in _NAMED:
		return _NAMED[low]

	h = low.lstrip("#")
	try:
		if len(h) == 6:
			return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
		if len(h) == 8:
			return (int(h[2:4], 16), int(h[4:6], 16),
					int(h[6:8], 16), int(h[0:2], 16))
	except ValueError:
		pass
	return _BLACK


# ─────────────────────────────────────────────────────────────────────────────
# Color-lock helpers  (module-level, operate on a flat shape list)
# ─────────────────────────────────────────────────────────────────────────────

def lock_note_shapes(shapes: list) -> None:
	"""Lock every non-fill-mask shape so set_color() becomes a no-op."""
	for s in shapes:
		if not getattr(s, '_is_fill_mask', False):
			s.lock_color()


def unlock_note_shapes(shapes: list) -> None:
	"""Unlock every shape (call when a note expires so it can be recolored)."""
	for s in shapes:
		s.unlock_color()


# ─────────────────────────────────────────────────────────────────────────────
# Bezier / curve sampling utilities
# ─────────────────────────────────────────────────────────────────────────────

_CURVE_STEPS = 48


def _sample_cubic(p0, cp1, cp2, p1, steps: int = _CURVE_STEPS):
	pts = []
	for i in range(steps + 1):
		t  = i / steps
		mt = 1 - t
		x  = (mt**3 * p0[0]
			  + 3 * mt**2 * t  * cp1[0]
			  + 3 * mt	 * t**2 * cp2[0]
			  + t**3			* p1[0])
		y  = (mt**3 * p0[1]
			  + 3 * mt**2 * t  * cp1[1]
			  + 3 * mt	 * t**2 * cp2[1]
			  + t**3			* p1[1])
		pts.append((x, y))
	return pts


def _sample_rational_quadratic(p0, cp, p1, w: float,
								steps: int = _CURVE_STEPS):
	pts = []
	for i in range(steps + 1):
		t	= i / steps
		mt	= 1 - t
		b0	= mt * mt
		b1	= 2 * mt * t * w
		b2	= t  * t
		denom = b0 + b1 + b2
		x = (b0 * p0[0] + b1 * cp[0] + b2 * p1[0]) / denom
		y = (b0 * p0[1] + b1 * cp[1] + b2 * p1[1]) / denom
		pts.append((x, y))
	return pts


def _quad_to_cubic(p0, cp, p1):
	c1 = (p0[0] + (2/3) * (cp[0] - p0[0]),
		  p0[1] + (2/3) * (cp[1] - p0[1]))
	c2 = (p1[0] + (2/3) * (cp[0] - p1[0]),
		  p1[1] + (2/3) * (cp[1] - p1[1]))
	return c1, c2


# ─────────────────────────────────────────────────────────────────────────────
# Abstract base
# ─────────────────────────────────────────────────────────────────────────────

class PygameShape:
	"""
	Base class for all drawable note primitives.

	color_locked
	────────────
	When True, set_color() is silently ignored.  This lets the frame loop
	call edit_shape(event, color=black) every frame without wiping out a
	note that was already turned green by a correct keypress.

	_is_fill_mask
	─────────────
	Set to True on inner "hole" polygons (hollow noteheads, whole notes).
	lock_note_shapes() skips these so the white hole is never recolored.
	"""

	color: RGBA = _BLACK
	color_locked: bool = False
	_is_fill_mask: bool = False   # inner white polygons set this True

	def draw(self, surface: pygame.Surface) -> None:
		raise NotImplementedError

	def shift_x(self, dx: float) -> None:
		raise NotImplementedError

	def set_color(self, color) -> None:
		if self.color_locked:
			return
		self.color = parse_color(color)

	def lock_color(self) -> None:
		self.color_locked = True

	def unlock_color(self) -> None:
		self.color_locked = False


# ─────────────────────────────────────────────────────────────────────────────
# Concrete shape classes
# ─────────────────────────────────────────────────────────────────────────────

class PygamePolygon(PygameShape):
	__slots__ = ("_pts", "color", "_dx", "color_locked", "_is_fill_mask")

	def __init__(self, points, color=None):
		self._pts		  = list(points)
		self._dx		  = 0.0
		self.color		  = parse_color(color) if color is not None else _BLACK
		self.color_locked = False
		self._is_fill_mask = False

	def shift_x(self, dx: float):
		self._dx += dx

	def draw(self, surface):
		if len(self._pts) < 3:
			return
		dx = self._dx
		ipts = [(round(x + dx), round(y)) for x, y in self._pts]
		pygame.draw.polygon(surface, self.color, ipts)


class PygamePolyline(PygameShape):
	__slots__ = ("_pts", "color", "stroke_width", "_dx", "color_locked", "_is_fill_mask")

	def __init__(self, points, color=None, stroke_width=1.0):
		self._pts		   = list(points)
		self._dx		   = 0.0
		self.color		   = parse_color(color) if color is not None else _BLACK
		self.stroke_width  = stroke_width
		self.color_locked  = False
		self._is_fill_mask = False

	def shift_x(self, dx: float):
		self._dx += dx

	def draw(self, surface):
		if len(self._pts) < 2:
			return
		dx = self._dx
		ipts = [(round(x + dx), round(y)) for x, y in self._pts]
		w = max(1, round(self.stroke_width))
		if w == 1:
			pygame.draw.aalines(surface, self.color, False, ipts)
		else:
			pygame.draw.lines(surface, self.color, False, ipts, w)


class PygameLine(PygameShape):
	__slots__ = ("x1", "y1", "x2", "y2", "color", "stroke_width", "_dx",
				 "color_locked", "_is_fill_mask")

	def __init__(self, x1, y1, x2, y2, color=None, stroke_width=1.0):
		self.x1, self.y1   = x1, y1
		self.x2, self.y2   = x2, y2
		self._dx		   = 0.0
		self.color		   = parse_color(color) if color is not None else _BLACK
		self.stroke_width  = stroke_width
		self.color_locked  = False
		self._is_fill_mask = False

	def shift_x(self, dx: float):
		self._dx += dx

	def draw(self, surface):
		w  = max(1, round(self.stroke_width))
		dx = self._dx
		p1 = (round(self.x1 + dx), round(self.y1))
		p2 = (round(self.x2 + dx), round(self.y2))
		if w == 1:
			pygame.draw.aaline(surface, self.color, p1, p2)
		else:
			pygame.draw.line(surface, self.color, p1, p2, w)


class PygameCircle(PygameShape):
	__slots__ = ("x", "y", "radius", "color", "stroke_width", "_fill", "_dx",
				 "color_locked", "_is_fill_mask")

	def __init__(self, x, y, radius, color=None, stroke_width=1.0, fill=True):
		self.x, self.y	   = x, y
		self._dx		   = 0.0
		self.radius		   = radius
		self.color		   = parse_color(color) if color is not None else _BLACK
		self.stroke_width  = stroke_width
		self._fill		   = fill
		self.color_locked  = False
		self._is_fill_mask = False

	def shift_x(self, dx: float):
		self._dx += dx

	def draw(self, surface):
		w = 0 if self._fill else max(1, round(self.stroke_width))
		pygame.draw.circle(surface, self.color,
						   (round(self.x + self._dx), round(self.y)),
						   max(1, round(self.radius)), w)


class PygameEllipse(PygameShape):
	__slots__ = ("x", "y", "width", "height", "color", "_dx",
				 "color_locked", "_is_fill_mask")

	def __init__(self, x, y, width, height, color=None):
		self.x, self.y		   = x, y
		self._dx			   = 0.0
		self.width, self.height = width, height
		self.color			   = parse_color(color) if color is not None else _BLACK
		self.color_locked	   = False
		self._is_fill_mask	   = False

	def shift_x(self, dx: float):
		self._dx += dx

	def draw(self, surface):
		rect = pygame.Rect(round(self.x + self._dx), round(self.y),
						   max(1, round(self.width)), max(1, round(self.height)))
		pygame.draw.ellipse(surface, self.color, rect)


# ─────────────────────────────────────────────────────────────────────────────
# PygameNotehead  —  rotated ellipse via pre-sampled rational quadratic arcs
# ─────────────────────────────────────────────────────────────────────────────

_W = math.cos(math.pi / 4)	 # ≈ 0.7071 — exact ellipse arc weight


class PygameNotehead:
	"""
	Rotated ellipse notehead built from four rational quadratic bezier arcs,
	pre-sampled at construction time into polygon point lists.

	Hollow rendering
	────────────────
	Hollow noteheads use two filled PygamePolygons (outer black + inner white
	scaled toward the centre) instead of a thick PygamePolyline.
	pygame.draw.lines / aalines with width > 1 produces spotty, uneven strokes;
	the double-polygon approach is always crisp regardless of size.

	The inner white polygon has _is_fill_mask = True so lock_note_shapes()
	skips it — it must always stay white regardless of note color.

	.shapes  — list of PygameShape objects to draw (1 for filled, 2 for hollow)
	.shape	 — the primary (outer) shape, kept for back-compat
	"""

	_HOLLOW_INNER_SCALE = 0.45

	def __init__(self, cx, cy,
				 width: float = 20.0, height: float = 13.0,
				 theta: float = -math.pi / 6,
				 color=None, hollow: bool = False):
		self._cx, self._cy = cx, cy
		self._a, self._b   = width / 2, height / 2
		self._theta		   = theta
		self._color		   = parse_color(color) if color is not None else _BLACK
		self._hollow	   = hollow
		self._width		   = width

		self._compute_geometry()
		self._shapes = self._build_shapes()

	def _compute_geometry(self):
		a, b   = self._a, self._b
		cx, cy = self._cx, self._cy
		c, s   = math.cos(self._theta), math.sin(self._theta)

		self.P0  = (cx + a*c,		 cy + a*s		)
		self.P1  = (cx - b*s,		 cy + b*c		)
		self.P2  = (cx - a*c,		 cy - a*s		)
		self.P3  = (cx + b*s,		 cy - b*c		)

		self.CP01 = (cx + a*c - b*s, cy + a*s + b*c )
		self.CP12 = (cx - a*c - b*s, cy - a*s + b*c )
		self.CP23 = (cx - a*c + b*s, cy - a*s - b*c )
		self.CP30 = (cx + a*c + b*s, cy + a*s - b*c )

	def _sample_outline(self) -> list[tuple[float, float]]:
		pts = []
		arcs = [
			(self.P0,  self.CP01, self.P1),
			(self.P1,  self.CP12, self.P2),
			(self.P2,  self.CP23, self.P3),
			(self.P3,  self.CP30, self.P0),
		]
		for p0, cp, p1 in arcs:
			pts.extend(_sample_rational_quadratic(p0, cp, p1, _W)[:-1])
		return pts

	def _build_shapes(self) -> list[PygameShape]:
		pts = self._sample_outline()
		outer = PygamePolygon(pts, self._color)

		if not self._hollow:
			return [outer]

		cx, cy = self._cx, self._cy
		k = self._HOLLOW_INNER_SCALE
		inner_pts = [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in pts]
		inner = PygamePolygon(inner_pts, _WHITE)
		inner._is_fill_mask = True	 # ← never recolored by lock/unlock helpers
		return [outer, inner]

	@property
	def shape(self) -> PygameShape:
		return self._shapes[0]

	@property
	def shapes(self) -> list[PygameShape]:
		return list(self._shapes)

	@property
	def stem_up_attach(self)   -> tuple: return self.P0
	@property
	def stem_down_attach(self) -> tuple: return self.P2


# ─────────────────────────────────────────────────────────────────────────────
# Primitive builders
# ─────────────────────────────────────────────────────────────────────────────

def _stem(x1, y1, x2, y2, shape_width: float, color) -> PygameLine:
	return PygameLine(x1, y1, x2, y2, color,
					  stroke_width=shape_width * 0.15)


def _flag(stem_x, stem_y, shape_width, shape_height, color,
		  length_scale: float = 1.0) -> PygamePolyline:
	cp1 = (stem_x + shape_width  * 0.5,
		   stem_y + shape_height * 0.3 * length_scale)
	cp2 = (stem_x + shape_width  * 0.5,
		   stem_y + shape_height * 0.8 * length_scale)
	end = cp2
	pts = _sample_cubic((stem_x, stem_y), cp1, cp2, end)
	return PygamePolyline(pts, color, stroke_width=shape_width * 0.15)


def _straight_flag(x1, y1, x2, y2, shape_width, color) -> PygameLine:
	return PygameLine(x1, y1, x2, y2, color, stroke_width=shape_width * 0.15)


def _accidental_sw(paint, shape_width: float) -> float:
	if paint is not None:
		sw = getattr(paint, 'stroke_width', None)
		if sw:
			return sw
	return shape_width * 0.15


#--
# Cleff helpers
#

def _treble_clef(shape_x, shape_y, shape_width, shape_height, color):
	sp       = shape_height
	sw       = max(4.5, sp * 0.30)
	cx, cy   = shape_x, shape_y

	top_y    = cy - sp * 4.5
	bottom_y = cy + sp * 1.7

	# better engraving alignment
	#cx -= sp * 0.15

	stem = PygameLine(cx, top_y, cx, bottom_y, color, sw)

# ── Segment A: rise and sweep left ──
	tail_pts_a = _sample_cubic(
		(cx, bottom_y),

		(cx + sp * 0.25, bottom_y + sp * 1.2),

		(cx - sp * 0.9, bottom_y + sp * 0.6),

		(cx - sp * 1.2, bottom_y - sp * 0.3),
		steps=20,
	)



	tail = PygamePolyline(tail_pts_a, color, stroke_width=sw)

	pts = []

	# ── Segment A: top curl (FIX: return higher) ─────────────────────────
	pts += _sample_cubic(
		(cx,             top_y),
		(cx + sp * 0.9,  top_y + sp * 0.1),
		(cx + sp * 1.0,  cy - sp * 3.2),   # higher turnback
		(cx + sp * 0.35, cy - sp * 2.2),
		steps=30,
	)[:-1]

	# ── Segment B: outer loop (FIX: stronger left sweep) ─────────────────
	pts += _sample_cubic(
		(cx + sp * 0.35, cy - sp * 2.2),
		(cx - sp * 1.8,  cy - sp * 0.8),   # push LEFT harder
		(cx - sp * 1.7,  cy + sp * 0.8),
		(cx + sp * 0.05, cy + sp * 0.6),
		steps=26,
	)[:-1]

	# ── Segment C: inner spiral (FIX: MUST go DOWN) ──────────────────────
	pts += _sample_cubic(
		(cx + sp * 0.05, cy + sp * 0.6),
		(cx + sp * 1.5,  cy + sp * 0.6),   # right push
		(cx + sp * 0.4,  cy - sp * 1.5),   # start turning inward
		(cx - sp * 1, cy + sp * 0.2),   # drop through center (KEY FIX)
		steps=30,
	)[:-1]



	body = PygamePolyline(pts, color, stroke_width=sw)

	return [body, stem, tail]

def _bass_clef(shape_x, shape_y, shape_width, shape_height, color):
	"""
	Bass (F) clef.
	shape_y      = F3 line anchor (the F line sits between the two right dots).
	shape_height = one staff space.

	Fixes:
	  - Curve now starts from OUTER LEFT edge of main ball
	  - Proper rounded sweep over top
	  - Curves inward and downward like true bass clef
	  - Ball remains centered on F line
	  - Better visual proportionality
	"""
	sp = shape_height

	# Symbol scaling
	scale = 1.5
	sw = max(2.5, sp * 0.30)

	cx, cy = shape_x, shape_y

	# ── Main ball centered on F line ──────────────────────────────────────
	ball_r = sp * 0.3 * scale
	ball_x = cx - sp * 0.25 * scale
	ball_y = cy

	# Start from LEFT OUTER edge of ball
	start_x = ball_x - ball_r
	start_y = ball_y

	# ── Main bass clef curve ──────────────────────────────────────────────
	# Sweeps upward, rightward, loops around, then descends
	body_pts = _sample_cubic(
		(start_x, start_y),

		# Upper sweep
		(cx + sp * 0.6 * scale, cy - sp * 1.8 * scale),

		# Outer right curve
		(cx + sp * 1.5 * scale, cy + sp * 0.8 * scale),

		# Lower tail
		(cx - sp * 0.1 * scale, cy + sp * 2.1 * scale),

		steps=48,
	)

	body = PygamePolyline(body_pts, color, stroke_width=sw)

	# ── Filled main ball ──────────────────────────────────────────────────
	ball = PygameCircle(
		ball_x,
		ball_y,
		ball_r,
		color,
		fill=True
	)

	# ── Two right-side dots ───────────────────────────────────────────────
	dot_r = sp * 0.16 * scale
	dot_x = cx + sp * 1.65 * scale

	d1 = PygameCircle(
		dot_x,
		cy - sp * 0.45 * scale,
		dot_r,
		color,
		fill=True
	)

	d2 = PygameCircle(
		dot_x,
		cy + sp * 0.45 * scale,
		dot_r,
		color,
		fill=True
	)

	return [body, ball, d1, d2]

# ─────────────────────────────────────────────────────────────────────────────
# Rest shape helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rect_polygon(cx: float, top_y: float, w: float, h: float,
				  color) -> PygamePolygon:
	"""Axis-aligned filled rectangle as a PygamePolygon."""
	pts = [
		(cx - w / 2, top_y),
		(cx + w / 2, top_y),
		(cx + w / 2, top_y + h),
		(cx - w / 2, top_y + h),
	]
	return PygamePolygon(pts, color)


def _rest_dot(x: float, y: float, r: float, color) -> PygameCircle:
	"""Small filled circle used as a rest flag dot."""
	return PygameCircle(x, y, r, color, fill=True)


def _eighth_stem_pts(dot_x: float, dot_y: float, dot_r: float,
					  shape_width: float, shape_height: float,
					  stem_length_scale: float = 1.0) -> list:
	"""
	Pre-sample the curved diagonal stem of an eighth/16th/32nd rest.
	The stem starts just below the dot and curves to the lower-left,
	ending at approximately (dot_x - w*0.5, dot_y + h*2 * scale).
	"""
	h = shape_height * 2.0 * stem_length_scale
	w = shape_width
	p0	= (dot_x - dot_r * 0.7, dot_y + dot_r * 0.8)
	cp1 = (dot_x - w * 0.15,	dot_y + h * 0.35)
	cp2 = (dot_x - w * 0.55,	dot_y + h * 0.65)
	p1	= (dot_x - w * 0.45,	dot_y + h)
	return _sample_cubic(p0, cp1, cp2, p1, steps=14)


# ─────────────────────────────────────────────────────────────────────────────
# pygame_shape_constructor
# ─────────────────────────────────────────────────────────────────────────────

def pygame_shape_constructor(
	shape_x		  = None,
	shape_y		  = None,
	shape_width   = None,
	shape_height  = None,
	type		  = None,
	paint		  = None,
	canvas_width  = None,
	canvas_height = None,
	top_margin	  = None,
	left_margin   = None,
	right_margin  = None,
	dotted: bool  = False,
) -> list | None:
	if type is None:
		return None

	color: RGBA = parse_color(paint) if paint is not None else _BLACK
	result: list = []

	def _need(*args):
		return all(a is not None for a in args)

	match type:

		# ── quarter ──────────────────────────────────────────────────────────
		case 'quarter':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			head   = PygameNotehead(shape_x, shape_y, shape_width, shape_height,
									-math.pi / 6, color)
			ox, oy = head.stem_down_attach
			sx, sy = head.stem_up_attach
			top_y  = sy - shape_height * 2.5
			st = _stem(sx + (ox-sx)*0.05, sy + (oy-sy)*0.3,
					   sx + (ox-sx)*0.05, top_y, shape_width, color)
			result.append(([head.shape, st], 'quarter'))

		# ── eighth ───────────────────────────────────────────────────────────
		case 'eighth':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			head   = PygameNotehead(shape_x, shape_y, shape_width, shape_height,
									-math.pi / 6, color)
			ox, oy = head.stem_down_attach
			sx, sy = head.stem_up_attach
			top_y  = sy - shape_height * 2.5
			st = _stem(sx + (ox-sx)*0.05, sy + (oy-sy)*0.3,
					   sx + (ox-sx)*0.05, top_y, shape_width, color)
			fl = _flag(sx, top_y, shape_width, shape_height, color)
			result.append(([head.shape, st, fl], 'eighth'))

		# ── 16th ─────────────────────────────────────────────────────────────
		case '16th':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			head   = PygameNotehead(shape_x + shape_width/2, shape_y,
									shape_width, shape_height, -math.pi/6, color)
			ox, oy = head.stem_down_attach
			sx, sy = head.stem_up_attach
			top_y  = sy - shape_height * 2.5
			st	= _stem(sx + (ox-sx)*0.05, sy + (oy-sy)*0.3,
						sx + (ox-sx)*0.05, top_y, shape_width, color)
			gap = shape_height * 0.6
			fl1 = _straight_flag(sx, top_y,
								  sx + shape_width*0.6, top_y + shape_height*0.8,
								  shape_width, color)
			fl2 = _straight_flag(sx, top_y + gap,
								  sx + shape_width*0.5, top_y + gap + shape_height*0.8,
								  shape_width, color)
			result.append(([head.shape, st, fl1, fl2], 'sixteenth'))

		# ── 32nd ─────────────────────────────────────────────────────────────
		case '32nd':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			head   = PygameNotehead(shape_x, shape_y, shape_width, shape_height,
									-math.pi/6, color)
			ox, oy = head.stem_down_attach
			sx, sy = head.stem_up_attach
			top_y  = sy - shape_height * 2.5
			st	= _stem(sx + (ox-sx)*0.05, sy + (oy-sy)*0.3,
						sx + (ox-sx)*0.05, top_y, shape_width, color)
			g2	= shape_height * 0.4
			g3	= shape_height * 0.45
			fl1 = _straight_flag(sx, top_y,
								  sx + shape_width*0.6, top_y + shape_height*0.8,
								  shape_width, color)
			fl2 = _straight_flag(sx, top_y + g2,
								  sx + shape_width*0.5, top_y + g2 + shape_height*0.75,
								  shape_width, color)
			fl3 = _straight_flag(sx, top_y + g3*2,
								  sx + shape_width*0.45, top_y + g3*2 + shape_height*0.75,
								  shape_width, color)
			result.append(([head.shape, st, fl1, fl2, fl3], 'thirtysecond'))

		# ── half ─────────────────────────────────────────────────────────────
		case 'half':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			head   = PygameNotehead(shape_x, shape_y,
									shape_width*0.8, shape_height*0.7,
									-math.pi/6, color, hollow=True)
			ox, oy = head.stem_down_attach
			sx, sy = head.stem_up_attach
			top_y  = sy - shape_height * 2.5
			stem_x = sx - (ox-sx)*0.069
			st = _stem(stem_x, sy + (oy-sy)*0.3, stem_x, top_y,
					   shape_width, color)
			result.append(([*head.shapes, st], 'half'))

		# ── whole ─────────────────────────────────────────────────────────────
		case 'whole':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None

			shape_width*=1.1
			shape_height*=1.1
			outer = PygameEllipse(
				shape_x, shape_y - shape_height/2,
				shape_width, shape_height, color)
			inner = PygameEllipse(
				shape_x + shape_height/2.3,
				shape_y - shape_width/4,
				shape_height/2.2, shape_width/2, _WHITE)
			inner._is_fill_mask = True	 # ← white hole, never recolored
			result.append(([outer, inner], 'whole'))

		# ── grace (type == 0) ─────────────────────────────────────────────────
		case 0:
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			head   = PygameNotehead(shape_x, shape_y, shape_width, shape_height,
									-math.pi/6, color)
			ox, oy = head.stem_down_attach
			sx, sy = head.stem_up_attach
			top_y  = sy - shape_height * 2.5
			st = _stem(sx + (ox-sx)*0.05, sy + (oy-sy)*0.3,
					   sx + (ox-sx)*0.05, top_y, shape_width, color)
			fl = _flag(sx, top_y, shape_width, shape_height, color)
			slash_off = shape_height * 0.4
			slash = PygameLine(
				sx - shape_width*0.4, top_y + slash_off,
				sx + shape_width*0.4, top_y + slash_off + shape_height*0.3*0.9,
				color, stroke_width=shape_width*0.12)
			result.append(([head.shape, st, fl, slash], 'grace'))

		# ── accidentals ───────────────────────────────────────────────────────

		case '#':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			sw = _accidental_sw(paint, shape_width)
			result.append(([
				PygameLine(shape_x+shape_width/3, shape_y+(shape_height/4-shape_height/7),
						   shape_x-shape_width/3, shape_y+shape_height/4, color, sw),
				PygameLine(shape_x+shape_width/3, shape_y-(shape_height/4+shape_height/7),
						   shape_x-shape_width/3, shape_y-shape_height/4, color, sw),
				PygameLine(shape_x+shape_width/7, shape_y-(shape_width-shape_width/3),
						   shape_x+shape_width/7, shape_y+(shape_width-shape_width/3), color, sw),
				PygameLine(shape_x-shape_width/7, shape_y-(shape_width-shape_width/3),
						   shape_x-shape_width/7, shape_y+(shape_width-shape_width/3), color, sw),
			], '#'))

		case 'b':
			if not _need(shape_x, shape_y, shape_width):
				return None
			sw	 = _accidental_sw(paint, shape_width)
			vert = PygameLine(
				shape_x - shape_width/20, shape_y - (shape_width - shape_width/4),
				shape_x - shape_width/20, shape_y + (shape_width - shape_width/1.4),
				color, sw)
			p0	= (shape_x - shape_width/20, shape_y + (shape_width - shape_width/1.3))
			cp	= (shape_x + shape_width*0.6, shape_y - shape_width*0.2)
			p1	= (shape_x - shape_width/20, shape_y + (shape_width - shape_width*1.2))
			pts = _sample_rational_quadratic(p0, cp, p1, w=1.0)
			pts.append(p0)
			result.append(([vert, PygamePolygon(pts, color)], 'b'))

		case 'N':
			if not _need(shape_x, shape_y, shape_width):
				return None
			sw = _accidental_sw(paint, shape_width)
			result.append(([
				PygameLine(shape_x+shape_width/5, shape_y-(shape_width-shape_width/2),
						   shape_x+shape_width/5, shape_y+(shape_width-shape_width/2), color, sw),
				PygameLine(shape_x-shape_width/5, shape_y-(shape_width-shape_width/2),
						   shape_x-shape_width/5, shape_y+(shape_width-shape_width/2), color, sw),
				PygameLine(shape_x-shape_width/5, shape_y-(shape_width-shape_width/2),
						   shape_x+shape_width/5, shape_y+(shape_width-shape_width/2), color, sw),
			], 'N'))

		case '##':
			if not _need(shape_x, shape_y, shape_width):
				return None
			sw = _accidental_sw(paint, shape_width)
			result.append(([
				PygameLine(shape_x-shape_width/5, shape_y-(shape_width-shape_width/2),
						   shape_x+shape_width/5, shape_y+(shape_width-shape_width/2), color, sw),
				PygameLine(shape_x+shape_width/5, shape_y-(shape_width-shape_width/2),
						   shape_x-shape_width/5, shape_y+(shape_width-shape_width/2), color, sw),
			], '##'))

		case 'bb':
			if not _need(shape_x, shape_y, shape_width):
				return None
			sw = _accidental_sw(paint, shape_width)

			def _flat(ox: float):
				v = PygameLine(
					ox, shape_y-(shape_width-shape_width/4),
					ox, shape_y+(shape_width-shape_width/1.4), color, sw)
				p0	= (ox, shape_y+(shape_width-shape_width/1.3))
				cp	= (ox + shape_width*0.27*(2 if ox < shape_x else 1),
					   shape_y - shape_width*0.2)
				p1	= (ox, shape_y+(shape_width-shape_width*1.2))
				pts = _sample_rational_quadratic(p0, cp, p1, w=1.0)
				pts.append(p0)
				return v, PygamePolygon(pts, color)

			v1, c1 = _flat(shape_x - shape_width/2.3)
			v2, c2 = _flat(shape_x - shape_width/10)
			result.append(([v1, c1, v2, c2], 'bb'))

		# ── bar line ──────────────────────────────────────────────────────────
		case 'bar':
			if not _need(shape_x, shape_y, shape_height):
				return None
			sw = float(shape_width) if shape_width is not None else 2.0
			bar = PygameLine(
				shape_x, shape_y,
				shape_x, shape_y + shape_height,
				color, sw)
			result.append(([bar], 'bar'))

		# ══════════════════════════════════════════════════════════════════════
		# REST SHAPES
		# ══════════════════════════════════════════════════════════════════════

		# ── whole rest  (solid rect hanging BELOW shape_y) ────────────────────
		# shape_y = the staff line the rect hangs from (rect top-edge = shape_y)
		case 'whole_rest':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			rw = shape_width * 1.5
			rh = shape_height * 0.45
			rect = _rect_polygon(shape_x, shape_y, rw, rh, color)
			result.append(([rect], 'whole_rest'))

		# ── half rest	(solid rect sitting ON TOP of shape_y) ─────────────────
		# shape_y = the staff line the rect sits on (rect bottom-edge = shape_y)
		case 'half_rest':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			rw = shape_width * 1.5
			rh = shape_height * 0.45
			rect = _rect_polygon(shape_x, shape_y - rh, rw, rh, color)
			result.append(([rect], 'half_rest'))

		# ── double whole rest	(two thick vertical bars) ──────────────────────
		# shape_y = vertical centre of the symbol
		case 'double_whole_rest':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			bar_w = shape_width * 0.22
			bar_h = shape_height * 1.0
			sep   = shape_width * 0.55			# half-separation between bars
			left  = _rect_polygon(shape_x - sep, shape_y - bar_h / 2, bar_w, bar_h, color)
			right = _rect_polygon(shape_x + sep, shape_y - bar_h / 2, bar_w, bar_h, color)
			result.append(([left, right], 'double_whole_rest'))

		# ── quarter rest  (classic squiggly zigzag) ────────────────────────────
		# shape_y = vertical centre of the symbol
		# The shape mimics the traditional hand-engraved quarter rest:
		#	top hook  →  diagonal stroke  →  bottom curl
		case 'quarter_rest':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			total_h = shape_height * 3.4
			w		= shape_width  * 0.9
			sw		= max(1.5, shape_width * 0.16)
			ty		= shape_y - total_h * 0.46	 # topmost point

			# Segment 1 — top rightward hook
			seg1 = _sample_cubic(
				(shape_x - w * 0.05, ty),
				(shape_x + w * 0.65, ty + total_h * 0.09),
				(shape_x + w * 0.40, ty + total_h * 0.20),
				(shape_x - w * 0.20, ty + total_h * 0.36),
				steps=12,
			)
			# Segment 2 — diagonal through centre
			seg2 = _sample_cubic(
				(shape_x - w * 0.20, ty + total_h * 0.36),
				(shape_x + w * 0.15, ty + total_h * 0.48),
				(shape_x + w * 0.22, ty + total_h * 0.57),
				(shape_x - w * 0.08, ty + total_h * 0.67),
				steps=12,
			)
			# Segment 3 — bottom left curl with upward tail
			seg3 = _sample_cubic(
				(shape_x - w * 0.08, ty + total_h * 0.67),
				(shape_x - w * 0.50, ty + total_h * 0.80),
				(shape_x - w * 0.38, ty + total_h * 0.91),
				(shape_x + w * 0.12, ty + total_h * 1.00),
				steps=12,
			)
			pts = seg1 + seg2[1:] + seg3[1:]
			result.append(([PygamePolyline(pts, color, stroke_width=sw)], 'quarter_rest'))

		# ── eighth rest  (filled dot + curved diagonal stem) ──────────────────
		# shape_y = vertical centre; dot at upper-right, stem sweeps lower-left
		case 'eighth_rest':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			dot_r  = shape_width  * 0.21
			dot_x  = shape_x + shape_width	* 0.28
			dot_y  = shape_y - shape_height * 0.72
			sw	   = max(1.5, shape_width * 0.16)

			dot  = _rest_dot(dot_x, dot_y, dot_r, color)
			stem_pts = _eighth_stem_pts(dot_x, dot_y, dot_r,
										shape_width, shape_height,
										stem_length_scale=1.0)
			stem = PygamePolyline(stem_pts, color, stroke_width=sw)
			result.append(([dot, stem], 'eighth_rest'))

		# ── 16th rest	(two dots + longer curved stem) ────────────────────────
		case '16th_rest':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			dot_r	= shape_width  * 0.21
			gap		= shape_height * 0.75		   # vertical gap between dots
			dot1_x	= shape_x + shape_width  * 0.28
			dot1_y	= shape_y - shape_height * 0.72
			dot2_x	= dot1_x  - shape_width  * 0.12
			dot2_y	= dot1_y  + gap
			sw		= max(1.5, shape_width * 0.16)

			dot1 = _rest_dot(dot1_x, dot1_y, dot_r, color)
			dot2 = _rest_dot(dot2_x, dot2_y, dot_r, color)

			# Single stem long enough to pass both dots
			stem_pts = _eighth_stem_pts(dot1_x, dot1_y, dot_r,
										shape_width, shape_height,
										stem_length_scale=1.5)
			stem = PygamePolyline(stem_pts, color, stroke_width=sw)
			result.append(([dot1, dot2, stem], '16th_rest'))

		# ── 32nd rest	(three dots + even longer curved stem) ─────────────────
		case '32nd_rest':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			dot_r	= shape_width  * 0.20
			gap		= shape_height * 0.68
			dot1_x	= shape_x + shape_width  * 0.30
			dot1_y	= shape_y - shape_height * 0.72
			dot2_x	= dot1_x  - shape_width  * 0.10
			dot2_y	= dot1_y  + gap
			dot3_x	= dot2_x  - shape_width  * 0.10
			dot3_y	= dot2_y  + gap
			sw		= max(1.5, shape_width * 0.15)

			dot1 = _rest_dot(dot1_x, dot1_y, dot_r, color)
			dot2 = _rest_dot(dot2_x, dot2_y, dot_r, color)
			dot3 = _rest_dot(dot3_x, dot3_y, dot_r, color)

			stem_pts = _eighth_stem_pts(dot1_x, dot1_y, dot_r,
										shape_width, shape_height,
										stem_length_scale=2.1)
			stem = PygamePolyline(stem_pts, color, stroke_width=sw)
			result.append(([dot1, dot2, dot3, stem], '32nd_rest'))

		case 'treble_clef':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			shapes = _treble_clef(
				shape_x, shape_y,
				shape_width, shape_height,
				color
			)
			result.append((shapes, 'treble_clef'))

		case 'bass_clef':
			if not _need(shape_x, shape_y, shape_width, shape_height):
				return None
			shapes = _bass_clef(
				shape_x, shape_y,
				shape_width, shape_height,
				color
			)
			result.append((shapes, 'bass_clef'))

		case _:
			print(f"pygame_shape_constructor: unknown type '{type}'")
			return None

	# ── augmentation dot ──────────────────────────────────────────────────────
	if dotted and result:
		dot = PygameCircle(
			shape_x + shape_width*0.75, shape_y,
			shape_width*0.1, color, fill=True)
		result[0][0].append(dot)

	return result
