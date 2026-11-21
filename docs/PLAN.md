# Implementation plan

Work through the steps in order, one per Claude Code session/turn (`/next-step`).
Each step ends green: `make check` passes and the "Done when" commands work.
After each step, run the `code-reviewer` agent, then commit.

---

## Step 0 — Bootstrap the workspace
Config files already exist (`CLAUDE.md`s, `.claude/`, `pyproject.toml`, `Makefile`, pre-commit, CI).

- [x] Create the three uv workspace members with `src/` layout and an empty `tests/` package each:
  - `common/` → distribution `iris-common`, package `iris_common`; deps: `sqlalchemy>=2`, `psycopg[binary]>=3`
  - `seeder/` → `iris-seeder`, package `iris_seeder`; deps: `iris-common`, `pydantic>=2`, `pydantic-settings`, `kagglehub`; script `iris-seed = "iris_seeder.__main__:main"`
  - `api/` → `iris-api`, package `iris_api`; deps: `iris-common`, `flask>=3`, `pydantic>=2`, `pydantic-settings`, `gunicorn`
  - Workspace deps via `[tool.uv.sources] iris-common = { workspace = true }`
- [x] Each package has a `py.typed` file and a trivial test (`test_import.py`) so pytest/coverage run.
- [x] `uv sync --all-packages` creates `uv.lock`; `uv run pre-commit install`.
- [x] Add a short `README.md` (what it is, `make setup`, `make up`, URLs).

**Done when:** `make setup && make check` passes; `uv run pre-commit run --all-files` passes.

---

## Step 1 — Shared model (`common`)
- [x] `iris_common/models.py`: `Base(DeclarativeBase)`, `Species(StrEnum)` = setosa/versicolor/virginica,
      `Iris` table `iris`: `id` int PK (no autoincrement — comes from the CSV),
      four `Numeric(3, 1)` non-null columns, `species` `String(16)` non-null + index,
      `CheckConstraint` on species values.
- [x] `iris_common/db.py`: `make_engine(url: str) -> Engine`, `make_session_factory(engine) -> sessionmaker[Session]`.
- [x] Tests (SQLite): table creation, insert/select round-trip with `Decimal`, species check constraint rejects bad value.
- [x] Integration test fixture in `common/tests/conftest.py` (re-usable pattern): `pg_engine` that skips when
      `TEST_DATABASE_URL` is unset, creates tables, and drops them after the session.

**Done when:** `make check` passes.

---

## Step 2 — Seeder: parsing and source resolution
- [x] Download the dataset once on your machine and vendor it:
      `uv run --with kagglehub python -c "import kagglehub; print(kagglehub.dataset_download('uciml/iris'))"`
      then copy `Iris.csv` to `seeder/data/Iris.csv`. *(Manual step for the developer — Claude asks.)*
- [x] `config.py` (`Settings` via pydantic-settings), `parsing.py` (`IrisRow` model + `read_rows`),
      `source.py` (`resolve_dataset_path`) exactly as described in `seeder/CLAUDE.md`.
- [x] Test fixtures: `small.csv` (2 rows per species), `bad_number.csv`, `bad_species.csv`, `missing_column.csv`.
- [x] Tests: species mapping; each bad file raises an error that names the line; `DATASET_PATH` wins;
      kagglehub success path (monkeypatched to return a tmp dir); download failure with fallback on → vendored file;
      fallback off → error; the vendored file has 150 rows, 50 per species.

**Done when:** `make check` passes.

---

## Step 3 — Seeder: loading + database container
- [x] `loader.py`: `upsert_rows(engine, rows) -> int` with `sqlalchemy.dialects.postgresql.insert(...).on_conflict_do_update`,
      one transaction, `create_all` first; in the same transaction delete ids not in `rows` (empty `rows` keeps the table).
      `read_rows` rejects a duplicate `Id` with its line number.
- [x] `__main__.py`: `main() -> int` — logging setup, run, return 0/1; never raises to the top.
- [x] `docker-compose.yml` with `db` and `seeder`:
  - `db`: `postgres:17-alpine`, env from `.env`, named volume `pgdata`, healthcheck `pg_isready`,
    port `${DB_PORT}:5432`, mount `db/init/` to `/docker-entrypoint-initdb.d/`.
  - `db/init/01-test-db.sql`: `CREATE DATABASE iris_test;` (used by integration tests).
  - `seeder`: build `context: .`, `dockerfile: seeder/Dockerfile`; `depends_on: db: condition: service_healthy`;
    `restart: "no"`; named volume `kagglehub-cache` → `/home/app/.cache/kagglehub`.
  - `adminer`: `adminer:latest`, `depends_on: db: condition: service_healthy`,
    `ADMINER_DEFAULT_SERVER=db`, port `127.0.0.1:${ADMINER_PORT}:8080` (dev-only DB browser, localhost only;
    `ADMINER_PORT=8081` in `.env.example` because the frontend uses 8080). No healthcheck: nothing depends on it.
  - Add `adminer` to the services table in the root `CLAUDE.md` and its URL to `README.md`.
