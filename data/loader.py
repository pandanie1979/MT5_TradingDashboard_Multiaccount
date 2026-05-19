import streamlit as st
import pandas as pd
import os
import glob
import re
from config import SUPPORTED_ENCODINGS, EA_MONITOR_PATTERN, TRADE_FILE_PATTERN, CACHE_TTL_EA, CACHE_TTL_TRADES

DEBUG = os.getenv("DASHBOARD_DEBUG", "false").lower() == "true"

@st.cache_data(ttl=CACHE_TTL_EA)
def get_ea_data(account_id: str, mt5_path: str):
    """Carica i dati di monitoraggio degli EA da file CSV per un account specifico"""
    pattern = os.path.join(mt5_path, EA_MONITOR_PATTERN)
    ea_list = []

    try:
        csv_files = glob.glob(pattern)
        
        if not csv_files:
            st.warning(f"Nessun file EA Monitor trovato per Account {account_id} in: {mt5_path}")
            return pd.DataFrame()
        
        # Filtra solo i file dell'account corrente
        account_files = [f for f in csv_files if f"EAMon_{account_id}_" in os.path.basename(f)]
        
        if not account_files:
            st.warning(f"Nessun file EA Monitor trovato per Account {account_id}")
            return pd.DataFrame()
            
        for file_path in account_files:
            try:
                # Prova encoding multipli
                df = None
                for encoding in SUPPORTED_ENCODINGS:
                    try:
                        df = pd.read_csv(file_path, sep=',', encoding=encoding)
                        break
                    except (UnicodeDecodeError, Exception):
                        continue
                
                if df is None:
                    continue
                    
                df.columns = df.columns.str.strip()

                if not df.empty:
                    # Prendi l'ultima riga (stato più recente)
                    row = df.iloc[-1]
                    filename = os.path.basename(file_path)
                    setup_name = filename.replace('EAMon_', '').replace('.csv', '')

                    # Estrai magic number dal nome file
                    magic_number = "N/A"
                    mn_match = re.search(r'MN(\d+)', setup_name)
                    if mn_match:
                        magic_number = mn_match.group(1)

                    ea_info = {
                        'Account_ID': account_id,
                        'Setup_Name': setup_name,
                        'Magic_Number': magic_number,
                        'EA_Name': row.get('EA_Name', 'Unknown'),
                        'Symbol': row.get('Symbol', 'Unknown'),
                        'Timeframe': row.get('Timeframe', 'Unknown'),
                        'Status': row.get('Status', 'UNKNOWN'),
                        'Trading_Enabled': row.get('TradingEnabled', 'UNKNOWN'),
                        'Has_Position': row.get('HasPosition', 'NO'),
                        'Position_Margin': float(row.get('PositionMargin', 0)),
                        'Tick_Count': int(row.get('TickCount', 0)),
                        'EA_Start_Time': pd.to_datetime(row.get('EAStartTime', pd.NaT)),
                        'Last_Tick_Time': pd.to_datetime(row.get('LastTickTime', pd.NaT)),
                        'Last_Update': pd.to_datetime(row.get('DateTime', pd.NaT)),
                        'File_Path': file_path
                    }
                    ea_list.append(ea_info)
                    
            except Exception as e:
                if DEBUG:
                    st.warning(f"⚠ Errore nel file EA {os.path.basename(file_path)}: {str(e)}")
                continue
                
    except Exception as e:
        st.error(f"[Errore] Errore nell'accesso alla cartella MT5 per Account {account_id}: {str(e)}")
        return pd.DataFrame()

    return pd.DataFrame(ea_list)

