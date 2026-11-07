"""
Generates a SYNTHETIC course catalog and class schedule for development and
testing of the MDC Career Path Advisor.

THIS IS NOT MIAMI DADE COLLEGE'S CATALOG. Every course code starts with "Z"
(e.g. ZAI 3200) so it can never be confused with a real Florida course
number. Instructors are fictional. Do not show this data to real students.

Outputs (next to this script):
  programs.json  - 6 degree programs and their requirement groups
  courses.json   - every course: credits, prerequisites, corequisites, terms offered
  sections.json  - individual classes (sections) for Fall 2026, Spring 2027, Summer 2027

Run:  python data/synthetic/generate_catalog.py
Same seed -> same output, so diffs stay clean.
"""
import json
import random
from pathlib import Path

SEED = 2026
OUT = Path(__file__).resolve().parent
NOTE = "SYNTHETIC DATA for development and testing. Not Miami Dade College's catalog."

F, S, U = "Fall", "Spring", "Summer"
ALL_TERMS = [F, S, U]
FS = [F, S]

courses = {}


def course(code, title, credits, category, prereqs=None, coreqs=None, terms=None,
           min_credits=None, permission=False, status="active", cross_listed=None, description=None):
    assert code not in courses, code
    level = "lower" if code.split()[1][0] in "12" else "upper"
    courses[code] = {
        "code": code,
        "title": title,
        "credits": credits,
        "level": level,
        "category": category,
        "prefix": code.split()[0],
        "description": description or f"{title}. Synthetic placeholder description.",
        "prerequisites": prereqs or [],          # list of groups; ANY course in a group satisfies it, ALL groups required
        "corequisites": coreqs or [],
        "min_grade": "C",
        "min_credits_completed": min_credits,
        "instructor_permission": permission,
        "terms_offered": terms or (ALL_TERMS if level == "lower" else FS),
        "cross_listed_as": cross_listed or [],
        "status": status,
        "synthetic": True,
    }
    return code


def req(*codes):
    """Each argument is one course (required) or a tuple of alternatives."""
    return [list(c) if isinstance(c, tuple) else [c] for c in codes]


# ---------------- General education (36 credits, all programs) ----------------
GEN_ED = [
    course("ZEN 1101", "Composition I", 3, "gen_ed"),
    course("ZEN 1102", "Composition II", 3, "gen_ed", req("ZEN 1101")),
    course("ZMA 1105", "College Algebra", 3, "gen_ed"),
    course("ZST 2023", "Statistical Methods", 3, "gen_ed", req("ZMA 1105")),
    course("ZAH 2020", "American History and Civic Literacy", 3, "gen_ed"),
    course("ZHU 1020", "Humanities and Culture", 3, "gen_ed"),
    course("ZSC 1005", "Environmental Science", 3, "gen_ed"),
    course("ZSP 2600", "Public Speaking", 3, "gen_ed"),
    course("ZPS 2012", "General Psychology", 3, "gen_ed"),
    course("ZEC 2013", "Principles of Economics", 3, "gen_ed"),
    course("ZPH 2048", "General Physics I", 3, "gen_ed", req("ZMA 1105")),
    course("ZAR 1000", "Art and Visual Culture", 3, "gen_ed"),
]
course("ZMA 1140", "Precalculus", 3, "support", req("ZMA 1105"),
       description="Precalculus. Optional preparation course; not required by any program.")

# ---------------- Common technology core (24 credits, all programs) ----------------
COMMON = [
    course("ZCP 1000", "Introduction to Programming", 3, "common_core"),
    course("ZCP 2006", "Object-Oriented Programming", 3, "common_core", req("ZCP 1000")),
    course("ZCS 1100", "Computer Systems Concepts", 3, "common_core"),
    course("ZNT 1110", "Networking Fundamentals", 3, "common_core", req("ZCS 1100")),
    course("ZDB 2300", "Database Fundamentals", 3, "common_core", req("ZCP 1000")),
    course("ZMA 2100", "Discrete Mathematics", 3, "common_core", req("ZMA 1105")),
    course("ZMA 2311", "Calculus I", 3, "common_core", req(("ZMA 1105", "ZMA 1140"))),
    course("ZCY 1300", "Cybersecurity Fundamentals", 3, "common_core", req("ZCS 1100")),
]

# ---------------- Program courses ----------------
PROGRAMS = {}


def program(pid, app_code, name, lower, core, capstone, internship, electives, elective_credits=18):
    PROGRAMS[pid] = {"id": pid, "app_program_code": app_code, "name": name,
                     "lower": lower, "core": core, "capstone": [capstone, internship],
                     "electives": electives, "elective_credits": elective_credits}


