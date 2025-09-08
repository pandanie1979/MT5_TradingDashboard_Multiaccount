# MT5 Trading Dashboard - Advanced Filters Component
# File: tabs/performance/sidebar/filters.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Advanced filters panel for sidebar.
Handles trade type, profit thresholds, and symbol filtering.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional

from ..config.constants import FILTER_OPTIONS, get_session_key, VALIDATION
from ..utils.session_helpers import get_advanced_filters
from ..utils.formatting import format_filter_summary


def render_advanced_filters_panel(trades_df: pd.DataFrame, account_id: str):
    """
    Render advanced filters panel without column nesting.
    Uses vertical layout for all controls to avoid Streamlit column issues.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    st.markdown("**Filtri di Analisi:**")
    
    # Trade Type Filter
    _render_trade_type_filter(account_id)
    
    st.markdown("---")
    
    # Performance Thresholds
    _render_performance_thresholds(account_id)
    
    st.markdown("---")
    
    # Symbol Filter
    _render_symbol_filter(trades_df, account_id)
    
    st.markdown("---")
    
    # Filter Summary
    _render_filter_summary(account_id)


def _render_trade_type_filter(account_id: str):
    """
    Render trade type filter (Backtest/Live/All).
    
    Args:
        account_id: Account identifier
    """
    st.markdown("**Tipo Trade:**")
    
    trade_type_filter = st.selectbox(
        "Filtra per tipo",
        options=FILTER_OPTIONS["trade_types"],
        key=f"trade_type_filter_{account_id}",
        help="Filtra trade per origine (backtest vs live trading)"
    )
    
    # Show explanation for each filter type
    if trade_type_filter == "Solo Backtest":
        st.caption("🔘 Solo trade da Strategy Tester MT5")
    elif trade_type_filter == "Solo Live":
        st.caption("🔵 Solo trade da trading reale")
    else:
        st.caption("📊 Tutti i trade (backtest + live)")


def _render_performance_thresholds(account_id: str):
    """
    Render performance threshold filters.
    Uses vertical layout to avoid column nesting.
    
    Args:
        account_id: Account identifier
    """
    st.markdown("**Soglie Performance:**")
    
    # Minimum Profit Filter
    min_profit = st.number_input(
        "Profit Minimo (€)",
        value=None,
        min_value=VALIDATION["profit_threshold"]["min"],
        max_value=VALIDATION["profit_threshold"]["max"],
        key=f"min_profit_filter_{account_id}",
        help="Includi solo setup con profit >= soglia"
    )
    
    # Maximum Drawdown Filter
    max_drawdown = st.number_input(
        "Max Drawdown (€)",
        value=None,
        min_value=VALIDATION["drawdown_threshold"]["min"],
        max_value=VALIDATION["drawdown_threshold"]["max"],
        key=f"max_dd_filter_{account_id}",
        help="Includi solo setup con drawdown <= soglia"
    )
    
    # Show active thresholds
    active_thresholds = []
    if min_profit is not None:
        active_thresholds.append(f"Profit >= €{min_profit}")
    if max_drawdown is not None:
        active_thresholds.append(f"MaxDD <= €{max_drawdown}")
    
    if active_thresholds:
        st.caption("Soglie attive: " + " | ".join(active_thresholds))


def _render_symbol_filter(trades_df: pd.DataFrame, account_id: str):
    """
    Render symbol filter with multiselect.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    if trades_df.empty:
        st.info("Nessun simbolo disponibile")
        return
    
    st.markdown("**Simboli:**")
    
    # Get available symbols
    symbol_column = 'OrderSymbol' if 'OrderSymbol' in trades_df.columns else 'Symbol'
    if symbol_column in trades_df.columns:
        available_symbols = sorted(trades_df[symbol_column].dropna().unique())
        
        selected_symbols = st.multiselect(
            "Filtra simboli",
            options=available_symbols,
            default=available_symbols,  # All selected by default
            key=f"symbols_filter_{account_id}",
            help="Seleziona simboli da includere nell'analisi"
        )
        
        # Show selection summary
        if len(selected_symbols) == len(available_symbols):
            st.caption("📊 Tutti i simboli selezionati")
        elif len(selected_symbols) == 0:
            st.warning("⚠️ Nessun simbolo selezionato")
        else:
            st.caption(f"📈 {len(selected_symbols)}/{len(available_symbols)} simboli selezionati")
            
            # Show selected symbols if not too many
            if len(selected_symbols) <= 5:
                st.caption("Simboli: " + ", ".join(selected_symbols))
    else:
        st.warning("Colonna simboli non trovata nei dati")


