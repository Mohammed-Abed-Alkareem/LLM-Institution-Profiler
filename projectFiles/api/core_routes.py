# -*- coding: utf-8 -*-
"""
Core routes for the Institution Profiler Flask application.
Handles main functionality, autocomplete, and basic processing.
"""
from flask import render_template, request, jsonify
from institution_processor import process_institution_pipeline
from .json_utils import safe_json_dumps, safe_jsonify


def register_core_routes(app, services):
    """Register core application routes."""
    
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
                    search_params['exclude_terms'] = exclude_terms                # Process the institution with enhanced search parameters
                processed_data = process_institution_pipeline(
                    institution_name, institution_type, search_params=search_params
                )
                # show as pure text for now
                institution_data_str = safe_json_dumps(processed_data, indent=2)
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
            return jsonify([])
        
        # Get suggestions from the Trie-based autocomplete service (includes spell correction)
        result = services['autocomplete'].get_suggestions(term, max_suggestions=5)
        
        return jsonify(result)

    @app.route('/autocomplete/debug', methods=['GET'])
    def autocomplete_debug():
        """
        Debug endpoint to check autocomplete service status and statistics.
        """
        stats = services['autocomplete'].get_stats()
        sample_suggestions = services['autocomplete'].get_suggestions('university', max_suggestions=3)
        
        debug_info = {
            'service_stats': stats,
            'sample_suggestions_for_university': sample_suggestions,
            'service_initialized': services['autocomplete'].is_initialized
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
        corrections = services['autocomplete'].get_spell_corrections(term, max_suggestions=5)
        
        return jsonify({
            'corrections': corrections,
            'original_query': term,
            'message': f'Found {len(corrections)} suggestions' if corrections else 'No suggestions found'
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
        result = process_institution_pipeline(
            institution_name, institution_type, skip_extraction=True, search_params={}
        )
        
        return jsonify({
            'success': not result.get('error'),
            'data': result
        })