@st.cache_data(ttl=CACHE_TTL_TRADES)
def get_trades_data(account_id: str, mt5_path: str):
    """
    Carica tutti i deals (chiusure) dai file di trade per un account specifico
    ✅ VERSIONE AGGIORNATA: Cattura filename per classificazione backtest/live
    """
    pattern = os.path.join(mt5_path, TRADE_FILE_PATTERN)
    all_trades = []
    files_processed = 0
    files_with_trades = 0

    try:
        csv_files = glob.glob(pattern)
        # Escludi file EA Monitor e filtra per account
        trade_files = [f for f in csv_files if not os.path.basename(f).startswith('EAMon_')]
        account_files = [f for f in trade_files if os.path.basename(f).startswith(f"{account_id}_")]
        
        if not account_files:
            st.warning(f"Nessun file di trade trovato per Account {account_id} in: {mt5_path}")
            return pd.DataFrame()

        if DEBUG:
            st.info(f"[DEBUG] {len(account_files)} file trovati per account {account_id}. Primo: {os.path.basename(account_files[0])}")

        # Progress bar per file numerosi
        if len(account_files) > 5:
            progress_bar = st.progress(0)
            progress_text = st.empty()

        for idx, file_path in enumerate(account_files):
            try:
                # Update progress
                if len(account_files) > 5:
                    progress = (idx + 1) / len(account_files)
                    progress_bar.progress(progress)
                    progress_text.text(f"Caricamento file Account {account_id}: {idx + 1}/{len(account_files)}...")

                # CHIAVE: Estrai filename PRIMA del caricamento CSV
                filename = os.path.basename(file_path)
                
                # Prova encoding multipli
                df = None
                for encoding in SUPPORTED_ENCODINGS:
                    try:
                        df = pd.read_csv(file_path, sep=',', encoding=encoding)
                        break
                    except (UnicodeDecodeError, Exception):
                        continue
                
                if df is None:
                    continue
                
                # Verifica colonne richieste
                required_columns = ['OpenPositionTicket', 'MagicNumber', 'PL', 'OpenDatetime']
                if not all(col in df.columns for col in required_columns):
                    if DEBUG and idx == 0:
                        st.warning(f"[DEBUG] Colonne mancanti nel primo file. Colonne trovate: {list(df.columns)}")
                    continue

                # Filtra solo trade chiusi (con P&L)
                completed_trades = df[df['PL'].notna() & (df['PL'] != 0)].copy()
                if DEBUG and idx == 0:
                    st.info(f"[DEBUG] Primo file: {len(df)} righe totali, {len(completed_trades)} con PL != 0. PL dtype: {df['PL'].dtype}, sample values: {df['PL'].head(3).tolist()}")
                    try:
                        with open(file_path, 'rb') as _raw:
                            raw_preview = _raw.read(400)
                        st.code(f"[DEBUG] Raw bytes primo file:\n{raw_preview}")
                    except Exception as _e:
                        st.warning(f"[DEBUG] Lettura raw fallita: {_e}")
                
                if not completed_trades.empty:
                    files_with_trades += 1
                    completed_trades['Account_ID'] = account_id
                    completed_trades['LogFile'] = filename  # Nome file corto
                    
                    # AGGIUNTA CRITICA: Cattura filename per classificazione
                    completed_trades['SourceFilename'] = filename
                    
                    # Estrai info dal nome file
                    parts = filename.replace('.csv', '').split('_')
                    if len(parts) >= 4:
                        completed_trades['Account'] = parts[0]
                        completed_trades['MagicFromFile'] = parts[1]
                        completed_trades['Symbol'] = parts[2] if 'Symbol' not in completed_trades.columns else completed_trades['Symbol']
                        completed_trades['StrategyFromFile'] = parts[3]
                    
                    all_trades.append(completed_trades)
                
                files_processed += 1
                    
            except Exception as e:
                # Log solo se verbose mode
                if DEBUG:
                    st.warning(f"⚠ Errore nel file trade {os.path.basename(file_path)}: {str(e)}")
                continue
        
        # Pulisci progress bar
        if len(account_files) > 5:
            progress_bar.empty()
            progress_text.empty()
    
    except Exception as e:
        st.error(f"[Errore] Errore nell'accesso alla cartella MT5 per Account {account_id}: {str(e)}")
        return pd.DataFrame()

    if all_trades:
        # Concatena tutti i DataFrame
        trades_df = pd.concat(all_trades, ignore_index=True)
        
        # Converti date
        trades_df['OpenDatetime'] = pd.to_datetime(trades_df['OpenDatetime'], errors='coerce')
        if 'CloseDatetime' in trades_df.columns:
            trades_df['CloseDatetime'] = pd.to_datetime(trades_df['CloseDatetime'], errors='coerce')
        
        # Statistiche di caricamento
        unique_trades = trades_df['OpenPositionTicket'].nunique()
        total_deals = len(trades_df)
        
        # AGGIUNTA: Debug info filename pattern per sidebar
        filenames_with_000000 = trades_df['SourceFilename'].str.contains('_000000', na=False).sum()
        filenames_without_000000 = len(trades_df) - filenames_with_000000
        
        # Log informazioni di caricamento nella sidebar
        '''
        with st.sidebar:
            st.success(f"""
            ðŸ“Š **Account {account_id}:**
            - Files processati: {files_processed}
            - Files con trades: {files_with_trades}
            - Trades unici: {unique_trades:,}
            - Deals totali: {total_deals:,}
            - Files _000000: {filenames_with_000000}
            - Files altri: {filenames_without_000000}
            """)
        '''
        
        # NON rimuovere duplicati - mantieni tutte le chiusure (deals)
        return trades_df
    else:
        st.warning(f"Nessun file di trade trovato per Account {account_id}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL_EA)
def check_mt5_connection(account_id: str, mt5_path: str):
    """Verifica che la cartella MT5 sia accessibile per un account specifico"""
    if not os.path.exists(mt5_path):
        return False, f"Percorso non trovato: {mt5_path}"
    
    if not os.access(mt5_path, os.R_OK):
        return False, f"Permessi di lettura mancanti per: {mt5_path}"
    
    # Conta file disponibili per questo account
    ea_files = len(glob.glob(os.path.join(mt5_path, f"EAMon_{account_id}_*.csv")))
    all_trade_files = [f for f in glob.glob(os.path.join(mt5_path, TRADE_FILE_PATTERN)) 
                       if not os.path.basename(f).startswith('EAMon_')]
    trade_files = len([f for f in all_trade_files if os.path.basename(f).startswith(f"{account_id}_")])
    
    return True, {
        'account_id': account_id,
        'ea_files': ea_files,
        'trade_files': trade_files,
        'path': mt5_path
    }

# Funzione helper per debug filename patterns
@st.cache_data(ttl=CACHE_TTL_EA)
def analyze_filename_patterns(account_id: str, mt5_path: str):
    """
    Analizza i pattern dei filename per un account specifico
    Utile per debug della classificazione backtest/live
    """
    pattern = os.path.join(mt5_path, TRADE_FILE_PATTERN)
    
    try:
        csv_files = glob.glob(pattern)
        trade_files = [f for f in csv_files if not os.path.basename(f).startswith('EAMon_')]
        account_files = [f for f in trade_files if os.path.basename(f).startswith(f"{account_id}_")]
        
        if not account_files:
            return {}
        
        filenames = [os.path.basename(f) for f in account_files]
        
        analysis = {
            'total_files': len(filenames),
            'files_with_000000': len([f for f in filenames if '_000000' in f]),
            'files_without_000000': len([f for f in filenames if '_000000' not in f]),
            'filename_examples': filenames[:10],  # Prime 10 per esempio
            'time_patterns': {}
        }
        
        # Analizza pattern temporali
        for filename in filenames:
            parts = filename.replace('.csv', '').split('_')
            if len(parts) >= 6:  # Account_Magic_Symbol_Strategy_Date_Time
                time_part = parts[-1]  # Ultima parte = HHMMSS
                if time_part not in analysis['time_patterns']:
                    analysis['time_patterns'][time_part] = 0
                analysis['time_patterns'][time_part] += 1
        
        return analysis
        
    except Exception as e:
        return {'error': str(e)}

# Funzione spostata in config.py per evitare import circolari