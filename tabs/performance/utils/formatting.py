# MT5 Trading Dashboard - Formatting Utilities
# File: tabs/performance/utils/formatting.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Data formatting and display utilities for performance tab.
Handles currency formatting, status indicators, and UI components.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from ..config.constants import TABLE_CONFIG, SUCCESS_MESSAGES, ERROR_MESSAGES


def format_currency(value: float, currency: str = "€", decimals: int = 2) -> str:
    """
    Formatta valori monetari con segno e colore.
    
    Args:
        value: Valore da formattare
        currency: Simbolo valuta
        decimals: Numero decimali
        
    Returns:
        String HTML formattata con colore
    """
    if pd.isna(value):
        return "N/A"
    
    if value >= 0:
        color = "green"
        sign = "+"
    else:
        color = "red"
        sign = ""
    
    formatted_value = f"{value:.{decimals}f}"
    return f"<span style='color: {color}; font-weight: bold;'>{sign}{formatted_value} {currency}</span>"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Formatta percentuali con colore basato sul valore.
    
    Args:
        value: Valore percentuale
        decimals: Numero decimali
        
    Returns:
        String HTML formattata
    """
    if pd.isna(value):
        return "N/A"
    
    color = "green" if value >= 0 else "red"
    formatted_value = f"{value:.{decimals}f}%"
    
    return f"<span style='color: {color}; font-weight: bold;'>{formatted_value}</span>"


def format_status(status: str) -> str:
    """
    Formatta lo status con colori e icone.
    
    Args:
        status: Status da formattare
        
    Returns:
        String HTML formattata
    """
    status_upper = status.upper()
    
    status_config = {
        'ACTIVE': {'color': 'green', 'icon': '●'},
        'INACTIVE': {'color': 'red', 'icon': '●'},
        'PAUSED': {'color': 'orange', 'icon': '●'},
        'ERROR': {'color': 'red', 'icon': '⚠'},
        'UNKNOWN': {'color': 'gray', 'icon': '?'}
    }
    
    config = status_config.get(status_upper, status_config['UNKNOWN'])
    return f"<span style='color: {config['color']}; font-weight: bold;'>{config['icon']}</span> {status_upper}"


def format_yes_no(value: Union[str, bool]) -> str:
    """
    Formatta valori Yes/No con colori.
    
    Args:
        value: Valore da formattare (Yes/No o True/False)
        
    Returns:
        String HTML formattata
    """
    if isinstance(value, bool):
        display_value = "YES" if value else "NO"
    else:
        display_value = str(value).upper()
    
    color = "green" if display_value in ["YES", "TRUE", "1"] else "red"
    return f"<span style='color: {color}; font-weight: bold;'>{display_value}</span>"


def format_account_badge(account_id: str, color: str = '#1f77b4') -> str:
    """
    Genera un badge colorato per l'account.
    
    Args:
        account_id: ID dell'account
        color: Colore del badge
        
    Returns:
        String HTML per badge
    """
    return f"""
    <div style="display: inline-block; padding: 4px 8px; background: {color}22; 
                color: {color}; border: 1px solid {color}44; border-radius: 12px; 
                font-size: 12px; font-weight: bold; margin: 2px;">
        {account_id}
