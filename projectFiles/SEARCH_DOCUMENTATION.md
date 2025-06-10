# Institution Profiler Enhanced Search System Documentation

This document explains the complete integrated search and data processing pipeline for the Institution Profiler project, including the latest enhancements.

## System Overview

The Institution Profiler uses a sophisticated multi-stage pipeline with intelligent query enhancement and flexible search parameters:

### **Complete Pipeline Flow:**
1. **Smart Query Enhancement** → Flexible search parameters with auto-detection
2. **Search & Discovery** → Google Custom Search API (primary) + LLM Search (fallback)
3. **Link Prioritization** → Institution type-aware domain scoring
4. **Web Crawling** → Intelligent content extraction from prioritized sites *(planned)*
5. **RAG Processing** → Document chunking and relevance filtering *(planned)*
6. **LLM Extraction** → Structured data extraction with validation
7. **Comprehensive Benchmarking** → End-to-end performance and cost tracking

### **Latest Enhancements (June 2025):**
- ✅ **Flexible Search Parameters**: Location, keywords, domain hints, exclusion terms
- ✅ **Smart Query Enhancement**: Automatic institution type detection and query optimization
- ✅ **Modern Web Interface**: Polished toggle-based refinement panel
- ✅ **Centralized Cache System**: All cache data organized in `project_cache/` folder
- ✅ **Enhanced Benchmarking**: Pipeline-wide performance tracking
- ✅ **Improved User Experience**: Clean, intuitive search refinement options

### **Core Features:**
- **Smart Query Building**: Automatic enhancement based on institution type and context
- **Flexible Search Parameters**: Optional location, keywords, domain hints, exclusions
- **Dual Search Strategy**: Google Custom Search API with LLM fallback
- **Intelligent Caching** with similarity matching to minimize API costs
- **Institution Type-Aware Processing** with auto-detection
- **Crawling Optimization** with domain prioritization and extraction targets
- **Comprehensive Benchmarking** tracking entire pipeline performance
- **Cost Optimization** through caching, rate limiting, and smart processing

## Enhanced Search System

### **Smart Query Enhancement**

The system now intelligently enhances queries using configurable parameters:

**Verified Enhancement Examples:**
- `MIT` → `"MIT university education academic"` (auto-detected: university) ✅ **WORKING**
- `Mayo Clinic` → `"Mayo Clinic hospital healthcare medical"` (auto-detected: hospital) ✅ **WORKING**
- `Harvard University` → Enhanced with university keywords ✅ **WORKING**
- `JPMorgan Chase` → `"JPMorgan Chase bank banking financial"` (auto-detected: bank) *(example)*

**Enhancement Parameters:**
- **Institution Type**: Auto-detected or manually specified
- **Location**: Geographic filtering (e.g., "Boston", "California", "UK")
- **Additional Keywords**: Domain-specific terms (e.g., "research", "cardiology")
- **Domain Hint**: Known website domains (e.g., "mit.edu", "mayo.org")
- **Exclude Terms**: Terms to avoid (e.g., "jobs", "admissions", "news")

**Query Strategy Selection:**
```javascript
// Strategy examples based on parameters
{
  "official_sites_first": true,     // Try .edu/.org/.gov first
  "fallback_to_general": true,      // Broaden search if needed
  "combine_results": true,          // Merge official + general results
  "max_results_per_query": 10       // Adaptive result limits
}
```

### **Modern Web Interface**

**Refined Search Panel:**
- Clean toggle button: "Refine Search" with sliders icon
- Smooth animations and hover effects
- Card-based layout for additional parameters
- Visual feedback for active/inactive states

**Search Parameters Available:**
1. **Institution Type** - Auto-detected or manual override
2. **Location** - Geographic context for better targeting
3. **Additional Keywords** - Domain-specific enhancement terms
4. **Domain Hint** - Known website domains for precise targeting
5. **Exclude Terms** - Terms to filter out from results

### **Enhanced Caching System**

**Centralized Structure:**
```
project_cache/
├── search_results/          # Enhanced search cache with parameters
├── benchmarks/              # Performance tracking data
├── crawling_data/           # Web crawling cache (future)
├── rag_embeddings/          # RAG processing cache (future)
└── llm_responses/           # LLM response cache (future)
```

**Smart Caching Features:**
- Parameter-aware cache keys
- Similarity matching (85% threshold)
- Enhanced metadata tracking
- Automatic cleanup of old cache folders

### **Stage 2: Link Prioritization & Crawling Preparation**

**Domain Scoring Algorithm:**
```
Educational Institutions:
- .edu domains: +100 priority
- Academic keywords: +15 each
- Official domains: +50

Financial Institutions:
- Financial domains (.gov financial pages): +100
- Banking keywords: +15 each
- Regulatory sites: +70

Medical Institutions:
- Healthcare domains: +100
- Medical keywords: +15 each
- Hospital/clinic indicators: +50
```

**Crawling Configuration:**
- Maximum pages per domain based on institution size
- Extraction targets tailored to institution type
- Content filtering rules for relevant data

### **Stage 3: Web Crawling** *(Planned)*
- Intelligent content extraction from prioritized URLs
- HTML size tracking and optimization
- Content deduplication and quality filtering
- Structured data preservation

### **Stage 4: RAG Processing** *(Planned)*
- Document chunking with overlap optimization
- Relevance scoring for information extraction
- Chunk size optimization based on institution type
- Vector embedding for semantic search

### **Stage 5: LLM Extraction** *(Planned)*
- Institution type-specific prompting
- Structured JSON output with validation
- Token usage optimization
- Confidence scoring and validation

