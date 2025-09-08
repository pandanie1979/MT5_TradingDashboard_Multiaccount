import streamlit as st
import os
import glob
from config import (
    load_accounts_config, save_accounts_config, verify_mt5_path, 
    discover_accounts_from_paths, get_available_accounts_from_path,
    DEFAULT_MT5_PATHS, ACCOUNTS_CONFIG_FILE
)
from datetime import datetime

def render(accounts_data: dict):
    st.header("⚙️ Impostazioni & Configurazione")
    
    # Tabs per organizzare le impostazioni
    settings_tab1, settings_tab2, settings_tab3 = st.tabs([
        "🏦 Gestione Account", 
        "📁 Percorsi MT5", 
        "🔧 Debug & Info"
    ])
    
    with settings_tab1:
        render_account_management(accounts_data)
    
    with settings_tab2:
        render_path_management()
    
    with settings_tab3:
        render_debug_info(accounts_data)

def render_account_management(accounts_data: dict):
    """Sezione gestione account"""
    st.subheader("🏦 Account Configurati")
    
    if not accounts_data:
        st.warning("❌ Nessun account trovato. Configura i percorsi MT5 nella tab 'Percorsi MT5'.")
        return
    
    # Tabella account con status
    st.write("**Account disponibili:**")
    
    account_status_data = []
    for account_id, info in accounts_data.items():
        is_valid, message = verify_mt5_path(info['path'])
        
        account_status_data.append({
            'Account ID': account_id,
            'Status': '🟢 Attivo' if is_valid else '🔴 Errore',
            'Path': info['path'],
            'EA Files': info.get('ea_files', 0),
            'Trade Files': info.get('trade_files', 0),
            'Colore': info.get('color', '#1f77b4'),
            'Dettagli': message if not is_valid else 'OK'
        })
    
    if account_status_data:
        import pandas as pd
        df_accounts = pd.DataFrame(account_status_data)
        
        # Mostra tabella con styling
        st.dataframe(
            df_accounts[['Account ID', 'Status', 'EA Files', 'Trade Files', 'Dettagli']],
            use_container_width=True,
            hide_index=True
        )
        
        # Dettagli account selezionato
        st.markdown("---")
        st.subheader("📊 Dettagli Account Selezionato")
        
        selected_account = st.selectbox(
            "Seleziona account per dettagli:",
            options=list(accounts_data.keys()),
            key="settings_account_selector"
        )
        
        if selected_account:
            account_info = accounts_data[selected_account]
            account_color = account_info.get('color', '#1f77b4')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div style="padding: 15px; border-left: 4px solid {account_color}; background: {account_color}22; border-radius: 5px;">
                    <h4 style="margin: 0 0 10px 0;">Account {selected_account}</h4>
                    <strong>Path:</strong> {account_info['path']}<br>
                    <strong>EA Files:</strong> {account_info.get('ea_files', 0)}<br>
                    <strong>Trade Files:</strong> {account_info.get('trade_files', 0)}<br>
                    <strong>Status:</strong> {account_info.get('status', 'unknown').upper()}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Test connessione in tempo reale
                if st.button(f"🔍 Test Connessione Account {selected_account}", use_container_width=True):
                    with st.spinner("Verificando connessione..."):
                        from data.loader import check_mt5_connection
                        success, result = check_mt5_connection(selected_account, account_info['path'])
                        
                        if success:
                            st.success(f"✅ Connessione OK per Account {selected_account}")
                            st.json(result)
                        else:
                            st.error(f"❌ Errore connessione: {result}")
                
                # Mostra file recenti
                if st.button(f"📂 Mostra File Account {selected_account}", use_container_width=True):
                    show_account_files(selected_account, account_info['path'])

