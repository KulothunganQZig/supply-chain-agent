# CI/CD — GitHub Actions + Azure OIDC (keyless)

`.github/workflows/ci-cd.yml` runs on every push/PR (lint + tests) and, on push
to `main`, builds the image in ACR and updates the Container App — authenticating
to Azure with **OIDC**, so there is **no Azure secret stored in GitHub** (just
three non-sensitive IDs).

## Azure side (already provisioned via az)

A dedicated managed identity `id-supplychain-cicd` with:
- a **federated credential** trusting GitHub's OIDC token for
  `repo:KulothunganQZig/supply-chain-agent:ref:refs/heads/main`, and
- **Contributor** on `rg-supplychain-agent` (to run `az acr build` + update the app).

To recreate:

```bash
RG=rg-supplychain-agent; REPO=KulothunganQZig/supply-chain-agent
az identity create -g $RG -n id-supplychain-cicd
az identity federated-credential create --name github-main --identity-name id-supplychain-cicd -g $RG \
  --issuer https://token.actions.githubusercontent.com \
  --subject "repo:$REPO:ref:refs/heads/main" \
  --audiences api://AzureADTokenExchange
PRINCIPAL=$(az identity show -g $RG -n id-supplychain-cicd --query principalId -o tsv)
az role assignment create --assignee-object-id $PRINCIPAL --assignee-principal-type ServicePrincipal \
  --role Contributor --scope $(az group show -n $RG --query id -o tsv)
```

(Least-privilege alternative to RG-Contributor: `AcrPush` + Container Apps
Contributor scoped to just those two resources.)

## GitHub side (manual — you do this once)

Add three **repository secrets** (Settings → Secrets and variables → Actions →
New repository secret). These are IDs, not credentials — the OIDC exchange is
what actually authenticates:

| Secret | Value |
|---|---|
| `AZURE_CLIENT_ID` | `ff93b23b-0775-4cea-8c12-4c9815296f23` (id-supplychain-cicd) |
| `AZURE_TENANT_ID` | `30f43a59-83f4-4883-b650-4a3e36a194f3` |
| `AZURE_SUBSCRIPTION_ID` | `5268915a-77ef-4b6a-a224-b0e54217e3f0` |

Then push to `main` — the workflow lints, tests, builds `supply-chain-agent:<sha>`
in ACR, and rolls the Container App to it.

## Notes

- The federated credential is scoped to the `main` branch. To deploy from other
  branches/environments, add more federated credentials (e.g. a `pull_request`
  or environment subject).
- Image tag is the commit SHA — immutable and traceable back to the source.
- `az acr build` runs server-side, so the GitHub runner needs no Docker.
