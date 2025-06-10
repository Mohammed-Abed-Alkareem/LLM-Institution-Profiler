"""
Comprehensive benchmarking system for tracking the entire institution processing pipeline.
"""
import json
import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field


@dataclass
class SearchBenchmark:
    """Data class for search phase benchmark results."""
    query: str
    timestamp: float
    response_time: float
    success: bool
    source: str  # 'cache', 'api', 'similar_cache', 'llm_fallback'
    num_results: int
    total_results: str
    api_search_time: float = 0.0
    error: Optional[str] = None
    cache_similarity: float = 0.0
    institution_type: Optional[str] = None


@dataclass
class CrawlingBenchmark:
    """Data class for web crawling phase benchmark results."""
    institution_name: str
    timestamp: float
    total_crawl_time: float
    urls_crawled: int
    urls_failed: int
    total_html_size: int  # bytes
    optimized_content_size: int  # bytes after cleaning
    pages_per_domain: Dict[str, int] = field(default_factory=dict)
    average_page_size: float = 0.0
    crawl_errors: List[str] = field(default_factory=list)
    content_types_found: Dict[str, int] = field(default_factory=dict)


@dataclass
class RAGBenchmark:
    """Data class for RAG processing phase benchmark results."""
    institution_name: str
    timestamp: float
    processing_time: float
    original_content_size: int  # bytes
    num_chunks: int
    chunk_sizes: List[int] = field(default_factory=list)
    average_chunk_size: float = 0.0
    overlap_ratio: float = 0.0
    relevance_scores: List[float] = field(default_factory=list)
    chunks_filtered: int = 0
    embedding_time: float = 0.0
    similarity_search_time: float = 0.0


@dataclass
class LLMBenchmark:
    """Data class for LLM extraction phase benchmark results."""
    institution_name: str
    timestamp: float
    extraction_time: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_estimate: float  # USD
    model_used: str
    prompt_type: str  # e.g., 'structured_extraction', 'validation'
    success: bool
    extraction_fields: int  # number of fields successfully extracted
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    validation_passes: int = 0
    error: Optional[str] = None


@dataclass
class ComprehensiveBenchmark:
    """Data class for complete pipeline benchmark results."""
    institution_name: str
    institution_type: Optional[str]
    pipeline_start: float
    pipeline_end: float
    total_pipeline_time: float
    success: bool
    
    # Phase benchmarks
    search_benchmark: Optional[SearchBenchmark] = None
    crawling_benchmark: Optional[CrawlingBenchmark] = None
    rag_benchmark: Optional[RAGBenchmark] = None
    llm_benchmark: Optional[LLMBenchmark] = None
    
    # Pipeline-level metrics
    data_quality_score: float = 0.0
    completeness_score: float = 0.0  # percentage of target fields extracted
    total_cost_estimate: float = 0.0  # USD
    cache_efficiency: float = 0.0  # percentage of cached vs fresh data
    
    # Error tracking
    phase_errors: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


