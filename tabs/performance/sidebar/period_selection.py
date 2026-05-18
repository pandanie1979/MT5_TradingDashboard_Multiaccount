# MT5 Trading Dashboard - Period Selection Component
# File: tabs/performance/sidebar/period_selection.py

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, Any

from ..config.constants import get_session_key


def render_period_selection_enhanced(trades_data, account_id):
    """
    Period selection interface. Sidebar changes apply immediately to charts.

    Render order: preset buttons → date inputs. This ensures that when a preset
    button is clicked, it sets the canonical session state keys BEFORE the
    date_input widgets render, which is required by Streamlit's widget ownership rules.

    Args:
        trades_data: DataFrame dei trade
        account_id: ID dell'account

    Returns:
        Dict con configurazione periodo corrente
    """
    real_account_id = str(account_id)
    start_key = get_session_key("period_start", real_account_id)
    end_key = get_session_key("period_end", real_account_id)

    st.write("\U0001f4c5 **Selezione Periodo**")

    if hasattr(trades_data, 'shape') and not trades_data.empty:
        data_start = trades_data['OpenDatetime'].min().date()
        data_end = trades_data['OpenDatetime'].max().date()
        st.info(f"\U0001f4ca Dati disponibili: {data_start} → {data_end}")
    else:
        data_start = datetime.now().date() - timedelta(days=365)
        data_end = datetime.now().date()
        st.warning("⚠ Nessun dato disponibile")

    # Guard: initialize if not yet set (normally done in render() before this runs)
    if start_key not in st.session_state:
        safe_end = min(datetime.now().date(), data_end)
        safe_start = max(data_start, safe_end - timedelta(days=30))
        st.session_state[start_key] = safe_start
        st.session_state[end_key] = safe_end

    # PRESET BUTTONS FIRST: clicking a preset sets the canonical keys before
    # the date_input widgets render below, so Streamlit accepts the state update.
    render_period_quick_presets(real_account_id, trades_data)

    # Clamp stored values to valid data range (after any preset update)
    _clamp_date_key(start_key, data_start, data_end - timedelta(days=1))
    _clamp_date_key(end_key, data_start, data_end)

    # DATE INPUTS: use canonical keys directly as widget keys.
    # Streamlit reads and writes the session state key automatically.
    col1, col2 = st.columns(2)

    with col1:
        st.date_input(
            "Data Inizio:",
            min_value=data_start,
            max_value=data_end,
            key=start_key,
        )

    with col2:
        st.date_input(
            "Data Fine:",
            min_value=data_start,
            max_value=data_end,
            key=end_key,
        )

    current_start = st.session_state[start_key]
    current_end = st.session_state[end_key]

    if current_start > current_end:
        st.error("⚠ Data inizio deve essere <= data fine")
    else:
        days_diff = (current_end - current_start).days
        st.caption(f"\U0001f3af Periodo: {current_start} → {current_end} ({days_diff} giorni)")

    return {
        'start_date': current_start,
        'end_date': current_end,
        'configured': True,
    }


def _clamp_date_key(key: str, min_val: date, max_val: date):
    """Clamp the date stored in session_state[key] to [min_val, max_val]."""
    val = st.session_state.get(key)
    if val is None:
        return
    if val < min_val:
        st.session_state[key] = min_val
    elif val > max_val:
        st.session_state[key] = max_val


def render_period_quick_presets(account_id: str, trades_df: pd.DataFrame):
    """
    Render quick preset buttons. Each preset sets the canonical period keys.
    Must be called BEFORE the date_input widgets to satisfy Streamlit widget
    ownership rules (state set before widget renders = allowed).
    """
    if trades_df.empty:
        return

    st.markdown("**\U0001f680 Preset Rapidi:**")

    data_start = trades_df['OpenDatetime'].min().date()
    data_end = trades_df['OpenDatetime'].max().date()
    today = min(datetime.now().date(), data_end)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("7D", key=f"preset_7d_{account_id}", use_container_width=True):
            _apply_preset(account_id, today, data_start, 7)

    with col2:
        if st.button("30D", key=f"preset_30d_{account_id}", use_container_width=True):
            _apply_preset(account_id, today, data_start, 30)

    with col3:
        if st.button("90D", key=f"preset_90d_{account_id}", use_container_width=True):
            _apply_preset(account_id, today, data_start, 90)

    with col4:
        if st.button("YTD", key=f"preset_ytd_{account_id}", use_container_width=True):
            year_start = datetime(today.year, 1, 1).date()
            _apply_preset(account_id, today, max(data_start, year_start), None)


def _apply_preset(account_id: str, end_date: date, data_start: date, days):
    """
    Write preset dates to canonical session state keys.
    Safe to call before date_input widgets render in the same run.
    """
    if days is None:
        preset_start = data_start
    else:
        preset_start = max(data_start, end_date - timedelta(days=days))

    st.session_state[get_session_key("period_start", account_id)] = preset_start
    st.session_state[get_session_key("period_end", account_id)] = end_date


def get_period_info_for_display(account_id: str) -> Dict[str, Any]:
    """Get period information formatted for display."""
    start_date = st.session_state.get(get_session_key("period_start", account_id))
    end_date = st.session_state.get(get_session_key("period_end", account_id))

    if not start_date or not end_date:
        return {'configured': False, 'message': 'Periodo non configurato'}

    days_span = (end_date - start_date).days
    return {
        'configured': True,
        'start_date': start_date,
        'end_date': end_date,
        'days_span': days_span,
        'formatted_range': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
    }


def reset_period_to_default(account_id: str, trades_df: pd.DataFrame) -> bool:
    """Reset period selection to default (last 30 days)."""
    if trades_df.empty:
        return False

    data_start = trades_df['OpenDatetime'].min().date()
    data_end = trades_df['OpenDatetime'].max().date()
    default_end = min(datetime.now().date(), data_end)
    default_start = max(data_start, default_end - timedelta(days=30))

    st.session_state[get_session_key("period_start", account_id)] = default_start
    st.session_state[get_session_key("period_end", account_id)] = default_end

    return True
