# processing_logic.py
import os
import json
from google import genai
from google.genai.types import Tool, GoogleSearch, GenerateContentConfig 

from search_logic import fetch_raw_institution_text_LLM_version
from extraction_logic import extract_structured_data, STRUCTURED_INFO_KEYS

# I'm using google for now, but OpenAI's library can be used for everything if you
# change the link since they all support its API

# TODO: switch to OpenAI's library if we want to use it

# Get the key from https://aistudio.google.com/app/apikey
# If environmental variables aren't detected, try to set it in VScode directly
# The client gets passed to the other modules.
try:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        print("Warning: GOOGLE_API_KEY environment variable not set. AI features will be limited.")
        genai_client = None
    else:
        genai_client = genai.Client(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Fatal Error: Could not configure Google Generative AI Client: {e}")
    genai_client = None

# pipeline flow here
def process_institution_pipeline(institution_name: str):
    """
    Coordinates the pipeline for processing an institution's name:
    1. Fetches raw descriptive text about the institution (using search).
    2. Extracts structured information from that raw text.
    
    Args:
        institution_name: The name of the institution to process.

    Returns:
        A dictionary containing structured data about the institution,
        including raw text, source notes, and any errors encountered.
        Example:
        {
            "name": "Institution Name",
            "address": "...",
            "country": "...",
            "number_of_employees": "...",
            "entity_type": "...",
            "description_raw": "Full raw text fetched...",
            "data_source_notes": "Details about how data was fetched/processed",
            "error": "Error message if any, else null"
        }
    """
    # Initialize the base structure to ensure 
    # consistent keys even if errors happen early on
    final_result = {key: "Unknown" for key in STRUCTURED_INFO_KEYS}
    final_result["name"] = institution_name if institution_name else "Unknown"
    final_result["description_raw"] = "N/A"
    final_result["data_source_notes"] = ""
    final_result["error"] = None

    if not institution_name:
        final_result["error"] = "No institution name provided."
        final_result["data_source_notes"] = "Processing aborted: No institution name."
        return final_result

    if not genai_client:
        final_result["error"] = "Generative AI client not available."
        final_result["data_source_notes"] = "Processing aborted: AI client not configured."
        return final_result

    # Fetch raw descriptive text
    raw_text_data = fetch_raw_institution_text_LLM_version(genai_client, institution_name)

    if "error" in raw_text_data and raw_text_data["error"]:
        final_result["error"] = f"Failed to fetch raw text: {raw_text_data['error']}"
        final_result["data_source_notes"] = "Error during raw text fetching with search."
        return final_result
    
    raw_text = raw_text_data.get("text", "")
    final_result["description_raw"] = raw_text
    final_result["data_source_notes"] = "Raw text fetched using LLM with Google Search. "

    if not raw_text:
        final_result["error"] = "No raw text content was fetched or returned."
        final_result["data_source_notes"] += "Extraction step skipped due to no raw text."
        return final_result

    # Extract information from the raw text
    structured_info = extract_structured_data(genai_client, raw_text, institution_name)

    # Merge extracted data
    for key in STRUCTURED_INFO_KEYS:
        if key in structured_info:
            final_result[key] = structured_info[key]
    
    if "error" in structured_info and structured_info["error"]:
        final_result["error"] = (final_result["error"] + "; " if final_result["error"] else "") + f"Extraction issue: {structured_info['error']}"
        final_result["data_source_notes"] += "Error during structured data extraction from raw text."
        if "raw_llm_output" in structured_info: # Include raw output from LLM if JSON parsing failed
             final_result["extraction_raw_llm_output"] = structured_info["raw_llm_output"]
    else:
        final_result["data_source_notes"] += "Structured data extracted by LLM from raw text."
        # Ensure the name from extraction (which might be more accurate or normalized) is used
        if "name" in structured_info and structured_info["name"] != "Unknown":
            final_result["name"] = structured_info["name"]


    return final_result

def get_institution_profile(institution_name, document_text=None):
    """
    Generates a general textual profile for an institution.
    If document_text is provided, it uses that. Otherwise, it uses general knowledge
    potentially augmented by Google Search (if no document_text).
    This function provides a narrative description rather than structured data.
    (for quick summary)
    """
    if not institution_name:
        return None

    if not genai_client: 
        return {
            "name": institution_name,
            "description": "Generative AI client not available or not configured.", 
            "details": "Please ensure GOOGLE_API_KEY is set and client is initialized." 
        }

    try:
        prompt: str
        details_source: str
        api_config = None

        # Has to be edited
        if document_text:
            prompt = (
                f"From the following document about '{institution_name}', provide a concise profile. "
                f"Summarize its primary focus, type, country, and notable characteristics. "
                f"If the document does not provide sufficient information for a profile, or if the information is contradictory or unclear, please state that. "
                f"Document text:\n\n{document_text}\n\nProfile:"
            )
            details_source = "Profile based on provided document text (Google Generative AI)."
        else:
            prompt = (
                f"Provide a concise profile for the institution: '{institution_name}'. "
                f"Include its primary focus/type, country, and notable characteristics. "
                f"If specific information is unavailable or the institution is unknown/fictional, please indicate this in your response. "
                f"Keep the response to a few sentences."
            )
            details_source = "Profile based on general knowledge (Google Generative AI with Search)."
            google_search_tool = Tool(google_search=GoogleSearch())
            api_config = GenerateContentConfig(tools=[google_search_tool])
            
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config=api_config 
        )
        
        generated_description = "No information generated."
        if response:
            # Check for prompt_feedback and then block_reason
            if response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                generated_description = f"Content generation blocked. Reason: {response.prompt_feedback.block_reason}"
            elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                text_parts = [part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')]
                generated_description = "".join(text_parts).strip() if text_parts else "No text in response parts."
            elif hasattr(response, 'text') and response.text:
                generated_description = response.text.strip()
            
            if not generated_description or generated_description == "No information generated.":
                 generated_description = "AI returned an empty response or no relevant text."
        else: 
            generated_description = "No response received from AI."

        return {
            "name": institution_name,
            "description": generated_description,
            "details": details_source
        }
    except Exception as e:
        print(f"Error in get_institution_profile for {institution_name}: {e}")
        return {
            "name": institution_name,
            "description": "Could not generate profile due to an error.",
            "details": f"Error: {str(e)}"
        }

if __name__ == '__main__':
    test_institutions = [
        "Massachusetts Institute of Technology", 
        "University of Oxford", 
        "A small local bakery called 'The Sweet Spot'", 
        "Globex Corporation (fictional)",
        "An institution that does not exist XYZ123"
    ]
    
    print("Starting institution processing pipeline tests...\n")
    for inst_name in test_institutions:
        print(f"--- Processing Pipeline for: {inst_name} ---")
        structured_data = process_institution_pipeline(inst_name)
        print("Final Structured Data:")
        print(json.dumps(structured_data, indent=2))
        print("--------------------------------------------------\n")

    print("\n--- Testing get_institution_profile (general textual profile) ---")
    profile = get_institution_profile("Stanford University")
    if profile:
        print("Profile for Stanford University:")
        print(json.dumps(profile, indent=2))
    print("--------------------------------------------------\n")

    sample_doc_text = """
    Tech Solutions Inc. is a for-profit company based in Silicon Valley, USA. 
    It was founded in 2010 and employs approximately 250 people. 
    Their main office is at 123 Innovation Drive, Techville, CA 94000.
    They specialize in cloud software.
    """
    print("\n--- Testing get_institution_profile (with document text) ---")
    profile_with_doc = get_institution_profile("Tech Solutions Inc.", document_text=sample_doc_text)
    if profile_with_doc:
         print("Profile for Tech Solutions Inc. (from doc):")
         print(json.dumps(profile_with_doc, indent=2))
    print("--------------------------------------------------\n")

    print("\n--- Testing pipeline with empty name ---")
    empty_name_data = process_institution_pipeline("")
    print("Data for empty name:")
    print(json.dumps(empty_name_data, indent=2))
    print("--------------------------------------------------\n")