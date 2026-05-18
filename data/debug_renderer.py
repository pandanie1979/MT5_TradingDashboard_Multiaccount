# data/debug_renderer.py
"""
Modulo per il rendering dell'interfaccia di debug del margine.
Fornisce funzioni per visualizzare i risultati dell'analisi in modo user-friendly.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
from datetime import datetime

def render_margin_debug_section(debug_results: Dict, account_id: str, account_color: str):
    """
    Renderizza la sezione completa di debug del margine.

    Args:
        debug_results: Risultati dell'analisi dal MarginDebugger
        account_id: ID dell'account corrente
        account_color: Colore dell'account per styling
    """
    st.markdown("---")
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <div style="width: 3px; height: 25px; background: {account_color}; margin-right: 10px; border-radius: 1px;"></div>
        <h3 style="margin: 0;">DEBUG: Analisi Dati Margine Account {account_id}</h3>
    </div>
    """, unsafe_allow_html=True)

    if "error" in debug_results:
        st.error(f"[ERR] {debug_results['error']}")
        return

    # Tab per organizzare le varie sezioni di debug
    debug_tab1, debug_tab2, debug_tab3, debug_tab4 = st.tabs([
        "Panoramica", "Anomalie", "Eventi Dettaglio", "Dati Raw"
    ])

    with debug_tab1:
        render_debug_overview(debug_results, account_id, account_color)

    with debug_tab2:
        render_anomalies_analysis(debug_results, account_id)

    with debug_tab3:
        render_events_detail(debug_results, account_id)

    with debug_tab4:
        render_raw_data_analysis(debug_results, account_id)

def render_debug_overview(debug_results: Dict, account_id: str, account_color: str):
    """
    Renderizza la panoramica generale del debug.
    """
    st.subheader(f"Panoramica Debug Account {account_id}")

    stats = debug_results.get('statistics', {})
    timeline = debug_results.get('debug_timeline', pd.DataFrame())
    anomalies = debug_results.get('anomalies', [])

    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Righe Dati", stats.get('total_rows', 0))

    with col2:
        st.metric("Eventi Margine", stats.get('total_events', 0))

    with col3:
        st.metric("Anomalie Trovate", len(anomalies))

    with col4:
        timeline_stats = stats.get('timeline', {})
        final_margin = timeline_stats.get('final_margin', 0)
        final_positions = timeline_stats.get('final_positions', 0)

        # Indica se c'e il problema del piedistallo
        if final_margin > 0 and final_positions == 0:
            st.metric("[ALERT] Piedistallo", f"€{final_margin:.2f}",
                     help="Margine finale > 0 senza posizioni aperte!")
        else:
            st.metric("Margine Finale", f"€{final_margin:.2f}")

    # Grafico timeline debug
    if not timeline.empty:
        render_debug_timeline_chart(timeline, account_id, account_color)

    # Riepilogo statistiche dettagliate
    if stats:
        render_statistics_summary(stats)

