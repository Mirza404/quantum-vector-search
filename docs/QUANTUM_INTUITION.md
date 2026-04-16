# Quantum Computing Intuition -- The Maze

This file explains quantum computing from zero, using the maze analogy your professor
described. No prior physics or math required.

---

## 1. The classical way -- one door at a time

Imagine a room with 1,000 locked doors. Behind exactly one door is the prize. You have
a key that glows when it is touching the right door, but you can only hold it up to one
door at a time.

**Classical search:** Hold the key up to door 1. Not glowing. Try door 2. Not glowing.
Try door 3... On average you find the prize after 500 attempts. Worst case: 1,000.

This is exactly how classical brute-force search works. You check every candidate one
by one. For N candidates: O(N) checks.

---

## 2. The quantum trick -- all doors at once

Quantum mechanics allows a particle (or a qubit) to be in multiple states at the same
time. This is called **superposition**.

The classic analogy your professor mentioned: you do not send one copy of yourself down
one path. You send a copy down every path simultaneously. All copies exist at the same
time, each one having a certain "amplitude" (think of it as a strength, or probability
weight).

In the door analogy: you are somehow in front of all 1,000 doors simultaneously. Each
"copy of you" has equal weight. This is what a Hadamard gate does to a quantum register
-- it puts all N states into equal superposition at once.

