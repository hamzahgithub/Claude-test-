#!/usr/bin/env python3
"""Render scene files to SVG and PNG.

    python render.py --all              # every scene in scenes/
    python render.py scenes/x.yaml      # just one
    python render.py --all --out build  # somewhere else
"""

import argparse
import sys
from pathlib import Path

from drawlib.scene import SceneError, load, modes_for, render, render_panels

ROOT = Path(__file__).parent


def render_scene(path: Path, out_dir: Path, pixel_scale: float) -> list[Path]:
    spec = load(path)
    modes = modes_for(spec)
    written = []
    for mode in modes:
        # A single-mode scene keeps its plain name; 'both' gets a suffix per
        # mode; a 'panels' scene is one combined file under the plain name.
        stem = path.stem if len(modes) == 1 else f"{path.stem}_{mode}"
        drawing = render_panels(spec) if mode == "panels" else render(spec, mode)
        drawing.set_pixel_scale(pixel_scale)
        svg, png = out_dir / f"{stem}.svg", out_dir / f"{stem}.png"
        drawing.save_svg(str(svg))
        drawing.save_png(str(png))
        written += [svg, png]
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenes", nargs="*", type=Path, help="scene files to render")
    parser.add_argument("--all", action="store_true", help="render every scene in scenes/")
    parser.add_argument("--out", type=Path, default=ROOT / "renders", help="output directory")
    parser.add_argument("--scale", type=float, default=1.5, help="PNG pixel scale")
    args = parser.parse_args()

    targets = sorted((ROOT / "scenes").glob("*.yaml")) if args.all else args.scenes
    if not targets:
        parser.error("give a scene file, or --all to render scenes/")

    args.out.mkdir(parents=True, exist_ok=True)
    failed = False
    for path in targets:
        try:
            for written in render_scene(path, args.out, args.scale):
                print(f"  {written.relative_to(ROOT) if ROOT in written.parents else written}")
        except (SceneError, ValueError, KeyError) as exc:
            print(f"{path}: {exc}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
