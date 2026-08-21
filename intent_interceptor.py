import asyncio
import json
import sys
import websockets
from discovery import find_or_become_leader

async def check_intent_ws(dev_id: str, prompt: str, target_file: str):
    node_info = find_or_become_leader()
    host = "127.0.0.1" if node_info["role"] == "leader" else node_info["host"]
    uri = f"ws://{host}:8765"

    try:
        async with websockets.connect(uri, timeout=2) as websocket:
            payload = {
                "type": "CHECK_INTENT",
                "dev_id": dev_id,
                "prompt": prompt,
                "target_file": target_file
            }
            await websocket.send(json.dumps(payload))
            response = json.loads(await websocket.recv())

            if not response.get("allowed"):
                print(f"⚠️ BLOCCO AI: Il collega '{response['conflicting_dev']}' ha modifiche attive su {target_file}!")
                sys.exit(1)
            
            print("✅ Nessuna collisione. Generazione autorizzata.")
    except Exception as e:
        print(f"⚠️ Registro non raggiungibile ({e}). Proseguo in modalità isolata.")

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        asyncio.run(check_intent_ws(sys.argv[1], sys.argv[2], sys.argv[3]))
