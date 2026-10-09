"""The one style every plaincard image shares: colours, fonts, line weights and canvas sizes.

Restyling every image is changing this file and rendering the specs again.
"""
from __future__ import annotations

BACKGROUND = "#0f1419"
TEXT = "#e6edf3"
MUTED = "#8b98a5"
FAINT = "#56636f"
LINE = "#2b3743"      # the outline of a part that is not the point of the picture
DETAIL = "#3a4754"    # lines inside a part (text lines in a pane, rows on a phone)

#: named accents; a spec may also give any #rrggbb
ACCENTS = {
    "clay": "#d97757",
    "blue": "#7aa2f7",
    "amber": "#e0af68",
    "green": "#9ece6a",
    "violet": "#bb9af7",
    "teal": "#73daca",
    "rose": "#f7768e",
    "sky": "#7dcfff",
}

MONO = "'SF Mono','Menlo','JetBrains Mono','DejaVu Sans Mono',monospace"
SANS = "-apple-system,'Inter','Helvetica Neue','Segoe UI',Arial,sans-serif"

STROKE = 3          # an outline
STROKE_THIN = 2     # inner structure
STROKE_ACCENT = 3

#: canvas size of each kind, in CSS pixels; the PNG is rendered at twice this
KINDS = {
    "card": (1280, 640),      # GitHub social preview, project pages, posts (2:1)
    "banner": (1600, 400),    # a wide header at the top of a README (4:1)
    "diagram": (1200, 480),   # a figure inside a README, a doc or a post
    "icon": (512, 512),       # a square mark
}


def accent(value: str | None) -> str:
    """A named accent or a #rrggbb colour; the first accent when none is given."""
    if not value:
        return ACCENTS["clay"]
    if value.startswith("#") and len(value) in (4, 7):
        return value
    if value in ACCENTS:
        return ACCENTS[value]
    raise ValueError(f"unknown accent {value!r}: use one of {', '.join(ACCENTS)} or #rrggbb")
