## Dependency & tooling decisions

- **Stay with `uv` (March 23, 2026):** Chose to keep `uv` for dependency management instead of switching to `pip + requirements.txt` because `uv` gives deterministic lockfiles, a single source of truth (`pyproject.toml`), and faster installs. Adding a `requirements.txt` would require manual syncing and lose `uv`'s platform-aware locking.

- **Large `uv.lock` is expected:** Running `uv lock --refresh` after adding `[tool.uv.required-environments]` forced uv to emit metadata for both Linux/x86_64 and macOS/arm64. That’s why the lockfile gained hundreds of wheel URLs/hashes—it now records every candidate per required platform so future installs don’t miss a wheel. Only the current platform’s subset actually gets downloaded at install time.

- **Remove stale `*.egg-info` (Mar 23, 2026):** Deleted `backend/src/quantum_vector_search.egg-info` because it’s a build artifact created by editable installs. Keeping it out of the tree avoids noisy diffs and aligns with the existing ignore rule (`src/*.egg-info/`).

- **Single virtual environment (Mar 23, 2026):** Dropped the repo-level `.venv` and standardized on `backend/.venv`, which `uv` manages automatically. This eliminates redundant environments and makes it obvious which interpreter houses the backend dependencies. Updated `.gitignore` to keep both paths ignored going forward.

## Dataset decisions

- **Importer switch (March 23, 2026):** Hugging Face removed `trust_remote_code`, so the old Flickr30k loader stopped working. Replaced it with the built-in `beans` dataset (available without custom scripts) and added `DATASET_NAME`, `DATASET_SPLIT`, and `SHUFFLE_SEED` constants for clarity. These settings let us keep pulling a tiny, reproducible image sample until we decide on the long-term dataset strategy.

- **Flickr30k → Beans clarification (Mar 23, 2026):** The change wasn’t triggered by a local `datasets` install or a version bump—the dependency is still `datasets==2.21.0` inside `backend/.venv`. The issue was Hugging Face’s policy change that blocks datasets requiring `trust_remote_code`, which Flickr30k depends on. To unblock teammates, `scripts/import_dataset.py` now calls `load_dataset("beans", split="train")`, shuffles with a fixed seed, and saves the first `num_images` rows. Nothing else in the project changes: engines still read WebP files via `DirectoryDataLoader`, and swapping back only requires pointing the importer at another dataset that doesn’t rely on custom scripts.
