# Тайм‑трекер (Telegram WebApp)

Монорепозиторий: бэкенд FastAPI + PostgreSQL, фронтенд Vite/React/TS, PWA с Workbox Background Sync, авторизация через Telegram WebApp initData → JWT, React Query, RHF+Zod, Sentry и OpenTelemetry.

## Быстрый старт

1) Скопируйте окружение

```bash
cp .env.example .env
# Укажите BOT_TOKEN и ALLOWED_ORIGINS
```

2) Поднимите сервисы

```bash
docker compose up -d --build
```

3) Примените миграции и сид‑данные

```bash
make migrate
```

4) Откройте
- Swagger: http://localhost:8000/docs
- Фронтенд (через Nginx): http://localhost:8080

## Сервисы
- reverse-proxy: Nginx на :8080
- frontend: Vite dev сервер на :5173
- api: FastAPI на :8000
- db: Postgres 15

## Авторизация через Telegram WebApp
- Фронт отправляет `POST /auth/telegram?initData=<сырой querystring>` (используйте `tgWebAppData`)
- Сервер валидирует HMAC-SHA256 (BOT_TOKEN), возвращает JWT access и ставит HttpOnly refresh cookie

## API (основные)
- POST /auth/telegram — вход по initData
- POST /auth/refresh — обновление access по cookie
- GET /me — профиль и настройки
- GET /shifts — список смен
- POST /shifts/start — старт смены (обязателен заголовок Idempotency-Key)
- POST /shifts/pause — пауза
- POST /shifts/resume — продолжение
- POST /shifts/finish — завершение смены (Idempotency-Key обязателен)
- GET /shifts/:id/breaks — перерывы смены
- POST /breaks/start — начало перерыва
- POST /breaks/finish — конец перерыва
- GET /reports/summary — сводка день/неделя/месяц
- GET /reports/export.csv | /reports/export.xlsx — экспорт
- GET /requests — заявки
- POST /requests — создать
- PATCH /requests/:id — изменить статус/комментарий
- GET /admin/users — пользователи
- PATCH /admin/users/:id — смена роли/статуса

OpenAPI: http://localhost:8000/openapi.json (`make openapi` сохранит в корень)

## Примеры curl

```bash
# Вход по Telegram (пример; реальный initData подпишите вашим BOT_TOKEN)
curl -X POST "http://localhost:8000/auth/telegram?initData=auth_date%3D...&user%3D...&hash%3D..." -c cookies.txt

# Обновление токена по cookie
curl -X POST http://localhost:8000/auth/refresh -b cookies.txt

# Профиль
curl -H "Authorization: Bearer ACCESS" http://localhost:8000/me

# Старт смены (идемпотентно)
IK=$(uuidgen)
curl -X POST http://localhost:8000/shifts/start -H "Authorization: Bearer ACCESS" -H "Idempotency-Key: $IK" -H 'Content-Type: application/json' -d '{"note":"Старт"}'

# Пауза/Продолжить
curl -X POST http://localhost:8000/shifts/pause -H "Authorization: Bearer ACCESS"
curl -X POST http://localhost:8000/shifts/resume -H "Authorization: Bearer ACCESS"

# Завершение (идемпотентно)
IK=$(uuidgen)
curl -X POST http://localhost:8000/shifts/finish -H "Authorization: Bearer ACCESS" -H "Idempotency-Key: $IK"

# Перерывы
curl -X POST http://localhost:8000/breaks/start -H "Authorization: Bearer ACCESS" -H 'Content-Type: application/json' -d '{"type":"lunch"}'
curl -X POST http://localhost:8000/breaks/finish -H "Authorization: Bearer ACCESS"

# Заявки
curl http://localhost:8000/requests -H "Authorization: Bearer ACCESS"
curl -X POST http://localhost:8000/requests -H "Authorization: Bearer ACCESS" -H 'Content-Type: application/json' -d '{"type":"dayoff","from_date":"2025-01-01","to_date":"2025-01-01","days":1}'

# Отчёты
curl "http://localhost:8000/reports/summary?period=day" -H "Authorization: Bearer ACCESS"
curl -L "http://localhost:8000/reports/export.csv?period=day" -H "Authorization: Bearer ACCESS" -o report.csv

# Админка
curl http://localhost:8000/admin/users -H "Authorization: Bearer ACCESS"
curl -X PATCH http://localhost:8000/admin/users/1 -H "Authorization: Bearer ACCESS" -H 'Content-Type: application/json' -d '{"role":"manager"}'
```

## Бизнес‑правила
- Одна активная смена одновременно
- Перерыв допускается только в активной смене
- Авто‑стоп по `MAX_SHIFT_HOURS`
- Округление по `ROUNDING_MINUTES` в отчётах
- Для start/finish обязателен `Idempotency-Key`
- Все ключевые действия пишутся в аудит
- Лимиты: /auth (10/мин), /shifts start/finish (30/мин), pause/resume (60/мин)

## PWA/Офлайн
- Workbox Background Sync ставит в очередь POST к /shifts/* и /breaks/* и отправляет при восстановлении сети

## Разработка
- Тесты: `make up && make test`
- Бэкенд dev: `uvicorn app.main:app --reload`
- Фронтенд dev: `pnpm dev`

## ERD
DBML в `docs/schema.dbml` (можно визуализировать в dbdiagram.io)

