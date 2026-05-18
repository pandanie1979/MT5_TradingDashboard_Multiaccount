# MT5 Trading Dashboard - Chart Helpers
# File: tabs/performance/utils/chart_helpers.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Chart visualization helpers for Plotly graphs.
Handles color segments, hover formatting, and subplot creation.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple, Any

from ..config.constants import CHART_CONFIG, TRADE_TYPE_COLORS


def generate_enhanced_color_segments(equity_data: pd.DataFrame, 
                                   plot_date_col: str = 'PlotDate') -> List[Dict]:
    """
    Genera segmenti di colore PIÙ VISIBILI per overlay backtest/live.
    
    Args:
        equity_data: DataFrame con equity curve e trade_type
        plot_date_col: Nome colonna con date per plotting
        
    Returns:
        Lista di shapes per overlay Plotly
    """
    if equity_data.empty or 'trade_type' not in equity_data.columns:
        return []
    
    shapes = []
    
    # Raggruppa per settimana per creare segmenti
    equity_data = equity_data.copy()
    equity_data['week'] = equity_data[plot_date_col].dt.to_period('W')
    
    for week, week_data in equity_data.groupby('week'):
        if len(week_data) == 0:
            continue
            
        bt_count = len(week_data[week_data['trade_type'] == 'backtest'])
        live_count = len(week_data[week_data['trade_type'] == 'live'])
        total_count = bt_count + live_count
        
        if total_count == 0:
            continue
        
        # Colori PIÙ INTENSI e VISIBILI
        if bt_count == total_count:
            # Solo backtest = grigio INTENSO
            color = TRADE_TYPE_COLORS['backtest']['base']
        elif live_count == total_count:
            # Solo live = blu INTENSO
            color = TRADE_TYPE_COLORS['live']['base']
        else:
            # Mix = gradiente più visibile
            live_ratio = live_count / total_count
            if live_ratio > 0.7:
                color = TRADE_TYPE_COLORS['live']['light']  # Blu predominante
            elif live_ratio < 0.3:
                color = TRADE_TYPE_COLORS['backtest']['light']  # Grigio predominante  
            else:
                color = TRADE_TYPE_COLORS['mixed']['base']  # Mix visibile
        
        x_start = week_data[plot_date_col].min()
        x_end = week_data[plot_date_col].max()
        
        shape = {
            'type': 'rect',
            'x0': x_start,
            'x1': x_end,
            'y0': 0,
            'y1': 1,
            'yref': 'paper',
            'fillcolor': color,
            'line': {'width': 0},
            'layer': 'below'
        }
        
        shapes.append(shape)
    
    return shapes


def format_hover_info_detailed(row: pd.Series, multi_mn: bool = False) -> str:
    """
    Crea hover info dettagliato per i punti della equity curve.
    
    Args:
        row: Riga del DataFrame con dati trade
        multi_mn: Se True, include info multi-setup
        
    Returns:
        String HTML formattata per hover
    """
    base_info = f"<b>P&L:</b> €{row.get('PL', 0):.2f}<br>"
    base_info += f"<b>Equity:</b> €{row.get('Cumulative_PL', 0):.2f}<br>"
    
    if 'trade_type' in row:
        trade_type_display = "Backtest" if row['trade_type'] == 'backtest' else "Live"
        base_info += f"<b>Tipo:</b> {trade_type_display}<br>"
    
    if multi_mn and 'MagicNumber' in row:
        base_info += f"<b>MN:</b> {row['MagicNumber']}<br>"
    
    if 'OrderSymbol' in row:
        base_info += f"<b>Symbol:</b> {row['OrderSymbol']}<br>"
    
    if 'ExitReason' in row:
        base_info += f"<b>Exit:</b> {row['ExitReason']}"
    
    return base_info


def create_multi_panel_chart(equity_data: pd.DataFrame, 
                            margin_timeline: pd.DataFrame,
                            account_id: str,
                            account_color: str,
                            multi_mn_selected: bool = False) -> go.Figure:
    """
    Crea chart multi-panel con Equity/Drawdown/Margin.
    
    Args:
        equity_data: DataFrame con equity curve
        margin_timeline: DataFrame con timeline margine
        account_id: ID account per titoli
        account_color: Colore account
        multi_mn_selected: Se True, modalità multi-setup
        
    Returns:
        Figura Plotly configurata
    """
    # Crea subplot con margini corretti
    fig = make_subplots(
        rows=3, cols=1,
        row_heights=CHART_CONFIG['subplot_heights'],
        subplot_titles=(
            f'Equity Curve - Account {account_id}',
            f'Portfolio Drawdown - Account {account_id}',
            f'Margine Impegnato - Account {account_id}'
        ),
        vertical_spacing=CHART_CONFIG['vertical_spacing'],
        shared_xaxes=True
    )
    
    # Calcola valori finali per annotation
    final_equity = equity_data['Cumulative_PL'].iloc[-1] if not equity_data.empty else 0
    final_drawdown = equity_data['Drawdown'].iloc[-1] if not equity_data.empty else 0
    final_margin = margin_timeline['total_margin'].iloc[-1] if not margin_timeline.empty else 0
    
    # Calcola posizioni per annotation box
    x_range, annotation_x_pos, extended_max_date = _calculate_annotation_positions(equity_data)
    
    # 1. Equity Curve
    if not equity_data.empty:
        _add_equity_trace(fig, equity_data, account_id, multi_mn_selected)
        _add_color_overlay(fig, equity_data)
        _add_annotation_box(fig, annotation_x_pos, final_equity, account_color, 'equity')
    
    # 2. Drawdown
    if not equity_data.empty:
        _add_drawdown_trace(fig, equity_data, account_id)
        _add_annotation_box(fig, annotation_x_pos, final_drawdown, "#d62728", 'drawdown')
    
    # 3. Margine Impegnato
    if not margin_timeline.empty:
        _add_margin_trace(fig, margin_timeline, account_id)
        margin_color = "#ff7f0e" if final_margin > 0 else "gray"
        _add_annotation_box(fig, annotation_x_pos, final_margin, margin_color, 'margin')
    
    # Layout finale
    _configure_chart_layout(fig, account_id, multi_mn_selected, extended_max_date, equity_data)
    
    return fig


