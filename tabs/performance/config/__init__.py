# Configuration module for performance tab
# File: tabs/performance/config/__init__.py

"""
Configuration module for performance tab.
Contains constants, settings, and configuration utilities.
"""

from .constants import (
    DEFAULT_SIDEBAR_WIDTH,
    SIDEBAR_PRESETS,
    SESSION_KEYS,
    PERIOD_PRESETS,
    CHART_CONFIG,
    TABLE_CONFIG,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    get_session_key,
    validate_sidebar_width,
    get_default_expanded
)

__all__ = [
    "DEFAULT_SIDEBAR_WIDTH",
    "SIDEBAR_PRESETS", 
    "SESSION_KEYS",
    "PERIOD_PRESETS",
    "CHART_CONFIG",
    "TABLE_CONFIG",
    "ERROR_MESSAGES",
    "SUCCESS_MESSAGES",
    "get_session_key",
    "validate_sidebar_width",
    "get_default_expanded"
]