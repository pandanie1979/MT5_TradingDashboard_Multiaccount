# Current Sprint: R2 — Cache and State Simplification

**STATUS**: `DONE`
**Branch**: `refactor/r2-state`

## Objective
Simplify the application architecture by removing the redundant "pending/applied" state system and the manual update button, ensuring sidebar changes reflect immediately in charts.

## Tasks (from ROADMAP.md)

- [x] **TD-05**: Remove `st.session_state` DataFrame cache from `tabs/performance/main.py`. Rely solely on `@st.cache_data` from `data/loader.py`.
- [x] **TD-06**: Delete the pending/applied dual-state system in `session_helpers.py`.
- [x] **TD-06**: Remove the "Update Metrics" button and "Modifiche in Attesa" info boxes.
- [x] **TD-06**: Update `get_current_period_trades()` to read sidebar state directly.
- [x] **TD-11**: Gate `debug_tools.py` loading behind `DASHBOARD_DEBUG` env var in sidebar `layout.py`.
- [x] **TD-10**: Final fix for encoding garbage in `tabs/tab_performance.py` docstrings (file was already clean ASCII).

## Done When

- [x] No `pending_` or `applied_` prefixed keys are used in `st.session_state`.
- [x] UI updates immediately when changing dates or setups in the sidebar.
- [x] `session_helpers.py` line count reduced significantly (771 → ~280 lines).
- [x] `tab_performance.py` is free of encoding artifacts (was already clean).

## ADRs in Effect
- **ADR-001**: No pending/applied state system.
- **ADR-002**: Single cache layer (`@st.cache_data` only).
- **ADR-006**: Immediate apply on sidebar changes.
