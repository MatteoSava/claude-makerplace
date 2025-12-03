---
name: bicep-infrastructure-standards
description: Write maintainable Azure Bicep infrastructure. Use when creating or modifying Container Apps, managed identities, RBAC, Key Vault, Application Insights, networking, or environment-specific parameters.
argument-hint: "[infrastructure task]"
---

# Bicep Infrastructure Standards

Use this skill for Azure infrastructure-as-code changes.

## Principles

- Keep modules small and purpose-specific.
- Use parameters for environment differences.
- Prefer managed identity over secrets.
- Scope RBAC narrowly.
- Make diagnostics and observability first-class.
- Keep names deterministic and length-safe.

## Workflow

1. Inspect existing module layout and naming convention.
2. Identify resource ownership and deployment scope.
3. Add or update parameters with safe defaults.
4. Declare resources with explicit dependencies only when needed.
5. Add managed identity and RBAC assignments.
6. Add logs, metrics, and Application Insights integration where applicable.
7. Validate and preview before deploy.

## Security Rules

- Do not hardcode secrets.
- Use Key Vault references or platform secret stores.
- Assign least-privilege roles.
- Avoid broad subscription-scope permissions unless required.
- Keep public ingress explicit.

## Container App Checks

- CPU and memory sizing.
- Revision mode and traffic split.
- Environment variables and secret references.
- Health probes.
- Managed identity.
- Log Analytics/Application Insights integration.
- Scale rules.

## Expected Output

Return:

- Resources changed.
- Security and identity model.
- Deployment command or validation command.
- Risks and rollback considerations.
