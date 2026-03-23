# Frequently Asked Questions

**Q: Why does this project exist if quantum offers no speedup over classical search?**
A: Because "does it work?" and "is it faster today?" are two different questions.
Classical vector search is already highly optimised — brute-force cosine similarity with
NumPy, FAISS with SIMD intrinsics, HNSW approximate indices. There is no practical case for
replacing any of these with quantum hardware today.

The point of this project is not to win a race classical computers have already won. The
point is to answer the question that comes *before* that race can be meaningfully run:

1. **Can the quantum similarity computation (the swap test) match classical accuracy?**
   If the algorithm itself is wrong or irreducibly noisy, nothing else matters.
2. **What does it cost in quantum resources?** Qubits, circuit depth, and shots are the
   currency of near-term quantum hardware. This project measures all three as a function
   of vector dimension and noise level.
3. **What are the bottlenecks?** State preparation turns out to cost O(n) gates — the same
   as classical search — which kills the asymptotic speedup. That is the most important
   finding: not that quantum is slow today, but *why*, and what would have to change
   (specifically, efficient qRAM) for it to become competitive.

Quantum hardware is improving rapidly. The algorithms, resource costs, and accuracy
characteristics studied here are the prerequisites for knowing when quantum search becomes
practical — and for recognising when we get there.

*In plain terms:* you do not build the bridge after the river floods. This project
characterises the quantum approach now, while the hardware is still too limited to run it at
scale, so the benchmarking framework, the resource cost model, and the accuracy baseline
are ready when the hardware catches up.

**Q: Why compare classical and quantum search?**
A: Quantum algorithms theoretically offer speedups for certain search problems (Grover's algorithm
is O(√N) for unstructured search vs O(N) classically). For vector similarity search the advantage
is less certain and depends on efficient state preparation, which is an open problem. We study
whether quantum approaches can achieve comparable *accuracy* to classical ones, and characterise
the quantum resource cost, to determine whether they are practically relevant at small scale.

*In plain terms:* classical computers are already very good at searching images. This project
asks: can a quantum computer do the same job just as well? We are not claiming quantum is better
— we are measuring whether it is even competitive at small scale, and what it would cost in
quantum resources to get there.

**Q: What does CLIP actually learn?**
A: CLIP learns a joint embedding function through contrastive training on 400M image-caption
pairs. The loss pushes matched (image, text) pairs to be nearby in embedding space and unmatched
pairs to be far apart. The result is a universal visual-semantic encoder that generalises to
unseen domains without fine-tuning.

*In plain terms:* CLIP is trained to know that the word "dog" and a photo of a dog belong
together. It learns this by looking at 400 million images paired with their captions. After
training, you can type a description and CLIP will find matching images — even for things it
has never explicitly seen — because it has learned a shared language for images and text.

**Q: What is the swap test and why does it measure similarity?**
A: The swap test is a quantum circuit that estimates |⟨ψ|φ⟩|² — the squared inner product of
two quantum states. When states encode L2-normalised vectors as amplitudes, this equals the
squared cosine similarity. The circuit works by using a controlled-SWAP gate and two Hadamard
gates around an ancilla qubit. The measurement statistics of the ancilla encode the overlap.

*In plain terms:* the swap test is a quantum trick for checking how similar two vectors are.
You encode both vectors into quantum states, run a small circuit that involves swapping them
(hence the name), and measure one special qubit. The probability of getting a particular
measurement outcome tells you how similar the two vectors were — the more similar, the more
predictable the result.

**Q: What is amplitude encoding, why do we use it, and what is its limitation?**
A: Amplitude encoding is how classical vectors are loaded into a quantum computer. Quantum gates
can only operate on qubits — not on classical arrays — so any quantum algorithm for similarity
search must first translate vectors into quantum states. Amplitude encoding is the standard
method: a normalised n-dimensional vector is stored as the amplitudes of a log₂(n)-qubit
quantum state. This gives two concrete benefits: (1) it requires exponentially fewer qubits
than naive encodings — a 64-dimensional vector needs only 6 qubits instead of 64; (2) once
two vectors are encoded as quantum states, the swap test can estimate their inner product using
quantum interference, which is the core quantum operation in this project. The limitation is
state preparation: loading an arbitrary classical vector into a quantum register requires O(n)
gates in the worst case, which removes the qubit-count advantage when the bottleneck shifts
to gate count. This is an open research problem in quantum machine learning.

