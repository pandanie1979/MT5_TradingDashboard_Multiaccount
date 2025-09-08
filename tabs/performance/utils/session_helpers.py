# MT5 Trading Dashboard - Session State Helpers (DUAL STATE SYSTEM)
# File: tabs/performance/utils/session_helpers.py
# Modified: September 2025 - Added dual state (pending/applied) system

"""
Session state management utilities for performance tab.
ADDED: Dual state system with pending/applied separation for manual updates.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple

from ..config.constants import (
    SESSION_KEYS, PERIOD_PRESETS, DEFAULTS, 
    get_session_key, validate_sidebar_width
)


# ============================================================================
# DUAL STATE SYSTEM - Core Functions
# ============================================================================

def detect_pending_changes(account_id: str) -> bool:
    """
    Detect if there are pending changes not yet applied.
    
    Args:
        account_id: Account identifier
        
    Returns:
        True if pending state differs from applied state
    """
    # Check period changes
    period_changed = _detect_period_changes(account_id)
    
    # Check setup changes  
    setup_changed = _detect_setup_changes(account_id)
    
    return period_changed or setup_changed


def apply_pending_changes(account_id: str) -> Dict[str, int]:
    """
    Apply all pending changes to applied state.
    
    Args:
        account_id: Account identifier
        
    Returns:
        Dict with counts of applied changes
    """
    changes_applied = {
        'period_changes': 0,
        'setup_changes': 0,
        'total_changes': 0
    }
    
    # Apply period changes
    if _apply_pending_period(account_id):
        changes_applied['period_changes'] = 1
    
    # Apply setup changes
    setup_count = _apply_pending_setups(account_id)
    changes_applied['setup_changes'] = setup_count
    
    changes_applied['total_changes'] = changes_applied['period_changes'] + changes_applied['setup_changes']
    
    return changes_applied


def get_applied_period_configuration(account_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the APPLIED period configuration (used by charts/metrics).
    
    Args:
        account_id: Account identifier
        
    Returns:
        Dict with applied period configuration or None
    """
    start_key = f"applied_start_{account_id}"
    end_key = f"applied_end_{account_id}"
    
    start_date = st.session_state.get(start_key)
    end_date = st.session_state.get(end_key)
    
    # Fallback to old keys for backward compatibility
    if start_date is None:
        old_start_key = f"date_start_{account_id}"
        start_date = st.session_state.get(old_start_key)
        if start_date:
            st.session_state[start_key] = start_date  # Auto-migrate
    
    if end_date is None:
        old_end_key = f"date_end_{account_id}"
        end_date = st.session_state.get(old_end_key)
        if end_date:
            st.session_state[end_key] = end_date  # Auto-migrate
    
    if not start_date or not end_date:
        return None
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'start_datetime': pd.to_datetime(start_date),
        'end_datetime': pd.to_datetime(end_date) + pd.Timedelta(days=1)
    }


def get_applied_selected_setups(account_id: str) -> List[int]:
    """
    Get the APPLIED setup selection (used by charts/metrics).
    
    Args:
        account_id: Account identifier
        
    Returns:
        List of applied selected magic numbers
    """
    selected_setups = []
    
    # Search for applied setup keys
    for key in st.session_state:
        if key.startswith(f"applied_setup_{account_id}_") and st.session_state[key]:
            magic_str = key.replace(f"applied_setup_{account_id}_", "").split("_")[0]
            try:
                magic_number = int(magic_str)
                selected_setups.append(magic_number)
            except ValueError:
                continue
    
    # Fallback to old keys for backward compatibility
    if not selected_setups:
        for key in st.session_state:
            if key.startswith(f"setup_{account_id}_") and st.session_state[key]:
                magic_str = key.replace(f"setup_{account_id}_", "").split("_")[0]
                try:
                    magic_number = int(magic_str)
                    selected_setups.append(magic_number)
                    # Auto-migrate
                    applied_key = f"applied_setup_{account_id}_{magic_number}"
                    st.session_state[applied_key] = True
                except ValueError:
                    continue
    
    return selected_setups


def get_current_period_trades(trades_df: pd.DataFrame, account_id: str) -> pd.DataFrame:
    """
    Get trades filtered by APPLIED period and setup selection.
    MODIFIED: Uses applied state instead of pending state.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
        
    Returns:
        DataFrame filtered by applied period and setup selection
    """
    if trades_df.empty:
        return trades_df
    
    # Apply period filter using APPLIED configuration
    period_config = get_applied_period_configuration(account_id)
    if period_config:
        filtered_df = trades_df[
            (trades_df['OpenDatetime'] >= period_config['start_datetime']) & 
            (trades_df['OpenDatetime'] <= period_config['end_datetime'])
        ]
    else:
        filtered_df = trades_df
    
    # Apply setup filter using APPLIED selection
    selected_setups = get_applied_selected_setups(account_id)
    if selected_setups:
        filtered_df = filtered_df[filtered_df['MagicNumber'].isin(selected_setups)]
    
    return filtered_df


