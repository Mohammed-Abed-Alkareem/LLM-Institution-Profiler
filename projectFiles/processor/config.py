# -*- coding: utf-8 -*-
"""
Configuration and constants for the institution processing pipeline.
Centralizes settings and data structures used throughout the processing flow.
"""
import os
from typing import Dict, List
from google import genai


# Pipeline configuration constants
DEFAULT_MAX_LINKS = 15
DEFAULT_MAX_PAGES = 12
DEFAULT_CONTENT_LIMIT_PER_PAGE = 2000
DEFAULT_TOTAL_CONTENT_LIMIT = 8000

# Supported institution types for detection
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


class ProcessorConfig:
    """Configuration class for the institution processor."""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.genai_client = self._initialize_genai_client()
        
    def _initialize_genai_client(self):
        """Initialize the Google Generative AI client."""
        try:
            if not self.google_api_key:
                print("Warning: GOOGLE_API_KEY environment variable not set. AI features will be limited.")
                return None
            else:
                return genai.Client(api_key=self.google_api_key)
        except Exception as e:
            print(f"Fatal Error: Could not configure Google Generative AI Client: {e}")
            return None
    
    def is_ai_available(self) -> bool:
        """Check if AI client is available."""
        return self.genai_client is not None
    
    def get_client(self):
        """Get the AI client."""
        return self.genai_client
