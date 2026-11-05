"""Sound effects, synthesized at runtime (no audio files to ship, so the web build stays tiny).

Everything is lazy and defensive: the mixer is only opened on the first sound, and any problem
(no audio device, browser blocking audio, unsupported format) just turns sound off for the
session. The game never depends on audio working.
"""
import math

SAMPLE_RATE = 22050

# name -> list of (frequency_hz | (start_hz, end_hz), seconds, volume, wave)
RECIPES = {
    "click":   [(880, 0.035, 0.35, "square")],
    "error":   [(190, 0.11, 0.45, "saw"), (150, 0.16, 0.45, "saw")],
    "hire":    [(523.25, 0.08, 0.4, "sine"), (783.99, 0.14, 0.4, "sine")],
    "month":   [((260, 620), 0.28, 0.35, "sine")],
    "release": [(523.25, 0.09, 0.4, "square"), (659.25, 0.09, 0.4, "square"),
                (783.99, 0.09, 0.4, "square"), (1046.5, 0.22, 0.4, "square")],
    "victory": [(523.25, 0.12, 0.45, "square"), (659.25, 0.12, 0.45, "square"), (783.99, 0.12, 0.45, "square"),
                (1046.5, 0.18, 0.45, "square"), (783.99, 0.1, 0.45, "square"), (1046.5, 0.5, 0.45, "square")],
    "defeat":  [(392.0, 0.22, 0.45, "saw"), (329.63, 0.22, 0.45, "saw"), (261.63, 0.22, 0.45, "saw"),
                (196.0, 0.55, 0.45, "saw")],
}


def _wave(kind, phase):
    if kind == "square":
        return 1.0 if math.sin(phase) >= 0 else -1.0
    if kind == "saw":
        x = (phase / (2 * math.pi)) % 1.0
        return 2.0 * x - 1.0
    return math.sin(phase)


def synthesize(recipe, rate=SAMPLE_RATE):
    """Recipe -> list of float samples in [-1, 1]."""
    out = []
    for freq, secs, vol, kind in recipe:
        n = max(1, int(rate * secs))
        attack = max(1, int(rate * 0.004))
        phase = 0.0
        for i in range(n):
            f = freq if not isinstance(freq, tuple) else freq[0] + (freq[1] - freq[0]) * i / n
            phase += 2 * math.pi * f / rate
            env = min(1.0, i / attack) * (1.0 - i / n) ** 1.5      # click-free attack, smooth decay
            out.append(_wave(kind, phase) * vol * env)
    return out


class Audio:
    def __init__(self, enabled=True, volume=80):
        self.enabled = enabled
        self.volume = volume                 # 0..100
        self._ready = None                   # None = not tried yet, False = unavailable
        self._channels = 1
        self._cache = {}

    # ------------------------------------------------------------ setup
    def _init(self) -> bool:
        if self._ready is not None:
            return self._ready
        self._ready = False
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            fmt = pygame.mixer.get_init()
            if not fmt or fmt[1] != -16:
                return False
            self._rate, self._channels = fmt[0], fmt[2]
            self._ready = True
        except Exception:
            self._ready = False
        return self._ready

    def _build(self, name):
        import pygame
        from array import array
        samples = synthesize(RECIPES[name], self._rate)
        data = array("h")
        for s in samples:
            v = int(max(-1.0, min(1.0, s)) * 32767)
            for _ in range(self._channels):
                data.append(v)
        return pygame.mixer.Sound(buffer=data.tobytes())

    # ------------------------------------------------------------ api
    def play(self, name):
        if not self.enabled or self.volume <= 0 or name not in RECIPES:
            return
        try:
            if not self._init():
                return
            snd = self._cache.get(name)
            if snd is None:
                snd = self._cache[name] = self._build(name)
            snd.set_volume(self.volume / 100.0)
            snd.play()
        except Exception:
            self._ready = False              # give up quietly for the rest of the session

    def set_volume(self, volume):
        self.volume = int(max(0, min(100, volume)))

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
