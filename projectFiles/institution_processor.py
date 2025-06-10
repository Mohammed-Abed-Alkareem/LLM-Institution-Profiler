# processing_logic.py
import os
import json
import asyncio
from typing import Dict, List
from google import genai
from google.genai.types import Tool, GoogleSearch, GenerateContentConfig 

from search.search_service import SearchService
from search.search_enhancer import SearchQueryEnhancer
from benchmark import ComprehensiveBenchmarkTracker
from extraction_logic import extract_structured_data, STRUCTURED_INFO_KEYS
from crawling_prep import get_institution_links_for_crawling
from crawler import CrawlerService, CrawlingStrategy, InstitutionType

# I'm using google for now, but OpenAI's library can be used for everything if you
# change the link since they all support its API

# TODO: switch to OpenAI's library if we want to use it

# Get the key from https://aistudio.google.com/app/apikey
# If environmental variables aren't detected, try to set it in VScode directly
# The client gets passed to the other modules.
try:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        print("Warning: GOOGLE_API_KEY environment variable not set. AI features will be limited.")
        genai_client = None
    else:
        genai_client = genai.Client(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Fatal Error: Could not configure Google Generative AI Client: {e}")
    genai_client = None

# Initialize search service for data retrieval
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
search_service = SearchService(BASE_DIR)

# Initialize crawler service for comprehensive content extraction
crawler_service = CrawlerService(BASE_DIR)

# Initialize comprehensive benchmark tracker with centralized cache
from cache_config import get_cache_config
cache_config = get_cache_config(BASE_DIR)
benchmark_tracker = ComprehensiveBenchmarkTracker(cache_config.get_benchmarks_dir())

# pipeline flow here
def process_institution_pipeline(institution_name: str, institution_type: str = None, search_params: dict = None, skip_extraction: bool = False, enable_crawling: bool = True):
    """
    Coordinates the comprehensive pipeline for processing an institution's name:
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
        
    Returns:
        A dictionary containing complete structured data about the institution,
        including crawled content, images, links, extracted data, and benchmarks.
    """
    # Initialize the comprehensive result structure
    final_result = {key: "Unknown" for key in STRUCTURED_INFO_KEYS}
    final_result.update({
        "name": institution_name if institution_name else "Unknown",
        "description_raw": "N/A",
        "data_source_notes": "",
        "crawling_links": [],
        "crawling_config": {},
        "crawled_data": {},
        "images_found": [],
        "logos_found": [],
        "comprehensive_content": {},
        "content_summary": {},
        "error": None
    })

    if not institution_name:
        final_result["error"] = "No institution name provided."
        final_result["data_source_notes"] = "Processing aborted: No institution name."
        return final_result

    # Start comprehensive pipeline benchmarking
    pipeline_id = benchmark_tracker.start_pipeline(institution_name, institution_type)
    final_result["pipeline_id"] = pipeline_id
    
    try:
        # Phase 1: Enhanced Search to find URLs and initial data
        print(f"🔍 Phase 1: Searching for {institution_name}...")
        crawling_data = get_institution_links_for_crawling(
            institution_name, 
            institution_type, 
            max_links=15,  # Get more links for comprehensive crawling
            base_dir=BASE_DIR,
            search_params=search_params
        )
        
        if not crawling_data.get('search_successful', False):
            benchmark_tracker.add_pipeline_error(pipeline_id, 'search', crawling_data.get('error', 'Search failed'))
            final_result["error"] = f"Failed to get institution data: {crawling_data.get('error', 'Search failed')}"
            final_result["data_source_notes"] = "Error during search phase."
            
            # Complete pipeline with failure
            pipeline_benchmark = benchmark_tracker.complete_pipeline(pipeline_id, success=False)
            final_result["benchmark_data"] = {
                'pipeline_time': pipeline_benchmark.total_pipeline_time if pipeline_benchmark else 0,
                'success': False,
                'phase': 'search'
            }
            return final_result
        
        # Store crawling information
        final_result["crawling_links"] = crawling_data.get('links', [])
        final_result["data_source_notes"] = f"Found {len(final_result['crawling_links'])} links for crawling. "
        
        # Create basic description from search snippets
        text_parts = []
        for link_data in final_result["crawling_links"][:3]:  # Use top 3 results
            if link_data.get('title'):
                text_parts.append(f"Title: {link_data['title']}")
            if link_data.get('snippet'):
                text_parts.append(f"Description: {link_data['snippet']}")
            text_parts.append("---")
        
        raw_text = "\n".join(text_parts)
        final_result["description_raw"] = raw_text
        final_result["data_source_notes"] += f"Search method: {crawling_data.get('metadata', {}).get('source', 'unknown')}. "
        
        # Add metadata from search
        search_metadata = crawling_data.get('metadata', {})
        if search_metadata.get('cache_hit'):
            final_result["data_source_notes"] += "Used cached search results. "
        
        # Add search enhancement info if available
        if search_metadata.get('enhanced_query'):
            final_result["data_source_notes"] += f"Enhanced query: '{search_metadata['enhanced_query']}'. "
        
        # Prepare crawling configuration for later use
        from crawling_prep import InstitutionLinkManager
        link_manager = InstitutionLinkManager(BASE_DIR)
        final_result["crawling_config"] = link_manager.prepare_crawling_config(crawling_data)

        # Phase 2: Comprehensive Web Crawling (if enabled)
        crawled_content = {}
        if enable_crawling and final_result["crawling_links"]:
            print(f"🕷️ Phase 2: Comprehensive crawling of {len(final_result['crawling_links'])} URLs...")
            
            try:
                # Determine institution type if not provided
                detected_type = institution_type
                if not detected_type:
                    # Try to detect from URL patterns or search results
                    for link in final_result["crawling_links"][:3]:
                        url = link.get('url', '').lower()
                        title = link.get('title', '').lower()
                        snippet = link.get('snippet', '').lower()
                        content = f"{url} {title} {snippet}"
                        
                        if any(word in content for word in ['university', 'college', 'education', 'academic']):
                            detected_type = 'university'
                            break
                        elif any(word in content for word in ['hospital', 'medical', 'health', 'clinic']):
                            detected_type = 'hospital'
                            break
                        elif any(word in content for word in ['bank', 'banking', 'financial', 'finance']):
                            detected_type = 'bank'
                            break
                    
                    if not detected_type:
                        detected_type = 'general'
                
                # Run async crawling
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                crawl_result = loop.run_until_complete(
                    crawler_service.crawl_institution_urls(
                        institution_name=institution_name,
                        urls=[link['url'] for link in final_result["crawling_links"]],
                        institution_type=detected_type,
                        max_pages=12,  # Comprehensive crawling
                        strategy=CrawlingStrategy.ADVANCED
                    )
                )
                
                loop.close()
                
                # Store comprehensive crawled data
                final_result["crawled_data"] = crawl_result
                crawled_content = crawl_result
                
                # Extract comprehensive media and content with enhanced processor
                all_images = []
                logos_found = []
                facility_images = []
                social_media_links = {}
                documents_found = []
                
                for page in crawl_result.get('crawled_pages', []):
                    if page.get('success') and page.get('processed_content'):
                        processed = page['processed_content']
                        
                        # Extract comprehensive image data
                        images_and_logos = processed.get('images_and_logos', {})
                        
                        # Add all images with source information
                        for category in ['logos', 'facility_images', 'people_images', 'general_images']:
                            for img in images_and_logos.get(category, []):
                                img_with_source = img.copy()
                                img_with_source.update({
                                    'source_page': page.get('url', ''),
                                    'page_title': page.get('title', ''),
                                    'category': category
                                })
                                all_images.append(img_with_source)
                                
                                # Separate logos for easy access
                                if category == 'logos':
                                    logos_found.append(img_with_source)
                                elif category == 'facility_images':
                                    facility_images.append(img_with_source)
                        
                        # Aggregate social media links
                        page_social = processed.get('social_media_links', {})
                        for platform, links in page_social.items():
                            if platform not in social_media_links:
                                social_media_links[platform] = []
                            social_media_links[platform].extend(links)
                        
                        # Collect important documents
                        page_docs = processed.get('documents_and_files', {})
                        for doc_type, docs in page_docs.items():
                            for doc in docs:
                                documents_found.append({
                                    'url': doc,
                                    'type': doc_type,
                                    'source_page': page.get('url', ''),
                                    'page_title': page.get('title', '')
                                })
                
                # Remove duplicates and organize data
                final_result["images_found"] = all_images
                final_result["logos_found"] = _deduplicate_images(logos_found)
                final_result["facility_images"] = _deduplicate_images(facility_images)
                final_result["social_media_links"] = _deduplicate_social_links(social_media_links)
                final_result["documents_found"] = _deduplicate_documents(documents_found)
                
                # Create comprehensive content summary
                total_content = ""
                page_summaries = []
                
                for page in crawl_result.get('crawled_pages', []):
                    if page.get('success') and page.get('processed_content'):
                        processed = page['processed_content']
                        
                        # Add cleaned text
                        if processed.get('cleaned_text'):
                            total_content += f"\n\n--- Content from {page.get('url', 'Unknown URL')} ---\n"
                            total_content += processed['cleaned_text'][:2000]  # Limit per page
                        
                        # Store page summary
                        page_summaries.append({
                            'url': page.get('url', ''),
                            'title': page.get('title', ''),
                            'quality_score': page.get('content_quality_score', 0),
                            'word_count': page.get('word_count', 0),
                            'key_info': processed.get('key_information', {}),
                            'content_sections': processed.get('content_sections', {})
                        })
                
                final_result["comprehensive_content"] = {
                    'total_text': total_content,
                    'page_summaries': page_summaries,
                    'crawl_summary': crawl_result.get('crawl_summary', {}),
                    'total_pages_crawled': len(crawl_result.get('crawled_pages', [])),
                    'total_images_found': len(all_images),
                    'logos_identified': len(logos_found)
                }
                
                # Update raw text with comprehensive content for better extraction
                if total_content.strip():
                    raw_text = total_content[:8000]  # Use crawled content instead of search snippets
                    final_result["description_raw"] = raw_text
                    final_result["data_source_notes"] += f"Enhanced with comprehensive crawling: {len(crawl_result.get('crawled_pages', []))} pages. "
                
                print(f"✅ Crawling completed: {len(crawl_result.get('crawled_pages', []))} pages, {len(all_images)} images, {len(logos_found)} logos")
                
            except Exception as e:
                print(f"⚠️ Crawling failed: {str(e)}")
                final_result["data_source_notes"] += f"Crawling failed: {str(e)}. "
                benchmark_tracker.add_pipeline_error(pipeline_id, 'crawling', str(e))
        
        elif not enable_crawling:
            final_result["data_source_notes"] += "Crawling disabled. "
        else:
            final_result["data_source_notes"] += "No URLs available for crawling. "

        # Skip extraction if requested (but we've done crawling)
        if skip_extraction:
            # Calculate completeness based on what we have
            completeness = 50.0  # Base for search + crawling
            if crawled_content.get('crawled_pages'):
                completeness = 70.0  # Good crawling results
            if final_result.get('logos_found'):
                completeness += 5.0
            if final_result.get('images_found'):
                completeness += 5.0
            
            final_result["data_source_notes"] += "Skipped LLM extraction - comprehensive crawling completed."
            
            pipeline_benchmark = benchmark_tracker.complete_pipeline(pipeline_id, success=True, completeness_score=completeness)
            final_result["benchmark_data"] = {
                'pipeline_time': pipeline_benchmark.total_pipeline_time if pipeline_benchmark else 0,
                'success': True,
                'phase': 'search_and_crawling',
                'completeness_percent': completeness,
                'pages_crawled': len(crawled_content.get('crawled_pages', [])),
                'images_found': len(final_result.get('images_found', [])),
                'logos_found': len(final_result.get('logos_found', []))
            }
            return final_result

        # Phase 3: LLM-Powered Extraction for Complete Profiling
        print(f"🤖 Phase 3: LLM extraction from comprehensive content...")
        
        if not genai_client:
            # Calculate completeness without LLM extraction
            completeness = 60.0 if crawled_content.get('crawled_pages') else 30.0
            final_result["data_source_notes"] += "Skipped extraction - AI client not configured. Comprehensive crawling completed."
            
            pipeline_benchmark = benchmark_tracker.complete_pipeline(pipeline_id, success=True, completeness_score=completeness)
            final_result["benchmark_data"] = {
                'pipeline_time': pipeline_benchmark.total_pipeline_time if pipeline_benchmark else 0,
                'success': True,
                'phase': 'search_and_crawling',
                'completeness_percent': completeness
            }
            return final_result

        if len(raw_text.strip()) < 50:  # Very little text available
            completeness = 40.0 if crawled_content.get('crawled_pages') else 35.0
            final_result["data_source_notes"] += "Skipped extraction - insufficient text content available."
            
            pipeline_benchmark = benchmark_tracker.complete_pipeline(pipeline_id, success=True, completeness_score=completeness)
            final_result["benchmark_data"] = {
                'pipeline_time': pipeline_benchmark.total_pipeline_time if pipeline_benchmark else 0,
                'success': True,
                'phase': 'search_and_crawling',
                'completeness_percent': completeness
            }
            return final_result

        # Extract comprehensive information from the raw text (enhanced with crawling)

        if len(raw_text.strip()) < 50:  # Very little text from search snippets
            final_result["data_source_notes"] += "Skipped extraction - insufficient text from search snippets. Use crawling for full data."
            
            # Complete pipeline (search successful, extraction skipped due to insufficient data)
            pipeline_benchmark = benchmark_tracker.complete_pipeline(pipeline_id, success=True, completeness_score=35.0)
            final_result["benchmark_data"] = {
                'pipeline_time': pipeline_benchmark.total_pipeline_time if pipeline_benchmark else 0,
                'success': True,
                'phase': 'search_only',
                'completeness_percent': 35.0
            }
            return final_result

        # Extract information from the raw text
        structured_info = extract_structured_data(genai_client, raw_text, institution_name)

        # Merge extracted data
        for key in STRUCTURED_INFO_KEYS:
            if key in structured_info:
                final_result[key] = structured_info[key]
        
        # Calculate completeness score based on extracted fields
        extracted_fields = sum(1 for key in STRUCTURED_INFO_KEYS if final_result.get(key) != "Unknown")
        completeness_score = (extracted_fields / len(STRUCTURED_INFO_KEYS)) * 100
        
        if "error" in structured_info and structured_info["error"]:
            final_result["error"] = (final_result["error"] + "; " if final_result["error"] else "") + f"Extraction issue: {structured_info['error']}"
            final_result["data_source_notes"] += "Error during structured data extraction from raw text."
            if "raw_llm_output" in structured_info:
                 final_result["extraction_raw_llm_output"] = structured_info["raw_llm_output"]
            
            # Complete pipeline with partial success
            pipeline_benchmark = benchmark_tracker.complete_pipeline(pipeline_id, success=True, completeness_score=completeness_score)
            final_result["benchmark_data"] = {
                'pipeline_time': pipeline_benchmark.total_pipeline_time if pipeline_benchmark else 0,
                'success': True,
                'phase': 'extraction_partial',
                'completeness_percent': completeness_score
            }
        else:
            final_result["data_source_notes"] += "Structured data extracted by LLM from raw text."
            # Ensure the name from extraction (which might be more accurate or normalized) is used
            if "name" in structured_info and structured_info["name"] != "Unknown":
                final_result["name"] = structured_info["name"]

            # Complete pipeline successfully
            pipeline_benchmark = benchmark_tracker.complete_pipeline(pipeline_id, success=True, completeness_score=completeness_score)
            final_result["benchmark_data"] = {
                'pipeline_time': pipeline_benchmark.total_pipeline_time if pipeline_benchmark else 0,
                'success': True,
                'phase': 'extraction_complete',
                'completeness_percent': completeness_score
            }

        return final_result
        
    except Exception as e:
        # Handle unexpected errors
        benchmark_tracker.add_pipeline_error(pipeline_id, 'unexpected', str(e))
        final_result["error"] = f"Unexpected error in pipeline: {str(e)}"
        
        # Complete pipeline with failure
        pipeline_benchmark = benchmark_tracker.complete_pipeline(pipeline_id, success=False)
        final_result["benchmark_data"] = {
            'pipeline_time': pipeline_benchmark.total_pipeline_time if pipeline_benchmark else 0,
            'success': False,
            'phase': 'error'
        }
        return final_result

def _deduplicate_images(images: List[Dict]) -> List[Dict]:
    """Remove duplicate images based on URL."""
    seen_urls = set()
    unique_images = []
    
    for img in images:
        url = img.get('url', img.get('src', ''))
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_images.append(img)
    
    return unique_images[:20]  # Limit to top 20


def _deduplicate_social_links(social_links: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Remove duplicate social media links."""
    deduplicated = {}
    
    for platform, links in social_links.items():
        unique_links = list(set(links))[:3]  # Keep top 3 per platform
        if unique_links:
            deduplicated[platform] = unique_links
    
    return deduplicated


def _deduplicate_documents(documents: List[Dict]) -> List[Dict]:
    """Remove duplicate documents based on URL."""
    seen_urls = set()
    unique_docs = []
    
    for doc in documents:
        url = doc.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_docs.append(doc)
    
    return unique_docs[:15]  # Limit to top 15

def get_institution_profile(institution_name, document_text=None):
    """
    Generates a general textual profile for an institution.
    If document_text is provided, it uses that. Otherwise, it uses general knowledge
    potentially augmented by Google Search (if no document_text).
    This function provides a narrative description rather than structured data.
    (for quick summary)
    """
    if not institution_name:
        return None

    if not genai_client: 
        return {
            "name": institution_name,
            "description": "Generative AI client not available or not configured.", 
            "details": "Please ensure GOOGLE_API_KEY is set and client is initialized." 
        }

    try:
        prompt: str
        details_source: str
        api_config = None

        # Has to be edited
        if document_text:
            prompt = (
                f"From the following document about '{institution_name}', provide a concise profile. "
                f"Summarize its primary focus, type, country, and notable characteristics. "
                f"If the document does not provide sufficient information for a profile, or if the information is contradictory or unclear, please state that. "
                f"Document text:\n\n{document_text}\n\nProfile:"
            )
            details_source = "Profile based on provided document text (Google Generative AI)."
        else:
            prompt = (
                f"Provide a concise profile for the institution: '{institution_name}'. "
                f"Include its primary focus/type, country, and notable characteristics. "
                f"If specific information is unavailable or the institution is unknown/fictional, please indicate this in your response. "
                f"Keep the response to a few sentences."
            )
            details_source = "Profile based on general knowledge (Google Generative AI with Search)."
            google_search_tool = Tool(google_search=GoogleSearch())
            api_config = GenerateContentConfig(tools=[google_search_tool])
            
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config=api_config 
        )
        
        generated_description = "No information generated."
        if response:
            # Check for prompt_feedback and then block_reason
            if response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                generated_description = f"Content generation blocked. Reason: {response.prompt_feedback.block_reason}"
            elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                text_parts = [part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')]
                generated_description = "".join(text_parts).strip() if text_parts else "No text in response parts."
            elif hasattr(response, 'text') and response.text:
                generated_description = response.text.strip()
            
            if not generated_description or generated_description == "No information generated.":
                 generated_description = "AI returned an empty response or no relevant text."
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

if __name__ == '__main__':
    test_institutions = [
        "Massachusetts Institute of Technology", 
        "University of Oxford", 
        "A small local bakery called 'The Sweet Spot'", 
        "Globex Corporation (fictional)",
        "An institution that does not exist XYZ123"
    ]
    
    print("Starting institution processing pipeline tests...\n")
    for inst_name in test_institutions:
        print(f"--- Processing Pipeline for: {inst_name} ---")
        structured_data = process_institution_pipeline(inst_name)
        print("Final Structured Data:")
        print(json.dumps(structured_data, indent=2))
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
    print(json.dumps(empty_name_data, indent=2))
    print("--------------------------------------------------\n")