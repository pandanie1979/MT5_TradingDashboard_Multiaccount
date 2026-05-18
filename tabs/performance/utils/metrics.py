import pandas as pd
from typing import Any, Dict


def get_performance_summary_data(trades_df: pd.DataFrame, acc_id: str) -> Dict[str, Any]:
    """
    Calculate aggregated performance KPIs from a filtered trades DataFrame.
    Pure Python/Pandas only. Returns zeroed values for empty input.
    """
    empty = {
        'Account_ID': acc_id,
        'Start_Date': '',
        'End_Date': '',
        'Total_Deals': 0,
        'Unique_Trades': 0,
        'Total_PL': 0.0,
        'Avg_PL_Per_Deal': 0.0,
        'Win_Count': 0,
        'Loss_Count': 0,
        'Win_Rate_Pct': 0.0,
        'Max_Win': 0.0,
        'Max_Loss': 0.0,
        'Profit_Factor': 0.0,
    }

    if trades_df.empty or 'PL' not in trades_df.columns:
        return empty

    pl = trades_df['PL']
    total_deals = len(trades_df)

    date_col = 'CloseDatetime' if 'CloseDatetime' in trades_df.columns else 'OpenDatetime'
    dates = pd.to_datetime(trades_df[date_col], errors='coerce').dropna()
    start_date = dates.min().date().isoformat() if not dates.empty else ''
    end_date = dates.max().date().isoformat() if not dates.empty else ''

    unique_trades = (
        trades_df['OpenPositionTicket'].nunique()
        if 'OpenPositionTicket' in trades_df.columns
        else total_deals
    )

    total_pl = pl.sum()
    avg_pl_per_deal = total_pl / total_deals if total_deals > 0 else 0.0

    wins = pl[pl > 0]
    losses = pl[pl < 0]
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (win_count / total_deals * 100) if total_deals > 0 else 0.0

    max_win = float(wins.max()) if not wins.empty else 0.0
    max_loss = float(losses.min()) if not losses.empty else 0.0

    total_losses_abs = abs(losses.sum())
    profit_factor = (wins.sum() / total_losses_abs) if total_losses_abs > 0 else 0.0

    return {
        'Account_ID': acc_id,
        'Start_Date': start_date,
        'End_Date': end_date,
        'Total_Deals': total_deals,
        'Unique_Trades': unique_trades,
        'Total_PL': round(float(total_pl), 2),
        'Avg_PL_Per_Deal': round(float(avg_pl_per_deal), 2),
        'Win_Count': win_count,
        'Loss_Count': loss_count,
        'Win_Rate_Pct': round(float(win_rate), 2),
        'Max_Win': round(max_win, 2),
        'Max_Loss': round(max_loss, 2),
        'Profit_Factor': round(float(profit_factor), 4),
    }
