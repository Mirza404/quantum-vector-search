# Quantum-Enhanced Multi-Modal Vector Search: A Hybrid Database Web App 

## Problem Statement & Project Overview
Modern applications often require similarity search on large amounts of cross-modal data (for example: searching images using text description). Classic vector and embedding methods provide sufficient solutions, however new quantum computing techniques could offer performance and accuracy improvement. In this project, we aim to bridge the gap in existing research by directly comparing classical vector search methods with emerging quantum-based techniques.

We plan to create a hybrid web application that performs cross-modal search using both classical and quantum engines. Results and metrics (accuracy and performance) will be displayed in a web-based dashboard. Since current quantum hardware and simulators operate differently than classical processors, our primary goal is not merely to compare raw execution speed, as this heavily depends on the underlying hardware rather than just the algorithmic implementation. Instead, our empirical study will evaluate accuracy trade-offs, state-preparation overhead (data transition), and scaling behavior to determine when, or it, quantum processing offers theoretical or practical benefits at a small scale. The project scope includes system design, implementation, testing and result analysis. This project combines software engineering implementation with empirical evaluation.

## Objectives & Expected Deliverables
**Objectives:**
* Develop two parallel search engines: classical vector and quantum model, so they can be compared side-by-side.
* Build a share embedding pipeline that converts text and images into a single space, so their vector representations can be compared.
* Desing and develop interactive web interface that allows users to submit queries and view their results.
* Provide analysis about results and draw conclusions based on returned metrics.

**Expected Deliverables:**
* Fully functional web application that demonstrates the cross-modal search.
* Experimental dataset and evaluation pipeline.
* Comparison between classical and quantum methods.
* Conclusion about practical benefits and limitations of quantum vector search.

## Core Engineering Philosophy
To ensure project stability and prevent late-stage rewrites, the implementation strictly adheres to the following boundaries:
* **Modular Monolith:** Everything lives in one Python repository with strictly isolated folders. The web server remains agnostic to quantum math.
* **API-First Design:** Core logic runs behind a Python web framework (FastAPI/Flask). Hooking up the React frontend requires zero backend changes.
* **No UI in MVP:** The MVP is driven 100% by an Automated Python Benchmarking Script. No React code is written in this phase.
* **Strategy Pattern:** Data loading, search engines, and data storage MUST use Interfaces (Base Classes) to allow swapping underlying technologies while keeping the codebase clean and modular.

## System Architecture & Implementation Phases
First step in our approach is to convert data into numerical embedding using machine learning models. They will be stored and queried using a classical vector search system like FAISS. We will also implement quantum similarity module using quantum computing frameworks such as Qiskit. Classical vectors will be encoded into quantum states.

### Phase 1: The Repository Layer (Data Management)
Responsible for fetching the experimental dataset.
* **Component:** `BaseDataLoader` interface with a `get_dataset()` method. 
* **MVP Implementation:** `LocalCSVDataLoader` (reads local images and a CSV mapping text to image paths).
* **Strict Rule:** NO user uploads for the MVP. An unpredictable dataset corrupts empirical data. A stable, controlled baseline is required.

### Phase 2: The Incremental Embedding Pipeline (The Translator)
The ML pipeline (e.g., CLIP) that converts cross-modal data (text/images) into a single shared embedding space.
* **MVP Implementation:** A standalone setup script running before the main server to process and save the dataset embeddings manually, avoiding repetitive model execution.

### Phase 3: The Modular Search Engines (The Core Comparison)
Two parallel engines strictly adhering to a `BaseSearchEngine` interface.
* **MVP Implementations:**
    1. `FAISSEngine`: Classical vector search baseline.
    2. `QiskitEngine`: Quantum module on a local simulator. Similatiry between vectors will be calculated using quantum operations (like swap test). We plan to execute the comparison on simulators or available cloud-based quantum hardware.
* **Strict Rule:** Engines MUST accept dynamic parameters via `search(query, params)` (e.g., `dimensions=4`, `shots=1024`, `encoding_type='amplitude'`). Dimensionality reduction (e.g., PCA) must be applied on the fly to prevent RAM crashes on local simulators. Moving to real hardware means passing `hardware='ibm_cloud'`.

