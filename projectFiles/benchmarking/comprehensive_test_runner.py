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

# Add project directory to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from benchmarking.quality_score_integration import QualityScoreIntegrator
from benchmarking.benchmark_config import BenchmarkCategory
from benchmarking.integration import get_benchmarking_manager
from institution_processor import process_institution_pipeline

# Create fresh quality integrator instance
quality_integrator = QualityScoreIntegrator()


@dataclass
class ComprehensiveTestResult:
    """Enhanced test result with quality score integration."""
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
        self.benchmarking_manager = get_benchmarking_manager()
        self.results: List[ComprehensiveTestResult] = []
        
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
            self._run_test_configuration(test_config)
        
        # Generate comprehensive analysis
        total_time = time.time() - start_time
        analysis = self._generate_comprehensive_analysis()
        
        # Generate output files
        output_files = self._generate_output_files(config, analysis)
        
        print(f"\n✅ Test Suite Completed in {total_time:.2f} seconds")
        print(f"📊 Total Tests: {len(self.results)}")
        print(f"✅ Successful: {sum(1 for r in self.results if r.success)}")
        print(f"❌ Failed: {sum(1 for r in self.results if not r.success)}")
        print(f"📁 Output Files: {', '.join(output_files)}")
        
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
                        test_config.get('category', 'pipeline'),
                        iteration + 1,
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
            
            if benchmarking_manager:
                # Use benchmarking context for proper cost tracking
                with benchmark_context(
                    institution_name=institution_name,
                    institution_type=institution_type or "unknown",
                    category=BenchmarkCategory.COMPREHENSIVE_TEST,
                    test_iteration=iteration
                ):
                    processed_data = process_institution_pipeline(
                        institution_name=institution_name,
                        institution_type=institution_type,
                        search_params=None
                    )
            else:
                # Fallback without benchmarking context
                print(f"⚠️ Warning: Benchmarking manager not available, cost tracking will be limited")
                processed_data = process_institution_pipeline(
                    institution_name=institution_name,
                    institution_type=institution_type,
                    search_params=None
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
            quality_metrics = quality_integrator.get_output_type_metrics(processed_data, output_type)
            cost_metrics = self._extract_cost_metrics(processed_data)
            performance_metrics = self._extract_performance_metrics(processed_data)
        else:
            quality_metrics = quality_integrator.calculate_enhanced_quality_metrics({})
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
            core_quality_rating=quality_metrics.get('core_quality_rating', 'No Data'),
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
            
            # Error information
            error_message=error_message,
            validation_errors=quality_metrics.get('validation_errors', [])
        )
        
        self.results.append(result)
        
        # Print result summary
        status = "✅" if success else "❌"
        print(f"         {status} Quality: {result.core_quality_score:.1f} | Time: {execution_time:.2f}s | Cost: ${result.cost_usd:.4f}")
        
        if not success and error_message:
            print(f"         ⚠️  Error: {error_message}")
    
    def _extract_cost_metrics(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract cost metrics from processed data."""
        cost_metrics = processed_data.get('cost_metrics', {})
        return {
            'total_cost': cost_metrics.get('total_cost_usd', 0.0),
            'api_calls': cost_metrics.get('api_calls', 0),
            'input_tokens': cost_metrics.get('input_tokens', 0),
            'output_tokens': cost_metrics.get('output_tokens', 0)
        }
    
    def _extract_performance_metrics(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance metrics from processed data."""
        crawl_summary = processed_data.get('crawl_summary', {})
        processing_phases = processed_data.get('processing_phases', {})
        
        # Count completed phases
        completed_phases = sum(1 for phase in processing_phases.values() if phase.get('success', False))
        
        return {
            'cache_hit_rate': crawl_summary.get('cache_hit_rate', 0.0),
            'network_requests': crawl_summary.get('total_urls_requested', 0),
            'processing_phases_completed': completed_phases
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
            'field_completion_analysis': field_completion_analysis,
            'performance_analysis': performance_analysis,
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
            json.dump({
                'test_config': config,
                'analysis': analysis,
                'results': [r.to_dict() for r in self.results]
            }, f, indent=2, ensure_ascii=False)
        output_files.append(json_file)
        
        # 2. CSV results file
        csv_file = os.path.join(output_dir, f'comprehensive_benchmark_results_{timestamp}.csv')
        df = pd.DataFrame([asdict(r) for r in self.results])
        df.to_csv(csv_file, index=False)
        output_files.append(csv_file)
        
        # 3. HTML analysis report
        html_file = os.path.join(output_dir, f'comprehensive_benchmark_analysis_{timestamp}.html')
        self._generate_html_report(analysis, html_file)
        output_files.append(html_file)
        
        # 4. Summary analysis JSON
        summary_file = os.path.join(output_dir, f'benchmark_summary_{timestamp}.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
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
                <th>Avg Time (s)</th>
                <th>Avg Cost ($)</th>
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
                <th>Avg Time (s)</th>
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
            <tr>
                <td>{performer['institution_name']}</td>
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
    
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


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
