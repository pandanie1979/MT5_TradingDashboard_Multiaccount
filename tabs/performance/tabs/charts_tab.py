# MT5 Trading Dashboard - Charts Tab Component
# File: tabs/performance/tabs/charts_tab.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Charts tab component for main area.
Handles Equity/Drawdown/Margin visualization with enhanced overlays.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any

from ..utils.data_processing import (
    classify_trades_backtest_vs_live,
    create_continuous_equity_curve,
    calculate_margin_timeline
)
from ..utils.chart_helpers import (
    create_multi_panel_chart,
    generate_period_info_enhanced
)
from ..utils.formatting import get_error_message

try:
    from data.loader import get_trades_data
except ImportError:
    from ....data.loader import get_trades_data

def render_charts_tab(period_trades: pd.DataFrame, account_id: str, 
                     account_path: str, account_color: str, selected_setups: List[int]):
    """
    Render Tab 1: Equity/Drawdown/Margin charts with enhanced visualization.
    
    Args:
        period_trades: Filtered trades for current period and setups
        account_id: Account identifier
        account_path: Path to MT5 data
        account_color: Account color for styling
        selected_setups: List of selected magic numbers
    """
    st.markdown(f"### ?? Analisi Grafici - Account {account_id}")
    
    if period_trades.empty:
        st.info(get_error_message("no_data"))
        return
    
    # Determine if multi-setup analysis
    multi_mn_selected = len(selected_setups) > 1
    
    # Load complete dataset for consistent classification
    all_trades = get_trades_data(account_id, account_path)
    all_trades_classified = classify_trades_backtest_vs_live(all_trades)
    
    # Create classification mapping for period trades
    ticket_classification = dict(zip(
        all_trades_classified['OpenPositionTicket'], 
        all_trades_classified['trade_type']
    ))
    
    # Apply classification to period trades
    equity_data = period_trades.copy()
    equity_data['trade_type'] = equity_data['OpenPositionTicket'].map(
        ticket_classification
    ).fillna('live')
    
    # Prepare data for plotting
    equity_data = _prepare_plot_data(equity_data, multi_mn_selected)
    
    # Calculate margin timeline
    margin_timeline = calculate_margin_timeline(period_trades)
    
    # Create and display multi-panel chart
    _render_multi_panel_chart(equity_data, margin_timeline, account_id, 
                             account_color, multi_mn_selected)
    
    # Show classification information
    _render_classification_info(equity_data, multi_mn_selected)
    
    # Show enhanced period analysis
    _render_period_analysis(equity_data)


def _prepare_plot_data(equity_data: pd.DataFrame, multi_mn: bool) -> pd.DataFrame:
    """
    Prepare equity data for plotting with proper date handling.
    
    Args:
        equity_data: Trades DataFrame with trade_type
        multi_mn: Whether multi-setup analysis
        
    Returns:
        DataFrame prepared for plotting
    """
    # Use CloseDatetime if available, otherwise OpenDatetime
    if 'CloseDatetime' in equity_data.columns:
        equity_data = equity_data.sort_values('CloseDatetime')
        equity_data['PlotDate'] = equity_data['CloseDatetime']
    else:
        equity_data = equity_data.sort_values('OpenDatetime') 
        equity_data['PlotDate'] = equity_data['OpenDatetime']
    
    # Create continuous equity curve
    equity_data = create_continuous_equity_curve(
        equity_data, 'PlotDate', multi_mn=multi_mn
    )
    
    return equity_data


def _render_multi_panel_chart(equity_data: pd.DataFrame, margin_timeline: pd.DataFrame,
                             account_id: str, account_color: str, multi_mn: bool):
    """
    Render the main multi-panel chart.
    
    Args:
        equity_data: Prepared equity data
        margin_timeline: Margin timeline data
        account_id: Account identifier
        account_color: Account color
        multi_mn: Multi-setup flag
    """
    try:
        # Create chart using helper function
        fig = create_multi_panel_chart(
            equity_data, margin_timeline, account_id, account_color, multi_mn
        )
        
        # Display chart
        st.plotly_chart(fig, width="stretch")
        
    except Exception as e:
        st.error(f"Errore nella creazione del grafico: {str(e)}")
        st.info("Verifica la qualità dei dati e riprova.")


