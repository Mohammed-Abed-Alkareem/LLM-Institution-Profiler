"""
Example usage and integration scripts for the enhanced benchmarking system.
"""

import os
import sys
import time
import json
from typing import Dict, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from benchmarking.benchmark_config import BenchmarkConfig
from benchmarking.benchmark_tracker import BenchmarkTracker
from benchmarking.benchmark_analyzer import BenchmarkAnalyzer
from benchmarking.benchmark_reporter import BenchmarkReporter
from benchmarking.test_runner import BenchmarkTestRunner, TestConfiguration


def example_single_pipeline_tracking():
    """Example: Track a single pipeline execution."""
    print("🔍 Example: Single Pipeline Tracking")
    print("=" * 50)
    
    # Initialize benchmarking system
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = BenchmarkConfig.from_base_dir(base_dir)
    tracker = BenchmarkTracker(config)
    
    # Start tracking a pipeline
    pipeline_id = tracker.start_pipeline(
        pipeline_name="enhanced_extraction_v2",
        institution_name="Harvard University",
        institution_type="university",
        pipeline_version="2.1",
        pipeline_config={
            "use_rag": True,
            "llm_model": "gpt-4",
            "max_crawl_pages": 10,
            "enable_validation": True
        }
    )
    
    print(f"📊 Started tracking pipeline: {pipeline_id}")
    
    # Simulate search phase
    print("🔍 Simulating search phase...")
    time.sleep(0.5)  # Simulate processing time
    tracker.add_search_metrics(
        pipeline_id=pipeline_id,
        search_time=0.8,
        cache_hit=False,  # API call required
        api_queries=1,
        results_count=15,
        results_quality=0.85
    )
    
    # Simulate crawling phase
    print("🕷️ Simulating crawling phase...")
    time.sleep(1.0)
    tracker.add_crawling_metrics(
        pipeline_id=pipeline_id,
        crawling_time=2.3,
        pages_crawled=8,
        pages_successful=7,
        total_content_size=524288,  # 512 KB
        content_quality=0.78
    )
    
    # Simulate LLM processing phase
    print("🤖 Simulating LLM processing phase...")
    time.sleep(0.8)
    tracker.add_llm_metrics(
        pipeline_id=pipeline_id,
        llm_time=1.5,
        model_name="gpt-4",
        input_tokens=3500,
        output_tokens=800,
        fields_requested=12,
        fields_extracted=10,
        confidence_scores={
            "name": 0.98,
            "address": 0.92,
            "founded": 0.85,
            "type": 0.95
        }
    )
    
    # Add validation results
    tracker.add_validation_results(
        pipeline_id=pipeline_id,
        validation_passed=True,
        validation_errors=[],
        accuracy_score=0.87
    )
    
    # Complete pipeline
    completed_pipeline = tracker.complete_pipeline(
        pipeline_id=pipeline_id,
        success=True,
        results_summary={
            "institution_profile": {
                "name": "Harvard University",
                "type": "Private Research University",
                "location": "Cambridge, MA",
                "founded": 1636,
                "students": 23000
            },
            "data_sources": 7,
            "confidence": 0.87
        }
    )
    
    print("✅ Pipeline completed!")
    
    # Show summary
    if completed_pipeline:
        summary = completed_pipeline.get_summary()
        print(f"\n📈 Pipeline Summary:")
        print(f"   Institution: {summary['institution_name']}")
        print(f"   Success: {summary['success']}")
        print(f"   Total Cost: ${summary['total_cost_usd']:.4f}")
        print(f"   Total Time: {summary['total_time_seconds']:.2f}s")
        print(f"   Quality Score: {summary['quality_score']:.2%}")
        print(f"   Cache Hit Rate: {summary['cache_hit_rate']:.2%}")
        print(f"   Completeness: {summary['completeness_score']:.2%}")
    
    return tracker


