# Report Structure Plan

This file is the section-by-section build plan for `report/main.tex`. It tells
you, for each chapter:

- what content goes in,
- which **existing project artefacts** to mine for that content
  (we have a lot of material already: `docs/*.md`, `midterm/`, the
  benchmark database, the speaker notes),
- which **figures** belong in that chapter and where they come from,
- and what we still need to **produce** before the section can be filled in.

The goal of this file is to make sure no chapter starts from a blank page.

> **Pictures**: the figures for the written chapters (Ch 3 + Ch 4) are now
> real (see the status table at the end of this file). The two pipeline
> diagrams are TikZ; the two Qiskit circuit diagrams and the Grover
> oracle-scaling plot are produced by `backend/scripts/make_report_figures.py`.
> Figures for not-yet-written chapters remain to be made when those chapters
> are drafted.

---

## Cover and Front Matter — `chapters/00_*.tex`

| File | Status | Action needed |
|---|---|---|
| `00_cover.tex` | Names filled, `[PROGRAM]` placeholders, logo missing | Drop `figures/ius_logo.png`; pick programs (CSE / SE / EE…). |
| `00_approval.tex` | Supervisor filled, co-mentor placeholder | Remove co-mentor block if not applicable. |
| `00_declaration.tex` | Done structurally; signatures on print copy | — |
| `00_copyright.tex` | Done | — |
| `00_acknowledgements.tex` | One placeholder paragraph | Write near the end. |
| `00_abbreviations.tex` | Pre-populated with project-relevant terms | Add/remove as the body stabilises. |
| `00_abstract.tex` | Placeholder, keywords pre-set | Write **last** (250–500 words). |

---

## Chapter 1 — Introduction (~600–900 words)

| Section | What it covers | Source material |
|---|---|---|
| 1.0 opening | Why cross-modal vector search matters; one paragraph framing the report. | `midterm/speaker_notes.md` slides 1–2, `docs/NOTES.md` "What This Project Does". |
| 1.1 Background | Vector search, embeddings, CLIP, quantum primitives at a high level. | `docs/THEORY.md`, `docs/QUANTUM_INTUITION.md`. |
| 1.2 Problem statement | Frame as empirical investigation, not advantage claim. | `midterm/speaker_notes.md` slide 11 (qRAM honesty). |
| 1.3 RQs + objectives | 3 research questions already drafted in the .tex file. Confirm or revise. | `docs/RESEARCH_QUESTIONS.md` (152 lines — primary source). |

**Figures**: none in this chapter.

---

## Chapter 2 — Literature Review (~800–1,200 words)

Four short sections, each one paragraph plus a citation cluster.

| Section | What it covers | Key citations (already in `references.bib`) |
|---|---|---|
| 2.1 Classical vector search | Brute force, FAISS, HNSW. | `johnson2019faiss`, `malkov2020hnsw`. |
| 2.2 Cross-modal embeddings | CLIP and contrastive learning. | `radford2021clip`. |
| 2.3 Quantum similarity | Swap test, amplitude encoding, Grover, qRAM caveat. | `grover1996`, `buhrman2001swaptest`, `giovannetti2008qram`, `aaronson2015readfine`. |
| 2.4 Hybrid architectures | Position our hybrid engine in the hybrid-retrieval landscape. | `biamonte2017qml` + at least one fresh hybrid-retrieval citation (TODO). |

**Figures**: none.

**Action items**: find one survey on hybrid quantum-classical retrieval to
cite in 2.4. Cross-check that every reference we cite is actually in the body.

---

## Chapter 3 — Research Methodology (~1,500–2,500 words)

This is the largest chapter. The structure is already in the .tex file; below
is the artefact-to-section mapping so the writer never has to invent.

| Section | Source for content | Source for figure |
|---|---|---|
| 3.1 System overview | `docs/NOTES.md` "Implementation Phases". | `figures/architecture.png` — 5-phase diagram, **needs to be drawn**. Mermaid or draw.io export both fine. |
| 3.2 Methodology diagram | Step-by-step "how we did it" walkthrough. | `figures/methodology.png` — **needs to be drawn**. Per project brief, this is required. |
| 3.3 Dataset & ground truth | Flickr30k subset, ground-truth JSONC format. | None (table only). |
| 3.4 Embedding pipeline | CLIP ViT-B/32, normalisation, truncation rationale. | Optional: `figures/clip_pipeline.png`. |
| 3.5 Search engines | One paragraph per engine, with formulas where needed. | `figures/swap_test_circuit.png` (Qiskit circuit diagram), `figures/grover_circuit.png`. Both can be rendered directly with `circuit.draw('mpl')`. |
| 3.6 Evaluation metrics | MRR formula (already in .tex), oracle calls, circuit depth, wall-clock policy. | None. |
| 3.7 Experimental configuration | Table (already in .tex) — fill from `backend/config/benchmarks.yaml`. | None. |
| 3.8 Use of AI Tools | **Mandatory** per FENS handbook §1.1. | None. |

