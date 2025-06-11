import json
import json
import time
from openai import OpenAI

# Defines the core structured information we aim to extract
# This can be modified to include more or fewer fields as needed
# The LLM will be prompted to fill these fields, using "Unknown" if information is not found
STRUCTURED_INFO_KEYS = ["name", "address", "country", "number_of_employees", "entity_type", "logo_url", "main_image_url"]

# Change this as we wish
MODEL = "gemini-2.0-flash"

# OpenAI-compatible client for Gemini
def create_openai_gemini_client(api_key: str) -> OpenAI:
    """Create OpenAI client configured for Gemini API."""
    return OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )


def extract_structured_data(openai_client, raw_text: str, institution_name: str):
    """
    Extracts structured information from raw text using an LLM call via OpenAI client.
    This call does NOT use grounding tools (so purely our input).

    Args:
        openai_client: The initialized OpenAI client configured for Gemini.
        raw_text: The raw text content about the institution.
        institution_name: The name of the institution, used for context and as a fallback.

    Returns:
        A dictionary containing the extracted structured information, metrics, and any errors.
        Example success structure:
        {
            "name": "Example University",
            "address": "123 University Dr, City, State, Zip",
            "country": "CountryName", 
            "number_of_employees": "1000-5000",
            "entity_type": "Non-profit",
            "extraction_metrics": {
                "input_tokens": 1500,
                "output_tokens": 200,
                "total_tokens": 1700,
                "model_used": "gemini-2.0-flash",
                "extraction_time": 2.3,
                "success": True
            }
        }
    """
    if not openai_client:
        return {
            **{key: "Unknown (AI client not available)" for key in STRUCTURED_INFO_KEYS},
            "name": institution_name, 
            "error": "OpenAI client not available for extraction.",
            "extraction_metrics": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "model_used": MODEL,
                "extraction_time": 0,
                "success": False
            }
        }

    if not raw_text:
        return {
            **{key: "Unknown (No raw text provided)" for key in STRUCTURED_INFO_KEYS},
            "name": institution_name, 
            "error": "No raw text provided for extraction.",
            "extraction_metrics": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "model_used": MODEL,
                "extraction_time": 0,
                "success": False
            }
        }    # Instructs the LLM to find specific pieces of information and return them in a JSON format
    keys_string = ", ".join(f'"{key}"' for key in STRUCTURED_INFO_KEYS)
    structured_data_prompt = f"""
    From the following text about '{institution_name}', extract the specified information.
    If a piece of information is not found in the text, use the string "Unknown".
    
    Special instructions for images:
    - For "logo_url": Extract the main logo image URL if mentioned in the content
    - For "main_image_url": Extract the primary/main image URL representing the institution
    - Look for image URLs mentioned in the "MEDIA CONTENT SUMMARY" section and "Images found" sections
    - Convert relative URLs to absolute URLs where possible (e.g., //example.com/image.jpg becomes https://example.com/image.jpg)
    
    Return the information strictly as a JSON object with the following keys: {keys_string}.

    Text:
    ---
    {raw_text}
    ---

    JSON Output:
    """
    
    extraction_start_time = time.time()
    
    try:
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured information from text and returns it as JSON."},
                {"role": "user", "content": structured_data_prompt}
            ]
        )
        
        extraction_time = time.time() - extraction_start_time
        
        # Extract token usage metrics from response
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        total_tokens = response.usage.total_tokens if response.usage else 0
        
        extraction_metrics = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "model_used": MODEL,
            "extraction_time": extraction_time,
            "success": True
        }

        if response.choices and response.choices[0].message:
            extracted_text = response.choices[0].message.content.strip()
            
            if extracted_text:
                # Some cleaning
                if extracted_text.startswith("```json"):
                    extracted_text = extracted_text[7:]
                if extracted_text.startswith("```"): # Handle cases where just ``` is used
                    extracted_text = extracted_text[3:]
                if extracted_text.endswith("```"):
                    extracted_text = extracted_text[:-3]
                extracted_text = extracted_text.strip()
                
                try:
                    parsed_json = json.loads(extracted_text)
                    # Ensure all predefined keys are present, defaulting to "Unknown"
                    final_data = {key: parsed_json.get(key, "Unknown") for key in STRUCTURED_INFO_KEYS}
                    
                    # If the LLM fails to extract the name, or returns "Unknown" for it,
                    # use the original for now
                    if not final_data.get("name") or final_data.get("name") == "Unknown":
                         final_data["name"] = institution_name
                    
                    # Add extraction metrics to the result
                    final_data["extraction_metrics"] = extraction_metrics
                    return final_data
                    
                except json.JSONDecodeError as je:
                    error_message = "Failed to parse JSON response from LLM for structured data."
                    print(f"JSONDecodeError for {institution_name}: {je}. Raw response: {extracted_text}")
                    extraction_metrics["success"] = False
                    return {
                        **{key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                        "name": institution_name, 
                        "error": error_message, 
                        "raw_llm_output": extracted_text,
                        "extraction_metrics": extraction_metrics
                    }
            else:
                error_message = "No text returned from LLM for structured data extraction."
                extraction_metrics["success"] = False
                return {
                    **{key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                    "name": institution_name, 
                    "error": error_message,
                    "extraction_metrics": extraction_metrics
                }
        else:
            error_message = "No response from LLM for structured data extraction."
            extraction_metrics["success"] = False
            return {
                **{key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                "name": institution_name, 
                "error": error_message,
                "extraction_metrics": extraction_metrics
            }
            
    except Exception as e:
        extraction_time = time.time() - extraction_start_time
        print(f"Error during structured data extraction for {institution_name}: {e}")
        extraction_metrics = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "model_used": MODEL,
            "extraction_time": extraction_time,
            "success": False
        }
        return {
            **{key: "Unknown" for key in STRUCTURED_INFO_KEYS},
            "name": institution_name, 
            "error": f"Exception during structured data extraction: {str(e)}",
            "extraction_metrics": extraction_metrics
        }