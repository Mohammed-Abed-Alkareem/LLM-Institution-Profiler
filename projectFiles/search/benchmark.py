"""
Benchmarking system for tracking search performance and costs.
"""
import json
import os
import time
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class SearchBenchmark:
    """Data class for search benchmark results."""
    query: str
    timestamp: float
    response_time: float
    success: bool
    source: str  # 'cache', 'api', 'similar_cache'
    num_results: int
    total_results: str
    api_search_time: float = 0.0
    error: Optional[str] = None
    cache_similarity: float = 0.0
    institution_type: Optional[str] = None


class BenchmarkTracker:
    """Tracks and analyzes search performance benchmarks."""
    
    def __init__(self, benchmark_dir: str):
        self.benchmark_dir = benchmark_dir
        self.ensure_benchmark_dir()
        self.current_session_file = os.path.join(
            benchmark_dir, 
            f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        self.all_benchmarks_file = os.path.join(benchmark_dir, 'all_benchmarks.json')
        self.session_benchmarks = []
    
    def ensure_benchmark_dir(self):
        """Ensure benchmark directory exists."""
        if not os.path.exists(self.benchmark_dir):
            os.makedirs(self.benchmark_dir)
    
    def record_search(self, benchmark: SearchBenchmark):
        """Record a search benchmark."""
        self.session_benchmarks.append(benchmark)
        
        # Save to session file
        self._save_session_benchmarks()
        
        # Append to all benchmarks file
        self._append_to_all_benchmarks(benchmark)
    
    def _save_session_benchmarks(self):
        """Save current session benchmarks."""
        try:
            with open(self.current_session_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(b) for b in self.session_benchmarks], f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save session benchmarks: {e}")
    
    def _append_to_all_benchmarks(self, benchmark: SearchBenchmark):
        """Append benchmark to all benchmarks file."""
        try:
            # Load existing benchmarks
            all_benchmarks = []
            if os.path.exists(self.all_benchmarks_file):
                with open(self.all_benchmarks_file, 'r', encoding='utf-8') as f:
                    all_benchmarks = json.load(f)
            
            # Append new benchmark
            all_benchmarks.append(asdict(benchmark))
            
            # Save back
            with open(self.all_benchmarks_file, 'w', encoding='utf-8') as f:
                json.dump(all_benchmarks, f, indent=2)
                
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not update all benchmarks: {e}")
    
    def get_session_stats(self) -> Dict:
        """Get statistics for the current session."""
        if not self.session_benchmarks:
            return {}
        
        total_searches = len(self.session_benchmarks)
        successful_searches = sum(1 for b in self.session_benchmarks if b.success)
        cache_hits = sum(1 for b in self.session_benchmarks if b.source == 'cache')
        similar_cache_hits = sum(1 for b in self.session_benchmarks if b.source == 'similar_cache')
        api_calls = sum(1 for b in self.session_benchmarks if b.source == 'api')
        
        response_times = [b.response_time for b in self.session_benchmarks if b.success]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        api_search_times = [b.api_search_time for b in self.session_benchmarks if b.source == 'api' and b.success]
        avg_api_time = sum(api_search_times) / len(api_search_times) if api_search_times else 0
        
        return {
            'session_file': os.path.basename(self.current_session_file),
            'total_searches': total_searches,
            'successful_searches': successful_searches,
            'success_rate_percent': round((successful_searches / total_searches) * 100, 2) if total_searches > 0 else 0,
            'cache_hits': cache_hits,
            'similar_cache_hits': similar_cache_hits,
            'api_calls': api_calls,
            'cache_hit_rate_percent': round(((cache_hits + similar_cache_hits) / total_searches) * 100, 2) if total_searches > 0 else 0,
            'avg_response_time_ms': round(avg_response_time * 1000, 2),
            'avg_api_search_time_ms': round(avg_api_time * 1000, 2) if avg_api_time > 0 else 0,
            'total_session_time': round(sum(b.response_time for b in self.session_benchmarks), 2)
        }
    
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
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent search benchmarks."""
        recent = sorted(self.session_benchmarks, key=lambda b: b.timestamp, reverse=True)[:limit]
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
