import streamlit as st
from data.loader import get_ea_data
from data.metrics import format_status, format_yes_no
from datetime import datetime
import pandas as pd
import os

def render(account_id: str, account_path: str, account_info: dict):
    # Header con indicatore account
    account_color = account_info.get('color', '#1f77b4')
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <div style="width: 4px; height: 40px; background: {account_color}; margin-right: 15px; border-radius: 2px;"></div>
        <div>
            <h2 style="margin: 0; color: #1f1f1f;">📊 Expert Advisors Attivi</h2>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Account: {account_id} | 
            {account_info.get('ea_files', 0)} file EA trovati</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    ea_df = get_ea_data(account_id, account_path)

    if ea_df is None or ea_df.empty:
        st.error(f"❌ Impossibile caricare i dati degli EA per Account {account_id}.")
        st.info(f"📁 Percorso verificato: `{account_path}`")
        st.info(f"🔍 Pattern cercato: `EAMon_{account_id}_*.csv`")
        
        # Mostra status connessione
        if os.path.exists(account_path):
            all_ea_files = [f for f in os.listdir(account_path) if f.startswith('EAMon_')]
            st.info(f"File EA totali trovati: {len(all_ea_files)}")
            if all_ea_files:
                st.write("File EA disponibili (primi 5):")
                for f in all_ea_files[:5]:
                    st.write(f"- {f}")
        else:
            st.error(f"❌ Cartella non accessibile: {account_path}")
        
        return

    # Metriche con colore account
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        active_count = len(ea_df[ea_df['Status'] == 'ACTIVE'])
        st.metric("EA Attivi", active_count, 
                 delta=f"su {len(ea_df)}" if len(ea_df) > 0 else None)
    with col2:
        st.metric("Totale EA", len(ea_df))
    with col3:
        positions_count = len(ea_df[ea_df['Has_Position'] == 'YES'])
        st.metric("Con Posizioni", positions_count)
    with col4:
        trading_on_count = len(ea_df[ea_df['Trading_Enabled'] == 'YES'])
        st.metric("Trading ON", trading_on_count)

    # Alert per EA problematici
    if len(ea_df) > 0:
        inactive_ea = ea_df[ea_df['Status'] != 'ACTIVE']
        if not inactive_ea.empty:
            st.warning(f"⚠️ {len(inactive_ea)} EA non attivi trovati per Account {account_id}")

    st.markdown("---")

    # Filtri
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filtra per Status", 
            ['Tutti'] + sorted(ea_df['Status'].unique().tolist()),
            key=f"status_filter_{account_id}"
        )
    with col2:
        symbol_filter = st.selectbox(
            "Filtra per Symbol", 
            ['Tutti'] + sorted(ea_df['Symbol'].unique().tolist()),
            key=f"symbol_filter_{account_id}"
        )
    with col3:
        ea_filter = st.selectbox(
            "Filtra per EA", 
            ['Tutti'] + sorted(ea_df['EA_Name'].unique().tolist()),
            key=f"ea_filter_{account_id}"
        )

    filtered_df = ea_df.copy()
    if status_filter != 'Tutti':
        filtered_df = filtered_df[filtered_df['Status'] == status_filter]
    if symbol_filter != 'Tutti':
        filtered_df = filtered_df[filtered_df['Symbol'] == symbol_filter]
    if ea_filter != 'Tutti':
        filtered_df = filtered_df[filtered_df['EA_Name'] == ea_filter]

    st.subheader(f"📋 Elenco EA Account {account_id} ({len(filtered_df)} di {len(ea_df)})")

    if not filtered_df.empty:
        display_df = filtered_df.copy()
        now = datetime.now()
        display_df['Minutes_Since_Last_Tick'] = (
            now - pd.to_datetime(display_df['Last_Tick_Time'])
        ).dt.total_seconds() / 60

        display_columns = {
            'Magic_Number': 'Magic Number',
            'EA_Name': 'EA',
            'Symbol': 'Symbol',
            'Timeframe': 'TF',
            'Status': 'Status',
            'Trading_Enabled': 'Trading',
            'Has_Position': 'Position',
            'Position_Margin': 'Margin (€)',
            'Tick_Count': 'Ticks',
            'Minutes_Since_Last_Tick': 'Min da Ultimo Tick'
        }

        table_df = display_df[list(display_columns.keys())].rename(columns=display_columns)

        # Aggiungi colorazione per status
        def color_status(val):
            if val == 'ACTIVE':
                return f'background-color: #d4edda; color: #155724'
            elif val == 'INACTIVE':
                return f'background-color: #f8d7da; color: #721c24'
            else:
                return f'background-color: #fff3cd; color: #856404'

        # Applica styling condizionale
        styled_df = table_df.style.map(color_status, subset=['Status'])

        st.dataframe(
            styled_df, 
            width='stretch',
            column_config={
                "Margin (€)": st.column_config.NumberColumn(
                    "Margin (€)",
                    format="%.2f €"
                )
            }
        )

        st.markdown("---")
        st.subheader(f"📊 Dettagli EA Selezionato - Account {account_id}")

        selected_setup = st.selectbox(
            "Seleziona un setup per i dettagli",
            options=filtered_df['Setup_Name'].tolist(),
            key=f"setup_selector_{account_id}"
        )

        if selected_setup:
            selected_ea = filtered_df[filtered_df['Setup_Name'] == selected_setup].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"""
                **Account:** {account_id}
                **Setup:** {selected_ea['Setup_Name']}
                **EA:** {selected_ea['EA_Name']}
                **Symbol:** {selected_ea['Symbol']}
                **Timeframe:** {selected_ea['Timeframe']}
                **Magic Number:** {selected_ea['Magic_Number']}
                """)
            with col2:
                st.info(f"""
                **Status:** {selected_ea['Status']}
                **Trading:** {selected_ea['Trading_Enabled']}
                **Posizione:** {selected_ea['Has_Position']}
                **Margine:** €{selected_ea['Position_Margin']:.2f}
                **Tick Ricevuti:** {selected_ea['Tick_Count']:,}
                **Ultimo Tick:** {selected_ea['Last_Tick_Time'].strftime('%d/%m/%Y %H:%M:%S') if pd.notna(selected_ea['Last_Tick_Time']) else 'N/A'}
                """)

            # Timeline EA
            st.markdown("**📈 Timeline EA:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                if pd.notna(selected_ea['EA_Start_Time']):
                    st.metric("Avviato", selected_ea['EA_Start_Time'].strftime('%d/%m %H:%M'))
                else:
                    st.metric("Avviato", "N/A")
            with col2:
                if pd.notna(selected_ea['Last_Tick_Time']):
                    minutes_since = (now - selected_ea['Last_Tick_Time']).total_seconds() / 60
                    st.metric("Ultimo Tick", f"{minutes_since:.1f} min fa")
                else:
                    st.metric("Ultimo Tick", "N/A")
            with col3:
                st.metric("File", os.path.basename(selected_ea['File_Path']))

        # Alert specifici per account
        st.markdown("---")
        st.subheader(f"⚠️ Monitoraggio Account {account_id}")

        # Check EA inattivi con posizioni
        inactive_with_positions = filtered_df[
            (filtered_df['Status'] != 'ACTIVE') & 
            (filtered_df['Has_Position'] == 'YES')
        ]
        
        if not inactive_with_positions.empty:
            st.error(f"🚨 {len(inactive_with_positions)} EA inattivi con posizioni aperte:")
            for _, ea in inactive_with_positions.iterrows():
                st.write(f"- **{ea['Setup_Name']}** ({ea['Symbol']}): Status = {ea['Status']}, Margine = €{ea['Position_Margin']:.2f}")

        # Check tick non ricevuti
        now = datetime.now()
        old_ticks = filtered_df[
            (pd.to_datetime(filtered_df['Last_Tick_Time']) < (now - pd.Timedelta(minutes=5))) &
            (filtered_df['Status'] == 'ACTIVE')
        ]
        
        if not old_ticks.empty:
            st.warning(f"⚠️ {len(old_ticks)} EA attivi senza tick da >5 minuti:")
            for _, ea in old_ticks.iterrows():
                minutes_ago = (now - pd.to_datetime(ea['Last_Tick_Time'])).total_seconds() / 60
                st.write(f"- **{ea['Setup_Name']}** ({ea['Symbol']}): {minutes_ago:.1f} minuti fa")
        else:
            if len(filtered_df[filtered_df['Status'] == 'ACTIVE']) > 0:
                st.success(f"✅ Tutti gli EA attivi di Account {account_id} ricevono tick regolarmente")

    else:
        st.info(f"Nessun EA corrisponde ai filtri selezionati per Account {account_id}.")

    # Pulsanti di controllo (RIMOSSI PULSANTI NAVIGAZIONE + REFRESH NON INVASIVO)
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"🔄 Aggiorna EA Account {account_id}", width='stretch'):
            st.cache_data.clear()
            # NON usare st.rerun() per preservare stato tab
            st.success("✅ Cache pulita! I dati EA saranno aggiornati automaticamente.")
    
    with col2:
        # Spazio libero - pulsante navigazione rimosso
        st.write("")