![Bloch sphere -- a single qubit in superposition](https://upload.wikimedia.org/wikipedia/commons/f/f0/Bloch_Sphere_representation.svg)

> A single qubit can be in a combination of |0> and |1> at the same time. The Bloch
> sphere shows every possible state as a point on its surface. The north pole is |0>,
> the south pole is |1>, and everything in between is a superposition of both.
> With n qubits you get 2^n states simultaneously.

---

## 3. The problem with just "being everywhere"

Being in superposition is not enough on its own. If you measured immediately after the
Hadamard step, you would collapse to one of the 1,000 doors at random with equal
probability. 1/1,000 chance of finding the prize -- worse than just trying door 1.

You need a way to *boost* the probability of the correct answer before measuring. That
is what the next two steps do.

---

## 4. The oracle -- marking the prize door

The oracle is a quantum gate that knows which state is the answer. It does one specific
thing: it flips the phase (the sign of the amplitude) of the correct state, leaving
every other state untouched.

Amplitude is a complex number. Think of it as an arrow. Flipping the phase is like
flipping that arrow upside-down -- the magnitude does not change, only the direction.

Going back to the doors: the oracle secretly paints the prize door's arrow upside-down.
From the outside nothing looks different yet. But the marking is there, ready to be
exploited.

**Key point:** The oracle does not *reveal* the answer. It marks it. You still need to
*amplify* it.

---

## 5. The diffusion step -- cancelling dead ends, boosting the prize

This is the heart of Grover's algorithm. The diffusion operator does something elegant:
it reflects all amplitudes around their average value.

Here is why that amplifies the marked state:

Before diffusion:
- 999 normal states each have amplitude +A (small positive number, let's say +1)
- 1 marked state has amplitude -A (the oracle flipped it, so -1)
- Average amplitude across all 1,000 states is slightly below +1 (the one -1 pulls it down)

After reflecting around the average:
- Every state's new amplitude = 2 × average - old amplitude
- The 999 normal states: each gets a bit smaller (they were above average, reflecting
  pushes them below average)
- The 1 marked state: it was well below average (-1), so reflecting it around the
  average pushes it well above average -- it becomes a large positive number

The net effect: every round of oracle + diffusion makes the marked state's amplitude a
bit larger and every other state's amplitude a bit smaller. After enough rounds the
marked state is so dominant that measuring almost certainly lands on it.

**This is amplitude amplification.** You are not eliminating wrong answers one by one.
You are using wave interference -- like waves in water that cancel out or reinforce each
other -- to sculpt the probability distribution so the correct answer dominates.

![Grover's algorithm circuit](https://upload.wikimedia.org/wikipedia/commons/a/ae/Grovers_algorithm.svg)

> The circuit structure: Hadamard (superposition) -> Oracle -> Diffusion -> repeat.
> Each oracle+diffusion cycle is one "Grover iteration". You need about sqrt(N) of them.

---

## 6. How many rounds until the prize dominates?

The amplitudes grow like a sine curve. If you do too few rounds the prize has not been
amplified enough. If you do *too many* rounds you actually overshoot -- the prize starts
shrinking again and wrong answers come back.

The exact sweet spot is `floor(π · √N / 4)` iterations. This is where the probability
of measuring the correct state is at its maximum (close to 1).

| N (doors / dataset size) | Iterations needed | Probability of success |
|---|---|---|
| 4 | 1 | ~1.0 |
| 16 | 3 | ~0.96 |
| 100 | 8 | ~0.98 |
| 1,000 | 25 | ~0.999 |
| 1,000,000 | 785 | ~0.999 |

For classical brute force those numbers are 4, 16, 100, 1,000, and 1,000,000
respectively. The gap grows as N grows -- that is what O(√N) vs O(N) means.

---

## 7. The measurement -- collapsing to the answer

After `floor(π · √N / 4)` iterations you measure. Quantum measurement is not passive --
it forces the quantum state to commit to one outcome. The probability of each outcome
is proportional to the square of its amplitude.

Because the diffusion step has been amplifying the target's amplitude for many rounds,
its amplitude squared (its probability) is now close to 1. Measurement almost always
gives you the correct door.

---

## 8. The killer problem -- state preparation and qRAM

### First: qRAM is not the same as IBM's quantum processor

This distinction is critical and easy to miss.

#### What IBM actually built -- processor qubits

IBM's quantum processors are the **quantum CPU**. A processor qubit runs quantum gates:
it can be put in superposition, entangled with other qubits, and measured. Chains of
gates form a circuit. Circuits implement algorithms -- the oracle, the diffusion step,
the swap test. This is computation.

IBM's processor qubit counts over time:

| Year | Processor | Qubits |
|---|---|---|
| 2019 | Falcon | 27 |
| 2021 | Eagle | 127 |
| 2022 | Osprey | 433 |
| 2023 | Condor | ~1,100 |

These are all the same type of thing -- superconducting processor qubits for running
circuits. This is what we simulate with AerSimulator. IBM built this; it exists.

#### What qRAM nodes are -- quantum routers

A qRAM node is a **quantum router**, not a computing qubit. It does not run gates or
execute algorithms. Its only job is to route a quantum signal to the right memory address
while keeping the routing in superposition.

qRAM is structured as a binary tree. To look up vector number 437 out of 1,000:
- Enter the tree at the root
- At each branch, go left or right based on the bits of address "437"
- After ~10 steps (log₂(1000)) you reach the leaf -- your vector

Each branching point is one qRAM node -- a quantum switch. The tree must stay quantum
(not collapse to a classical path) because Grover needs to route to *all* addresses
simultaneously in superposition.

A binary tree with N leaves has ~2N total nodes. That is why N vectors requires O(N)
qRAM nodes. There is no shortcut -- it is a consequence of how binary trees are structured.

#### The comparison

| | Processor qubit | qRAM node |
|---|---|---|
| Job | Runs gates, executes algorithms | Routes a signal to a memory address |
| Analogy | Transistor in a CPU | Switch in an address decoder |
| IBM built this? | Yes | No -- nobody has |
| Scales with | Circuit complexity | Dataset size (O(N)) |

You cannot use processor qubits as qRAM nodes. They are different devices with different
physical architectures, like asking your CPU's transistors to act as RAM capacitors.

When we say "qRAM doesn't exist," we are not saying IBM's processor is too small. We are
saying the memory device -- an entirely different piece of hardware that has never been
built by anyone -- does not exist. IBM's 1,100 processor qubits and qRAM nodes are not
the same thing and cannot be compared directly.

### The state preparation problem

Everything above assumes you can load all N vectors into superposition in the first
place. This is called **state preparation** and it is where the whole speedup breaks
down in practice.

Loading N classical numbers into a quantum superposition takes O(N) quantum gate
operations -- the same work as just checking all N items classically. Without a
shortcut, the total cost is:

```
O(N) state preparation + O(sqrt(N)) Grover search = O(N) total
```

The speedup evaporates.

The theoretical solution is **qRAM** (Quantum Random Access Memory) -- a type of
quantum memory that can load N items into superposition in O(log N) steps. With qRAM
the total becomes O(log N) + O(sqrt(N)) = O(sqrt(N)), and the speedup is real end-to-end.

The problem: **qRAM does not exist.** The bucket-brigade qRAM architecture would require
O(N) quantum routing nodes as memory hardware. With error correction (~1,000 physical
qubits per logical qubit), storing even 1,000 vectors in qRAM would need ~1,000,000
physical qubits of memory hardware. For comparison, 1,000 vectors in classical RAM is
~2 MB. This is not a timeline problem -- the hardware architecture does not exist at
any scale on any roadmap. (Note: this is separate from IBM's quantum processors, which
run circuits -- see the subsection above.)

---

## 9. Three compounding reasons Grover loses -- even with ideal qRAM

This is the complete picture. Each layer is sufficient on its own. All three together
leave no realistic path to quantum vector search being competitive.

### Blocker 1 -- qRAM does not exist (hard blocker today)

Without qRAM, state preparation is O(N). Total cost: O(N) + O(√N) = O(N). No speedup
over brute force, let alone HNSW. This is the situation right now.

### Blocker 2 -- qRAM hardware scales as O(N) quantum nodes (economic blocker at scale)

Even if qRAM technology existed, the bucket-brigade architecture requires O(N) physical
quantum routing nodes to address N memory locations. Classical RAM also scales as O(N)
bits -- but the cost per unit is not comparable:

| | Classical RAM | qRAM (hypothetical) |
|---|---|---|
| 1 billion 512-dim vectors | ~2 TB, costs ~$50-100 today | ~1 billion qRAM nodes; with error correction ~1 trillion physical qubits |
| Cost per "slot" | fractions of a cent | trillions of dollars at any foreseeable cost per qubit |

Both memory types scale linearly with dataset size. Classical RAM wins because it is
already cheap. qRAM, even in an optimistic future, would require a physically massive
quantum hardware installation proportional to dataset size. This is not a technology
problem you solve by waiting -- it is a fundamental resource comparison.

### Blocker 3 -- Grover's O(√N) is beaten by HNSW's O(log N) classically

Even ignoring blockers 1 and 2 -- even with free, perfect, infinitely scalable qRAM --
Grover achieves O(√N) search. Classical HNSW achieves O(log N) approximate search.
O(log N) grows slower than O(√N). HNSW wins on the algorithm alone.

At N = 1,000,000:
- HNSW: ~20 operations, on a laptop, today, 95-99%+ accuracy, zero exotic hardware
- Grover + ideal qRAM: ~785 oracle calls, plus a trillion-qubit memory device

HNSW wins by ~40x even under the most favourable possible assumptions for quantum.

### Why this matters

The conclusion is not just "quantum hardware doesn't exist yet." It is that for vector
similarity search specifically, quantum offers no algorithmic advantage even in the
ideal case, because the problem has geometric structure that classical algorithms already
exploit to reach O(log N). Grover does not exploit vector geometry -- it treats search
as unstructured. HNSW exploits it completely.

---

## 10. So what is Grover actually good for?

Grover's speedup is a **proven, unconditional quantum speedup** for unstructured search.
"Unstructured" means no index, no shortcut, no way to skip candidates -- you genuinely
have to check. Classical cannot do better than O(N) for unstructured search. Grover does
O(√N). That is real.

The speedup has also not been "dequantized" -- no one has found a classical algorithm
that matches it for truly unstructured problems (unlike some other quantum algorithms
that turned out to have classical equivalents).

Where quantum wins is in cases where:
1. The dataset cannot be pre-indexed (qRAM solves state prep)
2. Exact search is required (approximate algorithms like HNSW are not acceptable)
3. N is large enough that O(√N) is meaningfully better than O(N)

For vector similarity search in ML: condition 3 is met, condition 2 is rarely a hard
requirement (approximation is almost always fine), and condition 1 blocks everything
until qRAM hardware exists.

---

## Summary

| Step | What happens | Analogy |
|---|---|---|
| Hadamard | All N states in superposition | You are in front of all 1,000 doors at once |
| Oracle | Marks target state (phase flip) | Prize door gets secretly tagged |
| Diffusion | Amplifies marked state via interference | Dead-end copies cancel; prize copy grows |
| Repeat sqrt(N) times | Marked amplitude keeps growing | Each round: prize more likely, others less |
| Measure | Collapse to answer | You open one door -- almost certainly the prize |

The magic is in step 3: **interference**. Quantum amplitudes are signed numbers (they
can be positive or negative). The diffusion step is engineered so that wrong answers
cancel each other out (negative + positive = 0) while the right answer's copies add up
(positive + positive = bigger positive). This is not magic -- it is wave mechanics.
The same principle lets noise-cancelling headphones work.

For more on how this applies to vector search specifically, see
`QUANTUM_SEARCH_ANALYSIS.md`. For how the circuits are actually implemented in this
project, see `THEORY.md`.
