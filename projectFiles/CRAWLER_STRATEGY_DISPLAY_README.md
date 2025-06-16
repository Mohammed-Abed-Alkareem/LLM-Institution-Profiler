# Crawler Strategy Display Script

This script displays benchmark results with crawler strategy information that is missing from the standard text summary reports.

## Usage

```powershell
# Activate the Python environment first
.\nlp\Scripts\Activate.ps1

# Display results from latest benchmark files
python display_crawler_strategies.py

# Display results from specific file
python display_crawler_strategies.py -f "project_cache/benchmark_results/comprehensive_benchmark_results_20250616_104238.csv"

# Include strategy analysis
python display_crawler_strategies.py --analysis

# Output to LaTeX file for academic papers
python display_crawler_strategies.py --output "results.tex" --latex

# Output to CSV file
python display_crawler_strategies.py --output "results.csv"

# Use table format instead of pandas
python display_crawler_strategies.py --format table
```

## Output Formats

- **Console Display**: Shows formatted table with crawler strategy column
- **CSV Output**: Clean CSV file with all benchmark data including crawler strategies
- **LaTeX Output**: Ready-to-use LaTeX table for academic papers/reports

## Purpose

The standard benchmark summary text files do not show which crawler strategy was used for each test. This script extracts that information from the detailed CSV/JSON results and displays it clearly, making it easy to compare performance across different crawling strategies (priority_based, equal, high_links, high_depth).

## Files Processed

- `comprehensive_benchmark_results_*.csv` - Preferred source
- `comprehensive_benchmark_results_*.json` - Alternative source
- Automatically finds the latest files if no specific file is specified
