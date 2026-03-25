from openai import AzureOpenAI
from openai import OpenAI
import os
import json

def _get_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def _get_client_and_model():
    azure_endpoint = _get_env("AZURE_OPENAI_ENDPOINT")
    azure_key = _get_env("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_KEY")
    azure_deployment = _get_env(
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_OPENAI_MODEL",
    )
    azure_api_version = _get_env("AZURE_OPENAI_API_VERSION") or "2024-02-15-preview"

    if azure_endpoint and azure_key and azure_deployment:
        return (
            AzureOpenAI(
                api_key=azure_key,
                api_version=azure_api_version,
                azure_endpoint=azure_endpoint,
            ),
            azure_deployment,
        )

    openai_key = _get_env("OPENAI_API_KEY")
    if openai_key:
        return OpenAI(api_key=openai_key), _get_env("OPENAI_MODEL") or "gpt-4o-mini"

    raise RuntimeError(
        "LLM is not configured. Set AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY + AZURE_OPENAI_DEPLOYMENT "
        "(recommended for Azure Web App), or set OPENAI_API_KEY."
    )


def chat_completion(prompt: str, temperature: float = 0.2) -> str:
    client, model = _get_client_and_model()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content


def generate_control(title):

    prompt = f"""
Convert cloud security policy into structured JSON.

Policy: {title}

Return ONLY JSON:
{{
  "control_id": "",
  "title": "",
  "cloud_provider": "",
  "service": "",
  "api_calls": [],
  "permissions": [],
  "remediation": []
}}
"""

    content = chat_completion(prompt, temperature=0.2)
    return json.loads(content)