class ComprehensiveBenchmarkTracker:
    """Tracks and analyzes performance across the entire institution processing pipeline."""
    
    def __init__(self, benchmark_dir: str):
        self.benchmark_dir = benchmark_dir
        self.ensure_benchmark_dir()
        
        # Session files for different tracking types
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.search_session_file = os.path.join(benchmark_dir, f"search_session_{session_id}.json")
        self.pipeline_session_file = os.path.join(benchmark_dir, f"pipeline_session_{session_id}.json")
        self.comprehensive_file = os.path.join(benchmark_dir, 'comprehensive_benchmarks.json')
        self.all_benchmarks_file = os.path.join(benchmark_dir, 'all_benchmarks.json')
        
        # In-memory tracking
        self.search_benchmarks = []
        self.pipeline_benchmarks = []
        self.active_pipelines = {}  # track ongoing pipeline executions
    
    def ensure_benchmark_dir(self):
        """Ensure benchmark directory exists."""
        if not os.path.exists(self.benchmark_dir):
            os.makedirs(self.benchmark_dir)
    
    # === Pipeline Tracking Methods ===
    
    def start_pipeline(self, institution_name: str, institution_type: str = None) -> str:
        """
        Start tracking a new pipeline execution.
        Returns a pipeline_id for tracking.
        """
        pipeline_id = f"{institution_name}_{int(time.time() * 1000)}"
        
        self.active_pipelines[pipeline_id] = ComprehensiveBenchmark(
            institution_name=institution_name,
            institution_type=institution_type,
            pipeline_start=time.time(),
            pipeline_end=0.0,
            total_pipeline_time=0.0,
            success=False
        )
        
        return pipeline_id
    
    def record_search_phase(self, pipeline_id: str, search_benchmark: SearchBenchmark):
        """Record search phase results for a pipeline."""
        if pipeline_id in self.active_pipelines:
            self.active_pipelines[pipeline_id].search_benchmark = search_benchmark
        
        # Also record for search-specific tracking
        self.record_search(search_benchmark)
    
    def record_crawling_phase(self, pipeline_id: str, crawling_benchmark: CrawlingBenchmark):
        """Record crawling phase results for a pipeline."""
        if pipeline_id in self.active_pipelines:
            self.active_pipelines[pipeline_id].crawling_benchmark = crawling_benchmark
    
    def record_rag_phase(self, pipeline_id: str, rag_benchmark: RAGBenchmark):
        """Record RAG processing phase results for a pipeline."""
        if pipeline_id in self.active_pipelines:
            self.active_pipelines[pipeline_id].rag_benchmark = rag_benchmark
    
    def record_llm_phase(self, pipeline_id: str, llm_benchmark: LLMBenchmark):
        """Record LLM extraction phase results for a pipeline."""
        if pipeline_id in self.active_pipelines:
            pipeline = self.active_pipelines[pipeline_id]
            pipeline.llm_benchmark = llm_benchmark
            pipeline.total_cost_estimate += llm_benchmark.cost_estimate
    
    def add_pipeline_error(self, pipeline_id: str, phase: str, error: str):
        """Add an error to a specific pipeline phase."""
        if pipeline_id in self.active_pipelines:
            self.active_pipelines[pipeline_id].phase_errors[phase] = error
    
    def add_pipeline_warning(self, pipeline_id: str, warning: str):
        """Add a warning to a pipeline."""
        if pipeline_id in self.active_pipelines:
            self.active_pipelines[pipeline_id].warnings.append(warning)
    
    def complete_pipeline(self, pipeline_id: str, success: bool, 
                         data_quality_score: float = 0.0, 
                         completeness_score: float = 0.0) -> ComprehensiveBenchmark:
        """
        Complete a pipeline and calculate final metrics.
        Returns the completed benchmark for immediate use.
        """
        if pipeline_id not in self.active_pipelines:
            return None
        
        pipeline = self.active_pipelines[pipeline_id]
        pipeline.pipeline_end = time.time()
        pipeline.total_pipeline_time = pipeline.pipeline_end - pipeline.pipeline_start
        pipeline.success = success
        pipeline.data_quality_score = data_quality_score
        pipeline.completeness_score = completeness_score
        
        # Calculate cache efficiency
        if pipeline.search_benchmark:
            pipeline.cache_efficiency = 1.0 if pipeline.search_benchmark.source in ['cache', 'similar_cache'] else 0.0
        
        # Add to completed pipelines
        self.pipeline_benchmarks.append(pipeline)
        
        # Save to files
        self._save_pipeline_benchmarks()
        self._append_to_comprehensive(pipeline)
        
        # Clean up active tracking
        del self.active_pipelines[pipeline_id]
        
        return pipeline
    
    # === Search-Only Tracking (Backward Compatibility) ===
    
    def record_search(self, benchmark: SearchBenchmark):
        """Record a search benchmark (for backward compatibility)."""
        self.search_benchmarks.append(benchmark)
        self._save_search_benchmarks()
        self._append_to_all_benchmarks(benchmark)
    
    def _save_search_benchmarks(self):
        """Save current session search benchmarks."""
        try:
            with open(self.search_session_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(b) for b in self.search_benchmarks], f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save search benchmarks: {e}")
    
    def _save_pipeline_benchmarks(self):
        """Save current session pipeline benchmarks."""
        try:
            with open(self.pipeline_session_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(b) for b in self.pipeline_benchmarks], f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save pipeline benchmarks: {e}")
    
    def _append_to_all_benchmarks(self, benchmark: SearchBenchmark):
        """Append search benchmark to all benchmarks file (legacy)."""
        try:
            all_benchmarks = []
            if os.path.exists(self.all_benchmarks_file):
                with open(self.all_benchmarks_file, 'r', encoding='utf-8') as f:
                    all_benchmarks = json.load(f)
            
            all_benchmarks.append(asdict(benchmark))
            
            with open(self.all_benchmarks_file, 'w', encoding='utf-8') as f:
                json.dump(all_benchmarks, f, indent=2)
                
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not update all benchmarks: {e}")
    
    def _append_to_comprehensive(self, pipeline: ComprehensiveBenchmark):
        """Append pipeline benchmark to comprehensive benchmarks file."""
        try:
            comprehensive = []
            if os.path.exists(self.comprehensive_file):
                with open(self.comprehensive_file, 'r', encoding='utf-8') as f:
                    comprehensive = json.load(f)
            
            comprehensive.append(asdict(pipeline))
            
            with open(self.comprehensive_file, 'w', encoding='utf-8') as f:
                json.dump(comprehensive, f, indent=2)
                
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not update comprehensive benchmarks: {e}")
    
    # === Analytics and Reporting ===
    
    def get_session_stats(self) -> Dict:
        """Get statistics for the current session (search-only for backward compatibility)."""
        if not self.search_benchmarks:
            return {}
        
        total_searches = len(self.search_benchmarks)
        successful_searches = sum(1 for b in self.search_benchmarks if b.success)
        cache_hits = sum(1 for b in self.search_benchmarks if b.source == 'cache')
        similar_cache_hits = sum(1 for b in self.search_benchmarks if b.source == 'similar_cache')
        api_calls = sum(1 for b in self.search_benchmarks if b.source == 'api')
        
        response_times = [b.response_time for b in self.search_benchmarks if b.success]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        api_search_times = [b.api_search_time for b in self.search_benchmarks if b.source == 'api' and b.success]
        avg_api_time = sum(api_search_times) / len(api_search_times) if api_search_times else 0
        
        return {
            'session_file': os.path.basename(self.search_session_file),
            'total_searches': total_searches,
            'successful_searches': successful_searches,
            'success_rate_percent': round((successful_searches / total_searches) * 100, 2) if total_searches > 0 else 0,
            'cache_hits': cache_hits,
            'similar_cache_hits': similar_cache_hits,
            'api_calls': api_calls,
            'cache_hit_rate_percent': round(((cache_hits + similar_cache_hits) / total_searches) * 100, 2) if total_searches > 0 else 0,
            'avg_response_time_ms': round(avg_response_time * 1000, 2),
            'avg_api_search_time_ms': round(avg_api_time * 1000, 2) if avg_api_time > 0 else 0,
            'total_session_time': round(sum(b.response_time for b in self.search_benchmarks), 2)
        }
    
    def get_pipeline_stats(self) -> Dict:
        """Get statistics for completed pipeline executions."""
        if not self.pipeline_benchmarks:
            return {}
        
        total_pipelines = len(self.pipeline_benchmarks)
        successful_pipelines = sum(1 for p in self.pipeline_benchmarks if p.success)
        
        # Calculate averages
        avg_pipeline_time = sum(p.total_pipeline_time for p in self.pipeline_benchmarks) / total_pipelines
        avg_cost = sum(p.total_cost_estimate for p in self.pipeline_benchmarks) / total_pipelines
        avg_quality = sum(p.data_quality_score for p in self.pipeline_benchmarks) / total_pipelines
        avg_completeness = sum(p.completeness_score for p in self.pipeline_benchmarks) / total_pipelines
        
        # Phase success rates
        search_successes = sum(1 for p in self.pipeline_benchmarks if p.search_benchmark and p.search_benchmark.success)
        crawling_successes = sum(1 for p in self.pipeline_benchmarks if p.crawling_benchmark)
        rag_successes = sum(1 for p in self.pipeline_benchmarks if p.rag_benchmark)
        llm_successes = sum(1 for p in self.pipeline_benchmarks if p.llm_benchmark and p.llm_benchmark.success)
        
        return {
            'session_file': os.path.basename(self.pipeline_session_file),
            'total_pipelines': total_pipelines,
            'successful_pipelines': successful_pipelines,
            'success_rate_percent': round((successful_pipelines / total_pipelines) * 100, 2) if total_pipelines > 0 else 0,
            'avg_pipeline_time_seconds': round(avg_pipeline_time, 2),
            'avg_cost_usd': round(avg_cost, 4),
            'avg_data_quality_score': round(avg_quality, 2),
            'avg_completeness_percent': round(avg_completeness, 2),
            'phase_success_rates': {
                'search_percent': round((search_successes / total_pipelines) * 100, 2) if total_pipelines > 0 else 0,
                'crawling_percent': round((crawling_successes / total_pipelines) * 100, 2) if total_pipelines > 0 else 0,
                'rag_percent': round((rag_successes / total_pipelines) * 100, 2) if total_pipelines > 0 else 0,
                'llm_percent': round((llm_successes / total_pipelines) * 100, 2) if total_pipelines > 0 else 0
            }
        }
    
    def get_comprehensive_stats(self) -> Dict:
        """Get comprehensive statistics from all pipeline executions."""
        try:
            if not os.path.exists(self.comprehensive_file):
                return {}
            
            with open(self.comprehensive_file, 'r', encoding='utf-8') as f:
                all_pipelines = json.load(f)
            
            if not all_pipelines:
                return {}
            
            total_pipelines = len(all_pipelines)
            successful_pipelines = sum(1 for p in all_pipelines if p.get('success', False))
            
            # Cost analysis
            total_cost = sum(p.get('total_cost_estimate', 0) for p in all_pipelines)
            
            # Time analysis
            pipeline_times = [p.get('total_pipeline_time', 0) for p in all_pipelines if p.get('success', False)]
            avg_pipeline_time = sum(pipeline_times) / len(pipeline_times) if pipeline_times else 0
            
            # Quality metrics
            quality_scores = [p.get('data_quality_score', 0) for p in all_pipelines if p.get('success', False)]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            return {
                'total_pipelines_processed': total_pipelines,
                'successful_pipelines': successful_pipelines,
                'overall_success_rate_percent': round((successful_pipelines / total_pipelines) * 100, 2) if total_pipelines > 0 else 0,
                'total_cost_usd': round(total_cost, 4),
                'avg_pipeline_time_seconds': round(avg_pipeline_time, 2),
                'avg_data_quality_score': round(avg_quality, 2),
                'first_pipeline': datetime.fromtimestamp(min(p.get('pipeline_start', 0) for p in all_pipelines)).strftime('%Y-%m-%d %H:%M:%S'),
                'last_pipeline': datetime.fromtimestamp(max(p.get('pipeline_end', 0) for p in all_pipelines)).strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load comprehensive stats: {e}")
            return {}
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent search benchmarks."""
        recent = sorted(self.search_benchmarks, key=lambda b: b.timestamp, reverse=True)[:limit]
        return [
            {
                'query': b.query,
                'timestamp': datetime.fromtimestamp(b.timestamp).strftime('%H:%M:%S'),
                'response_time_ms': round(b.response_time * 1000, 2),
                'source': b.source,
                'success': b.success,
                'num_results': b.num_results,
                'error': b.error
            }
            for b in recent
        ]
    
    def get_recent_pipelines(self, limit: int = 10) -> List[Dict]:
        """Get recent pipeline benchmarks."""
        recent = sorted(self.pipeline_benchmarks, key=lambda p: p.pipeline_start, reverse=True)[:limit]
        return [
            {
                'institution_name': p.institution_name,
                'institution_type': p.institution_type,
                'timestamp': datetime.fromtimestamp(p.pipeline_start).strftime('%H:%M:%S'),
                'total_time_seconds': round(p.total_pipeline_time, 2),
                'success': p.success,
                'data_quality_score': p.data_quality_score,
                'completeness_percent': p.completeness_score,
                'total_cost_usd': round(p.total_cost_estimate, 4),
                'phases_completed': [
                    phase for phase, benchmark in [
                        ('search', p.search_benchmark),
                        ('crawling', p.crawling_benchmark),
                        ('rag', p.rag_benchmark),
                        ('llm', p.llm_benchmark)
                    ] if benchmark is not None
                ]
            }
            for p in recent
        ]
    
    def get_all_time_stats(self) -> Dict:
        """Get all-time statistics from all benchmark files."""
        try:
            if not os.path.exists(self.all_benchmarks_file):
                return {}
            
            with open(self.all_benchmarks_file, 'r', encoding='utf-8') as f:
                all_benchmarks = json.load(f)
            
            if not all_benchmarks:
                return {}
            
            total_searches = len(all_benchmarks)
            successful_searches = sum(1 for b in all_benchmarks if b.get('success', False))
            cache_hits = sum(1 for b in all_benchmarks if b.get('source') == 'cache')
            similar_cache_hits = sum(1 for b in all_benchmarks if b.get('source') == 'similar_cache')
            api_calls = sum(1 for b in all_benchmarks if b.get('source') == 'api')
            
            response_times = [b.get('response_time', 0) for b in all_benchmarks if b.get('success', False)]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Cost estimation (assuming Google Custom Search pricing)
            estimated_cost = api_calls * 0.005  # $5 per 1000 queries
            
            return {
                'total_searches': total_searches,
                'successful_searches': successful_searches,
                'success_rate_percent': round((successful_searches / total_searches) * 100, 2) if total_searches > 0 else 0,
                'cache_hits': cache_hits,
                'similar_cache_hits': similar_cache_hits,
                'api_calls': api_calls,
                'cache_hit_rate_percent': round(((cache_hits + similar_cache_hits) / total_searches) * 100, 2) if total_searches > 0 else 0,
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
                'estimated_cost_usd': round(estimated_cost, 4),
                'first_search': datetime.fromtimestamp(min(b.get('timestamp', 0) for b in all_benchmarks)).strftime('%Y-%m-%d %H:%M:%S'),
                'last_search': datetime.fromtimestamp(max(b.get('timestamp', 0) for b in all_benchmarks)).strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load all-time stats: {e}")
            return {}
    
    def analyze_performance_by_type(self) -> Dict:
        """Analyze performance by institution type."""
        if not os.path.exists(self.all_benchmarks_file):
            return {}
        
        try:
            with open(self.all_benchmarks_file, 'r', encoding='utf-8') as f:
                all_benchmarks = json.load(f)
            
            type_stats = {}
            
            for benchmark in all_benchmarks:
                inst_type = benchmark.get('institution_type', 'unknown')
                if inst_type not in type_stats:
                    type_stats[inst_type] = {
                        'count': 0,
                        'successful': 0,
                        'response_times': [],
                        'api_calls': 0
                    }
                
                type_stats[inst_type]['count'] += 1
                if benchmark.get('success'):
                    type_stats[inst_type]['successful'] += 1
                    type_stats[inst_type]['response_times'].append(benchmark.get('response_time', 0))
                
                if benchmark.get('source') == 'api':
                    type_stats[inst_type]['api_calls'] += 1
            
            # Calculate averages
            result = {}
            for inst_type, stats in type_stats.items():
                avg_time = (sum(stats['response_times']) / len(stats['response_times'])) if stats['response_times'] else 0
                result[inst_type] = {
                    'total_searches': stats['count'],
                    'successful_searches': stats['successful'],
                    'success_rate_percent': round((stats['successful'] / stats['count']) * 100, 2) if stats['count'] > 0 else 0,
                    'avg_response_time_ms': round(avg_time * 1000, 2),
                    'api_calls': stats['api_calls']
                }
            
            return result
            
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not analyze performance by type: {e}")
            return {}
