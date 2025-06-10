"""
Configuration for future crawler integration and pipeline optimization.
"""
import os

# Pipeline Configuration
PIPELINE_CONFIG = {
    # Search Phase
    'search': {
        'max_search_results': 10,
        'search_timeout': 30,
        'enable_fallback_llm_search': True,
        'cache_similarity_threshold': 0.85,
    },
    
    # Crawling Phase (Future Implementation)
    'crawling': {
        'max_pages_per_domain': {
            'university': 15,
            'hospital': 12,
            'bank': 10,
            'default': 8
        },
        'crawl_timeout': 60,
        'max_concurrent_requests': 5,
        'respect_robots_txt': True,
        'min_content_length': 500,  # bytes
        'max_content_length': 1000000,  # 1MB
    },
    
    # RAG Processing Phase (Future Implementation)
    'rag': {
        'chunk_size': 1000,
        'chunk_overlap': 200,
        'max_chunks_per_institution': 50,
        'relevance_threshold': 0.7,
        'embedding_model': 'text-embedding-ada-002',
    },
    
    # LLM Extraction Phase
    'llm': {
        'model': 'gemini-2.0-flash',
        'max_tokens': 4000,
        'temperature': 0.1,
        'extraction_timeout': 45,
        'validation_enabled': True,
        'confidence_threshold': 0.6,
    },
    
    # Benchmarking
    'benchmarking': {
        'enabled': True,
        'detailed_logging': True,
        'cost_tracking': True,
        'quality_scoring': True,
        'session_retention_days': 30,
        'comprehensive_retention_days': 365,
    }
}

# Institution Type Specific Extraction Targets
EXTRACTION_TARGETS = {
    'university': [
        'institution_name', 'official_name', 'address', 'city', 'state', 'country',
        'postal_code', 'phone', 'website', 'entity_type', 'founding_year',
        'number_of_students', 'number_of_faculty', 'endowment', 'accreditation',
        'programs_offered', 'campus_size', 'tuition_fees'
    ],
    'hospital': [
        'institution_name', 'official_name', 'address', 'city', 'state', 'country',
        'postal_code', 'phone', 'website', 'entity_type', 'founding_year',
        'number_of_beds', 'number_of_employees', 'medical_specialties',
        'accreditation', 'emergency_services', 'trauma_level', 'teaching_hospital'
    ],
    'bank': [
        'institution_name', 'official_name', 'address', 'city', 'state', 'country',
        'postal_code', 'phone', 'website', 'entity_type', 'founding_year',
        'number_of_employees', 'assets', 'number_of_branches', 'services_offered',
        'regulatory_body', 'stock_symbol', 'annual_revenue'
    ],
    'default': [
        'institution_name', 'official_name', 'address', 'city', 'state', 'country',
        'postal_code', 'phone', 'website', 'entity_type', 'founding_year',
        'number_of_employees', 'description', 'services_offered'
    ]
}

# Domain Priority Scoring
DOMAIN_PRIORITY = {
    'university': {
        '.edu': 100,
        '.ac.': 90,
        '.org': 50,
        'academic': 15,
        'university': 15,
        'college': 15,
        'school': 10,
        'education': 10,
    },
    'hospital': {
        '.org': 80,
        '.gov': 70,
        'hospital': 20,
        'medical': 15,
        'health': 15,
        'clinic': 10,
        'care': 10,
    },
    'bank': {
        '.gov': 100,  # Regulatory sites
        'federal': 70,
        'fdic': 70,
        'occ': 70,
        'bank': 20,
        'financial': 15,
        'credit': 10,
        'finance': 10,
    },
    'default': {
        '.org': 50,
        '.gov': 40,
        'official': 20,
    }
}

# Quality Scoring Weights
QUALITY_WEIGHTS = {
    'completeness': 0.4,  # Percentage of target fields extracted
    'accuracy': 0.3,      # Confidence scores from LLM
    'consistency': 0.2,   # Consistency across sources
    'freshness': 0.1,     # Recency of data sources
}

# Cost Estimates (USD)
COST_ESTIMATES = {
    'google_custom_search': 0.005,  # per query
    'gemini_pro': {
        'input_tokens': 0.000001,    # per token
        'output_tokens': 0.000003,   # per token
    },
    'crawling': 0.001,  # per page (bandwidth, compute)
}

def get_extraction_targets(institution_type: str) -> list:
    """Get extraction targets for a specific institution type."""
    return EXTRACTION_TARGETS.get(institution_type, EXTRACTION_TARGETS['default'])

def get_domain_priority(institution_type: str) -> dict:
    """Get domain priority scoring for a specific institution type."""
    base_priority = DOMAIN_PRIORITY.get('default', {})
    type_priority = DOMAIN_PRIORITY.get(institution_type, {})
    return {**base_priority, **type_priority}

def get_crawling_config(institution_type: str) -> dict:
    """Get crawling configuration for a specific institution type."""
    config = PIPELINE_CONFIG['crawling'].copy()
    if institution_type in config['max_pages_per_domain']:
        config['max_pages'] = config['max_pages_per_domain'][institution_type]
    else:
        config['max_pages'] = config['max_pages_per_domain']['default']
    return config

def estimate_cost(operation: str, **kwargs) -> float:
    """Estimate cost for different operations."""
    if operation == 'search':
        return COST_ESTIMATES['google_custom_search']
    elif operation == 'llm_extraction':
        input_tokens = kwargs.get('input_tokens', 0)
        output_tokens = kwargs.get('output_tokens', 0)
        costs = COST_ESTIMATES['gemini_pro']
        return (input_tokens * costs['input_tokens'] + 
                output_tokens * costs['output_tokens'])
    elif operation == 'crawling':
        pages = kwargs.get('pages', 1)
        return pages * COST_ESTIMATES['crawling']
    return 0.0
