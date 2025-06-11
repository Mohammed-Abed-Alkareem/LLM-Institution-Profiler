"""
Link extraction and crawling preparation for institution data.
"""
import os
from typing import List, Dict
from search.search_service import SearchService


class InstitutionLinkManager:
    """Manages links for institution crawling and data extraction."""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.getcwd()
        self.search_service = SearchService(base_dir)
    def get_crawling_links(self, institution_name: str, institution_type: str = None, 
                          max_links: int = 10, include_search_metadata: bool = True, search_params: dict = None) -> Dict:
        """
        Get links for institution crawling with metadata.
        
        Args:
            institution_name: Name of the institution
            institution_type: Type of institution (if known)
            max_links: Maximum number of links to return
            include_search_metadata: Whether to include search metadata
            search_params: Enhanced search parameters (location, keywords, domain_hint, exclude_terms)
            
        Returns:
            Dictionary with links and metadata for crawling
        """
        # Get search results with links using enhanced search params
        search_result = self.search_service.search_institution(institution_name, institution_type, search_params=search_params)
        
        crawling_data = {
            'institution_name': institution_name,
            'institution_type': institution_type,
            'search_successful': search_result.get('success', False),
            'links': [],
            'metadata': {}
        }
        
        if not search_result.get('success'):
            crawling_data['error'] = search_result.get('error', 'Search failed')
            return crawling_data
        
        # Extract links from search results
        links = []
        for item in search_result.get('results', []):
            link = item.get('link')
            if link and link not in links:
                links.append({
                    'url': link,
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'display_link': item.get('displayLink', ''),
                    'priority': self._calculate_link_priority(link, item, institution_type)
                })
                
                if len(links) >= max_links:
                    break
        
        # Sort by priority (higher is better)
        links.sort(key=lambda x: x['priority'], reverse=True)
        crawling_data['links'] = links
        
        if include_search_metadata:
            crawling_data['metadata'] = {
                'total_search_results': search_result.get('total_results', '0'),
                'search_time': search_result.get('search_time', 0),
                'cache_hit': search_result.get('cache_hit', False),
                'source': search_result.get('source', 'unknown'),
                'response_time': search_result.get('response_time', 0)
            }
        
        return crawling_data
    
    def _calculate_link_priority(self, url: str, search_item: Dict, institution_type: str = None) -> int:
        """Calculate priority score for a link (higher = better)."""
        priority = 0
        url_lower = url.lower()
        title_lower = search_item.get('title', '').lower()
        
        # Official domain indicators (highest priority)
        if any(domain in url_lower for domain in ['.edu', '.org', '.gov']):
            priority += 100
        
        # Institution type specific priorities
        if institution_type:
            if institution_type.lower() in ['university', 'college', 'school', 'edu']:
                if any(edu_indicator in url_lower for edu_indicator in ['.edu', 'university', 'college']):
                    priority += 50
                if any(edu_word in title_lower for edu_word in ['university', 'college', 'school']):
                    priority += 30
            
            elif institution_type.lower() in ['hospital', 'clinic', 'medical', 'med']:
                if any(med_indicator in url_lower for med_indicator in ['hospital', 'medical', 'health']):
                    priority += 50
                if any(med_word in title_lower for med_word in ['hospital', 'medical', 'health', 'clinic']):
                    priority += 30
            
            elif institution_type.lower() in ['bank', 'financial', 'fin']:
                if any(fin_indicator in url_lower for fin_indicator in ['bank', 'financial']):
                    priority += 50
                if any(fin_word in title_lower for fin_word in ['bank', 'financial']):
                    priority += 30
        
        # Homepage indicators
        if any(homepage in url_lower for homepage in ['/', '/home', '/index', '/about']):
            priority += 20
        
        # Official pages
        if any(official in title_lower for official in ['official', 'homepage', 'home']):
            priority += 15
        
        # Avoid less useful pages
        if any(avoid in url_lower for avoid in ['facebook', 'twitter', 'linkedin', 'wikipedia']):
            priority -= 20
        
        return priority
    
    def prepare_crawling_config(self, institution_data: Dict, crawl_depth: int = 2) -> Dict:
        """
        Prepare configuration for web crawling based on institution data.
        
        Args:
            institution_data: Data from get_crawling_links()
            crawl_depth: How deep to crawl (1 = just provided links, 2+ = follow links)
            
        Returns:
            Crawling configuration dictionary
        """
        config = {
            'institution_name': institution_data['institution_name'],
            'institution_type': institution_data['institution_type'],
            'seed_urls': [link['url'] for link in institution_data['links']],
            'crawl_depth': crawl_depth,
            'crawl_settings': {
                'max_pages_per_domain': 10,
                'respect_robots_txt': True,
                'delay_between_requests': 1.0,
                'timeout': 30,
                'max_file_size': 5 * 1024 * 1024,  # 5MB
                'allowed_content_types': ['text/html', 'text/plain'],
                'exclude_patterns': [
                    r'\.pdf$', r'\.doc$', r'\.docx$', r'\.ppt$', r'\.pptx$',
                    r'/search\?', r'/login', r'/register', r'/cart',
                    r'facebook\.com', r'twitter\.com', r'linkedin\.com'
                ]
            },
            'extraction_targets': self._get_extraction_targets(institution_data['institution_type']),
            'metadata': institution_data.get('metadata', {})
        }
        
        return config
    
    def _get_extraction_targets(self, institution_type: str = None) -> List[str]:
        """Get target information types for extraction based on institution type."""
        common_targets = [
            'institution_name', 'official_name', 'address', 'city', 'state', 'country',
            'phone', 'email', 'website', 'description', 'established_date'
        ]
        
        if not institution_type:
            return common_targets
        
        type_lower = institution_type.lower()
        
        if type_lower in ['university', 'college', 'school', 'edu']:
            return common_targets + [
                'student_population', 'faculty_count', 'programs_offered',
                'accreditation', 'ranking', 'tuition_fees', 'campus_size',
                'academic_divisions', 'research_areas'
            ]
        
        elif type_lower in ['hospital', 'clinic', 'medical', 'med']:
            return common_targets + [
                'bed_count', 'medical_specialties', 'services_offered',
                'accreditation', 'certifications', 'emergency_services',
                'staff_count', 'patient_capacity'
            ]
        
        elif type_lower in ['bank', 'financial', 'fin']:
            return common_targets + [
                'institution_type', 'regulatory_body', 'license_number',
                'services_offered', 'branches_count', 'assets_size',
                'founding_date', 'headquarters', 'subsidiaries'
            ]
        
        return common_targets


def get_institution_links_for_crawling(institution_name: str, institution_type: str = None, 
                                     max_links: int = 10, base_dir: str = None, search_params: dict = None) -> Dict:
    """
    Convenience function to get institution links for crawling.
    
    Args:
        institution_name: Name of the institution
        institution_type: Type of institution
        max_links: Maximum number of links to return
        base_dir: Base directory for search service
        search_params: Enhanced search parameters (location, keywords, domain_hint, exclude_terms)
        
    Returns:
        Dictionary with links and metadata for crawling
    """
    link_manager = InstitutionLinkManager(base_dir)
    return link_manager.get_crawling_links(institution_name, institution_type, max_links, search_params=search_params)
