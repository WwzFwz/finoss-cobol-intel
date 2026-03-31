# Artifact Example

Dokumen ini memberi contoh singkat bentuk artifact yang dihasilkan
`cobol-intel` setelah satu kali run analisis.

Tujuannya bukan mendokumentasikan setiap field secara lengkap, tetapi memberi
gambaran publish-ready untuk calon pengguna repo, recruiter, atau integrator
yang ingin cepat memahami output-nya.

---

## Directory Layout

```text
artifacts/samples/run_20260331_001/
  manifest.json
  ast/
    payment.json
  graphs/
    call_graph.json
    call_graph.mmd
  rules/
    payment.json
  docs/
    payment_rules.md
    summary.md
```

---

## `manifest.json`

Contoh bentuk root artifact:

```json
{
  "schema_version": "1.0",
  "tool_version": "0.1.0",
  "run_id": "run_20260331_001",
  "project_name": "samples",
  "status": "completed",
  "started_at": "2026-03-31T10:00:00Z",
  "finished_at": "2026-03-31T10:00:06Z",
  "input_paths": ["samples"],
  "artifacts": {
    "ast": ["ast/payment.json"],
    "graphs": ["graphs/call_graph.json", "graphs/call_graph.mmd"],
    "rules": ["rules/payment.json"],
    "docs": ["docs/payment_rules.md", "docs/summary.md"]
  },
  "warnings": [],
  "errors": []
}
```

---

## AST Artifact

Potongan dari `ast/payment.json`:

```json
{
  "schema_version": "1.0",
  "program_id": "PAYMENT",
  "parser_name": "antlr4",
  "procedure_using": [],
  "copybooks_used": [],
  "paragraphs": [
    {
      "name": "VALIDATE-PAYMENT",
      "statements": [
        {
          "type": "CALL",
          "target": "DATEUTIL",
          "condition": null,
          "children": []
        },
        {
          "type": "IF",
          "target": null,
          "condition": "WS-DATE-VALID=\"N\"",
          "children": [
            {"type": "MOVE"},
            {"type": "MOVE"}
          ]
        }
      ]
    }
  ]
}
```

---

## Rules Artifact

Potongan dari `rules/payment.json`:

```json
{
  "schema_version": "1.0",
  "program_id": "PAYMENT",
  "rules": [
    {
      "rule_id": "R002",
      "type": "IF",
      "condition": "WS-DATE-VALID=\"N\"",
      "actions": ["MOVE", "MOVE", "CALL", "IF"],
      "paragraph": "VALIDATE-PAYMENT"
    },
    {
      "rule_id": "R004",
      "type": "EVALUATE",
      "condition": "EVALUATE TRUE",
      "actions": ["IF", "MOVE", "MOVE", "MOVE"],
      "paragraph": "CALCULATE-FEE"
    }
  ]
}
```

---

## Graph Artifact

Potongan dari `graphs/call_graph.json`:

```json
{
  "schema_version": "1.0",
  "nodes": ["PAYMENT", "DATEUTIL", "BALCHK"],
  "edges": [
    {"caller": "PAYMENT", "callee": "DATEUTIL", "call_type": "STATIC"},
    {"caller": "PAYMENT", "callee": "BALCHK", "call_type": "STATIC"}
  ],
  "adjacency": {
    "PAYMENT": ["BALCHK", "DATEUTIL"]
  },
  "external_calls": ["BALCHK", "DATEUTIL"]
}
```

---

## Why This Matters

Output model ini sengaja dibuat stabil dan versioned supaya:

- hasil analisis bisa dikonsumsi ulang tanpa rerun parser
- GUI atau API nanti cukup membaca artifact yang sama
- regression tests bisa menjaga perubahan parser tetap aman
- layer LLM nanti punya input yang traceable dan bisa diaudit
