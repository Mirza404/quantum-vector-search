"""Generate the poster's data figures into poster/figures/.

* ``mrr_chart.png`` -- horizontal bar chart of average MRR per engine, coloured
  by category (classical blue, quantum purple, hybrid green), matching the
  frontend palette. Values are the per-engine averages from
  ``backend/reports/benchmark_report.md`` (the source of truth).
* ``qr_repo.png`` -- QR code linking to the public repository.

It also copies ``oracle_scaling.png`` from the report figures. The methodology
diagram is rendered separately from ``methodology_standalone.tex`` (see the build
comment in that file).

Run with the project virtualenv:

    backend/.venv/bin/python poster/make_poster_assets.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import qrcode  # noqa: E402

HERE = Path(__file__).resolve().parent
FIGURES = HERE / "figures"
REPO_URL = "https://github.com/Mirza404/quantum-vector-search"

# (label, average MRR, category) from backend/reports/benchmark_report.md.
ENGINES = [
    ("Brute-force cosine", 0.829, "classical"),
    ("FAISS flat", 0.829, "classical"),
    ("FAISS HNSW", 0.829, "classical"),
    ("Hybrid (HNSW + swap test)", 0.823, "hybrid"),
    ("Grover (hardcoded oracle)", 0.759, "quantum"),
    ("Swap test", 0.728, "quantum"),
    ("Grover (quantum state prep)", 0.559, "quantum"),
]

COLOR = {"classical": "#1e40af", "quantum": "#7c3aed", "hybrid": "#16a34a"}


def make_mrr_chart(path: Path) -> None:
    rows = sorted(ENGINES, key=lambda r: r[1])  # ascending so largest is on top
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]
    colors = [COLOR[r[2]] for r in rows]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(labels, values, color=colors)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Average Mean Reciprocal Rank (higher is better)", fontsize=13)
    ax.tick_params(axis="y", labelsize=12)
    ax.tick_params(axis="x", labelsize=11)
    for bar, value in zip(bars, values):
        ax.text(value + 0.012, bar.get_y() + bar.get_height() / 2,
                f"{value:.3f}", va="center", fontsize=11)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in
               (COLOR["classical"], COLOR["quantum"], COLOR["hybrid"])]
    ax.legend(handles, ["Classical", "Quantum", "Hybrid"],
              loc="lower right", fontsize=11, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_qr(path: Path) -> None:
    qr = qrcode.QRCode(box_size=10, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(REPO_URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="white")
    img.save(path)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    make_mrr_chart(FIGURES / "mrr_chart.png")
    make_qr(FIGURES / "qr_repo.png")
    report_oracle = HERE.parent / "report" / "figures" / "oracle_scaling.png"
    if report_oracle.exists():
        shutil.copyfile(report_oracle, FIGURES / "oracle_scaling.png")
    print(f"Wrote poster assets to {FIGURES}")


if __name__ == "__main__":
    main()
