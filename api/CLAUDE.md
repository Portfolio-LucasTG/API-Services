# api — Flask REST API (read-only)

Package: `iris_api` (`api/src/iris_api/`), distribution name `iris-api`.
Depends on `iris-common` for the `Iris` model and the session factory.

## Layout

```
api/
  pyproject.toml
  Dockerfile               # multi-stage, uv, runs gunicorn "iris_api:create_app()"
  src/iris_api/
    __init__.py            # create_app(config: Settings | None = None) -> Flask
    config.py              # Settings (pydantic-settings): DATABASE_URL, LOG_LEVEL
    db.py                  # session per request (teardown_appcontext closes it)
    schemas.py             # Pydantic models: IrisOut, ListQuery, Page/List responses
    queries.py             # build select() from a ListQuery; no Flask imports here
    routes.py              # Blueprint: /health, /iris/<species>, /iris/<species>/<id>
    errors.py              # error handlers -> JSON error envelope
  tests/
    conftest.py            # app/client fixtures on SQLite in memory + sample rows
    test_health.py  test_list.py  test_retrieve.py
    test_filters.py test_pagination.py test_errors.py
```

## API contract (source of truth — the frontend depends on it)

All responses are JSON. Field names are snake_case.

### Species
Path segment `<species>` is one of `setosa`, `versicolor`, `virginica`.
Any other value → **404** `species_not_found`.

### Item
```json
{"id": 1, "sepal_length_cm": 5.1, "sepal_width_cm": 3.5,
 "petal_length_cm": 1.4, "petal_width_cm": 0.2, "species": "setosa"}
```

### `GET /health`
`200 {"status": "ok"}` after a `SELECT 1`; `503 {"status": "unavailable"}` if the DB is down.

### `GET /iris/<species>` — list
Results are always ordered by `id` ascending.

**Filters** (optional, combined with AND). For each column
`id`, `sepal_length_cm`, `sepal_width_cm`, `petal_length_cm`, `petal_width_cm`:

| Param           | Meaning                  |
|-----------------|--------------------------|
| `<column>`      | equal to value          |
| `<column>_min`  | greater than or equal    |
| `<column>_max`  | less than or equal       |

- `id*` params are integers; the others are decimals with at most 1 decimal place (e.g. `5.1`).
- Unknown query params → **400** `invalid_query`.
- Values that don't parse, or `_min` > `_max` for the same column → **400** `invalid_query`.

**Pagination** is opt-in: it is applied only if `page` or `per_page` is present.
- `page`: integer ≥ 1, default `1`.
- `per_page`: integer 1–100, default **10**.
- `page` beyond the last page → `200` with empty `items`.

Response without pagination:
```json
{"items": [ ... ], "count": 50}
```
Response with pagination:
```json
{"items": [ ... ], "page": 1, "per_page": 10, "total": 50, "pages": 5}
```
(`total` and `pages` reflect the filters.)

### `GET /iris/<species>/<int:id>` — retrieve
`200` with one item. **404** `not_found` if the id doesn't exist **or belongs to another species**.

### Errors
```json
{"error": {"code": "invalid_query", "message": "human readable", "details": [ ... ]}}
```
`details` is optional (Pydantic validation errors, simplified to `{field, message}`).
Unhandled exceptions → **500** `internal_error` (logged, no stack trace in the body).
Non-GET methods → **405** with the same envelope.

## Rules
- Validate query params with a Pydantic model (`extra="forbid"`), not by hand.
- Decimal columns are `Numeric(3, 1)` in the DB; compare with `Decimal`, serialise as JSON numbers (floats).
- Keep `queries.py` free of Flask so it can be tested on its own.
- Every row of the contract above needs at least one test, including each error case.