*In plain terms:* imagine you have a list of 64 numbers describing an image. To run a quantum
similarity calculation on it, you first need to "pour" those 64 numbers into the quantum
computer. Amplitude encoding is the way you do that pouring — it squeezes all 64 numbers into
just 6 qubits instead of 64, because each qubit can exist in a superposition that simultaneously
encodes multiple values. That compression is the benefit: fewer qubits means the hardware
requirements are manageable. The catch is that the pouring process itself is slow — it takes
as many steps as just comparing the vectors classically. It is like packing a suitcase very
efficiently, but the packing itself takes as long as the whole trip. The hope for the future is
a technology called qRAM that would make the packing instant — but that does not exist yet.

**Q: Why does more shots lead to higher accuracy in the quantum engine?**
A: Measuring a quantum circuit once gives a single bit. Estimating P(ancilla=0) requires
running the circuit N times and counting. The standard error in the estimate is 1/√N. With
few shots (e.g., 64) the noise in the similarity estimate is large enough to scramble the
ranking. With 2048 shots the noise is small enough (~2%) that rankings match the classical
result on most queries.

*In plain terms:* quantum measurement is random — you run the same circuit twice and can get
different results. To get a reliable similarity score you have to run it many times and
average. It is like flipping a coin to estimate if it is fair: flip it 10 times and you might
get 8 heads by chance; flip it 2000 times and the average settles close to the true value.
More shots = more flips = more reliable answer.

**Q: What is circuit depth and why does it matter?**
A: Circuit depth is the number of sequential gate layers (gates operating on the same qubit
cannot be parallelised). On real quantum hardware, qubits decohere (lose their quantum state)
over time due to environmental noise. Deeper circuits run longer and suffer more decoherence
errors. Circuit depth is therefore a proxy for hardware feasibility on near-term NISQ devices.

*In plain terms:* qubits are fragile — they lose their quantum state quickly due to interference
from the environment. Circuit depth is how many steps the computation takes. A shallow circuit
finishes before the qubits fall apart; a deep circuit runs long enough that errors accumulate
and the result becomes unreliable. It is like trying to carry a melting ice cream cone — the
longer you walk, the less ice cream you end up with.

**Q: What is the difference between the quantum mock engine and the real Qiskit engine?**
A: The `QuantumMockEngine` computes exact cosine similarity and then adds synthetic Gaussian
noise to simulate shot-based statistical error. It does not run any quantum circuits. The
`QiskitSwapTestEngine` builds and executes real Qiskit circuits on `AerSimulator`, which is a
classical software simulation of a quantum computer. The mock is useful for fast iteration and
studying the noise model; the Qiskit engine demonstrates a real quantum algorithm.

*In plain terms:* the mock engine cheats slightly — it computes the right answer the classical
way and then adds random noise to imitate what a quantum measurement would look like. It is
fast and useful for testing. The Qiskit engine actually builds and runs quantum circuits, just
on a software simulator instead of real hardware. The mock is "quantum-inspired"; the Qiskit
engine is the real algorithm running on a virtual chip.

**Q: Why is the Qiskit engine slow in this project?**
A: It runs on AerSimulator, a classical software simulator. Simulating k qubits requires 2^k
complex numbers. For a 128-dim vector we need 15 qubits → 32,768 complex amplitudes per state.
On top of that, the engine runs one full circuit per dataset image per query. For a 100-image
dataset that is 100 circuit executions per query, each with 2048 shots.

*In plain terms:* a real quantum chip with 15 qubits processes all 32,768 possible states at
the same time — that is the whole point of quantum computing. A regular CPU has to work through
them one by one. Add in the fact that you run each circuit 2048 times, for every image in the
dataset, and you end up with a huge amount of work for a laptop that is fundamentally not built
for this job.

**Q: What is FAISS and why is IndexFlatL2 used here?**
A: FAISS (Facebook AI Similarity Search) is a Python library for dense vector similarity search
whose internals use highly optimised SIMD/BLAS routines. `IndexFlatL2` is its exact brute-force
L2 index — it always finds the true nearest neighbours. For our small dataset there is no need
for approximate indices. FAISS is used to demonstrate a production-grade classical baseline
beyond the pure-NumPy brute-force cosine engine.

