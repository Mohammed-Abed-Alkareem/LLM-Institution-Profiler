#!/usr/bin/env python3
"""
Status check script for the benchmarking system
"""
import sys
import os

# Add the project files directory to the path
project_files = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_files)

try:
    from benchmarking.integration import get_benchmarking_manager, initialize_benchmarking
    from benchmarking.benchmark_config import BenchmarkConfig
    
    print('🔧 Initializing benchmarking system...')
    manager = initialize_benchmarking(project_files)
    
    config = manager.config
    
    print('✅ Benchmarking System Status:')
    print(f'   📁 Benchmarks Directory: {config.benchmarks_dir}')
    print(f'   📊 Reports Directory: {config.reports_dir}')
    print(f'   🧪 Test Results Directory: {config.test_results_dir}')
    print(f'   💰 Cost Tracking: {"Enabled" if config.enable_cost_tracking else "Disabled"}')
    print(f'   ⏱️  Latency Tracking: {"Enabled" if config.enable_latency_tracking else "Disabled"}')
    print(f'   🎯 Quality Tracking: {"Enabled" if config.enable_quality_tracking else "Disabled"}')
    
    summary = manager.get_session_summary()
    print(f'   📈 Session Summary: {summary}')
    
    print('✅ Status check completed successfully!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
