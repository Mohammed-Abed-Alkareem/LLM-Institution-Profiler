# Institution Profiler Processing Pipeline

This module orchestrates the complete institution profiling pipeline through a modular, phase-based architecture. It integrates search, crawling, and extraction operations with comprehensive benchmarking and flexible content processing.

## 🚀 Features

### **Modular Pipeline Architecture**
- **Phase-Based Processing**: Cleanly separated search, crawling, and extraction phases
- **Flexible Execution**: Individual phases can be skipped or configured independently
- **Universal Content Processing**: Extraction phase accepts any text format from multiple sources
- **Intelligent Fallbacks**: Graceful degradation when services are unavailable
- **Comprehensive Error Handling**: Detailed error tracking and recovery mechanisms

### **Universal Extraction Capabilities**
- **Multi-Source Input**: Processes content from search results, crawled pages, or direct text input
- **Flexible Text Preparation**: Intelligently combines multiple content formats (HTML, markdown, structured data)
- **Content Prioritization**: Uses comprehensive crawled content when available, falls back to search descriptions
- **Format-Agnostic Processing**: Handles any text input format for LLM extraction
- **Smart Content Limits**: Optimizes content length for LLM processing while preserving structure

### **Advanced Integration**
- **Centralized Configuration**: Single configuration point for all pipeline settings
- **Service Factory Integration**: Dynamic service initialization and management
- **Benchmarking Integration**: Comprehensive performance tracking across all phases
- **Cache-Aware Processing**: Intelligent cache utilization with hit tracking
- **Quality Preservation**: Maintains crawled images, logos, and media through extraction process

### **Performance Optimization**
- **Cache Hit Tracking**: Accurate monitoring of search and crawler cache performance
- **Cost Management**: Token usage optimization and API cost tracking
- **Quality Scoring**: Content completeness and confidence assessment
- **Timing Analysis**: Detailed performance metrics for each pipeline phase
- **Resource Management**: Efficient memory and processing resource utilization

## 📁 Module Structure

```
processor/
├── __init__.py              # Module initialization and exports
├── config.py                # Pipeline configuration and constants
├── pipeline.py              # Main pipeline orchestrator
├── search_phase.py          # Search phase handler and management
├── crawling_phase.py        # Crawling phase handler and content processing
└── extraction_phase.py      # LLM extraction phase handler
```

## 🔄 Pipeline Workflow

### **Phase 1: Search Phase**
```python
# Executed by: search_phase.py
# Purpose: Find institution URLs and basic information
# Outputs: Links for crawling, initial descriptions, metadata
```

**Process Flow:**
1. **Institution Query Formation**: Creates targeted search queries based on institution name and type
2. **Search Execution**: Uses search service with intelligent caching
3. **Link Analysis**: Filters and prioritizes found URLs for crawling
4. **Cache Integration**: Tracks cache hits and performance metrics
5. **Quality Assessment**: Evaluates search result quality and relevance

**Key Features:**
- Intelligent query construction with institution type awareness
- Cache-aware search execution with hit rate tracking
- Link quality assessment and filtering
- Comprehensive metadata extraction from search results
- Fallback strategies for failed searches

### **Phase 2: Crawling Phase**
```python
# Executed by: crawling_phase.py  
# Purpose: Extract detailed content from websites
# Outputs: Rich content, images, logos, structured data
```

**Process Flow:**
1. **URL Processing**: Crawls prioritized URLs from search phase
2. **Content Extraction**: Comprehensive data collection using advanced crawler
3. **Image Analysis**: Processes and scores all images for institutional relevance
4. **Content Organization**: Structures crawled data for extraction processing
5. **Quality Evaluation**: Assesses content richness and institutional relevance

**Key Features:**
- Advanced image scoring system (0-6 scale) for institutional relevance
- Logo detection with confidence levels and institutional context
- Comprehensive content format preservation (HTML, markdown, structured data)
- Social media link aggregation and categorization
- Facility image identification and categorization

### **Phase 3: Extraction Phase**
```python
# Executed by: extraction_phase.py
# Purpose: Process content with LLM for structured data
# Outputs: Structured institution data, validation metrics
```

**Process Flow:**
1. **Content Preparation**: Intelligently combines multiple content sources
2. **Universal Processing**: Accepts any text format or content combination
3. **LLM Extraction**: Uses optimized prompts for structured data extraction
4. **Quality Assessment**: Evaluates extraction completeness and confidence
5. **Result Integration**: Merges extracted data while preserving crawled assets

**Key Features:**
- **Universal Input Processing**: Handles content from any source (search, crawling, direct input)
- **Intelligent Content Combination**: Merges HTML, markdown, and structured data optimally
- **Smart Content Limits**: Optimizes input length for LLM efficiency while preserving key information
- **Flexible Fallbacks**: Falls back to search descriptions when crawling is unavailable
- **Asset Preservation**: Maintains images, logos, and media found during crawling

## 🔧 Configuration

### **Pipeline Configuration (`config.py`)**
```python
# Institution type detection
INSTITUTION_TYPE_KEYWORDS = {
    'university': ['university', 'college', 'education', 'academic', 'school'],
    'hospital': ['hospital', 'medical', 'health', 'clinic', 'healthcare'],
    'bank': ['bank', 'banking', 'financial', 'finance', 'credit'],
    'general': []
}

# Content processing limits
CONTENT_LIMITS = {
    'max_images_per_institution': 20,
    'max_documents_per_institution': 15,
    'max_social_links_per_platform': 3,
    'min_text_length_for_extraction': 50
}

# Pipeline defaults
DEFAULT_MAX_LINKS = 15
DEFAULT_MAX_PAGES = 12
DEFAULT_CONTENT_LIMIT_PER_PAGE = 2000
DEFAULT_TOTAL_CONTENT_LIMIT = 8000
```

