# MT5 Trading Dashboard

Dashboard interattiva per monitoraggio trading MetaTrader 5.

## Features
- Multi-account support
- Performance analysis
- Equity/Drawdown charts
- Setup management

## Installation
```bash
pip install -r requirements.txt
streamlit run main.py
```

## Deployment

### accounts_config.json

Copy `accounts_config.example.json` to `accounts_config.json` and replace the placeholder paths with the actual MT5 Terminal data folders on the target machine.

Each entry is the `MQL5\Files` directory of a MetaTrader 5 terminal instance. On Windows the default path is:

```
C:\Users\<USERNAME>\AppData\Roaming\MetaQuotes\Terminal\<TERMINAL_HASH>\MQL5\Files
```

`<TERMINAL_HASH>` is the 32-character hex identifier assigned by MT5 to each terminal installation. It can be found inside the MT5 terminal under **File → Open Data Folder**.

`accounts_config.json` is listed in `.gitignore` — never commit real paths.

### Debug mode

Set the environment variable `DASHBOARD_DEBUG=true` to enable debug panels (margin analysis, file pattern inspection, timestamp correction details). When unset or set to any other value, all debug output is hidden.

**Windows CMD:**
```cmd
set DASHBOARD_DEBUG=true
streamlit run main.py
```

**Windows PowerShell:**
```powershell
$env:DASHBOARD_DEBUG = "true"
streamlit run main.py
```

**Linux / macOS:**
```bash
DASHBOARD_DEBUG=true streamlit run main.py