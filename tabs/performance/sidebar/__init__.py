# Sidebar components module for performance tab
# File: tabs/performance/sidebar/__init__.py

"""
Sidebar components module for performance tab.
Contains layout, account info, controls, and filter components.
"""

from .layout import render_scrollable_sidebar, render_sidebar_width_control
from .account_info import render_account_info_header, get_account_summary_data
from .period_selection import render_period_selection_enhanced, get_period_info_for_display
from .setup_selection import render_setup_selection_clean, get_setup_selection_summary
from .filters import render_advanced_filters_panel, get_filter_statistics, validate_filters
from .debug_tools import render_debug_tools_panel, render_advanced_debug_analysis

__all__ = [
    # Layout
    "render_scrollable_sidebar",
    "render_sidebar_width_control",
    
    # Account Info
    "render_account_info_header",
    "get_account_summary_data",
    
    # Period Selection
    "render_period_selection_enhanced", 
    "get_period_info_for_display",
    
    # Setup Selection
    "render_setup_selection_clean",
    "get_setup_selection_summary",
    
    # Filters
    "render_advanced_filters_panel",
    "get_filter_statistics",
    "validate_filters",
    
    # Debug Tools
    "render_debug_tools_panel",
    "render_advanced_debug_analysis"
]