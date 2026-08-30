"""A second wave of elements: everyday props for storybook scenes.

Kept separate from ``elements.py`` (which holds primitives and the
``creature`` element) purely to keep each file a manageable size. Registration
works the same way — importing this module runs its ``@element`` decorators.
"""

from __future__ import annotations

import math

import drawsvg as draw

from .elements import _add, _ellipse_path, _furry, _opt, _tapered
from .geometry import (bezier_points, catmull_closed, catmull_open_points,
                       polyline_path, rounded_rect_path, star_points)
from .registry import element


# ------------------------------------------------------------------ vessels

@element("vessel")
def vessel(ctx, width=200, height=220, taper=0.85, fill="#2E7BC4",
          handle=None, spout=None, lid=None, **params):
    """A pourable container: watering can, kettle, teapot, pitcher, jug.

    Origin sits on the ground at the container's centre-front.
    """
    g = draw.Group()
    top, bottom_half, top_half = -height, width / 2, width * taper / 2
    _add(g, ctx, polyline_path([(-bottom_half, 0), (bottom_half, 0),
                                (top_half, top), (-top_half, top)]), params, fill)

    if handle is not None:
        handle = _opt(handle, {})
        side = 1 if handle.get("side", "right") == "right" else -1
        hx = side * top_half * handle.get("reach", 1.15)
        hy = top + height * handle.get("dy", 0.4)
        outer, inner = height * handle.get("size", 0.32), height * handle.get("size", 0.32) * 0.5
        _add(g, ctx, _ellipse_path(hx, hy, outer, outer), params, "none")
        ring = catmull_closed([
            (hx - outer, hy), (hx, hy - outer), (hx + outer, hy), (hx, hy + outer)],
            tension=0.9)
        _add(g, ctx, ring, params, fill)
        _add(g, ctx, _ellipse_path(hx, hy, inner, inner), params, ctx.color(params.get(
            "cutout", "#ffffff")))

    if spout is not None:
        spout = _opt(spout, {})
        side = 1 if spout.get("side", "left") == "left" else -1
        sx, sy = side * -top_half * 0.6, top + height * spout.get("at", 0.12)
        length = spout.get("length", height * 0.55)
        angle = math.radians(spout.get("angle", 55))
        tip = (sx + side * -math.cos(angle) * length, sy - math.sin(angle) * length)
        spine = bezier_points((sx, sy),
                              (sx + side * -length * 0.3, sy - length * 0.1),
                              (tip[0] - side * -length * 0.15, tip[1] + length * 0.15),
                              tip, steps=16)
        _add(g, ctx, _tapered(spine, width * 0.22, width * 0.1), params, fill)

    if lid is not None:
        lid = _opt(lid, {})
        lw = top_half * lid.get("scale", 1.05)
        _add(g, ctx, _ellipse_path(0, top, lw, lw * 0.28), params, fill)
        _add(g, ctx, _ellipse_path(0, top - height * 0.09, lw * 0.22, lw * 0.22),
             params, fill)
    else:
        _add(g, ctx, _ellipse_path(0, top, top_half, top_half * 0.24), params, fill)
    return g


@element("bowl")
def bowl(ctx, width=200, height=90, fill="#F6E7CB", **params):
    """A shallow bowl standing on the ground, origin at the centre of its base."""
    g = draw.Group()
    top = -height
    half, half_top = width * 0.66 / 2, width / 2
    _add(g, ctx, polyline_path([(-half, 0), (half, 0), (half_top, top), (-half_top, top)]),
         params, fill)
    _add(g, ctx, _ellipse_path(0, top, half_top, height * 0.3), params, fill)
    return g


@element("stump")
def stump(ctx, width=150, height=110, fill="#8A5A2B", ring_fill="#A9763F", **params):
    """A cut tree stump, origin at the centre of its base."""
    g = draw.Group()
    half = width / 2
    _add(g, ctx, polyline_path([(-half, 0), (half, 0), (half, -height), (-half, -height)]),
         params, fill)
    _add(g, ctx, _ellipse_path(0, -height, half, half * 0.3), params, ring_fill)
    for k in (0.6, 0.32):
        _add(g, ctx, _ellipse_path(0, -height, half * k, half * 0.3 * k), params, "none")
    return g


