import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv("INTENT_SYNC_DB", "intent_sync.db")

def init_db():
    """Inizializza lo schema SQLite minimale per M1."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS intents (
            id TEXT PRIMARY KEY,
            repository_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            operation TEXT CHECK(operation IN ('read','modify','refactor','delete','rename')),
            description TEXT,
            status TEXT CHECK(status IN ('ACTIVE','EXPIRED','RELEASED')) DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS intent_files (
            intent_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            FOREIGN KEY(intent_id) REFERENCES intents(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_intents_repo_status ON intents(repository_id, status);
        """)
        conn.commit()

@contextmanager
def get_db():
    """Context manager per connessioni sicure al DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permette l'accesso ai risultati come dizionari
    try:
        yield conn
    finally:
        conn.close()
      
