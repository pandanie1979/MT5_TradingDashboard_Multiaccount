# MT5 Trading Dashboard - Setup Selection Component (PENDING STATE)
# File: tabs/performance/sidebar/setup_selection.py
# Modified: September 2025 - Updated to use pending state keys

"""
Setup selection component for sidebar.
UPDATED: Uses pending state keys - changes are applied only when user clicks Update Metrics.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any

from ..utils.formatting import format_profit_indicator
from ..config.constants import get_session_key


def render_setup_selection_clean(trades_df: pd.DataFrame, account_id: str):
    """
    Setup selection using PENDING state.
    Changes are saved to pending_* keys and applied only via Update Metrics button.
    
    Args:
        trades_df: Complete trades DataFrame  
        account_id: Account identifier
    """
    if trades_df.empty:
        st.warning("Nessun trade disponibile")
        return
    
    # Calculate available setups using complete dataset
    setup_list = _calculate_setup_list(trades_df)
    
    if not setup_list:
        st.info("Nessun setup disponibile nei trade caricati")
        return
    
    # Render search functionality
    filtered_setups = _render_search_controls(setup_list, account_id)
    
    # Render bulk action buttons
    _render_bulk_actions(filtered_setups, account_id)
    
    # Render setup list with pending state checkboxes
    _render_setup_checkboxes_pending(filtered_setups, account_id)
    
    # Show selection summary
    _render_selection_summary_pending(filtered_setups, account_id)


def _calculate_setup_list(trades_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Calculate list of available setups with performance data (unchanged)."""
    if trades_df.empty:
        return []
    
    setup_list = []
    
    try:
        for magic_number in trades_df['MagicNumber'].unique():
            setup_trades = trades_df[trades_df['MagicNumber'] == magic_number]
            
            if setup_trades.empty:
                continue
                
            first_trade = setup_trades.iloc[0]
            
            setup_name = first_trade.get('StrategyName', 
                        first_trade.get('StrategyFromFile', 
                        f'Strategy_{magic_number}'))
            
            symbol = first_trade.get('OrderSymbol', 
                    first_trade.get('Symbol', 'Unknown'))
            
            try:
                unique_trades = setup_trades.groupby('OpenPositionTicket')['PL'].sum()
                setup_profit = unique_trades.sum()
                setup_trades_count = len(unique_trades)
            except Exception:
                setup_profit = setup_trades['PL'].sum()
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
    
    except Exception as e:
        st.error(f"Errore nel calcolo setup: {str(e)}")
        return []
    
    setup_list.sort(key=lambda x: x['Profit'], reverse=True)
    return setup_list


def _render_search_controls(setup_list: List[Dict[str, Any]], account_id: str) -> List[Dict[str, Any]]:
    """Render search controls and return filtered setup list (unchanged)."""
    search_term = st.text_input(
        "🔍 Cerca Setup:", 
        key=f"setup_search_{account_id}",
        placeholder="MN, nome, simbolo...",
        help="Filtra setup per magic number, nome strategia o simbolo"
    )
    
    if search_term:
        filtered_setups = [
            s for s in setup_list 
            if search_term.lower() in s['Display_Name'].lower()
        ]
    else:
        filtered_setups = setup_list
    
    if search_term and len(filtered_setups) != len(setup_list):
        st.caption(f"Mostrando {len(filtered_setups)} di {len(setup_list)} setup")
    
    return filtered_setups


def _render_bulk_actions(filtered_setups: List[Dict[str, Any]], account_id: str):
    """
    Render bulk action buttons for setup selection using PENDING state.
    
    Args:
        filtered_setups: Filtered setup list
        account_id: Account identifier
    """
    if not filtered_setups:
        return
        
    st.markdown("**Azioni Bulk:**")
    
    col1, col2, col3 = st.columns(3)
    
    magic_numbers = [s['Magic_Number'] for s in filtered_setups]
    
    with col1:
        if st.button("✅ Tutti", key=f"select_all_pending_{account_id}", width="stretch"):
            count = _toggle_all_setups_pending(account_id, magic_numbers, select_all=True)
            st.success(f"✅ {count} setup attivati (pending)!")
    
    with col2:
        if st.button("❌ Nessuno", key=f"select_none_pending_{account_id}", width="stretch"):
            count = _toggle_all_setups_pending(account_id, magic_numbers, select_all=False)
            st.warning(f"❌ {count} setup disattivati (pending)!")
    
    with col3:
        if st.button("🔄 Inverti", key=f"invert_pending_{account_id}", width="stretch"):
            count = _invert_setup_selection_pending(account_id, magic_numbers)
            st.info(f"🔄 {count} setup invertiti (pending)!")


