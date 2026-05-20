# Mentor Presentation Guide

What to show, what to say, and how to frame it at the end-of-semester presentation.

---

## What the Mentors Are Evaluating

They are not expecting a research breakthrough. They are evaluating:
- Did you understand what you built?
- Can you explain non-trivial technical concepts clearly?
- Did you engage seriously with the limitations, or did you just ignore them?
- Is there a complete, working system?

This project delivers all four. The depth of understanding is the grade, not novelty.

---

## The Core Narrative (Say This First)

> "We built a benchmarking system that compares classical, quantum, and hybrid vector search algorithms side by side. The user selects from predefined ground-truth queries and chooses which engines to run; the system finds matching images using CLIP embeddings. We benchmarked multiple search engines on the same data and measured accuracy and algorithmic cost. The quantum engines run on a real quantum circuit simulator. We found that the quantum algorithms produce correct results but cannot beat classical today, and we documented exactly why."

That framing sets up every follow-up question with a clear answer.

---

## What to Show

### 1. The running system
- Live demo: select a predefined ground-truth query, choose which engines to run, see results side by side
- Show MRR scores and oracle call counts in the UI
- This proves it works end-to-end

### 2. The Oracle Count Scaling chart
This is the most important single output. Show two curves plotted against N:
- Classical: linear (N comparisons)
- Grover: sqrt(N) curve (floor(pi*sqrt(N)/4) oracle calls)

At N = 1,000,000: classical does 1,000,000 comparisons, Grover does 785. The visual divergence is the entire argument for quantum search. You measured this empirically.

### 3. The qRAM explanation
Walk through the two-step problem (loading data vs searching). Explain that Grover's search step works and is verified, but loading data requires qRAM which does not exist. The speedup is real in theory and blocked in practice.

This is where you demonstrate actual understanding. Most people who talk about quantum search do not explain this clearly.

### 4. The honest limitations
- Without qRAM: O(N) loading cancels O(sqrt(N)) search, total is still O(N)
- Even with qRAM: HNSW (the standard production algorithm) achieves O(log N) approximate search, which beats Grover's O(sqrt(N)) exact search
- qRAM hardware would need ~1 billion physical qubits for 1M vectors - not on any credible roadmap

Mentors will respect this honesty. It shows you understand the field, not just your own code.

---

## Likely Questions and How to Answer Them

**"So quantum is useless for search?"**

> "Not useless - Grover's proven speedup is real and one of the few unconditional quantum speedups that hasn't been overturned. It wins for exact search over brute force. But in practice, approximate search algorithms like HNSW already achieve O(log N) classically, which is faster than Grover even with ideal qRAM. And qRAM doesn't exist at practical scale. So: correct in theory, blocked in practice, with a better classical alternative for most use cases."

**"What did you contribute if you didn't discover anything new?"**

> "We implemented Grover's algorithm and the quantum swap test on a real simulator and empirically verified that they behave as theory predicts - that oracle calls follow floor(pi*sqrt(N)/4) across multiple dataset sizes. We built the infrastructure to measure this. We also built a complete production-quality system around it. That's the contribution: engineering plus empirical verification plus honest analysis."

**"Why not use real IBM hardware?"**

> "Our circuits fit the free tier in qubit count, but IBM free tier introduces hours of queue wait and noise that would make results hard to interpret. AerSimulator is mathematically exact - it gives the same statistics as a perfect noiseless chip. The only noise is shot noise, which exists on real hardware too. Real IBM hardware would be a Phase 2 noise-accuracy study, not the core benchmark."

**"Why is the Grover engine slow in your benchmarks?"**

> "That timing reflects how expensive it is to *simulate* quantum circuits on a CPU - the simulator has to track 2^n amplitudes. A real quantum chip processes all amplitudes simultaneously. Quantum engine wall-clock time on a simulator is meaningless, which is why we use oracle call count as the cross-engine comparison, not wall-clock speed."

**"What would you need to make this actually fast?"**

> "Two things. First, working qRAM at scale - roughly a billion physical qubits for a million-vector dataset, using a hardware architecture that doesn't exist yet. Second, at that scale you would still need to beat HNSW's O(log N) approximate performance, which Grover's O(sqrt(N)) does not do. The realistic path is that quantum computing finds its advantage in other domains - chemistry, cryptography - rather than vector search specifically."

---

## What NOT to Say

- Do not claim quantum is faster. It is not, and the mentors will know.
- Do not say "this could be used in production." It cannot without qRAM.
- Do not apologise for not discovering something new. That was never the goal.

---

## One-Paragraph Summary of the Whole Project

> We built a text-to-image search system benchmarking classical, quantum, and hybrid engines on the same CLIP embeddings. The quantum engines implement the swap test and Grover's algorithm on Qiskit's AerSimulator, while the hybrid engine uses classical HNSW candidate retrieval followed by quantum swap-test reranking. We empirically verified that Grover's oracle call count follows the O(sqrt(N)) curve across dataset sizes, that the swap test produces MRR comparable to classical at sufficient shot counts, and measured circuit depth and qubit requirements at each vector dimension. We found that quantum search algorithms are correct and their resource costs match theory, but the O(N) state preparation cost (requiring qRAM which does not exist) prevents end-to-end speedup. Even in the ideal future with working qRAM, the standard classical approximate search algorithm HNSW achieves O(log N) which outperforms Grover's O(sqrt(N)). The project's value is the empirical verification, the complete benchmarking infrastructure, and the honest analysis of exactly where the gap between quantum theory and quantum practice lies.
