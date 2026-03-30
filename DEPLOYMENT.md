# Azure Web App Deployment Guide

Complete step-by-step guide to deploy your GAP Analysis FastAPI application to Azure Web App.

---

## Prerequisites

- Azure subscription with active credits
- GitHub account
- Git installed locally
- Azure CLI (optional, for command-line deployment)

---

## Part 1: Prepare Your Code for Deployment

### 1.1 Initialize Git Repository (if not already done)

```powershell
# Navigate to your project directory
cd C:\Scripts\GapAnalysisData

# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - GAP Analysis API"
```

### 1.2 Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., `gap-analysis-api`)
3. **Do NOT initialize with README** (you already have code)
4. Set to **Private** (recommended for enterprise projects)
5. Click "Create repository"

### 1.3 Push Code to GitHub

```powershell
# Add GitHub remote (replace with your repository URL)
git remote add origin https://github.com/YOUR_USERNAME/gap-analysis-api.git

# Push code
git branch -M main
git push -u origin main
```

---

## Part 2: Create Azure Web App

### Option A: Using Azure Portal (Recommended for First-Time)

#### Step 1: Create Web App

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"**
3. Search for **"Web App"** and click **Create**

#### Step 2: Configure Basic Settings

**Basics Tab:**
- **Subscription**: Select your subscription
- **Resource Group**: Create new (e.g., `rg-gap-analysis`) or use existing
- **Name**: Choose unique name (e.g., `gap-analysis-api-prod`)
  - This will be your URL: `https://gap-analysis-api-prod.azurewebsites.net`
- **Publish**: **Code**
- **Runtime stack**: **Python 3.11** (or latest available)
- **Operating System**: **Linux**
- **Region**: Choose closest to your users (e.g., `East US`, `West Europe`)

**Pricing Plan:**
- **Linux Plan**: Create new or select existing
- **Pricing Tier**: 
  - **Development**: `B1 Basic` ($13/month) - Good for testing
  - **Production**: `S1 Standard` ($70/month) - Recommended for production
  - Click **"Change size"** to see all options

#### Step 3: Configure Deployment

**Deployment Tab:**
- **Continuous deployment**: **Enable**
- **GitHub account**: Click **Authorize** and sign in
- **Organization**: Select your GitHub username
- **Repository**: Select `gap-analysis-api`
- **Branch**: `main`

#### Step 4: Review and Create

1. Click **"Review + create"**
2. Verify all settings
3. Click **"Create"**
4. Wait 2-3 minutes for deployment to complete

---

## Part 3: Configure Application Settings

### 3.1 Set Startup Command

1. In Azure Portal, go to your Web App
2. Navigate to **Settings** → **Configuration**
3. Click **"General settings"** tab
4. Under **Startup Command**, enter:
   ```
   python -m uvicorn api:app --host 0.0.0.0 --port 8000
   ```
5. Click **"Save"** at the top
6. Click **"Continue"** when prompted (app will restart)

### 3.2 Configure Environment Variables (Azure OpenAI)

1. Still in **Configuration** page
2. Click **"Application settings"** tab
3. Click **"+ New application setting"** for each variable below:

#### Required Settings for Azure OpenAI:

| Name | Value | Example |
|------|-------|---------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint | `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key | `abc123...` |
| `AZURE_OPENAI_DEPLOYMENT` | Your deployment name | `gpt-4o-mini` |
| `AZURE_OPENAI_API_VERSION` | API version (optional) | `2024-02-15-preview` |

#### Alternative: Standard OpenAI (if not using Azure OpenAI):

| Name | Value |
|------|-------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_MODEL` | Model name (optional, defaults to `gpt-4o-mini`) |

**Steps to add each setting:**
1. Click **"+ New application setting"**
2. Enter **Name** and **Value**
3. Click **"OK"**
4. Repeat for all variables
5. Click **"Save"** at the top
6. Click **"Continue"** to restart the app

### 3.3 Get Your Azure OpenAI Credentials

