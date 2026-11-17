# Library API
## by Nadiia Grechana

A small library backend built with FastAPI, SQLAlchemy, Alembic, and PostgreSQL. Built as a first part of the project for subject "Programiranje za Web" at University of Zadar.

## Requirements

- Python 3.11 or newer
- Docker Desktop with Docker Compose
- [`uv`](https://docs.astral.sh/uv/)

## Run locally (PowerShell)

Run these commands from the project root:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
docker compose up -d db
Set-Location api
uv venv
uv pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

The API is at <http://127.0.0.1:8000> and the interactive endpoint list is at
<http://127.0.0.1:8000/docs>.

## Demo accounts

The seed script creates accounts only when their email is not already in the
database. It also adds three sample books if their ISBNs are not present. It is
safe to run more than once; existing accounts are not reset or overwritten.

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `demo-admin-password` |
| User | `reader@example.com` | `demo-reader-password` |

These credentials are for local development only. Change them in `.env` before
running the seed script if the database will be accessible to anyone else.

To add the starter data again after starting the database and applying
migrations, run from the `api` directory:

```powershell
python -m app.seed
```

## Configuration

`.env` contains local settings and is ignored by Git. `.env.example` documents
the required database and JWT settings plus optional demo account credentials.
The database settings must match `docker-compose.yml`.

## Database migrations

Run Alembic commands from the `api` directory:

```powershell
alembic current
alembic upgrade head
alembic downgrade -1
```

The last command rolls back one migration; use it only when you intend to
reverse the latest schema change.

