import json
import subprocess
import time
import urllib.request

REGISTRY_URL = "http://localhost:8000/register"  # Endpoint di team condiviso
DEV_ID = "dev_alpha"

def get_dirty_files():
    """Rileva i file modificati localmente non ancora committati."""
    try:
        output = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8")
        return [line.strip().split()[-1] for line in output.splitlines() if line]
    except Exception:
        return []

def sync_local_state():
    """Invia lo stato dei file dirty al registro di team ogni 5 secondi."""
    while True:
        dirty_files = get_dirty_files()
        payload = json.dumps({
            "dev_id": DEV_ID,
            "dirty_files": dirty_files,
            "timestamp": time.time()
        }).encode("utf-8")
        
        req = urllib.request.Request(REGISTRY_URL, data=payload, headers={'Content-Type': 'application/json'})
        try:
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass  # Fail silent se il registro non è momentaneamente raggiungibile
        time.sleep(5)

if __name__ == "__main__":
    sync_local_state()
  
