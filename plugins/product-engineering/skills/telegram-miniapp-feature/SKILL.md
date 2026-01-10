---
name: telegram-miniapp-feature
description: Build full-stack Telegram Mini App features with a web frontend, edge API, database, and server-side initData validation. Use when implementing pages, Hono or Workers routes, D1/SQLite data access, or Telegram WebApp behavior.
argument-hint: "[feature brief]"
---

# Telegram Mini App Feature

Use this skill for production-shaped Telegram Mini App work. Adapt framework details to the repository; do not force this stack if the project already uses another one.

## Reference Architecture

```text
Telegram client
  -> Mini App frontend
  -> Edge API
  -> Database
```

Common implementation:

- Frontend: Next.js static export or another client-rendered web app.
- API: Cloudflare Workers with Hono or an equivalent edge router.
- Data: Cloudflare D1, SQLite, Postgres, or the existing project database.
- Auth: Telegram `initData` validated server-side on every privileged request.

## Required Checks

Before editing:

- Locate current app structure, package manager, deploy target, and routing convention.
- Find existing Telegram WebApp provider or bootstrap code.
- Find API middleware, validation library, and database migration pattern.
- Confirm whether the feature needs TON wallet integration; if yes, use `ton-wallet-integration`.

## Implementation Workflow

1. Define the feature contract.
   - User action.
   - Required Telegram user fields.
   - API endpoints.
   - Data model and authorization boundaries.
2. Add frontend behavior.
   - Initialize `window.Telegram.WebApp`.
   - Respect theme parameters and viewport constraints.
   - Handle loading, error, empty, and success states.
3. Add API route.
   - Validate `X-Init-Data` or equivalent signed init data.
   - Validate request body with the repo's validation approach.
   - Return explicit JSON errors.
4. Add persistence.
   - Create a migration when schema changes.
   - Scope reads and writes by Telegram user ID or app tenant.
5. Add tests.
   - Unit test initData validation.
   - Test authorization failure paths.
   - Add integration or route tests for the new endpoint.
6. Verify in Telegram-like constraints.
   - Mobile viewport.
   - Light and dark theme.
   - Back button or close behavior if applicable.

## initData Validation Requirements

- Recompute the HMAC using the bot token-derived secret.
- Compare hashes with a timing-safe comparison when available.
- Enforce auth date freshness when the project has a session policy.
- Never trust `initDataUnsafe` on the server.
- Never persist the bot token in frontend code.

## Expected Output

Provide:

- Files changed and feature flow.
- API contract.
- Migration summary.
- Security checks performed.
- Test and manual verification commands.
