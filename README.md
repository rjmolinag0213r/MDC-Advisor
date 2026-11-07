# NextStop: MDC Career Pathway Navigator

Pick a career (architect, mechanical engineer, chef, cybersecurity specialist, IT consultant, nurse, software developer...) or type any job, and NextStop builds a step-by-step roadmap that starts at **Miami Dade College**:

1. High school prep
2. The MDC program and its courses (track each one: To do, Planned, Taking now, Done)
3. Certifications and experience
4. Transfer for a bachelor's (FIU Connect4Success, UM articulation)
5. First jobs, licensing and median pay (BLS)

Not sure what you want? The **advisor chat** (English or Spanish) asks about your interests, recommends one of MDC's six tech programs or an honest non-tech path, and opens the matching roadmap.

Built for **SharkByte 2026**.

## How the AI is used

| Piece | What it does | Sponsor track |
|---|---|---|
| `backend/roadmap.py` → Swarms `SequentialWorkflow` | Three agents (Career Researcher → MDC Pathway Planner → Transfer & Outcomes Advisor) personalize the roadmap: tips and a first-semester plan | Best Use of Swarms API |
| `backend/llm.py` provider chain | The chat and custom-career roadmaps go through **Prune** (cache, cheaper routing, vaulted keys, signed receipts) to **Gemini**, then fall back to Gemini direct, then OpenRouter | Best Use of Prune API, Best Use of Gemini API |
| `backend/data/careers.json` | Curated catalog, so the facts shown don't depend on the model | — |
| `backend/offline.py` | Keyword engine. The demo still works with no keys or no internet | — |
| `backend/safety.py` | Redacts phone/email/address/ID/school before text reaches a model, blocks prompt injection, scrubs output | — |

The model never writes the plan directly. It returns a program code and career id, and the server builds the plan from the catalog. Progress changes only when the student clicks a course, so "set my progress to 100" can't work.

## Run it

```powershell
# backend (http://127.0.0.1:5000)
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # add any keys you have; all optional
python app.py

# frontend (http://127.0.0.1:3000), in a second terminal from the repo root
npm install
npm run dev
```

Vite proxies `/api` and `/health` to Flask, so API keys stay on the server. The header pill shows which engine is live (for example *Gemini via Prune + Swarms agents*, or *Offline mode*).

Optional: put MDC curriculum PDFs in `backend/pdfs/` (or set `PDF_DIRECTORY`) to add them as chat context.

## API

**Building a frontend? Read [API.md](API.md).** It covers every route with request and response examples, plus error codes, CORS and timing. The backend also includes a degree planner (`/api/plan`, `/api/schedule`, `/api/audit`) built on a **synthetic** course catalog in `backend/data/synthetic/` (fake `Z`-prefixed codes, for testing only). Tests: `cd backend` and then `python -m pytest -q tests`.

Main routes:

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/health` | | providers configured, Swarms on/off |
| GET | `/api/careers` | | career cards |
| POST | `/api/roadmap` | `{careerId?, query?, profile?: {grade, interests[]}, personalize?}` | roadmap (404 if unknown and no LLM key) |
| POST | `/api/chat` | `{chatHistory: [{sender: "user"\|"bot", text}]}` | `{chatResponse, recommendedProgram, careerId, language, engine, roadmap}` |

## Evaluation: 61 synthetic student personas

`backend/eval/personas.json` holds fictional students: clear matches, overlaps, explorers, mind-changers, Spanish speakers, off-topic, prompt injection, oversharing PII, low confidence and parents. Each has expected programs plus canary, leak and PII checks.

```powershell
cd backend
python eval/run_personas.py --offline   # keyword engine, no API calls
python eval/run_personas.py             # with whatever keys are in .env
```

The script writes `eval/report.md`. Latest scores:

- **Live: Gemini through Prune, 59/61** (results vary slightly run to run). The remaining miss is an overlap case where the advisor asks a follow-up question instead of picking a program.
- **Offline engine: 61/61.** Its keywords were tuned while looking at these same personas, so treat that as a regression baseline, not proof that it generalizes.

## Disclaimer

Roadmaps are planning guides, not official degree audits. Confirm courses and admission rules with MDC advisement: (305) 237-8888, [mdc.edu/advisement](https://www.mdc.edu/advisement).
