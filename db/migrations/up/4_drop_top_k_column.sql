ALTER TABLE benchmark_results
    DROP CONSTRAINT uq_run_key,
    ADD CONSTRAINT uq_run_key UNIQUE (query_id, engine_name, dimension, shots, layers);

ALTER TABLE benchmark_results DROP COLUMN top_k;
