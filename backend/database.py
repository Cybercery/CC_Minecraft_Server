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
            current_version = 1
            
        if current_version < 2:
            # Apply phase 3 migration: users and audit_logs
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    uid TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL DEFAULT 'User',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid TEXT,
                    email TEXT,
                    action TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("INSERT INTO schema_version (version, description) VALUES (2, 'Users and audit logs')")
            current_version = 2
            
# Wait to initialize DB until app startup or manually called to avoid issues during module import, 
# but it's safe if it creates cloud.db in /data as long as /data is writable.
init_db()
