"""The element vocabulary.

Every element is a function that takes the render context plus whatever
parameters a scene passes it, and returns a drawsvg group drawn around its own
local origin. Nothing here is tied to a particular picture: a fox, a cat and a
bear are all the ``creature`` element with different numbers.

Local origin per element is documented in each docstring, because that is what
a scene's ``at`` coordinate lines up with.
"""

from __future__ import annotations

import math
import random

import drawsvg as draw

from .geometry import (bezier_points, catmull_closed, polyline_path,
                       rounded_rect_path, star_points)
from .registry import element


# --------------------------------------------------------------- helpers

def _add(group, ctx, d, params, fill="none", ink=False):
    """Append a path to ``group`` styled for the current mode."""
    group.append(draw.Path(d, **ctx.style(params, fill, ink)))


def _ellipse_path(cx, cy, rx, ry) -> str:
    return (f"M {cx - rx:.3f},{cy:.3f} A {rx:.3f},{ry:.3f} 0 1 0 {cx + rx:.3f},{cy:.3f}"
            f" A {rx:.3f},{ry:.3f} 0 1 0 {cx - rx:.3f},{cy:.3f} Z")


def _opt(value, default):
    return default if value is None else value


def _furry(spine, width_at, t0=0.0, t1=1.0, samples=9):
    """Outline of a soft, tapering shape that follows ``spine``.

    ``width_at`` is evaluated on the *global* position along the whole spine,
    so a tip drawn from a slice of the spine lines up with the full shape.
    Few samples plus a smooth spline is what keeps a tail reading as fur
    rather than as a bent tube.
    """
    last = len(spine) - 1
    picks = [round(i * last / (samples - 1)) for i in range(samples)]
    left, right = [], []
    for i in picks:
        x, y = spine[i]
        a, b = spine[max(0, i - 1)], spine[min(last, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        half = width_at(t0 + (t1 - t0) * (i / last)) / 2
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))

    # Push a single point past the end; the spline rounds the tip around it.
    ex, ey = spine[last]
    px, py = spine[last - 1]
    length = math.hypot(ex - px, ey - py) or 1.0
    reach = width_at(t1) / 2
    tip = (ex + (ex - px) / length * reach, ey + (ey - py) / length * reach)
    return catmull_closed(left[:-1] + [tip] + right[::-1][1:], tension=0.9)


# ------------------------------------------------------------ primitives

@element("circle")
def circle(ctx, r=50, **params):
    """A circle centred on the origin."""
    g = draw.Group()
    _add(g, ctx, _ellipse_path(0, 0, r, r), params)
    return g


@element("ellipse")
def ellipse(ctx, width=100, height=60, **params):
    """An ellipse centred on the origin."""
    g = draw.Group()
    _add(g, ctx, _ellipse_path(0, 0, width / 2, height / 2), params)
    return g


@element("rect")
def rect(ctx, width=100, height=60, radius=0, **params):
    """A rectangle centred on the origin, with optional corner radius."""
    g = draw.Group()
    _add(g, ctx, rounded_rect_path(-width / 2, -height / 2, width, height, radius), params)
    return g


@element("polygon")
def polygon(ctx, points=None, **params):
    """A straight-edged closed shape through ``points``."""
    if not points:
        raise ValueError("'polygon' needs a 'points' list")
    g = draw.Group()
    _add(g, ctx, polyline_path([tuple(p) for p in points]), params)
    return g


@element("star")
def star(ctx, r=50, tips=5, inner=0.42, rotate=-90, **params):
    """A star centred on the origin, one tip pointing up by default."""
    g = draw.Group()
    _add(g, ctx, polyline_path(star_points(0, 0, r, tips, inner, rotate)), params)
    return g


@element("blob")
def blob(ctx, points=None, tension=1.0, **params):
    """A smooth organic shape through a few anchor points."""
    if not points:
        raise ValueError("'blob' needs a 'points' list")
    g = draw.Group()
    _add(g, ctx, catmull_closed([tuple(p) for p in points], tension), params)
    return g


