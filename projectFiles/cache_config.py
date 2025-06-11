"""
Centralized cache configuration for the Institution Profiler project.
All caching and benchmarking data goes into a single project_cache folder.
"""
import os
from typing import Dict


class CacheConfig:
    """Centralized configuration for all caching in the project."""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.project_cache_dir = os.path.join(base_dir, 'project_cache')
        
        # Define all cache subdirectories
        self.cache_dirs = {
            'search_cache': os.path.join(self.project_cache_dir, 'search_results'),
            'benchmarks': os.path.join(self.project_cache_dir, 'benchmarks'),
            'crawling_cache': os.path.join(self.project_cache_dir, 'crawling_data'),
            'rag_cache': os.path.join(self.project_cache_dir, 'rag_embeddings'),
            'llm_cache': os.path.join(self.project_cache_dir, 'llm_responses')
        }
        
        # Ensure all directories exist
        self._ensure_cache_directories()
    
    def _ensure_cache_directories(self):
        """Create all cache directories if they don't exist."""
        # Create main project_cache directory
        if not os.path.exists(self.project_cache_dir):
            os.makedirs(self.project_cache_dir)
        
        # Create all subdirectories
        for cache_type, cache_path in self.cache_dirs.items():
            if not os.path.exists(cache_path):
                os.makedirs(cache_path)
    
    def get_cache_dir(self, cache_type: str) -> str:
        """Get the path for a specific cache type."""
        if cache_type not in self.cache_dirs:
            raise ValueError(f"Unknown cache type: {cache_type}. Available: {list(self.cache_dirs.keys())}")
        return self.cache_dirs[cache_type]
    
    def get_search_cache_dir(self) -> str:
        """Get the search cache directory."""
        return self.cache_dirs['search_cache']
    
    def get_benchmarks_dir(self) -> str:
        """Get the benchmarks directory."""
        return self.cache_dirs['benchmarks']
    
    def get_crawling_cache_dir(self) -> str:
        """Get the crawling cache directory."""
        return self.cache_dirs['crawling_cache']
    
    def get_rag_cache_dir(self) -> str:
        """Get the RAG cache directory."""
        return self.cache_dirs['rag_cache']
    
    def get_llm_cache_dir(self) -> str:
        """Get the LLM cache directory."""
        return self.cache_dirs['llm_cache']
    
    def get_cache_info(self) -> Dict:
        """Get information about all cache directories."""
        info = {
            'project_cache_root': self.project_cache_dir,
            'cache_directories': {}
        }
        
        for cache_type, cache_path in self.cache_dirs.items():
            cache_exists = os.path.exists(cache_path)
            file_count = 0
            total_size = 0
            
            if cache_exists:
                try:
                    files = os.listdir(cache_path)
                    file_count = len(files)
                    
                    for file in files:
                        file_path = os.path.join(cache_path, file)
                        if os.path.isfile(file_path):
                            total_size += os.path.getsize(file_path)
                except (OSError, PermissionError):
                    pass
            
            info['cache_directories'][cache_type] = {
                'path': cache_path,
                'exists': cache_exists,
                'file_count': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        
        return info
    
    def cleanup_old_caches(self, dry_run: bool = True) -> Dict:
        """
        Clean up old cache directories outside project_cache.
        If dry_run=True, just returns what would be cleaned up.
        """
        cleanup_info = {
            'old_directories_found': [],
            'would_remove': [],
            'removed': []
        }
        
        # Look for old cache directories
        old_dirs_to_check = [
            os.path.join(self.base_dir, 'search_cache'),
            os.path.join(self.base_dir, 'benchmarks'),
            os.path.join(os.path.dirname(self.base_dir), 'search_cache'),
            os.path.join(os.path.dirname(self.base_dir), 'benchmarks')
        ]
        
        for old_dir in old_dirs_to_check:
            if os.path.exists(old_dir) and old_dir != self.project_cache_dir:
                cleanup_info['old_directories_found'].append(old_dir)
                
                if dry_run:
                    cleanup_info['would_remove'].append(old_dir)
                else:
                    try:
                        import shutil
                        shutil.rmtree(old_dir)
                        cleanup_info['removed'].append(old_dir)
                    except Exception as e:
                        cleanup_info['errors'] = cleanup_info.get('errors', [])
                        cleanup_info['errors'].append(f"Failed to remove {old_dir}: {e}")
        
        return cleanup_info


# Global cache configuration instance
_cache_config = None


def get_cache_config(base_dir: str = None) -> CacheConfig:
    """Get the global cache configuration instance."""
    global _cache_config
    
    if _cache_config is None:
        if base_dir is None:
            # Default to the projectFiles directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
        _cache_config = CacheConfig(base_dir)
    
    return _cache_config


def reset_cache_config():
    """Reset the global cache configuration (useful for testing)."""
    global _cache_config
    _cache_config = None
