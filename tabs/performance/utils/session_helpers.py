# MT5 Trading Dashboard - Session State Helpers
# File: tabs/performance/utils/session_helpers.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Session state management utilities for performance tab.
Handles period configuration, setup selection, and filter management.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple

from ..config.constants import (
    SESSION_KEYS, PERIOD_PRESETS, DEFAULTS, 
    get_session_key, validate_sidebar_width
)


# AGGIORNAMENTO alla funzione get_period_configuration
def get_period_configuration(account_id: str) -> Optional[Dict[str, Any]]:
    """
    Ottiene la configurazione del periodo dai widget (non session state).
    UPDATED: Marca automaticamente come modificato dall'utente quando accede ai widget.
    """
    # Usa chiavi widget
    start_widget_key = f"date_start_{account_id}"
    end_widget_key = f"date_end_{account_id}"
    
    start_date = st.session_state.get(start_widget_key)
    end_date = st.session_state.get(end_widget_key)
    
    if not start_date or not end_date:
        return None
    
    # NUOVO: Se l'utente sta usando la configurazione periodo, marcala come user-modified
    # per proteggerla da reset futuri
    period_initialized_key = f"period_user_set_{account_id}"
    if st.session_state.get(period_initialized_key) == "auto_default":
        # Solo la prima volta che accede, marcala come user-accessed
        st.session_state[period_initialized_key] = "user_accessed"
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'start_datetime': pd.to_datetime(start_date),
        'end_datetime': pd.to_datetime(end_date) + pd.Timedelta(days=1)
    }
    
def get_selected_setups(account_id: str) -> List[int]:
    """
    Ottiene la lista dei setup selezionati dalla session state.
    
    Args:
        account_id: ID dell'account
        
    Returns:
        Lista di magic numbers selezionati
    """
    selected_setups = []
    
    # Cerca tutte le chiavi che iniziano con setup_{account_id}_
    for key in st.session_state:
        if key.startswith(f"setup_{account_id}_") and st.session_state[key]:
            # Estrai magic number dalla chiave
            magic_str = key.replace(f"setup_{account_id}_", "").replace("_cb_", "_").split("_")[0]
            try:
                magic_number = int(magic_str)
                selected_setups.append(magic_number)
            except ValueError:
                continue
    
    return selected_setups


def get_advanced_filters(account_id: str) -> Dict[str, Any]:
    """
    Ottiene i filtri avanzati dalla session state.
    
    Args:
        account_id: ID dell'account
        
    Returns:
        Dict con configurazione filtri
    """
    return {
        'trade_type': st.session_state.get(
            get_session_key("trade_type_filter", account_id), "Tutti"
        ),
        'min_profit': st.session_state.get(
            get_session_key("min_profit_filter", account_id)
        ),
        'max_drawdown': st.session_state.get(
            get_session_key("max_dd_filter", account_id)
        ),
        'selected_symbols': st.session_state.get(
            get_session_key("symbols_filter", account_id), []
        )
    }