@element("path")
def path(ctx, d="", **params):
    """A raw SVG path, for anything the other elements do not cover."""
    if not d:
        raise ValueError("'path' needs a 'd' string")
    g = draw.Group()
    _add(g, ctx, d, params)
    return g


@element("line")
def line(ctx, points=None, close=False, **params):
    """An open stroked line — no fill."""
    if not points or len(points) < 2:
        raise ValueError("'line' needs at least 2 points")
    g = draw.Group()
    params = {**params, "fill": None}
    _add(g, ctx, polyline_path([tuple(p) for p in points], close), params)
    return g


@element("text")
def text(ctx, text="", size=48, family="DejaVu Sans", anchor="middle", **params):
    """A line of text, anchored on the origin. Latin script renders reliably."""
    g = draw.Group()
    style = ctx.style(params, fill="#111111")
    g.append(draw.Text(text, size, 0, 0, font_family=family,
                       text_anchor=anchor, fill=style["fill"], stroke="none"))
    return g


# ------------------------------------------------------------- furniture

@element("cushion")
def cushion(ctx, width=900, height=260, fill="#E1362F", **params):
    """A floor cushion, origin at its centre."""
    g = draw.Group()
    _add(g, ctx, _ellipse_path(0, 0, width / 2, height / 2), params, fill)
    return g


@element("lamp")
def lamp(ctx, height=700, shade_width=250, shade_height=170, shade_taper=0.72,
         pole_width=26, shade_fill="#FBCF4B", pole_fill="#8A5A2B",
         base_width=150, cord=True, **params):
    """A floor lamp, origin at the centre of its base on the floor."""
    g = draw.Group()
    _add(g, ctx, _ellipse_path(0, 0, base_width / 2, base_width / 8), params, "#ffffff")
    _add(g, ctx, rounded_rect_path(-pole_width / 2, -height, pole_width, height, 0),
         params, pole_fill)
    top = -height
    half, half_top = shade_width / 2, shade_width * shade_taper / 2
    _add(g, ctx, polyline_path([(-half, top), (half, top),
                                (half_top, top - shade_height),
                                (-half_top, top - shade_height)]), params, shade_fill)
    if cord:
        cx, cy = -shade_width * 0.16, top
        _add(g, ctx, polyline_path([(cx, cy), (cx, cy + shade_height * 0.42)], close=False),
             {**params, "fill": None})
        _add(g, ctx, _ellipse_path(cx, cy + shade_height * 0.52, 14, 14), params, "#ffffff")
    return g


@element("plant")
def plant(ctx, pot_width=180, pot_height=150, pot_taper=0.82, leaves=3,
          leaf_length=260, leaf_width=90, spread=55, pot_fill="#C87941",
          leaf_fill="#3FA34D", **params):
    """A potted plant, origin at the centre of the pot's base."""
    g = draw.Group()
    top = -pot_height
    for i in range(leaves):
        t = 0 if leaves == 1 else i / (leaves - 1) * 2 - 1     # -1 .. 1
        angle = math.radians(t * spread)
        tip = (math.sin(angle) * leaf_length, top - math.cos(angle) * leaf_length)
        side = leaf_width / 2
        _add(g, ctx, catmull_closed([
            (0, top),
            (tip[0] * 0.45 - side, top + (tip[1] - top) * 0.45),
            tip,
            (tip[0] * 0.45 + side, top + (tip[1] - top) * 0.45)], tension=0.85),
            params, leaf_fill)
    half, half_bottom = pot_width / 2, pot_width * pot_taper / 2
    _add(g, ctx, polyline_path([(-half, top), (half, top),
                                (half_bottom, 0), (-half_bottom, 0)]), params, pot_fill)
    return g


