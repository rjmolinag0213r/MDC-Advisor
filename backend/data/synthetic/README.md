# Synthetic course catalog

**This is fake data for development and testing. It is not Miami Dade
College's catalog.** Every course code starts with `Z` (for example
`ZAI 3200`) so it can't be mistaken for a real Florida course number, and
all instructors are fictional. Don't load it into the advisor for real
students.

| File | Contents |
|---|---|
| `programs.json` | 6 programs (120 credits each) split into requirement groups: General Education (36), Common Technology Core (24), Program Foundations, Program Core, Capstone and Internship, Electives (choose 18 credits) |
| `courses.json` | 142 courses with credits, prerequisites, corequisites, terms offered, credit minimums, and which programs use them |
| `sections.json` | 604 individual classes across Fall 2026, Spring 2027, and Summer 2027 (sessions A, B, and full), with days, times, rooms, instructors, seats, and waitlists |

`app_program_code` in `programs.json` matches the codes in
`eval/personas.json` (`AI`, `DATA`, `CYBER`, `SWE`, `NET`, `ECE`).

## Prerequisite format

`prerequisites` is a list of groups. A student must satisfy every group, and
any one course in a group satisfies that group.

```json
"prerequisites": [["ZAI 2050", "ZDA 3100"], ["ZAI 3100", "ZDA 3150"]]
```

This means (ZAI 2050 or ZDA 3100) and (ZAI 3100 or ZDA 3150). A minimum
grade of C applies to all of them. Some courses also have
`min_credits_completed` or `instructor_permission`.

## Built-in edge cases

`courses.json` lists these under `edge_cases`, and the affected sections
carry `test_tags`:

- **Planning cases:** cross-listed courses, alternative prerequisites, a lecture plus lab corequisite with linked sections, courses offered in one term only, capstones that require 90 credits, and internships that require permission.
- **Catalog cases:** electives whose prerequisites fall outside the program (listed per program), one inactive course, and one course no program requires.
- **Schedule cases:** two required Applied AI courses whose only Spring sections overlap, a required course with every Fall section full, a cancelled section, instructor-TBA sections, and asynchronous online, evening, and weekend sections.

## Regenerating

```
python data/synthetic/generate_catalog.py
pytest tests/test_catalog.py
```

The seed is fixed, so the output is the same every run. To add or change
courses, edit the generator rather than the JSON. The tests check codes,
credit totals, prerequisite cycles, double-booked instructors and rooms,
lab pairing, and that every documented edge case still exists.