If you don't have Azure OpenAI yet:

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for **"Azure OpenAI"**
3. Click **"Create"** and fill in details
4. After creation, go to **Keys and Endpoint**
5. Copy **Endpoint** and **Key 1**
6. Go to **Model deployments** → **Manage Deployments**
7. Create a deployment (e.g., `gpt-4o-mini`)
8. Note the **deployment name**

---

## Part 4: Verify Deployment

### 4.1 Check Deployment Status

1. In your Web App, go to **Deployment** → **Deployment Center**
2. You should see GitHub connected
3. Check **Logs** tab to see build progress
4. Wait for **"Deployment successful"** message (5-10 minutes for first deployment)

### 4.2 Test Your API

Once deployment is complete:

1. Get your app URL: `https://YOUR_APP_NAME.azurewebsites.net`

2. **Test Health Endpoints:**
   ```
   https://YOUR_APP_NAME.azurewebsites.net/health/llm
   https://YOUR_APP_NAME.azurewebsites.net/health/kb
   ```

3. **Test Main Endpoint:**
   - Use Postman, curl, or browser
   - POST to: `https://YOUR_APP_NAME.azurewebsites.net/analyze`
   - Upload your GAP Excel file
   - You should get JSON response with enriched controls

### 4.3 View Application Logs

If something goes wrong:

1. Go to **Monitoring** → **Log stream**
2. Watch real-time logs
3. Look for errors in startup or request handling

Or download logs:
1. Go to **Development Tools** → **Advanced Tools** → **Go**
2. Click **Debug console** → **CMD**
3. Navigate to `LogFiles/` to see detailed logs

---

## Part 5: Testing with Postman/cURL

### Test /analyze Endpoint

**Using cURL (PowerShell):**
```powershell
$uri = "https://YOUR_APP_NAME.azurewebsites.net/analyze"
$file = "C:\path\to\your\gap_file.xlsx"

curl.exe -X POST $uri `
  -F "file=@$file" `
  -H "Accept: application/json"
```

**Using Postman:**
1. Create new POST request
2. URL: `https://YOUR_APP_NAME.azurewebsites.net/analyze`
3. Go to **Body** tab
4. Select **form-data**
5. Add key: `file` (type: File)
6. Choose your Excel file
7. Click **Send**

### Expected Response

```json
{
  "gap_analysis_download": "Use /download endpoint",
  "gap_controls": [
    {
      "control_id": "gap_1",
      "title": "App Service apps should disable public network access",
      "cloud_provider": "azure",
      "service": "Azure App Service",
      "api_calls": [
        "az webapp list",
        "az webapp show --name <app-name> --resource-group <rg>",
        "az webapp show --name <app-name> --resource-group <rg> --query publicNetworkAccess"
      ],
      "permissions": [
        "Microsoft.Web/sites/read",
        "Microsoft.Web/sites/config/read",
        "Microsoft.Web/sites/config/write"
      ],
      "remediation": [
        "Navigate to the resource in Azure Portal",
        "Go to 'Networking' or 'Network settings'",
        "Set 'Public network access' to 'Disabled'",
        "Configure private endpoints if needed",
        "Save the configuration"
      ]
    }
  ]
}
```

---

## Part 6: Continuous Deployment (Automatic Updates)

Once GitHub is connected, any push to `main` branch will automatically deploy:

```powershell
# Make changes to your code
# Commit and push
git add .
git commit -m "Updated service detection patterns"
git push origin main

# Azure will automatically:
# 1. Detect the push
# 2. Pull latest code
# 3. Install dependencies
# 4. Restart the app
# 5. Takes ~5 minutes
```

Monitor deployment in **Deployment Center** → **Logs**

---

## Part 7: Troubleshooting

### Issue: App shows "Application Error"

**Solution:**
1. Check **Log stream** for errors
2. Verify startup command is correct
3. Ensure `requirements.txt` has all dependencies
4. Check Python version matches (3.11 recommended)

