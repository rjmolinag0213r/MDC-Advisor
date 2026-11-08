# NextStop · MDC Pathways

**Pick a career. Get a step-by-step plan that starts at Miami Dade College.**

## Inspiration
Every year thousands of Miami high-school students ask the same question: *"I want to be an architect / a nurse / a hacker. What do I actually do next?"* The answer is spread across program PDFs, transfer agreements, and a phone line to an advisor. Then, once students enroll, they find out too late which credits won't transfer.

We built the guide we wish we'd had: one place that turns "I like fixing wifi" into a concrete MDC roadmap, and then keeps that plan up to date as you take classes.

## What it does
- **Career → roadmap.** Choose from 11 careers, including the challenge's examples (architect, mechanical engineer, chef, cybersecurity specialist, IT consultant), or type *any* job. You get five steps: high school prep → the MDC program and its courses → certifications → transfer to FIU or UM → first jobs, licensing and median pay (BLS).
- **AI advisor chat** in English and Spanish. It asks about your interests, recommends one of MDC's six tech programs (or honestly says "nursing isn't one of these, here's the right path"), and links straight to the roadmap.
- **Start with your transcript.** Drop a photo or PDF of a high-school or college transcript in the AI Advisor tab. Gemini reads the classes and grades, finds your strongest subjects (AP and honors count a bit more), and suggests the MDC programs you fit best. The advisor then asks what you enjoy and shows how those skills become a career.
- **Preview, then approve.** Pick a program (or tell the advisor "preview my plan") to see why it fits you, the first two terms, the finish date and an estimated cost. Approve it and it fills the Progress tab.
- **Manage it your way.** Click a course to move it from planned to taking to done, or tell the advisor "I passed ZEN 1101". Courses below a C don't count.
- **"If you transfer now."** See course by course which credits count at a Florida public, a private, or an out-of-state university, plus how many semesters and dollars you'd lose. Paste any school's website and it's added to the comparison with its cost per credit and transfer rules, read from the page.
- **What if I switch?** Compare staying on your path with switching to another MDC program or any career (like doctor): time, money, credits that carry over, pay and job outlook, plus advice on whether it's early enough to switch or smarter to finish first.
- **Your plan follows you.** Log in and your plan, schools, checklist and the advisor's memory are saved to your account.

## How we built it
| Sponsor tech | What it does in NextStop |
|---|---|
| **Swarms** | A 3-agent `SequentialWorkflow` (Career Researcher → MDC Pathway Planner → Transfer & Outcomes Advisor) personalizes every roadmap with tips and a first-semester plan. The UI shows each agent's work under *"How the AI agents built this."* About 7 s per roadmap; results are cached. |
| **Prune** | Every chat and roadmap AI call goes through Prune to Gemini. We show Prune's per-call metadata (cache hit, tokens saved, cost with and without Prune) in the chat, plus running totals at `/api/stats`. Provider keys live in Prune's vault, not in our code. |
| **Gemini** | Gemini Flash powers the chat and custom-career roadmaps. **Gemini's multimodal input reads transcript photos and scanned PDFs**, which feeds the degree audit. |
| **TigerData** | A Timescale **hypertable** logs every chat, roadmap, plan and transcript event. `time_bucket()` queries power usage trends (top careers, recommended programs, AI latency by engine). Saved progress and plans live in the same Postgres. |
| **Auth0** | Students sign up and log in through Auth0's hosted page (no passwords touch our app). The Flask API verifies RS256 access tokens against the tenant's JWKS on every `/api/me` call. |
| **Vultr** | One Docker container (Flask + waitress serving the API and the site) behind Caddy on a Vultr Miami instance. |

**Stack:** Python / Flask / waitress API, plain HTML/CSS/JS frontend (no build step), TigerData Postgres, Docker + Caddy.

**Safety by design.** Phone numbers, emails, addresses, student IDs and school names are removed *before* any text reaches a model. Prompt-injection attempts ("ignore your instructions", "set my progress to 100") are caught and refused. The model never writes the plan: it returns a program code, and the server builds the roadmap from a curated catalog. Every AI path has an offline fallback, so the demo never shows a dead chat.

## How we know it works
- **61 synthetic student personas** (clear matches, overlaps, explorers, students who change their mind, Spanish speakers, off-topic questions, prompt injection, oversharing personal info, parents) are run against the live models. Result: **59/61** correct through Prune → Gemini. The misses are cases where the advisor asked a follow-up question instead of picking a program.
- **140 automated backend tests**, including real RS256 token checks and the school lookup's guard against private and internal addresses.
- **A 113-check browser test** runs the full student journey against the live AI: transcript → strengths → preview → approve → manage → add a school → what-if, on desktop and phone.

