# MT5 Trading Dashboard - Debug Tools Component
# File: tabs/performance/sidebar/debug_tools.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Debug tools panel for sidebar.
Provides data analysis, classification testing, and system diagnostics.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any

from ..utils.data_processing import (
    classify_trades_backtest_vs_live,
    debug_ticket_analysis,
    debug_classification_results,
    calculate_margin_timeline,
    render_timestamp_corrections_debug
)
from ..utils.session_helpers import clear_account_session_state, export_session_config
from ..utils.formatting import format_debug_info, create_info_box


def render_debug_tools_panel(trades_df: pd.DataFrame, account_id: str, account_path: str):
    """
    Render debug tools and data analysis utilities.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
        account_path: Path to MT5 data
    """
    st.markdown("**Strumenti Analisi:**")
    
    # Data Analysis Tools
    _render_data_analysis_tools(trades_df, account_id)
    
    st.markdown("---")
    
    # Classification Tools
    _render_classification_tools(trades_df, account_id)
    
    st.markdown("---")
    
    # System Tools
    _render_system_tools(trades_df, account_id, account_path)


def _render_data_analysis_tools(trades_df: pd.DataFrame, account_id: str):
    """
    Render data analysis tools section.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    st.markdown("**Analisi Dati:**")
    
    if st.button("📊 Analizza Dataset", key=f"analyze_data_{account_id}", width='stretch'):
        if not trades_df.empty:
            stats = _calculate_dataset_statistics(trades_df)
            
            st.markdown("**📈 Statistiche Dataset:**")
            st.write(f"- Righe totali: {stats['total_rows']:,}")
            st.write(f"- Trades unici: {stats['unique_trades']:,}")
            st.write(f"- Magic Numbers: {stats['magic_numbers']}")
            st.write(f"- Simboli: {stats['symbols']}")
            
            st.markdown("**📅 Range Temporale:**")
            st.write(f"- Dal: {stats['date_range']['start']}")
            st.write(f"- Al: {stats['date_range']['end']}")
            st.write(f"- Durata: {stats['date_range']['days']} giorni")
            
            # Performance overview
            if 'PL' in trades_df.columns:
                st.markdown("**💰 Performance Overview:**")
                st.write(f"- P&L Totale: €{stats['performance']['total_pl']:.2f}")
                st.write(f"- P&L Medio/Trade: €{stats['performance']['avg_pl_per_trade']:.2f}")
                st.write(f"- Win Rate: {stats['performance']['win_rate']:.1f}%")
        else:
            st.warning("Nessun dato disponibile per l'analisi")


def _render_classification_tools(trades_df: pd.DataFrame, account_id: str):
    """
    Render classification testing tools.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    st.markdown("**Test Classificazione:**")
    
    if st.button("🎯 Test Backtest/Live", key=f"test_classification_{account_id}", width='stretch'):
        if not trades_df.empty:
            classified = classify_trades_backtest_vs_live(trades_df)
            results = debug_classification_results(classified)
            
            st.markdown("**🏷️ Risultati Classificazione:**")
            st.write(f"- Backtest: {results['backtest_count']:,}")
            st.write(f"- Live: {results['live_count']:,}")
            st.write(f"- Ratio Backtest: {results['backtest_percentage']:.1f}%")
            st.write(f"- Range Ticket: {results['ticket_range']}")
            
            # Show ticket analysis
            ticket_analysis = debug_ticket_analysis(trades_df)
            if ticket_analysis:
                st.markdown("**🎟️ Analisi Ticket:**")
                st.write(f"- Gap Massimo: {ticket_analysis.get('gap_analysis', {}).get('max_gap', 0):,}")
                st.write(f"- Consecutivi: {ticket_analysis.get('gap_analysis', {}).get('consecutive_percentage', 0):.1f}%")
        else:
            st.warning("Nessun dato per classificazione")


def _render_system_tools(trades_df: pd.DataFrame, account_id: str, account_path: str):
    """
    Render system maintenance tools.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
        account_path: Path to MT5 data
    """
    st.markdown("**Strumenti Sistema:**")
    
    # Cache management
    if st.button("🗑️ Pulisci Cache", key=f"clear_cache_{account_id}", width='stretch'):
        st.cache_data.clear()
        st.success("✅ Cache pulita!")
    
    # Session state management
    if st.button("🔄 Reset Sessione", key=f"reset_session_{account_id}", width='stretch'):
        count = clear_account_session_state(account_id)
        st.success(f"✅ {count} chiavi di sessione rimosse!")
    
    # Configuration export
    if st.button("📦 Esporta Config", key=f"export_config_{account_id}", width='stretch'):
        config = export_session_config(account_id)
        st.download_button(
            label="📥 Download Configurazione",
            data=str(config),
            file_name=f"config_{account_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            key=f"download_config_{account_id}"
        )


