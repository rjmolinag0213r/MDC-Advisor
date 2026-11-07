# NextStop API (v1.0)

Base URL in development: `http://127.0.0.1:5000`. Start it with `cd backend` and then `.\.venv\Scripts\python app.py`.

- All requests and responses are JSON (`Content-Type: application/json`).
- **CORS:** any `localhost` or `127.0.0.1` port works with no setup (Vite 5173, CRA 3000, Next 3001...). For a deployed frontend, set `CORS_ORIGINS=https://your-site.example` in `backend/.env`.
- **Errors:** every error has the same shape, and the status code says what kind:
  ```json
  { "error": "invalid_request", "message": "chatHistory[0].text must be a string.", "field": "chatHistory[0].text", "requestId": "a1b2c3d4e5f6" }
  ```
  | Status | `error` | When |
  |---|---|---|
  | 400 | `invalid_request` / `invalid_json` | bad input; `field` names the culprit |
  | 404 | `not_found` / `career_not_found` / `course_not_found` / `program_not_found` | unknown id |
  | 405 | `method_not_allowed` | e.g. GET on a POST route |
  | 413 | `payload_too_large` | body over 64 KB |
  | 429 | `rate_limited` | over 40 AI calls per minute per IP; wait `retryAfter` seconds |
  | 500 | `internal_error` | bug; include `requestId` when you report it |
- Every response carries `X-Request-Id` and `X-Response-Time` headers.
- **Timing:** `/api/careers*`, `/api/programs*`, `/api/plan`, `/api/schedule` and `/api/audit` answer in milliseconds. `/api/chat` takes about 1 to 10 s. `/api/roadmap` with `personalize: true` takes about 8 s, because it runs the Swarms agents; repeat calls are cached and come back instantly. Show a loading state.
- **AI never blocks the app.** If Prune, Gemini or Swarms is down, the API falls back to the offline engine and the curated catalog. Read `engine.name` to see which one answered.

---

## Health

`GET /api/health` (alias: `/health`)
```json
{ "status": "ok", "version": "1.0", "llmProviders": ["prune","gemini","openrouter"], "swarms": true, "pdfContext": false, "careers": 11, "catalog": true }
```

## Careers and roadmaps (curated MDC data)

`GET /api/careers` returns the cards for a career picker:
```json
{ "careers": [ { "id": "chef", "title": "Chef", "icon": "chef", "cluster": "Hospitality & Culinary",
                 "tagline": "Run a kitchen...", "program": null, "salary": { "median": 58920, "occupation": "Chefs and head cooks" } } ],
  "disclaimer": "Roadmaps are planning guides..." }
```
`program` is one of `AI DATA CYBER SWE NET ECE` or `null` for non-tech careers. `icon` names: building, gear, chef, shield, briefcase, code, chart, spark, network, chip, heart, compass.

`GET /api/careers/{id}` returns the roadmap instantly, with no AI and no rate limit.

`POST /api/roadmap` returns a roadmap, personalized by AI unless you turn that off.
```json
{ "careerId": "chef",                       // or "query": "game designer" (fuzzy match, or AI-generated if unknown)
  "profile": { "grade": "11", "interests": ["cooking", "TikTok"] },   // optional; interests may also be "a, b"
  "personalize": true }                     // false = instant curated version
```
Response (a **Roadmap**):
```json
{ "careerId": "chef", "title": "Chef", "tagline": "...", "cluster": "Hospitality & Culinary",
  "program": null,                          // or { "key": "CYBER", "name": "Cybersecurity", "code": "S9515" }
  "salary": { "median": 58920, "occupation": "Chefs and head cooks" },
  "salarySource": { "label": "U.S. BLS ...", "url": "https://www.bls.gov/ooh/" },
  "stages": [
    { "id": "hs",       "title": "High school prep", "items": ["..."] },
    { "id": "mdc",      "title": "Start at Miami Dade College", "credential": "...", "notes": "...",
                        "courses": [ { "name": "Food safety and sanitation", "status": "planned" } ] },
    { "id": "certs",    "title": "Certifications & experience", "items": ["ServSafe ..."] },
    { "id": "transfer", "title": "Transfer for a bachelor's", "options": [ { "name": "FIU", "program": "...", "note": "..." } ] },
    { "id": "career",   "title": "Launch your career", "items": ["Line cook", "Sous chef"], "license": null }
  ],
  "personalTips": ["..."], "summary": "...",     // filled when AI personalized it
  "reviewed": true,                              // false = AI-generated career outside the catalog
  "disclaimer": "...",
  "engine": { "name": "swarms", "detail": "Swarms SequentialWorkflow, 3 agents", "seconds": 6.3 },  // swarms | llm | catalog
  "cached": true }                               // present when served from cache
```
Course `status` is one of `pending planned in-progress completed`. The frontend owns progress: store the student's clicks yourself (for example in localStorage).

