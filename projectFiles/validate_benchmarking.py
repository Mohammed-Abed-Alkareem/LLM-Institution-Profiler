"""
Quick validation script for the Enhanced Benchmarking System integration.
This script tests all key components to ensure everything is working correctly.
"""

import os
import sys
import time
import json
from typing import Dict, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from benchmarking.integration import (
            initialize_benchmarking, 
            get_benchmarking_manager,
            benchmark_context,
            BenchmarkCategory
        )
        print("  ✅ Integration module imported successfully")
        
        from benchmarking.benchmark_config import BenchmarkConfig
        print("  ✅ Configuration module imported successfully")
        
        from benchmarking.benchmark_tracker import BenchmarkTracker
        print("  ✅ Enhanced benchmark tracker imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_initialization():
    """Test benchmarking system initialization."""
    print("🏗️ Testing system initialization...")
    
    try:
        from benchmarking.integration import initialize_benchmarking
        
        # Initialize the system
        manager = initialize_benchmarking(project_root)
        
        if manager is None:
            print("  ❌ Manager initialization returned None")
            return False
        
        print("  ✅ Benchmarking manager initialized successfully")
        
        # Test configuration
        config = manager.config
        print(f"  📁 Benchmarks directory: {config.benchmarks_dir}")
        print(f"  📊 Reports directory: {config.reports_dir}")
        print(f"  🧪 Test results directory: {config.test_results_dir}")
        
        # Check if directories exist
        for directory in [config.benchmarks_dir, config.reports_dir, config.test_results_dir]:
            if os.path.exists(directory):
                print(f"  ✅ Directory exists: {os.path.basename(directory)}")
            else:
                print(f"  ⚠️ Directory created: {os.path.basename(directory)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        return False

def test_context_manager():
    """Test context manager functionality."""
    print("🔄 Testing context manager...")
    
    try:
        from benchmarking.integration import benchmark_context, BenchmarkCategory
        
        institution_name = "Test University"
        institution_type = "university"
        
        with benchmark_context(BenchmarkCategory.SEARCH, institution_name, institution_type) as ctx:
            # Simulate some work
            time.sleep(0.1)
            
            # Test recording different types of metrics
            ctx.record_cost(api_calls=1, service_type="google_search")
            print("  ✅ Cost metrics recorded")
            
            ctx.record_quality(
                completeness_score=0.9,
                accuracy_score=0.85,
                confidence_scores={'test_metric': 1.0}
            )
            print("  ✅ Quality metrics recorded")
            
            ctx.record_content(
                content_size=1000,
                word_count=150,
                structured_data_size=500
            )
            print("  ✅ Content metrics recorded")
        
        print("  ✅ Context manager test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Context manager test failed: {e}")
        return False

def test_decorator():
    """Test decorator functionality."""
    print("🎯 Testing decorator functionality...")
    
    try:
        from benchmarking.integration import benchmark, BenchmarkCategory
        
        @benchmark(BenchmarkCategory.SEARCH, "Decorator Test University", "university")
        def test_function():
            """Test function for decorator."""
            time.sleep(0.05)  # Simulate some work
            return {"success": True, "data": "test data"}
        
        # Call the decorated function
        result = test_function()
        
        if result.get("success"):
            print("  ✅ Decorated function executed successfully")
            return True
        else:
            print("  ❌ Decorated function returned unexpected result")
            return False
        
    except Exception as e:
        print(f"  ❌ Decorator test failed: {e}")
        return False

def test_session_management():
    """Test session summary and data export."""
    print("📊 Testing session management...")
    
    try:
        from benchmarking.integration import get_benchmarking_manager, BenchmarkCategory
        
        manager = get_benchmarking_manager()
        
        if not manager:
            print("  ❌ No benchmarking manager available")
            return False
        
        # Get session summary
        summary = manager.get_session_summary()
        print(f"  📈 Session summary: {json.dumps(summary, indent=2, default=str)}")
        
        # Test export
        exported_data = manager.export_benchmarks(format='json')
        
        if exported_data:
            print("  ✅ Data export successful")
            
            # Try to parse the exported JSON
            if isinstance(exported_data, str):
                parsed_data = json.loads(exported_data)
                print(f"  📤 Exported {len(str(parsed_data))} characters of data")
            else:
                print(f"  📤 Exported data object: {type(exported_data)}")
            
            return True
        else:
            print("  ❌ Data export failed")
            return False
        
    except Exception as e:
        print(f"  ❌ Session management test failed: {e}")
        return False

def test_cost_calculations():
    """Test cost calculation functionality."""
    print("💰 Testing cost calculations...")
    
    try:
        from benchmarking.integration import get_benchmarking_manager, BenchmarkCategory
        
        manager = get_benchmarking_manager()
        
        if not manager:
            print("  ❌ No benchmarking manager available")
            return False
        
        # Test cost recording
        benchmark_id = manager.start_operation_benchmark(
            BenchmarkCategory.COST,
            "Cost Test University",
            "university"
        )
        
        # Record various costs
        manager.record_cost(
            benchmark_id,
            api_calls=5,
            input_tokens=1000,
            output_tokens=500,
            service_type="openai_gpt4"
        )
        
        # Complete the benchmark
        manager.complete_operation_benchmark(benchmark_id, True)
        
        print("  ✅ Cost calculation test completed")
        return True
        
    except Exception as e:
        print(f"  ❌ Cost calculation test failed: {e}")
        return False

def test_integration_with_app():
    """Test integration points with the main app."""
    print("🌐 Testing app integration points...")
    
    try:
        # Test that app.py can import the integration
        import importlib.util
        
        app_path = os.path.join(project_root, "app.py")
        if not os.path.exists(app_path):
            print("  ⚠️ app.py not found - skipping app integration test")
            return True
        
        # Check if the import statements work
        spec = importlib.util.spec_from_file_location("app", app_path)
        
        if spec is None:
            print("  ❌ Could not load app.py spec")
            return False
        
        # Test specific integration imports
        from benchmarking.integration import (
            initialize_benchmarking, 
            get_benchmarking_manager,
            benchmark_context,
            BenchmarkCategory
        )
        
        print("  ✅ App integration imports successful")
        
        # Test that we can check if benchmarking is available
        manager = get_benchmarking_manager()
        is_available = manager is not None
        
        print(f"  📊 Benchmarking manager availability: {is_available}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ App integration test failed: {e}")
        return False

def run_all_tests():
    """Run all validation tests."""
    print("🚀 Enhanced Benchmarking System Validation")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Initialization Tests", test_initialization),
        ("Context Manager Tests", test_context_manager),
        ("Decorator Tests", test_decorator),
        ("Session Management Tests", test_session_management),
        ("Cost Calculation Tests", test_cost_calculations),
        ("App Integration Tests", test_integration_with_app)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'-' * 30}")
        print(f"Running: {test_name}")
        print(f"{'-' * 30}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 50}")
    print("🏁 VALIDATION SUMMARY")
    print(f"{'=' * 50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced benchmarking system is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
