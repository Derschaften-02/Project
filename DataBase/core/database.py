import sqlite3
from pathlib import Path
from contextlib import contextmanager
import sys
import hashlib
import os
import csv
import zipfile
import tempfile
import pygame

# -------------------------------------------------
# DATABASE PATH & CONNECTION
# -------------------------------------------------
def get_db_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "app.db"
    return Path(__file__).resolve().parent.parent / "app.db"

DB_PATH = get_db_path()

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# -------------------------------------------------
# INITIALIZATION
# -------------------------------------------------
def initialize_database():
    """Create core tables if missing."""
    with db_cursor() as cur:
        # Posts
        cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
        """)
        # FTS
        cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts
        USING fts5(title, content)
        """)
        # Users
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','guest'))
        )
        """)

# -------------------------------------------------
# USER MANAGEMENT
# -------------------------------------------------
def create_user(username, password, role="guest"):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )

def verify_user(username, password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password_hash)
        )
        row = cur.fetchone()
        if row:
            return {"id": row["id"], "username": row["username"], "role": row["role"]}
        return None

# -------------------------------------------------
# POSTS MANAGEMENT
# -------------------------------------------------
def add_post(title: str, content: str):
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO posts (title, content) VALUES (?, ?)",
            (title, content)
        )
        post_id = cur.lastrowid
        cur.execute(
            "INSERT INTO posts_fts(rowid, title, content) VALUES (?, ?, ?)",
            (post_id, title, content)
        )

def search_posts_like(keyword: str):
    like_term = f"%{keyword}%"
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM posts WHERE title LIKE ? OR content LIKE ?",
            (like_term, like_term)
        )
        return cur.fetchall()

def search_posts_fts(keyword: str):
    with db_cursor() as cur:
        cur.execute(
            "SELECT rowid AS id, title, content FROM posts_fts WHERE posts_fts MATCH ?",
            (keyword,)
        )
        return cur.fetchall()

def search_posts(keyword: str, mode="fts"):
    return search_posts_fts(keyword) if mode == "fts" else search_posts_like(keyword)

def rebuild_fts():
    with db_cursor() as cur:
        cur.execute("DELETE FROM posts_fts")
        cur.execute("INSERT INTO posts_fts(rowid, title, content) SELECT id, title, content FROM posts")

# -------------------------------------------------
# GENERIC SEARCH UTILITIES
# -------------------------------------------------
def search_column(table: str, column: str, keyword: str):
    """
    Generic column search for any table (single column).
    Example: search_column("users", "username", "john")
    """
    like_term = f"%{keyword}%"
    with db_cursor() as cur:
        query = f"SELECT * FROM {table} WHERE {column} LIKE ?"
        cur.execute(query, (like_term,))
        return cur.fetchall()

def search_table(table: str, keyword: str):
    """
    Advanced search: search all columns of a table automatically (case-insensitive).
    Example:
        search_table("users", "john")
        search_table("posts", "database")
    """
    keyword_term = f"%{keyword}%"
    with db_cursor() as cur:
        # Get all columns
        cur.execute(f"PRAGMA table_info({table})")
        columns = [row["name"] for row in cur.fetchall()]
        if not columns:
            raise ValueError(f"Table '{table}' does not exist or has no columns.")
        # Build dynamic WHERE clause
        where_clause = " OR ".join([f"LOWER({col}) LIKE LOWER(?)" for col in columns])
        params = [keyword_term] * len(columns)
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        cur.execute(query, params)
        return cur.fetchall()

# -------------------------------------------------
# IMPORTER / FILE HANDLING
# -------------------------------------------------
class Importer:
    """
    Handles file path input for import. Works with Pygame UI.
    """
    def __init__(self):
        self.FONT = None
        self.BIG = None
        self.active = False
        self.done = False
        self.selected_path = None
        self.buffer = ""
        self.error = None
        self.BG = (20, 20, 26)
        self.PANEL = (50, 50, 60)
        self.TEXT = (230, 230, 230)
        self.HILITE = (255, 200, 80)
        self.ERROR = (220, 80, 80)

    def _ensure_fonts(self):
        if not self.FONT:
            self.FONT = pygame.font.SysFont(None, 22)
            self.BIG = pygame.font.SysFont(None, 26)

    def open(self):
        self._ensure_fonts()
        self.active = True
        self.done = False
        self.selected_path = None
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

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.reset()
            elif e.key == pygame.K_RETURN:
                path = self.buffer.strip()
                if os.path.isfile(path):
                    self.selected_path = path
                    self.done = True
                    self.active = False
                    pygame.key.stop_text_input()
                else:
                    self.error = "File not found"
            elif e.key == pygame.K_BACKSPACE:
                self.buffer = self.buffer[:-1]
        elif e.type == pygame.TEXTINPUT:
            self.buffer += e.text
            self.error = None

    def draw(self, screen):
        if not self.active:
            return
        self._ensure_fonts()
        w, h = screen.get_size()
        panel = pygame.Rect(w//2 - 260, h//2 - 90, 520, 180)
        pygame.draw.rect(screen, self.BG, panel)
        pygame.draw.rect(screen, self.HILITE, panel, 2)
        screen.blit(self.BIG.render("Import File", True, self.HILITE), (panel.x + 16, panel.y + 12))
        screen.blit(self.FONT.render("Enter file path and press Enter:", True, self.TEXT), (panel.x + 16, panel.y + 48))
        pygame.draw.rect(screen, self.PANEL, (panel.x + 16, panel.y + 72, panel.width - 32, 32))
        screen.blit(self.FONT.render(self.buffer, True, self.TEXT), (panel.x + 22, panel.y + 80))
        screen.blit(self.FONT.render("Enter = confirm | Esc = cancel", True, (160,160,160)), (panel.x + 16, panel.y + 120))
        if self.error:
            screen.blit(self.FONT.render(self.error, True, self.ERROR), (panel.x + 16, panel.y + 148))