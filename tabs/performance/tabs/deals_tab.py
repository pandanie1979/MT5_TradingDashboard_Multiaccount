# MT5 Trading Dashboard - Recent Deals Tab Component
# File: tabs/performance/tabs/deals_tab.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Recent deals tab component.
Shows latest trading activity with statistics and controls.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List

from ..utils.formatting import get_error_message
from ..config.constants import TABLE_CONFIG, get_session_key


def render_recent_deals_tab(period_trades: pd.DataFrame, account_id: str):
    """
    Render Tab 4: Recent Deals with statistics and controls.
    
    Args:
        period_trades: Filtered trades for current period and setups
        account_id: Account identifier
    """
    st.markdown(f"### 🔍 Recent Deals - Account {account_id}")
    
    if period_trades.empty:
        st.info(get_error_message("no_data"))
        return
    
    # Render deals table
    _render_deals_table(period_trades, account_id)
    
    # Render deals statistics
    _render_deals_statistics(period_trades, account_id)
    
    # Render controls
    _render_deals_controls(period_trades, account_id)


def _render_deals_table(period_trades: pd.DataFrame, account_id: str):
    """
    Render the main deals table with proper formatting.
    
    Args:
        period_trades: Filtered trades DataFrame
        account_id: Account identifier
    """
    # Check if extended view is requested
    show_extended = st.session_state.get(f'show_more_deals_{account_id}', False)
    
    # Determine number of deals to show
    limit = TABLE_CONFIG["deals_table"]["extended_limit"] if show_extended else TABLE_CONFIG["deals_table"]["default_limit"]
    
    # Sort and limit deals
    recent_deals = period_trades.sort_values('OpenDatetime', ascending=False).head(limit)
    
    # Show info about displayed deals
    unique_in_recent = recent_deals['OpenPositionTicket'].nunique()
    st.info(f"📊 Ultimi {len(recent_deals)} deals da {unique_in_recent} trades unici")
    
    # Prepare display data
    display_deals = _prepare_deals_display_data(recent_deals)
    
    # Configure columns
    column_config = _get_deals_column_configuration()
    
    # Display table
    st.dataframe(
        display_deals,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        height=TABLE_CONFIG["deals_table"]["height"]
    )


