# Tab components module for performance tab main area
# File: tabs/performance/tabs/__init__.py

"""
Tab components module for performance tab main area.
Contains charts, summary, table, and deals tab components.
"""

from .charts_tab import render_charts_tab, export_chart_data
from .summary_tab import render_performance_summary_tab, export_summary_metrics
from .table_tab import render_performance_table_tab, get_table_statistics
from .deals_tab import render_recent_deals_tab, export_deals_data

__all__ = [
    # Charts Tab
    "render_charts_tab",
    "export_chart_data",
    
    # Summary Tab
    "render_performance_summary_tab",
    "export_summary_metrics",
    
    # Table Tab
    "render_performance_table_tab",
    "get_table_statistics",
    
    # Deals Tab
    "render_recent_deals_tab",
    "export_deals_data"
]