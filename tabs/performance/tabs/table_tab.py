# MT5 Trading Dashboard - Performance Table Tab Component
# File: tabs/performance/tabs/table_tab.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Performance table tab component.
Displays detailed performance metrics per setup with sorting and configuration.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from ..utils.formatting import get_error_message
from ..config.constants import TABLE_CONFIG
from data.metrics import calculate_performance_metrics


def render_performance_table_tab(period_trades: pd.DataFrame, account_id: str):
    """
    Render Tab 3: Setup Performance Table with enhanced sorting and formatting.
    
    Args:
        period_trades: Filtered trades for current period and setups
        account_id: Account identifier
    """
    st.markdown(f"### 📋 Performance per Setup - Account {account_id}")
    
    if period_trades.empty:
        st.warning(get_error_message("no_data"))
        return
    
    # Calculate performance metrics
    performance_df = calculate_performance_metrics(
        period_trades, 
        period_trades['OpenDatetime'].min(), 
        period_trades['OpenDatetime'].max()
    )
    
    if performance_df.empty:
        st.warning("Nessuna metrica calcolabile")
        return
    
    # Render performance table
    _render_performance_table(performance_df)
    
    # Render summary statistics
    _render_setup_summary_statistics(performance_df, account_id)
    
    # Render table controls
    _render_table_controls(performance_df, account_id)


def _render_performance_table(performance_df: pd.DataFrame):
    """
    Render the main performance table with proper formatting.
    
    Args:
        performance_df: Performance metrics DataFrame
    """
    # Prepare display DataFrame
    display_df = _prepare_table_data(performance_df)
    
    # Configure column formatting
    column_config = _get_column_configuration()
    
    # Display table with enhanced configuration
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        height=TABLE_CONFIG["performance_table"]["height"]
    )


