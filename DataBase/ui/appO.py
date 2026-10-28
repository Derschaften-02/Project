"""
Basic admin UI for the DataBase framework
Add / Remove data support + Drag & Drop import
"""

import pygame

# --------------------
# EARLY INIT (CRITICAL)
# --------------------
pygame.init()
pygame.font.init()
pygame.key.set_repeat(0, 0)

# --------------------
# FORCE MODEL REGISTRY
# --------------------
import models.user
import models.post

# ----------------------
# CORE IMPORTS
# ----------------------
from core.registry import all_models
from core.database import db_cursor, search_posts
from ui.importer import Importer, import_file

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

FONT = pygame.font.SysFont(None, 22)
BIG = pygame.font.SysFont(None, 26)

# --------------------
# DROP ZONE (BOTTOM-RIGHT)
# --------------------
DROP_ZONE_WIDTH = 280
DROP_ZONE_HEIGHT = 120
DROP_ZONE_MARGIN = 10  # distance from edges

DROP_ZONE = pygame.Rect(
    WIDTH - DROP_ZONE_WIDTH - DROP_ZONE_MARGIN,       
    HEIGHT - DROP_ZONE_HEIGHT - 40 - DROP_ZONE_MARGIN, 
    DROP_ZONE_WIDTH,
    DROP_ZONE_HEIGHT
)

