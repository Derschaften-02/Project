import csv
from pathlib import Path
from core.model import Model
from core.registry import register_model, all_models


# ----------------------------
# CSV Reading
# ----------------------------
def read_csv(file_path):
    """Read CSV file and return list of rows and fieldnames."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]

    return data, reader.fieldnames


# ----------------------------
# Type Inference (multi-row)
# ----------------------------
def infer_column_type(values):
    """
    Infer SQLite column type from multiple sample values.
    INTEGER > REAL > TEXT
    """
    is_int = True
    is_float = True

    for v in values:
        if v is None or v == "":
            continue

        try:
            int(v)
        except:
            is_int = False

        try:
            float(v)
        except:
            is_float = False

    if is_int:
        return "INTEGER"
    if is_float:
        return "REAL"
    return "TEXT"


# ----------------------------
# Safe Dynamic Model Creation
# ----------------------------
def create_csv_model(model_name, fieldnames, sample_rows):
    """
    Create a dynamic Model class from CSV headers,
    safely register it, and create the database table.
    """

    existing = all_models()

    base_name = model_name.lower()
    final_name = base_name
    counter = 1

    # Prevent collisions
    while final_name in existing:
        final_name = f"{base_name}_{counter}"
        counter += 1

    fields = {}

    for name in fieldnames:
        column_values = [row.get(name) for row in sample_rows]
        fields[name] = infer_column_type(column_values)

    model_class = type(final_name.capitalize(), (Model,), {
        "table": final_name,
        "fields": fields
    })

    register_model(model_class)
    model_class.create_table()

    return model_class


# ----------------------------
# Import CSV into DB
# ----------------------------
def import_csv_to_model(file_path, model_name="ImportedTable"):
    """
    Read a CSV file and import it into a dynamically created model.
    """

    data, headers = read_csv(file_path)
    sample_rows = data[:10] if data else []

    # Create and register dynamic model
    model_class = create_csv_model(model_name, headers, sample_rows)

    # Insert all rows
    for row in data:
        prepared = {}

        for k, v in row.items():
            field_type = model_class.fields.get(k, "TEXT")

            if field_type == "INTEGER":
                try:
                    prepared[k] = int(v) if v != "" else 0
                except:
                    prepared[k] = 0

            elif field_type == "REAL":
                try:
                    prepared[k] = float(v) if v != "" else 0.0
                except:
                    prepared[k] = 0.0

            else:
                prepared[k] = v

        model_class.create(**prepared)

    return model_class


# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    seating_model = import_csv_to_model("seating.csv", "SeatingCSV")

    print("Registered models:", list(all_models().keys()))
    print("Imported rows:", len(seating_model.all()))