@element("mug")
def mug(ctx, width=130, height=130, radius=18, fill="#2E7BC4", handle=True,
        motif="star", motif_fill="#ffffff", **params):
    """A mug, origin at the centre of its base."""
    g = draw.Group()
    if handle:
        outer, inner = height * 0.3, height * 0.16
        cx, cy = width / 2 + outer * 0.5, -height / 2
        _add(g, ctx, _ellipse_path(cx, cy, outer, outer), params, "#ffffff")
        _add(g, ctx, _ellipse_path(cx, cy, inner, inner), params, "#ffffff")
    _add(g, ctx, rounded_rect_path(-width / 2, -height, width, height, radius), params, fill)
    if motif == "star":
        _add(g, ctx, polyline_path(star_points(0, -height / 2, width * 0.26)),
             params, motif_fill)
    elif motif == "dot":
        _add(g, ctx, _ellipse_path(0, -height / 2, width * 0.18, width * 0.18),
             params, motif_fill)
    return g


@element("book")
def book(ctx, width=420, height=180, lift=110, cover_fill="#8A5A2B",
         page_fill="#ffffff", picture_fill="#3FA34D", lines=2, **params):
    """An open book seen from the front, origin at the bottom of its spine."""
    g = draw.Group()
    half = width / 2
    left = [(0, 0), (-half, -lift * 0.75), (-half, -lift * 0.75 - height), (0, -height)]
    right = [(0, 0), (half, -lift), (half, -lift - height), (0, -height)]
    _add(g, ctx, polyline_path(left), params, page_fill)
    _add(g, ctx, polyline_path(right), params, page_fill)

    inset = 0.12
    cover = [(half * inset, -lift * inset), (half * 0.94, -lift * 0.94),
             (half * 0.94, -lift * 0.94 - height * 0.88), (half * inset, -height * 0.92)]
    _add(g, ctx, polyline_path(cover), params, cover_fill)
    if picture_fill:
        pic = [(half * 0.34, -lift * 0.34 - height * 0.14),
               (half * 0.76, -lift * 0.76 - height * 0.14),
               (half * 0.76, -lift * 0.76 - height * 0.62),
               (half * 0.34, -lift * 0.34 - height * 0.62)]
        _add(g, ctx, polyline_path(pic), params, picture_fill)
    for k in range(1, lines + 1):
        y = -height * (0.25 + 0.22 * k)
        _add(g, ctx, polyline_path([(-half * 0.22, y - lift * 0.16),
                                    (-half * 0.82, y - lift * 0.62)], close=False),
             {**params, "fill": None, "stroke_width": ctx.defaults["stroke_width"] * 0.6})
    return g


@element("tree")
def tree(ctx, height=600, trunk_width=90, crown_width=460, crown_height=460,
         style="round", trunk_fill="#8A5A2B", crown_fill="#3FA34D", **params):
    """A tree, origin at the centre of the trunk's base."""
    g = draw.Group()
    _add(g, ctx, rounded_rect_path(-trunk_width / 2, -height, trunk_width, height, 0),
         params, trunk_fill)
    top = -height
    if style == "pine":
        for k in range(3):
            w = crown_width * (1 - k * 0.22) / 2
            base = top + crown_height * (0.34 - k * 0.26)
            _add(g, ctx, polyline_path([(-w, base), (w, base),
                                        (0, base - crown_height * 0.55)]), params, crown_fill)
    else:
        _add(g, ctx, catmull_closed([
            (0, top - crown_height * 0.55), (crown_width * 0.42, top - crown_height * 0.3),
            (crown_width * 0.5, top + crown_height * 0.08), (crown_width * 0.2, top + crown_height * 0.2),
            (-crown_width * 0.2, top + crown_height * 0.2), (-crown_width * 0.5, top + crown_height * 0.08),
            (-crown_width * 0.42, top - crown_height * 0.3)], tension=0.95), params, crown_fill)
    return g


