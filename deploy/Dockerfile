FROM ghcr.io/astral-sh/uv:0.10.11 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
ENV PYTHONUTF8=1 PYTHONIOENCODING=utf-8
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev
COPY db ./db
COPY scripts/download_dataset.py ./scripts/download_dataset.py
COPY eval/subset_manifest.json eval/corpus_manifest_20k.json ./eval/
COPY deploy ./deploy
EXPOSE 10000
CMD ["sh", "deploy/start.sh"]
