# MT5 Trading Dashboard - Setup Selection Component
# File: tabs/performance/sidebar/setup_selection.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Setup selection component for sidebar.
Handles setup list, search, and bulk operations without container boxes.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any

from ..utils.session_helpers import (
    get_current_period_trades,
    toggle_all_setups,
    invert_setup_selection,
    get_setup_search_term
)
from ..utils.formatting import format_profit_indicator
from ..config.constants import get_session_key


def render_setup_selection_clean(trades_df: pd.DataFrame, account_id: str):
    """
    Setup selection WITHOUT container box - FIX accessibility labels.
    Clean implementation with proper checkbox labels and help tooltips.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    period_trades = get_current_period_trades(trades_df, account_id)
    
    if period_trades.empty:
        st.warning("Nessun trade nel periodo")
        return
    
    # Calculate available setups
    setup_list = _calculate_setup_list(period_trades)
    
    # Render search functionality
    filtered_setups = _render_search_controls(setup_list, account_id)
    
    # Render bulk action buttons
    _render_bulk_actions(filtered_setups, account_id)
    
    # Render setup list with accessible checkboxes
    _render_setup_checkboxes(filtered_setups, account_id)
    
    # Show selection summary
    _render_selection_summary(filtered_setups, account_id)


def _calculate_setup_list(period_trades: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Calculate list of available setups with performance data.
    
    Args:
        period_trades: Filtered trades for current period
        
    Returns:
        List of setup dictionaries
    """
    setup_list = []
    
    for magic_number in period_trades['MagicNumber'].unique():
        setup_trades = period_trades[period_trades['MagicNumber'] == magic_number]
        first_trade = setup_trades.iloc[0]
        
        # Extract setup information
        setup_name = first_trade.get('StrategyName', first_trade.get('StrategyFromFile', 'Unknown'))
        symbol = first_trade.get('OrderSymbol', first_trade.get('Symbol', 'Unknown'))
        
        # Calculate performance
        setup_profit = setup_trades.groupby('OpenPositionTicket')['PL'].sum().sum()
        setup_trades_count = setup_trades['OpenPositionTicket'].nunique()
        
        setup_list.append({
            'Magic_Number': magic_number,
            'Setup_Name': setup_name,
            'Symbol': symbol,
            'Profit': setup_profit,
            'Trades_Count': setup_trades_count,
            'Display_Name': f"MN{magic_number} - {setup_name} ({symbol})",
            'Performance': f"€{setup_profit:.0f} ({setup_trades_count}T)"
        })
    
    # Sort by profit descending
    setup_list.sort(key=lambda x: x['Profit'], reverse=True)
    
    return setup_list


def _render_search_controls(setup_list: List[Dict[str, Any]], account_id: str) -> List[Dict[str, Any]]:
    """
    Render search controls and return filtered setup list.
    
    Args:
        setup_list: Complete setup list
        account_id: Account identifier
        
    Returns:
        Filtered setup list based on search
    """
    # Search input
    search_term = st.text_input(
        "🔍 Cerca Setup:", 
        key=f"setup_search_{account_id}",
        placeholder="MN, nome, simbolo...",
        help="Filtra setup per magic number, nome strategia o simbolo"
    )
    
    # Filter setups based on search
    if search_term:
        filtered_setups = [
            s for s in setup_list 
            if search_term.lower() in s['Display_Name'].lower()
        ]
    else:
        filtered_setups = setup_list
    
    # Show filter results
    if search_term and len(filtered_setups) != len(setup_list):
        st.caption(f"Mostrando {len(filtered_setups)} di {len(setup_list)} setup")
    
    return filtered_setups


def _render_bulk_actions(filtered_setups: List[Dict[str, Any]], account_id: str):
    """
    Render bulk action buttons for setup selection.
    
    Args:
        filtered_setups: Filtered setup list
        account_id: Account identifier
    """
    st.markdown("**Azioni Bulk:**")
    
    # Create three columns for bulk actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Tutti", key=f"select_all_{account_id}", use_container_width=True):
            magic_numbers = [s['Magic_Number'] for s in filtered_setups]
            count = toggle_all_setups(account_id, magic_numbers, select_all=True)
            st.success(f"✅ {count} setup attivati!")
    
    with col2:
        if st.button("❌ Nessuno", key=f"select_none_{account_id}", use_container_width=True):
            magic_numbers = [s['Magic_Number'] for s in filtered_setups]
            count = toggle_all_setups(account_id, magic_numbers, select_all=False)
            st.warning(f"❌ {count} setup disattivati!")
    
    with col3:
        if st.button("🔄 Inverti", key=f"invert_{account_id}", use_container_width=True):
            magic_numbers = [s['Magic_Number'] for s in filtered_setups]
            count = invert_setup_selection(account_id, magic_numbers)
            st.info(f"🔄 {count} setup invertiti!")


