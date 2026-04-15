# Research Questions & Thesis Guide

What the thesis asks, what we benchmark, and how results lead to conclusions. For theory: [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

## What This Project Actually Is

This is a bachelor's graduation project. It is **not** discovering a new algorithm, proving a new theorem, or building something commercially viable. That is fine — that is not what a bachelor's project is for.

What this project does:

1. **Engineering:** Builds a complete, working system — CLIP embedding pipeline, four search engines (two classical, two quantum), PostgreSQL storage, FastAPI backend, React frontend. This is non-trivial and demonstrates real software engineering capability.

2. **Empirical verification:** Theory says Grover's algorithm scales as O(sqrt(N)). We actually ran it, measured oracle calls at multiple dataset sizes, and verified the curve. That is a real empirical contribution, not just reading a textbook.

3. **Honest analysis:** We documented exactly why quantum search cannot beat classical today (qRAM does not exist), what the hardware would need to look like, and where the theoretical limits are. Most student projects either overclaim or ignore limitations. This one engages with them clearly.

4. **Framework:** The pluggable architecture means the benchmark is ready to re-run if relevant hardware improves.

**The contribution in one sentence:** We built a working quantum vector search system, empirically verified that the algorithms behave as theory predicts, and produced an honest analysis of why the speedup does not materialise in practice.

**What to say if asked "did you discover anything new?":** No. We implemented and verified existing algorithms on real quantum simulator infrastructure, measured their behaviour empirically, and built production-quality surrounding infrastructure. The value is in the engineering, the empirical data, and the depth of understanding demonstrated.

---

## The Main Question

> **On a noiseless quantum simulator, can quantum search algorithms (swap test and Grover's) perform cross-modal vector similarity search with accuracy comparable to classical search, and what are the quantum resource costs as a function of vector dimension and dataset size?**

Two parts: **accuracy** (does it work?) and **cost** (what does it need?).

Everything runs on **AerSimulator** (Qiskit's noiseless simulator):
- Accuracy results are the **best-case ceiling** -- real hardware would score lower due to physical noise
- Circuit depth and qubit counts are **hardware-agnostic** -- properties of the algorithm, not the chip

**What we're NOT asking:** Is quantum faster? (It isn't without qRAM.) Will it beat classical? (Unknown, depends on future hardware.)

**What we ARE asking:** Do the algorithms produce correct results, and what do they cost?

**Self-test**

**Q: Why use a simulator instead of real hardware?**
A: Two reasons. First, AerSimulator is mathematically exact -- isolates shot noise from hardware noise, giving the best-case accuracy ceiling. Second, real IBM hardware on the free tier has queue times that can stretch to hours, making iterative benchmarking impractical.

**Q: If not claiming quantum is faster, what's the point?**
A: Establishing a baseline. When qRAM and better hardware arrive, we already know the algorithms work and what they cost.


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

**Self-test**

**Q: What has this project proven beyond theory?**
A: Theory says the swap test and Grover should work. We verified it empirically with specific MRR numbers on CLIP embeddings and Flickr30k images, and measured actual circuit costs.


---

## The Sub-Questions

### 1. Does the quantum algorithm produce correct results?

**Metric:** MRR for each engine. "Correct" means `qiskit_swap_test` and `qiskit_grover` MRR are close to `brute_force_cosine` MRR.

| Outcome | Interpretation |
|---|---|
| MRR matches | Algorithm is correct at this shot count |
| MRR significantly lower | Shot noise is scrambling rankings -- need more shots |

**In one sentence:** Does the quantum engine find the right images, measured by comparing its MRR to the classical ground truth?

**Self-test**

**Q: If Qiskit gets MRR 0.95 and brute-force gets 1.0?**
A: Quantum is mostly correct -- shot noise causes slight ranking errors. More shots should close the gap.


### 2. What hardware resources does it need?

**Metrics:** Circuit depth and qubit count at each dimension.

| Metric | Why it matters | Practical limit |
|---|---|---|
| **Circuit depth** | Deeper = more decoherence | NISQ devices: ~100 layers |
| **Qubit count** | More = harder to allocate | Current QPUs: 100-1,000 |

Extracted from compiled Qiskit circuits: `circuit.depth()` and `circuit.num_qubits` in `_run_swap_test()` and `_build_grover_circuit()`.

**Concrete claim format:** "128-dim swap test needs 15 qubits and circuit depth D."

**Self-test**

**Q: Why are circuit metrics "hardware-agnostic"?**
A: They describe circuit structure (gates, qubits), not how a specific chip executes it. Same circuit, any quantum computer.


### 3. How many shots for acceptable quality?

**Metric:** MRR at each shots value (configured in `benchmarks.yaml` under `shots_values:`).

Shot noise (1/sqrt(shots)) is identical on simulator and real hardware. Our results are a **lower bound** -- real hardware needs at least this many shots, probably more to compensate for physical noise.

**Self-test**

**Q: MRR acceptable at 1024 shots on simulator -- what about real hardware?**
A: At least 1024, probably more. Our number is the floor.


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

Defence prep

**Q: "So quantum is useless for search?"**
A: "Algorithmically correct, but practically blocked on two fronts. First, qRAM doesn't exist — and even building it requires O(N) quantum routing nodes as hardware, so at 1M vectors you'd need roughly a billion physical qubits just for memory, not search. Second, even with ideal qRAM, Grover runs in O(sqrt(N)) while HNSW already achieves O(log N) classically — so quantum search would still lose on speed for the approximate case that covers most real applications. The honest answer is: the algorithms work, the oracle scaling is verified, but the path to practical quantum vector search requires hardware advances far beyond 'just build qRAM'."

**Q: "Why not test on real IBM hardware?"**
A: "Two practical reasons: free tier queue times can stretch to hours, making iterative benchmarking impractical, and turnaround is slow. The simulator gives mathematically exact results and is the right tool for establishing correctness. Real hardware would add one interesting data point — the accuracy gap between simulator and real hardware due to physical noise — but that's a future extension, not the core benchmark."

**Q: "What's the single most important number?"**
A: "MRR comparison between quantum and classical engines. If they match, the algorithms are correct. Everything else follows."

