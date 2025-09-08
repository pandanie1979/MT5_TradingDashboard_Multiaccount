import streamlit as st
from datetime import datetime
import pandas as pd
from data.loader import get_ea_data

def render(account_id: str, account_path: str, account_info: dict):
    # Header con indicatore account
    account_color = account_info.get('color', '#1f77b4')
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <div style="width: 4px; height: 40px; background: {account_color}; margin-right: 15px; border-radius: 2px;"></div>
        <div>
            <h2 style="margin: 0; color: #1f1f1f;">💰 Posizioni Aperte</h2>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Account: {account_id} | 
            Monitoraggio posizioni real-time</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    ea_df = get_ea_data(account_id, account_path)

    if ea_df is None or ea_df.empty:
        st.error(f"❌ Impossibile caricare i dati degli EA per Account {account_id}")
        st.info(f"📁 Percorso: {account_path}")
        return

    ea_with_positions = ea_df[ea_df['Has_Position'] == 'YES'].copy()

    if ea_with_positions.empty:
        st.info(f"🎉 Account {account_id}: Non ci sono posizioni aperte al momento")
        
        # Mostra comunque statistiche generali
        st.markdown("### 📊 Statistiche Account")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("EA Totali", len(ea_df))
        with col2:
            active_ea = len(ea_df[ea_df['Status'] == 'ACTIVE'])
            st.metric("EA Attivi", active_ea)
        with col3:
            trading_enabled = len(ea_df[ea_df['Trading_Enabled'] == 'YES'])
            st.metric("Trading Abilitato", trading_enabled)
        
        return

    st.success(f"📍 Account {account_id}: Trovate {len(ea_with_positions)} posizioni aperte")

    # Metriche con stile account
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Posizioni Aperte", len(ea_with_positions))
    with col2:
        total_margin = ea_with_positions['Position_Margin'].sum()
        st.metric("Margine Totale", f"{total_margin:.2f} €")
    with col3:
        unique_symbols = ea_with_positions['Symbol'].nunique()
        st.metric("Symbols Coinvolti", unique_symbols)
    with col4:
        avg_margin = ea_with_positions['Position_Margin'].mean()
        st.metric("Margine Medio", f"{avg_margin:.2f} €")

    st.markdown("---")
    st.subheader(f"📋 Dettaglio Posizioni Aperte - Account {account_id}")

    now = datetime.now()
    ea_with_positions['Minutes_Since_Last_Tick'] = (
        now - pd.to_datetime(ea_with_positions['Last_Tick_Time'])
    ).dt.total_seconds() / 60

    display_columns = {
        'Setup_Name': 'Setup',
        'EA_Name': 'EA',
        'Symbol': 'Symbol',
        'Magic_Number': 'Magic',
        'Status': 'Status',
        'Position_Margin': 'Margine (€)',
        'Tick_Count': 'Tick Ricevuti',
        'Minutes_Since_Last_Tick': 'Min da Ultimo Tick',
        'Last_Tick_Time': 'Ultimo Tick'
    }

    table_df = ea_with_positions[list(display_columns.keys())].rename(columns=display_columns)

    # Styling condizionale per la tabella
    def color_margin(val):
        try:
            if float(val) > 1000:
                return 'background-color: #fff3cd; color: #856404'  # Giallo per margini alti
            elif float(val) > 500:
                return 'background-color: #d1ecf1; color: #0c5460'  # Azzurro per margini medi
            else:
                return 'background-color: #d4edda; color: #155724'  # Verde per margini bassi
        except:
            return ''

    def color_status(val):
        if val == 'ACTIVE':
            return 'background-color: #d4edda; color: #155724'
        elif val == 'INACTIVE':
            return 'background-color: #f8d7da; color: #721c24'
        else:
            return 'background-color: #fff3cd; color: #856404'

    # Applica styling
    styled_df = table_df.style.map(color_margin, subset=['Margine (€)']) \
                              .map(color_status, subset=['Status'])

    st.dataframe(
        styled_df, 
        use_container_width=True,
        column_config={
            "Margine (€)": st.column_config.NumberColumn(
                "Margine (€)",
                format="%.2f €"
            )
        }
    )

    st.markdown("---")
    st.subheader(f"⚠️ Monitoraggio Posizioni Account {account_id}")

    # Alert per tick non ricevuti (più di 5 minuti)
    old_ticks = ea_with_positions[ea_with_positions['Minutes_Since_Last_Tick'] > 5]
    if not old_ticks.empty:
        st.warning(f"🚨 {len(old_ticks)} posizioni non ricevono tick da più di 5 minuti:")
        for _, pos in old_ticks.iterrows():
            st.write(f"- **{pos['Setup_Name']}** ({pos['Symbol']}): {pos['Minutes_Since_Last_Tick']:.1f} minuti fa")
    else:
        st.success(f"✅ Tutte le posizioni di Account {account_id} ricevono tick regolarmente")

    # Alert per EA inattivi con posizioni
    inactive_with_positions = ea_with_positions[ea_with_positions['Status'] != 'ACTIVE']
    if not inactive_with_positions.empty:
        st.error(f"🚨 {len(inactive_with_positions)} EA con posizioni aperte ma NON attivi:")
        for _, ea in inactive_with_positions.iterrows():
            st.write(f"- **{ea['Setup_Name']}** ({ea['Symbol']}): Status = {ea['Status']}, Margine = €{ea['Position_Margin']:.2f}")

    # Alert per margini elevati
    high_margin_positions = ea_with_positions[ea_with_positions['Position_Margin'] > 1000]
    if not high_margin_positions.empty:
        st.warning(f"💰 {len(high_margin_positions)} posizioni con margine elevato (>€1000):")
        for _, pos in high_margin_positions.iterrows():
            st.write(f"- **{pos['Setup_Name']}** ({pos['Symbol']}): €{pos['Position_Margin']:.2f}")

    # Distribuzione per Symbol
    st.markdown("---")
    st.subheader(f"📊 Distribuzione Posizioni per Symbol - Account {account_id}")
    
    symbol_summary = ea_with_positions.groupby('Symbol').agg({
        'Position_Margin': ['sum', 'count', 'mean']
    }).round(2)
    
    symbol_summary.columns = ['Margine Totale (€)', 'Num. Posizioni', 'Margine Medio (€)']
    symbol_summary = symbol_summary.sort_values('Margine Totale (€)', ascending=False)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(symbol_summary, use_container_width=True)
    
    with col2:
        # Grafico a torta delle posizioni per symbol
        import plotly.express as px
        
        symbol_counts = ea_with_positions['Symbol'].value_counts()
        if len(symbol_counts) > 0:
            fig = px.pie(
                values=symbol_counts.values,
                names=symbol_counts.index,
                title=f"Posizioni per Symbol - Account {account_id}",
                color_discrete_sequence=[account_color] + px.colors.qualitative.Set3
            )
            fig.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

    # Timeline delle aperture posizioni
    st.markdown("---")
    st.subheader(f"⏰ Timeline Aperture Posizioni - Account {account_id}")
    
    if 'EA_Start_Time' in ea_with_positions.columns:
        ea_starts = ea_with_positions[['Setup_Name', 'Symbol', 'EA_Start_Time', 'Position_Margin']].copy()
        ea_starts = ea_starts.dropna(subset=['EA_Start_Time'])
        ea_starts = ea_starts.sort_values('EA_Start_Time', ascending=False)
        
        if not ea_starts.empty:
            st.write(f"**Ultime aperture posizioni Account {account_id}:**")
            for _, row in ea_starts.head(10).iterrows():
                time_diff = now - pd.to_datetime(row['EA_Start_Time'])
                hours_ago = time_diff.total_seconds() / 3600
                
                if hours_ago < 1:
                    time_str = f"{int(time_diff.total_seconds() / 60)} min fa"
                elif hours_ago < 24:
                    time_str = f"{hours_ago:.1f} ore fa"
                else:
                    days_ago = hours_ago / 24
                    time_str = f"{days_ago:.1f} giorni fa"
                
                st.write(f"- **{row['Setup_Name']}** ({row['Symbol']}): €{row['Position_Margin']:.2f} - {time_str}")
        else:
            st.info("Nessuna informazione di timing disponibile per le posizioni")

    # Pulsanti di controllo (RIMOSSI PULSANTI NAVIGAZIONE + REFRESH NON INVASIVO)
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"🔄 Aggiorna Posizioni Account {account_id}", use_container_width=True):
            st.cache_data.clear()
            # NON usare st.rerun() per preservare stato tab
            st.success("✅ Cache pulita! I dati posizioni saranno aggiornati automaticamente.")
    
    with col2:
        # Spazio libero - pulsanti navigazione rimossi
        st.write("")

    # Riepilogo finale
    st.markdown("---")
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, {account_color}22 0%, {account_color}11 100%); 
                padding: 12px 16px; border-radius: 8px; border-left: 4px solid {account_color}; 
                margin: 10px 0;">
        <strong>📊 Riepilogo Account {account_id}:</strong><br>
        • {len(ea_with_positions)} posizioni aperte per un margine totale di €{total_margin:.2f}<br>
        • {len(ea_with_positions[ea_with_positions['Status'] == 'ACTIVE'])} EA attivi con posizioni<br>
        • Symbols coinvolti: {', '.join(ea_with_positions['Symbol'].unique())}<br>
        • Status monitoraggio: {"🟢 OK" if len(old_ticks) == 0 and len(inactive_with_positions) == 0 else "🟡 Attenzione"}
    </div>
    """, unsafe_allow_html=True)