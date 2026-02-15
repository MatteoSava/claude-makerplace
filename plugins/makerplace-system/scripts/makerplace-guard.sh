#!/usr/bin/env sh
set -eu

case "${MAKERPLACE_HOOKS:-on}" in
  off|OFF|false|FALSE|0|disabled|DISABLED) exit 0 ;;
esac

INPUT="$(cat)"

FILE_PATH="$(printf '%s' "$INPUT" | sed -nE 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' | head -n 1)"

case "$FILE_PATH" in
  *SKILL.md|*plugin.json|*marketplace.json|*hooks.json|*source-inventory.md|*source-audit.md|*README.md) ;;
  *) exit 0 ;;
esac

[ -f "$FILE_PATH" ] || exit 0

MAC_HOME_MARKER='/'"Users"'/'
INTERNAL_HOST_MARKER='dev[.]azure[.]com'
LEAK_PATTERN="(${MAC_HOME_MARKER}|${INTERNAL_HOST_MARKER}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}|[0-9]{1,3}([.][0-9]{1,3}){3}|api[_-]?key|client[_ -]?secret|access[_ -]?token|bearer[_ -]?token|private[_ -]?key|mnemonic|password|client name|internal repository)"

if LC_ALL=C grep -Eiq "$LEAK_PATTERN" "$FILE_PATH"; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"Makerplace guard: the edited marketplace/plugin artifact may contain personal, client, credential, local path, or internal URL markers. Before presenting or publishing it, sanitize the content and rerun `claude plugin validate .` plus a targeted leak scan."}}'
else
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"Makerplace guard: marketplace/plugin artifact changed. Before publishing, keep skill bodies concise, verify frontmatter, and run `claude plugin validate .`."}}'
fi