</div>
    """


def format_time_ago(timestamp: Union[str, datetime, pd.Timestamp]) -> str:
    """
    Formatta un timestamp in formato 'X ore fa'.
    
    Args:
        timestamp: Timestamp da formattare
        
    Returns:
        String con tempo relativo
    """
    if pd.isna(timestamp) or timestamp is None:
        return "N/A"
    
    now = datetime.now()
    if isinstance(timestamp, str):
        timestamp = pd.to_datetime(timestamp)
    elif isinstance(timestamp, pd.Timestamp):
        timestamp = timestamp.to_pydatetime().values
    
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} giorni fa"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} ore fa"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} min fa"
    else:
        return "Ora"


def format_number_compact(value: float, unit: str = "") -> str:
    """
    Formatta numeri in modo compatto (K, M, B).
    
    Args:
        value: Numero da formattare
        unit: Unità di misura
        
    Returns:
        String formattata
    """
    if pd.isna(value):
        return "N/A"
    
    if abs(value) >= 1_000_000_000:
        return f"{value/1_000_000_000:.1f}B{unit}"
    elif abs(value) >= 1_000_000:
        return f"{value/1_000_000:.1f}M{unit}"
    elif abs(value) >= 1_000:
        return f"{value/1_000:.1f}K{unit}"
    else:
        return f"{value:.0f}{unit}"


def format_profit_indicator(profit: float) -> str:
    """
    Formatta indicatore di profitto con colore e icona.
    
    Args:
        profit: Valore del profitto
        
    Returns:
        String HTML con indicatore colorato
    """
    if pd.isna(profit):
        return "N/A"
    
    if profit > 0:
        return f"<span style='color: green; font-weight: bold;'>+{profit:.0f}€</span>"
    elif profit < 0:
        return f"<span style='color: red; font-weight: bold;'>{profit:.0f}€</span>"
    else:
        return f"<span style='color: gray; font-weight: bold;'>0€</span>"


def format_trade_type_badge(trade_type: str) -> str:
    """
    Formatta badge per tipo di trade.
    
    Args:
        trade_type: Tipo di trade (backtest/live)
        
    Returns:
        String HTML con badge colorato
    """
    if trade_type == 'backtest':
        return "<span style='background: #cccccc; color: #333; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: bold;'>BT</span>"
    else:
        return "<span style='background: #1f77b4; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: bold;'>LIVE</span>"


def format_setup_display_name(magic_number: int, strategy_name: str, symbol: str, 
                             profit: float, trades_count: int) -> str:
    """
    Formatta nome display per setup con performance.
    
    Args:
        magic_number: Magic number del setup
        strategy_name: Nome strategia
        symbol: Simbolo tradato
        profit: Profitto totale
        trades_count: Numero trade
        
    Returns:
        String formattata per display
    """
    performance_indicator = format_profit_indicator(profit)
    return f"MN{magic_number} - {strategy_name} ({symbol}) | {performance_indicator} ({trades_count}T)"


def format_datetime_range(start_date: datetime, end_date: datetime) -> str:
    """
    Formatta un range di date in modo compatto.
    
    Args:
        start_date: Data inizio
        end_date: Data fine
        
    Returns:
        String formattata del range
    """
    if start_date.year == end_date.year:
        if start_date.month == end_date.month:
            return f"{start_date.strftime('%d')}-{end_date.strftime('%d %b %Y')}"
        else:
            return f"{start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')}"
    else:
        return f"{start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}"


def create_metric_card_html(title: str, value: str, delta: Optional[str] = None,
                           color: str = "#1f77b4") -> str:
    """
    Crea HTML per una card metrica personalizzata.
    
    Args:
        title: Titolo della metrica
        value: Valore principale
        delta: Valore delta opzionale
        color: Colore del bordo
        
    Returns:
        String HTML per card
    """
    delta_html = f"<small style='color: #666;'>{delta}</small>" if delta else ""
    
    return f"""
    <div style="
        border-left: 4px solid {color}; 
        padding: 12px; 
        background: white; 
        border-radius: 4px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin: 4px 0;
    ">
        <div style="font-size: 12px; color: #666; margin-bottom: 4px;">{title}</div>
        <div style="font-size: 18px; font-weight: bold; color: #333;">{value}</div>
        {delta_html}
    </div>
    """


def format_table_columns(df: pd.DataFrame, table_type: str = "performance") -> Dict[str, Any]:
    """
    Formatta configurazione colonne per tabelle Streamlit.
    
    Args:
        df: DataFrame da formattare
        table_type: Tipo di tabella (performance, deals)
        
    Returns:
        Dict con configurazione colonne
    """
    if table_type == "performance":
        return {
            "P&L (€)": {"format": "%.0f €", "help": "Profitto totale"},
            "P&L/Trade (€)": {"format": "%.2f €", "help": "Profitto medio per trade"},
            "Win Rate (%)": {"format": "%.1f%%", "help": "Percentuale trade vincenti"},
            "Profit Factor": {"format": "%.2f", "help": "Profit Factor (Vincite/Perdite)"},
            "Max DD (€)": {"format": "%.0f €", "help": "Massimo drawdown"}
        }
    elif table_type == "deals":
        return {
            "P&L (€)": {"format": "%.2f €"},
            "Data Apertura": {"format": "DD/MM/YYYY HH:mm"},
            "Data Chiusura": {"format": "DD/MM/YYYY HH:mm"}
        }
    else:
        return {}


def format_debug_info(data: Dict[str, Any], max_items: int = 10) -> str:
    """
    Formatta informazioni di debug in modo leggibile.
    
    Args:
        data: Dict con dati di debug
        max_items: Massimo numero elementi da mostrare per lista
        
    Returns:
        String formattata per debug
    """
    formatted_lines = []
    
    for key, value in data.items():
        if isinstance(value, list):
            if len(value) > max_items:
                display_value = f"{value[:max_items]}... ({len(value)} totali)"
            else:
                display_value = str(value)
        elif isinstance(value, dict):
            display_value = f"Dict con {len(value)} chiavi"
        else:
            display_value = str(value)
        
        formatted_lines.append(f"**{key}**: {display_value}")
    
    return "\n".join(formatted_lines)


def get_success_message(message_key: str) -> str:
    """
    Ottiene un messaggio di successo dalle costanti.
    
    Args:
        message_key: Chiave del messaggio
        
    Returns:
        Messaggio di successo formattato
    """
    return SUCCESS_MESSAGES.get(message_key, "Operazione completata con successo")


def get_error_message(message_key: str) -> str:
    """
    Ottiene un messaggio di errore dalle costanti.
    
    Args:
        message_key: Chiave del messaggio
        
    Returns:
        Messaggio di errore formattato
    """
    return ERROR_MESSAGES.get(message_key, "Si è verificato un errore")


def create_info_box(title: str, content: str, box_type: str = "info") -> str:
    """
    Crea un box informativo colorato.
    
    Args:
        title: Titolo del box
        content: Contenuto del box
        box_type: Tipo di box (info, success, warning, error)
        
    Returns:
        String HTML per box informativo
    """
    colors = {
        "info": {"bg": "#e3f2fd", "border": "#2196f3", "icon": "[i]"},
        "success": {"bg": "#e8f5e8", "border": "#4caf50", "icon": "[OK]"},
        "warning": {"bg": "#fff3e0", "border": "#ff9800", "icon": "⚠"},
        "error": {"bg": "#ffebee", "border": "#f44336", "icon": "[ERR]"}
    }
    
    config = colors.get(box_type, colors["info"])
    
    return f"""
    <div style="
        background: {config['bg']}; 
        border-left: 4px solid {config['border']}; 
        padding: 12px; 
        margin: 8px 0; 
        border-radius: 4px;
    ">
        <div style="font-weight: bold; margin-bottom: 4px;">
            {config['icon']} {title}
        </div>
        <div>{content}</div>
    </div>
    """


def format_filter_summary(filters: Dict[str, Any]) -> str:
    """
    Formatta un riassunto dei filtri attivi.
    
    Args:
        filters: Dict con filtri attivi
        
    Returns:
        String HTML con riassunto filtri
    """
    active_filters = []
    
    if filters.get('trade_type') and filters['trade_type'] != "Tutti":
        active_filters.append(f"Tipo: {filters['trade_type']}")
    
    if filters.get('min_profit') is not None:
        active_filters.append(f"Min Profit: €{filters['min_profit']}")
    
    if filters.get('max_drawdown') is not None:
        active_filters.append(f"Max DD: €{filters['max_drawdown']}")
    
    if filters.get('selected_symbols'):
        symbol_count = len(filters['selected_symbols'])
        active_filters.append(f"Simboli: {symbol_count}")
    
    if not active_filters:
        return "<span style='color: #666; font-style: italic;'>Nessun filtro attivo</span>"
    
    return " | ".join(active_filters)
