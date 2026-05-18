# MT5 Trading Dashboard - Performance Tab (Refactored Entry Point)
# File: tabs/tab_performance.py
# Version: 1.5.0 - Modular Architecture
# Generated: September 2025

"""
Performance tab entry point - now using modular architecture.
This file maintains backward compatibility while delegating to modular components.
"""

# Import from the new modular performance system
from tabs.performance import render as performance_render

def render(account_id: str, account_path: str, account_info: dict):
    """
    Performance tab render function - delegated to modular system.
    
    This function maintains backward compatibility with the existing application
    while using the new modular architecture under the hood.
    
    Args:
        account_id: Account identifier
        account_path: Path to MT5 data
        account_info: Account information dict with color, status, etc.
    """
    # Delegate to the new modular performance system
    performance_render(account_id, account_path, account_info)


# Backward compatibility aliases
render_performance_tab = render

# Module metadata
__version__ = "1.5.0"
__refactored__ = "September 2025"
__migration_status__ = "Complete - Using modular architecture"

# Development notes for future maintenance:
"""
REFACTORING COMPLETED - v1.4 -> v1.5

This file now acts as a thin compatibility layer that delegates to the 
new modular performance system located in tabs/performance/.

The original 2500+ line monolithic file has been successfully broken down into:

- Configuration: tabs/performance/config/
- Utilities: tabs/performance/utils/  
- Sidebar: tabs/performance/sidebar/
- Main Tabs: tabs/performance/tabs/
- Entry Point: tabs/performance/main.py

Benefits of the new architecture:
- Modular components for easier maintenance
- Clear separation of concerns
- Improved testability
- Better code reusability
- Easier feature development
- Reduced complexity per file

For future development:
- Add new features in appropriate modules
- Extend utils/ for new processing functions
- Add new tabs in tabs/ directory
- Update config/constants.py for new settings
"""