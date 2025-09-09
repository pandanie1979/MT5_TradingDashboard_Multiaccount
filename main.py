# main.py - Soluzione pulita con fix per le funzioni config

import streamlit as st
import os
import glob
from pathlib import Path
from datetime import datetime, timedelta

# Import dei tab
try:
    from tabs import tab_ea_attivi, tab_performance, tab_posizioni, tab_settings
except ImportError as e:
    st.error(f"Errore import tab: {e}")
    st.stop()

# Import configurazione con fallback
try:
    from config import load_accounts_config
    CONFIG_AVAILABLE = True
except ImportError as e:
    st.warning(f"Config module non disponibile: {e}")
    CONFIG_AVAILABLE = False

def get_available_accounts_from_path_fixed(mt5_path):
    """
    Versione corretta di get_available_accounts_from_path che evita l'errore
    'dictionary update sequence element #0 has length 7; 2 is required'
    """
    accounts = {}
    
    if not os.path.exists(mt5_path):
        return accounts
    
    try:
        # Cerca file CSV nel percorso
        csv_files = glob.glob(os.path.join(mt5_path, "*.csv"))
        
        if not csv_files:
            return accounts
        
        # Estrai account ID dai nomi file
        account_ids = set()
        
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            
            # Pattern per file di trading: Account_Magic_Symbol_Strategy_Date_Time.csv
            # Pattern per EA Monitor: EAMon_Account_EA_Strategy_MNMagic_Symbol_TF.csv
            parts = filename.replace('.csv', '').split('_')
            
            # Cerca numeri che potrebbero essere account ID (6+ cifre)
            for part in parts:
                if part.isdigit() and len(part) >= 6:
                    account_ids.add(part)
                    break
        
        # Crea dizionario account con struttura corretta
        for account_id in account_ids:
            # Conta file per questo account
            account_files = [f for f in csv_files if account_id in os.path.basename(f)]
            
            accounts[account_id] = {
                'path': mt5_path,
                'status': 'active' if account_files else 'inactive',
                'files_count': len(account_files),
                'ea_files': len([f for f in account_files if 'EAMon' in f]),
                'trade_files': len([f for f in account_files if 'EAMon' not in f])
            }
        
        return accounts
        
    except Exception as e:
        st.warning(f"Errore durante scansione {mt5_path}: {e}")
        return {}

def load_mt5_paths():
    """Carica percorsi MT5 con fallback multipli"""
    
    # Metodo 1: Prova a usare la configurazione esistente
    if CONFIG_AVAILABLE:
        try:
            config_result = load_accounts_config()
            
            # Se è una lista, usa direttamente
            if isinstance(config_result, list):
                return config_result
            
            # Se è un dict, estrai mt5_paths
            if isinstance(config_result, dict):
                return config_result.get('mt5_paths', [])
                
        except Exception as e:
            st.warning(f"Errore caricamento config: {e}")
    
    # Metodo 2: Auto-discovery percorsi standard MT5
    standard_paths = []
    
    # Percorsi comuni MT5
    base_paths = [
        os.path.expanduser("~") + r"\AppData\Roaming\MetaQuotes\Terminal",
        r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal",
        r"C:\Program Files\MetaTrader 5\MQL5\Files",
        r"C:\Program Files (x86)\MetaTrader 5\MQL5\Files"
    ]
    
    for base_path in base_paths:
        if os.path.exists(base_path):
            # Cerca subdirectory con pattern hash MT5
            try:
                for item in os.listdir(base_path):
                    item_path = os.path.join(base_path, item)
                    if os.path.isdir(item_path) and len(item) == 32:  # Hash MT5 è 32 caratteri
                        files_path = os.path.join(item_path, "MQL5", "Files")
                        if os.path.exists(files_path):
                            standard_paths.append(files_path)
            except (PermissionError, OSError):
                continue
    
    return standard_paths

def _ensure_basic_session_state(account_id: str):
    """
    Assicura che le chiavi session state base esistano SEMPRE.
    Evita KeyError nelle funzioni helper.
    """
    start_key = f"date_start_{account_id}"
    end_key = f"date_end_{account_id}"
    
    # Solo inizializza se NON esistono (non sovrascrive)
    if start_key not in st.session_state:
        default_end = datetime.now().date()
        default_start = default_end - timedelta(days=30)
        st.session_state[start_key] = default_start
        st.session_state[end_key] = default_end
        
        # Marca che è stata fatta inizializzazione basic
        st.session_state[f"basic_init_{account_id}"] = True

