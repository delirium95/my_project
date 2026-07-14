# Boutique API

The backend follows clean (hexagonal) architecture. Dependencies point inward:

```text
presentation (FastAPI) → application (use cases, ports) → domain (business models)
                                 ↑
               infrastructure (PostgreSQL, Redis, JWT, PostHog, Sentry)
```

`src/boutique/bootstrap/container.py` is the composition root; all external adapters
are assembled there. HTTP routers never import SQLAlchemy or Redis directly.

## Local stack

```bash
cp .env.example .env
uv sync --all-groups
docker compose -f ../docker-compose.yml up -d postgres redis
uv run alembic upgrade head
uv run fastapi dev --entrypoint boutique.main:app --reload-dir src
```

Postgres is exposed on port `5433` and Redis on `6380`, avoiding common local-service
collisions. The API docs are at <http://127.0.0.1:8000/docs>.

## Authentication

The current adapter is local email/password authentication with short-lived HS256 access
JWTs and rotating refresh JWTs. Refresh tokens are kept only in an HttpOnly cookie and
their revoked IDs are stored in Redis. Set a strong `JWT_SECRET` and `COOKIE_SECURE=true`
outside local development. The domain `TokenService` port lets a future Auth0 adapter
replace this infrastructure without changing HTTP handlers or use cases.

The public auth endpoints are `POST /api/v1/auth/register`, `login`, `refresh`, and
`logout`; `GET /api/v1/auth/me` and every dashboard endpoint require a bearer access token.

## Quality checks

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest
```

The integration suite uses the actual Postgres and Redis containers. It creates only
`integration-*@example.com` users, removes those users during teardown, and reserves
Redis database `15` exclusively for its disposable cache and refresh-token data:

```bash
RUN_INTEGRATION_TESTS=1 uv run pytest -m integration
```

## Caching

Dashboard read models use cache-aside Redis caching with versioned keys and a short TTL.
The data-import command invalidates the `dashboard:v1:*` namespace after a successful
dataset refresh, so stale aggregates are never silently kept after an import.

## Deployment shape

The intended AWS cloud shape is CloudFront + private S3 static hosting → Lambda Function URL/FastAPI → RDS
PostgreSQL and ElastiCache Redis inside a VPC. The app currently ships with its local JWT
adapter; Auth0 can be introduced as a second `TokenService` implementation. Set
`SERVERLESS=true` in Lambda to use SQLAlchemy `NullPool`, which prevents connection-pool
exhaustion during scaling. See [../docs/cloud-deployment.md](../docs/cloud-deployment.md) for
the deployment walkthrough and the SAM template.

`boutique.lambda_handler.handler` is a Mangum handler for API Gateway or a Lambda Function
URL. Its lifespan is off so a warm invocation can reuse initialized clients; use the
serverless database configuration above. A portable container image is also available for
Render, Railway, Fly, or Cloud Run:

```bash
docker build -t boutique-api -f backend/Dockerfile backend
docker run --rm -p 8000:8000 --env-file backend/.env boutique-api
```

## Seed the Olist dataset

After setting `KAGGLE_USERNAME` and `KAGGLE_KEY` in `.env`, a signed-in user can
import the official Olist Kaggle archive from the dashboard. The API downloads it
server-side and accepts only the four required CSV files. The import button requires
explicit confirmation before replacing existing data.

Download and extract the Olist Brazilian E-Commerce dataset, then point the seed command
at the folder containing its four core CSV files. The command is intentionally destructive
only when `--replace` is explicit.

```bash
uv run python -m boutique.commands.seed_olist /path/to/olist-csvs
uv run python -m boutique.commands.seed_olist /path/to/olist-csvs --replace
```

The import runs in one database transaction, loads rows in batches, and invalidates the
versioned dashboard Redis namespace only after that transaction succeeds.
