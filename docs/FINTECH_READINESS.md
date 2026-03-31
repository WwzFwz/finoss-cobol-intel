# Fintech Readiness Checklist

Dokumen ini merangkum apa yang sudah ada di repo untuk kebutuhan fintech/global
integration, apa yang masih berupa fondasi, dan apa yang masih gap.

---

## Sudah Ada

### Traceable Artifacts

- `manifest.json`, AST, graph, rules, dan explanation artifacts sudah versioned
- output LLM punya source refs sampai level paragraph dan top-level summary
- run status mendukung `completed`, `partially_completed`, dan `failed`

### Audit/Event Trail

- setiap analysis run sekarang menulis `logs/audit_events.jsonl`
- explain pipeline mencatat event `started`, `completed`, dan `failed`
- event menyimpan `run_id`, actor, backend, model, file, program, dan sensitivity

### Governance Summary

- manifest sekarang membawa `governance` summary
- field utamanya:
  - `data_sensitivity`
  - `approved_backend`
  - `approved_model`
  - `deployment_tier`
  - `redaction_applied`
  - `token_usage`

### Model Governance

- approved model registry tersedia untuk `claude`, `openai`, dan `ollama`
- preset dasar tersedia:
  - `fast`
  - `balanced`
  - `audit`
  - `local-only`
- policy helper memberi warning jika model tidak approved atau cloud backend
  dipakai untuk workload sensitif

### Sensitivity Guard

- AST dianalisis untuk mengklasifikasikan data menjadi `low`, `moderate`,
  `high`, atau `restricted`
- prompt cloud bisa melalui redaction helper untuk identifier sensitif

---

## Sudah Cukup Untuk

- portfolio dan demo enterprise
- internal PoC
- pilot terbatas dengan review manusia
- on-prem story awal via `ollama`
- diskusi integration readiness dengan tim engineer/security

---

## Belum Cukup Untuk Production Global Fintech

### Identity And Access

- auth platform
- RBAC yang enforceable
- approval workflow multi-user

### Enterprise Integration

- read-only API yang stabil untuk consumer eksternal
- webhook / event forwarding ke SIEM atau internal logging stack
- persistent project store selain filesystem artifact layout

### Operational Controls

- backend timeout / retry / circuit breaker policy
- quota / budget enforcement
- observability dashboard untuk latency, failure rate, dan token usage

### Data Protection

- field-level classifier yang lebih akurat
- configurable redaction policy per tenant / per project
- policy routing yang enforce local-only, bukan sekadar warning

### Model Lifecycle

- model registry dengan approval owner / review date
- benchmark suite per use case bisnis
- fine-tuning / LoRA pipeline untuk self-hosted model

---

## Prioritas Implementasi Yang Disarankan

1. Read-only API untuk consume artifacts dan audit logs
2. Retry/timeout/fallback policy per backend
3. Token budget + quota policy
4. Sensitivity policy yang bisa enforce local-only
5. Auth/RBAC jika sudah masuk multi-user deployment

