import socket
import time

MULTICAST_GROUP = '224.1.1.1'
PORT = 5007

def find_or_become_leader():
    """Cerca un server attivo in LAN/VPN. Se non risponde nessuno entro 2 sec, diventa Leader."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(2.0)
    
    # Invia ping broadcast
    sock.sendto(b"DISCOVER_INTENT_SYNC", (MULTICAST_GROUP, PORT))
    
    try:
        data, addr = sock.recvfrom(1024)
        if data.startswith(b"LEADER_IP"):
            leader_ip = data.decode().split(":")[1]
            return {"role": "client", "host": leader_ip}
    except socket.timeout:
        pass
        
    return {"role": "leader", "host": "0.0.0.0"}
  
