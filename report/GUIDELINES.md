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

- Every acronym used in the body must appear in
  `chapters/00_abbreviations.tex`, alphabetised.
- Because every acronym is defined in that list, **do not re-expand it in the
  body**. Use the acronym alone (CLIP, FAISS, HNSW, qRAM, NISQ, MRR) and let the
  list carry the definition. This avoids repeating "Full Name (ACRONYM)" across
  several chapters and keeps the word count down.
- Exception: a metric or term may be glossed in one sentence where it is first
  computed if the explanation aids the reader, but without re-spelling the
  acronym itself.

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

The `.tex` source must contain only standard keyboard characters. Raw
typographic and mathematical glyphs (Greek letters, roots, arrows, smart
quotes) break compilation, render inconsistently across font setups, and
confuse search/replace. The fix is to write them as LaTeX commands, which
compile to the correct symbol in the PDF.

There are **two separate concerns here. Do not conflate them.**

### 7a. Mathematical notation: write it in LaTeX math, and do use it

Maths belongs in a thesis, and the reader should see real mathematical
symbols. Write them with LaTeX math syntax: `$\sqrt{N}$`, `$\pi$`,
`$O(\sqrt{N})$`, `$\lceil \log_2 d \rceil$`, `$|\langle\psi|\phi\rangle|^2$`.
These render as proper symbols (the radical sign, the Greek letter, and so on)
in the PDF, which is exactly what you want. **This is correct and expected; it
is not an AI tell.**

Two failure modes to avoid:
- **Do not paste the raw unicode glyph** (`√`, `π`, `θ`) into the source. It
  is not ASCII and may not compile.
- **Do not degrade maths into ASCII words in prose.** Write `$\sqrt{N}$`, never
  "sqrt(N)"; write `$\lceil \log_2 d \rceil$`, never "ceil(log2 d)"; write
  `$O(N)$`, never a bare "O(N)". The LaTeX form is the correct one.

| Raw glyph (do not paste) | Write instead (LaTeX) |
|---|---|
| `→` `←` `↑` `↓` | `$\rightarrow$` `$\leftarrow$` `$\uparrow$` `$\downarrow$` |
| `⟨ψ\|φ⟩` | `\ket{\psi}`, `\bra{\phi}`, `\braket{\psi\|\phi}` (braket package) |
| `…` (ellipsis) | `\ldots{}` (text) or `\dots` (math) |
| `"smart"` `'quotes'` | `` `` text '' `` and `` ` text ' `` |
| `×` `÷` `≤` `≥` `≈` | `$\times$` `$\div$` `$\leq$` `$\geq$` `$\approx$` |
| `π` `√` `½` `²` `³` `θ` | `$\pi$` `$\sqrt{x}$` `$\tfrac{1}{2}$` `$x^2$` `$x^3$` `$\theta$` |
| `−` (unicode minus) | `-` (text) or `$-$` (math) |
| `°` (degree) | `$^\circ$` or `\degree` (with siunitx) |

### 7b. The em dash is a STYLE rule, not an encoding one: avoid it in prose

A sentence joined by an em dash (whether you encode it `---` or `\,--\,`) reads
as an obvious AI tell. Unlike the maths above, there is no "correct LaTeX way"
to keep it: **in body prose, do not use the em-dash construction at all.**
Rewrite with a comma, a colon, parentheses, or two sentences.

| Glyph | In body prose | In ranges |
|---|---|---|
| `—` em dash | avoid; rewrite the sentence | n/a |
| `–` / range | n/a | `--` (e.g. `pp.~212--219`) |

The en dash `--` for numeric and page ranges is standard and fine. A `\,--\,`
inside a scaffold label or placeholder is also fine, because that is not prose.

### 7c. Proper names keep their diacritics: do NOT anglicise them

The rules above are about technical and typographic glyphs, not people's names.
A name is spelled the way its owner spells it, so keep the diacritics. The
authors are Mahmutovic with the acute (Mahmutovi + c-acute), Kikanovic,
Musanovic (s-caron), and Abdulahovic; cited authors keep theirs too
(Haner with an umlaut, Jegou with an acute).

- **In `.tex` source** (which must stay ASCII), write names with LaTeX accent
  commands so they render the correct glyph: `Mahmutovi\'{c}`,
  `Mu\v{s}anovi\'{c}`, `J\'{e}gou`, `H\"{a}ner`, plus `\v{c}`, `\v{z}`,
  `\dj{}` (the d-stroke). These compile correctly under `T1` fontenc.
- **In Markdown, docs, and code comments**, raw UTF-8 diacritics in names are
  fine (đ, š, ž, ć, č, ä, é). Do not transliterate or strip them. If you run an
  ASCII sweep over the codebase, exclude proper names from it.
- **The PDF filename stays ASCII** per handbook §2.5
  (`..._Mahmutovic_Kikanovic_Musanovic_Abdulahovic_2026.pdf`). The romanised
  form is correct only in the filename.

### 7d. The same spirit applies beyond `.tex` (Markdown, docs, code)

For non-`.tex` files, prefer ASCII or LaTeX-style notation over raw unicode
maths glyphs: write `^2` or `$x^2$`, not `²`; `sqrt(N)` or `$\sqrt{N}$`, not
`√N`; `->`, not `→`. Markdown renderers understand LaTeX math between dollar
signs, so reach for it when a real formula helps. The names exception in 7c
still holds: keep diacritics in names everywhere, including Markdown and code.

Quick check before committing: `grep -nP "[^\x00-\x7F]" chapters/*.tex` should
return nothing (the `.tex` source is strict ASCII; names there use the LaTeX
accent commands from 7c). For Markdown and code, a non-ASCII hit is only
acceptable when it is a diacritic inside a proper name.

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
