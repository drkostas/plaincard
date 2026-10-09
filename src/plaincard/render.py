"""Turn a spec into an SVG.

The layout keeps text and diagram apart by construction: the text block owns the top of the canvas,
the diagram is scaled to fit the region left below it, and text that would not fit its width is
wrapped or refused, never drawn over the picture.
"""
from __future__ import annotations

from plaincard import parts as P
from plaincard import style
from plaincard.spec import Edge, Part, Spec, SpecError

#: rough advance width of one character, as a fraction of the font size
SANS_EM = 0.47
MONO_EM = 0.61
GAP = 18          # between a part and an edge
LABEL_SPACE = 34  # under a row whose parts have labels


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(text: str, size: float, width: float) -> list[str]:
    """Greedy word wrap by estimated width."""
    per_line = max(10, int(width / (size * SANS_EM)))
    lines, cur = [], ""
    for word in text.split():
        cand = f"{cur} {word}".strip()
        if len(cand) <= per_line or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _edge_svg(e: Edge, x: float, y: float, ink: P.Ink) -> str:
    color = ink.line if e.kind == "line" else ink.accent
    dash = "2 10" if e.kind == "dots" else ""
    out = P._line(x, y, x + e.length, y, color, style.STROKE, dash)
    if e.kind == "arrow":
        out += P._path(f"M{x + e.length - 12} {y - 10} L {x + e.length} {y} L {x + e.length - 12} {y + 10}",
                       color, style.STROKE)
    if e.label:
        out += P._text(x + e.length / 2, y - 16, e.label, color, size=18)
    return out


def row(items: list, ink: P.Ink) -> tuple[float, float, str]:
    """Lay the diagram's items out left to right. Returns width, height and SVG."""
    drawn = []
    for it in items:
        if isinstance(it, Part):
            fn = P.PARTS[it.name]
            try:
                kw = dict(it.options)
                if it.accent is not None:
                    kw["accent"] = it.accent
                d = fn(ink, **kw)
            except (TypeError, ValueError) as e:
                raise SpecError(f"{it.name}: {e}") from None
            drawn.append((it, d))
        else:
            drawn.append((it, None))
    labelled = any(isinstance(it, Part) and it.label for it, _ in drawn)
    body_h = max([d.h for _, d in drawn if d] or [0])
    h = body_h + (LABEL_SPACE if labelled else 0)
    mid = body_h / 2
    x, out = 0.0, ""
    for i, (it, d) in enumerate(drawn):
        if d is not None:
            y = (body_h - d.h) / 2
            out += f'<g transform="translate({x:.1f} {y:.1f})">{d.svg}</g>'
            if it.label:
                out += P._text(x + d.w / 2, body_h + 28, it.label,
                               ink.accent if it.accent else style.MUTED, size=18)
            x += d.w
        else:
            x += GAP
            out += _edge_svg(it, x, mid, ink)
            x += it.length
        nxt = drawn[i + 1] if i + 1 < len(drawn) else None
        if d is not None and nxt is not None and nxt[1] is not None:
            x += 40   # two parts side by side, no edge between them
        elif d is not None and nxt is not None:
            x += GAP
    return x, h, out


def _fit(w: float, h: float, box: tuple[float, float, float, float], max_scale: float) -> str:
    bx, by, bw, bh = box
    if w <= 0 or h <= 0:
        return ""
    s = min(bw / w, bh / h, max_scale)
    return f"translate({bx + (bw - w * s) / 2:.1f} {by + (bh - h * s) / 2:.1f}) scale({s:.3f})"


def _title_size(name: str, start: int, smallest: int, width: float) -> int:
    size = start
    while size > smallest and len(name) * size * MONO_EM > width:
        size -= 2
    if len(name) * size * MONO_EM > width:
        raise SpecError(f"the name {name!r} is too long for this kind; shorten it")
    return size


def svg(spec: Spec) -> str:
    W, H = style.KINDS[spec.kind]
    ink = P.Ink(accent=spec.accent)
    w, h, diagram = row(spec.diagram, ink) if spec.diagram else (0, 0, "")
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           f'<rect width="{W}" height="{H}" fill="{style.BACKGROUND}"/>']

    def text(x, y, s, size, color, font, weight=""):
        wt = f' font-weight="{weight}"' if weight else ""
        out.append(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}"{wt} '
                   f'fill="{color}">{_esc(s)}</text>')

    if spec.kind == "card":
        text_w = W - 144
        size = _title_size(spec.name, 64, 44, text_w)
        out.append(f'<rect x="72" y="72" width="56" height="6" rx="3" fill="{spec.accent}"/>')
        text(72, 160, spec.name, size, style.TEXT, style.MONO, "600")
        lines = wrap(spec.line, 27, 760) if spec.line else []
        if len(lines) > 3:
            raise SpecError("the line is too long for a card: keep it to about two lines")
        for i, ln in enumerate(lines):
            text(72, 214 + i * 36, ln, 27, style.MUTED, style.SANS)
        top = 214 + max(len(lines) - 1, 0) * 36 + 50
        bottom = 560 if spec.footer else 600
        if spec.footer:
            text(72, 604, spec.footer, 20, style.FAINT, style.MONO)
        box = (120, top, W - 240, bottom - top)
        scale_cap = 1.3     # a small drawing grows to fill its space, a big one shrinks
    elif spec.kind == "banner":
        size = _title_size(spec.name, 56, 40, 760)
        out.append(f'<rect x="64" y="96" width="48" height="6" rx="3" fill="{spec.accent}"/>')
        text(64, 182, spec.name, size, style.TEXT, style.MONO, "600")
        lines = wrap(spec.line, 24, 760) if spec.line else []
        if len(lines) > 3:
            raise SpecError("the line is too long for a banner: keep it to about two lines")
        for i, ln in enumerate(lines):
            text(64, 232 + i * 32, ln, 24, style.MUTED, style.SANS)
        box = (900, 50, 636, 300)
        scale_cap = 1.3
    elif spec.kind == "diagram":
        bottom = H - 40
        if spec.caption:
            text(W / 2 - len(spec.caption) * 18 * MONO_EM / 2, H - 28, spec.caption, 18,
                 style.MUTED, style.MONO)
            bottom = H - 70
        box = (40, 40, W - 80, bottom - 40)
        scale_cap = 1.25
    else:  # icon
        box = (96, 96, W - 192, H - 192)
        scale_cap = 1.6
    if diagram:
        out.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round" '
                   f'transform="{_fit(w, h, box, scale_cap)}">{diagram}</g>')
    out.append("</svg>")
    return "\n".join(out)
