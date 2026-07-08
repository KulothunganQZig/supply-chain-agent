using './main.bicep'

// AAD admin — your user (SQL admin + OpenAI User for local dev).
// Get with: az ad signed-in-user show --query "{id:id, upn:userPrincipalName}"
param aadAdminObjectId = 'c3a7c25f-6df5-44cb-87da-512a32f328dc'
param aadAdminName = 'kulothungans@quantzig.com'

// Image tag that must already be built + pushed to the ACR
// (az acr build --registry <acr> --image supply-chain-agent:v2 .)
param imageTag = 'v2'

// Model (gpt-5-mini / GlobalStandard / 2025+ api-version — see README gotchas)
param modelDeploymentName = 'gpt-5-mini'
param modelName = 'gpt-5-mini'
param modelVersion = '2025-08-07'
param modelSku = 'GlobalStandard'
param modelCapacity = 30
param openAiApiVersion = '2025-04-01-preview'

// Resource names default (in main.bicep) to the live deployment; override here
// for a clean-slate environment. ACR/SQL-server names must be globally unique.
