# COBOL Samples

Dataset untuk testing parser dan pipeline.

## Struktur

```
samples/
├── fixed_format/    — program COBOL fixed-format (kolom 1-72)
├── free_format/     — program COBOL free-format (modern)
├── with_copybook/   — program yang pakai COPY statement
└── complex/         — program dengan COMP-3, REDEFINES, CALL, OCCURS
```

## Cara Mendapatkan Samples

### Open Mainframe Project (Rekomendasi Utama)
```
https://github.com/openmainframeproject/cobol-programming-course
```
Download folder `COBOL-programming-course-2.0/Labs/` — berisi puluhan program nyata.

### IBM Z Learning
```
https://github.com/IBM/IBM-Z-zOS
```

### Rosetta Code
Banyak implementasi algoritma dalam COBOL:
```
https://rosettacode.org/wiki/Category:COBOL
```

## Minimum untuk Parser PoC (Fase 0)

Sebelum memilih parser (lark vs ANTLR4), pastikan ada minimal:

| File | Kategori | Tujuan |
|---|---|---|
| `fixed_format/hello.cbl` | fixed-format sederhana | baseline |
| `fixed_format/calc.cbl` | fixed-format dengan kondisi IF | kondisi dasar |
| `free_format/simple.cbl` | free-format sederhana | validasi free-format |
| `with_copybook/customer.cbl` + `copybooks/CUSTMAST.cpy` | COPY statement | resolver |
| `complex/interest.cbl` | COMP-3, REDEFINES, CALL | edge cases kritis |

Tambahkan file ke folder yang sesuai dan update tabel ini.
