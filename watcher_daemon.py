import asyncio
import json
import subprocess
import time
import websockets
from discovery import find_or_become_leader

def get_dirty_files():
    try:
        output = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8")
        return [line.strip().split()[-1] for line in output.splitlines() if line]
    except Exception:
        return []

async def sync_loop(dev_id: str):
    node_info = find_or_become_leader()
    host = "127.0.0.1" if node_info["role"] == "leader" else node_info["host"]
    uri = f"ws://{host}:8765"

    while True:
        try:
            async with websockets.connect(uri) as ws:
                while True:
                    dirty_files = get_dirty_files()
                    payload = {
                        "type": "STATE_UPDATE",
                        "dev_id": dev_id,
                        "payload": {
                            "dirty_files": dirty_files,
                            "timestamp": time.time()
                        }
                    }
                    await ws.send(json.dumps(payload))
                    await asyncio.sleep(5)
        except Exception:
            await asyncio.sleep(3)  # Riprova la connessione se cade

def start_watcher(dev_id: str):
    asyncio.run(sync_loop(dev_id))
