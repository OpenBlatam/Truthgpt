import sqlite3
import threading
from typing import Optional

class DatabaseConnection:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = "truthgpt_unified.db"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseConnection, cls).__new__(cls)
                cls._instance.db_path = db_path
                cls._instance.conn = sqlite3.connect(db_path, check_same_thread=False)
                cls._instance.conn.row_factory = sqlite3.Row
                cls._instance._initialize_tables()
            return cls._instance

    def _initialize_tables(self):
        cursor = self.conn.cursor()
        # Initialize unified tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                key TEXT,
                value TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        return self.conn
