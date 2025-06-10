# Search System Documentation

This document explains how to set up and use the Google Custom Search integration for the Institution Profiler project.

## Overview

The search system provides:
- **Google Custom Search API integration** for fetching institution data
- **Intelligent caching** with similarity matching to minimize API calls
- **Comprehensive benchmarking** for performance analysis and cost tracking
- **RESTful API endpoints** for easy integration

## Setup

### 1. Get Google API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Custom Search API"
4. Create an API key in "Credentials"
5. Go to [Google Custom Search Engine](https://cse.google.com/cse/)
6. Create a new search engine
7. Get your Custom Search Engine ID

### 2. Configure Environment Variables

**Option A: Environment Variables (Recommended)**
```powershell
# In PowerShell
$env:GOOGLE_API_KEY="your_api_key_here"
$env:GOOGLE_CSE_ID="your_cse_id_here"
```

**Option B: .env file**
```bash
# Copy .env.example to .env and fill in your credentials
cp .env.example .env
# Edit .env with your credentials
```

### 3. Test the Setup

Run the setup script to verify everything is working:
```powershell
python setup_search.py
```

## API Endpoints

### Search for Institution
```http
GET /search?name=institution_name&type=university&force_api=false
```
- `name` (required): Institution name
- `type` (optional): Institution type (university, hospital, bank, etc.)
- `force_api` (optional): Force API call even if cached result exists

**Response:**
```json
{
  "success": true,
  "query": "MIT university",
  "results": [...],
  "total_results": "123000",
  "search_time": 0.45,
  "cache_hit": false,
  "source": "api",
  "response_time": 1.23
}
```

### Get Institution Links for Crawling
```http
GET /search/links?name=institution_name&type=university&max_links=10
```
Returns just the URLs from search results, useful for web crawling.

### Search Statistics
```http
GET /search/stats
```
Get comprehensive statistics including cache performance and API usage.

### Recent Searches
```http
GET /search/recent?limit=10
```
Get recent search history with performance metrics.

### Performance Analysis
```http
GET /search/performance
```
Get performance analysis broken down by institution type.

### Cache Management
```http
GET /search/cache          # List cached queries
POST /search/cache/clear    # Clear expired cache entries
```

## Caching System

The caching system includes:

### Direct Cache Hits
Exact matches for previous queries are served from cache.

### Similarity Matching
Queries with 85% similarity to cached queries reuse cached results:
- "Massachusetts Institute of Technology" ≈ "MIT"
- "Harvard University" ≈ "Harvard College"

### Cache Expiration
Cache entries expire after 7 days by default.

### Cache Statistics
Track cache hit rates, similar matches, and performance metrics.

## Benchmarking

Every search is benchmarked with:
- **Response time** (total time including cache lookup)
- **API search time** (time spent in Google API)
- **Source tracking** (cache, similar_cache, api, error)
- **Cost estimation** (based on API usage)
- **Success rates** by institution type

### Benchmark Files
- `benchmarks/session_YYYYMMDD_HHMMSS.json` - Current session
- `benchmarks/all_benchmarks.json` - Historical data

## Integration with Your Code

### Using in Python
```python
from search.search_service import SearchService

# Initialize service
search_service = SearchService()

# Search for institution
result = search_service.search_institution("Harvard", "university")

# Get links for crawling
links = search_service.get_search_links("MIT", "university", max_links=5)

# Check if service is ready
if search_service.is_ready():
    # Make searches
    pass
```

### Using the Legacy Interface
The existing `search_logic.py` functions now use the new system:
```python
from search_logic import fetch_raw_institution_text_api_version, get_institution_links_for_crawling

# Get institution text
result = fetch_raw_institution_text_api_version("Harvard", "university")

# Get crawling links
links = get_institution_links_for_crawling("MIT", "university", 10)
```

## Configuration

Modify `search/config.py` to adjust:
- Cache expiry time
- Similarity threshold for cache matching
- Rate limiting settings
- Default search parameters

## Error Handling

The system gracefully handles:
- **Missing credentials** - Returns error without crashing
- **API rate limits** - Built-in rate limiting
- **Network timeouts** - Configurable timeout settings
- **Cache corruption** - Automatic cache cleanup

## Cost Optimization

- **Cache first**: Always check cache before API calls
- **Similarity matching**: Reuse similar queries
- **Rate limiting**: Prevent accidental quota exhaustion
- **Usage tracking**: Monitor API call costs
- **Selective caching**: Only cache successful results

## Monitoring

Use the stats endpoints to monitor:
- Cache hit rates (aim for >80%)
- Average response times
- API usage patterns
- Error rates by institution type

## Troubleshooting

### "Search service not configured"
- Check environment variables are set
- Verify API key and CSE ID are correct
- Run `python setup_search.py` to test

### Poor cache hit rates
- Check query similarity threshold in config
- Verify cache directory permissions
- Monitor cache expiration settings

### High API costs
- Increase cache expiry time
- Lower similarity threshold for more cache reuse
- Implement query preprocessing to normalize inputs