### Issue: LLM returns empty data

**Solution:**
1. Verify environment variables are set correctly
2. Check `/health/llm` endpoint to see detected config
3. Ensure Azure OpenAI resource is in same subscription
4. Verify API key is valid (regenerate if needed)

### Issue: Deployment fails

**Solution:**
1. Check GitHub Actions logs in your repository
2. Verify `requirements.txt` syntax is correct
3. Ensure no syntax errors in Python files
4. Check deployment logs in Azure Portal

### Issue: Slow performance

**Solution:**
1. Upgrade to higher pricing tier (S1 or above)
2. Enable **Always On** in Configuration → General settings
3. Consider adding Application Insights for monitoring

---

## Part 8: Security Best Practices

### 8.1 Enable HTTPS Only
1. Go to **Settings** → **Configuration**
2. **General settings** tab
3. Set **HTTPS Only** to **On**

### 8.2 Enable Authentication (Optional)
1. Go to **Settings** → **Authentication**
2. Click **Add identity provider**
3. Choose **Microsoft** (Azure AD) or other provider
4. Configure as needed

### 8.3 Restrict Access by IP (Optional)
1. Go to **Settings** → **Networking**
2. Click **Access restriction**
3. Add allowed IP ranges

### 8.4 Monitor API Keys
- Never commit API keys to GitHub
- Rotate keys regularly (every 90 days)
- Use Azure Key Vault for production (advanced)

---

## Part 9: Scaling and Monitoring

### Enable Application Insights

1. Go to your Web App
2. Navigate to **Settings** → **Application Insights**
3. Click **Turn on Application Insights**
4. Create new or use existing workspace
5. Click **Apply**

**Benefits:**
- Request/response tracking
- Performance monitoring
- Error tracking
- Custom metrics

### Scale Up (Vertical Scaling)

1. Go to **Settings** → **Scale up (App Service plan)**
2. Choose higher tier for more CPU/RAM
3. Click **Apply**

### Scale Out (Horizontal Scaling)

1. Go to **Settings** → **Scale out (App Service plan)**
2. Set instance count (2-10 instances)
3. Or enable **Auto-scale** based on CPU/memory

---

## Part 10: Cost Optimization

### Pricing Estimates

| Tier | Monthly Cost | Use Case |
|------|--------------|----------|
| B1 Basic | ~$13 | Development/Testing |
| S1 Standard | ~$70 | Small production |
| P1V2 Premium | ~$146 | Production with high traffic |

### Save Costs:
- Use **B1** for development
- Stop app when not in use (dev environments)
- Use **consumption-based** pricing for Azure OpenAI
- Monitor usage in **Cost Management**

---

## Quick Reference Commands

```powershell
# Check app status
az webapp show --name YOUR_APP_NAME --resource-group YOUR_RG

# View logs
az webapp log tail --name YOUR_APP_NAME --resource-group YOUR_RG

# Restart app
az webapp restart --name YOUR_APP_NAME --resource-group YOUR_RG

# Set environment variable
az webapp config appsettings set --name YOUR_APP_NAME --resource-group YOUR_RG --settings AZURE_OPENAI_ENDPOINT="https://..."
```

---

## Support and Next Steps

### Your API Endpoints:
- **Analyze**: `POST /analyze` - Upload GAP file, get enriched controls
- **Download**: `POST /download` - Get Excel file with results
- **Health Check**: `GET /health/llm` - Verify LLM configuration
- **KB Check**: `GET /health/kb` - Verify knowledge base

### Documentation:
- Azure Web App: https://learn.microsoft.com/azure/app-service/
- Azure OpenAI: https://learn.microsoft.com/azure/ai-services/openai/
- FastAPI: https://fastapi.tiangolo.com/

---

**Deployment Complete! 🚀**

Your GAP Analysis API is now live and accessible from anywhere. All control metadata is generated dynamically from cloud documentation patterns - no data files needed in your repository.