## Advisor chat

`POST /api/chat`
```json
{ "chatHistory": [
    { "sender": "user", "text": "I fix the wifi at home" },
    { "sender": "bot",  "text": "Nice! What do you enjoy most about it?" },
    { "sender": "user", "text": "Figuring out why things won't connect" } ] }
```
- Send the **whole conversation** each time, ending with the user's new message. The server keeps the last 50 turns.
- `sender` is `user` or `bot`; `role: "model"/"assistant"` also works. Each `text` can be up to 2000 characters.

Response:
```json
{ "chatResponse": "Sounds like Networking is a great fit...",
  "recommendedProgram": "NET",              // AI DATA CYBER SWE NET ECE | "OTHER" (non-tech goal) | null (still exploring)
  "careerId": "network-engineer",           // open this roadmap; null while exploring
  "language": "en",                         // "es" when the student writes in Spanish
  "engine": { "name": "llm", "detail": "prune/gemini-flash-lite-latest" },   // llm | offline | guard
  "roadmap": { ...Roadmap or null... },
  "careerPlan": { ... } }                   // legacy shape, ignore
```
Built-in safety: phone numbers, emails, addresses, IDs and school names are removed before any AI sees them. Prompt-injection attempts get `engine.name: "guard"` and a polite refusal.

## Degree planner (SYNTHETIC catalog)

> ⚠️ This data is fake, generated for testing. Course codes start with `Z` (e.g. `ZAI 3200`). Every response has `"synthetic": true`, so show a "sample data" label in the UI.

| Route | What it does |
|---|---|
| `GET /api/terms` | Fall 2026, Spring 2027, Summer 2027 (sessions A/B/full) |
| `GET /api/programs` | 6 programs (`AI DATA CYBER SWE NET ECE`), 120 credits each |
| `GET /api/programs/{code}` | requirement groups with full course info |
| `GET /api/courses/{code}?term=Fall 2026` | course plus its sections. Codes are forgiving: `zai3200` works, and so does the cross-listed `ZDA 3200` |
| `POST /api/audit` | `{ "program": "AI", "completed": ["ZEN 1101", ...] }` returns credits earned and what's left in each group |
| `POST /api/plan` | semester-by-semester plan to graduation |
| `POST /api/schedule` | picks conflict-free sections for one term |

`POST /api/plan`
```json
{ "program": "AI", "completed": ["ZEN 1101"], "startTerm": "Fall 2026", "maxCredits": 15, "summerCredits": 6, "includeSummer": true }
```
The response has `terms: [{ term, credits, courses: [{ code, title, credits, notes? }] }]`, plus `graduationTerm`, `creditsAtGraduation`, `meetsTotalCredits`, `blocked`, `warnings` and `unknownCourses`. The plan respects prerequisites (including either/or options), corequisite labs, terms offered, credit minimums for capstones (90) and internships (60), and flags permission-required courses in `notes`.