def render_debug_timeline_chart(timeline_df: pd.DataFrame, account_id: str, account_color: str):
    """
    Renderizza il grafico della timeline di debug del margine.
    """
    st.markdown("### Timeline Debug Margine")

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        subplot_titles=(
            f'Margine Calcolato Step-by-Step - Account {account_id}',
            f'Numero Posizioni Aperte - Account {account_id}'
        ),
        vertical_spacing=0.1,
        shared_xaxes=True
    )

    # Grafico margine
    fig.add_trace(
        go.Scatter(
            x=timeline_df['timestamp'],
            y=timeline_df['total_margin_calculated'],
            mode='lines+markers',
            name='Margine Debug',
            line=dict(color=account_color, width=2),
            marker=dict(size=4),
            hovertemplate=('<b>Data:</b> %{x}<br>' +
                          '<b>Margine:</b> €%{y:.2f}<br>' +
                          '<b>Evento:</b> %{customdata[0]}<br>' +
                          '<b>Ticket:</b> %{customdata[1]}<extra></extra>'),
            customdata=timeline_df[['event_type', 'ticket']].values
        ),
        row=1, col=1
    )

    # Grafico numero posizioni
    fig.add_trace(
        go.Scatter(
            x=timeline_df['timestamp'],
            y=timeline_df['open_positions_count'],
            mode='lines+markers',
            name='Posizioni Aperte',
            line=dict(color='#ff7f0e', width=2),
            marker=dict(size=4),
            hovertemplate=('<b>Data:</b> %{x}<br>' +
                          '<b>Posizioni:</b> %{y}<br>' +
                          '<b>Tickets:</b> %{customdata}<extra></extra>'),
            customdata=timeline_df['open_tickets'].apply(lambda x: ', '.join(map(str, x)))
        ),
        row=2, col=1
    )

    # Layout
    fig.update_layout(
        height=600,
        showlegend=False,
        hovermode='x unified',
        plot_bgcolor='white'
    )

    fig.update_yaxes(title_text="Margine (€)", row=1, col=1, gridcolor='lightgray')
    fig.update_yaxes(title_text="N. Posizioni", row=2, col=1, gridcolor='lightgray')
    fig.update_xaxes(title_text="Data", row=2, col=1, gridcolor='lightgray')

    st.plotly_chart(fig, use_container_width=True)

    # Highlight del problema finale
    final_row = timeline_df.iloc[-1]
    if final_row['total_margin_calculated'] > 0 and final_row['open_positions_count'] == 0:
        st.error(f"[ALERT] **PROBLEMA IDENTIFICATO**: Margine finale €{final_row['total_margin_calculated']:.2f} " +
                f"con 0 posizioni aperte alla data {final_row['timestamp']}")
    else:
        st.success(f"[OK] Stato finale coerente: €{final_row['total_margin_calculated']:.2f} margine " +
                  f"con {final_row['open_positions_count']} posizioni aperte")

def render_anomalies_analysis(debug_results: Dict, account_id: str):
    """
    Renderizza l'analisi delle anomalie trovate.
    """
    st.subheader(f"⚠ Anomalie Identificate - Account {account_id}")

    anomalies = debug_results.get('anomalies', [])

    if not anomalies:
        st.success("[OK] Nessuna anomalia rilevata nei dati di margine!")
        return

    # Organizza anomalie per severita
    high_severity = [a for a in anomalies if a.get('severity') == 'HIGH']
    medium_severity = [a for a in anomalies if a.get('severity') == 'MEDIUM']

    if high_severity:
        st.error(f"[ALERT] **{len(high_severity)} Anomalie ad Alta Severita:**")
        for i, anomaly in enumerate(high_severity):
            # Usa container invece di expander per evitare nesting
            st.markdown(f"### {anomaly['type']}")
            with st.container():
                st.write(f"**Descrizione:** {anomaly['description']}")
                if 'timestamp' in anomaly:
                    st.write(f"**Timestamp:** {anomaly['timestamp']}")
                if 'details' in anomaly:
                    st.json(anomaly['details'])
            st.markdown("---")  # Separatore tra anomalie

    if medium_severity:
        st.warning(f"⚠ **{len(medium_severity)} Anomalie a Media Severita:**")
        for i, anomaly in enumerate(medium_severity):
            show_details = st.checkbox(f"Mostra dettagli: {anomaly['type']}",
                                     key=f"anomaly_details_{account_id}_{i}")
            if show_details:
                with st.container():
                    st.write(f"**Descrizione:** {anomaly['description']}")
                    if 'details' in anomaly:
                        st.json(anomaly['details'])
                st.markdown("---")

