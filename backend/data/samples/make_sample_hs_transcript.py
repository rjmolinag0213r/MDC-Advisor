"""Generate sample_hs_transcript.png: a fake unofficial HIGH-SCHOOL transcript for demos of /api/transcript.

Fictional student, synthetic data. Run: python data/samples/make_sample_hs_transcript.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROWS = [
    ("Grade 10 (2024-2025)", [("Geometry Honors", "A", "1.0"), ("English 2", "B", "1.0"), ("Biology", "B+", "1.0"),
                              ("World History", "B-", "1.0"), ("Spanish 2", "A-", "1.0"), ("Intro to Programming", "A", "1.0")]),
    ("Grade 11 (2025-2026)", [("Algebra 2 Honors", "A", "1.0"), ("AP Computer Science Principles", "A", "1.0"),
                              ("Chemistry", "B", "1.0"), ("English 3", "B", "1.0"), ("US History", "C+", "1.0"),
                              ("Digital Art", "B+", "0.5")]),
]


def font(size, bold=False):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    img = Image.new("RGB", (1100, 900), "#fbfaf7")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1100, 110], fill="#3b0d4f")
    d.text((40, 28), "SAMPLE HIGH SCHOOL - Unofficial Transcript", font=font(34, True), fill="white")
    d.text((40, 72), "Student: Jordan Lee (fictional)   Grade 12   SYNTHETIC DEMO DATA", font=font(20), fill="#f0a874")
    y = 140
    for term, courses in ROWS:
        d.text((40, y), term, font=font(26, True), fill="#3b0d4f")
        y += 44
        d.text((60, y), "Course", font=font(20, True), fill="#334155")
        d.text((800, y), "Grade", font=font(20, True), fill="#334155")
        d.text((920, y), "Credit", font=font(20, True), fill="#334155")
        y += 34
        for title, grade, cr in courses:
            d.text((60, y), title, font=font(22), fill="#0f172a")
            d.text((815, y), grade, font=font(22), fill="#0f172a")
            d.text((940, y), cr, font=font(22), fill="#0f172a")
            y += 36
        y += 30
    d.text((40, 860), "Not an official record. Generated for NextStop testing.", font=font(18), fill="#64748b")
    out = Path(__file__).with_name("sample_hs_transcript.png")
    img.save(out)
    print(out)


if __name__ == "__main__":
    main()