- [x] `seeder/Dockerfile`: `python:3.12-slim`, uv from `ghcr.io/astral-sh/uv`, `uv sync --frozen --no-dev --package iris-seeder`,
      copies `seeder/data/`, non-root user `app`, `CMD ["iris-seed"]`.
      Keep the workspace layout (`/app/seeder/src`, `/app/seeder/data`) and the editable install uv does by default:
      `source.VENDORED_CSV` is resolved relative to the package. Check with
      `docker compose run --rm seeder python -c "from iris_seeder.source import VENDORED_CSV; assert VENDORED_CSV.is_file()"`.
- [x] Tests: integration — upsert inserts 6 fixture rows; running twice keeps 6 rows; changed value is updated.
      Unit — `main()` returns 1 on parse error and on DB error (monkeypatched), 0 on success.

**Done when:** `make check` and `make test-integration` pass;
`docker compose up -d --wait db && docker compose run --rm seeder && docker compose run --rm seeder`
ends with `SELECT species, count(*) FROM iris GROUP BY 1` = 50/50/50.

---

## Step 4 — API skeleton
- [x] `create_app(settings=None, engine=None)`, `config.py`, `db.py` (scoped session per request, closed on teardown),
      `errors.py` (JSON envelope for 400/404/405/500 incl. Werkzeug `HTTPException`s), `GET /health`.
- [x] `api/tests/conftest.py`: `app` fixture on `sqlite+pysqlite:///:memory:` with `StaticPool`,
      tables created, sample rows (3 per species with distinct values); `client` fixture.
- [x] Tests: health 200; health 503 when the session raises; unknown route → 404 envelope; POST → 405 envelope;
      an unexpected exception → 500 envelope without stack trace.

**Done when:** `make check` passes.

---

## Step 5 — List and retrieve
- [x] `schemas.py`: `IrisOut` (floats in JSON), `ListResponse`.
- [x] `queries.py`: `build_list_query(species, filters)`; `routes.py`: `GET /iris/<species>` and `GET /iris/<species>/<int:id>`.
- [x] Tests: each species returns only its rows ordered by id; `count` is correct; unknown species → 404 `species_not_found`;
      retrieve OK; retrieve with an id of another species → 404 `not_found`; nonexistent id → 404.
- [x] Review fixes: species ownership in `queries.build_retrieve_query`; ids above int32 → 404 via
      `<int(max=...)>`; empty `ListQuery(extra="forbid")` + `ApiError` so unknown params → 400 `invalid_query`
      with `details` (pulled forward from Step 6).

**Done when:** `make check` passes.

---

## Step 6 — Filters
- [x] `ListQuery` Pydantic model with `extra="forbid"`: exact / `_min` / `_max` for the five columns
      (`id*` ints, others `Decimal` with max 1 decimal place); model validator for `_min > _max`.
- [x] Errors from the model validator have an empty `loc`: give them `field: "query"` in `details` and name both
      columns in the message (`id_min must be less than or equal to id_max`). Test: `?id_min=5&id_max=1` → that detail.
- [x] Translate validation errors to 400 `invalid_query` with `details`. *(Done in Step 5; Step 6 adds the fields.)*
- [x] Tests (parametrize!): exact match per column, min only, max only, min+max, combined columns,
      no match → empty list, unknown param, bad number, too many decimals, min > max.
- [x] Review fixes: decimals capped at `max_digits=3` (huge values were a 500 on PostgreSQL);
      empty values → 400 "Value must not be empty"; every `_min` > `_max` conflict reported, not just the first;
      `id*` filters limited to int32 (shared `MAX_ID`); repeated params → 400.

**Done when:** `make check` passes.

---

## Step 7 — Pagination
- [x] `page` / `per_page` in `ListQuery`; pagination only when at least one is present; `PageResponse`.
- [x] Count with `select(func.count()).select_from(subquery)` using the same filters.
- [x] Tests: no params → `ListResponse` shape; `page=1` → `per_page` 10 by default; `per_page=2` math for
      `total`/`pages`; last partial page; page past the end → empty items; `per_page=0`, `101`, `page=0` → 400;
      pagination + filters together.
