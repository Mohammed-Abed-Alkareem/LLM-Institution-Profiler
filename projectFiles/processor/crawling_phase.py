# -*- coding: utf-8 -*-
"""
Crawling phase handler for the institution processing pipeline.
Manages comprehensive web crawling and content extraction.
"""
import asyncio
import time
from typing import Dict, List, Optional
from .config import DEFAULT_MAX_PAGES, INSTITUTION_TYPE_KEYWORDS, CONTENT_LIMITS
from crawler import CrawlerService, CrawlingStrategy, InstitutionType


class CrawlingPhaseHandler:
    """Handles the crawling phase of institution processing."""
    
    def __init__(self, base_dir: str, crawler_service: CrawlerService):
        self.base_dir = base_dir
        self.crawler_service = crawler_service
    
    def execute_crawling_phase(
        self,
        institution_name: str,
        links: List[Dict],
        institution_type: Optional[str] = None,
        max_pages: int = DEFAULT_MAX_PAGES
    ) -> Dict:
        """
        Execute the crawling phase to extract detailed content.
        
        Args:
            institution_name: Name of the institution
            links: List of URLs to crawl
            institution_type: Type of institution
            max_pages: Maximum number of pages to crawl
            
        Returns:
            Dict containing crawling results and extracted content
        """
        if not links:
            return {
                'success': False,
                'error': 'No URLs available for crawling',
                'crawled_data': {},
                'content_summary': {}
            }
        
        print(f"🕷️ Phase 2: Comprehensive crawling of {len(links)} URLs...")
        
        crawling_start_time = time.time()
        
        try:
            # Detect institution type if not provided
            detected_type = self._detect_institution_type(links, institution_type)
              # Convert to enum
            inst_type_enum = self._convert_to_institution_type_enum(detected_type)
            
            # Run async crawling
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            crawl_result = loop.run_until_complete(
                self.crawler_service.crawl_institution_urls(
                    institution_name=institution_name,
                    urls=[link['url'] for link in links],
                    institution_type=detected_type,  # Pass string instead of enum
                    max_pages=max_pages,
                    strategy=CrawlingStrategy.ADVANCED
                )
            )
            
            loop.close()
            
            crawling_time = time.time() - crawling_start_time
            
            # Process and organize crawled content
            processed_content = self._process_crawled_content(crawl_result)
            
            result = {
                'success': True,
                'crawling_time': crawling_time,
                'detected_type': detected_type,
                'crawled_data': crawl_result,
                'content_summary': processed_content,
                'pages_crawled': len(crawl_result.get('crawled_pages', [])),
                'successful_pages': sum(1 for page in crawl_result.get('crawled_pages', []) if page.get('success'))
            }
            
            print(f"✅ Crawling completed: {result['pages_crawled']} pages, "
                  f"{result['successful_pages']} successful in {crawling_time:.2f}s")
            
            return result
            
        except Exception as e:
            crawling_time = time.time() - crawling_start_time
            print(f"⚠️ Crawling failed: {str(e)}")
            
            return {
                'success': False,
                'error': f"Crawling failed: {str(e)}",
                'crawling_time': crawling_time,
                'crawled_data': {},
                'content_summary': {}
            }
    
    def _detect_institution_type(self, links: List[Dict], provided_type: Optional[str]) -> str:
        """Detect institution type from URLs and content if not provided."""
        if provided_type:
            return provided_type
        
        # Analyze top 3 links for type detection
        for link in links[:3]:
            url = link.get('url', '').lower()
            title = link.get('title', '').lower()
            snippet = link.get('snippet', '').lower()
            content = f"{url} {title} {snippet}"
            
            for inst_type, keywords in INSTITUTION_TYPE_KEYWORDS.items():
                if inst_type != 'general' and any(word in content for word in keywords):
                    return inst_type
        
        return 'general'
    
    def _convert_to_institution_type_enum(self, type_str: str) -> InstitutionType:
        """Convert string type to InstitutionType enum."""
        try:
                    return InstitutionType(type_str.lower())
        except ValueError:
            return InstitutionType.GENERAL
    
    def _process_crawled_content(self, crawl_result: Dict) -> Dict:
        """Process and organize crawled content into structured format."""
        all_images = []
        logos_found = []
        facility_images = []
        social_media_links = {}
        documents_found = []
        total_content = ""
        page_summaries = []
        
        for page in crawl_result.get('crawled_pages', []):
            if not page.get('success') or not page.get('processed_content'):
                continue
                
            processed = page['processed_content']
            
            # Extract image data from the actual crawler structure
            # Check for images in the media section
            page_images = processed.get('media', {}).get('images', [])
            
            # Also get logos detected by the crawler
            page_logos = processed.get('logos', [])
            
            # Process regular images
            for img in page_images:
                img_with_source = {
                    'url': img.get('src', ''),
                    'alt': img.get('alt', ''),
                    'type': img.get('type', 'image'),
                    'score': img.get('score', 0),
                    'source_page': page.get('url', ''),
                    'page_title': page.get('title', ''),
                    'category': 'general_image'
                }
                all_images.append(img_with_source)
            
            # Process detected logos
            for logo in page_logos:
                logo_with_source = {
                    'url': logo.get('src', ''),
                    'alt': logo.get('alt', ''),
                    'confidence': logo.get('confidence', 'medium'),
                    'detected_by': logo.get('detected_by', []),
                    'source_page': page.get('url', ''),
                    'page_title': page.get('title', ''),
                    'category': 'logo'
                }
                logos_found.append(logo_with_source)
                all_images.append(logo_with_source)  # Also add to all images
            
            # Check for facility images (images with certain keywords)
            for img in page_images:
                img_alt = (img.get('alt', '') or '').lower()
                img_desc = (img.get('desc', '') or '').lower()
                if any(keyword in f"{img_alt} {img_desc}" for keyword in ['building', 'campus', 'facility', 'office', 'hospital', 'bank', 'center']):
                    facility_img = {
                        'url': img.get('src', ''),
                        'alt': img.get('alt', ''),
                        'type': img.get('type', 'image'),
                        'score': img.get('score', 0),
                        'source_page': page.get('url', ''),
                        'page_title': page.get('title', ''),
                        'category': 'facility_image'
                    }
                    facility_images.append(facility_img)
            
            # Aggregate social media links from links section
            page_links = processed.get('links', {})
            for link_type in ['internal', 'external']:
                for link in page_links.get(link_type, []):
                    link_url = link.get('href', '') if isinstance(link, dict) else str(link)
                    link_url_lower = link_url.lower()
                    
                    # Detect social media platforms
                    for platform in ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube']:
                        if platform in link_url_lower:
                            if platform not in social_media_links:
                                social_media_links[platform] = []
                            social_media_links[platform].append(link_url)
            
            # Collect important documents from links
            page_links = processed.get('links', {})
            for link_type in ['internal', 'external']:
                for link in page_links.get(link_type, []):
                    link_url = link.get('href', '') if isinstance(link, dict) else str(link)
                    link_text = link.get('text', '') if isinstance(link, dict) else ''
                    
                    # Check for document extensions or keywords
                    if any(ext in link_url.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']):
                        documents_found.append({
                            'url': link_url,
                            'text': link_text,
                            'type': 'document',
                            'source_page': page.get('url', ''),
                            'page_title': page.get('title', '')
                        })
            
            # Add cleaned text content
            text_content = processed.get('content_formats', {}).get('text_content', '')
            if text_content and len(text_content.strip()) > 100:
                total_content += f"\n\n--- Content from {page.get('url', 'Unknown URL')} ---\n"
                total_content += text_content[:2000]  # Limit per page
            
            # Store page summary
            page_summaries.append({
                'url': page.get('url', ''),
                'title': page.get('title', ''),
                'quality_score': page.get('content_quality_score', 0),
                'word_count': page.get('word_count', 0),
                'key_info': processed.get('institution_hints', {}),
                'content_sections': {
                    'images_count': len(page_images),
                    'logos_count': len(page_logos),
                    'text_length': len(text_content)
                }
            })
        
        # Remove duplicates and apply limits
        return {
            'total_text': total_content,
            'page_summaries': page_summaries,
            'all_images': self._deduplicate_images(all_images),
            'logos_found': self._deduplicate_images(logos_found),
            'facility_images': self._deduplicate_images(facility_images),
            'social_media_links': self._deduplicate_social_links(social_media_links),
            'documents_found': self._deduplicate_documents(documents_found),
            'crawl_summary': crawl_result.get('crawl_summary', {}),
            'statistics': {
                'total_pages_crawled': len(crawl_result.get('crawled_pages', [])),
                'total_images_found': len(all_images),
                'logos_identified': len(logos_found),
                'documents_found': len(documents_found)
            }
        }
    
    def _deduplicate_images(self, images: List[Dict]) -> List[Dict]:
        """Remove duplicate images based on URL."""
        seen_urls = set()
        unique_images = []
        
        for img in images:
            url = img.get('url', img.get('src', ''))
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_images.append(img)
        
        return unique_images[:CONTENT_LIMITS['max_images_per_institution']]
    
    def _deduplicate_social_links(self, social_links: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Remove duplicate social media links."""
        deduplicated = {}
        
        for platform, links in social_links.items():
            unique_links = list(set(links))[:CONTENT_LIMITS['max_social_links_per_platform']]
            if unique_links:
                deduplicated[platform] = unique_links
        
        return deduplicated
    
    def _deduplicate_documents(self, documents: List[Dict]) -> List[Dict]:
        """Remove duplicate documents based on URL."""
        seen_urls = set()
        unique_docs = []
        
        for doc in documents:
            url = doc.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_docs.append(doc)
        
        return unique_docs[:CONTENT_LIMITS['max_documents_per_institution']]
