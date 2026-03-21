# Dataset Overhaul: Structure, WebP, and Scalable Ground Truth

## Tasks

### 1 — Remove the `sample_dataset` nesting

Move everything one level up:

```
backend/data/sample_dataset/images/*.jpg   →   backend/data/images/*.webp
backend/data/sample_dataset/ground_truth.jsonc   →   backend/data/ground_truth.jsonc
```

Path references to update: `index_dataset.py`, `run_benchmarks.py` (×2), `main.py`, `benchmarks.yaml` comment, `backend/README.md`, `docs/NOTES.md`.

---

### 2 — Replace old images with 20 real WebP images via the import script

**Why WebP?** 25–35 % smaller than JPEG at the same quality. Already supported by `DirectoryDataLoader`. CLIP handles it fine (Pillow decodes before the encoder sees it).

The 4 old JPGs are not worth converting — drop them entirely. The 20 new images are the POC. If we need to scale to 100 later, we just run the same import script with more images.

- Delete `backend/data/sample_dataset/images/` and its contents
- Source 20 images from Flickr30k (see Task 3) and run the import script

---

### 3 — Ground truth strategy: use Flickr30k from HuggingFace

```
from datasets import load_dataset

ds = load_dataset("nlphuji/flickr30k")
```

Flickr30k is available on HuggingFace (`nlphuji/flickr30k`). Each row maps one image to an array of 5 human-written captions — so the dataset structure is `image → [caption1, caption2, ...]`. Ground truth comes for free, no manual work, and it is academically defensible.

Download a subset (20 images for now, 100+ later), parse the metadata, generate `ground_truth.jsonc` automatically.

**Important:** since every query maps to exactly one image, `target_ids` is removed from the schema. The target is derived directly from the query `id` by stripping the `"query_"` prefix — no redundant field needed. The benchmark harness needs to be updated accordingly.

---

### 4 — Import script

Create `backend/scripts/import_dataset.py`:

```
python import_dataset.py
```

Source folder and metadata path are hardcoded constants at the top of the file — no CLI params needed. Just drop your images and metadata in the expected place and run it.

**Every run wipes `backend/data/images/` and regenerates `ground_truth.jsonc` from scratch.** No incremental updates, no merge logic — just a clean rebuild.

**Flickr30k → `ground_truth.jsonc` mapping:**

Each Flickr30k row has `filename` (image file), `caption` (array of 5 captions), and `img_id`. One image = one query, using the first caption as the query text. `target_id` is derived from `id` at runtime — not stored in the file.

```jsonc
// ground_truth.jsonc — no target_ids, target is derived from id at runtime
[
  {
    "id": "query_1000092795",
    "text": "Two young guys with shaggy hair look at their hands while hanging out in the yard."
  }
]
```

---

### 5 — Update KPIs

Drop Recall@K entirely — with 1 query = 1 image it is just a binary pass/fail and adds no value. **MRR is the only metric we need** — it measures where the correct image ranked, which is the most useful signal for comparing engines.

Since MRR does not require a variable K, **remove `top_k_values` from `benchmarks.yaml`** and hardcode the retrieval depth (e.g. always fetch top 10). This removes the top_k loop from `run_benchmarks.py`, the `invalid_top_k` validation, and the `top_k` column from the `benchmark_results` table (add a DB migration to drop it).

Or even better maybe, add top_k as single input not list to benchmarks.yaml config

---

### 6 — Update all docs and report generation

After the schema and metric changes, the following need to be reviewed and updated:

- `docs/NOTES.md` — dataset structure, metric definitions
- `docs/THEORY.md` — metric explanations (Recall@K / MRR section)
- `backend/README.md` — dataset setup instructions
- `backend/config/benchmarks.yaml` — query IDs, remove `top_k_values`
- `backend/scripts/generate_report.py` — column names, metric labels in the generated report

---

## Result

After this issue is done, the dataset folder will look like this:

```
backend/data/
  images/
    1000092795.webp
    1000268201.webp
    ...
  ground_truth.jsonc
```
