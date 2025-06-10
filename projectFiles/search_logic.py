from google.genai.types import Tool, GoogleSearch, GenerateContentConfig
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

# The reason I'm using LLMs for this and not a search API is the current ones are
# either rate limited (100-2k requests) or they'll be out of service soon (bing in october or so)
# so I didn't want to mess with them, there are some other options but they need to be checked
def fetch_raw_institution_text_LLM_version(genai_client, institution_name: str):
    """
    Fetches a general raw text description of an institution using an LLM call
    enhanced with Google Search for grounding. (see reason for this above)

    Args:
        genai_client: The initialized Google Generative AI client.
        institution_name: The name of the institution to search for.

    Returns:
        A dictionary containing the raw text or an error message.
    """
    if not genai_client:
        return {"error": "Generative AI client not available for search."}

    # Has to be edited
    raw_text_prompt = (
        f"Provide a general overview or description of the institution: '{institution_name}'. "
        f"Include any publicly known details that might be relevant for understanding its nature, "
        f"such as its focus, type, location hints, or scale if widely known. "
        f"Prioritize information from reliable sources. "
        f"If you cannot find reliable information or the institution seems fictional or too obscure, please state that clearly in your response."
    )
    
    try:
        google_search_tool = Tool(google_search=GoogleSearch())
        config = GenerateContentConfig(tools=[google_search_tool])
        
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=raw_text_prompt,
            config=config
        )

        raw_text = ""
        if response:
            # Check for prompt_feedback and then block_reason
            if response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                return {"error": f"Raw text generation blocked. Reason: {response.prompt_feedback.block_reason}"}
            
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                text_parts = [part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')]
                raw_text = "".join(text_parts).strip()
            elif hasattr(response, 'text') and response.text:
                raw_text = response.text.strip()

            if not raw_text:
                return {"error": "LLM returned no raw text for the institution after search."}
            return {"text": raw_text}
        else:
            return {"error": "No response from LLM for raw text generation with search."}

    except Exception as e:
        print(f"Error getting raw text for {institution_name} using search: {e}")
        return {"error": f"Exception during raw text generation with search: {str(e)}"}