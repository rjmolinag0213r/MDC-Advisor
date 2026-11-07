# Sponsor setup, step by step

The code for every item below is already in the repo. Each section is account setup only: you create something on the sponsor's site, then paste a value into `backend/.env` (or send it to whoever runs the server).

Order: **1 TigerData → 2 Auth0 → 3 Vultr → 4 GoDaddy**. Each step takes 5 to 10 minutes. Steps 1 and 2 also work locally before you deploy.

---

## 1. TigerData (database for saved progress and usage trends)

1. Sign up at **https://console.cloud.timescale.com** (free trial, no card needed).
2. Click **Create service** → choose **Time-series** (TimescaleDB) → any AWS region close to Miami (us-east-1) → smallest size → **Create**.
3. When it's ready, open the service → **Connection info** (or "Connect") → copy the **Service URL**. It looks like this:
   `postgres://tsdbadmin:PASSWORD@abc123.tsdb.cloud.timescale.com:34567/tsdb?sslmode=require`
4. Paste it into `backend/.env`:
   ```
   DATABASE_URL=postgres://tsdbadmin:...?sslmode=require
   ```
5. Restart the backend. The log should say `TigerData/Postgres ready (timescaledb hypertable)`.

What the app uses it for: an `events` hypertable that logs every chat, roadmap, plan and transcript request (career, program, engine, latency, language). `GET /api/stats` runs `time_bucket()` queries on it to show trends: top careers, recommended programs, and AI engine latency by hour or day. Saved progress and saved plans are stored there too.

## 2. Auth0 (student login so progress follows them)

1. Sign up at **https://auth0.com** → create a tenant (for example `nextstop`).
2. **Applications → APIs → + Create API**
   - Name: `NextStop API`
   - Identifier: `https://api.nextstop` (any URL-like string; this becomes the **audience**)
   - Signing algorithm: **RS256** → Create
3. **Applications → Applications → + Create Application** → **Single Page Application** → Create. In **Settings**:
   - Allowed Callback URLs: `http://localhost:5173, http://127.0.0.1:3000, https://YOURDOMAIN`
   - Allowed Logout URLs: same list
   - Allowed Web Origins: same list
   - Save.
4. Copy the **Domain** (for example `dev-abc123.us.auth0.com`) and put it in `backend/.env`:
   ```
   AUTH0_DOMAIN=dev-abc123.us.auth0.com
   AUTH0_AUDIENCE=https://api.nextstop
   ```
5. **Give your classmate:** the Domain, the SPA's **Client ID**, and the audience. In React they use `@auth0/auth0-react`:
   ```jsx
   <Auth0Provider domain="dev-abc123.us.auth0.com" clientId="..."
     authorizationParams={{ redirect_uri: window.location.origin, audience: "https://api.nextstop" }}>
   ```
   and call the API with `Authorization: Bearer ${await getAccessTokenSilently()}`.
6. Optional: under **Authentication → Social**, enable Google so students sign in with one click.

Until Auth0 is set, the backend runs in **demo mode**: the frontend sends `X-Demo-User: anyname` and saving still works.

## 3. Vultr (hosting)

MLH usually gives hackers Vultr credit. Check the MLH SharkByte prize page for the promo code.

1. Sign up at **https://www.vultr.com** → **Deploy +** → **Cloud Compute – Shared CPU**.
2. Location: **Miami**. Image: **Marketplace Apps → Docker** (Ubuntu with Docker already installed). Plan: 2 GB RAM ($10/mo is plenty; it's billed hourly, so destroy it after judging).
3. Under SSH Keys, add yours (or use the root password Vultr emails you) → **Deploy**. Copy the server's **IP address**.
4. In PowerShell on your PC:
   ```powershell
   ssh root@YOUR_IP
   ```
   Then on the server:
   ```bash
   git clone -b Ricardo_2026 https://github.com/rjmolinag0213r/MDC-Advisor.git
   cd MDC-Advisor
   nano backend/.env        # paste the same contents as your local backend/.env, then Ctrl+O, Enter, Ctrl+X
   ufw allow 80 && ufw allow 443
   cd deploy
   DOMAIN=YOURDOMAIN.xyz docker compose up -d --build
   ```
   The first build takes about 3 minutes.
5. Before you have a domain, test with `curl http://localhost:5000/api/health` on the server. Port 5000 isn't exposed publicly; Caddy serves it on 80 and 443 once the domain points at the server.

## 4. GoDaddy domain (MLH "Best Domain Name")

1. Use the MLH GoDaddy Registry offer (free domain for hackers; see the MLH prize page) to register a name such as `nextstopmdc.xyz`.
2. In GoDaddy → **My Products → DNS** for the domain, add:
   - `A` record, Name `@`, Value `YOUR_VULTR_IP`
   - `A` record, Name `www`, Value `YOUR_VULTR_IP`
3. Wait 5 to 30 minutes for DNS, then open `https://YOURDOMAIN.xyz`. Caddy gets the HTTPS certificate automatically.
4. Add the domain to `backend/.env` on the server so your classmate's deployed frontend can call the API:
   ```
   CORS_ORIGINS=https://YOURDOMAIN.xyz,https://www.YOURDOMAIN.xyz
   ```
   then run `docker compose up -d` again.

---

## What's already done (no setup needed)

| Track | Where it shows up |
|---|---|
| **Swarms** | `POST /api/roadmap` → `engine.name == "swarms"` plus `agentSteps[]` (what each of the 3 agents did) and `engine.usage.costUsd` |
| **Prune** | `POST /api/chat` and `/api/roadmap` → `engine.prune` (`cacheHit`, `tokensSaved`, `costSavedUsd`, `optimizations`). Running totals in `GET /api/stats` → `prune` |
| **Gemini** | `POST /api/transcript`: upload a photo or PDF of a transcript, and Gemini's multimodal model reads the courses, then the audit and plan are built. Demo file: `backend/data/samples/sample_transcript.png` |
