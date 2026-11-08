import sqlite3
import sys
from pathlib import Path

from migrations.init import migrate
from core.database import create_user
from core.importer import import_file


def setup_database():
    migrate()
    for username, password, role in [("admin", "adminpass", "admin"),
                                     ("guest", "guestpass", "guest")]:
        try:
            create_user(username, password, role)
            print(f"[DB] default {role} created")
        except sqlite3.IntegrityError:
            pass  # already exists


def cli_import(file_path):
    path = Path(file_path)
    if not path.exists():
        print("[IMPORT] file not found")
        return
    try:
        model = import_file(path)
        print(f"[IMPORT] {model.count()} rows -> table '{model.table}'")
    except Exception as e:
        print("[IMPORT ERROR]", e)


def run_gui():
    # pygame/UI imported here so CLI import works without them
    import pygame
    from ui.app import run_ui
    from ui.login_screen import LoginScreen

    pygame.init()
    screen = pygame.display.set_mode((1000, 620), pygame.RESIZABLE)
    pygame.display.set_caption("DataBase UI - Login")
    clock = pygame.time.Clock()

    login = LoginScreen(screen)
    logged_in = False
    while not logged_in:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if login.handle_event(event):
                logged_in = True
        login.draw()
        pygame.display.flip()
        clock.tick(60)

    print(f"[LOGIN] {login.current_user['username']} ({login.current_user['role']})")
    run_ui()


def main():
    setup_database()
    if len(sys.argv) > 1:
        cli_import(sys.argv[1])
    else:
        run_gui()


if __name__ == "__main__":
    main()