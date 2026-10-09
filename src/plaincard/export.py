"""SVG to PNG through a headless Chrome or Chromium, at twice the canvas size.

A real browser draws the fonts and line joins exactly as a reader's browser will, which a pure
converter does not. ⚠️ Headless Chrome can write its screenshot and then fail to exit, so every run
is watched: once the PNG exists it is stopped, and a run that writes nothing is stopped and refused.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
)
NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")


def chrome() -> str | None:
    """The browser to render with: $PLAINCARD_CHROME, a standard install, or one on PATH."""
    env = os.environ.get("PLAINCARD_CHROME")
    if env and Path(env).exists():
        return env
    for c in CANDIDATES:
        if Path(c).exists():
            return c
    for n in NAMES:
        found = shutil.which(n)
        if found:
            return found
    return None


def size_of(svg_text: str) -> tuple[int, int]:
    m = re.search(r'<svg[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', svg_text)
    if not m:
        raise ValueError("the SVG has no width and height")
    return int(m.group(1)), int(m.group(2))


def png(svg_path: Path, png_path: Path, scale: int = 2, timeout: float = 30) -> Path:
    """Render `svg_path` to `png_path`. Raises RuntimeError with the reason when it cannot."""
    browser = chrome()
    if browser is None:
        raise RuntimeError("no Chrome or Chromium found; install one or set PLAINCARD_CHROME")
    w, h = size_of(svg_path.read_text())
    png_path = png_path.resolve()
    if png_path.exists():
        png_path.unlink()
    proc = subprocess.Popen(
        [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
         f"--force-device-scale-factor={scale}", f"--window-size={w},{h}",
         f"--screenshot={png_path}", svg_path.resolve().as_uri()],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.time() + timeout
    try:
        while time.time() < end:
            if png_path.exists() and png_path.stat().st_size > 0:
                time.sleep(0.5)          # let the write finish
                return png_path
            if proc.poll() is not None and not png_path.exists():
                break
            time.sleep(0.25)
        raise RuntimeError(f"the browser wrote no PNG for {svg_path.name} within {timeout:.0f}s")
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                proc.kill()
