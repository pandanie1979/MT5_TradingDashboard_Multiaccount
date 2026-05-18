# ROADMAP.md — MT5 Trading Dashboard Refactoring
> Repo: https://github.com/pandanie1979/MT5_TradingDashboard_Multiaccount
> Started: 2026-05-18 | Workflow: Gemini (architect) → Claude Code (implementation)

---

## Current sprint

**R3 — UI polish and production hardening** | STATUS: `READY`

---

## Technical debt register
> Source: architectural assessment 2026-05-18

| ID  | Severity | Description | Sprint |
|-----|----------|-------------|--------|
| TD-01 | CRITICAL | Hardcoded paths to `Administrator` user in `config.py` and `accounts_config.json` | R1 |
| TD-02 | CRITICAL | Encoding corruption in `tab_posizioni.py` and `data/loader.py` (UTF-8 read as cp1252) | R1 |
| TD-03 | HIGH | `width='stretch'` deprecated parameter on `st.dataframe()`, `st.button()`, `st.plotly_chart()` | R1 |
| TD-04 | HIGH | Account discovery logic duplicated in 3 places (`config.py`, `main.py`, `loader.py`) — one copy has known bug | R1 |
| TD-05 | HIGH | Double caching: `@st.cache_data` + `st.session_state` DataFrame cache in `performance/main.py` | R2 |
| TD-06 | HIGH | Pending/applied dual-state system in `session_helpers.py` (~27KB, ~40% of codebase) — over-engineered for single-user tool | R2 |
| TD-07 | MEDIUM | Debug widgets (`st.checkbox("Mostra errori...")`) active in production sidebar and inline in `loader.py` | R1 |
| TD-08 | MEDIUM | `CACHE_TTL_EA` defined in `config.py` but not passed to `@st.cache_data` decorator | R1 |
| TD-09 | MEDIUM | `accounts_config.json` committed with real filesystem paths — should be in `.gitignore` | R1 |
| TD-10 | LOW | `tab_performance.py` thin wrapper has encoding garbage in docstring comments | R2 |
| TD-11 | LOW | `debug_tools.py` (13KB) loaded unconditionally in sidebar — should be env-gated | R2 |

---

## Sprint plan

---

### R1 — Foundation cleanup (COMPLETED)
**STATUS**: `DONE`
**Branch**: `refactor/r1-foundation`
**Scope**: Blockers for deployment + single-account discovery + encoding fix.
**ADRs in effect**: ADR-003, ADR-004, ADR-005

#### Tasks
- [ ] TD-09: Add `accounts_config.json` to `.gitignore`, create `accounts_config.example.json`
- [ ] TD-01: Remove all hardcoded paths from `config.py DEFAULT_MT5_PATHS`
- [ ] TD-03: Replace all `width='stretch'` with `use_container_width=True` (global grep + replace)
- [ ] TD-08: Pass `ttl=CACHE_TTL_EA` / `ttl=CACHE_TTL_TRADES` to all `@st.cache_data` decorators in `loader.py`
- [ ] TD-04: Consolidate account discovery into `config.py::discover_accounts()`, delete workaround in `main.py`
- [ ] TD-02: Fix encoding corruption in `tab_posizioni.py` and `data/loader.py` — rewrite all broken non-ASCII
- [ ] TD-07: Gate all debug widgets behind `DASHBOARD_DEBUG` env var in `loader.py` and `tabs/`

**Done when**:
- [ ] `accounts_config.json` not tracked by git
- [ ] `accounts_config.example.json` present with placeholder paths
- [ ] No `width='stretch'` string anywhere in codebase (`grep -r "width='stretch'"` returns empty)
- [ ] No hardcoded `Administrator` or `Daniele` paths in any `.py` file
- [ ] No encoding garbage characters (`ðŸ`, `â‚¬`, `Ã¢`) in any `.py` file
- [ ] `@st.cache_data(ttl=CACHE_TTL_EA)` used consistently — no bare `@st.cache_data`
- [ ] Single `discover_accounts()` function in `config.py` — no duplicate in `main.py`
- [ ] App starts and finds MT5 account on contabo-win after updating `accounts_config.json`

---

### R2 — Cache and state simplification
**STATUS**: `READY`
**Branch**: `refactor/r2-state`
**Scope**: Eliminate double caching and pending/applied system.
**ADRs in effect**: ADR-001, ADR-002, ADR-006