def cap(prefix, name, prereqs):
    return course(f"{prefix} 4950", f"{name} Capstone Project", 3, "capstone", prereqs, min_credits=90)


def intern(prefix, name):
    return course(f"{prefix} 4940", f"{name} Internship", 3, "internship", min_credits=60,
                  permission=True, terms=[U, F])


# Applied AI
program("SYN-AI", "AI", "Applied Artificial Intelligence",
    [course("ZAI 1010", "Foundations of Artificial Intelligence", 3, "program_core", req("ZCP 1000")),
     course("ZAI 2050", "Python for AI", 3, "program_core", req("ZCP 1000"))],
    [course("ZAI 3100", "Linear Algebra for Machine Learning", 3, "program_core", req("ZMA 2311")),
     course("ZAI 3150", "Probability for AI", 3, "program_core", req("ZST 2023")),
     course("ZAI 3200", "Machine Learning Foundations", 3, "program_core",
            req(("ZAI 2050", "ZDA 3100"), ("ZAI 3100", "ZDA 3150")), cross_listed=["ZDA 3200"]),
     course("ZAI 3300", "Deep Learning", 3, "program_core", req("ZAI 3200")),
     course("ZAI 3400", "Natural Language Processing", 3, "program_core", req("ZAI 3300")),
     course("ZAI 3500", "Computer Vision", 3, "program_core", req("ZAI 3300"), terms=[F]),
     course("ZAI 4100", "Reinforcement Learning", 3, "program_core", req("ZAI 3200", "ZAI 3150"), terms=[S]),
     course("ZAI 4200", "AI Ethics and Policy", 3, "program_core", req("ZAI 1010")),
     course("ZAI 4300", "MLOps and Model Deployment", 3, "program_core", req("ZAI 3200", "ZDB 2300")),
     course("ZAI 4400", "Generative AI Systems", 3, "program_core", req("ZAI 3300"))],
    cap("ZAI", "Applied AI", req("ZAI 3300", "ZAI 4300")), intern("ZAI", "Applied AI"),
    [course("ZAI 4510", "Speech Recognition", 3, "elective", req("ZAI 3400"), terms=[S]),
     course("ZAI 4520", "Robotics and Perception", 3, "elective", req("ZAI 3500"), terms=[S]),
     course("ZAI 4530", "Recommender Systems", 3, "elective", req("ZAI 3200"), terms=[F]),
     course("ZAI 4540", "AI for Healthcare", 3, "elective", req("ZAI 3200"), terms=[S]),
     course("ZAI 4550", "Time Series Forecasting", 3, "elective", req("ZAI 3200"), terms=[F]),
     course("ZAI 4560", "Edge AI", 3, "elective", req("ZAI 3300"), terms=[S]),
     "ZDA 3600", "ZCY 4510"])

# Data Analytics
program("SYN-DATA", "DATA", "Data Analytics",
    [course("ZDA 1010", "Introduction to Data Analytics", 3, "program_core", req("ZCP 1000")),
     course("ZDA 2100", "Spreadsheet Modeling", 3, "program_core", req("ZMA 1105"))],
    [course("ZDA 3100", "Data Wrangling with Python", 3, "program_core", req("ZDA 1010")),
     course("ZDA 3150", "Applied Regression", 3, "program_core", req("ZST 2023")),
     "ZAI 3200",
     course("ZDA 3300", "Data Visualization", 3, "program_core", req("ZDA 3100")),
     course("ZDA 3400", "Advanced SQL and Data Warehousing", 3, "program_core", req("ZDB 2300")),
     course("ZDA 3500", "Business Intelligence", 3, "program_core", req("ZDA 3300")),
     course("ZDA 3600", "Big Data Technologies", 3, "program_core", req("ZDA 3400"), terms=[S]),
     course("ZDA 4100", "Experimental Design and A/B Testing", 3, "program_core", req("ZDA 3150")),
     course("ZDA 4200", "Data Ethics and Privacy", 3, "program_core", req("ZDA 1010")),
     course("ZDA 4300", "Predictive Analytics", 3, "program_core", req("ZAI 3200", "ZDA 3150"))],
    cap("ZDA", "Data Analytics", req("ZDA 3500", "ZDA 4300")), intern("ZDA", "Data Analytics"),
    [course("ZDA 4510", "Sports Analytics", 3, "elective", req("ZDA 3150"), terms=[F]),
     course("ZDA 4520", "Marketing Analytics", 3, "elective", req("ZDA 3300"), terms=[S]),
     course("ZDA 4530", "Financial Data Analysis", 3, "elective", req("ZDA 3150"), terms=[F]),
     course("ZDA 4540", "Healthcare Analytics", 3, "elective", req("ZDA 3300"), terms=[S]),
     course("ZDA 4550", "Geospatial Analytics", 3, "elective", req("ZDA 3300"), terms=[S]),
     course("ZDA 4560", "Text Analytics", 3, "elective", req("ZDA 3100"), terms=[F]),
     "ZAI 4550", "ZAI 4530"])

