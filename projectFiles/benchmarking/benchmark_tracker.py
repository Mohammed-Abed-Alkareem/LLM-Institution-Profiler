"""
Enhanced benchmark tracker with comprehensive tracking capabilities.
"""

import os
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import asdict

from .benchmark_config import BenchmarkConfig, BenchmarkCategory
from .benchmark_metrics import (
    CostMetrics, LatencyMetrics, QualityMetrics, EfficiencyMetrics,
    PipelineMetrics, ComparisonMetrics
)


class BenchmarkTracker:
    """
    Comprehensive benchmark tracker with advanced tracking capabilities.
    
    Features:
    - Cost tracking (API calls, tokens, infrastructure)
    - Latency measurements (all phases, network, processing)
    - Quality metrics (completeness, accuracy, validation)
    - Efficiency tracking (cache, resources, processing rate)
    - Pipeline comparisons (A/B testing, configuration optimization)
    """
    
    def __init__(self, config: BenchmarkConfig):
        """Initialize the enhanced benchmark tracker."""
        self.config = config
        self.active_pipelines: Dict[str, PipelineMetrics] = {}
        self.active_comparisons: Dict[str, ComparisonMetrics] = {}
        
        # Session tracking
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_data = {
            'session_id': self.session_id,
            'start_time': time.time(),
            'pipelines': [],
            'comparisons': [],
            'summary_stats': {}
        }
          # File paths
        self.session_file = os.path.join(
            config.benchmarks_dir, 
            f"session_{self.session_id}.json"
        )
        self.all_benchmarks_file = os.path.join(
            config.benchmarks_dir, 
            "all_benchmarks.json"
        )
    
    # === Pipeline Tracking ===
    
    def start_pipeline(
        self, 
        pipeline_name: str,
        institution_name: str,
        institution_type: str,
        pipeline_version: str = "1.0",
        pipeline_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking a new pipeline execution.
        
        Args:
            pipeline_name: Name/identifier for the pipeline
            institution_name: Institution being processed
            institution_type: Type of institution
            pipeline_version: Version of the pipeline
            pipeline_config: Configuration parameters used
            
        Returns:
            Pipeline ID for tracking
        """
        pipeline_id = f"{pipeline_name}_{institution_name}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        pipeline_metrics = PipelineMetrics(
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            pipeline_version=pipeline_version,
            institution_name=institution_name,
            institution_type=institution_type,
            pipeline_config=pipeline_config or {}
        )
        
        pipeline_metrics.latency_metrics.start_timing()
        self.active_pipelines[pipeline_id] = pipeline_metrics
        
        return pipeline_id
    
    def add_search_metrics(
        self, 
        pipeline_id: str, 
        search_time: float,
        cache_hit: bool,
        api_queries: int = 0,
        results_count: int = 0,
        results_quality: float = 0.0
    ):
        """Add search phase metrics to pipeline."""
        if pipeline_id not in self.active_pipelines:
            return
        
        pipeline = self.active_pipelines[pipeline_id]
        
        # Latency
        pipeline.latency_metrics.search_time_seconds = search_time
        
        # Cost
        if api_queries > 0:
            pipeline.cost_metrics.add_search_cost(
                api_queries, 
                self.config.google_search_cost_per_1000
            )
        
        # Efficiency
        pipeline.efficiency_metrics.add_cache_request(cache_hit)
        
        # Quality
        if results_count > 0:
            pipeline.quality_metrics.relevance_score = results_quality
    
    def add_crawling_metrics(
        self,
        pipeline_id: str,
        crawling_time: float,
        pages_crawled: int,
        pages_successful: int,
        total_content_size: int,
        content_quality: float = 0.0
    ):
        """Add crawling phase metrics to pipeline."""
        if pipeline_id not in self.active_pipelines:
            return
        
        pipeline = self.active_pipelines[pipeline_id]
        
        # Latency
        pipeline.latency_metrics.crawling_time_seconds = crawling_time
        
        # Efficiency
        pipeline.efficiency_metrics.items_processed = pages_crawled
        pipeline.efficiency_metrics.calculate_processing_rate(pages_crawled, crawling_time)
        pipeline.efficiency_metrics.error_rate = (pages_crawled - pages_successful) / pages_crawled if pages_crawled > 0 else 0
        
        # Quality
        pipeline.quality_metrics.content_quality_score = content_quality
        
        # Data size
        pipeline.efficiency_metrics.input_data_size_mb = total_content_size / (1024 * 1024)
    
    def add_rag_metrics(
        self,
        pipeline_id: str,
        rag_time: float,
        chunks_processed: int,
        chunks_relevant: int,
        relevance_scores: List[float]
    ):
        """Add RAG processing phase metrics to pipeline."""
        if pipeline_id not in self.active_pipelines:
            return
        
        pipeline = self.active_pipelines[pipeline_id]
        
        # Latency
        pipeline.latency_metrics.rag_processing_time_seconds = rag_time
        
        # Quality
        if chunks_processed > 0:
            pipeline.quality_metrics.relevance_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
            pipeline.quality_metrics.precision_score = chunks_relevant / chunks_processed
    
    def add_llm_metrics(
        self,
        pipeline_id: str,
        llm_time: float,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        fields_requested: int,
        fields_extracted: int,
        confidence_scores: Optional[Dict[str, float]] = None
    ):
        """Add LLM processing phase metrics to pipeline."""
        if pipeline_id not in self.active_pipelines:
            return
        
        pipeline = self.active_pipelines[pipeline_id]
        
        # Latency
        pipeline.latency_metrics.llm_processing_time_seconds = llm_time
        
        # Cost
        if 'gpt-4' in model_name.lower():
            pipeline.cost_metrics.add_llm_cost(
                model_name, input_tokens, output_tokens,
                self.config.openai_gpt4_input_cost_per_1k_tokens,
                self.config.openai_gpt4_output_cost_per_1k_tokens
            )
        elif 'gpt-3.5' in model_name.lower():
            pipeline.cost_metrics.add_llm_cost(
                model_name, input_tokens, output_tokens,
                self.config.openai_gpt35_input_cost_per_1k_tokens,
                self.config.openai_gpt35_output_cost_per_1k_tokens
            )
        
        # Quality
        pipeline.quality_metrics.calculate_completeness(fields_requested, fields_extracted)
        if confidence_scores:
            pipeline.quality_metrics.confidence_scores = confidence_scores
    
    def add_validation_results(
        self,
        pipeline_id: str,
        validation_passed: bool,
        validation_errors: List[str],
        accuracy_score: float = 0.0
    ):
        """Add validation results to pipeline metrics."""
        if pipeline_id not in self.active_pipelines:
            return
        
        pipeline = self.active_pipelines[pipeline_id]
        pipeline.quality_metrics.validation_passed = validation_passed
        pipeline.quality_metrics.validation_errors = validation_errors
        pipeline.quality_metrics.accuracy_score = accuracy_score
    
    def complete_pipeline(
        self,
        pipeline_id: str,
        success: bool,
        error_message: Optional[str] = None,
        results_summary: Optional[Dict[str, Any]] = None
    ) -> Optional[PipelineMetrics]:
        """
        Complete pipeline tracking and save results.
        
        Args:
            pipeline_id: Pipeline ID
            success: Whether pipeline completed successfully
            error_message: Error message if failed
            results_summary: Summary of results produced
            
        Returns:
            Completed pipeline metrics
        """
        if pipeline_id not in self.active_pipelines:
            return None
        
        pipeline = self.active_pipelines[pipeline_id]
        pipeline.mark_completed(success, error_message)
        
        if results_summary:
            pipeline.results_summary = results_summary
        
        # Save to session
        self.session_data['pipelines'].append(asdict(pipeline))
        
        # Save files
        self._save_session_data()
        self._append_to_all_benchmarks(pipeline)
        
        # Remove from active tracking
        completed_pipeline = self.active_pipelines.pop(pipeline_id)
        
        return completed_pipeline
    
    # === Comparison Tracking ===
    
    def start_comparison(
        self,
        comparison_name: str,
        baseline_pipeline: str,
        test_pipelines: List[str]
    ) -> str:
        """Start a pipeline comparison test."""
        comparison_id = f"comp_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        comparison = ComparisonMetrics(
            comparison_id=comparison_id,
            comparison_name=comparison_name,
            baseline_pipeline=baseline_pipeline,
            test_pipelines=test_pipelines
        )
        
        self.active_comparisons[comparison_id] = comparison
        return comparison_id
    
    def add_pipeline_to_comparison(
        self,
        comparison_id: str,
        pipeline_metrics: PipelineMetrics
    ):
        """Add pipeline results to a comparison."""
        if comparison_id not in self.active_comparisons:
            return
        
        comparison = self.active_comparisons[comparison_id]
        comparison.add_pipeline_comparison(pipeline_metrics.pipeline_id, pipeline_metrics)
    
    def complete_comparison(
        self,
        comparison_id: str,
        weight_cost: float = 0.3,
        weight_latency: float = 0.3,
        weight_quality: float = 0.4
    ) -> Optional[ComparisonMetrics]:
        """Complete comparison and determine winner."""
        if comparison_id not in self.active_comparisons:
            return None
        
        comparison = self.active_comparisons[comparison_id]
        winner = comparison.determine_winner(weight_cost, weight_latency, weight_quality)
        
        # Save comparison results
        self.session_data['comparisons'].append(asdict(comparison))
        self._save_session_data()
        
        # Remove from active tracking
        completed_comparison = self.active_comparisons.pop(comparison_id)
        
        return completed_comparison
    
    # === Analytics and Reporting ===
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        pipelines = self.session_data['pipelines']
        
        if not pipelines:
            return {
                'session_id': self.session_id,
                'pipelines_count': 0,
                'message': 'No pipelines tracked in this session'
            }
        
        # Calculate summary statistics
        total_cost = sum(p.get('cost_metrics', {}).get('total_cost_usd', 0) for p in pipelines)
        total_time = sum(p.get('latency_metrics', {}).get('total_pipeline_time_seconds', 0) for p in pipelines)
        success_count = sum(1 for p in pipelines if p.get('success', False))
        
        avg_quality = sum(
            p.get('quality_metrics', {}).get('completeness_score', 0) 
            for p in pipelines if p.get('success', False)
        ) / max(success_count, 1)
        
        avg_efficiency = sum(
            p.get('efficiency_metrics', {}).get('cache_hit_rate', 0) 
            for p in pipelines if p.get('success', False)
        ) / max(success_count, 1)
        
        return {
            'session_id': self.session_id,
            'session_start': datetime.fromtimestamp(self.session_data['start_time']).isoformat(),
            'pipelines_count': len(pipelines),
            'successful_pipelines': success_count,
            'success_rate_percent': (success_count / len(pipelines)) * 100,
            'total_cost_usd': round(total_cost, 4),
            'total_time_seconds': round(total_time, 2),
            'average_quality_score': round(avg_quality, 3),
            'average_cache_hit_rate': round(avg_efficiency, 3),
            'comparisons_count': len(self.session_data['comparisons'])
        }
    
    def get_cost_breakdown(self) -> Dict[str, Any]:
        """Get detailed cost breakdown across all tracked pipelines."""
        pipelines = self.session_data['pipelines']
        
        total_search_cost = sum(p.get('cost_metrics', {}).get('google_search_cost_usd', 0) for p in pipelines)
        total_llm_cost = sum(p.get('cost_metrics', {}).get('llm_cost_usd', 0) for p in pipelines)
        total_infrastructure_cost = sum(p.get('cost_metrics', {}).get('infrastructure_cost_usd', 0) for p in pipelines)
        
        total_search_queries = sum(p.get('cost_metrics', {}).get('google_search_queries', 0) for p in pipelines)
        total_tokens = sum(p.get('cost_metrics', {}).get('total_tokens', 0) for p in pipelines)
        
        return {
            'cost_breakdown': {
                'search_api_usd': round(total_search_cost, 4),
                'llm_processing_usd': round(total_llm_cost, 4),
                'infrastructure_usd': round(total_infrastructure_cost, 4),
                'total_usd': round(total_search_cost + total_llm_cost + total_infrastructure_cost, 4)
            },
            'usage_stats': {
                'google_search_queries': total_search_queries,
                'llm_tokens_processed': total_tokens,
                'cost_per_query': round((total_search_cost + total_llm_cost) / max(total_search_queries, 1), 4),
                'cost_per_token': round(total_llm_cost / max(total_tokens, 1), 6)
            }
        }
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """Get comprehensive performance analysis."""
        pipelines = self.session_data['pipelines']
        successful_pipelines = [p for p in pipelines if p.get('success', False)]
        
        if not successful_pipelines:
            return {'message': 'No successful pipelines to analyze'}
        
        # Latency analysis
        search_times = [p.get('latency_metrics', {}).get('search_time_seconds', 0) for p in successful_pipelines]
        crawl_times = [p.get('latency_metrics', {}).get('crawling_time_seconds', 0) for p in successful_pipelines]
        llm_times = [p.get('latency_metrics', {}).get('llm_processing_time_seconds', 0) for p in successful_pipelines]
        total_times = [p.get('latency_metrics', {}).get('total_pipeline_time_seconds', 0) for p in successful_pipelines]
        
        # Quality analysis
        quality_scores = [p.get('quality_metrics', {}).get('completeness_score', 0) for p in successful_pipelines]
        cache_hit_rates = [p.get('efficiency_metrics', {}).get('cache_hit_rate', 0) for p in successful_pipelines]
        
        def safe_avg(values):
            return sum(values) / len(values) if values else 0
        
        return {
            'latency_analysis': {
                'avg_search_time_seconds': round(safe_avg(search_times), 3),
                'avg_crawling_time_seconds': round(safe_avg(crawl_times), 3),
                'avg_llm_time_seconds': round(safe_avg(llm_times), 3),
                'avg_total_time_seconds': round(safe_avg(total_times), 3),
                'max_total_time_seconds': round(max(total_times) if total_times else 0, 3)
            },
            'quality_analysis': {
                'avg_completeness_score': round(safe_avg(quality_scores), 3),
                'min_completeness_score': round(min(quality_scores) if quality_scores else 0, 3),
                'max_completeness_score': round(max(quality_scores) if quality_scores else 0, 3),
                'quality_threshold_met': sum(1 for q in quality_scores if q >= self.config.min_completeness_score)
            },
            'efficiency_analysis': {
                'avg_cache_hit_rate': round(safe_avg(cache_hit_rates), 3),
                'efficiency_threshold_met': sum(1 for c in cache_hit_rates if c >= self.config.target_cache_hit_rate),
                'total_pipelines_analyzed': len(successful_pipelines)
            }
        }
    
    def get_comparison_results(self) -> List[Dict[str, Any]]:
        """Get results from all completed comparisons."""
        return [
            {
                'comparison_id': comp['comparison_id'],
                'comparison_name': comp['comparison_name'],
                'baseline_pipeline': comp['baseline_pipeline'],
                'test_pipelines': comp['test_pipelines'],
                'recommended_pipeline': comp.get('recommended_pipeline'),
                'cost_comparison': comp.get('cost_comparison', {}),
                'latency_comparison': comp.get('latency_comparison', {}),
                'quality_comparison': comp.get('quality_comparison', {})
            }
            for comp in self.session_data['comparisons']
        ]
    
    # === File Management ===
    
    def _save_session_data(self):
        """Save current session data to file."""
        try:
            self.session_data['last_updated'] = time.time()
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save session data: {e}")
    
    def _append_to_all_benchmarks(self, pipeline: PipelineMetrics):
        """Append pipeline to historical benchmarks file."""
        try:
            all_benchmarks = []
            
            if os.path.exists(self.all_benchmarks_file):
                with open(self.all_benchmarks_file, 'r', encoding='utf-8') as f:
                    all_benchmarks = json.load(f)
            
            all_benchmarks.append(asdict(pipeline))
            
            # Keep only recent benchmarks if too many
            if len(all_benchmarks) > self.config.max_benchmark_files:
                all_benchmarks = all_benchmarks[-self.config.max_benchmark_files:]
            
            with open(self.all_benchmarks_file, 'w', encoding='utf-8') as f:
                json.dump(all_benchmarks, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Could not update all benchmarks: {e}")
    
    def cleanup_old_data(self, days: int = None) -> Dict[str, Any]:
        """Clean up old benchmark data."""
        days = days or self.config.retention_days
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        cleaned_files = 0
        cleaned_benchmarks = 0
        
        try:
            # Clean session files
            for filename in os.listdir(self.config.benchmarks_dir):
                if filename.startswith('session_') and filename.endswith('.json'):
                    file_path = os.path.join(self.config.benchmarks_dir, filename)
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        cleaned_files += 1
            
            # Clean all benchmarks file
            if os.path.exists(self.all_benchmarks_file):
                with open(self.all_benchmarks_file, 'r', encoding='utf-8') as f:
                    all_benchmarks = json.load(f)
                
                original_count = len(all_benchmarks)
                all_benchmarks = [
                    b for b in all_benchmarks 
                    if b.get('latency_metrics', {}).get('start_timestamp', 0) > cutoff_time
                ]
                cleaned_benchmarks = original_count - len(all_benchmarks)
                
                with open(self.all_benchmarks_file, 'w', encoding='utf-8') as f:
                    json.dump(all_benchmarks, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            return {'error': f"Cleanup failed: {e}"}
        
        return {
            'cleaned_files': cleaned_files,
            'cleaned_benchmarks': cleaned_benchmarks,
            'cutoff_date': datetime.fromtimestamp(cutoff_time).isoformat()
        }
