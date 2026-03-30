# GAP Analysis API

FastAPI-based REST API for analyzing cloud security GAP (Governance, Audit, and Policy) controls. Automatically enriches control data with permissions, API calls, and remediation steps using cloud documentation patterns and Azure OpenAI.

## Features

- 📊 **Excel GAP File Analysis** - Upload Excel files with control titles
- 🤖 **AI-Powered Enrichment** - Uses Azure OpenAI to enhance control metadata
- 🔍 **Pattern-Based Fallbacks** - Generates permissions/API calls from cloud provider patterns (no data files needed)
- ☁️ **Multi-Cloud Support** - Azure, AWS, and GCP
- 📥 **Excel Export** - Download enriched results as formatted Excel
- 🚀 **Azure Web App Ready** - Optimized for Azure deployment

## Architecture

```
┌─────────────────┐
│  Excel Upload   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  FastAPI API (/analyze endpoint)   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Control Generator                  │
│  - Parses GAP titles                │
│  - Detects cloud provider           │
└────────┬────────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────────────┐
│ LLM     │ │ Cloud Docs Fetcher   │
│ Service │ │ - Pattern matching   │
│ (Azure  │ │ - Service detection  │
│ OpenAI) │ │ - Permission rules   │
└────┬────┘ └──────────┬───────────┘
     │               │
     └───────┬───────┘
             │
             ▼
    ┌─────────────────┐
    │ Enriched Control│
    │ - Service       │
    │ - Permissions   │
    │ - API Calls     │
    │ - Remediation   │
    └─────────────────┘
```

## API Endpoints

### `POST /analyze`
Upload GAP Excel file and get enriched JSON response.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (Excel file)

**Response:**
```json
{
  "gap_analysis_download": "Use /download endpoint",
  "gap_controls": [
    {
      "control_id": "gap_1",
      "title": "App Service apps should disable public network access",
      "cloud_provider": "azure",
      "service": "Azure App Service",
      "api_calls": ["az webapp list", "..."],
      "permissions": ["Microsoft.Web/sites/read", "..."],
      "remediation": ["Navigate to resource...", "..."]
    }
  ]
}
```

### `POST /download`
Get enriched results as formatted Excel file.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (Excel file)

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Excel file with enriched control data

### `GET /health/llm`
Check LLM configuration status.

**Response:**
```json
{
  "mode": "azure_openai",
  "azure": {
    "endpoint_present": true,
    "endpoint": "https://your-resource.openai.azure.com/",
    "api_key_present": true,
    "deployment": "gpt-4o-mini"
  }
}
```


## Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

1. **Clone repository:**
```powershell
git clone https://github.com/YOUR_USERNAME/gap-analysis-api.git
cd gap-analysis-api
```

2. **Create virtual environment:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

4. **Set environment variables:**

Create `.env` file or set in your IDE:
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

Or use standard OpenAI:
```env
OPENAI_API_KEY=your-openai-key
```

5. **Run the application:**
```powershell
python -m uvicorn api:app --reload
```

6. **Test locally:**
- Open browser: http://localhost:8000/docs
- Or use Postman/curl to test endpoints

## Deployment to Azure Web App

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete step-by-step deployment guide.

### Quick Deploy Steps:

1. **Push to GitHub:**
```powershell
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/gap-analysis-api.git
git push -u origin main
```

2. **Create Azure Web App:**
- Go to Azure Portal
- Create Web App (Python 3.11, Linux)
- Connect to GitHub repository
- Enable continuous deployment

3. **Configure Settings:**
- Set startup command: `python -m uvicorn api:app --host 0.0.0.0 --port 8000`
- Add environment variables (Azure OpenAI credentials)