def render_advanced_debug_analysis(trades_df: pd.DataFrame, account_id: str):
    """
    Render advanced debug analysis (used in expanded debug sections).
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    st.markdown("### 🔧 Analisi Debug Avanzata")
    
    if trades_df.empty:
        st.warning("Nessun dato disponibile")
        return
    
    # Margin timeline debug
    with st.expander("💰 Debug Margin Timeline"):
        _render_margin_timeline_debug(trades_df, account_id)
    
    # Timestamp corrections debug
    with st.expander("⏰ Debug Timestamp Corrections"):
        _render_timestamp_debug(trades_df, account_id)
    
    # File pattern analysis
    with st.expander("📁 Analisi Pattern File"):
        _render_file_pattern_analysis(trades_df, account_id)


def _render_margin_timeline_debug(trades_df: pd.DataFrame, account_id: str):
    """
    Render margin timeline debug analysis.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    if st.button(f"🔧 Test Margin Timeline", key=f"test_margin_{account_id}"):
        with st.spinner("Calcolando margin timeline..."):
            margin_timeline = calculate_margin_timeline(trades_df)
            
            if not margin_timeline.empty:
                final_margin = margin_timeline.attrs.get('final_margin', margin_timeline['total_margin'].iloc[-1])
                final_positions = margin_timeline.attrs.get('final_positions', margin_timeline['open_positions'].iloc[-1])
                corrections_count = margin_timeline.attrs.get('corrections_count', 0)
                max_margin = margin_timeline['total_margin'].max()
                
                # Show results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Margine Finale", f"€{final_margin:.2f}")
                
                with col2:
                    st.metric("Posizioni Finali", final_positions)
                
                with col3:
                    st.metric("Max Margine", f"€{max_margin:.2f}")
                
                # Check for issues
                if final_margin > 0 and final_positions == 0:
                    st.error("⚠️ Piedistallo di margine rilevato!")
                else:
                    st.success("✅ Timeline margine corretta")
                
                if corrections_count > 0:
                    st.warning(f"🔧 {corrections_count} correzioni timestamp applicate")
            else:
                st.error("❌ Impossibile calcolare margin timeline")


def _render_timestamp_debug(trades_df: pd.DataFrame, account_id: str):
    """
    Render timestamp corrections debug.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    if st.button(f"⏰ Analizza Timestamp", key=f"test_timestamp_{account_id}"):
        margin_timeline = calculate_margin_timeline(trades_df)
        if not margin_timeline.empty:
            render_timestamp_corrections_debug(margin_timeline)
        else:
            st.warning("Nessun dato margin timeline disponibile")


def _render_file_pattern_analysis(trades_df: pd.DataFrame, account_id: str):
    """
    Render file pattern analysis for classification debugging.
    
    Args:
        trades_df: Complete trades DataFrame
        account_id: Account identifier
    """
    if 'SourceFilename' not in trades_df.columns:
        st.info("Analisi pattern file non disponibile (colonna SourceFilename mancante)")
        return
    
    filenames = trades_df['SourceFilename'].unique()
    
    # Pattern analysis
    backtest_files = [f for f in filenames if '_000000' in f]
    live_files = [f for f in filenames if '_000000' not in f]
    
    st.markdown("**📁 Analisi Pattern File:**")
    st.write(f"- File totali: {len(filenames)}")
    st.write(f"- File backtest (_000000): {len(backtest_files)}")
    st.write(f"- File live (altri): {len(live_files)}")
    
    # Show examples
    if backtest_files:
        st.markdown("**Esempi Backtest:**")
        for f in backtest_files[:3]:
            st.code(f, language=None)
    
    if live_files:
        st.markdown("**Esempi Live:**")
        for f in live_files[:3]:
            st.code(f, language=None)


def _calculate_dataset_statistics(trades_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate comprehensive dataset statistics.
    
    Args:
        trades_df: Complete trades DataFrame
        
    Returns:
        Dict with dataset statistics
    """
    stats = {
        'total_rows': len(trades_df),
        'columns': list(trades_df.columns),
        'unique_trades': trades_df['OpenPositionTicket'].nunique() if 'OpenPositionTicket' in trades_df.columns else 0,
        'magic_numbers': trades_df['MagicNumber'].nunique() if 'MagicNumber' in trades_df.columns else 0,
        'symbols': trades_df['OrderSymbol'].nunique() if 'OrderSymbol' in trades_df.columns else 0
    }
    
    # Date range analysis
    if 'OpenDatetime' in trades_df.columns:
        min_date = trades_df['OpenDatetime'].min()
        max_date = trades_df['OpenDatetime'].max()
        stats['date_range'] = {
            'start': min_date,
            'end': max_date,
            'days': (max_date - min_date).days
        }
    
    # Performance analysis
    if 'PL' in trades_df.columns:
        trade_results = trades_df.groupby('OpenPositionTicket')['PL'].sum() if 'OpenPositionTicket' in trades_df.columns else trades_df['PL']
        
        stats['performance'] = {
            'total_pl': trades_df['PL'].sum(),
            'avg_pl_per_trade': trade_results.mean(),
            'win_rate': (len(trade_results[trade_results > 0]) / len(trade_results) * 100) if len(trade_results) > 0 else 0,
            'max_win': trade_results.max(),
            'max_loss': trade_results.min()
        }
    
    return stats


def get_debug_session_info(account_id: str) -> Dict[str, Any]:
    """
    Get debug information about current session state.
    
    Args:
        account_id: Account identifier
        
    Returns:
        Dict with debug session information
    """
    from ..utils.session_helpers import (
        get_sidebar_width,
        get_selected_setups,
        get_period_configuration,
        get_advanced_filters
    )
    
    return {
        'account_id': account_id,
        'sidebar_width': get_sidebar_width(account_id),
        'selected_setups': get_selected_setups(account_id),
        'period_configured': get_period_configuration(account_id) is not None,
        'active_filters': get_advanced_filters(account_id),
        'session_keys_count': len([k for k in st.session_state.keys() if account_id in k])
    }