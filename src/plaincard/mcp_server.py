"""plaincard as an MCP server: render an image from a spec, list the parts, show an example.

    plaincard-mcp            (stdio; needs `pip install 'plaincard[mcp]'`)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def build():
    from mcp.server.fastmcp import FastMCP  # noqa: PLC0415 - optional dependency

    from plaincard import cli, parts, render_spec, style  # noqa: PLC0415
    from plaincard.spec import SpecError  # noqa: PLC0415

    mcp = FastMCP("plaincard")

    @mcp.tool()
    def render_image(spec: str, out_dir: str, name: str, png: bool = True) -> str:
        """Render a plaincard image. `spec` is the spec as YAML or JSON text (kind, name, line,
        accent, footer, caption, diagram); `out_dir` is the folder to write into, usually the
        project's images folder; `name` is the file name without extension. Writes NAME.svg and,
        unless png is false, NAME.png at twice the size. Returns the paths, or the reason it cannot.
        Open the PNG and look at it before using it."""
        try:
            data = json.loads(spec) if spec.lstrip().startswith("{") else __import__("yaml").safe_load(spec)
            files = render_spec(data, Path(out_dir).expanduser(), name, png=png)
            return json.dumps({"ok": True, "files": [str(f) for f in files]})
        except (SpecError, RuntimeError, ValueError, OSError) as e:
            return json.dumps({"ok": False, "reason": str(e)})

    @mcp.tool()
    def list_parts() -> str:
        """The parts and edges a diagram can use, the accents and the kinds with their sizes."""
        return json.dumps({"parts": dict(parts.describe()), "edges": list(parts.EDGES),
                           "accents": style.ACCENTS, "kinds": style.KINDS})

    @mcp.tool()
    def example(kind: str = "card") -> str:
        """A starting spec for a kind: card, banner, diagram or icon."""
        return cli.EXAMPLES.get(kind, cli.EXAMPLES["card"])

    return mcp


def main() -> int:
    build().run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
