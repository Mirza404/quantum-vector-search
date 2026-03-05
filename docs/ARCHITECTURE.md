# MASTER ARCHITECTURE PLAN: QUANTUM VECTOR SEARCH

**Project:** Quantum-Enhanced Multi-Modal Vector Search: A Hybrid Database Web App
**Goal:** Directly compare classical vector search (FAISS) with emerging quantum-based techniques (Qiskit). Measure accuracy trade-offs, state-preparation overhead, and scaling behavior.

## CORE ENGINEERING PHILOSOPHY
To the engineer implementing this: **Do not deviate from these boundaries.** This architecture is designed to prevent rewriting the entire codebase a month before the presentation. 

1. **Modular Monolith:** Everything lives in one Python repository, but folders are strictly isolated. The web server knows nothing about quantum math.
2. **API-First Design:** Core logic runs behind a Python web framework (FastAPI/Flask). Hooking up the React frontend later should require zero backend changes.
3. **No UI in MVP:** Do not write any React code yet. The MVP is driven 100% by an Automated Python Benchmarking Script.
4. **Strategy Pattern:** Data loading, search engines, and data storage MUST use Interfaces (Base Classes). This allows us to swap components (like moving from a CSV to a Database) without touching the core search algorithm.

---

## Phase 1: The Repository Layer (Data Management)
**What it is:** The isolated module responsible for fetching the experimental dataset.

* **The Component:** Create a `BaseDataLoader` interface with a `get_dataset()` method.
* **MVP Implementation:** `LocalCSVDataLoader`. It reads a local directory of images and a CSV file mapping text descriptions to image paths.
* **The Strict Rule:** **NO user uploads for the MVP.** * **The Why:** To accurately measure "state-preparation overhead" and "scaling behavior", we need a perfectly stable, controlled baseline dataset. Unpredictable user uploads (varying file sizes/resolutions) will corrupt the empirical data.
* **Future-Proofing:** If we need a real database later, we just write `SQLDataLoader(BaseDataLoader)`. The search engine will not know the difference.

---

## Phase 2: The Incremental Embedding Pipeline (The Translator)
**What it is:** The ML pipeline (e.g., CLIP) that converts cross-modal data (text/images) into a single shared embedding space.

* **MVP Implementation:** A standalone setup script that runs *before* the main server starts. 
* **The Strict Rule:** **It MUST have an Incremental Cache.** Save embeddings to a local file (`embeddings.npy` or `embeddings.h5`). When the script runs, it checks the cache first. If an image is already embedded, skip it.
* **The Why:**  Re-running a heavy ML model on 500 images takes hours. If 1 image fails, or we add 10 new images to the dataset, the incremental cache ensures we only spend a few seconds processing the new data instead of starting from scratch.

---

## Phase 3: The Modular Search Engines (The Core Comparison)
**What it is:** Two parallel search engines strictly adhering to a `BaseSearchEngine` interface.

* **MVP Implementations:**
    1. `FAISSEngine`: The classical vector search baseline.
    2. `QiskitEngine`: The quantum module executing on a local simulator. It encodes classical vectors into quantum states and calculates similarity (e.g., using the swap test).
* **The Strict Rule:** Engines MUST accept **dynamic parameters** via their `search(query, params)` function (e.g., `dimensions=4`, `shots=1024`, `encoding_type='amplitude'`). 
* **The Why:** We must apply dimensionality reduction (like PCA) *on the fly* inside the engine. If we hardcode a 512-dimension vector into the quantum engine, the local simulator will crash instantly due to RAM limits. We need to test different dimensions to find the sweet spot.
* **Future-Proofing:** Moving to real quantum hardware later simply means passing `hardware='ibm_cloud'` into the parameters.

---

## Phase 4: The Iterative Benchmarking & Storage (The MVP Brain)
**What it is:** An automated testing script and a `BaseBenchmarkStorage` interface to record the empirical study.

* **MVP Implementation:** `CsvMarkdownStorage`.
* **How It Works:**
    1. The script fires a batch of 30 automated text queries at both engines (e.g., using `dimensions=4`).
    2. It captures execution speed, accuracy, and data transition overhead.
    3. `CsvMarkdownStorage` saves the raw numbers to `results.csv` and auto-generates a human-readable `Report.md`.
* **The Strict Rule:** The storage must **Append, not Overwrite**. 
* **The Why:**  When we run a test at `dimensions=4` and then again at `dimensions=8`, the script must append the new results side-by-side in the Markdown file. We need to easily read these files during the MVP phase to visually prove the scaling behavior.
* **Future-Proofing (The Database Transition):** This is exactly why we use the Strategy Pattern. Later, we will write `DatabaseStorage(BaseBenchmarkStorage)`. The core testing script stays exactly the same, but it starts saving these benchmark runs into a real database instead of a CSV.

---

## Phase 5: The API & React Dashboard (The Final Deliverables)
**What it is:** A Python web server (FastAPI/Flask) that feeds data to the final React UI.

* **The Backend (API):** Expose two endpoints:
    * `POST /search`: Accepts a text query, routes it to both `FAISSEngine` and `QiskitEngine` to run in parallel, and returns the image IDs.
    * `GET /api/benchmarks`: Retrieves the historical test data saved by Phase 4.
* **The Frontend (React - POST-MVP):** * **Feature 1: User Search:** A text bar that returns side-by-side images from both engines.
    * **Feature 2: Benchmark Dashboard:**  This is where the Phase 4 database shines. React will call the `/api/benchmarks` endpoint and use charting libraries (like Recharts or Chart.js) to display beautiful, interactive grids and graphs of our empirical data (e.g., Accuracy vs. Dimensions, or Classical Speed vs. Quantum Speed).
* **The Why:** Building the backend as an API during the MVP phase means that fulfilling the final "web-based dashboard" requirement is incredibly easy. The frontend team just consumes the API endpoints without needing to touch the complex quantum logic.