def apply_period_filters(trades_df: pd.DataFrame, 
                        period_config: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """
    Applica i filtri temporali ai trade.
    
    Args:
        trades_df: DataFrame con i trade
        period_config: Configurazione periodo (da get_period_configuration)
        
    Returns:
        DataFrame filtrato per periodo
    """
    if not period_config or trades_df.empty:
        return trades_df
    
    return trades_df[
        (trades_df['OpenDatetime'] >= period_config['start_datetime']) & 
        (trades_df['OpenDatetime'] <= period_config['end_datetime'])
    ]


def apply_advanced_filters(trades_df: pd.DataFrame, 
                          filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Applica i filtri avanzati ai trade.
    
    IMPORTANTE: 
    - Filtri profit/drawdown si applicano a livello SETUP (magic number)
    - Filtro simboli si applica a livello TRADE singolo
    - Filtro tipo trade si applica a livello TRADE singolo
    
    Args:
        trades_df: DataFrame con i trade
        filters: Configurazione filtri
        
    Returns:
        DataFrame filtrato
    """
    if trades_df.empty:
        return trades_df
    
    filtered_df = trades_df.copy()
    
    # Filtro tipo trade
    if filters['trade_type'] == "Solo Backtest":
        from .data_processing import classify_trades_backtest_vs_live
        classified_df = classify_trades_backtest_vs_live(filtered_df)
        filtered_df = classified_df[classified_df['trade_type'] == 'backtest']
    elif filters['trade_type'] == "Solo Live":
        from .data_processing import classify_trades_backtest_vs_live
        classified_df = classify_trades_backtest_vs_live(filtered_df)
        filtered_df = classified_df[classified_df['trade_type'] == 'live']
    
    # Filtro profit minimo
    if filters['min_profit'] is not None:
        trade_profits = filtered_df.groupby('OpenPositionTicket')['PL'].sum()
        valid_tickets = trade_profits[trade_profits >= filters['min_profit']].index
        filtered_df = filtered_df[filtered_df['OpenPositionTicket'].isin(valid_tickets)]
    
    # Filtro simboli
    if filters['selected_symbols'] and 'OrderSymbol' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['OrderSymbol'].isin(filters['selected_symbols'])]
    
    return filtered_df


def calculate_preset_dates(preset: str, min_date: date, max_date: date) -> Tuple[date, date]:
    """
    Calcola le date di default basate sul preset selezionato.
    
    Args:
        preset: Tipo di preset (7d, 30d, 90d, ytd)
        min_date: Data minima disponibile
        max_date: Data massima disponibile
        
    Returns:
        Tupla (start_date, end_date)
    """
    end_date = max_date
    
    if preset in PERIOD_PRESETS:
        days = PERIOD_PRESETS[preset]["days"]
        if days is None:  # YTD
            start_date = max(min_date, datetime(end_date.year, 1, 1).date())
        else:
            start_date = max(min_date, end_date - timedelta(days=days))
    else:
        # Default 30 giorni
        start_date = max(min_date, end_date - timedelta(days=30))
    
    return start_date, end_date


def get_current_period_trades(trades_df: pd.DataFrame, account_id: str) -> pd.DataFrame:
    """
    Ottiene i trade filtrati per il periodo corrente.
    CLEANED: Removed debug prints for production use.
    
    Args:
        trades_df: DataFrame with trades
        account_id: Account identifier
        
    Returns:
        DataFrame filtered by current period selection
    """
    start_widget_key = f"date_start_{account_id}"
    end_widget_key = f"date_end_{account_id}"
    
    # Check if widget keys exist in session state
    if start_widget_key in st.session_state and end_widget_key in st.session_state:
        start_date = st.session_state[start_widget_key]
        end_date = st.session_state[end_widget_key]
        
        # Convert to datetime for filtering
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1)
        
        # Apply period filter
        filtered_df = trades_df[
            (trades_df['OpenDatetime'] >= start_datetime) & 
            (trades_df['OpenDatetime'] <= end_datetime)
        ]
        
        return filtered_df
    else:
        # If no period selection exists, return all trades
        # This allows the period widgets to initialize properly
        return trades_df


def initialize_session_defaults(account_id: str, trades_df: pd.DataFrame):
    """
    Inizializza SOLO se NULLA è configurato dall'utente.
    FIXED: Protegge le date impostate dall'utente da reset involontari.
    """
    # Sidebar width
    sidebar_width_key = get_session_key("sidebar_width", account_id)
    if sidebar_width_key not in st.session_state:
        st.session_state[sidebar_width_key] = DEFAULTS["sidebar_width"]
    
    # CRITICO: Periodo date - PROTETTO da sovrascrittura
    start_widget_key = f"date_start_{account_id}"
    end_widget_key = f"date_end_{account_id}"
    
    # NUOVO: Controlla se l'utente ha mai impostato date custom
    period_initialized_key = f"period_user_set_{account_id}"
    
    # Solo se NON ci sono widget period attivi E l'utente non li ha mai toccati
    if (start_widget_key not in st.session_state and 
        end_widget_key not in st.session_state and
        period_initialized_key not in st.session_state):
        
        if not trades_df.empty:
            min_date = trades_df['OpenDatetime'].min().date()
            max_date = trades_df['OpenDatetime'].max().date()
            default_start, default_end = calculate_preset_dates("30d", min_date, max_date)
            
            # Inizializza i widget per la PRIMA volta
            st.session_state[start_widget_key] = default_start
            st.session_state[end_widget_key] = default_end
            
            # IMPORTANTE: Marca che sono stati inizializzati ma non ancora toccati dall'utente
            st.session_state[period_initialized_key] = "auto_default"
    
    # Setup selections (questo può rimanere come prima)
    if not trades_df.empty:
        for magic_number in trades_df['MagicNumber'].unique():
            setup_key = f"setup_{account_id}_{magic_number}"
            if setup_key not in st.session_state:
                st.session_state[setup_key] = DEFAULTS["setup_selected"]


def mark_period_as_user_modified(account_id: str):
    """
    Marca che l'utente ha modificato manualmente il periodo.
    Questo previene reset automatici futuri.
    """
    period_initialized_key = f"period_user_set_{account_id}"
    st.session_state[period_initialized_key] = "user_modified"


def get_sidebar_width(account_id: str) -> int:
    """
    Ottiene la larghezza della sidebar per un account, con validazione.
    
    Args:
        account_id: ID dell'account
        
    Returns:
        Larghezza sidebar validata
    """
    width_key = get_session_key("sidebar_width", account_id)
    width = st.session_state.get(width_key, DEFAULTS["sidebar_width"])
    return validate_sidebar_width(width)


def set_sidebar_width(account_id: str, width: int) -> bool:
    """
    Imposta la larghezza della sidebar per un account.
    
    Args:
        account_id: ID dell'account
        width: Nuova larghezza (verrà validata)
        
    Returns:
        True se l'impostazione è riuscita
    """
    validated_width = validate_sidebar_width(width)
    width_key = get_session_key("sidebar_width", account_id)
    st.session_state[width_key] = validated_width
    return True


def update_period_preset(account_id: str, preset: str, 
                        min_date: date, max_date: date) -> bool:
    """
    Aggiorna il preset del periodo e calcola le date corrispondenti.
    
    Args:
        account_id: ID dell'account
        preset: Tipo di preset (7d, 30d, 90d, ytd)
        min_date: Data minima disponibile
        max_date: Data massima disponibile
        
    Returns:
        True se l'aggiornamento è riuscito
    """
    preset_key = get_session_key("period_preset", account_id)
    start_date_key = get_session_key("period_start", account_id)
    end_date_key = get_session_key("period_end", account_id)
    
    # Aggiorna preset
    st.session_state[preset_key] = preset
    
    # Calcola e aggiorna date
    start_date, end_date = calculate_preset_dates(preset, min_date, max_date)
    st.session_state[start_date_key] = start_date
    st.session_state[end_date_key] = end_date
    
    return True


def toggle_all_setups(account_id: str, magic_numbers: List[int], 
                     select_all: bool = True) -> int:
    """
    Seleziona o deseleziona tutti i setup per un account.
    
    Args:
        account_id: ID dell'account
        magic_numbers: Lista di magic numbers disponibili
        select_all: True per selezionare tutti, False per deselezionare
        
    Returns:
        Numero di setup modificati
    """
    modified_count = 0
    
    for magic_number in magic_numbers:
        setup_key = f"setup_{account_id}_{magic_number}"
        if setup_key in st.session_state:
            st.session_state[setup_key] = select_all
            modified_count += 1
    
    return modified_count


def invert_setup_selection(account_id: str, magic_numbers: List[int]) -> int:
    """
    Inverte la selezione di tutti i setup per un account.
    
    Args:
        account_id: ID dell'account
        magic_numbers: Lista di magic numbers disponibili
        
    Returns:
        Numero di setup modificati
    """
    modified_count = 0
    
    for magic_number in magic_numbers:
        setup_key = f"setup_{account_id}_{magic_number}"
        if setup_key in st.session_state:
            current_value = st.session_state[setup_key]
            st.session_state[setup_key] = not current_value
            modified_count += 1
    
    return modified_count


def get_setup_search_term(account_id: str) -> str:
    """
    Ottiene il termine di ricerca per i setup.
    
    Args:
        account_id: ID dell'account
        
    Returns:
        Termine di ricerca attuale
    """
    search_key = get_session_key("setup_search", account_id)
    return st.session_state.get(search_key, "")


def validate_date_range(start_date: date, end_date: date) -> Tuple[bool, str]:
    """
    Valida un range di date.
    
    Args:
        start_date: Data di inizio
        end_date: Data di fine
        
    Returns:
        Tupla (is_valid, error_message)
    """
    if start_date > end_date:
        return False, "Data inizio deve essere ≤ data fine"
    
    # Verifica che il range non sia troppo grande (es. > 2 anni)
    max_days = 730  # 2 anni
    if (end_date - start_date).days > max_days:
        return False, f"Range massimo consentito: {max_days} giorni"
    
    return True, ""


def get_filter_summary(account_id: str) -> str:
    """
    Ottiene un riassunto testuale dei filtri attivi.
    
    Args:
        account_id: ID dell'account
        
    Returns:
        String con riassunto filtri
    """
    filters = get_advanced_filters(account_id)
    period_config = get_period_configuration(account_id)
    selected_setups = get_selected_setups(account_id)
    
    summary_parts = []
    
    # Periodo
    if period_config:
        days = (period_config['end_date'] - period_config['start_date']).days
        summary_parts.append(f"Periodo: {days} giorni")
    
    # Setup
    if selected_setups:
        summary_parts.append(f"Setup: {len(selected_setups)} selezionati")
    
    # Tipo trade
    if filters['trade_type'] != "Tutti":
        summary_parts.append(f"Tipo: {filters['trade_type']}")
    
    # Filtri numerici
    if filters['min_profit'] is not None:
        summary_parts.append(f"Min Profit: €{filters['min_profit']}")
    
    if filters['max_drawdown'] is not None:
        summary_parts.append(f"Max DD: €{filters['max_drawdown']}")
    
    # Simboli
    if filters['selected_symbols']:
        symbol_count = len(filters['selected_symbols'])
        summary_parts.append(f"Simboli: {symbol_count}")
    
    return " | ".join(summary_parts) if summary_parts else "Nessun filtro attivo"


def clear_account_session_state(account_id: str) -> int:
    """
    Pulisce tutti i dati di session state per un account specifico.
    
    Args:
        account_id: ID dell'account
        
    Returns:
        Numero di chiavi rimosse
    """
    keys_to_remove = []
    
    # Trova tutte le chiavi che contengono l'account_id
    for key in st.session_state.keys():
        if account_id in key:
            keys_to_remove.append(key)
    
    # Rimuovi le chiavi
    for key in keys_to_remove:
        del st.session_state[key]
    
    return len(keys_to_remove)


def export_session_config(account_id: str) -> Dict[str, Any]:
    """
    Esporta la configurazione di session state per un account.
    
    Args:
        account_id: ID dell'account
        
    Returns:
        Dict con configurazione esportabile
    """
    config = {
        'account_id': account_id,
        'export_timestamp': datetime.now().isoformat(),
        'sidebar_width': get_sidebar_width(account_id),
        'period_config': get_period_configuration(account_id),
        'selected_setups': get_selected_setups(account_id),
        'advanced_filters': get_advanced_filters(account_id),
        'search_term': get_setup_search_term(account_id)
    }
    
    return config


def import_session_config(account_id: str, config: Dict[str, Any]) -> bool:
    """
    Importa una configurazione di session state per un account.
    
    Args:
        account_id: ID dell'account
        config: Dict con configurazione da importare
        
    Returns:
        True se l'importazione è riuscita
    """
    try:
        # Sidebar width
        if 'sidebar_width' in config:
            set_sidebar_width(account_id, config['sidebar_width'])
        
        # Period config
        if 'period_config' in config and config['period_config']:
            period_config = config['period_config']
            start_date_key = get_session_key("period_start", account_id)
            end_date_key = get_session_key("period_end", account_id)
            
            st.session_state[start_date_key] = period_config['start_date']
            st.session_state[end_date_key] = period_config['end_date']
        
        # Setup selections
        if 'selected_setups' in config:
            # Prima deseleziona tutti
            for key in st.session_state.keys():
                if key.startswith(f"setup_{account_id}_"):
                    st.session_state[key] = False
            
            # Poi seleziona quelli specificati
            for magic_number in config['selected_setups']:
                setup_key = f"setup_{account_id}_{magic_number}"
                st.session_state[setup_key] = True
        
        # Advanced filters
        if 'advanced_filters' in config:
            filters = config['advanced_filters']
            
            if 'trade_type' in filters:
                filter_key = get_session_key("trade_type_filter", account_id)
                st.session_state[filter_key] = filters['trade_type']
            
            if 'min_profit' in filters:
                filter_key = get_session_key("min_profit_filter", account_id)
                st.session_state[filter_key] = filters['min_profit']
            
            if 'max_drawdown' in filters:
                filter_key = get_session_key("max_dd_filter", account_id)
                st.session_state[filter_key] = filters['max_drawdown']
            
            if 'selected_symbols' in filters:
                filter_key = get_session_key("symbols_filter", account_id)
                st.session_state[filter_key] = filters['selected_symbols']
        
        return True
        
    except Exception as e:
        st.error(f"Errore nell'importazione configurazione: {str(e)}")
        return False
    
def cleanup_large_session_objects(account_id: str, max_objects: int = 50):
    """
    Pulisce oggetti di sessione troppo grandi o vecchi.
    
    Args:
        account_id: Account identifier
        max_objects: Numero massimo oggetti per account
    """
    account_keys = [k for k in st.session_state.keys() if account_id in k]
    
    # Rimuovi oggetti più vecchi se troppi
    if len(account_keys) > max_objects:
        # Ordina per timestamp se disponibile, altrimenti per nome
        sorted_keys = sorted(account_keys)
        keys_to_remove = sorted_keys[:-max_objects]
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        st.info(f"🧹 Puliti {len(keys_to_remove)} oggetti sessione obsoleti")

# Chiamare questa funzione in render() main