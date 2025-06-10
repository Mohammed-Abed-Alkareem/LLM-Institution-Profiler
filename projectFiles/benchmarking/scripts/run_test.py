#!/usr/bin/env python3
"""
Test runner script for the benchmarking system
"""
import sys
import os
import json

# Add the project files directory to the path
project_files = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..')
test_config_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(project_files, 'benchmarking', 'test_config_quick.json')

sys.path.insert(0, project_files)

try:
    from benchmarking.integration import get_benchmarking_manager, initialize_benchmarking
    
    print('🔧 Initializing benchmarking system...')
    manager = initialize_benchmarking(project_files)
    
    print(f'📄 Loading test configuration from: {test_config_path}')
    if not os.path.exists(test_config_path):
        print(f'❌ Test configuration not found: {test_config_path}')
        sys.exit(1)
    
    with open(test_config_path, 'r') as f:
        config = json.load(f)
    print(f'🧪 Running test: {config.get("test_suite_name", "Unnamed Test")}')
    
    # Run a simple benchmark test using context manager
    from benchmarking.integration import benchmark_context, BenchmarkCategory
    
    # Use test suite name for benchmark
    test_name = config.get("test_suite_name", "test_session")
    
    with benchmark_context(BenchmarkCategory.SEARCH, test_name, 'test') as ctx:
        print('⏱️  Starting benchmark session...')
        
        # Simulate some operations based on test config
        test_operations = config.get('test_operations', ['test_operation'])
        
        # If no test_operations, use test configurations
        if 'test_configurations' in config:
            test_operations = [tc.get('test_name', 'test_op') for tc in config['test_configurations']]
        
        for operation in test_operations:
            print(f'   🔄 Running operation: {operation}')
            
            # Simulate work
            import time
            time.sleep(0.1)
            
            # Log some metrics
            ctx.record_cost(api_calls=1, service_type="google_search")
            ctx.record_quality(completeness_score=0.95, accuracy_score=0.9)
        
        print('📊 Test operations completed')
    
    # Get results
    summary = manager.get_session_summary()
    print(f'📈 Test Results: {summary}')
    
    print('✅ Benchmark test completed successfully!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