### Phase 4: Database Benchmarking Storage, Sharing & Aggregation
Responsible for executing, storing, and compiling the empirical study. Writing directly to a database simplifies the backend requirements for Phase 5.
* **The Strategy Pattern:** Data storage MUST use a `BaseBenchmarkStorage` interface (e.g., implemented as `DatabaseStorage`). This keeps database communication clean and decoupled from the search logic.
* **Direct DB Writes:** We will exclusively write benchmark results directly to a Database. There is no CSV file support.
* **Granular Storage:** Results from each distinct benchmark run are stored granularly in the DB (e.g., linked to specific run IDs or configuration profiles).
* **Aggregation to Markdown:** Analysis is decoupled from execution. A dedicated script will read the granular data from the database and aggregate it into a single, human-readable Markdown report (`Report.md`).
* **Strictly Decoupled State Sharing:** To allow team members to share the local database state seamlessly, the infrastructure and database dumps must be strictly decoupled into three isolated layers:
    1. **Docker Infrastructure:** The container setup only spins up the raw, empty database engine. It knows nothing about our tables or data.
    2. **Schema Dump:** A dedicated script/file (`schema.sql`) that only handles creating the empty table structures and relations required for the project.
    3. **Data Dump:** A separate script/file (`data.sql`) that extracts and loads only the actual benchmark result data. This separation allows team members to safely wipe, update, or share experimental data without breaking or overwriting the underlying database architecture.
* **Isolated Database Directory Structure:** To maintain a clean Modular Monolith, all database infrastructure and dump files must live strictly outside of the Python API. The Python backend only connects to the database; it does not manage its infrastructure. 

### Phase 5: API & React Dashboard (The Final Deliverables)
The web application's frontend will be built using React, while we are leaning toward Python for the backend due to its vast ecosystem of libraries that support quantum computing integration.
* **The Backend (API):** Exposes endpoints:
    * `POST /search`: Routes query to both engines in parallel and returns image IDs. When users enter queries, both engines will work in parallel to provide accuracy measurements and metrics.
    * `GET /api/benchmarks`: Retrieves historical test data directly from the Database.
* **The Frontend (React - POST-MVP):**
    * **User Search:** Text bar returning side-by-side images.
    * **Benchmark Dashboard:** Consumes `/api/benchmarks` to chart empirical data (Accuracy vs. Dimensions, Speed comparisons).

## 6. Configuration-Driven Benchmarking Strategy
We will automate the empirical study using a highly controlled, configuration-driven approach to avoid repetitive work and complex state management.

### A. The "Ground Truth" Evaluation
* Uses a JSON test suite of 30-50 predefined text queries, each mapped to a `target_image` (e.g., `image_042.jpg`).
* **Grading Logic:** The script evaluates the top 3 results from both engines. #1 placement = 100%, lower placements = reduced scores, misses = 0%.

### B. Configuration Files & Granular Execution
* **Manual Configurations:** We will define exact benchmark parameters (e.g., target engine, dimensions, shots) inside configuration files edited by us *before* running the scripts.
* **Isolated Runs:** The testing script executes strictly based on the provided config file. You can run one specific benchmark at a time (e.g., running *only* "Quantum 2 dim" or *only* "Classical Vector").

### C. Granular Data Recording (To Database)
During an isolated run, the script records:
1. **Classical (FAISS):** Execution time and returned IDs.
2. **Quantum (Qiskit):** State-Preparation Time vs. Circuit Execution Time (tracked separately).
3. **Accuracy:** Computed against the Ground Truth target.
*The results are then passed to the `BaseBenchmarkStorage` implementation to be saved directly into the database as a distinct dataset for that specific configuration.*

### D. The Aggregation Script
Because benchmarks are executed and stored granularly in the DB, a separate Python aggregation script is required. This script will:
1. Query all the separated benchmark results from the database.
2. Compile, compare, and analyze the metrics.
3. Automatically generate the final, aggregated, human-readable Markdown file (`Report.md`).

### E. Empirical Metrics Measured
1. **Accuracy Trade-offs:** The Ground Truth score. Measures accuracy lost/gained by translating classical data into quantum states using probabilities (shots) and dimensionality reduction.
2. **State-Preparation Overhead:** Time taken to encode classical numerical vectors into qubits (e.g., Amplitude Encoding). Critical to see if data-loading negates the quantum speed advantage.
3. **Raw Execution Speed:** FAISS search time vs. Qiskit Swap Test circuit + measurement time.
4. **Scaling Behavior:** How metrics change across our granular runs when vector dimensions increase (e.g., 2 to 4 to 8). Tracks if quantum execution time scales linearly or exponentially.