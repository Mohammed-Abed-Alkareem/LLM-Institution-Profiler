# -*- coding: utf-8 -*-
"""
Field Categorization System

This module defines which fields are relevant for different types of institutions
to enable smart quality scoring that only considers relevant fields.
"""

# Universal fields that apply to all institution types (always relevant)
UNIVERSAL_FIELDS = [
    "name", "official_name", "type", "founded", "website", "description",
    "location_city", "location_country", "address", "state", "postal_code",
    "phone", "email", "social_media", "fax", "mailing_address",
    "size", "entity_type", "fields_of_focus", "key_people", "leadership",
    "ceo", "president", "chairman", "founders", "board_of_directors",
    "executive_team", "notable_achievements", "rankings", "awards",
    "certifications", "accreditations", "affiliations", "partnerships",
    "parent_organization", "member_organizations", "headquarters_location",
    "facilities", "locations", "buildings", "infrastructure",
    "logo_url", "main_image_url", "recent_news", "latest_updates",
    "press_releases", "announcements", "upcoming_events", "recent_developments"
]

# Institution-specific fields that only apply to certain types
UNIVERSITY_SPECIFIC_FIELDS = [
    "student_population", "faculty_count", "programs_offered", "degrees_awarded",
    "research_areas", "departments", "colleges", "schools", "accreditation_bodies",
    "course_catalog", "professors", "academic_staff", "administrative_staff",
    "undergraduate_programs", "graduate_programs", "doctoral_programs",
    "professional_programs", "online_programs", "continuing_education",
    "admission_requirements", "tuition_costs", "scholarship_programs",
    "academic_calendar", "semester_system", "graduation_rate",
    "student_faculty_ratio", "campus_housing", "dormitories",
    "libraries", "laboratory_facilities", "sports_facilities",
    "student_organizations", "fraternities_sororities", "athletics_programs",
    "research_centers", "institutes", "academic_rankings",
    "notable_faculty", "distinguished_alumni", "university_press",
    "endowment", "tuition_fees", "campus_size", "campus_images", 
    "facility_images", "notable_alumni", "research_achievements", "patents", "publications"
]

HOSPITAL_SPECIFIC_FIELDS = [
    "patient_capacity", "medical_specialties", "bed_count", "accreditation_bodies",
    "departments", "research_areas", "research_achievements", "certifications"
]

COMPANY_SPECIFIC_FIELDS = [
    "number_of_employees", "annual_revenue", "market_cap", "stock_symbol",
    "industry_sector", "services_offered", "products", "subsidiaries",
    "divisions", "branches", "employees_worldwide", "operating_countries",
    "legal_status", "financial_data", "profit_margins"
]

GOVERNMENT_SPECIFIC_FIELDS = [
    "number_of_employees", "services_offered", "departments", "divisions",
    "budget", "operating_countries", "legal_status"
]

NON_PROFIT_SPECIFIC_FIELDS = [
    "number_of_employees", "services_offered", "funding_sources",
    "grants_received", "budget", "operating_countries"
]

# Keywords that help identify institution types
INSTITUTION_TYPE_KEYWORDS = {
    'university': [
        'university', 'universiteit', 'université', 'universidad', 'università',
        'research university', 'state university', 'public university', 'private university',
        'college', 'community college', 'liberal arts college', 'technical college',
        'polytechnic', 'institute of technology'
    ],
    'hospital': [
        'hospital', 'medical center', 'health system', 'clinic', 'medical',
        'healthcare', 'health care', 'medical facility'
    ],
    'company': [
        'corporation', 'company', 'inc', 'ltd', 'llc', 'enterprises',
        'technologies', 'solutions', 'systems', 'group'
    ],
    'government': [
        'government', 'ministry', 'department', 'agency', 'bureau',
        'administration', 'commission', 'authority'
    ],
    'non_profit': [
        'foundation', 'charity', 'non-profit', 'nonprofit', 'ngo',
        'organization', 'association', 'society', 'institute'
    ]
}


def detect_institution_type(institution_data):
    """
    Detect the institution type based on the extracted data.
    
    Args:
        institution_data: Dictionary containing institution information
        
    Returns:
        String indicating the detected institution type
    """
    # Check explicit type field first
    explicit_type = institution_data.get('type', '').lower()
    entity_type = institution_data.get('entity_type', '').lower()
    name = institution_data.get('name', '').lower()
    description = institution_data.get('description', '').lower()
    
    # Check against keywords
    for inst_type, keywords in INSTITUTION_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if (keyword in explicit_type or 
                keyword in entity_type or
                keyword in name or
                keyword in description):
                return inst_type
    
    # Default fallback logic based on specific fields
    if (institution_data.get('student_population') != 'Unknown' or 
        institution_data.get('faculty_count') != 'Unknown' or
        institution_data.get('programs_offered') != 'Unknown'):
        return 'university'
    
    if (institution_data.get('patient_capacity') != 'Unknown' or
        institution_data.get('bed_count') != 'Unknown' or
        institution_data.get('medical_specialties') != 'Unknown'):
        return 'hospital'
    
    if (institution_data.get('annual_revenue') != 'Unknown' or
        institution_data.get('stock_symbol') != 'Unknown' or
        institution_data.get('market_cap') != 'Unknown'):
        return 'company'
    
    return 'general'


def get_field_relevance_score(field_name, institution_data):
    """
    Determine if a field is relevant for the given institution type.
    
    Args:
        field_name: Name of the field to check
        institution_data: Dictionary containing institution information
        
    Returns:
        Float: 1.0 if relevant, 0.0 if not relevant
    """
    # Universal fields are always relevant
    if field_name in UNIVERSAL_FIELDS:
        return 1.0
    
    # Detect institution type
    institution_type = detect_institution_type(institution_data)
    
    # For unknown/general institutions, only universal fields are relevant
    if institution_type == 'general':
        return 0.0
    
    # Check institution-specific fields
    if institution_type == 'university' and field_name in UNIVERSITY_SPECIFIC_FIELDS:
        return 1.0
    elif institution_type == 'hospital' and field_name in HOSPITAL_SPECIFIC_FIELDS:
        return 1.0
    elif institution_type == 'company' and field_name in COMPANY_SPECIFIC_FIELDS:
        return 1.0
    elif institution_type == 'government' and field_name in GOVERNMENT_SPECIFIC_FIELDS:
        return 1.0
    elif institution_type == 'non_profit' and field_name in NON_PROFIT_SPECIFIC_FIELDS:
        return 1.0
    
    return 0.0
