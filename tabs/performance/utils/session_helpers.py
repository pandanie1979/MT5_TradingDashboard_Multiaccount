# MT5 Trading Dashboard - Session State Helpers
# File: tabs/performance/utils/session_helpers.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple

from ..config.constants import (
    SESSION_KEYS, PERIOD_PRESETS, DEFAULTS,
    get_session_key, validate_sidebar_width
)


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_performance_state(account_id: str, trades_df: pd.DataFrame):
    """
    Initialize canonical session state keys for the performance tab.
    Called once per account per session, guarded by the caller.
    """
    _initialize_period_state(account_id, trades_df)
    _initialize_setup_state(account_id, trades_df)


def _initialize_period_state(account_id: str, trades_df: pd.DataFrame):
    start_key = get_session_key("period_start", account_id)
    end_key = get_session_key("period_end", account_id)

    if start_key not in st.session_state:
        if not trades_df.empty:
            data_start = trades_df['OpenDatetime'].min().date()
            data_end = trades_df['OpenDatetime'].max().date()
            default_end = min(datetime.now().date(), data_end)
            default_start = max(data_start, default_end - timedelta(days=30))
        else:
            default_end = datetime.now().date()
            default_start = default_end - timedelta(days=30)

        st.session_state[start_key] = default_start
        st.session_state[end_key] = default_end


def _initialize_setup_state(account_id: str, trades_df: pd.DataFrame):
    if trades_df.empty:
        return

    for magic_number in trades_df['MagicNumber'].unique():
        setup_key = get_session_key("setup_selection", account_id, magic_number=magic_number)
        if setup_key not in st.session_state:
            st.session_state[setup_key] = DEFAULTS["setup_selected"]


# ============================================================================
# PERIOD AND SETUP READ FUNCTIONS
# ============================================================================

def get_period_configuration(account_id: str) -> Optional[Dict[str, Any]]:
    """Get current period configuration from canonical session state keys."""
    start_key = get_session_key("period_start", account_id)
    end_key = get_session_key("period_end", account_id)

    start_date = st.session_state.get(start_key)
    end_date = st.session_state.get(end_key)

    if not start_date or not end_date:
        return None

    return {
        'start_date': start_date,
        'end_date': end_date,
        'start_datetime': pd.to_datetime(start_date),
        'end_datetime': pd.to_datetime(end_date) + pd.Timedelta(days=1)
    }


def get_selected_setups(account_id: str) -> List[int]:
    """Get list of currently selected magic numbers from canonical session state keys."""
    selected = []
    prefix = f"setup_{account_id}_"
    for key, value in st.session_state.items():
        if key.startswith(prefix) and value:
            magic_str = key[len(prefix):].split("_")[0]
            try:
                selected.append(int(magic_str))
            except ValueError:
                continue
    return selected


def get_current_period_trades(trades_df: pd.DataFrame, account_id: str) -> pd.DataFrame:
    """Filter trades by current period and setup selection from session state."""
    if trades_df.empty:
        return trades_df

    period_config = get_period_configuration(account_id)
    if period_config:
        filtered = trades_df[
            (trades_df['OpenDatetime'] >= period_config['start_datetime']) &
            (trades_df['OpenDatetime'] <= period_config['end_datetime'])
        ]
    else:
        filtered = trades_df

    selected_setups = get_selected_setups(account_id)
    if selected_setups:
        filtered = filtered[filtered['MagicNumber'].isin(selected_setups)]

    return filtered


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_advanced_filters(account_id: str) -> Dict[str, Any]:
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
    if trades_df.empty:
        return trades_df

    filtered_df = trades_df.copy()

    if filters['trade_type'] == "Solo Backtest":
        from .data_processing import classify_trades_backtest_vs_live
        classified_df = classify_trades_backtest_vs_live(filtered_df)
        filtered_df = classified_df[classified_df['trade_type'] == 'backtest']
    elif filters['trade_type'] == "Solo Live":
        from .data_processing import classify_trades_backtest_vs_live
        classified_df = classify_trades_backtest_vs_live(filtered_df)
        filtered_df = classified_df[classified_df['trade_type'] == 'live']

    if filters['min_profit'] is not None:
        trade_profits = filtered_df.groupby('OpenPositionTicket')['PL'].sum()
        valid_tickets = trade_profits[trade_profits >= filters['min_profit']].index
        filtered_df = filtered_df[filtered_df['OpenPositionTicket'].isin(valid_tickets)]

    if filters['selected_symbols'] and 'OrderSymbol' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['OrderSymbol'].isin(filters['selected_symbols'])]

    return filtered_df


def apply_period_filters(trades_df: pd.DataFrame,
                         period_config: Optional[Dict[str, Any]]) -> pd.DataFrame:
    if not period_config or trades_df.empty:
        return trades_df

    return trades_df[
        (trades_df['OpenDatetime'] >= period_config['start_datetime']) &
        (trades_df['OpenDatetime'] <= period_config['end_datetime'])
    ]


def calculate_preset_dates(preset: str, min_date: date, max_date: date) -> Tuple[date, date]:
    end_date = max_date

    if preset in PERIOD_PRESETS:
        days = PERIOD_PRESETS[preset]["days"]
        if days is None:  # YTD
            start_date = max(min_date, datetime(end_date.year, 1, 1).date())
        else:
            start_date = max(min_date, end_date - timedelta(days=days))
    else:
        start_date = max(min_date, end_date - timedelta(days=30))

    return start_date, end_date


