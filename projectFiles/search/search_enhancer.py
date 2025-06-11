"""
Smart search query enhancement system for institution searches.
Configurable system to improve search quality with additional parameters.
"""
from typing import Dict, List, Optional, Tuple
import re


class SearchQueryEnhancer:
    """Enhances search queries with additional context and parameters."""
    
    def __init__(self):
        # Configuration for how different parameters affect queries
        self.enhancement_config = {
            'institution_type': {
                'keywords': {
                    'university': ['education', 'academic', 'college', 'campus'],
                    'college': ['education', 'academic', 'university', 'campus'],
                    'school': ['education', 'academic', 'learning'],
                    'hospital': ['healthcare', 'medical', 'health system', 'clinic'],
                    'clinic': ['healthcare', 'medical', 'health', 'hospital'],
                    'medical': ['healthcare', 'health system', 'hospital'],
                    'bank': ['banking', 'financial', 'finance', 'institution'],
                    'financial': ['banking', 'finance', 'investment'],
                    'government': ['official', 'public', 'agency'],
                    'nonprofit': ['organization', 'foundation', 'charity'],
                    'research': ['institute', 'laboratory', 'science']
                },
                'domain_hints': {
                    'university': ['site:edu', 'site:ac.uk', 'site:edu.au'],
                    'college': ['site:edu', 'site:ac.uk'],
                    'school': ['site:edu', 'site:k12.*.us'],
                    'hospital': ['site:org', 'site:gov', 'site:edu'],
                    'medical': ['site:org', 'site:gov', 'site:edu'],
                    'government': ['site:gov', 'site:gov.*'],
                    'nonprofit': ['site:org']
                }
            },
            'location': {
                'format_patterns': [
                    '{institution} {location}',
                    '{institution} located in {location}',
                    '{location} {institution}'
                ]
            }
        }
    
    def enhance_query(self, institution_name: str, search_params: Dict[str, str] = None) -> Dict[str, any]:
        """
        Enhance a search query with additional parameters.
        
        Args:
            institution_name: Base institution name
            search_params: Dictionary of additional search parameters
                - institution_type: Type of institution
                - location: Geographic location
                - additional_keywords: Extra keywords to include
                - domain_hint: Known domain information
                - exclude_terms: Terms to exclude from results
        
        Returns:
            Dictionary with enhanced query information:
                - primary_query: Main search query
                - site_restrictions: Domain restrictions to try
                - exclude_terms: Terms to exclude
                - query_variations: Alternative query formulations
                - search_strategy: Recommended search approach
        """
        if not search_params:
            search_params = {}
        
        # Clean and prepare parameters
        institution_type = self._clean_param(search_params.get('institution_type', ''))
        location = self._clean_param(search_params.get('location', ''))
        additional_keywords = self._clean_param(search_params.get('additional_keywords', ''))
        domain_hint = self._clean_param(search_params.get('domain_hint', ''))
        exclude_terms = self._clean_param(search_params.get('exclude_terms', ''))
        
        # Auto-detect institution type if not provided
        if not institution_type:
            institution_type = self._auto_detect_type(institution_name)
        
        # Build primary query
        primary_query = self._build_primary_query(
            institution_name, institution_type, location, additional_keywords
        )
        
        # Generate site restrictions
        site_restrictions = self._generate_site_restrictions(institution_type, domain_hint)
        
        # Create query variations for fallback
        query_variations = self._create_query_variations(
            institution_name, institution_type, location, additional_keywords
        )
        
        # Determine search strategy
        search_strategy = self._determine_search_strategy(
            institution_type, location, domain_hint
        )
        
        return {
            'primary_query': primary_query,
            'site_restrictions': site_restrictions,
            'exclude_terms': exclude_terms.split() if exclude_terms else [],
            'query_variations': query_variations,
            'search_strategy': search_strategy,
            'detected_type': institution_type,
            'enhancement_applied': bool(any([institution_type, location, additional_keywords, domain_hint]))
        }
    
    def _clean_param(self, param: str) -> str:
        """Clean and normalize a parameter."""
        if not param:
            return ''
        return param.strip().lower()
    
    def _auto_detect_type(self, institution_name: str) -> str:
        """Auto-detect institution type from name."""
        name_lower = institution_name.lower()
        
        # Educational indicators
        if any(keyword in name_lower for keyword in [
            'university', 'college', 'school', 'institute of technology', 'polytechnic'
        ]):
            return 'university'
        
        # Medical indicators
        if any(keyword in name_lower for keyword in [
            'hospital', 'medical center', 'clinic', 'health system', 'medical'
        ]):
            return 'hospital'
        
        # Financial indicators
        if any(keyword in name_lower for keyword in [
            'bank', 'credit union', 'financial', 'trust', 'savings'
        ]):
            return 'bank'
        
        # Government indicators
        if any(keyword in name_lower for keyword in [
            'department of', 'ministry', 'agency', 'bureau', 'commission'
        ]):
            return 'government'
        
        return ''
    
    def _build_primary_query(self, institution_name: str, institution_type: str, 
                           location: str, additional_keywords: str) -> str:
        """Build the primary search query."""
        query_parts = [institution_name]
        
        # Add institution type if specified
        if institution_type:
            query_parts.append(institution_type)
            
            # Add relevant keywords for the type
            type_keywords = self.enhancement_config['institution_type']['keywords'].get(
                institution_type, []
            )
            if type_keywords:
                # Add the most relevant keyword
                query_parts.append(type_keywords[0])
        
        # Add location
        if location:
            query_parts.append(location)
        
        # Add additional keywords
        if additional_keywords:
            query_parts.extend(additional_keywords.split())
        
        return ' '.join(query_parts)
    
    def _generate_site_restrictions(self, institution_type: str, domain_hint: str) -> List[str]:
        """Generate site restrictions for the search."""
        restrictions = []
        
        # Add domain hint if provided
        if domain_hint:
            if not domain_hint.startswith('site:'):
                domain_hint = f'site:{domain_hint}'
            restrictions.append(domain_hint)
        
        # Add type-based restrictions
        if institution_type:
            type_domains = self.enhancement_config['institution_type']['domain_hints'].get(
                institution_type, []
            )
            restrictions.extend(type_domains)
        
        # Default institutional domains
        if not restrictions:
            restrictions = ['site:edu OR site:org OR site:gov']
        
        return restrictions
    
    def _create_query_variations(self, institution_name: str, institution_type: str,
                               location: str, additional_keywords: str) -> List[str]:
        """Create alternative query formulations for fallback searches."""
        variations = []
        
        # Basic name + type
        if institution_type:
            variations.append(f'"{institution_name}" {institution_type}')
        
        # Name + location
        if location:
            variations.append(f'"{institution_name}" {location}')
            variations.append(f'{institution_name} located in {location}')
        
        # Name + additional keywords
        if additional_keywords:
            variations.append(f'"{institution_name}" {additional_keywords}')
        
        # Exact name match
        variations.append(f'"{institution_name}"')
        
        # Name without quotes (broader search)
        variations.append(institution_name)
        
        return variations
    
    def _determine_search_strategy(self, institution_type: str, location: str, 
                                 domain_hint: str) -> Dict[str, any]:
        """Determine the best search strategy based on parameters."""
        strategy = {
            'use_official_sites_first': True,
            'fallback_to_general': True,
            'max_results_per_query': 10,
            'combine_results': True
        }
        
        # Adjust strategy based on parameters
        if domain_hint:
            strategy['use_official_sites_first'] = True
            strategy['max_results_per_query'] = 5  # Focus on specific domain
        
        if institution_type in ['government', 'university']:
            strategy['use_official_sites_first'] = True
            strategy['max_results_per_query'] = 8
        
        if location and not domain_hint:
            strategy['fallback_to_general'] = True
            strategy['max_results_per_query'] = 12  # Need more results to filter by location
        
        return strategy
    
    def format_search_query_for_api(self, enhanced_query: Dict[str, any]) -> Tuple[str, str]:
        """
        Format the enhanced query for the Google Search API.
        
        Returns:
            Tuple of (query_string, site_restriction)
        """
        query = enhanced_query['primary_query']
        site_restriction = None
        
        # Use the first site restriction if available
        if enhanced_query['site_restrictions']:
            site_restriction = enhanced_query['site_restrictions'][0]
        
        # Add exclusions to query
        if enhanced_query['exclude_terms']:
            exclusions = ' '.join(f'-{term}' for term in enhanced_query['exclude_terms'])
            query = f'{query} {exclusions}'
        
        return query, site_restriction
    
    def get_enhancement_suggestions(self, institution_name: str) -> Dict[str, List[str]]:
        """Get suggestions for enhancement parameters based on institution name."""
        detected_type = self._auto_detect_type(institution_name)
        
        suggestions = {
            'institution_type': [],
            'location_examples': ['Boston', 'California', 'London', 'New York'],
            'keyword_suggestions': [],
            'domain_hints': []
        }
        
        # Type suggestions
        if detected_type:
            suggestions['institution_type'] = [detected_type]
            type_keywords = self.enhancement_config['institution_type']['keywords'].get(
                detected_type, []
            )
            suggestions['keyword_suggestions'] = type_keywords[:3]
        else:
            suggestions['institution_type'] = ['university', 'hospital', 'bank', 'government']
        
        return suggestions