def render_events_detail(debug_results: Dict, account_id: str):
    """
    Renderizza i dettagli degli eventi di margine.
    """
    st.subheader(f"Eventi Margine Dettagliati - Account {account_id}")

    timeline = debug_results.get('debug_timeline', pd.DataFrame())

    if timeline.empty:
        st.info("Nessun evento di margine da mostrare")
        return

    # Filtri per gli eventi
    col1, col2 = st.columns(2)

    with col1:
        event_types = ['Tutti'] + list(timeline['event_type'].unique())
        selected_event_type = st.selectbox("Filtra per Tipo Evento:", event_types)

    with col2:
        tickets = ['Tutti'] + list(timeline['ticket'].unique())
        selected_ticket = st.selectbox("Filtra per Ticket:", tickets)

    # Applica filtri
    filtered_timeline = timeline.copy()
    if selected_event_type != 'Tutti':
        filtered_timeline = filtered_timeline[filtered_timeline['event_type'] == selected_event_type]
    if selected_ticket != 'Tutti':
        filtered_timeline = filtered_timeline[filtered_timeline['ticket'] == selected_ticket]

    # Tabella eventi
    if not filtered_timeline.empty:
        display_columns = [
            'timestamp', 'event_type', 'ticket', 'event_margin',
            'total_margin_calculated', 'open_positions_count'
        ]

        st.dataframe(
            filtered_timeline[display_columns],
            use_container_width=True,
            column_config={
                "timestamp": st.column_config.DatetimeColumn("Data/Ora"),
                "event_type": st.column_config.TextColumn("Tipo Evento"),
                "ticket": st.column_config.NumberColumn("Ticket"),
                "event_margin": st.column_config.NumberColumn("Margine Evento", format="%.2f €"),
                "total_margin_calculated": st.column_config.NumberColumn("Margine Totale", format="%.2f €"),
                "open_positions_count": st.column_config.NumberColumn("N. Posizioni")
            }
        )
    else:
        st.info("Nessun evento corrisponde ai filtri selezionati")

    # Dettaglio evento selezionato
    if not filtered_timeline.empty:
        st.markdown("---")
        st.subheader("Dettaglio Evento Selezionato")

        selected_idx = st.selectbox(
            "Seleziona evento per dettagli:",
            range(len(filtered_timeline)),
            format_func=lambda i: f"{filtered_timeline.iloc[i]['timestamp']} - {filtered_timeline.iloc[i]['event_type']}"
        )

        if selected_idx is not None:
            selected_event = filtered_timeline.iloc[selected_idx]

            col1, col2 = st.columns(2)

            with col1:
                st.json({
                    "Event ID": selected_event['event_id'],
                    "Timestamp": str(selected_event['timestamp']),
                    "Event Type": selected_event['event_type'],
                    "Ticket": int(selected_event['ticket']),
                    "Event Margin": f"€{selected_event['event_margin']:.2f}",
                    "Total Margin": f"€{selected_event['total_margin_calculated']:.2f}",
                    "Open Positions": int(selected_event['open_positions_count'])
                })

            with col2:
                st.write("**Posizioni Aperte in questo momento:**")
                position_details = selected_event.get('position_details', {})
                if position_details:
                    for ticket, details in position_details.items():
                        st.write(f"- **Ticket {ticket}**: €{details['margin']:.2f} ({details['symbol']})")
                else:
                    st.write("Nessuna posizione aperta")

def render_statistics_summary(stats: Dict):
    """
    Renderizza il riepilogo delle statistiche di debug.
    """
    st.markdown("### Statistiche Debug")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Statistiche Generali:**")
        st.json({
            "Righe totali": stats.get('total_rows', 0),
            "Eventi totali": stats.get('total_events', 0),
            "Ticket unici": stats.get('unique_tickets', 0),
            "Periodo": {
                "Inizio": str(stats.get('date_range', {}).get('start', 'N/A')),
                "Fine": str(stats.get('date_range', {}).get('end', 'N/A'))
            }
        })

    with col2:
        # Statistiche margine
        margin_open = stats.get('margin_at_open', {})
        margin_close = stats.get('margin_at_close', {})

        if margin_open:
            st.write("**MarginAtOpen:**")
            st.json({
                "Min": f"€{margin_open.get('min', 0):.2f}",
                "Max": f"€{margin_open.get('max', 0):.2f}",
                "Media": f"€{margin_open.get('avg', 0):.2f}",
                "Count": margin_open.get('count', 0)
            })

        if margin_close:
            st.write("**MarginAtClose:**")
            st.json({
                "Min": f"€{margin_close.get('min', 0):.2f}",
                "Max": f"€{margin_close.get('max', 0):.2f}",
                "Media": f"€{margin_close.get('avg', 0):.2f}",
                "Chiusure complete (=0)": margin_close.get('zero_count', 0),
                "Chiusure parziali (>0)": margin_close.get('non_zero_count', 0)
            })

