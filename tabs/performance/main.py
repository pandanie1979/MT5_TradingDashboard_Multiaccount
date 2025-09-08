# MT5 Trading Dashboard - Performance Tab Main Entry Point
# File: tabs/performance/main.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5
# Fixed: Import paths, error handling, memory cleanup

"""
Main entry point for the performance tab.
Orchestrates sidebar and main tabbed area rendering.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

# Import modular components
from .config.constants import DEFAULTS, get_session_key
from .utils.session_helpers import (
    initialize_session_defaults, 
    get_sidebar_width,
    get_current_period_trades,
    get_selected_setups,
    get_advanced_filters,
    apply_period_filters,
    apply_advanced_filters,
    cleanup_large_session_objects  # NUOVO: Memory cleanup
)
from .utils.formatting import get_error_message
from .sidebar.layout import render_scrollable_sidebar
from .tabs.charts_tab import render_charts_tab
from .tabs.summary_tab import render_performance_summary_tab
from .tabs.table_tab import render_performance_table_tab
from .tabs.deals_tab import render_recent_deals_tab

# Import data loading (from parent modules) - FIXED: Import with fallback
try:
    from data.loader import get_trades_data
except ImportError:
    from ...data.loader import get_trades_data


def render(account_id: str, account_path: str, account_info: Dict[str, Any]):
    """
    Main render function for performance tab.
    Orchestrates sidebar and main tabbed area with modular components.
    
    Args:
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict with color, status, etc.
    """
    try:
        # Memory cleanup before heavy processing
        cleanup_large_session_objects(account_id, max_objects=50)
        
        # Load trade data for the account
        trades_df = get_trades_data(account_id, account_path)
        
        if trades_df.empty:
            _render_no_data_state(account_id, account_path)
            return
        
        # REMOVED: initialize_session_defaults() - was causing date reset bug
        # The period widgets now initialize themselves when first rendered
        
        # Get layout configuration
        sidebar_width = get_sidebar_width(account_id)
        main_width = 100 - sidebar_width
        column_ratio = [sidebar_width, main_width]
        
        # Create main layout: Sidebar + Main Area
        sidebar_col, main_col = st.columns(column_ratio)
        
        # Render sidebar (always visible, scrollable)
        with sidebar_col:
            render_scrollable_sidebar(trades_df, account_id, account_path, account_info)
        
        # Render main tabbed area
        with main_col:
            render_main_tabbed_area(trades_df, account_id, account_path, account_info)
            
    except FileNotFoundError as e:
        st.error(f"File dati non trovati: {str(e)}")
        st.info("Verifica i percorsi MT5 nella tab Impostazioni")
    except pd.errors.EmptyDataError:
        st.warning("File dati vuoti o corrotti")
        st.info("Controlla il formato e contenuto dei file CSV")
    except KeyError as e:
        st.error(f"Colonna mancante nei dati: {str(e)}")
        st.info("Verifica formato file CSV MT5 - potrebbe mancare una colonna richiesta")
        with st.expander("Debug Info"):
            st.code(f"Error details: {str(e)}")
    except ImportError as e:
        st.error(f"Errore modulo: {str(e)}")
        st.info("Problema con importazione moduli - riavvia l'applicazione")
    except Exception as e:
        st.error(f"Errore imprevisto: {str(e)}")
        st.info("Riavvia l'applicazione o controlla i log")
        
        # Debug info in expandable section
        with st.expander("Debug Tecnico"):
            st.code(f"Exception type: {type(e).__name__}")
            st.code(f"Exception args: {e.args}")


def render_main_tabbed_area(trades_df: pd.DataFrame, account_id: str, 
                           account_path: str, account_info: Dict[str, Any]):
    """
    Render main tabbed area with filtered data.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict
    """
    account_color = account_info.get('color', '#1f77b4')
    
    # NUOVO: Validate required columns before processing
    required_columns = ['MagicNumber', 'OpenPositionTicket']
    missing_columns = [col for col in required_columns if col not in trades_df.columns]
    
    if missing_columns:
        st.error(f"Colonne mancanti nel dataset: {missing_columns}")
        st.info(f"Colonne disponibili: {list(trades_df.columns)}")
        return
    
    # Get current filters and configuration
    selected_setups = get_selected_setups(account_id)
    advanced_filters = get_advanced_filters(account_id)
    
    # Apply period filters first
    period_trades = get_current_period_trades(trades_df, account_id)
    
    if period_trades.empty:
        st.warning(get_error_message("no_trades_period"))
        return
    
    # Apply setup selection filter
    if selected_setups:
        period_trades = period_trades[period_trades['MagicNumber'].isin(selected_setups)]
    else:
        st.warning(get_error_message("no_setup_selected"))
        return
    
    # Apply advanced filters
    period_trades = apply_advanced_filters(period_trades, advanced_filters)
    
    if period_trades.empty:
        st.warning("Nessun trade dopo l'applicazione dei filtri")
        return
    
    # Create tab system (Performance-first ordering from v1.4)
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Equity/Drawdown/Margin", 
        "📊 Performance Summary", 
        "📋 Setup Performance Table", 
        "🔍 Recent Deals"
    ])
    
    # TAB 1: Charts (Equity, Drawdown, Margin)
    with tab1:
        try:
            render_charts_tab(period_trades, account_id, account_path, account_color, selected_setups)
        except Exception as e:
            st.error(f"Errore rendering grafici: {str(e)}")
            st.info("Prova a cambiare periodo o setup selezionati")
    
    # TAB 2: Performance Summary (Aggregate Metrics)
    with tab2:
        try:
            render_performance_summary_tab(period_trades, account_id, account_color)
        except Exception as e:
            st.error(f"Errore calcolo metriche: {str(e)}")
            st.info("Alcuni calcoli potrebbero richiedere più dati")
    
    # TAB 3: Setup Performance Table
    with tab3:
        try:
            render_performance_table_tab(period_trades, account_id)
        except Exception as e:
            st.error(f"Errore tabella performance: {str(e)}")
    
    # TAB 4: Recent Deals
    with tab4:
        try:
            render_recent_deals_tab(period_trades, account_id)
        except Exception as e:
            st.error(f"Errore visualizzazione deals: {str(e)}")


def _render_no_data_state(account_id: str, account_path: str):
    """
    Render state when no trade data is available.
    
    Args:
        account_id: Account identifier
        account_path: Path to MT5 data
    """
    st.warning(f"⚠️ {get_error_message('no_data')} per Account {account_id}")
    
    with st.expander("🔍 Informazioni Debug", expanded=False):
        st.info(f"📁 Pattern cercato: `{account_id}_*_*_*_*.csv`")
        st.info(f"📂 Percorso: {account_path}")
        
        # NUOVO: Enhanced troubleshooting info
        import os
        if os.path.exists(account_path):
            csv_files = [f for f in os.listdir(account_path) if f.endswith('.csv')]
            st.info(f"📄 File CSV trovati: {len(csv_files)}")
            if csv_files:
                st.write("Esempi file trovati:")
                for f in csv_files[:5]:  # Show first 5
                    st.code(f)
        else:
            st.error(f"📂 Percorso non esistente: {account_path}")
        
        # Suggerimenti troubleshooting
        st.markdown("""
        **Possibili cause:**
        - File di trade non presenti nella cartella MT5
        - Formato nome file non corretto
        - Encoding file non supportato
        - Permessi di accesso alla cartella
        
        **Verifica:**
        1. Controlla che ci siano file CSV nella cartella
        2. Verifica che i nomi file inizino con il numero account
        3. Vai alla tab Impostazioni per verificare i percorsi
        4. Controlla permessi lettura cartella
        """)


# Compatibility function to maintain backward compatibility
def render_performance_tab(account_id: str, account_path: str, account_info: Dict[str, Any]):
    """
    Backward compatibility wrapper for the main render function.
    
    Args:
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict
    """
    render(account_id, account_path, account_info)


def get_performance_health_check(account_id: str) -> Dict[str, Any]:
    """
    NUOVO: Health check function per diagnosticare problemi performance tab.
    
    Args:
        account_id: Account identifier
        
    Returns:
        Dict with health status information
    """
    health_status = {
        'account_id': account_id,
        'timestamp': pd.Timestamp.now().isoformat(),
        'status': 'healthy',
        'issues': []
    }
    
    # Check session state size
    account_keys = [k for k in st.session_state.keys() if account_id in k]
    if len(account_keys) > 100:
        health_status['issues'].append(f"High session state usage: {len(account_keys)} keys")
        health_status['status'] = 'warning'
    
    # Check memory usage if possible
    try:
        import sys
        total_size = sum(sys.getsizeof(st.session_state[k]) for k in account_keys)
        if total_size > 50 * 1024 * 1024:  # > 50MB
            health_status['issues'].append(f"High memory usage: {total_size / 1024 / 1024:.1f}MB")
            health_status['status'] = 'warning'
    except:
        pass
    
    health_status['session_keys_count'] = len(account_keys)
    return health_status