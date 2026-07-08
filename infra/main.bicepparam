using './main.bicep'

// Your Azure AD object ID — for local dev this is your own user, so the
// `az login` session (DefaultAzureCredential) can call the deployed model.
// Get it with: az ad signed-in-user show --query id -o tsv
param principalId = '<YOUR-AAD-OBJECT-ID>'
param principalType = 'User'

// Region must have GPT-4.1 capacity. Check with:
//   az cognitiveservices account list-models -n <name> -g <rg> -o table
// (or the model availability docs) and adjust modelVersion if needed.
param modelDeploymentName = 'gpt-4.1'
param modelName = 'gpt-4.1'
param modelVersion = '2025-04-14'
param modelCapacity = 30
