---
name: aspnet-api-standards
description: Apply clean ASP.NET Core API standards. Use when writing Minimal APIs, middleware, authentication, streaming services, cancellation-aware async code, or consistent error responses.
argument-hint: "[backend task]"
---

# ASP.NET API Standards

Use this skill when modifying an ASP.NET Core backend.

## Endpoint Pattern

- Use typed request/response models.
- Accept `CancellationToken`.
- Keep handlers thin.
- Delegate domain work to services.
- Require authorization on protected endpoints.
- Return consistent error responses.

```csharp
app.MapPost("/api/resource", async (
    RequestModel request,
    ResourceService service,
    IHostEnvironment env,
    CancellationToken cancellationToken) =>
{
    try
    {
        var result = await service.ProcessAsync(request, cancellationToken);
        return Results.Ok(result);
    }
    catch (Exception ex)
    {
        return ErrorResponseFactory.FromException(ex, env);
    }
})
.RequireAuthorization()
.WithName("CreateResource");
```

## Async Rules

- Use `async`/`await` end to end.
- Do not call `.Result` or `.Wait()`.
- Pass cancellation tokens to downstream calls.
- Use `IAsyncEnumerable<T>` for streaming APIs when appropriate.
- Use `[EnumeratorCancellation]` for streaming cancellation.

## Authentication Rules

- Prefer provider-supported JWT middleware.
- Validate issuer, audience, and scopes.
- Keep development credentials explicit and predictable.
- Use managed identity or workload identity in production.
- Do not expose internal auth errors to clients.

## Disposal Rules

- Guard public methods after disposal.
- Cancel pending operations before disposing shared resources.
- Dispose semaphores, cancellation sources, and SDK clients when owned.

## Error Responses

- Use RFC 7807-style problem responses where possible.
- Include correlation IDs.
- Avoid stack traces and internal exception messages in production.
- Preserve actionable messages for validation errors.

## Expected Output

When applying this skill, report:

- API shape and auth boundary.
- Cancellation and streaming behavior.
- Error response strategy.
- Tests or manual checks performed.