4. **Deploy and Test:**
- Wait for deployment to complete
- Test: `https://YOUR_APP_NAME.azurewebsites.net/health/llm`

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Yes* | Azure OpenAI endpoint | `https://resource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Yes* | Azure OpenAI API key | `abc123...` |
| `AZURE_OPENAI_DEPLOYMENT` | Yes* | Deployment/model name | `gpt-4o-mini` |
| `AZURE_OPENAI_API_VERSION` | No | API version | `2024-02-15-preview` |
| `OPENAI_API_KEY` | Yes** | Standard OpenAI key | `sk-...` |
| `OPENAI_MODEL` | No | OpenAI model name | `gpt-4o-mini` |

\* Required if using Azure OpenAI  
\** Required if using standard OpenAI (alternative to Azure)

## Project Structure

```
gap-analysis-api/
├── api.py                    # FastAPI application & endpoints
├── control_generator.py      # Main control generation logic
├── ai_control_generator.py   # LLM integration & enrichment
├── llm_service.py            # Azure OpenAI/OpenAI client wrapper
├── cloud_docs_fetcher.py     # Pattern-based metadata generation
├── cache.py                  # Simple in-memory caching
├── engine.py                 # Excel processing utilities
├── requirements.txt          # Python dependencies
├── startup.sh                # Azure Web App startup script
├── .gitignore               # Git ignore rules
├── README.md                # This file
└── DEPLOYMENT.md            # Detailed deployment guide
```

## How It Works

### 1. Control Title Parsing
Extracts control titles from uploaded Excel file (first column).

### 2. Cloud Provider Detection
Identifies provider (Azure/AWS/GCP) from keywords in title:
- "Azure", "App Service", "Key Vault" → Azure
- "S3", "EC2", "IAM" → AWS
- "GKE", "BigQuery" → GCP

### 3. Service Detection
Matches title keywords to cloud services:
- "App Service" → Azure App Service
- "PostgreSQL" → Azure Database for PostgreSQL
- "S3" → Amazon S3

### 4. Metadata Enrichment
Generates control metadata using two approaches:

**A. LLM-Based (Primary):**
- Sends control title to Azure OpenAI
- Gets structured JSON with permissions, API calls, remediation
- Retries with stronger prompt if output incomplete

**B. Pattern-Based (Fallback):**
- Uses cloud provider naming conventions
- Generates permissions based on service patterns
- Creates CLI commands for auditing
- Provides step-by-step remediation

### 5. Output Generation
Returns enriched JSON or formatted Excel with:
- Control ID (gap_1, gap_2, ...)
- Cloud provider
- Service name
- Required permissions
- API/CLI commands for auditing
- Remediation steps

## Supported Services

### Azure
App Service, Storage, Key Vault, PostgreSQL, MySQL, SQL Database, Kubernetes (AKS), Virtual Machines, API Management, Cosmos DB, Redis, Service Bus, Event Hubs, Network Security Groups, Monitor

### AWS
S3, EC2, RDS, IAM, CloudTrail, KMS, VPC, Lambda, EKS

### GCP
Cloud Storage, Cloud SQL, GKE, BigQuery, Cloud IAM

## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pandas** - Excel processing
- **openpyxl** - Excel file handling
- **openai** - Azure OpenAI/OpenAI SDK
- **python-multipart** - File upload support

## Security

- ✅ API keys stored as environment variables (never in code)
- ✅ `.gitignore` prevents committing secrets
- ✅ HTTPS enforced on Azure Web App
- ✅ No sensitive data in logs
- ⚠️ Consider Azure Key Vault for production secrets
- ⚠️ Enable authentication for production deployments

## Troubleshooting

### Empty permissions/API calls in output
- **Cause**: LLM not configured or service not recognized
- **Solution**: 
  1. Check `/health/llm` endpoint
  2. Verify environment variables are set
  3. Add service patterns to `cloud_docs_fetcher.py`

### "Application Error" on Azure
- **Cause**: Startup command incorrect or dependencies missing
- **Solution**:
  1. Check Log Stream in Azure Portal
  2. Verify startup command: `python -m uvicorn api:app --host 0.0.0.0 --port 8000`
  3. Ensure Python version matches (3.11)

### Slow performance
- **Cause**: Basic tier or cold start
- **Solution**:
  1. Upgrade to S1 or higher tier
  2. Enable "Always On" in Azure configuration
  3. Add caching for repeated requests

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-service`)
3. Add service patterns to `cloud_docs_fetcher.py`
4. Test locally
5. Commit changes (`git commit -m "Add support for Azure Service X"`)
6. Push to branch (`git push origin feature/new-service`)
7. Open Pull Request

## License

Proprietary - Internal use only

## Support

For issues or questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
2. Review Azure Web App logs
3. Test with `/health/llm` and `/health/kb` endpoints
4. Contact your Azure administrator for subscription/quota issues

---

**Built with ❤️ for cloud security compliance automation**
