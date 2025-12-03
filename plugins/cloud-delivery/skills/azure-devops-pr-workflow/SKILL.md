---
name: azure-devops-pr-workflow
description: Create or update Azure DevOps pull requests and link work items through MCP or CLI tools. Use when opening a PR, resolving repository IDs, preparing reviewer assignment, or attaching work items to a PR.
argument-hint: "[repository branch work item]"
---

# Azure DevOps PR Workflow

Use this skill for Azure DevOps pull request workflows. Adapt tool names to the MCP server or CLI available in the current environment.

## Required Inputs

- Azure DevOps organization or collection.
- Project name.
- Repository name or ID.
- Source branch ref.
- Target branch ref.
- PR title.
- PR description.
- Optional work item IDs.
- Optional reviewer list.

## Workflow

1. Inspect git state.
   - Confirm current branch.
   - Confirm pushed source branch or create branch if the tool supports it.
   - Confirm no unintended local changes are included.
2. Resolve repository identity.
   - Prefer repository ID for PR creation APIs.
   - Do not assume repository name and ID are interchangeable.
3. Create or update the PR.
   - Use fully qualified refs such as `refs/heads/feature/example`.
   - Use a concise title and implementation-focused description.
   - Include linked work item references in text when useful.
4. Add work item relations.
   - Query work items before linking.
   - Link only relevant items.
   - Verify relation appears on the PR or work item.
5. Add reviewers.
   - Resolve users or groups to the expected descriptor format.
   - Add reviewers after PR creation when the API requires a PR ID.
6. Report the result.
   - PR URL.
   - Source and target branch.
   - Work items linked.
   - Reviewers added.

## Pitfalls

- PR creation often needs repository ID, not repository name.
- Branch refs should be fully qualified.
- Work item text references may not create explicit relations.
- Reviewer identifiers vary by API.
- Do not create duplicate PRs for the same source and target branch.

## Expected Output

Return a short PR summary with any unresolved work item or reviewer issues.
