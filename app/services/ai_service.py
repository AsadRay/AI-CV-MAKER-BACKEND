import requests
import os
import re
import json

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def clean_ai_response(text):
    """Remove markdown code blocks if model adds them"""
    text = re.sub(r"```json|```", "", text)
    return text.strip()


def generate_structured_cv(user_message, existing_data=None):
    """
    Generate or update CV data through conversational AI.
    AI asks questions and fills data progressively.
    """
    
    # Initialize empty structure if no existing data
    if existing_data is None:
        existing_data = {
            "personal_info": {"name": "", "email": "", "phone": "", "location": "", "position": "", "summary": "", "linkedin": "", "github": "", "portfolio": "", "twitter": "", "leetcode": "", "codechef": "", "hackerrank": "", "hackerrank": ""},
            "education": [],
            "experience": [],
            "skills": [],
            "projects": [],
            "certifications": []
        }

    # Check if CV has existing data
    has_existing_data = (
        existing_data.get('personal_info', {}).get('name') or
        len(existing_data.get('experience', [])) > 0 or
        len(existing_data.get('education', [])) > 0 or
        len(existing_data.get('skills', [])) > 0
    )

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Different system prompts based on whether CV has data
    if has_existing_data:
        system_prompt = """
You are a professional resume builder helping the user UPDATE their existing CV.

The user already has some information in their CV. Your job is to:
1. Help them update or modify existing sections
2. Add new information they provide
3. NEVER delete existing data unless they explicitly ask to remove it
4. Ask clarifying questions when needed
5. Be conversational and helpful

CRITICAL: You MUST respond with ONLY a JSON object. No other text before or after.

JSON Structure (ALWAYS include this complete structure in your response):
{
  "cv_data": {
    "personal_info": {
      "name": "",
      "email": "",
      "phone": "",
      "location": "",
      "position": "",
      "summary": ""
    },
    "education": [
      {
        "degree": "",
        "institution": "",
        "start_date": "",
        "end_date": "",
        "location": "",
        "gpa": ""
      }
    ],
    "experience": [
      {
        "position": "",
        "company": "",
        "start_date": "",
        "end_date": "",
        "location": "",
        "responsibilities": []
      }
    ],
    "skills": [{"name": ""}],
    "projects": [
      {
        "name": "",
        "description": "",
        "technologies": "",
        "date": ""
      }
    ],
    "certifications": [
      {
        "name": "",
        "issuer": "",
        "date": "",
        "expiry_date": "",
        "credential_id": ""
      }
    ]
  },
  "next_question": "Your next question here",
  "ai_message": "A friendly response acknowledging what they said",
  "progress_percentage": 0,
  "current_section": "personal_info",
  "all_complete": false
}

IMPORTANT Rules for UPDATING:
- MERGE new information with existing data - DO NOT replace entire sections
- If user wants to add a new job, ADD it to the experience array, don't replace existing jobs
- If user wants to add skills, APPEND them to existing skills
- Only UPDATE specific fields the user mentions
- Keep all other existing data intact
- Ask "Is there anything else you'd like to update?" when they seem done with a section

Examples:

User: "I want to add a new skill"
Current CV has: skills: [{"name": "Python"}]
Response:
{
  "cv_data": {
    "personal_info": {...existing data...},
    "education": [...existing data...],
    "experience": [...existing data...],
    "skills": [{"name": "Python"}],
    "projects": [...existing data...],
    "certifications": [...existing data...]
  },
  "next_question": "What skill would you like to add?",
  "ai_message": "Sure! What new skill would you like to add to your CV?",
  "progress_percentage": 60,
  "current_section": "skills",
  "all_complete": false
}

User: "JavaScript and React"
Current CV has: skills: [{"name": "Python"}]
Response:
{
  "cv_data": {
    "personal_info": {...existing data...},
    "education": [...existing data...],
    "experience": [...existing data...],
    "skills": [{"name": "Python"}, {"name": "JavaScript"}, {"name": "React"}],
    "projects": [...existing data...],
    "certifications": [...existing data...]
  },
  "next_question": "Great! Any other skills you'd like to add?",
  "ai_message": "Added JavaScript and React to your skills! These are great additions.",
  "progress_percentage": 65,
  "current_section": "skills",
  "all_complete": false
}
"""
    else:
        # Original system prompt for new CVs
        system_prompt = """
You are a professional resume builder having a friendly conversation with the user.

Your job is to:
1. Ask ONE question at a time to gather CV information
2. Extract and store the information in the JSON structure
3. Guide the user through: Personal Info → Education → Experience → Skills → Projects → Certifications
4. Be conversational, friendly, and encouraging

CRITICAL: You MUST respond with ONLY a JSON object. No other text before or after.

JSON Structure (ALWAYS include this complete structure in your response):
{
  "cv_data": {
    "personal_info": {
      "name": "",
      "email": "",
      "phone": "",
      "location": "",
      "position": "",
      "summary": ""
    },
    "education": [
      {
        "degree": "",
        "institution": "",
        "start_date": "",
        "end_date": "",
        "location": "",
        "gpa": ""
      }
    ],
    "experience": [
      {
        "position": "",
        "company": "",
        "start_date": "",
        "end_date": "",
        "location": "",
        "responsibilities": []
      }
    ],
    "skills": [{"name": ""}],
    "projects": [
      {
        "name": "",
        "description": "",
        "technologies": "",
        "date": ""
      }
    ],
    "certifications": [
      {
        "name": "",
        "issuer": "",
        "date": "",
        "expiry_date": "",
        "credential_id": ""
      }
    ]
  },
  "next_question": "Your next question here",
  "ai_message": "A friendly response to the user",
  "progress_percentage": 0,
  "current_section": "personal_info",
  "all_complete": false
}

Rules:
- Extract info from user's message and fill cv_data
- PRESERVE all existing data from previous responses
- Ask ONE follow-up question in "next_question"
- Provide a friendly acknowledgment in "ai_message"
- Update "progress_percentage" (0-100) based on completion
- Set "current_section" to the section you're working on
- Set "all_complete": true when entire CV is complete
- Be friendly and encouraging
- If user says "skip" or "next", move to the next section

Section Order:
1. personal_info (name, email, phone, location, position, summary)
2. education (degrees, institutions, dates, GPAs)
3. experience (positions, companies, dates, responsibilities)
4. skills (list of skills)
5. projects (name, description, technologies)
6. certifications (name, issuer, date, expiry_date, credential_id)

Examples:

User: "Hi" or "Hello" or "Start"
Response:
{
  "cv_data": {
    "personal_info": {"name": "", "email": "", "phone": "", "location": "", "position": "", "summary": ""},
    "education": [],
    "experience": [],
    "skills": [],
    "projects": [],
    "certifications": []
  },
  "next_question": "What's your full name?",
  "ai_message": "Hi! I'm excited to help you build your CV. Let's start with your basic information.",
  "progress_percentage": 0,
  "current_section": "personal_info",
  "all_complete": false
}

User: "My name is John Smith and I'm a software engineer"
Response:
{
  "cv_data": {
    "personal_info": {"name": "John Smith", "email": "", "phone": "", "location": "", "position": "Software Engineer", "summary": ""},
    "education": [],
    "experience": [],
    "skills": [],
    "projects": [],
    "certifications": []
  },
  "next_question": "What's your email address?",
  "ai_message": "Nice to meet you, John! I've noted that you're a Software Engineer.",
  "progress_percentage": 8,
  "current_section": "personal_info",
  "all_complete": false
}
"""

    # Build the user message based on context
    if has_existing_data:
        user_content = f"""
Current CV Data (DO NOT DELETE THIS DATA - only update/add to it):
{json.dumps(existing_data, indent=2)}

User's message: "{user_message}"

IMPORTANT: 
- MERGE the user's new information with the existing data above
- DO NOT replace entire sections
- ONLY update the specific fields the user mentions
- Keep all other existing data exactly as it is
- If adding to arrays (experience, education, skills, projects, certifications), APPEND new items

Update the CV data and respond with your JSON.
"""
    else:
        user_content = f"""
Current CV Data:
{json.dumps(existing_data, indent=2)}

User's message: "{user_message}"

Update the CV data with any new information from the user's message, then ask the next appropriate question.
Remember to output ONLY JSON, nothing else. No explanations, no markdown.
"""

    payload = {
        "model": "openrouter/auto",
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print("OpenRouter Error:", response.text)
            return None

        result = response.json()
        raw_output = result["choices"][0]["message"]["content"]
        cleaned_output = clean_ai_response(raw_output)

        # Parse JSON
        try:
            ai_response = json.loads(cleaned_output)
            
            # Ensure all required fields exist
            if "ai_message" not in ai_response:
                ai_response["ai_message"] = ai_response.get("next_question", "")
            
            return ai_response
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {str(e)}")
            print(f"Raw output: {cleaned_output[:500]}")
            return None

    except Exception as e:
        print("AI Service Error:", str(e))
        return None