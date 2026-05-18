# deploy_dashboard_contabo.ps1
# Deploy MT5 Trading Dashboard su Windows Server 2025 (contabo-win)
# Eseguire come utente normale (pandanie1979), NON come Administrator
# Uso: .\deploy_dashboard_contabo.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Configurazione ────────────────────────────────────────────────────────────
$REPO_URL      = "https://github.com/pandanie1979/MT5_TradingDashboard_Multiaccount.git"
$INSTALL_DIR   = "C:\Projects\MT5Dashboard"
$MT5_PATH      = "C:\Users\pandanie1979\AppData\Roaming\MetaQuotes\Terminal\A08D7ED01C99FCE48D19989B40781EBB\MQL5\Files"
$STREAMLIT_PORT = 8501
$GIT_INSTALLER  = "Git-2.47.1-64-bit.exe"
$GIT_URL        = "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/$GIT_INSTALLER"

# ── Utility ───────────────────────────────────────────────────────────────────
function Write-Step { param($msg) Write-Host "`n[+] $msg" -ForegroundColor Cyan }
function Write-Ok   { param($msg) Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "    WARN: $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "    --> $msg" -ForegroundColor Gray }

# ── 0. Verifica che NON sia Administrator ────────────────────────────────────
Write-Step "Verifica utente"
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal   = New-Object Security.Principal.WindowsPrincipal($currentUser)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warn "Stai eseguendo come Administrator."
    Write-Warn "Raccomandato: esegui come utente normale (pandanie1979)."
    $answer = Read-Host "    Continuare comunque? [y/N]"
    if ($answer -ne "y" -and $answer -ne "Y") { exit 0 }
}
Write-Ok "Utente: $($currentUser.Name)"

# ── 1. Verifica Python ────────────────────────────────────────────────────────
Write-Step "Verifica Python"
$pyExe = "C:\Python312\python.exe"
if (-not (Test-Path $pyExe)) {
    Write-Error "Python non trovato in $pyExe. Esegui prima install_python_contabo.ps1"
    exit 1
}
$pyVer = & $pyExe --version 2>&1
Write-Ok $pyVer

