CREATE TABLE IF NOT EXISTS benchmark_results (
    id           BIGSERIAL PRIMARY KEY,
    recorded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    query_id     TEXT        NOT NULL,
    engine_name  TEXT        NOT NULL,
    dimension    INTEGER     NOT NULL,
    target_id    TEXT        NOT NULL,
    top_ids      JSONB       NOT NULL,
    accuracy     DOUBLE PRECISION NOT NULL,
    state_prep_ms DOUBLE PRECISION,
    search_ms    DOUBLE PRECISION NOT NULL,
    total_ms     DOUBLE PRECISION NOT NULL,
    parameters   JSONB       NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (query_id, engine_name, dimension)
);

CREATE INDEX IF NOT EXISTS idx_benchmark_results_query
    ON benchmark_results (query_id, engine_name);

CREATE INDEX IF NOT EXISTS idx_benchmark_results_recorded_at
    ON benchmark_results (recorded_at DESC);
