"""In-memory lookup of models, rebuilt from the database at startup."""
from core.database import db_cursor
from core.model import Model, ensure_meta_table

_registry = {}


def register_model(model):
    _registry[model.table] = model
    return model


def unregister_model(table):
    _registry.pop(table, None)


def get_model(table):
    return _registry.get(table)


def all_models():
    return _registry


def load_models():
    """Rebuild a Model for every previously imported table."""
    with db_cursor() as cur:
        ensure_meta_table(cur)
        cur.execute("SELECT table_name, column_name, label, type FROM _columns ORDER BY rowid")
        rows = cur.fetchall()

    tables = {}
    for r in rows:
        t = tables.setdefault(r["table_name"], ({}, {}))
        t[0][r["column_name"]] = r["type"]
        t[1][r["column_name"]] = r["label"]

    _registry.clear()
    for name, (fields, labels) in tables.items():
        register_model(Model(name, fields, labels))