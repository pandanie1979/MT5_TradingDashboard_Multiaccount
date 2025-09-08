# data/margin_debugger.py
"""
Modulo dedicato al debug e analisi dei dati di margine per identificare
l'origine del "piedistallo" di margine che rimane > 0 anche senza posizioni.

Questo modulo analizza i dati raw dei trade per verificare:
1. Coerenza dei valori MarginAtOpen/MarginAtClose
2. Sequenza corretta degli eventi di margine
3. Identificazione di anomalie nei dati
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class MarginDebugger:
    """
    Classe principale per il debug dei dati di margine.
    Analizza i trade raw per identificare problemi nel calcolo del margine timeline.
    """
    
    def __init__(self, trades_df: pd.DataFrame):
        """
        Inizializza il debugger con i dati dei trade.
        
        Args:
            trades_df: DataFrame con i dati dei trade (deve contenere colonne di margine)
        """
        self.trades_df = trades_df.copy() if not trades_df.empty else pd.DataFrame()
        self.margin_events = []
        self.anomalies = []
        self.debug_timeline = pd.DataFrame()
        
    def analyze_margin_data(self) -> Dict:
        """
        Esegue analisi completa dei dati di margine.
        
        Returns:
            Dict con risultati dell'analisi: eventi, anomalie, statistiche
        """
        if self.trades_df.empty:
            return {"error": "Nessun dato disponibile per l'analisi"}
        
        # 1. Estrai e analizza eventi di margine
        self._extract_margin_events()
        
        # 2. Costruisci timeline dettagliata
        self._build_debug_timeline()
        
        # 3. Identifica anomalie
        self._detect_anomalies()
        
        # 4. Calcola statistiche di debug
        stats = self._calculate_debug_statistics()
        
        return {
            "margin_events": self.margin_events,
            "debug_timeline": self.debug_timeline,
            "anomalies": self.anomalies,
            "statistics": stats,
            "raw_data_info": self._get_raw_data_info()
        }
    
    def _extract_margin_events(self):
        """
        Estrae tutti gli eventi di margine dai dati raw in ordine cronologico.
        Ogni riga del CSV rappresenta un evento (apertura o chiusura parziale/totale).
        """
        self.margin_events = []
        
        for idx, trade in self.trades_df.iterrows():
            # Evento di apertura (basato su OpenDatetime)
            open_event = {
                'event_id': f"open_{trade['OpenPositionTicket']}_{idx}",
                'timestamp': trade['OpenDatetime'],
                'ticket': trade['OpenPositionTicket'],
                'event_type': 'OPEN',
                'margin_at_open': trade.get('MarginAtOpen', 0),
                'margin_at_close': None,
                'position_size': trade.get('OpenPositionSize', 0),
                'symbol': trade.get('Symbol', 'Unknown'),
                'magic_number': trade.get('MagicNumber', 'Unknown'),
                'row_index': idx,
                'pl': trade.get('PL', 0)
            }
            self.margin_events.append(open_event)
            
            # Evento di chiusura (se disponibile CloseDatetime)
            if 'CloseDatetime' in trade and pd.notna(trade['CloseDatetime']):
                close_event = {
                    'event_id': f"close_{trade['OpenPositionTicket']}_{idx}",
                    'timestamp': pd.to_datetime(trade['CloseDatetime']),
                    'ticket': trade['OpenPositionTicket'],
                    'event_type': 'CLOSE',
                    'margin_at_open': None,
                    'margin_at_close': trade.get('MarginAtClose', 0),
                    'position_size': trade.get('ClosePositionSize', 0),
                    'symbol': trade.get('Symbol', 'Unknown'),
                    'magic_number': trade.get('MagicNumber', 'Unknown'),
                    'row_index': idx,
                    'pl': trade.get('PL', 0)
                }
                self.margin_events.append(close_event)
        
        # Ordina eventi per timestamp
        self.margin_events.sort(key=lambda x: x['timestamp'])
    
    def _build_debug_timeline(self):
        """
        Costruisce una timeline dettagliata che mostra l'evoluzione del margine
        step-by-step per ogni evento, tracciando le posizioni aperte.
        """
        timeline_data = []
        open_positions = {}  # ticket -> {margin, size, symbol, magic}
        
        for event in self.margin_events:
            if event['event_type'] == 'OPEN':
                # Apertura posizione
                ticket = event['ticket']
                margin_value = event['margin_at_open']
                
                open_positions[ticket] = {
                    'margin': margin_value,
                    'size': event['position_size'],
                    'symbol': event['symbol'],
                    'magic': event['magic_number'],
                    'open_time': event['timestamp']
                }
                
                # Calcola margine totale
                total_margin = sum(pos['margin'] for pos in open_positions.values())
                
                timeline_data.append({
                    'timestamp': event['timestamp'],
                    'event_type': 'OPEN',
                    'ticket': ticket,
                    'event_margin': margin_value,
                    'total_margin_calculated': total_margin,
                    'open_positions_count': len(open_positions),
                    'open_tickets': list(open_positions.keys()),
                    'position_details': dict(open_positions),
                    'event_id': event['event_id'],
                    'row_index': event['row_index']
                })
                
            elif event['event_type'] == 'CLOSE':
                # Chiusura posizione (parziale o totale)
                ticket = event['ticket']
                margin_after_close = event['margin_at_close']
                
                if ticket in open_positions:
                    if margin_after_close == 0:
                        # Chiusura completa
                        removed_position = open_positions.pop(ticket, None)
                        event_description = f"CLOSE_COMPLETE"
                    else:
                        # Chiusura parziale - aggiorna margine residuo
                        open_positions[ticket]['margin'] = margin_after_close
                        event_description = f"CLOSE_PARTIAL"
                else:
                    # ANOMALIA: Tentativo di chiudere posizione non aperta
                    event_description = f"CLOSE_ERROR_NOT_FOUND"
                
                # Calcola margine totale dopo chiusura
                total_margin = sum(pos['margin'] for pos in open_positions.values())
                
                timeline_data.append({
                    'timestamp': event['timestamp'],
                    'event_type': event_description,
                    'ticket': ticket,
                    'event_margin': margin_after_close,
                    'total_margin_calculated': total_margin,
                    'open_positions_count': len(open_positions),
                    'open_tickets': list(open_positions.keys()),
                    'position_details': dict(open_positions),
                    'event_id': event['event_id'],
                    'row_index': event['row_index']
                })
        
        self.debug_timeline = pd.DataFrame(timeline_data)
    
    def _detect_anomalies(self):
        """
        Identifica anomalie nei dati di margine che potrebbero causare
        il "piedistallo" di margine sempre > 0.
        """
        self.anomalies = []
        
        # ANOMALIA 1: Margine finale non zero senza posizioni aperte
        if not self.debug_timeline.empty:
            final_state = self.debug_timeline.iloc[-1]
            if final_state['total_margin_calculated'] > 0 and final_state['open_positions_count'] == 0:
                self.anomalies.append({
                    'type': 'FINAL_MARGIN_WITHOUT_POSITIONS',
                    'severity': 'HIGH',
                    'description': f"Margine finale {final_state['total_margin_calculated']:.2f} > 0 ma 0 posizioni aperte",
                    'timestamp': final_state['timestamp'],
                    'details': final_state
                })
        
        # ANOMALIA 2: MarginAtClose > 0 ma posizione considerata chiusa
        margin_close_anomalies = []
        for event in self.margin_events:
            if (event['event_type'] == 'CLOSE' and 
                event['margin_at_close'] is not None and 
                event['margin_at_close'] > 0):
                # Verifica se questa è davvero una chiusura completa
                margin_close_anomalies.append({
                    'ticket': event['ticket'],
                    'margin_at_close': event['margin_at_close'],
                    'timestamp': event['timestamp'],
                    'row_index': event['row_index']
                })
        
        if margin_close_anomalies:
            self.anomalies.append({
                'type': 'MARGIN_AT_CLOSE_NON_ZERO',
                'severity': 'MEDIUM',
                'description': f"Trovate {len(margin_close_anomalies)} chiusure con MarginAtClose > 0",
                'details': margin_close_anomalies
            })
        
        # ANOMALIA 3: Posizioni mai chiuse (solo apertura senza chiusura)
        opened_tickets = {event['ticket'] for event in self.margin_events if event['event_type'] == 'OPEN'}
        closed_tickets = {event['ticket'] for event in self.margin_events if event['event_type'] == 'CLOSE'}
        never_closed = opened_tickets - closed_tickets
        
        if never_closed:
            self.anomalies.append({
                'type': 'POSITIONS_NEVER_CLOSED',
                'severity': 'HIGH',
                'description': f"Trovate {len(never_closed)} posizioni mai chiuse",
                'details': list(never_closed)
            })
        
        # ANOMALIA 4: Valori di margine inconsistenti
        margin_inconsistencies = []
        for event in self.margin_events:
            margin_value = event.get('margin_at_open') or event.get('margin_at_close', 0)
            if margin_value < 0:
                margin_inconsistencies.append({
                    'event_id': event['event_id'],
                    'margin_value': margin_value,
                    'issue': 'NEGATIVE_MARGIN'
                })
        
        if margin_inconsistencies:
            self.anomalies.append({
                'type': 'INVALID_MARGIN_VALUES',
                'severity': 'MEDIUM',
                'description': f"Trovati {len(margin_inconsistencies)} valori di margine invalidi",
                'details': margin_inconsistencies
            })
        
        # NUOVA ANOMALIA 5: Posizioni incompletamente chiuse - per debug EA
        incomplete_closures = self._detect_incomplete_closures()
        if incomplete_closures:
            self.anomalies.append({
                'type': 'INCOMPLETE_POSITION_CLOSURES',
                'severity': 'HIGH',
                'description': f"Trovate {len(incomplete_closures)} posizioni non completamente chiuse",
                'details': incomplete_closures
            })
    
    def _detect_incomplete_closures(self):
        """
        Identifica posizioni dove la somma dei ClosePositionSize != OpenPositionSize
        o dove non esiste una riga con MarginAtClose = 0.
        
        Returns:
            Lista di posizioni problematiche con dettagli temporali
        """
        incomplete_positions = []
        
        # Raggruppa per ticket per analizzare ogni posizione
        for ticket, ticket_trades in self.trades_df.groupby('OpenPositionTicket'):
            
            # Dati della posizione
            open_size = ticket_trades['OpenPositionSize'].iloc[0]  # Stesso per tutte le righe del ticket
            close_sizes = ticket_trades['ClosePositionSize'].dropna()
            margin_at_close_values = ticket_trades['MarginAtClose'].dropna()
            
            # Test 1: Somma ClosePositionSize != OpenPositionSize
            total_closed_size = close_sizes.sum() if not close_sizes.empty else 0
            size_mismatch = abs(total_closed_size - open_size) > 0.001  # Tolleranza per errori float
            
            # Test 2: Nessuna riga con MarginAtClose = 0
            no_zero_margin = not any(margin_at_close_values == 0) if not margin_at_close_values.empty else True
            
            # Se c'è un problema, raccoglie dettagli
            if size_mismatch or no_zero_margin:
                
                # Trova tutte le date di chiusura per questa posizione
                close_datetimes = ticket_trades['CloseDatetime'].dropna().sort_values()
                open_datetime = ticket_trades['OpenDatetime'].iloc[0]
                
                # Cronologia delle chiusure
                closure_history = []
                for idx, trade in ticket_trades.iterrows():
                    if pd.notna(trade.get('CloseDatetime')):
                        closure_history.append({
                            'close_datetime': trade['CloseDatetime'],
                            'close_size': trade.get('ClosePositionSize', 0),
                            'margin_at_close': trade.get('MarginAtClose', 0),
                            'pl': trade.get('PL', 0),
                            'row_index': idx
                        })
                
                # Ultima chiusura registrata
                last_closure = max(closure_history, key=lambda x: x['close_datetime']) if closure_history else None
                
                incomplete_positions.append({
                    'ticket': ticket,
                    'open_datetime': open_datetime,
                    'open_size': open_size,
                    'total_closed_size': total_closed_size,
                    'size_mismatch': size_mismatch,
                    'size_difference': total_closed_size - open_size,
                    'no_zero_margin': no_zero_margin,
                    'last_closure_datetime': last_closure['close_datetime'] if last_closure else None,
                    'last_margin_at_close': last_closure['margin_at_close'] if last_closure else None,
                    'closure_count': len(closure_history),
                    'closure_history': closure_history,
                    'problem_type': self._classify_closure_problem(size_mismatch, no_zero_margin, total_closed_size, open_size),
                    'symbol': ticket_trades['Symbol'].iloc[0] if 'Symbol' in ticket_trades.columns else 'Unknown',
                    'magic_number': ticket_trades['MagicNumber'].iloc[0] if 'MagicNumber' in ticket_trades.columns else 'Unknown'
                })
        
        # Ordina per data dell'ultima chiusura per analisi temporale
        incomplete_positions.sort(key=lambda x: x['last_closure_datetime'] or x['open_datetime'])
        
        return incomplete_positions
    
    def _classify_closure_problem(self, size_mismatch, no_zero_margin, total_closed, open_size):
        """
        Classifica il tipo di problema di chiusura per facilitare il debug EA.
        """
        if size_mismatch and no_zero_margin:
            if total_closed < open_size:
                return "PARTIAL_CLOSURE_INCOMPLETE"  # Chiusura parziale mai completata
            else:
                return "OVER_CLOSURE_NO_ZERO"  # Chiuso più del dovuto senza MarginAtClose=0
        elif size_mismatch:
            if total_closed < open_size:
                return "UNDER_CLOSURE"  # Chiuso meno del volume originale
            else:
                return "OVER_CLOSURE"  # Chiuso più del volume originale
        elif no_zero_margin:
            return "NO_FINAL_ZERO_MARGIN"  # Mai marcato come completamente chiuso
        else:
            return "UNKNOWN_PROBLEM"
    
    def _calculate_debug_statistics(self) -> Dict:
        """
        Calcola statistiche utili per il debug.
        """
        if self.trades_df.empty:
            return {}
        
        stats = {
            'total_rows': len(self.trades_df),
            'total_events': len(self.margin_events),
            'unique_tickets': self.trades_df['OpenPositionTicket'].nunique(),
            'date_range': {
                'start': self.trades_df['OpenDatetime'].min(),
                'end': self.trades_df['OpenDatetime'].max()
            }
        }
        
        # Statistiche margine
        margin_at_open_values = [e['margin_at_open'] for e in self.margin_events 
                                if e['margin_at_open'] is not None]
        margin_at_close_values = [e['margin_at_close'] for e in self.margin_events 
                                 if e['margin_at_close'] is not None]
        
        if margin_at_open_values:
            stats['margin_at_open'] = {
                'min': min(margin_at_open_values),
                'max': max(margin_at_open_values),
                'avg': sum(margin_at_open_values) / len(margin_at_open_values),
                'count': len(margin_at_open_values)
            }
        
        if margin_at_close_values:
            stats['margin_at_close'] = {
                'min': min(margin_at_close_values),
                'max': max(margin_at_close_values),
                'avg': sum(margin_at_close_values) / len(margin_at_close_values),
                'count': len(margin_at_close_values),
                'zero_count': sum(1 for v in margin_at_close_values if v == 0),
                'non_zero_count': sum(1 for v in margin_at_close_values if v > 0)
            }
        
        # Timeline statistics
        if not self.debug_timeline.empty:
            stats['timeline'] = {
                'final_margin': self.debug_timeline['total_margin_calculated'].iloc[-1],
                'max_margin': self.debug_timeline['total_margin_calculated'].max(),
                'max_positions': self.debug_timeline['open_positions_count'].max(),
                'final_positions': self.debug_timeline['open_positions_count'].iloc[-1]
            }
        
        return stats
    
    def _get_raw_data_info(self) -> Dict:
        """
        Informazioni sui dati raw per verificare completezza.
        """
        if self.trades_df.empty:
            return {}
        
        columns_available = list(self.trades_df.columns)
        margin_columns = [col for col in columns_available if 'margin' in col.lower()]
        
        return {
            'total_columns': len(columns_available),
            'margin_related_columns': margin_columns,
            'has_margin_at_open': 'MarginAtOpen' in columns_available,
            'has_margin_at_close': 'MarginAtClose' in columns_available,
            'has_close_datetime': 'CloseDatetime' in columns_available,
            'sample_data': self.trades_df.head(3).to_dict('records') if len(self.trades_df) > 0 else []
        }

def run_margin_debug_analysis(trades_df: pd.DataFrame) -> Dict:
    """
    Funzione helper per eseguire l'analisi completa di debug del margine.
    
    Args:
        trades_df: DataFrame con i dati dei trade
        
    Returns:
        Dict con risultati completi dell'analisi
    """
    debugger = MarginDebugger(trades_df)
    return debugger.analyze_margin_data()

def get_margin_timeline_comparison(trades_df: pd.DataFrame, 
                                 current_timeline: pd.DataFrame) -> Dict:
    """
    Confronta il margin timeline attuale con quello calcolato dal debugger
    per identificare differenze.
    
    Args:
        trades_df: DataFrame con i dati dei trade
        current_timeline: Timeline del margine attualmente calcolato
        
    Returns:
        Dict con confronto dettagliato
    """
    debug_results = run_margin_debug_analysis(trades_df)
    debug_timeline = debug_results.get('debug_timeline', pd.DataFrame())
    
    if debug_timeline.empty or current_timeline.empty:
        return {"error": "Timeline vuote, confronto impossibile"}
    
    # Confronta i valori finali
    debug_final = debug_timeline['total_margin_calculated'].iloc[-1]
    current_final = current_timeline['total_margin'].iloc[-1]
    
    comparison = {
        'debug_final_margin': debug_final,
        'current_final_margin': current_final,
        'difference': abs(debug_final - current_final),
        'match': abs(debug_final - current_final) < 0.01,  # Tolleranza di 1 centesimo
        'debug_events_count': len(debug_timeline),
        'current_events_count': len(current_timeline)
    }
    
    return comparison