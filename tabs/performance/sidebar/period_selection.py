# MT5 Trading Dashboard - Period Selection Component (BUG FIXED)
# File: tabs/performance/sidebar/period_selection.py
# Fixed: September 2025 - Removed undefined function references

"""
Period selection controls for sidebar.
FIXED: Removed _render_widgets_only reference and simplified implementation.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, Any


def render_period_selection_enhanced(trades_data, account_id):
    """
    Period selection interface using PENDING state.
    FIXED: Simplified implementation without undefined functions.
    
    Args:
        trades_data: DataFrame dei trade
        account_id: ID dell'account
    
    Returns:
        Dict con configurazione periodo pending
    """
    real_account_id = str(account_id)
    
    st.write("📅 **Selezione Periodo**")
    
    # Calculate data range
    if hasattr(trades_data, 'shape') and not trades_data.empty:
        data_start = trades_data['OpenDatetime'].min().date()
        data_end = trades_data['OpenDatetime'].max().date()
        st.info(f"📊 Dati disponibili: {data_start} → {data_end}")
    else:
        data_start = datetime.now().date() - timedelta(days=365)
        data_end = datetime.now().date()
        st.warning("⚠️ Nessun dato disponibile")
    
    # PENDING state keys for widgets
    pending_start_key = f"pending_start_{real_account_id}"
    pending_end_key = f"pending_end_{real_account_id}"
    
    # Initialize pending state if not exists
    if pending_start_key not in st.session_state:
        today = datetime.now().date()
        safe_end = min(today, data_end)
        proposed_start = safe_end - timedelta(days=30)
        safe_start = max(data_start, proposed_start)
        
        if safe_start > safe_end:
            safe_start = max(data_start, safe_end - timedelta(days=7))
        
        st.session_state[pending_start_key] = safe_start
        st.session_state[pending_end_key] = safe_end
    
    # Date input widgets using PENDING keys
    col1, col2 = st.columns(2)
    
    with col1:
        safe_start_value = st.session_state[pending_start_key]
        if safe_start_value < data_start:
            safe_start_value = data_start
            st.session_state[pending_start_key] = safe_start_value
        elif safe_start_value > data_end:
            safe_start_value = data_end - timedelta(days=1)
            st.session_state[pending_start_key] = safe_start_value
            
        start_date = st.date_input(
            "Data Inizio:",
            value=safe_start_value,
            min_value=data_start,
            max_value=data_end,
            key=f"widget_start_pending_{real_account_id}",
            help="Seleziona data inizio analisi (non applicata fino a Update)"
        )
        
        # Update pending state
        st.session_state[pending_start_key] = start_date
    
    with col2:
        safe_end_value = st.session_state[pending_end_key]
        if safe_end_value < data_start:
            safe_end_value = data_start + timedelta(days=1)
            st.session_state[pending_end_key] = safe_end_value
        elif safe_end_value > data_end:
            safe_end_value = data_end
            st.session_state[pending_end_key] = safe_end_value
            
        end_date = st.date_input(
            "Data Fine:",
            value=safe_end_value,
            min_value=data_start,
            max_value=data_end,
            key=f"widget_end_pending_{real_account_id}",
            help="Seleziona data fine analisi (non applicata fino a Update)"
        )
        
        # Update pending state
        st.session_state[pending_end_key] = end_date
    
    # Show current pending period
    current_start = st.session_state[pending_start_key]
    current_end = st.session_state[pending_end_key]
    
    if current_start > current_end:
        st.error("⚠️ Data inizio deve essere ≤ data fine")
    else:
        days_diff = (current_end - current_start).days
        st.caption(f"🎯 **Periodo Selezionato** (pending): {current_start} → {current_end} ({days_diff} giorni)")
    
    # Show if different from applied state
    _render_pending_vs_applied_indicator(real_account_id)
    
    # Add preset buttons
    render_period_quick_presets(real_account_id, trades_data)
    
    return {
        'start_date': current_start,
        'end_date': current_end,
        'configured': True,
        'state': 'pending'
    }


def _render_pending_vs_applied_indicator(account_id: str):
    """Show indicator if pending state differs from applied state."""
    pending_start = st.session_state.get(f"pending_start_{account_id}")
    pending_end = st.session_state.get(f"pending_end_{account_id}")
    
    applied_start = st.session_state.get(f"applied_start_{account_id}")
    applied_end = st.session_state.get(f"applied_end_{account_id}")
    
    if (pending_start != applied_start or pending_end != applied_end):
        if applied_start and applied_end:
            st.info(f"📋 **Applicato**: {applied_start} → {applied_end}")
            st.warning("⚠️ Modifiche non applicate - clicca 'Update Metrics'")
        else:
            st.info("🆕 Nuova configurazione - clicca 'Update Metrics' per applicare")


def render_period_quick_presets(account_id: str, trades_df: pd.DataFrame):
    """
    Render quick preset buttons for common periods.
    Updates pending state only.
    
    Args:
        account_id: Account identifier
        trades_df: Complete trades DataFrame
    """
    if trades_df.empty:
        return
    
    st.markdown("**🚀 Preset Rapidi:**")
    
    data_start = trades_df['OpenDatetime'].min().date()
    data_end = trades_df['OpenDatetime'].max().date()
    today = min(datetime.now().date(), data_end)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("7D", key=f"preset_7d_{account_id}", use_container_width=True):
            _apply_preset_to_pending(account_id, today, data_start, 7)
    
    with col2:
        if st.button("30D", key=f"preset_30d_{account_id}", use_container_width=True):
            _apply_preset_to_pending(account_id, today, data_start, 30)
    
    with col3:
        if st.button("90D", key=f"preset_90d_{account_id}", use_container_width=True):
            _apply_preset_to_pending(account_id, today, data_start, 90)
    
    with col4:
        if st.button("YTD", key=f"preset_ytd_{account_id}", use_container_width=True):
            year_start = datetime(today.year, 1, 1).date()
            ytd_start = max(data_start, year_start)
            _apply_preset_to_pending(account_id, today, ytd_start, None)


def _apply_preset_to_pending(account_id: str, end_date: date, data_start: date, days: int):
    """Apply preset to pending state only."""
    if days is None:  # YTD case
        preset_start = data_start
    else:
        preset_start = max(data_start, end_date - timedelta(days=days))
    
    st.session_state[f"pending_start_{account_id}"] = preset_start
    st.session_state[f"pending_end_{account_id}"] = end_date
    
    st.success(f"✅ Preset applicato al pending state!")


def get_period_info_for_display(account_id: str) -> Dict[str, Any]:
    """Get period information formatted for display (uses pending state)."""
    pending_start_key = f"pending_start_{account_id}"
    pending_end_key = f"pending_end_{account_id}"
    
    start_date = st.session_state.get(pending_start_key)
    end_date = st.session_state.get(pending_end_key)
    
    if not start_date or not end_date:
        return {
            'configured': False,
            'message': 'Periodo non configurato'
        }
    
    days_span = (end_date - start_date).days
    
    return {
        'configured': True,
        'start_date': start_date,
        'end_date': end_date,
        'days_span': days_span,
        'formatted_range': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
        'state': 'pending'
    }


def reset_period_to_default(account_id: str, trades_df: pd.DataFrame) -> bool:
    """Reset PENDING period selection to default (30 days)."""
    if trades_df.empty:
        return False
    
    data_start = trades_df['OpenDatetime'].min().date()
    data_end = trades_df['OpenDatetime'].max().date()
    
    default_end = min(datetime.now().date(), data_end)
    default_start = max(data_start, default_end - timedelta(days=30))
    
    # Reset pending state (applied state unchanged until Update button)
    st.session_state[f"pending_start_{account_id}"] = default_start
    st.session_state[f"pending_end_{account_id}"] = default_end
    
    return True


def get_pending_period_summary(account_id: str) -> str:
    """Get summary of pending period configuration."""
    pending_start = st.session_state.get(f"pending_start_{account_id}")
    pending_end = st.session_state.get(f"pending_end_{account_id}")
    
    applied_start = st.session_state.get(f"applied_start_{account_id}")
    applied_end = st.session_state.get(f"applied_end_{account_id}")
    
    if not pending_start or not pending_end:
        return "Periodo non configurato"
    
    days_span = (pending_end - pending_start).days
    summary = f"Pending: {days_span} giorni"
    
    if pending_start != applied_start or pending_end != applied_end:
        summary += " (⚠️ Non applicato)"
    else:
        summary += " (✅ Applicato)"
    
    return summary