def _prepare_table_data(performance_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare performance data for table display with proper formatting.
    
    Args:
        performance_df: Raw performance metrics DataFrame
        
    Returns:
        Formatted DataFrame for display
    """
    display_df = performance_df.copy()
    
    # Round numeric columns appropriately
    numeric_formatting = {
        'Total_Profit': 2,
        'Avg_Profit_Per_Trade': 2, 
        'Profit_Factor': 2,
        'Win_Rate': 1,
        'Max_Drawdown': 2,
        'Recovery_Factor': 2
    }
    
    for col, decimals in numeric_formatting.items():
        if col in display_df.columns:
            display_df[col] = display_df[col].round(decimals)
    
    # Rename columns for better display
    column_renames = {
        'Magic_Number': 'Magic Number',
        'Strategy_Name': 'Strategia',
        'Symbol': 'Symbol',
        'Unique_Trades': 'Trades',
        'Total_Deals': 'Deals',
        'Total_Profit': 'P&L Totale (€)',
        'Avg_Profit_Per_Trade': 'P&L/Trade (€)',
        'Profit_Factor': 'Profit Factor',
        'Win_Rate': 'Win Rate (%)',
        'Wins': 'Vincenti',
        'Losses': 'Perdenti',
        'Max_Drawdown': 'Max DD (€)',
        'Recovery_Factor': 'Recovery Factor',
        'First_Trade': 'Primo Trade',
        'Last_Trade': 'Ultimo Trade'
    }
    
    # Apply renames only for existing columns
    available_renames = {k: v for k, v in column_renames.items() if k in display_df.columns}
    display_df = display_df.rename(columns=available_renames)
    
    return display_df


def _get_column_configuration() -> Dict[str, Any]:
    """
    Get column configuration for enhanced table display.
    
    Returns:
        Dict with Streamlit column configuration
    """
    return {
        "P&L Totale (€)": st.column_config.NumberColumn(
            format="%.2f €",
            help="Profitto totale del setup"
        ),
        "P&L/Trade (€)": st.column_config.NumberColumn(
            format="%.2f €",
            help="Profitto medio per trade"
        ),
        "Win Rate (%)": st.column_config.NumberColumn(
            format="%.1f%%", 
            help="Percentuale trade vincenti"
        ),
        "Profit Factor": st.column_config.NumberColumn(
            format="%.2f",
            help="Profit Factor (Vincite/Perdite)"
        ),
        "Max DD (€)": st.column_config.NumberColumn(
            format="%.2f €",
            help="Massimo drawdown"
        ),
        "Recovery Factor": st.column_config.NumberColumn(
            format="%.2f",
            help="Rapporto Profit/MaxDD"
        ),
        "Primo Trade": st.column_config.DatetimeColumn(
            format="DD/MM/YYYY",
            help="Data primo trade"
        ),
        "Ultimo Trade": st.column_config.DatetimeColumn(
            format="DD/MM/YYYY", 
            help="Data ultimo trade"
        )
    }


def _render_setup_summary_statistics(performance_df: pd.DataFrame, account_id: str):
    """
    Render summary statistics below the table.
    
    Args:
        performance_df: Performance metrics DataFrame
        account_id: Account identifier
    """
    st.markdown("---")
    st.markdown("#### 📊 Riepilogo Setup")
    
    # Calculate summary metrics
    total_setups = len(performance_df)
    profitable_setups = len(performance_df[performance_df['Total_Profit'] > 0])
    total_profit_all = performance_df['Total_Profit'].sum()
    
    # Find best and worst performing setups
    if total_setups > 0:
        best_setup = performance_df.loc[performance_df['Total_Profit'].idxmax()]
        worst_setup = performance_df.loc[performance_df['Total_Profit'].idxmin()]
    else:
        best_setup = worst_setup = None
    
    # Display summary in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Setup Totali", total_setups)
    
    with col2:
        profitable_pct = (profitable_setups / total_setups * 100) if total_setups > 0 else 0
        st.metric("Setup Profittevoli", profitable_setups, delta=f"{profitable_pct:.1f}%")
    
    with col3:
        if best_setup is not None:
            st.metric("Miglior Setup", f"MN{best_setup['Magic_Number']}")
        else:
            st.metric("Miglior Setup", "N/A")
    
    with col4:
        st.metric("P&L Combinato", f"€{total_profit_all:.2f}")
    
    # Additional insights
    if best_setup is not None and worst_setup is not None:
        st.markdown("**🎯 Performance Highlights:**")
        st.write(f"- **Best**: MN{best_setup['Magic_Number']} - {best_setup['Strategy_Name']} (€{best_setup['Total_Profit']:.2f})")
        st.write(f"- **Worst**: MN{worst_setup['Magic_Number']} - {worst_setup['Strategy_Name']} (€{worst_setup['Total_Profit']:.2f})")


def _render_table_controls(performance_df: pd.DataFrame, account_id: str):
    """
    Render table control buttons and options.
    
    Args:
        performance_df: Performance metrics DataFrame
        account_id: Account identifier
    """
    st.markdown("---")
    st.markdown("#### ⚙️ Controlli Tabella")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export button
        if st.button("📥 Esporta Tabella", key=f"export_table_{account_id}", use_container_width=True):
            csv_data = performance_df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name=f"performance_table_{account_id}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key=f"download_csv_{account_id}"
            )
    
    with col2:
        # Refresh data button
        if st.button("🔄 Aggiorna Dati", key=f"refresh_table_{account_id}", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Cache pulita! I dati saranno aggiornati.")


def render_advanced_table_analysis(performance_df: pd.DataFrame, account_id: str):
    """
    Render advanced table analysis in expandable section.
    
    Args:
        performance_df: Performance metrics DataFrame
        account_id: Account identifier
    """
    with st.expander("📈 Analisi Avanzata Setup", expanded=False):
        if performance_df.empty:
            st.info("Nessun dato disponibile per analisi avanzata")
            return
        
        # Correlation analysis
        _render_setup_correlations(performance_df)
        
        # Performance distribution
        _render_performance_distribution(performance_df)
        
        # Risk-Return analysis
        _render_risk_return_analysis(performance_df)


def _render_setup_correlations(performance_df: pd.DataFrame):
    """
    Render setup correlation analysis.
    
    Args:
        performance_df: Performance metrics DataFrame
    """
    st.markdown("**🔗 Correlazioni Setup:**")
    
    # Select numeric columns for correlation
    numeric_cols = ['Total_Profit', 'Win_Rate', 'Profit_Factor', 'Max_Drawdown']
    available_cols = [col for col in numeric_cols if col in performance_df.columns]
    
    if len(available_cols) >= 2:
        corr_matrix = performance_df[available_cols].corr()
        st.dataframe(corr_matrix, use_container_width=True)
    else:
        st.info("Dati insufficienti per analisi correlazioni")


def _render_performance_distribution(performance_df: pd.DataFrame):
    """
    Render performance distribution analysis.
    
    Args:
        performance_df: Performance metrics DataFrame
    """
    st.markdown("**📊 Distribuzione Performance:**")
    
    if 'Total_Profit' in performance_df.columns:
        profit_data = performance_df['Total_Profit']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Media", f"€{profit_data.mean():.2f}")
        
        with col2:
            st.metric("Mediana", f"€{profit_data.median():.2f}")
        
        with col3:
            st.metric("Std Dev", f"€{profit_data.std():.2f}")


def _render_risk_return_analysis(performance_df: pd.DataFrame):
    """
    Render risk-return analysis.
    
    Args:
        performance_df: Performance metrics DataFrame
    """
    st.markdown("**⚖️ Analisi Rischio-Rendimento:**")
    
    if all(col in performance_df.columns for col in ['Total_Profit', 'Max_Drawdown']):
        # Calculate risk-adjusted metrics
        performance_df_copy = performance_df.copy()
        performance_df_copy['Risk_Adjusted_Return'] = (
            performance_df_copy['Total_Profit'] / abs(performance_df_copy['Max_Drawdown'])
        ).replace([float('inf'), -float('inf')], 0)
        
        # Show top risk-adjusted performers
        top_performers = performance_df_copy.nlargest(3, 'Risk_Adjusted_Return')
        
        st.markdown("**🏆 Top Risk-Adjusted Performers:**")
        for idx, setup in top_performers.iterrows():
            st.write(f"- MN{setup['Magic_Number']}: {setup['Risk_Adjusted_Return']:.2f}")


def get_table_statistics(performance_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get comprehensive table statistics for external use.
    
    Args:
        performance_df: Performance metrics DataFrame
        
    Returns:
        Dict with table statistics
    """
    if performance_df.empty:
        return {'error': 'No data available'}
    
    return {
        'total_setups': len(performance_df),
        'profitable_setups': len(performance_df[performance_df['Total_Profit'] > 0]),
        'total_combined_profit': performance_df['Total_Profit'].sum(),
        'avg_setup_profit': performance_df['Total_Profit'].mean(),
        'best_setup': {
            'magic_number': performance_df.loc[performance_df['Total_Profit'].idxmax(), 'Magic_Number'],
            'profit': performance_df['Total_Profit'].max()
        },
        'worst_setup': {
            'magic_number': performance_df.loc[performance_df['Total_Profit'].idxmin(), 'Magic_Number'],
            'profit': performance_df['Total_Profit'].min()
        },
        'performance_range': {
            'min': performance_df['Total_Profit'].min(),
            'max': performance_df['Total_Profit'].max(),
            'std': performance_df['Total_Profit'].std()
        }
    }