import json
from llm_service import chat_completion

def generate_control_ai(title):
    """
    Convert GAP policy into structured control using LLM
    """

    prompt = f"""
You are a cloud security expert.

Convert the following policy into structured JSON.

Policy:
"{title}"

Return ONLY JSON in this format:
{{
  "control_id": "short_unique_id",
  "title": "normalized control title",
  "cloud_provider": "aws/azure/gcp/unknown",
  "service": "service name",
  "api_calls": ["list of API calls"],
  "permissions": ["required permissions"],
  "remediation": ["step-by-step remediation"]
}}

Rules:
- Be concise
- Use real cloud API names when possible
- If unsure, make best guess
- Do NOT add explanation text
"""

    content = chat_completion(prompt, temperature=0.2)

    try:
        return json.loads(content)
    except:
        return {
            "control_id": "parse_error",
            "title": title,
            "api_calls": [],
            "permissions": [],
            "remediation": ["Manual review required"]
        }