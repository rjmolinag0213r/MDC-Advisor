# 🦈 NextStop: MDC Career Pathway Navigator

A full-stack academic and career advisor for Miami Dade College students. Drop in a transcript and **Finn**, the advisor shark, finds your strongest subjects, suggests MDC programs, builds a term-by-term plan you approve, and shows how your credits would transfer to FIU, UM, UCF or USF.

Built for **SharkByte 2026** by the NextStop team.

## 🌟 Features

- **Transcript-first plan.** Drop a high-school or college transcript (photo or PDF). Gemini reads the classes and grades, finds your strongest subjects (AP and honors count a bit more) and suggests the programs that fit. Grades below C don't count.
- **Preview, approve, lock.** Preview a plan (why it fits you, first two terms, finish date, cost), then approve it. The approved plan is locked; other programs appear as "possible paths" ranked by how many of your credits would carry over.
- **Finn, the AI advisor.** A pixel-art shark with moods (listening, thinking, speaking, celebrating) and animated thinking orbs during each AI step. Finn knows your record, remembers past chats when you're logged in, answers in English or Spanish, and handles small talk without going off the rails.
- **Manage your plan.** Click a course to move it from planned to taking to done, or tell Finn "I passed ENC 1101".
- **Real MDC programs.** Applied Artificial Intelligence **A.S. (25080)** and **B.S. (S9520)** loaded from MDC's official program sheets: every requirement group, credit total and prerequisite.
- **Transfer comparison.** FIU, UM, UCF and USF course by course, with tuition from each school's 2026-27 page. Paste any school's website to add it (cost per credit and transfer notes read from the page).
- **What if I switch?** Compare staying with switching to another program or any career (for example doctor): years, cost, credits that carry over, median pay and job outlook, plus advice on whether it's early enough to switch.
- **Career explorer.** 15 careers with step-by-step roadmaps (high school prep → MDC → certifications → transfer → jobs and BLS pay), or type any job for an AI-built roadmap.
- **Accounts.** Auth0 login. Plans, checklist, schools and Finn's memory are saved per student in TigerData. A "sample student" mode lets anyone explore without an account.

## 🏗️ Architecture

