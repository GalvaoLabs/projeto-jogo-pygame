"""Pick real pygame when installed, otherwise the dev-only Pillow shim."""
import os
import sys


def ensure_pygame():
    """Returns 'real' or 'shim'. Call before importing game modules."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    try:
        import pygame  # noqa: F401
        return "shim" if getattr(pygame, "IS_SHIM", False) else "real"
    except ImportError:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pygame_shim"))
        import pygame  # noqa: F401
        return "shim"
