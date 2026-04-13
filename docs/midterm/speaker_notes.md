# Midterm Presentation -- Speaker Notes

Full talking points per slide, transitions, opening script, closing script, and Q&A cheat sheet.
Target: 7-8 minutes total speaking time. Approximate time per slide is noted.

Inline citation numbers like [1] match the numbered sources on the final slide.
You do not need to say these numbers aloud -- they are there so you know which claim
has backing if a committee member challenges it.

## Reference Key (quick lookup during Q&A)

| # | Source | What it backs |
|---|--------|---------------|
| [1] | Grover (1996), DOI:10.1145/237814.237866 | O(sqrt(N)) oracle count |
| [2] | Bennett et al. (1997), arxiv.org/abs/quant-ph/9701001 | O(sqrt(N)) is provably optimal lower bound |
| [3] | Buhrman et al. (2001), DOI:10.1103/PhysRevLett.87.167902 | Swap test circuit formula |
| [4] | Giovannetti, Lloyd, Maccone (2008), DOI:10.1103/PhysRevLett.100.160501 | qRAM requires O(N) hardware nodes; physical qubit estimates |
| [5] | Malkov & Yashunin (2020), arXiv:1603.09320 | HNSW O(log N); 95-99% recall; ~20 ops at N=1M |
| [6] | Radford et al. (2021), arXiv:2103.00020 | CLIP ViT-B/32 shared embedding space |
| [7] | Tang (2019), arXiv:1807.04271 | Dequantization context -- Grover's speedup not overturned |
| [8] | Young et al. (2014), DOI:10.1162/tacl_a_00166 | Flickr30k dataset |
| [9] | IBM Newsroom (Dec 4, 2023), newsroom.ibm.com/2023-12-04-IBM-Debuts-Next-Generation-Quantum-Processor-IBM-Quantum-System-Two,-Extends-Roadmap-to-Advance-Era-of-Quantum-Utility | IBM Condor ~1,100 qubits; free-tier constraints |

---

---

## Opening Script (~45 seconds, before slide 1)

"Good morning. This project sits at the intersection of machine learning and quantum computing.
The central question is whether quantum algorithms can improve how we search through large collections
of vectors -- the kind of search that powers image retrieval, recommendation systems, and semantic search.

To answer that empirically, we built a complete benchmarking platform where classical and quantum search
engines run on identical data, measured by identical evaluation code. Today I will walk you through
what we built, what we have found so far, and where we expect the results to land."

---

## Slide 1 -- Title (~15 seconds)

No content to deliver here beyond what is on the slide. Use this moment to establish composure.
Optionally add: "The system is a text-to-image search application -- you type a query, the system finds
matching images -- and the backend runs multiple search algorithms simultaneously so we can compare them."

---

## Slide 2 -- Context and Motivation (~50 seconds)

Start with the problem: vector search is everywhere in modern ML. Recommendation systems, image retrieval,
semantic document search -- all of them work by encoding items as vectors and finding the ones closest to a query.

Point to the CLIP image: this is what enables text-to-image search. CLIP trains two encoders --
one for text, one for images -- so that a text description and the matching image land near each other
in a shared 512-dimensional vector space. Once you have that, finding images with a text query is just
a nearest-neighbour lookup.

The quantum angle: Grover's algorithm has a proven quadratic speedup for unstructured search.
It is one of the very few quantum speedups that has not been overturned by classical improvements.
But almost all the literature is theoretical. Our question is: what does it actually look like
when you run it on a real simulator against real embeddings?

Transition: "Let me be precise about what we are trying to measure."

---

## Slide 3 -- Problem Definition (~45 seconds)

Walk through the three research questions. The third one is the most interesting and is a finding
in itself: even if qRAM existed and state preparation were free, would quantum vector search
actually be better than classical? We will address that directly in slide 10.

Scope: clarify the IBM question upfront. We are not using real quantum hardware.
IBM's free tier has multi-hour queue waits and significant noise beyond about 7 qubits.
That would make controlled scaling experiments impossible to interpret cleanly.
AerSimulator gives us a mathematically exact simulation -- the shot noise behaves identically
to real hardware, so our MRR results are directly transferable. The only thing we are missing
is a hardware noise study, which is not the point of this project.