| Layer | Technology |
|---|---|
| Website | Plain HTML, CSS and JavaScript (`mdc-pathways/`, design by Cris), no build step, served by Flask at `/` |
| Backend | Python Flask API, served by waitress |
| AI chat and roadmaps | **Gemini** (`gemini-flash-lite-latest`) through the **Prune** gateway, falling back to Gemini direct, then OpenRouter |
| Transcript reading | Gemini multimodal (images and scanned PDFs); text PDFs are parsed locally with pypdf |
| Roadmap agents | **Swarms** `SequentialWorkflow`: Career Researcher → MDC Pathway Planner → Transfer & Outcomes Advisor |
| Database | **TigerData** (Postgres + TimescaleDB hypertable for usage events); local SQLite when no `DATABASE_URL` |
| Login | **Auth0** hosted login; the API verifies RS256 tokens against the tenant's JWKS |
| Hosting | Docker + Caddy on **Vultr** (`deploy/`) |
| Mascot and orbs | Finn: our pixel shark with CSS moods, inspired by [wobnimo](https://github.com/Pouryaak/wobnimo). Orbs: [thinking-orbs](https://github.com/Jakubantalik/thinking-orbs) engine (MIT, vendored) |

**Safety by design.** Phone numbers, emails, addresses, student IDs, school names and self-introduced names are removed before text reaches a model. Prompt-injection attempts are refused. The model never writes the plan: it returns a program code and the server builds the plan from the catalog. Every AI feature has a no-AI fallback.

## 📋 Prerequisites

- **Python 3.10 or higher** (tested on 3.13) and pip
- Optional API keys (the app runs without any of them, on the offline engine): Prune, Gemini, Swarms, OpenRouter, a TigerData service, an Auth0 tenant
- Node.js is **not** needed for the website

## 🚀 Quick Start

### 1. Set up the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```powershell
copy .env.example .env                # macOS/Linux: cp .env.example .env
```

Fill in whatever keys you have (see [Configuration](#-configuration)). Every key is optional. `backend/.env` is gitignored: never commit it.

### 3. Start the server

```powershell
python app.py
```

You should see something like:

```
[store] TigerData/Postgres ready (timescaledb hypertable)      # or: SQLite
LLM providers: ['prune', 'gemini', 'openrouter'] | Swarms: True
NextStop API on http://127.0.0.1:5000 (waitress, 16 threads)
```

### 4. Open the app

Go to **http://127.0.0.1:5000**. The intro scrolls into the Student Hub. Log in, or choose **"Just looking? Explore with a sample student"** on the log-in page.

## 📁 Project Structure

```
MDC-Advisor/
├── backend/
│   ├── app.py               # Flask API + serves the website
│   ├── llm.py               # Prune → Gemini → OpenRouter chain, Gemini vision
│   ├── roadmap.py           # career roadmaps + Swarms agents
│   ├── planner.py           # degree audit, term plans, schedules, Student Hub data, transfer rules
│   ├── advisor_tools.py     # plan preview, school lookup by URL, what-if, possible paths
│   ├── transcript.py        # transcript reading + strengths → programs
│   ├── safety.py            # PII removal, prompt-injection guard, output scrubbing
│   ├── store.py             # TigerData/Postgres or SQLite: plans, progress, chat memory, events
│   ├── auth.py              # Auth0 token verification (demo mode without Auth0)
│   ├── offline.py           # keyword engine used when no AI key works
│   ├── data/
│   │   ├── careers.json     # curated career catalog (15 careers, BLS pay)
│   │   ├── real/            # MDC program sheets, FIU/UM/UCF/USF data (see its README)
│   │   ├── synthetic/       # sample catalog for other programs (Z-prefixed codes)
│   │   └── samples/         # sample transcripts (fictional students)
│   ├── eval/                # 61 synthetic student personas + scorer
│   ├── tests/               # pytest suite
│   ├── requirements.txt
│   └── .env.example
├── mdc-pathways/            # the website
│   ├── student-hub.html     # main page: AI Advisor, Progress, What if, Transfer
│   ├── explore.html         # career explorer
│   ├── login.html, account.html, index.html
│   ├── js/nextstop.js       # API + Auth0 client
│   ├── js/mascot.js         # Finn's moods + thinking orbs
│   ├── js/vendor/           # thinking-orbs engine (MIT)
│   └── images/              # artwork, Finn, favicon (+ the scripts that build them)
├── deploy/                  # Dockerfile setup, Caddy, Vultr script, Auth0 branding, SETUP.md
├── API.md                   # full API reference
├── DEVPOST.md               # hackathon write-up
└── App.tsx, components/ …   # earlier React UI, kept for reference (not served)
```

## 🔧 Configuration

Set these in `backend/.env` (all optional):

| Variable | What it does |
|---|---|
| `PRUNE_API_KEY` | Prune gateway key. Store your Gemini key in Prune's vault (Connect → Providers → Gemini) |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Gemini direct, also used for reading transcript images. Default model `gemini-flash-lite-latest` |
| `OPENROUTER_API_KEY` | Last-resort fallback |
| `LLM_PROVIDERS` | Order to try, default `prune,gemini,openrouter` |
| `SWARMS_API_KEY`, `SWARMS_MODEL` | Multi-agent roadmaps (`gpt-4.1-mini` recommended) |
| `DATABASE_URL` | TigerData service URL (keep `?sslmode=require`). Empty = local SQLite |
| `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `AUTH0_CLIENT_ID` | Auth0 login. Empty = demo mode |
| `HOST`, `PORT` | Default `127.0.0.1:5000` |
| `CORS_ORIGINS`, `RATE_LIMIT_PER_MIN` | For deployments |
| `PDF_DIRECTORY` | Optional folder of MDC curriculum PDFs added as chat context (default `backend/pdfs`) |

## 📚 Data

| Data | Source | Official? |
|---|---|---|
| Applied AI A.S. (25080) and B.S. (S9520) | MDC program sheets, effective Spring 2026 | ✅ Yes (class terms are estimated) |
| FIU AI & IoT B.S., Biomedical Eng. M.S., Civil Eng. Ph.D. | FIU program sheets, catalog 2026-08-01 | ✅ Yes |
| UM Computer Science and Medicine course lists | UM Academic Bulletin | ✅ Yes |
| Tuition: FIU $205.57, UCF $212.28, USF ≈ $199, UM ≈ $2,210 per credit; MDC $118.22 / $186.08 | Each school's 2026-27 page | ✅ Yes |
| UM degree structure and equivalencies, UCF/USF requirement lists | Modeled | ⚠️ Estimate, labeled in the UI |
| Data Analytics, Cybersecurity, Software Eng., Networking, ECE | Synthetic catalog (`Z` codes) | ❌ Sample data, labeled |
| Career pay | U.S. Bureau of Labor Statistics | ✅ Yes |

Details: `backend/data/real/README.md` and `backend/data/synthetic/README.md`.

## 🎯 How to Use

1. **Start in the AI Advisor tab.** Drop your transcript, or try one of the three sample transcripts (high school, sample college, real MDC course numbers).
2. **See your strengths** and the programs that fit. Tell Finn what you enjoy.
3. **Preview a plan** by clicking a program or typing "preview my plan", then **approve** it. Progress fills in and the plan locks.
4. **Keep it current:** click courses in Progress, or tell Finn:
   - "I passed ENC 1101"
   - "I'm taking CAI 2100C"
5. **Ask Finn anything:** "Am I on track?", "What should I take next term?", "What happens to my credits at a private school?"
6. **Transfer tab:** compare FIU, UM, UCF and USF, or paste a school's website.
7. **What if tab:** type a program or career ("Cybersecurity", "doctor") to compare.

## 🛠️ Development

```powershell
cd backend

# tests (153)
python -m pytest -q tests

# persona evaluation: 61 fictional students
python eval/run_personas.py --offline   # keyword engine, no API calls
python eval/run_personas.py             # with the keys in .env (latest: 59/61 via Prune → Gemini)

# rebuild data
python data/real/build_real_catalog.py  # MDC program sheets + universities
python data/real/add_careers.py         # careers from the real programs
python data/synthetic/generate_catalog.py
```

Image scripts (need Pillow): `mdc-pathways/images/make_favicon.py`, `mdc-pathways/images/make_shark.py`, and `backend/data/samples/make_sample_*.py`.

## 🔍 API Endpoints

Full reference with request and response examples: **[API.md](API.md)**.

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Status, configured AI providers |
| POST | `/api/chat` | Finn's reply: `{chatHistory: [{sender, text}], context?}` |
| POST | `/api/transcript` | Read a transcript file or pasted text → courses, strengths, suggested programs |
| POST | `/api/plan/preview` | Plan preview for a program before approval |
| POST | `/api/hub` | Everything the Student Hub shows for a record |
| POST | `/api/paths` | Possible paths close to the approved plan |
| POST | `/api/whatif` | Stay vs switch comparison |
| POST | `/api/schools/lookup` | Read a school's web page for cost per credit and transfer notes |
| GET | `/api/careers`, POST `/api/roadmap` | Career catalog and roadmaps |
| GET | `/api/programs`, POST `/api/plan`, `/api/audit`, `/api/schedule` | Degree planner |
| GET/PUT/DELETE | `/api/me…` | Signed-in student's plans, progress and chat memory |
| GET | `/api/stats` | Usage trends from TigerData and Prune savings |

Example:

```http
POST http://127.0.0.1:5000/api/chat
Content-Type: application/json

{ "chatHistory": [ { "sender": "user", "text": "I like math and video games, what fits me?" } ] }
```

## 🌐 Deployment

See **[deploy/SETUP.md](deploy/SETUP.md)**. On a Vultr server:

```powershell
powershell -ExecutionPolicy Bypass -File deploy\deploy-vultr.ps1 -Ip <server-ip> -Domain "<server-ip>.sslip.io"
```

Then add the site's address to the Auth0 application's allowed callback, logout and web-origin URLs.

## 🐛 Troubleshooting

**The server won't start**
- Check `python --version` (3.10+) and that the virtual environment is active.
- Run `pip install -r requirements.txt` again.

**Finn says "Offline mode" or gives simple answers**
- No AI key works. Check `backend/.env`. With Prune, the Gemini key must be in Prune's vault, not only in `.env`.
- `/health` lists the providers the server found.

**"Reading images needs the Gemini key"**
- Transcript photos need `GEMINI_API_KEY`. Text PDFs and pasted text work without it.

**Log in fails or loops**
- Add the exact site address (for example `http://127.0.0.1:5000/student-hub.html`) to the Auth0 app's allowed callback URLs, and the origin to allowed web origins.
- Without Auth0 settings, the app runs in demo mode.

**Plans aren't saved across devices**
- Without `DATABASE_URL` the app uses a local SQLite file. Set the TigerData URL to share data.

**A school's page can't be read**
- Use the school's public tuition or transfer page (`https://…`). Private, local and non-web addresses are refused on purpose.

## 📝 License

Built for educational use at SharkByte 2026. Course and tuition data belong to their institutions; confirm everything with an MDC advisor. Third-party code: thinking-orbs (MIT, © Jakub Antalik, license in `mdc-pathways/js/vendor/`).

## 🤝 Support

- MDC advisement: **(305) 237-8888**, [mdc.edu/advisement](https://www.mdc.edu/advisement)
- Issues: open one on this repository
- Check the server console and the browser console when something fails

## 🎓 About

NextStop helps Miami students go from "I like computers" to an approved MDC plan, a transfer school and a career, with an advisor that explains the trade-offs honestly. Roadmaps are planning guides, not official degree audits.

**Team:** Ricardo (backend, AI, data, deployment) · Cris (UI/UX design and the MDC Pathways site) · Cyrus · Demond
