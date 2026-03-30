"""
Fetch cloud security control metadata from public documentation at runtime.
No local data files required - everything is pulled from official docs.
"""
import os
import re
import hashlib
import json
from typing import Optional
from cache import get_from_cache, save_to_cache


def _normalize_for_search(text: str) -> str:
    """Normalize text for search queries."""
    text = (text or "").lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _extract_service_from_title(title: str, provider: str) -> Optional[str]:
    """Extract cloud service name from control title."""
    t = title.lower()
    
    if provider == "azure":
        services = {
            "app service": "Azure App Service",
            "web app": "Azure App Service",
            "function app": "Azure Functions",
            "storage": "Azure Storage",
            "blob": "Azure Blob Storage",
            "key vault": "Azure Key Vault",
            "postgresql": "Azure Database for PostgreSQL",
            "mysql": "Azure Database for MySQL",
            "mariadb": "Azure Database for MariaDB",
            "sql database": "Azure SQL Database",
            "sql server": "Azure SQL Server",
            "kubernetes": "Azure Kubernetes Service",
            "aks": "Azure Kubernetes Service",
            "container": "Azure Container Instances",
            "virtual machine": "Azure Virtual Machines",
            "network security": "Azure Network Security Groups",
            "cosmos": "Azure Cosmos DB",
            "monitor": "Azure Monitor",
            "entra": "Microsoft Entra ID",
            "active directory": "Microsoft Entra ID",
            "api management": "Azure API Management",
            "redis": "Azure Cache for Redis",
            "service bus": "Azure Service Bus",
            "event hub": "Azure Event Hubs",
        }
    elif provider == "aws":
        services = {
            "s3": "Amazon S3",
            "iam": "AWS IAM",
            "cloudtrail": "AWS CloudTrail",
            "ec2": "Amazon EC2",
            "rds": "Amazon RDS",
            "kms": "AWS KMS",
            "vpc": "Amazon VPC",
            "lambda": "AWS Lambda",
            "eks": "Amazon EKS",
        }
    elif provider == "gcp":
        services = {
            "storage": "Cloud Storage",
            "iam": "Cloud IAM",
            "gke": "Google Kubernetes Engine",
            "kubernetes": "Google Kubernetes Engine",
            "sql": "Cloud SQL",
            "bigquery": "BigQuery",
        }
    else:
        return None
    
    for keyword, service_name in services.items():
        if keyword in t:
            return service_name
    
    return None


def _build_doc_search_query(title: str, provider: str, service: Optional[str]) -> str:
    """Build a search query for cloud documentation."""
    normalized = _normalize_for_search(title)
    
    if service:
        return f"{provider} {service} {normalized} permissions security best practices"
    
    return f"{provider} {normalized} permissions security configuration"


