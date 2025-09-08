# MT5 Trading Dashboard - Period Selection Component (SIMPLIFIED)
# File: tabs/performance/sidebar/period_selection.py
# Modified: September 2025 - Removed preset buttons, manual date selection only

"""
Period selection controls for sidebar.
SIMPLIFIED: Only manual date range selection, no preset buttons.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from typing import Dict, Any, Tuple

from ..utils.session_helpers import (
    get_period_configuration,
    calculate_preset_dates,
    validate_date_range
)
from ..config.constants import get_session_key
from ..utils.formatting import get_error_message, get_success_message


def render_period_selection_enhanced(trades_df: pd.DataFrame, account_id: str):
    """
    Render SIMPLIFIED period selection - ONLY manual date inputs.
    Removed preset buttons as requested.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    if trades_df.empty:
        st.warning("Nessun dato disponibile per selezione periodo")
        return
    
    # Get date range from data
    min_date = trades_df['OpenDatetime'].min().date()
    max_date = trades_df['OpenDatetime'].max().date()
    
    # REMOVED: render_preset_buttons() - non più necessari
    
    st.markdown("**Selezione Periodo:**")
    
    # Render ONLY custom date inputs
    render_custom_date_inputs(account_id, min_date, max_date)
    
    # Show period validation
    render_period_validation(account_id)


def render_custom_date_inputs(account_id: str, min_date: date, max_date: date):
    """
    Render ONLY custom date input controls - FIXED with user modification tracking.
    Now properly tracks when user modifies dates to prevent resets.
    """
    # IMPORTANTE: Inizializza SEMPRE le chiavi prima di usarle nei widget
    start_key = f"date_start_{account_id}"
    end_key = f"date_end_{account_id}"
    
    # Inizializza se non esistono
    if start_key not in st.session_state or end_key not in st.session_state:
        default_start, default_end = calculate_preset_dates("30d", min_date, max_date)
        st.session_state[start_key] = default_start
        st.session_state[end_key] = default_end
    
    # Store original values to detect changes
    original_start = st.session_state[start_key]
    original_end = st.session_state[end_key]
    
    # Render widgets
    start_date = st.date_input(
        "Data Inizio",
        min_value=min_date,
        max_value=max_date,
        key=start_key,
        help="Seleziona data inizio periodo analisi"
    )
    
    end_date = st.date_input(
        "Data Fine", 
        min_value=min_date,
        max_value=max_date,
        key=end_key,
        help="Seleziona data fine periodo analisi"
    )
    
    # NUOVO: Detect if user changed dates and mark as user-modified
    if (start_date != original_start or end_date != original_end):
        from ..utils.session_helpers import mark_period_as_user_modified
        mark_period_as_user_modified(account_id)


def render_period_validation(account_id: str):
    """
    Render period validation feedback.
    
    Args:
        account_id: Account identifier
    """
    period_config = get_period_configuration(account_id)
    
    if not period_config:
        st.info("Seleziona un periodo per l'analisi")
        return
    
    start_date = period_config['start_date']
    end_date = period_config['end_date']
    
    # Validate date range
    is_valid, error_message = validate_date_range(start_date, end_date)
    
    if not is_valid:
        st.error(f"❌ {error_message}")
    else:
        days_span = (end_date - start_date).days
        st.success(f"✅ Periodo: {days_span} giorni")
        
        # Show additional period info
        render_period_summary(start_date, end_date, days_span)


def render_period_summary(start_date: date, end_date: date, days_span: int):
    """
    Render period summary information.
    
    Args:
        start_date: Start date
        end_date: End date
        days_span: Number of days in period
    """
    # Determine period type
    if days_span <= 7:
        period_type = "📅 Settimana"
    elif days_span <= 31:
        period_type = "📆 Mese"
    elif days_span <= 93:
        period_type = "🗓️ Trimestre"
    elif days_span <= 366:
        period_type = "📋 Anno"
    else:
        period_type = "📊 Multi-Anno"
    
    st.caption(f"{period_type} | {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")


def get_period_info_for_display(account_id: str) -> Dict[str, Any]:
    """
    Get period information formatted for display.
    
    Args:
        account_id: Account identifier
        
    Returns:
        Dict with period display information
    """
    period_config = get_period_configuration(account_id)
    
    if not period_config:
        return {
            'configured': False,
            'message': 'Periodo non configurato'
        }
    
    start_date = period_config['start_date']
    end_date = period_config['end_date']
    days_span = (end_date - start_date).days
    
    return {
        'configured': True,
        'start_date': start_date,
        'end_date': end_date,
        'days_span': days_span,
        'formatted_range': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
        'period_type': _get_period_type(days_span)
    }


def _get_period_type(days_span: int) -> str:
    """
    Get period type based on number of days.
    
    Args:
        days_span: Number of days in period
        
    Returns:
        Period type string
    """
    if days_span <= 7:
        return "week"
    elif days_span <= 31:
        return "month"
    elif days_span <= 93:
        return "quarter"
    elif days_span <= 366:
        return "year"
    else:
        return "multi_year"


def reset_period_to_default(account_id: str, trades_df: pd.DataFrame) -> bool:
    """
    Reset period selection to default (30 days).
    
    Args:
        account_id: Account identifier
        trades_df: Trades DataFrame for date range
        
    Returns:
        True if reset was successful
    """
    if trades_df.empty:
        return False
    
    min_date = trades_df['OpenDatetime'].min().date()
    max_date = trades_df['OpenDatetime'].max().date()
    
    # Calcola default e aggiorna widget
    default_start, default_end = calculate_preset_dates("30d", min_date, max_date)
    st.session_state[f"date_start_{account_id}"] = default_start
    st.session_state[f"date_end_{account_id}"] = default_end
    
    return True


# REMOVED FUNCTIONS (no longer needed):
# - render_preset_buttons() 
# - All preset button logic and PERIOD_PRESETS dependencies