# Database Migration Guide

Alembic (already installed; nothing new added) is configured at the repo
root (`alembic.ini`) with scripts under `backend/migrations/`. Migrations
always run against whatever `DATABASE_URL` the app itself would use —
`backend/migrations/env.py` reads it from
`backend.app.config.get_settings()`, the same function `backend/app/
database.py` uses, so there is exactly one source of truth for "which
database" regardless of whether you're running the app or a migration.

## Commands (run from the repo root)

```
# Apply all migrations up to the latest
alembic upgrade head

# Roll back the most recent migration
alembic downgrade -1

# Roll back everything (drops all tables)
alembic downgrade base

# See the current revision
alembic current

# See full history
alembic history

# Generate a new migration after changing a model in backend/app/models/
alembic revision --autogenerate -m "describe the change"
```

To target a non-default database, set `DATABASE_URL` first:
```
DATABASE_URL=postgresql://user:pass@localhost:5432/policylens alembic upgrade head
```

## Current migration

`91d0b35d3fb2_initial_schema.py` — creates all 12 tables from
`docs/backend/DATABASE_SCHEMA.md`. No prior schema exists yet in any real
deployment, so this is a clean baseline, not a migration of pre-existing
data.

## Verified upgrade/downgrade/data-preservation behavior

This exact sequence was run against SQLite during development (not a
one-time claim — reproducible with the commands above):

1. `alembic upgrade head` against a fresh database — succeeds, creates
   all 12 tables.
2. Inserted a `PolicyDocument` row via the ORM, with other data (a
   `Comment`, `CommentSourceMetadata`, a `StancePrediction`) attached —
   all constraints (mutual exclusivity, model-version requirement,
   dedup uniqueness) enforced correctly against the migrated schema, not
   just against tables created directly by `Base.metadata.create_all()`.
3. `alembic downgrade base` — drops every table cleanly; only
   `alembic_version` remains.
4. `alembic upgrade head` again — re-creates everything from scratch
   without error (confirms the migration is safely re-runnable).

**A second, additive migration** (adding a nullable `description` column
to `PolicyDocument`) was also generated and tested in isolation during
development to specifically verify **data preservation across a
non-destructive schema change**: a row inserted before the column existed
retained its other fields (`title`, `jurisdiction`) unchanged after
upgrading to add the column, and after downgrading to remove it again.
That throwaway migration was not kept in the shipped history (it existed
only to prove the mechanism), but the same pattern applies to any future
additive migration generated the normal way with `--autogenerate`.

## PostgreSQL

Not live-tested — no PostgreSQL server was available in this development
environment (see `docs/backend/DATABASE_COMPATIBILITY.md` for exactly
what was and wasn't verified, and how to complete live verification once
a server is available). The `psycopg2` driver is already installed.
Every type used in this schema was confirmed, by direct dialect
compilation, to render the same portable SQL on both dialects (after
fixing one real divergence — see `DATABASE_COMPATIBILITY.md` — native
PostgreSQL enum types were being generated where SQLite used plain
`VARCHAR`; both now use `VARCHAR` + `CHECK`).

## Preserving existing records

- Migrations never run `DROP TABLE` / `DROP COLUMN` except as an explicit
  `downgrade()` step for a column/table that migration itself added — a
  downgrade past the point where a table was introduced is the only way
  its data is removed, exactly as expected for any migration tool.
- No migration in this history alters or drops `original_text` or any
  other column this project treats as immutable.
- `init_db()` (`backend/app/database.py`) still calls
  `Base.metadata.create_all()` directly for convenience in tests and
  fresh local setups — this is additive-only (`create_all` never drops
  or alters an existing table) and is safe to run alongside Alembic; it
  does not replace the migration history for a database that already has
  data in it.

## Not yet done (known next step)

- No migration has been generated or tested that *alters* an existing
  column's type or constraints (only "create all" and "add a nullable
  column" have been exercised) — a genuinely destructive or
  type-changing migration (e.g. shrinking a `VARCHAR` length) would need
  its own careful review before being trusted on real data, and SQLite in
  particular requires Alembic's "batch mode" (`op.batch_alter_table(...)`)
  for several column-alteration operations it can't do with a plain
  `ALTER TABLE`. This hasn't come up yet because no such migration has
  been needed.
