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
            "personal_info": {
                "name": "", "email": "", "phone": "", "location": "",
                "position": "", "summary": "", "linkedin": "", "github": "",
                "portfolio": "", "twitter": "", "leetcode": "", "codechef": "",
                "hackerrank": ""
            },
            "education": [],
            "experience": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "research_and_publications": [],
            "layout_settings": {
                "page_break_before_projects": False,
                "page_break_before_certifications": False,
                "page_break_before_experience": False,
                "page_break_before_education": False,
                "page_break_before_skills": False,
                "page_break_before_research": False,
                "margin_after_summary": 0,
                "margin_after_experience": 0,
                "margin_after_education": 0,
                "margin_after_skills": 0,
                "margin_after_projects": 0,
                "margin_after_certifications": 0,
                "margin_after_research": 0,
            }
        }

    # Ensure layout_settings exists in existing data (for old CVs)
    if "layout_settings" not in existing_data:
        existing_data["layout_settings"] = {
            "page_break_before_projects": False,
            "page_break_before_certifications": False,
            "page_break_before_experience": False,
            "page_break_before_education": False,
            "page_break_before_skills": False,
            "page_break_before_research": False,
            "margin_after_summary": 0,
            "margin_after_experience": 0,
            "margin_after_education": 0,
            "margin_after_skills": 0,
            "margin_after_projects": 0,
            "margin_after_certifications": 0,
            "margin_after_research": 0,
        }

    # Check if CV has existing data
    has_existing_data = (
        existing_data.get('personal_info', {}).get('name') or
        len(existing_data.get('experience', [])) > 0 or
        len(existing_data.get('education', [])) > 0 or
        len(existing_data.get('skills', [])) > 0 or
        len(existing_data.get('projects', [])) > 0 or
        len(existing_data.get('certifications', [])) > 0 or
        len(existing_data.get('research_and_publications', [])) > 0
    )

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    layout_instructions = """
LAYOUT COMMANDS — When the user asks to adjust spacing or page breaks, update layout_settings:

PAGE BREAKS (set to true to force section onto a new page):
  "start projects on page 2" / "projects on new page"       → page_break_before_projects: true
  "start certifications on new page"                         → page_break_before_certifications: true
  "start experience on new page"                             → page_break_before_experience: true
  "start education on new page"                              → page_break_before_education: true
  "start skills on new page"                                 → page_break_before_skills: true
  "start research on new page"                               → page_break_before_research: true
  To remove a page break, set the value back to false.

BLANK SPACE / MARGINS (value in px, added after the section):
  Conversion rules:
    "1 blank line"  / "1 blank space"  → 40
    "2 blank lines" / "2 blank spaces" → 80
    "3 blank lines" / "3 blank spaces" → 120
    "small space"                      → 20
    "medium space"                     → 60
    "large space"                      → 100
    "remove space"  / "no space"       → 0

  Examples:
    "add 2 blank lines after skills"           → margin_after_skills: 80
    "add 1 blank space after experience"       → margin_after_experience: 40
    "large space after projects"               → margin_after_projects: 100
    "remove space after education"             → margin_after_education: 0
    "3 blank lines before projects section"    → margin_after_skills: 120
      (space before projects = space after the section that comes before it)

Always confirm to the user what layout change was made, e.g.:
  "Done! I've added 2 blank lines after the Skills section."
  "Got it! Projects will now start on a new page."
"""

    # ─── SYSTEM PROMPT: UPDATE MODE ───────────────────────────────────────────
    if has_existing_data:
        system_prompt = f"""
You are a professional resume builder helping the user UPDATE their existing CV.

The user already has some information in their CV. Your job is to:
1. Help them update or modify existing sections
2. Add new information they provide
3. Handle layout/spacing commands (see LAYOUT COMMANDS below)
4. NEVER delete existing data unless they explicitly ask to remove it
5. Ask clarifying questions when needed
6. Be conversational and helpful

{layout_instructions}

CRITICAL: You MUST respond with ONLY a JSON object. No other text before or after.

JSON Structure (ALWAYS include this complete structure in your response):
{{
  "cv_data": {{
    "personal_info": {{
      "name": "", "email": "", "phone": "", "location": "",
      "position": "", "summary": ""
    }},
    "education": [
      {{
        "degree": "", "institution": "", "start_date": "",
        "end_date": "", "location": "", "gpa": ""
      }}
    ],
    "experience": [
      {{
        "position": "", "company": "", "start_date": "",
        "end_date": "", "location": "", "responsibilities": []
      }}
    ],
    "skills": [{{"name": ""}}],
    "projects": [
      {{
        "name": "", "description": "", "technologies": "",
        "date": "", "link": ""
      }}
    ],
    "certifications": [
      {{
        "name": "", "issuer": "", "date": "",
        "expiry_date": "", "credential_id": ""
      }}
    ],
    "research_and_publications": [
      {{
        "title": "", "publication": "", "date": "", "link": ""
      }}
    ],
    "layout_settings": {{
      "page_break_before_projects": false,
      "page_break_before_certifications": false,
      "page_break_before_experience": false,
      "page_break_before_education": false,
      "page_break_before_skills": false,
      "page_break_before_research": false,
      "margin_after_summary": 0,
      "margin_after_experience": 0,
      "margin_after_education": 0,
      "margin_after_skills": 0,
      "margin_after_projects": 0,
      "margin_after_certifications": 0,
      "margin_after_research": 0
    }}
  }},
  "next_question": "Your next question here",
  "ai_message": "A friendly response acknowledging what they said",
  "progress_percentage": 0,
  "current_section": "personal_info",
  "all_complete": false
}}

IMPORTANT Rules for UPDATING:
- MERGE new information with existing data — DO NOT replace entire sections
- If user wants to add a new job, ADD it to the experience array
- If user wants to add skills, APPEND them to existing skills
- Only UPDATE specific fields the user mentions
- Keep all other existing data intact
- For layout commands, only update the specific layout_settings fields mentioned
- Ask "Is there anything else you'd like to update?" when they seem done
"""

    # ─── SYSTEM PROMPT: NEW CV MODE ───────────────────────────────────────────
    else:
        system_prompt = f"""
You are a professional resume builder having a friendly conversation with the user.

Your job is to:
1. Ask ONE question at a time to gather CV information
2. Extract and store the information in the JSON structure
3. Handle layout/spacing commands at any time (see LAYOUT COMMANDS below)
4. Guide the user through: Personal Info → Education → Experience → Skills → Projects → Certifications → Research and Publications
5. Be conversational, friendly, and encouraging

{layout_instructions}

CRITICAL: You MUST respond with ONLY a JSON object. No other text before or after.

JSON Structure (ALWAYS include this complete structure in your response):
{{
  "cv_data": {{
    "personal_info": {{
      "name": "", "email": "", "phone": "", "location": "",
      "position": "", "summary": ""
    }},
    "education": [
      {{
        "degree": "", "institution": "", "start_date": "",
        "end_date": "", "location": "", "gpa": ""
      }}
    ],
    "experience": [
      {{
        "position": "", "company": "", "start_date": "",
        "end_date": "", "location": "", "responsibilities": []
      }}
    ],
    "skills": [{{"name": ""}}],
    "projects": [
      {{
        "name": "", "description": "", "technologies": "",
        "date": "", "link": ""
      }}
    ],
    "certifications": [
      {{
        "name": "", "issuer": "", "date": "",
        "expiry_date": "", "credential_id": ""
      }}
    ],
    "research_and_publications": [
      {{
        "title": "", "publication": "", "date": "", "link": ""
      }}
    ],
    "layout_settings": {{
      "page_break_before_projects": false,
      "page_break_before_certifications": false,
      "page_break_before_experience": false,
      "page_break_before_education": false,
      "page_break_before_skills": false,
      "page_break_before_research": false,
      "margin_after_summary": 0,
      "margin_after_experience": 0,
      "margin_after_education": 0,
      "margin_after_skills": 0,
      "margin_after_projects": 0,
      "margin_after_certifications": 0,
      "margin_after_research": 0
    }}
  }},
  "next_question": "Your next question here",
  "ai_message": "A friendly response to the user",
  "progress_percentage": 0,
  "current_section": "personal_info",
  "all_complete": false
}}

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
5. projects (name, description, technologies, link)
6. certifications (name, issuer, date, expiry_date, credential_id)
7. research_and_publications (title, publication, date, link)
"""

    # ─── USER CONTENT ─────────────────────────────────────────────────────────
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
- If adding to arrays (experience, education, skills, projects, certifications, research_and_publications), APPEND new items
- If this is a layout command, ONLY update the relevant layout_settings fields

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

        try:
            ai_response = json.loads(cleaned_output)

            # Ensure layout_settings always exists in response
            if "cv_data" in ai_response and "layout_settings" not in ai_response["cv_data"]:
                ai_response["cv_data"]["layout_settings"] = existing_data.get("layout_settings", {
                    "page_break_before_projects": False,
                    "page_break_before_certifications": False,
                    "page_break_before_experience": False,
                    "page_break_before_education": False,
                    "page_break_before_skills": False,
                    "page_break_before_research": False,
                    "margin_after_summary": 0,
                    "margin_after_experience": 0,
                    "margin_after_education": 0,
                    "margin_after_skills": 0,
                    "margin_after_projects": 0,
                    "margin_after_certifications": 0,
                    "margin_after_research": 0,
                })

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