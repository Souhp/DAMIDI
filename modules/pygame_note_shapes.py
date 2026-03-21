"""
pygame_note_shapes.py
─────────────────────
Pygame-native note-shape primitives.

Replaces cairo_note_shapes.py.  The public API is identical:

    pygame_shape_constructor(...)  →  [ ([PygameShape, …], type_string), … ]

Key differences from the Cairo version
───────────────────────────────────────
• Colors are (r, g, b, a) ints 0-255 instead of floats 0-1.
• Shapes draw onto a pygame.Surface instead of a cairo.Context.
• Bezier / ellipse curves are pre-sampled into point lists at construction
  time so draw() is a single polygon / lines call with zero math overhead.
• No ctx.save()/restore(), no transform matrices, no Cairo path state.
• Hollow noteheads are drawn as outer filled polygon + smaller inner white
  polygon — always crisp, no thick-polyline aliasing artefacts.
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
    "black":       (0,   0,   0,   255),
    "white":       (255, 255, 255, 255),
    "red":         (255, 0,   0,   255),
    "green":       (0,   128, 0,   255),
    "blue":        (0,   0,   255, 255),
    "grey":        (128, 128, 128, 255),
    "gray":        (128, 128, 128, 255),
    "transparent": (0,   0,   0,   0  ),
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
# Bezier / curve sampling utilities
# ─────────────────────────────────────────────────────────────────────────────

_CURVE_STEPS = 16


def _sample_cubic(p0, cp1, cp2, p1, steps: int = _CURVE_STEPS):
    pts = []
    for i in range(steps + 1):
        t  = i / steps
        mt = 1 - t
        x  = (mt**3 * p0[0]
              + 3 * mt**2 * t  * cp1[0]
              + 3 * mt   * t**2 * cp2[0]
              + t**3            * p1[0])
        y  = (mt**3 * p0[1]
              + 3 * mt**2 * t  * cp1[1]
              + 3 * mt   * t**2 * cp2[1]
              + t**3            * p1[1])
        pts.append((x, y))
    return pts


def _sample_rational_quadratic(p0, cp, p1, w: float,
                                steps: int = _CURVE_STEPS):
    pts = []
    for i in range(steps + 1):
        t   = i / steps
        mt  = 1 - t
        b0  = mt * mt
        b1  = 2 * mt * t * w
        b2  = t  * t
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
    color: RGBA = _BLACK

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

    def shift_x(self, dx: float) -> None:
        raise NotImplementedError

    def set_color(self, color) -> None:
        self.color = parse_color(color)


# ─────────────────────────────────────────────────────────────────────────────
# PygameLine
# ─────────────────────────────────────────────────────────────────────────────

class PygamePolygon(PygameShape):
    __slots__ = ("_pts", "color", "_dx")

    def __init__(self, points, color=None):
        self._pts  = list(points)
        self._dx   = 0.0                          # ← offset, never reallocates
        self.color = parse_color(color) if color is not None else _BLACK

    def shift_x(self, dx: float):
        self._dx += dx                            # ← O(1), no allocation

    def draw(self, surface):
        if len(self._pts) < 3:
            return
        dx = self._dx
        ipts = [(round(x + dx), round(y)) for x, y in self._pts]
        pygame.draw.polygon(surface, self.color, ipts)


class PygamePolyline(PygameShape):
    __slots__ = ("_pts", "color", "stroke_width", "_dx")

    def __init__(self, points, color=None, stroke_width=1.0):
        self._pts         = list(points)
        self._dx          = 0.0
        self.color        = parse_color(color) if color is not None else _BLACK
        self.stroke_width = stroke_width

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
    __slots__ = ("x1", "y1", "x2", "y2", "color", "stroke_width", "_dx")

    def __init__(self, x1, y1, x2, y2, color=None, stroke_width=1.0):
        self.x1, self.y1  = x1, y1
        self.x2, self.y2  = x2, y2
        self._dx          = 0.0
        self.color        = parse_color(color) if color is not None else _BLACK
        self.stroke_width = stroke_width

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
    __slots__ = ("x", "y", "radius", "color", "stroke_width", "_fill", "_dx")

    def __init__(self, x, y, radius, color=None, stroke_width=1.0, fill=True):
        self.x, self.y    = x, y
        self._dx          = 0.0
        self.radius       = radius
        self.color        = parse_color(color) if color is not None else _BLACK
        self.stroke_width = stroke_width
        self._fill        = fill

    def shift_x(self, dx: float):
        self._dx += dx

    def draw(self, surface):
        w = 0 if self._fill else max(1, round(self.stroke_width))
        pygame.draw.circle(surface, self.color,
                           (round(self.x + self._dx), round(self.y)),
                           max(1, round(self.radius)), w)


class PygameEllipse(PygameShape):
    __slots__ = ("x", "y", "width", "height", "color", "_dx")

    def __init__(self, x, y, width, height, color=None):
        self.x, self.y          = x, y
        self._dx                = 0.0
        self.width, self.height = width, height
        self.color              = parse_color(color) if color is not None else _BLACK

    def shift_x(self, dx: float):
        self._dx += dx

    def draw(self, surface):
        rect = pygame.Rect(round(self.x + self._dx), round(self.y),
                           max(1, round(self.width)), max(1, round(self.height)))
        pygame.draw.ellipse(surface, self.color, rect)
# ─────────────────────────────────────────────────────────────────────────────
# PygameNotehead  —  rotated ellipse via pre-sampled rational quadratic arcs
# ─────────────────────────────────────────────────────────────────────────────

_W = math.cos(math.pi / 4)   # ≈ 0.7071 — exact ellipse arc weight


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

    .shapes  — list of PygameShape objects to draw (1 for filled, 2 for hollow)
    .shape   — the primary (outer) shape, kept for back-compat
    """

    # How much to shrink the outer polygon to produce the hollow "hole".
    # 0.45 gives a ring width of roughly 28 % of the semi-axis — visually
    # matches engraving conventions at typical staff sizes.
    _HOLLOW_INNER_SCALE = 0.45

    def __init__(self, cx, cy,
                 width: float = 20.0, height: float = 13.0,
                 theta: float = -math.pi / 6,
                 color=None, hollow: bool = False):
        self._cx, self._cy = cx, cy
        self._a, self._b   = width / 2, height / 2
        self._theta        = theta
        self._color        = parse_color(color) if color is not None else _BLACK
        self._hollow       = hollow
        self._width        = width

        self._compute_geometry()
        self._shapes = self._build_shapes()

    # ------------------------------------------------------------------
    def _compute_geometry(self):
        a, b   = self._a, self._b
        cx, cy = self._cx, self._cy
        c, s   = math.cos(self._theta), math.sin(self._theta)

        self.P0  = (cx + a*c,        cy + a*s       )
        self.P1  = (cx - b*s,        cy + b*c       )
        self.P2  = (cx - a*c,        cy - a*s       )
        self.P3  = (cx + b*s,        cy - b*c       )

        self.CP01 = (cx + a*c - b*s, cy + a*s + b*c )
        self.CP12 = (cx - a*c - b*s, cy - a*s + b*c )
        self.CP23 = (cx - a*c + b*s, cy - a*s - b*c )
        self.CP30 = (cx + a*c + b*s, cy + a*s - b*c )

    def _sample_outline(self) -> list[tuple[float, float]]:
        """Return the pre-sampled ellipse outline points."""
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

        # ── Hollow: add a smaller white polygon to punch the hole ──────────
        # Scale all outline points toward the centre by _HOLLOW_INNER_SCALE.
        # This keeps the rotated orientation perfectly matched to the outer
        # ring without any trig — and both polygons are always filled, so
        # pygame.draw.polygon stays crisp at every size.
        cx, cy = self._cx, self._cy
        k = self._HOLLOW_INNER_SCALE
        inner_pts = [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in pts]
        inner = PygamePolygon(inner_pts, _WHITE)
        return [outer, inner]

    # ------------------------------------------------------------------
    @property
    def shape(self) -> PygameShape:
        """Primary (outer) shape — kept for back-compat."""
        return self._shapes[0]

    @property
    def shapes(self) -> list[PygameShape]:
        """All shapes needed to render this notehead (outer + optional inner)."""
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


