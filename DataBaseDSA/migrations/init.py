from core.database import db_cursor
from core.model import ensure_meta_table
from core.registry import load_models


def migrate():
    """Make sure the schema-tracking table exists, then reload imported tables."""
    with db_cursor() as cur:
        ensure_meta_table(cur)
    load_models()