def _render_setup_checkboxes_pending(filtered_setups: List[Dict[str, Any]], account_id: str):
    """
    Render setup checkboxes using PENDING state keys.
    
    Args:
        filtered_setups: Filtered setup list
        account_id: Account identifier
    """
    if not filtered_setups:
        st.info("Nessun setup trovato con i criteri di ricerca")
        return
    
    st.markdown("**Setup Disponibili:**")
    
    for i, setup in enumerate(filtered_setups):
        # Use PENDING keys
        pending_setup_key = f"pending_setup_{account_id}_{setup['Magic_Number']}"
        
        # Initialize pending state if not exists
        if pending_setup_key not in st.session_state:
            st.session_state[pending_setup_key] = True
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            is_selected = st.checkbox(
                setup['Display_Name'],
                value=st.session_state[pending_setup_key],
                key=f"{pending_setup_key}_cb_{i}",
                help=f"Seleziona setup {setup['Performance']} (pending - non applicato)"
            )
            
            # Update pending state
            st.session_state[pending_setup_key] = is_selected
        
        with col2:
            profit_color = "🟢" if setup['Profit'] >= 0 else "🔴"
            st.caption(f"{profit_color} {setup['Performance']}")
            
            # Show pending vs applied indicator
            _render_setup_pending_indicator(account_id, setup['Magic_Number'])


def _render_setup_pending_indicator(account_id: str, magic_number: int):
    """Show indicator if pending state differs from applied state for this setup."""
    pending_key = f"pending_setup_{account_id}_{magic_number}"
    applied_key = f"applied_setup_{account_id}_{magic_number}"
    
    pending_value = st.session_state.get(pending_key)
    applied_value = st.session_state.get(applied_key)
    
    if pending_value != applied_value:
        if pending_value:
            st.caption("⚠️ Attivazione pending")
        else:
            st.caption("⚠️ Disattivazione pending")


def _render_selection_summary_pending(filtered_setups: List[Dict[str, Any]], account_id: str):
    """
    Render selection summary for PENDING state.
    
    Args:
        filtered_setups: Filtered setup list
        account_id: Account identifier
    """
    if not filtered_setups:
        return
        
    # Count pending selected setups
    pending_selected_count = 0
    pending_total_profit = 0
    
    # Count applied selected setups for comparison
    applied_selected_count = 0
    applied_total_profit = 0
    
    for setup in filtered_setups:
        magic_number = setup['Magic_Number']
        
        # Pending state
        pending_key = f"pending_setup_{account_id}_{magic_number}"
        if st.session_state.get(pending_key, True):
            pending_selected_count += 1
            pending_total_profit += setup['Profit']
        
        # Applied state for comparison
        applied_key = f"applied_setup_{account_id}_{magic_number}"
        if st.session_state.get(applied_key, True):
            applied_selected_count += 1
            applied_total_profit += setup['Profit']
    
    # Show pending summary
    if pending_selected_count > 0:
        st.info(f"📋 {pending_selected_count}/{len(filtered_setups)} setup selezionati (pending)")
        
        if pending_total_profit != 0:
            profit_color = "🟢" if pending_total_profit >= 0 else "🔴"
            st.markdown(f"**Performance Combinata (pending):** {profit_color} €{pending_total_profit:.0f}")
    else:
        st.warning("⚠️ Nessun setup selezionato (pending)")
    
    # Show difference from applied state
    if pending_selected_count != applied_selected_count:
        diff = pending_selected_count - applied_selected_count
        if diff > 0:
            st.caption(f"⬆️ +{diff} setup rispetto all'applicato")
        else:
            st.caption(f"⬇️ {diff} setup rispetto all'applicato")


def _toggle_all_setups_pending(account_id: str, magic_numbers: List[int], select_all: bool = True) -> int:
    """Toggle all setups in PENDING state."""
    modified_count = 0
    
    for magic_number in magic_numbers:
        pending_key = f"pending_setup_{account_id}_{magic_number}"
        st.session_state[pending_key] = select_all
        modified_count += 1
    
    return modified_count


def _invert_setup_selection_pending(account_id: str, magic_numbers: List[int]) -> int:
    """Invert setup selection in PENDING state."""
    modified_count = 0
    
    for magic_number in magic_numbers:
        pending_key = f"pending_setup_{account_id}_{magic_number}"
        current_value = st.session_state.get(pending_key, True)
        st.session_state[pending_key] = not current_value
        modified_count += 1
    
    return modified_count


