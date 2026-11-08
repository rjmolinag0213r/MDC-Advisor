"""Build the browser-tab icon from Cris's white MD logo: logo on a dark synthwave tile with a sand underline.

Run: python mdc-pathways/images/make_favicon.py  (needs Pillow)
"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent
TILE, SAND = (42, 10, 58, 255), (240, 168, 116, 255)   # deep purple of the hub bar, Cris's sand accent


def icon(size: int) -> Image.Image:
    big = size * 4                                       # draw large, then downscale for smooth edges
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, big - 1, big - 1], radius=big // 5, fill=TILE)
    logo = Image.open(HERE / "mdc-logo-md.png").convert("RGBA")
    logo = logo.crop(logo.getchannel("A").getbbox())
    w = int(big * 0.74)
    h = int(logo.height * w / logo.width)
    if h > big * 0.56:
        h = int(big * 0.56)
        w = int(logo.width * h / logo.height)
    logo = logo.resize((w, h), Image.LANCZOS)
    top = (big - h) // 2 - big // 14
    img.alpha_composite(logo, ((big - w) // 2, top))
    bar = max(big // 16, 4)
    y = top + h + big // 14
    d.rounded_rectangle([big * 0.24, y, big * 0.76, y + bar], radius=bar // 2, fill=SAND)
    return img.resize((size, size), Image.LANCZOS)


def main():
    icon(32).save(HERE / "favicon-32.png")
    icon(180).save(HERE / "apple-touch-icon.png")
    icon(256).save(HERE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print("favicon-32.png, apple-touch-icon.png, favicon.ico")


if __name__ == "__main__":
    main()
