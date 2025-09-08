# MT5 Trading Dashboard - Performance Tab Main Entry Point (UPDATED)
# File: tabs/performance/main.py
# Modified: September 2025 - Added Update Metrics button in main area

"""
Main entry point for performance tab with modular architecture.
ADDED: Update Metrics button in main chart area (top-left).
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
    Main render function for performance tab with update button in main area.
    
    Args:
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict
    """
    # Load complete dataset
    try:
        trades_df = get_trades_data(account_id, account_path)
        
        if trades_df.empty:
            st.warning(get_error_message("no_trade_data"))
            return
            
    except Exception as e:
        st.error(f"Errore caricamento dati: {str(e)}")
        return
    
    # Initialize dual state system
    initialize_dual_state_for_account(account_id, trades_df)
    
    # Calculate sidebar width
    from .utils.session_helpers import get_sidebar_width
    sidebar_width = get_sidebar_width(account_id)
    main_width = 100 - sidebar_width
    
    # Create main layout
    sidebar_col, main_col = st.columns([sidebar_width, main_width])
    
    # Render sidebar
    with sidebar_col:
        render_scrollable_sidebar(trades_df, account_id, account_path, account_info)
    
    # Render main area with update button header
    with main_col:
        # HEADER WITH UPDATE BUTTON (always visible across all tabs)
        render_main_area_header(account_id, account_info)
        
        # Get filtered data using APPLIED state
        period_trades = get_current_period_trades(trades_df, account_id)
        
        # Render tab system
        render_main_tabbed_area(period_trades, account_id, account_path, account_info)


def render_main_area_header(account_id: str, account_info: Dict[str, Any]):
    """
    Render main area header with update button and status.
    Positioned at top-left of main chart area, visible across all tabs.
    
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
                           account_path: str, account_info: Dict[str, Any]):
    """
    Render the main tabbed area with 4 performance analysis tabs.
    
    Args:
        period_trades: Filtered trades for current period and setup selection
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict
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
            render_charts_tab(period_trades, account_id, account_path, account_color, 
                            _get_applied_setup_list(account_id))
        except Exception as e:
            st.error(f"Errore rendering charts: {str(e)}")
            _render_fallback_message("charts", e)
    
    # Tab 2: Performance summary metrics
    with tab2:
        try:
            render_performance_summary_tab(period_trades, account_id, account_color)
        except Exception as e:
            st.error(f"Errore rendering summary: {str(e)}")
            _render_fallback_message("summary", e)
    
    # Tab 3: Setup performance table
    with tab3:
        try:
            render_performance_table_tab(period_trades, account_id)
        except Exception as e:
            st.error(f"Errore rendering table: {str(e)}")
            _render_fallback_message("table", e)
    
    # Tab 4: Recent deals
    with tab4:
        try:
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


def get_main_area_summary(account_id: str, period_trades: pd.DataFrame) -> Dict[str, Any]:
    """
    Get summary information for the main area for debugging/monitoring.
    
    Args:
        account_id: Account identifier
        period_trades: Current filtered trades
        
    Returns:
        Dict with main area status summary
    """
    from .utils.session_helpers import (
        get_applied_period_configuration,
        get_applied_selected_setups
    )
    
    period_config = get_applied_period_configuration(account_id)
    selected_setups = get_applied_selected_setups(account_id)
    
    return {
        'account_id': account_id,
        'has_period_config': period_config is not None,
        'period_days': (period_config['end_date'] - period_config['start_date']).days if period_config else 0,
        'selected_setups_count': len(selected_setups),
        'filtered_trades_count': len(period_trades),
        'unique_trades_count': period_trades['OpenPositionTicket'].nunique() if not period_trades.empty else 0,
        'has_pending_changes': detect_pending_changes(account_id),
        'data_date_range': {
            'start': period_trades['OpenDatetime'].min() if not period_trades.empty else None,
            'end': period_trades['OpenDatetime'].max() if not period_trades.empty else None
        }
    }


# Legacy compatibility function
def render_main_chart_enhanced(*args, **kwargs):
    """Legacy function for backward compatibility - redirects to new system."""
    st.warning("⚠️ Using legacy render function - please update to new modular system")
    return render(*args, **kwargs)


# Legacy compatibility alias
def render_performance_tab(account_id: str, account_path: str, account_info: Dict[str, Any]):
    """
    LEGACY COMPATIBILITY: Old function name redirects to new render function.
    This maintains backward compatibility with existing imports.
    
    Args:
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict
    """
    return render(account_id, account_path, account_info)