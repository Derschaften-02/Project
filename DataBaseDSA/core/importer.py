"""Import a data file into a brand-new table, inferring columns and types."""
import csv
import math
import re
from pathlib import Path

from core.database import safe_name, table_exists
from core.model import Model
from core.registry import register_model

_INT = re.compile(r"-?(0|[1-9]\d*)")  # "007" is NOT an int: keep it as text


# ---------- reading (add new formats here) ----------
def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:  # utf-8-sig strips Excel's BOM
        reader = csv.reader(f)  # by position, so duplicate headers can't overwrite each other
        headers = next(reader, [])
        return list(reader), headers


READERS = {".csv": read_csv}


# ---------- schema inference ----------
def infer_type(values):
    """INTEGER > REAL > TEXT, judged on every non-empty value."""
    vals = [v.strip() for v in values if v is not None and v.strip() != ""]
    if not vals:
        return "TEXT"
    if all(_INT.fullmatch(v) for v in vals):
        return "INTEGER"
    if all(_is_float(v) for v in vals):
        return "REAL"
    return "TEXT"


def _is_float(v):
    if re.fullmatch(r"-?0\d+", v):  # "00123" is an ID/zip, not a number
        return False
    try:
        return math.isfinite(float(v))
    except ValueError:
        return False


def convert(value, col_type):
    """Empty cells become NULL (not 0), so 'missing' stays distinguishable."""
    if value is None or value.strip() == "":
        return None
    if col_type == "INTEGER":
        return int(value)
    if col_type == "REAL":
        return float(value)
    return value


def make_columns(headers):
    """[(original_header, unique_safe_name)] - 'id' is reserved for the primary key."""
    used, cols = {"id"}, []
    for i, h in enumerate(headers, 1):
        base = safe_name(h, f"col{i}")
        name, n = base, 1
        while name in used:
            n += 1
            name = f"{base}_{n}"
        used.add(name)
        cols.append((h, name))
    return cols


def unique_table_name(name):
    base = safe_name(name, "imported")
    final, n = base, 1
    while table_exists(final) or final.startswith("sqlite_") or final.startswith("_"):
        n += 1
        final = f"{base}_{n}"
    return final


# ---------- main entry point ----------
def import_file(path, name=None):
    """Create a table from the file, insert every row, register and return the Model."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    reader = READERS.get(path.suffix.lower())
    if not reader:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    rows, headers = reader(path)
    if not headers:
        raise ValueError("File has no header row")

    cols = make_columns(headers)
    def cell(row, i):
        return row[i] if i < len(row) else None  # short rows -> NULL

    fields = {safe: infer_type([cell(r, i) for r in rows]) for i, (_, safe) in enumerate(cols)}
    labels = {safe: orig for orig, safe in cols}

    model = Model(unique_table_name(name or path.stem), fields, labels)
    model.save()
    try:
        model.insert_many([{safe: convert(cell(r, i), fields[safe]) for i, (_, safe) in enumerate(cols)}
                           for r in rows])
    except Exception:
        model.drop()  # don't leave a half-built table behind
        raise
    return register_model(model)