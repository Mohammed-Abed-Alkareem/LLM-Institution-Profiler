# -*- coding: utf-8 -*-
"""
Enhanced Comprehensive Test Runner for Institution Benchmarking

This module provides enhanced test running capabilities with quality score integration,
output type testing, and comprehensive analysis generation.
"""

import json
import time
import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

# Add project directory to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from benchmarking.quality_score_integration import QualityScoreIntegrator
from benchmarking.benchmark_config import BenchmarkCategory
from benchmarking.integration import get_benchmarking_manager, initialize_benchmarking
# Remove institution_processor import to avoid circular dependency - import inside functions where needed
from api.service_init import initialize_services


class NumpyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super().default(obj)

# Create fresh quality integrator instance
quality_integrator = QualityScoreIntegrator()


@dataclass
class ComprehensiveTestResult:
    """Enhanced test result with comprehensive metrics from pipeline."""
    institution_name: str
    institution_type: str
    output_type: str
    success: bool
    execution_time: float
    cost_usd: float
    
    # Core quality metrics (from web interface)
    core_quality_score: float
    core_quality_rating: str
    completeness_score: float
    fields_extracted: int
    fields_requested: int
    
    # Enhanced quality metrics
    critical_fields_completion: float
    important_fields_completion: float
    specialized_fields_completion: float
    content_quality_score: float
    relevance_score: float
    
    # Pipeline success metrics
    search_success: bool
    crawling_success: bool
    extraction_success: bool
    overall_pipeline_success: bool
    
    # Output type specific metrics
    data_size_bytes: int
    serialization_complexity: float
    information_density: float
    
    # Performance metrics
    cache_hit_rate: float
    network_requests: int
    processing_phases_completed: int
    total_pipeline_time: float
    search_time: float
    crawling_time: float
    extraction_time: float
    
    # Crawling metrics
    success_rate: float
    total_urls_requested: int
    successful_crawls: int
    failed_crawls: int
    content_size_mb: float
    compression_ratio: float
    
    # Cost breakdown
    google_search_cost: float
    llm_cost: float
    infrastructure_cost: float
    google_search_queries: int
    llm_model_used: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
    # Error information
    error_message: str = ""
    
    # Error information
    error_message: Optional[str] = None
    validation_errors: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['timestamp'] = datetime.now().isoformat()
        return result


