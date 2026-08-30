"""Scene loading and rendering.

A scene is a YAML file: a canvas, a palette, and an ordered list of layers.
Each layer names an element, where to put it, and the parameters that element
takes. This module resolves colours, applies transforms and hands each layer to
its element function; the elements themselves live in ``elements.py``.
"""

from __future__ import annotations

import math
from pathlib import Path

import drawsvg as draw
import yaml

from . import elements as _elements  # noqa: F401  (registers every element)
from . import props as _props        # noqa: F401  (registers every element)
from .registry import ALIASES, REGISTRY

MODES = ("color", "line", "both")

# Anything drawn as ink stays black in both modes: eyes, noses, pupils.
INK = {"fill": "#000000", "stroke": "none", "stroke_width": 0}


class SceneError(Exception):
    """A problem in the scene file, phrased for whoever wrote the YAML."""


class Context:
    """Per-render state: the mode, the defaults and the resolved palette."""

    def __init__(self, mode: str, defaults: dict, palette: dict):
        self.mode = mode
        self.defaults = {"stroke": "#111111", "stroke_width": 3.0,
                         "stroke_linejoin": "round", "stroke_linecap": "round",
                         **(defaults or {})}
        self._palette = palette or {}
        self._gradients: dict[str, draw.LinearGradient] = {}

    # ---- colours ----------------------------------------------------------
    def color(self, value):
        """Resolve a colour: a literal, ``"$name"`` from the palette, or none."""
        if value is None:
            return "none"
        if isinstance(value, str) and value.startswith("$"):
            key = value[1:]
            if key not in self._palette:
                raise SceneError(
                    f"unknown palette colour '{value}'. "
                    f"Defined: {', '.join(sorted(self._palette)) or '(none)'}")
            value = self._palette[key]
            if isinstance(value, dict) and "gradient" in value:
                return self._gradient(key, value)
        return value

    def _gradient(self, key: str, spec: dict):
        if key in self._gradients:
            return self._gradients[key]
        angle = math.radians(spec.get("angle", 90))
        x2, y2 = (math.cos(angle) + 1) / 2, (math.sin(angle) + 1) / 2
        grad = draw.LinearGradient(1 - x2, 1 - y2, x2, y2,
                                   gradientUnits="objectBoundingBox")
        for offset, colour in spec["gradient"]:
            grad.add_stop(offset, colour)
        self._gradients[key] = grad
        return grad

    # ---- style ------------------------------------------------------------
    def style(self, params: dict, fill="none", ink: bool = False) -> dict:
        """Build the SVG attributes for one shape, honouring the render mode."""
        if ink:
            return dict(INK)
        resolved = self.color(params.get("fill", fill))
        if self.mode == "line" and resolved != "none":
            resolved = "#ffffff"
        style = {
            "fill": resolved,
            "stroke": self.color(params.get("stroke", self.defaults["stroke"])),
            "stroke_width": params.get("stroke_width",
                                       self.defaults["stroke_width"]),
            "stroke_linejoin": self.defaults["stroke_linejoin"],
            "stroke_linecap": self.defaults["stroke_linecap"],
        }
        dash = params.get("dash")
        if dash:
            style["stroke_dasharray"] = ",".join(str(d) for d in dash)
        return style

    # ---- layers -----------------------------------------------------------
    def build(self, layer: dict) -> draw.Group:
        """Turn one layer dict into a positioned group."""
        if not isinstance(layer, dict):
            raise SceneError(f"each layer must be a mapping, got {type(layer).__name__}")
        name = layer.get("element") or layer.get("عنصر")
        if not name:
            raise SceneError(f"layer is missing the 'element' key: {layer!r}")
        key = ALIASES.get(name, name)
        if key not in REGISTRY:
            raise SceneError(
                f"unknown element '{name}'. Available: {', '.join(sorted(REGISTRY))}")

        params = layer.get("params") or layer.get("خصائص") or {}
        if not isinstance(params, dict):
            raise SceneError(f"'params' of element '{name}' must be a mapping")
        try:
            group = REGISTRY[key](self, **params)
        except SceneError:
            raise
        except TypeError as exc:
            raise SceneError(f"bad parameters for element '{name}': {exc}") from exc

        group.args["transform"] = _transform(layer)
        return group


