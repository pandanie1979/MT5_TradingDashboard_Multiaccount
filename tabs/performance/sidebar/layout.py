# MT5 Trading Dashboard - Sidebar Layout (SIMPLIFIED)
# File: tabs/performance/sidebar/layout.py
# Modified: September 2025 - Removed advanced filters section

"""
Sidebar layout management for performance tab.
SIMPLIFIED: Removed advanced filters section as requested.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from .account_info import render_account_info_header
from .period_selection import render_period_selection_enhanced
from .setup_selection import render_setup_selection_clean
# REMOVED: from .filters import render_advanced_filters_panel
from .debug_tools import render_debug_tools_panel
from ..utils.session_helpers import get_sidebar_width, set_sidebar_width
from ..config.constants import SIDEBAR_PRESETS, get_default_expanded


def render_scrollable_sidebar(trades_df: pd.DataFrame, account_id: str, 
                             account_path: str, account_info: Dict[str, Any]):
    """
    Render the main scrollable sidebar with SIMPLIFIED components.
    REMOVED: Advanced filters section as requested.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict with color, status, etc.
    """
    account_color = account_info.get('color', '#1f77b4')
    
    # Account Info Header (moved from main area)
    render_account_info_header(trades_df, account_id, account_info)
    
    st.markdown("---")
    
    # Sidebar Width Control
    render_sidebar_width_control(account_id)
    
    st.markdown("---")
    
    # Period Selection (SIMPLIFIED - no preset buttons)
    with st.expander("ðŸ“… Periodo di Analisi", expanded=get_default_expanded("period_analysis")):
        render_period_selection_enhanced(trades_df, account_id)
    
    # Setup Selection (without container boxes)
    with st.expander("🎯 Selezione Setup", expanded=get_default_expanded("setup_selection")):
        render_setup_selection_clean(trades_df, account_id)
    
    # REMOVED: Advanced Filters section
    # with st.expander("ðŸ” Filtri Avanzati", expanded=get_default_expanded("advanced_filters")):
    #     render_advanced_filters_panel(trades_df, account_id)
    
    # Debug Tools (kept for development/troubleshooting)
    with st.expander("ðŸ”§ Debug & Tools", expanded=get_default_expanded("debug_tools")):
        render_debug_tools_panel(trades_df, account_id, account_path)


def render_sidebar_width_control(account_id: str):
    """
    Render sidebar width control with preset buttons only.
    SIMPLIFIED: Removed slider, only preset buttons remain.
    
    Args:
        account_id: Account identifier
    """
    st.markdown("### ðŸŽ›ï¸ Layout")
    
    current_width = get_sidebar_width(account_id)
    
    # Show current width
    st.caption(f"Larghezza corrente: {current_width}%")
    
    # Preset buttons only
    st.markdown("**Preset Larghezza:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("ðŸ“±20%", key=f"preset_compact_{account_id}", width='stretch'):
            set_sidebar_width(account_id, SIDEBAR_PRESETS["compact"])
    
    with col2:
        if st.button("ðŸ’»25%", key=f"preset_normal_{account_id}", width='stretch'):
            set_sidebar_width(account_id, SIDEBAR_PRESETS["normal"])
    
    with col3:
        if st.button("ðŸ–¥ï¸35%", key=f"preset_wide_{account_id}", width='stretch'):
            set_sidebar_width(account_id, SIDEBAR_PRESETS["wide"])


def render_sidebar_header(account_id: str, account_color: str):
    """
    Render sidebar header with account identification.
    
    Args:
        account_id: Account identifier
        account_color: Account color for styling
    """
    st.markdown(f"""
    <div style="border-left: 4px solid {account_color}; padding-left: 12px; margin-bottom: 20px;">
        <h3 style="margin: 0; color: {account_color};">âš™ï¸ Impostazioni</h3>
        <p style="margin: 5px 0 0 0; color: #666; font-size: 12px;">Account: {account_id}</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_footer(account_id: str):
    """
    Render sidebar footer with additional controls or info.
    
    Args:
        account_id: Account identifier
    """
    st.markdown("---")
    st.markdown("### ðŸ“Š Quick Stats")
    
    # Show current configuration summary
    current_width = get_sidebar_width(account_id)
    st.caption(f"Sidebar: {current_width}% | Account: {account_id}")


def get_sidebar_state_summary(account_id: str) -> Dict[str, Any]:
    """
    Get summary of current sidebar state for debugging.
    UPDATED: Removed advanced_filters dependency.
    
    Args:
        account_id: Account identifier
        
    Returns:
        Dict with sidebar state summary
    """
    from ..utils.session_helpers import (
        get_selected_setups, 
        get_period_configuration
    )
    
    return {
        'sidebar_width': get_sidebar_width(account_id),
        'selected_setups_count': len(get_selected_setups(account_id)),
        'period_config': get_period_configuration(account_id) is not None,
        # REMOVED: 'active_filters': get_advanced_filters(account_id)
    }