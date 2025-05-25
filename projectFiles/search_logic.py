from google.genai.types import Tool, GoogleSearch, GenerateContentConfig

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