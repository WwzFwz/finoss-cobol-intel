# Artifact Example

This document provides a brief example of the artifacts produced by
`cobol-intel` after a single analysis run.

The purpose is not to document every field exhaustively, but to give a
publish-ready overview for prospective users, recruiters, or integrators
who want to quickly understand the output.

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

Example root artifact:

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

Excerpt from `ast/payment.json`:

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

Excerpt from `rules/payment.json`:

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

Excerpt from `graphs/call_graph.json`:

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

This output model is deliberately stable and versioned so that:

- analysis results can be re-consumed without rerunning the parser
- a GUI or API can later read the same artifacts
- regression tests can ensure parser changes remain safe
- the LLM layer gets traceable and auditable input
