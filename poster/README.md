# Poster

A0 portrait HTML/CSS poster for the FENS Graduation Projects Exhibition 2026.

## Files

- `index.html` — the poster itself, one A0 page.
- `style.css` — A0-sized layout, print rules, colour palette.
- `PLAN.md` — design brief: layout, content sourcing, image punch list, open decisions.
- `figures/` — drop real images here when ready (placeholders render until then).

## Preview

```bash
cd poster
python3 -m http.server 8000
# open http://localhost:8000
```

The on-screen view is scaled down to fit the viewport. To tweak the scale,
edit the CSS variable `--screen-scale` in DevTools (default `0.32`, ≈ A0
shrunk to ~270 mm wide for a typical laptop).

## Export to print PDF

1. Open `index.html` in Chrome.
2. Print → Destination: Save as PDF → Layout: Portrait → Paper size: A0 → Margins: None → Background graphics: ON.
3. Save as `Poster_QuantumVectorSearch_<surnames>_2026.pdf`.

## Edit

Most edits are in `index.html` (content) and `style.css` (`--c-*` for colour,
`--fs-*` for type sizes, `--gap` / `--pad` for spacing). The HTML is laid out
top-to-bottom in plain `<section>` blocks — no framework, no build step.
