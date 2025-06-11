# -*- coding: utf-8 -*-
"""
Search-related routes for the Institution Profiler Flask application.
Handles search operations, performance tracking, and cache management.
"""
import time
from flask import request, jsonify
from benchmarking.integration import benchmark_context, BenchmarkCategory


def register_search_routes(app, services):
    """Register search-related routes."""
    benchmarking_manager = services.get('benchmarking')
    search_service = services['search']

    @app.route('/search', methods=['GET'])
    def search_institution():
        """
        Search endpoint for institution information with benchmarking.
        """
        institution_name = request.args.get('name', '').strip()
        institution_type = request.args.get('type', '').strip() or None
        force_api = request.args.get('force_api', 'false').lower() == 'true'
        
        if not institution_name:
            return jsonify({
                'success': False,
                'error': 'Institution name is required'
            })
          # Benchmarking integration
        if benchmarking_manager:
            with benchmark_context(BenchmarkCategory.SEARCH, institution_name, institution_type or 'general') as ctx:
                # Perform search
                result = search_service.search_institution(institution_name, institution_type, force_api)
                
                # Record cost metrics based on actual API usage
                api_calls_made = result.get('api_calls_made', 0)
                if api_calls_made > 0:
                    ctx.record_cost(api_calls=api_calls_made, service_type="google_search")
                
                # Record latency metrics with actual timings
                if 'api_call_time' in result:
                    ctx.record_latency(
                        operation_type="search",
                        duration=result.get('response_time', 0),
                        network_time=result.get('api_call_time', 0)
                    )
                
                # Record quality metrics based on search results
                if result.get('success'):
                    cache_hit = result.get('source') == 'cache'
                    results_count = result.get('results_count', 0)
                    total_results = result.get('total_results_numeric', 0)
                    
                    # Calculate quality scores based on actual data
                    completeness_score = min(results_count / 10.0, 1.0) if results_count else 0.0
                    coverage_score = min(total_results / 100000, 1.0) if total_results else 0.0
                    quality_score = (completeness_score + coverage_score) / 2.0
                    
                    ctx.record_quality(
                        completeness_score=quality_score,
                        confidence_scores={
                            'cache_efficiency': 1.0 if cache_hit else 0.0,
                            'api_success': 1.0,
                            'results_quality': result.get('results_quality_score', 0.0),
                            'search_coverage': result.get('search_coverage_score', 0.0)
                        }
                    )
                    
                    # Record content metrics based on actual search results
                    content_size = len(str(result.get('results', [])))
                    links_count = len(result.get('results', []))
                    ctx.record_content(
                        content_size=content_size,
                        structured_data_size=links_count * 100,  # Estimate based on links
                        word_count=content_size // 6  # Rough estimate of word count
                    )
        else:
            result = search_service.search_institution(institution_name, institution_type, force_api)
        
        return jsonify(result)

    @app.route('/search/links', methods=['GET'])
    def get_search_links():
        """
        Get links for an institution (useful for crawling).
        """
        institution_name = request.args.get('name', '').strip()
        institution_type = request.args.get('type', '').strip() or None
        max_links = int(request.args.get('max_links', 10))
        
        if not institution_name:
            return jsonify({
                'success': False,
                'error': 'Institution name is required'
            })
        
        links = search_service.get_search_links(institution_name, institution_type, max_links)
        return jsonify({
            'success': True,
            'institution_name': institution_name,
            'institution_type': institution_type,
            'links': links,
            'count': len(links)
        })

    @app.route('/search/stats', methods=['GET'])
    def search_stats():
        """
        Get search service statistics and performance metrics.
        """
        stats = search_service.get_stats()
        return jsonify(stats)

    @app.route('/search/recent', methods=['GET'])
    def recent_searches():
        """
        Get recent search history.
        """
        limit = int(request.args.get('limit', 10))
        recent = search_service.get_recent_searches(limit)
        return jsonify({
            'recent_searches': recent,
            'count': len(recent)
        })

    @app.route('/search/performance', methods=['GET'])
    def search_performance():
        """
        Get performance analysis by institution type.
        """
        analysis = search_service.analyze_performance()
        return jsonify(analysis)

    @app.route('/search/cache', methods=['GET'])
    def search_cache_info():
        """
        Get cached queries information.
        """
        cached_queries = search_service.get_cached_queries()
        return jsonify({
            'cached_queries': cached_queries,
            'count': len(cached_queries)
        })

    @app.route('/search/cache/clear', methods=['POST'])
    def clear_search_cache():
        """
        Clear expired cache entries.
        """
        result = search_service.clear_cache()
        return jsonify(result)
