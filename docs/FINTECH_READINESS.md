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
- registry dan preset bisa di-load dari `config/llm_policy.json` atau path JSON kustom
- preset dasar tersedia:
  - `fast`
  - `balanced`
  - `audit`
  - `local-only`
- policy helper memberi warning jika model tidak approved atau cloud backend
  dipakai untuk workload sensitif
- strict policy mode bisa hard block request yang melanggar aturan deployment

### Cost And Reliability Guard

- token budget per explain run sekarang bisa dibatasi
- backend OpenAI, Claude, dan Ollama punya retry + timeout dasar
- explain pipeline bisa berhenti lebih awal saat budget habis

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

- API versioned yang stabil dan konsisten untuk consumer eksternal
- webhook / event forwarding ke SIEM atau internal logging stack
- persistent project store selain filesystem artifact layout

### Operational Controls

- circuit breaker policy
- observability dashboard untuk latency, failure rate, dan token usage

### Data Protection

- field-level classifier yang lebih akurat
- configurable redaction policy per tenant / per project yang lebih kaya
- policy routing yang lebih granular dari sekadar cloud vs local

### Model Lifecycle

- model registry dengan approval owner / review date
- benchmark suite per use case bisnis
- fine-tuning / LoRA pipeline untuk self-hosted model

---

## Prioritas Implementasi Yang Disarankan

1. Konsolidasikan kontrak API: typed errors, typed manifests, pagination, dan auth boundary yang jelas
2. Circuit breaker + richer fallback policy per backend
3. Observability dashboard untuk token, latency, cache hit rate, dan failure rate
4. Sensitivity policy yang lebih granular per tenant / per project
5. Auth/RBAC jika sudah masuk multi-user deployment
