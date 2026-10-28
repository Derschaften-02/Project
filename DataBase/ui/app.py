import sys
import pygame
from ui.admin_ui import AdminUI

# --------------------
# UI LOGGER
# --------------------
class UILogger:
    """
    Redirects stdout and stderr to the UI while keeping terminal output.
    """
    def __init__(self, original, max_lines=500):
        self.original = original
        self.lines = []
        self.max_lines = max_lines

    def write(self, message):
        try:
            self.original.write(message)  # still prints to terminal
            self.original.flush()
        except Exception:
            pass  # avoid breaking if terminal output fails

        if message.strip():
            self.lines.append(message.strip())
            if len(self.lines) > self.max_lines:
                self.lines.pop(0)

    def flush(self):
        try:
            self.original.flush()
        except Exception:
            pass


def run_ui(exit_callback=None):
    """
    Initialize Pygame, redirect logs, and run the AdminUI.
    """
    try:
        pygame.init()
        pygame.font.init()
    except Exception as e:
        print("[UI INIT ERROR]", e)
        return

    # Setup screen
    screen = pygame.display.set_mode((1000, 620), pygame.RESIZABLE)
    pygame.display.set_caption("DataBase UI")

    # Redirect console output to UI logger
    ui_logger = UILogger(sys.stdout)
    sys.stdout = ui_logger
    sys.stderr = ui_logger

    # Initialize Admin UI
    try:
        admin_ui = AdminUI(screen, logger=ui_logger)
        admin_ui.run()
    except Exception as e:
        print("[UI ERROR]", e)
    finally:
        # Reset stdout/stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        if exit_callback:
            exit_callback()
        pygame.quit()


if __name__ == "__main__":
    run_ui()