# ---------------------------------------------------------------- nature

@element("flower")
def flower(ctx, height=260, bloom_r=70, petals=6, stem_fill="#3FA34D",
          bloom_fill="#F6A5B4", center_fill="#F7C948", face=False, **params):
    """A stemmed flower, origin at its base on the ground."""
    g = draw.Group()
    top = -height
    _add(g, ctx, _tapered([(0, 0), (0, top * 0.5), (0, top)], 18, 12), params, stem_fill)
    leaf = catmull_closed([(0, top * 0.55), (bloom_r * 0.7, top * 0.62),
                           (bloom_r * 0.55, top * 0.42), (0, top * 0.42)], tension=0.8)
    _add(g, ctx, leaf, params, stem_fill)
    for i in range(petals):
        ang = 2 * math.pi * i / petals
        px, py = top + math.sin(ang) * bloom_r * 1.05, math.cos(ang) * bloom_r * 1.05 * -1
        _add(g, ctx, _ellipse_path(math.cos(ang) * bloom_r * 0.85,
                                   top - math.sin(ang) * bloom_r * 0.05,
                                   bloom_r * 0.62, bloom_r * 0.46), params, bloom_fill)
    _add(g, ctx, _ellipse_path(0, top, bloom_r * 0.55, bloom_r * 0.55), params, center_fill)
    if face:
        for sx in (-1, 1):
            _add(g, ctx, _ellipse_path(sx * bloom_r * 0.2, top - bloom_r * 0.05,
                                       bloom_r * 0.07, bloom_r * 0.09), params, ink=True)
        smile = (f"M {-bloom_r * 0.18:.2f},{top + bloom_r * 0.16:.2f}"
                f" Q 0,{top + bloom_r * 0.3:.2f} {bloom_r * 0.18:.2f},{top + bloom_r * 0.16:.2f}")
        _add(g, ctx, smile, {**params, "fill": None,
                             "stroke_width": ctx.defaults["stroke_width"] * 0.7})
    return g


@element("droplet")
def droplet(ctx, r=22, fill="#BFE0F2", **params):
    """A single water droplet, origin at its centre."""
    g = draw.Group()
    d = catmull_closed([(0, -r * 1.5), (r * 0.85, r * 0.35),
                        (0, r * 1.0), (-r * 0.85, r * 0.35)], tension=1.1)
    _add(g, ctx, d, params, fill)
    return g


@element("bubble")
def bubble(ctx, r=30, fill="none", **params):
    """A round bubble with a small highlight arc, origin at its centre."""
    g = draw.Group()
    _add(g, ctx, _ellipse_path(0, 0, r, r), params, fill)
    hx, hy, hr = -r * 0.35, -r * 0.35, r * 0.3
    _add(g, ctx, _ellipse_path(hx, hy, hr, hr * 0.7), {**params, "fill": None,
                                                        "stroke_width": ctx.defaults["stroke_width"] * 0.6})
    return g


@element("butterfly")
def butterfly(ctx, wingspan=90, fill="#F7C948", body_fill="#3A3A3A", **params):
    """A small butterfly, origin at the centre of its body."""
    g = draw.Group()
    w = wingspan / 2
    for side in (-1, 1):
        _add(g, ctx, catmull_closed([
            (0, -w * 0.1), (side * w * 0.85, -w * 0.55), (side * w * 0.55, -w * 0.05),
            (side * w * 0.2, w * 0.05)], tension=0.9), params, fill)
        _add(g, ctx, catmull_closed([
            (0, w * 0.05), (side * w * 0.55, w * 0.15), (side * w * 0.35, w * 0.5),
            (0, w * 0.35)], tension=0.9), params, fill)
    _add(g, ctx, _tapered([(0, -w * 0.5), (0, w * 0.4)], w * 0.13, w * 0.1), params, body_fill)
    return g


