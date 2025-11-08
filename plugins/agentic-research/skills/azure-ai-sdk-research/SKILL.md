---
name: azure-ai-sdk-research
description: Research Azure AI SDK usage before implementing agent features. Use when looking up Azure AI Foundry, Azure.AI.Projects, Responses API, streaming types, citations, MCP/tool calls, or .NET agent samples.
argument-hint: "[SDK question]"
---

# Azure AI SDK Research

Use this skill when SDK behavior is uncertain. Do not guess API shape from memory.

## Research Order

1. Official SDK documentation.
2. SDK source repository and samples.
3. Official product quickstarts.
4. Architecture sample repositories.
5. Existing project code.
6. GitHub code search for narrow method/type usage.

When information may have changed, verify against official sources first.

## Research Question Shape

Make the question specific:

- method signature
- streaming event type
- authentication pattern
- citation/annotation extraction
- file search or tool call handling
- conversation/thread lifecycle
- agent ID format and endpoint family

## Evidence Rules

- Capture source path or URL for every concrete SDK claim.
- Prefer minimal pseudocode over copied sample blocks.
- Separate stable patterns from preview/beta behavior.
- Record package versions when found.
- Note whether a sample uses a different API surface than the project.

## Output Format

Return:

- Answer in one paragraph.
- Key method/type names.
- Minimal pseudocode.
- Source references.
- Gotchas and version caveats.