class ComprehensiveTestRunner:
    """Enhanced test runner with quality score integration and output type testing."""
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        
        # Initialize benchmarking system
        print("🔧 Initializing benchmarking system...")
        self.benchmarking_manager = initialize_benchmarking(base_dir)
        print("✅ Benchmarking system initialized")
          # Initialize crawler service with proper caching (same as main app)        print("🔧 Initializing crawler service with caching...")        
        services = initialize_services(base_dir)
        self.crawler_service = services.get('crawler')
        self.search_service = services.get('search')
        
        # Import here to avoid circular dependency
        from institution_processor import set_global_crawler_service, set_global_search_service
        
        if self.crawler_service:
            # Set the global crawler service so the pipeline uses it
            set_global_crawler_service(self.crawler_service)
            print("✅ Crawler service initialized with caching enabled")
        else:
            print("⚠️ Warning: Crawler service initialization failed")
        if self.search_service:
            # Set the global search service so the pipeline uses it
            set_global_search_service(self.search_service)
            print("✅ Search service initialized with caching enabled")
        else:
            print("⚠️ Warning: Search service initialization failed")
            
        # Pre-initialize the pipeline to ensure it uses the cached services
        print("🔧 Pre-initializing pipeline with cached services...")
        from institution_processor import _get_pipeline_instance
        pipeline = _get_pipeline_instance()
        print("✅ Pipeline pre-initialized with cached services")
        
        self.results: List[ComprehensiveTestResult] = []
        self.test_counter = 0
        self.live_table_interval = 5  # Update table every 5 tests
        
        # Initialize live table headers
        self._print_table_header()
        
    def _print_table_header(self):
        """Print the header for the live results table."""
        print("\n" + "="*120)
        print("🔥 LIVE BENCHMARK RESULTS TABLE")
        print("="*120)
        header = f"{'Institution':<25} {'Type':<12} {'Format':<12} {'Quality':<8} {'Rating':<12} {'Time(s)':<8} {'Cost($)':<10} {'Fields':<8} {'Status':<10}"
        print(header)
        print("-"*120)
    
    def _print_table_row(self, result: ComprehensiveTestResult):
        """Print a single row in the live results table."""
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        row = f"{result.institution_name[:24]:<25} {result.institution_type[:11]:<12} {result.output_type:<12} {result.core_quality_score:<8.1f} {result.core_quality_rating[:11]:<12} {result.execution_time:<8.1f} ${result.cost_usd:<9.4f} {result.fields_extracted:<8} {status:<10}"
        print(row)
    
    def _print_summary_stats(self):
        """Print current summary statistics."""
        if not self.results:
            return
            
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        avg_quality = sum(r.core_quality_score for r in self.results) / total_tests
        total_cost = sum(r.cost_usd for r in self.results)
        avg_time = sum(r.execution_time for r in self.results) / total_tests
        
        print(f"\n📊 RUNNING STATS: {successful_tests}/{total_tests} successful | Avg Quality: {avg_quality:.1f} | Total Cost: ${total_cost:.4f} | Avg Time: {avg_time:.1f}s")
        print("-"*120)
    
    def _add_result_and_update_table(self, result: ComprehensiveTestResult):
        """Add result and update live table if needed."""
        self.results.append(result)
        self.test_counter += 1
        
        # Always print the current result
        self._print_table_row(result)
        
        # Print summary every N tests
        if self.test_counter % self.live_table_interval == 0:
            self._print_summary_stats()
    
    def run_comprehensive_test_suite(self, config_file: str) -> Dict[str, Any]:
        """
        Run the comprehensive test suite with enhanced metrics and analysis.
        
        Args:
            config_file: Path to the test configuration JSON file
            
        Returns:
            Comprehensive test results and analysis
        """
        print("🚀 Starting Comprehensive Institution Benchmark Test Suite...")
        start_time = time.time()
        
        # Load test configuration
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"📋 Test Suite: {config.get('test_suite_name', 'Unknown')}")
        print(f"📝 Description: {config.get('description', 'No description')}")
        
        # Run all test configurations
        for test_config in config.get('test_configurations', []):
            print(f"\n🧪 Running Test: {test_config.get('test_name', 'Unknown')}")
            self._run_test_configuration(test_config)        # Generate comprehensive analysis
        total_time = time.time() - start_time
        analysis = self._generate_comprehensive_analysis()
        
        # Display final summary
        print(f"\n{'='*140}")
        print("🏆 COMPREHENSIVE BENCHMARK RESULTS SUMMARY")
        print(f"{'='*140}")
        self._print_summary_stats()
        
        # Generate output files
        output_files = self._generate_output_files(config, analysis)
        
        print(f"\n✅ Test Suite Completed in {total_time:.2f} seconds")
        print(f"📊 Total Tests: {len(self.results)}")
        print(f"✅ Successful: {sum(1 for r in self.results if r.success)}")
        print(f"❌ Failed: {sum(1 for r in self.results if not r.success)}")
        
        print(f"\n📁 Generated Output Files:")
        for i, file_path in enumerate(output_files, 1):
            file_name = os.path.basename(file_path)
            if 'comprehensive_benchmark_results_' in file_name and file_name.endswith('.json'):
                print(f"   {i}. {file_name} - Complete results data (JSON)")
            elif 'comprehensive_benchmark_results_' in file_name and file_name.endswith('.csv'):
                print(f"   {i}. {file_name} - Detailed results table (CSV)")
            elif 'comprehensive_benchmark_analysis_' in file_name:
                print(f"   {i}. {file_name} - Interactive analysis report (HTML)")
            elif 'comprehensive_benchmark_report_' in file_name:
                print(f"   {i}. {file_name} - Formatted report (Markdown)")
            elif 'benchmark_summary_table_' in file_name:
                print(f"   {i}. {file_name} - Summary table (Text)")
            elif 'benchmark_summary_' in file_name:
                print(f"   {i}. {file_name} - Analysis summary (JSON)")
            else:
                print(f"   {i}. {file_name}")
        
        print(f"\n💡 Open the HTML file in a browser for interactive analysis")
        print(f"📊 Use the CSV file for data analysis in Excel/Pandas")
        print(f"📝 Read the Markdown file for formatted report")
        print(f"📋 Check the text file for quick summary table")
        
        return {
            'summary': {
                'total_tests': len(self.results),
                'successful_tests': sum(1 for r in self.results if r.success),
                'failed_tests': sum(1 for r in self.results if not r.success),
                'total_execution_time': total_time,
                'output_files': output_files
            },
            'analysis': analysis,
            'results': [r.to_dict() for r in self.results]
        }
    
    def _run_test_configuration(self, test_config: Dict[str, Any]):
        """Run a single test configuration with multiple institutions and output types."""
        institutions = test_config.get('institutions', [])
        output_types = test_config.get('output_types', ['json'])
        iterations = test_config.get('iterations', 1)
        
        print(f"   📈 Testing {len(institutions)} institutions x {len(output_types)} output types x {iterations} iterations")
        
        for institution in institutions:
            for output_type in output_types:
                for iteration in range(iterations):
                    self._run_single_test(
                        institution, 
                        output_type, 
                        test_config.get('category', 'pipeline'),                        iteration + 1,
                        iterations
                    )
    
    def _run_single_test(
        self, 
        institution: Dict[str, Any], 
        output_type: str, 
        category: str,
        iteration: int,
        total_iterations: int
    ):
        """Run a single test case with comprehensive metrics collection."""
        # Import here to avoid circular dependency
        from institution_processor import process_institution_pipeline
        
        institution_name = institution.get('institution_name', 'Unknown')
        institution_type = institution.get('institution_type', 'general')
        
        print(f"      🏛️  {institution_name} ({institution_type}) - {output_type} format - iteration {iteration}/{total_iterations}")
        start_time = time.time()
        success = False
        error_message = None
        processed_data = None
        try:
            # Enable benchmarking context for proper cost tracking
            from benchmarking.integration import get_benchmarking_manager, benchmark_context, BenchmarkCategory
              # Get benchmarking manager
            benchmarking_manager = get_benchmarking_manager()
            
            if benchmarking_manager:                # Use benchmarking context for proper cost tracking
                with benchmark_context(
                    category=BenchmarkCategory.PIPELINE,
                    institution_name=institution_name,
                    institution_type=institution_type or "unknown"                ):
                    processed_data = process_institution_pipeline(
                        institution_name=institution_name,
                        institution_type=institution_type,
                        search_params=None,
                        output_type=output_type
                    )
            else:
                # Fallback without benchmarking context
                print(f"⚠️ Warning: Benchmarking manager not available, cost tracking will be limited")
                processed_data = process_institution_pipeline(
                    institution_name=institution_name,
                    institution_type=institution_type,
                    search_params=None,
                    output_type=output_type
                )
            
            if processed_data and not processed_data.get('error'):
                success = True
            else:
                error_message = processed_data.get('error', 'Unknown processing error') if processed_data else 'No data returned'
                
        except Exception as e:
            error_message = str(e)
            success = False
        
        execution_time = time.time() - start_time
          # Calculate comprehensive metrics using quality score integration
        if success and processed_data:
            try:
                quality_metrics = quality_integrator.get_output_type_metrics(processed_data, output_type)
            except AttributeError as e:
                print(f"⚠️ Quality integration error: {e}")
                # Fallback to basic quality metrics
                quality_metrics = {'core_quality_score': processed_data.get('quality_score', 0), 'output_type': output_type}
            cost_metrics = self._extract_cost_metrics(processed_data)
            performance_metrics = self._extract_performance_metrics(processed_data)
        else:
            try:
                quality_metrics = quality_integrator.calculate_enhanced_quality_metrics({})
            except AttributeError:
                quality_metrics = {'core_quality_score': 0, 'output_type': output_type}
            cost_metrics = {'total_cost': 0.0, 'api_calls': 0}
            performance_metrics = {
                'cache_hit_rate': 0.0,
                'network_requests': 0,
                'processing_phases_completed': 0
            }
          # Create comprehensive test result
        result = ComprehensiveTestResult(
            institution_name=institution_name,
            institution_type=institution_type,
            output_type=output_type,
            success=success,
            execution_time=execution_time,
            cost_usd=cost_metrics.get('total_cost', 0.0),
            
            # Core quality metrics
            core_quality_score=quality_metrics.get('core_quality_score', 0),
            core_quality_rating=quality_metrics.get('core_quality_rating', 'Unknown'),
            completeness_score=quality_metrics.get('completeness_score', 0.0),
            fields_extracted=quality_metrics.get('fields_extracted', 0),
            fields_requested=quality_metrics.get('fields_requested', 97),
            
            # Enhanced quality metrics
            critical_fields_completion=quality_metrics.get('critical_fields_completion', 0.0),
            important_fields_completion=quality_metrics.get('important_fields_completion', 0.0),
            specialized_fields_completion=quality_metrics.get('specialized_fields_completion', 0.0),
            content_quality_score=quality_metrics.get('content_quality_score', 0.0),
            relevance_score=quality_metrics.get('relevance_score', 0.0),
            
            # Pipeline success metrics
            search_success=quality_metrics.get('search_success', False),
            crawling_success=quality_metrics.get('crawling_success', False),
            extraction_success=quality_metrics.get('extraction_success', False),
            overall_pipeline_success=quality_metrics.get('overall_pipeline_success', False),
            
            # Output type specific metrics
            data_size_bytes=quality_metrics.get('data_size_estimate', 0),
            serialization_complexity=quality_metrics.get('serialization_complexity', 0.0),
            information_density=quality_metrics.get('information_density', 0.0),
            
            # Performance metrics
            cache_hit_rate=performance_metrics.get('cache_hit_rate', 0.0),
            network_requests=performance_metrics.get('network_requests', 0),
            processing_phases_completed=performance_metrics.get('processing_phases_completed', 0),
            total_pipeline_time=performance_metrics.get('total_pipeline_time', 0.0),
            search_time=performance_metrics.get('search_time', 0.0),
            crawling_time=performance_metrics.get('crawling_time', 0.0),
            extraction_time=performance_metrics.get('extraction_time', 0.0),
            
            # Crawling metrics
            success_rate=performance_metrics.get('success_rate', 0.0),
            total_urls_requested=performance_metrics.get('total_urls_requested', 0),
            successful_crawls=performance_metrics.get('successful_crawls', 0),
            failed_crawls=performance_metrics.get('failed_crawls', 0),
            content_size_mb=performance_metrics.get('content_size_mb', 0.0),
            compression_ratio=performance_metrics.get('compression_ratio', 0.0),
            
            # Cost breakdown
            google_search_cost=cost_metrics.get('google_search_cost', 0.0),
            llm_cost=cost_metrics.get('llm_cost', 0.0),
            infrastructure_cost=cost_metrics.get('infrastructure_cost', 0.0),
            google_search_queries=cost_metrics.get('google_search_queries', 0),
            llm_model_used=cost_metrics.get('llm_model_used', 'unknown'),
            input_tokens=cost_metrics.get('input_tokens', 0),
            output_tokens=cost_metrics.get('output_tokens', 0),
            total_tokens=cost_metrics.get('total_tokens', 0),
            
            # Error information
            error_message=error_message or ""        )
        
        # Add result to collection and update live table
        self._add_result_and_update_table(result)
        
        # Print any error details
        if not success and error_message:
            print(f"         ⚠️  Error: {error_message}")
    
    def _extract_cost_metrics(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive cost metrics from processed data."""
        cost_metrics = processed_data.get('cost_metrics', {})
        extraction_metrics = processed_data.get('extraction_metrics', {})
        
        return {
            'total_cost': cost_metrics.get('total_cost_usd', 0.0),
            'google_search_cost': cost_metrics.get('google_search_cost_usd', 0.0),
            'llm_cost': cost_metrics.get('llm_cost_usd', 0.0),
            'infrastructure_cost': cost_metrics.get('infrastructure_cost_usd', 0.0),
            'google_search_queries': cost_metrics.get('google_search_queries', 0),
            'llm_model_used': cost_metrics.get('llm_model_used', extraction_metrics.get('model_used', 'unknown')),
            'input_tokens': cost_metrics.get('input_tokens', extraction_metrics.get('input_tokens', 0)),
            'output_tokens': cost_metrics.get('output_tokens', extraction_metrics.get('output_tokens', 0)),
            'total_tokens': cost_metrics.get('total_tokens', extraction_metrics.get('total_tokens', 0))
        }
    def _extract_performance_metrics(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive performance metrics from processed data."""
        crawl_summary = processed_data.get('crawl_summary', {})
        processing_phases = processed_data.get('processing_phases', {})
        performance_metrics = processed_data.get('performance_metrics', {})
        latency_metrics = processed_data.get('latency_metrics', {})
        efficiency_metrics = processed_data.get('efficiency_metrics', {})
        
        # Count completed phases
        completed_phases = sum(1 for phase in processing_phases.values() if phase.get('success', False))
        
        return {
            'cache_hit_rate': crawl_summary.get('cache_hit_rate', efficiency_metrics.get('cache_hit_rate', 0.0)),
            'network_requests': latency_metrics.get('network_requests', 0),
            'processing_phases_completed': completed_phases,
            'total_pipeline_time': performance_metrics.get('total_pipeline_time', latency_metrics.get('total_pipeline_time_seconds', 0.0)),
            'search_time': processing_phases.get('search', {}).get('time', latency_metrics.get('search_time_seconds', 0.0)),
            'crawling_time': processing_phases.get('crawling', {}).get('time', latency_metrics.get('crawling_time_seconds', 0.0)),
            'extraction_time': processing_phases.get('extraction', {}).get('time', latency_metrics.get('llm_processing_time_seconds', 0.0)),
            'success_rate': crawl_summary.get('success_rate', 0.0),
            'total_urls_requested': crawl_summary.get('total_urls_requested', 0),
            'successful_crawls': crawl_summary.get('successful_crawls', 0),
            'failed_crawls': crawl_summary.get('failed_crawls', 0),
            'content_size_mb': crawl_summary.get('total_content_size_mb', 0.0),
            'compression_ratio': crawl_summary.get('compression_ratio', 0.0),
            'overall_success': performance_metrics.get('overall_success', False)
        }
    
    def _generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive analysis of all test results."""
        if not self.results:
            return {'error': 'No test results available for analysis'}
        
        # Convert results to DataFrame for easier analysis
        df = pd.DataFrame([asdict(r) for r in self.results])
        
        # Overall statistics
        overall_stats = {
            'total_tests': len(self.results),
            'success_rate': df['success'].mean(),
            'avg_execution_time': df['execution_time'].mean(),
            'avg_cost': df['cost_usd'].mean(),
            'avg_quality_score': df['core_quality_score'].mean(),
            'avg_completeness': df['completeness_score'].mean()
        }
        
        # Institution type analysis
        institution_type_analysis = {}
        for inst_type in df['institution_type'].unique():
            type_df = df[df['institution_type'] == inst_type]
            institution_type_analysis[inst_type] = {
                'count': len(type_df),
                'success_rate': type_df['success'].mean(),
                'avg_quality_score': type_df['core_quality_score'].mean(),
                'avg_execution_time': type_df['execution_time'].mean(),
                'avg_cost': type_df['cost_usd'].mean(),
                'avg_completeness': type_df['completeness_score'].mean(),
                'critical_fields_completion': type_df['critical_fields_completion'].mean(),
                'important_fields_completion': type_df['important_fields_completion'].mean()
            }
        
        # Output type analysis
        output_type_analysis = {}
        for output_type in df['output_type'].unique():
            output_df = df[df['output_type'] == output_type]
            output_type_analysis[output_type] = {
                'count': len(output_df),
                'success_rate': output_df['success'].mean(),
                'avg_data_size': output_df['data_size_bytes'].mean(),
                'avg_complexity': output_df['serialization_complexity'].mean(),
                'avg_information_density': output_df['information_density'].mean(),
                'avg_execution_time': output_df['execution_time'].mean()
            }
        
        # Quality score distribution
        quality_distribution = {
            'excellent_90_plus': (df['core_quality_score'] >= 90).sum(),
            'good_70_to_89': ((df['core_quality_score'] >= 70) & (df['core_quality_score'] < 90)).sum(),
            'fair_50_to_69': ((df['core_quality_score'] >= 50) & (df['core_quality_score'] < 70)).sum(),
            'poor_below_50': (df['core_quality_score'] < 50).sum()
        }
        
        # Field completion analysis
        field_completion_analysis = {
            'avg_critical_completion': df['critical_fields_completion'].mean(),
            'avg_important_completion': df['important_fields_completion'].mean(),
            'avg_specialized_completion': df['specialized_fields_completion'].mean(),
            'avg_fields_extracted': df['fields_extracted'].mean(),
            'max_fields_extracted': df['fields_extracted'].max(),
            'min_fields_extracted': df['fields_extracted'].min()
        }
        
        # Performance analysis
        performance_analysis = {
            'avg_cache_hit_rate': df['cache_hit_rate'].mean(),
            'avg_network_requests': df['network_requests'].mean(),
            'avg_processing_phases_completed': df['processing_phases_completed'].mean(),
            'pipeline_success_rate': df['overall_pipeline_success'].mean()
        }
        
        # Top and bottom performers
        successful_results = df[df['success'] == True]
        if len(successful_results) > 0:
            top_performers = successful_results.nlargest(5, 'core_quality_score')[
                ['institution_name', 'institution_type', 'core_quality_score', 'execution_time']
            ].to_dict('records')
            
            bottom_performers = successful_results.nsmallest(5, 'core_quality_score')[
                ['institution_name', 'institution_type', 'core_quality_score', 'execution_time']
            ].to_dict('records')
        else:
            top_performers = []
            bottom_performers = []
        
        return {
            'overall_statistics': overall_stats,
            'institution_type_analysis': institution_type_analysis,
            'output_type_analysis': output_type_analysis,
            'quality_distribution': quality_distribution,
            'field_completion_analysis': field_completion_analysis,            'performance_analysis': performance_analysis,
            'top_performers': top_performers,
            'bottom_performers': bottom_performers,
            'total_cost': df['cost_usd'].sum(),
            'total_execution_time': df['execution_time'].sum()
        }
    
    def _generate_output_files(self, config: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Generate various output files with test results and analysis."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(self.base_dir, 'project_cache', 'benchmark_results')
        os.makedirs(output_dir, exist_ok=True)
        
        output_files = []
        
        # 1. JSON results file
        json_file = os.path.join(output_dir, f'comprehensive_benchmark_results_{timestamp}.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            # Sanitize data before JSON serialization
            sanitized_data = self._sanitize_for_json({
                'test_config': config,
                'analysis': analysis,
                'results': [r.to_dict() for r in self.results]
            })
            json.dump(sanitized_data, f, indent=2, ensure_ascii=False, cls=NumpyJSONEncoder)
        output_files.append(json_file)
        
        # 2. CSV results file (detailed)
        csv_file = os.path.join(output_dir, f'comprehensive_benchmark_results_{timestamp}.csv')
        df = pd.DataFrame([asdict(r) for r in self.results])
        df.to_csv(csv_file, index=False)
        output_files.append(csv_file)
        
        # 3. Enhanced HTML analysis report with detailed tables
        html_file = os.path.join(output_dir, f'comprehensive_benchmark_analysis_{timestamp}.html')
        self._generate_html_report(analysis, html_file)
        output_files.append(html_file)
        
        # 4. Markdown detailed report
        markdown_file = os.path.join(output_dir, f'comprehensive_benchmark_report_{timestamp}.md')
        self._generate_markdown_report(analysis, markdown_file)
        output_files.append(markdown_file)
        
        # 5. Formatted text summary table
        text_file = os.path.join(output_dir, f'benchmark_summary_table_{timestamp}.txt')
        self._generate_text_summary_table(text_file)
        output_files.append(text_file)
        # 6. Summary analysis JSON
        summary_file = os.path.join(output_dir, f'benchmark_summary_{timestamp}.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            sanitized_analysis = self._sanitize_for_json(analysis)
            json.dump(sanitized_analysis, f, indent=2, ensure_ascii=False, cls=NumpyJSONEncoder)
        output_files.append(summary_file)
        
        return output_files
    
    def _generate_html_report(self, analysis: Dict[str, Any], output_file: str):
        """Generate a comprehensive HTML analysis report."""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Institution Benchmark Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .section {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #007bff; }}
        .metric {{ display: inline-block; margin: 10px 15px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .metric-label {{ font-size: 0.9em; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .error {{ color: #dc3545; }}
        .chart-placeholder {{ background: #e9ecef; padding: 40px; text-align: center; color: #6c757d; border-radius: 4px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Comprehensive Institution Benchmark Analysis</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>📊 Overall Statistics</h2>
        <div class="metric">
            <div class="metric-value">{analysis['overall_statistics']['total_tests']}</div>
            <div class="metric-label">Total Tests</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis['overall_statistics']['success_rate']:.1%}</div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis['overall_statistics']['avg_quality_score']:.1f}</div>
            <div class="metric-label">Avg Quality Score</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis['overall_statistics']['avg_execution_time']:.2f}s</div>
            <div class="metric-label">Avg Execution Time</div>
        </div>
        <div class="metric">
            <div class="metric-value">${analysis['overall_statistics']['avg_cost']:.4f}</div>
            <div class="metric-label">Avg Cost</div>
        </div>
    </div>
    
    <div class="section">
        <h2>🏛️ Institution Type Analysis</h2>
        <table>
            <tr>
                <th>Institution Type</th>
                <th>Count</th>
                <th>Success Rate</th>
                <th>Avg Quality Score</th>
                <th>Avg Execution Time</th>
                <th>Avg Cost</th>
                <th>Critical Fields</th>
                <th>Important Fields</th>
            </tr>
"""
        
        for inst_type, data in analysis['institution_type_analysis'].items():
            html_content += f"""
            <tr>
                <td>{inst_type.title()}</td>
                <td>{data['count']}</td>
                <td class="{'success' if data['success_rate'] > 0.8 else 'warning' if data['success_rate'] > 0.5 else 'error'}">{data['success_rate']:.1%}</td>
                <td>{data['avg_quality_score']:.1f}</td>
                <td>{data['avg_execution_time']:.2f}</td>
                <td>${data['avg_cost']:.4f}</td>
                <td>{data['critical_fields_completion']:.1%}</td>
                <td>{data['important_fields_completion']:.1%}</td>
            </tr>
"""
        
        html_content += f"""
        </table>
    </div>
    
    <div class="section">
        <h2>📄 Output Type Analysis</h2>
        <table>
            <tr>
                <th>Output Type</th>
                <th>Count</th>
                <th>Success Rate</th>
                <th>Avg Data Size</th>
                <th>Complexity</th>
                <th>Information Density</th>
                <th>Avg Execution Time</th>
            </tr>
"""
        
        for output_type, data in analysis['output_type_analysis'].items():
            html_content += f"""
            <tr>
                <td>{output_type.upper()}</td>
                <td>{data['count']}</td>
                <td class="{'success' if data['success_rate'] > 0.8 else 'warning' if data['success_rate'] > 0.5 else 'error'}">{data['success_rate']:.1%}</td>
                <td>{data['avg_data_size']:.0f} bytes</td>
                <td>{data['avg_complexity']:.2f}</td>
                <td>{data['avg_information_density']:.2f}</td>
                <td>{data['avg_execution_time']:.2f}</td>
            </tr>
"""
        
        html_content += f"""
        </table>
    </div>
    
    <div class="section">
        <h2>🎯 Quality Score Distribution</h2>
        <table>
            <tr>
                <th>Quality Range</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
            <tr>
                <td class="success">Excellent (90+)</td>
                <td>{analysis['quality_distribution']['excellent_90_plus']}</td>
                <td>{(analysis['quality_distribution']['excellent_90_plus'] / analysis['overall_statistics']['total_tests'] * 100):.1f}%</td>
            </tr>
            <tr>
                <td class="success">Good (70-89)</td>
                <td>{analysis['quality_distribution']['good_70_to_89']}</td>
                <td>{(analysis['quality_distribution']['good_70_to_89'] / analysis['overall_statistics']['total_tests'] * 100):.1f}%</td>
            </tr>
            <tr>
                <td class="warning">Fair (50-69)</td>
                <td>{analysis['quality_distribution']['fair_50_to_69']}</td>
                <td>{(analysis['quality_distribution']['fair_50_to_69'] / analysis['overall_statistics']['total_tests'] * 100):.1f}%</td>
            </tr>
            <tr>
                <td class="error">Poor (<50)</td>
                <td>{analysis['quality_distribution']['poor_below_50']}</td>
                <td>{(analysis['quality_distribution']['poor_below_50'] / analysis['overall_statistics']['total_tests'] * 100):.1f}%</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>📋 Field Completion Analysis</h2>
        <div class="metric">
            <div class="metric-value">{analysis['field_completion_analysis']['avg_critical_completion']:.1%}</div>
            <div class="metric-label">Critical Fields</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis['field_completion_analysis']['avg_important_completion']:.1%}</div>
            <div class="metric-label">Important Fields</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis['field_completion_analysis']['avg_specialized_completion']:.1%}</div>
            <div class="metric-label">Specialized Fields</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis['field_completion_analysis']['avg_fields_extracted']:.0f}</div>
            <div class="metric-label">Avg Fields Extracted</div>
        </div>
    </div>
    
    <div class="section">
        <h2>🚀 Performance Analysis</h2>
        <div class="metric">
            <div class="metric-value">{analysis['performance_analysis']['avg_cache_hit_rate']:.1%}</div>
            <div class="metric-label">Cache Hit Rate</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis['performance_analysis']['avg_network_requests']:.0f}</div>
            <div class="metric-label">Network Requests</div>
        </div>
        <div class="metric">
            <div class="metric-value">{analysis['performance_analysis']['pipeline_success_rate']:.1%}</div>
            <div class="metric-label">Pipeline Success</div>
        </div>
    </div>
    
    <div class="section">
        <h2>🏆 Top Performers</h2>
        <table>
            <tr>
                <th>Institution</th>
                <th>Type</th>
                <th>Quality Score</th>
                <th>Execution Time (s)</th>
            </tr>
"""
        
        for performer in analysis['top_performers']:
            html_content += f"""
            <tr>                <td>{performer['institution_name']}</td>
                <td>{performer['institution_type']}</td>
                <td class="success">{performer['core_quality_score']:.1f}</td>
                <td>{performer['execution_time']:.2f}</td>
            </tr>
"""
        
        html_content += f"""
        </table>
    </div>
    
    <div class="section">
        <h2>💰 Cost Summary</h2>
        <p><strong>Total Cost:</strong> ${analysis['total_cost']:.4f}</p>
        <p><strong>Total Execution Time:</strong> {analysis['total_execution_time']:.2f} seconds</p>
        <p><strong>Cost per Test:</strong> ${(analysis['total_cost'] / analysis['overall_statistics']['total_tests']):.4f}</p>
        <p><strong>Time per Test:</strong> {(analysis['total_execution_time'] / analysis['overall_statistics']['total_tests']):.2f} seconds</p>
    </div>
"""

        # Add detailed results table if we have results
        if self.results:
            df = pd.DataFrame([asdict(r) for r in self.results])
            html_content += """
    <div class="section">
        <h2>📊 Detailed Results by Institution Type</h2>
"""
            
            for inst_type in df['institution_type'].unique():
                type_df = df[df['institution_type'] == inst_type]
                html_content += f"""
        <h3>{inst_type.title()} Institutions ({len(type_df)} tests)</h3>
        <table>
            <tr>
                <th>Institution</th>
                <th>Format</th>
                <th>Quality</th>
                <th>Rating</th>
                <th>Time (s)</th>
                <th>Cost ($)</th>
                <th>Fields</th>
                <th>Tokens</th>
                <th>Model</th>
                <th>Status</th>
            </tr>
"""
                
                for _, result in type_df.sort_values('core_quality_score', ascending=False).iterrows():
                    status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                    status_class = "success" if result['success'] else "error"
                    quality_class = "success" if result['core_quality_score'] >= 70 else "warning" if result['core_quality_score'] >= 50 else "error"
                    
                    html_content += f"""
            <tr>
                <td>{result['institution_name']}</td>
                <td>{result['output_type']}</td>
                <td class="{quality_class}">{result['core_quality_score']:.1f}</td>
                <td>{result['core_quality_rating']}</td>
                <td>{result['execution_time']:.1f}</td>
                <td>${result['cost_usd']:.4f}</td>
                <td>{result['fields_extracted']}</td>
                <td>{result['total_tokens']}</td>
                <td>{result['llm_model_used']}</td>
                <td class="{status_class}">{status}</td>
            </tr>
"""
                
                # Type summary
                html_content += f"""
        </table>
        <p><strong>{inst_type.title()} Summary:</strong> Avg Quality: {type_df['core_quality_score'].mean():.1f} | Avg Cost: ${type_df['cost_usd'].mean():.4f} | Success Rate: {type_df['success'].mean()*100:.1f}%</p>
"""
            
            html_content += """
    </div>
"""

        html_content += """
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_markdown_report(self, analysis: Dict[str, Any], output_file: str):
        """Generate a comprehensive Markdown analysis report with detailed tables."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        markdown_content = f"""# 🏛️ Comprehensive Institution Benchmark Analysis

**Generated on:** {timestamp}

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| Total Tests | {analysis['overall_statistics']['total_tests']} |
| Success Rate | {analysis['overall_statistics']['success_rate']:.1%} |
| Average Quality Score | {analysis['overall_statistics']['avg_quality_score']:.1f} |
| Average Execution Time | {analysis['overall_statistics']['avg_execution_time']:.2f}s |
| Average Cost | ${analysis['overall_statistics']['avg_cost']:.4f} |
| Total Cost | ${analysis['total_cost']:.4f} |
| Total Execution Time | {analysis['total_execution_time']:.2f}s |

## 🏛️ Institution Type Performance Analysis

| Institution Type | Count | Success Rate | Avg Quality | Avg Time (s) | Avg Cost ($) | Critical Fields | Important Fields |
|------------------|-------|--------------|-------------|--------------|---------------|----------------|------------------|
"""

        for inst_type, data in analysis['institution_type_analysis'].items():
            markdown_content += f"| {inst_type.title()} | {data['count']} | {data['success_rate']:.1%} | {data['avg_quality_score']:.1f} | {data['avg_execution_time']:.2f} | ${data['avg_cost']:.4f} | {data['critical_fields_completion']:.1%} | {data['important_fields_completion']:.1%} |\n"

        markdown_content += f"""
## 📄 Output Format Performance Analysis

| Output Type | Count | Success Rate | Avg Data Size | Complexity | Information Density | Avg Time (s) |
|-------------|-------|--------------|---------------|------------|-------------------|--------------|
"""

        for output_type, data in analysis['output_type_analysis'].items():
            markdown_content += f"| {output_type.upper()} | {data['count']} | {data['success_rate']:.1%} | {data['avg_data_size']:.0f} bytes | {data['avg_complexity']:.2f} | {data['avg_information_density']:.2f} | {data['avg_execution_time']:.2f} |\n"

        markdown_content += f"""
## 🎯 Quality Score Distribution

| Quality Range | Count | Percentage |
|---------------|-------|------------|
| Excellent (90+) | {analysis['quality_distribution']['excellent_90_plus']} | {(analysis['quality_distribution']['excellent_90_plus'] / analysis['overall_statistics']['total_tests'] * 100):.1f}% |
| Good (70-89) | {analysis['quality_distribution']['good_70_to_89']} | {(analysis['quality_distribution']['good_70_to_89'] / analysis['overall_statistics']['total_tests'] * 100):.1f}% |
| Fair (50-69) | {analysis['quality_distribution']['fair_50_to_69']} | {(analysis['quality_distribution']['fair_50_to_69'] / analysis['overall_statistics']['total_tests'] * 100):.1f}% |
| Poor (<50) | {analysis['quality_distribution']['poor_below_50']} | {(analysis['quality_distribution']['poor_below_50'] / analysis['overall_statistics']['total_tests'] * 100):.1f}% |

## 📋 Field Completion Analysis

| Field Category | Completion Rate |
|----------------|-----------------|
| Critical Fields | {analysis['field_completion_analysis']['avg_critical_completion']:.1%} |
| Important Fields | {analysis['field_completion_analysis']['avg_important_completion']:.1%} |
| Specialized Fields | {analysis['field_completion_analysis']['avg_specialized_completion']:.1%} |

**Field Extraction Statistics:**
- Average Fields Extracted: {analysis['field_completion_analysis']['avg_fields_extracted']:.0f}
- Maximum Fields Extracted: {analysis['field_completion_analysis']['max_fields_extracted']}
- Minimum Fields Extracted: {analysis['field_completion_analysis']['min_fields_extracted']}

## 🚀 Performance Metrics

| Metric | Value |
|--------|-------|
| Average Cache Hit Rate | {analysis['performance_analysis']['avg_cache_hit_rate']:.1%} |
| Average Network Requests | {analysis['performance_analysis']['avg_network_requests']:.0f} |
| Pipeline Success Rate | {analysis['performance_analysis']['pipeline_success_rate']:.1%} |
| Average Processing Phases Completed | {analysis['performance_analysis']['avg_processing_phases_completed']:.1f} |

## 🏆 Top Performers

| Rank | Institution | Type | Quality Score | Execution Time (s) |
|------|-------------|------|---------------|--------------------|
"""

        for i, performer in enumerate(analysis['top_performers'], 1):
            markdown_content += f"| {i} | {performer['institution_name']} | {performer['institution_type']} | {performer['core_quality_score']:.1f} | {performer['execution_time']:.2f} |\n"

        # Add detailed results table
        if self.results:
            df = pd.DataFrame([asdict(r) for r in self.results])
            markdown_content += f"""
## 📊 Detailed Results by Institution Type

"""
            for inst_type in df['institution_type'].unique():
                type_df = df[df['institution_type'] == inst_type]
                markdown_content += f"""
### {inst_type.title()} Institutions

| Institution | Format | Quality | Rating | Time (s) | Cost ($) | Fields | Tokens | Model | Status |
|-------------|--------|---------|--------|----------|----------|--------|--------|-------|--------|
"""
                for _, result in type_df.sort_values('core_quality_score', ascending=False).iterrows():
                    status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                    markdown_content += f"| {result['institution_name']} | {result['output_type']} | {result['core_quality_score']:.1f} | {result['core_quality_rating']} | {result['execution_time']:.1f} | ${result['cost_usd']:.4f} | {result['fields_extracted']} | {result['total_tokens']} | {result['llm_model_used']} | {status} |\n"
                
                # Type summary
                markdown_content += f"""
**{inst_type.title()} Summary:** Avg Quality: {type_df['core_quality_score'].mean():.1f} | Avg Cost: ${type_df['cost_usd'].mean():.4f} | Success Rate: {type_df['success'].mean()*100:.1f}%

"""

        markdown_content += f"""
## 💰 Cost Analysis

- **Total Cost:** ${analysis['total_cost']:.4f}
- **Cost per Test:** ${(analysis['total_cost'] / analysis['overall_statistics']['total_tests']):.4f}
- **Time per Test:** {(analysis['total_execution_time'] / analysis['overall_statistics']['total_tests']):.2f} seconds

## 📈 Recommendations

Based on the benchmark results:

1. **Performance Optimization:** Focus on improving cache hit rates and reducing network requests
2. **Quality Improvement:** Target institutions with low quality scores for enhanced data extraction
3. **Cost Efficiency:** Consider output format optimization for better cost-performance ratios
4. **Field Completion:** Enhance extraction logic for critical and important fields

---
*Report generated by Comprehensive Institution Benchmark Suite*
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    def _generate_text_summary_table(self, output_file: str):
        """Generate a formatted text table summarizing all benchmark results."""
        if not self.results:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("No benchmark results available.\n")
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df = pd.DataFrame([asdict(r) for r in self.results])
        
        content = f"""COMPREHENSIVE INSTITUTION BENCHMARK RESULTS
Generated: {timestamp}
{'='*140}

EXECUTIVE SUMMARY
{'-'*50}
Total Tests Run: {len(df)}
Successful Tests: {df['success'].sum()} ({df['success'].mean()*100:.1f}%)
Average Quality Score: {df['core_quality_score'].mean():.1f}
Total Cost: ${df['cost_usd'].sum():.4f}
Average Execution Time: {df['execution_time'].mean():.1f} seconds

"""

        # Results by institution type
        for inst_type in df['institution_type'].unique():
            type_df = df[df['institution_type'] == inst_type]
            content += f"""
{inst_type.upper()} INSTITUTIONS ({len(type_df)} tests)
{'-'*140}
{'Institution':<30} {'Format':<12} {'Quality':<8} {'Rating':<15} {'Time(s)':<8} {'Cost($)':<12} {'Fields':<8} {'Tokens':<8} {'Model':<15} {'Status':<10}
{'-'*140}
"""
            
            for _, result in type_df.sort_values('core_quality_score', ascending=False).iterrows():
                status = "SUCCESS" if result['success'] else "FAILED"
                line = f"{result['institution_name'][:29]:<30} {result['output_type']:<12} {result['core_quality_score']:<8.1f} {result['core_quality_rating'][:14]:<15} {result['execution_time']:<8.1f} ${result['cost_usd']:<11.4f} {result['fields_extracted']:<8} {result['total_tokens']:<8} {result['llm_model_used'][:14]:<15} {status:<10}"
                content += line + "\n"
            
            # Type summary
            content += f"""
Summary: Avg Quality: {type_df['core_quality_score'].mean():.1f} | Avg Cost: ${type_df['cost_usd'].mean():.4f} | Success Rate: {type_df['success'].mean()*100:.1f}%
"""

        # Overall analysis
        content += f"""
{'='*140}
OVERALL ANALYSIS
{'='*140}

TOP 5 PERFORMERS BY QUALITY:
{'-'*50}
"""
        
        top_5 = df.nlargest(5, 'core_quality_score')
        for i, (_, result) in enumerate(top_5.iterrows(), 1):
            content += f"{i}. {result['institution_name']} ({result['institution_type']}) - Quality: {result['core_quality_score']:.1f}\n"

        content += f"""
MOST COST EFFICIENT (Successful tests only):
{'-'*50}
"""
        
        cost_efficient = df[df['success'] == True].nsmallest(5, 'cost_usd')
        for i, (_, result) in enumerate(cost_efficient.iterrows(), 1):
            content += f"{i}. {result['institution_name']} - Cost: ${result['cost_usd']:.4f} (Quality: {result['core_quality_score']:.1f})\n"

        content += f"""
OUTPUT FORMAT ANALYSIS:
{'-'*50}
"""
        
        for output_type in df['output_type'].unique():
            output_df = df[df['output_type'] == output_type]
            content += f"{output_type.upper()}: {len(output_df)} tests, {output_df['success'].mean()*100:.1f}% success, avg quality: {output_df['core_quality_score'].mean():.1f}\n"

        content += f"""
QUALITY DISTRIBUTION:
{'-'*50}
Excellent (90+): {(df['core_quality_score'] >= 90).sum()} tests ({(df['core_quality_score'] >= 90).sum()/len(df)*100:.1f}%)
Good (70-89): {((df['core_quality_score'] >= 70) & (df['core_quality_score'] < 90)).sum()} tests ({((df['core_quality_score'] >= 70) & (df['core_quality_score'] < 90)).sum()/len(df)*100:.1f}%)
Fair (50-69): {((df['core_quality_score'] >= 50) & (df['core_quality_score'] < 70)).sum()} tests ({((df['core_quality_score'] >= 50) & (df['core_quality_score'] < 70)).sum()/len(df)*100:.1f}%)
Poor (<50): {(df['core_quality_score'] < 50).sum()} tests ({(df['core_quality_score'] < 50).sum()/len(df)*100:.1f}%)

{'='*140}
End of Report
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _sanitize_for_json(self, obj):
        """Convert numpy/pandas types to JSON-serializable Python types."""
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        else:
            return obj


# CLI interface for easy execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive institution benchmarking tests')
    parser.add_argument('config_file', help='Path to test configuration JSON file')
    parser.add_argument('--base-dir', default='.', help='Base directory for the project')
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner(args.base_dir)
    results = runner.run_comprehensive_test_suite(args.config_file)
    
    print(f"\n🎉 Test suite completed successfully!")
    print(f"📊 Results summary: {results['summary']}")
