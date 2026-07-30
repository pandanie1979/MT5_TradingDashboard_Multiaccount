$procs = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine -match 'MT5Dashboard' -and
    ($_.Name -eq 'streamlit.exe' -or $_.Name -eq 'python.exe')
}

if (-not $procs) {
    Write-Host "No MT5 Dashboard process found running."
} else {
    foreach ($p in $procs) {
        Write-Host "Stopping $($p.Name) (PID $($p.ProcessId))"
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Done."
}
