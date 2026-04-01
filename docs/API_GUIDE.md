# API Guide

`cobol-intel` includes an optional versioned REST API for consuming analysis
artifacts and, when desired, triggering runs. Install with:

```bash
pip install cobol-intel[api]
```

## Starting the Server

```bash
cobol-intel-api
# or
uvicorn cobol_intel.api.app:app --host 0.0.0.0 --port 8000
```

OpenAPI docs available at: `http://localhost:8000/api/v1/docs`

The API is read-heavy by design: most endpoints serve manifests, artifacts, and
audit logs, while run-triggering endpoints are explicit `POST` calls.

## Endpoints

### Health & Version

```bash
# Health check
curl http://localhost:8000/api/v1/health
# {"status": "ok"}

# Version
curl http://localhost:8000/api/v1/version
# {"version": "0.2.0", "api_version": "v1"}
```

### List Runs

```bash
curl http://localhost:8000/api/v1/runs?output_dir=artifacts
```

Response:

```json
{
  "runs": [
    {
      "run_id": "run_20260401_001",
      "project_name": "samples",
      "status": "completed",
      "started_at": "2026-04-01T10:00:00Z",
      "artifacts_dir": "artifacts/samples/run_20260401_001",
      "program_count": 5,
      "error_count": 0
    }
  ],
  "total": 1
}
```

### Get Run Detail

```bash
curl http://localhost:8000/api/v1/runs/run_20260401_001?output_dir=artifacts
```

### Trigger Analysis

```bash
curl -X POST http://localhost:8000/api/v1/runs/analyze \
  -H "Content-Type: application/json" \
  -d '{"path": "samples/", "output_dir": "artifacts"}'
```

### Trigger Explain

```bash
curl -X POST http://localhost:8000/api/v1/runs/explain \
  -H "Content-Type: application/json" \
  -d '{
    "path": "samples/complex/payment.cbl",
    "output_dir": "artifacts",
    "model": "claude",
    "mode": "technical"
  }'
```

### Retrieve Artifacts

```bash
# Get specific artifact
curl http://localhost:8000/api/v1/runs/run_20260401_001/artifacts/ast/payment_ast.json \
  --output payment_ast.json

# Get audit log
curl http://localhost:8000/api/v1/runs/run_20260401_001/audit-log
```

## Error Responses

All errors follow a consistent shape:

```json
{
  "error_code": "E1001",
  "message": "Parse failed",
  "detail": "Syntax error at line 42"
}
```

Error code prefixes:

| Prefix | Domain |
|--------|--------|
| E1xxx | Parser |
| E2xxx | Analysis |
| E3xxx | LLM |
| E4xxx | Impact |
| E5xxx | I/O |
| E6xxx | Config |

## Docker

```bash
docker-compose up -d
curl http://localhost:8000/api/v1/health
```

For full on-prem with Ollama:

```bash
docker-compose --profile ollama up -d
```
