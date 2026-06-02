import { useState } from 'react'

/**
 * Collapsible glossary panel. Same wording as the report's Methodology
 * chapter so the live UI and the document agree on what each KPI means.
 */
export default function MetricsLegend() {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold text-slate-700 hover:text-slate-900"
        aria-expanded={open}
      >
        <span>About these metrics</span>
        <span className="text-slate-400">{open ? '-' : '+'}</span>
      </button>
      {open && (
        <dl className="space-y-3 border-t border-slate-200 px-4 py-3 text-sm text-slate-600">
          <div>
            <dt className="font-semibold text-slate-800">MRR (Mean Reciprocal Rank)</dt>
            <dd>
              Average of 1 / (rank of the first relevant result) across queries.
              Higher is better; 1.0 means the correct image was first every time.
              Computed over the top 10 results - if the truth is outside the top 10, that query contributes 0.
            </dd>
          </div>
          <div>
            <dt className="font-semibold text-slate-800">Search ms vs. state-prep ms</dt>
            <dd>
              <strong>Search ms</strong> is the time spent on the actual similarity step
              (one classical pass for FAISS / brute force, or one round of circuit executions for quantum engines).
              <strong> State-prep ms</strong> is the extra time quantum engines spend encoding vectors into a
              quantum state before they can run. Classical engines have no state-prep step, so it's <code>-</code> for them.
              <strong> Total ms = state-prep + search.</strong> All timings come from a CPU simulator and are
              not comparable to real quantum hardware.
            </dd>
          </div>
          <div>
            <dt className="font-semibold text-slate-800">Scaling</dt>
            <dd>
              Algorithmic comparisons per query (e.g. O(N) for brute force, O(sqrt(N)) oracle calls for Grover).
              This is the only fair cross-engine measure of cost. Wall-clock time on a simulator reflects
              CPU overhead, not the quantum algorithm.
            </dd>
          </div>
          <div>
            <dt className="font-semibold text-slate-800">Circuit depth &amp; qubits</dt>
            <dd>
              Hardware-cost proxies for the quantum engines. Circuit depth is the longest path through the
              gate graph; qubits is the total register width including the swap-test ancilla.
            </dd>
          </div>
        </dl>
      )}
    </div>
  )
}
