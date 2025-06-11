# -*- coding: utf-8 -*-
"""
Quality Score Calculator

This module contains the quality score calculation logic extracted from core_routes
to avoid circular imports and make it reusable across the application.
"""

def is_field_populated(value):
    """Check if a field value is considered populated (not empty/null)."""
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != "" and value.lower() not in ['unknown', 'n/a', 'not available', 'none']
    if isinstance(value, (list, dict)):
        return len(value) > 0
    if isinstance(value, (int, float)):
        return value != 0
    return bool(value)


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
