import json
import json
import time
from openai import OpenAI

# Defines the core structured information we aim to extract
# This can be modified to include more or fewer fields as needed
# The LLM will be prompted to fill these fields, using "Unknown" if information is not found
# Enhanced structured information keys for comprehensive institutional profiling
STRUCTURED_INFO_KEYS = [
    # Basic Information
    "name", "official_name", "type", "founded", "website", "description",
    
    # Location Details
    "location_city", "location_country", "address", "state", "postal_code",
    
    # Contact Information
    "phone", "email", "social_media", "fax", "mailing_address",
    
    # Organization Details
    "size", "number_of_employees", "entity_type", "fields_of_focus", "industry_sector",
    "annual_revenue", "market_cap", "stock_symbol", "legal_status",
    
    # Leadership & Personnel
    "key_people", "leadership", "ceo", "president", "chairman", "founders",
    "board_of_directors", "executive_team", "department_heads",
    # Academic/Healthcare Specific
    "student_population", "faculty_count", "programs_offered", "degrees_awarded",
    "research_areas", "departments", "colleges", "schools", "patient_capacity",
    "medical_specialties", "bed_count", "accreditation_bodies",
    
    # Enhanced University Specific Fields
    "course_catalog", "professors", "academic_staff", "administrative_staff",
    "undergraduate_programs", "graduate_programs", "doctoral_programs",
    "professional_programs", "online_programs", "continuing_education",
    "admission_requirements", "tuition_costs", "scholarship_programs",
    "academic_calendar", "semester_system", "graduation_rate",
    "student_faculty_ratio", "campus_housing", "dormitories",
    "libraries", "laboratory_facilities", "sports_facilities",
    "student_organizations", "fraternities_sororities", "athletics_programs",
    "research_centers", "institutes", "academic_rankings",
    "notable_faculty", "distinguished_alumni", "university_press",
    
    # Business/Financial Specific
    "services_offered", "products", "subsidiaries", "divisions", "branches",
    "employees_worldwide", "headquarters_location", "operating_countries",
    
    # Achievements and Recognition
    "notable_achievements", "rankings", "awards", "certifications", "accreditations",
    "notable_alumni", "research_achievements", "patents", "publications",
    
    # Relationships and Affiliations
    "affiliations", "partnerships", "parent_organization", "member_organizations",
    "joint_ventures", "collaborations", "network_memberships",
    
    # Financial Information
    "financial_data", "endowment", "budget", "funding_sources", "grants_received",
    "tuition_fees", "operating_expenses", "profit_margins",
    
    # Infrastructure & Facilities
    "campus_size", "facilities", "locations", "buildings", "infrastructure",
    "technology_resources", "library_collections", "research_facilities",
    
    # Visual Assets
    "logo_url", "main_image_url", "campus_images", "facility_images",
    
    # Recent Activity & News
    "recent_news", "latest_updates", "press_releases", "announcements",
    "upcoming_events", "recent_developments"
]

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
        }    # Enhanced research analyst prompt for comprehensive institutional profiling
    keys_string = ", ".join(f'"{key}"' for key in STRUCTURED_INFO_KEYS)
    structured_data_prompt = f"""You are a research analyst AI that generates structured, factual institutional profiles using diverse, reputable sources.

Given the following institution name: "{institution_name}", and the raw web content or extracted data below, your task is to generate a comprehensive profile.

### Instructions:
- Prioritize information from official websites, Wikipedia, Wikidata, and reliable news or academic sources.
- Extract specific, detailed information rather than generic descriptions.
- For leadership roles, include full names with titles and positions.
- If data is missing or ambiguous, infer carefully from context or mark as "Unknown".
- Keep the tone professional, objective, and factual.
- Extract concrete numbers, dates, and specific details whenever possible.

### Special Instructions for Key Fields:

**Leadership & Personnel:**
- **key_people**: Extract current leadership with full names and titles (e.g., "Dr. Sarah Johnson, President & CEO")
- **ceo**, **president**, **chairman**: Extract individual names for these specific roles
- **founders**: Include founding team members if known
- **executive_team**: List C-level executives and senior leadership
- **board_of_directors**: Include board members if publicly available

**Organization Details:**
- **type**: Be very specific (e.g., "Public Research University", "Private Investment Bank", "Teaching Hospital")
- **description**: Provide a comprehensive, detailed description of the institution. This should be 1-2 paragraphs covering the institution's mission, history, key characteristics, primary activities, and significance. Include context about what makes the institution unique or notable. Be thorough and informative rather than brief.
- **founded**: Extract exact founding year or date
- **size**: Provide specific numbers (students for universities, employees for companies, beds for hospitals)
- **annual_revenue**: Include financial figures if publicly available
- **stock_symbol**: For public companies, include trading symbol

**Academic/Healthcare Specific:**
- **student_population**: Exact enrollment numbers
- **faculty_count**: Number of faculty/staff
- **programs_offered**: List specific degree programs or medical specialties
- **research_areas**: Key research focus areas
- **patient_capacity**: For hospitals, bed count and capacity

**Enhanced University Specific:**
- **course_catalog**: Available courses and curricula
- **professors**: Notable professors and their specializations
- **academic_staff**: Number of academic personnel by category
- **undergraduate_programs**: Specific undergraduate degree programs
- **graduate_programs**: Master's and graduate programs offered
- **doctoral_programs**: PhD and doctoral programs
- **professional_programs**: Professional certification programs
- **admission_requirements**: Entry requirements and criteria
- **tuition_costs**: Tuition fees and associated costs
- **graduation_rate**: Percentage of students who graduate
- **student_faculty_ratio**: Ratio of students to faculty
- **campus_housing**: Dormitory and housing information
- **libraries**: Library facilities and collections
- **laboratory_facilities**: Research and teaching labs
- **sports_facilities**: Athletic and recreational facilities
- **student_organizations**: Clubs and student groups
- **athletics_programs**: Sports teams and competitions
- **research_centers**: Specialized research institutes
- **academic_rankings**: University rankings and recognition
- **notable_faculty**: Distinguished faculty members
- **distinguished_alumni**: Famous graduates

**Business Specific:**
- **services_offered**: Detailed list of main services or products
- **subsidiaries**: List major subsidiary companies
- **headquarters_location**: Specific address of main headquarters
- **operating_countries**: Geographic presence

**Achievements:**
- **notable_achievements**: List 3-5 significant accomplishments with dates
- **rankings**: Include specific rankings and sources
- **awards**: Recent awards and recognitions
- **notable_alumni**: Famous graduates or former employees

**Financial & Infrastructure:**
- **financial_data**: Revenue, budget, endowment figures
- **campus_size**: Physical size in acres/hectares
- **facilities**: Major buildings, campuses, or facilities

**Visual Assets:**
- **logo_url**: Extract the main institutional logo URL from MEDIA CONTENT SUMMARY
- **main_image_url**: Primary building/campus image URL
- **campus_images**: Additional facility or campus images

### Output Format:
Return the information strictly as a JSON object with these keys: {keys_string}

For array fields, provide actual items as arrays [] or use empty array if not found.
For object fields, provide structured data or empty object {{}} if not found.
Use "Unknown" only for simple string fields when information is genuinely not available.

### Data Input:
---
{raw_text}
---

JSON Output:"""
    
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