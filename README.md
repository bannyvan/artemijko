# TimeTracker Telegram WebApp

Monorepo: FastAPI + PostgreSQL backend, Vite React TS frontend, PWA with Workbox Background Sync, Telegram WebApp Auth, JWT, React Query, RHF+Zod, Sentry & OpenTelemetry.

## Quick start

1) Copy env

```bash
cp .env.example .env
# Edit BOT_TOKEN, ALLOWED_ORIGINS
```

2) Start stack

```bash
docker compose up -d --build
```

3) Apply DB migrations and seed data

```bash
make migrate
```

4) Open
- API Swagger: http://localhost:8000/docs
- Frontend: http://localhost:8080 (proxied via Nginx to frontend dev and backend API)

## Services
- reverse-proxy: Nginx on :8080
- frontend: Vite dev server on :5173
- api: FastAPI on :8000
- db: Postgres 15

## Auth via Telegram WebApp
- Frontend calls `POST /auth/telegram?initData=<raw querystring>` using `tgWebAppData` value
- Server validates HMAC-SHA256 per Telegram docs (bot token) and responds with JWT access and sets HttpOnly refresh cookie

## API Contract (selected)
- POST /auth/telegram
- POST /auth/refresh (uses HttpOnly cookie)
- GET /me
- GET /shifts?from&to&user_id?&project_id?
- POST /shifts/start (Idempotency-Key required)
- POST /shifts/pause
- POST /shifts/resume
- POST /shifts/finish (Idempotency-Key required)
- GET /shifts/:id/breaks
- POST /breaks/start
- POST /breaks/finish
- GET /reports/summary?period=day|week|month
- GET /reports/export.csv | /reports/export.xlsx
- GET /requests
- POST /requests
- PATCH /requests/:id
- GET /admin/users
- PATCH /admin/users/:id

OpenAPI: http://localhost:8000/openapi.json (make openapi to save file)

## Curl examples

Replace ACCESS with the token from /auth/telegram response.

```bash
# Telegram auth (example initData; compute real one using bot token)
curl -X POST "http://localhost:8000/auth/telegram?initData=auth_date%3D...&user%3D...&hash%3D..." -c cookies.txt

# Refresh via cookie
curl -X POST http://localhost:8000/auth/refresh -b cookies.txt

# Me
curl -H "Authorization: Bearer ACCESS" http://localhost:8000/me

# Start shift (idempotent)
IK=$(uuidgen)
curl -X POST http://localhost:8000/shifts/start -H "Authorization: Bearer ACCESS" -H "Idempotency-Key: $IK" -H 'Content-Type: application/json' -d '{"note":"Start"}'

# Pause/Resume
curl -X POST http://localhost:8000/shifts/pause -H "Authorization: Bearer ACCESS"
curl -X POST http://localhost:8000/shifts/resume -H "Authorization: Bearer ACCESS"

# Finish shift (idempotent)
IK=$(uuidgen)
curl -X POST http://localhost:8000/shifts/finish -H "Authorization: Bearer ACCESS" -H "Idempotency-Key: $IK"

# Breaks
curl -X POST http://localhost:8000/breaks/start -H "Authorization: Bearer ACCESS" -H 'Content-Type: application/json' -d '{"type":"lunch"}'
curl -X POST http://localhost:8000/breaks/finish -H "Authorization: Bearer ACCESS"

# Requests
curl http://localhost:8000/requests -H "Authorization: Bearer ACCESS"
curl -X POST http://localhost:8000/requests -H "Authorization: Bearer ACCESS" -H 'Content-Type: application/json' -d '{"type":"dayoff","from_date":"2025-01-01","to_date":"2025-01-01","days":1}'

# Reports
curl "http://localhost:8000/reports/summary?period=day" -H "Authorization: Bearer ACCESS"
curl -L "http://localhost:8000/reports/export.csv?period=day" -H "Authorization: Bearer ACCESS" -o report.csv

# Admin
curl http://localhost:8000/admin/users -H "Authorization: Bearer ACCESS"
curl -X PATCH http://localhost:8000/admin/users/1 -H "Authorization: Bearer ACCESS" -H 'Content-Type: application/json' -d '{"role":"manager"}'
```

## Business rules
- Single active shift enforced
- Breaks allowed only in active shift
- Auto-stop after MAX_SHIFT_HOURS
- Rounding to ROUNDING_MINUTES in reports
- Idempotency-Key required for start/finish
- Audit log recorded for key actions
- Rate limits: /auth (10/min), /shifts start/finish (30/min), pause/resume (60/min)

## PWA/Offline
- Workbox Background Sync queues POSTs to /shifts/* and /breaks/* in IndexedDB and replays when online

## Dev tasks
- Run tests: `make up && make test`
- Backend dev: `uvicorn app.main:app --reload`
- Frontend dev: `pnpm dev`

## ERD
DBML at `docs/schema.dbml` (use dbdiagram.io to render)