def _prepare_deals_display_data(recent_deals: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare deals data for display with proper column selection and naming.
    """
    # Define column mapping with priority order - FIXED: no duplicates
    column_mapping = {
        'OpenDatetime': 'Data Apertura',
        'CloseDatetime': 'Data Chiusura', 
        'OpenPositionTicket': 'Ticket',
        'OrderSymbol': 'Symbol',
        'MagicNumber': 'Magic',
        'PL': 'P&L (€)',
        'StrategyName': 'Strategia',
        'ExitReason': 'Exit Reason',
        'OrderType': 'Tipo',
        'OpenPositionSize': 'Volume',
        'OpenPrice': 'Prezzo Open',
        'ClosePrice': 'Prezzo Close'
    }
    
    # Select available columns in priority order - FIXED: avoid duplicates
    available_columns = []
    display_names = []
    
    for original_col, display_name in column_mapping.items():
        if original_col in recent_deals.columns:
            available_columns.append(original_col)
            display_names.append(display_name)
    
    # Fallbacks for missing columns - FIXED: check if already added
    if 'OrderSymbol' not in available_columns and 'Symbol' in recent_deals.columns:
        available_columns.append('Symbol')
        display_names.append('Symbol')
    
    if 'StrategyName' not in available_columns and 'StrategyFromFile' in recent_deals.columns:
        available_columns.append('StrategyFromFile')
        display_names.append('Strategia')
    
    # Create display DataFrame
    if available_columns:
        display_deals = recent_deals[available_columns].copy()
        display_deals.columns = display_names
        return display_deals
    else:
        return pd.DataFrame()


def _get_deals_column_configuration() -> Dict[str, Any]:
    """
    Get column configuration for deals table.
    
    Returns:
        Dict with Streamlit column configuration
    """
    return {
        "P&L (€)": st.column_config.NumberColumn(
            format="%.2f €",
            help="Profit/Loss del deal"
        ),
        "Data Apertura": st.column_config.DatetimeColumn(
            format="DD/MM/YYYY HH:mm",
            help="Data e ora apertura posizione"
        ),
        "Data Chiusura": st.column_config.DatetimeColumn(
            format="DD/MM/YYYY HH:mm",
            help="Data e ora chiusura posizione"
        ),
        "Volume": st.column_config.NumberColumn(
            format="%.2f",
            help="Volume in lotti"
        ),
        "Prezzo Open": st.column_config.NumberColumn(
            format="%.5f",
            help="Prezzo di apertura"
        ),
        "Prezzo Close": st.column_config.NumberColumn(
            format="%.5f", 
            help="Prezzo di chiusura"
        )
    }


def _render_deals_statistics(period_trades: pd.DataFrame, account_id: str):
    """
    Render deals statistics section.
    
    Args:
        period_trades: Filtered trades DataFrame
        account_id: Account identifier
    """
    st.markdown("---")
    st.markdown("#### 📈 Statistiche Deals")
    
    # Calculate statistics
    stats = _calculate_deals_statistics(period_trades)
    
    # Display in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Deals", stats['total_deals'])
    
    with col2:
        profit_delta = f"{stats['profit_percentage']:.1f}%"
        st.metric("Deals Profittevoli", stats['profitable_deals'], delta=profit_delta)
    
    with col3:
        st.metric("P&L Totale", f"€{stats['total_pl']:.2f}")
    
    with col4:
        st.metric("P&L Medio", f"€{stats['avg_pl']:.2f}")
    
    # Additional statistics
    if stats['symbols_count'] > 1:
        st.markdown("**📊 Distribuzione per Symbol:**")
        symbol_stats = _calculate_symbol_distribution(period_trades)
        
        for symbol, count in symbol_stats.items():
            percentage = (count / stats['total_deals'] * 100)
            st.write(f"- {symbol}: {count} deals ({percentage:.1f}%)")


def _calculate_deals_statistics(period_trades: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate comprehensive deals statistics.
    
    Args:
        period_trades: Filtered trades DataFrame
        
    Returns:
        Dict with calculated statistics
    """
    total_deals = len(period_trades)
    
    if total_deals == 0:
        return {
            'total_deals': 0,
            'profitable_deals': 0,
            'profit_percentage': 0,
            'total_pl': 0,
            'avg_pl': 0,
            'symbols_count': 0
        }
    
    # Basic statistics
    profitable_deals = len(period_trades[period_trades['PL'] > 0])
    profit_percentage = (profitable_deals / total_deals * 100)
    total_pl = period_trades['PL'].sum()
    avg_pl = period_trades['PL'].mean()
    
    # Symbol diversity
    symbol_col = 'OrderSymbol' if 'OrderSymbol' in period_trades.columns else 'Symbol'
    symbols_count = period_trades[symbol_col].nunique() if symbol_col in period_trades.columns else 1
    
    return {
        'total_deals': total_deals,
        'profitable_deals': profitable_deals,
        'profit_percentage': profit_percentage,
        'total_pl': total_pl,
        'avg_pl': avg_pl,
        'symbols_count': symbols_count
    }


def _calculate_symbol_distribution(period_trades: pd.DataFrame) -> Dict[str, int]:
    """
    Calculate distribution of deals per symbol.
    
    Args:
        period_trades: Filtered trades DataFrame
        
    Returns:
        Dict with symbol -> count mapping
    """
    symbol_col = 'OrderSymbol' if 'OrderSymbol' in period_trades.columns else 'Symbol'
    
    if symbol_col not in period_trades.columns:
        return {}
    
    return period_trades[symbol_col].value_counts().to_dict()


def _render_deals_controls(period_trades: pd.DataFrame, account_id: str):
    """
    Render deals control buttons and options.
    
    Args:
        period_trades: Filtered trades DataFrame
        account_id: Account identifier
    """
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # Refresh data button
        if st.button(f"🔄 Aggiorna Dati Account {account_id}", 
                     key=f"refresh_data_tab4_{account_id}", 
                     use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Cache pulita! I dati saranno aggiornati.")
    
    with col2:
        # Toggle extended view
        show_extended = st.session_state.get(f'show_more_deals_{account_id}', False)
        
        if not show_extended:
            if st.button("📋 Mostra più deals (100)", 
                         key=f"show_more_deals_tab4_{account_id}", 
                         use_container_width=True):
                st.session_state[f'show_more_deals_{account_id}'] = True
                st.rerun()
        else:
            if st.button("📙 Mostra meno deals (50)", 
                         key=f"hide_extended_deals_tab4_{account_id}", 
                         use_container_width=True):
                st.session_state[f'show_more_deals_{account_id}'] = False
                st.rerun()


def render_deals_timeline_analysis(period_trades: pd.DataFrame, account_id: str):
    """
    Render deals timeline analysis in expandable section.
    
    Args:
        period_trades: Filtered trades DataFrame
        account_id: Account identifier
    """
    with st.expander("📅 Analisi Timeline Deals", expanded=False):
        if period_trades.empty:
            st.info("Nessun dato disponibile per analisi timeline")
            return
        
        # Daily activity analysis
        _render_daily_activity_analysis(period_trades)
        
        # Recent activity trends
        _render_recent_activity_trends(period_trades)


def _render_daily_activity_analysis(period_trades: pd.DataFrame):
    """
    Render daily trading activity analysis.
    
    Args:
        period_trades: Filtered trades DataFrame
    """
    st.markdown("**📅 Attività Giornaliera:**")
    
    # Group by date
    period_trades_copy = period_trades.copy()
    period_trades_copy['Date'] = period_trades_copy['OpenDatetime'].dt.date
    daily_activity = period_trades_copy.groupby('Date').agg({
        'PL': ['count', 'sum', 'mean'],
        'OpenPositionTicket': 'nunique'
    }).round(2)
    
    # Flatten column names
    daily_activity.columns = ['Deals', 'Total_PL', 'Avg_PL', 'Unique_Trades']
    
    # Show last 7 days
    recent_days = daily_activity.tail(7)
    
    if not recent_days.empty:
        st.dataframe(recent_days, use_container_width=True)
        
        # Show daily averages
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Deals/Giorno", f"{recent_days['Deals'].mean():.1f}")
        
        with col2:
            st.metric("P&L/Giorno", f"€{recent_days['Total_PL'].mean():.2f}")
        
        with col3:
            st.metric("Trades/Giorno", f"{recent_days['Unique_Trades'].mean():.1f}")


def _render_recent_activity_trends(period_trades: pd.DataFrame):
    """
    Render recent activity trends.
    
    Args:
        period_trades: Filtered trades DataFrame
    """
    st.markdown("**📈 Trend Attività Recente:**")
    
    # Compare last 7 days vs previous 7 days
    if len(period_trades) < 14:
        st.info("Dati insufficienti per analisi trend (minimo 14 deals)")
        return
    
    # Sort by date and split into periods
    sorted_deals = period_trades.sort_values('OpenDatetime')
    
    # Last 7 deals vs previous 7 deals
    recent_deals = sorted_deals.tail(7)
    previous_deals = sorted_deals.tail(14).head(7)
    
    # Calculate metrics for comparison
    recent_pl = recent_deals['PL'].sum()
    previous_pl = previous_deals['PL'].sum()
    
    recent_avg = recent_deals['PL'].mean()
    previous_avg = previous_deals['PL'].mean()
    
    # Show comparison
    col1, col2 = st.columns(2)
    
    with col1:
        pl_change = recent_pl - previous_pl
        st.metric("P&L Ultimi 7 Deals", f"€{recent_pl:.2f}", delta=f"€{pl_change:.2f}")
    
    with col2:
        avg_change = recent_avg - previous_avg
        st.metric("P&L Medio Ultimi 7", f"€{recent_avg:.2f}", delta=f"€{avg_change:.2f}")


def export_deals_data(period_trades: pd.DataFrame, account_id: str) -> Dict[str, Any]:
    """
    Export deals data for external analysis.
    
    Args:
        period_trades: Filtered trades DataFrame
        account_id: Account identifier
        
    Returns:
        Dict with exportable deals data
    """
    # Prepare recent deals
    recent_deals = period_trades.sort_values('OpenDatetime', ascending=False).head(100)
    
    # Calculate export statistics
    stats = _calculate_deals_statistics(period_trades)
    
    return {
        'account_id': account_id,
        'export_timestamp': pd.Timestamp.now().isoformat(),
        'recent_deals': recent_deals.to_dict('records') if not recent_deals.empty else [],
        'statistics': stats,
        'data_info': {
            'total_period_deals': len(period_trades),
            'exported_deals': len(recent_deals),
            'date_range': {
                'start': period_trades['OpenDatetime'].min().isoformat() if not period_trades.empty else None,
                'end': period_trades['OpenDatetime'].max().isoformat() if not period_trades.empty else None
            }
        }
    }