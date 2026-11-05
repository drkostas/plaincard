from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from plaincard import cli, export, parts, render, render_file, render_spec, spec, style

EXAMPLES = sorted((Path(__file__).parent.parent / "examples").glob("*.yaml"))


def parse_svg(text: str) -> ET.Element:
    return ET.fromstring(text)


def test_every_part_draws_valid_svg_inside_its_box():
    ink = parts.Ink(accent="#d97757")
    for name, fn in parts.PARTS.items():
        d = fn(ink)
        assert d.w > 0 and d.h > 0, name
        parse_svg(f'<svg xmlns="http://www.w3.org/2000/svg"><g>{d.svg}</g></svg>')


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.stem for p in EXAMPLES])
def test_examples_render_to_their_kind_size(path, tmp_path):
    out = render_file(path, tmp_path, png=False)
    root = parse_svg(out[0].read_text())
    s = spec.load(path)
    assert (int(root.get("width")), int(root.get("height"))) == style.KINDS[s.kind]


def test_a_card_keeps_text_above_the_diagram():
    s = spec.parse({"kind": "card", "name": "x", "line": "a " * 40, "diagram": ["cloud", "arrow", "db"]})
    svg = render.svg(s)
    text_bottom = max(float(y) for y in re.findall(r'<text x="72" y="([\d.]+)"', svg) if float(y) < 560)
    m = re.search(r'translate\(([\d.]+) ([\d.]+)\) scale\(([\d.]+)\)', svg)
    assert m and float(m.group(2)) > text_bottom, "the diagram starts below the last line of text"


def test_long_text_is_wrapped_or_refused():
    assert len(render.wrap("word " * 30, 27, 760)) >= 2
    with pytest.raises(spec.SpecError, match="too long"):
        render.svg(spec.parse({"kind": "card", "name": "x", "line": "word " * 200}))
    with pytest.raises(spec.SpecError, match="too long"):
        render.svg(spec.parse({"kind": "card", "name": "n" * 80}))


def test_spec_errors_say_what_to_do():
    with pytest.raises(spec.SpecError, match="unknown part 'rocket'"):
        spec.parse({"kind": "card", "name": "x", "diagram": ["rocket"]})
    with pytest.raises(spec.SpecError, match="has no option colour"):
        spec.parse({"kind": "card", "name": "x", "diagram": [{"db": {"colour": "red"}}]})
    with pytest.raises(spec.SpecError, match="two edges in a row"):
        spec.parse({"kind": "card", "name": "x", "diagram": ["cloud", "arrow", "dots", "db"]})
    with pytest.raises(spec.SpecError, match="unknown accent"):
        spec.parse({"kind": "card", "name": "x", "accent": "pink"})
    with pytest.raises(spec.SpecError, match="needs a name"):
        spec.parse({"kind": "card"})


def test_a_part_keeps_its_own_accent_unless_told(tmp_path):
    lit = render.svg(spec.parse({"kind": "diagram", "accent": "green", "diagram": ["gate"]}))
    dim = render.svg(spec.parse({"kind": "diagram", "accent": "green",
                                 "diagram": [{"gate": {"accent": False}}]}))
    assert style.ACCENTS["green"] in lit and style.ACCENTS["green"] not in dim.split("<g", 1)[1]


def test_yaml_with_an_unquoted_colon_is_explained(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("kind: card\nname: x\nline: one: two\n")
    with pytest.raises(spec.SpecError, match="in quotes"):
        spec.load(p)


def test_cli_lists_parts_and_prints_examples(capsys):
    assert cli.main(["parts"]) == 0
    assert "gate" in capsys.readouterr().out
    for kind in cli.EXAMPLES:
        assert cli.main(["example", kind]) == 0
        spec.parse(__import__("yaml").safe_load(capsys.readouterr().out))


@pytest.mark.skipif(export.chrome() is None, reason="no Chrome or Chromium on this machine")
def test_png_is_twice_the_canvas(tmp_path):
    out = render_spec({"kind": "icon", "diagram": ["db"]}, tmp_path, "db")
    data = out[1].read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    assert (w, h) == (1024, 1024)


STUB = '''#!{python}
import json, struct, sys, time, zlib
from pathlib import Path

calls = Path({calls!r})
plan = {plan!r}
n = len(calls.read_text().splitlines()) if calls.exists() else 0
with calls.open("a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
step = plan[min(n, len(plan) - 1)]
shot = next(a.split("=", 1)[1] for a in sys.argv if a.startswith("--screenshot="))

def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

if step == "hang":
    print("stalled before drawing", file=sys.stderr, flush=True)
    time.sleep(60)
elif step == "exit":
    print("could not start", file=sys.stderr, flush=True)
    sys.exit(3)
else:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
    Path(shot).write_bytes(b"\\x89PNG\\r\\n\\x1a\\n" + chunk(b"IHDR", ihdr)
                           + chunk(b"IDAT", zlib.compress(b"\\x00\\x00")) + chunk(b"IEND", b""))
    if step == "write-and-stay":
        time.sleep(60)
'''


def stub_browser(tmp_path, monkeypatch, plan):
    """A stand-in browser that takes the next step of `plan` on each launch and logs its args."""
    import json
    import sys
    calls = tmp_path / "calls.jsonl"
    stub = tmp_path / "browser"
    stub.write_text(STUB.format(python=sys.executable, calls=str(calls), plan=plan))
    stub.chmod(0o755)
    monkeypatch.setenv("PLAINCARD_CHROME", str(stub))
    svg = tmp_path / "card.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>')

    def launches():
        return [json.loads(line) for line in calls.read_text().splitlines()]
    return svg, launches


def profile_of(args):
    return next(a.split("=", 1)[1] for a in args if a.startswith("--user-data-dir="))


def test_png_launches_again_with_a_fresh_profile_after_a_launch_that_stalls(tmp_path, monkeypatch):
    svg, launches = stub_browser(tmp_path, monkeypatch, ["hang", "write"])
    out = export.png(svg, tmp_path / "card.png", timeout=1)
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    first, second = launches()
    assert profile_of(first) != profile_of(second)
    assert not Path(profile_of(first)).exists() and not Path(profile_of(second)).exists()


def test_png_says_what_each_launch_did_when_none_writes(tmp_path, monkeypatch):
    svg, launches = stub_browser(tmp_path, monkeypatch, ["exit", "hang"])
    with pytest.raises(RuntimeError) as err:
        export.png(svg, tmp_path / "card.png", timeout=1)
    msg = str(err.value)
    assert "launch 1: it exited with code 3 and wrote no PNG" in msg and "could not start" in msg
    assert "launch 2: it was still running after 1s" in msg and "stalled before drawing" in msg
    assert len(launches()) == 2 and not (tmp_path / "card.png").exists()


def test_png_stops_a_browser_that_writes_and_does_not_exit(tmp_path, monkeypatch):
    import time
    svg, launches = stub_browser(tmp_path, monkeypatch, ["write-and-stay"])
    start = time.monotonic()
    out = export.png(svg, tmp_path / "card.png", timeout=20)
    assert out.exists() and time.monotonic() - start < 10 and len(launches()) == 1
