import streamlit as st
from tabs import tab_ea_attivi, tab_performance, tab_posizioni, tab_settings
from config import load_accounts_config, discover_accounts_from_paths, get_current_account_path

st.set_page_config(
    page_title="MT5 Trading Dashboard", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Carica stile CSS (FIX PATH)
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("⚠️ File CSS non trovato. Usando stili di default.")

# ✅ MIGLIORAMENTO: Inizializzazione session_state più robusta
if 'accounts_data' not in st.session_state:
    st.session_state.accounts_data = {}

if 'current_account' not in st.session_state:
    st.session_state.current_account = None

# ✅ NUOVO: Persistenza stato tab attiva (opzionale - Streamlit gestisce automaticamente)
if 'active_tab_index' not in st.session_state:
    st.session_state.active_tab_index = 0

# Carica e scopri account
@st.cache_data(ttl=60)
def load_and_discover_accounts():
    """Carica configurazione e scopre account disponibili"""
    mt5_paths = load_accounts_config()
    return discover_accounts_from_paths(mt5_paths)

# Aggiorna account data
accounts_data = load_and_discover_accounts()
st.session_state.accounts_data = accounts_data

# HEADER GLOBALE CON ACCOUNT SELECTOR
st.markdown("### 🏦 MT5 Trading Dashboard")

if not accounts_data:
    st.error("❌ Nessun account MT5 trovato. Configura i percorsi nella tab Impostazioni.")
    st.info("La dashboard cerca file con pattern: `EAMon_ACCOUNT_*` e `ACCOUNT_*_*_*_*`")
else:
    # Account selector sempre visibile
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        account_options = list(accounts_data.keys())
        
        # Imposta account di default se non selezionato
        if st.session_state.current_account is None:
            st.session_state.current_account = account_options[0] if account_options else None
        
        # Verifica che l'account corrente sia ancora disponibile
        if st.session_state.current_account not in account_options:
            st.session_state.current_account = account_options[0] if account_options else None
        
        current_account = st.selectbox(
            "🏦 Seleziona Account:",
            options=account_options,
            index=account_options.index(st.session_state.current_account) if st.session_state.current_account in account_options else 0,
            key="account_selector",
            help="Cambio account aggiorna automaticamente i dati"
        )
        
        # ✅ CHIAVE DEL FIX: Aggiornamento SELETTIVO senza st.rerun()
        if current_account != st.session_state.current_account:
            st.session_state.current_account = current_account
            st.cache_data.clear()  # Clear cache per nuovo account
            # ✅ IMPORTANTE: NON usare st.rerun() per preservare tab attiva
    
    with col2:
        if current_account in accounts_data:
            account_info = accounts_data[current_account]
            status_color = "🟢" if account_info['status'] == 'active' else "🔴"
            st.markdown(f"**Status:** {status_color} {account_info['status'].upper()}")
    
    with col3:
        if current_account in accounts_data:
            account_info = accounts_data[current_account]
            total_files = account_info['ea_files'] + account_info['trade_files']
            st.markdown(f"**Files:** {total_files} trovati")

# Indicatore account corrente colorato
if current_account and current_account in accounts_data:
    account_color = accounts_data[current_account]['color']
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, {account_color}22 0%, {account_color}11 100%); 
                padding: 8px 16px; border-radius: 8px; border-left: 4px solid {account_color}; 
                margin: 10px 0; font-weight: bold;">
        🏦 Account Attivo: {current_account} | 
        📁 Path: {accounts_data[current_account]['path']} |
        📊 EA Files: {accounts_data[current_account]['ea_files']} | 
        📈 Trade Files: {accounts_data[current_account]['trade_files']}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ✅ SOLUZIONE DEFINITIVA: TAB PERFORMANCE COME PRIMA TAB
tab_names = ["📈 Performance", "📊 EA Attivi", "💰 Posizioni", "⚙️ Impostazioni"]
tab1, tab2, tab3, tab4 = st.tabs(tab_names)

# Passa current_account e path a tutti i tab
current_account_path = get_current_account_path(current_account, accounts_data) if current_account else ""

# ✅ REORDER: Performance diventa la prima tab (più importante)
with tab1:
    if current_account and current_account_path:
        tab_performance.render(current_account, current_account_path, accounts_data[current_account])
    else:
        st.error("❌ Seleziona un account valido per visualizzare le performance")

with tab2:
    if current_account and current_account_path:
        tab_ea_attivi.render(current_account, current_account_path, accounts_data[current_account])
    else:
        st.error("❌ Seleziona un account valido per visualizzare gli EA")

with tab3:
    if current_account and current_account_path:
        tab_posizioni.render(current_account, current_account_path, accounts_data[current_account])
    else:
        st.error("❌ Seleziona un account valido per visualizzare le posizioni")

with tab4:
    tab_settings.render(accounts_data)

# ✅ MIGLIORAMENTO: Refresh button in sidebar con controllo intelligente
with st.sidebar:
    st.markdown("### 🔄 Controlli")
    
    if st.button("🔄 Aggiorna Dati", use_container_width=True, help="Ricarica tutti i dati e riscansiona account"):
        st.cache_data.clear()
        # ✅ IMPORTANTE: NON usare st.rerun() per preservare tab
        st.success("✅ Cache pulita! I dati saranno aggiornati automaticamente.")
    
    if st.button("🏠 Reset Account", use_container_width=True, help="Resetta selezione account"):
        st.session_state.current_account = None
        # ✅ IMPORTANTE: NON usare st.rerun() per preservare tab
        st.info("🔄 Seleziona un nuovo account dal dropdown sopra.")
    
    # ✅ NUOVO: Pulsante reset completo solo se necessario
    if st.button("🔄 Reset Completo", use_container_width=True, help="Reset completo applicazione (usa solo se necessario)"):
        # Questo è l'unico caso dove usiamo st.rerun()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Info debug migliorata
    if st.checkbox("🔍 Info Debug", value=False):
        st.json({
            "Current Account": current_account,
            "Total Accounts": len(accounts_data),
            "Session State Keys": len(st.session_state),
            "Cache Status": "Active" if hasattr(st.cache_data, 'clear') else "N/A",
            "Account Status": {acc: info.get('status', 'unknown') for acc, info in accounts_data.items()},
            "Active Tab": "Performance (Prima Tab)" 
        })