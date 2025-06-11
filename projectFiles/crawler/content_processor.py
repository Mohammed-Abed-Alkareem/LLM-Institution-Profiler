"""
Institution Profiler Content Processor Module

This module provides basic content cleaning and organization for crawled web content.
The goal is to collect all valuable data and present it in a clean, structured format
for other modules to process and extract insights from.
"""

import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse
from .crawler_config import InstitutionType


class ContentProcessor:
    """
    Content processor for cleaning and organizing crawled web content.
    Focus: Collect all valuable data, minimal processing, maximum data preservation.
    """
    
    def __init__(self):
        """Initialize the content processor."""
        # Basic noise patterns to remove (keep minimal)
        self.noise_patterns = [
            r'<script[^>]*>.*?</script>',  # JavaScript
            r'<style[^>]*>.*?</style>',   # CSS
            r'<!--.*?-->',                # Comments
        ]    
    def process_crawl_result(self, crawl_result: Any, institution_type: InstitutionType) -> Dict[str, Any]:
        """
        Process a crawl4ai result into clean, organized data for other modules to use.
        Captures ALL valuable data formats that crawl4ai provides for benchmarking and comparison.
        
        Args:
            crawl_result: The result from crawl4ai
            institution_type: Type of institution (for reference only)
            
        Returns:
            Dictionary containing ALL organized crawl data
        """
        try:
            # Extract ALL content formats from crawl4ai
            raw_html = crawl_result.html or ""
            cleaned_html = crawl_result.cleaned_html or ""
            
            # Handle markdown - it can be a string or MarkdownGenerationResult object
            markdown_content = ""
            markdown_raw = ""
            markdown_fit_markdown = ""
            markdown_fit_html = ""
            
            if crawl_result.markdown:
                if hasattr(crawl_result.markdown, 'raw_markdown'):
                    # MarkdownGenerationResult object
                    markdown_raw = crawl_result.markdown.raw_markdown or ""
                    markdown_fit_markdown = getattr(crawl_result.markdown, 'fit_markdown', "") or ""
                    markdown_fit_html = getattr(crawl_result.markdown, 'fit_html', "") or ""
                    markdown_content = markdown_raw  # Use raw as primary
                else:
                    # Simple string
                    markdown_content = str(crawl_result.markdown)
                    markdown_raw = markdown_content
            
            # Organize ALL collected data
            organized_data = {
                # Crawl success info
                'success': getattr(crawl_result, 'success', True),
                'status_code': getattr(crawl_result, 'status_code', None),
                'error_message': getattr(crawl_result, 'error_message', None),
                
                # Basic metadata
                'timestamp': datetime.now().isoformat(),
                'url': crawl_result.url,
                'institution_type': institution_type.value if institution_type else 'unknown',
                
                # Page metadata (comprehensive)
                'metadata': crawl_result.metadata or {},
                'title': crawl_result.metadata.get('title', '') if crawl_result.metadata else '',
                'description': crawl_result.metadata.get('description', '') if crawl_result.metadata else '',
                'language': crawl_result.metadata.get('language', 'unknown') if crawl_result.metadata else 'unknown',
                'keywords': crawl_result.metadata.get('keywords', '') if crawl_result.metadata else '',
                'author': crawl_result.metadata.get('author', '') if crawl_result.metadata else '',
                'charset': crawl_result.metadata.get('charset', '') if crawl_result.metadata else '',
                'viewport': crawl_result.metadata.get('viewport', '') if crawl_result.metadata else '',
                
                # ALL content formats (for benchmarking and comparison)
                'content_formats': {
                    'raw_html': raw_html,
                    'cleaned_html': cleaned_html,
                    'markdown': {
                        'raw_markdown': markdown_raw,
                        'fit_markdown': markdown_fit_markdown,
                        'fit_html': markdown_fit_html,
                        'primary_content': markdown_content
                    },
                    'text_content': self._basic_text_extraction(cleaned_html),
                },
                
                # Media and assets (ALL preserved with full details)
                'media': {
                    'images': crawl_result.media.get('images', []) if crawl_result.media else [],
                    'videos': crawl_result.media.get('videos', []) if crawl_result.media else [],
                    'audio': crawl_result.media.get('audio', []) if crawl_result.media else [],
                    'all_media': crawl_result.media or {}
                },
                
                # Links (ALL preserved with full details)
                'links': {
                    'internal': crawl_result.links.get('internal', []) if crawl_result.links else [],
                    'external': crawl_result.links.get('external', []) if crawl_result.links else [],
                    'all_links': crawl_result.links or {}
                },
                
                # Structured data (ALL available formats)
                'structured_data': getattr(crawl_result, 'structured_data', {}),
                'json_ld': getattr(crawl_result, 'json_ld', []),
                'microdata': getattr(crawl_result, 'microdata', {}),
                'rdfa': getattr(crawl_result, 'rdfa', {}),
                
                # Additional crawl4ai outputs
                'screenshot': getattr(crawl_result, 'screenshot', None),
                'meta_tags': getattr(crawl_result, 'meta_tags', {}),
                'page_title': getattr(crawl_result, 'title', ''),
                'headers': getattr(crawl_result, 'headers', {}),
                'cookies': getattr(crawl_result, 'cookies', []),
                'performance_metrics': getattr(crawl_result, 'performance_metrics', {}),
                
                # Content analysis (basic stats for valuable insights)
                'content_analysis': {
                    'sizes': {
                        'raw_html_size': len(raw_html),
                        'cleaned_html_size': len(cleaned_html),
                        'markdown_size': len(markdown_content),
                        'text_length': len(self._basic_text_extraction(cleaned_html)),
                    },
                    'counts': {
                        'images_count': len(crawl_result.media.get('images', [])) if crawl_result.media else 0,
                        'videos_count': len(crawl_result.media.get('videos', [])) if crawl_result.media else 0,
                        'internal_links_count': len(crawl_result.links.get('internal', [])) if crawl_result.links else 0,
                        'external_links_count': len(crawl_result.links.get('external', [])) if crawl_result.links else 0,
                        'total_links_count': len(crawl_result.links.get('internal', []) + crawl_result.links.get('external', [])) if crawl_result.links else 0,
                    },
                    'quality_indicators': {
                        'has_title': bool(crawl_result.metadata.get('title') if crawl_result.metadata else False),
                        'has_description': bool(crawl_result.metadata.get('description') if crawl_result.metadata else False),
                        'has_images': bool(crawl_result.media and crawl_result.media.get('images')),
                        'has_structured_data': bool(getattr(crawl_result, 'structured_data', False) or getattr(crawl_result, 'json_ld', False)),
                        'content_richness_score': self._calculate_content_richness(crawl_result),
                    }
                },
                
                # Logo detection (valuable for institutions)
                'logos': self._detect_logos(crawl_result.media.get('images', []) if crawl_result.media else []),
                
                # Institution-relevant content hints (minimal processing)
                'institution_hints': self._extract_institution_hints(cleaned_html, institution_type)
            }
            
            return organized_data
            
        except Exception as e:
            return {
                'error': f"Error processing crawl result: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'url': getattr(crawl_result, 'url', 'unknown'),
                'institution_type': institution_type.value if institution_type else 'unknown',
            }

    def _basic_text_extraction(self, html_content: str) -> str:
        """Extract basic clean text from HTML content (minimal processing)."""
        try:
            # Remove basic noise patterns only
            clean_content = html_content
            for pattern in self.noise_patterns:
                clean_content = re.sub(pattern, '', clean_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            clean_content = re.sub(r'<[^>]+>', ' ', clean_content)
            
            # Basic whitespace cleanup
            clean_content = re.sub(r'\s+', ' ', clean_content)
            clean_content = clean_content.strip()
            
            return clean_content
        except Exception as e:
            return f"Error extracting text: {str(e)}"
        
    def _calculate_content_richness(self, crawl_result) -> int:
        """Calculate a basic content richness score (0-100) based on available data."""
        try:
            score = 0
            
            # Content presence (40 points total)
            if crawl_result.html:
                score += 10
            if crawl_result.cleaned_html:
                score += 10
            if crawl_result.markdown:
                score += 10
            if len(crawl_result.html or "") > 1000:
                score += 10
            
            # Media richness (30 points total)
            if crawl_result.media:
                if crawl_result.media.get('images'):
                    score += 15
                if crawl_result.media.get('videos'):
                    score += 10
                if len(crawl_result.media.get('images', [])) > 5:
                    score += 5
            
            # Metadata quality (20 points total)
            if crawl_result.metadata:
                if crawl_result.metadata.get('title'):
                    score += 5
                if crawl_result.metadata.get('description'):
                    score += 5
                if crawl_result.metadata.get('keywords'):
                    score += 5
                if crawl_result.metadata.get('language'):
                    score += 5
            
            # Structured data (10 points total)
            if getattr(crawl_result, 'structured_data', None):
                score += 5
            if getattr(crawl_result, 'json_ld', None):
                score += 5
            
            return min(score, 100)  # Cap at 100
            
        except Exception:
            return 0    
    def _detect_logos(self, images: List[Dict]) -> List[Dict]:
        """Detect potential logos from image list using simple heuristics."""
        try:
            logos = []
            
            for img in images[:20]:  # Limit to first 20 images for performance
                img_url = img.get('src', '').lower()
                img_alt = img.get('alt', '').lower()
                img_class = img.get('class', '').lower()
                img_id = img.get('id', '').lower()
                img_desc = img.get('desc', '').lower()
                
                # Enhanced logo detection heuristics
                logo_indicators = [
                    # Direct logo keywords
                    'logo' in img_url or 'logo' in img_alt or 'logo' in img_class or 'logo' in img_id or 'logo' in img_desc,
                    'brand' in img_url or 'brand' in img_alt or 'brand' in img_class or 'brand' in img_desc,
                    'emblem' in img_url or 'emblem' in img_alt or 'emblem' in img_class,
                    'seal' in img_url or 'seal' in img_alt or 'seal' in img_class,
                    
                    # Header/navigation context
                    'header' in img_class or 'nav' in img_class or 'navbar' in img_class,
                    'banner' in img_class or 'top' in img_class,
                    
                    # File format indicators
                    img_url.endswith('.svg') or img_url.endswith('.png'),  # Common logo formats
                    
                    # Size indicators (logos are often small or specific sizes)
                    (img.get('width', '0').replace('px', '').isdigit() and 
                     50 <= int(img.get('width', '0').replace('px', '')) <= 400),  # Typical logo size range
                    
                    # University/institution specific indicators
                    'university' in img_alt or 'college' in img_alt or 'institution' in img_alt,
                    'crest' in img_alt or 'shield' in img_alt,
                    
                    # Common logo-related URLs
                    '/logo' in img_url or '/brand' in img_url or '/assets/logo' in img_url,
                    'cent-logo' in img_url,  # Based on the Birzeit example
                    
                    # High-scoring images (crawler's own scoring)
                    img.get('score', 0) >= 4
                ]
                
                # Calculate confidence based on number of indicators
                indicator_count = sum(logo_indicators)
                if indicator_count >= 1:  # At least one indicator
                    confidence = 'high' if indicator_count >= 3 else ('medium' if indicator_count >= 2 else 'low')
                    
                    logos.append({
                        'src': img.get('src', ''),
                        'alt': img.get('alt', ''),
                        'confidence': confidence,
                        'indicator_count': indicator_count,
                        'detected_by': [i for i, indicator in enumerate(logo_indicators) if indicator]
                    })
            
            # Sort by confidence and indicator count
            logos.sort(key=lambda x: (
                {'high': 3, 'medium': 2, 'low': 1}[x['confidence']], 
                x['indicator_count']
            ), reverse=True)
            
            return logos[:5]  # Return top 5 logo candidates
            
        except Exception:
            return []

    def _extract_institution_hints(self, cleaned_html: str, institution_type: InstitutionType) -> Dict[str, Any]:
        """Extract basic institution-relevant hints from content (minimal processing)."""
        try:
            hints = {
                'institution_type': institution_type.value if institution_type else 'unknown',
                'detected_keywords': [],
                'contact_indicators': [],
                'social_media_present': False
            }
            
            # Simple keyword detection based on institution type
            content_lower = cleaned_html.lower()
            
            if institution_type == InstitutionType.UNIVERSITY:
                university_keywords = ['university', 'college', 'students', 'faculty', 'research', 
                                     'academic', 'degree', 'campus', 'admissions', 'enrollment']
                hints['detected_keywords'] = [kw for kw in university_keywords if kw in content_lower]
                
            elif institution_type == InstitutionType.HOSPITAL:
                hospital_keywords = ['hospital', 'medical', 'health', 'patient', 'doctor', 
                                   'care', 'treatment', 'clinic', 'emergency', 'surgery']
                hints['detected_keywords'] = [kw for kw in hospital_keywords if kw in content_lower]
                
            elif institution_type == InstitutionType.BANK:
                bank_keywords = ['bank', 'financial', 'loan', 'credit', 'investment', 
                               'account', 'mortgage', 'savings', 'branch', 'atm']
                hints['detected_keywords'] = [kw for kw in bank_keywords if kw in content_lower]
            
            # Basic contact indicators
            contact_patterns = [
                (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'phone'),
                (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email'),
                (r'\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|boulevard|blvd)', 'address')
            ]
            
            for pattern, contact_type in contact_patterns:
                if re.search(pattern, content_lower):
                    hints['contact_indicators'].append(contact_type)
            
            # Social media presence
            social_indicators = ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube']
            hints['social_media_present'] = any(social in content_lower for social in social_indicators)
            
            return hints
            
        except Exception:
            return {
                'institution_type': institution_type.value if institution_type else 'unknown',
                'detected_keywords': [],
                'contact_indicators': [],
                'social_media_present': False
            }
    
    def calculate_quality_score(self, processed_content: Dict[str, Any]) -> int:
        """Calculate a quality score for processed content (wrapper around _calculate_content_richness)."""
        try:
            # Use the content_analysis.quality_indicators.content_richness_score if available
            if 'content_analysis' in processed_content:
                quality_indicators = processed_content['content_analysis'].get('quality_indicators', {})
                if 'content_richness_score' in quality_indicators:
                    return quality_indicators['content_richness_score']
            
            # Fallback: calculate based on available data
            score = 0
            
            # Content presence (40 points)
            content_formats = processed_content.get('content_formats', {})
            if content_formats.get('raw_html'):
                score += 10
            if content_formats.get('cleaned_html'):
                score += 10
            if content_formats.get('markdown', {}).get('primary_content'):
                score += 10
            if len(content_formats.get('raw_html', '')) > 1000:
                score += 10
            
            # Media richness (30 points)
            media = processed_content.get('media', {})
            if media.get('images'):
                score += 15
            if media.get('videos'):
                score += 10
            if len(media.get('images', [])) > 5:
                score += 5
            
            # Metadata quality (20 points)
            if processed_content.get('title'):
                score += 5
            if processed_content.get('description'):
                score += 5
            if processed_content.get('keywords'):
                score += 5
            if processed_content.get('language', 'unknown') != 'unknown':
                score += 5
            
            # Structured data (10 points)
            if processed_content.get('structured_data'):
                score += 5
            if processed_content.get('json_ld'):
                score += 5
            
            return min(score, 100)
            
        except Exception:
            return 0
