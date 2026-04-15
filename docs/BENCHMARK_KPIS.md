# Benchmark KPI Definitions

Three metrics answer three different questions about the engines. For theory: [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

## 1. MRR — Does it find the right answer?

**Mean Reciprocal Rank** = average of 1/(rank of correct result) across all queries.

- Rank 1 → 1.0, rank 2 → 0.5, rank 5 → 0.2
- Evaluated over top_k results (default 10). Correct result outside top 10 = 0 for that query.
- This is the primary accuracy metric. Directly comparable across all engines.

> "How far does the user scroll before finding the right image?" MRR 1.0 = always first.

---

## 2. Operation Count — How does it scale?

The number of times the core operation runs per query — literally the loop iteration count. Hardware-agnostic: a slow laptop and a fast server run the same number of iterations.

| Engine | Loop runs N times? | Complexity |
|---|---|---|
| `brute_force_cosine` | Yes — one comparison per vector | O(N) |
| `faiss_flat_l2` | Yes — one comparison per vector | O(N) |
| `qiskit_swap_test` | Yes — one circuit per vector | O(N) |
| `qiskit_grover` | No — floor(π√N/4) oracle cycles | **O(√N)** |

This is why you can't compare wall-clock time across engines — one runs on a CPU, one on a simulator, one eventually on quantum hardware. Iteration count is the only fair comparison.

Stored in `benchmark_results.oracle_calls`, computed by `_oracle_calls()` in `run_benchmarks.py`.

---

## 3. Circuit Metrics — What hardware does it need? (quantum only)

- **Circuit depth** — number of sequential gate layers. Deeper = more noise on real hardware. NISQ devices handle ~100 layers reliably.
- **Qubit count** — qubits the circuit requires. 64-dim swap test = 13 qubits. 128-dim = 15 qubits.
- **Shots vs. MRR** — how accuracy changes as you run more circuit shots. More shots = less noise = better MRR.

These answer "could this run on real hardware, and what would it cost?"

Stored in `benchmark_results.circuit_depth`, `num_qubits`.

---

## What We Don't Report (and why)

**Wall-clock time is never compared across engines.** Classical runs on CPU, quantum runs on a simulator that uses exponentially more CPU to fake quantum states. Comparing their runtimes would just show "simulation is slow" — not anything about the quantum algorithm itself. Simulator wall-clock is stored in the DB but excluded from report graphs.

---

**Self-test**

**Q: What's the only valid cross-engine speed metric?**
A: Operation count. Classical = N iterations, Grover = floor(π√N/4) iterations.

**Q: Why not compare wall-clock times across engines?**
A: Simulator wall-clock measures how expensive it is to *simulate* quantum on a CPU — not how fast the quantum algorithm is. It would make quantum look worse for the wrong reason.