@element("steam")
def steam(ctx, height=140, width=44, fill="#ffffff", **params):
    """A rising wavy steam curl, origin at its base."""
    g = draw.Group()
    spine = [(0, 0), (width * 0.5, -height * 0.28), (-width * 0.5, -height * 0.58),
            (width * 0.3, -height * 0.85), (0, -height)]
    sampled = bezier_points(spine[0], spine[1], spine[2], spine[3], steps=20) + \
        bezier_points(spine[2], spine[3], spine[3], spine[4], steps=8)
    _add(g, ctx, _tapered(sampled, width * 0.3, width * 0.12), params, fill)
    return g


# -------------------------------------------------------------- everyday

@element("heart")
def heart(ctx, size=60, fill="#DC5B4C", **params):
    """A heart, origin at its centre."""
    g = draw.Group()
    s = size / 2
    d = catmull_closed([
        (0, s * 0.9), (-s * 1.05, s * 0.05), (-s * 0.95, -s * 0.55),
        (-s * 0.35, -s * 0.85), (0, -s * 0.35),
        (s * 0.35, -s * 0.85), (s * 0.95, -s * 0.55), (s * 1.05, s * 0.05)],
        tension=0.95)
    _add(g, ctx, d, params, fill)
    return g


@element("citrus_slice")
def citrus_slice(ctx, r=40, rind_fill="#F7D34E", flesh_fill="#FCEB9E", segments=8, **params):
    """A round citrus slice, origin at its centre."""
    g = draw.Group()
    _add(g, ctx, _ellipse_path(0, 0, r, r), params, rind_fill)
    _add(g, ctx, _ellipse_path(0, 0, r * 0.82, r * 0.82), params, flesh_fill)
    for i in range(segments):
        ang = 2 * math.pi * i / segments
        _add(g, ctx, polyline_path([(0, 0), (math.cos(ang) * r * 0.8,
                                             math.sin(ang) * r * 0.8)], close=False),
             {**params, "fill": None, "stroke_width": ctx.defaults["stroke_width"] * 0.5})
    return g


@element("splat")
def splat(ctx, r=50, fill="#D2762F", drips=3, **params):
    """An irregular paint splat with a few small satellite drops."""
    g = draw.Group()
    anchors = [(1.0, 0), (0.55, 0.7), (0.85, 1.3), (0.2, 1.85), (-0.5, 1.5),
              (-1.0, 0.9), (-0.7, 0.1), (-1.05, -0.7), (-0.3, -1.2),
              (0.4, -0.9), (0.9, -1.3)]
    pts = [(math.cos(a * math.pi) * r * m, math.sin(a * math.pi) * r * m)
          for m, a in anchors]
    _add(g, ctx, catmull_closed(pts, tension=1.15), params, fill)
    for i in range(drips):
        ang = 2 * math.pi * (i + 0.5) / max(drips, 1) + 0.8
        dist = r * (1.5 + 0.3 * (i % 2))
        _add(g, ctx, _ellipse_path(math.cos(ang) * dist, math.sin(ang) * dist,
                                   r * 0.14, r * 0.14), params, fill)
    return g


