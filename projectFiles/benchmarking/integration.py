"""
Enhanced Benchmarking Integration for Institution Profiler

This module provides easy integration of the enhanced benchmarking system
with the existing application components.
"""

import os
import time
import json
from typing import Dict, List, Optional, Any, Callable
from functools import wraps

from benchmarking.benchmark_config import BenchmarkConfig, BenchmarkCategory
from benchmarking.benchmark_tracker import BenchmarkTracker
from benchmarking.benchmark_metrics import (
    CostMetrics, LatencyMetrics, QualityMetrics, EfficiencyMetrics,
    PipelineMetrics
)


class BenchmarkingManager:
    """
    Central manager for integrating enhanced benchmarking with the application.
    
    Provides decorators and context managers for easy benchmarking integration.
    """
    def __init__(self, base_dir: str):
        """Initialize the benchmarking manager."""
        self.base_dir = base_dir
        self.config = BenchmarkConfig.from_base_dir(base_dir)
        self.tracker = BenchmarkTracker(self.config)
        
        # Tracking state
        self.active_benchmarks: Dict[str, str] = {}  # operation_id -> benchmark_id
        self.cost_accumulator = CostMetrics()
        
    def benchmark_operation(
        self, 
        category: BenchmarkCategory = BenchmarkCategory.PIPELINE,
        institution_name: str = "unknown",
        institution_type: str = "general",
        track_cost: bool = True,
        track_latency: bool = True,
        track_quality: bool = True
    ):
        """
        Decorator for benchmarking any operation.
        
        Usage:
            @manager.benchmark_operation(BenchmarkCategory.SEARCH)
            def my_search_function(query):
                return search_results
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Start benchmark
                benchmark_id = self.start_operation_benchmark(
                    category, institution_name, institution_type
                )
                
                start_time = time.time()
                success = False
                result = None
                error = None
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                    
                    # Extract metrics from result if available
                    if isinstance(result, dict):
                        self._extract_metrics_from_result(benchmark_id, result)
                    
                except Exception as e:
                    error = str(e)
                    success = False
                    raise
                
                finally:
                    # Record latency
                    if track_latency:
                        execution_time = time.time() - start_time
                        self.record_latency(benchmark_id, category.value, execution_time)
                    
                    # Complete benchmark
                    self.complete_operation_benchmark(benchmark_id, success, error)
                return result
                
            return wrapper
        return decorator
    
    def start_operation_benchmark(
        self,
        category: BenchmarkCategory,
        institution_name: str = "unknown",
        institution_type: str = "general",
        config: Dict[str, Any] = None
    ) -> str:
        """Start benchmarking for an operation."""
        pipeline_id = self.tracker.start_pipeline(
            pipeline_name=category.value,
            institution_name=institution_name,
            institution_type=institution_type,
            pipeline_version="1.0",
            pipeline_config=config or {}        )
        
        return pipeline_id
    
    def record_cost(
        self,
        benchmark_id: str,
        api_calls: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        service_type: str = "general"
    ):
        """Record cost metrics for an operation."""
        # For search API calls, record as search metrics
        if api_calls > 0 and service_type == "google_search":
            self.tracker.add_search_metrics(
                pipeline_id=benchmark_id,
                search_time=0.0,  # Time tracked separately
                cache_hit=False,  # API call means no cache hit
                api_queries=api_calls,
                results_count=10,  # Estimate
                results_quality=0.8
            )
        
        # For LLM costs, use LLM metrics
        if input_tokens > 0 or output_tokens > 0:
            model_name = service_type if service_type in ["openai_gpt4", "openai_gpt35"] else "general"
            self.tracker.add_llm_metrics(
                pipeline_id=benchmark_id,
                llm_time=0.0,  # Time tracked separately
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                fields_requested=1,
                fields_extracted=1
            )
    def record_latency(
        self,
        benchmark_id: str,
        operation_type: str,
        duration: float,
        network_time: float = 0.0,
        processing_time: float = 0.0
    ):
        """Record latency metrics for an operation."""        
        if operation_type == "search":
            self.tracker.add_search_metrics(
                pipeline_id=benchmark_id,
                search_time=duration,
                cache_hit=False,  # Default assumption
                api_queries=1,
                results_count=10,
                results_quality=0.8
            )        
        elif operation_type == "crawling":
            self.tracker.add_crawling_metrics(
                pipeline_id=benchmark_id,
                crawling_time=duration,
                pages_crawled=1,
                pages_successful=1,
                total_content_size=1000,  # Estimate
                content_quality=0.8
            )        
        elif operation_type in ["llm", "processing"]:
            self.tracker.add_llm_metrics(
                pipeline_id=benchmark_id,
                llm_time=duration,
                model_name="general",                input_tokens=0,
                output_tokens=0,
                fields_requested=1,
                fields_extracted=1
            )
    
    def record_quality(
        self,
        benchmark_id: str,
        completeness_score: float = 0.0,
        accuracy_score: float = 0.0,
        relevance_score: float = 0.0,
        confidence_scores: Dict[str, float] = None
    ):
        """Record quality metrics for an operation."""
        # Use validation results to record quality
        validation_errors = []
        if completeness_score < 0.5:
            validation_errors.append("Low completeness score")
        if accuracy_score < 0.5:
            validation_errors.append("Low accuracy score")
        
        self.tracker.add_validation_results(
            pipeline_id=benchmark_id,
            validation_passed=completeness_score > 0.5,
            validation_errors=validation_errors,
            accuracy_score=accuracy_score
        )
    def record_content_metrics(
        self,
        benchmark_id: str,
        content_size: int = 0,
        word_count: int = 0,
        structured_data_size: int = 0,
        media_count: int = 0
    ):
        """Record content processing metrics."""
        # Use crawling metrics to record content information
        self.tracker.add_crawling_metrics(
            pipeline_id=benchmark_id,
            crawling_time=0.0,  # Time recorded separately
            pages_crawled=1,
            pages_successful=1,
            total_content_size=content_size,
            content_quality=0.8  # Default quality score
        )
    def complete_operation_benchmark(
        self,
        benchmark_id: str,
        success: bool,
        error: str = None
    ):
        """Complete an operation benchmark."""
        self.tracker.complete_pipeline(
            pipeline_id=benchmark_id,
            success=success,
            error_message=error
        )
    
    def _extract_metrics_from_result(self, benchmark_id: str, result: Dict[str, Any]):
        """Extract metrics from operation result if available."""
        # Extract search metrics
        if 'response_time' in result:
            self.record_latency(benchmark_id, "api_response", result['response_time'])
        
        if 'source' in result:
            # Quality metric based on cache hit
            cache_hit = 1.0 if result['source'] == 'cache' else 0.0
            self.record_quality(benchmark_id, confidence_scores={'cache_efficiency': cache_hit})
        
        # Extract crawling metrics
        if 'crawl_results' in result:
            crawl_data = result['crawl_results']
            if isinstance(crawl_data, dict):
                total_size = sum(r.get('content_size', 0) for r in crawl_data.get('results', []))
                total_words = sum(r.get('word_count', 0) for r in crawl_data.get('results', []))
                
                self.record_content_metrics(
                    benchmark_id,
                    content_size=total_size,
                    word_count=total_words
                )
        
        # Extract cost information if available
        if 'api_calls' in result:
            self.record_cost(
                benchmark_id,
                api_calls=result['api_calls'],
                service_type=result.get('service_type', 'general')
            )
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        return self.tracker.get_session_summary()
    
    def get_recent_benchmarks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent benchmark results from saved files."""
        all_benchmarks = []
        
        try:            # Load benchmark files  
            benchmarks_file = os.path.join(self.config.benchmarks_dir, "all_benchmarks.json")
            if os.path.exists(benchmarks_file):
                with open(benchmarks_file, 'r', encoding='utf-8') as f:
                    benchmark_data = json.load(f)
                    all_benchmarks.extend(benchmark_data)
              # Load session benchmarks
            session_files = [f for f in os.listdir(self.config.benchmarks_dir) 
                           if f.startswith('session_') and f.endswith('.json')]
            
            for session_file in sorted(session_files, reverse=True)[:5]:  # Last 5 sessions
                session_path = os.path.join(self.config.benchmarks_dir, session_file)
                try:
                    with open(session_path, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        if 'pipelines' in session_data:
                            all_benchmarks.extend(session_data['pipelines'])
                except Exception as e:
                    print(f"Warning: Could not load session file {session_file}: {e}")
            
            # Sort by timestamp (most recent first) and limit
            all_benchmarks.sort(key=lambda x: x.get('end_time', x.get('timestamp', 0)), reverse=True)
            recent_benchmarks = all_benchmarks[:limit]
            
            # Convert to consistent format for the API
            converted_benchmarks = []
            for benchmark in recent_benchmarks:
                converted = {
                    'pipeline_id': benchmark.get('pipeline_id', 'unknown'),
                    'institution_name': benchmark.get('institution_name', 'unknown'),
                    'institution_type': benchmark.get('institution_type', 'unknown'), 
                    'pipeline_name': benchmark.get('pipeline_name', 'unknown'),
                    'category': benchmark.get('category', 'general'),
                    'success': benchmark.get('success', benchmark.get('status') == 'completed'),
                    'total_cost': benchmark.get('total_cost_usd', benchmark.get('cost_metrics', {}).get('total_cost_usd', 0)),
                    'total_latency': benchmark.get('total_latency_seconds', benchmark.get('latency_metrics', {}).get('total_duration', 0)),
                    'timestamp': benchmark.get('end_time', benchmark.get('timestamp', 0)),
                    'quality_score': benchmark.get('quality_metrics', {}).get('overall_score', 0)
                }
                converted_benchmarks.append(converted)
            
            return converted_benchmarks
            
        except Exception as e:
            print(f"Warning: Could not load benchmark files: {e}")
            # Fallback to in-memory data
            completed_pipelines = list(self.tracker.active_pipelines.values())[:limit]
            return [
                {
                    'pipeline_id': p.pipeline_id,
                    'institution_name': p.institution_name,
                    'institution_type': p.institution_type,
                    'pipeline_name': p.pipeline_name,
                    'category': 'general',
                    'success': True,
                    'total_cost': 0,
                    'total_latency': 0,
                    'timestamp': time.time(),
                    'quality_score': 0
                }
                for p in completed_pipelines
            ]
    
    def export_benchmarks(self, format: str = 'json') -> str:
        """Export benchmark data."""
        if format == 'json':
            return json.dumps(self.get_session_summary(), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")


class BenchmarkContext:
    """Context manager for benchmarking operations."""
    
    def __init__(
        self,
        manager: BenchmarkingManager,
        category: BenchmarkCategory,
        institution_name: str = "unknown",
        institution_type: str = "general"
    ):
        self.manager = manager
        self.category = category
        self.institution_name = institution_name
        self.institution_type = institution_type
        self.benchmark_id = None
        self.start_time = None
    
    def __enter__(self):
        """Start benchmarking context."""
        self.benchmark_id = self.manager.start_operation_benchmark(
            self.category, self.institution_name, self.institution_type
        )
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End benchmarking context."""
        success = exc_type is None
        error = str(exc_val) if exc_val else None
        
        # Record total latency
        if self.start_time:
            total_time = time.time() - self.start_time
            self.manager.record_latency(
                self.benchmark_id, 
                self.category.value, 
                total_time
            )
        
        self.manager.complete_operation_benchmark(
            self.benchmark_id, success, error
        )
    
    def record_cost(self, **kwargs):
        """Record cost within context."""
        self.manager.record_cost(self.benchmark_id, **kwargs)
    
    def record_quality(self, **kwargs):
        """Record quality within context."""
        self.manager.record_quality(self.benchmark_id, **kwargs)
    
    def record_content(self, **kwargs):
        """Record content metrics within context."""
        self.manager.record_content_metrics(self.benchmark_id, **kwargs)


# Global instance for easy access
_global_manager: Optional[BenchmarkingManager] = None


def initialize_benchmarking(base_dir: str) -> BenchmarkingManager:
    """Initialize global benchmarking manager."""
    global _global_manager
    _global_manager = BenchmarkingManager(base_dir)
    return _global_manager


def get_benchmarking_manager() -> Optional[BenchmarkingManager]:
    """Get the global benchmarking manager."""
    return _global_manager


def benchmark(
    category: BenchmarkCategory = BenchmarkCategory.PIPELINE,
    institution_name: str = "unknown",
    institution_type: str = "general"
):
    """Convenience decorator for benchmarking."""
    if _global_manager is None:
        raise RuntimeError("Benchmarking not initialized. Call initialize_benchmarking() first.")
    
    return _global_manager.benchmark_operation(category, institution_name, institution_type)


def benchmark_context(
    category: BenchmarkCategory,
    institution_name: str = "unknown",
    institution_type: str = "general"
) -> BenchmarkContext:
    """Convenience context manager for benchmarking."""
    if _global_manager is None:
        raise RuntimeError("Benchmarking not initialized. Call initialize_benchmarking() first.")
    
    return BenchmarkContext(_global_manager, category, institution_name, institution_type)


# Specialized decorators for common operations
def benchmark_search(institution_name: str = "unknown", institution_type: str = "general"):
    """Decorator for search operations."""
    return benchmark(BenchmarkCategory.SEARCH, institution_name, institution_type)


def benchmark_crawling(institution_name: str = "unknown", institution_type: str = "general"):
    """Decorator for crawling operations."""
    return benchmark(BenchmarkCategory.CRAWLER, institution_name, institution_type)


def benchmark_llm(institution_name: str = "unknown", institution_type: str = "general"):
    """Decorator for LLM operations."""
    return benchmark(BenchmarkCategory.LLM, institution_name, institution_type)


# Cost tracking utilities
def track_api_cost(service: str, calls: int = 0, tokens: Dict[str, int] = None):
    """Utility to track API costs easily."""
    if _global_manager is None:
        return
    
    # This would need to be called within a benchmark context
    # Implementation would depend on current benchmark tracking
    pass


def track_content_processing(size: int, word_count: int = 0, media_count: int = 0):
    """Utility to track content processing metrics."""
    if _global_manager is None:
        return
    
    # This would need to be called within a benchmark context
    # Implementation would depend on current benchmark tracking
    pass