def example_batch_testing():
    """Example: Run batch tests with different configurations."""
    print("\n🧪 Example: Batch Testing")
    print("=" * 50)
    
    # Initialize system
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = BenchmarkConfig.from_base_dir(base_dir)
    tracker = BenchmarkTracker(config)
    test_runner = BenchmarkTestRunner(config, tracker)
    
    # Define test configurations
    test_configs = [
        TestConfiguration(
            test_name="basic_extraction_test",
            test_description="Test basic extraction without RAG",
            institution_name="MIT",
            institution_type="university",
            pipeline_config={"use_rag": False, "llm_model": "gpt-3.5-turbo"},
            expected_min_quality=0.7,
            expected_max_cost=0.05,
            expected_max_time=5.0
        ),
        TestConfiguration(
            test_name="enhanced_extraction_test",
            test_description="Test enhanced extraction with RAG",
            institution_name="MIT",
            institution_type="university",
            pipeline_config={"use_rag": True, "llm_model": "gpt-4"},
            expected_min_quality=0.8,
            expected_max_cost=0.15,
            expected_max_time=10.0
        ),
        TestConfiguration(
            test_name="fast_extraction_test",
            test_description="Test optimized for speed",
            institution_name="MIT",
            institution_type="university",
            pipeline_config={"use_rag": False, "llm_model": "gpt-3.5-turbo", "max_crawl_pages": 3},
            expected_min_quality=0.6,
            expected_max_cost=0.03,
            expected_max_time=3.0
        )
    ]
    
    # Mock pipeline function
    def mock_pipeline_function(institution_name: str, institution_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock pipeline function that simulates different performance based on configuration."""
        import random
        
        # Simulate different performance characteristics
        use_rag = config.get("use_rag", False)
        llm_model = config.get("llm_model", "gpt-3.5-turbo")
        max_pages = config.get("max_crawl_pages", 10)
        
        # Simulate processing time based on configuration
        base_time = 1.0
        if use_rag:
            base_time += 2.0
        if "gpt-4" in llm_model:
            base_time += 1.0
        if max_pages > 5:
            base_time += 0.5
        
        processing_time = base_time + random.uniform(-0.5, 1.0)
        time.sleep(min(processing_time, 3.0))  # Cap sleep time for demo
        
        # Simulate quality based on configuration
        base_quality = 0.7
        if use_rag:
            base_quality += 0.1
        if "gpt-4" in llm_model:
            base_quality += 0.05
        
        quality = min(1.0, base_quality + random.uniform(-0.1, 0.1))
        
        # Simulate cost based on configuration
        base_cost = 0.02
        if use_rag:
            base_cost += 0.03
        if "gpt-4" in llm_model:
            base_cost += 0.05
        
        cost = base_cost + random.uniform(-0.01, 0.02)
        
        return {
            'success': random.choice([True, True, True, False]),  # 75% success rate
            'processing_time': processing_time,
            'quality_score': quality,
            'cost_estimate': max(0, cost),
            'data_extracted': {
                'name': institution_name,
                'type': institution_type,
                'config_used': config
            }
        }
    
    print(f"🏃 Running {len(test_configs)} test configurations...")
    
    # Run batch tests
    results = test_runner.run_batch_tests(
        test_configs,
        mock_pipeline_function,
        parallel=True
    )
    
    # Show results
    summary = test_runner.get_test_session_summary()
    print(f"\n✅ Batch testing completed!")
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   Successful: {summary['successful_tests']}")
    print(f"   Success Rate: {summary['success_rate_percent']:.1f}%")
    print(f"   Average Quality: {summary['average_quality_score']:.2%}")
    print(f"   Total Cost: ${summary['total_cost_usd']:.4f}")
    
    # Show individual test results
    print(f"\n📊 Individual Test Results:")
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"   {status} {result.test_name}: {result.execution_time:.1f}s, ${result.cost_usd:.4f}, {result.quality_score:.2%}")
    
    return test_runner


def example_ab_testing():
    """Example: A/B test between different pipeline configurations."""
    print("\n⚖️ Example: A/B Testing")
    print("=" * 50)
    
    # Initialize system
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = BenchmarkConfig.from_base_dir(base_dir)
    tracker = BenchmarkTracker(config)
    test_runner = BenchmarkTestRunner(config, tracker)
    
    # Define baseline and test configurations
    baseline_config = {
        "use_rag": False,
        "llm_model": "gpt-3.5-turbo",
        "max_crawl_pages": 5,
        "enable_validation": False
    }
    
    test_configs = [
        {
            "use_rag": True,
            "llm_model": "gpt-3.5-turbo",
            "max_crawl_pages": 5,
            "enable_validation": False
        },
        {
            "use_rag": False,
            "llm_model": "gpt-4",
            "max_crawl_pages": 5,
            "enable_validation": True
        },
        {
            "use_rag": True,
            "llm_model": "gpt-4",
            "max_crawl_pages": 10,
            "enable_validation": True
        }
    ]
    
    # Mock pipeline function
    def mock_pipeline_function(institution_name: str, institution_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced mock function for A/B testing."""
        import random
        
        # Calculate performance based on configuration
        use_rag = config.get("use_rag", False)
        llm_model = config.get("llm_model", "gpt-3.5-turbo")
        max_pages = config.get("max_crawl_pages", 5)
        enable_validation = config.get("enable_validation", False)
        
        # Cost calculation
        cost = 0.02  # Base cost
        if use_rag:
            cost += 0.03
        if "gpt-4" in llm_model:
            cost += 0.04
        cost += max_pages * 0.001
        if enable_validation:
            cost += 0.01
        
        # Quality calculation
        quality = 0.65  # Base quality
        if use_rag:
            quality += 0.15
        if "gpt-4" in llm_model:
            quality += 0.10
        if enable_validation:
            quality += 0.05
        
        # Time calculation
        time_taken = 2.0  # Base time
        if use_rag:
            time_taken += 3.0
        if "gpt-4" in llm_model:
            time_taken += 1.5
        time_taken += max_pages * 0.2
        if enable_validation:
            time_taken += 0.5
        
        # Add some randomness
        cost += random.uniform(-0.005, 0.005)
        quality = min(1.0, quality + random.uniform(-0.05, 0.05))
        time_taken += random.uniform(-0.5, 0.5)
        
        # Simulate processing
        time.sleep(min(time_taken / 5, 2.0))  # Scale down for demo
        
        return {
            'success': random.choice([True] * 9 + [False]),  # 90% success rate
            'processing_time': time_taken,
            'quality_score': quality,
            'cost_estimate': max(0, cost),
            'configuration': config
        }
    
    print("🔬 Running A/B test with 3 iterations per configuration...")
    
    # Run A/B test
    ab_results = test_runner.run_ab_test(
        test_name="pipeline_optimization_ab_test",
        institution_name="Stanford University",
        institution_type="university",
        baseline_config=baseline_config,
        test_configs=test_configs,
        pipeline_function=mock_pipeline_function,
        iterations=3
    )
    
    # Show A/B test results
    print(f"\n🏆 A/B Test Results:")
    print(f"   Test Name: {ab_results['test_name']}")
    print(f"   Configurations Tested: {ab_results['configurations_tested']}")
    print(f"   Iterations per Config: {ab_results['iterations_per_config']}")
    
    analysis = ab_results.get('analysis', {})
    summary_stats = analysis.get('summary_stats', {})
    
    print(f"\n📊 Performance Summary:")
    for config_name, stats in summary_stats.items():
        print(f"   {config_name}:")
        print(f"     Avg Cost: ${stats.get('avg_cost_usd', 0):.4f}")
        print(f"     Avg Time: {stats.get('avg_execution_time', 0):.1f}s")
        print(f"     Avg Quality: {stats.get('avg_quality_score', 0):.2%}")
        print(f"     Success Rate: {stats.get('success_rate', 0):.1%}")
    
    winner = analysis.get('winner', 'unknown')
    print(f"\n🥇 Winner: {winner}")
    
    recommendations = analysis.get('recommendations', [])
    if recommendations:
        print(f"\n💡 Recommendations:")
        for rec in recommendations:
            print(f"   • {rec}")
    
    return ab_results


def example_analysis_and_reporting():
    """Example: Generate analysis and reports."""
    print("\n📊 Example: Analysis and Reporting")
    print("=" * 50)
    
    # Initialize system
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = BenchmarkConfig.from_base_dir(base_dir)
    analyzer = BenchmarkAnalyzer(config)
    reporter = BenchmarkReporter(config, analyzer)
    
    print("🔍 Analyzing benchmark data...")
    
    # Generate comprehensive analysis
    analysis = analyzer.generate_comprehensive_report()
    
    # Show data summary
    data_summary = analysis.get('data_summary', {})
    print(f"\n📈 Data Summary:")
    print(f"   Total Operations: {data_summary.get('total_operations', 0)}")
    print(f"   Success Rate: {data_summary.get('success_rate_percent', 0):.1f}%")
    print(f"   Total Cost: ${data_summary.get('total_cost_usd', 0):.2f}")
    print(f"   Avg Response Time: {data_summary.get('avg_response_time_seconds', 0):.1f}s")
    print(f"   Avg Quality: {data_summary.get('avg_quality_score', 0):.1%}")
    
    # Show performance trends
    trends = analysis.get('performance_trends', [])
    if trends:
        print(f"\n📈 Performance Trends:")
        for trend in trends:
            direction_emoji = {'improving': '📈', 'degrading': '📉', 'stable': '➡️'}.get(trend.get('trend_direction'), '❓')
            print(f"   {direction_emoji} {trend.get('metric_name', 'Unknown').title()}: {trend.get('trend_direction', 'stable')} ({trend.get('change_percent', 0):.1f}% change)")
    
    # Show anomalies
    anomalies = analysis.get('anomalies', [])
    if anomalies:
        print(f"\n⚠️ Anomalies Detected:")
        for anomaly in anomalies:
            severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}.get(anomaly.get('severity'), '⚪')
            print(f"   {severity_emoji} {anomaly.get('description', 'Unknown anomaly')} ({anomaly.get('severity', 'low')})")
    
    # Show insights
    insights = analysis.get('insights', [])
    if insights:
        print(f"\n💡 Performance Insights:")
        for insight in insights[:3]:  # Show top 3
            priority_emoji = {'critical': '🔥', 'high': '⚡', 'medium': '💡', 'low': '💭'}.get(insight.get('priority'), '💭')
            print(f"   {priority_emoji} {insight.get('title', 'Unknown')} ({insight.get('priority', 'low')} priority)")
            print(f"      {insight.get('recommendation', 'No recommendation')}")
    
    # Generate reports
    print(f"\n📋 Generating reports...")
    
    try:
        # HTML Dashboard
        html_report = reporter.generate_dashboard_report('html')
        print(f"   ✅ HTML Dashboard: {html_report}")
        
        # JSON Report
        json_report = reporter.generate_dashboard_report('json')
        print(f"   ✅ JSON Report: {json_report}")
        
        # CSV Export
        csv_export = reporter.generate_csv_export('all')
        print(f"   ✅ CSV Export: {csv_export}")
        
        # Markdown Report
        md_report = reporter.generate_dashboard_report('markdown')
        print(f"   ✅ Markdown Report: {md_report}")
        
        print(f"\n🌐 Open HTML dashboard in browser:")
        print(f"   file://{os.path.abspath(html_report)}")
        
    except Exception as e:
        print(f"   ❌ Error generating reports: {e}")
    
    return analysis


