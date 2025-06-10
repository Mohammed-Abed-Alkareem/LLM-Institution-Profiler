# -*- coding: utf-8 -*-
"""
Extraction phase handler for the institution processing pipeline.
Manages LLM-powered structured data extraction.
"""
import time
from typing import Dict, Optional
from .config import CONTENT_LIMITS
from extraction_logic import extract_structured_data, STRUCTURED_INFO_KEYS


class ExtractionPhaseHandler:
    """Handles the extraction phase of institution processing."""
    
    def __init__(self, processor_config):
        self.config = processor_config
    
    def execute_extraction_phase(
        self,
        institution_name: str,
        raw_text: str,
        skip_extraction: bool = False
    ) -> Dict:
        """
        Execute the extraction phase to get structured data.
        
        Args:
            institution_name: Name of the institution
            raw_text: Raw text content to extract from
            skip_extraction: Whether to skip LLM extraction
            
        Returns:
            Dict containing extraction results
        """
        if skip_extraction:
            return {
                'success': True,
                'skipped': True,
                'extraction_time': 0,
                'structured_data': {key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                'completeness_score': 50.0,  # Base score for search + crawling
                'message': 'LLM extraction skipped as requested'
            }
        
        if not self.config.is_ai_available():
            return {
                'success': True,
                'skipped': True,
                'extraction_time': 0,
                'structured_data': {key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                'completeness_score': 60.0,  # Higher score for crawling completed
                'message': 'LLM extraction skipped - AI client not configured'
            }
        
        if len(raw_text.strip()) < CONTENT_LIMITS['min_text_length_for_extraction']:
            return {
                'success': True,
                'skipped': True,
                'extraction_time': 0,
                'structured_data': {key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                'completeness_score': 40.0,
                'message': 'LLM extraction skipped - insufficient text content'
            }
        
        print(f"🤖 Phase 3: LLM extraction from comprehensive content...")
        
        extraction_start_time = time.time()
        
        try:
            # Extract comprehensive information from the raw text
            structured_info = extract_structured_data(
                self.config.get_client(), 
                raw_text, 
                institution_name
            )
            
            extraction_time = time.time() - extraction_start_time
            
            # Calculate completeness score based on extracted fields
            extracted_fields = sum(
                1 for key in STRUCTURED_INFO_KEYS 
                if structured_info.get(key) and structured_info[key] != "Unknown"
            )
            completeness_score = (extracted_fields / len(STRUCTURED_INFO_KEYS)) * 100
            
            if structured_info.get("error"):
                print(f"⚠️ Extraction completed with warnings: {structured_info['error']}")
                result = {
                    'success': True,
                    'skipped': False,
                    'extraction_time': extraction_time,
                    'structured_data': structured_info,
                    'completeness_score': completeness_score,
                    'error': structured_info["error"],
                    'message': 'Extraction completed with some issues'
                }
                
                if "raw_llm_output" in structured_info:
                    result["raw_llm_output"] = structured_info["raw_llm_output"]
            else:
                print(f"✅ Extraction completed successfully in {extraction_time:.2f}s")
                result = {
                    'success': True,
                    'skipped': False,
                    'extraction_time': extraction_time,
                    'structured_data': structured_info,
                    'completeness_score': completeness_score,
                    'message': 'Structured data extracted successfully'
                }
            
            return result
            
        except Exception as e:
            extraction_time = time.time() - extraction_start_time
            print(f"❌ Extraction failed: {str(e)}")
            
            return {
                'success': False,
                'skipped': False,
                'extraction_time': extraction_time,
                'structured_data': {key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                'completeness_score': 30.0,
                'error': f"Extraction failed: {str(e)}",
                'message': 'LLM extraction encountered an error'
            }
    
    def get_extraction_summary(self, extraction_result: Dict) -> str:
        """Get a summary of the extraction phase results."""
        if extraction_result.get('skipped'):
            return extraction_result.get('message', 'Extraction was skipped')
        
        if not extraction_result.get('success'):
            return f"Extraction failed: {extraction_result.get('error', 'Unknown error')}"
        
        completeness = extraction_result.get('completeness_score', 0)
        extraction_time = extraction_result.get('extraction_time', 0)
        
        summary = f"Extraction completed in {extraction_time:.2f}s with {completeness:.1f}% completeness"
        
        if extraction_result.get('error'):
            summary += f" (with warnings: {extraction_result['error']})"
        
        return summary
