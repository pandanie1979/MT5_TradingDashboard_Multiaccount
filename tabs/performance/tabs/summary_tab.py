# MT5 Trading Dashboard - Performance Summary Tab Component
# File: tabs/performance/tabs/summary_tab.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Performance summary tab component.
Displays aggregate metrics in 4x3 layout using pure Streamlit components.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from ..utils.data_processing import create_continuous_equity_curve, calculate_margin_timeline
from ..utils.formatting import get_error_message
from data.metrics import calculate_risk_metrics


def render_performance_summary_tab(period_trades: pd.DataFrame, account_id: str, account_color: str):
    """
    Render Tab 2: Performance Summary with aggregate metrics.
    Uses pure Streamlit components in 4x3 layout for maximum compatibility.
    
    Args:
        period_trades: Filtered trades for current period and setups
        account_id: Account identifier
        account_color: Account color for styling
    """
    st.markdown(f"### Performance Summary - Account {account_id}")
    
    if period_trades.empty:
        st.warning(get_error_message("no_data"))
        return
    
    # Calculate all required metrics
    metrics_data = _calculate_comprehensive_metrics(period_trades)
    
    # Render metrics in 4 sections with 3 metrics each
    _render_performance_base_section(metrics_data)
    _render_risk_metrics_section(metrics_data)
    _render_drawdown_analysis_section(metrics_data)
    _render_margin_stats_section(metrics_data)


