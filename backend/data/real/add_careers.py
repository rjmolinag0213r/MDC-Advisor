"""Add careers backed by the real program sheets to data/careers.json (idempotent: replaces by id).

Median pay: U.S. Bureau of Labor Statistics, Occupational Outlook Handbook, May 2025.
Run: python data/real/add_careers.py
"""
import json
from pathlib import Path

PATH = Path(__file__).parents[1] / "careers.json"

NEW = [
    {"id": "iot-engineer", "title": "AI & IoT Engineer", "icon": "chip", "cluster": "Engineering",
     "tagline": "Put AI inside smart homes, cars, medical devices and cities.", "program": "AIBS",
     "keywords": ["iot", "internet of things", "smart devices", "embedded", "sensors", "arduino", "raspberry pi",
                  "smart home", "drones", "internet de las cosas"],
     "salary": {"median": 161740, "occupation": "Computer hardware engineers (closest BLS category), May 2025",
                "source": "https://www.bls.gov/ooh/architecture-and-engineering/computer-hardware-engineers.htm"},
     "highSchool": ["Pre-Calculus and Trigonometry", "Physics", "AP Computer Science Principles", "Build an Arduino or Raspberry Pi project"],
     "mdc": {"credential": "MDC Applied Artificial Intelligence A.S. (25080) or B.S. (S9520), official program sheets",
             "notes": "Take MAC 1114 or MAC 1147 early: FIU's AI & IoT degree requires it within three terms.",
             "courses": ["CAI 1001C Artificial Intelligence (AI) Thinking", "COP 1047C Introduction to Python Programming",
                         "CAI 2100C Machine Learning Foundations", "CAI 2840C Introduction to Computer Vision",
                         "CTS 1120 Cybersecurity Fundamentals", "MAC 1147 Pre-Calculus Algebra and Trigonometry",
                         "PHY 2053 / PHY 2054 Physics without Calculus 1 and 2", "ETS 1603C Introduction to Robotics"]},
     "certifications": ["Cisco IoT fundamentals (CCST)", "CompTIA Security+", "AWS Certified AI Practitioner"],
     "transfer": [{"name": "FIU", "program": "B.S. Applied AI & Internet of Things (IOTAI:BS, 120 credits)",
                   "note": "Same-number MDC courses transfer directly: MAC 1105, MAC 1114/1147, PHY 2053, PHY 2054 and CTS 1120 are on FIU's sheet."}],
     "career": ["IoT developer", "Embedded AI engineer", "Smart-city systems engineer", "IoT security analyst"],
     "license": None, "realData": True},
    {"id": "biomedical-engineer", "title": "Biomedical Engineer", "icon": "heart", "cluster": "Health Sciences",
     "tagline": "Design medical devices, implants and imaging tools that help patients.", "program": None,
     "keywords": ["biomedical", "medical devices", "prosthetics", "bioengineering", "implants", "ingeniero biomedico"],
     "salary": {"median": 109370, "occupation": "Bioengineers and biomedical engineers, May 2025",
                "source": "https://www.bls.gov/ooh/architecture-and-engineering/biomedical-engineers.htm"},
     "highSchool": ["Biology and Chemistry (AP if you can)", "Calculus", "Physics", "Science fair or robotics team"],
     "mdc": {"credential": "Associate in Arts (AA) on an engineering transfer track",
             "notes": "Engineering bachelor's first; FIU's M.S. in Biomedical Engineering accepts engineering, science, CS or math graduates.",
             "courses": ["MAC 2311 / MAC 2312 Calculus 1 and 2", "PHY 2048 / PHY 2049 Physics with Calculus",
                         "CHM 1045 General Chemistry", "BSC 2010 Principles of Biology", "COP 1047C Introduction to Python Programming"]},
     "certifications": ["Fundamentals of Engineering (FE) exam", "FDA regulatory affairs coursework (RAC) later in career"],
     "transfer": [{"name": "FIU", "program": "B.S. Biomedical Engineering, then M.S. Biomedical Engineering (BIOMEG:MS, 30 credits)",
                   "note": "Accelerated BS-to-MS pathway: 75 FIU credits and a 3.25 GPA."}],
     "career": ["Medical device engineer", "Quality and regulatory engineer (FDA)", "Biomedical R&D engineer", "Clinical engineer"],
     "license": None, "realData": True},
    {"id": "civil-engineer", "title": "Civil Engineer", "icon": "building", "cluster": "Engineering",
     "tagline": "Design the roads, bridges, water systems and buildings a city runs on.", "program": None,
     "keywords": ["civil engineering", "bridges", "roads", "construction", "infrastructure", "water", "ingeniero civil"],
     "salary": {"median": 100840, "occupation": "Civil engineers, May 2025",
                "source": "https://www.bls.gov/ooh/architecture-and-engineering/civil-engineers.htm"},
     "highSchool": ["Calculus", "Physics", "Drafting or CAD class", "Bridge-building or engineering club"],
     "mdc": {"credential": "Associate in Arts (AA) on an engineering transfer track",
             "notes": "Florida common prerequisites: Calculus 1-3, differential equations, Physics with Calculus 1-2, General Chemistry.",
             "courses": ["MAC 2311 / MAC 2312 Calculus 1 and 2", "PHY 2048 / PHY 2049 Physics with Calculus", "CHM 1045 General Chemistry",
                         "ENC 1101 English Composition 1"]},
     "certifications": ["Fundamentals of Engineering (FE) exam", "Professional Engineer (PE) license after 4 years of experience"],
     "transfer": [{"name": "FIU", "program": "B.S. Civil Engineering; research path: Ph.D. Civil Engineering (CIVLEG:PHD, 75 credits)",
                   "note": "Ph.D. areas: structural/geotechnical/construction, environmental and water, transportation."}],
     "career": ["Structural engineer", "Transportation engineer", "Water resources engineer", "Construction project engineer"],
     "license": "Florida PE license: accredited degree, FE exam, 4 years of experience, then the PE exam.", "realData": True},
    {"id": "physician", "title": "Doctor (Physician)", "icon": "heart", "cluster": "Health Sciences",
     "tagline": "Diagnose and treat patients, from the clinic to the operating room.", "program": None,
     "keywords": ["doctor", "physician", "medicine", "medical school", "pre-med", "premed", "surgeon", "medico", "doctora"],
     "salary": {"median": 275930, "occupation": "Physicians and surgeons, May 2025",
                "source": "https://www.bls.gov/ooh/healthcare/physicians-and-surgeons.htm"},
     "highSchool": ["AP Biology and AP Chemistry", "Calculus or Statistics", "Hospital or clinic volunteering", "Spanish or Haitian Creole helps in Miami"],
     "mdc": {"credential": "Associate in Arts (AA) with pre-med science courses",
             "notes": "About 11+ years after high school: bachelor's (4), medical school (4), residency (3-7).",
             "courses": ["BSC 2010 / BSC 2011 Principles of Biology", "CHM 1045 / CHM 1046 General Chemistry",
                         "CHM 2210 / CHM 2211 Organic Chemistry", "PHY 2053 / PHY 2054 Physics", "STA 2023 Statistical Methods",
                         "PSY 2012 Introduction to Psychology (on the MCAT)"]},
     "certifications": ["MCAT", "USMLE Steps 1-3 during and after medical school", "Board certification after residency"],
     "transfer": [{"name": "FIU", "program": "B.S. Biology or Biomedical Engineering, then the Herbert Wertheim College of Medicine (M.D.)", "note": "Keep a strong science GPA."},
                  {"name": "University of Miami", "program": "Bachelor's, then the Miller School of Medicine (M.D.)",
                   "note": "Clinical years include clerkships such as the Public Health Clerkship and the Pediatric Mobile Clinic."}],
     "career": ["Resident physician", "Family or pediatric doctor", "Surgeon", "Public health physician"],
     "license": "Florida medical license: M.D./D.O., USMLE or COMLEX exams, and at least one year of residency.", "realData": True},
]


def main():
    d = json.loads(PATH.read_text(encoding="utf-8"))
    ids = {c["id"] for c in NEW}
    d["careers"] = [c for c in d["careers"] if c["id"] not in ids] + NEW
    d["programs"]["AIBS"] = {"name": "Applied Artificial Intelligence B.S. (official sheet)", "code": "S9520"}
    d["programs"]["AIAS"] = {"name": "Applied Artificial Intelligence A.S. (official sheet)", "code": "25080"}
    PATH.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(len(d["careers"]), "careers")


if __name__ == "__main__":
    main()
