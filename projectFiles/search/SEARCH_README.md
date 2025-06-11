# Institution Profiler Search Module

This module provides comprehensive search capabilities for the Institution Profiler project using Google Custom Search integration with intelligent caching, accurate cache hit tracking, and enhanced performance monitoring.

## 🚀 Features

### **Enhanced Search Capabilities**
- **Google Custom Search Integration**: Professional search API with configurable parameters
- **Intelligent Query Formation**: Institution-type aware query construction and optimization
- **Advanced Result Filtering**: Domain prioritization and relevance scoring
- **Fallback Search Methods**: Multiple search strategies for maximum reliability
- **Rate Limiting**: Respectful API usage with configurable rate controls

### **Cache Performance & Optimization**
- **Accurate Cache Hit Tracking**: Fixed monitoring system for precise cache performance metrics
- **Intelligent Cache Keys**: SHA256-based cache keys with institution-aware parameters
- **Cache Expiration Management**: Configurable TTL with automatic cleanup
- **Performance Optimization**: Sub-second response times with cache integration
- **Cost Management**: API call reduction through effective caching strategies

### **Search Enhancement & Quality**
- **Query Enhancement**: Advanced query construction with institution context
- **Result Quality Scoring**: Relevance assessment and domain prioritization
- **Link Analysis**: URL filtering and institutional relevance evaluation
- **Metadata Extraction**: Rich search result metadata with snippet analysis
- **Search Statistics**: Comprehensive performance and usage analytics

### **Integration & Benchmarking**
- **Benchmarking Integration**: Comprehensive search performance tracking
- **Cache Hit Monitoring**: Accurate tracking of cache vs API usage
- **Cost Analysis**: Real-time API cost monitoring and optimization
- **Quality Metrics**: Search success rates and result relevance scoring
- **Performance Analytics**: Latency, throughput, and efficiency measurements

## 📁 Module Structure

```
search/
├── __init__.py                 # Module initialization and exports
├── search_service.py          # Main search service with cache integration
├── search_backup_logic.py     # Fallback search methods
├── search_enhancer.py         # Query enhancement and optimization
├── google_client.py           # Google Custom Search client
├── config.py                  # Search configuration and settings
├── cache.py                   # Search-specific caching implementation
├── rate_limiter.py            # API rate limiting and throttling
├── benchmark.py               # Search performance benchmarking
└── setup_search.py           # Search service initialization utilities
```

## 🔧 Configuration

### **Search Configuration (`config.py`)**
```python
# Google Custom Search settings
GOOGLE_CSE_ID = "your_search_engine_id"
GOOGLE_API_KEY = "your_api_key"

# Search parameters
DEFAULT_SEARCH_PARAMS = {
    'num_results': 10,
    'language': 'en',
    'country': 'us',
    'safe_search': 'medium'
}

# Cache settings
CACHE_TTL_HOURS = 168  # 7 days
CACHE_CLEANUP_INTERVAL = 24  # hours

# Rate limiting
RATE_LIMIT_REQUESTS_PER_SECOND = 2
RATE_LIMIT_BURST_SIZE = 5
```

### **Enhanced Query Formation**
```python
# Institution-specific query enhancement
INSTITUTION_QUERY_TEMPLATES = {
    'university': '{name} university college education academic',
    'hospital': '{name} hospital medical health clinic healthcare',
    'bank': '{name} bank banking financial finance',
    'general': '{name} organization institution'
}

# Domain prioritization for different institution types
DOMAIN_PRIORITIES = {
    'university': ['.edu', '.ac.', 'university', 'college'],
    'hospital': ['.org', 'hospital', 'medical', 'health'],
    'bank': ['.com', 'bank', 'financial'],
    'general': ['.org', '.com', '.gov']
}
```

## 🚀 Usage Examples

### **Basic Search Operations**
```python
from search import SearchService
from cache_config import get_cache_config

# Initialize search service
cache_config = get_cache_config()
search_service = SearchService(cache_config)

# Perform institution search
result = search_service.search_institution(
    institution_name="Harvard University",
    institution_type="university",
    max_results=10
)

# Access search results
if result['success']:
    links = result['links']
    metadata = result['metadata']
    cache_hit = result['cache_hit']
    search_time = result['search_time']
```

### **Advanced Search with Benchmarking**
```python
from benchmarking import BenchmarkContext

# Search with performance tracking
with BenchmarkContext(benchmark_manager, "search_harvard") as ctx:
    result = search_service.search_institution_with_benchmark(
        institution_name="MIT",
        institution_type="university",
        benchmark_ctx=ctx
    )
    
    # Automatic cache hit tracking and cost analysis
    cache_efficiency = ctx.get_cache_efficiency()
    api_costs = ctx.get_total_costs()
```

### **Custom Query Enhancement**
```python
# Enhanced query construction
enhanced_query = search_service.enhance_query(
    base_query="Stanford University",
    institution_type="university",
    include_location=True,
    include_keywords=['computer science', 'engineering']
)

# Custom search parameters
custom_params = {
    'num_results': 15,
    'country': 'us',
    'language': 'en',
    'date_restrict': 'm6'  # Last 6 months
}

result = search_service.search_with_params(enhanced_query, custom_params)
```

## 📊 Cache Performance System

