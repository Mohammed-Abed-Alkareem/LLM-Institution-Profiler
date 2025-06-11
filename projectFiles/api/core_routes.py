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
                    search_params['exclude_terms'] = exclude_terms
                
                # Process the institution with enhanced search parameters
                processed_data = process_institution_pipeline(
                    institution_name, institution_type, search_params=search_params
                )
                
                # Calculate information quality score
                if processed_data:
                    score, rating, details = calculate_information_quality_score(processed_data)
                    processed_data['quality_score'] = score
                    processed_data['quality_rating'] = rating
                    processed_data['quality_details'] = details
                
                # Check if we have meaningful data to display in enhanced results view
                has_meaningful_data = any([
                    # Visual assets found
                    processed_data.get('logos_found'),
                    processed_data.get('images_found'),
                    # Crawling was successful
                    processed_data.get('crawling_links'),
                    # Basic institution info extracted
                    processed_data.get('address') and processed_data.get('address') != 'Unknown',
                    processed_data.get('location_city') and processed_data.get('location_city') != 'Unknown',
                    processed_data.get('phone') and processed_data.get('phone') != 'Unknown',
                    processed_data.get('website') and processed_data.get('website') != 'Unknown',
                    # Enhanced fields populated
                    processed_data.get('type') and processed_data.get('type') != 'Unknown',
                    processed_data.get('founded') and processed_data.get('founded') != 'Unknown',
                    processed_data.get('description') and processed_data.get('description') != 'Unknown',
                    # Processing phases completed successfully
                    any(phase.get('success') for phase in processed_data.get('processing_phases', {}).values())
                ])
                
                if processed_data and (not processed_data.get('error') or has_meaningful_data):
                    # Render the enhanced results template
                    return render_template('results.html', 
                                         institution_data=processed_data,
                                         raw_data=safe_json_dumps(processed_data, indent=2))
                else:
                    # Fall back to simple display for errors or minimal data
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


