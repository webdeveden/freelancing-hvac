# HVAC Pro — AI Receptionist & Dispatch Dashboard

A full-stack AI voice receptionist for an HVAC business. Answers calls 24/7, books appointments, handles FAQs, detects emergencies, and dispatches jobs in real time through a Vue.js admin dashboard.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [How the Pieces Connect](#how-the-pieces-connect)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Role-Based Permissions](#role-based-permissions)
- [Real-Time Events](#real-time-events)
- [AI Voice Call Flow](#ai-voice-call-flow)
- [Prerequisites](#prerequisites)
- [Docker Setup](#docker-setup)
- [Local Setup (Manual)](#local-setup-manual)
- [Default Credentials](#default-credentials)
- [Environment Variables](#environment-variables)
- [Twilio Configuration](#twilio-configuration)
- [Feature Summary](#feature-summary)

---

## Architecture Overview

```
                         ┌──────────────────────────────────────────────────┐
                         │               Inbound Phone Call                 │
                         │           (Customer dials Twilio #)              │
                         └───────────────────────┬──────────────────────────┘
                                                 │
                                                 ▼
                         ┌──────────────────────────────────────────────────┐
                         │              Twilio Voice Webhook                │
                         │      POST /twilio/voice/incoming                 │
                         └───────────────────────┬──────────────────────────┘
                                                 │
                          ┌──────────────────────┴──────────────────────┐
                          │   Business hours AND receptionist_phone set? │
                          └───────┬──────────────────────────┬──────────┘
                           YES ───┘                          └─── NO
                           │                                      │
                    <Dial receptionist                    AI greets directly
                     phone, 20s timeout>                         │
                           │                                      │
              ┌────────────┴──────────────┐                      │
         Answered                    Not answered                 │
              │                      no-answer/busy/failed        │
              │                           │                       │
         Normal call               POST /voice/missed             │
         (human handles)           AI takes over                  │
                                   "sorry we missed you"          │
                                        │                         │
                                        └────────────┬────────────┘
                                                     │
                                                     ▼
                                    ┌─────────────────────────────┐
                                    │    Python AI Service         │
                                    │  FastAPI + Claude (Haiku)    │
                                    │  Conversation state machine  │
                                    └──────────────┬──────────────┘
                                                   │  Job booked →
                                                   │  INSERT to PostgreSQL
                                                   │  POST /api/internal/jobs
                                                   ▼
┌──────────────────────┐    HTTP (X-Internal-Secret)   ┌──────────────────────┐
│  Python AI Service   │ ─────────────────────────────▶│   Node.js Backend    │
│  Port 8000           │                               │  Express + Socket.IO │
└──────────────────────┘                               │  Port 3001           │
                                                       └──────────┬───────────┘
                                                                  │
                                          ┌───────────────────────┤
                                          │                       │
                                    PostgreSQL              Socket.IO
                                    Port 5432         (job:created, emergency:alert,
                                          │             dispatch:new, …)
                                          │                       │
                                          │                       ▼
                                          │         ┌──────────────────────┐
                                          │         │   Vue.js Dashboard   │
                                          └────────▶│   Port 5173 / 80     │
                                                    └──────────────────────┘
```

---

## How the Pieces Connect

### 1 — Inbound call routing

The **Twilio number** is the published business number. When a call comes in:

- **Business hours + receptionist configured** → Twilio dials `RECEPTIONIST_PHONE` for up to 20 seconds. If the human answers, the call is handled normally. If not (no-answer, busy, missed), Twilio POSTs to `/twilio/voice/missed` and the AI takes over with a "sorry we missed you" greeting.
- **Outside business hours** → AI answers directly with the standard greeting.

Business hours logic runs in Python (`is_business_hours()`) using the `BUSINESS_TIMEZONE`, `BUSINESS_HOURS_START/END`, and `BUSINESS_DAYS` settings before any speech is processed.

### 2 — AI conversation (Python → Claude)

The Python **FastAPI** service (`ai-service/`) handles every Twilio webhook:

- `/incoming` — starts the call routing logic
- `/missed` — AI fallback when receptionist doesn't answer
- `/gather` — receives Twilio's speech-to-text, sends the full conversation history to **Claude**, returns TwiML with the AI's spoken reply
- `/status` — cleans up the in-memory session when the call ends
- `/fallback` — catches Twilio HTTP errors so no call ever drops

Claude is given a structured system prompt that enforces JSON output:

```json
{
  "speech_to_say": "What to say to the caller",
  "extracted_data": { "caller_name", "address", "service_type", … },
  "next_state": "GREETING | COLLECTING_INFO | CONFIRMING | BOOKING | ANYTHING_ELSE | FAREWELL",
  "is_emergency": false
}
```

The state machine drives the conversation from greeting → collecting info → confirming → booking → "anything else?" → farewell.

### 3 — Job creation bridge (Python → Node.js)

When the state reaches `BOOKING`:

1. Python inserts the job directly into **PostgreSQL** (`job_creator.py`)
2. Python POSTs `{ job_id }` to `POST /api/internal/jobs` with a shared secret header
3. Node.js fetches the full job row and fires Socket.IO events (`job:created`, `emergency:alert` if applicable)

The two-step design ensures the job is durable in the database before the notification is sent. A failed notification never loses the job.

### 4 — Real-time dashboard (Node.js → Vue.js)

The **Node.js** backend handles:

- All REST API endpoints (jobs, dispatches, users, FAQ, auth)
- Database access via **Prisma v7** with `@prisma/adapter-pg` (no native binary — uses the `pg` driver directly)
- Socket.IO server — authenticated joins via JWT, all events broadcast to the `dispatchers` room

The **Vue.js** frontend:

- Connects to Socket.IO on load and joins the `dispatchers` room
- Updates the job board, dispatch kanban, and toast notifications in real time without polling
- Role-based views: admins see the full dispatch kanban; techs see only their own assigned jobs

---

## Tech Stack

| Layer            | Technology                                                            |
| ---------------- | --------------------------------------------------------------------- |
| Frontend         | Vue 3, Vite, Tailwind CSS v4, Pinia, Vue Router                       |
| Real-time        | Node.js 20, Express, Socket.IO                                        |
| ORM              | Prisma v7.8.0 + `@prisma/adapter-pg`                                  |
| AI + Voice       | Python 3.11+, FastAPI, Anthropic Claude (`claude-haiku-4-5-20251001`) |
| Telephony        | Twilio Voice, TwiML, Polly.Joanna-Neural TTS                          |
| Database         | PostgreSQL 16                                                         |
| Auth             | JWT (role + name embedded in token)                                   |
| Containerization | Docker, Docker Compose                                                |

---

## Project Structure

```
HVAC_JS_PY/
├── docker-compose.yml              # Starts all 4 services + PostgreSQL
├── .env                            # Secrets — NEVER commit this file
├── .gitignore
│
├── database/
│   ├── migrations/                 # SQL files — applied in order at first startup
│   │   ├── 001_create_users.sql
│   │   ├── 002_create_jobs.sql
│   │   ├── 003_create_dispatches.sql
│   │   ├── 004_create_faq_entries.sql
│   │   └── 005_create_job_comments.sql
│   ├── mock/                       # Seed data (JSON)
│   │   ├── users.json              # 1 admin, 2 dispatchers, 3 techs
│   │   ├── jobs.json               # 18 jobs across statuses / priorities
│   │   ├── dispatches.json         # 8 dispatch records
│   │   └── faq_entries.json        # 15 common HVAC FAQs
│   └── seeds/
│       └── run_seeds.js
│
├── backend/                        # Node.js — REST API + Socket.IO
│   ├── package.json                # type: module (ES Modules)
│   ├── Dockerfile
│   ├── prisma/
│   │   └── schema.prisma           # Prisma v7 data model (5 models)
│   └── src/
│       ├── index.js                # Express + Socket.IO bootstrap
│       ├── config/
│       │   └── prisma.js           # PrismaClient singleton (PrismaPg adapter)
│       ├── middleware/
│       │   ├── auth.js             # requireAuth / requireAdmin
│       │   └── errorHandler.js
│       ├── routes/                 # auth, jobs, dispatches, techs, faq, internal
│       ├── controllers/            # Business logic — all queries via Prisma
│       ├── services/
│       │   └── socket.service.js   # emit helpers (emitJobCreated, emitEmergencyAlert…)
│       └── socket/
│           └── handlers.js         # Socket.IO event handlers + JWT auth
│
├── ai-service/                     # Python — Twilio webhooks + Claude AI
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── main.py                     # FastAPI app + router registration
│   ├── config/
│   │   └── settings.py             # Pydantic Settings — all env vars typed here
│   ├── routers/
│   │   ├── twilio_voice.py         # All Twilio webhook endpoints + is_business_hours()
│   │   └── health.py
│   ├── services/
│   │   ├── ai_agent.py             # Claude API call + JSON parsing + system prompt builder
│   │   ├── call_state.py           # In-memory session store (keyed by CallSid)
│   │   ├── job_creator.py          # Direct PostgreSQL INSERT via psycopg2
│   │   ├── dispatcher_notify.py    # HTTP POST to Node.js internal endpoint
│   │   └── faq_handler.py          # Keyword-based FAQ retrieval from DB
│   ├── models/
│   │   ├── call_session.py         # Pydantic: CallSession, Message
│   │   └── job.py                  # Pydantic: JobPayload
│   └── prompts/
│       └── system_prompt.txt       # Claude system prompt — HVAC persona, states, JSON format
│
└── frontend/                       # Vue 3 + Tailwind CSS v4
    ├── package.json
    ├── vite.config.js
    ├── nginx.conf                  # Serves built app in Docker
    ├── Dockerfile                  # Multi-stage: Vite build → nginx
    └── src/
        ├── main.js
        ├── App.vue
        ├── app.css                 # Tailwind @import + @theme brand tokens
        ├── router/index.js         # Routes + auth guard
        ├── stores/
        │   ├── auth.store.js       # JWT decode, isAdmin, isTech getters
        │   ├── jobs.store.js       # Jobs list + Socket.IO handlers
        │   ├── dispatches.store.js # Dispatch board + unread alert count
        │   └── theme.store.js      # dark / light / system, persisted
        ├── composables/
        │   ├── useSocket.js        # Socket.IO singleton + toast queue
        │   └── useAuth.js          # Login / logout helpers
        ├── services/               # Axios with JWT Authorization interceptor
        ├── views/
        │   ├── LoginView.vue
        │   ├── JobsListView.vue    # Status summary bar + job grid with filters
        │   ├── JobDetailView.vue   # Full detail + clickable map address + comments
        │   ├── JobCreateView.vue   # Manual job creation form (admin only)
        │   ├── DispatchBoardView.vue # Role-aware: admin kanban or tech assignments
        │   └── NotFoundView.vue
        └── components/
            ├── layout/             # AppLayout, AppHeader, AppSidebar
            ├── jobs/               # JobCard, JobStatusBadge, JobFilters,
            │                       # AssignTechModal, JobComments
            ├── dispatch/           # DispatchCard (status badge + map link), DispatchBell
            └── ui/                 # ThemeToggle, LoadingSpinner,
                                    # ToastNotification (emergency banner + regular toast)
```

---

## Database Schema

### `users`

| Column        | Type           | Notes                             |
| ------------- | -------------- | --------------------------------- |
| id            | SERIAL PK      |                                   |
| email         | VARCHAR UNIQUE |                                   |
| password_hash | VARCHAR        | bcrypt                            |
| role          | VARCHAR        | `admin` \| `dispatcher` \| `tech` |
| full_name     | VARCHAR        |                                   |
| phone         | VARCHAR        | nullable                          |
| is_active     | BOOLEAN        | default true                      |

### `jobs`

| Column           | Type        | Notes                                                                  |
| ---------------- | ----------- | ---------------------------------------------------------------------- |
| id               | SERIAL PK   |                                                                        |
| caller_name      | VARCHAR     | nullable                                                               |
| caller_phone     | VARCHAR     | required                                                               |
| service_type     | VARCHAR     | e.g. AC Repair, Furnace                                                |
| description      | TEXT        | AI-summarized or manually entered                                      |
| address / city   | TEXT        | clickable Google Maps link in UI                                       |
| status           | VARCHAR     | `pending` \| `assigned` \| `in-progress` \| `completed` \| `cancelled` |
| priority         | VARCHAR     | `normal` \| `high` \| `emergency`                                      |
| assigned_tech_id | FK → users  | nullable                                                               |
| scheduled_at     | TIMESTAMPTZ | nullable                                                               |
| notes            | TEXT        | internal dispatcher notes                                              |
| call_sid         | VARCHAR     | Twilio CallSid — set for AI-created jobs                               |

### `dispatches`

| Column         | Type              | Notes                                                             |
| -------------- | ----------------- | ----------------------------------------------------------------- |
| id             | SERIAL PK         |                                                                   |
| job_id         | FK → jobs CASCADE |                                                                   |
| tech_id        | FK → users        | nullable                                                          |
| dispatched_by  | FK → users        | nullable                                                          |
| dispatch_notes | TEXT              |                                                                   |
| dispatched_at  | TIMESTAMPTZ       | default now                                                       |
| status         | VARCHAR           | `sent` \| `acknowledged` \| `en-route` \| `on-site` \| `resolved` |

### `job_comments`

| Column    | Type               | Notes                      |
| --------- | ------------------ | -------------------------- |
| id        | SERIAL PK          |                            |
| job_id    | FK → jobs CASCADE  |                            |
| author_id | FK → users CASCADE |                            |
| content   | TEXT               | rendered as Markdown in UI |

### `faq_entries`

| Column            | Type      | Notes                                      |
| ----------------- | --------- | ------------------------------------------ |
| id                | SERIAL PK |                                            |
| category          | VARCHAR   | pricing, services, availability, emergency |
| question / answer | TEXT      |                                            |
| keywords          | TEXT[]    | GIN-indexed — used by AI for FAQ lookup    |
| active            | BOOLEAN   |                                            |

---

## API Reference

### Authentication

| Method | Path                 | Auth   | Description                     |
| ------ | -------------------- | ------ | ------------------------------- |
| POST   | `/api/auth/login`    | Public | Returns `{ token, user }`       |
| POST   | `/api/auth/register` | Public | Creates dispatcher/tech account |
| GET    | `/api/auth/me`       | JWT    | Current user profile            |

### Jobs

| Method | Path                          | Auth  | Description                                                     |
| ------ | ----------------------------- | ----- | --------------------------------------------------------------- |
| GET    | `/api/jobs`                   | JWT   | List jobs (`?status=&priority=&assigned_tech_id=&page=&limit=`) |
| GET    | `/api/jobs/:id`               | JWT   | Single job with tech info                                       |
| POST   | `/api/jobs`                   | Admin | Create job manually                                             |
| PATCH  | `/api/jobs/:id`               | JWT   | Update job (non-admin: `status` only)                           |
| PATCH  | `/api/jobs/:id/assign`        | Admin | Assign technician — auto-creates dispatch                       |
| DELETE | `/api/jobs/:id`               | Admin | Delete job                                                      |
| GET    | `/api/jobs/:id/comments`      | JWT   | Get comments                                                    |
| POST   | `/api/jobs/:id/comments`      | JWT   | Post a Markdown comment                                         |
| DELETE | `/api/jobs/:id/comments/:cid` | JWT   | Delete (own comment or admin)                                   |

### Dispatches

| Method | Path                         | Auth | Description                                          |
| ------ | ---------------------------- | ---- | ---------------------------------------------------- |
| GET    | `/api/dispatches`            | JWT  | List dispatches (`?status=&tech_id=&dispatched_by=`) |
| GET    | `/api/dispatches/:id`        | JWT  | Single dispatch with joined fields                   |
| POST   | `/api/dispatches`            | JWT  | Create dispatch + auto-assign tech on job            |
| PATCH  | `/api/dispatches/:id/status` | JWT  | Advance dispatch status                              |

### Other

| Method                | Path                 | Auth                       | Description                                     |
| --------------------- | -------------------- | -------------------------- | ----------------------------------------------- |
| GET                   | `/api/techs`         | JWT                        | Active technicians list                         |
| GET/POST/PATCH/DELETE | `/api/faq`           | JWT / Admin                | FAQ knowledge base CRUD                         |
| POST                  | `/api/internal/jobs` | `X-Internal-Secret` header | Python → Node.js bridge: emits Socket.IO events |

### Twilio Webhooks (Python AI Service)

| Method | Path                     | Description                                                     |
| ------ | ------------------------ | --------------------------------------------------------------- |
| POST   | `/twilio/voice/incoming` | Every inbound call — routes to receptionist or AI               |
| POST   | `/twilio/voice/missed`   | Called after `<Dial>` completes — AI takes over if not answered |
| POST   | `/twilio/voice/gather`   | Twilio speech result → Claude → TwiML response                  |
| POST   | `/twilio/voice/status`   | Call ended — cleans up session                                  |
| POST   | `/twilio/voice/fallback` | Primary webhook error fallback                                  |

---

## Role-Based Permissions

| Action                     | Admin | Dispatcher | Tech               |
| -------------------------- | ----- | ---------- | ------------------ |
| Create job manually        | ✅    | ❌         | ❌                 |
| Edit full job details      | ✅    | ❌         | ❌                 |
| Assign technician          | ✅    | ❌         | ❌                 |
| Delete job                 | ✅    | ❌         | ❌                 |
| Change job status          | ✅    | ✅         | ✅ (status only)   |
| Create / manage dispatches | ✅    | ✅         | ❌                 |
| Post comment               | ✅    | ✅         | ✅                 |
| Delete own comment         | ✅    | ✅         | ✅                 |
| Delete any comment         | ✅    | ❌         | ❌                 |
| Manage FAQ                 | ✅    | ❌         | ❌                 |
| See dispatch kanban        | ✅    | ✅         | ❌                 |
| See "My Assignments"       | ❌    | ❌         | ✅ (own jobs only) |

Non-admin PATCH requests to `/api/jobs/:id` have all fields except `status` stripped server-side — the restriction is enforced in the backend, not just the UI.

---

## Real-Time Events

### Server → Client (Socket.IO)

| Event             | Payload                  | Trigger                                                     |
| ----------------- | ------------------------ | ----------------------------------------------------------- |
| `job:created`     | `{ job }`                | New job from AI call or admin form                          |
| `job:updated`     | `{ job }`                | Status, assignment, or field changed                        |
| `job:deleted`     | `{ jobId }`              | Job removed                                                 |
| `dispatch:new`    | `{ dispatch, job }`      | Dispatch created or tech assigned to job                    |
| `dispatch:status` | `{ dispatchId, status }` | Dispatch status advanced                                    |
| `emergency:alert` | `{ job, message }`       | Emergency-priority job — red full-width banner + audio beep |
| `comment:added`   | `{ jobId, comment }`     | New comment posted                                          |
| `comment:deleted` | `{ jobId, commentId }`   | Comment removed                                             |

### Client → Server

| Event              | Payload     | Description                                       |
| ------------------ | ----------- | ------------------------------------------------- |
| `join:dispatchers` | `{ token }` | JWT verified server-side before admitting to room |

---

## AI Voice Call Flow

```
Customer calls Twilio number
        │
        ▼
POST /twilio/voice/incoming
        │
        ├─ Business hours AND RECEPTIONIST_PHONE set?
        │       YES ──▶ <Dial> rings receptionist (20s timeout)
        │                   ├─ Answered → normal human call
        │                   │   POST /voice/missed (DialCallStatus=completed) → empty response
        │                   ├─ No-answer/busy/failed
        │                   │   POST /voice/missed → AI greets "sorry we missed you"
        │                   └─ Caller hung up → POST /voice/missed (canceled) → empty response
        │
        └─ NO (after hours or no receptionist phone)
                AI answers directly with standard greeting
                │
                ▼
POST /twilio/voice/gather   (called each time caller speaks)
  ├─ No speech detected → retry (up to 3 attempts) → warm farewell
  └─ Speech received:
       ├─ Build system prompt (business info substituted via .replace())
       ├─ Inject FAQ context if caller asks a question
       ├─ Call Claude with full conversation history
       └─ Claude returns JSON:
            { speech_to_say, extracted_data, next_state, is_emergency }
                │
                ├─ States: GREETING → COLLECTING_INFO → CONFIRMING
                │                                           │
                │                                        BOOKING
                │                                           │
                │                             INSERT job → PostgreSQL
                │                             POST /api/internal/jobs
                │                             Node.js emits Socket.IO events
                │                                           │
                │                                    ANYTHING_ELSE
                │                             "Is there anything else I can help with?"
                │                                    ┌──────┴──────┐
                │                                  YES             NO
                │                             COLLECTING_INFO    FAREWELL
                │                                                   │
                └──────────────────────────────────────────────  Hang up

POST /twilio/voice/status   (call ended by either party)
  └─ Delete CallSession from memory
```

**Emergency keywords** — Claude sets `is_emergency: true` on: "no heat", "gas leak", "gas smell", "carbon monoxide", "CO detector", "smoke / burning smell" from HVAC, "flooding", "pipe burst", "frozen pipes", "AC failure" in extreme heat, "electrical sparks". Emergency jobs get `priority = 'emergency'` and trigger the `emergency:alert` Socket.IO event, which shows a full-width persistent red banner at the top of the dashboard and plays an audio beep.

---

## Prerequisites

- **Docker Desktop** (recommended — runs everything with one command)
- Or: Node.js 20+, Python 3.11+, PostgreSQL 16, pip
- A **Twilio** account with a Voice-capable phone number
- An **Anthropic** API key
- A public tunnel for Twilio webhooks: [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/) (free, persistent) or ngrok

---

## Docker Setup

The fastest way to run everything.

```bash
# 1. Copy and fill in the root .env
cp .env.example .env
# Required: DB_PASSWORD, JWT_SECRET, INTERNAL_API_SECRET,
#           ANTHROPIC_API_KEY, TWILIO_*, BUSINESS_*, RECEPTIONIST_PHONE

# 2. Build and start all 4 services
docker-compose up --build

# 3. Seed the database (first run only)
docker-compose exec backend node database/seeds/run_seeds.js
```

**Service URLs after startup:**

| Service           | URL                   |
| ----------------- | --------------------- |
| Vue.js Dashboard  | http://localhost:5173 |
| Node.js API       | http://localhost:3001 |
| Python AI Service | http://localhost:8000 |
| PostgreSQL        | http://localhost:5432 |

**LAN access** (other devices on the same network):

Set the LAN IP of your machine in `.env` before building:

```env
VITE_API_BASE_URL=http://192.168.x.x:3001/api
VITE_SOCKET_URL=http://192.168.x.x:3001
FRONTEND_URL=http://192.168.x.x:5173
```

Then rebuild: `docker-compose up --build -d frontend`

---

## Local Setup (Manual)

### 1 — PostgreSQL

```bash
psql -U postgres -c "CREATE USER hvac_user WITH PASSWORD 'hvacpassword';"
psql -U postgres -c "CREATE DATABASE hvac_db OWNER hvac_user;"

# Run migrations in order
for f in database/migrations/*.sql; do
  psql -U hvac_user -d hvac_db -f "$f"
done
```

### 2 — Seed mock data

```bash
cd database/seeds
npm install pg bcryptjs
DB_HOST=localhost DB_USER=hvac_user DB_PASSWORD=hvacpassword DB_NAME=hvac_db node run_seeds.js
```

### 3 — Node.js Backend

```bash
cd backend
npm install          # also runs: npx prisma generate
cp .env.example .env # set JWT_SECRET, INTERNAL_API_SECRET, DATABASE_URL
npm run dev          # http://localhost:3001
```

### 4 — Python AI Service

```bash
cd ai-service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # set ANTHROPIC_API_KEY, TWILIO_*, business info
python main.py       # http://localhost:8000
```

### 5 — Vue.js Frontend

```bash
cd frontend
npm install
cp .env.example .env
# VITE_API_BASE_URL=http://localhost:3001/api
# VITE_SOCKET_URL=http://localhost:3001
npm run dev          # http://localhost:5173
```

---

## Default Credentials

Created by the seed script.

| Role       | Email                   | Password      |
| ---------- | ----------------------- | ------------- |
| Admin      | admin@hvacpro.com       | Admin@1234    |
| Dispatcher | dispatch@hvacpro.com    | Dispatch@1234 |
| Dispatcher | dispatch2@hvacpro.com   | Dispatch@1234 |
| Technician | tech.mike@hvacpro.com   | Tech@1234     |
| Technician | tech.angela@hvacpro.com | Tech@1234     |
| Technician | tech.derek@hvacpro.com  | Tech@1234     |

---

## Environment Variables

All variables live in a single `.env` at the project root. Docker Compose reads this file and injects values into each service container.

```env
# ── PostgreSQL ──────────────────────────────────────────────────────────────
DB_NAME=hvac_db
DB_USER=hvac_user
DB_PASSWORD=your_secure_password

# Prisma connection URL (used by Node.js backend)
# URL-encode special chars in password, e.g. @ → %40
DATABASE_URL=postgresql://hvac_user:your_password@postgres:5432/hvac_db

# ── Node.js backend ─────────────────────────────────────────────────────────
# Generate: node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
JWT_SECRET=your_long_random_secret
JWT_EXPIRES_IN=8h
INTERNAL_API_SECRET=your_shared_secret    # Must match ai-service value
FRONTEND_URL=http://localhost:5173

# ── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-your-key
AI_MODEL=claude-haiku-4-5-20251001

# ── Twilio ───────────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX          # Your Twilio number (published as business #)

# ── Business info (injected into Claude system prompt) ───────────────────────
BUSINESS_NAME=Your HVAC Company Name
BUSINESS_PHONE=+1XXXXXXXXXX              # Real business phone (shown in AI farewell)
SERVICE_AREA=City, State and surrounding areas
BUSINESS_HOURS=Monday to Friday 8 AM to 6 PM, Saturday 9 AM to 2 PM

# ── Call routing ─────────────────────────────────────────────────────────────
RECEPTIONIST_PHONE=+1XXXXXXXXXX          # Phone to ring first during business hours
                                          # Leave empty to have AI always answer
BUSINESS_HOURS_START=08:00               # HH:MM 24h
BUSINESS_HOURS_END=18:00                 # HH:MM 24h (exclusive — 18:00 = last valid minute 17:59)
BUSINESS_DAYS=Mon,Tue,Wed,Thu,Fri,Sat    # comma-separated strftime %a values
BUSINESS_TIMEZONE=America/Chicago        # IANA timezone

# ── Public tunnel (Twilio webhook callbacks) ─────────────────────────────────
# Update each time you start a new tunnel session
PUBLIC_URL=https://your-tunnel.trycloudflare.com

# ── Frontend (Vite — baked in at build time) ─────────────────────────────────
# For LAN access, replace localhost with your machine's LAN IP
VITE_API_BASE_URL=http://localhost:3001/api
VITE_SOCKET_URL=http://localhost:3001
```

---

## Twilio Configuration

### 1 — Get a Twilio number

Buy a Voice-capable number from the [Twilio Console](https://console.twilio.com). This number becomes your published business phone number.

### 2 — Expose the AI service

Use a public tunnel so Twilio can reach your local machine:

```bash
# Cloudflare Tunnel (free, no account needed for temporary URLs)
cloudflared tunnel --url http://localhost:8000

# Or ngrok
ngrok http 8000
```

Set the tunnel URL in `.env`:

```env
PUBLIC_URL=https://your-tunnel-url.trycloudflare.com
```

Then restart the AI service: `docker-compose up -d ai-service`

### 3 — Configure Twilio webhooks

In the [Twilio Console](https://console.twilio.com) → Phone Numbers → your number → Voice Configuration:

| Setting                              | Value                                       |
| ------------------------------------ | ------------------------------------------- |
| **A call comes in** (Webhook)        | `https://your-tunnel/twilio/voice/incoming` |
| **Call status changes** (Webhook)    | `https://your-tunnel/twilio/voice/status`   |
| **Primary handler fails** (Fallback) | `https://your-tunnel/twilio/voice/fallback` |

### 4 — Verify the receptionist phone (trial accounts)

On Twilio trial accounts, outbound calls can only go to **verified numbers**. To verify your receptionist phone:

Twilio Console → Phone Numbers → **Verified Caller IDs** → Add the number → Complete verification call/SMS.

### 5 — Test the full flow

```
1. Call your Twilio number
2. During business hours:  your RECEPTIONIST_PHONE rings for ~12 seconds
   - Answer it → normal call handled by human
   - Don't answer → AI takes over: "Sorry we missed you, I'm the AI assistant…"
3. After hours:  AI greets directly
4. Complete a booking → job appears instantly in the dashboard
5. Say "my heat is completely out" → emergency banner appears in dashboard
```

---

## Feature Summary

| Feature               | Details                                                                     |
| --------------------- | --------------------------------------------------------------------------- |
| Smart call routing    | During business hours: rings real phone first; AI fallback on no-answer     |
| AI voice receptionist | 24/7 call handling via Twilio + Claude (Polly.Joanna-Neural TTS)            |
| Appointment booking   | Collects name, address, service type, description, optional schedule        |
| "Anything else?" flow | After booking, AI asks if there's another issue before saying goodbye       |
| FAQ handling          | Keyword-matched answers from DB — no hallucination                          |
| Emergency detection   | Specific keyword triggers: gas leak, no heat, CO alarm, etc.                |
| Emergency banner      | Full-width persistent red banner + audio beep in dashboard                  |
| Real-time dashboard   | Socket.IO — jobs/dispatches update without page refresh                     |
| Role-based views      | Admin/dispatcher: dispatch kanban. Techs: own assigned jobs only            |
| Map links             | Addresses in job cards, dispatch cards, job detail → open Google Maps       |
| Manual job creation   | Admin form to create jobs without a call                                    |
| Dispatch kanban       | 5-column board: Sent → Acknowledged → En Route → On Site → Resolved         |
| Markdown comments     | Write/Preview tab on job detail — stored as raw text, rendered on read      |
| Theme toggle          | Dark / Light / System — persisted to localStorage                           |
| JWT auth              | Role + name embedded in token; verified on every request and Socket.IO join |
| Prisma ORM            | v7.8.0 with `@prisma/adapter-pg` — type-safe queries, no native binary      |
| LAN access            | Frontend and backend configurable for local network access                  |
