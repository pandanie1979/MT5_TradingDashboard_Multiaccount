# Current Sprint: R3 — UI Polish and Production Hardening

**STATUS**: `READY`
**Branch**: `refactor/r3-polish`

## Objective
Finalize the application for production deployment. This involves removing all raw emoji from source code to prevent encoding issues on Windows, pinning dependencies for stability, and finalizing deployment documentation.

## Tasks (from ROADMAP.md)

- [ ] **ADR-005 Compliance**: Global scan to replace raw emoji characters in all `.py` files with plain text or Unicode escapes.
- [ ] **Documentation**: Update `README.md` with Windows Server 2025 installation, `accounts_config.json` setup, and `DASHBOARD_DEBUG` usage.
- [ ] **Config Examples**: Update `accounts_config.example.json` with a template for the Contabo VPS path structure.
- [ ] **Final Pass**: Search for any remaining `st.sidebar.checkbox` used for debug that is not gated by `DASHBOARD_DEBUG`.
- [ ] **Pin Dependencies**: Update `requirements.txt` with exact versions (`streamlit==1.40.1`, `pandas==2.2.3`, `plotly==5.24.1`).

## Done When

- [ ] `requirements.txt` contains pinned versions.
- [ ] No raw emoji characters found in source code via regex search.
- [ ] `README.md` contains clear deployment instructions for Windows.
- [ ] `ROADMAP.md` shows R3 as COMPLETE.

## ADRs in Effect
- **ADR-004**: No runtime debug UI — env var gate.
- **ADR-005**: UTF-8 source files, no inline emoji in code.
