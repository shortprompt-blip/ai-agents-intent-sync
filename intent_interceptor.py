import json
import sys
import urllib.request

CHECK_URL = "http://localhost:8000/check_intent"

def check_collision(dev_id: str, prompt: str, target_file: str):
    """Verifica se un altro sviluppatore ha il file aperto o un intento simile."""
    payload = json.dumps({
        "dev_id": dev_id,
        "prompt": prompt,
        "target_file": target_file
    }).encode("utf-8")
    
    req = urllib.request.Request(CHECK_URL, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("collision_detected"):
                print(f"⚠️ BLOCCO AI: Il collega {result['conflicting_dev']} sta già modificando {target_file}!")
                sys.exit(1)
            print("✅ Nessuna collisione rilevata. Generazione autorizzata.")
    except Exception:
        print("⚠️ Registro di team non raggiungibile. Proseguo in modalità isolata.")

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        check_collision(sys.argv[1], sys.argv[2], sys.argv[3])
