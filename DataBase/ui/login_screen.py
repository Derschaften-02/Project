import pygame
from core.database import verify_user  

class LoginScreen:
    def __init__(self, screen):
        if not pygame.get_init():
            pygame.init()
            pygame.font.init()

        self.screen = screen
        self.font = pygame.font.SysFont("consolas", 24)

        self.username = ""
        self.password = ""
        self.active_field = "username"
        self.message = ""
        self.current_user = None

    # --------------------
    # Event handling
    # --------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_TAB:
                # switch input field
                self.active_field = (
                    "password" if self.active_field == "username" else "username"
                )

            elif event.key == pygame.K_RETURN:
                return self.try_login()

            elif event.key == pygame.K_BACKSPACE:
                if self.active_field == "username":
                    self.username = self.username[:-1]
                else:
                    self.password = self.password[:-1]

            else:
                if event.unicode.isprintable():
                    if self.active_field == "username":
                        self.username += event.unicode
                    else:
                        self.password += event.unicode

        return False

    # --------------------
    # Login logic
    # --------------------
    def try_login(self):
        # verify credentials with hashed passwords
        user = verify_user(self.username, self.password)

        if not user:
            self.message = "User not found or wrong password"
            self.current_user = None
            return False

        self.current_user = user
        self.message = f"Login successful ({user['role']})"
        print(f"[LOGIN SUCCESS] {user['username']} ({user['role']})")
        return True

    # --------------------
    # Draw function
    # --------------------
    def draw(self):
        self.screen.fill((20, 20, 20))

        # Title
        title = self.font.render("DataBase Login", True, (255, 255, 255))
        self.screen.blit(title, (100, 50))

        # Labels
        u_label = self.font.render("Username:", True, (200, 200, 200))
        p_label = self.font.render("Password:", True, (200, 200, 200))
        self.screen.blit(u_label, (100, 150))
        self.screen.blit(p_label, (100, 200))

        # Input text
        u_text = self.font.render(self.username, True, (255, 255, 255))
        p_text = self.font.render("*" * len(self.password), True, (255, 255, 255))
        self.screen.blit(u_text, (250, 150))
        self.screen.blit(p_text, (250, 200))

        # Message
        msg = self.font.render(self.message, True, (255, 100, 100))
        self.screen.blit(msg, (100, 260))
