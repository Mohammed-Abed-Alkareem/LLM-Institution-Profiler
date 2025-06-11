"""
Institution Profiler Web Crawler Benchmarking Module

This module provides benchmarking and performance tracking capabilities
for the web crawler system, integrating with the existing benchmark infrastructure.
"""

import time
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid


@dataclass
class CrawlerUrlBenchmark:
    """Benchmark data for a single URL crawl operation with comprehensive data logging."""
    
    # Basic information
    url_benchmark_id: str
    session_id: str
    url: str
    timestamp: float
    
    # Performance metrics
    crawl_time: float = 0.0
    success: bool = False
    
    # Content metrics - Enhanced for comprehensive data tracking
    content_size_bytes: int = 0
    word_count: int = 0
    quality_score: float = 0.0
    
    # NEW: Comprehensive data type tracking for benchmarking
    data_types_extracted: Dict[str, Any] = None
    
    # NEW: Content format sizes for comparison
    content_format_sizes: Dict[str, int] = None
    
    # NEW: Media and asset counts for profiling
    media_counts: Dict[str, int] = None
    
    # NEW: Institution-specific data extracted
    institution_data_quality: Dict[str, Any] = None
    
    # Error information
    error: Optional[str] = None
    status_code: Optional[int] = None
    
    # NEW: Crawl4ai specific metrics
    crawl4ai_performance: Dict[str, Any] = None

    def __post_init__(self):
        if self.data_types_extracted is None:
            self.data_types_extracted = {}
        if self.content_format_sizes is None:
            self.content_format_sizes = {}
        if self.media_counts is None:
            self.media_counts = {}
        if self.institution_data_quality is None:
            self.institution_data_quality = {}
        if self.crawl4ai_performance is None:
            self.crawl4ai_performance = {}


@dataclass
class CrawlerSessionBenchmark:
    """Benchmark data for a complete crawling session."""
    
    # Basic information
    session_id: str
    institution_name: str
    institution_type: str
    timestamp: float
    
    # URLs and processing
    urls_requested: List[str]
    total_crawl_time: float = 0.0
    success: bool = False
    
    # Performance metrics
    urls_successful: int = 0
    urls_failed: int = 0
    cache_hits: int = 0
    api_calls: int = 0
    
    # Content metrics
    total_content_size_bytes: int = 0
    total_word_count: int = 0
    average_quality_score: float = 0.0
    
    # Timing breakdown
    url_benchmarks: List[CrawlerUrlBenchmark] = None
    
    # Domain analysis
    domains_crawled: Dict[str, int] = None
    
    # Error tracking
    errors: List[str] = None

    def __post_init__(self):
        if self.url_benchmarks is None:
            self.url_benchmarks = []
        if self.domains_crawled is None:
            self.domains_crawled = {}
        if self.errors is None:
            self.errors = []


