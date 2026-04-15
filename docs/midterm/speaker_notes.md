# Midterm Presentation -- Speaker Notes

Full talking points per slide, transitions, and Q&A cheat sheet.
Target: 8-10 minutes total speaking time. Approximate time per slide is noted.
Sources slide (18) does not count toward the time limit.

Inline citation numbers like [1] match the numbered sources on the final slide.
You do not need to say these aloud -- they are there so you know which claim
has backing if a committee member challenges it.

## Reference Key (quick lookup during Q&A)

| # | Source | What it backs |
|---|--------|---------------|
| [1] | Grover (1996), DOI:10.1145/237814.237866 | O(sqrt(N)) oracle count |
| [2] | Bennett et al. (1997), arxiv.org/abs/quant-ph/9701001 | O(sqrt(N)) is provably optimal |
| [3] | Buhrman et al. (2001), DOI:10.1103/PhysRevLett.87.167902 | Swap test circuit formula |
| [4] | Giovannetti, Lloyd, Maccone (2008), DOI:10.1103/PhysRevLett.100.160501 | qRAM hardware requirements |
| [5] | Malkov & Yashunin (2020), arXiv:1603.09320 | HNSW O(log N); ~20 ops at N=1M |
| [6] | Radford et al. (2021), arXiv:2103.00020 | CLIP ViT-B/32 embedding space |
| [7] | Tang (2019), arXiv:1807.04271 | Grover's speedup not dequantized |
| [8] | Young et al. (2014), DOI:10.1162/tacl_a_00166 | Flickr30k dataset |
| [9] | IBM Newsroom (Dec 4, 2023) | IBM Condor ~1,100 qubits |

---

## Slide 1 -- Title (~15 seconds)

"This project benchmarks classical and quantum vector search engines on identical data.
The system is a text-to-image search application -- the user selects a query, the backend
runs multiple search algorithms, and we compare them objectively."

---

## Slide 2 -- Context and Motivation (~45 seconds)

Vector search is the backbone of modern ML. Recommendation systems, image retrieval,
semantic document search -- all of it works by encoding items as vectors and finding
the nearest ones to a query.

CLIP [6] is what enables text-to-image search. It aligns a text encoder and an image encoder
so that a description and the matching image land near each other in a shared 512-dimensional
space. Nearest-neighbour lookup does the rest.

The quantum angle: Grover's algorithm has a proven quadratic speedup for unstructured search [1].
Most of the literature is theoretical. We run it on a real simulator against real embeddings
and measure what it actually costs.

---

## Slide 3 -- Problem Definition (~40 seconds)

Walk through the three research questions briefly. The third is the most interesting:
even if qRAM existed and state prep were free, would quantum search beat classical?
We address that on slide 15.

On IBM hardware: free tier has reported multi-hour queue waits and significant noise
beyond about 7 qubits. That makes controlled scaling experiments uninterpretable.
AerSimulator is mathematically exact -- shot noise is identical to real hardware,
so our MRR results transfer directly.

---

## Slide 4 -- Theoretical Background (~45 seconds)

Three building blocks, one sentence each.

CLIP [6]: contrastive pre-training aligns text and image encoders. Result: cosine similarity
between a text vector and an image vector measures semantic match.

Vector search: brute force and FAISS are O(N) exact. HNSW is O(log N) approximate -- the
production standard. It becomes critical on slide 15. Each engine has a dedicated slide.

Quantum: the swap test estimates vector overlap via a quantum circuit [3].
Grover amplifies the correct answer in O(sqrt(N)) oracle calls [1][2].
Point to the amber box: that O(sqrt(N)) is oracle calls only -- state preparation is
a separate cost. See slide 15.

---

## Slide 5 -- System Architecture (~25 seconds)

Walk through the pipeline left to right. The key point is the strategy pattern:
every engine implements the same two-method interface. The harness does not know or care
which engine it is running. Same data, same query, same evaluation. That is what makes
the comparison fair. The next five slides walk through each engine in detail.

