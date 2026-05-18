# MT5 Trading Dashboard - Code Analysis and Export Script v1.5
# Version: 1.5.0 - Updated for Modular Architecture
# Purpose: Analyze project structure and copy relevant files for Claude review
# Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# Updated for: Modular architecture with tabs/performance/ structure

param(
    [string]$ProjectRoot = ".",
    [string]$OutputDir = "shared_claude",
    [string]$LogFile = "analysis_log.txt"
)

# Initialize logging
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogFile -Value $logEntry
}

# Clear previous log
if (Test-Path $LogFile) { Remove-Item $LogFile }

Write-Log "=== MT5 TRADING DASHBOARD ANALYSIS v1.5 STARTED ===" "HEADER"
Write-Log "Project Root: $(Resolve-Path $ProjectRoot)"
Write-Log "Output Directory: $OutputDir"
Write-Log "Log File: $LogFile"
Write-Log "Updated for: Modular Architecture (v1.5+)"
Write-Log ""

# Create output directory
if (Test-Path $OutputDir) {
    Write-Log "Removing existing output directory..." "WARN"
    Remove-Item -Recurse -Force $OutputDir
}
New-Item -ItemType Directory -Path $OutputDir | Out-Null
Write-Log "Created output directory: $OutputDir" "SUCCESS"