def create_sample_test_config():
    """Create a sample test configuration file."""
    print("\n📄 Creating sample test configuration...")
    
    sample_config = {
        "description": "Sample test configuration for Institution Profiler benchmarking",
        "tests": [
            {
                "test_name": "university_basic_test",
                "test_description": "Basic extraction test for universities",
                "institution_name": "Harvard University",
                "institution_type": "university",
                "pipeline_config": {
                    "use_rag": False,
                    "llm_model": "gpt-3.5-turbo",
                    "max_crawl_pages": 5
                },
                "iterations": 1,
                "expected_min_quality": 0.7,
                "expected_max_cost": 0.05,
                "expected_max_time": 5.0
            },
            {
                "test_name": "university_enhanced_test",
                "test_description": "Enhanced extraction test with RAG",
                "institution_name": "MIT",
                "institution_type": "university",
                "pipeline_config": {
                    "use_rag": True,
                    "llm_model": "gpt-4",
                    "max_crawl_pages": 10,
                    "enable_validation": True
                },
                "iterations": 1,
                "expected_min_quality": 0.8,
                "expected_max_cost": 0.15,
                "expected_max_time": 10.0
            },
            {
                "test_name": "hospital_test",
                "test_description": "Test extraction for medical institutions",
                "institution_name": "Mayo Clinic",
                "institution_type": "hospital",
                "pipeline_config": {
                    "use_rag": True,
                    "llm_model": "gpt-4",
                    "max_crawl_pages": 8,
                    "medical_focus": True
                },
                "iterations": 1,
                "expected_min_quality": 0.75,
                "expected_max_cost": 0.12,
                "expected_max_time": 8.0
            }
        ]
    }
    
    config_file = "sample_test_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Sample configuration created: {config_file}")
    return config_file