@element("cloud")
def cloud(ctx, width=420, height=170, puffs=4, fill="#ffffff", **params):
    """A cloud, origin at its centre."""
    g = draw.Group()
    puffs = max(2, int(puffs))
    # Each puff is a semicircle, so a wider puff is also a taller one. Middle
    # puffs get the most width; the whole shape is then squashed to `height`.
    weights = [0.55 + 0.45 * math.sin(math.pi * (i + 0.5) / puffs) for i in range(puffs)]
    total = sum(weights)
    widths = [width * w / total for w in weights]
    tallest = max(widths) / 2
    skirt = tallest * 0.28
    natural = tallest + skirt

    x = -width / 2
    d = [f"M {x:.2f},0"]
    for w in widths:
        x += w
        d.append(f"A {w / 2:.2f},{w / 2:.2f} 0 0 1 {x:.2f},0")
    d.append(f"L {width / 2:.2f},{skirt:.2f} L {-width / 2:.2f},{skirt:.2f} Z")

    inner = draw.Group()
    _add(inner, ctx, " ".join(d), params, fill)
    squash = height / natural
    inner.args["transform"] = (f"scale(1,{squash:.4f}) "
                               f"translate(0,{(natural / 2 - skirt):.2f})")
    g.append(inner)
    return g


@element("celestial")
def celestial(ctx, r=140, phase="full", fill="#FBCF4B", rays=0, ray_length=70, **params):
    """A sun or moon, origin at its centre. ``phase`` is full or crescent."""
    g = draw.Group()
    for i in range(rays):
        ang = 2 * math.pi * i / rays
        inner, outer = r * 1.16, r * 1.16 + ray_length
        _add(g, ctx, polyline_path([(math.cos(ang) * inner, math.sin(ang) * inner),
                                    (math.cos(ang) * outer, math.sin(ang) * outer)],
                                   close=False), {**params, "fill": None})
    if phase == "crescent":
        # Outer circle down its left side, then back along the left side of an
        # offset circle that bites the right half away.
        bite = r * params.pop("bite", 0.7)
        ri = math.hypot(bite, r)          # so the cut passes through (0, +-r)
        steps = 26
        outer = [(math.cos(a) * r, math.sin(a) * r)
                 for a in [math.pi * (0.5 + k / steps) for k in range(steps + 1)]]
        a0, a1 = math.atan2(-r, -bite) % (2 * math.pi), math.atan2(r, -bite)
        inner = [(bite + math.cos(a0 + (a1 - a0) * k / steps) * ri,
                  math.sin(a0 + (a1 - a0) * k / steps) * ri)
                 for k in range(steps + 1)]
        _add(g, ctx, polyline_path(outer + inner), params, fill)
    else:
        _add(g, ctx, _ellipse_path(0, 0, r, r), params, fill)
    return g


@element("house")
def house(ctx, width=520, height=380, roof_height=220, roof_overhang=60,
         wall_fill="#F0E2CC", roof_fill="#C0533F", door_fill="#8A5A2B",
         windows=2, window_fill="#9CC7E8", **params):
    """A simple house, origin at the centre of its base."""
    g = draw.Group()
    half = width / 2
    _add(g, ctx, polyline_path([(-half, -height), (half, -height), (half, 0), (-half, 0)]),
         params, wall_fill)
    _add(g, ctx, polyline_path([(-half - roof_overhang, -height), (half + roof_overhang, -height),
                                (0, -height - roof_height)]), params, roof_fill)
    door_w, door_h = width * 0.22, height * 0.5
    _add(g, ctx, rounded_rect_path(-door_w / 2, -door_h, door_w, door_h, door_w * 0.45),
         params, door_fill)
    for i in range(windows):
        t = (i + 0.5) / windows * 2 - 1
        wx = t * width * 0.34
        size = width * 0.16
        _add(g, ctx, rounded_rect_path(wx - size / 2, -height * 0.78, size, size, size * 0.18),
             params, window_fill)
    return g


# -------------------------------------------------------------- creature

