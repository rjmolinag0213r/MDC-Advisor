"""Generate sample_mdc_transcript.png: a fake unofficial transcript that uses REAL MDC course numbers
from the Applied AI program sheets (25080 / S9520). The student and grades are fictional.

Run: python data/samples/make_sample_mdc_transcript.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROWS = [
    ("Fall 2025", [("ENC 1101", "English Composition 1", "A", 3), ("MAC 1105", "College Algebra", "B+", 3),
                   ("CAI 1001C", "Artificial Intelligence (AI) Thinking", "A", 3),
                   ("CGS 1060C", "Intro to Computer Technology & Applications", "A-", 4),
                   ("PSY 2012", "Introduction to Psychology", "B", 3)]),
    ("Spring 2026", [("COP 1047C", "Introduction to Python Programming", "A", 4), ("STA 2023", "Statistical Methods", "B", 3),
                     ("ENC 1102", "English Composition 2", "B+", 3), ("AMH 2020", "History of the US Since 1877", "C+", 3),
                     ("MAC 1114", "Trigonometry", "D", 3)]),
    ("Fall 2026", [("CAI 2100C", "Machine Learning Foundations", "IP", 3), ("PHI 2680", "Artificial Intelligence and Ethics", "IP", 3)]),
]


def font(size, bold=False):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    img = Image.new("RGB", (1100, 1000), "#fbfaf7")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1100, 110], fill="#0b2545")
    d.text((40, 24), "MIAMI DADE COLLEGE - Unofficial Course History (SAMPLE)", font=font(30, True), fill="white")
    d.text((40, 70), "Student: Sam Ortiz (fictional)   Program: Applied AI   Real MDC course numbers, made-up grades",
           font=font(18), fill="#f5c76b")
    y = 135
    for term, courses in ROWS:
        d.text((40, y), term, font=font(24, True), fill="#0b2545")
        y += 40
        for label, x in (("Course", 60), ("Title", 220), ("Grade", 830), ("Credits", 930)):
            d.text((x, y), label, font=font(19, True), fill="#334155")
        y += 32
        for code, title, grade, cr in courses:
            d.text((60, y), code, font=font(21), fill="#0f172a")
            d.text((220, y), title, font=font(21), fill="#0f172a")
            d.text((845, y), grade, font=font(21), fill="#0f172a")
            d.text((960, y), str(cr), font=font(21), fill="#0f172a")
            y += 34
        y += 26
    d.text((40, 960), "Not an official record. Generated for NextStop testing.", font=font(17), fill="#64748b")
    out = Path(__file__).with_name("sample_mdc_transcript.png")
    img.save(out)
    print(out)


if __name__ == "__main__":
    main()