# ─────────────────────────────────────────────────────────────────────────────
# pygame_shape_constructor
# ─────────────────────────────────────────────────────────────────────────────

def pygame_shape_constructor(
    shape_x       = None,
    shape_y       = None,
    shape_width   = None,
    shape_height  = None,
    type          = None,
    paint         = None,
    canvas_width  = None,
    canvas_height = None,
    top_margin    = None,
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
            st  = _stem(sx + (ox-sx)*0.05, sy + (oy-sy)*0.3,
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
            st  = _stem(sx + (ox-sx)*0.05, sy + (oy-sy)*0.3,
                        sx + (ox-sx)*0.05, top_y, shape_width, color)
            g2  = shape_height * 0.4
            g3  = shape_height * 0.45
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
        # FIX: use head.shapes (not head.shape) so the inner white polygon is
        # included.  The hollow head now returns [outer_polygon, inner_white]
        # instead of a thick PygamePolyline, which was spotty at larger sizes.
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
            # *head.shapes unpacks [outer, inner_white] into the shape list
            result.append(([*head.shapes, st], 'half'))

        # ── whole ─────────────────────────────────────────────────────────────
        case 'whole':
            if not _need(shape_x, shape_y, shape_width, shape_height):
                return None
            outer = PygameEllipse(
                shape_x, shape_y - shape_height/2,
                shape_width, shape_height, color)
            inner = PygameEllipse(
                shape_x + shape_height/2.3,
                shape_y - shape_width/4,
                shape_height/2.2, shape_width/2, _WHITE)
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
            sw   = _accidental_sw(paint, shape_width)
            vert = PygameLine(
                shape_x - shape_width/20, shape_y - (shape_width - shape_width/4),
                shape_x - shape_width/20, shape_y + (shape_width - shape_width/1.4),
                color, sw)
            p0  = (shape_x - shape_width/20, shape_y + (shape_width - shape_width/1.3))
            cp  = (shape_x + shape_width*0.6, shape_y - shape_width*0.2)
            p1  = (shape_x - shape_width/20, shape_y + (shape_width - shape_width*1.2))
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
                p0  = (ox, shape_y+(shape_width-shape_width/1.3))
                cp  = (ox + shape_width*0.27*(2 if ox < shape_x else 1),
                       shape_y - shape_width*0.2)
                p1  = (ox, shape_y+(shape_width-shape_width*1.2))
                pts = _sample_rational_quadratic(p0, cp, p1, w=1.0)
                pts.append(p0)
                return v, PygamePolygon(pts, color)

            v1, c1 = _flat(shape_x - shape_width/2.3)
            v2, c2 = _flat(shape_x - shape_width/10)
            result.append(([v1, c1, v2, c2], 'bb'))

        # ── bar line ──────────────────────────────────────────────────────────
        # FIX: shape_width IS the desired pixel width for bar lines.
        # Using _accidental_sw would multiply by 0.15 — e.g. a 3 px bar
        # becomes 0.45, rounds to 1, and every bar looks hair-thin.
        case 'bar':
            if not _need(shape_x, shape_y, shape_height):
                return None
            sw = float(shape_width) if shape_width is not None else 2.0
            bar = PygameLine(
                shape_x, shape_y,
                shape_x, shape_y + shape_height,
                color, sw)
            result.append(([bar], 'bar'))

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