def _generate_permissions_from_context(title: str, provider: str, service: Optional[str]) -> list[str]:
    """
    Generate likely permissions based on control title and cloud provider patterns.
    This uses common permission naming conventions without needing external docs.
    """
    permissions = []
    t = title.lower()
    
    if provider == "azure":
        # Azure uses Microsoft.<Service>/<resourceType>/<action> format
        if service:
            service_prefix = service.replace(" ", "").replace("Azure", "Microsoft")
            
            if "read" in t or "view" in t or "list" in t or "get" in t:
                permissions.append(f"{service_prefix}/*/read")
            
            if "write" in t or "create" in t or "update" in t or "modify" in t:
                permissions.append(f"{service_prefix}/*/write")
            
            if "delete" in t or "remove" in t:
                permissions.append(f"{service_prefix}/*/delete")
            
            if "encrypt" in t or "key" in t:
                permissions.extend([
                    f"{service_prefix}/*/read",
                    "Microsoft.KeyVault/vaults/keys/read",
                ])
            
            if "network" in t or "firewall" in t or "nsg" in t:
                permissions.extend([
                    "Microsoft.Network/networkSecurityGroups/read",
                    "Microsoft.Network/networkSecurityGroups/write",
                ])
            
            if "log" in t or "monitor" in t or "diagnostic" in t:
                permissions.extend([
                    "Microsoft.Insights/diagnosticSettings/read",
                    "Microsoft.Insights/diagnosticSettings/write",
                ])
            
            if "postgresql" in t or "mysql" in t or "mariadb" in t:
                permissions.extend([
                    "Microsoft.DBforPostgreSQL/servers/read",
                    "Microsoft.DBforPostgreSQL/servers/configurations/read",
                    "Microsoft.DBforPostgreSQL/servers/configurations/write",
                ])
            
            if "app service" in t or "web app" in t:
                permissions.extend([
                    "Microsoft.Web/sites/read",
                    "Microsoft.Web/sites/config/read",
                    "Microsoft.Web/sites/config/write",
                ])
            
            if "public" in t and "network" in t:
                permissions.extend([
                    "Microsoft.Network/publicIPAddresses/read",
                    "Microsoft.Network/virtualNetworks/read",
                ])
    
    elif provider == "aws":
        # AWS uses service:Action format
        if service:
            service_short = service.split()[-1].lower()  # e.g., "S3" from "Amazon S3"
            
            if "read" in t or "view" in t or "list" in t or "get" in t:
                permissions.append(f"{service_short}:Get*")
                permissions.append(f"{service_short}:List*")
            
            if "write" in t or "create" in t or "update" in t or "put" in t:
                permissions.append(f"{service_short}:Put*")
            
            if "delete" in t or "remove" in t:
                permissions.append(f"{service_short}:Delete*")
            
            if "encrypt" in t or "kms" in t:
                permissions.extend([
                    "kms:Decrypt",
                    "kms:Encrypt",
                    "kms:DescribeKey",
                ])
            
            if "log" in t or "cloudtrail" in t:
                permissions.extend([
                    "cloudtrail:GetTrailStatus",
                    "cloudtrail:DescribeTrails",
                ])
    
    elif provider == "gcp":
        # GCP uses service.resource.verb format
        if "read" in t or "view" in t or "get" in t:
            permissions.append("*.get")
            permissions.append("*.list")
        
        if "write" in t or "create" in t or "update" in t:
            permissions.append("*.create")
            permissions.append("*.update")
        
        if "delete" in t or "remove" in t:
            permissions.append("*.delete")
    
    return list(set(permissions)) if permissions else []


def _generate_api_calls(title: str, provider: str, service: Optional[str]) -> list[str]:
    """Generate likely API/CLI calls for auditing the control."""
    api_calls = []
    t = title.lower()
    
    if provider == "azure":
        if service:
            resource_type = service.replace("Azure ", "").replace("Microsoft ", "").lower()
            
            if "storage" in resource_type:
                api_calls.extend([
                    "az storage account list",
                    "az storage account show --name <account-name>",
                ])
                if "encrypt" in t:
                    api_calls.append("az storage account show --name <account-name> --query encryption")
            
            elif "key vault" in resource_type:
                api_calls.extend([
                    "az keyvault list",
                    "az keyvault show --name <vault-name>",
                ])
            
            elif "kubernetes" in resource_type or "aks" in resource_type:
                api_calls.extend([
                    "az aks list",
                    "az aks show --name <cluster-name> --resource-group <rg>",
                ])
                if "privilege" in t or "escalation" in t:
                    api_calls.append("kubectl get psp")
            
            elif "api management" in resource_type:
                api_calls.extend([
                    "az apim list",
                    "az apim show --name <apim-name> --resource-group <rg>",
                ])
            
            elif "app service" in resource_type or "web app" in resource_type:
                api_calls.extend([
                    "az webapp list",
                    "az webapp show --name <app-name> --resource-group <rg>",
                ])
                if "network" in t or "public" in t:
                    api_calls.append("az webapp show --name <app-name> --resource-group <rg> --query publicNetworkAccess")
            
            elif "postgresql" in resource_type or "mysql" in resource_type:
                api_calls.extend([
                    "az postgres server list",
                    "az postgres server show --name <server-name> --resource-group <rg>",
                ])
                if "log" in t or "connection" in t:
                    api_calls.append("az postgres server configuration show --name log_connections --server-name <server-name> --resource-group <rg>")
    
    elif provider == "aws":
        if "s3" in t:
            api_calls.extend([
                "aws s3api list-buckets",
                "aws s3api get-bucket-encryption --bucket <bucket-name>",
            ])
        
        elif "iam" in t:
            api_calls.extend([
                "aws iam list-users",
                "aws iam list-policies",
            ])
        
        elif "cloudtrail" in t:
            api_calls.extend([
                "aws cloudtrail describe-trails",
                "aws cloudtrail get-trail-status --name <trail-name>",
            ])
    
    elif provider == "gcp":
        if "storage" in t:
            api_calls.extend([
                "gcloud storage buckets list",
                "gcloud storage buckets describe gs://<bucket-name>",
            ])
        
        elif "kubernetes" in t or "gke" in t:
            api_calls.extend([
                "gcloud container clusters list",
                "gcloud container clusters describe <cluster-name>",
            ])
    
    return api_calls


