# MT5 Trading Dashboard - Setup Selection Component (PROFIT PERIOD FIXED)
# File: tabs/performance/sidebar/setup_selection.py
# Fixed: September 2025 - Fixed profit calculation to use period-filtered data

"""
Setup selection component for sidebar.
FIXED: Profit calculation now uses period-filtered data instead of complete dataset.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

from ..utils.formatting import format_profit_indicator
from ..config.constants import get_session_key


def render_setup_selection_clean(trades_df: pd.DataFrame, account_id: str):
    """
    Setup selection using PENDING state.
    FIXED: Now calculates profit based on applied period instead of complete dataset.
    
    Args:
        trades_df: Complete trades DataFrame  
        account_id: Account identifier
    """
    if trades_df.empty:
        st.warning("Nessun trade disponibile")
        return
    
    # CRITICAL FIX: Use period-filtered data for profit calculations
    period_filtered_trades = _get_period_filtered_trades(trades_df, account_id)
    
    if period_filtered_trades.empty:
        st.info("Nessun trade nel periodo selezionato")
        # Still show setups but with zero profit
        setup_list = _calculate_setup_list_with_period(trades_df, period_filtered_trades, account_id)
    else:
        # Calculate setups with period-specific profit
        setup_list = _calculate_setup_list_with_period(trades_df, period_filtered_trades, account_id)
    
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


def _get_period_filtered_trades(trades_df: pd.DataFrame, account_id: str) -> pd.DataFrame:
    """
    Get trades filtered by APPLIED period configuration.
    This ensures profit calculations match the current applied period.
    """
    from ..utils.session_helpers import get_applied_period_configuration
    
    # Get applied period configuration
    period_config = get_applied_period_configuration(account_id)
    
    if not period_config:
        # If no period configured, use last 30 days as default
        if not trades_df.empty:
            max_date = trades_df['OpenDatetime'].max()
            start_date = max_date - pd.Timedelta(days=30)
            return trades_df[trades_df['OpenDatetime'] >= start_date]
        else:
            return trades_df
    
    # Filter by applied period
    filtered_trades = trades_df[
        (trades_df['OpenDatetime'] >= period_config['start_datetime']) & 
        (trades_df['OpenDatetime'] <= period_config['end_datetime'])
    ]
    
    return filtered_trades


def _calculate_setup_list_with_period(complete_trades_df: pd.DataFrame, 
                                    period_trades_df: pd.DataFrame, 
                                    account_id: str) -> List[Dict[str, Any]]:
    """
    Calculate setup list with period-specific profit calculations.
    FIXED: Uses period_trades_df for profit but complete_trades_df for setup info.
    
    Args:
        complete_trades_df: Complete trades for setup identification
        period_trades_df: Period-filtered trades for profit calculation
        account_id: Account identifier
    """
    if complete_trades_df.empty:
        return []
    
    setup_list = []
    
    try:
        # Get all available magic numbers from complete dataset
        all_magic_numbers = complete_trades_df['MagicNumber'].unique()
        
        for magic_number in all_magic_numbers:
            # Get setup info from complete dataset (for strategy name, symbol)
            complete_setup_trades = complete_trades_df[complete_trades_df['MagicNumber'] == magic_number]
            
            if complete_setup_trades.empty:
                continue
                
            first_trade = complete_setup_trades.iloc[0]
            
            setup_name = first_trade.get('StrategyName', 
                        first_trade.get('StrategyFromFile', 
                        f'Strategy_{magic_number}'))
            
            symbol = first_trade.get('OrderSymbol', 
                    first_trade.get('Symbol', 'Unknown'))
            
            # CRITICAL: Calculate profit only from period-filtered data
            period_setup_trades = period_trades_df[period_trades_df['MagicNumber'] == magic_number]
            
            if period_setup_trades.empty:
                # Setup exists but no trades in period
                setup_profit = 0.0
                setup_trades_count = 0
            else:
                try:
                    # Calculate profit from period data only
                    unique_trades = period_setup_trades.groupby('OpenPositionTicket')['PL'].sum()
                    setup_profit = unique_trades.sum()
                    setup_trades_count = len(unique_trades)
                except Exception:
                    setup_profit = period_setup_trades['PL'].sum()
                    setup_trades_count = period_setup_trades['OpenPositionTicket'].nunique()
            
            # Get applied period info for display
            period_info = _get_period_display_info(account_id)
            
            setup_list.append({
                'Magic_Number': magic_number,
                'Setup_Name': setup_name,
                'Symbol': symbol,
                'Profit': setup_profit,
                'Trades_Count': setup_trades_count,
                'Display_Name': f"MN{magic_number} - {setup_name} ({symbol})",
                'Performance': f"€{setup_profit:.0f} ({setup_trades_count}T)",
                'Period_Info': period_info,  # Add period context
                'Has_Period_Data': setup_trades_count > 0
            })
    
    except Exception as e:
        st.error(f"Errore nel calcolo setup: {str(e)}")
        return []
    
    # Sort by profit (period-specific)
    setup_list.sort(key=lambda x: x['Profit'], reverse=True)
    return setup_list


def _get_period_display_info(account_id: str) -> str:
    """Get period information for display context."""
    from ..utils.session_helpers import get_applied_period_configuration
    
    period_config = get_applied_period_configuration(account_id)
    
    if not period_config:
        return "Ultimo mese"
    
    start_date = period_config['start_date']
    end_date = period_config['end_date']
    days_span = (end_date - start_date).days
    
    return f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')} ({days_span}g)"


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
        if st.button("✅ Tutti", key=f"select_all_pending_{account_id}", use_container_width=True):
            count = _toggle_all_setups_pending(account_id, magic_numbers, select_all=True)
            st.success(f"✅ {count} setup attivati (pending)!")
    
    with col2:
        if st.button("❌ Nessuno", key=f"select_none_pending_{account_id}", use_container_width=True):
            count = _toggle_all_setups_pending(account_id, magic_numbers, select_all=False)
            st.warning(f"❌ {count} setup disattivati (pending)!")
    
    with col3:
        if st.button("🔄 Inverti", key=f"invert_pending_{account_id}", use_container_width=True):
            count = _invert_setup_selection_pending(account_id, magic_numbers)
            st.info(f"🔄 {count} setup invertiti (pending)!")


def _render_setup_checkboxes_pending(filtered_setups: List[Dict[str, Any]], account_id: str):
    """
    Render setup checkboxes with PERIOD-SPECIFIC profit display.
    
    Args:
        filtered_setups: Filtered setup list with period-specific profits
        account_id: Account identifier
    """
    if not filtered_setups:
        st.info("Nessun setup trovato con i criteri di ricerca")
        return
    
    st.markdown("**Setup Disponibili:**")
    
    # Show period context
    period_info = _get_period_display_info(account_id)
    st.caption(f"💡 **Profitti mostrati per periodo**: {period_info}")
    
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
                help=f"Seleziona setup - Periodo: {setup['Period_Info']} (pending - non applicato)"
            )
            
            # Update pending state
            st.session_state[pending_setup_key] = is_selected
        
        with col2:
            # Show period-specific profit with indicator
            if setup['Has_Period_Data']:
                profit_color = "🟢" if setup['Profit'] >= 0 else "🔴"
                st.caption(f"{profit_color} {setup['Performance']}")
            else:
                st.caption("⭕ €0 (0T)")  # No trades in period
            
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
    Render selection summary for PENDING state with PERIOD-SPECIFIC profits.
    
    Args:
        filtered_setups: Filtered setup list with period profits
        account_id: Account identifier
    """
    if not filtered_setups:
        return
        
    # Count pending selected setups with period-specific profit
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
            pending_total_profit += setup['Profit']  # Period-specific profit
        
        # Applied state for comparison
        applied_key = f"applied_setup_{account_id}_{magic_number}"
        if st.session_state.get(applied_key, True):
            applied_selected_count += 1
            applied_total_profit += setup['Profit']  # Period-specific profit
    
    # Show pending summary with period context
    period_info = _get_period_display_info(account_id)
    
    if pending_selected_count > 0:
        st.info(f"📋 {pending_selected_count}/{len(filtered_setups)} setup selezionati (pending)")
        st.caption(f"📅 **Periodo**: {period_info}")
        
        if pending_total_profit != 0:
            profit_color = "🟢" if pending_total_profit >= 0 else "🔴"
            st.markdown(f"**Performance Periodo (pending):** {profit_color} €{pending_total_profit:.0f}")
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
    Get summary of PENDING setup selection with PERIOD-SPECIFIC data.
    
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
        
        # CRITICAL: Use period-filtered data for performance calculation
        period_trades = _get_period_filtered_trades(trades_df, account_id)
        
        # Calculate performance for pending selection (period-specific)
        if pending_magic_numbers and not period_trades.empty:
            pending_trades = period_trades[period_trades['MagicNumber'].isin(pending_magic_numbers)]
            pending_performance = pending_trades.groupby('OpenPositionTicket')['PL'].sum().sum()
        else:
            pending_performance = 0
        
        # Calculate performance for applied selection (period-specific)
        if applied_magic_numbers and not period_trades.empty:
            applied_trades = period_trades[period_trades['MagicNumber'].isin(applied_magic_numbers)]
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
            'performance_difference': pending_performance - applied_performance,
            'period_info': _get_period_display_info(account_id)
        }
    
    except Exception as e:
        st.error(f"Errore nel calcolo summary setup pending: {str(e)}")
        return {
            'total_setups': 0,
            'pending_selected_count': 0,
            'applied_selected_count': 0,
            'has_changes': False,
            'pending_performance': 0,
            'applied_performance': 0,
            'period_info': 'Errore calcolo periodo'
        }


# Legacy compatibility function
def get_setup_selection_summary(account_id: str, trades_df: pd.DataFrame) -> Dict[str, Any]:
    """
    LEGACY FUNCTION: Get summary of current setup selection for external use.
    Redirects to pending setup selection summary for backward compatibility.
    """
    return get_pending_setup_selection_summary(account_id, trades_df)