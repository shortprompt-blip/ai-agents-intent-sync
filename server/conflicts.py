import os

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
    Verifica se due percorsi si sovrappongono.
    Gestisce conflitti diretti (file == file) e conflitti di directory (dir/* overlap con dir/file.py).
    """
    p1 = os.path.normpath(path1)
    p2 = os.path.normpath(path2)
    
    if p1 == p2:
        return True
        
    # Gestione wildcard per le directory (es. src/auth/*)
    if p1.endswith('*') and p2.startswith(p1[:-1]):
        return True
    if p2.endswith('*') and p1.startswith(p2[:-1]):
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
  
