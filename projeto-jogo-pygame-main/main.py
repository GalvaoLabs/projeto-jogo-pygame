"""Startup Tycoon - Build an Empire. Run with: python main.py

The same entry point serves the desktop build (python / PyInstaller) and the browser build
(Pygbag). The game loop yields to the event loop every frame (``await asyncio.sleep(0)``),
which is mandatory in the browser and harmless on the desktop.
"""
import asyncio
import os
import sys
import traceback

from systems import paths


async def main():
    from game import Game
    await Game().run_async()


def _log_crash():
    """A windowed executable has no console: keep the traceback next to the user's settings."""
    try:
        folder = paths.user_config_dir()
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "crash.log"), "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
    except OSError:
        pass


if __name__ == "__main__" or paths.is_web():
    try:
        asyncio.run(main())
    except Exception:
        _log_crash()
        raise
