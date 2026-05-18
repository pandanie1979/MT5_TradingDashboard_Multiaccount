#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per correggere emoji corrotti nei file Python
Esegui dalla root del progetto: python fix_emoji_encoding.py
"""

import os
import re
from pathlib import Path

# Mapping emoji corrotti -> emoji corretti
EMOJI_FIXES = {
    # Emoji Dashboard
    "📊": "📊",
    "📈": "📈", 
    "📋": "📋",
    "📅": "📅",
    "🔄": "🔄",
    "📂": "📂",
    "🔍": "🔍",
    
    # Emoji Money/Finance
    "💰": "💰",
    "💯": "💯",
    "💾": "💾",
    "💡": "💡",
    
    # Emoji Status
    "✅": "✅",  # Potrebbe essere già corretto
    "❌": "❌",
    "⚠️": "⚠️",
    "ℹ️": "ℹ️",
    
    # Emoji Vari
    "🔍§": "🔧",
    "🔍´": "🔴",
    "🚨": "🚨",
    "🟢": "🟢",
    "🟡": "🟡",
    "🏦": "🏦",
    "🎯": "🎯",
    
    # Altri simboli comuni corrotti
    "€": "€",
    "→": "→",
    "≤": "≤",
    "≥": "≥",
    "–": "–",
    "—": "—",
    
    # Pattern UTF-8 mal codificati comuni
    "€": "€",
    "à": "à",
    "è": "è",
    "ì": "ì",
    "ò": "ò",
    "ù": "ù"
}

def fix_file_encoding(file_path):
    """
    Corregge l'encoding di un singolo file
    
    Args:
        file_path: Path del file da correggere
        
    Returns:
        Tuple (corrections_made, error_message)
    """
    try:
        # Leggi il file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()
        
        # Applica le correzioni
        content = original_content
        corrections_made = 0
        
        for corrupted, correct in EMOJI_FIXES.items():
            if corrupted in content:
                count = content.count(corrupted)
                content = content.replace(corrupted, correct)
                corrections_made += count
                print(f"  Fixed {count}x '{corrupted}' -> '{correct}'")
        
        # Scrivi solo se ci sono state modifiche
        if corrections_made > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path}: {corrections_made} correzioni applicate")
        
        return corrections_made, None
        
    except Exception as e:
        error_msg = f"❌ Errore processing {file_path}: {str(e)}"
        print(error_msg)
        return 0, error_msg

def main():
    """Funzione principale per correzione encoding"""
    print("🔧 Avvio correzione encoding emoji...")
    
    # Pattern per file da processare
    target_patterns = [
        "tabs/**/*.py",
        "data/**/*.py", 
        "*.py"
    ]
    
    # Raccogli tutti i file Python
    python_files = []
    for pattern in target_patterns:
        python_files.extend(Path('.').glob(pattern))
    
    # Rimuovi duplicati e converti a stringhe
    python_files = list(set(str(f) for f in python_files))
    python_files.sort()
    
    print(f"📁 Trovati {len(python_files)} file Python da processare")
    
    total_corrections = 0
    total_files_modified = 0
    errors = []
    
    # Processa ogni file
    for file_path in python_files:
        if os.path.exists(file_path):
            print(f"\n🔍 Processing: {file_path}")
            corrections, error = fix_file_encoding(file_path)
            
            if error:
                errors.append(error)
            elif corrections > 0:
                total_corrections += corrections
                total_files_modified += 1
    
    # Riepilogo
    print(f"\n" + "="*50)
    print(f"📊 RIEPILOGO CORREZIONI:")
    print(f"   Files processati: {len(python_files)}")
    print(f"   Files modificati: {total_files_modified}")
    print(f"   Correzioni totali: {total_corrections}")
    
    if errors:
        print(f"   Errori: {len(errors)}")
        for error in errors:
            print(f"     {error}")
    
    if total_corrections > 0:
        print(f"\n✅ Correzione emoji completata con successo!")
        print(f"💡 Tip: Esegui un test dell'applicazione per verificare che gli emoji siano visualizzati correttamente")
    else:
        print(f"\n💡 Nessuna correzione necessaria - emoji già corretti!")

if __name__ == "__main__":
    main()