def render_raw_data_analysis(debug_results: Dict, account_id: str):
    """
    Renderizza l'analisi dei dati raw.
    """
    st.subheader(f"Analisi Dati Raw - Account {account_id}")

    raw_info = debug_results.get('raw_data_info', {})

    if not raw_info:
        st.info("Nessuna informazione sui dati raw disponibile")
        return

    # Informazioni sulle colonne
    st.write("**Struttura Dati:**")
    col1, col2 = st.columns(2)

    with col1:
        st.json({
            "Colonne totali": raw_info.get('total_columns', 0),
            "Colonne margine": raw_info.get('margin_related_columns', []),
            "Ha MarginAtOpen": raw_info.get('has_margin_at_open', False),
            "Ha MarginAtClose": raw_info.get('has_margin_at_close', False),
            "Ha CloseDatetime": raw_info.get('has_close_datetime', False)
        })

    with col2:
        st.write("**Sample Data (prime 3 righe):**")
        sample_data = raw_info.get('sample_data', [])
        if sample_data:
            # Mostra solo colonne rilevanti per il margine
            relevant_columns = [
                'OpenPositionTicket', 'OpenDatetime', 'CloseDatetime',
                'MarginAtOpen', 'MarginAtClose', 'PL', 'Symbol', 'MagicNumber'
            ]

            for i, row in enumerate(sample_data):
                st.write(f"**Riga {i+1}:**")
                filtered_row = {k: v for k, v in row.items() if k in relevant_columns}
                st.json(filtered_row)
        else:
            st.write("Nessun sample data disponibile")

    # Verifica colonne mancanti critiche
    st.markdown("---")
    st.write("**Verifica Completezza Dati:**")

    missing_critical = []
    if not raw_info.get('has_margin_at_open', False):
        missing_critical.append("MarginAtOpen")
    if not raw_info.get('has_margin_at_close', False):
        missing_critical.append("MarginAtClose")
    if not raw_info.get('has_close_datetime', False):
        missing_critical.append("CloseDatetime")

    if missing_critical:
        st.error(f"[ERR] **Colonne critiche mancanti**: {', '.join(missing_critical)}")
        st.write("Questo potrebbe spiegare problemi nel calcolo del margine timeline.")
    else:
        st.success("[OK] Tutte le colonne critiche per il margine sono presenti")

def render_comparison_with_current_timeline(debug_results: Dict, current_timeline: pd.DataFrame, account_id: str):
    """
    Renderizza il confronto tra timeline debug e timeline corrente.

    Args:
        debug_results: Risultati del debug
        current_timeline: Timeline attualmente calcolato dalla dashboard
        account_id: ID account
    """
    st.markdown("---")
    st.subheader(f"Confronto Timeline Debug vs Corrente - Account {account_id}")

    debug_timeline = debug_results.get('debug_timeline', pd.DataFrame())

    if debug_timeline.empty or current_timeline.empty:
        st.warning("Impossibile fare confronto: una delle timeline e vuota")
        return

    # Confronta valori finali
    debug_final = debug_timeline['total_margin_calculated'].iloc[-1]
    current_final = current_timeline['total_margin'].iloc[-1]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Margine Finale (Debug)", f"€{debug_final:.2f}")

    with col2:
        st.metric("Margine Finale (Corrente)", f"€{current_final:.2f}")

    with col3:
        difference = abs(debug_final - current_final)
        match = difference < 0.01

        if match:
            st.metric("Differenza", f"€{difference:.2f}", delta="Match!")
        else:
            st.metric("⚠ Differenza", f"€{difference:.2f}", delta="Non coincidono")

    # Grafico comparativo
    if not match:
        st.write("**Grafico Comparativo:**")

        fig = go.Figure()

        # Timeline debug
        fig.add_trace(go.Scatter(
            x=debug_timeline['timestamp'],
            y=debug_timeline['total_margin_calculated'],
            mode='lines',
            name='Debug Timeline',
            line=dict(color='red', width=2),
            hovertemplate='<b>Debug:</b> €%{y:.2f}<br><b>Data:</b> %{x}<extra></extra>'
        ))

        # Timeline corrente
        fig.add_trace(go.Scatter(
            x=current_timeline['timestamp'],
            y=current_timeline['total_margin'],
            mode='lines',
            name='Timeline Corrente',
            line=dict(color='blue', width=2, dash='dash'),
            hovertemplate='<b>Corrente:</b> €%{y:.2f}<br><b>Data:</b> %{x}<extra></extra>'
        ))

        fig.update_layout(
            title=f"Confronto Timeline Margine - Account {account_id}",
            xaxis_title="Data",
            yaxis_title="Margine (€)",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        st.warning("⚠ **Le timeline non coincidono!** Questo indica un problema nella logica di calcolo del margine.")
    else:
        st.success("[OK] Le timeline coincidono perfettamente. Il problema potrebbe essere nei dati EA o nella logica di ricostruzione.")
