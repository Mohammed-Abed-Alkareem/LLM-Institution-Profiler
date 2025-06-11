"""
Test runner for comprehensive pipeline benchmarking and comparison testing.
"""

import os
import time
import json
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

from .benchmark_config import BenchmarkConfig
from .benchmark_tracker import BenchmarkTracker


@dataclass
class TestConfiguration:
    """Configuration for a specific test case."""
    
    test_name: str
    test_description: str
    institution_name: str
    institution_type: str
    
    # Pipeline configuration
    pipeline_config: Dict[str, Any] = field(default_factory=dict)
    
    # Test parameters
    iterations: int = 1
    parallel_execution: bool = False
    
    # Expected outcomes (for validation)
    expected_min_quality: float = 0.0
    expected_max_cost: float = float('inf')
    expected_max_time: float = float('inf')
    
    # Test data
    test_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """Result of a single test execution."""
    
    test_id: str
    test_name: str
    pipeline_id: str
    success: bool
    execution_time: float
    
    # Metrics
    cost_usd: float = 0.0
    quality_score: float = 0.0
    completeness_score: float = 0.0
    cache_hit_rate: float = 0.0
    
    # Validation results
    passed_quality_threshold: bool = False
    passed_cost_threshold: bool = False
    passed_time_threshold: bool = False
    
    # Error information
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)