def _transform(layer: dict) -> str:
    """``at`` / ``scale`` / ``rotate`` / ``flip_x`` as one SVG transform."""
    x, y = layer.get("at", layer.get("موضع", (0, 0)))
    scale = layer.get("scale", layer.get("حجم", 1))
    rotate = layer.get("rotate", layer.get("دوران", 0))
    parts = [f"translate({x},{y})"]
    if rotate:
        parts.append(f"rotate({rotate})")
    if layer.get("flip_x"):
        parts.append(f"scale({-scale},{scale})")
    elif scale != 1:
        parts.append(f"scale({scale})")
    return " ".join(parts)


def load(path: str | Path) -> dict:
    """Read a scene file and check the parts the renderer relies on."""
    path = Path(path)
    try:
        spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SceneError(f"{path}: invalid YAML — {exc}") from exc
    if not isinstance(spec, dict):
        raise SceneError(f"{path}: a scene must be a mapping at the top level")
    mode = spec.get("mode", "color")
    if mode not in MODES:
        raise SceneError(f"{path}: mode must be one of {', '.join(MODES)}, got '{mode}'")
    if not isinstance(spec.get("layers"), list):
        raise SceneError(f"{path}: 'layers' must be a list of layers")
    if "panels" in spec and not isinstance(spec["panels"], list):
        raise SceneError(f"{path}: 'panels' must be a list of panel specs")
    return spec


def _draw_layers(ctx: Context, layers: list[dict]) -> draw.Group:
    group = draw.Group()
    for index, layer in enumerate(layers, start=1):
        try:
            group.append(ctx.build(layer))
        except SceneError as exc:
            raise SceneError(f"layer {index}: {exc}") from None
    return group


def _background_and_border(spec: dict, ctx: Context, width, height) -> list:
    canvas = spec.get("canvas") or {}
    items = []
    background = canvas.get("background", "#ffffff")
    if background and background != "none":
        items.append(draw.Rectangle(0, 0, width, height,
                                    fill=ctx.color(background), stroke="none"))
    border = canvas.get("border")
    if border:
        margin = border.get("margin", 24)
        items.append(draw.Rectangle(
            margin, margin, width - 2 * margin, height - 2 * margin,
            fill="none", stroke=border.get("color", "#111111"),
            stroke_width=border.get("stroke_width", 4)))
    return items


def render(spec: dict, mode: str) -> draw.Drawing:
    """Render one scene in one mode (mode is 'color' or 'line')."""
    canvas = spec.get("canvas") or {}
    width = canvas.get("width", 1200)
    height = canvas.get("height", 1200)
    ctx = Context(mode, spec.get("defaults"), spec.get("palette"))

    drawing = draw.Drawing(width, height, origin=(0, 0))
    for item in _background_and_border(spec, ctx, width, height):
        drawing.append(item)
    drawing.append(_draw_layers(ctx, spec["layers"]))
    return drawing


def render_panels(spec: dict) -> draw.Drawing:
    """Render a scene's ``layers`` twice into one image, per ``panels`` entry.

    Each panel gets its own render mode (typically a small coloured panel and
    a large line-art panel), positioned and scaled independently, so a single
    scene definition produces the two-panel coloring-page layout in one file.
    """
    canvas = spec.get("canvas") or {}
    width = canvas.get("width", 1200)
    height = canvas.get("height", 1600)
    defaults, palette = spec.get("defaults"), spec.get("palette")

    drawing = draw.Drawing(width, height, origin=(0, 0))
    bg_ctx = Context("color", defaults, palette)
    for item in _background_and_border(spec, bg_ctx, width, height):
        drawing.append(item)

    for index, panel in enumerate(spec["panels"], start=1):
        panel_mode = panel.get("mode", "color")
        if panel_mode not in ("color", "line"):
            raise SceneError(f"panel {index}: mode must be 'color' or 'line', "
                             f"got '{panel_mode}'")
        ctx = Context(panel_mode, defaults, palette)
        group = _draw_layers(ctx, spec["layers"])
        x, y = panel.get("at", (width / 2, height / 2))
        scale = panel.get("scale", 1)
        group.args["transform"] = f"translate({x},{y}) scale({scale})"
        drawing.append(group)
    return drawing


def modes_for(spec: dict) -> list[str]:
    """The render modes a scene asks for. 'panels' scenes render as one file."""
    if "panels" in spec:
        return ["panels"]
    mode = spec.get("mode", "color")
    return ["color", "line"] if mode == "both" else [mode]
