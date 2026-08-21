import argparse
import json
import urllib.request
import urllib.error
import urllib.parse
import sys
import os
import subprocess

SERVER_URL = os.getenv("INTENT_SYNC_URL", "http://localhost:8000")

def get_repo_id():
    try:
        remote = subprocess.check_output(["git", "remote", "get-url", "origin"], stderr=subprocess.DEVNULL).decode().strip()
        return remote.split('/')[-1].replace('.git', '')
    except Exception:
        return os.path.basename(os.path.abspath(os.getcwd()))

def make_request(method, endpoint, payload=None):
    url = f"{SERVER_URL}{endpoint}"
    data = json.dumps(payload).encode('utf-8') if payload else None
    headers = {'Content-Type': 'application/json'} if payload else {}
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode()
        print(f"Server Error ({e.code}): {error_msg}")
        sys.exit(1)
    except Exception as e:
        print(f"Connection Error: Impossibile contattare {SERVER_URL}. Il server è avviato?")
        sys.exit(1)

def cmd_acquire(args):
    repo_id = args.repo or get_repo_id()
    files = [f.strip() for f in args.files.split(",")]
    
    payload = {
        "repository_id": repo_id,
        "agent_id": args.agent,
        "operation": args.op,
        "description": args.intent,
        "files": files,
        "ttl": args.ttl
    }
    
    res = make_request("POST", "/v1/intents", payload)
    
    if res.get("decision") == "allow":
        print(f"✅ ALLOWED: Lease acquisita. ID: {res['intent_id']} (Scade il {res['expires_at']})")
    else:
        print("❌ CONFLICT: Conflitto rilevato con altre lease attive:")
        for conflict in res.get("conflicts", []):
            print(f"  - Agente [{conflict['agent_id']}] sta eseguendo '{conflict['operation']}'")
            print(f"    Intent: {conflict['description']}")
            print(f"    File in overlap: {conflict['overlapping_files']}")
        sys.exit(1)

def cmd_release(args):
    query = urllib.parse.urlencode({"agent_id": args.agent})
    res = make_request("DELETE", f"/v1/intents/{args.intent_id}?{query}")
    print(f"✅ Rilasciato con successo: {args.intent_id}")

def cmd_renew(args):
    payload = {"ttl": args.ttl, "agent_id": args.agent}
    res = make_request("POST", f"/v1/intents/{args.intent_id}/renew", payload)
    print(f"✅ Rinnovato. Nuova scadenza: {res['expires_at']}")

def cmd_status(args):
    repo_id = args.repo or get_repo_id()
    res = make_request("GET", f"/v1/intents?repository_id={repo_id}")
    intents = res.get("active_intents", [])
    
    print(f"📊 Stato Repository: {repo_id}")
    print(f"Lease attive: {len(intents)}\n")
    for i in intents:
        print(f"[{i['agent_id']}] - {i['operation'].upper()} (ID: {i['id']})")
        print(f"  Intent: {i['description']}")
        print(f"  Files: {', '.join(i['files'])}\n")

def cmd_doctor(args):
    print("🩺 Intent-Sync Doctor")
    print(f"Controllando il server su {SERVER_URL}...")
    try:
        make_request("GET", "/v1/health")
        print("✅ Server API raggiungibile.")
    except Exception:
        print("❌ Impossibile raggiungere il Server API.")
        
    repo = get_repo_id()
    print(f"✅ Repository inferito: {repo}")

def main():
    parser = argparse.ArgumentParser(prog="intent-sync", description="AI Agents Intent Synchronization CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ACQUIRE
    p_acquire = subparsers.add_parser("acquire", help="Richiede una lease prima di modificare i file")
    p_acquire.add_argument("--files", required=True, help="Lista file separati da virgola")
    p_acquire.add_argument("--intent", required=True, help="Descrizione dell'operazione")
    p_acquire.add_argument("--op", default="modify", choices=['read', 'modify', 'refactor', 'delete', 'rename'], help="Tipo operazione")
    p_acquire.add_argument("--agent", default=os.getenv("USER", "unknown_agent"), help="ID Agente")
    p_acquire.add_argument("--repo", help="ID repository")
    p_acquire.add_argument("--ttl", type=int, default=900, help="Time to live in sec")
    p_acquire.set_defaults(func=cmd_acquire)

    # RELEASE
    p_release = subparsers.add_parser("release", help="Rilascia una lease")
    p_release.add_argument("intent_id", help="ID dell'intento")
    p_release.add_argument("--agent", default=os.getenv("USER", "unknown_agent"), help="ID Agente (deve essere l'owner)")
    p_release.set_defaults(func=cmd_release)

    # RENEW
    p_renew = subparsers.add_parser("renew", help="Rinnova il tempo di una lease")
    p_renew.add_argument("intent_id", help="ID dell'intento")
    p_renew.add_argument("--ttl", type=int, default=900, help="Tempo aggiuntivo in sec")
    p_renew.add_argument("--agent", default=os.getenv("USER", "unknown_agent"), help="ID Agente (deve essere l'owner)")
    p_renew.set_defaults(func=cmd_renew)

    # STATUS
    p_status = subparsers.add_parser("status", help="Mostra le lease attive")
    p_status.add_argument("--repo", help="ID repository")
    p_status.set_defaults(func=cmd_status)

    # DOCTOR
    p_doctor = subparsers.add_parser("doctor", help="Verifica connessione e stato")
    p_doctor.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
