# Handoff: Writing the Report

You (the AI assistant in the next session) are picking up a graduation project
that is **structurally finished and empirically complete** — the LaTeX
scaffold builds cleanly, all benchmarks have run, the code-audit fixes are
all merged. What is missing is the prose. This document is the operating
manual for writing it together with the user.

If you're the human user reading this: this is the brief I want you and the
next AI to follow. Hand it over verbatim.

---

## 1. How we work together

Writing the report is a **discussion**, not a delegation. The pattern is:

1. **User picks the next chapter or subsection** to work on.
2. **AI proposes an outline** (3–6 bullet points) of what will go in that
   section. User accepts, revises, or rejects.
3. **AI drafts the prose** *paragraph by paragraph*, not all at once.
4. **For every external claim, AI follows the citation protocol in §4
   below** — no exceptions, even for sources already in `references.bib`.
5. **User reads, edits, asks for changes.** AI applies them.
6. **User commits** when the section is locked.

The AI is not allowed to dump a full chapter without going through this
loop. The user is not allowed to rubber-stamp a paragraph without reading
it. Both behaviours produce the kind of report that fails plagiarism /
similarity checks or — worse — gets caught hallucinating references at
defense time.

---

## 2. State of the project

### What exists
- **LaTeX scaffold** at `report/main.tex` + `report/chapters/*.tex`. Builds
  with `cd report && make`. Use `make force` to rebuild from scratch.
- **Formatting decisions are locked in** the preamble: Times 12pt, 1.5
  spacing, FENS margins, IEEE numeric citations (`IEEEtran.bst`), sequential
  table/figure/equation numbering, dotted TOC leaders, coloured clickable
  hyperlinks. **Do not change the preamble without flagging it explicitly.**
- **`report/GUIDELINES.md`** — the writing rules. Read this first. Pay
  special attention to §2 (claims-must-be-sourced bucket system), §3 (IEEE
  citation usage), §7 (ASCII-only source — no unicode), §9 (AI disclosure
  is mandatory at the end of the Methodology chapter), §10 (20% similarity
  threshold).
- **`report/STRUCTURE.md`** — per-chapter plan with which existing project
  artefact to mine for each section, plus the figure punch list with
  detailed how-to for each figure.
- **`references.bib`** — 9 cornerstone citations already added. They are
  pre-seeded; every one of them still needs verification before its first
  use per the protocol in §4.
- **Benchmark dataset** is in PostgreSQL (`benchmark_results` table, 920
  runs across 8 engines × dims {2, 64, 128, 256} × shots {-1, 32, 512,
  1024, 2048}). A dump is committed at `db/seeds/seed.sql`.
- **`backend/reports/benchmark_report.md`** — auto-generated tabular
  summary. This is the source-of-truth for any number quoted in the
  Results chapter.

### What is incomplete and needs writing
- **All body chapters** (1 Introduction, 2 Literature Review, 3
  Methodology, 4 Results, 5 Sustainability, 6 Conclusion). Each contains
  scaffolded section headers + `[SECTION — what to write]` prompts +
  pre-placed figure boxes + the section's equations (where applicable).
- **Abstract** (`chapters/00_abstract.tex`) — write last, after the rest
  of the report has stabilised. 250–500 words.
- **Acknowledgements** (`chapters/00_acknowledgements.tex`) — short
  paragraph, write near the end.
- **Figures** — every figure in the report is currently a placeholder box.
  See `STRUCTURE.md` § "Figure Production Punch List" for per-figure
  how-to. The team initially deferred figure production. The AI is free to
  raise figures when the moment is right — e.g. when a section's prose is
  stable and a diagram would sharpen it, or when the punch list has
  everything needed to produce one. Propose it, explain why now, and let
  the user decide; do not silently generate figures or treat them as a
  blanket "later".

  When a figure does come up, pick the route that keeps it **editable**:
  - **Diagram-as-code** (preferred for anything structural): TikZ,
    Mermaid, draw.io XML, or a small matplotlib/Qiskit script committed to
    the repo. The source lives alongside the report so anyone can tweak a
    box or re-run it later.
  - **A screenshot or a real artefact the user captures** — in that case
    the AI's job is to spell out exactly what to capture (which page, which
    config, what to crop) so the user can produce it.
  - **An existing image from the web** used under a clear licence, cited in
    the caption per `GUIDELINES.md` §6.

  What we **avoid**: AI-generated raster images (e.g. asking an image model
  to "draw the methodology diagram"). They look plausible but cannot be
  edited cleanly when a label or arrow changes, and they are a poor fit for
  a thesis. A methodology or architecture diagram should always be
  diagram-as-code, never a generated picture.

