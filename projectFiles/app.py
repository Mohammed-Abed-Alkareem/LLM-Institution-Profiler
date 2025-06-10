from flask import Flask, render_template, request, jsonify
from institution_processor import process_institution_pipeline
import json
import os
from service_factory import initialize_autocomplete_with_all_institutions, get_autocomplete_service
from spell_check import SpellCorrectionService
from search.search_service import SearchService

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    Search endpoint for institution information.
    """
    institution_name = request.args.get('name', '').strip()
    institution_type = request.args.get('type', '').strip() or None
    force_api = request.args.get('force_api', 'false').lower() == 'true'
    
    if not institution_name:
        return jsonify({
            'success': False,
            'error': 'Institution name is required'
        })
    
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
    Get comprehensive pipeline benchmarking statistics.
    """
    from benchmark import ComprehensiveBenchmarkTracker
    from cache_config import get_cache_config
    
    cache_config = get_cache_config(BASE_DIR)
    benchmark_tracker = ComprehensiveBenchmarkTracker(cache_config.get_benchmarks_dir())
    
    stats = {
        'pipeline_stats': benchmark_tracker.get_pipeline_stats(),
        'comprehensive_stats': benchmark_tracker.get_comprehensive_stats(),
        'recent_pipelines': benchmark_tracker.get_recent_pipelines(10)
    }
    return jsonify(stats)


@app.route('/benchmarks/overview', methods=['GET'])
def benchmarks_overview():
    """
    Get a complete overview of all benchmarking data.
    """
    from benchmark import ComprehensiveBenchmarkTracker
    from cache_config import get_cache_config
    
    cache_config = get_cache_config(BASE_DIR)
    benchmark_tracker = ComprehensiveBenchmarkTracker(cache_config.get_benchmarks_dir())
    
    overview = {
        'search_only': {
            'session_stats': search_service.get_stats().get('session_stats', {}),
            'all_time_stats': search_service.get_stats().get('all_time_stats', {}),
            'recent_searches': search_service.get_recent_searches(5)
        },
        'pipeline_comprehensive': {
            'pipeline_stats': benchmark_tracker.get_pipeline_stats(),
            'comprehensive_stats': benchmark_tracker.get_comprehensive_stats(),
            'recent_pipelines': benchmark_tracker.get_recent_pipelines(5)
        }
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
    
    return jsonify({
        'dry_run': dry_run,
        'cleanup_result': cleanup_result,
        'message': 'Dry run completed - use ?dry_run=false to actually clean up' if dry_run else 'Cleanup completed'
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
