# Iris Explorer

Docker Compose monorepo that loads the Iris Species dataset into PostgreSQL,
exposes it through a read-only REST API and shows it in a Vue.js frontend.

## Services

| Service    | Folder      | Stack                                                    | Port     |
|------------|-------------|----------------------------------------------------------|----------|
| `db`       | `db/`       | PostgreSQL 17                                            | 5432     |
| `seeder`   | `seeder/`   | Python 3.12, SQLAlchemy 2, kagglehub (one-shot job)      | —        |
| `api`      | `api/`      | Python 3.12, Flask 3, SQLAlchemy 2, Pydantic 2, gunicorn | 5000     |
| `frontend` | `frontend/` | Vue 3, TypeScript, Vite, Vue Router, nginx               | 8080     |
| (library)  | `common/`   | `iris_common`: SQLAlchemy model, engine/session helpers  | —        |

Startup order in Compose: `db` (healthy) → `seeder` (completed successfully) → `api` (healthy) → `frontend`.

The browser only talks to `frontend`; nginx (and the Vite dev server) proxy `/api/*` to the `api`
service with the `/api` prefix stripped, so the API needs no CORS.

Each service folder has its own `CLAUDE.md` with service-specific rules. **Read it before editing that service.**
The API contract lives in `api/CLAUDE.md` and is the source of truth for both `api` and `frontend`.

## How we work: the plan

The implementation follows `docs/PLAN.md`, one step at a time.

1. Read `docs/PLAN.md` and find the first step that is not ticked (`- [ ]`).
2. Do **only** that step. Do not start the next step without being asked.
3. Write the tests listed for the step together with the code.
4. Run `make check` (and any extra "Done when" command of the step). Everything must pass.
5. Tick the step's boxes in `docs/PLAN.md` and summarise what changed.

If a step turns out to be wrong or incomplete, stop and propose a change to the plan instead of improvising.

## Commands

Python uses a **uv workspace** (root `pyproject.toml`, members `common`, `api`, `seeder`).
Frontend uses **npm** inside `frontend/`.

```bash
make setup             # uv sync + pre-commit install + npm ci (if frontend exists)
make format            # ruff format + ruff check --fix (+ prettier/eslint --fix)
make lint              # ruff check, ruff format --check (+ eslint, prettier --check)
make typecheck         # mypy (strict) (+ vue-tsc)
make test              # unit tests: pytest -m "not integration" (+ vitest)
make test-integration  # starts the db container and runs pytest -m integration
make check             # lint + typecheck + test  ← run before saying a step is done
make up / down / logs  # docker compose
make smoke             # curl the running stack end to end
```

Adding dependencies:
- Python: `uv add --package iris-api flask` (never `pip install`, never edit lock files by hand).
- Dev tools for everyone: `uv add --dev <pkg>` at the root.
- Frontend: `npm --prefix frontend install <pkg>` (`-D` for dev tools).

## Conventions

### Python
- Python 3.12, `src/` layout, type hints on everything, `mypy --strict` must pass.
- ruff is the only formatter/linter (no black, isort, flake8, pylint).
- SQLAlchemy 2.0 style only: `Mapped[...]`, `mapped_column`, `select()`, `session.scalars()`. No legacy `Query` API.
- Configuration comes from environment variables only (see `.env.example`). No hard-coded credentials or hosts.
- Use `logging`, never `print` in application code.
- Small modules with one responsibility; no business logic in Flask route functions beyond parsing → querying → serialising.

### Testing
- Every feature ships with tests in the same step. Coverage must stay ≥ 90 % (enforced by pytest-cov).
- Unit tests run against SQLite in memory through the app factory / session factory. Do not mock SQLAlchemy.
- Tests that need real PostgreSQL behaviour (upsert, numeric types) are marked `@pytest.mark.integration`
  and use `TEST_DATABASE_URL`; they are skipped automatically when it is not set.
- Use small fixtures (a handful of rows per species), not the full dataset, in unit tests.
- Frontend: Vitest + @vue/test-utils. Mock `fetch`, not components.

### Git
- Conventional Commits (`feat(api): add pagination`, `test(seeder): ...`, `chore: ...`).
- One plan step = one commit (or a few small ones). Run `make check` before committing.

## Don't
- Don't read or edit `.env`; change `.env.example` instead.
- Don't relax ruff, mypy, ESLint or coverage settings to make an error go away. Fix the code.
  A per-line `# noqa: <CODE>` / `# type: ignore[<code>]` is allowed only with a short reason comment.
- Don't commit downloaded dataset caches. The only data file in git is `seeder/data/Iris.csv`.
- Don't add endpoints that write data. The API is read-only.