### Open decisions waiting on the team
- Should we include a small group photo on the poster? (See
  `poster/PLAN.md` § "Open Decisions".)
- Does the supervisor want a co-mentor block on the Approval page, or
  should we delete that scaffold? Currently shows a placeholder.

---

## 3. Source material the user already has

Before you propose a single citation from outside the repository, mine
these first — they are the team's own writing and are free to paraphrase
without any plagiarism risk:

| File | What's in it |
|---|---|
| `docs/NOTES.md` | Architecture, five-phase pipeline, DB schema |
| `docs/THEORY.md` | Cheat sheet: metrics, CLIP, swap test, Grover, MRR, qubits |
| `docs/ENGINES_GUIDE.md` | Each engine's parameters and trade-offs |
| `docs/QUANTUM_INTUITION.md` | Plain-language walk-through of quantum bits |
| `docs/QUANTUM_SEARCH_ANALYSIS.md` | qRAM, scaling, the honest quantum picture |
| `docs/RESEARCH_QUESTIONS.md` | What we set out to measure |
| `docs/BENCHMARK_KPIS.md` | Precise definitions of MRR, oracle calls |
| `docs/FAQ.md` | Questions the team kept hitting |
| `docs/LEARNING_ROADMAP.md` | Theory roadmap (the team uses this internally) |
| `docs/midterm/speaker_notes.md` | The team's framing — particularly slide 11 (the honest quantum picture) which is already the best version of that argument |
| `backend/reports/benchmark_report.md` | The numbers |

The user has read these. Refer to them by file name — "I'm pulling the
swap test math from `docs/THEORY.md` § Swap Test, here's how I'd phrase
it" — and the user will know what you mean.

---

## 4. **Citation verification protocol — read this twice**

> The single most important rule in this document.

Every `\cite{key}` you add to the .tex source must go through this loop
**before** it is written:

### What you (the AI) must present

For each citation, post a block like this in the chat — do not edit the
file until the user has confirmed:

