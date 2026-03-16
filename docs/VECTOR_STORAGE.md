# Vector Storage Plan

## Why we need it

The React dashboard will let users type a query and search the image dataset in real time.
That requires CLIP embeddings for all dataset images to be stored persistently and queryable
without rebuilding the index on every request.

Currently the benchmark harness re-encodes and re-indexes vectors in memory on every run —
fine for experiments, not viable for a live search endpoint.

## Chosen solution: pgvector

pgvector is a Postgres extension that adds a `vector` column type and nearest-neighbour
operators (`<->`, `<#>`, `<=>`) directly to SQL queries.

**Why pgvector over a standalone vector DB:**
- Already running Postgres — no new infrastructure
- Same DSN, same Docker Compose file, same backup/dump workflow
- Sufficient for our dataset size

## What needs to change

1. **`db/docker-compose.yml`** — swap `postgres:16` image for `pgvector/pgvector:pg16`
   (a drop-in replacement that includes the extension)

2. **`db/schema.sql`** — enable the extension and add an `image_vectors` table:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;

   CREATE TABLE image_vectors (
       id          TEXT PRIMARY KEY,
       embedding   vector(512),   -- CLIP ViT-B/32 output dimension
       recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
   );

   CREATE INDEX ON image_vectors USING hnsw (embedding vector_cosine_ops);
   ```

3. **New backend script** `scripts/index_dataset.py` — encode all dataset images with CLIP
   and upsert their embeddings into `image_vectors`. Run once after `schema.sql`.

4. **FastAPI endpoint** `GET /search?q=<text>` — encode the query text with CLIP, run a
   cosine nearest-neighbour query against `image_vectors`, return the top-K image IDs.

## Order of implementation

1. Swap the Docker image and re-init the schema
2. Write and run `index_dataset.py`
3. Build the FastAPI search endpoint
4. Wire the React search box to the endpoint