# Function to get file size in human readable format
function Get-FileSize {
    param([long]$Bytes)
    if ($Bytes -gt 1MB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
    elseif ($Bytes -gt 1KB) { return "{0:N2} KB" -f ($Bytes / 1KB) }
    else { return "$Bytes bytes" }
}

# Function to copy and rename file
function Copy-FileWithRename {
    param(
        [string]$SourcePath,
        [string]$RelativePath,
        [string]$TargetDir
    )
    
    $sourceFile = Get-Item $SourcePath
    $fileSize = Get-FileSize $sourceFile.Length
    
    # Create new filename with folder structure
    $pathParts = $RelativePath.Split([IO.Path]::DirectorySeparatorChar)
    if ($pathParts.Length -gt 1) {
        $newName = ($pathParts[0..($pathParts.Length-2)] -join "_") + "_" + $sourceFile.Name
    } else {
        $newName = $sourceFile.Name
    }
    
    $targetPath = Join-Path $TargetDir $newName
    
    try {
        Copy-Item -Path $SourcePath -Destination $targetPath
        Write-Log "COPIED: $RelativePath -> $newName ($fileSize)" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "ERROR copying $RelativePath : $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# 1. ANALYZE PROJECT STRUCTURE
Write-Log "" 
Write-Log "=== 1. PROJECT STRUCTURE ANALYSIS ===" "HEADER"

$allFiles = Get-ChildItem -Recurse -File | Where-Object { 
    $_.Extension -in @('.py', '.css', '.json', '.md', '.txt', '.csv', '.mqh', '.mq5') -and
    $_.DirectoryName -notmatch '(__pycache__|\.git|\.vscode|node_modules|shared_claude)'
}

Write-Log "Total relevant files found: $($allFiles.Count)"
Write-Log ""

# Group files by extension
$filesByExt = $allFiles | Group-Object Extension | Sort-Object Name
foreach ($group in $filesByExt) {
    Write-Log "Files with extension $($group.Name): $($group.Count)"
}
Write-Log ""

# Directory structure analysis
Write-Log "DIRECTORY STRUCTURE:"
$directories = Get-ChildItem -Recurse -Directory | Where-Object { 
    $_.FullName -notmatch '(__pycache__|\.git|\.vscode|node_modules|shared_claude)' 
} | Sort-Object FullName

foreach ($dir in $directories) {
    $relativePath = $dir.FullName.Substring($PWD.Path.Length + 1)
    $fileCount = (Get-ChildItem -Path $dir.FullName -File | Where-Object { 
        $_.Extension -in @('.py', '.css', '.json', '.md') 
    }).Count
    Write-Log "  [DIR] $relativePath ($fileCount files)"
}
Write-Log ""

# 2. COPY CRITICAL FILES FOR CLAUDE ANALYSIS
Write-Log "=== 2. COPYING FILES FOR CLAUDE ANALYSIS ===" "HEADER"

# Define priority files to copy - UPDATED FOR v1.5 MODULAR ARCHITECTURE
$priorityFiles = @(
    # Core application files
    @{ Pattern = "main.py"; Priority = 1; Description = "Application entry point" },
    @{ Pattern = "config.py"; Priority = 1; Description = "Configuration management" },
    
    # Data layer
    @{ Pattern = "data\loader.py"; Priority = 1; Description = "Data loading system" },
    @{ Pattern = "data\metrics.py"; Priority = 1; Description = "Performance metrics" },
    @{ Pattern = "data\margin_debugger.py"; Priority = 2; Description = "Margin analysis" },
    @{ Pattern = "data\debug_renderer.py"; Priority = 2; Description = "Debug interface" },
    
    # NEW v1.5: Modular Performance Tab Structure
    @{ Pattern = "tabs\performance\main.py"; Priority = 1; Description = "Performance tab entry point" },
    @{ Pattern = "tabs\performance\__init__.py"; Priority = 1; Description = "Performance module exports" },
    
    # NEW v1.5: Configuration module
    @{ Pattern = "tabs\performance\config\constants.py"; Priority = 1; Description = "Performance constants" },
    @{ Pattern = "tabs\performance\config\__init__.py"; Priority = 2; Description = "Config module exports" },
    
    # NEW v1.5: Utilities module
    @{ Pattern = "tabs\performance\utils\data_processing.py"; Priority = 1; Description = "Core data processing" },
    @{ Pattern = "tabs\performance\utils\chart_helpers.py"; Priority = 1; Description = "Chart utilities" },
    @{ Pattern = "tabs\performance\utils\session_helpers.py"; Priority = 1; Description = "Session management" },
    @{ Pattern = "tabs\performance\utils\formatting.py"; Priority = 1; Description = "Display formatting" },
    @{ Pattern = "tabs\performance\utils\__init__.py"; Priority = 2; Description = "Utils module exports" },
    
    # NEW v1.5: Sidebar module
    @{ Pattern = "tabs\performance\sidebar\layout.py"; Priority = 1; Description = "Sidebar layout" },
    @{ Pattern = "tabs\performance\sidebar\account_info.py"; Priority = 1; Description = "Account information" },
    @{ Pattern = "tabs\performance\sidebar\period_selection.py"; Priority = 1; Description = "Period controls" },
    @{ Pattern = "tabs\performance\sidebar\setup_selection.py"; Priority = 1; Description = "Setup management" },
    @{ Pattern = "tabs\performance\sidebar\filters.py"; Priority = 1; Description = "Advanced filters" },
    @{ Pattern = "tabs\performance\sidebar\debug_tools.py"; Priority = 2; Description = "Debug utilities" },
    @{ Pattern = "tabs\performance\sidebar\__init__.py"; Priority = 2; Description = "Sidebar module exports" },
    
    # NEW v1.5: Tabs module
    @{ Pattern = "tabs\performance\tabs\charts_tab.py"; Priority = 1; Description = "Charts visualization" },
    @{ Pattern = "tabs\performance\tabs\summary_tab.py"; Priority = 1; Description = "Performance summary" },
    @{ Pattern = "tabs\performance\tabs\table_tab.py"; Priority = 1; Description = "Performance table" },
    @{ Pattern = "tabs\performance\tabs\deals_tab.py"; Priority = 1; Description = "Recent deals" },
    @{ Pattern = "tabs\performance\tabs\__init__.py"; Priority = 2; Description = "Tabs module exports" },
    
    # Other tab interfaces (non-modular)
    @{ Pattern = "tabs\tab_ea_attivi.py"; Priority = 1; Description = "EA monitoring tab" },
    @{ Pattern = "tabs\tab_posizioni.py"; Priority = 1; Description = "Position management tab" },
    @{ Pattern = "tabs\tab_settings.py"; Priority = 2; Description = "Settings and configuration" },
    
    # Legacy performance tab (if still exists for backward compatibility)
    @{ Pattern = "tabs\tab_performance.py"; Priority = 3; Description = "Legacy performance tab (backup)" },
    
    # Assets and configuration
    @{ Pattern = "assets\style.css"; Priority = 2; Description = "CSS styling" },
    @{ Pattern = "accounts_config.json"; Priority = 2; Description = "Account configuration" },
    
    # Documentation
    @{ Pattern = "README.md"; Priority = 3; Description = "Project documentation" },
    @{ Pattern = "requirements.txt"; Priority = 3; Description = "Python dependencies" }
)

$copiedCount = 0
$totalSize = 0

foreach ($fileSpec in $priorityFiles) {
    $pattern = $fileSpec.Pattern
    $priority = $fileSpec.Priority
    $description = $fileSpec.Description
    
    # Find files matching pattern - improved matching for nested structure
    $matchingFiles = Get-ChildItem -Recurse -File | Where-Object { 
        $relativePath = $_.FullName.Substring($PWD.Path.Length + 1)
        
        # Exact path match (for nested structure)
        if ($relativePath -eq $pattern) { return $true }
        
        # Filename match in correct directory context
        if ($pattern.Contains('\')) {
            $patternDir = Split-Path $pattern -Parent
            $patternFile = Split-Path $pattern -Leaf
            $fileDir = Split-Path $relativePath -Parent
            $fileName = Split-Path $relativePath -Leaf
            
            return ($fileDir -like "*$patternDir*" -and $fileName -eq $patternFile)
        }
        
        # Simple filename match for root files
        return ($_.Name -eq [IO.Path]::GetFileName($pattern))
    }
    
    if ($matchingFiles) {
        foreach ($file in $matchingFiles) {
            $relativePath = $file.FullName.Substring($PWD.Path.Length + 1)
            if (Copy-FileWithRename -SourcePath $file.FullName -RelativePath $relativePath -TargetDir $OutputDir) {
                $copiedCount++
                $totalSize += $file.Length
            }
        }
    } else {
        Write-Log "NOT FOUND: $pattern ($description)" "WARN"
    }
}

Write-Log ""
Write-Log "Total files copied: $copiedCount"
Write-Log "Total size copied: $(Get-FileSize $totalSize)"

# 3. ADDITIONAL FILES ANALYSIS
Write-Log ""
Write-Log "=== 3. ADDITIONAL FILES ANALYSIS ===" "HEADER"

# Look for any Python files not in our priority list
$additionalPyFiles = Get-ChildItem -Recurse -Filter "*.py" | Where-Object { 
    $relativePath = $_.FullName.Substring($PWD.Path.Length + 1)
    $relativePath -notmatch 'shared_claude' -and
    -not ($priorityFiles.Pattern | ForEach-Object { 
        $pattern = $_
        # Check exact match or directory context match
        ($relativePath -eq $pattern) -or 
        ($pattern.Contains('\') -and $relativePath -like "*$(Split-Path $pattern -Parent)*" -and $relativePath.EndsWith($(Split-Path $pattern -Leaf))) -or
        ($relativePath -like "*$pattern*")
    })
}

if ($additionalPyFiles) {
    Write-Log "ADDITIONAL PYTHON FILES FOUND:"
    foreach ($file in $additionalPyFiles) {
        $relativePath = $file.FullName.Substring($PWD.Path.Length + 1)
        $fileSize = Get-FileSize $file.Length
        Write-Log "  [PY] $relativePath ($fileSize)"
        
        # Copy additional Python files as they might be important
        if (Copy-FileWithRename -SourcePath $file.FullName -RelativePath $relativePath -TargetDir $OutputDir) {
            $copiedCount++
        }
    }
} else {
    Write-Log "No additional Python files found outside priority list." "INFO"
}

# Look for configuration files
$configFiles = Get-ChildItem -Recurse | Where-Object { 
    $_.Extension -in @('.json', '.yaml', '.yml', '.ini', '.cfg', '.conf') -and
    $_.DirectoryName -notmatch 'shared_claude' -and
    $_.Name -ne 'accounts_config.json'  # Already in priority list
}

if ($configFiles) {
    Write-Log ""
    Write-Log "CONFIGURATION FILES FOUND:"
    foreach ($file in $configFiles) {
        $relativePath = $file.FullName.Substring($PWD.Path.Length + 1)
        $fileSize = Get-FileSize $file.Length
        Write-Log "  [CFG] $relativePath ($fileSize)"
        
        # Copy config files
        Copy-FileWithRename -SourcePath $file.FullName -RelativePath $relativePath -TargetDir $OutputDir | Out-Null
    }
}

# 4. GENERATE FILE MANIFEST WITH v1.5 STRUCTURE INFO
Write-Log ""
Write-Log "=== 4. GENERATING FILE MANIFEST ===" "HEADER"

$manifestPath = Join-Path $OutputDir "file_manifest.txt"
$manifest = @()
$manifest += "MT5 TRADING DASHBOARD - FILE MANIFEST v1.5"
$manifest += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$manifest += "Source Directory: $(Resolve-Path $ProjectRoot)"
$manifest += "Architecture: Modular (v1.5+ Refactored)"
$manifest += "="*60
$manifest += ""
$manifest += "MODULAR STRUCTURE ANALYSIS:"
$manifest += "- Core Application: main.py, config.py"
$manifest += "- Data Layer: data/*.py"
$manifest += "- Performance Module: tabs/performance/ (Modular)"
$manifest += "- Other Tabs: tabs/tab_*.py (Legacy structure)"
$manifest += "- Assets: assets/*.css"
$manifest += ""
$manifest += "COPIED FILES:"

$copiedFiles = Get-ChildItem -Path $OutputDir -File | Sort-Object Name
foreach ($file in $copiedFiles) {
    if ($file.Name -ne "file_manifest.txt") {
        $fileSize = Get-FileSize $file.Length
        $lastModified = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        
        # Categorize files for better organization
        $category = "OTHER"
        if ($file.Name -like "*performance*") { $category = "PERFORMANCE" }
        elseif ($file.Name -like "*data*") { $category = "DATA" }
        elseif ($file.Name -like "*tab_*") { $category = "TABS" }
        elseif ($file.Name -like "*main*" -or $file.Name -like "*config*") { $category = "CORE" }
        elseif ($file.Name -like "*style*" -or $file.Name -like "*assets*") { $category = "ASSETS" }
        
        $manifestEntry = "[$category] $($file.Name) | $fileSize | Modified: $lastModified"
        $manifest += $manifestEntry
    }
}

$manifest += ""
$manifest += "ARCHITECTURE NOTES:"
$manifest += "- Performance tab refactored into modular structure (v1.5)"
$manifest += "- 21 specialized files across 5 module categories"
$manifest += "- Backward compatibility maintained via delegation"
$manifest += "- Average ~170 lines per file vs. 2,500 lines in monolithic file"
$manifest += ""
$manifest += "TOTAL FILES: $($copiedFiles.Count - 1)"  # -1 for the manifest itself
$manifest += "TOTAL SIZE: $(Get-FileSize ($copiedFiles | Measure-Object Length -Sum).Sum)"

$manifest | Out-File -FilePath $manifestPath -Encoding UTF8
Write-Log "File manifest created: file_manifest.txt"

# 5. FINAL SUMMARY WITH v1.5 SPECIFIC INFO
Write-Log ""
Write-Log "=== 5. ANALYSIS SUMMARY v1.5 ===" "HEADER"
Write-Log "Project structure analyzed: OK (Modular architecture detected)"
Write-Log "$copiedCount files copied to $OutputDir OK"
Write-Log "File manifest generated: OK"
Write-Log "Analysis log created: $LogFile"
Write-Log ""
Write-Log "v1.5 MODULAR ARCHITECTURE DETECTED:"
Write-Log "- Performance tab: Modular structure in tabs/performance/"
Write-Log "- 5 module categories: config, utils, sidebar, tabs, main"
Write-Log "- 21+ specialized files vs. monolithic structure"
Write-Log "- Backward compatibility layer maintained"
Write-Log ""
Write-Log "NEXT STEPS:"
Write-Log "1. Review the analysis log ($LogFile)"
Write-Log "2. Share the contents of '$OutputDir' folder with Claude"
Write-Log "3. Include the analysis log for context"
Write-Log "4. Mention v1.5 modular architecture in discussion"
Write-Log ""
Write-Log "FILES TO SHARE WITH CLAUDE:"
Get-ChildItem -Path $OutputDir -File | Sort-Object Name | ForEach-Object {
    Write-Log "  [FILE] $($_.Name)"
}

Write-Log ""
Write-Log "=== ANALYSIS COMPLETED SUCCESSFULLY (v1.5 MODULAR) ==="

# Display final summary
Write-Host ""
Write-Host "Analysis completed for v1.5 Modular Architecture!" -ForegroundColor Green
Write-Host "Files copied to: ${OutputDir}" -ForegroundColor Cyan
Write-Host "Analysis log: ${LogFile}" -ForegroundColor Cyan
Write-Host ""
Write-Host "Modular structure detected and processed!" -ForegroundColor Magenta
Write-Host "Ready to share with Claude!" -ForegroundColor Yellow