- [x] An unknown query param → the 400 `invalid_query` error also carries `supported_params`
      (name → type and allowed values), generated from `ListQuery`'s JSON schema (decimal fields get a simple
      `{"type": "number", "format": "float", "decimal_places": 1}`). Document it in the contract in `api/CLAUDE.md`.
      Test: `?foo=1` returns `supported_params` with the filter and pagination params.
- [x] Review fixes: `build_list_query(species, query, order_by=None)` is unordered unless an order rule
      (`"<column>+"` / `"<column>-"`) is passed, so the count query skips sorting;
      the API passes `order_by=DEFAULT_ORDER_BY` (`"id+"`, a constant at the top of `routes.py`);
      an invalid rule raises `ValueError`. `extra` in the error envelope can't overwrite `code`/`message`/`details`.
      Tests for repeated `page`/`per_page` and for the largest page (`2147483647` → 200, empty `items`).
      On PostgreSQL the API engine uses `REPEATABLE READ`, so a page's `items` and `total` come from one snapshot
      (integration test checks `SHOW transaction_isolation`). `supported_params()` is cached.
- [x] Update `README.md` with what this step changes for users (services, URLs, endpoints, commands, env vars).

**Done when:** `make check` passes.

---

## Step 8 — API container
- [ ] `api/Dockerfile` (same pattern as seeder), `CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "iris_api:create_app()"]`.
- [ ] Compose `api`: `depends_on: seeder: condition: service_completed_successfully`,
      healthcheck with `python -c "urllib.request.urlopen('http://localhost:5000/health')"`, port `${API_PORT}:5000`.

**Done when:** `make up` then `curl localhost:5000/iris/setosa?page=1` returns 10 items and `total: 50`.

---

## Step 9 — Frontend scaffold
- [ ] `npm create vue@latest frontend` with TypeScript, Router, Vitest, ESLint, Prettier (no Pinia, no JSX, no e2e).
      Keep the existing `frontend/CLAUDE.md`.
- [ ] Ensure scripts `lint`, `format`, `format:check`, `type-check`, `test:unit` (with `--coverage`, `@vitest/coverage-v8`)
      exist; ESLint runs with `--max-warnings=0`; coverage thresholds 80 % in `vitest.config.ts`.
- [ ] `vite.config.ts` dev proxy `/api` → `http://localhost:5000` with prefix rewrite.
- [ ] Remove the scaffold's demo components/tests.

**Done when:** `make check` (now including frontend) passes; `npm run build` passes.

---

## Step 10 — Frontend API client
- [ ] `src/api/types.ts` mirroring the contract; `src/api/iris.ts` with `listIris` / `getIris`; an `ApiError` class
      carrying `status`, `code`, `message`.
- [ ] Tests: query string building (omits empty filters, adds pagination only when enabled), successful parse,
      API error envelope → `ApiError`, network failure → `ApiError` with code `network_error`.

**Done when:** `make check` passes.

---

## Step 11 — Frontend screens
- [ ] Router, `SpeciesTabs`, `IrisTable`, `IrisFilters`, `PaginationControls`, `ErrorBanner`,
      `useIrisList` (URL query ⇄ state), `SpeciesListView`, `IrisDetailView`, `NotFoundView`.
- [ ] Tests: filters apply/clear update the route query; pagination toggle and next/prev; loading/empty/error states;
      unknown species route → not found; row click navigates to detail; detail shows 404 message.

**Done when:** `make check` passes; with `make up` running the API and `npm run dev`, the UI works manually.

---

## Step 12 — Frontend container + full stack
- [ ] `frontend/Dockerfile` (node:22-alpine build → nginx:alpine), `nginx.conf` with SPA fallback and `/api/` proxy.
- [ ] Compose `frontend`: `depends_on: api: condition: service_healthy`, port `${FRONTEND_PORT}:80`.

**Done when:** `make up && make smoke` prints `smoke OK`; http://localhost:8080 works.

---

## Step 13 — Polish
- [ ] README: architecture diagram (Mermaid), endpoints with examples, dev workflow, how to run tests.
- [ ] CI green on GitHub (python, frontend, compose jobs).
- [ ] Run `code-reviewer` on the whole repo (`git diff` against the first commit) and fix findings.

**Done when:** CI is green on `main`.
