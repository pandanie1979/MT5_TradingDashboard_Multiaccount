# MT5 Trading Dashboard - Performance Tab Constants
# File: tabs/performance/config/constants.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Performance tab specific constants and configuration values.
Extracted from original tab_performance.py for better maintainability.
"""

from typing import Dict, List

# Layout Constants
DEFAULT_SIDEBAR_WIDTH = 25
MIN_SIDEBAR_WIDTH = 15
MAX_SIDEBAR_WIDTH = 40
SIDEBAR_WIDTH_STEP = 5

# Preset Sidebar Widths
SIDEBAR_PRESETS = {
    "compact": 20,
    "normal": 25,
    "wide": 35
}

# Classification Constants
BACKTEST_TICKET_THRESHOLD = 10000
BACKTEST_FILENAME_PATTERN = "_000000"

# Color Constants for Trade Types
TRADE_TYPE_COLORS = {
    "backtest": {
        "base": "rgba(128, 128, 128, 0.4)",
        "light": "rgba(128, 128, 128, 0.2)",
        "hex": "#808080"
    },
    "live": {
        "base": "rgba(31, 119, 180, 0.3)",
        "light": "rgba(31, 119, 180, 0.1)",
        "hex": "#1f77b4"
    },
    "mixed": {
        "base": "rgba(75, 150, 200, 0.3)",
        "light": "rgba(75, 150, 200, 0.15)",
        "hex": "#4b96c8"
    }
}

# Chart Configuration
CHART_CONFIG = {
    "height": 700,
    "subplot_heights": [0.5, 0.25, 0.25],
    "vertical_spacing": 0.08,
    "margins": {
        "l": 60,
        "r": 120,
        "t": 80,
        "b": 60
    },
    "right_margin_factor": 0.12,
    "annotation_x_factor": 0.4
}

# Performance Metrics Layout
METRICS_LAYOUT = {
    "sections": {
        "performance_base": ["profit_total", "win_rate", "profit_factor"],
        "risk_metrics": ["max_win_streak", "max_loss_streak", "sharpe_ratio"],
        "drawdown_analysis": ["max_drawdown", "avg_drawdown", "dd_duration"],
        "margin_stats": ["max_margin", "trades_unique", "avg_win_loss"]
    },
    "columns_per_section": 3
}

# Session State Key Patterns
SESSION_KEYS = {
    "sidebar_width": "sidebar_width_{account_id}",
    "setup_selection": "setup_{account_id}_{magic_number}",
    "period_start": "perf_start_date_{account_id}",
    "period_end": "perf_end_date_{account_id}",
    "period_preset": "period_preset_{account_id}",
    "trade_type_filter": "trade_type_filter_{account_id}",
    "min_profit_filter": "min_profit_filter_{account_id}",
    "max_dd_filter": "max_dd_filter_{account_id}",
    "symbols_filter": "symbols_filter_{account_id}",
    "setup_search": "setup_search_{account_id}",
    "show_more_deals": "show_more_deals_{account_id}",
    "chart_colors_enhanced": "chart_colors_enhanced_{account_id}",
    "show_period_analysis": "show_period_analysis_{account_id}"
}

# Period Presets Configuration
PERIOD_PRESETS = {
    "7d": {"days": 7, "label": "Last 7D"},
    "30d": {"days": 30, "label": "Last 30D"},
    "90d": {"days": 90, "label": "Last 90D"},
    "ytd": {"days": None, "label": "YTD"}  # Year to date - special handling
}

# Filter Options
FILTER_OPTIONS = {
    "trade_types": ["Tutti", "Solo Backtest", "Solo Live"],
    "period_quick_buttons": ["7D", "30D", "90D", "YTD"]
}

# Debug Configuration
DEBUG_CONFIG = {
    "max_sample_rows": 100,
    "max_filename_examples": 10,
    "timestamp_corrections_enabled": True,
    "margin_timeline_fix_version": "2025-08-11_simple_timestamp_fix"
}

# Table Configuration
TABLE_CONFIG = {
    "performance_table": {
        "height": 400,
        "column_config": {
            "profit_format": "%.0f €",
            "percentage_format": "%.1f%%",
            "profit_factor_format": "%.2f",
            "date_format": "DD/MM/YYYY HH:mm"
        }
    },
    "deals_table": {
        "default_limit": 50,
        "extended_limit": 100,
        "height": 400
    }
}

# Error Messages
ERROR_MESSAGES = {
    "no_data": "Nessun dato disponibile",
    "no_trades_period": "Nessun trade nel periodo selezionato",
    "no_setup_selected": "Nessun setup selezionato dalla sidebar",
    "invalid_date_range": "Data inizio deve essere ≤ data fine",
    "classification_failed": "Errore nella classificazione dei trade",
    "margin_calculation_failed": "Errore nel calcolo del margine timeline"
}

# Success Messages
SUCCESS_MESSAGES = {
    "cache_cleared": "Cache pulita! I dati saranno aggiornati automaticamente.",
    "all_setups_selected": "Tutti i setup attivati!",
    "no_setups_selected": "Tutti i setup disattivati!",
    "setup_reset": "Reset a default (tutto attivo)!",
    "timestamp_corrections_ok": "Nessuna correzione timestamp necessaria",
    "margin_timeline_fixed": "Piedistallo di margine eliminato!"
}

# Tab Names and Icons
TAB_CONFIG = {
    "tabs": [
        {"name": "Equity/Drawdown/Margin", "icon": "[CHART]"},
        {"name": "Performance Summary", "icon": "[SUMMARY]"},
        {"name": "Setup Performance Table", "icon": "[TABLE]"},
        {"name": "Recent Deals", "icon": "[SEARCH]"}
    ]
}

# Default Values
DEFAULTS = {
    "sidebar_width": DEFAULT_SIDEBAR_WIDTH,
    "period_preset": "30d",
    "setup_selected": True,
    "show_debug": False,
    "expanded_expanders": {
        "period_analysis": True,
        "setup_selection": True,
        "advanced_filters": False,
        "debug_tools": False
    }
}

# Validation Rules
VALIDATION = {
    "sidebar_width": {
        "min": MIN_SIDEBAR_WIDTH,
        "max": MAX_SIDEBAR_WIDTH,
        "step": SIDEBAR_WIDTH_STEP
    },
    "profit_threshold": {
        "min": -100000,
        "max": 100000
    },
    "drawdown_threshold": {
        "min": 0,
        "max": 100000
    }
}

# Helper function to get session key
def get_session_key(key_pattern: str, account_id: str, **kwargs) -> str:
    """
    Generate session state key from pattern and account ID.
    
    Args:
        key_pattern: Pattern from SESSION_KEYS
        account_id: Account identifier
        **kwargs: Additional parameters for key formatting
    
    Returns:
        Formatted session state key
    """
    if key_pattern in SESSION_KEYS:
        return SESSION_KEYS[key_pattern].format(account_id=account_id, **kwargs)
    return f"{key_pattern}_{account_id}"

# Helper function to get default expanded state
def get_default_expanded(expander_name: str) -> bool:
    """Get default expanded state for expander."""
    return DEFAULTS["expanded_expanders"].get(expander_name, False)

# Helper function to validate sidebar width
def validate_sidebar_width(width: int) -> int:
    """Validate and clamp sidebar width to valid range."""
    min_width = VALIDATION["sidebar_width"]["min"]
    max_width = VALIDATION["sidebar_width"]["max"]
    return max(min_width, min(max_width, width))