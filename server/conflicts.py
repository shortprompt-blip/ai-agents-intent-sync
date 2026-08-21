import os
from pathlib import Path

# Matrice delle regole di conflitto. True = CONFLITTO, False = PERMESSO
# Chiave: (Nuova Operazione, Operazione Attiva)
CONFLICT_MATRIX = {
    ('read', 'read'): False,
    ('read', 'modify'): False,
    ('modify', 'read'): False,
    ('modify', 'modify'): True,
    ('modify', 'delete'): True,
    ('delete', 'modify'): True,
    ('refactor', 'modify'): True,
    ('modify', 'refactor'): True,
    ('delete', 'read'): True,
    ('read', 'delete'): True,
    ('rename', 'modify'): True,
    ('modify', 'rename'): True,
    ('refactor', 'refactor'): True,
}

def is_path_overlap(path1: str, path2: str) -> bool:
    """
    Verifica overlap usando pathlib per rispettare i boundary delle directory.
    Previene il bug per cui 'src/auth/*' colliderebbe erroneamente con 'src/authentication.py'.
    """
    p1 = Path(os.path.normpath(path1))
    p2 = Path(os.path.normpath(path2))
    
    if p1 == p2:
        return True
        
    # Se p1 è una wildcard (es: src/auth/*)
    if p1.name == '*':
        p1_parent = p1.parent
        # True se p2 è dentro la directory genitore di p1
        if p1_parent in p2.parents or p1_parent == p2:
            return True
            
    # Se p2 è una wildcard (es: src/auth/*)
    if p2.name == '*':
        p2_parent = p2.parent
        # True se p1 è dentro la directory genitore di p2
        if p2_parent in p1.parents or p2_parent == p1:
            return True
            
    return False

def check_conflicts(new_op: str, new_files: list, active_intents: list) -> list:
    """
    Valuta una nuova richiesta rispetto a tutte le lease attive.
    Ritorna una lista di dizionari con i conflitti rilevati (vuota se tutto ok).
    """
    conflicts = []
    
    for intent in active_intents:
        active_op = intent['operation']
        
        # 1. Controlla la matrice delle operazioni
        has_op_conflict = CONFLICT_MATRIX.get((new_op, active_op), True) # Default a True (conflitto) per sicurezza su ops sconosciute
        
        if not has_op_conflict:
            continue
            
        # 2. Controlla l'overlap dei file (Gerarchia)
        overlapping_files = []
        for n_file in new_files:
            for a_file in intent['files']:
                if is_path_overlap(n_file, a_file):
                    overlapping_files.append((n_file, a_file))
                    
        if overlapping_files:
            conflicts.append({
                "intent_id": intent['id'],
                "agent_id": intent['agent_id'],
                "operation": active_op,
                "description": intent['description'],
                "overlapping_files": overlapping_files
            })
            
    return conflicts
  
