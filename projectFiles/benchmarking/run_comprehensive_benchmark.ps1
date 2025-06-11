# Enhanced Comprehensive Benchmark Test Runner for Institution Profiler
# This PowerShell script runs the comprehensive 60-institution benchmark test suite

param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = "benchmarking\comprehensive_institution_benchmark.json",
    
    [Parameter(Mandatory=$false)]
    [string]$BaseDir = ".",
    
    [Parameter(Mandatory=$false)]
    [switch]$ActivateEnv = $true,
    
    [Parameter(Mandatory=$false)]
    [switch]$OpenResults = $true,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose = $false
)

# Set error handling
$ErrorActionPreference = "Stop"

# Define colors for output
$ColorSuccess = "Green"
$ColorWarning = "Yellow" 
$ColorError = "Red"
$ColorInfo = "Cyan"

function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Prerequisites {
    Write-ColoredOutput "🔍 Checking prerequisites..." $ColorInfo
    
    # Check if we're in the right directory
    if (-not (Test-Path "app.py") -or -not (Test-Path "benchmarking")) {
        Write-ColoredOutput "❌ Error: Not in the correct project directory. Please run from the projectFiles directory." $ColorError
        exit 1
    }
    
    # Check if config file exists
    if (-not (Test-Path $ConfigFile)) {
        Write-ColoredOutput "❌ Error: Configuration file not found: $ConfigFile" $ColorError
        exit 1
    }
    
    # Check if Python is available
    try {
        $pythonVersion = python --version 2>&1
        Write-ColoredOutput "✅ Python found: $pythonVersion" $ColorSuccess
    } catch {
        Write-ColoredOutput "❌ Error: Python not found in PATH" $ColorError
        exit 1
    }
    
    Write-ColoredOutput "✅ Prerequisites check passed" $ColorSuccess
}

function Activate-Environment {
    if ($ActivateEnv) {
        Write-ColoredOutput "🐍 Activating Python virtual environment..." $ColorInfo
        
        $envPath = "..\nlp\Scripts\Activate.ps1"
        if (Test-Path $envPath) {
            try {
                & $envPath
                Write-ColoredOutput "✅ Virtual environment activated" $ColorSuccess
            } catch {
                Write-ColoredOutput "⚠️  Warning: Could not activate virtual environment: $_" $ColorWarning
                Write-ColoredOutput "   Continuing with system Python..." $ColorWarning
            }
        } else {
            Write-ColoredOutput "⚠️  Warning: Virtual environment not found at $envPath" $ColorWarning
            Write-ColoredOutput "   Continuing with system Python..." $ColorWarning
        }
    }
}

function Install-Dependencies {
    Write-ColoredOutput "📦 Checking Python dependencies..." $ColorInfo
    
    # Check if pandas is installed (required for analysis)
    try {
        python -c "import pandas" 2>$null
        Write-ColoredOutput "✅ Pandas is available" $ColorSuccess
    } catch {
        Write-ColoredOutput "📦 Installing pandas for data analysis..." $ColorInfo
        pip install pandas
    }
    
    # Check if other required packages are available
    $requiredPackages = @("json", "time", "datetime", "os", "sys")
    foreach ($package in $requiredPackages) {
        try {
            python -c "import $package" 2>$null
        } catch {
            Write-ColoredOutput "⚠️  Warning: Package $package not available" $ColorWarning
        }
    }
}

function Start-BenchmarkTest {
    Write-ColoredOutput "`n🚀 Starting Comprehensive Institution Benchmark Test" $ColorInfo
    Write-ColoredOutput "   📋 Configuration: $ConfigFile" $ColorInfo
    Write-ColoredOutput "   📁 Base Directory: $BaseDir" $ColorInfo
    Write-ColoredOutput "   ⏰ Start Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" $ColorInfo
    
    # Prepare the Python command
    $pythonScript = "benchmarking\comprehensive_test_runner.py"
    $command = "python `"$pythonScript`" `"$ConfigFile`" --base-dir `"$BaseDir`""
    
    if ($Verbose) {
        Write-ColoredOutput "   🔧 Command: $command" $ColorInfo
    }
    
    Write-ColoredOutput "`n📊 Running comprehensive benchmark test suite..." $ColorInfo
    Write-ColoredOutput "   This will test 60 institutions across 4 categories with multiple output formats" $ColorInfo
    Write-ColoredOutput "   Expected duration: 15-30 minutes depending on your system and API limits" $ColorWarning
    Write-ColoredOutput "`n   Progress will be displayed below:" $ColorInfo
    Write-ColoredOutput "   " + ("=" * 80) $ColorInfo
    
    try {
        # Execute the Python script
        $result = Invoke-Expression $command
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColoredOutput "`n   " + ("=" * 80) $ColorSuccess
            Write-ColoredOutput "✅ Benchmark test completed successfully!" $ColorSuccess
            return $true
        } else {
            Write-ColoredOutput "`n   " + ("=" * 80) $ColorError
            Write-ColoredOutput "❌ Benchmark test failed with exit code: $LASTEXITCODE" $ColorError
            return $false
        }
    } catch {
        Write-ColoredOutput "`n   " + ("=" * 80) $ColorError
        Write-ColoredOutput "❌ Error running benchmark test: $_" $ColorError
        return $false
    }
}