def _calculate_annotation_positions(equity_data: pd.DataFrame) -> Tuple[float, float, pd.Timestamp]:
    """Calcola posizioni per annotation box."""
    if equity_data.empty:
        return 0, 0, pd.Timestamp.now()
    
    x_range = equity_data['PlotDate'].max() - equity_data['PlotDate'].min()
    right_margin = x_range * CHART_CONFIG['right_margin_factor']
    extended_max_date = equity_data['PlotDate'].max() + right_margin
    annotation_x_pos = equity_data['PlotDate'].max() + (right_margin * CHART_CONFIG['annotation_x_factor'])
    
    return x_range, annotation_x_pos, extended_max_date


def _add_equity_trace(fig: go.Figure, equity_data: pd.DataFrame, 
                     account_id: str, multi_mn: bool):
    """Aggiunge trace per equity curve."""
    hover_texts = []
    for _, row in equity_data.iterrows():
        hover_texts.append(format_hover_info_detailed(row, multi_mn))
    
    fig.add_trace(
        go.Scatter(
            x=equity_data['PlotDate'],
            y=equity_data['Cumulative_PL'],
            mode='lines',
            name=f'Equity Account {account_id}',
            line=dict(color='#1f77b4', width=3, shape='hv'),
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_texts,
            showlegend=False
        ),
        row=1, col=1
    )


def _add_color_overlay(fig: go.Figure, equity_data: pd.DataFrame):
    """Aggiunge overlay colori per backtest/live."""
    color_shapes = generate_enhanced_color_segments(equity_data, 'PlotDate')
    for shape in color_shapes:
        fig.add_shape(shape, row=1, col=1)