**Action items**:
- Draw `architecture.png` and `methodology.png` (the two priority diagrams).
- Generate `swap_test_circuit.png` and `grover_circuit.png` from Qiskit's
  `circuit.draw('mpl')` once we pick a representative configuration.
- Confirm the dimension / shots table in 3.7 matches `benchmarks.yaml`
  **on the same commit** as the report.

---

## Chapter 4 — Results and Analysis (~1,500–2,500 words)

This chapter is the one that most needs **real numbers** before writing.
Process: run the benchmark harness end-to-end, dump the report, then write
prose against the actual outputs.

| Section | What it covers | Source |
|---|---|---|
| 4.0 Opening summary | Headline findings in plain English. | The numbers below. |
| 4.1 Accuracy across engines | MRR per engine, broken out by dimension. | API `/api/benchmarks` or `backend/reports/benchmark_report.md`. |
| 4.2 Quantum resource cost | Circuit depth, qubit count, oracle calls vs. theory. | Same source. Figure: `figures/oracle_scaling.png` — line plot, empirical vs. theoretical Grover oracle calls. |
| 4.3 Wall-clock behaviour | **Within-engine only.** State clearly why cross-engine wall-time is misleading. | Same source. |
| 4.4 IBM hardware sanity check | The validation run; what it does and doesn't tell us. | `backend/scripts/run_ibm_validation.py` output. |
| 4.5 Discussion | One paragraph per RQ, ending with a one-sentence answer. | Synthesised. |
| 4.6 Limitations | Small dataset, simulator-only, truncated embeddings, classically-precomputed Grover oracle. | Honest. |

**Action items**:
- Run `python3 scripts/run_benchmarks.py` end-to-end on a stable commit.
- Run `python3 scripts/generate_report.py` to dump the markdown report; copy
  the relevant tables into 4.1 and 4.2.
- Generate the oracle-call scaling figure as a quick matplotlib plot.

---

## Chapter 5 — Sustainability, Inclusivity, and Societal Impact (~200–400 words)

One or two paragraphs (template says "a short paragraph is sufficient").
Optional but worth +10% on the poster grade. See GUIDELINES.md §12 for the
five-sentence template.

---

## Chapter 6 — Conclusion (~300–500 words)

Three parts already scaffolded:

1. Summary of RQs and their answers (two or three sentences).
2. Contributions list (benchmarking infrastructure, empirical verification,
   web app, honest analysis).
3. Future work (larger dataset, wider dimension sweep, real-hardware noise
   study, pgvector HNSW comparison).

No new results may appear here.

---

## References — `references.bib`

Pre-seeded with the eight cornerstone citations. Add as we go. **Do not** add
a reference without using it in the body, and vice versa.

---

## Appendices — `chapters/07_appendix.tex`

Three candidates listed in the file. Trim to what is actually useful.

---

## Build & Iteration

- `cd report && make` produces
  `report/SoftwareEngineering_QuantumVectorSearch_Mahmutovic_Kikanovic_Musanovic_Abdulahovic_2026.pdf`.
- `make clean` — removes generated files.
- `make watch` — rebuilds on every save (requires `entr`).
- Word count: `detex chapters/01_introduction.tex | wc -w`.

---

## Figure Production Punch List

A single batch to handle once the prose is mostly stable. Each entry tells you
**what to make**, **what tool to use**, **what source to copy from**, and
**roughly what it should look like**. Drop the result at the path shown — the
`.tex` files already reference these paths.

---

### `figures/ius_logo.png` — cover page

- **Status:** ✅ already in repo.
- **Source:** official IUS logo from <https://www.ius.edu.ba>.
- **Specs:** at least 300 DPI, transparent background.

---

### `figures/architecture.png` — chapter 3 §3.1

