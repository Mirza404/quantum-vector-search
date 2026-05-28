# Report Writing Guidelines

These rules apply to **every** sentence written into `report/chapters/*.tex`,
whether by a human or an AI assistant. They exist so the report is grading-safe
under the FENS handbook (≤20% similarity, transparent AI disclosure, IEEE
citations) and so the writing reads as a careful empirical investigation
rather than a marketing pitch.

If you (human or AI) are about to write a sentence and any rule below is
unclear, stop and ask in the conversation rather than guessing.

---

## 1. Voice and Stance

- **Investigative, not promotional.** This is a study of when quantum search
  works and when it does not. We are not selling quantum advantage. Phrasing
  like "revolutionary", "groundbreaking", or "first ever" is banned.
- **First-person plural ("we").** "We measured", "we observed", "we built".
  Avoid "the authors" except in the AI-tools disclosure section.
- **Present tense for the system, past tense for what we did.**
  "The swap-test engine encodes vectors via amplitude encoding."
  "We ran 240 benchmark configurations and recorded the results in PostgreSQL."
- **Reader assumption.** The committee includes faculty from other programs
  who are not quantum specialists. Define every domain-specific term on first
  use. Do **not** assume the reader has read Nielsen & Chuang.

## 2. Claims Must Be Sourced

Every factual claim falls into exactly one of three buckets. Pick the bucket
**before** you write the sentence.

| Bucket | What it means | How to back it |
|---|---|---|
| **Measured** | A number produced by our benchmark runs. | Cite the table or figure: "Table~\ref{tab:mrr} shows..." The underlying row must exist in `backend/reports/benchmark_report.md` or be reproducible from `scripts/run_benchmarks.py`. |
| **Cited** | A claim taken from prior literature or documentation. | Add an entry to `references.bib` and cite with `\cite{key}`. IEEE style: `[1]`, `[2,3]`. |
| **Argued** | A logical inference combining measured + cited claims. | The reasoning must be visible to the reader in the same paragraph. No hidden steps. |

