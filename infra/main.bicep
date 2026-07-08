// Azure OpenAI resource + model deployment + keyless RBAC for the
// Supply Chain Visibility Agent (migration Phase 1, Azure OpenAI only).
//
// Deploy:
//   az group create -n rg-supplychain-agent -l eastus2
//   az deployment group create -g rg-supplychain-agent \
//     -f infra/main.bicep -p infra/main.bicepparam
//
// After deploy, the output `azureOpenAIEndpoint` goes into .env as
// AZURE_OPENAI_ENDPOINT, and MODEL_DEPLOYMENT_NAME = the `modelDeploymentName`.

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Globally-unique name for the Azure OpenAI resource.')
param openAiName string = 'oai-supplychain-${uniqueString(resourceGroup().id)}'

@description('Model deployment name — must match MODEL_DEPLOYMENT_NAME in the app config.')
param modelDeploymentName string = 'gpt-4.1'

@description('Underlying model to deploy.')
param modelName string = 'gpt-4.1'

@description('Model version. Check availability in your region with: az cognitiveservices account list-models.')
param modelVersion string = '2025-04-14'

@description('Tokens-per-minute capacity, in thousands (e.g. 30 = 30K TPM).')
param modelCapacity int = 30

@description('Object ID of the principal (your user for local dev, or a Managed Identity) to grant OpenAI access.')
param principalId string

@description('Principal type: User for `az login` dev auth, ServicePrincipal for a Managed Identity.')
@allowed([
  'User'
  'ServicePrincipal'
])
param principalType string = 'User'

// --- Azure OpenAI resource (Cognitive Services account, kind = OpenAI) ---
resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    // Custom subdomain is required for AAD/token auth (the keyless path).
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
    // Disable local API keys so the only way in is AAD — enforces the keyless design.
    disableLocalAuth: true
  }
}

// --- Model deployment ---
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAi
  name: modelDeploymentName
  sku: {
    name: 'Standard'
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
  }
}

// --- RBAC: Cognitive Services OpenAI User (data-plane inference access) ---
// Role definition ID is a well-known built-in GUID, constant across tenants.
var openAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, principalId, openAiUserRoleId)
  scope: openAi
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiUserRoleId)
    principalId: principalId
    principalType: principalType
  }
}

@description('Set this as AZURE_OPENAI_ENDPOINT in .env.')
output azureOpenAIEndpoint string = openAi.properties.endpoint

@description('Set this as MODEL_DEPLOYMENT_NAME in .env.')
output modelDeploymentName string = modelDeploymentName
