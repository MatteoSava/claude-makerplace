# Browser privacy threat model

Chrome DevTools MCP can inspect live browser state. That is powerful and risky.

## Risks

- screenshots containing user data
- network responses containing tokens or PII
- cookies/session state exposed through browser automation
- agents typing secrets into pages
- unintended production writes
- persistent browser profile state leaking between sessions

## Defaults

The project scaffold defaults to:

- local URLs only
- restricted artifact paths
- sensitive HTTP headers blocked
- no production domains
- evidence reports stored locally under `.webqa-devtools/reports/`

## Recommended practice

- Use a dedicated test browser profile.
- Prefer `--isolated` for MCP sessions.
- Use test credentials only.
- Redact tokens, cookies, auth headers, passwords, API keys, and session IDs.
- Do not save traces/screenshots that include sensitive data unless explicitly required.
