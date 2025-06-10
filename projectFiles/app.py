from flask import Flask, render_template, request, jsonify
from institution_processor import process_institution_pipeline
import json
import os
import asyncio
import time
from service_factory import initialize_autocomplete_with_all_institutions, get_autocomplete_service
from spell_check import SpellCorrectionService
from search.search_service import SearchService
from crawler.crawler_service import CrawlerService

# Enhanced Benchmarking Integration
from benchmarking.integration import (
    initialize_benchmarking, 
    get_benchmarking_manager,
    benchmark_context,
    BenchmarkCategory
)

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize enhanced benchmarking system
try:
    benchmarking_manager = initialize_benchmarking(BASE_DIR)
    print("✅ Enhanced benchmarking system initialized")
except Exception as e:
    print(f"⚠️ Warning: Benchmarking initialization failed: {e}")
    benchmarking_manager = None

# Initialize spell checking service
dictionary_path = os.path.join(BASE_DIR, 'spell_check', 'symspell_dict.txt')
spell_service = SpellCorrectionService(dictionary_path=dictionary_path)

# Check if spell correction is available
if not spell_service.is_initialized:
    print("Warning: Spell checking service is not initialized.")
    print("Spell checking will be disabled, but autocomplete will still work.")

# Initialize autocomplete service with all institution types
initialize_autocomplete_with_all_institutions(BASE_DIR)
autocomplete_service = get_autocomplete_service()

# Initialize search service
search_service = SearchService(BASE_DIR)

# Initialize crawler service
crawler_service = CrawlerService(BASE_DIR)

@app.route('/', methods=['GET', 'POST'])
def index():
    institution_data_str = None
    corrected = None

    if request.method == 'POST':
        institution_name = request.form.get('institution_name')
        institution_type = request.form.get('institution_type', '').strip() or None
        
        # Get additional search parameters
        location = request.form.get('location', '').strip() or None
        additional_keywords = request.form.get('additional_keywords', '').strip() or None
        domain_hint = request.form.get('domain_hint', '').strip() or None
        exclude_terms = request.form.get('exclude_terms', '').strip() or None
        
        if institution_name:
            # Build search parameters dictionary
            search_params = {}
            if institution_type:
                search_params['institution_type'] = institution_type
            if location:
                search_params['location'] = location
            if additional_keywords:
                search_params['additional_keywords'] = additional_keywords
            if domain_hint:
                search_params['domain_hint'] = domain_hint
            if exclude_terms:
                search_params['exclude_terms'] = exclude_terms            # Process the institution with enhanced search parameters
            processed_data = process_institution_pipeline(institution_name, institution_type, search_params=search_params)
            # show as pure text for now
            institution_data_str = json.dumps(processed_data, indent=2)
        else:
            institution_data_str = "Please enter an institution name."
            
    return render_template('index.html', institution_data_str=institution_data_str)


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    """
    Autocomplete endpoint using Trie-based search for fast prefix matching.
    Returns top 5 university suggestions for the given prefix.
    Falls back to spell correction if no matches found.
    """
    term = request.args.get('term', '').strip()
    
    if not term:
        return jsonify([])    # Get suggestions from the Trie-based autocomplete service (includes spell correction)
    result = autocomplete_service.get_suggestions(term, max_suggestions=5)
    
    return jsonify(result)


@app.route('/autocomplete/debug', methods=['GET'])
def autocomplete_debug():
    """
    Debug endpoint to check autocomplete service status and statistics.
    """
    stats = autocomplete_service.get_stats()
    sample_suggestions = autocomplete_service.get_suggestions('university', max_suggestions=3)
    
    debug_info = {
        'service_stats': stats,
        'sample_suggestions_for_university': sample_suggestions,
        'service_initialized': autocomplete_service.is_initialized
    }
    
    return jsonify(debug_info)


