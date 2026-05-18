# MT5 Trading Dashboard — Multi-Account Monitor

A modular Streamlit dashboard for real-time monitoring of MetaTrader 5 trading accounts
on a Windows VPS. Data is read directly from CSV files written by MT5 Expert Advisors
— no MetaTrader API dependency, no broker connection at runtime.

**Project Status**: See [STATUS.md](STATUS.md) for the current readiness report.

---

## Architectural Principles

| Principle | Implementation |
|-----------|---------------|
| Modular tabs | Each tab is an independent module; no cross-tab imports. |
| Single-layer cache | `@st.cache_data` in `data/loader.py` only. No secondary session-state cache. |
| Pure data layer | `data/metrics.py` contains pure functions: no `st.*` calls, no side effects. |
| Config as single source of truth | All constants and path logic live in `config.py`. |
| UTF-8 / no inline emoji | ADR-005: source files use Unicode escapes (`⚠`) not raw emoji characters. |

---

## Project Structure

```
MT5_TradingDashboard_Multiaccount/
|
+-- main.py                          Entry point: page config, account selector, tab router.
+-- config.py                        All constants, TTL values, path helpers.
+-- accounts_config.json             MT5 paths per machine  [git-ignored]
+-- accounts_config.example.json     Template for accounts_config.json
+-- requirements.txt                 Pinned dependencies
+-- assets/
|   +-- style.css
+-- data/
|   +-- loader.py                    get_ea_data(), get_trades_data() with @st.cache_data
|   +-- metrics.py                   Pure KPI functions (no Streamlit imports)
+-- tabs/
    +-- tab_ea_attivi.py             Active EA monitor tab
    +-- tab_posizioni.py             Open positions tab
    +-- tab_settings.py              Account path settings tab
    +-- tab_global_analytics.py      Cross-account portfolio aggregator (R6)
    +-- tab_performance.py           Performance tab entry point
    +-- performance/
        +-- main.py                  Orchestrator (no business logic)
        +-- config/
        |   +-- constants.py
        +-- sidebar/                 One file per sidebar section
        +-- tabs/                    One file per inner tab (receives DataFrames, renders only)
        +-- utils/                   Pure functions + session-state helpers
```

---

## Operational Logic

### CSV-Driven Data Model

MT5 Expert Advisors write two types of CSV files to their terminal's `MQL5\Files` folder:

| File Pattern | Content |
|---|---|
| `EAMon_*.csv` | EA heartbeat: status, symbol, magic number, margin. |
| `<id>_*_*_*_*.csv` | Trade history: deal records for a single account. |

The dashboard reads these files directly from the filesystem. No broker API or MT5 Python
library is involved. This makes the dashboard safe to deploy as a non-Administrator service.

### Account Discovery

`config.py::discover_accounts_from_paths()` scans each configured `MQL5\Files` path and
extracts Account IDs from the filename prefix (e.g. `123456_...`). No manual account
registration is needed.

### Auto-Refresh

The dashboard calls `st.rerun()` on a 300-second timer (`DASHBOARD_REFRESH_INTERVAL` in
`config.py`). This matches the cache TTL so every refresh fetches fresh data from disk.
The minimum interval is capped at 60 seconds to prevent CPU spikes on the VPS.

### Caching

`data/loader.py` wraps all file reads with `@st.cache_data(ttl=CACHE_TTL_EA)` (300 s).
Between refreshes, all tabs read from the in-memory cache — disk I/O occurs at most once
per TTL window per account.

---

## Deployment (Windows Server 2025 VPS)

### Prerequisites

- Python 3.12.x
- pip packages from `requirements.txt` (pinned versions)

### Installation

```powershell
git clone https://github.com/pandanie1979/MT5_TradingDashboard_Multiaccount
cd MT5_TradingDashboard_Multiaccount
pip install -r requirements.txt
```

### Account Configuration

1. Copy the example config:
   ```powershell
   Copy-Item accounts_config.example.json accounts_config.json
   ```

2. Open `accounts_config.json` and replace placeholder paths with the actual
   `MQL5\Files` directories for each MT5 terminal on the machine.

   The terminal data folder can be found inside MT5 via **File → Open Data Folder**.
   The default path pattern is:
   ```
   C:\Users\<USERNAME>\AppData\Roaming\MetaQuotes\Terminal\<HASH>\MQL5\Files
   ```

3. `accounts_config.json` is in `.gitignore`. Never commit real paths.

### Running the Dashboard

```powershell
streamlit run main.py
```

The dashboard will be available at `http://localhost:8501` by default.

### Debug Mode

Set `DASHBOARD_DEBUG=true` to enable file-pattern analysis and detailed error output.
In production, leave this unset (defaults to `false`).

```powershell
# PowerShell
$env:DASHBOARD_DEBUG = "true"
streamlit run main.py
```

```cmd
:: CMD
set DASHBOARD_DEBUG=true
streamlit run main.py
```

---

## Key Configuration Values (`config.py`)

| Constant | Default | Description |
|---|---|---|
| `CACHE_TTL_EA` | 300 s | Cache TTL for EA monitor data |
| `CACHE_TTL_TRADES` | 300 s | Cache TTL for trade history |
| `DASHBOARD_REFRESH_INTERVAL` | 300 s | Auto-rerun interval |
| `MAX_RECENT_DEALS` | 50 | Max deals shown in recent deals table |

---

## Development Notes

- Branch strategy: feature work on named branches; never commit directly to `main`.
- Architectural decisions are tracked in `GEMINI.md` (ADR log).
- Coding rules and module contracts are defined in `CLAUDE.md`.
