import socket
import threading

MULTICAST_GROUP = '224.1.1.1'
PORT = 5007

def listen_as_leader(local_ip: str):
    """In ascolto in background per rispondere ai nuovi client nella LAN/VPN."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))
    
    mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0")
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data == b"DISCOVER_INTENT_SYNC":
                sock.sendto(f"LEADER_IP:{local_ip}".encode(), addr)
        except Exception:
            break

def find_or_become_leader():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1.5)
    
    sock.sendto(b"DISCOVER_INTENT_SYNC", (MULTICAST_GROUP, PORT))
    
    try:
        data, _ = sock.recvfrom(1024)
        if data.startswith(b"LEADER_IP"):
            leader_ip = data.decode().split(":")[1]
            return {"role": "client", "host": leader_ip}
    except socket.timeout:
        pass
        
    # Nessun leader trovato: questo nodo diventa Leader e avvia il responder UDP
    local_ip = socket.gethostbyname(socket.gethostname())
    threading.Thread(target=listen_as_leader, args=(local_ip,), daemon=True).start()
    return {"role": "leader", "host": "127.0.0.1"}
