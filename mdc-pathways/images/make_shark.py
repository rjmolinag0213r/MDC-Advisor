"""Cut the shark mascot out of its JPEG (the checkerboard is painted in, not real transparency) and build
the chat images: shark-head.png (header + reply avatar) and shark-full.png.

How: flood-fill the checkerboard from the image edges, through neutral light/grey pixels only, so the fill
stops at the shark's dark navy outline and never reaches the white face or grey shirt inside it.
Run: python mdc-pathways/images/make_shark.py <shark.jpg>   (needs Pillow)
"""
import sys
from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter

HERE = Path(__file__).parent


def is_bg(p) -> bool:
    r, g, b = p[:3]
    v, spread = (r + g + b) / 3, max(r, g, b) - min(r, g, b)
    return spread < 24 and v > 120     # checker white/grey and the faint watermark letters (JPEG noise allowed)


def cut(src: Path) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    px = im.load()
    bg = bytearray(w * h)
    # seed from the top and both sides only: the grey shirt runs off the bottom edge, and a fill started
    # there would eat it (the background below is still reached around the sides)
    q = deque((x, 0) for x in range(w))
    q.extend((x, y) for y in range(h) for x in (0, w - 1))
    while q:
        x, y = q.popleft()
        i = y * w + x
        if bg[i] or not is_bg(px[x, y]):
            continue
        bg[i] = 1
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not bg[ny * w + nx]:
                q.append((nx, ny))
    mask = Image.frombytes("L", (w, h), bytes(0 if b else 255 for b in bg))
    mask = mask.filter(ImageFilter.MinFilter(3))            # eat the 1px JPEG halo around the outline
    im.putalpha(mask)
    return im.crop(mask.getbbox())


def square(img: Image.Image, size: int, box=None) -> Image.Image:
    if box:
        img = img.crop(box)
    s = max(img.size)
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    canvas.alpha_composite(img, ((s - img.width) // 2, (s - img.height) // 2))
    return canvas.resize((size, size), Image.LANCZOS)


def main(src: str):
    full = cut(Path(src))
    full.save(HERE / "shark-full.png")
    w, h = full.size
    head = (0, 0, w, int(h * 0.60))                         # fin to chin: the part that reads at avatar size
    square(full, 160, head).save(HERE / "shark-head.png")
    print("shark-full.png", full.size, "| shark-head.png 160x160")


if __name__ == "__main__":
    main(sys.argv[1])
