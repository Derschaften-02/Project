import pygame
import os
import csv
import zipfile
import tempfile
from pathlib import Path


class Importer:
    def __init__(self):
        print("[IMPORTER] init from", __file__)
        # fonts will be created lazily
        self.FONT = None
        self.BIG = None

        self.active = False
        self.done = False
        self.selected_path = None
        self.buffer = ""
        self.error = None

        # colors
        self.BG = (20, 20, 26)
        self.PANEL = (50, 50, 60)
        self.TEXT = (230, 230, 230)
        self.HILITE = (255, 200, 80)
        self.ERROR = (220, 80, 80)

    # --------------------
    # INTERNAL
    # --------------------
    def _ensure_fonts(self):
        if not self.FONT:
            self.FONT = pygame.font.SysFont(None, 22)
            self.BIG = pygame.font.SysFont(None, 26)

    # --------------------
    # STATE
    # --------------------
    def open(self):
        self._ensure_fonts()
        self.active = True
        self.done = False
        self.selected_path = None
        self.buffer = ""
        self.error = None
        pygame.key.start_text_input()
        print("[IMPORTER] open")

    def reset(self):
        self.active = False
        self.done = False
        self.selected_path = None
        self.buffer = ""
        self.error = None
        pygame.key.stop_text_input()

    # --------------------
    # EVENTS
    # --------------------
    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                print("[IMPORTER] cancel")
                self.reset()

            elif e.key == pygame.K_RETURN:
                path = self.buffer.strip()
                if os.path.isfile(path):
                    self.selected_path = path
                    self.done = True
                    self.active = False
                    pygame.key.stop_text_input()
                    print("[IMPORTER] selected:", path)
                else:
                    self.error = "File not found"

            elif e.key == pygame.K_BACKSPACE:
                self.buffer = self.buffer[:-1]

        elif e.type == pygame.TEXTINPUT:
            self.buffer += e.text
            self.error = None

    # --------------------
    # DRAW
    # --------------------
    def draw(self, screen):
        if not self.active:
            return

        self._ensure_fonts()

        w, h = screen.get_size()
        panel = pygame.Rect(w // 2 - 260, h // 2 - 90, 520, 180)

        pygame.draw.rect(screen, self.BG, panel)
        pygame.draw.rect(screen, self.HILITE, panel, 2)

        screen.blit(
            self.BIG.render("Import File", True, self.HILITE),
            (panel.x + 16, panel.y + 12),
        )

        screen.blit(
            self.FONT.render("Enter file path and press Enter:", True, self.TEXT),
            (panel.x + 16, panel.y + 48),
        )

        pygame.draw.rect(
            screen,
            self.PANEL,
            (panel.x + 16, panel.y + 72, panel.width - 32, 32),
        )

        screen.blit(
            self.FONT.render(self.buffer, True, self.TEXT),
            (panel.x + 22, panel.y + 80),
        )

        screen.blit(
            self.FONT.render("Enter = confirm | Esc = cancel", True, (160, 160, 160)),
            (panel.x + 16, panel.y + 120),
        )

        if self.error:
            screen.blit(
                self.FONT.render(self.error, True, self.ERROR),
                (panel.x + 16, panel.y + 148),
            )


# --------------------
# API
# --------------------
def import_file(model, path, ui=None):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    # --------------------
    # ZIP file support
    # --------------------
    if path.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
                print(f"[IMPORTER] Extracted ZIP to {tmpdir}")

                for file_name in os.listdir(tmpdir):
                    extracted_path = Path(tmpdir) / file_name
                    if extracted_path.suffix.lower() in [".csv", ".txt"]:
                        import_file(model, extracted_path, ui)
                    else:
                        print(f"[IMPORTER] Skipped unsupported file: {file_name}")

    # --------------------
    # CSV file
    # --------------------
    elif path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                model.create(**row)

    # --------------------
    # TXT file
    # --------------------
    elif path.suffix.lower() == ".txt":
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                data = {}
                for pair in line.split():
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        data[k] = v

                if data:
                    model.create(**data)

    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    # --------------------
    # Refresh UI if provided
    # --------------------
    if ui and hasattr(ui, "load_models"):
        ui.load_models()
        print("[IMPORTER] UI refreshed after import")