function Open-Results {
    if ($OpenResults) {
        Write-ColoredOutput "`n📁 Opening results directory..." $ColorInfo
        
        $resultsDir = "project_cache\benchmark_results"
        
        if (Test-Path $resultsDir) {
            # Find the most recent HTML report
            $htmlFiles = Get-ChildItem -Path $resultsDir -Filter "*analysis*.html" | Sort-Object LastWriteTime -Descending
            
            if ($htmlFiles) {
                $latestHtml = $htmlFiles[0].FullName
                Write-ColoredOutput "🌐 Opening HTML analysis report: $($htmlFiles[0].Name)" $ColorSuccess
                Start-Process $latestHtml
            }
            
            # Open the results directory
            Write-ColoredOutput "📂 Opening results directory..." $ColorInfo
            Start-Process explorer.exe $resultsDir
        } else {
            Write-ColoredOutput "⚠️  Results directory not found: $resultsDir" $ColorWarning
        }
    }
}

function Show-Summary {
    Write-ColoredOutput "`n📋 Benchmark Test Summary" $ColorInfo
    Write-ColoredOutput "   " + ("=" * 50) $ColorInfo
    Write-ColoredOutput "   ✅ Test Suite: Comprehensive Institution Benchmark" $ColorSuccess
    Write-ColoredOutput "   📊 Institutions Tested: 60 (15 universities, 15 hospitals, 15 banks, 15 others)" $ColorInfo
    Write-ColoredOutput "   📄 Output Formats: JSON, Structured, Comprehensive" $ColorInfo
    Write-ColoredOutput "   🎯 Quality Integration: Core routes quality score integrated" $ColorSuccess
    Write-ColoredOutput "   📈 Analysis Generated: Performance, cost, quality, and field completion" $ColorSuccess
    Write-ColoredOutput "   ⏰ Completion Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" $ColorInfo
    
    # Check for results files
    $resultsDir = "project_cache\benchmark_results"
    if (Test-Path $resultsDir) {
        $resultFiles = Get-ChildItem -Path $resultsDir -Filter "*$(Get-Date -Format 'yyyyMMdd')*"
        Write-ColoredOutput "   📁 Generated Files: $($resultFiles.Count) files in $resultsDir" $ColorSuccess
        
        foreach ($file in $resultFiles) {
            $fileType = switch ($file.Extension) {
                ".json" { "📊 JSON Data" }
                ".csv" { "📈 CSV Data" }
                ".html" { "🌐 HTML Report" }
                default { "📄 File" }
            }
            Write-ColoredOutput "      $fileType : $($file.Name)" $ColorInfo
        }
    }
    
    Write-ColoredOutput "`n🎉 Comprehensive benchmark test completed!" $ColorSuccess
    Write-ColoredOutput "   Check the generated files for detailed analysis and results." $ColorInfo
}

# Main execution
try {
    Write-ColoredOutput "🏛️  Institution Profiler - Comprehensive Benchmark Test Runner" $ColorInfo
    Write-ColoredOutput "   " + ("=" * 70) $ColorInfo
    
    # Run all steps
    Test-Prerequisites
    Activate-Environment
    Install-Dependencies
    
    $success = Start-BenchmarkTest
    
    if ($success) {
        Open-Results
        Show-Summary
    } else {
        Write-ColoredOutput "`n❌ Benchmark test failed. Check the error messages above." $ColorError
        Write-ColoredOutput "   💡 Troubleshooting tips:" $ColorInfo
        Write-ColoredOutput "      - Ensure you have a valid GOOGLE_API_KEY environment variable" $ColorInfo
        Write-ColoredOutput "      - Check your internet connection" $ColorInfo
        Write-ColoredOutput "      - Verify all required Python packages are installed" $ColorInfo
        Write-ColoredOutput "      - Try running with -Verbose for more details" $ColorInfo
        exit 1
    }
    
} catch {
    Write-ColoredOutput "`n💥 Unexpected error occurred: $_" $ColorError
    Write-ColoredOutput "   Please check your configuration and try again." $ColorError
    exit 1
}
