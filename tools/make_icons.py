"""Generate the app icons (original artwork, drawn with Pillow) for every platform.

    python tools/make_icons.py

Writes assets/icon.png (512px, used by the window, Android and the web favicon),
assets/icon.ico (Windows) and assets/icon.icns (macOS).
"""
import os

from PIL import Image, ImageDraw

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
S = 2048          # draw large, then downsample for smooth edges


def draw_icon() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # background: vertical gradient inside a rounded square
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    top, bottom = (36, 44, 78), (14, 17, 30)
    for y in range(S):
        f = y / (S - 1)
        gd.line([(0, y), (S, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * f) for i in range(3)) + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=int(S * 0.22), fill=255)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((12, 12, S - 13, S - 13), radius=int(S * 0.22), outline=(84, 98, 150, 255), width=18)

    # three growing bars: the company's revenue
    base, w, gap = int(S * 0.76), int(S * 0.17), int(S * 0.055)
    x0 = (S - (3 * w + 2 * gap)) // 2
    bars = [((77, 140, 255), 0.20), ((155, 110, 240), 0.33), ((46, 204, 113), 0.46)]
    tops = []
    for i, (col, h) in enumerate(bars):
        x = x0 + i * (w + gap)
        y = base - int(S * h)
        d.rounded_rectangle((x, y, x + w, base), radius=int(w * 0.16), fill=col + (255,))
        tops.append((x + w // 2, y))

    # arrow riding on top of the bars
    pts = [(tops[0][0] - int(w * 0.2), tops[0][1] - int(S * 0.07)), (tops[1][0], tops[1][1] - int(S * 0.08)),
           (tops[2][0] + int(w * 0.1), tops[2][1] - int(S * 0.11))]
    d.line(pts, fill=(255, 215, 64, 255), width=int(S * 0.028), joint="curve")
    ex, ey = pts[-1]
    d.polygon([(ex + int(S * 0.075), ey - int(S * 0.075)), (ex - int(S * 0.03), ey - int(S * 0.05)),
               (ex + int(S * 0.05), ey + int(S * 0.03))], fill=(255, 215, 64, 255))
    # coin
    r = int(S * 0.055)
    cx, cy = int(S * 0.27), int(S * 0.27)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 215, 64, 255), outline=(214, 160, 20, 255), width=14)
    d.line([(cx, cy - r // 2), (cx, cy + r // 2)], fill=(214, 160, 20, 255), width=16)
    return img


def main():
    big = draw_icon()
    png = big.resize((512, 512), Image.LANCZOS)
    png.save(os.path.join(ASSETS, "icon.png"))
    png.save(os.path.join(ASSETS, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    big.resize((1024, 1024), Image.LANCZOS).save(os.path.join(ASSETS, "icon.icns"))
    big.resize((96, 96), Image.LANCZOS).save(os.path.join(ASSETS, "favicon.png"))
    print("icons written to", ASSETS)


if __name__ == "__main__":
    main()
