# Browser flow contract

A browser flow should be written so any agent can repeat it.

```yaml
name: signup smoke
url: http://localhost:3000/signup
preconditions:
  - dev server running
  - use disposable test email
steps:
  - snapshot page
  - fill form fields
  - submit
  - wait for success text
assertions:
  - success message visible
  - no console errors matching /hydration|TypeError|ReferenceError/
  - no failed API requests for /signup
artifacts:
  - snapshot
  - screenshot after submit
  - console message list
  - network request list
```

Keep flows small. A flow is not a test suite; it is a reproducible browser QA path.
