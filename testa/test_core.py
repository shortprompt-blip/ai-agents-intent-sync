import pytest
from concurrent.futures import ThreadPoolExecutor
import os
from server.db import init_db, get_db
from server.leases import acquire_lease, release_lease, get_active_intents
import time

# Usa un DB in memoria per i test
os.environ["INTENT_SYNC_DB"] = ":memory:"

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    # Nessun teardown necessario per :memory:

def test_acquire_and_release_ownership():
    """Testa che solo l'owner possa rilasciare la lease."""
    repo = "test_repo"
    res1 = acquire_lease(repo, "agent_A", "modify", "task", ["src/main.py"])
    assert res1["decision"] == "allow"
    
    # Agente B tenta di rilasciare la lease di Agente A (Deve fallire)
    assert not release_lease(res1["intent_id"], "agent_B")
    
    # Agente A rilascia la propria lease (Deve funzionare)
    assert release_lease(res1["intent_id"], "agent_A")

def test_conflict_detection():
    """Testa l'overlap su matrici e percorsi."""
    repo = "test_repo"
    acquire_lease(repo, "agent_A", "modify", "task", ["src/auth/*"])
    
    # Conflitto diretto dentro la directory
    res2 = acquire_lease(repo, "agent_B", "modify", "task", ["src/auth/session.py"])
    assert res2["decision"] == "conflict"
    
    # NON deve essere conflitto (risolve il bug del prefix test precedente)
    res3 = acquire_lease(repo, "agent_C", "modify", "task", ["src/authentication.py"])
    assert res3["decision"] == "allow"

def test_race_condition():
    """Testa 10 agenti che provano ad acquisire lo stesso file nello stesso millisecondo."""
    repo = "race_repo"
    file_target = ["src/critical.py"]
    
    def worker(agent_id):
        return acquire_lease(repo, agent_id, "modify", "race", file_target)
        
    agents = [f"agent_{i}" for i in range(10)]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(worker, agents))
        
    allowed = [r for r in results if r["decision"] == "allow"]
    conflicts = [r for r in results if r["decision"] == "conflict"]
    
    # Solo UNO deve vincere, gli altri 9 DEVONO fallire in conflitto
    assert len(allowed) == 1
    assert len(conflicts) == 9
