# Espelha o ambiente Python do Raspberry Pi OS 12 (Bookworm): Debian 12 + Python 3.11.
# Serve APENAS a camada headless (core/services/simulation/data).
# A UI (PySide6/QML) nunca roda em container - ela e validada no Pi real.
FROM python:3.11-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Camada de dependencias separada do codigo, para aproveitar cache do Docker.
COPY pyproject.toml README.md ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev]"

COPY . .

CMD ["sleep", "infinity"]