class CrawlerBenchmarkTracker:
    """
    Tracker for crawler benchmarking that integrates with the existing benchmark system.
    """
    
    def __init__(self, benchmarks_dir: str):
        """Initialize the crawler benchmark tracker."""
        self.benchmarks_dir = benchmarks_dir
        self.ensure_benchmarks_directory()
        
        # Current session tracking
        self.active_sessions: Dict[str, CrawlerSessionBenchmark] = {}
        self.active_url_benchmarks: Dict[str, CrawlerUrlBenchmark] = {}
        
        # Session files
        self.session_filename = f"crawler_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.all_crawler_benchmarks_file = os.path.join(benchmarks_dir, "all_crawler_benchmarks.json")
        
        # Load existing benchmarks
        self.all_benchmarks = self._load_all_benchmarks()
    
    def ensure_benchmarks_directory(self):
        """Ensure the benchmarks directory exists."""
        if not os.path.exists(self.benchmarks_dir):
            os.makedirs(self.benchmarks_dir)
    
    def start_crawl_session(
        self, 
        institution_name: str, 
        institution_type: str, 
        urls: List[str]
    ) -> str:
        """
        Start a new crawling session benchmark.
        
        Args:
            institution_name: Name of the institution
            institution_type: Type of institution
            urls: List of URLs to crawl
            
        Returns:
            Session ID for tracking
        """
        session_id = f"crawl_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        session_benchmark = CrawlerSessionBenchmark(
            session_id=session_id,
            institution_name=institution_name,
            institution_type=institution_type,
            timestamp=time.time(),
            urls_requested=urls.copy()
        )
        
        self.active_sessions[session_id] = session_benchmark
        return session_id
    
    def start_url_crawl(self, session_id: str, url: str) -> str:
        """
        Start benchmarking for a single URL crawl.
        
        Args:
            session_id: The session this URL belongs to
            url: The URL being crawled
            
        Returns:
            URL benchmark ID for tracking
        """
        url_benchmark_id = f"url_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        url_benchmark = CrawlerUrlBenchmark(
            url_benchmark_id=url_benchmark_id,
            session_id=session_id,
            url=url,
            timestamp=time.time()
        )
        
        self.active_url_benchmarks[url_benchmark_id] = url_benchmark
        return url_benchmark_id
    
    def complete_url_crawl(
        self, 
        url_benchmark_id: str, 
        success: bool,
        crawl_time: float,
        content_size: int = 0,
        word_count: int = 0,
        quality_score: float = 0.0,
        status_code: Optional[int] = None,
        error: Optional[str] = None
    ):
        """
        Complete benchmarking for a single URL crawl.
        
        Args:
            url_benchmark_id: The URL benchmark ID
            success: Whether the crawl was successful
            crawl_time: Time taken to crawl
            content_size: Size of content in bytes
            word_count: Number of words in content
            quality_score: Quality score of content
            status_code: HTTP status code
            error: Error message if failed
        """
        if url_benchmark_id not in self.active_url_benchmarks:
            return
        
        url_benchmark = self.active_url_benchmarks[url_benchmark_id]
        
        # Update benchmark data
        url_benchmark.crawl_time = crawl_time
        url_benchmark.success = success
        url_benchmark.content_size_bytes = content_size
        url_benchmark.word_count = word_count
        url_benchmark.quality_score = quality_score
        url_benchmark.status_code = status_code
        url_benchmark.error = error
        
        # Add to session
        session_id = url_benchmark.session_id
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.url_benchmarks.append(url_benchmark)
            
            # Update session statistics
            if success:
                session.urls_successful += 1
                session.total_content_size_bytes += content_size
                session.total_word_count += word_count
            else:
                session.urls_failed += 1
                if error:
                    session.errors.append(f"{url_benchmark.url}: {error}")
        
        # Remove from active tracking
        del self.active_url_benchmarks[url_benchmark_id]
    
    def add_crawl_error(self, session_id: str, url: str, error: str):
        """
        Add an error to the crawling session.
        
        Args:
            session_id: The session ID
            url: The URL that failed
            error: Error message
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.errors.append(f"{url}: {error}")
    
    def complete_crawl_session(
        self, 
        session_id: str, 
        success: bool, 
        total_time: float
    ) -> Optional[CrawlerSessionBenchmark]:
        """
        Complete a crawling session benchmark.
        
        Args:
            session_id: The session ID
            success: Whether the overall session was successful
            total_time: Total time for the session
            
        Returns:
            The completed session benchmark
        """
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        # Update session data
        session.total_crawl_time = total_time
        session.success = success
        
        # Calculate average quality score
        if session.url_benchmarks:
            quality_scores = [url.quality_score for url in session.url_benchmarks if url.success]
            session.average_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            # Analyze domains
            from urllib.parse import urlparse
            for url_benchmark in session.url_benchmarks:
                domain = urlparse(url_benchmark.url).netloc
                session.domains_crawled[domain] = session.domains_crawled.get(domain, 0) + 1
        
        # Save to files
        self._save_session_benchmark(session)
        self._append_to_all_benchmarks(session)
        
        # Remove from active tracking
        del self.active_sessions[session_id]
        
        return session
    
    def _save_session_benchmark(self, session: CrawlerSessionBenchmark):
        """Save a session benchmark to its own file."""
        try:
            session_file = os.path.join(
                self.benchmarks_dir, 
                f"crawler_session_{session.session_id}.json"
            )
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(session), f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Error saving session benchmark: {e}")
    
    def _append_to_all_benchmarks(self, session: CrawlerSessionBenchmark):
        """Append session benchmark to the all benchmarks file."""
        try:
            # Convert to dict for JSON serialization
            session_dict = asdict(session)
            
            # Add to all benchmarks list
            self.all_benchmarks.append(session_dict)
            
            # Keep only recent benchmarks (last 1000)
            if len(self.all_benchmarks) > 1000:
                self.all_benchmarks = self.all_benchmarks[-1000:]
            
            # Save to file
            with open(self.all_crawler_benchmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_benchmarks, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Error saving to all benchmarks: {e}")
    
    def _load_all_benchmarks(self) -> List[Dict[str, Any]]:
        """Load all existing benchmarks."""
        try:
            if os.path.exists(self.all_crawler_benchmarks_file):
                with open(self.all_crawler_benchmarks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading benchmarks: {e}")
        
        return []
    
    def get_crawl_stats(self) -> Dict[str, Any]:
        """Get comprehensive crawling statistics."""
        try:
            if not self.all_benchmarks:
                return {
                    'total_sessions': 0,
                    'message': 'No crawling data available'
                }
            
            # Overall statistics
            total_sessions = len(self.all_benchmarks)
            successful_sessions = sum(1 for b in self.all_benchmarks if b.get('success', False))
            
            # URL statistics
            total_urls_crawled = sum(b.get('urls_successful', 0) + b.get('urls_failed', 0) for b in self.all_benchmarks)
            total_urls_successful = sum(b.get('urls_successful', 0) for b in self.all_benchmarks)
            
            # Performance statistics
            crawl_times = [b.get('total_crawl_time', 0) for b in self.all_benchmarks if b.get('total_crawl_time', 0) > 0]
            avg_crawl_time = sum(crawl_times) / len(crawl_times) if crawl_times else 0
            
            # Content statistics
            total_content_size = sum(b.get('total_content_size_bytes', 0) for b in self.all_benchmarks)
            quality_scores = [b.get('average_quality_score', 0) for b in self.all_benchmarks if b.get('average_quality_score', 0) > 0]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Institution type analysis
            institution_types = {}
            for benchmark in self.all_benchmarks:
                inst_type = benchmark.get('institution_type', 'unknown')
                institution_types[inst_type] = institution_types.get(inst_type, 0) + 1
            
            # Recent activity
            recent_benchmarks = sorted(
                self.all_benchmarks, 
                key=lambda x: x.get('timestamp', 0), 
                reverse=True
            )[:10]
            
            return {
                'total_sessions': total_sessions,
                'successful_sessions': successful_sessions,
                'success_rate_percent': (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                'total_urls_crawled': total_urls_crawled,
                'total_urls_successful': total_urls_successful,
                'url_success_rate_percent': (total_urls_successful / total_urls_crawled * 100) if total_urls_crawled > 0 else 0,
                'average_crawl_time_seconds': round(avg_crawl_time, 2),
                'total_content_size_mb': round(total_content_size / (1024 * 1024), 2),
                'average_quality_score': round(avg_quality, 2),
                'institution_types': institution_types,
                'recent_activity': [
                    {
                        'institution_name': b.get('institution_name', 'Unknown'),
                        'institution_type': b.get('institution_type', 'unknown'),
                        'timestamp': datetime.fromtimestamp(b.get('timestamp', 0)).isoformat(),
                        'urls_successful': b.get('urls_successful', 0),
                        'success': b.get('success', False)
                    }
                    for b in recent_benchmarks
                ]
            }
        
        except Exception as e:
            return {
                'error': f"Error generating stats: {str(e)}",
                'total_sessions': len(self.all_benchmarks) if self.all_benchmarks else 0
            }
    
    def get_recent_crawls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent crawling sessions."""
        try:
            recent = sorted(
                self.all_benchmarks, 
                key=lambda x: x.get('timestamp', 0), 
                reverse=True
            )[:limit]
            
            return [
                {
                    'session_id': b.get('session_id', 'unknown'),
                    'institution_name': b.get('institution_name', 'Unknown'),
                    'institution_type': b.get('institution_type', 'unknown'),
                    'timestamp': datetime.fromtimestamp(b.get('timestamp', 0)).isoformat(),
                    'success': b.get('success', False),
                    'urls_requested': len(b.get('urls_requested', [])),
                    'urls_successful': b.get('urls_successful', 0),
                    'urls_failed': b.get('urls_failed', 0),
                    'total_crawl_time': round(b.get('total_crawl_time', 0), 2),
                    'average_quality_score': round(b.get('average_quality_score', 0), 2),
                    'domains_crawled': b.get('domains_crawled', {})
                }
                for b in recent
            ]
        
        except Exception as e:
            return [{'error': f"Error getting recent crawls: {str(e)}"}]
    
    def get_institution_crawl_history(self, institution_name: str) -> List[Dict[str, Any]]:
        """Get crawling history for a specific institution."""
        try:
            institution_crawls = [
                b for b in self.all_benchmarks 
                if b.get('institution_name', '').lower() == institution_name.lower()
            ]
            
            return sorted(
                institution_crawls, 
                key=lambda x: x.get('timestamp', 0), 
                reverse=True
            )
        
        except Exception as e:
            return [{'error': f"Error getting institution history: {str(e)}"}]
    
    def clear_old_benchmarks(self, older_than_days: int = 30) -> Dict[str, Any]:
        """Clear benchmark data older than specified days."""
        try:
            current_time = time.time()
            cutoff_time = current_time - (older_than_days * 24 * 60 * 60)
            
            original_count = len(self.all_benchmarks)
            self.all_benchmarks = [
                b for b in self.all_benchmarks 
                if b.get('timestamp', 0) > cutoff_time
            ]
            removed_count = original_count - len(self.all_benchmarks)
            
            # Save updated benchmarks
            with open(self.all_crawler_benchmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_benchmarks, f, indent=2, ensure_ascii=False)
            
            # Clean up individual session files
            session_files_removed = 0
            try:
                for filename in os.listdir(self.benchmarks_dir):
                    if filename.startswith('crawler_session_') and filename.endswith('.json'):
                        file_path = os.path.join(self.benchmarks_dir, filename)
                        file_mtime = os.path.getmtime(file_path)
                        if file_mtime < cutoff_time:
                            os.remove(file_path)
                            session_files_removed += 1
            except Exception:
                pass
            
            return {
                'removed_benchmarks': removed_count,
                'remaining_benchmarks': len(self.all_benchmarks),
                'removed_session_files': session_files_removed,
                'cleanup_date': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'error': f"Error during cleanup: {str(e)}",
                'cleanup_date': datetime.now().isoformat()
            }
