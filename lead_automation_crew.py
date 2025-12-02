import json
import time
import random
from typing import Dict, Any, Optional

# --- Configuration for Gemini API ---
# NOTE: The API key is left blank. In the Canvas environment, it is provided automatically
# for the gemini-2.5-flash-preview-09-2025 model.
API_KEY = ""
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# --- AGENT 1: Scraping Agent (Simulation) ---
def scraping_agent(company_name: str) -> Dict[str, Any]:
    """
    Simulates finding key data points for a company.
    In a real system, this would involve calling Google Search or specific
    data APIs (e.g., Crunchbase, Hunter.io) to enrich the lead data.
    """
    print(f"🔍 AGENT 1 (Scraping): Searching for key data on '{company_name}'...")

    # Mock Data based on the company name to simulate real-world outcomes
    if "Innovatech" in company_name:
        lead_data = {
            "name": company_name,
            "sector": "FinTech / AI Solutions",
            "recent_news": "Just closed a $50M Series B funding round; launched a new LLM-powered compliance tool.",
            "hiring_focus": "Actively hiring for 15 Senior AI/ML Engineer roles and 5 Product Managers.",
            "automation_potential": "High - Recent funding suggests budget for large-scale tool adoption."
        }
    else:
        lead_data = {
            "name": company_name,
            "sector": "Legacy Manufacturing",
            "recent_news": "Announced slight revenue decline last quarter; CEO mentioned 'cost consolidation'.",
            "hiring_focus": "Hiring 2 Junior Accountants and 1 HR Generalist; no immediate tech hiring.",
            "automation_potential": "Low - Focus is currently on cost cutting, not major investment."
        }

    print("✅ AGENT 1 (Scraping): Data collected and enriched.")
    return lead_data

# --- Helper Function for API Calls (with backoff) ---
def _fetch_with_backoff(payload: Dict[str, Any], max_retries: int = 5) -> Optional[Dict[str, Any]]:
    """Handles API calls with exponential backoff and retries."""
    import requests
    # Set up the request headers
    headers = {'Content-Type': 'application/json'}

    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            if response.ok:
                return response.json()

            # Handle common retryable errors
            if response.status_code in [429, 500, 503]:
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"⚠️ API error ({response.status_code}). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    continue
                else:
                    print(f"❌ API call failed after {max_retries} attempts: {response.status_code} - {response.text}")
                    return None
            else:
                print(f"❌ Non-retryable API error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Network or Request exception occurred: {e}")
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ Network error. Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            else:
                return None
        except ImportError:
            print("\n🚨 ERROR: 'requests' library not installed. Please run 'pip install requests'.")
            return None
    return None

# --- AGENT 2: Qualification Agent (LLM Reasoning) ---
def qualification_agent(lead_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Uses the Gemini API and structured output to qualify the lead automatically.
    This demonstrates the core AI automation expertise: making an LLM reliable.
    """
    if not lead_data:
        print("🛑 AGENT 2 (Qualification): No lead data available to process.")
        return None

    print(f"🧠 AGENT 2 (Qualification): Analyzing data for '{lead_data['name']}' using Gemini...")

    # Define the System Instruction (The Agent's Persona and Rules)
    system_prompt = (
        "You are a Senior B2B Lead Qualification Specialist. "
        "Your goal is to analyze the provided company information and determine if they are a 'High-Value Lead' (HV), "
        "a 'Medium-Value Lead' (MV), or a 'Low-Value Lead' (LV). "
        "Base your decision ONLY on whether the company is growing, actively hiring for AI/Tech roles, "
        "and shows clear signs of investment or digital transformation (funding, new product launches). "
        "Provide only a single JSON object."
    )

    # Define the Content to Analyze
    lead_summary = "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in lead_data.items()])
    user_query = f"Qualify the following lead based on the criteria: \n\n{lead_summary}"

    # Define the Structured Output Schema (The Crucial Automation Constraint)
    schema = {
        "type": "OBJECT",
        "properties": {
            "qualification_level": { "type": "STRING", "description": "HV, MV, or LV" },
            "justification": { "type": "STRING", "description": "A concise reason for the qualification based on growth/hiring/funding evidence." }
        },
        "propertyOrdering": ["qualification_level", "justification"]
    }

    # Construct the API Payload
    payload = {
        "contents": [{ "parts": [{ "text": user_query }] }],
        "systemInstruction": { "parts": [{ "text": system_prompt }] },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }

    # Call the API
    api_result = _fetch_with_backoff(payload)

    if api_result:
        try:
            # Extract the JSON text and parse it
            json_text = api_result['candidates'][0]['content']['parts'][0]['text']
            qualification = json.loads(json_text)
            print(f"✅ AGENT 2 (Qualification): Successfully returned structured data.")
            return qualification

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"❌ AGENT 2 (Qualification): Failed to parse structured JSON response. Error: {e}")
            return None
    else:
        print("❌ AGENT 2 (Qualification): Failed to get a response from the AI model.")
        return None

# --- ORCHESTRATOR FUNCTION ---
def run_automation_workflow(company_name: str):
    """Orchestrates the sequence of agents."""
    print(f"\n--- 🚀 Starting Autonomous Workflow for: {company_name} ---")

    # 1. Execute AGENT 1: Get data
    initial_data = scraping_agent(company_name)
    print("-" * 50)

    # 2. Execute AGENT 2: Process data with LLM
    qualification_result = qualification_agent(initial_data)
    print("-" * 50)

    # 3. Final Report & Action (simulated)
    final_report = initial_data
    if qualification_result:
        final_report['AI_Qualification'] = qualification_result
        level = qualification_result.get('qualification_level', 'N/A')
        print(f"🎯 WORKFLOW COMPLETE: Lead '{company_name}' rated as {level} Value.")
        # In a real system, a 'Routing Agent' would take this 'level' and automatically trigger the next step (e.g., send to Sales Team 1).
        print("➡️ ACTION: Lead successfully scored and ready for automated routing/outreach.")
    else:
        print("❌ WORKFLOW FAILED: Qualification step did not return a result. Manual review needed.")

    print("\n📊 FINAL PROCESSED LEAD DATA:")
    print(json.dumps(final_report, indent=4))
    print("----------------------------------------------------\n")

# --- EXECUTION ---
if __name__ == "__main__":
    # Ensure you run 'pip install requests' locally to execute this script.

    # Demonstrate a High-Value Lead (HV)
    run_automation_workflow("Innovatech Solutions")

    # Demonstrate a Low-Value Lead (LV)
    run_automation_workflow("Midwest Metalworks Inc")