# Cybersecurity
program("SYN-CYBER", "CYBER", "Cybersecurity",
    [course("ZCY 1400", "Operating Systems Security", 3, "program_core", req("ZCS 1100")),
     course("ZCY 2200", "Linux Administration", 3, "program_core", req("ZCS 1100"))],
    [course("ZCY 3100", "Network Security", 3, "program_core", req("ZNT 1110", "ZCY 1300")),
     course("ZCY 3200", "Cryptography", 3, "program_core", req("ZMA 2100")),
     course("ZCY 3300", "Ethical Hacking", 3, "program_core", req("ZCY 3100")),
     course("ZCY 3400", "Digital Forensics", 3, "program_core", req("ZCY 1400")),
     course("ZCY 3500", "Security Operations and Incident Response", 3, "program_core", req("ZCY 3100")),
     course("ZCY 3600", "Secure Software Development", 3, "program_core", req("ZCP 2006")),
     course("ZCY 4100", "Cloud Security", 3, "program_core", req("ZCY 3100")),
     course("ZCY 4200", "Governance, Risk and Compliance", 3, "program_core", req("ZCY 1300")),
     course("ZCY 4300", "Penetration Testing", 3, "program_core", req("ZCY 3300"), terms=[S]),
     course("ZCY 4400", "Malware Analysis", 3, "program_core", req("ZCY 3400", "ZCP 2006"), terms=[F])],
    cap("ZCY", "Cybersecurity", req("ZCY 3500", "ZCY 4300")), intern("ZCY", "Cybersecurity"),
    [course("ZCY 4510", "AI in Cybersecurity", 3, "elective", req("ZCY 3100", ("ZAI 3200", "ZST 2023")), terms=[S]),
     course("ZCY 4520", "Wireless Security", 3, "elective", req("ZCY 3100"), terms=[F]),
     course("ZCY 4530", "Industrial Control Systems Security", 3, "elective", req("ZCY 3100"), terms=[S]),
     course("ZCY 4540", "Threat Intelligence", 3, "elective", req("ZCY 3500"), terms=[F]),
     course("ZCY 4550", "Mobile Device Security", 3, "elective", req("ZCY 1400"), terms=[S]),
     course("ZCY 4560", "Cyber Law and Ethics", 3, "elective", req("ZCY 4200"), terms=[F]),
     "ZNT 3500", "ZAI 4200"])

# Software Engineering
program("SYN-SWE", "SWE", "Software Engineering",
    [course("ZSE 1500", "Web Development Fundamentals", 3, "program_core", req("ZCP 1000")),
     course("ZSE 2400", "Data Structures", 3, "program_core", req("ZCP 2006"))],
    [course("ZSE 3100", "Algorithms", 3, "program_core", req("ZSE 2400", "ZMA 2100")),
     course("ZSE 3200", "Software Engineering Principles", 3, "program_core", req("ZCP 2006")),
     course("ZSE 3300", "Full-Stack Web Development", 3, "program_core", req("ZSE 1500", "ZDB 2300")),
     course("ZSE 3400", "Mobile App Development", 3, "program_core", req("ZCP 2006")),
     course("ZSE 3500", "Software Testing and Quality", 3, "program_core", req("ZSE 3200")),
     course("ZSE 3600", "Operating Systems", 3, "program_core", req("ZSE 2400", "ZCS 1100")),
     course("ZSE 4100", "Software Architecture", 3, "program_core", req("ZSE 3200")),
     course("ZSE 4200", "DevOps and CI/CD", 3, "program_core", req("ZSE 3200")),
     course("ZSE 4300", "Human-Computer Interaction", 3, "program_core", req("ZSE 1500")),
     course("ZSE 4400", "Cloud-Native Applications", 3, "program_core", req("ZSE 3300"))],
    cap("ZSE", "Software Engineering", req("ZSE 4100", "ZSE 3500")), intern("ZSE", "Software Engineering"),
    [course("ZSE 4510", "Game Development", 3, "elective", req("ZSE 2400"), terms=[F]),
     course("ZSE 4520", "Compilers", 3, "elective", req("ZSE 3100"), terms=[S]),
     course("ZSE 4530", "Distributed Systems", 3, "elective", req("ZSE 3600"), terms=[S]),
     course("ZSE 4540", "Open Source Development", 3, "elective", req("ZSE 3200"), terms=[F]),
     course("ZSE 4550", "Embedded Software", 3, "elective", req("ZSE 3600"), terms=[F]),
     course("ZSE 4560", "UX Prototyping", 3, "elective", req("ZSE 4300"), terms=[S]),
     "ZAI 2050", "ZCY 3600"])

