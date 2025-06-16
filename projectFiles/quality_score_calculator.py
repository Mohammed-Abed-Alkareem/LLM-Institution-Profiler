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
    Uses a sophisticated weighted system that categorizes fields by importance and
    institution relevance. Only counts institution-specific fields for relevant types.
    Returns a score from 0-100 and a quality rating with detailed breakdown.
    """
    from extraction_logic import STRUCTURED_INFO_KEYS
    from field_categorization import detect_institution_type, get_field_relevance_score
    
    if not institution_data:
        return 0, "No Data", {
            'total_fields': 0,
            'populated_fields': 0,
            'critical_fields_populated': 0,
            'critical_fields_total': 0,
            'bonus_points': 0,
            'institution_type': 'unknown'
        }
    
    # Detect institution type for relevance filtering
    institution_type = detect_institution_type(institution_data)


    # Field categories with different scoring weights
    # Only fields relevant to the institution type will contribute to the score
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
        
        # Specialized Fields (10% of score) - Institution-specific details
        # These only count if relevant to the institution type
        'specialized': {
            'weight': 10,
            'fields': [
                'student_population', 'faculty_count', 'programs_offered',
                'medical_specialties', 'patient_capacity', 'bed_count',
                'departments', 'research_areas', 'accreditation_bodies',
                # New university-specific fields
                'course_catalog', 'professors', 'academic_staff', 'administrative_staff',
                'undergraduate_programs', 'graduate_programs', 'doctoral_programs',
                'professional_programs', 'online_programs', 'continuing_education',
                'admission_requirements', 'tuition_costs', 'scholarship_programs',
                'academic_calendar', 'semester_system', 'graduation_rate',
                'student_faculty_ratio', 'campus_housing', 'dormitories',
                'libraries', 'laboratory_facilities', 'sports_facilities',
                'student_organizations', 'fraternities_sororities', 'athletics_programs',
                'research_centers', 'institutes', 'academic_rankings',
                'notable_faculty', 'distinguished_alumni', 'university_press'
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
    
    # Calculate scores for each category with institution-type awareness
    category_scores = {}
    total_populated = 0
    total_relevant_fields = 0
    
    for category_name, category_info in field_categories.items():
        category_fields = category_info['fields']
        category_populated = 0
        category_relevant_count = 0
        
        for field in category_fields:
            if field in STRUCTURED_INFO_KEYS:
                # Check if field is relevant for this institution type
                relevance = get_field_relevance_score(field, institution_data)
                
                if relevance > 0:  # Field is relevant
                    category_relevant_count += 1
                    total_relevant_fields += 1
                    
                    value = institution_data.get(field)
                    if is_field_populated(value):
                        category_populated += 1
                        total_populated += 1
        
        # Calculate category score (0-1 range) based on relevant fields only
        category_completion = category_populated / category_relevant_count if category_relevant_count > 0 else 0
        category_scores[category_name] = {
            'completion_rate': category_completion,
            'populated_count': category_populated,
            'total_count': category_relevant_count,
            'weighted_score': category_completion * category_info['weight']
        }
    
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
    if institution_type == 'general':
        institution_type = institution_data.get('type', 'Unknown')
        if institution_type == 'Unknown':
            institution_type = institution_data.get('entity_type', 'Unknown')
    
    # Detailed breakdown for transparency
    details = {
        'total_fields': len(STRUCTURED_INFO_KEYS),
        'relevant_fields': total_relevant_fields,
        'populated_fields': total_populated,
        'completion_percentage': round((total_populated / total_relevant_fields) * 100, 1) if total_relevant_fields > 0 else 0,
        'critical_fields_populated': category_scores['critical']['populated_count'],
        'critical_fields_total': category_scores['critical']['total_count'],
        'important_fields_populated': category_scores['important']['populated_count'],
        'important_fields_total': category_scores['important']['total_count'],
        'bonus_points': round(bonus_score, 1),
        'base_score': round(base_score, 1),
        'institution_type': institution_type,
        'scoring_method': 'institution_aware',
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
