#!/usr/bin/env bash
# Send sanitized Claude Makerplace feedback to a configured destination.
# Usage: send-feedback.sh <json-payload-file>
#   or:  echo '<json>' | send-feedback.sh -

set -euo pipefail

INPUT="${1:--}"
DESTINATION="${MAKERPLACE_FEEDBACK_DESTINATION:-auto}"
WEBHOOK_URL="${MAKERPLACE_FEEDBACK_WEBHOOK_URL:-}"
GITHUB_REPOSITORY="${MAKERPLACE_FEEDBACK_GITHUB_REPOSITORY:-}"
GITHUB_ISSUE_NUMBER="${MAKERPLACE_FEEDBACK_GITHUB_ISSUE_NUMBER:-}"
GITHUB_TOKEN="${MAKERPLACE_FEEDBACK_GITHUB_TOKEN:-${GITHUB_TOKEN:-}}"
GITHUB_API_URL="${MAKERPLACE_FEEDBACK_GITHUB_API_URL:-https://api.github.com}"
GITHUB_API_VERSION="${MAKERPLACE_FEEDBACK_GITHUB_API_VERSION:-2026-03-10}"
GITHUB_TITLE="${MAKERPLACE_FEEDBACK_GITHUB_TITLE:-Claude Makerplace feedback}"
GITHUB_LABELS="${MAKERPLACE_FEEDBACK_GITHUB_LABELS:-}"
DRY_RUN="${MAKERPLACE_FEEDBACK_DRY_RUN:-}"

if [[ "$INPUT" == "-" ]]; then
  PAYLOAD=$(cat)
else
  PAYLOAD=$(cat "$INPUT")
fi

json_string() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  value="${value//$'\t'/\\t}"
  printf '"%s"' "$value"
}

labels_json() {
  local labels="$1"
  local first=1
  local label
  printf '['
  IFS=',' read -ra parts <<< "$labels"
  for label in "${parts[@]}"; do
    label="${label#"${label%%[![:space:]]*}"}"
    label="${label%"${label##*[![:space:]]}"}"
    [[ -z "$label" ]] && continue
    if [[ "$first" -eq 0 ]]; then
      printf ','
    fi
    json_string "$label"
    first=0
  done
  printf ']'
}

feedback_markdown() {
  printf '## Claude Makerplace Feedback\n\n```json\n%s\n```\n' "$PAYLOAD"
}

send_webhook() {
  if [[ -z "$WEBHOOK_URL" ]]; then
    echo "FAIL:missing-webhook"
    exit 1
  fi
  if [[ "$DRY_RUN" == "1" || "$DRY_RUN" == "true" ]]; then
    echo "DRYRUN:webhook"
    exit 0
  fi

  local http_code
  http_code=$(curl -sS -o /dev/null -w "%{http_code}" \
    -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    --data-binary "$PAYLOAD" 2>/dev/null || true)

  if [[ "$http_code" =~ ^2[0-9]{2}$ ]]; then
    echo "OK"
    exit 0
  fi

  echo "FAIL:http-${http_code:-000}"
  exit 1
}

send_github() {
  if [[ ! "$GITHUB_REPOSITORY" =~ ^[^/]+/[^/]+$ ]]; then
    echo "FAIL:missing-github-repository"
    exit 1
  fi
  if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "FAIL:missing-github-token"
    exit 1
  fi

  local body endpoint request http_code mode
  body=$(feedback_markdown)
  if [[ -n "$GITHUB_ISSUE_NUMBER" ]]; then
    mode="github-comment"
    endpoint="${GITHUB_API_URL%/}/repos/${GITHUB_REPOSITORY}/issues/${GITHUB_ISSUE_NUMBER}/comments"
    request=$(printf '{"body":%s}' "$(json_string "$body")")
  else
    mode="github-issue"
    endpoint="${GITHUB_API_URL%/}/repos/${GITHUB_REPOSITORY}/issues"
    request=$(printf '{"title":%s,"body":%s' "$(json_string "$GITHUB_TITLE")" "$(json_string "$body")")
    if [[ -n "$GITHUB_LABELS" ]]; then
      request="${request},\"labels\":$(labels_json "$GITHUB_LABELS")"
    fi
    request="${request}}"
  fi

  if [[ "$DRY_RUN" == "1" || "$DRY_RUN" == "true" ]]; then
    echo "DRYRUN:${mode}"
    exit 0
  fi

  http_code=$(curl -sS -o /dev/null -w "%{http_code}" \
    -X POST "$endpoint" \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "X-GitHub-Api-Version: ${GITHUB_API_VERSION}" \
    -H "Content-Type: application/json" \
    --data-binary "$request" 2>/dev/null || true)

  if [[ "$http_code" =~ ^2[0-9]{2}$ ]]; then
    echo "OK"
    exit 0
  fi

  echo "FAIL:github-http-${http_code:-000}"
  exit 1
}

case "$DESTINATION" in
  github)
    send_github
    ;;
  webhook)
    send_webhook
    ;;
  auto)
    if [[ -n "$GITHUB_REPOSITORY" ]]; then
      send_github
    elif [[ -n "$WEBHOOK_URL" ]]; then
      send_webhook
    else
      echo "FAIL:missing-destination"
      exit 1
    fi
    ;;
  *)
    echo "FAIL:invalid-destination"
    exit 1
    ;;
esac