@element("easel")
def easel(ctx, height=340, width=210, canvas_fill="#ffffff", wood_fill="#A9763F",
         picture=True, **params):
    """A painter's easel with a small canvas, origin where the front legs meet the ground."""
    g = draw.Group()
    leg = width * 0.42
    for side in (-1, 1):
        _add(g, ctx, _tapered([(0, -height * 0.94), (side * leg, 0)], 16, 20),
             params, wood_fill)
    _add(g, ctx, _tapered([(0, -height * 0.94), (-leg * 0.55, -height * 0.1)], 14, 18),
         params, wood_fill)
    cw, ch = width * 0.92, height * 0.78
    cy = -height * 0.98
    _add(g, ctx, rounded_rect_path(-cw / 2, cy, cw, ch, 10), params, canvas_fill)
    _add(g, ctx, polyline_path([(-cw * 0.46, cy + ch * 0.15), (cw * 0.46, cy + ch * 0.15)],
                               close=False), params, wood_fill)
    if picture:
        base = cy + ch * 0.68
        _add(g, ctx, polyline_path([(-cw * 0.3, base), (0, base - ch * 0.32),
                                    (cw * 0.3, base)]),
             {**params, "fill": None, "stroke_width": ctx.defaults["stroke_width"] * 0.6})
        _add(g, ctx, _ellipse_path(cw * 0.22, cy + ch * 0.24, ch * 0.09, ch * 0.09),
             {**params, "fill": None, "stroke_width": ctx.defaults["stroke_width"] * 0.6})
    return g


@element("tub")
def tub(ctx, width=460, height=220, depth=70, fill="#ffffff", feet_fill="#8B6242",
       **params):
    """A clawfoot bathtub, origin at the centre of its base on the floor."""
    g = draw.Group()
    half = width / 2
    for side in (-1, 1):
        _add(g, ctx, _ellipse_path(side * half * 0.72, 0, width * 0.06, width * 0.045),
             params, feet_fill)
    body_y = -height * 0.35
    _add(g, ctx, catmull_closed([
        (-half, body_y), (-half * 0.98, body_y - height * 0.45),
        (0, body_y - height * 0.6), (half * 0.98, body_y - height * 0.45),
        (half, body_y), (half * 0.9, body_y + depth * 0.3),
        (-half * 0.9, body_y + depth * 0.3)], tension=0.85), params, fill)
    _add(g, ctx, _ellipse_path(0, body_y - height * 0.6, half * 0.94, depth * 0.55),
         params, fill)
    return g


@element("duck")
def duck(ctx, size=90, fill="#F8CE4B", bill_fill="#E2892F", **params):
    """A small rubber duck, origin at its base (floating waterline)."""
    g = draw.Group()
    s = size
    _add(g, ctx, catmull_closed([
        (-s * 0.55, 0), (-s * 0.6, -s * 0.42), (-s * 0.1, -s * 0.6),
        (s * 0.35, -s * 0.5), (s * 0.55, -s * 0.18), (s * 0.3, 0)], tension=0.95),
        params, fill)
    hx, hy = -s * 0.28, -s * 0.72
    _add(g, ctx, _ellipse_path(hx, hy, s * 0.26, s * 0.24), params, fill)
    _add(g, ctx, polyline_path([(hx - s * 0.24, hy + s * 0.02), (hx - s * 0.42, hy - s * 0.02),
                                (hx - s * 0.22, hy + s * 0.14)]), params, bill_fill)
    _add(g, ctx, _ellipse_path(hx - s * 0.02, hy - s * 0.08, s * 0.04, s * 0.04),
         params, ink=True)
    return g


@element("bird")
def bird(ctx, size=70, fill="#7FC4E8", beak_fill="#F7C948", **params):
    """A small perching/flying bird, origin at its base."""
    g = draw.Group()
    s = size
    _add(g, ctx, catmull_closed([
        (-s * 0.5, -s * 0.05), (-s * 0.2, -s * 0.55), (s * 0.35, -s * 0.5),
        (s * 0.5, -s * 0.1), (s * 0.1, s * 0.05), (-s * 0.25, s * 0.02)], tension=0.9),
        params, fill)
    _add(g, ctx, catmull_closed([
        (-s * 0.05, -s * 0.28), (-s * 0.55, -s * 0.32), (-s * 0.5, -s * 0.05),
        (-s * 0.1, -s * 0.1)], tension=0.8), params, fill)
    _add(g, ctx, polyline_path([(s * 0.42, -s * 0.32), (s * 0.68, -s * 0.24),
                                (s * 0.4, -s * 0.18)]), params, beak_fill)
    _add(g, ctx, _ellipse_path(s * 0.28, -s * 0.36, s * 0.045, s * 0.045), params, ink=True)
    return g


