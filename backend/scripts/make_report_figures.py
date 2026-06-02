"""Generate the diagram-as-code figures used in the graduation report.

Produces three PNGs into ``report/figures/``:

* ``oracle_scaling.png`` -- the theoretical Grover oracle-call curve
  ``floor((pi/4) sqrt(N))`` with the single padded index size we benchmarked
  (N = 32) marked. We ran one dataset size, so this confirms the count at one
  point on the curve rather than tracing it empirically.
* ``swap_test_circuit.png`` -- a representative swap-test circuit, built with the
  same construction as ``QiskitSwapTestEngine._run_swap_test`` (here for a
  4-dimensional vector, i.e. two qubits per register plus one ancilla).
* ``grover_circuit.png`` -- one Grover iteration for N = 4 (two index qubits),
  built from the engine's own oracle and diffusion operators, with barriers
  separating the phases.

Run from the ``backend`` directory with the project virtualenv:

    .venv/bin/python scripts/make_report_figures.py

The figures are committed to the repository so the report builds without this
script, but anyone can re-run it to regenerate them.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from qiskit import QuantumCircuit  # noqa: E402

SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from engines.qiskit_grover import QiskitGroverEngine  # noqa: E402

FIGURES_DIR = Path(__file__).resolve().parent.parent.parent / "report" / "figures"

# Palette aligned with the frontend (classical blue, quantum purple).
QUANTUM = "#7C3AED"
CLASSICAL = "#2563EB"


def make_oracle_scaling(path: Path) -> None:
    """Theoretical Grover oracle-call curve with our one verified point marked."""
    n = np.linspace(2, 256, 512)
    theoretical = (math.pi / 4) * np.sqrt(n)

    # Powers of two are the index sizes Grover actually addresses.
    pow2 = np.array([2, 4, 8, 16, 32, 64, 128, 256])
    floored = np.floor((math.pi / 4) * np.sqrt(pow2)).astype(int)

    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    ax.plot(n, theoretical, color=QUANTUM, lw=1.8,
            label=r"$(\pi/4)\sqrt{N}$")
    ax.step(pow2, floored, where="mid", color=QUANTUM, alpha=0.35, lw=1.2,
            label=r"$\lfloor (\pi/4)\sqrt{N} \rfloor$")
    ax.scatter(pow2, floored, color=QUANTUM, alpha=0.5, s=22, zorder=3)

    # Our verified point: N = 32 (20 images padded to a power of two), 4 calls.
    ax.scatter([32], [4], color=CLASSICAL, s=80, zorder=5,
               label="Benchmarked: $N=32$, 4 calls")
    ax.annotate("20 images\npadded to $N=32$",
                xy=(32, 4), xytext=(70, 2.3),
                fontsize=9, color=CLASSICAL,
                arrowprops=dict(arrowstyle="->", color=CLASSICAL, lw=1.0))

    ax.set_xlabel("Padded index size $N$")
    ax.set_ylabel("Oracle calls per query")
    ax.set_xlim(0, 260)
    ax.set_ylim(0, 11)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_swap_test_circuit(path: Path) -> None:
    """Representative swap-test circuit (4-dim vectors: two qubits per register).

    Mirrors ``QiskitSwapTestEngine._run_swap_test``: one ancilla, two amplitude
    -encoded registers, controlled swaps, and a Hadamard test on the ancilla.
    """
    num_qubits = 2  # log2(dimension); dimension = 4 here for a readable figure.
    query = [1.0, 0.0, 0.0, 0.0]
    data = (np.ones(4) / 2.0).tolist()

    circuit = QuantumCircuit(1 + 2 * num_qubits, 1)
    ancilla = 0
    left = list(range(1, 1 + num_qubits))
    right = list(range(1 + num_qubits, 1 + 2 * num_qubits))
    circuit.h(ancilla)
    circuit.initialize(query, left)
    circuit.initialize(data, right)
    for ql, qr in zip(left, right):
        circuit.cswap(ancilla, ql, qr)
    circuit.h(ancilla)
    circuit.measure(ancilla, 0)

    fig = circuit.draw("mpl", fold=-1, scale=0.9)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_grover_circuit(path: Path) -> None:
    """One Grover iteration for N = 4, using the engine's oracle and diffusion."""
    n_qubits = 2          # N = 4 search space.
    target = 2            # marked basis state |10>.

    circuit = QuantumCircuit(n_qubits, n_qubits)
    circuit.h(range(n_qubits))
    circuit.barrier(label="prepare")
    QiskitGroverEngine._apply_oracle(circuit, n_qubits, target)
    circuit.barrier(label="oracle")
    QiskitGroverEngine._apply_diffusion(circuit, n_qubits)
    circuit.barrier(label="diffusion")
    circuit.measure(range(n_qubits), range(n_qubits))

    fig = circuit.draw("mpl", fold=-1, scale=0.9)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    make_oracle_scaling(FIGURES_DIR / "oracle_scaling.png")
    make_swap_test_circuit(FIGURES_DIR / "swap_test_circuit.png")
    make_grover_circuit(FIGURES_DIR / "grover_circuit.png")
    print(f"Wrote 3 figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
