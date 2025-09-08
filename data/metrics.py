import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_performance_metrics(trades_df, start_date, end_date):
    """
    Calcola le metriche di performance per ogni setup nel periodo specificato
    Supporta multi-account con colonna Account_ID
    """
    # Filtra per periodo
    filtered_trades = trades_df[
        (trades_df['OpenDatetime'] >= start_date) & 
        (trades_df['OpenDatetime'] <= end_date)
    ].copy()
    
    if filtered_trades.empty:
        return pd.DataFrame()
    
    # Raggruppa per MagicNumber (identificativo univoco del setup)
    performance_data = []
    
    for magic_number in filtered_trades['MagicNumber'].unique():
        setup_trades = filtered_trades[filtered_trades['MagicNumber'] == magic_number]
        
        # Conta trades unici e deals
        unique_trades = setup_trades['OpenPositionTicket'].nunique()
        total_deals = len(setup_trades)
        
        # Calcola metriche sui P&L aggregati per trade
        trade_performance = setup_trades.groupby('OpenPositionTicket')['PL'].sum()
        
        # Metriche
        total_profit = trade_performance.sum()
        avg_profit_per_trade = trade_performance.mean()
        
        # Profit Factor
        winning_trades = trade_performance[trade_performance > 0].sum()
        losing_trades = abs(trade_performance[trade_performance < 0].sum())
        profit_factor = winning_trades / losing_trades if losing_trades > 0 else float('inf')
        
        # Win Rate (basato su trades unici)
        wins = len(trade_performance[trade_performance > 0])
        win_rate = (wins / unique_trades) * 100 if unique_trades > 0 else 0
        
        # Max Drawdown
        cumulative_pl = setup_trades.sort_values('OpenDatetime')['PL'].cumsum()
        max_drawdown = (cumulative_pl.cummax() - cumulative_pl).max()
        
        # Prendi informazioni dal primo trade del setup
        first_trade = setup_trades.iloc[0]
        
        # Account ID (se disponibile)
        account_id = first_trade.get('Account_ID', first_trade.get('Account', 'Unknown'))
        
        performance_data.append({
            'Account_ID': account_id,
            'Magic_Number': magic_number,
            'Strategy_Name': first_trade.get('StrategyName', first_trade.get('StrategyFromFile', 'Unknown')),
            'Symbol': first_trade.get('OrderSymbol', first_trade.get('Symbol', 'Unknown')),
            'Unique_Trades': unique_trades,
            'Total_Deals': total_deals,
            'Total_Profit': total_profit,
            'Avg_Profit_Per_Trade': avg_profit_per_trade,
            'Profit_Factor': profit_factor,
            'Win_Rate': win_rate,
            'Max_Drawdown': max_drawdown,
            'Wins': wins,
            'Losses': unique_trades - wins,
            'First_Trade': setup_trades['OpenDatetime'].min(),
            'Last_Trade': setup_trades['OpenDatetime'].max(),
            'Recovery_Factor': abs(total_profit / max_drawdown) if max_drawdown > 0 else 0
        })
    
    return pd.DataFrame(performance_data)

def calculate_risk_metrics(trades_df) -> dict:
    """
    Calcola metriche di rischio avanzate per il pannello metriche.
    """
    if trades_df.empty:
        return {}
    
    # P&L per trade unico
    trade_pls = trades_df.groupby('OpenPositionTicket')['PL'].sum()
    
    # Metriche base
    total_trades = len(trade_pls)
    winning_trades = len(trade_pls[trade_pls > 0])
    losing_trades = len(trade_pls[trade_pls < 0])
    
    # Streak consecutivi
    consecutive_wins = 0
    consecutive_losses = 0
    current_streak = 0
    max_win_streak = 0
    max_loss_streak = 0
    
    trade_results = trade_pls.apply(lambda x: 1 if x > 0 else -1)
    
    for result in trade_results:
        if result == 1:  # Win
            if current_streak >= 0:
                current_streak += 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                current_streak = 1
        else:  # Loss
            if current_streak <= 0:
                current_streak -= 1
                max_loss_streak = max(max_loss_streak, abs(current_streak))
            else:
                current_streak = -1
    
    # Sharpe Ratio semplificato
    mean_return = trade_pls.mean()
    std_return = trade_pls.std()
    sharpe_ratio = mean_return / std_return if std_return > 0 else 0
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'avg_win': trade_pls[trade_pls > 0].mean() if winning_trades > 0 else 0,
        'avg_loss': trade_pls[trade_pls < 0].mean() if losing_trades > 0 else 0,
        'largest_win': trade_pls.max(),
        'largest_loss': trade_pls.min(),
        'sharpe_ratio': sharpe_ratio,
        'total_pnl': trade_pls.sum(),
        'avg_pnl_per_trade': trade_pls.mean()
    }

