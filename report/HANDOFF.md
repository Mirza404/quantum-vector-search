# Handoff: Writing the Report

Operating manual for finishing and polishing the graduation report. The report
is **structurally and empirically complete and now has a full first draft of
every chapter**; what remains is team review, polish, and submission mechanics.

---

## 1. How we work together

Writing is a **discussion, not a delegation**:

1. User picks the section. AI proposes a short outline. User accepts/revises.
2. AI drafts prose paragraph by paragraph, not whole chapters blind.
3. Every external claim follows the **citation protocol in §4**.
4. User reads, edits; user commits when a section is locked.

**Evaluate, don't just comply.** Treat each instruction as a proposal to check
against the code, the benchmark data, and the rest of the report. If something
would produce a false or unsupported claim, say so and explain why rather than
writing it. The user wants pushback. Past good catches: the active sweep is 7
engines not 8; Grover's 4 oracle calls match theory only for the *padded* index
N=32, not N=20; the Biamonte survey abstract did not support the original §2.4
hybrid claim (narrowed it). "The user said so" never justifies writing something
false.

---

## 2. Current state

- **LaTeX scaffold** at `report/main.tex` + `report/chapters/*.tex`. Build with
  `cd report && make` (`make force` to rebuild from scratch, `make clean` to
  wipe). PDF at
  `report/SoftwareEngineering_QuantumVectorSearch_Mahmutovic_Kikanovic_Musanovic_Abdulahovic_2026.pdf`,
  currently **40 pages**.
- **Formatting is locked in the preamble** (Times 12pt, 1.5 spacing, FENS
  margins, IEEE numeric citations, sequential numbering, dotted TOC leaders,
  coloured hyperlinks). Added since scaffold: `\usepackage{tikz}` and
  `\usepackage{listings}` are in use. **Flag any further preamble change.**
- **All six body chapters, the Abstract, the Acknowledgements, the Abbreviations
  list, and the three Appendices are drafted.** No scaffold placeholders remain
  anywhere. All `\ref`/`\cite` resolve, no unused bib entries, every `.tex` is
  strict ASCII (names use LaTeX accent commands; see §7c).
- **All 9 references in `references.bib` are verified** and in use (Ch 1-4).
- **Figures are all real:** two TikZ pipeline diagrams (Ch 3), two Qiskit circuit
  diagrams + the Grover oracle-scaling plot, all produced by
  `backend/scripts/make_report_figures.py` (re-runnable) into `report/figures/`.
  `mrr_chart.png` is poster-only, not in the report.

### What remains (no drafting left)
- Team read-through and per-chapter sign-off.
- Optional length trim of Ch 3/Ch 4 (their `detex` counts are inflated by
  tables/TikZ/math; real prose is lower, but they are the long chapters).
