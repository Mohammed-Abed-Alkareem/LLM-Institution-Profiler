# -*- coding: utf-8 -*-
"""
Refactored Institution Processor - Main interface for the processing pipeline.
This module provides a clean interface to the comprehensive institution processing system.
"""
import os
from typing import Dict, Optional
from processor.pipeline import InstitutionPipeline
from processor.config import ProcessorConfig
from search.search_service import SearchService
from crawler.crawler_service import CrawlerService


# Global instances (initialized once)
_pipeline_instance = None
_processor_config = None
_crawler_service = None
_search_service = None


def set_global_crawler_service(crawler_service):
	"""Set the global crawler service instance for use by the pipeline."""
	global _crawler_service
	_crawler_service = crawler_service


def set_global_search_service(search_service):
	"""Set the global search service instance for use by the pipeline."""
	global _search_service
	_search_service = search_service


def _get_pipeline_instance():
	"""Get or create the global pipeline instance."""
	global _pipeline_instance, _processor_config, _crawler_service, _search_service
	
	if _pipeline_instance is None:
		BASE_DIR = os.path.dirname(os.path.abspath(__file__))
		
		# Use global crawler service if available, otherwise create new one
		if _crawler_service is not None:
			crawler_service = _crawler_service
		else:
			# Initialize services
			crawler_service = CrawlerService(BASE_DIR)
		
		# Create pipeline
		_pipeline_instance = InstitutionPipeline(BASE_DIR, crawler_service)
		_processor_config = _pipeline_instance.config
		
		print("✅ Institution processing pipeline initialized")
	
	return _pipeline_instance


def process_institution_pipeline(
	institution_name: str, 
	institution_type: Optional[str] = None, 
	search_params: Optional[Dict] = None, 
	skip_extraction: bool = False, 
	enable_crawling: bool = True,
	output_type: str = "json",
	crawler_config: Optional[Dict] = None,
	force_refresh: bool = False
	) -> Dict:
	"""
	Main entry point for comprehensive institution processing.
	
	This function coordinates the complete pipeline:
	1. Enhanced search with flexible parameters to find initial data and URLs
	2. Comprehensive web crawling to extract detailed content including:
	   - About/overview information
	   - Contact details
	   - Key statistics and facts
	   - Images including logos and facility photos
	   - Links to important pages
	3. LLM-powered structured data extraction for complete profiling
	4. Comprehensive benchmarking and caching throughout
	
	Args:
		institution_name: The name of the institution to process
		institution_type: Optional type of institution (university, hospital, bank, etc.)
		search_params: Enhanced search parameters (location, keywords, domain_hint, exclude_terms)
		skip_extraction: If True, skip LLM extraction but still perform crawling
		enable_crawling: If True, perform comprehensive web crawling (recommended)
		output_type: Format for the output ("json", "markdown", etc.)
		crawler_config: Optional crawler configuration (strategy, priority settings, etc.)
		disable_cache: If True, disable caching for this specific request
		
	Returns:
		A dictionary containing complete structured data about the institution,
		including crawled content, images, links, extracted data, and benchmarks.    
	"""
	pipeline = _get_pipeline_instance()	
	return pipeline.process_institution(
		institution_name=institution_name,
		institution_type=institution_type,
		search_params=search_params or {},
		skip_extraction=skip_extraction,
		enable_crawling=enable_crawling,
		output_type=output_type,
		crawler_config=crawler_config,
		force_refresh=force_refresh
	)


