import sys
from pathlib import Path
import pygame

from migrations.init import migrate
from core.database import create_user
from ui.pivot_importer import import_csv_to_model
from core.registry import all_models
from ui.app import run_ui
from ui.login_screen import LoginScreen

def setup_database():
    migrate()

    try:
        create_user("admin", "adminpass", role="admin")
        print("[DB] default admin created")
    except:
        print("[DB] default admin exists")

    try:
        create_user("guest", "guestpass", role="guest")
        print("[DB] default guest created")
    except:
        print("[DB] default guest exists")


def main():
    print("[DataBase] starting framework")
    setup_database()
    print("[DataBase] database ready")

    # CLI import mode
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            print("[IMPORT] file not found")
            return

        try:
            import_csv_to_model(str(file_path), model_name = file_path.stem)
            print("[IMPORT] completed successfully")
        except Exception as e:
            print("[IMPORT ERROR]", e)

        return

    # ------------------------
    # GUI Mode: Login First
    # ------------------------
    pygame.init()
    screen = pygame.display.set_mode((1000, 620), pygame.RESIZABLE)
    pygame.display.set_caption("DataBase UI - Login")

    login = LoginScreen(screen)
    logged_in = False

    while not logged_in:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            else:
                logged_in = login.handle_event(event)

        login.draw()
        pygame.display.flip()

    print(f"[LOGIN SUCCESS] {login.current_user['username']} ({login.current_user['role']})")

    # Launch AdminUI after successful login

    run_ui()


if __name__ == "__main__":
    main()