`POST /api/schedule`
```json
{ "courses": ["ZEE 2100", "ZMA 2311"], "term": "Fall 2026",
  "preferences": { "modality": ["online","hybrid"], "noEvening": true, "noWeekend": true,
                   "avoidDays": "F", "earliestStart": "09:00", "campus": ["Kendall"], "allowWaitlist": true } }
```
The response has `sections` (with `crn`, `meetings`, `instructor`, `seatsOpen`, `status`, `linked_crn`), `credits`, `conflicts`, `waitlisted`, `unscheduled` (each with a `reason`: `not_offered`, `cancelled`, `preferences` (includes `alternatives`), or `full`) and `ok`. Linked labs are added automatically, and cancelled sections are never picked.

## Transcript reading (Gemini multimodal)

`POST /api/transcript` accepts either:
- `multipart/form-data` with `file` (PDF, PNG, JPEG or WebP, up to 5 MB) and an optional `program`
- or JSON `{ "text": "pasted course list", "program": "AI" }`

```js
const form = new FormData(); form.append("file", fileInput.files[0]); form.append("program", "AI");
const r = await fetch(API + "/api/transcript", { method: "POST", body: form });   // don't set Content-Type yourself
```
The response has `completed` (course codes that count), `courses` (with grade, credits and term), `notCounted` (D, F or W grades, with a `reason`), `notInCatalog` and `engine` (`gemini` for images or scans, `parser` for text). When `program` is sent, it also includes `audit` and `plan`, the same shapes as `/api/audit` and `/api/plan`. The file is not stored, and names and IDs are never returned. Without a Gemini key, image uploads return `503 vision_unavailable`; pasted text still works.

## Signed-in student data

| Route | Body | Notes |
|---|---|---|
| `GET /api/me` | | `{ user, progress: {careerId: {statuses, updatedAt}}, plans: {program: {plan, updatedAt}} }` |
| `PUT /api/me/progress/{careerId}` | `{ "statuses": { "Food safety and sanitation": "completed" } }` | replaces that career's statuses |
| `DELETE /api/me/progress/{careerId}` | | |
| `PUT /api/me/plans/{program}` | `{ "plan": <the /api/plan response> }` | |

**Auth:** once Auth0 is configured (`GET /api/health` returns `"auth": "auth0"`), send `Authorization: Bearer <access token>` from `@auth0/auth0-react`'s `getAccessTokenSilently()`. Until then (`"auth": "demo"`), send `X-Demo-User: <any 3-64 letters/digits>`. Missing or bad credentials return `401` with `error` set to `auth_required`, `invalid_token` or `token_expired`.

## Sponsor data in responses

- **Prune:** `engine.prune` on chat and roadmap responses: `{ cacheHit, cacheType, tokensSaved, costWithoutPruneUsd, costWithPruneUsd, costSavedUsd, optimizations }`.
- **Swarms:** personalized roadmaps include `agentSteps: [{ agent, role, summary }]` (Career Researcher → MDC Pathway Planner → Transfer & Outcomes Advisor) and `engine.usage: { totalTokens, costUsd }`.
- **Stats:** `GET /api/stats?days=7&bucket=day|hour` returns `{ prune: { pruneCalls, cacheHits, cacheHitRate, tokensSaved, costSavedUsd }, trends: { series: [{bucket, chat, roadmap, plan, transcript}], topCareers, recommendedPrograms, engines: [{engine, count, avgLatencyMs}], languages, storage } }`. It's computed with TigerData `time_bucket()` when `DATABASE_URL` is set, and with SQLite otherwise.

---

## Quick start (fetch)

```js
const API = "http://127.0.0.1:5000";
async function api(path, body) {
  const res = await fetch(API + path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : undefined);
  const data = await res.json();
  if (!res.ok) throw Object.assign(new Error(data.message), data);   // data.error, data.field
  return data;
}
const { careers } = await api("/api/careers");
const roadmap = await api("/api/roadmap", { careerId: "chef", profile: { grade: "11", interests: ["baking"] } });
const reply = await api("/api/chat", { chatHistory: [{ sender: "user", text: "I love Arduino projects" }] });
const plan = await api("/api/plan", { program: "ECE" });
```

Tests that pin this contract: `cd backend` and then `.\.venv\Scripts\python -m pytest -q tests` (87 tests, offline, no keys used).
