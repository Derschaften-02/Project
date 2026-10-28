# --- force model imports ---
from core.registry import all_models
from core.database import db_cursor


def migrate():
    """
    Initialize the database:
    - Create core tables (users)
    - Create all registered model tables (static + dynamic)
    """

    # 1. Core users table (always exists)
    with db_cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','guest'))
        )
        """)

    # 2. Create all registered models
    for model in all_models().values():
        try:
            model.create_table()
        except Exception as e:
            print(f"[MIGRATION WARNING] {model.table}: {e}")