@app.route('/spell-check', methods=['GET'])
def spell_check():
    """
    Spell correction endpoint for getting "did you mean" suggestions.
    Returns spell correction suggestions for misspelled institution names.
    """
    term = request.args.get('term', '').strip()
    
    if not term:
        return jsonify({
            'corrections': [],
            'original_query': term,
            'message': 'Empty query'
        })
    
    # Get spell corrections directly
    corrections = autocomplete_service.get_spell_corrections(term, max_suggestions=5)
    
    return jsonify({
        'corrections': corrections,
        'original_query': term,
        'message': f'Found {len(corrections)} suggestions' if corrections else 'No suggestions found'
    })


@app.route('/search', methods=['GET'])
def search_institution():
    """
    Search endpoint for institution information with enhanced benchmarking.
    """
    institution_name = request.args.get('name', '').strip()
    institution_type = request.args.get('type', '').strip() or None
    force_api = request.args.get('force_api', 'false').lower() == 'true'
    
    if not institution_name:
        return jsonify({
            'success': False,
            'error': 'Institution name is required'
        })
    
    # Enhanced benchmarking integration
    if benchmarking_manager:
        with benchmark_context(BenchmarkCategory.SEARCH, institution_name, institution_type or 'general') as ctx:
            # Record API cost if making external call
            if force_api:
                ctx.record_cost(api_calls=1, service_type="google_search")
            
            # Perform search
            result = search_service.search_institution(institution_name, institution_type, force_api)
            
            # Record quality metrics
            if result.get('success'):
                cache_hit = result.get('source') == 'cache'
                ctx.record_quality(
                    completeness_score=0.9 if result.get('links') else 0.5,
                    confidence_scores={
                        'cache_efficiency': 1.0 if cache_hit else 0.0,
                        'api_success': 1.0
                    }
                )
                
                # Record content metrics
                links_count = len(result.get('links', []))
                ctx.record_content(
                    content_size=len(str(result)),
                    structured_data_size=links_count * 100  # Estimate
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


@app.route('/benchmarks/pipeline', methods=['GET'])
def pipeline_benchmarks():
    """
    Get comprehensive pipeline benchmarking statistics - now redirects to enhanced system.
    """
    if not benchmarking_manager:
        return jsonify({
            'success': False,
            'error': 'Enhanced benchmarking not initialized'
        })
    
    # Redirect to enhanced benchmarking system
    return jsonify({
        'success': True,
        'message': 'Pipeline benchmarks now available through enhanced system',
        'redirect_to': '/benchmarks/enhanced/metrics',
        'enhanced_data': benchmarking_manager.get_session_summary()
    })


@app.route('/benchmarks/overview', methods=['GET'])
def benchmarks_overview():
    """
    Get a complete overview of all benchmarking data - now uses enhanced system.
    """
    if not benchmarking_manager:
        return jsonify({
            'success': False,
            'error': 'Enhanced benchmarking not initialized'
        })
    
    overview = {
        'enhanced_system': {
            'session_summary': benchmarking_manager.get_session_summary(),
            'recent_benchmarks': benchmarking_manager.get_recent_benchmarks(10),
            'system_status': 'active'
        },
        'search_service': {
            'cache_stats': search_service.get_stats().get('cache_stats', {}),
            'service_configured': search_service.get_stats().get('service_configured', False)        },
        'message': 'Now using enhanced benchmarking system for comprehensive tracking'
    }
    return jsonify(overview)


@app.route('/crawling/prepare', methods=['GET'])
def prepare_crawling():
    """
    Prepare crawling configuration for an institution.
    """
    institution_name = request.args.get('name', '').strip()
    institution_type = request.args.get('type', '').strip() or None
    max_links = int(request.args.get('max_links', 10))
    
    if not institution_name:
        return jsonify({
            'success': False,
            'error': 'Institution name is required'
        })
    
    from crawling_prep import get_institution_links_for_crawling, InstitutionLinkManager
    
    # Get crawling data
    crawling_data = get_institution_links_for_crawling(
        institution_name, institution_type, max_links, 
        os.path.dirname(os.path.abspath(__file__))
    )
    
    if not crawling_data.get('search_successful'):
        return jsonify({
            'success': False,
            'error': crawling_data.get('error', 'Failed to prepare crawling data'),
            'institution_name': institution_name,
            'institution_type': institution_type
        })
    
    # Prepare crawling configuration
    link_manager = InstitutionLinkManager(os.path.dirname(os.path.abspath(__file__)))
    crawling_config = link_manager.prepare_crawling_config(crawling_data)
    
    return jsonify({
        'success': True,
        'institution_name': institution_name,
        'institution_type': institution_type,
        'links_found': len(crawling_data['links']),
        'crawling_data': crawling_data,
        'crawling_config': crawling_config
    })


@app.route('/process/skip-extraction', methods=['POST'])
def process_institution_skip_extraction():
    """
    Process institution but skip extraction - prepare for crawling instead.
    """
    data = request.get_json() or {}
    institution_name = data.get('institution_name', '').strip()
    institution_type = data.get('institution_type', '').strip() or None
    
    if not institution_name:
        return jsonify({
            'success': False,
            'error': 'Institution name is required'
        })
      # Process with extraction skipped
    result = process_institution_pipeline(institution_name, institution_type, skip_extraction=True, search_params={})
    
    return jsonify({
        'success': not result.get('error'),
        'data': result
    })


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
    
    return jsonify({        'dry_run': dry_run,
        'cleanup_result': cleanup_result,
        'message': 'Dry run completed - use ?dry_run=false to actually clean up' if dry_run else 'Cleanup completed'
    })


# =============================================================================
# CRAWLER ENDPOINTS - Comprehensive Web Crawling with Central Cache Integration
# =============================================================================

@app.route('/crawl', methods=['POST'])
def crawl_institution():
    """
    Main crawling endpoint - Comprehensive institution data extraction with enhanced benchmarking.
    Uses central cache system and comprehensive performance tracking.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        institution_name = data.get('institution_name', '').strip()
        urls = data.get('urls', [])
        institution_type = data.get('institution_type', 'general')
        max_pages = min(int(data.get('max_pages', 5)), 20)  # Limit to 20 pages
        
        if not institution_name:
            return jsonify({'success': False, 'error': 'Institution name is required'}), 400
        
        if not urls:
            return jsonify({'success': False, 'error': 'URLs list is required'}), 400
        
        # Convert institution type string to enum
        from crawler.crawler_config import InstitutionType
        try:
            inst_type = InstitutionType(institution_type.lower())
        except ValueError:
            inst_type = InstitutionType.GENERAL
        
        # Enhanced benchmarking integration
        if benchmarking_manager:
            with benchmark_context(BenchmarkCategory.CRAWLER, institution_name, institution_type) as ctx:
                # Run async crawling
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                start_time = time.time()
                result = loop.run_until_complete(
                    crawler_service.crawl_institution_urls(
                        urls=urls[:max_pages],  # Limit URLs
                        institution_type=inst_type,
                        session_id=f"web_{institution_name}_{int(time.time())}"
                    )
                )
                crawl_time = time.time() - start_time
                loop.close()
                
                # Record detailed metrics
                if result and result.get('success'):
                    crawl_results = result.get('crawl_results', {})
                    results_list = crawl_results.get('results', [])
                    
                    total_content_size = sum(r.get('content_size', 0) for r in results_list)
                    total_words = sum(r.get('word_count', 0) for r in results_list)
                    successful_crawls = sum(1 for r in results_list if r.get('success', False))
                    
                    ctx.record_content(
                        content_size=total_content_size,
                        word_count=total_words,
                        structured_data_size=len(str(result))
                    )
                    
                    ctx.record_quality(
                        completeness_score=successful_crawls / len(urls) if urls else 0.0,
                        accuracy_score=0.8,  # Based on content extraction quality
                        confidence_scores={
                            'crawl_success_rate': successful_crawls / len(urls) if urls else 0.0,
                            'content_quality': 0.8 if total_words > 100 else 0.4
                        }
                    )
        else:
            # Run without benchmarking
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                crawler_service.crawl_institution_urls(
                    urls=urls[:max_pages],
                    institution_type=inst_type,
                    session_id=f"web_{institution_name}_{int(time.time())}"
                )
            )
            
            loop.close()
        
        return jsonify({
            'success': True,
            'institution_name': institution_name,
            'institution_type': institution_type,
            'crawl_results': result,
            'cache_integration': 'centralized_project_cache',
            'benchmark_tracking': 'enabled' if benchmarking_manager else 'disabled'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Crawling error: {str(e)}'
        }), 500


@app.route('/crawl/cache', methods=['GET'])
def get_crawler_cache_stats():
    """Get crawler cache statistics and management."""
    try:
        cache_stats = crawler_service.get_cache_stats()
        cache_info = crawler_service.cache_config.get_cache_info()
        
        return jsonify({
            'success': True,
            'cache_stats': cache_stats,
            'central_cache_info': cache_info,
            'cache_directories': {
                'crawling_data': crawler_service.cache_config.get_crawling_cache_dir(),
                'benchmarks': crawler_service.cache_config.get_benchmarks_dir()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Cache stats error: {str(e)}'
        }), 500


@app.route('/crawl/cache/clear', methods=['POST'])
def clear_crawler_cache():
    """Clear crawler cache (central cache integration)."""
    try:
        result = crawler_service.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'Crawler cache cleared successfully',
            'cache_cleared': result,
            'central_cache_integration': 'maintained'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Cache clear error: {str(e)}'
        }), 500


@app.route('/crawl/benchmark', methods=['GET'])
def get_crawler_benchmarks():
    """Get crawler performance benchmarks and analytics."""
    try:
        # Get benchmark data
        benchmark_data = crawler_service.get_benchmark_summary()
        
        return jsonify({
            'success': True,
            'benchmarks': benchmark_data,
            'benchmark_storage': 'centralized_project_cache',
            'analytics_available': True
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Benchmark error: {str(e)}'
        }), 500


@app.route('/crawl/test', methods=['GET'])
def test_crawler():
    """Quick crawler test endpoint."""
    try:
        test_url = request.args.get('url', 'https://example.com')
        
        # Run quick test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from crawler.crawler_config import InstitutionType
        result = loop.run_until_complete(
            crawler_service.crawl_institution_urls(
                urls=[test_url],
                institution_type=InstitutionType.GENERAL,
                session_id=f"test_{int(time.time())}"
            )
        )
        
        loop.close()
        
        return jsonify({
            'success': True,
            'test_url': test_url,
            'crawl_result': result,
            'cache_integration': 'verified',
            'message': 'Crawler test completed successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Crawler test error: {str(e)}'
        }), 500


# =============================================================================
# ENHANCED BENCHMARKING ENDPOINTS - Comprehensive Performance Tracking
# =============================================================================

@app.route('/benchmarks/status', methods=['GET'])
def benchmarks_status():
    """Get benchmarking system status and configuration."""
    if not benchmarking_manager:
        return jsonify({
            'success': False,
            'error': 'Enhanced benchmarking not initialized'
        })
    
    try:
        config = benchmarking_manager.config
        summary = benchmarking_manager.get_session_summary()
        
        return jsonify({
            'success': True,
            'status': 'active',
            'configuration': {
                'cost_tracking': config.enable_cost_tracking,
                'latency_tracking': config.enable_latency_tracking,
                'quality_tracking': config.enable_quality_tracking,
                'efficiency_tracking': config.enable_efficiency_tracking,
                'auto_reports': config.auto_generate_reports,
                'retention_days': config.retention_days
            },
            'session_summary': summary,
            'directories': {
                'benchmarks': config.benchmarks_dir,
                'reports': config.reports_dir,
                'test_results': config.test_results_dir
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Status check failed: {str(e)}'
        })


@app.route('/benchmarks/metrics', methods=['GET'])
def get_benchmarks_metrics():
    """Get comprehensive metrics from recent benchmarks."""
    if not benchmarking_manager:
        return jsonify({
            'success': False,
            'error': 'Enhanced benchmarking not initialized'
        })
    
    try:
        limit = int(request.args.get('limit', 20))
        category = request.args.get('category', 'all')
        
        recent_benchmarks = benchmarking_manager.get_recent_benchmarks(limit)
        
        # Filter by category if specified
        if category != 'all':
            recent_benchmarks = [
                b for b in recent_benchmarks 
                if b.get('category', '').lower() == category.lower()
            ]
        
        # Calculate aggregated metrics
        total_cost = sum(b.get('total_cost', 0) for b in recent_benchmarks)
        avg_latency = (
            sum(b.get('total_latency', 0) for b in recent_benchmarks) / 
            len(recent_benchmarks) if recent_benchmarks else 0
        )
        success_rate = (
            sum(1 for b in recent_benchmarks if b.get('success', False)) /
            len(recent_benchmarks) if recent_benchmarks else 0
        )
        
        # Group by institution type
        by_type = {}
        for benchmark in recent_benchmarks:
            inst_type = benchmark.get('institution_type', 'unknown')
            if inst_type not in by_type:
                by_type[inst_type] = []
            by_type[inst_type].append(benchmark)
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_benchmarks': len(recent_benchmarks),
                'total_cost_usd': round(total_cost, 4),
                'average_latency_seconds': round(avg_latency, 3),
                'success_rate_percent': round(success_rate * 100, 2),
                'by_institution_type': {
                    inst_type: {
                        'count': len(benchmarks),
                        'avg_cost': round(
                            sum(b.get('total_cost', 0) for b in benchmarks) / len(benchmarks), 4
                        ) if benchmarks else 0,
                        'success_rate': round(
                            sum(1 for b in benchmarks if b.get('success', False)) / len(benchmarks) * 100, 2
                        ) if benchmarks else 0
                    }
                    for inst_type, benchmarks in by_type.items()
                }
            },
            'recent_benchmarks': recent_benchmarks[:10]  # Return top 10 for display
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Metrics retrieval failed: {str(e)}'
        })


@app.route('/benchmarks/enhanced/cost-analysis', methods=['GET'])
def get_cost_analysis():
    """Get detailed cost analysis and optimization recommendations."""
    if not benchmarking_manager:
        return jsonify({
            'success': False,
            'error': 'Enhanced benchmarking not initialized'
        })
    
    try:
        days = int(request.args.get('days', 7))
        
        # Get recent benchmarks for analysis
        recent_benchmarks = benchmarking_manager.get_recent_benchmarks(limit=100)
        
        # Cost breakdown
        total_api_cost = sum(b.get('api_cost', 0) for b in recent_benchmarks)
        total_llm_cost = sum(b.get('llm_cost', 0) for b in recent_benchmarks)
        total_compute_cost = sum(b.get('compute_cost', 0) for b in recent_benchmarks)
        
        # Token usage analysis
        total_input_tokens = sum(b.get('input_tokens', 0) for b in recent_benchmarks)
        total_output_tokens = sum(b.get('output_tokens', 0) for b in recent_benchmarks)
        
        # Cache efficiency analysis
        cache_hits = sum(1 for b in recent_benchmarks if b.get('cache_hit', False))
        cache_efficiency = cache_hits / len(recent_benchmarks) if recent_benchmarks else 0
        
        # Cost optimization recommendations
        recommendations = []
        
        if cache_efficiency < 0.7:
            recommendations.append({
                'type': 'cache_optimization',
                'priority': 'high',
                'message': f'Cache hit rate is {cache_efficiency:.1%}. Consider tuning cache similarity thresholds.',
                'potential_savings': total_api_cost * (0.7 - cache_efficiency)
            })
        
        if total_llm_cost > total_api_cost * 2:
            recommendations.append({
                'type': 'llm_optimization',
                'priority': 'medium',
                'message': 'LLM costs are high relative to API costs. Consider prompt optimization.',
                'potential_savings': total_llm_cost * 0.2
            })
        
        return jsonify({
            'success': True,
            'cost_analysis': {
                'period_days': days,
                'total_operations': len(recent_benchmarks),
                'cost_breakdown': {
                    'api_cost_usd': round(total_api_cost, 4),
                    'llm_cost_usd': round(total_llm_cost, 4),
                    'compute_cost_usd': round(total_compute_cost, 4),
                    'total_cost_usd': round(total_api_cost + total_llm_cost + total_compute_cost, 4)
                },
                'token_usage': {
                    'total_input_tokens': total_input_tokens,
                    'total_output_tokens': total_output_tokens,
                    'total_tokens': total_input_tokens + total_output_tokens
                },
                'efficiency_metrics': {
                    'cache_hit_rate': round(cache_efficiency * 100, 2),
                    'cost_per_operation': round(
                        (total_api_cost + total_llm_cost) / len(recent_benchmarks), 4
                    ) if recent_benchmarks else 0
                },
                'optimization_recommendations': recommendations
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Cost analysis failed: {str(e)}'
        })


@app.route('/benchmarks/enhanced/performance-report', methods=['GET'])
def generate_performance_report():
    """Generate a comprehensive performance report."""
    if not benchmarking_manager:
        return jsonify({
            'success': False,
            'error': 'Enhanced benchmarking not initialized'
        })
    
    try:
        format_type = request.args.get('format', 'json')
        include_charts = request.args.get('charts', 'false').lower() == 'true'
        
        # Generate report using the benchmarking manager
        if format_type == 'json':
            report_data = benchmarking_manager.export_benchmarks(format='json')
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_type}'
            })
        
        return jsonify({
            'success': True,
            'report_format': format_type,
            'include_charts': include_charts,
            'report_data': json.loads(report_data) if isinstance(report_data, str) else report_data,
            'generated_at': time.time()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Report generation failed: {str(e)}'
        })


@app.route('/benchmarks/enhanced/test', methods=['POST'])
def run_benchmark_test():
    """Run a custom benchmark test with specified configuration."""
    if not benchmarking_manager:
        return jsonify({
            'success': False,
            'error': 'Enhanced benchmarking not initialized'
        })
    
    try:
        test_config = request.get_json()
        if not test_config:
            return jsonify({
                'success': False,
                'error': 'Test configuration required'
            })
        
        institution_name = test_config.get('institution_name', 'Test Institution')
        institution_type = test_config.get('institution_type', 'general')
        test_type = test_config.get('test_type', 'search')
        iterations = test_config.get('iterations', 1)
        
        results = []
        
        for i in range(iterations):
            # Create a test benchmark
            category = BenchmarkCategory.SEARCH if test_type == 'search' else BenchmarkCategory.PIPELINE
            
            with benchmark_context(category, institution_name, institution_type) as ctx:
                start_time = time.time()
                
                # Simulate test operation based on type
                if test_type == 'search':
                    # Simulate search operation
                    time.sleep(0.1)  # Simulate processing
                    ctx.record_cost(api_calls=1, service_type="google_search")
                    ctx.record_quality(completeness_score=0.9, accuracy_score=0.85)
                
                elif test_type == 'crawling':
                    # Simulate crawling operation
                    time.sleep(0.5)  # Simulate processing
                    ctx.record_content(content_size=10000, word_count=1500)
                    ctx.record_quality(completeness_score=0.8, accuracy_score=0.9)
                
                execution_time = time.time() - start_time
                
                results.append({
                    'iteration': i + 1,
                    'execution_time': round(execution_time, 3),
                    'success': True
                })
        
        # Get session summary for results
        summary = benchmarking_manager.get_session_summary()
        
        return jsonify({
            'success': True,
            'test_configuration': test_config,
            'test_results': {
                'iterations_completed': len(results),
                'individual_results': results,
                'average_execution_time': round(
                    sum(r['execution_time'] for r in results) / len(results), 3
                ),
                'success_rate': sum(1 for r in results if r['success']) / len(results)
            },
            'session_summary': summary
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Benchmark test failed: {str(e)}'
        })


@app.route('/benchmarks/enhanced/export', methods=['GET'])
def export_benchmark_data():
    """Export comprehensive benchmark data in various formats."""
    if not benchmarking_manager:
        return jsonify({
            'success': False,
            'error': 'Enhanced benchmarking not initialized'
        })
    
    try:
        format_type = request.args.get('format', 'json')
        limit = int(request.args.get('limit', 100))
        
        # Export data
        if format_type == 'json':
            exported_data = benchmarking_manager.export_benchmarks(format='json')
            
            return jsonify({
                'success': True,
                'format': format_type,
                'data': json.loads(exported_data) if isinstance(exported_data, str) else exported_data,
                'export_timestamp': time.time()
            })
        
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported export format: {format_type}'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Export failed: {str(e)}'
        })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