# ============================================================================
# PRIVATE HELPER FUNCTIONS
# ============================================================================

def _detect_period_changes(account_id: str) -> bool:
    """Check if period configuration has pending changes."""
    pending_start = st.session_state.get(f"pending_start_{account_id}")
    pending_end = st.session_state.get(f"pending_end_{account_id}")
    
    applied_start = st.session_state.get(f"applied_start_{account_id}")
    applied_end = st.session_state.get(f"applied_end_{account_id}")
    
    return pending_start != applied_start or pending_end != applied_end


def _detect_setup_changes(account_id: str) -> bool:
    """Check if setup selection has pending changes."""
    # Get all pending setup keys
    pending_setups = {}
    for key in st.session_state:
        if key.startswith(f"pending_setup_{account_id}_"):
            magic_str = key.replace(f"pending_setup_{account_id}_", "").split("_")[0]
            try:
                magic_number = int(magic_str)
                pending_setups[magic_number] = st.session_state[key]
            except ValueError:
                continue
    
    # Get all applied setup keys
    applied_setups = {}
    for key in st.session_state:
        if key.startswith(f"applied_setup_{account_id}_"):
            magic_str = key.replace(f"applied_setup_{account_id}_", "").split("_")[0]
            try:
                magic_number = int(magic_str)
                applied_setups[magic_number] = st.session_state[key]
            except ValueError:
                continue
    
    return pending_setups != applied_setups


def _apply_pending_period(account_id: str) -> bool:
    """Apply pending period changes to applied state."""
    pending_start = st.session_state.get(f"pending_start_{account_id}")
    pending_end = st.session_state.get(f"pending_end_{account_id}")
    
    if pending_start is not None:
        st.session_state[f"applied_start_{account_id}"] = pending_start
    
    if pending_end is not None:
        st.session_state[f"applied_end_{account_id}"] = pending_end
    
    return pending_start is not None or pending_end is not None


def _apply_pending_setups(account_id: str) -> int:
    """Apply pending setup changes to applied state."""
    changes_count = 0
    
    # Copy all pending setup states to applied
    for key in list(st.session_state.keys()):
        if key.startswith(f"pending_setup_{account_id}_"):
            applied_key = key.replace("pending_", "applied_")
            st.session_state[applied_key] = st.session_state[key]
            changes_count += 1
    
    return changes_count


# ============================================================================
# INITIALIZATION AND COMPATIBILITY
# ============================================================================

def initialize_dual_state_for_account(account_id: str, trades_df: pd.DataFrame):
    """
    Initialize dual state system for an account.
    Creates both pending and applied states with same initial values.
    
    Args:
        account_id: Account identifier
        trades_df: Complete trades DataFrame for date range calculation
    """
    # Initialize period state
    _initialize_period_dual_state(account_id, trades_df)
    
    # Initialize setup state
    _initialize_setup_dual_state(account_id, trades_df)


def _initialize_period_dual_state(account_id: str, trades_df: pd.DataFrame):
    """Initialize period dual state."""
    pending_start_key = f"pending_start_{account_id}"
    pending_end_key = f"pending_end_{account_id}"
    applied_start_key = f"applied_start_{account_id}"
    applied_end_key = f"applied_end_{account_id}"
    
    # Calculate default period if not exists
    if (pending_start_key not in st.session_state or 
        applied_start_key not in st.session_state):
        
        if not trades_df.empty:
            data_start = trades_df['OpenDatetime'].min().date()
            data_end = trades_df['OpenDatetime'].max().date()
            
            default_end = min(datetime.now().date(), data_end)
            default_start = max(data_start, default_end - timedelta(days=30))
        else:
            default_end = datetime.now().date()
            default_start = default_end - timedelta(days=30)
        
        # Initialize both pending and applied with same values
        st.session_state[pending_start_key] = default_start
        st.session_state[pending_end_key] = default_end
        st.session_state[applied_start_key] = default_start
        st.session_state[applied_end_key] = default_end