Transition: "Before the architecture, a quick look at the theory we are building on."

---

## Slide 4 -- Theoretical Background (~60 seconds)

THREE building blocks -- keep this tight, one sentence each, the slides carry the detail.

CLIP [6]: contrastive pre-training aligns a text encoder and an image encoder so they agree on
which text describes which image. The result is a shared vector space where cosine similarity
measures semantic relevance. We use the ViT-B/32 variant at 512 dimensions.

Vector search: the standard classical algorithm here is brute force cosine or FAISS, both O(N).
Worth mentioning HNSW briefly -- that is the production standard at O(log N) approximate search [5].
It will be important when we discuss the quantum picture later.

Quantum algorithms: point to the Grover circuit image.
The swap test estimates the overlap between two quantum states -- that is our similarity measure.
One ancilla qubit, two registers encoding the query and data vectors, a controlled-SWAP,
measure the ancilla. The probability of measuring zero gives you the overlap squared [3].

Grover works differently -- it uses amplitude amplification to boost the probability
of the correct answer after floor(pi * sqrt(N) / 4) iterations [1].
The oracle marks the answer by flipping its phase. The diffusion operator pushes its amplitude up.
Repeat until the probability peaks. This is provably optimal for unstructured quantum search [2].

Important caveat -- point to the amber box: the O(sqrt(N)) count is oracle calls.
Getting the data into superposition first is a separate step. That is the qRAM problem.
We will quantify it on slide 10.

Transition: "Here is how all of this fits together in the system."

---

## Slide 5 -- System Architecture (~50 seconds)

Walk through the pipeline left to right: images go in, CLIP encodes them, vectors are stored
in PostgreSQL with pgvector, then any search engine can query against them, and the API and
frontend surface the comparison.

The key design decision is the strategy pattern. Every engine -- classical or quantum --
implements the same two-method interface: build_index and search. The benchmark harness
does not know or care which engine it is running. That is what makes the comparison fair:
same data, same query, same evaluation logic.

Walk through the engine cards: brute force is our deterministic ground truth.
FAISS is the SIMD-accelerated exact classical baseline. The mock sampler injects
controlled Gaussian noise so we can validate the noise model before running real circuits.
The swap test runs actual Qiskit circuits on AerSimulator.
Grover is the central scaling experiment.

Point out the note about extensibility -- the architecture is not locked to these five engines.
HNSW is a natural addition as future work, as are other quantum approaches.

Transition: "Let me walk through what is actually working today."

---

## Slide 6 -- Completed Work (~55 seconds)

Phases 1 through 4 are done. The pipeline runs end to end from raw image files to benchmark
results in the database.

On quantum circuit verification: this is not just "it runs" -- we have verified correctness.
The swap test overlap matches the analytical formula on known vector pairs.
The Grover oracle call count follows floor(pi * sqrt(N) / 4) across integration tests.
This is important: the circuits are producing results that agree with theory.

Point to the early results table. This is a 20-image integration test -- not the final benchmark.
The numbers are there to show the system works, not to draw conclusions about engine quality.
What they tell us: all classical engines produce identical MRR on exact search, which is expected.
The swap test is close. Grover used 3 oracle calls where classical needed 20 -- that ratio is
exactly what O(sqrt(N)) predicts at N=20. That is the relationship we will measure systematically.

The backend API is also done, including the engines endpoint and the dynamic search endpoint
that accepts a list of engine names as a parameter.

Transition: "Two pieces are still in progress."

---

## Slide 7 -- In Progress and TODO (~45 seconds)

Two open areas.

Frontend: the React application is scaffolded and connecting to the API.
The main remaining work is the comparison view -- a multi-select component where the user
picks which engines to include, and the results render in a dynamic grid.
Not a hardcoded two-column layout -- it adapts to however many engines were selected.
Each result card shows the ranked images, the MRR score, and the oracle call count.

The full benchmark matrix is the primary remaining technical milestone.
The harness is built and integration-tested, but we have not yet run it across the full
configuration space: multiple N values, dimensions 64 through 512, multiple shot budgets.
Running that matrix, verifying the outputs are reproducible, and analysing the scaling curves
is the core of the remaining work. We also need to go back over the algorithm implementations
and verify them carefully against the theoretical predictions before treating any results as final.

