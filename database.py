# todo_python_app/database.py
import sqlite3
import uuid
from typing import List, Dict

DB_PATH = "offline.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      description TEXT,
      completed INTEGER DEFAULT 0,
      synced INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

def add_task_local(title: str, description: str = "") -> str:
    """Add a task to local SQLite and return its id."""
    task_id = str(uuid.uuid4())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (id, title, description, completed, synced) VALUES (?, ?, ?, 0, 0)",
        (task_id, title, description),
    )
    conn.commit()
    conn.close()
    return task_id

def list_tasks_local() -> List[Dict]:
    """Return list of local tasks as dicts (most recent first)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, completed, synced FROM tasks ORDER BY rowid DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_task_local(task_id: str, title: str = None, description: str = None, completed: bool = None):
    conn = get_connection()
    cur = conn.cursor()
    if title is not None:
        cur.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
    if description is not None:
        cur.execute("UPDATE tasks SET description = ? WHERE id = ?", (description, task_id))
    if completed is not None:
        cur.execute("UPDATE tasks SET completed = ? WHERE id = ?", (1 if completed else 0, task_id))
    # mark unsynced after update
    cur.execute("UPDATE tasks SET synced = 0 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def delete_task_local(task_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def mark_task_synced(task_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET synced = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def update_task_local(task_id: str, title: str = None, description: str = None, completed: bool = None):
    conn = get_connection()
    cur = conn.cursor()
    if title is not None:
        cur.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
    if description is not None:
        cur.execute("UPDATE tasks SET description = ? WHERE id = ?", (description, task_id))
    if completed is not None:
        cur.execute("UPDATE tasks SET completed = ? WHERE id = ?", (1 if completed else 0, task_id))
    # mark unsynced after update
    cur.execute("UPDATE tasks SET synced = 0 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
def clear_all_tasks():
    """Remove all tasks from local SQLite table."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()
