# Quantum Computing Intuition - The Maze

This file explains quantum computing from zero, using the maze analogy your professor
described. No prior physics or math required.

---

## 1. The classical way - one door at a time

Imagine a room with 1,000 locked doors. Behind exactly one door is the prize. You have
a key that glows when it is touching the right door, but you can only hold it up to one
door at a time.

**Classical search:** Hold the key up to door 1. Not glowing. Try door 2. Not glowing.
Try door 3... On average you find the prize after 500 attempts. Worst case: 1,000.

This is exactly how classical brute-force search works. You check every candidate one
by one. For N candidates: O(N) checks.

---

## 2. The quantum trick - all doors at once

Quantum mechanics allows a particle (or a qubit) to be in multiple states at the same
time. This is called **superposition**.

The classic analogy your professor mentioned: you do not send one copy of yourself down
one path. You send a copy down every path simultaneously. All copies exist at the same
time, each one having a certain "amplitude" (think of it as a strength, or probability
weight).

In the door analogy: you are somehow in front of all 1,000 doors simultaneously. Each
"copy of you" has equal weight. This is what a Hadamard gate does to a quantum register
-- it puts all N states into equal superposition at once.

![Bloch sphere - a single qubit in superposition](https://upload.wikimedia.org/wikipedia/commons/f/f0/Bloch_Sphere_representation.svg)

> A single qubit can be in a combination of |0> and |1> at the same time. The Bloch
> sphere shows every possible state as a point on its surface. The north pole is |0>,
> the south pole is |1>, and everything in between is a superposition of both.
> With n qubits you get 2^n states simultaneously.

---

## 3. The problem with just "being everywhere"

Being in superposition is not enough on its own. If you measured immediately after the
Hadamard step, you would collapse to one of the 1,000 doors at random with equal
probability. 1/1,000 chance of finding the prize - worse than just trying door 1.

You need a way to *boost* the probability of the correct answer before measuring. That
is what the next two steps do.

---

## 4. The oracle - marking the prize door

The oracle does not discover the answer. It is *constructed* to mark a specific state.
There are two very different situations:

**In theory - the oracle computes the answer.**
The oracle is a quantum circuit that evaluates a function (e.g. "is this the closest
vector to the query?") across all N states simultaneously while they are in superposition.
It does not search sequentially - it runs the computation over all candidates at once
and flips the phase of whichever state satisfies the condition. But to do this, the
circuit needs all N database vectors loaded into quantum registers at the same time.
That is the qRAM requirement. Without qRAM, you cannot build this oracle.

**In our simulation - the oracle is hardcoded.**
We have no qRAM, so we find the nearest neighbour classically first (brute force), then
construct a circuit that marks exactly that index. The oracle "knows" because we told it
the answer before running the quantum part. This is why the simulation is measuring the
*scaling behaviour* of amplitude amplification, not a search that replaces the classical step.

In both cases the oracle does one specific thing: it flips the phase (the sign of the
amplitude) of the target state, leaving every other state untouched.

Amplitude is a complex number. Think of it as an arrow. Flipping the phase is like
flipping that arrow upside-down - the magnitude does not change, only the direction.

Going back to the doors: the oracle secretly paints the prize door's arrow upside-down.
From the outside nothing looks different yet. But the marking is there, ready to be
exploited.

**Key point:** The oracle does not *reveal* the answer. It marks it. You still need to
*amplify* it.

**Why can't the oracle just tell you what it marked?**

Because the oracle is not a classical function that returns a value - it is a quantum gate
that transforms quantum states. It has no output channel. The marking lives inside the
quantum amplitudes as a sign change, trapped inside the quantum system.

The only way to extract classical information from a quantum system is to measure it. But
measuring right after the oracle still gives you a random state - the phase flip did not
change any probabilities (probability = |amplitude|^2, squaring removes the sign). You would
still get a random answer.

If the oracle could simply tell you which state it marked, you would not need Grover at all --
you would run the oracle once, ask "what did you mark?", and have your answer in O(1). The
reason Grover is interesting is precisely that the oracle evaluates the condition across all
N states simultaneously, but only as a quantum operation, not as a readable output. You pay
for that power with the constraint that measurement only gives you one answer, and only gives
you the *right* answer if the amplitudes are already concentrated there.

The diffusion step is the bridge: it converts the oracle's invisible phase marking into a
real shift in measurement probabilities, round by round, until the target dominates.

---

## 5. The diffusion step - cancelling dead ends, boosting the prize

This is the heart of Grover's algorithm. The diffusion operator does something elegant:
it reflects all amplitudes around their average value.

Here is why that amplifies the marked state:

Before diffusion:
- 999 normal states each have amplitude +A (small positive number, let's say +1)
- 1 marked state has amplitude -A (the oracle flipped it, so -1)
- Average amplitude across all 1,000 states is slightly below +1 (the one -1 pulls it down)

After reflecting around the average:
- Every state's new amplitude = 2 x average - old amplitude
- The 999 normal states: each gets a bit smaller (they were above average, reflecting
  pushes them below average)
- The 1 marked state: it was well below average (-1), so reflecting it around the
  average pushes it well above average - it becomes a large positive number

The net effect: every round of oracle + diffusion makes the marked state's amplitude a
bit larger and every other state's amplitude a bit smaller. After enough rounds the
marked state is so dominant that measuring almost certainly lands on it.

**This is amplitude amplification.** You are not eliminating wrong answers one by one.
You are using wave interference - like waves in water that cancel out or reinforce each
other - to sculpt the probability distribution so the correct answer dominates.

![Grover's algorithm circuit](https://upload.wikimedia.org/wikipedia/commons/a/ae/Grovers_algorithm.svg)

> The circuit structure: Hadamard (superposition) -> Oracle -> Diffusion -> repeat.
> Each oracle+diffusion cycle is one "Grover iteration". You need about sqrt(N) of them.

---

## 6. How many rounds until the prize dominates?

The amplitudes grow like a sine curve. If you do too few rounds the prize has not been
amplified enough. If you do *too many* rounds you actually overshoot - the prize starts
shrinking again and wrong answers come back.

The exact sweet spot is `floor(pi * sqrt(N) / 4)` iterations. This is where the probability
of measuring the correct state is at its maximum (close to 1).

| N (doors / dataset size) | Iterations needed | Probability of success |
|---|---|---|
| 4 | 1 | ~1.0 |
| 16 | 3 | ~0.96 |
| 100 | 8 | ~0.98 |
| 1,000 | 25 | ~0.999 |
| 1,000,000 | 785 | ~0.999 |

For classical brute force those numbers are 4, 16, 100, 1,000, and 1,000,000
respectively. The gap grows as N grows - that is what O(sqrt(N)) vs O(N) means.

---

## 7. The measurement - collapsing to the answer

After `floor(pi * sqrt(N) / 4)` iterations you measure. Quantum measurement is not passive --
it forces the quantum state to commit to one outcome. The probability of each outcome
is proportional to the square of its amplitude.

Because the diffusion step has been amplifying the target's amplitude for many rounds,
its amplitude squared (its probability) is now close to 1. Measurement almost always
gives you the correct door.

---

## 8. The killer problem - state preparation and qRAM

### First: qRAM is not the same as IBM's quantum processor

This distinction is critical and easy to miss.

#### What IBM actually built - processor qubits

IBM's quantum processors are the **quantum CPU**. A processor qubit runs quantum gates:
it can be put in superposition, entangled with other qubits, and measured. Chains of
gates form a circuit. Circuits implement algorithms - the oracle, the diffusion step,
the swap test. This is computation.

IBM's processor qubit counts over time:

| Year | Processor | Qubits |
|---|---|---|
| 2019 | Falcon | 27 |
| 2021 | Eagle | 127 |
| 2022 | Osprey | 433 |
| 2023 | Condor | ~1,100 |

These are all the same type of thing - superconducting processor qubits for running
circuits. This is what we simulate with AerSimulator. IBM built this; it exists.

#### What qRAM nodes are - quantum routers

A qRAM node is a **quantum router**, not a computing qubit. It does not run gates or
execute algorithms. Its only job is to route a quantum signal to the right memory address
while keeping the routing in superposition.

qRAM is structured as a binary tree. To look up vector number 437 out of 1,000:
- Enter the tree at the root
- At each branch, go left or right based on the bits of address "437"
- After ~10 steps (log2(1000)) you reach the leaf - your vector

Each branching point is one qRAM node - a quantum switch. The tree must stay quantum
(not collapse to a classical path) because Grover needs to route to *all* addresses
simultaneously in superposition.

A binary tree with N leaves has ~2N total nodes. That is why N vectors requires O(N)
qRAM nodes. There is no shortcut - it is a consequence of how binary trees are structured.

#### The comparison

| | Processor qubit | qRAM node |
|---|---|---|
| Job | Runs gates, executes algorithms | Routes a signal to a memory address |
| Analogy | Transistor in a CPU | Switch in an address decoder |
| IBM built this? | Yes | No - nobody has |
| Scales with | Circuit complexity | Dataset size (O(N)) |

You cannot use processor qubits as qRAM nodes. They are different devices with different
physical architectures, like asking your CPU's transistors to act as RAM capacitors.

When we say "qRAM doesn't exist," we are not saying IBM's processor is too small. We are
saying the memory device - an entirely different piece of hardware that has never been
built by anyone - does not exist. Both are built from qubits, but they need completely different physical architectures.
Processor qubits are wired for gate operations - running circuits, executing algorithms.
qRAM nodes need qubits arranged as a memory routing tree, with different connectivity,
different error correction, and different fabrication requirements. You cannot repurpose
IBM's processor qubits as qRAM nodes, just as you cannot repurpose a CPU's transistors
as RAM capacitors - same underlying physics, incompatible architecture.

### The state preparation problem

Everything above assumes you can load all N vectors into superposition in the first
place. This is called **state preparation** and it is where the whole speedup breaks
down in practice.

Loading N classical numbers into a quantum superposition takes O(N) quantum gate
operations - the same work as just checking all N items classically. Without a
shortcut, the total cost is:

```
O(N) state preparation + O(sqrt(N)) Grover search = O(N) total
```

The speedup evaporates.

The theoretical solution is **qRAM** (Quantum Random Access Memory) - a type of
quantum memory that can load N items into superposition in O(log N) steps. With qRAM
the total becomes O(log N) + O(sqrt(N)) = O(sqrt(N)), and the speedup is real end-to-end.

The problem: **qRAM does not exist.** The bucket-brigade qRAM architecture would require
O(N) quantum routing nodes as memory hardware. With error correction (~1,000 physical
qubits per logical qubit), storing even 1,000 vectors in qRAM would need ~1,000,000
physical qubits of memory hardware. For comparison, 1,000 vectors in classical RAM is
~2 MB. This is not a timeline problem - the hardware architecture does not exist at
any scale on any roadmap. (Note: this is separate from IBM's quantum processors, which
run circuits - see the subsection above.)

---

## 9. Three compounding reasons Grover loses - even with ideal qRAM

This is the complete picture. Each layer is sufficient on its own. All three together
leave no realistic path to quantum vector search being competitive.

### Blocker 1 - qRAM does not exist (hard blocker today)

Without qRAM, state preparation is O(N). Total cost: O(N) + O(sqrt(N)) = O(N). No speedup
over brute force, let alone HNSW. This is the situation right now.

### Blocker 2 - qRAM hardware scales as O(N) quantum nodes (economic blocker at scale)

Even if qRAM technology existed, the bucket-brigade architecture requires O(N) physical
quantum routing nodes to address N memory locations. Classical RAM also scales as O(N)
bits - but the cost per unit is not comparable:

| | Classical RAM | qRAM (hypothetical) |
|---|---|---|
| 1 billion 512-dim vectors | ~2 TB, costs ~$50-100 today | ~1 billion qRAM nodes; with error correction ~1 trillion physical qubits |
| Cost per "slot" | fractions of a cent | trillions of dollars at any foreseeable cost per qubit |

Both memory types scale linearly with dataset size. Classical RAM wins because it is
already cheap. qRAM, even in an optimistic future, would require a physically massive
quantum hardware installation proportional to dataset size. This is not a technology
problem you solve by waiting - it is a fundamental resource comparison.

### Blocker 3 - Grover's O(sqrt(N)) is beaten by HNSW's O(log N) classically

Even ignoring blockers 1 and 2 - even with free, perfect, infinitely scalable qRAM --
Grover achieves O(sqrt(N)) search. Classical HNSW achieves O(log N) approximate search.
O(log N) grows slower than O(sqrt(N)). HNSW wins on the algorithm alone.

At N = 1,000,000:
- HNSW: ~20 operations, on a laptop, today, 95-99%+ accuracy, zero exotic hardware
- Grover + ideal qRAM: ~785 oracle calls, plus a trillion-qubit memory device

HNSW wins by ~40x even under the most favourable possible assumptions for quantum.

### Why this matters

The conclusion is not just "quantum hardware doesn't exist yet." It is that for vector
similarity search specifically, quantum offers no algorithmic advantage even in the
ideal case, because the problem has geometric structure that classical algorithms already
exploit to reach O(log N). Grover does not exploit vector geometry - it treats search
as unstructured. HNSW exploits it completely.

**The ideal-world comparison.**
In an ideal world with infinite, free, perfect qRAM, Grover would be meaningful for quantum vector search:
it would return the exact nearest neighbour in O(sqrt(N)) oracle calls, with no approximation
error - unlike HNSW, which accepts some inaccuracy in exchange for speed. That is a
genuine advantage in correctness. But at any dataset size large enough to matter,
O(log N) is so much smaller than O(sqrt(N)) that HNSW's approximation is the better
engineering trade: a few percent of missed results versus ~40x more operations and a
hardware installation proportional to dataset size that does not exist.

The conclusion is therefore: for exact vector search, Grover wins over brute
force (O(N)) in theory - but exact search is an impractical goal at scale, and
no one builds systems that require it. The practical question is always approximate
search at scale, and there HNSW dominates regardless of QRAM assumptions.

---

## 10. So what is Grover actually good for?

Grover's speedup is a **proven, unconditional quantum speedup** for unstructured search.
"Unstructured" means no index, no shortcut, no way to skip candidates - you genuinely
have to check. Classical cannot do better than O(N) for unstructured search. Grover does
O(sqrt(N)). That is real.

The speedup has also not been "dequantized" - no one has found a classical algorithm
that matches it for truly unstructured problems (unlike some other quantum algorithms
that turned out to have classical equivalents).

### When HNSW doesn't apply and Grover would win

HNSW requires building an index in advance on a static dataset and exploits the geometric
structure of vectors in a metric space. When either condition breaks down, you are back to
unstructured search and Grover has its opening.

**No geometric structure.**
HNSW works because nearby vectors stay nearby - it builds a graph of neighbours from that
structure. If the search is over an arbitrary boolean function ("does this input satisfy this
condition?"), there is no geometry to exploit and no index to build. Grover's oracle works on
any computable function, not just distance in a metric space.

**Cryptography.**
Finding a hash preimage (a password that produces a given hash) is pure unstructured search
-- the hash function deliberately destroys structure. You cannot index hash outputs. Classical
is stuck at O(N). Grover does O(sqrt(N)). This is the domain where quantum search actually matters.

**Combinatorial search.**
SAT solving, finding a satisfying assignment to a boolean formula - no geometry, no shortcut,
no index possible. Grover applies directly.

**One-shot data with no preprocessing.**
If you receive data and must search it immediately without any indexing phase, brute force is
all you have classically. Grover beats it.

### Does Grover need qRAM for cryptography?

No - and this is the key difference from vector search. For a hash preimage search, the
oracle is the hash function itself implemented as quantum gates: "does hash(x) equal the
target?" The circuit runs entirely on the processor. There is no dataset to load into
superposition. qRAM is only needed when the oracle has to evaluate distances over a stored
dataset - not when it computes a function from scratch.

This means Grover is a real cryptographic threat in principle. AES-128 has effective 64-bit
security against Grover (halved from 128-bit), because Grover can search the key space in
O(sqrt21^28) = O(264) oracle calls instead of O(21^28). This is why post-quantum cryptography
standards recommend AES-256 - Grover halves it to 128-bit, which remains acceptable.

**However**, breaking AES-128 with Grover still requires ~264 oracle calls, each running a
full AES circuit on fault-tolerant hardware. Current estimates put this at millions of
physical qubits running for years. Not a near-term threat, but a real long-term one.

### Grover vs Shor - two different threats to cryptography

The headlines about "quantum breaks encryption" mostly conflate two different algorithms:

- **Grover** threatens *symmetric* encryption (AES, SHA). Quadratic speedup. Halves effective
  key length. Mitigated by doubling key size (AES-128 -> AES-256).
- **Shor** threatens *asymmetric* encryption (RSA, ECC). *Exponential* speedup for integer
  factorization and discrete logarithm. RSA-2048 is broken entirely - no key size increase
  helps. This is the catastrophic threat that drives post-quantum cryptography research.

Grover is the less severe threat. Shor is the one that breaks the internet's security model.

### Why vector search is the wrong problem for Grover

For vector similarity search in ML: the data has rich geometric structure (HNSW exploits it),
approximation is almost always acceptable (HNSW's 95-99% recall is fine), and the qRAM
requirement blocks state preparation entirely. Grover's real domain is problems with no
exploitable structure. Vector search just happens to be the wrong shape for it.

### Is Grover the best at anything? What is it actually used for?

In practice today: nothing at production scale. The fault-tolerant hardware to run it usefully
does not exist yet. But theoretically it holds a strong position:

**It is proven optimal for unstructured search.**
There is a proven lower bound that no quantum algorithm - not just Grover, any algorithm --
can do better than O(sqrt(N)) for truly unstructured search. Grover hits that bound exactly. That
is rare in computer science: most algorithms are just "the best we know of." Grover is
provably the best possible.

**It is a subroutine inside larger quantum algorithms.**
Many algorithms contain a step that is essentially "search N candidates for one satisfying a
condition." You can drop Grover in as that step and get a quadratic speedup on the whole
algorithm. Most of Grover's practical theoretical value is here - not as a standalone search
tool but as a component that makes other quantum algorithms faster.

**Collision finding in cryptography.**
Finding two inputs that produce the same hash output (used in attacking hash functions) --
Grover-based algorithms do this in O(N^(1/3)) vs the classical O(N^(1/2)). A real
improvement, just not deployable on current hardware.

**NP problems generally.**
Any NP problem is essentially "search an exponential space for a satisfying assignment."
Grover gives a quadratic speedup on all of them. For problems with 2^300 possible
assignments, even a quadratic speedup is enormous in theory.

The blunt summary: Grover is a fundamental theoretical result that defines the limits of
quantum search, and a useful building block inside future algorithms. It is not a near-term
practical tool. Shor gets the headlines because it threatens something we rely on right now.
Grover's impact is more abstract and longer-term.

### When will Shor break encryption?

Nobody knows. Breaking RSA-2048 requires ~4,000 logical qubits - with error correction
overhead, that is roughly 4-8 million physical qubits. Current best hardware is ~1,100
noisy physical qubits. Credible estimates range from 10 to 30+ years. Some researchers say
never, if error rates do not improve fundamentally.

The threat that already exists is "harvest now, decrypt later" - adversaries collecting
encrypted traffic today to decrypt once the hardware arrives. NIST responded: in 2024 they
finalized post-quantum cryptography standards resistant to both Shor and Grover. TLS,
Signal, and Apple iMessage have already started migrating. The cryptography world is
treating it as a planning horizon, not science fiction.

---

## Summary

| Step | What happens | Analogy |
|---|---|---|
| Hadamard | All N states in superposition | You are in front of all 1,000 doors at once |
| Oracle | Marks target state (phase flip) | Prize door gets secretly tagged |
| Diffusion | Amplifies marked state via interference | Dead-end copies cancel; prize copy grows |
| Repeat sqrt(N) times | Marked amplitude keeps growing | Each round: prize more likely, others less |
| Measure | Collapse to answer | You open one door - almost certainly the prize |

The magic is in step 3: **interference**. Quantum amplitudes are signed numbers (they
can be positive or negative). The diffusion step is engineered so that wrong answers
cancel each other out (negative + positive = 0) while the right answer's copies add up
(positive + positive = bigger positive). This is not magic - it is wave mechanics.
The same principle lets noise-cancelling headphones work.

For more on how this applies to vector search specifically, see
`QUANTUM_SEARCH_ANALYSIS.md`. For how the circuits are actually implemented in this
project, see `THEORY.md`.

Quantum computing isn't powerful because it's faster at everything - it's powerful because for certain problems (like factoring large numbers, simulating quantum systems, and some structured algebraic problems), it uses interference and quantum states to achieve exponential or otherwise unique speedups that classical computers can't match; but for problems like vector search, Grover's algorithm only gives a limited sqrt(N) improvement (at large hardware costs) and doesn't beat well-optimized classical approaches that already use massive parallelism and indexing effectively.


---
*Last updated: 2026-04-17.*