> **Claim:** [the exact sentence I want to write, with the citation inline]
>
> **Proposed source:** [full bibliographic info: authors, title, venue,
> year, DOI if any]
>
> **URL to verify:** [a direct, freely accessible link — preprint on
> arXiv, official PDF, DOI link if it leads to the full text, publisher
> page that includes the abstract at minimum]
>
> **Quote to find in that document:** ["exact string, ≥10 words, copied
> from the source, that supports the claim"]
>
> **Why this source supports the claim:** [one short sentence connecting
> the quote to the claim]

The user will then open the URL, search for the quote (Ctrl+F), and
either:
- ✅ Approve — you add the `\cite{key}` and proceed.
- ❌ Reject — you find a different source, or weaken the claim until it
  can be supported by what you have, or drop the claim entirely.

### Why this protocol exists

LLMs hallucinate references constantly — fabricated author names, wrong
years, wrong page numbers, papers that don't exist. A graduation report
caught with a fabricated citation at defense time can fail the project.
The 20% similarity check (handbook §1.1) will also catch fake citations
because the text won't match anything real.

The user does not have time to verify every paper in depth. The user
*does* have time to open a link and Ctrl+F a sentence. So that is the
contract: you do the work of finding the quote, the user does the work of
confirming it exists.

### Already-in-bib references still go through this

`references.bib` was pre-populated with 9 entries that look correct, but
**none of them have been verified yet by the user**. Before any of those
keys gets its first `\cite{}` in the body, run the protocol on it. The
existing keys are:

- `johnson2019faiss`, `malkov2020hnsw`, `radford2021clip`,
- `grover1996`, `buhrman2001swaptest`, `giovannetti2008qram`,
  `aaronson2015readfine`,
- `biamonte2017qml`, `qiskit2024`.

The example sentences I dropped into chapter 2 (Literature Review) use
all 9 of these. **Treat those example sentences as untrusted until the
user has verified each citation.** The user can either delete the
example sentences and we re-add them properly, or we walk through each
one in order.

### Self-test: did you follow the protocol?

Before you commit a paragraph, ask yourself:
- Does every claim I wrote fall into the **Measured / Cited / Argued**
  buckets from `GUIDELINES.md` §2?
- For each Cited claim, did I post the URL + quote in chat?
- Did the user actually say ✅ for each one?

If any answer is "no" or "I don't remember", revert the paragraph and
restart the loop.

---

## 5. Suggested order of operations

This is the order the user and I (the previous AI) agreed makes the most
sense. Negotiable.

1. **Methodology (Chapter 3) first.** It is the longest chapter and the
   one most directly grounded in the code. Writing it first forces you to
   nail down terminology that the other chapters will reuse.
2. **Results (Chapter 4) next.** Numbers are in the DB; writing the
   analysis against them while the methodology is fresh keeps the prose
   consistent.
3. **Introduction (Chapter 1).** Easier to write the framing once you know
   exactly what the contribution is.
4. **Literature Review (Chapter 2).** Heavy citation chapter — most use
   of the citation protocol will be here.
5. **Sustainability (Chapter 5).** Short. Half a page.
6. **Conclusion (Chapter 6).** Restatement of findings.
7. **Abstract** (`chapters/00_abstract.tex`).
8. **Acknowledgements** (`chapters/00_acknowledgements.tex`).
9. **Final polish:** run through `GUIDELINES.md` § "Pre-Submission
   Checklist", produce the renamed PDF per handbook §2.5.

---

## 6. Working with the code while writing

The benchmark data is canonical. If the user asks you to write a sentence
that quotes a number ("the swap test achieved MRR 0.975"), **always**:

1. Open `backend/reports/benchmark_report.md` (or query the DB directly:
   `docker exec qvs-postgres psql -U qvs -d qvs_benchmarks -c "<sql>"`).
2. Confirm the number is what's actually there.
3. Quote it in the prose.

If the user asks you to make an argument that needs new data ("can you
plot MRR vs shots for the swap test?"), look at what's in
`backend/scripts/generate_report.py` — that's the template for any new
analysis script.

Do not invent benchmark numbers. Do not round numbers differently in the
prose than in the table. Use the same vocabulary the live UI uses (the
frontend reads from `frontend/src/engines.ts` — same labels).

---

## 7. Building and inspecting the PDF

```bash
cd report
make           # build only if something changed
make force     # always rebuild from scratch (use after editing figures/)
make clean     # delete artifacts
```

PDF is at `report/report.pdf`. Open with `xdg-open report/report.pdf` or
from your file manager.

If the build fails with an undefined-character or font-related error, the
first thing to check is whether someone pasted unicode into a `.tex` file
(see `GUIDELINES.md` §7 for the lookup table).

---

## 8. Things that look done but actually aren't

- **Example sentences in chapter 2 use citations that haven't been
  verified.** See §4 above.
- **All figure boxes are placeholders.** The user will produce real
  figures later. Do not be tempted to remove the boxes or to "improve" the
  captions — the placement and caption text are already what the
  finished report needs.
- **`chapters/07_appendix.tex` lists three candidate appendices.** Trim to
  the ones actually used; otherwise leave the file as-is.
- **The Methodology chapter has a `\section*{Use of AI Tools}` placeholder
  at the end** (handbook §1.1, mandatory). The team's actual AI usage
  should be documented there — name the tools (Claude Code, ChatGPT, etc.)
  and the activities they assisted with. Be specific. Be honest. The
  supervisor will be looking for this section.

---

## 9. The user's framing preferences

- The project is an **investigation**, not a discovery. Phrases like
  "groundbreaking", "revolutionary", "first ever" are banned.
  See `GUIDELINES.md` §1.
- The committee includes faculty who are not quantum specialists. Define
  every domain term on first use. Do not assume the reader has read
  Nielsen & Chuang.
- Writing voice is "we" (first-person plural), past tense for what was
  done, present tense for what the system is.
- The team wrote a lot of internal docs — paraphrase, don't paste.
  Verbatim copies from `docs/*.md` will technically pass the similarity
  check (because they're the team's own writing and won't be in the
  reference corpus) but the tone is engineering-team-internal and reads
  wrong in a thesis.

---

## 10. Quick start for the first conversation

A reasonable opening message from the AI in the next session:

> I've read `report/HANDOFF.md`, `report/GUIDELINES.md`, and
> `report/STRUCTURE.md`. The scaffold builds; the benchmark dataset is
> complete (920 runs, headline MRR 0.829 across the classical engines).
> Per the handoff doc, I'll work paragraph by paragraph and run every
> citation through the verification protocol before adding it to the
> source. Where do you want to start — Methodology §3.1 (System
> Overview) is the suggested first section. Want to talk through the
> outline for that?

---

## 11. Living progress log — keep this current

This section is the running history of what's been done. The user pastes
this whole file at the start of each fresh AI session, and the new AI
reads this log to feel like the previous session never ended. **Every AI
that touches this project must update this section before ending a turn
that produced meaningful changes.**

How to update:
- Append a new dated entry at the top of the log (newest first).
- Each entry: 1–4 lines. What changed, why, where to find it.
- Don't rewrite history. If a previous claim is now wrong, add a new
  entry that supersedes it; don't silently edit the old one.
- After updating, rebuild the report (`cd report && make`) so the PDF
  reflects the latest source.

### Done so far

#### 2026-06-02 - First prose: Methodology 3.1 + 3.2 + both diagrams

- **Research questions locked.** Kept RQ1 (Accuracy) and RQ3 (Practicality).
  Reworded RQ2 ("on real circuits" -> "in practice", to avoid implying
  real-QPU scaling data, since the IBM run is separate). Added **RQ4
  (Suitability)**: whether vector search is a problem class quantum is
  suited to at all, grounded in Aaronson's "big compute on small data"
  argument (`aaronson2015readfine`). RQ1-3 are empirical; RQ4 is the
  Argued synthesis question. See `chapters/01_introduction.tex` 1.3.
- **Methodology 3.1 (System Overview) written** - three paragraphs
  (framing, the strategy-pattern keystone, the five phases). All
  descriptive of our own system, no citations. `chapters/03_methodology.tex`.
- **Figure policy changed.** No longer a blanket defer. The AI may propose
  figures as prose stabilises, using editable routes (diagram-as-code
  preferred; screenshots the user captures; licensed web images). What we
  avoid: AI-generated raster images that cannot be edited. See 2 above.
- **Methodology 3.2 (Methodology Diagram) written** - four-paragraph
  narrative walking the four scripts in order (import -> index -> benchmark
  -> report), with the IBM validation as a side arm. Reproducibility
  framing throughout (GUIDELINES 14). `chapters/03_methodology.tex`.
- **Two figures produced as TikZ** (diagram-as-code, live in the .tex,
  rebuild with `make`), replacing both placeholder boxes:
  - Fig 1 architecture: five-phase pipeline, palette matches the frontend
    (classical blue, quantum purple, hybrid green).
  - Fig 2 methodology: four-script vertical flow with rotated lane labels
    (Data prep / Execution / Reporting) and the IBM hardware validation as
    an amber side arm into the same `benchmark_results` table.
  - Note for future TikZ: avoid `step` as a style name, it collides with
    TikZ's grid `step` key (caused a fatal error; renamed to `procbox`).
  - **Preamble change flagged:** added `\usepackage{tikz}` +
    `arrows.meta, positioning` to `main.tex`.
- **Approval page:** removed the co-mentor block (the team has no
  co-mentor). `chapters/00_approval.tex` now shows the mentor block only.
- Report now builds at 28 pages.
- **RESUME HERE next session:** Methodology 3.3 (Dataset and Ground Truth),
  prose-only, no figure. Source: `import_dataset.py` (deterministic
  Flickr30k subset) and `backend/data/ground_truth.jsonc` (20 image-caption
  pairs, definition of a correct hit). Same loop: outline -> react ->
  paragraph-by-paragraph draft. After that, 3.4 Embedding Pipeline, 3.5
  Search Engines (incl. the IBM Hardware Validation subsection), 3.6-3.8,
  then Chapter 4 Results.

#### 2026-05-28 (afternoon) — Live-search config + StrictMode fix

- **`/api/search` was hanging in the UI forever** — root cause was a React
  StrictMode double-mount bug in `SearchRoute` (the `lastFetchedId` guard
  made the second invocation short-circuit while the first was already
  cancelled, leaving `loading=true`). Fixed by dropping the guard and
  relying solely on the cancelled flag in the effect cleanup.
- **Backend timing** verified at ~2.9 s end-to-end for the previous
  dim-64 config; ~7-20 s at the new dim 128 (dominated by
  `qiskit_grover_quantum_prep`).
- **New `live_search:` block in `backend/config/benchmarks.yaml`** so live
  API config is separated from benchmark sweep order. Defaults bumped to
  **dim 128, shots 512, top-k 10**. Trade-off: classical engines now hit
  MRR 0.858 (vs 0.655 at dim 64), swap test reaches 0.65–0.88, but
  quantum simulator wait grew to 10–20 s.
- **`/api/search` returns a `config` block** so the UI can show what was
  run; SearchResults now displays a params badge ("dim 128 | 512 shots |
  top-10") above the result grid.
- Loading message updated to set the expectation ("Expect ~10–20 s at
  dim 128").

#### 2026-05-28 (morning) — Structural setup + benchmarks complete

**Report scaffolding**
- LaTeX project at `report/` builds cleanly (25 pages).
- All 6 body chapters + front matter scaffolded with `[SECTION — …]` prompts.
- Cover page filled: 4 students + Software Engineering program + supervisor
  (Assist. Prof. Dr. Ali Abd Almisreb). IUS logo embedded.
- Front matter formatted to FENS spec: dotted TOC leaders, dotted signature
  lines, right-aligned mentor block + date, `Table N:` / `Figure N:` prefix
  in LoT/LoF, sequential numbering (no chapter prefix), coloured clickable
  hyperlinks (`#1E40AF`).
- `report/GUIDELINES.md` (writing rules, 15 sections including the
  citation bucket system, ASCII-only rule, AI disclosure, similarity
  threshold, pre-submission checklist).
- `report/STRUCTURE.md` (per-chapter plan + figure punch list with
  per-figure how-to: which tool, which source, layout sketch).
- `report/HANDOFF.md` (this file).

**Citations**
- `references.bib` seeded with 9 IEEE entries (Johnson FAISS, Malkov HNSW,
  Radford CLIP, Grover 1996, Buhrman swap test, Giovannetti qRAM,
  Aaronson "Read the fine print", Biamonte QML survey, Qiskit).
- Example sentences in `chapters/02_literature_review.tex` exercise all 9.
  **Marked untrusted** — must run through the §4 verification protocol
  before staying in the final report.

**Frontend / app**
- 3 tabs wired as routes via `react-router-dom`: `/browse`, `/search`,
  `/benchmarks`. `/search?q=<query_id>` persists selection across refresh.
- `frontend/src/engines.ts` is the single source of truth for engine
  labels, categories, score semantics, scaling.
- `frontend/src/components/MetricsLegend.tsx` is a collapsible "About
  these metrics" panel — same wording the report's methodology chapter
  should use.
- Benchmarks page has two views: Summary (one row per engine) and By
  dim & shots (faceted breakdown, fed by `/api/benchmarks/by-config`).
- Search results show top-6 by default with a "Show all N" toggle, plus
  an amber banner when the truth is at rank 7–10.
- StrictMode double-mount bug in SearchRoute fixed (was leaving
  loading=true forever).

**Backend**
- `/api/engines` returns `{id, category, is_quantum, live}` per engine.
- `/api/benchmarks/by-config` exposes the faceted dim×shots breakdown.
- `/api/search` uses cached pre-built engines (no per-request
  `build_index` rebuild). Cold-search response time ≈ 2.9 s end-to-end at
  dim 64 / 512 shots; cached searches faster.
- All response shapes carry `category` so FE never has to guess.

**Bug fixes**
- **Critical: FAISS engines weren't re-normalising vectors after CLIP
  truncation.** Now both `FaissFlatEngine` and `FaissHnswEngine`
  re-normalise in `build_index` and `search` via shared
  `_l2_normalize_rows()`. All three classical engines now produce
  identical rankings (MRR 0.829 averaged across the sweep).
- Removed hardcoded engine year/count from the App header (now
  computed).

**Benchmark dataset**
- `backend/config/benchmarks.yaml` sweep widened: `dimensions: [64, 128, 256]`,
  `shots_values: [512, 1024, 2048]`. Dim 512 + shots 4096 kept commented
  out (too slow on simulator).
- Full sweep ran end-to-end. **920 rows in `benchmark_results`** across
  8 engines × {dim, shots}.
- `backend/reports/benchmark_report.md` regenerated (121 KB).
- `db/seeds/seed.sql` dumped (506 KB) — teammates can `make seed` to
  reproduce exact dataset.

**Headline numbers** (use these as ground truth):
- Classical (brute force = FAISS flat = FAISS HNSW): MRR 0.655 / 0.858 /
  0.975 at dim 64 / 128 / 256.
- Swap test at dim 256: MRR 0.975 for all shot counts — converges to
  classical ceiling.
- Swap test shots curve at dim 128: 0.642 → 0.688 → 0.883 across 512 /
  1024 / 2048 shots (this is the curve RQ1 needs).
- Grover (hardcoded oracle) at dim 256: 0.955.
- Grover quantum-prep at dim 256, 2048 shots: 0.780 (weakest engine).
- Hybrid HNSW + swap test: tied with classical baseline at every dim.
- IBM hardware sanity check: MRR 0.125 (dim 2, 2 candidates, 32 shots —
  not a scaling experiment).

**Poster**
- `poster/index.html` + `poster/style.css` — A0 portrait HTML scaffold,
  9 sections, content where I had material, placeholder boxes for
  figures. Print via Chrome → Save as PDF, A0 portrait, no margins.
- `poster/PLAN.md` — layout brief, image punch list, print workflow.

**Code audit punch list — 18 items, all cleared**
- P0 (labels, complexity column, dynamic engine count): 4/4.
- P1 (single SoT, perf, conclusion-from-data, About panel, top_k
  pagination, search empty state, snake_case labels, faceted view):
  8/8.
- P2 (backend engine list, rounding, response shape, "Time" unit, dynamic
  year): 5/5.
- P3 (README docs section, architecture sketch, dated docs): 3/3.
- Plus: the FAISS normalisation bug found during the audit.

### Definition of done for the next session

A chapter is done when:
1. Every `[SECTION — …]` placeholder in that chapter's `.tex` is gone.
2. Every external claim is backed by a `\cite{key}` that went through
   §4's verification protocol with explicit ✅ from the user.
3. Word count is inside the budget in `GUIDELINES.md` §11.
4. `cd report && make` produces no new warnings.
5. The user has read the rendered PDF section end-to-end and signed off.
6. This log got a new dated entry.

### What's NOT done and waiting for next session

- All prose in chapters 1–6 (placeholders only).
- Abstract + Acknowledgements (write last).
- "Use of AI Tools" subsection at the end of Methodology — mandatory per
  FENS handbook §1.1.
- Real figures (placeholder boxes in place). No longer a blanket defer —
  the AI may propose figures as prose stabilises, using the editable
  routes in §2 (diagram-as-code preferred; no AI-generated raster images).
- Verification pass on the 9 seeded references.
- Group photo decision for the poster.

---

*File created 2026-05-28 at the close of the structural-setup session.
Last updated 2026-06-02. Keep this date in sync with the most recent log
entry.*