def classify_trades_backtest_vs_live(trades_df, ticket_threshold=100000):
    """
    Classifica i trade come backtest o live basandosi sui ticket numbers.
    
    Args:
        trades_df: DataFrame con i trade
        ticket_threshold: Soglia per distinguere backtest (sotto) da live (sopra)
    
    Returns:
        DataFrame con colonna aggiuntiva 'trade_type' ['backtest', 'live']
    """
    if trades_df.empty or 'OpenPositionTicket' not in trades_df.columns:
        return trades_df
    
    # Classifica basandosi sui ticket numbers
    trades_df = trades_df.copy()
    trades_df['trade_type'] = trades_df['OpenPositionTicket'].apply(
        lambda ticket: 'backtest' if ticket < ticket_threshold else 'live'
    )
    
    return trades_df

def calculate_weekly_trade_composition(equity_data, date_col='PlotDate'):
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

def calculate_dynamic_color(live_ratio):
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

def create_continuous_equity_curve(trades_df, plot_date_col='PlotDate', multi_mn=False):
    """
    Crea equity curve continua SENZA interruzioni per colori.
    PRIORITÃ€: Mantenere continuitÃ  matematica perfetta.
    
    Args:
        trades_df: DataFrame con i trade
        plot_date_col: Nome colonna date per plot
        multi_mn: Se True, calcola info settimanali per colori
    
    Returns:
        DataFrame con equity curve continua + info per colori overlay
    """
    if trades_df.empty:
        return pd.DataFrame()
    
    # Ordina per data e RESET INDEX per partire da zero
    equity_data = trades_df.sort_values(plot_date_col).reset_index(drop=True).copy()
    
    # IMPORTANTE: Equity cumulativa continua - SEMPRE da zero
    equity_data['Cumulative_PL'] = equity_data['PL'].cumsum()
    equity_data['Running_Peak'] = equity_data['Cumulative_PL'].cummax()
    equity_data['Drawdown'] = equity_data['Cumulative_PL'] - equity_data['Running_Peak']
    
    # Aggiungi info per colori SENZA interrompere la continuitÃ 
    if multi_mn and 'trade_type' in equity_data.columns:
        # Analisi settimanale per multi-MN
        equity_data = calculate_weekly_trade_composition(equity_data, plot_date_col)
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
        # Default per compatibilitÃ 
        equity_data['live_ratio'] = 1.0
        equity_data['week_type'] = 'live'
        equity_data['dynamic_color'] = '#1f77b4'
    
    return equity_data

def generate_color_segments_for_plotly(equity_data, plot_date_col='PlotDate'):
    """
    Genera segmenti di colore per overlay su Plotly SENZA interrompere la linea principale.
    
    Args:
        equity_data: DataFrame con equity curve e color info
        plot_date_col: Nome colonna date
    
    Returns:
        Lista di shapes per Plotly overlay
    """
    if equity_data.empty or 'dynamic_color' not in equity_data.columns:
        return []
    
    shapes = []
    current_color = None
    segment_start_date = None
    
    for i, row in equity_data.iterrows():
        if current_color != row['dynamic_color']:
            # Se non Ã¨ il primo segmento, chiudi il precedente
            if current_color is not None and segment_start_date is not None:
                shapes.append({
                    'type': 'rect',
                    'x0': segment_start_date,
                    'x1': row[plot_date_col],
                    'y0': 0,
                    'y1': 1,
                    'yref': 'paper',
                    'fillcolor': current_color,
                    'opacity': 0.1,
                    'line': {'width': 0},
                    'layer': 'below'
                })
            
            # Inizia nuovo segmento
            current_color = row['dynamic_color']
            segment_start_date = row[plot_date_col]
    
    # Chiudi l'ultimo segmento
    if current_color is not None and segment_start_date is not None:
        shapes.append({
            'type': 'rect',
            'x0': segment_start_date,
            'x1': equity_data[plot_date_col].iloc[-1],
            'y0': 0,
            'y1': 1,
            'yref': 'paper',
            'fillcolor': current_color,
            'opacity': 0.1,
            'line': {'width': 0},
            'layer': 'below'
        })
    
    return shapes

def format_hover_info_detailed(row, multi_mn=False):
    """
    Formatta informazioni dettagliate per tooltip hover.
    
    Args:
        row: Riga del DataFrame con dati trade
        multi_mn: Se True, include info settimanali
    
    Returns:
        String formattata per hover
    """
    base_info = f"""
    <b>Data:</b> {row.get('PlotDate', 'N/A')}<br>
    <b>Equity:</b> â‚¬{row.get('Cumulative_PL', 0):.2f}
    """
    
    if 'live_ratio' in row and pd.notna(row['live_ratio']):
        live_pct = row['live_ratio'] * 100
        backtest_pct = (1 - row['live_ratio']) * 100
        
        if multi_mn:
            if live_pct == 100:
                period_info = "<br><b>Settimana:</b> ðŸ“ˆ 100% Live Trading"
            elif live_pct == 0:
                period_info = "<br><b>Settimana:</b> ðŸ§ª 100% Backtest"
            else:
                period_info = f"<br><b>Settimana:</b> ðŸ”„ {live_pct:.0f}% Live, {backtest_pct:.0f}% Backtest"
        else:
            if live_pct == 100:
                period_info = "<br><b>Tipo:</b> ðŸ“ˆ Live Trading"
            else:
                period_info = "<br><b>Tipo:</b> ðŸ§ª Backtest"
        
        return base_info + period_info
    
    return base_info

