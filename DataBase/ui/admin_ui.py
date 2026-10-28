import pygame
from core.registry import all_models
from core.database import db_cursor, search_posts
from ui.pivot_importer import Importer, import_csv_to_model as import_file
from pathlib import Path

# --------------------
# CONSTANTS
# --------------------
WIDTH, HEIGHT = 1000, 620

BG = (28, 28, 32)
PANEL = (40, 40, 46)
TEXT = (220, 220, 220)
HILITE = (255, 200, 80)
SELECT = (80, 120, 200)

DROP_BG = (55, 55, 65)
DROP_ACTIVE = (90, 140, 220)

DROP_ZONE_WIDTH = 280
DROP_ZONE_HEIGHT = 120
DROP_ZONE_MARGIN = 10

# --------------------
# ADMIN UI CLASS
# --------------------
class AdminUI:
    def __init__(self, screen, logger=None):
        if not pygame.get_init():
            pygame.init()
            pygame.font.init()

        self.screen = screen
        self.clock = pygame.time.Clock()

        # Fonts
        self.FONT = pygame.font.SysFont(None, 22)
        self.BIG = pygame.font.SysFont(None, 26)
        self.logger_font = pygame.font.SysFont(None, 18)

        # State
        self.models = [m for m in all_models().values() if m.table != "users"]
        self.current = self.models[0] if self.models else None
        self.selected_row = None

        self.input_mode = False
        self.input_buffer = ""
        self.group_mode = False
        self.group_column = None
        self.group_buffer = ""
        self.search_mode = False
        self.search_buffer = ""
        self.search_type = "fts"

        self.importer = Importer(ui=self)

        # Scroll states
        self.table_scroll = 0
        self.logger_scroll = 0
        self.SCROLL_SPEED = 20

        # Logger
        self.logs = []
        self.LOG_HEIGHT = 120
        self.logger = logger  # optional external logger

        # Drop zone rect (recomputed on resize)
        self._update_drop_zone(WIDTH, HEIGHT)

    # --------------------
    # LOGGER METHODS
    # --------------------
    def log(self, message):
        print(message)
        if self.logger:
            try:
                self.logger.log(message)
            except Exception as e:
                print(f"[EXTERNAL LOGGER ERROR] {e}")
        self.logs.append(message)
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]

    # --------------------
    # RUN LOOP
    # --------------------
    def run(self):
        running = True
        last_mouse = pygame.mouse.get_pos()
        while running:
            self.clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()
            drag_hover = self.drop_zone.collidepoint(mouse_pos)
            mouse_pressed = pygame.mouse.get_pressed()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                    continue

                if e.type == pygame.VIDEORESIZE:
                    global WIDTH, HEIGHT
                    WIDTH, HEIGHT = e.w, e.h
                    self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    self._update_drop_zone(WIDTH, HEIGHT)

                # Mouse scroll
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button in (4, 5):  # wheel
                        self._handle_scroll(e.button)

                # File drop
                if e.type == pygame.DROPFILE:
                    self._handle_drop(e.file, drag_hover)

                # Importer
                if self.importer.active:
                    self.importer.handle_event(e)

                # Mouse click
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self._handle_mouse(e.pos)

                # Keyboard
                if e.type in (pygame.KEYDOWN, pygame.TEXTINPUT):
                    self._handle_keyboard(e)
                    
            # Scrollbar
            self._handle_scrollbar_drag(mouse_pressed, mouse_pos, last_mouse)
            last_mouse = mouse_pos

            # Draw everything
            self._draw(drag_hover)
            self._draw_logger()
            self._draw_scrollbars()
            self.importer.draw(self.screen)
            pygame.display.flip()

        pygame.quit()

    # --------------------
    # SCROLL HANDLER
    # --------------------
    def _handle_scroll(self, button):
        # Table scroll
        table_max = min(0, HEIGHT - 60 - self._table_content_height())
        if button == 4:  # scroll up
            self.table_scroll = min(self.table_scroll + self.SCROLL_SPEED, 0)
            self.logger_scroll = min(self.logger_scroll + self.SCROLL_SPEED, 0)
        elif button == 5:  # scroll down
            self.table_scroll = max(self.table_scroll - self.SCROLL_SPEED, table_max)
            logger_max = min(0, self.LOG_HEIGHT - self._logger_content_height())
            self.logger_scroll = max(self.logger_scroll - self.SCROLL_SPEED, logger_max)

    # --------------------
    # DROP ZONE
    # --------------------
    def _update_drop_zone(self, width, height):
        self.drop_zone = pygame.Rect(
            width - DROP_ZONE_WIDTH - DROP_ZONE_MARGIN,
            height - DROP_ZONE_HEIGHT - 40 - DROP_ZONE_MARGIN,
            DROP_ZONE_WIDTH,
            DROP_ZONE_HEIGHT,
        )

    def _handle_drop(self, path, hover):
        if hover:
            self.log(f"Dropped file: {path}")
            try:
                model_name = Path(path).stem if not self.current else self.current.table
                imported_model = import_file(path, model_name=model_name, ui=self)
                self.load_models()
                if not self.current:
                    self.current = next((m for m in self.models if m.table == model_name), imported_model)
                self.selected_row = None
                self.log(f"Imported: {path} into {model_name}")
            except Exception as ex:
                self.log(f"[IMPORT ERROR] {ex}")

    # --------------------
    # MOUSE HANDLING
    # --------------------
    def _handle_mouse(self, pos):
        mx, my = pos
        if mx < 180:
            index = (my - 10) // 32
            if 0 <= index < len(self.models):
                self.current = self.models[index]
                self.selected_row = None
                self.log(f"Selected model: {self.current.table}")
        elif self.current and mx > 200 and not self.group_column:
            rows = self.current.all()
            if self.search_buffer.strip():
                try:
                    rows = search_posts(self.search_buffer, mode=self.search_type)
                except:
                    rows = []
            index = int((my - 10 - self.table_scroll) // 28)
            if 0 <= index < len(rows):
                self.selected_row = rows[index]
                self.log(f"Selected row ID: {self.selected_row['id']}")

    # --------------------
    # KEYBOARD HANDLING
    # --------------------
    def _handle_keyboard(self, e):
        if e.type == pygame.TEXTINPUT:
            if self.input_mode: self.input_buffer += e.text
            elif self.group_mode: self.group_buffer += e.text
            elif self.search_mode: self.search_buffer += e.text
            return
        if e.type != pygame.KEYDOWN: return

        if e.key == pygame.K_ESCAPE:
            self.input_mode = self.group_mode = self.search_mode = False
            self.input_buffer = self.group_buffer = self.search_buffer = ""
            self.group_column = None
            pygame.key.stop_text_input()
            self.log("Cleared input/group/search mode")
            return

        if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.input_mode:
                self.create_row(self.current, self.input_buffer)
                self.log(f"Added row: {self.input_buffer}")
                self.input_buffer = ""
                self.input_mode = False
                pygame.key.stop_text_input()
            elif self.group_mode:
                self.group_column = self.group_buffer.strip() or None
                self.group_buffer = ""
                self.group_mode = False
                pygame.key.stop_text_input()
                self.log(f"Grouping by: {self.group_column}")
            elif self.search_mode:
                self.search_mode = False
                pygame.key.stop_text_input()
                self.log(f"Search completed: {self.search_buffer}")
            return

        if e.key == pygame.K_BACKSPACE:
            if self.input_mode: self.input_buffer = self.input_buffer[:-1]
            elif self.group_mode: self.group_buffer = self.group_buffer[:-1]
            elif self.search_mode: self.search_buffer = self.search_buffer[:-1]
            return

        if not (self.input_mode or self.group_mode or self.search_mode):
            if e.key == pygame.K_a:  # Add
                self.input_mode = True
                self.input_buffer = ""
                pygame.key.start_text_input()
            elif e.key == pygame.K_g:  # Group
                self.group_mode = True
                self.group_buffer = ""
                pygame.key.start_text_input()
            elif e.key == pygame.K_s:  # Search
                self.search_mode = True
                self.search_buffer = ""
                pygame.key.start_text_input()
            elif e.key == pygame.K_i:  # Import
                if not self.current:
                    self.log("[IMPORT] No model selected")
                    self.importer.open()
                else:
                    self.importer.open()
            elif e.key == pygame.K_d:  # Deselect
                if self.current:
                    self.log(f"Deselected model: {self.current.table}")
                    self.current = None
                    self.selected_row = None
        elif e.key == pygame.K_TAB and self.search_mode:
            self.search_type = "like" if self.search_type == "fts" else "fts"

    # --------------------
    # CREATE ROW
    # --------------------
    def create_row(self, model, buffer):
        if not model: return
        data = {}
        for pair in buffer.split():
            if "=" in pair:
                k, v = pair.split("=", 1)
                data[k] = v
        try:
            model.create(**data)
        except Exception as e:
            self.log(f"[ADD ERROR] {e}")

    # --------------------
    # MODEL LOADER
    # --------------------
    def load_models(self):
        self.models = [m for m in all_models().values() if m.table != "users"]
        if self.models and not self.current:
            self.current = self.models[-1]

    # --------------------
    # DRAW UI
    # --------------------
    def _draw(self, drag_hover):
        self.screen.fill(BG)
        self._draw_drop_zone(drag_hover)
        self._draw_sidebar()
        self._draw_table()
        self._draw_bottom_bar()

    # --------------------
    # DRAW LOGGER
    # --------------------
    def _draw_logger(self):
        LOGGER_WIDTH = 150
        LOGGER_PADDING = 6
        logger_x = 10
        logger_y = HEIGHT - self.LOG_HEIGHT - 5

        pygame.draw.rect(self.screen, PANEL, (logger_x, logger_y, LOGGER_WIDTH, self.LOG_HEIGHT), border_radius=6)

        surface = pygame.Surface((LOGGER_WIDTH - 2*LOGGER_PADDING, self.LOG_HEIGHT - 2*LOGGER_PADDING))
        surface.fill(PANEL)
        font_height = self.logger_font.get_linesize()
        y_offset = self.logger_scroll

        for msg in self.logs:
            words = msg.split()
            line = ""
            for word in words:
                test_line = line + (" " if line else "") + word
                if self.logger_font.size(test_line)[0] > surface.get_width():
                    surface.blit(self.logger_font.render(line, True, TEXT), (0, y_offset))
                    y_offset += font_height
                    line = word
                else:
                    line = test_line
            if line:
                surface.blit(self.logger_font.render(line, True, TEXT), (0, y_offset))
                y_offset += font_height

        self.screen.blit(surface, (logger_x + LOGGER_PADDING, logger_y + LOGGER_PADDING))

    # --------------------
    # DRAW SIDEBAR, TABLE, BOTTOM BAR, DROP ZONE
    # --------------------
    def _draw_sidebar(self):
        pygame.draw.rect(self.screen, PANEL, (0, 0, 180, HEIGHT))
        y = 10
        for m in self.models:
            self.screen.blit(self.FONT.render(m.table, True, HILITE if m == self.current else TEXT), (12, y))
            y += 32

    def _compute_column_widths(self, rows, columns, min_width=80, padding=20):
        widths = []

        for col in columns:
            max_w = self.BIG.size(col.upper())[0]

            for r in rows:
                text = str(r.get(col, ""))
                w = self.FONT.size(text)[0]
                if w > max_w:
                    max_w = w

            widths.append(max(min_width, max_w + padding))

        return widths

    def _draw_table(self):
        if not self.current:
            return
        rows = self.current.all()
        
        if self.search_buffer.strip():
            try:
                rows = search_posts(self.search_buffer, mode=self.search_type)
            except:
                rows = []

        panel_x = 200
        panel_width = WIDTH - 200
        y = 10 + self.table_scroll

        columns = list(rows[0].keys()) if rows else ["id"]

        col_widths = self._compute_column_widths(rows, columns)

        groups = {None: rows}
        if self.group_column:
            groups = {}
            for row in rows:
                key = row.get(self.group_column, "<missing>")
                groups.setdefault(key, []).append(row)

        for group_key, items in groups.items():

            if group_key is not None:
                self.screen.blit(
                    self.BIG.render(
                        f"{self.group_column} = {group_key} ({len(items)})",
                        True,
                        HILITE,
                    ),
                    (panel_x, y),
                )
                y += 30

            header_height = 28
            pygame.draw.rect(self.screen, PANEL, (panel_x, y, panel_width, header_height))

            x_offset = panel_x + 5

            for i, col in enumerate(columns):
                self.screen.blit(
                    self.BIG.render(col.upper(), True, HILITE),
                    (x_offset, y + 4),
                )
                x_offset += col_widths[i]

            y += header_height + 2

            for row in items:

                x_offset = panel_x + 5

                if self.selected_row and row["id"] == self.selected_row["id"]:
                    pygame.draw.rect(
                        self.screen,
                        SELECT,
                        (panel_x, y, panel_width, header_height),
                    )

                for i, col in enumerate(columns):
                    val = str(row.get(col, ""))
                    self.screen.blit(
                        self.FONT.render(val, True, TEXT),
                        (x_offset, y + 4),
                    )
                    x_offset += col_widths[i]

                y += header_height + 2

    def _draw_bottom_bar(self):
        pygame.draw.rect(self.screen, PANEL, (190, HEIGHT - 40, WIDTH - 200, 30))
        if self.search_mode:
            display_text = f"SEARCH ({self.search_type.upper()}): {self.search_buffer}"
        elif self.group_mode:
            display_text = "GROUP BY: " + self.group_buffer
        elif self.input_mode:
            display_text = "ADD: " + self.input_buffer
        else:
            status_text = f"Current model: {self.current.table}" if self.current else "No model selected"
            display_text = status_text + " | A=add | G=group | S=search | I=import | D=deselect | ESC=cancel | TAB=toggle search"

        self.screen.blit(self.FONT.render(display_text, True, HILITE if (self.input_mode or self.group_mode or self.search_mode) else (150,150,150)), (200, HEIGHT - 30))

    def _draw_drop_zone(self, hover):
        color = DROP_ACTIVE if hover else DROP_BG
        pygame.draw.rect(self.screen, color, self.drop_zone, border_radius=6)
        pygame.draw.rect(self.screen, HILITE, self.drop_zone, 2, border_radius=6)
        self.screen.blit(self.BIG.render("Drag File Here", True, HILITE), (self.drop_zone.x + 20, self.drop_zone.y + 18))
        self.screen.blit(self.FONT.render("TXT / CSV", True, TEXT), (self.drop_zone.x + 20, self.drop_zone.y + 55))
        self.screen.blit(self.FONT.render("Imports into active table", True, TEXT), (self.drop_zone.x + 20, self.drop_zone.y + 78))
        
    # --------------------
    # CONTENT HEIGHT CALCULATORS
    # --------------------
    def _table_content_height(self):
        if not self.current: 
            return 0
        rows = self.current.all()
        header_height = 28 + 2
        row_height = 28 + 2
        y = 0
        if self.group_column:
            groups = {}
            for row in rows:
                key = row.get(self.group_column, "<missing>")
                groups.setdefault(key, []).append(row)
            for items in groups.values():
                y += 30
                y += header_height
                y += row_height * len(items)
            return y
        else:
            return header_height + row_height * len(rows)

    def _logger_content_height(self):
        font_height = self.logger_font.get_linesize()
        total_lines = 0
        for msg in self.logs:
            words = msg.split()
            line = ""
            for word in words:
                test_line = line + (" " if line else "") + word
                if self.logger_font.size(test_line)[0] > 150 - 2*6:
                    total_lines += 1
                    line = word
                else:
                    line = test_line
            if line:
                total_lines += 1
        return total_lines * font_height
        
    # --------------------
    # SCROLLBAR DRAWING & DRAG
    # --------------------
    def _draw_scrollbars(self):
        # Table scrollbar
        if self.current:
            content_height = self._table_content_height()
            view_height = HEIGHT - 60
            if content_height > view_height:
                scrollbar_height = max(20, view_height * view_height // content_height)
                scroll_ratio = -self.table_scroll / (content_height - view_height)
                scroll_y = int(scroll_ratio * (view_height - scrollbar_height))
                table_scrollbar_rect = pygame.Rect(WIDTH - 10, scroll_y, 8, scrollbar_height)
                pygame.draw.rect(self.screen, (80, 80, 80), table_scrollbar_rect)

        # Logger scrollbar
        logger_content_height = self._logger_content_height()
        LOGGER_WIDTH = 150
        LOGGER_PADDING = 6
        logger_x = 10
        logger_y = HEIGHT - self.LOG_HEIGHT - 5
        if logger_content_height > self.LOG_HEIGHT:
            scrollbar_height = max(10, self.LOG_HEIGHT * self.LOG_HEIGHT // logger_content_height)
            scroll_ratio = -self.logger_scroll / (logger_content_height - self.LOG_HEIGHT)
            scroll_y = int(logger_y + scroll_ratio * (self.LOG_HEIGHT - scrollbar_height))
            logger_scrollbar_rect = pygame.Rect(logger_x + LOGGER_WIDTH - 8, scroll_y, 6, scrollbar_height)
            pygame.draw.rect(self.screen, (80, 80, 80), logger_scrollbar_rect)

    def _handle_scrollbar_drag(self, mouse_pressed, mouse_pos, last_mouse):
        mx, my = mouse_pos
        lx, ly = last_mouse

        if not hasattr(self, '_dragging_table'): self._dragging_table = False
        if not hasattr(self, '_dragging_logger'): self._dragging_logger = False

        # Table drag
        if self.current:
            content_height = self._table_content_height()
            view_height = HEIGHT - 60
            if content_height > view_height:
                scrollbar_height = max(20, view_height * view_height // content_height)
                scroll_ratio = -self.table_scroll / (content_height - view_height)
                scroll_y = int(scroll_ratio * (view_height - scrollbar_height))
                table_scrollbar_rect = pygame.Rect(WIDTH - 10, scroll_y, 8, scrollbar_height)

                if mouse_pressed[0] and table_scrollbar_rect.collidepoint(mx, my):
                    self._dragging_table = True
                if not mouse_pressed[0]: self._dragging_table = False
                if self._dragging_table:
                    delta = my - ly
                    self.table_scroll -= delta * (content_height - view_height) / (view_height - scrollbar_height)
                    self.table_scroll = max(-(content_height - view_height), min(0, self.table_scroll))

        # Logger drag
        LOGGER_WIDTH = 150
        LOGGER_PADDING = 6
        logger_y = HEIGHT - self.LOG_HEIGHT - 5
        logger_content_height = self._logger_content_height()
        if logger_content_height > self.LOG_HEIGHT:
            scrollbar_height = max(10, self.LOG_HEIGHT * self.LOG_HEIGHT // logger_content_height)
            scroll_ratio = -self.logger_scroll / (logger_content_height - self.LOG_HEIGHT)
            scroll_y = int(logger_y + scroll_ratio * (self.LOG_HEIGHT - scrollbar_height))
            logger_scrollbar_rect = pygame.Rect(10 + LOGGER_WIDTH - 8, scroll_y, 6, scrollbar_height)

            if mouse_pressed[0] and logger_scrollbar_rect.collidepoint(mx, my):
                self._dragging_logger = True
            if not mouse_pressed[0]: self._dragging_logger = False
            if self._dragging_logger:
                delta = my - ly
                self.logger_scroll -= delta * (logger_content_height - self.LOG_HEIGHT) / (self.LOG_HEIGHT - scrollbar_height)
                self.logger_scroll = max(-(logger_content_height - self.LOG_HEIGHT), min(0, self.logger_scroll))