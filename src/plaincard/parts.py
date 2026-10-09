"""The parts a diagram is made of.

Each part draws itself in its own coordinates, from (0, 0), and returns its width, height and SVG.
A part is quiet (a dim outline) unless the spec marks it `accent: true`, which makes it the point of
the picture. Parts never pick colours of their own: they draw with the inks they are given, so the
style lives in one place.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from plaincard import style


@dataclass
class Ink:
    accent: str
    line: str = style.LINE
    detail: str = style.DETAIL

    def outline(self, on: bool) -> tuple[str, int]:
        return (self.accent, style.STROKE_ACCENT) if on else (self.line, style.STROKE)


@dataclass
class Drawn:
    w: float
    h: float
    svg: str


def _rect(x, y, w, h, color, width, rx=8, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" stroke="{color}" '
            f'stroke-width="{width}"{d}/>')


def _line(x1, y1, x2, y2, color, width, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{width}"{d}/>')


def _path(d, color, width, dash=""):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" stroke="{color}" stroke-width="{width}"{extra}/>'


def _text(x, y, s, color, size=18, anchor="middle", font=style.MONO):
    s = (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{color}" '
            f'stroke="none" text-anchor="{anchor}">{s}</text>')


# ------------------------------------------------------------------------------------- parts

def pane(ink: Ink, accent: bool = False, lines: int = 3, w: int = 140, h: int = 110) -> Drawn:
    """A window or chat: a title bar and a few lines of text."""
    c, sw = ink.outline(accent)
    out = _rect(0, 0, w, h, c, sw) + _line(0, 22, w, 22, c, style.STROKE_THIN)
    for i in range(lines):
        ww = (w - 40 - (i * 23) % 60) * 0.6
        last = accent and i == lines - 1
        out += _line(18, 46 + i * 20, 18 + ww, 46 + i * 20, ink.accent if last else ink.detail, 5)
    return Drawn(w, h, out)


def panes(ink: Ink, accent: bool = False, rows: int = 3, cols: int = 3,
          highlight: list[int] | None = None) -> Drawn:
    """Many windows or chats in a grid; `highlight: [row, col]` marks the one that matters."""
    hl = tuple(highlight) if highlight else None
    out = ""
    for r in range(rows):
        for c in range(cols):
            p = pane(ink, accent=(hl == (r, c)) or (accent and hl is None))
            out += f'<g transform="translate({c * 160} {r * 130})">{p.svg}</g>'
    return Drawn(cols * 160 - 20, rows * 130 - 20, out)


def terminal(ink: Ink, accent: bool = False, w: int = 220, h: int = 140) -> Drawn:
    """A terminal: a prompt and a cursor."""
    c, sw = ink.outline(accent)
    out = _rect(0, 0, w, h, c, sw) + _line(0, 24, w, 24, c, style.STROKE_THIN)
    out += _path("M22 56 l14 12 l-14 12", ink.accent if accent else ink.detail, 4)
    out += _line(48, 82, 78, 82, ink.accent if accent else ink.detail, 4)
    out += _line(22, 108, 150, 108, ink.detail, 5)
    return Drawn(w, h, out)


def phone(ink: Ink, accent: bool = False, rows: int = 4, model: str = "plain",
          shows: str = "") -> Drawn:
    """A phone with rows on its screen. `model: ios` gives a speaker slit, `android` a camera dot;
    `shows: lock | check` draws that instead of rows."""
    w, h = 130, 250
    out = _rect(0, 0, w, h, ink.line, style.STROKE, rx=22 if model != "android" else 12)
    if model == "android":
        out += f'<circle cx="{w / 2}" cy="16" r="4" stroke="{ink.line}" stroke-width="2"/>'
    else:
        out += _line(45, 18, 85, 18, ink.line, style.STROKE)
    if shows:
        inner = SCREEN.get(shows)
        if inner is None:
            raise ValueError(f"phone shows {shows!r}: use one of {', '.join(SCREEN)}")
        d = inner(ink, True)
        return Drawn(w, h, out + f'<g transform="translate({w / 2 - d.w / 2} {h / 2 - d.h / 2})">{d.svg}</g>')
    for i in range(rows):
        out += _rect(25, 50 + i * 45, 80, 26, ink.accent if accent else ink.detail,
                     style.STROKE_THIN, rx=5)
    return Drawn(w, h, out)


def laptop(ink: Ink, accent: bool = False, shows: str = "") -> Drawn:
    """A laptop. `shows: lock | check | lines` draws that on its screen."""
    out = _rect(30, 0, 300, 200, ink.line, style.STROKE, rx=12) + _line(0, 230, 360, 230, ink.line,
                                                                         style.STROKE)
    if shows:
        inner = SCREEN.get(shows)
        if inner is None:
            raise ValueError(f"laptop shows {shows!r}: use one of {', '.join(SCREEN)}")
        d = inner(ink, True if accent or shows else False)
        out += f'<g transform="translate({180 - d.w / 2} {100 - d.h / 2})">{d.svg}</g>'
    return Drawn(360, 232, out)


def tv(ink: Ink, accent: bool = False, tiles: int = 3, crossed: int | None = None,
       highlight: int | None = None) -> Drawn:
    """A television with app tiles; `crossed` strikes one out, `highlight` marks the one chosen."""
    w = 40 + tiles * 114
    out = _rect(0, 0, w, 230, ink.line, style.STROKE, rx=10) + _line(w / 2 - 50, 250, w / 2 + 50, 250,
                                                                      ink.line, style.STROKE)
    for i in range(tiles):
        x = 32 + i * 114
        on = highlight == i
        out += _rect(x, 40, 90, 60, ink.accent if on else ink.detail,
                     style.STROKE if on else style.STROKE_THIN, rx=6)
        if crossed == i:
            out += _path(f"M{x + 14} 52 l62 36 M{x + 76} 52 l-62 36", ink.detail, style.STROKE_THIN)
    return Drawn(w, 252, out)


def remote(ink: Ink, accent: bool = True) -> Drawn:
    """A remote control with one button lit."""
    out = _rect(0, 0, 56, 170, ink.line, style.STROKE, rx=20)
    out += f'<circle cx="28" cy="40" r="10" stroke="{ink.accent if accent else ink.detail}" stroke-width="3"/>'
    out += _line(18, 80, 38, 80, ink.detail, 4) + _line(18, 100, 38, 100, ink.detail, 4)
    return Drawn(56, 170, out)


def cloud(ink: Ink, accent: bool = False) -> Drawn:
    """A hosted service: Vercel, a serverless function, someone else's computer."""
    c, sw = ink.outline(accent)
    return Drawn(176, 104, _path("M20 94 a30 30 0 0 1 10 -50 a40 40 0 0 1 60 -40 a50 50 0 0 1 "
                                 "90 20 a35 35 0 0 1 -6 70 z", c, sw))


