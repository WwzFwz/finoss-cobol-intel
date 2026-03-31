# Suite Vision

Dokumen ini menjelaskan arah jangka panjang project sebagai fondasi untuk
finance open-source suite, tanpa memperlebar scope MVP saat ini.

Tujuan dokumen ini bukan menambah fitur baru sekarang, tetapi memastikan bahwa
keputusan teknis di modul pertama tidak tanpa sengaja mengunci arsitektur hanya
untuk use case COBOL.

---

## Long-Term Direction

Target jangka panjangnya adalah membangun kumpulan modul open-source untuk
kebutuhan finance yang memiliki pola kerja serupa:

- menerima input yang cukup terstruktur
- melakukan analisis programatik dan/atau LLM-assisted
- menghasilkan artifact yang dapat divalidasi, ditrace, dan diintegrasikan

Modul pertama adalah `cobol-intel`.

Naming kerja yang dipakai saat ini:

- repo publik: `cobol-intel`
- command line: `cobol-intel`
- Python package: `cobol_intel`

Artinya, walaupun ada visi suite jangka panjang, identitas project yang
dipublikasikan sekarang tetap konsisten sebagai `cobol-intel`.

Jika arsitekturnya terbukti sehat di modul ini, pola yang sama dapat dipakai
ulang untuk modul lain seperti:

- `regtech`
- `doc-intel`
- `aml-assist`
- `reconcile`

Daftar ini masih ilustratif, bukan komitmen roadmap.

---

## Shared Layer Yang Disepakati Sekarang

Untuk tahap saat ini, shared layer sengaja dibatasi agar tidak over-designed.
Yang boleh dianggap reusable lintas modul hanya lima hal berikut:

1. Artifact metadata dan manifest pattern
2. Run lifecycle dan status execution
3. Source reference model
4. LLM backend abstraction
5. Output formatter conventions

Penjelasan singkat:

- **Artifact metadata dan manifest pattern**
  Semua modul nanti sebaiknya menghasilkan output dengan pola manifest yang
  konsisten, termasuk `schema_version`, `run_id`, status, artifact list,
  warning, dan error.

- **Run lifecycle dan status execution**
  Lifecycle dasar seperti `queued -> running -> completed/failed` sebaiknya
  konsisten di semua modul.

- **Source reference model**
  Semua temuan atau penjelasan sebaiknya bisa menunjuk kembali ke sumbernya,
  baik itu file COBOL, dokumen, aturan regulasi, maupun dataset transaksi.

- **LLM backend abstraction**
  Integrasi model harus tetap pluggable dan tidak mengubah pipeline inti.

- **Output formatter conventions**
  Format seperti JSON, Markdown, HTML, dan Mermaid sebaiknya mengikuti pola
  yang seragam antar modul.

---

## Yang Belum Diputuskan

Hal-hal berikut sengaja belum diputuskan sekarang:

- nama suite final
- namespace suite final di atas `cobol-intel`
- monorepo layout final tingkat suite
- apakah shared code nanti dipisah ke package khusus
- shared finance domain types seperti `Money`, `DateRange`, dan sejenisnya
- modul kedua setelah `cobol-intel`

Alasan penundaan:

- kebutuhan shared layer baru akan lebih jelas setelah satu modul benar-benar berjalan
- terlalu cepat mengunci abstraksi suite bisa menghasilkan desain yang rapi di atas kertas
  tetapi tidak dipakai nyata

---

## Decision Timing

Waktu pengambilan keputusan yang disarankan:

- **Sekarang**
  Sepakati bahwa project ini harus tetap `suite-friendly`, tetapi tetap fokus
  pada `cobol-intel` sebagai modul pertama.

- **Setelah `cobol-intel` selesai Fase 0**
  Review apakah contracts, artifact model, dan service boundary sudah cukup
  reusable atau masih terlalu COBOL-specific.

- **Setelah `cobol-intel` selesai Fase 1**
  Baru putuskan:
  - nama suite
  - namespace package jangka panjang
  - strategi repo: tetap satu repo atau diubah menjadi monorepo formal
  - shared layer mana yang benar-benar dipromosikan jadi reusable package

---

## Explicit Constraints

Constraint ini berlaku agar visi suite tidak merusak fokus MVP:

- Tidak membuat modul baru sebelum `cobol-intel` menyelesaikan minimal Fase 1.
- Tidak menambah abstraksi shared layer baru tanpa minimal dua use case nyata.
- Tidak mengorbankan kejelasan arsitektur `cobol-intel` hanya demi hipotesis suite.
- Tidak membangun platform besar terlebih dahulu sebelum engine pertama terbukti berguna.

---

## Working Principle

Prinsip kerja untuk beberapa bulan pertama:

- bangun `cobol-intel` seolah-olah ini modul pertama dari suite
- evaluasi shared concern secara disiplin
- generalisasi hanya yang benar-benar terbukti reusable

Dengan pendekatan ini, project tetap fokus sebagai MVP yang bisa selesai, tetapi
tidak menutup jalan untuk tumbuh menjadi finance open-source suite di masa depan.