---

## Slide 6 -- Engine 1: Brute Force Cosine (~20 seconds)

Point to the diagram. "Simplest possible engine -- dot product against every vector.
No index, no approximation. Its only role is ground truth: every other engine's MRR
is computed against this output."

---

## Slide 7 -- Engine 2: FAISS Flat L2 (~20 seconds)

"FAISS is the production library from Meta. SIMD-vectorised L2 distance.
The unit circle diagram shows why L2 and cosine give identical rankings on normalised vectors:
smaller chord equals smaller angle equals higher cosine. Results match brute force exactly,
just faster."

---

## Slide 8 -- Engine 3: Qiskit Swap Test (~35 seconds)

Point to the circuit diagram. "One ancilla qubit controls a swap between the two vector
registers. The measurement probability encodes the vector overlap -- that formula at the bottom
is the exact relationship [3]. You repeat the circuit many times (shots) and average.
It is a quantum similarity measurement, not a speedup -- still O(N) circuits, one per candidate.
What it tells us is how accurately a real quantum circuit can estimate vector similarity,
and how many shots you need for acceptable MRR."

---

## Slide 9 -- Engine 4: Qiskit Grover Oracle (~35 seconds)

Point to the circuit diagram. "This is different. All N candidates go into superposition.
The oracle marks the target with a phase flip. The diffusion operator amplifies it.
Repeat floor(pi * sqrt(N) / 4) times. The table shows what that means:
1,000 vectors needs 24 oracle calls instead of 1,000.
We verify this empirically -- our circuit reproduces the theoretical scaling curve."

---

## Slide 10 -- Future Extension: HNSW (~25 seconds)

Point to the graph. "Three layers -- sparse at the top for fast navigation, dense at
the bottom for precision. The query enters at the top and greedily descends. O(log N) total.
It is not in the benchmark yet, but the architecture is ready for it.
And as we will see in two slides, it is the most important comparison point."

---

## Slide 11 -- Completed Work (~40 seconds)

Phases 1 through 4 are done. End-to-end pipeline running.

On circuit verification: not just "it runs" -- we verified correctness.
Swap test overlap matches the analytical formula. Grover oracle count follows floor(pi*sqrt(N)/4).

Point to the integration results table. 20-image test only -- not final.
Grover used 3 oracle calls where classical needed 20. That ratio is exactly O(sqrt(N)) at N=20.
That is the relationship we will measure systematically at scale.

---

## Slide 12 -- In Progress and TODO (~35 seconds)

Two open areas.

Frontend: React app scaffolded and connecting to the API. Main remaining work is the
comparison view -- user selects from predefined ground-truth queries, results render
in a dynamic grid with MRR and oracle call count per engine.

Full benchmark matrix is the primary remaining technical milestone.
The harness is built, but we have not yet run it across the full configuration space:
multiple N values, dimensions 64 through 512, multiple shot budgets.
All quantitative conclusions are pending that run.

---

## Slide 13 -- Timeline (~15 seconds)

Green is done, amber is now, open circles are upcoming.
Core engineering is complete. Remaining work is running the experiments,
analysing the output, and writing the thesis. Brief and move on.

---

## Slide 14 -- KPIs (~25 seconds)

MRR: measures quality. Directly comparable across all engines -- same normalised vectors,
same ground truth. MRR 1.0 means always first. MRR 0.5 means typically second.

Oracle call count: the cross-engine speed metric. Hardware-independent.
Captures the algorithmic difference between O(N) and O(sqrt(N)).
Wall-clock time is not a valid comparison -- simulator overhead reflects classical CPU cost,
not the quantum algorithm's complexity.

---

## Slide 15 -- The Honest Quantum Picture (~55 seconds)

Most important slide. Take your time.

The two-step problem: quantum search is two operations. Loading data into superposition is O(N)
without qRAM [4] -- same as classical. The speedup is cancelled. Grover's O(sqrt(N)) search
still works -- we verify it -- but the total is O(N) without hardware that does not exist.

