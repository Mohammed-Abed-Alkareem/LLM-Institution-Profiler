"""
Institution Profiler Web Crawler Configuration Module

This module provides configuration classes for the web crawler system,
including browser settings, extraction strategies, and institution-specific
crawling parameters.
"""

import os
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy


class InstitutionType(Enum):
    """Supported institution types for specialized crawling strategies."""
    UNIVERSITY = "university"
    HOSPITAL = "hospital"
    BANK = "bank"
    GENERAL = "general"
    UNKNOWN = "unknown"


class CrawlingStrategy(Enum):
    """Different crawling strategies based on content complexity."""
    SIMPLE = "simple"  # Basic content extraction
    ADVANCED = "advanced"  # JavaScript execution + dynamic content
    COMPREHENSIVE = "comprehensive"  # Multi-page crawling


@dataclass
class CrawlerConfig:
    """Main configuration class for the crawler system."""
    
    # Basic crawler settings
    headless: bool = True
    java_script_enabled: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    cache_mode: CacheMode = CacheMode.ENABLED
    
    # Institution-specific settings
    institution_type: InstitutionType = InstitutionType.UNKNOWN
    crawling_strategy: CrawlingStrategy = CrawlingStrategy.SIMPLE
    
    # Content extraction settings
    max_pages_per_domain: int = 5
    page_timeout: int = 30000  # 30 seconds
    word_count_threshold: int = 100
    
    # Content filtering
    excluded_tags: List[str] = field(default_factory=lambda: [
        "nav", "footer", "aside", "header", "script", "style", "meta"
    ])
    remove_overlay_elements: bool = True
    exclude_external_links: bool = True
    exclude_social_media_links: bool = True
    
    # Screenshot and media
    take_screenshot: bool = False
    include_images: bool = False
    exclude_external_images: bool = True
    
    # Rate limiting and delays
    delay_between_requests: float = 1.0  # seconds
    delay_before_return_html: float = 2.0  # seconds for JS-heavy sites
      # Advanced settings
    simulate_user: bool = False
    override_navigator: bool = False
    user_agent_mode: str = "random"  # random, custom, default
    
    # Extraction strategy (optional)
    extraction_strategy: Optional[Any] = None
    
    def get_browser_config(self) -> BrowserConfig:
        """Get crawl4ai BrowserConfig from our settings."""
        config_dict = {
            "headless": self.headless,
            "java_script_enabled": self.java_script_enabled,
            "browser_type": self.browser_type
        }
        
        # Add user agent configuration for anti-bot measures
        if self.user_agent_mode == "random":
            config_dict["user_agent_mode"] = "random"
            config_dict["user_agent_generator_config"] = {
                "device_type": "desktop",
                "os_type": "windows"
            }
        
        return BrowserConfig(**config_dict)
    
    def get_crawler_run_config(self, 
                              url: str = None, 
                              css_selector: str = None,
                              js_code: str = None) -> CrawlerRunConfig:
        """Get crawl4ai CrawlerRunConfig from our settings."""
        from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        from crawl4ai.content_filter_strategy import PruningContentFilter
        
        config_dict = {
            "cache_mode": self.cache_mode,
            "excluded_tags": self.excluded_tags,
            "remove_overlay_elements": self.remove_overlay_elements,
            "exclude_external_links": self.exclude_external_links,
            "exclude_social_media_links": self.exclude_social_media_links,
            "page_timeout": self.page_timeout,
            "word_count_threshold": self.word_count_threshold,
            "screenshot": self.take_screenshot,
            "exclude_external_images": self.exclude_external_images,
            "delay_before_return_html": self.delay_before_return_html
        }
        
        # Add advanced settings for anti-bot measures
        if self.simulate_user:
            config_dict["simulate_user"] = True
            config_dict["override_navigator"] = self.override_navigator
            config_dict["magic"] = True
        
        # Add CSS selector if provided
        if css_selector:
            config_dict["css_selector"] = css_selector
        
        # Add JavaScript code if provided
        if js_code:
            config_dict["js_code"] = js_code
        
        # Configure content filtering based on institution type
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,  # Keep content with relevance > 48%
                threshold_type="fixed",
                min_word_threshold=self.word_count_threshold
            ),
            options={"ignore_links": False}  # Keep links for institution data
        )
        config_dict["markdown_generator"] = markdown_generator
        return CrawlerRunConfig(**config_dict)
    
    @classmethod
    def for_institution_type(cls, institution_type: InstitutionType, strategy: CrawlingStrategy = CrawlingStrategy.SIMPLE) -> 'CrawlerConfig':
        """Create a CrawlerConfig optimized for a specific institution type and strategy."""
        config = cls()
        config.institution_type = institution_type
        config.crawling_strategy = strategy
        
        # Configure based on strategy
        if strategy == CrawlingStrategy.SIMPLE:
            config.java_script_enabled = False
            config.page_timeout = 15000
            config.delay_before_return_html = 1.0
            config.take_screenshot = False
        elif strategy == CrawlingStrategy.ADVANCED:
            config.java_script_enabled = True
            config.page_timeout = 30000
            config.delay_before_return_html = 2.0
            config.simulate_user = True
        elif strategy == CrawlingStrategy.COMPREHENSIVE:
            config.java_script_enabled = True
            config.delay_before_return_html = 5.0
            config.page_timeout = 60000
            config.max_pages_per_domain = 10
            config.simulate_user = True
            config.take_screenshot = True
        
        # Adjust settings based on institution type
        if institution_type == InstitutionType.UNIVERSITY:
            config.max_pages_per_domain = 8  # Universities often have more relevant pages
            config.word_count_threshold = 150
        elif institution_type == InstitutionType.HOSPITAL:
            config.max_pages_per_domain = 6
            config.word_count_threshold = 100
        elif institution_type == InstitutionType.BANK:
            config.max_pages_per_domain = 4  # Banks typically have more focused content
            config.word_count_threshold = 80
        
        return config


