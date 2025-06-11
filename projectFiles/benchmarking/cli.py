"""
CLI interface for the enhanced benchmarking system.
"""

import os
import sys
import argparse
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from benchmarking.benchmark_config import BenchmarkConfig
from benchmarking.benchmark_tracker import BenchmarkTracker
from benchmarking.benchmark_analyzer import BenchmarkAnalyzer
from benchmarking.benchmark_reporter import BenchmarkReporter
from benchmarking.test_runner import BenchmarkTestRunner, TestConfiguration


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Institution Profiler Enhanced Benchmarking System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze benchmark data')
    analyze_parser.add_argument('--days', type=int, default=30, help='Days of data to analyze')
    analyze_parser.add_argument('--output', default='dashboard.html', help='Output file name')
    analyze_parser.add_argument('--format', choices=['html', 'json', 'markdown'], default='html', help='Output format')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate reports')
    report_parser.add_argument('--type', choices=['dashboard', 'csv', 'comparison'], default='dashboard', help='Report type')
    report_parser.add_argument('--format', choices=['html', 'json', 'markdown', 'csv'], default='html', help='Output format')
    report_parser.add_argument('--data-type', choices=['all', 'successful', 'failed'], default='all', help='Data to include')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run benchmark tests')
    test_parser.add_argument('--config', required=True, help='Test configuration file (JSON)')
    test_parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean old benchmark data')
    clean_parser.add_argument('--days', type=int, default=30, help='Keep data newer than X days')
    clean_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show benchmark system status')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export benchmark data')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='csv', help='Export format')
    export_parser.add_argument('--data-type', choices=['all', 'successful', 'failed'], default='all', help='Data to export')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize system
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = BenchmarkConfig.from_base_dir(base_dir)
    
    try:
        if args.command == 'analyze':
            handle_analyze_command(config, args)
        elif args.command == 'report':
            handle_report_command(config, args)
        elif args.command == 'test':
            handle_test_command(config, args)
        elif args.command == 'clean':
            handle_clean_command(config, args)
        elif args.command == 'status':
            handle_status_command(config, args)
        elif args.command == 'export':
            handle_export_command(config, args)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


def handle_analyze_command(config: BenchmarkConfig, args):
    """Handle the analyze command."""
    print("🔍 Analyzing benchmark data...")
    
    analyzer = BenchmarkAnalyzer(config)
    reporter = BenchmarkReporter(config, analyzer)
    
    # Generate comprehensive report
    if args.format in ['html', 'json', 'markdown']:
        report_file = reporter.generate_dashboard_report(args.format)
        print(f"✅ Analysis complete! Report saved to: {report_file}")
        
        if args.format == 'html':
            print(f"📊 Open the report in your browser: file://{os.path.abspath(report_file)}")
    
    # Also show quick summary in terminal
    analysis = analyzer.generate_comprehensive_report()
    data_summary = analysis.get('data_summary', {})
    
    print(f"\n📈 Quick Summary:")
    print(f"   Total Operations: {data_summary.get('total_operations', 0)}")
    print(f"   Success Rate: {data_summary.get('success_rate_percent', 0):.1f}%")
    print(f"   Total Cost: ${data_summary.get('total_cost_usd', 0):.2f}")
    print(f"   Avg Response Time: {data_summary.get('avg_response_time_seconds', 0):.1f}s")
    print(f"   Data Coverage: {data_summary.get('analysis_coverage', 'unknown')}")
    
    # Show top recommendations
    recommendations = analysis.get('recommendations', [])
    if recommendations:
        print(f"\n🎯 Top Recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. {rec.get('title', 'Unknown')} ({rec.get('priority', 'low')} priority)")


def handle_report_command(config: BenchmarkConfig, args):
    """Handle the report command."""
    print(f"📋 Generating {args.type} report in {args.format} format...")
    
    analyzer = BenchmarkAnalyzer(config)
    reporter = BenchmarkReporter(config, analyzer)
    
    if args.type == 'dashboard':
        report_file = reporter.generate_dashboard_report(args.format)
    elif args.type == 'csv':
        report_file = reporter.generate_csv_export(args.data_type)
    elif args.type == 'comparison':
        # For comparison reports, we'd need additional parameters
        # For now, using placeholder dates
        baseline_date = "2025-06-01"
        comparison_date = "2025-06-10"
        report_file = reporter.generate_performance_comparison_report(baseline_date, comparison_date)
    
    print(f"✅ Report generated: {report_file}")
    
    if args.format == 'html':
        print(f"🌐 Open in browser: file://{os.path.abspath(report_file)}")


