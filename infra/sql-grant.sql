-- Grant the app's user-assigned Managed Identity access to the database.
--
-- Azure SQL data-plane access is NOT controlled by Azure RBAC — it needs a
-- contained database user created via T-SQL. This is the one step that can't be
-- done with `az` or Bicep; run it once as the AAD admin.
--
-- HOW TO RUN (no local ODBC driver needed):
--   Azure Portal -> SQL databases -> scdb (server sql-sc-309221)
--     -> "Query editor (preview)" in the left nav
--     -> sign in with Microsoft Entra (your account, the AAD admin)
--     -> paste the block below -> Run.
--   (Firewall already allows Azure services; if the editor complains about your
--    client IP, click "Add client IP" then retry.)
--
-- Run this against the scdb database (NOT master).

CREATE USER [id-supplychain-app] FROM EXTERNAL PROVIDER;
ALTER ROLE db_ddladmin  ADD MEMBER [id-supplychain-app];  -- create tables on first boot
ALTER ROLE db_datareader ADD MEMBER [id-supplychain-app];
ALTER ROLE db_datawriter ADD MEMBER [id-supplychain-app];
