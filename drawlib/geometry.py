"""Geometry helpers that produce SVG path data.

Everything here is pure maths: the functions take a handful of numbers and
return either a list of points or an SVG ``d`` string. Nothing in this module
knows about scenes, colours or elements.
"""

import math

Point = tuple[float, float]


def catmull_closed(points: list[Point], tension: float = 1.0) -> str:
    """Turn a few anchor points into a smooth closed shape.

    Converts a Catmull-Rom spline through ``points`` into cubic Beziers, which
    is what makes a handful of coordinates read as an organic blob rather than
    a polygon. Used for bodies, heads, tails, ears and leaves.
    """
    if len(points) < 3:
        raise ValueError("catmull_closed needs at least 3 points")
    n = len(points)
    d = [f"M {points[0][0]:.3f},{points[0][1]:.3f}"]
    for i in range(n):
        p0, p1 = points[(i - 1) % n], points[i]
        p2, p3 = points[(i + 1) % n], points[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension,
              p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension,
              p2[1] - (p3[1] - p1[1]) / 6 * tension)
        d.append(f"C {c1[0]:.3f},{c1[1]:.3f} {c2[0]:.3f},{c2[1]:.3f}"
                 f" {p2[0]:.3f},{p2[1]:.3f}")
    d.append("Z")
    return " ".join(d)


def polyline_path(points: list[Point], close: bool = True) -> str:
    """Straight-edged path through ``points``."""
    if not points:
        raise ValueError("polyline_path needs at least 1 point")
    d = [f"M {points[0][0]:.3f},{points[0][1]:.3f}"]
    d += [f"L {x:.3f},{y:.3f}" for x, y in points[1:]]
    if close:
        d.append("Z")
    return " ".join(d)


def star_points(cx: float, cy: float, r: float, tips: int = 5,
                inner: float = 0.42, rotate: float = -90.0) -> list[Point]:
    """Points of a star. ``rotate`` -90 puts one tip straight up."""
    pts = []
    for i in range(tips * 2):
        ang = math.radians(rotate + i * 180 / tips)
        rad = r if i % 2 == 0 else r * inner
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return pts


def bezier_points(p0: Point, p1: Point, p2: Point, p3: Point,
                  steps: int = 40) -> list[Point]:
    """Sample a cubic Bezier — useful when a curve needs to be walked."""
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0]
                    + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1]
                    + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out


def ribbon(spine: list[Point], width_at) -> str:
    """A thick stroke of varying width following ``spine`` — tails, branches.

    ``width_at`` maps a position along the spine (0..1) to a width.
    """
    left, right = [], []
    last = len(spine) - 1
    for i, (x, y) in enumerate(spine):
        a, b = spine[max(0, i - 1)], spine[min(last, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        half = width_at(i / last) / 2
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))
    return catmull_closed(left + right[::-1], tension=0.5)


def rounded_rect_path(x: float, y: float, w: float, h: float, r: float) -> str:
    """Rectangle path with uniform corner radius, drawn from its top-left."""
    r = max(0.0, min(r, w / 2, h / 2))
    return (f"M {x + r:.3f},{y:.3f} H {x + w - r:.3f} A {r},{r} 0 0 1 {x + w:.3f},{y + r:.3f}"
            f" V {y + h - r:.3f} A {r},{r} 0 0 1 {x + w - r:.3f},{y + h:.3f}"
            f" H {x + r:.3f} A {r},{r} 0 0 1 {x:.3f},{y + h - r:.3f}"
            f" V {y + r:.3f} A {r},{r} 0 0 1 {x + r:.3f},{y:.3f} Z")