def _initialize_setup_dual_state(account_id: str, trades_df: pd.DataFrame):
    """Initialize setup dual state."""
    if trades_df.empty:
        return
    
    # Get all available magic numbers
    magic_numbers = trades_df['MagicNumber'].unique()
    
    for magic_number in magic_numbers:
        pending_key = f"pending_setup_{account_id}_{magic_number}"
        applied_key = f"applied_setup_{account_id}_{magic_number}"
        
        # Initialize both with default selection (True)
        if pending_key not in st.session_state:
            st.session_state[pending_key] = DEFAULTS["setup_selected"]
        
        if applied_key not in st.session_state:
            st.session_state[applied_key] = DEFAULTS["setup_selected"]


# ============================================================================
# LEGACY COMPATIBILITY FUNCTIONS (kept for backward compatibility)
# ============================================================================

def get_period_configuration(account_id: str) -> Optional[Dict[str, Any]]:
    """Legacy function - redirects to applied configuration."""
    return get_applied_period_configuration(account_id)


def get_selected_setups(account_id: str) -> List[int]:
    """Legacy function - redirects to applied selection."""
    return get_applied_selected_setups(account_id)


def mark_period_as_user_modified(account_id: str):
    """Legacy function - kept for compatibility but no longer used."""
    period_initialized_key = f"period_user_set_{account_id}"
    st.session_state[period_initialized_key] = "user_modified"


# ============================================================================
# OTHER EXISTING FUNCTIONS (unchanged)
# ============================================================================

def get_advanced_filters(account_id: str) -> Dict[str, Any]:
    """Get advanced filters from session state (unchanged)."""
    return {
        'trade_type': st.session_state.get(
            get_session_key("trade_type_filter", account_id), "Tutti"
        ),
        'min_profit': st.session_state.get(
            get_session_key("min_profit_filter", account_id)
        ),
        'max_drawdown': st.session_state.get(
            get_session_key("max_dd_filter", account_id)
        ),
        'selected_symbols': st.session_state.get(
            get_session_key("symbols_filter", account_id), []
        )
    }