@dataclass
class InstitutionCrawlerSettings:
    """Institution-specific crawler settings and strategies."""
    
    # Content extraction targets by institution type
    UNIVERSITY_TARGETS = {
        "about_selectors": [
            ".about", "#about", "[class*='about']",
            ".overview", "#overview", "[class*='overview']",
            ".mission", "#mission", "[class*='mission']"
        ],
        "contact_selectors": [
            ".contact", "#contact", "[class*='contact']",
            ".address", "#address", "[class*='address']",
            "footer", ".footer"
        ],
        "facts_selectors": [
            ".facts", "#facts", "[class*='facts']",
            ".stats", "#stats", "[class*='statistics']",
            ".numbers", "[class*='enrollment']"
        ],
        "priority_keywords": [
            "university", "college", "education", "students", "faculty",
            "academic", "research", "campus", "degree", "programs"
        ]
    }
    
    HOSPITAL_TARGETS = {
        "about_selectors": [
            ".about", "#about", "[class*='about']",
            ".services", "#services", "[class*='services']",
            ".care", "[class*='care']"
        ],
        "contact_selectors": [
            ".contact", "#contact", "[class*='contact']",
            ".location", "#location", "[class*='location']",
            ".directions", "[class*='address']"
        ],
        "facts_selectors": [
            ".stats", "#stats", "[class*='statistics']",
            ".facts", "[class*='beds']", "[class*='patients']"
        ],
        "priority_keywords": [
            "hospital", "medical", "healthcare", "patients", "doctors",
            "clinic", "health", "care", "treatment", "services"
        ]
    }
    
    BANK_TARGETS = {
        "about_selectors": [
            ".about", "#about", "[class*='about']",
            ".company", "#company", "[class*='company']",
            ".bank-info", "[class*='bank']"
        ],
        "contact_selectors": [
            ".contact", "#contact", "[class*='contact']",
            ".locations", "#locations", "[class*='branch']",
            ".headquarters", "[class*='address']"
        ],
        "facts_selectors": [
            ".facts", "#facts", "[class*='facts']",
            ".assets", "[class*='assets']", "[class*='financial']"
        ],
        "priority_keywords": [
            "bank", "banking", "financial", "finance", "assets",
            "loans", "deposits", "branch", "headquarters", "services"
        ]
    }
    
    @classmethod
    def get_targets_for_type(cls, institution_type: InstitutionType) -> Dict[str, List[str]]:
        """Get extraction targets for a specific institution type."""
        if institution_type == InstitutionType.UNIVERSITY:
            return cls.UNIVERSITY_TARGETS
        elif institution_type == InstitutionType.HOSPITAL:
            return cls.HOSPITAL_TARGETS
        elif institution_type == InstitutionType.BANK:
            return cls.BANK_TARGETS
        else:
            # Generic targets for unknown types
            return {
                "about_selectors": [".about", "#about", ".overview", "#overview"],
                "contact_selectors": [".contact", "#contact", ".address", "footer"],
                "facts_selectors": [".facts", "#facts", ".stats", "#stats"],
                "priority_keywords": ["about", "contact", "information", "company"]
            }
    
    @classmethod
    def get_css_extraction_schema(cls, institution_type: InstitutionType) -> Dict[str, Any]:
        """Get a structured extraction schema for CSS-based extraction."""
        targets = cls.get_targets_for_type(institution_type)
        
        schema = {
            "name": f"{institution_type.value.title()} Information Extractor",
            "baseSelector": "body",
            "fields": []
        }
        
        # Add about information fields
        for i, selector in enumerate(targets["about_selectors"][:3]):  # Limit to top 3
            schema["fields"].append({
                "name": f"about_content_{i+1}",
                "selector": selector,
                "type": "text",
                "transform": "strip"
            })
        
        # Add contact information fields
        for i, selector in enumerate(targets["contact_selectors"][:3]):
            schema["fields"].append({
                "name": f"contact_info_{i+1}",
                "selector": selector,
                "type": "text",
                "transform": "strip"
            })
        
        # Add facts/statistics fields
        for i, selector in enumerate(targets["facts_selectors"][:2]):
            schema["fields"].append({
                "name": f"facts_stats_{i+1}",
                "selector": selector,
                "type": "text",
                "transform": "strip"
            })
        
        return schema
    
    @classmethod
    def detect_institution_type(cls, url: str, title: str = "", content: str = "") -> InstitutionType:
        """Auto-detect institution type from URL, title, and content."""
        text_to_analyze = f"{url} {title} {content}".lower()
        
        # University indicators
        university_indicators = [
            ".edu", "university", "college", "academic", "student", 
            "faculty", "campus", "degree", "education", "school"
        ]
        
        # Hospital indicators  
        hospital_indicators = [
            "hospital", "medical", "health", "clinic", "care",
            "patient", "doctor", "healthcare", "medicine"
        ]
        
        # Bank indicators
        bank_indicators = [
            "bank", "banking", "financial", "finance", "credit",
            "loan", "deposit", "branch", "investment"
        ]
        
        # Count matches for each type
        university_score = sum(1 for indicator in university_indicators if indicator in text_to_analyze)
        hospital_score = sum(1 for indicator in hospital_indicators if indicator in text_to_analyze)
        bank_score = sum(1 for indicator in bank_indicators if indicator in text_to_analyze)
        
        # Return type with highest score
        max_score = max(university_score, hospital_score, bank_score)
        if max_score == 0:
            return InstitutionType.UNKNOWN
        elif university_score == max_score:
            return InstitutionType.UNIVERSITY
        elif hospital_score == max_score:
            return InstitutionType.HOSPITAL
        else:
            return InstitutionType.BANK