# ── 2. Installa Git se non presente ──────────────────────────────────────────
Write-Step "Verifica Git"
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Info "Git non trovato — download installer..."
    $gitTmp = "$env:TEMP\$GIT_INSTALLER"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $GIT_URL -OutFile $gitTmp -UseBasicParsing
    Write-Info "Installazione Git (silenziosa)..."
    # Installazione silente — aggiunge git al PATH di sistema, richiede Admin
    # Se sei utente normale, Git viene installato per l'utente corrente
    $gitArgs = "/VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS " +
               "/RESTARTAPPLICATIONS /COMPONENTS=`"icons,ext\reg\shellhere,assoc,assoc_sh`""
    Start-Process -FilePath $gitTmp -ArgumentList $gitArgs -Wait
    Remove-Item $gitTmp -Force
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path","User")
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitCmd) {
        Write-Warn "Git installato ma non trovato nel PATH. Apri una nuova shell e riesegui lo script."
        exit 1
    }
}
$gitVer = & git --version 2>&1
Write-Ok $gitVer

# ── 3. Crea cartella Projects se non esiste ───────────────────────────────────
Write-Step "Preparazione cartella di installazione"
$projectsDir = Split-Path $INSTALL_DIR -Parent
if (-not (Test-Path $projectsDir)) {
    New-Item -ItemType Directory -Path $projectsDir | Out-Null
    Write-Ok "Creata: $projectsDir"
}

# ── 4. Clone o pull del repo ──────────────────────────────────────────────────
Write-Step "Repository GitHub"
if (Test-Path "$INSTALL_DIR\.git") {
    Write-Info "Repo gia' presente — eseguo git pull..."
    Set-Location $INSTALL_DIR
    & git pull origin main
    Write-Ok "Repo aggiornato"
} else {
    Write-Info "Clone da $REPO_URL..."
    & git clone $REPO_URL $INSTALL_DIR
    Set-Location $INSTALL_DIR
    Write-Ok "Clone completato in $INSTALL_DIR"
}

# ── 5. Crea virtual environment ───────────────────────────────────────────────
Write-Step "Virtual environment"
$venvPath = "$INSTALL_DIR\.venv"
if (-not (Test-Path "$venvPath\Scripts\python.exe")) {
    & $pyExe -m venv $venvPath
    Write-Ok "venv creato in $venvPath"
} else {
    Write-Ok "venv gia' presente"
}
$venvPython = "$venvPath\Scripts\python.exe"
$venvPip    = "$venvPath\Scripts\pip.exe"

# ── 6. Installa dipendenze ────────────────────────────────────────────────────
Write-Step "Installazione dipendenze (requirements.txt)"
& $venvPip install --upgrade pip --quiet
& $venvPip install -r "$INSTALL_DIR\requirements.txt"
Write-Ok "Dipendenze installate"

# ── 7. Configura accounts_config.json ─────────────────────────────────────────
Write-Step "Configurazione accounts_config.json"
$configDst = "$INSTALL_DIR\accounts_config.json"
$configSrc = "$INSTALL_DIR\accounts_config.example.json"

# Verifica che il path MT5 esista
if (-not (Test-Path $MT5_PATH)) {
    Write-Warn "Path MT5 non trovato: $MT5_PATH"
    Write-Warn "Verifica che MT5 demo sia stato avviato almeno una volta per creare la cartella."
    Write-Warn "Il file accounts_config.json non sara' generato automaticamente."
    Write-Warn "Crea manualmente $configDst dopo aver verificato il path."
} else {
    Write-Ok "Path MT5 verificato: $MT5_PATH"
    
    # Genera accounts_config.json con il path corretto
    $config = @{
        mt5_paths    = @($MT5_PATH)
        version      = "1.0"
        last_updated = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    }
    $config | ConvertTo-Json -Depth 3 | Set-Content -Path $configDst -Encoding UTF8
    Write-Ok "accounts_config.json generato con path contabo-win"
}

# ── 8. Verifica che accounts_config.json non sia tracciato da git ─────────────
Write-Step "Verifica .gitignore"
$gitignorePath = "$INSTALL_DIR\.gitignore"
if (Test-Path $gitignorePath) {
    $content = Get-Content $gitignorePath -Raw
    if ($content -notmatch "accounts_config\.json") {
        Add-Content -Path $gitignorePath -Value "`naccounts_config.json"
        Write-Ok "accounts_config.json aggiunto a .gitignore"
    } else {
        Write-Ok "accounts_config.json gia' in .gitignore"
    }
} else {
    "accounts_config.json" | Set-Content -Path $gitignorePath -Encoding UTF8
    Write-Ok ".gitignore creato con accounts_config.json"
}

# ── 9. Crea script di avvio ───────────────────────────────────────────────────
Write-Step "Creazione script di avvio"
$launchScript = "$INSTALL_DIR\start_dashboard.ps1"
@"
# start_dashboard.ps1 — Avvia MT5 Trading Dashboard
# Eseguire come utente normale dalla cartella $INSTALL_DIR
Set-Location "$INSTALL_DIR"
& "$venvPath\Scripts\streamlit.exe" run main.py --server.port $STREAMLIT_PORT --server.headless true
"@ | Set-Content -Path $launchScript -Encoding UTF8
Write-Ok "Script di avvio: $launchScript"

# ── 10. Test import Streamlit ─────────────────────────────────────────────────
Write-Step "Test dipendenze Python"
$testResult = & $venvPython -c "import streamlit, pandas, plotly; print('OK')" 2>&1
if ($testResult -eq "OK") {
    Write-Ok "streamlit, pandas, plotly importati correttamente"
} else {
    Write-Warn "Errore import: $testResult"
}

# ── 11. Riepilogo finale ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  DEPLOY COMPLETATO" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Installazione : $INSTALL_DIR" -ForegroundColor White
Write-Host "  MT5 path      : $MT5_PATH" -ForegroundColor White
Write-Host "  Porta         : $STREAMLIT_PORT" -ForegroundColor White
Write-Host ""
Write-Host "  Per avviare la dashboard:" -ForegroundColor White
Write-Host "    cd $INSTALL_DIR" -ForegroundColor Gray
Write-Host "    .\start_dashboard.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  Oppure direttamente:" -ForegroundColor White
Write-Host "    .venv\Scripts\streamlit.exe run main.py --server.port $STREAMLIT_PORT" -ForegroundColor Gray
Write-Host ""
Write-Host "  Dashboard disponibile su: http://localhost:$STREAMLIT_PORT" -ForegroundColor Green
Write-Host "  Da remoto (RDP tunnel):   http://127.0.0.1:$STREAMLIT_PORT" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