def apply_advanced_filters(trades_df: pd.DataFrame, 
                          filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply advanced filters to trades (unchanged)."""
    if trades_df.empty:
        return trades_df
    
    filtered_df = trades_df.copy()
    
    # Filtro tipo trade
    if filters['trade_type'] == "Solo Backtest":
        from .data_processing import classify_trades_backtest_vs_live
        classified_df = classify_trades_backtest_vs_live(filtered_df)
        filtered_df = classified_df[classified_df['trade_type'] == 'backtest']
    elif filters['trade_type'] == "Solo Live":
        from .data_processing import classify_trades_backtest_vs_live
        classified_df = classify_trades_backtest_vs_live(filtered_df)
        filtered_df = classified_df[classified_df['trade_type'] == 'live']
    
    # Filtro profit minimo
    if filters['min_profit'] is not None:
        trade_profits = filtered_df.groupby('OpenPositionTicket')['PL'].sum()
        valid_tickets = trade_profits[trade_profits >= filters['min_profit']].index
        filtered_df = filtered_df[filtered_df['OpenPositionTicket'].isin(valid_tickets)]
    
    # Filtro simboli
    if filters['selected_symbols'] and 'OrderSymbol' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['OrderSymbol'].isin(filters['selected_symbols'])]
    
    return filtered_df


def apply_period_filters(trades_df: pd.DataFrame, 
                        period_config: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """
    Apply period filters to trades (uses applied configuration).
    
    Args:
        trades_df: DataFrame with trades
        period_config: Period configuration (from get_applied_period_configuration)
        
    Returns:
        DataFrame filtered by period
    """
    if not period_config or trades_df.empty:
        return trades_df
    
    return trades_df[
        (trades_df['OpenDatetime'] >= period_config['start_datetime']) & 
        (trades_df['OpenDatetime'] <= period_config['end_datetime'])
    ]


def calculate_preset_dates(preset: str, min_date: date, max_date: date) -> Tuple[date, date]:
    """Calculate default dates based on selected preset (unchanged)."""
    end_date = max_date
    
    if preset in PERIOD_PRESETS:
        days = PERIOD_PRESETS[preset]["days"]
        if days is None:  # YTD
            start_date = max(min_date, datetime(end_date.year, 1, 1).date())
        else:
            start_date = max(min_date, end_date - timedelta(days=days))
    else:
        # Default 30 giorni
        start_date = max(min_date, end_date - timedelta(days=30))
    
    return start_date, end_date


def get_sidebar_width(account_id: str) -> int:
    """Get sidebar width for account with validation (unchanged)."""
    width_key = get_session_key("sidebar_width", account_id)
    width = st.session_state.get(width_key, DEFAULTS["sidebar_width"])
    return validate_sidebar_width(width)


def set_sidebar_width(account_id: str, width: int) -> bool:
    """Set sidebar width for account (unchanged)."""
    validated_width = validate_sidebar_width(width)
    width_key = get_session_key("sidebar_width", account_id)
    st.session_state[width_key] = validated_width
    return True


def toggle_all_setups(account_id: str, magic_numbers: List[int], 
                     select_all: bool = True) -> int:
    """
    Toggle all setups for an account (LEGACY - uses applied keys).
    
    Args:
        account_id: Account ID
        magic_numbers: List of available magic numbers
        select_all: True to select all, False to deselect
        
    Returns:
        Number of setups modified
    """
    modified_count = 0
    
    for magic_number in magic_numbers:
        setup_key = f"applied_setup_{account_id}_{magic_number}"
        st.session_state[setup_key] = select_all
        modified_count += 1
    
    return modified_count


def invert_setup_selection(account_id: str, magic_numbers: List[int]) -> int:
    """
    Invert setup selection for an account (LEGACY - uses applied keys).
    
    Args:
        account_id: Account ID
        magic_numbers: List of available magic numbers
        
    Returns:
        Number of setups modified
    """
    modified_count = 0
    
    for magic_number in magic_numbers:
        setup_key = f"applied_setup_{account_id}_{magic_number}"
        if setup_key in st.session_state:
            current_value = st.session_state[setup_key]
            st.session_state[setup_key] = not current_value
            modified_count += 1
        else:
            st.session_state[setup_key] = True
            modified_count += 1
    
    return modified_count


def get_setup_search_term(account_id: str) -> str:
    """
    Get search term for setups.
    
    Args:
        account_id: Account ID
        
    Returns:
        Current search term
    """
    search_key = get_session_key("setup_search", account_id)
    return st.session_state.get(search_key, "")


def validate_date_range(start_date: date, end_date: date) -> Tuple[bool, str]:
    """
    Validate a date range.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if start_date > end_date:
        return False, "Data inizio deve essere ≤ data fine"
    
    # Check range is not too large (e.g. > 2 years)
    max_days = 730  # 2 years
    if (end_date - start_date).days > max_days:
        return False, f"Range massimo consentito: {max_days} giorni"
    
    return True, ""


def get_filter_summary(account_id: str) -> str:
    """
    Get textual summary of active filters.
    
    Args:
        account_id: Account ID
        
    Returns:
        String with filter summary
    """
    filters = get_advanced_filters(account_id)
    period_config = get_applied_period_configuration(account_id)
    selected_setups = get_applied_selected_setups(account_id)
    
    summary_parts = []
    
    # Period
    if period_config:
        days = (period_config['end_date'] - period_config['start_date']).days
        summary_parts.append(f"Periodo: {days} giorni")
    
    # Setup
    if selected_setups:
        summary_parts.append(f"Setup: {len(selected_setups)} selezionati")
    
    # Trade type
    if filters['trade_type'] != "Tutti":
        summary_parts.append(f"Tipo: {filters['trade_type']}")
    
    # Numeric filters
    if filters['min_profit'] is not None:
        summary_parts.append(f"Min Profit: €{filters['min_profit']}")
    
    if filters['max_drawdown'] is not None:
        summary_parts.append(f"Max DD: €{filters['max_drawdown']}")
    
    # Symbols
    if filters['selected_symbols']:
        symbol_count = len(filters['selected_symbols'])
        summary_parts.append(f"Simboli: {symbol_count}")
    
    return " | ".join(summary_parts) if summary_parts else "Nessun filtro attivo"


def clear_account_session_state(account_id: str) -> int:
    """
    Clear all session state data for a specific account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Number of keys removed
    """
    keys_to_remove = []
    
    # Find all keys containing the account_id
    for key in st.session_state.keys():
        if account_id in key:
            keys_to_remove.append(key)
    
    # Remove keys
    for key in keys_to_remove:
        del st.session_state[key]
    
    return len(keys_to_remove)


def export_session_config(account_id: str) -> Dict[str, Any]:
    """
    Export session state configuration for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Dict with exportable configuration
    """
    config = {
        'account_id': account_id,
        'export_timestamp': datetime.now().isoformat(),
        'sidebar_width': get_sidebar_width(account_id),
        'applied_period_config': get_applied_period_configuration(account_id),
        'applied_selected_setups': get_applied_selected_setups(account_id),
        'advanced_filters': get_advanced_filters(account_id),
        'search_term': get_setup_search_term(account_id),
        'pending_changes': detect_pending_changes(account_id)
    }
    
    return config


def import_session_config(account_id: str, config: Dict[str, Any]) -> bool:
    """
    Import session state configuration for an account.
    
    Args:
        account_id: Account ID
        config: Dict with configuration to import
        
    Returns:
        True if import was successful
    """
    try:
        # Sidebar width
        if 'sidebar_width' in config:
            set_sidebar_width(account_id, config['sidebar_width'])
        
        # Applied period config
        if 'applied_period_config' in config and config['applied_period_config']:
            period_config = config['applied_period_config']
            st.session_state[f"applied_start_{account_id}"] = period_config['start_date']
            st.session_state[f"applied_end_{account_id}"] = period_config['end_date']
            
            # Also set pending to same values
            st.session_state[f"pending_start_{account_id}"] = period_config['start_date']
            st.session_state[f"pending_end_{account_id}"] = period_config['end_date']
        
        # Applied setup selections
        if 'applied_selected_setups' in config:
            # First clear existing selections
            for key in list(st.session_state.keys()):
                if key.startswith(f"applied_setup_{account_id}_"):
                    st.session_state[key] = False
                if key.startswith(f"pending_setup_{account_id}_"):
                    st.session_state[key] = False
            
            # Set selected setups
            for magic_number in config['applied_selected_setups']:
                st.session_state[f"applied_setup_{account_id}_{magic_number}"] = True
                st.session_state[f"pending_setup_{account_id}_{magic_number}"] = True
        
        # Advanced filters
        if 'advanced_filters' in config:
            filters = config['advanced_filters']
            
            if 'trade_type' in filters:
                filter_key = get_session_key("trade_type_filter", account_id)
                st.session_state[filter_key] = filters['trade_type']
            
            if 'min_profit' in filters:
                filter_key = get_session_key("min_profit_filter", account_id)
                st.session_state[filter_key] = filters['min_profit']
            
            if 'max_drawdown' in filters:
                filter_key = get_session_key("max_dd_filter", account_id)
                st.session_state[filter_key] = filters['max_drawdown']
            
            if 'selected_symbols' in filters:
                filter_key = get_session_key("symbols_filter", account_id)
                st.session_state[filter_key] = filters['selected_symbols']
        
        return True
        
    except Exception as e:
        st.error(f"Errore nell'importazione configurazione: {str(e)}")
        return False


def cleanup_large_session_objects(account_id: str, max_objects: int = 50):
    """
    Clean up large or old session objects.
    
    Args:
        account_id: Account identifier
        max_objects: Maximum number of objects per account
    """
    account_keys = [k for k in st.session_state.keys() if account_id in k]
    
    # Remove older objects if too many
    if len(account_keys) > max_objects:
        sorted_keys = sorted(account_keys)
        keys_to_remove = sorted_keys[:-max_objects]
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        st.info(f"Puliti {len(keys_to_remove)} oggetti sessione obsoleti")


def reset_period_selection_to_default(account_id: str, trades_df: pd.DataFrame) -> bool:
    """
    Reset period selection to default values (both pending and applied).
    
    Args:
        account_id: Account identifier
        trades_df: DataFrame for date range calculation
        
    Returns:
        True if reset was successful
    """
    if trades_df.empty:
        return False
    
    # Calculate range
    data_start = trades_df['OpenDatetime'].min().date()
    data_end = trades_df['OpenDatetime'].max().date()
    
    # Calculate default (last 30 days)
    default_end = min(datetime.now().date(), data_end)
    default_start = max(data_start, default_end - timedelta(days=30))
    
    # Update both pending and applied
    st.session_state[f"pending_start_{account_id}"] = default_start
    st.session_state[f"pending_end_{account_id}"] = default_end
    st.session_state[f"applied_start_{account_id}"] = default_start
    st.session_state[f"applied_end_{account_id}"] = default_end
    
    return True


def get_dual_state_summary(account_id: str) -> Dict[str, Any]:
    """
    Get comprehensive summary of dual state system for debugging.
    
    Args:
        account_id: Account identifier
        
    Returns:
        Dict with dual state summary
    """
    return {
        'account_id': account_id,
        'has_pending_changes': detect_pending_changes(account_id),
        'pending_period': {
            'start': st.session_state.get(f"pending_start_{account_id}"),
            'end': st.session_state.get(f"pending_end_{account_id}")
        },
        'applied_period': {
            'start': st.session_state.get(f"applied_start_{account_id}"),
            'end': st.session_state.get(f"applied_end_{account_id}")
        },
        'pending_setup_count': len([k for k in st.session_state.keys() 
                                   if k.startswith(f"pending_setup_{account_id}_") and st.session_state[k]]),
        'applied_setup_count': len([k for k in st.session_state.keys() 
                                   if k.startswith(f"applied_setup_{account_id}_") and st.session_state[k]]),
        'system_ready': True
    }