def get_institution_profile(institution_name: str, document_text: Optional[str] = None) -> Optional[Dict]:
	"""
	Generates a general textual profile for an institution.
	If document_text is provided, it uses that. Otherwise, it uses general knowledge
	potentially augmented by Google Search (if no document_text).
	This function provides a narrative description rather than structured data.
	(for quick summary)
	
	Args:
		institution_name: Name of the institution
		document_text: Optional document text to base the profile on
		
	Returns:
		Dictionary containing institution profile or None if failed
	"""
	if not institution_name:
		return None    # Get the processor config
	pipeline = _get_pipeline_instance()
	openai_client = pipeline.config.get_client()
	
	if not openai_client: 
		return {
			"name": institution_name,
			"description": "OpenAI client not available or not configured.", 
			"details": "Please ensure GOOGLE_API_KEY is set and client is initialized." 
		}    
	try:
		prompt: str
		details_source: str

		if document_text:
			prompt = (
				f"From the following document about '{institution_name}', provide a concise profile. "
				f"Summarize its primary focus, type, country, and notable characteristics. "
				f"If the document does not provide sufficient information for a profile, or if the information is contradictory or unclear, please state that. "
				f"Document text:\n\n{document_text}\n\nProfile:"
			)
			details_source = "Profile based on provided document text (OpenAI-compatible Gemini)."
		else:
			prompt = (
				f"Provide a concise profile for the institution: '{institution_name}'. "
				f"Include its primary focus/type, country, and notable characteristics. "
				f"If specific information is unavailable or the institution is unknown/fictional, please indicate this in your response. "
				f"Keep the response to a few sentences."
			)
			details_source = "Profile based on general knowledge (OpenAI-compatible Gemini)."
			
		response = openai_client.chat.completions.create(
			model="gemini-2.0-flash",
			messages=[
				{"role": "system", "content": "You are a helpful assistant that provides concise institutional profiles."},
				{"role": "user", "content": prompt}
			]
		)
		
		generated_description = "No information generated."
		if response and response.choices and response.choices[0].message:
			generated_description = response.choices[0].message.content.strip()
			
			if not generated_description:
				generated_description = "AI returned an empty response."
		else: 
			generated_description = "No response received from AI."

		return {
			"name": institution_name,
			"description": generated_description,
			"details": details_source
		}
	except Exception as e:
		print(f"Error in get_institution_profile for {institution_name}: {e}")
		return {
			"name": institution_name,
			"description": "Could not generate profile due to an error.",
			"details": f"Error: {str(e)}"
		}


def get_pipeline_stats() -> Dict:
	"""Get statistics about the processing pipeline."""
	pipeline = _get_pipeline_instance()
	
	return {
		"ai_available": pipeline.config.is_ai_available(),
		"base_directory": pipeline.base_dir,
		"benchmarking_enabled": pipeline.benchmarking_manager is not None,
		"services_initialized": {
			"search_handler": pipeline.search_handler is not None,
			"crawling_handler": pipeline.crawling_handler is not None,
			"extraction_handler": pipeline.extraction_handler is not None
		}
	}


def reset_pipeline_instance():
	"""Reset the pipeline instance (for testing purposes)."""
	global _pipeline_instance
	_pipeline_instance = None


# For backward compatibility and testing
if __name__ == '__main__':
	import json
	
	test_institutions = [
		"Massachusetts Institute of Technology", 
		"University of Oxford", 
		"A small local bakery called 'The Sweet Spot'", 
		"Globex Corporation (fictional)",
		"An institution that does not exist XYZ123"
	]
	
	print("🚀 Starting institution processing pipeline tests...\n")
	print("📊 Pipeline Stats:")
	print(json.dumps(get_pipeline_stats(), indent=2))
	print("\n" + "="*60 + "\n")
	
	for inst_name in test_institutions:
		print(f"--- Processing Pipeline for: {inst_name} ---")
		structured_data = process_institution_pipeline(inst_name)
		print("Final Structured Data (summary):")
		
		# Print a summary instead of the full data
		summary = {
			"name": structured_data.get("name", "Unknown"),
			"type": structured_data.get("type", "Unknown"),
			"location": structured_data.get("location", "Unknown"),
			"processing_success": not structured_data.get("error"),
			"phases_completed": structured_data.get("processing_phases", {}),
			"images_found": len(structured_data.get("images_found", [])),
			"logos_found": len(structured_data.get("logos_found", [])),
			"links_crawled": len(structured_data.get("crawling_links", [])),
			"error": structured_data.get("error")
		}
		print(json.dumps(summary, indent=2))
		print("--------------------------------------------------\n")

	print("\n--- Testing get_institution_profile (general textual profile) ---")
	profile = get_institution_profile("Stanford University")
	if profile:
		print("Profile for Stanford University:")
		print(json.dumps(profile, indent=2))
	print("--------------------------------------------------\n")

	sample_doc_text = """
	Tech Solutions Inc. is a for-profit company based in Silicon Valley, USA. 
	It was founded in 2010 and employs approximately 250 people. 
	Their main office is at 123 Innovation Drive, Techville, CA 94000.
	They specialize in cloud software.
	"""
	print("\n--- Testing get_institution_profile (with document text) ---")
	profile_with_doc = get_institution_profile("Tech Solutions Inc.", document_text=sample_doc_text)
	if profile_with_doc:
		print("Profile for Tech Solutions Inc. (from doc):")
		print(json.dumps(profile_with_doc, indent=2))
	print("--------------------------------------------------\n")

	print("\n--- Testing pipeline with empty name ---")
	empty_name_data = process_institution_pipeline("")
	print("Data for empty name:")
	print(json.dumps({
		"error": empty_name_data.get("error"),
		"data_source_notes": empty_name_data.get("data_source_notes")
	}, indent=2))
	print("--------------------------------------------------\n")
