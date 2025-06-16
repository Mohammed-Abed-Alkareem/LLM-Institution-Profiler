#!/usr/bin/env python3
"""
Script to display benchmark results with crawler strategy information.
Reads the comprehensive benchmark results and shows a table including the crawler strategy for each test.
"""

import json
import csv
import pandas as pd
import argparse
from pathlib import Path
from typing import List, Dict, Any
import os
from datetime import datetime

def find_latest_benchmark_files(benchmark_dir: str) -> Dict[str, str]:
    """Find the most recent benchmark result files."""
    benchmark_path = Path(benchmark_dir)
    
    if not benchmark_path.exists():
        raise FileNotFoundError(f"Benchmark directory not found: {benchmark_dir}")
    
    # Find all benchmark files
    json_files = list(benchmark_path.glob("comprehensive_benchmark_results_*.json"))
    csv_files = list(benchmark_path.glob("comprehensive_benchmark_results_*.csv"))
    
    if not json_files and not csv_files:
        raise FileNotFoundError("No benchmark result files found")
    
    # Get the latest files based on timestamp in filename
    latest_json = max(json_files, key=lambda x: x.stat().st_mtime) if json_files else None
    latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime) if csv_files else None
    
    return {
        'json': str(latest_json) if latest_json else None,
        'csv': str(latest_csv) if latest_csv else None
    }

