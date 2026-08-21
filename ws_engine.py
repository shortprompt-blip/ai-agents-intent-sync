import asyncio
import json
import websockets

CONNECTED_PEERS = set()
TEAM_STATE = {}  # { "dev_id": { "dirty_files": [...], "current_intent": "..." } }

async def handler(websocket):
    CONNECTED_PEERS.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            
            # Sincronizzazione file modificati localmente
            if msg_type == "STATE_UPDATE":
                TEAM_STATE[data["dev_id"]] = data["payload"]
                
            # Verifica preventiva prima della generazione AI
            elif msg_type == "CHECK_INTENT":
                target_file = data["target_file"]
                conflict = None
                
                for dev, state in TEAM_STATE.items():
                    if dev != data["dev_id"] and target_file in state.get("dirty_files", []):
                        conflict = dev
                        break
                
                response = {
                    "type": "INTENT_RESPONSE",
                    "allowed": conflict is None,
                    "conflicting_dev": conflict
                }
                await websocket.send(json.dumps(response))
                
    finally:
        CONNECTED_PEERS.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Mantiene il server attivo

if __name__ == "__main__":
    asyncio.run(main())
