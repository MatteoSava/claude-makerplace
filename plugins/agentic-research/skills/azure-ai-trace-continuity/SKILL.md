---
name: azure-ai-trace-continuity
description: Diagnose and repair fragmented Azure AI or OpenAI traces with OpenTelemetry propagation. Use when one application run appears as multiple traces across Azure AI Foundry, Application Insights, OpenAI SDK calls, httpx, or other HTTP clients.
argument-hint: "[trace id or symptom]"
---

# Azure AI Trace Continuity

Use this skill when a single logical AI run appears fragmented across observability tools.

## Diagnosis Model

Check propagation in layers:

1. In-process spans are correctly parented.
2. Outbound HTTP instrumentation injects `traceparent`.
3. The remote AI service receives and joins the caller trace.
4. Exporters send the same operation context to the observability backend.

If layer 1 works but layer 2 is missing, local traces may look coherent while service-side traces fragment.

## Required Checks

- Confirm the active execution mode: streaming vs non-streaming.
- Confirm OpenTelemetry bootstrap order.
- Confirm HTTP client instrumentation for the actual client library.
- Confirm outbound AI dependencies include trace headers.
- Confirm remote service traces share operation IDs or parent IDs.
- Separate trace continuity issues from application-level tool or response errors.

## Python/httpx Pattern

```python
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def configure_observability():
    configure_azure_monitor_or_exporter()
    HTTPXClientInstrumentor().instrument()
```

Install and pin the instrumentation dependency used by the project.

## Verification Workflow

1. Run one representative dry run.
2. Capture the root trace ID printed by the app or exporter.
3. Query the observability backend for dependencies under that trace.
4. Verify outbound AI HTTP calls have:
   - one shared operation ID
   - populated parent IDs
   - expected result codes
   - expected timing
5. Compare the same run in the AI provider's trace UI.
6. If still fragmented, inspect raw request instrumentation and streaming span activation.

## Common Fixes

- Instrument the actual HTTP client library, not just the framework.
- Activate span context before the SDK call that creates the outbound request.
- Avoid creating streaming spans after the first remote request has already started.
- Ensure custom transports preserve headers.
- Initialize telemetry once at process startup.

## Expected Output

Produce:

- Layer-by-layer diagnosis.
- Probable missing propagation point.
- Minimal code/config change.
- Verification query or command shape.
- Residual risks.
