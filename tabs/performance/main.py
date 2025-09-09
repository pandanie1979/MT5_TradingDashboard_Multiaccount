# MT5 Trading Dashboard - Performance Tab Main Entry Point (OPTIMIZED)
# File: tabs/performance/main.py
# Modified: September 2025 - Added conditional data loading for pending changes

"""
Main entry point for performance tab with optimized data loading.
OPTIMIZATION: Avoid heavy data reloading when only pending changes exist.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

# Import sidebar components
from .sidebar.layout import render_scrollable_sidebar

# Import tab components  
from .tabs.charts_tab import render_charts_tab
from .tabs.summary_tab import render_performance_summary_tab
from .tabs.table_tab import render_performance_table_tab
from .tabs.deals_tab import render_recent_deals_tab

# Import utilities
from .utils.session_helpers import (
    initialize_dual_state_for_account,
    get_current_period_trades,
    detect_pending_changes,
    apply_pending_changes
)
from .utils.formatting import get_error_message

# Import data loading
try:
    from data.loader import get_trades_data
except ImportError:
    from ...data.loader import get_trades_data


def render(account_id: str, account_path: str, account_info: Dict[str, Any]):
    """
    Main render function with OPTIMIZED data loading.
    
    OPTIMIZATION: Skip heavy data reload if only pending changes exist.
    
    Args:
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict
    """
    # OPTIMIZATION 1: Check for cached data first
    cache_key = f"trades_data_{account_id}"
    data_timestamp_key = f"data_timestamp_{account_id}"
    
    # Get current time
    current_time = pd.Timestamp.now()
    
    # Check if we have recent cached data (< 5 minutes old)
    if (cache_key in st.session_state and 
        data_timestamp_key in st.session_state):
        
        last_load_time = st.session_state[data_timestamp_key]
        if (current_time - last_load_time).total_seconds() < 300:  # 5 minutes
            # Use cached data
            trades_df = st.session_state[cache_key]
            use_cached = True
        else:
            # Data too old, reload
            use_cached = False
    else:
        use_cached = False
    
    # OPTIMIZATION 2: Load data only if needed
    if not use_cached:
        try:
            with st.spinner("Caricamento dati..."):
                trades_df = get_trades_data(account_id, account_path)
                
                # Cache the data
                st.session_state[cache_key] = trades_df
                st.session_state[data_timestamp_key] = current_time
                
        except Exception as e:
            st.error(f"Errore caricamento dati: {str(e)}")
            return
    
    # Check if we have data
    if trades_df.empty:
        st.warning(get_error_message("no_trade_data"))
        return
    
    # OPTIMIZATION 3: Initialize dual state only once per session
    init_key = f"dual_state_initialized_{account_id}"
    if init_key not in st.session_state:
        initialize_dual_state_for_account(account_id, trades_df)
        st.session_state[init_key] = True
    
    # Calculate sidebar width
    from .utils.session_helpers import get_sidebar_width
    sidebar_width = get_sidebar_width(account_id)
    main_width = 100 - sidebar_width
    
    # Create main layout
    sidebar_col, main_col = st.columns([sidebar_width, main_width])
    
    # Render sidebar (always responsive for pending state)
    with sidebar_col:
        render_scrollable_sidebar(trades_df, account_id, account_path, account_info)
    
    # OPTIMIZATION 4: Conditional main area rendering
    with main_col:
        # HEADER WITH UPDATE BUTTON (always visible)
        render_main_area_header(account_id, account_info)
        
        # Check for pending changes
        has_pending = detect_pending_changes(account_id)
        
        if has_pending:
            # FAST PATH: Show current state + pending indicator
            render_pending_state_view(trades_df, account_id, account_path, account_info)
        else:
            # NORMAL PATH: Full render with applied data
            period_trades = get_current_period_trades(trades_df, account_id)
            render_main_tabbed_area(period_trades, account_id, account_path, account_info)


def render_pending_state_view(trades_df: pd.DataFrame, account_id: str, 
                             account_path: str, account_info: Dict[str, Any]):
    """
    Render a lightweight view when pending changes exist.
    Shows current (applied) data with pending change indicators.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier  
        account_path: Path to MT5 data
        account_info: Account information dict
    """
    # Show pending changes info
    st.info("⏳ **Modifiche in Attesa** - I grafici mostrano la configurazione attuale. Clicca 'Update Metrics' per applicare le modifiche.")
    
    # Get current applied data (lightweight)
    period_trades = get_current_period_trades(trades_df, account_id)
    
    # Show summary of pending vs applied
    render_pending_changes_summary(account_id)
    
    # Render tabs with current data (no heavy processing)
    render_main_tabbed_area(period_trades, account_id, account_path, account_info, 
                           lightweight=True)


def render_pending_changes_summary(account_id: str):
    """Show summary of what changes are pending."""
    from .utils.session_helpers import (
        get_applied_period_configuration,
        get_applied_selected_setups
    )
    
    # Period changes
    pending_start = st.session_state.get(f"pending_start_{account_id}")
    pending_end = st.session_state.get(f"pending_end_{account_id}")
    applied_config = get_applied_period_configuration(account_id)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if applied_config and (pending_start != applied_config['start_date'] or 
                              pending_end != applied_config['end_date']):
            st.warning(f"📅 **Periodo**: {pending_start} → {pending_end} (pending)")
        else:
            st.success("📅 **Periodo**: Nessuna modifica")
    
    with col2:
        # Setup changes
        pending_count = len([k for k in st.session_state.keys() 
                           if k.startswith(f"pending_setup_{account_id}_") and st.session_state[k]])
        applied_count = len(get_applied_selected_setups(account_id))
        
        if pending_count != applied_count:
            st.warning(f"🎯 **Setup**: {pending_count} selezionati (pending)")
        else:
            st.success("🎯 **Setup**: Nessuna modifica")


def render_main_area_header(account_id: str, account_info: Dict[str, Any]):
    """
    Render main area header with update button and status.
    
    Args:
        account_id: Account identifier
        account_info: Account information dict
    """
    # Create header layout
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        account_color = account_info.get('color', '#1f77b4')
        st.markdown(f"""
        <div style="border-left: 4px solid {account_color}; padding-left: 12px;">
            <h3 style="margin: 0; color: {account_color};">📊 Performance Analysis</h3>
            <p style="margin: 0; color: #666; font-size: 12px;">Account: {account_id}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        render_update_metrics_button(account_id)
    
    with col3:
        render_status_indicator(account_id)
    
    # Separator
    st.markdown("---")