def _render_setup_checkboxes(filtered_setups: List[Dict[str, Any]], account_id: str):
    """
    Render setup checkboxes with accessible labels.
    
    Args:
        filtered_setups: Filtered setup list
        account_id: Account identifier
    """
    if not filtered_setups:
        st.info("Nessun setup trovato con i criteri di ricerca")
        return
    
    st.markdown("**Setup Disponibili:**")
    
    # Render each setup as checkbox with performance info
    for i, setup in enumerate(filtered_setups):
        setup_key = f"setup_{account_id}_{setup['Magic_Number']}"
        
        # Initialize if not exists
        if setup_key not in st.session_state:
            st.session_state[setup_key] = True
        
        # Checkbox with accessible label and help
        is_selected = st.checkbox(
            setup['Display_Name'],  # Accessible label
            value=st.session_state[setup_key],
            key=f"{setup_key}_cb_{i}",  # Unique key with index
            help=f"Seleziona setup {setup['Performance']}"  # Help tooltip
        )
        
        # Update session state
        st.session_state[setup_key] = is_selected
        
        # Show performance info for selected setups
        if is_selected:
            profit_color = "🟢" if setup['Profit'] >= 0 else "🔴"
            st.caption(f"{profit_color} {setup['Performance']}")


def _render_selection_summary(filtered_setups: List[Dict[str, Any]], account_id: str):
    """
    Render selection summary information.
    
    Args:
        filtered_setups: Filtered setup list
        account_id: Account identifier
    """
    # Count selected setups
    selected_count = 0
    total_selected_profit = 0
    
    for setup in filtered_setups:
        setup_key = f"setup_{account_id}_{setup['Magic_Number']}"
        if st.session_state.get(setup_key, True):
            selected_count += 1
            total_selected_profit += setup['Profit']
    
    # Show summary
    if selected_count > 0:
        st.info(f"📊 {selected_count}/{len(filtered_setups)} setup selezionati")
        
        # Show combined performance of selected setups
        if total_selected_profit != 0:
            profit_indicator = format_profit_indicator(total_selected_profit)
            st.markdown(f"**Performance Combinata:** {profit_indicator}", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Nessun setup selezionato - selezionare almeno uno per l'analisi")


def get_setup_selection_summary(account_id: str, trades_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get summary of current setup selection for external use.
    
    Args:
        account_id: Account identifier
        trades_df: Complete trades DataFrame
        
    Returns:
        Dict with setup selection summary
    """
    from ..utils.session_helpers import get_selected_setups
    
    selected_magic_numbers = get_selected_setups(account_id)
    period_trades = get_current_period_trades(trades_df, account_id)
    
    if period_trades.empty:
        return {
            'total_setups': 0,
            'selected_count': 0,
            'selected_magic_numbers': [],
            'combined_performance': 0
        }
    
    # Calculate total available setups
    total_setups = period_trades['MagicNumber'].nunique()
    
    # Calculate combined performance of selected setups
    if selected_magic_numbers:
        selected_trades = period_trades[period_trades['MagicNumber'].isin(selected_magic_numbers)]
        combined_performance = selected_trades.groupby('OpenPositionTicket')['PL'].sum().sum()
    else:
        combined_performance = 0
    
    return {
        'total_setups': total_setups,
        'selected_count': len(selected_magic_numbers),
        'selected_magic_numbers': selected_magic_numbers,
        'combined_performance': combined_performance,
        'selection_percentage': (len(selected_magic_numbers) / total_setups * 100) if total_setups > 0 else 0
    }


def reset_setup_selection(account_id: str, trades_df: pd.DataFrame, select_all: bool = True) -> bool:
    """
    Reset setup selection to default state.
    
    Args:
        account_id: Account identifier
        trades_df: Complete trades DataFrame
        select_all: If True, select all setups; if False, deselect all
        
    Returns:
        True if reset was successful
    """
    period_trades = get_current_period_trades(trades_df, account_id)
    
    if period_trades.empty:
        return False
    
    magic_numbers = period_trades['MagicNumber'].unique().tolist()
    count = toggle_all_setups(account_id, magic_numbers, select_all)
    
    return count > 0