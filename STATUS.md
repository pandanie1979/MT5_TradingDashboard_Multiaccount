# Project Status Report: MT5 Trading Dashboard
**Date**: 2026-07-30 (last hotfix pass; refactoring section below dated 2026-05-18)
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

## 6. 2026-07-30 hotfix pass (post-refactor)

Cross-checked against `portfolio_governance`'s dashboard integration data contract
(sibling project, same VPS, sizes risk for the same EAs this dashboard monitors):

- **Monitored accounts changed**: `accounts_config.json` (local, git-ignored) now watches
  the sensor account (login `5977682`) and the real account (login `955617`). The demo
  actor account was dropped — permanently decommissioned 2026-07-29/30, frozen, no longer
  live. See `ROADMAP.md`'s Hotfix log for the full account-ID mapping.
- **Encoding bug fixed**: `SUPPORTED_ENCODINGS` in `config.py` tried `utf-16` before
  `utf-8`. EAMonitor CSVs are UTF-8 — decoding them as `utf-16` was succeeding silently
  with garbled output rather than raising, a TD-02-class regression. Reordered to try
  `utf-8` first; trade CSVs (genuinely UTF-16LE) are unaffected since a real UTF-16 BOM
  fails a `utf-8` decode immediately and falls through correctly.
- **BOM tolerance fixed**: `load_accounts_config()` now opens `accounts_config.json` with
  `encoding='utf-8-sig'`, so a stray UTF-8 BOM (e.g. from a Windows text editor) no longer
  causes a silent fallback to blind auto-discovery of every terminal folder on disk.
- **Repo ACL fixed**: every pre-existing tracked file had an Administrators/SYSTEM-only
  write ACL (consistent with the repo having been cloned from an elevated session) —
  recursively granted the runtime user Modify rights so non-elevated writes (including the
  dashboard's own Settings-tab `save_accounts_config()`) work correctly.
- **New tooling**: `stop_dashboard.ps1` (repo root) plus a Desktop `.bat` launcher, to stop
  the running dashboard by matching `MT5Dashboard` in the process command line.
- Verified via direct `discover_accounts_from_paths()` / `get_ea_data()` /
  `get_trades_data()` calls against the real terminal folders, and a live `streamlit run`
  smoke test (HTTP 200, no server errors).

---
**Migration Verdict**: READY FOR DEPLOYMENT.
The codebase is clean, technical debt is resolved, and modular contracts are enforced.