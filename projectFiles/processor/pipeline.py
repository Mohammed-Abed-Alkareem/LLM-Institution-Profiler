# -*- coding: utf-8 -*-
"""
Main pipeline orchestrator for institution processing.
Coordinates all phases with comprehensive benchmarking and error handling.
"""
import time
from typing import Dict, Optional
from .config import ProcessorConfig
from .search_phase import SearchPhaseHandler
from .crawling_phase import CrawlingPhaseHandler
from .extraction_phase import ExtractionPhaseHandler
from extraction_logic import STRUCTURED_INFO_KEYS
from benchmarking.integration import get_benchmarking_manager, benchmark_context, BenchmarkCategory


class InstitutionPipeline:
    """Main pipeline orchestrator for comprehensive institution processing."""
    
    def __init__(self, base_dir: str, crawler_service):
        self.base_dir = base_dir
        self.config = ProcessorConfig(base_dir)
        self.benchmarking_manager = get_benchmarking_manager()
        
        # Initialize phase handlers
        self.search_handler = SearchPhaseHandler(base_dir)
        self.crawling_handler = CrawlingPhaseHandler(base_dir, crawler_service)
        self.extraction_handler = ExtractionPhaseHandler(self.config)
    
    def process_institution(
        self,
        institution_name: str,
        institution_type: Optional[str] = None,
        search_params: Optional[Dict] = None,
        skip_extraction: bool = False,
        enable_crawling: bool = True
    ) -> Dict:
        """
        Execute the complete institution processing pipeline.
        
        Args:
            institution_name: Name of the institution to process
            institution_type: Optional type of institution
            search_params: Search parameters
            skip_extraction: If True, skip LLM extraction
            enable_crawling: If True, perform comprehensive web crawling
            
        Returns:
            Complete structured data about the institution
        """
        # Initialize result structure
        final_result = self._initialize_result_structure(institution_name)
        
        if not institution_name:
            final_result["error"] = "No institution name provided."
            final_result["data_source_notes"] = "Processing aborted: No institution name."
            return final_result
        
        # Execute with or without benchmarking
        if self.benchmarking_manager:
            return self._execute_with_benchmarking(
                institution_name, institution_type, search_params,
                skip_extraction, enable_crawling, final_result
            )
        else:
            return self._execute_without_benchmarking(
                institution_name, institution_type, search_params,
                skip_extraction, enable_crawling, final_result
            )
    
    def _initialize_result_structure(self, institution_name: str) -> Dict:
        """Initialize the comprehensive result structure."""
        result = {key: "Unknown" for key in STRUCTURED_INFO_KEYS}
        result.update({
            "name": institution_name if institution_name else "Unknown",
            "description_raw": "N/A",
            "data_source_notes": "",
            "crawling_links": [],
            "crawling_config": {},
            "crawled_data": {},
            "images_found": [],
            "logos_found": [],
            "facility_images": [],
            "social_media_links": {},
            "documents_found": [],
            "comprehensive_content": {},
            "content_summary": {},
            "processing_phases": {
                "search": {"completed": False, "success": False},
                "crawling": {"completed": False, "success": False},
                "extraction": {"completed": False, "success": False}
            },
            "performance_metrics": {},
            "error": None
        })
        return result
    
    def _execute_with_benchmarking(
        self, institution_name, institution_type, search_params,
        skip_extraction, enable_crawling, final_result
    ):
        """Execute pipeline with benchmarking integration."""
        with benchmark_context(
            BenchmarkCategory.PIPELINE, 
            institution_name, 
            institution_type or 'general'
        ) as ctx:
            return self._execute_pipeline_phases(
                institution_name, institution_type, search_params,
                skip_extraction, enable_crawling, final_result, ctx
            )
    
    def _execute_without_benchmarking(
        self, institution_name, institution_type, search_params,
        skip_extraction, enable_crawling, final_result
    ):
        """Execute pipeline without benchmarking (fallback mode)."""
        return self._execute_pipeline_phases(
            institution_name, institution_type, search_params,
            skip_extraction, enable_crawling, final_result, None
        )
    
    def _execute_pipeline_phases(
        self, institution_name, institution_type, search_params,
        skip_extraction, enable_crawling, final_result, benchmark_ctx
    ):
        """Execute all pipeline phases with comprehensive error handling."""
        try:
            pipeline_start_time = time.time()
            
            # Phase 1: Search
            search_result = self._execute_search_phase(
                institution_name, institution_type, search_params, benchmark_ctx
            )
            
            final_result["processing_phases"]["search"] = {
                "completed": True,
                "success": search_result["success"],
                "time": search_result.get("search_time", 0)
            }
            
            if not search_result["success"]:
                final_result["error"] = search_result["error"]
                final_result["data_source_notes"] = "Error during search phase."
                if benchmark_ctx:
                    benchmark_ctx.record_quality(completeness_score=0.0, confidence_scores={'search_success': 0.0})
                return final_result
            
            # Update final result with search data
            self._merge_search_results(final_result, search_result)
            
            # Phase 2: Crawling (if enabled)
            crawling_result = None
            if enable_crawling and final_result["crawling_links"]:
                crawling_result = self._execute_crawling_phase(
                    institution_name, final_result["crawling_links"], 
                    institution_type, benchmark_ctx
                )
                
                final_result["processing_phases"]["crawling"] = {
                    "completed": True,
                    "success": crawling_result["success"],
                    "time": crawling_result.get("crawling_time", 0)
                }
                
                if crawling_result["success"]:
                    self._merge_crawling_results(final_result, crawling_result)
            
            # Phase 3: Extraction
            raw_text = self._prepare_text_for_extraction(final_result, crawling_result)
            extraction_result = self._execute_extraction_phase(
                institution_name, raw_text, skip_extraction, benchmark_ctx
            )
            
            final_result["processing_phases"]["extraction"] = {
                "completed": True,
                "success": extraction_result["success"],
                "time": extraction_result.get("extraction_time", 0),
                "skipped": extraction_result.get("skipped", False)
            }
            
            if extraction_result["success"] and not extraction_result.get("skipped"):
                self._merge_extraction_results(final_result, extraction_result)
            
            # Calculate final metrics
            pipeline_time = time.time() - pipeline_start_time
            final_result["performance_metrics"] = {
                "total_pipeline_time": pipeline_time,
                "phases_completed": sum(1 for phase in final_result["processing_phases"].values() if phase["completed"]),
                "overall_success": all(phase["success"] for phase in final_result["processing_phases"].values() if phase["completed"])
            }
            
            # Record final benchmarking metrics
            if benchmark_ctx:
                self._record_final_benchmark_metrics(benchmark_ctx, final_result, search_result, crawling_result, extraction_result)
            
            return final_result
            
        except Exception as e:
            final_result["error"] = f"Unexpected error in pipeline: {str(e)}"
            if benchmark_ctx:
                benchmark_ctx.record_quality(completeness_score=0.0, confidence_scores={'pipeline_success': 0.0})
            return final_result
    
    def _execute_search_phase(self, institution_name, institution_type, search_params, benchmark_ctx):
        """Execute the search phase with benchmarking."""
        search_result = self.search_handler.execute_search_phase(
            institution_name, institution_type, search_params
        )
        
        if benchmark_ctx and search_result["success"]:
            metadata = search_result.get("metadata", {})
            cache_hit = metadata.get("cache_hit", False)
            
            if not cache_hit:
                benchmark_ctx.record_cost(api_calls=1, service_type="google_search")
            
            benchmark_ctx.record_quality(
                completeness_score=min(100.0, len(search_result["links"]) * 6.67),
                confidence_scores={
                    'search_success': 1.0,
                    'cache_efficiency': 1.0 if cache_hit else 0.0,
                    'links_quality': min(1.0, len(search_result["links"]) / 10.0)
                }
            )
            
            benchmark_ctx.record_content(
                content_size=len(str(search_result)),
                structured_data_size=len(search_result["links"]) * 100
            )
        
        return search_result
    
    def _execute_crawling_phase(self, institution_name, links, institution_type, benchmark_ctx):
        """Execute the crawling phase with benchmarking."""
        crawling_result = self.crawling_handler.execute_crawling_phase(
            institution_name, links, institution_type
        )
        
        if benchmark_ctx and crawling_result["success"]:
            pages_crawled = crawling_result.get("pages_crawled", 0)
            successful_pages = crawling_result.get("successful_pages", 0)
            
            benchmark_ctx.record_cost(api_calls=pages_crawled, service_type="web_crawling")
            
            benchmark_ctx.record_quality(
                completeness_score=min(100.0, successful_pages * 8.33),
                confidence_scores={
                    'crawl_success_rate': successful_pages / max(pages_crawled, 1),
                    'content_depth': min(1.0, successful_pages / 10.0)
                }
            )
        
        return crawling_result
    
    def _execute_extraction_phase(self, institution_name, raw_text, skip_extraction, benchmark_ctx):
        """Execute the extraction phase with benchmarking."""
        extraction_result = self.extraction_handler.execute_extraction_phase(
            institution_name, raw_text, skip_extraction
        )
        
        if benchmark_ctx and extraction_result["success"] and not extraction_result.get("skipped"):
            benchmark_ctx.record_cost(api_calls=1, service_type="llm_extraction")
            
            benchmark_ctx.record_quality(
                completeness_score=extraction_result.get("completeness_score", 0),
                confidence_scores={
                    'extraction_success': 1.0 if not extraction_result.get("error") else 0.5,
                    'data_completeness': extraction_result.get("completeness_score", 0) / 100.0
                }
            )
        
        return extraction_result
    
    def _merge_search_results(self, final_result, search_result):
        """Merge search phase results into final result."""
        final_result["crawling_links"] = search_result["links"]
        final_result["crawling_config"] = search_result.get("crawling_config", {})
        final_result["description_raw"] = search_result.get("initial_description", "")
        final_result["data_source_notes"] = self.search_handler.get_search_summary(search_result)
    
    def _merge_crawling_results(self, final_result, crawling_result):
        """Merge crawling phase results into final result."""
        final_result["crawled_data"] = crawling_result["crawled_data"]
        content_summary = crawling_result["content_summary"]
        
        # Update with comprehensive crawled content
        final_result["images_found"] = content_summary.get("all_images", [])
        final_result["logos_found"] = content_summary.get("logos_found", [])
        final_result["facility_images"] = content_summary.get("facility_images", [])
        final_result["social_media_links"] = content_summary.get("social_media_links", {})
        final_result["documents_found"] = content_summary.get("documents_found", [])
        final_result["comprehensive_content"] = content_summary
        
        # Update data source notes
        stats = content_summary.get("statistics", {})
        final_result["data_source_notes"] += f" Augmented with comprehensive crawling: {stats.get('total_pages_crawled', 0)} pages."
    
    def _merge_extraction_results(self, final_result, extraction_result):
        """Merge extraction phase results into final result."""
        structured_data = extraction_result["structured_data"]
        
        # Merge extracted structured data
        for key in STRUCTURED_INFO_KEYS:
            if key in structured_data and structured_data[key] != "Unknown":
                final_result[key] = structured_data[key]
        
        # Update data source notes
        final_result["data_source_notes"] += f" {extraction_result.get('message', '')}"
        
        if extraction_result.get("error"):
            if final_result["error"]:
                final_result["error"] += f"; {extraction_result['error']}"
            else:
                final_result["error"] = extraction_result["error"]
        
        # Ensure name is properly set
        if structured_data.get("name") and structured_data["name"] != "Unknown":
            final_result["name"] = structured_data["name"]
    
    def _prepare_text_for_extraction(self, final_result, crawling_result):
        """Prepare the best available text for extraction."""
        # Use crawled content if available, otherwise fall back to search snippets
        if crawling_result and crawling_result.get("success"):
            content_summary = crawling_result.get("content_summary", {})
            total_text = content_summary.get("total_text", "")
            if total_text.strip():
                return total_text[:8000]  # Limit for LLM processing
        
        # Fall back to initial description from search
        return final_result.get("description_raw", "")
    
    def _record_final_benchmark_metrics(self, benchmark_ctx, final_result, search_result, crawling_result, extraction_result):
        """Record comprehensive final benchmark metrics."""
        # Calculate total content size
        total_content_size = len(str(final_result))
        if crawling_result:
            total_content_size += len(str(crawling_result.get("crawled_data", {})))
        
        benchmark_ctx.record_content(
            content_size=total_content_size,
            structured_data_size=len(str(final_result))
        )
        
        # Calculate overall completeness
        phases_completed = sum(1 for phase in final_result["processing_phases"].values() if phase["completed"])
        overall_success = final_result["performance_metrics"]["overall_success"]
        
        final_completeness = 0
        if extraction_result and not extraction_result.get("skipped"):
            final_completeness = extraction_result.get("completeness_score", 0)
        elif crawling_result and crawling_result.get("success"):
            final_completeness = 70.0  # Good crawling results
        elif search_result and search_result.get("success"):
            final_completeness = 50.0  # Basic search results
        
        benchmark_ctx.record_quality(
            completeness_score=final_completeness,
            confidence_scores={
                'overall_pipeline_success': 1.0 if overall_success else 0.5,
                'phases_completion_rate': phases_completed / 3.0
            }
        )