All quantitative conclusions are pending that run.

Transition: "Here is the schedule."

---

## Slide 8 -- Timeline (~30 seconds)

Point to the dot markers. Green is done, amber is now, open circles are upcoming.

We are at midterm with the core implementation complete. The next five weeks are the benchmark
campaign, analysis, and thesis writing. The timeline is achievable because the harness is already
built -- we are not waiting on more engineering, we are waiting on compute time and careful analysis.

Brief and move on.

Transition: "Let me be explicit about how we are measuring success."

---

## Slide 9 -- KPIs (~40 seconds)

Two primary KPIs.

MRR measures quality: does the system return the right image near the top?
It is directly comparable across all engines because they all operate on the same normalised vectors
with the same ground truth. MRR 1.0 means you never need to scroll. MRR 0.5 means the right answer
is on average second.

Oracle call count is our cross-engine speed metric. It is hardware-independent and captures the
algorithmic difference between O(N) and O(sqrt(N)). Wall-clock time is not a valid cross-engine
comparison -- the simulator's wall-clock reflects how expensive it is to simulate quantum circuits
on a CPU, not how fast the quantum algorithm is. So we do not use it.

The quantum-specific metrics -- shots, circuit depth, qubits -- tell us what the algorithm costs
in terms of physical quantum resources. Those are what we need to know when thinking about
whether any of this could run on real hardware.

The amber box: all final values pending the benchmark run.

---

## Slide 10 -- The Honest Quantum Picture (~60 seconds)

This slide has the most important result in the project, so take your time here.

Walk through the two-step problem. Quantum search is not one operation -- it is two.
First you load the data into superposition. Without qRAM that takes O(N) gates, the same as
classical scan [4]. The speedup you gained from Grover is immediately cancelled.
Second, Grover finds the answer in O(sqrt(N)) calls [1] -- and that part works. We verify it.
But the total complexity without qRAM is still O(N).

Point to the qRAM table. The bucket-brigade qRAM model requires O(N) quantum routing nodes
as physical hardware [4]. With error correction, roughly 1,000 physical qubits are needed per
logical qubit. To load 1,000 vectors into superposition you need roughly a million physical
qubits. IBM's best machine today has about 1,100 [9]. For a million vectors: a billion
physical qubits. This is not a timeline problem or a budget problem. The hardware architecture
for qRAM does not exist and has no credible path to existence. And critically: qRAM is a
completely different hardware architecture from processor qubits -- IBM's processor qubits
cannot substitute for qRAM nodes.

Now the more interesting result -- point to the complexity table.
Even if qRAM existed, HNSW [5] runs in O(log N). Grover [1] runs in O(sqrt(N)).
Log N grows much slower than sqrt(N). At N = one million, HNSW needs about 20 operations.
Grover with ideal qRAM needs 785 oracle calls [1][5]. HNSW wins by 40x, on a laptop, today.

The only scenario where Grover would win is exact nearest-neighbour search at very large N,
where you specifically need the exact answer rather than an approximate one. In practice,
HNSW recall is 95-99% [5] and the approximate nearest neighbour is indistinguishable from the
exact one for a user. That niche essentially does not exist in real ML applications.

This is the honest answer to the research question: quantum vector search is theoretically
elegant, one of the few proven quantum speedups that has not been dequantized [7], but it is
not competitive with classical algorithms for this problem even in an ideal hardware future.

---

## Slide 11 -- Expected Outcomes (~35 seconds)

Walk through the hypotheses quickly -- these are what we expect to find, not what we have found.

The contribution framing: we are not claiming a new discovery. We are claiming empirical
verification of theoretical predictions, a complete and fair benchmarking infrastructure,
and a rigorous documented analysis of where the gap between quantum theory and quantum practice lies.

Read out the defensible claim callout -- this is the one-sentence version of the project.

Transition to closing.

---

## Closing Script (~25 seconds, after slide 11, before sources)

