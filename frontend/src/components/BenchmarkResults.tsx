export default function BenchmarkResults() {
  const benchmarkData = [
    {
      engine: 'Classical',
      mrr: 0.85,
      avgSearchTime: 12.5,
      circuitDepth: 0,
      qubits: 0,
    },
    {
      engine: 'Quantum',
      mrr: 0.92,
      avgSearchTime: 18.3,
      circuitDepth: 42,
      qubits: 12,
    },
  ]

  return (
    <section className="space-y-6">
      <div className="text-center">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Comparison</p>
        <h2 className="text-3xl font-semibold text-slate-900">Benchmark Results</h2>
        <p className="mt-2 text-base text-slate-500">Classical vs. Quantum engine comparison</p>
      </div>

      <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-card">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="px-4 py-3 text-left font-semibold text-slate-900">Engine</th>
                <th className="px-4 py-3 text-right font-semibold text-slate-900">MRR</th>
                <th className="px-4 py-3 text-right font-semibold text-slate-900">
                  Avg Search Time (ms)
                </th>
                <th className="px-4 py-3 text-right font-semibold text-slate-900">
                  Circuit Depth
                </th>
                <th className="px-4 py-3 text-right font-semibold text-slate-900">Qubits</th>
              </tr>
            </thead>
            <tbody>
              {benchmarkData.map((row) => (
                <tr key={row.engine} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-900 font-medium">{row.engine}</td>
                  <td className="px-4 py-3 text-right text-slate-600">{row.mrr.toFixed(3)}</td>
                  <td className="px-4 py-3 text-right text-slate-600">{row.avgSearchTime.toFixed(1)}</td>
                  <td className="px-4 py-3 text-right text-slate-600">{row.circuitDepth}</td>
                  <td className="px-4 py-3 text-right text-slate-600">{row.qubits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
