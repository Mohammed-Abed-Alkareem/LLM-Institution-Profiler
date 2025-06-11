"""
Comprehensive metrics data classes for the enhanced benchmarking system.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json


@dataclass
class CostMetrics:
    """Comprehensive cost tracking metrics."""
    
    # API costs
    google_search_queries: int = 0
    google_search_cost_usd: float = 0.0
    
    # LLM costs
    llm_model_used: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    llm_cost_usd: float = 0.0
    
    # Infrastructure costs (estimates)
    compute_time_seconds: float = 0.0
    storage_bytes: int = 0
    bandwidth_bytes: int = 0
    infrastructure_cost_usd: float = 0.0
    
    # Total cost
    total_cost_usd: float = 0.0
    
    def add_search_cost(self, queries: int, cost_per_1000: float):
        """Add Google search API cost."""
        self.google_search_queries += queries
        cost = (queries / 1000) * cost_per_1000
        self.google_search_cost_usd += cost
        self.total_cost_usd += cost
    
    def add_llm_cost(self, model: str, input_tokens: int, output_tokens: int, 
                    input_cost_per_1k: float, output_cost_per_1k: float):
        """Add LLM usage cost."""
        self.llm_model_used = model
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens
        
        cost = ((input_tokens / 1000) * input_cost_per_1k + 
               (output_tokens / 1000) * output_cost_per_1k)
        self.llm_cost_usd += cost
        self.total_cost_usd += cost
    
    def add_infrastructure_cost(self, compute_seconds: float, storage_bytes: int, 
                              bandwidth_bytes: int, hourly_rate: float = 0.10):
        """Add estimated infrastructure cost."""
        self.compute_time_seconds += compute_seconds
        self.storage_bytes += storage_bytes
        self.bandwidth_bytes += bandwidth_bytes
        
        # Simple cost estimate
        cost = (compute_seconds / 3600) * hourly_rate
        self.infrastructure_cost_usd += cost
        self.total_cost_usd += cost


@dataclass
class LatencyMetrics:
    """Comprehensive latency tracking metrics."""
    
    # Phase timings
    search_time_seconds: float = 0.0
    crawling_time_seconds: float = 0.0
    rag_processing_time_seconds: float = 0.0
    llm_processing_time_seconds: float = 0.0
    total_pipeline_time_seconds: float = 0.0
    
    # Detailed timings
    cache_lookup_time_seconds: float = 0.0
    api_call_time_seconds: float = 0.0
    data_processing_time_seconds: float = 0.0
    
    # Network latency
    network_requests: int = 0
    total_network_time_seconds: float = 0.0
    average_network_latency_ms: float = 0.0
    
    # Timestamps
    start_timestamp: float = field(default_factory=time.time)
    end_timestamp: Optional[float] = None
    
    def start_timing(self):
        """Start timing the operation."""
        self.start_timestamp = time.time()
    
    def end_timing(self):
        """End timing and calculate total time."""
        self.end_timestamp = time.time()
        self.total_pipeline_time_seconds = self.end_timestamp - self.start_timestamp
    
    def add_network_request(self, request_time_seconds: float):
        """Add network request timing."""
        self.network_requests += 1
        self.total_network_time_seconds += request_time_seconds
        self.average_network_latency_ms = (self.total_network_time_seconds / self.network_requests) * 1000


@dataclass
class QualityMetrics:
    """Comprehensive quality tracking metrics."""
    
    # Data completeness
    fields_requested: int = 0
    fields_extracted: int = 0
    completeness_score: float = 0.0
    
    # Data accuracy (when ground truth available)
    accuracy_score: float = 0.0
    precision_score: float = 0.0
    recall_score: float = 0.0
    f1_score: float = 0.0
    
    # Content quality
    content_quality_score: float = 0.0
    relevance_score: float = 0.0
    coherence_score: float = 0.0
    
    # Validation results
    validation_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    # Source quality
    source_authority_score: float = 0.0
    source_freshness_score: float = 0.0
    source_credibility_score: float = 0.0
    
    def calculate_completeness(self, fields_requested: int, fields_extracted: int):
        """Calculate data completeness score."""
        self.fields_requested = fields_requested
        self.fields_extracted = fields_extracted
        self.completeness_score = fields_extracted / fields_requested if fields_requested > 0 else 0.0
    
    def calculate_overall_quality(self):
        """Calculate overall quality score from individual metrics."""
        scores = [
            self.completeness_score,
            self.accuracy_score,
            self.content_quality_score,
            self.relevance_score,
            self.source_authority_score
        ]
        valid_scores = [s for s in scores if s > 0]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0.0


@dataclass
class EfficiencyMetrics:
    """Comprehensive efficiency tracking metrics."""
    
    # Cache efficiency
    cache_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    
    # Resource utilization
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    disk_io_mb: float = 0.0
    network_io_mb: float = 0.0
    
    # Processing efficiency
    items_processed: int = 0
    processing_rate_per_second: float = 0.0
    error_rate: float = 0.0
    retry_count: int = 0
    
    # Data efficiency
    input_data_size_mb: float = 0.0
    output_data_size_mb: float = 0.0
    compression_ratio: float = 0.0
    
    def add_cache_request(self, hit: bool):
        """Add cache request result."""
        self.cache_requests += 1
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        self.cache_hit_rate = self.cache_hits / self.cache_requests if self.cache_requests > 0 else 0.0
    
    def calculate_processing_rate(self, items: int, time_seconds: float):
        """Calculate processing rate."""
        self.items_processed += items
        self.processing_rate_per_second = items / time_seconds if time_seconds > 0 else 0.0


@dataclass
class PipelineMetrics:
    """Comprehensive pipeline performance metrics."""
    
    # Pipeline identification
    pipeline_id: str
    pipeline_name: str
    pipeline_version: str
    institution_name: str
    institution_type: str
    
    # Component metrics
    cost_metrics: CostMetrics = field(default_factory=CostMetrics)
    latency_metrics: LatencyMetrics = field(default_factory=LatencyMetrics)
    quality_metrics: QualityMetrics = field(default_factory=QualityMetrics)
    efficiency_metrics: EfficiencyMetrics = field(default_factory=EfficiencyMetrics)
    
    # Pipeline state
    status: str = "running"  # running, completed, failed, cancelled
    success: bool = False
    error_message: Optional[str] = None
    
    # Configuration
    pipeline_config: Dict[str, Any] = field(default_factory=dict)
    
    # Results
    results_summary: Dict[str, Any] = field(default_factory=dict)
    
    def mark_completed(self, success: bool, error_message: Optional[str] = None):
        """Mark pipeline as completed."""
        self.status = "completed" if success else "failed"
        self.success = success
        self.error_message = error_message
        self.latency_metrics.end_timing()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get pipeline summary for reporting."""
        return {
            'pipeline_id': self.pipeline_id,
            'pipeline_name': self.pipeline_name,
            'institution_name': self.institution_name,
            'institution_type': self.institution_type,
            'status': self.status,
            'success': self.success,
            'total_cost_usd': self.cost_metrics.total_cost_usd,
            'total_time_seconds': self.latency_metrics.total_pipeline_time_seconds,
            'quality_score': self.quality_metrics.calculate_overall_quality(),
            'cache_hit_rate': self.efficiency_metrics.cache_hit_rate,
            'completeness_score': self.quality_metrics.completeness_score
        }


