# PowerShell Script per ripristinare emoji corrotte - SINTASSI CORRETTA
# Esegui nel terminal VS Code

Write-Host "=== Ripristino Emoji MT5 Dashboard ===" -ForegroundColor Cyan

# Mappatura delle emoji più comuni usate nel dashboard
$emojiMap = @{
    "ðŸ"Š" = "📊"
    "ðŸ"ˆ" = "📈"
    "ðŸ"‰" = "📉"
    "ðŸ"…" = "📅"
    "ðŸ"‹" = "📋"
    "âš™ï¸" = "⚙️"
    "ðŸ'" = "💰"
    "ðŸŽ¯" = "🎯"
    "âœ…" = "✅"
    "â­" = "❌"
    "âš ï¸" = "⚠️"
    "ðŸ"" = "🔍"
    "ðŸ§¹" = "🧹"
    "ðŸ"„" = "🔄"
    "ðŸŽ‰" = "🎉"
    "ðŸš€" = "🚀"
    "ðŸ"§" = "🔧"
    "ðŸ'¡" = "💡"
    "ðŸ"'" = "🔑"
    "ðŸ"…" = "📆"
    "ðŸ—"ï¸" = "🗓️"
    "ðŸ"" = "📁"
    "ðŸ"" = "📄"
    "ðŸ"" = "📝"
    "ðŸŸ¢" = "🟢"
    "ðŸ"´" = "🔴"
    "ðŸŸ¡" = "🟡"
    "â€™" = "'"
    "â€œ" = '"'
    "â€" = '"'
    "â€"" = "—"
    "â€"" = "–"
    "â€¦" = "…"
}

# Funzione per ripristinare emoji in un file
function Restore-EmojiInFile {
    param([string]$FilePath)
    
    try {
        $content = Get-Content $FilePath -Raw -Encoding UTF8
        $originalContent = $content
        
        foreach ($corrupt in $emojiMap.Keys) {
            $correct = $emojiMap[$corrupt]
            $content = $content -replace [regex]::Escape($corrupt), $correct
        }
        
        if ($content -ne $originalContent) {
            $utf8WithBom = New-Object System.Text.UTF8Encoding $true
            [System.IO.File]::WriteAllText($FilePath, $content, $utf8WithBom)
            return $true
        }
        
        return $false
    }
    catch {
        Write-Host "Errore ripristino $FilePath : $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Trova e ripristina file Python
Write-Host "Cercando file Python da ripristinare..." -ForegroundColor Yellow

$pythonFiles = Get-ChildItem -Path . -Recurse -Include "*.py"
$restoredCount = 0

foreach ($file in $pythonFiles) {
    $restored = Restore-EmojiInFile $file.FullName
    if ($restored) {
        Write-Host "✅ Ripristinato: $($file.Name)" -ForegroundColor Green
        $restoredCount++
    }
}

Write-Host "📊 File ripristinati: $restoredCount" -ForegroundColor Cyan

# Cerca caratteri corrotti rimanenti
Write-Host "`nCercando caratteri corrotti rimanenti..." -ForegroundColor Yellow

$corruptedFiles = @()
foreach ($file in $pythonFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    if ($content -match "ðŸ|â€|â™|â|Ã|Â") {
        $corruptedFiles += $file.Name
        Write-Host "⚠️ Caratteri sospetti in: $($file.Name)" -ForegroundColor Yellow
    }
}

if ($corruptedFiles.Count -eq 0) {
    Write-Host "✅ Nessun carattere corrotto trovato!" -ForegroundColor Green
} else {
    Write-Host "File da controllare manualmente:" -ForegroundColor White
    foreach ($file in $corruptedFiles) {
        Write-Host "  - $file" -ForegroundColor Gray
    }
}

Write-Host "`n🎯 Test ora: streamlit run main.py" -ForegroundColor Green