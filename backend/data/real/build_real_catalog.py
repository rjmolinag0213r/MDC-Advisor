"""Build the REAL catalog layer: MDC's Applied AI A.S. and B.S. from the official program sheets, plus
transfer universities (FIU, UM, UCF, USF) with official tuition and the program sheets we have.

Sources (copied by hand from the official documents, effective Spring 2026 / 2026-08-01):
  - MDC Applied Artificial Intelligence, Associate in Science, code 25080 (60 credits)
  - MDC Applied Artificial Intelligence, Bachelor of Science, code S9520 (120 credits)
  - FIU program sheets: IOTAI:BS, BIOMEG:MS, CIVLEG:PHD (catalog 2026-08-01)
  - University of Miami Academic Bulletin course lists: Computer Science (CSC), Medicine (MDR)
  - Tuition: costcalculator.fiu.edu, admissions.miami.edu cost of attendance 2026-27,
    studentaccounts.ucf.edu current rates 2026-27, stpetersburg.usf.edu at-a-glance 2026-27,
    nwsa.mdc.edu tuition (MDC per-credit rates)

What is NOT on the sheets is marked so the UI can label it:
  - terms_offered: the sheets don't say, so every course is assumed Fall/Spring/Summer ("terms_assumed": true)
  - prerequisites outside these programs (e.g. MAT 1033 placement) are kept as text only
  - UM equivalencies and UCF/USF requirement lists are modeled ("synthetic": true), not official

Run: python data/real/build_real_catalog.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
SHEET_BS = "MDC program sheet S9520, Applied Artificial Intelligence B.S., effective Spring 2026 (2263)"
SHEET_AS = "MDC program sheet 25080, Applied Artificial Intelligence A.S., effective Spring 2026 (2263)"

# code, title, credits, category, prerequisite text from the sheet ("A and B", "A or B", "" for none)
COURSES = [
    # communications / gen ed
    ("ENC 1101", "English Composition 1", 3, "gen_ed", ""),
    ("ENC 1102", "English Composition 2", 3, "gen_ed", "ENC 1101"),
    ("ENC 2300", "Advanced Composition & Communication", 3, "gen_ed", "ENC 1101 and ENC 1102"),
    ("SPC 1017", "Introduction to Communications", 3, "gen_ed", ""),
    ("SPC 2608", "Introduction to Public Speaking", 3, "gen_ed", ""),
    ("ARH 1000", "Art Appreciation", 3, "gen_ed", ""),
    ("HUM 1020", "Introduction to Humanities", 3, "gen_ed", ""),
    ("LIT 2000", "Introduction to Literature", 3, "gen_ed", "ENC 1101"),
    ("MUL 1010", "Music Appreciation", 3, "gen_ed", ""),
    ("PHI 2010", "Introduction to Philosophy", 3, "gen_ed", ""),
    ("THE 2000", "Theatre Appreciation", 3, "gen_ed", ""),
    ("PHI 2600", "Introduction to Ethics", 3, "gen_ed", ""),
    ("ARH 2050", "Art History 1", 3, "gen_ed", ""),
    ("AMH 2010", "History of the US to 1877", 3, "gen_ed", ""),
    ("AMH 2020", "History of the US Since 1877", 3, "gen_ed", ""),
    ("POS 2041", "American Federal Government", 3, "gen_ed", ""),
    ("PSY 2012", "Introduction to Psychology", 3, "gen_ed", ""),
    ("ECO 2013", "Principles of Economics (Macro)", 3, "gen_ed", ""),
    ("ANT 2000", "Introduction to Anthropology", 3, "gen_ed", ""),
    ("SYG 2000", "Introduction to Sociology", 3, "gen_ed", ""),
    ("WOH 2012", "History of World Civilization to 1789", 3, "gen_ed", ""),
    ("AST 1002", "Descriptive Astronomy", 3, "gen_ed", ""),
    ("BSC 1005", "General Education Biology", 3, "gen_ed", ""),
    ("CHM 1020", "General Education Chemistry", 3, "gen_ed", ""),
    ("ESC 1000", "General Education Earth Science", 3, "gen_ed", ""),
    ("EVR 1001", "Introduction to Environmental Science", 3, "gen_ed", ""),
    ("GLY 1010", "Physical Geology", 3, "gen_ed", ""),
    ("OCE 1001", "Introduction to Oceanography", 3, "gen_ed", ""),
    ("PHY 1020", "General Education Physics", 3, "gen_ed", ""),
    ("HUN 1201", "Essentials of Human Nutrition", 3, "gen_ed", ""),
    ("PHY 2053", "Physics (without Calculus) 1", 3, "gen_ed", "MAC 1114 or MAC 1147"),
    ("PHY 2054", "Physics (without Calculus) 2", 3, "gen_ed", "PHY 2053"),
    ("PHY 2048", "Physics with Calculus 1", 4, "gen_ed", "MAC 2311"),
    ("PHY 2049", "Physics with Calculus 2", 4, "gen_ed", "PHY 2048"),
    # mathematics
    ("MAC 1105", "College Algebra", 3, "gen_ed", "MAT 1033"),
    ("STA 2023", "Statistical Methods", 3, "gen_ed", "MAT 1033 or MGF 1131"),
    ("MAC 1114", "Trigonometry", 3, "gen_ed", "MAC 1105"),
    ("MAC 1140", "Pre-Calculus Algebra", 3, "gen_ed", "MAC 1105"),
    ("MAC 1147", "Pre-Calculus Algebra and Trigonometry", 5, "gen_ed", "MAC 1105"),
    ("MAC 2311", "Calculus and Analytical Geometry 1", 5, "gen_ed", "MAC 1147 or MAC 1140"),
    ("MAC 2312", "Calculus and Analytical Geometry 2", 4, "gen_ed", "MAC 2311"),
    ("MAD 2104", "Discrete Mathematics", 3, "gen_ed", "MAC 1140"),
    ("MAS 2103", "Elementary Linear Algebra", 3, "gen_ed", "MAC 2311"),
    # technology: lower division
    ("CGS 1060C", "Introduction to Computer Technology and Applications", 4, "common_core", ""),
    ("CAI 1001C", "Artificial Intelligence (AI) Thinking", 3, "program_core", ""),
    ("COP 1047C", "Introduction to Python Programming", 4, "program_core", ""),
    ("CAI 2100C", "Machine Learning Foundations", 3, "program_core", "CAI 1001C and COP 1047C"),
    ("CAI 2300C", "Introduction to Natural Language Processing", 3, "program_core", "CAI 2100C"),
    ("CAI 2840C", "Introduction to Computer Vision", 3, "program_core", "CAI 2100C"),
    ("CAI 2820C", "Artificial Intelligence Application Solutions", 3, "program_core", "CAI 2300C and CAI 2840C"),
    ("COP 2800", "Java Programming", 4, "program_core", "COP 1047C or COP 1334 or COP 2270"),
    ("PHI 2680", "Artificial Intelligence and Ethics", 3, "program_core", ""),
    ("CGS 1540C", "Database Concepts and Design", 4, "program_core", ""),
    ("CTS 1145", "Cloud Essentials", 4, "program_core", ""),
    ("CAP 1788", "Introduction to Data Analytics", 4, "elective", ""),
    ("CTS 1120", "Cybersecurity Fundamentals", 4, "elective", ""),
    ("ETS 1603C", "Introduction to Robotics", 4, "elective", ""),
    ("GEB 1432", "Applied Artificial Intelligence (AI) in Business", 3, "elective", ""),
    ("HSC 2060", "Artificial Intelligence Applications in Healthcare", 3, "elective", ""),
    # technology: upper division (B.S.)
    ("COP 3530", "Data Structures", 4, "program_core", "COP 2800"),
    ("CAI 3303C", "Natural Language Processing", 3, "program_core", "CAI 2300C"),
    ("CAI 3821C", "Computational Methods and Applications for Artificial Intelligence 1", 3, "program_core",
     "CAI 2100C and COP 1047C and MAC 1105 and STA 2023"),
    ("CAI 3822C", "Computational Methods and Applications for Artificial Intelligence 2", 3, "program_core", "CAI 3821C"),
    ("CAI 4505C", "Artificial Intelligence", 3, "program_core", "CAI 3822C and COP 3530"),
    ("CAI 4510C", "Machine Intelligence", 3, "program_core", "CAI 3822C and COP 3530"),
    ("CAI 4420C", "Applied Decision and Optimization Theory", 3, "program_core", "CAI 4505C"),
    ("CAI 4525C", "Artificial Intelligence Systems Automation", 3, "program_core", "CAI 4505C and CAI 4510C"),
    ("CAI 4830C", "Simulation for Applied Artificial Intelligence", 3, "program_core", "CAI 4505C (pre/corequisite)"),
    ("CAI 4950C", "Artificial Intelligence Capstone", 3, "capstone",
     "CAI 4510C and CAI 4420C and CAI 4830C and CAI 4525C (pre/corequisite)"),
    ("CAP 3330", "Programming R for Statistics", 4, "program_core", "STA 2023"),
    ("STA 3164", "Statistical Methods II", 4, "program_core", "STA 2023"),
]
CODES = {c[0] for c in COURSES}


def prereq_groups(text: str) -> list[list[str]]:
    """'A and B or C' -> [[A], [B, C]]. Options outside this catalog are dropped (kept in the text);
    a group left empty (only outside options, e.g. MAT 1033 placement) is treated as met."""
    groups = []
    for part in text.replace("(pre/corequisite)", "").split(" and "):
        opts = [o.strip() for o in part.split(" or ") if o.strip()]
        inside = [o for o in opts if o in CODES]
        if inside and len(inside) == len(opts) or (inside and len(inside) < len(opts)):
            groups.append(inside)
    return groups


def course(code, title, credits, category, prereq):
    num = int("".join(ch for ch in code.split()[1] if ch.isdigit()))
    return {"code": code, "title": title, "credits": credits, "level": "upper" if num >= 3000 else "lower",
            "category": category, "prefix": code.split()[0], "description": f"{title} (from the MDC program sheet).",
            "prerequisites": prereq_groups(prereq), "prerequisite_text": prereq or None, "corequisites": [],
            "min_grade": "C", "min_credits_completed": None, "instructor_permission": False,
            "terms_offered": ["Fall", "Spring", "Summer"], "terms_assumed": True, "cross_listed_as": [],
            "status": "active", "synthetic": False, "source": SHEET_BS if num >= 3000 else "MDC program sheets 25080 / S9520",
            "used_by_programs": []}


HUM = ["ARH 1000", "HUM 1020", "LIT 2000", "MUL 1010", "PHI 2010", "THE 2000", "PHI 2600", "ARH 2050"]
SOC = ["AMH 2010", "AMH 2020", "POS 2041", "PSY 2012", "ECO 2013", "ANT 2000", "SYG 2000", "WOH 2012"]
SCI = ["AST 1002", "BSC 1005", "CHM 1020", "ESC 1000", "EVR 1001", "GLY 1010", "OCE 1001", "PHY 1020", "HUN 1201"]

PROGRAMS = [
    {"id": "MDC-S9520", "app_program_code": "AIBS", "name": "Applied Artificial Intelligence", "credential": "B.S.",
     "degree": "Bachelor of Science (MDC official program sheet)", "sheet_code": "S9520", "total_credits": 120,
     "min_gpa": 2.0, "min_grade_in_major": "C", "synthetic": False, "source": SHEET_BS,
     "notes": ["Civic literacy: one social science must be AMH 2010, AMH 2020 or POS 2041, plus an approved assessment.",
               "Computer competency: CGS 1060C or MDC's competency test by the 31st credit.",
               "Foreign language: two years in high school, an elementary 2 course, or an exam."],
     "requirement_groups": [
         {"group": "Communications", "rule": "all", "courses": ["ENC 1101", "ENC 1102"], "credits": 6},
         {"group": "Oral Communications", "rule": "choose_credits", "courses": ["SPC 1017", "SPC 2608", "ENC 2300"], "credits": 3},
         {"group": "Humanities", "rule": "choose_credits", "courses": HUM, "credits": 6},
         {"group": "Social Sciences", "rule": "choose_credits", "courses": SOC, "credits": 6},
         {"group": "Natural Sciences", "rule": "choose_credits", "courses": SCI, "credits": 6},
         {"group": "Mathematics", "rule": "all", "courses": ["MAC 1105", "STA 2023"], "credits": 6},
         {"group": "General Education Elective", "rule": "choose_credits", "courses": ["MAC 1114", "MAC 1140", "MAC 2311", "MAD 2104", "MAS 2103", "PHY 2053"], "credits": 3},
         {"group": "Lower Division Technology A", "rule": "all", "courses": ["CAI 1001C", "COP 1047C", "CAI 2100C", "CAI 2300C"], "credits": 13},
         {"group": "Lower Division Technology B", "rule": "all", "courses": ["CAI 2840C", "COP 2800", "PHI 2680"], "credits": 10},
         {"group": "Lower Division Technology C", "rule": "choose_credits", "courses": ["CGS 1060C", "CGS 1540C", "CTS 1145"], "credits": 8},
         {"group": "Upper Division Core", "rule": "all", "credits": 31,
          "courses": ["COP 3530", "CAI 3303C", "CAI 3821C", "CAI 3822C", "CAI 4505C", "CAI 4510C", "CAI 4420C", "CAI 4525C", "CAI 4830C", "CAI 4950C"]},
         {"group": "Upper Division Statistics", "rule": "choose_credits", "courses": ["CAP 3330", "STA 3164"], "credits": 4},
         {"group": "Program Electives", "rule": "choose_credits", "credits": 18,
          "courses": ["CAI 2820C", "CAP 1788", "CTS 1120", "ETS 1603C", "GEB 1432", "HSC 2060"]},
     ]},
    {"id": "MDC-25080", "app_program_code": "AIAS", "name": "Applied Artificial Intelligence", "credential": "A.S.",
     "degree": "Associate in Science (MDC official program sheet)", "sheet_code": "25080", "total_credits": 60,
     "min_gpa": 2.0, "min_grade_in_major": "C", "synthetic": False, "source": SHEET_AS,
     "notes": ["Leads to jobs as an AI developer or AI specialist, and stacks into the B.S. (S9520)."],
     "requirement_groups": [
         {"group": "Communications", "rule": "all", "courses": ["ENC 1101"], "credits": 3},
         {"group": "Humanities", "rule": "choose_credits", "courses": HUM[:6], "credits": 3},
         {"group": "Mathematics", "rule": "all", "courses": ["MAC 1105"], "credits": 3},
         {"group": "Natural Sciences", "rule": "choose_credits", "courses": SCI[:8], "credits": 3},
         {"group": "Social Sciences", "rule": "choose_credits", "courses": ["AMH 2010", "AMH 2020", "POS 2041"], "credits": 3},
         {"group": "Major Courses", "rule": "all", "credits": 37,
          "courses": ["CAI 1001C", "CAI 2100C", "CAI 2300C", "CAI 2820C", "CAI 2840C", "CGS 1060C", "CGS 1540C",
                      "COP 1047C", "CTS 1145", "PHI 2680", "STA 2023"]},
         {"group": "Program Electives", "rule": "choose_credits", "credits": 8,
          "courses": ["CAP 1788", "COP 2800", "CTS 1120", "ETS 1603C", "GEB 1432", "HSC 2060"]},
     ]},
]

# ---------------- universities ----------------
FIU_IOTAI = {
    "code": "IOTAI:BS", "name": "Applied AI & Internet of Things", "degree": "B.S.", "credits": 120, "years": 4,
    "college": "College of Engineering and Computing", "official": True,
    "source": "FIU program sheet IOTAI:BS (catalog 2026-08-01)",
    "progression": "Finish MAC 1147 (or MAC 1114 Trigonometry) within three terms of enrolling.",
    "requirements": [
        {"group": "Common prerequisites", "official": True, "courses": [
            ["MAC 1105"], ["MAC 1114", "MAC 1147"], ["PHY 2053"], ["PHY 2054"]]},
        {"group": "Applied AI & IoT core (45 credits)", "official": True, "courses": [
            ["TCN 2720"], ["CTS 1120"], ["EGN 2271"], ["CDA 3104"], ["EEL 2880"], ["EEL 4730"], ["TCN 4940"],
            ["EEL 4806"], ["EEL 4802", "EEL 4804"], ["CNT 3143"], ["CNT 4149"], ["CNT 4153"], ["CNT 4155"],
            ["CAI 3864"], ["CAI 4863"]]},
        {"group": "ECE electives (9 credits)", "official": True, "chooseCredits": 9, "courses": [
            ["TCN 4211"], ["TCN 4081"], ["CNT 4147"], ["CNT 4151"], ["CNT 3142"], ["EEE 4717"], ["CAI 4854"]]},
    ],
    "titles": {"TCN 2720": "Introduction to Internet of Things", "CTS 1120": "Fundamentals of Cybersecurity",
               "EGN 2271": "Introduction to Circuits and Electronic Hardware", "CDA 3104": "Introduction to Computer Design",
               "EEL 2880": "C Programming for Embedded Systems", "EEL 4730": "Programming Embedded Systems",
               "TCN 4940": "Senior Project", "EEL 4806": "Ethical Hacking and Countermeasures",
               "EEL 4802": "Introduction to Digital Forensics Engineering", "EEL 4804": "Introduction to Malware Reverse Engineering",
               "CNT 3143": "Analytics with Cloud Services in ECE", "CNT 4149": "Deep Learning in ECE",
               "CNT 4153": "Machine Learning in ECE", "CNT 4155": "Python Programming in ECE",
               "CAI 3864": "Data Engineering in ECE", "CAI 4863": "Generative AI Fundamentals in ECE",
               "CAI 4854": "Embedded AI", "MAC 1105": "College Algebra", "MAC 1114": "Trigonometry",
               "MAC 1147": "Pre-Calculus Algebra and Trigonometry", "PHY 2053": "Physics without Calculus I",
               "PHY 2054": "Physics without Calculus II"},
}
FIU_BME = {"code": "BIOMEG:MS", "name": "Biomedical Engineering", "degree": "M.S.", "credits": 30, "years": 1,
           "college": "College of Engineering and Computing", "official": True, "graduate": True,
           "source": "FIU program sheet BIOMEG:MS (catalog 2026-08-01)",
           "summary": "Research or Professional track. Professional track: 27 credits of coursework plus a 3-credit industry "
                      "project, in life sciences, math, BME core, professional development and electives.",
           "admission": ["Bachelor's in engineering, physical/life sciences, computer science or math",
                         "B average in upper-level undergraduate work", "Graduate GPA of 3.0 to stay in good standing"],
           "careers": ["biomedical-engineer"]}
FIU_CIVIL = {"code": "CIVLEG:PHD", "name": "Civil Engineering", "degree": "Ph.D.", "credits": 75, "years": 5,
             "college": "College of Engineering and Computing", "official": True, "graduate": True,
             "source": "FIU program sheet CIVLEG:PHD (catalog 2026-08-01)",
             "summary": "75 credits beyond the bachelor's: 54 of coursework (3+ in math/statistics, 18+ in the major area) "
                        "and 15 of dissertation. Up to 30 credits transfer in with a civil or environmental M.S.",
             "admission": ["M.S. in civil or environmental engineering with a 3.3 GPA (others reviewed case by case)",
                           "Three recommendation letters, a statement naming the research area, and a resume",
                           "A professor must agree to supervise the dissertation within 15 months"],
             "areas": ["Structural, geotechnical and construction", "Environmental and water resources", "Transportation"],
             "careers": ["civil-engineer"]}

# UM: real course numbers and titles from the bulletin; the B.S. structure and the MDC equivalencies are modeled.
UM_CS = {"code": "UM-BS-CS", "name": "Computer Science", "degree": "B.S.", "credits": 120, "years": 4,
         "college": "College of Arts and Sciences", "official": False, "synthetic": True,
         "source": "Course numbers and titles from the UM Academic Bulletin (CSC). Degree structure is modeled, not UM's official plan.",
         "requirements": [
             {"group": "Programming sequence", "courses": [["CSC 120"], ["CSC 220"]]},
             {"group": "Systems and theory core", "courses": [["CSC 314"], ["CSC 317"], ["CSC 322"], ["CSC 419", "CSC 427"]]},
             {"group": "Upper-division core", "courses": [["CSC 421"], ["CSC 423"], ["CSC 424"], ["CSC 431"]]},
             {"group": "AI and electives", "courses": [["CSC 345"], ["CSC 329", "CSC 330"]]},
             {"group": "Senior project", "courses": [["CSC 410"], ["CSC 411"]]},
         ]}
UM_MD = {"code": "UM-MD", "name": "Doctor of Medicine (Miller School of Medicine)", "degree": "M.D.", "credits": None, "years": 4,
         "college": "Leonard M. Miller School of Medicine", "official": False, "graduate": True,
         "source": "Clerkship and elective names from the UM Academic Bulletin (MDR). Admission steps are the typical U.S. M.D. path.",
         "summary": "Four years after a bachelor's: two of medical science, then clinical clerkships and electives "
                    "(for example Public Health Clerkship, Pediatric Mobile Clinic, Med-Peds), then residency.",
         "admission": ["Any bachelor's degree with pre-med science courses (biology, general and organic chemistry, physics with labs)",
                       "MCAT exam", "Clinical, volunteer and research experience"],
         "careers": ["physician"]}
# modeled equivalencies MDC -> UM (UM evaluates every course itself)
UM_EQUIV = {"COP 1047C": "CSC 115", "CAI 1001C": "CSC 145", "PHI 2680": "CSC 110", "COP 2800": "CSC 120",
            "COP 3530": "CSC 317", "CAI 4505C": "CSC 345", "CGS 1060C": "CSC 118", "CTS 1120": "CSC 116",
            "CAP 1788": "CSC 113"}

FL_CS_PREREQS = {"group": "Florida common prerequisites for computer science (check cpm.flvc.org)", "official": False,
                 "courses": [["MAC 2311"], ["MAC 2312"], ["PHY 2048"], ["PHY 2049"], ["COP 1047C", "COP 2800"]]}

UNIVERSITIES = [
    {"id": "fiu", "name": "Florida International University", "short": "FIU", "type": "florida_public", "typeIndex": 0,
     "rate": 205.57, "rateOutOfState": 660.19, "rateGraduate": 455.64,
     "tuitionNote": "Undergraduate tuition and fees per credit for Florida residents ($660.19 out of state).",
     "tuitionSource": "https://costcalculator.fiu.edu/", "url": "https://www.fiu.edu",
     "transferNotes": ["Same course number as MDC = same course (Florida Statewide Course Numbering System).",
                       "Connect4Success: MDC associate graduates get guaranteed admission pathways to FIU."],
     "programs": [FIU_IOTAI, FIU_BME, FIU_CIVIL]},
    {"id": "um", "name": "University of Miami", "short": "UM", "type": "private", "typeIndex": 1,
     "rate": round(66312 / 30, 2), "rateOutOfState": None,
     "tuitionNote": "$66,312 a year flat tuition for 12-20 credits a term (2026-27), about $2,210 a credit at 30 credits a year.",
     "tuitionSource": "https://admissions.miami.edu/undergraduate/financial-aid/cost-of-attendance/index.html",
     "url": "https://www.miami.edu",
     "transferNotes": ["Private: UM evaluates each course; equivalencies shown here are estimates.",
                       "Courses use 3-digit numbers (e.g. CSC 120), so nothing matches MDC numbers automatically."],
     "equivalencies": UM_EQUIV, "programs": [UM_CS, UM_MD]},
    {"id": "ucf", "name": "University of Central Florida", "short": "UCF", "type": "florida_public", "typeIndex": 0,
     "rate": 212.28, "rateOutOfState": 891.07,
     "tuitionNote": "Undergraduate tuition and fees for 1 credit hour, 2026-27 ($891.07 out of state).",
     "tuitionSource": "https://studentaccounts.ucf.edu/tf-tuitionratescurrent/", "url": "https://www.ucf.edu",
     "transferNotes": ["Same course number as MDC = same course (Florida Statewide Course Numbering System).",
                       "DirectConnect to UCF guarantees admission for Florida College System associate graduates."],
     "programs": [{"code": "UCF-BS-CS", "name": "Computer Science", "degree": "B.S.", "credits": 120, "years": 4,
                   "official": False, "synthetic": True, "requirements": [FL_CS_PREREQS],
                   "source": "Requirements modeled on Florida's common prerequisites; confirm in UCF's catalog."}]},
    {"id": "usf", "name": "University of South Florida", "short": "USF", "type": "florida_public", "typeIndex": 0,
     "rate": round(5960 / 30, 2), "rateOutOfState": round(18846 / 30, 2),
     "tuitionNote": "$5,960 a year for a full-time Florida resident (2026-27), about $199 a credit at 30 credits a year.",
     "tuitionSource": "https://www.stpetersburg.usf.edu/about/at-a-glance.aspx", "url": "https://www.usf.edu",
     "transferNotes": ["Same course number as MDC = same course (Florida Statewide Course Numbering System)."],
     "programs": [{"code": "USF-BS-CS", "name": "Computer Science", "degree": "B.S.", "credits": 120, "years": 4,
                   "official": False, "synthetic": True, "requirements": [FL_CS_PREREQS],
                   "source": "Requirements modeled on Florida's common prerequisites; confirm in USF's catalog."}]},
]

MDC_RATES = {"lowerDivision": 118.22, "upperDivision": 186.08, "lowerOutOfState": 402.51, "upperOutOfState": 1002.90,
             "source": "https://nwsa.mdc.edu/apply/college/tuition/", "year": "2025-26"}


def main():
    courses = [course(*c) for c in COURSES]
    by_code = {c["code"]: c for c in courses}
    for p in PROGRAMS:
        total = 0
        for g in p["requirement_groups"]:
            for code in g["courses"]:
                assert code in by_code, f"{p['id']}: {code} missing from COURSES"
                by_code[code]["used_by_programs"].append(p["id"])
            if g["rule"] == "all":
                got = sum(by_code[c]["credits"] for c in g["courses"])
                assert got == g["credits"], f"{p['id']} {g['group']}: {got} != {g['credits']}"
            else:
                assert sum(by_code[c]["credits"] for c in g["courses"]) >= g["credits"], f"{g['group']} pool too small"
            total += g["credits"]
        assert total == p["total_credits"], f"{p['id']} groups add to {total}"
    for c in courses:
        c["used_by_programs"] = sorted(set(c["used_by_programs"]))
    note = "REAL MDC program data (official program sheets, Spring 2026). terms_offered is assumed; see build_real_catalog.py."
    (HERE / "courses.json").write_text(json.dumps({"note": note, "courses": courses}, indent=1), encoding="utf-8")
    (HERE / "programs.json").write_text(json.dumps({"note": note, "programs": PROGRAMS}, indent=1), encoding="utf-8")
    (HERE / "universities.json").write_text(json.dumps(
        {"note": "Tuition from each school's official 2026-27 page. Program sheets for FIU are official; UM structure and "
                 "equivalencies, and UCF/USF requirement lists, are modeled and marked synthetic.",
         "mdcRates": MDC_RATES, "universities": UNIVERSITIES}, indent=1), encoding="utf-8")
    print(f"{len(courses)} courses, {len(PROGRAMS)} programs, {len(UNIVERSITIES)} universities")


if __name__ == "__main__":
    main()
