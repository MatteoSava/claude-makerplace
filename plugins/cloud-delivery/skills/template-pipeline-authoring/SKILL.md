---
name: template-pipeline-authoring
description: Generate or update Azure DevOps YAML pipelines from an internal template catalog. Use when selecting CI, release, GitOps, security scan, build, deploy, cloud, testing, or utility templates with required resources and parameters.
argument-hint: "[pipeline scenario]"
---

# Template Pipeline Authoring

Use this skill when a repository standardizes Azure DevOps pipelines through a reusable template catalog.

## Workflow

1. Classify intent.
   - CI build only.
   - CI plus release.
   - CI plus GitOps sync.
   - Security or quality scan only.
   - Utility pipeline.
2. Find existing pipeline YAML and repo conventions.
3. Choose the nearest starter scenario.
4. Load only the relevant template category reference.
5. Infer parameters from:
   - existing pipeline files
   - repository name and folder conventions
   - README/docs/config files
   - selected starter template defaults
6. Ask one consolidated question for unresolved values.
7. Keep standard resource and template-reference structure.
8. Validate YAML and schema where possible.

## GitOps Mental Model

- App repository pipeline builds immutable artifact or image.
- Manifest/config repository pipeline updates environment references.
- Environment promotion should not rebuild artifacts.
- Tag or manifest sync is the release boundary.

## Output Checks

- YAML indentation is valid.
- Template paths are relative and include the catalog alias expected by the project.
- Only documented template parameters are used unless the user asks for a custom extension.
- Required pools, resources, and trigger policy match local conventions.

## Expected Output

Return:

- Pipeline type.
- Template category selected.
- Inferred parameters.
- Unresolved parameters.
- Validation result.
