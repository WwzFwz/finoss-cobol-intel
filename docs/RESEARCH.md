# Research & Domain Knowledge

This document contains COBOL domain knowledge that must be understood before
and during development. Updated as research progresses.

---

## Essential COBOL Fundamentals

### Basic COBOL Program Structure

```cobol
IDENTIFICATION DIVISION.        -- program identity
    PROGRAM-ID. PROGRAM-NAME.

ENVIRONMENT DIVISION.           -- environment & file assignment
    INPUT-OUTPUT SECTION.
    FILE-CONTROL.
        SELECT file-name ASSIGN TO 'path'.

DATA DIVISION.                  -- all data definitions
    FILE SECTION.               -- file structures
    WORKING-STORAGE SECTION.    -- temporary variables
    LINKAGE SECTION.            -- data from/to other programs (CALL)

PROCEDURE DIVISION.             -- program logic
    PARAGRAPH-NAME.
        statements.
```

### Critical Data Types (Must Handle Correctly)

| PIC Clause | Meaning | Example Value |
|---|---|---|
| `PIC 9(5)` | 5-digit integer | 12345 |
| `PIC 9(7)V99` | Decimal, 7 digits + 2 decimal places | 1234567.89 |
| `PIC X(20)` | 20-char alphanumeric string | "JOHN DOE" |
| `PIC S9(5)` | Signed integer | -12345 |
| `COMP` / `COMP-4` | Binary integer | Internal binary |
| `COMP-3` | Packed decimal | Special binary format |
| `COMP-5` | Native binary | Platform-dependent |

**COMP-3 (Packed Decimal)**: This is the most commonly mishandled type.
Each byte stores 2 decimal digits. Last byte: 1 digit + sign (C=positive, D=negative).
Used for financial calculations due to high precision.

### COPYBOOK

External files (`.cpy`) that are `COPY`-ed into programs.
Usually contain data structure definitions shared across many programs.

```cobol
-- In CUSTMAST.cpy:
01 CUSTOMER-RECORD.
   05 CUST-ID      PIC 9(8).
   05 CUST-NAME    PIC X(30).
   05 CUST-BALANCE PIC 9(9)V99 COMP-3.

-- In program:
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-CUSTOMER.
   COPY CUSTMAST.   <- contents of CUSTMAST.cpy are embedded here
```

### REDEFINES

One memory area given different names/types. Similar to a union in C.

```cobol
01 WS-DATE-NUM    PIC 9(8).               -- 20240315
01 WS-DATE-STR REDEFINES WS-DATE-NUM.    -- same memory area
   05 WS-YEAR     PIC 9(4).              -- 2024
   05 WS-MONTH    PIC 9(2).              -- 03
   05 WS-DAY      PIC 9(2).              -- 15
```

### OCCURS (Array)

```cobol
01 WS-MONTHLY-DATA.
   05 WS-MONTH-RECORD OCCURS 12 TIMES.
      10 WS-MONTH-AMOUNT  PIC 9(9)V99.
      10 WS-MONTH-STATUS  PIC X.

-- Access: WS-MONTH-AMOUNT(3) = 3rd month
```

### PERFORM (Loop & Subroutine Call)

```cobol
-- Loop
PERFORM CALC-INTEREST
    VARYING IDX FROM 1 BY 1
    UNTIL IDX > 12.

-- Call paragraph (like an internal function)
PERFORM VALIDATE-ACCOUNT.

-- Inline loop
PERFORM UNTIL WS-EOF = 'Y'
    READ ACCOUNT-FILE
    ...
END-PERFORM.
```

### CALL (External Program)

```cobol
-- Static call (compile-time)
CALL 'CALCINT' USING WS-ACCOUNT-DATA WS-RESULT.

-- Dynamic call (runtime)
CALL WS-PROGRAM-NAME USING WS-DATA.   <- hard to trace statically
```

---

## JCL (Job Control Language)

JCL is the "wrapper" that runs COBOL programs on the mainframe.
No need to parse JCL deeply, but important to understand:

```jcl
//CALCJOB  JOB ...
//STEP1    EXEC PGM=CALCINT          <- COBOL program being executed
//INFILE   DD   DSN=PROD.ACCOUNTS,   <- input file
//              DISP=SHR
//OUTFILE  DD   DSN=PROD.RESULTS,    <- output file
//              DISP=(NEW,CATLG)
```

Relevant for: knowing which program runs when and what its input/output files are.

---

## COBOL Parsing Challenges

### Fixed Format vs Free Format

**Fixed format** (legacy COBOL, prevalent in banks):
```
Columns 1-6:   sequence number (ignored)
Column 7:      indicator (* = comment, - = continuation)
Columns 8-11:  Area A (DIVISION, SECTION, paragraph names)
Columns 12-72: Area B (statements)
Columns 73-80: identification (ignored)
```

**Free format** (modern COBOL):
No fixed columns. Easier to parse.

### What Makes Parsing Difficult
- Strict column layout in fixed format
- `COPY REPLACING` — text substitution during copy
- Literal continuation (long strings split across lines)
- `REPLACE` statement — global text substitution
- Nested `COPY` (copybooks that copy other copybooks)

---

## Learning Resources & Datasets

### Learning COBOL
- [COBOL Programming Course (Open Mainframe Project)](https://github.com/openmainframeproject/cobol-programming-course) — best starting point
- [IBM COBOL documentation](https://www.ibm.com/docs/en/cobol-zos)
- "Programming in COBOL" — Murach (book, very practical)

### COBOL Datasets (for testing & fine-tuning)
- [Open Mainframe Project GitHub](https://github.com/openmainframeproject) — hundreds of real programs
- [Rosetta Code COBOL](https://rosettacode.org/wiki/Category:COBOL) — various algorithms
- [NIST COBOL Test Suite](https://www.itl.nist.gov/div897/ctg/cobol_form.htm) — conformance tests
- GitHub search: `language:COBOL` — thousands of repos

### Reference Tools
- **GnuCOBOL** — open source COBOL compiler, can study its parser
- **Eclipse COBOL plugins** — to understand existing tooling
- **Micro Focus COBOL** — industry standard (commercial)

---

## Competitive Landscape

| Tool | Price | Weakness |
|---|---|---|
| IBM watsonx Code Assistant | Enterprise, expensive | Closed, requires IBM infrastructure |
| Micro Focus Modernization Workbench | Very expensive | Closed, complex |
| AWS Mainframe Modernization | Per-usage, cloud only | Code must go to AWS |
| Manual + consultants | $200-500/hr | Slow, not scalable |
| **This project** | Open source | — |

**Gap filled**: A tool that can run on-premise, is open source, and is accessible for teams without enterprise budgets.

---

## Research Questions To Answer

- [ ] How accurately does an LLM (Claude/GPT-4) explain COBOL without preprocessing vs with preprocessing? (needs benchmark)
- [ ] Which COBOL grammar is most complete and usable as a base? (GnuCOBOL grammar? ANTLR COBOL grammar?)
- [ ] What is the minimum model size that is still accurate for the COBOL explanation task?
- [ ] Does fine-tuning on public COBOL datasets significantly improve accuracy?
- [ ] What output format is most useful for bank teams? (survey / interview)
