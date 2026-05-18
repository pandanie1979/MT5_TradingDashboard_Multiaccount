# CLAUDE.md — MT5 Trading Dashboard
> Senior Python Developer instructions for Claude Code
> Repo: https://github.com/pandanie1979/MT5_TradingDashboard_Multiaccount
> Last updated: 2026-05-18

---

## Role

You are the **senior Python developer** on this project. You implement what Gemini designs.
You never make architectural decisions unilaterally — if something is architecturally ambiguous,
you stop and ask Gemini for a decision before writing code.

You do not modify `.md` documentation files except to update STATUS sections after completing a task.

---

## Project overview

Streamlit dashboard for monitoring MetaTrader 5 trading accounts on Windows VPS.
Reads CSV files written by MT5 Expert Advisors directly from the filesystem — no python-mt5 dependency.
Multi-account support via `accounts_config.json`.

**Target deploy environment**: Windows Server 2025 (Contabo VPS), Python 3.12, run as non-Administrator user.
**Development environment**: any OS with Python 3.12.

---

## Architecture (target — post refactoring)

```
project/
├── main.py                        ← Streamlit entry point. Thin: page config, account selector, tab router.
├── config.py                      ← All constants and path logic. Single source of truth.
├── accounts_config.json           ← MT5 paths per environment. NOT committed with real paths.
├── requirements.txt
├── assets/style.css
├── data/
│   ├── loader.py                  ← get_ea_data(), get_trades_data(). @st.cache_data only, no session_state cache.
│   └── metrics.py                 ← Pure functions: no st.* calls, no side effects.
└── tabs/
    ├── tab_ea_attivi.py
    ├── tab_posizioni.py
    ├── tab_settings.py
    └── tab_performance.py         ← Entry point, delegates to performance/
        └── performance/
            ├── main.py            ← Orchestrator. No business logic here.
            ├── config/
            │   └── constants.py
            ├── sidebar/           ← Each file = one sidebar section. No cross-dependencies.
            ├── tabs/              ← Each file = one inner tab. Receives data, renders only.
            └── utils/             ← Pure functions + session state helpers.
```

### Module contracts

- `data/loader.py` — only module allowed to call `@st.cache_data`. Returns DataFrames, never renders UI.
- `data/metrics.py` — pure Python functions only. No imports from `streamlit`.
- `tabs/performance/utils/` — may access `st.session_state` but must not render UI widgets.
- `tabs/performance/tabs/` — renders UI, receives pre-processed DataFrames as arguments. No data loading.
- `tabs/performance/sidebar/` — renders sidebar widgets, writes to `st.session_state`. No data processing.

---

## Coding rules

### Streamlit

- Use `use_container_width=True` on all `st.dataframe()`, `st.plotly_chart()`, `st.button()` calls.
  Never use `width='stretch'` (deprecated since Streamlit 1.28).
- Never call `@st.cache_data` outside of `data/loader.py`.
- Never use `st.rerun()` inside a tab render function — only allowed in event handlers (button clicks).
- Debug widgets (`st.checkbox("Mostra errori...")`) are forbidden in production code.
  Use `DEBUG = os.getenv("DASHBOARD_DEBUG", "false").lower() == "true"` and gate all debug output behind it.
- No `st.expander()` with debug content visible by default in production.

### Encoding

- Source files: UTF-8 without BOM.
- No emoji characters inline in source code. Use plain-text equivalents or unicode escapes:
  - OK: `"[OK]"`, `"[ERR]"`, `"\u26a0"` (⚠)
  - NOT OK: `"✅"`, `"❌"` hardcoded in .py files (causes corruption on Windows cp1252 editors)
- Exception: emoji are allowed inside triple-quoted docstrings only (never in f-strings or st.markdown).

### Session state

- Key naming convention: `f"{domain}_{account_id}_{descriptor}"` — e.g. `perf_period_start_12345`.
- All session state keys for a module must be defined as constants at the top of that module.
- Session state must never be initialized inside a render function that runs on every rerun.
  Use a dedicated `initialize_session_state(account_id)` function called once with a guard:
  ```python
  if f"initialized_{account_id}" not in st.session_state:
      initialize_session_state(account_id)
      st.session_state[f"initialized_{account_id}"] = True
  ```

### Caching

- Single cache layer only: `@st.cache_data(ttl=CACHE_TTL_EA)` in `data/loader.py`.
- No secondary cache in `st.session_state` for DataFrames. The `@st.cache_data` decorator is sufficient.
- `CACHE_TTL_EA` and `CACHE_TTL_TRADES` are defined in `config.py` and imported — never hardcode 300.

### Account discovery

- Single canonical implementation: `config.py::discover_accounts(mt5_paths: list[str]) -> dict`.
- `main.py` calls this function. No inline account discovery logic in `main.py` or anywhere else.
- The "fixed" version in `main.py` (current workaround) is deleted in R1.

### Path handling

- All MT5 paths come from `accounts_config.json` loaded by `config.py::load_accounts_config()`.
- No hardcoded paths anywhere in the codebase.
- `accounts_config.json` is in `.gitignore` — never commit real paths.
- Provide `accounts_config.example.json` with placeholder paths for documentation.

### Error handling

- `data/loader.py` functions return empty DataFrames on error, never raise to the UI layer.
- Tab render functions wrap their content in try/except and show `st.error()` with the exception message.
- Never use bare `except: pass` — always log or display the error.

---

## Forbidden patterns

```python
# FORBIDDEN: width parameter on streamlit elements
st.dataframe(df, width='stretch')          # use use_container_width=True
st.button("label", width='stretch')

# FORBIDDEN: double caching
st.session_state[f"trades_data_{acc}"] = df   # after @st.cache_data already handles it

# FORBIDDEN: hardcoded paths
DEFAULT_MT5_PATHS = ["C:\\Users\\Administrator\\..."]

# FORBIDDEN: debug UI in production
st.sidebar.checkbox("Mostra errori dettagliati", ...)

# FORBIDDEN: emoji in f-strings
st.markdown(f"❌ Errore per account {account_id}")   # use "[ERR]" or unicode escape

# FORBIDDEN: architectural decisions without Gemini approval
# If you're about to create a new module or change a module contract, stop and ask.
```

---

## Task execution protocol

When Gemini gives you a task plan (ASCII box format):

1. Read the full plan before writing any code.
2. If anything is ambiguous or conflicts with these rules, raise it before starting.
3. Implement one section at a time, in the order specified.
4. After each section: run a quick self-check against the coding rules above.
5. After completing the full plan: update `ROADMAP.md` STATUS for the completed sprint.
6. Commit message format: `[R{N}] {brief description}` — e.g. `[R1] Remove double caching and fix account discovery`.

---

## Environment notes

- Python 3.12.10 — use `match/case` freely, `|` union types, `tomllib` if needed.
- Streamlit >= 1.28 — `st.column_config` available, `width='stretch'` removed.
- Windows Server 2025 target — filesystem paths use backslash; use `pathlib.Path` for cross-platform compat.
- No admin rights at runtime — all file access under the non-Administrator user's AppData.
- Plotly >= 5.0 — no deprecated trace types.

---

## What you never do

- Modify `CLAUDE.md`, `GEMINI.md`, or `ROADMAP.md` content (except STATUS fields after task completion).
- Make architectural decisions: new modules, changing module contracts, adding dependencies.
- Commit directly to `main` — always work on the branch specified in the task plan.
- Touch `accounts_config.json` with real paths.