def _render_filter_summary(account_id: str):
    """Render summary of currently active filters."""
    st.markdown("**Riepilogo Filtri:**")
    
    filters = get_advanced_filters(account_id)
    
    # Show detailed filter effects
    active_filters = []
    if filters['trade_type'] != "Tutti":
        active_filters.append(f"• Tipo: {filters['trade_type']}")
    
    if filters['min_profit'] is not None:
        active_filters.append(f"• Min Profit: €{filters['min_profit']} (filtra SETUP)")
    
    if filters['max_drawdown'] is not None:
        active_filters.append(f"• Max DD: €{filters['max_drawdown']} (filtra SETUP)")
    
    if filters['selected_symbols']:
        symbols_text = ", ".join(filters['selected_symbols'][:3])
        if len(filters['selected_symbols']) > 3:
            symbols_text += f" + {len(filters['selected_symbols'])-3} altri"
        active_filters.append(f"• Simboli: {symbols_text}")
    
    if active_filters:
        st.info("**Filtri Attivi:**\n" + "\n".join(active_filters))
        st.caption("💡 I filtri Profit/DD si applicano ai SETUP (magic numbers), non ai singoli trade")
    else:
        st.success("✅ Nessun filtro attivo")


def _reset_all_filters(account_id: str):
    """
    Reset all advanced filters to default values.
    
    Args:
        account_id: Account identifier
    """
    # Instead of modifying session state directly, we'll use st.rerun() 
    # to force widget recreation with default values
    
    # Remove the keys from session state so widgets will use defaults
    keys_to_remove = [
        f"trade_type_filter_{account_id}",
        f"min_profit_filter_{account_id}", 
        f"max_dd_filter_{account_id}",
        f"symbols_filter_{account_id}"
    ]
    
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]


def get_filter_statistics(trades_df: pd.DataFrame, account_id: str) -> Dict[str, Any]:
    """
    Get statistics about how filters affect the dataset.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
        
    Returns:
        Dict with filter impact statistics
    """
    from ..utils.session_helpers import apply_advanced_filters, get_current_period_trades
    
    if trades_df.empty:
        return {'error': 'No data available'}
    
    # Get current period trades
    period_trades = get_current_period_trades(trades_df, account_id)
    original_count = len(period_trades)
    
    if original_count == 0:
        return {'error': 'No trades in current period'}
    
    # Apply filters
    filters = get_advanced_filters(account_id)
    filtered_trades = apply_advanced_filters(period_trades, filters)
    filtered_count = len(filtered_trades)
    
    # Calculate impact
    filter_impact = {
        'original_deals': original_count,
        'filtered_deals': filtered_count,
        'deals_removed': original_count - filtered_count,
        'retention_percentage': (filtered_count / original_count * 100) if original_count > 0 else 0,
        'unique_trades_original': period_trades['OpenPositionTicket'].nunique(),
        'unique_trades_filtered': filtered_trades['OpenPositionTicket'].nunique() if not filtered_trades.empty else 0
    }
    
    # Add filter details
    filter_impact['active_filters'] = {
        'trade_type': filters['trade_type'] != "Tutti",
        'min_profit': filters['min_profit'] is not None,
        'max_drawdown': filters['max_drawdown'] is not None,
        'symbol_filter': len(filters['selected_symbols']) > 0
    }
    
    return filter_impact


def validate_filters(filters: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate filter values and return any errors.
    
    Args:
        filters: Filter configuration dict
        
    Returns:
        Dict with validation errors (empty if all valid)
    """
    errors = {}
    
    # Validate profit threshold
    if filters['min_profit'] is not None:
        min_val = VALIDATION["profit_threshold"]["min"]
        max_val = VALIDATION["profit_threshold"]["max"]
        if not (min_val <= filters['min_profit'] <= max_val):
            errors['min_profit'] = f"Deve essere tra {min_val} e {max_val}"
    
    # Validate drawdown threshold
    if filters['max_drawdown'] is not None:
        min_val = VALIDATION["drawdown_threshold"]["min"]
        max_val = VALIDATION["drawdown_threshold"]["max"]
        if not (min_val <= filters['max_drawdown'] <= max_val):
            errors['max_drawdown'] = f"Deve essere tra {min_val} e {max_val}"
    
    return errors