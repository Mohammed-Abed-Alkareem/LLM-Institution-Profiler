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
from benchmarking.quality_score_integration import quality_integrator


class InstitutionPipeline:
	"""Main pipeline orchestrator for comprehensive institution processing."""
	def __init__(self, base_dir: str, crawler_service, search_service=None):
		self.base_dir = base_dir
		self.config = ProcessorConfig(base_dir)
		self.benchmarking_manager = get_benchmarking_manager()
		# Initialize phase handlers
		self.search_handler = SearchPhaseHandler(base_dir, search_service)
		self.crawling_handler = CrawlingPhaseHandler(base_dir, crawler_service)        
		self.extraction_handler = ExtractionPhaseHandler(self.config)
	def process_institution(
		self,
		institution_name: str,
		institution_type: Optional[str] = None,
		search_params: Optional[Dict] = None,
		skip_extraction: bool = False,
		enable_crawling: bool = True,
		output_type: str = "markdown",
		crawler_config: Optional[Dict] = None,
		force_refresh: bool = False
	) -> Dict:
		"""
		Execute the complete institution processing pipeline.
		
		Args:
			institution_name: Name of the institution to process
			institution_type: Optional type of institution
			search_params: Search parameters
			skip_extraction: If True, skip LLM extraction
			enable_crawling: If True, perform comprehensive web crawling
			output_type: Content format to use ("markdown", "raw_html", "cleaned_html", "text")
			
		Returns:
			Complete structured data about the institution        """
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
				skip_extraction, enable_crawling, final_result, output_type,
				crawler_config, force_refresh
			)
		else:
			return self._execute_without_benchmarking(
				institution_name, institution_type, search_params,
				skip_extraction, enable_crawling, final_result, output_type,
				crawler_config, force_refresh
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
			"extraction_metrics": {},  # Add extraction metrics to final result
			"error": None        })
		return result
	def _execute_with_benchmarking(
		self, institution_name, institution_type, search_params,
		skip_extraction, enable_crawling, final_result, output_type,
		crawler_config, force_refresh
	):
		"""Execute pipeline with benchmarking integration."""
		with benchmark_context(
			BenchmarkCategory.PIPELINE, 
			institution_name, 
			institution_type or 'general'
		) as ctx:			return self._execute_pipeline_phases(
				institution_name, institution_type, search_params,
				skip_extraction, enable_crawling, final_result, ctx, output_type,
				crawler_config, force_refresh
			)	
	def _execute_without_benchmarking(
		self, institution_name, institution_type, search_params,
		skip_extraction, enable_crawling, final_result, output_type,
		crawler_config, force_refresh
	):
		"""Execute pipeline without benchmarking (fallback mode)."""		
		return self._execute_pipeline_phases(
			institution_name, institution_type, search_params,
			skip_extraction, enable_crawling, final_result, None, output_type,
			crawler_config, force_refresh
        )
	def _execute_pipeline_phases(
		self, institution_name, institution_type, search_params,
		skip_extraction, enable_crawling, final_result, benchmark_ctx, output_type,
		crawler_config, force_refresh
	):
		"""Execute all pipeline phases with comprehensive error handling."""
		try:
			pipeline_start_time = time.time()
					# Phase 1: Search
			search_result = self._execute_search_phase(
				institution_name, institution_type, search_params, benchmark_ctx, crawler_config
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
					institution_type, benchmark_ctx, force_refresh
				)

				final_result["processing_phases"]["crawling"] = {
					"completed": True,
					"success": crawling_result["success"],
					"time": crawling_result.get("crawling_time", 0)
				}
				
				if crawling_result["success"]:
					self._merge_crawling_results(final_result, crawling_result)
			# Phase 3: Extraction
			raw_text = self._prepare_text_for_extraction(final_result, crawling_result, output_type)
			extraction_result = self._execute_extraction_phase(
				institution_name, raw_text, skip_extraction, benchmark_ctx
			)
			# Get extraction time from extraction_metrics if available
			extraction_time = extraction_result.get("extraction_time", 0)
			if not extraction_time and extraction_result.get("structured_data", {}).get("extraction_metrics"):
				extraction_time = extraction_result["structured_data"]["extraction_metrics"].get("extraction_time", 0)
			
			final_result["processing_phases"]["extraction"] = {
				"completed": True,
				"success": extraction_result["success"],
				"time": extraction_time,
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
			
			# Calculate information quality score after all phases complete
			self._calculate_and_attach_quality_score(final_result)
			
			# Record final benchmarking metrics
			if benchmark_ctx:
				self._record_final_benchmark_metrics(benchmark_ctx, final_result, search_result, crawling_result, extraction_result)
				# Attach benchmark metrics to final result
				self._attach_benchmark_metrics(benchmark_ctx, final_result)
			
			return final_result
			
		except Exception as e:
			final_result["error"] = f"Unexpected error in pipeline: {str(e)}"
			if benchmark_ctx:
				benchmark_ctx.record_quality(completeness_score=0.0, confidence_scores={'pipeline_success': 0.0})            
				return final_result
	def _execute_search_phase(self, institution_name, institution_type, search_params, benchmark_ctx, crawler_config=None):
		"""Execute the search phase with benchmarking."""
		search_result = self.search_handler.execute_search_phase(
			institution_name, institution_type, search_params, crawler_config=crawler_config
		)
		
		if benchmark_ctx:
			metadata = search_result.get("metadata", {})
			cache_hit = metadata.get("cache_hit", False)
			search_time = search_result.get("search_time", 0)
			# Record search phase latency with cache hit information
			if search_time > 0:
				benchmark_ctx.manager.record_latency(
					benchmark_ctx.benchmark_id, 
					"search", 
					search_time,
					cache_hit=cache_hit
				)
			
			if search_result["success"]:
				# Record API costs (only if not cached)
				if not cache_hit:
					api_calls = metadata.get("total_api_calls", 1)
					benchmark_ctx.record_cost(api_calls=api_calls, service_type="google_search")
				
				# Calculate quality scores based on actual results
				num_links = len(search_result["links"])
				links_quality = min(1.0, num_links / 15.0) if num_links > 0 else 0.0
				completeness = min(100.0, num_links * 6.67)
				
				benchmark_ctx.record_quality(
					completeness_score=completeness,
					confidence_scores={
						'search_success': 1.0,
						'cache_efficiency': 1.0 if cache_hit else 0.8,
						'links_quality': links_quality,                        
						'query_relevance': metadata.get("query_relevance_score", 0.8)
					}
				)
				# Record content metrics
				total_snippet_length = sum(len(link.get("snippet", "")) for link in search_result["links"])
				benchmark_ctx.record_content(
					content_size=total_snippet_length,
					word_count=num_links * 20,  # Estimate 20 words per link description
					structured_data_size=num_links * 150  # Average link metadata size
				)
			else:
				# Record failure metrics
				benchmark_ctx.record_quality(
					completeness_score=0.0,
					confidence_scores={
						'search_success': 0.0,
						'error_severity': 1.0 if "critical" in str(search_result.get("error", "")).lower() else 0.5
					}
				)
		
		return search_result	
	def _execute_crawling_phase(self, institution_name, links, institution_type, benchmark_ctx, force_refresh=False):
		"""Execute the crawling phase with benchmarking."""
		crawling_result = self.crawling_handler.execute_crawling_phase(
			institution_name, links, institution_type, force_refresh=force_refresh
		)
		if benchmark_ctx:
			crawling_time = crawling_result.get("crawling_time", 0)
			pages_crawled = crawling_result.get("pages_crawled", 0)
			successful_pages = crawling_result.get("successful_pages", 0)            
			# Record crawling phase latency specifically
			if crawling_time > 0:
				# Calculate success rate first (needed for quality metrics)
				success_rate = successful_pages / max(pages_crawled, 1)
				
				benchmark_ctx.manager.record_latency(
					benchmark_ctx.benchmark_id, 
					"crawling", 
					crawling_time
				)
				
				# Also record using the tracker method for proper integration
				benchmark_ctx.manager.tracker.add_crawling_metrics(
					pipeline_id=benchmark_ctx.benchmark_id,
					crawling_time=crawling_time,
					pages_crawled=pages_crawled,
					pages_successful=successful_pages,
					total_content_size=len(str(crawling_result.get("crawled_data", {}))),
					content_quality=success_rate
				)
			
			if crawling_result["success"]:
				# Record API costs based on actual pages crawled
				benchmark_ctx.record_cost(api_calls=pages_crawled, service_type="web_crawling")
				
				# Calculate quality scores based on success rates and content depth
				if crawling_time == 0:  # If not calculated above
					success_rate = successful_pages / max(pages_crawled, 1)
				content_depth = min(1.0, successful_pages / 12.0)
				completeness = min(100.0, successful_pages * 8.33)
				
				# Extract content metrics from crawled data
				content_summary = crawling_result.get("content_summary", {})
				total_text_length = len(content_summary.get("total_text", ""))
				total_images = len(content_summary.get("all_images", []))
				social_links = len(content_summary.get("social_media_links", {}))
				
				benchmark_ctx.record_quality(
					completeness_score=completeness,
					confidence_scores={
						'crawl_success_rate': success_rate,
						'content_depth': content_depth,
						'content_richness': min(1.0, (total_images + social_links) / 20.0),
						'text_extraction_quality': min(1.0, total_text_length / 10000.0)
					}
				)
				  # Record detailed content metrics
				crawled_data = crawling_result.get("crawled_data", {})
				benchmark_ctx.record_content(
					content_size=len(str(crawled_data)),
					structured_data_size=len(str(content_summary)),
					word_count=total_text_length // 5,  # Estimate words from character count
					media_count=total_images
				)
			else:
				# Record failure metrics
				benchmark_ctx.record_quality(
					completeness_score=0.0,
					confidence_scores={
						'crawl_success_rate': 0.0,
						'error_recovery': 0.5 if pages_crawled > 0 else 0.0
					}
				)
		
		return crawling_result
	def _execute_extraction_phase(self, institution_name, raw_text, skip_extraction, benchmark_ctx):
		"""Execute the extraction phase with benchmarking."""        
		extraction_result = self.extraction_handler.execute_extraction_phase(
			institution_name, raw_text, skip_extraction
		)
		if benchmark_ctx:
			# Get extraction time from extraction_metrics (real LLM processing time)
			structured_data = extraction_result.get("structured_data", {})
			extraction_metrics = structured_data.get("extraction_metrics", {})
			extraction_time = extraction_metrics.get("extraction_time", 0)
			
			# Record extraction phase latency specifically
			if extraction_time > 0:
				benchmark_ctx.manager.record_latency(
					benchmark_ctx.benchmark_id, 
					"llm", 
					extraction_time
				)
			if extraction_result["success"] and not extraction_result.get("skipped"):
				# Get extraction metrics from the LLM response
				structured_data = extraction_result.get("structured_data", {})
				extraction_metrics = structured_data.get("extraction_metrics", {})
				  # Record actual LLM costs with real token usage
				if extraction_metrics.get("total_tokens", 0) > 0:
					benchmark_ctx.record_cost(
						api_calls=1, 
						input_tokens=extraction_metrics.get("input_tokens", 0),
						output_tokens=extraction_metrics.get("output_tokens", 0),
						service_type="gemini_flash"  # Use Gemini pricing
					)
				else:
					# Fallback for cases where metrics weren't captured
					benchmark_ctx.record_cost(api_calls=1, service_type="llm_extraction")
				
				# Get actual completeness score from extraction
				completeness = extraction_result.get("completeness_score", 0)
				
				# Calculate field completion rates
				total_fields = len(STRUCTURED_INFO_KEYS)
				filled_fields = sum(
					1 for key in STRUCTURED_INFO_KEYS 
					if structured_data.get(key) and structured_data[key] not in ["Unknown", "", None]
				)
				field_completion_rate = filled_fields / total_fields
				
				# Calculate content utilization
				input_length = len(raw_text)
				content_utilization = min(1.0, input_length / 8000.0) if input_length > 0 else 0.0
				
				# Calculate LLM confidence based on extraction metrics
				llm_confidence = 0.8  # Default
				if extraction_metrics.get("success"):
					llm_confidence = 0.9
					if extraction_metrics.get("extraction_time", 0) < 3.0:  # Fast response
						llm_confidence = 0.95
				
				benchmark_ctx.record_quality(
					completeness_score=completeness,
					confidence_scores={
						'extraction_success': 1.0 if not extraction_result.get("error") else 0.7,
						'data_completeness': field_completion_rate,
						'content_utilization': content_utilization,
						'llm_confidence': llm_confidence,
						'token_efficiency': min(1.0, extraction_metrics.get("output_tokens", 100) / 500.0)  # Efficient token usage
					}
				)
				  # Record content metrics
				benchmark_ctx.record_content(
					content_size=len(str(structured_data)),
					structured_data_size=len(str(structured_data)),
					word_count=input_length // 5  # Estimate words from character count
				)
			else:
				# Record skip/failure metrics
				skip_reason = "user_request" if skip_extraction else "system_limitation"
				benchmark_ctx.record_quality(
					completeness_score=extraction_result.get("completeness_score", 50.0),
					confidence_scores={
						'extraction_success': 0.0 if extraction_result.get("error") else 0.5,
						'skip_reason_severity': 0.2 if skip_reason == "user_request" else 0.8
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
		"""Merge extraction phase results into final result while preserving crawled content."""
		structured_data = extraction_result["structured_data"]
		
		# Preserve existing images/logos found during crawling
		existing_images = final_result.get("images_found", [])
		existing_logos = final_result.get("logos_found", [])
		existing_facility_images = final_result.get("facility_images", [])
		
		# Merge extracted structured data
		for key in STRUCTURED_INFO_KEYS:
			if key in structured_data and structured_data[key] != "Unknown":
				final_result[key] = structured_data[key]
		
		# Restore preserved content (don't let LLM extraction override crawled images)
		if existing_images:
			final_result["images_found"] = existing_images
		if existing_logos:
			final_result["logos_found"] = existing_logos  
		if existing_facility_images:
			final_result["facility_images"] = existing_facility_images
			
		# Store extraction metrics for debugging
		if "extraction_metrics" in structured_data:
			final_result["extraction_metrics"] = structured_data["extraction_metrics"]
		
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
			
		# Integrate quality score calculation
		self._integrate_quality_score(final_result)
	def _integrate_quality_score(self, final_result):
		"""
		Integrate quality score calculation using the core quality scoring system.
		This adds the same quality metrics used in the web interface to pipeline results.
		"""
		try:
			# Import locally to avoid circular import issues
			import sys
			import os
			
			# Ensure benchmarking module is in path
			current_dir = os.path.dirname(os.path.abspath(__file__))
			project_dir = os.path.dirname(current_dir)
			if project_dir not in sys.path:
				sys.path.append(project_dir)
			
			from benchmarking.quality_score_integration import QualityScoreIntegrator
			
			# Create fresh integrator instance
			integrator = QualityScoreIntegrator()
			
			# Calculate enhanced quality metrics
			quality_metrics = integrator.calculate_enhanced_quality_metrics(
				final_result, 
				benchmark_context={"pipeline_stage": "post_extraction"}
			)
			
			# Add quality metrics to final result
			final_result['quality_score'] = quality_metrics.get('core_quality_score', 0)
			final_result['quality_rating'] = quality_metrics.get('core_quality_rating', 'Unknown')
			final_result['quality_details'] = quality_metrics.get('core_quality_details', {})
			final_result['quality_metrics'] = quality_metrics
			
		except Exception as e:
			# Graceful fallback if quality integration fails
			print(f"Warning: Quality score integration failed: {e}")
			# Try fallback to direct calculation
			try:
				from quality_score_calculator import calculate_information_quality_score
				score, rating, details = calculate_information_quality_score(final_result)
				final_result['quality_score'] = score
				final_result['quality_rating'] = rating
				final_result['quality_details'] = details
			except Exception as fallback_e:
				print(f"Warning: Fallback quality calculation also failed: {fallback_e}")
				final_result['quality_score'] = 0                
				final_result['quality_rating'] = 'Error'
				final_result['quality_details'] = {'error': str(e), 'fallback_error': str(fallback_e)}
	
	def _prepare_text_for_extraction(self, final_result, crawling_result, output_type="markdown"):
		"""
		Prepare comprehensive text for extraction using the specified content format.
		Leverages the crawler's rich content formats for optimal LLM processing.
		
		Args:
			final_result: Current pipeline results
			crawling_result: Results from crawling phase
			output_type: Content format to use ("markdown", "raw_html", "cleaned_html", "text")
		"""
		# Use crawled content if available
		if crawling_result and crawling_result.get("success"):
			# Get the comprehensive crawled data
			crawled_data = crawling_result.get("crawled_data", {})
			content_summary = crawling_result.get("content_summary", {})
			  # Build comprehensive content using multiple formats and structured data
			content_parts = []
			
			# Add comprehensive media summary at the beginning
			all_images = content_summary.get("all_images", [])
			logos_found = content_summary.get("logos_found", [])
			if all_images or logos_found:
				content_parts.append("=== MEDIA CONTENT SUMMARY ===")
				if all_images:
					content_parts.append(f"Total Images Found: {len(all_images)}")
					for img in all_images[:10]:  # Top 10 images
						img_info = f"- {img.get('src', 'Unknown source')}"
						if img.get('alt'):
							img_info += f" | Alt: {img['alt']}"
						if img.get('title'):
							img_info += f" | Title: {img['title']}"
						content_parts.append(img_info)
				
				if logos_found:
					content_parts.append(f"\nLogos Identified: {len(logos_found)}")
					for logo in logos_found[:5]:
						content_parts.append(f"- {logo.get('src', 'Unknown source')}")
				content_parts.append("")  # Empty line for separation
			
			# Add page summaries with key information (structured data from each page)
			page_summaries = content_summary.get("page_summaries", [])
			for page_summary in page_summaries[:5]:  # Top 5 pages by quality
				if page_summary.get("key_info"):
					content_parts.append(f"=== Page: {page_summary.get('title', 'Unknown Title')} ===")
					content_parts.append(f"URL: {page_summary.get('url', 'N/A')}")
					
					# Add key information extracted by crawler
					key_info = page_summary.get("key_info", {})
					if isinstance(key_info, dict):
						relevant_keywords = key_info.get("relevant_keywords_found", [])
						if relevant_keywords:
							content_parts.append(f"Keywords: {', '.join(relevant_keywords)}")
						
						contact_info = key_info.get("contact_information", {})
						if contact_info:
							if contact_info.get("emails"):
								content_parts.append(f"Emails: {', '.join(contact_info['emails'])}")
							if contact_info.get("phones"):
								content_parts.append(f"Phones: {', '.join(contact_info['phones'])}")
					
					# Add content sections if available
					content_sections = page_summary.get("content_sections", {})
					if content_sections:
						for section_name, section_content in content_sections.items():
							if section_content and len(str(section_content).strip()) > 50:
								content_parts.append(f"{section_name}: {str(section_content)[:500]}")
					
					content_parts.append("")  # Empty line for separation
			
			# Add the comprehensive crawled pages content using best available formats
			for page in crawled_data.get("crawled_pages", []):
				if not page.get("success") or not page.get("processed_content"):
					continue
				
				processed = page["processed_content"]
				content_formats = processed.get("content_formats", {})
				
				# Prefer structured content formats for LLM processing
				page_text = ""
				
				# Try markdown variants first (best for LLM understanding)
				markdown_content = content_formats.get("markdown", {})
				if isinstance(markdown_content, dict):
					# Use fit_markdown if available (optimized format)
					if markdown_content.get("fit_markdown"):
						page_text = markdown_content["fit_markdown"]
					elif markdown_content.get("raw_markdown"):
						page_text = markdown_content["raw_markdown"]
					elif markdown_content.get("primary_content"):
						page_text = markdown_content["primary_content"]
				
				# Fall back to cleaned HTML if no good markdown
				if not page_text and content_formats.get("cleaned_html"):
					page_text = content_formats["cleaned_html"]
				  # Last resort: text content
				if not page_text and content_formats.get("text_content"):
					page_text = content_formats["text_content"]
				
				if page_text and len(page_text.strip()) > 100:
					content_parts.append(f"\n--- Content from {page.get('url', 'Unknown URL')} ---")
					content_parts.append(page_text[:3000])  # Limit per page
					
					# Add images and media information found on this page
					page_images = processed.get("media", {}).get("images", [])
					if page_images:
						content_parts.append("\n--- Images found on this page ---")
						for img in page_images[:5]:  # Limit to top 5 images per page
							img_info = f"Image: {img.get('src', 'N/A')}"
							if img.get('alt'):
								img_info += f" (Alt: {img['alt']})"
							if img.get('title'):
								img_info += f" (Title: {img['title']})"
							content_parts.append(img_info)
			
			# Add structured data and metadata if available
			for page in crawled_data.get("crawled_pages", []):
				if not page.get("success"):
					continue
				
				processed = page["processed_content"]
				
				# Add valuable metadata
				metadata = processed.get("metadata", {})
				if metadata:
					meta_info = []
					if metadata.get("title"):
						meta_info.append(f"Title: {metadata['title']}")
					if metadata.get("description"):
						meta_info.append(f"Description: {metadata['description']}")
					if metadata.get("keywords"):
						meta_info.append(f"Keywords: {metadata['keywords']}")
					
					if meta_info:
						content_parts.append(f"\n--- Metadata from {page.get('url', 'Unknown')} ---")
						content_parts.extend(meta_info)
				
				# Add structured data (JSON-LD, etc.)
				structured_data = processed.get("structured_data", {})
				json_ld = processed.get("json_ld", [])
				if json_ld:
					content_parts.append(f"\n--- Structured Data from {page.get('url', 'Unknown')} ---")
					for item in json_ld[:3]:  # Limit to avoid token overflow
						content_parts.append(str(item)[:500])
			
			# Combine all content
			comprehensive_text = "\n".join(content_parts)
			
			# If we have substantial comprehensive content, use it
			if len(comprehensive_text.strip()) > 500:
				# Limit total length for LLM processing while preserving structure
				return comprehensive_text[:12000]  # Increased limit for richer content
			
			# Fall back to simple total_text if comprehensive extraction didn't work
			total_text = content_summary.get("total_text", "")
			if total_text.strip():
				return total_text[:8000]
		
		# Fall back to initial description from search
		return final_result.get("description_raw", "")
	def _record_final_benchmark_metrics(self, benchmark_ctx, final_result, search_result, crawling_result, extraction_result):
		"""Record comprehensive final benchmark metrics."""
		# Calculate total content size and complexity
		total_content_size = len(str(final_result))
		structured_data_size = 0
		raw_data_size = 0
		
		if crawling_result and crawling_result.get("success"):
			crawled_data = crawling_result.get("crawled_data", {})
			content_summary = crawling_result.get("content_summary", {})
			total_content_size += len(str(crawled_data))
			structured_data_size += len(str(content_summary))
			raw_data_size += len(content_summary.get("total_text", ""))
		if extraction_result and not extraction_result.get("skipped"):
			structured_data = extraction_result.get("structured_data", {})
			structured_data_size += len(str(structured_data))
			  # Record LLM token usage and costs if extraction was performed
		if extraction_result and not extraction_result.get("skipped"):
			structured_data = extraction_result.get("structured_data", {})
			extraction_metrics = structured_data.get("extraction_metrics", {})
			if extraction_metrics.get("success") and extraction_metrics.get("total_tokens", 0) > 0:
				# Record actual LLM costs using real token usage
				benchmark_ctx.record_cost(
					input_tokens=extraction_metrics.get("input_tokens", 0),
					output_tokens=extraction_metrics.get("output_tokens", 0),
					service_type="gemini_flash"  # Use Gemini pricing
				)
				  # Record LLM processing time from extraction_metrics
				extraction_time = extraction_metrics.get("extraction_time", 0)
				if extraction_time > 0:
					benchmark_ctx.manager.record_latency(
						benchmark_ctx.benchmark_id,
						"llm_processing",
						extraction_time
					)
					
					# Also record using tracker method for proper integration
					benchmark_ctx.manager.tracker.add_llm_metrics(
						pipeline_id=benchmark_ctx.benchmark_id,
						llm_time=extraction_time,
						model_name=extraction_metrics.get("model_used", "gemini-2.0-flash"),
						input_tokens=extraction_metrics.get("input_tokens", 0),
						output_tokens=extraction_metrics.get("output_tokens", 0),
						fields_requested=len(extraction_result.get("structured_data", {})),
						fields_extracted=len([v for v in extraction_result.get("structured_data", {}).values() if v != "Unknown"])
					)
		  # Record comprehensive content metrics
		benchmark_ctx.record_content(
			content_size=total_content_size,
			structured_data_size=structured_data_size,
			word_count=raw_data_size // 5,  # Estimate words from character count
			media_count=len(final_result.get("images_found", []))
		)
		
		# Calculate overall pipeline performance metrics
		phases_completed = sum(1 for phase in final_result["processing_phases"].values() if phase["completed"])
		phases_successful = sum(1 for phase in final_result["processing_phases"].values() if phase.get("success", False))
		overall_success = final_result["performance_metrics"]["overall_success"]
		
		# Calculate total pipeline time and efficiency
		total_time = final_result["performance_metrics"]["total_pipeline_time"]
		search_time = final_result["processing_phases"]["search"].get("time", 0)
		crawling_time = final_result["processing_phases"]["crawling"].get("time", 0)
		extraction_time = final_result["processing_phases"]["extraction"].get("time", 0)
		
		# Calculate phase efficiency ratios
		search_efficiency = min(1.0, len(final_result.get("crawling_links", [])) / max(search_time, 0.1))
		crawling_efficiency = 0.0
		if crawling_result and crawling_time > 0:
			successful_pages = crawling_result.get("successful_pages", 0)
			crawling_efficiency = min(1.0, successful_pages / max(crawling_time / 10, 0.1))
		
		# Determine final completeness score
		final_completeness = 0
		if extraction_result and not extraction_result.get("skipped"):
			final_completeness = extraction_result.get("completeness_score", 0)
		elif crawling_result and crawling_result.get("success"):
			# Calculate based on content richness
			content_summary = crawling_result.get("content_summary", {})
			text_length = len(content_summary.get("total_text", ""))
			images_count = len(content_summary.get("all_images", []))
			social_links = len(content_summary.get("social_media_links", {}))
			documents_count = len(content_summary.get("documents_found", []))
			
			# Weight different content types
			content_score = min(100, (
				(text_length / 100) * 0.4 +  # Text content weight
				images_count * 2 +             # Images weight
				social_links * 3 +             # Social media weight
				documents_count * 5            # Documents weight
			))
			final_completeness = min(85.0, content_score)  # Cap at 85% without extraction
		elif search_result and search_result.get("success"):
			# Basic search-only completeness
			num_links = len(search_result.get("links", []))
			final_completeness = min(50.0, num_links * 3.33)
		
		# Record comprehensive quality metrics
		benchmark_ctx.record_quality(
			completeness_score=final_completeness,
			confidence_scores={
				'overall_pipeline_success': 1.0 if overall_success else 0.6,
				'phases_completion_rate': phases_completed / 3.0,
				'phases_success_rate': phases_successful / max(phases_completed, 1),
				'search_efficiency': min(1.0, search_efficiency),
				'crawling_efficiency': crawling_efficiency,
				'content_richness': min(1.0, (len(final_result.get("images_found", [])) + 
											len(final_result.get("social_media_links", {})) +
											len(final_result.get("documents_found", []))) / 20.0),
				'data_completeness': final_completeness / 100.0
			}        )
		
		# Note: Efficiency metrics (throughput, resource utilization, cache hit rate, error rate) 
		# are automatically calculated and recorded by the benchmarking system
	
	def _attach_benchmark_metrics(self, benchmark_ctx, final_result):
		"""
		Retrieve and attach benchmark metrics to the final result.
		This makes cost, latency, quality, and efficiency metrics available in the template.
		"""
		try:
			# Get the pipeline metrics from the benchmark tracker
			pipeline_id = benchmark_ctx.benchmark_id
			if hasattr(benchmark_ctx.manager, 'tracker') and pipeline_id in benchmark_ctx.manager.tracker.active_pipelines:
				pipeline_metrics = benchmark_ctx.manager.tracker.active_pipelines[pipeline_id]
				
				# Attach cost metrics (actual USD costs)
				final_result['cost_metrics'] = {
					'total_cost_usd': pipeline_metrics.cost_metrics.total_cost_usd,
					'google_search_cost_usd': pipeline_metrics.cost_metrics.google_search_cost_usd,
					'llm_cost_usd': pipeline_metrics.cost_metrics.llm_cost_usd,
					'infrastructure_cost_usd': pipeline_metrics.cost_metrics.infrastructure_cost_usd,
					'google_search_queries': pipeline_metrics.cost_metrics.google_search_queries,
					'llm_model_used': pipeline_metrics.cost_metrics.llm_model_used,
					'input_tokens': pipeline_metrics.cost_metrics.input_tokens,
					'output_tokens': pipeline_metrics.cost_metrics.output_tokens,
					'total_tokens': pipeline_metrics.cost_metrics.total_tokens
				}
				
				# Attach latency metrics (detailed timing)
				final_result['latency_metrics'] = {
					'total_pipeline_time_seconds': pipeline_metrics.latency_metrics.total_pipeline_time_seconds,
					'search_time_seconds': pipeline_metrics.latency_metrics.search_time_seconds,
					'crawling_time_seconds': pipeline_metrics.latency_metrics.crawling_time_seconds,
					'llm_processing_time_seconds': pipeline_metrics.latency_metrics.llm_processing_time_seconds,
					'rag_processing_time_seconds': pipeline_metrics.latency_metrics.rag_processing_time_seconds,
					'cache_lookup_time_seconds': pipeline_metrics.latency_metrics.cache_lookup_time_seconds,
					'api_call_time_seconds': pipeline_metrics.latency_metrics.api_call_time_seconds,
					'network_requests': pipeline_metrics.latency_metrics.network_requests,
					'total_network_time_seconds': pipeline_metrics.latency_metrics.total_network_time_seconds,
					'average_network_latency_ms': pipeline_metrics.latency_metrics.average_network_latency_ms
				}
				
				# Attach quality metrics (completeness and accuracy)
				final_result['quality_metrics'] = {
					'fields_requested': pipeline_metrics.quality_metrics.fields_requested,
					'fields_extracted': pipeline_metrics.quality_metrics.fields_extracted,
					'completeness_score': pipeline_metrics.quality_metrics.completeness_score,
					'accuracy_score': pipeline_metrics.quality_metrics.accuracy_score,
					'precision_score': pipeline_metrics.quality_metrics.precision_score,
					'recall_score': pipeline_metrics.quality_metrics.recall_score,
					'f1_score': pipeline_metrics.quality_metrics.f1_score,
					'content_quality_score': pipeline_metrics.quality_metrics.content_quality_score,
					'relevance_score': pipeline_metrics.quality_metrics.relevance_score,
					'validation_passed': pipeline_metrics.quality_metrics.validation_passed,
					'validation_errors': pipeline_metrics.quality_metrics.validation_errors,
					'confidence_scores': pipeline_metrics.quality_metrics.confidence_scores
				}
				
				# Attach efficiency metrics (cache and performance)
				final_result['efficiency_metrics'] = {
					'cache_requests': pipeline_metrics.efficiency_metrics.cache_requests,
					'cache_hits': pipeline_metrics.efficiency_metrics.cache_hits,
					'cache_misses': pipeline_metrics.efficiency_metrics.cache_misses,
					'cache_hit_rate': pipeline_metrics.efficiency_metrics.cache_hit_rate,
					'memory_usage_mb': pipeline_metrics.efficiency_metrics.memory_usage_mb,
					'cpu_usage_percent': pipeline_metrics.efficiency_metrics.cpu_usage_percent,
					'items_processed': pipeline_metrics.efficiency_metrics.items_processed,
					'processing_rate_per_second': pipeline_metrics.efficiency_metrics.processing_rate_per_second,
					'error_rate': pipeline_metrics.efficiency_metrics.error_rate,
					'retry_count': pipeline_metrics.efficiency_metrics.retry_count,
					'input_data_size_mb': pipeline_metrics.efficiency_metrics.input_data_size_mb,
					'output_data_size_mb': pipeline_metrics.efficiency_metrics.output_data_size_mb
				}
				
		except Exception as e:
			# If benchmark metrics can't be attached, don't fail the pipeline
			print(f"Warning: Could not attach benchmark metrics: {e}")
			# Ensure empty metrics exist to prevent template errors
			final_result.setdefault('cost_metrics', {})
			final_result.setdefault('latency_metrics', {})
			final_result.setdefault('quality_metrics', {})
			final_result.setdefault('efficiency_metrics', {})
	
	def _calculate_and_attach_quality_score(self, final_result: Dict):
		"""Calculate and attach information quality score to final result."""
		try:
			# Use the quality integrator to calculate enhanced score
			enhanced_score = quality_integrator.calculate_enhanced_quality_metrics(final_result, final_result)
			
			# Attach all quality scoring data to final result
			final_result.update(enhanced_score)
			
			print(f"✅ Quality score calculated: {enhanced_score.get('quality_score', 0):.1f} "
				  f"({enhanced_score.get('quality_rating', 'Unknown')})")
			
		except Exception as e:
			print(f"⚠️ Warning: Could not calculate quality score: {e}")
			# Set default quality metrics to prevent template errors
			final_result.setdefault('quality_score', 0.0)
			final_result.setdefault('quality_rating', 'Unknown')
			final_result.setdefault('quality_details', {})
	
	def _extract_content_by_format(self, crawled_data, content_summary, output_type: str):
		"""Extract content in the specified format from crawled data."""
		content_parts = []
		
		# Get crawled pages
		crawled_pages = crawled_data.get("crawled_pages", [])
		
		if output_type == "raw_xml":
			# Use raw HTML content
			for page in crawled_pages:
				content_formats = page.get("content_formats", {})
				raw_html = content_formats.get("raw_html", "")
				if raw_html:
					content_parts.append(f"=== RAW HTML from {page.get('url', 'Unknown')} ===")
					content_parts.append(raw_html)
					
		elif output_type == "cleaned_xml":
			# Use cleaned HTML content
			for page in crawled_pages:
				content_formats = page.get("content_formats", {})
				cleaned_html = content_formats.get("cleaned_html", "")
				if cleaned_html:
					content_parts.append(f"=== CLEANED HTML from {page.get('url', 'Unknown')} ===")
					content_parts.append(cleaned_html)
					
		elif output_type == "markdown":
			# Use markdown content
			for page in crawled_pages:
				content_formats = page.get("content_formats", {})
				markdown_formats = content_formats.get("markdown", {})
				# Prefer fit_markdown, then standard markdown
				markdown_content = (markdown_formats.get("fit_markdown") or 
								  markdown_formats.get("markdown") or "")
				if markdown_content:
					content_parts.append(f"=== MARKDOWN from {page.get('url', 'Unknown')} ===")
					content_parts.append(markdown_content)
					
		else:  # default to "json" format - use comprehensive structured content
			# Add comprehensive media summary
			all_images = content_summary.get("all_images", [])
			logos_found = content_summary.get("logos_found", [])
			if all_images or logos_found:
				content_parts.append("=== MEDIA CONTENT SUMMARY ===")
				if all_images:
					content_parts.append(f"Total Images Found: {len(all_images)}")
					for img in all_images[:10]:
						img_info = f"- {img.get('src', 'Unknown source')}"
						if img.get('alt'):
							img_info += f" | Alt: {img['alt']}"
						if img.get('title'):
							img_info += f" | Title: {img['title']}"
						content_parts.append(img_info)
				
				if logos_found:
					content_parts.append(f"\nLogos Identified: {len(logos_found)}")
			
			# Add structured content from each page
			for page in crawled_pages:
				url = page.get('url', 'Unknown')
				content_parts.append(f"\n=== STRUCTURED CONTENT from {url} ===")
				
				# Use the best available structured content
				content_formats = page.get("content_formats", {})
				if content_formats.get("text_content"):
					content_parts.append(content_formats["text_content"])
				elif content_formats.get("cleaned_html"):
					content_parts.append(content_formats["cleaned_html"])
		
		# Combine all content
		comprehensive_text = "\n".join(content_parts)
		
		# If we have substantial content, use it
		if len(comprehensive_text.strip()) > 500:
			return comprehensive_text
		
		# Fall back to total_text if format-specific extraction didn't work
		total_text = content_summary.get("total_text", "")
		if total_text.strip():
			return total_text
			
		return ""
