---
name: feedback-makerplace
description: Collect structured feedback about the Claude Makerplace plugin experience and send it to a configured webhook.
---

Collect feedback about this Claude Makerplace session.

## Step 1 - Analyze The Session

Review the current conversation and identify:

- Which Claude Makerplace skills, commands, or agents were used.
- Which package surfaces were involved: Claude Code, Codex, OpenCode, hooks, scripts, docs, or validation.
- Any errors, failed assumptions, validation failures, skipped checks, or user corrections.

Present a concise summary to the user:

```text
Here is what I observed in this session:
- Skills/commands/agents used: ...
- Surfaces involved: ...
- Errors or friction: ... or none
```

If there was no Claude Makerplace usage in the session, say there is nothing plugin-specific to report and stop.

## Step 2 - Ask For Feedback

Ask at most three questions, one at a time:

1. Overall, how was your experience with Claude Makerplace in this session?
   - Positive
   - Neutral
   - Negative
2. Adapt the details question to the sentiment:
   - Positive: What worked well?
   - Neutral: What could be improved?
   - Negative: What was frustrating or incorrect?
3. Optional: Any feature requests or workflow suggestions?

Keep answers short. Do not ask for private repository names, credentials, internal URLs, client names, or personal identifiers.

## Step 3 - Build The Payload

Create a sanitized JSON payload:

```json
{
  "timestamp": "<ISO 8601 UTC>",
  "sentiment": "<positive|neutral|negative>",
  "summary": {
    "components": ["<skills, commands, agents, hooks, docs, validation>"],
    "surfaces": ["<claude-code|codex|opencode>"],
    "errors": ["<sanitized error or friction summary>"]
  },
  "details": "<feedback answer>",
  "suggestions": "<suggestions or None>"
}
```

Before sending, remove or generalize:

- local filesystem paths
- private repository names
- personal names or usernames
- internal hosts or URLs
- credentials, tokens, API keys, signatures, or secrets
- client, employer, account, run, or telemetry identifiers

## Step 4 - Send Feedback

Send the payload only when a feedback destination is configured:

```bash
echo '<sanitized-json-payload>' | bash "${CLAUDE_PLUGIN_ROOT}/scripts/send-feedback.sh" -
```

Supported destination config:

- Generic webhook:
  - `MAKERPLACE_FEEDBACK_DESTINATION=webhook`
  - `MAKERPLACE_FEEDBACK_WEBHOOK_URL=<https endpoint>`
- GitHub issue:
  - `MAKERPLACE_FEEDBACK_DESTINATION=github`
  - `MAKERPLACE_FEEDBACK_GITHUB_REPOSITORY=<owner/repo>`
  - `MAKERPLACE_FEEDBACK_GITHUB_TOKEN=<token with Issues write permission>`
  - optional `MAKERPLACE_FEEDBACK_GITHUB_TITLE`
  - optional `MAKERPLACE_FEEDBACK_GITHUB_LABELS=feedback,plugin`
- GitHub issue comment:
  - all GitHub issue settings above
  - `MAKERPLACE_FEEDBACK_GITHUB_ISSUE_NUMBER=<number>`

With `MAKERPLACE_FEEDBACK_DESTINATION=auto`, the sender uses GitHub when `MAKERPLACE_FEEDBACK_GITHUB_REPOSITORY` is set, otherwise it uses `MAKERPLACE_FEEDBACK_WEBHOOK_URL`.

The sender prints `OK` on success, `DRYRUN:<destination>` in dry-run mode, and `FAIL:<reason>` on failure.

If no destination is configured, tell the user the feedback was collected but not sent, and mention the required env vars for webhook or GitHub delivery.

## Step 5 - Confirm

- On `OK`: thank the user and say the feedback was sent.
- On `FAIL:*`: say the feedback could not be sent and avoid showing raw network or webhook details.

Do not modify repository files while running this command.
