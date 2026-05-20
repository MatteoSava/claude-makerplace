# Policy reference

The main policy file is `.repo-sentinel/policy.json`.

## Important sections

### `protected_paths`

Glob list blocked from agent writes. Defaults include agent config, sentinel policy, secret-like paths, generated folders, virtualenvs, and dependency caches.

### `migration_guard`

When `protect_existing` is true, existing migration files matching configured globs cannot be edited. Agents should create new migrations instead.

### `shell.deny_regex`

Regex list of command patterns blocked before execution. Defaults include destructive git commands, recursive root deletes, remote-code pipes, infrastructure apply/destroy, Kubernetes deletes, Docker prune, recursive chmod 777, and disk format/write commands.

### `shell.warn_regex`

Regex list that emits model-visible context without blocking. Defaults include `sudo`, file uploads over curl/wget, and broad recursive deletes.

### `secret_scan`

Post-edit scan for common secret patterns. This is not a replacement for a full secret scanner, but it catches high-signal mistakes early.

### `verification`

Stop gate configuration. If code/config files changed and no successful verification command was recorded after the last edit, the hook asks the agent to continue and run a check.

### `prompt_guard`

Blocks prompts that ask the agent to bypass/disable Repo Sentinel unless the explicit authorization phrase is present.

## Override env vars

Use only for one reviewed command:

```text
REPO_SENTINEL_ALLOW_ALL
REPO_SENTINEL_ALLOW_DESTRUCTIVE
REPO_SENTINEL_ALLOW_CONFIG_CHANGE
REPO_SENTINEL_ALLOW_SECRET_WRITE
```
