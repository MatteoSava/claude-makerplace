# Safety and privacy

Chrome DevTools MCP gives an agent browser-observation power. Treat it as sensitive.

## Guardrails

- Prefer local dev URLs over production.
- Do not inspect cookies, login databases, saved passwords, or browser profile secrets.
- Do not paste secrets into the browser for testing.
- Avoid logged-in production pages unless explicitly requested.
- Redact sensitive request/response data in summaries.
- Keep `.webqa-devtools/state/` and `.webqa-devtools/reports/` local unless the team intentionally checks in sanitized reports.

## Default policy

The default `.webqa-devtools/policy.json` blocks external DevTools navigation, sensitive headers, and artifact writes outside approved folders.
