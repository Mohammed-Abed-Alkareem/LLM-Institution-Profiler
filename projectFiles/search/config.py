"""
Configuration settings for the search module.
"""
import os

# Google Custom Search API configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', '')

# Search parameters
DEFAULT_SEARCH_RESULTS = 10
MAX_SEARCH_RESULTS = 20
REQUEST_TIMEOUT = 30

# Cache configuration
CACHE_EXPIRY_DAYS = 7
CACHE_SIMILARITY_THRESHOLD = 0.85

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 10
DAILY_REQUEST_LIMIT = 100

# File paths
CACHE_DIR = 'search_cache'
BENCHMARK_DIR = 'benchmarks'