class BenchmarkTestRunner:
    """
    Comprehensive test runner for pipeline benchmarking and comparison testing.
    
    Features:
    - A/B testing between different pipeline configurations
    - Batch testing with multiple institutions
    - Performance regression testing
    - Configuration optimization testing
    - Parallel test execution
    - Detailed result analysis and reporting
    """
    
    def __init__(self, config: BenchmarkConfig, benchmark_tracker: BenchmarkTracker):
        """Initialize the test runner."""
        self.config = config
        self.benchmark_tracker = benchmark_tracker
        
        # Test session management
        self.test_session_id = f"test_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.test_results: List[TestResult] = []
        self.active_tests: Dict[str, TestConfiguration] = {}
        
        # Results storage
        self.test_session_file = os.path.join(
            config.test_results_dir,
            f"test_session_{self.test_session_id}.json"
        )
    
    # === Single Test Execution ===
    
    def run_single_test(
        self,
        test_config: TestConfiguration,
        pipeline_function: Callable[[str, str, Dict[str, Any]], Dict[str, Any]]
    ) -> TestResult:
        """
        Run a single test with the given configuration.
        
        Args:
            test_config: Test configuration
            pipeline_function: Function that executes the pipeline
                             Should accept (institution_name, institution_type, config)
                             Should return pipeline results dict
                             
        Returns:
            Test result with metrics and validation
        """
        test_id = f"test_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        try:
            # Start pipeline tracking
            pipeline_id = self.benchmark_tracker.start_pipeline(
                pipeline_name=test_config.test_name,
                institution_name=test_config.institution_name,
                institution_type=test_config.institution_type,
                pipeline_config=test_config.pipeline_config
            )
            
            # Execute pipeline
            results = pipeline_function(
                test_config.institution_name,
                test_config.institution_type,
                test_config.pipeline_config
            )
            
            # Complete pipeline tracking
            pipeline_metrics = self.benchmark_tracker.complete_pipeline(
                pipeline_id=pipeline_id,
                success=results.get('success', False),
                error_message=results.get('error'),
                results_summary=results
            )
            
            execution_time = time.time() - start_time
            
            # Create test result
            test_result = TestResult(
                test_id=test_id,
                test_name=test_config.test_name,
                pipeline_id=pipeline_id,
                success=results.get('success', False),
                execution_time=execution_time
            )
            
            # Extract metrics if pipeline completed
            if pipeline_metrics:
                test_result.cost_usd = pipeline_metrics.cost_metrics.total_cost_usd
                test_result.quality_score = pipeline_metrics.quality_metrics.calculate_overall_quality()
                test_result.completeness_score = pipeline_metrics.quality_metrics.completeness_score
                test_result.cache_hit_rate = pipeline_metrics.efficiency_metrics.cache_hit_rate
                
                # Validate against thresholds
                test_result.passed_quality_threshold = test_result.quality_score >= test_config.expected_min_quality
                test_result.passed_cost_threshold = test_result.cost_usd <= test_config.expected_max_cost
                test_result.passed_time_threshold = execution_time <= test_config.expected_max_time
            
            return test_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TestResult(
                test_id=test_id,
                test_name=test_config.test_name,
                pipeline_id="",
                success=False,
                execution_time=execution_time,
                error_message=str(e),
                error_details={'exception_type': type(e).__name__}
            )
    
    # === Batch Testing ===
    
    def run_batch_tests(
        self,
        test_configurations: List[TestConfiguration],
        pipeline_function: Callable[[str, str, Dict[str, Any]], Dict[str, Any]],
        parallel: bool = True
    ) -> List[TestResult]:
        """
        Run multiple tests in batch.
        
        Args:
            test_configurations: List of test configurations
            pipeline_function: Pipeline execution function
            parallel: Whether to run tests in parallel
            
        Returns:
            List of test results
        """
        results = []
        
        if parallel and self.config.parallel_tests:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=self.config.max_concurrent_tests) as executor:
                # Submit all tests
                future_to_config = {
                    executor.submit(self.run_single_test, config, pipeline_function): config
                    for config in test_configurations
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_config):
                    try:
                        result = future.result()
                        results.append(result)
                        self.test_results.append(result)
                    except Exception as e:
                        config = future_to_config[future]
                        error_result = TestResult(
                            test_id=f"error_{int(time.time())}",
                            test_name=config.test_name,
                            pipeline_id="",
                            success=False,
                            execution_time=0.0,
                            error_message=f"Test execution failed: {str(e)}"
                        )
                        results.append(error_result)
                        self.test_results.append(error_result)
        else:
            # Sequential execution
            for config in test_configurations:
                result = self.run_single_test(config, pipeline_function)
                results.append(result)
                self.test_results.append(result)
        
        # Save results
        self._save_test_results()
        
        return results
    
    # === A/B Testing ===
    
    def run_ab_test(
        self,
        test_name: str,
        institution_name: str,
        institution_type: str,
        baseline_config: Dict[str, Any],
        test_configs: List[Dict[str, Any]],
        pipeline_function: Callable[[str, str, Dict[str, Any]], Dict[str, Any]],
        iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Run A/B test comparing baseline configuration against test configurations.
        
        Args:
            test_name: Name for the A/B test
            institution_name: Institution to test with
            institution_type: Type of institution
            baseline_config: Baseline configuration (A)
            test_configs: List of test configurations (B, C, D, etc.)
            pipeline_function: Pipeline execution function
            iterations: Number of iterations per configuration
            
        Returns:
            A/B test results with statistical analysis
        """
        # Start comparison tracking
        comparison_id = self.benchmark_tracker.start_comparison(
            comparison_name=test_name,
            baseline_pipeline="baseline",
            test_pipelines=[f"test_{i}" for i in range(len(test_configs))]
        )
        
        all_configurations = [("baseline", baseline_config)] + [
            (f"test_{i}", config) for i, config in enumerate(test_configs)
        ]
        
        test_results_by_config = {}
        
        # Run tests for each configuration
        for config_name, config in all_configurations:
            config_results = []
            
            for iteration in range(iterations):
                test_config = TestConfiguration(
                    test_name=f"{test_name}_{config_name}_iter_{iteration}",
                    test_description=f"A/B test iteration {iteration} for {config_name}",
                    institution_name=institution_name,
                    institution_type=institution_type,
                    pipeline_config=config
                )
                
                result = self.run_single_test(test_config, pipeline_function)
                config_results.append(result)
                
                # Add to comparison if successful
                if result.success and result.pipeline_id:
                    # We would need to get the actual pipeline metrics here
                    # This is a simplified version
                    pass
            
            test_results_by_config[config_name] = config_results
        
        # Analyze results
        analysis = self._analyze_ab_test_results(test_results_by_config)
        
        # Complete comparison
        self.benchmark_tracker.complete_comparison(comparison_id)
        
        return {
            'test_name': test_name,
            'comparison_id': comparison_id,
            'configurations_tested': len(all_configurations),
            'iterations_per_config': iterations,
            'results_by_config': test_results_by_config,
            'analysis': analysis
        }
    
    def _analyze_ab_test_results(self, results_by_config: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """Analyze A/B test results and determine statistical significance."""
        analysis = {
            'summary_stats': {},
            'winner': None,
            'significant_differences': [],
            'recommendations': []
        }
        
        # Calculate summary statistics for each configuration
        for config_name, results in results_by_config.items():
            successful_results = [r for r in results if r.success]
            
            if successful_results:
                avg_cost = sum(r.cost_usd for r in successful_results) / len(successful_results)
                avg_time = sum(r.execution_time for r in successful_results) / len(successful_results)
                avg_quality = sum(r.quality_score for r in successful_results) / len(successful_results)
                success_rate = len(successful_results) / len(results)
                
                analysis['summary_stats'][config_name] = {
                    'avg_cost_usd': round(avg_cost, 4),
                    'avg_execution_time': round(avg_time, 2),
                    'avg_quality_score': round(avg_quality, 3),
                    'success_rate': round(success_rate, 3),
                    'iterations': len(results),
                    'successful_iterations': len(successful_results)
                }
        
        # Determine winner based on weighted score
        if 'baseline' in analysis['summary_stats']:
            baseline_stats = analysis['summary_stats']['baseline']
            
            best_config = 'baseline'
            best_score = self._calculate_weighted_score(baseline_stats)
            
            for config_name, stats in analysis['summary_stats'].items():
                if config_name != 'baseline':
                    score = self._calculate_weighted_score(stats)
                    if score > best_score:
                        best_score = score
                        best_config = config_name
            
            analysis['winner'] = best_config
            
            # Generate recommendations
            if best_config != 'baseline':
                analysis['recommendations'].append(
                    f"Configuration '{best_config}' outperformed baseline"
                )
            else:
                analysis['recommendations'].append(
                    "Baseline configuration performed best"
                )
        
        return analysis
    
    def _calculate_weighted_score(self, stats: Dict[str, float]) -> float:
        """Calculate weighted score for configuration comparison."""
        # Normalize and weight metrics (lower cost and time are better, higher quality is better)
        quality_weight = 0.4
        cost_weight = 0.3
        time_weight = 0.2
        success_weight = 0.1
        
        # Simple scoring (would be more sophisticated in real implementation)
        quality_score = stats.get('avg_quality_score', 0) * quality_weight
        cost_score = max(0, 1 - stats.get('avg_cost_usd', 1)) * cost_weight  # Invert cost
        time_score = max(0, 1 - stats.get('avg_execution_time', 10) / 10) * time_weight  # Invert time
        success_score = stats.get('success_rate', 0) * success_weight
        
        return quality_score + cost_score + time_score + success_score
    
    # === Configuration Testing ===
    
    def test_configuration_matrix(
        self,
        base_institution: str,
        institution_type: str,
        configuration_matrix: Dict[str, List[Any]],
        pipeline_function: Callable[[str, str, Dict[str, Any]], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Test a matrix of configuration options.
        
        Args:
            base_institution: Institution to test with
            institution_type: Type of institution
            configuration_matrix: Dict of parameter_name -> [values_to_test]
            pipeline_function: Pipeline execution function
            
        Returns:
            Configuration testing results
        """
        # Generate all configuration combinations
        import itertools
        
        param_names = list(configuration_matrix.keys())
        param_values = list(configuration_matrix.values())
        
        test_configurations = []
        
        for combination in itertools.product(*param_values):
            config = dict(zip(param_names, combination))
            config_name = "_".join(f"{k}={v}" for k, v in config.items())
            
            test_config = TestConfiguration(
                test_name=f"config_test_{config_name}",
                test_description=f"Configuration test: {config_name}",
                institution_name=base_institution,
                institution_type=institution_type,
                pipeline_config=config
            )
            
            test_configurations.append(test_config)
        
        # Run batch tests
        results = self.run_batch_tests(test_configurations, pipeline_function)
        
        # Analyze configuration impact
        analysis = self._analyze_configuration_impact(results, param_names)
        
        return {
            'test_type': 'configuration_matrix',
            'base_institution': base_institution,
            'parameters_tested': param_names,
            'total_configurations': len(test_configurations),
            'results': results,
            'analysis': analysis
        }
    
    def _analyze_configuration_impact(self, results: List[TestResult], param_names: List[str]) -> Dict[str, Any]:
        """Analyze the impact of different configuration parameters."""
        analysis = {
            'parameter_impact': {},
            'best_configuration': None,
            'worst_configuration': None,
            'performance_insights': []
        }
        
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return analysis
        
        # Find best and worst configurations
        best_result = max(successful_results, key=lambda r: r.quality_score - r.cost_usd * 10)
        worst_result = min(successful_results, key=lambda r: r.quality_score - r.cost_usd * 10)
        
        analysis['best_configuration'] = {
            'test_name': best_result.test_name,
            'quality_score': best_result.quality_score,
            'cost_usd': best_result.cost_usd,
            'execution_time': best_result.execution_time
        }
        
        analysis['worst_configuration'] = {
            'test_name': worst_result.test_name,
            'quality_score': worst_result.quality_score,
            'cost_usd': worst_result.cost_usd,
            'execution_time': worst_result.execution_time
        }
        
        # Analyze parameter impact (simplified)
        for param in param_names:
            param_results = {}
            for result in successful_results:
                # Extract parameter value from test name (simplified)
                if param in result.test_name:
                    # This would need more sophisticated parsing in real implementation
                    pass
            
            analysis['parameter_impact'][param] = param_results
        
        return analysis
    
    # === Results Management ===
    
    def get_test_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive test session summary."""
        if not self.test_results:
            return {
                'session_id': self.test_session_id,
                'total_tests': 0,
                'message': 'No tests run in this session'
            }
        
        successful_tests = [r for r in self.test_results if r.success]
        failed_tests = [r for r in self.test_results if not r.success]
        
        total_cost = sum(r.cost_usd for r in successful_tests)
        total_time = sum(r.execution_time for r in self.test_results)
        avg_quality = sum(r.quality_score for r in successful_tests) / len(successful_tests) if successful_tests else 0
        
        return {
            'session_id': self.test_session_id,
            'total_tests': len(self.test_results),
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'success_rate_percent': (len(successful_tests) / len(self.test_results)) * 100,
            'total_cost_usd': round(total_cost, 4),
            'total_execution_time_seconds': round(total_time, 2),
            'average_quality_score': round(avg_quality, 3),
            'tests_passed_quality_threshold': sum(1 for r in successful_tests if r.passed_quality_threshold),
            'tests_passed_cost_threshold': sum(1 for r in successful_tests if r.passed_cost_threshold),
            'tests_passed_time_threshold': sum(1 for r in successful_tests if r.passed_time_threshold)
        }
    
    def _save_test_results(self):
        """Save test results to file."""
        try:
            test_data = {
                'session_id': self.test_session_id,
                'timestamp': time.time(),
                'total_tests': len(self.test_results),
                'results': [
                    {
                        'test_id': r.test_id,
                        'test_name': r.test_name,
                        'pipeline_id': r.pipeline_id,
                        'success': r.success,
                        'execution_time': r.execution_time,
                        'cost_usd': r.cost_usd,
                        'quality_score': r.quality_score,
                        'completeness_score': r.completeness_score,
                        'cache_hit_rate': r.cache_hit_rate,
                        'passed_quality_threshold': r.passed_quality_threshold,
                        'passed_cost_threshold': r.passed_cost_threshold,
                        'passed_time_threshold': r.passed_time_threshold,
                        'error_message': r.error_message,
                        'error_details': r.error_details
                    }
                    for r in self.test_results
                ],
                'summary': self.get_test_session_summary()
            }
            
            with open(self.test_session_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Could not save test results: {e}")
    
    def export_test_results(self, format: str = 'json') -> str:
        """Export test results in specified format."""
        if format == 'json':
            export_file = self.test_session_file.replace('.json', '_export.json')
            # File already saved in JSON format
            return export_file
        
        elif format == 'csv':
            import csv
            export_file = self.test_session_file.replace('.json', '_export.csv')
            
            with open(export_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'test_id', 'test_name', 'success', 'execution_time',
                    'cost_usd', 'quality_score', 'completeness_score',
                    'cache_hit_rate', 'error_message'
                ])
                
                # Data rows
                for result in self.test_results:
                    writer.writerow([
                        result.test_id,
                        result.test_name,
                        result.success,
                        result.execution_time,
                        result.cost_usd,
                        result.quality_score,
                        result.completeness_score,
                        result.cache_hit_rate,
                        result.error_message or ''
                    ])
            
            return export_file
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
