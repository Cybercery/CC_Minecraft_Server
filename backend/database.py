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

        if current_version < 3:
            # Apply phase 4 migration: minecraft_links and verification_sessions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS minecraft_links (
                    uid TEXT PRIMARY KEY,
                    minecraft_uuid TEXT UNIQUE NOT NULL,
                    minecraft_username TEXT NOT NULL,
                    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS verification_sessions (
                    code_hash TEXT PRIMARY KEY,
                    uid TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used INTEGER DEFAULT 0,
                    FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
                )
            """)
            conn.execute("INSERT INTO schema_version (version, description) VALUES (3, 'Minecraft links and verification sessions')")
            current_version = 3

        if current_version < 4:
            # Apply phase 5 migration: backups
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    s3_key TEXT UNIQUE NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    checksum_sha256 TEXT NOT NULL,
                    backup_type TEXT NOT NULL DEFAULT 'manual',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by_uid TEXT,
                    created_by_email TEXT,
                    status TEXT NOT NULL DEFAULT 'completed',
                    metadata TEXT
                )
            """)
            conn.execute("INSERT INTO schema_version (version, description) VALUES (4, 'Backups management schema')")
            current_version = 4

        if current_version < 5:
            # Apply phase 6 migration: server_metrics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS server_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_percent REAL NOT NULL,
                    memory_bytes INTEGER NOT NULL,
                    memory_percent REAL NOT NULL,
                    disk_used_bytes INTEGER NOT NULL,
                    disk_total_bytes INTEGER NOT NULL,
                    disk_percent REAL NOT NULL,
                    online_players INTEGER NOT NULL,
                    is_running INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON server_metrics(timestamp)")
            conn.execute("INSERT INTO schema_version (version, description) VALUES (5, 'Metrics and historical tracking schema')")
            current_version = 5

        if current_version < 6:
            # Apply phase 8 migration: alerts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'warning',
                    message TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    acknowledged INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("INSERT INTO schema_version (version, description) VALUES (6, 'Alerts schema')")
            current_version = 6
            
# Wait to initialize DB until app startup or manually called to avoid issues during module import, 
# but it's safe if it creates cloud.db in /data as long as /data is writable.
init_db()
