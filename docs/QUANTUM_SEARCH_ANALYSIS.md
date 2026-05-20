# Quantum Vector Search Analysis

Why quantum vector search can't deliver a real speedup today, what our benchmarks actually measure, and why this project still has value. This is the authoritative reference for the thesis defence on the qRAM problem, benchmarking strategy, and scaling theory.

For algorithm basics: [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md). For KPI definitions: [BENCHMARK_KPIS.md](BENCHMARK_KPIS.md).

---

## The Two-Step Problem

Quantum vector search is two separate steps, and confusing them causes all the misunderstanding.

### Step 1: Loading data into superposition (broken)

To get any quantum speedup, all N database vectors need to be in quantum superposition simultaneously. This requires **qRAM** (Quantum Random Access Memory) - hardware that can load N classical data items into superposition in O(log N) time.

**qRAM does not exist.** Not on IBM's machines, not anywhere.

Without qRAM, loading vectors requires O(N) gate operations - the same as classical linear scan. The speedup is erased before search even starts.

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

**Self-test**

**Q: What are the two steps?**
A: (1) Loading data into superposition (needs qRAM, O(N) without it), (2) Searching (O(sqrt(N)) with Grover's).

**Q: Why doesn't the O(sqrt(N)) search help without qRAM?**
A: The O(N) loading cost dominates. O(N) + O(sqrt(N)) = O(N).


---

## How Grover's Algorithm Gets O(sqrt(N))

Classical search checks items one at a time. Grover's exploits **amplitude amplification**:

1. **Start in uniform superposition** - all N items have equal amplitude 1/sqrt(N)
2. **Oracle** - flips the phase of the correct answer from +1/sqrt(N) to -1/sqrt(N). Invisible to measurement (probability is amplitude *squared*), but it *marks* the answer
3. **Diffusion operator** - reflects all amplitudes around the mean. Since the marked answer pulled the mean down slightly, reflecting pushes the correct answer *up* and everything else *down*
4. **Repeat** - each iteration amplifies the correct answer. After floor(pi*sqrt(N)/4) iterations, measuring gives the right answer with probability ~1

**Why sqrt(N)?** The amplitude of the correct answer after k iterations follows sin((2k+1) * arcsin(1/sqrt(N))). This peaks at k ~ pi*sqrt(N)/4.

**In the code:** `QiskitGroverEngine._build_grover_circuit()` in `qiskit_grover.py`. Oracle: `_apply_oracle()`. Diffusion: `_apply_diffusion()`.

| N | Brute-force comparisons (O(N)) | Grover oracle calls (O(√N)) | Speedup vs brute force |
|---|---|---|---|
| 100 | 100 | 8 | 12x |
| 1,000 | 1,000 | 25 | 40x |
| 1,000,000 | 1,000,000 | 785 | 1,274x |

> Note: this compares Grover against brute-force exact search only. HNSW achieves O(log N) approximate search (~20 ops at N=1M) - faster than Grover even with ideal qRAM.

**In one sentence:** Grover's uses quantum interference to amplify the correct answer's probability, needing only sqrt(N) iterations instead of N checks - a speedup over brute force, but not over HNSW.

**Self-test**

**Q: What does the oracle do?**
A: Flips the phase (sign) of the correct answer's amplitude. Doesn't change its probability directly - the diffusion step converts the phase difference into amplitude difference.

**Q: What happens if you run too many iterations?**
A: The amplitude overshoots and the probability of the correct answer starts *decreasing*. The optimal number is floor(pi*sqrt(N)/4).


---

## How Much qRAM Would We Need?

The most studied model (bucket-brigade qRAM) requires **O(N) quantum routing nodes** as hardware - not O(log N). The log N is query *time*, not hardware *size*.

**Important:** qRAM is memory hardware, not a quantum processor. IBM's processors run circuits. qRAM would store data. They are completely different devices - like CPU vs RAM in a laptop. IBM having ~1,100 processor qubits says nothing about qRAM; qRAM doesn't exist at any scale.

| Dataset size | Classical RAM needed | qRAM nodes needed | With error correction |
|---|---|---|---|
| 1,000 vectors | ~2 MB | ~1,000 | ~1,000,000 physical qubits |
| 100,000 vectors | ~200 MB | ~100,000 | ~100,000,000 physical qubits |
| 1,000,000 vectors | ~2 GB | ~1,000,000 | ~1,000,000,000 physical qubits |

Both scale linearly with dataset size. Classical RAM is already cheap. qRAM hardware does not exist.

For our use case (512-dim float32 embeddings): each vector = 16,384 bits. The numbers don't improve with data width.

> The qRAM gap is not "we need a bigger chip." It's "we need a fundamentally different kind of hardware that nobody has built."

**In one sentence:** Practical qRAM for interesting dataset sizes is multiple orders of magnitude beyond current or near-term hardware.

**Self-test**

**Q: Why can't you just use IBM's qubits as qRAM?**
A: Different architecture entirely. Processor qubits run gate circuits. qRAM needs quantum memory with coherent tree routing.

**Q: How many physical qubits for qRAM at 1M vectors with error correction?**
A: ~1 billion qRAM routing nodes. IBM Condor has ~1,100 processor qubits - but those are gate-circuit qubits, not qRAM. They're a completely different hardware category. IBM having 1,100 processor qubits says nothing about qRAM capacity; it's like saying "we have transistors, so we're close to RAM." qRAM doesn't exist at any scale.


---

## Would Future qRAM Actually Make This Viable?

Theoretically yes. With working qRAM: O(log N) data loading + O(sqrt(N)) search = O(sqrt(N)) total. A real quadratic speedup over classical brute force.

Practically: not a near-term or medium-term prospect, and the requirements are not just "expensive" - the hardware category does not exist.

**The hardware requirement:** The most studied qRAM model (bucket-brigade) needs O(N) quantum routing nodes as physical hardware. The O(log N) figure is query *time*, not hardware *size*. With error correction (~1,000 physical qubits per logical qubit):

| Dataset size | Physical qubits for qRAM |
|---|---|
| 1,000 vectors | ~1,000,000 |
| 1,000,000 vectors | ~1,000,000,000 |

IBM's aggressive roadmap targets ~100,000 processor qubits by ~2033. Those are gate-circuit qubits - a completely different architecture from qRAM, which needs quantum memory with coherent tree routing. No lab has demonstrated working qRAM at any meaningful scale. This is not "we need a bigger chip." It is a hardware category that does not exist yet and has no clear path to existence.

**Honest assessment:** The O(sqrt(N)) future is theoretically real. Practically, it is blocked by hardware requirements so extreme that it does not appear on any credible roadmap.

**But even in that hypothetical future, classical still wins.** Grover with ideal qRAM gives O(sqrt(N)) *exact* search. HNSW gives O(log N) *approximate* search - and since log N grows far slower than sqrt(N), HNSW is faster at any interesting dataset size. At N=1M: HNSW ~20 ops, Grover ~785 oracle calls. HNSW wins by ~40x, on a laptop, today, with no exotic hardware. The only domain where Grover would win is *exact* nearest-neighbor search - and in practice, HNSW's 95-99% recall is indistinguishable from exact for virtually every real application. So qRAM would not make quantum vector search the best option; it would just make it viable rather than hopeless.

---

## Grover vs. Parallelised Classical and HNSW

### Parallelism: N cores = O(1)

If you have K parallel cores doing K comparisons simultaneously, wall-clock time is O(N/K). At K = N that is O(1). This is technically correct. The proper hardware-aware comparison is:

- Classical with K cores: O(N/K) time, requires O(K) hardware
- Grover with qRAM: O(sqrt(N)) time, requires O(log N) qubits

Grover uses far less *hardware* to achieve sqrt(N) time. That is the real argument - not just fewer operations, but fewer operations with logarithmically fewer hardware units.

**But:** qRAM itself requires O(N) hardware nodes. So the hardware efficiency argument collapses. You need O(N) qRAM hardware to run Grover, which means classical with O(N) cores would achieve O(1). Classical wins on both counts once qRAM hardware cost is included.

### HNSW: the classical algorithm that changes the comparison

HNSW (Hierarchical Navigable Small World) is the standard production vector search algorithm. It builds a multi-layer graph over your vectors. A query navigates the graph - sparse top layers to find the approximate region, denser bottom layers to narrow in. Query time: **O(log N)**. It is approximate (might not always return the exact nearest neighbor), but recall is 95-99%+ in practice. This is what runs behind every production recommendation system at scale.

**Why this matters:**

Grover with ideal qRAM is O(sqrt(N)). HNSW is O(log N). Since log N grows much slower than sqrt(N), HNSW is faster than Grover even in the ideal qRAM future.

For N = 1,000,000:
- HNSW: ~20 effective operations
- Grover with ideal qRAM: ~785 oracle calls

HNSW wins by ~40x. On a laptop. Today.

**Where Grover still wins:** HNSW is approximate. For *exact* nearest neighbor search, no classical sub-linear algorithm exists. Grover with qRAM would be the only known sub-linear exact search method. But in practice, approximate is fine for almost every ML application - the exact nearest neighbor and the approximate nearest neighbor are effectively the same result for a user.

**Summary:**

| Method | Complexity | Exact? | Requires |
|---|---|---|---|
| Brute force | O(N) | Yes | Nothing |
| HNSW | O(log N) | Approximate | Nothing |
| Grover | O(sqrt(N)) | Yes | qRAM (doesn't exist) |

Grover's niche is exact search at large N. That niche barely exists in practice.

---

## Is Quantum Vector Search Actually Promising?

Honest answer: it is a theoretically clean example of quantum speedup, not an active research frontier.

Grover's algorithm is famous because it is one of the only quantum algorithms with a **proven, unconditional speedup** that has not been undone. Many quantum ML algorithms that claimed exponential speedups were "dequantized" - classical algorithms were found that achieve similar performance given the right data access structure (Ewin Tang, 2018). Grover's quadratic speedup is real and provably optimal for quantum unstructured search. It has not been dequantized.

But for vector search specifically:
- The speedup requires qRAM, which does not exist
- Even with qRAM, HNSW beats Grover for the practical use case (approximate search)
- The only scenario where Grover wins is exact search at very large N, which is rarely needed

Where quantum computing research energy actually goes: quantum chemistry (simulating molecules - exponential speedup, no qRAM needed), Shor's algorithm (breaking RSA - already influencing post-quantum cryptography standards), quantum optimisation (unclear advantage, actively studied). Quantum vector search appears in textbooks as an application of Grover's because it is pedagogically clean, not because it is a research priority.

**In one sentence:** Quantum vector search is interesting because Grover's proven speedup is rare and mathematically elegant, not because it is practically promising.

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

### Why IBM runs the hybrid swap-test engine, not Grover

The real-hardware IBM path uses `hybrid_hnsw_swap_test_ibm`: classical HNSW first
selects a small candidate set, then IBM hardware runs swap-test circuits to rerank
those candidates.

We intentionally do **not** run `qiskit_grover` on IBM hardware for the main demo:

- Grover in this project isolates oracle scaling, but its oracle target is selected
  classically first. That is useful for theory, but less convincing as a real-hardware
  retrieval demo.
- Grover circuits become deeper because each iteration applies an oracle plus diffusion.
  On noisy free-tier hardware, depth hurts reliability quickly.
- A full Grover benchmark would consume limited QPU quota and queue time without adding
  much beyond what the simulator already proves: the O(sqrt(N)) oracle count.
- The hybrid swap-test circuit is smaller and directly validates a useful quantum
  subroutine: quantum similarity estimation after classical candidate retrieval.

So the simulator remains the source of the full benchmark data, while IBM hardware is
used as a controlled validation that the quantum reranking component can execute on a
real QPU.

### IBM validation result

We ran one explicit IBM hardware validation, separate from the normal benchmark suite:

| Setting | Value |
|---|---|
| Engine | `hybrid_hnsw_swap_test_ibm` |
| Queries | 20 |
| Vector dimension | 2 |
| Candidate pool | 2 |
| Shots | 32 |
| QPU quota used | 80 seconds |
| Open Plan quota after run | 516 / 600 seconds remaining |
| Average MRR | 0.125 |
| Hit rate | 15% |

This is intentionally a **validation experiment**, not a full benchmark. We reduced
dimension, candidate count, and shots to avoid burning the free IBM Open Plan quota.
The result proves the real-hardware path works and gives a small noise-affected data
point, but it should not be compared directly against simulator/classical runs that use
higher dimensions and more complete candidate rankings.

---

## Why Wall-Clock Speed Is Not a KPI

Comparing wall-clock time between IBM (HTTP to data centre, queue waits, shot overhead) and local classical search (CPU, instant) is comparing different planets. The numbers are meaningless.

**Valid speed metric:** Oracle query count as a function of N. Hardware-independent, directly comparable. See [BENCHMARK_KPIS.md](BENCHMARK_KPIS.md).

---

## What This Project Delivers

We are **not** demonstrating a real end-to-end quantum speedup. That requires qRAM.

What we deliver:

1. **Classical infrastructure** - production-quality vector search pipeline (CLIP embeddings, PostgreSQL + pgvector, FastAPI, React frontend) with pluggable quantum backend
2. **Working Grover oracle** - verified on simulator, demonstrates O(sqrt(N)) oracle scaling (`qiskit_grover.py`)
3. **Working swap test** - matches classical MRR with enough shots (`qiskit_swaptest.py`)
4. **Empirical scaling data** - oracle calls plotted against N for classical and Grover
5. **Honest qRAM documentation** - where the bottleneck is, what it takes to remove it, and what happens when it's gone

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
