# Quantum Vector Search Analysis

Why quantum vector search can't deliver a real speedup today, what our benchmarks actually measure, and why this project still has value. This is the authoritative reference for the thesis defence on the qRAM problem, benchmarking strategy, and scaling theory.

For algorithm basics: [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md). For KPI definitions: [BENCHMARK_KPIS.md](BENCHMARK_KPIS.md).

---

## The Two-Step Problem

Quantum vector search is two separate steps, and confusing them causes all the misunderstanding.

### Step 1: Loading data into superposition (broken)

To get any quantum speedup, all N database vectors need to be in quantum superposition simultaneously. This requires **qRAM** (Quantum Random Access Memory) -- hardware that can load N classical data items into superposition in O(log N) time.

**qRAM does not exist.** Not on IBM's machines, not anywhere.

Without qRAM, loading vectors requires O(N) gate operations -- the same as classical linear scan. The speedup is erased before search even starts.

### Step 2: Searching (works)

Once data is in superposition, **Grover's algorithm** finds the closest match in O(sqrt(N)) oracle calls instead of O(N) classical comparisons. This is mathematically proven.

**The catch:** This speedup only matters if Step 1 is solved. Without qRAM:

| Method | Complexity |
|---|---|
| Classical | O(N) |
| Quantum without qRAM | O(N) loading + O(sqrt(N)) search = **still O(N)** |
| Quantum with qRAM | O(log N) loading + O(sqrt(N)) search = **O(sqrt(N))** |

> Like having a super-fast search engine but the only way to enter data is typing each record one at a time. The search is fast, but the data entry bottleneck kills the advantage.

**In one sentence:** The search algorithm works (we prove it), but the data loading step can't be done efficiently without hardware that doesn't exist yet.

<details><summary>Self-test</summary>

