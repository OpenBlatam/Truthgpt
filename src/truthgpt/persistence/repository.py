from typing import List, Optional
from truthgpt.persistence.connection import DatabaseConnection
from truthgpt.persistence.models import MemoryEntry, SecurityEvent

class UnifiedRepository:
    def __init__(self):
        self.db = DatabaseConnection()

    def add_memory(self, agent_id: str, key: str, value: str) -> int:
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "INSERT INTO memory (agent_id, key, value) VALUES (?, ?, ?)",
            (agent_id, key, value)
        )
        self.db.get_connection().commit()
        return cursor.lastrowid

    def get_memories(self, agent_id: str) -> List[MemoryEntry]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM memory WHERE agent_id = ?", (agent_id,))
        rows = cursor.fetchall()
        return [MemoryEntry(id=row['id'], agent_id=row['agent_id'], key=row['key'], value=row['value'], timestamp=row['timestamp']) for row in rows]

    def log_security_event(self, event_type: str, details: str) -> int:
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "INSERT INTO security_events (event_type, details) VALUES (?, ?)",
            (event_type, details)
        )
        self.db.get_connection().commit()
        return cursor.lastrowid

    def get_security_events(self) -> List[SecurityEvent]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM security_events ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        return [SecurityEvent(id=row['id'], event_type=row['event_type'], details=row['details'], timestamp=row['timestamp']) for row in rows]