def _render_classification_info(equity_data: pd.DataFrame, multi_mn: bool):
    """
    Render classification information below charts.
    
    Args:
        equity_data: Equity data with trade_type
        multi_mn: Multi-setup flag
    """
    if 'trade_type' not in equity_data.columns:
        return
    
    # Count trades by type
    backtest_count = len(equity_data[equity_data['trade_type'] == 'backtest'])
    live_count = len(equity_data[equity_data['trade_type'] == 'live'])
    
    # Analyze ticket ranges for debugging
    bt_tickets = equity_data[equity_data['trade_type'] == 'backtest']['OpenPositionTicket'].unique()
    live_tickets = equity_data[equity_data['trade_type'] == 'live']['OpenPositionTicket'].unique()
    
    bt_range = f"{min(bt_tickets)}-{max(bt_tickets)}" if len(bt_tickets) > 0 else "N/A"
    live_range = f"{min(live_tickets)}-{max(live_tickets)}" if len(live_tickets) > 0 else "N/A"
    
    # Display info based on setup type
    if multi_mn:
        st.info(
            f"?? **Analisi Multi-Setup con Overlay Colori**: "
            f"{backtest_count} deals backtest (tickets: {bt_range}) + "
            f"{live_count} deals live (tickets: {live_range}). "
            f"Sfondo colorato per composizione settimanale (grigio = backtest, blu = live, gradiente = mix)"
        )
    else:
        st.info(
            f"?? **Analisi Singolo Setup con Overlay**: "
            f"{backtest_count} deals backtest (tickets: {bt_range}) + "
            f"{live_count} deals live (tickets: {live_range}). "
            f"Sfondo grigio = backtest, sfondo blu = live"
        )


def _render_period_analysis(equity_data: pd.DataFrame):
    """
    Render enhanced period analysis in expandable section.
    
    Args:
        equity_data: Equity data with trade_type and period info
    """
    with st.expander("?? Analisi Dettagliata Periodo", expanded=False):
        if 'trade_type' in equity_data.columns:
            # Generate enhanced period information
            period_info = generate_period_info_enhanced(equity_data, 'PlotDate')
            st.markdown(period_info)
        else:
            st.info("Analisi periodo non disponibile (classificazione mancante)")


def render_chart_controls(account_id: str):
    """
    Render additional chart controls and options.
    
    Args:
        account_id: Account identifier
    """
    st.markdown("### ?? Opzioni Grafico")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Enhanced colors toggle
        enhanced_colors = st.checkbox(
            "Colori Enfatizzati",
            value=st.session_state.get(f"chart_colors_enhanced_{account_id}", True),
            key=f"chart_colors_enhanced_{account_id}",
            help="Usa colori più intensi per overlay backtest/live"
        )
    
    with col2:
        # Show period analysis toggle
        show_period_analysis = st.checkbox(
            "Mostra Analisi Periodo",
            value=st.session_state.get(f"show_period_analysis_{account_id}", False),
            key=f"show_period_analysis_{account_id}",
            help="Mostra informazioni dettagliate sui periodi"
        )
    
    return {
        'enhanced_colors': enhanced_colors,
        'show_period_analysis': show_period_analysis
    }


def export_chart_data(equity_data: pd.DataFrame, margin_timeline: pd.DataFrame,
                     account_id: str) -> Dict[str, Any]:
    """
    Export chart data for external analysis.
    
    Args:
        equity_data: Equity curve data
        margin_timeline: Margin timeline data
        account_id: Account identifier
        
    Returns:
        Dict with exportable chart data
    """
    export_data = {
        'account_id': account_id,
        'export_timestamp': pd.Timestamp.now().isoformat(),
        'equity_data': equity_data.to_dict('records') if not equity_data.empty else [],
        'margin_timeline': margin_timeline.to_dict('records') if not margin_timeline.empty else [],
        'summary': {
            'total_deals': len(equity_data),
            'date_range': {
                'start': equity_data['PlotDate'].min().isoformat() if not equity_data.empty else None,
                'end': equity_data['PlotDate'].max().isoformat() if not equity_data.empty else None
            },
            'final_equity': equity_data['Cumulative_PL'].iloc[-1] if not equity_data.empty else 0,
            'final_margin': margin_timeline['total_margin'].iloc[-1] if not margin_timeline.empty else 0
        }
    }
    
    # Add classification summary if available
    if 'trade_type' in equity_data.columns:
        export_data['classification'] = {
            'backtest_deals': len(equity_data[equity_data['trade_type'] == 'backtest']),
            'live_deals': len(equity_data[equity_data['trade_type'] == 'live']),
            'classification_method': 'dual_criteria_ticket_and_filename'
        }
    
    return export_data
