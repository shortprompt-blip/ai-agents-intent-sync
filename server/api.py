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

# --- Modelli Pydantic ---
class AcquireRequest(BaseModel):
    repository_id: str
    agent_id: str
    operation: str = Field(..., pattern="^(read|modify|refactor|delete|rename)$")
    description: str
    files: List[str]
    ttl: int = 900

class RenewRequest(BaseModel):
    ttl: int = 900
    agent_id: str  # Aggiunto per verifica ownership

# --- Endpoints ---

@app.get("/v1/health")
def health_check():
    return {"status": "ok", "service": "intent-sync-server"}

@app.post("/v1/intents")
def api_acquire(req: AcquireRequest):
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
    result = renew_lease(intent_id, agent_id=req.agent_id, extra_ttl_seconds=req.ttl)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result["error"])
    return result

@app.delete("/v1/intents/{intent_id}")
def api_release(intent_id: str, agent_id: str):
    """Richiede agent_id come query parameter (?agent_id=...) per validare l'ownership."""
    success = release_lease(intent_id, agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Intent not found, already released, or unauthorized (wrong agent_id)"
        )
    return {"status": "released", "intent_id": intent_id}

@app.get("/v1/intents")
def api_list_intents(repository_id: str):
    intents = get_active_intents(repository_id)
    return {"repository_id": repository_id, "active_intents": intents}

if __name__ == "__main__":
    uvicorn.run("server.api:app", host="0.0.0.0", port=8000, reload=True)
