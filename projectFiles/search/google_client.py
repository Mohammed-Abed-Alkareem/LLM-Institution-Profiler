"""
Google Custom Search JSON API client for institution search.
"""
import requests
import time
from typing import Dict, List, Optional
from .config import (
    GOOGLE_SEARCH_API_KEY, GOOGLE_CSE_ID, DEFAULT_SEARCH_RESULTS,
    REQUEST_TIMEOUT, MAX_REQUESTS_PER_MINUTE
)
from .rate_limiter import RateLimiter


class GoogleSearchClient:
    """Client for Google Custom Search JSON API."""
    
    def __init__(self, api_key: str = None, cse_id: str = None):
        self.api_key = api_key or GOOGLE_SEARCH_API_KEY
        self.cse_id = cse_id or GOOGLE_CSE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.rate_limiter = RateLimiter(max_requests=MAX_REQUESTS_PER_MINUTE, time_window=60)
        
        if not self.api_key or not self.cse_id:
            raise ValueError("Google API key and CSE ID must be provided")
    
    def search(self, query: str, num_results: int = DEFAULT_SEARCH_RESULTS, 
               site_restrict: str = None) -> Dict:
        """
        Perform a Google Custom Search.
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 10 per request)
            site_restrict: Optional site restriction (e.g., 'site:edu')
            
        Returns:
            Dictionary containing search results and metadata
        """
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': query,
            'num': min(num_results, 10),  # API limit is 10 per request
            'fields': 'items(title,link,snippet,displayLink),searchInformation(totalResults,searchTime)'
        }
        
        if site_restrict:
            params['q'] = f"{query} {site_restrict}"
        
        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Record the request for rate limiting
            self.rate_limiter.record_request()
            
            return {
                'success': True,
                'query': query,
                'results': data.get('items', []),
                'total_results': data.get('searchInformation', {}).get('totalResults', '0'),
                'search_time': data.get('searchInformation', {}).get('searchTime', 0),
                'timestamp': time.time()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'timestamp': time.time()
            }
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'error': f"Unexpected error: {str(e)}",
                'timestamp': time.time()
            }
    def search_institution(self, institution_name: str, institution_type: str = None, 
                          search_params: Dict = None) -> Dict:
        """
        Search specifically for institution information with enhanced query building.
        
        Args:
            institution_name: Name of the institution
            institution_type: Optional type filter (university, hospital, bank, etc.)
            search_params: Additional search parameters (location, keywords, etc.)
            
        Returns:
            Dictionary containing search results
        """
        
        from .search_enhancer import SearchQueryEnhancer
        
        # Enhance the query with additional parameters
        enhancer = SearchQueryEnhancer()
        
        # Prepare search parameters
        if not search_params:
            search_params = {}
        if institution_type:
            search_params['institution_type'] = institution_type
        
        enhanced_query = enhancer.enhance_query(institution_name, search_params)
        strategy = enhanced_query['search_strategy']
        
        # Get formatted query for API
        query, site_restriction = enhancer.format_search_query_for_api(enhanced_query)
        
        results = []
        
        # Try official sites first if strategy recommends it
        if strategy['use_official_sites_first'] and enhanced_query['site_restrictions']:
            for site_restrict in enhanced_query['site_restrictions'][:2]:  # Try top 2 site restrictions
                official_result = self.search(
                    enhanced_query['primary_query'],
                    num_results=strategy['max_results_per_query'] // 2,
                    site_restrict=site_restrict
                )
                
                if official_result['success'] and official_result.get('results'):
                    results.extend(official_result['results'])
                    
                    # If we have enough good results, return them
                    if len(results) >= 5:
                        official_result['results'] = results[:10]
                        official_result['query'] = query
                        official_result['enhancement_info'] = {
                            'enhanced': enhanced_query['enhancement_applied'],
                            'detected_type': enhanced_query['detected_type'],
                            'strategy_used': 'official_sites'
                        }
                        return official_result
        
        # Try the primary enhanced query
        primary_result = self.search(query, num_results=strategy['max_results_per_query'])
        
        if primary_result['success']:
            if strategy['combine_results'] and results:
                # Combine with previous results
                combined_results = results + primary_result.get('results', [])
                primary_result['results'] = combined_results[:10]
            
            primary_result['enhancement_info'] = {
                'enhanced': enhanced_query['enhancement_applied'],
                'detected_type': enhanced_query['detected_type'],
                'strategy_used': 'enhanced_primary'
            }
            return primary_result
        
        # Fallback to query variations if primary fails
        if strategy['fallback_to_general'] and enhanced_query['query_variations']:
            for variation in enhanced_query['query_variations'][:3]:  # Try top 3 variations
                fallback_result = self.search(variation, num_results=8)
                if fallback_result['success'] and fallback_result.get('results'):
                    fallback_result['enhancement_info'] = {
                        'enhanced': enhanced_query['enhancement_applied'],
                        'detected_type': enhanced_query['detected_type'],
                        'strategy_used': 'fallback_variation',
                        'variation_used': variation
                    }
                    return fallback_result
        
        # If all else fails, return the primary result even if it failed
        primary_result['enhancement_info'] = {
            'enhanced': enhanced_query['enhancement_applied'],
            'detected_type': enhanced_query['detected_type'],
            'strategy_used': 'failed_enhanced'
        }
        return primary_result
    
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return bool(self.api_key and self.cse_id)