def _add_drawdown_trace(fig: go.Figure, equity_data: pd.DataFrame, account_id: str):
    """Aggiunge trace per drawdown."""
    fig.add_trace(
        go.Scatter(
            x=equity_data['PlotDate'],
            y=equity_data['Drawdown'],
            mode='lines',
            name=f'Drawdown Account {account_id}',
            line=dict(color='#d62728', width=2, shape='hv'),
            fill='tozeroy',
            fillcolor='rgba(214, 39, 40, 0.3)',
            hovertemplate=f'<b>Account:</b> {account_id}<br><b>Data:</b> %{{x}}<br><b>Drawdown:</b> €%{{y:.2f}}<extra></extra>',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Linea zero per il drawdown
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=2, col=1)


def _add_margin_trace(fig: go.Figure, margin_timeline: pd.DataFrame, account_id: str):
    """Aggiunge trace per margine."""
    fig.add_trace(
        go.Scatter(
            x=margin_timeline['timestamp'],
            y=margin_timeline['total_margin'],
            mode='lines',
            name=f'Margine Account {account_id}',
            line=dict(color='#ff7f0e', width=2, shape='hv'),
            fill='tozeroy',
            fillcolor='rgba(255, 127, 14, 0.3)',
            hovertemplate=f'<b>Account:</b> {account_id}<br><b>Data:</b> %{{x}}<br><b>Margine:</b> €%{{y:.2f}}<extra></extra>',
            showlegend=False
        ),
        row=3, col=1
    )


def _add_annotation_box(fig: go.Figure, x_pos: float, value: float, 
                       color: str, chart_type: str):
    """Aggiunge annotation box con valore finale."""
    row_map = {'equity': 1, 'drawdown': 2, 'margin': 3}
    row = row_map.get(chart_type, 1)
    
    fig.add_annotation(
        x=x_pos,
        y=value,
        text=f"€{value:.0f}",
        showarrow=False,
        bgcolor=color,
        bordercolor="white",
        borderwidth=2,
        font=dict(color="white", size=11, family="Arial Black"),
        xref=f"x{row}",
        yref=f"y{row}",
        xanchor="center",
        yanchor="middle"
    )


def _configure_chart_layout(fig: go.Figure, account_id: str, multi_mn: bool,
                          extended_max_date: pd.Timestamp, equity_data: pd.DataFrame):
    """Configura layout finale del chart."""
    title_suffix = " (Multi-Setup)" if multi_mn else " (Single Setup)"
    
    fig.update_layout(
        height=CHART_CONFIG['height'],
        showlegend=False,
        hovermode='x unified',
        plot_bgcolor='white',
        title_text=f"Dashboard Performance - Account {account_id}{title_suffix}",
        title_x=0.5,
        title_font_size=16,
        margin=CHART_CONFIG['margins']
    )
    
    # Configurazione assi
    fig.update_yaxes(title_text="Equity (€)", row=1, col=1, gridcolor='lightgray', gridwidth=1)
    fig.update_yaxes(title_text="Drawdown (€)", row=2, col=1, gridcolor='lightgray', gridwidth=1)
    fig.update_yaxes(title_text="Margine (€)", row=3, col=1, gridcolor='lightgray', gridwidth=1)
    
    fig.update_xaxes(title_text="", row=1, col=1, gridcolor='lightgray', gridwidth=1)
    fig.update_xaxes(title_text="", row=2, col=1, gridcolor='lightgray', gridwidth=1)
    fig.update_xaxes(title_text="Data", row=3, col=1, gridcolor='lightgray', gridwidth=1)
    
    # Estendi range X per annotation box
    if not equity_data.empty:
        for row_num in [1, 2, 3]:
            fig.update_xaxes(
                range=[
                    equity_data['PlotDate'].min(),
                    extended_max_date
                ],
                row=row_num, col=1
            )


def generate_period_info_enhanced(equity_data: pd.DataFrame, 
                                plot_date_col: str = 'PlotDate') -> str:
    """
    Genera informazioni testuali dettagliate sui periodi per migliorare la comprensione.
    
    Args:
        equity_data: DataFrame con equity curve e color info
        plot_date_col: Nome colonna date
        
    Returns:
        String con informazioni dettagliate periodo
    """
    if equity_data.empty or 'trade_type' not in equity_data.columns:
        return "Dati insufficienti per analisi periodo"
    
    # Analisi complessiva
    total_deals = len(equity_data)
    bt_deals = len(equity_data[equity_data['trade_type'] == 'backtest'])
    live_deals = len(equity_data[equity_data['trade_type'] == 'live'])
    
    bt_percentage = (bt_deals / total_deals * 100) if total_deals > 0 else 0
    live_percentage = (live_deals / total_deals * 100) if total_deals > 0 else 0
    
    # Analisi temporale
    total_days = (equity_data[plot_date_col].max() - equity_data[plot_date_col].min()).days
    
    # Trova i periodi
    equity_data_copy = equity_data.copy()
    equity_data_copy['month'] = equity_data_copy[plot_date_col].dt.to_period('M')
    monthly_analysis = []
    
    for month, month_data in equity_data_copy.groupby('month'):
        month_bt = len(month_data[month_data['trade_type'] == 'backtest'])
        month_live = len(month_data[month_data['trade_type'] == 'live'])
        month_total = len(month_data)
        
        if month_total == 0:
            continue
            
        month_bt_pct = (month_bt / month_total * 100)
        
        if month_bt_pct == 100:
            period_type = "Solo Backtest"
        elif month_bt_pct == 0:
            period_type = "Solo Live"
        elif month_bt_pct > 70:
            period_type = "Prevalenza Backtest"
        elif month_bt_pct < 30:
            period_type = "Prevalenza Live"
        else:
            period_type = "Mix Equilibrato"
        
        monthly_analysis.append(f"{month}: {period_type} ({month_bt}/{month_live})")
    
    # Componi messaggio informativo
    info_parts = [
        f"**Composizione Globale**: {bt_deals} deals backtest ({bt_percentage:.1f}%) + {live_deals} deals live ({live_percentage:.1f}%)",
        f"**Periodo Analizzato**: {total_days} giorni",
        f"**Legenda Colori**: Grigio = Backtest | Blu = Live | Viola = Mix"
    ]

    # Aggiunge analisi mensile se rilevante
    if len(monthly_analysis) <= 6:  # Solo se non troppo verboso
        info_parts.append("**Breakdown Mensile**:")
        info_parts.extend([f"  {analysis}" for analysis in monthly_analysis])
    
    return "\n".join(info_parts)


def create_simple_line_chart(data: pd.DataFrame, 
                            x_col: str, 
                            y_col: str, 
                            title: str,
                            color: str = '#1f77b4') -> go.Figure:
    """
    Crea un chart lineare semplice per visualizzazioni veloci.
    
    Args:
        data: DataFrame con i dati
        x_col: Nome colonna X
        y_col: Nome colonna Y  
        title: Titolo del grafico
        color: Colore della linea
        
    Returns:
        Figura Plotly configurata
    """
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=data[x_col],
            y=data[y_col],
            mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=4),
            name=title
        )
    )
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col,
        yaxis_title=y_col,
        height=400,
        showlegend=False,
        plot_bgcolor='white',
        hovermode='x'
    )
    
    return fig