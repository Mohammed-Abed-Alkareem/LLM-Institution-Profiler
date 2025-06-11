"""
Institution Profiler Web Crawler Service

This module provides the main crawler service for extracting content from institution websites
using crawl4ai. It includes intelligent caching, benchmarking, and content processing.
"""

import os
import json
import hashlib
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict
import time
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy

from .crawler_config import CrawlerConfig, InstitutionType, CrawlingStrategy
from .content_processor import ContentProcessor
from .cache import CrawlerCache
from .benchmark import CrawlerBenchmarkTracker

# Import cache config from parent directory
try:
    from cache_config import get_cache_config
except ImportError:
    print("Warning: Could not import cache_config, using fallback")
    def get_cache_config(base_dir):
        # Simple fallback cache config
        class FallbackCacheConfig:
            def __init__(self, base_dir):
                self.base_dir = base_dir
            def get_crawling_cache_dir(self):
                cache_dir = os.path.join(self.base_dir, 'project_cache', 'crawling_data')
                os.makedirs(cache_dir, exist_ok=True)
                return cache_dir
            def get_benchmarks_dir(self):
                bench_dir = os.path.join(self.base_dir, 'project_cache', 'benchmarks')
                os.makedirs(bench_dir, exist_ok=True)
                return bench_dir
        return FallbackCacheConfig(base_dir)