Point to the qRAM table. The bucket-brigade model needs O(N) quantum routing nodes [4].
With error correction, ~1,000 physical qubits per logical qubit.
For 1,000 vectors: ~1,000,000 physical qubits. IBM Condor has ~1,100 [9].
This is not a timeline problem. The hardware architecture does not exist.

The bigger finding -- point to the complexity table.
Even with ideal qRAM, HNSW is O(log N) [5], Grover is O(sqrt(N)) [1].
Log N grows slower than sqrt(N). At N = 1,000,000: HNSW needs ~20 ops, Grover needs ~785.
HNSW wins by 40x, on a laptop, today.

---

## Slide 16 -- Expected Outcomes (~25 seconds)

Walk through the hypotheses briefly -- these are predictions, not results.

The contribution: empirical verification of theoretical predictions, a complete fair
benchmarking infrastructure, and an honest documented analysis of where the quantum-classical
gap lies. Read out the defensible claim callout.

---

## Slide 17 -- Conclusion (~20 seconds)

"Quantum vector search is not useful in practice today. State preparation requires hardware
that does not exist, and even ideal qRAM would not make Grover competitive with HNSW.
The point of this project is not to prove quantum is better -- it is to empirically measure
exactly why it is not, and under what conditions it could be. Rigorous negative results
supported by real circuits and real data are a valid contribution."

---

## Q&A Cheat Sheet

**"So quantum is useless for search?"**

Grover's speedup [1] is real and proven -- one of the few unconditional quantum speedups not
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

IBM free tier has reported multi-hour queue waits and significant gate noise beyond ~7 qubits.
That makes controlled scaling experiments impossible to interpret cleanly.
AerSimulator is mathematically exact. Shot noise is identical on simulator and real hardware,
so MRR results transfer directly. IBM hardware would be a noise-accuracy study -- out of scope.

---

**"Why is the Grover engine slow in wall-clock timings?"**

Simulation overhead on a CPU -- the simulator tracks 2^n amplitudes using classical memory.
A real quantum chip processes all amplitudes in parallel by physical law.
Quantum engine wall-clock time on a simulator is not meaningful, which is why oracle call count
is the cross-engine comparison metric.

---

**"Why use predefined queries instead of free-text input?"**

With arbitrary free-text input there is no ground truth -- we can show two ranked lists side by
side but cannot compute MRR. No objective way to say which engine did better. Predefined queries
with known ground-truth image matches [8] are what make quantitative comparison possible.

---

**"Should you have implemented HNSW for comparison?"**

Fair point. HNSW [5] is the most relevant classical benchmark because it shows O(log N) already
exists classically. It is documented as the next extension and the architecture is ready for it.
Including it would make the comparison against Grover cleaner. It is a natural next step.

---

## Timing Guide

| Slide | Content | Target time |
|-------|---------|-------------|
| 1 | Title | 0:15 |
| 2 | Context | 0:45 |
| 3 | Problem | 0:40 |
| 4 | Theory | 0:45 |
| 5 | Architecture | 0:25 |
| 6 | Brute Force | 0:20 |
| 7 | FAISS | 0:20 |
| 8 | Swap Test | 0:35 |
| 9 | Grover | 0:35 |
| 10 | HNSW | 0:25 |
| 11 | Completed | 0:40 |
| 12 | In Progress | 0:35 |
| 13 | Timeline | 0:15 |
| 14 | KPIs | 0:25 |
| 15 | Honest Quantum | 0:55 |
| 16 | Expected Outcomes | 0:25 |
| 17 | Conclusion | 0:20 |
| **Total** | | **~8:40** |

If running long: cut slides 13 (timeline, 10 sec) and 14 (KPIs, 15 sec) -- they are supporting.
Engine slides 6-10 can be trimmed to 15 sec each if needed -- the diagrams carry the content.
Do not cut slides 15 or 17 -- that is where the project's argument lives.
