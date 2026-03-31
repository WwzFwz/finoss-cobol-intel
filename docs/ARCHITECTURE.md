# Architecture Deep Dive

Dokumen ini menjelaskan keputusan arsitektur dan alasan di baliknya.

---

## Kenapa Static Analysis Dulu, Bukan Langsung LLM

LLM tanpa preprocessing pada COBOL memiliki masalah fundamental:

| Masalah | Dampak | Solusi di project ini |
|---|---|---|
| COPYBOOK tidak resolved | LLM tebak isi struktur data | Resolver sebelum LLM |
| CALL ke program lain tidak diketahui | Analisis tidak lengkap | Call graph builder |
| Program > 10k baris | Melebihi context window | Smart chunking dengan konteks |
| COMP-3 / packed decimal | Sering salah interpretasi | Type-aware AST |
| Variabel dengan nama tidak deskriptif | LLM tidak bisa infer arti | Enrichment dari context sekitar |

Kesimpulan: **LLM hanya digunakan setelah data sudah bersih dan terstruktur.**

---

## Pluggable Model Architecture

```python
# Interface yang harus diimplementasikan semua model backend
class LLMBackend(ABC):
    @abstractmethod
    def explain(self, context: COBOLContext, mode: ExplanationMode) -> str:
        pass

    @abstractmethod
    def extract_rules(self, procedure_ast: AST) -> list[BusinessRule]:
        pass

# Implementasi
class ClaudeBackend(LLMBackend): ...
class OllamaBackend(LLMBackend): ...
class FineTunedCOBOLBackend(LLMBackend): ...
```

Pengguna memilih backend via config atau flag:
```bash
cobol-intel analyze program.cbl --model claude
cobol-intel analyze program.cbl --model ollama:codellama
cobol-intel analyze program.cbl --model local:/path/to/model
```

---

## COBOL AST Structure

```json
{
  "program_id": "CALCINT",
  "divisions": {
    "data": {
      "working_storage": [
        {
          "level": "01",
          "name": "WS-ACCOUNT-DATA",
          "type": "group",
          "children": [
            {
              "level": "05",
              "name": "WS-BALANCE",
              "pic": "9(7)V99",
              "usage": "COMP-3",
              "resolved_type": "packed_decimal",
              "bytes": 5
            }
          ]
        }
      ]
    },
    "procedure": {
      "paragraphs": [
        {
          "name": "CALC-INTEREST",
          "statements": [...],
          "conditions": [...],
          "calls": ["VALIDATE-ACCOUNT", "APPLY-RATE"]
        }
      ]
    }
  },
  "copybooks_used": ["CUSTMAST", "ACCTTYPE"],
  "programs_called": ["VALIDATE-ACCOUNT", "APPLY-RATE", "LOG-TRANSACTION"],
  "files_accessed": ["ACCOUNT-FILE", "AUDIT-LOG"]
}
```

---

## Smart Chunking Strategy

Untuk program besar yang melebihi context window LLM:

```
Program COBOL (50,000 baris)
         │
         ▼
   Divide by paragraph/section boundary (bukan potong sembarangan)
         │
         ▼
Setiap chunk mendapat "envelope":
  - Global data definitions yang relevan
  - Summary program secara keseluruhan
  - Paragraf yang dipanggil oleh chunk ini
         │
         ▼
LLM analisis per chunk dengan konteks yang cukup
         │
         ▼
Merge & deduplicate hasil
```

---

## Business Rules Output Format

```json
{
  "rule_id": "BR-047",
  "source": {
    "file": "CALCINT.cbl",
    "paragraph": "APPLY-PREMIUM-RATE",
    "lines": "247-263"
  },
  "conditions": [
    {"field": "WS-ACCOUNT-TYPE", "operator": "=", "value": "SAV"},
    {"field": "WS-BALANCE", "operator": ">", "value": 10000},
    {"field": "WS-TENURE-YEARS", "operator": ">=", "value": 2}
  ],
  "action": "PERFORM APPLY-PREMIUM-RATE",
  "description": "Nasabah mendapat premium rate jika tipe akun Savings, saldo di atas 10.000, dan masa keanggotaan minimal 2 tahun",
  "risk_level": "high"
}
```

---

## On-Premise Deployment

Untuk bank yang tidak bisa kirim kode ke cloud:

```
┌─────────────────────────────────┐
│         Bank's Server           │
│                                 │
│  ┌───────────────────────────┐  │
│  │   cobol-intel (Docker)    │  │
│  │                           │  │
│  │  Static Analysis Pipeline │  │
│  │           +               │  │
│  │  Ollama + Local LLM       │  │
│  └───────────────────────────┘  │
│                                 │
│  COBOL files tidak keluar       │
│  dari server bank               │
└─────────────────────────────────┘
```

Tidak ada data yang keluar. Semua berjalan di infrastruktur bank sendiri.