def calculate_information_quality_score(institution_data):
    """
    Calculate a comprehensive information quality score based on field population.
    Uses a sophisticated weighted system that categorizes all 96 structured fields
    by importance and assigns appropriate scoring weights.
    Returns a score from 0-100 and a quality rating with detailed breakdown.
    """
    from extraction_logic import STRUCTURED_INFO_KEYS
    
    if not institution_data:
        return 0, "No Data", {
            'total_fields': 0,
            'populated_fields': 0,
            'critical_fields_populated': 0,
            'critical_fields_total': 0,
            'bonus_points': 0,
            'institution_type': 'unknown'
        }
    
    # Field categories with different scoring weights
    field_categories = {
        # Critical Fields (40% of score) - Essential identification info
        'critical': {
            'weight': 40,
            'fields': [
                'name', 'official_name', 'type', 'website', 'description',
                'location_city', 'location_country', 'entity_type'
            ]
        },
        
        # Important Fields (25% of score) - Key operational details
        'important': {
            'weight': 25,
            'fields': [
                'founded', 'address', 'state', 'postal_code', 'phone', 'email',
                'industry_sector', 'size', 'number_of_employees', 'headquarters_location'
            ]
        },
        
        # Valuable Fields (20% of score) - Detailed organizational info
        'valuable': {
            'weight': 20,
            'fields': [
                'leadership', 'ceo', 'president', 'chairman', 'key_people',
                'annual_revenue', 'legal_status', 'fields_of_focus',
                'services_offered', 'products', 'operating_countries'
            ]
        },
        
        # Specialized Fields (10% of score) - Domain-specific details
        'specialized': {
            'weight': 10,
            'fields': [
                'student_population', 'faculty_count', 'programs_offered',
                'medical_specialties', 'patient_capacity', 'bed_count',
                'departments', 'research_areas', 'accreditation_bodies'
            ]
        },
        
        # Enhanced Fields (5% of score) - Rich content and relationships
        'enhanced': {
            'weight': 5,
            'fields': [
                'notable_achievements', 'rankings', 'awards', 'certifications',
                'affiliations', 'partnerships', 'publications', 'patents',
                'financial_data', 'endowment', 'budget', 'campus_size',
                'facilities', 'recent_news', 'press_releases'
            ]
        }
    }
    
    # Calculate scores for each category
    category_scores = {}
    total_populated = 0
    total_fields = len(STRUCTURED_INFO_KEYS)
    
    for category_name, category_info in field_categories.items():
        category_fields = category_info['fields']
        category_populated = 0
        
        for field in category_fields:
            if field in STRUCTURED_INFO_KEYS:
                value = institution_data.get(field)
                if is_field_populated(value):
                    category_populated += 1
                    total_populated += 1
        
        # Calculate category score (0-1 range)
        category_completion = category_populated / len(category_fields) if category_fields else 0
        category_scores[category_name] = {
            'completion_rate': category_completion,
            'populated_count': category_populated,
            'total_count': len(category_fields),
            'weighted_score': category_completion * category_info['weight']
        }
    
    # Calculate remaining fields not in any category
    categorized_fields = set()
    for category_info in field_categories.values():
        categorized_fields.update(category_info['fields'])
    
    remaining_fields = [f for f in STRUCTURED_INFO_KEYS if f not in categorized_fields]
    remaining_populated = 0
    for field in remaining_fields:
        value = institution_data.get(field)
        if is_field_populated(value):
            remaining_populated += 1
            total_populated += 1
    
    # Base score from weighted categories
    base_score = sum(cat['weighted_score'] for cat in category_scores.values())
    
    # Bonus scoring for additional content richness (up to 25 points)
    bonus_score = 0
    
    # Visual content bonus (up to 8 points)
    if institution_data.get('logos_found'):
        bonus_score += 3
    if institution_data.get('images_found'):
        bonus_score += 2
    if institution_data.get('facility_images'):
        bonus_score += 2
    if institution_data.get('campus_images'):
        bonus_score += 1
    
    # Content richness bonus (up to 7 points)
    if institution_data.get('social_media_links'):
        bonus_score += 2
    if institution_data.get('documents_found'):
        bonus_score += 2
    if institution_data.get('crawling_links') and len(institution_data.get('crawling_links', [])) > 3:
        bonus_score += 3
    
    # Data source quality bonus (up to 10 points)
    crawl_summary = institution_data.get('crawl_summary', {})
    if crawl_summary.get('success_rate', 0) >= 80:
        bonus_score += 3
    if crawl_summary.get('total_content_size_mb', 0) > 1:
        bonus_score += 2
    if crawl_summary.get('cache_hit_rate', 0) < 50:  # Fresh data bonus
        bonus_score += 2
    
    # Processing success bonus (up to 5 points)
    processing_phases = institution_data.get('processing_phases', {})
    successful_phases = sum(1 for phase in processing_phases.values() if phase.get('success'))
    if successful_phases >= 3:
        bonus_score += 3
    elif successful_phases >= 2:
        bonus_score += 2
    
    # Multi-source verification bonus
    if institution_data.get('extraction_metrics', {}).get('success') and crawl_summary.get('success_rate', 0) > 0:
        bonus_score += 2
    
    # Final score calculation
    final_score = min(100, base_score + bonus_score)
    
    # Determine quality rating with more nuanced ranges
    if final_score >= 90:
        rating = "Exceptional"
    elif final_score >= 80:
        rating = "Excellent" 
    elif final_score >= 70:
        rating = "Very Good"
    elif final_score >= 60:
        rating = "Good"
    elif final_score >= 50:
        rating = "Fair"
    elif final_score >= 35:
        rating = "Poor"
    elif final_score >= 20:
        rating = "Very Poor"
    else:
        rating = "Minimal"
    
    # Get institution type for context
    institution_type = institution_data.get('type', 'Unknown')
    if institution_type == 'Unknown':
        institution_type = institution_data.get('entity_type', 'Unknown')
    
    # Detailed breakdown for transparency
    details = {
        'total_fields': total_fields,
        'populated_fields': total_populated,
        'completion_percentage': round((total_populated / total_fields) * 100, 1),
        'critical_fields_populated': category_scores['critical']['populated_count'],
        'critical_fields_total': category_scores['critical']['total_count'],
        'important_fields_populated': category_scores['important']['populated_count'],
        'important_fields_total': category_scores['important']['total_count'],
        'bonus_points': round(bonus_score, 1),
        'base_score': round(base_score, 1),
        'institution_type': institution_type,
        'category_breakdown': {
            cat_name: {
                'completion_rate': round(cat_data['completion_rate'] * 100, 1),
                'populated': cat_data['populated_count'],
                'total': cat_data['total_count'],
                'contribution': round(cat_data['weighted_score'], 1)
            }
            for cat_name, cat_data in category_scores.items()
        },
        'content_sources': {
            'crawled_pages': crawl_summary.get('total_urls_requested', 0),
            'successful_crawls': crawl_summary.get('successful_crawls', 0),
            'content_size_mb': crawl_summary.get('total_content_size_mb', 0),
            'extraction_success': institution_data.get('extraction_metrics', {}).get('success', False)
        }
    }
    
    return round(final_score, 1), rating, details


def is_field_populated(value):
    """
    Determine if a field is meaningfully populated.
    More sophisticated checking for various data types.
    """
    if value is None:
        return False
    
    # Handle different data types
    if isinstance(value, str):
        # String fields
        cleaned = value.strip().lower()
        return cleaned and cleaned not in [
            'unknown', 'n/a', 'not available', 'none', 'null', 
            'not found', 'no information', 'tbd', 'pending',
            'not specified', 'not provided', 'unavailable'
        ]
    elif isinstance(value, (list, tuple)):
        # List/array fields
        return len(value) > 0 and any(is_field_populated(item) for item in value)
    elif isinstance(value, dict):
        # Dictionary fields
        return len(value) > 0 and any(is_field_populated(v) for v in value.values())
    elif isinstance(value, (int, float)):
        # Numeric fields
        return value > 0
    elif isinstance(value, bool):
        # Boolean fields are always considered populated
        return True
    else:
        # Other types
        return bool(value)