"To summarise: the system is built, the algorithms are running and verified on integration tests,
and the benchmark infrastructure is ready. What remains is executing the full experiment,
analysing the scaling curves, and writing the thesis.

The finding we expect to demonstrate -- that Grover's oracle count follows O(sqrt(N)) while
being unable to beat classical search in practice -- is already supported by theory and our
initial results. The full benchmark will put numbers on it.

We welcome your questions and any feedback on the methodology. Thank you."

---

## Q&A Cheat Sheet

**"So quantum is useless for search?"**

Not useless -- Grover's proven speedup [1] is real and one of the few unconditional quantum speedups
not overturned by classical improvements [7]. But for this specific problem: yes, in practice it cannot
compete. Without qRAM [4] the total complexity is still O(N). With hypothetical qRAM, HNSW [5] already
beats it at O(log N). Grover's niche -- exact search at extreme N -- barely exists in ML applications.

---

**"What is your actual contribution if the conclusion is negative?"**

We implemented Grover's algorithm [1] and the quantum swap test [3] on a real circuit simulator and
empirically verified they behave as theory predicts. Oracle calls follow floor(pi*sqrt(N)/4)
across multiple dataset sizes. We built the infrastructure to measure this fairly.
We also built a complete, working text-to-image search system around it.
That is the contribution: engineering plus empirical verification plus honest analysis.
Negative results that are well-supported are scientifically valid.

---

**"Why not use real IBM quantum hardware?"**

IBM free tier has multi-hour queue waits and significant gate noise beyond about 7 qubits [9].
That would make controlled scaling experiments impossible to interpret cleanly.
AerSimulator is mathematically exact -- it gives the same statistics as a noiseless chip.
Shot noise is identical on simulator and real hardware, so our MRR results transfer directly.
IBM hardware would be a noise-accuracy study, not the core benchmark, and that is out of scope.

---

**"Why is the Grover engine slow in your wall-clock timings?"**

That timing reflects simulation overhead on a CPU -- the simulator tracks 2^n amplitudes simultaneously
using classical memory. A real quantum chip processes all amplitudes in parallel by physical law.
Quantum engine wall-clock time on a simulator is not meaningful, which is why oracle call count
is the cross-engine comparison metric, not wall-clock speed.

---

**"Why use predefined queries instead of free-text input?"**

With arbitrary free-text input there is no ground truth -- we can show results from two engines
side by side but cannot compute MRR, so there is no objective way to say which engine did better.
We would just be presenting two unscorable ranked lists. Predefined queries with known ground-truth
image matches [8] are what makes quantitative comparison possible.

---

**"What would you need to actually make quantum search practical?"**

Two things. First, working qRAM at scale [4] -- roughly a billion physical qubits for a million-vector
dataset, a hardware category that does not exist. Second, you would still need to beat HNSW's [5]
O(log N) approximate performance, which Grover's [1] O(sqrt(N)) does not do. Realistically, quantum
computing's advantages are in chemistry simulation, cryptography, and certain optimisation problems --
not in vector search, where classical algorithms are already excellent.

---

**"Should you have implemented HNSW for comparison?"**

That is a fair point. HNSW [5] is the most relevant classical benchmark for the quantum question because
it shows that O(log N) classical search already exists. We have it documented as a next step.
Including it would make the comparison against Grover even cleaner, and it is a natural extension
of the current architecture given the strategy pattern design.

---

## Timing Guide

| Slide | Content | Target time |
|-------|---------|-------------|
| Opening | Script | 0:45 |
| 1 | Title | 0:15 |
| 2 | Context | 0:50 |
| 3 | Problem | 0:45 |
| 4 | Theory | 1:00 |
| 5 | Architecture | 0:50 |
| 6 | Completed | 0:55 |
| 7 | In Progress | 0:45 |
| 8 | Timeline | 0:30 |
| 9 | KPIs | 0:40 |
| 10 | Quantum picture | 1:00 |
| 11 | Outcomes | 0:35 |
| Closing | Script | 0:25 |
| **Total** | | **~8:15** |

If running long: compress slides 8 (timeline, 20 sec) and 9 (KPIs, 30 sec) -- they are supporting,
not core. Do not cut slides 10 or 11 -- that is where the project's intellectual depth lives.
