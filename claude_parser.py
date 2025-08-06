import os
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from custom_llm import custom_claude
from dotenv import load_dotenv

load_dotenv()

def extract_resume_info_with_claude(text):
    prompt = f"""{HUMAN_PROMPT}
You are an AI assistant that extracts structured candidate data from resume text.

Extract the following fields from the resume below:
- Full Name
- Email
- Phone
- Total Experience (in years)
- Key Skills (as a list)
- Previous Job Titles
- Last Company
- Education Degrees

Return only a **raw JSON object** (no markdown, no explanation), like:
{{
  "name": "...",
  "email": "...",
  "phone": "...",
  "experience_years": ...,
  "skills": ["...", "..."],
  "last_company": "...",
  "previous_roles": ["...", "..."],
  "education": ["..."]
}}

Resume Text:
\"\"\"
{text}
\"\"\"{AI_PROMPT}"""

    response = custom_claude.invoke(prompt)

    import json

    # Clean Markdown-style JSON code blocks if they exist
    if response.strip().startswith("```"):
        response = response.strip().strip("```").replace("json", "", 1).strip()

    try:
        return json.loads(response)
    except Exception as e:
        return {
            "error": f"Failed to parse Claude response: {str(e)}",
            "raw": response
        }