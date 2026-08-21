from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from contextlib import asynccontextmanager

from server.db import init_db
from server.leases import acquire_lease, release_lease, renew_lease, get_active_intents

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inizializza il DB SQLite all'avvio del server
    init_db()
    yield

app = FastAPI(title="Agent Coordination Protocol", version="2.0.0", lifespan=lifespan)

# --- Modelli Pydantic per validazione input ---
class AcquireRequest(BaseModel):
    repository_id: str
    agent_id: str
    operation: str = Field(..., pattern="^(read|modify|refactor|delete|rename)$")
    description: str
    files: List[str]
    ttl: int = 900

class RenewRequest(BaseModel):
    ttl: int = 900

# --- Endpoints ---

@app.get("/v1/health")
def health_check():
    """Usato dalla CLI (doctor) per verificare se il server è attivo."""
    return {"status": "ok", "service": "intent-sync-server"}

@app.post("/v1/intents")
def api_acquire(req: AcquireRequest):
    """L'agente richiede una lease per operare su un set di file."""
    result = acquire_lease(
        repository_id=req.repository_id,
        agent_id=req.agent_id,
        operation=req.operation,
        description=req.description,
        files=req.files,
        ttl_seconds=req.ttl
    )
    return result

@app.post("/v1/intents/{intent_id}/renew")
def api_renew(intent_id: str, req: RenewRequest):
    """Rinnova il TTL di un intento attivo."""
    result = renew_lease(intent_id, extra_ttl_seconds=req.ttl)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.delete("/v1/intents/{intent_id}")
def api_release(intent_id: str):
    """L'agente rilascia la lease dopo aver committato."""
    success = release_lease(intent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Intent not found or already released/expired")
    return {"status": "released", "intent_id": intent_id}

@app.get("/v1/intents")
def api_list_intents(repository_id: str):
    """Restituisce lo stato corrente del repo (utile per Dashboard e Debug)."""
    intents = get_active_intents(repository_id)
    return {"repository_id": repository_id, "active_intents": intents}

if __name__ == "__main__":
    uvicorn.run("server.api:app", host="0.0.0.0", port=8000, reload=True)
  