@st.cache_data
def load_css():
    """Load CSS with caching to avoid file read on every rerun."""
    try:
        with open("assets/style.css", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""


def main():
    """Main application function"""
    
    # Configurazione pagina
    st.set_page_config(
        page_title="MT5 Trading Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS
    css = load_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            
    # Titolo principale
    st.title("MT5 Trading Dashboard")
    
    # Carica percorsi MT5
    mt5_paths = load_mt5_paths()
    
    if not mt5_paths:
        st.error("Nessun percorso MT5 trovato")
        st.info("Assicurati che MetaTrader 5 sia installato e configurato")
        st.stop()
    
    st.info(f"Trovati {len(mt5_paths)} percorsi MT5")
    
    # Trova account in tutti i percorsi
    all_accounts = {}
    
    for path in mt5_paths:
        with st.expander(f"Scansionando: {path}"):
            try:
                path_accounts = get_available_accounts_from_path_fixed(path)
                
                if path_accounts:
                    st.success(f"Trovati {len(path_accounts)} account")
                    for acc_id, info in path_accounts.items():
                        st.write(f"Account {acc_id}: {info['files_count']} file totali")
                    all_accounts.update(path_accounts)
                else:
                    # Mostra alcuni file per debug
                    try:
                        files = os.listdir(path)[:5]
                        st.info(f"Nessun account, ma trovati {len(os.listdir(path))} file. Esempi: {files}")
                    except:
                        st.warning("Percorso non accessibile")
                        
            except Exception as e:
                st.error(f"Errore: {e}")
    
    if not all_accounts:
        st.error("Nessun account trovato in nessun percorso")
        st.info("Verifica che ci siano file CSV di trading nei percorsi MT5")
        st.stop()
    
    # Selector account
    account_ids = list(all_accounts.keys())
    selected_account = st.selectbox(
        "Seleziona Account:",
        account_ids,
        key="global_account_selector"
    )
    
    if not selected_account:
        st.stop()
    
    # Info account selezionato
    account_info = all_accounts[selected_account]
    account_path = account_info['path']

    # SAFE: Inizializzazione minimale session state
    _ensure_basic_session_state(selected_account)
        
    # Header con info account
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Account", selected_account)
    with col2:
        st.metric("File Trading", account_info['trade_files'])
    with col3:
        st.metric("File EA Monitor", account_info['ea_files'])
    
    # Tabs principali
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Performance", 
        "📊 EA Attivi", 
        "💰 Posizioni", 
        "⚙️ Impostazioni"
    ])
    
    # Render tab con gestione errori robusta
    with tab1:
        try:
            tab_performance.render(selected_account, account_path, account_info)
        except Exception as e:
            st.error(f"Errore tab Performance: {e}")
            st.exception(e)
    
    with tab2:
        try:
            tab_ea_attivi.render(selected_account, account_path, account_info)
        except Exception as e:
            st.error(f"Errore tab EA Attivi: {e}")
            st.exception(e)
    
    with tab3:
        try:
            tab_posizioni.render(selected_account, account_path, account_info)
        except Exception as e:
            st.error(f"Errore tab Posizioni: {e}")
            st.exception(e)
    
    with tab4:
        try:
            # Prepara dati per tab impostazioni
            accounts_data = {
                'all_accounts': all_accounts,
                'mt5_paths': mt5_paths,
                'selected_account': selected_account,
                'config_available': CONFIG_AVAILABLE
            }
            tab_settings.render(accounts_data)
        except Exception as e:
            st.error(f"Errore tab Impostazioni: {e}")
            st.exception(e)

def initialize_session_state_for_account(account_id, trades_data=None):
    """
    Inizializza le chiavi session state necessarie per un account
    """
    from datetime import datetime, timedelta
    
    # Chiavi per la selezione periodo
    start_key = f"date_start_{account_id}"
    end_key = f"date_end_{account_id}"
    
    # Inizializza solo se non esistono
    if start_key not in st.session_state or end_key not in st.session_state:
        
        if trades_data is not None and not trades_data.empty:
            # Usa date dai dati reali
            data_start = trades_data['OpenDatetime'].min().date()
            data_end = trades_data['OpenDatetime'].max().date()
            
            # Ultimi 30 giorni disponibili
            default_end = min(datetime.now().date(), data_end)
            default_start = max(data_start, default_end - timedelta(days=30))
        else:
            # Fallback se non ci sono dati
            default_end = datetime.now().date()
            default_start = default_end - timedelta(days=30)
        
        st.session_state[start_key] = default_start
        st.session_state[end_key] = default_end
    
    # Chiavi per user modification tracking
    user_modified_key = f"period_user_set_{account_id}"
    if user_modified_key not in st.session_state:
        st.session_state[user_modified_key] = "auto_default"

if __name__ == "__main__":
    main()