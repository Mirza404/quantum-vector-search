ALTER TABLE benchmark_results
    ADD COLUMN top_k   INTEGER NOT NULL DEFAULT 3,
    ADD COLUMN shots   INTEGER NOT NULL DEFAULT -1,
    ADD COLUMN layers  INTEGER NOT NULL DEFAULT -1;

ALTER TABLE benchmark_results
    DROP CONSTRAINT uq_run_key,
    ADD CONSTRAINT uq_run_key UNIQUE (query_id, engine_name, dimension, top_k, shots, layers);
