import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "/data/cloud.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    dirname = os.path.dirname(DB_PATH)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    with db_session() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor = conn.execute("SELECT MAX(version) as v FROM schema_version")
        row = cursor.fetchone()
        current_version = row['v'] if row['v'] is not None else 0
        
        # Migrations
        if current_version < 1:
            # Apply phase 1 migration
            conn.execute("INSERT INTO schema_version (version, description) VALUES (1, 'Initial phase 1 schema')")
            
# Wait to initialize DB until app startup or manually called to avoid issues during module import, 
# but it's safe if it creates cloud.db in /data as long as /data is writable.
init_db()
