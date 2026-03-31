# Research & Domain Knowledge

Dokumen ini berisi pengetahuan domain COBOL yang perlu dipahami sebelum
dan selama development. Update terus seiring riset berkembang.

---

## COBOL Fundamentals yang Wajib Dikuasai

### Structure Dasar Program COBOL

```cobol
IDENTIFICATION DIVISION.        -- identitas program
    PROGRAM-ID. NAMA-PROGRAM.

ENVIRONMENT DIVISION.           -- environment & file assignment
    INPUT-OUTPUT SECTION.
    FILE-CONTROL.
        SELECT file-name ASSIGN TO 'path'.

DATA DIVISION.                  -- definisi semua data
    FILE SECTION.               -- struktur file
    WORKING-STORAGE SECTION.    -- variabel sementara
    LINKAGE SECTION.            -- data dari/ke program lain (CALL)

PROCEDURE DIVISION.             -- logika program
    PARAGRAPH-NAME.
        statements.
```

### Tipe Data Kritis (Wajib Handle dengan Benar)

| PIC Clause | Arti | Contoh Value |
|---|---|---|
| `PIC 9(5)` | Integer 5 digit | 12345 |
| `PIC 9(7)V99` | Desimal, 7 digit + 2 desimal | 1234567.89 |
| `PIC X(20)` | String alphanumeric 20 char | "JOHN DOE" |
| `PIC S9(5)` | Signed integer | -12345 |
| `COMP` / `COMP-4` | Binary integer | Internal binary |
| `COMP-3` | Packed decimal | Format biner khusus |
| `COMP-5` | Native binary | Platform-dependent |

**COMP-3 (Packed Decimal)**: Ini yang paling sering salah.
Setiap byte menyimpan 2 digit desimal. Byte terakhir: 1 digit + sign (C=positive, D=negative).
Ini dipakai untuk kalkulasi keuangan karena presisi tinggi.

### COPYBOOK

File eksternal (`.cpy`) yang di-`COPY` ke dalam program.
Biasanya berisi definisi data structure yang dipakai banyak program.

```cobol
-- Di CUSTMAST.cpy:
01 CUSTOMER-RECORD.
   05 CUST-ID      PIC 9(8).
   05 CUST-NAME    PIC X(30).
   05 CUST-BALANCE PIC 9(9)V99 COMP-3.

-- Di program:
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-CUSTOMER.
   COPY CUSTMAST.   ← isi CUSTMAST.cpy di-embed di sini
```

### REDEFINES

Satu area memori diberi nama/tipe berbeda. Seperti union di C.

```cobol
01 WS-DATE-NUM    PIC 9(8).               -- 20240315
01 WS-DATE-STR REDEFINES WS-DATE-NUM.    -- area memori yang sama
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

-- Akses: WS-MONTH-AMOUNT(3) = bulan ke-3
```

### PERFORM (Loop & Subroutine Call)

```cobol
-- Loop
PERFORM CALC-INTEREST
    VARYING IDX FROM 1 BY 1
    UNTIL IDX > 12.

-- Call paragraph (seperti fungsi internal)
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
CALL WS-PROGRAM-NAME USING WS-DATA.   ← susah di-trace secara static
```

---

## JCL (Job Control Language)

JCL adalah "wrapper" yang menjalankan program COBOL di mainframe.
Tidak perlu parse JCL secara mendalam, tapi perlu mengerti:

```jcl
//CALCJOB  JOB ...
//STEP1    EXEC PGM=CALCINT          ← program COBOL yang dijalankan
//INFILE   DD   DSN=PROD.ACCOUNTS,   ← input file
//              DISP=SHR
//OUTFILE  DD   DSN=PROD.RESULTS,    ← output file
//              DISP=(NEW,CATLG)
```

Relevan untuk: tahu program mana dijalankan kapan, input/output filenya apa.

---

## Tantangan Parsing COBOL

### Fixed Format vs Free Format

**Fixed format** (COBOL lama, yang banyak di bank):
```
Kolom 1-6:   sequence number (diabaikan)
Kolom 7:     indicator (* = comment, - = continuation)
Kolom 8-11:  Area A (DIVISION, SECTION, paragraph names)
Kolom 12-72: Area B (statements)
Kolom 73-80: identification (diabaikan)
```

**Free format** (COBOL modern):
Tidak ada kolom khusus. Lebih mudah di-parse.

### Hal yang Bikin Parser Susah
- Kolom yang ketat di fixed format
- `COPY REPLACING` — substitusi teks saat copy
- Literal continuation (string panjang dipotong ke baris berikut)
- `REPLACE` statement — global text substitution
- Nested `COPY` (copybook yang copy copybook lain)

---

## Sumber Belajar & Dataset

### Belajar COBOL
- [COBOL Programming Course (Open Mainframe Project)](https://github.com/openmainframeproject/cobol-programming-course) — terbaik untuk mulai
- [IBM COBOL documentation](https://www.ibm.com/docs/en/cobol-zos)
- "Programming in COBOL" — Murach (buku, sangat praktis)

### Dataset COBOL (untuk testing & fine-tuning)
- [Open Mainframe Project GitHub](https://github.com/openmainframeproject) — ratusan program nyata
- [Rosetta Code COBOL](https://rosettacode.org/wiki/Category:COBOL) — berbagai algoritma
- [NIST COBOL Test Suite](https://www.itl.nist.gov/div897/ctg/cobol_form.htm) — conformance tests
- GitHub search: `language:COBOL` — ribuan repo

### Tools Referensi
- **GnuCOBOL** — open source COBOL compiler, bisa pelajari parser-nya
- **Eclipse COBOL plugins** — untuk memahami tooling yang ada
- **Micro Focus COBOL** — standar industri (commercial)

---

## Competitive Landscape

| Tool | Harga | Kelemahan |
|---|---|---|
| IBM watsonx Code Assistant | Enterprise, mahal | Closed, butuh IBM infrastructure |
| Micro Focus Modernization Workbench | Sangat mahal | Closed, kompleks |
| AWS Mainframe Modernization | Per-usage, cloud only | Kode harus ke AWS |
| Manual + konsultan | $200-500/jam | Lambat, tidak scalable |
| **Project ini** | Open source | — |

**Gap yang diisi**: Tool yang bisa jalan on-premise, open source, dan accessible untuk tim yang tidak punya budget enterprise.

---

## Pertanyaan Riset yang Perlu Dijawab

- [ ] Seberapa akurat LLM (Claude/GPT-4) menjelaskan COBOL tanpa preprocessing vs dengan preprocessing? (perlu benchmark)
- [ ] Grammar COBOL mana yang paling lengkap dan bisa dipakai sebagai basis? (GnuCOBOL grammar? ANTLR COBOL grammar?)
- [ ] Berapa ukuran model minimum yang masih akurat untuk COBOL explanation task?
- [ ] Apakah fine-tuning pada dataset COBOL publik meningkatkan akurasi secara signifikan?
- [ ] Format output apa yang paling berguna untuk tim bank? (survey / interview)