# Networking
program("SYN-NET", "NET", "Networking",
    [course("ZNT 1200", "Network Cabling and Infrastructure", 3, "program_core"),
     course("ZNT 2100", "Routing and Switching I", 3, "program_core", req("ZNT 1110"))],
    [course("ZNT 3100", "Routing and Switching II", 3, "program_core", req("ZNT 2100")),
     course("ZNT 3200", "Network Operating Systems", 3, "program_core", req("ZCS 1100")),
     course("ZNT 3300", "Wireless Networking", 3, "program_core", req("ZNT 2100")),
     course("ZNT 3400", "Cloud Infrastructure", 3, "program_core", req("ZNT 2100")),
     course("ZNT 3500", "Network Automation", 3, "program_core", req("ZNT 2100", "ZCP 1000")),
     course("ZNT 3600", "Virtualization and Data Centers", 3, "program_core", req("ZNT 3200")),
     course("ZNT 4100", "Enterprise Network Design", 3, "program_core", req("ZNT 3100")),
     course("ZNT 4200", "Network Security Operations", 3, "program_core", req("ZNT 3100", "ZCY 1300")),
     course("ZNT 4300", "Voice and Unified Communications", 3, "program_core", req("ZNT 3100"), terms=[S]),
     course("ZNT 4400", "Network Troubleshooting", 3, "program_core", req("ZNT 3100"))],
    cap("ZNT", "Networking", req("ZNT 4100", "ZNT 4400")), intern("ZNT", "Networking"),
    [course("ZNT 4510", "Software-Defined Networking", 3, "elective", req("ZNT 3100"), terms=[F]),
     course("ZNT 4520", "IPv6 Deployment", 3, "elective", req("ZNT 3100"), terms=[S]),
     course("ZNT 4530", "Network Monitoring and Analytics", 3, "elective", req("ZNT 3100"), terms=[F]),
     course("ZNT 4540", "Internet of Things Networks", 3, "elective", req("ZNT 3300"), terms=[S]),
     course("ZNT 4550", "Satellite and Undersea Communications", 3, "elective", req("ZNT 3100"), terms=[F]),
     course("ZNT 4560", "Service Provider Networks", 3, "elective", req("ZNT 4100"), terms=[S]),
     "ZCY 4100", "ZCY 4520"])

# Electrical & Computer Engineering (lab + seminar make the odd credit counts add up)
program("SYN-ECE", "ECE", "Electrical & Computer Engineering",
    [course("ZEE 1000", "Introduction to Engineering", 3, "program_core", req("ZMA 1105")),
     course("ZEE 2100", "Circuit Analysis I", 3, "program_core", req("ZMA 2311", "ZPH 2048"), coreqs=["ZEE 2100L"]),
     course("ZEE 2100L", "Circuit Analysis I Lab", 1, "lab", coreqs=["ZEE 2100"])],
    [course("ZEE 3010", "Engineering Seminar", 2, "program_core", req("ZEE 1000")),
     course("ZEE 3100", "Circuit Analysis II", 3, "program_core", req("ZEE 2100")),
     course("ZEE 3200", "Digital Logic Design", 3, "program_core", req("ZEE 1000")),
     course("ZEE 3300", "Electronics I", 3, "program_core", req("ZEE 3100")),
     course("ZEE 3400", "Signals and Systems", 3, "program_core", req("ZEE 3100", "ZMA 2311")),
     course("ZEE 3500", "Microcontrollers and Embedded Systems", 3, "program_core", req("ZEE 3200", "ZCP 1000")),
     course("ZEE 3600", "Computer Architecture", 3, "program_core", req("ZEE 3200")),
     course("ZEE 4100", "Control Systems", 3, "program_core", req("ZEE 3400"), terms=[S]),
     course("ZEE 4200", "Power Systems", 3, "program_core", req("ZEE 3100"), terms=[F]),
     course("ZEE 4300", "PCB Design and Fabrication", 3, "program_core", req("ZEE 3300"))],
    cap("ZEE", "Electrical & Computer Engineering", req("ZEE 3500", "ZEE 4300")),
    intern("ZEE", "Electrical & Computer Engineering"),
    [course("ZEE 4510", "Robotics Engineering", 3, "elective", req("ZEE 3500"), terms=[S]),
     course("ZEE 4520", "VLSI Design", 3, "elective", req("ZEE 3600"), terms=[F]),
     course("ZEE 4530", "Renewable Energy Systems", 3, "elective", req("ZEE 4200"), terms=[S]),
     course("ZEE 4540", "Communication Systems", 3, "elective", req("ZEE 3400"), terms=[F]),
     course("ZEE 4550", "Electronics II", 3, "elective", req("ZEE 3300"), terms=[S]),
     course("ZEE 4560", "Sensors and Instrumentation", 3, "elective", req("ZEE 3300"), terms=[F]),
     "ZAI 4520", "ZSE 4550"])

