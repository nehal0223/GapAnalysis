import json
import re
from llm_service import chat_completion
from cloud_docs_fetcher import fetch_control_metadata


def _strip_code_fences(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
    return text


def _sanitize_control(control: dict, title: str) -> dict:
    if not isinstance(control, dict):
        control = {}

    def _as_list(value):
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value if v is not None and str(v).strip()]
        if isinstance(value, str):
            v = value.strip()
            return [v] if v else []
        return [str(value)]

    sanitized = {
        "control_id": str(control.get("control_id") or "").strip() or "generated",
        "title": str(control.get("title") or "").strip() or title,
        "cloud_provider": str(control.get("cloud_provider") or "").strip() or "unknown",
        "service": str(control.get("service") or "").strip() or "unknown",
        "api_calls": _as_list(control.get("api_calls")),
        "permissions": _as_list(control.get("permissions")),
        "remediation": _as_list(control.get("remediation")),
    }

    return sanitized


_WORD_RE = re.compile(r"[a-z0-9]+")


def _normalize_text(text: str) -> str:
    return " ".join(_WORD_RE.findall((text or "").lower()))


def _infer_provider_from_title(title: str) -> str:
    t = (title or "").lower()
    if "aws" in t or "amazon" in t or "iam" in t or "cloudtrail" in t or "s3" in t or "ec2" in t:
        return "aws"
    if (
        "azure" in t
        or "entra" in t
        or "aad" in t
        or "microsoft" in t
        or "defender" in t
        or "storage account" in t
        or "key vault" in t
        or "resource group" in t
        or "subscription" in t
        or "virtual network" in t
        or "nsg" in t
    ):
        return "azure"
    if "gcp" in t or "google" in t or "gke" in t or "cloud run" in t or "cloud sql" in t:
        return "gcp"
    return "unknown"


def _infer_service_from_title(title: str, provider: str) -> str:
    t = (title or "").lower()
    if provider == "azure":
        if "storage" in t or "blob" in t or "file share" in t or "queue" in t:
            return "Azure Storage"
        if "key vault" in t:
            return "Azure Key Vault"
        if "sql" in t:
            return "Azure SQL"
        if "kubernetes" in t or "aks" in t:
            return "Azure Kubernetes Service"
        if "network security group" in t or "nsg" in t:
            return "Azure Network"
        if "virtual machine" in t or "vm" in t:
            return "Azure Virtual Machines"
        if "app service" in t or "web app" in t:
            return "Azure App Service"
        if "cosmos" in t:
            return "Azure Cosmos DB"
        if "monitor" in t or "log analytics" in t:
            return "Azure Monitor"
    if provider == "aws":
        if "s3" in t:
            return "Amazon S3"
        if "iam" in t:
            return "AWS IAM"
        if "cloudtrail" in t:
            return "AWS CloudTrail"
        if "ec2" in t:
            return "Amazon EC2"
        if "rds" in t:
            return "Amazon RDS"
        if "kms" in t:
            return "AWS KMS"
        if "vpc" in t:
            return "Amazon VPC"
    if provider == "gcp":
        if "gcs" in t or "cloud storage" in t:
            return "GCP Cloud Storage"
        if "iam" in t:
            return "GCP IAM"
        if "gke" in t or "kubernetes" in t:
            return "GKE"
        if "cloud sql" in t:
            return "Cloud SQL"
        if "bigquery" in t:
            return "BigQuery"
    return "unknown"


def _merge_doc_and_title_fallbacks(sanitized: dict, title: str) -> dict:
    provider = (sanitized.get("cloud_provider") or "").strip().lower()
    if provider in ("", "unknown", "null", "none"):
        provider = _infer_provider_from_title(title)
        sanitized["cloud_provider"] = provider

    # Fetch metadata from cloud documentation patterns
    doc_metadata = None
    if provider not in ("", "unknown"):
        try:
            doc_metadata = fetch_control_metadata(title, provider)
        except Exception:
            doc_metadata = None

    service = (sanitized.get("service") or "").strip()
    if service.lower() in ("", "unknown", "null", "none"):
        # Try doc metadata first
        if doc_metadata and doc_metadata.get("service") and doc_metadata["service"] != "unknown":
            sanitized["service"] = doc_metadata["service"]
        else:
            inferred_service = _infer_service_from_title(title, provider)
            if inferred_service != "unknown":
                sanitized["service"] = inferred_service

    # Apply doc metadata for empty fields
    if doc_metadata:
        if not sanitized.get("permissions") and doc_metadata.get("permissions"):
            sanitized["permissions"] = doc_metadata["permissions"]
        
        if not sanitized.get("api_calls") and doc_metadata.get("api_calls"):
            sanitized["api_calls"] = doc_metadata["api_calls"]
        
        if not sanitized.get("remediation") and doc_metadata.get("remediation"):
            sanitized["remediation"] = doc_metadata["remediation"]

    return sanitized


def _needs_retry(control: dict) -> bool:
    if not isinstance(control, dict):
        return True
    if (control.get("service") or "").strip().lower() in ("", "unknown", "null", "none"):
        return True
    if not control.get("permissions") and not control.get("api_calls"):
        return True
    if not control.get("remediation"):
        return True
    return False

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
- Do NOT use null for any field
- api_calls, permissions, remediation MUST be JSON arrays (use [] if truly unknown)
"""

    try:
        content = chat_completion(prompt, temperature=0.2)
    except RuntimeError as e:
        fallback = {
            "control_id": "llm_not_configured",
            "title": title,
            "cloud_provider": "unknown",
            "service": "unknown",
            "api_calls": [],
            "permissions": [],
            "remediation": [str(e)],
        }
        fallback = _merge_doc_and_title_fallbacks(fallback, title)
        return fallback

    content = _strip_code_fences(content)

    try:
        parsed = json.loads(content)
        sanitized = _sanitize_control(parsed, title)
    except:
        sanitized = {
            "control_id": "parse_error",
            "title": title,
            "cloud_provider": "unknown",
            "service": "unknown",
            "api_calls": [],
            "permissions": [],
            "remediation": ["Manual review required"],
        }

    sanitized = _merge_doc_and_title_fallbacks(sanitized, title)

    if _needs_retry(sanitized):
        retry_prompt = f"""
You are a cloud security engineer.

The previous output was incomplete. Try again and be SPECIFIC.

Policy:
"{title}"

Return ONLY JSON in this format:
{{
  "control_id": "short_unique_id",
  "title": "normalized control title",
  "cloud_provider": "aws/azure/gcp/unknown",
  "service": "specific service name (e.g., Azure Storage, AWS IAM, GCP GKE)",
  "api_calls": ["specific API/CLI calls used to audit"],
  "permissions": ["exact permissions/actions required"],
  "remediation": ["step-by-step remediation actions"]
}}

Hard requirements:
- service MUST NOT be "unknown"
- permissions MUST contain at least 1 item
- remediation MUST contain at least 2 steps
- api_calls MUST contain at least 1 realistic call (CLI/SDK/REST)
- No nulls; arrays must be arrays
"""

        try:
            retry_content = chat_completion(retry_prompt, temperature=0.2)
            retry_content = _strip_code_fences(retry_content)
            retry_parsed = json.loads(retry_content)
            retry_sanitized = _sanitize_control(retry_parsed, title)
            retry_sanitized = _merge_kb_and_title_fallbacks(retry_sanitized, title, kb_match)
            if not _needs_retry(retry_sanitized):
                return retry_sanitized
            return retry_sanitized
        except:
            return sanitized

    return sanitized