# ====================
# MAIN ENTRY
# ====================
def run_ui():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DataBase Admin")

    pygame.event.set_allowed([
        pygame.QUIT,
        pygame.KEYDOWN,
        pygame.MOUSEBUTTONDOWN,
        pygame.MOUSEMOTION,
        pygame.DROPFILE,
    ])

    clock = pygame.time.Clock()

    # --------------------
    # STATE
    # --------------------
    models = list(all_models().values())
    current = models[0] if models else None
    selected_row = None

    input_mode = False
    input_buffer = ""

    group_mode = False
    group_column = None
    group_buffer = ""

    search_mode = False
    search_buffer = ""
    search_type = "fts"  

    importer = Importer()

    running = True
    while running:
        clock.tick(60)
        drag_hover = DROP_ZONE.collidepoint(pygame.mouse.get_pos())

        # ====================
        # EVENTS
        # ====================
        for e in pygame.event.get():

            # ----- QUIT -----
            if e.type == pygame.QUIT:
                running = False
                continue

            # ----- IMPORTER MODAL (HARD BLOCK) -----
            if importer.active:
                importer.handle_event(e)
                continue

            # ----- FILE DROP -----
            if e.type == pygame.DROPFILE and current:
                if DROP_ZONE.collidepoint(pygame.mouse.get_pos()):
                    import_file(current, e.file)

            # ----- MOUSE -----
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos

                # model list
                if mx < 180:
                    index = (my - 10) // 32
                    if 0 <= index < len(models):
                        current = models[index]
                        selected_row = None

                # row select
                elif current and mx > 200 and not group_column:
                    rows = current.all()
                    index = (my - 10) // 28
                    if 0 <= index < len(rows):
                        selected_row = rows[index]

            # ----- KEYBOARD -----
            elif e.type == pygame.KEYDOWN:
                print("[KEYDOWN]", pygame.key.name(e.key), "input_mode=", input_mode)

                # ---------- CONFIRM ----------
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    print("[ENTER HIT]")

                    if input_mode:
                        print("[ADD CONFIRM]", input_buffer)
                        create_row(current, input_buffer)
                        input_buffer = ""
                        input_mode = False
                        pygame.key.stop_text_input()

                    elif group_mode:
                        group_column = group_buffer.strip() or None
                        group_buffer = ""
                        group_mode = False
                        pygame.key.stop_text_input()
                    
                    elif search_mode:
                        search_mode = False
                        pygame.key.stop_text_input()
                    continue

                # ---------- CANCEL ----------
                if e.key == pygame.K_ESCAPE:
                    input_mode = False
                    group_mode = False
                    search_mode = False
                    input_buffer = ""
                    group_buffer = ""
                    search_buffer = ""
                    group_column = None
                    pygame.key.stop_text_input()
                    continue

                # ---------- BACKSPACE ----------
                if e.key == pygame.K_BACKSPACE:
                    if input_mode:
                        input_buffer = input_buffer[:-1]
                    elif group_mode:
                        group_buffer = group_buffer[:-1]
                    elif search_mode:
                        search_buffer = search_buffer[:-1]
                    continue

                #this is vodoo code it doesnt like it when u remove it but doesnt work when its active leave it alone#
                # ---------- TEXT ----------
                #if input_mode and e.unicode and e.unicode.isprintable():
                    #input_buffer += e.unicode
                    #continue

                #if group_mode and e.unicode and e.unicode.isprintable():
                    #group_buffer += e.unicode
                    #continue                                            

                # ---------- SEARCH CONFIRM ----------
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    print("[ENTER HIT]")

                    if search_mode:
                        search_mode = False
                        continue

                # ---------- MODE ENTRY ----------
                if not input_mode and not group_mode and not search_mode:
                    if e.key == pygame.K_a:
                        print("[MODE] ADD")
                        input_mode = True
                        input_buffer = ""
                        pygame.key.start_text_input()
                        continue

                    elif e.key == pygame.K_g:
                        print("[MODE] GROUP")
                        group_mode = True
                        group_buffer = ""
                        pygame.key.start_text_input()
                        continue

                    elif e.key == pygame.K_i:
                        print("[MODE] IMPORT")
                        importer.open()
                        continue

                    elif e.key == pygame.K_s:
                        print("[MODE] SEARCH")
                        search_mode = True
                        search_buffer = ""
                        pygame.key.start_text_input()
                        continue

                elif e.key == pygame.K_TAB and search_mode:
                    search_type = "like" if search_type == "fts" else "fts"

            # ----- TEXT INPUT -----
            elif e.type == pygame.TEXTINPUT:
                if input_mode:
                    input_buffer += e.text
                elif group_mode:
                    group_buffer += e.text
                elif search_mode:
                    search_buffer += e.text
   
        # ====================
        # IMPORT RESULT
        # ====================
        if importer.done:
            if importer.selected_path and current:
                import_file(current, importer.selected_path)
            importer.reset()
            pygame.key.start_text_input()

        # ====================
        # DRAW
        # ====================
        draw(
            screen,
            models,
            current,
            selected_row,
            input_mode,
            input_buffer,
            group_mode,
            group_column,
            group_buffer,
            search_mode,
            search_buffer,
            search_type,
            drag_hover,
        )

        importer.draw(screen)
        pygame.display.flip()

    pygame.quit()


# ====================
# HELPERS
# ====================
def create_row(model, buffer):
    if model is None:
        print("[ADD ERROR] no active model")
        return

    if not hasattr(model, "create"):
        print("[ADD ERROR] model has no create()", model)
        return

    buffer = buffer.strip()
    if not buffer:
        print("[ADD] empty input")
        return

    data = {}
    for pair in buffer.split():
        if "=" not in pair:
            print(f"[ADD] invalid token '{pair}'")
            return
        k, v = pair.split("=", 1)
        data[k] = v

    try:
        model.create(**data)
        print("[ADD] row created:", data)

        cls = model if isinstance(model, type) else model.__class__
        if hasattr(cls.all, "cache_clear"):
            cls.all.cache_clear()

    except Exception as e:
        print("[ADD ERROR]", e)

def delete_row(model, row):
    with db_cursor() as cur:
        cur.execute(
            f"DELETE FROM {model.table} WHERE id = ?",
            (row["id"],),
        )

def group_rows(rows, column):
    groups = {}
    for row in rows:
        key = row.get(column, "<missing>")
        groups.setdefault(key, []).append(row)
    return groups

