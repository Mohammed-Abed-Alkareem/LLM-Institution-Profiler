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
    
    def search_institution(self, institution_name: str, institution_type: str = None) -> Dict:
        """
        Search specifically for institution information.
        
        Args:
            institution_name: Name of the institution
            institution_type: Optional type filter (university, hospital, bank, etc.)
            
        Returns:
            Dictionary containing search results
        """
        # Build targeted query
        query_parts = [institution_name]
        
        if institution_type:
            query_parts.append(institution_type)
        
        # Add relevant keywords for institutions
        if institution_type in ['university', 'college', 'school']:
            query_parts.extend(['education', 'academic'])
        elif institution_type in ['hospital', 'clinic', 'medical']:
            query_parts.extend(['healthcare', 'medical'])
        elif institution_type in ['bank', 'financial']:
            query_parts.extend(['finance', 'banking'])
        
        query = ' '.join(query_parts)
        
        # Try official sites first
        official_result = self.search(
            query, 
            num_results=5,
            site_restrict='site:edu OR site:org OR site:gov'
        )
        
        # If we have good official results, return them
        if official_result['success'] and len(official_result.get('results', [])) >= 3:
            return official_result
        
        # Otherwise, do a general search
        general_result = self.search(query, num_results=10)
        
        # Combine results if we had some official ones
        if official_result['success'] and official_result.get('results'):
            combined_results = official_result['results'] + general_result.get('results', [])
            general_result['results'] = combined_results[:10]  # Limit to 10 total
        
        return general_result
    
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return bool(self.api_key and self.cse_id)