#### Tasks
- [ ] TD-05: Remove session_state DataFrame cache from `performance/main.py` — rely solely on `@st.cache_data`
- [ ] TD-06: Delete pending/applied system from `session_helpers.py`:
  - Remove: `detect_pending_changes`, `apply_pending_changes`, `get_pending_*`, `apply_pending_*`
  - Remove: `render_pending_state_view`, `render_pending_changes_summary`, `render_update_metrics_button`
  - Remove: all `pending_*` session state keys
  - Rewrite: sidebar writes directly to applied state; `get_current_period_trades()` reads it immediately
- [ ] TD-06: Remove "Update Metrics" button from `performance/main.py` header
- [ ] TD-06: Remove `lightweight=True` parameter from `render_main_tabbed_area()`
- [ ] TD-10: Fix encoding garbage in `tab_performance.py` docstring
- [ ] TD-11: Gate `debug_tools.py` loading behind `DASHBOARD_DEBUG` env var in sidebar `layout.py`

**Done when**:
- [ ] No `pending_` prefixed keys written to `st.session_state` anywhere
- [ ] No "Update Metrics" button in UI
- [ ] `session_helpers.py` reduced by >50% in line count
- [ ] Sidebar period/setup changes reflect immediately in charts without any button click
- [ ] `performance/main.py` has no `st.session_state[cache_key]` DataFrame assignments

---

### R3 — UI polish and production hardening
**STATUS**: `READY`
**Branch**: `refactor/r3-polish`
**Scope**: Production-ready output. No structural changes.
**ADRs in effect**: all

#### Tasks
- [ ] Replace remaining inline emoji in all `.py` files with plain text or unicode escapes
- [ ] Add `accounts_config.example.json` documentation with contabo-win path template
- [ ] Add `systemd`-compatible startup script for future Linux port (optional, low priority)
- [ ] Update `README.md` with correct install instructions, architecture diagram, env var docs
- [ ] Final pass: `grep -r "st.sidebar.checkbox"` — confirm zero debug checkboxes remain
- [ ] requirements.txt: pin exact versions (`streamlit==1.45.x`, `pandas==2.x.x`, `plotly==5.x.x`)

**Done when**:
- [ ] `README.md` documents: install, `accounts_config.json` setup, `DASHBOARD_DEBUG` env var
- [ ] Requirements pinned to exact versions confirmed working on Python 3.12.10 / Windows Server 2025
- [ ] Zero `st.sidebar.checkbox` calls for debug in production path

---

### R4 — Feature development (post-refactoring)
**STATUS**: `PLANNED`
**Scope**: New features. To be designed by Gemini after R3 complete.

#### Candidate features (not yet designed)
- Auto-refresh timer (configurable interval, no manual cache clear button)
- Export to CSV / Excel for performance summary
- Per-setup P&L sparklines in EA Attivi tab
- Multi-account aggregated view (cross-account equity curve)
- Alert system: EA inactive with open position → notification (email or Telegram)

---

## Deployment checklist (post R1)

For initial deploy on contabo-win:

```
[ ] Python 3.12.10 installed (system-wide)
[ ] git clone https://github.com/pandanie1979/MT5_TradingDashboard_Multiaccount
[ ] cd MT5_TradingDashboard_Multiaccount
[ ] python -m venv .venv
[ ] .venv\Scripts\Activate.ps1
[ ] pip install -r requirements.txt
[ ] copy accounts_config.example.json accounts_config.json
[ ] edit accounts_config.json — insert correct MT5 path for contabo-win user
[ ] streamlit run main.py --server.port 8501
[ ] verify: browser → http://localhost:8501
[ ] configure as Windows scheduled task or service for auto-start
```

MT5 path to find on contabo-win:
```
%APPDATA%\MetaQuotes\Terminal\<HASH>\MQL5\Files
```
Hash is 32-char string. Find it by opening MT5 → Tools → Options → Expert Advisors → check the data folder path.

---

## Architectural decision log

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-001 | No pending/applied state system | ACTIVE |
| ADR-002 | Single cache layer (`@st.cache_data` only) | ACTIVE |
| ADR-003 | Single account discovery in `config.py` | ACTIVE |
| ADR-004 | No runtime debug UI — env var gate | ACTIVE |
| ADR-005 | UTF-8 source files, no inline emoji in code | ACTIVE |
| ADR-006 | Immediate apply on sidebar changes | ACTIVE |

---

*ROADMAP.md — v1.0 — 2026-05-18*
*Update STATUS fields after each sprint completion. Do not modify ADR entries without Gemini approval.*
