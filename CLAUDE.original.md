# HVAC Pro — Claude Code Context

## What This Is

Full-stack AI receptionist + dispatch system for HVAC businesses.

- **Voice AI**: Twilio calls → Python FastAPI → Claude Haiku → TwiML speech
- **Dispatch dashboard**: Vue 3 SPA with real-time Socket.IO updates
- **Backend API**: Node.js + Express + Prisma + PostgreSQL

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vite, Tailwind CSS v4, Pinia, Vue Router |
| Backend API | Node.js 20, Express, Socket.IO |
| ORM | Prisma v7 with `@prisma/adapter-pg` (`pg` driver — no native binary) |
| Database | PostgreSQL 16 |
| AI / Voice | Python 3.11, FastAPI, Anthropic SDK, Claude Haiku |
| Telephony | Twilio Voice, TwiML, Polly.Joanna-Neural TTS |
| Auth | JWT (role + name embedded in token) |
| Infra | Docker, Docker Compose |

---

## Directory Structure

```
HVAC_JS_PY/
├── backend/               Node.js REST API + Socket.IO
│   ├── src/
│   │   ├── index.js       Express + Socket.IO bootstrap
│   │   ├── routes/        auth, jobs, dispatches, techs, faq, internal
│   │   ├── controllers/   Business logic
│   │   ├── services/      socket.service.js
│   │   ├── socket/        handlers.js
│   │   └── middleware/    auth.js, errorHandler.js
│   └── prisma/schema.prisma
│
├── ai-service/            Python FastAPI voice agent
│   ├── main.py            FastAPI bootstrap
│   ├── routers/
│   │   ├── twilio_voice.py  All Twilio webhooks
│   │   └── health.py
│   ├── services/
│   │   ├── ai_agent.py      Claude API integration (main entry)
│   │   ├── call_state.py    In-memory call sessions (keyed by call_sid)
│   │   ├── job_creator.py   Direct psycopg2 INSERT into PostgreSQL
│   │   ├── tech_availability.py  Tech availability tool
│   │   ├── dispatcher_notify.py  HTTP POST to Node.js internal endpoint
│   │   └── faq_handler.py   FAQ keyword lookup
│   ├── models/            Pydantic models
│   ├── config/settings.py Environment config (Pydantic BaseSettings)
│   └── prompts/system_prompt.txt  Claude system prompt template
│
└── frontend/              Vue 3 SPA
    └── src/
        ├── router/        Auth guard + routes
        ├── stores/        Pinia: auth, jobs, dispatches, theme
        ├── services/      Axios with JWT interceptor
        ├── composables/   useSocket.js, useAuth.js
        └── views/         LoginView, JobsListView, JobDetailView,
                           JobCreateView, DispatchBoardView
```

---

## How to Run

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:3001
- AI service: http://localhost:8000

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/index.js` | Express + Socket.IO bootstrap |
| `backend/src/routes/internal.routes.js` | Python → Node bridge (`POST /api/internal/jobs`) |
| `ai-service/services/ai_agent.py` | Claude API call + tool-use loop |
| `ai-service/prompts/system_prompt.txt` | Claude system prompt (has `{placeholder}` substitution) |
| `ai-service/services/job_creator.py` | Direct DB insert (psycopg2) |
| `frontend/src/stores/jobs.store.js` | Job state + Socket.IO handlers |
| `frontend/src/views/DispatchBoardView.vue` | Dispatch kanban UI |

---

## Conventions

- **DB schema changes**: Always via `prisma/schema.prisma` + `prisma migrate dev`. Never raw SQL migrations.
- **Auth**: JWT with role embedded. Backend middleware extracts `req.user`. Roles: `admin`, `dispatcher`, `tech`.
- **Real-time**: Node.js emits Socket.IO events (`job:created`, `dispatch:new`, `emergency:alert`). Vue stores subscribe in `useSocket.js`.
- **Vue state**: Pinia stores only. No Vuex, no local component state for shared data.
- **AI responses**: Claude must return JSON matching `AIResponse` schema. Tool calls happen before the final JSON output.
- **DB connections in Python**: psycopg2 synchronous, new connection per operation (same pattern as `job_creator.py`). Close in `finally`.
- **System prompt placeholders**: `{business_name}`, `{business_phone}`, `{service_area}`, `{business_hours}`, `{emergency_hours}` — substituted in `ai_agent._build_system_prompt()`.

---

## Common Tasks

### Add a backend route
1. Create controller method in `backend/src/controllers/`
2. Add route in `backend/src/routes/`
3. Register router in `backend/src/index.js`

### Update the AI system prompt
Edit `ai-service/prompts/system_prompt.txt`. Placeholders substituted at runtime.

### Add a Claude tool (function calling)
1. Add tool handler in `ai-service/services/`
2. Register tool definition in `ai_agent.py` `_TOOLS` list
3. Add dispatch branch in `_handle_tool_call()` in `ai_agent.py`
4. Add trigger instruction to `system_prompt.txt`

### Run DB migrations
```bash
cd backend && npx prisma migrate dev --name <migration-name>
```

### Seed the database
```bash
cd backend && node prisma/seed.js
```

---

## Environment Variables (`.env` at root)

Key vars used across services:

| Var | Used by |
|-----|---------|
| `DATABASE_URL` | Prisma (backend) |
| `DB_HOST/PORT/NAME/USER/PASSWORD` | Python psycopg2 (ai-service) |
| `ANTHROPIC_API_KEY` | ai-service |
| `TWILIO_*` | ai-service |
| `JWT_SECRET` | backend |
| `BACKEND_URL` | ai-service → Node bridge |
| `INTERNAL_API_SECRET` | ai-service → Node bridge auth |

---

## Socket.IO Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `job:created` | Server → clients | full job object |
| `job:updated` | Server → clients | full job object |
| `dispatch:new` | Server → clients | dispatch + job |
| `dispatch:status` | Server → clients | `{dispatchId, status}` |
| `emergency:alert` | Server → clients | `{jobId, callerName, ...}` |
| `comment:added` | Server → clients | comment object |

---

## Dispatch Status Flow

`sent` → `acknowledged` → `en_route` → `on_site` → `resolved`

Active statuses (tech is busy): `sent`, `acknowledged`, `en_route`, `on_site`
