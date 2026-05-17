
import sqlite3
import os
from src.utils.logger import log_info

DB_PATH = os.path.join(os.path.dirname(__file__), "../../database/webhook.db")

def get_connection():
    """Return a new SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  
    conn.execute("PRAGMA journal_mode=WAL")  
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # EVENTS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id           TEXT PRIMARY KEY,
            type         TEXT NOT NULL,
            payload      TEXT NOT NULL,
            webhook_url  TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'pending',
            retry_count  INTEGER NOT NULL DEFAULT 0,
            next_retry_at DATETIME,
            created_at   DATETIME NOT NULL
        )
    """)

   
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id       TEXT NOT NULL,
            attempted_at   DATETIME NOT NULL,
            http_status    INTEGER,
            outcome        TEXT NOT NULL,
            error_message  TEXT,
            delivery_time_ms INTEGER,
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)

    conn.commit()
    conn.close()
    log_info("Database initialized successfully.")
