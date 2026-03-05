# AUTOMATED BENCHMARKING STRATEGY

**Goal:** Automate the empirical study to gather massive amounts of data without manual testing. This script is the "brain" of our MVP and is the only way to mathematically prove the limitations and benefits of the quantum search engine.

---

## 1. The "Ground Truth" Trick (How to Measure Accuracy)
To automate the grading of our search engines, the script must know the "correct" answer in advance. We will use a **Ground Truth Dataset**.

* **How it works:** We create a JSON test suite of 30-50 predefined text queries. Each query includes the ID of the image that *should* be the perfect match.
* **Example:** * `query`: "A red sports car parked on the street"
    * `target_image`: `image_042.jpg`
* **The Grading Logic:** The script looks at the top 3 results from FAISS and Qiskit. 
    * If an engine returns `image_042.jpg` as the #1 result, it gets 100% accuracy for that test.
    * If it returns it as #3, it gets a lower score. 
    * If it misses entirely, it gets 0%.

---

## 2. The Resumable Benchmarking Loop (Checkpointing)
The automated script (`run_benchmarks.py`) will loop through our Ground Truth test suite. Because quantum simulations are incredibly slow, **the script MUST be resumable.** If the script crashes, is manually canceled, or your computer goes to sleep after an hour, you should never have to start from zero.

* **The Checkpoint Rule:** Before running a query, the script must check the `results.csv` file. If `query_04` at `dimensions=8` is already recorded, the script skips it and moves to `query_05`. 
* **The Benefit:** You can cancel a 5-hour benchmark run halfway through, fix a bug in your code, restart the script, and it will instantly pick up exactly where it left off.



**For every un-benchmarked query in the suite, the script will:**
1. **Run Classical (FAISS):** Start the timer, send the vector, stop the timer. Record the execution time and the returned image IDs.
2. **Run Quantum (Qiskit):** Start the timer. 
    * *CRITICAL:* We must use separate timers inside this engine to track **State-Preparation Time** vs. **Circuit Execution Time**. 
3. **Calculate Accuracy:** Compare the returned IDs from both engines against the Ground Truth target to calculate the accuracy score.
4. **Save Immediately:** Append the result to the CSV immediately after the query finishes, creating the checkpoint.
5. **Iterate Parameters:** Once the 50-query suite finishes at `dimensions=4`, the script changes the configuration to `dimensions=8` and begins again (skipping any `dimensions=8` runs that are already logged).

---

## 3. What EXACTLY We Are Measuring
To formulate our final conclusion for the committee, the script's `CsvMarkdownStorage` module must log these four specific metrics for every single run:

### A. Accuracy Trade-offs
* **What it is:** The Ground Truth score.
* **Why:** Quantum simulators use probabilities (shots) and heavy dimensionality reduction (shrinking the vectors). We need to measure exactly how much accuracy we lose (or gain) by translating our classical data into a quantum state.

### B. State-Preparation Overhead (Data Transition Time)
* **What it is:** The exact time it takes to encode our classical numerical vectors into qubits (e.g., using Amplitude Encoding).
* **Why:** This is the biggest bottleneck in quantum machine learning. We must measure this *separately* from the actual search time to prove if the data-loading process negates the quantum speed advantage.

### C. Raw Execution Speed
* **What it is:** The time FAISS takes to search the index vs. the time Qiskit takes to run the Swap Test circuit and measure the results.
* **Why:** To establish the baseline computational speed difference between classical processors and quantum simulators for our specific task.

### D. Scaling Behavior
* **What it is:** How the first three metrics change when the problem gets harder.
* **Why:**  If we increase the vector dimensions from 4 to 8 to 16, does the quantum simulator's execution time scale linearly, or does it explode exponentially? Tracking this behavior is the core requirement of our empirical study.

## 4. Cache Invalidation (Handling Dataset or Test Suite Changes)
If the experimental dataset (images/text) or the Ground Truth test suite (JSON) changes in ANY way, **we do not attempt to surgically update the logs or the cache.** Attempting to track granular changes introduces massive risk of data corruption and invalidates the scientific baseline of the empirical study.

**The "Clean Slate" Protocol:**
If the data changes, we execute a full reset:
1. Delete the `embeddings.npy` (or `.h5`) cache file.
2. Delete the `results.csv` and `Report.md` benchmark logs.
3. Re-run the entire pipeline from zero. 

*Optional Quality-of-Life Feature:* We can include a `reset_environment.py` script or a `--force-refresh` flag in the CLI that automatically deletes these specific files before starting the run, ensuring our new data is 100% clean.
