# Institution Profiler Web Crawler Module

This module provides comprehensive web crawling capabilities for the Institution Profiler project using [crawl4ai](https://github.com/unclecode/crawl4ai). It integrates seamlessly with the existing search, caching, and benchmarking infrastructure.

## 🚀 Features

### **Comprehensive Data Collection**
- **ALL Content Formats**: Raw HTML, cleaned HTML, markdown (raw, fit_markdown, fit_html), and clean text extraction
- **Complete Media Capture**: Images, videos, audio with full metadata and intelligent logo detection
- **Full Link Preservation**: Internal, external links with complete details for analysis
- **Structured Data Extraction**: JSON-LD, microdata, RDFa, and all available structured formats
- **Rich Metadata**: Title, description, language, keywords, author, charset, viewport, and comprehensive page info
- **URL Extraction**: Comprehensive URL collection from all data formats including JSON-LD structured data
- **Performance Tracking**: Detailed benchmarking with costs, quality scores, timing, and format comparison metrics

### **Institution-Specific Intelligence**
- **Smart Type Detection**: Automatic institution recognition (university, hospital, bank, general)
- **Relevant Content Hints**: Institution-specific keyword detection and contact information extraction
- **Logo Detection**: Intelligent logo identification using multiple heuristics and image analysis
- **Quality Scoring**: Content richness assessment (0-100 scale) for benchmarking and comparison

### **Performance & Integration**
- **Async Web Crawling**: High-performance async crawling using crawl4ai and Playwright
- **Central Cache Integration**: Uses system-wide cache_config.py for consistency across modules
- **Comprehensive Benchmarking**: Detailed performance tracking integrated with main benchmark system
- **Flask API Integration**: RESTful endpoints for all crawling operations and cache management

### **Data Preservation Philosophy**
- **Maximum Data Retention**: Collect ALL valuable data formats for future analysis and benchmarking
- **Minimal Processing**: Focus on data collection and organization, not extraction (handled by other modules)
- **Format Comparison**: Multiple content formats preserved for effectiveness benchmarking
- **Quality Over Quantity**: Smart filtering to collect valuable data while discarding noise

## 📁 Module Structure

```
crawler/
├── __init__.py                 # Module exports
├── crawler_service.py          # Main crawler service
├── crawler_config.py           # Configuration classes
├── content_processor.py        # Content cleaning and extraction
├── cache.py                    # Caching functionality
└── benchmark.py               # Benchmarking and analytics
```

## 🛠️ Setup and Installation

### **Prerequisites**
Ensure you have the nlp environment activated:
```powershell
cd C:\Users\jihad\Desktop\nlp\LLM-Institution-Profiler
.\nlp\Scripts\Activate.ps1
```

### **Dependencies**
All dependencies are already installed:
- `crawl4ai` - Main crawling framework
- `playwright` - Browser automation (included with crawl4ai)
- Flask integration for API endpoints

### **Browser Setup**
Playwright browsers are automatically managed by crawl4ai. No manual setup required.

## 🔧 Configuration

### **Institution Types**
The crawler supports specialized configurations for:
- **Universities**: Enhanced academic content extraction
- **Hospitals**: Medical and healthcare-focused processing  
- **Banks**: Financial institution optimizations
- **General**: Default configuration for other organizations

### **Crawling Strategies**
- **Simple**: Basic content extraction, fast processing
- **Advanced**: JavaScript execution, dynamic content support
- **Comprehensive**: Multi-page crawling with screenshots

### **Example Configuration**
```python
from crawler import CrawlerService, CrawlingStrategy, InstitutionType

# Initialize crawler
crawler = CrawlerService(base_dir)

# Crawl with specific strategy
result = await crawler.crawl_institution_urls(
    institution_name="Harvard University",
    urls=["https://harvard.edu", "https://harvard.edu/about"],
    institution_type="university",
    strategy=CrawlingStrategy.ADVANCED,
    max_pages=5
)
```

## 🔄 Crawling Process & Workflow

### **Phase 1: Configuration & Setup**
1. **Institution Type Detection**: Automatic or manual specification of institution type
2. **Strategy Selection**: Choose crawling strategy based on content complexity
3. **Cache Check**: Verify if recent cached data exists (7-day default expiration)
4. **Benchmark Session Start**: Initialize tracking for performance monitoring

### **Phase 2: Intelligent Crawling**
1. **Browser Initialization**: Async Playwright browser with optimized settings
2. **Content Extraction**: Multiple format capture (HTML, markdown, structured data)
3. **Media Collection**: Image, video, audio detection with metadata
4. **Link Analysis**: Internal/external link categorization and preservation
5. **Screenshot Capture**: Visual page representation for analysis

### **Phase 3: Content Processing & Quality Assessment**
1. **Content Organization**: Structure all extracted data into standardized format
2. **Quality Scoring**: Comprehensive content richness evaluation (see scoring system below)
3. **Institution-Specific Analysis**: Extract relevant hints and contact information
4. **Logo Detection**: Multi-heuristic logo identification and URL extraction
5. **Benchmark Recording**: Performance metrics and content analysis logging

### **Phase 4: Caching & Response**
1. **Cache Storage**: Save processed results to central cache system
2. **Benchmark Completion**: Finalize session tracking with comprehensive metrics
3. **Response Generation**: Return structured data with all formats and analysis
4. **Statistics Update**: Update service-wide crawling statistics

## 📊 Quality Scoring System

### **Content Richness Score (0-100)**
The crawler uses a comprehensive scoring algorithm to evaluate content quality:

#### **Content Presence (40 points)**
- **Raw HTML Available** (10 pts): Basic page content extracted
- **Cleaned HTML Available** (10 pts): Processed, noise-free content
- **Markdown Available** (10 pts): Structured text representation
- **Substantial Content** (10 pts): Content length > 1000 characters

#### **Media Richness (30 points)**
- **Images Present** (10 pts): Visual content available
- **Videos Present** (10 pts): Video content detected
- **Rich Media Collection** (10 pts): 5+ images or multimedia content

#### **Metadata Quality (20 points)**
- **Page Title** (5 pts): Proper title tag present
- **Meta Description** (5 pts): SEO description available
- **Keywords** (5 pts): Meta keywords or structured keywords
- **Author Information** (5 pts): Content attribution data

#### **Structured Data (10 points)**
- **JSON-LD Data** (5 pts): Rich structured data available
- **Microdata/RDFa** (5 pts): Additional structured markup

### **Institution-Specific Quality Indicators**
- **Logo Detection Score**: Confidence level in identified logos
- **Contact Information**: Availability of institution contact details
- **Navigation Quality**: Link structure and internal organization
- **Content Relevance**: Institution-type specific keyword presence

### **Performance Scoring**
- **Crawl Speed**: Time efficiency vs. content quality ratio
- **Success Rate**: Successful extraction vs. attempted operations
- **Cache Efficiency**: Hit rate and storage optimization

## 🌐 API Endpoints

### **Main Crawling Endpoint**
```http
POST /crawl
Content-Type: application/json

{
  "institution_name": "Harvard University",
  "urls": ["https://harvard.edu", "https://harvard.edu/about"],
  "institution_type": "university", 
  "max_pages": 10,
  "force_refresh": false
}
```

### **Cache Management**
```http
GET /crawl/cache                    # Get cache statistics
GET /crawl/cache?url=<url>         # Get cached content for specific URL
POST /crawl/cache/clear             # Clear old cache entries
```

### **Statistics and Analytics**
```http
GET /crawl/stats                    # Comprehensive crawling statistics
GET /crawl/recent?limit=10          # Recent crawling sessions
```

### **Simple Crawling**
```http
POST /crawl/simple
Content-Type: application/json

{
  "institution_name": "MIT",
  "urls": ["https://mit.edu"],
  "institution_type": "university",
  "max_pages": 3
}
```

## 📋 Comprehensive Data Output Format

### **Standard Response Structure**
```json
{
  "institution_name": "Harvard University",
  "institution_type": "university",
  "crawl_session_id": "crawl_20241210_143022_abc123",
  "urls_requested": ["https://harvard.edu"],
  "crawled_pages": [...],
  "crawl_summary": {...},
  "benchmark_data": {...},
  "cache_hits": 2,
  "api_calls": 3
}
```

### **Individual Page Data Structure**
Each crawled page includes ALL available data formats:

```json
{
  "url": "https://harvard.edu",
  "success": true,
  "timestamp": "2024-12-10T14:30:22",
  "institution_type": "university",
  
  "content_formats": {
    "raw_html": "<!DOCTYPE html>...",
    "cleaned_html": "<div>...",
    "markdown": {
      "raw_markdown": "# Harvard University\n...",
      "fit_markdown": "Harvard University...",
      "fit_html": "<p>Harvard University...</p>",
      "primary_content": "Harvard University is..."
    },
    "text_content": "Harvard University is a private Ivy League..."
  },
  
  "media": {
    "images": [
      {
        "src": "https://harvard.edu/logo.png",
        "alt": "Harvard University Logo",
        "width": 200,
        "height": 100
      }
    ],
    "videos": [...],
    "audio": [...],
    "all_media": {...}
  },
  
  "links": {
    "internal": ["https://harvard.edu/about", ...],
    "external": ["https://external-site.com", ...],
    "all_links": {...}
  },
  
  "structured_data": {
    "json_ld": [
      {
        "@type": "EducationalOrganization",
        "name": "Harvard University",
        "url": "https://harvard.edu"
      }
    ],
    "microdata": {...},
    "rdfa": {...}
  },
  
  "content_analysis": {
    "sizes": {
      "raw_html_size": 45231,
      "cleaned_html_size": 23456,
      "markdown_size": 12345,
      "text_length": 8765
    },
    "counts": {
      "images_count": 15,
      "videos_count": 2,
      "internal_links_count": 45,
      "external_links_count": 12
    },
    "quality_indicators": {
      "has_title": true,
      "has_description": true,
      "has_images": true,
      "has_structured_data": true,
      "content_richness_score": 85
    }
  },
  
  "logos": [
    {
      "url": "https://harvard.edu/logo.png",
      "confidence": 0.95,
      "detection_method": "alt_text_logo"
    }
  ],
  
  "institution_hints": {
    "contact_emails": ["info@harvard.edu"],
    "phone_numbers": ["+1-617-495-1000"],
    "addresses": ["Cambridge, MA 02138"],
    "relevant_keywords": ["university", "education", "harvard"]
  }
}
```

### **Benchmark Data Structure**
Comprehensive performance tracking for analysis:

```json
{
  "session_id": "crawl_20241210_143022_abc123",
  "institution_name": "Harvard University",
  "institution_type": "university",
  "total_time": 12.45,
  "success": true,
  "performance_metrics": {
    "urls_processed": 3,
    "successful_crawls": 3,
    "failed_crawls": 0,
    "cache_hits": 1,
    "total_content_size": 123456,
    "average_quality_score": 87.3,
    "crawl_speeds": [2.1, 3.4, 2.8]
  },
  "content_analysis": {
    "total_images": 45,
    "total_videos": 5,
    "logos_found": 3,
    "structured_data_pages": 2,
    "format_comparison": {
      "markdown_vs_html_efficiency": 0.85,
      "text_extraction_quality": 0.92
    }
  }
}
```

## 📊 Response Format

### **Successful Crawl Response**
```json
{
  "success": true,
  "data": {
    "institution_name": "Harvard University",
    "institution_type": "university",
    "crawl_session_id": "crawl_1234567890_abc123",
    "urls_requested": ["https://harvard.edu"],
    "crawled_pages": [
      {
        "success": true,
        "url": "https://harvard.edu",
        "title": "Harvard University",
        "crawl_time": 2.34,
        "content_quality_score": 85.5,
        "processed_content": {
          "key_information": {
            "relevant_keywords_found": ["university", "education", "research"],
            "contact_information": {
              "emails": ["info@harvard.edu"],
              "phones": ["617-495-1000"]
            }
          }
        }
      }
    ],
    "crawl_summary": {
      "success_rate": 100,
      "average_quality_score": 85.5,
      "total_content_size_mb": 1.2,
      "cache_hit_rate": 0
    },
    "benchmark_data": {
      "total_crawl_time": 2.5,
      "urls_successful": 1,
      "urls_failed": 0
    }
  }
}
```

## 📊 Comprehensive Data Output

### **All Content Formats Preserved**
The crawler captures and preserves ALL valuable data formats from crawl4ai for benchmarking and analysis:

```json
{
  "content_formats": {
    "raw_html": "Complete original HTML",
    "cleaned_html": "Noise-filtered HTML", 
    "markdown": {
      "raw_markdown": "Basic markdown conversion",
      "fit_markdown": "Optimized markdown format",
      "fit_html": "Hybrid HTML-markdown format",
      "primary_content": "Best markdown representation"
    },
    "text_content": "Clean text extraction"
  },
  "media": {
    "images": ["Full image metadata with src, alt, dimensions"],
    "videos": ["Video content details"],
    "audio": ["Audio file information"],
    "all_media": "Complete media object from crawl4ai"
  },
  "links": {
    "internal": ["Internal site links"],
    "external": ["External site links"], 
    "all_links": "Complete links object from crawl4ai"
  },
  "structured_data": "JSON-LD, microdata, RDFa schemas",
  "metadata": "Complete page metadata (title, description, keywords, etc.)",
  "logos": ["Detected institution logos with confidence scores"],
  "content_analysis": {
    "sizes": "Content size metrics for all formats",
    "counts": "Image, link, and media counts",
    "quality_indicators": "Content richness assessment"
  }
}
```

### **Institution-Specific Hints**
Minimal processing to provide useful context for other modules:

```json
{
  "institution_hints": {
    "institution_type": "university|hospital|bank|general",
    "detected_keywords": ["relevant", "institution", "keywords"],
    "contact_indicators": ["phone", "email", "address"],
    "social_media_present": true
  }
}
```

## 🔍 Content Processing

### **University Content Extraction**
- Student enrollment numbers
- Faculty counts
- Founded year
- Academic programs
- Research information

### **Hospital Content Extraction**
- Bed counts
- Medical specialties
- Patient services
- Department information
- Healthcare facilities

### **Bank Content Extraction**
- Total assets
- Branch locations
- Financial services
- Corporate information
- Investment products

### **Quality Scoring**
Content quality is scored (0-100) based on:
- **Word count** (0-30 points)
- **Content density** (0-20 points)
- **Contact information** (0-20 points)
- **Structured data** (0-15 points)
- **Keyword relevance** (0-15 points)

## 📈 Performance Optimization

### **Caching Strategy**
- URL-based cache keys using SHA256 hashes
- 7-day default cache expiration
- Cache hit rate tracking
- Automatic cleanup of expired entries

### **Rate Limiting**
- Configurable delays between requests
- Anti-bot detection avoidance
- Human-like browsing patterns
- Respectful crawling practices

### **Content Optimization**
- HTML noise removal (nav, footer, ads)
- Content compression and cleaning
- Duplicate content detection
- Relevance-based filtering

## 📈 Comprehensive Benchmarking & Analytics

### **Detailed Performance Tracking**
The crawler provides extensive benchmarking data for analysis and optimization:

- **Timing Metrics**: Total crawl time, per-URL timing, cache vs API performance
- **Quality Scores**: Content richness (0-100), institution relevance, data completeness
- **Cost Analysis**: Cache hit rates, API call counts, bandwidth usage
- **Content Analysis**: Format sizes, compression ratios, data type extraction counts
- **Error Tracking**: Failed URLs, timeout issues, processing errors with detailed context
- **Institution Intelligence**: Type detection accuracy, relevant data extraction effectiveness

### **URL Extraction Excellence**
Smart URL discovery from multiple sources:

- **HTML Links**: Standard `<a>` tag extraction with context analysis
- **JSON-LD Structured Data**: Organization URLs, social media profiles, contact pages
- **Microdata & RDFa**: Schema.org URL properties and relationships
- **Meta Tags**: Canonical URLs, alternate versions, related resources
- **Content Analysis**: In-text URL patterns and references

### **Benchmark Data Structure**
```json
{
  "session_benchmark": {
    "timing": {
      "total_crawl_time": 15.34,
      "average_per_url": 3.07,
      "cache_vs_api_ratio": 0.4
    },
    "quality_metrics": {
      "average_content_score": 87.5,
      "institution_relevance": 92.1,
      "data_completeness": 78.3
    },
    "cost_analysis": {
      "cache_hit_rate": 40.0,
      "api_calls_made": 3,
      "bandwidth_mb": 2.4
    },
    "content_breakdown": {
      "html_compression_ratio": 23.1,
      "format_sizes": {
        "raw_html": 1024576,
        "cleaned_html": 235890,
        "markdown": 89123
      },
      "data_types_extracted": {
        "images": 15,
        "logos": 2,
        "structured_data_items": 8
      }
    }
  }
}
```

## 🔗 Integration

### **With Search Module**
```python
# Get URLs from search, then crawl them
search_data = get_institution_links_for_crawling("Harvard", "university", 10)
crawl_result = await crawler.crawl_institution_urls(
    "Harvard University",
    search_data['links'],
    "university"
)
```

### **With Pipeline Processing**
```python
# Complete pipeline with crawling
pipeline_result = process_institution_pipeline(
    "Harvard University", 
    "university",
    search_params={},
    skip_extraction=False  # Will use crawled data for extraction
)
```

### **With Benchmarking**
All crawling activities are automatically tracked in the centralized benchmarking system alongside search and LLM processing metrics.

## 🧪 Testing

### **Quick Test**
```powershell
# Navigate to project directory
cd C:\Users\jihad\Desktop\nlp\LLM-Institution-Profiler\projectFiles

# Activate environment
..\nlp\Scripts\Activate.ps1

# Start the Flask application
python app.py
```

### **Test API Endpoint**
```powershell
# Test simple crawling
curl -X POST http://localhost:5000/crawl/simple `
  -H "Content-Type: application/json" `
  -d '{
    "institution_name": "MIT",
    "urls": ["https://web.mit.edu"],
    "institution_type": "university",
    "max_pages": 2
  }'
```

### **Check Cache and Stats**
```powershell
# Get crawler statistics
curl http://localhost:5000/crawl/stats

# Get cache information
curl http://localhost:5000/crawl/cache
```

## 🚨 Error Handling

### **Common Issues**
- **Timeout errors**: Increase `page_timeout` in configuration
- **JavaScript errors**: Enable `java_script_enabled` for dynamic sites
- **Rate limiting**: Increase `delay_between_requests`
- **Memory issues**: Reduce `max_pages` or enable content filtering

### **Debugging**
- Check crawler logs in Flask console
- Use `/crawl/stats` endpoint for performance analysis
- Review cache statistics with `/crawl/cache`
- Monitor benchmark data for pattern analysis

## 📋 Cache Management

### **Cache Structure**
```
project_cache/crawling_data/
├── url_abc123def456.json    # Cached content for specific URLs
├── url_789ghi012jkl.json
└── ...
```

### **Cache Statistics**
- **Hit rate**: Percentage of requests served from cache
- **Total size**: Cache storage usage
- **File count**: Number of cached URLs
- **Age analysis**: Oldest and newest cache entries

### **Cache Cleanup**
```powershell
# Clear cache older than 7 days
curl -X POST http://localhost:5000/crawl/cache/clear

# Clear cache older than 3 days
curl -X POST "http://localhost:5000/crawl/cache/clear?older_than_days=3"
```

## 🔮 Future Enhancements

- **Parallel crawling**: Multi-threaded URL processing
- **Content deduplication**: Advanced similarity detection
- **Custom extraction rules**: User-defined content selectors
- **Crawl depth control**: Multi-level site crawling
- **Content archiving**: Long-term content storage
- **Machine learning optimization**: AI-powered crawling strategies

## 📞 Support

For issues or questions:
1. Check the Flask application logs
2. Review the `/crawl/stats` endpoint for performance data
3. Examine cache statistics with `/crawl/cache`
4. Test with the simple endpoint first: `/crawl/simple`

The crawler integrates seamlessly with your existing institution profiler pipeline and provides robust, efficient web content extraction for all institution types.
