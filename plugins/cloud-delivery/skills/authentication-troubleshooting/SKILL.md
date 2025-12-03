---
name: authentication-troubleshooting
description: Troubleshoot browser-to-API and API-to-cloud authentication flows. Use when debugging 401/403 errors, MSAL or OAuth token acquisition, JWT audience/scope mismatches, Entra ID config, managed identity, or local credential chains.
argument-hint: "[auth symptom]"
---

# Authentication Troubleshooting

Use this skill for authentication failures across frontend, backend, and cloud resource access.

## Architecture Model

Map the flow before fixing:

1. Browser obtains token through OAuth/MSAL or equivalent.
2. Frontend sends bearer token to backend.
3. Backend validates issuer, audience, and scope.
4. Backend uses managed identity or local developer credentials for downstream cloud resources.

## Debugging Steps

1. Identify failing hop: browser auth, API auth, or downstream resource auth.
2. Decode the access token locally.
3. Verify:
   - issuer
   - audience
   - scopes or roles
   - tenant
   - expiry
4. Check backend validation configuration.
5. Check frontend token request scopes.
6. Check redirect URI and app registration settings.
7. Check local credential chain or managed identity assignment.
8. Check downstream RBAC.

## Common Fixes

- Add the expected API audience.
- Request the correct scope.
- Use silent acquisition first and an interactive fallback only when needed.
- Use explicit local credential chains for development.
- Use managed identity in deployed environments.
- Recreate or refresh generated environment files after app registration changes.

## Expected Output

Return:

- Failing hop.
- Token/config evidence.
- Minimal config or code fix.
- Security risk check.
- Verification steps.
