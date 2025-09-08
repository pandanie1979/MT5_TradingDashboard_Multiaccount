# MT5 Trading Dashboard - Sidebar Account Info
# File: tabs/performance/sidebar/account_info.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Account information header component for sidebar.
Shows account statistics and status with color coding.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from ..utils.formatting import format_account_badge, format_number_compact


def render_account_info_header(trades_df: pd.DataFrame, account_id: str, 
                              account_info: Dict[str, Any]):
    """
    Render account information header in sidebar with complete statistics.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
        account_info: Account information dict with color, status, etc.
    """
    account_color = account_info.get('color', '#1f77b4')
    
    # Calculate comprehensive statistics
    unique_trades = trades_df['OpenPositionTicket'].nunique() if 'OpenPositionTicket' in trades_df.columns else 0
    total_deals = len(trades_df)
    total_files = account_info.get('trade_files', 0)
    
    # Filename statistics for debug/classification
    filenames_with_000000 = 0
    filenames_without_000000 = 0
    if 'SourceFilename' in trades_df.columns:
        filenames_with_000000 = trades_df['SourceFilename'].str.contains('_000000', na=False).sum()
        filenames_without_000000 = len(trades_df) - filenames_with_000000
    
    # Calculate basic performance metrics
    total_profit = trades_df['PL'].sum() if 'PL' in trades_df.columns else 0
    
    # Render complete header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {account_color}22 0%, {account_color}11 100%);
        border: 1px solid {account_color}44;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 15px;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="width: 4px; height: 30px; background: {account_color}; margin-right: 10px; border-radius: 2px;"></div>
            <div>
                <h4 style="margin: 0; color: {account_color};">📈 Account {account_id}</h4>
                <small style="color: #666;">Analisi Performance</small>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 11px;">
            <div><strong>📁 Files:</strong> {total_files}</div>
            <div><strong>📊 Deals:</strong> {total_deals:,}</div>
            <div><strong>🎯 Trades:</strong> {unique_trades:,}</div>
            <div><strong>📈 Ratio:</strong> {total_deals/unique_trades:.1f}</div>
            <div><strong>🔧 BT Files:</strong> {filenames_with_000000}</div>
            <div><strong>⚡ Live Files:</strong> {filenames_without_000000}</div>
        </div>
        <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid {account_color}33;">
            <div style="font-size: 12px; font-weight: bold; color: {account_color};">
                💰 P&L Totale: {format_number_compact(total_profit, '€')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_account_status_indicator(account_info: Dict[str, Any]):
    """
    Render account status indicator with color coding.
    
    Args:
        account_info: Account information dict
    """
    status = account_info.get('status', 'unknown')
    
    if status == 'active':
        st.success("✅ Account Attivo")
    elif status == 'error':
        st.error("❌ Errore Connessione")
    else:
        st.warning("⚠️ Status Sconosciuto")


def render_account_quick_stats(trades_df: pd.DataFrame):
    """
    Render quick statistics grid for account.
    
    Args:
        trades_df: Complete trades DataFrame
    """
    if trades_df.empty:
        st.info("Nessun dato disponibile")
        return
    
    # Calculate key metrics
    unique_trades = trades_df['OpenPositionTicket'].nunique()
    total_deals = len(trades_df)
    
    if 'PL' in trades_df.columns:
        total_profit = trades_df['PL'].sum()
        avg_profit = total_profit / unique_trades if unique_trades > 0 else 0
        
        # Win rate calculation
        trade_results = trades_df.groupby('OpenPositionTicket')['PL'].sum()
        winning_trades = len(trade_results[trade_results > 0])
        win_rate = (winning_trades / len(trade_results) * 100) if len(trade_results) > 0 else 0
    else:
        total_profit = avg_profit = win_rate = 0
    
    # Date range
    if 'OpenDatetime' in trades_df.columns:
        date_range = (trades_df['OpenDatetime'].max() - trades_df['OpenDatetime'].min()).days
    else:
        date_range = 0
    
    # Render metrics in compact format
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Trades", f"{unique_trades:,}", delta=f"{total_deals:,} deals")
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    with col2:
        st.metric("P&L Totale", f"€{total_profit:.0f}")
        st.metric("Periodo", f"{date_range} giorni")


def render_account_file_analysis(trades_df: pd.DataFrame, account_id: str):
    """
    Render file analysis for debug purposes.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    if 'SourceFilename' not in trades_df.columns:
        st.info("Analisi file non disponibile")
        return
    
    filenames = trades_df['SourceFilename'].unique()
    
    # Analyze filename patterns
    backtest_files = [f for f in filenames if '_000000' in f]
    live_files = [f for f in filenames if '_000000' not in f]
    
    # Show summary
    st.markdown("**📁 Analisi File:**")
    st.write(f"- Totale file: {len(filenames)}")
    st.write(f"- File backtest (_000000): {len(backtest_files)}")
    st.write(f"- File live: {len(live_files)}")
    
    # Show examples if requested
    with st.expander("📄 Esempi Filename"):
        if backtest_files:
            st.write("**Backtest:**")
            for f in backtest_files[:3]:
                st.code(f)
        
        if live_files:
            st.write("**Live:**")
            for f in live_files[:3]:
                st.code(f)


def get_account_summary_data(trades_df: pd.DataFrame, account_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get comprehensive account summary data for external use.
    
    Args:
        trades_df: Complete trades DataFrame
        account_info: Account information dict
        
    Returns:
        Dict with comprehensive account summary
    """
    summary = {
        'account_id': account_info.get('account_id', 'Unknown'),
        'status': account_info.get('status', 'unknown'),
        'color': account_info.get('color', '#1f77b4'),
        'total_files': account_info.get('trade_files', 0),
        'ea_files': account_info.get('ea_files', 0)
    }
    
    if not trades_df.empty:
        summary.update({
            'total_deals': len(trades_df),
            'unique_trades': trades_df['OpenPositionTicket'].nunique() if 'OpenPositionTicket' in trades_df.columns else 0,
            'total_profit': trades_df['PL'].sum() if 'PL' in trades_df.columns else 0,
            'date_range': {
                'start': trades_df['OpenDatetime'].min() if 'OpenDatetime' in trades_df.columns else None,
                'end': trades_df['OpenDatetime'].max() if 'OpenDatetime' in trades_df.columns else None
            }
        })
        
        # Filename analysis
        if 'SourceFilename' in trades_df.columns:
            filenames = trades_df['SourceFilename'].unique()
            summary['filename_analysis'] = {
                'total_files': len(filenames),
                'backtest_files': len([f for f in filenames if '_000000' in f]),
                'live_files': len([f for f in filenames if '_000000' not in f])
            }
    
    return summary