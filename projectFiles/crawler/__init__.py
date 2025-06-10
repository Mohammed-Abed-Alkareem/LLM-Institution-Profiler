# Institution Profiler Web Crawler Module
# This module provides web crawling capabilities for institution data extraction

# Import configuration and basic classes first
from .crawler_config import CrawlerConfig, InstitutionType, CrawlingStrategy
from .content_processor import ContentProcessor
from .cache import CrawlerCache
from .benchmark import CrawlerBenchmarkTracker, CrawlerSessionBenchmark, CrawlerUrlBenchmark

# Import service classes last to avoid circular imports
from .crawler_service import CrawlerService, crawl_institution_simple

__all__ = [
    'CrawlerService',
    'crawl_institution_simple',
    'CrawlerConfig',
    'InstitutionType',
    'CrawlingStrategy',
    'ContentProcessor',
    'CrawlerBenchmarkTracker',
    'CrawlerSessionBenchmark', 
    'CrawlerUrlBenchmark',
    'CrawlerCache'
]
