CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS schema_migrations (
    filename   TEXT        PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS benchmark_results (
    id            BIGSERIAL        PRIMARY KEY,
    recorded_at   TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    query_id      TEXT             NOT NULL,
    engine_name   TEXT             NOT NULL,
    dimension     INTEGER          NOT NULL,
    target_ids    JSONB            NOT NULL,
    top_ids       JSONB            NOT NULL,
    accuracy      DOUBLE PRECISION NOT NULL,
    state_prep_ms DOUBLE PRECISION,
    search_ms     DOUBLE PRECISION NOT NULL,
    total_ms      DOUBLE PRECISION NOT NULL,
    parameters    JSONB            NOT NULL DEFAULT '{}'::jsonb,
    dataset_size  INTEGER          NOT NULL DEFAULT 0,
    circuit_depth INTEGER,
    num_qubits    INTEGER,
    CONSTRAINT uq_run_key UNIQUE (query_id, engine_name, dimension)
);

CREATE TABLE IF NOT EXISTS image_vectors (
    id          TEXT        PRIMARY KEY,
    embedding   vector(512),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS image_vectors_embedding_idx
    ON image_vectors USING hnsw (embedding vector_cosine_ops);