def get_sidebar_width(account_id: str) -> int:
    width_key = get_session_key("sidebar_width", account_id)
    width = st.session_state.get(width_key, DEFAULTS["sidebar_width"])
    return validate_sidebar_width(width)


def set_sidebar_width(account_id: str, width: int) -> bool:
    validated_width = validate_sidebar_width(width)
    width_key = get_session_key("sidebar_width", account_id)
    st.session_state[width_key] = validated_width
    return True


def toggle_all_setups(account_id: str, magic_numbers: List[int],
                      select_all: bool = True) -> int:
    modified_count = 0
    for magic_number in magic_numbers:
        setup_key = get_session_key("setup_selection", account_id, magic_number=magic_number)
        st.session_state[setup_key] = select_all
        modified_count += 1
    return modified_count


def invert_setup_selection(account_id: str, magic_numbers: List[int]) -> int:
    modified_count = 0
    for magic_number in magic_numbers:
        setup_key = get_session_key("setup_selection", account_id, magic_number=magic_number)
        current_value = st.session_state.get(setup_key, True)
        st.session_state[setup_key] = not current_value
        modified_count += 1
    return modified_count


def get_setup_search_term(account_id: str) -> str:
    search_key = get_session_key("setup_search", account_id)
    return st.session_state.get(search_key, "")


def validate_date_range(start_date: date, end_date: date) -> Tuple[bool, str]:
    if start_date > end_date:
        return False, "Data inizio deve essere <= data fine"

    if (end_date - start_date).days > 730:
        return False, "Range massimo consentito: 730 giorni"

    return True, ""


def get_filter_summary(account_id: str) -> str:
    filters = get_advanced_filters(account_id)
    period_config = get_period_configuration(account_id)
    selected_setups = get_selected_setups(account_id)

    summary_parts = []

    if period_config:
        days = (period_config['end_date'] - period_config['start_date']).days
        summary_parts.append(f"Periodo: {days} giorni")

    if selected_setups:
        summary_parts.append(f"Setup: {len(selected_setups)} selezionati")

    if filters['trade_type'] != "Tutti":
        summary_parts.append(f"Tipo: {filters['trade_type']}")

    if filters['min_profit'] is not None:
        summary_parts.append(f"Min Profit: €{filters['min_profit']}")

    if filters['max_drawdown'] is not None:
        summary_parts.append(f"Max DD: €{filters['max_drawdown']}")

    if filters['selected_symbols']:
        summary_parts.append(f"Simboli: {len(filters['selected_symbols'])}")

    return " | ".join(summary_parts) if summary_parts else "Nessun filtro attivo"


def clear_account_session_state(account_id: str) -> int:
    keys_to_remove = [k for k in st.session_state.keys() if account_id in k]
    for key in keys_to_remove:
        del st.session_state[key]
    return len(keys_to_remove)


def export_session_config(account_id: str) -> Dict[str, Any]:
    return {
        'account_id': account_id,
        'export_timestamp': datetime.now().isoformat(),
        'sidebar_width': get_sidebar_width(account_id),
        'period_config': get_period_configuration(account_id),
        'selected_setups': get_selected_setups(account_id),
        'advanced_filters': get_advanced_filters(account_id),
        'search_term': get_setup_search_term(account_id),
    }


def import_session_config(account_id: str, config: Dict[str, Any]) -> bool:
    try:
        if 'sidebar_width' in config:
            set_sidebar_width(account_id, config['sidebar_width'])

        if 'period_config' in config and config['period_config']:
            period_config = config['period_config']
            st.session_state[get_session_key("period_start", account_id)] = period_config['start_date']
            st.session_state[get_session_key("period_end", account_id)] = period_config['end_date']

        if 'selected_setups' in config:
            for key in list(st.session_state.keys()):
                if key.startswith(f"setup_{account_id}_"):
                    st.session_state[key] = False
            for magic_number in config['selected_setups']:
                st.session_state[get_session_key("setup_selection", account_id, magic_number=magic_number)] = True

        if 'advanced_filters' in config:
            filters = config['advanced_filters']
            if 'trade_type' in filters:
                st.session_state[get_session_key("trade_type_filter", account_id)] = filters['trade_type']
            if 'min_profit' in filters:
                st.session_state[get_session_key("min_profit_filter", account_id)] = filters['min_profit']
            if 'max_drawdown' in filters:
                st.session_state[get_session_key("max_dd_filter", account_id)] = filters['max_drawdown']
            if 'selected_symbols' in filters:
                st.session_state[get_session_key("symbols_filter", account_id)] = filters['selected_symbols']

        return True

    except Exception as e:
        st.error(f"Errore nell'importazione configurazione: {str(e)}")
        return False


def cleanup_large_session_objects(account_id: str, max_objects: int = 50):
    account_keys = [k for k in st.session_state.keys() if account_id in k]
    if len(account_keys) > max_objects:
        sorted_keys = sorted(account_keys)
        for key in sorted_keys[:-max_objects]:
            del st.session_state[key]


def reset_period_selection_to_default(account_id: str, trades_df: pd.DataFrame) -> bool:
    if trades_df.empty:
        return False

    data_start = trades_df['OpenDatetime'].min().date()
    data_end = trades_df['OpenDatetime'].max().date()
    default_end = min(datetime.now().date(), data_end)
    default_start = max(data_start, default_end - timedelta(days=30))

    st.session_state[get_session_key("period_start", account_id)] = default_start
    st.session_state[get_session_key("period_end", account_id)] = default_end

    return True