### **Processor Configuration Class**
```python
class ProcessorConfig:
    """Centralized configuration for the processing pipeline"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._openai_client = None
    
    def get_client(self) -> Optional[OpenAI]:
        """Get OpenAI client for LLM extraction"""
    
    def is_ai_available(self) -> bool:
        """Check if AI services are configured and available"""
```

## 🚀 Usage Examples

### **Complete Pipeline Execution**
```python
from processor import InstitutionPipeline
from service_factory import ServiceFactory

# Initialize services
services = ServiceFactory(base_dir="projectFiles")
pipeline = InstitutionPipeline(
    search_handler=services.search_service,
    crawler_service=services.crawler_service,
    processor_config=services.processor_config
)

# Execute full pipeline
result = pipeline.process_institution(
    institution_name="Harvard University",
    institution_type="university",
    enable_crawling=True,
    skip_extraction=False,
    benchmark_ctx=benchmark_context
)
```

### **Flexible Extraction Processing**
```python
# Extract from crawled content
extraction_result = pipeline._execute_extraction_phase(
    institution_name="MIT", 
    raw_text=comprehensive_crawled_content,
    skip_extraction=False,
    benchmark_ctx=context
)

# Extract from search results only
extraction_result = pipeline._execute_extraction_phase(
    institution_name="Stanford", 
    raw_text=search_description_text,
    skip_extraction=False,
    benchmark_ctx=context
)

# Extract from any text source
extraction_result = pipeline._execute_extraction_phase(
    institution_name="Custom Institution", 
    raw_text=any_text_content,
    skip_extraction=False,
    benchmark_ctx=context
)
```

### **Phase-Specific Execution**
```python
# Search phase only
search_result = pipeline._execute_search_phase(
    institution_name="Oxford University",
    institution_type="university", 
    search_params={},
    benchmark_ctx=context
)

# Crawling phase only
crawling_result = pipeline._execute_crawling_phase(
    institution_name="Cambridge University",
    crawling_links=search_result['crawling_links'],
    institution_type="university",
    benchmark_ctx=context
)
```

## 📊 Universal Content Processing

### **Text Preparation Algorithm**
The extraction phase uses an intelligent content preparation system:

1. **Comprehensive Content Assembly**: 
   - Combines cleaned HTML, markdown, and structured data from all crawled pages
   - Preserves page context and source attribution
   - Limits content per page while maintaining structure

2. **Content Prioritization**:
   - Uses comprehensive crawled content when available (up to 12,000 characters)
   - Falls back to total text summary (up to 8,000 characters)
   - Uses search description as final fallback

3. **Format Optimization**:
   - Structures content for optimal LLM processing
   - Preserves institutional context and metadata
   - Includes structured data and media references

### **Flexible Input Handling**
```python
def _prepare_text_for_extraction(self, final_result, crawling_result):
    """
    Universal text preparation that works with:
    - Full crawling results with multiple pages
    - Partial crawling results 
    - Search-only results
    - Direct text input
    - Any combination of the above
    """
```

## 📈 Performance & Quality Metrics

### **Pipeline Benchmarking**
Each phase tracks comprehensive metrics:

- **Search Phase**: Cache hits, API calls, search quality, timing
- **Crawling Phase**: Content quality, image scores, logo detection, processing time
- **Extraction Phase**: Field completion, token usage, confidence scores, extraction time

### **Quality Assessment**
- **Completeness Scoring**: Percentage of structured fields successfully extracted
- **Confidence Scoring**: LLM extraction reliability and data quality assessment
- **Content Utilization**: Efficiency of input content usage
- **Token Efficiency**: Optimal token usage for cost management

### **Cache Performance Tracking**
- **Search Cache Hits**: Accurate monitoring of search service cache utilization
- **Crawler Cache Hits**: Web content cache performance tracking
- **Cost Optimization**: Cache hit rate impact on API costs

## 🔗 Integration Points

### **Service Factory Integration**
```python
# Automatic service initialization
services = ServiceFactory(base_dir)
pipeline = services.get_pipeline()
```

### **Benchmarking Integration**
```python
# Automatic benchmark tracking
with BenchmarkContext(manager, benchmark_id) as ctx:
    result = pipeline.process_institution(..., benchmark_ctx=ctx)
```

### **Flask API Integration**
```python
# Direct endpoint integration
@app.route('/process')
def process_institution():
    pipeline = services.get_pipeline()
    return pipeline.process_institution(...)
```

## 🛠️ Development Guidelines

### **Adding New Phases**
1. Create new phase handler in `processor/` directory
2. Implement standard interface with benchmarking support
3. Integrate into main pipeline orchestrator
4. Add configuration options to `config.py`

### **Extending Content Processing**
1. Universal content processors should accept any text format
2. Implement intelligent fallbacks for missing data
3. Preserve existing assets during processing
4. Maintain benchmark compatibility

### **Performance Optimization**
1. Cache-aware processing for all external service calls
2. Content length optimization for LLM efficiency
3. Memory-efficient processing for large content
4. Comprehensive error handling and recovery

## 🔮 Future Enhancements

- **Parallel Phase Processing**: Multi-threaded execution for independent phases
- **Advanced Content Fusion**: ML-powered content combination and optimization
- **Real-time Quality Assessment**: Live content quality evaluation during processing
- **Custom Extraction Templates**: Institution-type specific extraction patterns
- **Progressive Enhancement**: Iterative quality improvement through multiple passes

## 📞 Support

The processor module integrates seamlessly with all Institution Profiler services and provides robust, flexible content processing for any institutional data source. For questions or issues, check the main application logs and individual phase handlers for detailed processing information.