def db(ink: Ink, accent: bool = False) -> Drawn:
    """A database."""
    c, sw = ink.outline(accent)
    out = f'<ellipse cx="52" cy="16" rx="52" ry="16" stroke="{c}" stroke-width="{sw}"/>'
    out += _path("M0 16 v120 a52 16 0 0 0 104 0 v-120", c, sw)
    out += _path("M0 76 a52 16 0 0 0 104 0", c, style.STROKE_THIN)
    return Drawn(104, 154, out)


def gate(ink: Ink, accent: bool = True) -> Drawn:
    """A narrow door every request passes through: a proxy, a gateway, a tunnel's end."""
    c, sw = ink.outline(accent)
    return Drawn(24, 120, _rect(0, 0, 24, 120, c, sw, rx=4))


def server(ink: Ink, accent: bool = False) -> Drawn:
    """A machine: three stacked units with lights."""
    c, sw = ink.outline(accent)
    out = ""
    for i in range(3):
        out += _rect(0, i * 52, 140, 44, c, sw, rx=6)
        out += f'<circle cx="24" cy="{i * 52 + 22}" r="4" stroke="{ink.accent if accent else ink.detail}" stroke-width="3"/>'
        out += _line(44, i * 52 + 22, 110, i * 52 + 22, ink.detail, 4)
    return Drawn(140, 148, out)


def doc(ink: Ink, accent: bool = False) -> Drawn:
    """A document or file."""
    c, sw = ink.outline(accent)
    out = _path("M0 0 h76 l34 34 v106 h-110 z", c, sw) + _path("M76 0 v34 h34", c, style.STROKE_THIN)
    for i in range(4):
        out += _line(18, 56 + i * 18, 90 - (i % 2) * 22, 56 + i * 18,
                     ink.accent if accent and i == 3 else ink.detail, 4)
    return Drawn(110, 140, out)


def folder(ink: Ink, accent: bool = False) -> Drawn:
    """A folder or project."""
    c, sw = ink.outline(accent)
    return Drawn(140, 104, _path("M0 10 a8 8 0 0 1 8 -8 h40 l14 14 h70 a8 8 0 0 1 8 8 v72 a8 8 0 0 1 "
                                 "-8 8 h-124 a8 8 0 0 1 -8 -8 z", c, sw))


def lock(ink: Ink, accent: bool = True) -> Drawn:
    """Something locked or secret."""
    c, sw = ink.outline(accent)
    return Drawn(60, 68, _rect(0, 18, 60, 50, c, sw, rx=6) + _path("M12 18 v-14 a18 18 0 0 1 36 0 v14", c, sw))


def check(ink: Ink, accent: bool = True) -> Drawn:
    """Done, verified, approved."""
    c, _ = ink.outline(accent)
    return Drawn(60, 46, _path("M4 24 l16 16 l36 -36", c, 4))


