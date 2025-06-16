# -*- coding: utf-8 -*-
"""
Search phase handler for the institution processing pipeline.
Manages the initial search and URL discovery phase.
"""
import time
from typing import Dict, List, Optional
from .config import DEFAULT_MAX_LINKS
from crawling_prep import get_institution_links_for_crawling, InstitutionLinkManager


class SearchPhaseHandler:
	"""Handles the search phase of institution processing."""
	def __init__(self, base_dir: str, search_service=None):
		self.base_dir = base_dir
		self.link_manager = InstitutionLinkManager(base_dir, search_service)
	def execute_search_phase(
		self, 
		institution_name: str, 
		institution_type: Optional[str] = None,
		search_params: Optional[Dict] = None,
		max_links: int = DEFAULT_MAX_LINKS,
		crawler_config: Optional[Dict] = None
	) -> Dict:        
		"""
		Execute the search phase to find institution URLs and initial data.
		
		Args:
			institution_name: Name of the institution to search for
			institution_type: Optional type of institution
			search_params: Additional search parameters
			max_links: Maximum number of links to retrieve
			crawler_config: Optional custom crawler configuration
			
		Returns:
			Dict containing search results and metadata
		"""
		print(f"🔍 Phase 1: Searching for {institution_name}...")
		
		search_start_time = time.time()
		
		# Get institution links for crawling
		crawling_data = get_institution_links_for_crawling(
			institution_name, 
			institution_type, 
			max_links,
			self.base_dir,
			search_params
		)
		
		search_time = time.time() - search_start_time
		
		# Prepare result structure
		result = {
			'success': crawling_data.get('search_successful', False),
			'search_time': search_time,
			'links': crawling_data.get('links', []),
			'metadata': crawling_data.get('metadata', {}),
			'error': crawling_data.get('error') if not crawling_data.get('search_successful') else None
		}
		if result['success']:
			# Prepare crawling configuration - use custom config if provided
			if crawler_config:
				# Apply custom crawler configuration
				from crawling_prep import CrawlPriorityConfig, BenchmarkConfig, InstitutionLinkManager
				
				priority_config = None
				benchmark_config = None
				
				if 'priority_config' in crawler_config:
					priority_config = CrawlPriorityConfig(**crawler_config['priority_config'])
				if 'benchmark_config' in crawler_config:
					benchmark_config = BenchmarkConfig(**crawler_config['benchmark_config'])
				
				# Create new link manager with custom configurations
				custom_link_manager = InstitutionLinkManager(
					self.base_dir, 
					self.link_manager.search_service,
					priority_config,
					benchmark_config
				)
				result['crawling_config'] = custom_link_manager.prepare_crawling_config(crawling_data)
			else:
				# Use default configuration
				result['crawling_config'] = self.link_manager.prepare_crawling_config(crawling_data)
			
			# Create basic description from search snippets
			result['initial_description'] = self._create_initial_description(result['links'])
			
			print(f"✅ Search completed: {len(result['links'])} links found in {search_time:.2f}s")
		else:
			print(f"❌ Search failed: {result['error']}")
		
		return result
	
	def _create_initial_description(self, links: List[Dict]) -> str:
		"""Create initial description from search snippets."""
		text_parts = []
		
		for link_data in links[:3]:  # Use top 3 results
			if link_data.get('title'):
				text_parts.append(f"Title: {link_data['title']}")
			if link_data.get('snippet'):
				text_parts.append(f"Description: {link_data['snippet']}")
			text_parts.append("---")
		
		return "\n".join(text_parts)
	
	def get_search_summary(self, search_result: Dict) -> str:
		"""Get a summary of the search phase results."""
		if not search_result['success']:
			return f"Search failed: {search_result.get('error', 'Unknown error')}"
		
		metadata = search_result.get('metadata', {})
		cache_status = "cached" if metadata.get('cache_hit') else "fresh"
		enhanced_query = metadata.get('enhanced_query', '')
		
		summary_parts = [
			f"Found {len(search_result['links'])} links for crawling",
			f"Search method: {metadata.get('source', 'unknown')}",
			f"Cache status: {cache_status}"
		]
		if enhanced_query:
			summary_parts.append(f"Improved query: '{enhanced_query}'")
		
		return ". ".join(summary_parts) + "."