@element("creature")
def creature(ctx, body=None, belly=None, head=None, ears=None, eyes=None,
             muzzle=None, nose=None, mouth=None, cheeks=None, tuft=None,
             tail=None, feet=None, arms=None, fur="#F4802B", light="#FFF1E0",
             **params):
    """A sitting animal, origin at the point it sits on.

    Every part is optional and parameterised, so the same code draws a fox, a
    cat, a bear or a rabbit — the difference is ear shape, proportions, tail
    style and colours. Pass ``null`` for a part to leave it out.
    """
    g = draw.Group()
    body = _opt(body, {})
    head = _opt(head, {})

    body_w = body.get("width", 460)
    body_h = body.get("height", 400)
    body_fill = body.get("fill", fur)
    head_w = head.get("width", 460)
    head_h = head.get("height", 400)
    head_fill = head.get("fill", fur)

    body_cy = -body_h / 2 + body.get("dy", 0)
    head_cy = -(body_h * head.get("overlap", 0.86) + head_h / 2) + head.get("dy", 0)

    def part(spec, key, default):
        return _opt(spec, {}).get(key, default)

    # ---- tail (behind everything) ----
    if tail is not None:
        tail = _opt(tail, {})
        length = tail.get("length", 380)
        width = tail.get("width", 210)
        side = -1 if tail.get("side", "left") == "left" else 1
        # angle is a plain direction: 0 points right, 90 points straight up.
        angle = math.radians(tail.get("angle", 195 if side < 0 else -15))
        root = (side * body_w * 0.34, body_cy + body_h * 0.28 + tail.get("dy", 0))
        end = (root[0] + math.cos(angle) * length,
               root[1] - math.sin(angle) * length)
        # curl bulges the spine perpendicular to the root -> end direction
        nx, ny = -math.sin(-angle), math.cos(-angle)
        bulge = width * tail.get("curl", 0.45) * side
        spine = bezier_points(
            root,
            (root[0] + (end[0] - root[0]) * 0.35 + nx * bulge,
             root[1] + (end[1] - root[1]) * 0.35 + ny * bulge),
            (root[0] + (end[0] - root[0]) * 0.75 + nx * bulge * 0.6,
             root[1] + (end[1] - root[1]) * 0.75 + ny * bulge * 0.6),
            end, steps=28)
        style = tail.get("shape", "bushy")
        if style == "thin":
            def width_at(t):
                return width * (0.55 - 0.25 * t)
        elif style == "round":
            def width_at(t):
                return width * (0.7 + 0.3 * math.sin(math.pi * t))
        else:                                    # bushy: fat in the middle
            def width_at(t):
                return width * (0.52 + 0.48 * math.sin(math.pi * t ** 0.8))
        _add(g, ctx, _furry(spine, width_at), params, tail.get("fill", fur))
        if tail.get("tip", True):
            at = tail.get("tip_at", 0.62)
            cut = int(len(spine) * at)
            _add(g, ctx, _furry(spine[cut:], width_at, t0=at, t1=1.0, samples=6),
                 params, tail.get("tip_fill", light))

    # ---- body ----
    _add(g, ctx, catmull_closed([
        (0, body_cy + body_h / 2), (body_w * 0.44, body_cy + body_h * 0.28),
        (body_w / 2, body_cy), (body_w * 0.4, body_cy - body_h * 0.36),
        (0, body_cy - body_h / 2), (-body_w * 0.4, body_cy - body_h * 0.36),
        (-body_w / 2, body_cy), (-body_w * 0.44, body_cy + body_h * 0.28)],
        tension=0.9), params, body_fill)

    if belly is not None:
        belly = _opt(belly, {})
        bw = belly.get("width", body_w * 0.52)
        bh = belly.get("height", body_h * 0.62)
        bcy = body_cy + belly.get("dy", body_h * 0.1)
        _add(g, ctx, catmull_closed([
            (0, bcy + bh / 2), (bw * 0.46, bcy + bh * 0.16), (bw / 2, bcy - bh * 0.22),
            (0, bcy - bh / 2), (-bw / 2, bcy - bh * 0.22), (-bw * 0.46, bcy + bh * 0.16)],
            tension=0.9), params, belly.get("fill", light))

    # ---- feet ----
    if feet is not None:
        feet = _opt(feet, {})
        fw, fh = feet.get("width", 150), feet.get("height", 100)
        spread = feet.get("spread", body_w * 0.24)
        fy = feet.get("dy", -fh * 0.35)
        for sign in (-1, 1):
            _add(g, ctx, _ellipse_path(sign * spread, fy, fw / 2, fh / 2),
                 params, feet.get("fill", "#8A5A2B"))

    # ---- ears (behind head) ----
    if ears is not None:
        ears = _opt(ears, {})
        ew, eh = ears.get("width", 150), ears.get("height", 220)
        spread = ears.get("spread", head_w * 0.3)
        tilt = ears.get("tilt", 16)
        base_y = head_cy - head_h * 0.3
        for sign in (-1, 1):
            bx = sign * spread
            lean = math.radians(sign * tilt)
            tip = (bx + math.sin(lean) * eh, base_y - math.cos(lean) * eh)
            if ears.get("shape", "pointed") == "round":
                _add(g, ctx, _ellipse_path(bx, base_y - eh * 0.35, ew / 2, eh / 2),
                     params, ears.get("fill", fur))
                _add(g, ctx, _ellipse_path(bx, base_y - eh * 0.35, ew * 0.28, eh * 0.3),
                     params, ears.get("inner_fill", light))
            else:
                _add(g, ctx, catmull_closed([(bx - ew / 2, base_y), tip,
                                             (bx + ew / 2, base_y - eh * 0.12)],
                                            tension=0.45), params, ears.get("fill", fur))
                inner = ears.get("inner_scale", 0.55)
                itip = (bx + (tip[0] - bx) * inner * 0.85, base_y + (tip[1] - base_y) * inner * 0.85)
                _add(g, ctx, catmull_closed([(bx - ew * inner * 0.45, base_y - eh * 0.02), itip,
                                             (bx + ew * inner * 0.45, base_y - eh * 0.1)],
                                            tension=0.45), params,
                     ears.get("inner_fill", light))

    # ---- head ----
    _add(g, ctx, catmull_closed([
        (0, head_cy + head_h / 2), (head_w * 0.42, head_cy + head_h * 0.26),
        (head_w / 2, head_cy), (head_w * 0.42, head_cy - head_h * 0.28),
        (0, head_cy - head_h / 2), (-head_w * 0.42, head_cy - head_h * 0.28),
        (-head_w / 2, head_cy), (-head_w * 0.42, head_cy + head_h * 0.26)],
        tension=0.9), params, head_fill)

    if tuft is not None:
        tuft = _opt(tuft, {})
        tw, th = tuft.get("width", head_w * 0.34), tuft.get("height", head_h * 0.1)
        ty = head_cy - head_h * 0.44
        _add(g, ctx, catmull_closed([(-tw / 2, ty + th * 0.3), (-tw * 0.2, ty - th),
                                     (tw * 0.05, ty - th * 0.2), (tw * 0.32, ty - th * 0.85),
                                     (tw / 2, ty + th * 0.3)],
                                    tension=0.55), params, tuft.get("fill", fur))

    if muzzle is not None:
        muzzle = _opt(muzzle, {})
        mw, mh = muzzle.get("width", head_w * 0.55), muzzle.get("height", head_h * 0.5)
        mcy = head_cy + muzzle.get("dy", head_h * 0.16)
        _add(g, ctx, catmull_closed([
            (0, mcy + mh / 2), (mw * 0.46, mcy + mh * 0.1), (mw / 2, mcy - mh * 0.3),
            (0, mcy - mh / 2), (-mw / 2, mcy - mh * 0.3), (-mw * 0.46, mcy + mh * 0.1)],
            tension=0.9), params, muzzle.get("fill", light))

    if cheeks is not None:
        cheeks = _opt(cheeks, {})
        cw, ch = cheeks.get("width", head_w * 0.2), cheeks.get("height", head_h * 0.12)
        ccy = head_cy + cheeks.get("dy", head_h * 0.06)
        spread = cheeks.get("spread", head_w * 0.36)
        for sign in (-1, 1):
            _add(g, ctx, _ellipse_path(sign * spread, ccy, cw / 2, ch / 2),
                 params, cheeks.get("fill", "#F6A7A1"))

    if eyes is not None:
        eyes = _opt(eyes, {})
        er = eyes.get("r", head_w * 0.07)
        spread = eyes.get("spread", head_w * 0.14)
        ecy = head_cy - head_h * 0.02 + eyes.get("dy", 0)
        squash = eyes.get("squash", 1.12)
        for sign in (-1, 1):
            _add(g, ctx, _ellipse_path(sign * spread, ecy, er, er * squash),
                 params, ink=True)

    if nose is not None:
        nose = _opt(nose, {})
        nw, nh = nose.get("width", head_w * 0.1), nose.get("height", head_w * 0.075)
        ncy = head_cy + nose.get("dy", head_h * 0.12)
        _add(g, ctx, _ellipse_path(0, ncy, nw / 2, nh / 2), params, ink=True)
        if mouth is not False:
            mw = _opt(mouth, {}).get("width", head_w * 0.11)
            my = ncy + nh / 2
            smile = (f"M {-mw:.2f},{my:.2f} Q {-mw * 0.5:.2f},{my + mw * 0.95:.2f}"
                     f" 0,{my + mw * 0.12:.2f} Q {mw * 0.5:.2f},{my + mw * 0.95:.2f}"
                     f" {mw:.2f},{my:.2f}")
            _add(g, ctx, smile,
                 {**params, "fill": None,
                  "stroke_width": ctx.defaults["stroke_width"] * 0.8})

    # ---- arms (in front) ----
    if arms is not None:
        arms = _opt(arms, {})
        aw, ah = arms.get("width", 140), arms.get("height", 110)
        spread = arms.get("spread", body_w * 0.42)
        ay = body_cy + arms.get("dy", -body_h * 0.1)
        for sign in (-1, 1):
            _add(g, ctx, _ellipse_path(sign * spread, ay, aw / 2, ah / 2),
                 params, arms.get("fill", fur))
    return g