def user(ink: Ink, accent: bool = False) -> Drawn:
    """A person."""
    c, sw = ink.outline(accent)
    return Drawn(90, 100, f'<circle cx="45" cy="28" r="24" stroke="{c}" stroke-width="{sw}"/>'
                          + _path("M4 100 a41 41 0 0 1 82 0", c, sw))


def globe(ink: Ink, accent: bool = False) -> Drawn:
    """The internet, the public web."""
    c, sw = ink.outline(accent)
    out = f'<circle cx="55" cy="55" r="52" stroke="{c}" stroke-width="{sw}"/>'
    out += f'<ellipse cx="55" cy="55" rx="22" ry="52" stroke="{c}" stroke-width="{style.STROKE_THIN}"/>'
    out += _line(3, 55, 107, 55, c, style.STROKE_THIN)
    return Drawn(110, 110, out)


def box(ink: Ink, accent: bool = False, text: str = "") -> Drawn:
    """A labelled box, for anything the other parts do not cover; the text sits inside it."""
    c, sw = ink.outline(accent)
    w = max(120, int(len(text) * 12 + 40))
    out = _rect(0, 0, w, 64, c, sw)
    if text:
        out += _text(w / 2, 39, text, ink.accent if accent else style.MUTED, size=20)
    return Drawn(w, 64, out)


def chart(ink: Ink, accent: bool = True) -> Drawn:
    """A line chart on two axes: a model, a trend, a target over time."""
    c = ink.accent if accent else ink.line
    out = _path("M8 6 v118 h176", ink.line, style.STROKE)
    out += _path("M20 100 C 50 96, 60 40, 92 52 S 140 84, 176 26", c, style.STROKE_ACCENT)
    out += f'<circle cx="176" cy="26" r="5" stroke="{c}" stroke-width="3"/>'
    return Drawn(190, 128, out)


def heart(ink: Ink, accent: bool = False) -> Drawn:
    """A heart: heart rate, health."""
    c, sw = ink.outline(accent)
    return Drawn(92, 82, _path("M46 78 C 10 54, 0 36, 4 22 a22 22 0 0 1 42 -6 a22 22 0 0 1 42 6 "
                               "C 92 36, 82 54, 46 78 z", c, sw))


def note(ink: Ink, accent: bool = False) -> Drawn:
    """A music note: a song, a playlist, a tempo."""
    c, sw = ink.outline(accent)
    out = f'<ellipse cx="22" cy="92" rx="20" ry="14" stroke="{c}" stroke-width="{sw}"/>'
    out += f'<ellipse cx="82" cy="80" rx="20" ry="14" stroke="{c}" stroke-width="{sw}"/>'
    out += _path("M42 92 V 14 L 102 4 V 80", c, sw) + _path("M42 30 L 102 20", c, sw)
    return Drawn(106, 108, out)


def watch(ink: Ink, accent: bool = False) -> Drawn:
    """A smartwatch: a fitness device, a wearable's data."""
    c, sw = ink.outline(accent)
    out = _rect(16, 0, 60, 26, ink.line, style.STROKE_THIN, rx=6)
    out += _rect(16, 114, 60, 26, ink.line, style.STROKE_THIN, rx=6)
    out += _rect(0, 22, 92, 96, c, sw, rx=24)
    out += _path("M22 72 h12 l8 -16 l10 30 l8 -14 h12", ink.accent if accent else ink.detail, 3)
    return Drawn(92, 140, out)


def cube(ink: Ink, accent: bool = False) -> Drawn:
    """A 3D object: a model, a printed part."""
    c, sw = ink.outline(accent)
    out = _path("M60 4 L 112 32 V 92 L 60 120 L 8 92 V 32 Z", c, sw)
    out += _path("M8 32 L 60 60 L 112 32 M60 60 V 120", c, style.STROKE_THIN)
    return Drawn(120, 124, out)


#: what a laptop screen can show
SCREEN: dict[str, Callable[[Ink, bool], Drawn]] = {
    "lock": lambda ink, a: lock(ink, True),
    "check": lambda ink, a: check(ink, True),
    "lines": lambda ink, a: pane(ink, False, 3, 160, 110),
}

PARTS: dict[str, Callable[..., Drawn]] = {
    "pane": pane, "panes": panes, "terminal": terminal, "phone": phone, "laptop": laptop,
    "tv": tv, "remote": remote, "cloud": cloud, "db": db, "gate": gate, "server": server,
    "doc": doc, "folder": folder, "lock": lock, "check": check, "user": user, "globe": globe,
    "box": box, "chart": chart, "heart": heart, "note": note, "watch": watch, "cube": cube,
}

#: what joins two parts in a row
EDGES = ("arrow", "dots", "line")


def describe() -> list[tuple[str, str]]:
    """(name, first line of its docstring) for every part, for the CLI and the skill."""
    return [(n, (f.__doc__ or "").strip().splitlines()[0]) for n, f in PARTS.items()]