def render_update_metrics_button(account_id: str):
    """
    Render the update metrics button with smart state management.
    
    Args:
        account_id: Account identifier
    """
    has_pending_changes = detect_pending_changes(account_id)
    
    # Button styling based on state
    button_type = "primary" if has_pending_changes else "secondary"
    button_text = "🔄 Update Metrics" if has_pending_changes else "✅ Updated"
    
    # Render button
    if st.button(
        button_text,
        key=f"update_metrics_main_{account_id}",
        disabled=not has_pending_changes,
        type=button_type,
        use_container_width=True,
        help="Apply pending changes to charts and metrics"
    ):
        # Apply changes and show feedback
        changes_applied = apply_pending_changes(account_id)
        
        # OPTIMIZATION: Clear data cache to force reload after update
        cache_key = f"trades_data_{account_id}"
        init_key = f"dual_state_initialized_{account_id}"
        
        # Don't clear trades data (keep it cached), just mark as needing reprocessing
        if f"period_processing_needed_{account_id}" not in st.session_state:
            st.session_state[f"period_processing_needed_{account_id}"] = True
        
        if changes_applied['total_changes'] > 0:
            st.success(f"✅ Applied {changes_applied['total_changes']} changes!")
            st.rerun()
        else:
            st.info("No changes to apply")


def render_status_indicator(account_id: str):
    """
    Render status indicator showing current configuration state.
    
    Args:
        account_id: Account identifier
    """
    has_pending_changes = detect_pending_changes(account_id)
    
    if has_pending_changes:
        st.warning("⚠️ Changes Pending")
    else:
        st.success("✅ Applied")


def render_main_tabbed_area(period_trades: pd.DataFrame, account_id: str, 
                           account_path: str, account_info: Dict[str, Any],
                           lightweight: bool = False):
    """
    Render the main tabbed area with optional lightweight mode.
    
    Args:
        period_trades: Filtered trades for current period and setup selection
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict
        lightweight: If True, skip heavy processing for pending state
    """
    account_color = account_info.get('color', '#1f77b4')
    
    # Create 4 tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Equity/Drawdown/Margin", 
        "📊 Performance Summary", 
        "📋 Setup Performance Table", 
        "🔍 Recent Deals"
    ])
    
    # Tab 1: Charts with enhanced visualization
    with tab1:
        try:
            if lightweight:
                st.info("📊 Grafici con configurazione attuale (non aggiornati)")
            
            render_charts_tab(period_trades, account_id, account_path, account_color, 
                            _get_applied_setup_list(account_id))
        except Exception as e:
            st.error(f"Errore rendering charts: {str(e)}")
            _render_fallback_message("charts", e)
    
    # Tab 2: Performance summary metrics
    with tab2:
        try:
            if lightweight:
                st.info("📊 Metriche con configurazione attuale (non aggiornate)")
                
            render_performance_summary_tab(period_trades, account_id, account_color)
        except Exception as e:
            st.error(f"Errore rendering summary: {str(e)}")
            _render_fallback_message("summary", e)
    
    # Tab 3: Setup performance table
    with tab3:
        try:
            if lightweight:
                st.info("📋 Tabella con configurazione attuale (non aggiornata)")
                
            render_performance_table_tab(period_trades, account_id)
        except Exception as e:
            st.error(f"Errore rendering table: {str(e)}")
            _render_fallback_message("table", e)
    
    # Tab 4: Recent deals
    with tab4:
        try:
            if lightweight:
                st.info("🔍 Deals con configurazione attuale (non aggiornati)")
                
            render_recent_deals_tab(period_trades, account_id)
        except Exception as e:
            st.error(f"Errore rendering deals: {str(e)}")
            _render_fallback_message("deals", e)


def _get_applied_setup_list(account_id: str) -> list:
    """Get list of applied selected magic numbers."""
    from .utils.session_helpers import get_applied_selected_setups
    return get_applied_selected_setups(account_id)


def _render_fallback_message(component: str, error: Exception):
    """Render fallback message when component fails to load."""
    st.info(f"""
    🔧 **Componente {component} temporaneamente non disponibile**
    
    Errore tecnico: {str(error)}
    
    **Soluzioni suggerite:**
    1. Clicca su "🔄 Update Metrics" 
    2. Verifica la selezione periodo/setup
    3. Ricarica la pagina se il problema persiste
    """)


# Legacy compatibility functions
def render_main_chart_enhanced(*args, **kwargs):
    """Legacy function for backward compatibility - redirects to new system."""
    st.warning("⚠️ Using legacy render function - please update to new modular system")
    return render(*args, **kwargs)


def render_performance_tab(account_id: str, account_path: str, account_info: Dict[str, Any]):
    """Legacy compatibility alias."""
    return render(account_id, account_path, account_info)