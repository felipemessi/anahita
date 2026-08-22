FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Instalar dependências base
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copiar arquivos do projeto e instalar deps via uv
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project
ENV PATH="/app/.venv/bin:${PATH}"

# Copiar projeto
COPY . .

# Aplica migrations e sobe o servidor (exec substitui o shell, preservando
# o encaminhamento de sinais como SIGTERM para o uvicorn)
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --root-path \"${ROOT_PATH:-}\""]
