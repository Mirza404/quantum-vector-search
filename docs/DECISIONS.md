## Dependency & tooling decisions

- **Stay with `uv` (March 23, 2026):** Chose to keep `uv` for dependency management instead of switching to `pip + requirements.txt` because `uv` gives deterministic lockfiles, a single source of truth (`pyproject.toml`), and faster installs. Adding a `requirements.txt` would require manual syncing and lose `uv`'s platform-aware locking.

- **Large `uv.lock` is expected:** Running `uv lock --refresh` after adding `[tool.uv.required-environments]` forced uv to emit metadata for both Linux/x86_64 and macOS/arm64. That’s why the lockfile gained hundreds of wheel URLs/hashes—it now records every candidate per required platform so future installs don’t miss a wheel. Only the current platform’s subset actually gets downloaded at install time.

## Dataset decisions

- **Importer switch (March 23, 2026):** Hugging Face removed `trust_remote_code`, so the old Flickr30k loader stopped working. Replaced it with the built-in `beans` dataset (available without custom scripts) and added `DATASET_NAME`, `DATASET_SPLIT`, and `SHUFFLE_SEED` constants for clarity. These settings let us keep pulling a tiny, reproducible image sample until we decide on the long-term dataset strategy.
