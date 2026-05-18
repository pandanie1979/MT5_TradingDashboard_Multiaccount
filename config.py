# Configurazione MT5 Trading Dashboard - Multi Account Support
import os
import glob
import json
from typing import Dict, List, Tuple
import streamlit as st

# Path predefiniti degli account MT5
# Populate accounts_config.json (copy from accounts_config.example.json) with real paths.
DEFAULT_MT5_PATHS: list[str] = []

# Configurazione Cache
CACHE_TTL_EA = 300  # 5 minuti per dati EA
CACHE_TTL_TRADES = 300  # 5 minuti per dati trades

# Limiti di visualizzazione
MAX_RECENT_DEALS = 50
MAX_DEBUG_ROWS = 100

# Encoding supportati per i file CSV
SUPPORTED_ENCODINGS = ['utf-16', 'utf-8', 'cp1252', 'latin1']

# Pattern file
EA_MONITOR_PATTERN = "EAMon_*.csv"
TRADE_FILE_PATTERN = "*_*_*_*_*.csv"

# File configurazione account
ACCOUNTS_CONFIG_FILE = "accounts_config.json"

# Colori per distinguere account
ACCOUNT_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]

def discover_accounts_from_paths(mt5_paths: List[str]) -> Dict[str, Dict]:
    """
    Scansiona tutti i percorsi MT5 e scopre account dai prefissi dei file
    Returns: {account_id: {path: str, ea_files: int, trade_files: int, status: str}}
    """
    discovered_accounts = {}
    
    for path in mt5_paths:
        if not os.path.exists(path):
            continue
            
        try:
            # Cerca file EA Monitor per identificare account
            ea_files = glob.glob(os.path.join(path, EA_MONITOR_PATTERN))
            trade_files = [f for f in glob.glob(os.path.join(path, TRADE_FILE_PATTERN)) 
                          if not os.path.basename(f).startswith('EAMon_')]
            
            # Estrai account ID dai nomi file
            account_ids = set()
            
            # Da file EA Monitor: EAMon_ACCOUNT_EA_Strategy_...
            for file_path in ea_files:
                filename = os.path.basename(file_path)
                parts = filename.replace('EAMon_', '').split('_')
                if len(parts) >= 1 and parts[0].isdigit():
                    account_ids.add(parts[0])
            
            # Da file Trade: ACCOUNT_Magic_Symbol_Strategy_...
            for file_path in trade_files:
                filename = os.path.basename(file_path)
                parts = filename.split('_')
                if len(parts) >= 1:
                    # Debug: stampa i primi caratteri per verificare il pattern
                    potential_account = parts[0]
                    if potential_account.isdigit() or potential_account.replace('.', '').isdigit():
                        account_ids.add(potential_account)
            
            # Aggiungi account trovati
            for account_id in account_ids:
                if account_id not in discovered_accounts:
                    # Conta file specifici per questo account
                    account_ea_files = len([f for f in ea_files if f"EAMon_{account_id}_" in os.path.basename(f)])
                    account_trade_files = len([f for f in trade_files if os.path.basename(f).startswith(f"{account_id}_")])
                    
                    discovered_accounts[account_id] = {
                        'path': path,
                        'ea_files': account_ea_files,
                        'trade_files': account_trade_files,
                        'status': 'active',
                        'color': ACCOUNT_COLORS[len(discovered_accounts) % len(ACCOUNT_COLORS)]
                    }
                    
        except Exception as e:
            st.sidebar.warning(f"Errore scansione {path}: {str(e)}")
            continue
    
    return discovered_accounts

def load_accounts_config() -> Dict[str, List[str]]:
    """Carica configurazione account da file JSON"""
    try:
        if os.path.exists(ACCOUNTS_CONFIG_FILE):
            with open(ACCOUNTS_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('mt5_paths', DEFAULT_MT5_PATHS)
    except Exception:
        pass
    return DEFAULT_MT5_PATHS

def save_accounts_config(mt5_paths: List[str]):
    """Salva configurazione account su file JSON"""
    try:
        config = {'mt5_paths': mt5_paths}
        with open(ACCOUNTS_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False

def get_current_account_path(account_id: str, accounts_data: Dict) -> str:
    """Ottieni il percorso per un account specifico"""
    if account_id in accounts_data:
        return accounts_data[account_id]['path']
    return ""

def verify_mt5_path(path: str) -> Tuple[bool, str]:
    """Verifica che un percorso MT5 sia accessibile"""
    if not os.path.exists(path):
        return False, f"Percorso non trovato: {path}"
    
    if not os.access(path, os.R_OK):
        return False, f"Permessi di lettura mancanti per: {path}"
    
    return True, "OK"

def get_account_info(account_id: str, accounts_data: Dict) -> Dict:
    """Ottieni informazioni complete di un account"""
    if account_id not in accounts_data:
        return {}
    
    account_data = accounts_data[account_id].copy()
    
    # Verifica status in tempo reale
    is_valid, message = verify_mt5_path(account_data['path'])
    account_data['status'] = 'active' if is_valid else 'error'
    account_data['status_message'] = message
    
    return account_data

def get_available_accounts_from_path(mt5_path: str):
    """Ottiene lista account disponibili da un percorso MT5"""
    if not os.path.exists(mt5_path):
        return []
    
    accounts = set()
    
    try:
        # Cerca account dai file EA
        ea_files = glob.glob(os.path.join(mt5_path, EA_MONITOR_PATTERN))
        for file_path in ea_files:
            filename = os.path.basename(file_path)
            parts = filename.replace('EAMon_', '').split('_')
            if len(parts) >= 1 and parts[0].isdigit():
                accounts.add(parts[0])
        
        # Cerca account dai file trade
        trade_files = [f for f in glob.glob(os.path.join(mt5_path, TRADE_FILE_PATTERN)) 
                      if not os.path.basename(f).startswith('EAMon_')]
        for file_path in trade_files:
            filename = os.path.basename(file_path)
            parts = filename.split('_')
            if len(parts) >= 1 and parts[0].isdigit():
                accounts.add(parts[0])
                
    except Exception:
        pass
    
    return sorted(list(accounts))