# -------------------------------------------------------------- structures

@element("curl")
def curl(ctx, points=None, width_start=30, width_end=14, fill="#F4802B", **params):
    """A tapered tube through ``points`` — trunks, curled tails, ribbons, hoses, hanging vines.

    ``points`` may be just a few sparse control points; they are smoothed
    into a dense curve first so the tube can bend sharply without looping.
    """
    if not points or len(points) < 2:
        raise ValueError("'curl' needs at least 2 points")
    spine = catmull_open_points([tuple(p) for p in points], steps=10)
    g = draw.Group()
    _add(g, ctx, _tapered(spine, width_start, width_end), params, fill)
    return g


@element("tent")
def tent(ctx, width=340, height=280, fill="#EFDCC0", door_fill="#7A5537",
        stripe_fill=None, **params):
    """An A-frame tent seen from the front, origin at the centre of its base."""
    g = draw.Group()
    half = width / 2
    _add(g, ctx, polyline_path([(-half, 0), (half, 0), (0, -height)]), params, fill)
    if stripe_fill:
        _add(g, ctx, polyline_path([(-half * 0.35, 0), (half * 0.35, 0), (0, -height)]),
             params, stripe_fill)
    dw, dh = width * 0.3, height * 0.5
    _add(g, ctx, polyline_path([(-dw / 2, 0), (dw / 2, 0), (0, -dh)]), params, door_fill)
    return g


@element("campfire")
def campfire(ctx, width=220, flame_height=170, stone_fill="#8B8B8B",
            flame_fill="#E2892F", flame_inner="#F7C948", stones=6, **params):
    """A ring of stones with a small flame, origin at the centre of the ring."""
    g = draw.Group()
    r = width / 2
    for i in range(stones):
        ang = 2 * math.pi * i / stones
        sx, sy = math.cos(ang) * r, math.sin(ang) * r * 0.4
        _add(g, ctx, _ellipse_path(sx, sy, width * 0.11, width * 0.08), params, stone_fill)
    _add(g, ctx, catmull_closed([
        (0, 0), (-width * 0.22, -flame_height * 0.35), (0, -flame_height),
        (width * 0.22, -flame_height * 0.35)], tension=0.7), params, flame_fill)
    _add(g, ctx, catmull_closed([
        (0, -flame_height * 0.06), (-width * 0.11, -flame_height * 0.4),
        (0, -flame_height * 0.72), (width * 0.11, -flame_height * 0.4)], tension=0.7),
        params, flame_inner)
    return g


@element("backpack")
def backpack(ctx, width=190, height=230, fill="#4C8F5B", flap_fill=None,
            pocket_fill=None, **params):
    """A simple backpack, origin at the bottom centre."""
    g = draw.Group()
    flap_fill = flap_fill or fill
    pocket_fill = pocket_fill or fill
    _add(g, ctx, rounded_rect_path(-width / 2, -height, width, height, width * 0.28),
         params, fill)
    fh = height * 0.4
    _add(g, ctx, rounded_rect_path(-width * 0.56 / 2, -height - fh * 0.4,
                                   width * 0.56, fh, width * 0.24), params, flap_fill)
    pw, ph = width * 0.5, height * 0.32
    _add(g, ctx, rounded_rect_path(-pw / 2, -ph, pw, ph, pw * 0.3), params, pocket_fill)
    for side in (-1, 1):
        _add(g, ctx, _tapered([(side * width * 0.22, -height * 0.85),
                               (side * width * 0.3, 0)], 20, 20), params, fill)
    return g


