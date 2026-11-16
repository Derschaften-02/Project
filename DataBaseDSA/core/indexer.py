"""'Index' = load a table's rows into memory so searchcode can scan them quickly.

Reports real progress (0-100) through `progress`, so the progress bar tracks the
actual work. If Zahis_Index replaces this, keep the same shape:
    def my_index(model, progress) -> anything   # call progress(0..100) as you go
and change the one line in ui/app.py that calls load_rows().
"""
from core.database import db_cursor, q

CHUNK = 2000


def load_rows(model, progress=lambda pct: None):
    total = model.count() or 1
    rows, offset = [], 0
    while True:
        with db_cursor() as cur:
            cur.execute(f"SELECT * FROM {q(model.table)} ORDER BY id LIMIT ? OFFSET ?",
                        (CHUNK, offset))
            chunk = [dict(r) for r in cur.fetchall()]
        if not chunk:
            break
        rows.extend(chunk)
        offset += len(chunk)
        progress(min(100, offset * 100 // total))
    progress(100)
    return rows