@dataclass
class ComparisonMetrics:
    """Metrics for comparing different pipeline configurations."""
    
    comparison_id: str
    comparison_name: str
    baseline_pipeline: str
    test_pipelines: List[str]
    
    # Comparison results
    cost_comparison: Dict[str, float] = field(default_factory=dict)
    latency_comparison: Dict[str, float] = field(default_factory=dict)
    quality_comparison: Dict[str, float] = field(default_factory=dict)
    efficiency_comparison: Dict[str, float] = field(default_factory=dict)
    
    # Statistical analysis
    statistical_significance: Dict[str, bool] = field(default_factory=dict)
    confidence_intervals: Dict[str, tuple] = field(default_factory=dict)
    
    # Recommendations
    recommended_pipeline: Optional[str] = None
    recommendation_reason: Optional[str] = None
    
    def add_pipeline_comparison(self, pipeline_id: str, metrics: PipelineMetrics):
        """Add pipeline to comparison."""
        self.cost_comparison[pipeline_id] = metrics.cost_metrics.total_cost_usd
        self.latency_comparison[pipeline_id] = metrics.latency_metrics.total_pipeline_time_seconds
        self.quality_comparison[pipeline_id] = metrics.quality_metrics.calculate_overall_quality()
        self.efficiency_comparison[pipeline_id] = metrics.efficiency_metrics.cache_hit_rate
    
    def determine_winner(self, weight_cost: float = 0.3, weight_latency: float = 0.3, 
                        weight_quality: float = 0.4) -> str:
        """Determine the best pipeline based on weighted criteria."""
        if not self.test_pipelines:
            return self.baseline_pipeline
        
        scores = {}
        
        # Normalize metrics (0-1 scale)
        max_cost = max(self.cost_comparison.values()) if self.cost_comparison else 1
        max_latency = max(self.latency_comparison.values()) if self.latency_comparison else 1
        max_quality = max(self.quality_comparison.values()) if self.quality_comparison else 1
        
        for pipeline_id in [self.baseline_pipeline] + self.test_pipelines:
            cost_score = 1 - (self.cost_comparison.get(pipeline_id, 0) / max_cost)  # Lower cost is better
            latency_score = 1 - (self.latency_comparison.get(pipeline_id, 0) / max_latency)  # Lower latency is better
            quality_score = self.quality_comparison.get(pipeline_id, 0) / max_quality  # Higher quality is better
            
            weighted_score = (weight_cost * cost_score + 
                            weight_latency * latency_score + 
                            weight_quality * quality_score)
            scores[pipeline_id] = weighted_score
        
        winner = max(scores.keys(), key=lambda k: scores[k])
        self.recommended_pipeline = winner
        
        return winner