*In plain terms:* FAISS is Facebook's highly optimised library for finding the most similar
vectors in a large list. `IndexFlatL2` is its simplest mode — compare the query against every
single vector and return the closest ones. No shortcuts, no approximations, always the correct
answer. For our small dataset this is fine; at millions of images you would switch to an
approximate index that trades a little accuracy for a lot of speed.

**Q: What is MRR and when is it useful?**
A: MRR (Mean Reciprocal Rank) averages 1/rank across queries, where rank is the position of
the first relevant result. It is most useful when users care primarily about the first result
they see — search engines, question answering, recommendation. A system that always ranks the
correct answer at position 1 gets MRR = 1.0; always at position 2 gets MRR = 0.5.

*In plain terms:* MRR asks "how far down the list does a user have to scroll before hitting
the first correct result?" If the right image is always the very first result, MRR = 1.0. If
it is always second, MRR = 0.5. It is the most practical metric for a real search interface
where users typically stop looking after the first few results.

**Q: How does dataset size affect the quantum engine's performance and resource cost?**
A: The quantum engine runs one circuit per dataset image per query on a classical simulator.
Simulation runtime scales exponentially with qubit count and linearly with shots × dataset size.
A controlled, small initial dataset is therefore necessary for reproducible experiments that
complete in reasonable time. As the dataset grows, the classical overhead of the simulator
grows proportionally, while the qubit count (set by vector dimension, not dataset size) stays
fixed. On real quantum hardware, larger datasets would increase the number of circuit executions
but not the circuit complexity — making dataset size a scheduling concern rather than a
fundamental quantum resource constraint.

*In plain terms:* imagine you have 4 images and 1 query. The quantum engine compares the query
against each image one at a time using a small circuit, repeating each comparison 512 times
(shots) to get a stable answer. With 4 images that is 4 × 512 = 2048 circuit runs — each of
which requires the laptop to simulate quantum behaviour from scratch. With 400 images it becomes
204 800 runs. The circuit itself never gets more complicated as you add images — it is always
the same small circuit comparing one pair of vectors. The slowness comes purely from the
simulator having to fake quantum physics thousands of times, not from the quantum algorithm
itself being fundamentally harder.

**Q: What is the Strategy Pattern and why is it used?**
A: The Strategy Pattern encapsulates a family of interchangeable algorithms behind a common
interface. The benchmark harness calls `engine.build_index()` and `engine.search()` without
knowing the concrete implementation. This makes it trivial to add new engines, swap out the
embedding model, or change the data source — each dimension of variation is isolated behind
its own abstract interface.

*In plain terms:* all four search engines have the same interface — the same function names,
same inputs, same outputs. The benchmark harness does not know or care which engine it is
talking to. Adding a fifth engine requires no changes to the harness at all. It is like a
power strip with standard sockets — any device with the right plug just works.

**Q: Are the simulator results actually meaningful, or is the simulator just faking it?**
A: The Qiskit AerSimulator is mathematically exact — it computes the full quantum state vector
and produces measurement statistics identical to what a perfect, noiseless quantum chip would
produce. This makes it **more accurate but slower** than real hardware: accuracy is higher
because there is no physical noise; speed is lower because a regular CPU has to simulate
quantum behaviour step by step. Real quantum hardware executes circuits much faster but
introduces noise — gate errors, decoherence, crosstalk — that degrades accuracy below the
simulator baseline, with the degradation growing as circuit depth increases. The simulator
therefore represents the best-case ceiling for the algorithm's accuracy. The quantum mock
engine adds configurable artificial noise to explore what happens as you move away from that
ceiling toward realistic hardware conditions.

*In plain terms:* the simulator gives you the right answer slowly; real quantum hardware gives
you a noisier answer quickly. For this project the simulator is ideal — we care about whether
the algorithm works correctly, not about raw execution speed on hardware that does not yet
exist at scale.

