# --- Build stage ---
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src/ src/
COPY config/ config/

RUN pip install --no-cache-dir --prefix=/install ".[api]"

# --- Runtime stage ---
FROM python:3.11-slim

LABEL maintainer="WwzFwz" \
      description="COBOL Intelligence Platform — static analysis + LLM for legacy COBOL"

RUN groupadd --gid 1000 cobol && \
    useradd --uid 1000 --gid cobol --create-home cobol

COPY --from=builder /install /usr/local
COPY config/ /app/config/

WORKDIR /app
RUN mkdir -p /app/artifacts && chown -R cobol:cobol /app

USER cobol

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

ENTRYPOINT ["cobol-intel"]
CMD ["--help"]
