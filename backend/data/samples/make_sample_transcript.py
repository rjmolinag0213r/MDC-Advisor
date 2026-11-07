"""Generate sample_transcript.png: a fake unofficial transcript for demos of /api/transcript.

Fictional student, synthetic Z-prefixed courses. Run: python data/samples/make_sample_transcript.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROWS = [
    ("Fall 2026", [("ZEN 1101", "English Composition I", "A", 3), ("ZMA 1105", "College Algebra", "B+", 3),
                   ("ZCP 1000", "Introduction to Programming", "A-", 3), ("ZCS 1100", "Computer Concepts", "B", 3),
                   ("ZSC 1005", "Scientific Inquiry", "C", 3)]),
    ("Spring 2027", [("ZEN 1102", "English Composition II", "B", 3), ("ZMA 2311", "Calculus I", "D", 3),
                     ("ZCP 2006", "Programming II", "A", 3), ("ZNT 1110", "Networking Fundamentals", "B-", 3),
                     ("ZAI 1010", "Introduction to AI", "IP", 3)]),
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
    d.rectangle([0, 0, 1100, 110], fill="#0b2545")
    d.text((40, 28), "SAMPLE COLLEGE - Unofficial Transcript", font=font(34, True), fill="white")
    d.text((40, 72), "Student: Alex Rivera (fictional)   ID: 0000000   SYNTHETIC DEMO DATA", font=font(20), fill="#f5c76b")
    y = 140
    for term, courses in ROWS:
        d.text((40, y), term, font=font(26, True), fill="#0b2545")
        y += 44
        d.text((60, y), "Course", font=font(20, True), fill="#334155")
        d.text((230, y), "Title", font=font(20, True), fill="#334155")
        d.text((800, y), "Grade", font=font(20, True), fill="#334155")
        d.text((920, y), "Credits", font=font(20, True), fill="#334155")
        y += 34
        for code, title, grade, cr in courses:
            d.text((60, y), code, font=font(22), fill="#0f172a")
            d.text((230, y), title, font=font(22), fill="#0f172a")
            d.text((815, y), grade, font=font(22), fill="#0f172a")
            d.text((950, y), str(cr), font=font(22), fill="#0f172a")
            y += 36
        y += 30
    d.text((40, 860), "Not an official record. Generated for NextStop testing.", font=font(18), fill="#64748b")
    out = Path(__file__).with_name("sample_transcript.png")
    img.save(out)
    print(out)


if __name__ == "__main__":
    main()
