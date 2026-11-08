import csv
import sqlite3
import pandas as pd
from pathlib import Path

def import_csv(db_path, csv_path):
	table = Path(csv_path).stem.replace("-", "_").replace(" ", "_")

	with open(csv_path, newline="", encoding="utf-8") as f:
		reader = csv.reader(f)
		headers = next(reader)
		cols = [h.strip().replace(" ", "_") for h in headers]

		conn = sqlite3.connect(db_path)
		cur = conn.cursor()

		col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
		cur.execute(f'CREATE TABLE IF NOT EXISTS "{table}" '
					f'(id INTEGER PRIMARY KEY AUTOINCREMENT, {col_defs})')

		placeholders = ", ".join("?" for _ in cols)
		col_names = ", ".join(f'"{c}"' for c in cols)
		cur.executemany(
			f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders})', reader,
		)

		conn.commit()
		print(f"Imported {cur.rowcount} rows into '{table}'")
		conn.close()

import_csv("my_database.db", "customer.csv")

conn = sqlite3.connect("my_database.db")	
for row in conn.execute("SELECT * FROM customer LIMIT 5"):
	print(row)
conn.close()

df = pd.read_csv("customer.csv")

conn = sqlite3.connect("my_database.db")
df.to_sql("customer", conn, if_exists = "replace", index = False)

for row in conn.execute("SELECT * FROM customer LIMIT 5"):
	print(row)
conn.close()