### **Cache Hit Tracking**
The search module now provides **accurate cache hit monitoring**:

```python
# Cache performance metrics
cache_stats = search_service.get_cache_statistics()
{
    'total_requests': 150,
    'cache_hits': 98,
    'cache_misses': 52,
    'hit_rate_percent': 65.3,
    'average_response_time_cached': 0.05,  # seconds
    'average_response_time_api': 1.2,      # seconds
    'cost_savings_usd': 0.42
}
```

### **Cache Key Strategy**
```python
# Intelligent cache key generation
def generate_cache_key(institution_name, institution_type, search_params):
    """
    Creates SHA256-based cache keys that account for:
    - Institution name (normalized)
    - Institution type
    - Search parameters
    - API configuration
    """
    key_components = [
        institution_name.lower().strip(),
        institution_type or 'general',
        json.dumps(search_params, sort_keys=True),
        GOOGLE_CSE_ID[:8]  # API configuration fingerprint
    ]
    return hashlib.sha256('|'.join(key_components).encode()).hexdigest()[:16]
```

### **Cache Management**
```python
# Cache lifecycle management
search_service.cleanup_expired_cache()  # Remove expired entries
search_service.warm_cache(['Harvard', 'MIT', 'Stanford'])  # Pre-populate
search_service.invalidate_cache('Oxford University')  # Force refresh
```

## 📈 Performance Optimization

### **Search Speed Optimization**
- **Cache-First Strategy**: Check cache before API calls
- **Parallel Processing**: Concurrent handling of multiple search requests
- **Response Caching**: Full result caching with metadata
- **Query Optimization**: Enhanced query construction for better results

### **Cost Management**
```python
# API cost tracking and optimization
cost_analysis = {
    'total_api_calls': 52,
    'cache_hit_savings': 98,
    'estimated_cost_usd': 0.052,  # $0.001 per query
    'cost_savings_usd': 0.098,
    'efficiency_ratio': 65.3      # percentage
}
```

### **Quality Enhancement**
- **Result Filtering**: Domain-based relevance scoring
- **Snippet Analysis**: Content quality assessment
- **Link Validation**: URL accessibility and relevance checking
- **Metadata Enrichment**: Enhanced result information

## 🔗 Integration Points

### **Processor Pipeline Integration**
```python
# Seamless integration with processor pipeline
from processor import SearchPhaseHandler

search_handler = SearchPhaseHandler(search_service, link_manager)
search_result = search_handler.execute_search_phase(
    institution_name="Yale University",
    institution_type="university",
    search_params={},
    benchmark_ctx=context
)
```

### **Benchmarking Integration**
```python
# Automatic performance tracking
benchmark_data = {
    'search_time': 0.85,
    'cache_hit': True,
    'api_calls': 0,
    'results_count': 12,
    'quality_score': 87.5
}
```

### **Flask API Integration**
```python
# Direct endpoint integration
@app.route('/api/search')
def search_endpoint():
    result = search_service.search_institution(
        request.args.get('name'),
        request.args.get('type'),
        max_results=int(request.args.get('limit', 10))
    )
    return jsonify(result)
```

## 🔍 Search Enhancement Features

### **Query Enhancement Engine**
```python
# Advanced query construction
class SearchEnhancer:
    def enhance_institution_query(self, name, institution_type):
        """
        Enhances search queries with:
        - Institution type keywords
        - Location information
        - Domain preferences
        - Relevance filters
        """
```

### **Result Quality Assessment**
```python
# Search result quality scoring
def assess_result_quality(search_results, institution_type):
    """
    Evaluates search results based on:
    - Domain relevance (.edu for universities)
    - Content snippet quality
    - URL structure analysis
    - Institutional indicators
    """
```

### **Fallback Search Strategies**
```python
# Multiple search approaches
SEARCH_STRATEGIES = [
    'google_cse_primary',      # Main Google Custom Search
    'google_cse_fallback',     # Alternative CSE configuration
    'organic_search_simulation', # Fallback method
    'domain_specific_search'   # Institution-type specific search
]
```

## 📊 Search Analytics & Monitoring

### **Real-time Performance Metrics**
- **Search Latency**: Response time tracking and optimization
- **Cache Efficiency**: Hit rate monitoring and cost analysis
- **Result Quality**: Relevance scoring and success rates
- **API Usage**: Call frequency and cost management

### **Search Statistics Dashboard**
```python
# Comprehensive search analytics
search_analytics = {
    'daily_searches': 247,
    'average_response_time': 0.45,
    'cache_hit_rate': 68.5,
    'top_searched_institutions': ['Harvard', 'MIT', 'Stanford'],
    'search_success_rate': 94.7,
    'cost_per_search': 0.0032
}
```

## 🔮 Future Enhancements

- **Semantic Search**: Vector-based similarity search for institution matching
- **Multi-language Support**: International institution search capabilities
- **Real-time Suggestions**: Live search suggestions and autocomplete
- **Advanced Filtering**: Complex search filters and faceted search
- **Machine Learning**: AI-powered query enhancement and result ranking

## 📞 Support

The search module provides robust, efficient institution search capabilities with comprehensive caching, accurate performance tracking, and seamless integration with the Institution Profiler pipeline. For questions or issues, check the search service logs and cache statistics for detailed performance information.