@element("mushroom")
def mushroom(ctx, cap_r=70, stem_height=90, cap_fill="#DC5B4C", stem_fill="#FFF3E2",
            spots=3, **params):
    """A mushroom, origin at the bottom centre of the stem."""
    g = draw.Group()
    _add(g, ctx, rounded_rect_path(-cap_r * 0.32, -stem_height, cap_r * 0.64,
                                   stem_height, cap_r * 0.2), params, stem_fill)
    top = -stem_height
    _add(g, ctx, catmull_closed([
        (-cap_r, top), (-cap_r * 0.7, top - cap_r * 0.95), (0, top - cap_r * 1.1),
        (cap_r * 0.7, top - cap_r * 0.95), (cap_r, top)], tension=0.75), params, cap_fill)
    for i in range(spots):
        t = (i + 0.5) / spots * 2 - 1
        _add(g, ctx, _ellipse_path(t * cap_r * 0.55, top - cap_r * 0.55 - abs(t) * cap_r * 0.1,
                                   cap_r * 0.13, cap_r * 0.11), params, stem_fill)
    return g


@element("ladder")
def ladder(ctx, width=140, height=380, rungs=4, fill="#A9763F", **params):
    """A leaning ladder, origin at the bottom centre between the rails."""
    g = draw.Group()
    half = width / 2
    for side in (-1, 1):
        _add(g, ctx, _tapered([(side * half, 0), (side * half * 0.8, -height)], 16, 14),
             params, fill)
    for i in range(1, rungs + 1):
        t = i / (rungs + 1)
        y = -height * t
        w = half * (1 - t * 0.2)
        _add(g, ctx, rounded_rect_path(-w, y - 8, 2 * w, 16, 6), params, fill)
    return g


@element("books")
def books(ctx, width=200, thickness=34, count=3, lean=0, fills=None, **params):
    """A stack (or leaning pile) of books, origin at the bottom centre."""
    g = draw.Group()
    fills = fills or ["#B84A3A", "#3F7D5A", "#E08A3C", "#2E7BC4"]
    y = 0
    for i in range(count):
        w = width * (1 - i * 0.05)
        x_off = lean * i
        book = draw.Group()
        book.args["transform"] = f"translate({x_off},{y - thickness}) rotate({lean * i * 0.4})"
        _add(book, ctx, rounded_rect_path(-w / 2, 0, w, thickness, 6), params,
             fills[i % len(fills)])
        g.append(book)
        y -= thickness * 0.92
    return g


@element("stand")
def stand(ctx, width=440, height=260, top_height=40, fill="#A9763F",
         top_fill=None, leg_fill=None, **params):
    """A market stand / counter, origin at the centre of the ground in front."""
    g = draw.Group()
    top_fill, leg_fill = top_fill or fill, leg_fill or fill
    half = width / 2
    _add(g, ctx, rounded_rect_path(-half, -height, width, height - top_height, 10),
         params, fill)
    _add(g, ctx, rounded_rect_path(-half * 1.04, -height, width * 1.04, top_height, 10),
         params, top_fill)
    return g


@element("awning")
def awning(ctx, width=460, height=110, droop=40, stripes=5,
          fills=("#D64545", "#FFF1DC"), **params):
    """A striped canopy over a stand, origin at the centre of its top edge."""
    g = draw.Group()
    seg = width / stripes
    for i in range(stripes):
        x0 = -width / 2 + i * seg
        fill = fills[i % len(fills)]
        _add(g, ctx, polyline_path([(x0, 0), (x0 + seg, 0),
                                    (x0 + seg, height), (x0 + seg * 0.5, height + droop),
                                    (x0, height)]), params, fill)
    return g


@element("basket")
def basket(ctx, width=260, height=170, taper=0.72, fill="#B0793F",
          weave=3, handle=True, **params):
    """A woven basket, origin at the centre of its base."""
    g = draw.Group()
    top = -height
    half, half_top = width / 2, width * taper / 2
    _add(g, ctx, polyline_path([(-half, top), (half, top), (half_top, 0), (-half_top, 0)]),
         params, fill)
    for i in range(1, weave + 1):
        t = i / (weave + 1)
        y = top * (1 - t)
        w = half_top + (half - half_top) * (1 - t)
        _add(g, ctx, polyline_path([(-w, y), (w, y)], close=False),
             {**params, "fill": None, "stroke_width": ctx.defaults["stroke_width"] * 0.55})
    if handle:
        _add(g, ctx, polyline_path([(-half * 0.6, top), (0, top - height * 0.75),
                                    (half * 0.6, top)], close=False),
             {**params, "fill": None, "stroke_width": ctx.defaults["stroke_width"]})
    return g