def create_default_config(institution_type: InstitutionType = InstitutionType.UNKNOWN,
                         strategy: CrawlingStrategy = CrawlingStrategy.SIMPLE) -> CrawlerConfig:
    """Create a default crawler configuration for the given institution type and strategy."""
    config = CrawlerConfig(
        institution_type=institution_type,
        crawling_strategy=strategy
    )
    
    # Adjust settings based on strategy
    if strategy == CrawlingStrategy.ADVANCED:
        config.java_script_enabled = True
        config.delay_before_return_html = 3.0
        config.page_timeout = 45000
        config.simulate_user = True
    elif strategy == CrawlingStrategy.COMPREHENSIVE:
        config.java_script_enabled = True
        config.delay_before_return_html = 5.0
        config.page_timeout = 60000
        config.max_pages_per_domain = 10
        config.simulate_user = True
        config.take_screenshot = True
    
    # Adjust settings based on institution type
    if institution_type == InstitutionType.UNIVERSITY:
        config.max_pages_per_domain = 8  # Universities often have more relevant pages
        config.word_count_threshold = 150
    elif institution_type == InstitutionType.HOSPITAL:
        config.max_pages_per_domain = 6
        config.word_count_threshold = 100
    elif institution_type == InstitutionType.BANK:
        config.max_pages_per_domain = 4  # Banks typically have more focused content
        config.word_count_threshold = 80
    
    return config