def handle_test_command(config: BenchmarkConfig, args):
    """Handle the test command."""
    print(f"🧪 Running benchmark tests from: {args.config}")
    
    # Load test configuration
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            test_config_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Test configuration file not found: {args.config}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in test configuration: {e}")
        sys.exit(1)
      # Initialize test runner
    tracker = BenchmarkTracker(config)
    test_runner = BenchmarkTestRunner(config, tracker)
    
    # Convert config to TestConfiguration objects
    test_configurations = []
    for test_data in test_config_data.get('tests', []):
        test_config = TestConfiguration(
            test_name=test_data.get('test_name', 'Unknown Test'),
            test_description=test_data.get('test_description', ''),
            institution_name=test_data.get('institution_name', 'Test Institution'),
            institution_type=test_data.get('institution_type', 'university'),
            pipeline_config=test_data.get('pipeline_config', {}),
            iterations=test_data.get('iterations', 1),
            expected_min_quality=test_data.get('expected_min_quality', 0.0),
            expected_max_cost=test_data.get('expected_max_cost', float('inf')),
            expected_max_time=test_data.get('expected_max_time', float('inf'))
        )
        test_configurations.append(test_config)
    
    if not test_configurations:
        print("❌ No test configurations found in file")
        sys.exit(1)
    
    # Mock pipeline function for demonstration
    def mock_pipeline_function(institution_name: str, institution_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock pipeline function for testing."""
        import time
        import random
        
        # Simulate processing time
        time.sleep(random.uniform(0.5, 2.0))
        
        # Mock results
        return {
            'success': random.choice([True, True, True, False]),  # 75% success rate
            'data_extracted': {'name': institution_name, 'type': institution_type},
            'cost_estimate': random.uniform(0.01, 0.10),
            'quality_score': random.uniform(0.6, 0.95)
        }
    
    print(f"🏃 Running {len(test_configurations)} test configurations...")
    
    # Run tests
    results = test_runner.run_batch_tests(
        test_configurations,
        mock_pipeline_function,
        parallel=args.parallel
    )
    
    # Show results summary
    summary = test_runner.get_test_session_summary()
    print(f"\n✅ Tests completed!")
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   Successful: {summary['successful_tests']}")
    print(f"   Failed: {summary['failed_tests']}")
    print(f"   Success Rate: {summary['success_rate_percent']:.1f}%")
    print(f"   Total Cost: ${summary['total_cost_usd']:.4f}")
    print(f"   Total Time: {summary['total_execution_time_seconds']:.1f}s")
    
    # Export results
    results_file = test_runner.export_test_results('json')
    print(f"📄 Detailed results saved to: {results_file}")


def handle_clean_command(config: BenchmarkConfig, args):
    """Handle the clean command."""
    if args.dry_run:
        print(f"🔍 Dry run: Checking what would be cleaned (data older than {args.days} days)...")
    else:
        print(f"🧹 Cleaning benchmark data older than {args.days} days...")
    tracker = BenchmarkTracker(config)
    result = tracker.cleanup_old_data(args.days)
    
    if 'error' in result:
        print(f"❌ Cleanup failed: {result['error']}")
        sys.exit(1)
    
    if args.dry_run:
        print(f"📊 Would clean:")
        print(f"   Files: {result.get('cleaned_files', 0)}")
        print(f"   Benchmarks: {result.get('cleaned_benchmarks', 0)}")
        print(f"   Cutoff date: {result.get('cutoff_date', 'unknown')}")
    else:
        print(f"✅ Cleanup completed:")
        print(f"   Files cleaned: {result.get('cleaned_files', 0)}")
        print(f"   Benchmarks cleaned: {result.get('cleaned_benchmarks', 0)}")
        print(f"   Cutoff date: {result.get('cutoff_date', 'unknown')}")


def handle_status_command(config: BenchmarkConfig, args):
    """Handle the status command."""
    print("📊 Benchmark System Status")
    print("=" * 50)
    
    # Check directories
    dirs_status = {
        'Benchmarks': config.benchmarks_dir,
        'Reports': config.reports_dir,
        'Test Results': config.test_results_dir
    }
    
    for name, path in dirs_status.items():
        exists = "✅" if os.path.exists(path) else "❌"
        print(f"{name} Directory: {exists} {path}")
    
    # Check data availability
    analyzer = BenchmarkAnalyzer(config)
    data_count = len(analyzer.benchmarks_data)
    print(f"\nData Available: {data_count} benchmark records")
    
    if data_count > 0:
        # Show recent activity
        recent_data = sorted(
            analyzer.benchmarks_data,
            key=lambda x: x.get('latency_metrics', {}).get('start_timestamp', 0),
            reverse=True
        )[:5]
        
        print(f"\n📈 Recent Activity (last 5 operations):")
        for i, record in enumerate(recent_data, 1):
            timestamp = record.get('latency_metrics', {}).get('start_timestamp', 0)
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M') if timestamp > 0 else 'Unknown'
            institution = record.get('institution_name', 'Unknown')
            success = "✅" if record.get('success', False) else "❌"
            print(f"   {i}. {date_str} - {institution} {success}")
    
    # Check configuration
    print(f"\n⚙️ Configuration:")
    print(f"   Cost Tracking: {'✅' if config.enable_cost_tracking else '❌'}")
    print(f"   Quality Tracking: {'✅' if config.enable_quality_tracking else '❌'}")
    print(f"   Auto Reports: {'✅' if config.auto_generate_reports else '❌'}")
    print(f"   Parallel Tests: {'✅' if config.parallel_tests else '❌'}")


def handle_export_command(config: BenchmarkConfig, args):
    """Handle the export command."""
    print(f"📤 Exporting benchmark data in {args.format} format...")
    
    analyzer = BenchmarkAnalyzer(config)
    reporter = BenchmarkReporter(config, analyzer)
    
    if args.format == 'csv':
        export_file = reporter.generate_csv_export(args.data_type)
    elif args.format == 'json':
        # Generate JSON export
        export_file = os.path.join(
            config.reports_dir,
            config.get_report_filename(f'export_{args.data_type}', 'json')
        )
        
        # Filter data based on type
        if args.data_type == 'successful':
            data = [b for b in analyzer.benchmarks_data if b.get('success', False)]
        elif args.data_type == 'failed':
            data = [b for b in analyzer.benchmarks_data if not b.get('success', False)]
        else:
            data = analyzer.benchmarks_data
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'data_type': args.data_type,
            'total_records': len(data),
            'benchmarks': data
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Export completed: {export_file}")
    print(f"📁 File size: {os.path.getsize(export_file) / 1024:.1f} KB")


if __name__ == '__main__':
    main()
