// Full-stack IaC for the Supply Chain Visibility Agent — the declarative source
// of truth for the whole Azure deployment (Log Analytics, Managed Identity, ACR,
// Azure OpenAI, Azure SQL, Container Apps), all keyless via one user-assigned
// Managed Identity.
//
// The live environment was first bootstrapped imperatively with `az` (see
// README.md + container-apps.md); this template captures that same stack
// declaratively. Deploy to a fresh resource group:
//   az group create -n rg-supplychain-agent -l eastus2
//   az deployment group create -g rg-supplychain-agent -f infra/main.bicep -p infra/main.bicepparam
//
// One step is NOT expressible in Bicep: granting the Managed Identity a SQL
// contained-user (data-plane access is T-SQL, not ARM) — run infra/sql-grant.sql
// once as the AAD admin after deploy.
//
// The image must exist in ACR before the Container App can start — build it with
// `az acr build --registry <acr> --image supply-chain-agent:<tag> .` (see
// container-apps.md), then deploy/point this template at that tag.

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Region for most resources.')
param location string = resourceGroup().location

@description('Region for Azure SQL (East regions were capacity-blocked at bootstrap).')
param sqlLocation string = 'westus3'

@description('Object ID of the AAD admin (SQL admin + OpenAI User for local dev).')
param aadAdminObjectId string

@description('UPN / display name of the AAD admin.')
param aadAdminName string

@description('Container image tag (must already be built + pushed to the ACR).')
param imageTag string = 'v2'

// Resource names — defaulted to the live deployment so a redeploy aligns.
param identityName string = 'id-supplychain-app'
param acrName string = 'acrsupplychain85768'
param openAiName string = 'oai-supplychain-${uniqueString(resourceGroup().id)}'
param sqlServerName string = 'sql-sc-309221'
param sqlDatabaseName string = 'scdb'
param logAnalyticsName string = 'log-supplychain'
param appInsightsName string = 'appi-supplychain'
param containerEnvName string = 'cae-supplychain'
param containerAppName string = 'ca-supplychain'

// Model
param modelDeploymentName string = 'gpt-5-mini'
param modelName string = 'gpt-5-mini'
param modelVersion string = '2025-08-07'
param modelSku string = 'GlobalStandard'
param modelCapacity int = 30
param openAiApiVersion string = '2025-04-01-preview'

// Built-in role definition IDs (constant across tenants)
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
var openAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

// ---------------------------------------------------------------------------
// Identity + observability
// ---------------------------------------------------------------------------

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// Workspace-based Application Insights — receives the app's OpenTelemetry
// (HTTP request traces, per-executor / per-LLM-call spans, logs).
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// ---------------------------------------------------------------------------
// Container Registry
// ---------------------------------------------------------------------------

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
  }
}

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, identity.id, acrPullRoleId)
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ---------------------------------------------------------------------------
// Azure OpenAI
// ---------------------------------------------------------------------------

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
  }
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAi
  name: modelDeploymentName
  sku: {
    name: modelSku
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

// OpenAI User for both the app identity (runtime) and the AAD admin (local dev)
resource openAiUserForApp 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, identity.id, openAiUserRoleId)
  scope: openAi
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiUserRoleId)
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource openAiUserForAdmin 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, aadAdminObjectId, openAiUserRoleId)
  scope: openAi
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openAiUserRoleId)
    principalId: aadAdminObjectId
    principalType: 'User'
  }
}

// ---------------------------------------------------------------------------
// Azure SQL (AAD-only auth; the app connects keyless via ActiveDirectoryMsi)
// ---------------------------------------------------------------------------

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: sqlServerName
  location: sqlLocation
  properties: {
    administrators: {
      administratorType: 'ActiveDirectory'
      principalType: 'User'
      login: aadAdminName
      sid: aadAdminObjectId
      tenantId: tenant().tenantId
      azureADOnlyAuthentication: true
    }
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: sqlDatabaseName
  location: sqlLocation
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  properties: {
    requestedBackupStorageRedundancy: 'Local'
  }
}

// Special 0.0.0.0 rule = "Allow Azure services and resources to access this server"
resource sqlAllowAzure 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ---------------------------------------------------------------------------
// Container Apps
// ---------------------------------------------------------------------------

resource containerEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: identity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'app'
          image: '${acr.properties.loginServer}/supply-chain-agent:${imageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'AZURE_CLIENT_ID', value: identity.properties.clientId }
            { name: 'AZURE_OPENAI_ENDPOINT', value: openAi.properties.endpoint }
            { name: 'AZURE_OPENAI_API_VERSION', value: openAiApiVersion }
            { name: 'MODEL_DEPLOYMENT_NAME', value: modelDeploymentName }
            { name: 'AZURE_SQL_SERVER', value: '${sqlServer.name}${environment().suffixes.sqlServerHostname}' }
            { name: 'AZURE_SQL_DATABASE', value: sqlDatabaseName }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
  dependsOn: [
    acrPull
  ]
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

output appFqdn string = containerApp.properties.configuration.ingress.fqdn
output acrLoginServer string = acr.properties.loginServer
output azureOpenAIEndpoint string = openAi.properties.endpoint
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output managedIdentityClientId string = identity.properties.clientId
output managedIdentityName string = identity.name
