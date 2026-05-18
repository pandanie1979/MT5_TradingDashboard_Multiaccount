# MT5 Trading Dashboard - Setup Selection Component
# File: tabs/performance/sidebar/setup_selection.py

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

from ..utils.formatting import format_profit_indicator
from ..config.constants import get_session_key


def render_setup_selection_clean(trades_df: pd.DataFrame, account_id: str):
    """
    Setup selection. Checkboxes write to canonical session state keys;
    charts re-render immediately on the next Streamlit rerun.

    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    if trades_df.empty:
        st.warning("Nessun trade disponibile")
        return

    period_filtered_trades = _get_period_filtered_trades(trades_df, account_id)

    setup_list = _calculate_setup_list(trades_df, period_filtered_trades, account_id)

    if not setup_list:
        st.info("Nessun setup disponibile nei trade caricati")
        return

    filtered_setups = _render_search_controls(setup_list, account_id)
    _render_bulk_actions(filtered_setups, account_id)
    _render_setup_checkboxes(filtered_setups, account_id)
    _render_selection_summary(filtered_setups, account_id)


def _get_period_filtered_trades(trades_df: pd.DataFrame, account_id: str) -> pd.DataFrame:
    """Filter trades by current period configuration."""
    from ..utils.session_helpers import get_period_configuration

    period_config = get_period_configuration(account_id)

    if not period_config:
        if not trades_df.empty:
            max_date = trades_df['OpenDatetime'].max()
            start_date = max_date - pd.Timedelta(days=30)
            return trades_df[trades_df['OpenDatetime'] >= start_date]
        return trades_df

    return trades_df[
        (trades_df['OpenDatetime'] >= period_config['start_datetime']) &
        (trades_df['OpenDatetime'] <= period_config['end_datetime'])
    ]


def _calculate_setup_list(complete_trades_df: pd.DataFrame,
                          period_trades_df: pd.DataFrame,
                          account_id: str) -> List[Dict[str, Any]]:
    """Calculate setup list with period-specific profit figures."""
    if complete_trades_df.empty:
        return []

    setup_list = []

    try:
        for magic_number in complete_trades_df['MagicNumber'].unique():
            complete_setup_trades = complete_trades_df[complete_trades_df['MagicNumber'] == magic_number]
            if complete_setup_trades.empty:
                continue

            first_trade = complete_setup_trades.iloc[0]
            setup_name = first_trade.get('StrategyName',
                         first_trade.get('StrategyFromFile', f'Strategy_{magic_number}'))
            symbol = first_trade.get('OrderSymbol',
                     first_trade.get('Symbol', 'Unknown'))

            period_setup_trades = period_trades_df[period_trades_df['MagicNumber'] == magic_number]

            if period_setup_trades.empty:
                setup_profit = 0.0
                setup_trades_count = 0
            else:
                try:
                    unique_trades = period_setup_trades.groupby('OpenPositionTicket')['PL'].sum()
                    setup_profit = unique_trades.sum()
                    setup_trades_count = len(unique_trades)
                except Exception:
                    setup_profit = period_setup_trades['PL'].sum()
                    setup_trades_count = period_setup_trades['OpenPositionTicket'].nunique()

            period_info = _get_period_display_info(account_id)

            setup_list.append({
                'Magic_Number': magic_number,
                'Setup_Name': setup_name,
                'Symbol': symbol,
                'Profit': setup_profit,
                'Trades_Count': setup_trades_count,
                'Display_Name': f"MN{magic_number} - {setup_name} ({symbol})",
                'Performance': f"€{setup_profit:.0f} ({setup_trades_count}T)",
                'Period_Info': period_info,
                'Has_Period_Data': setup_trades_count > 0
            })

    except Exception as e:
        st.error(f"Errore nel calcolo setup: {str(e)}")
        return []

    setup_list.sort(key=lambda x: x['Profit'], reverse=True)
    return setup_list


def _get_period_display_info(account_id: str) -> str:
    """Get period information for display context."""
    from ..utils.session_helpers import get_period_configuration

    period_config = get_period_configuration(account_id)

    if not period_config:
        return "Ultimo mese"

    start_date = period_config['start_date']
    end_date = period_config['end_date']
    days_span = (end_date - start_date).days

    return f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')} ({days_span}g)"


def _render_search_controls(setup_list: List[Dict[str, Any]], account_id: str) -> List[Dict[str, Any]]:
    search_term = st.text_input(
        "\U0001f50d Cerca Setup:",
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
    """Bulk selection buttons — write directly to canonical keys for immediate apply."""
    if not filtered_setups:
        return

    st.markdown("**Azioni Bulk:**")
    col1, col2, col3 = st.columns(3)
    magic_numbers = [s['Magic_Number'] for s in filtered_setups]

    with col1:
        if st.button("Tutti", key=f"select_all_{account_id}", use_container_width=True):
            from ..utils.session_helpers import toggle_all_setups
            toggle_all_setups(account_id, magic_numbers, select_all=True)

    with col2:
        if st.button("Nessuno", key=f"select_none_{account_id}", use_container_width=True):
            from ..utils.session_helpers import toggle_all_setups
            toggle_all_setups(account_id, magic_numbers, select_all=False)

    with col3:
        if st.button("Inverti", key=f"invert_{account_id}", use_container_width=True):
            from ..utils.session_helpers import invert_setup_selection
            invert_setup_selection(account_id, magic_numbers)


def _render_setup_checkboxes(filtered_setups: List[Dict[str, Any]], account_id: str):
    """
    Render setup checkboxes using canonical session state keys as widget keys.
    Streamlit writes the checkbox value directly to the canonical key,
    so charts see the update on the next rerun without any extra step.
    """
    if not filtered_setups:
        st.info("Nessun setup trovato con i criteri di ricerca")
        return

    st.markdown("**Setup Disponibili:**")

    period_info = _get_period_display_info(account_id)
    st.caption(f"\U0001f4a1 **Profitti mostrati per periodo**: {period_info}")

    for setup in filtered_setups:
        canonical_key = get_session_key("setup_selection", account_id, magic_number=setup['Magic_Number'])

        # Ensure key exists before Streamlit renders the widget
        if canonical_key not in st.session_state:
            st.session_state[canonical_key] = True

        col1, col2 = st.columns([3, 1])

        with col1:
            st.checkbox(
                setup['Display_Name'],
                key=canonical_key,
                help=f"Periodo: {setup['Period_Info']}"
            )

        with col2:
            if setup['Has_Period_Data']:
                profit_color = "\U0001f7e2" if setup['Profit'] >= 0 else "\U0001f534"
                st.caption(f"{profit_color} {setup['Performance']}")
            else:
                st.caption("⊘ €0 (0T)")


def _render_selection_summary(filtered_setups: List[Dict[str, Any]], account_id: str):
    if not filtered_setups:
        return

    selected_count = 0
    total_profit = 0.0

    for setup in filtered_setups:
        canonical_key = get_session_key("setup_selection", account_id, magic_number=setup['Magic_Number'])
        if st.session_state.get(canonical_key, True):
            selected_count += 1
            total_profit += setup['Profit']

    period_info = _get_period_display_info(account_id)

    if selected_count > 0:
        st.info(f"\U0001f4cb {selected_count}/{len(filtered_setups)} setup selezionati")
        st.caption(f"\U0001f4c5 **Periodo**: {period_info}")
        if total_profit != 0:
            profit_color = "\U0001f7e2" if total_profit >= 0 else "\U0001f534"
            st.markdown(f"**Performance Periodo:** {profit_color} €{total_profit:.0f}")
    else:
        st.warning("⚠ Nessun setup selezionato")


# Legacy compatibility
def get_setup_selection_summary(account_id: str, trades_df: pd.DataFrame) -> Dict[str, Any]:
    """Legacy function — returns basic summary from canonical state."""
    from ..utils.session_helpers import get_selected_setups, get_period_configuration

    selected = get_selected_setups(account_id)
    total = trades_df['MagicNumber'].nunique() if not trades_df.empty else 0

    return {
        'total_setups': total,
        'selected_count': len(selected),
        'has_changes': False,
        'period_info': _get_period_display_info(account_id)
    }
