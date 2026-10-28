from core.database import db_cursor


class Model:
    table = ""
    fields = {}  # {"name": "TEXT", "age": "INTEGER"}

    # --------------------
    # TABLE SETUP
    # --------------------
    @classmethod
    def create_table(cls):
        if not cls.table or not cls.fields:
            raise ValueError(f"Invalid model definition for {cls.__name__}")

        cols = []
        for name, spec in cls.fields.items():
            cols.append(f"{name} {spec}")

        sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {", ".join(cols)}
        )
        """

        with db_cursor() as cur:
            cur.execute(sql)

        print(f"[DB] table ready: {cls.table}")

    # --------------------
    # INSERT
    # --------------------
    @classmethod
    def create(cls, **kwargs):
        if not kwargs:
            raise ValueError("create() called with no data")

        # validate fields
        for key in kwargs:
            if key not in cls.fields:
                raise ValueError(
                    f"Unknown field '{key}' for table '{cls.table}'"
                )

        keys = ", ".join(kwargs.keys())
        placeholders = ", ".join("?" for _ in kwargs)
        values = tuple(kwargs.values())

        with db_cursor() as cur:
            cur.execute(
                f"INSERT INTO {cls.table} ({keys}) VALUES ({placeholders})",
                values
            )
            row_id = cur.lastrowid

        print(f"[DB] INSERT {cls.table} id={row_id} data={kwargs}")
        return row_id

    # --------------------
    # QUERY
    # --------------------
    @classmethod
    def all(cls):
        with db_cursor() as cur:
            cur.execute(f"SELECT * FROM {cls.table}")
            rows = cur.fetchall()
            return [dict(row) for row in rows]
