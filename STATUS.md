# Project Status Report: MT5 Trading Dashboard
**Date**: 2026-05-18
**Target Environment**: Windows Server 2025 (Contabo VPS)
**Refactoring Status**: 100% COMPLETE

## 1. Architectural Readiness
The application has been fully refactored into a modular architecture.
- **UI Reactivity**: The "Pending/Applied" state system has been removed. All sidebar filters apply instantly (ADR-001, ADR-006).
- **State Management**: Session state is now minimal and initialized per-account only once per session.
- **Global Portfolio**: A new "Global" tab aggregates P&L and KPIs across all discovered accounts (R6).
- **Encoding**: All source files are UTF-8 compliant with ADR-005 (Unicode escapes for symbols).

## 2. Performance & Caching
- **Single Layer Cache**: Double caching has been eliminated. Data is managed exclusively by `@st.cache_data` in `data/loader.py` (ADR-002).
- **TTL Strategy**: EA data and Trade data both use a 300-second (5 min) TTL defined in `config.py`.
- **Auto-Refresh**: The dashboard automatically reruns every 300 seconds to reflect new CSV data without user interaction (ADR-008).

## 3. Migration & Deployment Specs
### Prerequisites
- **Python**: 3.12.x (Tested on 3.12.10).
- **Dependencies**: Pinned in `requirements.txt` (`streamlit==1.45.1`, `pandas==2.2.3`).

### Configuration Workflow
1. **Accounts**: Copy `accounts_config.example.json` to `accounts_config.json`.
2. **Paths**: Insert the `MQL5\Files` paths for each MT5 terminal instance.
3. **Discovery**: The app automatically identifies Account IDs from filename patterns (e.g., `123456_...`).

### Environment Variables
- `DASHBOARD_DEBUG`: Set to `true` to show file pattern analysis and detailed error logs. Default is `false` (Production mode).

## 4. Key Files Locations
| Component | File Path |
|-----------|-----------|
| Entry Point | `main.py` |
| Data Logic | `data/loader.py` |
| KPI Logic | `tabs/performance/utils/metrics.py` |
| Global View | `tabs/tab_global_analytics.py` |
| Config | `config.py` |
| Secrets | `accounts_config.json` (Git Ignored) |

## 5. Known Constraints & Backlog
- **CSV Dependency**: The dashboard relies on MT5 EAs correctly writing CSVs to the local disk.
- **VPS Safety**: Refresh interval is capped at 60s minimum to prevent CPU spikes on the VPS.
- **Future Features**:
    - Alert System (EA Inactivity/Notifications).
    - P&L Sparklines in the Active EA tab.

---
**Migration Verdict**: READY FOR DEPLOYMENT.
The codebase is clean, technical debt is resolved, and modular contracts are enforced.