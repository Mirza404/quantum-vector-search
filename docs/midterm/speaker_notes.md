# Midterm Presentation - Speaker Notes

## Slide 1 - Title (~15 seconds)

"This project benchmarks classical and quantum vector search engines on identical data.
The system is a text-to-image search application - the user selects a query, the backend
runs multiple search algorithms, and we compare them objectively."

---

## Slide 2 - Context and Motivation (~45 seconds)

Vector search is the backbone of modern ML. Recommendation systems, image retrieval,
semantic document search - all of it works by encoding items as vectors and finding
the nearest ones to a query.

CLIP [6] is what enables text-to-image search. It aligns a text encoder and an image encoder
so that a description and the matching image land near each other in a shared 512-dimensional
space. Nearest-neighbour lookup does the rest.

The quantum angle: Grover's algorithm has a proven quadratic speedup for exact unstructured search [1].
We run it on a real simulator against real embeddings
and measure what it actually costs.

---

## Slide 3 - Problem Definition (~40 seconds)

Walk through the three research questions briefly. The third is the most interesting:
even if qRAM existed and state prep were free, would quantum search beat classical?
We address that on slide 11.

On IBM hardware: free tier has reported  queue waits and significant noise
beyond about 7 qubits. That makes controlled scaling experiments uninterpretable.
AerSimulator is mathematically exact - shot noise is identical to real hardware,
so our MRR results transfer directly.

---

## Slide 4 - Theoretical Background (~45 seconds)

Three building blocks, one sentence each.

CLIP [6]: contrastive pre-training aligns text and image encoders. Result: cosine similarity
between a text vector and an image vector measures semantic match.

Vector search: brute force and FAISS are O(N) exact. HNSW is O(log N) approximate - the
production standard. It becomes critical on slide 11.

Quantum: the swap test estimates vector overlap via a quantum circuit [3].
Grover amplifies the correct answer in O(sqrt(N)) oracle calls [1][2].
That O(sqrt(N)) is oracle calls only - state preparation is
a separate cost.

---

## Slide 5 - System Architecture (~25 seconds)

Walk through the pipeline left to right. The key point is the strategy pattern:
every engine implements the same two-method interface. The harness does not know or care
which engine it is running. Same data, same query, same evaluation. That is what makes
the comparison fair.

If asked about pgvector and HNSW: pgvector (our storage layer) uses HNSW internally
as a database index to speed up vector lookups from PostgreSQL. This is unrelated to
the HNSW benchmarking engine. One is a storage optimization;
the other is a search algorithm we benchmark directly.

---

## Slide 6 - Search Engines (~45 seconds)

Walk across the five cards left to right.

Brute force: simplest possible - dot product against every vector, no index. Its only role
is ground truth; every other engine's MRR is computed against this output.

FAISS: Meta's production library, SIMD-vectorised. On normalised vectors L2 and cosine
give identical rankings - results match brute force exactly, just faster.

Swap test: one ancilla qubit controls a swap between two vector registers. Measurement
probability encodes vector overlap [3]. You repeat many times (shots) and average.
Still O(N) circuits - a similarity measurement, not a speedup.

Grover oracle: different. All N candidates in superposition. Oracle marks the target,
diffusion amplifies it. Repeat floor(pi*sqrt(N)/4) times. 1,000 vectors needs 24 oracle
calls instead of 1,000. We verify this empirically - our circuit reproduces the curve.

One thing to be explicit about: the oracle in this simulation is classically pre-specified.
For a real quantum search, the oracle circuit would need to compute which vector is closest
entirely inside the quantum system - loading all N vectors into superposition, evaluating
distances, marking the minimum. That requires qRAM. Since qRAM doesn't exist, we identify
the nearest neighbour classically first, then build an oracle that marks that specific index.
The amplitude amplification and the sqrt(N) scaling are fully real and verified. What we're
measuring is the scaling property of the algorithm, not a search that replaces the classical step.

HNSW: multi-layer proximity graph. O(log N), 95-99%+ recall. Implemented as
`faiss_hnsw_l2` using FAISS `IndexHNSWFlat`. This is the most important comparison
point - see slide 11 for why.

Point to the complexity callout: the progression brute force O(N) → Grover O(√N) → HNSW O(log N)
is the central story of the project.

---

## Slide 7 - Completed Work (~40 seconds)

Phases 1 through 4 are done. End-to-end pipeline running.

On circuit verification: not just "it runs" - we verified correctness.
Swap test overlap matches the analytical formula. Grover oracle count follows floor(pi*sqrt(N)/4).

Point to the integration results table. 20-image test only - not final.
Grover used 3 oracle calls where classical needed 20. That ratio is exactly O(sqrt(N)) at N=20.
That is the relationship we will measure systematically at scale.

---

## Slide 8 - In Progress and TODO (~35 seconds)

Two open areas.

Frontend: React app scaffolded and connecting to the API. Main remaining work is the
comparison view - user selects from predefined ground-truth queries, results render
in a dynamic grid with MRR and oracle call count per engine.

Full benchmark matrix is the primary remaining technical milestone.
The harness is built, but we have not yet run it across the full configuration space:
multiple N values, dimensions 64 through 512, multiple shot budgets.
All quantitative conclusions are pending that run.

---

## Slide 9 - Timeline (~15 seconds)

Green is done, amber is now, open circles are upcoming.
Core engineering is complete. Remaining work is running the experiments,
analysing the output, and writing the thesis. Brief and move on.

