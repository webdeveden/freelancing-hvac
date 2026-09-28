# HVAC Pro — Claude Code Context

## What This Is

Full-stack AI receptionist + dispatch system HVAC business.

- **Voice AI**: Twilio call → Python FastAPI → Claude Haiku → TwiML speech
- **Dispatch dashboard**: Vue 3 SPA real-time Socket.IO update
- **Backend API**: Python FastAPI + psycopg2 + python-socketio + PostgreSQL

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vite, Tailwind CSS v4, Pinia, Vue Router |
| Backend API | Python 3.11, FastAPI, python-socketio |
| DB access | psycopg2 (raw SQL), synchronous, connection-per-operation — no ORM |
| Database | PostgreSQL 16 |
| AI / Voice | Python 3.11, FastAPI, Anthropic SDK, Claude Haiku |
| Telephony | Twilio Voice, TwiML, Polly.Joanna-Neural TTS |
| Auth | JWT (role + name embedded in token) |
| Infra | Docker, Docker Compose |

---

## Directory Structure

```
HVAC_JS_PY/
├── backend/               Python FastAPI REST API + python-socketio
│   ├── main.py            FastAPI + Socket.IO ASGI bootstrap, error handlers
│   ├── config/settings.py Pydantic Settings (env vars)
│   ├── db/connection.py   psycopg2 connection helper
│   ├── auth/              security.py (JWT + bcrypt), dependencies.py (FastAPI Depends)
│   ├── sockets/manager.py python-socketio AsyncServer + emit_* helpers + event handlers
│   ├── routers/           auth, jobs, dispatches, techs, faq, internal (thin, call services/)
│   ├── models/            Pydantic request schemas
│   ├── services/          Business logic + raw SQL (sql_fragments.py holds shared JOIN projections)
│   └── seed.py            Seeds DB from seed_data/*.json
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
- AI service: http://localhost:8001 (mapped from container port 8000 — remapped locally to avoid a port clash with another project; see `docker-compose.yml`)
- Postgres: localhost:5433 (mapped from container port 5432, same reason)

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI + Socket.IO ASGI bootstrap |
| `backend/routers/internal.py` | ai-service → backend bridge (`POST /api/internal/jobs`) |
| `backend/sockets/manager.py` | Socket.IO server, room join/auth, emit_* helpers |
| `backend/services/jobs_service.py` | Jobs business logic (largest service module) |
| `ai-service/services/ai_agent.py` | Claude API call + tool-use loop |
| `ai-service/prompts/system_prompt.txt` | Claude system prompt (has `{placeholder}` substitution) |
| `ai-service/services/job_creator.py` | Direct DB insert (psycopg2) |
| `frontend/src/stores/jobs.store.js` | Job state + Socket.IO handlers |
| `frontend/src/views/DispatchBoardView.vue` | Dispatch kanban UI |

---

## Conventions

- **DB schema change**: Hand-written SQL migration file in `database/migrations/` (auto-run by Postgres on first container start via `docker-entrypoint-initdb.d`). No ORM, no migration tool — the schema is plain SQL (see `database/migrations/001_init.sql`).
- **Auth**: JWT w/ role embedded. Backend `auth/dependencies.py` (`get_current_user`, `require_admin`, `require_admin_or_dispatcher`) extract the user via `Depends()`. Role: `admin`, `dispatcher`, `tech`.
- **Real-time**: Backend emits Socket.IO events via `sockets/manager.py` helpers (`job:created`, `dispatch:new`, `emergency:alert`). Vue store subscribes in `useSocket.js`. Uses `python-socketio` (ASGI), protocol-compatible with the frontend's `socket.io-client` — no frontend changes needed when touching backend sockets.
- **Vue state**: Pinia store only. No Vuex, no local component state for shared data.
- **AI response**: Claude must return JSON match `AIResponse` schema. Tool call happen before final JSON output.
- **DB connection Python**: psycopg2 synchronous, new connection per operation (same pattern in both `backend/db/connection.py` and `ai-service/services/job_creator.py`). Close in `finally`. No ORM/SQLAlchemy — shared multi-table SELECTs live in `backend/services/sql_fragments.py`.
- **Backend error shape**: All backend errors return `{"error": "message"}` (not FastAPI's default `{"detail": ...}`) — enforced by the exception handlers in `main.py` — because the frontend reads `err.response.data.error`. Raise `HTTPException(status_code=..., detail="...")` as usual; the handler reshapes it.
- **System prompt placeholder**: `{business_name}`, `{business_phone}`, `{service_area}`, `{business_hours}`, `{emergency_hours}` — substitute in `ai_agent._build_system_prompt()`.

---

## Common Tasks

### Add backend route
1. Add business logic as a function in `backend/services/`
2. Add the path operation in `backend/routers/` calling that function
3. Router is auto-registered via `app.include_router(...)` in `backend/main.py` (add it there if it's a new router module)

### Update AI system prompt
Edit `ai-service/prompts/system_prompt.txt`. Placeholder substitute at runtime.

### Add Claude tool (function calling)
1. Add tool handler in `ai-service/services/`
2. Register tool definition in `ai_agent.py` `_TOOLS` list
3. Add dispatch branch in `_handle_tool_call()` in `ai_agent.py`
4. Add trigger instruction to `system_prompt.txt`

### Run DB migrations
Add a new numbered `.sql` file to `database/migrations/` and apply it manually against the running Postgres container (that directory only auto-runs on a *fresh* volume):
```bash
docker compose exec -T postgres psql -U hvac_user -d hvac_db < database/migrations/00X_description.sql
```

### Seed the database
```bash
docker compose exec backend python seed.py
```

---

## Environment Variables (`.env` at root)

Key var use across service:

| Var | Used by |
|-----|---------|
| `DB_HOST/PORT/NAME/USER/PASSWORD` | psycopg2, both backend and ai-service |
| `ANTHROPIC_API_KEY` | ai-service |
| `TWILIO_*` | ai-service |
| `JWT_SECRET` | backend |
| `BACKEND_URL` | ai-service → backend bridge |
| `INTERNAL_API_SECRET` | ai-service → backend bridge auth |

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

Active status (tech busy): `sent`, `acknowledged`, `en_route`, `on_site`