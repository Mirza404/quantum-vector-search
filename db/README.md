# Database

PostgreSQL + pgvector database for image embeddings and benchmark results. Start it before running backend scripts or the API.

## Setup

```bash
cd db
cp .env.example .env
make up
make migrate
make seed
```

`make up` starts the `qvs-postgres` container on host port `6432` and Adminer on `8080`. `make migrate` applies all pending migrations. `make seed` loads `seeds/seed.sql`, then applies any migrations that are newer than the seed.

## Common Commands

```bash
make up        # start Postgres and Adminer
make down      # stop containers, keep the volume
make migrate   # apply pending up migrations
make seed      # reset table data to seeds/seed.sql
make dump      # write current table data to seeds/seed.sql
make clean     # truncate data tables, keep schema_migrations
make reset     # remove the volume, migrate, then seed
```

Rollback is explicit:

```bash
make rollback N=2
```

That rolls back migrations above migration number 2 by using `migrations/down/`.

## Adminer

After `make up`, open `http://localhost:8080`.

Use:

```text
Server: postgres
Database: qvs_benchmarks
Username: qvs
Password: qvs
```

These defaults come from `.env.example`; use the values in `.env` if you changed them.
