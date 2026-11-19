# Iris Explorer

Loads the [Iris Species](https://www.kaggle.com/datasets/uciml/iris) dataset into PostgreSQL,
serves it through a read-only Flask REST API and shows it in a Vue.js frontend.
Everything runs with Docker Compose.

| Service    | What it does                                   |
|------------|------------------------------------------------|
| `db`       | PostgreSQL 17                                  |
| `seeder`   | One-shot job: downloads the CSV and upserts it |
| `api`      | Flask REST API (read-only)                     |
| `frontend` | Vue 3 single-page app served by nginx          |

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python 3.12 is installed by uv if missing)
- Node.js 22 + npm (frontend)
- Docker with Compose v2
- GNU make

## Getting started

```bash
cp .env.example .env   # adjust if needed
make setup             # Python + frontend deps, git hooks
make up                # build and start the stack
```

| URL                                   | What                                                    |
|---------------------------------------|---------------------------------------------------------|
| http://localhost:8080                 | Frontend                                                |
| http://localhost:8080/api/iris/setosa | API through the frontend proxy (as the browser uses it) |
| http://localhost:5000/health          | API health check (direct)                               |
| http://localhost:5000/iris/setosa     | API: list one species (direct)                          |
| http://localhost:8081                 | Adminer DB browser (dev only; server `db`, user `iris`) |

Run `make help` for all commands; `make check` runs lint, type checks and tests.
See `docs/PLAN.md` for the implementation plan and `api/CLAUDE.md` for the API contract.