def load_results_from_json(json_file: str) -> List[Dict[str, Any]]:
    """Load benchmark results from JSON file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = []
    
    # Handle different JSON structures
    if isinstance(data, list):
        # Direct list of results
        result_list = data
    elif isinstance(data, dict):
        # Check for common keys that might contain results
        if 'results' in data:
            result_list = data['results']
        elif 'test_results' in data:
            result_list = data['test_results']
        elif 'detailed_results' in data:
            result_list = data['detailed_results']
        else:
            # Look for any key that contains a list
            result_list = []
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], dict) and 'institution_name' in value[0]:
                        result_list = value
                        break
    else:
        result_list = []
    
    for result in result_list:
        if isinstance(result, dict):
            results.append({
                'institution_name': result.get('institution_name', 'N/A'),
                'institution_type': result.get('institution_type', 'N/A'),
                'crawler_strategy': result.get('crawler_strategy', 'N/A'),
                'force_refresh': result.get('force_refresh_used', result.get('force_refresh', False)),
                'quality_score': result.get('core_quality_score', result.get('quality_score', 0)),
                'rating_score': result.get('core_quality_rating', result.get('rating_score', 'N/A')),
                'processing_time': result.get('execution_time', result.get('processing_time_seconds', 0)),
                'estimated_cost': result.get('cost_usd', result.get('estimated_cost', 0)),
                'total_fields': result.get('fields_extracted', result.get('total_fields', 0)),
                'total_tokens': result.get('total_tokens', 0),
                'model_used': result.get('llm_model_used', result.get('model_used', 'N/A')),
                'status': 'Success' if result.get('success', result.get('overall_pipeline_success', False)) else 'Failed'
            })
    
    return results

def load_results_from_csv(csv_file: str) -> List[Dict[str, Any]]:
    """Load benchmark results from CSV file."""
    results = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle boolean values
            force_refresh = row.get('force_refresh_used', row.get('force_refresh', '')).lower() in ['true', '1', 'yes']
            success = row.get('success', row.get('overall_pipeline_success', '')).lower() in ['true', '1', 'yes']
            
            # Handle numeric values safely
            try:
                quality_score = float(row.get('core_quality_score', row.get('quality_score', 0))) if row.get('core_quality_score', row.get('quality_score', 0)) else 0
            except (ValueError, TypeError):
                quality_score = 0
            
            try:
                processing_time = float(row.get('execution_time', row.get('processing_time_seconds', 0))) if row.get('execution_time', row.get('processing_time_seconds', 0)) else 0
            except (ValueError, TypeError):
                processing_time = 0
            
            try:
                estimated_cost = float(row.get('cost_usd', row.get('estimated_cost', 0))) if row.get('cost_usd', row.get('estimated_cost', 0)) else 0
            except (ValueError, TypeError):
                estimated_cost = 0
            
            try:
                total_fields = int(row.get('fields_extracted', row.get('total_fields', 0))) if row.get('fields_extracted', row.get('total_fields', 0)) else 0
            except (ValueError, TypeError):
                total_fields = 0
            
            try:
                total_tokens = int(row.get('total_tokens', 0)) if row.get('total_tokens', 0) else 0
            except (ValueError, TypeError):
                total_tokens = 0
            
            results.append({
                'institution_name': row.get('institution_name', 'N/A'),
                'institution_type': row.get('institution_type', 'N/A'),
                'crawler_strategy': row.get('crawler_strategy', 'N/A'),
                'force_refresh': force_refresh,
                'quality_score': quality_score,
                'rating_score': row.get('core_quality_rating', row.get('rating_score', 'N/A')),
                'processing_time': processing_time,
                'estimated_cost': estimated_cost,
                'total_fields': total_fields,
                'total_tokens': total_tokens,
                'model_used': row.get('llm_model_used', row.get('model_used', 'N/A')),
                'status': 'Success' if success else 'Failed'
            })
    
    return results

def display_results_table(results: List[Dict[str, Any]], format_type: str = 'table', output_file: str = None):    
    """Display results in a formatted table."""
    if not results:
        output = "No results found."
        print(output)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
        return
    
    output_lines = []
    
    if format_type == 'latex':
        # LaTeX table format
        output_lines.append("\\begin{table}[htbp]")
        output_lines.append("\\centering")
        output_lines.append("\\caption{Benchmark Results with Crawler Strategies}")
        output_lines.append("\\label{tab:crawler_strategies}")
        output_lines.append("\\begin{tabular}{|l|l|l|c|c|c|c|c|c|c|}")
        output_lines.append("\\hline")
        output_lines.append("Institution & Type & Strategy & Refresh & Quality & Rating & Time(s) & Cost & Fields & Tokens \\\\")
        output_lines.append("\\hline")
        
        for result in results:
            institution = result['institution_name'].replace('&', '\\&').replace('_', '\\_')[:20]
            inst_type = result['institution_type'].replace('_', '\\_')[:12]
            strategy = result['crawler_strategy'].replace('_', '\\_')[:12]
            refresh = "T" if result['force_refresh'] else "F"
            quality = f"{result['quality_score']:.1f}"
            rating = str(result['rating_score'])[:8].replace('_', '\\_')
            time_val = f"{result['processing_time']:.1f}"
            cost = f"{result['estimated_cost']:.4f}"
            fields = str(result['total_fields'])
            tokens = str(result['total_tokens'])
            
            line = f"{institution} & {inst_type} & {strategy} & {refresh} & {quality} & {rating} & {time_val} & {cost} & {fields} & {tokens} \\\\"
            output_lines.append(line)
        
        output_lines.append("\\hline")
        output_lines.append("\\end{tabular}")
        output_lines.append("\\end{table}")
        
    elif format_type == 'csv_export':
        # CSV export format
        output_lines.append("institution_name,institution_type,crawler_strategy,force_refresh,quality_score,rating_score,processing_time,estimated_cost,total_fields,total_tokens,model_used,status")
        
        for result in results:
            line = f'"{result["institution_name"]}","{result["institution_type"]}","{result["crawler_strategy"]}",{result["force_refresh"]},{result["quality_score"]},"{result["rating_score"]}",{result["processing_time"]},{result["estimated_cost"]},{result["total_fields"]},{result["total_tokens"]},"{result["model_used"]}","{result["status"]}"'
            output_lines.append(line)
    
    if format_type == 'pandas':
        # Use pandas for nice formatting
        df = pd.DataFrame(results)
        
        # Reorder columns to put crawler_strategy prominently
        column_order = [
            'institution_name', 'institution_type', 'crawler_strategy', 'force_refresh',
            'quality_score', 'rating_score', 'processing_time', 'estimated_cost',
            'total_fields', 'total_tokens', 'model_used', 'status'
        ]
        
        # Only include columns that exist
        available_columns = [col for col in column_order if col in df.columns]
        df = df[available_columns]
        
        # Format numerical columns
        if 'quality_score' in df.columns:
            df['quality_score'] = df['quality_score'].round(2)
        if 'rating_score' in df.columns:
            df['rating_score'] = df['rating_score'].round(2)
        if 'processing_time' in df.columns:
            df['processing_time'] = df['processing_time'].round(1)
        if 'estimated_cost' in df.columns:
            df['estimated_cost'] = df['estimated_cost'].round(4)
        
        print("\n" + "="*120)
        print("BENCHMARK RESULTS WITH CRAWLER STRATEGIES")
        print("="*120)
        print(df.to_string(index=False, max_colwidth=20))
        print("="*120)
        
    else:
        # Manual table formatting
        print("\n" + "="*150)
        print("BENCHMARK RESULTS WITH CRAWLER STRATEGIES")
        print("="*150)
        
        # Header
        header = f"{'Institution':<25} {'Type':<15} {'Strategy':<15} {'Refresh':<8} {'Quality':<8} {'Rating':<8} {'Time(s)':<8} {'Cost':<8} {'Fields':<7} {'Tokens':<8} {'Model':<15} {'Status':<12}"
        print(header)
        print("-" * 150)
          # Rows
        for result in results:
            # Handle numeric vs string values for rating_score
            rating_display = result['rating_score'] if isinstance(result['rating_score'], str) else f"{result['rating_score']:.2f}"
            
            row = f"{result['institution_name'][:24]:<25} " \
                  f"{result['institution_type'][:14]:<15} " \
                  f"{result['crawler_strategy'][:14]:<15} " \
                  f"{str(result['force_refresh'])[:7]:<8} " \
                  f"{result['quality_score']:<8.2f} " \
                  f"{rating_display[:7]:<8} " \
                  f"{result['processing_time']:<8.1f} " \
                  f"{result['estimated_cost']:<8.4f} " \
                  f"{result['total_fields']:<7} " \
                  f"{result['total_tokens']:<8} " \
                  f"{result['model_used'][:14]:<15} " \
                  f"{result['status'][:11]:<12}"
            print(row)
        
        print("="*150)

def analyze_strategies(results: List[Dict[str, Any]]):
    """Provide analysis of crawler strategies."""
    if not results:
        return
    
    print("\n" + "="*80)
    print("CRAWLER STRATEGY ANALYSIS")
    print("="*80)
    
    # Group by strategy
    strategy_stats = {}
    for result in results:
        strategy = result['crawler_strategy']
        if strategy not in strategy_stats:
            strategy_stats[strategy] = {
                'count': 0,
                'avg_quality': 0,
                'avg_time': 0,
                'avg_cost': 0,
                'successful': 0,
                'quality_scores': [],
                'times': [],
                'costs': []
            }
        
        stats = strategy_stats[strategy]
        stats['count'] += 1
        
        # Collect numeric values
        if isinstance(result['quality_score'], (int, float)):
            stats['quality_scores'].append(result['quality_score'])
        if isinstance(result['processing_time'], (int, float)):
            stats['times'].append(result['processing_time'])
        if isinstance(result['estimated_cost'], (int, float)):
            stats['costs'].append(result['estimated_cost'])
        
        if result['status'].lower() == 'success':
            stats['successful'] += 1
    
    # Calculate averages
    for strategy, stats in strategy_stats.items():
        count = stats['count']
        if count > 0:
            stats['avg_quality'] = sum(stats['quality_scores']) / len(stats['quality_scores']) if stats['quality_scores'] else 0
            stats['avg_time'] = sum(stats['times']) / len(stats['times']) if stats['times'] else 0
            stats['avg_cost'] = sum(stats['costs']) / len(stats['costs']) if stats['costs'] else 0
            stats['success_rate'] = stats['successful'] / count * 100
    
    # Display analysis
    print(f"{'Strategy':<20} {'Count':<6} {'Avg Quality':<12} {'Avg Time':<10} {'Avg Cost':<10} {'Success %':<10}")
    print("-" * 80)
    
    for strategy, stats in strategy_stats.items():
        print(f"{strategy:<20} {stats['count']:<6} {stats['avg_quality']:<12.2f} "
              f"{stats['avg_time']:<10.1f} {stats['avg_cost']:<10.4f} {stats['success_rate']:<10.1f}")    
    print("="*80)

def write_latex_table(results: List[Dict[str, Any]], output_file: str):
    """Write results in LaTeX table format."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\\begin{table}[h!]\n")
        f.write("\\centering\n")
        f.write("\\caption{Benchmark Results with Crawler Strategies}\n")
        f.write("\\label{tab:crawler_strategies}\n")
        f.write("\\begin{tabular}{|l|l|l|l|r|r|r|r|r|l|}\n")
        f.write("\\hline\n")
        f.write("Institution & Type & Strategy & Refresh & Quality & Time(s) & Cost & Fields & Tokens & Status \\\\\n")
        f.write("\\hline\n")
        
        for result in results:
            # Escape special LaTeX characters
            institution = result['institution_name'].replace('&', '\\&').replace('_', '\\_')[:20]
            inst_type = result['institution_type'].replace('&', '\\&').replace('_', '\\_')[:12]
            strategy = result['crawler_strategy'].replace('&', '\\&').replace('_', '\\_')[:12]
            
            f.write(f"{institution} & {inst_type} & {strategy} & {str(result['force_refresh'])} & "
                   f"{result['quality_score']:.1f} & {result['processing_time']:.1f} & "
                   f"{result['estimated_cost']:.4f} & {result['total_fields']} & "
                   f"{result['total_tokens']} & {result['status']} \\\\\n")
        
        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")

