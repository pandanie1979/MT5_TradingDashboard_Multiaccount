import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Any, Dict

try:
    from data.loader import get_trades_data
except ImportError:
    from ..data.loader import get_trades_data


def render(all_accounts_dict: Dict[str, Any]):
    """Render the Global Analytics tab with aggregated portfolio view."""
    st.markdown("### Portfolio View — All Accounts")

    if not all_accounts_dict:
        st.warning("Nessun account configurato.")
        return

    portfolio_frames = []
    failed_accounts = []

    for acc_id, acc_info in all_accounts_dict.items():
        acc_path = acc_info.get('path', '')
        try:
            df = get_trades_data(acc_id, acc_path)
            if df.empty:
                continue
            df = df.copy()
            df['Account_ID'] = acc_id
            portfolio_frames.append(df)
        except Exception as e:
            failed_accounts.append(acc_id)
            st.error(f"[ERR] Errore caricamento account {acc_id}: {str(e)}")

    if failed_accounts:
        st.warning(f"Dati non disponibili per: {', '.join(failed_accounts)}")

    if not portfolio_frames:
        st.info("Nessun dato disponibile per la vista portfolio.")
        return

    portfolio_df = pd.concat(portfolio_frames, ignore_index=True)
    portfolio_df['OpenDatetime'] = pd.to_datetime(portfolio_df['OpenDatetime'], errors='coerce')
    portfolio_df = portfolio_df.dropna(subset=['OpenDatetime', 'PL'])
    portfolio_df = portfolio_df.sort_values('OpenDatetime').reset_index(drop=True)

    if portfolio_df.empty:
        st.info("Nessun trade valido nel portfolio.")
        return

    _render_equity_curve(portfolio_df)
    st.markdown("---")
    _render_account_comparison(portfolio_df)


def _render_equity_curve(portfolio_df: pd.DataFrame):
    """Render cumulative portfolio equity curve."""
    st.markdown("#### Equity Curve — Portfolio Aggregato")

    equity = portfolio_df[['OpenDatetime', 'PL']].copy()
    equity['Cumulative_PL'] = equity['PL'].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity['OpenDatetime'],
        y=equity['Cumulative_PL'],
        mode='lines',
        name='P&L Cumulativo',
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)',
    ))
    fig.update_layout(
        xaxis_title='Data',
        yaxis_title='P&L Cumulativo',
        hovermode='x unified',
        margin=dict(l=0, r=0, t=30, b=0),
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_account_comparison(portfolio_df: pd.DataFrame):
    """Render per-account KPI comparison table."""
    st.markdown("#### Confronto Account")

    rows = []
    for acc_id, group in portfolio_df.groupby('Account_ID'):
        deal_count = len(group)
        win_count = len(group[group['PL'] > 0])
        total_pl = group['PL'].sum()
        win_rate = (win_count / deal_count * 100) if deal_count > 0 else 0.0
        rows.append({
            'Account': acc_id,
            'Total P&L': round(float(total_pl), 2),
            'Win Rate %': round(float(win_rate), 1),
            'Deals': deal_count,
        })

    comparison_df = (
        pd.DataFrame(rows)
        .sort_values('Total P&L', ascending=False)
        .reset_index(drop=True)
    )

    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Account': st.column_config.TextColumn('Account'),
            'Total P&L': st.column_config.NumberColumn('Total P&L', format='%.2f'),
            'Win Rate %': st.column_config.NumberColumn('Win Rate', format='%.1f%%'),
            'Deals': st.column_config.NumberColumn('Deals', format='%d'),
        },
    )
