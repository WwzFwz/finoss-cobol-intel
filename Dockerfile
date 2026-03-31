FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/
COPY config/ config/

RUN pip install --no-cache-dir ".[api]"

EXPOSE 8000

CMD ["uvicorn", "cobol_intel.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
