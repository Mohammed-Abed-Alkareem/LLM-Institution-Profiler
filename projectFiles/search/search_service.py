"""
Main search service that orchestrates all search functionality.
"""
import os
import time
from typing import Dict, List, Optional
from .google_client import GoogleSearchClient
from .cache import SearchCache
from benchmark import ComprehensiveBenchmarkTracker, SearchBenchmark


class SearchService:
    """Main search service with caching and benchmarking."""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.getcwd()
        
        # Use centralized cache configuration
        from cache_config import get_cache_config
        cache_config = get_cache_config(self.base_dir)
        
        # Initialize components with centralized cache paths
        cache_path = cache_config.get_search_cache_dir()
        benchmark_path = cache_config.get_benchmarks_dir()
        self.cache = SearchCache(cache_path)
        self.benchmark_tracker = ComprehensiveBenchmarkTracker(benchmark_path)
        
        # Initialize Google client (may raise ValueError if not configured)
        try:
            self.google_client = GoogleSearchClient()
            self.is_configured = True
        except ValueError as e:
            print(f"Warning: Google Search not configured: {e}")
            self.google_client = None
            self.is_configured = False
    
    def search_institution(self, institution_name: str, institution_type: str = None, 
                          force_api: bool = False) -> Dict:
        """
        Search for institution information with caching and benchmarking.
        
        Args:
            institution_name: Name of the institution
            institution_type: Optional type of institution
            force_api: Force API call even if cache hit exists
            
        Returns:
            Dictionary containing search results and metadata
        """
        start_time = time.time()
        
        # Prepare search parameters
        search_params = {'institution_type': institution_type} if institution_type else None
        
        # Try cache first (unless forced to use API)
        cached_result = None
        source = 'api'
        cache_similarity = 0.0
        
        if not force_api:
            cached_result = self.cache.get(institution_name, search_params)
            if cached_result:
                source = 'similar_cache' if cached_result.get('cache_similarity', 0) > 0 else 'cache'
                cache_similarity = cached_result.get('cache_similarity', 0)
        
        # If cache hit, return cached result
        if cached_result and not force_api:
            response_time = time.time() - start_time
            
            # Record benchmark
            benchmark = SearchBenchmark(
                query=institution_name,
                timestamp=start_time,
                response_time=response_time,
                success=cached_result.get('success', True),
                source=source,
                num_results=len(cached_result.get('results', [])),
                total_results=cached_result.get('total_results', '0'),
                cache_similarity=cache_similarity,
                institution_type=institution_type
            )
            self.benchmark_tracker.record_search(benchmark)
            
            return {
                **cached_result,
                'cache_hit': True,
                'source': source,
                'response_time': response_time
            }
        
        # Make API call
        if not self.is_configured:
            error_result = {
                'success': False,
                'error': 'Google Search API not configured',
                'cache_hit': False,
                'source': 'error'
            }
            
            # Record failed benchmark
            benchmark = SearchBenchmark(
                query=institution_name,
                timestamp=start_time,
                response_time=time.time() - start_time,
                success=False,
                source='error',
                num_results=0,
                total_results='0',
                error='API not configured',
                institution_type=institution_type
            )
            self.benchmark_tracker.record_search(benchmark)
            
            return error_result
        
        # Make the API call
        api_result = self.google_client.search_institution(institution_name, institution_type)
        response_time = time.time() - start_time
        
        # Cache the result if successful
        if api_result.get('success', False):
            self.cache.put(institution_name, api_result, search_params)
        
        # Record benchmark
        benchmark = SearchBenchmark(
            query=institution_name,
            timestamp=start_time,
            response_time=response_time,
            success=api_result.get('success', False),
            source='api',
            num_results=len(api_result.get('results', [])),
            total_results=api_result.get('total_results', '0'),
            api_search_time=api_result.get('search_time', 0),
            error=api_result.get('error'),
            institution_type=institution_type
        )
        self.benchmark_tracker.record_search(benchmark)
        
        return {
            **api_result,
            'cache_hit': False,
            'source': 'api',
            'response_time': response_time
        }
    
    def get_search_links(self, institution_name: str, institution_type: str = None, 
                        max_links: int = 10) -> List[str]:
        """
        Get just the links from a search (useful for crawling).
        
        Args:
            institution_name: Name of the institution
            institution_type: Optional type of institution
            max_links: Maximum number of links to return
            
        Returns:
            List of URLs
        """
        result = self.search_institution(institution_name, institution_type)
        
        if not result.get('success', False):
            return []
        
        links = []
        for item in result.get('results', []):
            link = item.get('link')
            if link and link not in links:
                links.append(link)
                if len(links) >= max_links:
                    break
        
        return links
    
    def clear_cache(self) -> Dict:
        """Clear expired cache entries."""
        cleared_count = self.cache.clear_expired()
        return {
            'cleared_entries': cleared_count,
            'message': f'Cleared {cleared_count} expired cache entries'
        }
    
    def get_stats(self) -> Dict:
        """Get comprehensive service statistics."""
        cache_stats = self.cache.get_stats()
        session_stats = self.benchmark_tracker.get_session_stats()
        all_time_stats = self.benchmark_tracker.get_all_time_stats()
        
        return {
            'service_configured': self.is_configured,
            'cache_stats': cache_stats,
            'session_stats': session_stats,
            'all_time_stats': all_time_stats
        }
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent search history."""
        return self.benchmark_tracker.get_recent_searches(limit)
    
    def analyze_performance(self) -> Dict:
        """Get performance analysis by institution type."""
        return self.benchmark_tracker.analyze_performance_by_type()
    
    def get_cached_queries(self) -> List[Dict]:
        """Get list of all cached queries."""
        return self.cache.list_cached_queries()
    
    def is_ready(self) -> bool:
        """Check if the service is ready to make searches."""
        return self.is_configured
