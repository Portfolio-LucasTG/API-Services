# Build from the repo root: docker build -f seeder/Dockerfile .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependencies first (cached layer); uv needs every workspace member's pyproject.
COPY pyproject.toml uv.lock ./
COPY common/pyproject.toml common/
COPY api/pyproject.toml api/
COPY seeder/pyproject.toml seeder/
RUN uv sync --frozen --no-dev --package iris-seeder --no-install-workspace

# Editable install keeps source.VENDORED_CSV (/app/seeder/data/Iris.csv) resolvable.
COPY common/ common/
COPY seeder/ seeder/
RUN uv sync --frozen --no-dev --package iris-seeder

# kagglehub cache dir is pre-created so the named volume inherits app's ownership.
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /home/app/.cache/kagglehub \
    && chown -R app:app /home/app/.cache
USER 10001

CMD ["iris-seed"]
