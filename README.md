# Iris Explorer

Loads the [Iris Species](https://www.kaggle.com/datasets/uciml/iris) dataset into PostgreSQL
and serves it through a read-only Flask REST API.

| Service   | What it does                                          | Runs with      |
|-----------|-------------------------------------------------------|----------------|
| `db`      | PostgreSQL 17                                         | Docker Compose |
| `seeder`  | One-shot job: gets the CSV and upserts it into `iris` | Docker Compose |
| `adminer` | Web DB browser (dev only, bound to localhost)         | Docker Compose |
| `api`     | Flask REST API (read-only, gunicorn)                  | Docker Compose |

A shared library, `common/` (`iris_common`), holds the SQLAlchemy `Iris` model and the
engine/session helpers used by both the seeder and the API.

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python 3.12 is installed by uv if missing)
- Docker with Compose v2
- GNU make

## Getting started

```bash
cp .env.example .env   # adjust if needed
make setup             # Python deps (uv workspace) + git hooks
make up                # start db, run the seeder, start the api and adminer
```

After `make up`, the `iris` table holds the 150 rows (50 per species). The seeder is idempotent:
running it again (`docker compose run --rm seeder`) leaves exactly 150 rows.

| URL                                   | What                                                        |
|---------------------------------------|-------------------------------------------------------------|
| http://localhost:8081                 | Adminer (system "PostgreSQL", server `db`, user/password `iris`) |
| `localhost:5432`                      | PostgreSQL (localhost only; databases `iris` and `iris_test`) |
| http://localhost:5000/health          | API health check                                            |
| http://localhost:5000/iris/setosa     | API: list one species                                       |

## Configuration

All settings are environment variables, read from `.env` (copy [`.env.example`](.env.example)).

| Variable              | Used by     | Meaning                                                           |
|-----------------------|-------------|-------------------------------------------------------------------|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | db | Database credentials (default `iris`/`iris`/`iris`) |
| `DATABASE_URL`        | seeder, api | SQLAlchemy URL; inside Compose the host is `db`                   |
| `LOG_LEVEL`           | seeder, api | `DEBUG`, `INFO` (default), `WARNING`, ...                         |
| `KAGGLE_DATASET`      | seeder      | Kaggle dataset to download (default `uciml/iris`)                 |
| `DATASET_PATH`        | seeder      | Use this CSV (path inside the container) instead of downloading   |
| `SEED_ALLOW_FALLBACK` | seeder      | `true`: use the vendored `seeder/data/Iris.csv` if the download fails |
| `KAGGLE_USERNAME` / `KAGGLE_KEY` | seeder | Only if Kaggle asks for authentication                    |
| `DB_PORT` / `API_PORT` / `ADMINER_PORT` | Compose | Ports published on the host (5432 / 5000 / 8081) |

## How the data is loaded

The `seeder` runs once, after `db` is healthy, and exits `0` on success or `1` on failure:

1. **Source:** `DATASET_PATH` if set; otherwise download with kagglehub (cached in the
   `kagglehub-cache` volume); if that fails and `SEED_ALLOW_FALLBACK=true`, the vendored
   `seeder/data/Iris.csv` (with a warning).
2. **Validate** every row; a bad number, unknown species, missing column or duplicate `Id`
   stops the run with the line number in the error.
3. **Upsert** all rows by `id` in one transaction and delete rows whose `id` is no longer in the CSV,
   so the table always matches the dataset.

## Run the API

`make up` starts the `api` container (gunicorn, 2 workers) once the seeder has finished; Compose marks it
healthy when `GET /health` answers. To run it outside Docker instead (e.g. with the debugger), stop the container
and start Flask against the Compose database:

```bash
docker compose stop api
DATABASE_URL=postgresql+psycopg://iris:iris@localhost:5432/iris \
  uv run flask --app "iris_api:create_app()" run --port 5000
```

## API

Read-only, JSON only, snake_case fields. The full contract is in [`api/CLAUDE.md`](api/CLAUDE.md).

| Endpoint                         | Returns                                                          |
|----------------------------------|------------------------------------------------------------------|
| `GET /health`                    | `200 {"status": "ok"}`, or `503 {"status": "unavailable"}` if the DB is down |
| `GET /iris/<species>`            | The flowers of `setosa`, `versicolor` or `virginica`, ordered by `id` |
| `GET /iris/<species>/<id>`       | One flower; `404 not_found` if it doesn't exist or is another species |

An item:

```json
{"id": 1, "sepal_length_cm": 5.1, "sepal_width_cm": 3.5,
 "petal_length_cm": 1.4, "petal_width_cm": 0.2, "species": "setosa"}
```

### Filters

For each column `id`, `sepal_length_cm`, `sepal_width_cm`, `petal_length_cm`, `petal_width_cm`:
`<column>` (equal), `<column>_min` (≥), `<column>_max` (≤). Filters combine with AND.
`id*` values are 32-bit integers; the others are decimals with at most one decimal place (max `99.9`).

```bash
curl 'localhost:5000/iris/setosa?sepal_length_cm_min=5.5&petal_width_cm_max=0.4'
# {"items": [ ...5 items... ], "count": 5}
```

### Pagination

Opt-in: only when `page` (≥ 1, default 1) or `per_page` (1–100, default 10) is in the query.
`total` and `pages` count the filtered rows; a page past the end returns empty `items`.

```bash
curl 'localhost:5000/iris/setosa?page=1&per_page=2'
# {"items": [ ...2 items... ], "page": 1, "per_page": 2, "total": 50, "pages": 25}
```

### Errors

Every error uses the same envelope:

```bash
curl 'localhost:5000/iris/roses'
# 404 {"error": {"code": "species_not_found", "message": "Unknown species: roses"}}

curl 'localhost:5000/iris/setosa?per_page=500'
# 400 {"error": {"code": "invalid_query", "message": "Invalid query parameters",
#      "details": [{"field": "per_page", "message": "Input should be less than or equal to 100"}]}}
```

- Bad, empty or repeated params, or `_min` > `_max` → `400 invalid_query` with `details`.
- An unknown param (`?foo=1`) → the same 400, plus `supported_params`: every accepted
  param with its type and limits.
- Unknown routes → `404`, other methods than GET → `405`, unexpected errors → `500 internal_error`
  (no stack trace in the body).

## Development

| Command                 | What it does                                                    |
|-------------------------|-----------------------------------------------------------------|
| `make setup`            | Install deps and pre-commit hooks                               |
| `make format`           | ruff format + autofix                                           |
| `make check`            | Lint (ruff), type check (mypy strict) and unit tests — run before committing |
| `make test`             | Unit tests on SQLite in memory (coverage must stay ≥ 90 %)      |
| `make test-integration` | Starts `db` and runs the PostgreSQL tests against `iris_test`   |
| `make up` / `make down` / `make logs` | Docker Compose                                    |
| `make help`             | All commands                                                    |

Python is a uv workspace (`common`, `seeder`, `api`); add dependencies with
`uv add --package <member> <pkg>`. The work follows [`docs/PLAN.md`](docs/PLAN.md), one step at a time;
each service has a `CLAUDE.md` with its own rules.
