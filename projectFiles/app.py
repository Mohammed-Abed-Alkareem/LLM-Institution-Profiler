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
        if institution_name:
            # Process the institution name
            processed_data = process_institution_pipeline(institution_name)
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
