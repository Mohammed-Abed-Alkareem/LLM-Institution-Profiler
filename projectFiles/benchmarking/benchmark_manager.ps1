# Enhanced Benchmarking Manager
# Simple PowerShell interface for the Institution Profiler benchmarking system

param(
    [Parameter(Position=0)]
    [ValidateSet("status", "test", "analyze", "help")]
    [string]$Action = "help",
    
    [string]$ProjectFiles = "",
    [string]$TestConfig = "",
    [int]$Days = 7,
    [string]$Format = "json",
    [string]$Output = ""
)

# Set default project files path
if (-not $ProjectFiles) {
    $ProjectFiles = (Resolve-Path "$PSScriptRoot\..").Path
}

# Helper function to run Python scripts
function Invoke-PythonScript {
    param(
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )
    
    Write-Host "Running Python script: $ScriptPath" -ForegroundColor Gray
    
    try {
        $AllArgs = @($ScriptPath) + $Arguments
        $Process = Start-Process -FilePath "python" -ArgumentList $AllArgs -Wait -PassThru -NoNewWindow
        return ($Process.ExitCode -eq 0)
    }
    catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Status check function
function Show-Status {
    Write-Host "Checking Benchmarking System Status..." -ForegroundColor Cyan
    
    $StatusScript = Join-Path $PSScriptRoot "scripts\status_check.py"
    
    if (-not (Test-Path $StatusScript)) {
        Write-Host "Status script not found: $StatusScript" -ForegroundColor Red
        return
    }
    
    $Success = Invoke-PythonScript -ScriptPath $StatusScript -Arguments @($ProjectFiles)
    if ($Success) {
        Write-Host "Status check completed!" -ForegroundColor Green
    }
}

# Test function
function Start-Test {
    Write-Host "Running Benchmark Tests..." -ForegroundColor Cyan
    
    $ConfigPath = if ($TestConfig) { 
        $TestConfig 
    } else { 
        Join-Path $ProjectFiles "benchmarking\test_config_quick.json"
    }
    
    if (-not (Test-Path $ConfigPath)) {
        Write-Host "Test configuration not found: $ConfigPath" -ForegroundColor Red
        return
    }
    
    $TestScript = Join-Path $PSScriptRoot "scripts\run_test.py"
    
    if (-not (Test-Path $TestScript)) {
        Write-Host "Test script not found: $TestScript" -ForegroundColor Red
        return
    }
    
    $Success = Invoke-PythonScript -ScriptPath $TestScript -Arguments @($ProjectFiles, $ConfigPath)
    if ($Success) {
        Write-Host "Test completed!" -ForegroundColor Green
    }
}

# Analysis function
function Invoke-Analysis {
    Write-Host "Running Analysis..." -ForegroundColor Cyan
    
    $OutputFile = if ($Output) { $Output } else { "analysis_$(Get-Date -Format 'yyyyMMdd_HHmmss').$Format" }
    
    $AnalysisScript = Join-Path $PSScriptRoot "scripts\run_analysis.py"
    
    if (-not (Test-Path $AnalysisScript)) {
        Write-Host "Analysis script not found: $AnalysisScript" -ForegroundColor Red
        return
    }
    
    $Success = Invoke-PythonScript -ScriptPath $AnalysisScript -Arguments @($ProjectFiles, $Days.ToString(), $Format, $OutputFile)
    if ($Success) {
        Write-Host "Analysis completed!" -ForegroundColor Green
    }
}

# Help function
function Show-Help {
    Write-Host "Enhanced Benchmarking Manager" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor White
    Write-Host "  .\benchmark_manager_simple.ps1 [action] [options]" -ForegroundColor Gray
    Write-Host ""
    Write-Host "ACTIONS:" -ForegroundColor White
    Write-Host "  status      Check system status" -ForegroundColor Cyan
    Write-Host "  test        Run benchmark tests" -ForegroundColor Cyan
    Write-Host "  analyze     Analyze benchmark data" -ForegroundColor Cyan
    Write-Host "  help        Show this help" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "OPTIONS:" -ForegroundColor White
    Write-Host "  -ProjectFiles  Project directory path" -ForegroundColor Gray
    Write-Host "  -TestConfig    Test configuration file" -ForegroundColor Gray
    Write-Host "  -Days          Days for analysis (default: 7)" -ForegroundColor Gray
    Write-Host "  -Format        Output format (json/csv)" -ForegroundColor Gray
    Write-Host "  -Output        Output file name" -ForegroundColor Gray
}

# Main execution
Write-Host "Benchmarking Manager" -ForegroundColor Yellow
Write-Host "===================" -ForegroundColor Yellow

# Check project files directory
if (-not (Test-Path $ProjectFiles)) {
    Write-Host "Project directory not found: $ProjectFiles" -ForegroundColor Red
    exit 1
}

# Create scripts directory if needed
$ScriptsDir = Join-Path $PSScriptRoot "scripts"
if (-not (Test-Path $ScriptsDir)) {
    New-Item -ItemType Directory -Path $ScriptsDir -Force | Out-Null
    Write-Host "Created scripts directory" -ForegroundColor Green
}

# Execute action
switch ($Action.ToLower()) {
    "status" { Show-Status }
    "test" { Start-Test }
    "analyze" { Invoke-Analysis }
    "help" { Show-Help }
    default { 
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Show-Help
        exit 1
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
