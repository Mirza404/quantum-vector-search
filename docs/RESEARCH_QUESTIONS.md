# Research Questions & Thesis Guide

What the thesis asks, what we benchmark, and how results lead to conclusions. For theory: [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

## The Main Question

> **On a noiseless quantum simulator, can quantum search algorithms (swap test and Grover's) perform cross-modal vector similarity search with accuracy comparable to classical search, and what are the quantum resource costs as a function of vector dimension and dataset size?**

Two parts: **accuracy** (does it work?) and **cost** (what does it need?).

Everything runs on **AerSimulator** (Qiskit's noiseless simulator):
- Accuracy results are the **best-case ceiling** -- real hardware would score lower due to physical noise
- Circuit depth and qubit counts are **hardware-agnostic** -- properties of the algorithm, not the chip

**What we're NOT asking:** Is quantum faster? (It isn't without qRAM.) Will it beat classical? (Unknown, depends on future hardware.)

**What we ARE asking:** Do the algorithms produce correct results, and what do they cost?

<details><summary>Self-test</summary>

**Q: Why use a simulator instead of real hardware?**
A: AerSimulator is mathematically exact -- isolates shot noise from hardware noise. Gives the best-case accuracy ceiling.

**Q: If not claiming quantum is faster, what's the point?**
A: Establishing a baseline. When qRAM and better hardware arrive, we already know the algorithms work and what they cost.
</details>

---

## What's Known vs. What This Project Adds

| Known from theory | This project contributes |
|---|---|
| Grover's gives O(sqrt(N)) search | **Working Grover oracle** verified on simulator (`qiskit_grover.py`) |
| Swap test computes squared similarity | **Empirical proof** it matches classical MRR on CLIP embeddings |
| qRAM would unlock end-to-end speedup | **Measured circuit depth and qubit counts** from compiled Qiskit circuits |
| qRAM doesn't exist at practical scale | **Empirical O(sqrt(N)) oracle scaling** data across dataset sizes |
| State prep is O(N) without qRAM | **Complete benchmarking framework** ready for re-evaluation |

**What we do NOT claim:** quantum is faster, we found a new speedup, or wall-clock comparison on a simulator is meaningful.

> Test-driving a prototype car on a treadmill. We can verify the engine works and measure fuel consumption, but can't compare lap times to a real car on a real track.

<details><summary>Self-test</summary>

**Q: What has this project proven beyond theory?**
A: Theory says the swap test and Grover should work. We verified it empirically with specific MRR numbers on CLIP embeddings and Flickr30k images, and measured actual circuit costs.
</details>

---

## The Sub-Questions

### 1. Does the quantum algorithm produce correct results?

**Metric:** MRR for each engine. "Correct" means `qiskit_swap_test` and `qiskit_grover` MRR are close to `brute_force_cosine` MRR.

| Outcome | Interpretation |
|---|---|
| MRR matches | Algorithm is correct at this shot count |
| MRR significantly lower | Shot noise is scrambling rankings -- need more shots |

The mock sampler (`quantum_mock_sampler`) is a sanity check: if it and the Qiskit engines produce similar MRR, the noise model is valid.

**In one sentence:** Does the quantum engine find the right images, measured by comparing its MRR to the classical ground truth?

<details><summary>Self-test</summary>

**Q: If Qiskit gets MRR 0.95 and brute-force gets 1.0?**
A: Quantum is mostly correct -- shot noise causes slight ranking errors. More shots should close the gap.
</details>

### 2. What hardware resources does it need?

**Metrics:** Circuit depth and qubit count at each dimension.

| Metric | Why it matters | Practical limit |
|---|---|---|
| **Circuit depth** | Deeper = more decoherence | NISQ devices: ~100 layers |
| **Qubit count** | More = harder to allocate | Current QPUs: 100-1,000 |

Extracted from compiled Qiskit circuits: `circuit.depth()` and `circuit.num_qubits` in `_run_swap_test()` and `_build_grover_circuit()`.

**Concrete claim format:** "128-dim swap test needs 15 qubits and circuit depth D."

<details><summary>Self-test</summary>

**Q: Why are circuit metrics "hardware-agnostic"?**
A: They describe circuit structure (gates, qubits), not how a specific chip executes it. Same circuit, any quantum computer.
</details>

### 3. How many shots for acceptable quality?

**Metric:** MRR at each shots value (configured in `benchmarks.yaml` under `shots_values:`).

Shot noise (1/sqrt(shots)) is identical on simulator and real hardware. Our results are a **lower bound** -- real hardware needs at least this many shots, probably more to compensate for physical noise.

<details><summary>Self-test</summary>

**Q: MRR acceptable at 1024 shots on simulator -- what about real hardware?**
A: At least 1024, probably more. Our number is the floor.
</details>

### 4. How does the Grover engine scale?

**Metric:** Oracle call count as a function of dataset size N.

- Classical: N comparisons per query
- Grover: floor(pi*sqrt(N)/4) oracle calls per query
- Stored in `benchmark_results.oracle_calls`, computed by `_oracle_calls()` in `run_benchmarks.py`

Plot both curves against N. The divergence demonstrates the O(N) vs O(sqrt(N)) scaling difference -- the entire argument for quantum search at scale.

### Bonus: Scaling with dimension

Run at dim=64 and dim=128 to measure:
- MRR vs. dimension (does accuracy hold at lower dims?)
- Circuit depth vs. dimension (linear? worse?)
- Qubit count vs. dimension (should be log2(dim) per register + 1 ancilla -- verify)

---

## Reading the Benchmark Report

`backend/docs/benchmark_report.md` (generated by `scripts/generate_report.py`):

| Report section | Answers |
|---|---|
| Quality KPIs by Engine | Sub-Q 1 (accuracy) |
| Head-to-Head Comparison | Sub-Q 1, per-query detail |
| Quantum Circuit Complexity | Sub-Q 2 (resource cost) |
| Shots vs. Quality | Sub-Q 3 (measurement budget) |
| Operation Count Scaling | Sub-Q 4 (O(N) vs O(sqrt(N))) |
| Quality by Dimension | Scaling analysis |
| Speed by Dimension | Per-engine only (NOT cross-engine) |

---

## Thesis Conclusion Template

Fill in with your actual benchmark numbers:

1. **Accuracy:** `qiskit_swap_test` MRR = ___ vs `brute_force_cosine` MRR = ___. `qiskit_grover` MRR = ___. Quantum [matches / falls short by ___] at [shots] shots
2. **Resource cost:** 64-dim swap test: 13 qubits, depth ___. 128-dim: 15 qubits, depth ___. Grover at N=___: ___ oracle calls
3. **Shot budget:** MRR reaches acceptable threshold at ___ shots
4. **Oracle scaling:** Grover uses floor(pi*sqrt(N)/4) oracle calls vs N classical comparisons, verified at N = ___, ___, ___
5. **Bottleneck:** State preparation = O(N) without qRAM. Algorithms are correct; the unsolved problem is efficient data loading
6. **Implication:** Algorithmically correct but currently impractical. Framework provides the baseline for re-evaluation

<details><summary>Defence prep</summary>

**Q: "So quantum is useless for search?"**
A: "Not useless -- algorithmically correct but blocked by state preparation cost. The swap test works on the simulator. Grover's oracle scales as O(sqrt(N)). What's missing is qRAM. Our system is architecturally ready for when that hardware exists."

**Q: "Why not test on real IBM hardware?"**
A: "Our circuits fit the free tier. The valuable result would be the accuracy gap between simulator and real hardware. We plan this as a separate IBM demonstration, not the core benchmark."

**Q: "What's the single most important number?"**
A: "MRR comparison between quantum and classical engines. If they match, the algorithms are correct. Everything else follows."
</details>
