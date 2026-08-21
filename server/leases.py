import uuid
from datetime import datetime, timedelta, timezone
from server.db import get_db
from server.conflicts import check_conflicts

def expire_stale_leases():
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute("UPDATE intents SET status = 'EXPIRED' WHERE status = 'ACTIVE' AND expires_at <= ?", (now,))
        conn.commit()

def get_active_intents_internal(cursor, repository_id: str) -> list:
    """Funzione helper per leggere gli intent all'interno di una transazione esistente."""
    cursor.execute("""
        SELECT i.id, i.agent_id, i.operation, i.description 
        FROM intents i 
        WHERE i.repository_id = ? AND i.status = 'ACTIVE'
    """, (repository_id,))
    
    intents = [dict(row) for row in cursor.fetchall()]
    for intent in intents:
        cursor.execute("SELECT file_path FROM intent_files WHERE intent_id = ?", (intent['id'],))
        intent['files'] = [row['file_path'] for row in cursor.fetchall()]
    return intents

def get_active_intents(repository_id: str) -> list:
    expire_stale_leases()
    with get_db() as conn:
        return get_active_intents_internal(conn.cursor(), repository_id)

def acquire_lease(repository_id: str, agent_id: str, operation: str, description: str, files: list, ttl_seconds: int = 900) -> dict:
    expire_stale_leases()
    
    with get_db() as conn:
        cursor = conn.cursor()
        # TRANSACTION LOCK: Impedisce ad altri thread/processi di leggere o scrivere concorrentemente
        cursor.execute("BEGIN EXCLUSIVE")
        
        try:
            active_intents = get_active_intents_internal(cursor, repository_id)
            conflicts = check_conflicts(operation, files, active_intents)
            
            if conflicts:
                conn.rollback()
                return {"decision": "conflict", "conflicts": conflicts}
                
            intent_id = f"intent_{uuid.uuid4().hex[:8]}"
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
            
            cursor.execute("""
                INSERT INTO intents (id, repository_id, agent_id, operation, description, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (intent_id, repository_id, agent_id, operation, description, expires_at))
            
            for file_path in files:
                cursor.execute("INSERT INTO intent_files (intent_id, file_path) VALUES (?, ?)", (intent_id, file_path))
                
            conn.commit()
            return {"decision": "allow", "intent_id": intent_id, "expires_at": expires_at}
            
        except Exception as e:
            conn.rollback()
            raise e

def release_lease(intent_id: str, agent_id: str) -> bool:
    """Rilascia la lease SOLO se l'agent_id corrisponde all'owner."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE intents SET status = 'RELEASED' 
            WHERE id = ? AND agent_id = ? AND status = 'ACTIVE'
        """, (intent_id, agent_id))
        conn.commit()
        return cursor.rowcount > 0

def renew_lease(intent_id: str, agent_id: str, extra_ttl_seconds: int = 900) -> dict:
    """Rinnova la lease SOLO se l'agent_id corrisponde all'owner."""
    new_expires = (datetime.now(timezone.utc) + timedelta(seconds=extra_ttl_seconds)).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE intents SET expires_at = ? 
            WHERE id = ? AND agent_id = ? AND status = 'ACTIVE'
        """, (new_expires, intent_id, agent_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            return {"error": "Lease not found, expired, or unauthorized access"}
            
    return {"status": "renewed", "expires_at": new_expires}
