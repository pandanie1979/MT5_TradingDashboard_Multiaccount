# MT5 Trading Dashboard - Performance Tab Main Entry Point
# File: tabs/performance/main.py

import streamlit as st
import pandas as pd
from typing import Dict, Any

from .sidebar.layout import render_scrollable_sidebar
from .tabs.charts_tab import render_charts_tab
from .tabs.summary_tab import render_performance_summary_tab
from .tabs.table_tab import render_performance_table_tab
from .tabs.deals_tab import render_recent_deals_tab
from .utils.session_helpers import (
    initialize_performance_state,
    get_current_period_trades,
    get_selected_setups,
    get_sidebar_width,
)
from .utils.formatting import get_error_message

try:
    from data.loader import get_trades_data
except ImportError:
    from ...data.loader import get_trades_data


def render(account_id: str, account_path: str, account_info: Dict[str, Any]):
    """
    Main render function for the performance tab.

    Args:
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict
    """
    try:
        with st.spinner("Caricamento dati..."):
            trades_df = get_trades_data(account_id, account_path)
    except Exception as e:
        st.error(f"Errore caricamento dati: {str(e)}")
        return

    if trades_df.empty:
        st.warning(get_error_message("no_data"))
        return

    # Initialize canonical session state once per account per session
    init_key = f"perf_initialized_{account_id}"
    if init_key not in st.session_state:
        initialize_performance_state(account_id, trades_df)
        st.session_state[init_key] = True

    sidebar_width = get_sidebar_width(account_id)
    main_width = 100 - sidebar_width

    sidebar_col, main_col = st.columns([sidebar_width, main_width])

    with sidebar_col:
        render_scrollable_sidebar(trades_df, account_id, account_path, account_info)

    with main_col:
        render_main_area_header(account_id, account_info)
        period_trades = get_current_period_trades(trades_df, account_id)
        render_main_tabbed_area(period_trades, account_id, account_path, account_info)


def render_main_area_header(account_id: str, account_info: Dict[str, Any]):
    """Render account header in the main area."""
    account_color = account_info.get('color', '#1f77b4')
    st.markdown(f"""
    <div style="border-left: 4px solid {account_color}; padding-left: 12px;">
        <h3 style="margin: 0; color: {account_color};">Performance Analysis</h3>
        <p style="margin: 0; color: #666; font-size: 12px;">Account: {account_id}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")


def render_main_tabbed_area(period_trades: pd.DataFrame, account_id: str,
                            account_path: str, account_info: Dict[str, Any]):
    """
    Render the four inner tabs with the already-filtered period trades.

    Args:
        period_trades: Trades filtered by current period and setup selection
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict
    """
    account_color = account_info.get('color', '#1f77b4')

    tab1, tab2, tab3, tab4 = st.tabs([
        "\U0001f4c8 Equity/Drawdown/Margin",
        "\U0001f4ca Performance Summary",
        "\U0001f4cb Setup Performance Table",
        "\U0001f50d Recent Deals"
    ])

    with tab1:
        try:
            render_charts_tab(period_trades, account_id, account_path, account_color,
                              get_selected_setups(account_id))
        except Exception as e:
            st.error(f"Errore rendering charts: {str(e)}")

    with tab2:
        try:
            render_performance_summary_tab(period_trades, account_id, account_color)
        except Exception as e:
            st.error(f"Errore rendering summary: {str(e)}")

    with tab3:
        try:
            render_performance_table_tab(period_trades, account_id)
        except Exception as e:
            st.error(f"Errore rendering table: {str(e)}")

    with tab4:
        try:
            render_recent_deals_tab(period_trades, account_id)
        except Exception as e:
            st.error(f"Errore rendering deals: {str(e)}")


# Legacy compatibility aliases
def render_performance_tab(account_id: str, account_path: str, account_info: Dict[str, Any]):
    return render(account_id, account_path, account_info)
