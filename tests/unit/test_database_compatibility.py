"""Guards docs/backend/DATABASE_COMPATIBILITY.md's findings: compiles
this project's actual DDL against both the sqlite and postgresql
dialects (no live server needed or used) and asserts they render
identically for every table. This is a regression test for the
native_enum=False fix -- if someone reverts it, this test catches the
reintroduced SQLite/PostgreSQL divergence immediately."""
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable

from backend.app.models.base import Base


def _compiled_ddl(table, dialect):
    # Normalize the two cosmetic, EXPECTED differences (auto-increment PK
    # keyword, and timezone-aware timestamp type) so the comparison is
    # about everything else -- not a claim that literally every token
    # must match. These two are intentionally different (see
    # DATABASE_COMPATIBILITY.md) and are not under test here.
    ddl = str(CreateTable(table).compile(dialect=dialect))
    ddl = ddl.replace("SERIAL", "INTEGER")
    ddl = ddl.replace("TIMESTAMP WITH TIME ZONE", "DATETIME")
    return ddl


def test_every_table_compiles_identically_on_sqlite_and_postgresql_modulo_known_diffs():
    sqlite_dialect = sqlite.dialect()
    pg_dialect = postgresql.dialect()

    mismatches = []
    for table in Base.metadata.sorted_tables:
        sqlite_ddl = _compiled_ddl(table, sqlite_dialect)
        pg_ddl = _compiled_ddl(table, pg_dialect)
        if sqlite_ddl != pg_ddl:
            mismatches.append((table.name, sqlite_ddl, pg_ddl))

    assert mismatches == [], (
        "Found dialect-specific DDL beyond the known SERIAL/TIMESTAMPTZ differences "
        "-- update DATABASE_COMPATIBILITY.md if this is intentional, otherwise it's a "
        "real new SQLite/PostgreSQL divergence to fix:\n" + "\n".join(
            f"{name}:\n--SQLITE--\n{s}\n--POSTGRES--\n{p}" for name, s, p in mismatches
        )
    )


def test_no_native_postgres_enum_types_are_used():
    """A native PG enum type would show up as a bare lowercase type name
    (e.g. 'stancelabel') instead of VARCHAR(n) in the compiled column
    list -- this is the literal regression native_enum=False prevents."""
    pg_dialect = postgresql.dialect()
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=pg_dialect))
        for column in table.columns:
            if column.type.__class__.__name__ == "Enum" or getattr(column.type, "enums", None):
                col_line = next(l for l in ddl.splitlines() if l.strip().startswith(column.name + " "))
                assert "VARCHAR" in col_line, (
                    f"{table.name}.{column.name} appears to use a native PostgreSQL enum type: "
                    f"{col_line.strip()}"
                )