def main():
    """Run all examples."""
    print("🚀 Institution Profiler Enhanced Benchmarking Examples")
    print("=" * 60)
    
    try:
        # Run examples
        tracker = example_single_pipeline_tracking()
        test_runner = example_batch_testing()
        ab_results = example_ab_testing()
        analysis = example_analysis_and_reporting()
        
        # Create sample config
        config_file = create_sample_test_config()
        
        print(f"\n🎉 All examples completed successfully!")
        print(f"\n📚 Next steps:")
        print(f"   1. Use the CLI: python benchmarking/cli.py --help")
        print(f"   2. Run your own tests: python benchmarking/cli.py test --config {config_file}")
        print(f"   3. Generate reports: python benchmarking/cli.py report --type dashboard --format html")
        print(f"   4. Analyze trends: python benchmarking/cli.py analyze --days 30")
        
        # Show session summary
        session_summary = tracker.get_session_summary()
        print(f"\n📊 Session Summary:")
        print(f"   Pipelines Tracked: {session_summary['pipelines_count']}")
        print(f"   Success Rate: {session_summary['success_rate_percent']:.1f}%")
        print(f"   Total Cost: ${session_summary['total_cost_usd']:.4f}")
        print(f"   Average Quality: {session_summary['average_quality_score']:.2%}")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
