# Azure provisioning — Phase 1 (Azure OpenAI only)

Stands up the Azure OpenAI resource + model deployment that lights up the LLM
reasoning ([mitigation.py](../src/executors/mitigation.py)) and email-parsing
([email_parsing.py](../src/email_parsing.py)) hooks. Keyless: auth is AAD-only
(`disableLocalAuth: true`), so there is **no API key to copy** — access is
granted by RBAC role assignment instead.

## Prerequisites

- **Azure CLI** — installed here **without admin rights** via pip into a
  dedicated venv (the standard MSI/winget install needs admin):

  ```powershell
  # one-time, using the project's real Python:
  .\.venv\Scripts\python.exe -m venv "$env:USERPROFILE\azcli-venv"
  & "$env:USERPROFILE\azcli-venv\Scripts\python.exe" -m pip install azure-cli
  # add to user PATH (no admin); open a NEW terminal afterwards for plain `az`:
  # (already done on this machine — az.bat lives in %USERPROFILE%\azcli-venv\Scripts)
  az bicep install    # installs the Bicep CLI to %USERPROFILE%\.azure\bin
  ```

  Installed version: azure-cli 2.88.0, bicep 0.44.1.
  If `az` isn't found, either open a new terminal (PATH refresh) or call
  `%USERPROFILE%\azcli-venv\Scripts\az.bat` directly.
- An Azure subscription with quota for Azure OpenAI + the GPT-4.1 model.
- **No admin?** If the pip route ever fails, Azure Cloud Shell
  (`shell.azure.com`) has `az` + `bicep` preinstalled in-browser — upload
  `infra/` and run the same commands.

## Steps

```bash
# 1. Sign in and pick the target subscription
az login
az account set --subscription "<SUBSCRIPTION-NAME-OR-ID>"

# 2. Get your AAD object ID and paste it into main.bicepparam (principalId)
az ad signed-in-user show --query id -o tsv

# 3. Create the resource group
az group create -n rg-supplychain-agent -l eastus2

# 4. (optional) Preview what will be created
az deployment group what-if -g rg-supplychain-agent \
  -f infra/main.bicep -p infra/main.bicepparam

# 5. Deploy
az deployment group create -g rg-supplychain-agent \
  -f infra/main.bicep -p infra/main.bicepparam

# 6. Read the outputs
az deployment group show -g rg-supplychain-agent -n main \
  --query properties.outputs
```

## Wire it into the app

Copy `.env.example` to `.env` and set the two values from the deployment outputs:

```
AZURE_OPENAI_ENDPOINT=<azureOpenAIEndpoint output>   # https://<name>.openai.azure.com/
MODEL_DEPLOYMENT_NAME=<modelDeploymentName output>   # gpt-5-mini
```

Then run the pipeline — the LLM path activates automatically (no code change):

```bash
python -m src.main      # or: python -m src.api  → POST /run
```

The `az login` session is what `DefaultAzureCredential` uses locally, and the
role assignment in the Bicep grants that identity **Cognitive Services OpenAI
User** on the resource. In production the same code authenticates as a Managed
Identity instead — set `principalType = 'ServicePrincipal'` and `principalId`
to the identity's object ID.

## Notes / gotchas

- **Model version/region**: model versions age out fast. `gpt-4.1`,
  `gpt-4.1-mini`, and `gpt-4o-mini` all hit a deprecating state (~Oct 2026) and
  Azure blocks them for *new* deployments; the template uses `gpt-5-mini`
  (2025-08-07, runs to 2027-02-06) on the `GlobalStandard` SKU. If it ever fails
  on the model, list current options and their deprecation dates with:
  `az cognitiveservices model list --location eastus2 --query "[?starts_with(model.name,'gpt-')].{n:model.name,v:model.version,dep:model.deprecation.inference}" -o table`
  then adjust `modelName`/`modelVersion`/`skuName` in `main.bicepparam`.
- **RBAC propagation**: role assignments can take a few minutes to take effect —
  a 401/403 immediately after deploy usually just means "wait and retry".
- **Cost**: an idle Azure OpenAI resource costs nothing; you pay per token. The
  `S0` SKU + 30K TPM here is a modest dev default.
- **Teardown**: `az group delete -n rg-supplychain-agent` removes everything.
