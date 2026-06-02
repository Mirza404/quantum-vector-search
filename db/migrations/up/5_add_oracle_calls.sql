-- Migration 5: Add oracle_calls column to benchmark_results.
-- Tracks the number of oracle invocations per query:
--   Classical engines: N (dataset_size) comparisons
--   Grover engine:     floor(pi*sqrt(N) / 4) oracle calls
-- This is the cross-engine scaling KPI (O(N) vs O(sqrt(N))).

ALTER TABLE benchmark_results
    ADD COLUMN oracle_calls INTEGER;
