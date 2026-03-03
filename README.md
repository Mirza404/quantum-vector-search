# Quantum Vector Search (Prototype)

This repository currently houses a minimal prototype that compares two interchangeable search engines against a toy vector dataset. It is deliberately small, just so I could test how it all worked.

## What Works Now

- `backend/main.py` loads a preset, four-item, two-dimensional dataset, then instantiates two engines, and prints their top-2 matches for a fixed query vector.
- `qvs.engines.VectorMockEngine` implements a classical baseline that ranks vectors with negative L2 distance.
- `qvs.engines.QuantumMockEngine` normalizes vectors, estimates overlap probabilities, and injects Gaussian noise controlled by `shots`, `layers`, and a deterministic `seed`.
- The engines share a `SearchEngineStrategy` interface (`build_index` + `search`) so callers can swap them without touching the rest of the code.

## Repository Layout

```
.
├── backend/
│   ├── main.py            # demo entrypoint
│   ├── pyproject.toml     # uv project metadata 
│   └── src/qvs/engines/   # mock engine implementations + base classes
└── README.md
```

Empty namespace packages already exist for `qvs.repository` and `qvs.benchmark`; they will gain real implementations as we bring in the data layer and benchmarking workflow from the master architecture plan.

## Running the Demo

```bash
cd backend
uv pip install -e .
uv run python main.py
```

You should see two sections of output, one per engine, each listing the winning IDs, scores, and metadata describing the scoring method.

## Current Limitations

- There is no FastAPI server, repository layer, embedding pipeline, or benchmarking storage yet—`main.py` is the only entry point.
- The dataset is hard-coded. We have yet to load it.
- Both quantum and vector files are mocks. They do not call any of the actual engines.
- Tests are missing.

P.S. I was planning to make a branch for these mocks, but I guess we will just have to delete them as we go because I forgot to checkout before I added them :( .