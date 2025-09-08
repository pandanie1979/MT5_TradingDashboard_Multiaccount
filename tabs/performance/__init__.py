# MT5 Trading Dashboard - Performance Module Initialization
# File: tabs/performance/__init__.py
# Generated: September 2025
# Refactoring: v1.4 -> v1.5

"""
Performance tab module for MT5 Trading Dashboard.
Provides modular components for comprehensive trading analysis.
"""

from .main import render, render_performance_tab

__version__ = "1.5.0"
__author__ = "MT5 Dashboard Development Team"

# Public API
__all__ = [
    "render",
    "render_performance_tab"  # Backward compatibility
]