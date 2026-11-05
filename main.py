# /// script
# dependencies = [
#     "pygame-ce",
# ]
# ///
"""Startup Tycoon - Build an Empire. Run with: python main.py

The same entry point serves every platform:

* Desktop (Windows / macOS / Linux, from source or a PyInstaller build)
* Android (python-for-android / Buildozer)
* Browser (Pygbag / WebAssembly, e.g. itch.io)

The game loop yields to the event loop every frame (``await asyncio.sleep(0)``), which is
mandatory in the browser and harmless elsewhere.
"""
import asyncio
import sys
import traceback

# Pygbag only pre-loads the packages it finds imported in *this* file, so pygame must be
# imported here (not only inside game.py). On every other platform it is just a normal import.
import pygame  # noqa: F401

from systems import paths


async def main():
    from game import Game
    await Game().run_async()


def _log_crash():
    """A windowed executable has no console: keep the traceback next to the user's settings."""
    try:
        from systems.storage import default_storage
        default_storage().write("crash.log", traceback.format_exc())
    except Exception:
        pass


if __name__ == "__main__" or paths.is_web():
    try:
        asyncio.run(main())
    except Exception:
        _log_crash()
        print(traceback.format_exc(), file=sys.stderr)
        raise
