"""A plaincard spec: the few lines a person or an agent writes to describe an image.

    kind: card                 # card | banner | diagram | icon
    name: sqlgate              # the title (cards and banners)
    line: Serve a database you host yourself to serverless apps over HTTPS.
    accent: green              # a named accent or #rrggbb
    footer: github.com/drkostas/sqlgate   # optional, cards only
    caption: How a request reaches the database   # optional, diagrams only
    diagram:                   # parts left to right, joined by edges
      - cloud
      - arrow: https           # an edge, with an optional label
      - gate: {accent: true}
      - line
      - db: {label: postgres}

An item is a part or edge name, or a one-key mapping from that name to a label (a string) or to
options (a mapping). Every option a part takes is listed by `plaincard parts`.
"""
from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from pathlib import Path

from plaincard import parts, style


@dataclass
class Part:
    name: str
    options: dict = field(default_factory=dict)
    label: str | None = None
    accent: bool | None = None      # None: the part's own default (a gate, lock or check is lit)


@dataclass
class Edge:
    kind: str
    label: str | None = None
    length: int = 130


@dataclass
class Spec:
    kind: str
    name: str = ""
    line: str = ""
    accent: str = style.ACCENTS["clay"]
    footer: str = ""
    caption: str = ""
    diagram: list = field(default_factory=list)


class SpecError(ValueError):
    pass


def _item(raw, where: str):
    if isinstance(raw, str):
        name, value = raw, None
    elif isinstance(raw, dict) and len(raw) == 1:
        name, value = next(iter(raw.items()))
    else:
        raise SpecError(f"{where}: an item is a name or a one-key mapping, not {raw!r}")
    if name in parts.EDGES:
        if isinstance(value, dict):
            return Edge(name, value.get("label"), int(value.get("length", 130)))
        return Edge(name, None if value is None else str(value))
    if name not in parts.PARTS:
        raise SpecError(f"{where}: unknown part {name!r}. Parts: {', '.join(parts.PARTS)}; "
                        f"edges: {', '.join(parts.EDGES)}")
    if value is None:
        return Part(name)
    if isinstance(value, str):
        return Part(name, label=value)
    if not isinstance(value, dict):
        raise SpecError(f"{where}: {name} takes a label or a mapping of options, not {value!r}")
    opts = dict(value)
    label = opts.pop("label", None)
    accent = opts.pop("accent", None)
    accent = None if accent is None else bool(accent)
    allowed = set(inspect.signature(parts.PARTS[name]).parameters) - {"ink", "accent"}
    unknown = set(opts) - allowed
    if unknown:
        raise SpecError(f"{where}: {name} has no option {', '.join(sorted(unknown))}; "
                        f"it takes {', '.join(sorted(allowed)) or 'only label and accent'}")
    return Part(name, opts, label, accent)


def parse(data: dict) -> Spec:
    if not isinstance(data, dict):
        raise SpecError("a spec is a mapping")
    kind = data.get("kind", "card")
    if kind not in style.KINDS:
        raise SpecError(f"unknown kind {kind!r}: use one of {', '.join(style.KINDS)}")
    try:
        acc = style.accent(data.get("accent"))
    except ValueError as e:
        raise SpecError(str(e)) from None
    items = [_item(raw, f"diagram item {i + 1}") for i, raw in enumerate(data.get("diagram") or [])]
    for a, b in zip(items, items[1:]):
        if isinstance(a, Edge) and isinstance(b, Edge):
            raise SpecError("two edges in a row: put a part between them")
    if kind in ("card", "banner") and not data.get("name"):
        raise SpecError(f"a {kind} needs a name")
    if kind == "icon" and not items:
        raise SpecError("an icon needs a diagram with at least one part")
    return Spec(kind=kind, name=str(data.get("name") or ""), line=str(data.get("line") or ""),
                accent=acc, footer=str(data.get("footer") or ""),
                caption=str(data.get("caption") or ""), diagram=items)


def load(path: str | Path) -> Spec:
    """A spec from a .yaml, .yml or .json file."""
    p = Path(path)
    text = p.read_text()
    if p.suffix == ".json":
        data = json.loads(text)
    else:
        import yaml  # noqa: PLC0415 - only YAML specs need it
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            where = f" (line {mark.line + 1})" if mark else ""
            raise SpecError(f"{p.name}: not valid YAML{where}. A text containing ': ' or starting "
                            f"with a symbol must be in quotes, for example line: \"...\"") from None
    try:
        return parse(data)
    except SpecError as e:
        raise SpecError(f"{p.name}: {e}") from None