---

## Slide 10 - KPIs (~25 seconds)

MRR: measures quality. Directly comparable across all engines - same normalised vectors,
same ground truth. MRR 1.0 means always first. MRR 0.5 means typically second.

Oracle call count: the cross-engine speed metric. Hardware-independent.
Captures the algorithmic difference between O(N) and O(sqrt(N)).
Wall-clock time is not a valid comparison - simulator overhead reflects classical CPU cost,
not the quantum algorithm's complexity.

---

## Slide 11 - The Honest Quantum Picture (~55 seconds)

Most important slide. Take your time.

The two-step problem: quantum search is two operations. Loading data into superposition is O(N)
without qRAM [4] - same as classical. The speedup is cancelled. Grover's O(sqrt(N)) search
still works - we verify it - but the total is O(N) without hardware that does not exist.

Point to the qRAM table. Key framing: qubit = processor, qRAM = storage. IBM's processor
(the qubit chip) exists and runs Grover's circuit - that needs only ~20 qubits regardless
of dataset size. qRAM is the storage layer that would hold the dataset and feed it to the
processor - that does not exist. They are completely different hardware, like a CPU vs a
hard drive.

The table shows this split directly. Algorithm qubits: Grover needs log₂(N) qubits - just
enough to represent a number up to N. At 1,000 vectors that's ~10 qubits; at 1,000,000 it's
~20. Tiny. The qRAM storage is the opposite: 1,000 vectors needs ~1,000,000 physical qubits;
1,000,000 vectors needs ~1,000,000,000.
The multiplier is ~1,000 physical qubits per memory slot: qubits are fragile, so reliable
storage wraps each slot in error correction circuitry. qRAM needs one slot per vector, so the
cost is N × 1,000 qubits. Classical RAM for the same data is 2 MB vs 2 GB - linear in both
cases, but classical RAM is already cheap. This is not a timeline problem - the hardware
architecture does not exist on any roadmap.

The bigger finding - point to the complexity table.
Even with ideal qRAM, HNSW is O(log N) [5], Grover is O(sqrt(N)) [1].
Log N grows slower than sqrt(N). At N = 1,000,000: HNSW needs ~20 ops, Grover needs ~785.
HNSW wins by 40x, on a laptop, today.

Point to the quote callout at the bottom - Hoefler et al. (2023) [10]. Vector search is the wrong
shape for quantum: each comparison is a trivial dot product, the hard part is the data volume, and
loading all of it into superposition is exactly the qRAM problem already covered above. Quantum wins
on small data with enormous computation - molecule simulation, cryptography - not dataset scans.

---

## Slide 12 - Expected Outcomes (~25 seconds)

Walk through the hypotheses briefly - these are predictions, not results.

The contribution: empirical verification of theoretical predictions, a complete fair
benchmarking infrastructure, and an honest documented analysis of where the quantum-classical
gap lies. Read out the defensible claim callout.

---

## Slide 13 - Conclusion (~20 seconds)

"Quantum vector search is not useful in practice today. State preparation requires hardware
that does not exist, and even ideal qRAM would not make Grover competitive with HNSW.
The point of this project is not to prove quantum is better - it is to empirically measure
exactly why it is not, and under what conditions it could be. Rigorous negative results
supported by real circuits and real data are a valid contribution."

---

## Q&A Cheat Sheet

**"So quantum is useless for search?"**

Grover's speedup [1] is real and proven - one of the few unconditional quantum speedups not
overturned by classical improvements [7]. But for this specific problem: in practice it cannot
compete. Without qRAM [4] the total complexity is O(N). With hypothetical qRAM, HNSW [5] beats
it at O(log N). The niche where Grover would win barely exists in real ML applications.

---

**"What is your actual contribution if the conclusion is negative?"**

We implemented Grover [1] and the swap test [3] on a real circuit simulator and empirically
verified they behave as theory predicts. Oracle calls follow floor(pi*sqrt(N)/4) across dataset
sizes. We built infrastructure to measure this fairly. We also built a working text-to-image
search system around it. Negative results that are well-supported are scientifically valid.

---

**"Why not use real IBM quantum hardware?"**

IBM free tier reportedly has reported long queue waits and significant gate noise beyond ~7 qubits.
That makes controlled scaling experiments impossible to interpret cleanly.
AerSimulator is mathematically exact. Shot noise is identical on simulator and real hardware,
so MRR results transfer directly. IBM hardware would be a noise-accuracy study - out of scope.

---

**"Why is the Grover engine slow in wall-clock timings?"**

Simulation overhead on a CPU - the simulator tracks 2^n amplitudes using classical memory.
A real quantum chip processes all amplitudes in parallel by physical law.
Quantum engine wall-clock time on a simulator is not meaningful, which is why oracle call count
is the cross-engine comparison metric.

---

**"Why use predefined queries instead of free-text input?"**

With arbitrary free-text input there is no ground truth - we can show two ranked lists side by
side but cannot compute MRR. No objective way to say which engine did better. Predefined queries
with known ground-truth image matches [8] are what make quantitative comparison possible.

---

**"Should you have implemented HNSW for comparison?"**

Fair point. HNSW [5] is the most relevant classical benchmark because it shows O(log N) already
exists classically. It is documented as the next extension and the architecture is ready for it.
Including it would make the comparison against Grover cleaner. It is a natural next step.