### **Stage 6: Comprehensive Benchmarking**
Tracks performance across the entire pipeline:
- Search latency and cache performance
- Crawling efficiency and data quality
- RAG processing optimization
- LLM token usage and cost analysis

## Setup & Configuration

### **1. Get Google API Credentials**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Custom Search API"
4. Create an API key in "Credentials"
5. Go to [Google Custom Search Engine](https://cse.google.com/cse/)
6. Create a new search engine
7. Get your Custom Search Engine ID

### **2. Configure Environment Variables**

**Option A: Environment Variables (Recommended)**
```powershell
# In PowerShell
$env:GOOGLE_SEARCH_API_KEY="your_api_key_here"
$env:GOOGLE_CSE_ID="your_cse_id_here"
```

**Option B: .env file**
```bash
# Copy .env.example to .env and fill in your credentials
cp .env.example .env
# Edit .env with your credentials
```

### **3. Test the Setup**

Run the setup script to verify everything is working:
```powershell
cd projectFiles; python setup_search.py
```

## Current API Endpoints

### **Search for Institution**
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

### **Get Institution Links for Crawling**
```http
GET /search/links?name=institution_name&type=university&max_links=10
```
Returns prioritized URLs from search results, optimized for web crawling.

### **Crawling Preparation**
```http
GET /crawling/prepare?name=institution_name&type=university
```
Returns complete crawling configuration with prioritized links and extraction targets.

### **Performance & Analytics**
```http
GET /search/stats          # Comprehensive pipeline statistics
GET /search/recent?limit=10 # Recent search history
GET /search/performance     # Performance analysis by institution type
GET /search/cache          # Cache management and statistics
POST /search/cache/clear    # Clear expired cache entries
```

## Centralized Cache System

All caching and benchmarking data is now stored in a centralized `project_cache` folder structure:

```
project_cache/
├── search_results/          # Search cache with similarity matching
├── benchmarks/              # Performance and pipeline tracking
├── crawling_data/           # Web crawling cache (future)
├── rag_embeddings/          # RAG processing cache (future)
└── llm_responses/           # LLM response cache (future)
```

### Cache Management Endpoints
```http
GET /cache/info              # View cache structure and usage statistics
POST /cache/cleanup?dry_run=false  # Clean up old scattered cache folders
```

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

## Integration with Main Application

### **Python Integration**
```python
from institution_processor import process_institution_pipeline

# Full pipeline with extraction
result = process_institution_pipeline("Harvard University", "university")

# Search and prepare for crawling only (skip extraction)
result = process_institution_pipeline("MIT", "university", skip_extraction=True)

# Access benchmark data
pipeline_time = result.get('benchmark_data', {}).get('pipeline_time', 0)
completeness = result.get('benchmark_data', {}).get('completeness_percent', 0)
```

### **Enhanced Flask Endpoints**
```http
# Main processing endpoint (now with comprehensive benchmarking)
POST / 
Content-Type: application/x-www-form-urlencoded
institution_name=Harvard&institution_type=university

# Comprehensive benchmarking endpoints
GET /benchmarks/pipeline        # Pipeline-specific benchmarks
GET /benchmarks/overview        # Complete system overview
GET /search/stats               # Search-only statistics (legacy)
```

### **Response Format**
The main pipeline now returns comprehensive tracking data:
```json
{
  "name": "Harvard University",
  "entity_type": "University",
  "address": "Cambridge, MA",
  "crawling_links": [...],
  "crawling_config": {...},
  "pipeline_id": "Harvard University_1749537936008",
  "benchmark_data": {
    "pipeline_time": 1.234,
    "success": true,
    "phase": "extraction_complete",
    "completeness_percent": 85.0
  },
  "data_source_notes": "Found 5 links for crawling. Search method: api. Structured data extracted by LLM from raw text."
}
```

## Comprehensive Benchmarking System

The system tracks performance across the entire pipeline with multiple levels of granularity:

### **Benchmark Data Types**

**SearchBenchmark**: Individual search operations
- Query, response time, cache performance
- Source tracking (API, cache, similar cache, LLM fallback)
- Institution type-specific metrics

**CrawlingBenchmark**: Web crawling operations *(future)*
- URLs crawled, success rates, content sizes
- Domain-wise performance analysis
- Content optimization metrics

**RAGBenchmark**: Document processing *(future)*
- Chunking efficiency, relevance scoring
- Embedding performance, similarity search times

**LLMBenchmark**: AI extraction operations *(future)*
- Token usage, cost tracking, model performance
- Confidence scoring, validation metrics

**ComprehensiveBenchmark**: End-to-end pipeline
- Total processing time, success rates
- Data quality and completeness scores
- Cost analysis across all phases

### **Benchmark File Structure**
```
project_cache/benchmarks/
├── search_session_YYYYMMDD_HHMMSS.json      # Search-only tracking
├── pipeline_session_YYYYMMDD_HHMMSS.json    # Pipeline tracking
├── comprehensive_benchmarks.json            # Historical pipeline data
└── all_benchmarks.json                      # Legacy search data
```

### **Key Metrics Tracked**

**Performance Metrics:**
- Response times per phase and total pipeline
- Cache hit rates and optimization effectiveness
- API usage patterns and rate limiting efficiency

**Quality Metrics:**
- Data completeness percentage (fields extracted vs. total fields)
- Data quality scores (accuracy and confidence)
- Success rates by institution type

**Cost Metrics:**
- API call costs (search, LLM usage)
- Token usage optimization
- Cache efficiency ROI

**Operational Metrics:**
- Error rates and failure patterns
- Processing bottlenecks identification
- Scalability indicators

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
