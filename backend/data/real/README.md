# Real catalog layer

Loaded next to `data/synthetic` by `planner.catalog()`. Real courses keep their real numbers (no `Z` prefix), so the two never collide.

| File | What it is | Official? |
|---|---|---|
| `programs.json` | MDC Applied Artificial Intelligence **B.S. (S9520, 120 cr)** and **A.S. (25080, 60 cr)**, requirement groups exactly as on the Spring 2026 program sheets | Yes |
| `courses.json` | 71 MDC courses from those sheets: titles, credits, prerequisites | Yes, except `terms_offered` (assumed Fall/Spring/Summer, `terms_assumed: true`) |
| `universities.json` | FIU, UM, UCF, USF: tuition per credit, transfer notes, programs | Tuition: yes (each school's 2026-27 page, URL in `tuitionSource`). FIU IOTAI:BS, BIOMEG:MS, CIVLEG:PHD: yes. UM B.S. CS structure, UM equivalencies, UCF/USF requirement lists: **modeled** (`synthetic: true`) |
| `um_csc_courses.json`, `um_mdr_courses.json` | 108 UM Computer Science and 179 UM Medicine courses parsed from the UM Academic Bulletin | Yes (titles, credits, requisites) |

Transfer results (`planner.university_rule`):
- Florida public (FIU, UCF, USF): same course number = same course (Statewide Course Numbering). On the school's program sheet → counts; gen ed → counts; otherwise → elective.
- UM (private): modeled equivalency → counts; gen ed → counts; lower division → elective; upper division → not accepted.

MDC tuition: $118.22 lower division / $186.08 upper division per credit for Florida residents (nwsa.mdc.edu, 2025-26).

Rebuild: `python data/real/build_real_catalog.py` (asserts every group adds up to the sheet's credits), then `python data/real/add_careers.py`.
