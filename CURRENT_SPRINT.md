# Current Sprint: R1 — Foundation Cleanup

**STATUS**: `IN_PROGRESS`
**Branch**: `refactor/r1-foundation`

## Objective
Clean up technical debt related to hardcoded paths, deprecated UI parameters, and duplicate logic to ensure a stable foundation for further refactoring.

## Tasks (from ROADMAP.md)

- [x] **TD-09**: Add `accounts_config.json` to `.gitignore`, create `accounts_config.example.json`.
- [x] **TD-01**: Remove all hardcoded paths from `config.py DEFAULT_MT5_PATHS`.
- [x] **TD-03**: Replace all `width='stretch'` with `use_container_width=True` across the codebase.
- [ ] **TD-08**: Pass `ttl=CACHE_TTL_EA` / `ttl=CACHE_TTL_TRADES` to all `@st.cache_data` decorators in `loader.py`.
- [ ] **TD-04**: Consolidate account discovery into `config.py::discover_accounts()`, delete workaround in `main.py`.
- [ ] **TD-02**: Fix encoding corruption in `tab_posizioni.py` and `data/loader.py` (rewrite broken non-ASCII characters).
- [ ] **TD-07**: Gate all debug widgets behind `DASHBOARD_DEBUG` env var in `loader.py` and `tabs/`.

## Done When

- [x] `accounts_config.json` is ignored by git.
- [x] `accounts_config.example.json` exists with placeholder values.
- [x] `grep -r "width='stretch'"` returns no results.
- [ ] No hardcoded personal paths (e.g., "Administrator") remain in code. (partial: config.py clean; main.py workaround deferred to TD-04)
- [ ] Source code is free of encoding artifacts (e.g., `ðŸ`).
- [ ] The application starts and correctly discovers accounts using the unified logic in `config.py`.

## ADRs in Effect
- **ADR-003**: Single account discovery in `config.py`.
- **ADR-004**: No runtime debug UI — env var gate.
- **ADR-005**: UTF-8 source files, no inline emoji in code.