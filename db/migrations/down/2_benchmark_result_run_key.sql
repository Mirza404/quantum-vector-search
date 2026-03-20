ALTER TABLE benchmark_results
    DROP CONSTRAINT uq_run_key;

ALTER TABLE benchmark_results
    DROP COLUMN top_k,
    DROP COLUMN shots,
    DROP COLUMN layers;

ALTER TABLE benchmark_results
    ADD CONSTRAINT uq_run_key UNIQUE (query_id, engine_name, dimension);
