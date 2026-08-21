import uuid
from datetime import datetime, timedelta, timezone
from server.db import get_db
from server.conflicts import check_conflicts

def expire_stale_leases():
    """Trova le lease scadute (TTL superato) e ne cambia lo stato in EXPIRED."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE intents 
            SET status = 'EXPIRED' 
            WHERE status = 'ACTIVE' AND expires_at <= ?
        """, (now,))
        conn.commit()

def get_active_intents(repository_id: str) -> list:
    """Recupera tutte le lease attive per un repository (compresi i file associati)."""
    expire_stale_leases() # Auto-pulizia prima della lettura
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.id, i.agent_id, i.operation, i.description 
            FROM intents i 
            WHERE i.repository_id = ? AND i.status = 'ACTIVE'
        """, (repository_id,))
        
        intents = [dict(row) for row in cursor.fetchall()]
        
        # Recupera i file per ogni intent
        for intent in intents:
            cursor.execute("SELECT file_path FROM intent_files WHERE intent_id = ?", (intent['id'],))
            intent['files'] = [row['file_path'] for row in cursor.fetchall()]
            
        return intents

def acquire_lease(repository_id: str, agent_id: str, operation: str, description: str, files: list, ttl_seconds: int = 900) -> dict:
    """Richiede una nuova lease. Torna ALLOW con i dati o CONFLICT con i dettagli."""
    active_intents = get_active_intents(repository_id)
    
    # Passa al Conflict Engine
    conflicts = check_conflicts(operation, files, active_intents)
    
    if conflicts:
        return {
            "decision": "conflict",
            "conflicts": conflicts
        }
        
    # Nessun conflitto: Registrazione della Lease
    intent_id = f"intent_{uuid.uuid4().hex[:8]}"
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO intents (id, repository_id, agent_id, operation, description, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (intent_id, repository_id, agent_id, operation, description, expires_at))
        
        for file_path in files:
            cursor.execute("""
                INSERT INTO intent_files (intent_id, file_path) VALUES (?, ?)
            """, (intent_id, file_path))
            
        conn.commit()
        
    return {
        "decision": "allow",
        "intent_id": intent_id,
        "expires_at": expires_at
    }

def release_lease(intent_id: str) -> bool:
    """Rilascia esplicitamente una lease prima della scadenza del TTL."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE intents SET status = 'RELEASED' WHERE id = ? AND status = 'ACTIVE'", (intent_id,))
        conn.commit()
        return cursor.rowcount > 0

def renew_lease(intent_id: str, extra_ttl_seconds: int = 900) -> dict:
    """Rinnova il TTL di una lease ancora attiva."""
    new_expires = (datetime.now(timezone.utc) + timedelta(seconds=extra_ttl_seconds)).isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE intents 
            SET expires_at = ? 
            WHERE id = ? AND status = 'ACTIVE'
        """, (new_expires, intent_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            return {"error": "Lease not found or no longer active"}
            
    return {"status": "renewed", "expires_at": new_expires}
  
