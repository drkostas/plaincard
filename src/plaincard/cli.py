"""plaincard command line.

    plaincard render SPEC [SPEC ...] [-o DIR] [--no-png]
    plaincard parts            the parts and edges a diagram can use
    plaincard example [KIND]   a starting spec to copy
"""
from __future__ import annotations

import argparse
import sys

from plaincard import __version__, parts, render_file, style
from plaincard.spec import SpecError

EXAMPLES = {
    "card": """kind: card
name: sqlgate
line: Serve a database you host yourself to serverless apps over HTTPS, in the shape the Neon driver speaks.
accent: green
footer: github.com/drkostas/sqlgate
diagram:
  - cloud
  - arrow: https
  - gate: {accent: true}
  - line
  - db
""",
    "banner": """kind: banner
name: claude-ops
line: Tools for running many Claude Code chats on one machine.
accent: clay
diagram:
  - panes: {rows: 2, cols: 3, highlight: [0, 1]}
""",
    "diagram": """kind: diagram
caption: A message reaches a chat that is already running
accent: clay
diagram:
  - user: {label: you}
  - arrow: inject
  - terminal: {accent: true, label: chat}
""",
    "icon": """kind: icon
accent: violet
diagram:
  - phone: {accent: true, model: android}
""",
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plaincard", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=f"plaincard {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="render specs to SVG and PNG")
    r.add_argument("specs", nargs="+")
    r.add_argument("-o", "--out", help="output folder (default: next to each spec)")
    r.add_argument("--no-png", action="store_true", help="write only the SVG")
    sub.add_parser("parts", help="list the parts, edges, accents and kinds")
    e = sub.add_parser("example", help="print a starting spec")
    e.add_argument("kind", nargs="?", default="card", choices=list(EXAMPLES))
    a = ap.parse_args(argv)

    if a.cmd == "parts":
        print("parts:")
        for name, doc in parts.describe():
            print(f"  {name:<9} {doc}")
        print("edges:   " + ", ".join(parts.EDGES) + "   (e.g. `- arrow: https`)")
        print("accents: " + ", ".join(style.ACCENTS) + ", or #rrggbb")
        print("kinds:   " + ", ".join(f"{k} {w}x{h}" for k, (w, h) in style.KINDS.items()))
        return 0
    if a.cmd == "example":
        print(EXAMPLES[a.kind], end="")
        return 0
    rc = 0
    for path in a.specs:
        try:
            for f in render_file(path, a.out, png=not a.no_png):
                print(f)
        except (SpecError, RuntimeError, OSError) as err:
            print(f"plaincard: {err}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
