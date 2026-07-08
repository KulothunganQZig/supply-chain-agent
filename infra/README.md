# Azure provisioning — Phase 1 (Azure OpenAI only)

Stands up the Azure OpenAI resource + model deployment that lights up the LLM
reasoning ([mitigation.py](../src/executors/mitigation.py)) and email-parsing
([email_parsing.py](../src/email_parsing.py)) hooks. Keyless: auth is AAD-only
(`disableLocalAuth: true`), so there is **no API key to copy** — access is
granted by RBAC role assignment instead.

## Prerequisites

- **Azure CLI** — not currently installed on this machine. Install:
  `winget install -e --id Microsoft.AzureCLI` (then reopen the shell).
- An Azure subscription with quota for Azure OpenAI + the GPT-4.1 model.

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
MODEL_DEPLOYMENT_NAME=<modelDeploymentName output>   # gpt-4.1
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

- **Model version/region**: GPT-4.1 availability varies by region. If the deploy
  fails on the model, check `az cognitiveservices account list-models` and adjust
  `modelVersion` in `main.bicepparam`.
- **RBAC propagation**: role assignments can take a few minutes to take effect —
  a 401/403 immediately after deploy usually just means "wait and retry".
- **Cost**: an idle Azure OpenAI resource costs nothing; you pay per token. The
  `S0` SKU + 30K TPM here is a modest dev default.
- **Teardown**: `az group delete -n rg-supplychain-agent` removes everything.
