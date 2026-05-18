# MT5 Trading Dashboard - Data Processing Utilities
# File: tabs/performance/utils/data_processing.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Core data processing utilities for performance analysis.
Handles trade classification, margin timeline calculation, and equity curves.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

from ..config.constants import (
    BACKTEST_TICKET_THRESHOLD, 
    BACKTEST_FILENAME_PATTERN,
    DEBUG_CONFIG
)


def classify_trades_backtest_vs_live(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Classificazione DOPPIO CRITERIO per distinguere backtest da live trading:
    
    CRITERIO PRIMARIO - Ticket Number:
    - Ticket ≤ 10.000 = BACKTEST (progressivi da 1)
    - Ticket > 10.000 = LIVE (ticket broker reali a 9-10 cifre)
    
    CRITERIO SECONDARIO - Filename Pattern:
    - Filename con "_000000" = BACKTEST (ora inizio mezzanotte)
    - Filename senza "_000000" = LIVE
    
    Args:
        trades_df: DataFrame con i trade
        
    Returns:
        DataFrame con colonna 'trade_type' aggiunta ['backtest', 'live']
    """
    if trades_df.empty or 'OpenPositionTicket' not in trades_df.columns:
        trades_df = trades_df.copy()
        trades_df['trade_type'] = 'live'
        return trades_df
    
    trades_df = trades_df.copy()
    
    # CRITERIO PRIMARIO: Soglia ticket
    trades_df['trade_type'] = trades_df['OpenPositionTicket'].apply(
        lambda ticket: 'backtest' if ticket <= BACKTEST_TICKET_THRESHOLD else 'live'
    )
    
    # CRITERIO SECONDARIO: Filename pattern (se disponibile)
    if 'SourceFilename' in trades_df.columns:
        # Se il filename contiene _000000 = backtest
        filename_backtest_mask = trades_df['SourceFilename'].str.contains(
            BACKTEST_FILENAME_PATTERN, na=False
        )
        trades_df.loc[filename_backtest_mask, 'trade_type'] = 'backtest'
        
        # Se il filename NON contiene _000000 = live (ma solo se ticket è ambiguo)
        filename_live_mask = ~trades_df['SourceFilename'].str.contains(
            BACKTEST_FILENAME_PATTERN, na=False
        )
        # Applica solo se ticket è sopra soglia (evita conflitti)
        ambiguous_mask = trades_df['OpenPositionTicket'] > BACKTEST_TICKET_THRESHOLD
        trades_df.loc[filename_live_mask & ambiguous_mask, 'trade_type'] = 'live'
    
    # Statistiche per debug
    bt_count = len(trades_df[trades_df['trade_type'] == 'backtest'])
    live_count = len(trades_df[trades_df['trade_type'] == 'live'])
    
    # Range ticket per debug
    bt_tickets = trades_df[trades_df['trade_type'] == 'backtest']['OpenPositionTicket']
    live_tickets = trades_df[trades_df['trade_type'] == 'live']['OpenPositionTicket']
    
    # Analisi filename (se disponibile)
    filename_analysis = {}
    if 'SourceFilename' in trades_df.columns:
        filename_000000 = trades_df['SourceFilename'].str.contains(
            BACKTEST_FILENAME_PATTERN, na=False
        ).sum()
        filename_not_000000 = len(trades_df) - filename_000000
        
        filename_analysis = {
            'has_filename_column': True,
            'files_with_000000': filename_000000,
            'files_without_000000': filename_not_000000,
            'filename_examples': trades_df['SourceFilename'].unique()[:5].tolist()
        }
    else:
        filename_analysis = {
            'has_filename_column': False,
            'note': 'SourceFilename non disponibile - usando solo criterio ticket'
        }
    
    classification_summary = {
        'method': 'dual_criteria_ticket_and_filename',
        'primary_criterion': f'ticket_threshold_{BACKTEST_TICKET_THRESHOLD}',
        'secondary_criterion': f'filename_pattern{BACKTEST_FILENAME_PATTERN}',
        'total_trades': len(trades_df),
        'backtest_count': bt_count,
        'live_count': live_count,
        'backtest_ticket_range': f"{bt_tickets.min()}-{bt_tickets.max()}" if len(bt_tickets) > 0 else "N/A",
        'live_ticket_range': f"{live_tickets.min()}-{live_tickets.max()}" if len(live_tickets) > 0 else "N/A",
        'backtest_percentage': (bt_count / len(trades_df) * 100) if len(trades_df) > 0 else 0,
        'filename_analysis': filename_analysis
    }
    
    # Salva summary per debug
    trades_df.attrs['classification_summary'] = classification_summary
    
    return trades_df


def calculate_margin_timeline(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Timeline margine con correzione SEMPLICE timestamp invertiti.
    
    REGOLA SEMPLICE: Se CloseDatetime < OpenDatetime, 
    forza CloseDatetime = OpenDatetime + 1 millisecondo
    
    Fix per issue: MT5 Strategy Tester genera timestamp invertiti 
    per eventi di slippage protection ultra-rapidi.
    
    Args:
        trades_df: DataFrame con i trade
        
    Returns:
        DataFrame con timeline del margine
    """
    if trades_df.empty:
        return pd.DataFrame()
    
    all_events = []
    timestamp_corrections = []
    
    # Processa ogni trade unico
    for ticket, group in trades_df.groupby('OpenPositionTicket'):
        
        # Ordina per CloseDatetime
        if 'CloseDatetime' in group.columns:
            has_close = group['CloseDatetime'].notna()
            closes = group[has_close].sort_values('CloseDatetime')
        else:
            closes = group.sort_index()
        
        if closes.empty:
            continue
        
        # Evento apertura
        first_row = closes.iloc[0]
        open_datetime = pd.to_datetime(first_row['OpenDatetime'])
        margin_at_open = first_row.get('MarginAtOpen', 0)
        
        all_events.append({
            'datetime': open_datetime,
            'ticket': ticket,
            'type': 'open',
            'margin_after': margin_at_open,
            'priority': 0,
            'description': f'OPEN_{ticket}'
        })
        
        # Eventi chiusura con correzione timestamp
        for idx, row in closes.iterrows():
            original_close = row['CloseDatetime']
            close_datetime = pd.to_datetime(original_close)
            
            # CORREZIONE SEMPLICE: Timestamp invertiti
            if close_datetime < open_datetime:
                corrected_close = open_datetime + pd.Timedelta(milliseconds=1)
                
                timestamp_corrections.append({
                    'ticket': ticket,
                    'original_open': first_row['OpenDatetime'],
                    'original_close': original_close,
                    'corrected_close': corrected_close.strftime('%Y.%m.%d %H:%M:%S.%f')[:-3],
                    'time_diff_original': (close_datetime - open_datetime).total_seconds(),
                    'exit_reason': row.get('ExitReason', 'Unknown')
                })
                
                close_datetime = corrected_close
            
            margin_at_close = row.get('MarginAtClose', 0)
            exit_reason = row.get('ExitReason', 'Unknown')
            
            # Priorità eventi
            priority = 1 if exit_reason == 'Partial Close' else 2
            
            all_events.append({
                'datetime': close_datetime,
                'ticket': ticket,
                'type': 'close',
                'margin_after': margin_at_close,
                'priority': priority,
                'exit_reason': exit_reason,
                'description': f'CLOSE_{ticket}_{exit_reason}'
            })
    
    # Ordinamento eventi
    events_df = pd.DataFrame(all_events)
    events_df = events_df.sort_values(['datetime', 'priority', 'ticket'])
    
    # Processing timeline standard
    open_positions = {}
    timeline = []
    
    for _, event in events_df.iterrows():
        ticket = event['ticket']
        event_type = event['type']
        margin_after = event['margin_after']
        
        if event_type == 'open':
            open_positions[ticket] = margin_after
            action = f"OPEN {ticket}: margin={margin_after}"
            
        elif event_type == 'close':
            if margin_after == 0:
                open_positions.pop(ticket, None)
                action = f"CLOSE_FINAL {ticket}: removed"
            else:
                open_positions[ticket] = margin_after
                action = f"CLOSE_PARTIAL {ticket}: margin={margin_after}"
        
        total_margin = sum(open_positions.values())
        
        timeline.append({
            'timestamp': event['datetime'],
            'total_margin': total_margin,
            'open_positions': len(open_positions),
            'action': action,
            'description': event['description']
        })
    
    # Risultati finali
    final_margin = timeline[-1]['total_margin'] if timeline else 0
    final_positions = timeline[-1]['open_positions'] if timeline else 0
    
    # Crea DataFrame finale
    result_df = pd.DataFrame(timeline) if timeline else pd.DataFrame()
    result_df.attrs['timestamp_corrections'] = timestamp_corrections
    result_df.attrs['corrections_count'] = len(timestamp_corrections)
    result_df.attrs['final_margin'] = final_margin
    result_df.attrs['final_positions'] = final_positions
    result_df.attrs['fix_version'] = DEBUG_CONFIG['margin_timeline_fix_version']
    
    return result_df


def create_continuous_equity_curve(trades_df: pd.DataFrame, 
                                 date_col: str = 'PlotDate', 
                                 multi_mn: bool = False) -> pd.DataFrame:
    """
    Crea equity curve continua SENZA interruzioni per colori.
    PRIORITÀ: Mantenere continuità matematica perfetta.
    
    Args:
        trades_df: DataFrame con i trade
        date_col: Nome colonna date per plot
        multi_mn: Se True, calcola info settimanali per colori
    
    Returns:
        DataFrame con equity curve continua + info per colori overlay
    """
    if trades_df.empty:
        return pd.DataFrame()
    
    # Ordina per data e RESET INDEX per partire da zero
    equity_data = trades_df.sort_values(date_col).reset_index(drop=True).copy()
    
    # IMPORTANTE: Equity cumulativa continua - SEMPRE da zero
    equity_data['Cumulative_PL'] = equity_data['PL'].cumsum()
    equity_data['Running_Peak'] = equity_data['Cumulative_PL'].cummax()
    equity_data['Drawdown'] = equity_data['Cumulative_PL'] - equity_data['Running_Peak']
    
    # Aggiungi info per colori SENZA interrompere la continuità 
    if multi_mn and 'trade_type' in equity_data.columns:
        # Analisi settimanale per multi-MN
        equity_data = calculate_weekly_trade_composition(equity_data, date_col)
    elif 'trade_type' in equity_data.columns:
        # Info base per singolo MN
        equity_data['live_ratio'] = equity_data['trade_type'].apply(
            lambda x: 0.0 if x == 'backtest' else 1.0
        )
        equity_data['week_type'] = equity_data['trade_type']
        equity_data['dynamic_color'] = equity_data['trade_type'].apply(
            lambda x: '#cccccc' if x == 'backtest' else '#1f77b4'
        )
    else:
        # Default per compatibilità 
        equity_data['live_ratio'] = 1.0
        equity_data['week_type'] = 'live'
        equity_data['dynamic_color'] = '#1f77b4'
    
    return equity_data


def calculate_weekly_trade_composition(equity_data: pd.DataFrame, 
                                     date_col: str = 'PlotDate') -> pd.DataFrame:
    """
    Calcola la composizione backtest/live per finestre temporali settimanali.
    
    Args:
        equity_data: DataFrame con trade e trade_type
        date_col: Nome colonna con le date
    
    Returns:
        DataFrame con analisi settimanale e colori dinamici
    """
    if equity_data.empty or 'trade_type' not in equity_data.columns:
        return equity_data
    
    # Crea copia e aggiungi week info
    weekly_data = equity_data.copy()
    weekly_data[date_col] = pd.to_datetime(weekly_data[date_col])
    weekly_data['week'] = weekly_data[date_col].dt.isocalendar().week
    weekly_data['year'] = weekly_data[date_col].dt.year
    weekly_data['year_week'] = weekly_data['year'].astype(str) + '_W' + weekly_data['week'].astype(str)
    
    # Calcola composizione per settimana
    weekly_composition = []
    
    for year_week in weekly_data['year_week'].unique():
        week_trades = weekly_data[weekly_data['year_week'] == year_week]
        
        backtest_count = len(week_trades[week_trades['trade_type'] == 'backtest'])
        live_count = len(week_trades[week_trades['trade_type'] == 'live'])
        total_count = len(week_trades)
        
        if total_count > 0:
            live_ratio = live_count / total_count
            backtest_ratio = backtest_count / total_count
            
            # Calcola colore dinamico basato su ratio
            color = calculate_dynamic_color(live_ratio)
            
            # Determina tipo settimana
            if live_ratio == 1.0:
                week_type = 'pure_live'
            elif live_ratio == 0.0:
                week_type = 'pure_backtest'
            else:
                week_type = 'mixed'
            
            weekly_composition.append({
                'year_week': year_week,
                'live_ratio': live_ratio,
                'backtest_ratio': backtest_ratio,
                'live_count': live_count,
                'backtest_count': backtest_count,
                'total_count': total_count,
                'week_type': week_type,
                'dynamic_color': color
            })
    
    # Merge back con i dati originali
    composition_df = pd.DataFrame(weekly_composition)
    weekly_data = weekly_data.merge(composition_df, on='year_week', how='left')
    
    return weekly_data


def calculate_dynamic_color(live_ratio: float) -> str:
    """
    Calcola colore dinamico basato sul rapporto live/backtest.
    
    Args:
        live_ratio: Ratio da 0.0 (solo backtest) a 1.0 (solo live)
    
    Returns:
        String con colore hex
    """
    # Colori base
    backtest_color = np.array([204, 204, 204])  # #cccccc (grigio)
    live_color = np.array([31, 119, 180])       # #1f77b4 (blu)
    
    # Interpolazione lineare tra i due colori
    interpolated = backtest_color + live_ratio * (live_color - backtest_color)
    
    # Converti a hex
    r, g, b = interpolated.astype(int)
    return f"#{r:02x}{g:02x}{b:02x}"


def debug_ticket_analysis(trades_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Debug per analizzare i pattern dei ticket number.
    
    Args:
        trades_df: DataFrame con i trade
        
    Returns:
        Dict con analisi dettagliata dei pattern ticket
    """
    if trades_df.empty or 'OpenPositionTicket' not in trades_df.columns:
        return {}
    
    tickets = sorted(trades_df['OpenPositionTicket'].unique())
    
    # Analisi statistica dei ticket
    analysis = {
        'total_unique_tickets': len(tickets),
        'min_ticket': min(tickets),
        'max_ticket': max(tickets),
        'ticket_range_span': max(tickets) - min(tickets),
        'ticket_digits': {
            '1-4_digits': len([t for t in tickets if t < 10000]),
            '5-6_digits': len([t for t in tickets if 10000 <= t < 1000000]), 
            '7-8_digits': len([t for t in tickets if 1000000 <= t < 100000000]),
            '9-10_digits': len([t for t in tickets if t >= 100000000])
        },
        'suggested_classification': {
            'backtest_tickets': len([t for t in tickets if t <= BACKTEST_TICKET_THRESHOLD]),
            'live_tickets': len([t for t in tickets if t > BACKTEST_TICKET_THRESHOLD])
        },
        'sample_tickets': {
            'first_10': tickets[:10],
            'last_10': tickets[-10:] if len(tickets) > 10 else tickets
        }
    }
    
    # Gap analysis per vedere se sono consecutivi (tipico backtest)
    if len(tickets) > 1:
        gaps = [tickets[i+1] - tickets[i] for i in range(len(tickets)-1)]
        analysis['gap_analysis'] = {
            'min_gap': min(gaps),
            'max_gap': max(gaps),
            'avg_gap': sum(gaps) / len(gaps),
            'gaps_equal_1': len([g for g in gaps if g == 1]),
            'consecutive_percentage': (len([g for g in gaps if g == 1]) / len(gaps) * 100) if gaps else 0
        }
    
    return analysis


def debug_classification_results(trades_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Debug helper per verificare i risultati della classificazione.
    
    Args:
        trades_df: DataFrame con colonna trade_type
        
    Returns:
        Dict con statistiche di classificazione
    """
    if 'trade_type' not in trades_df.columns:
        return {"error": "Colonna 'trade_type' mancante"}
    
    bt_count = len(trades_df[trades_df['trade_type'] == 'backtest'])
    live_count = len(trades_df[trades_df['trade_type'] == 'live'])
    
    # Analizza gruppi di ticket
    unique_tickets = sorted(trades_df['OpenPositionTicket'].unique())
    gaps = [unique_tickets[i+1] - unique_tickets[i] for i in range(len(unique_tickets)-1)]
    
    result = {
        'total_trades': len(trades_df),
        'backtest_count': bt_count,
        'live_count': live_count,
        'backtest_percentage': (bt_count / len(trades_df) * 100) if len(trades_df) > 0 else 0,
        'ticket_range': f"{min(unique_tickets)} - {max(unique_tickets)}",
        'max_gap': max(gaps) if gaps else 0,
        'avg_gap': sum(gaps) / len(gaps) if gaps else 0
    }
    
    return result


def render_timestamp_corrections_debug(timeline_df: pd.DataFrame):
    """
    Renderizza debug per correzioni timestamp (import Streamlit necessario dal chiamante).
    
    Args:
        timeline_df: DataFrame con timeline del margine
    """
    import streamlit as st
    
    corrections = timeline_df.attrs.get('timestamp_corrections', [])
    
    if corrections:
        st.warning(f"⚠️ **TIMESTAMP CORRECTIONS**: {len(corrections)} correzioni applicate")
        
        st.write("**Dettagli correzioni timestamp invertiti:**")
        
        corrections_df = pd.DataFrame(corrections)
        
        # Mostra tabella correzioni
        display_df = corrections_df[['ticket', 'original_open', 'original_close', 'corrected_close', 'time_diff_original', 'exit_reason']]
        display_df.columns = ['Ticket', 'OpenDatetime', 'CloseDatetime (Originale)', 'CloseDatetime (Corretta)', 'Diff Originale (sec)', 'ExitReason']
        
        st.dataframe(display_df, use_container_width=True)
        
        # Statistiche
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Correzioni Totali", len(corrections))
        
        with col2:
            avg_diff = sum(c['time_diff_original'] for c in corrections) / len(corrections)
            st.metric("Diff Media (sec)", f"{avg_diff:.3f}")
        
        with col3:
            exit_reasons = [c['exit_reason'] for c in corrections]
            most_common = max(set(exit_reasons), key=exit_reasons.count)
            st.metric("ExitReason Prevalente", most_common)
        
        # Download dettagli correzioni
        corrections_json = {
            'total_corrections': len(corrections),
            'corrections_detail': corrections,
            'analysis_timestamp': datetime.now().isoformat(),
            'fix_version': DEBUG_CONFIG['margin_timeline_fix_version']
        }
        
        st.download_button(
            label="📥 Download Dettagli Correzioni",
            data=str(corrections_json),
            file_name=f"timestamp_corrections_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
    
    else:
        st.success("✅ **TIMESTAMP OK**: Nessuna correzione necessaria")