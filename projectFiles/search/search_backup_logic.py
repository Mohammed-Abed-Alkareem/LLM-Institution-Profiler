from search.search_service import SearchService
from crawling_prep import get_institution_links_for_crawling
import os

# Initialize search service
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
search_service = SearchService(BASE_DIR)

def fetch_raw_institution_text_api_version(institution_name: str, institution_type: str = None):
    """
    Fetches raw text about an institution using Google Custom Search API with caching.
    
    Args:
        institution_name: The name of the institution to search for.
        institution_type: Optional type of institution (university, hospital, bank, etc.)
        
    Returns:
        A dictionary containing the search results or an error message.
    """
    if not search_service.is_ready():
        return {"error": "Search service not configured. Please set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables."}
    
    try:
        result = search_service.search_institution(institution_name, institution_type)
        
        if not result.get('success', False):
            return {"error": result.get('error', 'Search failed')}
        
        # Extract text content from search results
        text_content = []
        links = []
        
        for item in result.get('results', []):
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            link = item.get('link', '')
            
            if title:
                text_content.append(f"Title: {title}")
            if snippet:
                text_content.append(f"Description: {snippet}")
            if link:
                links.append(link)
            text_content.append("---")
        
        combined_text = "\n".join(text_content)
        
        return {
            "text": combined_text,
            "links": links,
            "total_results": result.get('total_results', '0'),
            "search_time": result.get('search_time', 0),
            "cache_hit": result.get('cache_hit', False),
            "source": result.get('source', 'api')
        }
        
    except Exception as e:
        return {"error": f"Exception during search: {str(e)}"}

def get_institution_links_for_crawling(institution_name: str, institution_type: str = None, max_links: int = 10):
    """
    Get links for an institution that can be used for web crawling.
    This function now includes priority scoring and crawling preparation.
    
    Args:
        institution_name: Name of the institution
        institution_type: Optional type of institution
        max_links: Maximum number of links to return
        
    Returns:
        Dictionary with prioritized links and crawling metadata
    """
    if not search_service.is_ready():
        return {
            'institution_name': institution_name,
            'institution_type': institution_type,
            'search_successful': False,
            'error': 'Search service not configured',
            'links': [],
            'metadata': {}
        }
      # Use the enhanced crawling preparation function
    return get_institution_links_for_crawling(institution_name, institution_type, max_links, BASE_DIR)