course("ZEE 4570", "Vacuum Tube Electronics", 3, "elective", req("ZEE 3300"), terms=[], status="inactive",
       description="Vacuum Tube Electronics. Inactive course kept for testing; no sections are scheduled.")

# ---------------- programs.json ----------------
programs_out = []
for p in PROGRAMS.values():
    groups = [
        {"group": "General Education", "rule": "all", "courses": GEN_ED},
        {"group": "Common Technology Core", "rule": "all", "courses": COMMON},
        {"group": "Program Foundations", "rule": "all", "courses": p["lower"]},
        {"group": "Program Core", "rule": "all", "courses": p["core"]},
        {"group": "Capstone and Internship", "rule": "all", "courses": p["capstone"]},
        {"group": "Electives", "rule": "choose_credits", "credits": p["elective_credits"], "courses": p["electives"]},
    ]
    for g in groups:
        if g["rule"] == "all":
            g["credits"] = sum(courses[c]["credits"] for c in g["courses"])
    required = {c for g in groups if g["rule"] == "all" for c in g["courses"]}
    outside = {}
    for c in p["electives"]:
        missing = [grp for grp in courses[c]["prerequisites"] if not set(grp) & required]
        if missing:
            outside[c] = missing
    groups[-1]["electives_with_outside_prerequisites"] = outside
    programs_out.append({
        "id": p["id"], "app_program_code": p["app_program_code"], "name": p["name"],
        "degree": "Bachelor of Science (synthetic)", "total_credits": sum(g["credits"] for g in groups),
        "min_gpa": 2.0, "min_grade_in_major": "C", "requirement_groups": groups, "synthetic": True,
    })

for pr in programs_out:
    for g in pr["requirement_groups"]:
        for c in g["courses"]:
            courses[c].setdefault("used_by_programs", [])
            if pr["id"] not in courses[c]["used_by_programs"]:
                courses[c]["used_by_programs"].append(pr["id"])
for c in courses.values():
    c.setdefault("used_by_programs", [])

# ---------------- sections.json ----------------
rng = random.Random(SEED)

TERMS = [
    {"term": "Fall 2026", "type": F, "sessions": {"full": ("2026-08-24", "2026-12-12")}},
    {"term": "Spring 2027", "type": S, "sessions": {"full": ("2027-01-06", "2027-05-01")}},
    {"term": "Summer 2027", "type": U, "sessions": {"A": ("2027-05-10", "2027-06-18"),
                                                    "B": ("2027-06-21", "2027-07-30"),
                                                    "full": ("2027-05-10", "2027-07-30")}},
]
CAMPUSES = ["North", "Kendall", "Wolfson", "Hialeah", "Homestead", "West", "Padron"]
UPPER_CAMPUS = "North"  # upper-division tech courses meet at one campus, plus online
REG_SLOTS = [("MWF", "08:00", "08:50"), ("MWF", "09:00", "09:50"), ("MWF", "10:00", "10:50"),
             ("MWF", "11:00", "11:50"), ("MWF", "12:00", "12:50"),
             ("TR", "08:00", "09:15"), ("TR", "09:30", "10:45"), ("TR", "11:00", "12:15"),
             ("TR", "12:30", "13:45"), ("TR", "14:00", "15:15"),
             ("MW", "09:30", "10:45"), ("MW", "13:00", "14:15"), ("MW", "14:30", "15:45")]
EVENING_SLOTS = [("M", "18:00", "20:40"), ("T", "18:00", "20:40"), ("W", "18:00", "20:40"), ("R", "18:00", "20:40")]
SAT_SLOTS = [("S", "09:00", "11:45")]
HYBRID_SLOTS = [("T", "11:00", "12:15"), ("R", "11:00", "12:15"), ("M", "13:00", "14:15"), ("W", "13:00", "14:15")]
SUMMER_SLOTS = [("MTWR", "08:00", "09:50"), ("MTWR", "10:00", "11:50"), ("MTWR", "12:00", "13:50"),
                ("MTWR", "18:00", "19:50")]
