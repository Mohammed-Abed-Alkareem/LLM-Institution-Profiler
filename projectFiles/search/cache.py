"""
Caching system for search results with similarity matching.
"""
import json
import os
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from .config import CACHE_EXPIRY_DAYS, CACHE_SIMILARITY_THRESHOLD


class SearchCache:
    """Cache for storing and retrieving search results."""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self.ensure_cache_dir()
        self.metadata_file = os.path.join(cache_dir, 'metadata.json')
        self.metadata = self._load_metadata()
    
    def ensure_cache_dir(self):
        """Ensure cache directory exists."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _load_metadata(self) -> Dict:
        """Load cache metadata."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {'queries': {}, 'stats': {'hits': 0, 'misses': 0, 'similar_hits': 0}}
    
    def _save_metadata(self):
        """Save cache metadata."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save cache metadata: {e}")
    
    def _generate_cache_key(self, query: str, params: Dict = None) -> str:
        """Generate a cache key for the query."""
        key_data = f"{query.lower().strip()}"
        if params:
            key_data += json.dumps(params, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> str:
        """Get the file path for a cache key."""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cached entry has expired."""
        expiry_time = timestamp + (CACHE_EXPIRY_DAYS * 24 * 3600)
        return time.time() > expiry_time
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries."""
        return SequenceMatcher(None, query1.lower().strip(), query2.lower().strip()).ratio()
    
    def get(self, query: str, params: Dict = None) -> Optional[Dict]:
        """
        Get cached results for a query.
        
        Args:
            query: Search query
            params: Additional search parameters
            
        Returns:
            Cached results if found and not expired, None otherwise
        """
        cache_key = self._generate_cache_key(query, params)
        cache_file = self._get_cache_file_path(cache_key)
        
        # Check direct cache hit
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                if not self._is_expired(cached_data.get('timestamp', 0)):
                    self.metadata['stats']['hits'] += 1
                    self._save_metadata()
                    return cached_data
                else:
                    # Remove expired cache
                    os.remove(cache_file)
                    if cache_key in self.metadata['queries']:
                        del self.metadata['queries'][cache_key]
            except (json.JSONDecodeError, IOError):
                # Remove corrupted cache file
                if os.path.exists(cache_file):
                    os.remove(cache_file)
        
        # Check for similar queries
        similar_result = self._find_similar_cached_query(query, params)
        if similar_result:
            self.metadata['stats']['similar_hits'] += 1
            self._save_metadata()
            return similar_result
        
        self.metadata['stats']['misses'] += 1
        self._save_metadata()
        return None
    
    def _find_similar_cached_query(self, query: str, params: Dict = None) -> Optional[Dict]:
        """Find a similar cached query."""
        best_similarity = 0
        best_result = None
        
        for cached_key, cached_info in self.metadata['queries'].items():
            cached_query = cached_info.get('query', '')
            cached_params = cached_info.get('params', {})
            
            # Check if params match (if provided)
            if params and cached_params != params:
                continue
            
            similarity = self._calculate_similarity(query, cached_query)
            
            if similarity >= CACHE_SIMILARITY_THRESHOLD and similarity > best_similarity:
                cache_file = self._get_cache_file_path(cached_key)
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cached_data = json.load(f)
                        
                        if not self._is_expired(cached_data.get('timestamp', 0)):
                            best_similarity = similarity
                            best_result = cached_data
                    except (json.JSONDecodeError, IOError):
                        continue
        
        return best_result
    
    def put(self, query: str, results: Dict, params: Dict = None):
        """
        Cache search results.
        
        Args:
            query: Search query
            results: Search results to cache
            params: Additional search parameters
        """
        cache_key = self._generate_cache_key(query, params)
        cache_file = self._get_cache_file_path(cache_key)
        
        # Add metadata to results
        cache_data = {
            'query': query,
            'params': params or {},
            'cached_at': time.time(),
            'timestamp': results.get('timestamp', time.time()),
            **results
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            # Update metadata
            self.metadata['queries'][cache_key] = {
                'query': query,
                'params': params or {},
                'cached_at': time.time()
            }
            self._save_metadata()
            
        except IOError as e:
            print(f"Warning: Could not cache results: {e}")
    
    def clear_expired(self) -> int:
        """
        Clear expired cache entries.
        
        Returns:
            Number of entries cleared
        """
        cleared_count = 0
        expired_keys = []
        
        for cache_key, cache_info in self.metadata['queries'].items():
            cache_file = self._get_cache_file_path(cache_key)
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    
                    if self._is_expired(cached_data.get('timestamp', 0)):
                        os.remove(cache_file)
                        expired_keys.append(cache_key)
                        cleared_count += 1
                except (json.JSONDecodeError, IOError):
                    # Remove corrupted files
                    if os.path.exists(cache_file):
                        os.remove(cache_file)
                        expired_keys.append(cache_key)
                        cleared_count += 1
            else:
                # Remove metadata for missing files
                expired_keys.append(cache_key)
        
        # Remove expired keys from metadata
        for key in expired_keys:
            if key in self.metadata['queries']:
                del self.metadata['queries'][key]
        
        if expired_keys:
            self._save_metadata()
        
        return cleared_count
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = sum(self.metadata['stats'].values())
        hit_rate = (self.metadata['stats']['hits'] / total_requests * 100) if total_requests > 0 else 0
        similar_hit_rate = (self.metadata['stats']['similar_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_cached_queries': len(self.metadata['queries']),
            'cache_hits': self.metadata['stats']['hits'],
            'similar_hits': self.metadata['stats']['similar_hits'],
            'cache_misses': self.metadata['stats']['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'similar_hit_rate_percent': round(similar_hit_rate, 2),
            'total_requests': total_requests
        }
    
    def list_cached_queries(self) -> List[Dict]:
        """List all cached queries."""
        queries = []
        for cache_key, cache_info in self.metadata['queries'].items():
            queries.append({
                'cache_key': cache_key,
                'query': cache_info.get('query', ''),
                'params': cache_info.get('params', {}),
                'cached_at': cache_info.get('cached_at', 0),
                'cached_at_formatted': datetime.fromtimestamp(cache_info.get('cached_at', 0)).strftime('%Y-%m-%d %H:%M:%S')
            })
        return sorted(queries, key=lambda x: x['cached_at'], reverse=True)