**Q: Should we test on a real quantum computer? IBM offers free credits.**
A: Yes, and it would strengthen the project. IBM Quantum (quantum.ibm.com) provides free
access to real quantum hardware. The circuits used here are small — a handful of qubits for
low-dimensional vectors — so jobs fit within the free tier. The interesting result would be
the gap between simulator accuracy and real-hardware accuracy: real hardware noise would push
scores down, and the gap would grow with circuit depth (more layers = more noise). Showing
that gap empirically would directly validate why circuit depth is tracked as a KPI and give
concrete evidence for the conclusion that hardware limitations, not the algorithm, are the
current bottleneck. The practical downside is queue time — free IBM jobs can wait minutes to
hours depending on demand.

*In plain terms:* the simulator is the ideal version of a quantum computer — no mistakes, just
slow. Running the same experiment on a real IBM chip would show how much accuracy you lose to
hardware imperfection today. That comparison — "here is what the algorithm can do in theory,
here is what it actually does on today's hardware" — would be the strongest possible conclusion
for the project.

**Q: What theoretical quantum advantage exists for similarity search?**
A: Grover's algorithm offers a quadratic speedup (O(√N) vs O(N)) for unstructured search.
For structured vector similarity, algorithms like qRAM-based inner product estimation have
been proposed with polylogarithmic query complexity under certain assumptions. However, these
assume efficient quantum random access memory (qRAM), which does not yet exist as practical
hardware. For near-term NISQ devices, the swap test provides no asymptotic speedup over
classical cosine similarity — the value is in studying the resource requirements and accuracy
characteristics for when better hardware becomes available.

**How Grover's algorithm achieves the √N speedup:**
Classical unstructured search checks items one at a time until it finds the answer — O(N) in
the worst case. Grover's algorithm works in three repeating steps:

1. **Superposition** — load all N candidates into a quantum register simultaneously. Every
   candidate starts with equal probability amplitude (1/√N).
2. **Oracle** — apply a quantum operation that marks the correct answer by flipping its
   phase (making its amplitude negative). The oracle does not tell you which item is correct;
   it is defined as "the operation that recognises a match". All N candidates are checked
   simultaneously because they are all in superposition.
3. **Amplitude amplification (Grover diffusion)** — reflect all amplitudes around their
   average. Because the marked item has a negative amplitude, this reflection makes it larger
   relative to the others. Each iteration roughly doubles the gap.

After approximately π/4 × √N iterations, the marked item has near-100% probability amplitude.
A single measurement then returns it. Total cost: O(√N) oracle calls instead of O(N).

**Why this does not directly apply to this project:**
The oracle for similarity search would need to ask "which of these N image vectors is closest
to my query?" — but answering that question requires computing similarity for every image,
which brings you back to O(N). To get the Grover speedup you need quantum random access memory
(qRAM) that can load all N vectors into superposition in O(log N) steps. qRAM is theoretically
described but has never been built at practical scale.

The swap test used in this project measures the similarity between exactly two vectors. It does
not search — it just computes one similarity value. To search through N images the engine calls
it N times, giving O(N) total. The quantum part is only the similarity computation, not the
search itself.

*In plain terms:* imagine you are looking for a specific face in a crowd of 1 million people.
Classically you check one person at a time — up to 1 million checks. Grover's algorithm puts
all 1 million people into a quantum superposition, then runs a trick that gradually makes the
correct person "glow brighter" in probability while everyone else fades. After about 1000
rounds of this trick, the glowing person is almost certainly the right one. That is where the
√1,000,000 = 1000 number comes from.

The reason this project cannot use Grover's speedup is that you need a way to load all 1
million image vectors into the quantum computer at once (qRAM), and that technology does not
exist yet. Instead this project runs the swap test one image at a time — 1 million separate
quantum comparisons — so there is no speedup over just doing it classically. The value of the
project is demonstrating that the quantum similarity computation itself works correctly and
measuring what it costs, so we are ready when the missing piece (qRAM) eventually arrives.

**Q: Does truncating CLIP embeddings affect benchmark accuracy?**
A: Truncation cuts the less informative components from the end of CLIP embeddings. Most of the
semantic information is concentrated near the front of the vector, so small reductions
(e.g., from 512 → 128 or 64 dimensions) usually preserve nearest-neighbour rankings fairly well.

However, truncation can slightly alter top-k results, which may affect comparisons between search
engines, especially between classical FAISS and quantum engines. If exact ranking fidelity matters
for a benchmark, truncation introduces a confounding factor: differences in results might come from
the truncation rather than the engine itself.