LAB_SLOTS = [("F", "13:00", "15:45"), ("W", "16:00", "18:45"), ("R", "16:00", "18:45")]

FIRST = ["Adriana", "Benjamin", "Carmen", "Daniel", "Elena", "Felipe", "Gloria", "Hector", "Irene", "James",
         "Karina", "Leonard", "Marisol", "Nathan", "Olga", "Pablo", "Rosa", "Stephen", "Teresa", "Victor",
         "Wanda", "Xavier", "Yolanda", "Zachary", "Alicia", "Bernard", "Celeste", "Dmitri", "Esther", "Frank"]
LAST = ["Abernathy", "Barrientos", "Castellanos", "Dunmore", "Echeverri", "Fairweather", "Galvan", "Holloway",
        "Ibarra", "Jarrell", "Kowalczyk", "Lindqvist", "Maldonado", "Northcott", "Oyelaran", "Penaloza",
        "Quintanilla", "Ravensworth", "Saldivar", "Thornbury", "Urquhart", "Valcourt", "Whitlock", "Yarbrough"]
names = [f"{f} {l}" for f in FIRST for l in LAST]
rng.shuffle(names)
prefixes = sorted({c["prefix"] for c in courses.values()})
instructors = {}
for pfx in prefixes:
    n = 6 if pfx in {"ZEN", "ZMA", "ZCP"} else 4
    instructors[pfx] = [names.pop() for _ in range(n)]