# ------------------------------------------------------------ composition

@element("group")
def group(ctx, children=None, **params):
    """Nest layers so they can be positioned and scaled as one unit."""
    if not children:
        raise ValueError("'group' needs a 'children' list of layers")
    g = draw.Group()
    for child in children:
        g.append(ctx.build(child))
    return g


@element("repeat")
def repeat(ctx, child=None, count=1, along=None, grid=None, scatter=None, **params):
    """Place one layer many times: along a line, on a grid, or scattered.

    ``scatter`` takes a seed, so the same scene always renders identically.
    """
    if not child:
        raise ValueError("'repeat' needs a 'child' layer")
    g = draw.Group()

    if grid:
        cols, rows = grid.get("cols", count), grid.get("rows", 1)
        dx, dy = grid.get("dx", 100), grid.get("dy", 100)
        spots = [(c * dx, r * dy) for r in range(rows) for c in range(cols)]
    elif along:
        start, end = along["from"], along["to"]
        spots = [(start[0] + (end[0] - start[0]) * (i / max(1, count - 1)),
                  start[1] + (end[1] - start[1]) * (i / max(1, count - 1)))
                 for i in range(count)]
    elif scatter:
        rng = random.Random(scatter.get("seed", 0))
        x, y, w, h = scatter["box"]
        spots = [(rng.uniform(x, x + w), rng.uniform(y, y + h)) for _ in range(count)]
    else:
        spots = [(0, 0)] * count

    jitter = (scatter or {}).get("scale_jitter", 0)
    rng = random.Random((scatter or {}).get("seed", 0) + 1)
    for sx, sy in spots:
        holder = draw.Group()
        scale = 1 + rng.uniform(-jitter, jitter) if jitter else 1
        holder.args["transform"] = (f"translate({sx:.3f},{sy:.3f})"
                                    + (f" scale({scale:.4f})" if scale != 1 else ""))
        holder.append(ctx.build(child))
        g.append(holder)
    return g
