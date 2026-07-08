using './main.bicep'

// Your Azure AD object ID — for local dev this is your own user, so the
// `az login` session (DefaultAzureCredential) can call the deployed model.
// Get it with: az ad signed-in-user show --query id -o tsv
param principalId = 'c3a7c25f-6df5-44cb-87da-512a32f328dc'
param principalType = 'User'

// Model must be current (non-deprecating) and its SKU available in the region.
// gpt-4.1 / gpt-4.1-mini / gpt-4o-mini all deprecate ~Oct 2026 and are blocked
// for new deployments; gpt-5-mini (2025-08-07) runs to 2027-02-06. Re-check with:
//   az cognitiveservices model list --location eastus2 \
//     --query "[?model.name=='gpt-5-mini'].{v:model.version, dep:model.deprecation.inference, skus:model.skus[].name}"
param modelDeploymentName = 'gpt-5-mini'
param modelName = 'gpt-5-mini'
param modelVersion = '2025-08-07'
param skuName = 'GlobalStandard'
param modelCapacity = 30