def get_pending_setup_selection_summary(account_id: str, trades_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get summary of PENDING setup selection.
    
    Args:
        account_id: Account identifier
        trades_df: Complete trades DataFrame
        
    Returns:
        Dict with pending setup selection summary
    """
    try:
        pending_magic_numbers = []
        applied_magic_numbers = []
        
        # Get pending selection
        for key in st.session_state:
            if key.startswith(f"pending_setup_{account_id}_") and st.session_state[key]:
                magic_str = key.replace(f"pending_setup_{account_id}_", "").split("_")[0]
                try:
                    magic_number = int(magic_str)
                    pending_magic_numbers.append(magic_number)
                except ValueError:
                    continue
        
        # Get applied selection for comparison
        for key in st.session_state:
            if key.startswith(f"applied_setup_{account_id}_") and st.session_state[key]:
                magic_str = key.replace(f"applied_setup_{account_id}_", "").split("_")[0]
                try:
                    magic_number = int(magic_str)
                    applied_magic_numbers.append(magic_number)
                except ValueError:
                    continue
        
        if trades_df.empty:
            return {
                'total_setups': 0,
                'pending_selected_count': len(pending_magic_numbers),
                'applied_selected_count': len(applied_magic_numbers),
                'has_changes': len(pending_magic_numbers) != len(applied_magic_numbers),
                'pending_performance': 0,
                'applied_performance': 0
            }
        
        total_setups = trades_df['MagicNumber'].nunique()
        
        # Calculate performance for pending selection
        if pending_magic_numbers:
            pending_trades = trades_df[trades_df['MagicNumber'].isin(pending_magic_numbers)]
            pending_performance = pending_trades.groupby('OpenPositionTicket')['PL'].sum().sum()
        else:
            pending_performance = 0
        
        # Calculate performance for applied selection
        if applied_magic_numbers:
            applied_trades = trades_df[trades_df['MagicNumber'].isin(applied_magic_numbers)]
            applied_performance = applied_trades.groupby('OpenPositionTicket')['PL'].sum().sum()
        else:
            applied_performance = 0
        
        return {
            'total_setups': total_setups,
            'pending_selected_count': len(pending_magic_numbers),
            'applied_selected_count': len(applied_magic_numbers),
            'pending_magic_numbers': pending_magic_numbers,
            'applied_magic_numbers': applied_magic_numbers,
            'has_changes': set(pending_magic_numbers) != set(applied_magic_numbers),
            'pending_performance': pending_performance,
            'applied_performance': applied_performance,
            'performance_difference': pending_performance - applied_performance
        }
    
    except Exception as e:
        st.error(f"Errore nel calcolo summary setup pending: {str(e)}")
        return {
            'total_setups': 0,
            'pending_selected_count': 0,
            'applied_selected_count': 0,
            'has_changes': False,
            'pending_performance': 0,
            'applied_performance': 0
        }


def reset_pending_setup_selection(account_id: str, trades_df: pd.DataFrame, select_all: bool = True) -> bool:
    """
    Reset PENDING setup selection to default state.
    
    Args:
        account_id: Account identifier
        trades_df: Complete trades DataFrame
        select_all: If True, select all setups; if False, deselect all
        
    Returns:
        True if reset was successful
    """
    try:
        if trades_df.empty:
            return False
        
        magic_numbers = trades_df['MagicNumber'].unique().tolist()
        count = _toggle_all_setups_pending(account_id, magic_numbers, select_all)
        
        return count > 0
    
    except Exception as e:
        st.error(f"Errore nel reset pending setup selection: {str(e)}")
        return False


def get_setup_selection_summary(account_id: str, trades_df: pd.DataFrame) -> Dict[str, Any]:
    """
    LEGACY FUNCTION: Get summary of current setup selection for external use.
    Redirects to pending setup selection summary for backward compatibility.
    
    Args:
        account_id: Account identifier
        trades_df: Complete trades DataFrame
        
    Returns:
        Dict with setup selection summary
    """
    return get_pending_setup_selection_summary(account_id, trades_df)


def get_pending_vs_applied_differences(account_id: str) -> Dict[str, List[int]]:
    """
    Get differences between pending and applied setup selection.
    
    Args:
        account_id: Account identifier
        
    Returns:
        Dict with added, removed, and unchanged setup lists
    """
    pending_setups = set()
    applied_setups = set()
    
    # Get pending setups
    for key in st.session_state:
        if key.startswith(f"pending_setup_{account_id}_") and st.session_state[key]:
            magic_str = key.replace(f"pending_setup_{account_id}_", "").split("_")[0]
            try:
                magic_number = int(magic_str)
                pending_setups.add(magic_number)
            except ValueError:
                continue
    
    # Get applied setups
    for key in st.session_state:
        if key.startswith(f"applied_setup_{account_id}_") and st.session_state[key]:
            magic_str = key.replace(f"applied_setup_{account_id}_", "").split("_")[0]
            try:
                magic_number = int(magic_str)
                applied_setups.add(magic_number)
            except ValueError:
                continue
    
    return {
        'added': list(pending_setups - applied_setups),
        'removed': list(applied_setups - pending_setups),
        'unchanged': list(pending_setups & applied_setups),
        'total_changes': len(pending_setups - applied_setups) + len(applied_setups - pending_setups)
    }