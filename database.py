import os
import sqlite3
from contextlib import closing

from config import DB_PATH


def init_db() -> None:
    """Create the database file and table if they don't exist yet.

    CREATE TABLE IF NOT EXISTS silently skips existing tables, which is fine
    here since there's only ever one table — but keep this pattern in mind
    if columns are added later (a migration/ALTER step would be needed).
    """
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS message_map (
                admin_message_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                user_message_id INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()


def save_mapping(admin_message_id: int, user_id: int, user_message_id: int) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO message_map (admin_message_id, user_id, user_message_id) "
            "VALUES (?, ?, ?)",
            (admin_message_id, user_id, user_message_id),
        )
        conn.commit()


def get_user_for_admin_message(admin_message_id: int) -> int | None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT user_id FROM message_map WHERE admin_message_id = ?",
            (admin_message_id,),
        ).fetchone()
        return row[0] if row else None