@element("balloon")
def balloon(ctx, envelope_width=520, envelope_height=560, basket_width=220,
           basket_height=140, gap=90, fill="#D8524A", stripe_fill="#FFF4E4",
           panels=6, **params):
    """A hot-air balloon with its basket, origin at the centre of the basket base."""
    g = draw.Group()
    by = -basket_height
    g.append(basket(ctx, width=basket_width, height=basket_height, fill=params.get(
        "basket_fill", "#B0793F"), **{k: v for k, v in params.items() if k not in
        ("fill",)}))

    env_bottom = by - gap
    neck = envelope_width * 0.16
    ew, eh = envelope_width / 2, envelope_height
    outline = catmull_closed([
        (-neck, env_bottom), (-ew, env_bottom - eh * 0.32), (-ew * 0.62, env_bottom - eh * 0.85),
        (0, env_bottom - eh), (ew * 0.62, env_bottom - eh * 0.85),
        (ew, env_bottom - eh * 0.32), (neck, env_bottom)], tension=0.85)
    _add(g, ctx, outline, params, fill)
    for i in range(panels):
        if i % 2:
            continue
        t0, t1 = i / panels, (i + 1) / panels
        x0 = -ew + 2 * ew * t0
        x1 = -ew + 2 * ew * t1
        _add(g, ctx, catmull_closed([
            (x0 * 0.3, env_bottom), (x0, env_bottom - eh * 0.4), (x0 * 0.5, env_bottom - eh * 0.92),
            (x1 * 0.5, env_bottom - eh * 0.92), (x1, env_bottom - eh * 0.4), (x1 * 0.3, env_bottom)],
            tension=0.85), params, stripe_fill)
    for side in (-1, 1):
        _add(g, ctx, polyline_path([(side * basket_width * 0.4, by),
                                    (side * neck * 0.9, env_bottom)], close=False),
             {**params, "fill": None, "stroke_width": ctx.defaults["stroke_width"] * 0.6})
    return g


@element("kite")
def kite(ctx, width=180, height=220, fill="#D64545", tail_fill="#F7C948",
        bows=4, string_to=None, **params):
    """A diamond kite, optionally trailing a string down to ``string_to``."""
    g = draw.Group()
    half_w, half_h = width / 2, height / 2
    _add(g, ctx, polyline_path([(0, -half_h), (half_w, 0), (0, half_h), (-half_w, 0)]),
         params, fill)
    _add(g, ctx, polyline_path([(0, -half_h), (0, half_h)], close=False),
         {**params, "fill": None, "stroke_width": ctx.defaults["stroke_width"] * 0.6})
    _add(g, ctx, polyline_path([(-half_w, 0), (half_w, 0)], close=False),
         {**params, "fill": None, "stroke_width": ctx.defaults["stroke_width"] * 0.6})
    tx, ty = 0, half_h
    for i in range(bows):
        tx += width * 0.16
        ty += height * 0.12
        side = -1 if i % 2 else 1
        _add(g, ctx, polyline_path([(tx - width * 0.1, ty), (tx, ty + height * 0.1),
                                    (tx + width * 0.1 * side, ty)]), params, tail_fill)
    if string_to is not None:
        spine = bezier_points((0, half_h), (string_to[0] * 0.3, half_h + (string_to[1] - half_h) * 0.4),
                              (string_to[0] * 0.7, half_h + (string_to[1] - half_h) * 0.7),
                              string_to, steps=16)
        _add(g, ctx, polyline_path(spine, close=False),
             {**params, "fill": None, "stroke_width": ctx.defaults["stroke_width"] * 0.5})
    return g
