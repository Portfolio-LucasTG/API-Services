# seeder — one-shot dataset loader

Package: `iris_seeder` (`seeder/src/iris_seeder/`), distribution name `iris-seeder`.
Entry point: `python -m iris_seeder` (also a console script `iris-seed`).
Runs once in Compose, exits `0` on success and non-zero on failure; `api` waits for it
with `depends_on: condition: service_completed_successfully`.

## What it does
1. **Resolve the source CSV**
   - If `DATASET_PATH` is set, use that file.
   - Otherwise download with `kagglehub.dataset_download(KAGGLE_DATASET)` (default `uciml/iris`)
     and use `Iris.csv` from the returned folder.
   - If the download fails and `SEED_ALLOW_FALLBACK=true`, use the vendored `seeder/data/Iris.csv`
     and log a warning. Otherwise fail.
2. **Parse and validate** every row with a Pydantic model.
   CSV header: `Id,SepalLengthCm,SepalWidthCm,PetalLengthCm,PetalWidthCm,Species`.
   Map `Iris-setosa|Iris-versicolor|Iris-virginica` → `setosa|versicolor|virginica`.
   Any invalid row aborts the run (non-zero exit) with the line number in the error.
3. **Create the table** if it doesn't exist (`Base.metadata.create_all`, from `iris_common`).
4. **Upsert** all rows by `id` (PostgreSQL `INSERT ... ON CONFLICT (id) DO UPDATE`) in one transaction.
   Running the seeder twice must leave exactly 150 rows.
5. Log a summary: rows read, rows upserted, rows per species.

## Layout
```
seeder/
  pyproject.toml
  Dockerfile
  data/Iris.csv            # vendored copy of the dataset (fallback + tests)
  src/iris_seeder/
    __main__.py            # main() -> int, sets up logging, calls run()
    config.py              # Settings: DATABASE_URL, DATASET_PATH, KAGGLE_DATASET, SEED_ALLOW_FALLBACK, LOG_LEVEL
    source.py              # resolve_dataset_path(settings) -> Path
    parsing.py             # read_rows(path) -> list[IrisRow]
    loader.py              # upsert_rows(engine, rows) -> int
  tests/
    fixtures/small.csv     # 2 rows per species
    fixtures/bad_*.csv     # invalid number, unknown species, missing column
    test_source.py         # monkeypatch kagglehub; fallback on/off; DATASET_PATH
    test_parsing.py
    test_loader.py         # integration: upsert + idempotency on PostgreSQL
    test_main.py           # exit codes
```

## Rules
- Never call the real Kaggle API in tests: monkeypatch `kagglehub.dataset_download`.
- Kaggle credentials (if ever needed) come from `KAGGLE_USERNAME` / `KAGGLE_KEY` env vars, never from files in the repo.
- The kagglehub cache lives in a named Docker volume, not in the image.