def calculate_account_summary(accounts_data: dict) -> dict:
    """
    Calcola un riepilogo delle metriche per tutti gli account
    """
    summary = {
        'total_accounts': len(accounts_data),
        'active_accounts': len([acc for acc in accounts_data.values() if acc.get('status') == 'active']),
        'total_ea_files': sum(acc.get('ea_files', 0) for acc in accounts_data.values()),
        'total_trade_files': sum(acc.get('trade_files', 0) for acc in accounts_data.values()),
        'accounts_with_data': len([acc for acc in accounts_data.values() 
                                  if acc.get('ea_files', 0) > 0 or acc.get('trade_files', 0) > 0])
    }
    return summary

def format_status(status):
    """Formatta lo status con colori"""
    colors = {
        'ACTIVE': 'green',
        'INACTIVE': 'red',
        'PAUSED': 'orange'
    }
    color = colors.get(status, 'gray')
    return f"<span style='color: {color}; font-weight: bold;'>â—</span> {status}"

def format_yes_no(value):
    """Formatta i valori Yes/No con colori"""
    color = "green" if value == "YES" else "red"
    return f"<span style='color: {color}; font-weight: bold;'>{value}</span>"

def format_account_badge(account_id: str, color: str = '#1f77b4') -> str:
    """Genera un badge colorato per l'account"""
    return f"""
    <div style="display: inline-block; padding: 4px 8px; background: {color}22; 
                color: {color}; border: 1px solid {color}44; border-radius: 12px; 
                font-size: 12px; font-weight: bold; margin: 2px;">
        ðŸ¦ {account_id}
    </div>
    """

def format_currency(value: float, currency: str = "â‚¬") -> str:
    """Formatta valori monetari con segno e colore"""
    if value >= 0:
        color = "green"
        sign = "+"
    else:
        color = "red"
        sign = ""
    
    return f"<span style='color: {color}; font-weight: bold;'>{sign}{value:.2f} {currency}</span>"

def calculate_risk_metrics(trades_df) -> dict:
    """
    Calcola metriche di rischio avanzate
    """
    if trades_df.empty:
        return {}
    
    # P&L per trade unico
    trade_pls = trades_df.groupby('OpenPositionTicket')['PL'].sum()
    
    # Metriche base
    total_trades = len(trade_pls)
    winning_trades = len(trade_pls[trade_pls > 0])
    losing_trades = len(trade_pls[trade_pls < 0])
    
    # Consecutive wins/losses
    trade_results = trade_pls.apply(lambda x: 1 if x > 0 else -1)
    consecutive_wins = 0
    consecutive_losses = 0
    current_streak = 0
    max_win_streak = 0
    max_loss_streak = 0
    
    for result in trade_results:
        if result == 1:  # Win
            if current_streak >= 0:
                current_streak += 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                current_streak = 1
        else:  # Loss
            if current_streak <= 0:
                current_streak -= 1
                max_loss_streak = max(max_loss_streak, abs(current_streak))
            else:
                current_streak = -1
    
    # Sharpe Ratio semplificato
    mean_return = trade_pls.mean()
    std_return = trade_pls.std()
    sharpe_ratio = mean_return / std_return if std_return > 0 else 0
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'avg_win': trade_pls[trade_pls > 0].mean() if winning_trades > 0 else 0,
        'avg_loss': trade_pls[trade_pls < 0].mean() if losing_trades > 0 else 0,
        'largest_win': trade_pls.max(),
        'largest_loss': trade_pls.min(),
        'sharpe_ratio': sharpe_ratio,
        'total_pnl': trade_pls.sum(),
        'avg_pnl_per_trade': trade_pls.mean()
    }

def get_account_color(account_id: str, accounts_data: dict) -> str:
    """Ottieni il colore assegnato a un account"""
    return accounts_data.get(account_id, {}).get('color', '#1f77b4')

def format_time_ago(timestamp) -> str:
    """Formatta un timestamp in formato 'X ore fa'"""
    from datetime import datetime
    import pandas as pd
    
    if pd.isna(timestamp):
        return "N/A"
    
    now = datetime.now()
    if isinstance(timestamp, str):
        timestamp = pd.to_datetime(timestamp)
    
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