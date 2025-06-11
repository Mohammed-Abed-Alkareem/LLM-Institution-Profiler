"""
Configuration and category definitions for the enhanced benchmarking system.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import os
from datetime import datetime


class BenchmarkCategory(Enum):
    """Categories of benchmarks for organization and analysis."""
    SEARCH = "search"
    CRAWLER = "crawler"
    RAG = "rag"
    LLM = "llm"
    PIPELINE = "pipeline"
    COST = "cost"
    LATENCY = "latency"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    COMPARISON = "comparison"


@dataclass
class BenchmarkConfig:
    """Configuration for benchmarking operations."""
    
    # Directory settings
    benchmarks_dir: str
    reports_dir: str
    test_results_dir: str
    
    # Tracking settings
    enable_cost_tracking: bool = True
    enable_latency_tracking: bool = True
    enable_quality_tracking: bool = True
    enable_efficiency_tracking: bool = True
    
    # Storage settings
    max_benchmark_files: int = 1000
    retention_days: int = 30
    auto_cleanup: bool = True
    
    # Reporting settings
    auto_generate_reports: bool = True
    report_formats: List[str] = field(default_factory=lambda: ['json', 'html'])
    
    # Testing settings
    test_batch_size: int = 10
    parallel_tests: bool = True
    max_concurrent_tests: int = 3
    # Cost tracking settings
    google_search_cost_per_1000: float = 5.00  # USD
    openai_gpt4_input_cost_per_1k_tokens: float = 0.03  # USD
    openai_gpt4_output_cost_per_1k_tokens: float = 0.06  # USD
    openai_gpt35_input_cost_per_1k_tokens: float = 0.0015  # USD
    openai_gpt35_output_cost_per_1k_tokens: float = 0.002  # USD
    # Gemini pricing (using Gemini 2.0 Flash pricing)
    gemini_flash_input_cost_per_1k_tokens: float = 0.000010  # USD (free tier: $0.10 per 1M tokens)
    gemini_flash_output_cost_per_1k_tokens: float = 0.00040  # USD (free tier: $0.40 per 1M tokens)
    
    # Quality thresholds
    min_quality_score: float = 0.7
    min_completeness_score: float = 0.8
    min_accuracy_score: float = 0.85
    
    # Efficiency thresholds
    target_cache_hit_rate: float = 0.8
    max_response_time_seconds: float = 5.0
    max_crawl_time_per_page_seconds: float = 10.0
    
    def __post_init__(self):
        """Ensure required directories exist."""
        for directory in [self.benchmarks_dir, self.reports_dir, self.test_results_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def from_base_dir(cls, base_dir: str) -> 'BenchmarkConfig':
        """Create config from base project directory."""
        project_cache = os.path.join(base_dir, 'project_cache')
        
        return cls(
            benchmarks_dir=os.path.join(project_cache, 'benchmarks'),
            reports_dir=os.path.join(project_cache, 'reports'),
            test_results_dir=os.path.join(project_cache, 'test_results')
        )
    
    def get_session_filename(self, category: BenchmarkCategory) -> str:
        """Generate session filename for a benchmark category."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{category.value}_session_{timestamp}.json"
    
    def get_report_filename(self, report_type: str, format: str = 'json') -> str:
        """Generate report filename."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{report_type}_report_{timestamp}.{format}"
    
    def get_cost_estimate(self, service: str, usage: Dict[str, Any]) -> float:
        """Calculate cost estimate for a service."""
        cost = 0.0
        
        if service == 'google_search':
            queries = usage.get('queries', 0)
            cost = (queries / 1000) * self.google_search_cost_per_1000
            
        elif service == 'openai_gpt4':
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            cost = ((input_tokens / 1000) * self.openai_gpt4_input_cost_per_1k_tokens +
                   (output_tokens / 1000) * self.openai_gpt4_output_cost_per_1k_tokens)
        elif service == 'openai_gpt35':
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            cost = ((input_tokens / 1000) * self.openai_gpt35_input_cost_per_1k_tokens +
                   (output_tokens / 1000) * self.openai_gpt35_output_cost_per_1k_tokens)
                   
        elif service == 'gemini_flash':
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            cost = ((input_tokens / 1000) * self.gemini_flash_input_cost_per_1k_tokens +
                   (output_tokens / 1000) * self.gemini_flash_output_cost_per_1k_tokens)
        
        return round(cost, 6)
    
    def is_quality_acceptable(self, quality_score: float, completeness_score: float, 
                            accuracy_score: float) -> bool:
        """Check if quality metrics meet thresholds."""
        return (quality_score >= self.min_quality_score and
                completeness_score >= self.min_completeness_score and
                accuracy_score >= self.min_accuracy_score)
    
    def is_efficiency_acceptable(self, cache_hit_rate: float, response_time: float) -> bool:
        """Check if efficiency metrics meet thresholds."""
        return (cache_hit_rate >= self.target_cache_hit_rate and
                response_time <= self.max_response_time_seconds)