def to_min(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def overlaps(a, b):
    """a, b: (days, start, end, session)."""
    if a[3] != b[3] and "full" not in (a[3], b[3]):
        return False
    return bool(set(a[0]) & set(b[0])) and to_min(a[1]) < to_min(b[2]) and to_min(b[1]) < to_min(a[2])


busy_instr, busy_room = {}, {}


def free(table, key, slot):
    return all(not overlaps(slot, s) for s in table.get(key, []))


def room_for(campus, term_name, slot):
    bldg = {"North": 4, "Kendall": 2, "Wolfson": 1, "Hialeah": 3, "Homestead": 5, "West": 6, "Padron": 7}[campus]
    for _ in range(200):
        room = f"{campus} Bldg {bldg}, Rm {bldg}{rng.randint(1, 3)}{rng.randint(1, 30):02d}"
        if free(busy_room, (term_name, room), slot):
            return room
    raise RuntimeError("no free room")


crn_counter = iter(rng.sample(range(10000, 99999), 5000))
sections = []


def add_section(code, term, session, modality, slot, campus, instructor, capacity, tags=()):
    c = courses[code]
    start, end = term["sessions"][session]
    meetings = []
    if slot:
        days, t0, t1 = slot
        loc = room_for(campus, term["term"], (days, t0, t1, session)) if modality != "online" else None
        meetings.append({"days": days, "start": t0, "end": t1, "location": loc})
        if instructor:
            busy_instr.setdefault((term["term"], instructor), []).append((days, t0, t1, session))
        if loc:
            busy_room.setdefault((term["term"], loc), []).append((days, t0, t1, session))
    sec = {
        "crn": next(crn_counter), "course_code": code, "title": c["title"], "credits": c["credits"],
        "term": term["term"], "session": session, "start_date": start, "end_date": end,
        "section_number": None, "campus": campus if modality != "online" else "Online",
        "modality": modality, "meetings": meetings, "instructor": instructor,
        "capacity": capacity, "enrolled": 0, "waitlist": 0, "status": "open",
        "linked_crn": None, "test_tags": list(tags), "synthetic": True,
    }
    sections.append(sec)
    return sec


def pick_slot(term, session, pool, instructor, campus, modality):
    candidates = pool[:]
    rng.shuffle(candidates)
    for days, t0, t1 in candidates:
        slot = (days, t0, t1, session)
        if instructor and not free(busy_instr, (term["term"], instructor), slot):
            continue
        return (days, t0, t1)
    return None


def plan_count(c, ttype):
    cat = c["category"]
    if cat == "gen_ed":
        return rng.randint(2, 4) if ttype == U else rng.randint(6, 9)
    if cat == "common_core":
        return 2 if ttype == U else rng.randint(3, 5)
    if cat in ("program_core", "lab") and c["level"] == "lower":
        return 1 if ttype == U else rng.randint(2, 3)
    if cat == "internship":
        return 1
    if cat == "support":
        return 1 if ttype == U else 2
    return rng.randint(1, 2) if c["category"] in ("program_core", "capstone") else 1


FORCED_SINGLE = {("Spring 2027", "ZAI 3300"), ("Spring 2027", "ZAI 4200")}  # conflict pair, see below
LAB_PAIRS = []

for term in TERMS:
    ttype = term["type"]
    for code, c in courses.items():
        if c["status"] != "active" or ttype not in c["terms_offered"] or c["category"] == "lab":
            continue
        n = 1 if (term["term"], code) in FORCED_SINGLE else plan_count(c, ttype)
        for i in range(n):
            if c["category"] == "internship":
                add_section(code, term, "full", "online", None, "Online", rng.choice(instructors[c["prefix"]]), 15,
                            tags=["arranged_hours", "permission_required"])
                continue
            if ttype == U:
                session = rng.choice(["A", "B"])
                modality = rng.choice(["in_person", "online", "online"])
                pool = SUMMER_SLOTS
            else:
                session = "full"
                r = rng.random()
                modality = "online" if r < 0.22 else "hybrid" if r < 0.32 else "in_person"
                pool = HYBRID_SLOTS if modality == "hybrid" else (
                    REG_SLOTS + EVENING_SLOTS + (SAT_SLOTS if c["level"] == "lower" else []))
            campus = rng.choice(CAMPUSES) if c["level"] == "lower" else UPPER_CAMPUS
            instr = rng.choice(instructors[c["prefix"]])
            if modality == "online" and rng.random() < 0.8:
                slot = None  # asynchronous
            else:
                slot = pick_slot(term, session, pool, instr, campus, modality)
                if slot is None:
                    instr = None
                    slot = pick_slot(term, session, pool, None, campus, modality)
            cap_ = 25 if c["level"] == "upper" else rng.choice([30, 32, 35])
            if modality == "online":
                cap_ += 5
            sec = add_section(code, term, session, modality, slot, campus, instr, cap_)
            if modality == "online" and slot is None:
                sec["test_tags"].append("asynchronous")
            if slot and slot[1] >= "18:00":
                sec["test_tags"].append("evening")
            if slot and slot[0] == "S":
                sec["test_tags"].append("weekend")
            if code == "ZEE 2100":
                LAB_PAIRS.append(sec)

# Lab sections, each linked to one lecture section (corequisite pairing)
for lec in LAB_PAIRS:
    term = next(t for t in TERMS if t["term"] == lec["term"])
    instr = lec["instructor"]
    slot = None
    for days, t0, t1 in rng.sample(LAB_SLOTS, len(LAB_SLOTS)):
        cand = (days, t0, t1, lec["session"])
        if all(not overlaps(cand, (m["days"], m["start"], m["end"], lec["session"])) for m in lec["meetings"]) and \
                (not instr or free(busy_instr, (term["term"], instr), cand)):
            slot = (days, t0, t1)
            break
    campus = lec["campus"] if lec["campus"] != "Online" else UPPER_CAMPUS
    lab = add_section("ZEE 2100L", term, lec["session"], "in_person", slot, campus, instr, 20, tags=["lab"])
    lab["linked_crn"], lec["linked_crn"] = lec["crn"], lab["crn"]
    lec["test_tags"].append("has_linked_lab")

# ---------------- deliberate edge cases ----------------

def only(term, code):
    found = [s for s in sections if s["term"] == term and s["course_code"] == code]
    assert len(found) == 1, (term, code, len(found))
    return found[0]


# 1. Two required AI courses whose only Spring sections overlap (schedule-conflict test).
def unbook(sec):
    for table in (busy_instr, busy_room):
        for k in list(table):
            if k[0] != sec["term"]:
                continue
            if (table is busy_instr and k[1] != sec["instructor"]) or \
               (table is busy_room and k[1] not in {m["location"] for m in sec["meetings"]}):
                continue
            table[k] = [x for x in table[k] if not any((m["days"], m["start"], m["end"]) == x[:3] for m in sec["meetings"])]


def rebook(sec, days, t0, t1):
    slot = (days, t0, t1, sec["session"])
    sec["instructor"] = next(i for i in instructors["ZAI"] if free(busy_instr, (sec["term"], i), slot))
    loc = room_for(UPPER_CAMPUS, sec["term"], slot)
    sec["meetings"] = [{"days": days, "start": t0, "end": t1, "location": loc}]
    busy_instr.setdefault((sec["term"], sec["instructor"]), []).append(slot)
    busy_room.setdefault((sec["term"], loc), []).append(slot)
    sec["modality"], sec["campus"] = "in_person", UPPER_CAMPUS
    sec["test_tags"] = [t for t in sec["test_tags"] if t not in ("asynchronous", "evening")] + ["time_conflict_pair"]


dl, eth = only("Spring 2027", "ZAI 3300"), only("Spring 2027", "ZAI 4200")
for sec in (dl, eth):
    unbook(sec)
rebook(dl, "TR", "11:00", "12:15")
rebook(eth, "TR", "11:30", "12:45")

# Enrollment for everything
for s in sections:
    lo = 0.5 if s["course_code"].split()[1][0] in "34" else 0.65
    s["enrolled"] = min(s["capacity"], int(s["capacity"] * rng.uniform(lo, 1.08)))
    if s["enrolled"] >= s["capacity"]:
        s["status"] = "closed"
        s["waitlist"] = rng.randint(0, 8)
        if s["waitlist"]:
            s["test_tags"].append("waitlisted")

# 2. A cancelled section.
canc = next(s for s in sections if s["course_code"] == "ZHU 1020" and s["term"] == "Spring 2027")
canc.update(status="cancelled", enrolled=0, waitlist=0, instructor=None, meetings=[])
canc["test_tags"].append("cancelled")

# 3. A few instructor-TBA sections in Spring.
for s in [s for s in sections if s["term"] == "Spring 2027" and s["course_code"] in ("ZEN 1101", "ZCP 1000")][:3]:
    s["instructor"] = None
for s in sections:
    if s["instructor"] is None and "cancelled" not in s["test_tags"]:
        s["test_tags"].append("instructor_tba")

# 4. A required course that is completely full in Fall 2026 (every section closed).
for s in sections:
    if s["term"] == "Fall 2026" and s["course_code"] == "ZSE 2400":
        s["enrolled"], s["status"], s["waitlist"] = s["capacity"], "closed", rng.randint(3, 10)
        s["test_tags"] = [t for t in s["test_tags"] if t != "waitlisted"] + ["waitlisted", "all_sections_full"]

# Section numbers per course+term
counts = {}
for s in sections:
    k = (s["term"], s["course_code"])
    counts[k] = counts.get(k, 0) + 1
    s["section_number"] = f"{counts[k]:03d}"
    s["test_tags"] = sorted(set(s["test_tags"]))

sections.sort(key=lambda s: ([t["term"] for t in TERMS].index(s["term"]), s["course_code"], s["section_number"]))

# Courses that are in a program but have no section in a given term (useful for "not offered" answers)
EDGE_NOTES = {
    "hidden_prerequisite": "Some electives borrowed from other programs need prerequisites the program does not require "
                           "(e.g. ZDA 3600 for Applied AI needs ZDA 3400). Each program's Electives group lists them "
                           "under electives_with_outside_prerequisites.",
    "cross_listed": "ZAI 3200 (also listed as ZDA 3200) is required by both Applied AI and Data Analytics.",
    "alternative_prerequisites": "ZMA 2311 accepts ZMA 1105 or ZMA 1140; ZAI 3200 accepts either AI or Data Analytics prerequisites.",
    "corequisite_lab": "ZEE 2100 and ZEE 2100L must be taken together; lab sections carry linked_crn.",
    "single_term_courses": "Many electives and some core courses (e.g. ZEE 4200 Fall only, ZAI 4100 Spring only) run in one term.",
    "credit_minimums": "Capstones need 90 completed credits; internships need 60 and instructor permission.",
    "inactive_course": "ZEE 4570 is inactive and never scheduled.",
    "unused_course": "ZMA 1140 is not required by any program.",
    "time_conflict_pair": "In Spring 2027, the only sections of ZAI 3300 and ZAI 4200 overlap on TR.",
    "all_sections_full": "Every Fall 2026 section of ZSE 2400 is closed with a waitlist.",
    "cancelled": "One Spring 2027 ZHU 1020 section is cancelled.",
}

meta = {"note": NOTE, "seed": SEED, "generated_by": "data/synthetic/generate_catalog.py"}
(OUT / "programs.json").write_text(json.dumps({**meta, "programs": programs_out}, indent=2) + "\n", encoding="utf-8")
(OUT / "courses.json").write_text(json.dumps({**meta, "edge_cases": EDGE_NOTES,
                                              "courses": sorted(courses.values(), key=lambda c: c["code"])},
                                             indent=2) + "\n", encoding="utf-8")
(OUT / "sections.json").write_text(json.dumps({**meta, "terms": [
    {"term": t["term"], "sessions": {k: {"start": v[0], "end": v[1]} for k, v in t["sessions"].items()}} for t in TERMS],
    "sections": sections}, indent=2) + "\n", encoding="utf-8")

print(f"programs: {len(programs_out)}  courses: {len(courses)}  sections: {len(sections)}")
for p in programs_out:
    print(f"  {p['id']:<10} {p['total_credits']} credits")
