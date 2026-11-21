# Build from the repo root: docker build -f api/Dockerfile .
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
RUN uv sync --frozen --no-dev --package iris-api --no-install-workspace

COPY common/ common/
COPY api/ api/
RUN uv sync --frozen --no-dev --package iris-api \
    && useradd --create-home --uid 10001 app
USER 10001

EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "iris_api:create_app()"]
