"""One Model instance = one table. Works for any schema, built at runtime."""
from core.database import db_cursor, q


def ensure_meta_table(cur):
    """Remembers each imported table's columns so they survive restarts."""
    cur.execute("""
    CREATE TABLE IF NOT EXISTS _columns (
        table_name  TEXT NOT NULL,
        column_name TEXT NOT NULL,
        label       TEXT NOT NULL,   -- original CSV header, for display
        type        TEXT NOT NULL,
        PRIMARY KEY (table_name, column_name)
    )""")


class Model:
    def __init__(self, table, fields, labels=None):
        self.table = table
        self.fields = dict(fields)                      # {"age": "INTEGER"}
        self.labels = labels or {c: c for c in fields}  # {"age": "Age (years)"}

    # ----- schema -----
    def save(self):
        """Create the table and record its schema."""
        cols = ", ".join(f"{q(n)} {t}" for n, t in self.fields.items())
        with db_cursor() as cur:
            ensure_meta_table(cur)
            cur.execute(f"CREATE TABLE IF NOT EXISTS {q(self.table)} "
                        f"(id INTEGER PRIMARY KEY AUTOINCREMENT, {cols})")
            cur.execute("DELETE FROM _columns WHERE table_name=?", (self.table,))
            cur.executemany("INSERT INTO _columns VALUES (?, ?, ?, ?)",
                            [(self.table, n, self.labels.get(n, n), t) for n, t in self.fields.items()])

    def drop(self):
        with db_cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {q(self.table)}")
            cur.execute("DELETE FROM _columns WHERE table_name=?", (self.table,))

    # ----- write -----
    def insert_many(self, rows):
        """rows: list of dicts keyed by column name. One transaction."""
        cols = list(self.fields)
        sql = (f"INSERT INTO {q(self.table)} ({', '.join(map(q, cols))}) "
               f"VALUES ({', '.join('?' * len(cols))})")
        with db_cursor() as cur:
            cur.executemany(sql, [tuple(r.get(c) for c in cols) for r in rows])

    def create(self, **data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise ValueError(f"Unknown field(s) {sorted(unknown)} for table '{self.table}'")
        self.insert_many([data])

    # ----- read -----
    def all(self, limit=None):
        with db_cursor() as cur:
            cur.execute(f"SELECT * FROM {q(self.table)} LIMIT ?", (-1 if limit is None else limit,))
            return [dict(r) for r in cur.fetchall()]

    def count(self):
        with db_cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {q(self.table)}")
            return cur.fetchone()[0]

    def search(self, keyword, columns=None, limit=500):
        """Case-insensitive 'contains' match across all (or the given) columns."""
        cols = [c for c in (columns or self.fields) if c in self.fields]
        where = " OR ".join(f"CAST({q(c)} AS TEXT) LIKE ?" for c in cols)
        with db_cursor() as cur:
            cur.execute(f"SELECT * FROM {q(self.table)} WHERE {where} LIMIT ?",
                        [f"%{keyword}%"] * len(cols) + [limit])
            return [dict(r) for r in cur.fetchall()]