# -*- coding: utf-8 -*-
"""
Cache and utility routes for the Institution Profiler Flask application.
Handles cache management and general utility endpoints.
"""
import os
from flask import request, jsonify


def register_utility_routes(app, services):
    """Register utility and cache management routes."""
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @app.route('/cache/info', methods=['GET'])
    def cache_info():
        """
        Get information about all cache directories and usage.
        """
        from cache_config import get_cache_config
        
        cache_config = get_cache_config(BASE_DIR)
        cache_info = cache_config.get_cache_info()
        
        return jsonify({
            'cache_structure': cache_info,
            'total_cache_size_mb': sum(
                dir_info['total_size_mb'] 
                for dir_info in cache_info['cache_directories'].values()
            )
        })

    @app.route('/cache/cleanup', methods=['POST'])
    def cleanup_old_caches():
        """
        Clean up old cache directories outside the centralized project_cache.
        Use ?dry_run=false to actually perform the cleanup.
        """
        from cache_config import get_cache_config
        
        dry_run = request.args.get('dry_run', 'true').lower() != 'false'
        cache_config = get_cache_config(BASE_DIR)
        
        cleanup_result = cache_config.cleanup_old_caches(dry_run=dry_run)
        
        return jsonify({
            'dry_run': dry_run,
            'cleanup_result': cleanup_result,
            'message': 'Dry run completed - use ?dry_run=false to actually clean up' if dry_run else 'Cleanup completed'
        })
