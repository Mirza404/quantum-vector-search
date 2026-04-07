# Research Questions & Thesis Guide

What the thesis asks, what we benchmark, and how the results lead to conclusions. For the underlying theory, see [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

## The Thesis Question

> **On a mathematically exact quantum simulator, can the quantum swap test perform cross-modal vector similarity search with accuracy comparable to classical search, and what quantum resource cost does it require as a function of vector dimension?**

Two parts: **accuracy** and **cost**.

Everything runs on **AerSimulator** (Qiskit's noiseless simulator). This means:
- Accuracy results are the **best-case ceiling** -- real hardware would score lower due to physical noise
- Circuit depth and qubit counts are **hardware-agnostic** -- properties of the circuit itself, not the execution platform

**What we are NOT asking:**
- Whether quantum is faster (it isn't, and we don't claim it is)
- Whether quantum will beat classical (unknown, depends on qRAM)

**What we ARE asking:** Does the algorithm work under ideal conditions, and what does it cost?

**In one sentence:** We're testing whether the quantum approach gives correct results, not whether it's fast.

<details>
<summary>Self-test</summary>

**Q: Why use a simulator instead of real quantum hardware?**
A: AerSimulator is mathematically exact -- it isolates shot noise from hardware noise. This gives us the best-case accuracy ceiling. Real hardware results would be strictly worse.

**Q: If we're not claiming quantum is faster, what's the point?**
A: To establish a baseline. If/when qRAM and better hardware arrive, we'll already know: the algorithm works, here's what it costs, here's the accuracy to expect.
</details>

---

## What Is Known vs. What This Project Contributes

| Claim | Status |
|---|---|
| Grover's gives O(sqrt(N)) quantum search | Proven (1996) |
| qRAM would unlock that advantage for vector search | Known theoretically |
| qRAM at practical scale | **Does not exist** |
| When quantum gate speed becomes competitive with classical | Unknown |
| Whether quantum will ever beat classical for this task | Unknown |

**What theory already establishes:**
- Quantum search has better asymptotic complexity, but only with qRAM
- Better Big O does NOT automatically mean faster wall clock -- constant factors (gate speed vs CPU speed) determine the crossover point
- The swap test computes the same result as classical cosine similarity -- it's the same measure via a different mechanism
- Shot noise makes it *less* accurate unless enough measurements are taken

**What this project contributes:**
1. **Empirical proof** that the swap test produces correct results on AerSimulator
2. **Measured circuit depth and qubit count** at each dimension from actual compiled circuits (stored in `benchmark_results` table)
3. **Identification of the bottleneck:** state preparation costs O(n) gates, same as classical
4. **A benchmarking framework** (`run_benchmarks.py` + `generate_report.py`) ready for re-evaluation when hardware improves

**What this project does NOT claim:**
- Quantum search is or will be faster
- We discovered a new speedup
- Wall-clock speed comparison is meaningful (it's not, on a simulator)

> **Analogy:** We're test-driving a prototype car on a treadmill. We can verify the engine works and measure its fuel consumption, but we can't compare its lap time to a real car on a real track. The treadmill (simulator) tells us about the engine, not about race performance.

**In one sentence:** Theory says quantum search could be better with qRAM; this project proves the algorithm itself works and measures exactly what it costs.

<details>
<summary>Self-test</summary>

**Q: What has this project proven that wasn't already known from theory?**
A: Theory says the swap test should work. We empirically verified it does, with specific MRR numbers, on a real codebase with CLIP embeddings and Flickr30k images.

**Q: What's the honest thesis statement?**
A: "The quantum swap test correctly performs cross-modal search on a simulator, but state preparation cost blocks any speedup. Our framework provides the baseline for re-evaluation as hardware improves."
</details>

---

## The Three Sub-Questions

### Sub-question 1: Does the quantum algorithm produce correct results?

**Metric:** MRR for each engine across all queries

**"Correct" means:** `qiskit_swap_test` MRR is close to `brute_force_cosine` MRR. Brute-force cosine is the ground truth -- deterministic and exact.

**How to interpret results:**

| Outcome | What it means |
|---|---|
| MRR matches | Swap test is correct at this shot count. Best-case ceiling |
| MRR significantly lower | Shot noise is scrambling rankings. Need more shots, or there's a bug |

**Engines involved:** All four -- `brute_force_cosine`, `faiss_flat_l2`, `quantum_mock_sampler`, `qiskit_swap_test`

The mock sampler is a **sanity check**: if it and the Qiskit engine produce similar MRR, the noise model is valid. If they differ, the real circuit has additional overhead.

**In one sentence:** Sub-question 1 asks "does the quantum engine find the right images?", measured by comparing its MRR to the classical ground truth.

<details>
<summary>Self-test</summary>

**Q: If `qiskit_swap_test` gets MRR 0.95 and `brute_force_cosine` gets 1.0, what do you conclude?**
A: The quantum algorithm is mostly correct -- shot noise causes slight ranking errors. Increasing shots should close the gap.

**Q: What role does `quantum_mock_sampler` play in answering this sub-question?**
A: It validates the noise model. If mock and Qiskit give similar MRR, we know the noise is just shot noise. If Qiskit is worse, there's additional circuit overhead.
</details>

---

### Sub-question 2: What does the quantum approach cost in hardware resources?

**Metrics:** Circuit depth and qubit count for each dimension

| Metric | Why it matters | Practical limit |
|---|---|---|
| **Circuit depth** | Deeper = more decoherence. NISQ devices handle ~100 layers | Extracted from `circuit.depth()` in `qiskit_swaptest.py` |
| **Qubit count** | More qubits = harder to allocate. Current QPUs: 100-1000 qubits | Extracted from `circuit.num_qubits` |

**"Acceptable" means:** Depth below ~100, qubits in the tens (13 at dim=64, 15 at dim=128)

**Concrete claim this enables:** "To run quantum vector search on 128-dim embeddings, hardware needs at least 15 qubits and coherence time sufficient for depth D."

**Engines:** `qiskit_swap_test` (real metrics from compiled circuits), `quantum_mock_sampler` (theoretical estimates based on amplitude encoding)

**In one sentence:** Sub-question 2 asks "what hardware does this need?", measured by circuit depth and qubit count at each vector dimension.

<details>
<summary>Self-test</summary>

**Q: Why are circuit metrics "hardware-agnostic"?**
A: They describe the circuit's structure (how many gates, how many qubits), not how any specific chip executes it. Same circuit runs on any quantum computer.

**Q: Where in the code are these metrics extracted?**
A: In `_run_swap_test()` in `qiskit_swaptest.py`, lines 99-101: `self._circuit_depth = circuit.depth()` and `self._num_qubits = circuit.num_qubits`.
</details>

---

### Sub-question 3: How many shots are needed for acceptable quality?

**Metric:** MRR at each shots value (configured in `benchmarks.yaml` under `shots_values:`)

**Why this transfers to real hardware:** Shot noise (1/sqrt(shots)) is identical on simulator and real hardware. Our curve is a **lower bound** -- real hardware would need *more* shots to compensate for physical noise.

**Engines:** `quantum_mock_sampler`, `qiskit_swap_test`

**In one sentence:** Sub-question 3 asks "how many measurements before the results are reliable?", giving the minimum shot budget under ideal conditions.

<details>
<summary>Self-test</summary>

**Q: If MRR is acceptable at 1024 shots on the simulator, what can you say about real hardware?**
A: Real hardware would need at least 1024 shots (probably more, to compensate for physical noise). Our number is the floor, not the ceiling.

**Q: How does the mock engine simulate different shot counts?**
A: It adds Gaussian noise with standard deviation `layers / max(1, shots)`. More shots = smaller noise = better accuracy.
</details>

---

### Bonus: Scaling with Dimension

Run each engine at dim=64 and dim=128 to measure:
- **MRR vs. dimension** -- does accuracy hold up at lower dimensions?
- **Circuit depth vs. dimension** -- linear growth? worse?
- **Qubit count vs. dimension** -- should be log2(dim) + 1 per register. Verify theory matches practice

---

## How to Read the Benchmark Report

`backend/docs/benchmark_report.md` (generated by `backend/scripts/generate_report.py`) maps directly to the thesis:

| Report section | Answers which sub-question |
|---|---|
| Quality KPIs by Engine | Sub-question 1 (accuracy) |
| Head-to-Head Quality Comparison | Sub-question 1, per-query detail |
| Quantum Circuit Complexity | Sub-question 2 (resource cost) |
| Quantum: Shots vs. Quality | Sub-question 3 (measurement budget) |
| Quality by Dimension | Scaling analysis |
| Speed Scaling by Dimension | Intra-engine only (NOT cross-engine) |

---

## The Thesis Conclusion Template

Fill in the blanks with your actual benchmark numbers:

1. **Accuracy:** `qiskit_swap_test` achieved MRR of ___ vs ___ for `brute_force_cosine`. The quantum algorithm [matches / falls short by N%] at [shot count] shots on AerSimulator. This includes shot noise but no physical hardware noise

2. **Resource cost:** At 64-dim: 13 qubits, depth ___. At 128-dim: 15 qubits, depth ___. Growth is [as expected / faster than expected]

3. **Shot budget:** MRR reaches acceptable threshold at ___ shots. Below that, ranking quality degrades significantly

4. **Bottleneck:** State preparation costs O(n) gates -- same as classical search. The quantum similarity computation is correct; the unsolved problem is efficient data loading (qRAM)

5. **Implication:** Quantum vector search is algorithmically correct but currently impractical at scale due to state preparation overhead and near-term hardware limitations. The benchmarking framework provides the baseline for re-evaluation

6. **Trade-off framing:** This fits the accuracy-speed trade-off already understood in classical search (HNSW sacrifices some accuracy for speed). Quantum search with qRAM would be the same trade-off at a different scale: some accuracy cost from shot noise, in exchange for better asymptotic complexity on large datasets

<details>
<summary>Self-test (defense prep)</summary>

**Q: What would you say if an examiner asks "So quantum is useless for search?"**
A: "Not useless -- algorithmically correct but currently blocked by state preparation cost. The algorithm itself works perfectly on the simulator. What's missing is qRAM technology to load data efficiently. Our framework is ready to re-evaluate when that changes."

**Q: What would you say if asked "Why not just test on real IBM hardware?"**
A: "Our circuits (13-15 qubits) fit on the free tier. The valuable result would be the accuracy gap between simulator and real hardware -- empirical evidence for why circuit depth matters. We plan to do this as an extension."

**Q: What is the single most important number in your benchmark report?**
A: "The MRR comparison between `qiskit_swap_test` and `brute_force_cosine`. If they match, the quantum algorithm is correct. Everything else follows from that."
</details>
