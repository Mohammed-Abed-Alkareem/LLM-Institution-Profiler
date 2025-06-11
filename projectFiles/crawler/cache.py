"""
Institution Profiler Web Crawler Cache Module

This module provides caching functionality for crawled web content,
integrating with the centralized cache system.
"""

import os
import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class CrawlerCache:
    """
    Cache manager for crawled web content with URL-based caching.
    """
    
    def __init__(self, cache_dir: str):
        """Initialize the crawler cache."""
        self.cache_dir = cache_dir
        self.ensure_cache_directory()
        
        # Cache configuration
        self.default_cache_expiry_days = 7
        self.max_cache_size_mb = 500  # Limit cache size
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'stores': 0,
            'errors': 0
        }
    
    def ensure_cache_directory(self):
        """Ensure the cache directory exists."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _generate_cache_key(self, url: str) -> str:
        """Generate a cache key from a URL."""
        # Use URL hash as cache key
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
        return f"url_{url_hash[:16]}"
    
    def _get_cache_file_path(self, cache_key: str) -> str:
        """Get the full path to a cache file."""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_data: Dict[str, Any], max_age_days: int = None) -> bool:
        """Check if cached data is still valid."""
        if max_age_days is None:
            max_age_days = self.default_cache_expiry_days
        
        cached_time = cache_data.get('cached_at', 0)
        if not cached_time:
            return False
        
        cache_age = time.time() - cached_time
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        return cache_age < max_age_seconds
    
    def get_cached_content(self, url: str, max_age_days: int = None) -> Optional[Dict[str, Any]]:
        """
        Get cached content for a URL if it exists and is valid.
        
        Args:
            url: The URL to look up
            max_age_days: Maximum age of cache in days (uses default if None)
            
        Returns:
            Cached content dictionary or None if not found/expired
        """
        try:
            cache_key = self._generate_cache_key(url)
            cache_file = self._get_cache_file_path(cache_key)
            
            if not os.path.exists(cache_file):
                self.stats['misses'] += 1
                return None
            
            # Load cached data
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is valid
            if not self._is_cache_valid(cache_data, max_age_days):
                # Cache expired, remove it
                try:
                    os.remove(cache_file)
                except OSError:
                    pass
                self.stats['misses'] += 1
                return None
            
            # Return the cached content
            self.stats['hits'] += 1
            return cache_data.get('content')
        
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Error reading cache for {url}: {e}")
            return None
    
    def cache_content(self, url: str, content: Dict[str, Any]) -> bool:
        """
        Cache content for a URL.
        
        Args:
            url: The URL to cache
            content: The content dictionary to cache
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(url)
            cache_file = self._get_cache_file_path(cache_key)
            
            # Prepare cache data
            cache_data = {
                'url': url,
                'cached_at': time.time(),
                'cache_key': cache_key,
                'content': content
            }
            
            # Write to cache file
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            self.stats['stores'] += 1
            return True
        
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Error caching content for {url}: {e}")
            return False
    
    def invalidate_cache(self, url: str) -> bool:
        """
        Remove cached content for a specific URL.
        
        Args:
            url: The URL to invalidate
            
        Returns:
            True if cache was removed, False if not found or error
        """
        try:
            cache_key = self._generate_cache_key(url)
            cache_file = self._get_cache_file_path(cache_key)
            
            if os.path.exists(cache_file):
                os.remove(cache_file)
                return True
            return False
        
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Error invalidating cache for {url}: {e}")
            return False
    
    def clear_old_cache(self, older_than_days: int = 7) -> Dict[str, Any]:
        """
        Clear cache entries older than specified days.
        
        Args:
            older_than_days: Remove cache older than this many days
            
        Returns:
            Dictionary with cleanup statistics
        """
        removed_count = 0
        error_count = 0
        total_size_removed = 0
        
        try:
            current_time = time.time()
            max_age_seconds = older_than_days * 24 * 60 * 60
            
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                
                file_path = os.path.join(self.cache_dir, filename)
                
                try:
                    # Check file modification time
                    file_mtime = os.path.getmtime(file_path)
                    file_age = current_time - file_mtime
                    
                    if file_age > max_age_seconds:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        removed_count += 1
                        total_size_removed += file_size
                
                except OSError as e:
                    error_count += 1
                    print(f"Error processing cache file {filename}: {e}")
        
        except Exception as e:
            print(f"Error during cache cleanup: {e}")
        
        return {
            'removed_files': removed_count,
            'errors': error_count,
            'size_freed_mb': round(total_size_removed / (1024 * 1024), 2),
            'cleanup_date': datetime.now().isoformat()
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            # Count cache files and calculate total size
            cache_files = []
            total_size = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        file_size = os.path.getsize(file_path)
                        file_mtime = os.path.getmtime(file_path)
                        cache_files.append({
                            'filename': filename,
                            'size_bytes': file_size,
                            'modified_at': datetime.fromtimestamp(file_mtime).isoformat()
                        })
                        total_size += file_size
                    except OSError:
                        continue
            
            # Calculate cache efficiency
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'cache_directory': self.cache_dir,
                'total_files': len(cache_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'hit_rate_percent': round(hit_rate, 2),
                'session_stats': self.stats.copy(),
                'oldest_cache': min([f['modified_at'] for f in cache_files]) if cache_files else None,
                'newest_cache': max([f['modified_at'] for f in cache_files]) if cache_files else None,
                'files_details': cache_files[:10] if len(cache_files) <= 10 else cache_files[:10] + [{'note': f'... and {len(cache_files) - 10} more files'}]
            }
        
        except Exception as e:
            return {
                'cache_directory': self.cache_dir,
                'error': str(e),
                'session_stats': self.stats.copy()
            }
    
    def list_cached_urls(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List cached URLs with metadata.
        
        Args:
            limit: Maximum number of URLs to return
            
        Returns:
            List of cached URL information
        """
        cached_urls = []
        
        try:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                
                if len(cached_urls) >= limit:
                    break
                
                file_path = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    cached_urls.append({
                        'url': cache_data.get('url', 'Unknown'),
                        'cached_at': datetime.fromtimestamp(cache_data.get('cached_at', 0)).isoformat(),
                        'cache_key': cache_data.get('cache_key', filename.replace('.json', '')),
                        'content_title': cache_data.get('content', {}).get('title', 'No title'),
                        'success': cache_data.get('content', {}).get('success', False),
                        'file_size_kb': round(os.path.getsize(file_path) / 1024, 2)
                    })
                
                except (json.JSONDecodeError, OSError):
                    continue
        
        except Exception as e:
            print(f"Error listing cached URLs: {e}")
        
        return cached_urls
    
    def get_cache_info_for_urls(self, urls: List[str]) -> Dict[str, Any]:
        """
        Get cache information for specific URLs.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            Dictionary mapping URLs to their cache status
        """
        url_cache_info = {}
        
        for url in urls:
            cache_key = self._generate_cache_key(url)
            cache_file = self._get_cache_file_path(cache_key)
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    url_cache_info[url] = {
                        'cached': True,
                        'cached_at': datetime.fromtimestamp(cache_data.get('cached_at', 0)).isoformat(),
                        'valid': self._is_cache_valid(cache_data),
                        'file_size_kb': round(os.path.getsize(cache_file) / 1024, 2)
                    }
                except:
                    url_cache_info[url] = {
                        'cached': True,
                        'cached_at': 'Unknown',
                        'valid': False,
                        'error': 'Could not read cache file'
                    }
            else:
                url_cache_info[url] = {
                    'cached': False,
                    'cached_at': None,
                    'valid': False
                }
        
        return url_cache_info
