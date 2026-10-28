import csv
import pygame
from pathlib import Path
from core.model import Model
from core.registry import register_model, all_models

# ----------------------------
# CSV Reading
# ----------------------------
def read_csv(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]
    return data, reader.fieldnames


# ----------------------------
# Type Inference (multi-row)
# ----------------------------
def infer_column_type(values):
    """
    Infer SQLite type from multiple sample values.
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
# Dynamic Model Creation
# ----------------------------
def create_csv_model(model_name, fieldnames, sample_rows):
    existing = all_models()

    base_name = model_name.lower()
    final_name = base_name
    counter = 1

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
# Import CSV
# ----------------------------
def import_csv_to_model(file_path, model_name="ImportedTable", ui=None):
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    data, headers = read_csv(file_path)
    
    #remove id headers
    headers = [h for h in headers if h.lower() != "id"]
    for row in data:
        if "id" in row:
            del row["id"]
    
    sample_rows = data[:10] if data else []

    model_class = create_csv_model(model_name, headers, sample_rows)

    for row in data:
        prepared = {}
        for k, v in row.items():
            if k in model_class.fields:
                field_type = model_class.fields[k]

                if field_type == "INTEGER":
                    try:
                        prepared[k] = int(v)
                    except:
                        prepared[k] = 0

                elif field_type == "REAL":
                    try:
                        prepared[k] = float(v)
                    except:
                        prepared[k] = 0.0

                else:
                    prepared[k] = v

        model_class.create(**prepared)

    # Refresh UI dynamically
    if ui:
        if hasattr(ui, "load_models"):
            ui.load_models()
        ui.current = model_class
        if hasattr(ui, "log"):
            ui.log(f"Model '{model_name}' importeda nd set as current")

    return model_class


# ----------------------------
# UI Importer Panel
# ----------------------------
class Importer:
    def __init__(self, ui=None, rect=(100, 100, 400, 200)):
        self.ui = ui
        self.rect = pygame.Rect(rect)
        self.active = False
        self.done = False
        self.selected_path = None
        self.font = pygame.font.SysFont(None, 24)
        self.buffer = ""
        self.error = None

    def open(self):
        self.active = True
        self.done = False
        self.buffer = ""
        self.error = None
        pygame.key.start_text_input()

    def reset(self):
        self.active = False
        self.done = False
        self.selected_path = None
        self.buffer = ""
        self.error = None
        pygame.key.stop_text_input()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.reset()
            elif event.key == pygame.K_RETURN:
                path = self.buffer.strip()
                if Path(path).exists():
                    self.selected_path = path
                    self.done = True
                    self.active = False
                else:
                    self.error = "File not found"
            elif event.key == pygame.K_BACKSPACE:
                self.buffer = self.buffer[:-1]

        elif event.type == pygame.TEXTINPUT:
            self.buffer += event.text
            self.error = None

    def draw(self, screen):
        if not self.active:
            return

        pygame.draw.rect(screen, (50, 50, 60), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)

        screen.blit(self.font.render("CSV Importer", True, (200, 200, 200)),
                    (self.rect.x + 10, self.rect.y + 10))

        screen.blit(self.font.render("Enter file path:", True, (200, 200, 200)),
                    (self.rect.x + 10, self.rect.y + 40))

        pygame.draw.rect(screen, (30, 30, 40),
                         (self.rect.x + 10, self.rect.y + 70, self.rect.width - 20, 30))

        screen.blit(self.font.render(self.buffer, True, (200, 200, 200)),
                    (self.rect.x + 14, self.rect.y + 75))

        if self.error:
            screen.blit(self.font.render(self.error, True, (220, 80, 80)),
                        (self.rect.x + 10, self.rect.y + 110))