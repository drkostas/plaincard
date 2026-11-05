"""SVG to PNG through a headless Chrome or Chromium, at twice the canvas size.

A real browser draws the fonts and line joins exactly as a reader's browser will, which a pure
converter does not. ⚠️ Headless Chrome can write its screenshot and then fail to exit, and on a
busy machine it can also start slowly or stall before it draws anything. So every launch is
watched: once the PNG is complete the browser is stopped, a launch that writes nothing in its
time is stopped, and the render is tried once more with a fresh profile before it is refused.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
)
NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")

# Each launch gets a profile of its own (so it never waits on another browser's profile lock)
# and skips the start-up work a one-page render does not need: sign-in keyrings, extensions,
# component updates, background requests and the first-run checks.
QUIET_FLAGS = (
    "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
    "--no-default-browser-check", "--disable-extensions", "--disable-component-update",
    "--disable-background-networking", "--disable-sync", "--password-store=basic",
    "--use-mock-keychain", "--disable-dev-shm-usage",
)
PNG_END = b"IEND\xaeB`\x82"     # the last chunk of every complete PNG


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


def _complete(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            if f.read(8) != b"\x89PNG\r\n\x1a\n":
                return False
            f.seek(-len(PNG_END), os.SEEK_END)
            return f.read() == PNG_END
    except OSError:
        return False


def _last_line(path: Path) -> str:
    try:
        lines = [ln.strip() for ln in path.read_text(errors="replace").splitlines() if ln.strip()]
    except OSError:
        return ""
    return lines[-1][:200] if lines else ""


def _launch(browser: str, svg_path: Path, png_path: Path, w: int, h: int, scale: int,
            timeout: float) -> str | None:
    """One launch. None when it wrote a complete PNG, otherwise what went wrong."""
    # a helper process can outlive the browser for a moment, so a profile it still holds stays
    with tempfile.TemporaryDirectory(prefix="plaincard-chrome-",
                                     ignore_cleanup_errors=True) as profile:
        log = Path(profile) / "stderr.log"
        with log.open("wb") as err:
            proc = subprocess.Popen(
                [browser, *QUIET_FLAGS, f"--user-data-dir={profile}",
                 f"--force-device-scale-factor={scale}", f"--window-size={w},{h}",
                 f"--screenshot={png_path}", svg_path.resolve().as_uri()],
                stdout=subprocess.DEVNULL, stderr=err)
            end = time.monotonic() + timeout
            why = None
            try:
                while True:
                    if _complete(png_path):
                        return None
                    code = proc.poll()
                    if code is not None:
                        time.sleep(0.2)      # a write that ended with the process
                        if _complete(png_path):
                            return None
                        why = f"it exited with code {code} and wrote no PNG"
                        break
                    if time.monotonic() >= end:
                        why = f"it was still running after {timeout:.0f}s and had written no PNG"
                        break
                    time.sleep(0.1)
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
        said = _last_line(log)
        return f"{why} (its last message was: {said})" if said else why


def png(svg_path: Path, png_path: Path, scale: int = 2, timeout: float = 60,
        attempts: int = 2) -> Path:
    """Render `svg_path` to `png_path`, waiting up to `timeout` seconds a launch and launching
    up to `attempts` times. Raises RuntimeError saying what each launch did when none wrote it."""
    browser = chrome()
    if browser is None:
        raise RuntimeError("no Chrome or Chromium found; install one or set PLAINCARD_CHROME")
    w, h = size_of(svg_path.read_text())
    png_path = png_path.resolve()
    failures = []
    for n in range(1, max(1, attempts) + 1):
        if png_path.exists():
            png_path.unlink()
        why = _launch(browser, svg_path, png_path, w, h, scale, timeout)
        if why is None:
            return png_path
        failures.append(f"launch {n}: {why}")
    if png_path.exists():
        png_path.unlink()             # never leave a half-written PNG behind
    raise RuntimeError(f"the browser made no PNG for {svg_path.name}. " + ". ".join(failures))