def _calculate_comprehensive_metrics(period_trades: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate all metrics needed for the summary display.
    
    Args:
        period_trades: Filtered trades DataFrame
        
    Returns:
        Dict with all calculated metrics
    """
    # Basic calculations
    unique_trades = period_trades['OpenPositionTicket'].nunique()
    total_deals = len(period_trades)
    total_profit = period_trades['PL'].sum()
    
    # Trade results for win rate
    trade_results = period_trades.groupby('OpenPositionTicket')['PL'].sum()
    winning_trades = len(trade_results[trade_results > 0])
    win_rate = (winning_trades / len(trade_results) * 100) if len(trade_results) > 0 else 0
    
    # Profit Factor
    winning_sum = trade_results[trade_results > 0].sum()
    losing_sum = abs(trade_results[trade_results < 0].sum())
    profit_factor = winning_sum / losing_sum if losing_sum > 0 else float('inf')
    
    # Risk metrics
    try:
        risk_metrics = calculate_risk_metrics(period_trades)
    except:
        risk_metrics = {
            'max_win_streak': 0, 'max_loss_streak': 0, 'sharpe_ratio': 0,
            'avg_win': 0, 'avg_loss': 0
        }
    
    # Drawdown metrics
    equity_data = create_continuous_equity_curve(
        period_trades.sort_values('OpenDatetime'), 'OpenDatetime'
    )
    
    if not equity_data.empty and 'Drawdown' in equity_data.columns:
        max_drawdown = equity_data['Drawdown'].min()  # Most negative
        avg_drawdown = equity_data[equity_data['Drawdown'] < 0]['Drawdown'].mean() if any(equity_data['Drawdown'] < 0) else 0
        dd_periods = equity_data[equity_data['Drawdown'] < 0]
        max_dd_duration = len(dd_periods) if len(dd_periods) > 0 else 0
    else:
        max_drawdown = avg_drawdown = max_dd_duration = 0
    
    # Margin metrics
    margin_timeline = calculate_margin_timeline(period_trades)
    if not margin_timeline.empty:
        max_margin = margin_timeline['total_margin'].max()
        current_margin = margin_timeline['total_margin'].iloc[-1]
    else:
        max_margin = current_margin = 0
    
    return {
        # Performance Base
        'total_profit': total_profit,
        'unique_trades': unique_trades,
        'total_deals': total_deals,
        'win_rate': win_rate,
        'winning_trades': winning_trades,
        'profit_factor': profit_factor,
        
        # Risk Metrics
        'max_win_streak': risk_metrics.get('max_win_streak', 0),
        'max_loss_streak': risk_metrics.get('max_loss_streak', 0),
        'sharpe_ratio': risk_metrics.get('sharpe_ratio', 0),
        'avg_win': risk_metrics.get('avg_win', 0),
        'avg_loss': abs(risk_metrics.get('avg_loss', 0)),
        
        # Drawdown Analysis
        'max_drawdown': max_drawdown,
        'avg_drawdown': avg_drawdown,
        'max_dd_duration': max_dd_duration,
        
        # Margin & Stats
        'max_margin': max_margin,
        'current_margin': current_margin
    }


def _render_performance_base_section(metrics: Dict[str, Any]):
    """
    Render Section 1: Performance Base metrics.
    
    Args:
        metrics: Calculated metrics dictionary
    """
    st.markdown("#### Performance Base")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        profit_delta = f"€{metrics['total_profit']/metrics['unique_trades']:.0f}/trade" if metrics['unique_trades'] > 0 else None
        st.metric(
            label="Profit Totale",
            value=f"€{metrics['total_profit']:.0f}",
            delta=profit_delta
        )
    
    with col2:
        win_delta = f"{metrics['winning_trades']}/{metrics['unique_trades']}"
        st.metric(
            label="Win Rate",
            value=f"{metrics['win_rate']:.1f}%",
            delta=win_delta
        )
    
    with col3:
        pf_display = f"{metrics['profit_factor']:.2f}" if metrics['profit_factor'] != float('inf') else "∞"
        st.metric(
            label="Profit Factor",
            value=pf_display,
            delta="Wins/Losses"
        )


def _render_risk_metrics_section(metrics: Dict[str, Any]):
    """
    Render Section 2: Risk Metrics.
    
    Args:
        metrics: Calculated metrics dictionary
    """
    st.markdown("#### Risk Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Max Win Streak",
            value=f"{metrics['max_win_streak']}",
            delta="consecutivi"
        )
    
    with col2:
        st.metric(
            label="Max Loss Streak",
            value=f"{metrics['max_loss_streak']}",
            delta="consecutivi"
        )
    
    with col3:
        st.metric(
            label="Sharpe Ratio",
            value=f"{metrics['sharpe_ratio']:.2f}",
            delta="risk-adj return"
        )


def _render_drawdown_analysis_section(metrics: Dict[str, Any]):
    """
    Render Section 3: Drawdown Analysis.
    
    Args:
        metrics: Calculated metrics dictionary
    """
    st.markdown("#### Drawdown Analysis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Max Drawdown",
            value=f"€{metrics['max_drawdown']:.0f}",
            delta="peak-to-trough"
        )
    
    with col2:
        st.metric(
            label="Avg Drawdown",
            value=f"€{metrics['avg_drawdown']:.0f}",
            delta="media DD"
        )
    
    with col3:
        st.metric(
            label="DD Duration",
            value=f"{metrics['max_dd_duration']}",
            delta="deals in DD"
        )


def _render_margin_stats_section(metrics: Dict[str, Any]):
    """
    Render Section 4: Margin & Stats.
    
    Args:
        metrics: Calculated metrics dictionary
    """
    st.markdown("#### Margine & Stats")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Max Margine",
            value=f"€{metrics['max_margin']:.0f}",
            delta="picco utilizzo"
        )
    
    with col2:
        deals_delta = f"{metrics['total_deals']:,} deals"
        st.metric(
            label="Trades Unici",
            value=f"{metrics['unique_trades']:,}",
            delta=deals_delta
        )
    
    with col3:
        avg_win_loss = f"€{metrics['avg_win']:.0f}/€{metrics['avg_loss']:.0f}"
        st.metric(
            label="Avg Win/Loss",
            value=avg_win_loss,
            delta="per trade"
        )


def render_performance_insights(metrics: Dict[str, Any], account_id: str):
    """
    Render additional performance insights based on metrics.
    
    Args:
        metrics: Calculated metrics dictionary
        account_id: Account identifier
    """
    st.markdown("---")
    st.markdown("#### Performance Insights")
    
    insights = _generate_performance_insights(metrics)
    
    for insight in insights:
        if insight['type'] == 'success':
            st.success(insight['message'])
        elif insight['type'] == 'warning':
            st.warning(insight['message'])
        elif insight['type'] == 'info':
            st.info(insight['message'])


def _generate_performance_insights(metrics: Dict[str, Any]) -> list:
    """
    Generate performance insights based on metrics analysis.
    
    Args:
        metrics: Calculated metrics dictionary
        
    Returns:
        List of insight dictionaries
    """
    insights = []
    
    # Profit Factor Analysis
    if metrics['profit_factor'] > 2.0:
        insights.append({
            'type': 'success',
            'message': f"Excellent Profit Factor ({metrics['profit_factor']:.2f}) - Strong strategy performance!"
        })
    elif metrics['profit_factor'] < 1.0:
        insights.append({
            'type': 'warning',
            'message': f"⚠ Profit Factor below 1.0 ({metrics['profit_factor']:.2f}) - Strategy losing money overall"
        })
    
    # Win Rate Analysis
    if metrics['win_rate'] > 70:
        insights.append({
            'type': 'success',
            'message': f"[OK] High win rate ({metrics['win_rate']:.1f}%) - Consistent winning strategy"
        })
    elif metrics['win_rate'] < 30:
        insights.append({
            'type': 'warning',
            'message': f"Low win rate ({metrics['win_rate']:.1f}%) - Consider strategy optimization"
        })
    
    # Drawdown Analysis
    if abs(metrics['max_drawdown']) > abs(metrics['total_profit']) * 0.3:
        insights.append({
            'type': 'warning',
            'message': f"[HIGH DD] High drawdown risk - Max DD (€{metrics['max_drawdown']:.0f}) is significant vs profit"
        })
    
    # Streak Analysis
    if metrics['max_loss_streak'] > 10:
        insights.append({
            'type': 'info',
            'message': f"Long loss streak detected ({metrics['max_loss_streak']} consecutive) - Monitor risk management"
        })
    
    return insights


def export_summary_metrics(metrics: Dict[str, Any], account_id: str) -> Dict[str, Any]:
    """
    Export summary metrics for external analysis.
    
    Args:
        metrics: Calculated metrics dictionary
        account_id: Account identifier
        
    Returns:
        Dict with exportable summary data
    """
    return {
        'account_id': account_id,
        'export_timestamp': pd.Timestamp.now().isoformat(),
        'performance_summary': {
            'total_profit': metrics['total_profit'],
            'profit_factor': metrics['profit_factor'],
            'win_rate': metrics['win_rate'],
            'max_drawdown': metrics['max_drawdown'],
            'sharpe_ratio': metrics['sharpe_ratio']
        },
        'trading_activity': {
            'unique_trades': metrics['unique_trades'],
            'total_deals': metrics['total_deals'],
            'deals_per_trade': metrics['total_deals'] / metrics['unique_trades'] if metrics['unique_trades'] > 0 else 0
        },
        'risk_metrics': {
            'max_win_streak': metrics['max_win_streak'],
            'max_loss_streak': metrics['max_loss_streak'],
            'avg_win': metrics['avg_win'],
            'avg_loss': metrics['avg_loss']
        }
    }