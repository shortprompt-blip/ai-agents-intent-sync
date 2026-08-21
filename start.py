import asyncio
import threading
from discovery import find_or_become_leader
from ws_engine import main as start_ws_server
from watcher_daemon import sync_local_state

def run_node():
    node_info = find_or_become_leader()
    
    # Se la rete non ha un leader, avvia il server WS locale
    if node_info["role"] == "leader":
        print("👑 Questo nodo è stato eletto LEADER di rete. Avvio Server WebSocket...")
        threading.Thread(target=lambda: asyncio.run(start_ws_server()), daemon=True).start()
    else:
        print(f"🔗 Connesso al LEADER di rete su IP: {node_info['host']}")

    # Avvia il daemon che monitora il git working tree
    print("👀 Daemon di monitoraggio 'dirty files' attivo...")
    sync_local_state()

if __name__ == "__main__":
    run_node()