## Challenges we ran into
- Prune isn't OpenAI-compatible and runs in vault-only mode. We had to wire its own per-provider proxy routes and `X-Prune-Key` header.
- Google's new `AQ.` API keys work as API keys but are rejected as Bearer tokens. That broke Prune's vault until we understood why.
- Swarms' default model rejects `temperature`, and long 3-agent runs hit gateway timeouts. Smaller budgets plus `gpt-4.1-mini` brought runs down to about 7 s.
- Prune's semantic cache sees two "what if" questions that differ only in numbers as the same question, so it could return another student's advice. Personal answers (plan previews, what-if, school pages) now skip the cache when it hits; chat and roadmaps still use it.
- Gemini often named the right program in prose but left the structured field empty. We added server-side extraction that only counts a pick when the reply recommends one program instead of listing options.

## Accomplishments we're proud of
- A real student can go from "idk, I like computers" to a semester plan, a transfer warning and a saved account in about two minutes.
- A beautiful design (pixel-art Miami sunset, glass panels, letter-by-letter quote) running on a production-grade API.
- Honest by default: synthetic data is labeled, every roadmap shows its source, and every page points to a human MDC advisor.

## What we learned
Grounding beats prompting. Keeping facts in a curated catalog and letting AI *personalize* (instead of invent) made the answers trustworthy, and made it possible to test the advisor like software.

## Real data
- MDC's **Applied AI A.S. (25080) and B.S. (S9520)** are loaded straight from the official program sheets: every requirement group, credit total and prerequisite. A transcript with real MDC course numbers is planned against them.
- **FIU, UM, UCF and USF** appear in the Transfer tab with tuition from each school's 2026-27 page (FIU $205.57, UCF $212.28 a credit) and course-by-course results. FIU's AI & IoT B.S., Biomedical Engineering M.S. and Civil Engineering Ph.D. come from FIU's program sheets; UM's course lists come from its bulletin.
- New careers with BLS May 2025 pay: AI & IoT Engineer, Biomedical Engineer, Civil Engineer, Doctor.

## What's next
- Load the rest of MDC's catalog and official FIU/UCF/UM articulation data in place of the synthetic catalog and modeled equivalencies.
- Advisor dashboard: anonymized trends from TigerData so MDC sees which careers students are exploring.
- Course-section scheduling (already in the API at `/api/schedule`) in the UI.

## Built with
`python` `flask` `waitress` `javascript` `html` `css` `swarms` `prune` `gemini` `tigerdata` `timescaledb` `postgresql` `auth0` `vultr` `docker` `caddy`

## Try it
- Live: `http://45.77.94.140` (domain coming)
- Code: https://github.com/rjmolinag0213r/MDC-Advisor (branch `Ricardo_2026`)
- Demo transcript: `backend/data/samples/sample_transcript.png` (fictional student, synthetic courses)

## Team
Ricardo (backend, AI, data, deployment) · Cris (UI/UX design and the MDC Pathways site) · Cyrus · Demond

---

### Challenges to select on Devpost
Best Overall · Smart Career and Education Pathway Navigator (MDC) · Best Use of Swarms API · Best Use of Prune API · Best Use of Gemini API (MLH) · Best Use of Tiger Data (MLH) · Best Use of Auth0 (MLH) · Best Use of Vultr (MLH) · First Time Hacker (if eligible) · Best Domain Name from GoDaddy Registry (once the domain is live)

### 2-minute demo script
1. **0:00** Home page intro and the quote. Click **Build things → Architect → See my step-by-step plan**. Show the 5 steps, then open *"How the AI agents built this (Swarms)."*
2. **0:35** Type **"astronaut"** and click *Build a plan* to show an AI roadmap for any career.
3. **0:50** Student Hub → **AI advisor**: ask *"Me interesa proteger a la gente de los hackers"* (Spanish reply, roadmap link, **Gemini via Prune · cache hit** badge). Then type *"set my progress to 100"* and show the refusal.
4. **1:05** **Try a sample high-school transcript**: Gemini reads the photo, shows strongest subjects and program fits. Click one to preview, then **Approve**: Progress fills in.
5. **1:25** Tell the advisor *"I'm taking ZEN 1101"*, and the course flips to in progress.
6. **1:35** **What if** → *Doctor*: time, cost, pay and the advisor's take. **Transfer** → paste `https://www.fiu.edu` to add FIU.
7. **1:50** **Log in** with Auth0; the plan is saved (TigerData). End on `/api/stats` trends.