- **What:** the five-phase pipeline as a left-to-right block diagram.
- **Tool:** [draw.io](https://app.diagrams.net/) (free, exports PNG); or
  Mermaid if you prefer text-as-diagram.
- **Source to copy from:** `docs/NOTES.md` § "Implementation Phases" — the
  table there lists every box (`DirectoryDataLoader`, `CLIPEmbeddingModel`,
  the strategy interface, `DatabaseStorage`, FastAPI + React).
- **Layout sketch:**
  ```
  [DirectoryDataLoader] -> [CLIPEmbeddingModel] -> [SearchEngineStrategy]
                                                          |
       +---- BruteForceCosine / FaissFlat / FaissHNSW ----+
       +---- QiskitSwapTest / QiskitGrover(+QP) / Hybrid -+
                                                          v
                                            [DatabaseStorage (Postgres+pgvector)]
                                                          |
                                                          v
                                              [FastAPI + React UI]
  ```
- **Style:** classical engines in blue, quantum in purple, hybrid in green,
  IBM in amber — same palette as the frontend, see `frontend/src/engines.ts`.

---

### `figures/methodology.png` — chapter 3 §3.2

- **What:** a step-by-step "how we did this" flowchart. Required by the
  project brief.
- **Tool:** draw.io.
- **Source:** the five scripts in `backend/scripts/`:
  1. `import_dataset.py` (Flickr30k -> `data/images/`)
  2. `index_dataset.py` (CLIP encode -> `image_vectors`)
  3. `run_benchmarks.py` (engine x dim x shots loop -> `benchmark_results`)
  4. `generate_report.py` (DB -> `backend/reports/benchmark_report.md`)
  5. (parallel arm) `run_ibm_validation.py` (IBM QPU sanity check)
- **Layout sketch:** swim-lane diagram with three lanes ("data prep",
  "benchmark execution", "reporting"). Arrows show data flow between lanes.

---

### `figures/swap_test_circuit.png` — chapter 3 §3.5.2

- **What:** a small circuit diagram showing one swap-test execution.
- **Tool:** Qiskit itself.
- **How:** from `backend/`, in a Python shell after activating `.venv`:
  ```python
  from src.engines.qiskit_swaptest import QiskitSwapTestEngine
  import numpy as np
  e = QiskitSwapTestEngine()
  e.build_index(vectors=[np.eye(4)[0].tolist(), np.eye(4)[1].tolist()], ids=['a', 'b'])
  # Inspect the last circuit built; export with circuit.draw('mpl').savefig(...)
  ```
  (Add a small helper to the engine if needed to expose the circuit.)
- **Style:** matplotlib defaults. Crop tight to the circuit, no surrounding
  whitespace.

---

### `figures/grover_circuit.png` — chapter 3 §3.5.2

- **What:** circuit for one Grover iteration at small N (e.g. N=4 -> 2 qubits).
- **Tool:** same as above, but use `QiskitGroverEngine` from
  `backend/src/engines/qiskit_grover.py`.
- **Style:** label oracle and diffusion blocks.

---

### `figures/oracle_scaling.png` — chapter 4 §4.2

- **What:** line plot of empirical Grover oracle calls vs the theoretical
  `floor(pi * sqrt(N) / 4)` curve for several N values.
- **Tool:** matplotlib.
- **Source:** `benchmark_results.oracle_calls` column, joined with
  `dataset_size`. SQL:
  ```sql
  SELECT dataset_size, AVG(oracle_calls)
  FROM benchmark_results
  WHERE engine_name LIKE 'qiskit_grover%'
  GROUP BY dataset_size ORDER BY dataset_size;
  ```
- **Style:** two lines (empirical dots + theoretical curve), shared x-axis
  `N`, log-scale x optional.

---

### `figures/mrr_chart.png` — poster + optional in chapter 4

- **What:** horizontal bar chart of average MRR per engine, sorted descending.
- **Tool:** matplotlib.
- **Source:** `/api/benchmarks` JSON or the `benchmark_results` table directly.
- **Style:** colour bars by category (blue/purple/green/amber, same as UI).

---

### `figures/clip_pipeline.png` (optional) — chapter 3 §3.4

- **What:** a small diagram showing how text and image both land in the same
  512-dim CLIP space.
- **Tool:** draw.io.
- **Skip if** the prose alone is clear enough; it's a nice-to-have.

---

### `figures/qr_repo.png` — poster only

- **What:** QR code linking to the public GitHub repo.
- **How:** `qrencode -s 10 -m 2 -o poster/figures/qr_repo.png "https://github.com/<org>/<repo>"`
- **Regenerate before each print run** — URLs rot.

---

### Where each figure goes

| Figure | Used in | Already wired? |
|---|---|---|
| `ius_logo.png` | `chapters/00_cover.tex` | ✅ |
| `architecture.png` | `chapters/03_methodology.tex` (Fig. 3.1) | ✅ placeholder box |
| `methodology.png` | `chapters/03_methodology.tex` (Fig. 3.2) | ✅ placeholder box |
| `swap_test_circuit.png` | `chapters/03_methodology.tex` (§3.5, Fig. 3) | ✅ generated, wired |
| `grover_circuit.png` | `chapters/03_methodology.tex` (§3.5, Fig. 4) | ✅ generated, wired |
| `oracle_scaling.png` | `chapters/04_results.tex` (Fig. 5) | ✅ generated, wired |
| `mrr_chart.png` | poster `index.html` | ☐ poster-only, not in report |
| `clip_pipeline.png` | not yet — optional | ☐ |
| `qr_repo.png` | poster `index.html` | ✅ placeholder box |
