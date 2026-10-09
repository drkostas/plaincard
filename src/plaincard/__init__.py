"""plaincard: plain, consistent images for projects, from a few lines of spec.

    from plaincard import render_file
    render_file("examples/sqlgate.yaml", "images")   # images/sqlgate.svg and images/sqlgate.png
"""
from __future__ import annotations

from pathlib import Path

from plaincard import export, render, spec

__version__ = "0.1.0"


def render_spec(data: dict, out_dir: str | Path, stem: str, png: bool = True) -> list[Path]:
    """Render a spec given as a mapping. Returns the files written."""
    s = spec.parse(data)
    return _write(s, Path(out_dir), stem, png)


def render_file(path: str | Path, out_dir: str | Path | None = None, png: bool = True) -> list[Path]:
    """Render a .yaml or .json spec. Output goes next to the spec unless `out_dir` is given."""
    p = Path(path)
    s = spec.load(p)
    return _write(s, Path(out_dir) if out_dir else p.parent, p.stem, png)


def _write(s: spec.Spec, out_dir: Path, stem: str, png: bool) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    svg_path = out_dir / f"{stem}.svg"
    svg_path.write_text(render.svg(s))
    written = [svg_path]
    if png:
        written.append(export.png(svg_path, out_dir / f"{stem}.png"))
    return written