# ====================
# DRAWING
# ====================
def draw_drop_zone(screen, hover):
    color = DROP_ACTIVE if hover else DROP_BG
    pygame.draw.rect(screen, color, DROP_ZONE, border_radius=6)
    pygame.draw.rect(screen, HILITE, DROP_ZONE, 2, border_radius=6)

    screen.blit(BIG.render("Drag File Here", True, HILITE), (DROP_ZONE.x + 20, DROP_ZONE.y + 18))
    screen.blit(FONT.render("TXT / CSV", True, TEXT), (DROP_ZONE.x + 20, DROP_ZONE.y + 55))
    screen.blit(FONT.render("Imports into active table", True, TEXT), (DROP_ZONE.x + 20, DROP_ZONE.y + 78))

def draw(
    screen,
    models,
    current,
    selected,
    input_mode,
    buffer,
    group_mode,
    group_column,
    group_buffer,
    search_mode,
    search_buffer,
    search_type,
    drag_hover,
):
    screen.fill(BG)
    draw_drop_zone(screen, drag_hover)

    pygame.draw.rect(screen, PANEL, (0, 0, 180, HEIGHT))

    # -----------------------
    # MODEL LIST
    # -----------------------
    y = 10
    for m in models:
        screen.blit(
            FONT.render(m.table, True, HILITE if m == current else TEXT),
            (12, y),
        )
        y += 32

    # -----------------------
    # DATA PANEL
    # -----------------------
    if current:
        rows = current.all()

        # Apply search
        if search_buffer.strip():
            try:
                rows = search_posts(search_buffer, mode=search_type)
            except Exception as e:
                print("[SEARCH ERROR]", e)
                rows = []

        panel_x = 200
        panel_width = WIDTH - 200
        y = 10

        # Determine columns
        columns = rows[0].keys() if rows else ["id"]

        # Handle group mode
        groups = {None: rows}
        if group_column:
            groups = group_rows(rows, group_column)

        # Draw each group
        for group_key, items in groups.items():

            # Group title
            if group_key is not None:
                screen.blit(
                    BIG.render(f"{group_column} = {group_key} ({len(items)})", True, HILITE),
                    (panel_x, y),
                )
                y += 30

            # Draw column headers
            header_height = 28
            pygame.draw.rect(screen, PANEL, (panel_x, y, panel_width, header_height))
            x_offset = panel_x + 5
            for col in columns:
                screen.blit(BIG.render(col.upper(), True, HILITE), (x_offset, y + 4))
                x_offset += 180  # column width
            y += header_height + 2

            # Draw rows
            for row in items:
                x_offset = panel_x + 5
                if selected and row["id"] == selected["id"]:
                    pygame.draw.rect(screen, SELECT, (panel_x, y, panel_width, header_height))

                for col in columns:
                    val = str(row[col])
                    screen.blit(FONT.render(val, True, TEXT), (x_offset, y + 4))
                    x_offset += 180

                y += header_height + 2

    # -----------------------
    # BOTTOM BAR
    # -----------------------
    pygame.draw.rect(screen, PANEL, (190, HEIGHT - 40, WIDTH - 200, 30))

    if search_mode:
        screen.blit(
            BIG.render(f"SEARCH ({search_type.upper()}): " + search_buffer, True, HILITE),
            (200, HEIGHT - 36),
        )
    elif group_mode:
        screen.blit(BIG.render("GROUP BY: " + group_buffer, True, HILITE), (200, HEIGHT - 36))
    elif input_mode:
        screen.blit(BIG.render("ADD: " + buffer, True, HILITE), (200, HEIGHT - 36))
    else:
        screen.blit(
            FONT.render(
                "A=add | G=group | S=search | I=import | DEL=delete | ESC=cancel | TAB=toggle search",
                True,
                (150, 150, 150),
            ),
            (200, HEIGHT - 30),
        )