*In plain terms:* truncation makes vectors smaller and faster to process, but it can nudge results a
little. For speed-focused experiments it’s fine; for fair accuracy comparisons, it’s safest to use
full vectors or at least confirm that truncated vectors produce nearly identical rankings.

**Q: Does this project use AI, and exactly how does the CLIP model run locally without a GPU?**
A: Yes — the project uses OpenAI’s CLIP (Contrastive Language–Image Pretraining) model to convert
images and text queries into vectors in a shared embedding space, enabling cross-modal search.
Specifically, during indexing each image is passed through CLIP’s image encoder and the resulting
vector is stored in the database. During benchmarking, each text query is passed through CLIP’s
text encoder on the fly to produce a query vector — this vector is never stored in the database.
The search engines then compare that in-memory query vector against the stored image vectors.

CLIP runs entirely on your local machine via PyTorch. On startup the code checks for a CUDA GPU,
then Apple MPS, and falls back to CPU if neither is available. When running on CPU the model weights
are cast to 32-bit float for compatibility. The variant used here, **ViT-B/32**, has approximately
**63 million parameters across both its image and text encoders** — large by everyday standards, but
small for a vision-language model. It fits comfortably in RAM and runs on CPU without specialised
hardware.

*In plain terms:* CLIP is a pre-trained neural network with 63 million learned values, not a cloud
service. Images are encoded once and saved to the database. When you search, your text query is
encoded on the fly and compared against those stored image vectors — the query vector is never
saved anywhere. PyTorch runs it like any other program on your CPU — no GPU and no API key
required.

**Q: How does classical vector search work in this project?**
A: There are two classical engines.

`BruteForceCosineEngine` normalises every stored image vector once at index-build time. At
search time it normalises the query vector and computes a dot product between the query and
every image vector (a NumPy matrix multiply). Because both sides are normalised, the dot product
equals cosine similarity. It returns the top-k image IDs by descending score. This is exact and
O(N·d) per query — every image is checked.

`FaissFlatEngine` loads all vectors into a FAISS `IndexFlatL2` index. FAISS computes exact L2
(Euclidean) distance from the query to every image vector using SIMD-optimised BLAS routines
under the hood. Also exact and O(N·d), but faster in practice due to low-level CPU optimisations.

*In plain terms:* both engines check every image — there are no shortcuts. The brute-force engine
does it with plain NumPy; FAISS does the same thing using Facebook's highly optimised C++ library
that squeezes out extra speed from modern CPU instructions. For our small dataset the difference
is small; at millions of images, FAISS would be noticeably faster.

**Q: How does quantum vector search work in this project?**
A: The quantum engines receive the **exact same CLIP vectors from the database** as the classical
engines — there is no separate encoding step. The difference is only in how similarity is computed.

`QiskitSwapTestEngine`: at index-build time, each stored image vector (already a classical float
array from the DB) is mathematically reformatted as complex quantum amplitudes — normalised and
padded to the next power of two — so it can be loaded into a quantum circuit. No CLIP is
re-run. At search time, the query vector (also already a classical float array) is reformatted
the same way. For each image, a swap test circuit is built: one qubit register holds the query
amplitudes, another holds the image amplitudes. The circuit applies Hadamard → controlled-SWAP
→ Hadamard → measure on an ancilla qubit. The probability of measuring 0 encodes the squared
cosine similarity. The circuit is run `shots` times (default 2048) and the fraction of 0
outcomes estimates the score. This repeats for every image, giving O(N) circuit executions per
query on Qiskit's AerSimulator.

`QuantumMockEngine`: also uses the same DB vectors. It computes exact cosine similarity
classically and adds Gaussian noise scaled by `layers / shots`, mimicking the statistical error
that shot-based quantum measurement would introduce — without running any circuits.

*In plain terms:* all four engines start from the same CLIP vectors stored in the database.
Classical engines compare the query to each image using a dot product. Quantum engines do the
same comparison using a quantum circuit — they reformat the existing float vectors into quantum
states, run a circuit that "interferes" them, and count measurement outcomes to estimate
similarity. The quantum part is only the similarity computation method, not a different kind of
encoding.