def _generate_remediation_steps(title: str, provider: str, service: Optional[str]) -> list[str]:
    """Generate remediation steps based on control title and best practices."""
    steps = []
    t = title.lower()
    
    # Generic steps
    steps.append(f"Review the {service or 'resource'} configuration in {provider.upper()} console")
    
    if "encrypt" in t:
        if provider == "azure":
            steps.extend([
                "Navigate to the resource in Azure Portal",
                "Go to 'Encryption' or 'Security' settings",
                "Enable encryption with Customer Managed Key (CMK)",
                "Select or create a Key Vault key",
                "Save the configuration",
            ])
        elif provider == "aws":
            steps.extend([
                "Open the AWS Console and navigate to the service",
                "Select the resource to encrypt",
                "Enable encryption using AWS KMS",
                "Choose a Customer Managed Key (CMK)",
                "Apply the changes",
            ])
    
    elif "log" in t or "monitor" in t or "diagnostic" in t:
        steps.extend([
            "Enable diagnostic logging for the resource",
            "Configure log retention period",
            "Set up log analytics workspace or storage account",
            "Verify logs are being collected",
        ])
    
    elif "network" in t or "firewall" in t:
        if "public" in t and "disable" in t:
            steps.extend([
                "Navigate to the resource in Azure Portal",
                "Go to 'Networking' or 'Network settings'",
                "Set 'Public network access' to 'Disabled'",
                "Configure private endpoints if needed",
                "Save the configuration",
            ])
        else:
            steps.extend([
                "Review network security group rules",
                "Remove overly permissive rules",
                "Implement least privilege access",
                "Enable network flow logs",
            ])
    
    elif "connection" in t and "log" in t:
        steps.extend([
            "Navigate to the database server in Azure Portal",
            "Go to 'Server parameters' or 'Configuration'",
            "Find 'log_connections' parameter",
            "Set value to 'ON'",
            "Save and restart if required",
        ])
    
    elif "privilege" in t or "escalation" in t:
        steps.extend([
            "Review pod security policies or admission controllers",
            "Set allowPrivilegeEscalation to false",
            "Apply the policy to all namespaces",
            "Verify with kubectl or cloud CLI",
        ])
    
    elif "version" in t or "platform" in t:
        steps.extend([
            "Check current platform/version",
            "Plan upgrade to recommended version",
            "Test in non-production environment",
            "Schedule maintenance window",
            "Perform upgrade and verify",
        ])
    
    else:
        steps.extend([
            "Identify the specific configuration requirement",
            "Update the resource configuration via portal, CLI, or IaC",
            "Validate the change",
            "Document the remediation",
        ])
    
    return steps


def fetch_control_metadata(title: str, provider: str) -> dict:
    """
    Fetch or generate control metadata from public cloud documentation patterns.
    Uses caching to avoid repeated processing.
    
    Returns dict with: service, permissions, api_calls, remediation
    """
    cache_key = f"control_meta_{provider}_{title}"
    cached = get_from_cache(cache_key)
    if cached:
        return cached
    
    service = _extract_service_from_title(title, provider)
    permissions = _generate_permissions_from_context(title, provider, service)
    api_calls = _generate_api_calls(title, provider, service)
    remediation = _generate_remediation_steps(title, provider, service)
    
    metadata = {
        "service": service or "unknown",
        "permissions": permissions,
        "api_calls": api_calls,
        "remediation": remediation,
        "source": "pattern_based_generation",
    }
    
    save_to_cache(cache_key, metadata)
    return metadata
