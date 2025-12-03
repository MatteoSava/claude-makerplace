---
name: work-item-linking
description: Find, reference, and link Azure DevOps work items to pull requests. Use when discovering assigned work items, adding AB# references, or creating explicit PR-work-item relations through MCP or CLI tools.
argument-hint: "[work item or PR]"
---

# Work Item Linking

Use this skill when a PR or change must be connected to Azure DevOps work items.

## Required Inputs

- Azure DevOps organization or collection.
- Project name or ID.
- Repository ID.
- Pull request ID.
- Work item ID or search terms.

## Workflow

1. Discover work item.
   - List assigned items when no ID is known.
   - Search by title, area, iteration, or keywords.
   - Fetch details before linking.
2. Reference in PR text.
   - Use `Related to AB#12345`, `Fixes AB#12345`, or `Refs AB#12345` as appropriate.
3. Create explicit relation.
   - Use the tool/API relation call when available.
   - Confirm whether it needs project ID GUID, project name, repository ID, and PR ID.
4. Verify relation.
   - Check the PR and work item both show the association.

## Pitfalls

- Text references may not create durable relations.
- Project ID and project name are often different API inputs.
- Work item ID and PR ID should be kept distinct in notes.
- Do not link unrelated work just to satisfy process.

## Expected Output

Return:

- Work item selected.
- PR reference text.
- Explicit relation status.
- Any missing IDs or permissions.
