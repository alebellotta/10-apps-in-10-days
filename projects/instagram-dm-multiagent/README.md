# Instagram DM Multi-Agent MVP

## Project Tree

```text
instagram-dm-multiagent/
  app/
    agents/
    api/routes/
    core/
    dashboard/
    db/
    domain/
    integrations/
    orchestration/
    services/
    workers/
    main.py
  alembic/
  docker/
  scripts/
  tests/
  .env.example
  docker-compose.yml
  Dockerfile
  requirements.txt
```

## Architecture

This MVP receives Instagram webhook events, stores them in PostgreSQL, pushes event ids to Redis, processes them through a LangGraph workflow, stores conversation state, auto-sends safe replies, and escalates uncertain or sensitive cases to a minimal dashboard.

Core components:

- FastAPI for webhook intake, internal APIs, and dashboard pages
- LangGraph for multi-agent routing
- SQLAlchemy 2.x with async sessions for persistence
- Redis queue for background event processing
- OpenAI adapter with mock fallback for local runs
- Meta Graph API adapter with stubbed delivery when credentials are missing

## Local Setup

This project now runs locally without Docker by default.

1. Copy environment variables:

```bash
cp .env.example .env
```

2. Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Start the app:

```bash
uvicorn app.main:app --reload --port 8001
```

4. Seed demo KB data:

```bash
python scripts/seed_demo.py
```

The app is available at [http://localhost:8001](http://localhost:8001). The dashboard is at [http://localhost:8001/dashboard/threads](http://localhost:8001/dashboard/threads).

## Docker Setup

If you want the Postgres and Redis stack, use Docker:

```bash
docker compose up --build
```

Apply migrations if you want Alembic-managed schema setup:

```bash
docker compose exec app alembic upgrade head
```

Seed demo KB data:

```bash
docker compose exec app python scripts/seed_demo.py
```

## Environment Variables

Key settings:

- `APP_ENV`, `APP_HOST`, `APP_PORT`, `LOG_LEVEL`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`
- `OPENAI_API_KEY`, `OPENAI_MODEL`, `LLM_PROVIDER`
- `META_APP_SECRET`, `META_VERIFY_TOKEN`, `META_PAGE_ACCESS_TOKEN`, `META_GRAPH_API_VERSION`
- `DEFAULT_AUTO_REPLY_MODE`, `QUEUE_MODE`, `WORKER_ENABLED`

Safe local defaults:

- `LLM_PROVIDER=mock`
- `DATABASE_URL=sqlite+aiosqlite:///./local.db`
- `QUEUE_MODE=inline`
- empty Meta token values will keep message delivery stubbed

## Webhook Flow

`GET /webhooks/meta/instagram`

- verifies the Meta challenge using `hub.mode`, `hub.verify_token`, and `hub.challenge`

`POST /webhooks/meta/instagram`

- validates the optional `X-Hub-Signature-256`
- normalizes Instagram DM payloads
- deduplicates `incoming_events`
- enqueues event ids for processing

Worker flow:

1. Load event from `incoming_events`
2. Upsert thread and inbound message
3. Run LangGraph nodes:
   - `load_context_node`
   - `classifier_node`
   - `retrieval_node`
   - `policy_node`
   - `draft_node`
   - `critic_node`
   - `escalation_node` or `dispatch_node`
   - `persist_node`
4. Store conversation state and audit logs

## Internal APIs

- `GET /health`
- `GET /threads`
- `GET /threads/{thread_id}`
- `GET /threads/{thread_id}/messages`
- `GET /escalations`
- `POST /threads/{thread_id}/approve-draft`
- `POST /threads/{thread_id}/send-manual-message`
- `POST /threads/{thread_id}/retry-processing`
- `PATCH /threads/{thread_id}/mode`
- `GET /kb`
- `POST /kb`
- `PATCH /kb/{id}`
- `DELETE /kb/{id}`

## Testing

Run the full suite:

```bash
pytest
```

The tests use SQLite, inline queue mode, mock LLM behavior, and stubbed Meta delivery.

## Meta Developer App Setup

1. Create a Meta developer app with Instagram messaging permissions.
2. Configure the webhook callback URL to `/webhooks/meta/instagram`.
3. Set the verify token in Meta to match `META_VERIFY_TOKEN`.
4. Add `META_APP_SECRET` and `META_PAGE_ACCESS_TOKEN` to `.env`.
5. Expose local development with ngrok or Cloudflare Tunnel.

Example with ngrok:

```bash
ngrok http 8000
```

Use the generated HTTPS URL as the webhook callback.

## Current MVP Limits

- Retrieval is keyword-based, not vector search
- Delivery is stubbed unless real Meta credentials are provided
- Mock LLM mode is heuristic, intended for safe local execution
- Dashboard is intentionally minimal and server-rendered
- Basic in-memory rate limiting is single-process only

## Forward Design

The codebase is structured to extend toward:

- multi-account and multi-tenant support
- WhatsApp and Messenger channels
- pgvector or external vector stores
- CRM integrations
- analytics and agent evaluation
- prompt A/B testing
- assignment rules and quiet hours
