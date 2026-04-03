# Fintech Readiness Checklist

This document summarizes what already exists in the repo for fintech/global
integration needs, what is still foundational, and what gaps remain.

---

## Already Available

### Traceable Artifacts

- `manifest.json`, AST, graph, rules, and explanation artifacts are versioned
- LLM output has source refs down to paragraph level and top-level summary
- run status supports `completed`, `partially_completed`, and `failed`

### Audit/Event Trail

- every analysis run now writes `logs/audit_events.jsonl`
- explain pipeline logs `started`, `completed`, and `failed` events
- events store `run_id`, actor, backend, model, file, program, and sensitivity

### Governance Summary

- manifest now carries a `governance` summary
- key fields:
  - `data_sensitivity`
  - `approved_backend`
  - `approved_model`
  - `deployment_tier`
  - `redaction_applied`
  - `token_usage`

### Model Governance

- approved model registry available for `claude`, `openai`, and `ollama`
- registry and presets can be loaded from `config/llm_policy.json` or a custom JSON path
- basic presets available:
  - `fast`
  - `balanced`
  - `audit`
  - `local-only`
- policy helper warns if model is not approved or cloud backend
  is used for sensitive workloads
- strict policy mode can hard block requests that violate deployment rules

### Cost And Reliability Guard

- token budget per explain run can now be capped
- OpenAI, Claude, and Ollama backends have basic retry + timeout
- explain pipeline can stop early when budget is exhausted

### Sensitivity Guard

- AST is analyzed to classify data as `low`, `moderate`, `high`, or `restricted`
- cloud prompts can go through redaction helper for sensitive identifiers

---

## Sufficient For

- portfolio and enterprise demo
- internal PoC
- limited pilot with human review
- initial on-prem story via `ollama`
- integration readiness discussions with engineering/security teams

---

## Not Yet Sufficient For Production Global Fintech

### Identity And Access

- platform auth
- enforceable RBAC
- multi-user approval workflow

### Enterprise Integration

- stable and consistent versioned API for external consumers
- webhook / event forwarding to SIEM or internal logging stack
- persistent project store beyond filesystem artifact layout

### Operational Controls

- circuit breaker policy
- observability dashboard for latency, failure rate, and token usage

### Data Protection

- more accurate field-level classifier
- richer configurable redaction policy per tenant / per project
- more granular policy routing beyond just cloud vs local

### Model Lifecycle

- model registry with approval owner / review date
- benchmark suite per business use case
- fine-tuning / LoRA pipeline for self-hosted model

---

## Recommended Implementation Priority

1. Consolidate API contracts: typed errors, typed manifests, pagination, and clear auth boundary
2. Circuit breaker + richer fallback policy per backend
3. Observability dashboard for tokens, latency, cache hit rate, and failure rate
4. More granular sensitivity policy per tenant / per project
5. Auth/RBAC when multi-user deployment is needed
