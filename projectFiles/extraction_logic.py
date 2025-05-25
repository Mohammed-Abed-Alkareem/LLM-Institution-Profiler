import json

# Defines the core structured information we aim to extract
# This can be modified to include more or fewer fields as needed
# The LLM will be prompted to fill these fields, using "Unknown" if information is not found
STRUCTURED_INFO_KEYS = ["name", "address", "country", "number_of_employees", "entity_type"]

# Change this as we wish
MODEL = "gemini-2.0-flash"
# The gemini library is used rn but OpenAI's works with everything as long as you
# change the link, we can also use curl with OpenAI's API and it has the same effect
# refactor should be easy though


def extract_structured_data(genai_client, raw_text: str, institution_name: str):
    """
    Extracts structured information from raw text using an LLM call.
    This call does NOT use grounding tools (so purely our input).

    Args:
        genai_client: The initialized Google Generative AI client.
        raw_text: The raw text content about the institution.
        institution_name: The name of the institution, used for context and as a fallback.

    Returns:
        A dictionary containing the extracted structured information or an error message.
        Example success structure:
        {
            "name": "Example University",
            "address": "123 University Dr, City, State, Zip",
            "country": "CountryName",
            "number_of_employees": "1000-5000",
            "entity_type": "Non-profit"
        }
    """
    if not genai_client:
        return {
            **{key: "Unknown (AI client not available)" for key in STRUCTURED_INFO_KEYS},
            "name": institution_name, "error": "Generative AI client not available for extraction."
        }

    if not raw_text:
        return {
            **{key: "Unknown (No raw text provided)" for key in STRUCTURED_INFO_KEYS},
            "name": institution_name, "error": "No raw text provided for extraction."
        }

    # Instructs the LLM to find specific pieces of information and return them in a JSON format
    # We can use other formats later since JSON isn't the best from what I've seen
    # If a piece of information is not found, it should say "Unknown"
    # Has to be edited while we figure things out
    keys_string = ", ".join(f'"{key}"' for key in STRUCTURED_INFO_KEYS)
    structured_data_prompt = f"""
    From the following text about '{institution_name}', extract the specified information.
    If a piece of information is not found in the text, use the string "Unknown".
    Return the information strictly as a JSON object with the following keys: {keys_string}.

    Text:
    ---
    {raw_text}
    ---

    JSON Output:
    """
    try:
        response = genai_client.models.generate_content(
            model=MODEL,
            contents=structured_data_prompt
        )

        extracted_text = ""
        if response:
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                error_message = f"Extraction blocked. Reason: {response.prompt_feedback.block_reason}"
                return {
                    **{key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                    "name": institution_name, "error": error_message
                }
            elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                text_parts = [part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')]
                extracted_text = "".join(text_parts).strip()
            elif hasattr(response, 'text') and response.text: # Fallback
                extracted_text = response.text.strip()
            
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
                    return final_data
                except json.JSONDecodeError as je:
                    error_message = "Failed to parse JSON response from LLM for structured data."
                    print(f"JSONDecodeError for {institution_name}: {je}. Raw response: {extracted_text}")
                    return {
                        **{key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                        "name": institution_name, "error": error_message, "raw_llm_output": extracted_text
                    }
            else:
                error_message = "No text returned from LLM for structured data extraction."
                return {
                    **{key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                    "name": institution_name, "error": error_message
                }
        else:
            error_message = "No response from LLM for structured data extraction."
            return {
                **{key: "Unknown" for key in STRUCTURED_INFO_KEYS},
                "name": institution_name, "error": error_message
            }
    except Exception as e:
        print(f"Error during structured data extraction for {institution_name}: {e}")
        return {
            **{key: "Unknown" for key in STRUCTURED_INFO_KEYS},
            "name": institution_name, "error": f"Exception during structured data extraction: {str(e)}"
        }