**Banned:** unsourced superlatives ("the fastest"), vague gestures ("studies
have shown"), and confident assertions about future hardware roadmaps. If a
claim depends on something not yet built (qRAM, fault-tolerant QPUs), say so
explicitly.

## 3. Citations (IEEE Numeric)

- Bibliography style is set globally in `main.tex` (`IEEEtran.bst`). Do not
  change it.
- Cite with `\cite{key}` for one source, `\cite{keyA,keyB}` for multiple.
  IEEE collapses runs: `[1,2,3]` renders as `[1]--[3]`.
- Put the citation **after** the claim, before the period:
  `...has been shown empirically~\cite{grover1996}.`
- Use a non-breaking space (`~`) before `\cite` so the number does not wrap.
- Cite the **primary source** when you can. If you found a claim in a survey,
  go to the original paper. The survey gets cited only when discussing the
  survey itself.
- Software you used (Qiskit, FAISS, CLIP) is cited like any other source.

## 4. Footnotes

Footnotes are for short asides that would break the flow of the main
sentence — not for full references. Use sparingly (one or two per chapter
maximum). Examples of acceptable footnotes:

- A clarifying definition the reader can skip.
- A URL to a live system or repository.
- A note about a non-obvious convention ("Throughout this section, `N` denotes
  the dataset size after deduplication.").

Footnotes that are really just a citation belong in `\cite{}` instead.

## 5. Acronyms

- Expand on **first use** in the body: "Mean Reciprocal Rank (MRR)".
- After that, use the acronym alone.
- Every acronym used in the body must also appear in
  `chapters/00_abbreviations.tex`, alphabetised.
- Common acronyms (CPU, API, SQL) do not need to be expanded in the body but
  still belong in the list.

## 6. Figures, Tables, and Equations

- **Number sequentially per chapter** (LaTeX handles this).
- **Every figure has a caption** that makes sense without the body text. A
  reader skimming the figures alone should still understand the contribution.
- **Every figure and table is referenced in the text** using `\ref{fig:...}`
  or `\ref{tab:...}` — never "the figure below", because float placement may
  move it.
- **Source attribution.** If a figure is taken or adapted from another work,
  cite the source in the caption: "Adapted from~\cite{key}."
- **Equations**: use the `equation` environment so they auto-number. Reference
  with `(\ref{eq:swaptest})`.
- **Tables**: use `\toprule`, `\midrule`, `\bottomrule` from `booktabs`. Never
  use vertical rules.

## 7. ASCII-Only Source — Use LaTeX Commands, Not Unicode

The `.tex` source must contain only standard keyboard characters. Typographic
glyphs that look right in a word processor (em dash, arrows, smart quotes,
Greek letters, mathematical symbols) break compilation, render inconsistently
across font setups, and confuse search/replace.

| Don't paste | Use instead |
|---|---|
| `—` (em dash) | `---` or `\,--\,` if you want thin space around it |
| `–` (en dash) | `--` |
| `→` `←` `↑` `↓` | `$\rightarrow$` `$\leftarrow$` `$\uparrow$` `$\downarrow$` |
| `⟨ψ\|φ⟩` | `\ket{\psi}`, `\bra{\phi}`, `\braket{\psi\|\phi}` (braket package) |
| `…` (ellipsis) | `\ldots{}` (text) or `\dots` (math) |
| `"smart"` `'quotes'` | `` `` text '' `` and `` ` text ' `` |
| `×` `÷` `≤` `≥` `≈` | `$\times$` `$\div$` `$\leq$` `$\geq$` `$\approx$` |
| `π` `√` `½` `²` `³` | `$\pi$` `$\sqrt{x}$` `$\tfrac{1}{2}$` `$x^2$` `$x^3$` |
| `°` (degree) | `$^\circ$` or `\degree` (with siunitx) |

Quick check before committing: `grep -nP "[^\x00-\x7F]" chapters/*.tex` should
return nothing. CI / pre-commit could enforce this.

## 8. Numbers and Units

- Always use a `0.` prefix on decimals less than one (`0.23`, not `.23`),
  except for probabilities and correlations capped at 1 (`p < .01`).
- Same number of decimal places per column in a table.
- Units via `\SI{}{}` from siunitx where they help readability
  (`\SI{512}{shots}`, `\SI{13}{qubits}`).
- "Approximately" written as `\approx` in math, "~" in prose.

## 9. AI Disclosure (Mandatory)

The handbook (§1.1) requires a `Use of AI Tools` subsection at the **end of
the Methodology chapter** (`chapters/03_methodology.tex`). It must:

1. Name the tools used (e.g. "Claude Code, GitHub Copilot").
2. List the activities the tools assisted with (code generation, code review,
   prose drafting, diagram drafting).
3. State explicitly that "the authors are responsible for the correctness,
   originality, and verification of all results."
4. Identify the parts that are entirely human-authored (algorithm design,
   experimental design, analysis of results, final report decisions).

A vague "AI was used for assistance" will not satisfy the requirement.

## 10. Similarity Threshold

The supervisor will run a plagiarism check; the threshold is **20%** (excluding
the cover pages, methodology code listings, quotations, and references).
Concrete practices that keep us safely under it:

- Paraphrase, do not paste. If a sentence from a paper is so well-formed it
  must be quoted, use real quotation marks and a citation.
- Do not paste code listings as prose. Show code in `lstlisting` blocks with a
  caption.
- Reuse of our own midterm presentation text is fine, but it should be
  reworded for the report's longer-form style.
- Never paste from our own documentation files (`docs/*.md`) verbatim. They
  are part of the same project and will not increase similarity scores, but
  they were written for a different audience and tone.

## 11. Section Ownership and Pace

| Chapter | Word budget | Primary author (placeholder — agree among team) |
|---|---|---|
| Introduction | 600–900 | TBD |
| Literature Review | 800–1,200 | TBD |
| Methodology | 1,500–2,500 | TBD |
| Results and Analysis | 1,500–2,500 | TBD |
| Sustainability | 200–400 | TBD |
| Conclusion | 300–500 | TBD |

Total target: **5,000–10,000 words** per the FENS template. Aim for the
middle: ~7,000.

## 12. Acknowledgements

One paragraph. Thank the supervisor, the faculty, and anyone who helped. No
inside jokes, no acronyms. Real names and titles.

## 13. Sustainability Section Tone

The poster grading form awards up to +10% bonus for meaningfully addressing
sustainability, inclusivity, or societal impact (Appendix 3). The chapter is
short by design — get to the point fast:

1. One sentence on energy/compute discipline (we deliberately ran on a
   simulator + small dataset rather than burning GPU hours).
2. One sentence on data ethics (Flickr30k is public, no PII).
3. One sentence on openness/reproducibility (open repository, deterministic
   benchmark harness).
4. One sentence on honest framing of quantum claims as a counter to hype.
5. Optionally one sentence mapping to SDG 4 (education) and SDG 9 (industry,
   innovation, infrastructure).

## 14. Reproducibility Discipline

Every numerical claim must trace to either:

- a commit hash + script invocation: "Reproduced with
  `python3 scripts/run_benchmarks.py` at commit `<sha>`.", or
- a row in `benchmark_results` that can be queried back.

Before submission, do a final pass that takes each number in the Results
chapter, opens the database / report file, and confirms the digit-for-digit
match.

## 15. Pre-Submission Checklist

Run through this before sending the PDF to the supervisor.

- [ ] `make` from `report/` builds without warnings.
- [ ] Every `\ref{...}` resolves (no "??" in the PDF).
- [ ] Every chapter's word count is within budget (`detex chapters/*.tex | wc -w`).
- [ ] All `[PLACEHOLDER]` tokens are gone.
- [ ] All `[CHAPTER NAME -- ...]` scaffolding prompts are gone.
- [ ] Every figure and table is referenced from the body.
- [ ] Every acronym used appears in `00_abbreviations.tex`.
- [ ] AI Disclosure subsection is present and specific.
- [ ] References list contains no unused entries (bibtex warns about this).
- [ ] Plagiarism check is below 20%.
- [ ] PDF filename matches handbook §2.5:
      `Program(s)_QuantumVectorSearch_Mahmutovic_Kikanovic_Musanovic_Abdulahovic_2026.pdf`