def render_path_management():
    """Sezione gestione percorsi MT5"""
    st.subheader("📁 Gestione Percorsi MT5")
    
    # Carica configurazione corrente
    current_paths = load_accounts_config()
    
    st.write("**Percorsi MT5 configurati:**")
    
    # Mostra percorsi correnti
    for i, path in enumerate(current_paths):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            is_valid, message = verify_mt5_path(path)
            status_icon = "✅" if is_valid else "❌"
            st.write(f"{status_icon} `{path}`")
            if not is_valid:
                st.caption(f"⚠️ {message}")
        
        with col2:
            if st.button("🔍 Scansiona", key=f"scan_{i}"):
                scan_path_for_accounts(path)
        
        with col3:
            if st.button("🗑️ Rimuovi", key=f"remove_{i}"):
                new_paths = [p for j, p in enumerate(current_paths) if j != i]
                if save_accounts_config(new_paths):
                    st.success("Percorso rimosso! Ricarica la pagina per vedere le modifiche.")
                    # ✅ RIMOSSO st.rerun() per preservare tab
                else:
                    st.error("Errore nel salvare la configurazione")
    
    st.markdown("---")
    st.subheader("➕ Aggiungi Nuovo Percorso MT5")
    
    # Form per aggiungere nuovo percorso
    with st.form("add_path_form"):
        new_path = st.text_input(
            "Percorso MT5:",
            value="",
            help="Inserisci il percorso completo alla cartella Files di MT5",
            placeholder=r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\...\MQL5\Files"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("➕ Aggiungi Percorso", use_container_width=True)
        with col2:
            if st.form_submit_button("🔄 Reset a Default", use_container_width=True):
                if save_accounts_config(DEFAULT_MT5_PATHS):
                    st.success("Configurazione resettata ai valori di default! Ricarica la pagina per vedere le modifiche.")
                    # ✅ RIMOSSO st.rerun() per preservare tab
                            
        if submitted and new_path:
            # Verifica percorso
            is_valid, message = verify_mt5_path(new_path)
            
            if is_valid:
                # Aggiungi se non esiste già
                if new_path not in current_paths:
                    updated_paths = current_paths + [new_path]
                    if save_accounts_config(updated_paths):
                        st.success(f"✅ Percorso aggiunto: {new_path}. Ricarica la pagina per vedere le modifiche.")
                        # ✅ RIMOSSO st.rerun() per preservare tab
                    else:
                        st.error("❌ Errore nel salvare la configurazione")
                else:
                    st.warning("⚠️ Percorso già presente nella configurazione")
            else:
                st.error(f"❌ Percorso non valido: {message}")
    
    # Percorsi suggeriti
    st.markdown("---")
    st.subheader("💡 Percorsi Suggeriti")
    
    suggested_base = r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal"
    
    if os.path.exists(suggested_base):
        terminals = [d for d in os.listdir(suggested_base) 
                    if os.path.isdir(os.path.join(suggested_base, d)) 
                    and len(d) > 10]  # Terminal ID di solito sono lunghi
        
        if terminals:
            st.write("**Terminal MT5 trovati sul sistema:**")
            for terminal in terminals:
                terminal_path = os.path.join(suggested_base, terminal, "MQL5", "Files")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    is_valid, _ = verify_mt5_path(terminal_path)
                    status = "✅" if is_valid else "❌"
                    st.write(f"{status} Terminal: `{terminal}`")
                    st.caption(f"Path: `{terminal_path}`")
                
                with col2:
                    if terminal_path not in current_paths and is_valid:
                        if st.button("➕ Aggiungi", key=f"suggest_{terminal}"):
                            updated_paths = current_paths + [terminal_path]
                            if save_accounts_config(updated_paths):
                                st.success("Percorso aggiunto! Ricarica la pagina per vedere le modifiche.")
                                # ✅ RIMOSSO st.rerun() per preservare tab

        else:
            st.info("Nessun terminal MT5 trovato nella cartella standard")
    else:
        st.info("Cartella base MetaQuotes non trovata nel percorso standard")

def render_debug_info(accounts_data: dict):
    """Sezione debug e informazioni sistema"""
    st.subheader("🔧 Informazioni Debug")
    
    # Info configurazione
    st.write("**📋 Configurazione Sistema:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Info file configurazione
        config_exists = os.path.exists(ACCOUNTS_CONFIG_FILE)
        st.metric("File Configurazione", "✅ Presente" if config_exists else "❌ Mancante")
        
        if config_exists:
            try:
                config_size = os.path.getsize(ACCOUNTS_CONFIG_FILE)
                st.caption(f"Dimensione: {config_size} bytes")
            except:
                st.caption("Errore lettura file")
        
        # Info account
        st.metric("Account Rilevati", len(accounts_data))
        st.metric("Percorsi Configurati", len(load_accounts_config()))
    
    with col2:
        # Info cache e performance
        st.write("**⚡ Performance:**")
        
        # Verifica disponibilità cache
        cache_available = hasattr(st.cache_data, 'clear')
        st.write(f"Cache Streamlit: {'✅ Disponibile' if cache_available else '❌ Non disponibile'}")
        
        if st.button("🧹 Pulisci Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache pulita!")
    
    # Dettagli tecnici per ogni account
    if accounts_data:
        st.markdown("---")
        st.subheader("🔍 Dettagli Tecnici Account")
        
        for account_id, info in accounts_data.items():
            with st.expander(f"🏦 Account {account_id} - Debug Info"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Informazioni Base:**")
                    st.json({
                        "account_id": account_id,
                        "path": info['path'],
                        "status": info.get('status', 'unknown'),
                        "color": info.get('color', 'N/A'),
                        "ea_files": info.get('ea_files', 0),
                        "trade_files": info.get('trade_files', 0)
                    })
                
                with col2:
                    st.write("**Test Connessione:**")
                    
                    if st.button(f"🔄 Test {account_id}", key=f"debug_test_{account_id}"):
                        with st.spinner(f"Testing Account {account_id}..."):
                            from data.loader import check_mt5_connection
                            success, result = check_mt5_connection(account_id, info['path'])
                            
                            if success:
                                st.success("✅ Connessione OK")
                                st.json(result)
                            else:
                                st.error(f"❌ Errore: {result}")
                    
                    # Mostra file sample
                    if st.button(f"📂 File Sample {account_id}", key=f"debug_files_{account_id}"):
                        show_sample_files(account_id, info['path'])
    
    # Log sistema
    st.markdown("---")
    st.subheader("📋 Log Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Configurazione Corrente:**")
        current_config = {
            "mt5_paths": load_accounts_config(),
            "accounts_discovered": len(accounts_data),
            "config_file_exists": os.path.exists(ACCOUNTS_CONFIG_FILE)
        }
        st.json(current_config)
    
    with col2:
        st.write("**Environment Info:**")
        env_info = {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
            "platform": os.name,
            "cwd": os.getcwd()[:50] + "..." if len(os.getcwd()) > 50 else os.getcwd()
        }
        st.json(env_info)
    
    # Tools di manutenzione
    st.markdown("---")
    st.subheader("🛠️ Tools di Manutenzione")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Riscansiona Account", use_container_width=True):
            with st.spinner("Riscansionando account..."):
                mt5_paths = load_accounts_config()
                new_accounts = discover_accounts_from_paths(mt5_paths)
                st.success(f"Trovati {len(new_accounts)} account. Ricarica la pagina per vedere le modifiche.")
                # ✅ RIMOSSO st.rerun() per preservare tab
    
    with col2:
        if st.button("📊 Export Configurazione", use_container_width=True):
            export_config = {
                "mt5_paths": load_accounts_config(),
                "accounts_data": accounts_data,
                "timestamp": datetime.now().isoformat()
            }
            st.download_button(
                label="💾 Download Config JSON",
                data=str(export_config),
                file_name="mt5_dashboard_config.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("⚠️ Reset Completo", use_container_width=True):
            if st.button("⚠️ CONFERMA RESET", key="confirm_reset", type="primary"):
                # Reset configurazione
                if save_accounts_config(DEFAULT_MT5_PATHS):
                    st.cache_data.clear()
                    st.success("✅ Reset completato! Ricarica la pagina manualmente per vedere le modifiche.")
                    # ✅ RIMOSSO st.rerun() - ultimo caso risolto
                else:
                    st.error("❌ Errore durante il reset")

def scan_path_for_accounts(path: str):
    """Scansiona un percorso per trovare account"""
    st.write(f"**Scansione percorso:** `{path}`")
    
    if not os.path.exists(path):
        st.error("❌ Percorso non trovato")
        return
    
    accounts = get_available_accounts_from_path(path)
    
    if accounts:
        st.success(f"✅ Trovati {len(accounts)} account: {', '.join(accounts)}")
        
        # Mostra dettagli per ogni account
        for account in accounts:
            ea_files = glob.glob(os.path.join(path, f"EAMon_{account}_*.csv"))
            trade_files = [f for f in glob.glob(os.path.join(path, f"{account}_*.csv")) 
                          if not os.path.basename(f).startswith('EAMon_')]
            
            st.write(f"- **Account {account}**: {len(ea_files)} EA files, {len(trade_files)} trade files")
    else:
        st.warning("⚠️ Nessun account trovato in questo percorso")

def show_account_files(account_id: str, path: str):
    """Mostra i file di un account specifico"""
    st.write(f"**File Account {account_id}:**")
    
    # File EA
    ea_files = glob.glob(os.path.join(path, f"EAMon_{account_id}_*.csv"))
    st.write(f"**📊 EA Monitor Files ({len(ea_files)}):**")
    
    if ea_files:
        for f in ea_files[:5]:  # Mostra solo i primi 5
            file_size = os.path.getsize(f)
            file_time = os.path.getmtime(f)
            from datetime import datetime
            mod_time = datetime.fromtimestamp(file_time).strftime("%d/%m/%Y %H:%M")
            st.write(f"- `{os.path.basename(f)}` ({file_size} bytes, {mod_time})")
        
        if len(ea_files) > 5:
            st.write(f"... e altri {len(ea_files) - 5} file")
    else:
        st.write("Nessun file EA trovato")
    
    # File Trade
    trade_files = [f for f in glob.glob(os.path.join(path, f"{account_id}_*.csv")) 
                   if not os.path.basename(f).startswith('EAMon_')]
    st.write(f"**📈 Trade Files ({len(trade_files)}):**")
    
    if trade_files:
        for f in sorted(trade_files, key=os.path.getmtime, reverse=True)[:5]:
            file_size = os.path.getsize(f)
            file_time = os.path.getmtime(f)
            mod_time = datetime.fromtimestamp(file_time).strftime("%d/%m/%Y %H:%M")
            st.write(f"- `{os.path.basename(f)}` ({file_size} bytes, {mod_time})")
        
        if len(trade_files) > 5:
            st.write(f"... e altri {len(trade_files) - 5} file")
    else:
        st.write("Nessun file trade trovato")

def show_sample_files(account_id: str, path: str):
    """Mostra contenuto sample dei file"""
    st.write(f"**Sample File Content - Account {account_id}:**")
    
    # Sample EA file
    ea_files = glob.glob(os.path.join(path, f"EAMon_{account_id}_*.csv"))
    if ea_files:
        st.write("**Sample EA Monitor File:**")
        try:
            import pandas as pd
            df = pd.read_csv(ea_files[0], encoding='utf-8', nrows=3)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Errore lettura EA file: {e}")
    
    # Sample Trade file
    trade_files = [f for f in glob.glob(os.path.join(path, f"{account_id}_*.csv")) 
                   if not os.path.basename(f).startswith('EAMon_')]
    if trade_files:
        st.write("**Sample Trade File:**")
        try:
            import pandas as pd
            df = pd.read_csv(trade_files[0], encoding='cp1252', nrows=3)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Errore lettura Trade file: {e}")