# Poster Plan

The poster is the main public-facing artefact at the FENS Graduation Projects
Exhibition (June 19, 2026). It is graded by the Project Committee using
Appendix 3 of the handbook (problem definition, methodology appropriateness,
implementation quality, validation/targets, **poster design and visual
clarity**, oral explanation).

This file is the design brief. The actual poster lives in `poster/index.html`
+ `poster/style.css`. We mock it up in HTML so we can iterate quickly, then
export to a print-ready PDF (Chrome → Save as PDF, A0 portrait, no margins).

---

## Format

| Property | Value |
|---|---|
| Orientation | Portrait |
| Size | A0 (841 × 1189 mm, ~33 × 47 in) |
| Aspect ratio | ~1.41 : 1 (height to width) |
| Print resolution | 300 DPI minimum for any embedded raster figure |
| Reading distance | 1–1.5 m. Body text ≥ 24 pt. Headings ≥ 60 pt. |

> The project brief said "maybe twice as long as it is wide" — A0 portrait is
> actually only 1.4× taller than wide. We picked A0 because that is what the
> FENS poster template will almost certainly be. If the FENS template lands as
> a different ratio, update `style.css` (`#poster { width / height }`) and
> reflow the columns.

---

## Visual Identity

| Element | Value |
|---|---|
| Primary palette | Slate (#0f172a), Blue (#1e40af), Purple (#7c3aed), Green (#16a34a) |
| Fonts | System sans for headings, system serif optional for body |
| Logo | IUS logo top-left at ~120 px height |
| QR code | Bottom-right linking to repository (generate at build time, see §QR) |

The colour palette intentionally mirrors the frontend so a committee member
who sees the live app recognises the visual identity.

---

## Layout (top to bottom)

```
+----------------------------------------------------------+
| HEADER STRIP                                             |  ~140 mm
|   IUS logo | Project title (large) | Authors + Mentor    |
+----------------------------------------------------------+
| ABSTRACT                                                 |   ~90 mm
|   3-4 sentences, full-width banner                       |
+--------------------------+-------------------------------+
| 1. PROBLEM & RQs         | 2. WHY THIS MATTERS           |   ~200 mm
| Three bullet RQs.        | One paragraph + small icon.   |
+--------------------------+-------------------------------+
| 3. METHODOLOGY (full-width)                              |   ~250 mm
|   Big methodology diagram (figures/methodology.png)      |
|   Caption: data flow from import to benchmark to UI      |
+--------------------------+-------------------------------+
| 4. ENGINES               | 5. EVALUATION METRICS         |   ~180 mm
| Table: 8 engines × class | MRR formula, oracle-call defn |
| Highlight quantum rows.  | Wall-clock policy callout.    |
+--------------------------+-------------------------------+
| 6. RESULTS (full-width)                                  |   ~250 mm
|   Bar chart: avg MRR per engine.                         |
|   Line chart: Grover empirical vs theoretical scaling.   |
|   Two-sentence interpretation under each chart.          |
+--------------------------+-------------------------------+
| 7. HONEST QUANTUM PICTURE                                |   ~120 mm
|   qRAM caveat. HNSW beats Grover even with ideal qRAM.   |
|   Direct, plain English. The "investigation" framing.    |
+--------------------------+-------------------------------+
| 8. CONCLUSION & FUTURE WORK | 9. REFERENCES + QR CODE    |   ~130 mm
| Three bullet contributions  | Top-5 IEEE citations + QR  |
+--------------------------+-------------------------------+
```

Total ≈ 1,360 mm vertical; A0 is 1,189 mm, so we have ~170 mm of margin to
trim once content settles. Sections can be compressed by removing one of the
charts or shrinking the methodology diagram caption.

---

## Image Placeholders

Every image in the HTML is a labelled `<div class="placeholder">` box. The
filename and intent below — drop the real file in `poster/figures/` and the
CSS will swap to using it.

| Slot | Filename | Source | Intent |
|---|---|---|---|
| Header logo | `figures/ius_logo.png` | IUS website | Top-left branding. |
| Methodology | `figures/methodology.png` | draw.io export | Full-width data-flow diagram. Same artefact as `report/figures/methodology.png`. |
| Architecture inset (optional) | `figures/architecture.png` | draw.io export | Small, in the Engines section. |
| MRR chart | `figures/mrr_chart.png` | matplotlib (`scripts/plot_mrr.py` — to be written) | Horizontal bar chart, engines sorted by MRR. |
| Scaling chart | `figures/oracle_scaling.png` | matplotlib | Empirical vs theoretical Grover oracle calls. Same artefact as the report. |
| Swap-test circuit | `figures/swap_test_circuit.png` | Qiskit `circuit.draw('mpl')` | Used in the Engines section if space allows. |
| QR code | `figures/qr_repo.png` | `qrencode -o qr_repo.png https://github.com/<org>/<repo>` | Bottom-right. |

**Decision deferred:** which figures to ship. The CSS layout assumes all of
the above; if any are dropped, collapse the column or widen the neighbour.

---

## Content Sourcing

Reuse, do not invent.

- **Abstract**: the same 3–4 sentences as `report/chapters/00_abstract.tex`.
  Tighter than the 250-word report version.
- **RQs**: same three RQs as the report (`01_introduction.tex` §1.3).
- **Engines table**: dump from `backend/config/benchmarks.yaml` +
  `docs/ENGINES_GUIDE.md`.
- **Honest quantum picture**: condense `docs/midterm/speaker_notes.md`
  slide 11 — that is already the best version of this argument we have.
- **References**: top 5 from `report/references.bib`. No URLs (QR replaces them).

Single source of truth: when a number changes in the report, it changes on
the poster, and vice versa.

---

## Print Workflow

1. `cd poster && python3 -m http.server 8000` — open `localhost:8000`.
2. Iterate on `index.html` + `style.css`. Use Chrome DevTools device mode at
   841 × 1189 px to preview at-scale.
3. When happy: Chrome → Print → A0 portrait → Save as PDF → margins: None.
4. Send the PDF to the printer the faculty designates.

For onscreen review on smaller monitors, the CSS has a `@media screen` rule
that scales the poster to fit the viewport while preserving the layout. The
print export uses the raw 841 × 1189 mm size.

---

## QR Code

Generate before each printing pass — links can rot.

```
qrencode -s 10 -m 2 -o poster/figures/qr_repo.png \
  "https://github.com/Mirza404/quantum-vector-search"
```

(Update URL if the canonical repo moves.)

---

## Submission

Per handbook §2.3, the poster is uploaded to Microsoft Teams as a PDF
**before** the FENS Graduation Projects Exhibition. Only the Teams version is
official. Filename suggestion:

`Poster_QuantumVectorSearch_Mahmutovic_Kikanovic_Musanovic_Abdulahovic_2026.pdf`

---

## Open Decisions (need team discussion before final print)

1. Which programs go under each name on the header?
2. Do we want a "scan this to try the live app" QR code in addition to the
   repo QR? (Requires deploying the FastAPI backend somewhere public.)
3. Do we include a small group photo? Many FENS posters do; not required.
4. Final font choice — system fonts work for the HTML mockup; for the printed
   version we may want to embed Inter or Source Sans for sharper rendering.