class CrawlerService:
    """
    Main crawler service for institution data extraction with intelligent caching and benchmarking.
    """
    
    def __init__(self, base_dir: str):
        """Initialize the crawler service with caching and benchmarking."""
        self.base_dir = base_dir
        
        # Set up cache configuration
        self.cache_config = get_cache_config(base_dir)
        self.cache = CrawlerCache(self.cache_config.get_crawling_cache_dir())
        
        # Set up benchmarking
        self.benchmark_tracker = CrawlerBenchmarkTracker(
            self.cache_config.get_benchmarks_dir()
        )
        
        # Content processor for cleaning and extracting relevant data
        self.content_processor = ContentProcessor()
        # Browser configuration for crawl4ai
        self.browser_config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            user_agent="Institution-Profiler-Bot/1.0",
            viewport_width=1920,
            viewport_height=1080,
            java_script_enabled=True,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        
        # Default crawler configuration
        self.default_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,  # We handle caching ourselves
            word_count_threshold=50,
            exclude_external_links=True,
            exclude_social_media_links=True,
            remove_overlay_elements=True,
            simulate_user=True,
            override_navigator=True,
            magic=True,  # Smart content extraction
            page_timeout=30000,  # 30 seconds
            delay_before_return_html=2.0,  # Wait for dynamic content
        )
    
    async def crawl_institution_urls(
        self, 
        institution_name: str,
        urls: List[str],
        institution_type: str = "general",
        max_pages: int = 10,
        strategy: CrawlingStrategy = CrawlingStrategy.ADVANCED,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Crawl multiple URLs for an institution with intelligent caching and content processing.
        
        Args:
            institution_name: Name of the institution
            urls: List of URLs to crawl
            institution_type: Type of institution (university, hospital, bank, etc.)
            max_pages: Maximum number of pages to crawl
            strategy: Crawling strategy to use
            force_refresh: Force refresh cached content
            
        Returns:
            Dictionary containing crawled content, metadata, and benchmarks
        """
        # Start benchmarking
        crawl_session_id = self.benchmark_tracker.start_crawl_session(
            institution_name, institution_type, urls[:max_pages]
        )
        
        start_time = time.time()
        results = {
            'institution_name': institution_name,
            'institution_type': institution_type,
            'crawl_session_id': crawl_session_id,
            'urls_requested': urls[:max_pages],
            'crawled_pages': [],
            'failed_urls': [],
            'total_content_size': 0,
            'processed_content_size': 0,
            'crawl_summary': {},
            'benchmark_data': {},
            'cache_hits': 0,
            'api_calls': 0        }
        
        try:
            # Configure crawler based on institution type and strategy
            try:
                institution_type_enum = InstitutionType(institution_type.lower())
            except (ValueError, AttributeError):
                # Default to GENERAL if the institution type is not recognized
                institution_type_enum = InstitutionType.GENERAL
                
            crawler_config = CrawlerConfig.for_institution_type(
                institution_type_enum, strategy
            )
            
            # Create the async crawler
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                
                # Process each URL
                for i, url in enumerate(urls[:max_pages]):
                    if i >= max_pages:
                        break
                    
                    try:
                        # Check cache first (unless force refresh)
                        cached_result = None
                        if not force_refresh:
                            cached_result = self.cache.get_cached_content(url)
                        
                        if cached_result and not force_refresh:
                            # Use cached content
                            results['cache_hits'] += 1
                            page_result = cached_result
                            
                            # Add cache metadata
                            page_result['cache_hit'] = True
                            page_result['crawl_time'] = 0.0
                        else:
                            # Crawl the URL
                            results['api_calls'] += 1
                            page_result = await self._crawl_single_url(
                                crawler, url, crawler_config, crawl_session_id
                            )
                            
                            # Cache the result if successful
                            if page_result.get('success', False):
                                self.cache.cache_content(url, page_result)
                        
                        # Process and add to results
                        if page_result.get('success', False):
                            results['crawled_pages'].append(page_result)
                            results['total_content_size'] += len(page_result.get('raw_html', ''))
                            results['processed_content_size'] += len(page_result.get('cleaned_content', ''))
                        else:
                            results['failed_urls'].append({
                                'url': url,
                                'error': page_result.get('error', 'Unknown error')
                            })
                    
                    except Exception as e:
                        # Handle individual URL errors
                        error_msg = f"Error crawling {url}: {str(e)}"
                        results['failed_urls'].append({
                            'url': url,
                            'error': error_msg
                        })
                        
                        # Track error in benchmark
                        self.benchmark_tracker.add_crawl_error(crawl_session_id, url, str(e))
        
        except Exception as e:
            # Handle session-level errors
            error_msg = f"Crawler session error: {str(e)}"
            results['session_error'] = error_msg
            
            # Complete benchmarking with error
            total_time = time.time() - start_time
            benchmark_data = self.benchmark_tracker.complete_crawl_session(
                crawl_session_id, success=False, total_time=total_time
            )
            results['benchmark_data'] = asdict(benchmark_data) if benchmark_data else {}
            
            return results
        
        # Process and analyze crawled content
        results['crawl_summary'] = self._generate_crawl_summary(results)
        
        # Complete benchmarking
        total_time = time.time() - start_time
        success = len(results['crawled_pages']) > 0
        benchmark_data = self.benchmark_tracker.complete_crawl_session(
            crawl_session_id, success=success, total_time=total_time
        )
        results['benchmark_data'] = asdict(benchmark_data) if benchmark_data else {}
        
        return results
    
    async def _crawl_single_url(
        self, 
        crawler: AsyncWebCrawler, 
        url: str, 
        config: CrawlerConfig,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Crawl a single URL with the specified configuration.
        
        Args:
            crawler: The AsyncWebCrawler instance
            url: URL to crawl
            config: Crawler configuration
            session_id: Benchmark session ID
            
        Returns:
            Dictionary containing the crawled content and metadata
        """
        start_time = time.time()
        
        try:
            # Start URL-level benchmarking
            url_benchmark_id = self.benchmark_tracker.start_url_crawl(session_id, url)
            
            # Configure crawl run based on institution type and strategy
            run_config = self._create_run_config(config)
            
            # Perform the crawl
            result = await crawler.arun(url=url, config=run_config)
            
            crawl_time = time.time() - start_time
            
            # Process the result
            if result.success:
                # Extract content using the content processor
                processed_content = self.content_processor.process_crawl_result(
                    result, config.institution_type
                )
                
                # Prepare the page result
                page_result = {
                    'success': True,
                    'url': url,
                    'title': result.metadata.get('title', ''),
                    'description': result.metadata.get('description', ''),
                    'status_code': result.status_code,
                    'crawl_time': crawl_time,
                    'timestamp': datetime.now().isoformat(),
                    'cache_hit': False,
                    
                    # Content data
                    'raw_html': result.html,
                    'cleaned_content': result.cleaned_html,
                    'markdown_content': result.markdown,
                    'extracted_content': result.extracted_content,
                    'links': result.links.get('internal', [])[:20],  # Limit links
                    'images': result.media.get('images', [])[:10],  # Limit images
                    
                    # Processed content
                    'processed_content': processed_content,
                    'content_quality_score': self.content_processor.calculate_quality_score(processed_content),
                    
                    # Metadata
                    'metadata': result.metadata,
                    'word_count': len(result.cleaned_html.split()) if result.cleaned_html else 0,
                    'size_bytes': len(result.html) if result.html else 0,
                }
                
                # Complete URL benchmark
                self.benchmark_tracker.complete_url_crawl(
                    url_benchmark_id, 
                    success=True,
                    crawl_time=crawl_time,
                    content_size=len(result.html) if result.html else 0,
                    word_count=page_result['word_count']
                )
                
                return page_result
            
            else:
                # Handle failed crawl
                error_msg = f"Crawl failed: {result.error_message}"
                
                # Complete URL benchmark with error
                self.benchmark_tracker.complete_url_crawl(
                    url_benchmark_id, 
                    success=False,
                    crawl_time=crawl_time,
                    error=error_msg
                )
                
                return {
                    'success': False,
                    'url': url,
                    'error': error_msg,
                    'status_code': result.status_code,
                    'crawl_time': crawl_time,
                    'timestamp': datetime.now().isoformat(),
                    'cache_hit': False
                }
        
        except Exception as e:
            crawl_time = time.time() - start_time
            error_msg = f"Exception during crawl: {str(e)}"
            
            return {
                'success': False,
                'url': url,
                'error': error_msg,
                'crawl_time': crawl_time,
                'timestamp': datetime.now().isoformat(),
                'cache_hit': False
            }
    def _create_run_config(self, config: CrawlerConfig) -> CrawlerRunConfig:
        """Create a CrawlerRunConfig based on the institution-specific configuration."""
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,  # We handle caching ourselves
            word_count_threshold=config.word_count_threshold,
            exclude_external_links=config.exclude_external_links,
            exclude_social_media_links=config.exclude_social_media_links,
            remove_overlay_elements=config.remove_overlay_elements,
            simulate_user=config.simulate_user,
            override_navigator=config.override_navigator,
            magic=True,  # Enable magic extraction
            page_timeout=config.page_timeout,
            delay_before_return_html=config.delay_before_return_html,
            screenshot=config.take_screenshot,
            pdf=False,  # We don't need PDF generation
        )
        
        # Add extraction strategy if specified
        if config.extraction_strategy:
            run_config.extraction_strategy = config.extraction_strategy
        
        return run_config
    
    def _generate_crawl_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the crawling session."""
        crawled_pages = results.get('crawled_pages', [])
        failed_urls = results.get('failed_urls', [])
        
        # Calculate statistics
        total_requested = len(results.get('urls_requested', []))
        total_successful = len(crawled_pages)
        total_failed = len(failed_urls)
        
        # Content statistics
        total_content_size = results.get('total_content_size', 0)
        processed_content_size = results.get('processed_content_size', 0)
        
        # Quality statistics
        quality_scores = [
            page.get('content_quality_score', 0) 
            for page in crawled_pages
        ]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Domain analysis
        domains = {}
        for page in crawled_pages:
            from urllib.parse import urlparse
            domain = urlparse(page['url']).netloc
            domains[domain] = domains.get(domain, 0) + 1
        
        # Performance statistics
        crawl_times = [page.get('crawl_time', 0) for page in crawled_pages]
        avg_crawl_time = sum(crawl_times) / len(crawl_times) if crawl_times else 0
        
        return {
            'total_urls_requested': total_requested,
            'successful_crawls': total_successful,
            'failed_crawls': total_failed,
            'success_rate': (total_successful / total_requested * 100) if total_requested > 0 else 0,
            'total_content_size_mb': round(total_content_size / (1024 * 1024), 2),
            'processed_content_size_mb': round(processed_content_size / (1024 * 1024), 2),
            'compression_ratio': (processed_content_size / total_content_size * 100) if total_content_size > 0 else 0,
            'average_quality_score': round(avg_quality_score, 2),
            'domains_crawled': domains,
            'average_crawl_time_seconds': round(avg_crawl_time, 2),
            'cache_hit_rate': (results.get('cache_hits', 0) / total_requested * 100) if total_requested > 0 else 0,
        }
    
    def get_cached_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached content for a specific URL."""
        return self.cache.get_cached_content(url)
    
    def clear_cache(self, older_than_days: int = 7) -> Dict[str, Any]:
        """Clear cache entries older than specified days."""
        return self.cache.clear_old_cache(older_than_days)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_cache_stats()
    
    def get_crawl_stats(self) -> Dict[str, Any]:
        """Get comprehensive crawling statistics."""
        return self.benchmark_tracker.get_crawl_stats()
    
    def get_recent_crawls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent crawling sessions."""
        return self.benchmark_tracker.get_recent_crawls(limit)


# Convenience function for simple crawling
async def crawl_institution_simple(
    institution_name: str,
    urls: List[str],
    base_dir: str,
    institution_type: str = "general",
    max_pages: int = 5
) -> Dict[str, Any]:
    """
    Simple function to crawl institution URLs without managing a service instance.
    
    Args:
        institution_name: Name of the institution
        urls: List of URLs to crawl
        base_dir: Base directory for caching and benchmarking
        institution_type: Type of institution
        max_pages: Maximum number of pages to crawl
        
    Returns:
        Crawling results dictionary
    """
    service = CrawlerService(base_dir)
    return await service.crawl_institution_urls(
        institution_name=institution_name,
        urls=urls,
        institution_type=institution_type,
        max_pages=max_pages,
        strategy=CrawlingStrategy.ADVANCED
    )