- Similarity check < 20% (supervisor's Turnitin/iThenticate; a local 8-gram
  check against our own `docs/*.md` showed 0.07% self-overlap, so the self-paste
  risk is negligible, but only the supervisor's tool gives the official number).
- Signatures on the printed approval/declaration pages.
- Final PDF per handbook §2.5:
  `SoftwareEngineering_QuantumVectorSearch_Mahmutovic_Kikanovic_Musanovic_Abdulahovic_2026.pdf`.
- Open team decisions: poster group photo; the report builds without them.

---

## 3. Source material to mine (paraphrase, never paste)

`docs/NOTES.md` (architecture, phases, schema), `docs/THEORY.md` (metrics, CLIP,
swap test, Grover, MRR), `docs/ENGINES_GUIDE.md` (engine params),
`docs/QUANTUM_SEARCH_ANALYSIS.md` (qRAM, honest scaling),
`docs/BENCHMARK_KPIS.md` (MRR/oracle-call definitions),
`midterm/speaker_notes.md` (the team's framing, esp. the honest quantum
picture), `backend/reports/benchmark_report.md` (**the numbers, source of
truth**). The docs are the team's own writing, so they will not raise the
similarity score, but their tone is engineering-internal; reword for a thesis.

---

## 4. Citation verification protocol (most important rule)

Every new `\cite{key}` goes through this loop **before** it is written. Post a
block in chat and wait for the user to open the URL and Ctrl+F the quote:

> **Claim:** [exact sentence with the citation inline]
> **Proposed source:** [authors, title, venue, year, DOI]
> **URL to verify:** [free, direct link]
> **Quote to find:** ["verbatim string, >=10 words, from the source"]
> **Why it supports the claim:** [one sentence]

User approves (add the cite) or rejects (find another source, weaken the claim,
or drop it). LLMs hallucinate references, and a fabricated citation found at
defense can fail the project. All 9 seeded refs are already verified this way; any
*new* citation still needs the loop. Verification lessons learned: arXiv landing
abstracts can differ from the vN PDF (read the PDF for exact wording); ket glyphs
and superscripts break Ctrl+F (give a plain-ASCII tail); for abstract-only
sources, cite only the claim the abstract supports and present anything extra as
your own argument in the same sentence.

---

## 5. Numbers are canonical

Every quoted number must match `backend/reports/benchmark_report.md` (or a DB
query: `docker exec qvs-postgres psql -U qvs -d qvs_benchmarks -c "<sql>"`; MRR
is computed from `target_ids`/`top_ids`, not stored). Do not invent or re-round.
Use the engine labels from `frontend/src/engines.ts`.

**Ground-truth headline numbers** (already in the report):
- Classical (brute force = FAISS flat = FAISS HNSW): MRR 0.829 overall;
  0.655 / 0.858 / 0.975 at dim 64 / 128 / 256.
- Swap test: 0.728 overall; matches classical 0.975 exactly at dim 256; dim-128
  shot curve 0.642 -> 0.688 -> 0.883 (512/1024/2048 shots).
- Grover (hardcoded oracle): 0.759; 0.955 at dim 256; 4 oracle calls =
  floor((pi/4)*sqrt(32)) for the padded index, 5 qubits, depth ~50.
- Grover (quantum prep): 0.559 (weakest); hybrid: 0.823 (ties classical).
- IBM hardware validation: 0.125 (dim 2, 2 candidates, 32 shots, separate run).
- **Engine-count convention:** 7 active engines (3 classical + 4 quantum/hybrid)
  in the sweep/live UI. The 8th stored engine ID `hybrid_hnsw_swap_test_ibm` is
  only the separate IBM validation run, not part of the normal sweep.

---

## 6. Figures policy

Diagram-as-code only (TikZ, or a committed matplotlib/Qiskit script); never
AI-generated raster images. The structural diagrams are TikZ in the `.tex`; the
circuit and plot figures regenerate with
`cd backend && .venv/bin/python scripts/make_report_figures.py` (needs
`matplotlib` + `pylatexenc`, both installed in the venv). Every figure needs a
caption that stands alone and a short LoF label via `\caption[short]{long}`. The
same applies to tables for the List of Tables.

---

## 7. Writing rules (see GUIDELINES.md for the full set)

- **Investigative, not promotional.** No "revolutionary"/"groundbreaking"/
  "first ever". First-person plural "we"; past tense for what we did, present for
  the system. Define every domain term on first use (committee includes
  non-specialists).
- **No em dashes or AI-tell punctuation in prose.** Rewrite with commas, colons,
  parentheses, or two sentences. The en dash `--` for number/page ranges is fine.
- **Maths in LaTeX math syntax** (`$\sqrt{N}$`, `$\lfloor (\pi/4)\sqrt{N}\rfloor$`).
  This is correct and expected, not an AI tell. Never paste raw unicode glyphs
  and never degrade maths into ASCII words ("sqrt(N)").
- **`.tex` source is strict ASCII.** Check: `grep -nP "[^\x00-\x7F]" chapters/*.tex`
  returns nothing. Proper names keep diacritics via LaTeX accents (`Mahmutovi\'{c}`,
  `Mu\v{s}anovi\'{c}`, `H\"{a}ner`).
- **Clear intelligent-non-specialist level.** Explain the real idea plainly; no
  dumbed-down code-style analogies.
- Every acronym used in the body is in `00_abbreviations.tex` and expanded on
  first use; the "Use of AI Tools" section at the end of Methodology is mandatory
  (handbook §1.1) and is written.

---

## 8. Progress log (newest first; keep brief)

#### 2026-06-02 - Full first draft + figures + polish
- Wrote Ch 1, 2, 4, 5, 6, Abstract, Acknowledgements (Ch 3 was done earlier).
  Filled the three Appendices (config, schema, repo). Cleaned the Abbreviations
  list (added GPU, SDG; removed unused CSWAP/JSONB/ORM/REST/SIMD).
- Generated all figures via `make_report_figures.py`; fixed long List-of-Tables
  captions with `\caption[short]{}`.
- Verified `biamonte2017qml` (the last seeded ref) -> all 9 verified. Its abstract
  did not support the original §2.4 claim; narrowed the cited claim to "the
  hardware and software challenges are still considerable" and made the hybrid
  motivation our own argument.
- Added the GitHub repo as a footnote in §3.1 and in Appendix C.
- 46 pages, all refs resolve, no unused bib entries, strict ASCII throughout.
- Local self-overlap vs `docs/*.md`: 0.07% (8-gram), negligible.

#### Earlier (2026-05-28 to 2026-06-02)
- Structural setup: LaTeX scaffold, FENS front matter, `GUIDELINES.md`,
  `STRUCTURE.md`, 9 seeded references, cover/approval pages.
- Full benchmark sweep run: 920 rows in `benchmark_results` across 7 active
  engines plus the separate IBM run; `benchmark_report.md` regenerated.
- Chapter 3 Methodology written section by section (3.1-3.7 + the mandatory
  "Use of AI Tools" section), with the two TikZ pipeline diagrams.
- Code audit (18 items) cleared, including the FAISS re-normalisation bug that
  made the three classical engines agree.

### Definition of done for a chapter
Placeholders gone; every external claim verified via §4; word count within the
GUIDELINES §11 budget; `make` builds without new warnings; user has read the
rendered section and signed off; this log updated.
