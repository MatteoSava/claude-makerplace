---
name: azure-container-app-deploy
description: Deploy and troubleshoot Azure Container Apps with azd, container logs, Bicep infrastructure, Entra app configuration, managed identity, and RBAC. Use when deployments fail, containers do not update, or infrastructure hooks need diagnosis.
argument-hint: "[deployment issue or environment]"
---

# Azure Container App Deploy

Use this skill for Azure Container Apps deployment and troubleshooting.

## Deployment Model

Typical phases:

- Pre-provision: create or discover identity, app registration, AI/resource dependencies, and environment variables.
- Provision: deploy infrastructure and placeholder container image.
- Post-provision: update redirect URIs, assign RBAC, and connect external resources.
- Pre-deploy: build, push, and set the final container image.

Adapt names to the repository. Do not copy private resource names into reusable docs.

## Quick Diagnosis

Check in this order:

1. Provisioning state.
2. Current container image.
3. Latest revision status.
4. Container logs.
5. Environment variables and secret references.
6. Managed identity principal ID.
7. RBAC assignments.
8. Redirect URIs and auth app configuration.

## Log Handling

Container logs can be large. Summarize:

- root cause
- key error lines
- affected resource
- fix command

Do not paste full logs unless the user asks for them.

## Common Failure Classes

- Container image not updated.
- Build used stale frontend or backend environment.
- Missing auth configuration.
- Managed identity lacks access to downstream AI or data resource.
- Redirect URI missing after deployment URL changes.
- Local Docker unavailable and cloud build fallback differs from expected path.

## Expected Output

Return:

- Deployment phase that failed.
- Evidence from status/logs.
- Minimal fix.
- Validation command.
- Rollback or retry guidance.