def write_csv_output(results: List[Dict[str, Any]], output_file: str):
    """Write results to CSV file."""
    if not results:
        return
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['institution_name', 'institution_type', 'crawler_strategy', 'force_refresh',
                     'quality_score', 'rating_score', 'processing_time', 'estimated_cost',
                     'total_fields', 'total_tokens', 'model_used', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def main():
    parser = argparse.ArgumentParser(description='Display benchmark results with crawler strategy information')
    parser.add_argument('--benchmark-dir', '-d', 
                       default='project_cache/benchmark_results',
                       help='Directory containing benchmark results')
    parser.add_argument('--file', '-f', 
                       help='Specific file to read (JSON or CSV)')
    parser.add_argument('--format', '-fmt', 
                       choices=['table', 'pandas'], 
                       default='pandas',
                       help='Output format')
    parser.add_argument('--analysis', '-a', 
                       action='store_true',
                       help='Include strategy analysis')
    parser.add_argument('--output', '-o',
                       help='Output file path (CSV or LaTeX)')
    parser.add_argument('--latex', 
                       action='store_true',
                       help='Generate LaTeX table format')
    
    args = parser.parse_args()
    
    try:
        if args.file:
            # Use specific file
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File not found: {args.file}")
                return
            
            if file_path.suffix.lower() == '.json':
                results = load_results_from_json(str(file_path))
            elif file_path.suffix.lower() == '.csv':
                results = load_results_from_csv(str(file_path))
            else:
                print(f"Error: Unsupported file format: {file_path.suffix}")
                return
        else:
            # Find latest files
            files = find_latest_benchmark_files(args.benchmark_dir)
            
            # Prefer JSON, fallback to CSV
            if files['json']:
                print(f"Reading from: {files['json']}")
                results = load_results_from_json(files['json'])
            elif files['csv']:
                print(f"Reading from: {files['csv']}")
                results = load_results_from_csv(files['csv'])
            else:
                print("Error: No suitable benchmark files found")
                return
          # Display results
        display_results_table(results, args.format)
        
        # Optional analysis
        if args.analysis:
            analyze_strategies(results)
        
        # Output to file if requested
        if args.output:
            if args.latex or args.output.endswith('.tex'):
                write_latex_table(results, args.output)
                print(f"\nLaTeX table written to: {args.output}")
            else:
                write_csv_output(results, args.output)
                print(f"\nCSV file written to: {args.output}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