**Q: What are the two steps?**
A: (1) Loading data into superposition (needs qRAM, O(N) without it), (2) Searching (O(sqrt(N)) with Grover's).

**Q: Why doesn't the O(sqrt(N)) search help without qRAM?**
A: The O(N) loading cost dominates. O(N) + O(sqrt(N)) = O(N).
</details>

---

## How Grover's Algorithm Gets O(sqrt(N))

Classical search checks items one at a time. Grover's exploits **amplitude amplification**:

1. **Start in uniform superposition** -- all N items have equal amplitude 1/sqrt(N)
2. **Oracle** -- flips the phase of the correct answer from +1/sqrt(N) to -1/sqrt(N). Invisible to measurement (probability is amplitude *squared*), but it *marks* the answer
3. **Diffusion operator** -- reflects all amplitudes around the mean. Since the marked answer pulled the mean down slightly, reflecting pushes the correct answer *up* and everything else *down*
4. **Repeat** -- each iteration amplifies the correct answer. After floor(pi*sqrt(N)/4) iterations, measuring gives the right answer with probability ~1

**Why sqrt(N)?** The amplitude of the correct answer after k iterations follows sin((2k+1) * arcsin(1/sqrt(N))). This peaks at k ~ pi*sqrt(N)/4.

**In the code:** `QiskitGroverEngine._build_grover_circuit()` in `qiskit_grover.py`. Oracle: `_apply_oracle()`. Diffusion: `_apply_diffusion()`.

| N | Classical comparisons | Grover oracle calls | Speedup |
|---|---|---|---|
| 100 | 100 | 8 | 12x |
| 1,000 | 1,000 | 25 | 40x |
| 1,000,000 | 1,000,000 | 785 | 1,274x |

**In one sentence:** Grover's uses quantum interference to amplify the correct answer's probability, needing only sqrt(N) iterations instead of N checks.

<details><summary>Self-test</summary>

**Q: What does the oracle do?**
A: Flips the phase (sign) of the correct answer's amplitude. Doesn't change its probability directly -- the diffusion step converts the phase difference into amplitude difference.

**Q: What happens if you run too many iterations?**
A: The amplitude overshoots and the probability of the correct answer starts *decreasing*. The optimal number is floor(pi*sqrt(N)/4).
</details>

---

## How Much qRAM Would We Need?

The most studied model (bucket-brigade qRAM) requires **O(N) quantum routing nodes** as hardware -- not O(log N). The log N is query *time*, not hardware *size*.

| Dataset size | qRAM nodes | IBM's largest machine |
|---|---|---|
| 1,000 vectors | ~1,000 | ~1,100 qubits (Condor) |
| 100,000 vectors | ~100,000 | -- |
| 1,000,000 vectors | ~1,000,000 | -- |

**With error correction** (~1,000 physical qubits per logical qubit): 1,000,000 vectors would need ~**1 billion physical qubits**.

**Why IBM's qubits don't help:** Those are processor qubits for gate circuits. qRAM is a completely different architecture -- a quantum memory array with tree routing. Having processor qubits doesn't get you qRAM, like having transistors doesn't get you RAM (RAM needs capacitors, decoders, sense amplifiers).

For our use case (512-dim float32 embeddings): each vector = 16,384 bits. The numbers don't improve with data width.

> The qRAM gap is not "we need a bigger chip." It's "we need a fundamentally different kind of hardware that nobody has built."

**In one sentence:** Practical qRAM for interesting dataset sizes is multiple orders of magnitude beyond current or near-term hardware.

<details><summary>Self-test</summary>

**Q: Why can't you just use IBM's qubits as qRAM?**
A: Different architecture entirely. Processor qubits run gate circuits. qRAM needs quantum memory with coherent tree routing.

**Q: How many physical qubits for qRAM at 1M vectors with error correction?**
A: ~1 billion. IBM Condor has ~1,100.
</details>

---

## Chunking: You Don't Need Full qRAM

You don't need qRAM for the entire dataset. Split N items into chunks of M, search each chunk with Grover, compare chunk-winners classically.

**Example:** 1,000,000 images, qRAM holds 1,000 at a time:
- 1,000 chunks x sqrt(1000) ~ 32 oracle calls each = **32,000 operations**
- Classical: **1,000,000 operations**
- **~31x speedup** with qRAM for only 1,000 items

### The general formula

| Quantity | Value |
|---|---|
| Chunks | N / M |
| Oracle calls per chunk | O(sqrt(M)) |
| Total | O(N / sqrt(M)) |
| Speedup over classical | **O(sqrt(M))** |

| qRAM capacity (M) | Speedup |
|---|---|
| 100 | ~10x |
| 1,000 | ~32x |
| 10,000 | ~100x |
| 1,000,000 (full) | ~1,000x |

### Why chunking still needs qRAM

Chunking reduces *how much* qRAM you need, not *whether* you need it:

| Scenario | Load per chunk | Search per chunk | Total |
|---|---|---|---|
| No qRAM | O(M) | O(sqrt(M)) | **O(N)** -- no speedup |
| qRAM for M items | O(log M) | O(sqrt(M)) | **O(N/sqrt(M))** -- partial speedup |
| qRAM for all N | O(log N) | O(sqrt(N)) | **O(sqrt(N))** -- full speedup |

**Why this matters:** Quantum search is not all-or-nothing. As qRAM scales from hundreds to thousands to millions, the speedup improves continuously. Our system is architecturally ready (pluggable backend) to benefit the moment *any* working qRAM exists.

**In one sentence:** Even small qRAM gives real speedups through chunking -- the advantage scales continuously with qRAM capacity.

<details><summary>Self-test</summary>

**Q: With qRAM for 10,000 items and a 1M dataset, what's the speedup?**
A: O(sqrt(10,000)) = ~100x over classical linear scan.

**Q: Why doesn't chunking help without qRAM?**
A: Loading each chunk still costs O(M) gates, so total = (N/M) * O(M) = O(N). The O(M) loading dominates.
</details>

---

## Simulator vs. IBM Hardware

**Primary: simulator. IBM: one small demonstration later.**

### Why simulator for the core benchmarks

- Oracle scaling benchmarks (O(sqrt(N)) at various N) need many dataset sizes and circuit depths
- IBM free tier: noisy beyond ~5-7 qubits, hours of queue time
- A dataset of 8 vectors on IBM gives the **same oracle count** as 8 on the simulator
- The simulator is noise-free, deterministic, and immediate

### Where IBM adds value

One tiny demonstration (4-8 vectors) on real hardware to show:
1. That our circuits run on real qubits
2. What quantum noise does to accuracy

Those are real findings, but they're a single experiment, not the core benchmark.

| Platform | Use |
|---|---|
| **Simulator** | All scaling benchmarks, all O(N) vs O(sqrt(N)) comparisons |
| **IBM hardware** | One noise/accuracy demonstration on a toy dataset |

---

## Why Wall-Clock Speed Is Not a KPI

Comparing wall-clock time between IBM (HTTP to data centre, queue waits, shot overhead) and local classical search (CPU, instant) is comparing different planets. The numbers are meaningless.

**Valid speed metric:** Oracle query count as a function of N. Hardware-independent, directly comparable. See [BENCHMARK_KPIS.md](BENCHMARK_KPIS.md).

---

## What This Project Delivers

We are **not** demonstrating a real end-to-end quantum speedup. That requires qRAM.

What we deliver:

1. **Classical infrastructure** -- production-quality vector search pipeline (CLIP embeddings, PostgreSQL + pgvector, FastAPI, React frontend) with pluggable quantum backend
2. **Working Grover oracle** -- verified on simulator, demonstrates O(sqrt(N)) oracle scaling (`qiskit_grover.py`)
3. **Working swap test** -- matches classical MRR with enough shots (`qiskit_swaptest.py`)
4. **Empirical scaling data** -- oracle calls plotted against N for classical and Grover
5. **Honest qRAM documentation** -- where the bottleneck is, what it takes to remove it, and what happens when it's gone

### The defensible claim

> Our Grover oracle scales as O(sqrt(N)) on a simulator, the swap test produces accurate results, and the system is architecturally ready for a qRAM-capable backend when that hardware exists.

---

## Implementation Decisions

### Don't implement IBM engine yet

Simulator covers everything for current phase. IBM adds queue delays and noise overhead for a toy demo that proves nothing the simulator doesn't. Add later as a separate noise/accuracy experiment.

### Speed KPI: oracle count, not wall-clock

- Wall-clock: not valid (incomparable environments, O(N) end-to-end without qRAM)
- Oracle count: valid (hardware-independent, captures O(N) vs O(sqrt(N)) difference)
- Run at N = 100, 500, 1000, 2000, count operations, plot both curves

### Implementation phases

**Phase 1 (now):** `qiskit_grover.py` on AerSimulator, `oracle_calls` column, operation count scaling in reports

**Phase 2 (later):** IBM backend via constructor injection (no engine code changes), record circuit execution time from job metadata only
