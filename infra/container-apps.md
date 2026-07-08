# Azure provisioning — Phase 2 (Container Apps)

Builds the image in the cloud (no local Docker needed) and runs it on Azure
Container Apps, pulling from ACR and calling Azure OpenAI **keyless** via a
user-assigned Managed Identity. Assumes Phase 1 (`README.md`) is done — the
Azure OpenAI resource + `rg-supplychain-agent` already exist.

## What gets created

| Resource | Name (this deployment) | Purpose |
|---|---|---|
| Azure Container Registry (Basic) | `acrsupplychain85768` | holds the image |
| User-assigned Managed Identity | `id-supplychain-app` | keyless AcrPull + OpenAI access |
| Container Apps environment | `cae-supplychain` | + auto-created Log Analytics |
| Container App | `ca-supplychain` | runs `uvicorn src.api:app`, scales 0→1 |

## Steps (run after `az login`)

```bash
RG=rg-supplychain-agent
ACR=acrsupplychain$RANDOM          # must be globally unique, lowercase alnum
OAI=oai-supplychain-vpv6suzb4aue6  # the Phase 1 Azure OpenAI resource

# 1. Providers + registry
az provider register -n Microsoft.App --wait
az provider register -n Microsoft.ContainerRegistry --wait
az provider register -n Microsoft.OperationalInsights --wait
az acr create -g $RG -n $ACR --sku Basic --admin-enabled false

# 2. Build the image IN the cloud (no local daemon) — validates the Dockerfile
az acr build --registry $ACR --image supply-chain-agent:v1 .

# 3. Managed identity + keyless role assignments
az identity create -g $RG -n id-supplychain-app
PRINCIPAL=$(az identity show -g $RG -n id-supplychain-app --query principalId -o tsv)
IDID=$(az identity show -g $RG -n id-supplychain-app --query id -o tsv)
CLIENTID=$(az identity show -g $RG -n id-supplychain-app --query clientId -o tsv)
az role assignment create --assignee-object-id $PRINCIPAL --assignee-principal-type ServicePrincipal \
  --role AcrPull --scope $(az acr show -g $RG -n $ACR --query id -o tsv)
az role assignment create --assignee-object-id $PRINCIPAL --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" \
  --scope $(az cognitiveservices account show -g $RG -n $OAI --query id -o tsv)

# 4. Environment + app
az extension add -n containerapp
az containerapp env create -g $RG -n cae-supplychain -l eastus2
az containerapp create -g $RG -n ca-supplychain \
  --environment cae-supplychain \
  --image $ACR.azurecr.io/supply-chain-agent:v1 \
  --user-assigned $IDID \
  --registry-server $ACR.azurecr.io --registry-identity $IDID \
  --target-port 8000 --ingress external \
  --min-replicas 0 --max-replicas 1 \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=https://$OAI.openai.azure.com/ \
    MODEL_DEPLOYMENT_NAME=gpt-5-mini \
    AZURE_OPENAI_API_VERSION=2025-04-01-preview \
    AZURE_CLIENT_ID=$CLIENTID
```

`AZURE_CLIENT_ID` is essential: it tells `DefaultAzureCredential` *which*
user-assigned identity to use, so the keyless OpenAI call resolves.

## Test

```bash
FQDN=$(az containerapp show -g $RG -n ca-supplychain --query properties.configuration.ingress.fqdn -o tsv)
curl https://$FQDN/health              # {"status":"ok"}
curl -X POST https://$FQDN/run         # full pipeline; reasoning is LLM-authored
```

## Redeploy after a code change

```bash
az acr build --registry $ACR --image supply-chain-agent:v2 .
az containerapp update -g $RG -n ca-supplychain --image $ACR.azurecr.io/supply-chain-agent:v2
```

## Notes / gotchas

- **No local Docker required.** `az acr build` runs the build server-side. (Our
  local Docker Desktop engine was down; this sidesteps it entirely.)
- **Windows CLI + `az acr build`**: streaming build logs can crash with a
  `UnicodeEncodeError` (cp1252 console). The build still runs — set
  `PYTHONUTF8=1`, or check status with `az acr task list-runs -r $ACR --top 1`.
- **Scale-to-zero**: `--min-replicas 0` means the first request after idle
  cold-starts (a few seconds). Set `--min-replicas 1` to keep it warm (costs more).
- **Cost**: ACR Basic ~$5/mo; Container Apps consumption is ~free at zero
  replicas; OpenAI is pay-per-token. Teardown: `az group delete -n $RG`.
- **SQLite is baked into the image** (seeded at build) — stateless. Azure SQL is
  a later step; when added, the container needs `msodbcsql18` + `unixodbc`
  installed via apt in the Dockerfile.
